# plugins/musecraft_chords_progressions.py
import os
import threading
import time
import pretty_midi
from plugin_api import PluginBase
from typing import List, Dict, Any, Optional
from gradio_client import Client, handle_file

try:
    # Try absolute import first (when run as plugin)
    from api_helpers import (
        ApiConnectionManager, 
        MidiFileHandler, 
        TempFileManager,
        validate_api_parameters,
        create_fallback_melody
    )
except ImportError:
    # Fallback for relative import (when run from plugins directory)
    try:
        from .api_helpers import (
            ApiConnectionManager, 
            MidiFileHandler, 
            TempFileManager,
            validate_api_parameters,
            create_fallback_melody
        )
    except ImportError:
        # If api_helpers not available, create minimal fallbacks
        print("Warning: api_helpers not available, using minimal fallbacks")
        
        class ApiConnectionManager:
            def __init__(self, max_retries=3, timeout=60):
                self.max_retries = max_retries
                
            def call_with_retry(self, api_func, *args, **kwargs):
                for attempt in range(self.max_retries):
                    try:
                        return api_func(*args, **kwargs)
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            raise e
                        import time
                        time.sleep(2 ** attempt)
                return None
        
        class MidiFileHandler:           
            @staticmethod
            def parse_midi_file(midi_path):
                try:
                    pm = pretty_midi.PrettyMIDI(midi_path)
                    notes = []
                    for instrument in pm.instruments:
                        if not instrument.is_drum:
                            notes.extend(instrument.notes)
                    notes.sort(key=lambda n: n.start)
                    return notes
                except Exception:
                    return []
        
        class TempFileManager:
            def __init__(self):
                self.temp_files = []
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                for file_path in self.temp_files:
                    try:
                        if os.path.exists(file_path):
                            os.unlink(file_path)
                    except:
                        pass
                self.temp_files.clear()
            def add_temp_file(self, file_path):
                self.temp_files.append(file_path)
        
        def validate_api_parameters(params, param_specs):
            validated = {}
            for param_name, spec in param_specs.items():
                value = params.get(param_name, spec.get("default"))
                if value is not None:
                    param_type = spec.get("type", "str")
                    try:
                        if param_type == "int":
                            value = int(value)
                        elif param_type == "float":
                            value = float(value)
                        elif param_type == "bool":
                            value = bool(value)
                    except:
                        value = spec.get("default")
                    if "min" in spec and value < spec["min"]:
                        value = spec["min"]
                    if "max" in spec and value > spec["max"]:
                        value = spec["max"]
                    validated[param_name] = value
            return validated
        
        def create_fallback_melody(length_bars=4, scale_root=60, scale_type="major"):
            import random
            intervals = [0, 2, 4, 5, 7, 9, 11]  # major scale
            scale_notes = [scale_root + interval for interval in intervals]
            scale_notes.extend([scale_root + 12 + interval for interval in intervals])
            notes = []
            note_duration = 0.5
            current_time = 0.0
            total_notes = length_bars * 8
            for i in range(total_notes):
                if random.random() > 0.15:
                    pitch = random.choice(scale_notes)
                    velocity = random.randint(60, 100)
                    duration = note_duration * random.uniform(0.8, 1.0)
                    note = pretty_midi.Note(velocity=velocity, pitch=pitch, start=current_time, end=current_time + duration)
                    notes.append(note)
                current_time += note_duration
            return notes
        
class MidiFileHandler:    
    @staticmethod
    def parse_midi_file(midi_path):
        try:
            pm = pretty_midi.PrettyMIDI(midi_path)
            notes = []
            for instrument in pm.instruments:
                if not instrument.is_drum:
                    notes.extend(instrument.notes)
            notes.sort(key=lambda n: n.start)
            return notes
        except Exception:
            return []

class MuseCraftChordsProgressions(PluginBase):
    """
    MIDI generator plugin that uses the MuseCraft-Chords-Progressions Hugging Face space
    via Gradio API to generate unique chords progressions
    """
    
    def __init__(self):
        super().__init__()
        self.name = "MuseCraft Chords Progressions"
        self.description = "Algorithmic chords progressions generation with MuseCraft"
        self.author = "Alex" 
        self.version = "1.0"
        
        # Gradio API endpoint
        self.api_endpoint = "projectlosangeles/MuseCraft-Chords-Progressions"
        self.client = None
        self.connection_manager = ApiConnectionManager(max_retries=3, timeout=60)
        
        # Define parameters matching the Gradio API
        self.parameters = {
            "hf_auth_token": {
                "type": "str",
                "default": '',
                "description": "Hugging Face auth token"
            },
            "minimum_song_length_in_chords_chunks": {
                "type": "int",
                "min": 4,
                "max": 60,
                "default": 30,
                "description": "Song length in chords chunks"
            },
            "chord_time_step": {
                "type": "int",
                "min": 100,
                "max": 1000,
                "default": 250,
                "description": "Chord time step"
            },
            "fallback_on_error": {
                "type": "bool",
                "default": True,
                "description": "Generate simple fallback melody if API fails"
            },
            "timeout_seconds": {
                "type": "int",
                "min": 60,
                "max": 600,
                "default": 180,
                "description": "Maximum wait time for API response (seconds)"
            }
        }
    
    def _get_api_client(self, **kwargs):
        """Get or create API client"""
        try:
            if self.client is None:
                if kwargs.get("hf_auth_token", '') != '':
                    hf_token = kwargs.get("hf_auth_token", '')
                
                else:
                    hf_token = False
                self.client = Client(self.api_endpoint, hf_token=hf_token)
            return self.client
        except Exception as e:
            print(f"Failed to connect to MuseCraft-Chords-Progressions API: {e}")
            return None
    
    def _call_musecraft_api_async(self, input_midi_path: str, result_container: dict, **kwargs):
        """
        Call the MuseCraft-Chords-Progressions API asynchronously with progress updates
        
        Args:
            input_midi_path: Path to input MIDI file
            result_container: Dict to store result and status
            **kwargs: API parameters
        """
        def make_api_call():
            try:
                result_container['status'] = 'connecting'
                client = self._get_api_client(**kwargs)
                if client is None:
                    raise Exception("Could not connect to API client")
                
                print("🔌 Connecting to MuseCraft-Chords-Progressions...")
                result_container['status'] = 'connected'
                
                # Validate parameters
                validated_params = validate_api_parameters(kwargs, self.parameters)
                
                result_container['status'] = 'generating'
                print(f"🎵 Generating chords progression with MuseCraft:")
                print(f"   Minimum song length in chords chunks: {validated_params.get('minimum_song_length_in_chords_chunks', 30)}")
                print(f"   Chord time step: {validated_params.get('chord_time_step', 250)}")
                
                # Call the generation API (single endpoint, simpler than Godzilla)                
                result = client.predict(
                        minimum_song_length_in_chords_chunks=validated_params.get("minimum_song_length_in_chords_chunks", 30),
                        chords_chunks_memory_ratio=1,
                        chord_time_step=validated_params.get("chord_time_step", 250),
                        merge_chords_notes=2000,
                        melody_MIDI_patch_number=40,
                        chords_progression_MIDI_patch_number=0,
                        base_MIDI_patch_number=35,
                        add_drums=True,
                        output_as_solo_piano=True,
                        api_name="/Generate_Chords_Progression"
                )                
                # The API returns a single filepath directly
                if result and isinstance(result, str):
                    midi_file_path = result
                    print(f"🎼 Received MIDI file: {midi_file_path}")
                    result_container['result'] = midi_file_path
                    result_container['status'] = 'success'
                else:
                    raise Exception("No MIDI file returned from API")
                    
            except Exception as e:
                print(f"❌ API call failed: {e}")
                result_container['error'] = str(e)
                result_container['status'] = 'error'
        
        # Start the API call in a background thread
        thread = threading.Thread(target=make_api_call, daemon=True)
        thread.start()
        return thread
    
    def _wait_for_api_with_progress(self, thread: threading.Thread, result_container: dict, max_wait_time: int = 180) -> Optional[str]:
        """
        Wait for API call to complete with progress updates to keep UI responsive
        
        Args:
            thread: The thread running the API call
            result_container: Container with result and status
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            Path to generated MIDI file or None if failed
        """
        start_time = time.time()
        last_status = None
        dots = 0
        
        while thread.is_alive() and (time.time() - start_time) < max_wait_time:
            current_status = result_container.get('status', 'unknown')
            
            # Print status updates
            if current_status != last_status:
                if current_status == 'connecting':
                    print("🔌 Connecting to MuseCraft-Chords-Progressions HF space...")
                elif current_status == 'connected':
                    print("✅ Connected successfully!")
                elif current_status == 'generating':
                    print("🎵 AI is composing your melody...")
                last_status = current_status
            
            # Show progress dots for long operations
            if current_status == 'generating':
                dots = (dots + 1) % 4
                progress_dots = "." * dots + " " * (3 - dots)
                print(f"\r   Working{progress_dots} ({int(time.time() - start_time)}s elapsed)", end="", flush=True)
            
            # Small sleep to keep UI responsive and not spam output
            time.sleep(0.5)
        
        # Clear the progress line
        if last_status == 'generating':
            print()  # New line after progress dots
        
        # Check if thread completed
        if thread.is_alive():
            print("⚠️  API call timed out, but it may still complete in background")
            return None
        
        # Check result
        if 'error' in result_container:
            print(f"❌ API Error: {result_container['error']}")
            return None
        elif 'result' in result_container:
            print(f"🎉 Success! Generated melody ready!")
            return result_container['result']
        else:
            print("❌ Unknown error - no result received")
            return None
    
    def generate(self, existing_notes: Optional[List[pretty_midi.Note]] = None, **kwargs) -> List[pretty_midi.Note]:
        """
        Generate MIDI notes using MuseCraft-Chords-Progressions
        
        Args:
            existing_notes: Optional list of existing notes to build upon
            **kwargs: Generation parameters
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        print("Starting MuseCraft-Chords-Progressions generation...")
        
        # Extract parameters
        fallback_on_error = kwargs.get("fallback_on_error", True)
        
        with TempFileManager() as temp_manager:
            try:
                
                # Call the API asynchronously to keep UI responsive
                print("🚀 Starting MuseCraft Chords Progression generation...")
                print("   💡 The app will remain responsive during generation")
                
                result_container = {}
                api_thread = self._call_musecraft_api_async(None, result_container, **kwargs)
                
                # Wait for completion with progress updates
                timeout = kwargs.get("timeout_seconds", 180)
                generated_midi_path = self._wait_for_api_with_progress(api_thread, result_container, timeout)
                
                if generated_midi_path and os.path.exists(generated_midi_path):
                    print("Successfully generated chords progression! Parsing results...")
                    temp_manager.add_temp_file(generated_midi_path)
                    
                    # Check file size for debugging
                    file_size = os.path.getsize(generated_midi_path)
                    print(f"Generated MIDI file size: {file_size} bytes")
                    
                    generated_notes = MidiFileHandler.parse_midi_file(generated_midi_path)
                    
                    if generated_notes:
                        print(f"Generated {len(generated_notes)} notes from MuseCraft-Chords-Progressions")
                        return generated_notes
                    else:
                        print("Generated MIDI file was empty")
                else:
                    print("API did not return a valid MIDI file")
                
                # Fallback if API failed
                if fallback_on_error:
                    print("Using fallback melody generation...")
                    fallback_scale = "major"
                    return create_fallback_melody(length_bars=4, scale_root=60, scale_type=fallback_scale)
                else:
                    print("No fallback requested, returning empty result")
                    return []
                    
            except Exception as e:
                print(f"Generation failed: {e}")
                if fallback_on_error:
                    print("Using fallback melody generation...")
                    fallback_scale = "major"
                    return create_fallback_melody(length_bars=4, scale_root=60, scale_type=fallback_scale)
                return [] 