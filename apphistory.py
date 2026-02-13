# pyright: reportUnknownMemberType=false
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk  # type: ignore

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
        font=('Segoe UI', 20, 'bold')
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
            font=('Segoe UI', 14, 'bold'),
            text_color="#1976D2"
        )
        version_label.pack(side=tk.LEFT)
        
        date_label = ctk.CTkLabel(
            header_frame,
            text=version_info['date'], # type: ignore
            font=('Segoe UI', 12)
        )
        date_label.pack(side=tk.RIGHT)
        
        # Lista zmian
        changes_text = "\n".join(version_info['changes']) # type: ignore
        changes_label = ctk.CTkLabel(
            version_frame,
            text=changes_text,
            font=('Segoe UI', 11),
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
        font=('Segoe UI', 11),
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