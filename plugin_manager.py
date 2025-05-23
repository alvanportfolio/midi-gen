# plugin_manager.py
import os
import sys
import importlib
import importlib.util
from typing import List, Dict, Optional, Any
import pretty_midi

from plugin_api import PluginBase
from utils import get_resource_path # Import the new helper

DEFAULT_PLUGINS_DIR_NAME = "plugins"

class PluginManager:
    """Manages the discovery, loading, and execution of plugins"""
    
    def __init__(self, plugins_dir_name: str = DEFAULT_PLUGINS_DIR_NAME):
        # Resolve the absolute path to the plugins directory
        # For plugins, we want to look in a directory next to the executable when bundled.
        self.plugins_dir = get_resource_path(plugins_dir_name, is_external_to_bundle=True)
        print(f"PluginManager: Using plugins directory: {self.plugins_dir}")
        
        self.plugins = {}  # Map plugin IDs to plugin instances
        self.discover_plugins()
    
    def discover_plugins(self):
        """Discover and load all plugins from the plugins directory"""
        # Ensure the plugins directory exists
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
        
        # Add plugins directory to sys.path if not already there
        if self.plugins_dir not in sys.path:
            sys.path.append(os.path.abspath(self.plugins_dir))
        
        # Look for python files in the plugins directory
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]  # Remove .py extension
                self.load_plugin(module_name)
    
    def load_plugin(self, module_name):
        """
        Load a plugin by module name
        
        Args:
            module_name: Name of the module to load
        """
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Look for plugin classes
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                try:
                    # Check if this is a plugin class (not instance)
                    if (isinstance(attr, type) and 
                        issubclass(attr, PluginBase) and 
                        attr is not PluginBase):
                        # Create an instance of the plugin
                        plugin_instance = attr()
                        plugin_id = f"{module_name}.{attr_name}"
                        self.plugins[plugin_id] = plugin_instance
                        print(f"Loaded plugin: {plugin_instance.get_name()} ({plugin_id})")
                except TypeError:
                    # Not a class or unrelated class
                    continue
        except ImportError as e_imp:
            print(f"Failed to load plugin '{module_name}' due to missing dependency: {e_imp}")
            print(f"  Please ensure that any libraries required by '{module_name}.py' are available.")
            print(f"  If this is a bundled application, the library might need to be included in the PyInstaller build.")
        except Exception as e:
            print(f"Error loading plugin '{module_name}': {type(e).__name__} - {e}")
    
    def get_plugin_list(self) -> List[Dict[str, str]]:
        """
        Get a list of all loaded plugins
        
        Returns:
            List of dictionaries containing plugin information
        """
        return [
            {
                "id": plugin_id,
                "name": plugin.get_name(),
                "description": plugin.get_description(),
                "author": plugin.get_author(),
                "version": plugin.get_version()
            }
            for plugin_id, plugin in self.plugins.items()
        ]
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """
        Get a plugin by ID
        
        Args:
            plugin_id: ID of the plugin to get
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(plugin_id)
    
    def generate_notes(self, 
                       plugin_id: str, 
                       existing_notes: Optional[List[pretty_midi.Note]] = None, 
                       parameters: Optional[Dict[str, Any]] = None
                       ) -> List[pretty_midi.Note]:
        """
        Generate notes using a specific plugin
        
        Args:
            plugin_id: ID of the plugin to use
            existing_notes: Optional list of existing notes
            parameters: Optional dictionary of parameters
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin not found: {plugin_id}")
        
        current_params = parameters or {}
        # Assuming validate_parameters can handle empty dict if params is None
        validated_params = plugin.validate_parameters(current_params) 
        
        # Ensure an empty list is passed if existing_notes is None,
        # if the plugin's generate method expects a list.
        notes_to_pass = existing_notes if existing_notes is not None else []
        
        return plugin.generate(notes_to_pass, **validated_params)
