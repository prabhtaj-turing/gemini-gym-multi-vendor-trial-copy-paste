# cursor/__init__.py
import os  # For path manipulation like basename, dirname
import re
import logging
from typing import Any, Dict, List, Optional, Union  # Common type hints
import warnings
import subprocess
import shlex
import logging
import inspect

# This function requires 'thefuzz' library for fuzzy matching.
from thefuzz import process as fuzzy_process

# Import the DB object and utility functions
from .SimulationEngine.db import DB, load_state, save_state  # This is the application's in-memory database
from .SimulationEngine.utils import _log_util_message
from .SimulationEngine.llm_interface import call_llm


from .SimulationEngine.qdrant_config import QdrantManager, transform_qdrant_results_via_llm
from .SimulationEngine.chunker import chunk_codebase

from . import cursorAPI
import os
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import 
from .SimulationEngine.utils import add_line_numbers
from cursor.SimulationEngine import utils

# --- Logger Setup for this __init__.py module ---
# Get a logger instance specific to this top-level module.
logger = logging.getLogger(__name__) # Will typically be 'cursor' if run as package

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "list_dir": "cursor.cursorAPI.list_dir",
    "delete_file": "cursor.cursorAPI.delete_file",
    "file_search": "cursor.cursorAPI.file_search",
    "grep_search": "cursor.cursorAPI.grep_search",
    "edit_file": "cursor.cursorAPI.edit_file",
    "codebase_search": "cursor.cursorAPI.codebase_search",
    "read_file": "cursor.cursorAPI.read_file",
    "reapply": "cursor.cursorAPI.reapply",
    "run_terminal_cmd": "cursor.cursorAPI.run_terminal_cmd",
    "fetch_pull_request": "cursor.cursorAPI.fetch_pull_request",
    "add_to_memory": "cursor.cursorAPI.add_to_memory",
    "create_diagram": "cursor.cursorAPI.create_diagram",
    "fix_lints": "cursor.cursorAPI.fix_lints",
    "fetch_rules": "cursor.cursorAPI.fetch_rules",
    "deep_search": "cursor.cursorAPI.deep_search",
}

# Separate utils map for utility functions
_utils_map = {
    "hydrate_db_from_directory": "cursor.SimulationEngine.utils.hydrate_db_from_directory",
}

# You could potentially generate this map dynamically by inspecting the package,
# but that adds complexity and potential fragility. A manual map is often safer.
# --- Implement __getattr__ ---

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())