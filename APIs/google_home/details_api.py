from common_utils.tool_spec_decorator import tool_spec
import json
from typing import List, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.custom_errors import InvalidInputError, DeviceNotFoundError
from google_home.SimulationEngine.utils import process_schedules_and_get_structures, enrich_device_states
from google_home.SimulationEngine.models import DetailsParams


@tool_spec(
    spec={
        'name': 'details',
        'description': """ retrieves the state of devices in the user's home, such as the current temperature,
        
        the current volume, or the current status of a light. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'devices': {
                    'type': 'array',
                    'description': 'Unique identifiers of smart home devices. Empty list will return state of all devices.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'devices'
            ]
        }
    }
)
def details(devices: List[str]) -> Dict[str, Any]:
    """retrieves the state of devices in the user's home, such as the current temperature,
    the current volume, or the current status of a light.

    Args:
        devices (List[str]): Unique identifiers of smart home devices. Empty list will return state of all devices.

    Returns:
        Dict[str, Any]: A dictionary containing the state of the requested devices.
            - devices_info (str): A string representation of the devices' state.

    Raises:
        InvalidInputError: If the input parameters are invalid.
        DeviceNotFoundError: If any of the requested devices are not found.
    """
    try:
        DetailsParams(devices=devices)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid input: {e}") from e

    structures = process_schedules_and_get_structures()
    devices_info = {}
    all_devices = []
    for structure in structures.values():
        for room in structure.get("rooms", {}).values():
            for device_list in room.get("devices", {}).values():
                all_devices.extend(device_list)

    def _enrich_states(states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return enrich_device_states(states)

    if not devices:
        devices_info = {device["id"]: _enrich_states(device.get("device_state", [])) for device in all_devices}
        return {"devices_info": json.dumps(devices_info)}

    missing_devices = []
    for device_id in devices:
        device_found = False
        for device in all_devices:
            if device["id"] == device_id:
                devices_info[device_id] = _enrich_states(device.get("device_state", []))
                device_found = True
                break
        if not device_found:
            missing_devices.append(device_id)

    if missing_devices:
        raise DeviceNotFoundError(f"Devices with IDs {missing_devices} not found.")

    return {"devices_info": json.dumps(devices_info)}
