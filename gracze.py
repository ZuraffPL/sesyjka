# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import tkinter as tk
import tksheet  # type: ignore
from tkinter import ttk, messagebox
import sqlite3
from typing import Optional, Callable, Sequence, Any, Union, List, Dict
import customtkinter as ctk  # type: ignore

DB_FILE = "gracze.db"

# Moduł: Gracze
# Tutaj będą funkcje i klasy związane z obsługą graczy

# Przechowuj aktywne filtry na poziomie modułu
active_filters_gracze: Dict[str, Any] = {}

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

def apply_gender_colors(sheet: tksheet.Sheet, data: list[list[str]], dark_mode: bool) -> None:
    """Aplikuje kolorowanie wierszy wg płci gracza."""
    gender_col = 3  # Kolumna "Płeć"
    
    # Palety kolorów dla trybu jasnego
    light_colors = {
        "Kobieta": "#ffe6f0",      # Jasnoróżowy
        "Mężczyzna": "#e6f3ff",    # Jasnobłękitny  
        "Niebinarna": "#fff2e6",   # Jasnopomarańczowy
        "Inne": "#f0e6ff"          # Jasnofioletowy
    }
    
    # Palety kolorów dla trybu ciemnego
    dark_colors = {
        "Kobieta": "#4a1a3a",      # Ciemnoróżowy
        "Mężczyzna": "#1a3a4a",    # Ciemnobłękitny
        "Niebinarna": "#4a3a1a",   # Ciemnopomarańczowy  
        "Inne": "#3a1a4a"          # Ciemnofioletowy
    }
    
    colors = dark_colors if dark_mode else light_colors
    
    for r, row in enumerate(data):
        if r < len(data) and gender_col < len(row):
            gender = row[gender_col]
            if gender in colors:
                # Podświetl cały wiersz
                sheet.highlight_rows(r, bg=colors[gender])

def apply_status_colors(sheet: Any, data: list[list[str]], records: list[tuple[Any, ...]], dark_mode: bool = False) -> None:
    """Stosuje kolory dla głównego użytkownika i ważnych osób"""
    # Kolory dla trybu jasnego
    light_main_user = "#fff9e6"    # Jasny złoty/żółty
    light_important = "#f0e6ff"     # Jasny fioletowy
    
    # Kolory dla trybu ciemnego  
    dark_main_user = "#4a4a1a"     # Ciemny złoty/żółty
    dark_important = "#3a1a4a"      # Ciemny fioletowy
    
    main_color = dark_main_user if dark_mode else light_main_user
    important_color = dark_important if dark_mode else light_important
    
    for r, rec in enumerate(records):
        if len(rec) > 6:
            is_main = rec[5] == 1
            is_important = rec[6] == 1
            
            # Główny użytkownik ma priorytet
            if is_main:
                sheet.highlight_rows(r, bg=main_color)
            elif is_important:
                sheet.highlight_rows(r, bg=important_color)

def dodaj_gracza(parent: Optional[tk.Tk] = None, refresh_callback: Optional[Callable[..., None]] = None) -> None:
    if parent is None:
        parent = tk._default_root # type: ignore
    
    # Sprawdź tryb ciemny
    _dark_mode = parent and hasattr(parent, 'dark_mode') and getattr(parent, 'dark_mode', False)
    
    # Dialog CustomTkinter
    dialog = ctk.CTkToplevel(parent)  # type: ignore
    dialog.title("Dodaj gracza do bazy")
    dialog.transient(parent) # type: ignore
    dialog.grab_set()
    dialog.resizable(True, False)
    
    if parent is not None:
        parent.update_idletasks() # type: ignore
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200 # type: ignore
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 180 # type: ignore
        dialog.geometry(f"420x380+{x}+{y}")
    
    # Główny frame
    main_frame = ctk.CTkFrame(dialog, fg_color="transparent")  # type: ignore
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # ID gracza
    ctk.CTkLabel(main_frame, text="ID gracza:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, pady=(0, 10), padx=(0, 10), sticky="w")  # type: ignore
    id_entry = ctk.CTkEntry(main_frame, width=250, state="disabled")  # type: ignore
    id_entry.grid(row=0, column=1, pady=(0, 10), sticky="ew")
    id_entry.configure(state="normal")
    id_entry.insert(0, str(get_first_free_id()))
    id_entry.configure(state="disabled")

    # Nick gracza
    ctk.CTkLabel(main_frame, text="Nick gracza *", font=ctk.CTkFont(size=12)).grid(row=1, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    nick_entry = ctk.CTkEntry(main_frame, width=250, placeholder_text="Wpisz nick...")  # type: ignore
    nick_entry.grid(row=1, column=1, pady=8, sticky="ew")
    nick_entry.focus_set()

    # Imię i nazwisko
    ctk.CTkLabel(main_frame, text="Imię i nazwisko", font=ctk.CTkFont(size=12)).grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    name_entry = ctk.CTkEntry(main_frame, width=250, placeholder_text="Opcjonalnie...")  # type: ignore
    name_entry.grid(row=2, column=1, pady=8, sticky="ew")

    # Płeć
    ctk.CTkLabel(main_frame, text="Płeć", font=ctk.CTkFont(size=12)).grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    gender_var = tk.StringVar(value="Kobieta")
    gender_combo = ctk.CTkComboBox(main_frame, width=250, values=["Kobieta", "Mężczyzna", "Niebinarna", "Inne"], variable=gender_var, state="readonly")  # type: ignore
    gender_combo.grid(row=3, column=1, pady=8, sticky="ew")

    # Social media
    ctk.CTkLabel(main_frame, text="Social media / strona", font=ctk.CTkFont(size=12)).grid(row=4, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
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
    
    glowny_check = ctk.CTkCheckBox(main_frame, text="⭐ Główny użytkownik (tylko jedna osoba)", variable=glowny_var, command=on_glowny_toggle, font=ctk.CTkFont(size=11))  # type: ignore
    glowny_check.grid(row=5, column=0, columnspan=2, pady=8, sticky="w")
    
    # Checkbox ważna osoba
    wazna_check = ctk.CTkCheckBox(main_frame, text="👑 Ważna osoba", variable=wazna_var, command=on_wazna_toggle, font=ctk.CTkFont(size=11))  # type: ignore
    wazna_check.grid(row=6, column=0, columnspan=2, pady=8, sticky="w")

    def on_ok() -> None:
        nick: str = nick_entry.get().strip()
        name: str = name_entry.get().strip()
        gender: str = gender_var.get()
        social: str = social_entry.get().strip()
        glowny: int = 1 if glowny_var.get() else 0
        wazna: int = 1 if wazna_var.get() else 0
        
        if not nick:
            messagebox.showerror("Błąd", "Nick gracza jest wymagany.", parent=dialog) # type: ignore
            return
        
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS gracze (
                    id INTEGER PRIMARY KEY,
                    nick TEXT NOT NULL,
                    imie_nazwisko TEXT,
                    plec TEXT,
                    social TEXT,
                    glowny_uzytkownik INTEGER DEFAULT 0,
                    wazna INTEGER DEFAULT 0
                )
            """)
            
            # Jeśli ustawiamy głównego użytkownika, usuń flagę z pozostałych
            if glowny == 1:
                c.execute("UPDATE gracze SET glowny_uzytkownik = 0")
            
            c.execute("INSERT INTO gracze (nick, imie_nazwisko, plec, social, glowny_uzytkownik, wazna) VALUES (?, ?, ?, ?, ?, ?)", 
                     (nick, name if name else None, gender, social if social else None, glowny, wazna))
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent)) # type: ignore
        dialog.destroy()

    def on_cancel() -> None:
        dialog.destroy()

    # Przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")  # type: ignore
    btn_frame.grid(row=7, column=0, columnspan=2, pady=(15, 0))
    
    btn_ok = ctk.CTkButton(btn_frame, text="✚ Dodaj", command=on_ok, width=100, fg_color="#2E7D32", hover_color="#1B5E20", font=ctk.CTkFont(size=12, weight="bold"))  # type: ignore
    btn_ok.pack(side=tk.LEFT, padx=(0, 10))
    btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100, fg_color="#666666", hover_color="#555555", font=ctk.CTkFont(size=12))  # type: ignore
    btn_cancel.pack(side=tk.LEFT)
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)

def get_first_free_id() -> int:
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM gracze ORDER BY id ASC")
        used_ids = [row[0] for row in c.fetchall()]
    i = 1
    while i in used_ids:
        i += 1
    return i

def get_all_players() -> list[tuple[Any, ...]]:
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS gracze (
                id INTEGER PRIMARY KEY,
                nick TEXT NOT NULL,
                imie_nazwisko TEXT,
                plec TEXT,
                social TEXT,
                glowny_uzytkownik INTEGER DEFAULT 0,
                wazna INTEGER DEFAULT 0
            )
        """)
        # Migracja - dodaj kolumny jeśli nie istnieją
        try:
            c.execute("ALTER TABLE gracze ADD COLUMN glowny_uzytkownik INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Kolumna już istnieje
        try:
            c.execute("ALTER TABLE gracze ADD COLUMN wazna INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Kolumna już istnieje
        
        c.execute("SELECT id, nick, imie_nazwisko, plec, social, glowny_uzytkownik, wazna FROM gracze ORDER BY id ASC")
        return c.fetchall()

def fill_gracze_tab(tab: tk.Frame, dark_mode: bool = False) -> None:  # type: ignore
    for widget in tab.winfo_children():
        widget.destroy()
    headers: list[str] = ["ID", "Nick", "Imię i nazwisko", "Płeć", "Social media", "Status"]
    records: list[tuple[int, str, Optional[str], Optional[str], Optional[str], int, int]] = get_all_players()
    # Formatuj dane z oznaczeniami dla statusów
    data: list[list[str]] = []
    for rec in records:
        row = [str(v) if v is not None else "" for v in rec[:5]]
        # Status - główny użytkownik ma priorytet
        if rec[5] == 1:
            row.append("⭐")
        elif rec[6] == 1:
            row.append("👑")
        else:
            row.append("")
        data.append(row)
    sheet = tksheet.Sheet(tab,
        data=data,  # type: ignore
        headers=headers,
        show_x_scrollbar=True,
        show_y_scrollbar=True,
        width=1200,
        height=600)
    # Automatyczne dopasowanie szerokości kolumn do zawartości lub nagłówka
    for col in range(len(headers)):
        max_content = max([len(str(row[col])) for row in data] + [len(headers[col])])  # type: ignore
        width_px = max(80, min(400, int(max_content * 9 + 24)))
        sheet.column_width(column=col, width=width_px)
    # Wycentrowanie kolumny ID i Status
    sheet.align_columns(columns=[0, 5], align="center")
    # Włącz obsługę zaznaczania i interakcji jak u wydawców
    sheet.enable_bindings((
        "single_select",
        "row_select",
        "column_select",
        "arrowkeys",
        "right_click_popup_menu",
        "rc_select",
        "copy",
        "cut",
        "paste",
        "delete",
        "undo",
        "edit_cell",
        "column_header_click"
    )) # type: ignore
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
            data.sort(key=lambda x: int(x[0]) if x[0] else 0, reverse=reverse)
        elif col == 5:  # Status
            # Sortuj: gwiazdka, korona, puste
            def status_key(row: list[str]) -> tuple[int, str]:
                status = row[col]
                if status == '⭐':
                    return (0, status)
                elif status == '👑':
                    return (1, status)
                else:
                    return (2, status)
            data.sort(key=status_key, reverse=reverse)
        else:
            data.sort(key=lambda x: (x[col] or '').lower(), reverse=reverse)
        sheet.set_sheet_data(list(data)) # type: ignore
        for c in range(len(headers)):
            max_content = max([len(str(row[c])) for row in data] + [len(headers[c])])
            width_px = max(80, min(400, int(max_content * 9 + 24)))
            sheet.column_width(column=c, width=width_px)
        # Ponowne zastosowanie kolorowania po sortowaniu
        apply_gender_colors(sheet, data, dark_mode)
        apply_status_colors(sheet, data, records, dark_mode)
        # Ponowne zastosowanie stylowania linków
        link_col = 4
        for r, row in enumerate(data):
            if row[link_col]:
                sheet.highlight_cells(row=r, column=link_col, fg="#1a0dab" if not dark_mode else "#7baaff")
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
        dialog.title("Filtruj graczy")
        dialog.transient(tab.winfo_toplevel())
        dialog.grab_set()
        
        if dark_mode:
            apply_dark_theme_to_dialog(dialog)
        
        # Centrowanie okna
        tab.winfo_toplevel().update_idletasks()
        x = tab.winfo_toplevel().winfo_rootx() + (tab.winfo_toplevel().winfo_width() // 2) - 175
        y = tab.winfo_toplevel().winfo_rooty() + (tab.winfo_toplevel().winfo_height() // 2) - 125
        dialog.geometry(f"350x280+{x}+{y}")
        
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Filtr płci
        tk.Label(main_frame, text="Płeć:").grid(row=0, column=0, sticky="w", pady=5)
        plec_var = tk.StringVar(value=active_filters_gracze.get('plec', 'Wszystkie'))
        
        # Pobierz unikalne płcie z danych
        plci: set[str] = set()
        for row in data:
            if row[3]:  # Płeć
                plci.add(row[3])
        plec_values = ['Wszystkie'] + sorted(list(plci))
        plec_combo = ttk.Combobox(main_frame, textvariable=plec_var, values=plec_values, state="readonly", width=25)
        plec_combo.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Filtr Imię i nazwisko
        tk.Label(main_frame, text="Imię i nazwisko:").grid(row=1, column=0, sticky="w", pady=5)
        imie_var = tk.StringVar(value=active_filters_gracze.get('imie', 'Wszystkie'))
        imie_values = ['Wszystkie', 'Wpisane', 'Puste']
        imie_combo = ttk.Combobox(main_frame, textvariable=imie_var, values=imie_values, state="readonly", width=25)
        imie_combo.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Filtr Social media
        tk.Label(main_frame, text="Social media:").grid(row=2, column=0, sticky="w", pady=5)
        social_var = tk.StringVar(value=active_filters_gracze.get('social', 'Wszystkie'))
        social_values = ['Wszystkie', 'Wpisane', 'Puste']
        social_combo = ttk.Combobox(main_frame, textvariable=social_var, values=social_values, state="readonly", width=25)
        social_combo.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Filtr Status
        tk.Label(main_frame, text="Status:").grid(row=3, column=0, sticky="w", pady=5)
        status_var = tk.StringVar(value=active_filters_gracze.get('status', 'Wszystkie'))
        status_values = ['Wszystkie', 'Główny użytkownik', 'Ważna osoba', 'Zwykła osoba']
        status_combo = ttk.Combobox(main_frame, textvariable=status_var, values=status_values, state="readonly", width=25)
        status_combo.grid(row=3, column=1, sticky="ew", pady=5)
        
        main_frame.columnconfigure(1, weight=1)
        
        # Przyciski
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        def apply_filters() -> None:
            """Aplikuje filtry"""
            active_filters_gracze['plec'] = plec_var.get()
            active_filters_gracze['imie'] = imie_var.get()
            active_filters_gracze['social'] = social_var.get()
            active_filters_gracze['status'] = status_var.get()
            
            # Filtruj dane i rekordy równolegle
            filtered_data: List[Any] = []
            filtered_records: List[Any] = []
            for i, row in enumerate(data):
                # Filtr płci
                if active_filters_gracze['plec'] != 'Wszystkie':
                    if row[3] != active_filters_gracze['plec']:
                        continue
                
                # Filtr Imię i nazwisko (kolumna 2)
                if active_filters_gracze['imie'] == 'Wpisane':
                    if not row[2] or row[2].strip() == '':
                        continue
                elif active_filters_gracze['imie'] == 'Puste':
                    if row[2] and row[2].strip() != '':
                        continue
                
                # Filtr Social media (kolumna 4)
                if active_filters_gracze['social'] == 'Wpisane':
                    if not row[4] or row[4].strip() == '':
                        continue
                elif active_filters_gracze['social'] == 'Puste':
                    if row[4] and row[4].strip() != '':
                        continue
                
                # Filtr Status (kolumna 5)
                if active_filters_gracze.get('status') == 'Główny użytkownik':
                    if row[5] != '⭐':
                        continue
                elif active_filters_gracze.get('status') == 'Ważna osoba':
                    if row[5] != '👑':
                        continue
                elif active_filters_gracze.get('status') == 'Zwykła osoba':
                    if row[5] in ['⭐', '👑']:
                        continue
                
                filtered_data.append(row)
                filtered_records.append(records[i])
            
            sheet.set_sheet_data(filtered_data)  # type: ignore
            for c in range(len(headers)):
                max_content = max([len(str(row[c])) for row in filtered_data] + [len(headers[c])]) if filtered_data else len(headers[c])
                width_px = max(80, min(400, int(max_content * 9 + 24)))
                sheet.column_width(column=c, width=width_px)
            
            # Ponowne zastosowanie kolorowania po filtrowaniu
            apply_gender_colors(sheet, filtered_data, dark_mode)
            apply_status_colors(sheet, filtered_data, filtered_records, dark_mode)
            
            # Ponowne zastosowanie stylowania linków
            link_col = 4
            for r, row in enumerate(filtered_data):
                if row[link_col]:
                    sheet.highlight_cells(row=r, column=link_col, fg="#1a0dab" if not dark_mode else "#7baaff")
            
            sheet.refresh()
            
            # Aktualizuj tekst przycisku
            count = 0
            if active_filters_gracze.get('plec') != 'Wszystkie':
                count += 1
            if active_filters_gracze.get('imie') != 'Wszystkie':
                count += 1
            if active_filters_gracze.get('social') != 'Wszystkie':
                count += 1
            if active_filters_gracze.get('status') != 'Wszystkie':
                count += 1
            
            if count > 0:
                filter_btn.configure(text=f"Filtruj ({count})")
            else:
                filter_btn.configure(text="Filtruj")
            
            dialog.destroy()
        
        def reset_filters() -> None:
            """Resetuje wszystkie filtry"""
            active_filters_gracze.clear()
            sheet.set_sheet_data(list(data))  # type: ignore
            for c in range(len(headers)):
                max_content = max([len(str(row[c])) for row in data] + [len(headers[c])])
                width_px = max(80, min(400, int(max_content * 9 + 24)))
                sheet.column_width(column=c, width=width_px)
            
            # Ponowne zastosowanie kolorowania
            apply_gender_colors(sheet, data, dark_mode)
            
            # Ponowne zastosowanie stylowania linków
            link_col = 4
            for r, row in enumerate(data):
                if row[link_col]:
                    sheet.highlight_cells(row=r, column=link_col, fg="#1a0dab" if not dark_mode else "#7baaff")
            
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
    # Stylowanie kolumny Social media jako link (kolor)
    link_col = 4
    for r, row in enumerate(data):
        if row[link_col]:
            sheet.highlight_cells(row=r, column=link_col, fg="#1a0dab" if not dark_mode else "#7baaff")
    
    # Kolorowanie wierszy wg płci
    apply_gender_colors(sheet, data, dark_mode)
    # Kolorowanie wierszy dla głównego użytkownika i ważnych osób (nadpisuje kolory płci)
    apply_status_colors(sheet, data, records, dark_mode)
    # --- MENU KONTEKSTOWE ---
    menu = tk.Menu(tab, tearoff=0)
    def context_edit() -> None:
        sel = sheet.get_currently_selected()
        if sel and len(sel) >= 2:
            r, _ = sel[:2] # type: ignore
            values = data[r] # type: ignore
            open_edit_gracz_dialog(tab, values, refresh_callback=lambda **kwargs: fill_gracze_tab(tab, dark_mode=get_dark_mode_from_tab(tab))) # type: ignore
    def context_delete() -> None:
        sel = sheet.get_currently_selected()
        if sel and len(sel) >= 2:
            r, _ = sel[:2] # type: ignore
            values = data[r] # type: ignore
            if messagebox.askyesno("Usuń gracza", f"Czy na pewno chcesz usunąć gracza: {values[1]}?", parent=tab): # type: ignore
                with sqlite3.connect(DB_FILE) as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM gracze WHERE id=?", (values[0],)) # type: ignore
                    conn.commit()
                fill_gracze_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
    menu.add_command(label="Edytuj", command=context_edit)
    menu.add_command(label="Usuń", command=context_delete)
    def on_right_click(event: tk.Event) -> None:
        r = sheet.identify_row(event)
        c = sheet.identify_column(event)
        if r is not None and c is not None:
            sheet.set_currently_selected(r, c) # type: ignore
            menu.tk_popup(event.x_root, event.y_root)
    sheet.bind("<Button-3>", on_right_click) # type: ignore
    # --- KONIEC MENU KONTEKSTOWEGO ---
    def on_mouse_motion(event: tk.Event) -> None:
        r = sheet.identify_row(event)
        c = sheet.identify_column(event)
        if r is not None and c is not None and c == link_col and r < len(data) and data[r][link_col]:
            sheet.config(cursor="hand2")
        else:
            sheet.config(cursor="arrow")
    sheet.bind("<Motion>", on_mouse_motion) # type: ignore
    def on_cell_click(event: Any) -> None:
        sel = sheet.get_currently_selected()
        if sel and len(sel) >= 2:
            r, c = sel[:2] # type: ignore
            if c == link_col and data[r][link_col]:
                import webbrowser
                webbrowser.open(data[r][link_col]) # type: ignore
    sheet.extra_bindings("cell_select", on_cell_click) # type: ignore
    
    # Tryb ciemny
    if dark_mode:
        sheet.set_options(theme="dark") # type: ignore

# --- OKNO EDYCJI GRACZA ---
def open_edit_gracz_dialog(parent: tk.Widget, values: Sequence[Any], refresh_callback: Optional[Callable[..., None]] = None) -> None:
    # Sprawdź tryb ciemny
    root = parent.winfo_toplevel()
    _dark_mode = hasattr(root, 'dark_mode') and getattr(root, 'dark_mode', False)
    
    # Dialog CustomTkinter
    dialog = ctk.CTkToplevel(parent)  # type: ignore
    dialog.title("Edytuj gracza")
    dialog.transient(parent) # type: ignore
    dialog.grab_set()
    dialog.resizable(True, False)
    
    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 200
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 180
    dialog.geometry(f"420x380+{x}+{y}")
    
    # Główny frame
    main_frame = ctk.CTkFrame(dialog, fg_color="transparent")  # type: ignore
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # ID gracza
    ctk.CTkLabel(main_frame, text=f"ID gracza: {values[0]}", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")  # type: ignore
    
    # Nick gracza
    ctk.CTkLabel(main_frame, text="Nick gracza *", font=ctk.CTkFont(size=12)).grid(row=1, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    nick_entry = ctk.CTkEntry(main_frame, width=250)  # type: ignore
    nick_entry.grid(row=1, column=1, pady=8, sticky="ew")
    nick_entry.insert(0, values[1] if values[1] is not None else "")
    
    # Imię i nazwisko
    ctk.CTkLabel(main_frame, text="Imię i nazwisko", font=ctk.CTkFont(size=12)).grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    name_entry = ctk.CTkEntry(main_frame, width=250)  # type: ignore
    name_entry.grid(row=2, column=1, pady=8, sticky="ew")
    name_entry.insert(0, values[2] if values[2] is not None else "")
    
    # Płeć
    ctk.CTkLabel(main_frame, text="Płeć", font=ctk.CTkFont(size=12)).grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
    gender_var = tk.StringVar(value=values[3] if values[3] else "Kobieta")
    gender_combo = ctk.CTkComboBox(main_frame, width=250, values=["Kobieta", "Mężczyzna", "Niebinarna", "Inne"], variable=gender_var, state="readonly")  # type: ignore
    gender_combo.grid(row=3, column=1, pady=8, sticky="ew")
    
    # Social media
    ctk.CTkLabel(main_frame, text="Social media / strona", font=ctk.CTkFont(size=12)).grid(row=4, column=0, pady=8, padx=(0, 10), sticky="w")  # type: ignore
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
    
    glowny_check = ctk.CTkCheckBox(main_frame, text="⭐ Główny użytkownik (tylko jedna osoba)", variable=glowny_var, command=on_glowny_toggle, font=ctk.CTkFont(size=11))  # type: ignore
    glowny_check.grid(row=5, column=0, columnspan=2, pady=8, sticky="w")
    if glowny_var.get():
        glowny_check.select()  # type: ignore
    
    # Checkbox ważna osoba
    wazna_check = ctk.CTkCheckBox(main_frame, text="👑 Ważna osoba", variable=wazna_var, command=on_wazna_toggle, font=ctk.CTkFont(size=11))  # type: ignore
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
            messagebox.showerror("Błąd", "Nick gracza jest wymagany.", parent=dialog) # type: ignore
            return
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            
            # Jeśli ustawiamy głównego użytkownika, usuń flagę z pozostałych
            if glowny == 1:
                c.execute("UPDATE gracze SET glowny_uzytkownik = 0 WHERE id != ?", (values[0],))
            
            c.execute("UPDATE gracze SET nick=?, imie_nazwisko=?, plec=?, social=?, glowny_uzytkownik=?, wazna=? WHERE id=?", 
                     (nick, name if name else None, gender, social if social else None, glowny, wazna, values[0]))
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))
        dialog.destroy()
    
    def on_cancel() -> None:
        dialog.destroy()
    
    # Przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")  # type: ignore
    btn_frame.grid(row=7, column=0, columnspan=2, pady=(15, 0))
    
    btn_save = ctk.CTkButton(btn_frame, text="💾 Zapisz", command=on_save, width=100, fg_color="#2E7D32", hover_color="#1B5E20", font=ctk.CTkFont(size=12, weight="bold"))  # type: ignore
    btn_save.pack(side=tk.LEFT, padx=(0, 10))
    btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100, fg_color="#666666", hover_color="#555555", font=ctk.CTkFont(size=12))  # type: ignore
    btn_cancel.pack(side=tk.LEFT)
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)

def usun_zaznaczonego_gracza(tab: tk.Frame, refresh_callback: Optional[Callable[..., None]] = None) -> None:
    sheet: Optional[tksheet.Sheet] = None
    for widget in tab.winfo_children():
        if isinstance(widget, tksheet.Sheet):
            sheet = widget
            break
    if sheet is None:
        messagebox.showerror("Błąd", "Nie znaleziono tabeli graczy.", parent=tab) # type: ignore
        return
    sel = sheet.get_currently_selected()
    if not sel or len(sel) < 2:
        messagebox.showinfo("Brak wyboru", "Zaznacz gracza do usunięcia w tabeli.", parent=tab) # type: ignore
        return
    r, _ = sel[:2] # type: ignore
    values = sheet.get_row_data(r) # type: ignore
    if len(values) < 1:
        return
    gracz_id = values[0]
    if messagebox.askyesno("Usuń gracza", f"Czy na pewno chcesz usunąć gracza: {values[1]}?", parent=tab): # type: ignore
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM gracze WHERE id=?", (gracz_id,))
            conn.commit()
        if hasattr(sheet, 'delete_row'):
            sheet.delete_row(r) # type: ignore
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(tab))

# Alias dla kompatybilności z main.py
usun_zaznaczony_gracza = usun_zaznaczonego_gracza
