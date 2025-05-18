import sys
from PySide6.QtWidgets import QWidget, QApplication, QSizePolicy
from PySide6.QtCore import Qt, QRect, QSize, QPoint, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont, QRadialGradient, QFontMetrics
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

        # --- Vertical Grid Lines (Time) ---
        current_pixels_per_second = self.time_scale # self.time_scale is pixels per second

        # Calculate current viewport Y offset for fixed elements (like time signature, bar numbers)
        current_viewport_y_offset = 0
        parent_obj = self.parent()
        if parent_obj and hasattr(parent_obj, 'verticalScrollBar'): # Check if parent is QScrollArea
            current_viewport_y_offset = parent_obj.verticalScrollBar().value()
        elif parent_obj and hasattr(parent_obj, 'parentWidget') and parent_obj.parentWidget(): # Check if parent is viewport
            grandparent_obj = parent_obj.parentWidget()
            if grandparent_obj and hasattr(grandparent_obj, 'verticalScrollBar'): # Check if grandparent is QScrollArea
                 current_viewport_y_offset = grandparent_obj.verticalScrollBar().value()

        # Draw Time Signature Label (fixed vertically, scrolls horizontally with content)
        # Positioned at top-left of the grid area (right of piano keys)
        ts_text = f"{self.time_signature_numerator}/{self.time_signature_denominator}"
        # Using a slightly distinct color/font for the time signature for clarity
        painter.setPen(QPen(QColor(200, 200, 220, 220), 1.0)) 
        painter.setFont(QFont("Arial", 8, QFont.Bold)) # Arial, size 8, Bold
        
        # Calculate text metrics for potential centering or advanced placement if needed later
        # font_metrics = QFontMetrics(painter.font())
        # text_width = font_metrics.horizontalAdvance(ts_text)
        # text_height = font_metrics.height()
        
        ts_x_pos = keyboard_width + 6  # 6px padding from the piano keys
        ts_y_pos = current_viewport_y_offset + 15 # 15px padding from top of viewport
        painter.drawText(ts_x_pos, ts_y_pos, ts_text)

        actual_pixels_per_quarter_note = 0
        if self.bpm > 0:
            seconds_per_quarter_note = 60.0 / self.bpm
            actual_pixels_per_quarter_note = current_pixels_per_second * seconds_per_quarter_note
        
        # 1. Sub-beats (e.g., 16th notes relative to quarter notes)
        painter.setPen(QPen(GRID_COLOR, 1.0, Qt.DotLine))
        sixteenth_note_step_pixels = actual_pixels_per_quarter_note / 4.0 if actual_pixels_per_quarter_note > 0 else 0
        if sixteenth_note_step_pixels > 0:
            num_sixteenths = width / sixteenth_note_step_pixels
            for i in range(int(num_sixteenths) + 1):
                # Draw a 16th note line if it's not a quarter note line
                # (Quarter note lines will be drawn by the beat logic if applicable, or measure logic)
                if i % 4 != 0:
                    x = i * sixteenth_note_step_pixels + keyboard_width
                    painter.drawLine(int(x), 0, int(x), height)

        # 2. Beat lines (based on time signature denominator)
        # The "beat" is what the denominator of the time signature refers to.
        # E.g., in 3/4, a beat is a quarter note. In 6/8, a beat is an eighth note.
        try:
            beat_value_in_quarters = 4.0 / self.time_signature_denominator
        except ZeroDivisionError:
            beat_value_in_quarters = 1.0 # Default to quarter note if denominator is zero

        pixels_per_beat = actual_pixels_per_quarter_note * beat_value_in_quarters
        
        if pixels_per_beat > 0:
            painter.setPen(QPen(BEAT_COLOR, 1.2, Qt.SolidLine))
            num_beats_in_width = width / pixels_per_beat
            for i in range(int(num_beats_in_width) + 1):
                # Draw a beat line if it's not a measure line
                # (Measure lines will be drawn by the measure logic with a stronger pen)
                if i % self.time_signature_numerator != 0:
                    x = i * pixels_per_beat + keyboard_width
                    painter.drawLine(int(x), 0, int(x), height)

        # 3. Measure lines
        if pixels_per_beat > 0 and self.time_signature_numerator > 0:
            pixels_per_measure = pixels_per_beat * self.time_signature_numerator
            if pixels_per_measure > 0:
                painter.setPen(QPen(MEASURE_COLOR, 1.5, Qt.SolidLine))
                num_measures_in_width = width / pixels_per_measure

                # current_viewport_y_offset is calculated at the beginning of the "Vertical Grid Lines (Time)" section.
                # Ensure bar numbers use the same vertical anchor point as the time signature.
                measure_number_y_pos = current_viewport_y_offset + 15 # Use same 15px padding as time signature label

                for i in range(int(num_measures_in_width) + 1):
                    x = i * pixels_per_measure + keyboard_width
                    painter.drawLine(int(x), 0, int(x), height)
                    
                    # Draw measure numbers, fixed at the top of the viewport
                    painter.setPen(QPen(QColor(180, 180, 190, 180), 1.0))
                    painter.setFont(QFont("Arial", 7)) # Ensure font is reset
                    painter.drawText(int(x + 3), measure_number_y_pos, str(i + 1))
            
        # Draw border between piano keys and grid
        painter.setPen(QPen(KEY_BORDER_COLOR, 1.5))  # Increased width from 1.2 to 1.5
        painter.drawLine(keyboard_width, 0, keyboard_width, height)
    
    def draw_piano_keys(self, painter):
        """Draw the piano keyboard on the left side"""
        # General pen for key borders - can be overridden for black/white specifically
        default_key_border_pen = QPen(KEY_BORDER_COLOR, 0.5)
        
        # Calculate the total height required for all notes
        total_height = (MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT
        
        # Create a list of drawn black key positions to avoid duplicates
        drawn_black_keys = set()
        
        # First pass: Draw white keys
        for pitch in range(MIN_PITCH, MAX_PITCH + 1):
            # Use modulo arithmetic to determine if a note is a white key
            # C, D, E, F, G, A, B are white keys (0, 2, 4, 5, 7, 9, 11 in the 12-note pattern)
            pitch_class = pitch % 12
            is_white = pitch_class in [0, 2, 4, 5, 7, 9, 11]
            
            if is_white:
                y_pos_key_top = total_height - ((pitch - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)
                key_rect = QRect(0, int(y_pos_key_top), WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
                
                # Modern gradient for white keys (vertical)
                white_gradient = QLinearGradient(key_rect.topLeft(), key_rect.bottomLeft())
                white_gradient.setColorAt(0.0, QColor(245, 245, 245)) # Slightly brighter top
                white_gradient.setColorAt(1.0, QColor(220, 220, 220)) # Slightly darker bottom
                
                painter.fillRect(key_rect, white_gradient)
                painter.setPen(QPen(QColor(180, 180, 180), 0.5)) # Slightly darker border for white keys
                painter.drawRect(key_rect)
        
        # Second pass: Draw black keys on top
        for pitch in range(MIN_PITCH, MAX_PITCH + 1):
            # C#, D#, F#, G#, A# are black keys (1, 3, 6, 8, 10 in the 12-note pattern)
            pitch_class = pitch % 12
            is_black = pitch_class in [1, 3, 6, 8, 10]
            
            if is_black:
                # Check if we already drew this black key
                if pitch in drawn_black_keys:
                    continue
                
                drawn_black_keys.add(pitch)
                
                # Position the black key
                y_pos_key_top = total_height - ((pitch - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)
                key_rect = QRect(0, int(y_pos_key_top), BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
                
                # Subtle gradient for black keys
                black_gradient = QLinearGradient(key_rect.topLeft(), key_rect.bottomLeft())
                black_gradient.setColorAt(0.0, BLACK_KEY_COLOR.lighter(125)) # QColor(30,30,35)
                black_gradient.setColorAt(1.0, BLACK_KEY_COLOR)
                
                painter.fillRect(key_rect, black_gradient)
                # Subtle stroke for black keys
                painter.setPen(QPen(BLACK_KEY_COLOR.lighter(150), 0.5)) 
                painter.drawRect(key_rect)

        # Draw note labels (C2 to C7, displayed as C3 to C8)
        label_font = QFont("Segoe UI", 8)
        label_font.setBold(False)
        painter.setFont(label_font)
        
        MIN_LABEL_PITCH = 36  # C2 MIDI note number (will be displayed as C3)
        MAX_LABEL_PITCH = 96  # C7 MIDI note number (will be displayed as C8)

        for pitch_label in range(MIN_LABEL_PITCH, MAX_LABEL_PITCH + 1):
            if pitch_label < MIN_PITCH or pitch_label > MAX_PITCH:  # Ensure label is for a drawable key
                continue

            # Use modulo to determine key type
            pitch_class = pitch_label % 12
            is_white_key_for_label = pitch_class in [0, 2, 4, 5, 7, 9, 11]
            
            # Get note name
            original_note_name = pretty_midi.note_number_to_name(pitch_label)
            note_part = original_note_name[:-1]
            octave_str = original_note_name[-1:]
            
            # Adjust octave number (display octave + 1)
            corrected_label_name = original_note_name  # Fallback
            if octave_str.isdigit():
                octave_part = int(octave_str)
                corrected_label_name = f"{note_part}{octave_part + 1}"
            
            key_slot_y_top = total_height - ((pitch_label - MIN_PITCH + 1) * WHITE_KEY_HEIGHT)

            if is_white_key_for_label:
                text_rect = QRect(0, int(key_slot_y_top), WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
                painter.setPen(QColor(70, 70, 70))  # Darker gray text for better contrast
                painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name)
            else:
                # For black keys, only draw labels for those we actually drew
                if pitch_label in drawn_black_keys:
                    # Black key's actual rectangle for text centering
                    black_key_rect = QRect(0, int(key_slot_y_top), BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
                    painter.setPen(QColor(210, 210, 210))  # Lighter gray text
                    painter.drawText(black_key_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name)
    
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
            # Use modulo to consistently identify white/black keys
            pitch_class = pitch % 12
            is_white = pitch_class in [0, 2, 4, 5, 7, 9, 11]
            
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

            # Add note label text inside the note block with updated styling
            original_note_name = pretty_midi.note_number_to_name(pitch)
            note_part_label = original_note_name[:-1]
            octave_str_label = original_note_name[-1:]
            corrected_label_name_note = original_note_name # Fallback
            if octave_str_label.isdigit():
                octave_part_label = int(octave_str_label)
                corrected_label_name_note = f"{note_part_label}{octave_part_label + 1}"
            
            # Set font for note block labels with bold
            note_block_font = QFont("Segoe UI", 7)
            note_block_font.setBold(True)  # Make the text bold
            painter.setFont(note_block_font)
            painter.setPen(QColor(0, 0, 0))  # Black text for better visibility
            
            # Check if text fits (with some padding)
            font_metrics = QFontMetrics(painter.font())
            text_width_needed = font_metrics.horizontalAdvance(corrected_label_name_note)
            text_height_needed = font_metrics.height()

            # Define the rectangle for the note block content
            note_content_rect = QRectF(x_pos, y_pos + y_offset, width, height)

            if text_width_needed <= note_content_rect.width() - 4 and \
               text_height_needed <= note_content_rect.height() - 2:
                painter.drawText(note_content_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name_note)
    
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