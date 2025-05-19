# plugins/your_partner.py
import random
import pretty_midi
import numpy as np
from plugin_api import PluginBase
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
import copy
import math
import re
import time  # Add time module import

class YourPartner(PluginBase):
    """
    A musical partner that creates call and response melodic phrases in user-specified bars.
    Generates interactive melodies that form a musical dialogue between bars.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Your Partner"
        self.description = "Creates call and response melodies in user-specified bars"
        self.author = "MIDI Generator Project"
        self.version = "1.0"
        
        # Define parameters
        self.parameters = {
            "bars": {
                "type": "str",
                "default": "1,3,5,7",
                "description": "Bar numbers to generate melody in (comma-separated)"
            },
            "scale": {
                "type": "list",
                "options": ["Major", "Minor", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Locrian"],
                "default": "Major",
                "description": "Scale to use for the melody"
            },
            "root_note": {
                "type": "list",
                "options": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
                "default": "C",
                "description": "Root note of the scale"
            },
            "response_similarity": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.6,
                "description": "How similar responses should be to calls (0=very different, 1=very similar)"
            },
            "phrase_complexity": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5,
                "description": "Complexity of the melodic phrases (0=simple, 1=complex)"
            },
            "note_density": {
                "type": "float",
                "min": 0.2,
                "max": 2.0,
                "default": 1.0,
                "description": "Density of notes in each phrase"
            },
            "expressive_rhythm": {
                "type": "bool",
                "default": True,
                "description": "Use more expressive rhythmic patterns"
            },
            "maintain_contour": {
                "type": "bool",
                "default": True,
                "description": "Responses maintain similar contour to calls"
            },
            "response_technique": {
                "type": "list",
                "options": [
                    "Mirroring", 
                    "Continuation", 
                    "Inversion",
                    "Rhythmic Echo",
                    "Question-Answer",
                    "Intelligent"
                ],
                "default": "Intelligent",
                "description": "Technique for response generation"
            },
            "register": {
                "type": "list",
                "options": ["Low", "Medium", "High", "Full Range"],
                "default": "Medium",
                "description": "Pitch register for the melody"
            },
            "seed": {
                "type": "int",
                "min": 0,
                "max": 10000,
                "default": 0,
                "description": "Random seed (0 = different each time)"
            }
        }
        
        # Initialize scales
        self.scales = {
            "Major": [0, 2, 4, 5, 7, 9, 11],
            "Minor": [0, 2, 3, 5, 7, 8, 10],
            "Dorian": [0, 2, 3, 5, 7, 9, 10],
            "Phrygian": [0, 1, 3, 5, 7, 8, 10],
            "Lydian": [0, 2, 4, 6, 7, 9, 11],
            "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
            "Locrian": [0, 1, 3, 5, 6, 8, 10]
        }
        
        # Registry of typical phrase shapes
        self.phrase_shapes = {
            "rising": [0, 1, 2, 3, 4, 5, 6, 7],
            "falling": [7, 6, 5, 4, 3, 2, 1, 0],
            "arch": [0, 2, 4, 6, 7, 6, 4, 2, 0],
            "valley": [7, 5, 3, 1, 0, 1, 3, 5, 7],
            "wave": [0, 2, 4, 2, 0, 2, 4, 2, 0],
            "zigzag": [0, 3, 1, 4, 2, 5, 3, 6, 4, 7],
            "plateau": [0, 3, 3, 3, 5, 5, 5, 7],
            "question": [0, 2, 4, 7, 4, 5],  # Rising at the end
            "answer": [5, 4, 2, 0]  # Falling at the end
        }
        
        # Common rhythmic patterns (in proportions of bar)
        self.rhythm_patterns = {
            "even_quarters": [0.0, 0.25, 0.5, 0.75],
            "even_eighths": [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875],
            "dotted": [0.0, 0.375, 0.5, 0.875],
            "syncopated": [0.0, 0.25, 0.375, 0.625, 0.75, 0.875],
            "triplet": [0.0, 0.333, 0.667],
            "swing": [0.0, 0.333, 0.5, 0.833],
            "call_pattern": [0.0, 0.25, 0.375, 0.5],
            "response_pattern": [0.5, 0.625, 0.75, 1.0],
            "anticipation": [0.95, 0.0, 0.25, 0.5, 0.75],  # Note slightly before the bar
            "legato": [0.0, 0.4, 0.8]  # Longer notes
        }
        
        # Range of octaves for different registers
        self.registers = {
            "Low": (2, 3),
            "Medium": (3, 5),
            "High": (5, 6),
            "Full Range": (2, 6)
        }
        
        # Note utilities
        self.NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.NOTE_ALIASES = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        
        # Initialize note index mapping
        self.NOTE_INDEX_MAPPING = {note: i for i, note in enumerate(self.NOTE_NAMES)}
        self.NOTE_INDEX_MAPPING.update({alias: self.NOTE_INDEX_MAPPING[note] for alias, note in self.NOTE_ALIASES.items()})
    
    def _parse_bar_list(self, bar_string: str) -> List[int]:
        """Parse comma-separated bar numbers, handling various formats"""
        if not bar_string.strip():
            return [1, 3, 5, 7]  # Default
        
        bars = []
        
        # Handle various formats
        parts = re.split(r'[,;\s]+', bar_string.strip())
        
        for part in parts:
            try:
                bar = int(part)
                if bar > 0:  # Bars must be positive
                    bars.append(bar)
            except ValueError:
                # Check for range like "1-4"
                if '-' in part:
                    try:
                        start, end = map(int, part.split('-'))
                        if start > 0 and end >= start:
                            bars.extend(range(start, end + 1))
                    except ValueError:
                        pass
        
        return sorted(list(set(bars)))  # Remove duplicates and sort
    
    def _get_root_value(self, root_note: str) -> int:
        """Convert root note name to MIDI note value"""
        root_index = self.NOTE_INDEX_MAPPING.get(root_note, 0)
        return root_index
    
    def _get_scale_notes(self, root_note: str, scale_name: str, register: str) -> List[int]:
        """Get all notes in the scale within the specified register"""
        root_index = self._get_root_value(root_note)
        intervals = self.scales.get(scale_name, self.scales["Major"])
        
        # Get octave range for the selected register
        octave_min, octave_max = self.registers.get(register, (3, 5))
        
        scale_notes = []
        for octave in range(octave_min, octave_max + 1):
            for interval in intervals:
                note = (octave * 12) + root_index + interval
                if 0 <= note <= 127:  # Valid MIDI note range
                    scale_notes.append(note)
        
        return scale_notes
    
    def _get_bar_duration(self) -> float:
        """Return bar duration in beats (assuming 4/4 time)"""
        return 4.0  # 4 beats per bar
    
    def _calculate_note_position(self, bar_number: int, position_in_bar: float) -> float:
        """Calculate the absolute position (in beats) for a note"""
        bar_duration = self._get_bar_duration()
        return (bar_number - 1) * bar_duration + position_in_bar * bar_duration
    
    def _create_call_phrase(self, 
                           bar_number: int, 
                           scale_notes: List[int], 
                           complexity: float, 
                           note_density: float,
                           expressive_rhythm: bool) -> List[pretty_midi.Note]:
        """Create a 'call' melodic phrase in the specified bar"""
        result = []
        bar_duration = self._get_bar_duration()
        
        # First, determine the shape/contour of the phrase
        shape_keys = list(self.phrase_shapes.keys())
        if complexity < 0.3:
            # Simple shapes for low complexity
            shape_options = ["rising", "falling", "wave"]
        elif complexity < 0.7:
            # Medium complexity
            shape_options = ["arch", "valley", "zigzag", "question"]
        else:
            # High complexity
            shape_options = ["zigzag", "plateau", "question", "wave"]
        
        shape_name = random.choice(shape_options)
        shape = self.phrase_shapes[shape_name]
        
        # Determine rhythm pattern
        if expressive_rhythm:
            if complexity < 0.4:
                rhythm_options = ["even_quarters", "even_eighths", "triplet"]
            elif complexity < 0.8:
                rhythm_options = ["dotted", "syncopated", "swing", "call_pattern"]
            else:
                rhythm_options = ["syncopated", "anticipation", "call_pattern"]
        else:
            # Simpler rhythms when expressive_rhythm is off
            rhythm_options = ["even_quarters", "even_eighths", "legato"]
        
        rhythm_name = random.choice(rhythm_options)
        rhythm = self.rhythm_patterns[rhythm_name]
        
        # Adjust note count based on density
        base_note_count = len(rhythm)
        note_count = max(2, min(12, int(base_note_count * note_density)))
        
        # If density requires more notes than rhythm pattern, duplicate and modify
        if note_count > len(rhythm):
            # Create subdivisions or duplications of the rhythm
            extended_rhythm = []
            for pos in rhythm:
                extended_rhythm.append(pos)
                # Add subdivisions if needed
                if random.random() < 0.5:
                    subdivision = pos + 0.125  # eighth note later
                    if subdivision < 1.0:  # keep within bar
                        extended_rhythm.append(subdivision)
            
            # Sort and trim to get desired note count
            rhythm = sorted(extended_rhythm)[:note_count]
        elif note_count < len(rhythm):
            # Reduce number of notes by picking a subset
            rhythm = random.sample(rhythm, note_count)
            rhythm.sort()
        
        # Choose a starting pitch based on the middle of our scale
        if len(scale_notes) > 0:
            center_idx = len(scale_notes) // 2
            center_pitch = scale_notes[center_idx]
        else:
            center_pitch = 60  # Middle C fallback
        
        # Generate notes following the shape and rhythm
        for i, position in enumerate(rhythm):
            # Map position in sequence to position in shape
            shape_idx = int((i / len(rhythm)) * len(shape))
            shape_idx = min(shape_idx, len(shape) - 1)
            
            # Calculate pitch based on shape and scale
            shape_value = shape[shape_idx]
            
            # Scale the shape value to map to scale notes
            scale_idx = center_idx + shape_value - len(shape) // 2
            scale_idx = max(0, min(scale_idx, len(scale_notes) - 1))
            
            pitch = scale_notes[scale_idx]
            
            # Add some variation based on complexity
            if random.random() < complexity * 0.5:
                pitch_offset = random.choice([-2, -1, 1, 2])
                new_pitch = pitch + pitch_offset
                # Ensure pitch is in scale
                if new_pitch in scale_notes:
                    pitch = new_pitch
            
            # Calculate timing
            start_time = self._calculate_note_position(bar_number, position)
            
            # Determine note duration based on rhythm and next note
            if i < len(rhythm) - 1:
                next_pos = rhythm[i + 1]
                # Duration is until next note or slightly less
                duration_ratio = random.uniform(0.8, 0.95) if expressive_rhythm else 0.9
                duration = (next_pos - position) * bar_duration * duration_ratio
            else:
                # Last note - extend to end of bar or slightly less
                duration_ratio = random.uniform(0.7, 1.0) if expressive_rhythm else 0.9
                duration = (1.0 - position) * bar_duration * duration_ratio
            
            # Create note
            note = pretty_midi.Note(
                velocity=random.randint(80, 100),
                pitch=pitch,
                start=start_time,
                end=start_time + duration
            )
            
            result.append(note)
        
        return result
    
    def _create_response_phrase(self, 
                              call_notes: List[pretty_midi.Note], 
                              response_bar: int,
                              scale_notes: List[int],
                              similarity: float,
                              technique: str,
                              maintain_contour: bool) -> List[pretty_midi.Note]:
        """Create a 'response' phrase based on the call phrase"""
        if not call_notes:
            return []
        
        # Choose technique if set to "Intelligent"
        if technique == "Intelligent":
            techniques = ["Mirroring", "Continuation", "Inversion", "Rhythmic Echo", "Question-Answer"]
            technique = random.choice(techniques)
        
        bar_duration = self._get_bar_duration()
        result = []
        
        # Sort call notes by start time
        sorted_call = sorted(call_notes, key=lambda n: n.start)
        
        # Extract rhythm and pitch patterns from call
        call_bar = int(sorted_call[0].start // bar_duration) + 1
        call_rhythms = []
        call_pitches = []
        for note in sorted_call:
            # Get relative position within the call bar
            pos_in_bar = (note.start - (call_bar - 1) * bar_duration) / bar_duration
            call_rhythms.append(pos_in_bar)
            call_pitches.append(note.pitch)
        
        # Find the pitch range and center of the call
        if call_pitches:
            min_pitch = min(call_pitches)
            max_pitch = max(call_pitches)
            center_pitch = sum(call_pitches) // len(call_pitches)
        else:
            # Fallback
            min_pitch = 60
            max_pitch = 72
            center_pitch = 66
        
        # Analyze the call contour
        call_contour = []
        for i in range(1, len(call_pitches)):
            diff = call_pitches[i] - call_pitches[i-1]
            if diff > 0:
                call_contour.append(1)  # Up
            elif diff < 0:
                call_contour.append(-1)  # Down
            else:
                call_contour.append(0)  # Same
        
        # Create response based on selected technique
        if technique == "Mirroring":
            # Create a response that mirrors the call
            response_rhythms = call_rhythms.copy()
            response_pitches = []
            
            for pitch in call_pitches:
                # Mirror around the center pitch
                mirror_pitch = center_pitch - (pitch - center_pitch)
                
                # Ensure the mirror pitch is in scale
                if mirror_pitch not in scale_notes:
                    # Find closest scale note
                    closest = min(scale_notes, key=lambda p: abs(p - mirror_pitch))
                    mirror_pitch = closest
                
                response_pitches.append(mirror_pitch)
            
            # Add variation based on similarity parameter
            if similarity < 1.0:
                for i in range(len(response_rhythms)):
                    if random.random() > similarity:
                        # Vary rhythm slightly
                        offset = random.uniform(-0.1, 0.1)
                        response_rhythms[i] = max(0, min(1, response_rhythms[i] + offset))
                
                for i in range(len(response_pitches)):
                    if random.random() > similarity:
                        # Vary pitch within scale
                        scale_idx = scale_notes.index(response_pitches[i])
                        offset = random.choice([-2, -1, 1, 2])
                        new_idx = max(0, min(len(scale_notes) - 1, scale_idx + offset))
                        response_pitches[i] = scale_notes[new_idx]
        
        elif technique == "Continuation":
            # Create a response that continues the call's melodic idea
            # Take the last few notes of call as starting point
            start_count = min(2, len(call_rhythms))
            response_rhythms = [0.0]  # Start at beginning of bar
            response_pitches = [call_pitches[-1]]  # Continue from last pitch
            
            # Continue the established pattern
            for i in range(len(call_rhythms) - 1):
                # Continue rhythm pattern similar to call
                if i < len(call_rhythms) - 1:
                    interval = call_rhythms[i+1] - call_rhythms[i]
                else:
                    interval = 0.25  # Default to quarter note
                
                next_pos = response_rhythms[-1] + interval
                if next_pos < 1.0:  # Keep within bar
                    response_rhythms.append(next_pos)
                
                # Continue pitch pattern
                if i < len(call_contour):
                    direction = call_contour[i]
                else:
                    direction = random.choice([-1, 0, 1])
                
                # Find next pitch in scale
                curr_pitch = response_pitches[-1]
                curr_idx = scale_notes.index(curr_pitch) if curr_pitch in scale_notes else 0
                
                # Move in contour direction
                new_idx = curr_idx + direction
                new_idx = max(0, min(len(scale_notes) - 1, new_idx))
                response_pitches.append(scale_notes[new_idx])
            
            # Add variation based on similarity parameter
            if similarity < 0.8:
                for i in range(len(response_rhythms)):
                    if random.random() > similarity:
                        # More significant rhythm changes for continuation
                        offset = random.uniform(-0.15, 0.15)
                        response_rhythms[i] = max(0, min(1, response_rhythms[i] + offset))
        
        elif technique == "Inversion":
            # Invert the contour of the call
            response_rhythms = call_rhythms.copy()
            response_pitches = [call_pitches[0]]  # Start with same note
            
            # Invert the contour
            for i, direction in enumerate(call_contour):
                curr_pitch = response_pitches[-1]
                curr_idx = scale_notes.index(curr_pitch) if curr_pitch in scale_notes else 0
                
                # Move in opposite direction
                new_idx = curr_idx - direction
                new_idx = max(0, min(len(scale_notes) - 1, new_idx))
                response_pitches.append(scale_notes[new_idx])
            
            # Add variation based on similarity
            if similarity < 0.9:
                # More variation allows for more creative inversions
                random_inversions = random.randint(1, max(1, int((1-similarity) * len(response_pitches))))
                for _ in range(random_inversions):
                    idx = random.randint(0, len(response_pitches) - 1)
                    # Move to neighboring scale note
                    curr_idx = scale_notes.index(response_pitches[idx]) if response_pitches[idx] in scale_notes else 0
                    new_idx = curr_idx + random.choice([-1, 1])
                    new_idx = max(0, min(len(scale_notes) - 1, new_idx))
                    response_pitches[idx] = scale_notes[new_idx]
        
        elif technique == "Rhythmic Echo":
            # Keep similar rhythm, change pitches
            response_rhythms = call_rhythms.copy()
            
            # Generate new pitches in same scale
            response_pitches = []
            pitch_range = max_pitch - min_pitch
            
            for _ in range(len(call_pitches)):
                # Choose a pitch within same range but different
                if maintain_contour and call_contour:
                    # Follow similar contour if enabled
                    if response_pitches:
                        last_idx = scale_notes.index(response_pitches[-1]) if response_pitches[-1] in scale_notes else 0
                        contour_idx = min(len(call_contour) - 1, len(response_pitches) - 1)
                        if contour_idx >= 0:
                            direction = call_contour[contour_idx]
                            new_idx = last_idx + direction
                            new_idx = max(0, min(len(scale_notes) - 1, new_idx))
                            pitch = scale_notes[new_idx]
                        else:
                            # Start with random pitch in range
                            scale_min_idx = max(0, scale_notes.index(min(scale_notes, key=lambda p: abs(p - min_pitch))))
                            scale_max_idx = min(len(scale_notes) - 1, scale_notes.index(min(scale_notes, key=lambda p: abs(p - max_pitch))))
                            pitch_idx = random.randint(scale_min_idx, scale_max_idx)
                            pitch = scale_notes[pitch_idx]
                    else:
                        # Start with random pitch in range
                        scale_min_idx = max(0, scale_notes.index(min(scale_notes, key=lambda p: abs(p - min_pitch))))
                        scale_max_idx = min(len(scale_notes) - 1, scale_notes.index(min(scale_notes, key=lambda p: abs(p - max_pitch))))
                        pitch_idx = random.randint(scale_min_idx, scale_max_idx)
                        pitch = scale_notes[pitch_idx]
                else:
                    # Random but within same range
                    scale_min_idx = max(0, scale_notes.index(min(scale_notes, key=lambda p: abs(p - min_pitch))))
                    scale_max_idx = min(len(scale_notes) - 1, scale_notes.index(min(scale_notes, key=lambda p: abs(p - max_pitch))))
                    pitch_idx = random.randint(scale_min_idx, scale_max_idx)
                    pitch = scale_notes[pitch_idx]
                
                response_pitches.append(pitch)
            
            # Add some rhythm variation based on similarity
            if similarity < 0.7:
                for i in range(len(response_rhythms)):
                    if random.random() > similarity:
                        # Shift rhythmic timing slightly
                        jitter = random.uniform(-0.08, 0.08)
                        response_rhythms[i] = max(0, min(0.99, response_rhythms[i] + jitter))
        
        elif technique == "Question-Answer":
            # Treat call as question, response as answer
            # Questions often end on a higher note or unresolved, answers resolve
            
            # Start with similar rhythm but shaped like an answer
            response_rhythms = []
            
            # Use fewer notes for the answer typically
            note_count = max(2, len(call_rhythms) - random.randint(0, 2))
            
            # Distribute notes across the bar with focus on resolution
            for i in range(note_count):
                pos = i / (note_count - 1) if note_count > 1 else 0.5
                # Weight toward beginning or end based on position
                if i < note_count // 2:
                    pos = pos * 0.6  # Front-loaded for beginning of answer
                else:
                    pos = 0.4 + (pos * 0.6)  # Back-loaded for resolution
                
                response_rhythms.append(pos)
            
            # Create pitches that form an answer
            response_pitches = []
            
            # Start in similar range
            start_pitch = call_pitches[0]
            if start_pitch not in scale_notes:
                start_pitch = min(scale_notes, key=lambda p: abs(p - start_pitch))
            response_pitches.append(start_pitch)
            
            # Find tonic (first note of the scale) for resolution
            tonic = scale_notes[0]
            
            # Create descending shape toward resolution for answer
            pitch_indexes = []
            for i in range(1, note_count):
                # Gradual descent toward tonic
                progress = i / (note_count - 1) if note_count > 1 else 1.0
                
                # Find current pitch index in scale
                curr_pitch = response_pitches[-1]
                curr_idx = scale_notes.index(curr_pitch)
                
                # Calculate target index (toward tonic)
                tonic_idx = scale_notes.index(tonic)
                
                # Move toward tonic
                step = int((tonic_idx - curr_idx) * progress)
                new_idx = curr_idx + step
                
                # Add some variation
                if random.random() > similarity:
                    new_idx += random.choice([-1, 0, 1])
                
                new_idx = max(0, min(len(scale_notes) - 1, new_idx))
                pitch_indexes.append(new_idx)
            
            # Convert indexes to pitches
            for idx in pitch_indexes:
                response_pitches.append(scale_notes[idx])
        
        # Create notes from the generated response
        for i in range(min(len(response_rhythms), len(response_pitches))):
            pos = response_rhythms[i]
            pitch = response_pitches[i]
            
            # Calculate timing
            start_time = self._calculate_note_position(response_bar, pos)
            
            # Determine note duration based on rhythm and next note
            if i < len(response_rhythms) - 1:
                next_pos = response_rhythms[i + 1]
                # Duration is until next note or slightly less
                duration_ratio = random.uniform(0.8, 0.95)
                duration = (next_pos - pos) * bar_duration * duration_ratio
            else:
                # Last note - extend to end of bar or slightly less
                duration_ratio = random.uniform(0.7, 1.0)
                duration = (1.0 - pos) * bar_duration * duration_ratio
            
            # Create note
            note = pretty_midi.Note(
                velocity=random.randint(75, 100),
                pitch=pitch,
                start=start_time,
                end=start_time + duration
            )
            
            result.append(note)
        
        return result
    
    def generate(self, existing_notes=None, **kwargs):
        """
        Generate call and response melodies in user-specified bars
        
        Args:
            existing_notes: Optional list of existing notes (not used in this plugin)
            **kwargs: Additional parameters
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        # Extract parameters
        bar_string = kwargs.get("bars", "1,3,5,7")
        scale_name = kwargs.get("scale", "Major")
        root_note = kwargs.get("root_note", "C")
        response_similarity = kwargs.get("response_similarity", 0.6)
        phrase_complexity = kwargs.get("phrase_complexity", 0.5)
        note_density = kwargs.get("note_density", 1.0)
        expressive_rhythm = kwargs.get("expressive_rhythm", True)
        maintain_contour = kwargs.get("maintain_contour", True)
        response_technique = kwargs.get("response_technique", "Intelligent")
        register = kwargs.get("register", "Medium")
        seed_value = kwargs.get("seed", 0)
        
        # Set random seed (0 means use system time for different results each time)
        if seed_value == 0:
            seed_value = int(time.time())
        random.seed(seed_value)
        np.random.seed(seed_value)
        
        # Parse bar list
        bars = self._parse_bar_list(bar_string)
        if not bars:
            # If no valid bars specified, use defaults
            bars = [1, 3, 5, 7]
        
        # Get scale notes
        scale_notes = self._get_scale_notes(root_note, scale_name, register)
        
        # Generate melodies in pairs (call/response)
        result = []
        
        for i in range(0, len(bars), 2):
            call_bar = bars[i]
            
            # Create call phrase
            call_notes = self._create_call_phrase(
                bar_number=call_bar,
                scale_notes=scale_notes,
                complexity=phrase_complexity,
                note_density=note_density,
                expressive_rhythm=expressive_rhythm
            )
            
            result.extend(call_notes)
            
            # If there's a next bar, create response
            if i + 1 < len(bars):
                response_bar = bars[i + 1]
                
                response_notes = self._create_response_phrase(
                    call_notes=call_notes,
                    response_bar=response_bar,
                    scale_notes=scale_notes,
                    similarity=response_similarity,
                    technique=response_technique,
                    maintain_contour=maintain_contour
                )
                
                result.extend(response_notes)
        
        return result