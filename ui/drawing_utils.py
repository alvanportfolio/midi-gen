from PySide6.QtCore import Qt, QRect, QPoint, QRectF
from PySide6.QtGui import QColor, QPen, QBrush, QLinearGradient, QFont, QRadialGradient, QFontMetrics
import pretty_midi

from config.constants import (
    MIN_PITCH, MAX_PITCH, WHITE_KEY_WIDTH, BLACK_KEY_WIDTH,
    WHITE_KEY_HEIGHT, BLACK_KEY_HEIGHT,
    MIN_LABEL_PITCH, MAX_LABEL_PITCH
)
from config.theme import (
    GRID_COLOR, BEAT_COLOR, MEASURE_COLOR, ROW_HIGHLIGHT_COLOR,
    KEY_GRID_COLOR, PLAYHEAD_COLOR, WHITE_KEY_COLOR, BLACK_KEY_COLOR,
    KEY_BORDER_COLOR, NOTE_COLORS
)

def draw_time_grid(painter, width, height, time_scale, bpm, time_signature_numerator, time_signature_denominator, parent_widget):
    """Draw the time grid with beats and measures and horizontal note lines"""
    keyboard_width = WHITE_KEY_WIDTH
    
    # Calculate proper total height for all pitches from MIN_PITCH to MAX_PITCH
    total_height = (MAX_PITCH - MIN_PITCH + 1) * WHITE_KEY_HEIGHT
    
    # Get scroll position
    current_viewport_y_offset = 0
    if parent_widget and hasattr(parent_widget, 'verticalScrollBar'):
        current_viewport_y_offset = parent_widget.verticalScrollBar().value()
    elif parent_widget and hasattr(parent_widget, 'parentWidget') and parent_widget.parentWidget():
        grandparent_obj = parent_widget.parentWidget()
        if grandparent_obj and hasattr(grandparent_obj, 'verticalScrollBar'):
            current_viewport_y_offset = grandparent_obj.verticalScrollBar().value()
    
    # Draw horizontal lines for note rows
    painter.setPen(QPen(KEY_GRID_COLOR, 1.0, Qt.SolidLine))
    for pitch in range(MIN_PITCH, MAX_PITCH + 1):
        y_pos = (MAX_PITCH - pitch) * WHITE_KEY_HEIGHT  # Fixed calculation to show all notes
        painter.drawLine(keyboard_width, int(y_pos), width, int(y_pos))
        note_name = pretty_midi.note_number_to_name(pitch)
        if note_name.endswith('C') and '#' not in note_name:
            highlight_rect = QRect(keyboard_width, int(y_pos), width - keyboard_width, WHITE_KEY_HEIGHT)
            painter.fillRect(highlight_rect, ROW_HIGHLIGHT_COLOR)

    # Time signature display
    ts_text = f"{time_signature_numerator}/{time_signature_denominator}"
    painter.setPen(QPen(QColor(200, 200, 220, 220), 1.0))
    painter.setFont(QFont("Arial", 8, QFont.Bold))
    ts_x_pos = keyboard_width + 6
    ts_y_pos = current_viewport_y_offset + 15
    painter.drawText(ts_x_pos, ts_y_pos, ts_text)

    # Calculate timing grids
    actual_pixels_per_quarter_note = 0
    if bpm > 0:
        seconds_per_quarter_note = 60.0 / bpm
        actual_pixels_per_quarter_note = time_scale * seconds_per_quarter_note
    
    # Draw sixteenth note lines
    painter.setPen(QPen(GRID_COLOR, 1.0, Qt.DotLine))
    sixteenth_note_step_pixels = actual_pixels_per_quarter_note / 4.0 if actual_pixels_per_quarter_note > 0 else 0
    if sixteenth_note_step_pixels > 0:
        num_sixteenths = width / sixteenth_note_step_pixels
        for i in range(int(num_sixteenths) + 1):
            if i % 4 != 0:
                x = i * sixteenth_note_step_pixels + keyboard_width
                painter.drawLine(int(x), 0, int(x), height)

    # Calculate beat timing
    try:
        beat_value_in_quarters = 4.0 / time_signature_denominator
    except ZeroDivisionError:
        beat_value_in_quarters = 1.0

    pixels_per_beat = actual_pixels_per_quarter_note * beat_value_in_quarters
    
    # Draw beat lines
    if pixels_per_beat > 0:
        painter.setPen(QPen(BEAT_COLOR, 1.2, Qt.SolidLine))
        num_beats_in_width = width / pixels_per_beat
        for i in range(int(num_beats_in_width) + 1):
            if i % time_signature_numerator != 0:
                x = i * pixels_per_beat + keyboard_width
                painter.drawLine(int(x), 0, int(x), height)

    # Draw measure lines
    if pixels_per_beat > 0 and time_signature_numerator > 0:
        pixels_per_measure = pixels_per_beat * time_signature_numerator
        if pixels_per_measure > 0:
            painter.setPen(QPen(MEASURE_COLOR, 1.5, Qt.SolidLine))
            num_measures_in_width = width / pixels_per_measure
            measure_number_y_pos = current_viewport_y_offset + 15
            for i in range(int(num_measures_in_width) + 1):
                x = i * pixels_per_measure + keyboard_width
                painter.drawLine(int(x), 0, int(x), height)
                painter.setPen(QPen(QColor(180, 180, 190, 180), 1.0))
                painter.setFont(QFont("Arial", 7))
                painter.drawText(int(x + 3), measure_number_y_pos, str(i + 1))
            
    # Draw keyboard separator line
    painter.setPen(QPen(KEY_BORDER_COLOR, 1.5))
    painter.drawLine(keyboard_width, 0, keyboard_width, height)

def draw_piano_keys(painter):
    """Draw the piano keyboard on the left side"""
    # Fixed calculation of positions to show all keys
    drawn_black_keys = set()
    
    # Draw white keys first
    for pitch in range(MIN_PITCH, MAX_PITCH + 1):
        pitch_class = pitch % 12
        is_white = pitch_class in [0, 2, 4, 5, 7, 9, 11]
        if is_white:
            y_pos_key_top = (MAX_PITCH - pitch) * WHITE_KEY_HEIGHT  # Fixed calculation
            key_rect = QRect(0, int(y_pos_key_top), WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
            white_gradient = QLinearGradient(key_rect.topLeft(), key_rect.bottomLeft())
            white_gradient.setColorAt(0.0, QColor(245, 245, 245))
            white_gradient.setColorAt(1.0, QColor(220, 220, 220))
            painter.fillRect(key_rect, white_gradient)
            painter.setPen(QPen(QColor(180, 180, 180), 0.5))
            painter.drawRect(key_rect)
    
    # Draw black keys on top
    for pitch in range(MIN_PITCH, MAX_PITCH + 1):
        pitch_class = pitch % 12
        is_black = pitch_class in [1, 3, 6, 8, 10]
        if is_black:
            if pitch in drawn_black_keys:
                continue
            drawn_black_keys.add(pitch)
            y_pos_key_top = (MAX_PITCH - pitch) * WHITE_KEY_HEIGHT  # Fixed calculation
            key_rect = QRect(0, int(y_pos_key_top), BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
            black_gradient = QLinearGradient(key_rect.topLeft(), key_rect.bottomLeft())
            black_gradient.setColorAt(0.0, BLACK_KEY_COLOR.lighter(125))
            black_gradient.setColorAt(1.0, BLACK_KEY_COLOR)
            painter.fillRect(key_rect, black_gradient)
            painter.setPen(QPen(BLACK_KEY_COLOR.lighter(150), 0.5))
            painter.drawRect(key_rect)

    # Draw labels on keys
    label_font = QFont("Segoe UI", 8)
    label_font.setBold(False)
    painter.setFont(label_font)
    for pitch_label in range(MIN_LABEL_PITCH, MAX_LABEL_PITCH + 1):
        if pitch_label < MIN_PITCH or pitch_label > MAX_PITCH:
            continue
        pitch_class = pitch_label % 12
        is_white_key_for_label = pitch_class in [0, 2, 4, 5, 7, 9, 11]
        original_note_name = pretty_midi.note_number_to_name(pitch_label)
        note_part = original_note_name[:-1]
        octave_str = original_note_name[-1:]
        corrected_label_name = original_note_name
        if octave_str.isdigit():
            octave_part = int(octave_str)
            corrected_label_name = f"{note_part}{octave_part + 1}"
        key_slot_y_top = (MAX_PITCH - pitch_label) * WHITE_KEY_HEIGHT  # Fixed calculation
        if is_white_key_for_label:
            text_rect = QRect(0, int(key_slot_y_top), WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
            painter.setPen(QColor(70, 70, 70))
            painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name)
        else:
            if pitch_label in drawn_black_keys:
                black_key_rect = QRect(0, int(key_slot_y_top), BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
                painter.setPen(QColor(210, 210, 210))
                painter.drawText(black_key_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name)

def draw_notes(painter, notes, time_scale):
    """Draw the MIDI notes as colored rectangles"""
    for note in notes:
        if not hasattr(note, 'pitch') or not hasattr(note, 'start') or not hasattr(note, 'end'):
            continue
        pitch = note.pitch
        if pitch < MIN_PITCH or pitch > MAX_PITCH:
            continue
        
        # Fixed y position calculation to show all notes
        y_pos = (MAX_PITCH - pitch) * WHITE_KEY_HEIGHT
        
        x_pos = note.start * time_scale + WHITE_KEY_WIDTH
        width = max((note.end - note.start) * time_scale, 4)
        pitch_class = pitch % 12
        is_white = pitch_class in [0, 2, 4, 5, 7, 9, 11]
        if is_white:
            height = WHITE_KEY_HEIGHT - 4
            y_offset = 2
        else:
            height = WHITE_KEY_HEIGHT - 8
            y_offset = 4
        velocity = getattr(note, 'velocity', 64)
        if velocity < 50:
            color = NOTE_COLORS['low']
        elif velocity < 90:
            color = NOTE_COLORS['med']
        else:
            color = NOTE_COLORS['high']
        gradient = QLinearGradient(x_pos, y_pos, x_pos, y_pos + height)
        gradient.setColorAt(0, color.lighter(130))
        gradient.setColorAt(0.5, color)
        gradient.setColorAt(1, color.darker(110))
        painter.setPen(QPen(color.darker(120), 0.5))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(
            int(x_pos), 
            int(y_pos + y_offset), 
            int(width), 
            int(height), 
            4, 4
        )
        original_note_name = pretty_midi.note_number_to_name(pitch)
        note_part_label = original_note_name[:-1]
        octave_str_label = original_note_name[-1:]
        corrected_label_name_note = original_note_name
        if octave_str_label.isdigit():
            octave_part_label = int(octave_str_label)
            corrected_label_name_note = f"{note_part_label}{octave_part_label + 1}"
        note_block_font = QFont("Segoe UI", 7)
        note_block_font.setBold(True)
        painter.setFont(note_block_font)
        painter.setPen(QColor(0, 0, 0))
        font_metrics = QFontMetrics(painter.font())
        text_width_needed = font_metrics.horizontalAdvance(corrected_label_name_note)
        text_height_needed = font_metrics.height()
        note_content_rect = QRectF(x_pos, y_pos + y_offset, width, height)
        if text_width_needed <= note_content_rect.width() - 4 and \
           text_height_needed <= note_content_rect.height() - 2:
            painter.drawText(note_content_rect, Qt.AlignCenter | Qt.AlignVCenter, corrected_label_name_note)

def draw_playhead(painter, playhead_position, time_scale, height):
    """Draw the playhead indicator"""
    if playhead_position > 0:
        playhead_x = playhead_position * time_scale + WHITE_KEY_WIDTH
        playhead_gradient = QLinearGradient(0, 0, 0, height)
        playhead_gradient.setColorAt(0, QColor(255, 150, 50, 200))
        playhead_gradient.setColorAt(1, QColor(255, 100, 20, 180))
        playhead_pen = QPen(playhead_gradient, 1.5)
        painter.setPen(playhead_pen)
        painter.drawLine(int(playhead_x), 0, int(playhead_x), height)
        triangle_size = 8
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
        painter.drawPolygon(points)