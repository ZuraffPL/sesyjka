# Moduł: Systemy RPG
# Tutaj będą funkcje i klasy związane z obsługą systemów RPG
import tkinter as tk
import tkinter.font as tkfont
import tksheet  # type: ignore
from tkinter import ttk, messagebox
import sqlite3
import logging
import threading
from typing import Optional, Callable, Sequence, Any, Dict, List, Union
import customtkinter as ctk  # type: ignore
from database_manager import get_db_path, get_app_data_dir
from font_scaling import scale_font_size
from ctk_table import CTkDataTable
from dialog_utils import apply_safe_geometry, clamp_geometry, create_ctk_toplevel

DB_FILE = get_db_path("systemy_rpg.db")


# ── Konfiguracja loggera ────────────────────────────────────────────────────
def _setup_logger() -> logging.Logger:
    """Tworzy logger zapisujący do pliku w katalogu danych aplikacji."""
    _logger = logging.getLogger("systemy_rpg")
    if _logger.handlers:
        return _logger  # Już skonfigurowany
    _logger.setLevel(logging.DEBUG)
    try:
        log_path = get_app_data_dir() / "sesyjka_debug.log"
        fh = logging.FileHandler(str(log_path), encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(fmt)
        _logger.addHandler(fh)
    except Exception as _e:
        print(f"[systemy_rpg] Nie można otworzyć pliku logu: {_e}")
    return _logger


logger = _setup_logger()
# ────────────────────────────────────────────────────────────────────────────

# Przechowuj aktywne filtry na poziomie modułu
active_filters_systemy: Dict[str, Any] = {}
# Przechowuj stan sortowania na poziomie modułu
active_sort_systemy: Dict[str, Any] = {"column": "ID", "reverse": False}
# Zapisane szerokości kolumn (None = użyj auto-obliczonych)
active_col_widths_systemy: List[int] = []
# Stan przełącznika rozwiń/zwiń wszystkie suplementy
all_expanded_systemy: bool = False
# Widoczność kolumn w tabeli systemów (klucz = nazwa kolumny, wartość = czy widoczna)
active_visible_cols_systemy: Dict[str, bool] = {
    "Nazwa systemu": True,
    "Typ": True,
    "System główny": True,
    "Typ suplementu": True,
    "Wydawca": True,
    "Fizyczny": True,
    "PDF": True,
    "VTT": True,
    "Język": True,
    "Status": True,
    "Cena": True,
}

# Kolumny, które zawsze są widoczne (nie można ich ukryć)
_ALWAYS_VISIBLE_SYSTEMY = {"", "ID"}


def _migrate_remove_cross_db_fks() -> None:
    """Jednorazowa migracja: usuwa cross-bazowy FK wydawcy z tabeli systemy_rpg.

    `FOREIGN KEY (wydawca_id) REFERENCES wydawcy(id)` wskazuje na inny plik .db,
    co jest nieobsługiwane przez SQLite i powoduje błąd przy INSERT gdy
    PRAGMA foreign_keys = ON.  FK do systemy_rpg(id) (self-reference) jest
    zachowywany — leży w tej samej bazie.
    """
    import os

    if not os.path.exists(DB_FILE):
        return  # Baza nie istnieje — init_db() stworzy ją poprawnie

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.isolation_level = None  # tryb explicit — pełna kontrola nad transakcją
    try:
        c = conn.cursor()
        c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='systemy_rpg'")
        row = c.fetchone()
        if row is None or "REFERENCES wydawcy" not in row["sql"]:
            return  # Migracja nie jest potrzebna

        logger.info("Migracja: usuwanie cross-bazowego FK wydawcy z tabeli systemy_rpg…")

        # Pobierz faktyczne kolumny istniejącej tabeli
        c.execute("PRAGMA table_info(systemy_rpg)")
        existing_cols = [r["name"] for r in c.fetchall()]

        # Docelowa lista kolumn nowej tabeli
        target_cols = [
            "id", "nazwa", "typ", "system_glowny_id", "typ_suplementu", "wydawca_id",
            "fizyczny", "pdf", "jezyk", "status_gra", "status_kolekcja",
            "cena_zakupu", "waluta_zakupu", "cena_sprzedazy", "waluta_sprzedazy",
            "vtt", "system_glowny_nazwa_custom",
        ]
        copy_cols = [col for col in target_cols if col in existing_cols]
        cols_str = ", ".join(copy_cols)

        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("BEGIN")

        conn.execute(
            """
            CREATE TABLE systemy_rpg_mig_new (
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
                vtt TEXT,
                system_glowny_nazwa_custom TEXT,
                FOREIGN KEY (system_glowny_id) REFERENCES systemy_rpg(id)
            )
        """
        )
        conn.execute(
            f"INSERT INTO systemy_rpg_mig_new ({cols_str}) "
            f"SELECT {cols_str} FROM systemy_rpg"
        )
        conn.execute("DROP TABLE systemy_rpg")
        conn.execute("ALTER TABLE systemy_rpg_mig_new RENAME TO systemy_rpg")

        conn.execute("COMMIT")
        conn.execute("PRAGMA foreign_keys = ON")
        logger.info("Migracja systemy_rpg zakończona pomyślnie.")
    except Exception as exc:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        logger.error("Błąd podczas migracji systemy_rpg: %s", exc)
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Inicjalizuje bazę danych systemów RPG"""
    # Jednorazowa migracja usuwająca cross-bazowe FK sprzed poprawki
    _migrate_remove_cross_db_fks()

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute(
            """
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
                FOREIGN KEY (system_glowny_id) REFERENCES systemy_rpg(id)
            )
        """
        )

        # Migracja - dodaj nowe kolumny do istniejących tabel
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN status_gra TEXT DEFAULT 'Nie grane'")
        except sqlite3.OperationalError:
            # Kolumna już istnieje
            pass

        try:
            c.execute(
                "ALTER TABLE systemy_rpg ADD COLUMN status_kolekcja TEXT DEFAULT 'W kolekcji'"
            )
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

        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN system_glowny_nazwa_custom TEXT")
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
            _w: Any = widget
            _w.configure(
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
        logger.debug(
            "TclError w _apply_dark_theme_to_widget (ignorowany): %s", widget, exc_info=True
        )


def get_first_free_id() -> int:
    """Zwraca pierwszy wolny ID w bazie systemów RPG"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
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
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        # Najpierw sprawdź czy tabela istnieje i jest pusta
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='systemy_rpg'")
        if not c.fetchone():
            return []

        c.execute("SELECT COUNT(*) FROM systemy_rpg")
        if c.fetchone()[0] == 0:
            return []

        # Pobierz systemy z LEFT JOIN do wydawców z innej bazy
        c.execute(
            """
            SELECT s.id, s.nazwa, s.typ, s.system_glowny_id, s.typ_suplementu, 
                   s.wydawca_id, s.fizyczny, s.pdf, s.vtt, s.jezyk,
                   s.status_gra, s.status_kolekcja,
                   s.cena_zakupu, s.waluta_zakupu, s.cena_sprzedazy, s.waluta_sprzedazy,
                   s.system_glowny_nazwa_custom
            FROM systemy_rpg s
            ORDER BY s.id ASC
        """
        )
        systems = c.fetchall()

    # Pobierz wszystkich wydawców jednym zapytaniem
    publishers_map: Dict[int, str] = {}
    try:
        with sqlite3.connect(get_db_path("wydawcy.db")) as wydawcy_conn:
            wydawcy_conn.row_factory = sqlite3.Row
            wydawcy_conn.execute("PRAGMA foreign_keys = ON")
            w_cursor = wydawcy_conn.cursor()
            w_cursor.execute("SELECT id, nazwa FROM wydawcy")
            publishers_map = {row[0]: row[1] for row in w_cursor.fetchall()}
    except sqlite3.Error:
        pass

    result = []
    for system in systems:
        wydawca_nazwa = publishers_map.get(system[5], "") if system[5] else ""

        # Sformuj status jako string: "Grane/Nie grane, W kolekcji/Na sprzedaż"
        status_gra = system[10] if system[10] else "Nie grane"
        status_kolekcja = system[11] if system[11] else "W kolekcji"
        # Jeśli status to "Na sprzedaż", pokaż jako "W kolekcji, Na sprzedaż"
        status_kolekcja_display = (
            "W kolekcji, Na sprzedaż" if status_kolekcja == "Na sprzedaż" else status_kolekcja
        )
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
        # Format: id, nazwa, typ, system_glowny_id, typ_suplementu, wydawca_nazwa,
        # fizyczny, pdf, vtt, jezyk, status, cena, system_glowny_nazwa_custom
        result.append(
            (  # type: ignore
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
                cena_str,  # cena (zakupu lub sprzedaży w zależności od statusu)
                system[16] if len(system) > 16 else None,  # system_glowny_nazwa_custom
            )
        )  # type: ignore

    return result  # type: ignore


def get_main_systems() -> list[tuple[int, str]]:
    """Pobiera systemy główne (Podręcznik Główny) do wyboru jako rodzic dla suplementów"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute(
            "SELECT id, nazwa FROM systemy_rpg WHERE typ = 'Podręcznik Główny' ORDER BY nazwa"
        )
        return c.fetchall()


def get_all_publishers() -> list[tuple[int, str]]:
    """Pobiera wszystkich wydawców z bazy wydawców"""
    try:
        with sqlite3.connect(get_db_path("wydawcy.db")) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
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

    dialog = create_ctk_toplevel(parent)
    dialog.withdraw()  # ukryj podczas budowania – eliminuje czarną ramkę
    dialog.title("Dodaj system RPG do bazy")
    dialog.transient(parent)
    dialog.resizable(True, True)

    apply_safe_geometry(dialog, parent, 950, 550)

    # Główna ramka z padding (scrollowalna dla małych ekranów / wysokiego DPI)
    main_frame = ctk.CTkScrollableFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.columnconfigure(1, weight=1)
    main_frame.columnconfigure(3, weight=1)

    # ID systemu
    ctk.CTkLabel(
        main_frame, text=f"ID systemu: {reserved_id}", font=("Segoe UI", scale_font_size(12))
    ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

    # Nazwa systemu (obowiązkowe)
    ctk.CTkLabel(main_frame, text="Nazwa systemu *").grid(
        row=1, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    nazwa_entry = ctk.CTkEntry(main_frame, placeholder_text="Wprowadź nazwę systemu")
    nazwa_entry.grid(row=1, column=1, pady=8, sticky="ew")
    dialog.after(100, lambda: nazwa_entry.focus_set() if nazwa_entry.winfo_exists() else None)

    # Typ (Podręcznik Główny / Suplement)
    ctk.CTkLabel(main_frame, text="Typ *").grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")
    typ_var = tk.StringVar(value="Podręcznik Główny")
    typ_combo = ctk.CTkComboBox(
        main_frame, variable=typ_var, values=["Podręcznik Główny", "Suplement"], state="readonly"
    )
    typ_combo.grid(row=2, column=1, pady=8, sticky="ew")

    # System główny (dla suplementów) - początkowo ukryte, opcjonalne
    system_glowny_label = ctk.CTkLabel(main_frame, text="System główny (opcjonalnie)")
    system_glowny_label.grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")
    system_glowny_var = tk.StringVar()
    system_glowny_combo = ctk.CTkComboBox(main_frame, variable=system_glowny_var, state="readonly")
    system_glowny_combo.grid(row=3, column=1, pady=8, sticky="ew")

    # Niestandardowa nazwa systemu głównego (dla suplementów bez systemu w kolekcji)
    # - w tym samym rzędzie
    system_glowny_custom_label = ctk.CTkLabel(main_frame, text="lub wpisz nazwę:")
    system_glowny_custom_label.grid(row=3, column=2, pady=8, padx=(20, 10), sticky="w")
    system_glowny_custom_entry = ctk.CTkEntry(
        main_frame, placeholder_text="Nazwa systemu spoza kolekcji", width=200
    )
    system_glowny_custom_entry.grid(row=3, column=3, pady=8, sticky="ew")

    # Typ suplementu - początkowo ukryte, obowiązkowe dla suplementów (wielokrotny wybór)
    typ_suplementu_label = ctk.CTkLabel(main_frame, text="Typ suplementu *")
    typ_suplementu_label.grid(row=4, column=0, pady=8, padx=(0, 10), sticky="nw")
    typ_suplementu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")

    # Słownik do przechowywania zmiennych checkboxów
    typ_suplementu_vars = {}
    typ_suplementu_checkboxes = {}
    typy_suplementow = [
        "Scenariusz/kampania",
        "Rozwinięcie zasad",
        "Moduł",
        "Lorebook/Sourcebook",
        "Bestiariusz",
    ]

    for i, typ in enumerate(typy_suplementow):
        var = tk.BooleanVar()
        typ_suplementu_vars[typ] = var
        checkbox = ctk.CTkCheckBox(typ_suplementu_frame, text=typ, variable=var, width=280)
        checkbox.grid(row=i, column=0, sticky="w", pady=2)
        typ_suplementu_checkboxes[typ] = checkbox

    # Wydawca
    ctk.CTkLabel(main_frame, text="Wydawca").grid(
        row=5, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    wydawca_var = tk.StringVar()
    wydawca_combo = ctk.CTkComboBox(main_frame, variable=wydawca_var, state="readonly")

    def refresh_publishers_on_click(event: Any = None) -> None:
        """Odświeża listę wydawców z bazy przy każdym kliknięciu w combobox"""
        nonlocal publishers
        current_value = wydawca_var.get()
        publishers = get_all_publishers()
        if publishers:
            wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
            wydawca_combo.configure(values=wydawca_values)
            if current_value and current_value in wydawca_values:
                wydawca_var.set(current_value)
        else:
            wydawca_combo.configure(values=[])

    # Inicjalne załadowanie listy
    if publishers:
        wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
        wydawca_combo.configure(values=wydawca_values)

    # Odśwież listę wydawców przy każdym kliknięciu w combobox
    wydawca_combo.bind("<Button-1>", refresh_publishers_on_click)
    wydawca_combo.grid(row=5, column=1, pady=8, sticky="ew")

    # Posiadanie
    ctk.CTkLabel(main_frame, text="Posiadanie").grid(
        row=6, column=0, pady=8, padx=(0, 10), sticky="nw"
    )
    posiadanie_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    posiadanie_frame.grid(row=6, column=1, pady=8, sticky="w", columnspan=3)
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
        "Telespire",
    ]

    # Frame dla wyboru platform VTT w prawej kolumnie (początkowo ukryty)
    vtt_selection_frame = ctk.CTkFrame(posiadanie_frame, fg_color="transparent")
    vtt_selection_frame.grid(row=0, column=1, rowspan=3, sticky="nsw", padx=(20, 0))

    # Label dla platform VTT
    vtt_label = ctk.CTkLabel(
        vtt_selection_frame, text="Platformy VTT:", font=("Segoe UI", scale_font_size(10))
    )
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
        parent.update_idletasks()

        is_vtt = vtt_var.get()
        is_suplement = typ_var.get() == "Suplement"

        if is_vtt and is_suplement:
            width, height = 1100, 850
        elif is_vtt:
            width, height = 1100, 680
        elif is_suplement:
            width, height = 950, 720
        else:
            width, height = 950, 560

        geo = clamp_geometry(dialog, parent, width, height)
        dialog.geometry(geo)

    def on_vtt_change(*args: Any) -> None:
        """Obsługuje zmianę checkboxa VTT - pokazuje/ukrywa listę platform"""
        if vtt_var.get():
            vtt_selection_frame.grid()
        else:
            vtt_selection_frame.grid_remove()
        update_dialog_size()

    vtt_var.trace_add('write', on_vtt_change)

    # Język
    ctk.CTkLabel(main_frame, text="Język").grid(row=7, column=0, pady=8, padx=(0, 10), sticky="w")
    jezyk_var = tk.StringVar(value="PL")
    jezyk_combo = ctk.CTkComboBox(
        main_frame,
        variable=jezyk_var,
        values=["PL", "ENG", "DE", "FR", "ES", "IT"],
        state="readonly",
        width=100,
    )
    jezyk_combo.grid(row=7, column=1, pady=8, sticky="w")

    # Status gry
    ctk.CTkLabel(main_frame, text="Status gry").grid(
        row=8, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_gra_var = tk.StringVar(value="Nie grane")
    status_gra_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_gra_var,
        values=["Grane", "Nie grane"],
        state="readonly",
        width=150,
    )
    status_gra_combo.grid(row=8, column=1, pady=8, sticky="w")

    # Status kolekcji
    ctk.CTkLabel(main_frame, text="Status kolekcji").grid(
        row=9, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_kolekcja_var = tk.StringVar(value="W kolekcji")
    status_kolekcja_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_kolekcja_var,
        values=["W kolekcji", "Na sprzedaż", "Sprzedane", "Nieposiadane", "Do kupienia"],
        state="readonly",
        width=150,
    )
    status_kolekcja_combo.grid(row=9, column=1, pady=8, sticky="w")

    # Cena zakupu (dla statusu "W kolekcji")
    cena_zakupu_label = ctk.CTkLabel(main_frame, text="Cena zakupu")
    cena_zakupu_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")

    cena_zakupu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_zakupu_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")

    cena_zakupu_entry = ctk.CTkEntry(cena_zakupu_frame, width=100)
    cena_zakupu_entry.pack(side=tk.LEFT, padx=(0, 5))

    waluta_zakupu_var = tk.StringVar(value="PLN")
    waluta_zakupu_combo = ctk.CTkComboBox(
        cena_zakupu_frame,
        variable=waluta_zakupu_var,
        values=["PLN", "USD", "EUR", "GBP"],
        state="readonly",
        width=70,
    )
    waluta_zakupu_combo.pack(side=tk.LEFT)

    # Cena sprzedaży (dla statusu "Sprzedane")
    cena_sprzedazy_label = ctk.CTkLabel(main_frame, text="Cena sprzedaży")
    cena_sprzedazy_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")

    cena_sprzedazy_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_sprzedazy_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")

    cena_sprzedazy_entry = ctk.CTkEntry(cena_sprzedazy_frame, width=100)
    cena_sprzedazy_entry.pack(side=tk.LEFT, padx=(0, 5))

    waluta_sprzedazy_var = tk.StringVar(value="PLN")
    waluta_sprzedazy_combo = ctk.CTkComboBox(
        cena_sprzedazy_frame,
        variable=waluta_sprzedazy_var,
        values=["PLN", "USD", "EUR", "GBP"],
        state="readonly",
        width=70,
    )
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
            system_glowny_custom_label.grid(row=3, column=2, pady=8, padx=(20, 10), sticky="w")
            system_glowny_custom_entry.grid(row=3, column=3, pady=8, sticky="ew")
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
            system_glowny_custom_label.grid_remove()
            system_glowny_custom_entry.grid_remove()
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
            messagebox.showerror("Błąd", "Nazwa systemu jest wymagana.", parent=dialog)  # type: ignore
            return

        system_glowny_id = None
        typ_suplementu = None
        system_glowny_custom = None

        if typ == "Suplement":
            # Zbierz wybrane typy suplementu
            wybrane_typy = [typ for typ, var in typ_suplementu_vars.items() if var.get()]  # type: ignore

            if not wybrane_typy:
                messagebox.showerror("Błąd", "Dla suplementu musisz wybrać przynajmniej jeden typ suplementu.", parent=dialog)  # type: ignore
                return

            # Połącz wybrane typy separatorem
            typ_suplementu = " | ".join(wybrane_typy)  # type: ignore

            # System główny jest opcjonalny - może być pusty dla osieroconych suplementów
            if system_glowny_var.get():
                system_glowny_id = int(system_glowny_var.get().split(' - ')[0])
            elif system_glowny_custom_entry.get().strip():
                # Jeśli nie wybrano z listy, ale wpisano niestandardową nazwę
                system_glowny_custom = system_glowny_custom_entry.get().strip()

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
                    messagebox.showerror("Błąd", "Cena zakupu musi być liczbą.", parent=dialog)  # type: ignore
                    return
        elif status_kolekcja_var.get() == "Sprzedane":
            cena_str = cena_sprzedazy_entry.get().strip().replace(',', '.')
            if cena_str:
                try:
                    cena_sprzedazy = float(cena_str)
                    waluta_sprzedazy = waluta_sprzedazy_var.get()
                except ValueError:
                    messagebox.showerror("Błąd", "Cena sprzedaży musi być liczbą.", parent=dialog)  # type: ignore
                    return

        # Zbierz wybrane platformy VTT
        vtt_str = None
        if vtt_var.get():
            wybrane_vtt = [platform for platform, var in vtt_platform_vars.items() if var.get()]  # type: ignore
            if wybrane_vtt:
                vtt_str = ", ".join(wybrane_vtt)  # type: ignore

        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO systemy_rpg (id, nazwa, typ, system_glowny_id, typ_suplementu, 
                                       wydawca_id, fizyczny, pdf, vtt, jezyk,
                                       status_gra, status_kolekcja,
                                       cena_zakupu, waluta_zakupu, cena_sprzedazy,
                                       waluta_sprzedazy,
                                       system_glowny_nazwa_custom) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    reserved_id,
                    nazwa,
                    typ,
                    system_glowny_id,
                    typ_suplementu,
                    wydawca_id,
                    int(fizyczny_var.get()),
                    int(pdf_var.get()),
                    vtt_str,
                    jezyk if jezyk else None,
                    status_gra_var.get(),
                    status_kolekcja_var.get(),
                    cena_zakupu,
                    waluta_zakupu,
                    cena_sprzedazy,
                    waluta_sprzedazy,
                    system_glowny_custom,
                ),
            )
            conn.commit()

        if refresh_callback:
            refresh_callback(dark_mode=getattr(parent, 'dark_mode', False))
        dialog.destroy()

    def on_cancel() -> None:
        """Anuluje dodawanie"""
        dialog.destroy()

    # Przyciski
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.grid(row=10, column=0, columnspan=4, pady=15, sticky="ew")
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)

    btn_ok = ctk.CTkButton(
        button_frame, text="Dodaj", command=on_ok, fg_color="#2E7D32", hover_color="#1B5E20"
    )
    btn_ok.grid(row=0, column=0, padx=5, sticky="e")

    btn_cancel = ctk.CTkButton(
        button_frame, text="Anuluj", command=on_cancel, fg_color="#666666", hover_color="#555555"
    )
    btn_cancel.grid(row=0, column=1, padx=5, sticky="w")

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.after(0, dialog.deiconify)  # pokaż gdy wszystkie widgety są gotowe


def fill_systemy_rpg_tab(
    tab: tk.Frame,
    dark_mode: bool = False,
    _preloaded_data: Optional[List[Any]] = None,
) -> None:  # type: ignore
    """Wypełnia zakładkę systemów RPG danymi z bazy – CTkDataTable."""
    init_db()

    # ── Szybka ścieżka: odśwież dane bez niszczenia całego UI ───────────────
    cache = getattr(tab, '_systemy_tab_cache', None)
    if (
        cache is not None
        and cache.get('table_ref') is not None
        and cache.get('dark_mode') == dark_mode
    ):
        try:
            if cache['table_ref'].winfo_exists():
                if _preloaded_data is None:

                    def _bg_fast_sys() -> None:
                        data = get_all_systems()
                        tab.after(
                            0,
                            lambda: fill_systemy_rpg_tab(
                                tab, dark_mode, _preloaded_data=data
                            ),
                        )

                    threading.Thread(target=_bg_fast_sys, daemon=True).start()
                    return
                cache['records_ref'][0] = _preloaded_data
                cache['rebuild_fn']()
                return
        except Exception:
            pass
        del tab._systemy_tab_cache  # type: ignore[attr-defined]

    if _preloaded_data is None:

        def _bg_full_sys() -> None:
            data = get_all_systems()
            tab.after(
                0,
                lambda: fill_systemy_rpg_tab(tab, dark_mode, _preloaded_data=data),
            )

        threading.Thread(target=_bg_full_sys, daemon=True).start()
        return

    for widget in tab.winfo_children():
        widget.destroy()

    records_ref: List[List[Any]] = [_preloaded_data]  # type: ignore

    _HEADERS = [
        "",
        "ID",
        "Nazwa systemu",
        "Typ",
        "System główny",
        "Typ suplementu",
        "Wydawca",
        "Fizyczny",
        "PDF",
        "VTT",
        "Język",
        "Status",
        "Cena",
    ]
    # col: 0=sym, 1=ID, 2=nazwa, 3=typ, 4=sys_gl, 5=typ_supl,
    #      6=wydawca, 7=fiz, 8=pdf, 9=vtt, 10=jezyk, 11=status, 12=cena

    bg_top = "#1e1e2e" if dark_mode else "#f5f5f5"
    fg_top = "#e0e0e0" if dark_mode else "#212121"
    FONT = ("Segoe UI", scale_font_size(10))
    _mf = tkfont.Font(family="Segoe UI", size=scale_font_size(10))
    _mf_bold = tkfont.Font(family="Segoe UI", size=scale_font_size(10), weight="bold")

    # ── Hierarchia i stan ─────────────────────────────────────────────────
    from collections import OrderedDict

    main_systems: OrderedDict[Any, Any] = OrderedDict()
    supplements: Dict[Any, List[Any]] = {}
    orphaned_supplements: List[Any] = []
    expanded_state: Dict[Any, bool] = {}
    current_sort_reverse: List[bool] = [active_sort_systemy.get("reverse", False)]
    _table: List[Optional[CTkDataTable]] = [None]
    search_var: tk.StringVar = tk.StringVar()

    def _apply_record_filters(recs: List[Any]) -> List[Any]:
        result = []
        for rec in recs:
            if active_filters_systemy.get('typ', 'Wszystkie') not in ('Wszystkie', rec[2]):
                continue
            if active_filters_systemy.get('wydawca', 'Wszystkie') not in (
                'Wszystkie',
                rec[5] or '',
            ):
                continue
            pf = active_filters_systemy.get('posiadanie', 'Wszystkie')
            if pf == 'Fizyczny' and not rec[6]:
                continue
            if pf == 'PDF' and not rec[7]:
                continue
            if pf == 'Fizyczny i PDF' and not (rec[6] and rec[7]):
                continue
            if pf == 'Żadne' and (rec[6] or rec[7]):
                continue
            sf = active_filters_systemy.get('status', 'Wszystkie')
            if sf != 'Wszystkie' and sf not in (rec[10] or ''):
                continue
            wf = active_filters_systemy.get('waluta', 'Wszystkie')
            if wf != 'Wszystkie' and wf not in (rec[11] or ''):
                continue
            jf = active_filters_systemy.get('jezyk', 'Wszystkie')
            if jf not in ('Wszystkie', rec[9] or ''):
                continue
            result.append(rec)
        return result  # type: ignore[return-value]

    def _rebuild_groups() -> None:
        nonlocal main_systems, supplements, orphaned_supplements
        filtered = _apply_record_filters(records_ref[0])
        phrase = search_var.get().strip().lower()
        all_main: OrderedDict[Any, Any] = OrderedDict()
        all_supps: Dict[Any, List[Any]] = {}
        all_orph: List[Any] = []
        for rec in filtered:
            if rec[2] == "Podręcznik Główny":
                all_main[rec[0]] = rec
            elif rec[2] == "Suplement":
                pid = rec[3]
                if pid and pid in all_main:
                    all_supps.setdefault(pid, []).append(rec)
                else:
                    all_orph.append(rec)
        main_systems.clear()
        supplements.clear()
        orphaned_supplements.clear()
        if not phrase:
            main_systems.update(all_main)
            supplements.update(all_supps)
            orphaned_supplements.extend(all_orph)
        else:
            for mid, rec in all_main.items():
                name_match = phrase in (rec[1] or '').lower()
                supps = all_supps.get(mid, [])
                matching_supps = [s for s in supps if phrase in (s[1] or '').lower()]
                if name_match or matching_supps:
                    main_systems[mid] = rec
                    supplements[mid] = supps if name_match else matching_supps
            for rec in all_orph:
                if phrase in (rec[1] or '').lower():
                    orphaned_supplements.append(rec)

    def _build_hierarchical_data() -> List[List[Any]]:
        data_h: List[List[Any]] = []
        for main_id in main_systems:
            rec = main_systems[main_id]
            has_supps = main_id in supplements
            scnt = len(supplements.get(main_id, []))
            symbol = "[-]" if expanded_state.get(main_id) else ("[+]" if has_supps else "   ")
            name = (rec[1] or "") + (f" ({scnt} supl.)" if has_supps else "")
            row: List[Any] = [
                symbol,
                str(rec[0]),
                name,
                rec[2] or "",
                "",
                "",
                rec[5] or "",
                "Tak" if rec[6] else "Nie",
                "Tak" if rec[7] else "Nie",
                rec[8] or "",
                rec[9] or "",
                rec[10] or "",
                rec[11] or "",
            ]
            data_h.append(row)
            if expanded_state.get(main_id) and main_id in supplements:
                for sr in sorted(supplements[main_id], key=lambda x: x[1] or ""):
                    mn = main_systems[main_id][1] if main_id in main_systems else ""
                    sr_row: List[Any] = [
                        "   →",
                        str(sr[0]),
                        "  " + (sr[1] or ""),
                        sr[2] or "",
                        mn,
                        sr[4] or "",
                        sr[5] or "",
                        "Tak" if sr[6] else "Nie",
                        "Tak" if sr[7] else "Nie",
                        sr[8] or "",
                        sr[9] or "",
                        sr[10] or "",
                        sr[11] or "",
                    ]
                    data_h.append(sr_row)
        for rec in sorted(
            orphaned_supplements,
            key=lambda r: (r[1] or '').lower(),
            reverse=current_sort_reverse[0],
        ):
            mn = ""
            if rec[3]:
                try:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.row_factory = sqlite3.Row
                        conn.execute("PRAGMA foreign_keys = ON")
                        row_r = (
                            conn.cursor()
                            .execute("SELECT nazwa FROM systemy_rpg WHERE id=?", (rec[3],))
                            .fetchone()
                        )
                        if row_r:
                            mn = row_r[0]
                except sqlite3.Error:
                    pass
            elif rec[12]:
                mn = rec[12]
            oph_row: List[Any] = [
                "   !",
                str(rec[0]),
                rec[1] or "",
                rec[2] or "",
                mn,
                rec[4] or "",
                rec[5] or "",
                "Tak" if rec[6] else "Nie",
                "Tak" if rec[7] else "Nie",
                rec[8] or "",
                rec[9] or "",
                rec[10] or "",
                rec[11] or "",
            ]
            data_h.append(oph_row)
        return data_h

    displayed_data: List[List[Any]] = []

    def _do_sort_main_systems(reverse: bool) -> None:
        sort_by = sort_var.get()

        def _key(x: Any) -> Any:
            if sort_by == "Nazwa systemu":
                return (main_systems[x][1] or '').lower()
            elif sort_by == "Wydawca":
                return (main_systems[x][5] or '').lower()
            elif sort_by == "Język":
                return (main_systems[x][9] or '').lower()
            elif sort_by == "Status":
                return (main_systems[x][10] or '').lower()
            elif sort_by == "Posiadanie":
                r = main_systems[x]
                if r[6] and r[7]:
                    return "1"
                elif r[6]:
                    return "2"
                elif r[7]:
                    return "3"
                return "4"
            elif sort_by == "Cena":
                s = main_systems[x][11] or ""
                try:
                    return float(s.split()[0])
                except:
                    return 0.0
            else:  # ID (default)
                try:
                    return int(main_systems[x][0])
                except:
                    return 0

        sorted_ids = sorted(main_systems.keys(), key=_key, reverse=reverse)
        new_ms: OrderedDict[Any, Any] = OrderedDict((k, main_systems[k]) for k in sorted_ids)
        main_systems.clear()
        main_systems.update(new_ms)

    def _apply_and_draw() -> None:
        nonlocal displayed_data
        _rebuild_groups()
        if search_var.get().strip() or all_expanded_systemy:
            for mid in main_systems:
                expanded_state[mid] = True
        _do_sort_main_systems(current_sort_reverse[0])
        active_sort_systemy["column"] = sort_var.get()
        active_sort_systemy["reverse"] = current_sort_reverse[0]
        displayed_data = _build_hierarchical_data()
        if _table[0] is not None:
            _table[0].set_data(displayed_data)
        _refresh_filter_btn()

    def _rebuild_fn() -> None:
        _apply_and_draw()

    def _refresh_filter_btn() -> None:
        active = sum(1 for v in active_filters_systemy.values() if v != 'Wszystkie')
        filter_btn.configure(text=f"Filtruj ({active})" if active else "Filtruj")

    # ── Kolorowanie wierszy ──────────────────────────────────────────────
    def _row_color(i: int, row: List[Any]) -> Any:  # type: ignore[return]
        symbol = row[0] if row else ""
        typ = row[3] if len(row) > 3 else ""
        status = row[11] if len(row) > 11 else ""
        if "Na sprzedaż" in status:
            return ("#660000" if dark_mode else "#ff6666", "#ffcccc" if dark_mode else "#ffffff")
        if "Nieposiadane" in status:
            return ("#3a3a3a" if dark_mode else "#d3d3d3", "#b0b0b0" if dark_mode else "#505050")
        if "Do kupienia" in status:
            return ("#4a1a4a" if dark_mode else "#e6b3ff", "#e6b3e6" if dark_mode else "#4a004a")
        if typ == "Podręcznik Główny":
            if symbol in ("[+]", "[-]"):
                return (
                    "#5d4e00" if dark_mode else "#ffa500",
                    "#ffd700" if dark_mode else "#4d2d00",
                )
            return ("#1a3d1a" if dark_mode else "#d4edda", "#90ee90" if dark_mode else "#155724")
        if typ == "Suplement":
            return ("#1a2a3d" if dark_mode else "#f0f8ff", "#87ceeb" if dark_mode else "#2c5282")
        if symbol == "   !":
            return ("#3d1a1a" if dark_mode else "#ffe6e6", "#ffb3b3" if dark_mode else "#8b0000")
        return None

    # ── Callbacki tabeli ─────────────────────────────────────────────────
    def _systemy_refresh(**_kw: Any) -> None:
        fill_systemy_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab))

    def _on_edit(_row_idx: int, row_data: List[Any]) -> None:
        sid = row_data[1] if len(row_data) > 1 else ""
        if sid:
            try:
                open_edit_system_dialog(tab, [str(sid)], refresh_callback=_systemy_refresh)
            except Exception as e:
                logger.exception("_on_edit: błąd otwierania edycji")
                messagebox.showerror(
                    "Błąd edycji", f"Nie można otworzyć okna edycji:\n{e}", parent=tab
                )

    def _on_cell_click(row_idx: int, col_idx: int, row_data: List[Any]) -> None:
        if col_idx != 0:
            return
        symbol = row_data[0] if row_data else ""
        if symbol not in ("[+]", "[-]"):
            return
        try:
            import time as _t

            _ts_click = _t.perf_counter()
            main_id = int(row_data[1])
            is_expanding = not expanded_state.get(main_id, False)
            expanded_state[main_id] = is_expanding
            if _table[0] is None:
                return

            if is_expanding:
                # Pobierz tylko wiersze suplementów dla tego systemu
                supp_rows: List[List[Any]] = []
                for sr in sorted(supplements.get(main_id, []), key=lambda x: x[1] or ""):
                    mn = main_systems[main_id][1] if main_id in main_systems else ""
                    supp_rows.append(
                        [
                            "   \u2192",
                            str(sr[0]),
                            "  " + (sr[1] or ""),
                            sr[2] or "",
                            mn,
                            sr[4] or "",
                            sr[5] or "",
                            "Tak" if sr[6] else "Nie",
                            "Tak" if sr[7] else "Nie",
                            sr[8] or "",
                            sr[9] or "",
                            sr[10] or "",
                            sr[11] or "",
                        ]
                    )
                _table[0].toggle_expand(str(main_id), True, supp_rows)
            else:
                _table[0].toggle_expand(str(main_id), False)

            _ts_done = _t.perf_counter()

            def _after_render(_ts: float = _ts_click, _td: float = _ts_done) -> None:
                logger.debug(
                    "[toggle_expand fast] expand=%s  elapsed=%.1f ms"
                    "  render=%.1f ms  TOTAL=%.1f ms",
                    is_expanding,
                    (_td - _ts) * 1000,
                    (_t.perf_counter() - _td) * 1000,
                    (_t.perf_counter() - _ts) * 1000,
                )

            tab.after(0, _after_render)
        except (ValueError, IndexError):
            pass

    def _on_sort(col_idx: int) -> None:
        col_map = {
            1: "ID",
            2: "Nazwa systemu",
            6: "Wydawca",
            10: "Język",
            11: "Status",
            12: "Cena",
        }
        sort_name = col_map.get(col_idx)
        if not sort_name:
            return
        if active_sort_systemy.get("column") == sort_name:
            rev = not active_sort_systemy.get("reverse", False)
        else:
            rev = False
        current_sort_reverse[0] = rev
        active_sort_systemy["column"] = sort_name
        active_sort_systemy["reverse"] = rev
        sort_var.set(sort_name)
        _do_sort_main_systems(rev)
        if _table[0] is not None:
            _table[0].set_data(_build_hierarchical_data())

    def _on_right_click(row_idx: int, row_data: List[Any], event: Any) -> None:
        symbol = row_data[0] if row_data else ""
        sid = row_data[1] if len(row_data) > 1 else ""
        sname = row_data[2] if len(row_data) > 2 else ""
        stype = row_data[3] if len(row_data) > 3 else ""
        clean_name = sname.split(" (")[0] if (" (" in sname and " supl.)" in sname) else sname

        def _edit() -> None:
            _on_edit(row_idx, row_data)

        def _delete() -> None:
            if not sid:
                return
            is_main = stype == "Podręcznik Główny"
            warn = f"Czy na pewno chcesz usunąć system: {clean_name}?"
            sid_int: Optional[int] = None
            try:
                sid_int = int(sid)
                if is_main and sid_int in supplements:
                    cnt = len(supplements[sid_int])
                    warn += (
                        f"\n\nUWAGA: Ten podręcznik główny ma {cnt} suplementów,"
                        " które również zostaną usunięte!"
                    )
            except ValueError:
                pass
            if messagebox.askyesno("Usuń system RPG", warn, parent=tab):
                try:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.row_factory = sqlite3.Row
                        conn.execute("PRAGMA foreign_keys = ON")
                        cur = conn.cursor()
                        if is_main and sid_int is not None:
                            cur.execute(
                                "DELETE FROM systemy_rpg WHERE system_glowny_id=?", (sid_int,)
                            )
                        cur.execute("DELETE FROM systemy_rpg WHERE id=?", (sid,))
                        conn.commit()
                    fill_systemy_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
                except sqlite3.Error as e:
                    messagebox.showerror(
                        "Błąd bazy danych", f"Nie udało się usunąć:\n{e}", parent=tab
                    )

        def _toggle() -> None:
            _on_cell_click(row_idx, 0, row_data)

        def _add_supp() -> None:
            if sid:
                dodaj_suplement_do_systemu(
                    tab.winfo_toplevel(), int(sid), clean_name, refresh_callback=_systemy_refresh
                )

        ctx = tk.Menu(tab, tearoff=0)
        ctx.add_command(label="Edytuj", command=_edit)
        if stype == "Podręcznik Główny":
            ctx.add_command(label="Dodaj suplement do podręcznika głównego", command=_add_supp)
            if symbol in ("[+]", "[-]"):
                ctx.add_command(label="Zwiń" if symbol == "[-]" else "Rozwiń", command=_toggle)
        ctx.add_separator()
        ctx.add_command(label="Usuń", command=_delete)
        ctx.tk_popup(event.x_root, event.y_root)
        ctx.grab_release()

    # ── Obliczanie szerokości kolumn ──────────────────────────────────────
    def _compute_widths(rows: List[List[Any]]) -> List[int]:
        if not rows:
            return [34, 44, 200, 130, 160, 160, 160, 60, 52, 100, 58, 200, 100]
        pad = 20

        def _w(ci: int, hdr: str, max_w: int, min_w: int = 60) -> int:
            v = max([_mf.measure(str(r[ci])) for r in rows if len(r) > ci and r[ci]] or [0])
            return min(max(max(v, _mf_bold.measure(hdr)) + pad, min_w), max_w)

        return [
            34,
            44,
            _w(2, "Nazwa systemu", 360, 100),
            _w(3, "Typ", 160, 80),
            _w(4, "System główny", 260, 80),
            _w(5, "Typ suplementu", 220, 80),
            _w(6, "Wydawca", 220, 80),
            _w(7, "Fizyczny", 70, 60),
            _w(8, "PDF", 52, 50),
            _w(9, "VTT", 120, 60),
            _w(10, "Język", 60, 50),
            _w(11, "Status", 200, 90),
            _w(12, "Cena", 130, 60),
        ]

    # ── Górny pasek ──────────────────────────────────────────────────────
    top_bar = tk.Frame(tab, bg=bg_top)
    top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
    tk.Label(top_bar, text="Sortuj:", bg=bg_top, fg=fg_top, font=FONT).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    sort_options = ["ID", "Nazwa systemu", "Wydawca", "Język", "Status", "Posiadanie", "Cena"]
    sort_var = tk.StringVar(value=active_sort_systemy.get("column", "ID"))
    ttk.Combobox(
        top_bar,
        textvariable=sort_var,
        values=sort_options,
        state="readonly",
        width=14,
    ).pack(side=tk.LEFT)

    def _sort_asc() -> None:
        current_sort_reverse[0] = False
        active_sort_systemy["column"] = sort_var.get()
        active_sort_systemy["reverse"] = False
        _do_sort_main_systems(False)
        if _table[0] is not None:
            _table[0].set_data(_build_hierarchical_data())

    def _sort_desc() -> None:
        current_sort_reverse[0] = True
        active_sort_systemy["column"] = sort_var.get()
        active_sort_systemy["reverse"] = True
        _do_sort_main_systems(True)
        if _table[0] is not None:
            _table[0].set_data(_build_hierarchical_data())

    ttk.Button(top_bar, text="Rosnąco", command=_sort_asc).pack(side=tk.LEFT, padx=4)
    ttk.Button(top_bar, text="Malejąco", command=_sort_desc).pack(side=tk.LEFT, padx=4)
    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
    tk.Label(top_bar, text="Filtruj:", bg=bg_top, fg=fg_top, font=FONT).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    filter_btn = ttk.Button(top_bar, text="Filtruj", command=lambda: _open_filter())
    filter_btn.pack(side=tk.LEFT, padx=4)

    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

    expand_var = tk.BooleanVar(value=all_expanded_systemy)

    def _on_toggle_expand_all() -> None:
        global all_expanded_systemy
        all_expanded_systemy = bool(expand_var.get())
        if all_expanded_systemy:
            for mid in main_systems:
                expanded_state[mid] = True
        else:
            expanded_state.clear()
        if _table[0] is not None:
            _table[0].set_data(_build_hierarchical_data())

    expand_switch = ctk.CTkSwitch(
        top_bar,
        text="Rozwiń wszystkie",
        variable=expand_var,
        command=_on_toggle_expand_all,
        onvalue=True,
        offvalue=False,
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(10)),
        width=50,
    )
    expand_switch.pack(side=tk.LEFT, padx=4)
    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
    tk.Label(top_bar, text="Wyszukaj:", bg=bg_top, fg=fg_top, font=FONT).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    search_entry = ttk.Entry(top_bar, textvariable=search_var, width=20)
    search_entry.pack(side=tk.LEFT, padx=4)
    search_var.trace_add('write', lambda *_: _apply_and_draw())  # type: ignore[misc]
    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
    cols_btn = ttk.Button(top_bar, text="Kolumny", command=lambda: _open_columns_dialog())
    cols_btn.pack(side=tk.LEFT, padx=4)

    # ── Tabela ───────────────────────────────────────────────────────────
    _rebuild_groups()
    if all_expanded_systemy:
        for mid in main_systems:
            expanded_state[mid] = True
    if active_sort_systemy.get("column", "ID") != "ID" or active_sort_systemy.get(
        "reverse", False
    ):
        _do_sort_main_systems(active_sort_systemy.get("reverse", False))
    initial_data = _build_hierarchical_data()

    def _compute_hidden_cols() -> List[int]:
        """Zwraca listę indeksów kolumn do ukrycia na podstawie active_visible_cols_systemy."""
        hidden: List[int] = []
        for idx, hdr in enumerate(_HEADERS):
            if hdr in _ALWAYS_VISIBLE_SYSTEMY:
                continue
            if not active_visible_cols_systemy.get(hdr, True):
                hidden.append(idx)
        return hidden

    _col_w = list(active_col_widths_systemy) if len(active_col_widths_systemy) == len(_HEADERS) else _compute_widths(initial_data)

    def _on_col_resize_systemy(widths: List[int]) -> None:
        active_col_widths_systemy.clear()
        active_col_widths_systemy.extend(widths)

    tbl = CTkDataTable(
        tab,
        headers=_HEADERS,
        col_widths=_col_w,
        data=[],
        edit_callback=_on_edit,
        id_col=1,
        row_color_fn=_row_color,
        center_cols=[1, 7, 8, 10],
        dark_mode=dark_mode,
        sort_callback=_on_sort,
        right_click_callback=_on_right_click,
        cell_click_callback=_on_cell_click,
        show_row_numbers=True,
        hidden_cols=_compute_hidden_cols(),
        resize_callback=_on_col_resize_systemy,
    )
    tbl.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    tab.rowconfigure(1, weight=1)
    tab.columnconfigure(0, weight=1)
    _table[0] = tbl

    tab._systemy_tab_cache = {  # type: ignore[attr-defined]
        'records_ref': records_ref,
        'rebuild_fn': _rebuild_fn,
        'table_ref': tbl,
        'dark_mode': dark_mode,
    }

    # ── Dialog filtrowania ────────────────────────────────────────────────
    def _open_filter() -> None:
        dlg = create_ctk_toplevel(tab)
        dlg.title("Filtruj systemy RPG")
        dlg.transient(tab.winfo_toplevel())
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 420, 380)

        mf = ctk.CTkFrame(dlg)
        mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        cur = records_ref[0]
        rows_cfg = [
            ("Typ:", 'typ', ['Wszystkie', 'Podręcznik Główny', 'Suplement']),
            ("Wydawca:", 'wydawca', ['Wszystkie'] + sorted({str(r[5]) for r in cur if r[5]})),
            (
                "Posiadanie:",
                'posiadanie',
                ['Wszystkie', 'Fizyczny', 'PDF', 'Fizyczny i PDF', 'Żadne'],
            ),
            ("Język:", 'jezyk', ['Wszystkie'] + sorted({str(r[9]) for r in cur if r[9]})),
            (
                "Status:",
                'status',
                [
                    'Wszystkie',
                    'Grane',
                    'Nie grane',
                    'W kolekcji',
                    'Na sprzedaż',
                    'Sprzedane',
                    'Nieposiadane',
                    'Do kupienia',
                ],
            ),
            ("Waluta:", 'waluta', ['Wszystkie', 'PLN', 'USD', 'EUR', 'GBP']),
        ]
        vars_: Dict[str, tk.StringVar] = {}
        for ri, (label, key, vals) in enumerate(rows_cfg):
            ctk.CTkLabel(mf, text=label).grid(row=ri, column=0, sticky="w", pady=8)
            v = tk.StringVar(value=active_filters_systemy.get(key, 'Wszystkie'))
            vars_[key] = v
            ttk.Combobox(mf, textvariable=v, values=vals, width=24, state="readonly").grid(
                row=ri, column=1, sticky="ew", pady=8, padx=(10, 0)
            )
        mf.columnconfigure(1, weight=1)

        bf = ctk.CTkFrame(mf, fg_color="transparent")
        bf.grid(row=len(rows_cfg), column=0, columnspan=2, pady=(20, 0))

        def _apply() -> None:
            for key, v in vars_.items():
                active_filters_systemy[key] = v.get()
            _apply_and_draw()
            dlg.destroy()

        def _reset() -> None:
            active_filters_systemy.clear()
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

    # ── Pierwsze wypełnienie ─────────────────────────────────────────────
    displayed_data = initial_data
    tbl.set_data(initial_data)
    _refresh_filter_btn()

    # ── Dialog wyboru kolumn ─────────────────────────────────────────────
    def _open_columns_dialog() -> None:
        """Otwiera dialog z checkboxami do wyboru widocznych kolumn tabeli systemów."""
        dlg = create_ctk_toplevel(tab)
        dlg.title("Widoczność kolumn – Systemy RPG")
        dlg.transient(tab.winfo_toplevel())

        # Kolumny z możliwością ukrycia (bez zawsze-widocznych)
        toggleable = [h for h in _HEADERS if h not in _ALWAYS_VISIBLE_SYSTEMY]
        dialog_h = 80 + len(toggleable) * 38
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 280, dialog_h)

        mf = ctk.CTkFrame(dlg)
        mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            mf,
            text="Wybierz widoczne kolumny:",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(10), weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

        vars_: Dict[str, tk.BooleanVar] = {}
        for col_name in toggleable:
            v = tk.BooleanVar(value=active_visible_cols_systemy.get(col_name, True))
            vars_[col_name] = v
            ctk.CTkCheckBox(mf, text=col_name, variable=v).pack(anchor="w", pady=2)

        bf = ctk.CTkFrame(mf, fg_color="transparent")
        bf.pack(pady=(14, 0))

        def _apply() -> None:
            for col_name, v in vars_.items():
                active_visible_cols_systemy[col_name] = bool(v.get())
            dlg.destroy()
            cache = getattr(tab, '_systemy_tab_cache', None)
            preloaded = cache['records_ref'][0] if cache else None
            # Wymuś pełny rebuild tabeli (nowe hidden_cols pomija szybka ścieżka)
            if hasattr(tab, '_systemy_tab_cache'):
                del tab._systemy_tab_cache  # type: ignore[attr-defined]
            fill_systemy_rpg_tab(tab, dark_mode=dark_mode, _preloaded_data=preloaded)

        def _reset() -> None:
            for v in vars_.values():
                v.set(True)

        ctk.CTkButton(
            bf, text="Zastosuj", command=_apply, fg_color="#2E7D32", hover_color="#1B5E20", width=90
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(
            bf, text="Zaznacz wszystkie", command=_reset, fg_color="#1976D2",
            hover_color="#1565C0", width=130,
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(
            bf, text="Anuluj", command=dlg.destroy, fg_color="#666666",
            hover_color="#555555", width=90,
        ).pack(side=tk.LEFT, padx=5)

        dlg.after(
            300, lambda: dlg.winfo_exists() and (dlg.deiconify(), dlg.lift(), dlg.focus_force())
        )


def usun_zaznaczony_system(
    tab: tk.Frame, refresh_callback: Optional[Callable[..., None]] = None
) -> None:
    """Usuwa zaznaczony system RPG – deleguje do menu kontekstowego tabeli."""
    cache = getattr(tab, '_systemy_tab_cache', None)
    tbl: Optional[CTkDataTable] = cache.get('table_ref') if cache else None
    if tbl is None:
        messagebox.showerror("Błąd", "Nie znaleziono tabeli systemów RPG.", parent=tab)  # type: ignore
        return
    row_data = tbl.get_selected()
    if row_data is None:
        messagebox.showinfo("Brak wyboru", "Zaznacz system do usunięcia w tabeli.", parent=tab)  # type: ignore
        return
    system_id = row_data[1] if len(row_data) > 1 else None
    system_name = row_data[2] if len(row_data) > 2 else ""
    if system_name and " (" in system_name and " supl.)" in system_name:
        system_name = system_name.split(" (")[0]
    if not system_id:
        return
    if messagebox.askyesno("Usuń system RPG", f"Czy na pewno chcesz usunąć system: {system_name}?", parent=tab):  # type: ignore
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute("DELETE FROM systemy_rpg WHERE id=?", (system_id,))
            conn.commit()
        fill_systemy_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(tab))


def open_edit_system_dialog(
    parent: tk.Widget,
    values: Sequence[Any],
    refresh_callback: Optional[Callable[..., None]] = None,
) -> None:
    """Otwiera okno edycji systemu RPG"""

    # Najpierw pobierz dane z bazy, aby sprawdzić czy VTT jest zaznaczone
    system_id = values[0]
    logger.info("=== open_edit_system_dialog: START === system_id=%r", system_id)
    logger.debug("open_edit_system_dialog: przekazane values=%r", list(values))

    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute(
                """
                SELECT id, nazwa, typ, system_glowny_id, typ_suplementu, 
                       wydawca_id, fizyczny, pdf, vtt, jezyk, status_gra, status_kolekcja,
                       cena_zakupu, waluta_zakupu, cena_sprzedazy, waluta_sprzedazy,
                       system_glowny_nazwa_custom
                FROM systemy_rpg WHERE id = ?
            """,
                (system_id,),
            )
            system_data = c.fetchone()
    except Exception as _db_exc:
        logger.exception("open_edit_system_dialog: błąd zapytania do bazy")
        messagebox.showerror(
            "Błąd bazy danych", f"Nie można odczytać danych systemu:\n{_db_exc}", parent=parent
        )
        return

    if not system_data:
        logger.error("open_edit_system_dialog: brak rekordu w bazie dla id=%r", system_id)
        messagebox.showerror("Błąd", "Nie znaleziono systemu w bazie danych.", parent=parent)
        return

    logger.debug(
        "open_edit_system_dialog: dane z bazy: id=%r, nazwa=%r, typ=%r, "
        "system_glowny_id=%r, typ_suplementu=%r, system_glowny_nazwa_custom=%r, "
        "kolumn=%d",
        system_data[0],
        system_data[1],
        system_data[2],
        system_data[3],
        system_data[4],
        system_data[16] if len(system_data) > 16 else "<brak kolumny>",
        len(system_data),
    )

    # Sprawdź czy VTT jest zaznaczone
    has_vtt = bool(system_data[8])  # vtt
    is_suplement = system_data[2] == "Suplement"  # typ
    logger.info(
        "open_edit_system_dialog: is_suplement=%r, has_vtt=%r, system_glowny_id=%r",
        is_suplement,
        has_vtt,
        system_data[3],
    )

    dialog = create_ctk_toplevel(parent)  # type: ignore
    dialog.withdraw()  # ukryj podczas budowania – eliminuje czarną ramkę
    dialog.title("Edytuj system RPG")
    dialog.transient(parent)  # type: ignore
    dialog.resizable(True, True)

    # Ustaw geometrię na podstawie tego czy VTT jest zaznaczone i czy to suplement
    if has_vtt and is_suplement:
        width, height = 1100, 850
    elif has_vtt:
        width, height = 1100, 680
    elif is_suplement:
        width, height = 950, 720
    else:
        width, height = 950, 560

    apply_safe_geometry(dialog, parent, width, height)

    # Główny frame z paddingiem (scrollowalny dla małych ekranów / wysokiego DPI)
    main_frame = ctk.CTkScrollableFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.columnconfigure(1, weight=1)
    main_frame.columnconfigure(3, weight=1)

    publishers = get_all_publishers()

    # ID systemu (tylko do odczytu)
    ctk.CTkLabel(main_frame, text=f"ID systemu: {system_data[0]}").grid(
        row=0, column=0, columnspan=2, pady=(0, 8), sticky="w"
    )

    # Nazwa systemu (obowiązkowe)
    ctk.CTkLabel(main_frame, text="Nazwa systemu *").grid(
        row=1, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    nazwa_entry = ctk.CTkEntry(main_frame, placeholder_text="Wprowadź nazwę systemu")
    nazwa_entry.grid(row=1, column=1, pady=8, sticky="ew")
    nazwa_entry.insert(0, system_data[1] or "")
    dialog.after(100, lambda: nazwa_entry.focus_set() if nazwa_entry.winfo_exists() else None)

    # Typ (Podręcznik Główny / Suplement)
    ctk.CTkLabel(main_frame, text="Typ *").grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")
    typ_var = tk.StringVar(value=system_data[2] or "Podręcznik Główny")
    typ_combo = ctk.CTkComboBox(
        main_frame, variable=typ_var, values=["Podręcznik Główny", "Suplement"], state="readonly"
    )
    typ_combo.grid(row=2, column=1, pady=8, sticky="ew")

    # System główny (dla suplementów) - opcjonalne
    system_glowny_label = ctk.CTkLabel(main_frame, text="System główny (opcjonalnie)")
    system_glowny_label.grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")
    system_glowny_var = tk.StringVar()
    system_glowny_combo = ctk.CTkComboBox(main_frame, variable=system_glowny_var, state="readonly")
    system_glowny_combo.grid(row=3, column=1, pady=8, sticky="ew")

    # Niestandardowa nazwa systemu głównego (dla suplementów bez systemu w kolekcji)
    system_glowny_custom_label = ctk.CTkLabel(main_frame, text="lub wpisz nazwę:")
    system_glowny_custom_label.grid(row=3, column=2, pady=8, padx=(20, 10), sticky="w")
    system_glowny_custom_entry = ctk.CTkEntry(
        main_frame, placeholder_text="Nazwa systemu spoza kolekcji", width=200
    )
    system_glowny_custom_entry.grid(row=3, column=3, pady=8, sticky="ew")
    if system_data[16]:  # system_glowny_nazwa_custom
        system_glowny_custom_entry.insert(0, system_data[16] or "")

    # Typ suplementu - obowiązkowe dla suplementów (wielokrotny wybór)
    typ_suplementu_label = ctk.CTkLabel(main_frame, text="Typ suplementu *")
    typ_suplementu_label.grid(row=4, column=0, pady=8, padx=(0, 10), sticky="nw")
    typ_suplementu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")

    # Słownik do przechowywania zmiennych checkboxów
    typ_suplementu_vars = {}
    typ_suplementu_checkboxes = {}
    typy_suplementow = [
        "Scenariusz/kampania",
        "Rozwinięcie zasad",
        "Moduł",
        "Lorebook/Sourcebook",
        "Bestiariusz",
        "Starter/Zestaw Startowy",
    ]

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
    ctk.CTkLabel(main_frame, text="Wydawca").grid(
        row=5, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    wydawca_var = tk.StringVar()
    wydawca_combo = ctk.CTkComboBox(main_frame, variable=wydawca_var, state="readonly")

    def refresh_publishers_on_click(event: Any = None) -> None:
        """Odświeża listę wydawców z bazy przy każdym kliknięciu w combobox"""
        nonlocal publishers
        current_value = wydawca_var.get()
        publishers = get_all_publishers()
        if publishers:
            wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
            wydawca_combo.configure(values=wydawca_values)
            if current_value and current_value in wydawca_values:
                wydawca_var.set(current_value)
        else:
            wydawca_combo.configure(values=[])

    # Inicjalne załadowanie listy i ustawienie obecnego wydawcy
    if publishers:
        wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
        wydawca_combo.configure(values=wydawca_values)
        # Ustaw obecnie wybranego wydawcę
        if system_data[5]:  # wydawca_id
            for pub in publishers:
                if pub[0] == system_data[5]:
                    wydawca_var.set(f"{pub[0]} - {pub[1]}")
                    break

    # Odśwież listę wydawców przy każdym kliknięciu w combobox
    wydawca_combo.bind("<Button-1>", refresh_publishers_on_click)
    wydawca_combo.grid(row=5, column=1, pady=8, sticky="ew")

    # Posiadanie
    ctk.CTkLabel(main_frame, text="Posiadanie").grid(
        row=6, column=0, pady=8, padx=(0, 10), sticky="nw"
    )
    posiadanie_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    posiadanie_frame.grid(row=6, column=1, pady=8, sticky="w", columnspan=3)
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
        "Telespire",
    ]

    # Frame dla wyboru platform VTT w prawej kolumnie (początkowo ukryty)
    vtt_selection_frame = ctk.CTkFrame(posiadanie_frame, fg_color="transparent")
    vtt_selection_frame.grid(row=0, column=1, rowspan=3, sticky="nsw", padx=(20, 0))

    # Label dla platform VTT
    vtt_label = ctk.CTkLabel(
        vtt_selection_frame, text="Platformy VTT:", font=("Segoe UI", scale_font_size(10))
    )
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
        if not dialog.winfo_exists():
            return
        parent.update_idletasks()

        is_vtt = vtt_var.get()
        is_suplement = typ_var.get() == "Suplement"

        if is_vtt and is_suplement:
            width, height = 1100, 880
        elif is_vtt:
            width, height = 1100, 680
        elif is_suplement:
            width, height = 950, 750
        else:
            width, height = 950, 590

        geo = clamp_geometry(dialog, parent, width, height)
        dialog.geometry(geo)

    def on_vtt_change(*args: Any) -> None:
        """Obsługuje zmianę checkboxa VTT - pokazuje/ukrywa listę platform"""
        if vtt_var.get():
            vtt_selection_frame.grid()
        else:
            vtt_selection_frame.grid_remove()
        update_dialog_size()

    vtt_var.trace_add('write', on_vtt_change)

    # Język
    ctk.CTkLabel(main_frame, text="Język").grid(row=7, column=0, pady=8, padx=(0, 10), sticky="w")
    jezyk_var = tk.StringVar(value=system_data[9] or "PL")
    jezyk_combo = ctk.CTkComboBox(
        main_frame,
        variable=jezyk_var,
        values=["PL", "ENG", "DE", "FR", "ES", "IT"],
        state="readonly",
        width=100,
    )
    jezyk_combo.grid(row=7, column=1, pady=8, sticky="w")

    # Status gry
    ctk.CTkLabel(main_frame, text="Status gry").grid(
        row=8, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_gra_var = tk.StringVar(value=system_data[10] or "Nie grane")
    status_gra_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_gra_var,
        values=["Grane", "Nie grane"],
        state="readonly",
        width=150,
    )
    status_gra_combo.grid(row=8, column=1, pady=8, sticky="w")

    # Status kolekcji
    ctk.CTkLabel(main_frame, text="Status kolekcji").grid(
        row=9, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_kolekcja_var = tk.StringVar(value=system_data[11] or "W kolekcji")
    status_kolekcja_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_kolekcja_var,
        values=["W kolekcji", "Na sprzedaż", "Sprzedane", "Nieposiadane", "Do kupienia"],
        state="readonly",
        width=150,
    )
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
    waluta_zakupu_combo = ctk.CTkComboBox(
        cena_zakupu_frame,
        variable=waluta_zakupu_var,
        values=["PLN", "USD", "EUR", "GBP"],
        state="readonly",
        width=70,
    )
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
    waluta_sprzedazy_combo = ctk.CTkComboBox(
        cena_sprzedazy_frame,
        variable=waluta_sprzedazy_var,
        values=["PLN", "USD", "EUR", "GBP"],
        state="readonly",
        width=70,
    )
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

    # Flaga inicjalizacji - zapobiega wywołaniu update_dialog_size() podczas budowania dialogu
    _initializing: List[bool] = [True]

    def on_typ_change(*args: Any) -> None:
        """Obsługuje zmianę typu (Podręcznik Główny/Suplement)"""
        current_typ = typ_var.get()
        logger.debug(
            "on_typ_change: wywołano, typ=%r, _initializing=%r", current_typ, _initializing[0]
        )
        try:
            if current_typ == "Suplement":
                # Pokaż pola dla suplementu
                system_glowny_label.grid()
                system_glowny_combo.grid()
                system_glowny_custom_label.grid(row=3, column=2, pady=8, padx=(20, 10), sticky="w")
                system_glowny_custom_entry.grid(row=3, column=3, pady=8, sticky="ew")
                typ_suplementu_label.grid(row=4, column=0, pady=8, padx=(0, 10), sticky="nw")
                typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")
                # Załaduj systemy główne
                main_systems_list = get_main_systems()
                logger.debug(
                    "on_typ_change: pobrano %d systemów głównych, system_glowny_id=%r",
                    len(main_systems_list) if main_systems_list else 0,
                    system_data[3],
                )
                if main_systems_list:
                    system_values = [f"{sys[0]} - {sys[1]}" for sys in main_systems_list]
                    system_glowny_combo.configure(values=system_values)
                    # Ustaw obecnie wybrany system główny lub jawnie wyczyść
                    matched = False
                    if system_data[3]:  # system_glowny_id
                        for sys in main_systems_list:
                            if sys[0] == system_data[3]:
                                system_glowny_var.set(f"{sys[0]} - {sys[1]}")
                                matched = True
                                logger.debug(
                                    "on_typ_change: dopasowano system główny id=%r", sys[0]
                                )
                                break
                    if not matched:
                        # Osierocony suplement - brak rodzica, wyczyść combo
                        system_glowny_var.set("")
                        logger.info(
                            "on_typ_change: suplement id=%r nie ma dopasowanego systemu głównego "
                            "(system_glowny_id=%r) – ustawiam pusty combo",
                            system_data[0],
                            system_data[3],
                        )
                else:
                    # Brak podręczników głównych w bazie
                    system_glowny_combo.configure(values=[])
                    system_glowny_var.set("")
                    logger.warning(
                        "on_typ_change: brak podręczników głównych w bazie dla suplementu id=%r",
                        system_data[0],
                    )
            else:
                # Ukryj pola dla suplementu
                system_glowny_label.grid_remove()
                system_glowny_combo.grid_remove()
                system_glowny_custom_label.grid_remove()
                system_glowny_custom_entry.grid_remove()
                typ_suplementu_label.grid_remove()
                typ_suplementu_frame.grid_remove()
        except Exception as _exc:
            logger.exception(
                "on_typ_change: nieoczekiwany wyjątek dla system_id=%r, typ=%r",
                system_data[0] if system_data else '?',
                current_typ,
            )
            raise

        if not _initializing[0]:
            update_dialog_size()

    typ_var.trace_add('write', on_typ_change)
    on_typ_change()  # Ustaw początkowy stan bez resize
    _initializing[0] = False
    dialog.after(50, update_dialog_size)  # Opóźniony resize - po pełnej inicjalizacji CTkToplevel

    # Wymuszenie widoczności okna po zakończeniu cyklu withdraw/deiconify CTkToplevel.
    # CTkToplevel wywołuje wewnętrznie withdraw() a potem after(~200ms, deiconify).
    # Dla osieroconych suplementów (system_glowny_id=None) configure() na CTkComboBox
    # może sprowokować wcześniejsze przetwarzanie kolejki zdarzeń Tk, przez co okno
    # zostaje ukryte zanim CTkToplevel zrobi deiconify. 300 ms > 200 ms = bezpieczna wartość.
    def _ensure_visible() -> None:
        if dialog.winfo_exists():
            dialog.deiconify()
            dialog.lift()
            dialog.focus_force()

    dialog.after(300, _ensure_visible)

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
        system_glowny_custom = None

        if typ == "Suplement":
            # Zbierz wybrane typy suplementu
            wybrane_typy = [typ for typ, var in typ_suplementu_vars.items() if var.get()]  # type: ignore

            if not wybrane_typy:
                messagebox.showerror(
                    "Błąd",
                    "Dla suplementu musisz wybrać przynajmniej jeden typ suplementu.",
                    parent=dialog,
                )
                return

            # Połącz wybrane typy separatorem
            typ_suplementu = " | ".join(wybrane_typy)  # type: ignore

            # System główny jest opcjonalny - może być pusty dla osieroconych suplementów
            if system_glowny_var.get():
                system_glowny_id = int(system_glowny_var.get().split(' - ')[0])

            # Pobierz niestandardową nazwę systemu głównego
            system_glowny_custom = system_glowny_custom_entry.get().strip() or None

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
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute(
                """
                UPDATE systemy_rpg 
                SET nazwa=?, typ=?, system_glowny_id=?, typ_suplementu=?, 
                    wydawca_id=?, fizyczny=?, pdf=?, vtt=?, jezyk=?,
                    status_gra=?, status_kolekcja=?,
                    cena_zakupu=?, waluta_zakupu=?, cena_sprzedazy=?,
                    waluta_sprzedazy=?, system_glowny_nazwa_custom=?
                WHERE id=?
            """,
                (
                    nazwa,
                    typ,
                    system_glowny_id,
                    typ_suplementu,
                    wydawca_id,
                    int(fizyczny_var.get()),
                    int(pdf_var.get()),
                    vtt_str,
                    jezyk if jezyk else None,
                    status_gra_var.get(),
                    status_kolekcja_var.get(),
                    cena_zakupu,
                    waluta_zakupu,
                    cena_sprzedazy,
                    waluta_sprzedazy,
                    system_glowny_custom,
                    system_data[0],
                ),
            )
            conn.commit()

        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))
        dialog.destroy()

    def on_cancel() -> None:
        """Anuluje edycję"""
        dialog.destroy()

    # Przyciski
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.grid(row=10, column=0, columnspan=4, pady=15, sticky="ew")
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)

    btn_save = ctk.CTkButton(
        button_frame, text="Zapisz", command=on_save, fg_color="#2E7D32", hover_color="#1B5E20"
    )
    btn_save.grid(row=0, column=0, padx=5, sticky="e")

    btn_cancel = ctk.CTkButton(
        button_frame, text="Anuluj", command=on_cancel, fg_color="#666666", hover_color="#555555"
    )
    btn_cancel.grid(row=0, column=1, padx=5, sticky="w")

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.after(0, dialog.deiconify)  # pokaż gdy wszystkie widgety są gotowe


def show_supplements_window(parent: tk.Widget, system_id: str, system_name: str) -> None:
    """Wyświetla okno z wszystkimi suplementami dla danego podręcznika głównego"""
    dialog = tk.Toplevel(parent)
    dialog.title(f"Suplementy do: {system_name}")
    dialog.transient(parent.winfo_toplevel())
    dialog.resizable(True, True)

    # Zastosuj tryb ciemny jeśli aktywny
    root = parent.winfo_toplevel()
    if hasattr(root, 'dark_mode') and getattr(root, 'dark_mode', False):
        apply_dark_theme_to_dialog(dialog)

    # Ustawienia okna (bezpieczna geometria)
    apply_safe_geometry(dialog, parent, 800, 600)

    # Pobierz suplementy z bazy
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        c = conn.cursor()
        c.execute(
            """
            SELECT s.id, s.nazwa, s.typ_suplementu, s.wydawca_id,
                   s.fizyczny, s.pdf, s.jezyk
            FROM systemy_rpg s
            WHERE s.system_glowny_id = ? AND s.typ = 'Suplement'
            ORDER BY s.nazwa
        """,
            (system_id,),
        )
        supplements_base = c.fetchall()

    # Pobierz nazwy wydawców z oddzielnej bazy
    supplements = []
    for supp in supplements_base:
        try:
            with sqlite3.connect(get_db_path("wydawcy.db")) as wydawcy_conn:
                wydawcy_conn.row_factory = sqlite3.Row
                wydawcy_conn.execute("PRAGMA foreign_keys = ON")
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
        tk.Label(
            dialog,
            text=f"Brak suplementów dla systemu: {system_name}",
            font=('Segoe UI', scale_font_size(12)),
            pady=20,
        ).pack()
    else:
        # Nagłówek
        header_frame = tk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(
            header_frame,
            text=f"Znaleziono {len(supplements)} suplementów:",  # type: ignore
            font=('Segoe UI', scale_font_size(12), 'bold'),
        ).pack(side=tk.LEFT)

        # Tabela z suplementami
        headers = [
            "ID",
            "Nazwa suplementu",
            "Typ suplementu",
            "Wydawca",
            "Fizyczny",
            "PDF",
            "Język",
        ]
        data: List[List[Any]] = []  # type: ignore
        for supp in supplements:  # type: ignore
            row: List[Any] = [  # type: ignore
                str(supp[0]),  # type: ignore
                supp[1] or "",
                supp[2] or "",
                supp[3] or "",
                "Tak" if supp[4] else "Nie",
                "Tak" if supp[5] else "Nie",
                supp[6] or "",
            ]
            data.append(row)  # type: ignore

        sheet = tksheet.Sheet(
            dialog,
            data=data,  # type: ignore
            headers=headers,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
            width=750,
            height=450,
        )

        # Automatyczne dopasowanie szerokości kolumn
        for col in range(len(headers)):
            max_content = max([len(str(row[col])) for row in data] + [len(headers[col])])  # type: ignore
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


def dodaj_suplement_do_systemu(
    parent: Any,
    system_glowny_id: int,
    system_glowny_nazwa: str,
    refresh_callback: Optional[Callable[..., None]] = None,
) -> None:
    """Otwiera okno dodawania suplementu do określonego podręcznika głównego"""

    init_db()
    reserved_id = get_first_free_id()
    publishers = get_all_publishers()

    dialog = create_ctk_toplevel(parent)
    dialog.title(f"Dodaj suplement do: {system_glowny_nazwa}")
    dialog.transient(parent)
    dialog.resizable(True, True)

    apply_safe_geometry(dialog, parent, 700, 680)

    # Główny frame z paddingiem (scrollowalny dla małych ekranów / wysokiego DPI)
    main_frame = ctk.CTkScrollableFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.columnconfigure(1, weight=1)

    # ID systemu
    ctk.CTkLabel(
        main_frame, text=f"ID systemu: {reserved_id}", font=("Segoe UI", scale_font_size(12))
    ).grid(row=0, column=0, columnspan=2, pady=(0, 8), sticky="w")

    # Nazwa systemu (obowiązkowe)
    ctk.CTkLabel(main_frame, text="Nazwa suplementu *").grid(
        row=1, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    nazwa_entry = ctk.CTkEntry(main_frame, placeholder_text="Wprowadź nazwę suplementu")
    nazwa_entry.grid(row=1, column=1, pady=8, sticky="ew")
    dialog.after(100, lambda: nazwa_entry.focus_set() if nazwa_entry.winfo_exists() else None)

    # Typ (zawsze Suplement)
    ctk.CTkLabel(main_frame, text="Typ *").grid(row=2, column=0, pady=8, padx=(0, 10), sticky="w")
    typ_var = tk.StringVar(value="Suplement")
    typ_combo = ctk.CTkComboBox(
        main_frame, variable=typ_var, values=["Suplement"], state="readonly"
    )
    typ_combo.grid(row=2, column=1, pady=8, sticky="ew")

    # System główny (predefiniowany)
    ctk.CTkLabel(main_frame, text="System główny *").grid(
        row=3, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    system_glowny_var = tk.StringVar(value=f"{system_glowny_id} - {system_glowny_nazwa}")
    system_glowny_entry = ctk.CTkEntry(
        main_frame, textvariable=system_glowny_var, state="readonly"
    )
    system_glowny_entry.grid(row=3, column=1, pady=8, sticky="ew")

    # Typ suplementu (obowiązkowe) - wielokrotny wybór
    ctk.CTkLabel(main_frame, text="Typ suplementu *").grid(
        row=4, column=0, pady=8, padx=(0, 10), sticky="nw"
    )
    typ_suplementu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")

    # Słownik do przechowywania zmiennych checkboxów
    typ_suplementu_vars = {}
    typ_suplementu_checkboxes = {}
    typy_suplementow = [
        "Scenariusz/kampania",
        "Rozwinięcie zasad",
        "Moduł",
        "Lorebook/Sourcebook",
        "Bestiariusz",
        "Starter/Zestaw Startowy",
    ]

    for i, typ in enumerate(typy_suplementow):
        var = tk.BooleanVar()
        typ_suplementu_vars[typ] = var
        checkbox = ctk.CTkCheckBox(typ_suplementu_frame, text=typ, variable=var, width=280)
        checkbox.grid(row=i, column=0, sticky="w", pady=2)
        typ_suplementu_checkboxes[typ] = checkbox

    # Wydawca
    ctk.CTkLabel(main_frame, text="Wydawca").grid(
        row=5, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    wydawca_var = tk.StringVar()
    wydawca_combo = ctk.CTkComboBox(main_frame, variable=wydawca_var, state="readonly")

    def refresh_publishers_on_click(event: Any = None) -> None:
        """Odświeża listę wydawców z bazy przy każdym kliknięciu w combobox"""
        nonlocal publishers
        current_value = wydawca_var.get()
        publishers = get_all_publishers()
        if publishers:
            wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
            wydawca_combo.configure(values=wydawca_values)
            if current_value and current_value in wydawca_values:
                wydawca_var.set(current_value)
        else:
            wydawca_combo.configure(values=[])

    # Inicjalne załadowanie listy
    if publishers:
        wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
        wydawca_combo.configure(values=wydawca_values)

    # Odśwież listę wydawców przy każdym kliknięciu w combobox
    wydawca_combo.bind("<Button-1>", refresh_publishers_on_click)
    wydawca_combo.grid(row=5, column=1, pady=8, sticky="ew")

    # Posiadanie
    ctk.CTkLabel(main_frame, text="Posiadanie").grid(
        row=6, column=0, pady=8, padx=(0, 10), sticky="nw"
    )
    posiadanie_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    posiadanie_frame.grid(row=6, column=1, pady=8, sticky="w")
    fizyczny_var = tk.BooleanVar()
    pdf_var = tk.BooleanVar()
    fizyczny_check = ctk.CTkCheckBox(posiadanie_frame, text="Fizyczny", variable=fizyczny_var)
    fizyczny_check.grid(row=0, column=0, sticky="w", pady=2)
    pdf_check = ctk.CTkCheckBox(posiadanie_frame, text="PDF", variable=pdf_var)
    pdf_check.grid(row=1, column=0, sticky="w", pady=2)

    # Język
    ctk.CTkLabel(main_frame, text="Język").grid(row=7, column=0, pady=8, padx=(0, 10), sticky="w")
    jezyk_var = tk.StringVar(value="PL")
    jezyk_combo = ctk.CTkComboBox(
        main_frame,
        variable=jezyk_var,
        values=["PL", "ENG", "DE", "FR", "ES", "IT"],
        state="readonly",
        width=100,
    )
    jezyk_combo.grid(row=7, column=1, pady=8, sticky="w")

    # Status gry
    ctk.CTkLabel(main_frame, text="Status gry").grid(
        row=8, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_gra_var = tk.StringVar(value="Nie grane")
    status_gra_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_gra_var,
        values=["Grane", "Nie grane"],
        state="readonly",
        width=150,
    )
    status_gra_combo.grid(row=8, column=1, pady=8, sticky="w")

    # Status kolekcji
    ctk.CTkLabel(main_frame, text="Status kolekcji").grid(
        row=9, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_kolekcja_var = tk.StringVar(value="W kolekcji")
    status_kolekcja_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_kolekcja_var,
        values=["W kolekcji", "Na sprzedaż", "Sprzedane", "Nieposiadane", "Do kupienia"],
        state="readonly",
        width=150,
    )
    status_kolekcja_combo.grid(row=9, column=1, pady=8, sticky="w")

    # Cena zakupu (dla statusu "W kolekcji")
    cena_zakupu_label = ctk.CTkLabel(main_frame, text="Cena zakupu")
    cena_zakupu_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")

    cena_zakupu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_zakupu_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")

    cena_zakupu_entry = ctk.CTkEntry(cena_zakupu_frame, width=100)
    cena_zakupu_entry.pack(side=tk.LEFT, padx=(0, 5))

    waluta_zakupu_var = tk.StringVar(value="PLN")
    waluta_zakupu_combo = ctk.CTkComboBox(
        cena_zakupu_frame,
        variable=waluta_zakupu_var,
        values=["PLN", "USD", "EUR", "GBP"],
        state="readonly",
        width=70,
    )
    waluta_zakupu_combo.pack(side=tk.LEFT)

    # Cena sprzedaży (dla statusu "Sprzedane")
    cena_sprzedazy_label = ctk.CTkLabel(main_frame, text="Cena sprzedaży")
    cena_sprzedazy_label.grid(row=9, column=2, pady=8, padx=(20, 5), sticky="w")

    cena_sprzedazy_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_sprzedazy_frame.grid(row=9, column=3, pady=8, padx=10, sticky="w")

    cena_sprzedazy_entry = ctk.CTkEntry(cena_sprzedazy_frame, width=100)
    cena_sprzedazy_entry.pack(side=tk.LEFT, padx=(0, 5))

    waluta_sprzedazy_var = tk.StringVar(value="PLN")
    waluta_sprzedazy_combo = ctk.CTkComboBox(
        cena_sprzedazy_frame,
        variable=waluta_sprzedazy_var,
        values=["PLN", "USD", "EUR", "GBP"],
        state="readonly",
        width=70,
    )
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
            messagebox.showerror("Błąd", "Nazwa suplementu jest wymagana.", parent=dialog)  # type: ignore
            return

        # Zbierz wybrane typy suplementu
        wybrane_typy = [typ for typ, var in typ_suplementu_vars.items() if var.get()]  # type: ignore

        if not wybrane_typy:
            messagebox.showerror("Błąd", "Musisz wybrać przynajmniej jeden typ suplementu.", parent=dialog)  # type: ignore
            return

        # Połącz wybrane typy separatorem
        typ_suplementu = " | ".join(wybrane_typy)  # type: ignore

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
                    messagebox.showerror("Błąd", "Cena zakupu musi być liczbą.", parent=dialog)  # type: ignore
                    return
        elif status_kolekcja_var.get() == "Sprzedane":
            cena_str = cena_sprzedazy_entry.get().strip().replace(',', '.')
            if cena_str:
                try:
                    cena_sprzedazy = float(cena_str)
                    waluta_sprzedazy = waluta_sprzedazy_var.get()
                except ValueError:
                    messagebox.showerror("Błąd", "Cena sprzedaży musi być liczbą.", parent=dialog)  # type: ignore
                    return

        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO systemy_rpg (id, nazwa, typ, system_glowny_id, typ_suplementu, 
                                       wydawca_id, fizyczny, pdf, jezyk,
                                       status_gra, status_kolekcja,
                                       cena_zakupu, waluta_zakupu, cena_sprzedazy,
                                       waluta_sprzedazy) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    reserved_id,
                    nazwa,
                    "Suplement",
                    system_glowny_id,
                    typ_suplementu,
                    wydawca_id,
                    int(fizyczny_var.get()),
                    int(pdf_var.get()),
                    jezyk if jezyk else None,
                    status_gra_var.get(),
                    status_kolekcja_var.get(),
                    cena_zakupu,
                    waluta_zakupu,
                    cena_sprzedazy,
                    waluta_sprzedazy,
                ),
            )
            conn.commit()

        messagebox.showinfo("Sukces", f"Suplement '{nazwa}' został dodany do systemu '{system_glowny_nazwa}'.", parent=dialog)  # type: ignore

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

    btn_ok = ctk.CTkButton(
        button_frame,
        text="Dodaj suplement",
        command=on_ok,
        fg_color="#2E7D32",
        hover_color="#1B5E20",
    )
    btn_ok.grid(row=0, column=0, padx=5, sticky="e")

    btn_cancel = ctk.CTkButton(
        button_frame, text="Anuluj", command=on_cancel, fg_color="#666666", hover_color="#555555"
    )
    btn_cancel.grid(row=0, column=1, padx=5, sticky="w")

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
