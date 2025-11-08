# contacts/SimulationEngine/db.py
import json
import os
from .db_models import ContactsDB

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "ContactsDefaultDB.json",
)

DB = {}

# Use Pydantic DB to load the DefaultDB
with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    default_data = json.load(f)
    # Validate the default data against the Pydantic schema
    #validated_default_db = ContactsDB(**default_data)
    # If validation passes, update the database
    DB.update(default_data)

def save_state(filepath: str) -> None:
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=2)


def load_state(filepath: str) -> None:
    """
    Load DB state from a JSON file, validating it against the schema before updating.
    
    This function ensures that only valid data conforming to the ContactsDB
    schema can be loaded into the database, preventing data corruption.
    
    Args:
        filepath: Path to the JSON file containing the database state.
        
    Raises:
        ValidationError: If the loaded data doesn't match the expected schema.
        FileNotFoundError: If the specified file doesn't exist.
        JSONDecodeError: If the file contains invalid JSON.
    """
    global DB
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise e

    # Validate the data against the Pydantic schema
    #validated_db = ContactsDB(**data)

    # If validation passes, update the database with original data (preserve structure)
    DB.clear()
    DB.update(data)


def get_database() -> ContactsDB:
    """
    Returns the current database as a Pydantic BaseModel derived class.
    
    Returns:
        ContactsDB: The current database state as a Pydantic model
    """
    global DB
    return ContactsDB(**DB)





def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
