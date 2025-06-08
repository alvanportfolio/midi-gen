@echo off
setlocal

echo === Downloading alex_melody.pth model ===

:: Define model URL and target path
set "MODEL_URL=https://huggingface.co/datasets/asigalov61/misc-and-temp/resolve/main/model_checkpoint_21254_steps_0.2733_loss_0.9145_acc.pth"
set "TARGET_DIR=ai_studio\models"
set "MODEL_PATH=%TARGET_DIR%\alex_melody.pth"

:: Create target directory if it doesn't exist
if not exist "%TARGET_DIR%" (
    echo Creating target directory...
    mkdir "%TARGET_DIR%"
)

:: Use curl to download
echo 🔄 Downloading model from Hugging Face...
echo Source: %MODEL_URL%
echo Target: %MODEL_PATH%
echo.

curl -L "%MODEL_URL%" -o "%MODEL_PATH%"
if %errorlevel% neq 0 (
    echo.
    echo ❌ Error: Failed to download the model automatically.
    echo.
    echo 📋 MANUAL DOWNLOAD INSTRUCTIONS:
    echo ================================================
    echo 1. Copy this link and open it in your browser:
    echo    %MODEL_URL%
    echo.
    echo 2. Download the file and rename it to: alex_melody.pth
    echo.
    echo 3. Place it in this folder: %TARGET_DIR%
    echo.
    echo 4. Alternatively, check the README.txt file in ai_studio/models
    echo    for additional download instructions and alternative links.
    echo ================================================
    echo.
    pause
    exit /b 1
)

echo ✅ Model downloaded successfully to %MODEL_PATH%
exit /b 0
