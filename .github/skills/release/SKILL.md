---
name: release
description: 'Tworzy nowe wydanie Sesyjki: bump wersji, build EXE (PyInstaller), publikacja na GitHubie. Use when: user asks to release, wydać nową wersję, zbudować i opublikować EXE, "zrób release", "nowy release", "wypuść wersję".'
---

# Release Sesyjki

## Kiedy używać
Użytkownik prosi o wydanie nowej wersji aplikacji (bump wersji, build `.exe`, publikacja assetów na GitHub).

## Procedura
Pełna procedura krok po kroku znajduje się w [create_release.prompt.md](../../../create_release.prompt.md)
w katalogu głównym repo — wykonaj ją w całości, w podanej kolejności.

## Krytyczne pułapki (zweryfikowane, 2026-09-03)

### `gh release create --notes` z heredoc PowerShell
NIE przekazuj wieloliniowych release notes przez zmienną `$notes` zbudowaną heredokiem
`@"..."@` do `--notes $notes` — markdown (nagłówki, listy, emoji, backtick) wewnątrz
heredocu potrafi przerwać/pomieszać wywołanie `gh`, co skutkuje **draftem** z brakującym
plikiem `.exe` wśród assets. `create_release.prompt.md` (Krok 9) stosuje bezpieczny
wzorzec: zapis notatek do pliku tymczasowego + `gh release create ... --notes-file`.

### Zawsze weryfikuj wynik release'u
Nie zakładaj sukcesu na podstawie samego outputu terminala (bywa ucięty przy długich
komendach). Po `gh release create` zawsze:
```powershell
gh release view v{wersja} --json isDraft,tagName,assets --jq "{isDraft, tagName, assets: [.assets[].name]}"
```
Jeśli `isDraft: true` lub brakuje `.exe` w assets, napraw przez:
```powershell
gh release upload v{wersja} "dist\Sesyjka-v{wersja}.exe"
gh release edit v{wersja} --draft=false
```

### `git log v{stara}..HEAD --oneline` może zwrócić pustą listę
Mimo realnych zmian — sprawdź wtedy `git status --short` (niezacommitowane zmiany
w plikach źródłowych) i `git diff --stat`, żeby zbudować changelog na podstawie diffu,
nie tylko commitów.

### Build PyInstaller
`.venv\Scripts\pyinstaller.exe --noconfirm Sesyjka-v{wersja}.spec` działa w trybie
sync bez problemu (build trwa rząd kilkudziesięciu sekund), nie wymaga trybu tła.

## Po zakończeniu
Jeśli podczas release'u natrafisz na nową pułapkę, zapisz ją do pamięci repo
(`/memories/repo/release_process_gotchas.md`), żeby kolejne wydania jej nie powtórzyły.
