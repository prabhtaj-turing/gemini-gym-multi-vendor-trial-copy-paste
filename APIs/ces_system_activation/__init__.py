
from common_utils.error_handling import get_package_error_mode

import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode

from .SimulationEngine.db import DB, load_state, save_state
from .SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    "get_activation_visit_details": "ces_system_activation.ces_system_activation.get_activation_visit_details",
    "find_available_technician_appointment_slots": "ces_system_activation.ces_system_activation.find_available_technician_appointment_slots",
    "reschedule_technician_visit": "ces_system_activation.ces_system_activation.reschedule_technician_visit",
    "schedule_new_technician_visit": "ces_system_activation.ces_system_activation.schedule_new_technician_visit",
    "flag_technician_visit_issue": "ces_system_activation.ces_system_activation.flag_technician_visit_issue",
    "trigger_service_activation": "ces_system_activation.ces_system_activation.trigger_service_activation",
    "get_service_activation_status": "ces_system_activation.ces_system_activation.get_service_activation_status",
    "send_customer_notification": "ces_system_activation.ces_system_activation.send_customer_notification",
    "search_order_details": "ces_system_activation.ces_system_activation.search_order_details",
    "search_activation_guides": "ces_system_activation.ces_system_activation.search_activation_guides",
    "escalate": "ces_system_activation.ces_system_activation.escalate",
    "fail": "ces_system_activation.ces_system_activation.fail",
    "cancel": "ces_system_activation.ces_system_activation.cancel",
}

_utils_map = {
    "get_conversation_end_status": "ces_system_activation.SimulationEngine.utils.get_conversation_end_status",
    "get_infobot_config": "ces_system_activation.SimulationEngine.utils.get_infobot_config",
    "update_infobot_config": "ces_system_activation.SimulationEngine.utils.update_infobot_config",
    "save_infobot_config": "ces_system_activation.SimulationEngine.utils.save_infobot_config",
    "load_infobot_config": "ces_system_activation.SimulationEngine.utils.load_infobot_config",
    "reset_infobot_config": "ces_system_activation.SimulationEngine.utils.reset_infobot_config",
    "show_infobot_config": "ces_system_activation.SimulationEngine.utils.show_infobot_config",
    "set_infobot_mode": "ces_system_activation.SimulationEngine.utils.set_infobot_mode",
}


def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)


def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))


__all__ = list(_function_map.keys())
