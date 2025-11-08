from home_assistant.SimulationEngine.db import DB

allowed_states = {
    "light": ["On", "Off"],
    "fan": ["On", "Off"],
    "pump": ["On", "Off"],
    "sprinkler": ["On", "Off"],
    "door": ["Open", "Closed", "Locked", "Unlocked"],
    "window": ["Open", "Closed"],
    "wifi": ["On", "Off"],
    "frame": ["On", "Off"],
    "speaker": ["On", "Off"],
    "clock": ["On", "Off"],
    "tv": ["On", "Off"],
    "alarm": ["On", "Off"],
    "vacuum": ["On", "Off"],
    "pet_feeder": ["On", "Off"],
    "curtain": ["Open", "Closed"]
}

def _get_device_type(entity_id: str, devices: dict) -> str:
    # This helper remains the same
    if entity_id in devices and "type" in devices[entity_id]:
        return devices[entity_id]["type"].lower()
    return entity_id.split('.')[0]

def _get_home_assistant_devices() -> dict:
    """Helper function to get the Home Assistant devices from the database."""
    return DB.get('environment', {}).get('home_assistant', {}).get("devices", {})
