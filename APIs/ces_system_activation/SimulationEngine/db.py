# ces/SimulationEngine/db.py
import json
import os

# Define the default path to your JSON DB file
DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../DBs/CesSystemActivationDefaultDB.json")
)

# Initialize DB structure
DB = {}

def load_default_data():
    """Load default database from DBs directory"""
    global DB
    if os.path.exists(DEFAULT_DB_PATH):
        try:
            with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
                default_data = json.load(f)
                DB.clear()
                DB.update(default_data)
        except (json.JSONDecodeError, IOError) as e:
            Exception(f"Warning: Failed to load default DB from {DEFAULT_DB_PATH}: {e}")

def reset_db():
    """Reset database to initial state"""
    global DB
    for key in list(DB.keys()):
        if isinstance(DB[key], dict):
            DB[key].clear()
        elif isinstance(DB[key], list):
            DB[key].clear()

    # Reload default data after reset


def save_state(filepath: str) -> None:
    """
    Saves the current state of the database to a file.

    Args:
        filepath (str): Path to the file where the state should be saved.
    """
    with open(filepath, "w") as f:
        json.dump(DB, f)

def load_state(filepath: str) -> None:
    """
    Loads the database state from a file and updates the global DB.

    Args:
        filepath (str): Path to the file from which to load the state.
    """
    global DB
    with open(filepath, "r") as f:
        DB.clear()
        loaded_db = json.load(f)
        DB.update(loaded_db)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB

# Load DB data if available
load_state(DEFAULT_DB_PATH)