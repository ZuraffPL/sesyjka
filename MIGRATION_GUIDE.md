# 🔄 System Migracji Baz Danych - Dokumentacja

## 📝 Przegląd

Od wersji 0.3.8 aplikacja Sesyjka używa nowego systemu zarządzania bazami danych, który zapewnia:
- ✅ **Automatyczną migrację baz** ze starych lokalizacji
- ✅ **Kompatybilność wsteczną** - stare bazy działają z nową wersją
- ✅ **Bezpieczeństwo danych** - automatyczne backupy podczas migracji
- ✅ **Wersjonowanie schematu** - kontrolowana aktualizacja struktury baz

## 📁 Nowa Lokalizacja Baz Danych

### Windows
```
C:\Users\{username}\AppData\Local\Sesyjka\
├── systemy_rpg.db
├── sesje_rpg.db
├── gracze.db
├── wydawcy.db
└── backups\
    ├── systemy_rpg.db.backup_20260213_174500
    ├── sesje_rpg.db.backup_20260213_174501
    └── ...
```

### Linux/Mac
```
~/.sesyjka/
├── systemy_rpg.db
├── sesje_rpg.db
├── gracze.db
├── wydawcy.db
└── backups/
```

## 🔄 Automatyczna Migracja

### Co się dzieje przy pierwszym uruchomieniu nowej wersji?

1. **Wykrywanie starych baz** - System sprawdza czy istnieją bazy w katalogu aplikacji
2. **Kopiowanie do nowej lokalizacji** - Bazy są kopiowane do `AppData\Local\Sesyjka`
3. **Tworzenie backupu** - Oryginalne bazy są zachowywane jako backup
4. **Sprawdzanie wersji** - System sprawdza wersję schematu każdej bazy
5. **Migracja schematu** - Jeśli potrzebne, schemat jest aktualizowany
6. **Backup przed migracją** - Przed każdą zmianą schematu tworzony jest backup

### Komunikaty podczas migracji

```
============================================================
Inicjalizacja baz danych Sesyjka
============================================================
✓ Zmigrowano systemy_rpg.db do C:\Users\...\AppData\Local\Sesyjka
✓ Utworzono backup: systemy_rpg.db.backup_20260213_174500
✓ Systemy RPG: Znaleziono istniejącą bazę
✓ Migracja systemy_rpg.db zakończona
...
============================================================
Inicjalizacja zakończona
============================================================
```

## 🛡️ Bezpieczeństwo Danych

### Backupy
- Automatyczne backupy podczas migracji
- Backupy przechowywane w `AppData\Local\Sesyjka\backups\`
- Format nazwy: `{nazwa_bazy}.backup_{data}_{czas}`
- Backupy NIE są automatycznie usuwane

### Przywracanie z backupu

1. Zamknij aplikację Sesyjka
2. Przejdź do `C:\Users\{username}\AppData\Local\Sesyjka\`
3. Skopiuj żądany backup (np. `systemy_rpg.db.backup_20260213_174500`)
4. Usuń aktualną bazę (np. `systemy_rpg.db`)
5. Zmień nazwę backupu na `systemy_rpg.db`
6. Uruchom aplikację ponownie

## 🔢 System Wersjonowania

### Wersje Schematu
- Każda baza danych ma przypisaną wersję schematu
- Wersja przechowywana w specjalnej tabeli `db_version`
- Aktualna wersja: `1`

### Migracje
- System automatycznie wykrywa czy baza wymaga aktualizacji
- Migracje są bezpieczne - zawsze tworzony jest backup
- Nie można "cofnąć" wersji (tylko w górę)

### Sprawdzanie wersji bazy

```python
from database_manager import get_db_version, get_db_path

db_path = get_db_path("systemy_rpg.db")
version = get_db_version(db_path)
print(f"Wersja schematu: {version}")
```

## 🔧 API dla Deweloperów

### Podstawowe funkcje

```python
from database_manager import (
    get_app_data_dir,      # Pobierz katalog danych aplikacji
    get_db_path,           # Pobierz pełną ścieżkę do bazy
    backup_database,       # Utwórz backup bazy
    initialize_app_databases  # Inicjalizuj wszystkie bazy
)

# Przykład użycia
db_path = get_db_path("moja_baza.db")
backup_path = backup_database(db_path)
```

### Dodawanie nowej migracji

Edytuj `database_manager.py`:

```python
CURRENT_DB_VERSION = 2  # Zwiększ wersję

def migrate_database_schema(db_path: str, db_name: str) -> None:
    current_version = get_db_version(db_path)
    
    if current_version < 1:
        migrate_to_v1(db_path, db_name)
    if current_version < 2:
        migrate_to_v2(db_path, db_name)  # Dodaj nową migrację
    
    set_db_version(db_path, CURRENT_DB_VERSION)

def migrate_to_v2(db_path: str, db_name: str) -> None:
    """Migracja do wersji 2: dodaj nowe kolumny"""
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        
        if db_name == "systemy_rpg.db":
            try:
                c.execute("ALTER TABLE systemy_rpg ADD COLUMN nowa_kolumna TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass  # Kolumna już istnieje
```

## ❓ FAQ

### Co się stanie ze starymi bazami w katalogu aplikacji?
Pozostaną nietknięte. System tworzy kopie w nowej lokalizacji i dodatkowo zapisuje backupy.

### Czy mogę ręcznie przenieść bazy?
Tak, ale nie jest to zalecane. System automatycznie to robi przy pierwszym uruchomieniu.

### Co jeśli chcę używać baz z innej lokalizacji?
Możesz ręcznie skopiować bazy do `AppData\Local\Sesyjka\`.

### Czy mogę usunąć stare bazy po migracji?
Tak, ale zalecamy poczekać kilka dni i upewnić się że wszystko działa poprawnie.

### Co się stanie jeśli zainstaluję starszą wersję aplikacji?
Starsza wersja nie będzie widziała baz w nowej lokalizacji. System nie wspiera cofania wersji.

## 🐛 Rozwiązywanie Problemów

### Baza nie została zmigrowana
1. Sprawdź czy stara baza istnieje w katalogu aplikacji
2. Sprawdź logi w konsoli podczas uruchamiania
3. Ręcznie skopiuj bazy do `AppData\Local\Sesyjka\`

### Błąd podczas migracji schematu
1. Sprawdź czy masz uprawnienia do zapisu w katalog
 
u AppData
2. Sprawdź czy backup został utworzony
3. W razie problemów przywróć z backupu

### Nie widzę swoich danych
1. Sprawdź czy bazy znajdują się w `AppData\Local\Sesyjka\`
2. Sprawdź czy masz uprawnienia do odczytu
3. Sprawdź czy nie uruchamiasz aplikacji jako inny użytkownik

## 📞 Wsparcie

Jeśli napotkasz problemy z migracją:
1. Zachowaj backupy (znajdują się w katalogu aplikacji i w folderze backups)
2. Zgłoś issue na GitHub: https://github.com/ZuraffPL/sesyjka/issues
3. Dołącz komunikaty z konsoli podczas uruchamiania

---

**Bezpieczeństwo Twoich danych jest naszym priorytetem!** 🛡️
