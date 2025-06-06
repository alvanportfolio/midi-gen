#!/bin/bash

echo "=== Downloading alex_melody.pth model ==="

MODEL_URL="https://huggingface.co/asigalov61/Godzilla-Piano-Transformer/resolve/main/alex_melody.pth"
TARGET_DIR="ai_studio/models"
MODEL_PATH="$TARGET_DIR/alex_melody.pth"

# Create target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Download with curl
curl -L "$MODEL_URL" -o "$MODEL_PATH"
if [ $? -ne 0 ]; then
    echo
    echo "❌ Error: Failed to download the model."
    echo "Please download manually from:"
    echo "$MODEL_URL"
    echo "Then place it into: $TARGET_DIR and rename it to alex_melody.pth"
    exit 1
fi

echo "✅ Model downloaded successfully to $MODEL_PATH"
exit 0
