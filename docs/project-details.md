# MIDI Generator Piano Roll Project Details

## Project Overview

This project is a plugin-based MIDI generator system that integrates with a custom piano roll GUI. The system allows users to generate MIDI notes using various algorithms encapsulated in plugins, visualize them on a piano roll, play them back, and export them to MIDI files.

## System Architecture

The architecture follows a modular plugin-based design:

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│                 │     │                   │     │                 │
│  Piano Roll UI  │◄────┤  Plugin Manager   │◄────┤  Plugin System  │
│                 │     │                   │     │                 │
└────────┬────────┘     └───────────────────┘     └────────┬────────┘
         │                                                 │
         │                                                 │
         ▼                                                 ▼
┌─────────────────┐                               ┌─────────────────┐
│                 │                               │                 │
│  Note Display   │                               │  MIDI Export    │
│                 │                               │                 │
└─────────────────┘                               └─────────────────┘
```

- **Piano Roll UI**: The main application window with transport controls and visualization
- **Plugin Manager**: Discovers, loads, and manages MIDI generator plugins
- **Plugin System**: Provides the base API for creating plugins
- **Note Display**: Renders MIDI notes on a piano roll
- **MIDI Export**: Exports generated notes to standard MIDI files

## Project Structure

```
piano_roll_project/
├── app.py                     # Main application entry point
├── note_display.py            # Piano roll grid and note visualization (QWidget)
├── midi_player.py             # Facade for MIDI playback
├── plugin_manager.py          # Plugin discovery and management system
├── plugin_api.py              # Base classes and API for plugins
├── export_utils.py            # MIDI export functionality
├── start.bat                  # Windows startup script
├── start.sh                   # Linux/macOS startup script
├── config/
│   ├── __init__.py
│   ├── constants.py
│   └── theme.py
├── ui/
│   ├── __init__.py
│   ├── custom_widgets.py      # ModernSlider, ModernButton
│   ├── drawing_utils.py       # PianoRollDisplay drawing functions
│   ├── event_handlers.py      # MainWindowEventHandlersMixin
│   ├── main_window.py         # PianoRollMainWindow (QMainWindow)
│   ├── plugin_dialogs.py      # PluginParameterDialog
│   └── plugin_panel.py        # PluginManagerPanel (QDockWidget)
├── midi/
│   ├── __init__.py
│   ├── device_manager.py
│   ├── midi_event_utils.py
│   ├── note_scheduler.py
│   └── playback_controller.py
├── plugins/
│   ├── __init__.py
│   ├── markov_generator.py
│   ├── melody_generator.py
│   └── motif_generator.py
└── docs/
    ├── project-details.md     # This file
    └── plugin-docs.md         # Documentation for plugin developers
```

## File Details

### Core Files

#### `app.py`
- **Purpose**: Application entry point
- **Key Functions**: 
  - Initializes QApplication
  - Sets application style
  - Creates and shows the main application window (`PianoRollMainWindow` from `ui.main_window`)
  - Runs the application event loop

#### `ui/main_window.py` (formerly parts of `piano_roll.py`)
- **Purpose**: Main application window (`PianoRollMainWindow`)
- **Key Classes**:
  - `PianoRollMainWindow`: Main window with piano roll display and transport controls
  - `PluginManagerPanel`: Dockable panel for plugin management
  - `PluginParameterDialog`: Dialog for configuring plugin parameters
  - `ModernSlider` and `ModernButton`: Custom UI elements for better appearance
- **Key Functions**:
  - Transport controls (play, pause, stop)
  - MIDI note management
  - Time and position tracking
  - Integration with plugin manager

#### `note_display.py`
- **Purpose**: Piano roll grid and note visualization
- **Key Classes**:
  - `PianoRollDisplay`: Widget that displays MIDI notes graphically
- **Key Functions**:
  - Draw piano keyboard
  - Draw time grid with bars and beats
  - Draw MIDI notes with color-coding
  - Draw playhead
  - Handle mouse interactions

#### `midi_player.py`
- **Purpose**: MIDI playback implementation
- **Not Shown in Provided Code**: This file needs to implement MIDI playback functionality
- **Key Functions**:
  - Play, pause, stop MIDI notes
  - Set playback tempo
  - Get current playback position
  - Seek to position

### Plugin System Files

#### `plugin_api.py`
- **Purpose**: Defines the plugin API and base classes
- **Key Classes**:
  - `PluginBase`: Abstract base class for all plugins
- **Key Functions**:
  - `generate()`: Core method to generate MIDI notes
  - `get_parameter_info()`: Returns plugin parameter information
  - `validate_parameters()`: Validates parameter values

#### `plugin_manager.py`
- **Purpose**: Discovers, loads, and manages plugins
- **Key Classes**:
  - `PluginManager`: Manages plugin discovery and execution
- **Key Functions**:
  - `discover_plugins()`: Finds plugins in the plugins directory
  - `load_plugin()`: Loads a plugin from a module
  - `get_plugin_list()`: Returns a list of available plugins
  - `generate_notes()`: Generates notes using a specific plugin

#### `export_utils.py`
- **Purpose**: Provides MIDI export functionality
- **Key Functions**:
  - `export_to_midi()`: Exports notes to a MIDI file

### Plugin Files

#### `plugins/motif_generator.py`
- **Purpose**: Example plugin that generates melodies based on motifs
- **Key Classes**:
  - `MotifGenerator`: Plugin implementation
- **Key Functions**:
  - `_create_motif()`: Creates a musical motif
  - `_create_variation()`: Creates variations of a motif
  - `generate()`: Generates a melody based on motifs and variations

#### `plugins/markov_generator.py`
- **Purpose**: Example plugin that generates melodies using Markov chains
- **Key Classes**:
  - `MarkovGenerator`: Plugin implementation
- **Key Functions**:
  - `_build_transition_matrix()`: Builds a Markov transition matrix
  - `_choose_next_note()`: Selects the next note based on transition probabilities
  - `generate()`: Generates a melody using Markov chains

#### `plugins/melody_generator.py`
- **Purpose**: Emotional melody generator inspired by FL Studio script
- **Key Classes**:
  - `MelodyGenerator`: Plugin implementation
- **Key Functions**:
  - `_get_scale_notes()`: Gets notes in a scale
  - `_apply_emotion_contour()`: Applies emotional contour to a melody
  - `_generate_random_walk()`: Generates random walk patterns
  - `generate()`: Generates an emotional melody

## Key Components and Workflows

### Plugin Loading Process
1. `PluginManager` scans the `plugins` directory for Python files
2. For each file, it imports the module and looks for classes that inherit from `PluginBase`
3. It creates instances of these classes and adds them to the list of available plugins

### Note Generation Process
1. User selects a plugin from the list in the Plugin Manager panel
2. User configures plugin parameters using the Configure button
3. User clicks Generate to generate notes
4. The selected plugin's `generate()` method is called with the specified parameters
5. The generated notes are added to the piano roll display and MIDI player

### MIDI Playback Process
1. Notes are added to the `midi_player` 
2. User clicks Play to start playback
3. The playback timer regularly updates the playhead position
4. The piano roll display shows the current playback position

### MIDI Export Process
1. User clicks Export MIDI in the Plugin Manager panel
2. User selects a destination file
3. The `export_to_midi()` function is called to export the notes to a MIDI file

## Contribution Guidelines

### Adding New Plugins
1. Create a new Python file in the `plugins` directory
2. Define a class that inherits from `PluginBase`
3. Implement the required methods, especially `generate()`
4. Define parameters using the standard parameter format
5. Test your plugin with different parameter values

### Enhancing Existing Plugins
1. Improve generation algorithms for better musical results
2. Add new parameters for more control
3. Optimize performance for faster generation
4. Add support for more musical features (e.g., chords, harmonies)

### Improving Core Functionality
1. Enhance the piano roll display for better visualization
2. Improve MIDI playback for more accurate timing
3. Add support for more MIDI features (e.g., control changes, program changes)
4. Implement additional export formats
5. Add support for loading existing MIDI files

## Future Enhancement Ideas

### Plugin System Enhancements
- Plugin categories and tags for better organization
- Plugin dependency management
- Plugin versioning and compatibility checking
- Plugin marketplace for sharing and downloading plugins

### UI Enhancements
- Themes and color schemes
- Customizable keyboard shortcuts
- Multi-track support
- Zoom and navigation improvements
- Note editing tools

### Generation Enhancements
- AI-based generation using machine learning models
- Style transfer between different musical genres
- Chord progression generation
- Drum pattern generation
- Bass line generation
- Multi-instrument arrangement

### Integration Enhancements
- VST/AU plugin support
- DAW integration (ReWire, MIDI routing)
- Real-time MIDI input/output
- Cloud storage integration

## Development Environment

### Requirements
- Python 3.8 or higher
- PySide6 for the GUI
- pretty_midi for MIDI processing
- Additional libraries as needed by specific plugins

### Setting Up Development Environment
1. Clone the repository
2. Install dependencies: `pip install PySide6 pretty_midi numpy pygame` (pygame is used by midi_player)
3. Run the application:
   - Using the script: `python app.py`
   - On Windows: `start.bat`
   - On Linux/macOS: `sh start.sh` or `./start.sh` (after `chmod +x start.sh`)

## Testing

When contributing new features or plugins, ensure:
1. The application runs without errors
2. The piano roll display works correctly
3. MIDI playback functions properly
4. Plugins generate valid notes
5. MIDI export produces valid files

## License

This project is open-source and available under the MIT License. See the LICENSE file for details.
