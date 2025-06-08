import sys
import os
import time

# ===== AUDIO INITIALIZATION FIX =====
# Configure SDL audio driver before any audio-related imports to prevent startup ticks/pops
os.environ["SDL_AUDIODRIVER"] = "directsound"  # Use directsound for Windows

def setup_embedded_python_environment():
    """Setup the embedded Python environment for standalone exe"""
    
    # Get the directory where the executable/script is located
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller executable
        app_dir = os.path.dirname(sys.executable)
        print(f"🔍 Running as standalone executable from: {app_dir}")
    else:
        # Running in development mode
        app_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"🔍 Running in development mode from: {app_dir}")
    
    # Path to embedded Python environment
    embedded_python_dir = os.path.join(app_dir, "pythonpackages")
    embedded_site_packages = os.path.join(embedded_python_dir, "Lib", "site-packages")
    embedded_lib = os.path.join(embedded_python_dir, "Lib")
    
    if os.path.exists(embedded_python_dir):
        print(f"✅ Found embedded Python environment: {embedded_python_dir}")
        
        # CRITICAL: Add embedded Python paths at the VERY BEGINNING of sys.path
        # This ensures embedded modules are found BEFORE any bundled modules
        paths_to_add = [
            embedded_site_packages,  # FIRST: Installed packages (numpy, torch, TMIDIX, etc.)
            embedded_lib,             # SECOND: Standard library extensions
            app_dir,                  # THIRD: Project root for local modules (ui, config, etc.)
        ]
        
        # Remove any existing instances of these paths first
        for path in paths_to_add:
            while path in sys.path:
                sys.path.remove(path)
        
        # Add paths at the beginning in reverse order (so first added ends up first)
        for path in reversed(paths_to_add):
            if os.path.exists(path):
                sys.path.insert(0, path)
                print(f"➕ Added to Python path (priority): {path}")
        
        # Verify critical modules can be found
        print("🧪 Verifying embedded Python modules...")
        try:
            import numpy
            print(f"✅ numpy found at: {numpy.__file__}")
        except ImportError as e:
            print(f"❌ numpy not found: {e}")
            
        try:
            import torch
            print(f"✅ torch found at: {torch.__file__}")
        except ImportError as e:
            print(f"❌ torch not found: {e}")
            
        print("✅ Embedded Python environment configured successfully")
        return True
    else:
        print(f"⚠️ Embedded Python environment not found at: {embedded_python_dir}")
        print("   The application will use the system Python environment")
        return False

# Setup embedded Python environment first (before any other imports)
setup_embedded_python_environment()

# ===== PYGAME AUDIO PRE-INITIALIZATION =====
# Initialize pygame mixer with proper settings before any MIDI/audio modules are imported
try:
    import pygame
    # Pre-initialize mixer with optimal settings to prevent audio pops
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()
    print("✅ Pygame audio pre-initialized successfully")
    
    # Small delay to let audio device settle
    time.sleep(0.1)
    
except ImportError:
    print("⚠️ Pygame not available - MIDI functionality may be limited")
except Exception as e:
    print(f"⚠️ Error during pygame audio initialization: {e}")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import PianoRollMainWindow
from config import theme # Import theme for APP_ICON_PATH
import pretty_midi
from utils import ensure_ai_dependencies  # Import AI dependency setup

def create_required_directories():
    """Create required external directories for plugins and AI studio"""
    try:
        # Get the directory where the executable/script is located
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running in development mode
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create plugins directory
        plugins_dir = os.path.join(base_dir, "plugins")
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)
            print(f"✅ Created plugins directory: {plugins_dir}")
        
        # Create ai_studio directory structure (for model files)
        ai_studio_dir = os.path.join(base_dir, "ai_studio")
        models_dir = os.path.join(ai_studio_dir, "models")
        
        for directory in [ai_studio_dir, models_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"✅ Created directory: {directory}")
        
        # Create placeholder files with instructions
        readme_plugins = os.path.join(plugins_dir, "README.txt")
        if not os.path.exists(readme_plugins):
            with open(readme_plugins, 'w') as f:
                f.write("Piano Roll Studio - Plugins Directory\n")
                f.write("=====================================\n\n")
                f.write("Place your .py plugin files in this directory.\n")
                f.write("The application will automatically discover and load them.\n\n")
                f.write("You can also install additional Python packages:\n")
                f.write("1. Run 'manage_python.bat' (if using portable version)\n")
                f.write("2. Or use: pythonpackages\\python.exe -m pip install package_name\n\n")
                f.write("The app will automatically use packages from the embedded Python environment.\n")
        
        readme_models = os.path.join(models_dir, "README.txt")
        if not os.path.exists(readme_models):
            with open(readme_models, 'w') as f:
                f.write("Piano Roll Studio - AI Models Directory\n")
                f.write("======================================\n\n")
                f.write("Place your AI model files in this directory.\n\n")
                f.write("Required files:\n")
                f.write("- alex_melody.pth (main AI melody model)\n\n")
                f.write("The AI Studio will look for models in this directory.\n")
        
        # Check if embedded Python environment exists
        embedded_python_dir = os.path.join(base_dir, "pythonpackages")
        if os.path.exists(embedded_python_dir):
            print(f"✅ Embedded Python environment found: {embedded_python_dir}")
        else:
            print(f"⚠️ Embedded Python environment not found. For full functionality, ensure 'pythonpackages' folder is present.")
        
        print(f"📁 All required directories created successfully!")
        return True
        
    except Exception as e:
        print(f"⚠️ Error creating directories: {e}")
        return False

def main():
    app = QApplication(sys.argv)
    
    # Setup AI dependencies FIRST (before any imports that need them)
    print("🧠 Setting up AI dependencies...")
    ai_setup_success = ensure_ai_dependencies()
    if ai_setup_success:
        print("✅ AI dependency setup completed successfully")
    else:
        print("⚠️ AI dependency setup failed - some AI features may not work")
    
    # Create required external directories
    create_required_directories()
    
    # Set application icon using the path from theme.py
    # theme.APP_ICON_PATH is already an absolute path resolved by get_resource_path
    if os.path.exists(theme.APP_ICON_PATH):
        app.setWindowIcon(QIcon(theme.APP_ICON_PATH))
    else:
        print(f"Warning: Application icon not found at {theme.APP_ICON_PATH}")

    # app.setStyle('Fusion') # Commented out to allow custom QSS to take full effect

    # Optional: Load initial MIDI data if a file is specified via an environment variable or argument
    # For simplicity, this example does not load initial data by default.
    # You could add logic here to load from a default file or command-line argument.
    # initial_midi_file = os.environ.get("INITIAL_MIDI_FILE") 
    # notes_to_load = []
    # if initial_midi_file and os.path.exists(initial_midi_file):
    #     try:
    #         midi_data = pretty_midi.PrettyMIDI(initial_midi_file)
    #         for instrument in midi_data.instruments:
    #             if not instrument.is_drum:
    #                 notes_to_load.extend(instrument.notes)
    #         print(f"Loaded {len(notes_to_load)} notes from {initial_midi_file}")
    #     except Exception as e:
    #         print(f"Error loading initial MIDI file {initial_midi_file}: {e}")
    # else:
    #     print("No initial MIDI file specified or found, starting empty.")
        
    # window = PianoRollMainWindow(notes_to_load)
    window = PianoRollMainWindow() # Start with an empty piano roll
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
