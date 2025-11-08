from typing import Dict, Any, List, Optional
import copy
from datetime import datetime, timezone, time, timedelta
import re
from pydantic import StrictBool, ValidationError
from google_home.SimulationEngine.custom_errors import (
    InvalidInputError,
    DeviceNotFoundError,
)
from google_home.SimulationEngine.models import (
    CommandName,
    StateName,
    COMMAND_STATE_MAP,
    STATE_VALUE_TYPE_MAP,
    COMMAND_RANGE_RULES,
    FAN_SPEED_STRING_TO_INT_MAP,
    COMMANDS_REQUIRING_VALUES,
    COMMANDS_NOT_REQUIRING_VALUES,
    COMMAND_VALUE_MAP,
    STATELESS_COMMANDS,
    MutateTraitResult,
    Structure,
    Room,
    DeviceInfo,
    DeviceType,
)
from google_home.SimulationEngine.db import DB
from google_home.engine.registry import apply_command


def string_to_bool(s: str) -> bool:
    s_lower = s.lower()
    if s_lower == 'true':
        return True
    if s_lower == 'false':
        return False
    raise ValueError("must be a valid bool")

def parse_duration_to_timedelta(duration_str: Optional[str]) -> timedelta:
    if not duration_str:
        return timedelta(0)
    parts = re.match(r'(\d+)([smh])', duration_str)
    if not parts:
        raise ValueError(f"Invalid duration format: {duration_str}")
    value, unit = int(parts.group(1)), parts.group(2)
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    return timedelta(0)

def calculate_start_time(
    time_of_day: Optional[str], 
    date: Optional[str], 
    am_pm_or_unknown: Optional[str], 
    delay: Optional[str]
) -> datetime:
    now = datetime.now(timezone.utc)
    
    has_time_info = date or time_of_day

    if has_time_info:
        target_date = datetime.fromisoformat(date).date() if date else now.date()
        
        if time_of_day:
            hour, minute, second = map(int, time_of_day.split(':'))
            
            if am_pm_or_unknown:
                am_pm = am_pm_or_unknown.upper()
                if am_pm == 'PM' and 1 <= hour <= 11:
                    hour += 12
                elif am_pm == 'AM' and hour == 12: # 12 AM is 00:00
                    hour = 0
                elif am_pm == 'UNKNOWN': # use am for unknown
                    if hour == 12: # 12 AM is 00:00
                        hour = 0
        else:
            hour, minute, second = 0, 0, 0

        target_time = time(hour, minute, second)
        schedule_time = datetime.combine(target_date, target_time)
        schedule_time = schedule_time.replace(tzinfo=timezone.utc)

        if not date and schedule_time < now:
            schedule_time += timedelta(days=1)
    else:
        schedule_time = now

    if delay:
        delay_td = parse_duration_to_timedelta(delay)
        schedule_time += delay_td
            
    return schedule_time

def add_schedule_to_device(
    device: Dict[str, Any], 
    command: CommandName, 
    values: List[str], 
    time_of_day: Optional[str], 
    date: Optional[str], 
    am_pm_or_unknown: Optional[str], 
    delay: Optional[str], 
    duration: Optional[str]
):
    start_time = calculate_start_time(time_of_day, date, am_pm_or_unknown, delay)
    
    new_schedule = {
        "action": command.value,
        "values": values,
        "start_time": start_time.isoformat(),
    }
    if duration:
        new_schedule["duration"] = duration

    # Store schedules in device_state['schedules'] so view/cancel endpoints see them
    schedules_state = None
    for state in device.get("device_state", []):
        if state.get("name") == "schedules":
            schedules_state = state
            break

    if schedules_state is None:
        device.setdefault("device_state", []).append({"name": "schedules", "value": []})
        schedules_state = device["device_state"][-1]

    schedules_state["value"].append(new_schedule)


def process_schedules():
    """
    Processes all schedules in the database and updates the device states accordingly.
    """
    now = datetime.now(timezone.utc)
    for structure in DB.get("structures", {}).values():
        for room in structure.get("rooms", {}).values():
            for device_list in room.get("devices", {}).values():
                for device in device_list:
                    # Locate schedules in device_state
                    schedules_state = None
                    for state in device.get("device_state", []):
                        if state.get("name") == "schedules":
                            schedules_state = state
                            break

                    if not schedules_state:
                        continue

                    schedules_to_remove = []
                    schedules_to_add: List[Dict[str, Any]] = []
                    for schedule in schedules_state.get("value", []):
                        # Only process schedules that have a start_time
                        if "start_time" not in schedule:
                            continue
                        schedule_time = datetime.fromisoformat(schedule["start_time"])
                        # If schedule time is naive, treat as static display-only and skip processing
                        if schedule_time.tzinfo is None:
                            continue
                        if schedule_time <= now:
                            command_str = schedule["action"]
                            try:
                                cmd = CommandName(command_str)
                                vals = schedule.get("values") or []
                                # Ignore extraneous values for commands that do not require values
                                if cmd in COMMANDS_NOT_REQUIRING_VALUES:
                                    vals = []
                                apply_command(device, cmd, vals)
                            except Exception as e:
                                # Fail-safe: skip invalid schedule applications
                                pass
                            schedules_to_remove.append(schedule)

                            if "duration" in schedule and schedule["duration"]:
                                duration_td = parse_duration_to_timedelta(schedule["duration"])
                                revert_time = schedule_time + duration_td

                                command = CommandName(command_str)
                                if command == CommandName.ON:
                                    schedules_to_add.append({
                                        "action": CommandName.OFF.value,
                                        "values": [],
                                        "start_time": revert_time.isoformat(),
                                    })
                                elif command == CommandName.OFF:
                                    schedules_to_add.append({
                                        "action": CommandName.ON.value,
                                        "values": [],
                                        "start_time": revert_time.isoformat(),
                                    })
                                elif command == CommandName.TOGGLE_ON_OFF:
                                    schedules_to_add.append({
                                        "action": command.value,
                                        "values": [],
                                        "start_time": revert_time.isoformat(),
                                    })
                                elif command in (CommandName.SET_LIGHT_EFFECT, CommandName.SET_LIGHT_EFFECT_WITH_DURATION):
                                    schedules_to_add.append({
                                        "action": CommandName.SET_MODE.value,
                                        "values": ["lightEffect", ""],
                                        "start_time": revert_time.isoformat(),
                                    })

                    if schedules_to_remove or schedules_to_add:
                        current = schedules_state.get("value", [])
                        updated = [s for s in current if s not in schedules_to_remove]
                        updated.extend(schedules_to_add)
                        schedules_state["value"] = updated


# ============================ VALIDATION HELPERS ============================

def _flatten_all_devices() -> List[Dict[str, Any]]:
    structures = DB.get("structures", {})
    devices: List[Dict[str, Any]] = []
    for structure in structures.values():
        for room in structure.get("rooms", {}).values():
            for device_list in room.get("devices", {}).values():
                devices.extend(device_list)
    return devices

def validate_device_ids_exist(device_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Validate that all device IDs exist; returns id->device mapping or raises."""
    all_devices = _flatten_all_devices()
    id_to_device = {d.get("id"): d for d in all_devices}
    missing = [d for d in device_ids if d not in id_to_device]
    if missing:
        raise DeviceNotFoundError(f"Devices not found: {', '.join(missing)}")
    return id_to_device

def resolve_trait_for_operation(op: str) -> Optional[str]:
    try:
        cmd = CommandName(op)
    except Exception:
        return None
    for trait_name, command_names in COMMAND_STATE_MAP.items():
        # COMMAND_STATE_MAP keys are CommandName to StateName list; not helpful to get Trait.
        # Use TRAIT_COMMAND_MAP from models by importing lazily to avoid cycles.
        from google_home.SimulationEngine.models import TRAIT_COMMAND_MAP as _TCM  # local import
        for t, cmds in _TCM.items():
            if cmd in cmds:
                return t.value if hasattr(t, 'value') else str(t)
    return None

def validate_devices_support_trait(device_ids: List[str], trait_value: str) -> None:
    id_to_device = validate_device_ids_exist(device_ids)
    unsupported = [d for d in device_ids if trait_value not in id_to_device[d].get("traits", [])]
    if unsupported:
        raise InvalidInputError(
            f"Devices do not support trait '{trait_value}': {', '.join(unsupported)}"
        )


# ============================ STAGING HELPERS ===============================

def clone_device(device: Dict[str, Any]) -> Dict[str, Any]:
    """Deep clone a device dict to stage changes safely."""
    return copy.deepcopy(device)

def stage_update_on_copy(device_copy: Dict[str, Any], command: CommandName, values: Optional[List[str]]) -> Dict[str, Any]:
    """Apply update_device_state to the copy for staging; raises if invalid."""
    update_device_state(device_copy, command, values)
    return device_copy

def stage_add_schedule_on_copy(
    device_copy: Dict[str, Any], 
    command: CommandName, 
    values: Optional[List[str]], 
    time_of_day: Optional[str], 
    date: Optional[str], 
    am_pm_or_unknown: Optional[str], 
    delay: Optional[str], 
    duration: Optional[str]
) -> Dict[str, Any]:
    add_schedule_to_device(device_copy, command, values, time_of_day, date, am_pm_or_unknown, delay, duration)
    return device_copy

def commit_staged_device_state(target: Dict[str, Any], staged: Dict[str, Any]) -> None:
    """Commit only the device_state from staged to target atomically."""
    target["device_state"] = staged.get("device_state", [])


def prevalidate_command_values(op: str, values: Optional[List[str]]) -> None:
    """Deprecated: validation now centralized in engine. Left for backward-compat tests that import it."""
    return
    # Friendly validation for light effects (per OpenAPI: use set_mode for other values)
    if cmd in (CommandName.SET_LIGHT_EFFECT, CommandName.SET_LIGHT_EFFECT_WITH_DURATION):
        allowed_effects = ["sleep", "wake", "colorLoop", "pulse"]
        if not values or len(values) == 0:
            raise ValueError(f"Command '{op}' requires values.")
        effect = values[0]
        if effect not in allowed_effects:
            allowed_str = ", ".join(allowed_effects)
            raise InvalidInputError(
                f"Invalid light effect. Must be one of: {allowed_str}. Use 'set_mode' for other effects."
            )
        if cmd == CommandName.SET_LIGHT_EFFECT_WITH_DURATION:
            if len(values) < 2:
                raise InvalidInputError(
                    "Invalid input: set_light_effect_with_duration requires two values: effect and duration_seconds."
                )
            try:
                duration = int(values[1])
            except Exception:
                raise InvalidInputError("Invalid input: duration must be a positive integer (seconds).")
            if duration < 1:
                raise InvalidInputError("Invalid input: duration must be a positive integer (seconds).")

def process_schedules_and_get_structures():
    """
    Processes all schedules in the database, updates the device states accordingly,
    and returns the updated structures.
    """
    process_schedules()
    return DB.get("structures", {})


def get_all_devices_flat(structures: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns a flat list of all device dictionaries from the provided structures.

    Args:
        structures (Dict[str, Any]): The structures dictionary from the DB.

    Returns:
        List[Dict[str, Any]]: A flat list containing all devices across all rooms and structures.
    """
    devices: List[Dict[str, Any]] = []
    for structure in structures.values():
        for room in structure.get("rooms", {}).values():
            for device_list in room.get("devices", {}).values():
                devices.extend(device_list)
    return devices


def enrich_device_states(states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Engine-level enrichment for device states. Adds dual-unit temperature values
    for thermostat states and normalizes unit to single-letter C/F where present.
    """
    enriched: List[Dict[str, Any]] = []
    for st in states or []:
        name = st.get("name")
        if name in (StateName.THERMOSTAT_TEMPERATURE_SETPOINT, StateName.THERMOSTAT_TEMPERATURE_AMBIENT):
            value = st.get("value")
            unit = st.get("unit", "F")
            try:
                v = float(value)
            except (TypeError, ValueError):
                enriched.append(st)
                continue
            if str(unit).upper().startswith("F"):
                c = (v - 32.0) * 5.0 / 9.0
                f = v
                unit_out = "F"
            else:
                c = v
                f = (v * 9.0 / 5.0) + 32.0
                unit_out = "C"
            st_out = dict(st)
            st_out["value_metric"] = round(c, 2)
            st_out["value_imperial"] = round(f, 2)
            st_out["unit"] = unit_out
            enriched.append(st_out)
        else:
            enriched.append(st)
    return enriched


def update_device_state(device: Dict[str, Any], command: CommandName | str, values: List[str]):
    # Back-compat wrapper around engine.apply_command to preserve legacy error behavior in tests
    cmd: CommandName
    if isinstance(command, str):
        try:
            cmd = CommandName(command)
        except Exception:
            raise NotImplementedError(f"Command '{command}' is not implemented.")
    else:
        cmd = command
    try:
        vals = values
        if cmd in COMMANDS_NOT_REQUIRING_VALUES:
            vals = []
        apply_command(device, cmd, vals)
    except ValidationError as e:
        # Normalize some historical error messages expected by tests
        emsg = str(e)
        if cmd == CommandName.SET_BRIGHTNESS:
            if "float_parsing" in emsg or "valid number" in emsg:
                bad = values[0] if values else ""
                raise ValueError(f"could not convert string to float: '{bad}'")
            if "less than or equal to 1" in emsg or "greater than or equal to 0" in emsg:
                raise ValueError("Value for set_brightness must be between 0.0 and 1.0")
        raise


def get_structure(name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a structure by its name from the GoogleHomeDB.

    Args:
        name (str): The name of the structure to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The structure as a dictionary if found, otherwise None.
        The dictionary conforms to the `Structure` model. See the model for more details on the fields.
    """
    structure = DB.get("structures", {}).get(name)
    if structure:
        return Structure(**structure).model_dump(mode="json")
    return None

def add_structure(structure_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds a new structure to the GoogleHomeDB.

    Args:
        structure_data (Dict[str, Any]): The dictionary representing the new structure.
        It must conform to the `Structure` model. See the model for more details on the fields.

    Returns:
        Dict[str, Any]: The added structure as a dictionary, conforming to the `Structure` model.

    Raises:
        InvalidInputError: If the structure_data is invalid or a structure with the same name already exists.
    """
    try:
        structure = Structure(**structure_data)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid structure data: {e}") from e

    if structure.name in DB.get("structures", {}):
        raise InvalidInputError(f"Structure '{structure.name}' already exists.")

    DB.setdefault("structures", {})[structure.name] = structure.model_dump(mode="json")
    return structure.model_dump(mode="json")

def update_structure(name: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing structure in the GoogleHomeDB.

    Args:
        name (str): The name of the structure to update.
        update_data (Dict[str, Any]): The dictionary with fields to update. The fields
        should be valid fields of the `Structure` model.

    Returns:
        Dict[str, Any]: The updated structure as a dictionary, conforming to the `Structure` model.

    Raises:
        DeviceNotFoundError: If the structure is not found.
        InvalidInputError: If the update_data is invalid.
    """
    structures = DB.get("structures", {})
    if name not in structures:
        raise DeviceNotFoundError(f"Structure '{name}' not found.")

    try:
        updated_structure_data = structures[name].copy()
        updated_structure_data.update(update_data)
        updated_structure = Structure(**updated_structure_data)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid update data: {e}") from e

    del structures[name]
    structures[updated_structure.name] = updated_structure.model_dump(mode="json")
    return updated_structure.model_dump(mode="json")

def delete_structure(name: str) -> None:
    """
    Deletes a structure from the GoogleHomeDB.

    Args:
        name (str): The name of the structure to delete.

    Raises:
        DeviceNotFoundError: If the structure is not found.
    """
    structures = DB.get("structures", {})
    if name not in structures:
        raise DeviceNotFoundError(f"Structure '{name}' not found.")
    del structures[name]

def get_room(structure_name: str, room_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a room from a structure in the GoogleHomeDB.

    Args:
        structure_name (str): The name of the structure containing the room.
        room_name (str): The name of the room to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The room as a dictionary if found, otherwise None.
        The dictionary conforms to the `Room` model. See the model for more details on the fields.
    """
    structure = get_structure(structure_name)
    if not structure:
        return None
    room = structure.get("rooms", {}).get(room_name)
    if room:
        return Room(**room).model_dump(mode="json")
    return None

def add_room(structure_name: str, room_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds a new room to a structure in the GoogleHomeDB.

    Args:
        structure_name (str): The name of the structure to add the room to.
        room_data (Dict[str, Any]): The dictionary representing the new room.
        It must conform to the `Room` model. See the model for more details on the fields.

    Returns:
        Dict[str, Any]: The added room as a dictionary, conforming to the `Room` model.

    Raises:
        DeviceNotFoundError: If the structure is not found.
        InvalidInputError: If the room_data is invalid or a room with the same name already exists.
    """
    structures = DB.get("structures", {})
    if structure_name not in structures:
        raise DeviceNotFoundError(f"Structure '{structure_name}' not found.")

    try:
        room = Room(**room_data)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid room data: {e}") from e

    if room.name in structures[structure_name].get("rooms", {}):
        raise InvalidInputError(f"Room '{room.name}' already exists in structure '{structure_name}'.")

    structures[structure_name].setdefault("rooms", {})[room.name] = room.model_dump(mode="json")
    return room.model_dump(mode="json")

def update_room(structure_name: str, room_name: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing room in a structure.

    Args:
        structure_name (str): The name of the structure containing the room.
        room_name (str): The name of the room to update.
        update_data (Dict[str, Any]): The dictionary with fields to update. The fields
        should be valid fields of the `Room` model.

    Returns:
        Dict[str, Any]: The updated room as a dictionary, conforming to the `Room` model.

    Raises:
        DeviceNotFoundError: If the structure or room is not found.
        InvalidInputError: If the update_data is invalid.
    """
    structures = DB.get("structures", {})
    if structure_name not in structures or room_name not in structures[structure_name].get("rooms", {}):
        raise DeviceNotFoundError(f"Room '{room_name}' in structure '{structure_name}' not found.")

    try:
        updated_room_data = structures[structure_name]["rooms"][room_name].copy()
        updated_room_data.update(update_data)
        updated_room = Room(**updated_room_data)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid update data: {e}") from e

    del structures[structure_name]["rooms"][room_name]
    structures[structure_name]["rooms"][updated_room.name] = updated_room.model_dump(mode="json")
    return updated_room.model_dump(mode="json")

def delete_room(structure_name: str, room_name: str) -> None:
    """
    Deletes a room from a structure.

    Args:
        structure_name (str): The name of the structure containing the room.
        room_name (str): The name of the room to delete.

    Raises:
        DeviceNotFoundError: If the structure or room is not found.
    """
    structures = DB.get("structures", {})
    if structure_name not in structures or room_name not in structures[structure_name].get("rooms", {}):
        raise DeviceNotFoundError(f"Room '{room_name}' in structure '{structure_name}' not found.")
    del structures[structure_name]["rooms"][room_name]

def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a device by its ID from the GoogleHomeDB.

    Args:
        device_id (str): The ID of the device to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The device as a dictionary if found, otherwise None.
        The dictionary conforms to the `DeviceInfo` model. See the model for more details on the fields.
    """
    for structure in DB.get("structures", {}).values():
        for room in structure.get("rooms", {}).values():
            for device_list in room.get("devices", {}).values():
                for device in device_list:
                    if device.get("id") == device_id:
                        return DeviceInfo(**device).model_dump(mode="json")
    return None

def add_device(structure_name: str, room_name: str, device_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds a new device to a room in the GoogleHomeDB.

    Args:
        structure_name (str): The name of the structure.
        room_name (str): The name of the room.
        device_data (Dict[str, Any]): The dictionary representing the new device.
        It must conform to the `DeviceInfo` model. See the model for more details on the fields.

    Returns:
        Dict[str, Any]: The added device as a dictionary, conforming to the `DeviceInfo` model.

    Raises:
        DeviceNotFoundError: If the structure or room is not found.
        InvalidInputError: If the device_data is invalid or a device with the same ID already exists.
    """
    structures = DB.get("structures", {})
    if structure_name not in structures or room_name not in structures[structure_name].get("rooms", {}):
        raise DeviceNotFoundError(f"Room '{room_name}' in structure '{structure_name}' not found.")

    try:
        device = DeviceInfo(**device_data)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid device data: {e}") from e

    if get_device(device.id):
        raise InvalidInputError(f"Device with ID '{device.id}' already exists.")

    device_type = device.types[0] if device.types else DeviceType.SWITCH
    room = structures[structure_name]["rooms"][room_name]
    room.setdefault("devices", {}).setdefault(device_type, []).append(device.model_dump(mode="json"))
    return device.model_dump(mode="json")

def update_device(device_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing device in the GoogleHomeDB.

    Args:
        device_id (str): The ID of the device to update.
        update_data (Dict[str, Any]): The dictionary with fields to update. The fields
        should be valid fields of the `DeviceInfo` model.

    Returns:
        Dict[str, Any]: The updated device as a dictionary, conforming to the `DeviceInfo` model.

    Raises:
        DeviceNotFoundError: If the device is not found.
        InvalidInputError: If the update_data is invalid.
    """
    for structure in DB.get("structures", {}).values():
        for room in structure.get("rooms", {}).values():
            for device_type, device_list in room.get("devices", {}).items():
                for i, device in enumerate(device_list):
                    if device.get("id") == device_id:
                        try:
                            updated_device_data = device.copy()
                            updated_device_data.update(update_data)
                            updated_device = DeviceInfo(**updated_device_data)
                        except ValidationError as e:
                            raise InvalidInputError(f"Invalid update data: {e}") from e
                        
                        device_list[i] = updated_device.model_dump(mode="json")
                        return updated_device.model_dump(mode="json")
    raise DeviceNotFoundError(f"Device with ID '{device_id}' not found.")

def delete_device(device_id: str) -> None:
    """
    Deletes a device from the GoogleHomeDB.

    Args:
        device_id (str): The ID of the device to delete.

    Raises:
        DeviceNotFoundError: If the device is not found.
    """
    for structure in DB.get("structures", {}).values():
        for room in structure.get("rooms", {}).values():
            for device_type, device_list in room.get("devices", {}).items():
                for i, device in enumerate(device_list):
                    if device.get("id") == device_id:
                        del device_list[i]
                        return
    raise DeviceNotFoundError(f"Device with ID '{device_id}' not found.")

# Utility to handle edge cases for device operations in Google Home Simulation Engine
def handle_edge_case_operation(op: str, devices: list):
    """
    Handles special-case operations that do not mutate device state or require custom handling.

    Args:
        op (str): The operation/command name.
        devices (list): List of device IDs.

    Returns:
        list or None: List of MutateTraitResult dicts if handled, else None.
    """
    from google_home.cancel_schedules_api import cancel_schedules as _cancel_schedules_api

    # Special-case: show_device_info is a display-only op
    if op == CommandName.SHOW_DEVICE_INFO.value:
        results = []
        for device_id in devices:
            results.append(
                MutateTraitResult(
                    result="SUCCESS",
                    device_execution_results={
                        "text_to_speech": f"Showing device info for {device_id}",
                        "results": [{"device_id": device_id, "result": "SUCCESS"}],
                    },
                ).model_dump(mode="json")
            )
        return results

    # Special-case: cancel_schedules should delegate to the API and surface its response
    if op == CommandName.CANCEL_SCHEDULES.value:
        if not devices:
            raise InvalidInputError("At least one device id must be provided for 'cancel_schedules'.")
        resp = _cancel_schedules_api(devices=devices)
        tts_msg = resp.get("tts", "")
        results = []
        for device_id in devices:
            results.append(
                MutateTraitResult(
                    result="SUCCESS",
                    device_execution_results={
                        "text_to_speech": tts_msg,
                        "results": [{"device_id": device_id, "result": "SUCCESS"}],
                    },
                ).model_dump(mode="json")
            )
        return results

    # Special-case: view_schedules does not mutate device state via run(); succeed directly
    if op == CommandName.VIEW_SCHEDULES.value:
        results = []
        for device_id in devices:
            results.append(
                MutateTraitResult(
                    result="SUCCESS",
                    device_execution_results={
                        "text_to_speech": f"{op} processed for {device_id}",
                        "results": [{"device_id": device_id, "result": "SUCCESS"}],
                    },
                ).model_dump(mode="json")
            )
        return results

    # Special-case: no state changes commands should succeed directly
    if op in STATELESS_COMMANDS:
        results = []
        for device_id in devices:
            results.append(
                MutateTraitResult(
                    result="SUCCESS",
                    device_execution_results={
                        "text_to_speech": f"{op} processed for {device_id}",
                        "results": [{"device_id": device_id, "result": "SUCCESS"}],
                    },
                ).model_dump(mode="json")
            )
        return results

    # If not handled, return None so caller can proceed with normal logic
    return None
