# Sesyjka - TTRPG Base Manager

![Version](https://img.shields.io/badge/version-0.3.7-blue)
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
2. Pobierz `Sesyjka-v0.3.7-Windows.zip`
3. Rozpakuj archiwum
4. Uruchom `Sesyjka-v0.3.7.exe`

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

Aplikacja automatycznie tworzy następujące bazy SQLite przy pierwszym uruchomieniu:
- `systemy_rpg.db` - Systemy RPG
- `sesje_rpg.db` - Sesje RPG
- `gracze.db` - Gracze
- `wydawcy.db` - Wydawcy

## 🎨 Interfejs

- Nowoczesny interfejs oparty na CustomTkinter
- Tryb jasny/ciemny
- Responsywne tabele z tksheet
- Domyślna rozdzielczość: 1800x1000 (Full HD)

## 📝 Changelog

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

Stworzone z ❤️ dla społeczności graczy RPG
