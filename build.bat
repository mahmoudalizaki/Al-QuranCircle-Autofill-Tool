@echo off
REM --- PyInstaller build script for autofillmyform ---

REM Paths
set ICON_PATH=K:\WebDev\Extentions\autofillmyform\images\icon.ico
set UPX_PATH=K:\WebDev\Extentions\autofillmyform\upx-5.0.2-win64
set VERSION_FILE=K:\WebDev\Extentions\autofillmyform\version-file.txt
set MANIFEST_FILE=K:\WebDev\Extentions\autofillmyform\app.manifest
set MAIN_SCRIPT=K:\WebDev\Extentions\autofillmyform\main.py
set ADD_DATA=K:\WebDev\Extentions\autofillmyform\images;images/

REM --- Build with PyInstaller ---
pyinstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --icon "%ICON_PATH%" ^
    --upx-dir "%UPX_PATH%" ^
    --version-file "%VERSION_FILE%" ^
    --manifest "%MANIFEST_FILE%" ^
    --add-data "%ADD_DATA%" ^
    --hidden-import "customtkinter" ^
    --hidden-import "playwright" ^
    --hidden-import "reportlab" ^
    --hidden-import "tkcalendar" ^
    --hidden-import "requests" ^
    "%MAIN_SCRIPT%"

echo.
echo Build finished!
pause
