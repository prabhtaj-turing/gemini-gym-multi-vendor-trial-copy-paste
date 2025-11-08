
# google_maps/__init__.py
# Import the Places class from the Places module. This allows us to use the Places class in other files
from google_maps import Places
from google_maps.Places import Photos
from google_maps.SimulationEngine.db import DB, load_state, save_state
from google_maps.SimulationEngine import utils
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
  "get_place_autocomplete_predictions": "google_maps.Places.autocomplete",
  "get_place_details": "google_maps.Places.get",
  "search_nearby_places": "google_maps.Places.searchNearby",
  "search_places_by_text": "google_maps.Places.searchText",
  "get_place_photo_media": "google_maps.Places.Photos.getMedia"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
