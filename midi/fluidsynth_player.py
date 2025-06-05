import fluidsynth
import os
import inspect # For inspect.getfile
from config.constants import DEFAULT_MIDI_PROGRAM
from utils import get_resource_path # Import the new helper

# Default SoundFont path relative to project root
DEFAULT_SOUNDFONT_RELATIVE_PATH = "soundbank/soundfont.sf2"

class FluidSynthPlayer:
    def __init__(self, soundfont_path_str: str | None = None): # Allow passing a specific path
        self.fs = None
        self.soundfont_id = None
        
        # Determine the soundfont path to use
        if soundfont_path_str:
            self.soundfont_path = soundfont_path_str
        else:
            self.soundfont_path = get_resource_path(DEFAULT_SOUNDFONT_RELATIVE_PATH)

        try:
            # Print the path of the imported fluidsynth module for diagnostics
            print(f"Attempting to use fluidsynth module from: {inspect.getfile(fluidsynth)}")
            
            # Note: FluidSynth may show warnings during initialization such as:
            # - "SDL3 not initialized" - This is normal if SDL3 is not used
            # - "Unknown parameter" warnings - These are usually version-related and can be ignored
            # These warnings do not affect functionality as FluidSynth will use available audio drivers
            
            self.fs = fluidsynth.Synth()
            # Start the synth. For Windows, 'dsound' or 'wasapi' might be needed.
            # For Linux, 'alsa' or 'pulseaudio'. For macOS, 'coreaudio'.
            # 'dsound' is often a safe default for Windows if PortAudio is not set up.
            # Let's try with default first, or allow configuration.
            # For now, let's assume fluidsynth.Synth() picks a sensible default audio driver.
            # Or, we might need to specify it, e.g., self.fs.start(driver="dsound") on Windows.
            # For simplicity, I'll rely on the default driver selection by pyfluidsynth.
            # If issues arise, driver selection might need to be exposed or made platform-dependent.
            self.fs.start()

            if not os.path.exists(self.soundfont_path):
                print(f"ERROR: SoundFont file not found at '{self.soundfont_path}'.")
                print("Please ensure 'soundbank/soundfont.sf2' exists relative to the application or _MEIPASS folder.")
                # self.fs.delete() # Clean up synth if soundfont is critical
                # self.fs = None
                self.soundfont_id = None
                # Optionally, raise an error or use a silent fallback
            else:
                self.soundfont_id = self.fs.sfload(self.soundfont_path)
                if self.soundfont_id == fluidsynth.FLUID_FAILED: # More robust check for failure
                    print(f"ERROR: Failed to load SoundFont from '{self.soundfont_path}'.")
                    self.soundfont_id = None
                else:
                    print(f"SoundFont loaded successfully from '{self.soundfont_path}' with ID {self.soundfont_id}")
                    # Default instrument for all channels (0-15)
                    for channel in range(16):
                        self.fs.program_select(channel, self.soundfont_id, 0, DEFAULT_MIDI_PROGRAM)

        except Exception as e:
            print(f"Failed to initialize FluidSynth: {e}")
            print("MIDI playback via FluidSynth will not be available.")
            if self.fs:
                self.fs.delete()
            self.fs = None
            self.soundfont_id = None

    def set_instrument(self, channel: int, program_num: int):
        if self.fs and self.soundfont_id is not None:
            if 0 <= channel <= 15 and 0 <= program_num <= 127:
                # bank_num is typically 0 for GM SoundFonts
                self.fs.program_select(channel, self.soundfont_id, 0, program_num)
            else:
                print(f"Error: Invalid channel ({channel}) or program number ({program_num})")

    def noteon(self, channel: int, pitch: int, velocity: int):
        if self.fs and self.soundfont_id is not None:
            if 0 <= channel <= 15 and 0 <= pitch <= 127 and 0 <= velocity <= 127:
                self.fs.noteon(channel, pitch, velocity)
            else:
                print(f"Error: Invalid parameters for noteon: ch={channel}, p={pitch}, v={velocity}")

    def noteoff(self, channel: int, pitch: int):
        if self.fs and self.soundfont_id is not None:
            if 0 <= channel <= 15 and 0 <= pitch <= 127:
                self.fs.noteoff(channel, pitch)
            else:
                print(f"Error: Invalid parameters for noteoff: ch={channel}, p={pitch}")
    
    def all_notes_off(self, channel: int = -1):
        """Stop all notes on a specific channel, or all channels if channel is -1."""
        if self.fs:
            if channel == -1:
                for ch in range(16):
                    self.fs.cc(ch, 123, 0) # All Notes Off CC message
            elif 0 <= channel <= 15:
                 self.fs.cc(channel, 123, 0)
            else:
                print(f"Error: Invalid channel for all_notes_off: {channel}")

    def set_gain(self, gain: float):
        """Sets the master gain of the synthesizer."""
        if self.fs:
            # FluidSynth gain is typically 0.0 to 10.0.
            # The task specifies mapping 0-100% to 0.0-1.0 for FluidSynth.
            # We'll assume the 0.0-1.0 value is directly usable if fs.set_gain handles it,
            # or scale it if fs.set_gain expects a different range (e.g. 0-10).
            # For now, let's assume pyfluidsynth's set_gain takes a value that
            # can be 0.0-1.0 for proportional gain, or we might need to scale it (e.g., gain * 2.0 or gain * 10.0).
            # Default FluidSynth gain is 0.2. Max is often 10.0.
            # Let's scale 0.0-1.0 to 0.0-2.0, as 1.0 might be too quiet if it's max.
            # A common master gain range for FluidSynth is 0.0 to 5.0 or 10.0.
            # Let's try scaling to 0.0-3.0, where 0.5 (50%) maps to 1.5.
            # FluidSynth's gain is a property, not a method.
            # The property range is 0.0-10.0, default 0.2.
            # Let's try mapping our 0.0-1.0 slider directly to this,
            # effectively using a smaller portion of the available gain range.
            # If 1.0 is too quiet, we can increase the multiplier.
            clamped_gain = max(0.0, min(1.0, gain))
            # Using the 0.0-1.0 value directly. If fs.gain expects 0.0-10.0, then 1.0 will be 10% of max.
            # This might be too quiet. Let's try scaling to a max of 2.0 for now.
            # Default is 0.2. 50% slider (0.5 input) -> 1.0 gain. 100% slider (1.0 input) -> 2.0 gain.
            # Let's try scaling to the full documented range of 0.0-10.0 for fs.gain.
            # Based on the user-provided attribute list, direct self.fs.gain is not available.
            # The dir(self.fs) shows a 'setting' method. This is likely the correct way.
            # The dir(self.fs.settings) output suggests self.fs.settings is not a settings object with methods.
            # User feedback: 50% slider (gain 5.0) is too loud.
            # Let's scale 0-1 slider input to 0.0-2.0 for "synth.gain".
            # So, 50% slider (0.5 input) will result in a gain of 1.0.
            actual_fs_gain = clamped_gain * 2.0 
            if hasattr(self.fs, 'setting'):
                try:
                    # The 'setting' method might be used for various types.
                    # For numerical settings, it usually takes name and value.
                    self.fs.setting("synth.gain", actual_fs_gain)
                    # print(f"FluidSynthPlayer: Called self.fs.setting('synth.gain', {actual_fs_gain})")
                except Exception as e:
                    print(f"FluidSynthPlayer: Error calling self.fs.setting('synth.gain', ...): {e}")
            else:
                print(f"FluidSynthPlayer: Could not set 'synth.gain'. self.fs.setting method not available.")
                # This else block should ideally not be reached if dir(self.fs) was accurate.
        else:
            print("FluidSynthPlayer: Cannot set gain, FluidSynth not initialized.")

    def cleanup(self):
        if self.fs:
            try:
                # Unload soundfont if loaded
                if self.soundfont_id is not None and self.soundfont_id != -1:
                    self.fs.sfunload(self.soundfont_id)
                self.fs.delete()
            except Exception as e:
                print(f"Error during FluidSynth cleanup: {e}")
            finally:
                self.fs = None
                self.soundfont_id = None

    def __del__(self):
        self.cleanup()

if __name__ == '__main__':
    # Basic test
    print(f"Attempting to use SoundFont: {SOUNDFONT_PATH}")
    if not os.path.exists(SOUNDFONT_PATH):
        print(f"CRITICAL: SoundFont file does not exist at the expected path: {SOUNDFONT_PATH}")
        print("Please ensure 'soundbank/soundfont.sf2' is in the project root.")
    
    player = FluidSynthPlayer()
    if player.fs and player.soundfont_id is not None:
        print("FluidSynthPlayer initialized. Testing playback...")
        import time
        
        # Test with default instrument (Program 0)
        player.set_instrument(0, DEFAULT_MIDI_PROGRAM) # EZ Pluck (Acoustic Grand Piano)
        print(f"Playing C4 (pitch 60) with default instrument (Program {DEFAULT_MIDI_PROGRAM})")
        player.noteon(0, 60, 100) # Channel 0, Pitch C4 (60), Velocity 100
        time.sleep(1)
        player.noteoff(0, 60)
        time.sleep(0.5)

        # Test with another instrument (Synth Lead - Program 80)
        SYNTH_LEAD_PROGRAM = 80
        player.set_instrument(0, SYNTH_LEAD_PROGRAM)
        print(f"Playing E4 (pitch 64) with Synth Lead (Program {SYNTH_LEAD_PROGRAM})")
        player.noteon(0, 64, 90) # Pitch E4 (64), Velocity 90
        time.sleep(1)
        player.noteoff(0, 64)
        time.sleep(0.5)
        
        # Test polyphony
        print("Testing polyphony (C4 and G4)")
        player.set_instrument(0, DEFAULT_MIDI_PROGRAM) # Back to piano
        player.noteon(0, 60, 100) # C4
        player.noteon(0, 67, 95)  # G4
        time.sleep(1.5)
        player.noteoff(0, 60)
        player.noteoff(0, 67)
        time.sleep(0.5)

        print("Test finished.")
    else:
        print("FluidSynthPlayer could not be initialized or soundfont not loaded. Playback test skipped.")
    
    player.cleanup()
    print("FluidSynthPlayer cleaned up.")
