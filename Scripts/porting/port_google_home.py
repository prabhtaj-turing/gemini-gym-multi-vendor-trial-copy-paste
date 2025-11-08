import json
import sys
from pathlib import Path
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

from google_home.SimulationEngine.models import GoogleHomeDB

BASE_PATH = Path(__file__).resolve().parent / "SampleDBs" / "google_home"

def port_google_home(raw_data: str, file_path: str | None = None):
    """
    Port raw Google Home JSON into the default schema and validate.

    Args:
        raw_data (str): Raw JSON string of vendor Google Home data.
        file_path (str | None): Optional path to save the ported DB to disk.
        
    Returns:
        tuple: (result_dict, message) where result_dict is None on failure.
    """
    try:
        # Parse source JSON
        source_db = json.loads(raw_data, strict=False)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"

    # Validate input structure
    if not isinstance(source_db, dict):
        return None, "Input must be a JSON object"
    
    if "structures" not in source_db:
        return None, "Missing required 'structures' section"
    
    if not isinstance(source_db["structures"], dict):
        return None, "Structures must be an object"

    # Get the first structure
    structure_keys = list(source_db.get("structures", {}).keys())
    if not structure_keys:
        return None, "No structures found in source JSON"
    
    struct_key = structure_keys[0]
    source_structure = source_db["structures"][struct_key]

    # Initialize ported DB structure
    ported_db = {
        "structures": {
            struct_key: {
                "name": source_structure.get("name", struct_key),
                "rooms": {}
            }
        },
        "actions": []  # Required by GoogleHomeDB model
    }

    # States that should be converted to float (StrictFloat in model)
    float_states = {"brightness", "thermostatTemperatureSetpoint", "thermostatTemperatureAmbient", "openPercent"}
    
    # States that should be converted to int (StrictInt in model)
    int_states = {"fanSpeed", "currentVolume", "humiditySetting"}
    
    # Fan speed string to int mapping (from model)
    fan_speed_map = {"low": 33, "medium": 66, "high": 100}

    def convert_color_to_string(color_val):
        """Convert color dict to string format expected by the model."""
        if isinstance(color_val, str):
            return color_val
        if isinstance(color_val, dict):
            # Handle spectrumRgb format
            if 'spectrumRgb' in color_val:
                rgb = color_val['spectrumRgb']
                return f"#{rgb:06x}"
            # Handle hex format
            if 'hex' in color_val:
                return color_val['hex']
            # Handle temperature formats
            if 'temperature' in color_val:
                return f"{color_val['temperature']}K"
            if 'temperatureK' in color_val:
                return f"{color_val['temperatureK']}K"
            # Handle name format
            if 'name' in color_val:
                return color_val['name']
            # Fallback: return first available value as string
            for key, val in color_val.items():
                return str(val)
        return str(color_val)

    # Transform rooms and devices
    for room_name, room_data in source_structure.get("rooms", {}).items():
        ported_db["structures"][struct_key]["rooms"][room_name] = {
            "name": room_name,
            "devices": {}
        }

        for dev_type, dev_list in room_data.get("devices", {}).items():
            ported_db["structures"][struct_key]["rooms"][room_name]["devices"][dev_type] = []

            for device in dev_list:
                # Copy all device properties except device_state
                new_device = {k: v for k, v in device.items() if k != "device_state"}

                # Ensure toggles_modes exists
                if "toggles_modes" not in new_device:
                    new_device["toggles_modes"] = []

                # Transform device_state
                new_device["device_state"] = []
                for state in device.get("device_state", []):
                    name = state["name"]
                    val = state["value"]

                    # Handle "off" state by converting to "on" with inverted boolean
                    if name == "off":
                        new_device["device_state"].append({
                            "name": "on",
                            "value": not bool(val)
                        })
                    else:
                        # Convert color dicts to strings
                        if name == "color":
                            val = convert_color_to_string(val)
                        # Convert numeric values to float for specific states
                        elif name in float_states and isinstance(val, (int, float)):
                            val = float(val)
                            # Normalize brightness from 0-100 range to 0.0-1.0 range
                            if name == "brightness" and val > 1.0:
                                val = val / 100.0
                        # Convert numeric values to int for specific states
                        elif name in int_states:
                            if isinstance(val, (int, float)):
                                val = int(val)
                            # Handle fanSpeed string values (low, medium, high)
                            elif name == "fanSpeed" and isinstance(val, str):
                                val = fan_speed_map.get(val.lower(), int(val) if val.isdigit() else val)
                        
                        new_device["device_state"].append({
                            "name": name,
                            "value": val
                        })

                ported_db["structures"][struct_key]["rooms"][room_name]["devices"][dev_type].append(new_device)

    # Validate using GoogleHomeDB pydantic model
    try:
        validated = GoogleHomeDB(**ported_db)
    except ValidationError as e:
        return None, f"Validation error: {e}"

    if file_path:
        out_path = Path(file_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(validated.model_dump(), indent=2), encoding="utf-8")
        print(f"Output written to: {out_path.resolve()}")

    return validated.model_dump(), None


if __name__ == "__main__":
    if not sys.stdin.isatty():
        # read raw string from stdin
        raw = sys.stdin.read().strip()
        output_path = sys.argv[1] if len(sys.argv) > 1 else None
    else:   
        vendor_path = BASE_PATH / "vendor_google_home.json"
        raw = vendor_path.read_text()
        output_path = BASE_PATH / "ported_google_home.json"
    
    db, msg = port_google_home(raw, output_path)
    if db is None:
        print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Google Home porting completed successfully")
