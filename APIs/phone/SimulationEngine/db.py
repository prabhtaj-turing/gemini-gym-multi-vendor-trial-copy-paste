# phone/SimulationEngine/db.py
import json
import os
from .db_models import PhoneDB

# Bring in the live contacts dict from the centralized Contacts API
from contacts import DB as CONTACTS_DB

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "PhoneDefaultDB.json",
)

# Load the Phone DB
DB = {}

with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB = json.load(f)

# ——— Live-link contacts ———
# Point Phone’s contacts directly at the contacts API’s `myContacts` dict
DB["contacts"] = CONTACTS_DB["myContacts"]


def save_state(filepath: str) -> None:
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=2)


def load_state(filepath: str) -> None:
    """Load state from a JSON file and validate against the Pydantic schema.

    Args:
        filepath: Path to load the state file from.
        
    Raises:
        ValidationError: If the loaded data doesn't match the Pydantic schema
        FileNotFoundError: If the file doesn't exist
        JSONDecodeError: If the file contains invalid JSON
    """
    global DB
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise e

    # Validate the data against the Pydantic schema
    #validated_db = PhoneDB(**data)

    # If validation passes, update the database with original data (preserve structure)
    DB.clear()
    DB.update(data)

    # Re-bind to the live contacts dict after reset
    DB["contacts"] = CONTACTS_DB["myContacts"]


def get_database() -> PhoneDB:
    """
    Returns the current database as a Pydantic BaseModel derived class.
    
    Returns:
        PhoneDB: The current database state as a Pydantic model
    """
    global DB
    return PhoneDB(**DB)





def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
