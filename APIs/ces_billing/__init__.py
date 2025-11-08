"""CES Billing API Service.

This module provides a Verizon billing assistant API that can:
- Retrieve billing information and balances
- Process AutoPay enrollments
- Handle customer escalations
- Provide next bill estimates
- Manage conversation flows

The service follows the conversation flow defined in the billing assistant specification.
"""

from . import SimulationEngine
from . import ces_billing_service
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.error_handling import get_package_error_mode

import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode

from .SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "escalate": "ces_billing.ces_billing_service.escalate",
    "fail": "ces_billing.ces_billing_service.fail",
    "cancel": "ces_billing.ces_billing_service.cancel",
    "autopay": "ces_billing.ces_billing_service.autopay",
    "bill": "ces_billing.ces_billing_service.bill",
    "default_start_flow": "ces_billing.ces_billing_service.default_start_flow",
    "ghost": "ces_billing.ces_billing_service.ghost",
    "done": "ces_billing.ces_billing_service.done",
    "get_billing_info": "ces_billing.ces_billing_service.get_billing_info",
}

_utils_map = {
    "get_conversation_end_status": "ces_billing.SimulationEngine.utils.get_conversation_end_status",
    "get_default_start_flows": "ces_billing.SimulationEngine.utils.get_default_start_flows",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())