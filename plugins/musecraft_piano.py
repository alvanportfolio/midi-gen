# plugins/alex_melody_godzilla.py
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
            def create_temp_midi_from_notes(notes, tempo=120.0, instrument_program=0):
                import tempfile
                pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
                instrument = pretty_midi.Instrument(program=instrument_program)
                for note in notes:
                    instrument.notes.append(note)
                pm.instruments.append(instrument)
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mid', prefix='musecraft_piano_plugin_input_')
                os.close(temp_fd)
                pm.write(temp_path)
                return temp_path
            @staticmethod
            def create_primer_midi(prime_note_duration=1.0, prime_note_pitch=72, chordify_prime_note=True):
                notes = []

                note = pretty_midi.Note(velocity=80, pitch=prime_note_pitch, start=0.0, end=prime_note_duration)
                notes.append(note)
                
                if chordify_prime_note:
                    note = pretty_midi.Note(velocity=80, pitch=prime_note_pitch-12, start=0.0, end=prime_note_duration)
                    notes.append(note)                    
                    note = pretty_midi.Note(velocity=80, pitch=prime_note_pitch-24, start=0.0, end=prime_note_duration)
                    notes.append(note)
                    
                return MidiFileHandler.create_temp_midi_from_notes(notes)
            
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
    def create_temp_midi_from_notes(notes, tempo=120.0, instrument_program=0):
        import tempfile
        pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)
        instrument = pretty_midi.Instrument(program=instrument_program)
        for note in notes:
            instrument.notes.append(note)
        pm.instruments.append(instrument)
        temp_fd, temp_path = tempfile.mkstemp(suffix='.mid', prefix='musecraft_piano_plugin_input_')
        os.close(temp_fd)
        pm.write(temp_path)
        return temp_path
    @staticmethod
    def create_primer_midi(prime_note_duration=1.0, prime_note_pitch=72, chordify_prime_note=False):
        notes = []

        note = pretty_midi.Note(velocity=80, pitch=prime_note_pitch, start=0.0, end=prime_note_duration)
        notes.append(note)
        
        if chordify_prime_note:
            note = pretty_midi.Note(velocity=80, pitch=prime_note_pitch-12, start=0.0, end=prime_note_duration)
            notes.append(note)                    
            note = pretty_midi.Note(velocity=80, pitch=prime_note_pitch-24, start=0.0, end=prime_note_duration)
            notes.append(note)
            
        return MidiFileHandler.create_temp_midi_from_notes(notes)
    
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

class MuseCraftPiano(PluginBase):
    """
    MIDI generator plugin that uses the MuseCraft-Piano model
    via Gradio API to generate sophisticated piano melodies
    """
    
    def __init__(self):
        super().__init__()
        self.name = "MuseCraft Piano"
        self.description = "AI-powered piano melody generation using MuseCraft Piano model"
        self.author = "Alex" 
        self.version = "1.0"
        
        # Gradio API endpoint
        self.api_endpoint = "projectlosangeles/MuseCraft-Piano"
        self.client = None
        self.connection_manager = ApiConnectionManager(max_retries=3, timeout=60)
        
        # Define parameters matching the Gradio API
        self.parameters = {
            "hf_auth_token": {
                "type": "str",
                "default": '',
                "description": "Hugging Face auth token"
            },
            "num_prime_tokens": {
                "type": "int",
                "min": 512,
                "max": 8192,
                "default": 3072,
                "description": "Number of tokens from input to use as primer"
            },
            "num_gen_tokens": {
                "type": "int",
                "min": 128,
                "max": 2048,
                "default": 512,
                "description": "Number of new tokens to generate"
            },
            "num_mem_tokens": {
                "type": "int",
                "min": 1024,
                "max": 8192,
                "default": 4096,
                "description": "Number of memory tokens for the model"
            },
            "model_temperature": {
                "type": "float",
                "min": 0.1,
                "max": 2.0,
                "default": 0.9,
                "description": "Creativity/randomness of generation (higher = more creative)"
            },
            "use_existing_notes": {
                "type": "bool",
                "default": True,
                "description": "Use existing notes as input primer (if available)"
            },
            "prime_note_duration": {
                "type": "float",
                "min": 0.1,
                "max": 4.0,
                "default": 1.0,
                "description": "Prime note duration (seconds)"
            },
            "prime_note_pitch": {
                "type": "int",
                "min": 36,
                "max": 120,
                "default": 72,
                "description": "Prime note MIDI pitch"
            },
            "chordify_prime_note": {
                "type": "bool",
                "default": False,
                "description": "Chordify prime note"
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
            print(f"Failed to connect to MuseCraft-Piano API: {e}")
            return None
    
    def _create_temp_midi_file(self, notes: List[pretty_midi.Note] = None, **kwargs) -> str:
        """
        Create a temporary MIDI file from existing notes or a simple primer
        
        Args:
            notes: List of existing notes to convert to MIDI
            **kwargs: Additional parameters for primer creation
            
        Returns:
            Path to temporary MIDI file
        """
        if notes and len(notes) > 0:
            return MidiFileHandler.create_temp_midi_from_notes(notes)
        else:
            prime_note_duration = kwargs.get("prime_note_duration", 1.0)
            prime_note_pitch = kwargs.get("prime_note_pitch", 72)
            chordify_prime_note = kwargs.get("chordify_prime_note", False)
            return MidiFileHandler.create_primer_midi(
                prime_note_duration=prime_note_duration, 
                prime_note_pitch=prime_note_pitch, 
                chordify_prime_note=chordify_prime_note
            )
    
    def _call_musecraft_api_async(self, input_midi_path: str, result_container: dict, **kwargs):
        """
        Call the MuseCraft-Piano API asynchronously with progress updates
        
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
                
                print("🔌 Connecting to MuseCraft-Piano...")
                result_container['status'] = 'connected'
                
                # Validate parameters
                validated_params = validate_api_parameters(kwargs, self.parameters)
                
                result_container['status'] = 'generating'
                print(f"🎵 Generating melody with MuseCraft-Piano:")
                print(f"   Prime tokens: {validated_params.get('num_prime_tokens', 3072)}")
                print(f"   Generation tokens: {validated_params.get('num_gen_tokens', 512)}")
                print(f"   Memory tokens: {validated_params.get('num_mem_tokens', 4096)}")
                print(f"   Temperature: {validated_params.get('model_temperature', 0.9)}")
                print("   ⏳ This may take 1-2 minutes, please wait...")
                
                # Call the generation API (single endpoint, simpler than Godzilla)
                result = client.predict(
                    input_midi=handle_file(input_midi_path),
                    num_prime_tokens=validated_params.get("num_prime_tokens", 3072),
                    num_gen_tokens=validated_params.get("num_gen_tokens", 512),
                    num_mem_tokens=validated_params.get("num_mem_tokens", 4096),
                    model_temperature=validated_params.get("model_temperature", 0.9),
                    api_name="/generate_music"
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
                    print("🔌 Connecting to MuseCraft-Piano AI...")
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
        Generate MIDI notes using MuseCraft-Piano
        
        Args:
            existing_notes: Optional list of existing notes to build upon
            **kwargs: Generation parameters
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        print("Starting Alex Melody Godzilla (MuseCraft-Piano) generation...")
        
        # Extract parameters
        use_existing_notes = kwargs.get("use_existing_notes", True)
        fallback_on_error = kwargs.get("fallback_on_error", True)
        
        with TempFileManager() as temp_manager:
            try:
                # Create input MIDI file
                if use_existing_notes and existing_notes:
                    print(f"Using {len(existing_notes)} existing notes as input primer")
                    input_midi_path = self._create_temp_midi_file(existing_notes)
                else:
                    prime_note_duration = kwargs.get("prime_note_duration", 1.0)
                    prime_note_pitch = kwargs.get("prime_note_pitch", 72)
                    chordify_prime_note = kwargs.get("chordify_prime_note", False)
                    print(f"Prime note: MIDI pitch {prime_note_pitch} with duration ({prime_note_duration}s)")
                    input_midi_path = self._create_temp_midi_file(None, **kwargs)
                
                temp_manager.add_temp_file(input_midi_path)
                
                # Call the API asynchronously to keep UI responsive
                print("🚀 Starting MuseCraft-Piano melody generation...")
                print("   💡 The app will remain responsive during generation")
                
                result_container = {}
                api_thread = self._call_musecraft_api_async(input_midi_path, result_container, **kwargs)
                
                # Wait for completion with progress updates
                timeout = kwargs.get("timeout_seconds", 180)
                generated_midi_path = self._wait_for_api_with_progress(api_thread, result_container, timeout)
                
                if generated_midi_path and os.path.exists(generated_midi_path):
                    print("Successfully generated melody! Parsing results...")
                    temp_manager.add_temp_file(generated_midi_path)
                    
                    # Check file size for debugging
                    file_size = os.path.getsize(generated_midi_path)
                    print(f"Generated MIDI file size: {file_size} bytes")
                    
                    generated_notes = MidiFileHandler.parse_midi_file(generated_midi_path)
                    
                    if generated_notes:
                        print(f"Generated {len(generated_notes)} notes from MuseCraft-Piano AI")
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