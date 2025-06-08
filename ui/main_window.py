import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QSizePolicy, QSlider, QStyle, QToolButton,
    QFrame, QSpacerItem, QDockWidget, QListWidget, QListWidgetItem,
    QFormLayout, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QDialog, QDialogButtonBox, QFileDialog, QApplication, QMessageBox,
    QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize, QEvent
from PySide6.QtGui import QKeyEvent, QColor, QPalette, QFont, QLinearGradient, QBrush
import pretty_midi
import time
import os

# Import fixes - Try absolute imports first, then relative imports
try:
    from note_display import PianoRollDisplay, PianoRollComposite
    from midi_player import MidiPlayer
    from plugin_manager import PluginManager
    from export_utils import export_to_midi
except ImportError:
    try:
        from ..note_display import PianoRollDisplay, PianoRollComposite
        from ..midi_player import MidiPlayer
        from ..plugin_manager import PluginManager
        from ..export_utils import export_to_midi
    except ImportError as e:
        print(f"Failed to import modules: {e}")
        sys.exit(1)

from .custom_widgets import ModernSlider, ModernButton
from .plugin_dialogs import PluginParameterDialog
from .plugin_panel import PluginManagerPanel
from .ai_studio_panel import AIStudioPanel
from .transport_controls import TransportControls
from .event_handlers import MainWindowEventHandlersMixin, GlobalPlaybackHotkeyFilter

try:
    from config import theme
except ImportError:
    try:
        from ..config import theme
    except ImportError as e:
        print(f"Failed to import theme config: {e}")
        sys.exit(1)


class PianoRollMainWindow(QMainWindow, MainWindowEventHandlersMixin):
    """Piano roll window that displays MIDI notes graphically"""
    
    def __init__(self, midi_notes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MIDI-GEN V2.0")
        self.setMinimumSize(1000, 600)
        
        # Configure dock options for better drag-and-drop behavior
        self.setDockOptions(
            QMainWindow.AnimatedDocks |           # Enable animated docking
            QMainWindow.AllowNestedDocks |        # Allow dock widgets to be nested
            QMainWindow.AllowTabbedDocks |        # Allow dock widgets to be tabbed
            QMainWindow.GroupedDragging |         # Enable grouped dragging
            QMainWindow.VerticalTabs              # Enable vertical tabs
        )
        
        # Enable all dock areas
        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        
        self.midi_notes = midi_notes or []
        self.midi_player = MidiPlayer()
        self.bpm = 120
        self.total_duration = 10.0
        
        self._apply_stylesheet()
        
        if self.midi_notes:
            print(f"Setting initial {len(self.midi_notes)} notes in MIDI player")
            self.midi_player.set_notes(self.midi_notes)
            
        self._setup_central_widget()
        self._setup_main_layout()
        
        self.create_piano_roll_display()
        
        self.transport_controls = TransportControls()
        self.main_layout.addWidget(self.transport_controls)
        self._connect_transport_signals()
        
        self.create_plugin_manager()
        self.create_ai_studio_panel()
        
        # 🔧 FIXED: Install global spacebar handler that works everywhere
        self.global_hotkey_filter = GlobalPlaybackHotkeyFilter(self.toggle_playback)
        QApplication.instance().installEventFilter(self.global_hotkey_filter)
        print("Global spacebar event filter installed for playback control.")
            
        self.playback_timer = QTimer(self)
        self.update_timer_interval()
        self.playback_timer.timeout.connect(self.update_playback_position)

        # Initialize transport controls after all components are ready
        self.transport_controls.set_bpm_value(self.bpm)
        self.update_slider_range()
        
        # Debug: Print dock options to ensure they're set correctly
        print(f"Dock options enabled: {self.dockOptions()}")
        print(f"Plugin Manager allowed areas: {self.plugin_manager_panel.allowedAreas()}")
        print(f"AI Studio allowed areas: {self.ai_studio_panel.allowedAreas()}")

    def _apply_stylesheet(self):
        # Global stylesheet using constants from theme.py
        qss = f"""
            QMainWindow, QWidget {{
                background-color: {theme.APP_BG_COLOR.name()};
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_M}pt;
            }}

            QLabel {{
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_M}pt;
            }}

            QDockWidget::title {{
                background-color: {theme.PANEL_BG_COLOR.darker(110).name()};
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_L}pt;
                font-weight: {theme.FONT_WEIGHT_BOLD};
                padding: {theme.PADDING_S}px {theme.PADDING_M}px;
                border-bottom: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
                text-align: left;
            }}

            QDockWidget {{
                border: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
                titlebar-close-icon: url();
                titlebar-normal-icon: url();
            }}
            
            /* Dock widget separator styling */
            QMainWindow::separator {{
                background-color: {theme.BORDER_COLOR_NORMAL.name()};
                width: 2px;
                height: 2px;
            }}
            
            QMainWindow::separator:hover {{
                background-color: {theme.ACCENT_PRIMARY_COLOR.name()};
            }}
            
            /* Ensure dock indicators are visible */
            QMainWindow QRubberBand {{
                background-color: {theme.ACCENT_PRIMARY_COLOR.name()};
                border: 2px solid {theme.ACCENT_HOVER_COLOR.name()};
                opacity: 0.7;
            }}
            
            QScrollBar:horizontal {{
                background-color: {theme.PANEL_BG_COLOR.lighter(110).name()};
                height: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {theme.BORDER_COLOR_NORMAL.name()};
                min-width: 20px;
                border-radius: {theme.BORDER_RADIUS_S}px;
                margin: 2px 0px 2px 0px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {theme.BORDER_COLOR_HOVER.name()};
            }}
            QScrollBar::handle:horizontal:pressed {{
                background-color: {theme.ACCENT_PRIMARY_COLOR.name()};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}

            QScrollBar:vertical {{
                background-color: {theme.PANEL_BG_COLOR.lighter(110).name()};
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme.BORDER_COLOR_NORMAL.name()};
                min-height: 20px;
                border-radius: {theme.BORDER_RADIUS_S}px;
                margin: 0px 2px 0px 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.BORDER_COLOR_HOVER.name()};
            }}
            QScrollBar::handle:vertical:pressed {{
                background-color: {theme.ACCENT_PRIMARY_COLOR.name()};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            QScrollArea {{
                background-color: {theme.PIANO_ROLL_BG_COLOR.name()}; 
                border: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
            }}
            
            QPushButton {{
                background-color: {theme.STANDARD_BUTTON_BG_COLOR.name()};
                color: {theme.STANDARD_BUTTON_TEXT_COLOR.name()};
                border: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
                padding: {theme.PADDING_S}px {theme.PADDING_M}px;
                border-radius: {theme.BORDER_RADIUS_M}px;
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_M}pt;
            }}
            QPushButton:hover {{
                background-color: {theme.STANDARD_BUTTON_HOVER_BG_COLOR.name()};
                border: 1px solid {theme.BORDER_COLOR_HOVER.name()};
            }}
            QPushButton:pressed {{
                background-color: {theme.STANDARD_BUTTON_PRESSED_BG_COLOR.name()};
            }}
            QPushButton:disabled {{
                background-color: {theme.DISABLED_BG_COLOR.name()};
                color: {theme.DISABLED_TEXT_COLOR.name()};
                border-color: {theme.DISABLED_BG_COLOR.darker(110).name()};
            }}
        """
        self.setStyleSheet(qss)

    def _setup_central_widget(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

    def _setup_main_layout(self):
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
    
    def create_plugin_manager(self):
        self.plugin_manager_panel = PluginManagerPanel(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plugin_manager_panel)
        self.plugin_manager_panel.notesGenerated.connect(self.set_midi_notes)
        self.plugin_manager_panel.set_current_notes(self.midi_notes)

    def create_ai_studio_panel(self):
        self.ai_studio_panel = AIStudioPanel(self)
        # Start AI Studio in right dock area for better testing
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_studio_panel)
        self.ai_studio_panel.notesGenerated.connect(self.set_midi_notes)
        self.ai_studio_panel.set_current_notes(self.midi_notes)
        
        # Initially hide AI studio panel (start with plugin manager)
        self.ai_studio_panel.hide()

    def _connect_transport_signals(self):
        self.transport_controls.playClicked.connect(self.start_playback)
        self.transport_controls.pauseClicked.connect(self.pause_playback)
        self.transport_controls.stopClicked.connect(self.stop_playback)
        self.transport_controls.seekPositionChanged.connect(self.slider_position_changed_slot)
        self.transport_controls.bpmChangedSignal.connect(self.bpm_changed_slot)
        self.transport_controls.instrumentChangedSignal.connect(self.instrument_changed_slot)
        self.transport_controls.volumeChangedSignal.connect(self.volume_changed_slot)
        self.transport_controls.aiModeToggled.connect(self.toggle_ai_mode)
        self.transport_controls.clearNotesClicked.connect(self.clear_notes)

    def create_piano_roll_display(self):
        # Use the new composite widget with fixed piano keys
        self.piano_roll = PianoRollComposite(self.midi_notes)
        self.piano_roll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addWidget(self.piano_roll, 1)
        
        # Connect signals from PianoRollComposite
        self.piano_roll.midiFileProcessed.connect(self.handle_midi_file_processed)
        self.piano_roll.notesChanged.connect(self.handle_notes_changed_from_display)

    @Slot(list)
    def handle_midi_file_processed(self, loaded_notes: list):
        """Handles notes loaded from a dropped MIDI file."""
        print(f"MainWindow: MIDI file processed, {len(loaded_notes)} notes received.")
        self.set_midi_notes(loaded_notes)
        self.stop_playback()

    @Slot(list)
    def handle_notes_changed_from_display(self, current_notes_in_display: list):
        """Handles notes changed by direct interaction in PianoRollDisplay."""
        print(f"MainWindow: Notes changed in display, {len(current_notes_in_display)} notes.")
        
        self.midi_notes = current_notes_in_display
        
        self.midi_player.set_notes(self.midi_notes)
        if hasattr(self, 'plugin_manager_panel'):
            self.plugin_manager_panel.set_current_notes(self.midi_notes)
        if hasattr(self, 'ai_studio_panel'):
            self.ai_studio_panel.set_current_notes(self.midi_notes)
        if hasattr(self, 'transport_controls'):
            self.transport_controls.set_current_notes(self.midi_notes)
        
        # Recalculate duration and update UI elements
        max_end_time = 0
        if self.midi_notes:
            for note in self.midi_notes:
                if hasattr(note, 'end') and note.end > max_end_time:
                    max_end_time = note.end
        self.total_duration = max_end_time + 1.0
        self.update_slider_range()

    def set_midi_notes(self, notes: list):
        """Primary method to update notes across the application."""
        print(f"PianoRollMainWindow: Setting {len(notes)} notes globally.")
        self.midi_notes = notes if notes is not None else []
        
        # Update PianoRollDisplay
        if hasattr(self, 'piano_roll') and self.piano_roll.notes != self.midi_notes:
            self.piano_roll.set_notes(self.midi_notes) 
        
        self.midi_player.set_notes(notes)
        
        max_end_time = 0
        for note in notes:
            if hasattr(note, 'end') and note.end > max_end_time:
                max_end_time = note.end
        
        self.total_duration = max_end_time + 1.0
        self.update_slider_range()
        
        if hasattr(self, 'plugin_manager_panel'):
            self.plugin_manager_panel.set_current_notes(notes)
        if hasattr(self, 'ai_studio_panel'):
            self.ai_studio_panel.set_current_notes(notes)
        if hasattr(self, 'transport_controls'):
            self.transport_controls.set_current_notes(notes)
        
        self.transport_controls.set_bpm_value(self.bpm)

    def clear_notes(self):
        """Clear all notes with user confirmation"""
        # Check if there are any notes to clear
        if not self.midi_notes or len(self.midi_notes) == 0:
            print("PianoRollMainWindow: No notes to clear.")
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Clear All Notes",
            f"Are you sure you want to clear all {len(self.midi_notes)} notes?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No for safety
        )
        
        if reply == QMessageBox.Yes:
            print("PianoRollMainWindow: Clearing all notes (user confirmed).")
            
            # Stop playback first
            self.stop_playback()
            
            # Clear notes
            self.midi_notes = []
            if hasattr(self, 'piano_roll'):
                self.piano_roll.set_notes([])
            if hasattr(self, 'midi_player'):
                self.midi_player.set_notes([])
            
            self.total_duration = 10.0
            self.update_slider_range()
            if hasattr(self, 'piano_roll'):
                self.piano_roll.set_playhead_position(0)
            
            if hasattr(self, 'transport_controls'):
                self.transport_controls.update_position_label(0)
                self.transport_controls.update_time_slider_value(0)

            if hasattr(self, 'plugin_manager_panel'):
                self.plugin_manager_panel.set_current_notes([])
            if hasattr(self, 'ai_studio_panel'):
                self.ai_studio_panel.set_current_notes([])
            if hasattr(self, 'transport_controls'):
                self.transport_controls.set_current_notes([])
                
            print(f"✅ Successfully cleared all notes from piano roll.")
        else:
            print("PianoRollMainWindow: Clear notes cancelled by user.")

    def receive_generated_note(self, note: pretty_midi.Note):
        if not hasattr(note, 'start') or not hasattr(note, 'end') or not hasattr(note, 'pitch'):
            print(f"PianoRollMainWindow: Received invalid note object: {note}")
            return

        self.midi_notes.append(note)
        if hasattr(self, 'piano_roll'):
            self.piano_roll.add_note(note)

        if note.end > self.total_duration:
            self.total_duration = note.end + 1.0
            self.update_slider_range()
        
        if hasattr(self, 'plugin_manager_panel'):
            self.plugin_manager_panel.set_current_notes(self.midi_notes)
        if hasattr(self, 'ai_studio_panel'):
            self.ai_studio_panel.set_current_notes(self.midi_notes)
        if hasattr(self, 'transport_controls'):
            self.transport_controls.set_current_notes(self.midi_notes)
    
    def toggle_playback(self):
        print(f"🎮 toggle_playback() called! Current state: {'Playing' if self.midi_player.is_playing else 'Stopped/Paused'}")
        print(f"🎵 Current notes count: {len(self.midi_notes)}")
        
        if self.midi_player.is_playing:
            print("MainWindow: Toggle playback - was playing, now stopping and resetting.")
            self.stop_playback() 
        else:
            print("MainWindow: Toggle playback - was stopped/paused, now starting from beginning.")
            if self.midi_player.get_current_position() != 0.0:
                 self.midi_player.seek(0.0)
                 self.piano_roll.set_playhead_position(0.0)
                 self.transport_controls.update_time_slider_value(0)
                 self.transport_controls.update_position_label(0)
            self.start_playback()
    
    def start_playback(self):
        if not self.midi_player.notes and self.midi_notes:
            print("FIXING: Re-setting notes before playback")
            self.midi_player.set_notes(self.midi_notes)
        time.sleep(0.1)
        self.midi_player.play()
        self.transport_controls.set_playing_state(True)
        self.update_timer_interval()
        self.playback_timer.start()
    
    def pause_playback(self):
        self.midi_player.pause()
        self.transport_controls.set_playing_state(False)
        self.playback_timer.stop()
    
    def stop_playback(self):
        self.midi_player.stop()
        self.transport_controls.set_playing_state(False)
        self.playback_timer.stop()
        self.transport_controls.update_time_slider_value(0)
        self.transport_controls.update_position_label(0)
        self.piano_roll.set_playhead_position(0)
    
    def update_playback_position(self):
        position = self.midi_player.get_current_position()
        slider_value_ms = int(position * 1000)
        self.transport_controls.update_time_slider_value(slider_value_ms)
        self.transport_controls.update_position_label(position)
        self.piano_roll.set_playhead_position(position)
        if hasattr(self, 'total_duration') and position >= self.total_duration and self.midi_player.is_playing:
            self.stop_playback()

    @Slot(float)
    def slider_position_changed_slot(self, position_seconds):
        self.midi_player.seek(position_seconds)
        self.transport_controls.update_position_label(position_seconds)
        self.piano_roll.set_playhead_position(position_seconds)

    @Slot(int)
    def bpm_changed_slot(self, new_bpm):
        self.bpm = new_bpm
        self.piano_roll.set_bpm(new_bpm)
        self.update_slider_range()
        self.update_timer_interval()
        if hasattr(self.midi_player, 'set_tempo'):
            self.midi_player.set_tempo(new_bpm)

    @Slot(int)
    def instrument_changed_slot(self, program_num: int):
        """Handles instrument change from the transport controls."""
        if hasattr(self.midi_player, 'set_instrument'):
            print(f"MainWindow: Instrument changed to program {program_num}")
            self.midi_player.set_instrument(program_num)
        else:
            print(f"MainWindow: MidiPlayer does not have set_instrument method.")

    @Slot(int)
    def volume_changed_slot(self, volume_percentage: int):
        """Handles volume change from the transport controls."""
        volume_float = volume_percentage / 100.0
        if hasattr(self.midi_player, 'set_volume'):
            self.midi_player.set_volume(volume_float)
        else:
            print(f"MainWindow: MidiPlayer does not have set_volume method.")
    
    @Slot(bool)
    def toggle_ai_mode(self, is_ai_mode: bool):
        """Toggle between Plugin Manager and AI Studio modes"""
        if is_ai_mode:
            # Switch to AI Studio
            if hasattr(self, 'plugin_manager_panel'):
                self.plugin_manager_panel.setVisible(False)
            if hasattr(self, 'ai_studio_panel'):
                self.ai_studio_panel.setVisible(True)
                # Update AI Studio with current notes
                self.ai_studio_panel.set_current_notes(self.midi_notes)
                # Ensure it's dockable if it was floating
                if self.ai_studio_panel.isFloating():
                    # If floating, make sure it still has all features enabled
                    self.ai_studio_panel.setFeatures(
                        QDockWidget.DockWidgetMovable | 
                        QDockWidget.DockWidgetFloatable | 
                        QDockWidget.DockWidgetClosable
                    )
            print("MainWindow: Switched to AI Studio mode")
        else:
            # Switch to Plugin Manager
            if hasattr(self, 'ai_studio_panel'):
                self.ai_studio_panel.setVisible(False)
            if hasattr(self, 'plugin_manager_panel'):
                self.plugin_manager_panel.setVisible(True)
                # Update Plugin Manager with current notes
                self.plugin_manager_panel.set_current_notes(self.midi_notes)
                # Ensure it's dockable if it was floating
                if self.plugin_manager_panel.isFloating():
                    # If floating, make sure it still has all features enabled
                    self.plugin_manager_panel.setFeatures(
                        QDockWidget.DockWidgetMovable | 
                        QDockWidget.DockWidgetFloatable | 
                        QDockWidget.DockWidgetClosable
                    )
            print("MainWindow: Switched to Plugin Manager mode")
    
    def update_timer_interval(self):
        base_interval = 16
        scaled_interval = min(30, max(5, int(base_interval * (120 / max(1, self.bpm)))))
        was_active = self.playback_timer.isActive()
        if was_active:
            self.playback_timer.stop()
        self.playback_timer.setInterval(scaled_interval)
        if was_active:
            self.playback_timer.start()
    
    def update_slider_range(self):
        if hasattr(self, 'total_duration'):
            scaled_duration_ms = int(self.total_duration * 1000)
            if hasattr(self, 'transport_controls'):
                self.transport_controls.update_time_slider_maximum(scaled_duration_ms)

    def closeEvent(self, event):
        """Clean up resources when window is closed."""
        # Remove global event filter before closing
        if hasattr(self, 'global_hotkey_filter'):
            QApplication.instance().removeEventFilter(self.global_hotkey_filter)
            print("Global spacebar event filter removed.")
        
        # Clean up transport controls temporary files
        if hasattr(self, 'transport_controls') and hasattr(self.transport_controls, 'cleanup_temporary_files'):
            print("MainWindow: Cleaning up transport controls temporary MIDI files...")
            self.transport_controls.cleanup_temporary_files()
        
        # Call parent cleanup
        super().closeEvent(event)


# Example usage
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PianoRollMainWindow()
    window.show()
    sys.exit(app.exec())