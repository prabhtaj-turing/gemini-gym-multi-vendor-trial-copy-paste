from .devices import commands
from . import devices

import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state, STATE_DICTS
from common_utils.init_utils import create_error_simulator, resolve_function_import
from sdm.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "list_structures": "sdm.structures.list_structures",
  "get_device_info": "sdm.devices.get_device_info",
  "get_events_list": "sdm.devices.get_events_list",
  "list_devices": "sdm.devices.list_devices",
  "execute_command": "sdm.devices.execute_command",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())

def load_image_map() -> dict:
    """
    Load the image map.

    Returns:
        dict: Returns the image mapping.
    """
    return STATE_DICTS