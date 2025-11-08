"""
Generic Media API Simulation package.
This __init__.py uses dynamic imports for its main API functions.
"""

import importlib
from typing import Any, List  # For __getattr__ type hinting if needed, though not strictly necessary here.
import os
import json
import tempfile
from generic_media.SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from generic_media.SimulationEngine import utils  # This would import generic_media.SimulationEngine.utils
from common_utils.error_handling import get_package_error_mode
from generic_media.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "play": "generic_media.play_api.play",
    "search": "generic_media.search_api.search",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())