import pygame.midi
import time # For device test delay

class DeviceManager:
    """Manages MIDI output device selection and access."""
    def __init__(self):
        if not pygame.midi.get_init():
            print("🎹 Initializing pygame.midi...")
            pygame.midi.init()
            
            # ===== MIDI DEVICE SETTLING DELAY =====
            # Add delay after pygame.midi.init to allow MIDI subsystem to settle
            print("🔇 Pygame MIDI initialized, allowing MIDI subsystem to settle...")
            time.sleep(0.1)
        
        self.output_id = self._get_default_output_id()
        self._log_midi_devices()
        self.output_device = None

    def _log_midi_devices(self):
        device_count = pygame.midi.get_count()
        print(f"Found {device_count} MIDI devices:")
        for i in range(device_count):
            info = pygame.midi.get_device_info(i)
            if info: # Check if info is not None
                name = info[1].decode('utf-8') if info[1] else "Unknown Device"
                is_input = info[2]
                is_output = info[3]
                print(f"  Device {i}: {name}, Input: {is_input}, Output: {is_output}")
            else:
                print(f"  Device {i}: Could not retrieve info.")
        print(f"Selected output ID: {self.output_id}")

    def _get_default_output_id(self):
        device_count = pygame.midi.get_count()
        if device_count == 0:
            print("No MIDI devices found!")
            return -1

        # Try to find Microsoft GS Wavetable Synth first
        for i in range(device_count):
            info = pygame.midi.get_device_info(i)
            if info and info[3] and info[1]: # is_output and name exists
                name = info[1].decode('utf-8').lower()
                if 'microsoft gs wavetable' in name:
                    print(f"Selected Microsoft GS Wavetable Synth: ID {i}")
                    return i
        
        # Fallback: Find the first available output device
        for i in range(device_count):
            info = pygame.midi.get_device_info(i)
            if info and info[3]: # is_output
                print(f"Selected first available output device: ID {i} ({info[1].decode('utf-8') if info[1] else 'N/A'})")
                return i
        
        # Fallback to pygame's default output ID if any
        try:
            default_id = pygame.midi.get_default_output_id()
            if default_id != -1:
                print(f"Selected pygame default output device: ID {default_id}")
                return default_id
        except pygame.midi.MidiException: # Catch if no default output
            pass
        except Exception as e: # Catch other potential errors
            print(f"Error getting default MIDI output ID: {e}")

        print("No suitable output MIDI device found.")
        return -1

    def open_device(self):
        """Opens the selected MIDI output device."""
        if self.output_id < 0:
            print("Cannot open MIDI device: No output ID selected.")
            return None
        
        if self.output_device and self.output_device.opened:
             # It seems pygame.midi.Output doesn't have an 'opened' attribute.
             # We'll rely on re-opening or assume it's fine if already instantiated.
             # For safety, close if it exists and re-open.
            try:
                self.output_device.close()
            except: pass # Ignore errors if already closed or invalid state
            self.output_device = None

        try:
            self.output_device = pygame.midi.Output(self.output_id)
            print(f"Successfully opened MIDI output device ID: {self.output_id}")
            # Optional: Test the device
            # self.test_device() 
            return self.output_device
        except Exception as e:
            print(f"Error opening MIDI output device ID {self.output_id}: {e}")
            # Attempt to find and use Microsoft GS Wavetable Synth as a fallback
            print("Attempting to use Microsoft GS Wavetable Synth as fallback...")
            original_id = self.output_id
            ms_synth_id = -1
            device_count = pygame.midi.get_count()
            for i in range(device_count):
                info = pygame.midi.get_device_info(i)
                if info and info[3] and info[1]:
                    name = info[1].decode('utf-8').lower()
                    if 'microsoft gs wavetable' in name:
                        ms_synth_id = i
                        break
            if ms_synth_id != -1 and ms_synth_id != original_id:
                print(f"Found Microsoft GS Wavetable Synth at ID {ms_synth_id}. Trying it.")
                try:
                    self.output_id = ms_synth_id
                    self.output_device = pygame.midi.Output(self.output_id)
                    print(f"Successfully opened fallback MIDI output device ID: {self.output_id}")
                    return self.output_device
                except Exception as e2:
                    print(f"Error opening fallback MIDI output device ID {self.output_id}: {e2}")
                    self.output_id = original_id # Revert if fallback failed
            self.output_device = None
            return None

    def test_device(self):
        if self.output_device:
            try:
                print("Testing MIDI output with a C4 note...")
                self.output_device.note_on(60, 100, 0)  # Middle C, velocity 100, channel 0
                time.sleep(0.2)
                self.output_device.note_off(60, 0, 0)
                print("Test note sent.")
            except Exception as e:
                print(f"Error during MIDI device test: {e}")
        else:
            print("Cannot test MIDI device: Not open.")


    def close_device(self):
        """Closes the MIDI output device if it's open."""
        if self.output_device:
            try:
                # Send all notes off before closing
                for channel in range(16):
                    self.output_device.write_short(0xB0 + channel, 123, 0) # All notes off
                for pitch in range(128):
                     self.output_device.note_off(pitch, 0, 0)

                self.output_device.close()
                print(f"Closed MIDI output device ID: {self.output_id}")
            except Exception as e:
                print(f"Error closing MIDI device: {e}")
            finally:
                self.output_device = None
    
    def get_output_device(self):
        """Returns the currently opened output device, attempting to open if closed."""
        if not self.output_device: # or not self.output_device.opened (if attribute existed)
            return self.open_device()
        return self.output_device

    def __del__(self):
        self.close_device()
        # pygame.midi.quit() # Let the main application decide when to quit pygame.midi
