# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from typing import Optional, Callable, Any, List, Tuple, Dict, Union
import customtkinter as ctk  # type: ignore
from database_manager import get_db_path
from font_scaling import scale_font_size
from dialog_utils import apply_safe_geometry
from ctk_table import CTkDataTable

# Import funkcji dialogowych z oddzielnego modułu
from sesje_rpg_dialogs import open_edit_session_dialog

DB_FILE = get_db_path("sesje_rpg.db")

# Przechowuj aktywne filtry na poziomie modułu
active_filters_sesje: Dict[str, Any] = {}
# Przechowuj stan sortowania na poziomie modułu
active_sort_sesje: Dict[str, Any] = {"column": "ID", "reverse": False}

def init_db() -> None:
    """Inicjalizuje bazę danych sesji RPG"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Tabela główna sesji
        c.execute("""
            CREATE TABLE IF NOT EXISTS sesje_rpg (
                id INTEGER PRIMARY KEY,
                data_sesji TEXT NOT NULL,
                system_id INTEGER NOT NULL,
                liczba_graczy INTEGER NOT NULL,
                mg_id INTEGER NOT NULL,
                kampania INTEGER DEFAULT 0,
                jednostrzal INTEGER DEFAULT 0,
                tytul_kampanii TEXT,
                tytul_przygody TEXT,
                FOREIGN KEY (system_id) REFERENCES systemy_rpg(id),
                FOREIGN KEY (mg_id) REFERENCES gracze(id)
            )
        """)
        
        # Tabela relacji sesja-gracze
        c.execute("""
            CREATE TABLE IF NOT EXISTS sesje_gracze (
                sesja_id INTEGER NOT NULL,
                gracz_id INTEGER NOT NULL,
                PRIMARY KEY (sesja_id, gracz_id),
                FOREIGN KEY (sesja_id) REFERENCES sesje_rpg(id) ON DELETE CASCADE,
                FOREIGN KEY (gracz_id) REFERENCES gracze(id)
            )
        """)
        conn.commit()

def get_dark_mode_from_tab(tab: tk.Widget) -> bool:
    """Pobiera tryb ciemny z głównego okna"""
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

def _apply_dark_theme_to_widget(widget: Union[tk.Widget, tk.Toplevel], dark_bg: str, dark_fg: str, 
                               dark_entry_bg: str, dark_entry_fg: str) -> None:
    """Rekurencyjnie stosuje ciemny motyw do widgetów"""
    widget_class = widget.winfo_class()
    
    try:
        if widget_class in ('Label', 'Button', 'Checkbutton', 'Radiobutton'):
            widget.configure(bg=dark_bg, fg=dark_fg)  # type: ignore
            if widget_class in ('Checkbutton', 'Radiobutton'):
                widget.configure(selectcolor=dark_entry_bg, activebackground=dark_bg, activeforeground=dark_fg)  # type: ignore
        elif widget_class in ('Entry', 'Text'):
            widget.configure(bg=dark_entry_bg, fg=dark_entry_fg,  # type: ignore
                           insertbackground=dark_entry_fg, selectbackground="#0078d4")  # type: ignore
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
        pass

def get_first_free_id() -> int:
    """Zwraca pierwszy wolny ID w bazie sesji RPG"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM sesje_rpg ORDER BY id ASC")
        used_ids = [row[0] for row in c.fetchall()]
    i = 1
    while i in used_ids:
        i += 1
    return i

def get_all_systems() -> List[Tuple[int, str]]:
    """Pobiera tylko podręczniki główne systemów RPG z bazy (bez suplementów)"""
    try:
        with sqlite3.connect(get_db_path("systemy_rpg.db")) as conn:
            c = conn.cursor()
            c.execute("SELECT id, nazwa FROM systemy_rpg WHERE typ = 'Podręcznik Główny' ORDER BY nazwa")
            return c.fetchall()
    except sqlite3.Error:
        return []

def get_all_players() -> List[Tuple[int, str]]:
    """Pobiera wszystkich graczy z bazy"""
    try:
        with sqlite3.connect(get_db_path("gracze.db")) as conn:
            c = conn.cursor()
            c.execute("SELECT id, nick FROM gracze ORDER BY nick")
            return c.fetchall()
    except sqlite3.Error:
        return []

def get_all_sessions() -> List[Tuple[Any, ...]]:
    """Pobiera wszystkie sesje RPG z bazy"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Sprawdź czy tabela istnieje
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sesje_rpg'")
        if not c.fetchone():
            return []
        
        c.execute("SELECT COUNT(*) FROM sesje_rpg")
        if c.fetchone()[0] == 0:
            return []
        
        # Pobierz sesje z LEFT JOIN do systemów i graczy
        c.execute("""
            SELECT s.id, s.data_sesji, s.system_id, s.liczba_graczy, s.mg_id,
                   s.kampania, s.jednostrzal, s.tytul_kampanii, s.tytul_przygody
            FROM sesje_rpg s
            ORDER BY s.data_sesji ASC, s.id ASC
        """)
        sessions = c.fetchall()
    
    # Dla każdej sesji pobierz nazwy systemów i MG z innych baz
    result = []
    for session in sessions:
        try:
            # Pobierz nazwę systemu
            with sqlite3.connect(get_db_path("systemy_rpg.db")) as sys_conn:
                sys_cursor = sys_conn.cursor()
                sys_cursor.execute("SELECT nazwa FROM systemy_rpg WHERE id = ?", (session[2],))
                system_result = sys_cursor.fetchone()
                system_nazwa = system_result[0] if system_result else f"System ID {session[2]}"
        except sqlite3.Error:
            system_nazwa = f"System ID {session[2]}"
        
        try:
            # Pobierz nick MG
            with sqlite3.connect(get_db_path("gracze.db")) as gracze_conn:
                gracze_cursor = gracze_conn.cursor()
                gracze_cursor.execute("SELECT nick FROM gracze WHERE id = ?", (session[4],))
                mg_result = gracze_cursor.fetchone()
                mg_nick = mg_result[0] if mg_result else f"Gracz ID {session[4]}"
        except sqlite3.Error:
            mg_nick = f"Gracz ID {session[4]}"
        
        # Pobierz graczy z sesji
        try:
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute("SELECT gracz_id FROM sesje_gracze WHERE sesja_id = ?", (session[0],))
                gracz_ids = [row[0] for row in c.fetchall()]
                
                # Pobierz nicki graczy
                gracze_names = []
                for gracz_id in gracz_ids:
                    try:
                        with sqlite3.connect(get_db_path("gracze.db")) as gracze_conn:
                            gracze_cursor = gracze_conn.cursor()
                            gracze_cursor.execute("SELECT nick FROM gracze WHERE id = ?", (gracz_id,))
                            gracz_result = gracze_cursor.fetchone()
                            if gracz_result:
                                gracze_names.append(gracz_result[0]) # type: ignore
                    except sqlite3.Error:
                        gracze_names.append(f"Gracz ID {gracz_id}") # type: ignore
                
                gracze_str = ", ".join(gracze_names) if gracze_names else "" # type: ignore
        except sqlite3.Error:
            gracze_str = ""
        
        # Określ typ sesji
        typ_sesji = ""
        if session[5]:  # kampania
            typ_sesji = "Kampania"
            if session[7]:  # tytul_kampanii
                typ_sesji += f": {session[7]}"
        elif session[6]:  # jednostrzal
            typ_sesji = "Jednostrzał"
            if session[8]:  # tytul_przygody
                typ_sesji += f": {session[8]}"
        
        # Jeśli są oba tytuły i jest to kampania, dodaj również tytuł przygody
        if session[5] and session[7] and session[8]:  # kampania z tytułem kampanii i tytułem przygody
            typ_sesji += f" / {session[8]}"
        
        # Format: ID, Data, System, Typ sesji, MG, Gracze
        result.append(( # type: ignore
            session[0],          # ID
            session[1],          # Data sesji
            system_nazwa,        # Nazwa systemu
            typ_sesji,          # Typ sesji z tytułem
            mg_nick,            # Nick MG
            gracze_str          # Lista graczy
        ))
    
    return result # type: ignore

# Funkcja dodaj_sesje_rpg została przeniesiona do sesje_rpg_dialogs.py
def fill_sesje_rpg_tab(tab: tk.Frame, dark_mode: bool = False) -> None:
    """Wypełnia zakładkę Sesje RPG"""
    init_db()

    # ── Szybka ścieżka: odśwież dane bez niszczenia całego UI ───────────────
    cache = getattr(tab, '_sesje_tab_cache', None)
    if cache is not None and cache.get('table_ref') is not None and cache.get('dark_mode') == dark_mode:
        try:
            if cache['table_ref'].winfo_exists():
                new_raw = get_all_sessions()
                new_data: List[List[Any]] = [[v if v is not None else "" for v in rec] for rec in new_raw]
                cache['data_ref'][0] = new_data
                cache['apply_fn']()
                return
        except Exception:
            pass
        # Widget zniszczony – usuń stary cache i przebuduj
        del tab._sesje_tab_cache  # type: ignore[attr-defined]

    for widget in tab.winfo_children():
        widget.destroy()

    data_raw = get_all_sessions()
    _initial_data: List[List[Any]] = [[v if v is not None else "" for v in rec] for rec in data_raw]
    # Mutable holder – closure’y zawsze widzą aktualne dane przez data_ref[0]
    data_ref: List[List[List[Any]]] = [_initial_data]

    _HEADERS  = ["ID", "Data", "System", "Typ sesji", "Mistrz Gry", "Gracze"]
    _SORTABLE = {"ID": 0, "Data": 1, "System": 2, "Typ sesji": 3, "Mistrz Gry": 4, "Gracze": 5}

    # ── Kolory górnego paska ─────────────────────────────────────────────────
    bg_top = "#1e1e2e" if dark_mode else "#f5f5f5"
    fg_top = "#e0e0e0" if dark_mode else "#212121"
    FONT   = ("Segoe UI", scale_font_size(10))

    # ── Obliczanie szerokości kolumn ─────────────────────────────────────────
    _mf      = tkfont.Font(family="Segoe UI", size=scale_font_size(10))
    _mf_bold = tkfont.Font(family="Segoe UI", size=scale_font_size(10), weight="bold")

    def _compute_widths(rows: List[List[Any]]) -> List[int]:
        pad = 24
        w_data   = max([_mf_bold.measure("Data")]        + ([_mf.measure(str(r[1])) for r in rows if r[1]] or [0])) + pad
        w_system = max([_mf_bold.measure("System")]      + ([_mf.measure(str(r[2])) for r in rows if r[2]] or [0])) + pad
        w_typ    = max([_mf_bold.measure("Typ sesji")]   + ([_mf.measure(str(r[3])) for r in rows if r[3]] or [0])) + pad
        w_mg     = max([_mf_bold.measure("Mistrz Gry")] + ([_mf.measure(str(r[4])) for r in rows if r[4]] or [0])) + pad
        w_gracze = max([_mf_bold.measure("Gracze")]      + ([_mf.measure(str(r[5])) for r in rows if r[5]] or [0])) + pad
        return [
            44,
            min(max(w_data,    90), 120),
            min(max(w_system, 100), 280),
            min(max(w_typ,    100), 360),
            min(max(w_mg,      80), 160),
            min(max(w_gracze, 100), 480),
        ]

    # ── Kolorowanie wierszy według miesiąca daty sesji ───────────────────────
    _month_colors_light: Dict[int, str] = {
        1: "#D1E7FF", 2: "#E6D1FF", 3: "#D1FFD1",  4: "#FFF4C4",
        5: "#FFD1D1", 6: "#D1F4FF", 7: "#FFDED1",  8: "#F0D1FF",
        9: "#D1FFB8", 10: "#FFD8B8", 11: "#D1D1FF", 12: "#FFD1E6",
    }
    _month_colors_dark: Dict[int, str] = {
        1: "#0D4F73", 2: "#4D0D73", 3: "#0D730D",  4: "#73730D",
        5: "#730D0D", 6: "#0D7373", 7: "#73470D",  8: "#470D73",
        9: "#47730D", 10: "#73470D", 11: "#0D0D73", 12: "#730D47",
    }

    def _row_color(i: int, row: List[Any]) -> Optional[Tuple[Optional[str], Optional[str]]]:
        date_str = str(row[1]) if len(row) > 1 and row[1] else ""
        if not date_str:
            return None
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month = date_obj.month
        except (ValueError, TypeError):
            return None
        colors = _month_colors_dark if dark_mode else _month_colors_light
        return (colors.get(month), None)

    # ── Stan ─────────────────────────────────────────────────────────────────
    displayed_data: List[List[Any]] = []
    _table: List[Optional[CTkDataTable]] = [None]

    # ── Filtry + sortowanie ──────────────────────────────────────────────────
    def _apply_and_draw() -> None:
        nonlocal displayed_data
        filtered: List[List[Any]] = list(data_ref[0])

        year_f = active_filters_sesje.get('year', 'Wszystkie')
        if year_f != 'Wszystkie':
            filtered = [r for r in filtered if r[1] and str(r[1]).startswith(year_f)]

        system_f = active_filters_sesje.get('system', 'Wszystkie')
        if system_f != 'Wszystkie':
            filtered = [r for r in filtered if r[2] == system_f]

        typ_f = active_filters_sesje.get('typ', 'Wszystkie')
        if typ_f != 'Wszystkie':
            filtered = [r for r in filtered if r[3] and str(r[3]).startswith(typ_f)]

        mg_f = active_filters_sesje.get('mg', 'Wszystkie')
        if mg_f != 'Wszystkie':
            filtered = [r for r in filtered if r[4] == mg_f]

        col_i = _SORTABLE.get(active_sort_sesje.get("column", "ID"), 0)
        rev   = active_sort_sesje.get("reverse", False)
        if col_i == 0:
            filtered.sort(key=lambda x: int(x[0]) if x[0] != "" else 0, reverse=rev)
        else:
            filtered.sort(key=lambda x: (str(x[col_i]) or '').lower(), reverse=rev)

        displayed_data = filtered
        if _table[0] is not None:
            _table[0].set_data(displayed_data)
        _refresh_filter_btn()

    def _refresh_filter_btn() -> None:
        active = sum(1 for v in active_filters_sesje.values() if v != 'Wszystkie')
        filter_btn.configure(text=f"Filtruj ({active})" if active else "Filtruj")

    # ── Górny pasek ──────────────────────────────────────────────────────────
    top_bar = tk.Frame(tab, bg=bg_top)
    top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
    tk.Label(top_bar, text="Sortuj:", bg=bg_top, fg=fg_top, font=FONT).pack(side=tk.LEFT, padx=(0, 4))
    sort_var = tk.StringVar(value=active_sort_sesje.get("column", "ID"))
    ttk.Combobox(
        top_bar, textvariable=sort_var,
        values=list(_SORTABLE.keys()),
        state="readonly", width=12,
    ).pack(side=tk.LEFT)

    def _sort_asc() -> None:
        active_sort_sesje["column"]  = sort_var.get()
        active_sort_sesje["reverse"] = False
        _apply_and_draw()

    def _sort_desc() -> None:
        active_sort_sesje["column"]  = sort_var.get()
        active_sort_sesje["reverse"] = True
        _apply_and_draw()

    ttk.Button(top_bar, text="Rosnąco",  command=_sort_asc ).pack(side=tk.LEFT, padx=4)
    ttk.Button(top_bar, text="Malejąco", command=_sort_desc).pack(side=tk.LEFT, padx=4)
    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
    tk.Label(top_bar, text="Filtruj:", bg=bg_top, fg=fg_top, font=FONT).pack(side=tk.LEFT, padx=(0, 4))
    filter_btn = ttk.Button(top_bar, text="Filtruj", command=lambda: _open_filter())
    filter_btn.pack(side=tk.LEFT, padx=4)

    # ── Callbacki tabeli ─────────────────────────────────────────────────────
    def _on_edit(_row_idx: int, row_data: List[Any]) -> None:
        open_edit_session_dialog(
            tab, row_data,
            refresh_callback=lambda **_kw: fill_sesje_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab)),  # type: ignore[misc]
        )

    def _on_sort(col_idx: int) -> None:
        col_name = _HEADERS[col_idx]
        if active_sort_sesje.get("column") == col_name:
            active_sort_sesje["reverse"] = not active_sort_sesje.get("reverse", False)
        else:
            active_sort_sesje["column"]  = col_name
            active_sort_sesje["reverse"] = False
        sort_var.set(col_name)
        _apply_and_draw()

    def _on_right_click(_row_idx: int, row_data: List[Any], event: Any) -> None:
        def _edit() -> None:
            _on_edit(_row_idx, row_data)

        def _del() -> None:
            sesja_id   = row_data[0]
            sesja_data = row_data[1]
            if messagebox.askyesno(
                    "Usuń sesję",
                    f"Czy na pewno chcesz usunąć sesję z dnia {sesja_data}?\n\nOperacja jest nieodwracalna.",
                    parent=tab):
                try:
                    with sqlite3.connect(DB_FILE) as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM sesje_gracze WHERE sesja_id=?", (sesja_id,))
                        c.execute("DELETE FROM sesje_rpg WHERE id=?", (sesja_id,))
                        conn.commit()
                    fill_sesje_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
                except sqlite3.Error as e:
                    messagebox.showerror("Błąd bazy danych", f"Nie udało się usunąć sesji:\n{e}", parent=tab)

        ctx = tk.Menu(tab, tearoff=0)
        ctx.add_command(label="Edytuj", command=_edit)
        ctx.add_separator()
        ctx.add_command(label="Usuń",   command=_del)
        ctx.tk_popup(event.x_root, event.y_root)
        ctx.grab_release()

    # ── Tabela ───────────────────────────────────────────────────────────────
    tbl = CTkDataTable(
        tab,
        headers=_HEADERS,
        col_widths=_compute_widths(data_ref[0]) if data_ref[0] else [44, 100, 160, 200, 120, 260],
        data=[],
        edit_callback=_on_edit,
        id_col=0,
        row_color_fn=_row_color,
        center_cols=[0],
        dark_mode=dark_mode,
        sort_callback=_on_sort,
        right_click_callback=_on_right_click,
        show_row_numbers=True,
    )
    tbl.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    tab.rowconfigure(1, weight=1)
    tab.columnconfigure(0, weight=1)
    _table[0] = tbl

    # ── Zapisz cache na widgecie ───────────────────────────────────────────
    tab._sesje_tab_cache = {  # type: ignore[attr-defined]
        'data_ref':  data_ref,
        'apply_fn':  _apply_and_draw,
        'table_ref': tbl,
        'dark_mode': dark_mode,
    }

    # ── Dialog filtrowania ────────────────────────────────────────────────────
    def _open_filter() -> None:
        dlg = ctk.CTkToplevel(tab)
        dlg.title("Filtruj sesje RPG")
        dlg.transient(tab.winfo_toplevel())
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 400, 300)

        mf = ctk.CTkFrame(dlg)
        mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        cur = data_ref[0]  # bieżące dane (aktualne po każdym odświeżeniu)

        # Rok
        ctk.CTkLabel(mf, text="Rok:").grid(row=0, column=0, sticky="w", pady=8)
        years: set[str] = set()
        for r in cur:
            if r[1]:
                try:
                    years.add(str(r[1]).split('-')[0])
                except Exception:
                    pass
        year_var_ = tk.StringVar(value=active_filters_sesje.get('year', 'Wszystkie'))
        ttk.Combobox(
            mf, textvariable=year_var_,
            values=['Wszystkie'] + sorted(years, reverse=True),
            width=22, state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=8, padx=(10, 0))

        # System
        ctk.CTkLabel(mf, text="System:").grid(row=1, column=0, sticky="w", pady=8)
        systems: set[str] = {str(r[2]) for r in cur if r[2]}
        system_var_ = tk.StringVar(value=active_filters_sesje.get('system', 'Wszystkie'))
        ttk.Combobox(
            mf, textvariable=system_var_,
            values=['Wszystkie'] + sorted(systems),
            width=22, state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Typ sesji
        ctk.CTkLabel(mf, text="Typ sesji:").grid(row=2, column=0, sticky="w", pady=8)
        typ_var_ = tk.StringVar(value=active_filters_sesje.get('typ', 'Wszystkie'))
        ttk.Combobox(
            mf, textvariable=typ_var_,
            values=['Wszystkie', 'Kampania', 'Jednostrzał'],
            width=22, state="readonly",
        ).grid(row=2, column=1, sticky="ew", pady=8, padx=(10, 0))

        # Mistrz Gry
        ctk.CTkLabel(mf, text="Mistrz Gry:").grid(row=3, column=0, sticky="w", pady=8)
        mgs: set[str] = {str(r[4]) for r in cur if r[4]}
        mg_var_ = tk.StringVar(value=active_filters_sesje.get('mg', 'Wszystkie'))
        ttk.Combobox(
            mf, textvariable=mg_var_,
            values=['Wszystkie'] + sorted(mgs),
            width=22, state="readonly",
        ).grid(row=3, column=1, sticky="ew", pady=8, padx=(10, 0))

        mf.columnconfigure(1, weight=1)

        bf = ctk.CTkFrame(mf, fg_color="transparent")
        bf.grid(row=4, column=0, columnspan=2, pady=(20, 0))

        def _apply() -> None:
            active_filters_sesje['year']   = year_var_.get()
            active_filters_sesje['system'] = system_var_.get()
            active_filters_sesje['typ']    = typ_var_.get()
            active_filters_sesje['mg']     = mg_var_.get()
            _apply_and_draw()
            dlg.destroy()

        def _reset() -> None:
            active_filters_sesje.clear()
            _apply_and_draw()
            dlg.destroy()

        ctk.CTkButton(bf, text="Zastosuj", command=_apply,
                      fg_color="#2E7D32", hover_color="#1B5E20",
                      width=90).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(bf, text="Resetuj",  command=_reset,
                      fg_color="#1976D2", hover_color="#1565C0",
                      width=90).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(bf, text="Anuluj",   command=dlg.destroy,
                      fg_color="#666666", hover_color="#555555",
                      width=90).pack(side=tk.LEFT, padx=5)

        dlg.after(300, lambda: dlg.winfo_exists() and (
            dlg.deiconify(), dlg.lift(), dlg.focus_force()))

    # ── Pierwsze wypełnienie ─────────────────────────────────────────────────
    _apply_and_draw()


def usun_zaznaczona_sesja(tab: tk.Frame, refresh_callback: Optional[Callable[..., None]] = None) -> None:
    """Usuwa zaznaczoną sesję z bazy danych"""
    table: Optional[CTkDataTable] = None
    for widget in tab.winfo_children():
        if isinstance(widget, CTkDataTable):
            table = widget
            break

    if table is None:
        messagebox.showerror("Błąd", "Nie znaleziono tabeli sesji RPG.", parent=tab)
        return

    sel = table.get_selected()
    if not sel:
        messagebox.showinfo("Brak wyboru", "Zaznacz sesję do usunięcia w tabeli.", parent=tab)
        return

    _, row_data = sel
    sesja_id   = row_data[0]
    sesja_data = row_data[1]

    result = messagebox.askyesno(
        "Potwierdzenie usunięcia",
        f"Czy na pewno chcesz usunąć sesję z dnia {sesja_data}?\n\nOperacja jest nieodwracalna.",
        parent=tab
    )

    if result:
        try:
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM sesje_gracze WHERE sesja_id = ?", (sesja_id,))
                c.execute("DELETE FROM sesje_rpg WHERE id = ?", (sesja_id,))
                conn.commit()
            messagebox.showinfo("Sukces", "Sesja została usunięta z bazy.", parent=tab)
            if refresh_callback:
                refresh_callback()
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy danych", f"Nie udało się usunąć sesji:\n{str(e)}", parent=tab)

# Alias dla kompatybilności z main.py
# Funkcja open_edit_session_dialog została przeniesiona do sesje_rpg_dialogs.py

# Alias dla kompatybilności z main.py
usun_zaznaczony_sesja = usun_zaznaczona_sesja
