
"""
Google Docs API simulation module.

This module provides a Python simulation of the Google Docs API, with in-memory state
and JSON persistence. It includes methods for document creation, retrieval, and updates.
"""
import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from google_home.SimulationEngine import utils 

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "cancel_schedules": "google_home.cancel_schedules_api.cancel_schedules",
    "details": "google_home.details_api.details",
    "devices": "google_home.devices_api.devices",
    "generate_home_automation": "google_home.generate_home_automation_api.generate_home_automation",
    "get_all_devices": "google_home.get_all_devices_api.get_all_devices",
    "get_devices": "google_home.get_devices_api.get_devices",
    "mutate": "google_home.mutate_api.mutate",
    "mutate_traits": "google_home.mutate_traits_api.mutate_traits",
    "run": "google_home.run_api.run",
    "search_home_events": "google_home.search_home_events_api.search_home_events",
    "see_devices": "google_home.see_devices_api.see_devices",
    "view_schedules": "google_home.view_schedules_api.view_schedules",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
