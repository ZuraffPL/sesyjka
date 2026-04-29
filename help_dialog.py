"""
Okno pomocy / instrukcji obsługi aplikacji Sesyjka.
Zawiera opis wszystkich funkcjonalności programu.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any
import customtkinter as ctk  # type: ignore
import logging
from font_scaling import scale_font_size
from dialog_utils import apply_safe_geometry, create_ctk_toplevel

_log = logging.getLogger(__name__)

# ── Treść pomocy ──────────────────────────────────────────────────────────────
# Każdy element to (typ, tekst) gdzie typ to:
#   "h1"  — nagłówek sekcji głównej
#   "h2"  — nagłówek podsekcji
#   "p"   — akapit normalny
#   "li"  — punkt listy (z •)
#   "sep" — poziomy separator
_HELP_CONTENT: list[tuple[str, str]] = [
    ("h1", "Instrukcja obsługi Sesyjki"),
    ("p",  "Sesyjka to desktopowy menedżer baz danych dla graczy i mistrzów gry w "
           "systemy TTRPG. Umożliwia katalogowanie podręczników, suplementów, sesji, "
           "graczy i wydawców."),
    ("sep", ""),

    ("h1", "📖 Zakładka: Systemy RPG"),
    ("p",  "Główna biblioteka podręczników i suplementów RPG. Dane wyświetlane są w "
           "hierarchicznej tabeli: System → Podręczniki Główne → Suplementy."),
    ("h2", "Przyciski ribbonu"),
    ("li", "✚ Dodaj System — dodaje nowy wpis do katalogu systemów RPG (np. D&D, Warhammer). "
           "Jest to kategoria nadrzędna, do której przypisuje się podręczniki."),
    ("li", "✚ Dodaj PG/Suplement — dodaje podręcznik główny (PG) lub suplement do wybranego "
           "systemu. Wymaga wcześniejszego istnienia systemu."),
    ("li", "🗑 Usuń — usuwa zaznaczony wiersz (system, podręcznik lub suplement)."),
    ("li", "⚙ Migruj dane — dostępny tylko gdy istnieją stare dane wymagające migracji "
           "do nowej struktury hierarchicznej. Znika po zakończeniu migracji."),
    ("h2", "Pasek narzędziowy tabeli"),
    ("li", "Sortuj — wybierz kolumnę sortowania z listy (ID, Nazwa systemu, Wydawca, Język, "
           "Status, Posiadanie, Cena), następnie kliknij Rosnąco lub Malejąco."),
    ("li", "Filtruj — otwiera panel filtrów: Typ, Język, Status, Wydawca, Posiadanie (PDF/Fizyczny/VTT). "
           "Każdy filtr obsługuje multi-wybór za pomocą toggle-buttonów — kliknij kilka opcji, "
           "aby wyświetlić rekordy spełniające dowolną z nich. Przyciski zawijają się "
           "do nowych wierszy gdy opcji jest dużo."),
    ("li", "Rozwiń wszystko / Zwiń wszystko — przełącza widoczność podrzędnych wierszy "
           "w tabeli hierarchicznej."),
    ("li", "Szukaj — wyszukiwanie tekstowe w czasie rzeczywistym po nazwie systemu."),
    ("li", "Kolumny — umożliwia ukrycie/pokazanie wybranych kolumn tabeli oraz zmianę "
           "ich kolejności przyciskami \u2191/\u2193; ustawienie zapisywane w settings.json. "
           "W sekcji Opcje tabeli znajduje się checkbox \u201ePokaż przycisk edycji\u201d \u2014 "
           "po odznaczeniu ikona \u270f\ufe0f jest ukryta (edycja dostępna przez dwuklik)."),
    ("li", "Ukryj systemy — checkbox w pasku tabeli Systemy RPG; po włączeniu widoczne są "
           "tylko PG i suplementy (wiersze-systemy ukryte)."),
    ("h2", "Edycja rekordów"),
    ("li", "Kliknij ikonę ✏️ w wierszu lub dwukliknij wiersz, aby otworzyć dialog edycji."),
    ("li", "Kliknij nagłówek kolumny, aby posortować po danej kolumnie (przełącza rosnąco/malejąco)."),
    ("li", "Prawym przyciskiem myszy (PPM) na wierszu otwiera menu kontekstowe z opcjami edycji i usunięcia."),
    ("h2", "Pola rekordu PG / Suplementu"),    ("li", "Nazwa/Tytuł * — wymagana nazwa podręcznika lub suplementu."),
    ("li", "Typ — Podręcznik Główny lub Suplement."),
    ("li", "System główny — dla suplementów: opcjonalny wybór systemu-rodzica z kolekcji."),
    ("li", "Wydawca — wybór z listy wydawców (można dodać nowego przyciskiem ➕ Dodaj wydawcę)."),
    ("li", "Fizyczny / PDF / VTT — zaznaczenie formy posiadania."),
    ("li", "Cena Fizyczna / Cena PDF / Cena VTT — osobna cena dla każdej formy posiadania "
           "(wyświetlana dynamicznie po zaznaczeniu odpowiedniej formy)."),
    ("li", "Język — PL, ENG, DE, FR, ES, IT."),
    ("li", "Status — Posiadam, Chcę kupić, Przeczytane itp."),
    ("li", "Notatki — dowolny tekst."),
    ("sep", ""),

    ("h1", "🎲 Zakładka: Sesje RPG"),
    ("p",  "Dziennik rozegranych sesji. Umożliwia rejestrację każdej sesji z pełnymi metadanymi."),
    ("h2", "Przyciski ribbonu"),
    ("li", "✚ Dodaj Sesję RPG — otwiera formularz nowej sesji."),
    ("li", "🗑 Usuń — usuwa zaznaczoną sesję."),
    ("h2", "Pola sesji"),
    ("li", "Data — picker kalendarza, domyślnie dzisiaj."),
    ("li", "System RPG — filtrowalne pole tekstowe: wpisz fragment nazwy, aby zawęzić "
           "listę propozycji, a następnie kliknij lub wybierz z listy. "
           "Przycisk ➕ obok pola otwiera formularz dodawania nowego systemu RPG "
           "bez zamykania formularza sesji — lista systemów odświeża się automatycznie."),
    ("li", "Typ sesji — np. Kampania, One-shot, Konwentowa."),
    ("li", "Mistrz Gry — wybór gracza pełniącego funkcję MG. "
           "Checkbox \u201eGra GM-less\u201d (obok przycisku wybóru) pozwala oznaczyć sesję bez Mistrza Gry — "
           "w tabeli sesji wyświetlane jako N/A."),
    ("li", "Gracze — lista graczy uczestniczących w sesji (wielokrotny wybór). "
           "Można dodać nowego gracza bezpośrednio z formularza sesji."),
    ("li", "Notatki — opis sesji, podsumowanie fabuły itp."),
    ("h2", "Filtrowanie i sortowanie"),
    ("li", "Pasek narzędziowy obsługuje filtrowanie po systemie, MG, roku i typie sesji. "
           "Filtry mają multi-wybór: klikaj kolejne opcje (toggle-buttony), aby zawęzić widok "
           "do wielu wartości jednocześnie. Brak zaznaczenia = pokaż wszystko."),
    ("li", "Sortowanie po dacie, systemie, MG."),
    ("sep", ""),

    ("h1", "👥 Zakładka: Gracze"),
    ("p",  "Baza danych graczy uczestniczących w sesjach."),
    ("li", "✚ Dodaj Gracza — formularz z imieniem, pseudonimem i notatkami."),
    ("li", "🗑 Usuń — usuwa gracza (uwaga: usunięcie gracza będącego MG sesji wymaga "
           "ręcznej korekty sesji)."),
    ("li", "Edycja — kliknij ikonę ✏️ lub dwukliknij wiersz."),
    ("li", "Kolumny — przycisk w górnym pasku zakładki Gracze; otwiera dialog z "
           "checkboxami widoczności kolumn i przyciskami \u2191/\u2193 do zmiany kolejności. "
           "W sekcji Opcje tabeli: checkbox \u201ePokaż przycisk edycji\u201d. Ustawienia zapisywane w settings.json."),
    ("sep", ""),

    ("h1", "🏢 Zakładka: Wydawcy"),
    ("p",  "Katalog wydawców gier RPG powiązanych z podręcznikami w bazie."),
    ("li", "✚ Dodaj Wydawcę — nazwa (wymagana), strona internetowa, kraj."),
    ("li", "🗑 Usuń — usuwa wydawcę (nie usuwa powiązanych podręczników — tylko rozłącza relację)."),
    ("li", "Edycja — kliknij ikonę ✏️ lub dwukliknij wiersz."),
    ("sep", ""),

    ("h1", "📊 Zakładka: Statystyki"),
    ("p",  "Wykresy i zestawienia danych z całej bazy. Odświeżane automatycznie po "
           "każdej operacji CRUD."),
    ("li", "Liczba sesji w czasie — wykres słupkowy liczby sesji per rok."),
    ("li", "Sesje według systemu — rozkład sesji na systemy RPG."),
    ("li", "Aktywność graczy — liczba sesji per gracz."),
    ("li", "Posiadanie — procent podręczników w formie fizycznej, PDF, VTT."),
    ("li", "Wartość kolekcji — łączna szacowana wartość podręczników."),
    ("sep", ""),

    ("h1", "🔧 Panel kontrolny (prawy górny róg)"),
    ("h2", "Skala czcionki"),
    ("p",  "Suwak 80%–120% skaluje czcionkę w całej aplikacji (tabele, dialogi, "
           "wykresy). Ustawienie jest zapamiętywane między uruchomieniami."),
    ("h2", "Tryb jasny / ciemny"),
    ("p",  "Przełącznik między jasnym (domyślnym) a ciemnym motywem interfejsu. "
           "Zmiana jest natychmiastowa i zapamiętywana."),
    ("sep", ""),

    ("h1", "💾 Bazy danych i pliki"),
    ("p",  "Aplikacja przechowuje dane w czterech plikach SQLite w katalogu:"),
    ("p",  "%LOCALAPPDATA%\\Sesyjka\\"),
    ("li", "systemy_rpg.db — podręczniki i systemy RPG."),
    ("li", "sesje_rpg.db — sesje i powiązania sesja–gracz."),
    ("li", "gracze.db — gracze."),
    ("li", "wydawcy.db — wydawcy."),
    ("p",  "Ustawienia (sortowanie, filtry, motyw, skala czcionki) są zapisywane w pliku "
           "settings.json w tym samym katalogu."),
    ("sep", ""),

    ("h1", "📤 Transfer danych"),
    ("p",  "Okno transferu danych umożliwia eksport i import wszystkich baz do/z pliku "
           "archiwum lub arkusza kalkulacyjnego. Dostępne z przycisku w ribbonie."),
    ("h2", "Eksport"),
    ("li", "ZIP — pakuje wszystkie 4 pliki .db do archiwum. Przydatny do backupu i "
           "przenoszenia całej bazy między komputerami."),
    ("li", "Excel (.xlsx) — eksportuje wszystkie bazy do jednego pliku .xlsx. Każda tabela "
           "SQLite to osobny arkusz (nazwa: Label — tabela). Wiersz nagłówkowy ma niebieskie tło "
           "i białą pogrubioną czcionkę. Szerokości kolumn są automatycznie dopasowane (maks. 50 znaków). "
           "Wymaga zainstalowanego pakietu openpyxl (dołączonego do exe)."),
    ("h2", "Import"),
    ("li", "Wybierz archiwum ZIP zawierające pliki .db. Aplikacja zastąpi bieżące bazy "
           "danymi z archiwum i automatycznie przeprowadzi migrację do aktualnego schematu."),
    ("li", "Przed importem wykonywana jest automatyczna kopia zapasowa bieżących danych."),
    ("sep", ""),

    ("h1", "👁️ Tryb gościa"),
    ("p",  "Tryb gościa umożliwia przeglądanie danych z innego archiwum ZIP bez "
           "nadpisywania własnej bazy. Dostępny z przycisku w ribbonie."),
    ("li", "W trybie gościa wszystkie operacje zapisu są zablokowane: ikona ✏️, "
           "podwójne kliknięcie, menu PPM oraz przyciski Dodaj/Usuń są nieaktywne lub "
           "pokazują komunikat ostrzegawczy."),
    ("li", "Ribbon wyświetla pomarańczowy pasek z informacją o aktywnym trybie gościa."),
    ("li", "Klikni\u0119cie \u201eWr\u00f3\u0107 do swoich danych\u201d przywraca w\u0142asn\u0105 baz\u0119 i wy\u0142\u0105cza tryb go\u015bcia. "
           "Statystyki od\u015bwie\u017caj\u0105 si\u0119 automatycznie przy klikni\u0119ciu zak\u0142adki."),
    ("sep", ""),

    ("h1", "⌨️ Skróty i wskazówki"),
    ("li", "Enter w polu wyszukiwania — odświeża widok filtrowany."),
    ("li", "Kliknięcie nagłówka kolumny — sortowanie rosnąco/malejąco (przełącza)."),
    ("li", "Przeciągnięcie krawędzi nagłówka kolumny — ręczna zmiana szerokości; ustawienie jest "
           "zapamiętywane między uruchomieniami (settings.json)."),
    ("li", "PPM na wierszu tabeli — menu kontekstowe (edycja, usuń)."),
    ("li", "Podwójne kliknięcie wiersza — szybka edycja rekordu."),
    ("li", "Przycisk ➕ Dodaj wydawcę w formularzu PG — dodaje wydawcę bez zamykania "
           "głównego formularza i automatycznie go zaznacza."),
    ("sep", ""),

    ("h1", "ℹ️ Informacje techniczne"),
    ("li", "Platforma: Windows 10+."),
    ("li", "GUI: Python + CustomTkinter + tkinter/ttk."),
    ("li", "Tabele: CTkDataTable (własny widget) — sortowanie, hierarchia, tooltipy, ikony."),
    ("li", "Wykresy: matplotlib."),
    ("li", "Eksport Excel: openpyxl."),
    ("li", "Baza danych: SQLite (lokalna, bez serwera)."),
    ("li", "Autor: Marcin \"Zuraff\" Żurawicz."),
]


def show_help_dialog(parent: Any) -> None:
    """Wyświetla okno pomocy z instrukcją obsługi aplikacji."""
    _dark: bool = getattr(parent, 'dark_mode', False)
    ctk.set_appearance_mode("dark" if _dark else "light")

    dialog = create_ctk_toplevel(parent)
    dialog.title("Pomoc — instrukcja obsługi")
    dialog.resizable(True, True)
    dialog.transient(parent)
    apply_safe_geometry(dialog, parent, 700, 760)

    # ── Główna ramka ──────────────────────────────────────────────────────
    outer = ctk.CTkFrame(dialog)
    outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    # Nagłówek (stały)
    header = ctk.CTkLabel(
        outer,
        text="📖  Pomoc — Sesyjka",
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(18), weight="bold"),
    )
    header.pack(pady=(12, 4))

    ttk.Separator(outer, orient="horizontal").pack(fill=tk.X, padx=10, pady=(0, 8))

    # ── Scrollowany obszar treści ─────────────────────────────────────────
    scroll = ctk.CTkScrollableFrame(outer)
    scroll.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 8))

    _render_content(scroll, _dark)

    # ── Przycisk zamknięcia ───────────────────────────────────────────────
    close_btn = ctk.CTkButton(
        outer,
        text="Zamknij",
        command=dialog.destroy,
        width=110,
        height=32,
        font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
    )
    close_btn.pack(pady=(0, 10))


def _render_content(parent: Any, dark: bool) -> None:
    """Renderuje elementy treści pomocy w podanym kontenerze."""
    accent_color = "#c8943a" if dark else "#8b5e0a"
    h1_color     = "#f0e6d0" if dark else "#1a1410"
    h2_color     = "#c8943a" if dark else "#6b3a0a"
    p_color      = "#d4c8b0" if dark else "#2a2018"
    li_color     = "#b8a888" if dark else "#3a2e20"
    sep_color    = "#4a3828" if dark else "#c8b090"

    for kind, text in _HELP_CONTENT:
        if kind == "h1":
            lbl = ctk.CTkLabel(
                parent,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(14), weight="bold"),
                text_color=h1_color,
                anchor="w",
                justify="left",
            )
            lbl.pack(fill=tk.X, padx=4, pady=(14, 2))

        elif kind == "h2":
            lbl = ctk.CTkLabel(
                parent,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11), weight="bold"),
                text_color=h2_color,
                anchor="w",
                justify="left",
            )
            lbl.pack(fill=tk.X, padx=12, pady=(8, 1))

        elif kind == "p":
            lbl = ctk.CTkLabel(
                parent,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
                text_color=p_color,
                anchor="w",
                justify="left",
                wraplength=620,
            )
            lbl.pack(fill=tk.X, padx=12, pady=(3, 3))

        elif kind == "li":
            # Ramka z punktorim
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill=tk.X, padx=16, pady=(1, 1))

            ctk.CTkLabel(
                row,
                text="•",
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
                text_color=accent_color,
                width=16,
                anchor="nw",
            ).pack(side=tk.LEFT, anchor="nw", padx=(0, 4))

            ctk.CTkLabel(
                row,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=scale_font_size(11)),
                text_color=li_color,
                anchor="w",
                justify="left",
                wraplength=590,
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, anchor="nw")

        elif kind == "sep":
            frm = tk.Frame(parent, bg=sep_color, height=1)
            frm.pack(fill=tk.X, padx=4, pady=(8, 4))
