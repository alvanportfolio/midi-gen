from PySide6.QtWidgets import QSlider, QPushButton, QToolButton, QApplication
from PySide6.QtCore import Qt, QSize, Signal, QPoint
from PySide6.QtGui import QFont, QIcon, QMouseEvent # Added QMouseEvent
from typing import Optional
from config import theme

class ModernSlider(QSlider):
    """Custom slider with a modern appearance, using theme colors."""
    
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px; /* Slightly thicker for better touch/click */
                background: {theme.SLIDER_TRACK_COLOR.name()};
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background: {theme.SLIDER_HANDLE_COLOR.name()};
                width: 14px; /* Slightly wider handle */
                height: 14px;
                margin: -4px 0; /* Adjust to center on the groove */
                border-radius: 7px; /* Circular handle */
            }}
            QSlider::handle:horizontal:hover {{
                background: {theme.SLIDER_HANDLE_HOVER_COLOR.name()};
            }}
            QSlider::handle:horizontal:pressed {{
                background: {theme.SLIDER_HANDLE_PRESSED_COLOR.name()};
            }}
            
            QSlider::add-page:horizontal {{
                background: {theme.SLIDER_TRACK_COLOR.name()}; /* Unfilled part */
                border-radius: 3px;
            }}
            
            QSlider::sub-page:horizontal {{
                background: {theme.ACCENT_COLOR.name()}; /* Filled part */
                border-radius: 3px;
            }}

            /* Vertical Slider Styles (if needed) */
            QSlider::groove:vertical {{
                width: 6px;
                background: {theme.SLIDER_TRACK_COLOR.name()};
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {theme.SLIDER_HANDLE_COLOR.name()};
                height: 14px;
                width: 14px;
                margin: 0 -4px;
                border-radius: 7px;
            }}
            QSlider::handle:vertical:hover {{
                background: {theme.SLIDER_HANDLE_HOVER_COLOR.name()};
            }}
            QSlider::handle:vertical:pressed {{
                background: {theme.SLIDER_HANDLE_PRESSED_COLOR.name()};
            }}
            QSlider::add-page:vertical {{
                background: {theme.ACCENT_COLOR.name()}; /* Filled part for vertical */
                border-radius: 3px;
            }}
            QSlider::sub-page:vertical {{
                background: {theme.SLIDER_TRACK_COLOR.name()}; /* Unfilled part for vertical */
                border-radius: 3px;
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
        
        self.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL))
        
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
            bg = theme.ACCENT_COLOR.name()
            hover = theme.ACCENT_HOVER_COLOR.name()
            pressed = theme.ACCENT_PRESSED_COLOR.name()
            text_color = theme.SELECTION_TEXT_COLOR.name() # Often white/light for accent buttons
        else:
            bg = theme.BUTTON_COLOR.name()
            hover = theme.BUTTON_HOVER_COLOR.name()
            pressed = theme.BUTTON_PRESSED_COLOR.name()
            text_color = theme.BUTTON_TEXT_COLOR.name()

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: none; 
                padding: {theme.PADDING_SMALL + 2}px {theme.PADDING_MEDIUM}px;
                border-radius: {theme.BORDER_RADIUS}px;
                font-family: "{theme.FONT_FAMILY}";
                font-size: {theme.FONT_SIZE_NORMAL}pt;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {pressed};
            }}
            QPushButton:disabled {{
                background-color: {theme.BUTTON_COLOR.darker(120).name()}; /* Slightly darker/grayed out */
                color: {theme.SECONDARY_TEXT_COLOR.name()};
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
            self.setIconSize(QSize(24,24))
            border_radius = 18


        self.setStyleSheet(f"""
            QToolButton {{
                background-color: {theme.BUTTON_COLOR.name()};
                color: {theme.BUTTON_TEXT_COLOR.name()}; /* Icon color can be tricky, often part of SVG or PNG */
                border: none;
                border-radius: {border_radius}px; 
                padding: 6px; /* Padding around icon */
            }}
            QToolButton:hover {{
                background-color: {theme.BUTTON_HOVER_COLOR.name()};
            }}
            QToolButton:pressed {{
                background-color: {theme.BUTTON_PRESSED_COLOR.name()};
            }}
            QToolButton:checked {{ /* For toggle buttons */
                background-color: {theme.ACCENT_COLOR.name()};
            }}
            QToolButton:disabled {{
                background-color: {theme.BUTTON_COLOR.darker(120).name()};
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
