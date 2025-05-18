from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent

class MainWindowEventHandlersMixin:
    """
    Mixin class to handle specific events for the main window,
    such as keyboard shortcuts and close events.
    """
    
    def eventFilter(self, watched, event):
        """Handle keyboard events for shortcuts (e.g., Space for play/pause)."""
        if event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent) and event.key() == Qt.Key_Space:
                # toggle_playback needs to be a method on the class using this mixin
                if hasattr(self, 'toggle_playback') and callable(self.toggle_playback):
                    self.toggle_playback()
                    return True
        # Call the base class eventFilter if the event is not handled here.
        # This assumes the class using the mixin is a QObject or QWidget derivative.
        return super().eventFilter(watched, event) 
    
    def closeEvent(self, event):
        """Clean up resources when window is closed."""
        # midi_player and playback_timer need to be attributes of the class using this mixin
        if hasattr(self, 'midi_player') and self.midi_player:
            self.midi_player.stop()
        if hasattr(self, 'playback_timer') and self.playback_timer:
            self.playback_timer.stop()
        # Call the base class closeEvent.
        # This assumes the class using the mixin is a QWidget derivative (like QMainWindow).
        super().closeEvent(event)
