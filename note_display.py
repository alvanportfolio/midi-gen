import sys
from PySide6.QtWidgets import QWidget, QApplication, QSizePolicy
from PySide6.QtCore import Qt, QRect, QSize, QPoint, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, QRadialGradient, QFontMetrics
import pretty_midi

from config.constants import (
    MIN_PITCH, MAX_PITCH, WHITE_KEY_WIDTH, BLACK_KEY_WIDTH,
    WHITE_KEY_HEIGHT, BLACK_KEY_HEIGHT, BASE_TIME_SCALE, DEFAULT_BPM,
    MIN_LABEL_PITCH, MAX_LABEL_PITCH
)
from config.theme import (
    BG_COLOR, GRID_COLOR, BEAT_COLOR, MEASURE_COLOR, ROW_HIGHLIGHT_COLOR, # BG_COLOR is used in paintEvent
    KEY_GRID_COLOR, PLAYHEAD_COLOR, WHITE_KEY_COLOR, BLACK_KEY_COLOR, # PLAYHEAD_COLOR used in draw_playhead
    KEY_BORDER_COLOR, NOTE_COLORS # NOTE_COLORS used in draw_notes
)
from ui.drawing_utils import (
    draw_time_grid, draw_piano_keys, draw_notes, draw_playhead
)

class PianoRollDisplay(QWidget):
    """Widget that displays MIDI notes in a piano roll format"""
    
    def __init__(self, notes=None, parent=None):
        super().__init__(parent)
        self.notes = notes or []
        self.playhead_position = 0.0
        self.bpm = DEFAULT_BPM  # Default tempo
        self.time_scale = BASE_TIME_SCALE  # Will be adjusted based on BPM
        self.time_signature_numerator = 4
        self.time_signature_denominator = 4
        self.setMinimumHeight(88 * WHITE_KEY_HEIGHT)  # 88 piano keys
        
        # Calculate total width based on notes
        self.calculate_total_width()
        
        # Track mouse position for interactive features
        self.setMouseTracking(True)
        
        # Set size policy for proper scrolling
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def set_notes(self, notes):
        """Update the notes to display"""
        self.notes = notes
        self.calculate_total_width()
        self.update()

    def add_note(self, note: pretty_midi.Note):
        """Adds a single note to the display and updates."""
        if not hasattr(note, 'start') or not hasattr(note, 'end') or not hasattr(note, 'pitch'):
            print(f"PianoRollDisplay: Received invalid note object: {note}")
            return
            
        self.notes.append(note)
        
        # Check if this note extends the total width
        extended_width = False
        if (note.end + 2.0) * self.time_scale > self.minimumWidth(): # +2.0 for padding like in calculate_total_width
            self.calculate_total_width() # Recalculate if it extends
            extended_width = True
        
        self.update() # Repaint to show the new note

        # Auto-scroll to the new note
        # The PianoRollDisplay is usually inside a QScrollArea
        parent_scroll_area = self.parent()
        if parent_scroll_area and hasattr(parent_scroll_area, 'horizontalScrollBar'):
            # Calculate the x position of the new note
            note_x_start_pixels = note.start * self.time_scale + WHITE_KEY_WIDTH
            note_x_end_pixels = note.end * self.time_scale + WHITE_KEY_WIDTH
            
            scrollbar = parent_scroll_area.horizontalScrollBar()
            current_viewport_width = parent_scroll_area.viewport().width()
            
            # If the note starts beyond the current view or ends beyond it
            if note_x_start_pixels > scrollbar.value() + current_viewport_width or \
               note_x_end_pixels > scrollbar.value() + current_viewport_width or extended_width:
                # Scroll to make the start of the note visible, perhaps with some margin
                target_scroll_value = int(note_x_start_pixels - current_viewport_width / 4)
                scrollbar.setValue(max(0, target_scroll_value))
    
    def set_playhead_position(self, position):
        """Set the current playhead position in seconds"""
        self.playhead_position = position
        self.update()
    
    def set_bpm(self, bpm):
        """Set the tempo in beats per minute"""
        if bpm <= 0:
            return
            
        self.bpm = bpm
        # Adjust time scale based on BPM (make grid denser or sparser)
        # This creates a visual effect where higher BPM = more compressed grid
        self.time_scale = BASE_TIME_SCALE * (DEFAULT_BPM / bpm)
        
        # Recalculate width to account for new time scale
        self.calculate_total_width()
        self.update()  # Update grid to reflect new tempo

    def set_time_signature(self, numerator: int, denominator: int):
        """Set the time signature"""
        if numerator > 0 and denominator > 0:  # Basic validation
            self.time_signature_numerator = numerator
            self.time_signature_denominator = denominator
            # Potentially adjust time_scale or other dependent factors if needed
            self.calculate_total_width() # Ensure width is appropriate
            self.update() # Redraw with new signature
    
    def calculate_total_width(self):
        """Calculate the total width needed to display all notes"""
        max_time = 10.0  # Default minimum width (10 seconds)
        for note in self.notes:
            if hasattr(note, 'end') and note.end > max_time:
                max_time = note.end
        
        # Add some extra space at the end
        self.total_time = max_time + 2.0
        min_width = int(self.total_time * self.time_scale)
        self.setMinimumWidth(min_width)
    
    def sizeHint(self):
        """Suggest a size for the widget"""
        return QSize(int(self.total_time * self.time_scale), 
                    (MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)
    
    def paintEvent(self, event):
        """Paint the piano roll"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # Fill background with a subtle gradient
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0, BG_COLOR.lighter(105))
        bg_gradient.setColorAt(1, BG_COLOR)
        painter.fillRect(event.rect(), bg_gradient)

        # Draw time grid
        draw_time_grid(
            painter, self.width(), self.height(), self.time_scale, self.bpm,
            self.time_signature_numerator, self.time_signature_denominator, self.parent()
        )
        
        # Draw piano keys
        draw_piano_keys(painter)
        
        # Draw note blocks
        draw_notes(painter, self.notes, self.time_scale)
        
        # Draw playhead
        draw_playhead(painter, self.playhead_position, self.time_scale, self.height())

    def mousePressEvent(self, event):
        """Handle mouse press events for interactive features"""
        # Check if click is in the piano roll area (to the right of the keyboard)
        if event.x() > WHITE_KEY_WIDTH:
            # Set playhead position based on click, using the current time_scale
            self.playhead_position = (event.x() - WHITE_KEY_WIDTH) / self.time_scale
            self.update()
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for interactive features"""
        # This can be expanded to show tooltips or handle drag operations
        super().mouseMoveEvent(event)
