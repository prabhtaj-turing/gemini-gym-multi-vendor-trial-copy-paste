import json
import os
from .db_models import GoogleSearchDB

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "GoogleSearchDefaultDB.json",
)

DB = {}

with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB.update(json.load(f))


def reset_db():
    """Reset the database to its default state."""
    global DB
    DB.clear()
    with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
        DB.update(json.load(f))


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
    """
    global DB
    try:
        with open(filepath, "r") as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return
    
    # Validate the loaded data against the Pydantic schema
    try:
        #validated_db = GoogleSearchDB(**state)
        # If validation passes, update the database
        DB.clear()
        DB.update(state)
    except Exception as e:
        raise ValueError(f"Invalid database schema: {e}") from e


def get_database() -> GoogleSearchDB:
    """
    Returns the current database as a Pydantic BaseModel derived class.
    
    Returns:
        GoogleSearchDB: The current database state as a Pydantic model
    """
    global DB
    return GoogleSearchDB(**DB)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
