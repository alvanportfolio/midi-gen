"""
Piano Roll Display Module

Mouse Wheel Controls:
- Ctrl+Scroll: Horizontal zoom (time axis)
- Shift+Scroll: Horizontal panning (never affects piano keys column)
- Alt+Scroll: Vertical zoom (pitch axis, affects piano keys column)
- Regular Scroll: Default vertical scrolling

Keyboard Shortcuts:
- Ctrl+Plus/Minus: Horizontal zoom
- Ctrl+Shift+Plus/Minus: Vertical zoom
"""

import sys
import os # For file extension check
from PySide6.QtWidgets import QWidget, QApplication, QSizePolicy, QMessageBox, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt, QRect, QSize, QPoint, Signal, QRectF, QMimeData, QUrl, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, 
    QRadialGradient, QFontMetrics, QDragEnterEvent, QDropEvent, QMouseEvent, QDragLeaveEvent, QDragMoveEvent,
    QPaintEvent, QWheelEvent, QKeyEvent # Import QWheelEvent and QKeyEvent
)
import pretty_midi
import math # Import math

from config.constants import (
    MIN_PITCH, MAX_PITCH, WHITE_KEY_WIDTH, BLACK_KEY_WIDTH,
    WHITE_KEY_HEIGHT, BLACK_KEY_HEIGHT, BASE_TIME_SCALE, DEFAULT_BPM,
    MIN_LABEL_PITCH, MAX_LABEL_PITCH
)
from config.theme import (
    PIANO_ROLL_BG_COLOR, GRID_LINE_COLOR, GRID_BEAT_LINE_COLOR, GRID_MEASURE_LINE_COLOR, # Updated specific grid colors
    GRID_ROW_HIGHLIGHT_COLOR, KEY_GRID_LINE_COLOR, PLAYHEAD_COLOR, PIANO_KEY_WHITE_COLOR, PIANO_KEY_BLACK_COLOR, 
    PIANO_KEY_BORDER_COLOR, NOTE_LOW_COLOR, NOTE_MED_COLOR, NOTE_HIGH_COLOR, NOTE_BORDER_COLOR, # Updated specific note and key colors
    ACCENT_PRIMARY_COLOR, DRAG_OVERLAY_COLOR, SECONDARY_TEXT_COLOR # Updated general theme colors
)
from ui.drawing_utils import (
    draw_time_grid, draw_piano_keys, draw_notes, draw_playhead
)
from config import theme

class PianoRollDisplay(QWidget):
    """Widget that displays MIDI notes in a piano roll format"""
    
    notesChanged = Signal(list) 
    midiFileProcessed = Signal(list) 

    MIN_HORIZONTAL_ZOOM = 0.1
    MAX_HORIZONTAL_ZOOM = 10.0
    MIN_VERTICAL_ZOOM = 0.25
    MAX_VERTICAL_ZOOM = 4.0

    def __init__(self, notes=None, parent=None):
        super().__init__(parent)
        self.notes: list[pretty_midi.Note] = notes or []
        self.playhead_position = 0.0
        self.target_playhead_position = 0.0
        self.total_time = 0.0 # Initialize total_time
        self.bpm = DEFAULT_BPM
        self.horizontal_zoom_factor = 1.0
        self.vertical_zoom_factor = 1.0
        # time_scale is now independent of BPM, only controlled by horizontal_zoom_factor
        self.time_scale = BASE_TIME_SCALE * self.horizontal_zoom_factor
        self.time_signature_numerator = 4
        self.time_signature_denominator = 4
        
        num_white_keys = 0
        for i in range(MIN_PITCH, MAX_PITCH + 1):
            if i % 12 not in [1, 3, 6, 8, 10]: 
                num_white_keys +=1
        self.setMinimumHeight(int((MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT * self.vertical_zoom_factor))

        
        self.calculate_total_width()
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAcceptDrops(True)
        self._is_dragging_midi = False
        self._grid_quantize_value_seconds = (60.0 / self.bpm) / 4
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Ensure widget can receive key events

        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(1000 // 60) # Target ~60 FPS
        self.animation_timer.timeout.connect(self._animate_playhead)
        # The timer will be started when set_playhead_position is first called with a new target.

    def _animate_playhead(self):
        if abs(self.playhead_position - self.target_playhead_position) < 0.001: # Threshold to stop micro-updates
            # If very close, snap to target and potentially stop timer if no longer needed
            # For continuous playback, target_playhead_position will keep changing, so timer keeps running.
            if self.playhead_position != self.target_playhead_position:
                self._update_display_playhead_position(self.target_playhead_position)
            # Consider stopping timer if playback stops; for now, it runs if target might change.
            return

        # Simple interpolation - adjust factor for desired smoothness/responsiveness
        interpolation_factor = 0.2 # Lower for smoother, higher for more responsive
        new_pos = self.playhead_position + (self.target_playhead_position - self.playhead_position) * interpolation_factor
        self._update_display_playhead_position(new_pos)

    def _update_display_playhead_position(self, new_display_pos):
        """Internal method to update the visual playhead and trigger repaint."""
        if self.playhead_position == new_display_pos:
            return

        playhead_dirty_width = theme.ICON_SIZE_S + 8 # pixels (approximate visual width of playhead + shadow)
        
        # Calculate old playhead rect
        old_playhead_x_center = self.playhead_position * self.time_scale + WHITE_KEY_WIDTH
        old_rect_x = int(old_playhead_x_center - playhead_dirty_width / 2)
        old_rect = QRect(old_rect_x, 0, playhead_dirty_width, self.height())

        self.playhead_position = new_display_pos

        # Calculate new playhead rect
        new_playhead_x_center = self.playhead_position * self.time_scale + WHITE_KEY_WIDTH
        new_rect_x = int(new_playhead_x_center - playhead_dirty_width / 2)
        new_rect = QRect(new_rect_x, 0, playhead_dirty_width, self.height())
        
        self.update(old_rect.united(new_rect))

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

    def set_playhead_position(self, new_target_position):
        """Sets the target position for the playhead. Animation timer will smoothly update to it."""
        self.target_playhead_position = new_target_position
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        
        # For immediate feedback on large jumps (like seeking), update position immediately
        if abs(self.playhead_position - new_target_position) > 0.1: # Large jump threshold
             self._update_display_playhead_position(new_target_position)
    
    def set_bpm(self, bpm):
        if bpm <= 0 or self.bpm == bpm: return
        self.bpm = bpm
        # self.time_scale is no longer updated here as it's independent of BPM
        self._update_quantization_value()
        self.calculate_total_width() # This will use the new BPM for min_time_from_bars
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
        effective_white_key_height = WHITE_KEY_HEIGHT * self.vertical_zoom_factor
        return QSize(self.minimumWidth(), int(num_white_keys * effective_white_key_height))
    
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        
        # Use solid PIANO_ROLL_BG_COLOR
        painter.fillRect(event.rect(), theme.PIANO_ROLL_BG_COLOR)

        # Draw drag overlay BEFORE notes to prevent pink glitch
        if self._is_dragging_midi:
            painter.save()
            # Use the dedicated theme color for drag overlay
            painter.fillRect(self.rect().adjusted(WHITE_KEY_WIDTH + 1, 1, -1, -1), theme.DRAG_OVERLAY_COLOR)
            
            # Keep the border distinct
            border_pen = QPen(theme.ACCENT_PRIMARY_COLOR.lighter(130), 2, Qt.PenStyle.DashLine) # Use ACCENT_PRIMARY_COLOR
            painter.setPen(border_pen)
            painter.drawRect(self.rect().adjusted(WHITE_KEY_WIDTH + 1, 1, -1, -1))
            painter.restore()

        # Draw regular UI elements after the overlay
        draw_time_grid(painter, self.width(), self.height(), self.time_scale, self.bpm,
                       self.time_signature_numerator, self.time_signature_denominator, 
                       self.parentWidget(), self.vertical_zoom_factor)
        draw_piano_keys(painter, self.vertical_zoom_factor) 
        draw_notes(painter, self.notes, self.time_scale, self.vertical_zoom_factor) 
        draw_playhead(painter, self.playhead_position, self.time_scale, self.height())

    def _pixel_to_time(self, x_pos: int) -> float:
        if x_pos <= WHITE_KEY_WIDTH: return 0.0
        return (x_pos - WHITE_KEY_WIDTH) / self.time_scale

    def _pixel_to_pitch(self, y_pos: int) -> int:
        effective_white_key_height = WHITE_KEY_HEIGHT * self.vertical_zoom_factor
        if effective_white_key_height <= 0: return MIN_PITCH
        # Calculate pitch index from the top. Each key slot (white or black) effectively occupies `effective_white_key_height` vertically.
        # The y_pos is relative to the start of the piano roll content.
        pitch_offset = math.floor(y_pos / effective_white_key_height)
        # Convert this offset to an actual MIDI pitch number (higher y means lower pitch)
        pitch = MAX_PITCH - pitch_offset
        return max(MIN_PITCH, min(MAX_PITCH, pitch))

    def _pitch_to_pixel_y(self, pitch: int) -> float:
        effective_white_key_height = WHITE_KEY_HEIGHT * self.vertical_zoom_factor
        # Calculate y position from the top for a given pitch
        # Higher pitch means smaller y value
        y_pos = (MAX_PITCH - pitch) * effective_white_key_height
        return y_pos

    def _quantize_time(self, time_sec: float) -> float:
        if self._grid_quantize_value_seconds <= 0: return time_sec
        return round(time_sec / self._grid_quantize_value_seconds) * self._grid_quantize_value_seconds

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and event.x() > WHITE_KEY_WIDTH:
            pos_x = int(event.position().x())
            clicked_time_raw = self._pixel_to_time(pos_x)
            self.set_playhead_position(clicked_time_raw) # Call the optimized method
            # If MainWindow needs to know about manual playhead changes to sync TransportControls:
            # self.notesChanged.emit(self.notes) # Or a dedicated signal
            # self.update() is now handled by set_playhead_position
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

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            mouse_x = event.position().x()

            if mouse_x <= WHITE_KEY_WIDTH:
                # Ignore zoom if cursor is over piano keys for horizontal zoom
                # but allow vertical zoom or other handling by parent
                super().wheelEvent(event)
                return

            old_scroll_x = 0
            parent_scroll_area = self.parentWidget()
            while parent_scroll_area and not hasattr(parent_scroll_area, 'horizontalScrollBar'):
                parent_scroll_area = parent_scroll_area.parentWidget()
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
                old_scroll_x = parent_scroll_area.horizontalScrollBar().value()

            # Time at cursor before zoom (absolute time)
            time_at_cursor = self._pixel_to_time(int(mouse_x + old_scroll_x))

            delta = event.angleDelta().y()
            zoom_speed_factor = 1.1

            if delta > 0:  # Zoom in
                new_zoom_factor = self.horizontal_zoom_factor * zoom_speed_factor
            elif delta < 0:  # Zoom out
                new_zoom_factor = self.horizontal_zoom_factor / zoom_speed_factor
            else: # No change
                event.accept()
                return

            self.horizontal_zoom_factor = max(self.MIN_HORIZONTAL_ZOOM, min(self.MAX_HORIZONTAL_ZOOM, new_zoom_factor))
            
            # time_scale is now independent of BPM
            self.time_scale = BASE_TIME_SCALE * self.horizontal_zoom_factor
            
            # This recalculates minimum width based on new time_scale and total_time
            self.calculate_total_width() 

            # New pixel X for the time_at_cursor with the new time_scale (relative to grid start)
            new_pixel_x_for_time_at_cursor = time_at_cursor * self.time_scale
            
            # Calculate new scrollbar value to keep time_at_cursor under the mouse
            # mouse_x is relative to widget, WHITE_KEY_WIDTH is offset of grid from widget start
            new_scroll_x = new_pixel_x_for_time_at_cursor - (mouse_x - WHITE_KEY_WIDTH)
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
                parent_scroll_area.horizontalScrollBar().setValue(int(new_scroll_x))
            
            self.update() # Redraw with new zoom and scroll
            event.accept()
        elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier: # Horizontal panning
            # Shift+scroll should always pan horizontally, never affect piano keys column
            delta = event.angleDelta().y()
            
            # Find the parent scroll area
            parent_scroll_area = self.parentWidget()
            while parent_scroll_area and not hasattr(parent_scroll_area, 'horizontalScrollBar'):
                parent_scroll_area = parent_scroll_area.parentWidget()
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
                # Pan horizontally - convert vertical scroll delta to horizontal movement
                scroll_speed = 50  # Pixels per scroll step
                current_scroll_x = parent_scroll_area.horizontalScrollBar().value()
                
                if delta > 0:  # Scroll up = pan left
                    new_scroll_x = current_scroll_x - scroll_speed
                elif delta < 0:  # Scroll down = pan right
                    new_scroll_x = current_scroll_x + scroll_speed
                else:
                    event.accept()
                    return
                
                # Apply the horizontal scroll
                parent_scroll_area.horizontalScrollBar().setValue(int(new_scroll_x))
            
            event.accept()
        elif event.modifiers() == Qt.KeyboardModifier.AltModifier: # Vertical zoom
            mouse_y = event.position().y()
            old_scroll_y = 0
            parent_scroll_area = self.parentWidget()
            while parent_scroll_area and not hasattr(parent_scroll_area, 'verticalScrollBar'):
                parent_scroll_area = parent_scroll_area.parentWidget()
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'verticalScrollBar'):
                old_scroll_y = parent_scroll_area.verticalScrollBar().value()

            pitch_at_cursor = self._pixel_to_pitch(int(mouse_y + old_scroll_y))

            delta = event.angleDelta().y()
            zoom_speed_factor = 1.1

            if delta > 0:  # Zoom in
                new_zoom_factor = self.vertical_zoom_factor * zoom_speed_factor
            elif delta < 0:  # Zoom out
                new_zoom_factor = self.vertical_zoom_factor / zoom_speed_factor
            else: # No change
                event.accept()
                return
            
            self.vertical_zoom_factor = max(self.MIN_VERTICAL_ZOOM, min(self.MAX_VERTICAL_ZOOM, new_zoom_factor))
            
            new_min_height = int((MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT * self.vertical_zoom_factor)
            self.setMinimumHeight(new_min_height)

            new_pixel_y_for_pitch_at_cursor = self._pitch_to_pixel_y(pitch_at_cursor)
            new_scroll_y = new_pixel_y_for_pitch_at_cursor - mouse_y
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'verticalScrollBar'):
                parent_scroll_area.verticalScrollBar().setValue(int(new_scroll_y))
            
            self.update()
            event.accept()
        else:
            super().wheelEvent(event) # Default handling for other cases (e.g. vertical scroll)

    def _zoom_horizontal_to_center(self, zoom_factor_change_multiplier: float):
        parent_scroll_area = self.parentWidget()
        while parent_scroll_area and not hasattr(parent_scroll_area, 'horizontalScrollBar'):
            parent_scroll_area = parent_scroll_area.parentWidget()

        current_scroll_x = 0
        current_viewport_center_x_widget_relative = self.width() / 2 # Fallback if no scrollbar

        if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
            scrollbar = parent_scroll_area.horizontalScrollBar()
            viewport_width = parent_scroll_area.viewport().width()
            current_scroll_x = scrollbar.value()
            # Center of the viewport in viewport coordinates (relative to viewport start)
            current_viewport_center_x_widget_relative = viewport_width / 2
        
        # Time at the center of the viewport (absolute time)
        time_at_center = self._pixel_to_time(int(current_viewport_center_x_widget_relative + current_scroll_x))

        old_horizontal_zoom_factor = self.horizontal_zoom_factor
        new_horizontal_zoom_factor = old_horizontal_zoom_factor * zoom_factor_change_multiplier
        
        self.horizontal_zoom_factor = max(self.MIN_HORIZONTAL_ZOOM, min(self.MAX_HORIZONTAL_ZOOM, new_horizontal_zoom_factor))
        
        # Update time_scale based on the new zoom factor, independent of BPM
        self.time_scale = BASE_TIME_SCALE * self.horizontal_zoom_factor
        
        # Recalculate total width which also calls updateGeometry
        self.calculate_total_width() 

        # New pixel X for the time_at_center with the new time_scale (relative to grid start)
        new_pixel_x_for_time_at_center = time_at_center * self.time_scale
        
        # Calculate new scrollbar value
        # current_viewport_center_x_widget_relative is the offset from the start of the viewport to its center
        new_scroll_x = new_pixel_x_for_time_at_center - current_viewport_center_x_widget_relative
        
        if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
            parent_scroll_area.horizontalScrollBar().setValue(int(new_scroll_x))
            
        self.update()


    def keyPressEvent(self, event: QKeyEvent):
        zoom_speed_factor = 1.2 # Can be different from wheel zoom
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier: # Ctrl only
            if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
                self._zoom_horizontal_to_center(zoom_speed_factor)
                event.accept()
            elif event.key() == Qt.Key.Key_Minus:
                self._zoom_horizontal_to_center(1 / zoom_speed_factor)
                event.accept()
            else:
                super().keyPressEvent(event)
        elif event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier): # Ctrl + Shift
            if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
                self._zoom_vertical_to_center(zoom_speed_factor)
                event.accept()
            elif event.key() == Qt.Key.Key_Minus:
                self._zoom_vertical_to_center(1 / zoom_speed_factor)
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def _zoom_vertical_to_center(self, zoom_factor_change_multiplier: float):
        parent_scroll_area = self.parentWidget()
        while parent_scroll_area and not hasattr(parent_scroll_area, 'verticalScrollBar'):
            parent_scroll_area = parent_scroll_area.parentWidget()

        current_scroll_y = 0
        current_viewport_center_y_widget_relative = self.height() / 2 # Fallback

        if parent_scroll_area and hasattr(parent_scroll_area, 'verticalScrollBar'):
            scrollbar = parent_scroll_area.verticalScrollBar()
            viewport_height = parent_scroll_area.viewport().height()
            current_scroll_y = scrollbar.value()
            current_viewport_center_y_widget_relative = viewport_height / 2
        
        pitch_at_center = self._pixel_to_pitch(int(current_viewport_center_y_widget_relative + current_scroll_y))
        
        old_vertical_zoom_factor = self.vertical_zoom_factor
        new_vertical_zoom_factor = old_vertical_zoom_factor * zoom_factor_change_multiplier
        
        self.vertical_zoom_factor = max(self.MIN_VERTICAL_ZOOM, min(self.MAX_VERTICAL_ZOOM, new_vertical_zoom_factor))
        
        new_min_height = int((MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT * self.vertical_zoom_factor)
        self.setMinimumHeight(new_min_height)

        new_pixel_y_for_pitch_at_center = self._pitch_to_pixel_y(pitch_at_center)
        new_scroll_y = new_pixel_y_for_pitch_at_center - current_viewport_center_y_widget_relative
        
        if parent_scroll_area and hasattr(parent_scroll_area, 'verticalScrollBar'):
            parent_scroll_area.verticalScrollBar().setValue(int(new_scroll_y))
            
        self.update()

class PianoRollComposite(QWidget):
    """Composite widget that keeps piano keys fixed on the left while notes scroll horizontally"""
    
    # Forward signals from the internal piano roll
    notesChanged = Signal(list)
    midiFileProcessed = Signal(list)
    
    def __init__(self, notes=None, parent=None):
        super().__init__(parent)
        self._notes = notes or []
        
        # Create main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create fixed piano keys widget
        self.piano_keys_widget = FixedPianoKeysWidget()
        main_layout.addWidget(self.piano_keys_widget)
        
        # Create scroll area for notes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1c1c20;
            }
        """)
        
        # Create the note area (piano roll without piano keys)
        self.note_area = PianoRollNoteArea(self._notes)
        self.scroll_area.setWidget(self.note_area)
        main_layout.addWidget(self.scroll_area)
        
        # Connect signals
        self.note_area.notesChanged.connect(self.notesChanged.emit)
        self.note_area.midiFileProcessed.connect(self.midiFileProcessed.emit)
        
        # Synchronize vertical scrolling between piano keys and notes
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.piano_keys_widget.sync_vertical_scroll)
        
        # Synchronize vertical zoom when note area changes zoom
        self.note_area.vertical_zoom_changed = lambda zoom: self.piano_keys_widget.sync_vertical_zoom(zoom)
        
        # Forward method calls to the note area
        self.set_notes = self.note_area.set_notes
        self.add_note = self.note_area.add_note
        self.set_playhead_position = self.note_area.set_playhead_position
        self.set_bpm = self.note_area.set_bpm
        self.set_time_signature = self.note_area.set_time_signature
    
    @property
    def notes(self):
        return self.note_area.notes
    
    @notes.setter
    def notes(self, value):
        self.note_area.notes = value
    
    @property 
    def playhead_position(self):
        return self.note_area.playhead_position

class FixedPianoKeysWidget(QWidget):
    """Widget that displays only piano keys in a fixed position"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vertical_zoom_factor = 1.0
        self.vertical_scroll_offset = 0
        self.setFixedWidth(WHITE_KEY_WIDTH)
        
        # Calculate height based on number of keys
        num_white_keys = 0
        for i in range(MIN_PITCH, MAX_PITCH + 1):
            if i % 12 not in [1, 3, 6, 8, 10]: 
                num_white_keys += 1
        self.setMinimumHeight(int((MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT * self.vertical_zoom_factor))
    
    def sync_vertical_scroll(self, value):
        """Synchronize vertical scrolling with the note area"""
        self.vertical_scroll_offset = value
        self.update()
    
    def sync_vertical_zoom(self, zoom_factor):
        """Synchronize vertical zoom with the note area"""
        self.vertical_zoom_factor = zoom_factor
        # Update height
        effective_height = WHITE_KEY_HEIGHT * self.vertical_zoom_factor
        self.setMinimumHeight(int((MAX_PITCH - MIN_PITCH + 1) * effective_height))
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        
        # Fill background
        painter.fillRect(event.rect(), theme.PIANO_ROLL_BG_COLOR)
        
        # Translate for vertical scrolling
        painter.translate(0, -self.vertical_scroll_offset)
        
        # Draw piano keys
        draw_piano_keys(painter, self.vertical_zoom_factor)

class PianoRollNoteArea(PianoRollDisplay):
    """Piano roll display without piano keys - only notes, grid, and playhead"""
    
    def __init__(self, notes=None, parent=None):
        super().__init__(notes, parent)
        # Remove the piano key width offset since we don't draw piano keys here
        
    def _update_display_playhead_position(self, new_display_pos):
        """
        🔧 FIXED: Internal method to update the visual playhead and trigger repaint.
        Overridden to handle coordinate system without WHITE_KEY_WIDTH offset.
        """
        if self.playhead_position == new_display_pos:
            return

        playhead_dirty_width = theme.ICON_SIZE_S + 8 # pixels (approximate visual width of playhead + shadow)
        
        # 🔧 FIXED: Calculate old playhead rect WITHOUT WHITE_KEY_WIDTH offset
        old_playhead_x_center = self.playhead_position * self.time_scale  # No offset!
        old_rect_x = int(old_playhead_x_center - playhead_dirty_width / 2)
        old_rect = QRect(old_rect_x, 0, playhead_dirty_width, self.height())

        self.playhead_position = new_display_pos

        # 🔧 FIXED: Calculate new playhead rect WITHOUT WHITE_KEY_WIDTH offset
        new_playhead_x_center = self.playhead_position * self.time_scale  # No offset!
        new_rect_x = int(new_playhead_x_center - playhead_dirty_width / 2)
        new_rect = QRect(new_rect_x, 0, playhead_dirty_width, self.height())
        
        self.update(old_rect.united(new_rect))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        
        # Use solid PIANO_ROLL_BG_COLOR
        painter.fillRect(event.rect(), theme.PIANO_ROLL_BG_COLOR)

        # Draw drag overlay BEFORE notes to prevent pink glitch
        if self._is_dragging_midi:
            painter.save()
            # Use the dedicated theme color for drag overlay (no WHITE_KEY_WIDTH offset)
            painter.fillRect(self.rect().adjusted(1, 1, -1, -1), theme.DRAG_OVERLAY_COLOR)
            
            # Keep the border distinct
            border_pen = QPen(theme.ACCENT_PRIMARY_COLOR.lighter(130), 2, Qt.PenStyle.DashLine)
            painter.setPen(border_pen)
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
            painter.restore()

        # Draw grid without piano keys area
        self._draw_note_area_grid(painter)
        
        # Draw notes (adjusted for no piano key offset)
        self._draw_notes_no_piano_offset(painter)
        
        # Draw playhead (adjusted for no piano key offset)
        self._draw_playhead_no_piano_offset(painter)
    
    def _draw_note_area_grid(self, painter):
        """Draw time grid without piano keys area"""
        width = self.width()
        height = self.height()
        
        effective_white_key_height = WHITE_KEY_HEIGHT * self.vertical_zoom_factor
        
        current_viewport_y_offset = 0
        parent_widget = self.parentWidget()
        if parent_widget and hasattr(parent_widget, 'verticalScrollBar'):
            current_viewport_y_offset = parent_widget.verticalScrollBar().value()
        elif parent_widget and hasattr(parent_widget, 'parentWidget') and parent_widget.parentWidget():
            grandparent_obj = parent_widget.parentWidget()
            if grandparent_obj and hasattr(grandparent_obj, 'verticalScrollBar'):
                current_viewport_y_offset = grandparent_obj.verticalScrollBar().value()
        
        # Draw horizontal lines for note rows
        painter.setPen(QPen(theme.KEY_GRID_LINE_COLOR, 0.8, Qt.PenStyle.SolidLine))
        for pitch in range(MIN_PITCH, MAX_PITCH + 1):
            y_pos = (MAX_PITCH - pitch) * effective_white_key_height
            painter.drawLine(0, int(y_pos), width, int(y_pos))  # Start from 0 instead of WHITE_KEY_WIDTH
            note_name = pretty_midi.note_number_to_name(pitch)
            if note_name.endswith('C') and '#' not in note_name:
                highlight_rect = QRect(0, int(y_pos), width, int(effective_white_key_height))  # Start from 0
                painter.fillRect(highlight_rect, theme.GRID_ROW_HIGHLIGHT_COLOR)

        # Time signature display
        ts_text = f"{self.time_signature_numerator}/{self.time_signature_denominator}"
        painter.setPen(QPen(theme.SECONDARY_TEXT_COLOR, 1.0))
        painter.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S, weight=theme.FONT_WEIGHT_BOLD))
        ts_x_pos = theme.PADDING_S  # No WHITE_KEY_WIDTH offset
        ts_y_pos = current_viewport_y_offset + theme.PADDING_M + theme.FONT_SIZE_S
        painter.drawText(ts_x_pos, ts_y_pos, ts_text)

        actual_pixels_per_quarter_note = 0
        if self.bpm > 0:
            seconds_per_quarter_note = 60.0 / self.bpm
            actual_pixels_per_quarter_note = self.time_scale * seconds_per_quarter_note
        
        # Draw sixteenth note lines
        painter.setPen(QPen(theme.GRID_LINE_COLOR, 0.5, Qt.PenStyle.DotLine))
        sixteenth_note_step_pixels = actual_pixels_per_quarter_note / 4.0 if actual_pixels_per_quarter_note > 0 else 0
        if sixteenth_note_step_pixels > 5:
            for i in range(int(width / sixteenth_note_step_pixels) + 1):
                if i % 4 != 0:
                    x = i * sixteenth_note_step_pixels  # No WHITE_KEY_WIDTH offset
                    painter.drawLine(int(x), 0, int(x), height)

        pixels_per_beat = actual_pixels_per_quarter_note * (4.0 / self.time_signature_denominator) if self.time_signature_denominator > 0 else actual_pixels_per_quarter_note
        
        # Draw beat lines
        if pixels_per_beat > 0:
            painter.setPen(QPen(theme.GRID_BEAT_LINE_COLOR, 0.7, Qt.PenStyle.SolidLine))
            for i in range(int(width / pixels_per_beat) + 1):
                if i % self.time_signature_numerator != 0:
                    x = i * pixels_per_beat  # No WHITE_KEY_WIDTH offset
                    painter.drawLine(int(x), 0, int(x), height)

        # Draw measure lines
        if pixels_per_beat > 0 and self.time_signature_numerator > 0:
            pixels_per_measure = pixels_per_beat * self.time_signature_numerator
            if pixels_per_measure > 0:
                painter.setPen(QPen(theme.GRID_MEASURE_LINE_COLOR, 1.0, Qt.PenStyle.SolidLine))
                measure_number_y_pos = current_viewport_y_offset + theme.PADDING_M + theme.FONT_SIZE_S
                for i in range(int(width / pixels_per_measure) + 1):
                    x = i * pixels_per_measure  # No WHITE_KEY_WIDTH offset
                    painter.drawLine(int(x), 0, int(x), height)
                    painter.setPen(QPen(theme.SECONDARY_TEXT_COLOR, 1.0))
                    painter.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS))
                    painter.drawText(int(x + theme.PADDING_XS), measure_number_y_pos, str(i + 1))
    
    def _draw_notes_no_piano_offset(self, painter):
        """Draw notes without piano key offset"""
        effective_white_key_height = WHITE_KEY_HEIGHT * self.vertical_zoom_factor
        effective_black_key_height = BLACK_KEY_HEIGHT * self.vertical_zoom_factor

        for note in self.notes:
            if not hasattr(note, 'pitch') or not hasattr(note, 'start') or not hasattr(note, 'end'): 
                continue
            pitch = note.pitch
            if pitch < MIN_PITCH or pitch > MAX_PITCH: 
                continue
            
            y_pos = (MAX_PITCH - pitch) * effective_white_key_height 
            x_pos = note.start * self.time_scale  # No WHITE_KEY_WIDTH offset
            width = max((note.end - note.start) * self.time_scale, 4)
            pitch_class = pitch % 12
            is_white = pitch_class in [0, 2, 4, 5, 7, 9, 11]
            padding = 4 

            if is_white:
                height = effective_white_key_height - padding 
                y_offset = padding / 2
            else:
                height = effective_black_key_height - padding 
                y_offset = (effective_white_key_height - effective_black_key_height) / 2 + (padding / 2)
                
            velocity = getattr(note, 'velocity', 64)
            
            # Use theme note colors based on velocity
            if velocity < 42:
                base_color = theme.NOTE_LOW_COLOR
            elif velocity < 85:
                base_color = theme.NOTE_MED_COLOR
            else:
                base_color = theme.NOTE_HIGH_COLOR
            
            note_rect = QRect(int(x_pos), int(y_pos + y_offset), int(width), int(height))
            
            # Draw note with gradient
            from PySide6.QtGui import QLinearGradient
            gradient = QLinearGradient(note_rect.topLeft(), note_rect.bottomLeft())
            gradient.setColorAt(0.0, base_color.lighter(120))
            gradient.setColorAt(1.0, base_color)
            painter.fillRect(note_rect, gradient)
            
            # Draw border
            painter.setPen(QPen(theme.NOTE_BORDER_COLOR, 1.0))
            painter.drawRect(note_rect)
            
            # Note labels - make them bold and visible
            corrected_label_name_note = pretty_midi.note_number_to_name(pitch)

            note_block_font = QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S, weight=theme.FONT_WEIGHT_BOLD) # Bigger, bolder font
            painter.setFont(note_block_font)
            
            # Use high contrast color for note labels - white with some transparency for visibility
            note_label_color = QColor(255, 255, 255, 220)  # Bright white with high opacity
            painter.setPen(QPen(note_label_color))
            
            note_content_rect = QRectF(x_pos, y_pos + y_offset, width, height)
            
            # More relaxed condition for showing text - show if note is reasonably sized
            if width >= 25 and height >= 12:  # Simple size check instead of complex text fitting
                painter.drawText(note_content_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, corrected_label_name_note)
    
    def _draw_playhead_no_piano_offset(self, painter):
        """Draw playhead without piano key offset"""
        playhead_x = self.playhead_position * self.time_scale  # No WHITE_KEY_WIDTH offset
        playhead_line = QPen(theme.PLAYHEAD_COLOR, 2)
        painter.setPen(playhead_line)
        painter.drawLine(int(playhead_x), 0, int(playhead_x), self.height())
        
        # Draw playhead triangle at top
        triangle_size = 8
        triangle_points = [
            QPoint(int(playhead_x), 0),
            QPoint(int(playhead_x - triangle_size//2), triangle_size),
            QPoint(int(playhead_x + triangle_size//2), triangle_size)
        ]
        painter.setBrush(QBrush(theme.PLAYHEAD_COLOR))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(triangle_points)
    
    def _pixel_to_time(self, x_pos: int) -> float:
        # No WHITE_KEY_WIDTH offset since we don't have piano keys
        return max(0.0, x_pos / self.time_scale)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos_x = int(event.position().x())
            clicked_time_raw = self._pixel_to_time(pos_x)
            self.set_playhead_position(clicked_time_raw)
        super().mousePressEvent(event)
    
    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Horizontal zoom handling (no piano key width to consider)
            mouse_x = event.position().x()
            
            old_scroll_x = 0
            parent_scroll_area = self.parentWidget()
            while parent_scroll_area and not hasattr(parent_scroll_area, 'horizontalScrollBar'):
                parent_scroll_area = parent_scroll_area.parentWidget()
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
                old_scroll_x = parent_scroll_area.horizontalScrollBar().value()

            time_at_cursor = self._pixel_to_time(int(mouse_x + old_scroll_x))

            delta = event.angleDelta().y()
            zoom_speed_factor = 1.1

            if delta > 0:
                new_zoom_factor = self.horizontal_zoom_factor * zoom_speed_factor
            elif delta < 0:
                new_zoom_factor = self.horizontal_zoom_factor / zoom_speed_factor
            else:
                event.accept()
                return

            self.horizontal_zoom_factor = max(self.MIN_HORIZONTAL_ZOOM, min(self.MAX_HORIZONTAL_ZOOM, new_zoom_factor))
            self.time_scale = BASE_TIME_SCALE * self.horizontal_zoom_factor
            self.calculate_total_width()

            new_pixel_x_for_time_at_cursor = time_at_cursor * self.time_scale
            new_scroll_x = new_pixel_x_for_time_at_cursor - mouse_x
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
                parent_scroll_area.horizontalScrollBar().setValue(int(new_scroll_x))
            
            self.update()
            event.accept()
        elif event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            # Horizontal panning - never affect piano keys column
            delta = event.angleDelta().y()
            
            # Find the parent scroll area  
            parent_scroll_area = self.parentWidget()
            while parent_scroll_area and not hasattr(parent_scroll_area, 'horizontalScrollBar'):
                parent_scroll_area = parent_scroll_area.parentWidget()
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
                # Pan horizontally - convert vertical scroll delta to horizontal movement
                scroll_speed = 50  # Pixels per scroll step
                current_scroll_x = parent_scroll_area.horizontalScrollBar().value()
                
                if delta > 0:  # Scroll up = pan left
                    new_scroll_x = current_scroll_x - scroll_speed
                elif delta < 0:  # Scroll down = pan right
                    new_scroll_x = current_scroll_x + scroll_speed
                else:
                    event.accept()
                    return
                
                # Apply the horizontal scroll
                parent_scroll_area.horizontalScrollBar().setValue(int(new_scroll_x))
            
            event.accept()
        elif event.modifiers() == Qt.KeyboardModifier.AltModifier: # Vertical zoom
            mouse_y = event.position().y()
            old_scroll_y = 0
            parent_scroll_area = self.parentWidget()
            while parent_scroll_area and not hasattr(parent_scroll_area, 'verticalScrollBar'):
                parent_scroll_area = parent_scroll_area.parentWidget()
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'verticalScrollBar'):
                old_scroll_y = parent_scroll_area.verticalScrollBar().value()

            pitch_at_cursor = self._pixel_to_pitch(int(mouse_y + old_scroll_y))

            delta = event.angleDelta().y()
            zoom_speed_factor = 1.1

            if delta > 0:
                new_zoom_factor = self.vertical_zoom_factor * zoom_speed_factor
            elif delta < 0:
                new_zoom_factor = self.vertical_zoom_factor / zoom_speed_factor
            else:
                event.accept()
                return

            self.vertical_zoom_factor = max(self.MIN_VERTICAL_ZOOM, min(self.MAX_VERTICAL_ZOOM, new_zoom_factor))
            
            # Notify piano keys widget of zoom change
            if hasattr(self, 'vertical_zoom_changed'):
                self.vertical_zoom_changed(self.vertical_zoom_factor)

            # Update heights
            self.setMinimumHeight(int((MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT * self.vertical_zoom_factor))
            self.updateGeometry()
            
            # Keep the same pitch under cursor
            new_pixel_y_for_pitch_at_cursor = self._pitch_to_pixel_y(pitch_at_cursor)
            new_scroll_y = new_pixel_y_for_pitch_at_cursor - mouse_y
            
            if parent_scroll_area and hasattr(parent_scroll_area, 'verticalScrollBar'):
                parent_scroll_area.verticalScrollBar().setValue(int(new_scroll_y))
            
            self.update()
            event.accept()
        else:
            super().wheelEvent(event)
    
    def calculate_total_width(self):
        max_time = 0.0
        if self.notes:
            for note in self.notes:
                if hasattr(note, 'end') and note.end > max_time:
                    max_time = note.end
        min_visible_bars = 4
        min_time_from_bars = min_visible_bars * self.time_signature_numerator * (60.0 / self.bpm)
        self.total_time = max(max_time + 2.0, min_time_from_bars)
        new_min_width = int(self.total_time * self.time_scale)  # No WHITE_KEY_WIDTH offset
        if self.minimumWidth() != new_min_width:
            self.setMinimumWidth(new_min_width)
            self.updateGeometry()