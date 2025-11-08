from common_utils.tool_spec_decorator import tool_spec
import json
from typing import Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home.SimulationEngine.utils import process_schedules_and_get_structures
from google_home.SimulationEngine.models import SeeDevicesParams


@tool_spec(
    spec={
        'name': 'see_devices',
        'description': 'Retrieves smart home devices set up by the user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'state': {
                    'type': 'boolean',
                    'description': 'Whether to include the dynamic state of the devices.'
                }
            },
            'required': []
        }
    }
)
def see_devices(state: Optional[bool] = None) -> Dict[str, Any]:
    """Retrieves smart home devices set up by the user.

    Args:
        state (Optional[bool]): Whether to include the dynamic state of the devices.

    Returns:
        Dict[str, Any]: A dictionary containing the devices' information in a Markdown table format.
            - devices_info (str): A Markdown table of the devices' information.

    Raises:
        InvalidInputError: If the input parameters are invalid.
    """
    try:
        SeeDevicesParams(state=state)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid input: {e}") from e

    structures = process_schedules_and_get_structures()
    all_devices = []
    for structure in structures.values():
        for room in structure.get("rooms", {}).values():
            for device_list in room.get("devices", {}).values():
                all_devices.extend(device_list)

    if not all_devices:
        return {"devices_info": "No devices found."}

    headers = ["ID", "Name", "Type", "Room"]
    if state:
        headers.append("State")

    table = "| " + " | ".join(headers) + "|\n"
    table += "| " + " | ".join(["---"] * len(headers)) + "|\n"

    for device in all_devices:
        row = [
            device["id"],
            ", ".join(device["names"]),
            ", ".join(device["types"]),
            device["room_name"],
        ]
        if state:
            row.append(json.dumps(device["device_state"]))
        table += "| " + " | ".join(row) + "|\n"

    return {"devices_info": table}
