import json
import os
from typing import Optional
from device_actions.SimulationEngine.models import DeviceActionsDB

# Define the default path to your JSON DB file
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "DeviceActionsDefaultDB.json",
)

DB = {}

def load_initial_db() -> dict:
    with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# DB = DeviceActionsDB.model_validate(load_initial_db()).model_dump(mode="json") removing for now

def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.
    Args:
        filepath: Path to save the state file.
    """
    with open(filepath, "w") as f:
        json.dump(DB, f)

def load_state(
    filepath: str,
    error_config_path: str = "./error_config.json",
    error_definitions_path: str = "./error_definitions.json",
) -> None:
    """Load state from a JSON file.
    Args:
        filepath: Path to load the state file from.
    """
    global DB
    with open(filepath, "r") as f:
        new_data = json.load(f)
        #validated = DeviceActionsDB.model_validate(new_data).model_dump(mode="json") removing for now
        DB.clear()
        DB.update(new_data)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
