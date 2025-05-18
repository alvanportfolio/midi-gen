from PySide6.QtWidgets import QSlider, QToolButton
from PySide6.QtCore import Qt

class ModernSlider(QSlider):
    """Custom slider with a modern appearance"""
    
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #2a2a30;
                border-radius: 2px;
            }
            
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9040, stop:1 #ff7000);
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            
            QSlider::add-page:horizontal {
                background: #2a2a30;
                border-radius: 2px;
            }
            
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a3a45, stop:1 #ff7000);
                border-radius: 2px;
            }
        """)

class ModernButton(QToolButton):
    """Custom button with modern appearance"""
    
    def __init__(self, icon=None, text=None, tooltip=None, parent=None):
        super().__init__(parent)
        
        if tooltip:
            self.setToolTip(tooltip)
            
        if text:
            self.setText(text)
            
        if icon:
            self.setIcon(icon)
            
        self.setFixedSize(36, 36)
        
        self.setStyleSheet("""
            QToolButton {
                color: #e0e0e0;
                background-color: #2d2d35;
                border-radius: 18px;
                border: none;
                padding: 4px;
            }
            
            QToolButton:hover {
                background-color: #3d3d45;
            }
            
            QToolButton:pressed {
                background-color: #404050;
            }
        """)
