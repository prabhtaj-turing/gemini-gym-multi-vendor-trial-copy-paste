import json
import os
from typing import Any, Optional

# Define the default path to your JSON DB file
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "RetailDefaultDB.json",
)

DB: dict[str, Any] = {
    "orders": {}, 
    "users": {},
    "products": {},
}

def save_state(filepath: str) -> None: # pragma: no cover
    """Save the current state to a JSON file.
    Args:
        filepath: Path to save the state file.
    """
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=2)

def load_state(
    filepath: str,
    error_config_path: str = "./error_config.json",
    error_definitions_path: str = "./error_definitions.json",
) -> object: # pragma: no cover
    """Load state from a JSON file.
    Args:
        filepath: Path to load the state file from.
    """
    global DB
    with open(filepath, "r") as f:
        new_data = json.load(f)
        DB.clear()
        DB.update(new_data)

def reset_db(): # pragma: no cover
    """Reset database to initial state"""
    global DB
    for key in list(DB.keys()):
        if isinstance(DB[key], dict):
            DB[key].clear()
        elif isinstance(DB[key], list):
            DB[key].clear()

# Load default data if available
def load_default_data(): # pragma: no cover
    """Load default database from DBs directory"""
    if os.path.exists(DEFAULT_DB_PATH):
        load_state(DEFAULT_DB_PATH)


load_default_data()

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
