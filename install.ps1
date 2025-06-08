# ===========================================
# PianoRollStudio - PowerShell Installation Script
# Professional Installation System
# ===========================================

# Set execution policy for current process
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Configuration Variables
$PYTHON_ZIP = "pythonpackages.zip"
$PYTHON_DIR = "pythonpackages"
$TEMP_UNZIP = "temp_py_unpack"
$LOG_FILE = "install.log"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Set window title and location
$Host.UI.RawUI.WindowTitle = "PianoRollStudio Installation"
Set-Location $SCRIPT_DIR

# Initialize log file
"PianoRollStudio Installation Log" | Out-File -FilePath $LOG_FILE -Encoding UTF8
"Started: $(Get-Date)" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
"" | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8

function Write-Log {
    param([string]$Message)
    $Message | Out-File -FilePath $LOG_FILE -Append -Encoding UTF8
}

function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $coloredMessage = switch($Type) {
        "SUCCESS" { Write-Host "[$Type] $Message" -ForegroundColor Green }
        "ERROR" { Write-Host "[$Type] $Message" -ForegroundColor Red }
        "WARNING" { Write-Host "[$Type] $Message" -ForegroundColor Yellow }
        default { Write-Host "[$Type] $Message" -ForegroundColor Cyan }
    }
    Write-Log "[$timestamp] [$Type] $Message"
}

# Display header
Write-Host ""
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host "   PianoRollStudio Installation System" -ForegroundColor Magenta
Write-Host "===============================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
Write-Host "Script location: $SCRIPT_DIR" -ForegroundColor Gray
Write-Host ""

try {
    # STEP 1: Validate Python Environment
    Write-Host "[STEP 1/4] Validating Python Environment..." -ForegroundColor Yellow
    
    $pythonExe = Join-Path $PYTHON_DIR "python.exe"
    
    if (Test-Path $pythonExe) {
        Write-Status "Python environment found at $pythonExe" "SUCCESS"
    }
    elseif (Test-Path $PYTHON_ZIP) {
        Write-Status "Extracting Python environment from $PYTHON_ZIP..." "INFO"
        
        # Clean up previous attempts
        if (Test-Path $PYTHON_DIR) {
            Write-Status "Removing existing Python directory..." "INFO"
            Remove-Item -Path $PYTHON_DIR -Recurse -Force -ErrorAction SilentlyContinue
        }
        if (Test-Path $TEMP_UNZIP) {
            Write-Status "Removing temporary extraction directory..." "INFO"
            Remove-Item -Path $TEMP_UNZIP -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        # Create temp directory and extract
        New-Item -ItemType Directory -Path $TEMP_UNZIP -Force | Out-Null
        Write-Status "Extracting ZIP contents..." "INFO"
        
        Expand-Archive -Path $PYTHON_ZIP -DestinationPath $TEMP_UNZIP -Force
        
        $extractedPythonDir = Join-Path $TEMP_UNZIP "pythonpackages"
        if (Test-Path $extractedPythonDir) {
            Move-Item -Path $extractedPythonDir -Destination $PYTHON_DIR
            Remove-Item -Path $TEMP_UNZIP -Recurse -Force
            Write-Status "Python environment extracted successfully" "SUCCESS"
        } else {
            throw "Invalid Python package structure in ZIP file. Expected 'pythonpackages' directory not found."
        }
    } else {
        throw "Python package file ($PYTHON_ZIP) not found. Please ensure the Python packages are available in the current directory."
    }
    
    # STEP 2: Validate Package Manager
    Write-Host ""
    Write-Host "[STEP 2/4] Validating Package Manager..." -ForegroundColor Yellow
    
    $pipResult = & $pythonExe -m pip --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Installing package manager (pip)..." "INFO"
        
        $getPipPath = Join-Path $PYTHON_DIR "get-pip.py"
        if (-not (Test-Path $getPipPath)) {
            Write-Status "Downloading pip installer..." "INFO"
            Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPipPath
        }
        
        Write-Status "Running pip installer..." "INFO"
        & $pythonExe $getPipPath --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install package manager"
        }
        Write-Status "Package manager installed successfully" "SUCCESS"
    } else {
        Write-Status "Package manager is available" "SUCCESS"
    }
    
    # STEP 3: Install Dependencies
    Write-Host ""
    Write-Host "[STEP 3/4] Installing Application Dependencies..." -ForegroundColor Yellow
    
    Write-Status "Updating package manager..." "INFO"
    & $pythonExe -m pip install --upgrade pip --quiet
    
    Write-Status "Installing core dependencies..." "INFO"
    
    $packages = @(
        "PySide6==6.6.0",
        "pretty_midi==0.2.10",
        "mido==1.3.0",
        "python-rtmidi==1.5.5",
        "pygame==2.5.2",
        "pyfluidsynth==1.3.2",
        "numpy==1.24.3",
        "scikit-learn==1.3.2",
        "matplotlib==3.8.0",
        "tqdm==4.66.1",
        "einx==0.3.0",
        "einops==0.7.0",
        "gradio_client==1.10.2",
        "requests==2.31.0"
        "psutil"
    )
    
    # Create temporary requirements file
    $tempReq = Join-Path $env:TEMP "pianoreq_$(Get-Random).txt"
    $packages | Out-File -FilePath $tempReq -Encoding UTF8
    
    # Install from requirements file
    & $pythonExe -m pip install -r $tempReq --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Status "Some packages failed to install, trying individually..." "WARNING"
        
        foreach ($package in $packages) {
            Write-Status "Installing $package individually..." "INFO"
            & $pythonExe -m pip install $package --quiet
            if ($LASTEXITCODE -ne 0) {
                Write-Status "Failed to install $package, attempting with --no-deps..." "WARNING"
                & $pythonExe -m pip install $package --no-deps --quiet
            }
        }
    }
    
    Remove-Item -Path $tempReq -Force -ErrorAction SilentlyContinue
    
    # STEP 4: Configure PyTorch
    Write-Host ""
    Write-Host "[STEP 4/4] Configuring PyTorch Framework..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please select your system configuration:" -ForegroundColor Cyan
    Write-Host "  [1] CPU-only installation (No GPU acceleration)" -ForegroundColor White
    Write-Host "  [2] GPU-enabled installation (NVIDIA CUDA support)" -ForegroundColor White
    Write-Host ""
    
    do {
        $choice = Read-Host "Enter your choice (1 or 2)"
        if ($choice -eq "1" -or $choice -eq "2") {
            break
        }
        Write-Status "Invalid selection. Please enter 1 or 2." "ERROR"
    } while ($true)
    
    if ($choice -eq "1") {
        Write-Host ""
        Write-Status "Installing PyTorch (CPU-only version)..." "INFO"
        & $pythonExe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install PyTorch CPU version"
        }
        Write-Status "PyTorch CPU version installed successfully" "SUCCESS"
    } else {
        Write-Host ""
        Write-Status "Installing PyTorch (GPU-enabled version with CUDA support)..." "INFO"
        & $pythonExe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --quiet
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install PyTorch GPU version"
        }
        Write-Status "PyTorch GPU version installed successfully" "SUCCESS"
    }
    
    # Installation Complete
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host "   Installation Completed Successfully" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your PianoRollStudio environment is now ready." -ForegroundColor Green
    Write-Host "You can launch the application using start.bat" -ForegroundColor Green
    Write-Host ""
    Write-Log ""
    Write-Log "Installation completed successfully at $(Get-Date)"

} catch {
    # Installation Failed
    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Red
    Write-Host "   Installation Failed" -ForegroundColor Red
    Write-Host "===============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Detailed log saved to: $LOG_FILE" -ForegroundColor Yellow
    Write-Host ""
    Write-Log ""
    Write-Log "Installation failed at $(Get-Date)"
    Write-Log "Error: $($_.Exception.Message)"
    
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
exit 0