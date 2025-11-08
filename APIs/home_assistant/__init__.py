
from typing import Any, Dict, List, Literal, Optional, Union

# Import the DB object and utility functions
from .SimulationEngine.db import DB, load_state, save_state  # This is the application's in-memory database
from home_assistant.SimulationEngine import utils  # Utility functions
from . import devices
import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from common_utils.init_utils import create_error_simulator, resolve_function_import 

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "get_state": "home_assistant.devices.get_state",
    "toggle_device": "home_assistant.devices.toggle_device",
    "list_devices": "home_assistant.devices.list_devices",
    "get_id_by_name": "home_assistant.devices.get_id_by_name",
    "get_device_info": "home_assistant.devices.get_device_info",
    "set_device_property": "home_assistant.devices.set_device_property",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
