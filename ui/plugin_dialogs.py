from PySide6.QtWidgets import (
    QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QDialog, QDialogButtonBox, QLabel, QHBoxLayout, QFrame, QLineEdit, QWidget # Added QWidget
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QShowEvent # Added QShowEvent for type hint
from config import theme
from ui.custom_widgets import ModernButton # Import ModernButton

class PluginParameterDialog(QDialog):
    """Dialog for configuring plugin parameters with modern styling."""
    
    def __init__(self, plugin, current_params=None, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.params = current_params or {}
        self.param_widgets = {}
        
        self.setWindowTitle(f"Configure: {plugin.get_name()}")
        self.setMinimumWidth(450)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) 
        main_layout.setSpacing(0)

        # Define min_height for form elements based on font and padding
        # Example: theme.FONT_SIZE_M (9) + theme.PADDING_S (4) * 2 for top/bottom + 2 for borders = 9 + 8 + 2 = 19.
        # Let's use a slightly more generous calculation for visual comfort.
        form_element_min_height = theme.FONT_SIZE_M + theme.PADDING_S * 2 + 6 


        # --- Dialog Styling ---
        self.setStyleSheet(f"""
            QDialog#PluginParameterDialog {{ /* Object name selector for the dialog itself */
                background-color: {theme.DIALOG_BG_COLOR.name()};
                border-radius: {theme.BORDER_RADIUS_L}px; 
                color: {theme.PRIMARY_TEXT_COLOR.name()};
            }}
            QWidget#header_widget {{
                background-color: {theme.PANEL_BG_COLOR.lighter(110).name()}; /* Distinct header color */
                border-top-left-radius: {theme.BORDER_RADIUS_L}px;
                border-top-right-radius: {theme.BORDER_RADIUS_L}px;
                padding: {theme.PADDING_M}px;
                border-bottom: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
            }}
            QLabel#plugin_icon_label {{
                font-size: {theme.ICON_SIZE_XL}pt; /* Using pt for font-based icons */
                color: {theme.PRIMARY_TEXT_COLOR.name()};
            }}
            QLabel#title_label {{
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_XL}pt;
                font-weight: {theme.FONT_WEIGHT_BOLD};
            }}
             QWidget#content_widget {{
                /* No specific background, inherits from QDialog */
            }}
            QWidget#footer_widget {{
                background-color: {theme.PANEL_BG_COLOR.lighter(110).name()}; /* Same as header */
                border-bottom-left-radius: {theme.BORDER_RADIUS_L}px;
                border-bottom-right-radius: {theme.BORDER_RADIUS_L}px;
                padding: {theme.PADDING_M}px;
                border-top: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
            }}

            /* Form Element Styling within PluginParameterDialog */
            PluginParameterDialog QLabel {{ /* Parameter labels */
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_M}pt;
                padding-top: {theme.PADDING_S}px; /* Align with input field text */
            }}
            PluginParameterDialog QSpinBox, 
            PluginParameterDialog QDoubleSpinBox, 
            PluginParameterDialog QComboBox, 
            PluginParameterDialog QLineEdit {{
                background-color: {theme.INPUT_BG_COLOR.name()};
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                border: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
                border-radius: {theme.BORDER_RADIUS_M}px;
                padding: {theme.PADDING_S}px {theme.PADDING_M}px;
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_M}pt;
                min-height: {form_element_min_height}px;
            }}
            PluginParameterDialog QSpinBox:focus, 
            PluginParameterDialog QDoubleSpinBox:focus, 
            PluginParameterDialog QComboBox:focus, 
            PluginParameterDialog QLineEdit:focus {{
                border: 1px solid {theme.BORDER_COLOR_FOCUSED.name()};
                /* Optional: Add a subtle glow or outline if supported and desired */
                /* outline: 1px solid {theme.BORDER_COLOR_FOCUSED.lighter(150).name()}; */
            }}
            PluginParameterDialog QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {theme.ICON_SIZE_L}px; /* Width for the dropdown area */
                border-left-width: 1px;
                border-left-color: {theme.BORDER_COLOR_NORMAL.name()};
                border-left-style: solid;
                border-top-right-radius: {theme.BORDER_RADIUS_M}px;
                border-bottom-right-radius: {theme.BORDER_RADIUS_M}px;
            }}
            PluginParameterDialog QComboBox::down-arrow {{
                /* Default arrow should be fine. If custom SVG: image: url({theme.DROPDOWN_ICON_PATH}); */
                width: {theme.ICON_SIZE_S}px; 
                height: {theme.ICON_SIZE_S}px;
            }}
            PluginParameterDialog QComboBox QAbstractItemView {{ /* Dropdown list style */
                background-color: {theme.PANEL_BG_COLOR.name()}; /* Slightly different from input for distinction */
                border: 1px solid {theme.BORDER_COLOR_FOCUSED.name()};
                selection-background-color: {theme.ACCENT_PRIMARY_COLOR.name()};
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                padding: {theme.PADDING_S}px;
            }}
            PluginParameterDialog QCheckBox {{
                spacing: {theme.PADDING_S}px;
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-family: "{theme.FONT_FAMILY_PRIMARY}";
                font-size: {theme.FONT_SIZE_M}pt;
            }}
            PluginParameterDialog QCheckBox::indicator {{
                width: {theme.ICON_SIZE_M}px;
                height: {theme.ICON_SIZE_M}px;
                border: 1px solid {theme.BORDER_COLOR_NORMAL.name()};
                border-radius: {theme.BORDER_RADIUS_S}px;
                background-color: {theme.INPUT_BG_COLOR.name()};
            }}
            PluginParameterDialog QCheckBox::indicator:checked {{
                background-color: {theme.ACCENT_PRIMARY_COLOR.name()};
                border: 1px solid {theme.ACCENT_PRIMARY_COLOR.darker(120).name()};
                /* If custom SVG: image: url({theme.CHECKMARK_ICON_PATH}); */
            }}
            PluginParameterDialog QCheckBox::indicator:hover {{
                border: 1px solid {theme.ACCENT_PRIMARY_COLOR.name()};
            }}
        """)
        self.setObjectName("PluginParameterDialog") # For QDialog specific styling
        
        # --- Header ---
        header_widget = QWidget()
        header_widget.setObjectName("header_widget") # For QSS
        header_widget.setFixedHeight(60) # Keep fixed height or use dynamic based on content + padding
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(theme.PADDING_L, 0, theme.PADDING_L, 0) # Adjusted for consistent padding

        plugin_icon_label = QLabel(self._get_plugin_icon(plugin.get_name()))
        plugin_icon_label.setObjectName("plugin_icon_label")
        # Font size for emoji/text icon set in QSS
        header_layout.addWidget(plugin_icon_label)

        title_label = QLabel(plugin.get_name())
        title_label.setObjectName("title_label")
        # Font and color set in QSS
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addWidget(header_widget)

        # --- Content Area (Form) ---
        content_widget = QWidget()
        content_widget.setObjectName("content_widget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(theme.PADDING_L, theme.PADDING_L, theme.PADDING_L, theme.PADDING_L) # Consistent padding
        content_layout.setSpacing(theme.PADDING_L) # Spacing between elements in content
        
        form_layout = QFormLayout()
        form_layout.setSpacing(theme.PADDING_M) # Vertical spacing between rows
        form_layout.setHorizontalSpacing(theme.PADDING_L) # Horizontal spacing between label and widget
        form_layout.setLabelAlignment(Qt.AlignRight) 

        param_info = plugin.get_parameter_info()
        for param_name, param_config in param_info.items():
            widget = self._create_param_widget(param_name, param_config)
            if widget:
                label_text = param_config.get("description", param_name)
                label = QLabel(f"{label_text}:") 
                # Styling for these labels handled by "PluginParameterDialog QLabel" in QSS
                form_layout.addRow(label, widget)
                self.param_widgets[param_name] = widget
        
        content_layout.addLayout(form_layout)
        main_layout.addWidget(content_widget, 1) 

        # --- Footer (Buttons) ---
        footer_widget = QWidget()
        footer_widget.setObjectName("footer_widget") # For QSS
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(theme.PADDING_L, theme.PADDING_M, theme.PADDING_L, theme.PADDING_M) # Consistent padding
        footer_layout.addStretch()

        # ModernButton instances will pick up their styles from custom_widgets.py
        self.cancel_button = ModernButton("Cancel", tooltip="Discard changes")
        self.cancel_button.clicked.connect(self.reject)
        footer_layout.addWidget(self.cancel_button)

        self.ok_button = ModernButton("Apply", tooltip="Apply changes", accent=True)
        self.ok_button.setDefault(True) # Default button
        self.ok_button.clicked.connect(self.accept)
        footer_layout.addWidget(self.ok_button)
        
        main_layout.addWidget(footer_widget)

        # Optional: Fade-in animation
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(200) # ms
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        # self.opacity_animation.start() # Start animation on showEvent or init

    def showEvent(self, arg__1: QShowEvent): # Matched parameter name to Pylance expectation
        """Start fade-in animation when dialog is shown."""
        super().showEvent(arg__1)
        # Ensure window is not already fully opaque from a previous show
        current_opacity = self.windowOpacity()
        if current_opacity < 1.0:
             self.opacity_animation.setStartValue(current_opacity) # Start from current if partially visible
             self.opacity_animation.setEndValue(1.0)
             self.opacity_animation.start()
        elif self.opacity_animation.state() != QPropertyAnimation.Running: # Only start if not running and fully opaque
            self.setWindowOpacity(0.0) # Reset for animation if shown again
            self.opacity_animation.setStartValue(0.0)
            self.opacity_animation.setEndValue(1.0)
            self.opacity_animation.start()


    def _get_plugin_icon(self, plugin_name):
        """Returns an emoji icon based on plugin name (simple heuristic). Copied from PluginPanel."""
        name_lower = plugin_name.lower()
        if "markov" in name_lower or "chain" in name_lower:
            return "🧠"
        elif "melody" in name_lower or "generator" in name_lower:
            return "🎶"
        elif "motif" in name_lower or "sequence" in name_lower:
            return "🎼"
        elif "arp" in name_lower or "arpeggiator" in name_lower:
            return "🎹"
        elif "drum" in name_lower or "rhythm" in name_lower:
            return "🥁"
        return "🎛️"

    def _create_param_widget(self, param_name, param_config):
        """Create a styled widget for the parameter based on its type"""
        param_type = param_config.get("type", "str")
        current_value = self.params.get(param_name, param_config.get("default"))
        widget = None

        if param_type == "int":
            widget = QSpinBox()
            widget.setMinimum(param_config.get("min", 0))
            widget.setMaximum(param_config.get("max", 100))
            widget.setValue(current_value if current_value is not None else param_config.get("default", 0))
        
        elif param_type == "float":
            widget = QDoubleSpinBox()
            widget.setMinimum(param_config.get("min", 0.0))
            widget.setMaximum(param_config.get("max", 1.0))
            widget.setSingleStep(param_config.get("step", 0.1))
            widget.setDecimals(param_config.get("decimals", 2))
            widget.setValue(current_value if current_value is not None else param_config.get("default", 0.0))
        
        elif param_type == "bool":
            widget = QCheckBox()
            widget.setChecked(current_value if current_value is not None else param_config.get("default", False))
        
        elif param_type == "list" or (param_type == "str" and "options" in param_config):
            widget = QComboBox()
            options = param_config.get("options", [])
            widget.addItems([str(o) for o in options]) # Ensure options are strings
            
            val_to_set = current_value if current_value is not None else param_config.get("default")
            if val_to_set is not None:
                try:
                    index = options.index(val_to_set)
                    widget.setCurrentIndex(index)
                except ValueError: # If default/current value not in options
                    if options: widget.setCurrentIndex(0) 
            elif options: # If no current/default, select first if available
                 widget.setCurrentIndex(0)

        elif param_type == "str": # Fallback for string without options
            widget = QLineEdit()
            widget.setText(str(current_value) if current_value is not None else str(param_config.get("default", "")))
            placeholder = param_config.get("placeholder")
            if placeholder:
                widget.setPlaceholderText(str(placeholder))

        # Common styling for created widgets (already handled by dialog stylesheet)
        # if widget:
        #     widget.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL))
            
        return widget
    
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
            elif param_type == "list": # Explicitly for QComboBox from "list" type
                if isinstance(widget, QComboBox):
                    values[param_name] = widget.currentText()
                else:
                    print(f"Warning: Expected QComboBox for param '{param_name}' (type 'list') but got {type(widget)}. Skipping.")
            elif param_type == "str":
                if isinstance(widget, QComboBox): # "str" type with "options"
                    values[param_name] = widget.currentText()
                elif isinstance(widget, QLineEdit): # "str" type as free text
                    values[param_name] = widget.text()
                else:
                    print(f"Warning: Unknown widget type {type(widget)} for param '{param_name}' (type 'str'). Skipping.")
            else: # Fallback for unknown param_type
                print(f"Warning: Unknown parameter type '{param_type}' for param '{param_name}' with widget {type(widget)}. Skipping.")
            
        return values
