import time # For test_play_scale sleep
import pretty_midi # For Note type hint
import pygame.midi # For pygame.midi.quit in main test
from midi.playback_controller import PlaybackController

class MidiPlayer:
    """
    Facade class for MIDI playback functionality.
    Delegates most operations to PlaybackController.
    """
    
    def __init__(self):
        self.controller = PlaybackController()
        # The 'notes' attribute is now primarily managed by the controller.
        # This class can expose it via a property if direct access is still needed by UI.
        # self.notes = [] # No longer directly managed here

    def set_notes(self, notes: list[pretty_midi.Note]):
        """Set the notes to be played."""
        self.controller.set_notes(notes)

    def play(self):
        """Start playback of MIDI notes."""
        self.controller.play()

    def pause(self):
        """Pause playback."""
        self.controller.pause()

    def stop(self):
        """Stop playback and reset position."""
        self.controller.stop()

    def seek(self, position_sec: float):
        """Jump to a specific position in seconds."""
        self.controller.seek(position_sec)

    def get_current_position(self) -> float:
        """Get the current playback position in seconds."""
        return self.controller.get_current_position()

    @property
    def is_playing(self) -> bool:
        """Check if playback is active."""
        return self.controller.is_playing
    
    @property
    def notes(self) -> list[pretty_midi.Note]:
        """Get the current list of notes."""
        return self.controller.notes

    # Expose paused state if needed by UI, e.g. for button state
    @property
    def paused(self) -> bool:
        return self.controller.paused

    def set_tempo(self, bpm: float):
        """Set the tempo in beats per minute."""
        self.controller.set_tempo(bpm)

    def set_instrument(self, program_num: int):
        """Set the MIDI instrument (program change)."""
        # Assuming channel 0 for simplicity, or make channel configurable
        if hasattr(self.controller, 'set_instrument'):
            self.controller.set_instrument(program_num) 
        else:
            print("MidiPlayer: Controller does not have set_instrument method.")

    def set_volume(self, volume_float: float):
        """Sets the master volume for playback."""
        if hasattr(self.controller, 'set_master_volume'):
            self.controller.set_master_volume(volume_float)
        else:
            print("MidiPlayer: Controller does not have set_master_volume method.")

    def cleanup(self):
        """Clean up resources."""
        self.controller.cleanup()

    def __del__(self):
        self.cleanup()

    def test_play_scale(self):
        """Test function to play a C major scale."""
        from pretty_midi import Note # Keep local import for test
        
        scale_notes = []
        start_time = 0.0
        duration = 0.5
        
        for pitch_val in [60, 62, 64, 65, 67, 69, 71, 72]: # Corrected variable name
            note = Note(
                velocity=100,
                pitch=pitch_val, # Corrected variable name
                start=start_time,
                end=start_time + duration
            )
            scale_notes.append(note)
            start_time += duration
            
        print(f"MidiPlayer (test): Created test scale with {len(scale_notes)} notes")
        self.set_notes(scale_notes)
        self.play()
        return True

# Test function to run if this file is executed directly
if __name__ == "__main__":
    print("Testing MidiPlayer facade...")
    player = MidiPlayer()
    
    # Wait a moment for MIDI to initialize (DeviceManager handles init)
    time.sleep(0.5) 
    
    print("\nPlaying test scale via MidiPlayer facade...")
    player.test_play_scale()
    
    # Keep alive for playback
    try:
        while player.is_playing or player.get_current_position() < 4.0: # Wait for scale to roughly finish
            time.sleep(0.1)
            if player.is_playing:
                 print(f"Test playback position: {player.get_current_position():.2f}s")
            if player.get_current_position() >= 3.9 and player.is_playing: # Stop a bit before end
                player.stop()
                print("Test scale stopped by main.")
                break
    except KeyboardInterrupt:
        player.stop()
        print("Test interrupted.")
    finally:
        player.cleanup() # Explicit cleanup
        if pygame.midi.get_init(): # Quit pygame.midi if it was initialized
            pygame.midi.quit()
    
    print("MidiPlayer test complete.")
