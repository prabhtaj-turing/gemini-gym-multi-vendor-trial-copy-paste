"""
CES Loyalty Auth API Simulation

This package provides a simulation of the CES Loyalty Auth API functionality.
"""
import os
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "get_authenticated_customer_profile": "ces_loyalty_auth.loyalty_auth.get_authenticated_customer_profile",
    "manage_customer_authentication": "ces_loyalty_auth.loyalty_auth.manage_customer_authentication",
    "get_pre_authentication_call_data": "ces_loyalty_auth.loyalty_auth.get_pre_authentication_call_data",
    "record_call_outcome_and_disconnect": "ces_loyalty_auth.loyalty_auth.record_call_outcome_and_disconnect",
    "transfer_to_live_agent": "ces_loyalty_auth.loyalty_auth.transfer_to_live_agent",
    "enroll_in_offer": "ces_loyalty_auth.loyalty_auth.enroll_in_offer",
    
    # terminal action functions
    "done": "ces_loyalty_auth.loyalty_auth.done",
    "fail": "ces_loyalty_auth.loyalty_auth.fail",
    "cancel": "ces_loyalty_auth.loyalty_auth.cancel",
    "escalate": "ces_loyalty_auth.loyalty_auth.escalate",
}

_utils_map = {
    # getter utility functions
    "get_auth_status": "ces_loyalty_auth.SimulationEngine.utils.get_auth_status",
    "get_conversation_status": "ces_loyalty_auth.SimulationEngine.utils.get_conversation_status",
    "get_customer_account_number_from_preauth": "ces_loyalty_auth.SimulationEngine.utils.get_customer_account_number_from_preauth",
    "get_customer_name_from_preauth": "ces_loyalty_auth.SimulationEngine.utils.get_customer_name_from_preauth",
    "get_loyalty_offers": "ces_loyalty_auth.SimulationEngine.utils.get_loyalty_offers",
    "get_offer_enrollment": "ces_loyalty_auth.SimulationEngine.utils.get_offer_enrollment",
    "get_session_status": "ces_loyalty_auth.SimulationEngine.utils.get_session_status",

    # setter utility functions
    "set_auth_result": "ces_loyalty_auth.SimulationEngine.utils.set_auth_result",
    "set_customer_profile": "ces_loyalty_auth.SimulationEngine.utils.set_customer_profile",
    "set_preauth_data": "ces_loyalty_auth.SimulationEngine.utils.set_preauth_data",
    "update_auth_status": "ces_loyalty_auth.SimulationEngine.utils.update_auth_status",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)


def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
