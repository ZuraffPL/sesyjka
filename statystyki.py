import threading
import tkinter as tk
from tkinter import ttk  # type: ignore
from typing import Any, Callable, Dict, List, Optional, Set
import sqlite3
from collections import defaultdict
import matplotlib

matplotlib.use('TkAgg')  # Backend dla tkinter
import matplotlib.pyplot as plt  # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # type: ignore
from matplotlib.figure import Figure  # type: ignore
from database_manager import get_db_path
from font_scaling import scale_font_size
from dialog_utils import create_ctk_toplevel, apply_safe_geometry, enable_maximize_button


def _bind_click_recursive(
    widget: Any,
    handler: Callable[[Any], None],
    exclude: Optional[Set[Any]] = None,
) -> None:
    """Podpina LPM (rekurencyjnie) na widget i jego potomkach.

    Pomija `ttk.Combobox` (żeby nie kolidować z jego natywną obsługą) oraz
    widgety podane w `exclude` wraz z ich poddrzewem (używane dla fragmentów
    UI przebudowywanych dynamicznie, np. wykresu po zmianie roku).
    """
    if isinstance(widget, ttk.Combobox):
        return
    if exclude and widget in exclude:
        return
    try:
        widget.bind("<Button-1>", handler, add="+")
        widget.configure(cursor="hand2")
    except tk.TclError:
        pass
    for child in widget.winfo_children():  # type: ignore
        _bind_click_recursive(child, handler, exclude)


def fill_statystyki_tab(tab: Any, dark_mode: bool = False) -> None:
    """
    Wypełnia zakładkę Statystyki.

    Args:
        tab: Zakładka do wypełnienia
        dark_mode: Czy używać trybu ciemnego
    """
    # Wyczyść zakładkę
    for widget in tab.winfo_children():  # type: ignore
        widget.destroy()  # type: ignore

    # Kolory w zależności od trybu
    if dark_mode:
        bg_color = '#23272e'
        fg_color = '#f3f6fa'
        frame_bg = '#31343a'
    else:
        bg_color = '#f3f6fa'
        fg_color = '#23272e'
        frame_bg = '#ffffff'

    # Główny frame
    main_frame = tk.Frame(tab, bg=bg_color)  # type: ignore
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Tytuł i przycisk odświeżania
    header_frame = tk.Frame(main_frame, bg=bg_color)  # type: ignore
    header_frame.pack(pady=(20, 20))

    title_label = tk.Label(
        header_frame,
        text="Statystyki i Raporty",
        font=('Segoe UI', scale_font_size(24), 'bold'),
        bg=bg_color,
        fg=fg_color,
    )
    title_label.pack(side=tk.LEFT, padx=(0, 20))

    # Przycisk odświeżania
    refresh_button = tk.Button(
        header_frame,
        text="🔄 Odśwież statystyki",
        font=('Segoe UI', scale_font_size(11), 'bold'),
        bg='#2E7D32' if not dark_mode else '#1B5E20',
        fg='white',
        activebackground='#1B5E20' if not dark_mode else '#2E7D32',
        activeforeground='white',
        relief='raised',
        cursor='hand2',
        padx=15,
        pady=8,
        command=lambda: fill_statystyki_tab(tab, dark_mode),  # type: ignore
    )
    refresh_button.pack(side=tk.LEFT)

    # Canvas z scrollbarem dla całej zawartości
    canvas_frame = tk.Frame(main_frame, bg=bg_color)  # type: ignore
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

    main_canvas = tk.Canvas(canvas_frame, bg=bg_color, highlightthickness=0)  # type: ignore
    main_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=main_canvas.yview)  # type: ignore
    scrollable_main = tk.Frame(main_canvas, bg=bg_color)  # type: ignore

    scrollable_main.bind(
        "<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    )

    main_canvas.create_window((0, 0), window=scrollable_main, anchor="nw")
    main_canvas.configure(yscrollcommand=main_scrollbar.set)

    main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Przewijanie kółkiem myszy w dowolnym miejscu zakładki (nie tylko nad paskiem bocznym).
    # Bindowanie/odbindowanie globalne przy wejściu/wyjściu kursora nad obszarem canvas_frame,
    # aby nie przechwytywać scrolla z innych zakładek/okien.
    def _on_mousewheel(event: Any) -> None:
        if main_canvas.winfo_exists():
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel(_event: Any = None) -> None:
        canvas_frame.bind_all("<MouseWheel>", _on_mousewheel)

    def _unbind_mousewheel(_event: Any = None) -> None:
        canvas_frame.unbind_all("<MouseWheel>")

    canvas_frame.bind("<Enter>", _bind_mousewheel)
    canvas_frame.bind("<Leave>", _unbind_mousewheel)

    # Kontener dla siatki statystyk (3 kolumny)
    grid_container = tk.Frame(scrollable_main, bg=bg_color)  # type: ignore
    grid_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Konfiguracja kolumn - stała siatka 3 kolumn. Kolejne statystyki są
    # umieszczane przez _next_stat_cell(), które zawija je po 3 do nowego
    # wiersza — niezależnie od tego, ile statystyk będzie w przyszłości,
    # w oknie zawsze mieści się dokładnie jeden wiersz (3 statystyki) na raz,
    # a reszta jest dostępna przez istniejący scroll pionowy zakładki.
    STAT_GRID_COLUMNS = 3
    grid_container.columnconfigure(0, weight=1, minsize=280)  # Wykres kołowy
    grid_container.columnconfigure(1, weight=1, minsize=280)  # MG vs Gracz
    grid_container.columnconfigure(2, weight=3, minsize=520)  # Systemy - więcej miejsca

    _stat_index = 0

    def _next_stat_cell() -> tuple[int, int]:
        """Zwraca (wiersz, kolumna) kolejnej statystyki, zawijając po 3 kolumnach."""
        nonlocal _stat_index
        row, col = divmod(_stat_index, STAT_GRID_COLUMNS)
        grid_container.rowconfigure(row, weight=1, minsize=500)
        _stat_index += 1
        return row, col

    def _open_stat_detail_dialog(
        title: str, builder: Callable[[tk.Frame, bool], None]
    ) -> None:
        """Otwiera powiększone okno pojedynczej statystyki (pełny wykres, bez przycięć)."""
        root = tab.winfo_toplevel()
        dialog = create_ctk_toplevel(root)
        dialog.title(title)
        dialog.resizable(True, True)  # odblokowuje też przycisk maksymalizacji
        dialog.transient(root)
        apply_safe_geometry(dialog, root, 1000, 820)
        dialog.after(50, lambda: enable_maximize_button(dialog))

        dialog_bg = tk.Frame(dialog, bg=bg_color)  # type: ignore
        dialog_bg.pack(fill=tk.BOTH, expand=True)

        detail_canvas = tk.Canvas(dialog_bg, bg=bg_color, highlightthickness=0)  # type: ignore
        detail_scrollbar = ttk.Scrollbar(dialog_bg, orient="vertical", command=detail_canvas.yview)  # type: ignore
        detail_content = tk.Frame(detail_canvas, bg=frame_bg, relief='solid', borderwidth=1)  # type: ignore

        detail_content.bind(
            "<Configure>", lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox("all"))
        )
        detail_canvas.create_window((0, 0), window=detail_content, anchor="nw")
        detail_canvas.configure(yscrollcommand=detail_scrollbar.set)
        detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_detail_wheel(event: Any) -> None:
            if detail_canvas.winfo_exists():
                detail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_detail_wheel(_e: Any = None) -> None:
            detail_canvas.bind_all("<MouseWheel>", _on_detail_wheel)

        def _unbind_detail_wheel(_e: Any = None) -> None:
            detail_canvas.unbind_all("<MouseWheel>")

        dialog_bg.bind("<Enter>", _bind_detail_wheel)
        dialog_bg.bind("<Leave>", _unbind_detail_wheel)
        dialog.protocol("WM_DELETE_WINDOW", lambda: (_unbind_detail_wheel(), dialog.destroy()))

        builder(detail_content, True)

    def _build_year_pie_module(parent: tk.Frame, expanded: bool = False) -> None:
        """Buduje statystykę 'Sesje wg roku' — używane dla karty i powiększonego okna."""
        title_font = 18 if expanded else 14
        body_font = 14 if expanded else 12
        small_font = 13 if expanded else 11

        def _open_dialog(_e: Any = None) -> None:
            _open_stat_detail_dialog(
                "📊 Liczba sesji RPG przeprowadzonych w poszczególnych latach",
                _build_year_pie_module,
            )

        stats_title = tk.Label(
            parent,
            text="📊 Liczba sesji RPG przeprowadzonych w poszczególnych latach",
            font=('Segoe UI', scale_font_size(title_font), 'bold'),
            bg=frame_bg,
            fg=fg_color,
            wraplength=0 if expanded else 240,
            justify='center',
        )
        stats_title.pack(pady=(15, 10))

        stats_loading_label = tk.Label(
            parent,
            text="⏳ Ładowanie danych...",
            font=('Segoe UI', scale_font_size(body_font)),
            bg=frame_bg,
            fg=fg_color,
        )
        stats_loading_label.pack(pady=30)

        def _fetch_year_stats() -> None:
            """Pobiera i agreguje dane sesji po roku w wątku tła."""
            try:
                with sqlite3.connect(get_db_path("sesje_rpg.db")) as conn:
                    c = conn.cursor()
                    c.execute("SELECT data_sesji FROM sesje_rpg")
                    rows = c.fetchall()

                year_counts: Dict[str, int] = defaultdict(int)
                for row in rows:
                    date_str = row[0]
                    if '.' in date_str:
                        parts = date_str.split('.')
                        if len(parts) == 3:
                            year_counts[parts[2]] += 1
                    elif '-' in date_str:
                        parts = date_str.split('-')
                        if len(parts) == 3:
                            year_counts[parts[0]] += 1

                sorted_years: List[str] = sorted(year_counts.keys(), reverse=True)
                parent.after(0, lambda: _render_year_stats(sorted_years, year_counts))
            except Exception as exc:
                parent.after(0, lambda e=exc: _show_year_stats_error(str(e)))

        def _render_year_stats(sorted_years: List[str], year_counts: Dict[str, int]) -> None:
            """Buduje wykres kołowy sesji po roku w wątku głównym."""
            stats_loading_label.destroy()
            if sorted_years:
                chart_frame = tk.Frame(parent, bg=frame_bg)  # type: ignore
                chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 15))

                total_sessions = sum(year_counts.values())

                colors = [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                    '#9966FF', '#FF9F40', '#C9CBCF', '#FF9F40',
                ]

                years_data = list(sorted_years)
                counts_data = [year_counts[y] for y in years_data]

                legend_frame = tk.Frame(chart_frame, bg=frame_bg)  # type: ignore
                legend_frame.pack(fill=tk.X, pady=(5, 0))

                legend_inner = tk.Frame(legend_frame, bg=frame_bg)  # type: ignore
                legend_inner.pack(anchor='center')

                box_size = 24 if expanded else 20
                for idx, year in enumerate(years_data):
                    count = year_counts[year]
                    percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
                    color = colors[idx % len(colors)]

                    legend_item = tk.Frame(legend_inner, bg=frame_bg)  # type: ignore
                    legend_item.pack(fill=tk.X, pady=3)

                    color_box = tk.Canvas(legend_item, width=box_size, height=box_size, bg=frame_bg, highlightthickness=0)  # type: ignore
                    color_box.create_rectangle(2, 2, box_size - 2, box_size - 2, fill=color, outline='white')
                    color_box.pack(side=tk.LEFT, padx=(0, 8))

                    legend_text = tk.Label(
                        legend_item,
                        text=f"{year}: {count} sesji ({percentage:.1f}%)",
                        font=('Segoe UI', scale_font_size(small_font)),
                        bg=frame_bg,
                        fg=fg_color,
                        anchor='w',
                    )
                    legend_text.pack(side=tk.LEFT)

                fig_size = (8.5, 7.0) if expanded else (4.2, 3.5)
                fig = Figure(figsize=fig_size, dpi=100)
                fig.patch.set_facecolor(frame_bg)
                ax = fig.add_subplot(111)
                ax.set_facecolor(frame_bg)

                wedges, texts, autotexts = ax.pie(  # type: ignore
                    counts_data,
                    labels=years_data,
                    colors=colors[: len(years_data)],
                    autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
                    startangle=90,
                    explode=[0.02] * len(years_data),
                    shadow=True,
                    textprops={'fontsize': scale_font_size(small_font), 'color': fg_color},
                )

                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')

                ax.set_title(
                    'Sesje RPG według roku',
                    fontsize=scale_font_size(small_font),
                    fontweight='bold',
                    color=fg_color,
                    pad=5,
                )

                canvas_widget = FigureCanvasTkAgg(fig, chart_frame)
                canvas_widget.draw()
                canvas_widget.get_tk_widget().pack(pady=(5, 0))

                summary_label = tk.Label(
                    parent,
                    text=f"Łącznie: {total_sessions} sesji w {len(sorted_years)} latach",
                    font=('Segoe UI', scale_font_size(body_font), 'bold'),
                    bg=frame_bg,
                    fg=fg_color,
                )
                summary_label.pack(pady=(5, 15))
            else:
                no_data_label = tk.Label(
                    parent,
                    text="Brak danych do wyświetlenia",
                    font=('Segoe UI', scale_font_size(body_font)),
                    bg=frame_bg,
                    fg=fg_color,
                )
                no_data_label.pack(pady=30)

            if not expanded:
                _bind_click_recursive(parent, _open_dialog)

        def _show_year_stats_error(msg: str) -> None:
            stats_loading_label.destroy()
            error_label = tk.Label(
                parent,
                text=f"Błąd podczas pobierania danych:\n{msg}",
                font=('Segoe UI', scale_font_size(body_font)),
                bg=frame_bg,
                fg='#CC0000',
            )
            error_label.pack(pady=30)
            if not expanded:
                _bind_click_recursive(parent, _open_dialog)

        threading.Thread(target=_fetch_year_stats, daemon=True).start()

    def _build_user_stats_module(parent: tk.Frame, expanded: bool = False) -> None:
        """Buduje statystykę 'MG vs Gracz' — używane dla karty i powiększonego okna."""
        title_font = 18 if expanded else 14
        body_font = 14 if expanded else 12
        small_font = 13 if expanded else 10

        def _open_dialog(_e: Any = None) -> None:
            _open_stat_detail_dialog(
                "👤 Główny użytkownik: Mistrz Gry vs Gracz", _build_user_stats_module
            )

        user_stats_title = tk.Label(
            parent,
            text="👤 Główny użytkownik: Mistrz Gry vs Gracz",
            font=('Segoe UI', scale_font_size(title_font), 'bold'),
            bg=frame_bg,
            fg=fg_color,
        )
        user_stats_title.pack(pady=(15, 10))

        user_stats_loading_label = tk.Label(
            parent,
            text="⏳ Ładowanie danych...",
            font=('Segoe UI', scale_font_size(body_font)),
            bg=frame_bg,
            fg=fg_color,
        )
        user_stats_loading_label.pack(pady=30)

        def _parse_year(date_str: str) -> Optional[str]:
            """Wyciąga rok z daty w formacie DD.MM.YYYY lub YYYY-MM-DD."""
            if '.' in date_str:
                parts = date_str.split('.')
                if len(parts) == 3:
                    return parts[2]
            elif '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3:
                    return parts[0]
            return None

        def _fetch_user_stats() -> None:
            """Pobiera dane głównego użytkownika (MG vs Gracz) w wątku tła."""
            try:
                with sqlite3.connect(get_db_path("gracze.db")) as conn_gracze:
                    c_gracze = conn_gracze.cursor()
                    c_gracze.execute("SELECT id, nick FROM gracze WHERE glowny_uzytkownik = 1")
                    main_user = c_gracze.fetchone()

                if not main_user:
                    parent.after(0, _render_no_main_user)
                    return

                main_user_id, main_user_nick = main_user[0], main_user[1]

                with sqlite3.connect(get_db_path("sesje_rpg.db")) as conn_sesje:
                    c_sesje = conn_sesje.cursor()

                    c_sesje.execute(
                        "SELECT data_sesji FROM sesje_rpg WHERE mg_id = ?", (main_user_id,)
                    )
                    mg_sessions = c_sesje.fetchall()

                    c_sesje.execute(
                        """
                        SELECT s.data_sesji
                        FROM sesje_rpg s
                        JOIN sesje_gracze sg ON s.id = sg.sesja_id
                        WHERE sg.gracz_id = ?
                        """,
                        (main_user_id,),
                    )
                    player_sessions = c_sesje.fetchall()

                mg_by_year: Dict[str, int] = defaultdict(int)
                for row in mg_sessions:
                    year = _parse_year(row[0])
                    if year:
                        mg_by_year[year] += 1

                player_by_year: Dict[str, int] = defaultdict(int)
                for row in player_sessions:
                    year = _parse_year(row[0])
                    if year:
                        player_by_year[year] += 1

                all_years: Set[str] = set(mg_by_year.keys()) | set(player_by_year.keys())
                parent.after(
                    0,
                    lambda: _render_user_stats(main_user_nick, mg_by_year, player_by_year, all_years),
                )
            except Exception as exc:
                parent.after(0, lambda e=exc: _show_user_stats_error(str(e)))

        def _render_no_main_user() -> None:
            user_stats_loading_label.destroy()
            no_user_label = tk.Label(
                parent,
                text="Nie znaleziono głównego użytkownika",
                font=('Segoe UI', scale_font_size(body_font)),
                bg=frame_bg,
                fg=fg_color,
            )
            no_user_label.pack(pady=30)
            if not expanded:
                _bind_click_recursive(parent, _open_dialog)

        def _render_user_stats(
            main_user_nick: str,
            mg_by_year: Dict[str, int],
            player_by_year: Dict[str, int],
            all_years: Set[str],
        ) -> None:
            """Buduje UI (nick, wykres, lista lat) w wątku głównym."""
            user_stats_loading_label.destroy()

            if not all_years:
                no_sessions_label = tk.Label(
                    parent,
                    text=f"Główny użytkownik '{main_user_nick}' nie ma jeszcze żadnych sesji",
                    font=('Segoe UI', scale_font_size(body_font)),
                    bg=frame_bg,
                    fg=fg_color,
                )
                no_sessions_label.pack(pady=30)
                if not expanded:
                    _bind_click_recursive(parent, _open_dialog)
                return

            nick_label = tk.Label(
                parent,
                text=f"Nick: {main_user_nick}",
                font=('Segoe UI', scale_font_size(body_font), 'italic'),
                bg=frame_bg,
                fg=fg_color,
            )
            nick_label.pack(pady=(0, 10))

            year_selector_frame = tk.Frame(parent, bg=frame_bg)  # type: ignore
            year_selector_frame.pack(pady=(0, 10))

            year_label_select = tk.Label(
                year_selector_frame,
                text="Wybierz rok:",
                font=('Segoe UI', scale_font_size(small_font + 1)),
                bg=frame_bg,
                fg=fg_color,
            )
            year_label_select.pack(side=tk.LEFT, padx=(0, 10))

            sorted_years_user: List[str] = sorted(all_years, reverse=True)
            year_var_user = tk.StringVar(value=str(sorted_years_user[0]))  # type: ignore
            year_combo_user = ttk.Combobox(
                year_selector_frame,
                textvariable=year_var_user,
                values=sorted_years_user,  # type: ignore
                state='readonly',
                width=10,
                font=('Segoe UI', scale_font_size(small_font)),
            )
            year_combo_user.pack(side=tk.LEFT)

            content_frame = tk.Frame(parent, bg=frame_bg)  # type: ignore
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

            def update_user_chart(*args: object) -> None:
                """Aktualizuje wykres po zmianie roku"""
                for widget in content_frame.winfo_children():
                    widget.destroy()

                selected_year = year_var_user.get()
                year_mg = mg_by_year.get(selected_year, 0)
                year_player = player_by_year.get(selected_year, 0)

                if year_mg > 0 or year_player > 0:
                    fig_size = (7.0, 6.0) if expanded else (3.5, 3)
                    fig2 = Figure(figsize=fig_size, dpi=100)
                    fig2.patch.set_facecolor(frame_bg)
                    ax2 = fig2.add_subplot(111)
                    ax2.set_facecolor(frame_bg)

                    mg_color = '#2196F3' if not dark_mode else '#64B5F6'
                    player_color = '#4CAF50' if not dark_mode else '#81C784'

                    sizes = [year_mg, year_player]
                    labels = ['MG', 'Gracz']
                    colors_pie = [mg_color, player_color]
                    explode = (0.05, 0.05)

                    wedges, texts, autotexts = ax2.pie(  # type: ignore
                        sizes,
                        labels=labels,
                        colors=colors_pie,
                        autopct=lambda pct: f'{pct:.1f}%' if pct > 0 else '',
                        startangle=90,
                        explode=explode,
                        shadow=True,
                        textprops={'fontsize': scale_font_size(small_font), 'color': fg_color},
                    )

                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')

                    ax2.set_title(
                        'MG vs Gracz',
                        fontsize=scale_font_size(small_font + 1),
                        fontweight='bold',
                        color=fg_color,
                        pad=5,
                    )

                    canvas_widget2 = FigureCanvasTkAgg(fig2, content_frame)
                    canvas_widget2.draw()
                    canvas_widget2.get_tk_widget().pack()
                else:
                    no_data_label = tk.Label(
                        content_frame,
                        text=f"Brak sesji w roku {selected_year}",
                        font=('Segoe UI', scale_font_size(small_font + 1)),
                        bg=frame_bg,
                        fg=fg_color,
                    )
                    no_data_label.pack(pady=20)

                if not expanded:
                    for child in content_frame.winfo_children():
                        _bind_click_recursive(child, _open_dialog)

            year_combo_user.bind('<<ComboboxSelected>>', update_user_chart)
            update_user_chart()

            user_results_frame = tk.Frame(parent, bg=frame_bg)  # type: ignore
            user_results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

            canvas_height = 350 if expanded else 150
            user_canvas = tk.Canvas(user_results_frame, bg=frame_bg, highlightthickness=0, height=canvas_height)  # type: ignore
            user_scrollbar = ttk.Scrollbar(user_results_frame, orient="vertical", command=user_canvas.yview)  # type: ignore
            user_scrollable_frame = tk.Frame(user_canvas, bg=frame_bg)  # type: ignore

            user_scrollable_frame.bind(
                "<Configure>",
                lambda e: user_canvas.configure(scrollregion=user_canvas.bbox("all")),
            )

            user_canvas.create_window((0, 0), window=user_scrollable_frame, anchor="nw")
            user_canvas.configure(yscrollcommand=user_scrollbar.set)

            user_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            for year in sorted_years_user:
                mg_count = mg_by_year[year]
                player_count = player_by_year[year]
                year_total = mg_count + player_count
                mg_pct = (mg_count / year_total * 100) if year_total > 0 else 0
                player_pct = (player_count / year_total * 100) if year_total > 0 else 0

                year_frame = tk.Frame(user_scrollable_frame, bg=frame_bg)  # type: ignore
                year_frame.pack(fill=tk.X, pady=2, padx=5)

                year_label = tk.Label(
                    year_frame,
                    text=f"{year}:",
                    font=('Segoe UI', scale_font_size(small_font + 1), 'bold'),
                    bg=frame_bg,
                    fg=fg_color,
                    width=6,
                    anchor='w',
                )
                year_label.pack(side=tk.LEFT, padx=(0, 5))

                mg_label = tk.Label(
                    year_frame,
                    text=f"🎲 MG: {mg_count} ({mg_pct:.1f}%)",
                    font=('Segoe UI', scale_font_size(small_font)),
                    bg=frame_bg,
                    fg='#2196F3' if not dark_mode else '#64B5F6',
                    width=16,
                    anchor='w',
                )
                mg_label.pack(side=tk.LEFT, padx=(0, 5))

                player_label = tk.Label(
                    year_frame,
                    text=f"👥 Gracz: {player_count} ({player_pct:.1f}%)",
                    font=('Segoe UI', scale_font_size(small_font)),
                    bg=frame_bg,
                    fg='#4CAF50' if not dark_mode else '#81C784',
                    width=18,
                    anchor='w',
                )
                player_label.pack(side=tk.LEFT)

            total_mg_all = sum(mg_by_year.values())
            total_player_all = sum(player_by_year.values())
            summary_user_label = tk.Label(
                parent,
                text=(
                    f"Łącznie: {total_mg_all} sesji jako MG,"
                    f" {total_player_all} sesji jako Gracz"
                ),
                font=('Segoe UI', scale_font_size(body_font), 'bold'),
                bg=frame_bg,
                fg=fg_color,
            )
            summary_user_label.pack(pady=(5, 15))

            if not expanded:
                _bind_click_recursive(parent, _open_dialog, exclude={content_frame})

        def _show_user_stats_error(msg: str) -> None:
            user_stats_loading_label.destroy()
            user_error_label = tk.Label(
                parent,
                text=f"Błąd podczas pobierania danych:\n{msg}",
                font=('Segoe UI', scale_font_size(body_font)),
                bg=frame_bg,
                fg='#CC0000',
            )
            user_error_label.pack(pady=30)
            if not expanded:
                _bind_click_recursive(parent, _open_dialog)

        threading.Thread(target=_fetch_user_stats, daemon=True).start()

    def _build_system_sessions_module(parent: tk.Frame, expanded: bool = False) -> None:
        """Buduje statystykę 'Systemy RPG: ilość sesji' — dla karty i powiększonego okna."""
        title_font = 18 if expanded else 14
        body_font = 14 if expanded else 11
        small_font = 13 if expanded else 10

        def _open_dialog(_e: Any = None) -> None:
            _open_stat_detail_dialog("🎮 Systemy RPG: Ilość sesji", _build_system_sessions_module)

        system_sessions_title = tk.Label(
            parent,
            text="🎮 Systemy RPG: Ilość sesji",
            font=('Segoe UI', scale_font_size(title_font), 'bold'),
            bg=frame_bg,
            fg=fg_color,
        )
        system_sessions_title.pack(pady=(15, 10))

        year_selector_frame = tk.Frame(parent, bg=frame_bg)  # type: ignore
        year_selector_frame.pack(pady=(0, 10))

        year_label = tk.Label(
            year_selector_frame,
            text="Wybierz rok:",
            font=('Segoe UI', scale_font_size(small_font + 1)),
            bg=frame_bg,
            fg=fg_color,
        )
        year_label.pack(side=tk.LEFT, padx=(0, 10))

        try:
            with sqlite3.connect(get_db_path("sesje_rpg.db")) as conn_years:
                c_years = conn_years.cursor()
                c_years.execute(
                    "SELECT DISTINCT data_sesji FROM sesje_rpg ORDER BY data_sesji DESC"
                )
                all_dates = c_years.fetchall()

            available_years: Set[str] = set()
            for row in all_dates:
                date_str = row[0]
                if '.' in date_str:
                    parts = date_str.split('.')
                    if len(parts) == 3:
                        available_years.add(parts[2])
                elif '-' in date_str:
                    parts = date_str.split('-')
                    if len(parts) == 3:
                        available_years.add(parts[0])

            sorted_years_list = sorted(available_years, reverse=True)

            if not sorted_years_list:
                no_years_label = tk.Label(
                    parent,
                    text="Brak danych o sesjach",
                    font=('Segoe UI', scale_font_size(body_font)),
                    bg=frame_bg,
                    fg=fg_color,
                )
                no_years_label.pack(pady=30)
                if not expanded:
                    _bind_click_recursive(parent, _open_dialog)
                return

            year_var = tk.StringVar(value=sorted_years_list[0])
            year_combo = ttk.Combobox(
                year_selector_frame,
                textvariable=year_var,
                values=sorted_years_list,
                state="readonly",
                width=10,
                font=('Segoe UI', scale_font_size(small_font)),
            )
            year_combo.pack(side=tk.LEFT)

            chart_system_frame = tk.Frame(parent, bg=frame_bg)  # type: ignore
            if not expanded:
                chart_system_frame.pack_propagate(False)  # nie pozwól canvas rozciągać ramki
            chart_system_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 15))

            if not expanded:
                _bind_click_recursive(parent, _open_dialog)

            def update_system_chart(*args: object) -> None:
                """Aktualizuje wykres po zmianie roku"""
                for widget in chart_system_frame.winfo_children():
                    widget.destroy()

                selected_year = year_var.get()

                def _fetch() -> None:
                    """Pobiera dane SQL w wątku tła, naprawia N+1 query."""
                    try:
                        with sqlite3.connect(get_db_path("sesje_rpg.db")) as _conn_s:
                            _conn_s.row_factory = sqlite3.Row
                            _c_s = _conn_s.cursor()
                            _c_s.execute(
                                "SELECT system_id FROM sesje_rpg WHERE data_sesji LIKE ?",
                                (f"%{selected_year}%",),
                            )
                            sessions_data = _c_s.fetchall()

                        system_id_counts: Dict[int, int] = defaultdict(int)
                        for row in sessions_data:
                            if row[0]:
                                system_id_counts[row[0]] += 1

                        sorted_result: Optional[List] = None
                        if system_id_counts:
                            ids_ph = ",".join("?" * len(system_id_counts))
                            with sqlite3.connect(get_db_path("systemy_rpg.db")) as _conn_sys:
                                _conn_sys.row_factory = sqlite3.Row
                                _c_sys = _conn_sys.cursor()
                                _c_sys.execute(
                                    f"SELECT id, nazwa FROM systemy_gry"
                                    f" WHERE id IN ({ids_ph})",
                                    list(system_id_counts.keys()),
                                )
                                names_map = {row[0]: row[1] for row in _c_sys.fetchall()}

                            system_counts_map = {
                                names_map.get(sid, f"System ID {sid}"): cnt
                                for sid, cnt in system_id_counts.items()
                            }
                            sorted_result = sorted(
                                system_counts_map.items(),
                                key=lambda x: x[1],
                                reverse=True,
                            )

                        chart_system_frame.after(0, lambda r=sorted_result: _render(r))
                    except Exception as exc:
                        chart_system_frame.after(0, lambda e=exc: _show_error(str(e)))

                def _render(sorted_systems: Optional[List]) -> None:
                    """Buduje wykres w wątku głównym."""
                    for widget in chart_system_frame.winfo_children():
                        widget.destroy()
                    chart_system_frame.update_idletasks()
                    if sorted_systems:
                        systems = [s[0] for s in reversed(sorted_systems)]
                        counts = [s[1] for s in reversed(sorted_systems)]
                        colors_bar = [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#C9CBCF', '#8B5CF6',
                        ]
                        bar_colors = [
                            colors_bar[i % len(colors_bar)] for i in range(len(systems))
                        ]

                        if expanded:
                            # Wysokość figury skalowana do liczby systemów zamiast
                            # dopasowania do stałej ramki — bez przycinania/nakładania
                            # etykiet przy dużej liczbie zagregowanych danych.
                            _fig_w = 9.0
                            _fig_h = max(4.0, 0.45 * len(systems) + 1.5)
                        else:
                            _avail_w = max(chart_system_frame.winfo_width(), 400)
                            _avail_h = max(chart_system_frame.winfo_height(), 300)
                            _dpi = 100
                            _fig_w = _avail_w / _dpi
                            _fig_h = max(2.5, (_avail_h - 40) / _dpi)

                        fig3 = Figure(figsize=(_fig_w, _fig_h), dpi=100)
                        fig3.patch.set_facecolor(frame_bg)
                        ax3 = fig3.add_subplot(111)
                        ax3.set_facecolor(frame_bg)
                        y_pos = range(len(systems))
                        bars = ax3.barh(
                            y_pos, counts, color=bar_colors, edgecolor='white', linewidth=1.5
                        )
                        ax3.set_yticks(y_pos)
                        ax3.set_yticklabels(
                            systems, fontsize=scale_font_size(small_font - 1), color=fg_color
                        )
                        ax3.set_xlabel(
                            'Ilość sesji',
                            fontsize=scale_font_size(small_font),
                            color=fg_color,
                            fontweight='bold',
                        )
                        # Tytuł przez suptitle — zawsze wyśrodkowany względem figury,
                        # nie względem osi (oś jest przesunięta w lewo przez długie etykiety Y)
                        fig3.suptitle(
                            f'Sesje według systemów w {selected_year}',
                            fontsize=scale_font_size(small_font + 1),
                            fontweight='bold',
                            color=fg_color,
                            x=0.5,
                            y=0.98,
                        )
                        ax3.tick_params(axis='x', colors=fg_color)
                        ax3.tick_params(axis='y', colors=fg_color)
                        ax3.spines['bottom'].set_color(fg_color)
                        ax3.spines['left'].set_color(fg_color)
                        ax3.spines['top'].set_visible(False)
                        ax3.spines['right'].set_visible(False)
                        for _i, (bar, count) in enumerate(zip(bars, counts)):
                            width = bar.get_width()
                            ax3.text(
                                width + 0.1,
                                bar.get_y() + bar.get_height() / 2,
                                str(count),
                                ha='left',
                                va='center',
                                fontweight='bold',
                                fontsize=scale_font_size(small_font - 1),
                                color=fg_color,
                            )
                        # rect zostawia miejsce u góry dla suptitle
                        fig3.tight_layout(rect=(0, 0, 1, 0.93))
                        total_system_sessions = sum(counts)
                        summary_system_label = tk.Label(
                            chart_system_frame,
                            text=(
                                f"Łącznie: {total_system_sessions} sesji"
                                f" w {len(systems)} systemach"
                            ),
                            font=('Segoe UI', scale_font_size(body_font), 'bold'),
                            bg=frame_bg,
                            fg=fg_color,
                        )
                        summary_system_label.pack(side=tk.BOTTOM, pady=(5, 10))
                        canvas_widget3 = FigureCanvasTkAgg(fig3, chart_system_frame)
                        canvas_widget3.draw()
                        if expanded:
                            # Bez fill/expand — figura ma naturalny rozmiar, nadmiar
                            # przewija zewnętrzny scroll okna szczegółów.
                            canvas_widget3.get_tk_widget().pack(pady=(0, 10))
                        else:
                            canvas_widget3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                    else:
                        no_data_system_label = tk.Label(
                            chart_system_frame,
                            text=f"Brak sesji w roku {selected_year}",
                            font=('Segoe UI', scale_font_size(body_font)),
                            bg=frame_bg,
                            fg=fg_color,
                        )
                        no_data_system_label.pack(pady=30)

                    if not expanded:
                        for child in chart_system_frame.winfo_children():
                            _bind_click_recursive(child, _open_dialog)

                def _show_error(msg: str) -> None:
                    for widget in chart_system_frame.winfo_children():
                        widget.destroy()
                    error_system_label = tk.Label(
                        chart_system_frame,
                        text=f"Błąd: {msg}",
                        font=('Segoe UI', scale_font_size(small_font)),
                        bg=frame_bg,
                        fg='#CC0000',
                    )
                    error_system_label.pack(pady=30)
                    if not expanded:
                        for child in chart_system_frame.winfo_children():
                            _bind_click_recursive(child, _open_dialog)

                threading.Thread(target=_fetch, daemon=True).start()

            year_var.trace_add('write', update_system_chart)
            update_system_chart()  # Inicjalne wywołanie

        except Exception as e:
            system_error_label = tk.Label(
                parent,
                text=f"Błąd podczas pobierania danych:\n{str(e)}",
                font=('Segoe UI', scale_font_size(body_font)),
                bg=frame_bg,
                fg='#CC0000',
            )
            system_error_label.pack(pady=30)
            if not expanded:
                _bind_click_recursive(parent, _open_dialog)

    # Statystyka 1: Sesje RPG po roku
    stats_frame = tk.Frame(grid_container, bg=frame_bg, relief='solid', borderwidth=1)  # type: ignore
    _row, _col = _next_stat_cell()
    stats_frame.grid(row=_row, column=_col, sticky="nsew", padx=10, pady=10)
    _build_year_pie_module(stats_frame, expanded=False)

    # Statystyka 2: Główny użytkownik jako MG vs Gracz
    user_stats_frame = tk.Frame(grid_container, bg=frame_bg, relief='solid', borderwidth=1)  # type: ignore
    _row, _col = _next_stat_cell()
    user_stats_frame.grid(row=_row, column=_col, sticky="nsew", padx=10, pady=10)
    _build_user_stats_module(user_stats_frame, expanded=False)

    # Statystyka 3: System/Ilość sesji w danym roku
    system_sessions_frame = tk.Frame(grid_container, bg=frame_bg, relief='solid', borderwidth=1)  # type: ignore
    _row, _col = _next_stat_cell()
    system_sessions_frame.grid(row=_row, column=_col, sticky="nsew", padx=10, pady=10)
    _build_system_sessions_module(system_sessions_frame, expanded=False)
