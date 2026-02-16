# pyright: reportUnknownMemberType=false
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk  # type: ignore
from font_scaling import scale_font_size

def show_version_history_dialog(parent, app_name="Sesyjka"): # type: ignore
    """
    Wyświetla okno dialogowe z historią wersji aplikacji.
    
    Args:
        parent: Okno rodzicielskie
        app_name: Nazwa aplikacji
    """
    # Utwórz okno modalnie
    dialog = ctk.CTkToplevel(parent) # type: ignore
    dialog.title("Historia wersji")
    dialog.geometry("620x820")
    dialog.resizable(True, True)
    dialog.transient(parent) # type: ignore
    dialog.grab_set()
    
    # Wyśrodkuj okno względem rodzica
    dialog.update_idletasks()
    x = (parent.winfo_x() + (parent.winfo_width() // 2)) - 310 # type: ignore
    y = (parent.winfo_y() + (parent.winfo_height() // 2)) - 410 # type: ignore
    dialog.geometry(f"+{x}+{y}")
    
    # Główny frame
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Tytuł
    title_label = ctk.CTkLabel(
        main_frame,
        text=f"{app_name} - Historia wersji",
        font=('Segoe UI', scale_font_size(20), 'bold')
    )
    title_label.pack(pady=(10, 15))
    
    # Separator
    separator = ttk.Separator(main_frame, orient='horizontal')
    separator.pack(fill=tk.X, pady=(0, 15))
    
    # Scrollable Frame dla zawartości
    scrollable_frame = ctk.CTkScrollableFrame(main_frame, width=550, height=600)
    scrollable_frame.pack(fill=tk.BOTH, expand=True)
    
    # Historia wersji
    version_history = [ # type: ignore
        {
            "version": "0.3.16",
            "date": "16.02.2026",
            "changes": [
                "🐛 FIX: NAPRAWIONO SKALOWANIE FONTÓW:\n",
                "",
                "❌ PROBLEM 1 - RIBBON NA DOLE:",
                "  • Po użyciu suwaka skalowania fontów ribbon",
                "    renderował się na dole okna zamiast na górze",
                "  • Przyczyna: ribbon był zmienną lokalną, niszczoną",
                "    przez ogólną pętlę po wszystkich widgetach",
                "  • Notebook był już zapakowany z expand=True",
                "    i zajmował całą przestrzeń",
                "",
                "✅ ROZWIĄZANIE 1:",
                "  • Zmiana ribbon na self.ribbon (zmienna instancji)",
                "  • Poprawiono niszczenie: self.ribbon.destroy()",
                "  • Dodano notebook.pack_forget() przed odbudową",
                "  • Przepakowanie notebook po odbudowie ribbona",
                "  • Ribbon zawsze pozostaje na górze",
                "",
                "❌ PROBLEM 2 - BRAK SKALOWANIA W TABELACH:",
                "  • Skalowanie działało tylko w ribbonie",
                "  • Tabele tksheet (systemy/sesje/gracze/wydawcy)",
                "    nie skalowały fontów",
                "  • Brakowało konfiguracji font w Sheet.set_options()",
                "",
                "✅ ROZWIĄZANIE 2:",
                "  • Dodano brakujący import w sesje_rpg.py",
                "  • Zaktualizowano 4 moduły z tabelami:",
                "    - systemy_rpg.py (line 776-780)",
                "    - sesje_rpg.py (line 251-255)",
                "    - gracze.py (line 314-318)",
                "    - wydawcy.py (line 200-204)",
                "  • Dodano sheet.set_options() z fontami:",
                "    font=(\"Segoe UI\", scale_font_size(10), \"normal\")",
                "    header_font=(\"Segoe UI\", scale_font_size(10), \"bold\")",
                "",
                "✨ NOWA FUNKCJA - ELASTYCZNE SYSTEMY GŁÓWNE:\n",
                "",
                "🎯 SUGESTIA UŻYTKOWNIKA:",
                "  • Czasem dodajesz suplement do gry, której",
                "    nie masz w kolekcji jako system główny",
                "  • Brak możliwości wpisania niestandardowej nazwy",
                "",
                "✅ ROZWIĄZANIE - DWIE METODY:",
                "  1️⃣ WYBÓR Z KOLEKCJI:",
                "     • Dropdown \"System główny (opcjonalnie)\"",
                "     • Wybierz system z listy jeśli go posiadasz",
                "     • Wyświetli nazwę z bazy danych",
                "",
                "  2️⃣ WPISANA NAZWA:",
                "     • Pole \"lub wpisz nazwę:\" obok dropdowna",
                "     • Wpisz nazwę gry spoza kolekcji",
                "     • Nazwa wyświetli się w kolumnie \"System główny\"",
                "",
                "💾 IMPLEMENTACJA:",
                "  • Nowa kolumna: system_glowny_nazwa_custom",
                "  • Zaktualizowano get_all_systems()",
                "  • Formularz dodawania: szerokość 700→950px",
                "  • Formularz edycji: szerokość 700→950px",
                "  • Layout: dropdown i pole tekstowe obok siebie",
                "  • Lepsze dla panoramicznych monitorów",
                "",
                "🎨 LOGIKA WYŚWIETLANIA:",
                "  • Priorytet 1: Jeśli wybrano z listy → nazwa z bazy",
                "  • Priorytet 2: Jeśli wpisano custom → custom nazwa",
                "  • Edycja: wybór z listy zastępuje custom nazwę",
                "",
                "📐 LAYOUT FORMULARZY:",
                "  • Pole custom w tym samym row co dropdown",
                "  • Okna szersze zamiast wyższe",
                "  • Rozmiary: 950px/1100px (zamiast 700px/850px)",
                "  • Responsive: columnconfigure(3, weight=1)",
                "  • Wszystkie pola przesunięte o 1 row w dół"
            ]
        },
        {
            "version": "0.3.15",
            "date": "16.02.2026",
            "changes": [
                "✨ GLOBALNE SKALOWANIE FONTÓW (80%-120%):\n",
                "",
                "🎯 PROBLEM: PREFERENCJE UŻYTKOWNIKÓW:",
                "  • Testerzy zgłaszali różne potrzeby:",
                "    - Niektórzy: domyślne fonty za małe",
                "    - Inni: domyślne fonty za duże",
                "  • Rozdzielczości ekranów 1080p, 2K, 4K różnią się",
                "  • Brak uniwersalnej wielkości dla wszystkich",
                "",
                "✅ ROZWIĄZANIE - SUWAK W RIBBON:",
                "  • Nowy moduł: font_scaling.py z funkcją scale_font_size()",
                "  • Suwak w sekcji ribbon (80%-120%, 8 kroków)",
                "  • Zaktualizowano 96 specyfikacji fontów w 9 plikach:",
                "    - main.py (10), about_dialog.py (6)",
                "    - gracze.py (18), wydawcy.py (4)",
                "    - systemy_rpg.py (6), sesje_rpg_dialogs.py (2)",
                "    - sesje_rpg.py (0), statystyki.py (33)",
                "    - apphistory.py (5), font_scaling.py (12)",
                "",
                "🔧 DZIAŁANIE:",
                "  • Font 12 → scale_font_size(12):",
                "    - 80%  = 10 (min 8)",
                "    - 100% = 12 (domyślnie)",
                "    - 120% = 14",
                "  • Matplotlib również skaluje (wykresy statystyk)",
                "  • Zmiana natychmiastowa - ribbon się odbudowuje",
                "  • Wszystkie elementy UI: dialogi, przyciski,",
                "    labele, tabele zachowują proporcje",
                "",
                "💾 SZCZEGÓŁY TECHNICZNE:",
                "  • Slider: 0.8-1.2 z krokiem 0.05",
                "  • Zmienna globalna font_scale_factor",
                "  • Funkcje: set/get_font_scale_factor()",
                "  • Minimum: 8px (ochrona czytelności)",
                "  • Ribbon rebuild po każdej zmianie"
            ]
        },
        {
            "version": "0.3.14",
            "date": "16.02.2026",
            "changes": [
                "🐛 NAPRAWIONO WSZYSTKIE POZOSTAŁE HARDCODED ŚCIEŻKI:\n",
                "",
                "✅ PROBLEM: HARDCODED ŚCIEŻKI W STATYSTYKACH I SESJACH:",
                "  • 11 miejsc w kodzie używało hardcoded ścieżek do baz",
                "  • statystyki.py (6 odwołań):",
                "    - sesje_rpg.db, gracze.db, systemy_rpg.db",
                "  • sesje_rpg.py (5 odwołań):",
                "    - systemy_rpg.db (3x), gracze.db (2x)",
                "  • Aplikacja szukała baz w katalogu aplikacji",
                "    zamiast w AppData/Local/Sesyjka/",
                "",
                "✅ ROZWIĄZANIE:",
                "  • Dodano import get_db_path do statystyki.py",
                "  • Zamieniono wszystkie 11 hardcoded ścieżek na get_db_path()",
                "  • Wszystkie 56 wywołań sqlite3.connect() w projekcie",
                "    używają teraz poprawnych ścieżek",
                "",
                "🆕 NOWY TYP SUPLEMENTU:",
                "  • Dodano 'Starter/Zestaw Startowy' do typów suplementów",
                "  • Dostępny w formularzach dodawania i edycji systemów RPG",
                "  • 6 typów suplementów zamiast 5",
                "",
                "📐 DOSTOSOWANIE OKIEN DIALOGOWYCH:",
                "  • Zwiększono wysokość okien o +30px (6 checkboxów)",
                "  • Dodawanie systemu: 520→550px, 720→750px, 850→880px",
                "  • Edycja systemu: 560→590px, 720→750px, 850→880px",
                "  • Dodawanie suplementu: 650→680px"
            ]
        },
        {
            "version": "0.3.13",
            "date": "14.02.2026",
            "changes": [
                "🐛 NAPRAWIONO KRYTYCZNY BUG DIALOGU SESJI RPG:\n",
                "",
                "✅ PROBLEM: PUSTE OKNO DODAWANIA SESJI RPG:",
                "  • Dialog 'Dodaj sesję RPG do bazy' otwierał się pusty",
                "  • Brak list systemów RPG i graczy w formularzu",
                "  • Przyczyna: hardcoded ścieżki 'systemy_rpg.db' i 'gracze.db'",
                "    w module sesje_rpg_dialogs.py",
                "  • Moduł dialogów szukał baz w katalogu aplikacji",
                "    zamiast w AppData/Local/Sesyjka/",
                "",
                "✅ ROZWIĄZANIE:",
                "  • Naprawiono 2 funkcje w sesje_rpg_dialogs.py:",
                "    - get_all_systems() - lista systemów RPG w formularzu",
                "    - get_all_players() - lista graczy w formularzu",
                "  • Zastąpiono hardcoded ścieżki wywołaniami get_db_path()",
                "  • Analogiczny bug do naprawionego w v0.3.12 (wydawcy.db)"
            ]
        },
        {
            "version": "0.3.12",
            "date": "13.02.2026",
            "changes": [
                "🐛 NAPRAWIONO KRYTYCZNY BUG LISTY WYDAWCÓW:\n",
                "",
                "✅ PROBLEM: NOWI WYDAWCY NIE WIDOCZNI W SYSTEMACH RPG:",
                "  • Wydawcy dodani po wersji 0.3.7 nie pojawiali się",
                "    na liście wydawców w formularzach systemów RPG",
                "  • Przyczyna: hardcoded ścieżka 'wydawcy.db' zamiast",
                "    get_db_path('wydawcy.db') w module systemy_rpg.py",
                "  • Moduł systemów RPG czytał starą bazę z katalogu",
                "    aplikacji zamiast aktualnej z AppData",
                "",
                "✅ ROZWIĄZANIE:",
                "  • Naprawiono 3 miejsca w systemy_rpg.py z błędną ścieżką:",
                "    - get_all_publishers() - lista wydawców w comboboxach",
                "    - fill_systemy_rpg_tab() - nazwy wydawców w tabeli głównej",
                "    - Sekcja suplementów - nazwy wydawców w tabeli suplementów",
                "  • Wszystkie odwołania do wydawcy.db używają teraz get_db_path()",
                "",
                "✅ ULEPSZENIE ODŚWIEŻANIA LISTY WYDAWCÓW:",
                "  • Kliknięcie w combobox wydawcy automatycznie odświeża listę",
                "  • Pobieranie aktualnych danych bezpośrednio z bazy przy kliknięciu",
                "  • Działa we wszystkich 3 formularzach:",
                "    - Dodawanie systemu RPG",
                "    - Edycja systemu RPG",
                "    - Dodawanie suplementu",
                "",
                "🔧 CZYSZCZENIE KODU:",
                "  • Usunięto niedziałający system callbacków odświeżania",
                "  • Usunięto zbędne przyciski odświeżania (🔄)",
                "  • Uproszczony, niezawodny mechanizm refresh-on-click"
            ]
        },
        {
            "version": "0.3.11",
            "date": "13.02.2026",
            "changes": [
                "🎮 WSPARCIE DLA PLATFORM VTT (VIRTUAL TABLETOP):\n",
                "",
                "✅ NOWA FUNKCJA - VTT DLA SYSTEMÓW RPG:",
                "  • Dodano kolumnę VTT w bazie systemów RPG",
                "  • Opcja zaznaczenia, czy system wspiera VTT",
                "  • Po zaznaczeniu pojawia się lista 9 platform VTT",
                "  • Multi-select: możliwość wyboru wielu platform jednocześnie",
                "",
                "✅ DOSTĘPNE PLATFORMY VTT:",
                "  • AboveVTT (D&D Beyond companion)",
                "  • Alchemy VTT",
                "  • D&D Beyond",
                "  • Demiplane",
                "  • Fantasy Grounds (Unity)",
                "  • Foundry VTT",
                "  • Roll20",
                "  • Tabletop Simulator",
                "  • Telespire",
                "",
                "✅ INTERFEJS:",
                "  • Checkbox 'VTT' w formularzach dodawania/edycji",
                "  • Dynamiczne rozwijanie listy platform po zaznaczeniu",
                "  • Scrollowalny panel z platformami VTT",
                "  • Checkboxy dla każdej platformy",
                "  • Wyświetlanie wybranych platform w tabeli",
                "  • Inteligentne dopasowanie rozmiaru okna dialogu",
                "",
                "🔧 NAPRAWIONO KRYTYCZNE BŁĘDY FILTROWANIA:\n",
                "",
                "✅ PROBLEM: RESETOWANIE FILTRÓW PO EDYCJI:",
                "  • Filtry znikały po dodaniu/edycji/usunięciu rekordów",
                "  • Naprawiono we wszystkich 4 tabelach:",
                "    - Sesje RPG (sesje_rpg.py)",
                "    - Systemy RPG (systemy_rpg.py)",
                "    - Gracze (gracze.py)",
                "    - Wydawcy (wydawcy.py)",
                "",
                "✅ PROBLEM: BŁĘDNE INDEKSOWANIE W FILTRACH:",
                "  • Edycja/usuwanie rekordów operowało na złych wierszach",
                "  • Menu kontekstowe używało indeksów pełnej listy zamiast filtrowanej",
                "  • Mogło to prowadzić do edycji/usunięcia niewłaściwych rekordów",
                "",
                "✅ ROZWIĄZANIE - DISPLAYED_DATA:",
                "  • Wprowadzono zmienną displayed_data w każdej tabeli",
                "  • Przechowuje tylko aktualnie widoczne rekordy",
                "  • Wszystkie operacje (edycja, usuwanie) używają displayed_data",
                "  • Sortowanie i kolorowanie działa na displayed_data",
                "  • Auto-przywracanie aktywnych filtrów po odświeżeniu",
                "",
                "✅ BEZPIECZEŃSTWO DANYCH:",
                "  • Poprawne indeksowanie eliminuje ryzyko modyfikacji złych rekordów",
                "  • Filtry pozostają aktywne po wszystkich operacjach CRUD",
                "  • Spójność między wyświetlanym widokiem a bazą danych",
                "",
                "📊 ZAKRES NAPRAWY:",
                "  • 4 moduły tabel zaktualizowane",
                "  • Wszystkie funkcje kontekstowe (edycja, usuwanie)",
                "  • Wszystkie funkcje sortowania",
                "  • Wszystkie funkcje filtrowania",
                "  • Wykrywanie linków (w tabelach gracze i wydawcy)"
            ]
        },
        {
            "version": "0.3.10",
            "date": "13.02.2026",
            "changes": [
                "🔧 POPRAWKA WYKRYWANIA ROZDZIELCZOŚCI (KRYTYCZNA):\n",
                "",
                "✅ FIZYCZNA ROZDZIELCZOŚĆ EKRANU:",
                "  • Naprawiono wykrywanie rozdzielczości na Windows",
                "  • Aplikacja ignoruje teraz skalowanie DPI Windows",
                "  • Użycie EnumDisplaySettings dla fizycznej rozdzielczości",
                "  • SetProcessDpiAwareness przed wykrywaniem",
                "",
                "🐛 ROZWIĄZANY PROBLEM:",
                "  • Windows z 2880x1800 i skalowaniem 300%",
                "  • Aplikacja wykrywała 1920x1200 (logiczną) zamiast 2880x1800 (fizyczną)",
                "  • Teraz poprawnie wykrywa 2880x1800 i stosuje 167% skalowania",
                "",
                "🔧 SZCZEGÓŁY TECHNICZNE:",
                "  • Użycie ctypes.windll.shcore.SetProcessDpiAwareness(2)",
                "  • Użycie ctypes.windll.user32.EnumDisplaySettingsW",
                "  • Struktura DEVMODE do odczytu dmPelsWidth/Height",
                "  • Fallback do GetSystemMetrics jeśli EnumDisplaySettings zawiedzie",
                "  • Fallback do tkinter dla Linux/Mac",
                "",
                "📊 WYNIK:",
                "  • Poprawne wykrywanie rozdzielczości niezależnie od skalowania Windows",
                "  • Okno 'O programie' pokazuje teraz fizyczną rozdzielczość",
                "  • Odpowiednie skalowanie interfejsu dla monitorów 2K/4K"
            ]
        },
        {
            "version": "0.3.9",
            "date": "13.02.2026",
            "changes": [
                "🖥️ AUTOMATYCZNE SKALOWANIE DPI DLA WYSOKICH ROZDZIELCZOŚCI:\n",
                "",
                "✅ INTELIGENTNE WYKRYWANIE ROZDZIELCZOŚCI:",
                "  • Automatyczne wykrywanie rozdzielczości ekranu przy starcie",
                "  • Dynamiczne obliczanie współczynnika skalowania",
                "  • Bazowa rozdzielczość: 1920x1080 (Full HD)",
                "  • Maksymalne skalowanie: 250% dla ekranów 5K+",
                "",
                "✅ SKALOWANIE PROPORCJONALNE:",
                "  • 1920x1080 (Full HD) → 100% (bez skalowania)",
                "  • 2560x1440 (QHD) → 133% skalowania",
                "  • 2800x1800 → 167% skalowania",
                "  • 3840x2160 (4K) → 200% skalowania",
                "",
                "✅ INFORMACJE W APLIKACJI:",
                "  • Okno 'O programie' pokazuje wykrytą rozdzielczość",
                "  • Wyświetlany współczynnik skalowania w procentach",
                "  • Komunikaty w konsoli przy starcie (debug)",
                "",
                "📊 ZALETY SKALOWANIA:",
                "  • Elementy interfejsu pozostają czytelne na dużych ekranach",
                "  • Czcionki skalują się proporcjonalnie",
                "  • Przyciski i kontrolki zachowują odpowiedni rozmiar",
                "  • Brak mikroskopijnych elementów na ekranach 4K",
                "",
                "🔧 TECHNICZNE:",
                "  • Wykorzystanie CustomTkinter set_widget_scaling()",
                "  • Wykorzystanie CustomTkinter set_window_scaling()",
                "  • Zaokrąglanie do 0.1 dla lepszej wydajności",
                "  • Zabezpieczenia przed błędami wykrywania"
            ]
        },
        {
            "version": "0.3.8",
            "date": "13.02.2026",
            "changes": [
                "🗄️ SYSTEM ZARZĄDZANIA BAZAMI DANYCH - BEZPIECZNE AKTUALIZACJE:\n",
                "",
                "✅ NOWA LOKALIZACJA BAZ DANYCH:",
                "  • Windows: C:\\Users\\{username}\\AppData\\Local\\Sesyjka\\",
                "  • Linux/Mac: ~/.sesyjka/",
                "  • Bazy są teraz przechowywane w folderze użytkownika",
                "  • Bezpieczne miejsce, niezależne od lokalizacji aplikacji",
                "",
                "✅ AUTOMATYCZNA MIGRACJA:",
                "  • System automatycznie przenosi stare bazy do nowej lokalizacji",
                "  • Podczas migracji tworzone są automatyczne backupy",
                "  • Oryginalne bazy pozostają nietknięte",
                "  • Proces migracji jest transparentny dla użytkownika",
                "",
                "✅ SYSTEM WERSJONOWANIA SCHEMATU:",
                "  • Każda baza ma przypisaną wersję schematu",
                "  • Automatyczne wykrywanie czy baza wymaga aktualizacji",
                "  • Bezpieczne migracje schematu z automatycznymi backupami",
                "  • Brak możliwości konfliktu przy aktualizacji aplikacji",
                "",
                "✅ BACKUPY I BEZPIECZEŃSTWO:",
                "  • Automatyczne backupy przed każdą migracją",
                "  • Backupy przechowywane w folderze 'backups'",
                "  • Format: nazwa_bazy.backup_YYYYMMDD_HHMMSS",
                "  • Możliwość łatwego przywrócenia poprzedniej wersji",
                "",
                "✅ KOMPATYBILNOŚĆ WSTECZNA:",
                "  • Stare bazy działają z nową wersją aplikacji",
                "  • System automatycznie aktualizuje schemat gdy potrzebny",
                "  • Twoje dane są bezpieczne przy każdej aktualizacji",
                "  • Nie ma ryzyka utraty danych podczas update'u",
                "",
                "✅ NOWY MODUŁ:",
                "  • database_manager.py - zarządzanie bazami i migracjami",
                "  • API do tworzenia backupów i sprawdzania wersji",
                "  • Dokumentacja w MIGRATION_GUIDE.md",
                "",
                "✅ AKTUALIZACJA WSZYSTKICH MODUŁÓW:",
                "  • systemy_rpg.py - używa nowego systemu ścieżek",
                "  • sesje_rpg.py - używa nowego systemu ścieżek",
                "  • gracze.py - używa nowego systemu ścieżek",
                "  • wydawcy.py - używa nowego systemu ścieżek",
                "  • main.py - inicjalizacja przez database_manager"
            ]
        },
        {
            "version": "0.3.7",
            "date": "13.02.2026",
            "changes": [
                "🔄 SYSTEM STATUSÓW - ULEPSZENIE LOGIKI:\n",
                "",
                "✅ STATUS 'NA SPRZEDAŻ':",
                "  • Status 'Na sprzedaż' wyświetla się jako 'W kolekcji, Na sprzedaż'",
                "  • Logiczne podejście: przedmiot na sprzedaż musi być w posiadaniu",
                "  • Wyświetlanie: '{status_gry}, W kolekcji, Na sprzedaż'",
                "  • Przykład: 'Grane, W kolekcji, Na sprzedaż'",
                "",
                "✅ OBSŁUGA CENY ZAKUPU:",
                "  • Dla statusu 'Na sprzedaż' wyświetla się cena zakupu",
                "  • W formularzach dodawania/edycji pole ceny zakupu jest dostępne",
                "  • Logika: przedmiot na sprzedaż ma cenę zakupu (jak 'W kolekcji')",
                "  • Format: cena + waluta (np. '150.00 PLN')",
                "",
                "✅ FILTRY I KOLOROWANIE:",
                "  • Filtry działają poprawnie dla nowego formatu statusu",
                "  • Czerwone podświetlenie wierszy 'Na sprzedaż' nadal aktywne",
                "  • Sprawdzanie statusu używa operatora 'in' dla elastyczności",
                "",
                "✅ ZAKRES ZMIAN:",
                "  • Moduł: systemy_rpg.py",
                "  • Funkcja wyświetlania: get_all_systems()",
                "  • Funkcje dodawania: dodaj_system_rpg(), dodaj_suplement_do_systemu()",
                "  • Funkcja edycji: edit_system_rpg_dialog()",
                "  • Funkcje obsługi formularzy: on_status_kolekcja_change() (3 wystąpienia)"
            ]
        },
        {
            "version": "0.3.6",
            "date": "13.02.2026",
            "changes": [
                "🔄 ODŚWIEŻANIE I FILTRY - ULEPSZENIA UX:",
                "",
                "✅ ZACHOWANIE FILTRÓW:",
                "  • Filtry są teraz przechowywane na poziomie modułu",
                "  • Po dodaniu nowego rekordu filtry pozostają aktywne",
                "  • Dotyczy wszystkich zakładek:",
                "    - 🎲 Systemy RPG",
                "    - ⚔️ Sesje RPG",
                "    - 👥 Gracze",
                "    - 🏢 Wydawcy",
                "  • Filtry resetują się tylko po wybraniu 'Resetuj' lub zamknięciu aplikacji",
                "",
                "✅ AUTOMATYCZNE ODŚWIEŻANIE STATYSTYK:",
                "  • Statystyki automatycznie aktualizują się po:",
                "    - Dodaniu nowego systemu RPG",
                "    - Usunięciu systemu RPG",
                "    - Dodaniu nowej sesji RPG",
                "    - Usunięciu sesji RPG",
                "    - Dodaniu gracza",
                "    - Usunięciu gracza",
                "    - Dodaniu wydawcy",
                "    - Usunięciu wydawcy",
                "  • Wykresy w zakładce Statystyki są zawsze aktualne",
                "  • Brak potrzeby ręcznego odświeżania po zmianach",
                "",
                "✅ PRZYCISK ODŚWIEŻANIA STATYSTYK:",
                "  • Nowy przycisk '🔄 Odśwież statystyki' w zakładce Statystyki",
                "  • Umożliwia ręczne wymuszenie odświeżenia wykresów",
                "  • Zielony design zgodny z motywem aplikacji",
                "  • Umieszczony obok tytułu dla łatwego dostępu",
                "",
                "✅ POPRAWKI TECHNICZNE:",
                "  • Naprawa błędów typowania w plikach:",
                "    - about_dialog.py",
                "    - apphistory.py",
                "    - statystyki.py",
                "    - systemy_rpg.py",
                "    - wydawcy.py",
                "    - gracze.py",
                "  • Dodano dyrektywy pyright dla lepszego type checking",
                "  • Kod zgodny ze standardami Python 3.9+"
            ]
        },
        {
            "version": "0.3.5",
            "date": "16.01.2026",
            "changes": [
                "📊 STATYSTYKI - ROZBUDOWA I OPTYMALIZACJA:",
                "",
                "✅ UKŁAD STATYSTYK:",
                "  • Zmiana z 2 na 3 kolumny statystyk",
                "  • Optymalizacja szerokości kolumn dla ekranów 1080p:",
                "    - Kolumna 1: 220px (wykres kołowy - kompaktowy)",
                "    - Kolumna 2: 320px (MG vs Gracz)",
                "    - Kolumna 3: 450px (Systemy - długie nazwy)",
                "  • Jednolita wysokość wszystkich ramek statystyk (500px)",
                "  • Wszystkie statystyki widoczne bez przewijania",
                "",
                "✅ STATYSTYKA 1 - SESJE RPG WEDŁUG ROKU:",
                "  • Przeniesienie legendy nad wykres (wycentrowana)",
                "  • Powiększenie wykresu kołowego: 3.2x2.8 → 4.2x3.5",
                "  • Powiększenie elementów legendy:",
                "    - Kwadraty kolorów: 16x16 → 20x20",
                "    - Font legendy: 9 → 10",
                "    - Font na wykresie: 9 → 11",
                "  • Zwiększone odstępy dla lepszej czytelności",
                "  • Optymalne wykorzystanie dostępnej przestrzeni",
                "",
                "✅ STATYSTYKA 2 - MG VS GRACZ:",
                "  • Dodano wybór roku (Combobox z listą lat)",
                "  • Dynamiczna aktualizacja wykresu po zmianie roku",
                "  • Usunięto legendę z prawej strony wykresu",
                "  • Dodano procenty w nawiasach w rozpisie na lata:",
                "    - Format: '🎲 MG: 34 (79.1%)'",
                "    - Format: '👥 Gracz: 9 (20.9%)'",
                "  • Kompaktowy układ rozpisu na lata:",
                "    - Zmniejszone odstępy między wierszami (5px → 2px)",
                "    - Zmniejszone odstępy między kolumnami (10px → 5px)",
                "    - Zmniejszone fonty dla lepszego dopasowania (12/11 → 11/10)",
                "  • Lista wszystkich lat z pełną statystyką na dole",
                "  • Podsumowanie dla wszystkich lat razem",
                "",
                "✅ STATYSTYKA 3 - SYSTEMY RPG: ILOŚĆ SESJI:",
                "  • Zwiększenie szerokości kolumny (420px → 450px)",
                "  • Naprawa ucinania ostatniej cyfry roku",
                "  • Wybór roku z rozwijanej listy",
                "  • Poziomy wykres słupkowy z sortowaniem:",
                "    - Systemy z największą liczbą sesji na górze",
                "    - Pełne nazwy systemów widoczne",
                "  • Zapytania SQL między wieloma bazami danych",
                "  • Podsumowanie: Ilość systemów i sesji w wybranym roku",
                "",
                "✅ POPRAWKI TECHNICZNE:",
                "  • Naprawa błędu 'bad window path name' w matplotlib canvas",
                "  • Poprawna hierarchia widgetów w ramkach",
                "  • Optymalizacja renderowania wykresów",
                "  • Responsywny layout z weight dla kolumn",
                "  • Lepsza adaptacja do trybu ciemnego"
            ]
        },
        {
            "version": "0.3.0",
            "date": "10.01.2026",
            "changes": [
                "🎉 DUŻA AKTUALIZACJA - CUSTOMTKINTER:",
                "",
                "✅ MODERNIZACJA INTERFEJSU:",
                "  • Pełna migracja do CustomTkinter - nowoczesny, płaski design",
                "  • Zaokrąglone przyciski z animacjami hover",
                "  • Natywny przełącznik (switch) dla trybu ciemnego",
                "  • Kolorowe przyciski: Dodaj (zielone), Usuń (czerwone), Zapisz (zielone)",
                "  • Wszystkie dialogi zmigrowane do CTkToplevel",
                "  • CTkEntry z placeholder_text dla lepszego UX",
                "  • CTkComboBox zamiast ttk.Combobox",
                "  • CTkCheckBox z emoji (⭐, 👑)",
                "",
                "✅ STATYSTYKI I WYKRESY:",
                "  • Nowa zakładka 📊 Statystyki",
                "  • Wykres kołowy - sesje RPG według roku",
                "  • Wykres kołowy - główny użytkownik jako MG vs Gracz",
                "  • Integracja z matplotlib dla profesjonalnych wykresów",
                "  • Siatka 2-kolumnowa dla statystyk",
                "",
                "✅ GRACZE - STATUS OSOBY:",
                "  • Kolumna Status (Główny użytkownik ⭐ / Ważna osoba 👑)",
                "  • Wizualna identyfikacja: złoty kolor dla głównego, fioletowy dla ważnych",
                "  • Wzajemne wykluczanie statusów",
                "  • Filtrowanie i sortowanie według statusu",
                "",
                "✅ ZMIGROWANE MODUŁY:",
                "  • main.py - główne okno i ribbon",
                "  • gracze.py - dialogi dodawania i edycji",
                "  • wydawcy.py - dialogi dodawania, edycji i usuwania",
                "  • about_dialog.py - okno O programie",
                "  • apphistory.py - historia wersji"
            ]
        },
        {
            "version": "0.2.8",
            "date": "09.01.2026",
            "changes": [
                "✅ PRZYGOTOWANIE DO CUSTOMTKINTER:",
                "  • Instalacja biblioteki CustomTkinter",
                "  • Instalacja matplotlib dla wykresów",
                "  • Utworzenie backupu projektu",
                "  • Testy kompatybilności"
            ]
        },
        {
            "version": "0.2.7",
            "date": "09.01.2026",
            "changes": [
                "✅ INTERFEJS UŻYTKOWNIKA:",
                "  • Dodano przełącznik trybu jasny/ciemny w ribbonie",
                "  • Przełącznik zachowuje stan po zmianie trybu",
                "  • Uproszczona obsługa przełączania motywów",
                "",
                "✅ SYSTEMY RPG - ŚLEDZENIE CEN:",
                "  • Dodano pole Cena zakupu dla pozycji 'W kolekcji'",
                "  • Dodano pole Cena sprzedaży dla pozycji 'Sprzedane'",
                "  • Obsługa 4 walut: PLN, USD, EUR, GBP",
                "  • Automatyczna konwersja separatora dziesiętnego (przecinek → kropka)",
                "  • Kolumna 'Cena' w widoku głównym",
                "  • Sortowanie po cenie",
                "  • Filtrowanie po walucie",
                "",
                "✅ POPRAWKI:",
                "  • Naprawiono stabilność przełącznika trybu",
                "  • Usunięto nieużywane importy",
                "  • Zoptymalizowano kod przełączania motywów"
            ]
        },
        {
            "version": "0.2.6",
            "date": "03.01.2026",
            "changes": [
                "✅ FILTROWANIE DANYCH:",
                "  • Dodano kompleksowe filtrowanie w zakładce Sesje RPG:",
                "    - Filtr po Roku",
                "    - Filtr po Systemie",
                "    - Filtr po Typie sesji (Kampania/Jednostrzał)",
                "    - Filtr po Mistrzu Gry",
                "  • Dodano filtrowanie w zakładce Gracze:",
                "    - Filtr po Płci",
                "    - Filtr po Imieniu i nazwisku (Wpisane/Puste)",
                "    - Filtr po Social media (Wpisane/Puste)",
                "  • Dodano filtrowanie w zakładce Wydawcy:",
                "    - Filtr po Kraju",
                "    - Filtr po Stronie (Wpisane/Puste)",
                "  • Dodano zaawansowane filtrowanie w zakładce Systemy RPG:",
                "    - Filtr po Typie (Podręcznik Główny/Suplement)",
                "    - Filtr po Wydawcy",
                "    - Filtr po Posiadaniu (Fizyczny/PDF/Oba/Żadne)",
                "    - Filtr po Języku",
                "    - Filtr po Statusie",
                "  • Wszystkie okna filtrowania wycentrowane na środku ekranu",
                "  • Licznik aktywnych filtrów na przycisku",
                "  • Możliwość resetowania wszystkich filtrów",
                "",
                "✅ SYSTEMY RPG - NOWE STATUSY:",
                "  • Dodano nowe statusy kolekcji:",
                "    - Nieposiadane (szare wyróżnienie)",
                "    - Do kupienia (fioletowe wyróżnienie)",
                "  • Kolory statusu działają w trybie jasnym i ciemnym",
                "  • Zaktualizowane filtrowanie po statusie",
                "",
                "✅ POPRAWKI:",
                "  • Naprawione błędy typów we wszystkich modułach",
                "  • Poprawione obsługa trybu ciemnego w dialogach",
                "  • Ulepszona kompatybilność z Python 3.9+"
            ]
        },
        {
            "version": "0.2.2",
            "date": "19.09.2025",
            "changes": [
                "✅ SYSTEMY RPG:",
                "  • Dodano system statusów gry: Grane/Nie grane",
                "  • Dodano system statusów kolekcji: W kolekcji/Na sprzedaż/Sprzedane",
                "  • Czerwone wyróżnienie pozycji na sprzedaż",
                "  • Pola statusu w oknach dodawania i edycji systemów",
                "  • Poprawione pozycjonowanie przycisków w dialogach",
                "",
                "✅ INTERFEJS:",
                "  • Zwiększone wysokości okien dialogowych",
                "  • Dodano historię wersji aplikacji",
                "  • Zaktualizowane informacje o programie"
            ]
        },
        {
            "version": "0.2.1",
            "date": "18.09.2025",
            "changes": [
                "✅ SESJE RPG:",
                "  • Poprawione filtrowanie dropdown - tylko podręczniki główne",
                "  • Usunięto suplementy z listy wyboru systemów w sesjach",
                "",
                "🐛 POPRAWKI:",
                "  • Naprawione błędy indeksowania w wyświetlaniu danych",
                "  • Poprawiona struktura bazy danych"
            ]
        },
        {
            "version": "0.2.0",
            "date": "15.09.2025", 
            "changes": [
                "🎉 PIERWSZA PEŁNA WERSJA:",
                "",
                "✅ SYSTEMY RPG:",
                "  • Hierarchiczny widok podręczników i suplementów",
                "  • Dodawanie, edycja i usuwanie systemów",
                "  • Multi-wybór typów suplementów",
                "  • Kolorowe wyróżnienia typów publikacji",
                "  • Menu kontekstowe z opcjami edycji",
                "",
                "✅ SESJE RPG:",
                "  • Zarządzanie sesjami z datami i uczestnikami",
                "  • Wybór graczy i Mistrza Gry",
                "  • Kolorowanie wierszy według miesięcy",
                "  • Walidacja konfliktów",
                "",
                "✅ GRACZE I WYDAWCY:",
                "  • Pełne zarządzanie bazami danych",
                "  • Kolorowanie wierszy według płci (gracze)",
                "",
                "✅ INTERFEJS:",
                "  • Nowoczesna wstążka z kolorowymi przyciskami",
                "  • Zakładki z ikonami emoji",
                "  • Tryb jasny i ciemny",
                "  • Spójny design we wszystkich oknach"
            ]
        },
        {
            "version": "0.1.0",
            "date": "10.09.2025",
            "changes": [
                "🚀 WERSJA ROZWOJOWA:",
                "  • Podstawowa struktura aplikacji",
                "  • Implementacja baz danych SQLite",
                "  • Podstawowe operacje CRUD",
                "  • Prototyp interfejsu użytkownika"
            ]
        }
    ]
    
    # Dodaj każdą wersję jako osobną sekcję
    for version_info in version_history: # type: ignore
        # Frame dla wersji
        version_frame = ctk.CTkFrame(scrollable_frame)
        version_frame.pack(fill=tk.X, pady=(0, 15), padx=5)
        
        # Nagłówek wersji
        header_frame = ctk.CTkFrame(version_frame, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        version_label = ctk.CTkLabel(
            header_frame,
            text=f"Wersja {version_info['version']}",
            font=('Segoe UI', scale_font_size(14), 'bold'),
            text_color="#1976D2"
        )
        version_label.pack(side=tk.LEFT)
        
        date_label = ctk.CTkLabel(
            header_frame,
            text=version_info['date'], # type: ignore
            font=('Segoe UI', scale_font_size(12))
        )
        date_label.pack(side=tk.RIGHT)
        
        # Lista zmian
        changes_text = "\n".join(version_info['changes']) # type: ignore
        changes_label = ctk.CTkLabel(
            version_frame,
            text=changes_text,
            font=('Segoe UI', scale_font_size(11)),
            justify=tk.LEFT,
            anchor='w'
        )
        changes_label.pack(fill=tk.X, padx=15, pady=(0, 10))
    
    # Frame dla przycisku zamknij
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.pack(fill=tk.X, pady=(15, 0))
    
    # Przycisk zamknij
    close_button = ctk.CTkButton(
        button_frame,
        text="Zamknij",
        font=('Segoe UI', scale_font_size(11)),
        width=120,
        fg_color="#666666",
        hover_color="#555555",
        command=dialog.destroy
    )
    close_button.pack(side=tk.RIGHT)
    
    # Obsługa klawisza Escape
    dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    # Ustaw focus na przycisk zamknij
    close_button.focus_set()
    
    # Zaczekaj aż okno zostanie zamknięte
    dialog.wait_window()