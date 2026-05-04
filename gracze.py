import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
import sqlite3
import webbrowser
from typing import Optional, Callable, Sequence, Any, Union, List, Dict, Tuple
import customtkinter as ctk  # type: ignore
import logging
from database_manager import get_db_path, is_guest_mode
from font_scaling import scale_font_size
from dialog_utils import apply_safe_geometry, create_ctk_toplevel
from ctk_table import CTkDataTable

_log = logging.getLogger(__name__)
DB_FILE = get_db_path("gracze.db")

# Moduł: Gracze
# Tutaj będą funkcje i klasy związane z obsługą graczy

_gracze_db_initialized: bool = False


def _ensure_gracze_db() -> None:
    """Jednorazowa inicjalizacja i migracja bazy gracze.db."""
    global _gracze_db_initialized
    if _gracze_db_initialized:
        return
    _gracze_db_initialized = True
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
        try:
            c.execute("ALTER TABLE gracze ADD COLUMN grupa TEXT")
        except sqlite3.OperationalError:
            pass  # Kolumna już istnieje
        conn.commit()

# Przechowuj aktywne filtry na poziomie modułu
active_filters_gracze: Dict[str, Any] = {}
# Przechowuj stan sortowania na poziomie modułu
active_sort_gracze: Dict[str, Any] = {"column": "ID", "reverse": False}
# Zapisane szerokości kolumn (pusta lista = użyj auto-obliczonych)
active_col_widths_gracze: List[int] = []
# Widoczność przycisku edycji ✎
show_edit_btn_gracze: bool = True
# Widoczność kolumn w tabeli graczy (klucz = nazwa kolumny, wartość = czy widoczna)
active_visible_cols_gracze: Dict[str, bool] = {
    "Nick": True,
    "Imię i nazwisko": True,
    "Płeć": True,
    "Social media": True,
    "Status": True,
    "Grupa": True,
}
# Kolejność kolumn w tabeli graczy (bez "ID" który zawsze jest pierwszy)
active_col_order_gracze: List[str] = ["Nick", "Imię i nazwisko", "Płeć", "Social media", "Status", "Grupa"]
# Kolumny, które zawsze są widoczne (nie można ich ukryć)
_ALWAYS_VISIBLE_GRACZE = {"ID"}


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
            widget.configure(  # type: ignore[call-overload]
                bg=dark_entry_bg,
                fg=dark_entry_fg,
                insertbackground=dark_entry_fg,
                selectbackground="#0078d4",
            )
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
        apply_safe_geometry(dialog, parent, 420, 430)

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

    # Grupa
    ctk.CTkLabel(main_frame, text="Grupa", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=5, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    grupa_entry = ctk.CTkEntry(main_frame, width=250, placeholder_text="Tagi po przecinku, np.: Drużyna A, Kampania 2")  # type: ignore
    grupa_entry.grid(row=5, column=1, pady=8, sticky="ew")

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
    glowny_check.grid(row=6, column=0, columnspan=2, pady=8, sticky="w")

    # Checkbox ważna osoba
    wazna_check = ctk.CTkCheckBox(main_frame, text="👑 Ważna osoba", variable=wazna_var, command=on_wazna_toggle, font=ctk.CTkFont(size=scale_font_size(11)))  # type: ignore
    wazna_check.grid(row=7, column=0, columnspan=2, pady=8, sticky="w")

    def on_ok() -> None:
        nick: str = nick_entry.get().strip()
        name: str = name_entry.get().strip()
        gender: str = gender_var.get()
        social: str = social_entry.get().strip()
        grupa: str = grupa_entry.get().strip()
        glowny: int = 1 if glowny_var.get() else 0
        wazna: int = 1 if wazna_var.get() else 0

        if not nick:
            messagebox.showerror("Błąd", "Nick gracza jest wymagany.", parent=dialog)  # type: ignore
            return

        _ensure_gracze_db()
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()

            # Jeśli ustawiamy głównego użytkownika, usuń flagę z pozostałych
            if glowny == 1:
                c.execute("UPDATE gracze SET glowny_uzytkownik = 0")

            c.execute(
                "INSERT INTO gracze (nick, imie_nazwisko, plec, social,"
                " glowny_uzytkownik, wazna, grupa) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nick, name if name else None, gender, social if social else None, glowny, wazna,
                 grupa if grupa else None),
            )
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))  # type: ignore
        dialog.destroy()

    def on_cancel() -> None:
        dialog.destroy()

    # Przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")  # type: ignore
    btn_frame.grid(row=8, column=0, columnspan=2, pady=(15, 0))

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
        c.execute("SELECT MAX(id) FROM gracze")
        result = c.fetchone()
        return 1 if result[0] is None else result[0] + 1


def get_all_players() -> list[tuple[Any, ...]]:
    _ensure_gracze_db()
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute(
            "SELECT id, nick, imie_nazwisko, plec, social,"
            " glowny_uzytkownik, wazna, grupa FROM gracze ORDER BY id ASC"
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
                                    rec[7] if rec[7] else "",  # Grupa
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
                        rec[7] if rec[7] else "",  # Grupa
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

    # Buduj 9-polowe wiersze: [id, nick, imie, plec, social, emoji, grupa, glowny_int, wazna_int]
    data_ref: List[List[List[Any]]] = [_preloaded_data]

    _HEADERS = ["ID", "Nick", "Imię i nazwisko", "Płeć", "Social media", "Status", "Grupa"]
    _SORTABLE = {
        "ID": 0,
        "Nick": 1,
        "Imię i nazwisko": 2,
        "Płeć": 3,
        "Social media": 4,
        "Status": 5,
        "Grupa": 6,
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
        w_grupa = (
            max(
                [_mf_bold.measure("Grupa")]
                + ([_mf.measure(str(r[6])) for r in rows if r[6]] or [0])
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
            min(max(w_grupa, 60), 320),
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
                if phrase in (str(r[1]) or '').lower()
                or phrase in (str(r[2]) or '').lower()
                or phrase in (str(r[6]) or '').lower()  # Grupa
            ]

        def _fl(d: Dict[str, Any], key: str) -> List[str]:
            v = d.get(key, [])
            if isinstance(v, str):
                return [] if v == 'Wszystkie' else [v]
            return list(v)

        # Filtr plci
        plec_list = _fl(active_filters_gracze, 'plec')
        if plec_list:
            filtered = [r for r in filtered if (r[3] or '') in plec_list]

        # Filtr imie i nazwisko
        imie_list = _fl(active_filters_gracze, 'imie')
        if imie_list:
            show_wpisane = 'Wpisane' in imie_list
            show_puste = 'Puste' in imie_list
            if not (show_wpisane and show_puste):
                filtered = [
                    r for r in filtered
                    if (show_wpisane and r[2] and str(r[2]).strip())
                    or (show_puste and (not r[2] or not str(r[2]).strip()))
                ]

        # Filtr social media
        social_list = _fl(active_filters_gracze, 'social')
        if social_list:
            show_wpisane = 'Wpisane' in social_list
            show_puste = 'Puste' in social_list
            if not (show_wpisane and show_puste):
                filtered = [
                    r for r in filtered
                    if (show_wpisane and r[4] and str(r[4]).strip())
                    or (show_puste and (not r[4] or not str(r[4]).strip()))
                ]

        # Filtr status
        status_list = _fl(active_filters_gracze, 'status')
        if status_list:
            def _matches_status(row: List[Any]) -> bool:
                emoji = row[5] if len(row) > 5 else ''
                for s in status_list:
                    if s == 'Główny użytkownik' and emoji == "⭐":
                        return True
                    if s == 'Ważna osoba' and emoji == "👑":
                        return True
                    if s == 'Zwykła osoba' and emoji not in ("⭐", "👑"):
                        return True
                return False
            filtered = [r for r in filtered if _matches_status(r)]

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
        active = sum(1 for v in active_filters_gracze.values() if v)
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
    _search_after_id: List[Optional[str]] = [None]

    def _on_search_changed(*_: Any) -> None:
        if _search_after_id[0] is not None:
            try:
                tab.after_cancel(_search_after_id[0])
            except Exception:
                pass
        _search_after_id[0] = tab.after(200, _apply_and_draw)

    search_var.trace_add('write', _on_search_changed)  # type: ignore[misc]
    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
    cols_btn = ttk.Button(top_bar, text="Kolumny", command=lambda: _open_columns_dialog())
    cols_btn.pack(side=tk.LEFT, padx=4)

    # ── Callbacki tabeli ─────────────────────────────────────────────────────
    def _on_edit(_row_idx: int, row_data: List[Any]) -> None:
        if is_guest_mode():
            messagebox.showwarning(
                "Tryb gościa",
                "W trybie gościa edycja danych jest wyłączona.\n"
                "Wróć do własnych danych, aby dokonać zmian.",
                parent=tab,
            )
            return
        # row_data: [id, nick, imie, plec, social, emoji, grupa, glowny_int, wazna_int]
        # open_edit_gracz_dialog oczekuje: [id, nick, imie, plec, social, glowny_int, wazna_int, grupa]
        edit_vals: List[Any] = [
            row_data[0],
            row_data[1],
            row_data[2],
            row_data[3],
            row_data[4],
            row_data[7] if len(row_data) > 7 else 0,  # glowny_uzytkownik
            row_data[8] if len(row_data) > 8 else 0,  # wazna
            row_data[6] if len(row_data) > 6 else "",  # grupa
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
            if is_guest_mode():
                messagebox.showwarning(
                    "Tryb gościa",
                    "W trybie gościa usuwanie danych jest wyłączone.",
                    parent=tab,
                )
                return
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

    _col_w = (
        list(active_col_widths_gracze)
        if len(active_col_widths_gracze) == len(_HEADERS)
        else (_compute_widths(data_ref[0]) if data_ref[0] else [44, 120, 160, 90, 200, 56, 80])
    )

    def _on_col_resize_gracze(widths: List[int]) -> None:
        active_col_widths_gracze.clear()
        active_col_widths_gracze.extend(widths)

    def _compute_hidden_cols() -> List[int]:
        """Zwraca listę indeksów kolumn do ukrycia na podstawie active_visible_cols_gracze."""
        hidden: List[int] = []
        for idx, hdr in enumerate(_HEADERS):
            if hdr in _ALWAYS_VISIBLE_GRACZE:
                continue
            if not active_visible_cols_gracze.get(hdr, True):
                hidden.append(idx)
        return hidden

    def _compute_col_order() -> List[int]:
        """Zwraca permutację kolumn wg active_col_order_gracze."""
        fixed = [h for h in _HEADERS if h in _ALWAYS_VISIBLE_GRACZE]
        ordered = [h for h in active_col_order_gracze if h in _HEADERS and h not in _ALWAYS_VISIBLE_GRACZE]
        missing = [h for h in _HEADERS if h not in _ALWAYS_VISIBLE_GRACZE and h not in ordered]
        ordered += missing
        display_order = fixed + ordered
        hdr_idx = {h: i for i, h in enumerate(_HEADERS)}
        return [hdr_idx[h] for h in display_order if h in hdr_idx]

    def _open_columns_dialog() -> None:
        """Otwiera dialog z checkboxami i przyciskami kolejności kolumn tabeli graczy."""
        dlg = create_ctk_toplevel(tab)
        dlg.title("Kolumny – Gracze")
        dlg.transient(tab.winfo_toplevel())

        toggleable_base = [h for h in _HEADERS if h not in _ALWAYS_VISIBLE_GRACZE]
        ordered = [h for h in active_col_order_gracze if h in toggleable_base]
        ordered += [h for h in toggleable_base if h not in ordered]

        dialog_h = min(120 + len(ordered) * 38 + 100, 520)
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 340, dialog_h)

        outer = ctk.CTkScrollableFrame(dlg)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            outer,
            text="Widoczność i kolejność kolumn:",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(10), weight="bold"),
        ).pack(anchor="w", pady=(0, 6))

        order_list: List[str] = list(ordered)
        vis_vars: Dict[str, tk.BooleanVar] = {
            h: tk.BooleanVar(value=active_visible_cols_gracze.get(h, True))
            for h in order_list
        }

        rows_frame = ctk.CTkFrame(outer, fg_color="transparent")
        rows_frame.pack(fill=tk.X)

        def _rebuild_rows() -> None:
            for w in rows_frame.winfo_children():
                w.destroy()
            for idx, col_name in enumerate(order_list):
                rf = ctk.CTkFrame(rows_frame, fg_color="transparent")
                rf.pack(fill=tk.X, pady=1)
                ctk.CTkButton(
                    rf, text="↑", width=28, height=24,
                    fg_color="#555", hover_color="#333",
                    command=lambda i=idx: _move(i, -1),
                ).pack(side=tk.LEFT, padx=(0, 2))
                ctk.CTkButton(
                    rf, text="↓", width=28, height=24,
                    fg_color="#555", hover_color="#333",
                    command=lambda i=idx: _move(i, 1),
                ).pack(side=tk.LEFT, padx=(0, 6))
                ctk.CTkCheckBox(rf, text=col_name, variable=vis_vars[col_name],
                                width=180).pack(side=tk.LEFT)

        def _move(idx: int, direction: int) -> None:
            new_idx = idx + direction
            if 0 <= new_idx < len(order_list):
                order_list[idx], order_list[new_idx] = order_list[new_idx], order_list[idx]
                _rebuild_rows()

        _rebuild_rows()

        # ── Sekcja przełącznika przycisku edycji ──────────────────────────
        ctk.CTkLabel(
            outer,
            text="Opcje tabeli:",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(10), weight="bold"),
        ).pack(anchor="w", pady=(10, 4))
        edit_btn_var = tk.BooleanVar(value=show_edit_btn_gracze)
        ctk.CTkCheckBox(
            outer,
            text="Przycisk edycji ✎ w wierszu",
            variable=edit_btn_var,
            width=220,
        ).pack(anchor="w", pady=2)

        bf = ctk.CTkFrame(outer, fg_color="transparent")
        bf.pack(pady=(12, 0))

        def _apply() -> None:
            global show_edit_btn_gracze
            for col_name, v in vis_vars.items():
                active_visible_cols_gracze[col_name] = bool(v.get())
            active_col_order_gracze.clear()
            active_col_order_gracze.extend(order_list)
            show_edit_btn_gracze = bool(edit_btn_var.get())
            dlg.destroy()
            if hasattr(tab, '_gracze_tab_cache'):
                del tab._gracze_tab_cache  # type: ignore[attr-defined]
            fill_gracze_tab(tab, dark_mode=dark_mode)

        def _reset() -> None:
            for v in vis_vars.values():
                v.set(True)
            edit_btn_var.set(True)
            order_list.clear()
            order_list.extend(toggleable_base)
            _rebuild_rows()

        ctk.CTkButton(
            bf, text="Zastosuj", command=_apply, fg_color="#2E7D32", hover_color="#1B5E20", width=90
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(
            bf, text="Resetuj", command=_reset, fg_color="#1976D2",
            hover_color="#1565C0", width=90,
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(
            bf, text="Anuluj", command=dlg.destroy, fg_color="#666666",
            hover_color="#555555", width=90,
        ).pack(side=tk.LEFT, padx=5)

        dlg.after(
            300, lambda: dlg.winfo_exists() and (dlg.deiconify(), dlg.lift(), dlg.focus_force())
        )

    # ── Tabela ─────────────────────────────────────────────────────────────────
    tbl = CTkDataTable(
        tab,
        headers=_HEADERS,
        col_widths=_col_w,
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
        resize_callback=_on_col_resize_gracze,
        show_edit_button=show_edit_btn_gracze,
        hidden_cols=_compute_hidden_cols(),
        col_order=_compute_col_order(),
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
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 460, 300)

        outer = ctk.CTkScrollableFrame(dlg)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        cur = data_ref[0]
        plci_vals: List[str] = sorted({str(r[3]) for r in cur if r[3]})

        rows_cfg_g = [
            ("Płeć:", 'plec', plci_vals),
            ("Imię i nazwisko:", 'imie', ['Wpisane', 'Puste']),
            ("Social media:", 'social', ['Wpisane', 'Puste']),
            ("Status:", 'status', ['Główny użytkownik', 'Ważna osoba', 'Zwykła osoba']),
        ]

        selected: Dict[str, set] = {}

        def _get_existing(key: str) -> set:
            v = active_filters_gracze.get(key, [])
            if isinstance(v, str):
                return set() if v == 'Wszystkie' else {v}
            return set(v)

        def _add_toggle_row(parent: Any, row_idx: int, label: str, key: str, vals: List[str]) -> None:
            selected[key] = _get_existing(key)
            ctk.CTkLabel(parent, text=label, anchor="w", width=110).grid(
                row=row_idx, column=0, sticky="nw", pady=(6, 2), padx=(0, 6)
            )
            wrap = ctk.CTkFrame(parent, fg_color="transparent", height=30)
            wrap.grid(row=row_idx, column=1, sticky="ew", pady=(6, 2))
            wrap.grid_propagate(False)

            btns: List[ctk.CTkButton] = []

            def _make_btn(val: str) -> ctk.CTkButton:
                active = val in selected[key]
                btn = ctk.CTkButton(
                    wrap, text=val,
                    width=max(50, len(val) * 8), height=26,
                    fg_color="#2E7D32" if active else "#555555",
                    hover_color="#1B5E20" if active else "#444444",
                    font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(9)),
                )

                def _toggle(b: ctk.CTkButton = btn, v: str = val) -> None:
                    if v in selected[key]:
                        selected[key].discard(v)
                        b.configure(fg_color="#555555", hover_color="#444444")
                    else:
                        selected[key].add(v)
                        b.configure(fg_color="#2E7D32", hover_color="#1B5E20")

                btn.configure(command=_toggle)
                return btn

            for val in vals:
                btns.append(_make_btn(val))

            def _reflow(event: Any = None) -> None:
                avail = wrap.winfo_width()
                if avail <= 1:
                    wrap.after(50, _reflow)
                    return
                x, y, row_h = 0, 0, 0
                for b in btns:
                    b.update_idletasks()
                    w = b.winfo_reqwidth() + 4
                    h = b.winfo_reqheight() + 2
                    if x + w > avail and x > 0:
                        x = 0
                        y += row_h
                        row_h = 0
                    b.place(x=x, y=y)
                    x += w
                    row_h = max(row_h, h)
                wrap.configure(height=max(y + row_h, 30))

            wrap.bind("<Configure>", _reflow)
            dlg.after(150, _reflow)

        for ri, (label, key, vals) in enumerate(rows_cfg_g):
            _add_toggle_row(outer, ri, label, key, vals)
        outer.columnconfigure(1, weight=1)

        bf = ctk.CTkFrame(dlg, fg_color="transparent")
        bf.pack(pady=(6, 10))

        def _apply() -> None:
            for key in selected:
                active_filters_gracze[key] = list(selected[key])
            _apply_and_draw()
            dlg.destroy()

        def _reset() -> None:
            active_filters_gracze.clear()
            _apply_and_draw()
            dlg.destroy()

        ctk.CTkButton(
            bf, text="Zastosuj", command=_apply, fg_color="#2E7D32", hover_color="#1B5E20", width=90
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(
            bf, text="Resetuj", command=_reset, fg_color="#1976D2", hover_color="#1565C0", width=90
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(
            bf, text="Anuluj", command=dlg.destroy, fg_color="#666666", hover_color="#555555", width=90
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

    apply_safe_geometry(dialog, parent, 420, 430)

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

    # Grupa
    ctk.CTkLabel(main_frame, text="Grupa", font=ctk.CTkFont(size=scale_font_size(12))).grid(row=5, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    grupa_entry_edit = ctk.CTkEntry(main_frame, width=250, placeholder_text="Tagi po przecinku, np.: Drużyna A, Kampania 2")  # type: ignore
    grupa_entry_edit.grid(row=5, column=1, pady=8, sticky="ew")
    grupa_entry_edit.insert(0, values[7] if len(values) > 7 and values[7] is not None else "")

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
    glowny_check.grid(row=6, column=0, columnspan=2, pady=8, sticky="w")
    if glowny_var.get():
        glowny_check.select()  # type: ignore

    # Checkbox ważna osoba
    wazna_check = ctk.CTkCheckBox(main_frame, text="👑 Ważna osoba", variable=wazna_var, command=on_wazna_toggle, font=ctk.CTkFont(size=scale_font_size(11)))  # type: ignore
    wazna_check.grid(row=7, column=0, columnspan=2, pady=8, sticky="w")
    if wazna_var.get():
        wazna_check.select()  # type: ignore

    def on_save() -> None:
        nick: str = nick_entry.get().strip()
        name: str = name_entry.get().strip()
        gender: str = gender_var.get()
        social: str = social_entry.get().strip()
        grupa: str = grupa_entry_edit.get().strip()
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
                " glowny_uzytkownik=?, wazna=?, grupa=? WHERE id=?",
                (
                    nick,
                    name if name else None,
                    gender,
                    social if social else None,
                    glowny,
                    wazna,
                    grupa if grupa else None,
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
    btn_frame.grid(row=8, column=0, columnspan=2, pady=(15, 0))

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
