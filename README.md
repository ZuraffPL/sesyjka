# Sesyjka - TTRPG Base Manager

![Version](https://img.shields.io/badge/version-0.3.16-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![Platform](https://img.shields.io/badge/platform-Windows%2010-lightgrey)

Aplikacja desktopowa do zarządzania danymi związanymi z grami RPG (Tabletop Role-Playing Games).

## 📋 Funkcjonalności

### 🎲 Systemy RPG
- Zarządzanie kolekcją systemów RPG
- Hierarchiczna struktura: podręczniki główne i suplementy
- **Elastyczne systemy główne**: wybór z kolekcji lub wpisanie niestandardowej nazwy
- Statusy: W kolekcji, Na sprzedaż, Sprzedane, Nieposiadane, Do kupienia
- Obsługa wersji fizycznych i PDF
- Wielojęzyczna kolekcja
- Śledzenie cen zakupu i sprzedaży w różnych walutach

### ⚔️ Sesje RPG
- Rejestracja przeprowadzonych sesji
- Powiązanie z systemami RPG
- Obsługa graczy i mistrza gry
- Opis sesji z możliwością długich notatek

### 👥 Gracze
- Baza danych graczy
- Informacje kontaktowe
- Historia uczestnictwa w sesjach

### 🏢 Wydawcy
- Zarządzanie bazą wydawców
- Informacje kontaktowe
- Strony www i media społecznościowe

### 📊 Statystyki
- Automatyczne generowanie wykresów
- Przycisk ręcznego odświeżania
- Aktualizacja po każdej operacji CRUD

### 🔍 Filtry
- Zaawansowane filtrowanie danych
- Zachowanie filtrów po dodaniu rekordów
- Filtry dla wszystkich zakładek

### 🎨 Personalizacja
- **Globalne skalowanie fontów** (80%-120%)
- Suwak w ribbon z 8 krokami dostosowania
- Natychmiastowa zmiana wielkości wszystkich elementów UI
- Dostosowanie do różnych rozdzielczości (1080p, 2K, 4K)
- Ochrona czytelności (minimum 8px)
- Skalowanie wykresów matplotlib

## 🚀 Instalacja

### 📦 Opcja 1: Pobierz gotową wersję binarną (ZALECANE dla Windows)

**Najłatwiejszy sposób - nie wymaga instalacji Python!**

1. Przejdź do [Releases](https://github.com/ZuraffPL/sesyjka/releases/latest)
2. Pobierz `Sesyjka-v0.3.15-Windows.zip`
3. Rozpakuj archiwum
4. Uruchom `Sesyjka-v0.3.15.exe`

#### ⚠️ Fałszywe alarmy antywirusowe

**Jeśli Windows Defender lub antywirus blokuje plik exe, to normalny efekt uboczny.**

**Dlaczego to się dzieje?**
- Plik nie jest podpisany cyfrowym certyfikatem (certyfikaty kosztują 300-500 USD rocznie)
- PyInstaller tworzy pliki exe, które są często oznaczane jako "nieznane" przez antywirusy
- Jest to **fałszywy alarm** - kod źródłowy jest otwarty i dostępny na GitHub

**Rozwiązania:**

1. **Dodaj wyjątek w Windows Defender** (Zalecane):
   - Otwórz "Zabezpieczenia Windows" → "Ochrona przed wirusami i zagrożeniami"
   - Kliknij "Zarządzaj ustawieniami" w sekcji "Ustawienia ochrony przed wirusami i zagrożeniami"
   - Przewiń do "Wykluczenia" → "Dodaj lub usuń wykluczenia"
   - Dodaj folder, w którym znajduje się rozpakowany plik exe

2. **Użyj wersji ze źródeł** (Najbezpieczniejsza opcja):
   - Zobacz "Opcja 2: Instalacja ze źródeł" poniżej
   - Uruchamiasz czysty kod Python - brak fałszywych alarmów

3. **Weryfikuj autentyczność**:
   - Zawsze pobieraj z oficjalnego repozytorium GitHub
   - Link: https://github.com/ZuraffPL/sesyjka/releases/latest
   - **SHA256 checksum** dla `Sesyjka-v0.3.15-Windows.zip`:
     ```
     82A776A92BA97B7DCD23AE33A2993EE6F2E7094A7308B0F678687861B7BB73E2
     ```
   - Weryfikacja w PowerShell: `Get-FileHash Sesyjka-v0.3.15-Windows.zip -Algorithm SHA256`

### 🔧 Opcja 2: Instalacja ze źródeł

### Wymagania
- Windows 10 lub nowszy
- Python 3.9 lub nowszy

### Kroki instalacji

1. Sklonuj repozytorium:
```bash
git clone https://github.com/ZuraffPL/sesyjka.git
cd sesyjka
```

2. Utwórz środowisko wirtualne:
```bash
python -m venv .venv
```

3. Aktywuj środowisko wirtualne:
```bash
.venv\Scripts\activate
```

4. Zainstaluj wymagane pakiety:
```bash
pip install customtkinter tksheet matplotlib
```

5. Uruchom aplikację:
```bash
python main.py
```

## 📦 Struktura projektu

```
sesyjka/
├── main.py                 # Punkt wejścia aplikacji
├── database_manager.py     # Zarządzanie bazami i migracjami
├── font_scaling.py         # Moduł skalowania fontów
├── systemy_rpg.py         # Moduł systemów RPG
├── sesje_rpg.py           # Moduł sesji RPG
├── sesje_rpg_dialogs.py   # Dialogi dla sesji
├── gracze.py              # Moduł graczy
├── wydawcy.py             # Moduł wydawców
├── statystyki.py          # Moduł statystyk
├── about_dialog.py        # Dialog "O programie"
├── apphistory.py          # Historia wersji
├── Icons/                 # Ikony aplikacji
└── .github/               # Konfiguracja GitHub
```

## 🗄️ Bazy danych

Aplikacja automatycznie tworzy i zarządza następującymi bazami SQLite:
- `systemy_rpg.db` - Systemy RPG
- `sesje_rpg.db` - Sesje RPG
- `gracze.db` - Gracze
- `wydawcy.db` - Wydawcy

### 📁 Lokalizacja baz danych
**Windows:** `C:\Users\{username}\AppData\Local\Sesyjka\`  
**Linux/Mac:** `~/.sesyjka/`

### 🔄 Migracja i Kompatybilność
- ✅ **Automatyczna migracja** starych baz przy pierwszym uruchomieniu
- ✅ **Backupy** - automatyczne kopie zapasowe podczas aktualizacji
- ✅ **Wersjonowanie schematu** - bezpieczne aktualizacje struktury bazy
- ✅ **Kompatybilność wsteczna** - Twoje dane są bezpieczne przy aktualizacjach

📖 Szczegóły: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## 🎨 Interfejs

- Nowoczesny interfejs oparty na CustomTkinter
- Tryb jasny/ciemny
- Responsywne tabele z tksheet
- Domyślna rozdzielczość: 1800x1000 (Full HD)

## 📝 Changelog

### v0.3.15 (16.02.2026)
- ✨ **NOWE**: Globalne skalowanie fontów - suwak w ribbon (80%-120%, 8 kroków)
- 🎯 **Rozwiązanie**: Użytkownicy zgłaszali różne potrzeby - dla niektórych domyślne fonty były za małe, dla innych za duże
- 📐 **Zaktualizowano 96 specyfikacji fontów** w 9 plikach (main.py, about_dialog.py, gracze.py, wydawcy.py, systemy_rpg.py, sesje_rpg_dialogs.py, statystyki.py, apphistory.py, font_scaling.py)
- 🔧 **Działanie**: Font 12 → 80%=10 (min 8), 100%=12 (domyślnie), 120%=14
- 📊 **Matplotlib też skaluje** - również wykresy statystyk dostosowują się
- 💾 **Nowy moduł**: font_scaling.py z funkcją scale_font_size() i globalną zmienną font_scale_factor
- ⚡ **Natychmiastowa zmiana** - ribbon rebuild po każdej zmianie suwakiem
- ✅ **Wszystkie elementy UI**: dialogi, przyciski, labele, tabele zachowują proporcje

### v0.3.14 (16.02.2026)
- 🐛 **NAPRAWIONO**: Wszystkie pozostałe hardcodowane ścieżki do baz danych (11 miejsc)
- 📋 **Naprawiono pliki**:
  - `statystyki.py` (6 odwołań): sesje_rpg.db, gracze.db, systemy_rpg.db
  - `sesje_rpg.py` (5 odwołań): systemy_rpg.db, gracze.db
- 🆕 **NOWE**: Dodano typ suplementu "Starter/Zestaw Startowy"
- 📊 **Optymalizacja**: Dostosowano wysokości okien dialogów (+30px dla 6 typów suplementów)
- ✅ **Status**: Wszystkie 56 wywołań `sqlite3.connect()` używają teraz `get_db_path()`

### v0.3.13 (14.02.2026)
- 🐛 **NAPRAWIONO**: Puste okno dialogu "Dodaj sesję RPG" - brak list systemów i graczy
- 🔧 **Przyczyna**: Hardcoded ścieżki `systemy_rpg.db` i `gracze.db` w sesje_rpg_dialogs.py
- ✅ **Naprawiono** 2 funkcje: `get_all_systems()` i `get_all_players()` - używają teraz `get_db_path()`

### v0.3.12 (13.02.2026)
- 🐛 **NAPRAWIONO**: Nowi wydawcy dodani po v0.3.7 nie pojawiali się w formularzach systemów RPG
- 🔧 **Przyczyna**: Hardcoded ścieżka `wydawcy.db` zamiast `get_db_path()` w module systemy_rpg
- ✅ **Naprawiono** 3 odwołania do bazy wydawców - teraz wszystkie używają poprawnej ścieżki AppData
- 🔄 **Ulepszenie**: Combobox wydawcy automatycznie odświeża listę przy każdym kliknięciu
- 🧹 **Czyszczenie kodu**: Usunięto niedziałający system callbacków i zbędne przyciski odświeżania

### v0.3.11 (13.02.2026)
- 🎮 **NOWE**: Wsparcie dla platform VTT (Virtual Tabletop) w systemach RPG
- ✅ **9 platform VTT**: AboveVTT, Alchemy VTT, D&D Beyond, Demiplane, Fantasy Grounds, Foundry VTT, Roll20, Tabletop Simulator, Telespire
- 🔧 **NAPRAWIONO**: Krytyczne błędy filtrowania - resetowanie filtrów po edycji/usunięciu rekordów
- 🛡️ **NAPRAWIONO**: Błędne indeksowanie w filtrach - operacje na złych wierszach
- 📊 **Wprowadzono `displayed_data`** we wszystkich 4 tabelach dla poprawnego indeksowania

### v0.3.6 - v0.3.10 (13.02.2026)
**Seria ulepszeń interfejsu i zarządzania danymi**
- 🖥️ **Automatyczne skalowanie DPI** - interfejs dostosowuje się do rozdzielczości 2K/4K/wyższych
- 🔧 **Poprawiono wykrywanie fizycznej rozdzielczości** - działa z wysokim skalowaniem Windows (np. 2880x1800 @ 300%)
- 🗄️ **System zarządzania bazami** - nowa lokalizacja `AppData\Local\Sesyjka` z automatyczną migracją
- 🛡️ **Automatyczne backupy** - kopie zapasowe przed każdą aktualizacją struktury baz
- 🔄 **Zachowanie filtrów** po dodaniu rekordów + automatyczne odświeżanie statystyk
- 💰 **Status "Na sprzedaż"** - obsługa ceny zakupu i wyświetlanie jako "W kolekcji, Na sprzedaż"

## 🛠️ Technologie

- **Python 3.9+** - Język programowania
- **CustomTkinter** - Nowoczesny framework GUI
- **tkinter** - Podstawowy framework GUI
- **tksheet** - Widok tabelaryczny
- **matplotlib** - Wykresy i statystyki
- **SQLite** - Baza danych

## ❓ FAQ (Najczęściej Zadawane Pytania)

### Windows Defender blokuje plik .exe - co robić?

To normalny fałszywy alarm. Zobacz sekcję [⚠️ Fałszywe alarmy antywirusowe](#️-fałszywe-alarmy-antywirusowe) w instrukcji instalacji powyżej.

**Krótka odpowiedź:** Dodaj folder z aplikacją do wykluczeń Windows Defender lub użyj instalacji ze źródeł.

### Czy aplikacja jest bezpieczna?

Tak! Cały kod źródłowy jest otwarty i dostępny na GitHub. Możesz samodzielnie sprawdzić każdą linię kodu i zbudować aplikację ze źródeł.

### Gdzie są zapisywane moje dane?

Od wersji 0.3.8 wszystkie dane są przechowywane w lokalizacji:
- **Windows:** `C:\Users\{twoja_nazwa}\AppData\Local\Sesyjka\`
- **Linux/Mac:** `~/.sesyjka/`

Twoje dane są bezpieczne i oddzielone od plików aplikacji.

### Co się stanie z moimi danymi po aktualizacji?

Aplikacja automatycznie przeniesie Twoje dane do nowej lokalizacji i utworzy backup. Szczegóły w [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md).

### Czy mogę użyć aplikacji bez instalacji Python?

Tak! Pobierz wersję binarną (.exe) z sekcji [Releases](https://github.com/ZuraffPL/sesyjka/releases/latest). Nie wymaga instalacji Python ani żadnych dodatkowych pakietów.

## 👨‍💻 Autor

**Zuraffpl**
- Email: zuraffpl@gmail.com
- GitHub: [@ZuraffPL](https://github.com/ZuraffPL)

## 📄 Licencja

Ten projekt jest dostępny na licencji [Creative Commons Attribution 4.0 International (CC BY 4.0)](http://creativecommons.org/licenses/by/4.0/).

[![CC BY 4.0](https://licensebuttons.net/l/by/4.0/88x31.png)](http://creativecommons.org/licenses/by/4.0/)

Możesz swobodnie:
- ✅ Dzielić się — kopiować i rozpowszechniać
- ✅ Adaptować — remiksować, zmieniać i tworzyć na podstawie tego dzieła
- ✅ Używać komercyjnie

Pod warunkiem:
- 📝 Podania odpowiedniego uznania autorstwa

## 🤝 Współpraca

Zgłoszenia błędów i sugestie funkcjonalności są mile widziane! Możesz je zgłaszać przez GitHub Issues.

## 🔮 Plany rozwoju

- [ ] Integracja z bazą danych online
- [ ] Eksport danych do CSV/Excel
- [ ] Import danych z plików
- [ ] Backup automatyczny
- [ ] Wersja na Linux i macOS
- [ ] Wielojęzyczny interfejs

---

Stworzone z ❤️ dla społeczności mistrzów gry i graczy RPG
