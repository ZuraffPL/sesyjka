# pyright: reportUnknownMemberType=false
import tkinter as tk
from tkinter import ttk
import webbrowser
import customtkinter as ctk  # type: ignore

def show_about_dialog(parent, app_name="Sesyjka", app_version="0.3.9"): # type: ignore
    """
    Wyświetla okno dialogowe "O programie" z informacjami o aplikacji.
    
    Args:
        parent: Okno rodzicielskie
        app_name: Nazwa aplikacji
        app_version: Wersja aplikacji
    """
    # Importuj współczynnik skalowania z main
    try:
        from main import current_dpi_scale
        dpi_scale = current_dpi_scale
    except:
        dpi_scale = 1.0
    
    # Utwórz okno modalnie
    dialog = ctk.CTkToplevel(parent) # type: ignore
    dialog.title("O programie")
    dialog.geometry("520x720")
    dialog.resizable(False, False)
    dialog.transient(parent) # type: ignore
    dialog.grab_set()
    
    # Wyśrodkuj okno względem rodzica
    dialog.update_idletasks()
    x = (parent.winfo_x() + (parent.winfo_width() // 2)) - 260 # type: ignore
    y = (parent.winfo_y() + (parent.winfo_height() // 2)) - 360 # type: ignore
    dialog.geometry(f"+{x}+{y}")
    
    # Główny frame
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Nazwa aplikacji (duży, pogrubiony font)
    title_label = ctk.CTkLabel(
        main_frame,
        text=app_name,
        font=('Segoe UI', 28, 'bold')
    )
    title_label.pack(pady=(10, 5))
    
    # Wersja
    version_label = ctk.CTkLabel(
        main_frame,
        text=f"Wersja {app_version}",
        font=('Segoe UI', 14)
    )
    version_label.pack(pady=(0, 15))
    
    # Separator
    separator = ttk.Separator(main_frame, orient='horizontal')
    separator.pack(fill=tk.X, pady=(0, 15))
    
    # Frame dla informacji
    info_frame = ctk.CTkFrame(main_frame)
    info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    # Scrollable text widget dla opisu funkcjonalności
    text_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
    text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    # CTkTextbox dla tekstu
    text_widget = ctk.CTkTextbox(
        text_frame,
        wrap=tk.WORD,
        font=('Segoe UI', 11)
    )
    
    # Treść z opisem funkcjonalności
    content = f"""AUTOR I KONTAKT:
Autor: Marcin "Żuraff" Żurawicz
Kontakt: https://linktr.ee/zuraffpl
Wesprzyj mnie na Patronite: https://patronite.pl/zuraff

TECHNOLOGIE:
• Język: Python 3.9+
• GUI: CustomTkinter + tkinter
• Arkusze: tksheet
• Wykresy: matplotlib
• Baza danych: SQLite

SKALOWANIE INTERFEJSU:
• Wykryta rozdzielczość: {dialog.winfo_screenwidth()}x{dialog.winfo_screenheight()} pikseli
• Współczynnik skalowania: {dpi_scale:.1f}x ({int(dpi_scale * 100)}%)
• Bazowa rozdzielczość: 1920x1080 (Full HD)
ℹ️ Interfejs automatycznie dostosowuje się do rozdzielczości ekranu

FUNKCJONALNOŚCI:

SYSTEMY RPG:
• Hierarchiczny widok podręczników głównych i suplementów
• Dodawanie, edycja i usuwanie systemów RPG
• Multi-wybór typów suplementów (np. Bestiariusz + Przygoda)
• System statusów gry: Grane/Nie grane
• System statusów kolekcji: W kolekcji/Na sprzedaż/Sprzedane/Nieposiadane/Do kupienia
• Czerwone wyróżnienie pozycji na sprzedaż
• Szare wyróżnienie pozycji nieposiadanych
• Fioletowe wyróżnienie pozycji do kupienia
• Zaawansowane filtrowanie: Typ, Wydawca, Posiadanie, Język, Status
• Sortowanie z zachowaniem hierarchii
• Kolorowe wyróżnienia typów publikacji
• Menu kontekstowe z opcjami edycji
• Automatyczne dopasowanie szerokości okien

SESJE RPG:
• Zarządzanie sesjami z datami i uczestnikami
• Wybór graczy i Mistrza Gry przez dedykowane okna
• Kolorowanie wierszy według miesięcy
• Kompleksowe filtrowanie: Rok, System, Typ sesji, Mistrz Gry
• Sortowanie i filtrowanie danych
• Walidacja konfliktów (gracz nie może być jednocześnie MG)

GRACZE:
• Baza danych graczy z informacjami osobowymi
• Kolorowanie wierszy według płci
• Filtrowanie po: Płeć, Imię i nazwisko, Social media
• Zarządzanie danymi kontaktowymi

WYDAWCY:
• Katalog wydawców gier RPG
• Filtrowanie po: Kraj, Strona (wpisane/puste)
• Zarządzanie informacjami o wydawcach

INTERFEJS UŻYTKOWNIKA:
• 🎨 CustomTkinter - nowoczesny, płaski design z zaokrąglonymi rogami
• Nowoczesna wstążka z kolorowymi przyciskami (✚ zielony, ✖ czerwony)
• Zakładki z ikonami emoji (🎲 Systemy, ⚔️ Sesje, 👥 Gracze, 🏢 Wydawcy, 📊 Statystyki)
• Natywny przełącznik (switch) dla trybu jasny/ciemny
• Animacje hover na przyciskach
• Spójny tryb ciemny w WSZYSTKICH oknach dialogowych
• Okna filtrowania wycentrowane na środku ekranu
• Liczniki aktywnych filtrów na przyciskach
• Informacje o programie (ℹ️) i Historia wersji (📋)
• Responsywny design dostosowujący się do zawartości

STATYSTYKI:
• Układ 3-kolumnowy zoptymalizowany dla ekranów 1080p
• Statystyka 1: Sesje RPG według roku - wykres kołowy z legendą nad wykresem
• Statystyka 2: Główny użytkownik MG vs Gracz - wybór roku, wykres kołowy
• Statystyka 3: Systemy RPG: Ilość sesji - wykres słupkowy poziomy z wyborem roku
• Podział sesji po latach z procentami w statystyce MG vs Gracz
• Profesjonalne wykresy matplotlib z adaptacją do trybu ciemnego
• Kompaktowy układ z automatycznym scrollem
• Sortowanie systemów według liczby sesji (malejąco)
• 🔄 Przycisk odświeżania statystyk
• Automatyczne odświeżanie po dodaniu/usunięciu rekordów

DODATKOWE FUNKCJE:
• Zaawansowane filtrowanie we wszystkich zakładkach
• Zachowanie filtrów po dodaniu nowych rekordów
• Możliwość resetowania filtrów jednym kliknięciem
• Automatyczne odświeżanie widoków i statystyk
• Walidacja danych wejściowych
• Obsługa skrótów klawiszowych
• Eksport i import danych
• Backup automatyczny baz danych"""

    text_widget.insert('1.0', content)
    text_widget.configure(state='disabled')
    
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    # Frame dla przycisków
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.pack(fill=tk.X)
    
    # Link do strony autora
    def open_author_link():
        webbrowser.open("https://linktr.ee/zuraffpl")
    
    author_button = ctk.CTkButton(
        button_frame,
        text="Strona autora",
        font=('Segoe UI', 11),
        width=120,
        fg_color="#1976D2",
        hover_color="#1565C0",
        command=open_author_link
    )
    author_button.pack(side=tk.LEFT, pady=(10, 0))

    # Link do wsparcia
    def open_support_link():
        webbrowser.open("https://patronite.pl/zuraff")
    
    support_button = ctk.CTkButton(
        button_frame,
        text="💖 Wesprzyj mnie",
        font=('Segoe UI', 11),
        width=140,
        fg_color="#C62828",
        hover_color="#B71C1C",
        command=open_support_link
    )
    support_button.pack(side=tk.LEFT, pady=(10, 0), padx=(15, 0))

    # Przycisk zamknij
    close_button = ctk.CTkButton(
        button_frame,
        text="Zamknij",
        font=('Segoe UI', 11),
        width=100,
        fg_color="#666666",
        hover_color="#555555",
        command=dialog.destroy
    )
    close_button.pack(side=tk.RIGHT, pady=(10, 0))
    
    # Obsługa klawisza Escape
    dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    # Ustaw focus na przycisk zamknij
    close_button.focus_set()
    
    # Zaczekaj aż okno zostanie zamknięte
    dialog.wait_window()
