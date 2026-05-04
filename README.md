# Sesyjka - TTRPG Base Manager

![Version](https://img.shields.io/badge/version-0.4.39-blue)
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
- Obsługa platform VTT (9 platform: Roll20, Foundry VTT, Fantasy Grounds i inne)
- Multi-wybór typów suplementów
- Zaawansowane filtrowanie: Typ, Wydawca, Posiadanie, Język, Status, VTT

### ⚔️ Sesje RPG
- Rejestracja przeprowadzonych sesji
- Powiązanie z systemami RPG
- Obsługa graczy i mistrza gry

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
- Tryb jasny/ciemny z natychmiastową zmianą i bez flickera

### 🆕 UX i nawigacja
- **Splash screen** w klimacie TTRPG przy starcie aplikacji
- **Instrukcja obsługi** (❓ Pomoc) dostępna z ribbonu — opis wszystkich funkcji
- Trójkolorowe wiersze Systemów: szary (brak pozycji), niebieski (tylko suplementy), złoty (ma PG)
- Ręczna zmiana szerokości kolumn — zapamiętywana między uruchomieniami

### 💾 Transfer danych i kopie zapasowe
- **Eksport do ZIP** — zapis wszystkich 4 baz SQLite do jednego archiwum `.zip` (przenoszenie między urządzeniami, backup)
- **Eksport do folderu** — zapis baz jako osobne pliki `.db`
- **Eksport do Excel (.xlsx)** — każda tabela z każdej bazy jako osobny arkusz; nagłówki z niebieskim tłem, auto-szerokość kolumn
- **Import z ZIP/folderu** — zastąpienie własnych baz danymi z archiwum; automatyczny backup przed nadpisaniem + walidacja zawartości
- Automatyczna kopia zapasowa baz przy każdej aktualizacji struktury

### 👁️ Tryb gościa
- Przeglądanie baz innego użytkownika z pliku ZIP lub folderu **bez zastępowania własnych danych**
- Ribbon sygnalizuje tryb gościa pomarańczowym paskiem informacyjnym
- Wszystkie operacje zapisu zablokowane (ikona ✏️, dwuklik, PPM, Dodaj/Usuń) — tylko odczyt
- Przycisk „Wróć do swoich danych" przywraca własną bazę jednym kliknięciem

### 🖥️ Wysokie DPI i skalowanie
- Automatyczne skalowanie interfejsu do rozdzielczości ekranu
- Bezpieczna geometria dialogów — dopasowanie do aktualnego skalowania Windows (100%-300%)
- Scrollowalne formularze w dialogach — brak ucinania elementów przy wysokim DPI
- Poprawna obsługa rozdzielczości 2K/4K
- Zapamiętywanie rozmiaru i pozycji okna głównego

## 🚀 Instalacja

### 📦 Opcja 1: Pobierz gotową wersję binarną (ZALECANE dla Windows)

**Najłatwiejszy sposób - nie wymaga instalacji Python!**

1. Przejdź do [Releases](https://github.com/ZuraffPL/sesyjka/releases/latest)
2. Pobierz `Sesyjka-v0.4.39-Windows.zip`
3. Rozpakuj archiwum
4. Uruchom `Sesyjka-v0.4.39.exe`

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
   - **SHA256 checksum** dla `Sesyjka-v0.4.39.exe` dostępny w opisie najnowszego release
   - Weryfikacja w PowerShell: `Get-FileHash Sesyjka-v0.4.39.exe -Algorithm SHA256`

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
pip install -r requirements.txt
```

5. Uruchom aplikację:
```bash
python main.py
```

## 📦 Struktura projektu

```
sesyjka/
├── main.py                 # Punkt wejścia aplikacji
├── database_manager.py     # Zarządzanie bazami, migracjami i eksportem danych
├── settings.py             # Ustawienia aplikacji (rozmiar okna, motywy)
├── font_scaling.py         # Moduł skalowania fontów
├── dialog_utils.py         # Bezpieczna geometria dialogów (DPI-safe)
├── systemy_rpg.py          # Moduł systemów RPG
├── sesje_rpg.py            # Moduł sesji RPG
├── sesje_rpg_dialogs.py    # Dialogi dla sesji
├── ctk_table.py            # Reużywalny widget CTkDataTable (tabele z ikonami, tooltipami, sortowaniem)
├── gracze.py               # Moduł graczy
├── wydawcy.py              # Moduł wydawców
├── statystyki.py           # Moduł statystyk
├── about_dialog.py         # Dialog "O programie"
├── apphistory.py           # Historia wersji
├── help_dialog.py          # Dialog instrukcji obsługi
├── splash_screen.py        # Splash screen startowy
├── db_transfer_dialog.py   # Dialog transferu/eksportu baz (ZIP, Excel)
├── requirements.txt        # Wymagane pakiety Pythona
├── pyrightconfig.json      # Konfiguracja type checkera Pyright
├── Icons/                  # Ikony aplikacji (edit.png, ...)
└── .github/                # Konfiguracja GitHub
```

## 🗄️ Bazy danych

Aplikacja automatycznie tworzy i zarządza następującymi bazami SQLite:
- `systemy_rpg.db` - Systemy RPG
- `sesje_rpg.db` - Sesje RPG
- `gracze.db` - Gracze
- `wydawcy.db` - Wydawcy

### 📁 Lokalizacja baz danych
**Windows:** `C:\Users\{username}\AppData\Local\Sesyjka\`

### 🔄 Migracja i Kompatybilność
- ✅ **Automatyczna migracja** starych baz przy pierwszym uruchomieniu
- ✅ **Backupy** - automatyczne kopie zapasowe podczas aktualizacji
- ✅ **Wersjonowanie schematu** - bezpieczne aktualizacje struktury bazy
- ✅ **Kompatybilność wsteczna** - Twoje dane są bezpieczne przy aktualizacjach

## 🎨 Interfejs

- Nowoczesny interfejs oparty na CustomTkinter
- Tryb jasny/ciemny z natywnym przełącznikiem
- Responsywne tabele z tksheet
- Domyślna rozdzielczość okna: 1800x920 (proporcjonalne skalowanie na 2K/4K)
- Wstążka (ribbon) z kolorowymi przyciskami akcji
- Spójny tryb ciemny we wszystkich oknach dialogowych
- Liczniki aktywnych filtrów na przyciskach
- Bezpieczna geometria dialogów — dopasowanie do rozdzielczości i skalowania Windows

## � Stack technologiczny

| Komponent | Biblioteka | Opis |
|-----------|-----------|------|
| GUI (framework) | `customtkinter` | Nowoczesny UI z zaokrąglonymi rogami, tryb jasny/ciemny |
| GUI (baza) | `tkinter` / `ttk` | Natywny toolkit Pythona (wybrane widgety) |
| Tabele | `CTkDataTable` (własny) | Tabele z ikonami, sortowaniem, hierarchią, tooltipami |
| Kalendarz | `tkcalendar` | Graficzny picker dat w dialogach sesji |
| Wykresy | `matplotlib` | Wykresy kołowe i słupkowe w module statystyk |
| Ikony/grafika | `Pillow (PIL)` | Tintowanie PNG ikon dla trybu jasnego i ciemnego |
| Baza danych | `sqlite3` (stdlib) | 4 bazy: systemy, sesje, gracze, wydawcy |
| Eksport Excel | `openpyxl` | Eksport wszystkich baz do pliku `.xlsx` (każda tabela = osobny arkusz) |
| Budowanie EXE | `PyInstaller` | Budowanie samodzielnego pliku `.exe` dla Windows |

## 📝 Changelog

### v0.4.39 (04.05.2026)
- ✨ **Grupy graczy (tagi)**: nowe pole `Grupa` w katalogu graczy — gracz może należeć do wielu grup/kampanii wpisanych po przecinku (np. `Drużyna A, Kampania 2`); kolumna `Grupa` widoczna w tabeli z sortowaniem i wyszukiwaniem
- ✨ **Szybkie zaznaczanie grupy w sesjach**: przy dodawaniu i edycji sesji — panel `Zaznacz grupę` z listą rozwijalną tagów i przyciskiem `Zaznacz` błyskawicznie zaznacza wszystkich graczy z wybranego tagu (z zachowaniem limitu graczy w sesji)
- 🐛 **Naprawa pustych tabel po starcie**: widgety CTk budowane przy `withdraw()` nie renderowały się po `deiconify()`; po zamknięciu splash screenu wszystkie zakładki są teraz oznaczane jako `_dirty` i odświeżane po 100 ms
- 🐛 **Naprawa dialogu zapisu Excel**: `filedialog.asksaveasfilename(parent=CTkToplevel)` powodował błąd DPI ukrywający przycisk Zapisz; fix: `parent=main_window` + `dlg.update()` przed wywołaniem

### v0.4.37 (29.04.2026)
- 🔧 **Naprawa selekcji graczy w dialogach wyboru**: trwały zbiór `_persistent_sel` zapewnia zachowanie zaznaczenia graczy podczas filtrowania po nazwie — wątek `_rebuilding` blokuje nadpisanie przez programatyczne `select_set`; działa zarówno dla kliknięć myszką, jak i wpisywania tekstu
- ✨ **Sesje GM-less**: nowy checkbox „Gra GM-less” w sekcji Mistrza Gry — ukrywa przycisk wyboru MG, wstawia `NULL` w bazie i wyświetla `N/A` w tabeli; automatyczna migracja istniejących baz (`mg_id INTEGER NOT NULL` → `INTEGER`)

### v0.4.35 (28.04.2026)
- ⚡ **Optymalizacja: dialogi wyboru graczy/MG**: zastąpiono `CTkCheckBox`/`CTkRadioButton` na `tk.Listbox` — 1 widget zamiast ~435 operacji Tk; eliminacja zamrażania UI przy 87+ graczach w oknach wyboru (dodawanie i edycja sesji)
- ⚡ **Optymalizacja: tabela sesji (`_build_rows`)**: dopasowanie ramek po ID wiersza zamiast pozycji — eliminacja ~4356 destroy+recreate przy sortowaniu; przywrócenie płynności przy 484+ sesjach

### v0.4.34 (28.04.2026)
- � **Eksport baz danych**: zapis 4 baz SQLite do pliku **ZIP** (jedno archiwum) lub **folderu** (osobne pliki `.db`) — przenoszenie danych między urządzeniami lub tworzenie kopii zapasowej
- 📥 **Import baz danych**: wczytanie baz z pliku ZIP lub folderu z automatycznym backupem bieżących danych i walidacją zawartości przed nadpisaniem
- 📊 **Eksport do Excel (.xlsx)**: nowa trzecia opcja eksportu — każda tabela SQLite jako osobny arkusz; nagłówki z niebieskim tłem, auto-szerokość kolumn (maks. 50 znaków); wymagany `openpyxl>=3.1.5`
- 👁️ **Tryb gościa**: przeglądanie baz innego użytkownika z ZIP/folderu bez zastępowania własnych danych; ribbon sygnalizuje tryb pomarańczowym paskiem; przycisk „Wróć do swoich danych" przywraca własną bazę
- 🔒 **Pełna ochrona trybu gościa przed zapisem**: zablokowano wszystkie ścieżki edycji (ikona ✏️, dwuklik, PPM, przyciski Dodaj/Usuń) we wszystkich zakładkach; nowy `_fire_edit_cb()` w `CTkDataTable` jako centralna brama; guard w `save_session()`
- ⚡ **Naprawa zamrożenia po kliknięciu „Wróć do swoich danych"**: usunięto synchroniczne `refresh_statistics()` z `enter/exit_guest_mode()` — statystyki odświeżają się leniwie przy kliknięciu zakładki
- 📋 **`requirements.txt`**: dodano plik z zablokowanymi wersjami wszystkich zależności (`openpyxl==3.1.5` i inne)

### v0.4.30 (28.04.2026)
- 🐛 **Naprawa zawieszania okna wyboru graczy**: usunięto rekurencyjną kaskadę `var.trace` + `v.set(False)` w `validate_players_selection`; zamieniono `trace` na `command=` w CTkCheckBox; checkboxy 87 graczy ładowane partiami po 12 przez `after(0)` zamiast synchronicznie
- 🔍 **Naprawa dialogu filtrowania sesji**: powiększono okno do 820×580 (resizable), dodano `columnconfigure` przed budową wierszy, poprawiono mechanizm reflow — jeden zbiorczy `update_idletasks` + `_run_all_reflows` zamiast czterech rozłącznych `after(150)` z samoplanowaniem

### v0.4.29 (28.04.2026)
- 🐛 **Naprawa okna wyboru graczy i MG**: `CTkScrollableFrame` w dialogach wyboru graczy i Mistrza Gry (dodawanie i edycja sesji) nie miał ustawionej jawnej wysokości — przy 60+ graczach okno rozciągało się na ~2000px zamiast scrollować; naprawiono przez dodanie `height=300`

### v0.4.28 (27.04.2026)
- 🖱️ **Podwójne kliknięcie — edycja**: dwuklik na dowolnym wierszu tabeli otwiera dialog edycji we wszystkich zakładkach (Systemy RPG, Sesje RPG, Gracze, Wydawcy)
- 👁️ **Pokaż/ukryj przycisk edycji**: nowa opcja w dialogu „Kolumny" (sekcja Opcje tabeli) — ukrycie ikonki ✏️ gdy edycja przez dwuklik jest wystarczająca; ustawienie zapisywane w `settings.json`
- 🔍 **Kolumny dla zakładki Gracze**: nowy przycisk „Kolumny" z dialogiem widoczności i kolejności kolumn (checkboxy + ↑/↓), osobna opcja „Pokaż przycisk edycji"
- 🎲 **Filtrowalne pole systemu RPG w sesji**: wpisanie fragmentu nazwy zawęża listę propozycji w czasie rzeczywistym; walidacja sprawdza wybór z listy
- ➕ **Dodaj system z formularza sesji**: przycisk ➕ obok pola systemu otwiera formularz dodawania; po zapisaniu lista i zakładka Systemy RPG odświeżają się automatycznie
- 🔤 **Polska kolejność sortowania systemów**: ą, ć, ę, ł, ń, ó, ś, ź, ż sortowane w poprawnym miejscu alfabetu (wcześniej trafiały na koniec przez błąd sortowania SQLite)

### v0.4.22 (22.04.2026)
- 🔧 **Uproszczenie hierarchii Systemów RPG**: 2-poziomowa struktura (System → wszystkie pozycje) zamiast 3-poziomowej; kolumna „System główny” zawsze pokazuje nazwę systemu gry; PG wyświetlane przed suplementami
- 🐛 **Naprawiony zapis edycji**: edycja systemu/PG zachowuje `system_glowny_id`; dodawanie suplementu poprawnie zapisuje `system_gry_id`
- 🔄 **Odświeżanie zakładki Wydawcy**: po dodaniu wydawcy z formularza PG/suplementu tabela Wydawcy odświeża się natychmiast
- 📖 **Uzupełniona instrukcja obsługi**: opis zmiany kolejności kolumn ↑/↓ i checkbox „Ukryj systemy”; ręczna zmiana szerokości kolumn

### v0.4.20 (21.04.2026)
- 💰 **Ceny per forma posiadania**: nowe pola Cena Fizyczna / Cena PDF / Cena VTT w dialogach dodawania i edycji systemu — wyświetlane dynamicznie po zaznaczeniu odpowiedniej formy; automatyczna migracja istniejących danych z `cena_zakupu`
- 🎛️ **Multi-select filtry we wszystkich zakładkach**: toggle-buttony zamiast combobox — można zaznaczyć wiele opcji jednocześnie (Typ, Język, Status, Wydawca, Posiadanie, Rok, System, MG, Płeć, Kraj)
- 📐 **Zawijanie przycisków filtrów**: przy dużej liczbie opcji przyciski automatycznie zawijają się do nowych wierszy — brak ucinania opcji
- 🔧 **Naprawa dialogu edycji systemu**: poprawiony rozmiar okna i inicjalizacja pól cen przy otwarciu
- ⚡ **Optymalizacja rozwijania/zwijania hierarchii**: `_cached_lp` na ramkach wierszy `CTkDataTable` — złożoność O(k), tylko modyfikowane wiersze; pierwsze rozwinięcie ~5 ms
- 📄 **Zmiana kolejności kolumn**: dialog „Widoczność i kolejność kolumn” z przyciskami ↑/↓; kolejność zapisywana w `settings.json`; parametr `col_order` w `CTkDataTable`
- 👁️ **Checkbox „Ukryj systemy”**: przełącznik w pasku tabeli Systemy RPG — ukrywa wiersze-systemy, pozostawiając widoczne tylko PG i suplementy

### v0.4.16 (21.04.2026)
- 🔧 **Przebudowa dialogu edycji systemu**: pole „Przypisz do systemu” (powiązanie z katalogiem gier) zamiast tekstowego pola nazwy systemu głównego; przycisk ➕ Dodaj system bez zamykania formularza
- 🗑️ **Usunięcie pola „System główny (opcjonalnie)”**: suplementy i PG są równorzędne względem systemu — hierarchia tylko przez „Przypisz do systemu”
- 🐛 **Naprawa błędu edycji**: `tuple index out of range` przy otwieraniu dialogu edycji — brakująca kolumna `system_gry_id` w zapytaniu SELECT

### v0.4.13 (21.04.2026)
- 🏗️ **Przebudowa hierarchii Systemów RPG**: nowa trójpoziomowa struktura System → Podręczniki Główne → Suplementy z przyciskami rozwijania `[+]`/`[-]`; przyciski ribbonu przepisane (✚ Dodaj System / ✚ Dodaj PG/Suplement / 🗑 Usuń)
- 🎨 **Trójkolorowe wiersze Systemu**: szary = brak pozycji, niebieski = tylko suplementy bezpośrednie, złoty = ma PG — łatwiejszy wzrokowy przegląd kolekcji
- ➕ **Dodaj wydawcę z poziomu formularza PG**: przycisk ➕ w wierszu wydawcy otwiera formularz bez zamykania głównego okna; nowy wydawca jest od razu zaznaczony
- ⚙️ **Kreator migracji**: przycisk ⚙ Migruj dane w ribbonie — widoczny tylko gdy istnieją dane do migracji, znika automatycznie po zakończeniu
- 🔃 **Naprawione sortowanie**: Wydawca, Język (agregacja z pg_by_game), Status, Posiadanie, Cena — wszystkie kolumny sortowalne
- 🐛 **Naprawa rozwijania wszystkich**: `_on_toggle_expand_all` iteruje po `games` (poprawny zasięg)
- 🐛 **Naprawa routing suplementów**: suplementy przypisane bezpośrednio do systemu (`system_gry_id`, bez PG-rodzica) teraz poprawnie pojawiają się pod systemem w drzewie zamiast jako osierocone `(!)`
- 🧹 **Uproszczony dialog dodawania**: pola „System główny (opcjonalnie)" i „lub wpisz nazwę:" ukryte gdy dialog otwiera się z kontekstu konkretnego systemu (✚ Dodaj PG/Suplement do systemu)
- ⚡ **Naprawa flickera dark mode**: `_rebuild_tab()` przekazuje preloaded data z cache — rebuild synchroniczny, zero widocznego przebłysku
- 🎬 **Splash screen TTRPG**: ciemne tło, złote runy, nazwa/wersja/autor — 2 sekundy po starcie
- 📖 **Instrukcja obsługi** (❓ Pomoc): scrollowane okno z opisem wszystkich funkcjonalności, dostępne z ribbonu
- 📐 **Ręczna zmiana szerokości kolumn**: przeciąganie krawędzi nagłówka, zapisywane w `settings.json`
- 📅 **Graficzny kalendarz daty**: przycisk 📅 w dialogach dodawania/edycji sesji otwiera teraz okno z widgetem `tkcalendar` zamiast tekstowego pola — obsługa trybu ciemnego/jasnego, podwójne kliknięcie zatwierdza datę
- 🗂️ **Dodaj sesję do istniejącej kampanii**: nowa opcja w menu PPM na sesji typu Kampania — prefilluje dane (system, gracze, MG, tytuł kampanii) do formularza nowej sesji
- 🔧 **Konfiguracja VS Code**: poprawki `tasks.json` i `launch.json` — aktualne nazwy, usunięte przestarzałe opcje

### v0.3.32 (10.04.2026)
- 🎛️ **Wybór widocznych kolumn**: nowy przycisk „Kolumny" w górnym pasku zakładek Systemy RPG i Sesje RPG — dialog z checkboxami umożliwia ukrycie/pokazanie dowolnych kolumn tabeli; preferencje zapisywane w `settings.json`
- 🔧 **Naprawione błędy Pyright**: `reportPossiblyUnbound` dla `_PILImage`/`_PILImageTk` w `ctk_table.py`; wywołania `configure(bg=..., insertbackground=...)` na widgetach tkinter castowanych do `Any`
- 🐛 **Naprawa odświeżania tabeli po zmianie kolumn**: usunięcie cache przed przebudową wymusza pełny rebuild `CTkDataTable` z nową listą `hidden_cols`

### v0.3.31 (18.03.2026)
- 📈 **Naprawa rosnącego wykresu systemów**: `pack_propagate(False)` na ramce wykresu + `figsize` dopasowane do faktycznej przestrzeni ramki (`winfo_width/height`) — zmiana roku nie rozciąga już okna aplikacji
- 📊 **Etykieta podsumowania**: pakowana jako `BOTTOM` przed canvasem — nie wypycha wykresu poza ramkę
- 🖼️ **Layout kolumn statystyk**: kolumna 0 i 1 równe (`weight=1, minsize=280`), kolumna 2 szersza (`weight=3, minsize=520`); nagłówek pierwszej statystyki z `wraplength=240`

### v0.3.30 (18.03.2026)
- ⚙️ **Refaktoryzacja kodu (Rundy 1–4)**: Black formatter zastosowany do wszystkich 14 plików źródłowych; `pyrightconfig.json` — konfiguracja type checkera; PEP 484 type hints we wszystkich nowych funkcjach i metodach
- 🗄️ **SQLite best practices**: `conn.row_factory = sqlite3.Row` + `PRAGMA foreign_keys = ON` + context managery (`with sqlite3.connect(...) as conn:`) w całej aplikacji
- 🧵 **Threading**: `fill_systemy_rpg_tab()`, `fill_sesje_rpg_tab()`, `fill_gracze_tab()`, `fill_wydawcy_tab()` oraz `update_system_chart()` — SQL/IO przeniesione do wątków tła z `widget.after()` do UI; naprawa N+1 query w statystykach (`WHERE id IN (?)`)
- 🐛 **Naprawa UI**: `wraplength` zmniejszony do 510 px — tekst nie wychodzi poza krawędź okien dialogowych

### v0.3.28 (10.03.2026)
- 🔍 **Wyszukiwanie na żywo** we wszystkich zakładkach: pole „Wyszukaj" w górnym pasku Graczy, Sesji RPG, Wydawców i Systemów RPG — filtrowanie w czasie rzeczywistym
- 🔍 **Wyszukiwanie w dialogach** wyboru graczy i MG (dodaj/edytuj sesję): pole `🔍 Szukaj gracza…` z natychmiastowym filtrowaniem listy checkboxów i radiobutonów
- 🐛 **Naprawa dark mode flash**: `create_ctk_toplevel()` w `dialog_utils.py` eliminuje flicker trybu ciemnego przez wyłączenie manipulacji paskiem tytułu podczas `__init__`; `apply_dark_titlebar()` przez DWM API bez `withdraw/update`
- 🪵 **Debug logging**: `RotatingFileHandler` (2 MB) + monkey-patch `AppearanceModeTracker` w `dialog_utils.py` — logi do `debug_sesyjka.log`

### v0.3.27 (08.03.2026)
- ➕ **Przycisk „Dodaj gracza"** w dialogach wyboru graczy i MG sesji — bez zamykania okna, lista odświeżana natychmiast, zakładka Gracze aktualizowana automatycznie
- 🔧 **Refaktor dialogów wyboru** `sesje_rpg_dialogs.py`: `CTkToplevel` + `CTkScrollableFrame` + `CTkCheckBox` + `CTkRadioButton` zamiast `tk.Toplevel` + `Canvas`/`Scrollbar`/`ttk` — usunięto ręczne bindowanie scrolla i `apply_dark_theme_to_dialog()`
- 🎨 **Wyrównano kolory tekstu**: `text_color_disabled` checkboxów = `text_color` — zablokowane opcje wyglądają spójnie z radiobutonami MG
- 🔄 **Przełącznik „Rozwiń wszystkie"** w `systemy_rpg.py`: `CTkSwitch` w pasku górnym, stan zapamiętywany w `settings.json` i przywracany przy starcie
- 🐛 **Kolumna Lp.**: zawsze pokazuje numerację bezwzględną niezależnie od aktywnych filtrów

### v0.3.26 (05.03.2026)
- 🔧 **Migracja** `systemy_rpg.py`: tabela z `tksheet` na `CTkDataTable` — hierarchia główne/suplementy, expand/collapse `[+]`/`[-]`, 13 kolumn, filtry, sort, kolorowanie, menu PPM
- ⚡ **Optymalizacja** `sesje_rpg.py`: zastąpienie N+1 zapytań DB zapytaniami zbiorczymi (2800+ połączeń → 3 niezależnie od liczby rekordów)
- ⚡ **`toggle_expand()`**: nowa metoda w `CTkDataTable` — expand/collapse suplementów bez przebudowy całej tabeli; `pack(after=…)` / `pack_forget()` na konkretnych ramkach, złożoność O(k) niezależna od rozmiaru tabeli
- 🏷️ **`_cell_labels`**: każda ramka wiersza przechowuje referencje do swoich `Label` — aktualizacja symbolu `[+]`/`[-]` jednym `Label.configure()` bez destroy+create
- 🚀 **Wyniki expand/collapse**: pierwsze rozwinięcie ~450 ms → ~5 ms, zwinięcie/re-rozwinięcie ~120 ms → ~2 ms

### v0.3.25 (04.03.2026)
- ✅ **Kolumna Lp.**: parametr `show_row_numbers=True` w `CTkDataTable` — numeracja wierszy (36 px, centrowana, hover/selekcja/PPM jak pozostałe komórki); włączone w `sesje_rpg.py`, `gracze.py`, `wydawcy.py`
- ⚡ **Debounce suwaka czcionek**: pełny rebuild 250 ms po zatrzymaniu (zamiast przy każdym pikselu); ribbon rebuild w withdraw/deiconify eliminuje flicker
- ⚡ **Lazy rebuild zakładek**: dirty-flag — przebudowa tylko aktywnej zakładki natychmiast, pozostałe przy pierwszym przełączeniu (5 rebuildów → 1 przy zmianie dark/light)

### v0.3.24 (03.03.2026)
- 🔧 **MIGRACJA**: Moduł sesji RPG — tabela przebudowana z `tksheet.Sheet` na `CTkDataTable` (spójny z graczami i wydawcami)
- ✏️ **Przycisk Edytuj**: ikona PNG z tooltipem w każdym wierszu sesji
- 🎨 **Kolorowanie**: wiersze kolorowane według miesiąca sesji (12 kolorów, osobne palety dla trybu jasnego i ciemnego)
- 🔍 **Dialog filtrowania**: Rok, System, Typ sesji, Mistrz Gry — w stylu CTkToplevel
- 🗑️ **Usuwanie**: `usun_zaznaczona_sesja()` zaktualizowane do API CTkDataTable
- ⚡ **Optymalizacja `ctk_table.py`**: `_build_rows()` teraz inkrementalny — reużywa istniejące `tk.Frame`, niszczy tylko dzieci (`_refresh_row()` + `_populate_row()`)
- 🚀 **Cache zakładek**: `fill_*_tab()` dla graczy, wydawców i sesji zapisuje cache na obiekcie zakładki — szybka ścieżka bez przebudowy UI, brak flickera po operacjach CRUD
- 🔗 **`data_ref` pattern**: mutable container `List[data]` zapewnia poprawny sharing stanu w zamknięciach (filtr, sort)

### v0.3.23 (02.03.2026)
- 🔧 **MIGRACJA**: Moduł graczy — tabela przebudowana z `tksheet.Sheet` na `CTkDataTable` (spójny z wydawcami)
- ✏️ **Przycisk Edytuj**: ikona PNG z tooltipem w każdym wierszu graczy
- 🎨 **Kolorowanie**: Status (⭐/👑) ma priorytet nad kolorem płci, obsługiwane przez `row_color_fn`
- 🔗 **Kolumna Social media**: klikalny link (otwiera przeglądarkę), menu PPM: Edytuj / Usuń
- 📐 **Naprawa fillery**: ostatnia kolumna w CTkDataTable nie rozciąga się do szerokości okna (`relwidth=1, width=-x`)
- 📦 **Ikona edycji w EXE**: `ensure_app_icons()` kopiuje `edit.png` do `AppData/Local/Sesyjka/Icons/` przy starcie (PyInstaller + dev)
- 📝 **README i O programie**: zaktualizowane technologie i struktura projektu

### v0.3.22 (02.03.2026)
- 🔧 **PRZEBUDOWA**: Moduł wydawców — widok tabeli przeszedł z `CTkScrollableFrame` (ręczny grid) na `CTkDataTable` (spójny z resztą aplikacji)
- 📐 **Szerokość kolumn**: auto-dopasowanie do zawartości przez `_compute_widths()` (tkfont), limity: Nazwa ≤ 280px, Strona ≤ 500px, Kraj ≤ 120px
- 🖊️ **Ikona edycji**: `Icons/edit.png` z PIL tint — dwa warianty kolorystyczne: jasny tryb `#1558d6`, ciemny tryb `#7baaff`
- 💬 **Tooltip**: przycisk edycji wyświetla tooltip "Edytuj" (fix `add="+"` w bindingach)
- 🐛 **NAPRAWA**: `TclError: bad window path` po przełączeniu dark/light mode — `CTkComboBox` → `ttk.Combobox` w dialogu filtrowania + `report_callback_exception()` w `SesyjkaApp`
- 🔄 **Przywrócono** brakujące funkcje: `usun_wydawce_dialog`, `usun_zaznaczonego_wydawce` (używa `CTkDataTable.get_selected()`)

### v0.3.21 (24.02.2026)
- 🐛 **NAPRAWA**: Edycja suplementów bez przypisanego podręcznika głównego nie otwierała okna edycji u części użytkowników
- 🔧 **Przyczyna**: `context_edit`/`context_delete`/`context_add_supplement` czytały selekcję przez `get_currently_selected()` po otwarciu menu, przez co indeks wiersza mógł być nieważny
- ✅ **Naprawiono**: Indeks wiersza przechwytywany w `captured_r` w momencie prawego kliknięcia i przekazywany przez domyślne argumenty lambda
- 📜 **NOWE**: System logowania diagnostycznego (`sesyjka_debug.log`) w katalogu AppData
- 📎 Logi w `open_edit_system_dialog`, `on_typ_change`, `context_edit`, `show_context_menu`
- 🧾 **Refaktoryzacja**: funkcje menu kontekstowego przyjmują `row_idx` bezpośrednio zamiast pytać o aktualną selekcję

### v0.3.19 (18.02.2026)
- 🛡️ **NOWE**: `dialog_utils.py` - centralny system bezpiecznej geometrii dialogów
- 📐 **Bezpieczna geometria**: wszystkie dialogi dopasowują się do aktualnej rozdzielczości i skalowania DPI
- 📜 **Scrollowalne formularze**: dialogi systemów RPG używają `CTkScrollableFrame` — brak ucinania przy 300% DPI
- 🖥️ **Naprawa okna głównego**: poprawne rozmiary okna na 2K/4K z różnym skalowaniem Windows
- 💾 **Naprawa zapisu ustawień**: okno zapisuje wartości logiczne zamiast pikseli fizycznych
- 🎯 **Centrowanie przy starcie**: okno zawsze mieści się w obszarze ekranu (margines taskbar)
- 🔧 **Refaktoryzacja**: `apply_safe_geometry()`, `clamp_geometry()`, `make_scrollable_dialog_frame()`

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
- **tksheet** - Widok tabelaryczny (Systemy RPG)
- **CTkDataTable** (własny widget) - Tabele z ikonami, tooltipami i sortowaniem (Gracze, Wydawcy, Sesje)
- **Pillow (PIL)** - Przetwarzanie i tintowanie ikon PNG
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
