# plugins/motif_generator.py
import random
import pretty_midi
from plugin_api import PluginBase
from typing import List, Dict, Any

class MotifGenerator(PluginBase):
    """
    MIDI generator plugin that creates melodies based on motifs
    A motif is a short musical idea that gets developed through repetition and variation
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Motif Generator"
        self.description = "Generates melodies based on musical motifs"
        self.author = "MIDI Generator Project"
        self.version = "1.0"
        
        # Define parameters
        self.parameters = {
            "motif_length": {
                "type": "int",
                "min": 2,
                "max": 8,
                "default": 4,
                "description": "Length of the motif (in notes)"
            },
            "num_variations": {
                "type": "int",
                "min": 1,
                "max": 8,
                "default": 4,
                "description": "Number of variations to create"
            },
            "variation_strength": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "How much to vary the motif (0.0 = exact copies, 1.0 = completely different)"
            },
            "scale": {
                "type": "list",
                "options": ["major", "minor", "pentatonic", "blues", "chromatic"],
                "default": "major",
                "description": "Scale to use for the melody"
            },
            "root_note": {
                "type": "int",
                "min": 48,  # C3
                "max": 72,  # C5
                "default": 60,  # C4
                "description": "Root note of the scale"
            },
            "note_duration": {
                "type": "float",
                "min": 0.1,
                "max": 1.0,
                "default": 0.25,
                "description": "Duration of each note in beats"
            }
        }
    
    def _get_scale_notes(self, root_note, scale_name):
        """
        Get notes in a given scale
        
        Args:
            root_note: MIDI note number for the root note
            scale_name: Name of the scale
            
        Returns:
            List of MIDI note numbers in the scale
        """
        # Define scale intervals (semitones from root)
        scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "blues": [0, 3, 5, 6, 7, 10],
            "chromatic": list(range(12))
        }
        
        intervals = scales.get(scale_name, scales["major"])
        
        # Generate two octaves of notes
        scale_notes = []
        for octave in range(2):
            for interval in intervals:
                note = root_note + interval + (octave * 12)
                if 0 <= note <= 127:
                    scale_notes.append(note)
        
        return scale_notes
    
    def _create_motif(self, scale_notes, length):
        """
        Create a motif from scale notes
        
        Args:
            scale_notes: List of MIDI note numbers in the scale
            length: Length of the motif in notes
            
        Returns:
            List of MIDI note numbers forming the motif
        """
        return [random.choice(scale_notes) for _ in range(length)]
    
    def _create_variation(self, motif, scale_notes, strength):
        """
        Create a variation of a motif
        
        Args:
            motif: Original motif (list of MIDI note numbers)
            scale_notes: List of scale notes to choose from
            strength: How much to vary the motif (0.0 to 1.0)
            
        Returns:
            List of MIDI note numbers forming the variation
        """
        variation = []
        
        for note in motif:
            if random.random() < strength:
                # Change this note
                if random.random() < 0.7:
                    # Use a neighbor note in the scale
                    idx = scale_notes.index(note) if note in scale_notes else 0
                    idx = (idx + random.choice([-1, 1])) % len(scale_notes)
                    variation.append(scale_notes[idx])
                else:
                    # Use a random note from the scale
                    variation.append(random.choice(scale_notes))
            else:
                # Keep the original note
                variation.append(note)
        
        # Apply additional transformations with low probability
        if random.random() < 0.3:
            # Reverse the variation
            if random.random() < 0.5:
                variation = variation[::-1]
            # Transpose the variation
            elif random.random() < 0.5:
                transpose = random.choice([-12, -7, -5, 5, 7, 12])
                variation = [n + transpose for n in variation if 0 <= n + transpose <= 127]
        
        return variation
    
    def generate(self, existing_notes=None, **kwargs):
        """
        Generate notes based on motifs
        
        Args:
            existing_notes: Optional list of existing notes
            **kwargs: Additional parameters
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        # Extract parameters with defaults
        motif_length = kwargs.get("motif_length", 4)
        num_variations = kwargs.get("num_variations", 4)
        variation_strength = kwargs.get("variation_strength", 0.5)
        scale_name = kwargs.get("scale", "major")
        root_note = kwargs.get("root_note", 60)
        note_duration = kwargs.get("note_duration", 0.25)
        
        # Get scale notes
        scale_notes = self._get_scale_notes(root_note, scale_name)
        
        # Create initial motif
        motif = self._create_motif(scale_notes, motif_length)
        
        # Create variations
        all_notes = motif.copy()
        for _ in range(num_variations):
            variation = self._create_variation(motif, scale_notes, variation_strength)
            all_notes.extend(variation)
        
        # Convert to pretty_midi.Note objects
        result = []
        tick_time = 0.0
        
        for note_num in all_notes:
            midi_note = pretty_midi.Note(
                velocity=100,  # Medium velocity
                pitch=note_num,
                start=tick_time,
                end=tick_time + note_duration
            )
            result.append(midi_note)
            tick_time += note_duration
        
        return result