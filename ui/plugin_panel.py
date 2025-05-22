import os
import tempfile # Added
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QDockWidget, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QDialog, QLabel,
    QSizePolicy, QStyle
)
from PySide6.QtCore import Qt, Signal, QSize, QUrl, QMimeData # Added QUrl, QMimeData
from PySide6.QtGui import QFont, QIcon, QPixmap, QFontMetrics, QDrag # Added QDrag

from plugin_manager import PluginManager
from export_utils import export_to_midi
from ui.plugin_dialogs import PluginParameterDialog
from .custom_widgets import DragExportButton, ModernButton # Added ModernButton
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
        self.dock_content.setStyleSheet(f"background-color: {theme.PANEL_BG_COLOR.name()};") # Panel Styling
        
        main_panel_layout = QVBoxLayout(self.dock_content)
        main_panel_layout.setContentsMargins(theme.PADDING_L, theme.PADDING_L, theme.PADDING_L, theme.PADDING_L) # Panel Styling
        main_panel_layout.setSpacing(theme.PADDING_M) # Panel Styling
        
        self.plugin_list = QListWidget()
        # Set size policy to expand vertically
        self.plugin_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plugin_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent; 
                border: none; 
                outline: 0; 
                spacing: {theme.PADDING_M}px;  /* Use a theme constant for spacing */
            }}
            QListWidget::item {{
                border: none; 
                padding: 0px; /* Item itself is a container, padding handled by item_widget */
                /* margin-bottom is effectively handled by QListWidget::spacing now */
            }}
            QListWidget::item:selected {{ 
                background-color: transparent; /* Selection handled by item_widget */
            }}
            QListWidget::item:hover {{ 
                background-color: transparent; /* Hover handled by item_widget */
            }}
        """)
        main_panel_layout.addWidget(self.plugin_list)
        
        self.plugin_list.currentItemChanged.connect(self._on_plugin_selection_changed)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.configure_button = ModernButton("Configure") # Changed to ModernButton
        self.configure_button.clicked.connect(self._configure_plugin)
        button_layout.addWidget(self.configure_button)
        
        self.generate_button = ModernButton("Generate", accent=True) # Changed to ModernButton, accent=True
        self.generate_button.clicked.connect(self._generate_notes)
        button_layout.addWidget(self.generate_button)
        
        self.export_button = DragExportButton("Export MIDI") 
        self.export_button.setToolTip("Click to export, or drag to your DAW/folder as .mid") 
        self.export_button.clicked.connect(self._handle_export_click) 
        self.export_button.dragInitiated.connect(self._handle_export_drag) 
        button_layout.addWidget(self.export_button)
        
        main_panel_layout.addLayout(button_layout)
        
        self.plugin_params = {}
        self.current_notes = []
        self.temp_files_to_clean = [] 
        self.temp_midi_dir = os.path.join(tempfile.gettempdir(), "pianoroll_midi_exports")
        os.makedirs(self.temp_midi_dir, exist_ok=True)
        
        # Load plugins after UI setup
        self._load_plugins()
    
    # _get_button_style method removed

    def _get_plugin_icon_data(self):
        # Using a placeholder for now, will be replaced by theme.PLUGIN_ICON_PATH_DEFAULT if available
        # For actual icon files, ensure they exist at the path specified in theme.py
        default_icon_path = getattr(theme, 'PLUGIN_ICON_PATH_DEFAULT', os.path.join(theme.ICON_PATH, "default-plugin.svg"))
        if os.path.exists(default_icon_path):
            icon = QIcon(default_icon_path)
            if not icon.isNull():
                return icon
        # Fallback emoji if default SVG is missing or invalid
        return "🎛️" 

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
            item_layout.setContentsMargins(theme.PADDING_M, 0, theme.PADDING_M, 0)
            item_layout.setSpacing(theme.PADDING_S)

            icon_label = QLabel()
            icon_label.setObjectName("PluginItemIconLabel")
            icon_display_size = theme.ICON_SIZE_XL - 8 
            icon_label.setFixedSize(QSize(icon_display_size, icon_display_size))
            icon_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            if isinstance(icon_data, QIcon):
                icon_label.setPixmap(icon_data.pixmap(QSize(icon_display_size, icon_display_size)))
            else: # emoji
                icon_label.setText(icon_data)
                icon_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M + 1))
            
            name_label = QLabel(plugin_info['name'])
            name_label.setObjectName("PluginItemNameLabel")
            name_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, weight=theme.FONT_WEIGHT_BOLD))
            name_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            # name_label.setWordWrap(True) # Disabled for compact row, ensure PLUGIN_ROW_HEIGHT is sufficient

            version_label = QLabel(f"v{plugin_info['version']}")
            version_label.setObjectName("PluginItemVersionLabel")
            version_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
            version_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            
            item_layout.addWidget(icon_label)
            item_layout.addWidget(name_label)
            item_layout.addStretch(1)
            item_layout.addWidget(version_label)
            
            # Calculate correct item size hint
            item_size = QSize(self.plugin_list.width() - 10, theme.PLUGIN_ROW_HEIGHT + theme.PADDING_S)
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
            bg_color = theme.ACCENT_PRIMARY_COLOR.name()
            text_color_primary = theme.ACCENT_TEXT_COLOR.name()
            # For version text on accent, a slightly less prominent variant of accent text might be good.
            text_color_secondary = theme.ACCENT_TEXT_COLOR.lighter(130).name() 
            if theme.ACCENT_TEXT_COLOR.lightness() < 128: # If accent text is dark, lighten secondary
                 text_color_secondary = theme.ACCENT_TEXT_COLOR.lighter(150).name()
            else: # If accent text is light, darken secondary
                 text_color_secondary = theme.ACCENT_TEXT_COLOR.darker(150).name()

            border_style = f"border: 1px solid {theme.ACCENT_PRIMARY_COLOR.darker(120).name()};"
        else:
            bg_color = theme.ITEM_BG_COLOR.name()
            text_color_primary = theme.PRIMARY_TEXT_COLOR.name()
            text_color_secondary = theme.SECONDARY_TEXT_COLOR.name()
            border_style = f"border: 1px solid {theme.BORDER_COLOR_NORMAL.name()};"

        # Base style for the item widget (card)
        widget.setStyleSheet(f"""
            QWidget#PluginItemWidget {{
                background-color: {bg_color};
                border-radius: {theme.BORDER_RADIUS_M}px;
                {border_style}
            }}
        """)
        
        # Style child labels individually using object names for robustness
        icon_label = widget.findChild(QLabel, "PluginItemIconLabel")
        name_label = widget.findChild(QLabel, "PluginItemNameLabel")
        version_label = widget.findChild(QLabel, "PluginItemVersionLabel")

        if icon_label: # Icon color (for text/emoji based icons)
            icon_label.setStyleSheet(f"color: {text_color_primary}; background-color: transparent; border: none;")
        if name_label:
            name_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, weight=theme.FONT_WEIGHT_BOLD))
            name_label.setStyleSheet(f"color: {text_color_primary}; background-color: transparent; border: none;")
        if version_label:
            version_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
            version_label.setStyleSheet(f"color: {text_color_secondary}; background-color: transparent; border: none;")
            
    def resizeEvent(self, event):
        """Handle resize events to update item sizes"""
        super().resizeEvent(event)
        # Update item widths when resized
        for i in range(self.plugin_list.count()):
            item = self.plugin_list.item(i)
            item_widget = self.plugin_list.itemWidget(item) # Get the custom widget
            if item_widget: # Ensure item_widget exists
                 # Set item size hint on the QListWidgetItem for QListWidget to use
                item.setSizeHint(QSize(self.plugin_list.viewport().width() - (theme.PADDING_S * 2), theme.PLUGIN_ROW_HEIGHT))

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
        if hasattr(self.configure_button, 'clearFocus'): # ModernButton might not have it directly
            self.configure_button.clearFocus()
    
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
        finally:
            if hasattr(self.generate_button, 'clearFocus'):
                self.generate_button.clearFocus() 

    def _handle_export_click(self): 
        if not self.current_notes:
            QMessageBox.warning(self, "No Notes", "No notes to export.")
            return
        
        suggested_filename = "exported_melody.mid"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export MIDI", 
            suggested_filename, 
            "MIDI Files (*.mid);;All Files (*)"
        )
        
        if not file_path: 
            return
        
        if not file_path.lower().endswith('.mid'):
            file_path += '.mid'
            
        try:
            export_to_midi(self.current_notes, file_path)
            QMessageBox.information(self, "Export Successful", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting MIDI: {str(e)}")
        finally:
            if hasattr(self.export_button, 'clearFocus'):
                self.export_button.clearFocus()

    def _handle_export_drag(self):
        if not self.current_notes:
            return

        temp_file_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.temp_midi_dir,
                delete=False, 
                suffix=".mid", 
                prefix="dragged_"
            ) as tmp_file:
                temp_file_path = tmp_file.name
            
            export_to_midi(self.current_notes, temp_file_path)
            self.temp_files_to_clean.append(temp_file_path)

            mime_data = QMimeData()
            url = QUrl.fromLocalFile(temp_file_path)
            mime_data.setUrls([url])
            
            drag = QDrag(self.export_button)
            drag.setMimeData(mime_data)
            
            result = drag.exec_(Qt.CopyAction)

        except Exception as e:
            QMessageBox.critical(self, "Drag Export Error", f"Could not prepare MIDI for dragging: {str(e)}")
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path) 
                    if temp_file_path in self.temp_files_to_clean:
                        self.temp_files_to_clean.remove(temp_file_path)
                except OSError:
                    pass 
        finally:
            if hasattr(self.export_button, 'clearFocus'):
                self.export_button.clearFocus()


    def cleanup_temporary_files(self):
        """Cleans up temporary MIDI files created during drag operations."""
        cleaned_count = 0
        for f_path in list(self.temp_files_to_clean): # Iterate over a copy
            try:
                if os.path.exists(f_path):
                    os.remove(f_path)
                    cleaned_count += 1
                if f_path in self.temp_files_to_clean:
                    self.temp_files_to_clean.remove(f_path)
            except Exception as e:
                print(f"Error deleting temporary file {f_path}: {e}")
        
        if cleaned_count > 0:
            print(f"Cleaned up {cleaned_count} temporary MIDI files.")

        try:
            if os.path.exists(self.temp_midi_dir) and not os.listdir(self.temp_midi_dir):
                os.rmdir(self.temp_midi_dir)
                print(f"Removed temporary MIDI directory: {self.temp_midi_dir}")
        except Exception as e:
            print(f"Could not remove temporary MIDI directory {self.temp_midi_dir} (it might not be empty or access denied): {e}")
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
            item_layout.setContentsMargins(theme.PADDING_M, 0, theme.PADDING_M, 0)
            item_layout.setSpacing(theme.PADDING_S)

            icon_label = QLabel()
            icon_label.setObjectName("PluginItemIconLabel")
            icon_display_size = theme.ICON_SIZE_XL - 8 
            icon_label.setFixedSize(QSize(icon_display_size, icon_display_size))
            icon_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            if isinstance(icon_data, QIcon):
                icon_label.setPixmap(icon_data.pixmap(QSize(icon_display_size, icon_display_size)))
            else: # emoji
                icon_label.setText(icon_data)
                icon_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M + 1))
            
            name_label = QLabel(plugin_info['name'])
            name_label.setObjectName("PluginItemNameLabel")
            name_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, weight=theme.FONT_WEIGHT_BOLD))
            name_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            # name_label.setWordWrap(True) # Disabled for compact row, ensure PLUGIN_ROW_HEIGHT is sufficient

            version_label = QLabel(f"v{plugin_info['version']}")
            version_label.setObjectName("PluginItemVersionLabel")
            version_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
            version_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            
            item_layout.addWidget(icon_label)
            item_layout.addWidget(name_label)
            item_layout.addStretch(1)
            item_layout.addWidget(version_label)
            
            # Calculate correct item size hint
            item_size = QSize(self.plugin_list.width() - 10, theme.PLUGIN_ROW_HEIGHT + theme.PADDING_S)
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
            bg_color = theme.ACCENT_PRIMARY_COLOR.name()
            text_color_primary = theme.ACCENT_TEXT_COLOR.name()
            # For version text on accent, a slightly less prominent variant of accent text might be good.
            text_color_secondary = theme.ACCENT_TEXT_COLOR.lighter(130).name() 
            if theme.ACCENT_TEXT_COLOR.lightness() < 128: # If accent text is dark, lighten secondary
                 text_color_secondary = theme.ACCENT_TEXT_COLOR.lighter(150).name()
            else: # If accent text is light, darken secondary
                 text_color_secondary = theme.ACCENT_TEXT_COLOR.darker(150).name()

            border_style = f"border: 1px solid {theme.ACCENT_PRIMARY_COLOR.darker(120).name()};"
        else:
            bg_color = theme.ITEM_BG_COLOR.name()
            text_color_primary = theme.PRIMARY_TEXT_COLOR.name()
            text_color_secondary = theme.SECONDARY_TEXT_COLOR.name()
            border_style = f"border: 1px solid {theme.BORDER_COLOR_NORMAL.name()};"

        # Base style for the item widget (card)
        widget.setStyleSheet(f"""
            QWidget#PluginItemWidget {{
                background-color: {bg_color};
                border-radius: {theme.BORDER_RADIUS_M}px;
                {border_style}
            }}
        """)
        
        # Style child labels individually using object names for robustness
        icon_label = widget.findChild(QLabel, "PluginItemIconLabel")
        name_label = widget.findChild(QLabel, "PluginItemNameLabel")
        version_label = widget.findChild(QLabel, "PluginItemVersionLabel")

        if icon_label: # Icon color (for text/emoji based icons)
            icon_label.setStyleSheet(f"color: {text_color_primary}; background-color: transparent; border: none;")
        if name_label:
            name_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, weight=theme.FONT_WEIGHT_BOLD))
            name_label.setStyleSheet(f"color: {text_color_primary}; background-color: transparent; border: none;")
        if version_label:
            version_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
            version_label.setStyleSheet(f"color: {text_color_secondary}; background-color: transparent; border: none;")
            
    def resizeEvent(self, event):
        """Handle resize events to update item sizes"""
        super().resizeEvent(event)
        # Update item widths when resized
        for i in range(self.plugin_list.count()):
            item = self.plugin_list.item(i)
            item_widget = self.plugin_list.itemWidget(item) # Get the custom widget
            if item_widget: # Ensure item_widget exists
                 # Set item size hint on the QListWidgetItem for QListWidget to use
                item.setSizeHint(QSize(self.plugin_list.viewport().width() - (theme.PADDING_S * 2), theme.PLUGIN_ROW_HEIGHT))

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
        self.configure_button.clearFocus() # Clear focus after dialog
    
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
        finally:
            self.generate_button.clearFocus() # Clear focus after generation or error

    def _handle_export_click(self): # Renamed from _export_midi
        if not self.current_notes:
            QMessageBox.warning(self, "No Notes", "No notes to export.")
            return
        
        # Suggest a filename based on current context if possible (e.g., plugin name, timestamp)
        # For now, keeping it simple.
        suggested_filename = "exported_melody.mid"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export MIDI", 
            suggested_filename, # Default filename in dialog
            "MIDI Files (*.mid);;All Files (*)"
        )
        
        if not file_path: 
            return
        
        # Ensure the file has a .mid extension
        if not file_path.lower().endswith('.mid'):
            file_path += '.mid'
            
        try:
            export_to_midi(self.current_notes, file_path)
            QMessageBox.information(self, "Export Successful", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting MIDI: {str(e)}")
        finally:
            self.export_button.clearFocus() # Clear focus after click export attempt

    def _handle_export_drag(self):
        if not self.current_notes:
            # Optionally, could disable drag initiation if no notes, but a message is fine too.
            # QMessageBox.warning(self, "No Notes", "No notes to drag-export.")
            return

        temp_file_path = ""
        try:
            # Create a temporary file for the MIDI data
            with tempfile.NamedTemporaryFile(
                dir=self.temp_midi_dir,
                delete=False, 
                suffix=".mid", 
                prefix="dragged_"
            ) as tmp_file:
                temp_file_path = tmp_file.name
            
            # Export notes to this temporary file
            export_to_midi(self.current_notes, temp_file_path)
            self.temp_files_to_clean.append(temp_file_path) # Track for cleanup

            # Prepare QMimeData
            mime_data = QMimeData()
            url = QUrl.fromLocalFile(temp_file_path)
            mime_data.setUrls([url])
            # Some DAWs might look for specific MIME types, e.g. "audio/midi" or "application/x-midi"
            # mime_data.setData("audio/midi", b'') # Example, might need QByteArray

            # Create and execute QDrag
            drag = QDrag(self.export_button)
            drag.setMimeData(mime_data)
            
            # Optional: Set a pixmap for the drag cursor (e.g., a small icon or button representation)
            # For simplicity, we can omit this or use a generic icon if available
            # pixmap = QPixmap(self.export_button.size())
            # self.export_button.render(pixmap)
            # drag.setPixmap(pixmap)
            # drag.setHotSpot(pixmap.rect().center()) # Center of the pixmap

            # Qt.CopyAction is typical for exporting files.
            # The drag operation is blocking until completed or canceled.
            result = drag.exec_(Qt.CopyAction)

            # Note: The temporary file is not deleted immediately after drag.
            # It's up to the receiving application to copy it.
            # We clean it up when the application closes.

        except Exception as e:
            QMessageBox.critical(self, "Drag Export Error", f"Could not prepare MIDI for dragging: {str(e)}")
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path) # Clean up if drag prep failed
                    if temp_file_path in self.temp_files_to_clean:
                        self.temp_files_to_clean.remove(temp_file_path)
                except OSError:
                    pass # Ignore if removal fails at this stage
        finally:
            self.export_button.clearFocus() # Clear focus after drag export attempt


    def cleanup_temporary_files(self):
        """Cleans up temporary MIDI files created during drag operations."""
        cleaned_count = 0
        for f_path in list(self.temp_files_to_clean): # Iterate over a copy
            try:
                if os.path.exists(f_path):
                    os.remove(f_path)
                    cleaned_count += 1
                # Remove from list even if it didn't exist, to prevent re-attempts
                if f_path in self.temp_files_to_clean:
                    self.temp_files_to_clean.remove(f_path)
            except Exception as e:
                # Log this error appropriately in a real application
                print(f"Error deleting temporary file {f_path}: {e}")
        
        if cleaned_count > 0:
            print(f"Cleaned up {cleaned_count} temporary MIDI files.")

        # Optionally, try to remove the temporary directory if it's empty
        try:
            if os.path.exists(self.temp_midi_dir) and not os.listdir(self.temp_midi_dir):
                os.rmdir(self.temp_midi_dir)
                print(f"Removed temporary MIDI directory: {self.temp_midi_dir}")
        except Exception as e:
            print(f"Could not remove temporary MIDI directory {self.temp_midi_dir} (it might not be empty or access denied): {e}")
