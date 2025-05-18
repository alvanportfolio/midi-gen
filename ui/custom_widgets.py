from PySide6.QtWidgets import QSlider, QPushButton, QToolButton
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from typing import Optional # Import Optional
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
