import sys
import os # For file extension check
from PySide6.QtWidgets import QWidget, QApplication, QSizePolicy, QMessageBox
from PySide6.QtCore import Qt, QRect, QSize, QPoint, Signal, QRectF, QMimeData, QUrl
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, 
    QRadialGradient, QFontMetrics, QDragEnterEvent, QDropEvent, QMouseEvent, QDragLeaveEvent, QDragMoveEvent,
    QPaintEvent # Import QPaintEvent
)
import pretty_midi
import math # Import math

from config.constants import (
    MIN_PITCH, MAX_PITCH, WHITE_KEY_WIDTH, BLACK_KEY_WIDTH,
    WHITE_KEY_HEIGHT, BLACK_KEY_HEIGHT, BASE_TIME_SCALE, DEFAULT_BPM,
    MIN_LABEL_PITCH, MAX_LABEL_PITCH
)
from config.theme import (
    BG_COLOR, GRID_COLOR, BEAT_COLOR, MEASURE_COLOR, ROW_HIGHLIGHT_COLOR, 
    KEY_GRID_COLOR, PLAYHEAD_COLOR, WHITE_KEY_COLOR, BLACK_KEY_COLOR, 
    KEY_BORDER_COLOR, NOTE_COLORS, ACCENT_COLOR, DRAG_OVERLAY_COLOR
)
from ui.drawing_utils import (
    draw_time_grid, draw_piano_keys, draw_notes, draw_playhead
)
from config import theme

class PianoRollDisplay(QWidget):
    """Widget that displays MIDI notes in a piano roll format"""
    
    notesChanged = Signal(list) 
    midiFileProcessed = Signal(list) 

    def __init__(self, notes=None, parent=None):
        super().__init__(parent)
        self.notes: list[pretty_midi.Note] = notes or []
        self.playhead_position = 0.0
        self.bpm = DEFAULT_BPM
        self.time_scale = BASE_TIME_SCALE 
        self.time_signature_numerator = 4
        self.time_signature_denominator = 4
        
        num_white_keys = 0
        for i in range(MIN_PITCH, MAX_PITCH + 1):
            if i % 12 not in [1, 3, 6, 8, 10]: 
                num_white_keys +=1
        self.setMinimumHeight((MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)

        
        self.calculate_total_width()
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAcceptDrops(True) 
        self._is_dragging_midi = False 
        self._grid_quantize_value_seconds = (60.0 / self.bpm) / 4 

    def _update_quantization_value(self):
        beats_per_second = self.bpm / 60.0
        seconds_per_beat = 1.0 / beats_per_second
        self._grid_quantize_value_seconds = seconds_per_beat / 4.0

    def set_notes(self, notes: list[pretty_midi.Note]):
        self.notes = notes if notes is not None else []
        self.calculate_total_width()
        self.notesChanged.emit(self.notes) 
        self.update()

    def add_note(self, note: pretty_midi.Note, emit_change=True): # Kept for programmatic addition
        if not isinstance(note, pretty_midi.Note):
            print(f"PianoRollDisplay: Received invalid note object type: {type(note)}")
            return
        self.notes.append(note)
        self.notes.sort(key=lambda n: (n.start, n.pitch))
        original_min_width = self.minimumWidth()
        self.calculate_total_width()
        if emit_change:
            self.notesChanged.emit(self.notes)
        self.update()
        parent_scroll_area = self.parentWidget()
        while parent_scroll_area and not hasattr(parent_scroll_area, 'horizontalScrollBar'):
            parent_scroll_area = parent_scroll_area.parentWidget()
        if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
            note_x_end_pixels = note.end * self.time_scale + WHITE_KEY_WIDTH
            scrollbar = parent_scroll_area.horizontalScrollBar()
            if note_x_end_pixels > scrollbar.value() + parent_scroll_area.viewport().width() or self.minimumWidth() > original_min_width:
                scrollbar.setValue(int(note.start * self.time_scale))
    
    # Removed delete_note_at as per feedback

    def set_playhead_position(self, position):
        if self.playhead_position != position:
            self.playhead_position = position
            self.update() 
    
    def set_bpm(self, bpm):
        if bpm <= 0 or self.bpm == bpm: return
        self.bpm = bpm
        self.time_scale = BASE_TIME_SCALE * (DEFAULT_BPM / self.bpm)
        self._update_quantization_value()
        self.calculate_total_width()
        self.update()

    def set_time_signature(self, numerator: int, denominator: int):
        if numerator <= 0 or denominator <= 0: return
        if self.time_signature_numerator == numerator and self.time_signature_denominator == denominator: return
        self.time_signature_numerator = numerator
        self.time_signature_denominator = denominator
        self._update_quantization_value()
        self.calculate_total_width()
        self.update()
    
    def calculate_total_width(self):
        max_time = 0.0
        if self.notes:
            for note in self.notes:
                if hasattr(note, 'end') and note.end > max_time:
                    max_time = note.end
        min_visible_bars = 4
        min_time_from_bars = min_visible_bars * self.time_signature_numerator * (60.0 / self.bpm)
        self.total_time = max(max_time + 2.0, min_time_from_bars)
        new_min_width = int(self.total_time * self.time_scale) + WHITE_KEY_WIDTH
        if self.minimumWidth() != new_min_width:
            self.setMinimumWidth(new_min_width)
            self.updateGeometry()

    def sizeHint(self):
        num_white_keys = 0
        for i in range(MIN_PITCH, MAX_PITCH + 1):
            if i % 12 not in [1, 3, 6, 8, 10]:
                num_white_keys +=1
        return QSize(self.minimumWidth(), num_white_keys * WHITE_KEY_HEIGHT)
    
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0, theme.BG_COLOR.lighter(105))
        bg_gradient.setColorAt(1, theme.BG_COLOR)
        painter.fillRect(event.rect(), bg_gradient)

        # Draw drag overlay BEFORE notes to prevent pink glitch
        if self._is_dragging_midi:
            painter.save()
            # Use the dedicated theme color for drag overlay
            painter.fillRect(self.rect().adjusted(WHITE_KEY_WIDTH + 1, 1, -1, -1), theme.DRAG_OVERLAY_COLOR)
            
            # Keep the border distinct
            border_pen = QPen(theme.ACCENT_COLOR.lighter(130), 2, Qt.DashLine)
            painter.setPen(border_pen)
            painter.drawRect(self.rect().adjusted(WHITE_KEY_WIDTH + 1, 1, -1, -1))
            painter.restore()

        # Draw regular UI elements after the overlay
        draw_time_grid(painter, self.width(), self.height(), self.time_scale, self.bpm,
                       self.time_signature_numerator, self.time_signature_denominator, 
                       self.parentWidget())
        draw_piano_keys(painter) 
        draw_notes(painter, self.notes, self.time_scale) 
        draw_playhead(painter, self.playhead_position, self.time_scale, self.height())

    def _pixel_to_time(self, x_pos: int) -> float:
        if x_pos <= WHITE_KEY_WIDTH: return 0.0
        return (x_pos - WHITE_KEY_WIDTH) / self.time_scale

    def _pixel_to_pitch(self, y_pos: int) -> int:
        num_white_keys = 0
        for i in range(MIN_PITCH, MAX_PITCH + 1):
            if i % 12 not in [1, 3, 6, 8, 10]:
                num_white_keys +=1
        full_content_height = num_white_keys * WHITE_KEY_HEIGHT
        if full_content_height == 0: return MIN_PITCH
        num_total_pitches_display_range = MAX_PITCH - MIN_PITCH + 1
        clamped_y_pos = max(0, min(y_pos, full_content_height -1))
        proportion = clamped_y_pos / float(full_content_height)
        calculated_pitch = MAX_PITCH - (proportion * (num_total_pitches_display_range - 1))
        final_pitch = int(round(calculated_pitch))
        return max(MIN_PITCH, min(MAX_PITCH, final_pitch))

    def _quantize_time(self, time_sec: float) -> float:
        if self._grid_quantize_value_seconds <= 0: return time_sec
        return round(time_sec / self._grid_quantize_value_seconds) * self._grid_quantize_value_seconds

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and event.x() > WHITE_KEY_WIDTH:
            pos_x = int(event.position().x())
            clicked_time_raw = self._pixel_to_time(pos_x)
            self.playhead_position = clicked_time_raw
            # If MainWindow needs to know about manual playhead changes to sync TransportControls:
            # self.notesChanged.emit(self.notes) # Or a dedicated signal
            self.update() 
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        super().mouseDoubleClickEvent(event) # No custom double-click action

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.mid', '.midi')):
                    event.acceptProposedAction()
                    self._is_dragging_midi = True
                    self.update()
                    return
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if self._is_dragging_midi: event.acceptProposedAction()
        else: event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self._is_dragging_midi = False
        self.update()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self._is_dragging_midi = False
        self.update() # Clear drag feedback immediately
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.mid', '.midi')):
                    try:
                        midi_data = pretty_midi.PrettyMIDI(file_path)
                        if midi_data.instruments:
                            all_notes = []
                            for instrument in midi_data.instruments:
                                all_notes.extend(instrument.notes)
                            all_notes.sort(key=lambda x: x.start)
                            
                            # Update internal notes and repaint PianoRollDisplay first
                            self.set_notes(all_notes) # This calls self.update() and emits notesChanged
                            
                            # midiFileProcessed can still be used if MainWindow needs a distinct signal for "file loaded"
                            # vs. "notes changed by any means". If notesChanged is sufficient, this can be removed.
                            # For now, let's assume MainWindow might want to differentiate.
                            self.midiFileProcessed.emit(all_notes) # Emitting with the same notes set
                            
                            event.acceptProposedAction()
                        else:
                            QMessageBox.warning(self, "MIDI Parse Error", "No instruments found in MIDI file.")
                            event.ignore()
                    except Exception as e:
                        print(f"Error parsing MIDI file {file_path}: {e}")
                        QMessageBox.critical(self, "MIDI Parse Error", f"Could not parse MIDI file:\n{e}")
                        event.ignore()
                    return # Processed or ignored
        event.ignore()