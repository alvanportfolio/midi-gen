import time
import threading
import pygame.midi # For init/quit, though DeviceManager also handles init
import pretty_midi # For Note object type hint
from .device_manager import DeviceManager
from .note_scheduler import NoteScheduler
from .midi_event_utils import send_all_notes_off # For an explicit stop

class PlaybackController:
    """Controls MIDI playback, managing state, device, and note scheduling."""

    def __init__(self):
        # pygame.midi.init() # DeviceManager will handle this
        self.device_manager = DeviceManager()
        
        self.notes = []
        self._is_playing_internal = False # Actual state of playback for scheduler
        self.paused = False
        self.current_playback_time_sec = 0.0 # Time from start of current playback segment
        self.playback_start_real_time = 0.0  # time.time() when playback (re)started
        self.pause_start_time_sec = 0.0 # Stores current_playback_time_sec when paused

        self.tempo_bpm = 120.0
        self.tempo_scale_factor = 1.0 # (current_bpm / 120.0)

        self.stop_flag = threading.Event()
        
        # The NoteScheduler needs a way to know if it should be actively processing.
        # We pass a list containing our internal playing state.
        self._is_playing_for_scheduler = [self._is_playing_internal] 
        
        # Scheduler is created when notes are set, or on first play
        self.note_scheduler = None
        self.log_events = True # For debugging

    def _ensure_scheduler(self):
        """Creates a NoteScheduler instance if one doesn't exist or if output device changed."""
        output_dev = self.device_manager.get_output_device()
        if not self.note_scheduler or self.note_scheduler.output_device != output_dev:
            if self.note_scheduler: # If exists, stop its thread before replacing
                 self.note_scheduler.stop_playback_thread()
            
            if output_dev:
                self.note_scheduler = NoteScheduler(
                    notes=self.notes,
                    output_device=output_dev,
                    get_current_time_func=self.get_current_position,
                    tempo_scale_func=lambda: self.tempo_scale_factor,
                    stop_flag=self.stop_flag,
                    is_playing_flag=self._is_playing_for_scheduler # Pass the mutable list
                )
                if self.log_events: print("PlaybackController: NoteScheduler created/recreated.")
            else:
                self.note_scheduler = None
                if self.log_events: print("PlaybackController: Failed to create NoteScheduler, no output device.")
        elif self.note_scheduler:
             # If scheduler exists, ensure its notes are current
             self.note_scheduler.update_notes(self.notes)


    def set_notes(self, notes: list[pretty_midi.Note]):
        if self.log_events: print(f"PlaybackController: Setting {len(notes)} notes.")
        self.stop() # Stop current playback before changing notes
        self.notes = notes if notes else []
        self.current_playback_time_sec = 0.0
        self.pause_start_time_sec = 0.0
        if self.note_scheduler:
            self.note_scheduler.update_notes(self.notes)
            self.note_scheduler.reset_playback_position(0.0)
        else:
            self._ensure_scheduler() # Create scheduler if it wasn't there

    def play(self):
        if self.log_events: print(f"PlaybackController: Play called. Currently playing: {self._is_playing_internal}, Paused: {self.paused}")
        if not self.notes:
            if self.log_events: print("PlaybackController: No notes to play.")
            return

        self._ensure_scheduler()
        if not self.note_scheduler or not self.note_scheduler.output_device:
            if self.log_events: print("PlaybackController: Cannot play, scheduler or output device not available.")
            return

        if self._is_playing_internal and not self.paused: # Already playing
            return

        self.stop_flag.clear()
        self._is_playing_internal = True
        self._is_playing_for_scheduler[0] = True # Update shared flag for scheduler

        if self.paused: # Resuming
            # Adjust start time to account for pause duration
            self.playback_start_real_time = time.time() - self.pause_start_time_sec / self.tempo_scale_factor
            self.paused = False
            if self.log_events: print(f"PlaybackController: Resuming from {self.pause_start_time_sec:.2f}s.")
        else: # Starting new or from a seek
            self.playback_start_real_time = time.time() - self.current_playback_time_sec / self.tempo_scale_factor
            self.note_scheduler.reset_playback_position(self.current_playback_time_sec)
            if self.log_events: print(f"PlaybackController: Starting playback from {self.current_playback_time_sec:.2f}s.")
        
        self.note_scheduler.start_playback_thread()


    def pause(self):
        if self.log_events: print("PlaybackController: Pause called.")
        if self._is_playing_internal and not self.paused:
            self.paused = True
            self._is_playing_internal = False # Stop the scheduler's active loop
            self._is_playing_for_scheduler[0] = False
            # self.note_scheduler.stop_playback_thread() # Not stopping thread, just pausing its activity
            
            self.pause_start_time_sec = self.get_current_position() # Store accurate pause time
            if self.log_events: print(f"PlaybackController: Paused at {self.pause_start_time_sec:.2f}s.")
            
            # Send all notes off when pausing
            if self.note_scheduler and self.note_scheduler.output_device:
                send_all_notes_off(self.note_scheduler.output_device, self.log_events)
        

    def stop(self):
        if self.log_events: print("PlaybackController: Stop called.")
        self._is_playing_internal = False
        self._is_playing_for_scheduler[0] = False
        self.paused = False
        
        if self.note_scheduler:
            self.note_scheduler.stop_playback_thread() # This will also send all notes off
        
        self.current_playback_time_sec = 0.0
        self.pause_start_time_sec = 0.0
        if self.note_scheduler: # Reset scheduler's internal state too
            self.note_scheduler.reset_playback_position(0.0)


    def seek(self, position_sec: float):
        if self.log_events: print(f"PlaybackController: Seek to {position_sec:.2f}s.")
        
        # Stop notes before seek, regardless of playing state
        if self.note_scheduler and self.note_scheduler.output_device:
             send_all_notes_off(self.note_scheduler.output_device, self.log_events)

        self.current_playback_time_sec = max(0.0, position_sec)
        self.pause_start_time_sec = self.current_playback_time_sec # If paused, resume from here

        if self.note_scheduler:
            self.note_scheduler.reset_playback_position(self.current_playback_time_sec)

        # If it was playing, need to restart the thread from the new position
        # or if paused, update the resume point.
        if self._is_playing_internal or self.paused:
            self.playback_start_real_time = time.time() - self.current_playback_time_sec / self.tempo_scale_factor
            if self._is_playing_internal and not self.paused and self.note_scheduler: # Was playing, restart thread
                # self.note_scheduler.stop_playback_thread() # Stop existing - handled by start_playback_thread if needed
                self.note_scheduler.start_playback_thread() # Start new from current pos
        
        if self.log_events: print(f"PlaybackController: Seek complete. Current time: {self.current_playback_time_sec:.2f}s")


    def get_current_position(self) -> float:
        if self._is_playing_internal and not self.paused:
            elapsed_real_time = time.time() - self.playback_start_real_time
            self.current_playback_time_sec = elapsed_real_time * self.tempo_scale_factor
            return self.current_playback_time_sec
        elif self.paused:
            return self.pause_start_time_sec 
        return self.current_playback_time_sec # Stopped or not yet played

    @property
    def is_playing(self) -> bool:
        # This property reflects if the controller *thinks* it should be playing,
        # which might differ slightly from the scheduler thread's instantaneous state.
        return self._is_playing_internal and not self.paused

    def set_tempo(self, bpm: float):
        if bpm <= 0:
            if self.log_events: print("PlaybackController: BPM must be positive.")
            return
        
        if self.log_events: print(f"PlaybackController: Setting tempo to {bpm} BPM.")
        
        current_pos_before_tempo_change = self.get_current_position()
        
        self.tempo_bpm = float(bpm)
        self.tempo_scale_factor = self.tempo_bpm / 120.0
        
        # Adjust start time to maintain current logical position with new tempo
        if self._is_playing_internal or self.paused:
             self.playback_start_real_time = time.time() - (current_pos_before_tempo_change / self.tempo_scale_factor)
        
        if self.log_events: print(f"PlaybackController: Tempo scale factor: {self.tempo_scale_factor}")

    def cleanup(self):
        """Clean up resources, especially the MIDI device."""
        if self.log_events: print("PlaybackController: Cleanup called.")
        self.stop() # Ensure playback is stopped and thread joined
        self.device_manager.close_device()
        # pygame.midi.quit() # Main application should call this at the very end.

    def __del__(self):
        self.cleanup()
