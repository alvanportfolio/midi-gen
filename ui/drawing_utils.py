from PySide6.QtCore import Qt, QRect, QPoint, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QLinearGradient, QFont, QRadialGradient, QFontMetrics
import pretty_midi

from config.constants import (
    MIN_PITCH, MAX_PITCH, WHITE_KEY_WIDTH, BLACK_KEY_WIDTH,
    WHITE_KEY_HEIGHT, BLACK_KEY_HEIGHT,
    MIN_LABEL_PITCH, MAX_LABEL_PITCH
)
from config import theme # Updated to import the whole module

# Assuming these are defined in theme.py (if not, they will be added later)
# For now, using fallbacks if specific names are not yet in the imported theme object.
# PIANO_KEY_WHITE_COLOR = getattr(theme, 'PIANO_KEY_WHITE_COLOR', theme.WHITE_KEY_COLOR) # Already exists
# PIANO_KEY_BLACK_COLOR = getattr(theme, 'PIANO_KEY_BLACK_COLOR', theme.BLACK_KEY_COLOR) # Already exists
# PIANO_KEY_BORDER_COLOR = getattr(theme, 'PIANO_KEY_BORDER_COLOR', theme.KEY_BORDER_COLOR) # Already exists
# PIANO_KEY_LABEL_COLOR = getattr(theme, 'PIANO_KEY_LABEL_COLOR', theme.PRIMARY_TEXT_COLOR.darker(150)) # Example fallback
# PIANO_KEY_BLACK_LABEL_COLOR = getattr(theme, 'PIANO_KEY_BLACK_LABEL_COLOR', theme.PRIMARY_TEXT_COLOR.lighter(150)) # Example fallback
# NOTE_LABEL_COLOR = getattr(theme, 'NOTE_LABEL_COLOR', QColor(0,0,0,180)) # Example fallback
# PLAYHEAD_TRIANGLE_COLOR = getattr(theme, 'PLAYHEAD_TRIANGLE_COLOR', theme.PLAYHEAD_COLOR) # Example fallback
# PIANO_KEY_SEPARATOR_COLOR = getattr(theme, 'PIANO_KEY_SEPARATOR_COLOR', theme.BORDER_COLOR_NORMAL) # Example fallback


def draw_time_grid(painter, width, height, time_scale, bpm, time_signature_numerator, time_signature_denominator, parent_widget, vertical_zoom_factor=1.0):
    """Draw the time grid with beats and measures and horizontal note lines"""
    keyboard_width = WHITE_KEY_WIDTH # This constant is from config.constants, not theme
    
    effective_white_key_height = WHITE_KEY_HEIGHT * vertical_zoom_factor # WHITE_KEY_HEIGHT from config.constants
    
    current_viewport_y_offset = 0
    if parent_widget and hasattr(parent_widget, 'verticalScrollBar'):
        current_viewport_y_offset = parent_widget.verticalScrollBar().value()
    elif parent_widget and hasattr(parent_widget, 'parentWidget') and parent_widget.parentWidget():
        grandparent_obj = parent_widget.parentWidget()
        if grandparent_obj and hasattr(grandparent_obj, 'verticalScrollBar'):
            current_viewport_y_offset = grandparent_obj.verticalScrollBar().value()
    
    # Draw horizontal lines for note rows
    painter.setPen(QPen(theme.KEY_GRID_LINE_COLOR, 0.8, Qt.SolidLine)) # Use new name, subtle width
    for pitch in range(MIN_PITCH, MAX_PITCH + 1):
        y_pos = (MAX_PITCH - pitch) * effective_white_key_height
        painter.drawLine(keyboard_width, int(y_pos), width, int(y_pos))
        note_name = pretty_midi.note_number_to_name(pitch)
        if note_name.endswith('C') and '#' not in note_name:
            highlight_rect = QRect(keyboard_width, int(y_pos), width - keyboard_width, int(effective_white_key_height))
            painter.fillRect(highlight_rect, theme.GRID_ROW_HIGHLIGHT_COLOR)

    # Time signature display
    ts_text = f"{time_signature_numerator}/{time_signature_denominator}"
    painter.setPen(QPen(theme.SECONDARY_TEXT_COLOR, 1.0))
    painter.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S, weight=theme.FONT_WEIGHT_BOLD))
    ts_x_pos = keyboard_width + theme.PADDING_S
    ts_y_pos = current_viewport_y_offset + theme.PADDING_M + theme.FONT_SIZE_S # Adjusted for font size
    painter.drawText(ts_x_pos, ts_y_pos, ts_text)

    actual_pixels_per_quarter_note = 0
    if bpm > 0:
        seconds_per_quarter_note = 60.0 / bpm
        actual_pixels_per_quarter_note = time_scale * seconds_per_quarter_note
    
    # Draw sixteenth note lines (very faint)
    painter.setPen(QPen(theme.GRID_LINE_COLOR, 0.5, Qt.DotLine)) # Subtle width
    sixteenth_note_step_pixels = actual_pixels_per_quarter_note / 4.0 if actual_pixels_per_quarter_note > 0 else 0
    if sixteenth_note_step_pixels > 5: # Only draw if lines are reasonably spaced
        for i in range(int(width / sixteenth_note_step_pixels) + 1):
            if i % 4 != 0:
                x = i * sixteenth_note_step_pixels + keyboard_width
                painter.drawLine(int(x), 0, int(x), height)

    pixels_per_beat = actual_pixels_per_quarter_note * (4.0 / time_signature_denominator) if time_signature_denominator > 0 else actual_pixels_per_quarter_note
    
    # Draw beat lines (more visible than grid, less than measure)
    if pixels_per_beat > 0:
        painter.setPen(QPen(theme.GRID_BEAT_LINE_COLOR, 0.7, Qt.SolidLine)) # Subtle width
        for i in range(int(width / pixels_per_beat) + 1):
            if i % time_signature_numerator != 0:
                x = i * pixels_per_beat + keyboard_width
                painter.drawLine(int(x), 0, int(x), height)

    # Draw measure lines (most prominent grid line)
    if pixels_per_beat > 0 and time_signature_numerator > 0:
        pixels_per_measure = pixels_per_beat * time_signature_numerator
        if pixels_per_measure > 0:
            painter.setPen(QPen(theme.GRID_MEASURE_LINE_COLOR, 1.0, Qt.SolidLine)) # Slightly more prominent
            measure_number_y_pos = current_viewport_y_offset + theme.PADDING_M + theme.FONT_SIZE_S
            for i in range(int(width / pixels_per_measure) + 1):
                x = i * pixels_per_measure + keyboard_width
                painter.drawLine(int(x), 0, int(x), height)
                painter.setPen(QPen(theme.SECONDARY_TEXT_COLOR, 1.0))
                painter.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS))
                painter.drawText(int(x + theme.PADDING_XS), measure_number_y_pos, str(i + 1))
            
    # Draw keyboard separator line
    # Using BORDER_COLOR_NORMAL for a standard separator
    piano_key_separator_color = getattr(theme, 'PIANO_KEY_SEPARATOR_COLOR', theme.BORDER_COLOR_NORMAL)
    painter.setPen(QPen(piano_key_separator_color, 1.0)) 
    painter.drawLine(keyboard_width, 0, keyboard_width, height)

def draw_piano_keys(painter, vertical_zoom_factor=1.0):
    """Draw the piano keyboard on the left side"""
    effective_white_key_height = WHITE_KEY_HEIGHT * vertical_zoom_factor
    effective_black_key_height = BLACK_KEY_HEIGHT * vertical_zoom_factor
    drawn_black_keys = set()

    # Define label colors (assuming these will be added to theme.py)
    piano_key_label_color = getattr(theme, 'PIANO_KEY_LABEL_COLOR', theme.PRIMARY_TEXT_COLOR.darker(180)) # Darker text for light keys
    piano_key_black_label_color = getattr(theme, 'PIANO_KEY_BLACK_LABEL_COLOR', theme.PRIMARY_TEXT_COLOR.lighter(180)) # Lighter text for dark keys
    
    # Draw white keys first
    for pitch in range(MIN_PITCH, MAX_PITCH + 1):
        pitch_class = pitch % 12
        is_white = pitch_class in [0, 2, 4, 5, 7, 9, 11]
        if is_white:
            y_pos_key_top = (MAX_PITCH - pitch) * effective_white_key_height
            key_rect = QRect(0, int(y_pos_key_top), WHITE_KEY_WIDTH, int(effective_white_key_height))
            
            base_color = theme.WHITE_KEY_COLOR # New theme constant
            gradient = QLinearGradient(key_rect.topLeft(), key_rect.bottomLeft())
            gradient.setColorAt(0.0, base_color.lighter(105))
            gradient.setColorAt(1.0, base_color.darker(102))
            painter.fillRect(key_rect, gradient)
            painter.setPen(QPen(theme.KEY_BORDER_COLOR, 0.5)) # Use new theme constant, thin border
            painter.drawRect(key_rect)
    
    # Draw black keys on top
    for pitch in range(MIN_PITCH, MAX_PITCH + 1):
        pitch_class = pitch % 12
        is_black = pitch_class in [1, 3, 6, 8, 10]
        if is_black:
            if pitch in drawn_black_keys: continue
            drawn_black_keys.add(pitch)
            y_pos_key_top = (MAX_PITCH - pitch) * effective_white_key_height
            key_rect = QRect(0, int(y_pos_key_top), BLACK_KEY_WIDTH, int(effective_black_key_height))
            
            base_color = theme.BLACK_KEY_COLOR # New theme constant
            gradient = QLinearGradient(key_rect.topLeft(), key_rect.bottomLeft())
            gradient.setColorAt(0.0, base_color.lighter(115)) # Black keys get less intense gradient
            gradient.setColorAt(1.0, base_color)
            painter.fillRect(key_rect, gradient)
            painter.setPen(QPen(theme.KEY_BORDER_COLOR, 0.5)) # Use new theme constant
            painter.drawRect(key_rect)

    # Draw labels on keys
    label_font = QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S) # Use theme font
    painter.setFont(label_font)
    metrics = QFontMetrics(label_font)

    for pitch_label in range(MIN_LABEL_PITCH, MAX_LABEL_PITCH + 1):
        if pitch_label < MIN_PITCH or pitch_label > MAX_PITCH: continue
        pitch_class = pitch_label % 12
        is_white_key_for_label = pitch_class in [0, 2, 4, 5, 7, 9, 11]
        
        original_note_name = pretty_midi.note_number_to_name(pitch_label)
        # ... (name correction logic remains same)
        note_part = original_note_name[:-1]
        octave_str = original_note_name[-1:]
        corrected_label_name = original_note_name
        if octave_str.isdigit():
            octave_part = int(octave_str)
            corrected_label_name = f"{note_part}{octave_part + 1}"

        key_slot_y_top = (MAX_PITCH - pitch_label) * effective_white_key_height
        
        if is_white_key_for_label:
            text_rect = QRect(0, int(key_slot_y_top), WHITE_KEY_WIDTH, int(effective_white_key_height))
            painter.setPen(piano_key_label_color)
            painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name)
        else:
            if pitch_label in drawn_black_keys: # Ensure label is only for drawn keys
                black_key_rect = QRect(0, int(key_slot_y_top), BLACK_KEY_WIDTH, int(effective_black_key_height))
                painter.setPen(piano_key_black_label_color)
                painter.drawText(black_key_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name)

def draw_notes(painter, notes, time_scale, vertical_zoom_factor=1.0):
    """Draw the MIDI notes as colored rectangles"""
    effective_white_key_height = WHITE_KEY_HEIGHT * vertical_zoom_factor
    effective_black_key_height = BLACK_KEY_HEIGHT * vertical_zoom_factor
    note_label_color = getattr(theme, 'NOTE_LABEL_COLOR', QColor(0,0,0,180)) # Fallback

    for note in notes:
        if not hasattr(note, 'pitch') or not hasattr(note, 'start') or not hasattr(note, 'end'): continue
        pitch = note.pitch
        if pitch < MIN_PITCH or pitch > MAX_PITCH: continue
        
        y_pos = (MAX_PITCH - pitch) * effective_white_key_height 
        x_pos = note.start * time_scale + WHITE_KEY_WIDTH
        width = max((note.end - note.start) * time_scale, 4)
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
        # Use new theme note colors
        if velocity < 50: color = theme.NOTE_LOW_COLOR
        elif velocity < 90: color = theme.NOTE_MED_COLOR
        else: color = theme.NOTE_HIGH_COLOR
            
        gradient = QLinearGradient(x_pos, y_pos + y_offset, x_pos, y_pos + y_offset + height)
        gradient.setColorAt(0, color.lighter(130))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(110))
        
        painter.setPen(QPen(theme.NOTE_BORDER_COLOR, 0.5)) # Use new theme constant, subtle
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(int(x_pos), int(y_pos + y_offset), int(width), int(height), 
                                theme.BORDER_RADIUS_S, theme.BORDER_RADIUS_S) # Use theme radius
        
        # Note labels (optional)
        original_note_name = pretty_midi.note_number_to_name(pitch)
        # ... (name correction logic remains same)
        note_part_label = original_note_name[:-1]
        octave_str_label = original_note_name[-1:]
        corrected_label_name_note = original_note_name
        if octave_str_label.isdigit():
            octave_part_label = int(octave_str_label)
            corrected_label_name_note = f"{note_part_label}{octave_part_label + 1}"

        note_block_font = QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS) # Use theme font
        note_block_font.setBold(True) # Keep bold for readability on notes
        painter.setFont(note_block_font)
        painter.setPen(note_label_color) # Use defined note label color
        
        font_metrics = QFontMetrics(painter.font())
        text_width_needed = font_metrics.horizontalAdvance(corrected_label_name_note)
        text_height_needed = font_metrics.height()
        note_content_rect = QRectF(x_pos, y_pos + y_offset, width, height)
        
        if text_width_needed <= note_content_rect.width() - (theme.PADDING_XS * 2) and \
           text_height_needed <= note_content_rect.height() - (theme.PADDING_XS * 2):
            painter.drawText(note_content_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name_note)

def draw_playhead(painter, playhead_position, time_scale, height):
    """Draw the playhead indicator"""
    if playhead_position >= 0: # Allow drawing at position 0
        playhead_x = playhead_position * time_scale + WHITE_KEY_WIDTH
        
        # Main line
        playhead_pen = QPen(theme.PLAYHEAD_COLOR, 2) # Use theme color, 2px width
        painter.setPen(playhead_pen)
        painter.drawLine(int(playhead_x), 0, int(playhead_x), height)
        
        # Triangle marker
        triangle_size = theme.ICON_SIZE_S // 2 # Base size on theme icon size
        playhead_triangle_color = getattr(theme, 'PLAYHEAD_TRIANGLE_COLOR', theme.PLAYHEAD_COLOR) # Use defined or fallback
        
        painter.setBrush(QBrush(playhead_triangle_color)) # Solid color
        painter.setPen(Qt.NoPen) # No border for triangle for cleaner look
        
        points = [
            QPoint(int(playhead_x), 0),
            QPoint(int(playhead_x - triangle_size), int(triangle_size * 1.5)), # Make triangle a bit taller
            QPoint(int(playhead_x + triangle_size), int(triangle_size * 1.5))
        ]
        painter.drawPolygon(points)