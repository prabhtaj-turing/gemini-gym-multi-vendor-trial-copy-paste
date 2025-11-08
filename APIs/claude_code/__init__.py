"""Initializes the claude_code package, exporting key functions and setting up error simulation."""

import os

from common_utils.error_handling import get_package_error_mode
from common_utils.init_utils import create_error_simulator, resolve_function_import

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

_function_map = {
    # File system tools
    "readFile": "claude_code.file_system.read_file",
    "listFiles": "claude_code.file_system.list_files",
    "searchGlob": "claude_code.file_system.search_glob",
    "grep": "claude_code.file_system.grep",
    "editFile": "claude_code.file_system.edit_file",

    # Shell tools
    "bash": "claude_code.shell.bash",

    # Todo tools
    "todoWrite": "claude_code.todo.todo_write",

    # Web tools
    "webFetch": "claude_code.web.web_fetch",

    # Task tools
    "task": "claude_code.task.task",

    # Thinking tools
    "think": "claude_code.thinking.think",
    "codeReview": "claude_code.thinking.code_review",
}

# Separate utils map for utility functions
_utils_map = {
    # Path and workspace utilities
    "resolve_workspace_path": "claude_code.SimulationEngine.utils.resolve_workspace_path",
    "set_enable_common_file_system": "claude_code.SimulationEngine.utils.set_enable_common_file_system",
    "update_common_directory": "claude_code.SimulationEngine.utils.update_common_directory",
    "with_common_file_system": "claude_code.SimulationEngine.utils.with_common_file_system",
    
    # Metadata and state utilities
    "collect_pre_command_metadata_state": "claude_code.SimulationEngine.utils.collect_pre_command_metadata_state",
    "collect_post_command_metadata_state": "claude_code.SimulationEngine.utils.collect_post_command_metadata_state",
    "preserve_unchanged_change_times": "claude_code.SimulationEngine.utils.preserve_unchanged_change_times",
}

def __getattr__(name: str):
    """Dynamically import and return a function from the package."""
    return resolve_function_import(name, _function_map, error_simulator)


def __dir__():
    """Provide a list of available names in the package."""
    return sorted(list(_function_map.keys()))


__all__ = list(_function_map.keys())
