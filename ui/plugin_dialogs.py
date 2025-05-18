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
        self.setMinimumWidth(450) # Increased min width
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog) # For custom border, but can be tricky
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # Remove margins for custom header/footer
        main_layout.setSpacing(0)

        # --- Dialog Styling ---
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.DIALOG_BG_COLOR.name()};
                border-radius: {theme.BORDER_RADIUS + 2}px; /* Slightly larger for dialog window */
                color: {theme.PRIMARY_TEXT_COLOR.name()};
            }}
            QLabel {{
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-family: "{theme.FONT_FAMILY}";
                font-size: {theme.FONT_SIZE_NORMAL}pt;
            }}
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
                background-color: {theme.INPUT_BG_COLOR.name()};
                color: {theme.INPUT_TEXT_COLOR.name()};
                border: 1px solid {theme.INPUT_BORDER_COLOR.name()};
                border-radius: {theme.BORDER_RADIUS}px;
                padding: {theme.PADDING_SMALL +1}px {theme.PADDING_SMALL + 2}px;
                font-family: "{theme.FONT_FAMILY}";
                font-size: {theme.FONT_SIZE_NORMAL}pt;
                min-height: {theme.FONT_SIZE_NORMAL + 18}px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {{
                border: 1px solid {theme.INPUT_SELECTED_BORDER_COLOR.name()};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {theme.INPUT_BORDER_COLOR.name()};
                border-left-style: solid;
                border-top-right-radius: {theme.BORDER_RADIUS}px;
                border-bottom-right-radius: {theme.BORDER_RADIUS}px;
            }}
            QComboBox::down-arrow {{
                /* image: url(./assets/icons/chevron-down.svg); Removed to prevent warnings */
                /* Qt will use a default arrow */
                width: 12px; /* Still useful to size the default arrow area */
                height: 12px;
            }}
             QComboBox QAbstractItemView {{ /* Dropdown list style */
                background-color: {theme.INPUT_BG_COLOR.name()};
                border: 1px solid {theme.INPUT_SELECTED_BORDER_COLOR.name()};
                selection-background-color: {theme.ACCENT_COLOR.name()};
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                padding: {theme.PADDING_SMALL}px;
            }}
            QCheckBox {{
                spacing: {theme.PADDING_SMALL}px;
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                font-family: "{theme.FONT_FAMILY}";
                font-size: {theme.FONT_SIZE_NORMAL}pt;
            }}
            QCheckBox::indicator {{
                width: {theme.ICON_SIZE}px;
                height: {theme.ICON_SIZE}px;
                border: 1px solid {theme.INPUT_BORDER_COLOR.name()};
                border-radius: {theme.BORDER_RADIUS // 2}px;
                background-color: {theme.INPUT_BG_COLOR.name()};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme.ACCENT_COLOR.name()};
                /* image: url(./assets/icons/check.svg); Removed to prevent warnings */
                /* A colored background for checked state is often sufficient */
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {theme.ACCENT_COLOR.name()};
            }}
        """)
        
        # --- Header ---
        header_widget = QWidget()
        header_widget.setFixedHeight(60)
        header_widget.setStyleSheet(f"background-color: {theme.BG_COLOR.darker(110).name()}; border-top-left-radius: {theme.BORDER_RADIUS+2}px; border-top-right-radius: {theme.BORDER_RADIUS+2}px; padding: 0 {theme.PADDING_LARGE}px;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(theme.PADDING_MEDIUM, 0, theme.PADDING_MEDIUM, 0)

        plugin_icon_label = QLabel(self._get_plugin_icon(plugin.get_name()))
        plugin_icon_label.setFont(QFont(theme.FONT_FAMILY, theme.PLUGIN_ICON_SIZE))
        header_layout.addWidget(plugin_icon_label)

        title_label = QLabel(plugin.get_name())
        title_label.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_LARGE + 2, weight=QFont.Bold if theme.FONT_WEIGHT_BOLD == "bold" else QFont.Normal))
        title_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addWidget(header_widget)

        # --- Content Area (Form) ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(theme.PADDING_LARGE, theme.PADDING_MEDIUM, theme.PADDING_LARGE, theme.PADDING_MEDIUM)
        content_layout.setSpacing(theme.PADDING_MEDIUM)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(theme.PADDING_MEDIUM)
        form_layout.setLabelAlignment(Qt.AlignRight) # Align labels to the right

        param_info = plugin.get_parameter_info()
        for param_name, param_config in param_info.items():
            widget = self._create_param_widget(param_name, param_config)
            if widget:
                label_text = param_config.get("description", param_name)
                label = QLabel(f"{label_text}:") # Add colon to labels
                form_layout.addRow(label, widget)
                self.param_widgets[param_name] = widget
        
        content_layout.addLayout(form_layout)
        main_layout.addWidget(content_widget, 1) # Add stretch factor

        # --- Footer (Buttons) ---
        footer_widget = QWidget()
        footer_widget.setStyleSheet(f"background-color: {theme.BG_COLOR.darker(110).name()}; border-bottom-left-radius: {theme.BORDER_RADIUS+2}px; border-bottom-right-radius: {theme.BORDER_RADIUS+2}px; padding: {theme.PADDING_MEDIUM}px {theme.PADDING_LARGE}px;")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0,0,0,0)
        footer_layout.addStretch()

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
            elif param_type == "list" or param_type == "str":
                if isinstance(widget, QComboBox):
                    values[param_name] = widget.currentText()
            
        return values
