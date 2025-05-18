from PySide6.QtWidgets import (
    QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox, 
    QComboBox, QCheckBox, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt

class PluginParameterDialog(QDialog):
    """Dialog for configuring plugin parameters"""
    
    def __init__(self, plugin, current_params=None, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.params = current_params or {}
        self.param_widgets = {}
        
        self.setWindowTitle(f"Configure {plugin.get_name()}")
        self.resize(400, 300)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create form layout for parameters
        form_layout = QFormLayout()
        
        # Add parameter widgets
        param_info = plugin.get_parameter_info()
        for param_name, param_config in param_info.items():
            # Create widget based on parameter type
            widget = self._create_param_widget(param_name, param_config)
            if widget:
                form_layout.addRow(param_config.get("description", param_name), widget)
                self.param_widgets[param_name] = widget
        
        layout.addLayout(form_layout)
        
        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_param_widget(self, param_name, param_config):
        """Create a widget for the parameter based on its type"""
        param_type = param_config.get("type", "str")
        current_value = self.params.get(param_name, param_config.get("default"))
        
        if param_type == "int":
            widget = QSpinBox()
            widget.setMinimum(param_config.get("min", 0))
            widget.setMaximum(param_config.get("max", 100))
            widget.setValue(current_value or param_config.get("default", 0))
            return widget
        
        elif param_type == "float":
            widget = QDoubleSpinBox()
            widget.setMinimum(param_config.get("min", 0.0))
            widget.setMaximum(param_config.get("max", 1.0))
            widget.setSingleStep(0.1)
            widget.setDecimals(2)
            widget.setValue(current_value or param_config.get("default", 0.0))
            return widget
        
        elif param_type == "bool":
            widget = QCheckBox()
            widget.setChecked(current_value if current_value is not None else param_config.get("default", False))
            return widget
        
        elif param_type == "list":
            widget = QComboBox()
            options = param_config.get("options", [])
            widget.addItems(options)
            
            # Set current value
            if current_value:
                index = options.index(current_value) if current_value in options else 0
                widget.setCurrentIndex(index)
            else:
                default_value = param_config.get("default")
                index = options.index(default_value) if default_value in options else 0
                widget.setCurrentIndex(index)
            
            return widget
        
        elif param_type == "str":
            # Default to combobox if options provided, otherwise could use QLineEdit
            if "options" in param_config:
                widget = QComboBox()
                options = param_config.get("options", [])
                widget.addItems(options)
                
                # Set current value
                if current_value:
                    index = options.index(current_value) if current_value in options else 0
                    widget.setCurrentIndex(index)
                else:
                    default_value = param_config.get("default")
                    index = options.index(default_value) if default_value in options else 0
                    widget.setCurrentIndex(index)
                
                return widget
        
        return None
    
    def get_parameter_values(self):
        """Get the current parameter values from the widgets"""
        values = {}
        
        for param_name, widget in self.param_widgets.items():
            param_info = self.plugin.get_parameter_info().get(param_name, {})
            param_type = param_info.get("type", "str")
            
            if param_type == "int":
                values[param_name] = widget.value()
            elif param_type == "float":
                values[param_name] = widget.value()
            elif param_type == "bool":
                values[param_name] = widget.isChecked()
            elif param_type == "list" or param_type == "str":
                if isinstance(widget, QComboBox):
                    values[param_name] = widget.currentText()
            
        return values
