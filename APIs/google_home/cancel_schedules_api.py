from common_utils.tool_spec_decorator import tool_spec
from typing import List, Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.custom_errors import InvalidInputError, DeviceNotFoundError, NoSchedulesFoundError
from google_home.SimulationEngine.models import ScheduledActionResult, CancelSchedulesParams
from google_home.SimulationEngine.utils import process_schedules_and_get_structures, get_all_devices_flat


@tool_spec(
    spec={
        'name': 'cancel_schedules',
        'description': 'Cancel scheduled actions of smart home devices and returns status of those changes.',
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
def cancel_schedules(devices: Optional[List[str]] = None) -> Dict[str, Any]:
    """Cancel scheduled actions of smart home devices and returns status of those changes.

    Args:
        devices (Optional[List[str]]): Unique identifiers of smart home devices.

    Returns:
        Dict[str, Any]: A dictionary containing the result of the scheduled action cancellation.
            - tts (str): Text to be spoken to the user.
            - operation_type (str): The type of operation (e.g., 'CANCEL_SCHEDULES').
            - success (bool): Whether the operation was successful.

    Raises:
        InvalidInputError: If the input parameters are invalid.
        DeviceNotFoundError: If any of the requested devices are not found.
    """
    try:
        CancelSchedulesParams(devices=devices)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid input: {e}") from e

    structures = process_schedules_and_get_structures()
    all_devices = get_all_devices_flat(structures)  # type: ignore

    if devices:
        for device_id in devices:
            if not any(d["id"] == device_id for d in all_devices):
                raise DeviceNotFoundError(f"Device with ID '{device_id}' not found.")

    cancelled_schedules_details = []
    cancelled_count = 0

    apply_to_all_devices = devices is None

    for device in all_devices:
        if apply_to_all_devices or (devices and device["id"] in devices):
            for state in device.get("device_state", []):
                if state.get("name") == "schedules":
                    existing_schedules = state.get("value") or []
                    if isinstance(existing_schedules, list) and existing_schedules:
                        cancelled_schedules_details.append({
                            "device_id": device.get("id"),
                            "schedules": list(existing_schedules),
                        })
                        cancelled_count += len(existing_schedules)
                    state["value"] = []

    if cancelled_count == 0:
        raise NoSchedulesFoundError("No schedules found to cancel.")
    else:
        plural = "schedules" if cancelled_count != 1 else "schedule"
        # Build multi-line human-readable details string per device
        detail_lines = []
        for entry in cancelled_schedules_details:
            device_id = entry.get("device_id")
            schedule_items = []
            for s in entry.get("schedules", []):
                action = s.get("action")
                start_time = s.get("start_time")
                schedule_items.append(f"{action} @ {start_time}" if start_time else f"{action}")
            if device_id is not None:
                detail_lines.append(f"- {device_id}: " + ", ".join(schedule_items))
        details_text = "\n".join(detail_lines)
        message = f"Successfully canceled {cancelled_count} {plural}.\nDetails:\n{details_text}"

    result = ScheduledActionResult(
        tts=message,
        operation_type="CANCEL_SCHEDULES",
        success=True,
    ).model_dump(mode="json")
    return result
