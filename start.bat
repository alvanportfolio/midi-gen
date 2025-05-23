@echo off
echo Checking Python installation...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Checking required modules...
python -c "import sys, subprocess; required_modules = ['PySide6', 'pretty_midi', 'numpy', 'pygame', 'mido', 'python-rtmidi']; missing = [m for m in required_modules if m not in sys.modules and subprocess.call([sys.executable, '-c', 'import ' + m], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL) != 0]; print('Missing modules: ' + ', '.join(missing) if missing else 'All required modules found!')"

set /p install_modules="Install missing modules? (y/n): "
if /i "%install_modules%"=="y" (
    echo Installing required modules...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo Failed to install modules. Please check your internet connection or install them manually.
        pause
        exit /b 1
    )
    echo Modules installed successfully!
)

echo Starting Piano Roll Application...
python app.py
echo Application closed.
pause
