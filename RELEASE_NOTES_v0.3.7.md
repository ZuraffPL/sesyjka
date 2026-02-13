# 🎉 Sesyjka v0.3.7 - Initial Public Release

## 📦 What's New

### 🔄 Status Display Improvements

**Enhanced "For Sale" Status Logic:**
- Items marked as "For Sale" now display as "In Collection, For Sale"
- Logical approach: items for sale must be in possession
- Display format: `{game_status}, In Collection, For Sale`
- Example: `Played, In Collection, For Sale`

**Purchase Price Handling:**
- Purchase price is now shown for "For Sale" status
- Add/Edit forms include purchase price field for "For Sale" items
- Consistent logic: items for sale have purchase price (like "In Collection")
- Format: price + currency (e.g., '150.00 PLN')

**Filters & Row Coloring:**
- Filters work correctly with the new status format
- Red highlighting for "For Sale" rows remains active
- Status checking uses 'in' operator for flexibility

**Technical Changes:**
- Module: `systemy_rpg.py`
- Display function: `get_all_systems()`
- Add functions: `dodaj_system_rpg()`, `dodaj_suplement_do_systemu()`
- Edit function: `edit_system_rpg_dialog()`
- Form handlers: `on_status_kolekcja_change()` (3 occurrences)

### 📁 Repository Setup

**Initial Release Features:**
- Complete project structure with all source files
- Comprehensive README with installation instructions
- Icons and assets included
- Git repository initialized with proper .gitignore
- License changed to CC BY 4.0 (Creative Commons Attribution 4.0)
- Author information updated (Zuraffpl, zuraffpl@gmail.com)

## 🎯 Features

### Core Functionality
- 🎲 **RPG Systems Management** - Collection management with hierarchical structure
- ⚔️ **RPG Sessions** - Session tracking with player management
- 👥 **Players Database** - Contact information and session history
- 🏢 **Publishers Database** - Publisher information with contact details
- 📊 **Statistics** - Automatic chart generation with manual refresh option
- 🔍 **Advanced Filtering** - Persistent filters across all tabs

### Technical Stack
- Python 3.9+
- CustomTkinter (modern GUI)
- tksheet (spreadsheet views)
- matplotlib (statistics charts)
- SQLite (database)

## 📥 Installation

```bash
git clone https://github.com/ZuraffPL/sesyjka.git
cd sesyjka
python -m venv .venv
.venv\Scripts\activate
pip install customtkinter tksheet matplotlib
python main.py
```

## 📋 Requirements
- Windows 10 or newer
- Python 3.9 or newer

## 📄 License

This project is licensed under [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) (Creative Commons Attribution 4.0 International)

## 👨‍💻 Author

**Zuraffpl**
- Email: zuraffpl@gmail.com
- GitHub: [@ZuraffPL](https://github.com/ZuraffPL)

## 🔗 Links

- [Repository](https://github.com/ZuraffPL/sesyjka)
- [Issues](https://github.com/ZuraffPL/sesyjka/issues)
- [License](https://github.com/ZuraffPL/sesyjka/blob/main/LICENSE)

---

Created with ❤️ for the TTRPG community
