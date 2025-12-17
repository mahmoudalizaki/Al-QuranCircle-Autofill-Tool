@echo off
echo ===============================
echo Cleaning old build files...
echo ===============================

REM حذف بقايا بيلد قديمة
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del *.spec 2>nul

echo Clean done.
echo.

REM ===============================
REM Paths
REM ===============================
set ICON_PATH=K:\WebDev\Extentions\autofillmyform\images\icon.ico
set UPX_PATH=K:\WebDev\Extentions\autofillmyform\upx-5.0.2-win64
set VERSION_FILE=K:\WebDev\Extentions\autofillmyform\version-file.txt
set MANIFEST_FILE=K:\WebDev\Extentions\autofillmyform\app.manifest
set MAIN_SCRIPT=K:\WebDev\Extentions\autofillmyform\main.py
set ADD_DATA=K:\WebDev\Extentions\autofillmyform\images;images

REM ===============================
REM PyInstaller Build
REM ===============================
pyinstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --clean ^
    --icon "%ICON_PATH%" ^
    --upx-dir "%UPX_PATH%" ^
    --version-file "%VERSION_FILE%" ^
    --manifest "%MANIFEST_FILE%" ^
    --add-data "%ADD_DATA%" ^
    --collect-all arabic_reshaper ^
    --collect-all bidi ^
    --collect-all customtkinter ^
    "%MAIN_SCRIPT%"

echo.
echo ===============================
echo Build finished successfully!
echo ===============================
pause
