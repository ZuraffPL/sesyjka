import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
import sqlite3
import webbrowser
from typing import Optional, Callable, Sequence, Any, Union, List, Dict, Tuple
import customtkinter as ctk  # type: ignore
import logging
from database_manager import get_db_path
from font_scaling import scale_font_size
from dialog_utils import apply_safe_geometry, create_ctk_toplevel
from ctk_table import CTkDataTable

_log = logging.getLogger(__name__)
DB_FILE = get_db_path("gracze.db")

# Moduł: Gracze
# Tutaj będą funkcje i klasy związane z obsługą graczy

# Przechowuj aktywne filtry na poziomie modułu
active_filters_gracze: Dict[str, Any] = {}
# Przechowuj stan sortowania na poziomie modułu
active_sort_gracze: Dict[str, Any] = {"column": "ID", "reverse": False}


def get_dark_mode_from_tab(tab: tk.Widget) -> bool:
    root = tab.winfo_toplevel()
    return getattr(root, 'dark_mode', False)


def apply_dark_theme_to_dialog(dialog: tk.Toplevel) -> None:
    """Stosuje ciemny motyw do okna dialogowego"""
    dark_bg = "#2b2b2b"
    dark_fg = "#ffffff"
    dark_entry_bg = "#404040"
    dark_entry_fg = "#ffffff"

    # Główne okno
    dialog.configure(bg=dark_bg)

    # Wszystkie widgety w oknie
    for widget in dialog.winfo_children():
        _apply_dark_theme_to_widget(widget, dark_bg, dark_fg, dark_entry_bg, dark_entry_fg)


def _apply_dark_theme_to_widget(
    widget: Union[tk.Widget, tk.Toplevel],
    dark_bg: str,
    dark_fg: str,
    dark_entry_bg: str,
    dark_entry_fg: str,
) -> None:
    """Rekurencyjnie stosuje ciemny motyw do widgetów"""
    widget_class = widget.winfo_class()

    try:
        if widget_class in ('Label', 'Button', 'Checkbutton', 'Radiobutton'):
            widget.configure(bg=dark_bg, fg=dark_fg)  # type: ignore
            if widget_class in ('Checkbutton', 'Radiobutton'):
                widget.configure(selectcolor=dark_entry_bg, activebackground=dark_bg, activeforeground=dark_fg)  # type: ignore
        elif widget_class in ('Entry', 'Text'):
            widget.configure(
                bg=dark_entry_bg,
                fg=dark_entry_fg,  # type: ignore
                insertbackground=dark_entry_fg,
                selectbackground="#0078d4",
            )  # type: ignore
        elif widget_class == 'Frame':
            widget.configure(bg=dark_bg)  # type: ignore
        elif widget_class == 'Combobox':
            # Dla Combobox używamy ttk style
            pass

        # Rekurencyjnie dla dzieci
        for child in widget.winfo_children():
            _apply_dark_theme_to_widget(child, dark_bg, dark_fg, dark_entry_bg, dark_entry_fg)
    except tk.TclError:
        # Ignoruj błędy konfiguracji (niektóre widgety mogą nie obsługiwać pewnych opcji)
        _log.debug(
            "TclError w _apply_dark_theme_to_widget (ignorowany): %s", widget, exc_info=True
        )


def dodaj_gracza(
    parent: Optional[tk.Tk] = None, refresh_callback: Optional[Callable[..., None]] = None
) -> None:
    if parent is None:
        parent = tk._default_root  # type: ignore

    # Sprawdź tryb ciemny
    _dark_mode = parent and hasattr(parent, 'dark_mode') and getattr(parent, 'dark_mode', False)

    # Dialog CustomTkinter
    dialog = create_ctk_toplevel(parent)  # type: ignore
    dialog.title("Dodaj gracza do bazy")
    dialog.transient(parent)  # type: ignore
    dialog.resizable(True, True)

    if parent is not None:
        apply_safe_geometry(dialog, parent, 420, 380)

    # Główny frame
    main_frame = ctk.CTkFrame(dialog, fg_color="transparent")  # type: ignore
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # ID gracza
    ctk.CTkLabel(main_frame, text="ID gracza:", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=0, column=0, pady=(0, 10), padx=(0, 10), sticky="w")  # type: ignore
    id_entry = ctk.CTkEntry(main_frame, width=250, state="disabled")  # type: ignore
    id_entry.grid(row=0, column=1, pady=(0, 10), sticky="ew")
    id_entry.configure(state="normal")
    id_entry.insert(0, str(get_first_free_id()))
    id_entry.configure(state="disabled")

    # Nick gracza
    ctk.CTkLabel(main_frame, text="Nick gracza *", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=1, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    nick_entry = ctk.CTkEntry(main_frame, width=250, placeholder_text="Wpisz nick...")  # type: ignore
    nick_entry.grid(row=1, column=1, pady=8, sticky="ew")
    dialog.after(100, lambda: nick_entry.focus_set() if nick_entry.winfo_exists() else None)

    # Imię i nazwisko
    ctk.CTkLabel(main_frame, text="Imię i nazwisko", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    name_entry = ctk.CTkEntry(main_frame, width=250, placeholder_text="Opcjonalnie...")  # type: ignore
    name_entry.grid(row=2, column=1, pady=8, sticky="ew")

    # Płeć
    ctk.CTkLabel(main_frame, text="Płeć", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    gender_var = tk.StringVar(value="Kobieta")
    gender_combo = ctk.CTkComboBox(main_frame, width=250, values=["Kobieta", "Mężczyzna", "Niebinarna", "Inne"], variable=gender_var, state="readonly")  # type: ignore
    gender_combo.grid(row=3, column=1, pady=8, sticky="ew")

    # Social media
    ctk.CTkLabel(main_frame, text="Social media / strona", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=4, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    social_entry = ctk.CTkEntry(main_frame, width=250, placeholder_text="Link lub @nick...")  # type: ignore
    social_entry.grid(row=4, column=1, pady=8, sticky="ew")

    # Checkbox główny użytkownik
    glowny_var = tk.BooleanVar(value=False)
    wazna_var = tk.BooleanVar(value=False)

    def on_glowny_toggle() -> None:
        if glowny_var.get():
            wazna_var.set(False)
            wazna_check.deselect()  # type: ignore

    def on_wazna_toggle() -> None:
        if wazna_var.get():
            glowny_var.set(False)
            glowny_check.deselect()  # type: ignore

    glowny_check = ctk.CTkCheckBox(main_frame, text="⭐ Główny użytkownik (tylko jedna osoba)", variable=glowny_var, command=on_glowny_toggle, font=ctk.CTkFont(size=scale_font_size(11)))  # type: ignore
    glowny_check.grid(row=5, column=0, columnspan=2, pady=8, sticky="w")

    # Checkbox ważna osoba
    wazna_check = ctk.CTkCheckBox(main_frame, text="👑 Ważna osoba", variable=wazna_var, command=on_wazna_toggle, font=ctk.CTkFont(size=scale_font_size(11)))  # type: ignore
    wazna_check.grid(row=6, column=0, columnspan=2, pady=8, sticky="w")

    def on_ok() -> None:
        nick: str = nick_entry.get().strip()
        name: str = name_entry.get().strip()
        gender: str = gender_var.get()
        social: str = social_entry.get().strip()
        glowny: int = 1 if glowny_var.get() else 0
        wazna: int = 1 if wazna_var.get() else 0

        if not nick:
            messagebox.showerror("Błąd", "Nick gracza jest wymagany.", parent=dialog)  # type: ignore
            return

        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS gracze (
                    id INTEGER PRIMARY KEY,
                    nick TEXT NOT NULL,
                    imie_nazwisko TEXT,
                    plec TEXT,
                    social TEXT,
                    glowny_uzytkownik INTEGER DEFAULT 0,
                    wazna INTEGER DEFAULT 0
                )
            """
            )

            # Jeśli ustawiamy głównego użytkownika, usuń flagę z pozostałych
            if glowny == 1:
                c.execute("UPDATE gracze SET glowny_uzytkownik = 0")

            c.execute(
                "INSERT INTO gracze (nick, imie_nazwisko, plec, social,"
                " glowny_uzytkownik, wazna) VALUES (?, ?, ?, ?, ?, ?)",
                (nick, name if name else None, gender, social if social else None, glowny, wazna),
            )
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))  # type: ignore
        dialog.destroy()

    def on_cancel() -> None:
        dialog.destroy()

    # Przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")  # type: ignore
    btn_frame.grid(row=7, column=0, columnspan=2, pady=(15, 0))

    btn_ok = ctk.CTkButton(btn_frame, text="✚ Dodaj", command=on_ok, width=100, fg_color="#2E7D32", hover_color="#1B5E20", font=ctk.CTkFont(size=scale_font_size(12), weight="bold"))  # type: ignore
    btn_ok.pack(side=tk.LEFT, padx=(0, 10))
    btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100, fg_color="#666666", hover_color="#555555", font=ctk.CTkFont(size=scale_font_size(12)))  # type: ignore
    btn_cancel.pack(side=tk.LEFT)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)


def get_first_free_id() -> int:
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("SELECT id FROM gracze ORDER BY id ASC")
        used_ids = [row[0] for row in c.fetchall()]
    i = 1
    while i in used_ids:
        i += 1
    return i


def get_all_players() -> list[tuple[Any, ...]]:
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS gracze (
                id INTEGER PRIMARY KEY,
                nick TEXT NOT NULL,
                imie_nazwisko TEXT,
                plec TEXT,
                social TEXT,
                glowny_uzytkownik INTEGER DEFAULT 0,
                wazna INTEGER DEFAULT 0
            )
        """
        )
        # Migracja - dodaj kolumny jeśli nie istnieją
        try:
            c.execute("ALTER TABLE gracze ADD COLUMN glowny_uzytkownik INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Kolumna już istnieje
        try:
            c.execute("ALTER TABLE gracze ADD COLUMN wazna INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Kolumna już istnieje

        c.execute(
            "SELECT id, nick, imie_nazwisko, plec, social,"
            " glowny_uzytkownik, wazna FROM gracze ORDER BY id ASC"
        )
        return c.fetchall()


def fill_gracze_tab(
    tab: tk.Frame,
    dark_mode: bool = False,
    _preloaded_data: Optional[List[List[Any]]] = None,
) -> None:  # type: ignore
    """Główny widok graczy — tabela CTkDataTable."""

    # ── Szybka ścieżka: odśwież dane bez niszczenia całego UI ───────────────
    cache = getattr(tab, '_gracze_tab_cache', None)
    if (
        cache is not None
        and cache.get('table_ref') is not None
        and cache.get('dark_mode') == dark_mode
    ):
        try:
            if cache['table_ref'].winfo_exists():
                if _preloaded_data is None:

                    def _bg_fast_gr() -> None:
                        recs = get_all_players()
                        data: List[List[Any]] = []
                        for rec in recs:
                            status = "⭐" if rec[5] == 1 else ("👑" if rec[6] == 1 else "")
                            data.append(
                                [
                                    rec[0],
                                    rec[1] if rec[1] else "",
                                    rec[2] if rec[2] else "",
                                    rec[3] if rec[3] else "",
                                    rec[4] if rec[4] else "",
                                    status,
                                    rec[5],
                                    rec[6],
                                ]
                            )
                        tab.after(
                            0,
                            lambda: fill_gracze_tab(
                                tab, dark_mode, _preloaded_data=data
                            ),
                        )

                    threading.Thread(target=_bg_fast_gr, daemon=True).start()
                    return
                cache['data_ref'][0] = _preloaded_data
                cache['apply_fn']()
                return
        except Exception:
            pass
        del tab._gracze_tab_cache  # type: ignore[attr-defined]

    if _preloaded_data is None:

        def _bg_full_gr() -> None:
            recs = get_all_players()
            data: List[List[Any]] = []
            for rec in recs:
                status = "⭐" if rec[5] == 1 else ("👑" if rec[6] == 1 else "")
                data.append(
                    [
                        rec[0],
                        rec[1] if rec[1] else "",
                        rec[2] if rec[2] else "",
                        rec[3] if rec[3] else "",
                        rec[4] if rec[4] else "",
                        status,
                        rec[5],  # glowny_uzytkownik int (ukryty)
                        rec[6],  # wazna int (ukryty)
                    ]
                )
            tab.after(
                0,
                lambda: fill_gracze_tab(tab, dark_mode, _preloaded_data=data),
            )

        threading.Thread(target=_bg_full_gr, daemon=True).start()
        return

    for widget in tab.winfo_children():
        widget.destroy()

    # Buduj 8-polowe wiersze: [id, nick, imie, plec, social, emoji, glowny_int, wazna_int]
    data_ref: List[List[List[Any]]] = [_preloaded_data]

    _HEADERS = ["ID", "Nick", "Imię i nazwisko", "Płeć", "Social media", "Status"]
    _SORTABLE = {
        "ID": 0,
        "Nick": 1,
        "Imię i nazwisko": 2,
        "Płeć": 3,
        "Social media": 4,
        "Status": 5,
    }

    # ── Obliczanie szerokości kolumn ─────────────────────────────────────────
    _mf = tkfont.Font(family="Segoe UI", size=scale_font_size(10))
    _mf_bold = tkfont.Font(family="Segoe UI", size=scale_font_size(10), weight="bold")

    def _compute_widths(rows: List[List[Any]]) -> List[int]:
        pad = 24
        w_nick = (
            max(
                [_mf_bold.measure("Nick")]
                + ([_mf.measure(str(r[1])) for r in rows if r[1]] or [0])
            )
            + pad
        )
        w_imie = (
            max(
                [_mf_bold.measure("Imię i nazwisko")]
                + ([_mf.measure(str(r[2])) for r in rows if r[2]] or [0])
            )
            + pad
        )
        w_plec = (
            max(
                [_mf_bold.measure("Płeć")]
                + ([_mf.measure(str(r[3])) for r in rows if r[3]] or [0])
            )
            + pad
        )
        w_social = (
            max(
                [_mf_bold.measure("Social media")]
                + ([_mf.measure(str(r[4])) for r in rows if r[4]] or [0])
            )
            + pad
        )
        return [
            44,
            min(max(w_nick, 80), 200),
            min(max(w_imie, 120), 280),
            min(max(w_plec, 70), 110),
            min(max(w_social, 100), 380),
            56,
        ]

    # ── Kolorowanie wierszy (płeć + status, status ma priorytet) ─────────────
    def _row_color(i: int, row: List[Any]) -> Optional[Tuple[Optional[str], Optional[str]]]:
        status = row[5] if len(row) > 5 else ""
        gender = row[3] if len(row) > 3 else ""
        if dark_mode:
            if status == "⭐":
                return ("#4a4a1a", None)
            elif status == "👑":
                return ("#3a1a4a", None)
            dgc: Dict[str, str] = {
                "Kobieta": "#4a1a3a",
                "Mężczyzna": "#1a3a4a",
                "Niebinarna": "#4a3a1a",
                "Inne": "#3a1a4a",
            }
            return (dgc.get(gender), None)
        else:
            if status == "⭐":
                return ("#fff9e6", None)
            elif status == "👑":
                return ("#f0e6ff", None)
            lgc: Dict[str, str] = {
                "Kobieta": "#ffe6f0",
                "Mężczyzna": "#e6f3ff",
                "Niebinarna": "#fff2e6",
                "Inne": "#f0e6ff",
            }
            return (lgc.get(gender), None)

    # ── Stan ─────────────────────────────────────────────────────────────────
    bg_top = "#1e1e2e" if dark_mode else "#f5f5f5"
    fg_top = "#e0e0e0" if dark_mode else "#212121"
    FONT = ("Segoe UI", scale_font_size(10))
    displayed_data: List[List[Any]] = []
    _table: List[Optional[CTkDataTable]] = [None]
    search_var: tk.StringVar = tk.StringVar()

    # ── Filtry + sortowanie ──────────────────────────────────────────────────
    def _apply_and_draw() -> None:
        nonlocal displayed_data
        filtered: List[List[Any]] = list(data_ref[0])

        phrase = search_var.get().strip().lower()
        if phrase:
            filtered = [
                r
                for r in filtered
                if phrase in (str(r[1]) or '').lower() or phrase in (str(r[2]) or '').lower()
            ]

        # Filtr płci
        if active_filters_gracze.get('plec', 'Wszystkie') != 'Wszystkie':
            filtered = [r for r in filtered if r[3] == active_filters_gracze['plec']]

        # Filtr imię i nazwisko
        imie_f = active_filters_gracze.get('imie', 'Wszystkie')
        if imie_f == 'Wpisane':
            filtered = [r for r in filtered if r[2] and str(r[2]).strip()]
        elif imie_f == 'Puste':
            filtered = [r for r in filtered if not r[2] or not str(r[2]).strip()]

        # Filtr social media
        social_f = active_filters_gracze.get('social', 'Wszystkie')
        if social_f == 'Wpisane':
            filtered = [r for r in filtered if r[4] and str(r[4]).strip()]
        elif social_f == 'Puste':
            filtered = [r for r in filtered if not r[4] or not str(r[4]).strip()]

        # Filtr status
        status_f = active_filters_gracze.get('status', 'Wszystkie')
        if status_f == 'Główny użytkownik':
            filtered = [r for r in filtered if r[5] == "⭐"]
        elif status_f == 'Ważna osoba':
            filtered = [r for r in filtered if r[5] == "👑"]
        elif status_f == 'Zwykła osoba':
            filtered = [r for r in filtered if r[5] not in ("⭐", "👑")]

        # Sortowanie
        col_i = _SORTABLE.get(active_sort_gracze.get("column", "ID"), 0)
        rev = active_sort_gracze.get("reverse", False)
        if col_i == 0:
            filtered.sort(key=lambda x: int(x[0]) if x[0] != "" else 0, reverse=rev)
        elif col_i == 5:

            def _skey(r: List[Any]) -> Tuple[int, str]:
                s = r[5]
                if s == "⭐":
                    return (0, "")
                if s == "👑":
                    return (1, "")
                return (2, "")

            filtered.sort(key=_skey, reverse=rev)
        else:
            filtered.sort(key=lambda x: (str(x[col_i]) or '').lower(), reverse=rev)

        displayed_data = filtered
        if _table[0] is not None:
            _table[0].set_data(displayed_data)
        _refresh_filter_btn()

    def _refresh_filter_btn() -> None:
        active = sum(1 for v in active_filters_gracze.values() if v != 'Wszystkie')
        filter_btn.configure(text=f"Filtruj ({active})" if active else "Filtruj")

    # ── Górny pasek (sortowanie + filtry) ────────────────────────────────────
    top_bar = tk.Frame(tab, bg=bg_top)
    top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
    tk.Label(top_bar, text="Sortuj:", bg=bg_top, fg=fg_top, font=FONT).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    sort_var = tk.StringVar(value=active_sort_gracze.get("column", "ID"))
    ttk.Combobox(
        top_bar,
        textvariable=sort_var,
        values=list(_SORTABLE.keys()),
        state="readonly",
        width=14,
    ).pack(side=tk.LEFT)

    def _sort_asc() -> None:
        active_sort_gracze["column"] = sort_var.get()
        active_sort_gracze["reverse"] = False
        _apply_and_draw()

    def _sort_desc() -> None:
        active_sort_gracze["column"] = sort_var.get()
        active_sort_gracze["reverse"] = True
        _apply_and_draw()

    ttk.Button(top_bar, text="Rosnąco", command=_sort_asc).pack(side=tk.LEFT, padx=4)
    ttk.Button(top_bar, text="Malejąco", command=_sort_desc).pack(side=tk.LEFT, padx=4)
    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
    tk.Label(top_bar, text="Filtruj:", bg=bg_top, fg=fg_top, font=FONT).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    filter_btn = ttk.Button(top_bar, text="Filtruj", command=lambda: _open_filter())
    filter_btn.pack(side=tk.LEFT, padx=4)
    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
    tk.Label(top_bar, text="Wyszukaj:", bg=bg_top, fg=fg_top, font=FONT).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    search_entry = ttk.Entry(top_bar, textvariable=search_var, width=20)
    search_entry.pack(side=tk.LEFT, padx=4)
    search_var.trace_add('write', lambda *_: _apply_and_draw())  # type: ignore[misc]

    # ── Callbacki tabeli ─────────────────────────────────────────────────────
    def _on_edit(_row_idx: int, row_data: List[Any]) -> None:
        # row_data: [id, nick, imie, plec, social, emoji, glowny_int, wazna_int]
        # open_edit_gracz_dialog oczekuje: [id, nick, imie, plec, social, glowny_int, wazna_int]
        edit_vals: List[Any] = [
            row_data[0],
            row_data[1],
            row_data[2],
            row_data[3],
            row_data[4],
            row_data[6] if len(row_data) > 6 else 0,
            row_data[7] if len(row_data) > 7 else 0,
        ]
        open_edit_gracz_dialog(
            tab,
            edit_vals,
            refresh_callback=lambda **_kw: fill_gracze_tab(tab, dark_mode=get_dark_mode_from_tab(tab)),  # type: ignore[misc]
        )

    def _on_sort(col_idx: int) -> None:
        col_name = _HEADERS[col_idx]
        if active_sort_gracze.get("column") == col_name:
            active_sort_gracze["reverse"] = not active_sort_gracze.get("reverse", False)
        else:
            active_sort_gracze["column"] = col_name
            active_sort_gracze["reverse"] = False
        sort_var.set(col_name)
        _apply_and_draw()

    def _on_cell_click(_row_idx: int, col_idx: int, row_data: List[Any]) -> None:
        if col_idx == 4 and row_data[4]:
            webbrowser.open(str(row_data[4]))

    def _on_right_click(_row_idx: int, row_data: List[Any], event: Any) -> None:
        def _edit() -> None:
            _on_edit(_row_idx, row_data)

        def _del() -> None:
            if messagebox.askyesno(
                "Usuń gracza", f"Czy na pewno chcesz usunąć gracza: {row_data[1]}?", parent=tab
            ):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.row_factory = sqlite3.Row
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.cursor().execute("DELETE FROM gracze WHERE id=?", (row_data[0],))
                    conn.commit()
                fill_gracze_tab(tab, dark_mode=get_dark_mode_from_tab(tab))

        ctx = tk.Menu(tab, tearoff=0)
        ctx.add_command(label="Edytuj", command=_edit)
        ctx.add_separator()
        ctx.add_command(label="Usuń", command=_del)
        ctx.tk_popup(event.x_root, event.y_root)
        ctx.grab_release()

    # ── Tabela ───────────────────────────────────────────────────────────────
    tbl = CTkDataTable(
        tab,
        headers=_HEADERS,
        col_widths=_compute_widths(data_ref[0]) if data_ref[0] else [44, 120, 160, 90, 200, 56],
        data=[],
        edit_callback=_on_edit,
        id_col=0,
        row_color_fn=_row_color,
        link_cols=[4],
        center_cols=[0, 5],
        dark_mode=dark_mode,
        sort_callback=_on_sort,
        cell_click_callback=_on_cell_click,
        right_click_callback=_on_right_click,
        show_row_numbers=True,
    )
    tbl.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    tab.rowconfigure(1, weight=1)
    tab.columnconfigure(0, weight=1)
    _table[0] = tbl

    # ── Zapisz cache na widgecie ───────────────────────────────────────────
    tab._gracze_tab_cache = {  # type: ignore[attr-defined]
        'data_ref': data_ref,
        'apply_fn': _apply_and_draw,
        'table_ref': tbl,
        'dark_mode': dark_mode,
    }

    # ── Dialog filtrowania ────────────────────────────────────────────────────
    def _open_filter() -> None:
        dlg = create_ctk_toplevel(tab)
        dlg.title("Filtruj graczy")
        dlg.transient(tab.winfo_toplevel())
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 390, 310)

        mf = ctk.CTkFrame(dlg)
        mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        cur = data_ref[0]

        # Płeć
        ctk.CTkLabel(mf, text="Płeć:").grid(row=0, column=0, sticky="w", pady=8)
        plci: set[str] = {str(r[3]) for r in cur if r[3]}
        plec_var_ = tk.StringVar(value=active_filters_gracze.get('plec', 'Wszystkie'))
        ttk.Combobox(
            mf,
            textvariable=plec_var_,
            values=['Wszystkie'] + sorted(plci),
            width=22,
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Imię i nazwisko
        ctk.CTkLabel(mf, text="Imię i nazwisko:").grid(row=1, column=0, sticky="w", pady=8)
        imie_var_ = tk.StringVar(value=active_filters_gracze.get('imie', 'Wszystkie'))
        ttk.Combobox(
            mf,
            textvariable=imie_var_,
            values=['Wszystkie', 'Wpisane', 'Puste'],
            width=22,
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Social media
        ctk.CTkLabel(mf, text="Social media:").grid(row=2, column=0, sticky="w", pady=8)
        social_var_ = tk.StringVar(value=active_filters_gracze.get('social', 'Wszystkie'))
        ttk.Combobox(
            mf,
            textvariable=social_var_,
            values=['Wszystkie', 'Wpisane', 'Puste'],
            width=22,
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Status
        ctk.CTkLabel(mf, text="Status:").grid(row=3, column=0, sticky="w", pady=8)
        status_var_ = tk.StringVar(value=active_filters_gracze.get('status', 'Wszystkie'))
        ttk.Combobox(
            mf,
            textvariable=status_var_,
            values=['Wszystkie', 'Główny użytkownik', 'Ważna osoba', 'Zwykła osoba'],
            width=22,
            state="readonly",
        ).grid(row=3, column=1, sticky="ew", pady=8, padx=(10, 0))

        mf.columnconfigure(1, weight=1)

        bf = ctk.CTkFrame(mf, fg_color="transparent")
        bf.grid(row=4, column=0, columnspan=2, pady=(20, 0))

        def _apply() -> None:
            active_filters_gracze['plec'] = plec_var_.get()
            active_filters_gracze['imie'] = imie_var_.get()
            active_filters_gracze['social'] = social_var_.get()
            active_filters_gracze['status'] = status_var_.get()
            _apply_and_draw()
            dlg.destroy()

        def _reset() -> None:
            active_filters_gracze.clear()
            _apply_and_draw()
            dlg.destroy()

        ctk.CTkButton(
            bf,
            text="Zastosuj",
            command=_apply,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            width=90,
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(
            bf, text="Resetuj", command=_reset, fg_color="#1976D2", hover_color="#1565C0", width=90
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(
            bf,
            text="Anuluj",
            command=dlg.destroy,
            fg_color="#666666",
            hover_color="#555555",
            width=90,
        ).pack(side=tk.LEFT, padx=5)

        dlg.after(
            300, lambda: dlg.winfo_exists() and (dlg.deiconify(), dlg.lift(), dlg.focus_force())
        )

    # ── Pierwsze wypełnienie ─────────────────────────────────────────────────
    _apply_and_draw()


# --- OKNO EDYCJI GRACZA ---
def open_edit_gracz_dialog(
    parent: tk.Widget,
    values: Sequence[Any],
    refresh_callback: Optional[Callable[..., None]] = None,
) -> None:
    # Sprawdź tryb ciemny
    root = parent.winfo_toplevel()
    _dark_mode = hasattr(root, 'dark_mode') and getattr(root, 'dark_mode', False)

    # Dialog CustomTkinter
    dialog = create_ctk_toplevel(parent)  # type: ignore
    dialog.title("Edytuj gracza")
    dialog.transient(parent)  # type: ignore
    dialog.resizable(True, True)

    apply_safe_geometry(dialog, parent, 420, 380)

    # Główny frame
    main_frame = ctk.CTkFrame(dialog, fg_color="transparent")  # type: ignore
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # ID gracza
    ctk.CTkLabel(main_frame, text=f"ID gracza: {values[0]}", font=ctk.CTkFont(size=scale_font_size(12), weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")  # type: ignore

    # Nick gracza
    ctk.CTkLabel(main_frame, text="Nick gracza *", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=1, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    nick_entry = ctk.CTkEntry(main_frame, width=250)  # type: ignore
    nick_entry.grid(row=1, column=1, pady=8, sticky="ew")
    nick_entry.insert(0, values[1] if values[1] is not None else "")

    # Imię i nazwisko
    ctk.CTkLabel(main_frame, text="Imię i nazwisko", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    name_entry = ctk.CTkEntry(main_frame, width=250)  # type: ignore
    name_entry.grid(row=2, column=1, pady=8, sticky="ew")
    name_entry.insert(0, values[2] if values[2] is not None else "")

    # Płeć
    ctk.CTkLabel(main_frame, text="Płeć", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    gender_var = tk.StringVar(value=values[3] if values[3] else "Kobieta")
    gender_combo = ctk.CTkComboBox(main_frame, width=250, values=["Kobieta", "Mężczyzna", "Niebinarna", "Inne"], variable=gender_var, state="readonly")  # type: ignore
    gender_combo.grid(row=3, column=1, pady=8, sticky="ew")

    # Social media
    ctk.CTkLabel(main_frame, text="Social media / strona", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=4, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    social_entry = ctk.CTkEntry(main_frame, width=250)  # type: ignore
    social_entry.grid(row=4, column=1, pady=8, sticky="ew")
    social_entry.insert(0, values[4] if values[4] is not None else "")

    # Checkbox główny użytkownik
    glowny_var = tk.BooleanVar(value=bool(values[5]) if len(values) > 5 else False)
    wazna_var = tk.BooleanVar(value=bool(values[6]) if len(values) > 6 else False)

    def on_glowny_toggle() -> None:
        if glowny_var.get():
            wazna_var.set(False)
            wazna_check.deselect()  # type: ignore

    def on_wazna_toggle() -> None:
        if wazna_var.get():
            glowny_var.set(False)
            glowny_check.deselect()  # type: ignore

    glowny_check = ctk.CTkCheckBox(main_frame, text="⭐ Główny użytkownik (tylko jedna osoba)", variable=glowny_var, command=on_glowny_toggle, font=ctk.CTkFont(size=scale_font_size(11)))  # type: ignore
    glowny_check.grid(row=5, column=0, columnspan=2, pady=8, sticky="w")
    if glowny_var.get():
        glowny_check.select()  # type: ignore

    # Checkbox ważna osoba
    wazna_check = ctk.CTkCheckBox(main_frame, text="👑 Ważna osoba", variable=wazna_var, command=on_wazna_toggle, font=ctk.CTkFont(size=scale_font_size(11)))  # type: ignore
    wazna_check.grid(row=6, column=0, columnspan=2, pady=8, sticky="w")
    if wazna_var.get():
        wazna_check.select()  # type: ignore

    def on_save() -> None:
        nick: str = nick_entry.get().strip()
        name: str = name_entry.get().strip()
        gender: str = gender_var.get()
        social: str = social_entry.get().strip()
        glowny: int = 1 if glowny_var.get() else 0
        wazna: int = 1 if wazna_var.get() else 0

        if not nick:
            messagebox.showerror("Błąd", "Nick gracza jest wymagany.", parent=dialog)  # type: ignore
            return
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()

            # Jeśli ustawiamy głównego użytkownika, usuń flagę z pozostałych
            if glowny == 1:
                c.execute("UPDATE gracze SET glowny_uzytkownik = 0 WHERE id != ?", (values[0],))

            c.execute(
                "UPDATE gracze SET nick=?, imie_nazwisko=?, plec=?, social=?,"
                " glowny_uzytkownik=?, wazna=? WHERE id=?",
                (
                    nick,
                    name if name else None,
                    gender,
                    social if social else None,
                    glowny,
                    wazna,
                    values[0],
                ),
            )
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))
        dialog.destroy()

    def on_cancel() -> None:
        dialog.destroy()

    # Przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")  # type: ignore
    btn_frame.grid(row=7, column=0, columnspan=2, pady=(15, 0))

    btn_save = ctk.CTkButton(btn_frame, text="💾 Zapisz", command=on_save, width=100, fg_color="#2E7D32", hover_color="#1B5E20", font=ctk.CTkFont(size=scale_font_size(12), weight="bold"))  # type: ignore
    btn_save.pack(side=tk.LEFT, padx=(0, 10))
    btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100, fg_color="#666666", hover_color="#555555", font=ctk.CTkFont(size=scale_font_size(12)))  # type: ignore
    btn_cancel.pack(side=tk.LEFT)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)


def usun_zaznaczonego_gracza(
    tab: tk.Frame, refresh_callback: Optional[Callable[..., None]] = None
) -> None:
    table: Optional[CTkDataTable] = None
    for widget in tab.winfo_children():
        if isinstance(widget, CTkDataTable):
            table = widget
            break
    if table is None:
        messagebox.showerror("Błąd", "Nie znaleziono tabeli graczy.", parent=tab)  # type: ignore
        return
    sel = table.get_selected()
    if not sel:
        messagebox.showinfo("Brak wyboru", "Zaznacz gracza do usunięcia w tabeli.", parent=tab)  # type: ignore
        return
    _, row_data = sel
    gracz_id = row_data[0]
    gracz_nick = row_data[1]
    if messagebox.askyesno("Usuń gracza", f"Czy na pewno chcesz usunąć gracza: {gracz_nick}?", parent=tab):  # type: ignore
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute("DELETE FROM gracze WHERE id=?", (gracz_id,))
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(tab))


# Alias dla kompatybilności z main.py
usun_zaznaczony_gracza = usun_zaznaczonego_gracza
