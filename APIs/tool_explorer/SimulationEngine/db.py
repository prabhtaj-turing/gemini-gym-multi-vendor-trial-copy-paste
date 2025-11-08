# File: APIs/tool_explorer/SimulationEngine/db.py

import json
import os
from typing import Optional, Dict, Any

# Define the default path to the ToolExplorer JSON DB file
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "ToolExplorerDefaultDB.json",
)

# Load the database from the JSON file
DB = None
with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB = json.load(f)

def reset_db():
    """Reset the database to its default state."""
    global DB
    DB.clear()
    with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
        DB.update(json.load(f))

def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.

    Args:
        filepath: Path to save the state file.
    """
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=2)

def load_state(filepath: str) -> None:
    """Load database state from JSON file.
    
    Args:
        filepath: Path to load the state file from.
    """
    global DB
    try:
        with open(filepath, "r") as f:
            loaded_data = json.load(f)
            DB.update(loaded_data)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
