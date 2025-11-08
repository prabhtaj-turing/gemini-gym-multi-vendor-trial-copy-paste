"""
Pydantic models for device_setting API
"""

from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, timezone

from device_setting.SimulationEngine.enums import VolumeSettingType, ActionType, ToggleableDeviceSettingType

# Constants
ISO_TIMESTAMP_DESC = "ISO timestamp of last update"
DEVICE_ID_DESC = "Unique device identifier"
TIMEZONE_SUFFIX = "+00:00"
TIMESTAMP_ERROR_MSG = "last_updated must be a valid ISO timestamp"


class VolumeSettingMapping(BaseModel):
    """Mapping between VolumeSettingType enum and database keys."""
    ALARM: str = "ALARM_VOLUME"
    CALL: str = "CALL_VOLUME"
    MEDIA: str = "MEDIA_VOLUME"
    NOTIFICATION: str = "NOTIFICATION_VOLUME"
    RING: str = "RING_VOLUME"
    UNSPECIFIED: Optional[str] = None
    
    def get_database_key(self, setting_type: VolumeSettingType) -> Optional[str]:
        """Get the database key for a given volume setting type."""
        return getattr(self, setting_type.value, None)
    
    def get_all_volume_keys(self) -> list[str]:
        """Get all volume database keys."""
        return [self.ALARM, self.CALL, self.MEDIA, self.NOTIFICATION, self.RING, "VOLUME"]


class SettingInfo(BaseModel):
    """Detailed information about a specific device setting."""
    setting_type: str = Field(..., description="The type of the setting.")
    percentage_value: Optional[int] = Field(None, description="If the setting type can be adjusted, return the current percentage value of a device setting between [0, 100].")
    on_or_off: Optional[str] = Field(None, description="If the setting type can be toggled, return the current toggled value.")
    action_card_content_passthrough: Optional[str] = Field(None, description="Action card content for UI display.")
    card_id: Optional[str] = Field(None, description="Card identifier for UI components.")

    @field_validator('percentage_value')
    @classmethod
    def validate_percentage(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('percentage_value must be between 0 and 100')
        return v

    @model_validator(mode='after')
    def validate_and_set_on_or_off(self):
        """Validate on_or_off field and set default 'off' value for toggleable settings when None."""
        # Validate that on_or_off is either 'on', 'off', or None
        if self.on_or_off is not None and self.on_or_off not in ['on', 'off']:
            raise ValueError('on_or_off must be either "on" or "off"')
        
        # Set default 'off' value for toggleable settings when on_or_off is None
        if (self.on_or_off is None and 
            self.setting_type in [e.value for e in ToggleableDeviceSettingType]):
            self.on_or_off = "off"
        
        return self


class ActionSummary(BaseModel):
    """The description of the tool action result."""
    result: str = Field(..., description="Result message of the action.")
    action_card_content_passthrough: Optional[str] = Field(None, description="Action card content for UI display.")
    card_id: Optional[str] = Field(None, description="Card identifier for UI components.")


class Action(BaseModel):
    """An action record."""
    action_type: ActionType
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    metadata: Dict[str, Any] = {}
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ---------------------------
# Database Storage Models
# ---------------------------

class DeviceSettingStorage(BaseModel):
    """Storage model for individual device settings"""
    on_or_off: Optional[str] = Field(None, description="On/off setting value")
    percentage_value: Optional[int] = Field(None, description="Percentage value for the setting")
    last_updated: str = Field(..., description=ISO_TIMESTAMP_DESC)
    
    @field_validator('percentage_value')
    @classmethod
    def validate_percentage(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('percentage_value must be between 0 and 100')
        return v
    
    @field_validator('on_or_off')
    @classmethod
    def validate_on_off(cls, v):
        if v is not None and v.upper() not in ['ON', 'OFF']:
            raise ValueError('on_or_off must be either "ON" or "OFF"')
        return v.upper() if v else v
    
    @field_validator('last_updated')
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', TIMEZONE_SUFFIX))
            return v
        except ValueError as exc:
            raise ValueError(TIMESTAMP_ERROR_MSG) from exc


class DeviceSettingsStorage(BaseModel):
    """Storage model for device settings container"""
    device_id: str = Field(..., description=DEVICE_ID_DESC)
    settings: Dict[str, DeviceSettingStorage] = Field(default_factory=dict, description="Device settings by setting type")


class AppNotificationSetting(BaseModel):
    """Storage model for app notification settings"""
    value: str = Field(..., description="Notification setting value (on/off)")
    last_updated: str = Field(..., description=ISO_TIMESTAMP_DESC)
    
    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if v not in ['on', 'off']:
            raise ValueError('value must be either "on" or "off"')
        return v
    
    @field_validator('last_updated')
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', TIMEZONE_SUFFIX))
            return v
        except ValueError as exc:
            raise ValueError(TIMESTAMP_ERROR_MSG) from exc


class AppSettings(BaseModel):
    """Storage model for app settings"""
    notifications: AppNotificationSetting = Field(..., description="Notification settings for this app")


class InstalledAppsStorage(BaseModel):
    """Storage model for installed apps container"""
    device_id: str = Field(..., description=DEVICE_ID_DESC)
    apps: Dict[str, AppSettings] = Field(default_factory=dict, description="App settings by app name")


class BatteryInsight(BaseModel):
    """Storage model for battery insights"""
    percentage: int = Field(..., description="Battery percentage")
    charging_status: str = Field(..., description="Charging status")
    estimated_time_remaining: str = Field(..., description="Estimated time remaining")
    health: str = Field(..., description="Battery health status")
    temperature: str = Field(..., description="Battery temperature status")
    last_updated: str = Field(..., description=ISO_TIMESTAMP_DESC)
    
    @field_validator('percentage')
    @classmethod
    def validate_percentage(cls, v):
        if v < 0 or v > 100:
            raise ValueError('percentage must be between 0 and 100')
        return v
    
    @field_validator('charging_status')
    @classmethod
    def validate_charging_status(cls, v):
        if v not in ['charging', 'not_charging']:
            raise ValueError('charging_status must be either "charging" or "not_charging"')
        return v
    
    @field_validator('last_updated')
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', TIMEZONE_SUFFIX))
            return v
        except ValueError as exc:
            raise ValueError(TIMESTAMP_ERROR_MSG) from exc


class StorageInsight(BaseModel):
    """Storage model for storage insights"""
    total_gb: int = Field(..., description="Total storage in GB")
    used_gb: int = Field(..., description="Used storage in GB")
    available_gb: int = Field(..., description="Available storage in GB")
    usage_breakdown: Dict[str, int] = Field(..., description="Storage usage breakdown by category")
    last_updated: str = Field(..., description=ISO_TIMESTAMP_DESC)
    
    @field_validator('total_gb', 'used_gb', 'available_gb')
    @classmethod
    def validate_storage_values(cls, v):
        if v < 0:
            raise ValueError('Storage values must be non-negative')
        return v
    
    @field_validator('last_updated')
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', TIMEZONE_SUFFIX))
            return v
        except ValueError as exc:
            raise ValueError(TIMESTAMP_ERROR_MSG) from exc


class UncategorizedInsight(BaseModel):
    """Storage model for uncategorized insights"""
    network_signal: str = Field(..., description="Network signal quality")
    wifi_strength: int = Field(..., description="WiFi signal strength")
    cellular_signal: int = Field(..., description="Cellular signal strength")
    memory_usage: int = Field(..., description="Memory usage percentage")
    cpu_usage: int = Field(..., description="CPU usage percentage")
    last_updated: str = Field(..., description=ISO_TIMESTAMP_DESC)
    
    @field_validator('wifi_strength', 'cellular_signal', 'memory_usage', 'cpu_usage')
    @classmethod
    def validate_percentage_values(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Percentage values must be between 0 and 100')
        return v
    
    @field_validator('last_updated')
    @classmethod
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', TIMEZONE_SUFFIX))
            return v
        except ValueError as exc:
            raise ValueError(TIMESTAMP_ERROR_MSG) from exc


class DeviceInsightsStorage(BaseModel):
    """Storage model for device insights container"""
    device_id: str = Field(..., description=DEVICE_ID_DESC)
    insights: Dict[str, Union[BatteryInsight, StorageInsight, UncategorizedInsight]] = Field(
        default_factory=dict, 
        description="Device insights by insight type"
    )


# ---------------------------
# Root Database Model
# ---------------------------

class DeviceSettingDB(BaseModel):
    """Validates entire device setting database structure"""
    device_settings: DeviceSettingsStorage = Field(..., description="Device settings configuration")
    installed_apps: InstalledAppsStorage = Field(..., description="Installed apps and their settings")
    device_insights: DeviceInsightsStorage = Field(..., description="Device insights and analytics")
    
    class Config:
        str_strip_whitespace = True


# Global instance for volume setting mappings
volume_mapping = VolumeSettingMapping() 