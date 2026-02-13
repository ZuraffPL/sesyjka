# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from typing import Optional, Union, List, Dict, Any
import tksheet  # type: ignore # <- przywrócono wymagany import
import customtkinter as ctk  # type: ignore

DB_FILE = "wydawcy.db"

# Przechowuj aktywne filtry na poziomie modułu
active_filters_wydawcy: Dict[str, Any] = {}

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


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS wydawcy (
                id INTEGER PRIMARY KEY,
                nazwa TEXT NOT NULL,
                strona TEXT,
                kraj TEXT
            )
        """)
        # Dodaj kolumnę kraj jeśli nie istnieje (migracja)
        c.execute("PRAGMA table_info(wydawcy)")
        columns = [row[1] for row in c.fetchall()]
        if 'kraj' not in columns:
            c.execute("ALTER TABLE wydawcy ADD COLUMN kraj TEXT")
        conn.commit()


def get_all_publishers():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, nazwa, strona, kraj FROM wydawcy ORDER BY id ASC")
        return c.fetchall()


def get_first_free_id():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM wydawcy ORDER BY id ASC")
        used_ids = [row[0] for row in c.fetchall()]
    i = 1
    while i in used_ids:
        i += 1
    return i


def add_publisher_to_db(id_wydawcy: int, nazwa: str, strona: Optional[str], kraj: Optional[str]):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO wydawcy (id, nazwa, strona, kraj) VALUES (?, ?, ?, ?)", (id_wydawcy, nazwa, strona, kraj))
        conn.commit()


def get_dark_mode_from_tab(tab): # type: ignore
    # Szuka atrybutu dark_mode w głównym oknie
    root = tab.winfo_toplevel() # type: ignore
    return getattr(root, 'dark_mode', False) # type: ignore

def dodaj_wydawce(parent: tk.Tk, refresh_callback=None): # type: ignore
    init_db()
    reserved_id = get_first_free_id()

    dialog = ctk.CTkToplevel(parent)
    dialog.title("Dodaj wydawcę do bazy")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(True, False)

    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 180
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 130
    dialog.geometry(f"400x280+{x}+{y}")

    # Główna ramka
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # ID wydawcy (tylko do odczytu)
    ctk.CTkLabel(main_frame, text=f"ID wydawcy: {reserved_id}", font=("Segoe UI", 12)).grid(
        row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

    # Nazwa wydawcy
    ctk.CTkLabel(main_frame, text="Nazwa wydawcy *").grid(row=1, column=0, pady=5, sticky="w")
    nazwa_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="Wprowadź nazwę wydawcy")
    nazwa_entry.grid(row=1, column=1, pady=5, padx=(10, 0), sticky="ew")
    nazwa_entry.focus_set()

    # Strona internetowa
    ctk.CTkLabel(main_frame, text="Strona internetowa").grid(row=2, column=0, pady=5, sticky="w")
    strona_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="https://...")
    strona_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky="ew")

    # Kraj wydawcy
    ctk.CTkLabel(main_frame, text="Kraj wydawcy").grid(row=3, column=0, pady=5, sticky="w")
    kraj_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="Wprowadź kraj")
    kraj_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky="ew")

    main_frame.columnconfigure(1, weight=1)

    def on_ok():
        nazwa = nazwa_entry.get().strip()
        strona = strona_entry.get().strip()
        kraj = kraj_entry.get().strip()
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa wydawcy jest wymagana.", parent=dialog) # type: ignore
            return
        add_publisher_to_db(reserved_id, nazwa, strona if strona else None, kraj if kraj else None)
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    # Ramka na przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))

    btn_ok = ctk.CTkButton(btn_frame, text="Dodaj", command=on_ok, width=100,
                           fg_color="#2E7D32", hover_color="#1B5E20")
    btn_ok.pack(side=tk.LEFT, padx=10)
    btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100,
                               fg_color="#666666", hover_color="#555555")
    btn_cancel.pack(side=tk.LEFT, padx=10)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)


def fill_wydawcy_tab(tab: tk.Frame, dark_mode=False): # type: ignore
    for widget in tab.winfo_children():
        widget.destroy()
    init_db()
    records = get_all_publishers()
    headers = ["ID", "Nazwa", "Strona", "Kraj"]
    data = [[v if v is not None else "" for v in rec] for rec in records]
    sheet = tksheet.Sheet(tab,
        data=data,
        headers=headers,
        show_x_scrollbar=True,
        show_y_scrollbar=True,
        width=1200,
        height=600)
    # Automatyczne dopasowanie szerokości kolumn do zawartości lub nagłówka
    for col in range(len(headers)):
        max_content = max([len(str(row[col])) for row in data] + [len(headers[col])])
        width_px = max(80, min(400, int(max_content * 9 + 24)))
        sheet.column_width(column=col, width=width_px)
    # Wycentrowanie kolumn ID i Kraj
    sheet.align_columns(columns=[0, 3], align="center")
    # Aktywujemy event column_header_click w enable_bindings (można zostawić, nie przeszkadza)
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
    # Dodaj ramkę na przyciski sortowania nad tabelą
    sort_frame = tk.Frame(tab)
    sort_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
    sort_label = tk.Label(sort_frame, text="Sortuj po kolumnie:")
    sort_label.pack(side=tk.LEFT, padx=(0, 6))
    sort_var = tk.StringVar(value=headers[0])
    sort_menu = ttk.Combobox(sort_frame, textvariable=sort_var, values=headers, state="readonly", width=12)
    sort_menu.pack(side=tk.LEFT)
    def do_sort(reverse=False): # type: ignore
        col = headers.index(sort_var.get())
        if col == 0:
            data.sort(key=lambda x: int(x[0]) if x[0] else 0, reverse=reverse)
        else:
            data.sort(key=lambda x: (x[col] or '').lower(), reverse=reverse)
        sheet.set_sheet_data(list(data)) # type: ignore
        # Automatyczne dopasowanie szerokości kolumn po sortowaniu
        for c in range(len(headers)):
            max_content = max([len(str(row[c])) for row in data] + [len(headers[c])])
            width_px = max(80, min(400, int(max_content * 9 + 24)))
            sheet.column_width(column=c, width=width_px)
        sheet.refresh()
        for r, row in enumerate(data):
            if row[link_col]:
                sheet.highlight_cells(row=r, column=link_col, fg="#1a0dab" if not dark_mode else "#7baaff")
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
        dialog = ctk.CTkToplevel(tab)
        dialog.title("Filtruj wydawców")
        dialog.transient(tab.winfo_toplevel())
        dialog.grab_set()
        
        # Centrowanie okna
        tab.winfo_toplevel().update_idletasks()
        x = tab.winfo_toplevel().winfo_rootx() + (tab.winfo_toplevel().winfo_width() // 2) - 175
        y = tab.winfo_toplevel().winfo_rooty() + (tab.winfo_toplevel().winfo_height() // 2) - 100
        dialog.geometry(f"380x220+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Filtr Kraju
        ctk.CTkLabel(main_frame, text="Kraj:").grid(row=0, column=0, sticky="w", pady=8)
        
        # Pobierz unikalne kraje z danych
        kraje: set[str] = set()
        for row in data:
            if row[3]:  # Kraj
                kraje.add(row[3])
        kraj_values = ['Wszystkie'] + sorted(list(kraje))
        
        kraj_var = tk.StringVar(value=active_filters_wydawcy.get('kraj', 'Wszystkie'))
        kraj_combo = ctk.CTkComboBox(main_frame, variable=kraj_var, values=kraj_values, width=200, state="readonly")
        kraj_combo.grid(row=0, column=1, sticky="ew", pady=8, padx=(10, 0))
        
        # Filtr Strony
        ctk.CTkLabel(main_frame, text="Strona:").grid(row=1, column=0, sticky="w", pady=8)
        strona_values = ['Wszystkie', 'Wpisane', 'Puste']
        strona_var = tk.StringVar(value=active_filters_wydawcy.get('strona', 'Wszystkie'))
        strona_combo = ctk.CTkComboBox(main_frame, variable=strona_var, values=strona_values, width=200, state="readonly")
        strona_combo.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))
        
        main_frame.columnconfigure(1, weight=1)
        
        def apply_filters() -> None:
            """Aplikuje filtry"""
            active_filters_wydawcy['kraj'] = kraj_var.get()
            active_filters_wydawcy['strona'] = strona_var.get()
            
            # Filtruj dane
            filtered_data: List[Any] = []
            for row in data:
                # Filtr Kraju (kolumna 3)
                if active_filters_wydawcy['kraj'] != 'Wszystkie':
                    if row[3] != active_filters_wydawcy['kraj']:
                        continue
                
                # Filtr Strony (kolumna 2)
                if active_filters_wydawcy['strona'] == 'Wpisane':
                    if not row[2] or row[2].strip() == '':
                        continue
                elif active_filters_wydawcy['strona'] == 'Puste':
                    if row[2] and row[2].strip() != '':
                        continue
                
                filtered_data.append(row)
            
            sheet.set_sheet_data(filtered_data)  # type: ignore
            for c in range(len(headers)):
                max_content = max([len(str(row[c])) for row in filtered_data] + [len(headers[c])]) if filtered_data else len(headers[c])
                width_px = max(80, min(400, int(max_content * 9 + 24)))
                sheet.column_width(column=c, width=width_px)
            
            # Ponowne zastosowanie stylowania linków
            link_col = 2
            for r, row in enumerate(filtered_data):
                if row[link_col]:
                    sheet.highlight_cells(row=r, column=link_col, fg="#1a0dab" if not dark_mode else "#7baaff")
            
            sheet.refresh()
            
            # Aktualizuj tekst przycisku
            count = 0
            if active_filters_wydawcy.get('kraj') != 'Wszystkie':
                count += 1
            if active_filters_wydawcy.get('strona') != 'Wszystkie':
                count += 1
            
            if count > 0:
                filter_btn.configure(text=f"Filtruj ({count})")
            else:
                filter_btn.configure(text="Filtruj")
            
            dialog.destroy()
        
        def reset_filters() -> None:
            """Resetuje wszystkie filtry"""
            active_filters_wydawcy.clear()
            sheet.set_sheet_data(list(data))  # type: ignore
            for c in range(len(headers)):
                max_content = max([len(str(row[c])) for row in data] + [len(headers[c])])
                width_px = max(80, min(400, int(max_content * 9 + 24)))
                sheet.column_width(column=c, width=width_px)
            
            # Ponowne zastosowanie stylowania linków
            link_col = 2
            for r, row in enumerate(data):
                if row[link_col]:
                    sheet.highlight_cells(row=r, column=link_col, fg="#1a0dab" if not dark_mode else "#7baaff")
            
            sheet.refresh()
            filter_btn.configure(text="Filtruj")
            dialog.destroy()
        
        # Przyciski
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        
        ctk.CTkButton(btn_frame, text="Zastosuj", command=apply_filters, width=90,
                      fg_color="#2E7D32", hover_color="#1B5E20").pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Resetuj", command=reset_filters, width=90,
                      fg_color="#1976D2", hover_color="#1565C0").pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Anuluj", command=dialog.destroy, width=90,
                      fg_color="#666666", hover_color="#555555").pack(side=tk.LEFT, padx=5)
    filter_btn = ttk.Button(sort_frame, text="Filtruj", command=open_filter_dialog)
    filter_btn.pack(side=tk.LEFT, padx=4)
    
    # Przesuń tabelę w dół (row=1)
    sheet.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    tab.rowconfigure(1, weight=1)
    tab.columnconfigure(0, weight=1)

    # Stylowanie kolumny "Strona" jako link (kolor)
    link_col = 2
    for r, row in enumerate(data):
        if row[link_col]:
            sheet.highlight_cells(row=r, column=link_col, fg="#1a0dab" if not dark_mode else "#7baaff")
    # Kursor "ręka" tylko nad komórką linku
    def on_mouse_motion(event): # type: ignore
        r = sheet.identify_row(event)
        c = sheet.identify_column(event)
        if r is not None and c is not None and c == link_col and r < len(data) and data[r][link_col]:
            sheet.config(cursor="hand2")
        else:
            sheet.config(cursor="arrow")
    sheet.bind("<Motion>", on_mouse_motion) # type: ignore
    # Kliknięcie w link otwiera stronę
    def on_cell_click(event): # type: ignore
        sel = sheet.get_currently_selected()
        if sel and len(sel) >= 2:
            r, c = sel[:2] # type: ignore
            if c == link_col and data[r][link_col]:
                import webbrowser
                webbrowser.open(data[r][link_col])
    sheet.extra_bindings("cell_select", on_cell_click) # type: ignore

    # Menu kontekstowe
    menu = tk.Menu(tab, tearoff=0)
    def context_edit():
        sel = sheet.get_currently_selected()
        if sel and len(sel) >= 2:
            r, _ = sel[:2] # type: ignore
            values = data[r]
            open_edit_dialog(tab, values, refresh_callback=lambda **kwargs: fill_wydawcy_tab(tab, dark_mode=get_dark_mode_from_tab(tab))) # type: ignore
    def context_delete():
        sel = sheet.get_currently_selected()
        if sel and len(sel) >= 2:
            r, _ = sel[:2] # type: ignore
            values = data[r]
            if messagebox.askyesno("Usuń wydawcę", f"Czy na pewno chcesz usunąć wydawcę: {values[1]}?"): # type: ignore
                with sqlite3.connect(DB_FILE) as conn:
                    c = conn.cursor()
                    c.execute("DELETE FROM wydawcy WHERE id=?", (values[0],))
                    conn.commit()
                fill_wydawcy_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
    menu.add_command(label="Edytuj", command=context_edit)
    menu.add_command(label="Usuń", command=context_delete)
    def on_right_click(event): # type: ignore
        r = sheet.identify_row(event)
        c = sheet.identify_column(event)
        if r is not None and c is not None:
            sheet.set_currently_selected(r, c) # type: ignore
            menu.tk_popup(event.x_root, event.y_root) # type: ignore
    sheet.bind("<Button-3>", on_right_click) # type: ignore
    
    # Tryb ciemny
    if dark_mode:
        sheet.set_options(theme="dark") # type: ignore


def open_edit_dialog(parent, values, refresh_callback=None): # type: ignore
    dialog = ctk.CTkToplevel(parent) # type: ignore
    dialog.title("Edytuj wydawcę")
    dialog.transient(parent) # type: ignore
    dialog.grab_set()
    dialog.resizable(True, False)

    parent.update_idletasks() # type: ignore
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 180 # type: ignore
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 130 # type: ignore
    dialog.geometry(f"400x280+{x}+{y}")

    # Główna ramka
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # ID wydawcy (tylko do odczytu)
    ctk.CTkLabel(main_frame, text=f"ID wydawcy: {values[0]}", font=("Segoe UI", 12)).grid(
        row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

    # Nazwa wydawcy
    ctk.CTkLabel(main_frame, text="Nazwa wydawcy *").grid(row=1, column=0, pady=5, sticky="w")
    nazwa_entry = ctk.CTkEntry(main_frame, width=220)
    nazwa_entry.grid(row=1, column=1, pady=5, padx=(10, 0), sticky="ew")
    nazwa_entry.insert(0, values[1] if values[1] is not None else "") # type: ignore

    # Strona internetowa
    ctk.CTkLabel(main_frame, text="Strona internetowa").grid(row=2, column=0, pady=5, sticky="w")
    strona_entry = ctk.CTkEntry(main_frame, width=220)
    strona_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky="ew")
    strona_entry.insert(0, values[2] if values[2] is not None else "") # type: ignore

    # Kraj wydawcy
    ctk.CTkLabel(main_frame, text="Kraj wydawcy").grid(row=3, column=0, pady=5, sticky="w")
    kraj_entry = ctk.CTkEntry(main_frame, width=220)
    kraj_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky="ew")
    kraj_entry.insert(0, values[3] if values[3] is not None else "") # type: ignore

    main_frame.columnconfigure(1, weight=1)

    def on_save():
        nazwa = nazwa_entry.get().strip()
        strona = strona_entry.get().strip()
        kraj = kraj_entry.get().strip()
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa wydawcy jest wymagana.", parent=dialog) # type: ignore
            return
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("UPDATE wydawcy SET nazwa=?, strona=?, kraj=? WHERE id=?", (nazwa, strona if strona else None, kraj if kraj else None, values[0])) # type: ignore
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent)) # type: ignore
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    # Ramka na przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))

    btn_save = ctk.CTkButton(btn_frame, text="Zapisz", command=on_save, width=100,
                             fg_color="#2E7D32", hover_color="#1B5E20")
    btn_save.pack(side=tk.LEFT, padx=10)
    btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100,
                               fg_color="#666666", hover_color="#555555")
    btn_cancel.pack(side=tk.LEFT, padx=10)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)


def usun_wydawce_dialog(parent, refresh_callback=None): # type: ignore
    init_db()
    records = get_all_publishers()
    if not records:
        messagebox.showinfo("Brak danych", "Brak wydawców do usunięcia.", parent=parent) # type: ignore
        return
    dialog = ctk.CTkToplevel(parent) # type: ignore
    dialog.title("Usuń wydawcę")
    dialog.transient(parent) # type: ignore
    dialog.grab_set()
    dialog.resizable(False, False)

    parent.update_idletasks() # type: ignore
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 180 # type: ignore
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 130 # type: ignore
    dialog.geometry(f"400x300+{x}+{y}")

    # Główna ramka
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    ctk.CTkLabel(main_frame, text="Wybierz wydawcę do usunięcia:", font=("Segoe UI", 12)).pack(pady=(0, 10))
    
    # Ramka dla listbox ze scrollem
    list_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    listbox = tk.Listbox(list_frame, width=44, height=8, font=("Segoe UI", 10))
    for rec in records:
        listbox.insert(tk.END, f"{rec[0]}. {rec[1]}")
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)
    listbox.selection_set(0)

    def on_delete():
        sel = listbox.curselection() # type: ignore
        if not sel:
            return
        idx = sel[0] # type: ignore
        rec = records[idx]
        if messagebox.askyesno("Potwierdź usunięcie", f"Czy na pewno chcesz usunąć wydawcę: {rec[1]}?", parent=dialog): # type: ignore
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM wydawcy WHERE id=?", (rec[0],))
                conn.commit()
            if refresh_callback:
                refresh_callback()
            dialog.destroy()

    def on_cancel():
        dialog.destroy()

    # Ramka na przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.pack(pady=(10, 0))
    
    btn_del = ctk.CTkButton(btn_frame, text="Usuń", command=on_delete, width=100,
                            fg_color="#C62828", hover_color="#B71C1C")
    btn_del.pack(side=tk.LEFT, padx=10)
    btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100,
                               fg_color="#666666", hover_color="#555555")
    btn_cancel.pack(side=tk.LEFT, padx=10)
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)


def usun_zaznaczonego_wydawce(tab: tk.Frame, refresh_callback=None): # type: ignore
    # Usuwa zaznaczonego wydawcę z tksheet
    sheet = None
    for widget in tab.winfo_children():
        if isinstance(widget, tksheet.Sheet):
            sheet = widget
            break
    if sheet is None:
        messagebox.showerror("Błąd", "Nie znaleziono tabeli wydawców.", parent=tab) # type: ignore
        return
    sel = sheet.get_currently_selected()
    if not sel or len(sel) < 2:
        messagebox.showinfo("Brak wyboru", "Zaznacz wydawcę do usunięcia w tabeli.", parent=tab) # type: ignore
        return
    r, _ = sel[:2] # type: ignore
    values = sheet.get_row_data(r) # type: ignore
    if messagebox.askyesno("Usuń wydawcę", f"Czy na pewno chcesz usunąć wydawcę: {values[1]}?", parent=tab): # type: ignore
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM wydawcy WHERE id=?", (values[0],))
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(tab))

# Alias dla kompatybilności z main.py
usun_zaznaczony_wydawce = usun_zaznaczonego_wydawce # type: ignore
