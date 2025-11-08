import os, sys
import json
from typing import Any, Dict, Optional
from datetime import date, datetime
from pydantic import ValidationError as PydanticValidationError
from .db_models import CesFlightsDB

# Add the SimulationEngine directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SimulationEngine'))

# Load default database from JSON file
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'DBs', 'CESFlightsDefaultDB.json')

from .custom_errors import (
    InvalidDateError, 
    FlightDataError,
    DatabaseError,
    BookingError
)

def _load_default_db() -> Dict[str, Any]:
    """
    Load the default database from JSON file and validate it.
    
    Returns:
        Dict[str, Any]: The validated database content.
        
    Raises:
        PydanticValidationError: If the database structure doesn't match the schema.
    """
    try:
        with open(DEFAULT_DB_PATH, 'r') as f:
            loaded_data = json.load(f)
        
        # Validate the loaded data using Pydantic model
        validated_db = CesFlightsDB(**loaded_data)
        return validated_db.model_dump(by_alias=True)
        
    except FileNotFoundError:
        # Fallback to empty structure if file doesn't exist
        return {
            "flight_bookings": {},
            "flight_data": {},
            "_end_of_conversation_status": {},
            "use_real_datastore": False,
            "sessions": {},
            "conversation_states": {},
            "retry_counters": {},
            "sample_flights": {},
            "sample_travelers": {},
            "sample_bookings": {}
        }

# Initialize database from file with validation
DB = _load_default_db()

def _get_current_date() -> str:
    """Get current date in ISO format with timezone information."""
    from datetime import timezone
    return datetime.now(timezone.utc).isoformat()


def _validate_string_input(val: Optional[str], field: str, allow_empty: bool = False) -> Optional[str]:
    """Validate string input following CES billing pattern."""
    if val is None:
        return None
    if not isinstance(val, str):
        raise PydanticValidationError(f"{field} must be a string")
    if not allow_empty and not val.strip():
        raise PydanticValidationError(f"{field} cannot be empty")
    return val.strip()


def _validate_date_input(val: Any, field: str) -> date:
    """Validate date input with proper error handling."""
    if isinstance(val, date):
        return val
    try:
        parsed_date = date.fromisoformat(str(val))
        return parsed_date
    except Exception:
        raise InvalidDateError(f"{field} must be a valid YYYY-MM-DD date")

def _validate_date_range(earliest: date, latest: date, field_prefix: str) -> None:
    """Validate that earliest date is before or equal to latest date."""
    if earliest > latest:
        raise InvalidDateError(f"{field_prefix}_earliest_date must be before or equal to {field_prefix}_latest_date")

def _validate_booking_date_range(departure_date: date, return_date: date) -> None:
    """Validate that return date is after departure date."""
    if return_date <= departure_date:
        raise InvalidDateError("Return date must be after departure date")

def _validate_date_in_range(check_date: date, field_name: str) -> None:
    """Validate that date is within allowed booking range (2024-03-29 to 2025-03-28)."""
    min_date = date(2024, 3, 29)
    max_date = date(2025, 3, 28)
    
    if check_date < min_date or check_date > max_date:
        raise InvalidDateError(f"{field_name} must be between {min_date} and {max_date}")

def _ensure_json_serializable(data: Any) -> Dict[str, Any]:
    """Ensure data is JSON serializable and return as dict."""
    try:
        json_str = json.dumps(data, default=str)
        return json.loads(json_str)
    except (TypeError, ValueError) as e:
        raise FlightDataError(f"Data is not JSON serializable: {e}")

def _save_interaction_to_db(interaction_type: str, call_id: str, data: Dict[str, Any]) -> None:
    """Save interaction data to database with error handling."""
    try:
        if interaction_type not in DB:
            DB[interaction_type] = {}
        
        # Ensure data is JSON serializable
        serializable_data = _ensure_json_serializable(data)
        serializable_data["timestamp"] = _get_current_date()
        
        DB[interaction_type][call_id] = serializable_data
        
        # Save to file (simplified version of CES billing's save_state)
        _save_state_to_file()
    except Exception as e:
        raise DatabaseError(f"Failed to save {interaction_type} interaction: {e}")

def _save_state_to_file() -> None:
    """Save current database state to file."""
    try:
        with open(DEFAULT_DB_PATH, 'w') as f:
            json.dump(DB, f, default=str, indent=2)
    except Exception as e:
        raise DatabaseError(f"Failed to save database state: {e}")

def _validate_traveler_count(travelers: list, expected_adults: int, expected_children: int) -> None:
    """Validate that traveler count matches expected passenger count."""
    total_travelers = len(travelers)
    expected_total = expected_adults + expected_children
    
    if total_travelers != expected_total:
        raise BookingError(
            f"Traveler count mismatch. Expected {expected_total} travelers "
            f"({expected_adults} adults + {expected_children} children) "
            f"but received {total_travelers} travelers."
        )

def get_expected_traveler_count(search_id: str) -> Dict[str, int]:
    """Get expected traveler count for a search."""
    flight_data = DB.get("flight_data", {}).get(search_id, {})
    search_params = flight_data.get("search_params", {})
    
    adults = search_params.get("num_adult_passengers", 1)
    children = search_params.get("num_child_passengers", 0)
    
    return {
        "adults": adults,
        "children": children,
        "total": adults + children
    }


def new_record_id(record_type: str) -> str:
    """Generate a new record ID for the given type."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{record_type}_{timestamp}"


def save_state(file_path: str) -> None:
    """
    Save the current database state to a JSON file after validating it.
    
    Args:
        file_path: Path to the JSON file where the state will be saved.
        
    Raises:
        PydanticValidationError: If the current DB state does not conform to the CesFlightsDB schema.
        DatabaseError: If the file operation fails.
    """
    try:
        global DB
        # Validate the DB before saving - this will raise ValidationError if invalid
        validated_db = CesFlightsDB(**DB)
        with open(file_path, 'w') as f:
            json.dump(validated_db.model_dump(by_alias=True), f, indent=2, default=str)
    except PydanticValidationError as e:
        raise DatabaseError(f"Database validation failed before save: {e}")
    except Exception as e:
        raise DatabaseError(f"Failed to save database state: {e}")


def load_state(file_path: str) -> None:
    """
    Load database state from a JSON file and validate it against the schema.
    
    Args:
        file_path: Path to the JSON file containing the saved state.
        
    Raises:
        PydanticValidationError: If the loaded data does not conform to the CesFlightsDB schema.
        DatabaseError: If the file is not found, contains invalid JSON, or operation fails.
    """
    try:
        global DB
        with open(file_path, 'r') as f:
            loaded_data = json.load(f)
        
        # Validate the loaded data - this will raise ValidationError if invalid
        validated_db = CesFlightsDB(**loaded_data)
        # If validation passes, update DB with the validated data
        DB.clear()
        DB.update(validated_db.model_dump(by_alias=True))
        
    except FileNotFoundError:
        raise DatabaseError(f"Database file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise DatabaseError(f"Invalid JSON in database file: {e}")
    except PydanticValidationError as e:
        raise DatabaseError(f"Database validation failed on load: {e}")
    except Exception as e:
        raise DatabaseError(f"Failed to load database state: {e}")


def get_minified_state() -> Dict[str, int]:
    """Get a summary of the current database state with counts."""
    return {
        "flight_bookings": len(DB.get("flight_bookings", {})),
        "flight_data": len(DB.get("flight_data", {})),
        "_end_of_conversation_status": len(DB.get("_end_of_conversation_status", {})),
        "conversation_states": len(DB.get("conversation_states", {})),
        "retry_counters": len(DB.get("retry_counters", {})),
        "sessions": len(DB.get("sessions", {})),
        "sample_flights": len(DB.get("sample_flights", {})),
        "sample_travelers": len(DB.get("sample_travelers", {})),
        "sample_bookings": len(DB.get("sample_bookings", {}))
    }


def get_database() -> CesFlightsDB:
    """
    Returns the current database as a validated Pydantic CesFlightsDB model.
    
    Returns:
        CesFlightsDB: The current database state as a Pydantic model instance.
        
    Raises:
        PydanticValidationError: If the current DB state is invalid.
    """
    global DB
    return CesFlightsDB(**DB)


def save_conversation_state(session_id: str, state_data: Dict[str, Any]) -> None:
    """Save conversation state to database."""
    try:
        if "conversation_states" not in DB:
            DB["conversation_states"] = {}
        
        DB["conversation_states"][session_id] = _ensure_json_serializable(state_data)
        _save_state_to_file()
        
    except Exception as e:
        raise DatabaseError(f"Failed to save conversation state: {e}")


def load_conversation_state(session_id: str) -> Dict[str, Any]:
    """Load conversation state from database."""
    try:
        if "conversation_states" not in DB:
            return {}
        
        return DB["conversation_states"].get(session_id, {})
        
    except Exception as e:
        raise DatabaseError(f"Failed to load conversation state: {e}")


def save_retry_counters(session_id: str, counters: Dict[str, int]) -> None:
    """Save retry counters to database."""
    try:
        if "retry_counters" not in DB:
            DB["retry_counters"] = {}
        
        DB["retry_counters"][session_id] = _ensure_json_serializable(counters)
        _save_state_to_file()
        
    except Exception as e:
        raise DatabaseError(f"Failed to save retry counters: {e}")


def load_retry_counters(session_id: str) -> Dict[str, int]:
    """Load retry counters from database."""
    try:
        if "retry_counters" not in DB:
            return {}
        
        return DB["retry_counters"].get(session_id, {})
        
    except Exception as e:
        raise DatabaseError(f"Failed to load retry counters: {e}")


def update_retry_counter(session_id: str, counter_key: str, value: int) -> None:
    """Update a specific retry counter for a session."""
    try:
        if "retry_counters" not in DB:
            DB["retry_counters"] = {}
        
        if session_id not in DB["retry_counters"]:
            DB["retry_counters"][session_id] = {}
        
        DB["retry_counters"][session_id][counter_key] = value
        _save_state_to_file()
        
    except Exception as e:
        raise DatabaseError(f"Failed to update retry counter: {e}")


def reset_session_retry_counters(session_id: str) -> None:
    """Reset all retry counters for a session."""
    try:
        if "retry_counters" in DB and session_id in DB["retry_counters"]:
            DB["retry_counters"][session_id] = {}
            _save_state_to_file()
        
    except Exception as e:
        raise DatabaseError(f"Failed to reset retry counters: {e}")
