"""
Narzędzia do bezpiecznego zarządzania rozmiarami okien dialogowych.
Zabezpiecza przed wychodzeniem dialogów poza ekran przy wysokim skalowaniu DPI.
"""

import sys
import ctypes
import tkinter as tk
from typing import Tuple, Any, Optional
import customtkinter as ctk  # type: ignore
import logging
import os
from logging.handlers import RotatingFileHandler

# --- Debug log do pliku (max 2 MB, 1 kopia zapasowa) ---
_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_sesyjka.log")
_root_logger = logging.getLogger()
if not _root_logger.handlers:
    _handler = RotatingFileHandler(
        _log_path, maxBytes=2 * 1024 * 1024, backupCount=1, encoding="utf-8"
    )
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    _root_logger.addHandler(_handler)
    _root_logger.setLevel(logging.DEBUG)
    # Wycisz logowanie matplotlib (tysiące wpisów findfont)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
_log = logging.getLogger("dialog_utils")


# --- Monkey-patch: przechwytuj KAŻDĄ zmianę trybu wyglądu z pełnym stacktrace ---
import traceback as _tb
from customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker import AppearanceModeTracker as _AMT  # type: ignore

_orig_set_am = _AMT.set_appearance_mode.__func__  # type: ignore[attr-defined]
_orig_update = _AMT.update.__func__  # type: ignore[attr-defined]


@classmethod  # type: ignore[misc]
def _patched_set_am(cls, mode_string: str) -> None:  # type: ignore
    old_mode = cls.appearance_mode  # type: ignore[attr-defined]
    old_set_by = cls.appearance_mode_set_by  # type: ignore[attr-defined]
    _log.debug(
        "[TRACKER] set_appearance_mode('%s') [was: mode=%s, set_by=%s]\n%s",  # type: ignore[arg-type]
        mode_string,
        old_mode,
        old_set_by,  # type: ignore[arg-type]
        ''.join(_tb.format_stack()[-5:-1]),
    )
    _orig_set_am(cls, mode_string)  # type: ignore[arg-type]
    if cls.appearance_mode != old_mode:  # type: ignore[attr-defined]
        _log.debug("[TRACKER] → mode ZMIENIONY: %s → %s", old_mode, cls.appearance_mode)  # type: ignore[arg-type]


@classmethod  # type: ignore[misc]
def _patched_update(cls) -> None:  # type: ignore
    old_mode = cls.appearance_mode  # type: ignore[attr-defined]
    _orig_update(cls)  # type: ignore[arg-type]
    if cls.appearance_mode != old_mode:  # type: ignore[attr-defined]
        _log.debug(
            "[TRACKER] update() → mode ZMIENIONY: %s → %s (set_by=%s)",  # type: ignore[arg-type]
            old_mode,
            cls.appearance_mode,
            cls.appearance_mode_set_by,
        )  # type: ignore[attr-defined, arg-type]


_AMT.set_appearance_mode = _patched_set_am  # type: ignore[assignment]
_AMT.update = _patched_update  # type: ignore[assignment]
_log.debug("[TRACKER] monkey-patch zainstalowany")


def _log_ctk_mode(label: str) -> None:
    """Loguje aktualny stan AppearanceModeTracker — do diagnozowania problemu z trybem."""
    try:
        from customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker import AppearanceModeTracker  # type: ignore

        _log.debug(
            "  [MODE] %s → appearance_mode=%s (%s), set_by=%s",
            label,
            AppearanceModeTracker.appearance_mode,
            "Dark" if AppearanceModeTracker.appearance_mode == 1 else "Light",
            AppearanceModeTracker.appearance_mode_set_by,
        )
    except Exception as exc:
        _log.debug("  [MODE] %s → błąd odczytu: %s", label, exc)


def create_ctk_toplevel(parent: Any) -> Any:  # type: ignore
    """
    Tworzy CTkToplevel bez problematycznego cyklu withdraw/update/deiconify
    który na Windows resetuje tryb wyglądu i powoduje flicker rodzica.

    CTkToplevel._windows_set_titlebar_color() woła super().update() podczas
    inicjalizacji, co płucze WSZYSTKIE zdarzenia aplikacji i może:
      - nadpisywać _state_before z 'normal' na 'withdrawn' przy drugim wołaniu
      - permanentnie ukrywać okno (revert widzi stan 'withdrawn' i zostawia)
      - resetować tryb wyglądu CTk do jasnego

    Rozwiązanie: tymczasowo wyłącz manipulację paska tytułu na czas __init__
    (przez flagę klasową i natychmiastowe przełączenie na instancyjną).
    Ciemny titlebar jest ustawiany później przez apply_dark_titlebar().
    """
    _win = sys.platform.startswith("win")
    _log.debug("create_ctk_toplevel: start, platform_win=%s", _win)
    _log_ctk_mode("przed create_ctk_toplevel")
    if _win:
        class_flag_before = getattr(ctk.CTkToplevel, '_deactivate_windows_window_header_manipulation', False)  # type: ignore
        _log.debug("  class flag przed __init__: %s -> ustawiam True", class_flag_before)
        # Wyłącz mechanizm dla WSZYSTKICH instancji na czas __init__
        ctk.CTkToplevel._deactivate_windows_window_header_manipulation = True  # type: ignore
    dialog = ctk.CTkToplevel(parent)  # type: ignore
    if _win:
        # Przywróć flagę klasową i ustaw instancyjną, by blokować późniejsze wołania
        # (resizable(), _set_appearance_mode()) na tym konkretnym oknie
        ctk.CTkToplevel._deactivate_windows_window_header_manipulation = False  # type: ignore
        dialog._deactivate_windows_window_header_manipulation = True  # type: ignore
        _log.debug(
            "  class flag przywrócona: False; instance flag: %s",
            getattr(dialog, '_deactivate_windows_window_header_manipulation', '?'),
        )
    _log_ctk_mode("po CTkToplevel.__init__")
    _log.debug("  dialog fg_color = %s", dialog.cget("fg_color"))  # type: ignore[misc]
    _log.debug("create_ctk_toplevel: gotowe, dialog=%s", dialog)
    return dialog  # type: ignore


def apply_dark_titlebar(dialog: Any) -> None:  # type: ignore
    """
    Ustawia ciemny pasek tytułu przez Windows DWM API bez withdraw/update.
    Wywołuj przez dialog.after(50, ...) po pełnym wyrenderowaniu okna.
    """
    if not sys.platform.startswith("win"):
        return
    if not dialog.winfo_exists():
        _log.debug("apply_dark_titlebar: dialog już nie istnieje, skip")
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(dialog.winfo_id())  # type: ignore
        _log.debug("apply_dark_titlebar: hwnd=%s", hwnd)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        ctypes.windll.dwmapi.DwmSetWindowAttribute(  # type: ignore
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)),
            ctypes.sizeof(ctypes.c_int(1)),
        )
        _log.debug("apply_dark_titlebar: sukces")
    except Exception as exc:
        _log.error("apply_dark_titlebar: błąd — %s", exc)


def get_screen_size(widget: Any) -> Tuple[int, int]:
    """Zwraca dostępny rozmiar ekranu w pikselach (zgodnych z geometry() okna)."""
    return widget.winfo_screenwidth(), widget.winfo_screenheight()


def clamp_geometry(
    dialog: Any,
    parent: Any,
    desired_width: int,
    desired_height: int,
    *,
    margin_x: int = 20,
    margin_y: int = 60,
) -> str:
    """
    Oblicza bezpieczną geometrię okna, która mieści się na ekranie.

    Wartości desired_width i desired_height to bazowe wartości logiczne
    (takie same jakie przekazuje się do geometry()).
    CTk automatycznie przeskaluje je przez window_scaling.

    Funkcja sprawdza jaki będzie faktyczny rozmiar po skalowaniu
    i jeśli nie zmieści się na ekranie — zmniejsza wartości logiczne.

    Args:
        dialog: Okno dialogowe (CTkToplevel)
        parent: Okno nadrzędne
        desired_width: Pożądana szerokość bazowa (logiczna)
        desired_height: Pożądana wysokość bazowa (logiczna)
        margin_x: Margines boczny od krawędzi ekranu
        margin_y: Margines od góry/dołu (na pasek zadań itp.)

    Returns:
        String geometrii, np. "950x550+100+200"
    """
    parent.update_idletasks()

    # Pobierz łączne skalowanie CTk (custom + DPI systemu)
    try:
        total_scale = dialog._apply_window_scaling(10000) / 10000.0
    except Exception:
        total_scale = 1.0

    # Dostępny obszar ekranu w pikselach (zgodny z winfo_screenwidth)
    screen_w, screen_h = get_screen_size(dialog)

    # Maksymalny rozmiar fizyczny (piksele ekranu)
    max_phys_w = screen_w - margin_x * 2
    max_phys_h = screen_h - margin_y * 2

    # Oblicz fizyczny rozmiar po skalowaniu
    phys_w = desired_width * total_scale
    phys_h = desired_height * total_scale

    # Jeśli nie mieści się — zmniejsz wartości logiczne
    w = desired_width
    h = desired_height

    if phys_w > max_phys_w:
        w = int(max_phys_w / total_scale)
    if phys_h > max_phys_h:
        h = int(max_phys_h / total_scale)

    # Oblicz faktyczny rozmiar fizyczny (po korekcie)
    actual_phys_w = int(w * total_scale)
    actual_phys_h = int(h * total_scale)

    # Wycentruj na rodzicu (pozycja nie jest skalowana przez CTk)
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()

    x = parent_x + (parent_w - actual_phys_w) // 2
    y = parent_y + (parent_h - actual_phys_h) // 2

    # Upewnij się że okno nie wychodzi poza ekran
    x = max(margin_x, min(x, screen_w - actual_phys_w - margin_x))
    y = max(margin_y // 2, min(y, screen_h - actual_phys_h - margin_y))

    geometry_str = f"{w}x{h}+{x}+{y}"
    return geometry_str


def apply_safe_geometry(
    dialog: Any,
    parent: Any,
    desired_width: int,
    desired_height: int,
    *,
    margin_x: int = 20,
    margin_y: int = 60,
    allow_resize_height: bool = True,
) -> Tuple[int, int]:
    """
    Ustawia geometrię okna dialogowego z zabezpieczeniem przed wychodzeniem poza ekran.
    Zwraca (faktyczna_szerokość_logiczna, faktyczna_wysokość_logiczna).

    Jeśli pożądany rozmiar nie mieści się na ekranie po skalowaniu,
    okno jest zmniejszane i ustawia się resizable, aby użytkownik mógł
    w razie potrzeby powiększyć lub scrollować zawartość.
    """
    geo = clamp_geometry(
        dialog,
        parent,
        desired_width,
        desired_height,
        margin_x=margin_x,
        margin_y=margin_y,
    )
    dialog.geometry(geo)

    # Parsuj wynikowe wymiary
    size_part = geo.split("+")[0]
    parts = size_part.split("x")
    final_w = int(parts[0])
    final_h = int(parts[1])

    # Jeśli okno zostało zmniejszone — pozwól na zmianę rozmiaru
    if final_h < desired_height or final_w < desired_width:
        dialog.resizable(True, allow_resize_height)

    return final_w, final_h


def open_calendar_picker(parent: Any, initial_date_str: str = "") -> Optional[str]:
    """Otwiera modalne okno z widgetem kalendarza.

    Args:
        parent: Okno nadrzędne (CTkToplevel lub Tk).
        initial_date_str: Bieżąca data w formacie YYYY-MM-DD (lub pusty string).

    Returns:
        Wybrana data jako string YYYY-MM-DD lub ``None`` jeśli anulowano.
    """
    from tkcalendar import Calendar as _Cal  # type: ignore
    from datetime import date as _date, datetime as _dt

    try:
        init_date = _dt.strptime(initial_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        init_date = _date.today()

    dark = ctk.get_appearance_mode().lower() == "dark"

    # Kolory kalendarza zależne od trybu
    if dark:
        cal_kw = dict(
            background="#2b2b2b",
            foreground="#e0e0e0",
            bordercolor="#444444",
            headersbackground="#1e1e2e",
            headersforeground="#a0c4ff",
            selectbackground="#0078d4",
            selectforeground="#ffffff",
            normalbackground="#2b2b2b",
            normalforeground="#e0e0e0",
            weekendbackground="#353535",
            weekendforeground="#aaaaaa",
            othermonthbackground="#1e1e1e",
            othermonthforeground="#555555",
            othermonthwebackground="#1e1e1e",
            othermonthweforeground="#555555",
        )
        win_bg = "#2b2b2b"
        btn_bg = "#1e1e2e"
        btn_fg = "#e0e0e0"
        btn_abg = "#0078d4"
    else:
        cal_kw = dict(
            selectbackground="#0078d4",
            selectforeground="#ffffff",
        )
        win_bg = "#f5f5f5"
        btn_bg = "#e0e0e0"
        btn_fg = "#212121"
        btn_abg = "#bbdefb"

    result: list = [None]

    cal_win = tk.Toplevel(parent)
    cal_win.title("Wybierz datę")
    cal_win.resizable(False, False)
    cal_win.configure(bg=win_bg)
    cal_win.grab_set()
    cal_win.transient(parent)
    parent.update_idletasks()
    px = parent.winfo_rootx() + parent.winfo_width() // 2 - 160
    py = parent.winfo_rooty() + parent.winfo_height() // 2 - 130
    cal_win.geometry(f"+{px}+{py}")

    cal = _Cal(
        cal_win,
        selectmode="day",
        year=init_date.year,
        month=init_date.month,
        day=init_date.day,
        date_pattern="yyyy-mm-dd",
        **cal_kw,
    )
    cal.pack(padx=10, pady=(10, 4))

    def _ok() -> None:
        result[0] = cal.get_date()
        cal_win.destroy()

    def _cancel() -> None:
        cal_win.destroy()

    # Podwójne kliknięcie = szybkie zatwierdzenie
    cal.bind("<Double-Button-1>", lambda _e: _ok())

    btn_frame = tk.Frame(cal_win, bg=win_bg)
    btn_frame.pack(pady=(4, 10))
    tk.Button(
        btn_frame, text="OK", command=_ok, width=10,
        bg=btn_bg, fg=btn_fg, activebackground=btn_abg, relief="flat",
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(
        btn_frame, text="Anuluj", command=_cancel, width=10,
        bg=btn_bg, fg=btn_fg, activebackground=btn_abg, relief="flat",
    ).pack(side=tk.LEFT, padx=5)

    cal_win.wait_window()
    return result[0]


def make_scrollable_dialog_frame(
    dialog: Any,
    padx: int = 20,
    pady: int = 20,
) -> ctk.CTkScrollableFrame:
    """
    Tworzy scrollowalną ramkę jako główny kontener formularza w dialogu.
    Używaj zamiast zwykłego CTkFrame gdy formularz może nie zmieścić się
    na małych ekranach z wysokim skalowaniem.

    Returns:
        CTkScrollableFrame do którego dodajesz elementy formularza
    """
    scroll_frame = ctk.CTkScrollableFrame(dialog)
    scroll_frame.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)  # type: ignore[no-untyped-call]
    scroll_frame.columnconfigure(1, weight=1)
    return scroll_frame
