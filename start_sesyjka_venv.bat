@echo off
REM Uruchamia aplikację Sesyjka z użyciem środowiska wirtualnego
D:\Sesyjka\.venv\Scripts\python.exe main.py
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo === BLAD: Aplikacja zakonczyla sie z kodem %ERRORLEVEL% ===
    pause
)
