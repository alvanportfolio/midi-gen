"""
Helper utilities for AI-based MIDI generator plugins
Provides common functionality for API integration, file handling, and MIDI processing
"""

import os
import tempfile
import time
import threading
from typing import List, Dict, Any, Optional, Callable
import pretty_midi

class ApiConnectionManager:
    """Manages API connections with retry logic and timeout handling"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout
        self.last_error = None
    
    def call_with_retry(self, api_func: Callable, *args, **kwargs) -> Any:
        """
        Call an API function with retry logic
        
        Args:
            api_func: The API function to call
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the API call or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                print(f"API call attempt {attempt + 1}/{self.max_retries}")
                result = api_func(*args, **kwargs)
                return result
            except Exception as e:
                self.last_error = e
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
        
        print(f"All {self.max_retries} attempts failed. Last error: {self.last_error}")
        return None

class MidiFileHandler:
    """Handles MIDI file operations for plugin API integration"""
    
    @staticmethod
    def create_temp_midi_from_notes(notes: List[pretty_midi.Note], 
                                  tempo: float = 120.0,
                                  instrument_program: int = 0) -> str:
        """
        Create a temporary MIDI file from a list of notes
        
        Args:
            notes: List of pretty_midi.Note objects
            tempo: Tempo in BPM
            instrument_program: MIDI program number for instrument
            
        Returns:
            Path to temporary MIDI file
        """
        # Create pretty_midi object
        pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
        instrument = pretty_midi.Instrument(program=instrument_program)
        
        # Add notes to instrument
        for note in notes:
            instrument.notes.append(note)
        
        pm.instruments.append(instrument)
        
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.mid', prefix='plugin_input_')
        os.close(temp_fd)
        
        # Write MIDI file
        pm.write(temp_path)
        return temp_path
    
    @staticmethod
    def create_primer_midi(scale_root: int = 60, 
                          scale_type: str = "major",
                          length_seconds: float = 4.0) -> str:
        """
        Create a simple primer MIDI file when no existing notes are available
        
        Args:
            scale_root: Root note of the scale (MIDI number)
            scale_type: Type of scale ("major", "minor", "pentatonic")
            length_seconds: Length of primer in seconds
            
        Returns:
            Path to temporary MIDI file
        """
        # Define scale intervals
        scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "blues": [0, 3, 5, 6, 7, 10]
        }
        
        intervals = scales.get(scale_type, scales["major"])
        
        # Create simple ascending scale pattern
        notes = []
        note_duration = 0.5
        current_time = 0.0
        
        while current_time < length_seconds:
            for interval in intervals:
                if current_time >= length_seconds:
                    break
                
                pitch = scale_root + interval
                note = pretty_midi.Note(
                    velocity=80,
                    pitch=pitch,
                    start=current_time,
                    end=current_time + note_duration
                )
                notes.append(note)
                current_time += note_duration
        
        return MidiFileHandler.create_temp_midi_from_notes(notes)
    
    @staticmethod
    def parse_midi_file(midi_path: str) -> List[pretty_midi.Note]:
        """
        Parse a MIDI file and extract all notes
        
        Args:
            midi_path: Path to MIDI file
            
        Returns:
            List of pretty_midi.Note objects
        """
        try:
            pm = pretty_midi.PrettyMIDI(midi_path)
            notes = []
            
            # Extract notes from all non-drum instruments
            for instrument in pm.instruments:
                if not instrument.is_drum:
                    notes.extend(instrument.notes)
            
            # Sort by start time
            notes.sort(key=lambda n: n.start)
            return notes
            
        except Exception as e:
            print(f"Error parsing MIDI file: {e}")
            return []

class ProgressCallback:
    """Handles progress reporting for long-running API calls"""
    
    def __init__(self, callback_func: Optional[Callable[[str], None]] = None):
        self.callback_func = callback_func or self._default_callback
        self.is_cancelled = False
    
    def _default_callback(self, message: str):
        """Default progress callback that prints to console"""
        print(f"Progress: {message}")
    
    def update(self, message: str):
        """Update progress with a message"""
        if not self.is_cancelled:
            self.callback_func(message)
    
    def cancel(self):
        """Cancel the operation"""
        self.is_cancelled = True
        self.update("Operation cancelled")

class TempFileManager:
    """Context manager for handling temporary files"""
    
    def __init__(self):
        self.temp_files = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def add_temp_file(self, file_path: str):
        """Add a temporary file to be cleaned up"""
        self.temp_files.append(file_path)
    
    def cleanup(self):
        """Clean up all temporary files"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {file_path}: {e}")
        self.temp_files.clear()

def validate_api_parameters(params: Dict[str, Any], 
                          param_specs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate and normalize API parameters according to specifications
    
    Args:
        params: Dictionary of parameter values
        param_specs: Dictionary of parameter specifications
        
    Returns:
        Dictionary of validated parameters
    """
    validated = {}
    
    for param_name, spec in param_specs.items():
        value = params.get(param_name, spec.get("default"))
        
        if value is None:
            continue
        
        param_type = spec.get("type", "str")
        
        # Type conversion
        try:
            if param_type == "int":
                value = int(value)
            elif param_type == "float":
                value = float(value)
            elif param_type == "bool":
                value = bool(value)
            elif param_type == "str":
                value = str(value)
        except (ValueError, TypeError):
            print(f"Warning: Could not convert {param_name} to {param_type}, using default")
            value = spec.get("default")
        
        # Range validation
        if "min" in spec and value < spec["min"]:
            value = spec["min"]
        if "max" in spec and value > spec["max"]:
            value = spec["max"]
        
        # Options validation
        if "options" in spec and value not in spec["options"]:
            value = spec.get("default", spec["options"][0])
        
        validated[param_name] = value
    
    return validated

def create_fallback_melody(length_bars: int = 4, 
                          scale_root: int = 60,
                          scale_type: str = "major") -> List[pretty_midi.Note]:
    """
    Create a simple fallback melody for when API calls fail
    
    Args:
        length_bars: Number of bars to generate
        scale_root: Root note of the scale
        scale_type: Type of scale to use
        
    Returns:
        List of pretty_midi.Note objects
    """
    import random
    
    # Define scales
    scales = {
        "major": [0, 2, 4, 5, 7, 9, 11],
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "pentatonic": [0, 2, 4, 7, 9],
        "blues": [0, 3, 5, 6, 7, 10]
    }
    
    intervals = scales.get(scale_type, scales["major"])
    scale_notes = [scale_root + interval for interval in intervals]
    scale_notes.extend([scale_root + 12 + interval for interval in intervals])  # Add octave
    
    notes = []
    beats_per_bar = 4
    note_duration = 0.5  # Eighth notes
    current_time = 0.0
    
    total_notes = length_bars * beats_per_bar * 2  # 2 eighth notes per beat
    
    for i in range(total_notes):
        if random.random() > 0.15:  # 85% chance of playing a note
            pitch = random.choice(scale_notes)
            velocity = random.randint(60, 100)
            duration = note_duration * random.uniform(0.8, 1.0)
            
            note = pretty_midi.Note(
                velocity=velocity,
                pitch=pitch,
                start=current_time,
                end=current_time + duration
            )
            notes.append(note)
        
        current_time += note_duration
    
    return notes 