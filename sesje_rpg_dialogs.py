# type: ignore
import tkinter as tk
import sqlite3
import re
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Callable, Sequence, Any, Dict, List, Tuple
import customtkinter as ctk
import logging
from database_manager import get_db_path, is_guest_mode
from font_scaling import scale_font_size
from dialog_utils import apply_safe_geometry, create_ctk_toplevel, open_calendar_picker, make_scrollable_dialog_frame

_log = logging.getLogger(__name__)
# Stałe i podstawowe funkcje (duplikowane aby uniknąć cyklicznego importu)
DB_FILE = get_db_path("sesje_rpg.db")

# ── Polska kolejność alfabetyczna ─────────────────────────────────────────────
# Mapuje polskie litery na sekwencje sortujące zgodnie z kolejnością polskiego alfabetu:
# a ą b c ć d e ę f g h i j k l ł m n ń o ó p q r s ś t u v w x y z ź ż
_PL_SORT_MAP: Dict[str, str] = {
    'ą': 'a\x01', 'ć': 'c\x01', 'ę': 'e\x01', 'ł': 'l\x01', 'ń': 'n\x01',
    'ó': 'o\x01', 'ś': 's\x01', 'ź': 'z\x01', 'ż': 'z\x02',
}


def _pl_sort_key(s: str) -> str:
    """Zwraca klucz sortowania uwzględniający polską kolejność alfabetyczną."""
    return ''.join(_PL_SORT_MAP.get(c, c) for c in s.lower())


def init_db() -> None:
    """Inicjalizuje bazę danych sesji RPG"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        # Tabela główna sesji — bez cross-bazowych FK (system_id/mg_id z innych plików .db)
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS sesje_rpg (
                id INTEGER PRIMARY KEY,
                data_sesji TEXT NOT NULL,
                system_id INTEGER NOT NULL,
                liczba_graczy INTEGER NOT NULL,
                mg_id INTEGER NOT NULL,
                kampania INTEGER DEFAULT 0,
                jednostrzal INTEGER DEFAULT 0,
                tytul_kampanii TEXT,
                tytul_przygody TEXT
            )
        """
        )

        # Tabela relacji sesja-gracze — FK do sesje_rpg jest w tej samej bazie (OK)
        # gracz_id pochodzi z gracze.db (inna baza) — walidacja po stronie Pythona
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS sesje_gracze (
                sesja_id INTEGER NOT NULL,
                gracz_id INTEGER NOT NULL,
                PRIMARY KEY (sesja_id, gracz_id),
                FOREIGN KEY (sesja_id) REFERENCES sesje_rpg(id) ON DELETE CASCADE
            )
        """
        )
        conn.commit()


def get_first_free_id() -> int:
    """Pobiera pierwszy wolny ID dla nowej sesji"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("SELECT MAX(id) FROM sesje_rpg")
        result = c.fetchone()
        if result[0] is None:
            return 1
        return result[0] + 1


def get_all_systems() -> List[Tuple[int, str]]:
    """Pobiera tylko podręczniki główne systemów RPG z bazy danych (bez suplementów)"""
    try:
        with sqlite3.connect(get_db_path("systemy_rpg.db")) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute("SELECT id, nazwa FROM systemy_gry")
            rows = c.fetchall()
        # Sortuj po polsku (SQLite sortuje bajtowo – Ą/Ć/... trafiają na koniec)
        return sorted(rows, key=lambda r: _pl_sort_key(r[1] or ""))
    except sqlite3.Error:
        return []


def get_all_players() -> List[Tuple[int, str, Any]]:
    """Pobiera wszystkich graczy z bazy danych"""
    with sqlite3.connect(get_db_path("gracze.db")) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute("SELECT id, nick, grupa FROM gracze ORDER BY nick")
        return c.fetchall()


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
    widget: tk.Widget, dark_bg: str, dark_fg: str, dark_entry_bg: str, dark_entry_fg: str
) -> None:
    """Rekurencyjnie stosuje ciemny motyw do widgetów"""
    widget_class = widget.winfo_class()

    try:
        if widget_class in ('Label', 'Button', 'Checkbutton', 'Radiobutton'):
            widget.configure(bg=dark_bg, fg=dark_fg)
            if widget_class in ('Checkbutton', 'Radiobutton'):
                widget.configure(
                    selectcolor=dark_entry_bg, activebackground=dark_bg, activeforeground=dark_fg
                )
        elif widget_class in ('Entry', 'Text'):
            widget.configure(
                bg=dark_entry_bg,
                fg=dark_entry_fg,
                insertbackground=dark_entry_fg,
                selectbackground="#0078d4",
            )
        elif widget_class == 'Frame':
            widget.configure(bg=dark_bg)
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


def dodaj_sesje_rpg(
    parent: Optional[tk.Tk] = None,
    refresh_callback: Optional[Callable[..., None]] = None,
    prefill: Optional[Dict[str, Any]] = None,
) -> None:
    """Otwiera okno dodawania nowej sesji RPG.

    Args:
        parent: Okno nadrzędne.
        refresh_callback: Callback wywoływany po zapisaniu sesji.
        prefill: Opcjonalny słownik z danymi do wstępnego wypełnienia formularza
                 (np. z istniejącej kampanii). Obsługiwane klucze:
                 ``system_id`` (int), ``liczba_graczy`` (int),
                 ``player_ids`` (List[int]), ``mg_id`` (int),
                 ``tytul_kampanii`` (str | None).
    """
    if parent is None:
        parent = tk._default_root  # type: ignore

    dialog = create_ctk_toplevel(parent)  # type: ignore
    dialog.title("Dodaj sesję RPG do bazy")
    dialog.transient(parent)  # type: ignore
    dialog.resizable(True, True)

    if parent is not None:
        apply_safe_geometry(dialog, parent, 640, 680)

    # Główna ramka z padding (scrollowalna — formularz ma wiele pól)
    main_frame = make_scrollable_dialog_frame(dialog)
    main_frame.columnconfigure(1, weight=1)

    # Inicjalizuj bazę danych
    init_db()

    # Pobierz dane z baz
    systems_ref: List[List[Tuple[int, str]]] = [list(get_all_systems())]
    players = get_all_players()

    if not systems_ref[0]:
        messagebox.showerror("Błąd", "Brak systemów RPG w bazie. Dodaj najpierw system RPG.", parent=dialog)  # type: ignore
        dialog.destroy()
        return

    if not players:
        messagebox.showerror("Błąd", "Brak graczy w bazie. Dodaj najpierw graczy.", parent=dialog)  # type: ignore
        dialog.destroy()
        return

    # Pola formularza
    row = 0

    # ID Sesji
    ctk.CTkLabel(
        main_frame, text=f"ID Sesji: {get_first_free_id()}", font=("Segoe UI", scale_font_size(12))
    ).grid(row=row, column=0, columnspan=2, pady=(0, 10), sticky="w")
    row += 1

    # Data sesji
    ctk.CTkLabel(main_frame, text="Data sesji *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    date_frame.grid(row=row, column=1, pady=8, sticky="ew")
    date_frame.columnconfigure(0, weight=1)

    date_entry = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD")
    date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def choose_date() -> None:
        picked = open_calendar_picker(dialog, date_entry.get())
        if picked:
            date_entry.delete(0, tk.END)
            date_entry.insert(0, picked)

    calendar_btn = ctk.CTkButton(date_frame, text="📅", command=choose_date, width=40)
    calendar_btn.grid(row=0, column=1)
    row += 1

    # System RPG — frame z polem tekstowym (filtrowalnym) + przycisk Dodaj
    ctk.CTkLabel(main_frame, text="System RPG *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    system_row_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    system_row_frame.grid(row=row, column=1, pady=8, sticky="ew")
    system_row_frame.columnconfigure(0, weight=1)

    system_var = tk.StringVar(value="")
    # Buduj wartości z pełną listą systemów
    _all_sys_values: List[str] = [f"{s[1]} (ID: {s[0]})" for s in systems_ref[0]]
    system_combo = ctk.CTkComboBox(
        system_row_frame,
        variable=system_var,
        values=_all_sys_values,
        state="normal",
        width=380,
    )
    system_combo.grid(row=0, column=0, sticky="ew", padx=(0, 6))
    if systems_ref[0]:
        system_combo.set(f"{systems_ref[0][0][1]} (ID: {systems_ref[0][0][0]})")

    def _filter_systems_dodaj(*_: Any) -> None:
        query = system_var.get().lower()
        if query:
            filtered = [v for v in _all_sys_values if query in v.lower()]
            system_combo.configure(values=filtered if filtered else _all_sys_values)
        else:
            system_combo.configure(values=_all_sys_values)

    def _on_combo_scroll_dodaj(event: Any) -> None:
        vals = system_combo.cget("values")
        if not vals:
            return
        current = system_var.get()
        try:
            idx = list(vals).index(current)
        except ValueError:
            idx = 0
        if event.delta > 0:
            idx = max(0, idx - 1)
        else:
            idx = min(len(vals) - 1, idx + 1)
        system_combo.set(vals[idx])

    system_combo.bind("<KeyRelease>", _filter_systems_dodaj)
    system_combo.bind("<MouseWheel>", _on_combo_scroll_dodaj)

    def _after_add_system_dodaj() -> None:
        """Odświeża listę systemów po dodaniu nowego z poziomu dialogu sesji."""
        systems_ref[0] = list(get_all_systems())
        new_values = [f"{s[1]} (ID: {s[0]})" for s in systems_ref[0]]
        _all_sys_values.clear()
        _all_sys_values.extend(new_values)
        system_combo.configure(values=new_values)
        # Odśwież też zakładkę Systemy RPG w głównym oknie
        try:
            import systemy_rpg as _sysmod
            root = dialog.winfo_toplevel()
            sys_tab = getattr(root, 'tabs', {}).get('Systemy RPG')
            if sys_tab:
                _sysmod.fill_systemy_rpg_tab(sys_tab, dark_mode=getattr(root, 'dark_mode', False))
        except Exception:
            pass

    def _open_add_system_dodaj() -> None:
        import systemy_rpg as _sysmod
        _sysmod.open_add_game_dialog(dialog, refresh_callback=_after_add_system_dodaj)

    ctk.CTkButton(
        system_row_frame,
        text="➕",
        command=_open_add_system_dodaj,
        width=36,
        height=28,
        fg_color="#1565C0",
        hover_color="#0D47A1",
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12)),
    ).grid(row=0, column=1, sticky="w")
    row += 1

    # Liczba graczy
    ctk.CTkLabel(main_frame, text="Liczba graczy *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    liczba_var = tk.StringVar(value="1")
    liczba_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    liczba_frame.grid(row=row, column=1, pady=8, sticky="w")
    liczba_entry = ctk.CTkEntry(liczba_frame, textvariable=liczba_var, width=60)
    liczba_entry.grid(row=0, column=0)
    row += 1

    # Wybór graczy
    ctk.CTkLabel(main_frame, text="Wybierz graczy *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    players_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    players_frame.grid(row=row, column=1, pady=8, sticky="ew")
    players_frame.columnconfigure(0, weight=1)

    # Lista wybranych graczy i przycisk
    selected_players_list: List[int] = []
    selected_players_label = ctk.CTkLabel(
        players_frame, text="Brak wybranych graczy", anchor="w", fg_color=("gray85", "gray25")
    )
    selected_players_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    # Słownik {id: nick} dla szybkiego wyszukiwania graczy
    player_nick_map: Dict[int, str] = {p[0]: p[1] for p in players}  # type: ignore

    def update_selected_players_display() -> None:
        if not selected_players_list:
            selected_players_label.configure(text="Brak wybranych graczy")
        else:
            player_names = [player_nick_map.get(pid, f"ID:{pid}") for pid in selected_players_list]
            selected_players_label.configure(text=", ".join(player_names))  # type: ignore

    def open_players_selection() -> None:
        # Okno wyboru graczy — tk.Listbox zamiast CTkScrollableFrame+CTkCheckBox×N
        # (CTkCheckBox tworzy ~5 wewnętrznych widgetów Tk każdy; przy 87 graczach = ~435
        # synchronicznych operacji Tk blokujących UI. Listbox to 1 widget na całą listę.)
        players_dialog = create_ctk_toplevel(dialog)
        players_dialog.title("Wybierz graczy")
        players_dialog.transient(dialog)
        players_dialog.resizable(True, True)
        apply_safe_geometry(players_dialog, dialog, 420, 520)

        players_dialog.columnconfigure(0, weight=1)
        players_dialog.rowconfigure(3, weight=1)

        max_players = int(liczba_var.get())
        header_lbl = ctk.CTkLabel(
            players_dialog,
            text=f"Wybierz dok\u0142adnie {max_players} graczy: (zaznaczono: 0)",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12)),
        )
        header_lbl.grid(row=0, column=0, pady=(12, 4), padx=14, sticky="w")

        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            players_dialog,
            textvariable=search_var,
            placeholder_text="\U0001f50d Szukaj gracza...",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        )
        search_entry.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        search_entry.focus()

        # ── Szybkie zaznaczanie po tagu grupy ────────────────────────────────
        tags_map: Dict[str, List[int]] = {}
        for _p in players:
            _raw = _p[2]
            if _raw:
                for _tag in (t.strip() for t in _raw.split(",") if t.strip()):
                    tags_map.setdefault(_tag, []).append(_p[0])

        group_frame = ctk.CTkFrame(players_dialog, fg_color="transparent")
        group_frame.grid(row=2, column=0, padx=12, pady=(0, 2), sticky="ew")
        if tags_map:
            tag_names = sorted(tags_map.keys())
            tag_var = tk.StringVar(value=tag_names[0])
            ctk.CTkLabel(
                group_frame,
                text="Zaznacz grup\u0119:",
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
            ).pack(side=tk.LEFT, padx=(0, 6))
            ctk.CTkComboBox(
                group_frame,
                variable=tag_var,
                values=tag_names,
                state="readonly",
                width=170,
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
            ).pack(side=tk.LEFT, padx=(0, 6))

            def _add_tag_players() -> None:
                tag = tag_var.get()
                if not tag or tag not in tags_map:
                    return
                for pid in tags_map[tag]:
                    _persistent_sel.add(pid)
                if len(_persistent_sel) > max_players:
                    tag_ids = set(tags_map[tag])
                    outside = [pid for pid in list(_persistent_sel) if pid not in tag_ids]
                    for pid in outside[:len(_persistent_sel) - max_players]:
                        _persistent_sel.discard(pid)
                _rebuild_listbox()

            ctk.CTkButton(
                group_frame,
                text="Zaznacz",
                command=_add_tag_players,
                width=80,
                height=28,
                fg_color="#1565C0",
                hover_color="#0D47A1",
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
            ).pack(side=tk.LEFT)

        # ── Listbox + Scrollbar ──────────────────────────────────────────────
        lb_frame = tk.Frame(players_dialog)
        lb_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 8))
        lb_frame.rowconfigure(0, weight=1)
        lb_frame.columnconfigure(0, weight=1)

        listbox = tk.Listbox(
            lb_frame,
            selectmode=tk.MULTIPLE,
            activestyle="none",
            font=("Segoe UI", scale_font_size(11)),
            height=16,
            exportselection=False,
        )
        lb_scrollbar = ttk.Scrollbar(lb_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=lb_scrollbar.set)
        listbox.grid(row=0, column=0, sticky="nsew")
        lb_scrollbar.grid(row=0, column=1, sticky="ns")

        # filtered_ids mapuje indeks listboxa → player_id (zmienia się przy filtrze)
        filtered_ids: List[int] = []
        # Trwały zbiór zaznaczonych ID — niezależny od aktualnego filtra wyszukiwania
        _persistent_sel: set[int] = set(selected_players_list)
        # Flaga blokująca handler podczas programatycznego przebudowania listy
        _rebuilding: list[bool] = [False]

        def _rebuild_listbox(*_args: Any) -> None:
            _rebuilding[0] = True
            query = search_var.get().lower()
            listbox.delete(0, tk.END)
            filtered_ids.clear()
            for p in players:
                player_id, player_nick = p[0], p[1]
                if query and query not in player_nick.lower():
                    continue
                listbox.insert(tk.END, f"{player_nick} (ID: {player_id})")
                filtered_ids.append(player_id)
            # Przywróć zaznaczenie na podstawie trwałego zbioru
            for idx, pid in enumerate(filtered_ids):
                if pid in _persistent_sel:
                    listbox.select_set(idx)
            _rebuilding[0] = False
            _update_header()

        def _update_header() -> None:
            count = len(_persistent_sel)
            color = "#2E7D32" if count == max_players else "#C62828"
            header_lbl.configure(
                text=f"Wybierz dok\u0142adnie {max_players} graczy: (zaznaczono: {count})",
                text_color=color,
            )

        def _on_listbox_select(_e: Any) -> None:
            # Pomiń zdarzenia wywoływane programatycznie podczas przebudowy listy
            if _rebuilding[0]:
                return
            # Synchronizuj _persistent_sel z aktualnym widocznym stanem listboxa
            visible_set = set(filtered_ids)
            _persistent_sel.difference_update(visible_set)
            sel = list(listbox.curselection())
            for i in sel:
                if i < len(filtered_ids):
                    _persistent_sel.add(filtered_ids[i])
            # Ogranicz łączną liczbę zaznaczonych do max_players
            if len(_persistent_sel) > max_players:
                excess = len(_persistent_sel) - max_players
                visible_sel_ids = [filtered_ids[i] for i in sel if i < len(filtered_ids)]
                to_remove = visible_sel_ids[-excess:]
                for pid in to_remove:
                    _persistent_sel.discard(pid)
                    for i, fid in enumerate(filtered_ids):
                        if fid == pid:
                            listbox.select_clear(i)
                            break
            _update_header()

        listbox.bind("<<ListboxSelect>>", _on_listbox_select)
        search_var.trace_add("write", _rebuild_listbox)  # type: ignore[misc]

        buttons_frame = ctk.CTkFrame(players_dialog, fg_color="transparent")
        buttons_frame.grid(row=4, column=0, pady=(4, 12), padx=12, sticky="ew")
        buttons_frame.columnconfigure(1, weight=1)

        def _after_add_player(**_kw: Any) -> None:
            new_players = get_all_players()
            players.clear()
            players.extend(new_players)
            _rebuild_listbox()
            if hasattr(parent, 'tabs') and hasattr(parent, 'dark_mode'):
                import gracze as _gracze_mod

                _gracze_mod.fill_gracze_tab(parent.tabs["Gracze"], dark_mode=parent.dark_mode)  # type: ignore

        def _open_add_player() -> None:
            import gracze as _gracze

            _gracze.dodaj_gracza(players_dialog, refresh_callback=_after_add_player)

        ctk.CTkButton(
            buttons_frame,
            text="\u2795 Dodaj gracza",
            command=_open_add_player,
            width=120,
            fg_color="#1976D2",
            hover_color="#1565C0",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        def save_players_selection() -> None:
            selected = list(_persistent_sel)
            expected_count = int(liczba_var.get())
            if len(selected) != expected_count:
                messagebox.showerror(
                    "B\u0142\u0105d",
                    f"Wybierz dok\u0142adnie {expected_count} graczy.",
                    parent=players_dialog,
                )
                return
            if selected_mg_id in selected and not gmless_var.get():
                messagebox.showerror(
                    "B\u0142\u0105d",
                    "Mistrz Gry nie mo\u017ce by\u0107 jednocze\u015bnie graczem.",
                    parent=players_dialog,
                )
                return
            selected_players_list.clear()
            selected_players_list.extend(selected)
            update_selected_players_display()
            players_dialog.destroy()

        ctk.CTkButton(
            buttons_frame,
            text="Zapisz wyb\u00f3r",
            command=save_players_selection,
            width=110,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=2, padx=(0, 6), sticky="e")
        ctk.CTkButton(
            buttons_frame,
            text="Anuluj",
            command=players_dialog.destroy,
            width=80,
            fg_color="#666666",
            hover_color="#555555",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=3, sticky="e")

        _rebuild_listbox()

    choose_players_btn = ctk.CTkButton(
        players_frame, text="Wybierz graczy...", command=open_players_selection, width=140
    )
    choose_players_btn.grid(row=0, column=1)

    row += 1

    # Wybór MG
    ctk.CTkLabel(main_frame, text="Mistrz Gry *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    mg_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    mg_frame.grid(row=row, column=1, pady=8, sticky="ew")
    mg_frame.columnconfigure(0, weight=1)

    # Wybór MG i przycisk
    selected_mg_id: int = 0
    gmless_var = tk.BooleanVar(value=False)
    selected_mg_label = ctk.CTkLabel(
        mg_frame, text="Brak wybranego MG", anchor="w", fg_color=("gray85", "gray25")
    )
    selected_mg_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    def update_selected_mg_display() -> None:
        if gmless_var.get():
            selected_mg_label.configure(text="N/A")
            return
        if selected_mg_id == 0:
            selected_mg_label.configure(text="Brak wybranego MG")
        else:
            for p in players:
                if p[0] == selected_mg_id:
                    selected_mg_label.configure(text=f"{p[1]} (ID: {p[0]})")
                    break

    def open_mg_selection() -> None:
        # Okno wyboru MG — tk.Listbox zamiast CTkScrollableFrame+CTkRadioButton×N
        mg_dialog = create_ctk_toplevel(dialog)
        mg_dialog.title("Wybierz Mistrza Gry")
        mg_dialog.transient(dialog)
        mg_dialog.resizable(True, True)

        apply_safe_geometry(mg_dialog, dialog, 420, 500)

        mg_dialog.columnconfigure(0, weight=1)
        mg_dialog.rowconfigure(2, weight=1)

        ctk.CTkLabel(
            mg_dialog,
            text="Wybierz Mistrza Gry:",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12)),
        ).grid(row=0, column=0, pady=(12, 4), padx=14, sticky="w")

        mg_search_var = tk.StringVar()
        mg_search_entry = ctk.CTkEntry(
            mg_dialog,
            textvariable=mg_search_var,
            placeholder_text="\U0001f50d Szukaj gracza...",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        )
        mg_search_entry.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        mg_search_entry.focus()

        # ── Listbox + Scrollbar ──────────────────────────────────────────────
        mg_lb_frame = tk.Frame(mg_dialog)
        mg_lb_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))
        mg_lb_frame.rowconfigure(0, weight=1)
        mg_lb_frame.columnconfigure(0, weight=1)

        mg_listbox = tk.Listbox(
            mg_lb_frame,
            selectmode=tk.SINGLE,
            activestyle="none",
            font=("Segoe UI", scale_font_size(11)),
            height=16,
            exportselection=False,
        )
        mg_scrollbar = ttk.Scrollbar(mg_lb_frame, orient=tk.VERTICAL, command=mg_listbox.yview)
        mg_listbox.configure(yscrollcommand=mg_scrollbar.set)
        mg_listbox.grid(row=0, column=0, sticky="nsew")
        mg_scrollbar.grid(row=0, column=1, sticky="ns")

        mg_filtered_ids: List[int] = []

        def _rebuild_mg_listbox(*_args: Any) -> None:
            query = mg_search_var.get().lower()
            # Zapamiętaj bieżące zaznaczenie
            cur_sel = mg_listbox.curselection()
            current_mg = (
                mg_filtered_ids[cur_sel[0]]
                if cur_sel and cur_sel[0] < len(mg_filtered_ids)
                else selected_mg_id
            )
            mg_listbox.delete(0, tk.END)
            mg_filtered_ids.clear()
            for p in players:
                player_id, player_nick = p[0], p[1]
                if query and query not in player_nick.lower():
                    continue
                mg_listbox.insert(tk.END, f"{player_nick} (ID: {player_id})")
                mg_filtered_ids.append(player_id)
            # Przywróć zaznaczenie
            if current_mg != 0:
                for idx, pid in enumerate(mg_filtered_ids):
                    if pid == current_mg:
                        mg_listbox.select_set(idx)
                        mg_listbox.see(idx)
                        break

        mg_search_var.trace_add("write", _rebuild_mg_listbox)  # type: ignore[misc]

        buttons_frame = ctk.CTkFrame(mg_dialog, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, pady=(4, 12), padx=12, sticky="ew")
        buttons_frame.columnconfigure(1, weight=1)

        def _after_add_player_mg(**_kw: Any) -> None:
            new_players = get_all_players()
            players.clear()
            players.extend(new_players)
            _rebuild_mg_listbox()
            if hasattr(parent, 'tabs') and hasattr(parent, 'dark_mode'):
                import gracze as _gracze_mod

                _gracze_mod.fill_gracze_tab(parent.tabs["Gracze"], dark_mode=parent.dark_mode)  # type: ignore

        def _open_add_player_mg() -> None:
            import gracze as _gracze

            _gracze.dodaj_gracza(mg_dialog, refresh_callback=_after_add_player_mg)

        ctk.CTkButton(
            buttons_frame,
            text="\u2795 Dodaj gracza",
            command=_open_add_player_mg,
            width=120,
            fg_color="#1976D2",
            hover_color="#1565C0",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        def save_mg_selection() -> None:
            sel_indices = mg_listbox.curselection()
            if not sel_indices:
                messagebox.showerror("B\u0142\u0105d", "Wybierz Mistrza Gry.", parent=mg_dialog)
                return
            selected_id = (
                mg_filtered_ids[sel_indices[0]]
                if sel_indices[0] < len(mg_filtered_ids)
                else 0
            )
            if selected_id == 0:
                messagebox.showerror("B\u0142\u0105d", "Wybierz Mistrza Gry.", parent=mg_dialog)
                return
            if selected_id in selected_players_list:
                messagebox.showerror(
                    "B\u0142\u0105d",
                    "Mistrz Gry nie mo\u017ce by\u0107 jednocze\u015bnie graczem.",
                    parent=mg_dialog,
                )
                return
            nonlocal selected_mg_id
            selected_mg_id = selected_id
            update_selected_mg_display()
            mg_dialog.destroy()

        ctk.CTkButton(
            buttons_frame,
            text="Zapisz wyb\u00f3r",
            command=save_mg_selection,
            width=110,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=2, padx=(0, 6), sticky="e")
        ctk.CTkButton(
            buttons_frame,
            text="Anuluj",
            command=mg_dialog.destroy,
            width=80,
            fg_color="#666666",
            hover_color="#555555",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=3, sticky="e")

        _rebuild_mg_listbox()

    def on_gmless_change() -> None:
        if gmless_var.get():
            selected_mg_label.configure(text="N/A")
            choose_mg_btn.configure(state="disabled")
        else:
            choose_mg_btn.configure(state="normal")
            update_selected_mg_display()

    gmless_cb = ctk.CTkCheckBox(
        mg_frame,
        text="Gra GM-less",
        variable=gmless_var,
        command=on_gmless_change,
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
    )
    gmless_cb.grid(row=0, column=1, padx=(0, 10))

    choose_mg_btn = ctk.CTkButton(
        mg_frame, text="Wybierz MG...", command=open_mg_selection, width=140
    )
    choose_mg_btn.grid(row=0, column=2)
    row += 1

    # Typ sesji
    ctk.CTkLabel(main_frame, text="Typ sesji *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    typ_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_frame.grid(row=row, column=1, pady=8, sticky="ew")

    kampania_var = tk.BooleanVar()
    jednostrzal_var = tk.BooleanVar()

    kampania_cb = ctk.CTkCheckBox(typ_frame, text="Kampania", variable=kampania_var)
    kampania_cb.grid(row=0, column=0, sticky="w")

    jednostrzal_cb = ctk.CTkCheckBox(typ_frame, text="Jednostrzał", variable=jednostrzal_var)
    jednostrzal_cb.grid(row=0, column=1, sticky="w", padx=(20, 0))

    def validate_typ() -> None:  # type: ignore
        # Tylko jeden typ może być zaznaczony
        if kampania_var.get() and jednostrzal_var.get():
            # Jeśli oba są zaznaczone, odznacz ten, który nie był ostatnio kliknięty
            pass  # Obsłużymy to w funkcjach poniżej

    def on_kampania_change() -> None:
        if kampania_var.get():
            jednostrzal_var.set(False)

    def on_jednostrzal_change() -> None:
        if jednostrzal_var.get():
            kampania_var.set(False)

    kampania_cb.configure(command=on_kampania_change)
    jednostrzal_cb.configure(command=on_jednostrzal_change)
    row += 1

    # Tytuł kampanii
    ctk.CTkLabel(main_frame, text="Tytuł kampanii:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    tytul_kampanii_entry = ctk.CTkEntry(
        main_frame, placeholder_text="Tytuł kampanii (opcjonalnie)"
    )
    tytul_kampanii_entry.grid(row=row, column=1, pady=8, sticky="ew")
    row += 1

    # Tytuł przygody
    ctk.CTkLabel(main_frame, text="Tytuł przygody:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    tytul_przygody_entry = ctk.CTkEntry(
        main_frame, placeholder_text="Tytuł przygody (opcjonalnie)"
    )
    tytul_przygody_entry.grid(row=row, column=1, pady=8, sticky="ew")
    row += 1

    # Funkcja walidacji
    def validate_form() -> bool:
        # Sprawdź datę
        try:
            datetime.strptime(date_entry.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.", parent=dialog
            )
            return False

        # Sprawdź system
        if not system_var.get():
            messagebox.showerror("Błąd", "Wybierz system RPG.", parent=dialog)
            return False
        if not re.search(r'ID: \d+', system_var.get()):
            messagebox.showerror("Błąd", "Wybierz system RPG z listy (wpisz fragment nazwy, a następnie kliknij propozycję).", parent=dialog)
            return False

        # Sprawdź graczy
        expected_count = int(liczba_var.get())

        if len(selected_players_list) != expected_count:
            messagebox.showerror(
                "Błąd", f"Wybierz dokładnie {expected_count} graczy.", parent=dialog
            )
            return False

        # Sprawdź MG
        if not gmless_var.get():
            if selected_mg_id == 0:
                messagebox.showerror("Błąd", "Wybierz Mistrza Gry.", parent=dialog)
                return False
            if selected_mg_id in selected_players_list:
                messagebox.showerror(
                    "Błąd", "Mistrz Gry nie może być jednocześnie graczem.", parent=dialog
                )
                return False

        # Sprawdź typ sesji
        if not kampania_var.get() and not jednostrzal_var.get():
            messagebox.showerror(
                "Błąd", "Wybierz typ sesji (Kampania lub Jednostrzał).", parent=dialog
            )
            return False

        return True

    # Funkcja zapisu
    def save_session() -> None:
        if is_guest_mode():
            messagebox.showwarning(
                "Tryb gościa",
                "W trybie gościa zapis danych jest wyłączony.\n"
                "Wróć do własnych danych, aby dokonać zmian.",
                parent=dialog,
            )
            return
        if not validate_form():
            return

        try:
            # Pobierz ID systemu z combobox
            system_text = system_var.get()
            match = re.search(r'ID: (\d+)', system_text)
            if not match:
                messagebox.showerror("Błąd", "Nie można pobrać ID systemu.", parent=dialog)
                return
            system_id = int(match.group(1))

            # Zapisz do bazy
            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                c = conn.cursor()

                # Dodaj sesję
                c.execute(
                    """
                    INSERT INTO sesje_rpg (
                        data_sesji, system_id, liczba_graczy, mg_id, 
                        kampania, jednostrzal, tytul_kampanii, tytul_przygody
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        date_entry.get(),
                        system_id,
                        int(liczba_var.get()),
                        None if gmless_var.get() else selected_mg_id,
                        int(kampania_var.get()),
                        int(jednostrzal_var.get()),
                        tytul_kampanii_entry.get().strip() or None,
                        tytul_przygody_entry.get().strip() or None,
                    ),
                )

                sesja_id = c.lastrowid

                # Dodaj relacje sesja-gracze
                for player_id in selected_players_list:
                    c.execute(
                        "INSERT INTO sesje_gracze (sesja_id, gracz_id) VALUES (?, ?)",
                        (sesja_id, player_id),
                    )

                conn.commit()

            messagebox.showinfo("Sukces", "Sesja została dodana do bazy.", parent=dialog)

            # Odśwież widok jeśli callback istnieje
            if refresh_callback:
                refresh_callback()

            dialog.destroy()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać sesji:\n{str(e)}", parent=dialog)

    # Przyciski
    buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    buttons_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))

    save_btn = ctk.CTkButton(
        buttons_frame,
        text="Zapisz",
        command=save_session,
        width=120,
        fg_color="#2E7D32",
        hover_color="#1B5E20",
    )
    save_btn.pack(side=tk.LEFT, padx=10)

    cancel_btn = ctk.CTkButton(
        buttons_frame,
        text="Anuluj",
        command=dialog.destroy,
        width=120,
        fg_color="#666666",
        hover_color="#555555",
    )
    cancel_btn.pack(side=tk.LEFT, padx=10)

    # ── Wstępne wypełnienie pól z istniejącej kampanii ───────────────────────
    if prefill:
        pf_system_id: Optional[int] = prefill.get("system_id")
        if pf_system_id is not None:
            for s in systems_ref[0]:
                if s[0] == pf_system_id:
                    system_combo.set(f"{s[1]} (ID: {s[0]})")
                    break

        pf_liczba: Optional[int] = prefill.get("liczba_graczy")
        if pf_liczba is not None:
            liczba_var.set(str(pf_liczba))

        pf_player_ids: Optional[List[int]] = prefill.get("player_ids")
        if pf_player_ids:
            selected_players_list.clear()
            selected_players_list.extend(pf_player_ids)
            update_selected_players_display()

        pf_mg_id: Optional[int] = prefill.get("mg_id")
        if pf_mg_id:
            selected_mg_id = pf_mg_id
            update_selected_mg_display()

        kampania_var.set(True)
        jednostrzal_var.set(False)

        pf_tytul: Optional[str] = prefill.get("tytul_kampanii")
        if pf_tytul:
            tytul_kampanii_entry.insert(0, pf_tytul)

    # Focus na datę
    dialog.after(100, lambda: date_entry.focus_set() if date_entry.winfo_exists() else None)


def open_edit_session_dialog(
    parent: tk.Widget,
    values: Sequence[Any],
    refresh_callback: Optional[Callable[..., None]] = None,
) -> None:
    """Otwiera okno edycji sesji RPG"""
    dialog = create_ctk_toplevel(parent)
    dialog.title("Edytuj sesję RPG")
    dialog.transient(parent)
    dialog.resizable(True, True)

    apply_safe_geometry(dialog, parent, 640, 680)

    # Główna ramka z padding (scrollowalna — formularz ma wiele pól)
    main_frame = make_scrollable_dialog_frame(dialog)
    main_frame.columnconfigure(1, weight=1)

    # Pobierz pełne dane sesji z bazy
    session_id = values[0]

    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute(
                """
                SELECT id, data_sesji, system_id, liczba_graczy, mg_id,
                       kampania, jednostrzal, tytul_kampanii, tytul_przygody
                FROM sesje_rpg WHERE id = ?
            """,
                (session_id,),
            )
            session_data = c.fetchone()

            # Pobierz ID graczy przypisanych do sesji
            c.execute("SELECT gracz_id FROM sesje_gracze WHERE sesja_id = ?", (session_id,))
            assigned_players = [row[0] for row in c.fetchall()]

    except sqlite3.Error as e:
        messagebox.showerror(
            "Błąd bazy danych", f"Nie udało się pobrać danych sesji:\n{str(e)}", parent=dialog
        )
        dialog.destroy()
        return

    if not session_data:
        messagebox.showerror("Błąd", "Nie znaleziono sesji w bazie danych.", parent=dialog)
        dialog.destroy()
        return

    # Pobierz dane z baz
    systems_ref: List[List[Tuple[int, str]]] = [list(get_all_systems())]
    players = get_all_players()

    if not systems_ref[0]:
        messagebox.showerror("Błąd", "Brak systemów RPG w bazie.", parent=dialog)
        dialog.destroy()
        return

    if not players:
        messagebox.showerror("Błąd", "Brak graczy w bazie.", parent=dialog)
        dialog.destroy()
        return

    # Pola formularza
    row = 0

    # ID Sesji (tylko do odczytu)
    ctk.CTkLabel(
        main_frame, text=f"ID Sesji: {session_data[0]}", font=("Segoe UI", scale_font_size(12))
    ).grid(row=row, column=0, columnspan=2, pady=(0, 10), sticky="w")
    row += 1

    # Data sesji
    ctk.CTkLabel(main_frame, text="Data sesji *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    date_frame.grid(row=row, column=1, pady=8, sticky="ew")
    date_frame.columnconfigure(0, weight=1)

    date_entry = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD")
    date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    date_entry.insert(0, session_data[1] or "")

    def choose_date() -> None:
        picked = open_calendar_picker(dialog, date_entry.get())
        if picked:
            date_entry.delete(0, tk.END)
            date_entry.insert(0, picked)

    calendar_btn = ctk.CTkButton(date_frame, text="📅", command=choose_date, width=40)
    calendar_btn.grid(row=0, column=1)
    row += 1

    # System RPG — frame z polem tekstowym (filtrowalnym) + przycisk Dodaj
    ctk.CTkLabel(main_frame, text="System RPG *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    system_row_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    system_row_frame.grid(row=row, column=1, pady=8, sticky="ew")
    system_row_frame.columnconfigure(0, weight=1)

    system_var = tk.StringVar(value="")
    _all_sys_values_e: List[str] = [f"{s[1]} (ID: {s[0]})" for s in systems_ref[0]]
    system_combo = ctk.CTkComboBox(
        system_row_frame,
        variable=system_var,
        values=_all_sys_values_e,
        state="normal",
        width=380,
    )
    system_combo.grid(row=0, column=0, sticky="ew", padx=(0, 6))

    # Znajdź i ustaw aktualny system
    current_system_id = session_data[2]
    for sys_id, sys_name in systems_ref[0]:
        if sys_id == current_system_id:
            system_combo.set(f"{sys_name} (ID: {sys_id})")
            break

    def _filter_systems_edytuj(*_: Any) -> None:
        query = system_var.get().lower()
        if query:
            filtered = [v for v in _all_sys_values_e if query in v.lower()]
            system_combo.configure(values=filtered if filtered else _all_sys_values_e)
        else:
            system_combo.configure(values=_all_sys_values_e)

    def _on_combo_scroll_edytuj(event: Any) -> None:
        vals = system_combo.cget("values")
        if not vals:
            return
        current = system_var.get()
        try:
            idx = list(vals).index(current)
        except ValueError:
            idx = 0
        if event.delta > 0:
            idx = max(0, idx - 1)
        else:
            idx = min(len(vals) - 1, idx + 1)
        system_combo.set(vals[idx])

    system_combo.bind("<KeyRelease>", _filter_systems_edytuj)
    system_combo.bind("<MouseWheel>", _on_combo_scroll_edytuj)

    def _after_add_system_edytuj() -> None:
        """Odświeża listę systemów po dodaniu nowego z poziomu dialogu edycji sesji."""
        systems_ref[0] = list(get_all_systems())
        new_values = [f"{s[1]} (ID: {s[0]})" for s in systems_ref[0]]
        _all_sys_values_e.clear()
        _all_sys_values_e.extend(new_values)
        system_combo.configure(values=new_values)
        try:
            import systemy_rpg as _sysmod
            root = dialog.winfo_toplevel()
            sys_tab = getattr(root, 'tabs', {}).get('Systemy RPG')
            if sys_tab:
                _sysmod.fill_systemy_rpg_tab(sys_tab, dark_mode=getattr(root, 'dark_mode', False))
        except Exception:
            pass

    def _open_add_system_edytuj() -> None:
        import systemy_rpg as _sysmod
        _sysmod.open_add_game_dialog(dialog, refresh_callback=_after_add_system_edytuj)

    ctk.CTkButton(
        system_row_frame,
        text="➕",
        command=_open_add_system_edytuj,
        width=36,
        height=28,
        fg_color="#1565C0",
        hover_color="#0D47A1",
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12)),
    ).grid(row=0, column=1, sticky="w")
    row += 1

    # Liczba graczy
    ctk.CTkLabel(main_frame, text="Liczba graczy *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    liczba_var = tk.StringVar(value=str(session_data[3]))
    liczba_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    liczba_frame.grid(row=row, column=1, pady=8, sticky="w")
    liczba_entry = ctk.CTkEntry(liczba_frame, textvariable=liczba_var, width=60)
    liczba_entry.grid(row=0, column=0)
    row += 1

    # Wybór graczy
    ctk.CTkLabel(main_frame, text="Wybierz graczy *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    players_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    players_frame.grid(row=row, column=1, pady=8, sticky="ew")
    players_frame.columnconfigure(0, weight=1)

    # Lista wybranych graczy i przycisk
    selected_players_list: List[int] = list(assigned_players)  # Ustaw aktualnych graczy
    selected_players_label = ctk.CTkLabel(
        players_frame, text="Brak wybranych graczy", anchor="w", fg_color=("gray85", "gray25")
    )
    selected_players_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    def update_selected_players_display() -> None:
        if not selected_players_list:
            selected_players_label.configure(text="Brak wybranych graczy")
        else:
            player_names = []
            for pid in selected_players_list:
                for p in players:
                    if p[0] == pid:
                        player_names.append(p[1])
                        break
            selected_players_label.configure(
                text=f"Wybrani gracze ({len(selected_players_list)}): {', '.join(player_names)}"
            )

    def open_players_selection() -> None:
        # Okno wyboru graczy (edycja) — tk.Listbox zamiast CTkScrollableFrame+CTkCheckBox×N
        players_dialog = create_ctk_toplevel(dialog)
        players_dialog.title("Wybierz graczy")
        players_dialog.transient(dialog)
        players_dialog.resizable(True, True)
        apply_safe_geometry(players_dialog, dialog, 420, 540)

        players_dialog.columnconfigure(0, weight=1)
        players_dialog.rowconfigure(3, weight=1)

        max_players = int(liczba_var.get())
        header_lbl_edit = ctk.CTkLabel(
            players_dialog,
            text=f"Wybierz maksymalnie {max_players} graczy: (zaznaczono: 0)",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12)),
        )
        header_lbl_edit.grid(row=0, column=0, pady=(12, 4), padx=14, sticky="w")

        search_var_edit = tk.StringVar()
        search_entry_edit = ctk.CTkEntry(
            players_dialog,
            textvariable=search_var_edit,
            placeholder_text="\U0001f50d Szukaj gracza...",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        )
        search_entry_edit.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        search_entry_edit.focus()

        # ── Szybkie zaznaczanie po tagu grupy (edycja) ───────────────────────
        tags_map_edit: Dict[str, List[int]] = {}
        for _p in players:
            _raw = _p[2]
            if _raw:
                for _tag in (t.strip() for t in _raw.split(",") if t.strip()):
                    tags_map_edit.setdefault(_tag, []).append(_p[0])

        group_frame_edit = ctk.CTkFrame(players_dialog, fg_color="transparent")
        group_frame_edit.grid(row=2, column=0, padx=12, pady=(0, 2), sticky="ew")
        if tags_map_edit:
            tag_names_edit = sorted(tags_map_edit.keys())
            tag_var_edit = tk.StringVar(value=tag_names_edit[0])
            ctk.CTkLabel(
                group_frame_edit,
                text="Zaznacz grup\u0119:",
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
            ).pack(side=tk.LEFT, padx=(0, 6))
            ctk.CTkComboBox(
                group_frame_edit,
                variable=tag_var_edit,
                values=tag_names_edit,
                state="readonly",
                width=170,
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
            ).pack(side=tk.LEFT, padx=(0, 6))

            def _add_tag_players_edit() -> None:
                tag = tag_var_edit.get()
                if not tag or tag not in tags_map_edit:
                    return
                for pid in tags_map_edit[tag]:
                    _persistent_sel_edit.add(pid)
                if len(_persistent_sel_edit) > max_players:
                    tag_ids = set(tags_map_edit[tag])
                    outside = [pid for pid in list(_persistent_sel_edit) if pid not in tag_ids]
                    for pid in outside[:len(_persistent_sel_edit) - max_players]:
                        _persistent_sel_edit.discard(pid)
                _rebuild_listbox_edit()

            ctk.CTkButton(
                group_frame_edit,
                text="Zaznacz",
                command=_add_tag_players_edit,
                width=80,
                height=28,
                fg_color="#1565C0",
                hover_color="#0D47A1",
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
            ).pack(side=tk.LEFT)

        # ── Listbox + Scrollbar ──────────────────────────────────────────────
        lb_frame_edit = tk.Frame(players_dialog)
        lb_frame_edit.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 8))
        lb_frame_edit.rowconfigure(0, weight=1)
        lb_frame_edit.columnconfigure(0, weight=1)

        listbox_edit = tk.Listbox(
            lb_frame_edit,
            selectmode=tk.MULTIPLE,
            activestyle="none",
            font=("Segoe UI", scale_font_size(11)),
            height=16,
            exportselection=False,
        )
        lb_scrollbar_edit = ttk.Scrollbar(
            lb_frame_edit, orient=tk.VERTICAL, command=listbox_edit.yview
        )
        listbox_edit.configure(yscrollcommand=lb_scrollbar_edit.set)
        listbox_edit.grid(row=0, column=0, sticky="nsew")
        lb_scrollbar_edit.grid(row=0, column=1, sticky="ns")

        filtered_ids_edit: List[int] = []
        # Trwały zbiór zaznaczonych ID — niezależny od aktualnego filtra wyszukiwania
        _persistent_sel_edit: set[int] = set(selected_players_list)
        # Flaga blokująca handler podczas programatycznego przebudowania listy
        _rebuilding_edit: list[bool] = [False]

        def _rebuild_listbox_edit(*_args: Any) -> None:
            _rebuilding_edit[0] = True
            query = search_var_edit.get().lower()
            listbox_edit.delete(0, tk.END)
            filtered_ids_edit.clear()
            for p in players:
                player_id, player_nick = p[0], p[1]
                if query and query not in player_nick.lower():
                    continue
                listbox_edit.insert(tk.END, f"{player_nick} (ID: {player_id})")
                filtered_ids_edit.append(player_id)
            # Przywróć zaznaczenie na podstawie trwałego zbioru
            for idx, pid in enumerate(filtered_ids_edit):
                if pid in _persistent_sel_edit:
                    listbox_edit.select_set(idx)
            _rebuilding_edit[0] = False
            _update_header_edit()

        def _update_header_edit() -> None:
            count = len(_persistent_sel_edit)
            color = "#2E7D32" if 0 < count <= max_players else "#C62828"
            header_lbl_edit.configure(
                text=f"Wybierz maksymalnie {max_players} graczy: (zaznaczono: {count})",
                text_color=color,
            )

        def _on_listbox_select_edit(_e: Any) -> None:
            # Pomiń zdarzenia wywoływane programatycznie podczas przebudowy listy
            if _rebuilding_edit[0]:
                return
            # Synchronizuj _persistent_sel_edit z aktualnym widocznym stanem listboxa
            visible_set = set(filtered_ids_edit)
            _persistent_sel_edit.difference_update(visible_set)
            sel = list(listbox_edit.curselection())
            for i in sel:
                if i < len(filtered_ids_edit):
                    _persistent_sel_edit.add(filtered_ids_edit[i])
            # Ogranicz łączną liczbę zaznaczonych do max_players
            if len(_persistent_sel_edit) > max_players:
                excess = len(_persistent_sel_edit) - max_players
                visible_sel_ids = [filtered_ids_edit[i] for i in sel if i < len(filtered_ids_edit)]
                to_remove = visible_sel_ids[-excess:]
                for pid in to_remove:
                    _persistent_sel_edit.discard(pid)
                    for i, fid in enumerate(filtered_ids_edit):
                        if fid == pid:
                            listbox_edit.select_clear(i)
                            break
            _update_header_edit()

        listbox_edit.bind("<<ListboxSelect>>", _on_listbox_select_edit)
        search_var_edit.trace_add("write", _rebuild_listbox_edit)  # type: ignore[misc]

        buttons_frame = ctk.CTkFrame(players_dialog, fg_color="transparent")
        buttons_frame.grid(row=4, column=0, pady=(4, 12), padx=12, sticky="ew")
        buttons_frame.columnconfigure(1, weight=1)

        def _after_add_player_edit(**_kw: Any) -> None:
            new_players = get_all_players()
            players.clear()
            players.extend(new_players)
            _rebuild_listbox_edit()
            if hasattr(parent, 'tabs') and hasattr(parent, 'dark_mode'):
                import gracze as _gracze_mod

                _gracze_mod.fill_gracze_tab(parent.tabs["Gracze"], dark_mode=parent.dark_mode)  # type: ignore

        def _open_add_player_edit() -> None:
            import gracze as _gracze

            _gracze.dodaj_gracza(players_dialog, refresh_callback=_after_add_player_edit)

        ctk.CTkButton(
            buttons_frame,
            text="\u2795 Dodaj gracza",
            command=_open_add_player_edit,
            width=120,
            fg_color="#1976D2",
            hover_color="#1565C0",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        def save_players_selection() -> None:
            selected_ids = list(_persistent_sel_edit)
            if len(selected_ids) > max_players:
                messagebox.showerror(
                    "B\u0142\u0105d",
                    f"Wybierz maksymalnie {max_players} graczy.",
                    parent=players_dialog,
                )
                return
            if len(selected_ids) == 0:
                messagebox.showerror(
                    "B\u0142\u0105d",
                    "Wybierz co najmniej jednego gracza.",
                    parent=players_dialog,
                )
                return
            if selected_mg_id in selected_ids:
                messagebox.showerror(
                    "B\u0142\u0105d",
                    "Mistrz Gry nie mo\u017ce by\u0107 jednocze\u015bnie graczem.",
                    parent=players_dialog,
                )
                return
            selected_players_list.clear()
            selected_players_list.extend(selected_ids)
            update_selected_players_display()
            players_dialog.destroy()

        ctk.CTkButton(
            buttons_frame,
            text="Zapisz wyb\u00f3r",
            command=save_players_selection,
            width=110,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=2, padx=(0, 6), sticky="e")
        ctk.CTkButton(
            buttons_frame,
            text="Anuluj",
            command=players_dialog.destroy,
            width=80,
            fg_color="#666666",
            hover_color="#555555",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=3, sticky="e")

        _rebuild_listbox_edit()

    choose_players_btn = ctk.CTkButton(
        players_frame, text="Wybierz graczy...", command=open_players_selection, width=140
    )
    choose_players_btn.grid(row=0, column=1)

    # Ustaw początkowy wyświetlacz graczy
    update_selected_players_display()

    row += 1

    # Wybór MG
    ctk.CTkLabel(main_frame, text="Mistrz Gry *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    mg_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    mg_frame.grid(row=row, column=1, pady=8, sticky="ew")
    mg_frame.columnconfigure(0, weight=1)

    # Lista wybranego MG i przycisk
    _raw_mg_id = session_data[4]
    selected_mg_id: int = 0 if _raw_mg_id is None else _raw_mg_id
    gmless_var = tk.BooleanVar(value=(_raw_mg_id is None))
    selected_mg_label = ctk.CTkLabel(
        mg_frame, text="Brak wybranego MG", anchor="w", fg_color=("gray85", "gray25")
    )
    selected_mg_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    def update_selected_mg_display() -> None:
        if gmless_var.get():
            selected_mg_label.configure(text="N/A")
            return
        if selected_mg_id == 0:
            selected_mg_label.configure(text="Brak wybranego MG")
        else:
            for p in players:
                if p[0] == selected_mg_id:
                    selected_mg_label.configure(text=f"{p[1]} (ID: {p[0]})")
                    break

    def open_mg_selection() -> None:
        # Okno wyboru MG (edycja) — tk.Listbox zamiast CTkScrollableFrame+CTkRadioButton×N
        mg_dialog = create_ctk_toplevel(dialog)
        mg_dialog.title("Wybierz Mistrza Gry")
        mg_dialog.transient(dialog)
        mg_dialog.resizable(True, True)

        apply_safe_geometry(mg_dialog, dialog, 420, 500)

        mg_dialog.columnconfigure(0, weight=1)
        mg_dialog.rowconfigure(2, weight=1)

        ctk.CTkLabel(
            mg_dialog,
            text="Wybierz Mistrza Gry:",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12)),
        ).grid(row=0, column=0, pady=(12, 4), padx=14, sticky="w")

        mg_search_var_edit = tk.StringVar()
        mg_search_entry_edit = ctk.CTkEntry(
            mg_dialog,
            textvariable=mg_search_var_edit,
            placeholder_text="\U0001f50d Szukaj gracza...",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        )
        mg_search_entry_edit.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        mg_search_entry_edit.focus()

        # ── Listbox + Scrollbar ──────────────────────────────────────────────
        mg_lb_frame_edit = tk.Frame(mg_dialog)
        mg_lb_frame_edit.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 8))
        mg_lb_frame_edit.rowconfigure(0, weight=1)
        mg_lb_frame_edit.columnconfigure(0, weight=1)

        mg_listbox_edit = tk.Listbox(
            mg_lb_frame_edit,
            selectmode=tk.SINGLE,
            activestyle="none",
            font=("Segoe UI", scale_font_size(11)),
            height=16,
            exportselection=False,
        )
        mg_scrollbar_edit = ttk.Scrollbar(
            mg_lb_frame_edit, orient=tk.VERTICAL, command=mg_listbox_edit.yview
        )
        mg_listbox_edit.configure(yscrollcommand=mg_scrollbar_edit.set)
        mg_listbox_edit.grid(row=0, column=0, sticky="nsew")
        mg_scrollbar_edit.grid(row=0, column=1, sticky="ns")

        mg_filtered_ids_edit: List[int] = []

        def _rebuild_mg_listbox_edit(*_args: Any) -> None:
            query = mg_search_var_edit.get().lower()
            cur_sel = mg_listbox_edit.curselection()
            current_mg = (
                mg_filtered_ids_edit[cur_sel[0]]
                if cur_sel and cur_sel[0] < len(mg_filtered_ids_edit)
                else selected_mg_id
            )
            mg_listbox_edit.delete(0, tk.END)
            mg_filtered_ids_edit.clear()
            for p in players:
                player_id, player_nick = p[0], p[1]
                if query and query not in player_nick.lower():
                    continue
                mg_listbox_edit.insert(tk.END, f"{player_nick} (ID: {player_id})")
                mg_filtered_ids_edit.append(player_id)
            if current_mg != 0:
                for idx, pid in enumerate(mg_filtered_ids_edit):
                    if pid == current_mg:
                        mg_listbox_edit.select_set(idx)
                        mg_listbox_edit.see(idx)
                        break

        mg_search_var_edit.trace_add("write", _rebuild_mg_listbox_edit)  # type: ignore[misc]

        buttons_frame = ctk.CTkFrame(mg_dialog, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, pady=(4, 12), padx=12, sticky="ew")
        buttons_frame.columnconfigure(1, weight=1)

        def _after_add_player_mg_edit(**_kw: Any) -> None:
            new_players = get_all_players()
            players.clear()
            players.extend(new_players)
            _rebuild_mg_listbox_edit()
            if hasattr(parent, 'tabs') and hasattr(parent, 'dark_mode'):
                import gracze as _gracze_mod

                _gracze_mod.fill_gracze_tab(parent.tabs["Gracze"], dark_mode=parent.dark_mode)  # type: ignore

        def _open_add_player_mg_edit() -> None:
            import gracze as _gracze

            _gracze.dodaj_gracza(mg_dialog, refresh_callback=_after_add_player_mg_edit)

        ctk.CTkButton(
            buttons_frame,
            text="\u2795 Dodaj gracza",
            command=_open_add_player_mg_edit,
            width=120,
            fg_color="#1976D2",
            hover_color="#1565C0",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        def save_mg_selection() -> None:
            sel_indices = mg_listbox_edit.curselection()
            if not sel_indices:
                messagebox.showerror("B\u0142\u0105d", "Wybierz Mistrza Gry.", parent=mg_dialog)
                return
            selected_id = (
                mg_filtered_ids_edit[sel_indices[0]]
                if sel_indices[0] < len(mg_filtered_ids_edit)
                else 0
            )
            if selected_id == 0:
                messagebox.showerror("B\u0142\u0105d", "Wybierz Mistrza Gry.", parent=mg_dialog)
                return
            if selected_id in selected_players_list:
                messagebox.showerror(
                    "B\u0142\u0105d",
                    "Mistrz Gry nie mo\u017ce by\u0107 jednocze\u015bnie graczem.",
                    parent=mg_dialog,
                )
                return
            nonlocal selected_mg_id
            selected_mg_id = selected_id
            update_selected_mg_display()
            mg_dialog.destroy()

        ctk.CTkButton(
            buttons_frame,
            text="Zapisz wyb\u00f3r",
            command=save_mg_selection,
            width=110,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=2, padx=(0, 6), sticky="e")
        ctk.CTkButton(
            buttons_frame,
            text="Anuluj",
            command=mg_dialog.destroy,
            width=80,
            fg_color="#666666",
            hover_color="#555555",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
        ).grid(row=0, column=3, sticky="e")

        _rebuild_mg_listbox_edit()

    def on_gmless_change() -> None:
        if gmless_var.get():
            selected_mg_label.configure(text="N/A")
            choose_mg_btn.configure(state="disabled")
        else:
            choose_mg_btn.configure(state="normal")
            update_selected_mg_display()

    gmless_cb = ctk.CTkCheckBox(
        mg_frame,
        text="Gra GM-less",
        variable=gmless_var,
        command=on_gmless_change,
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
    )
    gmless_cb.grid(row=0, column=1, padx=(0, 10))

    choose_mg_btn = ctk.CTkButton(
        mg_frame, text="Wybierz MG...", command=open_mg_selection, width=140
    )
    choose_mg_btn.grid(row=0, column=2)
    if gmless_var.get():
        choose_mg_btn.configure(state="disabled")

    # Ustaw początkowy wyświetlacz MG
    update_selected_mg_display()
    row += 1

    # Typ sesji
    ctk.CTkLabel(main_frame, text="Typ sesji *:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    typ_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_frame.grid(row=row, column=1, pady=8, sticky="ew")

    kampania_var = tk.BooleanVar(value=bool(session_data[5]))
    jednostrzal_var = tk.BooleanVar(value=bool(session_data[6]))

    kampania_cb = ctk.CTkCheckBox(typ_frame, text="Kampania", variable=kampania_var)
    kampania_cb.grid(row=0, column=0, sticky="w")

    jednostrzal_cb = ctk.CTkCheckBox(typ_frame, text="Jednostrzał", variable=jednostrzal_var)
    jednostrzal_cb.grid(row=0, column=1, sticky="w", padx=(20, 0))

    def on_kampania_change() -> None:
        if kampania_var.get():
            jednostrzal_var.set(False)

    def on_jednostrzal_change() -> None:
        if jednostrzal_var.get():
            kampania_var.set(False)

    kampania_cb.configure(command=on_kampania_change)
    jednostrzal_cb.configure(command=on_jednostrzal_change)
    row += 1

    # Tytuł kampanii
    ctk.CTkLabel(main_frame, text="Tytuł kampanii:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    tytul_kampanii_entry = ctk.CTkEntry(
        main_frame, placeholder_text="Tytuł kampanii (opcjonalnie)"
    )
    tytul_kampanii_entry.grid(row=row, column=1, pady=8, sticky="ew")
    tytul_kampanii_entry.insert(0, session_data[7] or "")
    row += 1

    # Tytuł przygody
    ctk.CTkLabel(main_frame, text="Tytuł przygody:").grid(
        row=row, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    tytul_przygody_entry = ctk.CTkEntry(
        main_frame, placeholder_text="Tytuł przygody (opcjonalnie)"
    )
    tytul_przygody_entry.grid(row=row, column=1, pady=8, sticky="ew")
    tytul_przygody_entry.insert(0, session_data[8] or "")
    row += 1

    # Funkcja walidacji
    def validate_form() -> bool:
        # Sprawdź datę
        try:
            datetime.strptime(date_entry.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror(
                "Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.", parent=dialog
            )
            return False

        # Sprawdź system
        if not system_var.get():
            messagebox.showerror("Błąd", "Wybierz system RPG.", parent=dialog)
            return False
        if not re.search(r'ID: \d+', system_var.get()):
            messagebox.showerror("Błąd", "Wybierz system RPG z listy (wpisz fragment nazwy, a następnie kliknij propozycję).", parent=dialog)
            return False

        # Sprawdź MG
        if not gmless_var.get():
            if selected_mg_id == 0:
                messagebox.showerror("Błąd", "Wybierz Mistrza Gry.", parent=dialog)
                return False
            if selected_mg_id in selected_players_list:
                messagebox.showerror(
                    "Błąd", "Mistrz Gry nie może być jednocześnie graczem.", parent=dialog
                )
                return False

        # Sprawdź typ sesji
        if not kampania_var.get() and not jednostrzal_var.get():
            messagebox.showerror(
                "Błąd", "Wybierz typ sesji (Kampania lub Jednostrzał).", parent=dialog
            )
            return False

        return True

    # Funkcja zapisu
    def save_session() -> None:
        if is_guest_mode():
            messagebox.showwarning(
                "Tryb gościa",
                "W trybie gościa zapis danych jest wyłączony.\n"
                "Wróć do własnych danych, aby dokonać zmian.",
                parent=dialog,
            )
            return
        if not validate_form():
            return

        try:
            # Pobierz ID systemu z combobox
            system_text = system_var.get()
            match = re.search(r'ID: (\d+)', system_text)
            if not match:
                messagebox.showerror("Błąd", "Nie można pobrać ID systemu.", parent=dialog)
                return
            system_id = int(match.group(1))

            # Aktualizuj dane w bazie
            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                c = conn.cursor()

                # Aktualizuj sesję
                c.execute(
                    """
                    UPDATE sesje_rpg SET
                        data_sesji = ?, system_id = ?, liczba_graczy = ?, mg_id = ?,
                        kampania = ?, jednostrzal = ?, tytul_kampanii = ?, tytul_przygody = ?
                    WHERE id = ?
                """,
                    (
                        date_entry.get(),
                        system_id,
                        len(selected_players_list),
                        None if gmless_var.get() else selected_mg_id,
                        int(kampania_var.get()),
                        int(jednostrzal_var.get()),
                        tytul_kampanii_entry.get().strip() or None,
                        tytul_przygody_entry.get().strip() or None,
                        session_id,
                    ),
                )

                # Usuń stare relacje sesja-gracze
                c.execute("DELETE FROM sesje_gracze WHERE sesja_id = ?", (session_id,))

                # Dodaj nowe relacje sesja-gracze
                for player_id in selected_players_list:
                    c.execute(
                        "INSERT INTO sesje_gracze (sesja_id, gracz_id) VALUES (?, ?)",
                        (session_id, player_id),
                    )

                conn.commit()

            messagebox.showinfo("Sukces", "Sesja została zaktualizowana.", parent=dialog)

            # Odśwież widok jeśli callback istnieje
            if refresh_callback:
                refresh_callback()

            dialog.destroy()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zaktualizować sesji:\n{str(e)}", parent=dialog)  # type: ignore

    # Przyciski
    buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    buttons_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))

    save_btn = ctk.CTkButton(
        buttons_frame,
        text="Zapisz",
        command=save_session,
        width=120,
        fg_color="#2E7D32",
        hover_color="#1B5E20",
    )
    save_btn.pack(side=tk.LEFT, padx=10)

    cancel_btn = ctk.CTkButton(
        buttons_frame,
        text="Anuluj",
        command=dialog.destroy,
        width=120,
        fg_color="#666666",
        hover_color="#555555",
    )
    cancel_btn.pack(side=tk.LEFT, padx=10)

    # Focus na datę
    dialog.after(100, lambda: date_entry.focus_set() if date_entry.winfo_exists() else None)
