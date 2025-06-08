from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QStyle, QFrame, QComboBox, QButtonGroup,
    QFileDialog, QMessageBox
) # Added QFileDialog, QMessageBox for export functionality
from PySide6.QtCore import Qt, Signal, Slot, QSize, QUrl, QMimeData
from PySide6.QtGui import QFont, QIcon, QDrag
from ui.custom_widgets import ModernSlider, ModernIconButton, ModernButton, DragExportButton
from config import theme, constants # Import theme and constants
import tempfile
import os
from export_utils import export_to_midi

class TransportControls(QWidget):
    """Transport controls for MIDI playback (play, stop, BPM, time slider)"""

    # Signals to control playback in the main window
    playClicked = Signal()
    pauseClicked = Signal()
    stopClicked = Signal()
    seekPositionChanged = Signal(float) # position in seconds
    bpmChangedSignal = Signal(int)
    instrumentChangedSignal = Signal(int) # New signal for instrument changes
    volumeChangedSignal = Signal(int) # Signal for volume changes (0-100)
    
    # New signal for AI/Plugin toggle
    aiModeToggled = Signal(bool) # True for AI mode, False for Plugin mode
    
    # Signal for clear all notes
    clearNotesClicked = Signal()
    
    # Signals for export functionality
    exportClicked = Signal()  # Signal for export button click
    exportDragged = Signal()  # Signal for export button drag

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50) 
        self.setMaximumHeight(65) 
        # Panel Styling: Use PANEL_BG_COLOR and add a top border
        self.setStyleSheet(f"""
            TransportControls {{
                background-color: {theme.PANEL_BG_COLOR.name()};
                border-top: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
                border-radius: 0px; /* No radius for a bar */
            }}
        """)

        layout = QHBoxLayout(self)
        # Margins & Spacing: Use consistent theme padding
        layout.setContentsMargins(theme.PADDING_M, theme.PADDING_S, theme.PADDING_M, theme.PADDING_S)
        layout.setSpacing(theme.PADDING_M)

        # Iconography: Load icons from theme paths
        self.play_icon = QIcon(theme.PLAY_ICON_PATH)
        self.pause_icon = QIcon(theme.PAUSE_ICON_PATH)
        self.stop_icon = QIcon(theme.STOP_ICON_PATH)
        self.clear_icon = QIcon(theme.CLEAR_ICON_PATH)
        self.file_icon = QIcon(theme.FILE_ICON_PATH)
        
        # Play button - Uses ModernIconButton, should pick up its styles
        # Icon size for transport controls might be larger, e.g., ICON_SIZE_L
        button_size = (theme.ICON_SIZE_L + theme.PADDING_S * 2, theme.ICON_SIZE_L + theme.PADDING_S * 2) # Calculate button size based on icon + padding
        
        self.play_button = ModernIconButton(icon=self.play_icon, tooltip="Play (Space)", fixed_size=button_size)
        self.play_button.setIconSize(QSize(theme.ICON_SIZE_L, theme.ICON_SIZE_L))
        self.play_button.setCheckable(True) 
        self.play_button.clicked.connect(self._handle_play_pause)
        layout.addWidget(self.play_button)

        # Stop button - Uses ModernIconButton
        self.stop_button = ModernIconButton(icon=self.stop_icon, tooltip="Stop", fixed_size=button_size)
        self.stop_button.setIconSize(QSize(theme.ICON_SIZE_L, theme.ICON_SIZE_L))
        self.stop_button.clicked.connect(self.stopClicked)
        layout.addWidget(self.stop_button)

        layout.addSpacing(theme.PADDING_S) # Adjusted spacing
        
        # Separator line (optional) - Uncommented and styled
        line1 = QFrame()
        line1.setFrameShape(QFrame.VLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet(f"color: {theme.BORDER_COLOR_NORMAL.name()};")
        layout.addWidget(line1)
        layout.addSpacing(theme.PADDING_S) # Spacing after separator

        # Position indicator - Label Styling
        self.position_label = QLabel("0:00.000")
        self.position_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M))
        self.position_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()}; min-width: 75px;") # Adjusted min-width
        self.position_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.position_label)

        # Time slider - Uses ModernSlider, should pick up its styles
        self.time_slider = ModernSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(1000) 
        self.time_slider.valueChanged.connect(self._handle_slider_change)
        layout.addWidget(self.time_slider, 1) # Stretch factor 1

        layout.addSpacing(theme.PADDING_L) # Adjusted spacing
        
        # Separator line (optional) - Uncommented and styled
        line2 = QFrame()
        line2.setFrameShape(QFrame.VLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet(f"color: {theme.BORDER_COLOR_NORMAL.name()};")
        layout.addWidget(line2)
        layout.addSpacing(theme.PADDING_S) # Spacing after separator

        # BPM controls - Label Styling
        self.bpm_label = QLabel("BPM") 
        self.bpm_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M))
        self.bpm_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        layout.addWidget(self.bpm_label)

        # BPM slider - Uses ModernSlider
        self.bpm_slider = ModernSlider(Qt.Horizontal)
        self.bpm_slider.setRange(40, 240)
        self.bpm_slider.setValue(120)
        self.bpm_slider.setFixedWidth(100) # Adjusted width
        self.bpm_slider.valueChanged.connect(self._handle_bpm_change)
        layout.addWidget(self.bpm_slider)

        # BPM value label - Label Styling
        self.bpm_value_label = QLabel("120")
        self.bpm_value_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, weight=theme.FONT_WEIGHT_BOLD))
        self.bpm_value_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()}; min-width: 30px;") # Adjusted min-width
        self.bpm_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.bpm_value_label)

        layout.addSpacing(theme.PADDING_L) # Spacing before instrument selector

        # Separator line before instrument selector
        line3 = QFrame()
        line3.setFrameShape(QFrame.VLine)
        line3.setFrameShadow(QFrame.Sunken)
        line3.setStyleSheet(f"color: {theme.BORDER_COLOR_NORMAL.name()};")
        layout.addWidget(line3)
        layout.addSpacing(theme.PADDING_S)

        # Instrument Selector
        self.instrument_label = QLabel("Instrument")
        self.instrument_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M))
        self.instrument_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        layout.addWidget(self.instrument_label)

        self.instrument_selector = QComboBox()
        self.instrument_selector.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M))
        self.instrument_selector.setFixedWidth(150) # Adjust width as needed
        # Populate with instruments from constants
        for name in constants.INSTRUMENT_PRESETS.keys():
            self.instrument_selector.addItem(name)
        
        # Set default selection
        default_instrument_name = constants.DEFAULT_INSTRUMENT_NAME
        if default_instrument_name in constants.INSTRUMENT_PRESETS:
            self.instrument_selector.setCurrentText(default_instrument_name)

        self.instrument_selector.setStyleSheet(f"""
            QComboBox {{
                background-color: {theme.STANDARD_BUTTON_BG_COLOR.name()};
                color: {theme.STANDARD_BUTTON_TEXT_COLOR.name()};
                border: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
                border-radius: {theme.BORDER_RADIUS_M}px;
                padding: {theme.PADDING_XS}px {theme.PADDING_S}px;
                min-height: {theme.ICON_SIZE_M + theme.PADDING_XS * 2}px; /* Match button height */
            }}
            QComboBox:hover {{
                background-color: {theme.STANDARD_BUTTON_HOVER_BG_COLOR.name()};
                border: 1px solid {theme.BORDER_COLOR_HOVER.name()};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {theme.ICON_SIZE_M}px;
                border-left-width: 1px;
                border-left-color: {theme.BORDER_COLOR_NORMAL.name()};
                border-left-style: solid;
                border-top-right-radius: {theme.BORDER_RADIUS_M}px;
                border-bottom-right-radius: {theme.BORDER_RADIUS_M}px;
            }}
            QComboBox::down-arrow {{
                image: url({theme.DROPDOWN_ICON_PATH}); /* Assuming a theme path for dropdown arrow */
                width: {theme.ICON_SIZE_S}px;
                height: {theme.ICON_SIZE_S}px;
            }}
            QComboBox QAbstractItemView {{ /* Style for the dropdown list */
                background-color: {theme.PANEL_BG_COLOR.name()};
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                border: 1px solid {theme.BORDER_COLOR_HOVER.name()};
                selection-background-color: {theme.ACCENT_PRIMARY_COLOR.name()};
                selection-color: {theme.ACCENT_TEXT_COLOR.name()};
                outline: 0px; /* Remove focus outline from items */
            }}
        """)
        self.instrument_selector.currentTextChanged.connect(self._handle_instrument_change)
        layout.addWidget(self.instrument_selector)

        layout.addSpacing(theme.PADDING_L)  # Spacing before volume controls

        # Separator line before volume controls
        line4 = QFrame()
        line4.setFrameShape(QFrame.VLine)
        line4.setFrameShadow(QFrame.Sunken)
        line4.setStyleSheet(f"color: {theme.BORDER_COLOR_NORMAL.name()};")
        layout.addWidget(line4)
        layout.addSpacing(theme.PADDING_S)

        # Volume Label
        self.volume_label = QLabel("Volume")
        self.volume_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M))
        self.volume_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        layout.addWidget(self.volume_label)

        # Volume Slider
        self.volume_slider = ModernSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)  # Default volume 50%
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setToolTip("Adjust playback volume")
        self.volume_slider.valueChanged.connect(self._handle_volume_change)
        layout.addWidget(self.volume_slider)

        # Volume Value Label
        self.volume_value_label = QLabel("50%")
        self.volume_value_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, weight=theme.FONT_WEIGHT_BOLD))
        self.volume_value_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()}; min-width: 35px;") # Adjusted min-width
        self.volume_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.volume_value_label)

        layout.addSpacing(theme.PADDING_L)  # Spacing before AI/Plugin toggle

        # Separator line before AI/Plugin toggle
        line5 = QFrame()
        line5.setFrameShape(QFrame.VLine)
        line5.setFrameShadow(QFrame.Sunken)
        line5.setStyleSheet(f"color: {theme.BORDER_COLOR_NORMAL.name()};")
        layout.addWidget(line5)
        layout.addSpacing(theme.PADDING_S)

        # AI/Plugin Mode Toggle
        self.mode_toggle_group = QButtonGroup()
        
        self.plugin_mode_button = ModernButton("🎛️ Plugins")
        self.plugin_mode_button.setCheckable(True)
        self.plugin_mode_button.setFixedWidth(90)
        self.plugin_mode_button.setChecked(True)  # Default to plugin mode
        self.plugin_mode_button.clicked.connect(lambda: self._handle_mode_toggle(False))
        self.mode_toggle_group.addButton(self.plugin_mode_button, 0)
        layout.addWidget(self.plugin_mode_button)
        
        self.ai_mode_button = ModernButton("🤖 AI Studio")
        self.ai_mode_button.setCheckable(True)
        self.ai_mode_button.setFixedWidth(90)
        self.ai_mode_button.clicked.connect(lambda: self._handle_mode_toggle(True))
        self.mode_toggle_group.addButton(self.ai_mode_button, 1)
        layout.addWidget(self.ai_mode_button)
        
        layout.addSpacing(theme.PADDING_S)  # Small spacing before clear button
        
        # Export Button - Icon only  
        self.export_button = DragExportButton(
            icon=self.file_icon,
            tooltip="Export to MIDI (Click to save, or drag to your DAW/folder)", 
            fixed_size=button_size
        )
        self.export_button.setIconSize(QSize(theme.ICON_SIZE_L, theme.ICON_SIZE_L))
        self.export_button.clicked.connect(self._handle_export_click)
        self.export_button.dragInitiated.connect(self._handle_export_drag)
        layout.addWidget(self.export_button)
        
        # Clear Notes Button - Icon only
        self.clear_button = ModernIconButton(
            icon=self.clear_icon, 
            tooltip="Clear All Notes", 
            fixed_size=button_size
        )
        self.clear_button.setIconSize(QSize(theme.ICON_SIZE_L, theme.ICON_SIZE_L))
        self.clear_button.clicked.connect(self._handle_clear_notes)
        layout.addWidget(self.clear_button)
        
        layout.addStretch(1) # Add stretch at the end to push controls left

        self._is_playing = False
        
        # Initialize properties for export functionality
        self.current_notes = []
        self.temp_files_to_clean = []
        self.temp_midi_dir = os.path.join(tempfile.gettempdir(), "pianoroll_transport_midi_exports")
        os.makedirs(self.temp_midi_dir, exist_ok=True)

    def _handle_instrument_change(self, instrument_name: str):
        if instrument_name in constants.INSTRUMENT_PRESETS:
            program_num = constants.INSTRUMENT_PRESETS[instrument_name]
            self.instrumentChangedSignal.emit(program_num)

    def _handle_play_pause(self):
        if self.play_button.isChecked(): # If button is now checked (meaning play was clicked)
            self.playClicked.emit()
        else: # If button is now unchecked (meaning pause was clicked or stop was called)
            self.pauseClicked.emit()
        # The main window will call set_playing_state to sync icon and tooltip

    def _handle_slider_change(self, value):
        # Assuming slider max is total duration in ms
        position_seconds = value / 1000.0 
        self.seekPositionChanged.emit(position_seconds)
        # Main window will call update_position_label

    def _handle_bpm_change(self, value):
        self.bpm_value_label.setText(str(value))
        self.bpmChangedSignal.emit(value)
        # Main window will update piano_roll.set_bpm and slider range

    def _handle_volume_change(self, value: int):
        self.volume_value_label.setText(f"{value}%")
        self.volumeChangedSignal.emit(value)
        # Main window will connect this signal to adjust actual playback volume

    def _handle_mode_toggle(self, is_ai_mode: bool):
        """Handle toggle between Plugin Manager and AI Studio modes"""
        if is_ai_mode:
            self.ai_mode_button.setChecked(True)
            self.plugin_mode_button.setChecked(False)
        else:
            self.plugin_mode_button.setChecked(True)
            self.ai_mode_button.setChecked(False)
        
        self.aiModeToggled.emit(is_ai_mode)
    
    def _handle_clear_notes(self):
        """Handle clear all notes button click"""
        print("Transport Controls: Clear all notes button clicked")
        self.clearNotesClicked.emit()

    def _handle_export_click(self):
        """Handle export button click"""
        if not self.current_notes:
            QMessageBox.warning(self, "No Notes", "No notes to export.")
            return
        
        suggested_filename = "exported_melody.mid"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export MIDI", 
            suggested_filename, 
            "MIDI Files (*.mid);;All Files (*)"
        )
        
        if not file_path: 
            return
        
        if not file_path.lower().endswith('.mid'):
            file_path += '.mid'
            
        try:
            export_to_midi(self.current_notes, file_path)
            QMessageBox.information(self, "Export Successful", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting MIDI: {str(e)}")
        finally:
            if hasattr(self.export_button, 'clearFocus'):
                self.export_button.clearFocus()

    def _handle_export_drag(self):
        """Handle export button drag"""
        if not self.current_notes:
            return

        temp_file_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.temp_midi_dir,
                delete=False, 
                suffix=".mid", 
                prefix="dragged_"
            ) as tmp_file:
                temp_file_path = tmp_file.name
            
            export_to_midi(self.current_notes, temp_file_path)
            self.temp_files_to_clean.append(temp_file_path)

            mime_data = QMimeData()
            url = QUrl.fromLocalFile(temp_file_path)
            mime_data.setUrls([url])
            
            drag = QDrag(self.export_button)
            drag.setMimeData(mime_data)
            
            result = drag.exec_(Qt.CopyAction)

        except Exception as e:
            QMessageBox.critical(self, "Drag Export Error", f"Could not prepare MIDI for dragging: {str(e)}")
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path) 
                    if temp_file_path in self.temp_files_to_clean:
                        self.temp_files_to_clean.remove(temp_file_path)
                except OSError:
                    pass 
        finally:
            if hasattr(self.export_button, 'clearFocus'):
                self.export_button.clearFocus()

    def set_current_notes(self, notes):
        """Update current notes for export functionality"""
        self.current_notes = notes
        # Enable/disable export button based on whether we have notes
        self.export_button.setEnabled(len(notes) > 0 if notes else False)

    def cleanup_temporary_files(self):
        """Cleans up temporary MIDI files created during drag operations."""
        cleaned_count = 0
        for f_path in list(self.temp_files_to_clean): # Iterate over a copy
            try:
                if os.path.exists(f_path):
                    os.remove(f_path)
                    cleaned_count += 1
                if f_path in self.temp_files_to_clean:
                    self.temp_files_to_clean.remove(f_path)
            except Exception as e:
                print(f"Error deleting temporary file {f_path}: {e}")
        
        if cleaned_count > 0:
            print(f"Cleaned up {cleaned_count} temporary MIDI files.")

        try:
            if os.path.exists(self.temp_midi_dir) and not os.listdir(self.temp_midi_dir):
                os.rmdir(self.temp_midi_dir)
                print(f"Removed temporary MIDI directory: {self.temp_midi_dir}")
        except Exception as e:
            print(f"Could not remove temporary MIDI directory {self.temp_midi_dir} (it might not be empty or access denied): {e}")

    @Slot(bool)
    def set_playing_state(self, playing):
        """Called by the main window to update the play button icon, tooltip, and internal state."""
        self._is_playing = playing # Keep internal state if needed elsewhere
        self.play_button.setChecked(playing) # Sync check state
        if playing:
            self.play_button.setIcon(self.pause_icon)
            self.play_button.setToolTip("Pause (Space)")
        else:
            self.play_button.setIcon(self.play_icon)
            self.play_button.setToolTip("Play (Space)")
            # If stop was clicked, ensure play button is unchecked
            if not self.play_button.signalsBlocked(): # Check if stop was called externally
                 self.play_button.setChecked(False)


    @Slot(float)
    def update_position_label(self, position_seconds):
        minutes = int(position_seconds) // 60
        seconds = int(position_seconds) % 60
        milliseconds = int((position_seconds - int(position_seconds)) * 1000)
        self.position_label.setText(f"{minutes}:{seconds:02}.{milliseconds:03}")

    @Slot(int)
    def update_time_slider_value(self, position_ms):
        self.time_slider.blockSignals(True)
        slider_val = min(position_ms, self.time_slider.maximum())
        self.time_slider.setValue(slider_val)
        self.time_slider.blockSignals(False)

    @Slot(int)
    def update_time_slider_maximum(self, max_ms):
        self.time_slider.setMaximum(max_ms)

    @Slot(int)
    def set_bpm_value(self, bpm):
        self.bpm_slider.blockSignals(True)
        self.bpm_slider.setValue(bpm)
        self.bpm_slider.blockSignals(False)
        self.bpm_value_label.setText(str(bpm))
