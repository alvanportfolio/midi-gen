from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox

class MainWindowEventHandlersMixin:
    """
    Mixin class to handle specific events for the main window,
    such as keyboard shortcuts and close events.
    This event filter is installed on the MainWindow itself.
    """
    
    def eventFilter(self, watched, event):
        """Event filter for MainWindow - spacebar handling is now done in the main window class."""
        # Spacebar handling moved to PianoRollMainWindow.eventFilter() to avoid conflicts
        # This mixin eventFilter is kept for other potential shortcuts in the future
        return super().eventFilter(watched, event)
    
    def closeEvent(self, event):
        """Clean up resources when window is closed."""
        if hasattr(self, 'midi_player') and self.midi_player:
            self.midi_player.stop()
        if hasattr(self, 'playback_timer') and self.playback_timer:
            self.playback_timer.stop()
        
        if hasattr(self, 'plugin_manager_panel') and self.plugin_manager_panel and \
           hasattr(self.plugin_manager_panel, 'cleanup_temporary_files') and \
           callable(self.plugin_manager_panel.cleanup_temporary_files):
            print("MainWindow: Cleaning up temporary MIDI files...")
            self.plugin_manager_panel.cleanup_temporary_files()
            
        super().closeEvent(event)

class GlobalPlaybackHotkeyFilter(QObject):
    """
    Global event filter to handle Spacebar for toggling playback.
    Installed on QApplication.instance().
    """
    def __init__(self, main_window_toggle_method, parent=None): # Changed to accept main window's toggle method
        super().__init__(parent)
        self.main_window_toggle_method = main_window_toggle_method

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent) and event.key() == Qt.Key_Space:
                focused_widget = QApplication.focusWidget()
                
                if isinstance(focused_widget, (QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox)):
                    return False 

                if isinstance(focused_widget, QComboBox) and focused_widget.view().isVisible():
                    return False

                if callable(self.main_window_toggle_method):
                    print("GlobalHotkeyFilter: Spacebar pressed, calling main window toggle_playback.")
                    self.main_window_toggle_method()
                    return True 
        
        return False
