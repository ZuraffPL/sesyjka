from __future__ import annotations
from typing import Optional
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
import statystyki  # type: ignore
import about_dialog
import apphistory
import help_dialog
import splash_screen
import database_manager
import font_scaling
from font_scaling import scale_font_size
import settings as app_settings
import logging

_log = logging.getLogger(__name__)

# Konfiguracja CustomTkinter
ctk.set_appearance_mode("light")  # Domyślnie tryb jasny
ctk.set_default_color_theme("blue")  # Kolorystyka niebieska

APP_NAME = "Sesyjka"
APP_VERSION = "0.4.22"
START_WIDTH = 1800
START_HEIGHT = 920

# Ustawienia wczytane z pliku – wypełniane przed startem aplikacji
_initial_dark_mode: bool = False
_initial_geometry: dict[str, int] = {"width": START_WIDTH, "height": START_HEIGHT}

# Globalna zmienna do przechowywania współczynnika skalowania DPI
current_dpi_scale = 1.0
detected_screen_width = 1920
detected_screen_height = 1080


def setup_dpi_scaling() -> None:
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
                except Exception:
                    _log.debug("SetProcessDpiAwareness niedostępne", exc_info=True)
                    try:
                        # Fallback do starszej funkcji
                        windll.user32.SetProcessDPIAware()
                    except Exception:
                        _log.debug("SetProcessDPIAware (fallback) niedostępne", exc_info=True)

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
                    print(
                        f"[DPI Scaling] Fizyczna rozdzielczość (EnumDisplaySettings): "
                        f"{screen_width}x{screen_height}"
                    )
                else:
                    # Fallback: użyj GetSystemMetrics z fizycznymi wartościami
                    screen_width = windll.user32.GetSystemMetrics(0)  # SM_CXSCREEN
                    screen_height = windll.user32.GetSystemMetrics(1)  # SM_CYSCREEN
                    print(
                        f"[DPI Scaling] Rozdzielczość (GetSystemMetrics):"
                        f" {screen_width}x{screen_height}"
                    )

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
            print(
                f"[DPI Scaling] Zastosowano skalowanie: {scale_factor}x"
                f" ({int(scale_factor * 100)}%)"
            )
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

        # Pobierz łączne skalowanie okna CTk (nasze custom + DPI systemu)
        try:
            self._total_window_scale = self._apply_window_scaling(10000) / 10000.0
        except Exception:
            self._total_window_scale = current_dpi_scale if current_dpi_scale > 1.0 else 1.0
        scale = self._total_window_scale
        print(f"[Window] Total CTk window scaling: {scale}")

        # Rozmiar bazowy okna (wartości logiczne CTk)
        # CTk automatycznie przemnoży je przez window_scaling,
        # więc 1800x920 na 1080p = 1800px, a na 1440p (1.3x) = 2340px
        w = int(_initial_geometry.get("width", START_WIDTH))
        h = int(_initial_geometry.get("height", START_HEIGHT))

        # Wymiary ekranu w pikselach fizycznych
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        TASKBAR_MARGIN = 48  # miejsce na pasek zadań Windows

        # Ogranicz rozmiar bazowy, aby po przeskalowaniu nie wychodził poza ekran
        max_w = int((screen_w - 20) / scale) if scale > 1.0 else screen_w - 20
        max_h = (
            int((screen_h - TASKBAR_MARGIN) / scale) if scale > 1.0 else screen_h - TASKBAR_MARGIN
        )
        w = min(w, max_w)
        h = min(h, max_h)

        # Oblicz fizyczny rozmiar okna (do centrowania)
        phys_w = int(w * scale)
        phys_h = int(h * scale)
        x = max(0, (screen_w - phys_w) // 2)
        y = max(0, (screen_h - phys_h - TASKBAR_MARGIN) // 2)
        print(
            f"[Window] Base: {w}x{h}, Physical: {phys_w}x{phys_h}, Screen: {screen_w}x{screen_h}"
        )
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.minsize(800, 600)
        self.dark_mode = _initial_dark_mode

        # Rozmiar zapisywany przed zamknięciem
        self.saved_geometry: dict[str, int] = {}
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Ustaw tryb CTk zgodnie z zapisanym ustawieniem
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")

        # Style dla ttk (dla kompatybilności z tksheet i Notebook)
        self.style = ttk.Style(self)
        self.set_modern_theme(self.dark_mode)

        self.create_ribbon()
        self.create_content_area()

    def report_callback_exception(self, exc: type, val: BaseException, tb: object) -> None:  # type: ignore
        """Cicho ignoruje TclError 'bad window path' (po destroy widgetów przy rebuild tabeli)."""
        import _tkinter  # type: ignore

        if isinstance(val, _tkinter.TclError) and "bad window path" in str(val):  # type: ignore
            _log.debug("Ignorowanie TclError 'bad window path': %s", val)
            return
        super().report_callback_exception(exc, val, tb)  # type: ignore

    def set_modern_theme(self, dark: bool = False) -> None:
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
        self.style.configure('TNotebook', background=tab_bg)  # type: ignore
        self.style.configure('TNotebook.Tab', padding=[20, 10], font=('Segoe UI', scale_font_size(12), 'bold'), background=tab_bg, foreground=fg)  # type: ignore
        self.style.map('TNotebook.Tab', background=[('selected', tab_sel)])  # type: ignore
        self.style.configure('Ribbon.TFrame', background=ribbon_bg)  # type: ignore
        self.style.configure('RibbonGroup.TFrame', background=group_bg, relief='solid', borderwidth=1)  # type: ignore
        self.style.configure('Ribbon.TButton', background=btn_bg, foreground=btn_fg, font=('Segoe UI', scale_font_size(11)))  # type: ignore
        self.style.configure('RibbonHeader.TLabel', background=group_bg, foreground=fg, relief='flat', borderwidth=0)  # type: ignore
        # Specjalny styl dla przycisków dodaj z zielonym kolorem
        self.style.configure('Add.TButton', background=btn_bg, foreground='#00AA00', font=('Segoe UI', scale_font_size(11), 'bold'))  # type: ignore
        # Specjalny styl dla przycisków usuń z czerwonym kolorem
        self.style.configure('Delete.TButton', background=btn_bg, foreground='#CC0000', font=('Segoe UI', scale_font_size(11), 'bold'))  # type: ignore
        self.style.configure('TLabel', background=bg, foreground=fg)  # type: ignore
        self.style.configure('TFrame', background=bg)  # type: ignore
        self.style.configure('Treeview', background=bg, fieldbackground=bg, foreground=tree_fg)  # type: ignore
        self.style.configure('Treeview.Heading', background=ribbon_bg, foreground=tree_head_fg, font=('Segoe UI', scale_font_size(10), 'bold'))  # type: ignore

    def create_ribbon(self) -> None:
        # Ribbon jako CTkFrame
        self.ribbon = ctk.CTkFrame(self, height=100, corner_radius=0)
        self.ribbon.pack(side=tk.TOP, fill=tk.X)
        self.ribbon.pack_propagate(False)

        self.ribbon_groups = {}
        self.ribbon_add_buttons = {}

        sections = [
            ("Systemy RPG", "Dodaj System RPG", lambda: systemy_rpg.dodaj_system_rpg(self, refresh_callback=lambda **kwargs: (systemy_rpg.fill_systemy_rpg_tab(self.tabs["Systemy RPG"], dark_mode=self.dark_mode), self.refresh_statistics())), "Usuń", lambda: systemy_rpg.usun_zaznaczony_system(self.tabs["Systemy RPG"], refresh_callback=lambda **kwargs: (systemy_rpg.fill_systemy_rpg_tab(self.tabs["Systemy RPG"], dark_mode=self.dark_mode), self.refresh_statistics()))),  # type: ignore
            ("Sesje RPG", "Dodaj Sesję RPG", lambda: dodaj_sesje_rpg(self, refresh_callback=lambda **kwargs: (sesje_rpg.fill_sesje_rpg_tab(self.tabs["Sesje RPG"], dark_mode=self.dark_mode), self.refresh_statistics())), "Usuń", lambda: sesje_rpg.usun_zaznaczona_sesja(self.tabs["Sesje RPG"], refresh_callback=lambda **kwargs: (sesje_rpg.fill_sesje_rpg_tab(self.tabs["Sesje RPG"], dark_mode=self.dark_mode), self.refresh_statistics()))),  # type: ignore
            ("Gracze", "Dodaj Gracza", lambda: gracze.dodaj_gracza(self, refresh_callback=lambda **kwargs: (gracze.fill_gracze_tab(self.tabs["Gracze"], dark_mode=self.dark_mode), self.refresh_statistics())), "Usuń", lambda: gracze.usun_zaznaczony_gracza(self.tabs["Gracze"], refresh_callback=lambda **kwargs: (gracze.fill_gracze_tab(self.tabs["Gracze"], dark_mode=self.dark_mode), self.refresh_statistics()))),  # type: ignore
            ("Wydawcy", "Dodaj Wydawcę", lambda: wydawcy.dodaj_wydawce(self, refresh_callback=lambda **kwargs: (wydawcy.fill_wydawcy_tab(self.tabs["Wydawcy"], dark_mode=self.dark_mode), self.refresh_statistics())), "Usuń", lambda: wydawcy.usun_zaznaczony_wydawce(self.tabs["Wydawcy"], refresh_callback=lambda **kwargs: (wydawcy.fill_wydawcy_tab(self.tabs["Wydawcy"], dark_mode=self.dark_mode), self.refresh_statistics()))),  # type: ignore
        ]

        for _idx, (name, _tooltip, add_func, del_label, del_func) in enumerate(sections):
            # Grupa w ribbonie
            group = ctk.CTkFrame(self.ribbon, corner_radius=8)
            group.pack(side=tk.LEFT, padx=12, pady=8, ipadx=8, ipady=4)

            # Nagłówek grupy
            label = ctk.CTkLabel(
                group,
                text=name,
                font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(13), weight='bold'),
            )
            label.pack(side=tk.TOP, pady=(4, 6))

            # Kontener na przyciski
            btn_frame = ctk.CTkFrame(group, fg_color="transparent")
            btn_frame.pack(side=tk.TOP)

            # Dla Systemów RPG: najpierw "Dodaj System" (niebieski), potem "Dodaj PG/Suplement" (zielony)
            if name == "Systemy RPG":
                add_sys_btn = ctk.CTkButton(
                    btn_frame,
                    text="✚ Dodaj System",
                    command=lambda: systemy_rpg.open_add_game_dialog(
                        self,
                        refresh_callback=lambda **kwargs: (  # type: ignore[arg-type]
                            systemy_rpg.fill_systemy_rpg_tab(
                                self.tabs["Systemy RPG"], dark_mode=self.dark_mode
                            ),
                            self.refresh_statistics(),
                        ),
                    ),
                    width=110,
                    height=32,
                    font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(11), weight='bold'),
                    fg_color="#1565C0",
                    hover_color="#0D47A1",
                )
                add_sys_btn.pack(side=tk.LEFT, padx=(0, 6))

            # Przycisk Dodaj (zielony)
            add_btn = ctk.CTkButton(
                btn_frame,
                text="✚ Dodaj PG/Suplement" if name == "Systemy RPG" else "✚ Dodaj",
                command=add_func,
                width=130 if name == "Systemy RPG" else 90,
                height=32,
                font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(11), weight='bold'),
                fg_color="#2E7D32",
                hover_color="#1B5E20",
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
                    font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(11), weight='bold'),
                    fg_color="#C62828",
                    hover_color="#B71C1C",
                )
                del_btn.pack(side=tk.LEFT)

            self.ribbon_groups[name] = group
            self.ribbon_add_buttons[name] = add_btn

        # Kontener dla przycisków po prawej stronie
        right_buttons_frame = ctk.CTkFrame(self.ribbon, fg_color="transparent")
        right_buttons_frame.pack(side=tk.RIGHT, padx=15, pady=8)

        # Górny rząd - przyciski O programie i Historia wersji
        top_row = ctk.CTkFrame(right_buttons_frame, fg_color="transparent")
        top_row.pack(side=tk.TOP, pady=(0, 4))

        # Przycisk "Pomoc"
        help_btn = ctk.CTkButton(
            top_row,
            text="❓ Pomoc",
            command=self.show_help,
            width=100,
            height=28,
            font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(11)),
        )
        help_btn.pack(side=tk.LEFT, padx=(0, 6))

        # Przycisk "O programie"
        about_btn = ctk.CTkButton(
            top_row,
            text="ℹ️ O programie",
            command=self.show_about,
            width=120,
            height=28,
            font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(11)),
        )
        about_btn.pack(side=tk.LEFT, padx=(0, 6))

        # Przycisk "Historia wersji"
        history_btn = ctk.CTkButton(
            top_row,
            text="📋 Historia wersji",
            command=self.show_version_history,
            width=120,
            height=28,
            font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(11)),
        )
        history_btn.pack(side=tk.LEFT)

        # Środkowy rząd - Skalowanie fontów
        font_scale_frame = ctk.CTkFrame(right_buttons_frame, fg_color="transparent")
        font_scale_frame.pack(side=tk.TOP, pady=(0, 4))

        font_label = ctk.CTkLabel(
            font_scale_frame,
            text="🔤 Czcionka:",
            font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(10)),
        )
        font_label.pack(side=tk.LEFT, padx=(0, 4))

        self.font_scale_value_label = ctk.CTkLabel(
            font_scale_frame,
            text=f"{int(font_scaling.get_font_scale_factor() * 100)}%",
            font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(10), weight='bold'),
            width=45,
        )
        self.font_scale_value_label.pack(side=tk.LEFT, padx=(0, 4))

        self.font_scale_slider = ctk.CTkSlider(
            font_scale_frame,
            from_=80,
            to=120,
            number_of_steps=8,
            command=self.on_font_scale_change,
            width=150,
        )
        self.font_scale_slider.set(int(font_scaling.get_font_scale_factor() * 100))
        self.font_scale_slider.pack(side=tk.LEFT)

        # Dolny rząd - Przełącznik trybu jasny/ciemny
        mode_frame = ctk.CTkFrame(right_buttons_frame, fg_color="transparent")
        mode_frame.pack(side=tk.TOP)

        self.mode_label = ctk.CTkLabel(
            mode_frame,
            text="🌙 Ciemny" if self.dark_mode else "☀️ Jasny",
            font=ctk.CTkFont(family='Segoe UI', size=scale_font_size(11)),
        )
        self.mode_label.pack(side=tk.LEFT, padx=(0, 8))

        self.mode_switch = ctk.CTkSwitch(
            mode_frame, text="", command=self.toggle_mode, width=50, onvalue=True, offvalue=False
        )
        if self.dark_mode:
            self.mode_switch.select()
        self.mode_switch.pack(side=tk.LEFT)

    def create_content_area(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.tabs = {}

        # Definicja zakładek z nazwami i ikonami/prefiksami
        tab_configs = [
            ("🎲 Systemy RPG", "Systemy RPG"),
            ("⚔️ Sesje RPG", "Sesje RPG"),
            ("👥 Gracze", "Gracze"),
            ("🏢 Wydawcy", "Wydawcy"),
            ("📊 Statystyki", "Statystyki"),
        ]

        for display_name, internal_name in tab_configs:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=display_name)
            self.tabs[internal_name] = frame  # type: ignore
        # Po utworzeniu zakładek, wyświetl puste tksheet w każdej oprócz Wydawców
        import systemy_rpg, sesje_rpg, gracze, wydawcy, statystyki

        systemy_rpg.fill_systemy_rpg_tab(self.tabs["Systemy RPG"], dark_mode=getattr(self, 'dark_mode', False))  # type: ignore
        sesje_rpg.fill_sesje_rpg_tab(self.tabs["Sesje RPG"], dark_mode=getattr(self, 'dark_mode', False))  # type: ignore
        gracze.fill_gracze_tab(self.tabs["Gracze"], dark_mode=getattr(self, 'dark_mode', False))  # type: ignore
        wydawcy.fill_wydawcy_tab(self.tabs["Wydawcy"], dark_mode=getattr(self, 'dark_mode', False))  # type: ignore
        statystyki.fill_statystyki_tab(self.tabs["Statystyki"], dark_mode=getattr(self, 'dark_mode', False))  # type: ignore
        self.notebook.select(0)  # type: ignore # Startowa zakładka: Systemy RPG
        self._dirty_tabs: set[str] = set()
        self._font_scale_timer: Optional[str] = None  # type: ignore
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def select_tab(self, idx: int) -> None:
        self.notebook.select(idx)  # type: ignore

    # ── Lazy rebuild zakładek ─────────────────────────────────────────────────

    def _get_active_tab_name(self) -> Optional[str]:  # type: ignore
        try:
            idx = self.notebook.index(self.notebook.select())
            return list(self.tabs.keys())[idx]
        except Exception:
            return None

    def _on_tab_changed(self, _event: object = None) -> None:
        """Przy przełączeniu zakładki odświeża ją, jeśli jest oznaczona jako brudna."""
        self._refresh_active_tab()

    def _refresh_active_tab(self) -> None:
        name = self._get_active_tab_name()
        if name and name in self._dirty_tabs:
            self._rebuild_tab(name)
            self._dirty_tabs.discard(name)

    def _rebuild_tab(self, name: str) -> None:
        import systemy_rpg, sesje_rpg, gracze, wydawcy, statystyki

        dm = self.dark_mode
        tab = self.tabs[name]
        if name == "Systemy RPG":
            systemy_rpg.fill_systemy_rpg_tab(tab, dark_mode=dm)
        elif name == "Sesje RPG":
            sesje_rpg.fill_sesje_rpg_tab(tab, dark_mode=dm)
        elif name == "Gracze":
            gracze.fill_gracze_tab(tab, dark_mode=dm)
        elif name == "Wydawcy":
            wydawcy.fill_wydawcy_tab(tab, dark_mode=dm)
        elif name == "Statystyki":
            statystyki.fill_statystyki_tab(tab, dark_mode=dm)

    # ── Tryb jasny/ciemny ────────────────────────────────────────────────────

    def toggle_mode(self) -> None:
        self.dark_mode = bool(self.mode_switch.get())
        # Ukryj zawartość okna (przezroczystość) zamiast withdraw – okno zostaje na miejscu
        self.attributes('-alpha', 0)
        try:
            ctk.set_appearance_mode("dark" if self.dark_mode else "light")
            self.set_modern_theme(self.dark_mode)
            self.mode_label.configure(text="🌙 Ciemny" if self.dark_mode else "☀️ Jasny")
            self._dirty_tabs = set(self.tabs.keys())
            self._refresh_active_tab()
        finally:
            self.update_idletasks()  # wyrenderuj wszystko zanim okno wróci
            self.attributes('-alpha', 1)

    # ── Skalowanie czcionek (debounce) ────────────────────────────────────────

    def on_font_scale_change(self, value: float) -> None:
        """Aktualizuje etykietę natychmiast; rzeczywisty rebuild odkłada o 250 ms."""
        scale_percent = int(value)
        font_scaling.set_font_scale_factor(scale_percent / 100.0)

        # Zaktualizuj etykietę od razu (bez rebuild)
        try:
            self.font_scale_value_label.configure(text=f"{scale_percent}%")
        except Exception:
            _log.debug("font_scale_value_label niedostępna przy aktualizacji", exc_info=True)

        # Anuluj poprzedni timer i zaplanuj nowy
        if self._font_scale_timer is not None:
            try:
                self.after_cancel(self._font_scale_timer)
            except Exception:
                _log.debug("after_cancel nie powiodło się", exc_info=True)
        self._font_scale_timer = self.after(250, lambda v=scale_percent: self._apply_font_scale(v))  # type: ignore

    def _apply_font_scale(self, scale_percent: int) -> None:
        """Wykonuje pełny rebuild po zatrzymaniu slidera."""
        self._font_scale_timer = None

        # Użyj przezroczystości zamiast withdraw – okno zostaje na miejscu, brak flickera taskbara
        self.attributes('-alpha', 0)
        try:
            if hasattr(self, 'ribbon'):
                self.ribbon.destroy()
            self.notebook.pack_forget()
            self.create_ribbon()
            self.notebook.pack(fill=tk.BOTH, expand=True)
            self.font_scale_slider.set(scale_percent)
            self.font_scale_value_label.configure(text=f"{scale_percent}%")
            # Rebuild zakładki wewnątrz bloku try – przed deiconify()
            self._dirty_tabs = set(self.tabs.keys())
            self._refresh_active_tab()
        finally:
            self.update_idletasks()  # wyrenderuj wszystko zanim okno wróci
            self.attributes('-alpha', 1)

    def show_help(self) -> None:
        """Wyświetla okno instrukcji obsługi"""
        help_dialog.show_help_dialog(self)  # type: ignore

    def show_about(self) -> None:
        """Wyświetla okno 'O programie'"""
        about_dialog.show_about_dialog(self, APP_NAME, APP_VERSION)  # type: ignore

    def show_version_history(self) -> None:
        """Wyświetla okno historii wersji"""
        apphistory.show_version_history_dialog(self, APP_NAME)  # type: ignore

    def refresh_statistics(self) -> None:
        """Odświeża zakładkę statystyk"""
        statystyki.fill_statystyki_tab(self.tabs["Statystyki"], dark_mode=self.dark_mode)

    def on_close(self) -> None:
        """Zapamiętuje rozmiar okna przed zamknięciem."""
        # winfo_width/height zwraca piksele fizyczne (Tk), a geometry() CTk
        # przyjmuje wartości logiczne (które mnoży przez skalę).
        # Musimy podzielić przez skalę, aby zapisać wartości logiczne.
        scale = getattr(self, '_total_window_scale', 1.0)
        self.saved_geometry = {
            "width": int(self.winfo_width() / scale) if scale > 1.0 else self.winfo_width(),
            "height": int(self.winfo_height() / scale) if scale > 1.0 else self.winfo_height(),
        }
        self.destroy()


if __name__ == "__main__":
    # Inicjalizuj i zmigruj bazy danych
    database_manager.initialize_app_databases()
    # Skopiuj ikony do AppData (działa również z pliku EXE)
    database_manager.ensure_app_icons()

    # Wczytaj zapisane ustawienia filtrów i sortowania
    _saved = app_settings.load_settings()
    systemy_rpg.active_filters_systemy.update(_saved["filters"].get("systemy", {}))
    sesje_rpg.active_filters_sesje.update(_saved["filters"].get("sesje", {}))
    gracze.active_filters_gracze.update(_saved["filters"].get("gracze", {}))
    wydawcy.active_filters_wydawcy.update(_saved["filters"].get("wydawcy", {}))
    systemy_rpg.active_sort_systemy.update(_saved["sort"].get("systemy", {}))
    sesje_rpg.active_sort_sesje.update(_saved["sort"].get("sesje", {}))
    gracze.active_sort_gracze.update(_saved["sort"].get("gracze", {}))
    wydawcy.active_sort_wydawcy.update(_saved["sort"].get("wydawcy", {}))
    _vc = _saved.get("visible_columns", {})
    systemy_rpg.active_visible_cols_systemy.update(_vc.get("systemy", {}))
    sesje_rpg.active_visible_cols_sesje.update(_vc.get("sesje", {}))
    _cw = _saved.get("column_widths", {})
    if _cw.get("systemy"):
        systemy_rpg.active_col_widths_systemy.extend(_cw["systemy"])
    if _cw.get("sesje"):
        sesje_rpg.active_col_widths_sesje.extend(_cw["sesje"])
    if _cw.get("gracze"):
        gracze.active_col_widths_gracze.extend(_cw["gracze"])
    if _cw.get("wydawcy"):
        wydawcy.active_col_widths_wydawcy.extend(_cw["wydawcy"])

    # Wczytaj tryb i skalowanie czcionek
    _initial_dark_mode = bool(_saved.get("dark_mode", False))
    font_scaling.set_font_scale_factor(float(_saved.get("font_scale", 1.0)))
    systemy_rpg.all_expanded_systemy = bool(_saved.get("all_expanded_systemy", False))

    # Wczytaj geometrię okna (tylko rozmiar)
    _win = _saved.get("window", {})
    _initial_geometry = {
        "width": max(800, int(_win.get("width", START_WIDTH))),
        "height": max(600, int(_win.get("height", START_HEIGHT))),
    }

    # Skonfiguruj automatyczne skalowanie DPI dla wyższych rozdzielczości
    setup_dpi_scaling()

    app = SesyjkaApp()
    app.withdraw()
    _splash = splash_screen.SplashScreen(version=APP_VERSION, parent=app)
    _splash.show()
    _splash.set_status("Inicjalizacja interfejsu...")
    _splash.update()
    app.after(2000, _splash.close)

    # Kreator migracji — uruchom po pełnym zainicjowaniu okna
    def _run_migration_wizard() -> None:
        if systemy_rpg.needs_migration_wizard():
            systemy_rpg.show_migration_wizard(app)
    app.after(500, _run_migration_wizard)
    try:
        app.mainloop()
    finally:
        # Zapisz ustawienia filtrów i sortowania przed zamknięciem
        _to_save = {
            "dark_mode": app.dark_mode,
            "font_scale": font_scaling.get_font_scale_factor(),
            "all_expanded_systemy": systemy_rpg.all_expanded_systemy,
            "window": (
                app.saved_geometry
                if app.saved_geometry
                else {
                    "width": START_WIDTH,
                    "height": START_HEIGHT,
                }
            ),
            "filters": {
                "systemy": dict(systemy_rpg.active_filters_systemy),
                "sesje": dict(sesje_rpg.active_filters_sesje),
                "gracze": dict(gracze.active_filters_gracze),
                "wydawcy": dict(wydawcy.active_filters_wydawcy),
            },
            "sort": {
                "systemy": dict(systemy_rpg.active_sort_systemy),
                "sesje": dict(sesje_rpg.active_sort_sesje),
                "gracze": dict(gracze.active_sort_gracze),
                "wydawcy": dict(wydawcy.active_sort_wydawcy),
            },
            "visible_columns": {
                "systemy": dict(systemy_rpg.active_visible_cols_systemy),
                "sesje": dict(sesje_rpg.active_visible_cols_sesje),
            },
            "column_widths": {
                "systemy": list(systemy_rpg.active_col_widths_systemy) or None,
                "sesje": list(sesje_rpg.active_col_widths_sesje) or None,
                "gracze": list(gracze.active_col_widths_gracze) or None,
                "wydawcy": list(wydawcy.active_col_widths_wydawcy) or None,
            },
        }
        app_settings.save_settings(_to_save)
        # Zamknij okno cmd jeśli uruchomiono przez .bat
        import os, sys

        if os.name == "nt":
            # Zamknij tylko jeśli to nie jest uruchomienie z IDE
            if os.getenv("PROMPT") and not sys.stdin.isatty():
                os.system("exit")
