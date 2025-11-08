"""
Generic Tools API Simulation

This package provides tools for inspecting the available services and their documentation.
"""
import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from . import code_execution

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "write_to_file": "code_execution.code_execution.write_to_file",
    "execute_script": "code_execution.code_execution.execute_script",
    "execute_code": "code_execution.code_execution.execute_code",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
