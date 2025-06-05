from PySide6.QtGui import QColor

# =============================================================================
# --- Color Palette ---
# =============================================================================

# --- Primary Backgrounds ---
# Used for main application areas, panels, and dialogs.
APP_BG_COLOR = QColor(26, 26, 26)          # #1A1A1A - Main application background
PANEL_BG_COLOR = QColor(34, 34, 34)        # #222222 - Side panels, toolbars
DIALOG_BG_COLOR = QColor(42, 42, 42)       # #2A2A2A - Dialog windows, pop-ups
PIANO_ROLL_BG_COLOR = QColor(24, 24, 28)   # #18181C - Specific for the piano roll area

# --- Secondary Backgrounds / Accents (for UI elements) ---
# Used for interactive elements like inputs, list items.
INPUT_BG_COLOR = QColor(46, 46, 46)        # #2E2E2E - Background for text inputs, combo boxes
ITEM_BG_COLOR = QColor(44, 44, 44)         # #2C2C2C - Background for list items, tree items
ITEM_HOVER_BG_COLOR = QColor(56, 56, 56)   # #383838 - Hover state for list items
ITEM_SELECTED_BG_COLOR = QColor(0, 122, 204) # #007ACC - Background for selected items (using ACCENT_PRIMARY_COLOR)
DRAG_OVERLAY_COLOR = QColor(0, 122, 204, 30) # #007ACC with low alpha - For drag-and-drop feedback

# --- Text Colors ---
PRIMARY_TEXT_COLOR = QColor(224, 224, 224)    # #E0E0E0 - General text
SECONDARY_TEXT_COLOR = QColor(160, 160, 160)  # #A0A0A0 - Less important text, hints
ACCENT_TEXT_COLOR = QColor(255, 255, 255)     # #FFFFFF - Text on accent-colored backgrounds
PLACEHOLDER_TEXT_COLOR = QColor(120, 120, 120) # #787878 - Placeholder text in inputs
DISABLED_TEXT_COLOR = QColor(100, 100, 100)   # #646464 - For foreground elements like text on disabled controls
NOTE_LABEL_COLOR = QColor(255, 255, 255, 200) # Semi-transparent white for note labels

# --- Accent & State Colors ---
# Primary brand/action colors and their states.
ACCENT_PRIMARY_COLOR = QColor(0, 122, 204)   # #007ACC - Main accent color
ACCENT_HOVER_COLOR = QColor(20, 142, 224)    # #148EE0 - Hover state for accent elements (lighter)
ACCENT_PRESSED_COLOR = QColor(0, 102, 184)   # #0066B8 - Pressed state for accent elements (darker)

DISABLED_BG_COLOR = QColor(50, 50, 50)       # #323232 - Background for disabled controls

# Standard Button Colors (for non-accented buttons)
STANDARD_BUTTON_BG_COLOR = QColor(45, 45, 50)
STANDARD_BUTTON_HOVER_BG_COLOR = QColor(60, 60, 65)
STANDARD_BUTTON_PRESSED_BG_COLOR = QColor(35, 35, 40)
STANDARD_BUTTON_TEXT_COLOR = PRIMARY_TEXT_COLOR

# --- Borders & Lines ---
BORDER_COLOR_NORMAL = QColor(58, 58, 58)      # #3A3A3A - Default border for inputs, containers
BORDER_COLOR_FOCUSED = ACCENT_PRIMARY_COLOR   # Use accent color for focused input borders
BORDER_COLOR_HOVER = QColor(85, 85, 85)       # #555555 - Border color on hover for interactive elements

# Grid Lines (Piano Roll)
GRID_LINE_COLOR = QColor(40, 40, 45, 150)                # #3C3C3C
GRID_BEAT_LINE_COLOR = QColor(60, 60, 65, 180)           # #505050
GRID_MEASURE_LINE_COLOR = QColor(95, 95, 100)            # #6E6E6E
GRID_ROW_HIGHLIGHT_COLOR = QColor(PANEL_BG_COLOR.lighter(105).rgb() & 0xFFFFFF | (50 << 24)) # Panel BG lighter with low alpha
KEY_GRID_LINE_COLOR = GRID_LINE_COLOR.darker(110)        # Subtler than main grid lines

# --- Shadows ---
# Define color, actual implementation via QSS or QGraphicsDropShadowEffect.
SHADOW_COLOR = QColor(0, 0, 0, 70)                       # #000000 with alpha - For subtle depth

# --- Piano Roll Specific Colors ---
PLAYHEAD_COLOR = QColor(70, 130, 180)                    # #4682B4 - Cool Blue
PLAYHEAD_TRIANGLE_COLOR = QColor(100, 160, 210)           # #64A0D2 - Lighter Cool Blue
PLAYHEAD_SHADOW_COLOR = QColor(0, 0, 0, 70)                # #000000 with alpha - For playerhead shadow
PIANO_KEY_SEPARATOR_COLOR = BORDER_COLOR_NORMAL          # Consistent with other borders

# Piano Key Colors
WHITE_KEY_COLOR = QColor(240, 240, 240)                  # #F0F0F0
BLACK_KEY_COLOR = QColor(30, 30, 35)                     # #1E1E23
KEY_BORDER_COLOR = QColor(100, 100, 100, 60)             # Slightly reduced alpha for subtlety
PIANO_KEY_LABEL_COLOR = QColor(40, 40, 40)                 # Darker, more visible text on white keys
PIANO_KEY_BLACK_LABEL_COLOR = QColor(240, 240, 240)      # Brighter white text on black keys

# Add aliases for WHITE_KEY_COLOR and BLACK_KEY_COLOR to maintain compatibility
PIANO_KEY_WHITE_COLOR = WHITE_KEY_COLOR
PIANO_KEY_BLACK_COLOR = BLACK_KEY_COLOR
PIANO_KEY_BORDER_COLOR = KEY_BORDER_COLOR

# Note Colors
NOTE_LOW_COLOR = QColor(80, 200, 120)                    # #50C878
NOTE_MED_COLOR = QColor(70, 180, 210)                    # #46B4D2
NOTE_HIGH_COLOR = QColor(230, 120, 190)                  # #E678BE
NOTE_BORDER_COLOR = QColor(0, 0, 0, 100)                 # #000000 with alpha - Subtle border for notes

# =============================================================================
# --- Fonts ---
# =============================================================================
FONT_FAMILY_PRIMARY = "Segoe UI"
FONT_FAMILY_MONOSPACE = "Consolas"

# Font Sizes (in points)
FONT_SIZE_XS = 7
FONT_SIZE_S = 8
FONT_SIZE_M = 9    # Normal / Default
FONT_SIZE_L = 10
FONT_SIZE_XL = 12  # Headers

# Font Weights
FONT_WEIGHT_NORMAL = 400 # QFont.Normal
FONT_WEIGHT_MEDIUM = 500 # QFont.Medium
FONT_WEIGHT_BOLD = 700   # QFont.Bold

# =============================================================================
# --- Spacing & Sizing ---
# =============================================================================
# Border Radius (in pixels)
BORDER_RADIUS_S = 3
BORDER_RADIUS_M = 5  # Standard
BORDER_RADIUS_L = 7  # For larger elements like cards or dialogs

# Padding (in pixels)
PADDING_XS = 2
PADDING_S = 4
PADDING_M = 8   # Standard
PADDING_L = 12
PADDING_XL = 16

# Icon Sizes (in pixels)
ICON_SIZE_S = 12
ICON_SIZE_M = 16 # General icons
ICON_SIZE_L = 20
ICON_SIZE_XL = 24 # For plugin list/dialog headers

# Specific UI Element Sizing
PLUGIN_ROW_HEIGHT = 44

# =============================================================================
# --- Icon Paths ---
# =============================================================================
import os # Ensure os is imported if not already
from utils import get_resource_path # Import the helper

# Define the base path for assets using the portable resource path function
# ASSETS_BASE_PATH will be the absolute path to the 'assets' directory
ASSETS_BASE_PATH = get_resource_path("assets")

# Define icon paths relative to the ASSETS_BASE_PATH
ICON_DIR_NAME = "icons" # Subdirectory for icons within assets

# Helper to ensure forward slashes for QSS url() paths
def _qss_path(path_segments):
    return os.path.join(*path_segments).replace('\\', '/')

PLAY_ICON_PATH = _qss_path([ASSETS_BASE_PATH, ICON_DIR_NAME, "play.svg"])
PAUSE_ICON_PATH = _qss_path([ASSETS_BASE_PATH, ICON_DIR_NAME, "pause.svg"])
STOP_ICON_PATH = _qss_path([ASSETS_BASE_PATH, ICON_DIR_NAME, "stop.svg"])
PLUGIN_ICON_PATH_DEFAULT = _qss_path([ASSETS_BASE_PATH, ICON_DIR_NAME, "default-plugin.svg"])
DROPDOWN_ICON_PATH = _qss_path([ASSETS_BASE_PATH, ICON_DIR_NAME, "chevron_down.svg"])
APP_ICON_PATH = _qss_path([ASSETS_BASE_PATH, ICON_DIR_NAME, "app_icon.png"]) # For main window icon

# CHECKMARK_ICON_PATH = _qss_path([ASSETS_BASE_PATH, ICON_DIR_NAME, "checkmark.svg"])

# =============================================================================
# --- Mapping Legacy Names (Informational - to be removed or refactored in usage) ---
# =============================================================================
# This section is for reference during the transition. Ideally, all parts of the
# application will be updated to use the new semantic names directly.

# Old Name                     -> New Semantic Name
# ----------------------------------------------------
# BG_COLOR                     -> PIANO_ROLL_BG_COLOR
# GRID_COLOR                   -> GRID_LINE_COLOR
# BEAT_COLOR                   -> GRID_BEAT_LINE_COLOR
# MEASURE_COLOR                -> GRID_MEASURE_LINE_COLOR
# ROW_HIGHLIGHT_COLOR          -> GRID_ROW_HIGHLIGHT_COLOR
# KEY_GRID_COLOR               -> KEY_GRID_LINE_COLOR
# PLAYHEAD_COLOR (old alpha)   -> PLAYHEAD_COLOR (opaque)
# WHITE_KEY_COLOR              -> WHITE_KEY_COLOR
# BLACK_KEY_COLOR              -> BLACK_KEY_COLOR
# KEY_BORDER_COLOR (old alpha) -> KEY_BORDER_COLOR (updated alpha)

# NOTE_COLORS (dict)           -> NOTE_LOW_COLOR, NOTE_MED_COLOR, NOTE_HIGH_COLOR

# PRIMARY_TEXT_COLOR (old val) -> PRIMARY_TEXT_COLOR (value updated)
# SECONDARY_TEXT_COLOR (old val)-> SECONDARY_TEXT_COLOR (value updated)
# ACCENT_COLOR (old val)       -> ACCENT_PRIMARY_COLOR
# ACCENT_HOVER_COLOR (old val) -> ACCENT_HOVER_COLOR (value updated)
# ACCENT_PRESSED_COLOR (old val)-> ACCENT_PRESSED_COLOR (value updated)

# BUTTON_COLOR                 -> STANDARD_BUTTON_BG_COLOR
# BUTTON_HOVER_COLOR           -> STANDARD_BUTTON_HOVER_BG_COLOR
# BUTTON_PRESSED_COLOR         -> STANDARD_BUTTON_PRESSED_BG_COLOR
# BUTTON_TEXT_COLOR            -> STANDARD_BUTTON_TEXT_COLOR

# HIGHLIGHT_COLOR              -> ITEM_HOVER_BG_COLOR
# SELECTION_COLOR              -> ITEM_SELECTED_BG_COLOR
# SELECTION_TEXT_COLOR         -> ACCENT_TEXT_COLOR

# DIALOG_BG_COLOR (old val)    -> DIALOG_BG_COLOR (value updated)
# INPUT_BG_COLOR (old val)     -> INPUT_BG_COLOR (value updated)
# INPUT_BORDER_COLOR (old val) -> BORDER_COLOR_NORMAL
# INPUT_TEXT_COLOR (old val)   -> PRIMARY_TEXT_COLOR
# INPUT_SELECTED_BORDER_COLOR  -> BORDER_COLOR_FOCUSED

# DRAG_OVERLAY_COLOR (old val) -> DRAG_OVERLAY_COLOR (value updated with ACCENT_PRIMARY_COLOR + alpha)

# FONT_FAMILY (old)            -> FONT_FAMILY_PRIMARY
# FONT_SIZE_NORMAL             -> FONT_SIZE_M
# FONT_SIZE_LARGE              -> FONT_SIZE_L
# FONT_WEIGHT_BOLD (string)    -> FONT_WEIGHT_BOLD (integer)

# BORDER_RADIUS (old)          -> BORDER_RADIUS_M
# PADDING_SMALL (old)          -> PADDING_S
# PADDING_MEDIUM (old)         -> PADDING_M
# PADDING_LARGE (old)          -> PADDING_L

# ICON_SIZE (old)              -> ICON_SIZE_M
# PLUGIN_ICON_SIZE (old)       -> ICON_SIZE_XL
# (PLUGIN_ROW_HEIGHT remains)

# Removed old SLIDER_TRACK_COLOR, SLIDER_HANDLE_COLOR etc.
# ModernSlider uses ACCENT colors for handle and theme.INPUT_BG_COLOR or specific for track.
