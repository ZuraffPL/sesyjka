<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Sesyjka — instrukcje dla Copilot

Szczegółowa dokumentacja projektu, architektura, konwencje i zasady pracy z kodem
znajdują się w pliku **CLAUDE.md** w katalogu głównym repozytorium.
Poniżej skrócone informacje do szybkiego kontekstu.

## Projekt

- **Nazwa**: Sesyjka (TTRPG Base Manager)
- **Wersja**: 0.3.x
- **Platforma**: Windows 10+, Python 3.9–3.12
- **GUI**: `customtkinter` + `tkinter`/`ttk`
- **Bazy danych**: SQLite (4 pliki: `systemy_rpg.db`, `sesje_rpg.db`, `gracze.db`, `wydawcy.db`)

## Stack

- `customtkinter` — główny framework UI (tryb jasny/ciemny)
- `tksheet` / `CTkDataTable` (`ctk_table.py`) — tabele
- `matplotlib` — wykresy i statystyki
- `Pillow` — ikony
- `tkcalendar` — picker dat
- `PyInstaller` — budowanie EXE

## Kluczowe zasady

- Wszystkie połączenia z bazą przez `sqlite3.connect(get_db_path("...db"))` z `database_manager.py`
- Nowe dialogi używają `create_ctk_toplevel()` i `apply_safe_geometry()` z `dialog_utils.py`
- Skalowanie fontów przez `scale_font_size()` z `font_scaling.py`
- Operacje I/O > 50 ms — osobny wątek, wynik przez `widget.after()`
- Brak cross-bazowych FOREIGN KEY (SQLite nie obsługuje), walidacja po stronie Pythona
- Styl: PEP 8, max 99 znaków na linię, type hints wymagane w nowych funkcjach
