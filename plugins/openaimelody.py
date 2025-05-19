# plugins/openai_melody_generator.py
import random
import pretty_midi
import numpy as np
from collections import defaultdict
from plugin_api import PluginBase
from typing import List, Dict, Any, Tuple, Optional, Union
import os
import json
import re
import time
import threading
from dataclasses import dataclass
import requests

class OpenAIMelodyGenerator(PluginBase):
    """
    MIDI generator plugin that creates melodies using OpenAI APIs
    Uses OpenAI language models to interpret natural language instructions and generate music
    """
    
    def __init__(self):
        super().__init__()
        self.name = "OpenAI Melody Generator"
        self.description = "Generates melodies using OpenAI (or compatible) language models"
        self.author = "MIDI Generator Project"
        self.version = "1.0"
        
        # Define parameters
        self.parameters = {
            "prompt": {
                "type": "str",
                "default": "Create a happy 4-bar melody in C major with quarter notes.",
                "description": "Describe the melody you want to generate"
            },
            "openai_api_key": {
                "type": "str",
                "default": "",
                "description": "Your OpenAI API key"
            },
            "openai_base_url": {
                "type": "str",
                "default": "https://api.openai.com/v1/",
                "description": "Base URL for OpenAI API (customize for compatible APIs)"
            },
            "openai_model": {
                "type": "str",
                "default": "gpt-4-turbo",
                "description": "OpenAI model ID (editable for custom models)"
            },
            "temperature": {
                "type": "float",
                "min": 0.0,
                "max": 2.0,
                "default": 0.7,
                "description": "Temperature for generation (higher = more creative)"
            },
            "max_tokens": {
                "type": "int",
                "min": 256,
                "max": 8192,
                "default": 4096,
                "description": "Maximum tokens in AI response"
            },
            "melody_length": {
                "type": "list",
                "options": ["1 bar", "2 bars", "4 bars", "8 bars", "16 bars"],
                "default": "4 bars",
                "description": "Length of the generated melody"
            },
            "note_resolution": {
                "type": "list",
                "options": ["Whole", "Half", "Quarter", "Eighth", "Sixteenth"],
                "default": "Eighth",
                "description": "Smallest note duration to use"
            },
            "root_note": {
                "type": "list",
                "options": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
                "default": "C",
                "description": "Root note of the melody"
            },
            "octave": {
                "type": "int",
                "min": 2,
                "max": 7,
                "default": 4,
                "description": "Octave for the root note"
            },
            "mode": {
                "type": "list",
                "options": ["Major", "Minor", "Dorian", "Phrygian", "Lydian", "Mixolydian", "Locrian"],
                "default": "Major",
                "description": "Mode of the melody"
            },
            "use_selected_notes": {
                "type": "bool",
                "default": False,
                "description": "Use selected notes as input for AI generation"
            }
        }
        
        # Note utilities
        self.NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.NOTE_ALIASES = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
        
        # Initialize note index mapping
        self.NOTE_INDEX_MAPPING = {note: i for i, note in enumerate(self.NOTE_NAMES)}
        self.NOTE_INDEX_MAPPING.update({alias: self.NOTE_INDEX_MAPPING[note] for alias, note in self.NOTE_ALIASES.items()})
        
        # Cache for API keys (to avoid storing them in plaintext)
        self.api_key_cache = {}
        
        # Load cached API keys if available
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load cached API keys from a file if available"""
        try:
            cache_path = os.path.expanduser("~/.openai_melody_generator_api_key.json")
            if os.path.exists(cache_path):
                with open(cache_path, 'r') as f:
                    self.api_key_cache = json.load(f)
        except Exception:
            # Silently fail if we can't load cache
            self.api_key_cache = {}
    
    def _save_api_keys(self):
        """Save API keys to cache file"""
        try:
            cache_path = os.path.expanduser("~/.openai_melody_generator_api_key.json")
            with open(cache_path, 'w') as f:
                json.dump(self.api_key_cache, f)
            # Secure the file - only owner can read/write
            try:
                os.chmod(cache_path, 0o600)
            except:
                pass
        except Exception:
            # Silently fail if we can't save cache
            pass
    
    def _note_to_string(self, note_num: int) -> str:
        """Convert MIDI note number to note name with octave"""
        octave = note_num // 12
        note_index = note_num % 12
        note_name = self.NOTE_NAMES[note_index]
        return f"{note_name}{octave}"
    
    def _string_to_note(self, note_str: str) -> int:
        """Convert note name with octave to MIDI note number"""
        # Sanitize and standardize input
        note_str = note_str.strip().capitalize()
        
        # Handle notes with accidentals
        if len(note_str) >= 2 and note_str[1] in ['#', 'b']:
            note_name = note_str[:2]
            octave_str = note_str[2:]
        else:
            note_name = note_str[0]
            octave_str = note_str[1:]
        
        # Convert flats to sharps if needed
        if note_name in self.NOTE_ALIASES:
            note_name = self.NOTE_ALIASES[note_name]
        
        # Calculate MIDI note number
        try:
            octave = int(octave_str)
            note_index = self.NOTE_INDEX_MAPPING.get(note_name, 0)
            return (octave * 12) + note_index
        except ValueError:
            # Default to middle C if there's an error
            return 60
    
    def _extract_note_sequence(self, notes_text: str) -> List[Dict[str, Any]]:
        """
        Extract a sequence of notes from the AI model's text response
        
        Args:
            notes_text: Text containing note descriptions
            
        Returns:
            List of note dictionaries with pitch, start, duration, and velocity
        """
        notes = []
        
        # Different possible formats from AI responses
        
        # Format 1: Note-time-duration (e.g., "C4 0.0 0.5")
        pattern1 = r'([A-G][#b]?\d+)\s+([\d.]+)\s+([\d.]+)(?:\s+([\d.]+))?'
        
        # Format 2: Time-note-duration (e.g., "0.0 C4 0.5")
        pattern2 = r'([\d.]+)\s+([A-G][#b]?\d+)\s+([\d.]+)(?:\s+([\d.]+))?'
        
        # Format 3: JSON-like format
        pattern3 = r'\{\s*"(?:note|pitch)":\s*"([A-G][#b]?\d+)"[^}]*"(?:time|start)":\s*([\d.]+)[^}]*"(?:duration|length)":\s*([\d.]+)[^}]*\}'
        
        # Try all patterns
        for line in notes_text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
                
            # Try Pattern 1
            match = re.search(pattern1, line)
            if match:
                note, start, duration, *rest = match.groups()
                velocity = rest[0] if rest else 0.8
                notes.append({
                    'pitch': self._string_to_note(note),
                    'start': float(start),
                    'duration': float(duration),
                    'velocity': float(velocity) if velocity else 0.8
                })
                continue
                
            # Try Pattern 2
            match = re.search(pattern2, line)
            if match:
                start, note, duration, *rest = match.groups()
                velocity = rest[0] if rest else 0.8
                notes.append({
                    'pitch': self._string_to_note(note),
                    'start': float(start),
                    'duration': float(duration),
                    'velocity': float(velocity) if velocity else 0.8
                })
                continue
                
            # Try Pattern 3 (JSON-like)
            match = re.search(pattern3, line)
            if match:
                note, start, duration = match.groups()
                notes.append({
                    'pitch': self._string_to_note(note),
                    'start': float(start),
                    'duration': float(duration),
                    'velocity': 0.8  # Default velocity
                })
                continue
                
            # Try to parse JSON directly
            try:
                note_data = json.loads(line)
                if isinstance(note_data, dict):
                    # Handle single note JSON
                    if 'note' in note_data or 'pitch' in note_data:
                        pitch_val = note_data.get('note', note_data.get('pitch'))
                        # Handle if pitch is string or int
                        pitch = self._string_to_note(pitch_val) if isinstance(pitch_val, str) else int(pitch_val)
                        
                        start = float(note_data.get('start', note_data.get('time', 0.0)))
                        duration = float(note_data.get('duration', note_data.get('length', 0.25)))
                        velocity = float(note_data.get('velocity', note_data.get('volume', 0.8)))
                        
                        notes.append({
                            'pitch': pitch,
                            'start': start,
                            'duration': duration,
                            'velocity': velocity
                        })
            except:
                pass
        
        # Sort notes by start time
        notes.sort(key=lambda x: x['start'])
        return notes
    
    def _format_note_list(self, notes: List[pretty_midi.Note]) -> str:
        """
        Format a list of notes into a string representation for the AI prompt
        
        Args:
            notes: List of pretty_midi.Note objects
            
        Returns:
            Formatted string representing the notes
        """
        if not notes:
            return "No existing notes."
            
        formatted = []
        for note in sorted(notes, key=lambda n: (n.start, n.pitch)):
            note_name = self._note_to_string(note.pitch)
            formatted.append(f"{note_name} {note.start:.2f} {(note.end - note.start):.2f} {note.velocity/127:.2f}")
            
        return "\n".join(formatted)
    
    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for the AI
        
        Returns:
            System prompt string
        """
        prompt = """You are an expert music composer assistant that helps generate MIDI notes.

Your task is to create a sequence of musical notes based on the user's description.

Output Format:
- Each note should be in the format: NoteName StartTime Duration Velocity
- NoteName: Note name with octave (e.g., C4, F#5)
- StartTime: When the note starts in beats (floating point)
- Duration: How long the note lasts in beats (floating point)
- Velocity: Note volume from 0.0 to 1.0 (optional, defaults to 0.8)

Example output:
C4 0.0 0.5 0.8
E4 0.5 0.5 0.7
G4 1.0 1.0 0.9

Important guidelines:
- Start times should be absolute (not relative)
- Notes can overlap to create chords
- Use standard music notation (C, C#, D, etc.)
- Only output the note data in the specified format
- Do not include explanations, only output notes
"""
        return prompt
    
    def _build_user_prompt(self, user_prompt: str, existing_notes: List[pretty_midi.Note], melody_params: Dict[str, Any]) -> str:
        """
        Build the user prompt for the AI
        
        Args:
            user_prompt: User's prompt text
            existing_notes: Existing notes to reference
            melody_params: Additional melody parameters
            
        Returns:
            Complete user prompt
        """
        # Extract melody parameters
        melody_length = melody_params.get("melody_length", "4 bars")
        note_resolution = melody_params.get("note_resolution", "Eighth")
        root_note = melody_params.get("root_note", "C")
        octave = melody_params.get("octave", 4)
        mode = melody_params.get("mode", "Major")
        
        # Calculate reasonable time range based on melody length
        bars = int(melody_length.split()[0]) if melody_length[0].isdigit() else 4
        end_time = bars * 4.0  # Assuming 4 beats per bar
        
        # Create user prompt
        prompt = f"""Please create a melody with these characteristics:
- {user_prompt}
- Length: {melody_length}
- Key: {root_note} {mode}
- Root octave: {octave}
- Preferred note resolution: {note_resolution} notes

Time range: 0.0 to {end_time:.1f} beats

"""
        
        # Add existing notes if available
        if existing_notes:
            prompt += "Here are the existing notes that you should reference or complement:\n"
            prompt += self._format_note_list(existing_notes)
            prompt += "\n\nPlease generate additional notes that complement these existing notes."
        
        # Final instructions
        prompt += "\n\nRespond ONLY with the MIDI note sequence in the specified format, one note per line."
        
        return prompt
    
    def _query_openai(self, system_prompt: str, user_prompt: str, api_key: str, base_url: str, model: str, temperature: float, max_tokens: int) -> str:
        """
        Query OpenAI API directly using requests
        
        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt for the model
            api_key: OpenAI API key
            base_url: Base URL for the API
            model: Model name
            temperature: Temperature setting (0.0 to 2.0)
            max_tokens: Maximum tokens in the response
            
        Returns:
            Text response from OpenAI
        """
        # Format the URL
        if not base_url.endswith('/'):
            base_url += '/'
        url = f"{base_url}chat/completions"
        
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
        
        # Make the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        # Check for successful response
        if response.status_code != 200:
            error_msg = f"OpenAI API Error: {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f" - {error_data['error']['message']}"
            except:
                error_msg += f" - {response.text[:100]}..."
            raise Exception(error_msg)
        
        # Parse the response
        try:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"Failed to parse OpenAI response: {str(e)}")
    
    def _prompt_with_progress_indicator(self, system_prompt: str, user_prompt: str, api_key: str, base_url: str, model: str, temperature: float, max_tokens: int) -> str:
        """
        Prompt OpenAI with a progress indicator
        
        Args:
            system_prompt: System prompt for the model
            user_prompt: User prompt for the model
            api_key: API key
            base_url: Base URL for the API
            model: Model name
            temperature: Temperature setting
            max_tokens: Maximum tokens in the response
            
        Returns:
            Text response from the AI
        """
        # Variables for thread communication
        result = {"response": None, "error": None}
        
        # Thread function for API request
        def api_request_thread():
            try:
                response = self._query_openai(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                result["response"] = response
            except Exception as e:
                result["error"] = str(e)
        
        # Start API request in a separate thread
        thread = threading.Thread(target=api_request_thread)
        thread.daemon = True
        thread.start()
        
        # Display progress indicator while waiting
        progress_chars = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        i = 0
        start_time = time.time()
        
        try:
            # This would be replaced with your UI's progress indicator
            print(f"\rGenerating with OpenAI {progress_chars[i]} ", end="")
            while thread.is_alive():
                i = (i + 1) % len(progress_chars)
                elapsed = time.time() - start_time
                # This would be replaced with your UI's progress indicator
                print(f"\rGenerating with OpenAI {progress_chars[i]} {elapsed:.1f}s", end="")
                time.sleep(0.1)
            
            print("\rGeneration complete!                    ")
        except KeyboardInterrupt:
            print("\nCancelled by user.")
            # We can't directly stop the thread, but we can handle the cancellation
            # The daemon thread will be terminated when the program exits
            raise Exception("Generation cancelled by user.")
        
        # Check if there was an error
        if result["error"]:
            raise Exception(result["error"])
        
        return result["response"]
        
    def generate(self, existing_notes=None, **kwargs):
        """
        Generate notes using OpenAI
        
        Args:
            existing_notes: Optional list of existing notes
            **kwargs: Additional parameters from the UI
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        # Extract parameters
        prompt = kwargs.get("prompt", "Create a happy 4-bar melody in C major.")
        openai_model = kwargs.get("openai_model", "gpt-4-turbo")
        openai_base_url = kwargs.get("openai_base_url", "https://api.openai.com/v1/")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4096)
        use_selected_notes = kwargs.get("use_selected_notes", False)
        
        # Filter existing notes if use_selected_notes is True
        if existing_notes and use_selected_notes:
            filtered_notes = [note for note in existing_notes if hasattr(note, 'selected') and note.selected]
            existing_notes = filtered_notes if filtered_notes else None
        
        # Collect melody parameters
        melody_params = {
            "melody_length": kwargs.get("melody_length", "4 bars"),
            "note_resolution": kwargs.get("note_resolution", "Eighth"),
            "root_note": kwargs.get("root_note", "C"),
            "octave": kwargs.get("octave", 4),
            "mode": kwargs.get("mode", "Major")
        }
        
        # Get API key (prioritize input, fallback to cached)
        api_key = kwargs.get("openai_api_key", "")
        
        # Use cached key if available and no key provided
        if not api_key and "openai_api_key" in self.api_key_cache:
            api_key = self.api_key_cache["openai_api_key"]
            
        # Save key to cache if provided
        if api_key:
            self.api_key_cache["openai_api_key"] = api_key
            self._save_api_keys()
        
        # Check for API key
        if not api_key:
            raise ValueError("No OpenAI API key provided. Please enter an API key in the parameters.")
        
        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(prompt, existing_notes, melody_params)
        
        # Call the API with progress indicator
        try:
            response = self._prompt_with_progress_indicator(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                api_key=api_key,
                base_url=openai_base_url,
                model=openai_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            raise
        
        # Extract notes from the response
        note_sequence = self._extract_note_sequence(response)
        
        if not note_sequence:
            print("Could not parse any notes from the OpenAI response.")
            print("Response:", response[:500], "..." if len(response) > 500 else "")
            raise ValueError("Could not extract notes from the OpenAI response.")
        
        # Convert to pretty_midi.Note objects
        result = []
        for note_data in note_sequence:
            pitch = note_data['pitch']
            start = note_data['start']
            duration = note_data['duration']
            velocity = int(note_data['velocity'] * 127)  # Convert 0-1 to 0-127
            
            midi_note = pretty_midi.Note(
                velocity=velocity,
                pitch=pitch,
                start=start,
                end=start + duration
            )
            result.append(midi_note)
        
        return result