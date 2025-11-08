from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from google_home.SimulationEngine.custom_errors import InvalidInputError

from google_home.SimulationEngine.models import (
    TRAIT_COMMAND_MAP,
    COMMAND_STATE_MAP,
    STATELESS_COMMANDS,
    COMMAND_VALUE_MAP,
    THERMOSTAT_STRING_TO_FLOAT_MAP,
    CommandName,
    TraitName,
    StateName,
)

from .specs import CommandSpec
from . import value_models as vm


def _get_state(device: dict, state_name: StateName) -> dict:
    for state in device.get("device_state", []):
        n = state.get("name")
        if n == state_name or n == state_name.value:
            # normalize name to string value for consistency
            state["name"] = state_name.value
            return state
    state = {"name": state_name.value}
    device.setdefault("device_state", []).append(state)
    return state


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _as_bool_str(val: str) -> bool:
    v = str(val).lower()
    if v == "true":
        return True
    if v == "false":
        return False
    raise ValueError("Expected 'true' or 'false'")


def _get_current_numeric(device: dict, state_name: StateName, default: float = 0.0) -> float:
    for s in device.get("device_state", []):
        if s.get("name") == state_name:
            try:
                return float(s.get("value"))
            except Exception:
                return default
    return default


def _normalize_unit(u: str) -> str:
    l = u.lower()
    if l.startswith("c"):
        return "C"
    if l.startswith("f"):
        return "F"
    return u


def _convert_value(value: float, from_unit: str, to_unit: str) -> float:
    fu = _normalize_unit(from_unit)
    tu = _normalize_unit(to_unit)
    if fu == tu:
        return value
    if fu == "F" and tu == "C":
        return (value - 32.0) * 5.0 / 9.0
    if fu == "C" and tu == "F":
        return (value * 9.0 / 5.0) + 32.0
    return value


def _convert_delta(delta: float, from_unit: str, to_unit: str) -> float:
    fu = _normalize_unit(from_unit)
    tu = _normalize_unit(to_unit)
    if fu == tu:
        return delta
    if fu == "F" and tu == "C":
        return delta * 5.0 / 9.0
    if fu == "C" and tu == "F":
        return delta * 9.0 / 5.0
    return delta


def _handle_default_assignment(command: CommandName, device: dict, values_model: BaseModel, target_states: List[StateName]) -> None:
    if command in COMMAND_VALUE_MAP:
        const_value = COMMAND_VALUE_MAP[command]
        for st in target_states:
            _get_state(device, st)["value"] = const_value
        return

    if values_model is not None and hasattr(values_model, "values"):
        v_tuple = getattr(values_model, "values")
        if len(target_states) == 1 and len(v_tuple) >= 1:
            _get_state(device, target_states[0])["value"] = v_tuple[0]
            return

    raise NotImplementedError(f"No default assignment rule for command {command.value}")


def _handler_toggle_on_off(device: dict, _: BaseModel) -> None:
    st = _get_state(device, StateName.ON)
    st["value"] = not bool(st.get("value", False))


def _handler_set_mode_and_temperature(device: dict, values: vm.ModeAndTemperature) -> None:
    mode, temp = values.values
    _get_state(device, StateName.THERMOSTAT_MODE)["value"] = mode
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    st["value"] = float(temp)


def _handler_set_mode_and_temperature_no_unit(device: dict, values: vm.ModeAndTemperature) -> None:
    mode, temp = values.values
    _get_state(device, StateName.THERMOSTAT_MODE)["value"] = mode
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    try:
        st["value"] = float(temp)
    except Exception:
        raise ValueError("Invalid thermostat temperature. Value must be a float or one of ['min', 'max'].")


def _handler_set_mode_and_temperature_celsius(device: dict, values: vm.ModeAndTemperature) -> None:
    mode, temp = values.values
    _get_state(device, StateName.THERMOSTAT_MODE)["value"] = mode
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    existing_unit = st.get("unit", "F")
    st["value"] = _convert_value(float(temp), "C", existing_unit)


def _handler_set_mode_and_temperature_fahrenheit(device: dict, values: vm.ModeAndTemperature) -> None:
    mode, temp = values.values
    _get_state(device, StateName.THERMOSTAT_MODE)["value"] = mode
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    existing_unit = st.get("unit", "F")
    st["value"] = _convert_value(float(temp), "F", existing_unit)


def _handler_set_mode(device: dict, values: vm.ModeIdAndValue | vm.ModeOnly) -> None:
    if len(values.values) == 2:
        mode_id, mode_value = values.values
    else:
        mode_id, mode_value = values.values[0], ""
    current_modes = _get_state(device, StateName.CURRENT_MODES)
    if "value" not in current_modes or not isinstance(current_modes["value"], dict):
        current_modes["value"] = {}
    if mode_id is not None and mode_value is not None:
        # Validate mode_id exists in toggles_modes and value is allowed if settings provided
        valid_mode_ids = [tm.get("id") for tm in device.get("toggles_modes", []) if tm.get("id") is not None]
        if mode_id not in valid_mode_ids:
            raise ValueError(f"Invalid mode. Must be one of {valid_mode_ids}.")
        allowed_values = None
        for tm in device.get("toggles_modes", []):
            if tm.get("id") == mode_id:
                settings = tm.get("settings", [])
                if settings:
                    allowed_values = [s.get("id") for s in settings if s.get("id") is not None]
                break
        if allowed_values is not None and mode_value and mode_value not in allowed_values:
            raise ValueError(f"Invalid mode. Must be one of {allowed_values}.")
        if mode_value == "":
            current_modes["value"].pop(mode_id, None)
        else:
            current_modes["value"][mode_id] = mode_value


def _handler_toggle_setting(device: dict, values: vm.ToggleSettingValues) -> None:
    toggle_id, toggle_val = values.values
    toggles = _get_state(device, StateName.ACTIVE_TOGGLES)
    if "value" not in toggles or not isinstance(toggles["value"], dict):
        toggles["value"] = {}
    toggles["value"][toggle_id] = _as_bool_str(toggle_val)


def _handler_pause(device: dict, _: BaseModel) -> None:
    _get_state(device, StateName.IS_PAUSED)["value"] = True


def _handler_unpause(device: dict, _: BaseModel) -> None:
    _get_state(device, StateName.IS_PAUSED)["value"] = False


def _handler_start(device: dict, _: BaseModel) -> None:
    _get_state(device, StateName.IS_STOPPED)["value"] = False


def _handler_stop(device: dict, _: BaseModel) -> None:
    _get_state(device, StateName.IS_STOPPED)["value"] = True


def _handler_open_percent(device: dict, values: vm.SinglePercent) -> None:
    cur = _get_current_numeric(device, StateName.OPEN_PERCENT, default=0.0)
    new_val = _clamp(cur + float(values.values[0]), 0.0, 100.0)
    _get_state(device, StateName.OPEN_PERCENT)["value"] = new_val


def _handler_close_percent(device: dict, values: vm.SinglePercent) -> None:
    cur = _get_current_numeric(device, StateName.OPEN_PERCENT, default=0.0)
    new_val = _clamp(cur - float(values.values[0]), 0.0, 100.0)
    _get_state(device, StateName.OPEN_PERCENT)["value"] = new_val


def _handler_open_percent_absolute(device: dict, values: vm.SinglePercent) -> None:
    _get_state(device, StateName.OPEN_PERCENT)["value"] = float(values.values[0])


def _handler_close_percent_absolute(device: dict, values: vm.SinglePercent) -> None:
    _get_state(device, StateName.OPEN_PERCENT)["value"] = float(values.values[0])


def _handler_open_ambiguous(device: dict, values: vm.SingleDeltaMinus3to3) -> None:
    step = 15.0 * float(values.values[0])
    cur = _get_current_numeric(device, StateName.OPEN_PERCENT, default=0.0)
    _get_state(device, StateName.OPEN_PERCENT)["value"] = _clamp(cur + step, 0.0, 100.0)


def _handler_close_ambiguous(device: dict, values: vm.SingleDeltaMinus3to3) -> None:
    step = 15.0 * float(values.values[0])
    cur = _get_current_numeric(device, StateName.OPEN_PERCENT, default=0.0)
    _get_state(device, StateName.OPEN_PERCENT)["value"] = _clamp(cur - step, 0.0, 100.0)


def _handler_brighter_ambiguous(device: dict, values: vm.SingleLevel1to5) -> None:
    step = 0.08 * float(values.values[0])
    cur = _get_current_numeric(device, StateName.BRIGHTNESS, default=1.0)
    _get_state(device, StateName.BRIGHTNESS)["value"] = _clamp(cur + step, 0.0, 1.0)


def _handler_dimmer_ambiguous(device: dict, values: vm.SingleLevel1to5) -> None:
    step = 0.08 * float(values.values[0])
    cur = _get_current_numeric(device, StateName.BRIGHTNESS, default=1.0)
    _get_state(device, StateName.BRIGHTNESS)["value"] = _clamp(cur - step, 0.0, 1.0)


def _handler_brighter_percentage(device: dict, values: vm.SinglePercent) -> None:
    cur = _get_current_numeric(device, StateName.BRIGHTNESS, default=1.0)
    _get_state(device, StateName.BRIGHTNESS)["value"] = _clamp(cur + (float(values.values[0]) / 100.0), 0.0, 1.0)


def _handler_dimmer_percentage(device: dict, values: vm.SinglePercent) -> None:
    cur = _get_current_numeric(device, StateName.BRIGHTNESS, default=1.0)
    _get_state(device, StateName.BRIGHTNESS)["value"] = _clamp(cur - (float(values.values[0]) / 100.0), 0.0, 1.0)


def _handler_set_fan_speed(device: dict, values: vm.FanSpeedText) -> None:
    mapping = {"low": 33, "medium": 66, "high": 100}
    _get_state(device, StateName.FAN_SPEED)["value"] = mapping[values.values[0]]


def _handler_set_fan_speed_percentage(device: dict, values: vm.SinglePercent) -> None:
    _get_state(device, StateName.FAN_SPEED)["value"] = int(float(values.values[0]))


def _handler_fan_up_percentage(device: dict, values: vm.SinglePercent) -> None:
    cur = _get_current_numeric(device, StateName.FAN_SPEED, default=0.0)
    _get_state(device, StateName.FAN_SPEED)["value"] = int(_clamp(cur + float(values.values[0]), 0.0, 100.0))


def _handler_fan_down_percentage(device: dict, values: vm.SinglePercent) -> None:
    cur = _get_current_numeric(device, StateName.FAN_SPEED, default=0.0)
    _get_state(device, StateName.FAN_SPEED)["value"] = int(_clamp(cur - float(values.values[0]), 0.0, 100.0))


def _handler_fan_up_ambiguous(device: dict, values: vm.SingleLevel1to5) -> None:
    cur = _get_current_numeric(device, StateName.FAN_SPEED, default=0.0)
    _get_state(device, StateName.FAN_SPEED)["value"] = int(_clamp(cur + float(values.values[0]) * 10.0, 0.0, 100.0))


def _handler_fan_down_ambiguous(device: dict, values: vm.SingleLevel1to5) -> None:
    cur = _get_current_numeric(device, StateName.FAN_SPEED, default=0.0)
    _get_state(device, StateName.FAN_SPEED)["value"] = int(_clamp(cur - float(values.values[0]) * 10.0, 0.0, 100.0))


def _handler_set_temperature(device: dict, values: vm.TemperatureWithUnit) -> None:
    temp, unit = values.values
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    existing_unit = st.get("unit", "F")
    st["value"] = _convert_value(float(temp), unit, existing_unit)


def _handler_set_temperature_celsius(device: dict, values: vm.SingleFloat) -> None:
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    existing_unit = st.get("unit", "F")
    st["value"] = _convert_value(float(values.values[0]), "C", existing_unit)


def _handler_set_temperature_fahrenheit(device: dict, values: vm.SingleFloat) -> None:
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    existing_unit = st.get("unit", "F")
    st["value"] = _convert_value(float(values.values[0]), "F", existing_unit)


def _handler_set_temperature_mode(device: dict, values: vm.ModeWithUnit) -> None:
    mode, unit = values.values
    _get_state(device, StateName.THERMOSTAT_MODE)["value"] = mode
    # Do not change unit in DB; ignore provided unit for persistence


def _handler_change_relative_temperature(device: dict, values: vm.DeltaWithUnit) -> None:
    delta, unit = values.values
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    cur_val = float(st.get("value", 20.0))
    existing_unit = st.get("unit", "F")
    delta_adj = _convert_delta(float(delta), unit, existing_unit)
    st["value"] = cur_val + delta_adj


def _handler_cooler_warmer_ambiguous(device: dict, values: vm.LevelWithUnit, direction: int) -> None:
    level, unit = values.values
    st = _get_state(device, StateName.THERMOSTAT_TEMPERATURE_SETPOINT)
    cur_val = float(st.get("value", 20.0))
    existing_unit = st.get("unit", "F")
    delta_adj = _convert_delta(float(level), unit, existing_unit)
    st["value"] = cur_val + direction * delta_adj


def _handler_cooler_ambiguous(device: dict, values: vm.LevelWithUnit) -> None:
    _handler_cooler_warmer_ambiguous(device, values, direction=-1)


def _handler_warmer_ambiguous(device: dict, values: vm.LevelWithUnit) -> None:
    _handler_cooler_warmer_ambiguous(device, values, direction=1)


def _handler_set_input(device: dict, values: vm.SingleSlug) -> None:
    _get_state(device, StateName.CURRENT_INPUT)["value"] = values.values[0]


def _handler_next_input(device: dict, _: BaseModel) -> None:
    order = ["hdmi_1", "hdmi_2", "hdmi_3", "tv", "av"]
    st = _get_state(device, StateName.CURRENT_INPUT)
    cur = st.get("value", order[0])
    try:
        idx = order.index(cur)
    except ValueError:
        idx = 0
    st["value"] = order[(idx + 1) % len(order)]


def _handler_previous_input(device: dict, _: BaseModel) -> None:
    order = ["hdmi_1", "hdmi_2", "hdmi_3", "tv", "av"]
    st = _get_state(device, StateName.CURRENT_INPUT)
    cur = st.get("value", order[0])
    try:
        idx = order.index(cur)
    except ValueError:
        idx = 0
    st["value"] = order[(idx - 1) % len(order)]


def _handler_open_app(device: dict, values: vm.AppKey) -> None:
    _get_state(device, StateName.CURRENT_APP)["value"] = values.values[0]


def _handler_set_volume_level(device: dict, values: vm.VolumeLevel) -> None:
    _get_state(device, StateName.CURRENT_VOLUME)["value"] = int(values.values[0])


def _handler_set_volume_percentage(device: dict, values: vm.SinglePercent) -> None:
    _get_state(device, StateName.CURRENT_VOLUME)["value"] = int(float(values.values[0]))


def _handler_volume_up(device: dict, values: vm.VolumeLevel) -> None:
    cur = _get_current_numeric(device, StateName.CURRENT_VOLUME, default=0)
    _get_state(device, StateName.CURRENT_VOLUME)["value"] = int(_clamp(cur + int(values.values[0]), 0, 100))


def _handler_volume_down(device: dict, values: vm.VolumeLevel) -> None:
    cur = _get_current_numeric(device, StateName.CURRENT_VOLUME, default=0)
    _get_state(device, StateName.CURRENT_VOLUME)["value"] = int(_clamp(cur - int(values.values[0]), 0, 100))


def _handler_volume_up_percentage(device: dict, values: vm.SinglePercent) -> None:
    cur = _get_current_numeric(device, StateName.CURRENT_VOLUME, default=0)
    _get_state(device, StateName.CURRENT_VOLUME)["value"] = int(_clamp(cur + float(values.values[0]), 0, 100))


def _handler_volume_down_percentage(device: dict, values: vm.SinglePercent) -> None:
    cur = _get_current_numeric(device, StateName.CURRENT_VOLUME, default=0)
    _get_state(device, StateName.CURRENT_VOLUME)["value"] = int(_clamp(cur - float(values.values[0]), 0, 100))


def _handler_volume_up_ambiguous(device: dict, values: vm.SingleLevel1to5) -> None:
    cur = _get_current_numeric(device, StateName.CURRENT_VOLUME, default=0)
    _get_state(device, StateName.CURRENT_VOLUME)["value"] = int(_clamp(cur + int(values.values[0]) * 5, 0, 100))


def _handler_volume_down_ambiguous(device: dict, values: vm.SingleLevel1to5) -> None:
    cur = _get_current_numeric(device, StateName.CURRENT_VOLUME, default=0)
    _get_state(device, StateName.CURRENT_VOLUME)["value"] = int(_clamp(cur - int(values.values[0]) * 5, 0, 100))


def _handler_set_light_effect(device: dict, values: vm.LightEffectOnly) -> None:
    effect = values.values[0]
    current_modes = _get_state(device, StateName.CURRENT_MODES)
    if "value" not in current_modes or not isinstance(current_modes["value"], dict):
        current_modes["value"] = {}
    current_modes["value"]["lightEffect"] = effect


def _handler_set_light_effect_with_duration(device: dict, values: vm.LightEffectWithDuration) -> None:
    effect, _ = values.values
    _handler_set_light_effect(device, vm.LightEffectOnly(values=(effect,)))


VALUES_MODEL_BY_COMMAND: Dict[CommandName, type[BaseModel]] = {
    # OnOff
    CommandName.ON: vm.NoValues,
    CommandName.OFF: vm.NoValues,
    CommandName.TOGGLE_ON_OFF: vm.NoValues,

    # OpenClose
    CommandName.OPEN: vm.NoValues,
    CommandName.CLOSE: vm.NoValues,
    CommandName.OPEN_PERCENT: vm.SinglePercent,
    CommandName.CLOSE_PERCENT: vm.SinglePercent,
    CommandName.OPEN_PERCENT_ABSOLUTE: vm.SinglePercent,
    CommandName.CLOSE_PERCENT_ABSOLUTE: vm.SinglePercent,
    CommandName.OPEN_AMBIGUOUS_AMOUNT: vm.SingleDeltaMinus3to3,
    CommandName.CLOSE_AMBIGUOUS_AMOUNT: vm.SingleDeltaMinus3to3,

    # StartStop / TransportControl
    CommandName.START: vm.NoValues,
    CommandName.STOP: vm.NoValues,
    CommandName.PAUSE: vm.NoValues,
    CommandName.UNPAUSE: vm.NoValues,

    # Scene
    CommandName.ACTIVATE_SCENE: vm.NoValues,
    CommandName.DEACTIVATE_SCENE: vm.NoValues,

    # InputSelector
    CommandName.NEXT_INPUT: vm.NoValues,
    CommandName.PREVIOUS_INPUT: vm.NoValues,
    CommandName.SET_INPUT: vm.SingleSlug,

    # AppSelector
    CommandName.OPEN_APP: vm.AppKey,

    # Brightness
    CommandName.SET_BRIGHTNESS: vm.SingleFloat01,
    CommandName.BRIGHTER_AMBIGUOUS: vm.SingleLevel1to5,
    CommandName.DIMMER_AMBIGUOUS: vm.SingleLevel1to5,
    CommandName.BRIGHTER_PERCENTAGE: vm.SinglePercent,
    CommandName.DIMMER_PERCENTAGE: vm.SinglePercent,

    # ColorSetting
    CommandName.CHANGE_COLOR: vm.SingleSlug,

    # Dock
    CommandName.DOCK: vm.NoValues,

    # FanSpeed
    CommandName.FAN_UP_AMBIGUOUS: vm.SingleLevel1to5,
    CommandName.FAN_DOWN_AMBIGUOUS: vm.SingleLevel1to5,
    CommandName.SET_FAN_SPEED: vm.FanSpeedText,
    CommandName.SET_FAN_SPEED_PERCENTAGE: vm.SinglePercent,
    CommandName.FAN_UP_PERCENTAGE: vm.SinglePercent,
    CommandName.FAN_DOWN_PERCENTAGE: vm.SinglePercent,

    # TemperatureSetting
    CommandName.COOLER_AMBIGUOUS: vm.LevelWithUnit,
    CommandName.WARMER_AMBIGUOUS: vm.LevelWithUnit,
    CommandName.SET_TEMPERATURE: vm.TemperatureWithUnit,
    CommandName.SET_TEMPERATURE_CELSIUS: vm.SingleFloat,
    CommandName.SET_TEMPERATURE_FAHRENHEIT: vm.SingleFloat,
    CommandName.SET_TEMPERATURE_MODE: vm.ModeWithUnit,
    CommandName.SET_MODE_AND_TEMPERATURE: vm.ModeAndTemperature,
    CommandName.SET_MODE_AND_TEMPERATURE_FAHRENHEIT: vm.ModeAndTemperature,
    CommandName.SET_MODE_AND_TEMPERATURE_CELSIUS: vm.ModeAndTemperature,
    CommandName.CHANGE_RELATIVE_TEMPERATURE: vm.DeltaWithUnit,

    # Toggles
    CommandName.TOGGLE_SETTING: vm.ToggleSettingValues,

    # Locator
    CommandName.FIND_DEVICE: vm.NoValues,
    CommandName.SILENCE_RINGING: vm.NoValues,

    # Broadcast
    CommandName.BROADCAST: vm.NonEmptyMessage,

    # LightEffects
    CommandName.SET_LIGHT_EFFECT: vm.LightEffectOnly,
    CommandName.SET_LIGHT_EFFECT_WITH_DURATION: vm.LightEffectWithDuration,

    # Volume
    CommandName.VOLUME_UP: vm.VolumeLevel,
    CommandName.VOLUME_DOWN: vm.VolumeLevel,
    CommandName.VOLUME_UP_PERCENTAGE: vm.SinglePercent,
    CommandName.VOLUME_DOWN_PERCENTAGE: vm.SinglePercent,
    CommandName.VOLUME_UP_AMBIGUOUS: vm.SingleLevel1to5,
    CommandName.VOLUME_DOWN_AMBIGUOUS: vm.SingleLevel1to5,
    CommandName.SET_VOLUME_LEVEL: vm.VolumeLevel,
    CommandName.SET_VOLUME_PERCENTAGE: vm.SinglePercent,
    CommandName.MUTE: vm.NoValues,
    CommandName.UNMUTE: vm.NoValues,

    # Modes
    CommandName.SET_MODE: vm.ModeIdAndValue,

    # LockUnlock
    CommandName.LOCK: vm.NoValues,
    CommandName.UNLOCK: vm.NoValues,

    # Minimal support traits
    CommandName.CAMERA_STREAM: vm.NoValues,
    CommandName.HUMIDITY_SETTING: vm.NoValues,
    CommandName.ARM_DISARM: vm.NoValues,

    # Schedules / Show info
    CommandName.VIEW_SCHEDULES: vm.NoValues,
    CommandName.CANCEL_SCHEDULES: vm.NoValues,
    CommandName.SHOW_DEVICE_INFO: vm.NoValues,
}


SPECIALIZED_HANDLERS = {
    CommandName.TOGGLE_ON_OFF: _handler_toggle_on_off,
    CommandName.SET_MODE_AND_TEMPERATURE: _handler_set_mode_and_temperature,
    CommandName.SET_MODE_AND_TEMPERATURE_FAHRENHEIT: _handler_set_mode_and_temperature_fahrenheit,
    CommandName.SET_MODE_AND_TEMPERATURE_CELSIUS: _handler_set_mode_and_temperature_celsius,
    CommandName.SET_MODE: _handler_set_mode,
    CommandName.TOGGLE_SETTING: _handler_toggle_setting,
    CommandName.PAUSE: _handler_pause,
    CommandName.UNPAUSE: _handler_unpause,
    CommandName.START: _handler_start,
    CommandName.STOP: _handler_stop,
    CommandName.OPEN_PERCENT: _handler_open_percent,
    CommandName.CLOSE_PERCENT: _handler_close_percent,
    CommandName.OPEN_PERCENT_ABSOLUTE: _handler_open_percent_absolute,
    CommandName.CLOSE_PERCENT_ABSOLUTE: _handler_close_percent_absolute,
    CommandName.OPEN_AMBIGUOUS_AMOUNT: _handler_open_ambiguous,
    CommandName.CLOSE_AMBIGUOUS_AMOUNT: _handler_close_ambiguous,
    CommandName.BRIGHTER_AMBIGUOUS: _handler_brighter_ambiguous,
    CommandName.DIMMER_AMBIGUOUS: _handler_dimmer_ambiguous,
    CommandName.BRIGHTER_PERCENTAGE: _handler_brighter_percentage,
    CommandName.DIMMER_PERCENTAGE: _handler_dimmer_percentage,
    CommandName.SET_FAN_SPEED: _handler_set_fan_speed,
    CommandName.SET_FAN_SPEED_PERCENTAGE: _handler_set_fan_speed_percentage,
    CommandName.FAN_UP_PERCENTAGE: _handler_fan_up_percentage,
    CommandName.FAN_DOWN_PERCENTAGE: _handler_fan_down_percentage,
    CommandName.FAN_UP_AMBIGUOUS: _handler_fan_up_ambiguous,
    CommandName.FAN_DOWN_AMBIGUOUS: _handler_fan_down_ambiguous,
    CommandName.SET_TEMPERATURE: _handler_set_temperature,
    CommandName.SET_TEMPERATURE_CELSIUS: _handler_set_temperature_celsius,
    CommandName.SET_TEMPERATURE_FAHRENHEIT: _handler_set_temperature_fahrenheit,
    CommandName.SET_TEMPERATURE_MODE: _handler_set_temperature_mode,
    CommandName.CHANGE_RELATIVE_TEMPERATURE: _handler_change_relative_temperature,
    CommandName.COOLER_AMBIGUOUS: _handler_cooler_ambiguous,
    CommandName.WARMER_AMBIGUOUS: _handler_warmer_ambiguous,
    CommandName.SET_INPUT: _handler_set_input,
    CommandName.NEXT_INPUT: _handler_next_input,
    CommandName.PREVIOUS_INPUT: _handler_previous_input,
    CommandName.OPEN_APP: _handler_open_app,
    CommandName.SET_VOLUME_LEVEL: _handler_set_volume_level,
    CommandName.SET_VOLUME_PERCENTAGE: _handler_set_volume_percentage,
    CommandName.VOLUME_UP: _handler_volume_up,
    CommandName.VOLUME_DOWN: _handler_volume_down,
    CommandName.VOLUME_UP_PERCENTAGE: _handler_volume_up_percentage,
    CommandName.VOLUME_DOWN_PERCENTAGE: _handler_volume_down_percentage,
    CommandName.VOLUME_UP_AMBIGUOUS: _handler_volume_up_ambiguous,
    CommandName.VOLUME_DOWN_AMBIGUOUS: _handler_volume_down_ambiguous,
    CommandName.SET_LIGHT_EFFECT: _handler_set_light_effect,
    CommandName.SET_LIGHT_EFFECT_WITH_DURATION: _handler_set_light_effect_with_duration,
}


def build_registry() -> Dict[CommandName, CommandSpec]:
    registry: Dict[CommandName, CommandSpec] = {}
    for trait, commands in TRAIT_COMMAND_MAP.items():
        for cmd in commands:
            values_model_cls = VALUES_MODEL_BY_COMMAND.get(cmd, vm.NoValues)
            target_states = COMMAND_STATE_MAP.get(cmd, [])
            stateless = cmd in STATELESS_COMMANDS or len(target_states) == 0
            handler = SPECIALIZED_HANDLERS.get(cmd)
            spec = CommandSpec(
                trait=trait,
                op=cmd,
                values_model=values_model_cls,
                target_states=target_states,
                handler=handler,
                stateless=stateless,
            )
            registry[cmd] = spec
    return registry


REGISTRY: Dict[CommandName, CommandSpec] = build_registry()


def apply_command(device_copy: dict, command: CommandName, values: Optional[List[str]]) -> None:
    spec = REGISTRY.get(command)
    if not spec:
        raise NotImplementedError(f"Command '{command.value}' is not supported.")

    model_cls = spec.values_model
    parsed: BaseModel
    # Centralized validation for value presence/absence and friendly errors
    incoming_values = values or []
    # Non-valued commands must not have any values (including empty strings)
    if model_cls is vm.NoValues:
        # Any provided value (including empty string) is not allowed
        if len(incoming_values) > 0:
            raise ValueError(f"Command '{command.value}' does not support values.")
        parsed = model_cls(values=tuple(incoming_values))
    else:
        # Valued commands must provide values
        if len(incoming_values) == 0:
            raise ValueError(f"Command '{command.value}' requires values.")
        # Friendly pre-checks for specific commands (to match OpenAPI spec messages)
        if command == CommandName.SET_FAN_SPEED:
            allowed = {"low", "medium", "high"}
            if not incoming_values or incoming_values[0].lower() not in allowed:
                allowed_str = ", ".join(sorted(allowed))
                # Keep message aligned with tests and OpenAPI
                raise InvalidInputError(f"Invalid fan speed. Must be one of: {allowed_str}.")
        if command in (CommandName.SET_LIGHT_EFFECT, CommandName.SET_LIGHT_EFFECT_WITH_DURATION):
            allowed_effects = ["sleep", "wake", "colorLoop", "pulse"]
            effect = incoming_values[0]
            if effect not in allowed_effects:
                allowed_str = ", ".join(allowed_effects)
                raise InvalidInputError(
                    f"Invalid light effect. Must be one of: {allowed_str}. Use 'set_mode' for other effects."
                )
            if command == CommandName.SET_LIGHT_EFFECT_WITH_DURATION:
                if len(incoming_values) < 2:
                    raise InvalidInputError(
                        "Invalid input: set_light_effect_with_duration requires two values: effect and duration_seconds."
                    )
                try:
                    duration = int(incoming_values[1])
                except Exception:
                    raise InvalidInputError("Invalid input: duration must be a positive integer (seconds).")
                if duration < 1:
                    raise InvalidInputError("Invalid input: duration must be a positive integer (seconds).")
        parsed = model_cls(values=tuple(incoming_values))

    if spec.stateless:
        return

    if spec.handler:
        spec.handler(device_copy, parsed)
        return

    _handler_default = lambda dev, m: _handle_default_assignment(command, dev, m, spec.target_states)
    _handler_default(device_copy, parsed)


