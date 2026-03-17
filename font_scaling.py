"""
Moduł zarządzania skalowaniem fontów w aplikacji.
Pozwala na globalne skalowanie wszystkich czcionek w zakresie 80%-120%.
"""

# Globalna zmienna skalowania fontów (80% - 120%)
font_scale_factor = 1.0


def scale_font_size(base_size: int) -> int:
    """
    Skaluje rozmiar fontu na podstawie globalnego współczynnika.

    Args:
        base_size: bazowy rozmiar czcionki

    Returns:
        przeskalowany rozmiar czcionki (minimum 8px dla czytelności)
    """
    return max(8, int(base_size * font_scale_factor))


def set_font_scale_factor(factor: float) -> None:
    """
    Ustawia globalny współczynnik skalowania fontów.

    Args:
        factor: współczynnik skalowania (0.8 - 1.2)
    """
    global font_scale_factor
    font_scale_factor = max(0.8, min(1.2, factor))


def get_font_scale_factor() -> float:
    """
    Pobiera aktualny współczynnik skalowania fontów.

    Returns:
        aktualny współczynnik skalowania
    """
    return font_scale_factor
