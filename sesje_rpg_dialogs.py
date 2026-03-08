# type: ignore
import tkinter as tk
import sqlite3
import re
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Optional, Callable, Sequence, Any, Dict, List, Tuple
import customtkinter as ctk
from database_manager import get_db_path
from font_scaling import scale_font_size
from dialog_utils import apply_safe_geometry

# Stałe i podstawowe funkcje (duplikowane aby uniknąć cyklicznego importu)
DB_FILE = get_db_path("sesje_rpg.db")

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

def get_first_free_id() -> int:
    """Pobiera pierwszy wolny ID dla nowej sesji"""
    with sqlite3.connect(DB_FILE) as conn:
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
            c = conn.cursor()
            c.execute("SELECT id, nazwa FROM systemy_rpg WHERE typ = 'Podręcznik Główny' ORDER BY nazwa")
            return c.fetchall()
    except sqlite3.Error:
        return []

def get_all_players() -> List[Tuple[int, str]]:
    """Pobiera wszystkich graczy z bazy danych"""
    with sqlite3.connect(get_db_path("gracze.db")) as conn:
        c = conn.cursor()
        c.execute("SELECT id, nick FROM gracze ORDER BY nick")
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

def _apply_dark_theme_to_widget(widget: tk.Widget, dark_bg: str, dark_fg: str, 
                               dark_entry_bg: str, dark_entry_fg: str) -> None:
    """Rekurencyjnie stosuje ciemny motyw do widgetów"""
    widget_class = widget.winfo_class()
    
    try:
        if widget_class in ('Label', 'Button', 'Checkbutton', 'Radiobutton'):
            widget.configure(bg=dark_bg, fg=dark_fg)
            if widget_class in ('Checkbutton', 'Radiobutton'):
                widget.configure(selectcolor=dark_entry_bg, activebackground=dark_bg, activeforeground=dark_fg)
        elif widget_class in ('Entry', 'Text'):
            widget.configure(bg=dark_entry_bg, fg=dark_entry_fg, 
                           insertbackground=dark_entry_fg, selectbackground="#0078d4")
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
        pass

def dodaj_sesje_rpg(parent: Optional[tk.Tk] = None, refresh_callback: Optional[Callable[..., None]] = None) -> None:
    """Otwiera okno dodawania nowej sesji RPG"""
    if parent is None:
        parent = tk._default_root  # type: ignore
    
    dialog = ctk.CTkToplevel(parent)  # type: ignore
    dialog.title("Dodaj sesję RPG do bazy")
    dialog.transient(parent)  # type: ignore
    dialog.resizable(True, True)
    
    if parent is not None:
        apply_safe_geometry(dialog, parent, 640, 560)
    
    # Główna ramka z padding
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.columnconfigure(1, weight=1)
    
    # Inicjalizuj bazę danych
    init_db()
    
    # Pobierz dane z baz
    systems = get_all_systems()
    players = get_all_players()
    
    if not systems:
        messagebox.showerror("Błąd", "Brak systemów RPG w bazie. Dodaj najpierw system RPG.", parent=dialog) # type: ignore
        dialog.destroy()
        return
    
    if not players:
        messagebox.showerror("Błąd", "Brak graczy w bazie. Dodaj najpierw graczy.", parent=dialog) # type: ignore
        dialog.destroy()
        return

    # Pola formularza
    row = 0
    
    # ID Sesji
    ctk.CTkLabel(main_frame, text=f"ID Sesji: {get_first_free_id()}", font=("Segoe UI", scale_font_size(12))).grid(
        row=row, column=0, columnspan=2, pady=(0, 10), sticky="w")
    row += 1
    
    # Data sesji
    ctk.CTkLabel(main_frame, text="Data sesji *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    date_frame.grid(row=row, column=1, pady=8, sticky="ew")
    date_frame.columnconfigure(0, weight=1)
    
    date_entry = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD")
    date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
    
    def choose_date():
        # Prosty kalendarz - możesz to rozbudować
        date_str = simpledialog.askstring("Data", "Wprowadź datę (YYYY-MM-DD):", initialvalue=date_entry.get(), parent=dialog)
        if date_str:
            try:
                # Walidacja formatu daty
                datetime.strptime(date_str, "%Y-%m-%d")
                date_entry.delete(0, tk.END)
                date_entry.insert(0, date_str)
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.", parent=dialog) # type: ignore
    
    calendar_btn = ctk.CTkButton(date_frame, text="📅", command=choose_date, width=40)
    calendar_btn.grid(row=0, column=1)
    row += 1
    
    # System RPG
    ctk.CTkLabel(main_frame, text="System RPG *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    system_var = tk.StringVar(value="")
    system_combo = ctk.CTkComboBox(main_frame, variable=system_var, 
                                    values=[f"{s[1]} (ID: {s[0]})" for s in systems], 
                                    state="readonly", width=400)
    system_combo.grid(row=row, column=1, pady=8, sticky="ew")
    if systems:
        system_combo.set(f"{systems[0][1]} (ID: {systems[0][0]})")
    row += 1
    
    # Liczba graczy
    ctk.CTkLabel(main_frame, text="Liczba graczy *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    liczba_var = tk.StringVar(value="1")
    liczba_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    liczba_frame.grid(row=row, column=1, pady=8, sticky="w")
    liczba_entry = ctk.CTkEntry(liczba_frame, textvariable=liczba_var, width=60)
    liczba_entry.grid(row=0, column=0)
    row += 1
    
    # Wybór graczy
    ctk.CTkLabel(main_frame, text="Wybierz graczy *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    players_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    players_frame.grid(row=row, column=1, pady=8, sticky="ew")
    players_frame.columnconfigure(0, weight=1)
    
    # Lista wybranych graczy i przycisk
    selected_players_list: List[int] = []
    selected_players_label = ctk.CTkLabel(players_frame, text="Brak wybranych graczy", 
                                          anchor="w", fg_color=("gray85", "gray25"))
    selected_players_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    
    def update_selected_players_display():
        if not selected_players_list:
            selected_players_label.configure(text="Brak wybranych graczy")
        else:
            player_names = []
            for player_id in selected_players_list:
                for pid, pnick in players:
                    if pid == player_id:
                        player_names.append(pnick) # type: ignore
                        break
            selected_players_label.configure(text=", ".join(player_names)) # type: ignore
    
    def open_players_selection():
        # Okno wyboru graczy
        players_dialog = ctk.CTkToplevel(dialog)
        players_dialog.title("Wybierz graczy")
        players_dialog.transient(dialog)
        players_dialog.resizable(True, True)
        apply_safe_geometry(players_dialog, dialog, 420, 520)

        players_dialog.columnconfigure(0, weight=1)
        players_dialog.rowconfigure(1, weight=1)

        max_players = int(liczba_var.get())
        ctk.CTkLabel(players_dialog,
                     text=f"Wybierz dokładnie {max_players} graczy:",
                     font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12))
                     ).grid(row=0, column=0, pady=(12, 4), padx=14, sticky="w")

        scroll_frame = ctk.CTkScrollableFrame(players_dialog)
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        scroll_frame.columnconfigure(0, weight=1)

        player_vars: Dict[int, tk.BooleanVar] = {}
        player_checkboxes: Dict[int, ctk.CTkCheckBox] = {}

        def validate_players_selection() -> None:
            selected = sum(1 for v in player_vars.values() if v.get())
            max_p = int(liczba_var.get())
            if selected > max_p:
                count = 0
                for pid, v in player_vars.items():
                    if v.get():
                        count += 1
                        if count > max_p:
                            v.set(False)
            count = sum(1 for v in player_vars.values() if v.get())
            for pid, cb in player_checkboxes.items():
                cb.configure(state="disabled" if (not player_vars[pid].get() and count >= max_p) else "normal")

        def _rebuild_checkboxes() -> None:
            for w in scroll_frame.winfo_children():
                w.destroy()
            player_vars.clear()
            player_checkboxes.clear()
            for i, (player_id, player_nick) in enumerate(players):
                var = tk.BooleanVar(value=player_id in selected_players_list)
                player_vars[player_id] = var
                cb = ctk.CTkCheckBox(scroll_frame,
                                     text=f"{player_nick} (ID: {player_id})",
                                     variable=var,
                                     font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)))
                cb.grid(row=i, column=0, sticky="w", padx=6, pady=2)
                player_checkboxes[player_id] = cb
                var.trace("w", lambda *args: validate_players_selection())
            validate_players_selection()

        _rebuild_checkboxes()

        buttons_frame = ctk.CTkFrame(players_dialog, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, pady=(4, 12), padx=12, sticky="ew")
        buttons_frame.columnconfigure(1, weight=1)

        def _after_add_player(**_kw: Any) -> None:
            new_players = get_all_players()
            players.clear()
            players.extend(new_players)
            _rebuild_checkboxes()
            if hasattr(parent, 'tabs') and hasattr(parent, 'dark_mode'):
                import gracze as _gracze_mod
                _gracze_mod.fill_gracze_tab(parent.tabs["Gracze"], dark_mode=parent.dark_mode)  # type: ignore

        def _open_add_player() -> None:
            import gracze as _gracze
            _gracze.dodaj_gracza(players_dialog, refresh_callback=_after_add_player)

        ctk.CTkButton(buttons_frame, text="➕ Dodaj gracza", command=_open_add_player,
                      width=120, fg_color="#1976D2", hover_color="#1565C0",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        def save_players_selection() -> None:
            selected = [pid for pid, v in player_vars.items() if v.get()]
            expected_count = int(liczba_var.get())
            if len(selected) != expected_count:
                messagebox.showerror("Błąd", f"Wybierz dokładnie {expected_count} graczy.", parent=players_dialog)
                return
            if selected_mg_id in selected:
                messagebox.showerror("Błąd", "Mistrz Gry nie może być jednocześnie graczem.", parent=players_dialog)
                return
            selected_players_list.clear()
            selected_players_list.extend(selected)
            update_selected_players_display()
            players_dialog.destroy()

        ctk.CTkButton(buttons_frame, text="Zapisz wybór", command=save_players_selection,
                      width=110, fg_color="#2E7D32", hover_color="#1B5E20",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=2, padx=(0, 6), sticky="e")
        ctk.CTkButton(buttons_frame, text="Anuluj", command=players_dialog.destroy,
                      width=80, fg_color="#666666", hover_color="#555555",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=3, sticky="e")
    
    choose_players_btn = ctk.CTkButton(players_frame, text="Wybierz graczy...", 
                                       command=open_players_selection, width=140)
    choose_players_btn.grid(row=0, column=1)
    
    row += 1
    
    # Wybór MG
    ctk.CTkLabel(main_frame, text="Mistrz Gry *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    mg_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    mg_frame.grid(row=row, column=1, pady=8, sticky="ew")
    mg_frame.columnconfigure(0, weight=1)
    
    # Wybór MG i przycisk
    selected_mg_id: int = 0
    selected_mg_label = ctk.CTkLabel(mg_frame, text="Brak wybranego MG", 
                                     anchor="w", fg_color=("gray85", "gray25"))
    selected_mg_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    
    def update_selected_mg_display():
        if selected_mg_id == 0:
            selected_mg_label.configure(text="Brak wybranego MG")
        else:
            for pid, pnick in players:
                if pid == selected_mg_id:
                    selected_mg_label.configure(text=f"{pnick} (ID: {pid})")
                    break
    
    def open_mg_selection():
        # Okno wyboru MG
        mg_dialog = ctk.CTkToplevel(dialog)
        mg_dialog.title("Wybierz Mistrza Gry")
        mg_dialog.transient(dialog)
        mg_dialog.resizable(True, True)

        apply_safe_geometry(mg_dialog, dialog, 420, 500)

        mg_dialog.columnconfigure(0, weight=1)
        mg_dialog.rowconfigure(1, weight=1)

        ctk.CTkLabel(mg_dialog,
                     text="Wybierz Mistrza Gry:",
                     font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12))
                     ).grid(row=0, column=0, pady=(12, 4), padx=14, sticky="w")

        mg_scroll_frame = ctk.CTkScrollableFrame(mg_dialog)
        mg_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        mg_scroll_frame.columnconfigure(0, weight=1)

        mg_var = tk.IntVar(value=selected_mg_id)
        mg_radiobuttons: List[ctk.CTkRadioButton] = []

        def _rebuild_mg_radiobuttons() -> None:
            for w in mg_scroll_frame.winfo_children():
                w.destroy()
            mg_radiobuttons.clear()
            for i, (player_id, player_nick) in enumerate(players):
                rb = ctk.CTkRadioButton(mg_scroll_frame,
                                        text=f"{player_nick} (ID: {player_id})",
                                        variable=mg_var, value=player_id,
                                        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)))
                rb.grid(row=i, column=0, sticky="w", padx=6, pady=2)
                mg_radiobuttons.append(rb)

        _rebuild_mg_radiobuttons()

        buttons_frame = ctk.CTkFrame(mg_dialog, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, pady=(4, 12), padx=12, sticky="ew")
        buttons_frame.columnconfigure(1, weight=1)

        def _after_add_player_mg(**_kw: Any) -> None:
            new_players = get_all_players()
            players.clear()
            players.extend(new_players)
            _rebuild_mg_radiobuttons()
            if hasattr(parent, 'tabs') and hasattr(parent, 'dark_mode'):
                import gracze as _gracze_mod
                _gracze_mod.fill_gracze_tab(parent.tabs["Gracze"], dark_mode=parent.dark_mode)  # type: ignore

        def _open_add_player_mg() -> None:
            import gracze as _gracze
            _gracze.dodaj_gracza(mg_dialog, refresh_callback=_after_add_player_mg)

        ctk.CTkButton(buttons_frame, text="➕ Dodaj gracza", command=_open_add_player_mg,
                      width=120, fg_color="#1976D2", hover_color="#1565C0",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        def save_mg_selection() -> None:
            selected_id = mg_var.get()
            if selected_id == 0:
                messagebox.showerror("Błąd", "Wybierz Mistrza Gry.", parent=mg_dialog)
                return
            if selected_id in selected_players_list:
                messagebox.showerror("Błąd", "Mistrz Gry nie może być jednocześnie graczem.", parent=mg_dialog)
                return
            nonlocal selected_mg_id
            selected_mg_id = selected_id
            update_selected_mg_display()
            mg_dialog.destroy()

        ctk.CTkButton(buttons_frame, text="Zapisz wybór", command=save_mg_selection,
                      width=110, fg_color="#2E7D32", hover_color="#1B5E20",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=2, padx=(0, 6), sticky="e")
        ctk.CTkButton(buttons_frame, text="Anuluj", command=mg_dialog.destroy,
                      width=80, fg_color="#666666", hover_color="#555555",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=3, sticky="e")

    choose_mg_btn = ctk.CTkButton(mg_frame, text="Wybierz MG...",
                                  command=open_mg_selection, width=140)
    choose_mg_btn.grid(row=0, column=1)
    row += 1

    # Typ sesji
    ctk.CTkLabel(main_frame, text="Typ sesji *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    typ_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_frame.grid(row=row, column=1, pady=8, sticky="ew")
    
    kampania_var = tk.BooleanVar()
    jednostrzal_var = tk.BooleanVar()
    
    kampania_cb = ctk.CTkCheckBox(typ_frame, text="Kampania", variable=kampania_var)
    kampania_cb.grid(row=0, column=0, sticky="w")
    
    jednostrzal_cb = ctk.CTkCheckBox(typ_frame, text="Jednostrzał", variable=jednostrzal_var)
    jednostrzal_cb.grid(row=0, column=1, sticky="w", padx=(20, 0))
    
    def validate_typ(): # type: ignore
        # Tylko jeden typ może być zaznaczony
        if kampania_var.get() and jednostrzal_var.get():
            # Jeśli oba są zaznaczone, odznacz ten, który nie był ostatnio kliknięty
            pass  # Obsłużymy to w funkcjach poniżej
    
    def on_kampania_change():
        if kampania_var.get():
            jednostrzal_var.set(False)
    
    def on_jednostrzal_change():
        if jednostrzal_var.get():
            kampania_var.set(False)
    
    kampania_cb.configure(command=on_kampania_change)
    jednostrzal_cb.configure(command=on_jednostrzal_change)
    row += 1
    
    # Tytuł kampanii
    ctk.CTkLabel(main_frame, text="Tytuł kampanii:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    tytul_kampanii_entry = ctk.CTkEntry(main_frame, placeholder_text="Tytuł kampanii (opcjonalnie)")
    tytul_kampanii_entry.grid(row=row, column=1, pady=8, sticky="ew")
    row += 1
    
    # Tytuł przygody
    ctk.CTkLabel(main_frame, text="Tytuł przygody:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    tytul_przygody_entry = ctk.CTkEntry(main_frame, placeholder_text="Tytuł przygody (opcjonalnie)")
    tytul_przygody_entry.grid(row=row, column=1, pady=8, sticky="ew")
    row += 1
    
    # Funkcja walidacji
    def validate_form() -> bool:
        # Sprawdź datę
        try:
            datetime.strptime(date_entry.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.", parent=dialog)
            return False
        
        # Sprawdź system
        if not system_var.get():
            messagebox.showerror("Błąd", "Wybierz system RPG.", parent=dialog)
            return False
        
        # Sprawdź graczy
        expected_count = int(liczba_var.get())
        
        if len(selected_players_list) != expected_count:
            messagebox.showerror("Błąd", f"Wybierz dokładnie {expected_count} graczy.", parent=dialog)
            return False
        
        # Sprawdź MG
        if selected_mg_id == 0:
            messagebox.showerror("Błąd", "Wybierz Mistrza Gry.", parent=dialog)
            return False
        
        # Sprawdź czy MG nie jest w graczach
        if selected_mg_id in selected_players_list:
            messagebox.showerror("Błąd", "Mistrz Gry nie może być jednocześnie graczem.", parent=dialog)
            return False
        
        # Sprawdź typ sesji
        if not kampania_var.get() and not jednostrzal_var.get():
            messagebox.showerror("Błąd", "Wybierz typ sesji (Kampania lub Jednostrzał).", parent=dialog)
            return False
        
        return True
    
    # Funkcja zapisu
    def save_session():
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
                c = conn.cursor()
                
                # Dodaj sesję
                c.execute("""
                    INSERT INTO sesje_rpg (
                        data_sesji, system_id, liczba_graczy, mg_id, 
                        kampania, jednostrzal, tytul_kampanii, tytul_przygody
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date_entry.get(),
                    system_id,
                    int(liczba_var.get()),
                    selected_mg_id,
                    int(kampania_var.get()),
                    int(jednostrzal_var.get()),
                    tytul_kampanii_entry.get().strip() or None,
                    tytul_przygody_entry.get().strip() or None
                ))
                
                sesja_id = c.lastrowid
                
                # Dodaj relacje sesja-gracze
                for player_id in selected_players_list:
                    c.execute("INSERT INTO sesje_gracze (sesja_id, gracz_id) VALUES (?, ?)", 
                             (sesja_id, player_id))
                
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
    
    save_btn = ctk.CTkButton(buttons_frame, text="Zapisz", command=save_session, width=120,
                             fg_color="#2E7D32", hover_color="#1B5E20")
    save_btn.pack(side=tk.LEFT, padx=10)
    
    cancel_btn = ctk.CTkButton(buttons_frame, text="Anuluj", command=dialog.destroy, width=120,
                               fg_color="#666666", hover_color="#555555")
    cancel_btn.pack(side=tk.LEFT, padx=10)
    
    # Focus na datę
    dialog.after(100, lambda: date_entry.focus_set() if date_entry.winfo_exists() else None)

def open_edit_session_dialog(parent: tk.Widget, values: Sequence[Any], refresh_callback: Optional[Callable[..., None]] = None) -> None:
    """Otwiera okno edycji sesji RPG"""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Edytuj sesję RPG")
    dialog.transient(parent)
    dialog.resizable(True, True)
    
    apply_safe_geometry(dialog, parent, 640, 560)
    
    # Główna ramka z padding
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    main_frame.columnconfigure(1, weight=1)
    
    # Pobierz pełne dane sesji z bazy
    session_id = values[0]
    
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, data_sesji, system_id, liczba_graczy, mg_id,
                       kampania, jednostrzal, tytul_kampanii, tytul_przygody
                FROM sesje_rpg WHERE id = ?
            """, (session_id,))
            session_data = c.fetchone()
            
            # Pobierz ID graczy przypisanych do sesji
            c.execute("SELECT gracz_id FROM sesje_gracze WHERE sesja_id = ?", (session_id,))
            assigned_players = [row[0] for row in c.fetchall()]
    
    except sqlite3.Error as e:
        messagebox.showerror("Błąd bazy danych", f"Nie udało się pobrać danych sesji:\n{str(e)}", parent=dialog)
        dialog.destroy()
        return
    
    if not session_data:
        messagebox.showerror("Błąd", "Nie znaleziono sesji w bazie danych.", parent=dialog)
        dialog.destroy()
        return
    
    # Pobierz dane z baz
    systems = get_all_systems()
    players = get_all_players()
    
    if not systems:
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
    ctk.CTkLabel(main_frame, text=f"ID Sesji: {session_data[0]}", font=("Segoe UI", scale_font_size(12))).grid(
        row=row, column=0, columnspan=2, pady=(0, 10), sticky="w")
    row += 1
    
    # Data sesji
    ctk.CTkLabel(main_frame, text="Data sesji *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    date_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    date_frame.grid(row=row, column=1, pady=8, sticky="ew")
    date_frame.columnconfigure(0, weight=1)
    
    date_entry = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD")
    date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
    date_entry.insert(0, session_data[1] or "")
    
    def choose_date():
        date_str = simpledialog.askstring("Data", "Wprowadź datę (YYYY-MM-DD):", initialvalue=date_entry.get(), parent=dialog)
        if date_str:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                date_entry.delete(0, tk.END)
                date_entry.insert(0, date_str)
            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.", parent=dialog)
    
    calendar_btn = ctk.CTkButton(date_frame, text="📅", command=choose_date, width=40)
    calendar_btn.grid(row=0, column=1)
    row += 1
    
    # System RPG
    ctk.CTkLabel(main_frame, text="System RPG *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    system_var = tk.StringVar(value="")
    system_combo = ctk.CTkComboBox(main_frame, variable=system_var, 
                                    values=[f"{s[1]} (ID: {s[0]})" for s in systems], 
                                    state="readonly", width=400)
    system_combo.grid(row=row, column=1, pady=8, sticky="ew")
    
    # Znajdź i ustaw aktualny system
    current_system_id = session_data[2]
    for sys_id, sys_name in systems:
        if sys_id == current_system_id:
            system_combo.set(f"{sys_name} (ID: {sys_id})")
            break
    row += 1
    
    # Liczba graczy
    ctk.CTkLabel(main_frame, text="Liczba graczy *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    liczba_var = tk.StringVar(value=str(session_data[3]))
    liczba_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    liczba_frame.grid(row=row, column=1, pady=8, sticky="w")
    liczba_entry = ctk.CTkEntry(liczba_frame, textvariable=liczba_var, width=60)
    liczba_entry.grid(row=0, column=0)
    row += 1
    
    # Wybór graczy
    ctk.CTkLabel(main_frame, text="Wybierz graczy *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    players_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    players_frame.grid(row=row, column=1, pady=8, sticky="ew")
    players_frame.columnconfigure(0, weight=1)
    
    # Lista wybranych graczy i przycisk
    selected_players_list: List[int] = list(assigned_players)  # Ustaw aktualnych graczy
    selected_players_label = ctk.CTkLabel(players_frame, text="Brak wybranych graczy", 
                                          anchor="w", fg_color=("gray85", "gray25"))
    selected_players_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    
    def update_selected_players_display():
        if not selected_players_list:
            selected_players_label.configure(text="Brak wybranych graczy")
        else:
            player_names = []
            for pid in selected_players_list:
                for p_id, p_nick in players:
                    if p_id == pid:
                        player_names.append(p_nick)
                        break
            selected_players_label.configure(text=f"Wybrani gracze ({len(selected_players_list)}): {', '.join(player_names)}")
    
    def open_players_selection():
        # Okno wyboru graczy
        players_dialog = ctk.CTkToplevel(dialog)
        players_dialog.title("Wybierz graczy")
        players_dialog.transient(dialog)
        players_dialog.resizable(True, True)
        apply_safe_geometry(players_dialog, dialog, 420, 540)

        players_dialog.columnconfigure(0, weight=1)
        players_dialog.rowconfigure(1, weight=1)

        max_players = int(liczba_var.get())
        hdr_frame = ctk.CTkFrame(players_dialog, fg_color="transparent")
        hdr_frame.grid(row=0, column=0, pady=(12, 4), padx=14, sticky="ew")
        hdr_frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(hdr_frame,
                     text=f"Wybierz maksymalnie {max_players} graczy:",
                     font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12))
                     ).grid(row=0, column=0, sticky="w")
        count_label_var = tk.StringVar(value="")
        ctk.CTkLabel(hdr_frame, textvariable=count_label_var,
                     font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                     ).grid(row=0, column=1, padx=(12, 0), sticky="w")

        scroll_frame_edit = ctk.CTkScrollableFrame(players_dialog)
        scroll_frame_edit.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        scroll_frame_edit.columnconfigure(0, weight=1)

        player_vars_local: Dict[int, tk.BooleanVar] = {}
        player_checkboxes: Dict[int, ctk.CTkCheckBox] = {}

        def update_count_and_validate() -> None:
            selected_count = sum(1 for v in player_vars_local.values() if v.get())
            count_label_var.set(f"Wybrano: {selected_count}/{max_players}")
            for pid, cb in player_checkboxes.items():
                cb.configure(state="disabled" if (not player_vars_local[pid].get() and selected_count >= max_players) else "normal")

        def _rebuild_checkboxes_edit() -> None:
            for w in scroll_frame_edit.winfo_children():
                w.destroy()
            player_vars_local.clear()
            player_checkboxes.clear()
            for i, (player_id, player_nick) in enumerate(players):
                var = tk.BooleanVar(value=player_id in selected_players_list)
                player_vars_local[player_id] = var
                cb = ctk.CTkCheckBox(scroll_frame_edit,
                                     text=f"{player_nick} (ID: {player_id})",
                                     variable=var,
                                     font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)))
                cb.grid(row=i, column=0, sticky="w", padx=6, pady=2)
                player_checkboxes[player_id] = cb
                var.trace("w", lambda *args: update_count_and_validate())
            update_count_and_validate()

        _rebuild_checkboxes_edit()

        buttons_frame = ctk.CTkFrame(players_dialog, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, pady=(4, 12), padx=12, sticky="ew")
        buttons_frame.columnconfigure(1, weight=1)

        def _after_add_player_edit(**_kw: Any) -> None:
            new_players = get_all_players()
            players.clear()
            players.extend(new_players)
            _rebuild_checkboxes_edit()
            if hasattr(parent, 'tabs') and hasattr(parent, 'dark_mode'):
                import gracze as _gracze_mod
                _gracze_mod.fill_gracze_tab(parent.tabs["Gracze"], dark_mode=parent.dark_mode)  # type: ignore

        def _open_add_player_edit() -> None:
            import gracze as _gracze
            _gracze.dodaj_gracza(players_dialog, refresh_callback=_after_add_player_edit)

        ctk.CTkButton(buttons_frame, text="➕ Dodaj gracza", command=_open_add_player_edit,
                      width=120, fg_color="#1976D2", hover_color="#1565C0",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        def save_players_selection() -> None:
            selected_ids = [pid for pid, v in player_vars_local.items() if v.get()]
            if len(selected_ids) > max_players:
                messagebox.showerror("Błąd", f"Wybierz maksymalnie {max_players} graczy.", parent=players_dialog)
                return
            if len(selected_ids) == 0:
                messagebox.showerror("Błąd", "Wybierz co najmniej jednego gracza.", parent=players_dialog)
                return
            if selected_mg_id in selected_ids:
                messagebox.showerror("Błąd", "Mistrz Gry nie może być jednocześnie graczem.", parent=players_dialog)
                return
            selected_players_list.clear()
            selected_players_list.extend(selected_ids)
            update_selected_players_display()
            players_dialog.destroy()

        ctk.CTkButton(buttons_frame, text="Zapisz wybór", command=save_players_selection,
                      width=110, fg_color="#2E7D32", hover_color="#1B5E20",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=2, padx=(0, 6), sticky="e")
        ctk.CTkButton(buttons_frame, text="Anuluj", command=players_dialog.destroy,
                      width=80, fg_color="#666666", hover_color="#555555",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=3, sticky="e")
    
    choose_players_btn = ctk.CTkButton(players_frame, text="Wybierz graczy...", 
                                       command=open_players_selection, width=140)
    choose_players_btn.grid(row=0, column=1)
    
    # Ustaw początkowy wyświetlacz graczy
    update_selected_players_display()
    
    row += 1
    
    # Wybór MG
    ctk.CTkLabel(main_frame, text="Mistrz Gry *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    mg_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    mg_frame.grid(row=row, column=1, pady=8, sticky="ew")
    mg_frame.columnconfigure(0, weight=1)
    
    # Lista wybranego MG i przycisk
    selected_mg_id: int = session_data[4]  # Ustaw aktualnego MG
    selected_mg_label = ctk.CTkLabel(mg_frame, text="Brak wybranego MG", 
                                     anchor="w", fg_color=("gray85", "gray25"))
    selected_mg_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    
    def update_selected_mg_display():
        if selected_mg_id == 0:
            selected_mg_label.configure(text="Brak wybranego MG")
        else:
            for pid, pnick in players:
                if pid == selected_mg_id:
                    selected_mg_label.configure(text=f"{pnick} (ID: {pid})")
                    break
    
    def open_mg_selection():
        # Okno wyboru MG
        mg_dialog = ctk.CTkToplevel(dialog)
        mg_dialog.title("Wybierz Mistrza Gry")
        mg_dialog.transient(dialog)
        mg_dialog.resizable(True, True)

        apply_safe_geometry(mg_dialog, dialog, 420, 500)

        mg_dialog.columnconfigure(0, weight=1)
        mg_dialog.rowconfigure(1, weight=1)

        ctk.CTkLabel(mg_dialog,
                     text="Wybierz Mistrza Gry:",
                     font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(12))
                     ).grid(row=0, column=0, pady=(12, 4), padx=14, sticky="w")

        mg_scroll_frame_edit = ctk.CTkScrollableFrame(mg_dialog)
        mg_scroll_frame_edit.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        mg_scroll_frame_edit.columnconfigure(0, weight=1)

        mg_var = tk.IntVar(value=selected_mg_id)
        mg_radiobuttons_edit: List[ctk.CTkRadioButton] = []

        def _rebuild_mg_radiobuttons_edit() -> None:
            for w in mg_scroll_frame_edit.winfo_children():
                w.destroy()
            mg_radiobuttons_edit.clear()
            for i, (player_id, player_nick) in enumerate(players):
                rb = ctk.CTkRadioButton(mg_scroll_frame_edit,
                                        text=f"{player_nick} (ID: {player_id})",
                                        variable=mg_var, value=player_id,
                                        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)))
                rb.grid(row=i, column=0, sticky="w", padx=6, pady=2)
                mg_radiobuttons_edit.append(rb)

        _rebuild_mg_radiobuttons_edit()

        buttons_frame = ctk.CTkFrame(mg_dialog, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, pady=(4, 12), padx=12, sticky="ew")
        buttons_frame.columnconfigure(1, weight=1)

        def _after_add_player_mg_edit(**_kw: Any) -> None:
            new_players = get_all_players()
            players.clear()
            players.extend(new_players)
            _rebuild_mg_radiobuttons_edit()
            if hasattr(parent, 'tabs') and hasattr(parent, 'dark_mode'):
                import gracze as _gracze_mod
                _gracze_mod.fill_gracze_tab(parent.tabs["Gracze"], dark_mode=parent.dark_mode)  # type: ignore

        def _open_add_player_mg_edit() -> None:
            import gracze as _gracze
            _gracze.dodaj_gracza(mg_dialog, refresh_callback=_after_add_player_mg_edit)

        ctk.CTkButton(buttons_frame, text="➕ Dodaj gracza", command=_open_add_player_mg_edit,
                      width=120, fg_color="#1976D2", hover_color="#1565C0",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        def save_mg_selection() -> None:
            selected_id = mg_var.get()
            if selected_id == 0:
                messagebox.showerror("Błąd", "Wybierz Mistrza Gry.", parent=mg_dialog)
                return
            if selected_id in selected_players_list:
                messagebox.showerror("Błąd", "Mistrz Gry nie może być jednocześnie graczem.", parent=mg_dialog)
                return
            nonlocal selected_mg_id
            selected_mg_id = selected_id
            update_selected_mg_display()
            mg_dialog.destroy()

        ctk.CTkButton(buttons_frame, text="Zapisz wybór", command=save_mg_selection,
                      width=110, fg_color="#2E7D32", hover_color="#1B5E20",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=2, padx=(0, 6), sticky="e")
        ctk.CTkButton(buttons_frame, text="Anuluj", command=mg_dialog.destroy,
                      width=80, fg_color="#666666", hover_color="#555555",
                      font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11))
                      ).grid(row=0, column=3, sticky="e")
    
    choose_mg_btn = ctk.CTkButton(mg_frame, text="Wybierz MG...", 
                                  command=open_mg_selection, width=140)
    choose_mg_btn.grid(row=0, column=1)
    
    # Ustaw początkowy wyświetlacz MG
    update_selected_mg_display()
    row += 1
    
    # Typ sesji
    ctk.CTkLabel(main_frame, text="Typ sesji *:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    typ_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    typ_frame.grid(row=row, column=1, pady=8, sticky="ew")
    
    kampania_var = tk.BooleanVar(value=bool(session_data[5]))
    jednostrzal_var = tk.BooleanVar(value=bool(session_data[6]))
    
    kampania_cb = ctk.CTkCheckBox(typ_frame, text="Kampania", variable=kampania_var)
    kampania_cb.grid(row=0, column=0, sticky="w")
    
    jednostrzal_cb = ctk.CTkCheckBox(typ_frame, text="Jednostrzał", variable=jednostrzal_var)
    jednostrzal_cb.grid(row=0, column=1, sticky="w", padx=(20, 0))
    
    def on_kampania_change():
        if kampania_var.get():
            jednostrzal_var.set(False)
    
    def on_jednostrzal_change():
        if jednostrzal_var.get():
            kampania_var.set(False)
    
    kampania_cb.configure(command=on_kampania_change)
    jednostrzal_cb.configure(command=on_jednostrzal_change)
    row += 1
    
    # Tytuł kampanii
    ctk.CTkLabel(main_frame, text="Tytuł kampanii:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    tytul_kampanii_entry = ctk.CTkEntry(main_frame, placeholder_text="Tytuł kampanii (opcjonalnie)")
    tytul_kampanii_entry.grid(row=row, column=1, pady=8, sticky="ew")
    tytul_kampanii_entry.insert(0, session_data[7] or "")
    row += 1
    
    # Tytuł przygody
    ctk.CTkLabel(main_frame, text="Tytuł przygody:").grid(row=row, column=0, pady=8, padx=(0, 10), sticky="w")
    tytul_przygody_entry = ctk.CTkEntry(main_frame, placeholder_text="Tytuł przygody (opcjonalnie)")
    tytul_przygody_entry.grid(row=row, column=1, pady=8, sticky="ew")
    tytul_przygody_entry.insert(0, session_data[8] or "")
    row += 1
    
    # Funkcja walidacji
    def validate_form() -> bool:
        # Sprawdź datę
        try:
            datetime.strptime(date_entry.get(), "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.", parent=dialog)
            return False
        
        # Sprawdź system
        if not system_var.get():
            messagebox.showerror("Błąd", "Wybierz system RPG.", parent=dialog)
            return False
        
        # Sprawdź MG
        if selected_mg_id == 0:
            messagebox.showerror("Błąd", "Wybierz Mistrza Gry.", parent=dialog)
            return False
        
        # Sprawdź czy MG nie jest w graczach
        if selected_mg_id in selected_players_list:
            messagebox.showerror("Błąd", "Mistrz Gry nie może być jednocześnie graczem.", parent=dialog)
            return False
        
        # Sprawdź typ sesji
        if not kampania_var.get() and not jednostrzal_var.get():
            messagebox.showerror("Błąd", "Wybierz typ sesji (Kampania lub Jednostrzał).", parent=dialog)
            return False
        
        return True
    
    # Funkcja zapisu
    def save_session():
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
                c = conn.cursor()
                
                # Aktualizuj sesję
                c.execute("""
                    UPDATE sesje_rpg SET
                        data_sesji = ?, system_id = ?, liczba_graczy = ?, mg_id = ?,
                        kampania = ?, jednostrzal = ?, tytul_kampanii = ?, tytul_przygody = ?
                    WHERE id = ?
                """, (
                    date_entry.get(),
                    system_id,
                    len(selected_players_list),
                    selected_mg_id,
                    int(kampania_var.get()),
                    int(jednostrzal_var.get()),
                    tytul_kampanii_entry.get().strip() or None,
                    tytul_przygody_entry.get().strip() or None,
                    session_id
                ))
                
                # Usuń stare relacje sesja-gracze
                c.execute("DELETE FROM sesje_gracze WHERE sesja_id = ?", (session_id,))
                
                # Dodaj nowe relacje sesja-gracze
                for player_id in selected_players_list:
                    c.execute("INSERT INTO sesje_gracze (sesja_id, gracz_id) VALUES (?, ?)", 
                             (session_id, player_id))
                
                conn.commit()
            
            messagebox.showinfo("Sukces", "Sesja została zaktualizowana.", parent=dialog)
            
            # Odśwież widok jeśli callback istnieje
            if refresh_callback:
                refresh_callback()
            
            dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zaktualizować sesji:\n{str(e)}", parent=dialog) # type: ignore
    
    # Przyciski
    buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    buttons_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
    
    save_btn = ctk.CTkButton(buttons_frame, text="Zapisz", command=save_session, width=120,
                             fg_color="#2E7D32", hover_color="#1B5E20")
    save_btn.pack(side=tk.LEFT, padx=10)
    
    cancel_btn = ctk.CTkButton(buttons_frame, text="Anuluj", command=dialog.destroy, width=120,
                               fg_color="#666666", hover_color="#555555")
    cancel_btn.pack(side=tk.LEFT, padx=10)
    
    # Focus na datę
    dialog.after(100, lambda: date_entry.focus_set() if date_entry.winfo_exists() else None)
