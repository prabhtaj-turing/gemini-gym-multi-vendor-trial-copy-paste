from common_utils.tool_spec_decorator import tool_spec
from typing import List, Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.models import (
    RunParams,
    MutateTraitResult,
    MutateTraitCommands,
    TRAIT_COMMAND_MAP,
    CommandName,
    Action,
    APIName,
)
from google_home.SimulationEngine.utils import (
    process_schedules_and_get_structures,
    handle_edge_case_operation,
    validate_device_ids_exist,
    clone_device,
    stage_add_schedule_on_copy,
    commit_staged_device_state,
)
from google_home.engine.registry import apply_command
from google_home.SimulationEngine.utils import prevalidate_command_values


@tool_spec(
    spec={
        'name': 'run',
        'description': 'Runs a general operation on smart home devices and returns the status.',
        'parameters': {
            'type': 'object',
            'properties': {
                'devices': {
                    'type': 'array',
                    'description': 'Unique identifiers of smart home devices.',
                    'items': {
                        'type': 'string'
                    }
                },
                'op': {
                    'type': 'string',
                    'description': 'Name of the operation to run.'
                },
                'values': {
                    'type': 'array',
                    'description': 'Optional list of values for the operation.',
                    'items': {
                        'type': 'string'
                    }
                },
                'time_of_day': {
                    'type': 'string',
                    'description': 'Time to execute the operation, expected in the format of "HH:MM:SS"'
                },
                'date': {
                    'type': 'string',
                    'description': 'Date to execute the operation, expected in the format of "YYYY-MM-DD"'
                },
                'am_pm_or_unknown': {
                    'type': 'string',
                    'description': 'Whether time_of_day is AM or PM or UNKNOWN'
                },
                'delay': {
                    'type': 'string',
                    'description': 'How long to wait before executing the operation. Example format are 5s, 20m, 1h'
                },
                'duration': {
                    'type': 'string',
                    'description': 'How long the operation should last. Example format are 5s, 20m, 1h'
                }
            },
            'required': [
                'devices',
                'op'
            ]
        }
    }
)

def run(
    devices: List[str],
    op: str,
    values: Optional[List[str]] = None,
    time_of_day: Optional[str] = None,
    date: Optional[str] = None,
    am_pm_or_unknown: Optional[str] = None,
    delay: Optional[str] = None,
    duration: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Runs a general operation on smart home devices and returns the status.

    Args:
        devices (List[str]): Unique identifiers of smart home devices.
        op (str): Name of the operation to run.
        values (Optional[List[str]]): Optional list of values for the operation.
        time_of_day (Optional[str]): Time to execute the operation, expected in the format of "HH:MM:SS"
        date (Optional[str]): Date to execute the operation, expected in the format of "YYYY-MM-DD"
        am_pm_or_unknown (Optional[str]): Whether time_of_day is AM or PM or UNKNOWN
        delay (Optional[str]): How long to wait before executing the operation. Example format are 5s, 20m, 1h
        duration (Optional[str]): How long the operation should last. Example format are 5s, 20m, 1h

    Returns:
        List[Dict[str, Any]]: A list of mutation results for each device.
            - commands (Dict[str, Any]): The commands that were executed.
                - device_ids (List[str]): The IDs of the devices that were mutated.
                - commands (List[Dict[str, Any]]): The commands that were executed.
                    - trait (str): The name of the trait that was changed.
                    - command_names (List[str]): The names of the commands that were executed.
                    - command_values (List[str]): The new values of the commands.
            - result (str): The result of the mutation (e.g., 'SUCCESS', 'FAILURE').
            - device_execution_results (Dict[str, Any]): The execution results for each device.
                - text_to_speech (str): Text to be spoken to the user.
                - results (List[Dict[str, Any]]): The execution results for each device.
                    - device_id (str): The ID of the device.
                    - result (str): The result of the execution (e.g., 'SUCCESS', 'FAILURE').

    Raises:
        InvalidInputError: If the input parameters are invalid.
        DeviceNotFoundError: If any of the requested devices are not found.
        NoSchedulesFoundError: If op is 'cancel_schedules' and no schedules exist for the target devices.
    """
    try:
        run_params = RunParams(
            devices=devices,
            op=op,
            values=values,
            time_of_day=time_of_day,
            date=date,
            am_pm_or_unknown=am_pm_or_unknown,
            delay=delay,
            duration=duration,
        )
    except ValidationError as e:
        raise InvalidInputError(f"Invalid input: {e}") from e

    process_schedules_and_get_structures()
    # Engine performs all validations; no prevalidation here
    results = handle_edge_case_operation(op, devices)
    if results:
        return results

    # Resolve trait for op
    trait = None
    command = CommandName(op)
    for trait_name, command_names in TRAIT_COMMAND_MAP.items():
        if command in command_names:
            trait = trait_name
            break

    if not trait:
        raise InvalidInputError(f"Invalid operation: {op}")

    # Atomicity: ensure all devices exist before applying any updates
    id_to_device = validate_device_ids_exist(devices)
    # Validate trait support for all targets before any processing
    if trait:
        unsupported = [d for d in devices if trait.value not in id_to_device[d].get("traits", [])]
        if unsupported:
            raise InvalidInputError(
                f"Devices do not support trait '{trait.value}' for op '{op}': {', '.join(unsupported)}"
            )

    results: List[Dict[str, Any]] = []
    is_schedule = bool(time_of_day or date or delay or duration)

    # Stage all updates on copies first to avoid partial updates
    staged_by_id: Dict[str, Dict[str, Any]] = {}
    for device_id in devices:
        original = id_to_device[device_id]
        staged = clone_device(original)
        try:
            if is_schedule:
                staged = stage_add_schedule_on_copy(
                    staged, command, values or [], time_of_day, date, am_pm_or_unknown, delay, duration
                )
            else:
                apply_command(staged, command, values or [])
        except ValidationError as e:
            emsg = str(e)
            if command == CommandName.SET_BRIGHTNESS:
                if "float_parsing" in emsg or "valid number" in emsg:
                    bad = values[0] if values else ""
                    raise ValueError(f"could not convert string to float: '{bad}'")
                if "less than or equal to 1" in emsg or "greater than or equal to 0" in emsg:
                    raise ValueError("Value for set_brightness must be between 0.0 and 1.0")
            raise InvalidInputError(f"Invalid input: {e}") from e
        except (ValueError, NotImplementedError) as e:
            raise InvalidInputError(f"Invalid input: {e}") from e
        staged_by_id[device_id] = staged

    # Commit staged updates and build results
    for device_id in devices:
        original = id_to_device[device_id]
        staged = staged_by_id[device_id]
        commit_staged_device_state(original, staged)
        tts = (
            f"Successfully scheduled {op} for {device_id}" if is_schedule else f"Successfully ran {op} on {device_id}"
        )
        results.append(
            MutateTraitResult(
                commands=MutateTraitCommands(
                    device_ids=[device_id],
                    commands=[
                        {
                            "trait": trait,
                            "command_names": [op],
                            "command_values": values,
                        }
                    ],
                ),
                result="SUCCESS",
                device_execution_results={
                    "text_to_speech": tts,
                    "results": [{"device_id": device_id, "result": "SUCCESS"}],
                },
            ).model_dump(mode="json")
        )

    action = Action(
        action_type=APIName.RUN,
        inputs={
            "devices": devices,
            "op": op,
            "values": values,
            "time_of_day": time_of_day,
            "date": date,
            "am_pm_or_unknown": am_pm_or_unknown,
            "delay": delay,
            "duration": duration,
        },
        outputs={"results": results},
    )
    DB["actions"].append(action.model_dump(mode="json"))

    return results
