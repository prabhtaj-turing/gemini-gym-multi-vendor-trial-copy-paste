
# google_maps_live/__init__.py
from google_maps_live.SimulationEngine import utils
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
  "find_directions": "google_maps_live.directions.find_directions",
  "navigate": "google_maps_live.directions.navigate",
  "query_places": "google_maps_live.places.query_places",
  "lookup_place_details": "google_maps_live.places.lookup_place_details",
  "analyze_places": "google_maps_live.places.analyze_places",
  "show_on_map": "google_maps_live.places.show_on_map"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
