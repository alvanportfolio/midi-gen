#!/bin/bash
echo "Starting Piano Roll Application..."
# Try python3 first, then python if python3 is not available
if command -v python3 &>/dev/null; then
    python3 app.py
elif command -v python &>/dev/null; then
    python app.py
else
    echo "Python not found. Please install Python 3."
    exit 1
fi
echo "Application closed."
