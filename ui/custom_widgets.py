from PySide6.QtWidgets import QSlider, QPushButton, QToolButton, QApplication
from PySide6.QtCore import Qt, QSize, Signal, QPoint
from PySide6.QtGui import QFont, QIcon, QMouseEvent # Added QMouseEvent
from typing import Optional
from config import theme

class ModernSlider(QSlider):
    """Custom slider with a modern appearance, using theme colors."""
    
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        # Use a darker gray for the track, like INPUT_BG_COLOR or a specific SLIDER_TRACK_BG_COLOR if defined
        # Assuming SLIDER_TRACK_COLOR is suitable or will be updated in theme.py if needed.
        # For now, let's use a color that's distinct from the main app background for clarity.
        # If theme.SLIDER_TRACK_COLOR is not defined, using theme.INPUT_BG_COLOR as fallback.
        track_bg_color = getattr(theme, 'SLIDER_TRACK_COLOR', theme.INPUT_BG_COLOR).name()
        
        # Filled part color - using ACCENT_PRIMARY_COLOR, possibly a bit lighter if handle is same color
        sub_page_bg_color = theme.ACCENT_PRIMARY_COLOR.lighter(120).name()
        if theme.ACCENT_PRIMARY_COLOR.lightness() > 200: # If accent is very light, make sub-page darker
            sub_page_bg_color = theme.ACCENT_PRIMARY_COLOR.darker(120).name()


        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: {theme.PADDING_S}px; /* Use theme spacing */
                background: {track_bg_color};
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}
            
            QSlider::handle:horizontal {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.ACCENT_PRIMARY_COLOR.lighter(115).name()}, stop:1 {theme.ACCENT_PRIMARY_COLOR.darker(115).name()});
                width: {theme.ICON_SIZE_M}px; 
                height: {theme.ICON_SIZE_M}px;
                margin-top: -{(theme.ICON_SIZE_M - theme.PADDING_S) // 2}px; /* Center handle on groove */
                margin-bottom: -{(theme.ICON_SIZE_M - theme.PADDING_S) // 2}px;
                border-radius: {theme.ICON_SIZE_M // 2}px; /* Circular handle */
                border: 1px solid {theme.ACCENT_PRIMARY_COLOR.darker(130).name()}; /* Subtle border for definition */
            }}
            QSlider::handle:horizontal:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.ACCENT_HOVER_COLOR.lighter(115).name()}, stop:1 {theme.ACCENT_HOVER_COLOR.darker(115).name()});
                border: 1px solid {theme.ACCENT_HOVER_COLOR.darker(130).name()};
            }}
            QSlider::handle:horizontal:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.ACCENT_PRESSED_COLOR.lighter(115).name()}, stop:1 {theme.ACCENT_PRESSED_COLOR.darker(115).name()});
                border: 1px solid {theme.ACCENT_PRESSED_COLOR.darker(130).name()};
            }}
            
            QSlider::add-page:horizontal {{
                background: {track_bg_color}; /* Unfilled part */
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}
            
            QSlider::sub-page:horizontal {{
                background: {sub_page_bg_color}; /* Filled part */
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}

            /* Vertical Slider Styles */
            QSlider::groove:vertical {{
                width: {theme.PADDING_S}px;
                background: {track_bg_color};
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}
            QSlider::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.ACCENT_PRIMARY_COLOR.lighter(115).name()}, stop:1 {theme.ACCENT_PRIMARY_COLOR.darker(115).name()});
                height: {theme.ICON_SIZE_M}px;
                width: {theme.ICON_SIZE_M}px;
                margin-left: -{(theme.ICON_SIZE_M - theme.PADDING_S) // 2}px; /* Center handle on groove */
                margin-right: -{(theme.ICON_SIZE_M - theme.PADDING_S) // 2}px;
                border-radius: {theme.ICON_SIZE_M // 2}px;
                border: 1px solid {theme.ACCENT_PRIMARY_COLOR.darker(130).name()};
            }}
            QSlider::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.ACCENT_HOVER_COLOR.lighter(115).name()}, stop:1 {theme.ACCENT_HOVER_COLOR.darker(115).name()});
                border: 1px solid {theme.ACCENT_HOVER_COLOR.darker(130).name()};
            }}
            QSlider::handle:vertical:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme.ACCENT_PRESSED_COLOR.lighter(115).name()}, stop:1 {theme.ACCENT_PRESSED_COLOR.darker(115).name()});
                border: 1px solid {theme.ACCENT_PRESSED_COLOR.darker(130).name()};
            }}
            QSlider::add-page:vertical {{
                background: {sub_page_bg_color}; /* Filled part for vertical */
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}
            QSlider::sub-page:vertical {{
                background: {track_bg_color}; /* Unfilled part for vertical */
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}
        """)

class ModernButton(QPushButton):
    """
    Custom QPushButton with modern appearance using theme colors.
    Supports text, icons, and different styles (normal, accent).
    """
    
    def __init__(self, text="", icon: Optional[QIcon] = None, tooltip="", parent=None, accent=False, fixed_size=None):
        super().__init__(text, parent)
        
        if icon:
            self.setIcon(icon)
            # Adjust icon size based on theme if needed, e.g., self.setIconSize(QSize(theme.ICON_SIZE, theme.ICON_SIZE))
        
        if tooltip:
            self.setToolTip(tooltip)
        
        self.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M))
        
        if fixed_size and isinstance(fixed_size, tuple) and len(fixed_size) == 2:
            self.setFixedSize(QSize(fixed_size[0], fixed_size[1]))
        elif fixed_size and isinstance(fixed_size, QSize):
            self.setFixedSize(fixed_size)
        else:
            # Default padding if not fixed size, text will determine width
            self.setMinimumHeight(30) # Ensure a decent minimum height

        self.is_accent = accent
        self._update_style()

    def setAccent(self, accent: bool):
        if self.is_accent != accent:
            self.is_accent = accent
            self._update_style()

    def _update_style(self):
        if self.is_accent:
            bg_base = theme.ACCENT_PRIMARY_COLOR
            hover_base = theme.ACCENT_HOVER_COLOR
            pressed_base = theme.ACCENT_PRESSED_COLOR
            text_color = theme.ACCENT_TEXT_COLOR.name()
            border_color = bg_base.darker(120).name()
            border_hover_color = hover_base.darker(120).name()
        else:
            bg_base = theme.STANDARD_BUTTON_BG_COLOR
            hover_base = theme.STANDARD_BUTTON_HOVER_BG_COLOR
            pressed_base = theme.STANDARD_BUTTON_PRESSED_BG_COLOR
            text_color = theme.STANDARD_BUTTON_TEXT_COLOR.name()
            border_color = theme.BORDER_COLOR_NORMAL.name()
            border_hover_color = theme.BORDER_COLOR_HOVER.name()

        # Subtle gradient for depth
        bg_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {bg_base.lighter(105).name()}, stop:1 {bg_base.name()})"
        hover_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {hover_base.lighter(105).name()}, stop:1 {hover_base.name()})"
        pressed_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {pressed_base.name()}, stop:1 {pressed_base.darker(105).name()})"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_gradient};
                color: {text_color};
                border: 1px solid {border_color}; 
                padding: {theme.PADDING_S}px {theme.PADDING_M}px;
                border-radius: {theme.BORDER_RADIUS_M}px;
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_M}pt;
                text-align: center;
                /* Attempt for subtle shadow - might not work on all platforms/styles */
                /* box-shadow: 0px 1px 3px {theme.SHADOW_COLOR.name()}; */
            }}
            QPushButton:hover {{
                background-color: {hover_gradient};
                border: 1px solid {border_hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_gradient};
                border: 1px solid {pressed_base.darker(120).name()};
            }}
            QPushButton:focus {{
                border: 1px solid {theme.ACCENT_PRIMARY_COLOR.name()};
                /* outline: 2px solid {theme.ACCENT_PRIMARY_COLOR.name()}; */ /* Alternative focus indicator */
            }}
            QPushButton:disabled {{
                background-color: {theme.DISABLED_BG_COLOR.name()}; 
                color: {theme.DISABLED_TEXT_COLOR.name()};
                border: 1px solid {theme.DISABLED_BG_COLOR.darker(110).name()};
            }}
        """)

class ModernIconButton(QToolButton):
    """
    Custom QToolButton specifically for icon-only buttons, 
    often used in toolbars or for compact controls like transport.
    """
    def __init__(self, icon: Optional[QIcon] = None, tooltip="", parent=None, fixed_size=(36,36)): # Allow None for icon
        super().__init__(parent)
        
        if icon: # Check if icon is provided before setting
            self.setIcon(icon)
        self.setToolTip(tooltip)
        
        if fixed_size and isinstance(fixed_size, tuple) and len(fixed_size) == 2:
            self.setFixedSize(QSize(fixed_size[0], fixed_size[1]))
            self.setIconSize(QSize(fixed_size[0] - 12, fixed_size[1] - 12)) # Adjust icon size within button
            border_radius = fixed_size[0] // 2 # For circular buttons if square
        elif fixed_size and isinstance(fixed_size, QSize):
             self.setFixedSize(fixed_size)
             self.setIconSize(QSize(fixed_size.width() - 12, fixed_size.height() - 12))
             border_radius = fixed_size.width() // 2
        else:
            # Default if no fixed size, though typically icon buttons have one
            self.setFixedSize(QSize(36,36))
            self.setIconSize(QSize(theme.ICON_SIZE_L, theme.ICON_SIZE_L)) # Default icon size
            border_radius = theme.BORDER_RADIUS_M # Default border radius
        
        # Base colors
        bg_base = theme.STANDARD_BUTTON_BG_COLOR
        hover_base = theme.STANDARD_BUTTON_HOVER_BG_COLOR
        pressed_base = theme.STANDARD_BUTTON_PRESSED_BG_COLOR
        checked_bg_base = theme.ACCENT_PRIMARY_COLOR
        icon_color = theme.PRIMARY_TEXT_COLOR.name() # Default icon color
        border_color = theme.BORDER_COLOR_NORMAL.name()

        # Subtle gradient for depth
        bg_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {bg_base.lighter(105).name()}, stop:1 {bg_base.name()})"
        hover_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {hover_base.lighter(105).name()}, stop:1 {hover_base.name()})"
        pressed_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {pressed_base.name()}, stop:1 {pressed_base.darker(105).name()})"
        checked_gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {checked_bg_base.lighter(105).name()}, stop:1 {checked_bg_base.name()})"


        self.setStyleSheet(f"""
            QToolButton {{
                background-color: {bg_gradient};
                color: {icon_color}; /* For text if any, icon color is usually from icon itself */
                border: 1px solid {border_color};
                border-radius: {border_radius}px; 
                padding: {theme.PADDING_S}px; 
            }}
            QToolButton:hover {{
                background-color: {hover_gradient};
                border: 1px solid {theme.BORDER_COLOR_HOVER.name()};
            }}
            QToolButton:pressed {{
                background-color: {pressed_gradient};
                border: 1px solid {pressed_base.darker(120).name()};
            }}
            QToolButton:checked {{ /* For toggle buttons */
                background-color: {checked_gradient};
                border: 1px solid {checked_bg_base.darker(120).name()};
                color: {theme.ACCENT_TEXT_COLOR.name()}; /* Icon color for checked state */
            }}
            QToolButton:focus {{
                border: 1px solid {theme.ACCENT_PRIMARY_COLOR.name()};
            }}
            QToolButton:disabled {{
                background-color: {theme.DISABLED_BG_COLOR.name()};
                border: 1px solid {theme.DISABLED_BG_COLOR.darker(110).name()};
                /* Icon might need to be a different disabled version or QSS might not colorize it directly */
            }}
        """)

class DragExportButton(ModernButton):
    """
    A ModernButton that supports both click and drag-initiation.
    Emits 'clicked' for a normal click.
    Emits 'dragInitiated' when a drag gesture is detected.
    """
    dragInitiated = Signal()
    # 'clicked' signal is inherited from QPushButton

    def __init__(self, text="", icon: Optional[QIcon] = None, tooltip="", parent=None, accent=False, fixed_size=None):
        super().__init__(text, icon, tooltip, parent, accent, fixed_size)
        self.drag_start_position: Optional[QPoint] = None
        self.is_dragging = False

    def mousePressEvent(self, e: QMouseEvent): # Changed 'event' to 'e'
        if e.button() == Qt.LeftButton:
            self.drag_start_position = e.pos()
            self.is_dragging = False # Reset dragging state
        super().mousePressEvent(e) # Call base class to handle press styling etc.

    def mouseMoveEvent(self, arg__1: QMouseEvent): # Changed 'e' to 'arg__1'
        if not (arg__1.buttons() & Qt.LeftButton) or self.drag_start_position is None:
            super().mouseMoveEvent(arg__1)
            return

        # If already dragging, let the QDrag object handle events primarily
        if self.is_dragging:
            super().mouseMoveEvent(arg__1) # Allow base class to see it, but drag is active
            return

        # Check if the mouse has moved enough to start a drag
        if (arg__1.pos() - self.drag_start_position).manhattanLength() >= QApplication.startDragDistance():
            self.is_dragging = True
            self.dragInitiated.emit()
            # Once drag is initiated, we don't want to re-emit for this press-drag sequence.
            # The actual QDrag object will be created by the receiver of dragInitiated.
        
        super().mouseMoveEvent(arg__1) # Call base class

    def mouseReleaseEvent(self, e: QMouseEvent): # Changed 'event' to 'e'
        # The 'clicked' signal is emitted by QPushButton if mousePressEvent and mouseReleaseEvent
        # happen on the same button without a drag in between.
        # Our self.is_dragging flag helps differentiate.
        
        if e.button() == Qt.LeftButton:
            # If a drag was started, we don't want this to also be a click.
            # The base QPushButton handles emitting 'clicked' if it wasn't a drag.
            # We just need to reset our state.
            if self.is_dragging:
                # If a drag occurred, we ensure the button doesn't also process this as a click.
                # One way is to ensure the base class doesn't think it's a click.
                # However, simply setting is_dragging and letting super().mouseReleaseEvent run
                # might be enough if QPushButton checks internal state that we haven't disrupted.
                # For safety, we can temporarily unset 'pressed' state if needed,
                # but usually, QDrag takes over mouse events.
                pass # Drag was handled, base class might still try to click

            # Reset drag state whether it was a drag or a click
            self.drag_start_position = None
            self.is_dragging = False
        
        # Call super's mouseReleaseEvent. This is crucial for the 'clicked' signal to be emitted
        # by QPushButton if it was a genuine click (i.e., not a drag).
        current_is_pressed = self.isDown()
        super().mouseReleaseEvent(e)

        # If it was a click (not a drag) and the button was pressed and now released over the button
        if not self.is_dragging and \
           self.drag_start_position is not None and \
           self.rect().contains(e.pos()) and \
           current_is_pressed and not self.isDown():
            # This condition attempts to ensure 'clicked' is emitted for a simple click.
            # QPushButton's own logic is usually robust.
            # If 'clicked' signal is not working as expected, this area might need refinement
            # or ensuring that mousePressEvent doesn't interfere with base class state.
            # For now, relying on super() to emit 'clicked' correctly if not self.is_dragging.
            pass
