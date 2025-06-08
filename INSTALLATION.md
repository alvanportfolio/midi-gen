# 🚀 Installation Guide - MIDI Generator Piano Roll

This guide provides comprehensive installation instructions for all platforms and deployment methods.

## 📋 Table of Contents

- [Windows Portable Version (Recommended)](#-windows-portable-version-recommended)
- [Source Installation (All Platforms)](#-source-installation-all-platforms)
- [Manual Installation](#-manual-installation)
- [Troubleshooting](#-troubleshooting)

---

## 🪟 Windows Portable Version (Recommended)

### Step 1: Download Portable Package
1. Visit the [Releases](https://github.com/WebChatAppAi/midi-gen/releases) page
2. Download the latest Windows portable ZIP package
3. Extract the ZIP to your desired location

### Step 2: Verify Package Contents
After extraction, you should see:
```
midi-gen-portable/
├── ai_studio/
├── fluidsynth/
├── plugins/
├── pythonpackages/
├── install.bat
├── MidiGenV2.exe
└── IMPORTANT.txt
```

### Step 3: Setup FluidSynth
1. **Create the tools directory:**
   ```
   C:\tools\
   ```
2. **Move FluidSynth:**
   - Copy the `fluidsynth` folder from the extracted package
   - Paste it into `C:\tools\`
   - Final path should be: `C:\tools\fluidsynth\`

### Step 4: Install PyTorch Dependencies
1. **Double-click `install.bat`**
2. **Choose PyTorch version when prompted:**
   - **Option 1 (CPU)**: For systems without NVIDIA GPU
   - **Option 2 (CUDA/GPU)**: For systems with compatible NVIDIA GPU
3. **Wait for installation to complete**

### Step 5: Launch Application
- **Option**: Double-click `MidiGenV2.exe`

### Additional Notes
- Check `IMPORTANT.txt` for additional details and troubleshooting
- First launch may take longer as AI models initialize

---

## 🛠️ Source Installation (All Platforms)

### Prerequisites
- Python 3.10 or higher
- Git
- Internet connection for dependency downloads

### Step 1: Clone Repository
```bash
git clone https://github.com/WebChatAppAi/midi-gen.git
cd midi-gen
```

### Step 2: Download AI Models (Optional)
```bash
# Windows
model_download.bat

# Linux/macOS
chmod +x model_download.sh
./model_download.sh
```

### Step 3: Platform-Specific Installation

#### 🪟 Windows Source Installation

1. **Extract Python Environment:**
   - Extract `pythonpackages.zip` to project root
   - This creates the `pythonpackages/` directory

2. **Run Automated Installation:**
   ```cmd
   install.bat
   ```
   - This calls CMD → PowerShell → completes installation
   - Choose CPU or CUDA PyTorch when prompted

3. **Setup FluidSynth:**
   - Download FluidSynth from the original repo or extract `fluidsynth.zip`
   - Place in `C:\tools\fluidsynth\`

4. **Setup AI Models:**
   - Place downloaded AI models in `ai_studio\models\`

5. **Launch Application:**
   ```cmd
   start.bat
   # OR
   pythonpackages\python.exe app.py
   ```

#### 🐧 Linux Source Installation

1. **Run Automated Installation:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

2. **Verify FluidSynth:**
   ```bash
   # Install FluidSynth if not available
   # Ubuntu/Debian:
   sudo apt-get install fluidsynth libasound2-dev libjack-dev libportmidi-dev
   
   # Fedora/RHEL:
   sudo dnf install fluidsynth fluidsynth-devel alsa-lib-devel jack-audio-connection-kit-devel portmidi-devel
   
   # Arch/Manjaro:
   sudo pacman -Sy fluidsynth alsa-lib jack portmidi
   ```

3. **Launch Application:**
   ```bash
   ./start.sh
   # OR
   pythonpackages/bin/python app.py
   ```

#### 🍎 macOS Source Installation

1. **Install Homebrew (if not installed):**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Run Automated Installation:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Install FluidSynth:**
   ```bash
   brew install fluidsynth
   ```

4. **Launch Application:**
   ```bash
   chmod +x start.sh
   ./start.sh
   # OR
   pythonpackages/bin/python app.py
   ```

**Important Notes for Linux/macOS:**
- Create virtual environment named exactly `pythonpackages`
- Do NOT extract `pythonpackages.zip` (Windows-only)
- All dependencies installed via `install.sh`

---

## ⚙️ Manual Installation

### When to Use Manual Installation
- Automated `install.sh` fails
- Custom Python setup required
- Troubleshooting dependency issues

### Manual Steps

1. **Create Virtual Environment:**
   ```bash
   python3.10 -m venv pythonpackages
   ```

2. **Activate Environment:**
   ```bash
   # Linux/macOS:
   source pythonpackages/bin/activate
   
   # Windows:
   pythonpackages\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup AI Studio Modules:**
   - Locate the 2 Python files in `ai_studio\modules\`
   - Copy them to your environment's site-packages:
   
   ```bash
   # Target location:
   pythonpackages/
   ├── bin/                    # Linux/macOS
   ├── Scripts/               # Windows  
   ├── include/
   ├── lib/
   │   └── python3.10/
   │       └── site-packages/ # <- Place the 2 files here
   ```

5. **Launch Application:**
   ```bash
   python app.py
   ```

---

## 🔧 Troubleshooting

### Common Issues

#### FluidSynth Not Found
**Windows:**
- Ensure FluidSynth is at `C:\tools\fluidsynth\`
- Download from releases or extract provided `fluidsynth.zip`

**Linux/macOS:**
- Install via package manager (see installation steps above)
- Verify installation: `fluidsynth --version`

#### Python Environment Issues
- Ensure virtual environment is named exactly `pythonpackages`
- Use Python 3.10 for best compatibility
- Check that all requirements are installed: `pip list`

#### PyTorch Installation Fails
- Check internet connection
- For Windows: try both CPU and CUDA options
- Manual installation: `pip install torch torchvision torchaudio`

#### Permission Errors
**Windows:**
- Run Command Prompt as Administrator
- Check antivirus isn't blocking files

**Linux/macOS:**
- Use `sudo` for system package installations
- Ensure execute permissions: `chmod +x install.sh start.sh`

#### AI Models Not Loading
- Verify models are in `ai_studio\models\`
- Check file permissions
- Ensure sufficient disk space

### Getting Help

1. **Check `IMPORTANT.txt`** (portable version)
2. **Review GitHub Issues**: [Issues Page](https://github.com/WebChatAppAi/midi-gen/issues)
3. **Join Discussions**: [GitHub Discussions](https://github.com/WebChatAppAi/midi-gen/discussions)

---

## 📁 Project Structure Reference

```
midi-gen/
├── ai_studio/
│   ├── models/              # AI models location
│   └── modules/            # Contains 2 Python files for manual installation
├── fluidsynth/             # FluidSynth binaries (Windows portable)
├── plugins/                # Plugin system files
├── pythonpackages/         # Virtual environment
│   ├── bin/               # Python executable (Linux/macOS)
│   ├── Scripts/           # Python executable (Windows)
│   └── lib/python3.10/site-packages/  # Python packages
├── docs/                   # Documentation
├── app.py                  # Main application
├── requirements.txt        # Python dependencies
├── install.bat            # Windows installer
├── install.sh             # Linux/macOS installer
├── start.bat              # Windows launcher
├── start.sh               # Linux/macOS launcher
└── IMPORTANT.txt          # Additional notes (portable version)
```

---

*🎵 Ready to create amazing music with AI-powered MIDI generation!*