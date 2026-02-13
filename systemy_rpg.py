# Moduł: Systemy RPG
# Tutaj będą funkcje i klasy związane z obsługą systemów RPG
# pyright: reportUnknownMemberType=false

import tkinter as tk
import tksheet  # type: ignore
from tkinter import ttk, messagebox
import sqlite3
from typing import Optional, Callable, Sequence, Any, Dict, List, Union
import customtkinter as ctk  # type: ignore
from database_manager import get_db_path

DB_FILE = get_db_path("systemy_rpg.db")

# Przechowuj aktywne filtry na poziomie modułu
active_filters_systemy: Dict[str, Any] = {}

def init_db() -> None:
    """Inicjalizuje bazę danych systemów RPG"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS systemy_rpg (
                id INTEGER PRIMARY KEY,
                nazwa TEXT NOT NULL,
                typ TEXT NOT NULL,
                system_glowny_id INTEGER,
                typ_suplementu TEXT,
                wydawca_id INTEGER,
                fizyczny INTEGER DEFAULT 0,
                pdf INTEGER DEFAULT 0,
                jezyk TEXT,
                status_gra TEXT DEFAULT 'Nie grane',
                status_kolekcja TEXT DEFAULT 'W kolekcji',
                cena_zakupu REAL,
                waluta_zakupu TEXT,
                cena_sprzedazy REAL,
                waluta_sprzedazy TEXT,
                FOREIGN KEY (system_glowny_id) REFERENCES systemy_rpg(id),
                FOREIGN KEY (wydawca_id) REFERENCES wydawcy(id)
            )
        """)
        
        # Migracja - dodaj nowe kolumny do istniejących tabel
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN status_gra TEXT DEFAULT 'Nie grane'")
        except sqlite3.OperationalError:
            # Kolumna już istnieje
            pass
        
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN status_kolekcja TEXT DEFAULT 'W kolekcji'")
        except sqlite3.OperationalError:
            # Kolumna już istnieje
            pass
        
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN cena_zakupu REAL")
        except sqlite3.OperationalError:
            # Kolumna już istnieje
            pass
        
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN waluta_zakupu TEXT")
        except sqlite3.OperationalError:
            # Kolumna już istnieje
            pass
        
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN cena_sprzedazy REAL")
        except sqlite3.OperationalError:
            # Kolumna już istnieje
            pass
        
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN waluta_sprzedazy TEXT")
        except sqlite3.OperationalError:
            # Kolumna już istnieje
            pass
        
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN vtt TEXT")
        except sqlite3.OperationalError:
            # Kolumna już istnieje
            pass
        
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
            widget.configure(bg=dark_bg, fg=dark_fg) # type: ignore
            if widget_class in ('Checkbutton', 'Radiobutton'):
                widget.configure(selectcolor=dark_entry_bg, activebackground=dark_bg, activeforeground=dark_fg) # type: ignore
        elif widget_class in ('Entry', 'Text'):
            widget.configure(bg=dark_entry_bg, fg=dark_entry_fg,  # type: ignore
                           insertbackground=dark_entry_fg, selectbackground="#0078d4")  # type: ignore
        elif widget_class == 'Frame':
            widget.configure(bg=dark_bg) # type: ignore
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
    """Zwraca pierwszy wolny ID w bazie systemów RPG"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM systemy_rpg ORDER BY id ASC")
        used_ids = [row[0] for row in c.fetchall()]
    i = 1
    while i in used_ids:
        i += 1
    return i

def get_all_systems() -> list[tuple[Any, ...]]:
    """Pobiera wszystkie systemy RPG z bazy"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Najpierw sprawdź czy tabela istnieje i jest pusta
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='systemy_rpg'")
        if not c.fetchone():
            return []
        
        c.execute("SELECT COUNT(*) FROM systemy_rpg")
        if c.fetchone()[0] == 0:
            return []
        
        # Pobierz systemy z LEFT JOIN do wydawców z innej bazy
        c.execute("""
            SELECT s.id, s.nazwa, s.typ, s.system_glowny_id, s.typ_suplementu, 
                   s.wydawca_id, s.fizyczny, s.pdf, s.vtt, s.jezyk, s.status_gra, s.status_kolekcja,
                   s.cena_zakupu, s.waluta_zakupu, s.cena_sprzedazy, s.waluta_sprzedazy
            FROM systemy_rpg s
            ORDER BY s.id ASC
        """)
        systems = c.fetchall()
    
    # Dla każdego systemu pobierz nazwę wydawcy z oddzielnej bazy
    result = []
    for system in systems:
        try:
            with sqlite3.connect("wydawcy.db") as wydawcy_conn:
                w_cursor = wydawcy_conn.cursor()
                if system[5]:  # wydawca_id
                    w_cursor.execute("SELECT nazwa FROM wydawcy WHERE id = ?", (system[5],))
                    wydawca_result = w_cursor.fetchone()
                    wydawca_nazwa = wydawca_result[0] if wydawca_result else ""
                else:
                    wydawca_nazwa = ""
        except sqlite3.Error:
            wydawca_nazwa = ""
        
        # Sformuj status jako string: "Grane/Nie grane, W kolekcji/Na sprzedaż"
        status_gra = system[10] if system[10] else "Nie grane"
        status_kolekcja = system[11] if system[11] else "W kolekcji"
        # Jeśli status to "Na sprzedaż", pokaż jako "W kolekcji, Na sprzedaż"
        status_kolekcja_display = "W kolekcji, Na sprzedaż" if status_kolekcja == "Na sprzedaż" else status_kolekcja
        status_combined = f"{status_gra}, {status_kolekcja_display}"
        
        # Formatuj cenę w zależności od statusu kolekcji
        cena_str = ""
        if status_kolekcja in ["W kolekcji", "Na sprzedaż"] and system[12]:  # cena_zakupu
            waluta = system[13] if system[13] else "PLN"
            cena_str = f"{system[12]:.2f} {waluta}"
        elif status_kolekcja == "Sprzedane" and system[14]:  # cena_sprzedazy
            waluta = system[15] if system[15] else "PLN"
            cena_str = f"{system[14]:.2f} {waluta}"
        
        # Formatuj VTT - nazwy VTT oddzielone przecinkami
        vtt_str = system[8] if system[8] else ""
        
        # Dodaj nazwę wydawcy, status, VTT i cenę do systemu
        # Format: id, nazwa, typ, system_glowny_id, typ_suplementu, wydawca_nazwa, fizyczny, pdf, vtt, jezyk, status, cena
        result.append((  # type: ignore
            system[0],  # id
            system[1],  # nazwa  
            system[2],  # typ
            system[3],  # system_glowny_id
            system[4],  # typ_suplementu
            wydawca_nazwa,  # wydawca (nazwa)
            system[6],  # fizyczny
            system[7],  # pdf
            vtt_str,  # vtt
            system[9],  # jezyk
            status_combined,  # status
            cena_str  # cena (zakupu lub sprzedaży w zależności od statusu)
        )) # type: ignore
    
    return result # type: ignore

def get_main_systems() -> list[tuple[int, str]]:
    """Pobiera systemy główne (Podręcznik Główny) do wyboru jako rodzic dla suplementów"""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, nazwa FROM systemy_rpg WHERE typ = 'Podręcznik Główny' ORDER BY nazwa")
        return c.fetchall()

def get_all_publishers() -> list[tuple[int, str]]:
    """Pobiera wszystkich wydawców z bazy wydawców"""
    try:
        with sqlite3.connect("wydawcy.db") as conn:
            c = conn.cursor()
            c.execute("SELECT id, nazwa FROM wydawcy ORDER BY nazwa")
            return c.fetchall()
    except sqlite3.Error:
        return []

def dodaj_system_rpg(parent: tk.Tk, refresh_callback: Optional[Callable[..., None]] = None) -> None:  # type: ignore
    """Otwiera okno dodawania nowego systemu RPG"""
    
    init_db()
    reserved_id = get_first_free_id()
    publishers = get_all_publishers()

    dialog = ctk.CTkToplevel(parent)
    dialog.title("Dodaj system RPG do bazy")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(True, False)
    
    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 350
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 260
    dialog.geometry(f"700x520+{x}+{y}")
    
    # Główna ramka z padding
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.columnconfigure(1, weight=1)

    # ID systemu
    ctk.CTkLabel(main_frame, text=f"ID systemu: {reserved_id}", font=("Segoe UI", 12)).grid(
        row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

    # Nazwa systemu (obowiązkowe)
    ctk.CTkLabel(main_frame, text="Nazwa systemu *").grid(row=1, column=0, pady=8, padx=(0, 10), sticky="w")
    nazwa_entry = ctk.CTkEntry(main_frame, placeholder_text="Wprowadź nazwę systemu")
    nazwa_entry.grid(row=1, column=1, pady=8, sticky="ew")
    nazwa_entry.focus_set()

    # Typ (Podręcznik Główny / Suplement)
    ctk.CTkLabel(main_frame, text="Typ *").grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")
    typ_var = tk.StringVar(value="Podręcznik Główny")
    typ_combo = ctk.CTkComboBox(main_frame, variable=typ_var, 
                                values=["Podręcznik Główny", "Suplement"], state="readonly")
    typ_combo.grid(row=2, column=1, pady=8, sticky="ew")

    # System główny (dla suplementów) - początkowo ukryte, opcjonalne
    system_glowny_label = ctk.CTkLabel(main_frame, text="System główny (opcjonalnie)")
    system_glowny_label.grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")
    system_glowny_var = tk.StringVar()
    system_glowny_combo = ctk.CTkComboBox(main_frame, variable=system_glowny_var, state="readonly")
    system_glowny_combo.grid(row=3, column=1, pady=8, sticky="ew")

    # Typ suplementu - początkowo ukryte, obowiązkowe dla suplementów (wielokrotny wybór)
    typ_suplementu_label = ctk.CTkLabel(main_frame, text="Typ suplementu *")
    typ_suplementu_label.grid(row=4, column=0, pady=8, padx=(0, 10), sticky="nw")
    typ_suplementu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")
    
    # Słownik do przechowywania zmiennych checkboxów
    typ_suplementu_vars = {}
    typ_suplementu_checkboxes = {}
    typy_suplementow = ["Scenariusz/kampania", "Rozwinięcie zasad", "Moduł", "Lorebook/Sourcebook", "Bestiariusz"]
    
    for i, typ in enumerate(typy_suplementow):
        var = tk.BooleanVar()
        typ_suplementu_vars[typ] = var
        checkbox = ctk.CTkCheckBox(typ_suplementu_frame, text=typ, variable=var, width=280)
        checkbox.grid(row=i, column=0, sticky="w", pady=2)
        typ_suplementu_checkboxes[typ] = checkbox

    # Wydawca
    ctk.CTkLabel(main_frame, text="Wydawca").grid(row=5, column=0, pady=8, padx=(0,10), sticky="w")
    wydawca_var = tk.StringVar()
    wydawca_combo = ctk.CTkComboBox(main_frame, variable=wydawca_var, state="readonly")
    if publishers:
        wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
        wydawca_combo.configure(values=wydawca_values)
    wydawca_combo.grid(row=5, column=1, pady=8, sticky="ew")

    # Posiadanie
    ctk.CTkLabel(main_frame, text="Posiadanie").grid(row=6, column=0, pady=8, padx=(0,10), sticky="nw")
    posiadanie_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    posiadanie_frame.grid(row=6, column=1, pady=8, sticky="w", columnspan=2)
    posiadanie_frame.columnconfigure(1, weight=1)
    
    fizyczny_var = tk.BooleanVar()
    pdf_var = tk.BooleanVar()
    vtt_var = tk.BooleanVar()
    
    # Checkboxy w lewej kolumnie
    fizyczny_check = ctk.CTkCheckBox(posiadanie_frame, text="Fizyczny", variable=fizyczny_var)
    fizyczny_check.grid(row=0, column=0, sticky="w", pady=2)
    pdf_check = ctk.CTkCheckBox(posiadanie_frame, text="PDF", variable=pdf_var)
    pdf_check.grid(row=1, column=0, sticky="w", pady=2)
    vtt_check = ctk.CTkCheckBox(posiadanie_frame, text="VTT", variable=vtt_var)
    vtt_check.grid(row=2, column=0, sticky="w", pady=2)
    
    # Lista platform VTT (alfabetycznie)
    vtt_platforms = [
        "AboveVTT",
        "Alchemy VTT",
        "D&D Beyond",
        "Demiplane",
        "Fantasy Grounds",
        "Foundry VTT",
        "Roll20",
        "Tabletop Simulator",
        "Telespire"
    ]
    
    # Frame dla wyboru platform VTT w prawej kolumnie (początkowo ukryty)
    vtt_selection_frame = ctk.CTkFrame(posiadanie_frame, fg_color="transparent")
    vtt_selection_frame.grid(row=0, column=1, rowspan=3, sticky="nsw", padx=(20, 0))
    
    # Label dla platform VTT
    vtt_label = ctk.CTkLabel(vtt_selection_frame, text="Platformy VTT:", font=("Segoe UI", 10))
    vtt_label.pack(anchor="w", pady=(0, 5))
    
    # Scrollable frame dla checkboxów VTT
    vtt_scroll_frame = ctk.CTkScrollableFrame(vtt_selection_frame, width=200, height=120)
    vtt_scroll_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Słownik do przechowywania zmiennych checkboxów VTT
    vtt_platform_vars = {}
    for platform in vtt_platforms:
        var = tk.BooleanVar()
        vtt_platform_vars[platform] = var
        checkbox = ctk.CTkCheckBox(vtt_scroll_frame, text=platform, variable=var)
        checkbox.pack(anchor="w", pady=1)
    
    # Początkowo ukryj frame wyboru VTT
    vtt_selection_frame.grid_remove()
    
    def update_dialog_size() -> None:
        """Aktualizuje rozmiar okna na podstawie stanu VTT i typu"""
        dialog.update_idletasks()
        parent.update_idletasks()
        
        is_vtt = vtt_var.get()
        is_suplement = typ_var.get() == "Suplement"
        
        if is_vtt and is_suplement:
            # VTT + Suplement - największe okno
            width, height = 850, 850
        elif is_vtt:
            # VTT bez suplementu
            width, height = 850, 680
        elif is_suplement:
            # Suplement bez VTT
            width, height = 700, 720
        else:
            # Podstawowe okno
            width, height = 700, 520
        
        new_x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        new_y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{new_x}+{new_y}")
    
    def on_vtt_change(*args: Any) -> None:
        """Obsługuje zmianę checkboxa VTT - pokazuje/ukrywa listę platform"""
        if vtt_var.get():
            vtt_selection_frame.grid()
        else:
            vtt_selection_frame.grid_remove()
        update_dialog_size()
    
    vtt_var.trace_add('write', on_vtt_change)

    # Język
    ctk.CTkLabel(main_frame, text="Język").grid(row=7, column=0, pady=8, padx=(0,10), sticky="w")
    jezyk_var = tk.StringVar(value="PL")
    jezyk_combo = ctk.CTkComboBox(main_frame, variable=jezyk_var, 
                              values=["PL", "ENG", "DE", "FR", "ES", "IT"], 
                              state="readonly", width=100)
    jezyk_combo.grid(row=7, column=1, pady=8, sticky="w")

    # Status gry
    ctk.CTkLabel(main_frame, text="Status gry").grid(row=8, column=0, pady=8, padx=(0,10), sticky="w")
    status_gra_var = tk.StringVar(value="Nie grane")
    status_gra_combo = ctk.CTkComboBox(main_frame, variable=status_gra_var,
                                   values=["Grane", "Nie grane"],
                                   state="readonly", width=150)
    status_gra_combo.grid(row=8, column=1, pady=8, sticky="w")

    # Status kolekcji
    ctk.CTkLabel(main_frame, text="Status kolekcji").grid(row=9, column=0, pady=8, padx=(0,10), sticky="w")
    status_kolekcja_var = tk.StringVar(value="W kolekcji")
    status_kolekcja_combo = ctk.CTkComboBox(main_frame, variable=status_kolekcja_var,
                                        values=["W kolekcji", "Na sprzedaż", "Sprzedane", "Nieposiadane", "Do kupienia"],
                                        state="readonly", width=150)
    status_kolekcja_combo.grid(row=9, column=1, pady=8, sticky="w")

    # Cena zakupu (dla statusu "W kolekcji")
    cena_zakupu_label = ctk.CTkLabel(main_frame, text="Cena zakupu")
    cena_zakupu_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")
    
    cena_zakupu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_zakupu_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")
    
    cena_zakupu_entry = ctk.CTkEntry(cena_zakupu_frame, width=100)
    cena_zakupu_entry.pack(side=tk.LEFT, padx=(0, 5))
    
    waluta_zakupu_var = tk.StringVar(value="PLN")
    waluta_zakupu_combo = ctk.CTkComboBox(cena_zakupu_frame, variable=waluta_zakupu_var,
                                       values=["PLN", "USD", "EUR", "GBP"],
                                       state="readonly", width=70)
    waluta_zakupu_combo.pack(side=tk.LEFT)
    
    # Cena sprzedaży (dla statusu "Sprzedane")
    cena_sprzedazy_label = ctk.CTkLabel(main_frame, text="Cena sprzedaży")
    cena_sprzedazy_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")
    
    cena_sprzedazy_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_sprzedazy_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")
    
    cena_sprzedazy_entry = ctk.CTkEntry(cena_sprzedazy_frame, width=100)
    cena_sprzedazy_entry.pack(side=tk.LEFT, padx=(0, 5))
    
    waluta_sprzedazy_var = tk.StringVar(value="PLN")
    waluta_sprzedazy_combo = ctk.CTkComboBox(cena_sprzedazy_frame, variable=waluta_sprzedazy_var,
                                          values=["PLN", "USD", "EUR", "GBP"],
                                          state="readonly", width=70)
    waluta_sprzedazy_combo.pack(side=tk.LEFT)
    
    # Początkowo ukryj oba pola ceny
    cena_zakupu_label.grid_remove()
    cena_zakupu_frame.grid_remove()
    cena_sprzedazy_label.grid_remove()
    cena_sprzedazy_frame.grid_remove()
    
    def on_status_kolekcja_change(*args: Any) -> None:
        """Obsługuje zmianę statusu kolekcji - pokazuje odpowiednie pole ceny"""
        status = status_kolekcja_var.get()
        
        if status == "W kolekcji":
            # Pokaż cenę zakupu, ukryj cenę sprzedaży
            cena_zakupu_label.grid()
            cena_zakupu_frame.grid()
            cena_sprzedazy_label.grid_remove()
            cena_sprzedazy_frame.grid_remove()
        elif status == "Sprzedane":
            # Pokaż cenę sprzedaży, ukryj cenę zakupu
            cena_zakupu_label.grid_remove()
            cena_zakupu_frame.grid_remove()
            cena_sprzedazy_label.grid()
            cena_sprzedazy_frame.grid()
        else:
            # Ukryj oba pola dla innych statusów
            cena_zakupu_label.grid_remove()
            cena_zakupu_frame.grid_remove()
            cena_sprzedazy_label.grid_remove()
            cena_sprzedazy_frame.grid_remove()
    
    status_kolekcja_var.trace_add('write', on_status_kolekcja_change)
    on_status_kolekcja_change()  # Ustaw początkowy stan

    def on_typ_change(*args: Any) -> None:
        """Obsługuje zmianę typu (Podręcznik Główny/Suplement)"""
        if typ_var.get() == "Suplement":
            # Pokaż pola dla suplementu z oryginalnymi parametrami grid
            system_glowny_label.grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")
            system_glowny_combo.grid(row=3, column=1, pady=8, sticky="ew")
            typ_suplementu_label.grid(row=4, column=0, pady=8, padx=(0, 10), sticky="nw")
            typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")
            # Załaduj systemy główne
            main_systems = get_main_systems()
            if main_systems:
                system_values = [f"{sys[0]} - {sys[1]}" for sys in main_systems]
                system_glowny_combo.configure(values=system_values)
        else:
            # Ukryj pola dla suplementu
            system_glowny_label.grid_remove()
            system_glowny_combo.grid_remove()
            typ_suplementu_label.grid_remove()
            typ_suplementu_frame.grid_remove()
        update_dialog_size()

    typ_var.trace_add('write', on_typ_change)
    on_typ_change()  # Ustaw początkowy stan

    def on_ok() -> None:
        """Zapisuje nowy system do bazy"""
        nazwa = nazwa_entry.get().strip()
        typ = typ_var.get()
        jezyk = jezyk_var.get()
        
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa systemu jest wymagana.", parent=dialog) # type: ignore
            return
        
        system_glowny_id = None
        typ_suplementu = None
        
        if typ == "Suplement":
            # Zbierz wybrane typy suplementu
            wybrane_typy = [typ for typ, var in typ_suplementu_vars.items() if var.get()] # type: ignore
            
            if not wybrane_typy:
                messagebox.showerror("Błąd", "Dla suplementu musisz wybrać przynajmniej jeden typ suplementu.", parent=dialog) # type: ignore
                return
            
            # Połącz wybrane typy separatorem
            typ_suplementu = " | ".join(wybrane_typy) # type: ignore
            
            # System główny jest opcjonalny - może być pusty dla osieroconych suplementów
            if system_glowny_var.get():
                system_glowny_id = int(system_glowny_var.get().split(' - ')[0])
        
        wydawca_id = None
        if wydawca_var.get():
            wydawca_id = int(wydawca_var.get().split(' - ')[0])
        
        # Pobierz ceny w zależności od statusu
        cena_zakupu = None
        waluta_zakupu = None
        cena_sprzedazy = None
        waluta_sprzedazy = None
        
        if status_kolekcja_var.get() in ["W kolekcji", "Na sprzedaż"]:
            cena_str = cena_zakupu_entry.get().strip().replace(',', '.')
            if cena_str:
                try:
                    cena_zakupu = float(cena_str)
                    waluta_zakupu = waluta_zakupu_var.get()
                except ValueError:
                    messagebox.showerror("Błąd", "Cena zakupu musi być liczbą.", parent=dialog) # type: ignore
                    return
        elif status_kolekcja_var.get() == "Sprzedane":
            cena_str = cena_sprzedazy_entry.get().strip().replace(',', '.')
            if cena_str:
                try:
                    cena_sprzedazy = float(cena_str)
                    waluta_sprzedazy = waluta_sprzedazy_var.get()
                except ValueError:
                    messagebox.showerror("Błąd", "Cena sprzedaży musi być liczbą.", parent=dialog) # type: ignore
                    return
        
        # Zbierz wybrane platformy VTT
        vtt_str = None
        if vtt_var.get():
            wybrane_vtt = [platform for platform, var in vtt_platform_vars.items() if var.get()]  # type: ignore
            if wybrane_vtt:
                vtt_str = ", ".join(wybrane_vtt)  # type: ignore
        
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO systemy_rpg (id, nazwa, typ, system_glowny_id, typ_suplementu, 
                                       wydawca_id, fizyczny, pdf, vtt, jezyk, status_gra, status_kolekcja,
                                       cena_zakupu, waluta_zakupu, cena_sprzedazy, waluta_sprzedazy) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (reserved_id, nazwa, typ, system_glowny_id, typ_suplementu, wydawca_id,
                  int(fizyczny_var.get()), int(pdf_var.get()), vtt_str, jezyk if jezyk else None,
                  status_gra_var.get(), status_kolekcja_var.get(),
                  cena_zakupu, waluta_zakupu, cena_sprzedazy, waluta_sprzedazy))
            conn.commit()
        
        if refresh_callback:
            refresh_callback(dark_mode=getattr(parent, 'dark_mode', False))
        dialog.destroy()

    def on_cancel() -> None:
        """Anuluje dodawanie"""
        dialog.destroy()

    # Przyciski
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.grid(row=10, column=0, columnspan=2, pady=15, sticky="ew")
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    
    btn_ok = ctk.CTkButton(button_frame, text="Dodaj", command=on_ok,
                           fg_color="#2E7D32", hover_color="#1B5E20")
    btn_ok.grid(row=0, column=0, padx=5, sticky="e")
    
    btn_cancel = ctk.CTkButton(button_frame, text="Anuluj", command=on_cancel,
                               fg_color="#666666", hover_color="#555555")
    btn_cancel.grid(row=0, column=1, padx=5, sticky="w")
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)

def fill_systemy_rpg_tab(tab: tk.Frame, dark_mode: bool = False) -> None:  # type: ignore
    """Wypełnia zakładkę systemów RPG danymi z bazy w hierarchicznej strukturze"""
    for widget in tab.winfo_children():
        widget.destroy()
    
    init_db()
    records = get_all_systems()
    headers = ["", "ID", "Nazwa systemu", "Typ", "System główny", "Typ suplementu", "Wydawca", "Fizyczny", "PDF", "VTT", "Język", "Status", "Cena"]
    
    # Przygotuj hierarchiczne dane do wyświetlenia
    from collections import OrderedDict
    main_systems: OrderedDict[Any, Any] = OrderedDict()  # type: ignore # Słownik podręczników głównych zachowujący kolejność
    supplements: Dict[Any, List[Any]] = {}   # Słownik suplementów grupowanych po system_glowny_id
    orphaned_supplements: List[Any] = []  # Suplementy bez przypisanego systemu głównego
    
    # Grupuj systemy
    for rec in records:
        if rec[2] == "Podręcznik Główny":
            main_systems[rec[0]] = rec
        elif rec[2] == "Suplement":
            parent_id = rec[3]  # system_glowny_id
            if parent_id and parent_id in main_systems.keys():
                if parent_id not in supplements:
                    supplements[parent_id] = []
                supplements[parent_id].append(rec) # type: ignore
            else:
                orphaned_supplements.append(rec) # type: ignore
    
    # Stan rozwinięcia dla każdego podręcznika głównego
    expanded_state: Dict[Any, bool] = {}
    
    def build_hierarchical_data() -> List[List[Any]]:  # type: ignore
        """Buduje hierarchiczne dane na podstawie stanu rozwinięcia"""
        nonlocal main_systems, supplements, orphaned_supplements
        data: List[List[Any]] = []
        
        # Pobierz listę kluczy w aktualnej kolejności
        main_keys = list(main_systems.keys())
        
        # Dodaj podręczniki główne i ich suplementy w aktualnej kolejności
        for main_id in main_keys:
            rec = main_systems[main_id]
            
            # Sprawdź czy ten podręcznik główny ma suplementy
            has_supplements = main_id in supplements
            supplements_count = len(supplements.get(main_id, []))
            expand_symbol = "[-]" if expanded_state.get(main_id, False) else "[+]" if has_supplements else "   "
            
            # Dodaj podręcznik główny
            system_name = rec[1] or ""
            if has_supplements:
                system_name += f" ({supplements_count} supl.)"
            
            row: List[Any] = [
                expand_symbol,
                str(rec[0]),  # ID
                system_name,  # Nazwa z liczbą suplementów
                rec[2] or "",  # Typ
                "",  # System główny (puste dla podręczników głównych)
                "",  # Typ suplementu (puste dla podręczników głównych)
                rec[5] or "",  # Wydawca (nazwa)
                "Tak" if rec[6] else "Nie",  # Fizyczny
                "Tak" if rec[7] else "Nie",  # PDF
                rec[8] or "",  # VTT
                rec[9] or "",  # Język
                rec[10] or "",  # Status (sformowany w get_all_systems)
                rec[11] or ""  # Cena (zakupu lub sprzedaży)
            ]
            data.append(row)
            
            # Jeśli rozwinięty, dodaj suplementy
            if expanded_state.get(main_id, False) and main_id in supplements:
                for supp_rec in sorted(supplements[main_id], key=lambda x: x[1] or ""):  # Sortuj po nazwie
                    # Znajdź nazwę systemu głównego
                    main_system_name = main_systems[main_id][1] if main_id in main_systems else ""
                    
                    supp_row: List[Any] = [
                        "   →",  # Symbol suplementu
                        str(supp_rec[0]),  # ID
                        "  " + (supp_rec[1] or ""),  # Nazwa z wcięciem
                        supp_rec[2] or "",  # Typ
                        main_system_name,  # System główny
                        supp_rec[4] or "",  # Typ suplementu
                        supp_rec[5] or "",  # Wydawca (nazwa)
                        "Tak" if supp_rec[6] else "Nie",  # Fizyczny
                        "Tak" if supp_rec[7] else "Nie",  # PDF
                        supp_rec[8] or "",  # VTT
                        supp_rec[9] or "",  # Język
                        supp_rec[10] or "",  # Status
                        supp_rec[11] or ""  # Cena
                    ]
                    data.append(supp_row)
        
        # Dodaj osierocone suplementy na końcu
        for rec in orphaned_supplements:
            # Znajdź nazwę systemu głównego jeśli istnieje
            main_system_name = ""
            if rec[3]:  # system_glowny_id
                with sqlite3.connect(DB_FILE) as conn:
                    c = conn.cursor()
                    c.execute("SELECT nazwa FROM systemy_rpg WHERE id = ?", (rec[3],))
                    result = c.fetchone()
                    if result:
                        main_system_name = result[0]
            
            row: List[Any] = [
                "   !",  # Symbol problemowego suplementu
                str(rec[0]),  # ID
                rec[1] or "",  # Nazwa
                rec[2] or "",  # Typ
                main_system_name,  # System główny
                rec[4] or "",  # Typ suplementu
                rec[5] or "",  # Wydawca (nazwa)
                "Tak" if rec[6] else "Nie",  # Fizyczny
                "Tak" if rec[7] else "Nie",  # PDF
                rec[8] or "",  # VTT
                rec[9] or "",  # Język
                rec[10] or "",  # Status
                rec[11] or ""  # Cena
            ]
            data.append(row)
        
        return data
    
    data = build_hierarchical_data()

    sheet = tksheet.Sheet(tab,
        data=data,  # type: ignore
        headers=headers,
        show_x_scrollbar=True,
        show_y_scrollbar=True,
        width=1200,
        height=600)
    
    # Automatyczne dopasowanie szerokości kolumn do zawartości lub nagłówka
    for col in range(len(headers)):
        if col == 0:  # Kolumna rozwijania
            sheet.column_width(column=col, width=40)
        else:
            max_content = max([len(str(row[col])) for row in data] + [len(headers[col])])  # type: ignore
            width_px = max(80, min(400, int(max_content * 9 + 24)))
            sheet.column_width(column=col, width=width_px)
    
    # Wycentrowanie kolumn ID, Fizyczny, PDF
    sheet.align_columns(columns=[1, 7, 8], align="center")
    
    def apply_row_colors():
        """Aplikuje kolory wierszy w zależności od typu"""
        for r, row in enumerate(data):
            typ = row[3] if len(row) > 3 else ""  # Kolumna "Typ"
            expand_symbol = row[0] if len(row) > 0 else ""
            status = row[11] if len(row) > 11 else ""  # Kolumna "Status"
            
            # Sprawdź czy status kolekcji zawiera "Na sprzedaż"
            na_sprzedaz = "Na sprzedaż" in status
            # Sprawdź nowe statusy
            nieposiadane = "Nieposiadane" in status
            do_kupienia = "Do kupienia" in status
            
            if na_sprzedaz:
                # Czerwone tło dla elementów na sprzedaż (nadpisuje inne kolory)
                if dark_mode:
                    bg_color = "#660000"  # Ciemnoczerwony
                    fg_color = "#ffcccc"  # Jasnoczerowny tekst
                else:
                    bg_color = "#ff6666"  # Czerwony
                    fg_color = "#ffffff"  # Biały tekst
                sheet.highlight_rows(rows=r, bg=bg_color, fg=fg_color)
            elif nieposiadane:
                # Szare tło dla nieposiadanych
                if dark_mode:
                    bg_color = "#3a3a3a"  # Ciemnoszary
                    fg_color = "#b0b0b0"  # Jasnoszary tekst
                else:
                    bg_color = "#d3d3d3"  # Jasnoszary
                    fg_color = "#505050"  # Ciemnoszary tekst
                sheet.highlight_rows(rows=r, bg=bg_color, fg=fg_color)
            elif do_kupienia:
                # Fioletowe/różowe tło dla elementów do kupienia
                if dark_mode:
                    bg_color = "#4a1a4a"  # Ciemny fiolet
                    fg_color = "#e6b3e6"  # Jasny różowy tekst
                else:
                    bg_color = "#e6b3ff"  # Jasny fiolet
                    fg_color = "#4a004a"  # Ciemny fiolet tekst
                sheet.highlight_rows(rows=r, bg=bg_color, fg=fg_color)
            elif typ == "Podręcznik Główny":
                # Sprawdź czy ten podręcznik główny ma suplementy
                try:
                    int(row[1])  # ID z drugiej kolumny (sprawdza czy to poprawne ID)
                    has_supplements = expand_symbol in ["[+]", "[-]"]  # Ma symbol rozwijania
                except (ValueError, IndexError):
                    has_supplements = False
                
                if has_supplements:
                    # Bardzo wyraziste kolory dla podręczników głównych z suplementami
                    if dark_mode:
                        bg_color = "#5d4e00"  # Intensywny ciemny złoty/brązowy
                        fg_color = "#ffd700"  # Jaskrawy złoty tekst
                    else:
                        bg_color = "#ffa500"  # Jaskrawy pomarańczowy
                        fg_color = "#4d2d00"  # Bardzo ciemny brązowy tekst
                else:
                    # Subtelniejsze kolory dla podręczników głównych bez suplementów
                    if dark_mode:
                        bg_color = "#1a3d1a"  # Zwykły ciemnozielony
                        fg_color = "#90ee90"  # Jasnozielony tekst
                    else:
                        bg_color = "#d4edda"  # Zwykły jasnozielony
                        fg_color = "#155724"  # Ciemnozielony tekst
                
                sheet.highlight_rows(rows=r, bg=bg_color, fg=fg_color)
                    
            elif typ == "Suplement":
                # Subtelniejsze kolory dla suplementów
                if dark_mode:
                    bg_color = "#1a2a3d"  # Ciemnoniebieski
                    fg_color = "#87ceeb"  # Jasnoniebieski tekst
                else:
                    bg_color = "#f0f8ff"  # Bardzo jasnoniebieski
                    fg_color = "#2c5282"  # Niebieski tekst
                sheet.highlight_rows(rows=r, bg=bg_color, fg=fg_color)
                
            # Wyróżnij osierocone suplementy
            elif expand_symbol == "   !":
                if dark_mode:
                    bg_color = "#3d1a1a"  # Ciemnoczerwony
                    fg_color = "#ffb3b3"  # Jasnoczerowny tekst
                else:
                    bg_color = "#ffe6e6"  # Jasnoczerowny
                    fg_color = "#8b0000"  # Ciemnoczerwony tekst
                sheet.highlight_rows(rows=r, bg=bg_color, fg=fg_color)
    
    apply_row_colors()
    
    def on_cell_select(event: Any) -> None:  # type: ignore
        """Obsługuje wybór komórki - rozwijanie/zwijanie"""
        nonlocal data, expanded_state
        try:
            selected = sheet.get_currently_selected()
            if selected and len(selected) >= 2:
                r, c = selected[:2]  # type: ignore
                if c == 0 and r < len(data):  # Kliknięto w kolumnę rozwijania
                    expand_symbol = data[r][0]
                    if expand_symbol in ["[+]", "[-]"]:
                        # Znajdź ID podręcznika głównego
                        main_system_id = None
                        try:
                            main_system_id = int(data[r][1])  # ID z drugiej kolumny
                        except (ValueError, IndexError):
                            return
                        
                        # Przełącz stan rozwinięcia
                        expanded_state[main_system_id] = not expanded_state.get(main_system_id, False)
                        
                        # Przebuduj dane i odśwież tabelę
                        data = build_hierarchical_data()
                        sheet.set_sheet_data(data)  # type: ignore
                        
                        # Ponownie zastosuj kolory
                        apply_row_colors()
                        
                        # Ponownie ustaw szerokości kolumn
                        for col in range(len(headers)):
                            if col == 0:
                                sheet.column_width(column=col, width=40)
                            else:
                                max_content = max([len(str(row[col])) for row in data] + [len(headers[col])])  # type: ignore
                                width_px = max(80, min(400, int(max_content * 9 + 24)))
                                sheet.column_width(column=col, width=width_px)
                        
                        sheet.refresh()
        except Exception:
            pass  # Zignoruj błędy podczas obsługi kliknięć
    
    # Bind wyboru komórek
    sheet.extra_bindings("cell_select", on_cell_select)  # type: ignore
    
    # Włącz obsługę zaznaczania i interakcji
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
    ))  # type: ignore
    
    # Panel sortowania nad tabelą - dostosowany do hierarchii
    sort_frame = tk.Frame(tab)
    sort_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
    sort_label = tk.Label(sort_frame, text="Sortuj podręczniki główne po:")
    sort_label.pack(side=tk.LEFT, padx=(0, 6))
    # Opcje sortowania dostosowane do hierarchii
    sort_options = ["ID", "Nazwa systemu", "Wydawca", "Język", "Status", "Posiadanie", "Cena"]
    sort_var = tk.StringVar(value=sort_options[0])
    sort_menu = ttk.Combobox(sort_frame, textvariable=sort_var, values=sort_options, state="readonly", width=15)
    sort_menu.pack(side=tk.LEFT)
    
    def do_hierarchical_sort(reverse: bool = False) -> None:
        """Sortuje podręczniki główne zachowując hierarchię"""
        nonlocal data, main_systems, supplements, orphaned_supplements
        sort_by = sort_var.get()
        
        # Sortuj główne systemy na podstawie oryginalnych rekordów z bazy
        if sort_by == "ID":  # ID - sortowanie numeryczne
            sorted_main_ids = sorted(main_systems.keys(), 
                                   key=lambda x: int(main_systems[x][0]) if main_systems[x][0] else 0, 
                                   reverse=reverse)
        elif sort_by == "Nazwa systemu":  # Nazwa
            sorted_main_ids = sorted(main_systems.keys(), 
                                   key=lambda x: (main_systems[x][1] or '').lower(), 
                                   reverse=reverse)
        elif sort_by == "Wydawca":  # Wydawca (indeks 5 w oryginalnych rekordach)
            sorted_main_ids = sorted(main_systems.keys(), 
                                   key=lambda x: (main_systems[x][5] or '').lower(), 
                                   reverse=reverse)
        elif sort_by == "Język":  # Język (indeks 8 w oryginalnych rekordach)
            sorted_main_ids = sorted(main_systems.keys(), 
                                   key=lambda x: (main_systems[x][8] or '').lower(), 
                                   reverse=reverse)
        elif sort_by == "Status":  # Status (indeks 9 w oryginalnych rekordach - status połączony)
            sorted_main_ids = sorted(main_systems.keys(), 
                                   key=lambda x: (main_systems[x][9] or '').lower(), 
                                   reverse=reverse)
        elif sort_by == "Posiadanie":  # Posiadanie (fizyczny + pdf, indeks 6 i 7)
            def posiadanie_key(x: Any) -> str:
                rec = main_systems[x]
                if rec[6] and rec[7]:  # Fizyczny i PDF
                    return "1"
                elif rec[6]:  # Tylko fizyczny
                    return "2"
                elif rec[7]:  # Tylko PDF
                    return "3"
                else:  # Żadne
                    return "4"
            sorted_main_ids = sorted(main_systems.keys(), key=posiadanie_key, reverse=reverse)
        elif sort_by == "Cena":  # Cena (indeks 10 - sformatowana cena jako string)
            def cena_key(x: Any) -> float:
                rec = main_systems[x]
                cena_str = rec[10] if rec[10] else ""  # Sformatowana cena np. "123.45 PLN"
                if cena_str:
                    # Wyciągnij liczbę z początku stringa
                    try:
                        return float(cena_str.split()[0])
                    except (ValueError, IndexError):
                        return 0.0
                return 0.0
            sorted_main_ids = sorted(main_systems.keys(), key=cena_key, reverse=reverse)
        else:  # Domyślnie sortuj po ID
            sorted_main_ids = sorted(main_systems.keys(), 
                                   key=lambda x: int(main_systems[x][0]) if main_systems[x][0] else 0, 
                                   reverse=reverse)
        
        # Przebuduj main_systems w odpowiedniej kolejności (używając OrderedDict)
        from collections import OrderedDict
        temp_main_systems: OrderedDict[Any, Any] = OrderedDict()  # type: ignore
        for main_id in sorted_main_ids:
            temp_main_systems[main_id] = main_systems[main_id]
        
        # Zastąp main_systems nowym słownikiem w odpowiedniej kolejności  
        main_systems.clear()
        for k, v in temp_main_systems.items():
            main_systems[k] = v
        
        # Przebuduj hierarchiczne dane
        data = build_hierarchical_data()
        sheet.set_sheet_data(data)  # type: ignore
        apply_row_colors()
        
        # Ponownie ustaw szerokości kolumn
        for col in range(len(headers)):
            if col == 0:
                sheet.column_width(column=col, width=40)
            else:
                max_content = max([len(str(row[col])) for row in data] + [len(headers[col])])  # type: ignore
                width_px = max(80, min(400, int(max_content * 9 + 24)))
                sheet.column_width(column=col, width=width_px)
        
        sheet.refresh()
    
    sort_asc_btn = ttk.Button(sort_frame, text="Rosnąco", command=lambda: do_hierarchical_sort(False))
    sort_asc_btn.pack(side=tk.LEFT, padx=4)
    sort_desc_btn = ttk.Button(sort_frame, text="Malejąco", command=lambda: do_hierarchical_sort(True))
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
        dialog.title("Filtruj systemy RPG")
        dialog.transient(tab.winfo_toplevel())
        dialog.grab_set()
        
        if dark_mode:
            apply_dark_theme_to_dialog(dialog)
        
        # Centrowanie okna
        tab.winfo_toplevel().update_idletasks()
        x = tab.winfo_toplevel().winfo_rootx() + (tab.winfo_toplevel().winfo_width() // 2) - 200
        y = tab.winfo_toplevel().winfo_rooty() + (tab.winfo_toplevel().winfo_height() // 2) - 225
        dialog.geometry(f"400x450+{x}+{y}")
        
        main_frame = tk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Filtr Typu
        tk.Label(main_frame, text="Typ:").grid(row=0, column=0, sticky="w", pady=5)
        typ_var = tk.StringVar(value=active_filters_systemy.get('typ', 'Wszystkie'))
        typ_values = ['Wszystkie', 'Podręcznik Główny', 'Suplement']
        typ_combo = ttk.Combobox(main_frame, textvariable=typ_var, values=typ_values, state="readonly", width=25)
        typ_combo.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Filtr Wydawcy
        tk.Label(main_frame, text="Wydawca:").grid(row=1, column=0, sticky="w", pady=5)
        wydawca_var = tk.StringVar(value=active_filters_systemy.get('wydawca', 'Wszystkie'))
        
        # Pobierz unikalnych wydawców z danych
        wydawcy: set[str] = set()
        for row in data:
            if row[6]:  # Wydawca
                wydawcy.add(row[6])
        wydawca_values = ['Wszystkie'] + sorted(list(wydawcy))
        wydawca_combo = ttk.Combobox(main_frame, textvariable=wydawca_var, values=wydawca_values, state="readonly", width=25)
        wydawca_combo.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Filtr Posiadania
        tk.Label(main_frame, text="Posiadanie:").grid(row=2, column=0, sticky="w", pady=5)
        posiadanie_var = tk.StringVar(value=active_filters_systemy.get('posiadanie', 'Wszystkie'))
        posiadanie_values = ['Wszystkie', 'Fizyczny', 'PDF', 'Fizyczny i PDF', 'Żadne']
        posiadanie_combo = ttk.Combobox(main_frame, textvariable=posiadanie_var, values=posiadanie_values, state="readonly", width=25)
        posiadanie_combo.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Filtr Języka
        tk.Label(main_frame, text="Język:").grid(row=3, column=0, sticky="w", pady=5)
        jezyk_var = tk.StringVar(value=active_filters_systemy.get('jezyk', 'Wszystkie'))
        
        # Pobierz unikalne języki z danych
        jezyki: set[str] = set()
        for row in data:
            if row[9]:  # Język
                jezyki.add(row[9])
        jezyk_values = ['Wszystkie'] + sorted(list(jezyki))
        jezyk_combo = ttk.Combobox(main_frame, textvariable=jezyk_var, values=jezyk_values, state="readonly", width=25)
        jezyk_combo.grid(row=3, column=1, sticky="ew", pady=5)
        
        # Filtr Statusu
        tk.Label(main_frame, text="Status:").grid(row=4, column=0, sticky="w", pady=5)
        status_var = tk.StringVar(value=active_filters_systemy.get('status', 'Wszystkie'))
        
        # Lista możliwych statusów (zgodna z wartościami w combobox)
        status_values = ['Wszystkie', 'Grane', 'Nie grane', 
                        'W kolekcji', 'Na sprzedaż', 'Sprzedane', 
                        'Nieposiadane', 'Do kupienia']
        status_combo = ttk.Combobox(main_frame, textvariable=status_var, values=status_values, state="readonly", width=25)
        status_combo.grid(row=4, column=1, sticky="ew", pady=5)
        
        # Filtr Waluty
        tk.Label(main_frame, text="Waluta:").grid(row=5, column=0, sticky="w", pady=5)
        waluta_var = tk.StringVar(value=active_filters_systemy.get('waluta', 'Wszystkie'))
        
        # Lista możliwych walut
        waluta_values = ['Wszystkie', 'PLN', 'USD', 'EUR', 'GBP']
        waluta_combo = ttk.Combobox(main_frame, textvariable=waluta_var, values=waluta_values, state="readonly", width=25)
        waluta_combo.grid(row=5, column=1, sticky="ew", pady=5)
        
        main_frame.columnconfigure(1, weight=1)
        
        # Przyciski
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        def apply_filters() -> None:
            """Aplikuje filtry"""
            nonlocal data, main_systems, supplements, orphaned_supplements
            active_filters_systemy['typ'] = typ_var.get()
            active_filters_systemy['wydawca'] = wydawca_var.get()
            active_filters_systemy['posiadanie'] = posiadanie_var.get()
            active_filters_systemy['jezyk'] = jezyk_var.get()
            active_filters_systemy['status'] = status_var.get()
            active_filters_systemy['waluta'] = waluta_var.get()
            
            # Pobierz oryginalne rekordy z bazy dla filtrowania
            all_records = get_all_systems()
            
            # Filtruj rekordy na poziomie bazy danych
            filtered_main_systems: OrderedDict[Any, Any] = OrderedDict()  # type: ignore
            filtered_supplements: Dict[Any, List[Any]] = {}
            filtered_orphaned_supplements: List[Any] = []
            
            for rec in all_records:
                # Filtr Typu
                if active_filters_systemy['typ'] != 'Wszystkie':
                    if rec[2] != active_filters_systemy['typ']:
                        continue
                
                # Filtr Wydawcy
                if active_filters_systemy['wydawca'] != 'Wszystkie':
                    if rec[5] != active_filters_systemy['wydawca']:
                        continue
                
                # Filtr Posiadania (rec[6] to fizyczny, rec[7] to pdf)
                if active_filters_systemy['posiadanie'] == 'Fizyczny':
                    if not rec[6]:
                        continue
                elif active_filters_systemy['posiadanie'] == 'PDF':
                    if not rec[7]:
                        continue
                elif active_filters_systemy['posiadanie'] == 'Fizyczny i PDF':
                    if not (rec[6] and rec[7]):
                        continue
                elif active_filters_systemy['posiadanie'] == 'Żadne':
                    if rec[6] or rec[7]:
                        continue
                
                # Filtr Języka
                if active_filters_systemy['jezyk'] != 'Wszystkie':
                    if rec[8] != active_filters_systemy['jezyk']:
                        continue
                
                # Filtr Statusu (rec[9] to sformowany status)
                if active_filters_systemy['status'] != 'Wszystkie':
                    if active_filters_systemy['status'] not in (rec[9] or ''):
                        continue
                
                # Filtr Waluty (rec[10] to sformatowana cena np. "123.45 PLN")
                if active_filters_systemy['waluta'] != 'Wszystkie':
                    cena_str = rec[10] if rec[10] else ""
                    if active_filters_systemy['waluta'] not in cena_str:
                        continue
                
                # Dodaj do odpowiednich grup
                if rec[2] == "Podręcznik Główny":
                    filtered_main_systems[rec[0]] = rec
                elif rec[2] == "Suplement":
                    if rec[3]:  # system_glowny_id
                        if rec[3] not in filtered_supplements:
                            filtered_supplements[rec[3]] = []
                        filtered_supplements[rec[3]].append(rec)
                    else:
                        filtered_orphaned_supplements.append(rec)
            
            # Zaktualizuj globalne zmienne
            main_systems = filtered_main_systems
            supplements = filtered_supplements
            orphaned_supplements = filtered_orphaned_supplements
            
            # Przebuduj hierarchiczne dane
            data = build_hierarchical_data()
            sheet.set_sheet_data(data)  # type: ignore
            apply_row_colors()
            
            # Ponownie ustaw szerokości kolumn
            for col in range(len(headers)):
                if col == 0:
                    sheet.column_width(column=col, width=40)
                else:
                    max_content = max([len(str(row[col])) for row in data] + [len(headers[col])]) if data else len(headers[col])
                    width_px = max(80, min(400, int(max_content * 9 + 24)))
                    sheet.column_width(column=col, width=width_px)
            
            sheet.refresh()
            
            # Aktualizuj tekst przycisku
            count = 0
            if active_filters_systemy.get('typ') != 'Wszystkie':
                count += 1
            if active_filters_systemy.get('wydawca') != 'Wszystkie':
                count += 1
            if active_filters_systemy.get('posiadanie') != 'Wszystkie':
                count += 1
            if active_filters_systemy.get('jezyk') != 'Wszystkie':
                count += 1
            if active_filters_systemy.get('status') != 'Wszystkie':
                count += 1
            if active_filters_systemy.get('waluta') != 'Wszystkie':
                count += 1
            
            if count > 0:
                filter_btn.configure(text=f"Filtruj ({count})")
            else:
                filter_btn.configure(text="Filtruj")
            
            dialog.destroy()
        
        def reset_filters() -> None:
            """Resetuje wszystkie filtry"""
            nonlocal data, main_systems, supplements, orphaned_supplements
            active_filters_systemy.clear()
            
            # Przeładuj wszystkie dane z bazy
            records = get_all_systems()
            
            # Zresetuj grupy
            main_systems.clear()
            supplements.clear()
            orphaned_supplements.clear()
            
            for rec in records:
                if rec[2] == "Podręcznik Główny":
                    main_systems[rec[0]] = rec
                elif rec[2] == "Suplement":
                    if rec[3]:
                        if rec[3] not in supplements:
                            supplements[rec[3]] = []
                        supplements[rec[3]].append(rec)
                    else:
                        orphaned_supplements.append(rec)
            
            # Przebuduj hierarchiczne dane
            data = build_hierarchical_data()
            sheet.set_sheet_data(data)  # type: ignore
            apply_row_colors()
            
            # Ponownie ustaw szerokości kolumn
            for col in range(len(headers)):
                if col == 0:
                    sheet.column_width(column=col, width=40)
                else:
                    max_content = max([len(str(row[col])) for row in data] + [len(headers[col])])
                    width_px = max(80, min(400, int(max_content * 9 + 24)))
                    sheet.column_width(column=col, width=width_px)
            
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
    
    # Menu kontekstowe - dostosowane do hierarchii
    menu = tk.Menu(tab, tearoff=0)
    
    def context_edit() -> None:
        """Edytuje zaznaczony system"""
        try:
            selected = sheet.get_currently_selected()
            if selected and len(selected) >= 2:
                r: int = selected[0]  # type: ignore
                
                if r >= len(data):
                    return
                
                row = data[r]
                if len(row) < 2:
                    return
                
                system_id = row[1]  # ID z drugiej kolumny
                
                if system_id:
                    # Znajdź pełne dane systemu z oryginalnych rekordów
                    system_record = None
                    for rec in records:
                        if str(rec[0]) == str(system_id):
                            system_record = rec
                            break
                    
                    if system_record:
                        # Konwertuj na format wymagany przez open_edit_system_dialog
                        values: List[Any] = [  # type: ignore
                            str(system_record[0]),  # ID
                            system_record[1] or "",  # Nazwa
                            system_record[2] or "",  # Typ
                            "",  # System główny (zostanie wypełniony w dialog)
                            system_record[4] or "",  # Typ suplementu
                            system_record[5] or "",  # Wydawca (nazwa)
                            "Tak" if system_record[7] else "Nie",  # Fizyczny
                            "Tak" if system_record[8] else "Nie",  # PDF
                            system_record[9] or ""  # Język
                        ]
                        
                        # Jeśli to suplement, znajdź nazwę systemu głównego
                        if system_record[3]:  # system_glowny_id
                            with sqlite3.connect(DB_FILE) as conn:
                                c = conn.cursor()
                                c.execute("SELECT nazwa FROM systemy_rpg WHERE id = ?", (system_record[3],))
                                result = c.fetchone()
                                if result:
                                    values[3] = result[0]
                        
                        open_edit_system_dialog(tab, values, refresh_callback=lambda **kwargs: fill_systemy_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab)))  # type: ignore
        except Exception as e:
            print(f"Błąd podczas edycji: {e}")
    
    def context_delete() -> None:
        """Usuwa zaznaczony system"""
        try:
            selected = sheet.get_currently_selected()
            if selected and len(selected) >= 2:
                r: int = selected[0]  # type: ignore
                
                if r >= len(data):
                    return
                
                row = data[r]
                if len(row) < 4:
                    return
                
                system_id = row[1]  # ID z drugiej kolumny
                system_name = row[2]  # Nazwa z trzeciej kolumny
                system_type = row[3]  # Typ z czwartej kolumny
                
                # Sprawdź czy to podręcznik główny czy suplement
                is_main_system = (system_type == "Podręcznik Główny")
                
                # Dla podręczników głównych usuń licznik suplementów z nazwy
                if is_main_system and " (" in system_name and " supl.)" in system_name:
                    system_name = system_name.split(" (")[0]
                
                if system_id and system_name:
                    # Sprawdź czy podręcznik główny ma suplementy
                    warning_msg = f"Czy na pewno chcesz usunąć system: {system_name}?"
                    if is_main_system and int(system_id) in supplements:
                        supp_count = len(supplements[int(system_id)])
                        warning_msg += f"\n\nUWAGA: Ten podręcznik główny ma {supp_count} suplementów, które również zostaną usunięte!"
                    
                    if messagebox.askyesno("Usuń system RPG", warning_msg, parent=tab):  # type: ignore
                        with sqlite3.connect(DB_FILE) as conn:
                            c = conn.cursor()
                            # Usuń suplementy jeśli to podręcznik główny
                            if is_main_system:
                                c.execute("DELETE FROM systemy_rpg WHERE system_glowny_id = ?", (system_id,))
                            # Usuń główny system
                            c.execute("DELETE FROM systemy_rpg WHERE id = ?", (system_id,))
                            conn.commit()
                        fill_systemy_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
        except Exception as e:
            print(f"Błąd podczas usuwania: {e}")
    
    def context_add_supplement() -> None:
        """Dodaje suplement do wybranego podręcznika głównego"""
        try:
            selected = sheet.get_currently_selected()
            if selected and len(selected) >= 2:
                r: int = selected[0]  # type: ignore
                
                if r >= len(data):
                    return
                
                row = data[r]
                if len(row) < 4:
                    return
                
                system_id = row[1]  # ID z drugiej kolumny
                system_name = row[2]  # Nazwa z trzeciej kolumny
                system_type = row[3]  # Typ z czwartej kolumny
                
                # Sprawdź czy to podręcznik główny
                if system_type != "Podręcznik Główny":
                    return
                
                # Usuń licznik suplementów z nazwy jeśli istnieje
                if " (" in system_name and " supl.)" in system_name:
                    clean_system_name = system_name.split(" (")[0]
                else:
                    clean_system_name = system_name
                
                if system_id:
                    # Otwórz okno dodawania suplementu z predefiniowanym systemem głównym
                    dodaj_suplement_do_systemu(tab.winfo_toplevel(), int(system_id), clean_system_name, 
                                              refresh_callback=lambda **kwargs: fill_systemy_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab)))  # type: ignore
        except Exception as e:
            print(f"Błąd podczas dodawania suplementu: {e}")
    
    # Utwórz menu kontekstowe
    menu = tk.Menu(tab, tearoff=0)
    
    def show_context_menu(event: tk.Event) -> None:  # type: ignore
        """Wyświetla menu kontekstowe dostosowane do typu systemu"""
        r = sheet.identify_row(event)
        c = sheet.identify_column(event)
        if r is not None and c is not None:
            sheet.set_currently_selected(r, c)  # type: ignore
            
            # Sprawdź typ zaznaczonego systemu
            if r < len(data) and len(data[r]) > 3:
                system_type = data[r][3]  # Typ z czwartej kolumny
                
                # Wyczyść menu
                menu.delete(0, 'end')
                
                # Dodaj podstawowe opcje
                menu.add_command(label="Edytuj", command=context_edit)
                
                # Dodaj opcję dodawania suplementu tylko dla podręczników głównych
                if system_type == "Podręcznik Główny":
                    menu.add_command(label="Dodaj suplement do podręcznika głównego", command=context_add_supplement)
                
                menu.add_separator()
                menu.add_command(label="Usuń", command=context_delete)
                
                # Pokaż menu
                menu.tk_popup(event.x_root, event.y_root)  # type: ignore
    
    sheet.bind("<Button-3>", show_context_menu)  # type: ignore
    
    # Tryb ciemny
    if dark_mode:
        sheet.set_options(theme="dark")  # type: ignore
    
    # Automatycznie aplikuj filtry jeśli są aktywne
    if active_filters_systemy:
        # Pobierz oryginalne rekordy z bazy dla filtrowania
        all_records = get_all_systems()
        
        # Filtruj rekordy na poziomie bazy danych
        filtered_main_systems: OrderedDict[Any, Any] = OrderedDict()  # type: ignore
        filtered_supplements: Dict[Any, List[Any]] = {}
        filtered_orphaned_supplements: List[Any] = []
        
        for rec in all_records:
            # Filtr Typu
            if active_filters_systemy.get('typ', 'Wszystkie') != 'Wszystkie':
                if rec[2] != active_filters_systemy['typ']:
                    continue
            
            # Filtr Wydawcy
            if active_filters_systemy.get('wydawca', 'Wszystkie') != 'Wszystkie':
                if rec[5] != active_filters_systemy['wydawca']:
                    continue
            
            # Filtr Posiadania (rec[6] to fizyczny, rec[7] to pdf)
            posiadanie_filter = active_filters_systemy.get('posiadanie', 'Wszystkie')
            if posiadanie_filter == 'Fizyczny':
                if not rec[6]:
                    continue
            elif posiadanie_filter == 'PDF':
                if not rec[7]:
                    continue
            elif posiadanie_filter == 'Fizyczny i PDF':
                if not (rec[6] and rec[7]):
                    continue
            elif posiadanie_filter == 'Żadne':
                if rec[6] or rec[7]:
                    continue
            
            # Filtr Języka
            if active_filters_systemy.get('jezyk', 'Wszystkie') != 'Wszystkie':
                if rec[9] != active_filters_systemy['jezyk']:
                    continue
            
            # Filtr Statusu (rec[10] to sformowany status)
            if active_filters_systemy.get('status', 'Wszystkie') != 'Wszystkie':
                if active_filters_systemy['status'] not in (rec[10] or ''):
                    continue
            
            # Filtr Waluty (rec[11] to sformatowana cena np. "123.45 PLN")
            if active_filters_systemy.get('waluta', 'Wszystkie') != 'Wszystkie':
                cena_str = rec[11] if rec[11] else ""
                if active_filters_systemy['waluta'] not in cena_str:
                    continue
            
            # Dodaj do odpowiednich grup
            if rec[2] == "Podręcznik Główny":
                filtered_main_systems[rec[0]] = rec
            elif rec[2] == "Suplement":
                if rec[3]:  # system_glowny_id
                    if rec[3] not in filtered_supplements:
                        filtered_supplements[rec[3]] = []
                    filtered_supplements[rec[3]].append(rec)
                else:
                    filtered_orphaned_supplements.append(rec)
        
        # Zaktualizuj globalne zmienne
        main_systems = filtered_main_systems
        supplements = filtered_supplements
        orphaned_supplements = filtered_orphaned_supplements
        
        # Przebuduj hierarchiczne dane
        data = build_hierarchical_data()
        sheet.set_sheet_data(data)  # type: ignore
        apply_row_colors()
        
        # Ponownie ustaw szerokości kolumn
        for col in range(len(headers)):
            if col == 0:
                sheet.column_width(column=col, width=40)
            else:
                max_content = max([len(str(row[col])) for row in data] + [len(headers[col])]) if data else len(headers[col])
                width_px = max(80, min(400, int(max_content * 9 + 24)))
                sheet.column_width(column=col, width=width_px)
        
        sheet.refresh()
        
        # Aktualizuj tekst przycisku
        count = 0
        if active_filters_systemy.get('typ') != 'Wszystkie':
            count += 1
        if active_filters_systemy.get('wydawca') != 'Wszystkie':
            count += 1
        if active_filters_systemy.get('posiadanie') != 'Wszystkie':
            count += 1
        if active_filters_systemy.get('jezyk') != 'Wszystkie':
            count += 1
        if active_filters_systemy.get('status') != 'Wszystkie':
            count += 1
        if active_filters_systemy.get('waluta') != 'Wszystkie':
            count += 1
        if count > 0:
            filter_btn.configure(text=f"Filtruj ({count})")

def usun_zaznaczony_system(tab: tk.Frame, refresh_callback: Optional[Callable[..., None]] = None) -> None:
    """Usuwa zaznaczony system RPG z tabeli i bazy danych"""
    sheet = None
    for widget in tab.winfo_children():
        if isinstance(widget, tksheet.Sheet):
            sheet = widget
            break
    if sheet is None:
        messagebox.showerror("Błąd", "Nie znaleziono tabeli systemów RPG.", parent=tab)  # type: ignore
        return
    sel = sheet.get_currently_selected()
    if not sel or len(sel) < 2:
        messagebox.showinfo("Brak wyboru", "Zaznacz system do usunięcia w tabeli.", parent=tab)  # type: ignore
        return
    r, _ = sel[:2]  # type: ignore
    values = sheet.get_row_data(r)  # type: ignore
    if len(values) < 2:
        return
    
    if messagebox.askyesno("Usuń system RPG", f"Czy na pewno chcesz usunąć system: {values[1]}?", parent=tab):  # type: ignore
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM systemy_rpg WHERE id=?", (values[0],))
            conn.commit()
        
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(tab))

def open_edit_system_dialog(parent: tk.Widget, values: Sequence[Any], refresh_callback: Optional[Callable[..., None]] = None) -> None:
    """Otwiera okno edycji systemu RPG"""
    
    # Najpierw pobierz dane z bazy, aby sprawdzić czy VTT jest zaznaczone
    system_id = values[0]
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, nazwa, typ, system_glowny_id, typ_suplementu, 
                   wydawca_id, fizyczny, pdf, vtt, jezyk, status_gra, status_kolekcja,
                   cena_zakupu, waluta_zakupu, cena_sprzedazy, waluta_sprzedazy
            FROM systemy_rpg WHERE id = ?
        """, (system_id,))
        system_data = c.fetchone()
    
    if not system_data:
        messagebox.showerror("Błąd", "Nie znaleziono systemu w bazie danych.", parent=parent)
        return
    
    # Sprawdź czy VTT jest zaznaczone
    has_vtt = bool(system_data[8])  # vtt
    is_suplement = system_data[2] == "Suplement"  # typ
    
    dialog = ctk.CTkToplevel(parent)  # type: ignore
    dialog.title("Edytuj system RPG")
    dialog.transient(parent)  # type: ignore
    dialog.grab_set()
    dialog.resizable(True, False)
    
    # Ustaw geometrię na podstawie tego czy VTT jest zaznaczone i czy to suplement
    parent.update_idletasks()
    
    if has_vtt and is_suplement:
        # VTT + Suplement - największe okno
        width, height = 850, 850
    elif has_vtt:
        # VTT bez suplementu
        width, height = 850, 680
    elif is_suplement:
        # Suplement bez VTT
        width, height = 700, 720
    else:
        # Podstawowe okno
        width, height = 700, 560
    
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    # Główny frame z paddingiem
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.columnconfigure(1, weight=1)

    publishers = get_all_publishers()

    # ID systemu (tylko do odczytu)
    ctk.CTkLabel(main_frame, text=f"ID systemu: {system_data[0]}").grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")

    # Nazwa systemu (obowiązkowe)
    ctk.CTkLabel(main_frame, text="Nazwa systemu *").grid(row=1, column=0, pady=8, padx=(0,10), sticky="w")
    nazwa_entry = ctk.CTkEntry(main_frame, placeholder_text="Wprowadź nazwę systemu")
    nazwa_entry.grid(row=1, column=1, pady=8, sticky="ew")
    nazwa_entry.insert(0, system_data[1] or "")
    nazwa_entry.focus_set()

    # Typ (Podręcznik Główny / Suplement)
    ctk.CTkLabel(main_frame, text="Typ *").grid(row=2, column=0, pady=8, padx=(0,10), sticky="w")
    typ_var = tk.StringVar(value=system_data[2] or "Podręcznik Główny")
    typ_combo = ctk.CTkComboBox(main_frame, variable=typ_var, 
                            values=["Podręcznik Główny", "Suplement"], state="readonly")
    typ_combo.grid(row=2, column=1, pady=8, sticky="ew")

    # System główny (dla suplementów) - opcjonalne
    system_glowny_label = ctk.CTkLabel(main_frame, text="System główny (opcjonalnie)")
    system_glowny_label.grid(row=3, column=0, pady=8, padx=(0,10), sticky="w")
    system_glowny_var = tk.StringVar()
    system_glowny_combo = ctk.CTkComboBox(main_frame, variable=system_glowny_var, state="readonly")
    system_glowny_combo.grid(row=3, column=1, pady=8, sticky="ew")

    # Typ suplementu - obowiązkowe dla suplementów (wielokrotny wybór)
    typ_suplementu_label = ctk.CTkLabel(main_frame, text="Typ suplementu *")
    typ_suplementu_label.grid(row=4, column=0, pady=8, padx=(0,10), sticky="nw")
    typ_suplementu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")
    
    # Słownik do przechowywania zmiennych checkboxów
    typ_suplementu_vars = {}
    typ_suplementu_checkboxes = {}
    typy_suplementow = ["Scenariusz/kampania", "Rozwinięcie zasad", "Moduł", "Lorebook/Sourcebook", "Bestiariusz"]
    
    # Parsuj istniejące typy suplementu z bazy (oddzielone " | ")
    istniejace_typy = []
    if system_data[4]:  # typ_suplementu
        istniejace_typy = [typ.strip() for typ in system_data[4].split(" | ")]
    
    for i, typ in enumerate(typy_suplementow):
        var = tk.BooleanVar(value=(typ in istniejace_typy))
        typ_suplementu_vars[typ] = var
        checkbox = ctk.CTkCheckBox(typ_suplementu_frame, text=typ, variable=var, width=280)
        checkbox.grid(row=i, column=0, sticky="w", pady=2)
        typ_suplementu_checkboxes[typ] = checkbox

    # Wydawca
    ctk.CTkLabel(main_frame, text="Wydawca").grid(row=5, column=0, pady=8, padx=(0,10), sticky="w")
    wydawca_var = tk.StringVar()
    wydawca_combo = ctk.CTkComboBox(main_frame, variable=wydawca_var, state="readonly")
    if publishers:
        wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
        wydawca_combo.configure(values=wydawca_values)
        # Ustaw obecnie wybranego wydawcę
        if system_data[5]:  # wydawca_id
            for pub in publishers:
                if pub[0] == system_data[5]:
                    wydawca_var.set(f"{pub[0]} - {pub[1]}")
                    break
    wydawca_combo.grid(row=5, column=1, pady=8, sticky="ew")

    # Posiadanie
    ctk.CTkLabel(main_frame, text="Posiadanie").grid(row=6, column=0, pady=8, padx=(0,10), sticky="nw")
    posiadanie_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    posiadanie_frame.grid(row=6, column=1, pady=8, sticky="w", columnspan=2)
    posiadanie_frame.columnconfigure(1, weight=1)
    
    fizyczny_var = tk.BooleanVar(value=bool(system_data[6]))
    pdf_var = tk.BooleanVar(value=bool(system_data[7]))
    
    # Parsuj istniejące VTT z bazy (oddzielone przecinkami)
    istniejace_vtt = []
    if system_data[8]:  # vtt
        istniejace_vtt = [vtt.strip() for vtt in system_data[8].split(",")]
    vtt_var = tk.BooleanVar(value=len(istniejace_vtt) > 0)
    
    # Checkboxy w lewej kolumnie
    fizyczny_check = ctk.CTkCheckBox(posiadanie_frame, text="Fizyczny", variable=fizyczny_var)
    fizyczny_check.grid(row=0, column=0, sticky="w", pady=2)
    pdf_check = ctk.CTkCheckBox(posiadanie_frame, text="PDF", variable=pdf_var)
    pdf_check.grid(row=1, column=0, sticky="w", pady=2)
    vtt_check = ctk.CTkCheckBox(posiadanie_frame, text="VTT", variable=vtt_var)
    vtt_check.grid(row=2, column=0, sticky="w", pady=2)
    
    # Lista platform VTT (alfabetycznie)
    vtt_platforms = [
        "AboveVTT",
        "Alchemy VTT",
        "D&D Beyond",
        "Demiplane",
        "Fantasy Grounds",
        "Foundry VTT",
        "Roll20",
        "Tabletop Simulator",
        "Telespire"
    ]
    
    # Frame dla wyboru platform VTT w prawej kolumnie (początkowo ukryty)
    vtt_selection_frame = ctk.CTkFrame(posiadanie_frame, fg_color="transparent")
    vtt_selection_frame.grid(row=0, column=1, rowspan=3, sticky="nsw", padx=(20, 0))
    
    # Label dla platform VTT
    vtt_label = ctk.CTkLabel(vtt_selection_frame, text="Platformy VTT:", font=("Segoe UI", 10))
    vtt_label.pack(anchor="w", pady=(0, 5))
    
    # Scrollable frame dla checkboxów VTT
    vtt_scroll_frame = ctk.CTkScrollableFrame(vtt_selection_frame, width=200, height=120)
    vtt_scroll_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Słownik do przechowywania zmiennych checkboxów VTT
    vtt_platform_vars = {}
    for platform in vtt_platforms:
        var = tk.BooleanVar(value=(platform in istniejace_vtt))
        vtt_platform_vars[platform] = var
        checkbox = ctk.CTkCheckBox(vtt_scroll_frame, text=platform, variable=var)
        checkbox.pack(anchor="w", pady=1)
    
    # Aktualizuj dialog przed sprawdzeniem stanu VTT
    dialog.update_idletasks()
    
    # Początkowo ukryj frame wyboru VTT jeśli VTT nie jest zaznaczone
    # lub pokaż go jeśli jest zaznaczone
    if vtt_var.get():
        # VTT jest zaznaczone - upewnij się że frame jest widoczny
        vtt_selection_frame.grid()
    else:
        # VTT nie jest zaznaczone - ukryj frame
        vtt_selection_frame.grid_remove()
    
    def update_dialog_size() -> None:
        """Aktualizuje rozmiar okna na podstawie stanu VTT i typu"""
        dialog.update_idletasks()
        parent.update_idletasks()
        
        is_vtt = vtt_var.get()
        is_suplement = typ_var.get() == "Suplement"
        
        if is_vtt and is_suplement:
            # VTT + Suplement - największe okno
            width, height = 850, 850
        elif is_vtt:
            # VTT bez suplementu
            width, height = 850, 680
        elif is_suplement:
            # Suplement bez VTT
            width, height = 700, 720
        else:
            # Podstawowe okno
            width, height = 700, 560
        
        new_x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        new_y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{new_x}+{new_y}")
    
    def on_vtt_change(*args: Any) -> None:
        """Obsługuje zmianę checkboxa VTT - pokazuje/ukrywa listę platform"""
        if vtt_var.get():
            vtt_selection_frame.grid()
        else:
            vtt_selection_frame.grid_remove()
        update_dialog_size()
    
    vtt_var.trace_add('write', on_vtt_change)

    # Język
    ctk.CTkLabel(main_frame, text="Język").grid(row=7, column=0, pady=8, padx=(0,10), sticky="w")
    jezyk_var = tk.StringVar(value=system_data[9] or "PL")
    jezyk_combo = ctk.CTkComboBox(main_frame, variable=jezyk_var, 
                              values=["PL", "ENG", "DE", "FR", "ES", "IT"], 
                              state="readonly", width=100)
    jezyk_combo.grid(row=7, column=1, pady=8, sticky="w")

    # Status gry
    ctk.CTkLabel(main_frame, text="Status gry").grid(row=8, column=0, pady=8, padx=(0,10), sticky="w")
    status_gra_var = tk.StringVar(value=system_data[10] or "Nie grane")
    status_gra_combo = ctk.CTkComboBox(main_frame, variable=status_gra_var,
                                   values=["Grane", "Nie grane"],
                                   state="readonly", width=150)
    status_gra_combo.grid(row=8, column=1, pady=8, sticky="w")

    # Status kolekcji
    ctk.CTkLabel(main_frame, text="Status kolekcji").grid(row=9, column=0, pady=8, padx=(0,10), sticky="w")
    status_kolekcja_var = tk.StringVar(value=system_data[11] or "W kolekcji")
    status_kolekcja_combo = ctk.CTkComboBox(main_frame, variable=status_kolekcja_var,
                                        values=["W kolekcji", "Na sprzedaż", "Sprzedane", "Nieposiadane", "Do kupienia"],
                                        state="readonly", width=150)
    status_kolekcja_combo.grid(row=9, column=1, pady=8, sticky="w")

    # Cena zakupu (dla statusu "W kolekcji")
    cena_zakupu_label = ctk.CTkLabel(main_frame, text="Cena zakupu")
    cena_zakupu_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")
    
    cena_zakupu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_zakupu_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")
    
    cena_zakupu_entry = ctk.CTkEntry(cena_zakupu_frame, width=100)
    cena_zakupu_entry.pack(side=tk.LEFT, padx=(0, 5))
    if system_data[12]:  # cena_zakupu
        cena_zakupu_entry.insert(0, f"{system_data[12]:.2f}")
    
    waluta_zakupu_var = tk.StringVar(value=system_data[13] if system_data[13] else "PLN")
    waluta_zakupu_combo = ctk.CTkComboBox(cena_zakupu_frame, variable=waluta_zakupu_var,
                                       values=["PLN", "USD", "EUR", "GBP"],
                                       state="readonly", width=70)
    waluta_zakupu_combo.pack(side=tk.LEFT)
    
    # Cena sprzedaży (dla statusu "Sprzedane")
    cena_sprzedazy_label = ctk.CTkLabel(main_frame, text="Cena sprzedaży")
    cena_sprzedazy_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")
    
    cena_sprzedazy_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_sprzedazy_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")
    
    cena_sprzedazy_entry = ctk.CTkEntry(cena_sprzedazy_frame, width=100)
    cena_sprzedazy_entry.pack(side=tk.LEFT, padx=(0, 5))
    if system_data[14]:  # cena_sprzedazy
        cena_sprzedazy_entry.insert(0, f"{system_data[14]:.2f}")
    
    waluta_sprzedazy_var = tk.StringVar(value=system_data[15] if system_data[15] else "PLN")
    waluta_sprzedazy_combo = ctk.CTkComboBox(cena_sprzedazy_frame, variable=waluta_sprzedazy_var,
                                          values=["PLN", "USD", "EUR", "GBP"],
                                          state="readonly", width=70)
    waluta_sprzedazy_combo.pack(side=tk.LEFT)
    
    # Początkowo ukryj oba pola ceny
    cena_zakupu_label.grid_remove()
    cena_zakupu_frame.grid_remove()
    cena_sprzedazy_label.grid_remove()
    cena_sprzedazy_frame.grid_remove()
    
    def on_status_kolekcja_change(*args: Any) -> None:
        """Obsługuje zmianę statusu kolekcji - pokazuje odpowiednie pole ceny"""
        status = status_kolekcja_var.get()
        
        if status in ["W kolekcji", "Na sprzedaż"]:
            # Pokaż cenę zakupu, ukryj cenę sprzedaży
            cena_zakupu_label.grid()
            cena_zakupu_frame.grid()
            cena_sprzedazy_label.grid_remove()
            cena_sprzedazy_frame.grid_remove()
        elif status == "Sprzedane":
            # Pokaż cenę sprzedaży, ukryj cenę zakupu
            cena_zakupu_label.grid_remove()
            cena_zakupu_frame.grid_remove()
            cena_sprzedazy_label.grid()
            cena_sprzedazy_frame.grid()
        else:
            # Ukryj oba pola dla innych statusów
            cena_zakupu_label.grid_remove()
            cena_zakupu_frame.grid_remove()
            cena_sprzedazy_label.grid_remove()
            cena_sprzedazy_frame.grid_remove()
    
    status_kolekcja_var.trace_add('write', on_status_kolekcja_change)
    on_status_kolekcja_change()  # Ustaw początkowy stan

    def on_typ_change(*args: Any) -> None:
        """Obsługuje zmianę typu (Podręcznik Główny/Suplement)"""
        if typ_var.get() == "Suplement":
            # Pokaż pola dla suplementu
            system_glowny_label.grid()
            system_glowny_combo.grid()
            typ_suplementu_label.grid()
            typ_suplementu_frame.grid()
            # Załaduj systemy główne
            main_systems = get_main_systems()
            if main_systems:
                system_values = [f"{sys[0]} - {sys[1]}" for sys in main_systems]
                system_glowny_combo.configure(values=system_values)
                # Ustaw obecnie wybrany system główny
                if system_data[3]:  # system_glowny_id
                    for sys in main_systems:
                        if sys[0] == system_data[3]:
                            system_glowny_var.set(f"{sys[0]} - {sys[1]}")
                            break
        else:
            # Ukryj pola dla suplementu
            system_glowny_label.grid_remove()
            system_glowny_combo.grid_remove()
            typ_suplementu_label.grid_remove()
            typ_suplementu_frame.grid_remove()
        update_dialog_size()

    typ_var.trace_add('write', on_typ_change)
    on_typ_change()  # Ustaw początkowy stan

    def on_save() -> None:
        """Zapisuje zmiany do bazy"""
        nazwa = nazwa_entry.get().strip()
        typ = typ_var.get()
        jezyk = jezyk_var.get()
        
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa systemu jest wymagana.", parent=dialog)
            return
        
        system_glowny_id = None
        typ_suplementu = None
        
        if typ == "Suplement":
            # Zbierz wybrane typy suplementu
            wybrane_typy = [typ for typ, var in typ_suplementu_vars.items() if var.get()]  # type: ignore
            
            if not wybrane_typy:
                messagebox.showerror("Błąd", "Dla suplementu musisz wybrać przynajmniej jeden typ suplementu.", parent=dialog)
                return
            
            # Połącz wybrane typy separatorem
            typ_suplementu = " | ".join(wybrane_typy)  # type: ignore
            
            # System główny jest opcjonalny - może być pusty dla osieroconych suplementów
            if system_glowny_var.get():
                system_glowny_id = int(system_glowny_var.get().split(' - ')[0])
        
        wydawca_id = None
        if wydawca_var.get():
            wydawca_id = int(wydawca_var.get().split(' - ')[0])
        
        # Pobierz ceny w zależności od statusu
        cena_zakupu = None
        waluta_zakupu = None
        cena_sprzedazy = None
        waluta_sprzedazy = None
        
        if status_kolekcja_var.get() in ["W kolekcji", "Na sprzedaż"]:
            cena_str = cena_zakupu_entry.get().strip().replace(',', '.')
            if cena_str:
                try:
                    cena_zakupu = float(cena_str)
                    waluta_zakupu = waluta_zakupu_var.get()
                except ValueError:
                    messagebox.showerror("Błąd", "Cena zakupu musi być liczbą.", parent=dialog)
                    return
        elif status_kolekcja_var.get() == "Sprzedane":
            cena_str = cena_sprzedazy_entry.get().strip().replace(',', '.')
            if cena_str:
                try:
                    cena_sprzedazy = float(cena_str)
                    waluta_sprzedazy = waluta_sprzedazy_var.get()
                except ValueError:
                    messagebox.showerror("Błąd", "Cena sprzedaży musi być liczbą.", parent=dialog)
                    return
        
        # Zbierz wybrane platformy VTT
        vtt_str = None
        if vtt_var.get():
            wybrane_vtt = [platform for platform, var in vtt_platform_vars.items() if var.get()]  # type: ignore
            if wybrane_vtt:
                vtt_str = ", ".join(wybrane_vtt)  # type: ignore
        
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE systemy_rpg 
                SET nazwa=?, typ=?, system_glowny_id=?, typ_suplementu=?, 
                    wydawca_id=?, fizyczny=?, pdf=?, vtt=?, jezyk=?, status_gra=?, status_kolekcja=?,
                    cena_zakupu=?, waluta_zakupu=?, cena_sprzedazy=?, waluta_sprzedazy=? 
                WHERE id=?
            """, (nazwa, typ, system_glowny_id, typ_suplementu, wydawca_id,
                  int(fizyczny_var.get()), int(pdf_var.get()), vtt_str, jezyk if jezyk else None,
                  status_gra_var.get(), status_kolekcja_var.get(),
                  cena_zakupu, waluta_zakupu, cena_sprzedazy, waluta_sprzedazy,
                  system_data[0]))
            conn.commit()
        
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))
        dialog.destroy()

    def on_cancel() -> None:
        """Anuluje edycję"""
        dialog.destroy()

    # Przyciski
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.grid(row=10, column=0, columnspan=2, pady=15, sticky="ew")
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    
    btn_save = ctk.CTkButton(button_frame, text="Zapisz", command=on_save,
                             fg_color="#2E7D32", hover_color="#1B5E20")
    btn_save.grid(row=0, column=0, padx=5, sticky="e")
    
    btn_cancel = ctk.CTkButton(button_frame, text="Anuluj", command=on_cancel,
                               fg_color="#666666", hover_color="#555555")
    btn_cancel.grid(row=0, column=1, padx=5, sticky="w")
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)

def show_supplements_window(parent: tk.Widget, system_id: str, system_name: str) -> None:
    """Wyświetla okno z wszystkimi suplementami dla danego podręcznika głównego"""
    dialog = tk.Toplevel(parent)
    dialog.title(f"Suplementy do: {system_name}")
    dialog.transient(parent.winfo_toplevel())
    dialog.grab_set()
    dialog.resizable(True, True)
    
    # Zastosuj tryb ciemny jeśli aktywny
    root = parent.winfo_toplevel()
    if hasattr(root, 'dark_mode') and getattr(root, 'dark_mode', False):
        apply_dark_theme_to_dialog(dialog)
    
    # Ustawienia okna
    parent.update_idletasks()
    x = parent.winfo_rootx() + 50
    y = parent.winfo_rooty() + 50
    dialog.geometry(f"800x600+{x}+{y}")
    
    # Pobierz suplementy z bazy
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT s.id, s.nazwa, s.typ_suplementu, s.wydawca_id,
                   s.fizyczny, s.pdf, s.jezyk
            FROM systemy_rpg s
            WHERE s.system_glowny_id = ? AND s.typ = 'Suplement'
            ORDER BY s.nazwa
        """, (system_id,))
        supplements_base = c.fetchall()
    
    # Pobierz nazwy wydawców z oddzielnej bazy
    supplements = []
    for supp in supplements_base:
        try:
            with sqlite3.connect("wydawcy.db") as wydawcy_conn:
                w_cursor = wydawcy_conn.cursor()
                wydawca_id = supp[3]  # wydawca_id z zapytania
                
                if wydawca_id:
                    w_cursor.execute("SELECT nazwa FROM wydawcy WHERE id = ?", (wydawca_id,))
                    wydawca_result = w_cursor.fetchone()
                    wydawca_nazwa = wydawca_result[0] if wydawca_result else ""
                else:
                    wydawca_nazwa = ""
        except sqlite3.Error:
            wydawca_nazwa = ""
        
        # Zamień wydawcę w tupli (usuń wydawca_id, dodaj wydawca_nazwa)
        supplements.append(supp[:3] + (wydawca_nazwa,) + supp[4:])  # type: ignore
    
    if not supplements:
        tk.Label(dialog, text=f"Brak suplementów dla systemu: {system_name}", 
                font=('Segoe UI', 12), pady=20).pack()
    else:
        # Nagłówek
        header_frame = tk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(header_frame, text=f"Znaleziono {len(supplements)} suplementów:",  # type: ignore 
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT)
        
        # Tabela z suplementami
        headers = ["ID", "Nazwa suplementu", "Typ suplementu", "Wydawca", "Fizyczny", "PDF", "Język"]
        data: List[List[Any]] = []  # type: ignore
        for supp in supplements:  # type: ignore
            row: List[Any] = [  # type: ignore
                str(supp[0]),  # type: ignore
                supp[1] or "",
                supp[2] or "",
                supp[3] or "",
                "Tak" if supp[4] else "Nie",
                "Tak" if supp[5] else "Nie", 
                supp[6] or ""
            ]
            data.append(row) # type: ignore
        
        sheet = tksheet.Sheet(dialog,
            data=data, # type: ignore
            headers=headers,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            width=750,
            height=450)
        
        # Automatyczne dopasowanie szerokości kolumn
        for col in range(len(headers)):
            max_content = max([len(str(row[col])) for row in data] + [len(headers[col])]) # type: ignore
            width_px = max(80, min(300, int(max_content * 9 + 24)))
            sheet.column_width(column=col, width=width_px)
        
        # Wycentrowanie kolumn ID, Fizyczny, PDF
        sheet.align_columns(columns=[0, 4, 5], align="center")
        
        sheet.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Przycisk zamknij
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)
    btn_close = ttk.Button(btn_frame, text="Zamknij", command=dialog.destroy)
    btn_close.pack()
    
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

def dodaj_suplement_do_systemu(parent: Any, system_glowny_id: int, system_glowny_nazwa: str, refresh_callback: Optional[Callable[..., None]] = None) -> None:
    """Otwiera okno dodawania suplementu do określonego podręcznika głównego"""
    
    init_db()
    reserved_id = get_first_free_id()
    publishers = get_all_publishers()

    dialog = ctk.CTkToplevel(parent)
    dialog.title(f"Dodaj suplement do: {system_glowny_nazwa}")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(True, False)
    
    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - 350
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - 325
    dialog.geometry(f"700x650+{x}+{y}")
    
    # Główny frame z paddingiem
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.columnconfigure(1, weight=1)

    # ID systemu
    ctk.CTkLabel(main_frame, text=f"ID systemu: {reserved_id}", font=("Segoe UI", 12)).grid(
        row=0, column=0, columnspan=2, pady=(0, 8), sticky="w"
    )

    # Nazwa systemu (obowiązkowe)
    ctk.CTkLabel(main_frame, text="Nazwa suplementu *").grid(row=1, column=0, pady=8, padx=(0, 10), sticky="w")
    nazwa_entry = ctk.CTkEntry(main_frame, placeholder_text="Wprowadź nazwę suplementu")
    nazwa_entry.grid(row=1, column=1, pady=8, sticky="ew")
    nazwa_entry.focus_set()

    # Typ (zawsze Suplement)
    ctk.CTkLabel(main_frame, text="Typ *").grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")
    typ_var = tk.StringVar(value="Suplement")
    typ_combo = ctk.CTkComboBox(main_frame, variable=typ_var, 
                            values=["Suplement"], state="readonly")
    typ_combo.grid(row=2, column=1, pady=8, sticky="ew")

    # System główny (predefiniowany)
    ctk.CTkLabel(main_frame, text="System główny *").grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")
    system_glowny_var = tk.StringVar(value=f"{system_glowny_id} - {system_glowny_nazwa}")
    system_glowny_entry = ctk.CTkEntry(main_frame, textvariable=system_glowny_var, state="readonly")
    system_glowny_entry.grid(row=3, column=1, pady=8, sticky="ew")

    # Typ suplementu (obowiązkowe) - wielokrotny wybór
    ctk.CTkLabel(main_frame, text="Typ suplementu *").grid(row=4, column=0, pady=8, padx=(0, 10), sticky="nw")
    typ_suplementu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")
    
    # Słownik do przechowywania zmiennych checkboxów
    typ_suplementu_vars = {}
    typ_suplementu_checkboxes = {}
    typy_suplementow = ["Scenariusz/kampania", "Rozwinięcie zasad", "Moduł", "Lorebook/Sourcebook", "Bestiariusz"]
    
    for i, typ in enumerate(typy_suplementow):
        var = tk.BooleanVar()
        typ_suplementu_vars[typ] = var
        checkbox = ctk.CTkCheckBox(typ_suplementu_frame, text=typ, variable=var, width=280)
        checkbox.grid(row=i, column=0, sticky="w", pady=2)
        typ_suplementu_checkboxes[typ] = checkbox

    # Wydawca
    ctk.CTkLabel(main_frame, text="Wydawca").grid(row=5, column=0, pady=8, padx=(0,10), sticky="w")
    wydawca_var = tk.StringVar()
    wydawca_combo = ctk.CTkComboBox(main_frame, variable=wydawca_var, state="readonly")
    if publishers:
        wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
        wydawca_combo.configure(values=wydawca_values)
    wydawca_combo.grid(row=5, column=1, pady=8, sticky="ew")

    # Posiadanie
    ctk.CTkLabel(main_frame, text="Posiadanie").grid(row=6, column=0, pady=8, padx=(0,10), sticky="nw")
    posiadanie_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    posiadanie_frame.grid(row=6, column=1, pady=8, sticky="w")
    fizyczny_var = tk.BooleanVar()
    pdf_var = tk.BooleanVar()
    fizyczny_check = ctk.CTkCheckBox(posiadanie_frame, text="Fizyczny", variable=fizyczny_var)
    fizyczny_check.grid(row=0, column=0, sticky="w", pady=2)
    pdf_check = ctk.CTkCheckBox(posiadanie_frame, text="PDF", variable=pdf_var)
    pdf_check.grid(row=1, column=0, sticky="w", pady=2)

    # Język
    ctk.CTkLabel(main_frame, text="Język").grid(row=7, column=0, pady=8, padx=(0,10), sticky="w")
    jezyk_var = tk.StringVar(value="PL")
    jezyk_combo = ctk.CTkComboBox(main_frame, variable=jezyk_var, 
                              values=["PL", "ENG", "DE", "FR", "ES", "IT"], 
                              state="readonly", width=100)
    jezyk_combo.grid(row=7, column=1, pady=8, sticky="w")

    # Status gry
    ctk.CTkLabel(main_frame, text="Status gry").grid(row=8, column=0, pady=8, padx=(0,10), sticky="w")
    status_gra_var = tk.StringVar(value="Nie grane")
    status_gra_combo = ctk.CTkComboBox(main_frame, variable=status_gra_var,
                                   values=["Grane", "Nie grane"],
                                   state="readonly", width=150)
    status_gra_combo.grid(row=8, column=1, pady=8, sticky="w")

    # Status kolekcji
    ctk.CTkLabel(main_frame, text="Status kolekcji").grid(row=9, column=0, pady=8, padx=(0,10), sticky="w")
    status_kolekcja_var = tk.StringVar(value="W kolekcji")
    status_kolekcja_combo = ctk.CTkComboBox(main_frame, variable=status_kolekcja_var,
                                        values=["W kolekcji", "Na sprzedaż", "Sprzedane", "Nieposiadane", "Do kupienia"],
                                        state="readonly", width=150)
    status_kolekcja_combo.grid(row=9, column=1, pady=8, sticky="w")

    # Cena zakupu (dla statusu "W kolekcji")
    cena_zakupu_label = ctk.CTkLabel(main_frame, text="Cena zakupu")
    cena_zakupu_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")
    
    cena_zakupu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_zakupu_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")
    
    cena_zakupu_entry = ctk.CTkEntry(cena_zakupu_frame, width=100)
    cena_zakupu_entry.pack(side=tk.LEFT, padx=(0, 5))
    
    waluta_zakupu_var = tk.StringVar(value="PLN")
    waluta_zakupu_combo = ctk.CTkComboBox(cena_zakupu_frame, variable=waluta_zakupu_var,
                                       values=["PLN", "USD", "EUR", "GBP"],
                                       state="readonly", width=70)
    waluta_zakupu_combo.pack(side=tk.LEFT)
    
    # Cena sprzedaży (dla statusu "Sprzedane")
    cena_sprzedazy_label = ctk.CTkLabel(main_frame, text="Cena sprzedaży")
    cena_sprzedazy_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")
    
    cena_sprzedazy_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_sprzedazy_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")
    
    cena_sprzedazy_entry = ctk.CTkEntry(cena_sprzedazy_frame, width=100)
    cena_sprzedazy_entry.pack(side=tk.LEFT, padx=(0, 5))
    
    waluta_sprzedazy_var = tk.StringVar(value="PLN")
    waluta_sprzedazy_combo = ctk.CTkComboBox(cena_sprzedazy_frame, variable=waluta_sprzedazy_var,
                                          values=["PLN", "USD", "EUR", "GBP"],
                                          state="readonly", width=70)
    waluta_sprzedazy_combo.pack(side=tk.LEFT)
    
    # Początkowo ukryj oba pola ceny
    cena_zakupu_label.grid_remove()
    cena_zakupu_frame.grid_remove()
    cena_sprzedazy_label.grid_remove()
    cena_sprzedazy_frame.grid_remove()
    
    def on_status_kolekcja_change(*args: Any) -> None:
        """Obsługuje zmianę statusu kolekcji - pokazuje odpowiednie pole ceny"""
        status = status_kolekcja_var.get()
        
        if status in ["W kolekcji", "Na sprzedaż"]:
            # Pokaż cenę zakupu, ukryj cenę sprzedaży
            cena_zakupu_label.grid()
            cena_zakupu_frame.grid()
            cena_sprzedazy_label.grid_remove()
            cena_sprzedazy_frame.grid_remove()
        elif status == "Sprzedane":
            # Pokaż cenę sprzedaży, ukryj cenę zakupu
            cena_zakupu_label.grid_remove()
            cena_zakupu_frame.grid_remove()
            cena_sprzedazy_label.grid()
            cena_sprzedazy_frame.grid()
        else:
            # Ukryj oba pola dla innych statusów
            cena_zakupu_label.grid_remove()
            cena_zakupu_frame.grid_remove()
            cena_sprzedazy_label.grid_remove()
            cena_sprzedazy_frame.grid_remove()
    
    status_kolekcja_var.trace_add('write', on_status_kolekcja_change)
    on_status_kolekcja_change()  # Ustaw początkowy stan

    def on_ok() -> None:
        """Zapisuje nowy suplement do bazy"""
        nazwa = nazwa_entry.get().strip()
        jezyk = jezyk_var.get()
        
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa suplementu jest wymagana.", parent=dialog) # type: ignore
            return
        
        # Zbierz wybrane typy suplementu
        wybrane_typy = [typ for typ, var in typ_suplementu_vars.items() if var.get()] # type: ignore
        
        if not wybrane_typy:
            messagebox.showerror("Błąd", "Musisz wybrać przynajmniej jeden typ suplementu.", parent=dialog) # type: ignore
            return
        
        # Połącz wybrane typy separatorem
        typ_suplementu = " | ".join(wybrane_typy) # type: ignore
        
        wydawca_id = None
        if wydawca_var.get():
            wydawca_id = int(wydawca_var.get().split(' - ')[0])
        
        # Pobierz ceny w zależności od statusu
        cena_zakupu = None
        waluta_zakupu = None
        cena_sprzedazy = None
        waluta_sprzedazy = None
        
        if status_kolekcja_var.get() in ["W kolekcji", "Na sprzedaż"]:
            cena_str = cena_zakupu_entry.get().strip().replace(',', '.')
            if cena_str:
                try:
                    cena_zakupu = float(cena_str)
                    waluta_zakupu = waluta_zakupu_var.get()
                except ValueError:
                    messagebox.showerror("Błąd", "Cena zakupu musi być liczbą.", parent=dialog) # type: ignore
                    return
        elif status_kolekcja_var.get() == "Sprzedane":
            cena_str = cena_sprzedazy_entry.get().strip().replace(',', '.')
            if cena_str:
                try:
                    cena_sprzedazy = float(cena_str)
                    waluta_sprzedazy = waluta_sprzedazy_var.get()
                except ValueError:
                    messagebox.showerror("Błąd", "Cena sprzedaży musi być liczbą.", parent=dialog) # type: ignore
                    return
        
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO systemy_rpg (id, nazwa, typ, system_glowny_id, typ_suplementu, 
                                       wydawca_id, fizyczny, pdf, jezyk, status_gra, status_kolekcja,
                                       cena_zakupu, waluta_zakupu, cena_sprzedazy, waluta_sprzedazy) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (reserved_id, nazwa, "Suplement", system_glowny_id, typ_suplementu, wydawca_id,
                  int(fizyczny_var.get()), int(pdf_var.get()), jezyk if jezyk else None,
                  status_gra_var.get(), status_kolekcja_var.get(),
                  cena_zakupu, waluta_zakupu, cena_sprzedazy, waluta_sprzedazy))
            conn.commit()
        
        messagebox.showinfo("Sukces", f"Suplement '{nazwa}' został dodany do systemu '{system_glowny_nazwa}'.", parent=dialog) # type: ignore
        
        if refresh_callback:
            refresh_callback(dark_mode=getattr(parent, 'dark_mode', False))
        dialog.destroy()

    def on_cancel() -> None:
        """Anuluje dodawanie"""
        dialog.destroy()

    # Przyciski
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.grid(row=10, column=0, columnspan=2, pady=15, sticky="ew")
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    
    btn_ok = ctk.CTkButton(button_frame, text="Dodaj suplement", command=on_ok,
                           fg_color="#2E7D32", hover_color="#1B5E20")
    btn_ok.grid(row=0, column=0, padx=5, sticky="e")
    
    btn_cancel = ctk.CTkButton(button_frame, text="Anuluj", command=on_cancel,
                               fg_color="#666666", hover_color="#555555")
    btn_cancel.grid(row=0, column=1, padx=5, sticky="w")
    
    dialog.protocol("WM_DELETE_WINDOW", on_cancel)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
