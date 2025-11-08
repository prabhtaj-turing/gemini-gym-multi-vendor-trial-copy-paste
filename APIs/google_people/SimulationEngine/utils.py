import uuid
from typing import Dict, Any, List


def generate_id() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields are present in the data dictionary.
    
    Args:
        data: The data dictionary to validate
        required_fields: List of field names that must be present
        
    Raises:
        ValueError: If any required field is missing
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def sanitize_data_for_serialization(data: Any) -> Any:
    """
    Safety net function to sanitize data and convert enum objects to strings
    to prevent serialization failures in API responses.
    
    Args:
        data: Any data structure that might contain enum objects
        
    Returns:
        Sanitized data with enum objects converted to strings
    """
    # Import here to avoid circular imports
    from .models import PhoneType
    
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            sanitized[key] = sanitize_data_for_serialization(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data_for_serialization(item) for item in data]
    elif isinstance(data, PhoneType):
        # Convert PhoneType enum to string
        return data.value
    elif hasattr(data, '__dict__') and hasattr(data, 'value'):
        # Handle other enum types that have a 'value' attribute
        return data.value
    else:
        return data
