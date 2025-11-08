from common_utils.tool_spec_decorator import tool_spec
from typing import List, Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.db import DB
from google_home.SimulationEngine.custom_errors import InvalidInputError, DeviceNotFoundError
from google_home.SimulationEngine.models import (
    MutateTraitCommands,
    MutateTraitResult,
    Action,
    APIName,
    TraitName,
    CommandName,
)
from google_home.SimulationEngine.utils import (
    update_device_state,
    process_schedules_and_get_structures,
    validate_device_ids_exist,
    clone_device,
    stage_update_on_copy,
    commit_staged_device_state,
    prevalidate_command_values,
    handle_edge_case_operation,
)

@tool_spec(
    spec={
        'name': 'mutate_traits',
        'description': 'Changes traits of smart home devices and returns status of those changes. For now, only supported one trait and command at a time.',
        'parameters': {
            'type': 'object',
            'properties': {
                'device_ids': {
                    'type': 'array',
                    'description': 'Unique identifiers of smart home devices.',
                    'items': {
                        'type': 'string'
                    }
                },
                'trait_names': {
                    'type': 'array',
                    'description': "Name of the trait to change. Valid traits include: 'OnOff', 'OpenClose', 'StartStop', 'TransportControl', 'Scene', 'InputSelector', 'AppSelector', 'Brightness', 'ColorSetting', 'Dock', 'FanSpeed', 'TemperatureSetting', 'Toggles', 'Locator', 'Broadcast', 'LightEffects', 'Volume', 'Modes', 'LockUnlock', 'CameraStream', 'HumiditySetting', 'ArmDisarm', 'ViewSchedules', 'CancelSchedules'.",
                    'items': {
                        'type': 'string'
                    }
                },
                'command_names': {
                    'type': 'array',
                    'description': "Name of the command. Valid values for command_names depend on trait_name. Valid values are: 'on', 'off', 'toggle_on_off', 'open', 'close', 'open_percent', 'close_percent', 'open_percent_absolute', 'close_percent_absolute', 'open_ambiguous_amount', 'close_ambiguous_amount', 'start', 'stop', 'pause', 'unpause', 'activate_scene', 'deactivate_scene', 'next_input', 'previous_input', 'set_input', 'open_app', 'set_brightness', 'brighter_ambiguous', 'dimmer_ambiguous', 'brighter_percentage', 'dimmer_percentage', 'change_color', 'dock', 'fan_up_ambiguous', 'fan_down_ambiguous', 'set_fan_speed', 'set_fan_speed_percentage', 'fan_up_percentage', 'fan_down_percentage', 'cooler_ambiguous', 'warmer_ambiguous', 'set_temperature', 'set_temperature_celsius', 'set_temperature_fahrenheit', 'set_temperature_mode', 'set_mode_and_temperature', 'set_mode_and_temperature_fahrenheit', 'set_mode_and_temperature_celsius', 'change_relative_temperature', 'toggle_setting', 'find_device', 'silence_ringing', 'broadcast', 'set_light_effect', 'set_light_effect_with_duration', 'volume_up', 'volume_down', 'volume_up_percentage', 'volume_down_percentage', 'volume_up_ambiguous', 'volume_down_ambiguous', 'set_volume_level', 'set_volume_percentage', 'mute', 'unmute', 'set_mode', 'show_device_info', 'lock', 'unlock', 'camera_stream', 'humidity_setting', 'arm_disarm', 'view_schedules', 'cancel_schedules'.",
                    'items': {
                        'type': 'string'
                    }
                },
                'command_values': {
                    'type': 'array',
                    'description': 'New value of the command_name. Valid values for command_values depend on command_name. Default is None.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'device_ids',
                'trait_names',
                'command_names'
            ]
        }
    }
)
def mutate_traits(
    device_ids: List[str],
    trait_names: List[str],
    command_names: List[str],
    command_values: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Changes traits of smart home devices and returns status of those changes. For now, only supported one trait and command at a time.

    Args:
        device_ids (List[str]): Unique identifiers of smart home devices.
        trait_names (List[str]): Name of the trait to change. Valid traits include: 'OnOff', 'OpenClose', 'StartStop', 'TransportControl', 'Scene', 'InputSelector', 'AppSelector', 'Brightness', 'ColorSetting', 'Dock', 'FanSpeed', 'TemperatureSetting', 'Toggles', 'Locator', 'Broadcast', 'LightEffects', 'Volume', 'Modes', 'LockUnlock', 'CameraStream', 'HumiditySetting', 'ArmDisarm', 'ViewSchedules', 'CancelSchedules'.
        command_names (List[str]): Name of the command. Valid values for command_names depend on trait_name. Valid values are: 'on', 'off', 'toggle_on_off', 'open', 'close', 'open_percent', 'close_percent', 'open_percent_absolute', 'close_percent_absolute', 'open_ambiguous_amount', 'close_ambiguous_amount', 'start', 'stop', 'pause', 'unpause', 'activate_scene', 'deactivate_scene', 'next_input', 'previous_input', 'set_input', 'open_app', 'set_brightness', 'brighter_ambiguous', 'dimmer_ambiguous', 'brighter_percentage', 'dimmer_percentage', 'change_color', 'dock', 'fan_up_ambiguous', 'fan_down_ambiguous', 'set_fan_speed', 'set_fan_speed_percentage', 'fan_up_percentage', 'fan_down_percentage', 'cooler_ambiguous', 'warmer_ambiguous', 'set_temperature', 'set_temperature_celsius', 'set_temperature_fahrenheit', 'set_temperature_mode', 'set_mode_and_temperature', 'set_mode_and_temperature_fahrenheit', 'set_mode_and_temperature_celsius', 'change_relative_temperature', 'toggle_setting', 'find_device', 'silence_ringing', 'broadcast', 'set_light_effect', 'set_light_effect_with_duration', 'volume_up', 'volume_down', 'volume_up_percentage', 'volume_down_percentage', 'volume_up_ambiguous', 'volume_down_ambiguous', 'set_volume_level', 'set_volume_percentage', 'mute', 'unmute', 'set_mode', 'show_device_info', 'lock', 'unlock', 'camera_stream', 'humidity_setting', 'arm_disarm', 'view_schedules', 'cancel_schedules'.
        command_values (Optional[List[str]]): New value of the command_name. Valid values for command_values depend on command_name. Default is None.

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
        if len(trait_names) != 1 or len(command_names) != 1:
            raise InvalidInputError(
                f"Invalid input: only supported one trait and command at a time. Got {len(trait_names)} traits and {len(command_names)} commands."
            )

        commands = MutateTraitCommands(
            device_ids=device_ids,
            commands=[{
                "trait": trait_names[0],
                "command_names": command_names,
                "command_values": command_values,
            }],
        )
    except (ValidationError, InvalidInputError) as e:
        if isinstance(e, InvalidInputError):
            raise e
        raise InvalidInputError(f"Invalid input: {e}") from e

    structures = process_schedules_and_get_structures()

    # For mutate_traits, explicit values provided for non-valued commands should be rejected
    op = commands.commands[0].command_names[0].value
    if commands.commands[0].command_values:
        try:
            cmd = CommandName(op)
            from google_home.SimulationEngine.models import COMMANDS_NOT_REQUIRING_VALUES as _CNRV
            if cmd in _CNRV:
                raise InvalidInputError(f"Invalid input: Command '{op}' does not support values.")
        except Exception:
            pass

    results = handle_edge_case_operation(op, device_ids)
    if results:
        return results

    # Validate all device IDs up-front
    id_to_device = validate_device_ids_exist(device_ids)

    results = []
    # Stage then commit (directly use engine to keep single source of truth)
    staged_by_id: Dict[str, Dict[str, Any]] = {}
    for device_id in device_ids:
        device = id_to_device[device_id]
        staged = clone_device(device)
        for command in commands.commands:
            cmd_name = command.command_names[0]
            cmd_values = command.command_values or []
            try:
                from google_home.engine.registry import apply_command as _apply
                _apply(staged, cmd_name, cmd_values)
            except ValidationError as e:
                raise InvalidInputError(f"Invalid input: {e}") from e
            except ValueError as e:
                raise InvalidInputError(f"Invalid input: {e}") from e
        staged_by_id[device_id] = staged

    for device_id in device_ids:
        device = id_to_device[device_id]
        staged = staged_by_id[device_id]
        commit_staged_device_state(device, staged)
        results.append(
            MutateTraitResult(
                commands=commands,
                result="SUCCESS",
                device_execution_results={
                    "text_to_speech": f"Successfully mutated {device_id}",
                    "results": [
                        {"device_id": device_id, "result": "SUCCESS"}
                    ],
                },
            ).model_dump(mode="json")
        )

    action = Action(
        action_type=APIName.MUTATE_TRAITS,
        inputs={
            "device_ids": device_ids,
            "trait_names": trait_names,
            "command_names": command_names,
            "command_values": command_values,
        },
        outputs={"results": results},
    )
    DB["actions"].append(action.model_dump(mode="json"))

    return results