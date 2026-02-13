# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import tkinter as tk
from tkinter import ttk # type: ignore
import sqlite3
from collections import defaultdict
import matplotlib
matplotlib.use('TkAgg')  # Backend dla tkinter
import matplotlib.pyplot as plt  # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # type: ignore
from matplotlib.figure import Figure  # type: ignore

def fill_statystyki_tab(tab, dark_mode=False): # type: ignore
    """
    Wypełnia zakładkę Statystyki.
    
    Args:
        tab: Zakładka do wypełnienia
        dark_mode: Czy używać trybu ciemnego
    """
    # Wyczyść zakładkę
    for widget in tab.winfo_children(): # type: ignore
        widget.destroy() # type: ignore
    
    # Kolory w zależności od trybu
    if dark_mode:
        bg_color = '#23272e'
        fg_color = '#f3f6fa'
        frame_bg = '#31343a'
    else:
        bg_color = '#f3f6fa'
        fg_color = '#23272e'
        frame_bg = '#ffffff'
    
    # Główny frame
    main_frame = tk.Frame(tab, bg=bg_color) # type: ignore
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Tytuł i przycisk odświeżania
    header_frame = tk.Frame(main_frame, bg=bg_color) # type: ignore
    header_frame.pack(pady=(20, 20))
    
    title_label = tk.Label(
        header_frame,
        text="Statystyki i Raporty",
        font=('Segoe UI', 24, 'bold'),
        bg=bg_color,
        fg=fg_color
    )
    title_label.pack(side=tk.LEFT, padx=(0, 20))
    
    # Przycisk odświeżania
    refresh_button = tk.Button(
        header_frame,
        text="🔄 Odśwież statystyki",
        font=('Segoe UI', 11, 'bold'),
        bg='#2E7D32' if not dark_mode else '#1B5E20',
        fg='white',
        activebackground='#1B5E20' if not dark_mode else '#2E7D32',
        activeforeground='white',
        relief='raised',
        cursor='hand2',
        padx=15,
        pady=8,
        command=lambda: fill_statystyki_tab(tab, dark_mode)  # type: ignore
    )
    refresh_button.pack(side=tk.LEFT)
    
    # Canvas z scrollbarem dla całej zawartości
    canvas_frame = tk.Frame(main_frame, bg=bg_color) # type: ignore
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
    
    main_canvas = tk.Canvas(canvas_frame, bg=bg_color, highlightthickness=0) # type: ignore
    main_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=main_canvas.yview) # type: ignore
    scrollable_main = tk.Frame(main_canvas, bg=bg_color) # type: ignore
    
    scrollable_main.bind(
        "<Configure>",
        lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    )
    
    main_canvas.create_window((0, 0), window=scrollable_main, anchor="nw")
    main_canvas.configure(yscrollcommand=main_scrollbar.set)
    
    main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Kontener dla siatki statystyk (3 kolumny)
    grid_container = tk.Frame(scrollable_main, bg=bg_color) # type: ignore
    grid_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Konfiguracja kolumn - 3 kolumny z różnymi proporcjami
    grid_container.columnconfigure(0, weight=0, minsize=220)  # Wykres kołowy - kompaktowy
    grid_container.columnconfigure(1, weight=1, minsize=320)  # MG vs Gracz
    grid_container.columnconfigure(2, weight=2, minsize=450)  # Systemy - potrzebuje więcej miejsca
    # Konfiguracja wiersza - jednolita wysokość
    grid_container.rowconfigure(0, weight=1, minsize=500)
    
    # Statystyka 1: Sesje RPG po roku (wiersz 0, kolumna 0)
    stats_frame = tk.Frame(grid_container, bg=frame_bg, relief='solid', borderwidth=1) # type: ignore
    stats_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    # Tytuł statystyki
    stats_title = tk.Label(
        stats_frame,
        text="📊 Liczba sesji RPG przeprowadzonych w poszczególnych latach",
        font=('Segoe UI', 14, 'bold'),
        bg=frame_bg,
        fg=fg_color
    )
    stats_title.pack(pady=(15, 10))
    
    # Pobierz dane z bazy
    try:
        conn = sqlite3.connect("sesje_rpg.db")
        c = conn.cursor()
        c.execute("SELECT data_sesji FROM sesje_rpg")
        rows = c.fetchall()
        conn.close()
        
        # Zlicz sesje po roku
        year_counts: dict = defaultdict(int) # type: ignore
        for row in rows:
            date_str = row[0]
            # Format daty: DD.MM.YYYY lub YYYY-MM-DD
            if '.' in date_str:
                # Format DD.MM.YYYY
                parts = date_str.split('.')
                if len(parts) == 3:
                    year = parts[2]
                    year_counts[year] += 1
            elif '-' in date_str:
                # Format YYYY-MM-DD
                parts = date_str.split('-')
                if len(parts) == 3:
                    year = parts[0]
                    year_counts[year] += 1
        
        # Sortuj lata malejąco
        sorted_years: list = sorted(year_counts.keys(), reverse=True) # type: ignore
        
        if sorted_years:
            # Ramka dla wykresu matplotlib
            chart_frame = tk.Frame(stats_frame, bg=frame_bg) # type: ignore
            chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 15))
            
            total_sessions: int = sum(year_counts.values()) # type: ignore
            
            # Kolory dla segmentów
            colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', '#FF9F40']
            
            # Dane do wykresu
            years_data: list[str] = list(sorted_years) # type: ignore
            counts_data = [year_counts[y] for y in years_data]
            
            # Legenda nad wykresem (wycentrowana)
            legend_frame = tk.Frame(chart_frame, bg=frame_bg) # type: ignore
            legend_frame.pack(fill=tk.X, pady=(5, 0))
            
            # Kontener na elementy legendy (wycentrowany)
            legend_inner = tk.Frame(legend_frame, bg=frame_bg) # type: ignore
            legend_inner.pack(anchor='center')
            
            for idx, year in enumerate(years_data):
                count = year_counts[year]
                percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
                color = colors[idx % len(colors)]
                
                legend_item = tk.Frame(legend_inner, bg=frame_bg) # type: ignore
                legend_item.pack(fill=tk.X, pady=3)
                
                # Kwadrat koloru (większy)
                color_box = tk.Canvas(legend_item, width=20, height=20, bg=frame_bg, highlightthickness=0) # type: ignore
                color_box.create_rectangle(2, 2, 18, 18, fill=color, outline='white')
                color_box.pack(side=tk.LEFT, padx=(0, 8))
                
                # Tekst (większy font)
                legend_text = tk.Label(
                    legend_item,
                    text=f"{year}: {count} sesji ({percentage:.1f}%)",
                    font=('Segoe UI', 12),
                    bg=frame_bg,
                    fg=fg_color,
                    anchor='w'
                )
                legend_text.pack(side=tk.LEFT)
            
            # Tworzenie wykresu matplotlib (powiększony)
            fig = Figure(figsize=(4.2, 3.5), dpi=100)
            fig.patch.set_facecolor(frame_bg)
            ax = fig.add_subplot(111)
            ax.set_facecolor(frame_bg)
            
            # Wykres kołowy
            wedges, texts, autotexts = ax.pie(  # type: ignore
                counts_data, 
                labels=years_data,
                colors=colors[:len(years_data)],
                autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
                startangle=90,
                explode=[0.02] * len(years_data),
                shadow=True,
                textprops={'fontsize': 11, 'color': fg_color}
            )
            
            # Styl etykiet procentowych
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            ax.set_title('Sesje RPG według roku', fontsize=11, fontweight='bold', color=fg_color, pad=5)
            
            # Osadzenie wykresu w tkinter
            canvas_widget = FigureCanvasTkAgg(fig, chart_frame)
            canvas_widget.draw()
            canvas_widget.get_tk_widget().pack(pady=(5, 0))
            
            # Podsumowanie
            summary_label = tk.Label(
                stats_frame,
                text=f"Łącznie: {total_sessions} sesji w {len(sorted_years)} latach", # type: ignore
                font=('Segoe UI', 12, 'bold'),
                bg=frame_bg,
                fg=fg_color
            )
            summary_label.pack(pady=(5, 15))
        else:
            no_data_label = tk.Label(
                stats_frame,
                text="Brak danych do wyświetlenia",
                font=('Segoe UI', 12),
                bg=frame_bg,
                fg=fg_color
            )
            no_data_label.pack(pady=30)
            
    except Exception as e:
        error_label = tk.Label(
            stats_frame,
            text=f"Błąd podczas pobierania danych:\n{str(e)}",
            font=('Segoe UI', 12),
            bg=frame_bg,
            fg='#CC0000'
        )
        error_label.pack(pady=30)
    
    # Statystyka 2: Główny użytkownik jako MG vs Gracz (wiersz 0, kolumna 1)
    user_stats_frame = tk.Frame(grid_container, bg=frame_bg, relief='solid', borderwidth=1) # type: ignore
    user_stats_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
    
    # Tytuł statystyki
    user_stats_title = tk.Label(
        user_stats_frame,
        text="👤 Główny użytkownik: Mistrz Gry vs Gracz",
        font=('Segoe UI', 14, 'bold'),
        bg=frame_bg,
        fg=fg_color
    )
    user_stats_title.pack(pady=(15, 10))
    
    # Pobierz głównego użytkownika
    try:
        conn_gracze = sqlite3.connect("gracze.db")
        c_gracze = conn_gracze.cursor()
        c_gracze.execute("SELECT id, nick FROM gracze WHERE glowny_uzytkownik = 1")
        main_user = c_gracze.fetchone()
        conn_gracze.close()
        
        if main_user:
            main_user_id = main_user[0]
            main_user_nick = main_user[1]
            
            # Pobierz dane z sesji
            conn_sesje = sqlite3.connect("sesje_rpg.db")
            c_sesje = conn_sesje.cursor()
            
            # Zlicz sesje jako MG po roku
            c_sesje.execute("SELECT data_sesji FROM sesje_rpg WHERE mg_id = ?", (main_user_id,))
            mg_sessions = c_sesje.fetchall()
            
            mg_by_year: dict[str, int] = defaultdict(int)
            for row in mg_sessions:
                date_str = row[0]
                year = None
                if '.' in date_str:
                    parts = date_str.split('.')
                    if len(parts) == 3:
                        year = parts[2]
                elif '-' in date_str:
                    parts = date_str.split('-')
                    if len(parts) == 3:
                        year = parts[0]
                if year:
                    mg_by_year[year] += 1
            
            # Zlicz sesje jako Gracz po roku
            c_sesje.execute("""
                SELECT s.data_sesji 
                FROM sesje_rpg s
                JOIN sesje_gracze sg ON s.id = sg.sesja_id
                WHERE sg.gracz_id = ?
            """, (main_user_id,))
            player_sessions = c_sesje.fetchall()
            
            player_by_year: dict[str, int] = defaultdict(int)
            for row in player_sessions:
                date_str = row[0]
                year = None
                if '.' in date_str:
                    parts = date_str.split('.')
                    if len(parts) == 3:
                        year = parts[2]
                elif '-' in date_str:
                    parts = date_str.split('-')
                    if len(parts) == 3:
                        year = parts[0]
                if year:
                    player_by_year[year] += 1
            
            conn_sesje.close()
            
            # Zbierz wszystkie lata
            all_years = set(mg_by_year.keys()) | set(player_by_year.keys())
            
            if all_years:
                # Nagłówek z nickiem głównego użytkownika
                nick_label = tk.Label(
                    user_stats_frame,
                    text=f"Nick: {main_user_nick}",
                    font=('Segoe UI', 12, 'italic'),
                    bg=frame_bg,
                    fg=fg_color
                )
                nick_label.pack(pady=(0, 10))
                
                # Combobox do wyboru roku
                year_selector_frame = tk.Frame(user_stats_frame, bg=frame_bg) # type: ignore
                year_selector_frame.pack(pady=(0, 10))
                
                year_label_select = tk.Label(
                    year_selector_frame,
                    text="Wybierz rok:",
                    font=('Segoe UI', 11),
                    bg=frame_bg,
                    fg=fg_color
                )
                year_label_select.pack(side=tk.LEFT, padx=(0, 10))
                
                sorted_years_user: list = sorted(all_years, reverse=True) # type: ignore
                year_var_user = tk.StringVar(value=str(sorted_years_user[0])) # type: ignore
                year_combo_user = ttk.Combobox(
                    year_selector_frame,
                    textvariable=year_var_user,
                    values=sorted_years_user, # type: ignore
                    state='readonly',
                    width=10,
                    font=('Segoe UI', 10)
                )
                year_combo_user.pack(side=tk.LEFT)
                
                # Ramka dla wykresu
                content_frame = tk.Frame(user_stats_frame, bg=frame_bg) # type: ignore
                content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
                
                def update_user_chart(*args: object) -> None:
                    """Aktualizuje wykres po zmianie roku"""
                    for widget in content_frame.winfo_children():
                        widget.destroy()
                    
                    selected_year = year_var_user.get()
                    year_mg = mg_by_year.get(selected_year, 0)
                    year_player = player_by_year.get(selected_year, 0)
                    
                    if year_mg > 0 or year_player > 0:
                        _total_year = year_mg + year_player
                        
                        # Tworzenie wykresu matplotlib
                        fig2 = Figure(figsize=(3.5, 3), dpi=100)
                        fig2.patch.set_facecolor(frame_bg)
                        ax2 = fig2.add_subplot(111)
                        ax2.set_facecolor(frame_bg)
                        
                        # Kolory
                        mg_color = '#2196F3' if not dark_mode else '#64B5F6'
                        player_color = '#4CAF50' if not dark_mode else '#81C784'
                        
                        # Dane do wykresu
                        sizes = [year_mg, year_player]
                        labels = ['MG', 'Gracz']
                        colors_pie = [mg_color, player_color]
                        explode = (0.05, 0.05)
                        
                        wedges, texts, autotexts = ax2.pie(  # type: ignore
                            sizes, 
                            labels=labels,
                            colors=colors_pie,
                            autopct=lambda pct: f'{pct:.1f}%' if pct > 0 else '',
                            startangle=90,
                            explode=explode,
                            shadow=True,
                            textprops={'fontsize': 10, 'color': fg_color}
                        )
                        
                        for autotext in autotexts:
                            autotext.set_color('white')
                            autotext.set_fontweight('bold')
                        
                        ax2.set_title(f'MG vs Gracz', fontsize=11, fontweight='bold', color=fg_color, pad=5)
                        
                        # Osadzenie wykresu w tkinter
                        canvas_widget2 = FigureCanvasTkAgg(fig2, content_frame)
                        canvas_widget2.draw()
                        canvas_widget2.get_tk_widget().pack()
                    else:
                        no_data_label = tk.Label(
                            content_frame,
                            text=f"Brak sesji w roku {selected_year}",
                            font=('Segoe UI', 11),
                            bg=frame_bg,
                            fg=fg_color
                        )
                        no_data_label.pack(pady=20)
                
                year_combo_user.bind('<<ComboboxSelected>>', update_user_chart)
                update_user_chart()
                
                # Ramka z scrollbarem dla szczegółów po roku
                user_results_frame = tk.Frame(user_stats_frame, bg=frame_bg) # type: ignore
                user_results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
                
                # Canvas i scrollbar
                user_canvas = tk.Canvas(user_results_frame, bg=frame_bg, highlightthickness=0, height=150) # type: ignore
                user_scrollbar = ttk.Scrollbar(user_results_frame, orient="vertical", command=user_canvas.yview) # type: ignore
                user_scrollable_frame = tk.Frame(user_canvas, bg=frame_bg) # type: ignore
                
                user_scrollable_frame.bind(
                    "<Configure>",
                    lambda e: user_canvas.configure(scrollregion=user_canvas.bbox("all"))
                )
                
                user_canvas.create_window((0, 0), window=user_scrollable_frame, anchor="nw")
                user_canvas.configure(yscrollcommand=user_scrollbar.set)
                
                user_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                # Wyświetl statystyki
                for year in sorted_years_user: # type: ignore
                    mg_count = mg_by_year[year]
                    player_count = player_by_year[year]
                    year_total = mg_count + player_count
                    mg_pct = (mg_count / year_total * 100) if year_total > 0 else 0
                    player_pct = (player_count / year_total * 100) if year_total > 0 else 0
                    
                    year_frame = tk.Frame(user_scrollable_frame, bg=frame_bg) # type: ignore
                    year_frame.pack(fill=tk.X, pady=2, padx=5)
                    
                    # Rok
                    year_label = tk.Label(
                        year_frame,
                        text=f"{year}:",
                        font=('Segoe UI', 11, 'bold'),
                        bg=frame_bg,
                        fg=fg_color,
                        width=6,
                        anchor='w'
                    )
                    year_label.pack(side=tk.LEFT, padx=(0, 5))
                    
                    # MG
                    mg_label = tk.Label(
                        year_frame,
                        text=f"🎲 MG: {mg_count} ({mg_pct:.1f}%)",
                        font=('Segoe UI', 10),
                        bg=frame_bg,
                        fg='#2196F3' if not dark_mode else '#64B5F6',
                        width=16,
                        anchor='w'
                    )
                    mg_label.pack(side=tk.LEFT, padx=(0, 5))
                    
                    # Gracz
                    player_label = tk.Label(
                        year_frame,
                        text=f"👥 Gracz: {player_count} ({player_pct:.1f}%)",
                        font=('Segoe UI', 10),
                        bg=frame_bg,
                        fg='#4CAF50' if not dark_mode else '#81C784',
                        width=18,
                        anchor='w'
                    )
                    player_label.pack(side=tk.LEFT)
                
                # Podsumowanie - wszystkie lata
                total_mg_all = sum(mg_by_year.values())
                total_player_all = sum(player_by_year.values())
                summary_user_label = tk.Label(
                    user_stats_frame,
                    text=f"Łącznie: {total_mg_all} sesji jako MG, {total_player_all} sesji jako Gracz",
                    font=('Segoe UI', 12, 'bold'),
                    bg=frame_bg,
                    fg=fg_color
                )
                summary_user_label.pack(pady=(5, 15))
            else:
                no_sessions_label = tk.Label(
                    user_stats_frame,
                    text=f"Główny użytkownik '{main_user_nick}' nie ma jeszcze żadnych sesji",
                    font=('Segoe UI', 12),
                    bg=frame_bg,
                    fg=fg_color
                )
                no_sessions_label.pack(pady=30)
        else:
            no_user_label = tk.Label(
                user_stats_frame,
                text="Nie znaleziono głównego użytkownika",
                font=('Segoe UI', 12),
                bg=frame_bg,
                fg=fg_color
            )
            no_user_label.pack(pady=30)
            
    except Exception as e:
        user_error_label = tk.Label(
            user_stats_frame,
            text=f"Błąd podczas pobierania danych:\n{str(e)}",
            font=('Segoe UI', 12),
            bg=frame_bg,
            fg='#CC0000'
        )
        user_error_label.pack(pady=30)
    
    # Statystyka 3: System/Ilość sesji w danym roku (wiersz 0, kolumna 2)
    system_sessions_frame = tk.Frame(grid_container, bg=frame_bg, relief='solid', borderwidth=1) # type: ignore
    system_sessions_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
    
    # Tytuł statystyki
    system_sessions_title = tk.Label(
        system_sessions_frame,
        text="🎮 Systemy RPG: Ilość sesji",
        font=('Segoe UI', 14, 'bold'),
        bg=frame_bg,
        fg=fg_color
    )
    system_sessions_title.pack(pady=(15, 10))
    
    # Selektor roku
    year_selector_frame = tk.Frame(system_sessions_frame, bg=frame_bg) # type: ignore
    year_selector_frame.pack(pady=(0, 10))
    
    year_label = tk.Label(
        year_selector_frame,
        text="Wybierz rok:",
        font=('Segoe UI', 11),
        bg=frame_bg,
        fg=fg_color
    )
    year_label.pack(side=tk.LEFT, padx=(0, 10))
    
    # Pobierz wszystkie dostępne lata z bazy
    try:
        conn_years = sqlite3.connect("sesje_rpg.db")
        c_years = conn_years.cursor()
        c_years.execute("SELECT DISTINCT data_sesji FROM sesje_rpg ORDER BY data_sesji DESC")
        all_dates = c_years.fetchall()
        conn_years.close()
        
        available_years = set()
        for row in all_dates:
            date_str = row[0]
            if '.' in date_str:
                parts = date_str.split('.')
                if len(parts) == 3:
                    available_years.add(parts[2])
            elif '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3:
                    available_years.add(parts[0])
        
        sorted_years_list = sorted(available_years, reverse=True)
        
        if sorted_years_list:
            year_var = tk.StringVar(value=sorted_years_list[0])
            year_combo = ttk.Combobox(
                year_selector_frame,
                textvariable=year_var,
                values=sorted_years_list,
                state="readonly",
                width=10,
                font=('Segoe UI', 10)
            )
            year_combo.pack(side=tk.LEFT)
            
            # Ramka dla wykresu
            chart_system_frame = tk.Frame(system_sessions_frame, bg=frame_bg) # type: ignore
            chart_system_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 15))
            
            def update_system_chart(*args: object) -> None:
                """Aktualizuje wykres po zmianie roku"""
                # Wyczyść zawartość
                for widget in chart_system_frame.winfo_children():
                    widget.destroy()
                
                selected_year = year_var.get()
                
                # Pobierz dane dla wybranego roku
                try:
                    # Pobierz sesje z wybranego roku
                    conn_sessions = sqlite3.connect("sesje_rpg.db")
                    c_sessions = conn_sessions.cursor()
                    
                    c_sessions.execute("""
                        SELECT system_id
                        FROM sesje_rpg
                        WHERE data_sesji LIKE ?
                    """, (f"%{selected_year}%",))
                    
                    sessions_data = c_sessions.fetchall()
                    conn_sessions.close()
                    
                    # Zlicz system_id
                    system_id_counts: dict[int, int] = defaultdict(int)
                    for row in sessions_data:
                        system_id = row[0]
                        if system_id:
                            system_id_counts[system_id] += 1
                    
                    # Pobierz nazwy systemów
                    conn_systems = sqlite3.connect("systemy_rpg.db")
                    c_systems = conn_systems.cursor()
                    
                    system_counts: dict[str, int] = {}
                    for system_id, count in system_id_counts.items():
                        c_systems.execute("SELECT nazwa FROM systemy_rpg WHERE id = ?", (system_id,))
                        result = c_systems.fetchone()
                        system_name = result[0] if result else f"System ID {system_id}"
                        system_counts[system_name] = count
                    
                    conn_systems.close()
                    
                    if system_counts:
                        # Sortuj systemy według ilości sesji malejąco
                        sorted_systems = sorted(system_counts.items(), key=lambda x: x[1], reverse=True)
                        
                        # Wykres słupkowy poziomy (matplotlib)
                        fig3 = Figure(figsize=(5, max(3, len(sorted_systems) * 0.4)), dpi=100)
                        fig3.patch.set_facecolor(frame_bg)
                        ax3 = fig3.add_subplot(111)
                        ax3.set_facecolor(frame_bg)
                        
                        # Dane - odwróć kolejność aby największe były na górze wykresu
                        systems = [s[0] for s in reversed(sorted_systems)]
                        counts = [s[1] for s in reversed(sorted_systems)]
                        
                        # Kolory
                        colors_bar = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', '#8B5CF6']
                        bar_colors = [colors_bar[i % len(colors_bar)] for i in range(len(systems))]
                        
                        # Wykres poziomy
                        y_pos = range(len(systems))
                        bars = ax3.barh(y_pos, counts, color=bar_colors, edgecolor='white', linewidth=1.5)
                        
                        # Etykiety
                        ax3.set_yticks(y_pos)
                        ax3.set_yticklabels(systems, fontsize=9, color=fg_color)
                        ax3.set_xlabel('Ilość sesji', fontsize=10, color=fg_color, fontweight='bold')
                        ax3.set_title(f'Sesje według systemów w {selected_year}', fontsize=11, fontweight='bold', color=fg_color, pad=10)
                        
                        # Styl osi
                        ax3.tick_params(axis='x', colors=fg_color)
                        ax3.tick_params(axis='y', colors=fg_color)
                        ax3.spines['bottom'].set_color(fg_color)
                        ax3.spines['left'].set_color(fg_color)
                        ax3.spines['top'].set_visible(False)
                        ax3.spines['right'].set_visible(False)
                        
                        # Dodaj wartości na słupkach
                        for _i, (bar, count) in enumerate(zip(bars, counts)):
                            width = bar.get_width()
                            ax3.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                                    str(count), 
                                    ha='left', va='center',
                                    fontweight='bold', fontsize=9, color=fg_color)
                        
                        # Dopasuj layout
                        fig3.tight_layout()
                        
                        # Osadzenie wykresu
                        canvas_widget3 = FigureCanvasTkAgg(fig3, chart_system_frame)
                        canvas_widget3.draw()
                        canvas_widget3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                        
                        # Podsumowanie
                        total_system_sessions = sum(counts)
                        summary_system_label = tk.Label(
                            chart_system_frame,
                            text=f"Łącznie: {total_system_sessions} sesji w {len(systems)} systemach",
                            font=('Segoe UI', 11, 'bold'),
                            bg=frame_bg,
                            fg=fg_color
                        )
                        summary_system_label.pack(pady=(5, 10))
                    else:
                        no_data_system_label = tk.Label(
                            chart_system_frame,
                            text=f"Brak sesji w roku {selected_year}",
                            font=('Segoe UI', 11),
                            bg=frame_bg,
                            fg=fg_color
                        )
                        no_data_system_label.pack(pady=30)
                        
                except Exception as e:
                    error_system_label = tk.Label(
                        chart_system_frame,
                        text=f"Błąd: {str(e)}",
                        font=('Segoe UI', 10),
                        bg=frame_bg,
                        fg='#CC0000'
                    )
                    error_system_label.pack(pady=30)
            
            # Bind zmiany roku
            year_var.trace_add('write', update_system_chart)
            update_system_chart()  # Inicjalne wywołanie
        else:
            no_years_label = tk.Label(
                system_sessions_frame,
                text="Brak danych o sesjach",
                font=('Segoe UI', 11),
                bg=frame_bg,
                fg=fg_color
            )
            no_years_label.pack(pady=30)
            
    except Exception as e:
        system_error_label = tk.Label(
            system_sessions_frame,
            text=f"Błąd podczas pobierania danych:\n{str(e)}",
            font=('Segoe UI', 11),
            bg=frame_bg,
            fg='#CC0000'
        )
        system_error_label.pack(pady=30)
