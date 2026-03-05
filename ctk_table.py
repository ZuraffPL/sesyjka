"""ctk_table.py – Reużywalny widget tabeli danych dla aplikacji Sesyjka.

Zastępuje tksheet.Sheet w modułach wydawcy, gracze, sesje_rpg, systemy_rpg.
Wspiera:
  • Przycisk szybkiej edycji ✎ po kolumnie ID
  • Kolorowanie wierszy (bg i fg) przez row_color_fn
  • Kolumny-linki (niebieski tekst)
  • Centrowanie wybranych kolumn
  • Callback sortowania po kliknięciu nagłówka
  • Callback kliknięcia w komórkę
  • Callback prawego przycisku myszy
  • Zaznaczanie wierszy lewym kliknięciem (get_selected())
  • Tryb ciemny
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk  # type: ignore
import logging as _logging
import time as _time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

_log = _logging.getLogger(__name__)
# Podłącz do istniejącego handlera sesyjka_debug.log gdy tylko jest dostępny
def _attach_file_handler() -> None:
    try:
        from database_manager import get_app_data_dir  # type: ignore
        if not _log.handlers:
            _log.setLevel(_logging.DEBUG)
            fh = _logging.FileHandler(str(get_app_data_dir() / "sesyjka_debug.log"), encoding="utf-8")
            fh.setFormatter(_logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"))
            _log.addHandler(fh)
    except Exception:
        pass
_attach_file_handler()

try:
    from PIL import Image as _PILImage  # type: ignore
    from PIL import ImageTk as _PILImageTk  # type: ignore
    _pil_ok = True
except ImportError:  # pragma: no cover
    _pil_ok = False

import sys as _sys
from font_scaling import scale_font_size

# ── ikona przycisku edycji (dwa warianty: jasny/ciemny) ──────────────────────────
_edit_photo_light: Optional[Any] = None
_edit_photo_dark:  Optional[Any] = None

def _get_icon_path() -> Optional[Path]:
    """
    Szuka pliku edit.png w kolejności:
    1. AppData/Local/Sesyjka/Icons/  (skopiowane przez ensure_app_icons na starcie)
    2. sys._MEIPASS/Icons/           (PyInstaller one-file, jeszcze przed skopiowaniem)
    3. folder obok pliku             (tryb deweloperski)
    """
    try:
        from database_manager import get_app_data_dir
        p = get_app_data_dir() / 'Icons' / 'edit.png'
        if p.exists():
            return p
    except Exception:
        pass
    if hasattr(_sys, '_MEIPASS'):
        p2 = Path(getattr(_sys, '_MEIPASS')) / 'Icons' / 'edit.png'
        if p2.exists():
            return p2
    p3 = Path(__file__).parent / 'Icons' / 'edit.png'
    if p3.exists():
        return p3
    return None

def _get_edit_photo(dark: bool = False) -> Optional[Any]:
    """Zwraca ImageTk.PhotoImage z Icons/edit.png, pokolorowaną pod tryb."""
    global _edit_photo_light, _edit_photo_dark
    cached = _edit_photo_dark if dark else _edit_photo_light
    if cached is not None:
        return cached
    if not _pil_ok:
        return None
    icon_path = _get_icon_path()
    if icon_path is None:
        return None
    try:
        img = _PILImage.open(icon_path).convert("RGBA").resize(  # type: ignore
            (16, 16), _PILImage.Resampling.LANCZOS  # type: ignore
        )
        tint = (0x7B, 0xAA, 0xFF) if dark else (0x15, 0x58, 0xD6)
        r, g, b = tint
        pixels = img.load()  # type: ignore
        for y in range(img.height):  # type: ignore
            for x in range(img.width):  # type: ignore
                _, _, _, a = pixels[x, y]  # type: ignore
                if a > 10:
                    pixels[x, y] = (r, g, b, a)  # type: ignore
        photo = _PILImageTk.PhotoImage(img)  # type: ignore
        if dark:
            _edit_photo_dark = photo
        else:
            _edit_photo_light = photo
        return photo
    except Exception:  # pragma: no cover
        return None

# ─── palety kolorów ────────────────────────────────────────────────────────
_L: dict[str, str] = {
    "bg":         "#ffffff",
    "alt":        "#f5f5f5",
    "hover":      "#e8f0fe",
    "sel":        "#c2d9ff",
    "hdr_bg":     "#e2e5ea",
    "hdr_fg":     "#111111",
    "hdr_hover":  "#d0d4db",
    "row_fg":     "#1a1a1a",
    "edit_bg":    "#e8f0fe",
    "edit_hover": "#b8d0f8",
    "edit_fg":    "#1558d6",
    "link_fg":    "#1a0dab",
}
_D: dict[str, str] = {
    "bg":         "#1e1f22",
    "alt":        "#252628",
    "hover":      "#2a3a52",
    "sel":        "#1e3a6e",
    "hdr_bg":     "#2b2d32",
    "hdr_fg":     "#d8d8d8",
    "hdr_hover":  "#3a3c42",
    "row_fg":     "#d8d8d8",
    "edit_bg":    "#2a3a52",
    "edit_hover": "#1a3a5e",
    "edit_fg":    "#7baaff",
    "link_fg":    "#7baaff",
}

_EDIT_W    = 36   # szerokość kolumny przycisku edycji (px)
_ROW_NUM_W = 36   # szerokość kolumny numeru wiersza Lp. (px)
_ROW_H     = 28   # wysokość wiersza danych (px)
_HDR_H     = 30   # wysokość nagłówka (px)


# ─── tooltip ───────────────────────────────────────────────────────────────
class _Tooltip:
    """Prosta dymkowa podpowiedź wyświetlana po najechaniu kursorem."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self._w    = widget
        self._text = text
        self._win: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _: Any = None) -> None:
        if self._win:
            return
        x = self._w.winfo_rootx() + 4
        y = self._w.winfo_rooty() - 28
        self._win = tk.Toplevel(self._w)
        self._win.wm_overrideredirect(True)
        self._win.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self._win, text=self._text, bg="#ffffc0", fg="#222",
            font=("Segoe UI", 9), relief="solid", bd=1, padx=6, pady=2,
        ).pack()

    def _hide(self, _: Any = None) -> None:
        if self._win:
            self._win.destroy()
            self._win = None


# ─── główna klasa tabeli ───────────────────────────────────────────────────
class CTkDataTable(tk.Frame):
    """Scrollowalna tabela danych z przyciskiem szybkiej edycji ✎ po kolumnie ID.

    Parametry
    ---------
    parent
        Kontener nadrzędny.
    headers : list[str]
        Nagłówki kolumn danych.
    col_widths : list[int]
        Szerokości kolumn danych w pikselach.
    data : list[list[Any]]
        Wiersze danych do wyświetlenia.
    edit_callback : Callable[[int, list], None]
        Wywoływana po kliknięciu ✎: (row_idx, row_data).
    id_col : int
        Indeks kolumny ID – ✎ pojawia się zaraz po niej. Domyślnie 0.
    row_color_fn : Callable[[int, list], tuple | str | None] | None
        Opcjonalna funkcja zwracająca:
          - (bg_str, fg_str)  – kolor tła i tekstu,
          - bg_str            – tylko kolor tła,
          - None              – brak nadpisania.
    link_cols : list[int]
        Kolumny renderowane jako linki (niebieski tekst).
    center_cols : list[int]
        Kolumny z centrowaniem tekstu.
    dark_mode : bool
        Czy używać palety ciemnej.
    sort_callback : Callable[[int], None] | None
        Wywoływana (col_idx) po kliknięciu nagłówka kolumny.
    cell_click_callback : Callable[[int, int, list], None] | None
        Wywoływana (row_idx, col_idx, row_data) przy lewym kliku na komórkę.
    right_click_callback : Callable[[int, list, event], None] | None
        Wywoływana (row_idx, row_data, event) przy prawym kliku.
    show_row_numbers : bool
        Jeśli True, wyświetla kolumnę "Lp." przed pierwszą kolumną danych.
    """

    # ── konstruktor ────────────────────────────────────────────────────────
    def __init__(
        self,
        parent: Any,
        *,
        headers: List[str],
        col_widths: List[int],
        data: List[List[Any]],
        edit_callback: Callable[[int, List[Any]], None],
        id_col: int = 0,
        row_color_fn: Optional[Callable[[int, List[Any]], Any]] = None,
        link_cols: Optional[List[int]] = None,
        center_cols: Optional[List[int]] = None,
        dark_mode: bool = False,
        sort_callback: Optional[Callable[[int], None]] = None,
        cell_click_callback: Optional[Callable[[int, int, List[Any]], None]] = None,
        right_click_callback: Optional[Callable[[int, List[Any], Any], None]] = None,
        show_row_numbers: bool = False,
        **kw: Any,
    ) -> None:
        t = _D if dark_mode else _L
        super().__init__(parent, bg=t["bg"], **kw)

        self.headers          = headers
        self.col_widths       = col_widths
        self._data:   List[List[Any]] = list(data)
        self._edit_cb         = edit_callback
        self._id_col          = id_col
        self._color_fn        = row_color_fn
        self._link_cols       = set(link_cols or [])
        self._center_cols     = set(center_cols or [])
        self._sort_cb         = sort_callback
        self._cell_cb         = cell_click_callback
        self._rc_cb           = right_click_callback
        self._show_row_num    = show_row_numbers
        self._theme           = t
        self._row_frames: List[tk.Frame] = []
        self._row_pool:   Dict[Any, tk.Frame] = {}  # ID → ukryta ramka do ponownego użycia
        self._selected_idx:  Optional[int]       = None
        self._selected_data: Optional[List[Any]] = None

        self._build_header()
        self._scroll = ctk.CTkScrollableFrame(self, fg_color=t["bg"])
        self._scroll.pack(fill=tk.BOTH, expand=True)  # type: ignore[misc]
        self._build_rows()

    # ── nagłówek ───────────────────────────────────────────────────────────
    def _build_header(self) -> None:
        t  = self._theme
        hf = tk.Frame(self, bg=t["hdr_bg"], height=_HDR_H)
        hf.pack(fill=tk.X, side=tk.TOP)
        hf.pack_propagate(False)

        x = 0
        if self._show_row_num:
            tk.Label(
                hf, text="Lp.", bg=t["hdr_bg"], fg=t["hdr_fg"],
                font=("Segoe UI", scale_font_size(10), "bold"),
                anchor="center", relief="flat",
            ).place(x=x, y=0, width=_ROW_NUM_W, height=_HDR_H)
            x += _ROW_NUM_W

        for i, (h, w) in enumerate(zip(self.headers, self.col_widths)):
            lbl = tk.Label(
                hf, text=h, bg=t["hdr_bg"], fg=t["hdr_fg"],
                font=("Segoe UI", scale_font_size(10), "bold"),
                anchor="w", padx=4, relief="flat",
            )
            lbl.place(x=x, y=0, width=w, height=_HDR_H)

            if self._sort_cb is not None:
                ci = i
                lbl.bind("<Button-1>", lambda _e, c=ci: self._sort_cb(c))  # type: ignore
                lbl.bind("<Enter>", lambda _e, lb=lbl: lb.configure(bg=t["hdr_hover"]))
                lbl.bind("<Leave>", lambda _e, lb=lbl: lb.configure(bg=t["hdr_bg"]))
                lbl.config(cursor="hand2")

            x += w

            if i == self._id_col:
                # Wąska pusta kolumna ✎ w nagłówku
                tk.Label(hf, text="", bg=t["hdr_bg"]).place(
                    x=x, y=0, width=_EDIT_W, height=_HDR_H
                )
                x += _EDIT_W

        # Wypełnienie prawej części nagłówka za ostatnią kolumną
        tk.Label(hf, text="", bg=t["hdr_bg"]).place(
            x=x, y=0, relwidth=1, width=-x, height=_HDR_H
        )

    # ── wiersze ────────────────────────────────────────────────────────────
    def _pool_key(self, row: Optional[List[Any]]) -> Optional[Any]:
        """Klucz puli ramek: wartość z kolumny id_col lub None."""
        if row is None:
            return None
        if self._id_col < len(row) and row[self._id_col] is not None:
            return row[self._id_col]
        return None

    def _build_rows(self) -> None:
        _t0 = _time.perf_counter()
        new_count = len(self._data)
        old_count = len(self._row_frames)

        # Schowaj nadmiarowe ramki do puli zamiast niszczyć – dzięki temu
        # ponowny expand tego samego systemu to samo pack() bez tworzenia widgetów.
        pooled = destroyed = 0
        for f in self._row_frames[new_count:]:
            f.pack_forget()
            cached_r: Optional[List[Any]] = getattr(f, '_cached_row', None)
            key = self._pool_key(cached_r)
            if key is not None:
                self._row_pool[key] = f
                pooled += 1
            else:
                f.destroy()
                destroyed += 1
        del self._row_frames[new_count:]

        # Zaktualizuj istniejące ramki (cache bez winfo_children())
        refreshed = skipped = 0
        for i in range(min(new_count, old_count)):
            prev = getattr(self._row_frames[i], '_cached_row', None)
            self._refresh_row(i, self._data[i])
            if prev == self._data[i]:
                skipped += 1
            else:
                refreshed += 1

        # Dodaj brakujące ramki (reuse z puli jeśli możliwy)
        pool_before = len(self._row_pool)
        added = 0
        for i in range(old_count, new_count):
            self._add_row(i, self._data[i])
            added += 1
        pool_hits = pool_before - len(self._row_pool)

        # Resetuj selekcję jeśli wypadła poza zakres
        if self._selected_idx is not None and self._selected_idx >= new_count:
            self._selected_idx  = None
            self._selected_data = None

        _t1 = _time.perf_counter()
        _log.debug(
            "CTkDataTable._build_rows: rows=%d  pooled=%d  destroyed=%d  "
            "refreshed=%d  skipped=%d  added=%d(pool_hits=%d)  elapsed=%.1f ms",
            new_count, pooled, destroyed, refreshed, skipped, added, pool_hits,
            (_t1 - _t0) * 1000,
        )

    def _refresh_row(self, i: int, row: List[Any]) -> None:
        """Aktualizuje istniejącą ramkę wiersza in-place (bez destroy Frame).

        Jeśli dane wiersza są identyczne jak przy ostatnim renders, pomija
        kosztowne destroy/recreate dzieci – kluczowa optymalizacja dla
        expand/collapse w hierarchicznej tabeli (systemy RPG).
        """
        rf = self._row_frames[i]
        # ── szybka ścieżka: dane bez zmian → nic nie rób ─────────────────
        cached: Optional[List[Any]] = getattr(rf, '_cached_row', None)
        if cached is not None and cached == row:
            return
        rf._cached_row = list(row)  # type: ignore[attr-defined]
        # Zniszcz tylko dzieci (Label/Button) – Frame zostaje
        for ch in rf.winfo_children():
            ch.destroy()
        def_bg, _ = self._resolve_colors(i, row)
        rf.configure(bg=def_bg)
        self._populate_row(rf, i, row)

    def _resolve_colors(
        self, i: int, row: List[Any]
    ) -> Tuple[str, Optional[str]]:
        """Zwraca (bg, fg_override_or_None) dla wiersza."""
        t      = self._theme
        def_bg = t["alt"] if i % 2 else t["bg"]
        fg_ov: Optional[str] = None

        if self._color_fn:
            result: Any = self._color_fn(i, row)
            if result is not None:
                if isinstance(result, (list, tuple)) and len(result) >= 2:  # type: ignore[arg-type]
                    if result[0]:  # type: ignore[index]
                        def_bg = str(result[0])  # type: ignore[index]
                    fg_ov = str(result[1]) if result[1] else None  # type: ignore[index]
                elif isinstance(result, str):
                    def_bg = result

        return def_bg, fg_ov

    def _add_row(self, i: int, row: List[Any]) -> None:
        key = self._pool_key(row)
        rf: Optional[tk.Frame] = self._row_pool.pop(key, None) if key is not None else None
        if rf is not None:
            cached = getattr(rf, '_cached_row', None)
            if cached == row:
                # Idealne trafienie: dane bez zmian → tylko pack(), zero tworzenia widgetów
                rf.pack(fill=tk.X)
                self._row_frames.append(rf)
                return
            # Reuse ramki, ale odśwież zawartość (zniszcz stare dzieci)
            for ch in rf.winfo_children():
                ch.destroy()
            def_bg, _ = self._resolve_colors(i, row)
            rf.configure(bg=def_bg)
            rf.pack(fill=tk.X)
        else:
            def_bg, _ = self._resolve_colors(i, row)
            rf = tk.Frame(self._scroll, bg=def_bg, height=_ROW_H)
            rf.pack(fill=tk.X)
            rf.pack_propagate(False)
        self._row_frames.append(rf)
        self._populate_row(rf, i, row)
        rf._cached_row = list(row)  # type: ignore[attr-defined]

    def _populate_row(self, rf: tk.Frame, i: int, row: List[Any]) -> None:
        """Tworzy dzieci (Label/Button) wewnątrz ramki rf dla wiersza i."""
        t = self._theme
        def_bg, fg_ov = self._resolve_colors(i, row)

        # ── hover / selekcja ───────────────────────────────────────────
        def _repaint(f: tk.Frame, color: str) -> None:
            f.configure(bg=color)
            for ch in f.winfo_children():
                if isinstance(ch, tk.Label):
                    ch.configure(bg=color)

        def _on_enter(_e: Any, f: tk.Frame = rf, idx: int = i) -> None:
            if self._selected_idx != idx:
                _repaint(f, t["hover"])

        def _on_leave(
            _e: Any, f: tk.Frame = rf, orig: str = def_bg, idx: int = i
        ) -> None:
            if self._selected_idx != idx:
                _repaint(f, orig)

        def _on_click(
            _e: Any,
            row_i: int = i,
            row_d: List[Any] = list(row),
            f: tk.Frame = rf,
            orig: str = def_bg,
        ) -> None:
            # Odznacz poprzedni wiersz
            if (
                self._selected_idx is not None
                and self._selected_idx != row_i
                and self._selected_idx < len(self._row_frames)
            ):
                old_f  = self._row_frames[self._selected_idx]
                old_bg, _ = self._resolve_colors(
                    self._selected_idx, self._data[self._selected_idx]
                )
                _repaint(old_f, old_bg)
            self._selected_idx  = row_i
            self._selected_data = row_d
            _repaint(f, t["sel"])

        rf.bind("<Enter>", _on_enter)
        rf.bind("<Leave>", _on_leave)
        rf.bind("<Button-1>", _on_click)

        if self._rc_cb is not None:
            ri, rd = i, list(row)
            rf.bind(
                "<Button-3>",
                lambda _e, ri_=ri, rd_=rd: self._rc_cb(ri_, rd_, _e),  # type: ignore
            )

        # ── komórki ────────────────────────────────────────────────────
        x = 0
        cell_labels: List[tk.Label] = []
        if self._show_row_num:
            num_lbl = tk.Label(
                rf, text=str(i + 1), bg=def_bg,
                fg=t["hdr_fg"],
                font=("Segoe UI", scale_font_size(9)),
                anchor="center",
            )
            num_lbl.place(x=x, y=0, width=_ROW_NUM_W, height=_ROW_H)
            num_lbl.bind("<Enter>", _on_enter)
            num_lbl.bind("<Leave>", _on_leave)
            num_lbl.bind("<Button-1>", _on_click)
            if self._rc_cb is not None:
                ri_, rd_ = i, list(row)
                num_lbl.bind(
                    "<Button-3>",
                    lambda _e, ri=ri_, rd=rd_: self._rc_cb(ri, rd, _e),  # type: ignore
                )
            x += _ROW_NUM_W

        for j, (val, w) in enumerate(zip(row, self.col_widths)):
            text   = str(val) if val is not None else ""
            anchor = "center" if j in self._center_cols else "w"
            padx   = 0 if j in self._center_cols else 4

            if j in self._link_cols and text:
                fg = t["link_fg"]
            elif fg_ov:
                fg = fg_ov
            else:
                fg = t["row_fg"]

            lbl = tk.Label(
                rf, text=text, bg=def_bg, fg=fg,
                font=("Segoe UI", scale_font_size(10)),
                anchor=anchor, padx=padx,
            )
            cell_labels.append(lbl)
            lbl.place(x=x, y=0, width=w, height=_ROW_H)
            lbl.bind("<Enter>", _on_enter)
            lbl.bind("<Leave>", _on_leave)
            lbl.bind("<Button-1>", _on_click)

            # Dodatkowy callback kliknięcia w komórkę
            if self._cell_cb is not None:
                ci_, ri_, rd_ = j, i, list(row)
                lbl.bind(
                    "<Button-1>",
                    lambda _e, ci=ci_, ri=ri_, rd=rd_: (
                        _on_click(_e, ri, rd, rf, def_bg),
                        self._cell_cb(ri, ci, rd),  # type: ignore
                    ),
                    add="+",
                )

            if self._rc_cb is not None:
                ri_, rd_ = i, list(row)
                lbl.bind(
                    "<Button-3>",
                    lambda _e, ri=ri_, rd=rd_: self._rc_cb(ri, rd, _e),  # type: ignore
                )

            x += w

            # ── przycisk ✎ po kolumnie id_col ─────────────────────────
            if j == self._id_col:
                ri_, rd_ = i, list(row)
                is_dark = (t is _D)
                icon = _get_edit_photo(dark=is_dark)
                btn = tk.Button(
                    rf,
                    image=icon if icon else "",  # type: ignore
                    text="" if icon else "✎",
                    compound="center",
                    bg=t["edit_bg"], fg=t["edit_fg"],
                    activebackground=t["edit_hover"],
                    activeforeground=t["edit_fg"],
                    font=("Segoe UI", scale_font_size(11)),
                    relief="flat", bd=0, cursor="hand2",
                    command=lambda ri=ri_, rd=rd_: self._edit_cb(ri, rd),
                )
                if icon:
                    btn._icon_ref = icon  # zapobiegaj GC  # type: ignore
                btn.place(x=x + 2, y=2, width=_EDIT_W - 4, height=_ROW_H - 4)
                _Tooltip(btn, "Edytuj")
                btn.bind("<Enter>", _on_enter, add="+")
                btn.bind("<Leave>", _on_leave, add="+")

                if self._rc_cb is not None:
                    btn.bind(
                        "<Button-3>",
                        lambda _e, ri=ri_, rd=rd_: self._rc_cb(ri, rd, _e),  # type: ignore
                    )

                x += _EDIT_W

        # Wypełnienie prawej części wiersza za ostatnią kolumną
        rf._cell_labels = cell_labels  # type: ignore[attr-defined]
        filler = tk.Label(rf, text="", bg=def_bg)
        filler.place(x=x, y=0, relwidth=1, width=-x, height=_ROW_H)
        filler.bind("<Enter>", _on_enter)
        filler.bind("<Leave>", _on_leave)
        filler.bind("<Button-1>", _on_click)
        if self._rc_cb is not None:
            ri_, rd_ = i, list(row)
            filler.bind(
                "<Button-3>",
                lambda _e, ri=ri_, rd=rd_: self._rc_cb(ri, rd, _e),  # type: ignore
            )

    # ── publiczne API ──────────────────────────────────────────────────────
    def set_data(self, data: List[List[Any]]) -> None:
        """Odświeża dane tabeli i przebudowuje wszystkie wiersze."""
        self._data = list(data)
        self._build_rows()
    def toggle_expand(
        self,
        parent_id: Any,
        expand: bool,
        child_rows: Optional[List[List[Any]]] = None,
    ) -> None:
        """Rozwija/zwija wiersze potomne bez pełnego _build_rows.

        Zamiast przebudowywać całą tabelę, wykonuje tylko pack_forget/pack(after=...)
        na ramkach suplementu oraz aktualizuje symbol w wierszu nadrzędnym in-place.
        TOTAL cost: O(k) gdzie k = liczba suplementów; niezależne od rozmiaru tabeli.
        """
        _t0 = _time.perf_counter()
        # Znajdź indeks wiersza nadrzędnego po id_col
        parent_idx: Optional[int] = None
        for idx, row in enumerate(self._data):
            if self._id_col < len(row) and str(row[self._id_col]) == str(parent_id):
                parent_idx = idx
                break
        if parent_idx is None:
            _log.debug("toggle_expand: parent_id=%s not found", parent_id)
            return

        parent_frame = self._row_frames[parent_idx]
        new_symbol   = "[-]" if expand else "[+]"

        # Zaktualizuj symbol nadrzędnego wiersza in-place (1 Label.configure call)
        labels: Optional[List[tk.Label]] = getattr(parent_frame, '_cell_labels', None)
        if labels:
            labels[0].configure(text=new_symbol)
        # Uaktualnij też _cached_row i _data dla spójności
        if parent_idx < len(self._data):
            row_copy = list(self._data[parent_idx])
            if row_copy:  row_copy[0] = new_symbol
            self._data[parent_idx] = row_copy
        if hasattr(parent_frame, '_cached_row') and parent_frame._cached_row:  # type: ignore[attr-defined]
            parent_frame._cached_row[0] = new_symbol  # type: ignore[attr-defined]

        if expand:
            # ── EXPAND: wstaw ramki suplementów po wierszu nadrzędnym ────
            if not child_rows:
                _log.debug("toggle_expand: expand=True but no child_rows")
                return
            insert_after = parent_frame
            new_frames: List[tk.Frame] = []
            new_data_rows: List[List[Any]] = []
            for j, child_row in enumerate(child_rows):
                child_idx = parent_idx + 1 + j
                key = self._pool_key(child_row)
                rf: Optional[tk.Frame] = self._row_pool.pop(key, None) if key is not None else None
                if rf is not None:
                    cached = getattr(rf, '_cached_row', None)
                    if cached != child_row:
                        for ch in rf.winfo_children():
                            ch.destroy()
                        def_bg, _ = self._resolve_colors(child_idx, child_row)
                        rf.configure(bg=def_bg)
                        self._populate_row(rf, child_idx, child_row)
                        rf._cached_row = list(child_row)  # type: ignore[attr-defined]
                else:
                    def_bg, _ = self._resolve_colors(child_idx, child_row)
                    rf = tk.Frame(self._scroll, bg=def_bg, height=_ROW_H)
                    rf.pack_propagate(False)
                    self._populate_row(rf, child_idx, child_row)
                    rf._cached_row = list(child_row)  # type: ignore[attr-defined]
                rf.pack(fill=tk.X, after=insert_after)
                insert_after = rf
                new_frames.append(rf)
                new_data_rows.append(child_row)
            # Wstaw do wewnętrznych list
            ins = parent_idx + 1
            self._row_frames[ins:ins] = new_frames
            self._data[ins:ins] = new_data_rows
        else:
            # ── COLLAPSE: schowaj bezpośrednich potomków ("   →") do puli ────
            end = parent_idx + 1
            while end < len(self._row_frames):
                cd = getattr(self._row_frames[end], '_cached_row', None)
                if cd and len(cd) > 0 and str(cd[0]) == "   \u2192":
                    end += 1
                else:
                    break
            for rf_child in self._row_frames[parent_idx + 1 : end]:
                rf_child.pack_forget()
                key = self._pool_key(getattr(rf_child, '_cached_row', None))
                if key is not None:
                    self._row_pool[key] = rf_child
            del self._row_frames[parent_idx + 1 : end]
            del self._data[parent_idx + 1 : end]

        _t1 = _time.perf_counter()
        _log.debug(
            "toggle_expand: parent_id=%s  expand=%s  children=%d  elapsed=%.1f ms",
            parent_id, expand,
            len(child_rows) if child_rows else (end - parent_idx - 1 if not expand else 0),  # type: ignore[possibly-undefined]
            (_t1 - _t0) * 1000,
        )
    def set_data_patch(self, data: List[List[Any]], id_col: Optional[int] = None) -> None:
        """Szybka aktualizacja: patchuje tylko zmienione/dodane/usunięte wiersze.

        Porównuje nowe dane z bieżącymi po kluczu (id_col lub cały wiersz).
        Idealne do expand/collapse w hierarchicznej tabeli – zmienia się tylko
        kilka wierszy (symbol rozwinięcia + dodane/usunięte suplementy),
        a reszta tabeli nie jest przerysowywana.
        """
        ic = id_col if id_col is not None else self._id_col
        new_data = list(data)

        # Buduj mapę ID → indeks w starych danych (używając wybranej kolumny lub całego wiersza)
        def _key(row: List[Any]) -> Any:
            if ic < len(row):
                return (ic, row[ic])
            return tuple(row)

        old_keys = [_key(r) for r in self._data]
        new_keys = [_key(r) for r in new_data]

        if old_keys == new_keys:
            # Tylko zmiany wartości w istniejących wierszach
            self._data = new_data
            for i, row in enumerate(new_data):
                self._refresh_row(i, row)
            return

        # Liczba wierszy się zmieniła lub kolejność – użyj _build_rows z cache'em
        self._data = new_data
        self._build_rows()

    def get_selected(self) -> Optional[Tuple[int, List[Any]]]:
        """Zwraca (row_idx, row_data) ostatnio klikniętego wiersza lub None."""
        if self._selected_idx is None or self._selected_data is None:
            return None
        return (self._selected_idx, list(self._selected_data))
