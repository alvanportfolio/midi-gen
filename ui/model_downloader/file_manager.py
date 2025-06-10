# File Manager Module
# This module handles file operations for AI models (rename, delete, organize, etc.)

import os
import sys
import shutil
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QInputDialog, QMessageBox

class ModelFileManager(QObject):
    """
    Manages AI model files and operations
    
    Future implementation will include:
    - Safe file renaming with validation
    - Model file organization and categorization
    - Backup and restore functionality
    - Batch operations on multiple models
    """
    
    # Signals
    fileRenamed = Signal(str, str)    # Emitted when file is renamed (old_name, new_name)
    fileDeleted = Signal(str)         # Emitted when file is deleted (file_name)
    fileMoved = Signal(str, str)      # Emitted when file is moved (old_path, new_path)
    operationFailed = Signal(str, str)  # Emitted on error (operation, error_message)
    
    def __init__(self):
        super().__init__()
        self.models_directory = self._get_models_directory()
    
    def _get_models_directory(self):
        """Get the models directory path"""
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = os.path.dirname(sys.executable)
            return os.path.join(base_dir, "ai_studio", "models")
        else:
            # Development mode
            return "ai_studio/models"
    
    def rename_model(self, old_name, new_name):
        """
        Rename a model file
        
        Args:
            old_name (str): Current filename
            new_name (str): New filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate new name
            if not self._validate_filename(new_name):
                self.operationFailed.emit("rename", f"Invalid filename: {new_name}")
                return False
            
            # Ensure .pth extension
            if not new_name.endswith('.pth'):
                new_name += '.pth'
            
            old_path = os.path.join(self.models_directory, old_name)
            new_path = os.path.join(self.models_directory, new_name)
            
            # Check if old file exists
            if not os.path.exists(old_path):
                self.operationFailed.emit("rename", f"File not found: {old_name}")
                return False
            
            # Check if new name already exists
            if os.path.exists(new_path):
                self.operationFailed.emit("rename", f"File already exists: {new_name}")
                return False
            
            # Perform rename
            os.rename(old_path, new_path)
            self.fileRenamed.emit(old_name, new_name)
            return True
            
        except Exception as e:
            self.operationFailed.emit("rename", f"Error renaming file: {str(e)}")
            return False
    
    def delete_model(self, filename):
        """
        Delete a model file
        
        Args:
            filename (str): Name of the file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = os.path.join(self.models_directory, filename)
            
            # Check if file exists
            if not os.path.exists(file_path):
                self.operationFailed.emit("delete", f"File not found: {filename}")
                return False
            
            # Delete the file
            os.remove(file_path)
            self.fileDeleted.emit(filename)
            return True
            
        except Exception as e:
            self.operationFailed.emit("delete", f"Error deleting file: {str(e)}")
            return False
    
    def move_model(self, filename, destination_directory):
        """
        Move a model file to a different directory
        
        Args:
            filename (str): Name of the file to move
            destination_directory (str): Destination directory path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source_path = os.path.join(self.models_directory, filename)
            dest_path = os.path.join(destination_directory, filename)
            
            # Check if source file exists
            if not os.path.exists(source_path):
                self.operationFailed.emit("move", f"Source file not found: {filename}")
                return False
            
            # Create destination directory if it doesn't exist
            os.makedirs(destination_directory, exist_ok=True)
            
            # Check if destination file already exists
            if os.path.exists(dest_path):
                self.operationFailed.emit("move", f"Destination file already exists: {dest_path}")
                return False
            
            # Move the file
            shutil.move(source_path, dest_path)
            self.fileMoved.emit(source_path, dest_path)
            return True
            
        except Exception as e:
            self.operationFailed.emit("move", f"Error moving file: {str(e)}")
            return False
    
    def copy_model(self, filename, destination_directory, new_name=None):
        """
        Copy a model file to a different location
        
        Args:
            filename (str): Name of the file to copy
            destination_directory (str): Destination directory path
            new_name (str): Optional new name for the copied file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source_path = os.path.join(self.models_directory, filename)
            dest_filename = new_name if new_name else filename
            dest_path = os.path.join(destination_directory, dest_filename)
            
            # Check if source file exists
            if not os.path.exists(source_path):
                self.operationFailed.emit("copy", f"Source file not found: {filename}")
                return False
            
            # Create destination directory if it doesn't exist
            os.makedirs(destination_directory, exist_ok=True)
            
            # Copy the file
            shutil.copy2(source_path, dest_path)
            return True
            
        except Exception as e:
            self.operationFailed.emit("copy", f"Error copying file: {str(e)}")
            return False
    
    def get_model_info(self, filename):
        """
        Get detailed information about a model file
        
        Args:
            filename (str): Name of the model file
            
        Returns:
            dict: Dictionary containing file information
        """
        try:
            file_path = os.path.join(self.models_directory, filename)
            
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            
            return {
                'filename': filename,
                'path': file_path,
                'size_bytes': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'accessed_time': stat.st_atime
            }
            
        except Exception as e:
            self.operationFailed.emit("info", f"Error getting file info: {str(e)}")
            return None
    
    def list_models(self):
        """
        Get a list of all model files in the models directory
        
        Returns:
            list: List of model filenames
        """
        try:
            if not os.path.exists(self.models_directory):
                return []
            
            model_files = []
            for file in os.listdir(self.models_directory):
                if file.endswith('.pth'):
                    model_files.append(file)
            
            return sorted(model_files)
            
        except Exception as e:
            self.operationFailed.emit("list", f"Error listing models: {str(e)}")
            return []
    
    def create_backup(self, filename, backup_directory=None):
        """
        Create a backup of a model file
        
        Args:
            filename (str): Name of the file to backup
            backup_directory (str): Optional custom backup directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if backup_directory is None:
                backup_directory = os.path.join(self.models_directory, "backups")
            
            # Create backup directory if it doesn't exist
            os.makedirs(backup_directory, exist_ok=True)
            
            # Generate backup filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.splitext(filename)[0]}_{timestamp}.pth"
            
            return self.copy_model(filename, backup_directory, backup_filename)
            
        except Exception as e:
            self.operationFailed.emit("backup", f"Error creating backup: {str(e)}")
            return False
    
    def _validate_filename(self, filename):
        """
        Validate a filename for safety and compatibility
        
        Args:
            filename (str): Filename to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # TODO: Implement comprehensive filename validation
        # - Check for invalid characters
        # - Ensure reasonable length
        # - Check for reserved names
        # - Validate extension
        
        if not filename:
            return False
        
        # Basic validation for now
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in filename:
                return False
        
        return True
    
    def organize_models_by_category(self):
        """
        Organize models into subdirectories by category
        
        Future implementation will:
        - Analyze model names for category hints
        - Create category subdirectories
        - Move models to appropriate categories
        - Maintain a category mapping file
        """
        # TODO: Implement model organization by category
        pass
    
    def clean_temporary_files(self):
        """
        Clean up temporary files and incomplete downloads
        
        Returns:
            int: Number of files cleaned up
        """
        # TODO: Implement cleanup of temporary files
        # - Find .tmp files
        # - Find incomplete downloads
        # - Remove old backup files
        # - Clear cache files
        return 0 