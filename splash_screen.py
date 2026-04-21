"""
Splash screen aplikacji Sesyjka — wyświetlany podczas ładowania.
Klimat TTRPG: ciemne tło, runy, nazwa aplikacji, wersja i autor.
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable
from font_scaling import scale_font_size

# Paleta kolorów — mroczny klimat TTRPG
_BG        = "#1a1410"   # ciemna pergaminowa czerń
_ACCENT    = "#c8943a"   # złoto / brąz (inkaust)
_ACCENT2   = "#8b2020"   # rubinowa czerwień
_FG_MAIN   = "#f0e6d0"   # kremowa biel (pergamin)
_FG_SUB    = "#a09070"   # przyciemniony pergamin
_FG_VER    = "#c8943a"   # wersja złotem
_BORDER    = "#c8943a"

# Dekoracyjny napis runiczny (szeroki separator)
_RUNE_LINE = "⚔  ✦  ✦  ✦  ✦  ✦  ✦  ✦  ✦  ✦  ⚔"

# ASCII art / runy tytułowe (opcjonalnie widoczne)
_TAGLINE   = "TTRPG Base Manager"


class SplashScreen:
    """Splash screen wyświetlany na starcie aplikacji.

    Musi być tworzony PO istniejącym głównym oknie (jako Toplevel, nie Tk),
    aby uniknąć konfliktu dwóch jednoczesnych instancji tk.Tk.

    Użycie::

        app = SesyjkaApp()       # główne okno (ukryte)
        app.withdraw()
        splash = SplashScreen(version="0.3.34", parent=app)
        splash.show()
        app.after(2000, splash.close)
    """

    def __init__(
        self,
        version: str = "",
        parent: Optional[tk.Misc] = None,
        on_ready: Optional[Callable[[], None]] = None,
    ) -> None:
        self.version = version
        self.parent = parent
        self.on_ready = on_ready
        self._win: Optional[tk.Toplevel] = None
        self._closed = False

    # ── Publiczne API ─────────────────────────────────────────────────────

    def show(self) -> None:
        """Wyświetla splash screen."""
        self._build()

    def close(self) -> None:
        """Zamyka splash screen i pokazuje główne okno (jeśli było ukryte)."""
        self._closed = True
        if self._win is not None:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None
        # Przywóć główne okno jeśli było ukryte
        if self.parent is not None:
            try:
                self.parent.deiconify()  # type: ignore[attr-defined]
            except Exception:
                pass

    def close_after(self, ms: int) -> None:
        """Planuje automatyczne zamknięcie po `ms` milisekundach."""
        if self._win is not None:
            self._win.after(ms, self.close)

    def update(self) -> None:
        """Odświeża splash screen (wywołuj w trakcie ładowania)."""
        if self._win is not None and not self._closed:
            try:
                self._win.update()
            except Exception:
                pass

    # ── Budowanie UI ──────────────────────────────────────────────────────

    def _build(self) -> None:
        # Zawsze Toplevel na głównym oknie — nigdy drugi tk.Tk()
        win = tk.Toplevel(self.parent)
        self._win = win

        win.overrideredirect(True)          # bez ramki systemowej
        win.configure(bg=_BG)
        win.attributes("-topmost", True)    # zawsze na wierzchu

        w, h = 560, 380

        # Wyśrodkuj na ekranie
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")

        # Outer border frame (złote obramowanie)
        outer = tk.Frame(win, bg=_BORDER, padx=3, pady=3)
        outer.pack(fill=tk.BOTH, expand=True)

        inner = tk.Frame(outer, bg=_BG)
        inner.pack(fill=tk.BOTH, expand=True)

        # ── Górna dekoracja ───────────────────────────────────────────────
        tk.Label(
            inner,
            text=_RUNE_LINE,
            font=("Segoe UI", scale_font_size(10)),
            fg=_ACCENT,
            bg=_BG,
        ).pack(pady=(18, 2))

        # ── Główna nazwa ──────────────────────────────────────────────────
        tk.Label(
            inner,
            text="Sesyjka",
            font=("Segoe UI", scale_font_size(52), "bold"),
            fg=_FG_MAIN,
            bg=_BG,
        ).pack(pady=(6, 0))

        # Tagline pod nazwą
        tk.Label(
            inner,
            text=_TAGLINE,
            font=("Segoe UI", scale_font_size(12), "italic"),
            fg=_FG_SUB,
            bg=_BG,
        ).pack(pady=(0, 4))

        # ── Środkowa dekoracja ────────────────────────────────────────────
        tk.Label(
            inner,
            text="─────────────────────────────────",
            font=("Segoe UI", scale_font_size(10)),
            fg=_ACCENT2,
            bg=_BG,
        ).pack(pady=(2, 8))

        # ── Wersja ────────────────────────────────────────────────────────
        if self.version:
            tk.Label(
                inner,
                text=f"v{self.version}",
                font=("Segoe UI", scale_font_size(16), "bold"),
                fg=_FG_VER,
                bg=_BG,
            ).pack(pady=(0, 4))

        # ── Autor ─────────────────────────────────────────────────────────
        tk.Label(
            inner,
            text='Marcin "Zuraff" Żurawicz',
            font=("Segoe UI", scale_font_size(11)),
            fg=_FG_SUB,
            bg=_BG,
        ).pack(pady=(0, 8))

        # ── Dolna dekoracja ───────────────────────────────────────────────
        tk.Label(
            inner,
            text=_RUNE_LINE,
            font=("Segoe UI", scale_font_size(10)),
            fg=_ACCENT,
            bg=_BG,
        ).pack(side=tk.BOTTOM, pady=(0, 18))

        # ── Pasek ładowania ───────────────────────────────────────────────
        self._loading_label = tk.Label(
            inner,
            text="Ładowanie...",
            font=("Segoe UI", scale_font_size(9)),
            fg=_FG_SUB,
            bg=_BG,
        )
        self._loading_label.pack(side=tk.BOTTOM, pady=(0, 6))

        win.update()

    def set_status(self, text: str) -> None:
        """Aktualizuje tekst statusu ładowania."""
        if hasattr(self, '_loading_label') and self._loading_label.winfo_exists():
            try:
                self._loading_label.configure(text=text)
                self.update()
            except Exception:
                pass
