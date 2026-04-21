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
# Ukrywanie wierszy "System" gdy "Rozwiń wszystkie" jest włączone
hide_systems_systemy: bool = False
# Ukrywanie wierszy "System" gdy "Rozwiń wszystkie" jest włączone
hide_systems_systemy: bool = False
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

# Kolejność kolumn w tabeli systemów (tylko przestawiane, bez zawsze-widocznych ""/ID)
active_col_order_systemy: List[str] = [
    "Nazwa systemu", "Typ", "System główny", "Typ suplementu",
    "Wydawca", "Fizyczny", "PDF", "VTT", "Język", "Status", "Cena",
]

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

        # ── Nowy poziom hierarchii: systemy_gry ──────────────────────────
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS systemy_gry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nazwa TEXT NOT NULL,
                wydawca_id INTEGER,
                jezyk TEXT,
                notatki TEXT
            )
        """
        )

        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN system_gry_id INTEGER REFERENCES systemy_gry(id)")
        except sqlite3.OperationalError:
            pass  # Kolumna już istnieje

        # Migracja cen per forma posiadania (v0.4.x)
        # cena_zakupu → zostaje jako backup; cena_fiz kopiuje jej wartość
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN cena_fiz REAL")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN cena_pdf REAL")
        except sqlite3.OperationalError:
            pass
        try:
            c.execute("ALTER TABLE systemy_rpg ADD COLUMN cena_vtt REAL")
        except sqlite3.OperationalError:
            pass
        # Jednorazowe kopiowanie: cena_zakupu → cena_fiz (tylko gdy cena_fiz jeszcze NULL)
        c.execute(
            "UPDATE systemy_rpg SET cena_fiz = cena_zakupu "
            "WHERE cena_fiz IS NULL AND cena_zakupu IS NOT NULL"
        )

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
                   s.system_glowny_nazwa_custom,
                   s.system_gry_id,
                   s.cena_fiz, s.cena_pdf, s.cena_vtt
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

        # Formatuj cenę: pokaż niepuste ceny per forma z etykietą (fiz/pdf/vtt)
        # + cena sprzedaży gdy status == Sprzedane
        cena_fiz_val = system[18] if len(system) > 18 else None
        cena_pdf_val = system[19] if len(system) > 19 else None
        cena_vtt_val = system[20] if len(system) > 20 else None
        waluta = system[13] if system[13] else "PLN"  # wspólna waluta z waluta_zakupu

        cena_parts: List[str] = []
        if status_kolekcja == "Sprzedane":
            if system[14]:  # cena_sprzedazy
                w_sp = system[15] if system[15] else "PLN"
                cena_parts.append(f"sprzedaż: {system[14]:.2f} {w_sp}")
        else:
            if cena_fiz_val:
                cena_parts.append(f"fiz: {cena_fiz_val:.2f} {waluta}")
            if cena_pdf_val:
                cena_parts.append(f"pdf: {cena_pdf_val:.2f} {waluta}")
            if cena_vtt_val:
                cena_parts.append(f"vtt: {cena_vtt_val:.2f} {waluta}")
            # Fallback na starą kolumnę gdy brak nowych (stara baza bez migracji)
            if not cena_parts and system[12] and status_kolekcja in ("W kolekcji", "Na sprzedaż"):
                cena_parts.append(f"{system[12]:.2f} {waluta}")
        cena_str = " / ".join(cena_parts)

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
                system[17] if len(system) > 17 else None,  # system_gry_id
            )
        )  # type: ignore

    return result  # type: ignore


def get_all_games() -> list[tuple[Any, ...]]:
    """Pobiera wszystkie gry (systemy_gry – najwyższy poziom hierarchii) z bazy."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            c = conn.cursor()
            c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='systemy_gry'"
            )
            if not c.fetchone():
                return []
            c.execute(
                "SELECT id, nazwa, wydawca_id, jezyk, notatki FROM systemy_gry ORDER BY id"
            )
            games = c.fetchall()
    except sqlite3.Error:
        return []

    publishers_map: Dict[int, str] = {}
    try:
        with sqlite3.connect(get_db_path("wydawcy.db")) as wconn:
            wconn.row_factory = sqlite3.Row
            wc = wconn.cursor()
            wc.execute("SELECT id, nazwa FROM wydawcy")
            publishers_map = {row[0]: row[1] for row in wc.fetchall()}
    except sqlite3.Error:
        pass

    return [
        (
            g[0],  # 0: id
            g[1],  # 1: nazwa
            publishers_map.get(g[2], "") if g[2] else "",  # 2: wydawca_nazwa
            g[3] or "",  # 3: jezyk
            g[4] or "",  # 4: notatki
        )
        for g in games
    ]


def needs_migration_wizard() -> bool:
    """Zwraca True jeśli istnieją PG bez przypisanego system_gry_id (migracja wymagana)."""
    import os
    if not os.path.exists(DB_FILE):
        return False
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='systemy_gry'"
            )
            if not c.fetchone():
                return False
            c.execute(
                "SELECT COUNT(*) FROM systemy_rpg "
                "WHERE typ='Podręcznik Główny' AND (system_gry_id IS NULL OR system_gry_id=0)"
            )
            count = c.fetchone()[0]
            return count > 0
    except sqlite3.Error:
        return False


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


def show_migration_wizard(parent: tk.Misc) -> None:
    """Kreator migracji jednorazowej: przypisuje istniejące Podręczniki Główne do systemy_gry.

    Wyświetla listę wszystkich PG bez system_gry_id i pozwala użytkownikowi
    wpisać nazwę systemu dla każdego PG.  PG z tą samą nazwą systemu zostaną
    pogrupowane pod jednym wpisem w tabeli systemy_gry.

    Po zatwierdzeniu:
    - Tworzy rekordy w systemy_gry
    - Aktualizuje systemy_rpg.system_gry_id
    - Aktualizuje sesje_rpg.system_id (z PG-id na system_gry-id)
    """
    import os

    if not os.path.exists(DB_FILE):
        return

    # Pobierz PG bez system_gry_id
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT id, nazwa FROM systemy_rpg "
                "WHERE typ='Podręcznik Główny' AND (system_gry_id IS NULL OR system_gry_id=0) "
                "ORDER BY nazwa"
            )
            pgs = [(row[0], row[1]) for row in c.fetchall()]
    except sqlite3.Error:
        return

    if not pgs:
        return

    dlg = create_ctk_toplevel(parent)
    dlg.title("Kreator migracji — przypisz Podręczniki Główne do Systemów")
    dlg.transient(parent if isinstance(parent, tk.Tk) else parent.winfo_toplevel())
    dlg.resizable(True, True)
    dlg.grab_set()  # blokuj rodzica
    apply_safe_geometry(dlg, parent if isinstance(parent, tk.Tk) else parent.winfo_toplevel(), 760, 560)

    dlg.columnconfigure(0, weight=1)
    dlg.rowconfigure(1, weight=1)

    # Nagłówek
    hdr = ctk.CTkFrame(dlg, fg_color="transparent")
    hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))
    ctk.CTkLabel(
        hdr,
        text="Nowa hierarchia: System → Podręczniki i Suplementy",
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(14), weight="bold"),
    ).pack(anchor="w")
    ctk.CTkLabel(
        hdr,
        text=(
            "Wpisz nazwę systemu dla każdego Podręcznika Głównego.\n"
            "Podręczniki z tą samą nazwą systemu zostaną pogrupowane pod jednym Systemem.\n"
            "Możesz zmienić nazwy po zakończeniu kreatora."
        ),
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(10)),
        justify="left",
    ).pack(anchor="w", pady=(4, 0))

    # Scrollable frame z wierszami
    sf = ctk.CTkScrollableFrame(dlg)
    sf.grid(row=1, column=0, sticky="nsew", padx=20, pady=12)
    sf.columnconfigure(0, weight=1)
    sf.columnconfigure(1, weight=2)

    ctk.CTkLabel(sf, text="Podręcznik Główny", font=ctk.CTkFont(weight="bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 6), padx=(0, 12)
    )
    ctk.CTkLabel(sf, text="Nazwa systemu (edytuj)", font=ctk.CTkFont(weight="bold")).grid(
        row=0, column=1, sticky="w", pady=(0, 6)
    )

    entry_vars: List[tk.StringVar] = []
    for i, (pg_id, pg_nazwa) in enumerate(pgs, start=1):
        ctk.CTkLabel(
            sf,
            text=pg_nazwa,
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(10)),
            anchor="w",
        ).grid(row=i, column=0, sticky="w", pady=3, padx=(0, 12))
        # Domyślna nazwa systemu = nazwa PG (użytkownik może skrócić / ujednolicić)
        var = tk.StringVar(value=pg_nazwa)
        entry_vars.append(var)
        ctk.CTkEntry(sf, textvariable=var, width=320).grid(row=i, column=1, sticky="ew", pady=3)

    # Przyciski dolne
    bf = ctk.CTkFrame(dlg, fg_color="transparent")
    bf.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

    migration_done = [False]

    def _apply_migration() -> None:
        """Wykonuje migrację na podstawie wartości z pól tekstowych."""
        # Zbierz mapę: pg_id → nazwa_systemu
        assignments: Dict[int, str] = {}
        for (pg_id, _), var in zip(pgs, entry_vars):
            sysname = var.get().strip()
            if not sysname:
                messagebox.showerror(
                    "Błąd", "Każdy Podręcznik Główny musi mieć podaną nazwę systemu.", parent=dlg
                )
                return
            assignments[pg_id] = sysname

        # Unikalne nazwy systemów → utwórz rekordy w systemy_gry
        unique_names = dict.fromkeys(assignments.values())  # zachowuje kolejność
        name_to_gry_id: Dict[str, int] = {}

        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON")
                c = conn.cursor()

                for sysname in unique_names:
                    # Sprawdź czy System o tej nazwie już istnieje
                    c.execute("SELECT id FROM systemy_gry WHERE nazwa=?", (sysname,))
                    row = c.fetchone()
                    if row:
                        name_to_gry_id[sysname] = row[0]
                    else:
                        c.execute(
                            "INSERT INTO systemy_gry (nazwa) VALUES (?)", (sysname,)
                        )
                        name_to_gry_id[sysname] = c.lastrowid  # type: ignore[assignment]

                # Aktualizuj systemy_rpg.system_gry_id dla każdego PG
                for pg_id, sysname in assignments.items():
                    gry_id = name_to_gry_id[sysname]
                    c.execute(
                        "UPDATE systemy_rpg SET system_gry_id=? WHERE id=?",
                        (gry_id, pg_id),
                    )

                # Propaguj system_gry_id do suplementów przez system_glowny_id
                for pg_id, sysname in assignments.items():
                    gry_id = name_to_gry_id[sysname]
                    c.execute(
                        "UPDATE systemy_rpg SET system_gry_id=? "
                        "WHERE typ='Suplement' AND system_glowny_id=?",
                        (gry_id, pg_id),
                    )

                conn.commit()

            # Aktualizuj sesje_rpg.system_id: z PG-id → system_gry-id
            # Budujemy mapę: pg_id → system_gry_id
            pg_to_gry: Dict[int, int] = {}
            for pg_id, sysname in assignments.items():
                pg_to_gry[pg_id] = name_to_gry_id[sysname]

            sesje_db = get_db_path("sesje_rpg.db")
            if os.path.exists(sesje_db):
                with sqlite3.connect(sesje_db) as sconn:
                    sc = sconn.cursor()
                    sc.execute("SELECT id, system_id FROM sesje_rpg")
                    sessions = sc.fetchall()
                    for sess_id, old_sys_id in sessions:
                        new_sys_id = pg_to_gry.get(old_sys_id)
                        if new_sys_id:
                            sc.execute(
                                "UPDATE sesje_rpg SET system_id=? WHERE id=?",
                                (new_sys_id, sess_id),
                            )
                    sconn.commit()

            migration_done[0] = True
            messagebox.showinfo(
                "Migracja zakończona",
                f"Utworzono {len(unique_names)} systemów i przypisano {len(pgs)} Podręczników Głównych.",
                parent=dlg,
            )
            dlg.destroy()

        except sqlite3.Error as e:
            messagebox.showerror("Błąd migracji", f"Nie udało się wykonać migracji:\n{e}", parent=dlg)

    def _skip_migration() -> None:
        if messagebox.askyesno(
            "Pomiń migrację",
            "Czy na pewno chcesz pominąć kreator migracji?\n"
            "Podręczniki bez przypisanego Systemu będą widoczne jako 'Osierocone PG'.\n"
            "Możesz uruchomić kreator ponownie przez przycisk 'Migruj dane' w ribbonie Systemy RPG.",
            parent=dlg,
        ):
            dlg.destroy()

    ctk.CTkButton(
        bf,
        text="Wykonaj migrację",
        command=_apply_migration,
        fg_color="#2E7D32",
        hover_color="#1B5E20",
        width=160,
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
    ).pack(side=tk.LEFT, padx=(0, 10))
    ctk.CTkButton(
        bf,
        text="Pomiń na razie",
        command=_skip_migration,
        fg_color="#666666",
        hover_color="#555555",
        width=120,
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
    ).pack(side=tk.LEFT)

    dlg.wait_window()


def dodaj_system_rpg(
    parent: Any,
    refresh_callback: Optional[Callable[..., None]] = None,
    preset_game_id: Optional[int] = None,
) -> None:
    """Otwiera okno dodawania nowego systemu RPG.

    Args:
        preset_game_id: Jeśli podany, nowy wpis zostanie automatycznie przypisany
                        do tego Systemu (systemy_gry.id) i typ zostanie podpowiedziany.
    """

    init_db()
    reserved_id = get_first_free_id()
    publishers = get_all_publishers()

    # Pobierz nazwę systemu jeśli preset_game_id podany
    _preset_game_name = ""
    if preset_game_id is not None:
        try:
            with sqlite3.connect(DB_FILE) as _pc:
                _row = _pc.execute("SELECT nazwa FROM systemy_gry WHERE id=?", (preset_game_id,)).fetchone()
                _preset_game_name = _row[0] if _row else ""
        except sqlite3.Error:
            pass

    dialog = create_ctk_toplevel(parent)
    dialog.withdraw()  # ukryj podczas budowania – eliminuje czarną ramkę
    if preset_game_id is not None and _preset_game_name:
        dialog.title(f"Dodaj do systemu: {_preset_game_name}")
    else:
        dialog.title("Dodaj podręcznik lub suplement")
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
    ctk.CTkLabel(main_frame, text="Nazwa/Tytuł *").grid(
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

    # Przypisz do systemu (systemy_gry) — widoczne gdy brak preset_game_id
    all_games_list = get_all_games() if preset_game_id is None else []
    przypisz_label = ctk.CTkLabel(main_frame, text="Przypisz do systemu *")
    przypisz_label.grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")
    przypisz_var = tk.StringVar()
    przypisz_combo = ctk.CTkComboBox(main_frame, variable=przypisz_var, state="readonly")
    if all_games_list:
        game_values = [f"{g[0]} - {g[1]}" for g in all_games_list]
        przypisz_combo.configure(values=game_values)
    przypisz_combo.grid(row=3, column=1, pady=8, sticky="w")
    if preset_game_id is not None:
        przypisz_label.grid_remove()
        przypisz_combo.grid_remove()

    # Typ suplementu - początkowo ukryte, obowiązkowe dla suplementów (wielokrotny wybór)
    typ_suplementu_label = ctk.CTkLabel(main_frame, text="Typ suplementu *")
    typ_suplementu_label.grid(row=5, column=0, pady=8, padx=(0, 10), sticky="nw")
    typ_suplementu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_suplementu_frame.grid(row=5, column=1, pady=8, sticky="ew")

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
        row=6, column=0, pady=8, padx=(0, 10), sticky="w"
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

    def _after_add_publisher(**_kw: Any) -> None:
        """Po dodaniu wydawcy odświeża listę i zaznacza nowego wydawcę."""
        nonlocal publishers
        old_ids = {pub[0] for pub in publishers}
        publishers = get_all_publishers()
        if publishers:
            wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
            wydawca_combo.configure(values=wydawca_values)
            new_pub = next((pub for pub in publishers if pub[0] not in old_ids), None)
            if new_pub:
                wydawca_var.set(f"{new_pub[0]} - {new_pub[1]}")
        else:
            wydawca_combo.configure(values=[])
        # Odśwież zakładkę Wydawcy w głównym oknie
        try:
            import wydawcy as _wydawcy_mod
            root = dialog.winfo_toplevel()
            wydawcy_tab = getattr(root, 'tabs', {}).get('Wydawcy')
            if wydawcy_tab:
                _wydawcy_mod.fill_wydawcy_tab(wydawcy_tab, dark_mode=getattr(root, 'dark_mode', False))
        except Exception:
            pass

    def _open_add_publisher() -> None:
        import wydawcy as _wydawcy
        _wydawcy.dodaj_wydawce(dialog, refresh_callback=_after_add_publisher)

    # Inicjalne załadowanie listy
    if publishers:
        wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
        wydawca_combo.configure(values=wydawca_values)

    # Odśwież listę wydawców przy każdym kliknięciu w combobox
    wydawca_combo.bind("<Button-1>", refresh_publishers_on_click)
    wydawca_combo.grid(row=6, column=1, pady=8, sticky="ew")

    # Przycisk dodania nowego wydawcy inline
    ctk.CTkButton(
        main_frame,
        text="➕ Dodaj wydawcę",
        command=_open_add_publisher,
        width=130,
        height=28,
        fg_color="#1565C0",
        hover_color="#0D47A1",
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
    ).grid(row=6, column=2, pady=8, padx=(10, 0), sticky="w")

    # Posiadanie
    ctk.CTkLabel(main_frame, text="Posiadanie").grid(
        row=7, column=0, pady=8, padx=(0, 10), sticky="nw"
    )
    posiadanie_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    posiadanie_frame.grid(row=7, column=1, pady=8, sticky="w", columnspan=3)
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
    ctk.CTkLabel(main_frame, text="Język").grid(row=8, column=0, pady=8, padx=(0, 10), sticky="w")
    jezyk_var = tk.StringVar(value="PL")
    jezyk_combo = ctk.CTkComboBox(
        main_frame,
        variable=jezyk_var,
        values=["PL", "ENG", "DE", "FR", "ES", "IT"],
        state="readonly",
        width=100,
    )
    jezyk_combo.grid(row=8, column=1, pady=8, sticky="w")

    # Status gry
    ctk.CTkLabel(main_frame, text="Status gry").grid(
        row=9, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_gra_var = tk.StringVar(value="Nie grane")
    status_gra_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_gra_var,
        values=["Grane", "Nie grane"],
        state="readonly",
        width=150,
    )
    status_gra_combo.grid(row=9, column=1, pady=8, sticky="w")

    # Status kolekcji
    ctk.CTkLabel(main_frame, text="Status kolekcji").grid(
        row=10, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_kolekcja_var = tk.StringVar(value="W kolekcji")
    status_kolekcja_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_kolekcja_var,
        values=["W kolekcji", "Na sprzedaż", "Sprzedane", "Nieposiadane", "Do kupienia"],
        state="readonly",
        width=150,
    )
    status_kolekcja_combo.grid(row=10, column=1, pady=8, sticky="w")

    # Cena zakupu (dla statusu "W kolekcji") — per forma posiadania
    cena_row_label = ctk.CTkLabel(main_frame, text="Cena zakupu")
    cena_row_label.grid(row=10, column=2, pady=8, padx=(20, 5), sticky="nw")

    cena_fields_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_fields_frame.grid(row=10, column=3, pady=8, padx=10, sticky="w")

    waluta_cena_var = tk.StringVar(value="PLN")
    waluta_cena_combo = ctk.CTkComboBox(
        cena_fields_frame,
        variable=waluta_cena_var,
        values=["PLN", "USD", "EUR", "GBP"],
        state="readonly",
        width=70,
    )
    waluta_cena_combo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

    # Wiersz fiz
    cena_fiz_lbl = ctk.CTkLabel(cena_fields_frame, text="Fiz:", width=40, anchor="w")
    cena_fiz_lbl.grid(row=1, column=0, sticky="w", pady=2)
    cena_fiz_entry = ctk.CTkEntry(cena_fields_frame, width=100)
    cena_fiz_entry.grid(row=1, column=1, sticky="w", pady=2, padx=(4, 0))
    # Wiersz pdf
    cena_pdf_lbl = ctk.CTkLabel(cena_fields_frame, text="PDF:", width=40, anchor="w")
    cena_pdf_lbl.grid(row=2, column=0, sticky="w", pady=2)
    cena_pdf_entry = ctk.CTkEntry(cena_fields_frame, width=100)
    cena_pdf_entry.grid(row=2, column=1, sticky="w", pady=2, padx=(4, 0))
    # Wiersz vtt
    cena_vtt_lbl = ctk.CTkLabel(cena_fields_frame, text="VTT:", width=40, anchor="w")
    cena_vtt_lbl.grid(row=3, column=0, sticky="w", pady=2)
    cena_vtt_entry = ctk.CTkEntry(cena_fields_frame, width=100)
    cena_vtt_entry.grid(row=3, column=1, sticky="w", pady=2, padx=(4, 0))

    # Cena sprzedaży (dla statusu "Sprzedane")
    cena_sprzedazy_label = ctk.CTkLabel(main_frame, text="Cena sprzedaży")
    cena_sprzedazy_label.grid(row=10, column=2, pady=8, padx=(20, 5), sticky="w")

    cena_sprzedazy_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_sprzedazy_frame.grid(row=10, column=3, pady=8, padx=10, sticky="w")

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

    # Początkowo ukryj wszystko
    cena_row_label.grid_remove()
    cena_fields_frame.grid_remove()
    cena_sprzedazy_label.grid_remove()
    cena_sprzedazy_frame.grid_remove()

    def _update_cena_fields(*_args: Any) -> None:
        """Pokazuje/ukrywa wiersze cen zakupu zależnie od posiadania i statusu."""
        status = status_kolekcja_var.get()
        has_fiz = fizyczny_var.get()
        has_pdf = pdf_var.get()
        has_vtt = vtt_var.get()

        if status == "Sprzedane":
            cena_row_label.grid_remove()
            cena_fields_frame.grid_remove()
            cena_sprzedazy_label.grid()
            cena_sprzedazy_frame.grid()
            return

        cena_sprzedazy_label.grid_remove()
        cena_sprzedazy_frame.grid_remove()

        if status in ("W kolekcji", "Na sprzedaż") and (has_fiz or has_pdf or has_vtt):
            cena_row_label.grid()
            cena_fields_frame.grid()
            # Pokaż/ukryj wiersze per forma
            if has_fiz:
                cena_fiz_lbl.grid()
                cena_fiz_entry.grid()
            else:
                cena_fiz_lbl.grid_remove()
                cena_fiz_entry.grid_remove()
            if has_pdf:
                cena_pdf_lbl.grid()
                cena_pdf_entry.grid()
            else:
                cena_pdf_lbl.grid_remove()
                cena_pdf_entry.grid_remove()
            if has_vtt:
                cena_vtt_lbl.grid()
                cena_vtt_entry.grid()
            else:
                cena_vtt_lbl.grid_remove()
                cena_vtt_entry.grid_remove()
        else:
            cena_row_label.grid_remove()
            cena_fields_frame.grid_remove()

    status_kolekcja_var.trace_add('write', _update_cena_fields)
    fizyczny_var.trace_add('write', _update_cena_fields)
    pdf_var.trace_add('write', _update_cena_fields)
    vtt_var.trace_add('write', _update_cena_fields)
    _update_cena_fields()  # stan początkowy

    def on_typ_change(*args: Any) -> None:
        """Obsługuje zmianę typu (Podręcznik Główny/Suplement)"""
        if typ_var.get() == "Suplement":
            typ_suplementu_label.grid(row=4, column=0, pady=8, padx=(0, 10), sticky="nw")
            typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")
        else:
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

        # Określ system_gry_id: preset ma priorytet, potem wybór z dropdown
        if preset_game_id is not None:
            game_id_to_save: Optional[int] = preset_game_id
        elif przypisz_var.get():
            try:
                game_id_to_save = int(przypisz_var.get().split(' - ')[0])
            except (ValueError, IndexError):
                game_id_to_save = None
        else:
            game_id_to_save = None

        # Walidacja: PG musi mieć przypisany system
        if typ == "Podręcznik Główny" and game_id_to_save is None:
            messagebox.showerror(
                "Błąd",
                "Podręcznik Główny musi być przypisany do systemu gry.",
                parent=dialog,
            )
            return

        system_glowny_id = None
        typ_suplementu = None

        if typ == "Suplement":
            # Zbierz wybrane typy suplementu
            wybrane_typy = [typ for typ, var in typ_suplementu_vars.items() if var.get()]  # type: ignore

            if not wybrane_typy:
                messagebox.showerror("Błąd", "Dla suplementu musisz wybrać przynajmniej jeden typ suplementu.", parent=dialog)  # type: ignore
                return

            # Połącz wybrane typy separatorem
            typ_suplementu = " | ".join(wybrane_typy)  # type: ignore

        wydawca_id = None
        if wydawca_var.get():
            wydawca_id = int(wydawca_var.get().split(' - ')[0])

        # Pobierz ceny w zależności od statusu i formy posiadania
        cena_fiz_new: Optional[float] = None
        cena_pdf_new: Optional[float] = None
        cena_vtt_new: Optional[float] = None
        cena_sprzedazy: Optional[float] = None
        waluta_sprzedazy: Optional[str] = None
        waluta_cena_new: Optional[str] = None

        def _parse_cena_add(entry: ctk.CTkEntry, label: str) -> Optional[float]:
            s = entry.get().strip().replace(',', '.')
            if not s:
                return None
            try:
                return float(s)
            except ValueError:
                messagebox.showerror("Błąd", f"Cena {label} musi być liczbą.", parent=dialog)
                raise

        if status_kolekcja_var.get() in ["W kolekcji", "Na sprzedaż"]:
            waluta_cena_new = waluta_cena_var.get()
            try:
                if fizyczny_var.get():
                    cena_fiz_new = _parse_cena_add(cena_fiz_entry, "fiz.")
                if pdf_var.get():
                    cena_pdf_new = _parse_cena_add(cena_pdf_entry, "PDF")
                if vtt_var.get():
                    cena_vtt_new = _parse_cena_add(cena_vtt_entry, "VTT")
            except ValueError:
                return
        elif status_kolekcja_var.get() == "Sprzedane":
            cena_str_sp = cena_sprzedazy_entry.get().strip().replace(',', '.')
            if cena_str_sp:
                try:
                    cena_sprzedazy = float(cena_str_sp)
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
                INSERT INTO systemy_rpg (id, nazwa, typ, system_glowny_id, typ_suplementu,
                                       wydawca_id, fizyczny, pdf, vtt, jezyk,
                                       status_gra, status_kolekcja,
                                       cena_zakupu, waluta_zakupu, cena_sprzedazy,
                                       waluta_sprzedazy,
                                       system_glowny_nazwa_custom,
                                       system_gry_id,
                                       cena_fiz, cena_pdf, cena_vtt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    cena_fiz_new,   # cena_zakupu (backup = fiz)
                    waluta_cena_new,
                    cena_sprzedazy,
                    waluta_sprzedazy,
                    None,
                    game_id_to_save,
                    cena_fiz_new,
                    cena_pdf_new,
                    cena_vtt_new,
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
    button_frame.grid(row=11, column=0, columnspan=4, pady=15, sticky="ew")
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
    _preloaded_games: Optional[List[Any]] = None,
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
                        games = get_all_games()
                        tab.after(
                            0,
                            lambda: fill_systemy_rpg_tab(
                                tab, dark_mode, _preloaded_data=data, _preloaded_games=games
                            ),
                        )

                    threading.Thread(target=_bg_fast_sys, daemon=True).start()
                    return
                cache['records_ref'][0] = _preloaded_data
                if _preloaded_games is not None:
                    cache['games_ref'][0] = _preloaded_games
                cache['rebuild_fn']()
                return
        except Exception:
            pass
        del tab._systemy_tab_cache  # type: ignore[attr-defined]

    if _preloaded_data is None or _preloaded_games is None:

        def _bg_full_sys() -> None:
            data = get_all_systems()
            games = get_all_games()
            tab.after(
                0,
                lambda: fill_systemy_rpg_tab(
                    tab, dark_mode, _preloaded_data=data, _preloaded_games=games
                ),
            )

        threading.Thread(target=_bg_full_sys, daemon=True).start()
        return

    for widget in tab.winfo_children():
        widget.destroy()

    records_ref: List[List[Any]] = [_preloaded_data]  # type: ignore
    games_ref: List[List[Any]] = [_preloaded_games]  # type: ignore

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

    # games: OrderedDict[game_id → game_tuple (0=id,1=nazwa,2=wydawca,3=jezyk,4=notatki)]
    games: OrderedDict[Any, Any] = OrderedDict()
    # pg_by_game: game_id → [PG records] (filtrowane)
    pg_by_game: Dict[Any, List[Any]] = {}
    # supl_by_pg: pg_id → [Suplement records]
    supl_by_pg: Dict[Any, List[Any]] = {}
    # supl_direct_by_game: game_id → [Suplement records] przypisane bezpośrednio do systemu (bez PG-rodzica)
    supl_direct_by_game: Dict[Any, List[Any]] = {}
    # orphaned_pgs: PG bez system_gry_id
    orphaned_pgs: List[Any] = []
    # orphaned_supls: Suplementy bez żadnego przypisania
    orphaned_supls: List[Any] = []
    expanded_state: Dict[Any, bool] = {}
    current_sort_reverse: List[bool] = [active_sort_systemy.get("reverse", False)]
    _table: List[Optional[CTkDataTable]] = [None]
    search_var: tk.StringVar = tk.StringVar()

    def _apply_record_filters(recs: List[Any]) -> List[Any]:
        def _fl(key: str) -> List[str]:
            """Pobierz listę wybranych wartości filtra (backward-compat ze starymi stringami)."""
            v = active_filters_systemy.get(key, [])
            if isinstance(v, str):
                return [] if v == 'Wszystkie' else [v]
            return list(v)

        result = []
        for rec in recs:
            typ_list = _fl('typ')
            if typ_list and rec[2] not in typ_list:
                continue
            wyd_list = _fl('wydawca')
            if wyd_list and (rec[5] or '') not in wyd_list:
                continue
            pf_list = _fl('posiadanie')
            if pf_list:
                match = False
                for pf in pf_list:
                    if pf == 'Fizyczny' and rec[6]:
                        match = True
                    elif pf == 'PDF' and rec[7]:
                        match = True
                    elif pf == 'Fizyczny i PDF' and rec[6] and rec[7]:
                        match = True
                    elif pf == 'Żadne' and not rec[6] and not rec[7]:
                        match = True
                if not match:
                    continue
            sf_list = _fl('status')
            if sf_list and not any(sf in (rec[10] or '') for sf in sf_list):
                continue
            wf_list = _fl('waluta')
            if wf_list and not any(wf in (rec[11] or '') for wf in wf_list):
                continue
            jf_list = _fl('jezyk')
            if jf_list and (rec[9] or '') not in jf_list:
                continue
            result.append(rec)
        return result  # type: ignore[return-value]

    def _rebuild_groups() -> None:
        nonlocal games, pg_by_game, supl_by_pg, supl_direct_by_game, orphaned_pgs, orphaned_supls
        filtered = _apply_record_filters(records_ref[0])
        phrase = search_var.get().strip().lower()

        # Grupuj wszystkie pozycje (PG i suplementy) bezpośrednio po system_gry_id
        items_by_game: Dict[int, List[Any]] = {}   # game_id → [rec, ...]
        orphans: List[Any] = []  # pozycje bez przypisanego systemu

        for rec in filtered:
            sgid = rec[13] if len(rec) > 13 else None
            if sgid:
                items_by_game.setdefault(sgid, []).append(rec)
            else:
                orphans.append(rec)

        # Załaduj systemy_gry (games) z games_ref
        raw_games = games_ref[0] if games_ref else []
        games.clear()
        pg_by_game.clear()
        supl_by_pg.clear()
        supl_direct_by_game.clear()
        orphaned_pgs.clear()
        orphaned_supls.clear()

        if not phrase:
            for g in raw_games:
                games[g[0]] = g
            for gid, items in items_by_game.items():
                supl_direct_by_game[gid] = items
            orphaned_supls.extend(orphans)
        else:
            for g in raw_games:
                gid = g[0]
                gname = (g[1] or '').lower()
                items_in_game = items_by_game.get(gid, [])
                game_name_match = phrase in gname
                matching_items = [r for r in items_in_game if phrase in (r[1] or '').lower()]
                if game_name_match or matching_items:
                    games[gid] = g
                    supl_direct_by_game[gid] = items_in_game if game_name_match else matching_items
            for rec in orphans:
                if phrase in (rec[1] or '').lower():
                    orphaned_supls.append(rec)

    def _build_hierarchical_data() -> List[List[Any]]:
        """Buduje płaską listę wierszy dla CTkDataTable (2-poziomowa hierarchia).

        Poziom 1: System (systemy_gry) — z symbolem [+]/[-]/[ ]
        Poziom 2: Wszystkie pozycje należące do systemu (PG i suplementy), sortowane po nazwie.
        """
        data_h: List[List[Any]] = []

        for gid in games:
            game = games[gid]
            items_here = supl_direct_by_game.get(gid, [])

            has_children = bool(items_here)
            symbol = "[-]" if expanded_state.get(gid) else ("[+]" if has_children else "   ")

            # Agreguj posiadanie ze wszystkich pozycji (logika OR)
            agg_fiz = any(r[6] for r in items_here)
            agg_pdf = any(r[7] for r in items_here)
            vtt_set = {r[8] for r in items_here if r[8]}
            agg_vtt = ", ".join(sorted(vtt_set))
            cnt = len(items_here)
            cnt_label = f"{cnt} poz." if cnt else ""

            # Agreguj Wydawcę i Język (unikalne wartości)
            wydawca_set = {r[5] for r in items_here if r[5]}
            agg_wydawca = ", ".join(sorted(wydawca_set)) if wydawca_set else (game[2] or "")
            jezyk_set = {r[9] for r in items_here if r[9]}
            agg_jezyk = ", ".join(sorted(jezyk_set)) if jezyk_set else (game[3] or "")

            game_name = (game[1] or "") + (f" ({cnt_label})" if cnt_label else "")
            game_row: List[Any] = [
                symbol,
                f"G{gid}",
                game_name,
                "System",
                "",
                "",
                agg_wydawca,
                "Tak" if agg_fiz else "Nie",
                "Tak" if agg_pdf else "Nie",
                agg_vtt,
                agg_jezyk,
                "",
                "",
            ]
            if not hide_systems_systemy:
                data_h.append(game_row)

            if expanded_state.get(gid):
                for rec in sorted(items_here, key=lambda x: (0 if x[2] == "Podręcznik Główny" else 1, (x[1] or "").lower())):
                    data_h.append([
                        "   ",
                        str(rec[0]),
                        "  " + (rec[1] or ""),
                        rec[2] or "",
                        game[1] or "",   # system główny = nazwa systemu gry
                        rec[4] or "",
                        rec[5] or "",
                        "Tak" if rec[6] else "Nie",
                        "Tak" if rec[7] else "Nie",
                        rec[8] or "",
                        rec[9] or "",
                        rec[10] or "",
                        rec[11] or "",
                    ])

        # Pozycje bez przypisanego systemu gry
        for rec in sorted(orphaned_supls, key=lambda r: (r[1] or '').lower()):
            mn = rec[12] or ""  # system_glowny_nazwa_custom (legacy)
            data_h.append([
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
            ])
        return data_h

    displayed_data: List[List[Any]] = []

    def _do_sort_main_systems(reverse: bool) -> None:
        sort_by = sort_var.get()

        def _key(x: Any) -> Any:
            g = games.get(x)
            if g is None:
                return ""
            items_here = supl_direct_by_game.get(x, [])
            if sort_by == "Nazwa systemu":
                return (g[1] or '').lower()
            elif sort_by == "Wydawca":
                wydawca_set = {r[5] for r in items_here if r[5]}
                agg = ", ".join(sorted(wydawca_set)) if wydawca_set else (g[2] or "")
                return agg.lower()
            elif sort_by == "Język":
                jezyk_set = {r[9] for r in items_here if r[9]}
                agg = ", ".join(sorted(jezyk_set)) if jezyk_set else (g[3] or "")
                return agg.lower()
            elif sort_by == "Status":
                status_set = {r[10] for r in items_here if r[10]}
                return ", ".join(sorted(status_set)).lower()
            elif sort_by == "Posiadanie":
                agg_fiz = any(r[6] for r in items_here)
                agg_pdf = any(r[7] for r in items_here)
                return int(agg_fiz) + int(agg_pdf)
            elif sort_by == "Cena":
                total = 0.0
                for r in items_here:
                    cena_str = r[11] if len(r) > 11 else ""
                    if cena_str:
                        try:
                            total += float(cena_str.split()[0])
                        except (ValueError, IndexError):
                            pass
                return total
            else:  # ID (default)
                try:
                    return int(g[0])
                except Exception:
                    return 0

        sorted_ids = sorted(games.keys(), key=_key, reverse=reverse)
        new_games: OrderedDict[Any, Any] = OrderedDict((k, games[k]) for k in sorted_ids)
        games.clear()
        games.update(new_games)

    def _apply_and_draw() -> None:
        nonlocal displayed_data
        _rebuild_groups()
        if search_var.get().strip() or all_expanded_systemy:
            for gid in games:
                expanded_state[gid] = True
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
        active = sum(1 for v in active_filters_systemy.values() if v)
        filter_btn.configure(text=f"Filtruj ({active})" if active else "Filtruj")

    # ── Kolorowanie wierszy ──────────────────────────────────────────────
    def _row_color(i: int, row: List[Any]) -> Any:  # type: ignore[return]
        symbol = row[0] if row else ""
        typ = row[3] if len(row) > 3 else ""
        status = row[11] if len(row) > 11 else ""
        if typ == "System":
            row_id = row[1] if len(row) > 1 else ""
            gid_str = str(row_id)[1:] if str(row_id).startswith("G") else None
            has_items = False
            if gid_str:
                try:
                    gid_int = int(gid_str)
                    has_items = bool(supl_direct_by_game.get(gid_int))
                except ValueError:
                    pass
            if has_items:
                return ("#4a3000" if dark_mode else "#fff8e1", "#ffcc80" if dark_mode else "#e65100")
            else:
                # System bez żadnych pozycji — szary
                return ("#2a2a2a" if dark_mode else "#eeeeee", "#757575" if dark_mode else "#9e9e9e")
        if "Na sprzedaż" in status:
            return ("#660000" if dark_mode else "#ff6666", "#ffcccc" if dark_mode else "#ffffff")
        if "Nieposiadane" in status:
            return ("#3a3a3a" if dark_mode else "#d3d3d3", "#b0b0b0" if dark_mode else "#505050")
        if "Do kupienia" in status:
            return ("#4a1a4a" if dark_mode else "#e6b3ff", "#e6b3e6" if dark_mode else "#4a004a")
        if typ == "Podręcznik Główny":
            if symbol in ("[+]", "[-]"):
                # Osierocony PG z symbolem rozwinięcia
                return ("#5d4e00" if dark_mode else "#ffa500", "#ffd700" if dark_mode else "#4d2d00")
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
        typ = row_data[3] if len(row_data) > 3 else ""
        if not sid:
            return
        try:
            if typ == "System" or str(sid).startswith("G"):
                gid_str = str(sid)[1:] if str(sid).startswith("G") else str(sid)
                open_edit_game_dialog(tab, int(gid_str), refresh_callback=_systemy_refresh)
            else:
                open_edit_system_dialog(tab, [str(sid)], refresh_callback=_systemy_refresh)
        except Exception as e:
            logger.exception("_on_edit: błąd otwierania edycji")
            messagebox.showerror("Błąd edycji", f"Nie można otworzyć okna edycji:\n{e}", parent=tab)

    def _on_cell_click(row_idx: int, col_idx: int, row_data: List[Any]) -> None:  # Tk callback
        if col_idx != 0:
            return
        symbol = row_data[0] if row_data else ""
        if symbol not in ("[+]", "[-]"):
            return
        if _table[0] is None:
            return
        try:
            raw_id = row_data[1]
            typ = row_data[3] if len(row_data) > 3 else ""

            if typ == "System" or str(raw_id).startswith("G"):
                # ── System: O(k) expand/collapse przez toggle_expand ──────────
                gid_str = str(raw_id)[1:] if str(raw_id).startswith("G") else str(raw_id)
                try:
                    gid = int(gid_str)
                except ValueError:
                    return
                new_expanded = not expanded_state.get(gid, False)
                expanded_state[gid] = new_expanded

                def _is_system_child(row: List[Any]) -> bool:
                    """Zwraca True gdy wiersz jest dzieckiem systemu (PG/Suplement pod systemem)."""
                    sym = str(row[0]) if row and row[0] is not None else ""
                    rid = str(row[1]) if len(row) > 1 else ""
                    # Wiersz-dziecko systemu ma zawsze symbol "   " (3 spacje) i ID bez prefiksu G
                    return sym == "   " and not rid.startswith("G")

                if new_expanded:
                    # Zbuduj child_rows tylko dla tego systemu (bez pełnego rebuild)
                    items_here_loc = supl_direct_by_game.get(gid, [])
                    game_data = games.get(gid)
                    game_name_loc: str = game_data[1] if game_data else ""

                    child_rows: List[List[Any]] = []
                    for rec in sorted(items_here_loc, key=lambda x: (0 if x[2] == "Podręcznik Główny" else 1, (x[1] or "").lower())):
                        child_rows.append([
                            "   ", str(rec[0]), "  " + (rec[1] or ""),
                            rec[2] or "", game_name_loc, rec[4] or "",
                            rec[5] or "",
                            "Tak" if rec[6] else "Nie",
                            "Tak" if rec[7] else "Nie",
                            rec[8] or "", rec[9] or "", rec[10] or "", rec[11] or "",
                        ])
                    _table[0].toggle_expand(
                        parent_id=f"G{gid}",
                        expand=True,
                        child_rows=child_rows,
                    )
                else:
                    _table[0].toggle_expand(
                        parent_id=f"G{gid}",
                        expand=False,
                        is_child_fn=_is_system_child,
                    )
            else:
                # ── Osierocony PG: pełny rebuild (rzadka operacja) ────────────
                try:
                    main_id = int(raw_id)
                except ValueError:
                    return
                expanded_state[main_id] = not expanded_state.get(main_id, False)
                _table[0].set_data(_build_hierarchical_data())
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
        clean_name = sname.strip().split(" (")[0] if (" (" in sname) else sname.strip()

        def _edit() -> None:
            _on_edit(row_idx, row_data)

        def _delete() -> None:
            if not sid:
                return
            if stype == "System":
                gid_str = str(sid)[1:] if str(sid).startswith("G") else str(sid)
                try:
                    gid_int = int(gid_str)
                except ValueError:
                    return
                items_under = supl_direct_by_game.get(gid_int, [])
                warn = f"Czy na pewno chcesz usunąć System: {clean_name}?"
                if items_under:
                    warn += (
                        f"\n\nUWAGA: System ma {len(items_under)} pozycję/pozycje"
                        " — ich system_gry_id zostanie wyczyszczony (staną się osierocone)."
                    )
                if not messagebox.askyesno("Usuń System", warn, parent=tab):
                    return
                try:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.execute("PRAGMA foreign_keys = ON")
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE systemy_rpg SET system_gry_id=NULL WHERE system_gry_id=?",
                            (gid_int,),
                        )
                        cur.execute("DELETE FROM systemy_gry WHERE id=?", (gid_int,))
                        conn.commit()
                    fill_systemy_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
                except sqlite3.Error as e:
                    messagebox.showerror("Błąd bazy danych", f"Nie udało się usunąć:\n{e}", parent=tab)
                return

            is_pg = stype == "Podręcznik Główny"
            warn = f"Czy na pewno chcesz usunąć: {clean_name}?"
            sid_int: Optional[int] = None
            try:
                sid_int = int(str(sid))
            except ValueError:
                pass
            if messagebox.askyesno("Usuń", warn, parent=tab):
                try:
                    with sqlite3.connect(DB_FILE) as conn:
                        conn.row_factory = sqlite3.Row
                        conn.execute("PRAGMA foreign_keys = ON")
                        cur = conn.cursor()
                        if is_pg and sid_int is not None:
                            # Orphan supplements — nie usuwaj, tylko odłącz od PG
                            cur.execute(
                                "UPDATE systemy_rpg SET system_glowny_id=NULL WHERE system_glowny_id=?",
                                (sid_int,),
                            )
                        cur.execute("DELETE FROM systemy_rpg WHERE id=?", (str(sid),))
                        conn.commit()
                    fill_systemy_rpg_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
                except sqlite3.Error as e:
                    messagebox.showerror("Błąd bazy danych", f"Nie udało się usunąć:\n{e}", parent=tab)

        def _toggle() -> None:
            _on_cell_click(row_idx, 0, row_data)

        def _dodaj_do_systemu(raw_sid: Any) -> None:
            """Otwiera dialog dodawania PG lub Suplementu bezpośrednio do Systemu."""
            gid_str = str(raw_sid)[1:] if str(raw_sid).startswith("G") else str(raw_sid)
            try:
                gid = int(gid_str)
            except ValueError:
                return
            dodaj_system_rpg(tab.winfo_toplevel(), refresh_callback=_systemy_refresh, preset_game_id=gid)

        def _assign_pg_to_game() -> None:
            """Otwiera dialog do przypisania PG do Systemu."""
            if not sid:
                return
            try:
                pg_id = int(str(sid))
            except ValueError:
                return
            _open_assign_pg_dialog(tab, pg_id, clean_name, _systemy_refresh)

        ctx = tk.Menu(tab, tearoff=0)
        ctx.add_command(label="Edytuj", command=_edit)
        if stype == "System":
            if symbol in ("[+]", "[-]"):
                ctx.add_command(label="Zwiń" if symbol == "[-]" else "Rozwiń", command=_toggle)
            ctx.add_command(
                label="Dodaj Podręcznik Główny/Suplement do systemu",
                command=lambda cap_sid=sid: _dodaj_do_systemu(cap_sid),
            )
        elif stype == "Podręcznik Główny":
            ctx.add_command(label="Przypisz do Systemu...", command=_assign_pg_to_game)
        elif stype == "Suplement":
            ctx.add_command(
                label="Przypisz do Systemu...",
                command=lambda: _open_assign_supl_dialog(tab, int(str(sid)), clean_name, _systemy_refresh)
                if sid else None,
            )
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
    hide_systems_var = tk.BooleanVar(value=hide_systems_systemy)
    hide_switch_ref: List[Any] = [None]

    def _on_toggle_expand_all() -> None:
        global all_expanded_systemy, hide_systems_systemy
        all_expanded_systemy = bool(expand_var.get())
        if all_expanded_systemy:
            for gid in games:
                expanded_state[gid] = True
            if hide_switch_ref[0] is not None:
                hide_switch_ref[0].configure(state="normal")
        else:
            expanded_state.clear()
            # Gdy zwijamy wszystko — wyłącz też ukrywanie systemów
            hide_systems_systemy = False
            hide_systems_var.set(False)
            if hide_switch_ref[0] is not None:
                hide_switch_ref[0].configure(state="disabled")
        if _table[0] is not None:
            _table[0].set_data(_build_hierarchical_data())

    def _on_toggle_hide_systems() -> None:
        global hide_systems_systemy
        hide_systems_systemy = bool(hide_systems_var.get())
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

    hide_sw = ctk.CTkSwitch(
        top_bar,
        text="Ukryj systemy",
        variable=hide_systems_var,
        command=_on_toggle_hide_systems,
        onvalue=True,
        offvalue=False,
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(10)),
        width=50,
        state="normal" if all_expanded_systemy else "disabled",
    )
    hide_sw.pack(side=tk.LEFT, padx=4)
    hide_switch_ref[0] = hide_sw
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
        for gid in games:
            expanded_state[gid] = True
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

    def _compute_col_order() -> List[int]:
        """Zwraca permutację kolumn: [0, 1, ...] wg active_col_order_systemy."""
        fixed = [h for h in _HEADERS if h in _ALWAYS_VISIBLE_SYSTEMY]
        ordered = [h for h in active_col_order_systemy if h in _HEADERS and h not in _ALWAYS_VISIBLE_SYSTEMY]
        missing = [h for h in _HEADERS if h not in _ALWAYS_VISIBLE_SYSTEMY and h not in ordered]
        ordered += missing
        display_order = fixed + ordered
        hdr_idx = {h: i for i, h in enumerate(_HEADERS)}
        return [hdr_idx[h] for h in display_order if h in hdr_idx]

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
        col_order=_compute_col_order(),
    )
    tbl.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    tab.rowconfigure(1, weight=1)
    tab.columnconfigure(0, weight=1)
    _table[0] = tbl

    tab._systemy_tab_cache = {  # type: ignore[attr-defined]
        'records_ref': records_ref,
        'games_ref': games_ref,
        'rebuild_fn': _rebuild_fn,
        'table_ref': tbl,
        'dark_mode': dark_mode,
    }

    # ── Dialog filtrowania ────────────────────────────────────────────────
    def _open_filter() -> None:
        dlg = create_ctk_toplevel(tab)
        dlg.title("Filtruj systemy RPG")
        dlg.transient(tab.winfo_toplevel())
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 560, 400)

        outer = ctk.CTkScrollableFrame(dlg)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        cur = records_ref[0]
        rows_cfg = [
            ("Typ:", 'typ', ['Podręcznik Główny', 'Suplement']),
            ("Wydawca:", 'wydawca', sorted({str(r[5]) for r in cur if r[5]})),
            ("Posiadanie:", 'posiadanie', ['Fizyczny', 'PDF', 'Fizyczny i PDF', 'Żadne']),
            ("Język:", 'jezyk', sorted({str(r[9]) for r in cur if r[9]})),
            ("Status:", 'status', ['Grane', 'Nie grane', 'W kolekcji', 'Na sprzedaż', 'Sprzedane', 'Nieposiadane', 'Do kupienia']),
            ("Waluta:", 'waluta', ['PLN', 'USD', 'EUR', 'GBP']),
        ]

        # selected[key] = zbiór aktualnie wybranych wartości
        selected: Dict[str, set] = {}

        def _get_existing(key: str) -> set:
            v = active_filters_systemy.get(key, [])
            if isinstance(v, str):
                return set() if v == 'Wszystkie' else {v}
            return set(v)

        def _add_toggle_row(parent: Any, row_idx: int, label: str, key: str, vals: List[str]) -> None:
            selected[key] = _get_existing(key)
            ctk.CTkLabel(parent, text=label, anchor="w", width=80).grid(
                row=row_idx, column=0, sticky="nw", pady=(6, 2), padx=(0, 6)
            )
            wrap = ctk.CTkFrame(parent, fg_color="transparent", height=30)
            wrap.grid(row=row_idx, column=1, sticky="ew", pady=(6, 2))
            wrap.grid_propagate(False)

            btns: List[ctk.CTkButton] = []

            def _make_btn(val: str) -> ctk.CTkButton:
                active = val in selected[key]
                btn = ctk.CTkButton(
                    wrap,
                    text=val,
                    width=max(50, len(val) * 8),
                    height=26,
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

        for ri, (label, key, vals) in enumerate(rows_cfg):
            _add_toggle_row(outer, ri, label, key, vals)
        outer.columnconfigure(1, weight=1)

        bf = ctk.CTkFrame(dlg, fg_color="transparent")
        bf.pack(pady=(6, 10))

        def _apply() -> None:
            for key in selected:
                active_filters_systemy[key] = list(selected[key])
            _apply_and_draw()
            dlg.destroy()

        def _reset() -> None:
            active_filters_systemy.clear()
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

    # ── Pierwsze wypełnienie ─────────────────────────────────────────────
    displayed_data = initial_data
    tbl.set_data(initial_data)
    _refresh_filter_btn()

    # ── Dialog wyboru kolumn ─────────────────────────────────────────────
    def _open_columns_dialog() -> None:
        """Otwiera dialog z checkboxami i przyciskami kolejności kolumn tabeli systemów."""
        dlg = create_ctk_toplevel(tab)
        dlg.title("Kolumny – Systemy RPG")
        dlg.transient(tab.winfo_toplevel())

        # Buduj listę w aktualnej kolejności (active_col_order_systemy) uzupełnioną o brakujące
        toggleable_base = [h for h in _HEADERS if h not in _ALWAYS_VISIBLE_SYSTEMY]
        ordered = [h for h in active_col_order_systemy if h in toggleable_base]
        ordered += [h for h in toggleable_base if h not in ordered]

        dialog_h = min(120 + len(ordered) * 38, 520)
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 340, dialog_h)

        outer = ctk.CTkScrollableFrame(dlg)
        outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            outer,
            text="Widoczność i kolejność kolumn:",
            font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(10), weight="bold"),
        ).pack(anchor="w", pady=(0, 6))

        # Stan: lista [(col_name, BooleanVar)] zachowuje kolejność
        order_list: List[str] = list(ordered)
        vis_vars: Dict[str, tk.BooleanVar] = {
            h: tk.BooleanVar(value=active_visible_cols_systemy.get(h, True))
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

        bf = ctk.CTkFrame(outer, fg_color="transparent")
        bf.pack(pady=(12, 0))

        def _apply() -> None:
            for col_name, v in vis_vars.items():
                active_visible_cols_systemy[col_name] = bool(v.get())
            active_col_order_systemy.clear()
            active_col_order_systemy.extend(order_list)
            dlg.destroy()
            cache = getattr(tab, '_systemy_tab_cache', None)
            preloaded = cache['records_ref'][0] if cache else None
            if hasattr(tab, '_systemy_tab_cache'):
                del tab._systemy_tab_cache  # type: ignore[attr-defined]
            fill_systemy_rpg_tab(tab, dark_mode=dark_mode, _preloaded_data=preloaded)

        def _reset() -> None:
            for v in vis_vars.values():
                v.set(True)
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
                       system_glowny_nazwa_custom, system_gry_id,
                       cena_fiz, cena_pdf, cena_vtt
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

    # Nazwa/Tytuł (obowiązkowe)
    ctk.CTkLabel(main_frame, text="Nazwa/Tytuł *").grid(
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

    # Przypisz do systemu gry (systemy_gry) - zawsze widoczne
    all_games_edit = get_all_games()
    przypisz_edit_label = ctk.CTkLabel(main_frame, text="Przypisz do systemu *")
    przypisz_edit_label.grid(row=3, column=0, pady=8, padx=(0, 10), sticky="w")
    przypisz_edit_var = tk.StringVar()
    przypisz_edit_combo = ctk.CTkComboBox(main_frame, variable=przypisz_edit_var, state="readonly")
    if all_games_edit:
        game_edit_values = [f"{g[0]} - {g[1]}" for g in all_games_edit]
        przypisz_edit_combo.configure(values=game_edit_values)
        if system_data[17]:  # system_gry_id
            for g in all_games_edit:
                if g[0] == system_data[17]:
                    przypisz_edit_var.set(f"{g[0]} - {g[1]}")
                    break
    przypisz_edit_combo.grid(row=3, column=1, pady=8, sticky="w")

    def _after_add_game_edit(**_kw: Any) -> None:
        """Odświeża listę systemów gry po dodaniu nowego."""
        nonlocal all_games_edit
        current_val = przypisz_edit_var.get()
        all_games_edit = get_all_games()
        if all_games_edit:
            vals = [f"{g[0]} - {g[1]}" for g in all_games_edit]
            przypisz_edit_combo.configure(values=vals)
            if current_val and current_val in vals:
                przypisz_edit_var.set(current_val)
            else:
                # Zaznacz nowo dodany system (ostatni z nowych ID)
                old_ids = {g[0] for g in all_games_edit if f"{g[0]} - {g[1]}" != current_val}
                new_game = next((g for g in all_games_edit if g[0] not in old_ids), None)
                if new_game:
                    przypisz_edit_var.set(f"{new_game[0]} - {new_game[1]}")

    ctk.CTkButton(
        main_frame,
        text="➕ Dodaj system",
        command=lambda: open_add_game_dialog(dialog, refresh_callback=_after_add_game_edit),  # type: ignore[arg-type]
        width=130,
        height=28,
        fg_color="#1565C0",
        hover_color="#0D47A1",
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
    ).grid(row=3, column=2, pady=8, padx=(10, 0), sticky="w")

    # Typ suplementu - obowiązkowe dla suplementów (wielokrotny wybór)
    typ_suplementu_label = ctk.CTkLabel(main_frame, text="Typ suplementu *")
    typ_suplementu_label.grid(row=5, column=0, pady=8, padx=(0, 10), sticky="nw")
    typ_suplementu_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_suplementu_frame.grid(row=5, column=1, pady=8, sticky="ew")

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
        row=6, column=0, pady=8, padx=(0, 10), sticky="w"
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

    def _after_add_publisher(**_kw: Any) -> None:
        """Po dodaniu wydawcy odświeża listę i zaznacza nowego wydawcę."""
        nonlocal publishers
        old_ids = {pub[0] for pub in publishers}
        publishers = get_all_publishers()
        if publishers:
            wydawca_values = [f"{pub[0]} - {pub[1]}" for pub in publishers]
            wydawca_combo.configure(values=wydawca_values)
            new_pub = next((pub for pub in publishers if pub[0] not in old_ids), None)
            if new_pub:
                wydawca_var.set(f"{new_pub[0]} - {new_pub[1]}")
        else:
            wydawca_combo.configure(values=[])
        # Odśwież zakładkę Wydawcy w głównym oknie
        try:
            import wydawcy as _wydawcy_mod
            root = dialog.winfo_toplevel()
            wydawcy_tab = getattr(root, 'tabs', {}).get('Wydawcy')
            if wydawcy_tab:
                _wydawcy_mod.fill_wydawcy_tab(wydawcy_tab, dark_mode=getattr(root, 'dark_mode', False))
        except Exception:
            pass

    def _open_add_publisher() -> None:
        import wydawcy as _wydawcy
        _wydawcy.dodaj_wydawce(dialog, refresh_callback=_after_add_publisher)

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
    wydawca_combo.grid(row=6, column=1, pady=8, sticky="ew")

    # Przycisk dodania nowego wydawcy inline
    ctk.CTkButton(
        main_frame,
        text="➕ Dodaj wydawcę",
        command=_open_add_publisher,
        width=130,
        height=28,
        fg_color="#1565C0",
        hover_color="#0D47A1",
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
    ).grid(row=6, column=2, pady=8, padx=(10, 0), sticky="w")

    # Posiadanie
    ctk.CTkLabel(main_frame, text="Posiadanie").grid(
        row=7, column=0, pady=8, padx=(0, 10), sticky="nw"
    )
    posiadanie_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    posiadanie_frame.grid(row=7, column=1, pady=8, sticky="w", columnspan=3)
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
    ctk.CTkLabel(main_frame, text="Język").grid(row=8, column=0, pady=8, padx=(0, 10), sticky="w")
    jezyk_var = tk.StringVar(value=system_data[9] or "PL")
    jezyk_combo = ctk.CTkComboBox(
        main_frame,
        variable=jezyk_var,
        values=["PL", "ENG", "DE", "FR", "ES", "IT"],
        state="readonly",
        width=100,
    )
    jezyk_combo.grid(row=8, column=1, pady=8, sticky="w")

    # Status gry
    ctk.CTkLabel(main_frame, text="Status gry").grid(
        row=9, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_gra_var = tk.StringVar(value=system_data[10] or "Nie grane")
    status_gra_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_gra_var,
        values=["Grane", "Nie grane"],
        state="readonly",
        width=150,
    )
    status_gra_combo.grid(row=9, column=1, pady=8, sticky="w")

    # Status kolekcji
    ctk.CTkLabel(main_frame, text="Status kolekcji").grid(
        row=10, column=0, pady=8, padx=(0, 10), sticky="w"
    )
    status_kolekcja_var = tk.StringVar(value=system_data[11] or "W kolekcji")
    status_kolekcja_combo = ctk.CTkComboBox(
        main_frame,
        variable=status_kolekcja_var,
        values=["W kolekcji", "Na sprzedaż", "Sprzedane", "Nieposiadane", "Do kupienia"],
        state="readonly",
        width=150,
    )
    status_kolekcja_combo.grid(row=10, column=1, pady=8, sticky="w")

    # Cena zakupu — per forma posiadania
    cena_row_label_e = ctk.CTkLabel(main_frame, text="Cena zakupu")
    cena_row_label_e.grid(row=10, column=2, pady=8, padx=(20, 5), sticky="nw")

    cena_fields_frame_e = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_fields_frame_e.grid(row=10, column=3, pady=8, padx=10, sticky="w")

    _db_waluta_cena = system_data[13] if system_data[13] else "PLN"
    waluta_cena_e_var = tk.StringVar(value=_db_waluta_cena)
    waluta_cena_e_combo = ctk.CTkComboBox(
        cena_fields_frame_e,
        variable=waluta_cena_e_var,
        values=["PLN", "USD", "EUR", "GBP"],
        state="readonly",
        width=70,
    )
    waluta_cena_e_combo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

    cena_fiz_e_lbl = ctk.CTkLabel(cena_fields_frame_e, text="Fiz:", width=40, anchor="w")
    cena_fiz_e_lbl.grid(row=1, column=0, sticky="w", pady=2)
    cena_fiz_e_entry = ctk.CTkEntry(cena_fields_frame_e, width=100)
    cena_fiz_e_entry.grid(row=1, column=1, sticky="w", pady=2, padx=(4, 0))
    _cf = system_data[18] if len(system_data) > 18 and system_data[18] else None
    if _cf:
        cena_fiz_e_entry.insert(0, f"{_cf:.2f}")

    cena_pdf_e_lbl = ctk.CTkLabel(cena_fields_frame_e, text="PDF:", width=40, anchor="w")
    cena_pdf_e_lbl.grid(row=2, column=0, sticky="w", pady=2)
    cena_pdf_e_entry = ctk.CTkEntry(cena_fields_frame_e, width=100)
    cena_pdf_e_entry.grid(row=2, column=1, sticky="w", pady=2, padx=(4, 0))
    _cp = system_data[19] if len(system_data) > 19 and system_data[19] else None
    if _cp:
        cena_pdf_e_entry.insert(0, f"{_cp:.2f}")

    cena_vtt_e_lbl = ctk.CTkLabel(cena_fields_frame_e, text="VTT:", width=40, anchor="w")
    cena_vtt_e_lbl.grid(row=3, column=0, sticky="w", pady=2)
    cena_vtt_e_entry = ctk.CTkEntry(cena_fields_frame_e, width=100)
    cena_vtt_e_entry.grid(row=3, column=1, sticky="w", pady=2, padx=(4, 0))
    _cv = system_data[20] if len(system_data) > 20 and system_data[20] else None
    if _cv:
        cena_vtt_e_entry.insert(0, f"{_cv:.2f}")

    # Cena sprzedaży (dla statusu "Sprzedane")
    cena_sprzedazy_label = ctk.CTkLabel(main_frame, text="Cena sprzedaży")
    cena_sprzedazy_label.grid(row=10, column=2, pady=8, padx=(20, 5), sticky="w")

    cena_sprzedazy_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    cena_sprzedazy_frame.grid(row=10, column=3, pady=8, padx=10, sticky="w")

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

    # Początkowo ukryj
    cena_row_label_e.grid_remove()
    cena_fields_frame_e.grid_remove()
    cena_sprzedazy_label.grid_remove()
    cena_sprzedazy_frame.grid_remove()

    def _update_cena_fields_e(*_args: Any) -> None:
        """Pokazuje/ukrywa wiersze cen zakupu zależnie od posiadania i statusu (edycja)."""
        status = status_kolekcja_var.get()
        has_fiz = fizyczny_var.get()
        has_pdf = pdf_var.get()
        has_vtt = vtt_var.get()

        if status == "Sprzedane":
            cena_row_label_e.grid_remove()
            cena_fields_frame_e.grid_remove()
            cena_sprzedazy_label.grid()
            cena_sprzedazy_frame.grid()
            return

        cena_sprzedazy_label.grid_remove()
        cena_sprzedazy_frame.grid_remove()

        if status in ("W kolekcji", "Na sprzedaż") and (has_fiz or has_pdf or has_vtt):
            cena_row_label_e.grid()
            cena_fields_frame_e.grid()
            if has_fiz:
                cena_fiz_e_lbl.grid()
                cena_fiz_e_entry.grid()
            else:
                cena_fiz_e_lbl.grid_remove()
                cena_fiz_e_entry.grid_remove()
            if has_pdf:
                cena_pdf_e_lbl.grid()
                cena_pdf_e_entry.grid()
            else:
                cena_pdf_e_lbl.grid_remove()
                cena_pdf_e_entry.grid_remove()
            if has_vtt:
                cena_vtt_e_lbl.grid()
                cena_vtt_e_entry.grid()
            else:
                cena_vtt_e_lbl.grid_remove()
                cena_vtt_e_entry.grid_remove()
        else:
            cena_row_label_e.grid_remove()
            cena_fields_frame_e.grid_remove()

    status_kolekcja_var.trace_add('write', _update_cena_fields_e)
    fizyczny_var.trace_add('write', _update_cena_fields_e)
    pdf_var.trace_add('write', _update_cena_fields_e)
    vtt_var.trace_add('write', _update_cena_fields_e)
    _update_cena_fields_e()  # stan początkowy

    # Flaga inicjalizacji - zapobiega wywołaniu update_dialog_size() podczas budowania dialogu
    _initializing: List[bool] = [True]

    def on_typ_change(*args: Any) -> None:
        """Obsługuje zmianę typu (Podręcznik Główny/Suplement)"""
        current_typ = typ_var.get()
        logger.debug(
            "on_typ_change: wywołano, typ=%r, _initializing=%r", current_typ, _initializing[0]
        )
        if current_typ == "Suplement":
            typ_suplementu_label.grid(row=4, column=0, pady=8, padx=(0, 10), sticky="nw")
            typ_suplementu_frame.grid(row=4, column=1, pady=8, sticky="ew")
        else:
            typ_suplementu_label.grid_remove()
            typ_suplementu_frame.grid_remove()

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

        typ_suplementu = None

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

        # system_gry_id z dropdown Przypisz do systemu
        game_id_to_save: Optional[int] = None
        if przypisz_edit_var.get():
            try:
                game_id_to_save = int(przypisz_edit_var.get().split(' - ')[0])
            except (ValueError, IndexError):
                game_id_to_save = None

        wydawca_id = None
        if wydawca_var.get():
            wydawca_id = int(wydawca_var.get().split(' - ')[0])

        # Pobierz ceny w zależności od statusu i formy posiadania
        cena_fiz_save: Optional[float] = None
        cena_pdf_save: Optional[float] = None
        cena_vtt_save: Optional[float] = None
        cena_sprzedazy: Optional[float] = None
        waluta_sprzedazy: Optional[str] = None
        waluta_cena_save: Optional[str] = None

        def _parse_cena_edit(entry: ctk.CTkEntry, label: str) -> Optional[float]:
            s = entry.get().strip().replace(',', '.')
            if not s:
                return None
            try:
                return float(s)
            except ValueError:
                messagebox.showerror("Błąd", f"Cena {label} musi być liczbą.", parent=dialog)
                raise

        if status_kolekcja_var.get() in ["W kolekcji", "Na sprzedaż"]:
            waluta_cena_save = waluta_cena_e_var.get()
            try:
                if fizyczny_var.get():
                    cena_fiz_save = _parse_cena_edit(cena_fiz_e_entry, "fiz.")
                if pdf_var.get():
                    cena_pdf_save = _parse_cena_edit(cena_pdf_e_entry, "PDF")
                if vtt_var.get():
                    cena_vtt_save = _parse_cena_edit(cena_vtt_e_entry, "VTT")
            except ValueError:
                return
        elif status_kolekcja_var.get() == "Sprzedane":
            cena_str_sp = cena_sprzedazy_entry.get().strip().replace(',', '.')
            if cena_str_sp:
                try:
                    cena_sprzedazy = float(cena_str_sp)
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
                    waluta_sprzedazy=?, system_gry_id=?,
                    cena_fiz=?, cena_pdf=?, cena_vtt=?
                WHERE id=?
            """,
                (
                    nazwa,
                    typ,
                    system_data[3],  # zachowaj istniejący system_glowny_id
                    typ_suplementu,
                    wydawca_id,
                    int(fizyczny_var.get()),
                    int(pdf_var.get()),
                    vtt_str,
                    jezyk if jezyk else None,
                    status_gra_var.get(),
                    status_kolekcja_var.get(),
                    cena_fiz_save,  # cena_zakupu (backup = fiz)
                    waluta_cena_save,
                    cena_sprzedazy,
                    waluta_sprzedazy,
                    game_id_to_save,
                    cena_fiz_save,
                    cena_pdf_save,
                    cena_vtt_save,
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
    button_frame.grid(row=11, column=0, columnspan=4, pady=15, sticky="ew")
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


def open_add_game_dialog(
    parent: Any,
    refresh_callback: Optional[Callable[..., None]] = None,
) -> None:
    """Otwiera dialog dodawania nowego Systemu (systemy_gry)."""
    init_db()

    dlg = create_ctk_toplevel(parent)
    dlg.withdraw()
    dlg.title("Dodaj System (nowy wpis w katalogu systemów)")
    dlg.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)
    dlg.resizable(True, True)
    apply_safe_geometry(dlg, parent, 600, 230)

    mf = ctk.CTkScrollableFrame(dlg)
    mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    mf.columnconfigure(1, weight=1)

    row = 0
    ctk.CTkLabel(mf, text="Nazwa systemu *").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    nazwa_entry = ctk.CTkEntry(mf, placeholder_text="np. Delta Green, D&D 5e")
    nazwa_entry.grid(row=row, column=1, pady=8, sticky="ew")
    dlg.after(100, lambda: nazwa_entry.focus_set() if nazwa_entry.winfo_exists() else None)
    row += 1

    ctk.CTkLabel(mf, text="Notatki").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="nw")
    notatki_entry = ctk.CTkTextbox(mf, height=60)
    notatki_entry.grid(row=row, column=1, pady=8, sticky="ew")
    row += 1

    bf = ctk.CTkFrame(mf, fg_color="transparent")
    bf.grid(row=row, column=0, columnspan=2, pady=(16, 0))

    def _save() -> None:
        nazwa = nazwa_entry.get().strip()
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa systemu jest wymagana.", parent=dlg)
            return
        notatki = notatki_entry.get("1.0", tk.END).strip() or None
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute(
                    "INSERT INTO systemy_gry (nazwa, notatki) VALUES (?,?)",
                    (nazwa, notatki),
                )
                conn.commit()
            dlg.destroy()
            if refresh_callback:
                refresh_callback()
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy danych", f"Nie udało się dodać Systemu:\n{e}", parent=dlg)

    ctk.CTkButton(
        bf, text="Zapisz", command=_save, fg_color="#2E7D32", hover_color="#1B5E20", width=100,
    ).pack(side=tk.LEFT, padx=5)
    ctk.CTkButton(
        bf, text="Anuluj", command=dlg.destroy, fg_color="#666666", hover_color="#555555", width=90,
    ).pack(side=tk.LEFT, padx=5)
    dlg.after(0, dlg.deiconify)


def open_edit_game_dialog(
    parent: Any,
    game_id: int,
    refresh_callback: Optional[Callable[..., None]] = None,
) -> None:
    """Otwiera dialog edycji Systemu (systemy_gry)."""
    init_db()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id, nazwa, notatki FROM systemy_gry WHERE id=?", (game_id,))
            gdata = c.fetchone()
    except sqlite3.Error as e:
        messagebox.showerror("Błąd", f"Nie można odczytać danych systemu:\n{e}", parent=parent)
        return
    if not gdata:
        messagebox.showerror("Błąd", "Nie znaleziono systemu w bazie.", parent=parent)
        return

    dlg = create_ctk_toplevel(parent)
    dlg.withdraw()
    dlg.title(f"Edytuj System: {gdata[1]}")
    dlg.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)
    dlg.resizable(True, True)
    apply_safe_geometry(dlg, parent, 600, 360)

    mf = ctk.CTkScrollableFrame(dlg)
    mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    mf.columnconfigure(1, weight=1)

    row = 0
    ctk.CTkLabel(mf, text=f"ID systemu: {gdata[0]}", font=("Segoe UI", scale_font_size(11))).grid(
        row=row, column=0, columnspan=2, pady=(0, 8), sticky="w"
    )
    row += 1

    ctk.CTkLabel(mf, text="Nazwa systemu *").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    nazwa_entry = ctk.CTkEntry(mf)
    nazwa_entry.insert(0, gdata[1] or "")
    nazwa_entry.grid(row=row, column=1, pady=8, sticky="ew")
    row += 1

    ctk.CTkLabel(mf, text="Notatki").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="nw")
    notatki_entry = ctk.CTkTextbox(mf, height=60)
    if gdata[2]:
        notatki_entry.insert("1.0", gdata[2])
    notatki_entry.grid(row=row, column=1, pady=8, sticky="ew")
    row += 1

    bf = ctk.CTkFrame(mf, fg_color="transparent")
    bf.grid(row=row, column=0, columnspan=2, pady=(16, 0))

    def _save() -> None:
        nazwa = nazwa_entry.get().strip()
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa systemu jest wymagana.", parent=dlg)
            return
        notatki = notatki_entry.get("1.0", tk.END).strip() or None
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute(
                    "UPDATE systemy_gry SET nazwa=?, notatki=? WHERE id=?",
                    (nazwa, notatki, game_id),
                )
                conn.commit()
            dlg.destroy()
            if refresh_callback:
                refresh_callback()
        except sqlite3.Error as e:
            messagebox.showerror("Błąd bazy danych", f"Nie udało się zapisać:\n{e}", parent=dlg)

    ctk.CTkButton(
        bf, text="Zapisz", command=_save, fg_color="#2E7D32", hover_color="#1B5E20", width=100,
    ).pack(side=tk.LEFT, padx=5)
    ctk.CTkButton(
        bf, text="Anuluj", command=dlg.destroy, fg_color="#666666", hover_color="#555555", width=90,
    ).pack(side=tk.LEFT, padx=5)
    dlg.after(0, dlg.deiconify)


def _open_assign_supl_dialog(
    parent: Any,
    supl_id: int,
    supl_name: str,
    refresh_callback: Optional[Callable[..., None]] = None,
) -> None:
    """Otwiera dialog do przypisania Suplementu do Systemu (system_gry_id)."""
    init_db()
    games_list = get_all_games()
    if not games_list:
        messagebox.showinfo("Brak systemów", "Nie ma żadnych Sistemów w bazie. Najpierw dodaj System.", parent=parent)
        return

    dlg = create_ctk_toplevel(parent)
    dlg.withdraw()
    dlg.title(f"Przypisz Suplement do Systemu: {supl_name}")
    dlg.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)
    dlg.resizable(True, True)
    apply_safe_geometry(dlg, parent, 520, 260)

    mf = ctk.CTkFrame(dlg)
    mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    mf.columnconfigure(1, weight=1)

    ctk.CTkLabel(
        mf, text=f"Suplement: {supl_name}",
        font=ctk.CTkFont(weight="bold"),
    ).grid(row=0, column=0, columnspan=2, pady=(0, 12), sticky="w")

    ctk.CTkLabel(mf, text="Przypisz do Systemu:").grid(row=1, column=0, pady=8, padx=(0, 10), sticky="w")
    game_var = tk.StringVar()
    game_values = [f"{g[0]} — {g[1]}" for g in games_list]
    ctk.CTkComboBox(mf, variable=game_var, values=game_values, state="readonly", width=300).grid(
        row=1, column=1, pady=8, sticky="ew"
    )

    # Pobierz aktualny system_gry_id
    try:
        with sqlite3.connect(DB_FILE) as conn:
            _row = conn.execute("SELECT system_gry_id FROM systemy_rpg WHERE id=?", (supl_id,)).fetchone()
            cur_gid = _row[0] if _row else None
    except sqlite3.Error:
        cur_gid = None
    if cur_gid:
        for v in game_values:
            if v.startswith(f"{cur_gid} — "):
                game_var.set(v)
                break

    bf = ctk.CTkFrame(mf, fg_color="transparent")
    bf.grid(row=2, column=0, columnspan=2, pady=(16, 0))

    def _save() -> None:
        val = game_var.get()
        if not val:
            messagebox.showerror("Błąd", "Wybierz System.", parent=dlg)
            return
        try:
            gid = int(val.split(" — ")[0])
        except (ValueError, IndexError):
            messagebox.showerror("Błąd", "Nieprawidłowy wybór.", parent=dlg)
            return
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute(
                    "UPDATE systemy_rpg SET system_gry_id=? WHERE id=?", (gid, supl_id)
                )
                conn.commit()
            dlg.destroy()
            if refresh_callback:
                refresh_callback()
        except sqlite3.Error as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać:\n{e}", parent=dlg)

    ctk.CTkButton(bf, text="Zapisz", command=_save, fg_color="#2E7D32", hover_color="#1B5E20", width=100).pack(side=tk.LEFT, padx=5)
    ctk.CTkButton(bf, text="Anuluj", command=dlg.destroy, fg_color="#666666", hover_color="#555555", width=90).pack(side=tk.LEFT, padx=5)
    dlg.after(0, dlg.deiconify)


def _open_assign_pg_dialog(
    parent: Any,
    pg_id: int,
    pg_name: str,
    refresh_callback: Optional[Callable[..., None]] = None,
) -> None:
    """Otwiera dialog do przypisania Podręcznika Głównego do Systemu."""
    init_db()
    games_list = get_all_games()
    dlg = create_ctk_toplevel(parent)
    dlg.withdraw()
    dlg.title(f"Przypisz PG do Systemu: {pg_name}")
    dlg.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)
    dlg.resizable(True, True)
    apply_safe_geometry(dlg, parent, 500, 280)

    mf = ctk.CTkFrame(dlg)
    mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    mf.columnconfigure(1, weight=1)

    ctk.CTkLabel(
        mf, text=f"Podręcznik Główny: {pg_name}",
        font=ctk.CTkFont(weight="bold"),
    ).grid(row=0, column=0, columnspan=2, pady=(0, 12), sticky="w")

    ctk.CTkLabel(mf, text="Przypisz do Systemu:").grid(row=1, column=0, pady=8, padx=(0, 10), sticky="w")
    game_var = tk.StringVar()
    game_values = [f"{g[0]} — {g[1]}" for g in games_list]
    game_combo = ctk.CTkComboBox(mf, variable=game_var, values=game_values, state="readonly", width=280)
    game_combo.grid(row=1, column=1, pady=8, sticky="ew")

    # Pobierz aktualny system_gry_id
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT system_gry_id FROM systemy_rpg WHERE id=?", (pg_id,))
            row = c.fetchone()
            cur_gid = row[0] if row else None
    except sqlite3.Error:
        cur_gid = None

    if cur_gid:
        for v in game_values:
            if v.startswith(f"{cur_gid} — "):
                game_var.set(v)
                break

    bf = ctk.CTkFrame(mf, fg_color="transparent")
    bf.grid(row=3, column=0, columnspan=2, pady=(16, 0))

    def _save() -> None:
        val = game_var.get()
        if not val:
            messagebox.showerror("Błąd", "Wybierz System.", parent=dlg)
            return
        try:
            gid = int(val.split(" — ")[0])
        except (ValueError, IndexError):
            messagebox.showerror("Błąd", "Nieprawidłowy wybór.", parent=dlg)
            return
        try:
            with sqlite3.connect(DB_FILE) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute(
                    "UPDATE systemy_rpg SET system_gry_id=? WHERE id=?", (gid, pg_id)
                )
                # Propaguj też do suplementów tego PG
                conn.execute(
                    "UPDATE systemy_rpg SET system_gry_id=? WHERE system_glowny_id=?",
                    (gid, pg_id),
                )
                conn.commit()
            dlg.destroy()
            if refresh_callback:
                refresh_callback()
        except sqlite3.Error as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać:\n{e}", parent=dlg)

    ctk.CTkButton(bf, text="Zapisz", command=_save, fg_color="#2E7D32", hover_color="#1B5E20", width=100).pack(side=tk.LEFT, padx=5)
    ctk.CTkButton(bf, text="Anuluj", command=dlg.destroy, fg_color="#666666", hover_color="#555555", width=90).pack(side=tk.LEFT, padx=5)
    dlg.after(0, dlg.deiconify)


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

        # Pobierz system_gry_id z PG-rodzica, aby zachować spójność hierarchii
        parent_system_gry_id: Optional[int] = None
        try:
            with sqlite3.connect(DB_FILE) as _pc:
                _row = _pc.execute(
                    "SELECT system_gry_id FROM systemy_rpg WHERE id=?", (system_glowny_id,)
                ).fetchone()
                parent_system_gry_id = _row[0] if _row else None
        except sqlite3.Error:
            pass

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
                                       waluta_sprzedazy, system_gry_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    parent_system_gry_id,
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
