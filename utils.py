import os
import sys

def get_resource_path(relative_path: str, app_is_frozen: bool = hasattr(sys, 'frozen'), is_external_to_bundle: bool = False) -> str:
    """
    Get the absolute path to a resource.
    - In a PyInstaller bundle:
        - If is_external_to_bundle is True (e.g., for a 'plugins' folder next to the .exe):
          Uses the directory of the executable (sys.executable).
        - Otherwise (e.g., for bundled 'assets', 'soundbank' in _MEIPASS):
          Uses PyInstaller's temporary folder (sys._MEIPASS).
    - In development mode (not bundled):
      Uses paths relative to this script's directory (utils.py, assumed to be project root).
    """
    if app_is_frozen: # Running as a PyInstaller bundle
        if is_external_to_bundle:
            # Path relative to the executable (e.g., for a 'plugins' folder)
            base_path = os.path.dirname(sys.executable)
        else:
            # Path within the PyInstaller bundle (e.g., for 'assets', 'soundbank')
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                # Fallback if _MEIPASS is not set for some reason, though it should be for frozen apps.
                # This might happen in some PyInstaller configurations or if not truly frozen.
                print("Warning: sys._MEIPASS not found in frozen app, falling back to executable directory for bundled resource.")
                base_path = os.path.dirname(sys.executable)
    else:
        # Development mode: utils.py is at the project root.
        # Paths are relative to the project root.
        base_path = os.path.abspath(os.path.dirname(__file__)) 
        
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    # Example usage (assuming this file is in the project root)
    # Test with paths relative to where this script is located if not bundled.
    # If bundled, _MEIPASS would be the extraction directory.

    # To test this properly, you'd call it from other modules after import.
    # For example, from another file:
    # from utils import get_resource_path
    # icon_path = get_resource_path("assets/icons/app_icon.png")
    # print(f"Calculated app_icon.png path: {icon_path}")

    # plugins_dir = get_resource_path("plugins")
    # print(f"Calculated plugins directory: {plugins_dir}")

    # soundfont_file = get_resource_path("soundbank/soundfont.sf2")
    # print(f"Calculated soundfont.sf2 path: {soundfont_file}")
    
    # This basic test assumes utils.py is at the project root.
    # If utils.py is in a subdirectory (e.g., 'src/utils.py'), then
    # base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # might be needed for development mode to point to project root.
    # However, the provided structure has utils.py at the root.

    print(f"Testing get_resource_path from utils.py itself:")
    print(f"  For 'assets/icons/app_icon.png': {get_resource_path('assets/icons/app_icon.png')}")
    print(f"  For 'soundbank/soundfont.sf2': {get_resource_path('soundbank/soundfont.sf2')}")
    print(f"  For 'plugins': {get_resource_path('plugins')}")
    print(f"  Current sys._MEIPASS (if any): {getattr(sys, '_MEIPASS', 'Not set (running as .py)')}")
