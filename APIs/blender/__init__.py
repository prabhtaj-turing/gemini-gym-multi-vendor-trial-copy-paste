"""
Blender API Simulation Module

This module provides a simulation of the Blender API, allowing for testing
and development of Blender workflows without requiring actual Blender access.
"""
from . import execution
from . import hyper3d
from . import object
from . import polyhaven
from . import scene

import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from blender.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
  "run_python_script_in_blender": "blender.execution.execute_blender_code",
  "get_hyper3d_status": "blender.hyper3d.get_hyper3d_status",
  "generate_hyper3d_model_via_text": "blender.hyper3d.generate_hyper3d_model_via_text",
  "generate_hyper3d_model_via_images": "blender.hyper3d.generate_hyper3d_model_via_images",
  "poll_hyper3d_rodin_job_status": "blender.hyper3d.poll_rodin_job_status",
  "import_hyper3d_generated_asset": "blender.hyper3d.import_generated_asset",
  "get_object_info": "blender.object.get_object_info",
  "set_object_texture": "blender.object.set_texture",
  "get_polyhaven_categories": "blender.polyhaven.get_polyhaven_categories",
  "search_polyhaven_assets": "blender.polyhaven.search_polyhaven_assets",
  "download_polyhaven_asset": "blender.polyhaven.download_polyhaven_asset",
  "get_polyhaven_status": "blender.polyhaven.get_polyhaven_status",
  "get_scene_info": "blender.scene.get_scene_info",
}



def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    global _function_map
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())