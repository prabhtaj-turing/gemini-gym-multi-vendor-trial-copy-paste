from enum import Enum
from typing import List, Optional, Union, Dict, Any, Set
from pydantic import BaseModel, Field, model_validator, StrictStr, StrictBool, StrictInt, StrictFloat

# ===========================================================================
# SECTION 1: ENUMERATIONS
# ===========================================================================

class TraitName(str, Enum):
    ON_OFF = "OnOff"
    OPEN_CLOSE = "OpenClose"
    START_STOP = "StartStop"
    TRANSPORT_CONTROL = "TransportControl"
    SCENE = "Scene"
    INPUT_SELECTOR = "InputSelector"
    APP_SELECTOR = "AppSelector"
    BRIGHTNESS = "Brightness"
    COLOR_SETTING = "ColorSetting"
    DOCK = "Dock"
    FAN_SPEED = "FanSpeed"
    TEMPERATURE_SETTING = "TemperatureSetting"
    TOGGLES = "Toggles"
    LOCATOR = "Locator"
    BROADCAST = "Broadcast"
    LIGHT_EFFECTS = "LightEffects"
    VOLUME = "Volume"
    MODES = "Modes"
    LOCK_UNLOCK = "LockUnlock"
    CAMERA_STREAM = "CameraStream"
    HUMIDITY_SETTING = "HumiditySetting"
    ARM_DISARM = "ArmDisarm"
    VIEW_SCHEDULES = "ViewSchedules"
    CANCEL_SCHEDULES = "CancelSchedules"

class DeviceType(str, Enum):
    THERMOSTAT = "THERMOSTAT"
    LIGHT = "LIGHT"
    OUTLET = "OUTLET"
    TV = "TV"
    AC_UNIT = "AC_UNIT"
    SPEAKER = "SPEAKER"
    VACUUM = "VACUUM"
    SCENE = "SCENE"
    BLINDS = "BLINDS"
    CAMERA = "CAMERA"
    DOOR = "DOOR"
    WINDOW = "WINDOW"
    GARAGE = "GARAGE"
    LOCK = "LOCK"
    SWITCH = "SWITCH"
    FAN = "FAN"

class CommandName(str, Enum):
    ON = "on"
    OFF = "off"
    TOGGLE_ON_OFF = "toggle_on_off"
    OPEN = "open"
    CLOSE = "close"
    OPEN_PERCENT = "open_percent"
    CLOSE_PERCENT = "close_percent"
    OPEN_PERCENT_ABSOLUTE = "open_percent_absolute"
    CLOSE_PERCENT_ABSOLUTE = "close_percent_absolute"
    OPEN_AMBIGUOUS_AMOUNT = "open_ambiguous_amount"
    CLOSE_AMBIGUOUS_AMOUNT = "close_ambiguous_amount"
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    UNPAUSE = "unpause"
    ACTIVATE_SCENE = "activate_scene"
    DEACTIVATE_SCENE = "deactivate_scene"
    NEXT_INPUT = "next_input"
    PREVIOUS_INPUT = "previous_input"
    SET_INPUT = "set_input"
    OPEN_APP = "open_app"
    SET_BRIGHTNESS = "set_brightness"
    BRIGHTER_AMBIGUOUS = "brighter_ambiguous"
    DIMMER_AMBIGUOUS = "dimmer_ambiguous"
    BRIGHTER_PERCENTAGE = "brighter_percentage"
    DIMMER_PERCENTAGE = "dimmer_percentage"
    CHANGE_COLOR = "change_color"
    DOCK = "dock"
    FAN_UP_AMBIGUOUS = "fan_up_ambiguous"
    FAN_DOWN_AMBIGUOUS = "fan_down_ambiguous"
    SET_FAN_SPEED = "set_fan_speed"
    SET_FAN_SPEED_PERCENTAGE = "set_fan_speed_percentage"
    FAN_UP_PERCENTAGE = "fan_up_percentage"
    FAN_DOWN_PERCENTAGE = "fan_down_percentage"
    COOLER_AMBIGUOUS = "cooler_ambiguous"
    WARMER_AMBIGUOUS = "warmer_ambiguous"
    SET_TEMPERATURE = "set_temperature"
    SET_TEMPERATURE_CELSIUS = "set_temperature_celsius"
    SET_TEMPERATURE_FAHRENHEIT = "set_temperature_fahrenheit"
    SET_TEMPERATURE_MODE = "set_temperature_mode"
    SET_MODE_AND_TEMPERATURE = "set_mode_and_temperature"
    SET_MODE_AND_TEMPERATURE_FAHRENHEIT = "set_mode_and_temperature_fahrenheit"
    SET_MODE_AND_TEMPERATURE_CELSIUS = "set_mode_and_temperature_celsius"
    CHANGE_RELATIVE_TEMPERATURE = "change_relative_temperature"
    TOGGLE_SETTING = "toggle_setting"
    FIND_DEVICE = "find_device"
    SILENCE_RINGING = "silence_ringing"
    BROADCAST = "broadcast"
    SET_LIGHT_EFFECT = "set_light_effect"
    SET_LIGHT_EFFECT_WITH_DURATION = "set_light_effect_with_duration"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    VOLUME_UP_PERCENTAGE = "volume_up_percentage"
    VOLUME_DOWN_PERCENTAGE = "volume_down_percentage"
    VOLUME_UP_AMBIGUOUS = "volume_up_ambiguous"
    VOLUME_DOWN_AMBIGUOUS = "volume_down_ambiguous"
    SET_VOLUME_LEVEL = "set_volume_level"
    SET_VOLUME_PERCENTAGE = "set_volume_percentage"
    MUTE = "mute"
    UNMUTE = "unmute"
    SET_MODE = "set_mode"
    SHOW_DEVICE_INFO = "show_device_info"
    LOCK = "lock"
    UNLOCK = "unlock"
    CAMERA_STREAM = "camera_stream"
    HUMIDITY_SETTING = "humidity_setting"
    ARM_DISARM = "arm_disarm"
    VIEW_SCHEDULES = "view_schedules"
    CANCEL_SCHEDULES = "cancel_schedules"

class LightEffect(str, Enum):
    SLEEP = "sleep"
    WAKE = "wake"
    COLOR_LOOP = "colorLoop"
    PULSE = "pulse"

class FanSpeedSetting(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ExecutionResult(str, Enum):
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    OFFLINE = "OFFLINE"
    FAILURE = "FAILURE"

class MutateTraitResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    SHOW_DEVICES_ONLY = "SHOW_DEVICES_ONLY"
    FAILURE = "FAILURE"

class StateName(str, Enum):
    ON = "on"
    IS_PAUSED = "isPaused"
    IS_STOPPED = "isStopped"
    BRIGHTNESS = "brightness"
    COLOR = "color"
    THERMOSTAT_TEMPERATURE_SETPOINT = "thermostatTemperatureSetpoint"
    THERMOSTAT_MODE = "thermostatMode"
    THERMOSTAT_TEMPERATURE_AMBIENT = "thermostatTemperatureAmbient"
    FAN_SPEED = "fanSpeed"
    OPEN_PERCENT = "openPercent"
    CURRENT_VOLUME = "currentVolume"
    IS_MUTED = "isMuted"
    CURRENT_INPUT = "currentInput"
    CURRENT_APP = "currentApp"
    IS_LOCKED = "isLocked"
    IS_DOCKED = "isDocked"
    ACTIVE_TOGGLES = "activeToggles"
    CURRENT_MODES = "currentModes"
    IS_RINGING = "isRinging"
    SCHEDULES = "schedules"
    IS_ARMED = "isArmed"
    HUMIDITY_SETTING = "humiditySetting"

# ===========================================================================
# SECTION 2: VALIDATION AND TRANSFORMATION MAPPINGS
# ===========================================================================

TRAIT_COMMAND_MAP: Dict[TraitName, List[CommandName]] = {
    TraitName.ON_OFF: [CommandName.ON, CommandName.OFF, CommandName.TOGGLE_ON_OFF],
    TraitName.OPEN_CLOSE: [CommandName.OPEN, CommandName.CLOSE, CommandName.OPEN_PERCENT, CommandName.CLOSE_PERCENT, CommandName.OPEN_PERCENT_ABSOLUTE, CommandName.CLOSE_PERCENT_ABSOLUTE, CommandName.OPEN_AMBIGUOUS_AMOUNT, CommandName.CLOSE_AMBIGUOUS_AMOUNT],
    TraitName.START_STOP: [CommandName.START, CommandName.STOP, CommandName.PAUSE, CommandName.UNPAUSE],
    TraitName.TRANSPORT_CONTROL: [CommandName.START, CommandName.STOP, CommandName.PAUSE, CommandName.UNPAUSE],
    TraitName.SCENE: [CommandName.ACTIVATE_SCENE, CommandName.DEACTIVATE_SCENE],
    TraitName.INPUT_SELECTOR: [CommandName.NEXT_INPUT, CommandName.PREVIOUS_INPUT, CommandName.SET_INPUT],
    TraitName.APP_SELECTOR: [CommandName.OPEN_APP],
    TraitName.BRIGHTNESS: [CommandName.SET_BRIGHTNESS, CommandName.BRIGHTER_AMBIGUOUS, CommandName.DIMMER_AMBIGUOUS, CommandName.BRIGHTER_PERCENTAGE, CommandName.DIMMER_PERCENTAGE],
    TraitName.COLOR_SETTING: [CommandName.CHANGE_COLOR],
    TraitName.DOCK: [CommandName.DOCK],
    TraitName.FAN_SPEED: [CommandName.FAN_UP_AMBIGUOUS, CommandName.FAN_DOWN_AMBIGUOUS, CommandName.SET_FAN_SPEED, CommandName.SET_FAN_SPEED_PERCENTAGE, CommandName.FAN_UP_PERCENTAGE, CommandName.FAN_DOWN_PERCENTAGE],
    TraitName.TEMPERATURE_SETTING: [CommandName.COOLER_AMBIGUOUS, CommandName.WARMER_AMBIGUOUS, CommandName.SET_TEMPERATURE, CommandName.SET_TEMPERATURE_CELSIUS, CommandName.SET_TEMPERATURE_FAHRENHEIT, CommandName.SET_TEMPERATURE_MODE, CommandName.SET_MODE_AND_TEMPERATURE, CommandName.SET_MODE_AND_TEMPERATURE_FAHRENHEIT, CommandName.SET_MODE_AND_TEMPERATURE_CELSIUS, CommandName.CHANGE_RELATIVE_TEMPERATURE],
    TraitName.TOGGLES: [CommandName.TOGGLE_SETTING],
    TraitName.LOCATOR: [CommandName.FIND_DEVICE, CommandName.SILENCE_RINGING],
    TraitName.BROADCAST: [CommandName.BROADCAST],
    TraitName.LIGHT_EFFECTS: [CommandName.SET_LIGHT_EFFECT, CommandName.SET_LIGHT_EFFECT_WITH_DURATION],
    TraitName.VOLUME: [CommandName.VOLUME_UP, CommandName.VOLUME_DOWN, CommandName.VOLUME_UP_PERCENTAGE, CommandName.VOLUME_DOWN_PERCENTAGE, CommandName.VOLUME_UP_AMBIGUOUS, CommandName.VOLUME_DOWN_AMBIGUOUS, CommandName.SET_VOLUME_LEVEL, CommandName.SET_VOLUME_PERCENTAGE, CommandName.MUTE, CommandName.UNMUTE],
    TraitName.MODES: [CommandName.SET_MODE],
    TraitName.LOCK_UNLOCK: [CommandName.LOCK, CommandName.UNLOCK],
    TraitName.CAMERA_STREAM: [CommandName.CAMERA_STREAM],
    TraitName.HUMIDITY_SETTING: [CommandName.HUMIDITY_SETTING],
    TraitName.ARM_DISARM: [CommandName.ARM_DISARM],
    TraitName.VIEW_SCHEDULES: [CommandName.VIEW_SCHEDULES],
    TraitName.CANCEL_SCHEDULES: [CommandName.CANCEL_SCHEDULES],
}

COMMANDS_REQUIRING_VALUES: Set[CommandName] = {
    CommandName.OPEN_PERCENT, CommandName.CLOSE_PERCENT, CommandName.OPEN_PERCENT_ABSOLUTE,
    CommandName.CLOSE_PERCENT_ABSOLUTE, CommandName.OPEN_AMBIGUOUS_AMOUNT,
    CommandName.CLOSE_AMBIGUOUS_AMOUNT, CommandName.SET_INPUT, CommandName.OPEN_APP,
    CommandName.SET_BRIGHTNESS, CommandName.BRIGHTER_AMBIGUOUS, CommandName.DIMMER_AMBIGUOUS,
    CommandName.BRIGHTER_PERCENTAGE, CommandName.DIMMER_PERCENTAGE, CommandName.CHANGE_COLOR,
    CommandName.FAN_UP_AMBIGUOUS, CommandName.FAN_DOWN_AMBIGUOUS, CommandName.SET_FAN_SPEED,
    CommandName.SET_FAN_SPEED_PERCENTAGE, CommandName.FAN_UP_PERCENTAGE,
    CommandName.FAN_DOWN_PERCENTAGE, CommandName.COOLER_AMBIGUOUS, CommandName.WARMER_AMBIGUOUS,
    CommandName.SET_TEMPERATURE, CommandName.SET_TEMPERATURE_CELSIUS,
    CommandName.SET_TEMPERATURE_FAHRENHEIT, CommandName.SET_TEMPERATURE_MODE,
    CommandName.SET_MODE_AND_TEMPERATURE, CommandName.SET_MODE_AND_TEMPERATURE_FAHRENHEIT,
    CommandName.SET_MODE_AND_TEMPERATURE_CELSIUS, CommandName.CHANGE_RELATIVE_TEMPERATURE,
    CommandName.TOGGLE_SETTING, CommandName.BROADCAST, CommandName.SET_LIGHT_EFFECT_WITH_DURATION,
    CommandName.SET_LIGHT_EFFECT, CommandName.VOLUME_UP, CommandName.VOLUME_DOWN,
    CommandName.VOLUME_UP_PERCENTAGE, CommandName.VOLUME_DOWN_PERCENTAGE,
    CommandName.VOLUME_UP_AMBIGUOUS, CommandName.VOLUME_DOWN_AMBIGUOUS,
    CommandName.SET_VOLUME_LEVEL, CommandName.SET_VOLUME_PERCENTAGE, CommandName.SET_MODE
}

COMMANDS_NOT_REQUIRING_VALUES: Set[CommandName] = {
    CommandName.ON, CommandName.OFF, CommandName.TOGGLE_ON_OFF,
    CommandName.START, CommandName.STOP, CommandName.PAUSE, CommandName.UNPAUSE,
    CommandName.ACTIVATE_SCENE, CommandName.DEACTIVATE_SCENE,
    CommandName.NEXT_INPUT, CommandName.PREVIOUS_INPUT,
    CommandName.DOCK,
    CommandName.FIND_DEVICE, CommandName.SILENCE_RINGING,
    CommandName.MUTE, CommandName.UNMUTE,
    CommandName.LOCK, CommandName.UNLOCK,
    CommandName.CAMERA_STREAM,
    CommandName.HUMIDITY_SETTING,
    CommandName.ARM_DISARM,
    CommandName.VIEW_SCHEDULES,
    CommandName.CANCEL_SCHEDULES,
}

TRAIT_STATE_MAP: Dict[TraitName, List[StateName]] = {
    TraitName.ON_OFF: [StateName.ON],
    TraitName.BRIGHTNESS: [StateName.BRIGHTNESS],
    TraitName.COLOR_SETTING: [StateName.COLOR],
    TraitName.TEMPERATURE_SETTING: [StateName.THERMOSTAT_TEMPERATURE_SETPOINT, StateName.THERMOSTAT_MODE, StateName.THERMOSTAT_TEMPERATURE_AMBIENT],
    TraitName.FAN_SPEED: [StateName.FAN_SPEED],
    TraitName.OPEN_CLOSE: [StateName.OPEN_PERCENT],
    TraitName.VOLUME: [StateName.CURRENT_VOLUME, StateName.IS_MUTED],
    TraitName.INPUT_SELECTOR: [StateName.CURRENT_INPUT],
    TraitName.APP_SELECTOR: [StateName.CURRENT_APP],
    TraitName.LOCK_UNLOCK: [StateName.IS_LOCKED],
    TraitName.DOCK: [StateName.IS_DOCKED],
    TraitName.TRANSPORT_CONTROL: [StateName.IS_PAUSED, StateName.IS_STOPPED],
    TraitName.START_STOP: [StateName.IS_STOPPED],
    TraitName.TOGGLES: [StateName.ACTIVE_TOGGLES],
    TraitName.MODES: [StateName.CURRENT_MODES],
    TraitName.LIGHT_EFFECTS: [StateName.CURRENT_MODES],
    TraitName.LOCATOR: [StateName.IS_RINGING],
    TraitName.HUMIDITY_SETTING: [StateName.HUMIDITY_SETTING],
    TraitName.ARM_DISARM: [StateName.IS_ARMED],
    TraitName.VIEW_SCHEDULES: [StateName.SCHEDULES],
}

COMMAND_STATE_MAP: Dict[CommandName, List[StateName]] = {
    CommandName.ON: [StateName.ON],
    CommandName.OFF: [StateName.ON],
    CommandName.TOGGLE_ON_OFF: [StateName.ON],
    CommandName.SET_BRIGHTNESS: [StateName.BRIGHTNESS],
    CommandName.CHANGE_COLOR: [StateName.COLOR],
    CommandName.SET_TEMPERATURE: [StateName.THERMOSTAT_TEMPERATURE_SETPOINT],
    CommandName.SET_TEMPERATURE_CELSIUS: [StateName.THERMOSTAT_TEMPERATURE_SETPOINT],
    CommandName.SET_TEMPERATURE_FAHRENHEIT: [StateName.THERMOSTAT_TEMPERATURE_SETPOINT],
    CommandName.SET_TEMPERATURE_MODE: [StateName.THERMOSTAT_MODE],
    CommandName.SET_MODE_AND_TEMPERATURE: [
        StateName.THERMOSTAT_MODE,
        StateName.THERMOSTAT_TEMPERATURE_SETPOINT,
    ],
    CommandName.SET_MODE_AND_TEMPERATURE_FAHRENHEIT: [
        StateName.THERMOSTAT_MODE,
        StateName.THERMOSTAT_TEMPERATURE_SETPOINT,
    ],
    CommandName.SET_MODE_AND_TEMPERATURE_CELSIUS: [
        StateName.THERMOSTAT_MODE,
        StateName.THERMOSTAT_TEMPERATURE_SETPOINT,
    ],
    CommandName.CHANGE_RELATIVE_TEMPERATURE: [StateName.THERMOSTAT_TEMPERATURE_SETPOINT],
    CommandName.COOLER_AMBIGUOUS: [StateName.THERMOSTAT_TEMPERATURE_SETPOINT],
    CommandName.WARMER_AMBIGUOUS: [StateName.THERMOSTAT_TEMPERATURE_SETPOINT],
    CommandName.SET_FAN_SPEED: [StateName.FAN_SPEED],
    CommandName.SET_FAN_SPEED_PERCENTAGE: [StateName.FAN_SPEED],
    CommandName.FAN_UP_PERCENTAGE: [StateName.FAN_SPEED],
    CommandName.FAN_DOWN_PERCENTAGE: [StateName.FAN_SPEED],
    CommandName.FAN_UP_AMBIGUOUS: [StateName.FAN_SPEED],
    CommandName.FAN_DOWN_AMBIGUOUS: [StateName.FAN_SPEED],
    CommandName.OPEN: [StateName.OPEN_PERCENT],
    CommandName.CLOSE: [StateName.OPEN_PERCENT],
    CommandName.OPEN_PERCENT: [StateName.OPEN_PERCENT],
    CommandName.CLOSE_PERCENT: [StateName.OPEN_PERCENT],
    CommandName.OPEN_PERCENT_ABSOLUTE: [StateName.OPEN_PERCENT],
    CommandName.CLOSE_PERCENT_ABSOLUTE: [StateName.OPEN_PERCENT],
    CommandName.OPEN_AMBIGUOUS_AMOUNT: [StateName.OPEN_PERCENT],
    CommandName.CLOSE_AMBIGUOUS_AMOUNT: [StateName.OPEN_PERCENT],
    CommandName.SET_VOLUME_LEVEL: [StateName.CURRENT_VOLUME],
    CommandName.SET_VOLUME_PERCENTAGE: [StateName.CURRENT_VOLUME],
    CommandName.VOLUME_UP: [StateName.CURRENT_VOLUME],
    CommandName.VOLUME_DOWN: [StateName.CURRENT_VOLUME],
    CommandName.VOLUME_UP_PERCENTAGE: [StateName.CURRENT_VOLUME],
    CommandName.VOLUME_DOWN_PERCENTAGE: [StateName.CURRENT_VOLUME],
    CommandName.VOLUME_UP_AMBIGUOUS: [StateName.CURRENT_VOLUME],
    CommandName.VOLUME_DOWN_AMBIGUOUS: [StateName.CURRENT_VOLUME],
    CommandName.MUTE: [StateName.IS_MUTED],
    CommandName.UNMUTE: [StateName.IS_MUTED],
    CommandName.PAUSE: [StateName.IS_PAUSED],
    CommandName.UNPAUSE: [StateName.IS_PAUSED],
    CommandName.START: [StateName.IS_STOPPED],
    CommandName.STOP: [StateName.IS_STOPPED],
    CommandName.DOCK: [StateName.IS_DOCKED],
    CommandName.LOCK: [StateName.IS_LOCKED],
    CommandName.UNLOCK: [StateName.IS_LOCKED],
    CommandName.SET_MODE: [StateName.CURRENT_MODES],
    CommandName.SET_LIGHT_EFFECT: [StateName.CURRENT_MODES],
    CommandName.SET_LIGHT_EFFECT_WITH_DURATION: [StateName.CURRENT_MODES],
    CommandName.TOGGLE_SETTING: [StateName.ACTIVE_TOGGLES],
    CommandName.FIND_DEVICE: [StateName.IS_RINGING],
    CommandName.SILENCE_RINGING: [StateName.IS_RINGING],
    CommandName.SET_INPUT: [StateName.CURRENT_INPUT],
    CommandName.NEXT_INPUT: [StateName.CURRENT_INPUT],
    CommandName.PREVIOUS_INPUT: [StateName.CURRENT_INPUT],
    CommandName.OPEN_APP: [StateName.CURRENT_APP],
    CommandName.BRIGHTER_AMBIGUOUS: [StateName.BRIGHTNESS],
    CommandName.DIMMER_AMBIGUOUS: [StateName.BRIGHTNESS],
    CommandName.BRIGHTER_PERCENTAGE: [StateName.BRIGHTNESS],
    CommandName.DIMMER_PERCENTAGE: [StateName.BRIGHTNESS],
    CommandName.HUMIDITY_SETTING: [StateName.HUMIDITY_SETTING],
}

STATELESS_COMMANDS: Set[CommandName] = {
    CommandName.CAMERA_STREAM,
    CommandName.HUMIDITY_SETTING,
    CommandName.ARM_DISARM,
    CommandName.VIEW_SCHEDULES,
    CommandName.CANCEL_SCHEDULES,
}

STATE_VALUE_TYPE_MAP: Dict[StateName, Any] = {
    StateName.ON: StrictBool,
    StateName.IS_PAUSED: StrictBool,
    StateName.IS_STOPPED: StrictBool,
    StateName.BRIGHTNESS: StrictFloat,
    StateName.COLOR: StrictStr,
    StateName.THERMOSTAT_TEMPERATURE_SETPOINT: StrictFloat,
    StateName.THERMOSTAT_MODE: StrictStr,
    StateName.THERMOSTAT_TEMPERATURE_AMBIENT: StrictFloat,
    StateName.FAN_SPEED: StrictInt,
    StateName.OPEN_PERCENT: StrictFloat,
    StateName.CURRENT_VOLUME: StrictInt,
    StateName.IS_MUTED: StrictBool,
    StateName.CURRENT_INPUT: StrictStr,
    StateName.CURRENT_APP: StrictStr,
    StateName.IS_LOCKED: StrictBool,
    StateName.IS_DOCKED: StrictBool,
    StateName.ACTIVE_TOGGLES: dict,
    StateName.CURRENT_MODES: dict,
    StateName.IS_RINGING: StrictBool,
    StateName.SCHEDULES: list,
    StateName.HUMIDITY_SETTING: StrictInt,
    StateName.IS_ARMED: StrictBool,
}

FAN_SPEED_STRING_TO_INT_MAP: Dict[StrictStr, StrictInt] = {"low": 33, "medium": 66, "high": 100}
THERMOSTAT_STRING_TO_FLOAT_MAP: Dict[StrictStr, StrictFloat] = {"min": 16.0, "max": 30.0}

COMMAND_RANGE_RULES: Dict[CommandName, tuple] = {
    CommandName.OPEN_PERCENT: (0.0, 100.0), CommandName.CLOSE_PERCENT: (0.0, 100.0),
    CommandName.OPEN_PERCENT_ABSOLUTE: (0.0, 100.0), CommandName.CLOSE_PERCENT_ABSOLUTE: (0.0, 100.0),
    CommandName.SET_BRIGHTNESS: (0.0, 1.0), CommandName.BRIGHTER_PERCENTAGE: (0.0, 100.0),
    CommandName.DIMMER_PERCENTAGE: (0.0, 100.0), CommandName.SET_FAN_SPEED_PERCENTAGE: (0.0, 100.0),
    CommandName.FAN_UP_PERCENTAGE: (0.0, 100.0), CommandName.FAN_DOWN_PERCENTAGE: (0.0, 100.0),
    CommandName.VOLUME_UP_PERCENTAGE: (0.0, 100.0), CommandName.VOLUME_DOWN_PERCENTAGE: (0.0, 100.0),
    CommandName.SET_VOLUME_LEVEL: (0, 100), CommandName.SET_VOLUME_PERCENTAGE: (0.0, 100.0),
    CommandName.HUMIDITY_SETTING: (0, 100),
}

COMMAND_VALUE_MAP: Dict[CommandName, Any] = {
    CommandName.ON: True,
    CommandName.OFF: False,
    CommandName.MUTE: True,
    CommandName.UNMUTE: False,
    CommandName.PAUSE: True,
    CommandName.UNPAUSE: False,
    CommandName.STOP: True,
    CommandName.DOCK: True,
    CommandName.LOCK: True,
    CommandName.UNLOCK: False,
    CommandName.FIND_DEVICE: True,
    CommandName.SILENCE_RINGING: False,
    CommandName.OPEN: 100,
    CommandName.CLOSE: 0,
    CommandName.START: False,
}


# ===========================================================================
# SECTION 3: CORE DATA MODELS WITH VALIDATION
# ===========================================================================

class DeviceState(BaseModel):
    name: StateName = Field(..., description="Name of the state")
    value: Any = Field(..., description="Value of the state, validated for type correctness")

    @model_validator(mode='after')
    def validate_value_type_for_name(self) -> 'DeviceState':
        if self.name not in STATE_VALUE_TYPE_MAP:
            possible_names = [n.value for n in STATE_VALUE_TYPE_MAP.keys()]
            raise ValueError(f"State name '{self.name.value}' is not recognized. Possible values are: {possible_names}.")
        
        expected_type = STATE_VALUE_TYPE_MAP[self.name]
        
        if expected_type is dict:
            if not isinstance(self.value, dict):
                raise ValueError(f"For state '{self.name.value}', value must be a dict. Got type '{type(self.value).__name__}' instead.")
        elif expected_type is list:
            if not isinstance(self.value, list):
                raise ValueError(f"For state '{self.name.value}', value must be a list. Got type '{type(self.value).__name__}' instead.")
        else:
            # Explicit strict type checks for core pydantic strict types
            if expected_type is StrictFloat:
                if not isinstance(self.value, float):
                    raise ValueError(f"For state '{self.name.value}', value must be of type StrictFloat. Got type '{type(self.value).__name__}' instead.")
            elif expected_type is StrictInt:
                if not isinstance(self.value, int):
                    raise ValueError(f"For state '{self.name.value}', value must be of type StrictInt. Got type '{type(self.value).__name__}' instead.")
            elif expected_type is StrictStr:
                if not isinstance(self.value, str):
                    raise ValueError(f"For state '{self.name.value}', value must be of type StrictStr. Got type '{type(self.value).__name__}' instead.")
            elif expected_type is StrictBool:
                if not isinstance(self.value, bool):
                    raise ValueError(f"For state '{self.name.value}', value must be of type StrictBool. Got type '{type(self.value).__name__}' instead.")

        # Optional range validation for numeric states derived from COMMAND_RANGE_RULES
        range_by_state: Dict[StateName, tuple] = {}
        absolute_range_commands: Set[CommandName] = {
            CommandName.SET_BRIGHTNESS,
            CommandName.OPEN_PERCENT_ABSOLUTE,
            CommandName.CLOSE_PERCENT_ABSOLUTE,
            CommandName.SET_FAN_SPEED_PERCENTAGE,
            CommandName.SET_VOLUME_LEVEL,
            CommandName.SET_VOLUME_PERCENTAGE,
            CommandName.HUMIDITY_SETTING,
        }
        for cmd, rng in COMMAND_RANGE_RULES.items():
            if cmd not in absolute_range_commands:
                continue
            states = COMMAND_STATE_MAP.get(cmd, [])
            for st in states:
                if st in range_by_state:
                    lo_existing, hi_existing = range_by_state[st]
                    lo_new, hi_new = rng
                    range_by_state[st] = (min(lo_existing, lo_new), max(hi_existing, hi_new))
                else:
                    range_by_state[st] = rng
        if self.name in range_by_state:
            lo, hi = range_by_state[self.name]
            try:
                val = float(self.value)
            except Exception:
                return self
            if not (lo <= val <= hi):
                raise ValueError(f"For state '{self.name.value}', value must be between {lo} and {hi}.")
        return self

class ModesSetting(BaseModel):
    id: StrictStr = Field(..., description="ID of the mode setting")
    names: List[StrictStr] = Field(..., description="Names for the mode setting")

class TogglesModes(BaseModel):
    id: StrictStr = Field(..., description="ID of the toggle/mode")
    names: List[StrictStr] = Field(..., description="Names for the toggle/mode")
    settings: List[ModesSetting] = Field(..., description="Settings for the toggle/mode")

class DeviceInfo(BaseModel):
    id: StrictStr = Field(..., description="Device ID")
    names: List[StrictStr] = Field(..., description="Names for the device")
    types: List[DeviceType] = Field(..., description="Device type categories")
    traits: List[TraitName] = Field(..., description="Device trait names")
    room_name: StrictStr = Field(..., description="Room name")
    structure: StrictStr = Field(..., description="Structure name")
    toggles_modes: List[TogglesModes] = Field(..., description="Toggles and modes details")
    device_state: List[DeviceState] = Field(..., description="Dynamic state of the device")

    @model_validator(mode='after')
    def validate_states_against_traits(self) -> 'DeviceInfo':
        if self.traits and self.device_state:
            allowed_state_names = {s for t in self.traits if t in TRAIT_STATE_MAP for s in TRAIT_STATE_MAP[t]}
            for state in self.device_state:
                if state.name != StateName.SCHEDULES and state.name not in allowed_state_names:
                    raise ValueError(f"State '{state.name.value}' is not valid for this device's traits.")
        return self

    @model_validator(mode='after')
    def thermostat_mode_exists(self) -> 'DeviceInfo':
        if TraitName.TEMPERATURE_SETTING not in self.traits:
            return self
        # Validate mode only if toggles_modes define allowed thermostatMode settings
        thermostat_mode = next((m for m in (self.toggles_modes or []) if m.id == StateName.THERMOSTAT_MODE.value), None)
        if thermostat_mode and thermostat_mode.settings:
            all_mode_ids = [m.id for m in thermostat_mode.settings]
            thermostat_mode_state = next((s for s in self.device_state if s.name == StateName.THERMOSTAT_MODE), None)
            if thermostat_mode_state and thermostat_mode_state.value not in all_mode_ids:
                raise ValueError(f"Invalid thermostat mode. Must be one of {all_mode_ids}.")
        return self
    
    @model_validator(mode='after')
    def validate_device_modes(self) -> 'DeviceInfo':
        current_modes = next((s for s in self.device_state if s.name == StateName.CURRENT_MODES), None)
        if not current_modes:
            return self
        # The keys of currentModes must be defined in toggles_modes ids
        valid_mode_ids = [m.id for m in self.toggles_modes]
        if not all(mode_id in valid_mode_ids for mode_id in current_modes.value):
            raise ValueError(f"Invalid mode. Must be one of {valid_mode_ids}.")
        return self

class MutateTraitCommand(BaseModel):
    trait: TraitName = Field(..., description="Trait name")
    command_names: List[CommandName] = Field(..., description="Command names")
    command_values: Optional[List[StrictStr]] = Field(None, description="Command values")

    @model_validator(mode='after')
    def validate_commands_for_trait(self) -> 'MutateTraitCommand':
        if not self.trait or not self.command_names:
            return self
        valid_commands_for_trait = TRAIT_COMMAND_MAP.get(self.trait, [])
        for command in self.command_names:
            if command not in valid_commands_for_trait:
                raise ValueError(f"Command '{command.value}' is not valid for trait '{self.trait.value}'.")
        # Defer value validation and transformation entirely to the engine layer
        return self

# ===========================================================================
# SECTION 4: API-LEVEL PARAMETER & RESULT MODELS
# ===========================================================================

class GetDevicesParams(BaseModel):
    trait_hints: Optional[List[TraitName]] = Field(None, description="Optional list of traits to filter for.")
    type_hints: Optional[List[DeviceType]] = Field(None, description="Optional list of device_types to filter for.")
    include_state: Optional[StrictBool] = Field(False, description="Whether to include the dynamic state of the devices.")

class DevicesParams(BaseModel):
    traits: Optional[List[TraitName]] = Field(None, description="Optional list of traits to filter for.")
    include_state: Optional[StrictBool] = Field(False, description="Whether to include the dynamic state of the devices.")

class MutateParams(BaseModel):
    devices: List[StrictStr] = Field(...)
    traits: List[TraitName]
    commands: List[CommandName]
    values: List[StrictStr]
    time_of_day: Optional[StrictStr] = None
    date: Optional[StrictStr] = None
    am_pm_or_unknown: Optional[StrictStr] = None
    duration: Optional[StrictStr] = None

class RunParams(BaseModel):
    devices: List[StrictStr] = Field(..., min_length=1, description="Unique identifiers of smart home devices.")
    op: CommandName = Field(..., description="Name of the operation to run.")
    values: Optional[List[StrictStr]] = Field(None, description="Optional list of values for the operation.")
    time_of_day: Optional[StrictStr] = Field(None, description="Time to execute the operation, e.g., 'HH:MM:SS'")
    date: Optional[StrictStr] = Field(None, description="Date to execute the operation, e.g., 'YYYY-MM-DD'")
    am_pm_or_unknown: Optional[StrictStr] = Field(None, description="Whether time_of_day is AM or PM or UNKNOWN")
    delay: Optional[StrictStr] = Field(None, description="How long to wait before executing, e.g., '5s', '20m', '1h'")
    duration: Optional[StrictStr] = Field(None, description="How long the operation should last, e.g., '5s', '20m', '1h'")

class ScheduleInfo(BaseModel):
    start_date: Optional[StrictStr] = Field(None, description="Start date")
    start_time_of_day: Optional[StrictStr] = Field(None, description="Start time of day")
    start_am_pm_or_unknown: Optional[StrictStr] = Field(None, description="AM/PM/Unknown")
    duration: Optional[StrictStr] = Field(None, description="Duration")

class MutateTraitCommands(BaseModel):
    device_ids: List[StrictStr] = Field(..., description="Device IDs")
    commands: List[MutateTraitCommand] = Field(..., description="Trait mutating commands")
    schedule_info: Optional[ScheduleInfo] = Field(None, description="Schedule information")

class DeviceExecutionResult(BaseModel):
    device_id: Optional[StrictStr] = Field(None, description="Device ID")
    result: Optional[ExecutionResult] = Field(None, description="Execution result")

class DeviceExecutionResults(BaseModel):
    text_to_speech: Optional[StrictStr] = Field(None, description="Text to speech output")
    results: Optional[List[DeviceExecutionResult]] = Field(None, description="List of device execution results")

class MutateTraitResult(BaseModel):
    action_card_content_passthrough: Optional[StrictStr] = Field(None, description="Action card content passthrough")
    card_id: Optional[StrictStr] = Field(None, description="Card ID")
    commands: Optional[MutateTraitCommands] = Field(None, description="Trait mutation commands")
    result: Optional[MutateTraitResultStatus] = Field(None, description="Result of the mutation")
    device_execution_results: Optional[Union[StrictStr, DeviceExecutionResults]] = Field(None, description="Device execution results")

class GenerateHomeAutomationResult(BaseModel):
    automation_script_code: Optional[StrictStr] = Field(None, description="Automation script code")
    user_instructions: Optional[StrictStr] = Field(None, description="User instructions")

class GenerateHomeAutomationParams(BaseModel):
    query: str = Field(...)
    home_name: Optional[str] = Field(None)

class SearchHomeEventsResult(BaseModel):
    search_home_events_response: Optional[StrictStr] = Field(None, description="Search home events response")
    camera_clip_urls: Optional[List[StrictStr]] = Field(None, description="Camera clip URLs")

class SearchHomeEventsParams(BaseModel):
    query: str = Field(...)
    home_name: Optional[str] = Field(None)

class ApiHints(BaseModel):
    general_instructions: Optional[StrictStr] = Field(None, description="API hints")

class GetDevicesResult(BaseModel):
    devices: Optional[List[DeviceInfo]] = Field(None, description="List of devices")
    api_hints: Optional[ApiHints] = Field(None, description="API hints")

class CancelSchedulesParams(BaseModel):
    devices: Optional[List[str]] = Field(None)

class ScheduledActionResult(BaseModel):
    tts: Optional[StrictStr] = Field(None, description="Text to speech")
    operation_type: Optional[StrictStr] = Field(None, description="Operation type")
    success: Optional[StrictBool] = Field(None, description="Success flag")

class SeeDevicesResult(BaseModel):
    devices_info: Optional[StrictStr] = Field(None, description="Devices info")

class SeeDevicesParams(BaseModel):
    state: Optional[bool] = Field(None)

class ViewSchedulesParams(BaseModel):
    devices: Optional[List[str]] = Field(None)


class APIName(str, Enum):
    """The name of the API."""
    GET_ALL_DEVICES = "get_all_devices"
    GET_DEVICES = "get_devices"
    DEVICES = "devices"
    DETAILS = "details"
    SEE_DEVICES = "see_devices"
    MUTATE_TRAITS = "mutate_traits"
    MUTATE = "mutate"
    RUN = "run"
    VIEW_SCHEDULES = "view_schedules"
    CANCEL_SCHEDULES = "cancel_schedules"
    GENERATE_HOME_AUTOMATION = "generate_home_automation"
    SEARCH_HOME_EVENTS = "search_home_events"


class Action(BaseModel):
    """An action record."""
    action_type: APIName
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat())


class DetailsResult(BaseModel):
    devices_info: Optional[StrictStr] = Field(None, description="Devices info")

class DetailsParams(BaseModel):
    devices: List[str] = Field(...)

# ===========================================================================
# SECTION 5: HOME GRAPH DATABASE SCHEMA
# ===========================================================================

class Room(BaseModel):
    name: StrictStr = Field(..., description="Name of the room")
    devices: Dict[DeviceType, List[DeviceInfo]] = Field(..., description="Devices in the room, keyed by DeviceType")

class Structure(BaseModel):
    name: StrictStr = Field(..., description="Name of the structure")
    rooms: Dict[StrictStr, Room] = Field(..., description="Rooms in the structure, keyed by room name")

class GoogleHomeDB(BaseModel):
    structures: Dict[StrictStr, Structure] = Field(..., description="All structures, keyed by structure name")
    actions: List['Action'] = Field(default_factory=list)
