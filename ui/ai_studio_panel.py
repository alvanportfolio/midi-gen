import os
import sys
import tempfile
import datetime
from pathlib import Path
import random as random_module  # Explicit import to avoid naming conflicts
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDockWidget, QComboBox, QSpinBox, QGroupBox, QRadioButton,
    QButtonGroup, QSlider, QFrame, QProgressBar, QTextEdit,
    QCheckBox, QMessageBox, QToolButton
)
from PySide6.QtCore import Qt, Signal, QSize, QThread, QTimer, QUrl
from PySide6.QtGui import QFont, QIcon, QPixmap, QDesktopServices, QCursor, QColor

from ui.custom_widgets import ModernButton, ModernSlider
from config import theme

# Add AI studio paths for imports
ai_studio_path = os.path.abspath("ai_studio")
sys.path.append(ai_studio_path)
sys.path.append(os.path.join(ai_studio_path, 'tegridy-tools', 'tegridy-tools'))
sys.path.append(os.path.join(ai_studio_path, 'tegridy-tools', 'tegridy-tools', 'X-Transformer'))

# Import AI dependencies with error handling
AI_AVAILABLE = False
TMIDIX_AVAILABLE = False
TRANSFORMER_AVAILABLE = False

try:
    import torch
    import numpy as np
    print("✅ PyTorch and NumPy loaded successfully")
    
    # Try to import TMIDIX
    try:
        import TMIDIX
        TMIDIX_AVAILABLE = True
        print("✅ TMIDIX loaded successfully")
    except ImportError as e:
        print(f"⚠️ TMIDIX not available: {e}")
        print("ℹ️ AI Studio will use fallback MIDI processing")
    
    # Try to import X-Transformer
    try:
        from x_transformer_2_3_1 import *
        TRANSFORMER_AVAILABLE = True
        print("✅ X-Transformer loaded successfully")
    except ImportError as e:
        print(f"⚠️ X-Transformer not available: {e}")
        print("ℹ️ AI Studio will use simplified generation")
    
    # AI is available if we have at least PyTorch
    AI_AVAILABLE = True
    print("✅ Basic AI dependencies loaded successfully")
    
except ImportError as e:
    print(f"⚠️ Core AI dependencies not available: {e}")
    AI_AVAILABLE = False

class RealAIGenerator:
    """Real AI MIDI Generator using the alex_melody model"""
    
    def __init__(self):
        self.SEQ_LEN = 194
        self.PAD_IDX = 386
        self.model = None
        self.device = 'auto'
        self.ctx = None
        self.model_loaded = False
        
        # Auto-detect device with better error handling
        self.device = 'cpu'  # Default to CPU
        if AI_AVAILABLE:
            try:
                # First check if CUDA is available
                if torch.cuda.is_available():
                    self.device = 'cuda'
                    print(f"✅ CUDA GPU detected: {torch.cuda.get_device_name(0)}")
                else:
                    # Check for other device types (MPS for Mac)
                    if hasattr(torch, 'mps') and hasattr(torch.mps, 'is_available') and torch.mps.is_available():
                        self.device = 'mps'
                        print("✅ Apple MPS device detected")
                    else:
                        print("ℹ️ No GPU detected, using CPU")
            except Exception as e:
                print(f"⚠️ Error detecting device capabilities: {e}")
                print("ℹ️ Falling back to CPU")
                self.device = 'cpu'
    
    def load_model(self):
        """Load the alex_melody.pth model"""
        if not AI_AVAILABLE:
            raise ImportError("AI dependencies not available")
        
        # Look for model in external ai_studio folder next to executable when bundled
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = os.path.dirname(sys.executable)
            model_path = os.path.join(base_dir, "ai_studio", "models", "alex_melody.pth")
        else:
            # Running in development mode
            model_path = "ai_studio/models/alex_melody.pth"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Create model architecture
        self.model = TransformerWrapper(
            num_tokens=self.PAD_IDX + 1,
            max_seq_len=self.SEQ_LEN,
            attn_layers=Decoder(
                dim=1024,
                depth=4,
                heads=8,
                rotary_pos_emb=True,
                attn_flash=True
            )
        )
        
        self.model = AutoregressiveWrapper(
            self.model, 
            ignore_index=self.PAD_IDX, 
            pad_value=self.PAD_IDX
        )
        
        # Load weights
        if self.device == 'cpu':
            self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
        else:
            self.model.load_state_dict(torch.load(model_path))
        
        self.model.to(self.device)
        self.model.eval()
        
        # Setup autocast context with better error handling
        try:
            if self.device == 'cuda':
                # Check if bfloat16 is supported
                if torch.cuda.is_bf16_supported():
                    self.ctx = torch.amp.autocast(device_type='cuda', dtype=torch.bfloat16)
                else:
                    # Fall back to float16 if bfloat16 is not supported
                    self.ctx = torch.amp.autocast(device_type='cuda', dtype=torch.float16)
            elif self.device == 'mps':
                # MPS device (Apple Silicon)
                self.ctx = torch.amp.autocast(device_type='mps', dtype=torch.float16)
            else:
                # CPU fallback
                self.ctx = torch.amp.autocast(device_type='cpu', dtype=torch.bfloat16, enabled=False)
        except Exception as e:
            print(f"⚠️ Error setting up autocast context: {e}")
            print("ℹ️ Disabling autocast")
            # Create a dummy context manager that does nothing
            self.ctx = torch.amp.autocast(device_type='cpu', enabled=False)
        
        self.model_loaded = True
    
    def convert_notes_to_tokens(self, notes):
        """Convert pretty_midi notes to tokens for the model"""
        if not notes:
            return []
        
        # Create temporary MIDI file
        temp_dir = tempfile.mkdtemp()
        temp_midi = os.path.join(temp_dir, "temp.mid")
        
        try:
            import pretty_midi
            midi = pretty_midi.PrettyMIDI()
            piano = pretty_midi.Instrument(program=0)
            
            for note in notes:
                piano.notes.append(note)
            
            midi.instruments.append(piano)
            midi.write(temp_midi)
            
            # Process with TMIDIX
            raw_score = TMIDIX.midi2single_track_ms_score(temp_midi)
            escore_notes = TMIDIX.advanced_score_processor(
                raw_score, 
                return_enhanced_score_notes=True, 
                apply_sustain=True
            )[0]
            
            sp_escore_notes = TMIDIX.solo_piano_escore_notes(escore_notes)
            zscore = TMIDIX.recalculate_score_timings(sp_escore_notes)
            escore = TMIDIX.augment_enhanced_score_notes(zscore, timings_divider=32)
            escore = TMIDIX.fix_escore_notes_durations(escore)
            cscore = TMIDIX.chordify_score([1000, escore])
            
            # Convert to tokens
            score = []
            pc = cscore[0]
            
            for c in cscore:
                score.append(max(0, min(127, c[0][1] - pc[0][1])))
                for n in c:
                    score.extend([
                        max(1, min(127, n[2])) + 128,  # Duration token
                        max(1, min(127, n[4])) + 256   # Pitch token
                    ])
                    break
                pc = c
            
            return score
            
        finally:
            # Cleanup
            try:
                os.remove(temp_midi)
                os.rmdir(temp_dir)
            except:
                pass
    
    def generate_tokens(self, mode='from_seed', seed_tokens=None, temperature=0.9, 
                       seed_length=16, prime_duration=10, prime_pitch=72):
        """Generate tokens using the model"""
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")
        
        # Prepare input sequence
        if mode == 'from_seed' and seed_tokens:
            used_tokens = seed_tokens[:seed_length] if len(seed_tokens) >= seed_length else seed_tokens
            x = torch.LongTensor([384] + used_tokens).to(self.device)
        elif mode == 'random' and seed_tokens:
            context_tokens = seed_tokens[:8] if len(seed_tokens) >= 8 else seed_tokens
            x = torch.LongTensor([384, 0] + context_tokens).to(self.device)
        elif mode == 'prime_note':
            x = torch.LongTensor([384, 0, 128 + prime_duration, 256 + prime_pitch]).to(self.device)
        else:
            x = torch.LongTensor([384, 0, 128 + 10, 256 + 60]).to(self.device)
        
        tokens_to_generate = self.SEQ_LEN - x.shape[0]
        
        # Generate tokens
        with self.ctx:
            output = self.model.generate(
                x,
                tokens_to_generate,
                temperature=temperature,
                eos_token=385,
                return_prime=True,
                verbose=False
            )
        
        return output.tolist()
    
    def tokens_to_notes(self, tokens):
        """Convert tokens to pretty_midi notes"""
        import pretty_midi
        
        notes = []
        time = 0
        dur = 1
        vel = 90
        
        for token in tokens:
            if 0 <= token < 128:
                time += token * 32
            elif 128 <= token < 256:
                dur = (token - 128) * 32
            elif 256 <= token < 384:
                pitch = token - 256
                if 0 <= pitch <= 127 and dur > 0:
                    note = pretty_midi.Note(
                        velocity=vel,
                        pitch=pitch,
                        start=time / 1000.0,  # Convert to seconds
                        end=(time + dur) / 1000.0
                    )
                    notes.append(note)
        
        return notes

class AIGenerationWorker(QThread):
    """Worker thread for AI generation to keep UI responsive"""
    
    # Signals to communicate with the main thread
    finished = Signal(list)  # Emitted when generation is complete with notes
    error = Signal(str)      # Emitted when an error occurs
    progress = Signal(str)   # Emitted for progress updates
    
    def __init__(self, ai_generator, generation_mode, scale_root, scale_type, creativity, 
                 reference_length, existing_notes, use_piano_roll_input, seed_value, randomize_seed):
        super().__init__()
        self.ai_generator = ai_generator
        self.generation_mode = generation_mode
        self.scale_root = scale_root
        self.scale_type = scale_type
        self.creativity = creativity
        self.reference_length = reference_length
        self.existing_notes = existing_notes
        self.use_piano_roll_input = use_piano_roll_input
        self.seed_value = seed_value
        self.randomize_seed = randomize_seed
    
    def run(self):
        """Run the AI generation in background thread"""
        try:
            if not AI_AVAILABLE:
                self.error.emit("Required dependencies not found. Please install all required Python packages and restart the application.")
                return
            
            if not self.ai_generator.model_loaded:
                self.error.emit("AI model not loaded. Please load the model first.")
                return
            
            self.progress.emit("Converting parameters...")
            
            # Convert musician-friendly parameters to AI model parameters
            ai_params = self._convert_to_ai_parameters()
            
            self.progress.emit("Generating melody with AI...")
            
            # Generate using real AI model
            generated_notes = self._generate_with_ai(ai_params)
            
            self.progress.emit("Generation complete!")
            self.finished.emit(generated_notes)
        except Exception as e:
            self.error.emit(str(e))
    
    def _convert_to_ai_parameters(self):
        """Convert musician-friendly parameters to AI model parameters"""
        
        # Convert generation mode
        if self.generation_mode == "Continue Melody":
            ai_mode = "from_seed"
            seed_length = self.reference_length
        elif self.generation_mode == "Create Variation":
            ai_mode = "random"
            seed_length = 8  # Fixed for random mode
        elif self.generation_mode == "Start Fresh":
            ai_mode = "prime_note"
            seed_length = 0
        
        # Convert creativity to temperature
        temperature = 0.5 + (self.creativity / 100.0) * 1.0  # Maps 0-100 to 0.5-1.5
        
        # Convert scale to prime note (for prime_note mode)
        scale_to_midi = {
            "C": 60, "C#": 61, "D": 62, "D#": 63, "E": 64, "F": 65,
            "F#": 66, "G": 67, "G#": 68, "A": 69, "A#": 70, "B": 71
        }
        
        prime_pitch = scale_to_midi.get(self.scale_root, 60)
        if self.scale_type == "Minor":
            prime_pitch = prime_pitch  # Keep the same root note for minor
        
        prime_duration = 10  # Default duration for prime note
        
        # Set seed if needed
        if self.randomize_seed:
            seed = random_module.randint(1, 10000)
        else:
            seed = self.seed_value
        
        if seed:
            random_module.seed(seed)
            if AI_AVAILABLE:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
        
        return {
            "mode": ai_mode,
            "temperature": temperature,
            "seed_length": seed_length,
            "prime_pitch": prime_pitch,
            "prime_duration": prime_duration,
            "seed": seed
        }
    
    def _generate_with_ai(self, ai_params):
        """Generate using the real AI model"""
        # Convert existing notes to tokens if using piano roll input
        seed_tokens = None
        if self.use_piano_roll_input and self.existing_notes:
            seed_tokens = self.ai_generator.convert_notes_to_tokens(self.existing_notes)
        
        # Generate tokens
        generated_tokens = self.ai_generator.generate_tokens(
            mode=ai_params["mode"],
            seed_tokens=seed_tokens,
            temperature=ai_params["temperature"],
            seed_length=ai_params["seed_length"],
            prime_duration=ai_params["prime_duration"],
            prime_pitch=ai_params["prime_pitch"]
        )
        
        # Convert tokens back to notes
        notes = self.ai_generator.tokens_to_notes(generated_tokens)
        return notes

class AIStudioPanel(QDockWidget):
    """AI Studio panel for musician-friendly MIDI generation"""
    
    notesGenerated = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__("🤖 AI Studio", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetMovable | 
            QDockWidget.DockWidgetFloatable | 
            QDockWidget.DockWidgetClosable
        )
        
        self.dock_content = QWidget()
        self.setWidget(self.dock_content)
        self.dock_content.setStyleSheet(f"background-color: {theme.PANEL_BG_COLOR.name()};")
        
        main_layout = QVBoxLayout(self.dock_content)
        main_layout.setContentsMargins(theme.PADDING_L, theme.PADDING_L, theme.PADDING_L, theme.PADDING_L)
        main_layout.setSpacing(theme.PADDING_M)
        
        # Initialize AI generator
        self.ai_generator = RealAIGenerator()
        
        # Current notes reference
        self.current_notes = []
        self.generation_worker = None
        self.generation_in_progress = False
        
        self._setup_model_section(main_layout)
        self._setup_input_source_section(main_layout)
        self._setup_generation_mode_section(main_layout)
        self._setup_musical_settings_section(main_layout)
        self._setup_creativity_section(main_layout)
        self._setup_seed_section(main_layout)
        self._setup_controls_section(main_layout)
        self._setup_status_section(main_layout)
        self._setup_attribution_section(main_layout)
        
        # Add stretch to push everything to top
        main_layout.addStretch()
    
    def _setup_model_section(self, main_layout):
        """Setup AI model loading section"""
        model_group = QGroupBox("🧠 AI Model")
        model_group.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(theme.PADDING_S)
        
        # Model status and load button
        model_control_layout = QHBoxLayout()
        
        self.load_model_button = ModernButton("Load Melody Model", accent=True)
        self.load_model_button.setToolTip("Load the alex_melody.pth AI model")
        self.load_model_button.clicked.connect(self._load_model)
        model_control_layout.addWidget(self.load_model_button)
        
        model_control_layout.addStretch()
        model_layout.addLayout(model_control_layout)
        
        # Model info
        self.model_info_label = QLabel("Model not loaded")
        self.model_info_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        self.model_info_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        model_layout.addWidget(self.model_info_label)
        
        main_layout.addWidget(model_group)
    
    def _setup_input_source_section(self, main_layout):
        """Setup input source toggle section"""
        input_group = QGroupBox("📥 Input Source")
        input_group.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(theme.PADDING_S)
        
        # Piano roll input toggle
        self.use_piano_roll_checkbox = QCheckBox("Use Piano Roll Input MIDI")
        self.use_piano_roll_checkbox.setChecked(True)
        self.use_piano_roll_checkbox.setToolTip("Use currently visible notes in the piano roll as input")
        self.use_piano_roll_checkbox.stateChanged.connect(self._on_input_source_changed)
        input_layout.addWidget(self.use_piano_roll_checkbox)
        
        main_layout.addWidget(input_group)
    
    def _setup_generation_mode_section(self, main_layout):
        """Setup the generation mode selection"""
        mode_group = QGroupBox("✨ Generation Style")
        mode_group.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(theme.PADDING_S)
        
        self.mode_button_group = QButtonGroup()
        
        # Continue Melody (from_seed)
        self.continue_radio = QRadioButton("🎵 Continue Melody")
        self.continue_radio.setToolTip("Extend existing notes in your piano roll")
        self.continue_radio.setChecked(True)
        self.mode_button_group.addButton(self.continue_radio, 0)
        mode_layout.addWidget(self.continue_radio)
        
        # Create Variation (random)
        self.variation_radio = QRadioButton("🎭 Create Variation")
        self.variation_radio.setToolTip("Generate a variation based on existing notes")
        self.mode_button_group.addButton(self.variation_radio, 1)
        mode_layout.addWidget(self.variation_radio)
        
        # Start Fresh (prime_note)
        self.fresh_radio = QRadioButton("🌟 Start Fresh")
        self.fresh_radio.setToolTip("Create a new melody from scratch")
        self.mode_button_group.addButton(self.fresh_radio, 2)
        mode_layout.addWidget(self.fresh_radio)
        
        # Reference Length (only for Continue Melody)
        ref_layout = QHBoxLayout()
        self.ref_length_label = QLabel("Reference Length:")
        self.ref_length_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        
        self.ref_length_spinbox = QSpinBox()
        self.ref_length_spinbox.setRange(4, 32)
        self.ref_length_spinbox.setValue(16)
        self.ref_length_spinbox.setSuffix(" notes")
        self.ref_length_spinbox.setToolTip("How many notes to use as reference")
        
        ref_layout.addWidget(self.ref_length_label)
        ref_layout.addWidget(self.ref_length_spinbox)
        ref_layout.addStretch()
        
        mode_layout.addLayout(ref_layout)
        
        # Connect signals to enable/disable reference length
        self.mode_button_group.buttonClicked.connect(self._on_generation_mode_changed)
        
        main_layout.addWidget(mode_group)
    
    def _setup_musical_settings_section(self, main_layout):
        """Setup musical settings (scale, key, etc.)"""
        musical_group = QGroupBox("🎼 Musical Settings")
        musical_group.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        musical_layout = QVBoxLayout(musical_group)
        musical_layout.setSpacing(theme.PADDING_S)
        
        # Scale/Key selection
        scale_layout = QHBoxLayout()
        
        scale_layout.addWidget(QLabel("Key:"))
        
        self.scale_root_combo = QComboBox()
        self.scale_root_combo.addItems(["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"])
        self.scale_root_combo.setCurrentText("C")
        scale_layout.addWidget(self.scale_root_combo)
        
        self.scale_type_combo = QComboBox()
        self.scale_type_combo.addItems(["Major", "Minor", "Dorian", "Mixolydian", "Lydian", "Phrygian"])
        self.scale_type_combo.setCurrentText("Major")
        scale_layout.addWidget(self.scale_type_combo)
        
        scale_layout.addStretch()
        musical_layout.addLayout(scale_layout)
        
        # Note: This section is only visible when piano roll input is OFF
        self.musical_settings_group = musical_group
        
        main_layout.addWidget(musical_group)
    
    def _setup_seed_section(self, main_layout):
        """Setup seed settings section"""
        seed_group = QGroupBox("🎲 Seed Settings")
        seed_group.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        seed_layout = QVBoxLayout(seed_group)
        seed_layout.setSpacing(theme.PADDING_S)
        
        # Randomize seed checkbox
        self.randomize_seed_checkbox = QCheckBox("Randomize Seed")
        self.randomize_seed_checkbox.setChecked(True)
        self.randomize_seed_checkbox.setToolTip("Generate a new random seed for each generation")
        self.randomize_seed_checkbox.stateChanged.connect(self._on_randomize_seed_changed)
        seed_layout.addWidget(self.randomize_seed_checkbox)
        
        # Seed value input
        seed_value_layout = QHBoxLayout()
        seed_value_layout.addWidget(QLabel("Seed Value:"))
        
        self.seed_spinbox = QSpinBox()
        self.seed_spinbox.setRange(1, 999999)
        self.seed_spinbox.setValue(12345)
        self.seed_spinbox.setEnabled(False)  # Disabled by default when randomize is on
        self.seed_spinbox.setToolTip("Fixed seed value for reproducible results")
        seed_value_layout.addWidget(self.seed_spinbox)
        
        seed_value_layout.addStretch()
        seed_layout.addLayout(seed_value_layout)
        
        main_layout.addWidget(seed_group)
    
    def _setup_creativity_section(self, main_layout):
        """Setup creativity/variation controls"""
        creativity_group = QGroupBox("🎨 Creativity")
        creativity_group.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        creativity_layout = QVBoxLayout(creativity_group)
        creativity_layout.setSpacing(theme.PADDING_S)
        
        # Creativity slider
        creativity_desc_layout = QHBoxLayout()
        creativity_desc_layout.addWidget(QLabel("Conservative"))
        creativity_desc_layout.addStretch()
        creativity_desc_layout.addWidget(QLabel("Creative"))
        creativity_layout.addLayout(creativity_desc_layout)
        
        self.creativity_slider = ModernSlider(Qt.Horizontal)
        self.creativity_slider.setRange(0, 100)
        self.creativity_slider.setValue(70)  # Default to 70% creativity
        self.creativity_slider.setToolTip("Lower values create more predictable melodies, higher values are more experimental")
        creativity_layout.addWidget(self.creativity_slider)
        
        # Creativity value display
        self.creativity_value_label = QLabel("70%")
        self.creativity_value_label.setAlignment(Qt.AlignCenter)
        self.creativity_value_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        creativity_layout.addWidget(self.creativity_value_label)
        
        self.creativity_slider.valueChanged.connect(
            lambda value: self.creativity_value_label.setText(f"{value}%")
        )
        
        main_layout.addWidget(creativity_group)
    
    def _setup_controls_section(self, main_layout):
        """Setup control buttons"""
        controls_layout = QHBoxLayout()
        
        self.generate_button = ModernButton("✨ Generate", accent=True)
        self.generate_button.setToolTip("Generate new MIDI notes using AI")
        self.generate_button.clicked.connect(self._generate_notes)
        controls_layout.addWidget(self.generate_button)
        
        self.clear_button = ModernButton("🗑️ Clear")
        self.clear_button.setToolTip("Clear all notes from piano roll")
        self.clear_button.clicked.connect(self._clear_notes)
        controls_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(controls_layout)
    
    def _setup_status_section(self, main_layout):
        """Setup status display and progress"""
        status_group = QGroupBox("📊 Status")
        status_group.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(theme.PADDING_S)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_label = QLabel("Ready to generate")
        self.status_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        self.status_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        status_layout.addWidget(self.status_label)
        
        # Dependencies info
        deps_info_layout = QHBoxLayout()
        deps_info_layout.addWidget(QLabel("Dependencies:"))
        
        if AI_AVAILABLE:
            deps_status = "🟢 PyTorch & TMIDIX Available"
        else:
            deps_status = "🔴 Missing Dependencies"
        
        self.deps_status_label = QLabel(deps_status)
        self.deps_status_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        deps_info_layout.addWidget(self.deps_status_label)
        deps_info_layout.addStretch()
        
        status_layout.addLayout(deps_info_layout)
        
        main_layout.addWidget(status_group)
    
    def _setup_attribution_section(self, main_layout):
        """Setup attribution section for Alex's work"""
        attribution_group = QGroupBox("💝 Credits")
        attribution_group.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        attribution_layout = QHBoxLayout(attribution_group)
        attribution_layout.setSpacing(theme.PADDING_S)
        
        # Info icon with tooltip
        self.info_icon = QToolButton()
        self.info_icon.setText("ℹ️")
        self.info_icon.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_L))
        # Create a color with alpha for hover effect
        hover_color = QColor(theme.ACCENT_PRIMARY_COLOR)
        hover_color.setAlpha(30)
        
        self.info_icon.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                color: {theme.ACCENT_PRIMARY_COLOR.name()};
                padding: {theme.PADDING_XS}px;
                border-radius: {theme.BORDER_RADIUS_S}px;
            }}
            QToolButton:hover {{
                background-color: {hover_color.name()};
            }}
        """)
        
        # Rich tooltip with attribution
        tooltip_text = """<div style='font-size: 12px; line-height: 1.4; padding: 8px;'>
        <p><b>🙏 Special Thanks to Alex Sigalov</b></p>
        <p>• Creator of the awesome <b>tegridy-tools</b> framework</p>
        <p>• Provider of the <b>alex_melody.pth</b> AI model</p>
        <p>• Dedicated to building ethical AI for music</p>
        <p><br/>🌟 <b>Shout out to this amazing contributor!</b></p>
        <p>📧 Contact: <a href='https://github.com/asigalov61'>@asigalov61</a></p>
        </div>"""
        
        self.info_icon.setToolTip(tooltip_text)
        self.info_icon.setCursor(QCursor(Qt.PointingHandCursor))  # Set cursor programmatically
        self.info_icon.clicked.connect(self._open_alex_github)
        attribution_layout.addWidget(self.info_icon)
        
        # Attribution text
        attribution_text = QLabel("Powered by tegridy-tools & alex_melody model")
        attribution_text.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        attribution_text.setStyleSheet(f"""
            QLabel {{
                color: {theme.SECONDARY_TEXT_COLOR.name()};
                font-style: italic;
            }}
        """)
        attribution_layout.addWidget(attribution_text)
        
        # GitHub link button
        github_button = ModernButton("🔗 GitHub")
        github_button.setFixedWidth(80)
        github_button.setToolTip("Visit Alex's GitHub profile")
        github_button.clicked.connect(self._open_alex_github)
        github_button.setStyleSheet(f"""
            QPushButton {{
                font-size: {theme.FONT_SIZE_S}pt;
                padding: {theme.PADDING_XS}px {theme.PADDING_S}px;
            }}
        """)
        attribution_layout.addWidget(github_button)
        
        attribution_layout.addStretch()
        main_layout.addWidget(attribution_group)
    
    def _open_alex_github(self):
        """Open Alex's GitHub profile"""
        QDesktopServices.openUrl(QUrl("https://github.com/asigalov61"))
    
    def _load_model(self):
        """Load the AI model"""
        try:
            self.load_model_button.setEnabled(False)
            self.load_model_button.setText("Loading...")
            self.model_info_label.setText("Loading model...")
            
            # This runs in the main thread but should be quick
            self.ai_generator.load_model()
            
            # Update UI
            self.load_model_button.setText("✅ Model Loaded")
            self.load_model_button.setEnabled(False)  # Don't allow reloading
            device_info = "GPU" if self.ai_generator.device == 'cuda' else "CPU"
            self.model_info_label.setText(f"🟢 alex_melody.pth loaded on {device_info}")
            self.model_info_label.setStyleSheet(f"color: {theme.ACCENT_PRIMARY_COLOR.name()};")
            
        except Exception as e:
            # Show error dialog
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Model Loading Error")
            msg.setText("Failed to load model. Please install all dependencies and restart the app.")
            msg.setDetailedText(str(e))
            msg.exec()
            
            # Reset UI
            self.load_model_button.setText("Load Melody Model")
            self.load_model_button.setEnabled(True)
            self.model_info_label.setText("❌ Failed to load model")
            self.model_info_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
    
    def _on_input_source_changed(self, state):
        """Handle input source toggle"""
        use_piano_roll = state == Qt.Checked
        
        # Show/hide musical settings based on input source
        if use_piano_roll:
            self.musical_settings_group.setVisible(False)
        else:
            self.musical_settings_group.setVisible(True)
    
    def _on_randomize_seed_changed(self, state):
        """Handle randomize seed checkbox"""
        randomize = state == Qt.Checked
        self.seed_spinbox.setEnabled(not randomize)
    
    def _on_generation_mode_changed(self, button):
        """Handle generation mode changes"""
        is_continue_mode = (button == self.continue_radio)
        self.ref_length_label.setEnabled(is_continue_mode)
        self.ref_length_spinbox.setEnabled(is_continue_mode)
    
    def _generate_notes(self):
        """Start AI generation process"""
        if self.generation_in_progress:
            return
        
        # Check if model is loaded
        if not self.ai_generator.model_loaded:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Model Not Loaded")
            msg.setText("Please load the AI model first before generating.")
            msg.exec()
            return
        
        # Get current settings
        if self.continue_radio.isChecked():
            generation_mode = "Continue Melody"
        elif self.variation_radio.isChecked():
            generation_mode = "Create Variation"
        else:
            generation_mode = "Start Fresh"
        
        scale_root = self.scale_root_combo.currentText()
        scale_type = self.scale_type_combo.currentText()
        creativity = self.creativity_slider.value()
        reference_length = self.ref_length_spinbox.value()
        use_piano_roll_input = self.use_piano_roll_checkbox.isChecked()
        seed_value = self.seed_spinbox.value()
        randomize_seed = self.randomize_seed_checkbox.isChecked()
        
        # Start generation in worker thread
        self.generation_worker = AIGenerationWorker(
            self.ai_generator, generation_mode, scale_root, scale_type, creativity, 
            reference_length, self.current_notes, use_piano_roll_input, seed_value, randomize_seed
        )
        
        self.generation_worker.finished.connect(self._on_generation_finished)
        self.generation_worker.error.connect(self._on_generation_error)
        self.generation_worker.progress.connect(self._on_generation_progress)
        
        self.generation_in_progress = True
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.generation_worker.start()
    
    def _on_generation_finished(self, generated_notes):
        """Handle generation completion"""
        self.generation_in_progress = False
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Generated {len(generated_notes)} notes")
        
        # Emit the generated notes
        self.notesGenerated.emit(generated_notes)
    
    def _on_generation_error(self, error_message):
        """Handle generation errors"""
        self.generation_in_progress = False
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Error: {error_message}")
        
        # Update model info if it's a model error
        if "not loaded" in error_message.lower() or "dependencies" in error_message.lower():
            self.model_info_label.setText("❌ Model error")
            self.model_info_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
    
    def _on_generation_progress(self, message):
        """Handle generation progress updates"""
        self.status_label.setText(message)
    
    def _clear_notes(self):
        """Clear all notes"""
        self.notesGenerated.emit([])  # Emit empty list to clear notes
        self.status_label.setText("Notes cleared")
    
    def set_current_notes(self, notes):
        """Update current notes for reference"""
        self.current_notes = notes
        note_count = len(notes) if notes else 0
        if note_count > 0:
            self.status_label.setText(f"Ready - {note_count} notes loaded")
        else:
            self.status_label.setText("Ready to generate") 