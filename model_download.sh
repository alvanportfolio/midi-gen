#!/bin/bash

# ===========================================
# 🤖 MIDI-GEN - Model Download Script (Unix)
# ===========================================

echo "=== Downloading alex_melody.pth model ==="

# Define model URL and target path
MODEL_URL="https://huggingface.co/datasets/asigalov61/misc-and-temp/resolve/main/model_checkpoint_21254_steps_0.2733_loss_0.9145_acc.pth"
TARGET_DIR="ai_studio/models"
MODEL_PATH="$TARGET_DIR/alex_melody.pth"

# Create target directory if it doesn't exist
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating target directory..."
    mkdir -p "$TARGET_DIR"
fi

# Use curl or wget to download
echo "🔄 Downloading model from Hugging Face..."
echo "Source: $MODEL_URL"
echo "Target: $MODEL_PATH"
echo

if command -v curl &>/dev/null; then
    curl -L "$MODEL_URL" -o "$MODEL_PATH"
    DOWNLOAD_EXIT_CODE=$?
elif command -v wget &>/dev/null; then
    wget "$MODEL_URL" -O "$MODEL_PATH"
    DOWNLOAD_EXIT_CODE=$?
else
    echo "❌ Error: Neither curl nor wget is available for downloading."
    DOWNLOAD_EXIT_CODE=1
fi

if [ $DOWNLOAD_EXIT_CODE -ne 0 ]; then
    echo
    echo "❌ Error: Failed to download the model automatically."
    echo
    echo "📋 MANUAL DOWNLOAD INSTRUCTIONS:"
    echo "================================================"
    echo "1. Copy this link and open it in your browser:"
    echo "   $MODEL_URL"
    echo
    echo "2. Download the file and rename it to: alex_melody.pth"
    echo
    echo "3. Place it in this folder: $TARGET_DIR"
    echo
    echo "4. Alternatively, check the README.txt file in ai_studio/models"
    echo "   for additional download instructions and alternative links."
    echo "================================================"
    echo
    echo "Press Enter to exit..."
    read
    exit 1
fi

echo "✅ Model downloaded successfully to $MODEL_PATH"

# Make the script executable
chmod +x "$0" 2>/dev/null

exit 0
