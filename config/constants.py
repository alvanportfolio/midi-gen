# Constants for piano roll display
MIN_PITCH = 21  # A0
MAX_PITCH = 108  # C8
WHITE_KEY_WIDTH = 60
BLACK_KEY_WIDTH = 40
WHITE_KEY_HEIGHT = 24
BLACK_KEY_HEIGHT = 16
BASE_TIME_SCALE = 100  # Base pixels per second (at 120 BPM)
DEFAULT_BPM = 120

# Constants for note labels
MIN_LABEL_PITCH = 36  # C2 MIDI note number (will be displayed as C3)
MAX_LABEL_PITCH = 96  # C7 MIDI note number (will be displayed as C8)

# MIDI Program Change Constants
DEFAULT_MIDI_PROGRAM = 0  # Acoustic Grand Piano (EZ Pluck)
DEFAULT_MIDI_CHANNEL = 0  # Default MIDI channel for playback

INSTRUMENT_PRESETS = {
    "EZ Pluck": 0,        # Acoustic Grand Piano
    "Synth Lead": 80,     # Lead 1 (Square)
    "Warm Pad": 89,       # Pad 2 (Warm)
    "Classic Piano": 1    # Bright Acoustic Piano
}

# Default instrument name for UI
DEFAULT_INSTRUMENT_NAME = "EZ Pluck"
