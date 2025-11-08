"""
Generic Reminders API Simulation

This package provides a simulation of the Generic Reminders API functionality.
It allows for creating, modifying, searching, and managing reminders in a simulated environment.
"""
import importlib
import os
import json
import tempfile
from typing import Optional
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state, load_state, save_state
from generic_reminders.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    # Core reminder operations
    "create_reminder": "generic_reminders.generic_reminders.create_reminder",
    "modify_reminder": "generic_reminders.generic_reminders.modify_reminder",
    "get_reminders": "generic_reminders.generic_reminders.get_reminders",
    "show_matching_reminders": "generic_reminders.generic_reminders.show_matching_reminders",
    "undo": "generic_reminders.generic_reminders.undo",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))


__all__ = list(_function_map.keys())
