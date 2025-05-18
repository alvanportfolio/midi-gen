import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QSizePolicy, QSlider, QStyle, QToolButton,
    QFrame, QSpacerItem, QDockWidget, QListWidget, QListWidgetItem,
    QFormLayout, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QDialog, QDialogButtonBox, QFileDialog, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize, QEvent
from PySide6.QtGui import QKeyEvent, QColor, QPalette, QFont, QLinearGradient, QBrush
import pretty_midi
import time
import os

from note_display import PianoRollDisplay
from midi_player import MidiPlayer
# Assuming plugin_manager, export_utils are in the root or accessible via PYTHONPATH
from plugin_manager import PluginManager
from export_utils import export_to_midi
# UI components are now relative to the 'ui' package or root
from .custom_widgets import ModernSlider, ModernButton
from .plugin_dialogs import PluginParameterDialog
from .plugin_panel import PluginManagerPanel
from .transport_controls import TransportControls
from .event_handlers import MainWindowEventHandlersMixin


class PianoRollMainWindow(QMainWindow, MainWindowEventHandlersMixin):
    """Piano roll window that displays MIDI notes graphically"""
    
    def __init__(self, midi_notes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Piano Roll with Plugin Manager")
        self.setMinimumSize(1000, 600)
        
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
        
        self.installEventFilter(self)
        
        self.playback_timer = QTimer(self)
        self.update_timer_interval()
        self.playback_timer.timeout.connect(self.update_playback_position)

        # Initialize transport controls after all components are ready
        self.transport_controls.set_bpm_value(self.bpm)
        self.update_slider_range()


    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1c1c20;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 11px;
            }
            QScrollBar {
                background-color: #2a2a30;
                width: 12px;
                height: 12px;
            }
            QScrollBar::handle {
                background-color: #4a4a55;
                border-radius: 5px;
                margin: 1px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
                border: none;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
            }
            QPushButton {
                background-color: #2d2d35;
                color: #e0e0e0;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3d3d45;
            }
            QPushButton:pressed {
                background-color: #404050;
            }
        """)

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

    def _connect_transport_signals(self):
        self.transport_controls.playClicked.connect(self.start_playback)
        self.transport_controls.pauseClicked.connect(self.pause_playback)
        self.transport_controls.stopClicked.connect(self.stop_playback)
        self.transport_controls.seekPositionChanged.connect(self.slider_position_changed_slot)
        self.transport_controls.bpmChangedSignal.connect(self.bpm_changed_slot)

    def create_piano_roll_display(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1c1c20;
            }
        """)
        self.piano_roll = PianoRollDisplay(self.midi_notes)
        self.piano_roll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.setWidget(self.piano_roll)
        self.main_layout.addWidget(scroll_area, 1)
    
    def set_midi_notes(self, notes):
        if not notes:
            print("WARNING: Attempting to set empty notes list")
            return
        print(f"PianoRollMainWindow: Received {len(notes)} notes")
        self.midi_notes = notes
        self.piano_roll.set_notes(notes)
        
        if notes:
            sample = notes[0]
            # print(f"Sample note: pitch={getattr(sample, 'pitch', 'N/A')}, " +
            #       f"start={getattr(sample, 'start', 'N/A')}, " +
            #       f"end={getattr(sample, 'end', 'N/A')}, " +
            #       f"velocity={getattr(sample, 'velocity', 'N/A')}")
        
        self.midi_player.set_notes(notes)
        
        max_end_time = 0
        for note in notes:
            if hasattr(note, 'end') and note.end > max_end_time:
                max_end_time = note.end
        
        self.total_duration = max_end_time + 1.0
        self.update_slider_range()
        
        if hasattr(self, 'plugin_manager_panel'):
            self.plugin_manager_panel.set_current_notes(notes)
        
        self.transport_controls.set_bpm_value(self.bpm) # Ensure BPM display is correct
        # self.update_slider_range() # Called above

    def clear_notes(self):
        print("PianoRollMainWindow: Clearing all notes.")
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
    
    def toggle_playback(self):
        if self.midi_player.is_playing:
            self.pause_playback()
        else:
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
        else:
            pass
    
    # eventFilter and closeEvent are now inherited from MainWindowEventHandlersMixin

# Example usage (for testing, would be in main.py)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Load some initial MIDI data for testing if desired
    # initial_midi_file = "path_to_your_midi.mid" 
    # if os.path.exists(initial_midi_file):
    #     midi_data = pretty_midi.PrettyMIDI(initial_midi_file)
    #     notes_to_load = []
    #     for instrument in midi_data.instruments:
    #         if not instrument.is_drum:
    #             notes_to_load.extend(instrument.notes)
    # else:
    #     notes_to_load = []

    # window = PianoRollMainWindow(notes_to_load)
    window = PianoRollMainWindow() # Start with empty
    window.show()
    sys.exit(app.exec())
