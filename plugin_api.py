# plugin_api.py
import pretty_midi
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class PluginBase(ABC):
    """Base class for all piano roll plugins"""
    
    def __init__(self):
        self.name = "Base Plugin"
        self.description = "Base plugin class"
        self.author = "Unknown"
        self.version = "1.0"
        self.parameters = {}
        
    @abstractmethod
    def generate(self, existing_notes: List[pretty_midi.Note] = None, **kwargs) -> List[pretty_midi.Note]:
        """
        Generate MIDI notes based on the plugin's algorithm
        
        Args:
            existing_notes: Optional list of existing notes to build upon
            **kwargs: Additional parameters specific to the plugin
            
        Returns:
            List of generated pretty_midi.Note objects
        """
        pass
    
    def get_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Return information about the plugin's parameters
        
        Returns:
            Dictionary mapping parameter names to their metadata
            Example: {"param_name": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.5}}
        """
        return self.parameters
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize parameters
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            Dictionary of validated parameter values
        """
        validated = {}
        for param_name, param_value in params.items():
            if param_name in self.parameters:
                param_info = self.parameters[param_name]
                # Type conversion
                if param_info.get("type") == "int":
                    param_value = int(param_value)
                elif param_info.get("type") == "float":
                    param_value = float(param_value)
                elif param_info.get("type") == "bool":
                    param_value = bool(param_value)
                
                # Range validation
                if "min" in param_info and param_value < param_info["min"]:
                    param_value = param_info["min"]
                if "max" in param_info and param_value > param_info["max"]:
                    param_value = param_info["max"]
                
                validated[param_name] = param_value
        
        return validated
    
    def get_name(self) -> str:
        """Get the plugin name"""
        return self.name
    
    def get_description(self) -> str:
        """Get the plugin description"""
        return self.description
    
    def get_author(self) -> str:
        """Get the plugin author"""
        return self.author
    
    def get_version(self) -> str:
        """Get the plugin version"""
        return self.version