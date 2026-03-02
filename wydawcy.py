# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUndefinedVariable=false, reportUnknownParameterType=false
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
import sqlite3
from typing import Optional, Union, List, Dict, Any
import webbrowser
import customtkinter as ctk  # type: ignore
from database_manager import get_db_path
from font_scaling import scale_font_size
from dialog_utils import apply_safe_geometry
from ctk_table import CTkDataTable

DB_FILE = get_db_path("wydawcy.db")

# Przechowuj aktywne filtry na poziomie modułu
active_filters_wydawcy: Dict[str, Any] = {}
# Przechowuj stan sortowania na poziomie modułu
active_sort_wydawcy: Dict[str, Any] = {"column": "ID", "reverse": False}

def apply_dark_theme_to_dialog(dialog: tk.Toplevel) -> None:
    """Stosuje ciemny motyw do okna dialogowego"""
    dark_bg = "#2b2b2b"
    dark_fg = "#ffffff"
    dark_entry_bg = "#404040"
    dark_entry_fg = "#ffffff"
    
    # Główne okno
    dialog.configure(bg=dark_bg)
    
    # Wszystkie widgety w oknie
    for widget in dialog.winfo_children():
        _apply_dark_theme_to_widget(widget, dark_bg, dark_fg, dark_entry_bg, dark_entry_fg)

def _apply_dark_theme_to_widget(widget: Union[tk.Widget, tk.Toplevel], dark_bg: str, dark_fg: str, 
                               dark_entry_bg: str, dark_entry_fg: str) -> None:
    """Rekurencyjnie stosuje ciemny motyw do widgetów"""
    widget_class = widget.winfo_class()
    
    try:
        if widget_class in ('Label', 'Button', 'Checkbutton', 'Radiobutton'):
            widget.configure(bg=dark_bg, fg=dark_fg)  # type: ignore
            if widget_class in ('Checkbutton', 'Radiobutton'):
                widget.configure(selectcolor=dark_entry_bg, activebackground=dark_bg, activeforeground=dark_fg)  # type: ignore
        elif widget_class in ('Entry', 'Text'):
            widget.configure(bg=dark_entry_bg, fg=dark_entry_fg,  # type: ignore
                           insertbackground=dark_entry_fg, selectbackground="#0078d4")  # type: ignore
        elif widget_class == 'Frame':
            widget.configure(bg=dark_bg)  # type: ignore
        elif widget_class == 'Combobox':
            # Dla Combobox używamy ttk style
            pass
        
        # Rekurencyjnie dla dzieci
        for child in widget.winfo_children():
            _apply_dark_theme_to_widget(child, dark_bg, dark_fg, dark_entry_bg, dark_entry_fg)
    except tk.TclError:
        # Ignoruj błędy konfiguracji (niektóre widgety mogą nie obsługiwać pewnych opcji)
        pass


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS wydawcy (
                id INTEGER PRIMARY KEY,
                nazwa TEXT NOT NULL,
                strona TEXT,
                kraj TEXT
            )
        """)
        # Dodaj kolumnę kraj jeśli nie istnieje (migracja)
        c.execute("PRAGMA table_info(wydawcy)")
        columns = [row[1] for row in c.fetchall()]
        if 'kraj' not in columns:
            c.execute("ALTER TABLE wydawcy ADD COLUMN kraj TEXT")
        conn.commit()


def get_all_publishers():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, nazwa, strona, kraj FROM wydawcy ORDER BY id ASC")
        return c.fetchall()


def get_first_free_id():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM wydawcy ORDER BY id ASC")
        used_ids = [row[0] for row in c.fetchall()]
    i = 1
    while i in used_ids:
        i += 1
    return i


def add_publisher_to_db(id_wydawcy: int, nazwa: str, strona: Optional[str], kraj: Optional[str]):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO wydawcy (id, nazwa, strona, kraj) VALUES (?, ?, ?, ?)", (id_wydawcy, nazwa, strona, kraj))
        conn.commit()


def get_dark_mode_from_tab(tab): # type: ignore
    # Szuka atrybutu dark_mode w głównym oknie
    root = tab.winfo_toplevel() # type: ignore
    return getattr(root, 'dark_mode', False) # type: ignore

def dodaj_wydawce(parent: tk.Tk, refresh_callback=None): # type: ignore
    init_db()
    reserved_id = get_first_free_id()

    dialog = ctk.CTkToplevel(parent)
    dialog.title("Dodaj wydawcę do bazy")
    dialog.transient(parent)
    dialog.resizable(True, True)

    apply_safe_geometry(dialog, parent, 400, 280)

    # Główna ramka
    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # ID wydawcy (tylko do odczytu)
    ctk.CTkLabel(main_frame, text=f"ID wydawcy: {reserved_id}", font=("Segoe UI", scale_font_size(12))).grid(
        row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

    # Nazwa wydawcy
    ctk.CTkLabel(main_frame, text="Nazwa wydawcy *").grid(row=1, column=0, pady=5, sticky="w")
    nazwa_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="Wprowadź nazwę wydawcy")
    nazwa_entry.grid(row=1, column=1, pady=5, padx=(10, 0), sticky="ew")
    dialog.after(100, lambda: nazwa_entry.focus_set() if nazwa_entry.winfo_exists() else None)

    # Strona internetowa
    ctk.CTkLabel(main_frame, text="Strona internetowa").grid(row=2, column=0, pady=5, sticky="w")
    strona_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="https://...")
    strona_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky="ew")

    # Kraj wydawcy
    ctk.CTkLabel(main_frame, text="Kraj wydawcy").grid(row=3, column=0, pady=5, sticky="w")
    kraj_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="Wprowadź kraj")
    kraj_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky="ew")

    main_frame.columnconfigure(1, weight=1)

    def on_ok():
        nazwa = nazwa_entry.get().strip()
        strona = strona_entry.get().strip()
        kraj = kraj_entry.get().strip()
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa wydawcy jest wymagana.", parent=dialog) # type: ignore
            return
        add_publisher_to_db(reserved_id, nazwa, strona if strona else None, kraj if kraj else None)
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    # Ramka na przyciski
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))

    btn_ok = ctk.CTkButton(btn_frame, text="Dodaj", command=on_ok, width=100,
                           fg_color="#2E7D32", hover_color="#1B5E20")
    btn_ok.pack(side=tk.LEFT, padx=10)
    btn_cancel = ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100,
                               fg_color="#666666", hover_color="#555555")
    btn_cancel.pack(side=tk.LEFT, padx=10)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)


def fill_wydawcy_tab(tab: tk.Frame, dark_mode: bool = False) -> None:  # type: ignore
    """Główny widok wydawców — tabela CTkDataTable."""
    for widget in tab.winfo_children():
        widget.destroy()
    init_db()

    records = get_all_publishers()
    data: List[List[Any]] = [[v if v is not None else "" for v in rec] for rec in records]

    # ── Kolory górnego paska ─────────────────────────────────────────────────
    bg_top = "#1e1e2e" if dark_mode else "#f5f5f5"
    fg_top = "#e0e0e0" if dark_mode else "#212121"
    FONT   = ("Segoe UI", scale_font_size(10))

    _HEADERS  = ["ID", "Nazwa", "Strona", "Kraj"]
    _SORTABLE = {"ID": 0, "Nazwa": 1, "Strona": 2, "Kraj": 3}

    # ── Obliczanie szerokości kolumn z zawartości ────────────────────────────
    _mf      = tkfont.Font(family="Segoe UI", size=scale_font_size(10))
    _mf_bold = tkfont.Font(family="Segoe UI", size=scale_font_size(10), weight="bold")

    def _compute_widths(rows: List[List[Any]]) -> List[int]:
        pad = 24
        w_nazwa = max([_mf_bold.measure("Nazwa")] +
                      [_mf.measure(str(r[1])) for r in rows]) + pad
        w_str   = max([_mf_bold.measure("Strona")] +
                      ([_mf.measure(str(r[2])) for r in rows if r[2]] or [0])) + pad
        w_kraj  = max([_mf_bold.measure("Kraj")] +
                      ([_mf.measure(str(r[3])) for r in rows if r[3]] or [0])) + pad
        return [
            44,
            min(max(w_nazwa, 100), 280),
            min(max(w_str,   120), 500),
            min(max(w_kraj,   60), 120),
        ]

    # ── Stan ─────────────────────────────────────────────────────────────────
    displayed_data: List[List[Any]] = []
    _table: List[Optional[CTkDataTable]] = [None]

    # ── Filtry + sortowanie ──────────────────────────────────────────────────
    def _apply_and_draw() -> None:
        nonlocal displayed_data
        filtered: List[List[Any]] = list(data)
        if active_filters_wydawcy.get('kraj', 'Wszystkie') != 'Wszystkie':
            filtered = [r for r in filtered if r[3] == active_filters_wydawcy['kraj']]
        strona_f = active_filters_wydawcy.get('strona', 'Wszystkie')
        if strona_f == 'Wpisane':
            filtered = [r for r in filtered if r[2]]
        elif strona_f == 'Puste':
            filtered = [r for r in filtered if not r[2]]
        col_i = _SORTABLE.get(active_sort_wydawcy.get("column", "ID"), 0)
        rev   = active_sort_wydawcy.get("reverse", False)
        if col_i == 0:
            filtered.sort(key=lambda x: int(x[0]) if x[0] != "" else 0, reverse=rev)
        else:
            filtered.sort(key=lambda x: (str(x[col_i]) or '').lower(), reverse=rev)
        displayed_data = filtered
        if _table[0] is not None:
            _table[0].set_data(displayed_data)
        _refresh_filter_btn()

    def _refresh_filter_btn() -> None:
        active = sum(1 for v in active_filters_wydawcy.values() if v != 'Wszystkie')
        filter_btn.configure(text=f"Filtruj ({active})" if active else "Filtruj")

    # ── Górny pasek (sortowanie + filtrowanie) ───────────────────────────────
    top_bar = tk.Frame(tab, bg=bg_top)
    top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
    tk.Label(top_bar, text="Sortuj:", bg=bg_top, fg=fg_top,
             font=FONT).pack(side=tk.LEFT, padx=(0, 4))
    sort_var = tk.StringVar(value=active_sort_wydawcy.get("column", "ID"))
    ttk.Combobox(top_bar, textvariable=sort_var,
                 values=["ID", "Nazwa", "Strona", "Kraj"],
                 state="readonly", width=10).pack(side=tk.LEFT)

    def _sort_asc() -> None:
        active_sort_wydawcy["column"]  = sort_var.get()
        active_sort_wydawcy["reverse"] = False
        _apply_and_draw()

    def _sort_desc() -> None:
        active_sort_wydawcy["column"]  = sort_var.get()
        active_sort_wydawcy["reverse"] = True
        _apply_and_draw()

    ttk.Button(top_bar, text="Rosnąco",  command=_sort_asc ).pack(side=tk.LEFT, padx=4)
    ttk.Button(top_bar, text="Malejąco", command=_sort_desc).pack(side=tk.LEFT, padx=4)
    ttk.Separator(top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
    tk.Label(top_bar, text="Filtruj:", bg=bg_top, fg=fg_top,
             font=FONT).pack(side=tk.LEFT, padx=(0, 4))
    filter_btn = ttk.Button(top_bar, text="Filtruj", command=lambda: _open_filter())
    filter_btn.pack(side=tk.LEFT, padx=4)

    # ── Callbacki tabeli ────────────────────────────────────────────────────
    def _on_edit(_row_idx: int, row_data: List[Any]) -> None:
        open_edit_dialog(tab, row_data,
                         refresh_callback=lambda **kw: fill_wydawcy_tab(  # type: ignore[misc]
                             tab, dark_mode=get_dark_mode_from_tab(tab)))

    def _on_sort(col_idx: int) -> None:
        col_name = _HEADERS[col_idx]
        if active_sort_wydawcy.get("column") == col_name:
            active_sort_wydawcy["reverse"] = not active_sort_wydawcy.get("reverse", False)
        else:
            active_sort_wydawcy["column"]  = col_name
            active_sort_wydawcy["reverse"] = False
        sort_var.set(col_name)
        _apply_and_draw()

    def _on_cell_click(_row_idx: int, col_idx: int, row_data: List[Any]) -> None:
        if col_idx == 2 and row_data[2]:
            webbrowser.open(str(row_data[2]))

    def _on_right_click(_row_idx: int, row_data: List[Any], event: Any) -> None:
        def _edit() -> None:
            open_edit_dialog(tab, row_data,
                             refresh_callback=lambda **kw: fill_wydawcy_tab(  # type: ignore[misc]
                                 tab, dark_mode=get_dark_mode_from_tab(tab)))
        def _del() -> None:
            if messagebox.askyesno(
                    "Usuń wydawcę",
                    f"Czy na pewno chcesz usunąć wydawcę: {row_data[1]}?",
                    parent=tab):
                with sqlite3.connect(DB_FILE) as conn:
                    conn.cursor().execute(
                        "DELETE FROM wydawcy WHERE id=?", (row_data[0],))
                    conn.commit()
                fill_wydawcy_tab(tab, dark_mode=get_dark_mode_from_tab(tab))
        ctx = tk.Menu(tab, tearoff=0)
        ctx.add_command(label="Edytuj", command=_edit)
        ctx.add_separator()
        ctx.add_command(label="Usuń",   command=_del)
        ctx.tk_popup(event.x_root, event.y_root)
        ctx.grab_release()

    # ── Tabela ───────────────────────────────────────────────────────────────
    tbl = CTkDataTable(
        tab,
        headers=_HEADERS,
        col_widths=_compute_widths(data),
        data=[],
        edit_callback=_on_edit,
        id_col=0,
        link_cols=[2],
        center_cols=[0],
        dark_mode=dark_mode,
        sort_callback=_on_sort,
        cell_click_callback=_on_cell_click,
        right_click_callback=_on_right_click,
    )
    tbl.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    tab.rowconfigure(1, weight=1)
    tab.columnconfigure(0, weight=1)
    _table[0] = tbl

    # ── Dialog filtrowania ───────────────────────────────────────────────────
    def _open_filter() -> None:
        dlg = ctk.CTkToplevel(tab)
        dlg.title("Filtruj wydawców")
        dlg.transient(tab.winfo_toplevel())
        apply_safe_geometry(dlg, tab.winfo_toplevel(), 380, 220)

        mf = ctk.CTkFrame(dlg)
        mf.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(mf, text="Kraj:").grid(row=0, column=0, sticky="w", pady=8)
        kraje: set[str] = set(r[3] for r in data if r[3])
        kraj_var_ = tk.StringVar(value=active_filters_wydawcy.get('kraj', 'Wszystkie'))
        ttk.Combobox(
            mf, textvariable=kraj_var_,
            values=['Wszystkie'] + sorted(kraje),
            width=22, state="readonly"
        ).grid(row=0, column=1, sticky="ew", pady=8, padx=(10, 0))

        ctk.CTkLabel(mf, text="Strona:").grid(row=1, column=0, sticky="w", pady=8)
        strona_var_ = tk.StringVar(value=active_filters_wydawcy.get('strona', 'Wszystkie'))
        ttk.Combobox(
            mf, textvariable=strona_var_,
            values=['Wszystkie', 'Wpisane', 'Puste'],
            width=22, state="readonly"
        ).grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))

        mf.columnconfigure(1, weight=1)

        bf = ctk.CTkFrame(mf, fg_color="transparent")
        bf.grid(row=2, column=0, columnspan=2, pady=(20, 0))

        def _apply() -> None:
            active_filters_wydawcy['kraj']   = kraj_var_.get()
            active_filters_wydawcy['strona'] = strona_var_.get()
            _apply_and_draw()
            dlg.destroy()

        def _reset() -> None:
            active_filters_wydawcy.clear()
            _apply_and_draw()
            dlg.destroy()

        ctk.CTkButton(bf, text="Zastosuj", command=_apply,
                      fg_color="#2E7D32", hover_color="#1B5E20",
                      width=90).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(bf, text="Resetuj",  command=_reset,
                      fg_color="#1976D2", hover_color="#1565C0",
                      width=90).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(bf, text="Anuluj",   command=dlg.destroy,
                      fg_color="#666666", hover_color="#555555",
                      width=90).pack(side=tk.LEFT, padx=5)

        dlg.after(300, lambda: dlg.winfo_exists() and (
            dlg.deiconify(), dlg.lift(), dlg.focus_force()))

    # ── Pierwsze wypełnienie ─────────────────────────────────────────────────
    _apply_and_draw()


def open_edit_dialog(parent: Any, values: List[Any], refresh_callback: Any = None) -> None:
    """Otwiera okno edycji wydawcy. values = [id, nazwa, strona, kraj]"""
    record_id = values[0]
    current_nazwa  = str(values[1]) if values[1] else ""
    current_strona = str(values[2]) if values[2] else ""
    current_kraj   = str(values[3]) if values[3] else ""

    dialog = ctk.CTkToplevel(parent)
    dialog.title("Edytuj wydawcę")
    dialog.transient(parent)
    dialog.resizable(True, True)
    apply_safe_geometry(dialog, parent, 400, 280)

    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    ctk.CTkLabel(main_frame, text=f"ID wydawcy: {record_id}",
                 font=("Segoe UI", scale_font_size(12))).grid(
        row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

    ctk.CTkLabel(main_frame, text="Nazwa wydawcy *").grid(row=1, column=0, pady=5, sticky="w")
    nazwa_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="Wprowadź nazwę wydawcy")
    nazwa_entry.insert(0, current_nazwa)
    nazwa_entry.grid(row=1, column=1, pady=5, padx=(10, 0), sticky="ew")
    dialog.after(100, lambda: nazwa_entry.focus_set() if nazwa_entry.winfo_exists() else None)

    ctk.CTkLabel(main_frame, text="Strona internetowa").grid(row=2, column=0, pady=5, sticky="w")
    strona_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="https://...")
    strona_entry.insert(0, current_strona)
    strona_entry.grid(row=2, column=1, pady=5, padx=(10, 0), sticky="ew")

    ctk.CTkLabel(main_frame, text="Kraj wydawcy").grid(row=3, column=0, pady=5, sticky="w")
    kraj_entry = ctk.CTkEntry(main_frame, width=220, placeholder_text="Wprowadź kraj")
    kraj_entry.insert(0, current_kraj)
    kraj_entry.grid(row=3, column=1, pady=5, padx=(10, 0), sticky="ew")

    main_frame.columnconfigure(1, weight=1)

    def on_ok() -> None:
        nazwa  = nazwa_entry.get().strip()
        strona = strona_entry.get().strip()
        kraj   = kraj_entry.get().strip()
        if not nazwa:
            messagebox.showerror("Błąd", "Nazwa wydawcy jest wymagana.", parent=dialog)
            return
        with sqlite3.connect(DB_FILE) as conn:
            conn.cursor().execute(
                "UPDATE wydawcy SET nazwa=?, strona=?, kraj=? WHERE id=?",
                (nazwa, strona if strona else None, kraj if kraj else None, record_id)
            )
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(parent))
        dialog.destroy()

    def on_cancel() -> None:
        dialog.destroy()

    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
    ctk.CTkButton(btn_frame, text="Zapisz", command=on_ok, width=100,
                  fg_color="#1976D2", hover_color="#1565C0").pack(side=tk.LEFT, padx=10)
    ctk.CTkButton(btn_frame, text="Anuluj", command=on_cancel, width=100,
                  fg_color="#666666", hover_color="#555555").pack(side=tk.LEFT, padx=10)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)


def usun_wydawce_dialog(parent: Any, refresh_callback: Any = None) -> None:  # type: ignore
    """Dialog z listą wydawców do wyboru i usunięcia."""
    init_db()
    records = get_all_publishers()
    if not records:
        messagebox.showinfo("Brak danych", "Brak wydawców do usunięcia.", parent=parent)
        return

    dialog = ctk.CTkToplevel(parent)
    dialog.title("Usuń wydawcę")
    dialog.transient(parent)
    dialog.resizable(True, True)
    apply_safe_geometry(dialog, parent, 400, 300)

    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    ctk.CTkLabel(main_frame, text="Wybierz wydawcę do usunięcia:",
                 font=("Segoe UI", scale_font_size(12))).pack(pady=(0, 10))

    list_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    listbox = tk.Listbox(list_frame, width=44, height=8,
                         font=("Segoe UI", scale_font_size(10)))
    for rec in records:
        listbox.insert(tk.END, f"{rec[0]}. {rec[1]}")
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)
    listbox.selection_set(0)

    def on_delete() -> None:
        sel = listbox.curselection()  # type: ignore[assignment]
        if not sel:
            return
        rec = records[sel[0]]
        if messagebox.askyesno("Potwierdź usunięcie",
                               f"Czy na pewno chcesz usunąć wydawcę: {rec[1]}?",
                               parent=dialog):
            with sqlite3.connect(DB_FILE) as conn:
                conn.cursor().execute("DELETE FROM wydawcy WHERE id=?", (rec[0],))
                conn.commit()
            if refresh_callback:
                refresh_callback()
            dialog.destroy()

    def on_cancel_del() -> None:
        dialog.destroy()

    btn_frame_del = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame_del.pack(pady=(10, 0))
    ctk.CTkButton(btn_frame_del, text="Usuń", command=on_delete, width=100,
                  fg_color="#C62828", hover_color="#B71C1C").pack(side=tk.LEFT, padx=10)
    ctk.CTkButton(btn_frame_del, text="Anuluj", command=on_cancel_del, width=100,
                  fg_color="#666666", hover_color="#555555").pack(side=tk.LEFT, padx=10)

    dialog.protocol("WM_DELETE_WINDOW", on_cancel_del)


def usun_zaznaczonego_wydawce(tab: tk.Frame, refresh_callback: Any = None) -> None:  # type: ignore
    """Usuwa zaznaczonego wydawcę z tabeli CTkDataTable (przycisk w ribbonie)."""
    table: Any = None
    for widget in tab.winfo_children():
        if isinstance(widget, CTkDataTable):
            table = widget
            break
    if table is None:
        messagebox.showerror("Błąd", "Nie znaleziono tabeli wydawców.", parent=tab)
        return
    sel = table.get_selected()
    if sel is None:
        messagebox.showinfo("Brak wyboru", "Zaznacz wydawcę do usunięcia w tabeli.", parent=tab)
        return
    _, values = sel
    if messagebox.askyesno("Usuń wydawcę",
                           f"Czy na pewno chcesz usunąć wydawcę: {values[1]}?",
                           parent=tab):
        with sqlite3.connect(DB_FILE) as conn:
            conn.cursor().execute("DELETE FROM wydawcy WHERE id=?", (values[0],))
            conn.commit()
        if refresh_callback:
            refresh_callback(dark_mode=get_dark_mode_from_tab(tab))


# Alias dla kompatybilności z main.py
usun_zaznaczony_wydawce = usun_zaznaczonego_wydawce  # type: ignore
