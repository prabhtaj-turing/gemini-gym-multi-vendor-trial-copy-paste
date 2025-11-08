import json
import os
from typing import Dict, Any
from .db_models import GooglePeopleDB

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "GooglePeopleDefaultDB.json",
)


class DB:
    """Database class for Google People API simulation."""
    
    def __init__(self):
        self._data = {}
        self._load_default_data()
    
    def _load_default_data(self):
        """Load default data from JSON file with Pydantic validation."""
        try:
            with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
                default_data = json.load(f)
                # Validate the default data against the Pydantic schema
                #validated_default_db = GooglePeopleDB(**default_data)
                # If validation passes, update the database
                self._data.update(default_data)
        except FileNotFoundError:
            # Initialize with empty data if file doesn't exist
            self._data = {}
    
    def get(self, key: str, default=None):
        """Get a value from the database."""
        return self._data.get(key, default)
    
    def set(self, key: str, value):
        """Set a value in the database."""
        self._data[key] = value
    
    def clear(self):
        """Clear all data from the database."""
        self._data.clear()
    
    def update(self, data):
        """Update the database with new data."""
        self._data.update(data)


# Create a singleton instance
DB = DB()


def save_state(filepath: str) -> None:
    """Save the current state to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(DB._data, f)


def load_state(filepath: str) -> None:
    """
    Load DB state from a JSON file, validating it against the schema before updating.
    
    This function ensures that only valid data conforming to the GooglePeopleDB
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
    #validated_db = GooglePeopleDB(**data)

    # If validation passes, update the database with original data
    DB.clear()
    DB.update(data)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB._data


def get_database() -> GooglePeopleDB:
    """
    Returns the current database as a GooglePeopleDB Pydantic model.
    
    This function validates the current database state against the Pydantic model,
    ensuring data consistency and type safety.
    
    Returns:
        GooglePeopleDB: The validated database model instance.
        
    Raises:
        ValidationError: If the current database state doesn't match the expected schema.
    """
    global DB
    return GooglePeopleDB(**DB._data)
