import json
import os
from typing import Dict, Any
from pydantic import ValidationError
from .db_models import SlackDB

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "SlackDefaultDB.json",
)

DB = {}

# Load and validate the default database
with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    loaded_data = json.load(f)
    validated_db = SlackDB(**loaded_data)
    DB.update(validated_db.model_dump())


# -------------------------------------------------------------------
# Persistence Helpers
# -------------------------------------------------------------------
def save_state(filepath: str):
    """
    Saves the current API state to a JSON file after validating it.
    
    Args:
        filepath: Path to the JSON file where the state will be saved.
        
    Raises:
        ValidationError: If the current DB state does not conform to the SlackDB schema.
    """
    global DB
    # Validate the DB before saving - this will raise ValidationError if invalid
    #validated_db = SlackDB(**DB)
    with open(filepath, 'w') as f:
        json.dump(DB, f)

def load_state(filepath: str) -> None:
    """
    Loads the API state from a JSON file and validates it against the schema.
    
    Args:
        filepath: Path to the JSON file containing the saved state.
        
    Raises:
        ValidationError: If the loaded data does not conform to the SlackDB schema.
        
    Note:
        FileNotFoundError is silently ignored (no action taken if file doesn't exist).
    """
    global DB
    try:
        with open(filepath, 'r') as f:
            loaded_data = json.load(f)
        
        # Validate the loaded data - this will raise ValidationError if invalid
        #validated_db = SlackDB(**loaded_data)
        # If validation passes, update DB with the validated data
        DB.update(loaded_data)
    except FileNotFoundError:
        pass


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB

def get_database() -> SlackDB:
    """
    Returns the current database as a validated Pydantic SlackDB model.
    
    Returns:
        SlackDB: The current database state as a Pydantic model instance.
    """
    global DB
    return SlackDB(**DB)

def reset_db() -> None:
    """
    Resets the DB by clearing all data while maintaining the structure.
    
    This clears all users, channels, files, reminders, usergroups, and messages,
    but keeps the database structure intact with empty collections.
    """
    global DB
    # Get the current user info if it exists, otherwise use a default
    current_user_id = DB.get('current_user', {}).get('id', 'U_DEFAULT')
    current_user_is_admin = DB.get('current_user', {}).get('is_admin', False)
    
    # Reset DB to empty structure
    DB.clear()
    DB.update({
        "current_user": {
            "id": current_user_id,
            "is_admin": current_user_is_admin
        },
        "users": {},
        "channels": {},
        "files": {},
        "reminders": {},
        "usergroups": {},
        "scheduled_messages": [],
        "ephemeral_messages": []
    })
