from common_utils.tool_spec_decorator import tool_spec
from typing import List, Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.custom_errors import InvalidInputError, DeviceNotFoundError
from google_home.SimulationEngine.models import ScheduledActionResult, ViewSchedulesParams
from google_home.SimulationEngine.utils import process_schedules_and_get_structures


@tool_spec(
    spec={
        'name': 'view_schedules',
        'description': 'View scheduled actions of smart home devices and returns status of those changes.',
        'parameters': {
            'type': 'object',
            'properties': {
                'devices': {
                    'type': 'array',
                    'description': 'Unique identifiers of smart home devices.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': []
        }
    }
)
def view_schedules(devices: Optional[List[str]] = None) -> Dict[str, Any]:
    """View scheduled actions of smart home devices and returns status of those changes.

    Args:
        devices (Optional[List[str]]): Unique identifiers of smart home devices.

    Returns:
        Dict[str, Any]: A dictionary containing the result of the scheduled action viewing.
            - tts (str): Text to be spoken to the user.
            - operation_type (str): The type of operation (e.g., 'VIEW_SCHEDULES').
            - success (bool): Whether the operation was successful.

    Raises:
        InvalidInputError: If the input parameters are invalid.
        DeviceNotFoundError: If any of the requested devices are not found.
    """
    try:
        ViewSchedulesParams(devices=devices)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid input: {e}") from e
    
    structures = process_schedules_and_get_structures()
    all_devices = []
    for structure in structures.values():
        for room in structure.get("rooms", {}).values():
            for device_list in room.get("devices", {}).values():
                all_devices.extend(device_list) # type: ignore

    if devices:
        for device_id in devices:
            if not any(d["id"] == device_id for d in all_devices):
                raise DeviceNotFoundError(f"Device with ID '{device_id}' not found.")

    schedules = []
    for device in all_devices:
        if not devices or device["id"] in devices:
            for state in device["device_state"]:
                if state["name"] == "schedules":
                    schedules.extend(state["value"])

    return ScheduledActionResult(
        tts=f"Found {len(schedules)} schedules.",
        operation_type="VIEW_SCHEDULES",
        success=True,
    ).model_dump(mode="json")
