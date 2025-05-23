import time
import threading
# import pygame.midi # pygame.midi might not be directly used if FluidSynth is primary
import pretty_midi # For Note object type hint
# from .device_manager import DeviceManager # DeviceManager might be less relevant for FluidSynth
from .note_scheduler import NoteScheduler
# from .midi_event_utils import send_all_notes_off # Will use FluidSynthPlayer's method
from .fluidsynth_player import FluidSynthPlayer # Import FluidSynthPlayer
from config.constants import DEFAULT_MIDI_PROGRAM, DEFAULT_MIDI_CHANNEL # For default instrument

class PlaybackController:
    """Controls MIDI playback, managing state, device, and note scheduling, now using FluidSynth."""

    def __init__(self):
        # self.device_manager = DeviceManager() # Pygame MIDI device manager
        self.fluidsynth_player = FluidSynthPlayer() # Initialize FluidSynth backend
        
        if not self.fluidsynth_player.fs: # Check if FluidSynth initialized successfully
            print("PlaybackController: FluidSynthPlayer failed to initialize. Playback will be unavailable.")
            # Handle fallback or disable playback features if necessary
        else:
            print("PlaybackController: FluidSynthPlayer initialized successfully.")

        self.notes = []
        self._is_playing_internal = False
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
        
        self.master_volume: float = 0.5 # Default volume 50% (0.0 to 1.0)

        # Set default instrument and initial volume on FluidSynthPlayer
        if self.fluidsynth_player and self.fluidsynth_player.fs:
            self.fluidsynth_player.set_instrument(DEFAULT_MIDI_CHANNEL, DEFAULT_MIDI_PROGRAM)
            if hasattr(self.fluidsynth_player, 'set_gain'):
                self.fluidsynth_player.set_gain(self.master_volume)
            else:
                if self.log_events: print("PlaybackController: FluidSynthPlayer does not have set_gain method.")


    def _ensure_scheduler(self):
        """Creates a NoteScheduler instance if one doesn't exist."""
        if not self.fluidsynth_player or not self.fluidsynth_player.fs:
            if self.log_events: print("PlaybackController: FluidSynthPlayer not available, cannot create scheduler.")
            self.note_scheduler = None
            return

        # Check if scheduler needs to be (re)created.
        # With FluidSynth, the "output device" is the fluidsynth_player instance itself.
        # So, we mainly check if the scheduler exists.
        if not self.note_scheduler:
            if self.log_events: print("PlaybackController: Creating NoteScheduler.")
            self.note_scheduler = NoteScheduler(
                notes=self.notes,
                player_backend=self.fluidsynth_player, # Pass FluidSynthPlayer instance
                get_current_time_func=self.get_current_position,
                tempo_scale_func=lambda: self.tempo_scale_factor,
                stop_flag=self.stop_flag,
                is_playing_flag=self._is_playing_for_scheduler
            )
            if self.log_events: print("PlaybackController: NoteScheduler created with FluidSynthPlayer.")
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
        if not self.note_scheduler or not self.fluidsynth_player or not self.fluidsynth_player.fs:
            if self.log_events: print("PlaybackController: Cannot play, scheduler or FluidSynthPlayer not available.")
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
            
            # Send all notes off when pausing using FluidSynthPlayer
            if self.fluidsynth_player and self.fluidsynth_player.fs:
                self.fluidsynth_player.all_notes_off()
                if self.log_events: print("PlaybackController: All notes off sent to FluidSynthPlayer on pause.")
        

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
        
        # Stop notes before seek, regardless of playing state, using FluidSynthPlayer
        if self.fluidsynth_player and self.fluidsynth_player.fs:
            self.fluidsynth_player.all_notes_off()
            if self.log_events: print("PlaybackController: All notes off sent to FluidSynthPlayer on seek.")

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

    def toggle_playback(self):
        """Toggles playback between play and pause."""
        if self.is_playing:
            if self.log_events: print("PlaybackController: Toggling playback (was playing, now pausing).")
            self.pause()
        else:
            # If it was paused, play will resume. If stopped, play will start from current_playback_time_sec (usually 0).
            if self.log_events: print("PlaybackController: Toggling playback (was not playing, now playing).")
            self.play()

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
        
        if self.fluidsynth_player:
            self.fluidsynth_player.cleanup()
            if self.log_events: print("PlaybackController: FluidSynthPlayer cleaned up.")
        
        # self.device_manager.close_device() # If DeviceManager was used for pygame.midi
        # pygame.midi.quit() # Main application should call this at the very end if pygame.midi was used.

    def set_instrument(self, program_num: int, channel: int = DEFAULT_MIDI_CHANNEL):
        """Sets the instrument for a given channel on the FluidSynthPlayer."""
        if self.fluidsynth_player and self.fluidsynth_player.fs:
            if self.log_events: 
                print(f"PlaybackController: Setting instrument to program {program_num} on channel {channel}.")
            self.fluidsynth_player.set_instrument(channel, program_num)
        else:
            if self.log_events:
                print("PlaybackController: Cannot set instrument, FluidSynthPlayer not available.")

    def set_master_volume(self, volume_float: float):
        """Sets the master volume for playback."""
        clamped_volume = max(0.0, min(1.0, volume_float))
        self.master_volume = clamped_volume
        
        if self.fluidsynth_player and self.fluidsynth_player.fs and hasattr(self.fluidsynth_player, 'set_gain'):
            if self.log_events:
                print(f"PlaybackController: Setting master volume to {self.master_volume:.2f}")
            self.fluidsynth_player.set_gain(self.master_volume)
        elif self.log_events:
            print("PlaybackController: Cannot set master volume, FluidSynthPlayer or set_gain method not available.")

    def __del__(self):
        self.cleanup()
