from PySide6.QtGui import QColor

# Theme Colors - Dark professional theme
BG_COLOR = QColor(28, 28, 32)
GRID_COLOR = QColor(40, 40, 45, 150)  # Increased opacity for better visibility
BEAT_COLOR = QColor(60, 60, 65, 180)  # Increased opacity
MEASURE_COLOR = QColor(95, 95, 100)  # Slightly brighter
ROW_HIGHLIGHT_COLOR = QColor(45, 45, 50, 100)  # More visible
KEY_GRID_COLOR = QColor(50, 50, 55, 120)  # Increased opacity
PLAYHEAD_COLOR = QColor(255, 120, 0, 180)

# Piano key colors
WHITE_KEY_COLOR = QColor(240, 240, 240)
BLACK_KEY_COLOR = QColor(30, 30, 35)
KEY_BORDER_COLOR = QColor(100, 100, 100, 80)  # Thinner, semi-transparent

# Note colors based on velocity with better aesthetics
NOTE_COLORS = {
    'low': QColor(80, 200, 120),     # Softer green for low velocity
    'med': QColor(70, 180, 210),     # Soft blue for medium velocity
    'high': QColor(230, 120, 190)    # Purple-pink for high velocity
}
