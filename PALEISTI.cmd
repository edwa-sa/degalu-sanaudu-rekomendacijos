@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Degalu sanaudu rekomendaciju sistema
echo Tikrinamas Python 3.12...
py -3.12 -c "import sys; assert sys.version_info[:2] == (3,12)" >nul 2>&1
if not errorlevel 1 (
    py -3.12 paleidimas.py
    goto pabaiga
)
python -c "import sys; assert sys.version_info[:2] == (3,12)" >nul 2>&1
if not errorlevel 1 (
    python paleidimas.py
    goto pabaiga
)
echo.
echo Nerastas Python 3.12.
echo Idiekite Python 3.12 is oficialios svetaines https://www.python.org/downloads/
echo Diegdami palikite tkinter ir pip komponentus, pazymekite Add Python to PATH.
echo Tada vel paleiskite si faila.
:pabaiga
echo.
echo Jei programa nepasileido, nukopijuokite auksciau esanti klaidos teksta.
pause
endlocal
