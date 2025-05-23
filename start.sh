#!/bin/bash
# filepath: c:\Users\Alvan\Documents\00TSANDALONE-PIANOROLL-FOR-MIDIGEN\FINAL-MIDI-WORKING-JULES\midi-gen\start.sh

echo "Checking Python installation..."

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH."
    echo "Please install Python 3.8 or higher from https://www.python.org/downloads/"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Checking required modules..."
MISSING_MODULES=$(python3 -c "
import sys
import subprocess
required_modules = ['PySide6', 'pretty_midi', 'numpy', 'pygame', 'mido', 'python-rtmidi']
missing = [m for m in required_modules if subprocess.call([sys.executable, '-c', 'import ' + m], 
           stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL) != 0]
print(','.join(missing) if missing else '')
")

if [ -n "$MISSING_MODULES" ]; then
    echo "Missing modules: $MISSING_MODULES"
    read -p "Install missing modules? (y/n): " INSTALL_MODULES
    if [ "$INSTALL_MODULES" = "y" ] || [ "$INSTALL_MODULES" = "Y" ]; then
        echo "Installing required modules..."
        python3 -m pip install --upgrade pip
        python3 -m pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "Failed to install modules. Please check your internet connection or install them manually."
            read -p "Press Enter to exit..."
            exit 1
        fi
        echo "Modules installed successfully!"
    fi
else
    echo "All required modules found!"
fi

echo "Starting Piano Roll Application..."
python3 app.py
echo "Application closed."
read -p "Press Enter to exit..."
