@echo off
setlocal

REM ===========================================
REM 🟢 PianoRollStudio - App Starter (Embedded)
REM ===========================================

echo 📦 Using embedded Python: pythonpackages\python.exe

if not exist "pythonpackages\python.exe" (
    echo ❌ Embedded Python not found in pythonpackages\
    echo Please make sure python.exe is inside that folder.
    pause
    exit /b 1
)

echo 🚀 Launching app.py using embedded Python...
pythonpackages\python.exe app.py

echo 🛑 Application closed.
pause
