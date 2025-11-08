import importlib
import os
import json
import tempfile
from typing import Dict
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from gemini_cli.SimulationEngine import utils
from gemini_cli import SimulationEngine

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# ---------------------------------------------------------------------------
# Map external tool names → internal implementation paths.  Real functions
# will be filled in incrementally; for now they raise NotImplementedError.
# ---------------------------------------------------------------------------

_function_map = {
    "list_directory": "gemini_cli.file_system_api.list_directory",
    "read_file": "gemini_cli.file_system_api.read_file",
    "write_file": "gemini_cli.file_system_api.write_file",
    "glob": "gemini_cli.file_system_api.glob",
    "search_file_content": "gemini_cli.file_system_api.grep_search",
    "replace": "gemini_cli.file_system_api.replace",
    "read_many_files": "gemini_cli.read_many_files_api.read_many_files",
    "save_memory": "gemini_cli.memory.save_memory",
    "run_shell_command": "gemini_cli.shell_api.run_shell_command"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())