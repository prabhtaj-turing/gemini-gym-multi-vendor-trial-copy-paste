from typing import Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


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


# ---------------------------
# Internal Storage Models
# ---------------------------

class DeviceStateStorage(BaseModel):
    """Internal storage model for the state of a device attribute."""
    name: str = Field(..., description="The name of the device state attribute.")
    value: Any = Field(..., description="The current value of the device state attribute.")

class SettingStorage(BaseModel):
    """Internal storage model for a setting within a toggle or mode."""
    id: str = Field(..., description="The unique identifier for the setting.")
    names: List[str] = Field(..., description="The list of names for the setting.")

class ToggleModeStorage(BaseModel):
    """Internal storage model for a toggle or mode available on a device."""
    id: str = Field(..., description="The unique identifier for the toggle or mode.")
    names: List[str] = Field(..., description="The list of names for the toggle or mode.")
    settings: List[SettingStorage] = Field(..., description="A list of available settings for this toggle or mode.")

class DeviceStorage(BaseModel):
    """Internal storage model for a smart home device."""
    id: str = Field(..., description="The unique identifier for the device.", min_length=1)
    names: List[str] = Field(..., description="A list of names for the device.")
    types: List[str] = Field(..., description="The types of the device (e.g., 'LIGHT', 'TV').")
    traits: List[str] = Field(..., description="The traits supported by the device (e.g., 'OnOff', 'Brightness').")
    room_name: str = Field(..., description="The name of the room the device is in.")
    structure: str = Field(..., description="The name of the structure the device belongs to.")
    toggles_modes: List[ToggleModeStorage] = Field(..., description="A list of toggles and modes for the device.")
    device_state: List[DeviceStateStorage] = Field(..., description="The current state of the device's attributes.")

class RoomStorage(BaseModel):
    """Internal storage model for a room in a structure."""
    name: str = Field(..., description="The name of the room.")
    devices: Dict[str, List[DeviceStorage]] = Field(..., description="A dictionary of devices in the room, keyed by device type.")

class StructureStorage(BaseModel):
    """Internal storage model for a home structure."""
    name: str = Field(..., description="The name of the structure.")
    rooms: Dict[str, RoomStorage] = Field(..., description="A dictionary of rooms in the structure, keyed by room name.")

class Action(BaseModel):
    """An action record."""
    action_type: APIName = Field(..., description="The type of action performed")
    inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters for the action"
    )
    outputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Output results from the action"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="When the action occurred",
    )

# ---------------------------
# Root Database Model
# ---------------------------

class GoogleHomeDB(BaseModel):
    """Root model that validates the entire Google Home database structure."""
    structures: Dict[str, StructureStorage] = Field(
        default_factory=dict,
        description="A dictionary of home structures, keyed by structure name."
    )
    actions: List[Action] = Field(
        default_factory=list,
        description="A list of actions that have been performed."
    )

    class Config:
        str_strip_whitespace = True
