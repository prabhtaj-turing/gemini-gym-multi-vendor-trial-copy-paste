# File: APIs/messages/SimulationEngine/db.py

import json
import os
from typing import Dict, Any

# Bring in the live contacts dict from the centralized Contacts API
from contacts import DB as CONTACTS_DB

# Define the default path to your JSON DB file
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "MessagesDefaultDB.json",
)

# Load the Messages DB
DB = None
# Only load from file if DB is not already initialized
if DB is None:
    with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
        DB = json.load(f)

# ——— Live-link recipients ———
# Point Messages's recipients directly at the contacts API's `myContacts` dict
DB["recipients"] = CONTACTS_DB["myContacts"]

def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.

    Args:
        filepath: Path to save the state file.
    """
    with open(filepath, "w") as f:
        json.dump(DB, f)

def load_state(
    filepath: str,
) -> object:
    """Load state from a JSON file.

    Args:
        filepath: Path to load the state file from.
    """
    global DB
    # Load new data and replace contents
    with open(filepath, "r") as f:
        new_data = json.load(f)
        DB.clear()
        DB.update(new_data)

    # Re-bind to the live contacts dict after reset
    DB["recipients"] = CONTACTS_DB["myContacts"]

def reset_db():
    """Reset database to initial state"""
    global DB
    # Reset to completely empty state
    DB.clear()
    # Load fresh data from default DB
    with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
        fresh_data = json.load(f)
        DB.update(fresh_data)
    
    # Re-bind to the live contacts dict after reset
    DB["recipients"] = CONTACTS_DB["myContacts"]

# Load default data if available
if os.path.exists(DEFAULT_DB_PATH):
    try:
        with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
            default_data = json.load(f)
            # Only update with default data if our DB is missing key structures
            for key in ["messages", "message_history", "counters"]:
                if key not in DB:
                    DB[key] = default_data.get(key, {})
    except (json.JSONDecodeError, FileNotFoundError):
        # If there's an issue with the default data, continue with current DB
        pass

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
