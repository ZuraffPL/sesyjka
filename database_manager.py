# -*- coding: utf-8 -*-
"""
Moduł zarządzania ścieżkami i migracjami baz danych
Zapewnia kompatybilność wsteczną przy aktualizacjach aplikacji
"""

import os
import sqlite3
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

# Wersja schematu bazy danych
CURRENT_DB_VERSION = 1

def get_app_data_dir() -> Path:
    """
    Pobiera katalog danych aplikacji w folderze użytkownika.
    Struktura: C:/Users/{username}/AppData/Local/Sesyjka/
    
    Returns:
        Path: Ścieżka do katalogu danych aplikacji
    """
    if os.name == 'nt':  # Windows
        app_data = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
        app_dir = Path(app_data) / 'Sesyjka'
    else:  # Linux/Mac
        app_dir = Path.home() / '.sesyjka'
    
    # Utwórz katalog jeśli nie istnieje
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_db_path(db_name: str) -> str:
    """
    Pobiera pełną ścieżkę do pliku bazy danych.
    
    Args:
        db_name: Nazwa pliku bazy danych (np. 'systemy_rpg.db')
    
    Returns:
        str: Pełna ścieżka do pliku bazy danych
    """
    app_dir = get_app_data_dir()
    db_path = app_dir / db_name
    return str(db_path)

def migrate_old_databases() -> None:
    """
    Migruje stare bazy danych z katalogu aplikacji do folderu użytkownika.
    Tworzy kopie zapasowe podczas migracji.
    """
    old_db_files = [
        "systemy_rpg.db",
        "sesje_rpg.db",
        "gracze.db",
        "wydawcy.db"
    ]
    
    app_dir = get_app_data_dir()
    current_dir = Path.cwd()
    
    for db_file in old_db_files:
        old_path = current_dir / db_file
        new_path = app_dir / db_file
        
        # Jeśli stara baza istnieje w katalogu aplikacji i nie istnieje w nowej lokalizacji
        if old_path.exists() and not new_path.exists():
            try:
                # Skopiuj bazę danych do nowej lokalizacji
                shutil.copy2(old_path, new_path)
                print(f"✓ Zmigrowano {db_file} do {app_dir}")
                
                # Opcjonalnie: Utwórz backup starej bazy
                backup_name = f"{db_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path = current_dir / backup_name
                shutil.copy2(old_path, backup_path)
                print(f"✓ Utworzono backup: {backup_name}")
                
            except Exception as e:
                print(f"⚠ Błąd podczas migracji {db_file}: {e}")

def get_db_version(db_path: str) -> int:
    """
    Pobiera wersję schematu bazy danych.
    
    Args:
        db_path: Ścieżka do pliku bazy danych
    
    Returns:
        int: Numer wersji schematu (0 jeśli tabela nie istnieje)
    """
    if not os.path.exists(db_path):
        return 0
    
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='db_version'
            """)
            
            if c.fetchone():
                c.execute("SELECT version FROM db_version LIMIT 1")
                result = c.fetchone()
                return result[0] if result else 0
            return 0
    except Exception:
        return 0

def set_db_version(db_path: str, version: int) -> None:
    """
    Ustawia wersję schematu bazy danych.
    
    Args:
        db_path: Ścieżka do pliku bazy danych
        version: Numer wersji do ustawienia
    """
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        
        # Utwórz tabelę wersji jeśli nie istnieje
        c.execute("""
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Usuń starą wersję i wstaw nową
        c.execute("DELETE FROM db_version")
        c.execute("INSERT INTO db_version (version) VALUES (?)", (version,))
        conn.commit()

def backup_database(db_path: str) -> Optional[str]:
    """
    Tworzy kopię zapasową bazy danych przed migracją.
    
    Args:
        db_path: Ścieżka do pliku bazy danych
    
    Returns:
        Optional[str]: Ścieżka do pliku backup lub None w przypadku błędu
    """
    if not os.path.exists(db_path):
        return None
    
    try:
        app_dir = get_app_data_dir()
        backups_dir = app_dir / 'backups'
        backups_dir.mkdir(exist_ok=True)
        
        db_name = Path(db_path).name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{db_name}.backup_{timestamp}"
        backup_path = backups_dir / backup_name
        
        shutil.copy2(db_path, backup_path)
        print(f"✓ Utworzono backup: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        print(f"⚠ Błąd podczas tworzenia backupu: {e}")
        return None

def migrate_database_schema(db_path: str, db_name: str) -> None:
    """
    Przeprowadza migrację schematu bazy danych do najnowszej wersji.
    
    Args:
        db_path: Ścieżka do pliku bazy danych
        db_name: Nazwa bazy danych (dla identyfikacji typu)
    """
    current_version = get_db_version(db_path)
    
    if current_version >= CURRENT_DB_VERSION:
        return  # Baza jest aktualna
    
    # Utwórz backup przed migracją
    backup_database(db_path)
    
    print(f"Migracja {db_name} z wersji {current_version} do {CURRENT_DB_VERSION}")
    
    # W przyszłości tutaj będą migracje dla różnych wersji
    # if current_version < 1:
    #     migrate_to_v1(db_path, db_name)
    # if current_version < 2:
    #     migrate_to_v2(db_path, db_name)
    
    # Ustaw nową wersję
    set_db_version(db_path, CURRENT_DB_VERSION)
    print(f"✓ Migracja {db_name} zakończona")

def initialize_app_databases() -> None:
    """
    Inicjalizuje wszystkie bazy danych aplikacji.
    Wykonuje migrację starych baz i sprawdza zgodność wersji.
    """
    print("=" * 60)
    print("Inicjalizacja baz danych Sesyjka")
    print("=" * 60)
    
    # Najpierw sprawdź czy są stare bazy do migracji
    migrate_old_databases()
    
    # Zainicjalizuj ścieżki do nowych baz
    db_configs = {
        'systemy_rpg.db': 'Systemy RPG',
        'sesje_rpg.db': 'Sesje RPG',
        'gracze.db': 'Gracze',
        'wydawcy.db': 'Wydawcy'
    }
    
    app_dir = get_app_data_dir()
    print(f"\nLokalizacja baz danych: {app_dir}")
    print("-" * 60)
    
    for db_file, db_label in db_configs.items():
        db_path = get_db_path(db_file)
        
        if os.path.exists(db_path):
            print(f"✓ {db_label}: Znaleziono istniejącą bazę")
            # Sprawdź wersję i ewentualnie zmigruj
            migrate_database_schema(db_path, db_file)
        else:
            print(f"→ {db_label}: Utworzenie nowej bazy")
    
    print("=" * 60)
    print("Inicjalizacja zakończona")
    print("=" * 60)
    print()

# Eksportuj funkcje dla kompatybilności
__all__ = [
    'get_app_data_dir',
    'get_db_path',
    'migrate_old_databases',
    'initialize_app_databases',
    'backup_database',
    'CURRENT_DB_VERSION'
]
