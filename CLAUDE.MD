# CLAUDE.md — Sesyjka (TTRPG Base Manager)

## Kontekst projektu

Sesyjka to desktopowa aplikacja na Windows do zarządzania danymi związanymi z grami RPG (TTRPG): systemami, suplementami, sesjami, graczami, wydawcami oraz statystykami rozgrywek.  
Projekt jest rozwijany iteracyjnie (wersja 0.3.30) z dużym naciskiem na ergonomię UI (CustomTkinter), wysokie DPI, skalowanie fontów, wydajność tabel (CTkDataTable) i bezpieczne zarządzanie bazami SQLite (database_manager, migracje, backupy).

---

## Stack technologiczny

- **Język:** Python 3.9–3.12 (Python 3.13+ może powodować problemy z PyInstallerem — nie używać do budowania EXE bez wcześniejszego sprawdzenia kompatybilności).
- **Platforma docelowa:** Windows 10+ (wersja EXE budowana PyInstallerem).
- **GUI:**  
  - `tkinter` — baza,  
  - `customtkinter` — główny framework UI (tryb jasny/ciemny, nowoczesny wygląd),  
  - `ttk` — wybrane kontrolki (np. Combobox tam, gdzie CTk stwarzało problemy).
- **Widoki tabelaryczne:**  
  - `tksheet` — historycznie używane, obecnie stopniowo zastępowane,  
  - `CTkDataTable` (własny widget w `ctk_table.py`) — docelowy komponent do tabel z ikonami, tooltipami, sortowaniem, kolorowaniem, numeracją wierszy, hierarchią.
- **Inne komponenty UI:**  
  - `CTkScrollableFrame` — scrollowane formularze i dialogi (wysokie DPI),  
  - własne dialogi (`about_dialog.py`, `apphistory.py`, `sesje_rpg_dialogs.py`, dialogi systemów/filtrów).
- **Grafika:** `Pillow (PIL)` — ładowanie i tintowanie ikon PNG (np. ikona edycji w tabelach).
- **Wykresy:** `matplotlib` — generowanie wykresów i statystyk w `statystyki.py` (skaluje się razem z fontami).
- **Baza danych:**  
  - SQLite: 4 bazy (`systemy_rpg.db`, `sesje_rpg.db`, `gracze.db`, `wydawcy.db`) zarządzane przez `database_manager.py`,  
  - automatyczna migracja, wersjonowanie schematu, backupy, przeniesienie do `%LOCALAPPDATA%\Sesyjka\` / `~/.sesyjka/`.
- **Infrastruktura pomocnicza:**  
  - `database_manager.py` — ścieżki, migracje, backupy, `get_db_path()`, `ensure_app_icons()`,  
  - `settings.py` — ustawienia aplikacji (rozmiar okna, motyw, stan przełączników),  
  - `font_scaling.py` — globalne skalowanie czcionek 80–120%,  
  - `dialog_utils.py` — bezpieczna geometria, high-DPI, CTk/Tk dialog helpers.

---

## Aktualna struktura projektu (źródło prawdy)

Struktura katalogu głównego (README):

```text
sesyjka/
├── main.py                 # Punkt wejścia aplikacji
├── database_manager.py     # Zarządzanie bazami i migracjami
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
├── pyrightconfig.json      # Konfiguracja type checkera Pyright
├── Icons/                  # Ikony aplikacji (edit.png, ...)
└── .github/                # Konfiguracja GitHub
```



Wytyczne w tym pliku powinny nie zmieniać tej struktury bez wyraźnego polecenia; dopuszczalne jest proponowanie ewolucji (np. wydzielenie podkatalogów) po wcześniejszym planie.

## Architektura i podział odpowiedzialności

### Ogólny model

    Architektura zbliżona do modułowego MVC/MVP:

        moduły domenowe: systemy_rpg.py, sesje_rpg.py, gracze.py, wydawcy.py, statystyki.py,

        warstwa danych: SQLite + database_manager.py i użycie get_db_path(),

        warstwa prezentacji: main.py, CustomTkinter UI, ctk_table.py, dialogi (about_dialog.py, apphistory.py, sesje_rpg_dialogs.py, dialogi systemów).

    Logika domenowa dla danej zakładki powinna być skupiona w odpowiednim module (np. systemy w systemy_rpg.py), ale:

        dostęp do bazy zawsze przez sqlite3.connect(get_db_path("...db")),

        brak powrotu do hardcodowanych ścieżek typu "systemy_rpg.db", "gracze.db" itp.

### Zasada kluczowa: brak logiki biznesowej w widgetach

    Callbacki i handlery zdarzeń:

        mogą czytać wartości z kontrolek i aktualizować UI,

        nie powinny zawierać złożonej logiki domenowej lub SQL — tę logikę umieszczamy w funkcjach pomocniczych w odpowiednim module (np. get_all_systems(), apply_filters(), toggle_expand()), które można później łatwiej testować.

### Moduły specjalne

    ctk_table.py:

        centralny, reużywalny widget CTkDataTable z:

            ikoną edycji, tooltipami, sortowaniem, numeracją wierszy (show_row_numbers), hierarchią (parent/child, expand/collapse), kolorowaniem wierszy, obsługą menu PPM,

        wszelkie nowe tabele (np. przyszłe raporty) powinny używać CTkDataTable zamiast budować nowy grid ręcznie.

    dialog_utils.py:

        jedyne miejsce, w którym wolno dotykać niskopoziomowej geometrii okien (DPI, clampowanie do ekranu, CTk/Tk mix),

        nowe dialogi powinny wykorzystywać apply_safe_geometry(), make_scrollable_dialog_frame() i create_ctk_toplevel().

    font_scaling.py:

        centralne API do skalowania fontów (scale_font_size() + globalny font_scale_factor),

        wszystkie nowe definicje fontów muszą z tego korzystać (również w matplotlib).

    database_manager.py:

        jedyne miejsce odpowiedzialne za: lokalizację baz, migracje, backupy, get_db_path(),

        przy wszelkich zmianach schematów — najpierw aktualizacja database_manager/MIGRATION_GUIDE, dopiero później użycie nowych kolumn w modułach.

## Konwencje nazewnicze i styl kodu

    Moduły: snake_case (systemy_rpg.py, sesje_rpg_dialogs.py, ctk_table.py).

    Funkcje, metody, zmienne: snake_case (get_all_systems, apply_filters, toggle_expand, show_version_history_dialog).

    Klasy: PascalCase (SesyjkaApp, CTkDataTable, VersionHistoryDialog jeżeli wprowadzisz klasę).

    Stałe: UPPER_SNAKE_CASE dla globalnych konfiguracji/kluczy.

    Bazy i kolumny SQLite: snake_case (systemy_rpg, sesje_rpg, gracze, kolumny status, jezyk, system_glowny_id, system_glowny_nazwa_custom itd.).

    Styl: PEP 8, długość linii maksymalnie 99 znaków (zgodnie z Black/nowoczesną konwencją), docstringi w funkcjach reużywalnych/ważnych.

    **Type hints (PEP 484) są wymagane** we wszystkich nowych funkcjach i metodach. Wyjątek: callbacki Tkinter przyjmujące `*args` (np. `command=`, `bind()`), gdzie pominięcie adnotacji jest dopuszczalne z komentarzem `# Tk callback`.

### Komentarze i tekst w UI

    Język: polski (zgodnie z istniejącymi napisami), ale dopuszczalne angielskie komentarze techniczne — ważne, by w jednym pliku nie mieszać ich nadmiernie.

## Zasady dla GUI (CustomTkinter, CTkDataTable, dialogi)

### Główne okno i zakładki

    main.py zawiera:

        punkt wejścia, klasę głównego okna (np. SesyjkaApp), tworzenie ribbonu, zakładek (Systemy, Sesje, Gracze, Wydawcy, Statystyki, O programie, Historia wersji).

    Zasady:

        rozmiar i pozycja okna są zarządzane przez settings.py + logikę związaną z DPI (nie duplikować tego w innych modułach),

        zmiana trybu ciemny/jasny i skali fontów powinna przebudowywać UI leniwie (lazy rebuild) — tylko bieżąca zakładka od razu, reszta przy pierwszym przełączeniu (zachowywać istniejący wzorzec „dirty flags”).
### Wątki i blokowanie GUI

**Zakaz blokowania głównego wątku Tk.** Wszelkie operacje I/O (SQL, pliki, sieć) trwające >50 ms muszą być uruchamiane w osobnym wątku i zwracać wyniki do UI wyłącznie przez `widget.after()`:

```python
import threading

def _load_data_bg():
    result = fetch_from_db()          # ciężka operacja poza wątkiem UI
    widget.after(0, lambda: _update_ui(result))

threading.Thread(target=_load_data_bg, daemon=True).start()
```

    Reguły:

        - nie wolno wywoływać żadnych metod Tk/CTk bezpośrednio z wątku tła,
        - `after(0, callback)` lub `after(delay_ms, callback)` to jedyna akceptowana metoda komunikacji wątek→UI,
        - długie agregacje w `statystyki.py` (matplotlib, duże JOIN-y) podlegają tej samej zasadzie.
### CTkDataTable (ctk_table.py)

    Jest komponentem referencyjnym dla wszystkich rozbudowanych tabel (Wydawcy, Gracze, Sesje, Systemy).

    Nowe funkcje / refaktory:

        trzymać w ctk_table.py (np. kolejny typ „kolorowania wierszy”, nowy typ kolumny),

        używać istniejących patternów: show_row_numbers, row_color_fn, toggle_expand(), _build_rows(), _refresh_row().

    Przy rozwoju:

        nie kopiować kodu tabeli do innych modułów; zamiast tego rozszerzać API CTkDataTable lub przechodzić parametry (np. callbacki, konfigurację kolumn).

### Dialogi (w tym apphistory)

    Wszystkie nowe dialogi:

        używają create_ctk_toplevel(parent) z dialog_utils.py,

        stosują apply_safe_geometry(dialog, parent, width, height),

        dla długich formularzy używają CTkScrollableFrame z dialog_utils.make_scrollable_dialog_frame() lub analogicznego wzorca.

    apphistory.py / apphistory-2.py:

        dialog historii wersji to wzorzec dla czytelnego, scrollowalnego okna długiego tekstu (heading, separator, scrollable frame, labelki z pogrubieniem wersji i daty, monospaced / normalny font).

        przy generowaniu tekstu changeloga trzymać się istniejącego formatowania (punkty, emoji, sekcje „PROBLEM/ROZWIĄZANIE”) i nie skracać go automatycznie bez wyraźnej dyrektywy.
        **Uwaga dot. emoji i encodingu:** emoji w changelogu mogą powodować problemy z kodowaniem w `.exe` na starszych wersjach Windows (brak czcionki Segoe UI Emoji lub niepoprawne locale). Przy budowaniu EXE przez PyInstaller należy upewnić się, że plik źródłowy jest zapisany w UTF-8 i że `sys.stdout` jest odpowiednio skonfigurowany.
## Zasady pracy z bazą danych (SQLite + database_manager)

    Wszystkie połączenia do baz:

        - wyłącznie przez `sqlite3.connect(get_db_path("...db"))` z `database_manager.py`,
        - brak bezpośrednich ścieżek typu `"C:\\Users\\..."` albo `"systemy_rpg.db"`.
        - **zawsze używać context managera:** `with sqlite3.connect(get_db_path(...)) as conn:` — gwarantuje commit lub rollback bez ręcznego zarządzania transakcją.

    Każde nowo otwierane połączenie musi ustawiać:

```python
conn.row_factory = sqlite3.Row          # dostęp do kolumn po nazwie, nie po indeksie
conn.execute("PRAGMA foreign_keys = ON")  # wymuszenie integralności referencyjnej
```

    Operacje I/O na bazach:

        w razie wątpliwości korzystać z istniejących helperów w database_manager.py (ścieżki, backupy, migracje),

        przy nowych migracjach: dopisać je do mechanizmu wersjonowania schematów zamiast robić „ukryte” ALTER TABLE w logice UI.

    Złożone operacje:

        N+1 query pattern należy zastępować zapytaniami zbiorczymi (JOIN/GROUP BY) w stylu, który już został zastosowany w sesje_rpg.py (zmiana z 2800+ połączeń na 3 niezależnie od liczby sesji).

    Indeksy i wydajność:

        przy dużych tabelach (sesje, systemy) rozważyć dodanie indeksów na kolumnach filtrowanych (np. rok, system, MG, status) w ramach migracji; nie tworzyć indeksów „na żywo” w UI.
    Architektura wielu baz — uzasadnienie i ograniczenia:

        Projekt celowo utrzymuje 4 oddzielne pliki `.db` (`systemy_rpg.db`, `sesje_rpg.db`, `gracze.db`, `wydawcy.db`) dla rozdzielenia kontekstów domenowych i uproszczenia backupów/migracji per-moduł.

        **Zakaz:** nie używać `ATTACH DATABASE` do łączenia baz "na żywo" w czasie działania aplikacji bez osobnej decyzji architektonicznej — może prowadzić do trudnych w debugowaniu zależności między bazami. Zapytania cross-bazowe realizować przez denormalizację lub buforowanie w pamięci.
## Skalowanie, DPI, geometria

    Wszelka logika dot. DPI i geometrii dialogów:

        centralnie w dialog_utils.py + powiązania w main.py (skalowanie okna głównego, clampowanie do ekranu, margines na taskbar),

        nowe dialogi nie powinny wywoływać geometry() „na piechotę” bez apply_safe_geometry().

    Globalne skalowanie fontów:

        każda nowa kontrolka z własnym fontem ma używać scale_font_size() z font_scaling.py,

        w matplotlib: także korzystać z aktualnego font_scale_factor (statystyki już to robią — nowe wykresy dopasowywać do tego systemu).

        **Uwaga:** `font_scale_factor` jest zmienną globalną — zmiana skali w trakcie aktywnych operacji UI (np. podczas przebudowy zakładki lub rysowania wykresu) może prowadzić do race condition. Zmianę skali należy zawsze inicjować z głównego wątku Tk i poczekać na zakończenie bieżącego cyklu renderowania (np. przez `root.update_idletasks()`) przed odczytem nowej wartości w wątku tła.

## Wykresy i statystyki

    statystyki.py odpowiada za:

        zbieranie danych z baz (przez get_db_path()),

        agregowanie ich do struktur używanych przez wykresy,

        tworzenie i odświeżanie figur matplotlib.

    Nowe statystyki:

        logikę agregacji danych umieszczać w funkcjach pomocniczych w statystyki.py (lub dedykowanym module statystyk),

        UI (np. zakładka Statystyki) tylko woła te funkcje i renderuje wynik, nie robi samodzielnych zapytań SQL.

    Odświeżanie:

        po każdej operacji CRUD w systemach/sesjach/graczach/wydawcach statystyki są automatycznie odświeżane (już zaimplementowane) — nowe funkcje nie mogą tego mechanizmu psuć.

## Testowanie

Projekt nie posiada automatycznych testów jednostkowych. Obowiązuje następujące podejście:

- **Logika domenowa** (funkcje w `systemy_rpg.py`, `sesje_rpg.py`, `gracze.py`, `wydawcy.py`, `statystyki.py`) powinna być pisana tak, aby dało się ją wywołać i przetestować **bez uruchamiania GUI** — bez zależności od `tkinter`, `CTk` ani aktywnego okna.
- **Funkcje pomocnicze** (np. `get_all_systems()`, `apply_filters()`, `build_stats_data()`) są priorytetem dla ewentualnych testów w przyszłości.
- **Agent nie powinien generować testów automatycznie** chyba że użytkownik wprost o to prosi. Jeśli prosi — użyć `pytest` i umieszczać testy w katalogu `tests/` (który nie istnieje jeszcze w projekcie).
- **Manualne weryfikowanie** zmian: po każdej modyfikacji logiki domenowej agent powinien wskazać, jakie scenariusze warto sprawdzić ręcznie w aplikacji.

## Obsługa błędów i logowanie

    Logowanie:

        używać wbudowanego logging z konfiguracją rotacji plików (np. debug_sesyjka.log, sesyjka_debug.log) tak jak w istniejących modułach (dialog_utils.py, apphistory.py, inne),

        nowy kod powinien reużywać istniejącego loggera (logging.getLogger(__name__)) zamiast tworzyć własne systemy.

    Błędy Tk/CTk:

        report_callback_exception() w SesyjkaApp jest miejscem na przechwytywanie „benign” błędów Tk (np. TclError: bad window path przy zamykaniu okien) — nowy kod nie powinien ich „połykac” lokalnie, jeśli mogą być obsłużone globalnie.

    Brak pustych except::

        zawsze logować wyjątek (lub przynajmniej go przekazać wyżej),

        wyjątek: globalny handler w main.py / SesyjkaApp z jasno opisanym komentarzem.

## Zachowanie agenta AI w projekcie Sesyjka

### Kiedy zadawać pytania doprecyzowujące

Zadawaj pytania, gdy:

    wymaganie użytkownika dotyczy nowego feature’a bez jasnego zakresu:

        np. „dodaj raport sesji” → dopytać: zakres czasowy, poziom szczegółowości, format (tabela/wykres/eksport), powiązanie z istniejącymi statystykami,

    zmiana dotyka schematu bazy:

        dodanie nowych kolumn, tabel, relacji, indeksów — trzeba doprecyzować jak ma działać migracja i kompatybilność wsteczna,

    są co najmniej dwa sensowne warianty UX / architektury:

        nowa funkcja jako osobna zakładka czy dodatkowy dialog,

        rozszerzenie istniejącej tabeli vs. nowa tabela/raport.

### Jak proponować zmiany i refaktoryzację

    Przed większą zmianą:

        opisz krótko plan (maks. kilka punktów) i zapytaj o akceptację,

        pokaż, jak wpisuje się w obecną strukturę (np. „dodajemy nowy moduł raporty.py, integracja z statystyki.py i nową zakładką w main.py”).

    Przy refaktorze istniejących modułów (systemy_rpg.py, sesje_rpg.py, gracze.py, wydawcy.py, statystyki.py, ctk_table.py):

        nie zmieniaj publicznego API bez potrzeby (np. nazw funkcji używanych w wielu miejscach),

        jeżeli API trzeba zmienić — opisz konsekwencje i wskaż wszystkie miejsca w projekcie, których dotknie zmiana.

    Duże zadania dziel na kroki:

            decyzje dot. schematu / danych,

            implementacja w bazie (database_manager + migracje),

            logika Python (moduły domenowe/statystyki),

            integracja z UI (tabele, dialogi, wykresy).

### Styl generowanego kodu

    Zgodny z istniejącym stylem:

        użycie scale_font_size(),

        użycie helperów z dialog_utils.py i database_manager.py,

        spójny pattern w ctk_table.py (bez dublowania logiki w innych plikach).

    Każdy nowy moduł/funkcja:

        - krótki docstring,
        - type hints zgodnie z PEP 484 (patrz sekcja „Konwencje nazewnicze i styl kodu"),
        - deklaracje Pyright tam, gdzie konieczne (np. `# pyright: reportUnknownMemberType=false`).

## Komendy projektu (ze źródeł)

Referencyjnie (README):

```bash
git clone https://github.com/ZuraffPL/sesyjka.git
cd sesyjka

python -m venv .venv
.venv\Scripts\activate

pip install customtkinter tksheet matplotlib Pillow

python main.py
```

Wszelkie dodatkowe zależności (np. nowe pakiety zewnętrzne) należy dopisać w README **oraz** w `requirements.txt` z podpiętymi wersjami (np. `customtkinter==5.2.2`). Plik `requirements.txt` jest wymagany w projekcie — nie opcjonalny. Przykład:

```
customtkinter==5.2.2
tksheet==7.x.x
matplotlib==3.x.x
Pillow==10.x.x
```