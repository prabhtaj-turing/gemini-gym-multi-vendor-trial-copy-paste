import json
import sys
import re
from pathlib import Path
from datetime import datetime, timezone
from .helpers import validate_with_default_schema

BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "device_setting"

def normalize_timestamp(timestamp_str: str) -> str:
    """
    Normalize timestamp to ISO 8601 format with Z suffix.
    
    Args:
        timestamp_str: Timestamp string in various formats
        
    Returns:
        Normalized timestamp string in ISO 8601 format with Z suffix
    """
    if not timestamp_str:
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    # If already in ISO format with Z, return as is
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$', timestamp_str):
        return timestamp_str
    
    # Try to parse and normalize
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        normalized = dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Validate the result matches expected ISO format
        if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$', normalized):
            return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        return normalized
    except ValueError:
        # Return current timestamp if parsing fails
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def transform_device_settings(settings_data: dict) -> dict:
    """
    Transform and validate device settings data.
    
    Args:
        settings_data: Raw device settings data
        
    Returns:
        Transformed and validated device settings
    """
    if not settings_data:
        return {}
    
    # Valid device settings based on GetableDeviceSettingType enum
    VALID_DEVICE_SETTINGS = {
        "AIRPLANE_MODE", "ALARM_VOLUME", "AUTO_ROTATE", "BATTERY", "BATTERY_SAVER",
        "BLUETOOTH", "BRIGHTNESS", "CALL_VOLUME", "DO_NOT_DISTURB", "FLASHLIGHT",
        "HOT_SPOT", "MEDIA_VOLUME", "NETWORK", "NFC", "NIGHT_MODE", 
        "NOTIFICATION_VOLUME", "RING_VOLUME", "TALK_BACK", "VOLUME", "VIBRATION", "WIFI"
    }
    
    transformed = settings_data.copy()
    
    # Transform settings if they exist
    if "settings" in transformed:
        filtered_settings = {}
        for setting_name, setting_value in transformed["settings"].items():
            # Only process valid settings
            if setting_name in VALID_DEVICE_SETTINGS and isinstance(setting_value, dict):
                # Normalize percentage values
                if "percentage_value" in setting_value:
                    pct = setting_value["percentage_value"]
                    if pct is not None:
                        # Clamp percentage values to valid range [0, 100] for volume settings
                        # (0 is valid for muting)
                        if pct > 100:
                            setting_value["percentage_value"] = 100
                        elif pct < 0:
                            setting_value["percentage_value"] = 0
                
                # Normalize on/off values
                if "on_or_off" in setting_value:
                    val = setting_value["on_or_off"]
                    if val is not None:
                        # Convert to lowercase and validate
                        val_lower = str(val).lower()
                        if val_lower in ["on", "true", "1", "yes"]:
                            setting_value["on_or_off"] = "on"
                        elif val_lower in ["off", "false", "0", "no"]:
                            setting_value["on_or_off"] = "off"
                        else:
                            # Set invalid values to "off" as default
                            setting_value["on_or_off"] = "off"
                
                # Normalize timestamps
                if "last_updated" in setting_value:
                    setting_value["last_updated"] = normalize_timestamp(setting_value["last_updated"])
                
                # Add to filtered settings
                filtered_settings[setting_name] = setting_value
        
        transformed["settings"] = filtered_settings
    
    return transformed

def transform_installed_apps(apps_data: dict) -> dict:
    """
    Transform and validate installed apps data.
    
    Args:
        apps_data: Raw installed apps data
        
    Returns:
        Transformed and validated installed apps
    """
    if not apps_data:
        return {}
    
    transformed = apps_data.copy()
    
    # Transform apps if they exist
    if "apps" in transformed:
        for app_name, app_data in transformed["apps"].items():
            if isinstance(app_data, dict) and "notifications" in app_data:
                notifications = app_data["notifications"]
                if isinstance(notifications, dict):
                    # Normalize notification values
                    if "value" in notifications:
                        val = notifications["value"]
                        if val is not None:
                            # Convert to lowercase and validate
                            val_lower = str(val).lower()
                            if val_lower in ["on", "true", "1", "yes"]:
                                notifications["value"] = "on"
                            elif val_lower in ["off", "false", "0", "no"]:
                                notifications["value"] = "off"
                            else:
                                # Set invalid values to "off" as default
                                notifications["value"] = "off"
                    
                    # Normalize timestamps
                    if "last_updated" in notifications:
                        notifications["last_updated"] = normalize_timestamp(notifications["last_updated"])
    
    return transformed

def transform_device_insights(insights_data: dict) -> dict:
    """
    Transform and validate device insights data.
    
    Args:
        insights_data: Raw device insights data
        
    Returns:
        Transformed and validated device insights
    """
    if not insights_data:
        return {}
    
    # Valid device insights based on DeviceStateType enum
    VALID_DEVICE_INSIGHTS = {"BATTERY", "STORAGE", "UNCATEGORIZED"}
    
    transformed = insights_data.copy()
    
    # Transform insights if they exist
    if "insights" in transformed:
        filtered_insights = {}
        for insight_name, insight_data in transformed["insights"].items():
            # Only process valid insights
            if insight_name in VALID_DEVICE_INSIGHTS and isinstance(insight_data, dict):
                # Normalize percentage values
                if "percentage" in insight_data:
                    pct = insight_data["percentage"]
                    if pct is not None:
                        # Clamp percentage values to valid range [0, 100]
                        if pct > 100:
                            insight_data["percentage"] = 100
                        elif pct < 0:
                            insight_data["percentage"] = 0
                
                # Normalize charging status
                if "charging_status" in insight_data:
                    status = insight_data["charging_status"]
                    if status is not None:
                        status_lower = str(status).lower().replace(" ", "_")
                        if status_lower in ["charging", "charge", "yes"]:
                            insight_data["charging_status"] = "charging"
                        elif status_lower in ["not_charging", "notcharging", "no", "discharging"]:
                            insight_data["charging_status"] = "not_charging"
                        else:
                            # Set invalid values to "not_charging" as default
                            insight_data["charging_status"] = "not_charging"
                
                # Normalize timestamps
                if "last_updated" in insight_data:
                    insight_data["last_updated"] = normalize_timestamp(insight_data["last_updated"])
                
                # Add to filtered insights
                filtered_insights[insight_name] = insight_data
        
        transformed["insights"] = filtered_insights
    
    return transformed


def port_device_setting_db(source_json_str: str, file_path: str | None = None):
    """
    Port device settings JSON to match default DB structure.
    Returns the ported dict (pure function, no file writes).
    """

    default_db_path = Path("DBs/DeviceSettingDefaultDB.json")

    # Load default DB or use fallback
    if default_db_path.exists():
        with default_db_path.open() as f:
            default_db = json.load(f)
    else:
        # Create a minimal default structure
        default_db = {
            "device_settings": {},
            "installed_apps": {},
            "device_insights": {}
        }

    # Parse source JSON
    try:
        source_db = json.loads(source_json_str, strict=False)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"

    # Transform and map sections from source to default DB
    default_db['device_settings'] = transform_device_settings(source_db.get('device_settings', {}))
    default_db['installed_apps'] = transform_installed_apps(source_db.get('installed_apps', {}))
    default_db['device_insights'] = transform_device_insights(source_db.get('device_insights', {}))
    
    # Handle device_id consistency and defaults
    default_device_id = "google_pixel_9_a"
    
    # Get device_id from device_settings as the primary source, or use default
    primary_device_id = default_db['device_settings'].get('device_id', default_device_id)
    
    # Ensure all sections have the same device_id
    default_db['device_settings']['device_id'] = primary_device_id
    default_db['installed_apps']['device_id'] = primary_device_id
    default_db['device_insights']['device_id'] = primary_device_id
    
    # Run the default schema validation
    status, message = validate_with_default_schema("device_setting.SimulationEngine.models", default_db)
    
    if file_path and status:
        out_path = Path(file_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(default_db, indent=2), encoding="utf-8")
        print(f"Output written to: {out_path.resolve()}")
    
    if not status:
        return None, message
    return default_db, message

if __name__ == "__main__":
    if not sys.stdin.isatty():
        # read raw JSON strings from stdin
        raw_input = sys.stdin.read().strip()
        data = json.loads(raw_input)
        raw_device_settings = data.get("device_settings", "{}")
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:
        # fallback to local file
        device_path = BASE_PATH / "vendor_device_setting.json"
        raw_device_settings = device_path.read_text()
        output_path = BASE_PATH / "ported_final_device_setting.json"

    # call the porting function
    ported_device_db = port_device_setting_db(raw_device_settings, output_path)