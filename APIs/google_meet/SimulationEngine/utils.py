"""
Utility functions for the Meet API simulation.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from .db import DB


def validate_datetime_string(datetime_str: str, field_name: str = "datetime") -> datetime:
    """
    Validates and parses a datetime string to a datetime object.
    
    Expected formats:
    - ISO 8601 datetime: "2023-01-01T10:00:00Z" or "2023-01-01T10:00:00"
    - Simple time: "10:00", "10:05", "23:59" (assumes current date)
    
    Args:
        datetime_str (str): The datetime string to validate and parse.
        field_name (str): The name of the field being validated (for error messages).
        
    Returns:
        datetime: The parsed datetime object.
        
    Raises:
        ValueError: If the datetime string is invalid or cannot be parsed.
    """
    if not isinstance(datetime_str, str):
        raise ValueError(f"{field_name} must be a string, got {type(datetime_str).__name__}")
    
    if not datetime_str.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace only")
    
    # Try parsing as simple time format first (HH:MM or HH:MM:SS)
    if ':' in datetime_str and 'T' not in datetime_str and '-' not in datetime_str:
        try:
            # Handle simple time formats like "10:00" or "10:00:00"
            time_parts = datetime_str.split(':')
            if len(time_parts) == 2:  # HH:MM
                hour, minute = int(time_parts[0]), int(time_parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    # Create datetime with current date and specified time
                    from datetime import date, time
                    today = date.today()
                    return datetime.combine(today, time(hour=hour, minute=minute))
            elif len(time_parts) == 3:  # HH:MM:SS
                hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
                if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                    # Create datetime with current date and specified time
                    from datetime import date, time
                    today = date.today()
                    return datetime.combine(today, time(hour=hour, minute=minute, second=second))
        except (ValueError, IndexError):
            pass  # Fall through to ISO 8601 parsing
    
    # Try parsing ISO 8601 format
    try:
        # Handle both with and without timezone info
        if datetime_str.endswith('Z'):
            # UTC timezone
            dt = datetime.fromisoformat(datetime_str[:-1].replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(datetime_str)
        return dt
    except ValueError as e:
        raise ValueError(f"Invalid {field_name} format. Expected ISO 8601 format (e.g., '2023-01-01T10:00:00Z' or '2023-01-01T10:00:00') or simple time format (e.g., '10:00'). Error: {str(e)}")
    
    # If we get here, the format is not recognized
    raise ValueError(f"Invalid {field_name} format. Expected ISO 8601 format (e.g., '2023-01-01T10:00:00Z' or '2023-01-01T10:00:00') or simple time format (e.g., '10:00'). Got: {datetime_str}")


def ensure_exists(collection: str, item_id: str) -> bool:
    """
    Checks if an item exists in a specific collection in the database.
    
    Args:
        collection (str): The name of the collection to check (e.g., "spaces", "conferenceRecords").
        item_id (str): The ID of the item to check for.
        
    Returns:
        True if the item exists, raises ValueError otherwise.
    """
    if collection not in DB or item_id not in DB[collection]:
        raise ValueError(f"Item '{item_id}' does not exist in collection '{collection}'.")
    return True

def paginate_results(items: List[Dict[str, Any]], collection_name: str, page_size: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Paginates a list of items based on the provided page size and token.
    
    Args:
        items (List[Dict[str, Any]]): The list of items to paginate.
        collection_name (str): The name of the collection (used as the key in the result).
        page_size (Optional[int]): The maximum number of items to return in a page.
        page_token (Optional[str]): A token indicating the starting position for the page.
        
    Returns:
        A dictionary containing the paginated items under collection_name key and a next page token if applicable.
    """
    if not page_size:
        page_size = 100
    
    start_index = 0
    if page_token:
        try:
            start_index = int(page_token)
        except ValueError:
            start_index = 0
    
    end_index = min(start_index + page_size, len(items))
    paginated_items = items[start_index:end_index]
    
    result = {
        collection_name: paginated_items
    }
    
    if end_index < len(items):
        result["nextPageToken"] = str(end_index)
    
    return result 