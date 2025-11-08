# google_slides/__init__.py

"""
Google Slides API Simulation

This package provides a simulation of the Google Slides API, allowing for
creating, retrieving, and manipulating presentations in a simulated environment.
"""

# Import submodules where API functions will be defined.
# For example, if your functions are in 'google_slides/presentations.py':
from . import presentations 
from . import SimulationEngine

# Import core components from the SimulationEngine
from .SimulationEngine.db import DB, load_state, save_state, save_state, load_state
from google_slides.SimulationEngine import utils # If any utils are to be directly exposed or used here

# Import error handling and logging utilities
import importlib
import os
import json
import tempfile
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "create_presentation": "google_slides.presentations.create_presentation",
    "get_presentation": "google_slides.presentations.get_presentation",
    "batch_update_presentation": "google_slides.presentations.batch_update_presentation",
    "get_page": "google_slides.presentations.get_page",
    "summarize_presentation": "google_slides.presentations.summarize_presentation"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())