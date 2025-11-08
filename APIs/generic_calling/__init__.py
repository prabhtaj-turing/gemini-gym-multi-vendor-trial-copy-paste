"""
Generic Calling API Simulation

This package provides a unified interface for making calls through different services
(phone and WhatsApp) with recipient management and choice handling.
"""
import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from generic_calling.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "make_call": "generic_calling.generic_calling.make_call",
    "show_call_recipient_choices": "generic_calling.generic_calling.show_call_recipient_choices",
    "show_call_recipient_not_found_or_specified": "generic_calling.generic_calling.show_call_recipient_not_found_or_specified",
    "find_recipients": "generic_calling.SimulationEngine.utils.find_recipients",
    "check_geofencing": "generic_calling.SimulationEngine.utils.check_geofencing"
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())