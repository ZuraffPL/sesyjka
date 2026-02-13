# Sesyjka - TTRPG Base Manager

![Version](https://img.shields.io/badge/version-0.3.8-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![Platform](https://img.shields.io/badge/platform-Windows%2010-lightgrey)

Aplikacja desktopowa do zarządzania danymi związanymi z grami RPG (Tabletop Role-Playing Games).

## 📋 Funkcjonalności

### 🎲 Systemy RPG
- Zarządzanie kolekcją systemów RPG
- Hierarchiczna struktura: podręczniki główne i suplementy
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

## 🚀 Instalacja

### 📦 Opcja 1: Pobierz gotową wersję binarną (ZALECANE dla Windows)

**Najłatwiejszy sposób - nie wymaga instalacji Python!**

1. Przejdź do [Releases](https://github.com/ZuraffPL/sesyjka/releases/latest)
2. Pobierz `Sesyjka-v0.3.8-Windows.zip`
3. Rozpakuj archiwum
4. Uruchom `Sesyjka-v0.3.8.exe`

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
### v0.3.8 (13.02.2026)
- 🗄️ **System zarządzania bazami danych** - pełna kompatybilność wsteczna
- 📁 **Nowa lokalizacja baz** - `AppData\Local\Sesyjka` (Windows) lub `~/.sesyjka` (Linux/Mac)
- 🔄 **Automatyczna migracja** - stare bazy są automatycznie przenoszone
- 🛡️ **System backupów** - automatyczne kopie zapasowe przed każdą migracją
- 📊 **Wersjonowanie schematu** - bezpieczne aktualizacje struktury baz
- 📖 **Dokumentacja** - nowy przewodnik [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- ✅ **Bezpieczeństwo danych** - Twoje dane są chronione przy każdej aktualizacji
### v0.3.7 (13.02.2026)
- 🔄 Status "Na sprzedaż" wyświetla się jako "W kolekcji, Na sprzedaż"
- 💰 Obsługa ceny zakupu dla statusu "Na sprzedaż"
- 🎨 Zachowanie czerwonego podświetlenia dla przedmiotów na sprzedaż

### v0.3.6 (13.02.2026)
- 🔄 Zachowanie filtrów po dodaniu nowych rekordów
- 📊 Automatyczne odświeżanie statystyk po operacjach CRUD
- 🔄 Przycisk ręcznego odświeżania statystyk
- 🐛 Poprawki błędów typowania

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
