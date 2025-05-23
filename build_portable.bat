@echo off
REM ================================================================
REM PianoRollStudio Portable EXE Builder (Plugins External)
REM ================================================================
REM This script builds a single-file executable (app.exe).
REM - 'assets' and 'soundbank' are bundled into the .exe.
REM - The 'plugins' directory is NOT bundled. The app.exe will
REM   look for a 'plugins' folder next to itself at runtime.
REM - Includes 'requests' library for plugins that need it.
REM - Excludes other Qt bindings to prevent conflicts with PySide6.
REM
REM Instructions for distribution:
REM 1. Run this script to build dist\PianoRollStudio.exe.
REM 2. Create a folder for your application (e.g., PianoRollStudio_App).
REM 3. Copy dist\PianoRollStudio.exe into your application folder.
REM 4. Create a 'plugins' subfolder next to PianoRollStudio.exe (e.g., PianoRollStudio_App\plugins\).
REM 5. Place your .py plugin files into this 'plugins' subfolder.
REM ================================================================

REM Go to the directory where this script is located (should be project root)
cd /d "%~dp0"

REM Clean previous build directories
echo Cleaning previous build directories (dist, build)...
if exist "dist" (
    echo Removing old dist directory...
    rmdir /s /q dist
)
if exist "build" (
    echo Removing old build directory...
    rmdir /s /q build
)
echo Cleaning complete.
echo.

REM Build single-file app.exe
echo Building executable (PianoRollStudio.exe)...
pyinstaller app.py ^
  --noconsole ^
  --onefile ^
  --name PianoRollStudio ^
  --icon=assets/icons/app_icon.ico ^
  --add-data "assets;assets" ^
  --add-data "soundbank;soundbank" ^
  --hidden-import requests ^
  --exclude-module PyQt5 ^
  --exclude-module PySide2 ^
  --exclude-module PyQt6 ^
  --exclude-module PySide5

echo.
echo ================================================================
echo Build complete!
echo ================================================================
echo Your portable application is: dist\PianoRollStudio.exe
echo.
echo IMPORTANT:
echo To run the application with plugins:
echo 1. Create a folder (e.g., "MyPianoRollApp").
echo 2. Copy "dist\PianoRollStudio.exe" into that folder.
echo 3. Create a "plugins" subfolder next to "PianoRollStudio.exe".
echo    (e.g., "MyPianoRollApp\plugins\")
echo 4. Place your .py plugin files into this "plugins" subfolder.
echo.
echo The application will load plugins from this external 'plugins' directory.
echo 'assets' and 'soundbank' are bundled within PianoRollStudio.exe.
echo The 'requests' library is also bundled for plugins that require it.
echo If a plugin needs 'google-generativeai', it will not load unless
echo you add '--hidden-import google.generativeai' back to this script
echo and ensure the package is in your build environment.
echo ================================================================
echo.
pause
