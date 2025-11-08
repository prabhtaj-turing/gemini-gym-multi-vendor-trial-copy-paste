# ces_flights/__init__.py

import os
import sys
from typing import Dict, Any
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode

from . import ces_flights
from .SimulationEngine.db import DB, load_state, save_state

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Add current directory to path for imports
if _INIT_PY_DIR not in sys.path:
    sys.path.insert(0, _INIT_PY_DIR)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "search_flights": "ces_flights.ces_flights.search_flights",
    "book_flight": "ces_flights.ces_flights.book_flight",
    "escalate": "ces_flights.ces_flights.escalate",
    "done": "ces_flights.ces_flights.done",
    "fail": "ces_flights.ces_flights.fail",
    "cancel": "ces_flights.ces_flights.cancel"
}

# Separate utils map for utility functions
_utils_map = {
    # Conversation status functions
    "get_end_of_conversation_status": "ces_flights.SimulationEngine.utils.get_end_of_conversation_status",
    
    # Currency utilities
    "is_valid_currency": "ces_flights.SimulationEngine.utils.is_valid_currency",
    "get_supported_currencies": "ces_flights.SimulationEngine.utils.get_supported_currencies",
    "convert_price": "ces_flights.SimulationEngine.utils.convert_price",
    "convert_price_to_usd": "ces_flights.SimulationEngine.utils.convert_price_to_usd",
    
    # Date and time utilities
    "current_timestamp": "ces_flights.SimulationEngine.utils.current_timestamp",
    "validate_date": "ces_flights.SimulationEngine.utils.validate_date",
    "validate_date_range": "ces_flights.SimulationEngine.utils.validate_date_range",
    "validate_booking_date_range": "ces_flights.SimulationEngine.utils.validate_booking_date_range",
    "process_date_without_year": "ces_flights.SimulationEngine.utils.process_date_without_year",
    "validate_date_in_range": "ces_flights.SimulationEngine.utils.validate_date_in_range",
    
    # String and data validation utilities
    "validate_string": "ces_flights.SimulationEngine.utils.validate_string",
    "ensure_json_serializable": "ces_flights.SimulationEngine.utils.ensure_json_serializable",
    
    # City format utilities
    "convert_city_format": "ces_flights.SimulationEngine.utils.convert_city_format",
    
    # Workflow validation utilities
    "validate_workflow_order": "ces_flights.SimulationEngine.utils.validate_workflow_order",
    "validate_booking_readiness": "ces_flights.SimulationEngine.utils.validate_booking_readiness",
    
    # State management utilities
    "create_conversation_state_manager": "ces_flights.SimulationEngine.utils.create_conversation_state_manager",
    "validate_retry_logic": "ces_flights.SimulationEngine.utils.validate_retry_logic",
    "update_env_var": "ces_flights.SimulationEngine.utils.update_env_var",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    """Return list of available public functions and utilities."""
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())


