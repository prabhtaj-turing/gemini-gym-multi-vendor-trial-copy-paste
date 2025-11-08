"""
MySQL API Simulation Module

This module provides a simulation of the MySQL API, allowing for testing
and development of MySQL workflows without requiring actual MySQL access.
"""
import os
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode

# TODO: Add utils to the API
"""
Test cases are failing when utils is imported.
"""
# from mysql.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "query": "mysql.mysql_handler.query",
  "get_resources_list": "mysql.mysql_handler.get_resources_list",
  "get_resource": "mysql.mysql_handler.get_resource",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())