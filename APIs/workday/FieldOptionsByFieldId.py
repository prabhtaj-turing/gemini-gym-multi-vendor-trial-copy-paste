"""
This module provides functionality for retrieving field options associated with
specific fields in the Workday Strategic Sourcing system. It enables users to
access all options configured for a particular field, supporting comprehensive
field option management and configuration capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Union, Any, Optional
from .SimulationEngine import db
from pydantic import ValidationError
from .SimulationEngine.models import FieldIdModel

@tool_spec(
    spec={
        'name': 'list_field_options_by_field_id',
        'description': 'Returns a list of field options for the specified field.',
        'parameters': {
            'type': 'object',
            'properties': {
                'field_id': {
                    'type': 'string',
                    'description': """ The unique identifier of the field for which
                    to retrieve options. Must be a non-empty string containing only
                    alphanumeric characters, underscores, or dashes. """
                }
            },
            'required': [
                'field_id'
            ]
        }
    }
)
def get(field_id: str) -> List[Dict[str, Any]]:
    """Returns a list of field options for the specified field.

    Args:
        field_id (str): The unique identifier of the field for which
            to retrieve options. Must be a non-empty string containing only
            alphanumeric characters, underscores, or dashes.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a single field option record matching the `field_id`.
            - If no matches are found, or if the required database structure is missing, an empty list is returned.
            - Each dictionary in the list will have the following structure:
                - field_id (str): The unique identifier of the field.
                - options (List[str]): The list of available options for that field.
                
    Raises:
        TypeError: If `field_id` is not a string.
        ValueError: If `field_id` fails validation (e.g., is empty or contains characters other than alphanumerics, underscores, or dashes).
    """
    # 1. Type validation - ensure field_id is a string
    if field_id is None:
        raise TypeError("field_id cannot be None")
        
    if not isinstance(field_id, str):
        raise TypeError(f"field_id must be a string, got {type(field_id).__name__}")
    
    # 2. Use Pydantic model for comprehensive validation
    try:
        validated = FieldIdModel(field_id=field_id)
        field_id = validated.field_id  # Use the validated (and possibly stripped) field_id
    except ValidationError as e:
        # Extract validation error message for a more specific error
        error_detail = str(e)
        if "empty" in error_detail.lower():
            raise ValueError("field_id cannot be empty or contain only whitespace")
        elif "alphanumeric" in error_detail.lower():
            raise ValueError(
                "field_id must contain only alphanumeric characters, underscores, or dashes"
            )
        else:
            # Pass through the original validation error message
            raise ValueError(f"Invalid field_id: {error_detail}")
    
    # 3. Execute query with validated field_id
    field_options_list = []
    
    # Check if the fields collection and field_options subcollection exist
    if "fields" not in db.DB or "field_options" not in db.DB["fields"]:
        return field_options_list
    
    # Retrieve matching field options
    for option_id, option in db.DB["fields"]["field_options"].items():
        if option and option.get("field_id") == field_id:
            field_options_list.append(option)
            
    return field_options_list 