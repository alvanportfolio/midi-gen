import fluidsynth
import os
import sys
import time
import threading
import inspect # For inspect.getfile
import platform
from config.constants import DEFAULT_MIDI_PROGRAM
from utils import get_resource_path # Import the new helper

# Default SoundFont path relative to project root
DEFAULT_SOUNDFONT_RELATIVE_PATH = "soundbank/soundfont.sf2"

def setup_fluidsynth_library_path():
    """
    Setup FluidSynth library path for different platforms after PyInstaller build.
    
    Platform-specific setup:
    Windows: Add bundled FluidSynth bin directory to PATH
    macOS: Set DYLD_LIBRARY_PATH or use bundled libraries
    Linux: Set LD_LIBRARY_PATH or use bundled libraries
    """
    current_platform = platform.system().lower()
    
    # Check if we're running as a PyInstaller bundle
    if hasattr(sys, 'frozen'):
        # Running as PyInstaller executable
        if current_platform == "windows":
            # For Windows standalone: Add bundled FluidSynth bin to PATH
            fluidsynth_bin_path = get_resource_path("fluidsynth/bin")
            if os.path.exists(fluidsynth_bin_path):
                current_path = os.environ.get('PATH', '')
                if fluidsynth_bin_path not in current_path:
                    os.environ['PATH'] = fluidsynth_bin_path + os.pathsep + current_path
                    print(f"✅ Added FluidSynth bin path to PATH: {fluidsynth_bin_path}")
            else:
                print(f"⚠️ FluidSynth bin directory not found at: {fluidsynth_bin_path}")
                
        elif current_platform == "darwin":  # macOS
            # For macOS standalone: Set library path for bundled FluidSynth
            fluidsynth_lib_path = get_resource_path("fluidsynth/lib")
            if os.path.exists(fluidsynth_lib_path):
                current_dyld_path = os.environ.get('DYLD_LIBRARY_PATH', '')
                if fluidsynth_lib_path not in current_dyld_path:
                    os.environ['DYLD_LIBRARY_PATH'] = fluidsynth_lib_path + os.pathsep + current_dyld_path
                    print(f"✅ Added FluidSynth lib path to DYLD_LIBRARY_PATH: {fluidsynth_lib_path}")
            else:
                print(f"⚠️ FluidSynth lib directory not found at: {fluidsynth_lib_path}")
                
        elif current_platform == "linux":
            # For Linux standalone: Set library path for bundled FluidSynth
            fluidsynth_lib_path = get_resource_path("fluidsynth/lib")
            if os.path.exists(fluidsynth_lib_path):
                current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
                if fluidsynth_lib_path not in current_ld_path:
                    os.environ['LD_LIBRARY_PATH'] = fluidsynth_lib_path + os.pathsep + current_ld_path
                    print(f"✅ Added FluidSynth lib path to LD_LIBRARY_PATH: {fluidsynth_lib_path}")
            else:
                print(f"⚠️ FluidSynth lib directory not found at: {fluidsynth_lib_path}")
    else:
        # Development mode - libraries should be in system PATH or project fluidsynth folder
        print("🔧 Development mode: Ensure FluidSynth is installed on system or in project fluidsynth folder")

class FluidSynthPlayer:
    def __init__(self, soundfont_path_str: str | None = None): # Allow passing a specific path
        # Setup platform-specific library paths
        setup_fluidsynth_library_path()
        
        self.fs = None
        self.soundfont_id = None
        self._current_gain = 0.0  # Start with zero gain for fade-in
        self._target_gain = 1.0   # Target gain after fade-in
        self._fade_in_completed = False
        
        # Determine the soundfont path to use
        if soundfont_path_str:
            self.soundfont_path = soundfont_path_str
        else:
            self.soundfont_path = get_resource_path(DEFAULT_SOUNDFONT_RELATIVE_PATH)

        try:
            # Print the path of the imported fluidsynth module for diagnostics
            print(f"Attempting to use fluidsynth module from: {inspect.getfile(fluidsynth)}")
            
            # Platform-specific initialization warnings
            current_platform = platform.system().lower()
            if current_platform == "windows":
                print("🔊 Windows: Using DirectSound or WASAPI audio driver")
            elif current_platform == "darwin":
                print("🔊 macOS: Using CoreAudio driver")
            elif current_platform == "linux":
                print("🔊 Linux: Using ALSA or PulseAudio driver")
            
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
            
            # ===== AUDIO DEVICE SETTLING DELAY =====
            # Add delay after FluidSynth start to allow audio device to settle
            print("🔇 FluidSynth started, allowing audio device to settle...")
            time.sleep(0.1)

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
                    
                    # ===== FADE-IN INITIALIZATION =====
                    # Initialize with zero gain and start fade-in to prevent audio pops
                    print("🎵 Starting FluidSynth fade-in...")
                    self._initialize_silent_startup()

        except ImportError as e:
            print(f"FluidSynth library not found: {e}")
            print(self._get_platform_install_instructions())
            self.fs = None
            self.soundfont_id = None
        except Exception as e:
            print(f"Failed to initialize FluidSynth: {e}")
            print("MIDI playback via FluidSynth will not be available.")
            if self.fs:
                self.fs.delete()
            self.fs = None
            self.soundfont_id = None

    def _get_platform_install_instructions(self):
        """Return platform-specific installation instructions for FluidSynth."""
        current_platform = platform.system().lower()
        
        if current_platform == "windows":
            return """
📋 Windows FluidSynth Setup Instructions:
For STANDALONE BUILDS:
1. Ensure 'fluidsynth' folder with bin/, lib/, include/ is next to your .exe
2. The 'fluidsynth/bin' folder should contain:
   - libfluidsynth-3.dll
   - All dependency DLLs (SDL3.dll, sndfile.dll, etc.)

For DEVELOPMENT:
1. Install FluidSynth: Download from https://github.com/FluidSynth/fluidsynth/releases
2. Add FluidSynth bin directory to your PATH
3. Or copy FluidSynth DLLs to your project's fluidsynth/bin folder
            """
        elif current_platform == "darwin":
            return """
📋 macOS FluidSynth Setup Instructions:
For STANDALONE BUILDS:
1. Ensure 'fluidsynth' folder with lib/ is next to your .app bundle
2. The 'fluidsynth/lib' folder should contain:
   - libfluidsynth.dylib (or libfluidsynth.3.dylib)
   - All dependency dylibs

For DEVELOPMENT:
1. Install FluidSynth via Homebrew: brew install fluid-synth
2. Or download from https://github.com/FluidSynth/fluidsynth/releases
3. Or copy FluidSynth dylibs to your project's fluidsynth/lib folder

For Homebrew users, FluidSynth is typically at:
- Intel Macs: /usr/local/opt/fluid-synth/lib/
- Apple Silicon: /opt/homebrew/opt/fluid-synth/lib/
            """
        elif current_platform == "linux":
            return """
📋 Linux FluidSynth Setup Instructions:
For STANDALONE BUILDS:
1. Ensure 'fluidsynth' folder with lib/ is next to your executable
2. The 'fluidsynth/lib' folder should contain:
   - libfluidsynth.so.3 (or libfluidsynth.so)
   - All dependency .so files

For DEVELOPMENT:
1. Install FluidSynth via package manager:
   - Ubuntu/Debian: sudo apt install libfluidsynth-dev libfluidsynth3
   - CentOS/RHEL: sudo yum install fluidsynth-devel
   - Arch: sudo pacman -S fluidsynth
2. Or copy FluidSynth .so files to your project's fluidsynth/lib folder
            """
        else:
            return f"Unknown platform: {current_platform}. Please install FluidSynth manually."

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
            clamped_gain = max(0.0, min(1.0, gain))
            self._target_gain = clamped_gain
            
            # If fade-in is complete, set gain immediately
            # If fade-in is in progress, it will use the new target
            if self._fade_in_completed:
                actual_fs_gain = clamped_gain * 2.0  # Scale for FluidSynth
                if hasattr(self.fs, 'setting'):
                    try:
                        self.fs.setting("synth.gain", actual_fs_gain)
                        self._current_gain = clamped_gain
                    except Exception as e:
                        print(f"FluidSynthPlayer: Error calling self.fs.setting('synth.gain', ...): {e}")
                else:
                    print(f"FluidSynthPlayer: Could not set 'synth.gain'. self.fs.setting method not available.")
        else:
            print("FluidSynthPlayer: Cannot set gain, FluidSynth not initialized.")

    def _initialize_silent_startup(self):
        """Initialize FluidSynth with zero gain and perform fade-in to prevent audio pops."""
        if self.fs:
            try:
                # Set initial gain to 0 to prevent pops
                self.fs.setting("synth.gain", 0.0)
                self._current_gain = 0.0
                print("🔇 FluidSynth gain set to 0 for silent startup")
                
                # Start fade-in in background thread
                fade_thread = threading.Thread(target=self._perform_fade_in, daemon=True)
                fade_thread.start()
                
            except Exception as e:
                print(f"Error during silent startup initialization: {e}")
                # If fade-in fails, just set normal gain directly
                self._fade_in_completed = True
                try:
                    self.fs.setting("synth.gain", self._target_gain * 2.0)
                except:
                    pass

    def _perform_fade_in(self):
        """Gradually increase gain from 0 to target over ~100ms to prevent audio pops."""
        try:
            fade_duration = 0.1  # 100ms
            fade_steps = 20
            step_duration = fade_duration / fade_steps
            gain_increment = self._target_gain / fade_steps
            
            for step in range(fade_steps + 1):
                if not self.fs:  # Check if FluidSynth was destroyed during fade
                    break
                    
                current_step_gain = min(step * gain_increment, self._target_gain)
                actual_fs_gain = current_step_gain * 2.0  # Scale for FluidSynth
                
                try:
                    self.fs.setting("synth.gain", actual_fs_gain)
                    self._current_gain = current_step_gain
                except:
                    break  # Exit if setting fails
                    
                time.sleep(step_duration)
            
            self._fade_in_completed = True
            print("✅ FluidSynth fade-in completed")
            
        except Exception as e:
            print(f"Error during fade-in: {e}")
            self._fade_in_completed = True

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
