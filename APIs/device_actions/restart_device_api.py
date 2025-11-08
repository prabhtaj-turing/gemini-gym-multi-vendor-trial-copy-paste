from common_utils.tool_spec_decorator import tool_spec
from typing import Dict
from device_actions.SimulationEngine.models import ActionSummary
from device_actions.SimulationEngine.db import DB
from device_actions.SimulationEngine.utils import get_phone_state, update_phone_state
from datetime import datetime, timezone
from device_actions.SimulationEngine.custom_errors import DevicePoweredOffError

@tool_spec(
    spec={
        'name': 'restart_device',
        'description': 'Restarts the device. It can only open the power options menu.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def restart_device() -> Dict[str, str]:
    """
    Restarts the device. It can only open the power options menu.

    Returns:
        Dict[str, str]: A dictionary containing the result of the action.
            - result (str): A message indicating the result of the action.
            - card_id (str): A unique identifier for the action card.

    Raises:
        DevicePoweredOffError: If the device is powered off.
    """
    inputs = {}

    phone_state = get_phone_state()

    if not phone_state.is_on:
        raise DevicePoweredOffError("Device is powered off. This action cannot be performed.")

    result = "Opened power options menu"
    
    summary = ActionSummary(result=result)

    # Restarting closes the browser
    update_phone_state({
        "browser": {"is_open": False, "current_url": None},
        "is_on": True,
        "last_restart_timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return summary.model_dump(mode="json")