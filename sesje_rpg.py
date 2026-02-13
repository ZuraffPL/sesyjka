import tkinter as tk
import tksheet  # type: ignore
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from typing import Optional, Callable, Any, List, Tuple, Dict, Union
from database_manager import get_db_path

# Import funkcji dialogowych z oddzielnego modułu
from sesje_rpg_dialogs import open_edit_session_dialog

DB_FILE = get_db_path("sesje_rpg.db")

# Przechowuj aktywne filtry na poziomie modułu
active_filters_sesje: Dict[str, Any] = {}

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
        with sqlite3.connect("systemy_rpg.db") as conn:
            c = conn.cursor()
            c.execute("SELECT id, nazwa FROM systemy_rpg WHERE typ = 'Podręcznik Główny' ORDER BY nazwa")
            return c.fetchall()
    except sqlite3.Error:
        return []

def get_all_players() -> List[Tuple[int, str]]:
    """Pobiera wszystkich graczy z bazy"""
    try:
        with sqlite3.connect("gracze.db") as conn:
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
            with sqlite3.connect("systemy_rpg.db") as sys_conn:
                sys_cursor = sys_conn.cursor()
                sys_cursor.execute("SELECT nazwa FROM systemy_rpg WHERE id = ?", (session[2],))
                system_result = sys_cursor.fetchone()
                system_nazwa = system_result[0] if system_result else f"System ID {session[2]}"
        except sqlite3.Error:
            system_nazwa = f"System ID {session[2]}"
        
        try:
            # Pobierz nick MG
            with sqlite3.connect("gracze.db") as gracze_conn:
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
                        with sqlite3.connect("gracze.db") as gracze_conn:
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
    # Inicjalizuj bazę danych
    init_db()
    
    for widget in tab.winfo_children():
        widget.destroy()
    
    headers = ["ID", "Data", "System", "Typ sesji", "Mistrz Gry", "Gracze"]
    data = get_all_sessions()
    
    # Zmienna do przechowywania aktualnie wyświetlanych danych (pełne lub przefiltrowane)
    displayed_data: List[Any] = list(data)
    
    sheet = tksheet.Sheet(tab,
        data=displayed_data,  # type: ignore
        headers=headers,
        show_x_scrollbar=True,
        show_y_scrollbar=True,
        width=1200,
        height=600)
    
    # Automatyczne dopasowanie szerokości kolumn do zawartości lub nagłówka
    for col in range(len(headers)):
        max_content = max([len(str(row[col])) for row in data] + [len(headers[col])]) if data else len(headers[col])
        width_px = max(80, min(400, int(max_content * 9 + 24)))
        sheet.column_width(column=col, width=width_px)
    
    # Wycentrowanie kolumny ID
    sheet.align_columns(columns=[0], align="center")
    
    # Panel sortowania nad tabelą
    sort_frame = tk.Frame(tab)
    sort_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
    sort_label = tk.Label(sort_frame, text="Sortuj po kolumnie:")
    sort_label.pack(side=tk.LEFT, padx=(0, 6))
    sort_var = tk.StringVar(value=headers[0])
    sort_menu = ttk.Combobox(sort_frame, textvariable=sort_var, values=headers, state="readonly", width=12)
    sort_menu.pack(side=tk.LEFT)
    
    def do_sort(reverse: bool = False) -> None:
        col = headers.index(sort_var.get())
        if col == 0:
            displayed_data.sort(key=lambda x: int(x[0]) if x[0] else 0, reverse=reverse)  # type: ignore
        else:
            displayed_data.sort(key=lambda x: (x[col] or '').lower(), reverse=reverse)  # type: ignore
        sheet.set_sheet_data(list(displayed_data))  # type: ignore
        for c in range(len(headers)):
            max_content = max([len(str(row[c])) for row in displayed_data] + [len(headers[c])]) if displayed_data else len(headers[c])
            width_px = max(80, min(400, int(max_content * 9 + 24)))
            sheet.column_width(column=c, width=width_px)
        sheet.refresh()
    
    sort_asc_btn = ttk.Button(sort_frame, text="Rosnąco", command=lambda: do_sort(False))
    sort_asc_btn.pack(side=tk.LEFT, padx=4)
    sort_desc_btn = ttk.Button(sort_frame, text="Malejąco", command=lambda: do_sort(True))
    sort_desc_btn.pack(side=tk.LEFT, padx=4)
    
    # Separator
    separator = ttk.Separator(sort_frame, orient=tk.VERTICAL)
    separator.pack(side=tk.LEFT, padx=10, fill=tk.Y)
    
    # Filtrowanie
    filter_label = tk.Label(sort_frame, text="Filtruj:")
    filter_label.pack(side=tk.LEFT, padx=(0, 6))
    
    def open_filter_dialog() -> None:
        """Otwiera okno dialogowe filtrowania"""
        dialog = tk.Toplevel(tab)
        dialog.title("Filtruj sesje RPG")
        dialog.transient(tab.winfo_toplevel())
        dialog.grab_set()
        
        if dark_mode:
            apply_dark_theme_to_dialog(dialog)
        
        # Centrowanie okna
        tab.winfo_toplevel().update_idletasks()
        x = tab.winfo_toplevel().winfo_rootx() + (tab.winfo_toplevel().winfo_width() // 2) - 200
        y = tab.winfo_toplevel().winfo_rooty() + (tab.winfo_toplevel().winfo_height() // 2) - 150
        dialog.geometry(f"400x300+{x}+{y}")
        
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Filtr roku
        tk.Label(main_frame, text="Rok:").grid(row=0, column=0, sticky="w", pady=5)
        year_var = tk.StringVar(value=active_filters_sesje.get('year', 'Wszystkie'))
        
        # Pobierz unikalne lata z danych
        years: set[str] = set()
        for row in data:
            if row[1]:  # Data sesji
                try:
                    year = row[1].split('-')[0]
                    years.add(year)
                except:
                    pass
        year_values = ['Wszystkie'] + sorted(list(years), reverse=True)
        year_combo = ttk.Combobox(main_frame, textvariable=year_var, values=year_values, state="readonly", width=25)
        year_combo.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Filtr systemu
        tk.Label(main_frame, text="System:").grid(row=1, column=0, sticky="w", pady=5)
        system_var = tk.StringVar(value=active_filters_sesje.get('system', 'Wszystkie'))
        
        systems: set[str] = set()
        for row in data:
            if row[2]:  # System
                systems.add(row[2])
        system_values = ['Wszystkie'] + sorted(list(systems))
        system_combo = ttk.Combobox(main_frame, textvariable=system_var, values=system_values, state="readonly", width=25)
        system_combo.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Filtr typu sesji
        tk.Label(main_frame, text="Typ sesji:").grid(row=2, column=0, sticky="w", pady=5)
        typ_var = tk.StringVar(value=active_filters_sesje.get('typ', 'Wszystkie'))
        typ_values = ['Wszystkie', 'Kampania', 'Jednostrzał']
        typ_combo = ttk.Combobox(main_frame, textvariable=typ_var, values=typ_values, state="readonly", width=25)
        typ_combo.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Filtr Mistrza Gry
        tk.Label(main_frame, text="Mistrz Gry:").grid(row=3, column=0, sticky="w", pady=5)
        mg_var = tk.StringVar(value=active_filters_sesje.get('mg', 'Wszystkie'))
        
        mgs: set[str] = set()
        for row in data:
            if row[4]:  # MG
                mgs.add(row[4])
        mg_values = ['Wszystkie'] + sorted(list(mgs))
        mg_combo = ttk.Combobox(main_frame, textvariable=mg_var, values=mg_values, state="readonly", width=25)
        mg_combo.grid(row=3, column=1, sticky="ew", pady=5)
        
        main_frame.columnconfigure(1, weight=1)
        
        # Przyciski
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        def apply_filters() -> None:
            """Aplikuje filtry"""
            nonlocal displayed_data
            active_filters_sesje['year'] = year_var.get()
            active_filters_sesje['system'] = system_var.get()
            active_filters_sesje['typ'] = typ_var.get()
            active_filters_sesje['mg'] = mg_var.get()
            
            # Filtruj dane
            filtered_data: List[Any] = []
            for row in data:
                # Filtr roku
                if active_filters_sesje['year'] != 'Wszystkie':
                    if not row[1] or not row[1].startswith(active_filters_sesje['year']):
                        continue
                
                # Filtr systemu
                if active_filters_sesje['system'] != 'Wszystkie':
                    if row[2] != active_filters_sesje['system']:
                        continue
                
                # Filtr typu sesji
                if active_filters_sesje['typ'] != 'Wszystkie':
                    if not row[3] or not row[3].startswith(active_filters_sesje['typ']):
                        continue
                
                # Filtr MG
                if active_filters_sesje['mg'] != 'Wszystkie':
                    if row[4] != active_filters_sesje['mg']:
                        continue
                
                filtered_data.append(row)
            
            displayed_data = filtered_data
            sheet.set_sheet_data(displayed_data)  # type: ignore
            for c in range(len(headers)):
                max_content = max([len(str(row[c])) for row in displayed_data] + [len(headers[c])]) if displayed_data else len(headers[c])
                width_px = max(80, min(400, int(max_content * 9 + 24)))
                sheet.column_width(column=c, width=width_px)
            sheet.refresh()
            
            # Aktualizuj tekst przycisku
            count = sum(1 for v in active_filters_sesje.values() if v != 'Wszystkie')
            if count > 0:
                filter_btn.configure(text=f"Filtruj ({count})")
            else:
                filter_btn.configure(text="Filtruj")
            
            dialog.destroy()
        
        def reset_filters() -> None:
            """Resetuje wszystkie filtry"""
            nonlocal displayed_data
            active_filters_sesje.clear()
            displayed_data = list(data)
            sheet.set_sheet_data(displayed_data)  # type: ignore
            for c in range(len(headers)):
                max_content = max([len(str(row[c])) for row in displayed_data] + [len(headers[c])]) if displayed_data else len(headers[c])
                width_px = max(80, min(400, int(max_content * 9 + 24)))
                sheet.column_width(column=c, width=width_px)
            sheet.refresh()
            filter_btn.configure(text="Filtruj")
            dialog.destroy()
        
        ttk.Button(btn_frame, text="Zastosuj", command=apply_filters).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Resetuj", command=reset_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Anuluj", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    filter_btn = ttk.Button(sort_frame, text="Filtruj", command=open_filter_dialog)
    filter_btn.pack(side=tk.LEFT, padx=4)
    
    # Przesuń tabelę w dół (row=1)
    sheet.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    tab.rowconfigure(1, weight=1)
    tab.columnconfigure(0, weight=1)
    
    # Menu kontekstowe
    menu = tk.Menu(tab, tearoff=0)
    
    def context_delete() -> None:
        """Usuwa zaznaczoną sesję"""
        sel = sheet.get_currently_selected()  # type: ignore
        if sel and len(sel) >= 2:  # type: ignore
            r, _ = sel[:2]  # type: ignore
            if r < len(displayed_data):
                values = displayed_data[r]  # type: ignore
                sesja_id = values[0]  # type: ignore
                sesja_data = values[1]  # type: ignore
                
                result = messagebox.askyesno(
                    "Potwierdzenie usunięcia",
                    f"Czy na pewno chcesz usunąć sesję z dnia {sesja_data}?\n\nOperacja jest nieodwracalna.",
                    parent=tab
                )
                
                if result:
                    try:
                        with sqlite3.connect(DB_FILE) as conn:
                            c = conn.cursor()
                            c.execute("DELETE FROM sesje_gracze WHERE sesja_id = ?", (sesja_id,))  # type: ignore
                            c.execute("DELETE FROM sesje_rpg WHERE id = ?", (sesja_id,))  # type: ignore
                            conn.commit()
                        
                        messagebox.showinfo("Sukces", "Sesja została usunięta z bazy.", parent=tab)
                        fill_sesje_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
                    
                    except sqlite3.Error as e:
                        messagebox.showerror("Błąd bazy danych", f"Nie udało się usunąć sesji:\n{str(e)}", parent=tab)
    
    def context_edit() -> None:
        """Edytuje zaznaczoną sesję"""
        sel = sheet.get_currently_selected()
        if sel and len(sel) >= 2:
            r, _ = sel[:2]  # type: ignore
            if r < len(displayed_data):
                values = displayed_data[r]  # type: ignore
                open_edit_session_dialog(tab, values, refresh_callback=lambda **kwargs: fill_sesje_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab)))  # type: ignore
    
    menu.add_command(label="Edytuj", command=context_edit)
    menu.add_separator()
    menu.add_command(label="Usuń", command=context_delete)
    
    def show_context_menu(event: Any) -> None:
        """Obsługuje kliknięcie prawym przyciskiem myszy"""
        r = sheet.identify_row(event)  # type: ignore
        c = sheet.identify_column(event)  # type: ignore
        if r is not None and c is not None:
            sheet.set_currently_selected(r, c)  # type: ignore
        try:
            menu.tk_popup(event.x_root, event.y_root)  # type: ignore
        finally:
            menu.grab_release()
    
    sheet.bind("<Button-3>", show_context_menu)  # type: ignore
    
    # Dodaj dodatkowe opcje dla tksheet
    sheet.enable_bindings(
        "single_select",
        "row_select",
        "column_width_resize",
        "double_click_column_resize",
        "rc_select",
        "copy",
        "paste",
        "delete",
        "select_all"
    )
    
    sheet.set_all_column_widths()
    
    # Sortowanie po kliknięciu nagłówka dowolnej kolumny
    sort_state: Dict[str, Any] = {'col': None, 'reverse': False}  # type: ignore
    def on_header_click(event: Any) -> None:
        c = sheet.identify_column(event)
        if c is not None:
            col = c
            if sort_state['col'] == col:
                sort_state['reverse'] = not sort_state['reverse']
            else:
                sort_state['col'] = col
                sort_state['reverse'] = False
            if col == 0:
                displayed_data.sort(key=lambda x: int(x[0]) if x[0] else 0, reverse=sort_state['reverse'])  # type: ignore
            else:
                displayed_data.sort(key=lambda x: (x[col] or '').lower(), reverse=sort_state['reverse'])  # type: ignore
            sheet.set_sheet_data(displayed_data)  # type: ignore
    
    sheet.extra_bindings("header_select", on_header_click)  # type: ignore
    
    # Kolorowanie wierszy według miesiąca z daty sesji
    def apply_month_colors():
        """Aplikuje kolory tła wierszy według miesiąca z daty sesji"""
        # Kolory dla każdego miesiąca (tryb jasny i ciemny) - wysoki kontrast
        month_colors_light = {
            1: "#D1E7FF",   # Styczeń - mocny jasny niebieski
            2: "#E6D1FF",   # Luty - mocny jasny fioletowy  
            3: "#D1FFD1",   # Marzec - mocny jasny zielony
            4: "#FFF4C4",   # Kwiecień - mocny jasny żółty
            5: "#FFD1D1",   # Maj - mocny jasny różowy
            6: "#D1F4FF",   # Czerwiec - mocny jasny cyan
            7: "#FFDED1",   # Lipiec - mocny jasny pomarańczowy
            8: "#F0D1FF",   # Sierpień - mocny jasny lawendowy
            9: "#D1FFB8",   # Wrzesień - mocny jasny limonowy
            10: "#FFD8B8",  # Październik - mocny jasny brzoskwiniowy
            11: "#D1D1FF",  # Listopad - mocny jasny indygo
            12: "#FFD1E6"   # Grudzień - mocny jasny magenta
        }
        
        month_colors_dark = {
            1: "#0D4F73",   # Styczeń - mocny ciemny niebieski
            2: "#4D0D73",   # Luty - mocny ciemny fioletowy
            3: "#0D730D",   # Marzec - mocny ciemny zielony
            4: "#73730D",   # Kwiecień - mocny ciemny żółty
            5: "#730D0D",   # Maj - mocny ciemny czerwony
            6: "#0D7373",   # Czerwiec - mocny ciemny cyan
            7: "#73470D",   # Lipiec - mocny ciemny pomarańczowy
            8: "#470D73",   # Sierpień - mocny ciemny lawendowy
            9: "#47730D",   # Wrzesień - mocny ciemny limonowy
            10: "#73470D",  # Październik - mocny ciemny brzoskwiniowy
            11: "#0D0D73",  # Listopad - mocny ciemny indygo
            12: "#730D47"   # Grudzień - mocny ciemny magenta
        }
        
        colors = month_colors_dark if dark_mode else month_colors_light
        
        for r, row in enumerate(displayed_data):
            if len(row) > 1 and row[1]:  # Sprawdź czy istnieje data
                try:
                    # Parsuj datę w formacie YYYY-MM-DD
                    date_str = str(row[1])
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    month = date_obj.month
                    
                    # Aplikuj kolor dla całego wiersza
                    if month in colors:
                        for col in range(len(headers)):
                            sheet.highlight_cells(row=r, column=col, bg=colors[month])
                except (ValueError, TypeError):
                    # W przypadku błędu parsowania daty, zostaw domyślny kolor
                    pass
    
    # Aplikuj kolorowanie miesiąca
    apply_month_colors()
    
    # Funkcja do ponownego kolorowania po sortowaniu
    def reapply_colors_after_sort():
        apply_month_colors()
    
    # Nadpisz funkcję sortowania, żeby zachować kolorowanie
    original_do_sort = do_sort
    def do_sort_with_colors(reverse: bool = False) -> None:
        original_do_sort(reverse)
        reapply_colors_after_sort()
    
    # Zastąp przyciski sortowania
    sort_asc_btn.config(command=lambda: do_sort_with_colors(False))
    sort_desc_btn.config(command=lambda: do_sort_with_colors(True))
    
    # Nadpisz funkcję sortowania nagłówków
    original_header_click = on_header_click
    def on_header_click_with_colors(event: Any) -> None:
        original_header_click(event)
        reapply_colors_after_sort()
    
    sheet.extra_bindings("header_select", on_header_click_with_colors)  # type: ignore
    
    # Tryb ciemny
    if dark_mode:
        sheet.set_options(theme="dark")  # type: ignore
    
    # Automatycznie aplikuj filtry jeśli są aktywne
    if active_filters_sesje:
        # Filtruj dane
        filtered_data: List[Any] = []
        for row in data:
            # Filtr roku
            if active_filters_sesje.get('year', 'Wszystkie') != 'Wszystkie':
                if not row[1] or not row[1].startswith(active_filters_sesje['year']):
                    continue
            
            # Filtr systemu
            if active_filters_sesje.get('system', 'Wszystkie') != 'Wszystkie':
                if row[2] != active_filters_sesje['system']:
                    continue
            
            # Filtr typu sesji
            if active_filters_sesje.get('typ', 'Wszystkie') != 'Wszystkie':
                if not row[3] or not row[3].startswith(active_filters_sesje['typ']):
                    continue
            
            # Filtr MG
            if active_filters_sesje.get('mg', 'Wszystkie') != 'Wszystkie':
                if row[4] != active_filters_sesje['mg']:
                    continue
            
            filtered_data.append(row)
        
        displayed_data.clear()
        displayed_data.extend(filtered_data)
        sheet.set_sheet_data(displayed_data)  # type: ignore
        for c in range(len(headers)):
            max_content = max([len(str(row[c])) for row in displayed_data] + [len(headers[c])]) if displayed_data else len(headers[c])
            width_px = max(80, min(400, int(max_content * 9 + 24)))
            sheet.column_width(column=c, width=width_px)
        sheet.refresh()
        
        # Ponownie aplikuj kolorowanie po filtracji
        apply_month_colors()
        
        # Aktualizuj tekst przycisku
        count = sum(1 for v in active_filters_sesje.values() if v != 'Wszystkie')
        if count > 0:
            filter_btn.configure(text=f"Filtruj ({count})")

def usun_zaznaczona_sesja(tab: tk.Frame, refresh_callback: Optional[Callable[..., None]] = None) -> None:
    """Usuwa zaznaczoną sesję z bazy danych"""
    sheet = None
    for widget in tab.winfo_children():
        if hasattr(widget, 'get_currently_selected'):
            sheet = widget
            break
    
    if sheet is None:
        messagebox.showerror("Błąd", "Nie znaleziono tabeli sesji RPG.", parent=tab)
        return
    
    sel = sheet.get_currently_selected()  # type: ignore
    if not sel or len(sel) < 2:  # type: ignore
        messagebox.showinfo("Brak wyboru", "Zaznacz sesję do usunięcia w tabeli.", parent=tab)
        return
    
    r, _ = sel[:2]  # type: ignore
    values = sheet.get_row_data(r)  # type: ignore
    if len(values) < 2:  # type: ignore
        return
    
    sesja_id = values[0]  # type: ignore
    sesja_data = values[1]  # type: ignore
    
    # Potwierdzenie usunięcia
    result = messagebox.askyesno(
        "Potwierdzenie usunięcia",
        f"Czy na pewno chcesz usunąć sesję z dnia {sesja_data}?\n\nOperacja jest nieodwracalna.",
        parent=tab
    )
    
    if result:
        try:
            # Usuń z bazy danych
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                # Usuń relacje sesja-gracze (CASCADE powinno to zrobić automatycznie)
                c.execute("DELETE FROM sesje_gracze WHERE sesja_id = ?", (sesja_id,))  # type: ignore
                # Usuń sesję
                c.execute("DELETE FROM sesje_rpg WHERE id = ?", (sesja_id,))  # type: ignore
                conn.commit()
            
            messagebox.showinfo("Sukces", "Sesja została usunięta z bazy.", parent=tab)
            
            # Odśwież widok
            if refresh_callback:
                refresh_callback()
        
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy danych", f"Nie udało się usunąć sesji:\n{str(e)}", parent=tab)

# Alias dla kompatybilności z main.py
# Funkcja open_edit_session_dialog została przeniesiona do sesje_rpg_dialogs.py

# Alias dla kompatybilności z main.py
usun_zaznaczony_sesja = usun_zaznaczona_sesja
