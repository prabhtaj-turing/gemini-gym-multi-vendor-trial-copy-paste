import importlib
from common_utils.error_handling import get_package_error_mode

from typing import Dict, Any, Optional

from . import puppeteerAPI

from .SimulationEngine.db import DB, load_state, save_state
from puppeteer.SimulationEngine import utils
from .SimulationEngine import custom_errors
from .SimulationEngine import models
from pydantic import ValidationError as PydanticValidationError
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
    "navigate": "puppeteer.puppeteerAPI.puppeteer_navigate",
    "screenshot": "puppeteer.puppeteerAPI.puppeteer_screenshot",
    "click": "puppeteer.puppeteerAPI.puppeteer_click",
    "fill": "puppeteer.puppeteerAPI.puppeteer_fill",
    "select_option": "puppeteer.puppeteerAPI.puppeteer_select",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())