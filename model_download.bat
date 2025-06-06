@echo off
setlocal

echo === Downloading alex_melody.pth model ===

:: Define model URL and target path
set "MODEL_URL=https://huggingface.co/asigalov61/Godzilla-Piano-Transformer/resolve/main/alex_melody.pth"
set "TARGET_DIR=ai_studio\models"
set "MODEL_PATH=%TARGET_DIR%\alex_melody.pth"

:: Create target directory if it doesn't exist
if not exist "%TARGET_DIR%" (
    echo Creating target directory...
    mkdir "%TARGET_DIR%"
)

:: Use curl to download
curl -L "%MODEL_URL%" -o "%MODEL_PATH%"
if %errorlevel% neq 0 (
    echo.
    echo ❌ Error: Failed to download the model.
    echo Please download manually from:
    echo %MODEL_URL%
    echo Then place it into: %TARGET_DIR% and rename it to alex_melody.pth
    exit /b 1
)

echo ✅ Model downloaded successfully to %MODEL_PATH%
exit /b 0
