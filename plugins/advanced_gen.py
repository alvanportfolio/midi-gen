import random
import math
import pretty_midi
from plugin_api import PluginBase

class AdvancedGEN(PluginBase):
    """
    Advanced Rhythmic and Melodic Generator (AdvancedGEN)
    Creates complex rhythmic patterns with melodic content based on various parameters.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "AdvancedGEN"
        self.description = "Generates advanced rhythmic and melodic sequences."
        self.author = "Cline"
        self.version = "1.0"
        
        self.parameters = {
            "num_bars": {
                "type": "int", "min": 1, "max": 16, "default": 4,
                "description": "Number of bars to generate."
            },
            "bpm": {
                "type": "int", "min": 40, "max": 240, "default": 120,
                "description": "Beats per minute (for calculating note durations)."
            },
            "root_note_name": { # Changed from root_note (int)
                "type": "list",
                "options": ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
                "default": "C",
                "description": "Root note of the scale."
            },
            "root_octave": { 
                "type": "int", "min": 1, "max": 7, "default": 5, # Default to 5 (so C5 = MIDI 60, Middle C)
                "description": "Octave for the root note (C5=MIDI 60 is Middle C)."
            },
            "scale_type": {
                "type": "list", 
                "options": ["Major", "Minor (Natural)", "Dorian", "Mixolydian", "Lydian", "Phrygian", "Locrian", 
                            "Minor (Harmonic)", "Minor (Melodic)", "Chromatic", "Pentatonic Major", "Pentatonic Minor", "Blues"],
                "default": "Major",
                "description": "Musical scale/mode to use."
            },
            "melodic_contour_shape": { # Added
                "type": "list",
                "options": ["Random Walk", "Smooth Random Walk", "Rising", "Falling", "Wave", "Valley", "Mountain", "Static"],
                "default": "Smooth Random Walk",
                "description": "Overall melodic shape or contour."
            },
            "octave_span": { # Renamed from octave_range for clarity
                "type": "int", "min": 1, "max": 5, "default": 2,
                "description": "Number of octaves the melody can span around the root."
            },
            "rhythm_pattern_type": {
                "type": "list",
                "options": ["Euclidean", "Density-Based", "Fixed Pattern"],
                "default": "Density-Based",
                "description": "Method for generating the base rhythm."
            },
            "euclidean_pulses": {
                "type": "int", "min": 1, "max": 32, "default": 5,
                "description": "Pulses for Euclidean rhythm (if selected)."
            },
            "euclidean_steps": {
                "type": "int", "min": 2, "max": 32, "default": 8,
                "description": "Steps for Euclidean rhythm (if selected)."
            },
            "rhythm_density": { # For Density-Based
                "type": "float", "min": 0.1, "max": 1.0, "default": 0.6,
                "description": "Overall density of notes (0.1-1.0)."
            },
            "syncopation_factor": { # General syncopation modifier
                "type": "float", "min": 0.0, "max": 1.0, "default": 0.3,
                "description": "Likelihood/amount of syncopation (0.0-1.0)."
            },
            "base_subdivision": {
                "type": "list", "options": ["16th", "8th", "Triplet 8th", "Triplet 16th"],
                "default": "16th",
                "description": "Smallest rhythmic unit."
            },
            "note_duration_type": {
                "type": "list", "options": ["Fixed", "Varied", "Legato"],
                "default": "Varied",
                "description": "How note durations are determined."
            },
            "fixed_note_duration": { # if note_duration_type is Fixed
                "type": "float", "min": 0.05, "max": 4.0, "default": 0.25, 
                "description": "Fixed duration in beats (if Note Duration Type is Fixed)."
            },
            "humanization_amount": { # Added
                "type": "float", "min": 0.0, "max": 1.0, "default": 0.1,
                "description": "Amount of humanization for timing, velocity, duration (0=none)."
            },
            "random_seed": {
                "type": "int", "min": 0, "max": 999999, "default": 0,
                "description": "Seed for random number generator (0 for random)."
            }
        }

    def _get_midi_note_from_name(self, note_name_str: str, octave_val: int) -> int:
        """Converts note name (e.g., 'C#') and octave to a MIDI pitch number."""
        note_map = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
        base_pitch = note_map.get(note_name_str.upper(), 0) # Default to C if name is wrong
        # Assuming octave 0 = C0 (MIDI pitch 0), so C4 = 60.
        # pretty_midi C4 is 60. MIDI standard: C0=0, C1=12, C2=24, C3=36, C4=48, C5=60.
        # Let's adjust so user octave 4 means C4=60.
        # MIDI pitch = 12 * (octave + 1) + base_pitch (if C0 is octave 0)
        # If user octave 4 = C4 (MIDI 60), then MIDI pitch = 12 * octave + base_pitch
        # Example: C, octave 4 -> 12*4 + 0 = 48. This is C3 in pretty_midi.
        # To make user octave 4 = C4 (MIDI 60), we need: 12 * (user_octave - K) + base_pitch = MIDI_pitch
        # For C4 (MIDI 60), if user_octave=4, base_pitch=0: 12 * 4 + 0 = 48. This is standard MIDI C4.
        # pretty_midi uses C4=60. So, if user says octave 4, it should map to the 4th octave where C is 60.
        # MIDI standard: C0=0, C1=12, ..., C4=48, C5=60.
        # If user 'octave 4' means the octave where C is 60 (C5 in standard MIDI, C4 in Yamaha/some DAWs)
        # Let's assume user 'octave 4' means the octave containing middle C (MIDI 60).
        # So, if root_note_name is 'C' and root_octave is 4, target_midi_pitch = 60.
        # base_pitch for C is 0.  So, 60 = 12 * X + 0. X = 5. So, MIDI_octave = user_octave + 1.
        # MIDI pitch = 12 * (octave_val + 1) + base_pitch is a common way if octave 0 is the lowest.
        # Let's use: MIDI pitch = (octave_val * 12) + base_pitch. This makes C0=0, C1=12, C4=48, C5=60.
        # If user wants octave 4 to be where C is 60, then they should input octave 5.
        # To avoid confusion, let's map user octave 4 to MIDI C4 (48), and let them use higher octaves.
        # Or, map user octave 4 to MIDI C5 (60) as "middle C reference".
        # The parameter description says "C4 is middle C if octave 0 is C0". MIDI 60 is C4 in pretty_midi.
        # So, (octave_val * 12) + base_pitch. If C, octave 4 -> 48. If C, octave 5 -> 60.
        # The parameter default is octave 4, root C, expecting MIDI 60. So, we need to adjust.
        # If default root_octave=4 and root_note_name="C" should be MIDI 60:
        # MIDI_pitch = 12 * (octave_val - 1) + base_pitch + 12 (for C0 being 0)
        # Or simply: (octave_val * 12) + base_pitch, and adjust default octave to 5 for C4=60.
        # Let's keep it simple: (octave_val * 12) + base_pitch. User understands C0, C1, etc.
        # Default octave 4 for C means C4 (MIDI 48). If they want middle C (60), they use octave 5.
        # The previous default for root_note was 60 (C4). So, let's make root_octave default to 5.
        # The parameter description for root_note was "e.g., 60 for C4". This is Yamaha C4, or standard C5.
        # pretty_midi. नोट(pitch=60) is Middle C.
        # Let's adjust the default octave in parameters to 5.
        midi_pitch = (octave_val * 12) + base_pitch
        return max(0, min(127, midi_pitch))


    def _get_scale_intervals(self, scale_name):
        scales = {
            "Major": [0, 2, 4, 5, 7, 9, 11],
            "Minor (Natural)": [0, 2, 3, 5, 7, 8, 10],
            "Dorian": [0, 2, 3, 5, 7, 9, 10],
            "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
            "Lydian": [0, 2, 4, 6, 7, 9, 11],
            "Phrygian": [0, 1, 3, 5, 7, 8, 10],
            "Locrian": [0, 1, 3, 5, 6, 8, 10],
            "Minor (Harmonic)": [0, 2, 3, 5, 7, 8, 11],
            "Minor (Melodic)": [0, 2, 3, 5, 7, 9, 11], # Ascending
            "Chromatic": list(range(12)),
            "Pentatonic Major": [0, 2, 4, 7, 9],
            "Pentatonic Minor": [0, 3, 5, 7, 10],
            "Blues": [0, 3, 5, 6, 7, 10]
        }
        return scales.get(scale_name, scales["Major"])

    def _generate_euclidean_rhythm(self, pulses, steps):
        # Bjorklund's algorithm for Euclidean rhythms
        if pulses > steps or pulses == 0:
            return [1] * steps if pulses > 0 else [0] * steps # Fill all or none if invalid
        
        pattern = []
        counts = []
        remainders = []
        
        divisor = steps - pulses
        remainders.append(pulses)
        level = 0
        
        while True:
            counts.append(divisor // remainders[level])
            remainders.append(divisor % remainders[level])
            divisor = remainders[level]
            level += 1
            if remainders[level] <= 1:
                break
        
        counts.append(divisor)
        
        def build(k):
            if k == level:
                if remainders[k] == 0:
                    pattern.append(0)
                else:
                    pattern.append(1)
            else:
                for _ in range(counts[k]):
                    build(k + 1)
                if remainders[k] != 0:
                    pattern.append(0) # Original algorithm uses 0 for remainder part, but for rhythm we might invert
                                      # For drum patterns, 1 is a hit. Let's stick to 1 = pulse.
                                      # The standard way is to append the '1's first.
                                      # Let's re-think this part for typical representation.
        # A simpler interpretation of Bjorklund for direct pattern:
        pattern = [0] * steps
        for i in range(pulses):
            pattern[round(i * steps / pulses)] = 1
        return pattern


    def generate(self, existing_notes=None, **kwargs):
        # --- Parameter Extraction ---
        num_bars = kwargs.get("num_bars", self.parameters["num_bars"]["default"])
        bpm = kwargs.get("bpm", self.parameters["bpm"]["default"])
        
        root_note_name_str = kwargs.get("root_note_name", self.parameters["root_note_name"]["default"])
        # Adjusting default octave for root_octave to 5 to match previous root_note default of 60 (C4/Middle C)
        # The parameter definition for root_octave should be updated to default to 5.
        root_octave_val = kwargs.get("root_octave", self.parameters["root_octave"]["default"]) 
        root_note = self._get_midi_note_from_name(root_note_name_str, root_octave_val)

        scale_type = kwargs.get("scale_type", self.parameters["scale_type"]["default"])
        melodic_contour_shape = kwargs.get("melodic_contour_shape", self.parameters["melodic_contour_shape"]["default"])
        octave_span = kwargs.get("octave_span", self.parameters["octave_span"]["default"])
        
        rhythm_pattern_type = kwargs.get("rhythm_pattern_type", self.parameters["rhythm_pattern_type"]["default"])
        euclidean_pulses = kwargs.get("euclidean_pulses", self.parameters["euclidean_pulses"]["default"])
        euclidean_steps = kwargs.get("euclidean_steps", self.parameters["euclidean_steps"]["default"])
        rhythm_density = kwargs.get("rhythm_density", self.parameters["rhythm_density"]["default"])
        syncopation_factor = kwargs.get("syncopation_factor", self.parameters["syncopation_factor"]["default"])
        
        base_subdivision_str = kwargs.get("base_subdivision", self.parameters["base_subdivision"]["default"])
        note_duration_type = kwargs.get("note_duration_type", self.parameters["note_duration_type"]["default"])
        fixed_note_duration_beats = kwargs.get("fixed_note_duration", self.parameters["fixed_note_duration"]["default"])
        humanization_amount = kwargs.get("humanization_amount", self.parameters["humanization_amount"]["default"])
        
        seed = kwargs.get("random_seed", self.parameters["random_seed"]["default"])
        if seed != 0:
            random.seed(seed)

        # --- Time Calculations ---
        seconds_per_beat = 60.0 / bpm
        
        subdivision_map = {"8th": 2, "16th": 4, "Triplet 8th": 3, "Triplet 16th": 6} # divisions per beat
        divisions_per_beat = subdivision_map.get(base_subdivision_str, 4)
        
        total_beats = num_bars * 4 # Assuming 4/4 time signature
        total_steps = total_beats * divisions_per_beat
        time_per_step = seconds_per_beat / divisions_per_beat

        generated_notes = []
        
        # --- 1. Rhythm Generation ---
        rhythmic_slots = [0] * total_steps # 0 = no note, 1 = note onset

        if rhythm_pattern_type == "Euclidean":
            # Ensure euclidean_steps matches a meaningful unit, e.g., one bar or one beat
            # For simplicity, apply Euclidean pattern per bar or per N beats.
            # Let's make euclidean_steps apply to a single beat for now, and repeat/vary.
            base_euclidean_pattern = self._generate_euclidean_rhythm(euclidean_pulses, euclidean_steps)
            # Tile or adapt this pattern across total_steps
            for i in range(total_steps):
                # Map i to the effective step in the base pattern, possibly scaled by divisions_per_beat
                # This needs careful mapping if euclidean_steps is not equal to divisions_per_beat
                idx_in_euclidean_beat = i % divisions_per_beat
                if idx_in_euclidean_beat < len(base_euclidean_pattern): # simple tiling if steps match subdivision
                     if base_euclidean_pattern[idx_in_euclidean_beat % len(base_euclidean_pattern)] == 1:
                        rhythmic_slots[i] = 1
                elif rhythm_density > random.random(): # Fallback if euclidean pattern is shorter
                    rhythmic_slots[i] = 1


        elif rhythm_pattern_type == "Density-Based":
            for i in range(total_steps):
                if random.random() < rhythm_density:
                    rhythmic_slots[i] = 1
        
        elif rhythm_pattern_type == "Fixed Pattern": # Example: simple kick drum pattern
            pattern = [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0] # Four on the floor if 16th notes
            if base_subdivision_str == "8th": pattern = [1,0,1,0,1,0,1,0]
            for i in range(total_steps):
                rhythmic_slots[i] = pattern[i % len(pattern)]

        # Apply Syncopation (simple offset)
        if syncopation_factor > 0:
            temp_slots = list(rhythmic_slots) # Operate on a copy
            for i in range(total_steps -1):
                if rhythmic_slots[i] == 1 and random.random() < syncopation_factor:
                    if i > 0 and rhythmic_slots[i-1] == 0: # Can we shift it earlier?
                        temp_slots[i] = 0
                        temp_slots[i-1] = 1 
                    # Could also shift later if next slot is free (more complex)
            rhythmic_slots = temp_slots
            
        # --- 2. Pitch Generation ---
        scale_intervals = self._get_scale_intervals(scale_type)
        
        # Create a pool of notes based on scale and octave span
        note_pool = []
        min_octave_offset = -((octave_span -1) // 2)
        max_octave_offset = (octave_span -1) // 2 + (octave_span % 2) # ensure range includes center
        
        for o_offset in range(min_octave_offset, max_octave_offset +1):
            for interval in scale_intervals:
                pitch = root_note + (o_offset * 12) + interval
                if 21 <= pitch <= 108:
                    note_pool.append(pitch)
        note_pool = sorted(list(set(note_pool)))
        if not note_pool: note_pool = [root_note]

        # --- Melodic Contour Generation ---
        # This part needs significant enhancement based on melodic_contour_shape
        # For now, a slightly improved random walk
        
        contour_values = [0] * total_steps # Relative steps from a base or previous note
        if melodic_contour_shape == "Rising":
            for k in range(total_steps): contour_values[k] = k // (max(1, total_steps // len(note_pool)))
        elif melodic_contour_shape == "Falling":
            for k in range(total_steps): contour_values[k] = (total_steps - k) // (max(1, total_steps // len(note_pool)))
        # Add more shapes...
        else: # Default to Smooth Random Walk
            current_val = 0
            for k in range(total_steps):
                step = random.choice([-1, -1, 0, 0, 0, 1, 1]) # Smoother steps
                current_val += step
                contour_values[k] = current_val
        
        # Normalize contour to fit within note_pool indices
        min_contour, max_contour = min(contour_values), max(contour_values)
        contour_range = max_contour - min_contour
        
        # --- 3. Note Creation ---
        current_note_idx_in_pool = len(note_pool) // 2 # Start from middle of the pool
        
        for i in range(total_steps):
            if rhythmic_slots[i] == 1:
                start_time = i * time_per_step
                
                # Duration
                duration_seconds = self._calculate_note_duration(note_duration_type, fixed_note_duration_beats, 
                                                                seconds_per_beat, time_per_step, divisions_per_beat,
                                                                rhythmic_slots, i, total_steps)
                end_time = start_time + duration_seconds

                # Pitch from contour and pool
                target_idx = current_note_idx_in_pool
                if contour_range > 0:
                    normalized_contour_val = (contour_values[i] - min_contour) / contour_range
                    target_idx = int(normalized_contour_val * (len(note_pool) -1))
                else: # Static contour or single value
                    target_idx = len(note_pool) // 2
                
                # Add some local variation / step from previous actual note
                # This makes the contour guide the general direction but allows local movement
                step_from_prev = random.choice([-2, -1, -1, 0, 1, 1, 2])
                current_note_idx_in_pool = (target_idx + step_from_prev) 
                current_note_idx_in_pool = max(0, min(len(note_pool)-1, current_note_idx_in_pool)) # Clamp index
                
                pitch = note_pool[current_note_idx_in_pool]
                
                velocity = random.randint(80, 100) 

                note = pretty_midi.Note(velocity, pitch, start_time, end_time)
                
                if humanization_amount > 0:
                    note = self._humanize_note(note, time_per_step * humanization_amount * 0.5, 
                                               humanization_amount * 0.2, humanization_amount * 0.2)
                
                generated_notes.append(note)
        
        return generated_notes

    def _calculate_note_duration(self, duration_type, fixed_beats, sec_per_beat, time_per_step, divs_per_beat, slots, current_step, total_steps):
        if duration_type == "Fixed":
            return fixed_beats * sec_per_beat
        elif duration_type == "Legato":
            next_onset = total_steps
            for j in range(current_step + 1, total_steps):
                if slots[j] == 1:
                    next_onset = j
                    break
            return (next_onset - current_step) * time_per_step
        else: # Varied
            # More musical varied durations: 50% of step, full step, 1.5x step, 2x step
            multipliers = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
            chosen_mult = random.choice(multipliers)
            duration = time_per_step * chosen_mult
            # Ensure it doesn't grossly overlap common next beat/subdivision unless very long multiplier
            max_sensible_duration = sec_per_beat * 1.5 # Max 1.5 beats unless long multiplier
            if chosen_mult <= 1.0: max_sensible_duration = sec_per_beat / divs_per_beat * (divs_per_beat + 0.5)

            return max(time_per_step * 0.45, min(duration, max_sensible_duration)) # Min duration almost half step

    def _humanize_note(self, note: pretty_midi.Note, time_variation_max_s: float, 
                       vel_variation_factor: float, dur_variation_factor: float):
        # Time variation (swing / push-pull)
        start_offset = random.uniform(-time_variation_max_s, time_variation_max_s)
        note.start += start_offset
        note.end += start_offset # Keep duration same initially
        note.start = max(0, note.start)

        # Velocity variation
        vel_change = 1.0 + random.uniform(-vel_variation_factor, vel_variation_factor)
        note.velocity = int(max(1, min(127, note.velocity * vel_change)))

        # Duration variation
        current_duration = note.end - note.start
        dur_change = 1.0 + random.uniform(-dur_variation_factor, dur_variation_factor)
        new_duration = max(0.01, current_duration * dur_change) # Ensure positive duration
        note.end = note.start + new_duration
        return note
