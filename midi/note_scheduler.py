import time
import threading
import pretty_midi # For logging note names
# midi_event_utils are no longer used directly by NoteScheduler for FluidSynth

# Assuming FluidSynthPlayer is in midi.fluidsynth_player
# from .fluidsynth_player import FluidSynthPlayer # Type hint, actual instance passed in

DEFAULT_MIDI_CHANNEL = 0 # For FluidSynth playback

class NoteScheduler:
    """Handles the timing and scheduling of MIDI note events for playback using a player backend."""

    def __init__(self, notes, player_backend, get_current_time_func, tempo_scale_func, stop_flag, is_playing_flag):
        self.notes = sorted(notes, key=lambda note: note.start) if notes else []
        self.player_backend = player_backend # This will be an instance of FluidSynthPlayer
        self.get_current_time = get_current_time_func
        self.get_tempo_scale = tempo_scale_func
        self.stop_flag = stop_flag
        self.is_playing_flag = is_playing_flag

        self.playback_thread = None
        self.notes_on = {}  # Tracks currently playing notes {note_index_in_sorted_list: (pitch, channel)}
        self.next_note_idx = 0
        self.log_events = True # Enable/disable MIDI event logging

    def start_playback_thread(self):
        if not self.notes:
            print("NoteScheduler: No notes to play.")
            if callable(self.is_playing_flag): # if it's a setter function
                self.is_playing_flag(False)
            else: # assume it's a mutable list/object [value]
                self.is_playing_flag[0] = False
            return

        if self.playback_thread is None or not self.playback_thread.is_alive():
            self.stop_flag.clear()
            # Reset playback state for the thread
            self.notes_on = {}
            self.next_note_idx = 0
            # Find the first note to play based on current time (e.g., if resuming or seeking)
            initial_current_time = self.get_current_time()
            while self.next_note_idx < len(self.notes) and \
                  self.notes[self.next_note_idx].start < initial_current_time:
                # If a note should have started but also ended before current time, skip it.
                # Otherwise, if it should have started and is still ongoing, it should be turned on.
                # This logic can be complex for robust resume/seek. For now, simple advance.
                self.next_note_idx += 1
            
            self.playback_thread = threading.Thread(target=self._run_schedule)
            self.playback_thread.daemon = True
            self.playback_thread.start()
            if self.log_events:
                print(f"NoteScheduler: Playback thread started. First note index: {self.next_note_idx}")
        else:
            if self.log_events: print("NoteScheduler: Playback thread already running.")


    def _run_schedule(self):
        if self.log_events:
            print(f"NoteScheduler: _run_schedule entered. Notes: {len(self.notes)}")
            if self.notes:
                print(f"NoteScheduler: First note: P{self.notes[0].pitch} S{self.notes[0].start} E{self.notes[0].end}")

        if not self.player_backend: # Check player_backend instead of output_device
            print("NoteScheduler: No player backend available for playback.")
            if callable(self.is_playing_flag): self.is_playing_flag(False)
            else: self.is_playing_flag[0] = False
            return

        try:
            while not self.stop_flag.is_set():
                # Check if is_playing_flag (which might be a function call or list access) is false
                is_playing_check = self.is_playing_flag() if callable(self.is_playing_flag) else self.is_playing_flag[0]
                if not is_playing_check: # If playback was paused/stopped externally
                    time.sleep(0.01) # Sleep briefly and re-check
                    continue

                current_time = self.get_current_time()

                # Process note-offs
                notes_to_remove_from_on = []
                for note_idx, (pitch, channel) in list(self.notes_on.items()): # Use list for safe iteration
                    note = self.notes[note_idx] # Original note object for end time
                    if current_time >= note.end:
                        self.player_backend.noteoff(channel, pitch)
                        if self.log_events:
                            print(f"Note OFF: {pretty_midi.note_number_to_name(pitch)} (P: {pitch}, Ch: {channel}) sent to backend.")
                        notes_to_remove_from_on.append(note_idx)
                
                for note_idx in notes_to_remove_from_on:
                    if note_idx in self.notes_on: # Check if still exists (can be cleared by stop)
                        del self.notes_on[note_idx]

                # Process note-ons
                while (self.next_note_idx < len(self.notes) and
                       current_time >= self.notes[self.next_note_idx].start):
                    note = self.notes[self.next_note_idx]
                    # Check if this note is already "on" from a previous iteration (e.g. due to very short sleep or fast tempo)
                    # This check is more relevant if notes_on stores a boolean. Here it stores start time.
                    # The main check is `current_time < note.end`.
                    if current_time < note.end and self.next_note_idx not in self.notes_on:
                        # Use default channel for now, instrument selection is separate
                        channel_to_use = DEFAULT_MIDI_CHANNEL 
                        self.player_backend.noteon(channel_to_use, note.pitch, note.velocity)
                        if self.log_events:
                            print(f"Note ON: {pretty_midi.note_number_to_name(note.pitch)} (P: {note.pitch}, V: {note.velocity}, Ch: {channel_to_use}) sent to backend.")
                        self.notes_on[self.next_note_idx] = (note.pitch, channel_to_use)
                    self.next_note_idx += 1
                
                # If all notes have been scheduled and all playing notes have ended
                if self.next_note_idx >= len(self.notes) and not self.notes_on:
                    if self.log_events: print("NoteScheduler: All notes played.")
                    if callable(self.is_playing_flag): self.is_playing_flag(False) # Signal end of playback
                    else: self.is_playing_flag[0] = False
                    break 

                tempo_scale = self.get_tempo_scale()
                sleep_duration = min(0.01, 0.005 / max(0.1, tempo_scale)) # Ensure tempo_scale isn't too small
                time.sleep(sleep_duration)

        except Exception as e:
            print(f"NoteScheduler: Error in playback loop: {e}")
        finally:
            # Ensure all notes are turned off when the thread exits or is stopped
            if self.player_backend:
                self.player_backend.all_notes_off() # Use backend's all_notes_off
                if self.log_events: print("NoteScheduler: All notes off sent to backend via player_backend.")
            if self.log_events: print("NoteScheduler: Playback thread finished.")
            # Do not set is_playing_flag to False here if stop_flag was the cause,
            # as the main controller should handle that. Only if playback naturally ends.


    def stop_playback_thread(self):
        self.stop_flag.set()
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=0.5) # Wait briefly for thread to exit
        self.playback_thread = None
        # Crucially, turn off any lingering notes if the backend is still valid
        if self.player_backend:
            self.player_backend.all_notes_off() # Use backend's all_notes_off
            if self.log_events: print("NoteScheduler: All notes off sent to backend on explicit stop.")
        if self.log_events: print("NoteScheduler: Playback thread explicitly stopped.")

    def update_notes(self, notes):
        """Updates the notes for the scheduler. Playback should be stopped before calling this."""
        if self.playback_thread and self.playback_thread.is_alive():
            print("NoteScheduler: Warning - updating notes while playback thread is active. Stop playback first.")
            self.stop_playback_thread() # Ensure it's stopped
            
        self.notes = sorted(notes, key=lambda note: note.start) if notes else []
        self.next_note_idx = 0
        self.notes_on = {}
        if self.log_events: print(f"NoteScheduler: Notes updated. Count: {len(self.notes)}")

    def reset_playback_position(self, position_seconds=0.0):
        """Resets the scheduler's internal pointers to a given time, typically 0."""
        self.next_note_idx = 0
        while self.next_note_idx < len(self.notes) and \
              self.notes[self.next_note_idx].start < position_seconds:
            self.next_note_idx += 1
        self.notes_on = {} # Clear any tracked 'on' notes
        if self.log_events: print(f"NoteScheduler: Playback position reset to {position_seconds}s. Next note index: {self.next_note_idx}")
