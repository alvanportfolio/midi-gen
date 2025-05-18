from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QSlider, QStyle, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot
from ui.custom_widgets import ModernSlider, ModernButton

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
        self.setMaximumHeight(50)
        self.setStyleSheet("background-color: #1a1a1e;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # Play button
        self.play_button = ModernButton(self.style().standardIcon(QStyle.SP_MediaPlay), None, "Play (Space)")
        self.play_button.clicked.connect(self._handle_play_pause) # Internal handler first
        layout.addWidget(self.play_button)

        # Stop button
        self.stop_button = ModernButton(self.style().standardIcon(QStyle.SP_MediaStop), None, "Stop")
        self.stop_button.clicked.connect(self.stopClicked) # Emit signal directly
        layout.addWidget(self.stop_button)

        layout.addSpacing(5)

        # Position indicator
        self.position_label = QLabel("0:00.000")
        self.position_label.setStyleSheet("color: #e0e0e0; font-family: 'Consolas', monospace; font-size: 11px; min-width: 80px;")
        self.position_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.position_label)

        # Time slider
        self.time_slider = ModernSlider(Qt.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(1000) # Default, will be updated
        self.time_slider.valueChanged.connect(self._handle_slider_change)
        layout.addWidget(self.time_slider, 1)

        layout.addSpacing(15)

        # BPM controls
        self.bpm_label = QLabel("BPM:")
        self.bpm_label.setStyleSheet("color: #e0e0e0; font-size: 11px;")
        layout.addWidget(self.bpm_label)

        self.bpm_slider = ModernSlider(Qt.Horizontal)
        self.bpm_slider.setRange(40, 240)
        self.bpm_slider.setValue(120)
        self.bpm_slider.setFixedWidth(100)
        self.bpm_slider.valueChanged.connect(self._handle_bpm_change)
        layout.addWidget(self.bpm_slider)

        self.bpm_value_label = QLabel("120") # Renamed from self.bpm_value to avoid conflict
        self.bpm_value_label.setStyleSheet("color: #e0e0e0; font-size: 11px; min-width: 30px;")
        layout.addWidget(self.bpm_value_label)

        self._is_playing = False # Internal state for play/pause button

    def _handle_play_pause(self):
        if self._is_playing:
            self.pauseClicked.emit()
        else:
            self.playClicked.emit()
        # The main window will update our icon via set_playing_state

    def _handle_slider_change(self, value):
        position_seconds = value / 1000.0
        self.seekPositionChanged.emit(position_seconds)
        # Main window will call update_position_label

    def _handle_bpm_change(self, value):
        self.bpm_value_label.setText(str(value))
        self.bpmChangedSignal.emit(value)
        # Main window will update piano_roll.set_bpm and slider range

    @Slot(bool)
    def set_playing_state(self, playing):
        """Called by the main window to update the play button icon and internal state."""
        self._is_playing = playing
        if playing:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

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
