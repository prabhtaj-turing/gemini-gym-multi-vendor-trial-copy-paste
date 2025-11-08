import json
import os
from typing import Optional

# Define the default path to your JSON DB file
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "GenericMediaDefaultDB.json",
)

DB = None

def load_initial_db():
    with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

DB = load_initial_db()

def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.

    Args:
        filepath (str): Path to save the state file.
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
        filepath (str): Path to load the state file from.
        error_config_path (str): Path to the error configuration JSON file.
        error_definitions_path (str): Path to the error definitions JSON file.
    """
    global DB
    with open(filepath, "r") as f:
        new_data = json.load(f)
        DB.clear()
        DB.update(new_data)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB

def reset_db():
    """Reset database to initial state"""
    global DB
    for key in list(DB.keys()):
        if isinstance(DB[key], dict):
            DB[key].clear()
        elif isinstance(DB[key], list):
            DB[key].clear()
