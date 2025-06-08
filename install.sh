#!/bin/bash

# ===========================================
# 🛠️  MIDI-GEN - Installation Script (Unix)
# ===========================================

echo "🔄 Checking for Python 3.10 environment..."

PYTHON_DIR="pythonpackages"
VENV_ACTIVE=0
REQUIRED_PYTHON_VERSION="3.10"

# Function to check Python version (checks for any 3.10.x version)
check_python_version() {
    local python_cmd=$1
    local version_output=$($python_cmd --version 2>&1)
    
    # Check for Python 3.10.x (any minor version)
    if [[ $version_output =~ Python\ 3\.10\.[0-9]+ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to install Python 3.10
install_python310() {
    echo "⏳ Python 3.10 not found. Attempting to install..."
    
    # Detect OS
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        if command -v brew &>/dev/null; then
            echo "🍎 Installing Python 3.10 via Homebrew..."
            brew install python@3.10
            if [ $? -eq 0 ]; then
                echo "✅ Python 3.10 installed successfully via Homebrew"
                return 0
            fi
        else
            echo "❌ Homebrew not found. Please install Homebrew first or manually install Python 3.10"
            echo "Visit https://brew.sh for Homebrew installation"
            exit 1
        fi
    elif [[ "$(uname)" == "Linux" ]]; then
        # Linux
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
            
            if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO" == "pop" || "$DISTRO" == "mint" ]]; then
                echo "🐧 Installing Python 3.10 on $DISTRO..."
                if command -v sudo &>/dev/null; then
                    sudo apt-get update
                    sudo apt-get install -y software-properties-common
                    sudo add-apt-repository -y ppa:deadsnakes/ppa
                    sudo apt-get update
                    sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
                    if [ $? -eq 0 ]; then
                        echo "✅ Python 3.10 installed successfully"
                        return 0
                    fi
                else
                    echo "❌ No sudo access. Please install Python 3.10 manually"
                    exit 1
                fi
            elif [[ "$DISTRO" == "fedora" || "$DISTRO" == "rhel" || "$DISTRO" == "centos" ]]; then
                echo "🐧 Installing Python 3.10 on $DISTRO..."
                if command -v sudo &>/dev/null; then
                    sudo dnf install -y python3.10 python3.10-devel
                    if [ $? -eq 0 ]; then
                        echo "✅ Python 3.10 installed successfully"
                        return 0
                    fi
                else
                    echo "❌ No sudo access. Please install Python 3.10 manually"
                    exit 1
                fi
            elif [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" ]]; then
                echo "🐧 Installing Python 3.10 on $DISTRO..."
                if command -v sudo &>/dev/null; then
                    sudo pacman -Sy python310
                    if [ $? -eq 0 ]; then
                        echo "✅ Python 3.10 installed successfully"
                        return 0
                    fi
                else
                    echo "❌ No sudo access. Please install Python 3.10 manually"
                    exit 1
                fi
            fi
        fi
    fi
    
    echo "❌ Could not install Python 3.10 automatically"
    echo "Please install Python 3.10 manually and try again"
    exit 1
}

# Check if we're in a virtual environment with Python 3.10
if [ -n "$VIRTUAL_ENV" ]; then
    if check_python_version "python"; then
        echo "✅ Using active virtual environment with Python 3.10: $VIRTUAL_ENV"
        VENV_ACTIVE=1
    else
        echo "⚠️ Active virtual environment doesn't have Python 3.10"
        echo "Creating new Python 3.10 environment..."
    fi
elif [ -d "$PYTHON_DIR" ] && [ -f "$PYTHON_DIR/bin/python" ]; then
    if check_python_version "$PYTHON_DIR/bin/python"; then
        echo "✅ Found local Python 3.10 environment"
        source "$PYTHON_DIR/bin/activate"
        VENV_ACTIVE=1
    else
        echo "⚠️ Local Python environment doesn't have Python 3.10"
        echo "Recreating environment with Python 3.10..."
        rm -rf "$PYTHON_DIR"
    fi
fi

if [ $VENV_ACTIVE -eq 0 ]; then
    # Find Python 3.10 before attempting to install
    PYTHON_CMD=""
    
    echo "🔍 Searching for existing Python 3.10 installation..."
    
    # Try different Python 3.10 commands in order of preference
    for cmd in python3.10 python310 python3 python; do
        if command -v $cmd &>/dev/null; then
            echo "🔍 Checking $cmd..."
            if check_python_version $cmd; then
                PYTHON_CMD=$cmd
                echo "✅ Found existing Python 3.10: $PYTHON_CMD"
                break
            else
                # Show what version was found for debugging
                version_output=$($cmd --version 2>&1)
                echo "⚠️ $cmd is $version_output (not Python 3.10.x)"
            fi
        fi
    done
    
    # Only attempt to install if no Python 3.10 was found
    if [ -z "$PYTHON_CMD" ]; then
        echo "❌ No Python 3.10.x installation found on system"
        install_python310
        
        echo "🔍 Re-scanning for Python 3.10 after installation..."
        # Try to find Python 3.10 again after installation
        for cmd in python3.10 python310 python3 python; do
            if command -v $cmd &>/dev/null; then
                if check_python_version $cmd; then
                    PYTHON_CMD=$cmd
                    echo "✅ Found Python 3.10 after installation: $PYTHON_CMD"
                    break
                fi
            fi
        done
        
        if [ -z "$PYTHON_CMD" ]; then
            echo "❌ Python 3.10 installation failed or not accessible"
            echo "Please verify Python 3.10 is installed and accessible via command line"
            exit 1
        fi
    else
        echo "✅ Using existing Python 3.10 installation, skipping download"
    fi

    echo "⏳ Creating local Python 3.10 environment in $PYTHON_DIR..."
    $PYTHON_CMD -m venv "$PYTHON_DIR"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create Python virtual environment."
        echo "Please make sure python3.10-venv is installed."
        echo "On Ubuntu/Debian: sudo apt-get install python3.10-venv"
        exit 1
    fi
    
    source "$PYTHON_DIR/bin/activate"
    VENV_ACTIVE=1
    
    # Verify the environment has Python 3.10
    if ! check_python_version "python"; then
        echo "❌ Created environment doesn't have Python 3.10"
        exit 1
    fi
    
    echo "✅ Python 3.10 virtual environment created and activated"
fi

# Check if pip is available
if ! command -v pip &>/dev/null; then
    echo "⚠️ pip is not available. Attempting to install..."
    
    # Download get-pip.py
    if command -v curl &>/dev/null; then
        curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py
    elif command -v wget &>/dev/null; then
        wget https://bootstrap.pypa.io/get-pip.py
    else
        echo "❌ Neither curl nor wget is available to download pip."
        echo "Please install either curl or wget and try again."
        exit 1
    fi
    
    # Install pip
    python get-pip.py
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install pip. Cannot continue."
        exit 1
    fi
    
    echo "✅ pip installed successfully!"
    rm get-pip.py
fi

echo "🔄 Updating pip..."
pip install --upgrade pip

if [ $? -ne 0 ]; then
    echo "⚠️ Failed to update pip, trying to continue anyway..."
fi

echo "📦 Installing requirements from requirements.txt..."

# Check if we're on macOS
if [[ "$(uname)" == "Darwin" ]]; then
    echo "🍎 Detected macOS system"
    
    # Check if FluidSynth is installed via homebrew
    if ! command -v brew &>/dev/null; then
        echo "⚠️ Homebrew not found. We recommend installing it for FluidSynth support."
        echo "Visit https://brew.sh for installation instructions."
    elif ! brew list fluidsynth &>/dev/null; then
        echo "⚠️ FluidSynth not found. Installing via Homebrew..."
        brew install fluidsynth
    else
        echo "✅ FluidSynth already installed"
    fi
fi

# Check if we're on Linux
if [[ "$(uname)" == "Linux" ]]; then
    echo "🐧 Detected Linux system"
    
    # Detect distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        
        # Install system dependencies for common distributions
        if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO" == "pop" || "$DISTRO" == "mint" ]]; then
            echo "🔍 Detected $DISTRO distribution"
            echo "⚠️ Some packages may require system libraries. Checking..."
            
            # Check if we have sudo access
            if command -v sudo &>/dev/null; then
                echo "📦 Installing required system packages for audio/MIDI support..."
                sudo apt-get update
                sudo apt-get install -y fluidsynth libasound2-dev libjack-dev libportmidi-dev
            else
                echo "⚠️ No sudo access. You may need to manually install: fluidsynth, libasound2-dev, libjack-dev, libportmidi-dev"
            fi
        elif [[ "$DISTRO" == "fedora" || "$DISTRO" == "rhel" || "$DISTRO" == "centos" ]]; then
            if command -v sudo &>/dev/null; then
                echo "📦 Installing required system packages for audio/MIDI support..."
                sudo dnf install -y fluidsynth fluidsynth-devel alsa-lib-devel jack-audio-connection-kit-devel portmidi-devel
            else
                echo "⚠️ No sudo access. You may need to manually install: fluidsynth, fluidsynth-devel, alsa-lib-devel, jack-audio-connection-kit-devel, portmidi-devel"
            fi
        elif [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" ]]; then
            if command -v sudo &>/dev/null; then
                echo "📦 Installing required system packages for audio/MIDI support..."
                sudo pacman -Sy fluidsynth alsa-lib jack portmidi
            else
                echo "⚠️ No sudo access. You may need to manually install: fluidsynth, alsa-lib, jack, portmidi"
            fi
        else
            echo "⚠️ Unsupported Linux distribution. You may need to manually install FluidSynth and MIDI libraries."
        fi
    else
        echo "⚠️ Cannot determine Linux distribution. You may need to manually install FluidSynth and MIDI libraries."
    fi
fi

# Install Python packages directly (excluding PyTorch)
echo "📦 Installing Python packages (excluding PyTorch)..."

# GUI Framework
echo "🖼️ Installing GUI framework..."
pip install PySide6==6.6.0
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install PySide6. You may need to install it manually."
fi

# MIDI Processing
echo "🎵 Installing MIDI processing packages..."
pip install pretty_midi==0.2.10
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install pretty_midi. You may need to install it manually."
fi

pip install mido==1.3.0
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install mido. You may need to install it manually."
fi

pip install python-rtmidi==1.5.8 --no-build-isolation
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install python-rtmidi. You may need to install it manually."
fi

# Audio and MIDI Playback
echo "🔊 Installing audio packages..."
pip install pygame==2.5.2
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install pygame. You may need to install it manually."
fi

pip install pyfluidsynth==1.3.2
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install pyfluidsynth. You may need to install system fluidsynth library first."
fi

# Numerical and Scientific Computing
echo "🔢 Installing numerical and scientific computing packages..."
pip install numpy==1.24.3
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install numpy. You may need to install it manually."
fi

pip install scikit-learn==1.3.2
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install scikit-learn. You may need to install it manually."
fi

pip install matplotlib==3.8.0
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install matplotlib. You may need to install it manually."
fi

pip install tqdm==4.66.1
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install tqdm. You may need to install it manually."
fi

pip install einx==0.3.0
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install einx. You may need to install it manually."
fi

pip install einops==0.7.0
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install einops. You may need to install it manually."
fi

pip install psutil
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install psutil. You may need to install it manually."
fi

# API and Web Integration
echo "🌐 Installing API and web integration packages..."
pip install gradio_client==1.10.2
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install gradio_client. You may need to install it manually."
fi

pip install requests==2.31.0
if [ $? -ne 0 ]; then
    echo "⚠️ Could not install requests. You may need to install it manually."
fi

echo "✅ Python packages installation completed!"

# Copy custom modules to site-packages
echo "📁 Copying custom modules to site-packages..."

# Find site-packages directory
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")

if [ -z "$SITE_PACKAGES" ]; then
    echo "❌ Could not find site-packages directory"
    exit 1
fi

echo "📍 Found site-packages at: $SITE_PACKAGES"

# Check if ai_studio/modules directory exists
if [ ! -d "ai_studio/modules" ]; then
    echo "❌ ai_studio/modules directory not found"
    echo "Please make sure you're running this script from the project root"
    exit 1
fi

# Copy Python files from ai_studio/modules to site-packages
echo "📋 Copying modules from ai_studio/modules to site-packages..."

for file in ai_studio/modules/*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        echo "  📄 Copying $filename..."
        cp "$file" "$SITE_PACKAGES/"
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Successfully copied $filename"
        else
            echo "  ❌ Failed to copy $filename"
            exit 1
        fi
    fi
done

echo "✅ All custom modules copied successfully!"

echo
echo "🧠 Skipping PyTorch in requirements.txt — will install manually after user selects version."
echo

# Select PyTorch Version (only for Linux users)
if [[ "$(uname)" == "Linux" ]]; then
    echo "🧠 Choose which version of PyTorch to install:"
    echo "[1] CPU-only (no NVIDIA GPU)"
    echo "[2] CUDA (GPU) version (auto-detects)"
    read -p "Enter choice [1 or 2]: " TORCH_CHOICE

    if [ "$TORCH_CHOICE" == "1" ]; then
        echo "⏳ Installing PyTorch CPU-only version..."
        pip install torch --index-url https://download.pytorch.org/whl/cpu
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install CPU PyTorch. Exiting."
            exit 1
        fi
        
        echo "✅ PyTorch CPU-only version installed!"
    elif [ "$TORCH_CHOICE" == "2" ]; then
        echo "⏳ Installing PyTorch with CUDA support (will auto-detect appropriate version)..."
        pip install torch
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install GPU PyTorch. Exiting."
            exit 1
        fi
        
        echo "✅ PyTorch GPU version installed!"
    else
        echo "❌ Invalid input. Please choose 1 or 2."
        exit 1
    fi
elif [[ "$(uname)" == "Darwin" ]]; then
    # macOS - install CPU version by default
    echo "🍎 Installing PyTorch CPU version for macOS..."
    pip install torch
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install PyTorch. Exiting."
        exit 1
    fi
    
    echo "✅ PyTorch installed for macOS!"
fi

echo
echo "✅ Installation completed successfully!"
echo "🎉 Thanks for installing MIDI-GEN!"
echo
echo "If you enjoy our project, please consider giving us a ⭐ on GitHub!"
echo
echo "To start the project, please run: ./start.sh"
echo

# Make sure the start script is executable
if [ -f "start.sh" ]; then
    chmod +x start.sh
    echo "✅ Made start.sh executable"
else
    echo "⚠️ start.sh not found in current directory"
fi
