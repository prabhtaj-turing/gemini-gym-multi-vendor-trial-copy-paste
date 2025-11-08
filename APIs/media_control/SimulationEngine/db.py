import os
import json
from typing import Dict, Any

from APIs.media_control.SimulationEngine.db_models import AndroidDB

# Initialize empty database structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB: Dict[str, Any] = {}

def save_state(filepath: str):
    """Save current database state to JSON file"""
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=2)

def load_state(filepath: str) -> None:
    """Load database state from JSON file"""
    global DB
    try:
        with open(filepath, "r") as f:
            loaded_data = json.load(f)
            #AndroidDB(**loaded_data)
            DB.update(loaded_data)
    except (FileNotFoundError, json.JSONDecodeError):
        # Silently ignore file not found or invalid JSON
        pass

def reset_db():
    """Reset database to initial state"""
    global DB
    for key in list(DB.keys()):
        if isinstance(DB[key], dict):
            DB[key].clear()
        elif isinstance(DB[key], list):
            DB[key].clear()

def get_database():
    global DB
    return AndroidDB(**DB)

# Load default data if available
def load_default_data():
    """Load default database from DBs directory"""
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "DBs",
        "MediaControlDefaultDB.json"
    )
    if os.path.exists(db_path):
        load_state(db_path)

# Initialize with default data
load_default_data()

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
