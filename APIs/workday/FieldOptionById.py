"""
This module provides functionality for managing field options by their unique
identifiers in the Workday Strategic Sourcing system. It supports updating
and deleting specific field options using their internal IDs.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Optional, Union, Any
from pydantic import ValidationError
from .SimulationEngine import db
from .SimulationEngine.models import FieldOptionId
from pydantic import ValidationError

@tool_spec(
    spec={
        'name': 'update_field_options_by_id',
        'description': 'Update a field options with given parameters.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the field option to update.'
                },
                'new_options': {
                    'type': 'array',
                    'description': 'A list of new options to set for the field option.',
                    'items': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            },
            'required': [
                'id',
                'new_options'
            ]
        }
    }
)
def patch(id: str, new_options: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Update a field options with given parameters.

    Args:
        id (str): The unique identifier of the field option to update.
        new_options (List[Dict[str, Any]]): A list of new options to set for the field option.

    Returns:
        Dict[str, Any]: The entire updated field option object from the database.
        The returned dictionary will contain the following keys:
        - field_id (str): The identifier of the parent field to which these options belong.
        - options (List[str]): The newly updated list of string values.

    Raises:
        ValueError: If no field option exists with the given ID.
        TypeError: If the input data is invalid (e.g., id is not a string,
                         new_options is not a list of strings).
    """
    if not isinstance(id, str):
        raise TypeError("ID must be a string.")
    if not id.strip():
        raise ValueError("ID cannot be empty or contain only whitespace.")
    if not isinstance(new_options, list) or not all(isinstance(o, str) for o in new_options):
        raise TypeError("new_options must be a list of strings.")

    # ---- business logic ----
    if id not in db.DB["fields"]["field_options"]:
        raise ValueError(f"Field option with id '{id}' not found.")

    field_option = db.DB["fields"]["field_options"][id]
    field_option["options"] = new_options
    return field_option

@tool_spec(
    spec={
        'name': 'delete_field_options_by_id',
        'description': 'Deletes a field option from the system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the field option to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: str) -> bool:
    """Deletes a field option from the system.

    Args:
        id (str): The unique identifier of the field option to delete.

    Returns:
        bool: True if the field option was successfully deleted.

    Raises:
        ValidationError: If the ID is not a string, is empty, or has an invalid format.
        ValueError: If the field option with the given ID does not exist.
    """
    try:
        # Pydantic validation handles all checks (type, empty, format) in one step.
        validated_id = FieldOptionId(id=id)
    except ValidationError as e:
        # Let the detailed validation error bubble up.
        raise e

    # After validation, check for existence.
    if validated_id.id in db.DB["fields"]["field_options"]:
        del db.DB["fields"]["field_options"][validated_id.id]
        return True
    else:
        # Raise a clear, predictable error if not found.
        raise ValueError(f"Field option with id '{validated_id.id}' not found.")