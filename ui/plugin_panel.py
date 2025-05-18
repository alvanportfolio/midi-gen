from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QDockWidget, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QDialog
)
from PySide6.QtCore import Qt, Signal

from plugin_manager import PluginManager
from export_utils import export_to_midi
from ui.plugin_dialogs import PluginParameterDialog # Assuming PluginParameterDialog is in plugin_dialogs

class PluginManagerPanel(QDockWidget):
    """Dockable panel for managing plugins"""
    
    # Signal emitted when a plugin generates notes
    notesGenerated = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__("Plugin Manager", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        # Create plugin manager
        self.plugin_manager = PluginManager()
        
        # Create widget for the dock
        self.dock_content = QWidget()
        self.setWidget(self.dock_content)
        
        # Create layout
        layout = QVBoxLayout(self.dock_content)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Add plugin list
        self.plugin_list = QListWidget()
        self.plugin_list.setStyleSheet("""
            QListWidget {
                background-color: #1c1c20;
                color: #e0e0e0;
                border: 1px solid #3a3a45;
                border-radius: 4px;
            }
            
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3a3a45;
            }
            
            QListWidget::item:selected {
                background-color: #3a3a60;
            }
            
            QListWidget::item:hover {
                background-color: #2a2a30;
            }
        """)
        layout.addWidget(self.plugin_list)
        
        # Load plugins
        self._load_plugins()
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.configure_button = QPushButton("Configure")
        self.configure_button.clicked.connect(self._configure_plugin)
        button_layout.addWidget(self.configure_button)
        
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self._generate_notes)
        button_layout.addWidget(self.generate_button)
        
        self.export_button = QPushButton("Export MIDI")
        self.export_button.clicked.connect(self._export_midi)
        button_layout.addWidget(self.export_button)
        
        layout.addLayout(button_layout)
        
        # Store plugin parameters
        self.plugin_params = {}
        
        # Store current notes
        self.current_notes = []
    
    def _load_plugins(self):
        """Load plugins into the list widget"""
        self.plugin_list.clear()
        
        for plugin_info in self.plugin_manager.get_plugin_list():
            item = QListWidgetItem(f"{plugin_info['name']} v{plugin_info['version']}")
            item.setData(Qt.UserRole, plugin_info['id'])
            item.setToolTip(plugin_info['description'])
            self.plugin_list.addItem(item)
    
    def set_current_notes(self, notes):
        """Set the current notes for use with plugins"""
        self.current_notes = notes
    
    def _configure_plugin(self):
        """Configure the selected plugin"""
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            return
        
        plugin_id = selected_items[0].data(Qt.UserRole)
        plugin = self.plugin_manager.get_plugin(plugin_id)
        
        if not plugin:
            return
        
        # Get current parameters for this plugin
        current_params = self.plugin_params.get(plugin_id, {})
        
        # Create and show parameter dialog
        dialog = PluginParameterDialog(plugin, current_params, self)
        if dialog.exec() == QDialog.Accepted:
            # Store parameters
            params = dialog.get_parameter_values()
            self.plugin_params[plugin_id] = params
    
    def _generate_notes(self):
        """Generate notes using the selected plugin"""
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Plugin Selected", "Please select a plugin from the list.")
            return
        
        plugin_id = selected_items[0].data(Qt.UserRole)
        parameters = self.plugin_params.get(plugin_id, {})
        
        try:
            # Generate notes
            generated_notes = self.plugin_manager.generate_notes(
                plugin_id, 
                existing_notes=self.current_notes,
                parameters=parameters
            )
            
            # Emit signal with generated notes
            self.notesGenerated.emit(generated_notes)
            
            # Update current notes (the main window will also do this via the signal)
            self.current_notes = generated_notes 
            
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Error generating notes: {str(e)}")
    
    def _export_midi(self):
        """Export current notes to a MIDI file"""
        if not self.current_notes:
            QMessageBox.warning(self, "No Notes", "There are no notes to export.")
            return
        
        # Get file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export MIDI", "", "MIDI Files (*.mid);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Add .mid extension if not present
        if not file_path.lower().endswith('.mid'):
            file_path += '.mid'
        
        try:
            # Export notes
            export_to_midi(self.current_notes, file_path)
            QMessageBox.information(self, "Export Successful", f"MIDI file exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting MIDI file: {str(e)}")
