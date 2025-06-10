import os
import sys
import json
import requests
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFrame, QGroupBox, QTextEdit,
    QProgressBar, QSplitter, QWidget, QScrollArea, QGridLayout,
    QSizePolicy, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize, QThread, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap

from ui.custom_widgets import ModernButton
from config import theme

class ModelDownloadThread(QThread):
    """Thread for downloading models with progress tracking"""
    
    # Signals
    progressUpdated = Signal(int, str)  # progress_percent, status_text
    downloadCompleted = Signal(str, str)  # success_message, model_name
    downloadFailed = Signal(str, str)  # error_message, model_name
    
    def __init__(self, download_url, save_path, model_name, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.save_path = save_path
        self.model_name = model_name
        self.is_cancelled = False
        
    def run(self):
        """Download the model file"""
        try:
            # Note: File existence check is handled in the main thread before starting download
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            # Start download with streaming
            self.progressUpdated.emit(0, "Connecting to server...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get file size from headers
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            self.progressUpdated.emit(0, f"Downloading... 0 MB / {total_size / 1024 / 1024:.1f} MB")
            
            # Download file in chunks
            chunk_size = 8192
            with open(self.save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.is_cancelled:
                        file.close()
                        if os.path.exists(self.save_path):
                            os.remove(self.save_path)
                        return
                    
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progressUpdated.emit(
                                progress, 
                                f"Downloading... {downloaded_size / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB"
                            )
            
            # Verify file was downloaded completely
            if total_size > 0 and os.path.getsize(self.save_path) != total_size:
                if os.path.exists(self.save_path):
                    os.remove(self.save_path)
                self.downloadFailed.emit("Download incomplete. File size mismatch.", self.model_name)
                return
            
            self.progressUpdated.emit(100, "Download completed!")
            self.downloadCompleted.emit(f"Model '{self.model_name}' downloaded successfully!", self.model_name)
            
        except requests.exceptions.ConnectionError:
            self.downloadFailed.emit("Network connection error. Please check your internet connection.", self.model_name)
        except requests.exceptions.Timeout:
            self.downloadFailed.emit("Download timeout. The server is taking too long to respond.", self.model_name)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.downloadFailed.emit("Model file not found on server (404 error).", self.model_name)
            else:
                self.downloadFailed.emit(f"HTTP error {e.response.status_code}: {str(e)}", self.model_name)
        except PermissionError:
            self.downloadFailed.emit("Permission denied. Cannot write to models directory.", self.model_name)
        except OSError as e:
            if "No space left on device" in str(e):
                self.downloadFailed.emit("Insufficient disk space to download the model.", self.model_name)
            else:
                self.downloadFailed.emit(f"File system error: {str(e)}", self.model_name)
        except Exception as e:
            self.downloadFailed.emit(f"Unexpected error: {str(e)}", self.model_name)
        finally:
            # Clean up partial download on error
            if hasattr(self, 'save_path') and os.path.exists(self.save_path) and self.is_cancelled:
                try:
                    os.remove(self.save_path)
                except:
                    pass
    
    def cancel(self):
        """Cancel the download"""
        self.is_cancelled = True

class DownloadProgressDialog(QDialog):
    """Modern progress dialog for model downloads"""
    
    def __init__(self, model_name, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.download_thread = None
        self.setupUI()
        
    def setupUI(self):
        """Setup the progress dialog UI"""
        self.setWindowTitle("Downloading Model")
        self.setFixedSize(450, 200)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        
        # Apply modern styling
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme.DIALOG_BG_COLOR.lighter(105).name()},
                    stop: 1 {theme.DIALOG_BG_COLOR.name()}
                );
                color: {theme.PRIMARY_TEXT_COLOR.name()};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(theme.PADDING_L)
        layout.setContentsMargins(theme.PADDING_L, theme.PADDING_L, theme.PADDING_L, theme.PADDING_L)
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("⬇️")
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(f"Downloading: {self.model_name}")
        title_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        title_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, 1)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {theme.ACCENT_PRIMARY_COLOR.name()},
                    stop: 1 {theme.ACCENT_HOVER_COLOR.name()}
                );
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Preparing download...")
        self.status_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        self.status_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = ModernButton("❌ Cancel")
        self.cancel_button.clicked.connect(self.cancelDownload)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def updateProgress(self, progress, status):
        """Update progress bar and status"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(status)
    
    def cancelDownload(self):
        """Cancel the download"""
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.download_thread.wait(3000)  # Wait up to 3 seconds
        self.reject()

class ModernModelCard(QFrame):
    """Modern glassmorphic model card"""
    downloadRequested = Signal(dict)
    
    def __init__(self, model_info, parent=None):
        super().__init__(parent)
        self.model_info = model_info
        self.setupCard()
        
    def setupCard(self):
        # Modern card styling with glassmorphism
        self.setStyleSheet(f"""
            ModernModelCard {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 12),
                    stop: 1 rgba(255, 255, 255, 6)
                );
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: 12px;
                margin: 4px;
            }}
            ModernModelCard:hover {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 18),
                    stop: 1 rgba(255, 255, 255, 10)
                );
                border: 1px solid rgba(255, 255, 255, 25);
            }}
        """)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(theme.SHADOW_COLOR)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(theme.PADDING_S)
        layout.setContentsMargins(theme.PADDING_M, theme.PADDING_M, theme.PADDING_M, theme.PADDING_M)
        
        # Header with icon and name
        header_layout = QHBoxLayout()
        header_layout.setSpacing(theme.PADDING_S)
        
        # Category icon
        category_icons = {
            "Piano": "🎹",
            "Jazz": "🎷", 
            "Orchestral": "🎼",
            "Electronic": "🎧",
            "Folk": "🪕",
            "Ambient": "🌙"
        }
        
        icon_label = QLabel(category_icons.get(self.model_info['category'], "🎵"))
        icon_label.setFont(QFont("Arial", 20))
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 150);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 30);
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # Name and category
        name_container = QVBoxLayout()
        name_container.setSpacing(2)
        
        name_label = QLabel(self.model_info['name'])
        name_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M, theme.FONT_WEIGHT_BOLD))
        name_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        name_container.addWidget(name_label)
        
        category_label = QLabel(self.model_info['category'])
        category_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS))
        category_label.setStyleSheet(f"""
            background: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 100);
            color: {theme.ACCENT_TEXT_COLOR.name()};
            padding: 2px 8px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 20);
        """)
        category_label.setAlignment(Qt.AlignCenter)
        category_label.setMaximumWidth(80)
        name_container.addWidget(category_label)
        
        header_layout.addLayout(name_container)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(self.model_info['description'])
        desc_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        desc_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()}; line-height: 1.4;")
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(50)
        layout.addWidget(desc_label)
        
        # Info row with size and version
        info_layout = QHBoxLayout()
        info_layout.setSpacing(theme.PADDING_M)
        
        size_container = QHBoxLayout()
        size_icon = QLabel("📦")
        size_icon.setFont(QFont("Arial", 12))
        size_value = QLabel(self.model_info['size'])
        size_value.setFont(QFont(theme.FONT_FAMILY_MONOSPACE, theme.FONT_SIZE_XS))
        size_value.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        size_container.addWidget(size_icon)
        size_container.addWidget(size_value)
        size_container.addStretch()
        
        version_container = QHBoxLayout()
        version_icon = QLabel("🏷️")
        version_icon.setFont(QFont("Arial", 12))
        version_value = QLabel(self.model_info['version'])
        version_value.setFont(QFont(theme.FONT_FAMILY_MONOSPACE, theme.FONT_SIZE_XS))
        version_value.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        version_container.addWidget(version_icon)
        version_container.addWidget(version_value)
        version_container.addStretch()
        
        info_layout.addLayout(size_container)
        info_layout.addLayout(version_container)
        layout.addLayout(info_layout)
        
        # Download button
        self.download_button = ModernButton("⬇️ Download", accent=True)
        self.download_button.setFixedHeight(32)
        self.download_button.clicked.connect(lambda: self.downloadRequested.emit(self.model_info))
        layout.addWidget(self.download_button)

class ModernModelItem(QWidget):
    """Modern list item for installed models with selection support"""
    
    # Signals
    itemSelected = Signal(str)  # Emitted when item is selected (model_name)
    itemDoubleClicked = Signal(str)  # Emitted when item is double-clicked (model_name)
    
    def __init__(self, model_name, size_str, parent=None):
        super().__init__(parent)
        self.model_name = model_name
        self.size_str = size_str
        self.is_selected = False
        self.setupItem()
        
    def setupItem(self):
        self.setFixedHeight(56)  # Slightly smaller for compact layout
        self.setCursor(Qt.PointingHandCursor)  # Show pointer cursor
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(theme.PADDING_S, theme.PADDING_XS, theme.PADDING_S, theme.PADDING_XS)
        layout.setSpacing(theme.PADDING_S)
        
        # File icon
        icon_label = QLabel("🧠")
        icon_label.setFont(QFont("Arial", 16))
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 120),
                    stop: 1 rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 80)
                );
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 30);
            }}
        """)
        layout.addWidget(icon_label)
        
        # Model info container with fixed width to prevent overflow
        info_container = QWidget()
        info_container.setMinimumWidth(180)  # Ensure minimum space for text
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Model name with elision for long names
        self.name_label = QLabel()
        self.name_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S, theme.FONT_WEIGHT_BOLD))
        self.name_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        self.name_label.setWordWrap(False)
        
        # Create shortened display name
        display_name = self._createDisplayName(self.model_name)
        self.name_label.setText(display_name)
        self.name_label.setToolTip(f"Full name: {self.model_name}")  # Show full name in tooltip
        
        info_layout.addWidget(self.name_label)
        
        size_label = QLabel(f"Size: {self.size_str}")
        size_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XS))
        size_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        info_layout.addWidget(size_label)
        
        layout.addWidget(info_container, 1)  # Give it flex space but not unlimited
        
        # Selection indicator - ALWAYS visible with fixed position
        self.selection_indicator = QLabel("✓")
        self.selection_indicator.setFont(QFont("Arial", 14, theme.FONT_WEIGHT_BOLD))
        self.selection_indicator.setFixedSize(22, 22)
        self.selection_indicator.setAlignment(Qt.AlignCenter)
        self.selection_indicator.setVisible(False)
        self.selection_indicator.setStyleSheet(f"""
            QLabel {{
                background: {theme.ACCENT_PRIMARY_COLOR.name()};
                color: {theme.ACCENT_TEXT_COLOR.name()};
                border-radius: 11px;
                border: 2px solid rgba(255, 255, 255, 50);
            }}
        """)
        layout.addWidget(self.selection_indicator)  # No stretch before this
        
        # Now call updateStyle after all UI elements are created
        self.updateStyle()
    
    def _createDisplayName(self, full_name):
        """Create a shortened display name for long model names"""
        if len(full_name) <= 30:
            return full_name
        
        # Try to create intelligent short names
        name_lower = full_name.lower()
        
        if 'alex_melody' in name_lower:
            return "alex_melody.pth"
        elif 'piano' in name_lower and 'transformer' in name_lower:
            return "Piano_Transformer.pth"
        elif 'piano' in name_lower and 'hands' in name_lower:
            return "Piano_Hands_Model.pth"
        elif full_name.endswith('.pth'):
            # Generic truncation - keep start and extension
            base_name = full_name[:-4]  # Remove .pth
            if len(base_name) > 25:
                return base_name[:22] + "....pth"
            else:
                return full_name
        else:
            # Very long name without extension
            return full_name[:27] + "..."
    
    def updateStyle(self):
        """Update the style based on selection state"""
        if self.is_selected:
            self.setStyleSheet(f"""
                ModernModelItem {{
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 140),
                        stop: 1 rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 80)
                    );
                    border: 2px solid rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 200);
                    border-radius: 8px;
                    margin: 1px;
                }}
            """)
            # Update text colors for better visibility on selected background
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet(f"color: {theme.ACCENT_TEXT_COLOR.name()};")
        else:
            self.setStyleSheet(f"""
                ModernModelItem {{
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(255, 255, 255, 12),
                        stop: 1 rgba(255, 255, 255, 6)
                    );
                    border: 1px solid rgba(255, 255, 255, 15);
                    border-radius: 8px;
                    margin: 1px;
                }}
                ModernModelItem:hover {{
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(255, 255, 255, 20),
                        stop: 1 rgba(255, 255, 255, 12)
                    );
                    border: 1px solid rgba(255, 255, 255, 25);
                }}
            """)
            # Reset text colors for unselected state
            if hasattr(self, 'name_label'):
                self.name_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
    
    def setSelected(self, selected):
        """Set the selection state of this item"""
        if self.is_selected != selected:
            self.is_selected = selected
            self.selection_indicator.setVisible(selected)
            self.updateStyle()
            
            # Add a subtle animation effect
            if selected:
                # Make the selection indicator more prominent
                self.selection_indicator.setStyleSheet(f"""
                    QLabel {{
                        background: {theme.ACCENT_TEXT_COLOR.name()};
                        color: {theme.ACCENT_PRIMARY_COLOR.name()};
                        border-radius: 11px;
                        border: 2px solid rgba(255, 255, 255, 80);
                        font-weight: bold;
                    }}
                """)
            else:
                # Reset to normal style
                self.selection_indicator.setStyleSheet(f"""
                    QLabel {{
                        background: {theme.ACCENT_PRIMARY_COLOR.name()};
                        color: {theme.ACCENT_TEXT_COLOR.name()};
                        border-radius: 11px;
                        border: 2px solid rgba(255, 255, 255, 50);
                    }}
                """)
    
    def mousePressEvent(self, event):
        """Handle mouse press for selection"""
        if event.button() == Qt.LeftButton:
            self.itemSelected.emit(self.model_name)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click for default action (info)"""
        if event.button() == Qt.LeftButton:
            self.itemDoubleClicked.emit(self.model_name)
        super().mouseDoubleClickEvent(event)

class ModelDownloaderDialog(QDialog):
    """Modern AI Model Downloader Dialog with glassmorphism design"""
    
    # Signals
    modelDownloaded = Signal(str)
    modelDeleted = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Model Downloader")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        
        # Set dialog properties
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint)
        
        # Selection tracking
        self.current_selected_model = None
        self.model_items = []  # Track all model items
        
        # Apply modern theme styling
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {theme.DIALOG_BG_COLOR.lighter(105).name()},
                    stop: 1 {theme.DIALOG_BG_COLOR.name()}
                );
                color: {theme.PRIMARY_TEXT_COLOR.name()};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 8);
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 150);
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba({theme.ACCENT_HOVER_COLOR.red()}, {theme.ACCENT_HOVER_COLOR.green()}, {theme.ACCENT_HOVER_COLOR.blue()}, 180);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
        
        self.setupUI()
        self.refreshCurrentModels()
        
        # Load available models in a timer to avoid blocking UI
        QTimer.singleShot(100, self.loadAvailableModels)
    
    def setupUI(self):
        """Setup the modern UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(theme.PADDING_L)
        main_layout.setContentsMargins(theme.PADDING_L, theme.PADDING_L, theme.PADDING_L, theme.PADDING_L)
        
        # Modern header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(theme.PADDING_M)
        
        # App icon
        icon_label = QLabel("🤖")
        icon_label.setFont(QFont("Arial", 32))
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 180),
                    stop: 1 rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 120)
                );
                border-radius: 24px;
                border: 2px solid rgba(255, 255, 255, 30);
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # Title and subtitle
        title_container = QVBoxLayout()
        title_container.setSpacing(4)
        
        title_label = QLabel("AI Model Downloader")
        title_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_XL, theme.FONT_WEIGHT_BOLD))
        title_label.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        title_container.addWidget(title_label)
        
        subtitle_label = QLabel("Manage and download AI models for enhanced music generation")
        subtitle_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M))
        subtitle_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        title_container.addWidget(subtitle_label)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # Main content with modern sections
        content_layout = QHBoxLayout()
        content_layout.setSpacing(theme.PADDING_L)
        
        # Left side - Installed models
        installed_section = self._createInstalledModelsSection()
        content_layout.addWidget(installed_section, 1)
        
        # Right side - Available models  
        available_section = self._createAvailableModelsSection()
        content_layout.addWidget(available_section, 2)
        
        main_layout.addLayout(content_layout)
        
        # Modern footer with actions
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(theme.PADDING_M)
        
        self.refresh_button = ModernButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refreshAll)
        footer_layout.addWidget(self.refresh_button)
        
        footer_layout.addStretch()
        
        self.close_button = ModernButton("✅ Close", accent=True)
        self.close_button.clicked.connect(self.accept)
        footer_layout.addWidget(self.close_button)
        
        main_layout.addLayout(footer_layout)
    
    def _createInstalledModelsSection(self):
        """Create modern installed models section"""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 8),
                    stop: 1 rgba(255, 255, 255, 4)
                );
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: 16px;
            }}
        """)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(theme.SHADOW_COLOR)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(theme.PADDING_L, theme.PADDING_L, theme.PADDING_L, theme.PADDING_L)
        layout.setSpacing(theme.PADDING_M)
        
        # Section header
        header_layout = QHBoxLayout()
        header_icon = QLabel("📦")
        header_icon.setFont(QFont("Arial", 20))
        header_layout.addWidget(header_icon)
        
        header_title = QLabel("Installed Models")
        header_title.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_L, theme.FONT_WEIGHT_BOLD))
        header_title.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        header_layout.addWidget(header_title)
        
        header_layout.addStretch()
        
        self.current_count_label = QLabel("Loading...")
        self.current_count_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        self.current_count_label.setStyleSheet(f"""
            background: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 100);
            color: {theme.ACCENT_TEXT_COLOR.name()};
            padding: 4px 8px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 20);
        """)
        header_layout.addWidget(self.current_count_label)
        
        layout.addLayout(header_layout)
        
        # Models scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{ 
                background: transparent; 
                border: none; 
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 8);
                width: 6px;
                border-radius: 3px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba({theme.ACCENT_PRIMARY_COLOR.red()}, {theme.ACCENT_PRIMARY_COLOR.green()}, {theme.ACCENT_PRIMARY_COLOR.blue()}, 150);
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba({theme.ACCENT_HOVER_COLOR.red()}, {theme.ACCENT_HOVER_COLOR.green()}, {theme.ACCENT_HOVER_COLOR.blue()}, 180);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
        """)
        
        self.models_container = QWidget()
        self.models_layout = QVBoxLayout(self.models_container)
        self.models_layout.setSpacing(theme.PADDING_XS)  # Tighter spacing for compact design
        self.models_layout.setContentsMargins(2, 2, 2, 2)  # Small margins
        self.models_layout.addStretch()
        
        scroll_area.setWidget(self.models_container)
        layout.addWidget(scroll_area)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.rename_model_button = ModernButton("✏️ Rename")
        self.rename_model_button.setEnabled(False)
        self.rename_model_button.clicked.connect(self.renameSelectedModel)
        actions_layout.addWidget(self.rename_model_button)
        
        self.delete_model_button = ModernButton("🗑️ Delete")
        self.delete_model_button.setEnabled(False)
        self.delete_model_button.clicked.connect(self.deleteSelectedModel)
        actions_layout.addWidget(self.delete_model_button)
        
        actions_layout.addStretch()
        
        self.model_info_button = ModernButton("ℹ️ Info")
        self.model_info_button.setEnabled(False)
        self.model_info_button.clicked.connect(self.showModelInfo)
        actions_layout.addWidget(self.model_info_button)
        
        layout.addLayout(actions_layout)
        
        # Initialize button states
        self._updateActionButtons()
        
        return container
    
    def _createAvailableModelsSection(self):
        """Create modern available models section"""
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 8),
                    stop: 1 rgba(255, 255, 255, 4)
                );
                border: 1px solid rgba(255, 255, 255, 12);
                border-radius: 16px;
            }}
        """)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(theme.SHADOW_COLOR)
        container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(theme.PADDING_L, theme.PADDING_L, theme.PADDING_L, theme.PADDING_L)
        layout.setSpacing(theme.PADDING_M)
        
        # Section header
        header_layout = QHBoxLayout()
        header_icon = QLabel("🌐")
        header_icon.setFont(QFont("Arial", 20))
        header_layout.addWidget(header_icon)
        
        header_title = QLabel("Available Downloads")
        header_title.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_L, theme.FONT_WEIGHT_BOLD))
        header_title.setStyleSheet(f"color: {theme.PRIMARY_TEXT_COLOR.name()};")
        header_layout.addWidget(header_title)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("Expand your AI capabilities with these specialized models")
        subtitle.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_S))
        subtitle.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()};")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # Models grid scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        scroll_widget = QWidget()
        self.available_models_layout = QGridLayout(scroll_widget)
        self.available_models_layout.setSpacing(theme.PADDING_M)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return container
    
    def refreshCurrentModels(self):
        """Refresh the list of currently installed models"""
        # Clear previous models
        for i in reversed(range(self.models_layout.count() - 1)):  # Keep the stretch
            item = self.models_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        # Clear tracking lists
        self.model_items.clear()
        self.current_selected_model = None
        self._updateActionButtons()
        
        # Get models directory path
        models_dir = self._getModelsDirectory()
        
        if not os.path.exists(models_dir):
            self.current_count_label.setText("No models folder")
            return
        
        # Scan for .pth files
        model_files = []
        try:
            for file in os.listdir(models_dir):
                if file.endswith('.pth'):
                    file_path = os.path.join(models_dir, file)
                    file_size = os.path.getsize(file_path)
                    
                    # Format file size
                    if file_size > 1024 * 1024 * 1024:  # GB
                        size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
                    elif file_size > 1024 * 1024:  # MB
                        size_str = f"{file_size / (1024 * 1024):.1f} MB"
                    else:  # KB
                        size_str = f"{file_size / 1024:.1f} KB"
                    
                    model_files.append((file, size_str))
        
        except Exception as e:
            self.current_count_label.setText(f"Error: {str(e)}")
            return
        
        # Update count label
        self.current_count_label.setText(f"{len(model_files)} models")
        
        # Add model items with proper signal connections
        for model_name, size_str in model_files:
            model_item = ModernModelItem(model_name, size_str)
            
            # Connect signals
            model_item.itemSelected.connect(self._onModelItemSelected)
            model_item.itemDoubleClicked.connect(self._onModelItemDoubleClicked)
            
            # Add to layout and tracking
            self.models_layout.insertWidget(self.models_layout.count() - 1, model_item)
            self.model_items.append(model_item)
    
    def _onModelItemSelected(self, model_name):
        """Handle model item selection"""
        # Deselect all other items
        for item in self.model_items:
            item.setSelected(item.model_name == model_name)
        
        # Update current selection
        self.current_selected_model = model_name
        self._updateActionButtons()
    
    def _onModelItemDoubleClicked(self, model_name):
        """Handle model item double click - show info"""
        self.current_selected_model = model_name
        self.showModelInfo()
    
    def _updateActionButtons(self):
        """Update the state of action buttons based on selection"""
        has_selection = self.current_selected_model is not None
        self.rename_model_button.setEnabled(has_selection)
        self.delete_model_button.setEnabled(has_selection)
        self.model_info_button.setEnabled(has_selection)
    
    def loadAvailableModels(self):
        """Load and display available models for download from JSON file"""
        # Clear previous layout
        for i in reversed(range(self.available_models_layout.count())):
            item = self.available_models_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        # Show loading message
        loading_label = QLabel("Loading available models...")
        loading_label.setFont(QFont(theme.FONT_FAMILY_PRIMARY, theme.FONT_SIZE_M))
        loading_label.setStyleSheet(f"color: {theme.SECONDARY_TEXT_COLOR.name()}; padding: 20px;")
        loading_label.setAlignment(Qt.AlignCenter)
        self.available_models_layout.addWidget(loading_label, 0, 0)
        
        # Process the application to show the loading message
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Load available models from JSON file
        available_models = self._loadModelsFromJson()
        
        # Remove loading message
        loading_label.setParent(None)
        
        # Create model cards in grid layout
        row = 0
        col = 0
        max_cols = 2
        
        for model in available_models:
            model_card = ModernModelCard(model)
            model_card.downloadRequested.connect(self.downloadModel)
            self.available_models_layout.addWidget(model_card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Add stretch to push everything to top
        self.available_models_layout.setRowStretch(row + 1, 1)
    
    def _loadModelsFromJson(self):
        """Load available models from the models.json file"""
        try:
            # Get the directory where this dialog file is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_file_path = os.path.join(current_dir, "models.json")
            
            # Check if JSON file exists
            if not os.path.exists(json_file_path):
                QMessageBox.warning(self, "Models File Missing", 
                                   f"The models.json file was not found at:\n{json_file_path}\n\n"
                                   "Please ensure the models.json file exists in the model downloader directory.")
                return []
            
            # Read and parse JSON file
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                models = data.get('available_models', [])
                
                # Fetch actual file sizes for models with "TBD" size
                for model in models:
                    if model.get('size') == 'TBD':
                        try:
                            size = self._getRemoteFileSize(model['download_url'])
                            model['size'] = size
                        except:
                            model['size'] = 'Unknown'
                
                return models
                
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", 
                               f"Failed to parse models.json file:\n{str(e)}\n\n"
                               "Please check the JSON syntax in the models.json file.")
            return []
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Models", 
                               f"Failed to load available models:\n{str(e)}")
            return []
    
    def _getRemoteFileSize(self, url):
        """Get file size from remote URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.head(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            content_length = response.headers.get('content-length')
            if content_length:
                size_bytes = int(content_length)
                if size_bytes > 1024 * 1024 * 1024:  # GB
                    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
                elif size_bytes > 1024 * 1024:  # MB
                    return f"{size_bytes / (1024 * 1024):.0f} MB"
                else:  # KB
                    return f"{size_bytes / 1024:.0f} KB"
            return "Unknown"
        except:
            return "Unknown"
    
    def _getModelsDirectory(self):
        """Get the models directory path"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            return os.path.join(base_dir, "ai_studio", "models")
        else:
            return "ai_studio/models"
    
    def refreshAll(self):
        """Refresh both current and available models lists"""
        # Clear selection first
        self.current_selected_model = None
        self.refreshCurrentModels()
        self.loadAvailableModels()
    
    def renameSelectedModel(self):
        """Rename the selected model"""
        if not self.current_selected_model:
            return
        
        # Show input dialog for new name
        from PySide6.QtWidgets import QInputDialog, QLineEdit
        
        current_name = os.path.splitext(self.current_selected_model)[0]  # Remove .pth extension
        
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename Model", 
            f"Enter new name for '{current_name}':",
            QLineEdit.Normal,
            current_name
        )
        
        if ok and new_name and new_name != current_name:
            # Ensure .pth extension
            if not new_name.endswith('.pth'):
                new_name += '.pth'
            
            models_dir = self._getModelsDirectory()
            old_path = os.path.join(models_dir, self.current_selected_model)
            new_path = os.path.join(models_dir, new_name)
            
            try:
                # Check if new name already exists
                if os.path.exists(new_path):
                    QMessageBox.warning(self, "Rename Failed", f"A model named '{new_name}' already exists.")
                    return
                
                # Perform rename
                os.rename(old_path, new_path)
                QMessageBox.information(self, "Success", f"Model renamed to '{new_name}' successfully!")
                
                # Refresh the list
                self.refreshCurrentModels()
                
            except Exception as e:
                QMessageBox.critical(self, "Rename Failed", f"Failed to rename model:\n{str(e)}")
    
    def deleteSelectedModel(self):
        """Delete the selected model"""
        if not self.current_selected_model:
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Delete Model", 
            f"Are you sure you want to delete '{self.current_selected_model}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            models_dir = self._getModelsDirectory()
            file_path = os.path.join(models_dir, self.current_selected_model)
            
            try:
                os.remove(file_path)
                QMessageBox.information(self, "Success", f"Model '{self.current_selected_model}' deleted successfully!")
                
                # Refresh the list
                self.refreshCurrentModels()
                
            except Exception as e:
                QMessageBox.critical(self, "Delete Failed", f"Failed to delete model:\n{str(e)}")
    
    def showModelInfo(self):
        """Show detailed information about the selected model"""
        if not self.current_selected_model:
            return
        
        models_dir = self._getModelsDirectory()
        model_path = os.path.join(models_dir, self.current_selected_model)
        
        if not os.path.exists(model_path):
            QMessageBox.warning(self, "Model Not Found", f"The model file '{self.current_selected_model}' was not found.")
            return
        
        try:
            # Get file information
            file_size = os.path.getsize(model_path)
            
            # Format file size
            if file_size > 1024 * 1024 * 1024:  # GB
                size_str = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
            elif file_size > 1024 * 1024:  # MB
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            else:  # KB
                size_str = f"{file_size / 1024:.2f} KB"
            
            # Get file timestamps
            import datetime
            created_time = datetime.datetime.fromtimestamp(os.path.getctime(model_path))
            modified_time = datetime.datetime.fromtimestamp(os.path.getmtime(model_path))
            
            info_text = f"""Model Information

Name: {self.current_selected_model}
Size: {size_str} ({file_size:,} bytes)
Location: {model_path}

Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}
Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}

This AI model can be loaded in the AI Studio panel for enhanced music generation capabilities."""
            
            # Create custom info dialog
            info_dialog = QMessageBox(self)
            info_dialog.setWindowTitle(f"Model Info - {self.current_selected_model}")
            info_dialog.setText("Model Information")
            info_dialog.setDetailedText(info_text)
            info_dialog.setIcon(QMessageBox.Information)
            info_dialog.setStandardButtons(QMessageBox.Ok)
            
            # Style the dialog
            info_dialog.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {theme.DIALOG_BG_COLOR.name()};
                    color: {theme.PRIMARY_TEXT_COLOR.name()};
                }}
                QMessageBox QLabel {{
                    color: {theme.PRIMARY_TEXT_COLOR.name()};
                }}
            """)
            
            info_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get model information:\n{str(e)}")
    
    def downloadModel(self, model_info):
        """Download a model with progress tracking and error handling"""
        try:
            # Get models directory
            models_dir = self._getModelsDirectory()
            
            # Get filename from model info or extract from URL
            filename = model_info.get('filename')
            if not filename:
                filename = os.path.basename(model_info['download_url'])
                if not filename.endswith('.pth'):
                    filename += '.pth'
            
            save_path = os.path.join(models_dir, filename)
            
            # Check if model already exists
            if os.path.exists(save_path):
                reply = QMessageBox.question(
                    self,
                    "Model Already Exists",
                    f"The model '{filename}' already exists.\n\n"
                    "Do you want to download it again and overwrite the existing file?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
                
                # Remove existing file
                try:
                    os.remove(save_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to remove existing file:\n{str(e)}")
                    return
            
            # Create progress dialog
            progress_dialog = DownloadProgressDialog(model_info['name'], self)
            
            # Create download thread
            download_thread = ModelDownloadThread(
                model_info['download_url'],
                save_path,
                model_info['name'],
                self
            )
            
            # Connect signals
            download_thread.progressUpdated.connect(progress_dialog.updateProgress)
            download_thread.downloadCompleted.connect(self._onDownloadCompleted)
            download_thread.downloadFailed.connect(self._onDownloadFailed)
            
            # Store references
            progress_dialog.download_thread = download_thread
            
            # Start download
            download_thread.start()
            
            # Show progress dialog
            result = progress_dialog.exec()
            
            # Clean up if dialog was cancelled
            if result == QDialog.Rejected and download_thread.isRunning():
                download_thread.cancel()
                download_thread.wait(5000)  # Wait up to 5 seconds
                
        except Exception as e:
            QMessageBox.critical(self, "Download Error", f"Failed to start download:\n{str(e)}")
    
    def _onDownloadCompleted(self, message, model_name):
        """Handle successful download completion"""
        QMessageBox.information(self, "Download Successful", message)
        # Refresh the installed models list
        self.refreshCurrentModels()
        # Emit signal for external listeners
        self.modelDownloaded.emit(model_name)
    
    def _onDownloadFailed(self, error_message, model_name):
        """Handle download failure"""
        QMessageBox.critical(self, "Download Failed", 
                           f"Failed to download '{model_name}':\n\n{error_message}")
        # Emit signal for external listeners  
        # Note: We don't emit modelDeleted here since it was a download failure