# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false
import customtkinter as ctk  # type: ignore
import tkinter as tk
from tkinter import ttk
import os
import sys
import systemy_rpg
import sesje_rpg
from sesje_rpg_dialogs import dodaj_sesje_rpg
import gracze
import wydawcy
import statystyki # type: ignore
import about_dialog
import apphistory
import database_manager

# Konfiguracja CustomTkinter
ctk.set_appearance_mode("light")  # Domyślnie tryb jasny
ctk.set_default_color_theme("blue")  # Kolorystyka niebieska

APP_NAME = "Sesyjka"
APP_VERSION = "0.3.14"
START_WIDTH = 1800
START_HEIGHT = 1000

# Globalna zmienna do przechowywania współczynnika skalowania DPI
current_dpi_scale = 1.0
detected_screen_width = 1920
detected_screen_height = 1080

def setup_dpi_scaling():
    """
    Automatyczne skalowanie interfejsu dla wyższych rozdzielczości.
    Wykrywa FIZYCZNĄ rozdzielczość ekranu (ignorując skalowanie DPI Windows).
    Bazowa rozdzielczość: 1920x1080 (100% scaling)
    """
    global current_dpi_scale, detected_screen_width, detected_screen_height
    
    try:
        screen_width = 1920
        screen_height = 1080
        
        # Windows: użyj ctypes do pobrania fizycznej rozdzielczości
        if sys.platform == 'win32':
            try:
                import ctypes
                from ctypes import windll, Structure, c_long, byref
                
                # Ustaw proces jako DPI-aware aby móc wykryć fizyczną rozdzielczość
                try:
                    # Próba użycia nowszej funkcji (Windows 10+)
                    windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                except:
                    try:
                        # Fallback do starszej funkcji
                        windll.user32.SetProcessDPIAware()
                    except:
                        pass
                
                # Struktura DEVMODE do przechowywania informacji o trybie wyświetlania
                class DEVMODE(Structure):
                    _fields_ = [
                        ('dmDeviceName', ctypes.c_wchar * 32),
                        ('dmSpecVersion', ctypes.c_ushort),
                        ('dmDriverVersion', ctypes.c_ushort),
                        ('dmSize', ctypes.c_ushort),
                        ('dmDriverExtra', ctypes.c_ushort),
                        ('dmFields', ctypes.c_ulong),
                        ('dmPositionX', c_long),
                        ('dmPositionY', c_long),
                        ('dmDisplayOrientation', ctypes.c_ulong),
                        ('dmDisplayFixedOutput', ctypes.c_ulong),
                        ('dmColor', ctypes.c_short),
                        ('dmDuplex', ctypes.c_short),
                        ('dmYResolution', ctypes.c_short),
                        ('dmTTOption', ctypes.c_short),
                        ('dmCollate', ctypes.c_short),
                        ('dmFormName', ctypes.c_wchar * 32),
                        ('dmLogPixels', ctypes.c_ushort),
                        ('dmBitsPerPel', ctypes.c_ulong),
                        ('dmPelsWidth', ctypes.c_ulong),
                        ('dmPelsHeight', ctypes.c_ulong),
                        ('dmDisplayFlags', ctypes.c_ulong),
                        ('dmDisplayFrequency', ctypes.c_ulong),
                    ]
                
                # Pobierz informacje o aktualnym trybie wyświetlania
                devmode = DEVMODE()
                devmode.dmSize = ctypes.sizeof(DEVMODE)
                
                # ENUM_CURRENT_SETTINGS = -1 (aktualny tryb)
                if windll.user32.EnumDisplaySettingsW(None, -1, byref(devmode)):
                    screen_width = int(devmode.dmPelsWidth)
                    screen_height = int(devmode.dmPelsHeight)
                    print(f"[DPI Scaling] Fizyczna rozdzielczość (EnumDisplaySettings): {screen_width}x{screen_height}")
                else:
                    # Fallback: użyj GetSystemMetrics z fizycznymi wartościami
                    screen_width = windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
                    screen_height = windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN
                    print(f"[DPI Scaling] Rozdzielczość (GetSystemMetrics): {screen_width}x{screen_height}")
                    
            except Exception as e:
                print(f"[DPI Scaling] Błąd ctypes: {e}, używam fallback tkinter")
                # Fallback do tkinter
                temp_root = tk.Tk()
                temp_root.withdraw()
                screen_width = temp_root.winfo_screenwidth()
                screen_height = temp_root.winfo_screenheight()
                temp_root.destroy()
        else:
            # Linux/Mac: użyj tkinter (zazwyczaj działa poprawnie)
            temp_root = tk.Tk()
            temp_root.withdraw()
            screen_width = temp_root.winfo_screenwidth()
            screen_height = temp_root.winfo_screenheight()
            temp_root.destroy()
        
        # Zapisz wykrytą rozdzielczość
        detected_screen_width = screen_width
        detected_screen_height = screen_height
        
        # Bazowa rozdzielczość (1920x1080)
        BASE_HEIGHT = 1080
        
        # Obliczenie współczynnika skalowania na podstawie wysokości ekranu
        # (wysokość jest bardziej istotna dla czytelności)
        scale_factor = screen_height / BASE_HEIGHT
        
        # Ograniczenie zakresu skalowania (min 1.0, max 2.5)
        scale_factor = max(1.0, min(scale_factor, 2.5))
        
        # Zaokrąglenie do 0.1 dla lepszej wydajności
        scale_factor = round(scale_factor, 1)
        
        # Zapisz aktualny współczynnik skalowania
        current_dpi_scale = scale_factor
        
        # Zastosowanie skalowania tylko jeśli wykryto wyższą rozdzielczość
        if scale_factor > 1.0:
            ctk.set_widget_scaling(scale_factor)
            ctk.set_window_scaling(scale_factor)
            print(f"[DPI Scaling] Wykryto rozdzielczość: {screen_width}x{screen_height}")
            print(f"[DPI Scaling] Zastosowano skalowanie: {scale_factor}x ({int(scale_factor * 100)}%)")
        else:
            print(f"[DPI Scaling] Rozdzielczość: {screen_width}x{screen_height} (bez skalowania)")
            
    except Exception as e:
        print(f"[DPI Scaling] Błąd wykrywania rozdzielczości: {e}")
        print("[DPI Scaling] Kontynuacja z domyślnym skalowaniem")
        import traceback
        traceback.print_exc()

class SesyjkaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(f"{START_WIDTH}x{START_HEIGHT}")
        self.minsize(800, 600)
        self.dark_mode = False
        
        # Style dla ttk (dla kompatybilności z tksheet i Notebook)
        self.style = ttk.Style(self)
        self.set_modern_theme()
        
        self.create_ribbon()
        self.create_content_area()

    def set_modern_theme(self, dark=False): # type: ignore
        if dark:
            bg = '#23272e'
            fg = '#f3f6fa'
            tab_bg = '#23272e'
            tab_sel = '#31343a'
            ribbon_bg = '#31343a'
            group_bg = '#23272e'
            btn_bg = '#31343a'
            btn_fg = '#f3f6fa'
            tree_fg = '#f3f6fa'
            tree_head_fg = '#f3f6fa'
        else:
            bg = '#f3f6fa'
            fg = '#23272e'
            tab_bg = '#f3f6fa'
            tab_sel = '#e6eef7'
            ribbon_bg = '#e6eef7'
            group_bg = '#e0e7ef'
            btn_bg = '#e6eef7'
            btn_fg = '#23272e'
            tree_fg = '#23272e'
            tree_head_fg = '#23272e'
        self.configure(bg=bg)
        self.style.theme_use('clam')
        self.style.configure('TNotebook', background=tab_bg) # type: ignore
        self.style.configure('TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 12, 'bold'), background=tab_bg, foreground=fg) # type: ignore
        self.style.map('TNotebook.Tab', background=[('selected', tab_sel)]) # type: ignore
        self.style.configure('Ribbon.TFrame', background=ribbon_bg) # type: ignore
        self.style.configure('RibbonGroup.TFrame', background=group_bg, relief='solid', borderwidth=1) # type: ignore
        self.style.configure('Ribbon.TButton', background=btn_bg, foreground=btn_fg, font=('Segoe UI', 11)) # type: ignore
        self.style.configure('RibbonHeader.TLabel', background=group_bg, foreground=fg, relief='flat', borderwidth=0) # type: ignore
        # Specjalny styl dla przycisków dodaj z zielonym kolorem
        self.style.configure('Add.TButton', background=btn_bg, foreground='#00AA00', font=('Segoe UI', 11, 'bold')) # type: ignore
        # Specjalny styl dla przycisków usuń z czerwonym kolorem
        self.style.configure('Delete.TButton', background=btn_bg, foreground='#CC0000', font=('Segoe UI', 11, 'bold')) # type: ignore
        self.style.configure('TLabel', background=bg, foreground=fg) # type: ignore
        self.style.configure('TFrame', background=bg) # type: ignore
        self.style.configure('Treeview', background=bg, fieldbackground=bg, foreground=tree_fg) # type: ignore
        self.style.configure('Treeview.Heading', background=ribbon_bg, foreground=tree_head_fg, font=('Segoe UI', 10, 'bold')) # type: ignore

    def create_ribbon(self):
        # Ribbon jako CTkFrame
        ribbon = ctk.CTkFrame(self, height=100, corner_radius=0)
        ribbon.pack(side=tk.TOP, fill=tk.X)
        ribbon.pack_propagate(False)
        
        self.ribbon_groups = {}
        self.ribbon_add_buttons = {}
        
        sections = [
            ("Systemy RPG", "Dodaj System RPG", lambda: systemy_rpg.dodaj_system_rpg(self, refresh_callback=lambda **kwargs: (systemy_rpg.fill_systemy_rpg_tab(self.tabs["Systemy RPG"], dark_mode=self.dark_mode), self.refresh_statistics())), "Usuń", lambda: systemy_rpg.usun_zaznaczony_system(self.tabs["Systemy RPG"], refresh_callback=lambda **kwargs: (systemy_rpg.fill_systemy_rpg_tab(self.tabs["Systemy RPG"], dark_mode=self.dark_mode), self.refresh_statistics()))),  # type: ignore
            ("Sesje RPG", "Dodaj Sesję RPG", lambda: dodaj_sesje_rpg(self, refresh_callback=lambda **kwargs: (sesje_rpg.fill_sesje_rpg_tab(self.tabs["Sesje RPG"], dark_mode=self.dark_mode), self.refresh_statistics())), "Usuń", lambda: sesje_rpg.usun_zaznaczona_sesja(self.tabs["Sesje RPG"], refresh_callback=lambda **kwargs: (sesje_rpg.fill_sesje_rpg_tab(self.tabs["Sesje RPG"], dark_mode=self.dark_mode), self.refresh_statistics()))),  # type: ignore
            ("Gracze", "Dodaj Gracza", lambda: gracze.dodaj_gracza(self, refresh_callback=lambda **kwargs: (gracze.fill_gracze_tab(self.tabs["Gracze"], dark_mode=self.dark_mode), self.refresh_statistics())), "Usuń", lambda: gracze.usun_zaznaczony_gracza(self.tabs["Gracze"], refresh_callback=lambda **kwargs: (gracze.fill_gracze_tab(self.tabs["Gracze"], dark_mode=self.dark_mode), self.refresh_statistics()))),  # type: ignore
            ("Wydawcy", "Dodaj Wydawcę", lambda: wydawcy.dodaj_wydawce(self, refresh_callback=lambda **kwargs: (wydawcy.fill_wydawcy_tab(self.tabs["Wydawcy"], dark_mode=self.dark_mode), self.refresh_statistics())), "Usuń", lambda: wydawcy.usun_zaznaczony_wydawce(self.tabs["Wydawcy"], refresh_callback=lambda **kwargs: (wydawcy.fill_wydawcy_tab(self.tabs["Wydawcy"], dark_mode=self.dark_mode), self.refresh_statistics())))  # type: ignore
        ]
        
        for _idx, (name, _tooltip, add_func, del_label, del_func) in enumerate(sections):
            # Grupa w ribbonie
            group = ctk.CTkFrame(ribbon, corner_radius=8)
            group.pack(side=tk.LEFT, padx=12, pady=8, ipadx=8, ipady=4)
            
            # Nagłówek grupy
            label = ctk.CTkLabel(group, text=name, font=ctk.CTkFont(family='Segoe UI', size=13, weight='bold'))
            label.pack(side=tk.TOP, pady=(4, 6))
            
            # Kontener na przyciski
            btn_frame = ctk.CTkFrame(group, fg_color="transparent")
            btn_frame.pack(side=tk.TOP)
            
            # Przycisk Dodaj (zielony)
            add_btn = ctk.CTkButton(
                btn_frame, 
                text="✚ Dodaj", 
                command=add_func, 
                width=90,
                height=32,
                font=ctk.CTkFont(family='Segoe UI', size=11, weight='bold'),
                fg_color="#2E7D32",
                hover_color="#1B5E20"
            )
            add_btn.pack(side=tk.LEFT, padx=(0, 6))
            
            # Przycisk Usuń (czerwony)
            if del_label and callable(del_func):
                del_btn = ctk.CTkButton(
                    btn_frame, 
                    text=f"🗑 {del_label}", 
                    command=del_func, 
                    width=90,
                    height=32,
                    font=ctk.CTkFont(family='Segoe UI', size=11, weight='bold'),
                    fg_color="#C62828",
                    hover_color="#B71C1C"
                )
                del_btn.pack(side=tk.LEFT)
            
            self.ribbon_groups[name] = group
            self.ribbon_add_buttons[name] = add_btn
        
        # Kontener dla przycisków po prawej stronie
        right_buttons_frame = ctk.CTkFrame(ribbon, fg_color="transparent")
        right_buttons_frame.pack(side=tk.RIGHT, padx=15, pady=8)
        
        # Górny rząd - przyciski O programie i Historia wersji
        top_row = ctk.CTkFrame(right_buttons_frame, fg_color="transparent")
        top_row.pack(side=tk.TOP, pady=(0, 8))
        
        # Przycisk "O programie"
        about_btn = ctk.CTkButton(
            top_row, 
            text="ℹ️ O programie", 
            command=self.show_about,
            width=120,
            height=28,
            font=ctk.CTkFont(family='Segoe UI', size=11)
        )
        about_btn.pack(side=tk.LEFT, padx=(0, 6))
        
        # Przycisk "Historia wersji"
        history_btn = ctk.CTkButton(
            top_row, 
            text="📋 Historia wersji", 
            command=self.show_version_history,
            width=120,
            height=28,
            font=ctk.CTkFont(family='Segoe UI', size=11)
        )
        history_btn.pack(side=tk.LEFT)
        
        # Dolny rząd - Przełącznik trybu jasny/ciemny
        mode_frame = ctk.CTkFrame(right_buttons_frame, fg_color="transparent")
        mode_frame.pack(side=tk.TOP)
        
        self.mode_label = ctk.CTkLabel(
            mode_frame, 
            text="☀️ Jasny", 
            font=ctk.CTkFont(family='Segoe UI', size=11)
        )
        self.mode_label.pack(side=tk.LEFT, padx=(0, 8))
        
        self.mode_switch = ctk.CTkSwitch(
            mode_frame,
            text="",
            command=self.toggle_mode,
            width=50,
            onvalue=True,
            offvalue=False
        )
        self.mode_switch.pack(side=tk.LEFT)

    def create_content_area(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.tabs = {}
        
        # Definicja zakładek z nazwami i ikonami/prefiksami
        tab_configs = [
            ("🎲 Systemy RPG", "Systemy RPG"),
            ("⚔️ Sesje RPG", "Sesje RPG"),
            ("👥 Gracze", "Gracze"),
            ("🏢 Wydawcy", "Wydawcy"),
            ("📊 Statystyki", "Statystyki")
        ]
        
        for display_name, internal_name in tab_configs:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=display_name)
            self.tabs[internal_name] = frame # type: ignore
        # Po utworzeniu zakładek, wyświetl puste tksheet w każdej oprócz Wydawców
        import systemy_rpg, sesje_rpg, gracze, wydawcy, statystyki
        systemy_rpg.fill_systemy_rpg_tab(self.tabs["Systemy RPG"], dark_mode=getattr(self, 'dark_mode', False)) # type: ignore
        sesje_rpg.fill_sesje_rpg_tab(self.tabs["Sesje RPG"], dark_mode=getattr(self, 'dark_mode', False)) # type: ignore
        gracze.fill_gracze_tab(self.tabs["Gracze"], dark_mode=getattr(self, 'dark_mode', False)) # type: ignore
        wydawcy.fill_wydawcy_tab(self.tabs["Wydawcy"], dark_mode=getattr(self, 'dark_mode', False)) # type: ignore
        statystyki.fill_statystyki_tab(self.tabs["Statystyki"], dark_mode=getattr(self, 'dark_mode', False)) # type: ignore
        self.notebook.select(0)  # type: ignore # Startowa zakładka: Systemy RPG

    def select_tab(self, idx): # type: ignore
        self.notebook.select(idx) # type: ignore

    def toggle_mode(self):
        # Pobierz stan z przełącznika CTk
        self.dark_mode = bool(self.mode_switch.get())
        
        # Ustaw tryb CustomTkinter
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")
        
        # Aktualizuj style ttk dla kompatybilności
        self.set_modern_theme(self.dark_mode)
        
        # Aktualizuj tekst etykiety
        self.mode_label.configure(text="🌙 Ciemny" if self.dark_mode else "☀️ Jasny")
        
        # Odśwież wszystkie zakładki
        import systemy_rpg, sesje_rpg, gracze, wydawcy, statystyki
        systemy_rpg.fill_systemy_rpg_tab(self.tabs["Systemy RPG"], dark_mode=self.dark_mode)
        sesje_rpg.fill_sesje_rpg_tab(self.tabs["Sesje RPG"], dark_mode=self.dark_mode)
        gracze.fill_gracze_tab(self.tabs["Gracze"], dark_mode=self.dark_mode)
        wydawcy.fill_wydawcy_tab(self.tabs["Wydawcy"], dark_mode=self.dark_mode)
        statystyki.fill_statystyki_tab(self.tabs["Statystyki"], dark_mode=self.dark_mode)

    def show_about(self):
        """Wyświetla okno 'O programie'"""
        about_dialog.show_about_dialog(self, APP_NAME, APP_VERSION) # type: ignore

    def show_version_history(self):
        """Wyświetla okno historii wersji"""
        apphistory.show_version_history_dialog(self, APP_NAME) # type: ignore
    
    def refresh_statistics(self):
        """Odświeża zakładkę statystyk"""
        statystyki.fill_statystyki_tab(self.tabs["Statystyki"], dark_mode=self.dark_mode)

if __name__ == "__main__":
    # Inicjalizuj i zmigruj bazy danych
    database_manager.initialize_app_databases()
    
    # Skonfiguruj automatyczne skalowanie DPI dla wyższych rozdzielczości
    setup_dpi_scaling()
    
    app = SesyjkaApp()
    try:
        app.mainloop()
    finally:
        # Zamknij okno cmd jeśli uruchomiono przez .bat
        import os, sys
        if os.name == "nt":
            # Zamknij tylko jeśli to nie jest uruchomienie z IDE
            if os.getenv("PROMPT") and not sys.stdin.isatty():
                os.system("exit")
