import pygame.midi
import pretty_midi # For note_number_to_name in logging, if desired

def send_note_on(output_device, pitch, velocity, channel=0, log=False):
    """Sends a MIDI note ON message."""
    if output_device:
        try:
            output_device.note_on(pitch, int(velocity), channel)
            if log:
                print(f"Note ON: {pretty_midi.note_number_to_name(pitch)} (P: {pitch}, V: {int(velocity)}, Ch: {channel})")
        except Exception as e:
            print(f"Error sending note on (P: {pitch}): {e}")

def send_note_off(output_device, pitch, velocity=0, channel=0, log=False):
    """Sends a MIDI note OFF message."""
    # Velocity for note off is often 0 or 64 (release velocity), but typically ignored by synths for note termination.
    if output_device:
        try:
            output_device.note_off(pitch, int(velocity), channel)
            if log:
                print(f"Note OFF: {pretty_midi.note_number_to_name(pitch)} (P: {pitch}, V: {int(velocity)}, Ch: {channel})")
        except Exception as e:
            print(f"Error sending note off (P: {pitch}): {e}")

def send_all_notes_off(output_device, log=False):
    """Sends All Notes Off messages on all channels and individual note offs."""
    if not output_device:
        if log: print("AllNotesOff: No output device.")
        return

    if log: print("Sending All Notes Off...")
    try:
        # Standard "All Notes Off" CC message for each channel
        for channel in range(16):
            # Controller 123 (0x7B) = All Notes Off
            output_device.write_short(0xB0 + channel, 123, 0)
        
        # Additionally, send explicit note_off for all pitches on channel 0 as a fallback
        # Some devices might not respond to CC 123 thoroughly.
        # for pitch in range(128):
        #     output_device.note_off(pitch, 0, 0) # Channel 0, velocity 0
            
        if log: print("All Notes Off messages sent.")
    except Exception as e:
        print(f"Error sending All Notes Off CC messages: {e}")

def send_panic(output_device, log=False):
    """More aggressive version of all notes off, includes all sound off."""
    if not output_device:
        if log: print("Panic: No output device.")
        return
    
    if log: print("Sending MIDI Panic (All Sound Off & All Notes Off)...")
    try:
        for channel in range(16):
            # Controller 120 (0x78) = All Sound Off
            output_device.write_short(0xB0 + channel, 120, 0) 
            # Controller 123 (0x7B) = All Notes Off
            output_device.write_short(0xB0 + channel, 123, 0)
        
        # Explicit note_off for all pitches on all channels
        # for channel in range(16):
        #     for pitch in range(128):
        #         output_device.note_off(pitch, 0, channel)
        if log: print("MIDI Panic messages sent.")
    except Exception as e:
        print(f"Error sending MIDI Panic messages: {e}")
