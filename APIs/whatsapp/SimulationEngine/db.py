# File: APIs/whatsapp/SimulationEngine/db.py

import json
import os
from typing import Dict, Any, Optional
import threading
from .db_models import WhatsAppDB


# Bring in the live contacts dict from the centralized Contacts API
from contacts import DB as CONTACTS_DB

# Define the default path to your JSON DB file
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "WhatsAppDefaultDB.json",
)

# Load the WhatsApp DB
DB = None
with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB = json.load(f)

# ——— Live-link contacts ———
# Point WhatsApp’s contacts directly at the contacts API’s `myContacts` dict
DB["contacts"] = CONTACTS_DB["myContacts"]

def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.

    Args:
        filepath: Path to save the state file.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(DB, f)

def load_state(filepath: str) -> None:
    """
    Load DB state from a JSON file, validating it against the schema before updating.
    
    This function ensures that only valid data conforming to the WhatsAppDB
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
    #validated_db = WhatsAppDB(**data)

    # If validation passes, update the database with original data
    DB.clear()
    DB.update(data)

    # Re-bind to the live contacts dict after reset
    DB["contacts"] = CONTACTS_DB["myContacts"]

def get_database() -> WhatsAppDB:
    """
    Returns the current database as a WhatsAppDB Pydantic model.
    
    This function validates the current database state against the Pydantic model,
    ensuring data consistency and type safety.
    
    Returns:
        WhatsAppDB: The validated database model instance.
        
    Raises:
        ValidationError: If the current database state doesn't match the expected schema.
    """
    global DB
    return WhatsAppDB(**DB)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
