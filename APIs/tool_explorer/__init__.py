"""
Tool Explorer API Simulation

This package provides tools for inspecting the available services and their documentation.
"""
import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from .get_tools import fetch_documentation, list_services, list_tools


# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map - only tool explorer functions
_function_map = {
    "list_services": "tool_explorer.get_tools.list_services",
    "list_tools": "tool_explorer.get_tools.list_tools",
    "fetch_documentation": "tool_explorer.get_tools.fetch_documentation",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
