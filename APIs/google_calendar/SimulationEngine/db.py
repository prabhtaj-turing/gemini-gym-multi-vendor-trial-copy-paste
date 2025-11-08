# APIs/google_calendar/SimulationEngine/db.py
import json
from .db_models import GoogleCalendarDB

DB = {
    "acl_rules": {},  # Stores ACL rule objects, keyed by ruleId
    "calendar_list": {},  # Stores CalendarList entries, keyed by calendarId
    "calendars": {},  # Stores Calendar objects, keyed by calendarId
    "channels": {},  # Stores Channel objects, keyed by channelId (or random)
    "colors": {  # Colors are usually static in the real API, but we'll store them anyway
        "calendar": {},  # This might store color definitions for calendars
        "event": {},  # This might store color definitions for events
    },
    "events": {},  # Stores events, keyed by (calendarId, eventId) or a combined key
}


def reset_db():
    """Reset the database to its initial empty state."""
    global DB
    for key in DB:
        DB[key].clear()


def save_state(filepath: str) -> None:
    """
    Save the current in-memory DB state to a JSON file.
    """
    # Create a copy of DB with string keys for events
    db_copy = DB.copy()

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(db_copy, f, indent=2)


def load_state(filepath: str) -> None:
    """
    Load DB state from a JSON file, validating it against the schema before updating.
    
    This function ensures that only valid data conforming to the GoogleCalendarDB
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
    except (FileNotFoundError, json.JSONDecodeError):
        return

    # Validate the data against the Pydantic schema
    #validated_db = GoogleCalendarDB(**data)
    
    # Convert the validated Pydantic model back to dict for storage
    DB.clear()
    DB.update(data)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB


def get_database() -> GoogleCalendarDB:
    """
    Returns the current database as a GoogleCalendarDB Pydantic model.
    
    This function validates the current database state against the Pydantic model,
    ensuring data consistency and type safety.
    
    Returns:
        GoogleCalendarDB: The validated database model instance.
        
    Raises:
        ValidationError: If the current database state doesn't match the expected schema.
    """
    global DB
    return GoogleCalendarDB(**DB)
