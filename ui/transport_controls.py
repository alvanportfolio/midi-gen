from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QStyle, QFrame, QComboBox, QButtonGroup,
    QFileDialog, QMessageBox, QToolButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QUrl, QMimeData
from PySide6.QtGui import QFont, QIcon, QDrag
from ui.custom_widgets import ModernSlider, ModernIconButton, ModernButton, DragExportButton
from ui.model_downloader import ModelDownloaderDialog
from config import theme, constants
import tempfile
import os
from datetime import datetime
from export_utils import export_to_midi

class ModernSeparator(QFrame):
    """Compact modern separator line"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.VLine)
        self.setFixedWidth(1)
        self.setFixedHeight(40)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0),
                    stop: 0.3 rgba(255, 255, 255, 25),
                    stop: 0.7 rgba(255, 255, 255, 25),
                    stop: 1 rgba(255, 255, 255, 0)
                );
                border: none;
                margin: 4px 0px;
            }}
        """)

class CompactControlGroup(QWidget):
    """Compact control group with subtle glassmorphism"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CompactControlGroup {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 6),
                    stop: 1 rgba(255, 255, 255, 3)
                );
                border: 1px solid rgba(255, 255, 255, 8);
                border-radius: {theme.BORDER_RADIUS_M}px;
            }}
        """)

class TransportControls(QWidget):
    """Modern compact transport controls with responsive design"""

    # Signals
    playClicked = Signal()
    pauseClicked = Signal()
    stopClicked = Signal()
    seekPositionChanged = Signal(float)
    bpmChangedSignal = Signal(int)
    instrumentChangedSignal = Signal(int)
    volumeChangedSignal = Signal(int)
    aiModeToggled = Signal(bool)
    clearNotesClicked = Signal()
    exportClicked = Signal()
    exportDragged = Signal()
    modelDownloaderOpened = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50) 
        self.setMaximumHeight(56) 
        
        # Modern compact styling
        self.setStyleSheet(f"""
            TransportControls {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(42, 42, 47, 92),
                    stop: 0.5 rgba(38, 38, 43, 88),
                    stop: 1 rgba(34, 34, 39, 92)
                );
                border-top: 1px solid rgba(255, 255, 255, 8);
                border-bottom: 1px solid rgba(0, 0, 0, 25);
            }}
        """)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(theme.PADDING_M, theme.PADDING_S, theme.PADDING_M, theme.PADDING_S)
        layout.setSpacing(theme.PADDING_M)

        # Load icons
        self.play_icon = QIcon(theme.PLAY_ICON_PATH)
        self.pause_icon = QIcon(theme.PAUSE_ICON_PATH)
        self.stop_icon = QIcon(theme.STOP_ICON_PATH)
        self.clear_icon = QIcon(theme.CLEAR_ICON_PATH)
        self.file_icon = QIcon(theme.FILE_ICON_PATH)
        
        # === PLAYBACK CONTROLS ===
        playback_group = CompactControlGroup()
        playback_layout = QHBoxLayout(playback_group)
        playback_layout.setContentsMargins(theme.PADDING_S, theme.PADDING_XS, theme.PADDING_S, theme.PADDING_XS)
        playback_layout.setSpacing(theme.PADDING_XS)
        
        button_size = (32, 32)
        
        self.play_button = self._create_modern_icon_button(
            self.play_icon, "Play (Space)", button_size, accent=True
        )
        self.play_button.setCheckable(True) 
        self.play_button.clicked.connect(self._handle_play_pause)
        playback_layout.addWidget(self.play_button)

        self.stop_button = self._create_modern_icon_button(
            self.stop_icon, "Stop", button_size
        )
        self.stop_button.clicked.connect(self.stopClicked)
        playback_layout.addWidget(self.stop_button)
        
        layout.addWidget(playback_group)
        layout.addWidget(ModernSeparator())
        
        # === TIMELINE ===
        timeline_group = CompactControlGroup()
        timeline_layout = QHBoxLayout(timeline_group)
        timeline_layout.setContentsMargins(theme.PADDING_S, theme.PADDING_XS, theme.PADDING_S, theme.PADDING_XS)
        timeline_layout.setSpacing(theme.PADDING_S)

        self.position_label = QLabel("0:00.0")
        self.position_label.setFont(QFont(theme.FONT_FAMILY_MONOSPACE, theme.FONT_SIZE_XS))
        self.position_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.ACCENT_PRIMARY_COLOR.name()}; 
                background: rgba(255, 255, 255, 8);
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: {theme.BORDER_RADIUS_S}px;
                padding: 2px 6px;
                min-width: 50px;
                max-width: 60px;
            }}
        """)
        self.position_label.setAlignment(Qt.AlignCenter)
        timeline_layout.addWidget(self.position_label)

        self.time_slider = self._create_modern_slider()
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(1000) 
        self.time_slider.setFixedHeight(16)
        self.time_slider.setMaximumWidth(300)  # Limit maximum width
        self.time_slider.setMinimumWidth(150)  # Set minimum width
        self.time_slider.valueChanged.connect(self._handle_slider_change)
        timeline_layout.addWidget(self.time_slider, 0)  # Don't expand
        
        # Add spacer to absorb extra space
        timeline_layout.addStretch(1)
        
        layout.addWidget(timeline_group, 0)  # Don't expand timeline group
        layout.addWidget(ModernSeparator())

        # === BPM CONTROLS ===
        bpm_group = CompactControlGroup()
        bpm_layout = QVBoxLayout(bpm_group)
        bpm_layout.setContentsMargins(theme.PADDING_S, 2, theme.PADDING_S, 2)
        bpm_layout.setSpacing(1)

        bpm_header = QHBoxLayout()
        bpm_header.setSpacing(theme.PADDING_XS)
        
        bpm_label = QLabel("BPM")
        bpm_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS))
        bpm_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        bpm_header.addWidget(bpm_label)
        
        self.bpm_value_label = QLabel("120")
        self.bpm_value_label.setFont(QFont(theme.FONT_FAMILY_MONOSPACE, theme.FONT_SIZE_XS, theme.FONT_WEIGHT_BOLD))
        self.bpm_value_label.setStyleSheet(f"color: {theme.ACCENT_PRIMARY_COLOR.name()};")
        self.bpm_value_label.setAlignment(Qt.AlignRight)
        bpm_header.addWidget(self.bpm_value_label)
        
        bpm_layout.addLayout(bpm_header)

        self.bpm_slider = self._create_modern_slider()
        self.bpm_slider.setRange(40, 240)
        self.bpm_slider.setValue(120)
        self.bpm_slider.setFixedWidth(70)
        self.bpm_slider.setFixedHeight(14)
        self.bpm_slider.valueChanged.connect(self._handle_bpm_change)
        bpm_layout.addWidget(self.bpm_slider)

        layout.addWidget(bpm_group)
        layout.addWidget(ModernSeparator())

        # === INSTRUMENT SELECTOR ===
        instrument_group = CompactControlGroup()
        instrument_layout = QVBoxLayout(instrument_group)
        instrument_layout.setContentsMargins(theme.PADDING_S, 2, theme.PADDING_S, 2)
        instrument_layout.setSpacing(1)

        instrument_label = QLabel("Instrument")
        instrument_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS))
        instrument_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        instrument_layout.addWidget(instrument_label)

        self.instrument_selector = self._create_modern_combobox()
        for name in constants.INSTRUMENT_PRESETS.keys():
            self.instrument_selector.addItem(name)
        
        default_instrument_name = constants.DEFAULT_INSTRUMENT_NAME
        if default_instrument_name in constants.INSTRUMENT_PRESETS:
            self.instrument_selector.setCurrentText(default_instrument_name)

        self.instrument_selector.currentTextChanged.connect(self._handle_instrument_change)
        instrument_layout.addWidget(self.instrument_selector)
        
        layout.addWidget(instrument_group)
        layout.addWidget(ModernSeparator())

        # === VOLUME CONTROLS ===
        volume_group = CompactControlGroup()
        volume_layout = QVBoxLayout(volume_group)
        volume_layout.setContentsMargins(theme.PADDING_S, 2, theme.PADDING_S, 2)
        volume_layout.setSpacing(1)

        volume_header = QHBoxLayout()
        volume_header.setSpacing(theme.PADDING_XS)
        
        volume_label = QLabel("VOL")
        volume_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS))
        volume_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        volume_header.addWidget(volume_label)
        
        self.volume_value_label = QLabel("50%")
        self.volume_value_label.setFont(QFont(theme.FONT_FAMILY_MONOSPACE, theme.FONT_SIZE_XS, theme.FONT_WEIGHT_BOLD))
        self.volume_value_label.setStyleSheet(f"color: {theme.ACCENT_PRIMARY_COLOR.name()};")
        self.volume_value_label.setAlignment(Qt.AlignRight)
        volume_header.addWidget(self.volume_value_label)
        
        volume_layout.addLayout(volume_header)

        self.volume_slider = self._create_modern_slider()
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(70)
        self.volume_slider.setFixedHeight(14)
        self.volume_slider.setToolTip("Adjust playback volume")
        self.volume_slider.valueChanged.connect(self._handle_volume_change)
        volume_layout.addWidget(self.volume_slider)

        layout.addWidget(volume_group)
        layout.addWidget(ModernSeparator())

        # === MODE TOGGLE ===
        mode_group = CompactControlGroup()
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(theme.PADDING_XS, theme.PADDING_XS, theme.PADDING_XS, theme.PADDING_XS)
        mode_layout.setSpacing(2)
        
        self.mode_toggle_group = QButtonGroup()
        
        self.plugin_mode_button = self._create_compact_toggle_button("🎛️", "Plugin Manager")
        self.plugin_mode_button.setChecked(True)
        self.plugin_mode_button.clicked.connect(lambda: self._handle_mode_toggle(False))
        self.mode_toggle_group.addButton(self.plugin_mode_button, 0)
        mode_layout.addWidget(self.plugin_mode_button)
        
        self.ai_mode_button = self._create_compact_toggle_button("🤖", "AI Studio")
        self.ai_mode_button.clicked.connect(lambda: self._handle_mode_toggle(True))
        self.mode_toggle_group.addButton(self.ai_mode_button, 1)
        mode_layout.addWidget(self.ai_mode_button)
        
        layout.addWidget(mode_group)
        layout.addWidget(ModernSeparator())
        
        # === ACTION BUTTONS ===
        actions_group = CompactControlGroup()
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setContentsMargins(theme.PADDING_S, theme.PADDING_XS, theme.PADDING_S, theme.PADDING_XS)
        actions_layout.setSpacing(theme.PADDING_XS)
        
        action_button_size = (28, 28)
        
        self.model_downloader_button = self._create_compact_action_button(
            "📥", "Model Downloader", action_button_size
        )
        self.model_downloader_button.clicked.connect(self._handle_model_downloader)
        actions_layout.addWidget(self.model_downloader_button)
        
        self.export_button = self._create_compact_export_button(action_button_size)
        self.export_button.clicked.connect(self._handle_export_click)
        self.export_button.dragInitiated.connect(self._handle_export_drag)
        actions_layout.addWidget(self.export_button)
        
        self.clear_button = self._create_modern_icon_button(
            self.clear_icon, "Clear All Notes", action_button_size, warning=True
        )
        self.clear_button.clicked.connect(self._handle_clear_notes)
        actions_layout.addWidget(self.clear_button)
        
        layout.addWidget(actions_group)

        self._is_playing = False
        self.current_notes = []
        self.temp_files_to_clean = []
        self.temp_midi_dir = os.path.join(tempfile.gettempdir(), "pianoroll_transport_midi_exports")
        os.makedirs(self.temp_midi_dir, exist_ok=True)

    def _create_modern_icon_button(self, icon, tooltip, size, accent=False, warning=False):
        """Create a compact modern icon button"""
        button = ModernIconButton(icon=icon, tooltip=tooltip, fixed_size=size)
        
        if accent:
            bg_color = f"rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 160)"
            hover_color = f"rgba({theme.ACCENT_HOVER_COLOR.red()}, {theme.ACCENT_HOVER_COLOR.green()}, {theme.ACCENT_HOVER_COLOR.blue()}, 180)"
            border_color = f"rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 80)"
        elif warning:
            bg_color = "rgba(220, 100, 100, 100)"
            hover_color = "rgba(240, 120, 120, 130)"
            border_color = "rgba(220, 100, 100, 60)"
        else:
            bg_color = "rgba(255, 255, 255, 12)"
            hover_color = "rgba(255, 255, 255, 20)"
            border_color = "rgba(255, 255, 255, 15)"
        
        button.setStyleSheet(f"""
            QToolButton {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: {size[0] // 2}px;
            }}
            QToolButton:hover {{
                background: {hover_color};
                border: 1px solid rgba(255, 255, 255, 25);
            }}
            QToolButton:pressed {{
                background: rgba(255, 255, 255, 25);
            }}
            QToolButton:checked {{
                background: {hover_color};
                border: 1px solid rgba(255, 255, 255, 35);
            }}
        """)
        
        return button

    def _create_compact_toggle_button(self, text, tooltip):
        """Create a compact toggle button"""
        button = ModernButton(text)
        button.setCheckable(True)
        button.setFixedSize(QSize(32, 24))
        button.setToolTip(tooltip)
        
        button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 8);
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: {theme.BORDER_RADIUS_S}px;
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 20);
            }}
            QPushButton:checked {{
                background: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 140);
                border: 1px solid rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 80);
                color: {theme.ACCENT_TEXT_COLOR.name()};
            }}
        """)
        
        return button

    def _create_compact_action_button(self, text, tooltip, size):
        """Create a compact action button"""
        button = ModernButton(text)
        button.setFixedSize(QSize(size[0], size[1]))
        button.setToolTip(tooltip)
        
        button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 10);
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: {theme.BORDER_RADIUS_S}px;
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 25);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 25);
            }}
        """)
        
        return button

    def _create_compact_export_button(self, size):
        """Create a compact export button with drag capability"""
        button = DragExportButton(
            icon=self.file_icon,
            tooltip="Export MIDI", 
            fixed_size=size
        )
        button.setIconSize(QSize(14, 14))
        
        button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(100, 200, 120, 100);
                border: 1px solid rgba(100, 200, 120, 60);
                border-radius: {theme.BORDER_RADIUS_S}px;
                color: white;
            }}
            QPushButton:hover {{
                background: rgba(120, 220, 140, 120);
                border: 1px solid rgba(120, 220, 140, 80);
            }}
            QPushButton:pressed {{
                background: rgba(80, 180, 100, 130);
            }}
            QPushButton:disabled {{
                background: rgba(100, 100, 100, 50);
                border: 1px solid rgba(100, 100, 100, 30);
                color: rgba(200, 200, 200, 80);
            }}
        """)
        
        return button

    def _create_modern_slider(self):
        """Create a compact modern slider"""
        slider = ModernSlider(Qt.Horizontal)
        
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 4px;
                background: rgba(255, 255, 255, 8);
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: 2px;
            }}
            
            QSlider::handle:horizontal {{
                background: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 180);
                width: 14px;
                height: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
                border: 2px solid rgba(255, 255, 255, 30);
            }}
            QSlider::handle:horizontal:hover {{
                background: rgba({theme.ACCENT_HOVER_COLOR.red()}, {theme.ACCENT_HOVER_COLOR.green()}, {theme.ACCENT_HOVER_COLOR.blue()}, 200);
                border: 2px solid rgba(255, 255, 255, 45);
            }}
            QSlider::handle:horizontal:pressed {{
                background: rgba({theme.ACCENT_PRESSED_COLOR.red()}, {theme.ACCENT_PRESSED_COLOR.green()}, {theme.ACCENT_PRESSED_COLOR.blue()}, 220);
            }}
            
            QSlider::sub-page:horizontal {{
                background: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 100);
                border-radius: 2px;
            }}
            
            QSlider::add-page:horizontal {{
                background: rgba(255, 255, 255, 6);
                border-radius: 2px;
            }}
        """)
        
        return slider

    def _create_modern_combobox(self):
        """Create a compact modern combobox"""
        combo = QComboBox()
        combo.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS))
        combo.setFixedWidth(90)
        combo.setFixedHeight(20)
        
        combo.setStyleSheet(f"""
            QComboBox {{
                background: rgba(255, 255, 255, 10);
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: {theme.BORDER_RADIUS_S}px;
                padding: 2px 4px;
            }}
            QComboBox:hover {{
                background: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 25);
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 16px;
                border-left-width: 1px;
                border-left-color: rgba(255, 255, 255, 15);
                border-left-style: solid;
                border-top-right-radius: {theme.BORDER_RADIUS_S}px;
                border-bottom-right-radius: {theme.BORDER_RADIUS_S}px;
            }}
            QComboBox::down-arrow {{
                image: url({theme.DROPDOWN_ICON_PATH});
                width: 8px;
                height: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: rgba(40, 40, 45, 240);
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                border: 1px solid rgba(255, 255, 255, 25);
                border-radius: {theme.BORDER_RADIUS_S}px;
                selection-background-color: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 120);
                selection-color: {theme.ACCENT_TEXT_COLOR.name()};
                outline: 0px;
            }}
        """)
        
        return combo

    def _handle_instrument_change(self, instrument_name: str):
        if instrument_name in constants.INSTRUMENT_PRESETS:
            program_num = constants.INSTRUMENT_PRESETS[instrument_name]
            self.instrumentChangedSignal.emit(program_num)

    def _handle_play_pause(self):
        if self.play_button.isChecked() and not self.current_notes:
            self.play_button.setChecked(False)
            QMessageBox.information(self, "No Notes", "Add some notes to the piano roll before playing.")
            return
            
        if self.play_button.isChecked():
            self.playClicked.emit()
        else:
            self.pauseClicked.emit()

    def _handle_slider_change(self, value):
        position_seconds = value / 1000.0 
        self.seekPositionChanged.emit(position_seconds)

    def _handle_bpm_change(self, value):
        self.bpm_value_label.setText(str(value))
        self.bpmChangedSignal.emit(value)

    def _handle_volume_change(self, value: int):
        self.volume_value_label.setText(f"{value}%")
        self.volumeChangedSignal.emit(value)

    def _handle_mode_toggle(self, is_ai_mode: bool):
        if is_ai_mode:
            self.ai_mode_button.setChecked(True)
            self.plugin_mode_button.setChecked(False)
        else:
            self.plugin_mode_button.setChecked(True)
            self.ai_mode_button.setChecked(False)
        
        self.aiModeToggled.emit(is_ai_mode)
    
    def _handle_clear_notes(self):
        if not self.current_notes:
            QMessageBox.information(self, "No Notes", "There are no notes to clear.")
            return
            
        reply = QMessageBox.question(
            self, 
            "Clear All Notes", 
            "Are you sure you want to clear all notes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print("Transport Controls: Clear all notes button clicked")
            self.clearNotesClicked.emit()
    
    def _handle_model_downloader(self):
        try:
            dialog = ModelDownloaderDialog(self)
            dialog.exec()
            self.modelDownloaderOpened.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Model Downloader:\n{str(e)}")

    def _handle_export_click(self):
        if not self.current_notes:
            QMessageBox.warning(self, "No Notes", "No notes to export.")
            return
        
        suggested_filename = "midi-gen_exported_melody.mid"
        
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
        if not self.current_notes:
            return

        temp_file_path = ""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            with tempfile.NamedTemporaryFile(
                dir=self.temp_midi_dir,
                delete=False, 
                suffix=".mid", 
                prefix=f"midi-gen_{timestamp}_"
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
        self.current_notes = notes
        has_notes = len(notes) > 0 if notes else False
        self.export_button.setEnabled(has_notes)
        
        if self._is_playing and not has_notes:
            self.stop_button.click()

    def cleanup_temporary_files(self):
        cleaned_count = 0
        for f_path in list(self.temp_files_to_clean):
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
            print(f"Could not remove temporary MIDI directory {self.temp_midi_dir}: {e}")

    @Slot(bool)
    def set_playing_state(self, playing):
        self._is_playing = playing
        self.play_button.setChecked(playing)
        if playing:
            self.play_button.setIcon(self.pause_icon)
            self.play_button.setToolTip("Pause (Space)")
        else:
            self.play_button.setIcon(self.play_icon)
            self.play_button.setToolTip("Play (Space)")
            if not self.play_button.signalsBlocked():
                 self.play_button.setChecked(False)

    @Slot(float)
    def update_position_label(self, position_seconds):
        minutes = int(position_seconds) // 60
        seconds = position_seconds % 60
        self.position_label.setText(f"{minutes}:{seconds:04.1f}")

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