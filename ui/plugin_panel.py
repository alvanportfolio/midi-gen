import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QDockWidget, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QDialog, QLabel,
    QSizePolicy, QStyle # Import QSizePolicy and QStyle
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QFontMetrics # Import QFontMetrics

from plugin_manager import PluginManager
from export_utils import export_to_midi
from ui.plugin_dialogs import PluginParameterDialog
from config import theme

class PluginManagerPanel(QDockWidget):
    """Dockable panel for managing plugins"""
    
    notesGenerated = Signal(list) # Class attribute for the signal
    
    def __init__(self, parent=None):
        super().__init__("Plugin Manager", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        self.plugin_manager = PluginManager()
        
        self.dock_content = QWidget()
        self.setWidget(self.dock_content)
        
        main_panel_layout = QVBoxLayout(self.dock_content)
        main_panel_layout.setContentsMargins(theme.PADDING_MEDIUM, theme.PADDING_MEDIUM, theme.PADDING_MEDIUM, theme.PADDING_MEDIUM)
        main_panel_layout.setSpacing(theme.PADDING_MEDIUM)
        
        self.plugin_list = QListWidget()
        # Set size policy to expand vertically
        self.plugin_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plugin_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent; 
                border: none; 
                outline: 0; 
                spacing: {theme.PADDING_SMALL}px; 
            }}
            QListWidget::item {{ /* Item itself is just a container, no visual */
                border: none; 
                padding: 0px;
                margin-bottom: {theme.PADDING_SMALL}px;
            }}
            /* Remove item:selected and item:hover, as item_widget handles visuals */
            QListWidget::item:selected {{ background-color: transparent; }}
            QListWidget::item:hover {{ background-color: transparent; }}
        """)
        main_panel_layout.addWidget(self.plugin_list)
        
        self.plugin_list.currentItemChanged.connect(self._on_plugin_selection_changed)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.configure_button = QPushButton("Configure") # Text only for now
        # self.configure_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView)) # Example QStyle
        self.configure_button.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL))
        self.configure_button.setStyleSheet(self._get_button_style())
        self.configure_button.clicked.connect(self._configure_plugin)
        button_layout.addWidget(self.configure_button)
        
        self.generate_button = QPushButton("Generate")
        self.generate_button.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL))
        self.generate_button.setStyleSheet(self._get_button_style(accent=True))
        self.generate_button.clicked.connect(self._generate_notes)
        button_layout.addWidget(self.generate_button)
        
        self.export_button = QPushButton("Export MIDI")
        self.export_button.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL))
        self.export_button.setStyleSheet(self._get_button_style())
        self.export_button.clicked.connect(self._export_midi)
        button_layout.addWidget(self.export_button)
        
        main_panel_layout.addLayout(button_layout)
        
        self.plugin_params = {}
        self.current_notes = []
        
        # Load plugins after UI setup
        self._load_plugins()
    
    def _get_button_style(self, accent=False):
        if accent:
            bg, hover, pressed, text_color = theme.ACCENT_COLOR, theme.ACCENT_HOVER_COLOR, theme.ACCENT_PRESSED_COLOR, theme.SELECTION_TEXT_COLOR
        else:
            bg, hover, pressed, text_color = theme.BUTTON_COLOR, theme.BUTTON_HOVER_COLOR, theme.BUTTON_PRESSED_COLOR, theme.BUTTON_TEXT_COLOR
        return f"""
            QPushButton {{
                background-color: {bg.name()}; color: {text_color.name()}; border: none;
                padding: {theme.PADDING_SMALL + 2}px {theme.PADDING_MEDIUM}px; border-radius: {theme.BORDER_RADIUS}px;
                font-family: "{theme.FONT_FAMILY}"; font-size: {theme.FONT_SIZE_NORMAL}pt;
            }}
            QPushButton:hover {{ background-color: {hover.name()}; }}
            QPushButton:pressed {{ background-color: {pressed.name()}; }} """

    def _get_plugin_icon_data(self):
        piano_icon_path = os.path.join("assets", "icons", "piano.svg")
        if os.path.exists(piano_icon_path):
            icon = QIcon(piano_icon_path)
            if not icon.isNull():
                return icon
        return "🎹"

    def _load_plugins(self):
        self.plugin_list.clear()
        icon_data = self._get_plugin_icon_data()

        for plugin_info in self.plugin_manager.get_plugin_list():
            item = QListWidgetItem(self.plugin_list)
            item_widget = QWidget()
            item_widget.setObjectName("PluginItemWidget")
            item_widget.setAutoFillBackground(True)
            item_widget.setFixedHeight(theme.PLUGIN_ROW_HEIGHT)
            
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(theme.PADDING_MEDIUM, 0, theme.PADDING_MEDIUM, 0)
            item_layout.setSpacing(theme.PADDING_SMALL)

            icon_label = QLabel()
            icon_label.setObjectName("PluginItemIconLabel")
            icon_display_size = theme.PLUGIN_ICON_SIZE - 8 
            icon_label.setFixedSize(QSize(icon_display_size, icon_display_size))
            icon_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            if isinstance(icon_data, QIcon):
                icon_label.setPixmap(icon_data.pixmap(QSize(icon_display_size, icon_display_size)))
            else: # emoji
                icon_label.setText(icon_data)
                icon_label.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL + 1))
            
            name_label = QLabel(plugin_info['name'])
            name_label.setObjectName("PluginItemNameLabel")
            name_label.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL, weight=QFont.Bold if theme.FONT_WEIGHT_BOLD == "bold" else QFont.Normal))
            name_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            # name_label.setWordWrap(True) # Disabled for compact row, ensure PLUGIN_ROW_HEIGHT is sufficient

            version_label = QLabel(f"v{plugin_info['version']}")
            version_label.setObjectName("PluginItemVersionLabel")
            version_label.setFont(QFont(theme.FONT_FAMILY, theme.FONT_SIZE_NORMAL - 1))
            version_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            
            item_layout.addWidget(icon_label)
            item_layout.addWidget(name_label)
            item_layout.addStretch(1)
            item_layout.addWidget(version_label)
            
            # Calculate correct item size hint
            item_size = QSize(self.plugin_list.width() - 10, theme.PLUGIN_ROW_HEIGHT + theme.PADDING_SMALL)
            item.setSizeHint(item_size)
            
            item.setData(Qt.UserRole, plugin_info['id'])
            item.setData(Qt.UserRole + 1, item_widget)
            item.setToolTip(f"<b>{plugin_info['name']}</b><br>{plugin_info['description']}")
            
            self.plugin_list.setItemWidget(item, item_widget)
            
            # Apply initial style
            self._update_item_widget_style(item_widget, item.isSelected())

    def _on_plugin_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        if previous:
            prev_widget = previous.data(Qt.UserRole + 1)
            if prev_widget:
                self._update_item_widget_style(prev_widget, False)
        if current:
            curr_widget = current.data(Qt.UserRole + 1)
            if curr_widget:
                self._update_item_widget_style(curr_widget, True)

    def _update_item_widget_style(self, widget: QWidget, is_selected: bool):
        if is_selected:
            bg_color = theme.ACCENT_COLOR.name()  # Changed to match the screenshot
            text_color_primary = theme.SELECTION_TEXT_COLOR.name()
            text_color_secondary = theme.SELECTION_TEXT_COLOR.lighter(120).name()
            border_style = f"border: 1px solid {theme.ACCENT_COLOR.name()};"
        else:
            bg_color = theme.BUTTON_COLOR.name()
            text_color_primary = theme.PRIMARY_TEXT_COLOR.name()
            text_color_secondary = theme.SECONDARY_TEXT_COLOR.name()
            border_style = "border: none;"

        # Base style for the item widget (card)
        widget.setStyleSheet(f"""
            QWidget#PluginItemWidget {{
                background-color: {bg_color};
                border-radius: {theme.BORDER_RADIUS}px;
                {border_style}
            }}
        """)
        
        # Style child labels individually using object names for robustness
        icon_label = widget.findChild(QLabel, "PluginItemIconLabel")
        name_label = widget.findChild(QLabel, "PluginItemNameLabel")
        version_label = widget.findChild(QLabel, "PluginItemVersionLabel")

        if icon_label:
            icon_label.setStyleSheet(f"color: {text_color_primary}; background-color: transparent;")
        if name_label:
            name_label.setStyleSheet(f"color: {text_color_primary}; background-color: transparent;")
        if version_label:
            version_label.setStyleSheet(f"color: {text_color_secondary}; background-color: transparent;")
            
    def resizeEvent(self, event):
        """Handle resize events to update item sizes"""
        super().resizeEvent(event)
        # Update item widths when resized
        for i in range(self.plugin_list.count()):
            item = self.plugin_list.item(i)
            item.setSizeHint(QSize(self.plugin_list.width() - 10, theme.PLUGIN_ROW_HEIGHT + theme.PADDING_SMALL))
            
    def set_current_notes(self, notes):
        self.current_notes = notes
    
    def _configure_plugin(self):
        selected_items = self.plugin_list.selectedItems()
        if not selected_items: return
        plugin_id = selected_items[0].data(Qt.UserRole)
        plugin = self.plugin_manager.get_plugin(plugin_id)
        if not plugin: return
        current_params = self.plugin_params.get(plugin_id, {})
        dialog = PluginParameterDialog(plugin, current_params, self)
        if dialog.exec() == QDialog.Accepted:
            self.plugin_params[plugin_id] = dialog.get_parameter_values()
    
    def _generate_notes(self):
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Plugin Selected", "Please select a plugin.")
            return
        plugin_id = selected_items[0].data(Qt.UserRole)
        parameters = self.plugin_params.get(plugin_id, {})
        try:
            generated_notes = self.plugin_manager.generate_notes(plugin_id, existing_notes=self.current_notes, parameters=parameters)
            self.notesGenerated.emit(generated_notes)
            self.current_notes = generated_notes 
        except Exception as e:
            QMessageBox.critical(self, "Generation Error", f"Error: {str(e)}")
    
    def _export_midi(self):
        if not self.current_notes:
            QMessageBox.warning(self, "No Notes", "No notes to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export MIDI", "", "MIDI Files (*.mid);;All Files (*)")
        if not file_path: return
        if not file_path.lower().endswith('.mid'): file_path += '.mid'
        try:
            export_to_midi(self.current_notes, file_path)
            QMessageBox.information(self, "Export Successful", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error: {str(e)}")