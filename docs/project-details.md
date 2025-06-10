# Piano Roll Studio - Complete Project Details

## Project Overview

Piano Roll Studio is an advanced, plugin-based MIDI generator system that integrates a custom piano roll GUI with cutting-edge AI technology. The system allows users to generate MIDI notes using various algorithms (both traditional and AI-powered), visualize them on a professional piano roll interface, play them back with FluidSynth audio engine, and export them to standard MIDI files.

## 🏗️ System Architecture

The architecture follows a modular design combining traditional plugin systems with modern AI capabilities:

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│                 │     │                   │     │                 │
│  Piano Roll UI  │◄────┤  Plugin Manager   │◄────┤  Plugin System  │
│                 │     │                   │     │                 │
└────────┬────────┘     └───────────────────┘     └────────┬────────┘
         │                                                 │
         │              ┌───────────────────┐              │
         │              │                   │              │
         └──────────────┤   AI Studio       │──────────────┘
                        │   (NEW)           │
                        └────────┬──────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Note Display   │     │  AI Models      │     │  MIDI Export    │
│                 │     │  (PyTorch)      │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Core Components:
- **Piano Roll UI**: Modern main application window with transport controls and visualization
- **Plugin Manager**: Discovers, loads, and manages traditional MIDI generator plugins
- **AI Studio**: Advanced AI-powered melody generation using deep learning models
- **Plugin System**: Provides the base API for creating traditional plugins
- **Note Display**: Renders MIDI notes on a professional piano roll interface
- **MIDI Export**: Exports generated notes to standard MIDI files
- **AI Models**: PyTorch-based transformer models for sophisticated music generation

## 🛠️ Complete Project Structure

```text
midi-gen/
├── LICENSE                         # Non-Commercial License file
├── README.md                       # Main project README
├── INSTALLATION.md                 # Installation guide
├── app.py                          # Main application entry point
├── note_display.py                 # Piano roll grid and note visualization (QWidget)
├── midi_player.py                  # Facade for MIDI playback
├── plugin_manager.py               # Plugin discovery and management system
├── plugin_api.py                   # Base classes and API for plugins
├── export_utils.py                 # MIDI export functionality
├── utils.py                        # Enhanced with AI dependency management
├── requirements.txt                # Python dependencies
├── install.bat                     # Windows automated installer
├── install.sh                      # Linux/macOS automated installer
├── start.bat                       # Windows startup script
├── model_download.bat              # Windows AI model downloader
├── model_download.sh               # Linux/macOS AI model downloader
├── build_standalone.bat            # Windows standalone builder
├── pyrightconfig.json              # Python type checking configuration
├── EMBEDDED_PYTHON_GUIDE.md        # Embedded Python guide
├── image1.png                      # Documentation image
├── image2.png                      # Documentation image
├── config/
│   ├── __init__.py
│   ├── constants.py                # Application constants
│   └── theme.py                    # UI theme configuration
├── ui/
│   ├── __init__.py
│   ├── custom_widgets.py           # ModernSlider, ModernButton with animations
│   ├── drawing_utils.py            # PianoRollDisplay drawing functions
│   ├── event_handlers.py           # MainWindowEventHandlersMixin
│   ├── main_window.py              # PianoRollMainWindow (QMainWindow)
│   ├── plugin_dialogs.py           # PluginParameterDialog
│   ├── plugin_panel.py             # PluginManagerPanel (QDockWidget)
│   ├── transport_controls.py       # Transport control widgets
│   └── ai_studio_panel.py          # AI Studio panel with embedded RealAIGenerator class
├── midi/
│   ├── __init__.py
│   ├── device_manager.py           # (Legacy, if previously used for pygame.midi output)
│   ├── fluidsynth_player.py        # Wrapper for FluidSynth library
│   ├── midi_event_utils.py         # MIDI event utilities
│   ├── note_scheduler.py           # Note scheduling system
│   └── playback_controller.py      # Manages playback logic using FluidSynthPlayer
├── plugins/                        # Traditional MIDI generator plugins
│   ├── __init__.py
│   ├── markov_generator.py         # Markov chain melody generation
├── ai_studio/                      # AI features directory
│   └── models/                     # Contains .pth model files
│       ├── README.txt              # Instructions for model placement
│       ├── alex_melody.pth         # Main melody generation model
│       └── Piano_Hands_Transformer_Trained_Model_*.pth # Piano transformer models
├── assets/                         # Application assets
│   └── icons/                      # Application icons and UI icons
│       ├── app_icon.icns           # macOS application icon
│       ├── app_icon.ico            # Windows application icon
│       ├── app_icon.png            # PNG application icon
│       ├── chevron_down.svg        # UI chevron icon
│       ├── clear.svg               # Clear button icon
│       ├── default-plugin.svg      # Default plugin icon
│       ├── file.svg                # File icon
│       ├── pause.svg               # Pause button icon
│       ├── play.svg                # Play button icon
│       └── stop.svg                # Stop button icon
└── docs/                           # Documentation
    ├── index.html                  # Documentation index
    ├── project-details.md          # This comprehensive documentation
    ├── plugin-docs.md              # Documentation for plugin developers
    ├── assets/                     # Documentation assets
    └── pages/                      # Documentation pages
```

## 📁 Detailed File Structure and Purposes

### Core Application Files

#### `app.py`
- **Purpose**: Application entry point with enhanced startup optimizations
- **Key Functions**: 
  - Initializes QApplication with SDL audio settings
  - Sets modern application style and theme
  - Creates and shows the main application window (`PianoRollMainWindow`)
  - Implements startup optimizations to prevent audio pops and clicks
  - Runs the application event loop with error handling

#### `ui/main_window.py`
- **Purpose**: Main application window with modern UI elements
- **Key Classes**:
  - `PianoRollMainWindow`: Enhanced main window with dockable panels
  - Modern transport controls with animations
  - Integration with both traditional plugins and AI Studio
- **Key Features**:
  - Dockable AI Studio panel
  - Enhanced transport controls (play, pause, stop)
  - Real-time MIDI note management
  - Time and position tracking with visual feedback
  - Advanced zoom controls for viewing longer sequences
  - Integration with both plugin manager and AI Studio
#### `utils.py`
- **Purpose**: Utility functions with AI dependency management
- **Key Functions**: 
  - AI dependency checking and validation
  - System path management for AI modules
  - Cross-platform utility functions
  - Enhanced error handling and logging

#### `note_display.py`
- **Purpose**: Professional piano roll grid and note visualization
- **Key Classes**:
  - `PianoRollDisplay`: Advanced widget for MIDI note display
- **Key Functions**:
  - High-quality piano keyboard rendering
  - Precise time grid with bars and beats
  - Color-coded MIDI notes with velocity visualization
  - Smooth playhead animation
  - Advanced mouse interactions and editing capabilities
- **Purpose**: Professional piano roll grid and note visualization
- **Key Classes**:
  - `PianoRollDisplay`: Advanced widget for MIDI note display
- **Key Functions**:
  - High-quality piano keyboard rendering
  - Precise time grid with bars and beats
  - Color-coded MIDI notes with velocity visualization
  - Smooth playhead animation
  - Advanced mouse interactions and editing capabilities

### Configuration Files

#### `config/constants.py`
- **Purpose**: Application-wide constants and configuration values
- **Key Constants**: 
  - MIDI parameter constants (velocity, channel, timing)
  - UI configuration values (colors, sizes, animations)
  - File path constants and default values
  - Audio system configuration parameters

#### `config/theme.py`
- **Purpose**: UI theme and styling configuration
- **Key Functions**:
  - Dark theme color definitions
  - UI component styling parameters
  - Modern interface color schemes
  - Animation and transition settings

#### `pyrightconfig.json`
- **Purpose**: Python type checking configuration for development
- **Configuration**: 
  - Type checking strictness settings
  - Python path configuration
  - Import resolution settings
  - Development environment optimization

#### `midi_player.py`
- **Purpose**: Enhanced facade for MIDI playback with improved audio handling
- **Key Functions**:
  - Provides unified API for play, pause, stop, seek operations
  - Advanced tempo, instrument, and volume control
  - Manages `PlaybackController` instance with enhanced error handling

#### `midi/playback_controller.py`
- **Purpose**: Core MIDI playback logic with enhanced timing precision
- **Key Classes**:
  - `PlaybackController`: Advanced playback state management
- **Key Functions**:
  - Initializes and manages `FluidSynthPlayer` for high-quality audio
  - Uses `NoteScheduler` for precise timing
  - Enhanced methods for playback control with better responsiveness
  - Improved tempo and timing accuracy
  - Master volume control with smooth transitions

#### `midi/fluidsynth_player.py`
- **Purpose**: Optimized wrapper for FluidSynth library
- **Key Classes**:
  - `FluidSynthPlayer`: High-performance FluidSynth interface
- **Key Functions**:
  - `sfload()`: Intelligent SoundFont loading with caching
  - `noteon()`, `noteoff()`: Optimized note events with minimal latency
  - `program_select()`: Smooth instrument changes
  - `set_gain()`: Advanced volume control with fade support
  - `cleanup()`: Proper resource management and cleanup

### Plugin System Files

#### `plugin_api.py`
- **Purpose**: Defines the comprehensive plugin API and base classes
- **Key Classes**:
  - `PluginBase`: Enhanced abstract base class for all plugins
- **Key Functions**:
  - `generate()`: Core method with improved parameter validation
  - `get_parameter_info()`: Extended parameter information system
  - `validate_parameters()`: Robust parameter validation with error reporting

#### `plugin_manager.py`
- **Purpose**: Advanced plugin discovery and management system
- **Key Classes**:
  - `PluginManager`: Enhanced plugin lifecycle management
- **Key Functions**:
  - `discover_plugins()`: Improved plugin discovery with error handling
  - `load_plugin()`: Safe plugin loading with dependency checking
  - `get_plugin_list()`: Categorized plugin listing
  - `generate_notes()`: Enhanced note generation with progress feedback

### Traditional Plugin Files

#### `plugins/motif_generator.py`
- **Purpose**: Advanced motif-based melody generation
- **Key Classes**:
  - `MotifGenerator`: Enhanced motif manipulation
- **Key Functions**:
  - `_create_motif()`: Intelligent motif creation
  - `_create_variation()`: Advanced variation techniques
  - `generate()`: Professional motif-based composition

#### `plugins/markov_generator.py`
- **Purpose**: Sophisticated Markov chain melody generation
- **Key Classes**:
  - `MarkovGenerator`: Enhanced probabilistic generation
- **Key Functions**:
  - `_build_transition_matrix()`: Advanced transition analysis
  - `_choose_next_note()`: Intelligent note selection
  - `generate()`: Professional Markov-based composition

#### `plugins/melody_generator.py`
- **Purpose**: Emotional melody generator with musical intelligence
- **Key Classes**:
  - `MelodyGenerator`: Advanced emotional melody creation
- **Key Functions**:
  - `_get_scale_notes()`: Comprehensive scale support
  - `_apply_emotion_contour()`: Sophisticated emotional modeling
  - `_generate_random_walk()`: Intelligent random walk patterns
  - `generate()`: Professional emotional melody generation

## 🧠 AI Studio Features (NEW)

### AI Studio Overview

The AI Studio represents a revolutionary addition to Piano Roll Studio, bringing cutting-edge deep learning capabilities to music generation:

- **AI Models Integration**: Full support for PyTorch-based transformer models
- **Professional UI Panel**: Dedicated AI Studio panel with modern interface
- **Multi-device Support**: Intelligent device selection (CPU, CUDA GPU, Apple MPS)
- **Dynamic Model Management**: Automatic model discovery and loading
- **Real-time Generation**: Background processing with progress feedback

### AI Generation Capabilities

#### Multiple Generation Modes:
- **Continue Melody**: Intelligently extends existing piano roll content
- **Create Variation**: Generates sophisticated variations of existing melodies
- **Start Fresh**: Creates entirely new melodies from scratch
- **Context-Aware**: Uses existing notes as context for better generation

#### Advanced Musical Parameters:
- **Scale Selection**: Complete support for major/minor scales with all root notes
- **Creativity Control**: Fine-tuned temperature parameter for AI model control
- **Seed Configuration**: Reproducible results with seed management
- **Length Control**: Precise control over generated sequence length
- **Style Parameters**: Advanced style control based on training data

### Technical Implementation

#### `ui/ai_studio_panel.py`
- **Purpose**: Complete AI Studio implementation including both UI and generation engine
- **Key Classes**:
  - `RealAIGenerator`: Embedded AI generation engine class
  - `AIGenerationWorker`: Background generation thread
  - `AIStudioPanel`: Main AI interface panel
- **Key Functions**:
  - Model discovery and loading from `ai_studio/models/`
  - AI inference with multiple generation modes
  - Context processing and preparation
  - Post-processing and note conversion
  - Modern UI with animations and feedback
  - Real-time progress indicators
  - Parameter configuration interface
  - Integration with main piano roll display

### AI Model Management

#### Model Directory Structure:
```text
ai_studio/models/
├── README.txt                      # Model installation instructions
├── alex_melody.pth                 # Primary melody generation model
└── Piano_Hands_Transformer_Trained_Model_2942_steps_*.pth # Piano transformer models
```

#### Model Requirements:
- **PyTorch Models**: Standard .pth format
- **Transformer Architecture**: x_transformer-based models
- **MIDI Training**: Models trained on MIDI data
- **Compatibility**: Python 3.8+ and PyTorch 1.9+

## 🔄 Enhanced Workflows

### AI-Powered Generation Workflow
1. **Model Initialization**: AI Studio automatically loads available models
2. **Context Analysis**: Existing piano roll content is analyzed for context
3. **Parameter Configuration**: User sets generation parameters (scale, creativity, length)
4. **Background Generation**: AI model generates notes in separate thread
5. **Real-time Integration**: Generated notes appear immediately on piano roll
6. **Playback Integration**: Notes are automatically loaded into MIDI player

### Traditional Plugin Workflow
1. **Plugin Discovery**: Plugin Manager scans for traditional plugins
2. **Parameter Configuration**: User configures plugin-specific parameters
3. **Note Generation**: Plugin generates notes using traditional algorithms
4. **Piano Roll Integration**: Notes are displayed and integrated
5. **Playback and Export**: Standard playback and MIDI export capabilities

### Hybrid Workflow (NEW)
1. **Initial Generation**: Use traditional plugins or AI for base melody
2. **AI Enhancement**: Use AI Studio to create variations or extensions
3. **Iterative Refinement**: Combine multiple generation approaches
4. **Professional Output**: Export final composition to MIDI

## 🎨 UI Enhancements

### Modern Interface Elements
- **ModernButton**: Animated buttons with hover effects and visual feedback
- **ModernSlider**: Smooth sliders with value indicators and animations
- **Enhanced Color Scheme**: Professional dark theme with accent colors
- **Visual Feedback**: Real-time feedback for all user interactions
- **Responsive Layout**: Adaptive layouts for different screen sizes

### Dockable Panel System
- **AI Studio Panel**: Fully dockable with position memory
- **Plugin Manager Panel**: Enhanced with better organization
- **Flexible Workspace**: Users can arrange panels according to preference
- **Window State Management**: Automatic saving and restoration of window layouts

### Real-time Feedback Systems
- **Progress Indicators**: Visual progress for AI generation and plugin execution
- **Status Updates**: Real-time status information displayed in UI
- **Error Handling**: User-friendly error messages with recovery suggestions
- **Performance Monitoring**: Real-time performance feedback for resource usage

## 🛠️ Technical Improvements

### Startup Optimizations
- **Audio Initialization**: Improved FluidSynth initialization to prevent audio artifacts
- **SDL Configuration**: Pre-configured audio settings for optimal performance
- **Dependency Loading**: Intelligent dependency loading with fallbacks
- **Error Recovery**: Robust error handling during application startup

### Enhanced Dependency Management
- **Dynamic Loading**: AI dependencies loaded only when needed
- **Graceful Fallbacks**: Application functions without AI when dependencies missing
- **Version Compatibility**: Automatic compatibility checking for dependencies
- **Installation Guidance**: Clear instructions for missing dependencies

### Performance Enhancements
- **Background Processing**: All generation operations run in background threads
- **Memory Management**: Optimized memory usage for large models and sequences
- **Cache System**: Intelligent caching for frequently used models and data
- **Resource Monitoring**: Real-time monitoring of CPU, memory, and GPU usage

## 📋 System Requirements

### Technical Requirements
- **Python**: 3.10 or higher (specifically optimized for Python 3.10)
- **Operating System**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Memory**: 4GB RAM minimum, 8GB recommended for AI features
- **Storage**: 2GB free space for models and audio samples
- **Audio**: DirectSound (Windows), CoreAudio (macOS), ALSA (Linux)

### Dependencies Overview
Core dependencies are managed through `requirements.txt` and the automated installation scripts. The project uses a virtual environment structure named `pythonpackages/`.

### Optional AI Requirements
- **GPU Support**: NVIDIA GPU with CUDA 11.0+ for accelerated AI generation
- **Apple Silicon**: MPS support for M1/M2 Macs
- **Model Storage**: Additional 1-5GB for AI model files

## 📝 Installation

For complete installation instructions, please refer to **[INSTALLATION.md](INSTALLATION.md)** which covers:
- Windows Portable Version (Recommended)
- Source Installation (All Platforms)
- Manual Installation
- Troubleshooting
- Platform-specific setup guides

## 🧪 Testing and Quality Assurance

### Core Functionality Testing
- **Application Startup**: Verify clean startup without errors using `start.bat`/`start.sh`
- **Piano Roll Display**: Test note visualization and interaction
- **MIDI Playback**: Verify audio output and timing accuracy with FluidSynth
- **Plugin System**: Test all traditional plugins with various parameters
- **MIDI Export**: Validate exported MIDI file integrity

### AI Studio Testing
- **Model Loading**: Verify AI models load correctly from `ai_studio/models/`
- **Generation Modes**: Test all generation modes (continue, variation, fresh)
- **Parameter Control**: Verify all AI parameters affect output appropriately
- **Performance**: Test generation speed and resource usage
- **Error Handling**: Test behavior with missing models or dependencies

### Integration Testing
- **Cross-Panel Communication**: Test data flow between panels
- **Hybrid Workflows**: Test combining traditional and AI generation
- **State Management**: Verify application state persistence
- **Export Integration**: Test export of AI-generated content

## 🔧 Technical Notes

For installation, setup, and troubleshooting information, please refer to **[INSTALLATION.md](INSTALLATION.md)**.

### Key Technical Points
- **FluidSynth Integration**: Advanced audio synthesis with SoundFont support
- **AI Model Loading**: Dynamic model discovery and loading from `ai_studio/models/`
- **Plugin Architecture**: Extensible plugin system with hot-loading capabilities
- **Cross-Platform Support**: Unified codebase supporting Windows, Linux, and macOS

## 📚 Documentation Structure

### User Documentation
- **Getting Started Guide**: Step-by-step tutorial for new users
- **Feature Reference**: Comprehensive feature documentation
- **AI Studio Guide**: Detailed guide for AI features
- **Plugin Development**: Guide for creating custom plugins

### Developer Documentation
- **Architecture Overview**: Detailed system architecture documentation
- **API Reference**: Complete API documentation for all classes
- **Plugin Development Kit**: Tools and templates for plugin development
- **AI Model Integration**: Guide for integrating new AI models

### Troubleshooting
- **Common Issues**: Solutions for frequently encountered problems
- **Dependency Issues**: Troubleshooting for missing dependencies
- **Performance Optimization**: Guide for optimizing performance
- **Audio Configuration**: Audio system configuration guide

## 🔮 Future Roadmap

### Immediate Enhancements (Next Release)
- **Multi-track Support**: Support for multiple MIDI tracks
- **Advanced Note Editing**: In-place note editing and manipulation
- **Additional AI Models**: Support for more specialized AI models
- **Performance Optimizations**: Further performance improvements

### Medium-term Goals
- **VST/AU Integration**: Support for external audio plugins
- **Cloud Model Storage**: Cloud-based model storage and sharing
- **Collaborative Features**: Real-time collaboration capabilities
- **Advanced Export Options**: Support for more export formats

### Long-term Vision
- **DAW Integration**: Deep integration with popular DAWs
- **AI Training Interface**: Tools for training custom models
- **Music Theory Integration**: Advanced music theory features
- **Cross-platform Mobile**: Mobile app development

## 📄 License Information

This project is licensed under a custom Non-Commercial Software License. See the [LICENSE](LICENSE) file for complete details.

### Key License Terms:
- ✅ **Personal Use**: Free for personal and educational use
- ✅ **Modification**: You may modify the software for personal use
- ✅ **Distribution**: You may distribute modifications with attribution
- ❌ **Commercial Use**: Commercial use requires explicit permission
- ℹ️ **Attribution**: Credit to original author (Jonas) required
- ℹ️ **Notification**: Must notify copyright holder of distribution

## 🤝 Contributing

### Contributing Guidelines
1. **Fork** the repository at [https://github.com/WebChatAppAi/midi-gen](https://github.com/WebChatAppAi/midi-gen)
2. **Setup** development environment following **[INSTALLATION.md](INSTALLATION.md)**
3. **Create** a feature branch
4. **Implement** your changes with tests
5. **Document** your changes thoroughly
6. **Submit** a pull request with detailed description

### Areas for Contribution
- **Plugin Development**: Create new traditional plugins in `plugins/` directory
- **AI Model Integration**: Add support for new AI models in `ai_studio/`
- **UI Enhancements**: Improve user interface and experience in `ui/`
- **Performance Optimization**: Optimize performance and resource usage
- **Documentation**: Improve and expand documentation in `docs/`
- **Testing**: Add comprehensive tests for all features

### Code Standards
- **Python Style**: Follow PEP 8 guidelines
- **Python Version**: Ensure compatibility with Python 3.10+
- **Documentation**: Comprehensive docstrings for all functions
- **Testing**: Unit tests for all new functionality
- **Virtual Environment**: Use the `pythonpackages/` structure
- **Cross-Platform**: Ensure compatibility across Windows, Linux, and macOS

---

**Piano Roll Studio** - Where traditional music generation meets cutting-edge AI technology. Create, compose, and innovate with the power of both algorithmic and artificial intelligence.

---

> **Note**: This document focuses on technical project details and architecture. For installation instructions, setup guides, and troubleshooting, please refer to [INSTALLATION.md](INSTALLATION.md).
