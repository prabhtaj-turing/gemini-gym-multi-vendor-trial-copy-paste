"""
Copilot API Simulation

This package provides a simulation of the Copilot API functionality.
It includes modules for code intelligence, file system operations, command line operations,
VS Code environment management, project setup, code quality, version control, web content
retrieval, and test file management.
"""
from . import code_intelligence
from . import code_quality_version_control
from . import command_line
from . import file_system
from . import project_setup
from . import test_file_management
from . import vscode_environment

import os
from common_utils.error_handling import get_package_error_mode
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from copilot.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    # Code Intelligence
    "semantic_search": "copilot.code_intelligence.semantic_search",
    "list_code_usages": "copilot.code_intelligence.list_code_usages",
    "grep_search": "copilot.code_intelligence.grep_search",
    
    # File System
    "file_search": "copilot.file_system.file_search",
    "read_file": "copilot.file_system.read_file",
    "list_dir": "copilot.file_system.list_dir",
    "insert_edit_into_file": "copilot.file_system.insert_edit_into_file",
    
    # Command Line
    "run_in_terminal": "copilot.command_line.run_in_terminal",
    "get_terminal_output": "copilot.command_line.get_terminal_output",
    
    # VS Code Environment
    "get_vscode_api": "copilot.vscode_environment.get_vscode_api",
    "install_extension": "copilot.vscode_environment.install_extension",
    
    # Project Setup
    "create_new_workspace": "copilot.project_setup.create_new_workspace",
    "get_project_setup_info": "copilot.project_setup.get_project_setup_info",
    "create_new_jupyter_notebook": "copilot.project_setup.create_new_jupyter_notebook",
    
    # Code Quality & Version Control
    "get_errors": "copilot.code_quality_version_control.get_errors",
    "get_changed_files": "copilot.code_quality_version_control.get_changed_files",
    
    # Test File Management
    "test_search": "copilot.test_file_management.test_search"
}

# Separate utils map for utility functions
_utils_map = {
    "hydrate_db_from_directory": "copilot.SimulationEngine.utils.hydrate_db_from_directory",
}

# You could potentially generate this map dynamically by inspecting the package,
# but that adds complexity and potential fragility. A manual map is often safer.
# --- Implement __getattr__ ---

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())