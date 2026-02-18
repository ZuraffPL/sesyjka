# pyright: reportUnknownMemberType=false
"""
Moduł zarządzania ustawieniami aplikacji Sesyjka.
Przechowuje i odczytuje ustawienia sortowania/filtrowania z pliku JSON.
"""
import json
import os
from typing import Any, Dict

# Ścieżka do pliku ustawień (obok baz danych, w AppData)
def _get_settings_path() -> str:
    app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    settings_dir = os.path.join(app_data, "Sesyjka")
    os.makedirs(settings_dir, exist_ok=True)
    return os.path.join(settings_dir, "settings.json")


_DEFAULT_SETTINGS: Dict[str, Any] = {
    "dark_mode": False,
    "font_scale": 1.0,
    "window": {
        "width": 1800,
        "height": 920,
    },
    "filters": {
        "systemy": {},
        "sesje": {},
        "gracze": {},
        "wydawcy": {},
    },
    "sort": {
        "systemy": {"column": "ID", "reverse": False},
        "sesje":   {"column": "ID", "reverse": False},
        "gracze":  {"column": "ID", "reverse": False},
        "wydawcy": {"column": "ID", "reverse": False},
    },
}


def load_settings() -> Dict[str, Any]:
    """Wczytuje ustawienia z pliku JSON. Zwraca defaults jeśli plik nie istnieje."""
    path = _get_settings_path()
    if not os.path.exists(path):
        return _deep_copy(_DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Uzupełnij brakujące klucze wartościami domyślnymi
        merged = _deep_copy(_DEFAULT_SETTINGS)
        _deep_update(merged, data)
        return merged
    except Exception:
        return _deep_copy(_DEFAULT_SETTINGS)


def save_settings(settings: Dict[str, Any]) -> None:
    """Zapisuje ustawienia do pliku JSON."""
    path = _get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Settings] Błąd zapisu ustawień: {e}")


def _deep_copy(d: Any) -> Any:
    import copy
    return copy.deepcopy(d)


def _deep_update(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_update(base[k], v)  # type: ignore
        else:
            base[k] = v
