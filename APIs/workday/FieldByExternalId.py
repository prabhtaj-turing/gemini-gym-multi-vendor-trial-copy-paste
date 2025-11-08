"""
Field Management Module for Workday Strategic Sourcing API Simulation.

This module provides functionality for managing fields by their external identifiers
in the Workday Strategic Sourcing system. It supports retrieving, updating, and
deleting specific fields using their external IDs, with comprehensive error
handling for invalid or non-existent external IDs.
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, Optional, Union
import re

from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_field_by_external_id',
        'description': """ Retrieves the details of a specific field by its external ID.
        
        This function returns the complete details of a field identified by its
        external identifier. The function searches through all fields to find a
        match for the provided external ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the field to retrieve.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get(external_id: str) -> Dict:
    """Retrieves the details of a specific field by its external ID.

    This function returns the complete details of a field identified by its
    external identifier. The function searches through all fields to find a
    match for the provided external ID.

    Args:
        external_id (str): The external identifier of the field to retrieve.

    Returns:
        Dict: A dictionary containing the field details, including:
            - id (Union[int, str]): Internal unique identifier of the field
            - external_id (str): The provided external identifier
            - name (str): Name of the field
            - type (str): Data type of the field (e.g., 'text', 'number', 'date')
            - required (bool): Whether the field is required
            - description (str): Detailed description of the field
            - created_at (str): Timestamp of field creation
            - updated_at (str): Timestamp of last update
            - configurations (Dict): Field-specific settings
            - Other properties as defined in the database

    Raises:
        TypeError: If external_id is not a string
        ValueError: If the external ID fails validation (None, empty, whitespace, or invalid format) or if no field exists with the given external ID (business logic error)

    Note:
        The function performs a linear search through all fields to find a match
        for the external ID. The returned field data is read-only and should not
        be modified directly.
    """
    EXTERNAL_ID_RE = re.compile(r'^[A-Za-z0-9._-]+\Z')

    # Type validation
    if external_id is None:
        raise TypeError("external_id cannot be None")
    
    if not isinstance(external_id, str):
        raise TypeError(f"external_id must be a string, got {type(external_id).__name__}")
    # Value validation using Pydantic model
    external_id = external_id.strip()
    if not external_id:
        raise ValueError(
            "Invalid external_id format: external_id cannot be empty or only whitespace"
        )

    if not EXTERNAL_ID_RE.match(external_id):
        raise ValueError(
            "Invalid external_id format: external_id can only contain "
            "alphanumeric characters, dashes, underscores, and periods"
        )
        
        # Generic fallback for other validation errors
        raise ValueError(f"Invalid external_id format: {error_message}")
    
    # Business logic - search for the field
    for field in db.DB['fields'].values():
        if field.get('external_id') == external_id:
            return field
    
    # Business logic error - field not found
    raise ValueError(f"Field with external_id {external_id} not found")

@tool_spec(
    spec={
        'name': 'update_field_by_external_id',
        'description': """ Updates the details of an existing field by its external ID.
        
        This function updates the properties of a field identified by its external
        identifier. The function verifies that the provided body includes the correct
        external ID before performing the update. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the field to update.'
                },
                'body': {
                    'type': 'object',
                    'description': 'A dictionary containing the updated properties for the field. Defaults to None. If provided, can contain the following properties along with some other optional properties:',
                    'properties': {
                        'external_id': {
                            'type': 'string',
                            'description': 'Required. Must match the external_id in the URL'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Updated name of the field'
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Updated data type of the field'
                        },
                        'required': {
                            'type': 'boolean',
                            'description': 'Updated required status'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'Updated description'
                        },
                        'configurations': {
                            'type': 'object',
                            'description': 'Updated field-specific settings. If provided, dictionary key can be of stype string and value can be of any type.',
                            'properties': {},
                            'required': []
                        }
                    },
                    'required': [
                        'external_id'
                    ]
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def patch(external_id: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Updates the details of an existing field by its external ID.

    This function updates the properties of a field identified by its external
    identifier. The function verifies that the provided body includes the correct
    external ID before performing the update.

    Args:
        external_id (str): The external identifier of the field to update.
        body (Optional[Dict[str, Any]]): A dictionary containing the updated properties for the field. Defaults to None. If provided, can contain the following properties along with some other optional properties:
            - external_id (str): Required. Must match the external_id in the URL
            - name (Optional[str]): Updated name of the field
            - type (Optional[str]): Updated data type of the field
            - required (Optional[bool]): Updated required status
            - description (Optional[str]): Updated description
            - configurations (Optional[Dict[str, Any]]): Updated field-specific settings. If provided, dictionary key can be of stype string and value can be of any type.


    Returns:
        Dict[str, Any]: The updated field data, including all current properties of the field. It can have following keys with some other optional keys:
            - external_id (str): The provided external identifier
            - name (str): Name of the field
            - type (str): Data type of the field (e.g., 'text', 'number', 'date')
            - required (bool): Whether the field is required
            - description (str): Detailed description of the field
            - configurations (Dict[str, Any]): Field-specific settings. If provided key can be of stype string and value can be of any type.

    Raises:
        ValueError: If:
            - No field exists with the given external ID
            - The body is None
            - The body does not contain an 'external_id' field
            - The 'external_id' in the body does not match the URL parameter

    Note:
        The function performs a linear search through all fields to find a match
        for the external ID. The update is performed atomically and will either
        succeed completely or fail without partial updates. Only the properties
        provided in the body will be updated; existing properties not included
        in the body will remain unchanged.
    """
    field = None
    for f in db.DB['fields'].values():
        if f.get('external_id') == external_id:
            field = f
            break
    
    if not field:
        raise ValueError(f"Field with external_id {external_id} not found")
    
    if not body or 'external_id' not in body or body['external_id'] != external_id:
        raise ValueError("Body must contain 'external_id' matching the path parameter")
    
    field.update(body)
    return field

@tool_spec(
    spec={
        'name': 'delete_field_by_external_id',
        'description': """ Deletes a specific field from the system by its external ID.
        
        This function removes a field identified by its external identifier from
        the system. The function searches through all fields to find a match for
        the provided external ID before performing the deletion. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the field to delete.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete(external_id: str) -> None:
    """Deletes a specific field from the system by its external ID.

    This function removes a field identified by its external identifier from
    the system. The function searches through all fields to find a match for
    the provided external ID before performing the deletion.

    Args:
        external_id (str): The external identifier of the field to delete.

    Raises:
        TypeError: If external_id is not a string.
        ValueError: If external_id is empty or None, contains invalid characters,
                   exceeds maximum length, or if no field exists with the given external ID.

    Note:
        The function performs a linear search through all fields to find a match
        for the external ID. The deletion is permanent and cannot be undone.
    """
    # Type validation
    if not isinstance(external_id, str):
        raise TypeError("external_id must be a string")
    
    # Null/Empty checks
    if not external_id or external_id.isspace():
        raise ValueError("external_id cannot be empty or contain only whitespace")
    
    # Value validation - example: assuming external_id should be alphanumeric with underscores
    # and not exceed 100 characters (adjust as needed based on actual requirements)
    if len(external_id) > 100:
        raise ValueError("external_id exceeds maximum length of 100 characters")
    
    if not all(c.isalnum() or c == '_' or c == '-' for c in external_id):
        raise ValueError("external_id can only contain alphanumeric characters, underscores, and hyphens")
    
    # Check if field exists with the given external_id
    field_id = None
    for id, field in db.DB['fields'].items():
        if field.get('external_id') == external_id:
            field_id = id
            break
    
    if field_id is None:
        raise ValueError(f"Field with external_id {external_id} not found")
    
    del db.DB['fields'][field_id] 