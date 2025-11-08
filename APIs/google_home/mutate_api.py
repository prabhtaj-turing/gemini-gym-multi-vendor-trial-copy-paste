from common_utils.tool_spec_decorator import tool_spec
from typing import List, Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home.SimulationEngine.models import (
    MutateTraitCommands,
    MutateTraitResult,
    Action,
    APIName,
    CommandName,
    MutateParams,
    TraitName,
)
from google_home.SimulationEngine.utils import (
    process_schedules_and_get_structures,
    validate_device_ids_exist,
    clone_device,
    stage_add_schedule_on_copy,
    commit_staged_device_state,
    handle_edge_case_operation,
    prevalidate_command_values,
)
from google_home.engine.registry import apply_command

@tool_spec(
    spec={
        'name': 'mutate',
        'description': 'Changes traits of smart home devices and returns status of those changes. For now, only supported one trait and command at a time.',
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
                'traits': {
                    'type': 'array',
                    'description': "Name of the trait to change. Valid traits include: 'OnOff', 'OpenClose', 'StartStop', 'TransportControl', 'Scene', 'InputSelector', 'AppSelector', 'Brightness', 'ColorSetting', 'Dock', 'FanSpeed', 'TemperatureSetting', 'Toggles', 'Locator', 'Broadcast', 'LightEffects', 'Volume', 'Modes', 'LockUnlock', 'CameraStream', 'HumiditySetting', 'ArmDisarm', 'ViewSchedules', 'CancelSchedules'.",
                    'items': {
                        'type': 'string'
                    }
                },
                'commands': {
                    'type': 'array',
                    'description': "Name of the command. Valid values for command_names depend on trait_name. Valid values are: 'on', 'off', 'toggle_on_off', 'open', 'close', 'open_percent', 'close_percent', 'open_percent_absolute', 'close_percent_absolute', 'open_ambiguous_amount', 'close_ambiguous_amount', 'start', 'stop', 'pause', 'unpause', 'activate_scene', 'deactivate_scene', 'next_input', 'previous_input', 'set_input', 'open_app', 'set_brightness', 'brighter_ambiguous', 'dimmer_ambiguous', 'brighter_percentage', 'dimmer_percentage', 'change_color', 'dock', 'fan_up_ambiguous', 'fan_down_ambiguous', 'set_fan_speed', 'set_fan_speed_percentage', 'fan_up_percentage', 'fan_down_percentage', 'cooler_ambiguous', 'warmer_ambiguous', 'set_temperature', 'set_temperature_celsius', 'set_temperature_fahrenheit', 'set_temperature_mode', 'set_mode_and_temperature', 'set_mode_and_temperature_fahrenheit', 'set_mode_and_temperature_celsius', 'change_relative_temperature', 'toggle_setting', 'find_device', 'silence_ringing', 'broadcast', 'set_light_effect', 'set_light_effect_with_duration', 'volume_up', 'volume_down', 'volume_up_percentage', 'volume_down_percentage', 'volume_up_ambiguous', 'volume_down_ambiguous', 'set_volume_level', 'set_volume_percentage', 'mute', 'unmute', 'set_mode', 'show_device_info', 'lock', 'unlock', 'camera_stream', 'humidity_setting', 'arm_disarm', 'view_schedules', 'cancel_schedules'.",
                    'items': {
                        'type': 'string'
                    }
                },
                'values': {
                    'type': 'array',
                    'description': 'New value of the command_name. Valid values for command_values depend on command_name.',
                    'items': {
                        'type': 'string'
                    }
                },
                'time_of_day': {
                    'type': 'string',
                    'description': 'time in the format of "HH:MM:SS"'
                },
                'date': {
                    'type': 'string',
                    'description': 'date in the format of "YYYY-MM-DD"'
                },
                'am_pm_or_unknown': {
                    'type': 'string',
                    'description': 'AM or PM or UNKNOWN'
                },
                'duration': {
                    'type': 'string',
                    'description': 'duration in the format of 5s, 20m, 1h'
                }
            },
            'required': [
                'devices',
                'traits',
                'commands',
                'values'
            ]
        }
    }
)
def mutate(
    devices: List[str],
    traits: List[str],
    commands: List[str],
    values: List[str],
    time_of_day: Optional[str] = None,
    date: Optional[str] = None,
    am_pm_or_unknown: Optional[str] = None,
    duration: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Changes traits of smart home devices and returns status of those changes. For now, only supported one trait and command at a time.

    Args:
        devices (List[str]): Unique identifiers of smart home devices.
        traits (List[str]): Name of the trait to change. Valid traits include: 'OnOff', 'OpenClose', 'StartStop', 'TransportControl', 'Scene', 'InputSelector', 'AppSelector', 'Brightness', 'ColorSetting', 'Dock', 'FanSpeed', 'TemperatureSetting', 'Toggles', 'Locator', 'Broadcast', 'LightEffects', 'Volume', 'Modes', 'LockUnlock', 'CameraStream', 'HumiditySetting', 'ArmDisarm', 'ViewSchedules', 'CancelSchedules'.
        commands (List[str]): Name of the command. Valid values for command_names depend on trait_name. Valid values are: 'on', 'off', 'toggle_on_off', 'open', 'close', 'open_percent', 'close_percent', 'open_percent_absolute', 'close_percent_absolute', 'open_ambiguous_amount', 'close_ambiguous_amount', 'start', 'stop', 'pause', 'unpause', 'activate_scene', 'deactivate_scene', 'next_input', 'previous_input', 'set_input', 'open_app', 'set_brightness', 'brighter_ambiguous', 'dimmer_ambiguous', 'brighter_percentage', 'dimmer_percentage', 'change_color', 'dock', 'fan_up_ambiguous', 'fan_down_ambiguous', 'set_fan_speed', 'set_fan_speed_percentage', 'fan_up_percentage', 'fan_down_percentage', 'cooler_ambiguous', 'warmer_ambiguous', 'set_temperature', 'set_temperature_celsius', 'set_temperature_fahrenheit', 'set_temperature_mode', 'set_mode_and_temperature', 'set_mode_and_temperature_fahrenheit', 'set_mode_and_temperature_celsius', 'change_relative_temperature', 'toggle_setting', 'find_device', 'silence_ringing', 'broadcast', 'set_light_effect', 'set_light_effect_with_duration', 'volume_up', 'volume_down', 'volume_up_percentage', 'volume_down_percentage', 'volume_up_ambiguous', 'volume_down_ambiguous', 'set_volume_level', 'set_volume_percentage', 'mute', 'unmute', 'set_mode', 'show_device_info', 'lock', 'unlock', 'camera_stream', 'humidity_setting', 'arm_disarm', 'view_schedules', 'cancel_schedules'.
        values (List[str]): New value of the command_name. Valid values for command_values depend on command_name.
        time_of_day (Optional[str]): time in the format of "HH:MM:SS"
        date (Optional[str]): date in the format of "YYYY-MM-DD"
        am_pm_or_unknown (Optional[str]): AM or PM or UNKNOWN
        duration (Optional[str]): duration in the format of 5s, 20m, 1h

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
    """
    try:
        if len(traits) != 1 or len(commands) != 1:
            raise InvalidInputError(
                f"Invalid input: only supported one trait and command at a time. Got {len(traits)} traits and {len(commands)} commands."
            )
        mutated_commands = MutateTraitCommands(
            device_ids=devices,
            commands=[{
                "trait": traits[0],
                "command_names": commands,
                "command_values": values,
            }],
        )

        mutate_params = MutateParams(
            devices=devices,
            traits=traits,
            commands=commands,
            values=values if values is not None else [],
            time_of_day=time_of_day,
            date=date,
            am_pm_or_unknown=am_pm_or_unknown,
            duration=duration,
        )
    except (ValidationError, InvalidInputError) as e:
        if isinstance(e, InvalidInputError):
            raise e
        raise InvalidInputError(f"Invalid input: {e}") from e

    process_schedules_and_get_structures()

    # Engine performs all validations; no prevalidation here

    results = handle_edge_case_operation(mutated_commands.commands[0].command_names[0].value, devices)
    if results:
        return results

    # Validate all device IDs up-front
    id_to_device = validate_device_ids_exist(devices)
    trait = TraitName(traits[0])
    unsupported = [d for d in devices if trait.value not in id_to_device[d].get("traits", [])]
    if unsupported:
        raise InvalidInputError(
            f"Devices do not support trait '{trait.value}' for command '{commands[0]}': {', '.join(unsupported)}"
        )

    results = []
    is_schedule = time_of_day or date or duration
    # Stage all device updates first
    staged_by_id: Dict[str, Dict[str, Any]] = {}
    for device_id in devices:
        device = id_to_device[device_id]
        staged = clone_device(device)
        for command in mutated_commands.commands:
            cmd_name = CommandName(command.command_names[0])
            cmd_values = command.command_values
            try:
                if is_schedule:
                    staged = stage_add_schedule_on_copy(
                        staged, cmd_name, cmd_values or [], time_of_day, date, am_pm_or_unknown, None, duration
                    )
                else:
                    apply_command(staged, cmd_name, cmd_values or [])
            except ValidationError as e:
                emsg = str(e)
                if cmd_name == CommandName.SET_BRIGHTNESS:
                    if "float_parsing" in emsg or "valid number" in emsg:
                        raise InvalidInputError("Invalid input: value must be a valid number") from e
                    if "less than or equal to 1" in emsg or "greater than or equal to 0" in emsg:
                        raise InvalidInputError("Invalid input: Value for set_brightness must be between 0.0 and 1.0") from e
                raise InvalidInputError(f"Invalid input: {e}") from e
            except (ValueError, NotImplementedError) as e:
                # Normalize ValueError into InvalidInputError for mutate API
                raise InvalidInputError(f"Invalid input: {e}") from e
        staged_by_id[device_id] = staged

    # Commit staged and build results
    for device_id in devices:
        device = id_to_device[device_id]
        staged = staged_by_id[device_id]
        commit_staged_device_state(device, staged)

        text_to_speech = (
            f"Successfully scheduled mutation for {device_id}" if is_schedule else f"Successfully mutated {device_id}"
        )

        results.append(
            MutateTraitResult(
                commands=mutated_commands,
                result="SUCCESS",
                device_execution_results={
                    "text_to_speech": text_to_speech,
                    "results": [
                        {"device_id": device_id, "result": "SUCCESS"}
                    ],
                },
            ).model_dump(mode="json")
        )

    action = Action(
        action_type=APIName.MUTATE,
        inputs={
            "devices": devices,
            "traits": traits,
            "commands": commands,
            "values": values,
            "time_of_day": time_of_day,
            "date": date,
            "am_pm_or_unknown": am_pm_or_unknown,
            "duration": duration,
        },
        outputs={"results": results},
    )
    DB["actions"].append(action.model_dump(mode="json"))

    return results
