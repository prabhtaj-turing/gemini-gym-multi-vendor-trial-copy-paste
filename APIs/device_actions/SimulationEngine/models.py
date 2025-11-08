from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from enum import Enum
import uuid
from datetime import datetime, timezone
import re

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


class OpenCameraInput(BaseModel):
    camera_type: Optional[CameraType] = None
    camera_operation: Optional[CameraOperation] = None
    camera_mode: Optional[CameraMode] = None

class TakePhotoInput(BaseModel):
    camera_type: Optional[CameraType] = None
    self_timer_delay: Optional[str] = None
    camera_mode: Optional[CameraMode] = None

class RecordVideoInput(BaseModel):
    camera_type: Optional[CameraType] = None
    self_timer_delay: Optional[str] = None
    video_duration: Optional[str] = None

class OpenAppInput(BaseModel):
    app_name: str
    app_package_name: Optional[str] = None
    extras: Optional[str] = None

    @field_validator('app_package_name')
    def validate_package_name(cls, v):
        if v and not re.match(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$', v):
            raise ValueError('Invalid package name format. It must be in the format "com.example.app".')

        return v

class OpenUrlInput(BaseModel):
    url: str
    website_name: Optional[str] = None

class OpenWebsearchInput(BaseModel):
    query: str

class AppInfo(BaseModel):
    """Metadata of an application."""
    name: str
    app_package_name: str
    # Accept free-form types from vendors; no Enum validation
    app_type: str
    is_default: bool = False
    is_system_app: bool = False

class CameraState(BaseModel):
    """Represents the state of the device's camera."""
    is_open: bool = False
    type: Optional[CameraType] = None
    operation: Optional[CameraOperation] = None

class Media(BaseModel):
    """Represents a media file."""
    name: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BrowserState(BaseModel):
    """Represents the state of the device's browser."""
    is_open: bool = False
    current_url: Optional[str] = None

class PhoneState(BaseModel):
    """Represents the state of the phone."""
    flashlight_on: bool = False
    installed_apps: List[AppInfo] = [
        AppInfo(name="Google Maps", app_package_name="com.google.android.apps.maps", app_type=AppType.MAPS),
        AppInfo(name="Amazon Shopping", app_package_name="com.amazon.mShop.android.shopping", app_type=AppType.SHOPPING),
        AppInfo(name="Pixel Screenshots", app_package_name="com.google.android.apps.photosgo", app_type=AppType.PHOTOS),
        AppInfo(name="Amazon Alexa", app_package_name="com.amazon.dee.app", app_type=AppType.ASSISTANT),
        AppInfo(name="Google Photos", app_package_name="com.google.android.apps.photos", app_type=AppType.PHOTOS),
        AppInfo(name="Camera", app_package_name="com.google.android.camera", app_type=AppType.CAMERA, is_system_app=True, is_default=True),
        AppInfo(name="Chrome", app_package_name="com.android.chrome", app_type=AppType.BROWSER, is_system_app=True, is_default=True),
        AppInfo(name="Home Screen", app_package_name="com.google.android.apps.nexuslauncher", app_type=AppType.HOME_SCREEN, is_system_app=True),
    ]
    camera: CameraState = CameraState()
    browser: BrowserState = BrowserState()
    photos: List[Media] = []
    videos: List[Media] = []
    screenshots: List[Media] = []
    currently_open_app_package: Optional[str] = None
    last_ring_timestamp: Optional[str] = None
    last_shutdown_timestamp: Optional[str] = None
    last_restart_timestamp: Optional[str] = None
    is_on: bool = True  

class ActionSummary(BaseModel):
    """The description of the tool action result"""
    result: str
    action_card_content_passthrough: Optional[str] = Field(None, json_schema_extra={"x-google-bard-model-visible": False})
    card_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class DeviceActionsDB(BaseModel):
    """The database for device actions."""
    phone_state: PhoneState = PhoneState()
