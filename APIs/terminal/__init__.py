# terminal/__init__.py
import os
import logging
import tempfile

from .SimulationEngine.db import DB, load_state, save_state
from terminal.SimulationEngine import utils

from . import terminalAPI
import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from . import SimulationEngine

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "run_command": "terminal.terminalAPI.run_command",
}

# Separate utils map for utility functions
_utils_map = {
    "hydrate_db_from_directory": "terminal.SimulationEngine.utils.hydrate_db_from_directory",
}

# You could potentially generate this map dynamically by inspecting the package,
# but that adds complexity and potential fragility. A manual map is often safer.
# --- Implement __getattr__ ---

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())