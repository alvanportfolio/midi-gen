# Updated piano_roll.py with plugin manager integration
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
from plugin_manager import PluginManager
from export_utils import export_to_midi

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

class PluginParameterDialog(QDialog):
    """Dialog for configuring plugin parameters"""
    
    def __init__(self, plugin, current_params=None, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.params = current_params or {}
        self.param_widgets = {}
        
        self.setWindowTitle(f"Configure {plugin.get_name()}")
        self.resize(400, 300)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create form layout for parameters
        form_layout = QFormLayout()
        
        # Add parameter widgets
        param_info = plugin.get_parameter_info()
        for param_name, param_config in param_info.items():
            # Create widget based on parameter type
            widget = self._create_param_widget(param_name, param_config)
            if widget:
                form_layout.addRow(param_config.get("description", param_name), widget)
                self.param_widgets[param_name] = widget
        
        layout.addLayout(form_layout)
        
        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_param_widget(self, param_name, param_config):
        """Create a widget for the parameter based on its type"""
        param_type = param_config.get("type", "str")
        current_value = self.params.get(param_name, param_config.get("default"))
        
        if param_type == "int":
            widget = QSpinBox()
            widget.setMinimum(param_config.get("min", 0))
            widget.setMaximum(param_config.get("max", 100))
            widget.setValue(current_value or param_config.get("default", 0))
            return widget
        
        elif param_type == "float":
            widget = QDoubleSpinBox()
            widget.setMinimum(param_config.get("min", 0.0))
            widget.setMaximum(param_config.get("max", 1.0))
            widget.setSingleStep(0.1)
            widget.setDecimals(2)
            widget.setValue(current_value or param_config.get("default", 0.0))
            return widget
        
        elif param_type == "bool":
            widget = QCheckBox()
            widget.setChecked(current_value if current_value is not None else param_config.get("default", False))
            return widget
        
        elif param_type == "list":
            widget = QComboBox()
            options = param_config.get("options", [])
            widget.addItems(options)
            
            # Set current value
            if current_value:
                index = options.index(current_value) if current_value in options else 0
                widget.setCurrentIndex(index)
            else:
                default_value = param_config.get("default")
                index = options.index(default_value) if default_value in options else 0
                widget.setCurrentIndex(index)
            
            return widget
        
        elif param_type == "str":
            # Default to combobox if options provided, otherwise could use QLineEdit
            if "options" in param_config:
                widget = QComboBox()
                options = param_config.get("options", [])
                widget.addItems(options)
                
                # Set current value
                if current_value:
                    index = options.index(current_value) if current_value in options else 0
                    widget.setCurrentIndex(index)
                else:
                    default_value = param_config.get("default")
                    index = options.index(default_value) if default_value in options else 0
                    widget.setCurrentIndex(index)
                
                return widget
        
        return None
    
    def get_parameter_values(self):
        """Get the current parameter values from the widgets"""
        values = {}
        
        for param_name, widget in self.param_widgets.items():
            param_info = self.plugin.get_parameter_info().get(param_name, {})
            param_type = param_info.get("type", "str")
            
            if param_type == "int":
                values[param_name] = widget.value()
            elif param_type == "float":
                values[param_name] = widget.value()
            elif param_type == "bool":
                values[param_name] = widget.isChecked()
            elif param_type == "list" or param_type == "str":
                if isinstance(widget, QComboBox):
                    values[param_name] = widget.currentText()
            
        return values

class PluginManagerPanel(QDockWidget):
    """Dockable panel for managing plugins"""
    
    # Signal emitted when a plugin generates notes
    notesGenerated = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__("Plugin Manager", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        # Create plugin manager
        self.plugin_manager = PluginManager()
        
        # Create widget for the dock
        self.dock_content = QWidget()
        self.setWidget(self.dock_content)
        
        # Create layout
        layout = QVBoxLayout(self.dock_content)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Add plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.setStyleSheet("""
            QListWidget {
                background-color: #1c1c20;
                color: #e0e0e0;
                border: 1px solid #3a3a45;
                border-radius: 4px;
            }
            
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3a3a45;
            }
            
            QListWidget::item:selected {
                background-color: #3a3a60;
            }
            
            QListWidget::item:hover {
                background-color: #2a2a30;
            }
        """)
        layout.addWidget(self.plugin_list)
        
        # Load plugins
        self._load_plugins()
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.configure_button = QPushButton("Configure")
        self.configure_button.clicked.connect(self._configure_plugin)
        button_layout.addWidget(self.configure_button)
        
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self._generate_notes)
        button_layout.addWidget(self.generate_button)
        
        self.export_button = QPushButton("Export MIDI")
        self.export_button.clicked.connect(self._export_midi)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        # Store plugin parameters
        self.plugin_params = {}
        
        # Store current notes
        self.current_notes = []
    
    def _load_plugins(self):
        """Load plugins into the list widget"""
        self.plugin_list.clear()
        
        for plugin_info in self.plugin_manager.get_plugin_list():
            item = QListWidgetItem(f"{plugin_info['name']} v{plugin_info['version']}")
            item.setData(Qt.UserRole, plugin_info['id'])
            item.setToolTip(plugin_info['description'])
            self.plugin_list.addItem(item)
    
    def set_current_notes(self, notes):
        """Set the current notes for use with plugins"""
        self.current_notes = notes
    
    def _configure_plugin(self):
        """Configure the selected plugin"""
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            return
        
        plugin_id = selected_items[0].data(Qt.UserRole)
        plugin = self.plugin_manager.get_plugin(plugin_id)
        
        if not plugin:
            return
        
        # Get current parameters for this plugin
        current_params = self.plugin_params.get(plugin_id, {})
        
        # Create and show parameter dialog
        dialog = PluginParameterDialog(plugin, current_params, self)
        if dialog.exec() == QDialog.Accepted:
            # Store parameters
            params = dialog.get_parameter_values()
            self.plugin_params[plugin_id] = params
    
    def _generate_notes(self):
        """Generate notes using the selected plugin"""
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Plugin Selected", "Please select a plugin from the list.")
            return
        
        plugin_id = selected_items[0].data(Qt.UserRole)
        parameters = self.plugin_params.get(plugin_id, {})
        
        try:
            # Generate notes
            generated_notes = self.plugin_manager.generate_notes(
                plugin_id, 
                existing_notes=self.current_notes,
                parameters=parameters
            )
            
            # Emit signal with generated notes
            self.notesGenerated.emit(generated_notes)
            
            # Update current notes
            self.current_notes = generated_notes
            
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Error generating notes: {str(e)}")
    
    def _export_midi(self):
        """Export current notes to a MIDI file"""
        if not self.current_notes:
            QMessageBox.warning(self, "No Notes", "There are no notes to export.")
            return
        
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export MIDI", "", "MIDI Files (*.mid);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Add .mid extension if not present
        if not file_path.lower().endswith('.mid'):
            file_path += '.mid'
        
        try:
            # Export notes
            export_to_midi(self.current_notes, file_path)
            QMessageBox.information(self, "Export Successful", f"MIDI file exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting MIDI file: {str(e)}")

class PianoRollWindow(QMainWindow):
    """Piano roll window that displays MIDI notes graphically"""
    
    def __init__(self, midi_notes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Piano Roll with Plugin Manager")
        self.setMinimumSize(1000, 600)
        
        # Store notes data and create player
        self.midi_notes = midi_notes or []
        self.midi_player = MidiPlayer()
        self.bpm = 120  # Default BPM
        self.total_duration = 10.0  # Default duration in seconds if no notes loaded
        
        # Apply dark theme to whole window
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
        
        # Immediately set the notes in the player if available
        if self.midi_notes:
            print(f"Setting initial {len(self.midi_notes)} notes in MIDI player")
            self.midi_player.set_notes(self.midi_notes)
            
        # Create main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create piano roll display
        self.create_piano_roll_display()
        
        # Create transport controls
        self.create_transport_controls()
        
        # Create plugin manager panel
        self.create_plugin_manager()
        
        # Set up keyboard shortcuts
        self.installEventFilter(self)
        
        # Initialize playback timer - adjust interval based on BPM for smoother playback
        self.playback_timer = QTimer(self)
        self.update_timer_interval()  # Set initial interval based on default BPM
        self.playback_timer.timeout.connect(self.update_playback_position)
    
    def create_plugin_manager(self):
        """Create and add the plugin manager panel"""
        self.plugin_manager_panel = PluginManagerPanel(self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plugin_manager_panel)
        
        # Connect signals
        self.plugin_manager_panel.notesGenerated.connect(self.set_midi_notes)
        
        # Set initial notes in the plugin manager
        self.plugin_manager_panel.set_current_notes(self.midi_notes)
    
    def create_transport_controls(self):
        """Create transport controls (play, stop, etc.)"""
        # Create a frame for the transport controls
        transport_frame = QFrame()
        transport_frame.setFrameStyle(QFrame.NoFrame)
        transport_frame.setMaximumHeight(50)
        transport_frame.setStyleSheet("background-color: #1a1a1e;")
        
        transport_layout = QHBoxLayout(transport_frame)
        transport_layout.setContentsMargins(10, 5, 10, 5)
        transport_layout.setSpacing(10)
        
        # Play button
        self.play_button = ModernButton(self.style().standardIcon(QStyle.SP_MediaPlay), None, "Play (Space)")
        self.play_button.clicked.connect(self.toggle_playback)
        
        # Stop button
        self.stop_button = ModernButton(self.style().standardIcon(QStyle.SP_MediaStop), None, "Stop")
        self.stop_button.clicked.connect(self.stop_playback)
        
        # Position indicator
        self.position_label = QLabel("0:00.000")
        self.position_label.setStyleSheet("color: #e0e0e0; font-family: 'Consolas', monospace; font-size: 11px; min-width: 80px;")
        self.position_label.setAlignment(Qt.AlignCenter)
        
        # Time slider
        self.time_slider = ModernSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(1000)
        self.time_slider.valueChanged.connect(self.slider_position_changed)
        
        # BPM controls
        self.bpm_label = QLabel("BPM:")
        self.bpm_label.setStyleSheet("color: #e0e0e0; font-size: 11px;")
        
        self.bpm_slider = ModernSlider(Qt.Horizontal)
        self.bpm_slider.setRange(40, 240)
        self.bpm_slider.setValue(120)  # Default 120 BPM
        self.bpm_slider.setFixedWidth(100)
        self.bpm_slider.valueChanged.connect(self.bpm_changed)
        
        self.bpm_value = QLabel("120")
        self.bpm_value.setStyleSheet("color: #e0e0e0; font-size: 11px; min-width: 30px;")
        
        # Add widgets to layout
        transport_layout.addWidget(self.play_button)
        transport_layout.addWidget(self.stop_button)
        transport_layout.addSpacing(5)
        transport_layout.addWidget(self.position_label)
        transport_layout.addWidget(self.time_slider, 1)  # Give time slider more space
        
        transport_layout.addSpacing(15)
        transport_layout.addWidget(self.bpm_label)
        transport_layout.addWidget(self.bpm_slider)
        transport_layout.addWidget(self.bpm_value)
        
        self.main_layout.addWidget(transport_frame)
    
    def create_piano_roll_display(self):
        """Create the piano roll display widget"""
        # Create scroll area for piano roll
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
        
        # Create piano roll display widget
        self.piano_roll = PianoRollDisplay(self.midi_notes)
        self.piano_roll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set up scroll area
        scroll_area.setWidget(self.piano_roll)
        self.main_layout.addWidget(scroll_area, 1)  # Add with stretch
    
    def set_midi_notes(self, notes):
        """Update the piano roll with new MIDI notes"""
        if not notes:
            print("WARNING: Attempting to set empty notes list")
            return
            
        print(f"Piano roll received {len(notes)} notes")
        self.midi_notes = notes
        self.piano_roll.set_notes(notes)
        
        # Get a sample note to verify structure
        if notes:
            sample = notes[0]
            print(f"Sample note: pitch={getattr(sample, 'pitch', 'N/A')}, " +
                  f"start={getattr(sample, 'start', 'N/A')}, " +
                  f"end={getattr(sample, 'end', 'N/A')}, " +
                  f"velocity={getattr(sample, 'velocity', 'N/A')}")
        
        # Set notes in MIDI player
        self.midi_player.set_notes(notes)
        
        # Get the duration of the longest note
        max_end_time = 0
        for note in notes:
            if hasattr(note, 'end') and note.end > max_end_time:
                max_end_time = note.end
        
        # Add some padding to the maximum time and update the time slider
        max_end_time += 1.0  # Add 1 second padding
        self.total_duration = max_end_time
        self.update_slider_range()
        
        # Update plugin manager with current notes
        if hasattr(self, 'plugin_manager_panel'):
            self.plugin_manager_panel.set_current_notes(notes)

    def clear_notes(self):
        """Clears all notes from the piano roll and player."""
        print("PianoRollWindow: Clearing all notes.")
        self.midi_notes = []
        if hasattr(self, 'piano_roll'): # self.piano_roll is PianoRollDisplay instance
            self.piano_roll.set_notes([]) # Clear display
        if hasattr(self, 'midi_player'):
            self.midi_player.set_notes([]) # Clear player
        
        self.total_duration = 10.0 # Reset to default or minimum
        self.update_slider_range()
        if hasattr(self, 'piano_roll'):
            self.piano_roll.set_playhead_position(0) # Reset playhead display
        self.update_position_display(0) # Reset time display
        
        # Update plugin manager with empty notes
        if hasattr(self, 'plugin_manager_panel'):
            self.plugin_manager_panel.set_current_notes([])

    def receive_generated_note(self, note: pretty_midi.Note):
        """Receives a single generated note and updates the display."""
        if not hasattr(note, 'start') or not hasattr(note, 'end') or not hasattr(note, 'pitch'):
            print(f"PianoRollWindow: Received invalid note object: {note}")
            return

        self.midi_notes.append(note)
        
        if hasattr(self, 'piano_roll'): # self.piano_roll is PianoRollDisplay instance
            self.piano_roll.add_note(note) # This method needs to be added to PianoRollDisplay

        # Update total duration if this note extends it
        if note.end > self.total_duration:
            self.total_duration = note.end + 1.0 # Add padding
            self.update_slider_range()
        
        # For now, we don't add to midi_player live to keep Phase 1 simpler.
        # User would typically stop generation, then notes are fully set in player if needed.
        # Or, a separate "load generated notes to player" button could be added.
        
        # Update plugin manager with current notes
        if hasattr(self, 'plugin_manager_panel'):
            self.plugin_manager_panel.set_current_notes(self.midi_notes)
    
    def toggle_playback(self):
        """Toggle playback between play and pause"""
        if self.midi_player.is_playing:
            self.pause_playback()
        else:
            self.start_playback()
    
    def start_playback(self):
        """Start MIDI playback"""
        # Double-check that notes are properly set
        if not self.midi_player.notes and self.midi_notes:
            print("FIXING: Re-setting notes before playback")
            self.midi_player.set_notes(self.midi_notes)
            
        # Add a short delay to allow MIDI to initialize
        time.sleep(0.1)
        
        self.midi_player.play()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        
        # Start timer with appropriate interval
        self.update_timer_interval()
        self.playback_timer.start()
    
    def pause_playback(self):
        """Pause MIDI playback"""
        self.midi_player.pause()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playback_timer.stop()
    
    def stop_playback(self):
        """Stop MIDI playback and reset position"""
        self.midi_player.stop()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playback_timer.stop()
        self.time_slider.setValue(0)
        self.update_position_display(0)
        self.piano_roll.set_playhead_position(0)
    
    def update_playback_position(self):
        """Update UI elements with current playback position"""
        position = self.midi_player.get_current_position()
        
        # Update time slider - scaled to match the tempo
        self.time_slider.blockSignals(True)
        slider_value = int(position * 1000)  # Convert to milliseconds
        
        # Make sure slider value doesn't exceed maximum
        if slider_value > self.time_slider.maximum():
            slider_value = self.time_slider.maximum()
            
        self.time_slider.setValue(slider_value)
        self.time_slider.blockSignals(False)
        
        # Update position display
        self.update_position_display(position)
        
        # Update piano roll playhead
        self.piano_roll.set_playhead_position(position)
        
        # Check if we've reached the end of playback (with safety check)
        if hasattr(self, 'total_duration') and position >= self.total_duration and self.midi_player.is_playing:
            # Stop playback when we reach the end
            self.stop_playback()
    
    def update_position_display(self, position):
        """Update the position label with formatted time"""
        minutes = int(position) // 60
        seconds = int(position) % 60
        milliseconds = int((position - int(position)) * 1000)
        self.position_label.setText(f"{minutes}:{seconds:02}.{milliseconds:03}")
    
    def slider_position_changed(self, value):
        """Handle slider position change by user"""
        position = value / 1000.0  # Convert milliseconds to seconds
        self.midi_player.seek(position)
        self.update_position_display(position)
        self.piano_roll.set_playhead_position(position)
    
    def bpm_changed(self, value):
        """Handle BPM slider change"""
        self.bpm = value
        self.bpm_value.setText(str(value))
        self.piano_roll.set_bpm(value)
        
        # Update time slider's maximum to account for new BPM
        self.update_slider_range()
        
        # Update timer interval based on new BPM
        self.update_timer_interval()
        
        # Update MIDI player tempo
        if hasattr(self.midi_player, 'set_tempo'):
            self.midi_player.set_tempo(value)
    
    def update_timer_interval(self):
        """Adjust the playback timer interval based on current BPM for smoother updates"""
        # Calculate appropriate interval - higher BPM needs faster refresh
        # Balance between performance (not too fast) and smoothness
        base_interval = 16  # ~60fps at default 120BPM
        
        # Scale interval inversely with BPM (faster tempo = faster updates)
        # But limit to reasonable range (5ms to 30ms)
        scaled_interval = min(30, max(5, int(base_interval * (120 / max(1, self.bpm)))))
        
        # If playing, restart timer with new interval
        was_active = self.playback_timer.isActive()
        if was_active:
            self.playback_timer.stop()
            
        self.playback_timer.setInterval(scaled_interval)
        
        if was_active:
            self.playback_timer.start()
    
    def update_slider_range(self):
        """Update slider range based on BPM and total duration"""
        if hasattr(self, 'total_duration'):
            # Set time slider range to match the actual playback duration at current BPM
            # For higher BPM, the slider needs more resolution since playback is faster
            tempo_scale = self.bpm / 120.0
            scaled_duration = self.total_duration * 1000  # Convert to milliseconds
            self.time_slider.setMaximum(int(scaled_duration))
            print(f"Updated time slider range: 0-{scaled_duration}ms at BPM {self.bpm}")
    
    def eventFilter(self, obj, event):
        """Handle keyboard events for shortcuts"""
        if event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent) and event.key() == Qt.Key_Space:
                self.toggle_playback()
                return True
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event):
        """Clean up resources when window is closed"""
        self.midi_player.stop()
        self.playback_timer.stop()
        super().closeEvent(event)