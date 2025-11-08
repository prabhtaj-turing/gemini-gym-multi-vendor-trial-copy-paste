"""
Airline API Simulation

This package provides a simulation of the Airline API functionality.
"""
import os
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from airline.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "list_all_airports": "airline.airline.list_all_airports",
    "search_direct_flight": "airline.airline.search_direct_flight",
    "search_onestop_flight": "airline.airline.search_onestop_flight",
    "get_user_details": "airline.airline.get_user_details",
    "get_reservation_details": "airline.airline.get_reservation_details",
    "calculate": "airline.airline.calculate",
    "cancel_reservation": "airline.airline.cancel_reservation",
    "update_reservation_passengers": "airline.airline.update_reservation_passengers",
    "update_reservation_baggages": "airline.airline.update_reservation_baggages",
    "update_reservation_flights": "airline.airline.update_reservation_flights",
    "send_certificate": "airline.airline.send_certificate",
    "think": "airline.airline.think",
    "transfer_to_human_agents": "airline.airline.transfer_to_human_agents",
    "book_reservation": "airline.airline.book_reservation",
}

# Separate utils map for utility functions
_utils_map = {
    # Flight operations
    "get_flight": "airline.SimulationEngine.utils.get_flight",
    "search_flights": "airline.SimulationEngine.utils.search_flights",
    "search_onestop_flights": "airline.SimulationEngine.utils.search_onestop_flights",
    "add_flight": "airline.SimulationEngine.utils.add_flight",
    
    # User operations
    "get_user": "airline.SimulationEngine.utils.get_user",
    "create_user": "airline.SimulationEngine.utils.create_user",
    "add_payment_method_to_user": "airline.SimulationEngine.utils.add_payment_method_to_user",
    
    # Reservation operations
    "get_reservation": "airline.SimulationEngine.utils.get_reservation",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    global _function_map
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())