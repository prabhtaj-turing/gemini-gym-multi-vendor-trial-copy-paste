"""
Retail API Simulation package.
This __init__.py uses dynamic imports for its main API functions.
"""

import importlib
from typing import Any, List  # For __getattr__ type hinting if needed, though not strictly necessary here.
import os
import json
import tempfile
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from retail.SimulationEngine import utils  # This would import retail.SimulationEngine.utils
from common_utils.error_handling import get_package_error_mode

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "calculate": "retail.calculate_tool.calculate",
    "cancel_pending_order": "retail.cancel_pending_order_tool.cancel_pending_order",
    "modify_pending_order_address": "retail.modify_pending_order_address_tool.modify_pending_order_address",
    "modify_pending_order_items": "retail.modify_pending_order_items_tool.modify_pending_order_items",
    "modify_pending_order_payment": "retail.modify_pending_order_payment_tool.modify_pending_order_payment",
    "exchange_delivered_order_items": "retail.exchange_delivered_order_items_tool.exchange_delivered_order_items",
    "return_delivered_order_items": "retail.return_delivered_order_items_tool.return_delivered_order_items",
    "modify_user_address": "retail.modify_user_address_tool.modify_user_address",
    "find_user_id_by_email": "retail.find_user_id_by_email_tool.find_user_id_by_email",
    "find_user_id_by_name_zip": "retail.find_user_id_by_name_zip_tool.find_user_id_by_name_zip",
    "get_order_details": "retail.get_order_details_tool.get_order_details",
    "get_product_details": "retail.get_product_details_tool.get_product_details",
    "get_user_details": "retail.get_user_details_tool.get_user_details",
    "list_all_product_types": "retail.list_all_product_types_tool.list_all_product_types",
    "think": "retail.think_tool.think",
    "transfer_to_human_agents": "retail.transfer_to_human_agents_tool.transfer_to_human_agents",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())
