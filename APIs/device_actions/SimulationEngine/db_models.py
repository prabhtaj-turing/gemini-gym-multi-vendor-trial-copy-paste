from typing import Dict, List, Optional
import datetime as dt
from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------
# Enum Types
# ---------------------------

class CameraType(str, Enum):
    """Which camera to use."""
    FRONT = "FRONT"
    REAR = "REAR"
    DEFAULT = "DEFAULT"


class CameraOperation(str, Enum):
    """Which camera operation to select."""
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"


class CameraMode(str, Enum):
    """The mode the camera should use when taking a picture."""
    DEFAULT = "DEFAULT"
    PORTRAIT = "PORTRAIT"


class AppType(str, Enum):
    """The type of application."""
    BROWSER = "BROWSER"
    CAMERA = "CAMERA"
    HOME_SCREEN = "HOME_SCREEN"
    PHOTOS = "PHOTOS"
    SHOPPING = "SHOPPING"
    MAPS = "MAPS"
    ASSISTANT = "ASSISTANT"


# ---------------------------
# Internal Storage Models
# ---------------------------

class AppInfoStorage(BaseModel):
    """Metadata of an application installed on the device."""
    name: str = Field(
        ..., 
        description="User-visible application name as shown on the device.",
        min_length=1,
        max_length=200,
    )
    app_package_name: str = Field(
        ..., 
        description="Application package name (e.g., 'com.android.chrome').",
        min_length=3,
        max_length=255,
    )
    # Accept free-form types from vendors; no Enum validation here to allow flexibility
    app_type: str = Field(
        ..., 
        description="Application category/type as provided by vendor (e.g., 'BROWSER', 'MAPS').",
        min_length=1,
        max_length=100,
    )
    is_default: bool = Field(
        False,
        description="Whether this app is the default handler for its category on the device.",
    )
    is_system_app: bool = Field(
        False,
        description="Whether the app is preinstalled as a system application.",
    )


class CameraStateStorage(BaseModel):
    """Represents the state of the device's camera."""
    is_open: bool = Field(
        False,
        description="Whether the camera application is currently open.",
    )
    type: Optional[CameraType] = Field(
        None,
        description="Selected physical camera: FRONT, REAR, or DEFAULT.",
    )
    operation: Optional[CameraOperation] = Field(
        None,
        description="Functional mode of the camera: PHOTO or VIDEO.",
    )


class BrowserStateStorage(BaseModel):
    """Represents the state of the device's browser."""
    is_open: bool = Field(
        False,
        description="Whether a browser is currently open.",
    )
    current_url: Optional[str] = Field(
        None,
        description="Currently loaded URL in the browser (scheme may be omitted if not provided by the user).",
        min_length=1,
    )


class MediaStorage(BaseModel):
    """Represents a media file entry (photo/video/screenshot)."""
    name: str = Field(
        ..., 
        description="Filename or label for the media item.",
        min_length=1,
        max_length=200,
    )
    created_at: dt.datetime = Field(
        ..., 
        description="ISO 8601 timestamp when the media was created (e.g., '2023-10-27T10:00:00Z').",
    )


class PhoneStateStorage(BaseModel):
    """Represents the state of the phone."""
    flashlight_on: bool = Field(
        False,
        description="Whether the device flashlight is currently turned on.",
    )
    installed_apps: List[AppInfoStorage] = Field(
        default_factory=list,
        description="Flattened list of applications installed on the device.",
    )
    camera: CameraStateStorage = Field(
        default_factory=CameraStateStorage,
        description="Current camera state (open/closed, selected camera and operation).",
    )
    browser: BrowserStateStorage = Field(
        default_factory=BrowserStateStorage,
        description="Current browser state (open/closed and current URL).",
    )
    photos: List[MediaStorage] = Field(
        default_factory=list,
        description="Photos captured on the device.",
    )
    videos: List[MediaStorage] = Field(
        default_factory=list,
        description="Videos recorded on the device.",
    )
    screenshots: List[MediaStorage] = Field(
        default_factory=list,
        description="Screenshots captured on the device.",
    )
    currently_open_app_package: Optional[str] = Field(
        None,
        description="Package name of the currently open app.",
        min_length=1,
        max_length=255,
    )
    last_ring_timestamp: Optional[dt.datetime] = Field(
        None,
        description="ISO 8601 timestamp of the last ring_phone action.",
    )
    last_shutdown_timestamp: Optional[dt.datetime] = Field(
        None,
        description="ISO 8601 timestamp when the device was powered off.",
    )
    last_restart_timestamp: Optional[dt.datetime] = Field(
        None,
        description="ISO 8601 timestamp when the device was restarted.",
    )
    is_on: bool = Field(
        True,
        description="Whether the device is currently powered on.",
    )


# ---------------------------
# Root Database Model
# ---------------------------

class DeviceActionsDB(BaseModel):
    """Root model that validates the entire device actions database structure."""
    phone_state: PhoneStateStorage = Field(
        default_factory=PhoneStateStorage,
        description="Current device state including apps, camera, browser, media, and power.",
    )

    # Some DBs include an actions list for auditing; keep permissive typing (list of any dict)
    # Using a generic list keeps compatibility with empty list and future action shapes
    actions: List[dict] = Field(
        default_factory=list,
        description="Chronological log of executed actions for auditing; free-form item structure.",
    )

    class Config:
        str_strip_whitespace = True


