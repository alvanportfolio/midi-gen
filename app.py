import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import PianoRollMainWindow
from config import theme # Import theme for APP_ICON_PATH
import os # os is still needed for os.path.exists if we keep the check
import pretty_midi
# utils.get_resource_path is not directly needed here if theme.APP_ICON_PATH uses it

def main():
    app = QApplication(sys.argv)
    
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
