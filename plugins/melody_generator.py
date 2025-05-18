# plugins/melody_generator.py
import random
import pretty_midi
from plugin_api import PluginBase
from typing import List, Dict, Any

class MelodyGenerator(PluginBase):
    """
    MIDI generator plugin that creates emotional melodies
    Inspired by the FL Studio Melody.pyscript
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Emotional Melody Generator"
        self.description = "Generates emotional melodies based on scales and patterns"
        self.author = "MIDI Generator Project"
        self.version = "1.0"
        
        # Define parameters
        self.parameters = {
            "root_note": {
                "type": "list",
                "options": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
                "default": "C",
                "description": "Root note of the scale"
            },
            "octave": {
                "type": "int",
                "min": 2,
                "max": 7,
                "default": 4,
                "description": "Octave of the root note"
            },
            "scale": {
                "type": "list",
                "options": ["Major", "Minor", "Harmonic Minor", "Melodic Minor", "Dorian", 
                            "Phrygian", "Lydian", "Mixolydian", "Locrian", "Blues", "Japanese", "Arabic"],
                "default": "Major",
                "description": "Scale to use for the melody"
            },
            "total_bars": {
                "type": "int",
                "min": 1,
                "max": 10,
                "default": 4,
                "description": "Number of bars to generate"
            },
            "rhythm": {
                "type": "list",
                "options": ["Whole Notes", "Half Notes", "Quarter Notes", "Eighth Notes", 
                           "Emotional 1", "Emotional 2", "Emotional 3", "Flowing 1", "Flowing 2",
                           "Rhythmic 1", "Rhythmic 2", "Sparse", "Dense"],
                "default": "Emotional 1",
                "description": "Rhythm pattern to use"
            },
            "pattern": {
                "type": "list",
                "options": ["Rising", "Falling", "Wave Up", "Wave Down", "Mountain", "Valley",
                           "Emotional Rise", "Emotional Fall", "Arpeggios 1", "Arpeggios 2",
                           "Steps", "Skips", "Random Walk"],
                "default": "Emotional Rise",
                "description": "Melodic pattern to use"
            },
            "emotion": {
                "type": "list",
                "options": ["Happy", "Sad", "Calm", "Nostalgic", "Hopeful", "Melancholic", 
                           "Dramatic", "Reflective", "Tense", "Serene"],
                "default": "Happy",
                "description": "Emotional character of the melody"
            },
            "velocity": {
                "type": "float",
                "min": 0.5,
                "max": 1.0,
                "default": 0.8,
                "description": "Base velocity (volume) of notes"
            },
            "duration": {
                "type": "float",
                "min": 0.2,
                "max": 1.0,
                "default": 0.8,
                "description": "Base duration of notes"
            },
            "density": {
                "type": "float",
                "min": 0.1,
                "max": 1.0,
                "default": 1.0,
                "description": "Density of notes (probability of a note being played)"
            },
            "seed": {
                "type": "int",
                "min": 1,
                "max": 1000,
                "default": random.randint(1, 1000),
                "description": "Random seed for reproducible melodies"
            }
        }
        
        # Define scales (7-note scales)
        self.scales = {
            "Major":             [0, 2, 4, 5, 7, 9, 11],
            "Minor":             [0, 2, 3, 5, 7, 8, 10],
            "Harmonic Minor":    [0, 2, 3, 5, 7, 8, 11],
            "Melodic Minor":     [0, 2, 3, 5, 7, 9, 11],
            "Dorian":            [0, 2, 3, 5, 7, 9, 10],
            "Phrygian":          [0, 1, 3, 5, 7, 8, 10],
            "Lydian":            [0, 2, 4, 6, 7, 9, 11],
            "Mixolydian":        [0, 2, 4, 5, 7, 9, 10],
            "Locrian":           [0, 1, 3, 5, 6, 8, 10],
            "Blues":             [0, 3, 5, 6, 7, 10, 10],  # Repeated 10 to maintain 7 notes
            "Japanese":          [0, 2, 5, 7, 9, 9, 9],     # Repeated 9 to maintain 7 notes
            "Arabic":            [0, 1, 4, 5, 7, 8, 11],
        }
        
        # Rhythm patterns (16-step sequence where 1 = play note, 0 = rest)
        self.rhythms = {
            "Whole Notes":       [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] * 4,
            "Half Notes":        [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0] * 4,
            "Quarter Notes":     [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0] * 4,
            "Eighth Notes":      [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0] * 4,
            "Emotional 1":       [1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0] * 4,
            "Emotional 2":       [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0] * 4,
            "Emotional 3":       [1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0] * 4,
            "Flowing 1":         [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0] * 4,
            "Flowing 2":         [1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1] * 4,
            "Rhythmic 1":        [1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1] * 4,
            "Rhythmic 2":        [1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0] * 4,
            "Sparse":            [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0] * 4,
            "Dense":             [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1] * 4,
        }
        
        # Melodic patterns (relative scale degree movements)
        self.patterns = {
            "Rising":            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            "Falling":           [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            "Wave Up":           [0, 1, 2, 3, 4, 3, 2, 1, 2, 3, 4, 5, 6, 5, 4, 3],
            "Wave Down":         [7, 6, 5, 4, 3, 4, 5, 6, 5, 4, 3, 2, 1, 2, 3, 4],
            "Mountain":          [0, 1, 2, 3, 4, 5, 6, 7, 7, 6, 5, 4, 3, 2, 1, 0],
            "Valley":            [7, 6, 5, 4, 3, 2, 1, 0, 0, 1, 2, 3, 4, 5, 6, 7],
            "Emotional Rise":    [0, 0, 2, 2, 4, 4, 5, 5, 7, 7, 9, 9, 11, 11, 12, 12],
            "Emotional Fall":    [12, 12, 11, 11, 9, 9, 7, 7, 5, 5, 4, 4, 2, 2, 0, 0],
            "Arpeggios 1":       [0, 2, 4, 7, 4, 2, 0, 2, 4, 7, 9, 7, 4, 2, 0, 0],
            "Arpeggios 2":       [0, 4, 7, 12, 7, 4, 0, 2, 7, 11, 14, 11, 7, 2, 0, 0],
            "Steps":             [0, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7, 0, 0],
            "Skips":             [0, 2, 4, 0, 3, 5, 0, 4, 6, 0, 5, 7, 0, 6, 8, 0],
            "Random Walk":       [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Will be randomized
        }
        
        # Emotion-based contour patterns
        self.emotions = {
            "Happy":             [0, 2, 4, 3, 5, 7, 9, 7, 5, 4, 2, 4, 5, 7, 9, 7],
            "Sad":               [7, 5, 3, 2, 0, 2, 3, 1, 3, 2, 0, -1, 0, 2, 0, -3],
            "Calm":              [0, 2, 4, 2, 0, 2, 4, 5, 4, 2, 0, 2, 4, 2, 0, -1],
            "Nostalgic":         [7, 5, 4, 2, 0, -1, 0, 2, 0, -1, 0, 2, 4, 2, 0, -3],
            "Hopeful":           [0, 0, 2, 4, 5, 7, 7, 9, 7, 5, 4, 2, 4, 5, 4, 2],
            "Melancholic":       [4, 2, 0, -1, 0, 2, 0, -1, -3, -1, 0, 2, 0, -1, 0, -3],
            "Dramatic":          [0, 4, 7, 12, 11, 7, 4, 0, -1, -3, 0, 4, 7, 4, 0, -1],
            "Reflective":        [0, 2, 4, 7, 4, 2, 0, -1, 0, 2, 4, 2, 0, -1, -3, -1],
            "Tense":             [0, 1, 0, 3, 2, 1, 3, 2, 5, 4, 7, 6, 5, 4, 3, 2],
            "Serene":            [7, 5, 7, 4, 5, 2, 4, 0, 2, 4, 5, 7, 5, 4, 2, 0],
        }
    
    def _get_root_note_value(self, root_name, octave):
        """
        Convert root note name and octave to MIDI note number
        
        Args:
            root_name: Name of the root note (e.g., "C", "D#")
            octave: Octave number
            
        Returns:
            MIDI note number
        """
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        note_index = note_names.index(root_name)
        return (octave * 12) + note_index
    
    def _get_scale_notes(self, root_note, scale_name):
        """
        Get notes in a given scale
        
        Args:
            root_note: MIDI note number for the root note
            scale_name: Name of the scale
            
        Returns:
            List of MIDI note numbers in the scale
        """
        if scale_name not in self.scales:
            return []
            
        intervals = self.scales[scale_name]
        
        # Generate three octaves of notes
        scale_notes = []
        for i in range(3):  # Generate 3 octaves
            for interval in intervals:
                note = root_note + interval + (i * 12)
                if 0 <= note <= 127:  # Ensure note is in valid MIDI range
                    scale_notes.append(note)
        
        return scale_notes
    
    def _generate_random_walk(self, steps, range_limit=7):
        """
        Generate a random walk melodic pattern
        
        Args:
            steps: Number of steps in the pattern
            range_limit: Limit for range of the walk
            
        Returns:
            List of values forming the pattern
        """
        pattern = [0]
        for _ in range(steps - 1):
            # Generate steps that tend to move toward the center of the range
            current = pattern[-1]
            if abs(current) > range_limit:
                # Pull back toward center if we're getting too far out
                step = -1 if current > 0 else 1
            else:
                step = random.choice([-2, -1, -1, 0, 0, 1, 1, 2])
            pattern.append(current + step)
        return pattern
    
    def _normalize_pattern(self, pattern, octave_range):
        """
        Normalize pattern to fit within the given octave range
        
        Args:
            pattern: List of values to normalize
            octave_range: Range in octaves
            
        Returns:
            Normalized pattern
        """
        min_val = min(pattern)
        max_val = max(pattern)
        current_range = max_val - min_val
        
        # Scale to fit within octave_range
        target_range = octave_range * 7  # Approximate scale steps in octave_range octaves
        
        if current_range == 0:  # Avoid division by zero
            return [0] * len(pattern)
        
        result = []
        for val in pattern:
            normalized = (val - min_val) / current_range * target_range
            result.append(int(normalized))
        
        return result
    
    def _apply_emotion_contour(self, pattern, emotion_contour, intensity=1.0):
        """
        Apply emotion-based contour to a melodic pattern
        
        Args:
            pattern: Original pattern
            emotion_contour: Emotion contour to apply
            intensity: How strongly to apply the emotion
            
        Returns:
            Modified pattern
        """
        result = []
        for i in range(len(pattern)):
            emotion_influence = emotion_contour[i % len(emotion_contour)] * intensity
            result.append(pattern[i] + emotion_influence)
        return result
    
    def _create_seed_variation(self, seed_value):
        """
        Create a unique melody seed from the given seed value
        
        Args:
            seed_value: Random seed
            
        Returns:
            List of random variations
        """
        random.seed(seed_value)
        variation = []
        for _ in range(16):
            variation.append(random.randint(-2, 2))
        return variation
    
    def _humanize_note(self, note, position_var=0.05, vel_var=0.1, dur_var=0.1):
        """
        Add human-like variations to a note
        
        Args:
            note: Note to humanize
            position_var: Position variation amount
            vel_var: Velocity variation amount
            dur_var: Duration variation amount
            
        Returns:
            Humanized note
        """
        # Vary timing slightly
        if position_var > 0:
            note.start += random.uniform(-position_var, position_var)
            note.start = max(0, note.start)
        
        # Vary velocity
        if vel_var > 0:
            variation = random.uniform(1 - vel_var, 1 + vel_var)
            note.velocity = int(note.velocity * variation)
            note.velocity = max(30, min(127, note.velocity))
        
        # Vary duration
        if dur_var > 0:
            variation = random.uniform(1 - dur_var, 1 + dur_var)
            note_length = note.end - note.start
            note_length *= variation
            note.end = note.start + max(0.1, note_length)
        
        return note
    
    def generate(self, existing_notes=None, **kwargs):
        """
        Generate notes based on emotional melody parameters
        
        Args:
            existing_notes: Optional list of existing notes (not used in this generator)
            **kwargs: Parameters for melody generation
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        # Extract parameters with defaults
        root_name = kwargs.get("root_note", "C")
        octave = kwargs.get("octave", 4)
        scale_name = kwargs.get("scale", "Major")
        total_bars = kwargs.get("total_bars", 4)
        rhythm_name = kwargs.get("rhythm", "Emotional 1")
        pattern_name = kwargs.get("pattern", "Emotional Rise")
        emotion_name = kwargs.get("emotion", "Happy")
        velocity = kwargs.get("velocity", 0.8)
        duration = kwargs.get("duration", 0.8)
        density = kwargs.get("density", 1.0)
        seed = kwargs.get("seed", random.randint(1, 1000))
        
        # Set random seed for reproducibility
        random.seed(seed)
        
        # Calculate root note MIDI number
        root_note = self._get_root_note_value(root_name, octave)
        
        # Get scale notes
        scale_notes = self._get_scale_notes(root_note, scale_name)
        if not scale_notes:
            # Fallback to major scale if the specified scale is not found
            scale_notes = self._get_scale_notes(root_note, "Major")
        
        # Get rhythm pattern
        rhythm_pattern = self.rhythms.get(rhythm_name, self.rhythms["Emotional 1"])
        
        # Get melodic pattern
        melodic_pattern = self.patterns.get(pattern_name, self.patterns["Emotional Rise"])
        
        # For random walk pattern, generate it
        if pattern_name == "Random Walk":
            melodic_pattern = self._generate_random_walk(16, 12 // 2)
            # Extend to match rhythm length
            melodic_pattern = melodic_pattern * (len(rhythm_pattern) // len(melodic_pattern) + 1)
            melodic_pattern = melodic_pattern[:len(rhythm_pattern)]
        
        # Get emotion contour
        emotion_contour = self.emotions.get(emotion_name, self.emotions["Happy"])
        
        # Normalize the pattern
        melodic_pattern = self._normalize_pattern(melodic_pattern, 2.0)
        
        # Apply emotion to the pattern
        melodic_pattern = self._apply_emotion_contour(melodic_pattern, emotion_contour, 0.5)
        
        # Create seed variation
        seed_variation = self._create_seed_variation(seed)
        
        # Calculate notes per bar and total steps
        steps_per_bar = 16  # 16 sixteenth notes per bar (assuming 4/4 time)
        total_steps = total_bars * steps_per_bar
        
        # Make sure rhythm and melodic patterns are long enough
        while len(rhythm_pattern) < total_steps:
            rhythm_pattern = rhythm_pattern * 2
        
        while len(melodic_pattern) < total_steps:
            melodic_pattern = melodic_pattern * 2
        
        # Trim to exact length
        rhythm_pattern = rhythm_pattern[:total_steps]
        melodic_pattern = melodic_pattern[:total_steps]
        
        # Generate notes
        result = []
        sixteenth_duration = 60 / (120 * 4)  # Duration of a sixteenth note in seconds at 120 BPM
        
        for step in range(total_steps):
            # Check if this step should have a note based on rhythm pattern and density
            if rhythm_pattern[step] == 1 and random.random() <= density:
                # Calculate note timing
                start_time = step * sixteenth_duration
                
                # Get pattern value plus variation
                pattern_value = melodic_pattern[step % len(melodic_pattern)]
                variation_value = seed_variation[step % len(seed_variation)]
                
                # Calculate scale degree
                scale_degree = int(pattern_value + variation_value) % len(scale_notes)
                if scale_degree < 0:
                    scale_degree = 0
                elif scale_degree >= len(scale_notes):
                    scale_degree = len(scale_notes) - 1
                
                # Create the note
                note = pretty_midi.Note(
                    velocity=int(127 * velocity),
                    pitch=scale_notes[scale_degree],
                    start=start_time,
                    end=start_time + (sixteenth_duration * 4 * duration)  # Base duration on quarter note
                )
                
                # Humanize the note
                note = self._humanize_note(note, 0.05, 0.1, 0.1)
                
                result.append(note)
        
        return result