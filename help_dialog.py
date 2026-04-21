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
           "ich kolejności przyciskami ↑/↓; ustawienie zapisywane w settings.json."),
    ("li", "Ukryj systemy — checkbox w pasku tabeli Systemy RPG; po włączeniu widoczne są "
           "tylko PG i suplementy (wiersze-systemy ukryte)."),
    ("h2", "Edycja rekordów"),
    ("li", "Kliknij ikonę ✏️ w wierszu lub dwukliknij wiersz, aby otworzyć dialog edycji."),
    ("li", "Kliknij nagłówek kolumny, aby posortować po danej kolumnie (przełącza rosnąco/malejąco)."),
    ("li", "Prawym przyciskiem myszy (PPM) na wierszu otwiera menu kontekstowe z opcjami edycji i usunięcia."),
    ("h2", "Pola rekordu PG / Suplementu"),
    ("li", "Nazwa/Tytuł * — wymagana nazwa podręcznika lub suplementu."),
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
    ("li", "System RPG — wybór z listy systemów w bazie."),
    ("li", "Typ sesji — np. Kampania, One-shot, Konwentowa."),
    ("li", "Mistrz Gry — wybór gracza pełniącego funkcję MG."),
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
    ("li", "GUI: Python + CustomTkinter."),
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
