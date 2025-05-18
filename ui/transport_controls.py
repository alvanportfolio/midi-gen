from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QStyle, QFrame
) # QPushButton and QSlider removed as ModernSlider/Button are used
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QIcon # Import QFont and QIcon
from ui.custom_widgets import ModernSlider, ModernIconButton # Use ModernIconButton
from config import theme # Import theme

class TransportControls(QWidget):
    """Transport controls for MIDI playback (play, stop, BPM, time slider)"""

    # Signals to control playback in the main window
    playClicked = Signal()
    pauseClicked = Signal()
    stopClicked = Signal()
    seekPositionChanged = Signal(float) # position in seconds
    bpmChangedSignal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50) # Use minimum height, allow expansion if needed
        self.setMaximumHeight(65) # Max height
        self.setStyleSheet(f"background-color: {theme.BG_COLOR.darker(115).name()}; border-radius: {theme.BORDER_RADIUS}px;") # Slightly darker than main BG

        layout = QHBoxLayout(self)
        layout.setContentsMargins(theme.PADDING_MEDIUM, theme.PADDING_SMALL, theme.PADDING_MEDIUM, theme.PADDING_SMALL)
        layout.setSpacing(theme.PADDING_MEDIUM)

        # Icons (using QStyle for now, could be replaced with custom icons)
        self.play_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.pause_icon = self.style().standardIcon(QStyle.SP_MediaPause)
        self.stop_icon = self.style().standardIcon(QStyle.SP_MediaStop)

        # Play button
        self.play_button = ModernIconButton(icon=self.play_icon, tooltip="Play (Space)", fixed_size=(theme.ICON_SIZE * 2, theme.ICON_SIZE * 2))
        self.play_button.setCheckable(True) # Make it checkable for play/pause state
        self.play_button.clicked.connect(self._handle_play_pause)
        layout.addWidget(self.play_button)

        # Stop button
        self.stop_button = ModernIconButton(icon=self.stop_icon, tooltip="Stop", fixed_size=(theme.ICON_SIZE * 2, theme.ICON_SIZE * 2))
        self.stop_button.clicked.connect(self.stopClicked)
        layout.addWidget(self.stop_button)

        layout.addSpacing(theme.PADDING_SMALL)
        
        # Separator line (optional)
        # line1 = QFrame()
        # line1.setFrameShape(QFrame.VLine)
        # line1.setFrameShadow(QFrame.Sunken)
        # line1.setStyleSheet(f"color: {theme.GRID_COLOR.name()};")
        # layout.addWidget(line1)

        # Position indicator
        self.position_label = QLabel("0:00.000")
        self.position_label.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL))
        self.position_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()}; min-width: 70px;")
        self.position_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.position_label)

        # Time slider
        self.time_slider = ModernSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(1000) 
        self.time_slider.valueChanged.connect(self._handle_slider_change)
        layout.addWidget(self.time_slider, 1) # Stretch factor 1

        layout.addSpacing(theme.PADDING_LARGE)
        
        # Separator line (optional)
        # line2 = QFrame()
        # line2.setFrameShape(QFrame.VLine)
        # line2.setFrameShadow(QFrame.Sunken)
        # line2.setStyleSheet(f"color: {theme.GRID_COLOR.name()};")
        # layout.addWidget(line2)

        # BPM controls
        self.bpm_label = QLabel("BPM") # Simpler label
        self.bpm_label.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL))
        self.bpm_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        layout.addWidget(self.bpm_label)

        self.bpm_slider = ModernSlider(Qt.Horizontal)
        self.bpm_slider.setRange(40, 240)
        self.bpm_slider.setValue(120)
        self.bpm_slider.setFixedWidth(80) # Slightly smaller
        self.bpm_slider.valueChanged.connect(self._handle_bpm_change)
        layout.addWidget(self.bpm_slider)

        self.bpm_value_label = QLabel("120")
        self.bpm_value_label.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL, weight=QFont.Bold if theme.FONT_WEIGHT_BOLD == "bold" else QFont.Normal))
        self.bpm_value_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()}; min-width: 25px;")
        self.bpm_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.bpm_value_label)

        self._is_playing = False

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
