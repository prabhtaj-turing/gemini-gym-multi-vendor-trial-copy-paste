"""
Generic Service API Simulation

This package provides a template for creating a simulated API.
It demonstrates a structured approach to defining tools, managing state, 
handling errors and the E2E components of a simulated API
"""

import os
from common_utils.error_handling import get_package_error_mode
from common_utils.init_utils import create_error_simulator, resolve_function_import
from service_template.SimulationEngine import utils

# Get the directory of the current file (__init__.py)
_INIT_PY_DIR = os.path.dirname(__file__)

# Create an error simulator instance. This utility reads the error_config.json
# and error_definitions.json to simulate potential failures for each tool.
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package (e.g., 'development', 'production').
# This can be used to control error simulation behavior.
ERROR_MODE = get_package_error_mode()

# This dictionary maps the public-facing tool name to its actual implementation
# path within the service. The format is:
# "tool_name": "service_name.module_name.function_name"
#
# TODO: Update 'service_template' to your actual service name (e.g., 'calendar')
# and 'tool' to your actual function name.
_function_map = {
    "tool": "service_template.entity.tool",
    # Add other tools here, for example:
    # "get_entity": "service_template.entity.get_entity",
}

def __getattr__(name: str):
    """
    This function is called when an attribute (like a tool function) is accessed
    on the package. It uses the resolve_function_import utility to dynamically
    import and return the correct function from the _function_map, wrapping it
    with the error simulator.
    """
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    """
    This function informs tools like `help()` and tab-completion about the
    available functions in this package.
    """
    return sorted(set(globals().keys()) | set(_function_map.keys()))

# This list explicitly declares the public API of the module.
__all__ = list(_function_map.keys())
