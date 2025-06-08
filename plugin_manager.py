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
        
        # CRITICAL: Add plugins directory to BEGINNING of sys.path for exe compatibility
        plugins_path = os.path.abspath(self.plugins_dir)
        if plugins_path in sys.path:
            sys.path.remove(plugins_path)  # Remove if already there
        sys.path.insert(0, plugins_path)  # Insert at beginning for priority
        
        print(f"🔧 Plugin system: Added {plugins_path} to sys.path with priority")
        
        # Pre-load helper modules first (like api_helpers.py)
        helper_modules = []
        plugin_modules = []
        
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]  # Remove .py extension
                # Separate helpers from actual plugins
                if module_name in ['api_helpers', 'helpers', 'utils', 'common']:
                    helper_modules.append(module_name)
                else:
                    plugin_modules.append(module_name)
        
        # Load helper modules first
        for module_name in helper_modules:
            self.load_helper_module(module_name)
        
        # Then load actual plugins
        for module_name in plugin_modules:
                self.load_plugin(module_name)
    
    def load_helper_module(self, module_name):
        """
        Load a helper module (like api_helpers.py) without treating it as a plugin
        
        Args:
            module_name: Name of the helper module to load
        """
        try:
            print(f"📚 Loading helper module: {module_name}")
            
            # Try to load module with explicit path handling
            module_path = os.path.join(self.plugins_dir, f"{module_name}.py")
            if os.path.exists(module_path):
                print(f"Found helper file: {module_path}")
                
                # Use importlib.util.spec_from_file_location for direct file loading
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # CRITICAL: Add to sys.modules BEFORE exec for circular imports
                    sys.modules[module_name] = module  
                    spec.loader.exec_module(module)
                    print(f"✅ Helper module loaded: {module_name}")
                else:
                    print(f"❌ Failed to create spec for helper: {module_name}")
            else:
                print(f"⚠️ Helper file not found: {module_path}")
                
        except Exception as e:
            print(f"❌ Error loading helper module '{module_name}': {e}")
            import traceback
            print(f"   Full traceback: {traceback.format_exc()}")
    
    def load_plugin(self, module_name):
        """
        Load a plugin by module name
        
        Args:
            module_name: Name of the module to load
        """
        try:
            print(f"Attempting to load plugin: {module_name}")
            
            # Try to load module with explicit path handling for bundled apps
            module_path = os.path.join(self.plugins_dir, f"{module_name}.py")
            if os.path.exists(module_path):
                print(f"Found plugin file: {module_path}")
                
                # Check if module is already loaded (helper modules are pre-loaded)
                if module_name in sys.modules:
                    print(f"Module {module_name} already loaded, using existing")
                    module = sys.modules[module_name]
                else:
                    # Use importlib.util.spec_from_file_location for direct file loading
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module  # Add to sys.modules for dependency resolution
                        spec.loader.exec_module(module)
                        print(f"Successfully imported module: {module_name}")
                    else:
                        print(f"Failed to create module spec for: {module_name}")
                        return
            else:
                # Fallback to regular import
                print(f"Plugin file not found at {module_path}, trying regular import")
                try:
                    module = importlib.import_module(module_name)
                except ImportError as e:
                    print(f"Regular import also failed: {e}")
                    return
            
            # Look for plugin classes
            plugin_classes_found = 0
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                try:
                    # Check if this is a plugin class (not instance)
                    if (isinstance(attr, type) and 
                        issubclass(attr, PluginBase) and 
                        attr is not PluginBase):
                        
                        print(f"Found plugin class: {attr_name} in {module_name}")
                        
                        # Create an instance of the plugin
                        plugin_instance = attr()
                        plugin_id = f"{module_name}.{attr_name}"
                        self.plugins[plugin_id] = plugin_instance
                        plugin_classes_found += 1
                        print(f"✅ Loaded plugin: {plugin_instance.get_name()} ({plugin_id})")
                        
                except TypeError as te:
                    # Not a class or unrelated class
                    continue
                except Exception as pe:
                    print(f"⚠️ Error instantiating plugin class {attr_name}: {pe}")
                    continue
            
            if plugin_classes_found == 0:
                print(f"⚠️ No valid plugin classes found in {module_name}")
                
        except ImportError as e_imp:
            print(f"❌ Failed to load plugin '{module_name}' due to missing dependency:")
            print(f"   {e_imp}")
            print(f"   Please ensure that any libraries required by '{module_name}.py' are available.")
            print(f"   If this is a bundled application, the library might need to be included in the PyInstaller build.")
        except Exception as e:
            print(f"❌ Error loading plugin '{module_name}': {type(e).__name__} - {e}")
            import traceback
            print(f"   Full traceback: {traceback.format_exc()}")
    
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
