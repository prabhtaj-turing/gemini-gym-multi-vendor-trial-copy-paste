# canva/SimulationEngine/db.py
import json
import os
from typing import Dict, Any
from .db_models import CanvaDB
# Define the default path to your JSON DB file
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "CanvaDefaultDB.json",
)

# Initialize DB structure
DB = {
    "Users": {},
    "Designs": {},
    "brand_templates": {},
    "autofill_jobs": {},
    "asset_upload_jobs": {},
    "design_export_jobs": {},
    "design_import_jobs": {},
    "url_import_jobs": {},
    "assets": {},
    "folders": {}
}

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
            print(f"Warning: Failed to load default DB from {DEFAULT_DB_PATH}: {e}")

def reset_db():
    """Reset database to initial state"""
    global DB
    for key in list(DB.keys()):
        if isinstance(DB[key], dict):
            DB[key].clear()
        elif isinstance(DB[key], list):
            DB[key].clear()
    
    # Reload default data after reset
    load_default_data()


# Load default data if available
load_default_data()


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
        # CanvaDB.model_validate(loaded_db) removing for now
        DB.update(loaded_db)



def get_database():
    """Returns a validated CanvaDB model instance of the current database state."""
    return CanvaDB(**DB)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
