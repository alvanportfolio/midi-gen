import time
import threading
import pretty_midi
import pygame.midi

class MidiPlayer:
    """Class to handle MIDI playback functionality"""
    
    def __init__(self):
        # Initialize pygame midi
        pygame.midi.init()
        
        # Set up initial state
        self.notes = []
        self.is_playing = False
        self.paused = False
        self.current_position = 0.0
        self.start_time = 0.0
        self.pause_position = 0.0
        self.tempo = 120.0  # Default tempo in BPM
        self.tempo_scale = 1.0  # Scale factor for playback speed
        
        # Check available MIDI output devices
        self.output_id = self._get_default_output()
        
        # Create playback thread
        self.playback_thread = None
        self.stop_flag = threading.Event()
        
        # Log device info for debugging
        self._log_midi_devices()
    
    def _log_midi_devices(self):
        """Log available MIDI devices for debugging"""
        device_count = pygame.midi.get_count()
        print(f"Found {device_count} MIDI devices:")
        
        for i in range(device_count):
            info = pygame.midi.get_device_info(i)
            # In PySide6, device info is a tuple with interface, name, input, output, opened
            print(f"  Device {i}: {info[1].decode('utf-8')}, Input: {info[2]}, Output: {info[3]}")
        
        print(f"Default output ID: {self.output_id}")
        
        # For Microsoft Windows, use Microsoft GS Wavetable Synth if available
        if self.output_id == -1:
            for i in range(device_count):
                info = pygame.midi.get_device_info(i)
                name = info[1].decode('utf-8').lower()
                if info[3] and ('microsoft' in name or 'wavetable' in name or 'mapper' in name):
                    self.output_id = i
                    print(f"Using Windows default MIDI device: {name}, ID: {i}")
                    break
    
    def _get_default_output(self):
        """Get default MIDI output device ID"""
        device_count = pygame.midi.get_count()
        
        if device_count == 0:
            print("No MIDI devices found!")
            return -1
        
        # First try to find Microsoft GS Wavetable Synth (best for Windows)
        for i in range(device_count):
            info = pygame.midi.get_device_info(i)
            is_output = info[3]  # Index 3 is for output capability
            name = info[1].decode('utf-8').lower()
            
            if is_output and ('microsoft gs wavetable' in name):
                print(f"Selected Microsoft GS Wavetable Synth: {i}")
                return i
        
        # Find the first available output device
        for i in range(device_count):
            info = pygame.midi.get_device_info(i)
            is_output = info[3]  # Index 3 is for output capability
            
            if is_output:
                return i
        
        # Fall back to default
        try:
            default_id = pygame.midi.get_default_output_id()
            if default_id != -1:
                return default_id
        except:
            pass
        
        return -1
    
    def set_notes(self, notes):
        """Set the notes to be played"""
        # Add better error checking and debugging
        if not notes:
            print("WARNING: Empty notes list provided to set_notes")
            self.notes = []
        else:
            print(f"Setting {len(notes)} notes for playback")
            # Make sure these are proper pretty_midi Note objects
            valid_notes = []
            for note in notes:
                if hasattr(note, 'start') and hasattr(note, 'end') and hasattr(note, 'pitch') and hasattr(note, 'velocity'):
                    valid_notes.append(note)
                else:
                    print(f"WARNING: Invalid note object encountered: {note}")
            
            if len(valid_notes) != len(notes):
                print(f"WARNING: Only {len(valid_notes)} out of {len(notes)} notes are valid")
            
            self.notes = valid_notes
            
        self.current_position = 0.0
        self.pause_position = 0.0
        self.stop()
    
    def play(self):
        """Start playback of MIDI notes"""
        # Debug: Check if notes exist before playing
        print(f"PLAY called with {len(self.notes)} notes available")
        if not self.notes:
            print("WARNING: Attempting to play with no notes")
        
        if self.is_playing and not self.paused:
            return
            
        if self.paused:
            # Resume from paused state
            self.paused = False
            self.start_time = time.time() - self.pause_position
        else:
            # Start from beginning or current position
            self.start_time = time.time() - self.current_position
            
        self.is_playing = True
        
        # Start playback thread if not already running
        if self.playback_thread is None or not self.playback_thread.is_alive():
            self.stop_flag.clear()
            self.playback_thread = threading.Thread(target=self._playback_thread)
            self.playback_thread.daemon = True
            self.playback_thread.start()
    
    def pause(self):
        """Pause playback"""
        if self.is_playing and not self.paused:
            self.paused = True
            self.pause_position = self.get_current_position()
            self.is_playing = False
            
            # Send all notes off
            self._all_notes_off()
    
    def stop(self):
        """Stop playback and reset position"""
        if self.is_playing or self.playback_thread is not None:
            self.is_playing = False
            self.paused = False
            self.stop_flag.set()
            
            # Stop any currently playing notes
            self._all_notes_off()
            
            # Wait for thread to exit
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(1.0)
                
            self.playback_thread = None
            
        self.current_position = 0.0
        self.pause_position = 0.0
    
    def seek(self, position):
        """Jump to a specific position in seconds"""
        was_playing = self.is_playing
        
        # Stop any currently playing notes
        if was_playing:
            self._all_notes_off()
        
        # Update position
        self.current_position = position
        self.pause_position = position
        
        # If we were playing, adjust start time and continue
        if was_playing:
            self.start_time = time.time() - (position / self.tempo_scale)
    
    def get_current_position(self):
        """Get the current playback position in seconds, adjusted for tempo"""
        if self.is_playing:
            elapsed_time = time.time() - self.start_time
            self.current_position = elapsed_time * self.tempo_scale
            return self.current_position
        elif self.paused:
            return self.pause_position
        else:
            return self.current_position
    
    def _all_notes_off(self):
        """Send all notes off to MIDI output"""
        if self.output_id < 0:
            return  # No output device
            
        output = None
        try:
            output = pygame.midi.Output(self.output_id)
            
            # Send note off for all MIDI channels (0-15)
            for channel in range(16):
                # Controller 123 = All Notes Off
                output.write_short(0xB0 + channel, 123, 0)
                
            # Also send note off for common notes
            for pitch in range(0, 128):
                output.note_off(pitch, 0, 0)  # Channel 0
                
            output.close()
            output = None
        except Exception as e:
            print(f"Error when sending all notes off: {e}")
            if output:
                try:
                    output.close()
                except:
                    pass
    
    def _playback_thread(self):
        """Thread function to handle MIDI playback"""
        try:
            # Check if notes exist
            if len(self.notes) == 0:
                print("ERROR: No notes to play! Make sure you've loaded a MIDI file with notes.")
                self.is_playing = False
                return
                
            # Sort notes by start time
            sorted_notes = sorted(self.notes, key=lambda note: note.start)
            print(f"Playback thread starting with {len(sorted_notes)} notes")
            print(f"First note: pitch={sorted_notes[0].pitch}, start={sorted_notes[0].start}, end={sorted_notes[0].end}")
            
            # Open MIDI output if available
            output = None
            if self.output_id >= 0:
                try:
                    # Open the output device directly
                    output = pygame.midi.Output(self.output_id)
                    print(f"Successfully opened MIDI output device: {self.output_id}")
                    
                    # Test the MIDI output with a simple note
                    print("Testing MIDI output with a test note...")
                    output.note_on(60, 100, 0)  # Play middle C
                    time.sleep(0.1)
                    output.note_off(60, 0, 0)
                    
                except Exception as e:
                    print(f"Error opening MIDI output: {e}")
                    if output:
                        output.close()
                    
                    # Try one more time with explicit GS Wavetable initialization
                    try:
                        pygame.midi.quit()
                        pygame.midi.init()
                        
                        # Force to use Microsoft GS Wavetable Synth on Windows
                        device_count = pygame.midi.get_count()
                        for i in range(device_count):
                            info = pygame.midi.get_device_info(i)
                            is_output = info[3]
                            name = info[1].decode('utf-8').lower()
                            if is_output and ('microsoft gs wavetable' in name):
                                self.output_id = i
                                print(f"Using Microsoft GS Wavetable Synth: {i}")
                                break
                                
                        # Open the output device
                        output = pygame.midi.Output(self.output_id)
                        print(f"Successfully reopened MIDI output device: {self.output_id}")
                    except Exception as e2:
                        print(f"Failed to reopen MIDI device: {e2}")
                        self.is_playing = False
                        return
            else:
                print("No MIDI output device available")
                self.is_playing = False
                return
                
            # Playback info
            print(f"Starting playback with {len(sorted_notes)} notes, from position {self.get_current_position()}")
            print(f"Note range: {sorted_notes[0].start}s to {sorted_notes[-1].end}s")
            print(f"First few notes: {[pretty_midi.note_number_to_name(n.pitch) for n in sorted_notes[:5]]}")
            
            # Simulate MIDI playback 
            last_time = self.get_current_position()
            notes_on = {}  # Keep track of currently playing notes
            
            # Find the first note to play based on our current position
            next_note_idx = 0
            while next_note_idx < len(sorted_notes) and sorted_notes[next_note_idx].start < last_time:
                next_note_idx += 1
            
            # Main playback loop
            while not self.stop_flag.is_set() and self.is_playing:
                current_time = self.get_current_position()
                
                # Process note-offs for any notes that have ended
                notes_to_remove = []
                for note_idx, note_start_time in notes_on.items():
                    note = sorted_notes[note_idx]
                    if current_time >= note.end:
                        if output:
                            # Send note off
                            try:
                                output.note_off(note.pitch, 0, channel=0)
                                print(f"Note OFF: {pretty_midi.note_number_to_name(note.pitch)}")
                            except Exception as e:
                                print(f"Error sending note off: {e}")
                        notes_to_remove.append(note_idx)
                
                # Remove finished notes from tracking
                for note_idx in notes_to_remove:
                    del notes_on[note_idx]
                
                # Process note-ons for any notes that should start
                while (next_note_idx < len(sorted_notes) and 
                       current_time >= sorted_notes[next_note_idx].start):
                    note = sorted_notes[next_note_idx]
                    
                    if current_time < note.end:  # Only play if the note hasn't already ended
                        if output:
                            # Send note on
                            try:
                                output.note_on(note.pitch, int(note.velocity), channel=0)
                                print(f"Note ON: {pretty_midi.note_number_to_name(note.pitch)}, vel: {int(note.velocity)}")
                            except Exception as e:
                                print(f"Error sending note on: {e}")
                        notes_on[next_note_idx] = current_time
                    
                    next_note_idx += 1
                
                # Sleep a small amount to reduce CPU usage
                # Use smaller sleep time for higher BPM to ensure responsiveness
                sleep_time = min(0.005, 0.005 / max(1.0, self.tempo_scale))
                time.sleep(sleep_time)
                
                # Update last time
                last_time = current_time
            
            # Turn off any remaining notes
            if output:
                for note_idx in notes_on:
                    note = sorted_notes[note_idx]
                    try:
                        output.note_off(note.pitch, 0, channel=0)
                    except:
                        pass
                output.close()
                
        except Exception as e:
            print(f"Error in playback thread: {e}")
        finally:
            self.is_playing = False
            print("Playback thread exited")
    
    def __del__(self):
        """Clean up resources"""
        self.stop()
        try:
            pygame.midi.quit()
        except:
            pass

    def test_play_scale(self):
        """Test function to play a C major scale"""
        from pretty_midi import Note, Instrument
        
        # Create a set of notes for a C major scale
        scale_notes = []
        start_time = 0.0
        duration = 0.5  # half second per note
        
        # C major scale: C, D, E, F, G, A, B, C
        for pitch in [60, 62, 64, 65, 67, 69, 71, 72]:
            note = Note(
                velocity=100,
                pitch=pitch,
                start=start_time,
                end=start_time + duration
            )
            scale_notes.append(note)
            start_time += duration
            
        print(f"Created test scale with {len(scale_notes)} notes")
        
        # Set the notes and play
        self.set_notes(scale_notes)
        self.play()
        
        return True

    def set_tempo(self, bpm):
        """Set the tempo in beats per minute and adjust playback speed"""
        if bpm <= 0:
            print("Error: BPM must be positive")
            return
            
        was_playing = self.is_playing
        current_position = self.get_current_position()
        
        # Calculate tempo scale factor (relative to 120 BPM baseline)
        self.tempo = float(bpm)
        self.tempo_scale = self.tempo / 120.0
        
        # If playing, adjust start time to maintain current position with new tempo
        if was_playing:
            self.start_time = time.time() - (current_position / self.tempo_scale)
        
        print(f"Tempo set to {bpm} BPM (scale factor: {self.tempo_scale})")

# Test function to run if this file is executed directly
if __name__ == "__main__":
    print("Testing MIDI player...")
    player = MidiPlayer()
    
    # Wait a moment for MIDI to initialize
    time.sleep(1)
    
    # Play a test scale
    print("\nPlaying test scale...")
    player.test_play_scale()
    
    # Wait for the scale to finish
    time.sleep(5)
    
    print("Test complete. If you didn't hear anything, check your system's MIDI settings.")