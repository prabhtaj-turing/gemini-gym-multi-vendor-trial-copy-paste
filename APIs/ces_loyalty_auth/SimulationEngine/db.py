import os
import json
from typing import Dict, Any
from .db_models import CesLoyaltyAuthDB

# Initialize empty database structure
DB: Dict[str, Any] = {
    "CONVERSATION_STATUS": None,
    "SESSION_STATUS": None,
    "AUTH_RESULT": None,
    "AUTH_STATUS": None,
    "OFFER_ENROLLMENT": None,
    "PROFILE_BEFORE_AUTH": {},
    "PROFILE_AFTER_AUTH": {},
    "use_real_datastore": False,
    "_end_of_conversation_status": {},
}


def save_state(filepath: str):
    """Save current database state to JSON file"""
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=2)


def load_state(filepath: str) -> None:
    """Load database state from JSON file and validate against schema"""
    global DB
    try:
        with open(filepath, "r") as f:
            loaded_data = json.load(f)
            # Validate the loaded data against the Pydantic model
            CesLoyaltyAuthDB(**loaded_data)
            DB.update(loaded_data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load state from {filepath}: {e}")
    except Exception as e:
        print(f"Warning: Data validation failed for {filepath}: {e}")


def reset_db():
    """Reset database to initial state"""
    global DB
    DB.clear()
    DB.update(
        {
            "CONVERSATION_STATUS": None,
            "SESSION_STATUS": None,
            "AUTH_RESULT": None,
            "AUTH_STATUS": None,
            "OFFER_ENROLLMENT": None,
            "PROFILE_BEFORE_AUTH": {},
            "PROFILE_AFTER_AUTH": {},
            "use_real_datastore": False,
            "_end_of_conversation_status": {},
        }
    )
    load_default_data()


def get_database() -> CesLoyaltyAuthDB:
    """
    Returns the current database as a Pydantic model instance.
    This ensures type safety and validation.
    """
    global DB
    return CesLoyaltyAuthDB(**DB)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB


# Load default data if available
def load_default_data():
    """Load default database from DBs directory"""
    try:
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "DBs",
            "CesLoyaltyAuthDefaultDB.json",
        )
        if os.path.exists(db_path):
            load_state(db_path)
    except NameError:
        # Handle case when __file__ is not available (e.g., when exec'd)
        db_path = "DBs/CesLoyaltyAuthDefaultDB.json"
        if os.path.exists(db_path):
            load_state(db_path)


# Initialize with default data
load_default_data()
