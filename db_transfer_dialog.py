# type: ignore
"""
Dialog zarządzania bazami danych — eksport, import, tryb gościa.

Eksport: zapisuje własne 4 bazy do pliku ZIP lub folderu.
Import własnych danych: zastępuje własne bazy (z backupem) danymi z ZIP/folderu.
Tryb gościa: otwiera bazy innego użytkownika do przeglądania (tylko odczyt).
"""
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk
import logging

from database_manager import export_databases, export_databases_excel, prepare_import_source, replace_own_databases
from font_scaling import scale_font_size
from dialog_utils import apply_safe_geometry, create_ctk_toplevel

_log = logging.getLogger(__name__)


def show_db_transfer_dialog(
    parent: Any,
    on_enter_guest: Callable[[Path, str], None],
) -> None:
    """
    Otwiera dialog zarządzania bazami danych.

    Args:
        parent: Okno nadrzędne.
        on_enter_guest: callback(source_dir, label) — wywoływany po wybraniu baz gościa.
    """
    dlg = create_ctk_toplevel(parent)
    dlg.title("Zarządzanie bazami danych")
    dlg.transient(parent)
    dlg.resizable(True, True)
    apply_safe_geometry(dlg, parent, 540, 520)

    font_h = ctk.CTkFont(family='Segoe UI', size=scale_font_size(13), weight='bold')
    font_n = ctk.CTkFont(family='Segoe UI', size=scale_font_size(11))
    font_s = ctk.CTkFont(family='Segoe UI', size=scale_font_size(10))

    outer = ctk.CTkScrollableFrame(dlg)
    outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    # ── Sekcja EKSPORT ────────────────────────────────────────────────────────

    exp_frame = ctk.CTkFrame(outer)
    exp_frame.pack(fill=tk.X, pady=(0, 10))

    ctk.CTkLabel(exp_frame, text="📤  Eksport danych", font=font_h).pack(
        anchor="w", padx=12, pady=(10, 2)
    )
    ctk.CTkLabel(
        exp_frame,
        text=(
            "Zapisz swoje bazy danych do pliku ZIP, folderu lub arkusza Excel.\n"
            "Możesz otworzyć je na innym urządzeniu lub udostępnić komuś do wglądu."
        ),
        font=font_s,
        justify="left",
        wraplength=480,
    ).pack(anchor="w", padx=12, pady=(0, 8))

    exp_fmt_var = tk.StringVar(value="zip")
    fmt_row = ctk.CTkFrame(exp_frame, fg_color="transparent")
    fmt_row.pack(fill=tk.X, padx=12, pady=(0, 8))
    ctk.CTkLabel(fmt_row, text="Format:", font=font_n).pack(side=tk.LEFT, padx=(0, 8))
    ctk.CTkRadioButton(
        fmt_row, text="ZIP (jeden plik)", variable=exp_fmt_var, value="zip", font=font_n
    ).pack(side=tk.LEFT, padx=(0, 12))
    ctk.CTkRadioButton(
        fmt_row, text="Folder (osobne pliki .db)", variable=exp_fmt_var, value="folder", font=font_n
    ).pack(side=tk.LEFT, padx=(0, 12))
    ctk.CTkRadioButton(
        fmt_row, text="Excel (.xlsx)", variable=exp_fmt_var, value="excel", font=font_n
    ).pack(side=tk.LEFT)

    def _do_export() -> None:
        fmt = exp_fmt_var.get()
        if fmt == "excel":
            dlg.update()  # upewnij się, że CTkToplevel jest wyrenderowany przed natywnym dialogiem
            dest_str = filedialog.asksaveasfilename(
                parent=parent,
                title="Zapisz eksport jako arkusz Excel...",
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx"), ("Wszystkie pliki", "*.*")],
                initialfile="Sesyjka_bazy.xlsx",
            )
            if not dest_str:
                return
            try:
                result = export_databases_excel(Path(dest_str))
                messagebox.showinfo(
                    "Eksport zakończony",
                    f"Bazy danych zostały wyeksportowane do:\n{result}\n\n"
                    "Każda tabela to osobny arkusz w pliku Excel.",
                    parent=dlg,
                )
            except ImportError as exc:
                messagebox.showerror("Brak biblioteki", str(exc), parent=dlg)
            except Exception as exc:
                _log.error("Błąd eksportu Excel", exc_info=True)
                messagebox.showerror("Błąd eksportu", str(exc), parent=dlg)
            return
        if fmt == "zip":
            dlg.update()  # upewnij się, że CTkToplevel jest wyrenderowany przed natywnym dialogiem
            dest_str = filedialog.asksaveasfilename(
                parent=parent,
                title="Zapisz eksport jako...",
                defaultextension=".zip",
                filetypes=[("ZIP", "*.zip"), ("Wszystkie pliki", "*.*")],
                initialfile="Sesyjka_bazy.zip",
            )
            if not dest_str:
                return
            dest = Path(dest_str)
        else:
            dlg.update()  # upewnij się, że CTkToplevel jest wyrenderowany przed natywnym dialogiem
            dest_str = filedialog.askdirectory(parent=parent, title="Wybierz folder docelowy")
            if not dest_str:
                return
            dest = Path(dest_str)

        try:
            result = export_databases(dest, fmt)
            messagebox.showinfo(
                "Eksport zakończony",
                f"Bazy danych zostały wyeksportowane do:\n{result}",
                parent=dlg,
            )
        except Exception as exc:
            _log.error("Błąd eksportu baz danych", exc_info=True)
            messagebox.showerror("Błąd eksportu", str(exc), parent=dlg)

    ctk.CTkButton(
        exp_frame,
        text="📤  Eksportuj bazy danych",
        command=_do_export,
        font=font_n,
        fg_color="#1565C0",
        hover_color="#0D47A1",
        width=210,
        height=32,
    ).pack(padx=12, pady=(0, 12), anchor="w")

    # ── Sekcja IMPORT własnych danych ─────────────────────────────────────────

    imp_frame = ctk.CTkFrame(outer)
    imp_frame.pack(fill=tk.X, pady=(0, 10))

    ctk.CTkLabel(imp_frame, text="📥  Import — zastąp swoje dane", font=font_h).pack(
        anchor="w", padx=12, pady=(10, 2)
    )
    ctk.CTkLabel(
        imp_frame,
        text=(
            "Wczytaj bazy ze swojego eksportu (np. z innego urządzenia lub kopii zapasowej).\n"
            "Przed zastąpieniem automatycznie zostanie wykonany backup bieżących baz."
        ),
        font=font_s,
        justify="left",
        wraplength=480,
    ).pack(anchor="w", padx=12, pady=(0, 8))

    imp_btn_row = ctk.CTkFrame(imp_frame, fg_color="transparent")
    imp_btn_row.pack(fill=tk.X, padx=12, pady=(0, 12))

    def _pick_source(parent_dlg: Any) -> Optional[Path]:
        """Pokazuje dialog wyboru pliku ZIP lub folderu."""
        dlg.update()  # upewnij się, że CTkToplevel jest wyrenderowany przed natywnym dialogiem
        source_str = filedialog.askopenfilename(
            parent=parent_dlg,
            title="Wybierz plik ZIP z bazami danych",
            filetypes=[("ZIP", "*.zip"), ("Wszystkie pliki", "*.*")],
        )
        if source_str:
            return Path(source_str)
        # Fallback — wybór folderu
        dlg.update()
        source_str = filedialog.askdirectory(
            parent=parent_dlg, title="...lub wybierz folder z plikami .db"
        )
        return Path(source_str) if source_str else None

    def _do_import_own() -> None:
        source = _pick_source(parent)
        if source is None:
            return

        try:
            source_dir, found = prepare_import_source(source)
        except ValueError as exc:
            messagebox.showerror("Błąd", str(exc), parent=dlg)
            return

        answer = messagebox.askyesno(
            "Potwierdzenie importu",
            (
                f"Znaleziono {len(found)} plik(ów) baz danych:\n"
                f"  {', '.join(found)}\n\n"
                "Backup Twoich obecnych baz zostanie wykonany automatycznie.\n"
                "Czy zastąpić Twoje dane importowanymi?"
            ),
            parent=dlg,
        )
        if not answer:
            return

        try:
            replace_own_databases(source_dir, found)
            messagebox.showinfo(
                "Import zakończony",
                (
                    "Dane zostały zastąpione.\n\n"
                    "Uruchom ponownie aplikację, aby odświeżyć wszystkie widoki."
                ),
                parent=dlg,
            )
        except Exception as exc:
            _log.error("Błąd zastępowania własnych baz danych", exc_info=True)
            messagebox.showerror("Błąd importu", str(exc), parent=dlg)

    ctk.CTkButton(
        imp_btn_row,
        text="📥  Wybierz ZIP lub folder...",
        command=_do_import_own,
        font=font_n,
        fg_color="#4A148C",
        hover_color="#38006b",
        width=210,
        height=32,
    ).pack(side=tk.LEFT)

    # ── Sekcja TRYB GOŚCIA ────────────────────────────────────────────────────

    guest_frame = ctk.CTkFrame(outer)
    guest_frame.pack(fill=tk.X, pady=(0, 10))

    ctk.CTkLabel(guest_frame, text="👁️  Otwórz bazy gościa (tylko podgląd)", font=font_h).pack(
        anchor="w", padx=12, pady=(10, 2)
    )
    ctk.CTkLabel(
        guest_frame,
        text=(
            "Przeglądaj zbiory i statystyki innego użytkownika bez dotykania swoich danych.\n"
            "Wszystkie operacje dodawania i usuwania będą zablokowane.\n"
            "Powrót do swoich danych jednym przyciskiem."
        ),
        font=font_s,
        justify="left",
        wraplength=480,
    ).pack(anchor="w", padx=12, pady=(0, 8))

    def _do_open_guest() -> None:
        source = _pick_source(parent)
        if source is None:
            return

        label = source.stem  # nazwa pliku/folderu jako etykieta

        try:
            source_dir, found = prepare_import_source(source)
        except ValueError as exc:
            messagebox.showerror("Błąd", str(exc), parent=dlg)
            return

        dlg.destroy()
        on_enter_guest(source_dir, label)

    ctk.CTkButton(
        guest_frame,
        text="👁️  Otwórz bazy gościa...",
        command=_do_open_guest,
        font=font_n,
        fg_color="#E65100",
        hover_color="#BF360C",
        width=210,
        height=32,
    ).pack(padx=12, pady=(0, 12), anchor="w")

    # ── Dolne przyciski ───────────────────────────────────────────────────────

    ctk.CTkButton(
        dlg,
        text="Zamknij",
        command=dlg.destroy,
        font=font_n,
        fg_color="#555555",
        hover_color="#444444",
        width=100,
        height=32,
    ).pack(pady=(4, 12))
