"""
Narzędzia do bezpiecznego zarządzania rozmiarami okien dialogowych.
Zabezpiecza przed wychodzeniem dialogów poza ekran przy wysokim skalowaniu DPI.
"""
import tkinter as tk
from typing import Tuple, Any
import customtkinter as ctk  # type: ignore


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
        dialog, parent, desired_width, desired_height,
        margin_x=margin_x, margin_y=margin_y,
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
