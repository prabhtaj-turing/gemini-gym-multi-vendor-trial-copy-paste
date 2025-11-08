from common_utils.tool_spec_decorator import tool_spec
from typing import List, Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.models import GetDevicesParams
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home.SimulationEngine.utils import process_schedules_and_get_structures


@tool_spec(
    spec={
        'name': 'get_all_devices',
        'description': 'Retrieves all smart home devices set up by the user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'trait_hints': {
                    'type': 'array',
                    'description': """ Optional list of traits to filter for. If this is empty, all traits will
                    be allowed (no filter will be enforced). """,
                    'items': {
                        'type': 'string'
                    }
                },
                'type_hints': {
                    'type': 'array',
                    'description': """ Optional list of device_types to filter for. If this is empty, all
                    device_types will be allowed (no filter will be enforced). """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': []
        }
    }
)
def get_all_devices(
    trait_hints: Optional[List[str]] = None,
    type_hints: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Retrieves all smart home devices set up by the user.

    Args:
        trait_hints (Optional[List[str]]): Optional list of traits to filter for. If this is empty, all traits will
            be allowed (no filter will be enforced).
        type_hints (Optional[List[str]]): Optional list of device_types to filter for. If this is empty, all
            device_types will be allowed (no filter will be enforced).

    Returns:
        List[Dict[str, Any]]: A list of smart home devices, where each device is a dictionary with the
        following structure:
        - id (str): Unique identifier for the device.
        - names (List[str]): A list of names for the device.
        - types (List[str]): A list of types for the device (e.g., 'LIGHT', 'THERMOSTAT').
        - traits (List[str]): A list of traits the device supports (e.g., 'OnOff', 'Brightness').
        - room_name (str): The name of the room the device is in.
        - structure (str): The name of the structure (e.g., home) the device is in.
        - toggles_modes (List[Dict[str, Any]]): A list of toggles and modes for the device.
            - id (str): The ID of the toggle or mode.
            - names (List[str]): A list of names for the toggle or mode.
            - settings (List[Dict[str, Any]]): A list of settings for the toggle or mode.
                - id (str): The ID of the setting.
                - names (List[str]): A list of names for the setting.
        - device_state (List[Dict[str, Any]]): The current state of the device.
            - name (str): The name of the state (e.g., 'on', 'brightness').
            - value (Any): The value of the state.

    Raises:
        InvalidInputError: If the input parameters are invalid.
    """
    try:
        params = GetDevicesParams(
            trait_hints=trait_hints,
            type_hints=type_hints,
        )
    except ValidationError as e:
        raise InvalidInputError(f"Invalid input: {e}") from e

    structures = process_schedules_and_get_structures()
    all_devices = []
    for structure in structures.values():
        for room in structure.get("rooms", {}).values():
            for device_list in room.get("devices", {}).values():
                all_devices.extend(device_list)

    if not params.trait_hints and not params.type_hints:
        return all_devices

    filtered_devices = []
    for device in all_devices:
        if params.trait_hints and not any(
            trait.value in device["traits"] for trait in params.trait_hints
        ):
            continue
        if params.type_hints and not any(
            device_type.value in device["types"] for device_type in params.type_hints
        ):
            continue
        filtered_devices.append(device)

    return filtered_devices


