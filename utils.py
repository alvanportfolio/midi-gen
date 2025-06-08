import os
import sys

def ensure_ai_dependencies():
    """
    Ensure AI dependencies are properly available
    Since TMIDIX and x_transformer_2_3_1 are now in site-packages,
    we just need to pre-import core dependencies
    """
    try:
        # Pre-import critical dependencies
        import struct
        import traceback
        import tempfile
        import threading
        import time
        import datetime
        import collections
        import itertools
        import functools
        import warnings
        import statistics
        import abc
        import typing
        
        # Third-party dependencies
        import tqdm
        import torch
        import torch.nn
        import torch.nn.functional
        import numpy
        import random
        import math
        import copy
        import pickle
        import einops
        import einx
        
        # Make them available in builtins
        import builtins
        # Standard library
        builtins.struct = struct
        builtins.traceback = traceback
        builtins.tempfile = tempfile
        builtins.threading = threading
        builtins.time = time
        builtins.datetime = datetime
        builtins.collections = collections
        builtins.itertools = itertools
        builtins.functools = functools
        builtins.warnings = warnings
        builtins.statistics = statistics
        builtins.abc = abc
        builtins.typing = typing
        
        # Third-party
        builtins.tqdm = tqdm
        builtins.torch = torch
        builtins.np = numpy
        builtins.numpy = numpy
        builtins.random = random
        builtins.math = math
        builtins.copy = copy
        builtins.pickle = pickle
        builtins.einops = einops
        builtins.einx = einx
        
        print("✅ Pre-imported AI dependencies successfully")
        return True
        
    except Exception as e:
        print(f"⚠️ Warning: Could not pre-import some AI dependencies: {e}")
        return False

def get_resource_path(relative_path: str, app_is_frozen: bool = hasattr(sys, 'frozen'), is_external_to_bundle: bool = False) -> str:
    """
    Get the absolute path to a resource.
    - In a PyInstaller bundle:
        - If is_external_to_bundle is True (e.g., for a 'plugins' folder next to the .exe):
          Uses the directory of the executable (sys.executable).
        - Otherwise (e.g., for bundled 'assets', 'soundbank' in _MEIPASS):
          Uses PyInstaller's temporary folder (sys._MEIPASS).
    - In development mode (not bundled):
      Uses paths relative to this script's directory (utils.py, assumed to be project root).
    """
    if app_is_frozen: # Running as a PyInstaller bundle
        if is_external_to_bundle:
            # Path relative to the executable (e.g., for a 'plugins' folder)
            base_path = os.path.dirname(sys.executable)
        else:
            # Path within the PyInstaller bundle (e.g., for 'assets', 'soundbank')
            try:
                base_path = sys._MEIPASS
            except AttributeError:
                # Fallback if _MEIPASS is not set for some reason
                print("Warning: sys._MEIPASS not found in frozen app, falling back to executable directory for bundled resource.")
                base_path = os.path.dirname(sys.executable)
    else:
        # Development mode: utils.py is at the project root.
        # Paths are relative to the project root.
        base_path = os.path.abspath(os.path.dirname(__file__)) 
        
    return os.path.join(base_path, relative_path)

if __name__ == '__main__':
    # Test
    print("Testing AI dependency setup...")
    success = ensure_ai_dependencies()
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Test AI module imports
    try:
        import TMIDIX
        print("✅ TMIDIX can be imported from site-packages")
        if hasattr(TMIDIX, '__file__'):
            print(f"   Location: {TMIDIX.__file__}")
    except ImportError as e:
        print(f"❌ TMIDIX import failed: {e}")
    
    try:
        import x_transformer_2_3_1
        print("✅ x_transformer_2_3_1 can be imported from site-packages")
        if hasattr(x_transformer_2_3_1, '__file__'):
            print(f"   Location: {x_transformer_2_3_1.__file__}")
    except ImportError as e:
        print(f"❌ x_transformer_2_3_1 import failed: {e}")