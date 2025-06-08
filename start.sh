#!/bin/bash

# ===========================================
# 🎹 MIDI-GEN - Launcher (Unix)
# ===========================================

echo "🎹 Starting MIDI-GEN..."

PYTHON_DIR="pythonpackages"

# Check if pythonpackages environment exists
if [ ! -d "$PYTHON_DIR" ]; then
    echo "❌ Python environment not found: $PYTHON_DIR"
    echo "Please run ./install.sh first to set up the environment."
    echo "For troubleshooting, check installations.md"
    exit 1
fi

if [ ! -f "$PYTHON_DIR/bin/python" ]; then
    echo "❌ Python executable not found: $PYTHON_DIR/bin/python"
    echo "The environment appears to be corrupted. Please run ./install.sh to reinstall."
    echo "For troubleshooting, check installations.md"
    exit 1
fi

# Activate the pythonpackages environment
echo "🔄 Activating Python environment from $PYTHON_DIR..."
source "$PYTHON_DIR/bin/activate"

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate Python environment."
    echo "The environment may be corrupted. Please run ./install.sh to reinstall."
    echo "For troubleshooting, check installations.md"
    exit 1
fi

echo "✅ Python environment activated successfully"

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found in current directory"
    echo "Please make sure you're running this script from the project root"
    echo "For troubleshooting, check installations.md"
    exit 1
fi

echo "🚀 Launching MIDI-GEN application..."

# Run the main application
python app.py

# Check exit code
if [ $? -ne 0 ]; then
    echo "❌ Application terminated with an error. Check the log above."
    echo "For troubleshooting, check installations.md"
    echo "Press Enter to exit..."
    read
    exit 1
fi

echo "👋 Application closed successfully. Press Enter to exit..."
read
