"""
Dock Area Widget Module

Provides dedicated dock detection zones that remain accessible regardless 
of the piano roll state, ensuring consistent docking behavior for floating panels.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QDragEnterEvent, QDragMoveEvent, QDropEvent

try:
    from config import theme
except ImportError:
    try:
        from ..config import theme
    except ImportError as e:
        print(f"Failed to import theme config in dock_area_widget: {e}")


class DockAreaWidget(QWidget):
    """
    A thin, dedicated widget that provides consistent dock detection zones 
    for Qt's docking system, ensuring floating panels can always be reattached
    regardless of the piano roll's state.
    """
    
    def __init__(self, edge_position="left", parent=None):
        """
        Initialize the dock area widget.
        
        Args:
            edge_position (str): Either "left" or "right" to specify which edge this widget covers
            parent: Parent widget
        """
        super().__init__(parent)
        self.edge_position = edge_position
        
        # Make the widget extremely thin but tall enough to capture dock events
        self.setFixedWidth(3)  # Very thin - just enough for dock detection
            
        # Set minimum height to ensure it's always visible and stretches full height
        self.setMinimumHeight(200)
        
        # Set size policy to ensure it takes full height but stays thin
        from PySide6.QtWidgets import QSizePolicy
        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setSizePolicy(size_policy)
        
        # Configure widget properties for dock detection
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)  # Must accept mouse events for docking
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)  # Allow transparency
        
        # Set tool tip for debugging
        self.setToolTip(f"Dock Area Zone ({edge_position.title()})")
        
        # Make it invisible but functional
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
        """)
    
    def sizeHint(self):
        """Provide size hint for the layout system."""
        return QSize(3, 200)
    
    def minimumSizeHint(self):
        """Provide minimum size hint."""
        return QSize(3, 200)
    
    def paintEvent(self, event):
        """
        Paint the widget. Normally invisible, but can be made visible for debugging.
        """
        painter = QPainter(self)
        
        # For debugging purposes, uncomment the line below to make the dock zones visible
        # painter.fillRect(self.rect(), QColor(255, 0, 0, 50))  # Semi-transparent red
        
        # Normally, draw nothing (transparent)
        painter.fillRect(self.rect(), Qt.transparent)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Handle drag enter events - accept dock-related drags.
        """
        # Accept all drag events to ensure dock detection works
        event.acceptProposedAction()
        super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """
        Handle drag move events during docking operations.
        """
        event.acceptProposedAction()
        super().dragMoveEvent(event)
    
    def dropEvent(self, event: QDropEvent):
        """
        Handle drop events - let the main window handle the actual docking.
        """
        # Don't handle the drop ourselves - let Qt's docking system handle it
        event.ignore()
        super().dropEvent(event)
    
    def mousePressEvent(self, event):
        """
        Handle mouse press events - pass through to parent for docking.
        """
        # Pass through to parent widget to ensure dock detection works
        event.ignore()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """
        Handle mouse move events - pass through to parent for docking.
        """
        # Pass through to parent widget to ensure dock detection works
        event.ignore()
        super().mouseMoveEvent(event)
    
    def enable_debug_visual(self, enable=True):
        """
        Enable or disable visual debugging of the dock area.
        
        Args:
            enable (bool): Whether to show the dock area visually
        """
        if enable:
            self.setStyleSheet("""
                QWidget {
                    background-color: rgba(255, 0, 0, 50);
                    border: 1px solid red;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border: none;
                }
            """)
        self.update()


class DockAreaManager:
    """
    Manager class to coordinate multiple dock area widgets and integrate 
    them with the main window layout.
    """
    
    def __init__(self, main_window):
        """
        Initialize the dock area manager.
        
        Args:
            main_window: The main window instance to integrate dock areas with
        """
        self.main_window = main_window
        self.left_dock_area = None
        self.right_dock_area = None
    
    def setup_dock_areas(self, parent_layout):
        """
        Set up left and right dock area widgets in the provided layout.
        
        Args:
            parent_layout: The layout to add dock areas to (typically QHBoxLayout)
        """
        # Create left dock area
        self.left_dock_area = DockAreaWidget("left", self.main_window)
        parent_layout.insertWidget(0, self.left_dock_area)  # Insert at beginning
        
        # Create right dock area  
        self.right_dock_area = DockAreaWidget("right", self.main_window)
        parent_layout.addWidget(self.right_dock_area)  # Add at end
        
        # Ensure the dock areas have proper properties for Qt's docking system
        for dock_area in [self.left_dock_area, self.right_dock_area]:
            dock_area.setAcceptDrops(True)
            dock_area.raise_()  # Bring to front for better detection
        
        print("Dock area widgets created and integrated into layout")
    
    def enable_debug_visuals(self, enable=True):
        """
        Enable or disable visual debugging for all dock areas.
        
        Args:
            enable (bool): Whether to show dock areas visually
        """
        if self.left_dock_area:
            self.left_dock_area.enable_debug_visual(enable)
        if self.right_dock_area:
            self.right_dock_area.enable_debug_visual(enable)
    
    def get_dock_areas(self):
        """
        Get references to the dock area widgets.
        
        Returns:
            tuple: (left_dock_area, right_dock_area)
        """
        return (self.left_dock_area, self.right_dock_area) 