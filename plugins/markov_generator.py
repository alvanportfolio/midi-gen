# plugins/markov_generator.py
import random
import pretty_midi
import numpy as np
from collections import defaultdict
from plugin_api import PluginBase
from typing import List, Dict, Any, Tuple

class MarkovGenerator(PluginBase):
    """
    MIDI generator plugin that creates melodies using Markov chains
    Markov chains generate sequences where each note depends on the previous note(s)
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Markov Chain Generator"
        self.description = "Generates melodies using Markov chains"
        self.author = "MIDI Generator Project"
        self.version = "1.0"
        
        # Define parameters
        self.parameters = {
            "order": {
                "type": "int",
                "min": 1,
                "max": 3,
                "default": 1,
                "description": "Order of the Markov chain (how many previous notes to consider)"
            },
            "length": {
                "type": "int",
                "min": 8,
                "max": 64,
                "default": 16,
                "description": "Number of notes to generate"
            },
            "use_existing": {
                "type": "bool",
                "default": True,
                "description": "Use existing notes as training data (if available)"
            },
            "note_duration": {
                "type": "float",
                "min": 0.1,
                "max": 1.0,
                "default": 0.25,
                "description": "Duration of each note in beats"
            },
            "randomness": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.1,
                "description": "Adds randomness to the generation process"
            }
        }
        
        # Default training data in case no existing notes are provided
        self.default_training_data = [
            # C major scale
            60, 62, 64, 65, 67, 69, 71, 72,
            # C major chord arpeggios
            60, 64, 67, 72, 67, 64, 60,
            # G7 chord
            67, 71, 74, 77, 74, 71, 67,
            # A minor chord
            69, 72, 76, 72, 69
        ]
    
    def _build_transition_matrix(self, note_sequence, order):
        """
        Build a Markov transition matrix from a sequence of notes
        
        Args:
            note_sequence: List of MIDI note numbers
            order: Order of the Markov chain
            
        Returns:
            Dictionary mapping state tuples to possible next notes and their probabilities
        """
        transitions = defaultdict(lambda: defaultdict(int))
        
        if len(note_sequence) <= order:
            # Not enough data, fallback to simpler model
            order = 1
        
        # Count transitions
        for i in range(len(note_sequence) - order):
            state = tuple(note_sequence[i:i+order])
            next_note = note_sequence[i+order]
            transitions[state][next_note] += 1
        
        # Convert counts to probabilities
        transition_probs = {}
        for state, next_notes in transitions.items():
            total = sum(next_notes.values())
            transition_probs[state] = {note: count/total for note, count in next_notes.items()}
        
        return transition_probs
    
    def _choose_next_note(self, current_state, transition_probs, randomness):
        """
        Choose the next note based on the current state and transition probabilities
        
        Args:
            current_state: Tuple of current notes (state)
            transition_probs: Dictionary of transition probabilities
            randomness: How much randomness to add (0.0 to 1.0)
            
        Returns:
            Next note
        """
        if current_state not in transition_probs:
            # No data for this state, choose a random state
            if not transition_probs:
                return random.randint(60, 72)  # Fallback to C4-C5 range
            current_state = random.choice(list(transition_probs.keys()))
        
        next_note_probs = transition_probs[current_state]
        
        if not next_note_probs:
            # No transition data, return random note
            return random.randint(60, 72)
        
        if randomness > 0:
            # Add some randomness
            if random.random() < randomness:
                # Choose a completely random note
                return random.choice(list(next_note_probs.keys()))
        
        # Choose based on probabilities
        notes = list(next_note_probs.keys())
        probs = list(next_note_probs.values())
        return np.random.choice(notes, p=probs)
    
    def _extract_sequence(self, notes):
        """
        Extract a sequence of note numbers from pretty_midi.Note objects
        
        Args:
            notes: List of pretty_midi.Note objects
            
        Returns:
            List of MIDI note numbers sorted by start time
        """
        if not notes:
            return []
        
        # Sort notes by start time
        sorted_notes = sorted(notes, key=lambda n: n.start)
        return [note.pitch for note in sorted_notes]
    
    def generate(self, existing_notes=None, **kwargs):
        """
        Generate notes using a Markov chain
        
        Args:
            existing_notes: Optional list of existing notes to use as training data
            **kwargs: Additional parameters
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        # Extract parameters with defaults
        order = kwargs.get("order", 1)
        length = kwargs.get("length", 16)
        use_existing = kwargs.get("use_existing", True)
        note_duration = kwargs.get("note_duration", 0.25)
        randomness = kwargs.get("randomness", 0.1)
        
        # Get training data
        if existing_notes and use_existing:
            training_sequence = self._extract_sequence(existing_notes)
            if len(training_sequence) < order + 1:
                # Not enough data, use default + existing
                training_sequence = self.default_training_data + training_sequence
        else:
            training_sequence = self.default_training_data
        
        # Build transition matrix
        transition_probs = self._build_transition_matrix(training_sequence, order)
        
        # Generate new sequence
        new_sequence = []
        
        # Start with a random state from the training data
        if len(training_sequence) >= order:
            start_idx = random.randint(0, len(training_sequence) - order)
            current = tuple(training_sequence[start_idx:start_idx+order])
        else:
            # Fallback if training data is too short
            current = (60,) * order  # Start with middle C repeated
        
        new_sequence.extend(current)
        
        # Generate the rest of the sequence
        for _ in range(length - order):
            next_note = self._choose_next_note(current, transition_probs, randomness)
            new_sequence.append(next_note)
            
            # Update current state
            current = tuple(new_sequence[-order:])
        
        # Convert to pretty_midi.Note objects
        result = []
        tick_time = 0.0
        
        for note_num in new_sequence:
            midi_note = pretty_midi.Note(
                velocity=100,  # Medium velocity
                pitch=note_num,
                start=tick_time,
                end=tick_time + note_duration
            )
            result.append(midi_note)
            tick_time += note_duration
        
        return result