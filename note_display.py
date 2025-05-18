import sys
from PySide6.QtWidgets import QWidget, QApplication, QSizePolicy
from PySide6.QtCore import Qt, QRect, QSize, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, QRadialGradient
import pretty_midi

# Constants for piano roll display
MIN_PITCH = 21  # A0
MAX_PITCH = 108  # C8
WHITE_KEY_WIDTH = 60
BLACK_KEY_WIDTH = 40
WHITE_KEY_HEIGHT = 24
BLACK_KEY_HEIGHT = 16
BASE_TIME_SCALE = 100  # Base pixels per second (at 120 BPM)
DEFAULT_BPM = 120

# Theme Colors - Dark professional theme
BG_COLOR = QColor(28, 28, 32)
GRID_COLOR = QColor(40, 40, 45, 150)  # Increased opacity for better visibility
BEAT_COLOR = QColor(60, 60, 65, 180)  # Increased opacity
MEASURE_COLOR = QColor(95, 95, 100)  # Slightly brighter
ROW_HIGHLIGHT_COLOR = QColor(45, 45, 50, 100)  # More visible
KEY_GRID_COLOR = QColor(50, 50, 55, 120)  # Increased opacity
PLAYHEAD_COLOR = QColor(255, 120, 0, 180)

# Piano key colors
WHITE_KEY_COLOR = QColor(240, 240, 240)
BLACK_KEY_COLOR = QColor(30, 30, 35)
KEY_BORDER_COLOR = QColor(100, 100, 100, 80)  # Thinner, semi-transparent

# Note colors based on velocity with better aesthetics
NOTE_COLORS = {
    'low': QColor(80, 200, 120),     # Softer green for low velocity
    'med': QColor(70, 180, 210),     # Soft blue for medium velocity
    'high': QColor(230, 120, 190)    # Purple-pink for high velocity
}

class PianoRollDisplay(QWidget):
    """Widget that displays MIDI notes in a piano roll format"""
    
    def __init__(self, notes=None, parent=None):
        super().__init__(parent)
        self.notes = notes or []
        self.playhead_position = 0.0
        self.bpm = DEFAULT_BPM  # Default tempo
        self.time_scale = BASE_TIME_SCALE  # Will be adjusted based on BPM
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
        self.draw_time_grid(painter)
        
        # Draw piano keys
        self.draw_piano_keys(painter)
        
        # Draw note blocks
        self.draw_notes(painter)
        
        # Draw playhead
        self.draw_playhead(painter)
    
    def draw_time_grid(self, painter):
        """Draw the time grid with beats and measures and horizontal note lines"""
        width = self.width()
        height = self.height()
        
        # Get keyboard width for offset
        keyboard_width = WHITE_KEY_WIDTH
        
        # Calculate the total height required for all notes
        total_height = (MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT
        
        # Draw horizontal grid lines (note rows)
        painter.setPen(QPen(KEY_GRID_COLOR, 1.0, Qt.SolidLine))  # Increased width from 0.5 to 1.0
        
        # Draw a row for each pitch
        for pitch in range(MIN_PITCH, MAX_PITCH + 1):
            # Calculate position from the bottom (lower pitches at bottom)
            y_pos = total_height - ((pitch - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)
            
            # Draw grid line
            painter.drawLine(keyboard_width, int(y_pos), width, int(y_pos))
            
            # Highlight C notes with slightly darker background for better row identification
            note_name = pretty_midi.note_number_to_name(pitch)
            if note_name.endswith('C') and '#' not in note_name:
                highlight_rect = QRect(keyboard_width, int(y_pos), width - keyboard_width, WHITE_KEY_HEIGHT)
                painter.fillRect(highlight_rect, ROW_HIGHLIGHT_COLOR)
        
        # Draw vertical grid lines (time) - adjusted for BPM
        painter.setPen(QPen(GRID_COLOR, 1.0, Qt.DotLine))  # Increased width from 0.5 to 1.0
        
        # 16th notes (light grid lines)
        sixteenth_step = self.time_scale / 4.0
        steps = width / sixteenth_step
        for i in range(int(steps) + 1):
            x = i * sixteenth_step + keyboard_width
            if i % 4 != 0:  # Skip drawing on quarter notes (beats)
                painter.drawLine(int(x), 0, int(x), height)
        
        # Quarter notes (beats)
        painter.setPen(QPen(BEAT_COLOR, 1.2, Qt.SolidLine))  # Increased width from 0.7 to 1.2
        beat_step = self.time_scale
        beats = width / beat_step
        for i in range(int(beats) + 1):
            x = i * beat_step + keyboard_width
            if i % 4 != 0:  # Skip drawing on measure lines
                painter.drawLine(int(x), 0, int(x), height)
        
        # Measures (assuming 4/4 time)
        painter.setPen(QPen(MEASURE_COLOR, 1.5, Qt.SolidLine))  # Increased width from 0.9 to 1.5
        measure_step = self.time_scale * 4
        measures = width / measure_step
        for i in range(int(measures) + 1):
            x = i * measure_step + keyboard_width
            painter.drawLine(int(x), 0, int(x), height)
            
            # Draw measure numbers (small and subtle)
            painter.setPen(QPen(QColor(180, 180, 190, 180), 1.0))  # Increased visibility
            painter.setFont(QFont("Arial", 7))
            painter.drawText(int(x + 3), 12, str(i + 1))
            
        # Draw border between piano keys and grid
        painter.setPen(QPen(KEY_BORDER_COLOR, 1.5))  # Increased width from 1.2 to 1.5
        painter.drawLine(keyboard_width, 0, keyboard_width, height)
    
    def draw_piano_keys(self, painter):
        """Draw the piano keyboard on the left side"""
        # Draw white keys first
        painter.setPen(QPen(KEY_BORDER_COLOR, 0.5))  # Thinner border
        
        # Calculate the total height required for all notes
        total_height = (MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT
        
        # Draw white keys (fixed: Draw from low notes at bottom to high notes at top)
        for pitch in range(MIN_PITCH, MAX_PITCH + 1):
            # Check if this is a white key
            note_name = pretty_midi.note_number_to_name(pitch)
            is_white = '#' not in note_name
            
            if is_white:
                # Calculate position from the bottom (lower pitches at bottom)
                y_pos = total_height - ((pitch - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)
                key_rect = QRect(0, int(y_pos), WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
                
                # Create subtle gradient for white keys
                white_gradient = QLinearGradient(0, y_pos, WHITE_KEY_WIDTH, y_pos)
                white_gradient.setColorAt(0, WHITE_KEY_COLOR)
                white_gradient.setColorAt(1, WHITE_KEY_COLOR.darker(105))
                
                painter.fillRect(key_rect, white_gradient)
                painter.drawRect(key_rect)
                
                # Draw note name
                painter.setPen(QColor(80, 80, 85))
                painter.setFont(QFont("Arial", 7))
                
                # Calculate text position - better alignment
                text_rect = QRect(5, int(y_pos + 2), WHITE_KEY_WIDTH - 10, WHITE_KEY_HEIGHT - 4)
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, note_name)
        
        # Now draw black keys on top
        for pitch in range(MIN_PITCH, MAX_PITCH + 1):
            note_name = pretty_midi.note_number_to_name(pitch)
            is_white = '#' not in note_name
            
            if not is_white:
                # Calculate position from the bottom
                y_pos = total_height - ((pitch - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)
                key_rect = QRect(0, int(y_pos - BLACK_KEY_HEIGHT // 2), 
                                 BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
                
                # Create gradient for black keys
                black_gradient = QLinearGradient(0, y_pos, BLACK_KEY_WIDTH, y_pos)
                black_gradient.setColorAt(0, BLACK_KEY_COLOR)
                black_gradient.setColorAt(1, BLACK_KEY_COLOR.lighter(120))
                
                painter.fillRect(key_rect, black_gradient)
                painter.drawRect(key_rect)
    
    def draw_notes(self, painter):
        """Draw the MIDI notes as colored rectangles"""
        # Calculate the total height required for all notes
        total_height = (MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT
        
        for note in self.notes:
            if not hasattr(note, 'pitch') or not hasattr(note, 'start') or not hasattr(note, 'end'):
                continue
                
            # Calculate note position and size
            pitch = note.pitch
            if pitch < MIN_PITCH or pitch > MAX_PITCH:
                continue
                
            # Calculate position from the bottom (fixed: lower pitches at bottom)
            y_pos = total_height - ((pitch - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)
            
            # Adjust position for grid, using the current time_scale
            x_pos = note.start * self.time_scale + WHITE_KEY_WIDTH
            width = max((note.end - note.start) * self.time_scale, 4)  # Ensure minimum width
            
            # Calculate height based on key type for better visual distinction
            note_name = pretty_midi.note_number_to_name(pitch)
            is_white = '#' not in note_name
            
            if is_white:
                height = WHITE_KEY_HEIGHT - 4  # Slightly smaller than the grid cell
                y_offset = 2  # Center in grid cell
            else:
                height = WHITE_KEY_HEIGHT - 8  # Even smaller for black keys
                y_offset = 4  # More centering for black keys
            
            # Select color based on velocity
            velocity = getattr(note, 'velocity', 64)
            if velocity < 50:
                color = NOTE_COLORS['low']
            elif velocity < 90:
                color = NOTE_COLORS['med']
            else:
                color = NOTE_COLORS['high']
            
            # Create gradient for 3D effect
            gradient = QLinearGradient(x_pos, y_pos, x_pos, y_pos + height)
            gradient.setColorAt(0, color.lighter(130))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.darker(110))
            
            # Draw note rectangle with very thin border
            painter.setPen(QPen(color.darker(120), 0.5))  # Thinner border
            painter.setBrush(QBrush(gradient))
            
            # Draw with rounded corners for a more professional look
            painter.drawRoundedRect(
                int(x_pos), 
                int(y_pos + y_offset), 
                int(width), 
                int(height), 
                4, 4
            )
    
    def draw_playhead(self, painter):
        """Draw the playhead indicator"""
        if self.playhead_position > 0:
            playhead_x = self.playhead_position * self.time_scale + WHITE_KEY_WIDTH
            
            # Draw semi-transparent vertical gradient for playhead line
            playhead_gradient = QLinearGradient(0, 0, 0, self.height())
            playhead_gradient.setColorAt(0, QColor(255, 150, 50, 200))
            playhead_gradient.setColorAt(1, QColor(255, 100, 20, 180))
            
            playhead_pen = QPen(playhead_gradient, 1.5)
            painter.setPen(playhead_pen)
            painter.drawLine(int(playhead_x), 0, int(playhead_x), self.height())
            
            # Draw a small triangle at the top of the playhead for better visibility
            triangle_size = 8
            
            # Create a nice gradient for the triangle
            tri_gradient = QRadialGradient(int(playhead_x), triangle_size/2, triangle_size)
            tri_gradient.setColorAt(0, QColor(255, 180, 70, 240))
            tri_gradient.setColorAt(1, QColor(255, 120, 0, 220))
            
            painter.setBrush(QBrush(tri_gradient))
            painter.setPen(Qt.NoPen)
            
            points = [
                QPoint(int(playhead_x), 0),
                QPoint(int(playhead_x - triangle_size/2), int(triangle_size)),
                QPoint(int(playhead_x + triangle_size/2), int(triangle_size))
            ]
            
            # Draw triangle at top of playhead
            painter.drawPolygon(points)
    
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