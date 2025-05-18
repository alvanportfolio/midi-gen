# export_utils.py
import os
import pretty_midi
from typing import List

def export_to_midi(notes: List[pretty_midi.Note], filename: str, tempo: float = 120.0):
    """
    Export notes to a MIDI file
    
    Args:
        notes: List of pretty_midi.Note objects
        filename: Path to save the MIDI file
        tempo: Tempo in BPM
    """
    # Create a PrettyMIDI object
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # Create an instrument
    instrument = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano
    
    # Add the notes to the instrument
    for note in notes:
        instrument.notes.append(note)
    
    # Add the instrument to the PrettyMIDI object
    midi.instruments.append(instrument)
    
    # Write the MIDI file
    midi.write(filename)
    
    return os.path.abspath(filename)