"""
Contact Type Management by External ID Module for Workday Strategic Sourcing API Simulation.

This module provides functionality for managing contact types using their external
identifiers in the Workday Strategic Sourcing system. It supports updating and
deleting contact types through their external IDs, with proper validation and
error handling. The module enables comprehensive contact type management through
external identifiers.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Tuple, Optional
from .SimulationEngine import db
from .SimulationEngine.custom_errors import (
    InvalidInputError,
    ResourceNotFoundError,
    DatabaseStructureError
)

@tool_spec(
    spec={
        'name': 'update_contact_type_by_external_id',
        'description': """ Updates the details of an existing contact type using its external ID.
        
        This function allows for the modification of an existing contact type's properties
        by searching for it using its external identifier. It performs validation checks
        to ensure the update is valid and the contact type exists before applying the
        changes. The function supports partial updates of contact type properties. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The unique external identifier of the contact type to update.'
                },
                'body': {
                    'type': 'object',
                    'description': """ A dictionary containing the updated properties for
                    the contact type. The dictionary must include: """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "contact_types"'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Contact type identifier'
                        },
                        'external_id': {
                            'type': 'string',
                            'description': 'Contact type external identifier (max 255 characters)'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Contact type name (max 255 characters)'
                        }
                    },
                    'required': [
                        'type',
                        'id',
                        'external_id',
                        'name'
                    ]
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def patch(external_id: str, body: Optional[Dict] = None) -> Tuple[Dict, int]:
    """Updates the details of an existing contact type using its external ID.

    This function allows for the modification of an existing contact type's properties
    by searching for it using its external identifier. It performs validation checks
    to ensure the update is valid and the contact type exists before applying the
    changes. The function supports partial updates of contact type properties.

    Args:
        external_id (str): The unique external identifier of the contact type to update.
        body (Optional[Dict]): A dictionary containing the updated properties for
            the contact type. The dictionary must include:
            - type (str): Object type, should always be "contact_types"
            - id (int): Contact type identifier
            - external_id (str): Contact type external identifier (max 255 characters)
            - name (str): Contact type name (max 255 characters)

    Returns:
        Tuple[Dict, int]: A tuple containing:
            - An error message if the body is missing or if the external_id in the body doesn't
                match the URL parameter or if contact type is not found.
                This is a dictionary with the key "error" and the value is the error message.
            - Dict: The updated contact type data if successful, including:
                - id (int): Internal identifier of the contact type
                - external_id (str): External identifier of the contact type
                - All updated fields from the body
            - int: The HTTP status code:
                - 200: Contact type successfully updated
                - 400: Invalid request or mismatched external_id
                - 404: Contact type not found


    Note:
        The function performs a partial update, meaning only the fields provided
        in the body will be updated. All other fields will remain unchanged.
    """
    for contact_type_id, contact_type in db.DB["suppliers"]["contact_types"].items():
        if contact_type.get("external_id") == external_id:
            if not body:
                return {"error": "Body is required"}, 400
            if body.get("external_id") != external_id:
                return {"error": "External id in body must match url"}, 400
            contact_type.update(body)
            db.DB["suppliers"]["contact_types"][contact_type_id] = contact_type
            return contact_type, 200
    return {"error": "Contact type not found"}, 404

@tool_spec(
    spec={
        'name': 'delete_contact_type_by_external_id',
        'description': """ Deletes a contact type from the system using its external ID.
        
        This function removes a contact type from the database by searching for it
        using its external identifier. It performs validation to ensure the external_id
        is valid and the contact type exists before deletion. The function raises
        appropriate custom errors for different failure scenarios. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ The unique external identifier of the contact type to delete.
                    Must be a non-empty string. """
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete(external_id: str) -> str:
    """Deletes a contact type from the system using its external ID.

    This function removes a contact type from the database by searching for it
    using its external identifier. It performs validation to ensure the external_id
    is valid and the contact type exists before deletion. The function raises
    appropriate custom errors for different failure scenarios.

    Args:
        external_id (str): The unique external identifier of the contact type to delete.
            Must be a non-empty string.

    Returns:
        str: A success message indicating the contact type was successfully deleted.

    Raises:
        InvalidInputError: If the external_id is not a valid string or is empty.
        ResourceNotFoundError: If no contact type is found with the specified external_id.
        DatabaseStructureError: If the database structure is invalid or missing expected keys.

    Note:
        This function performs a permanent deletion. The contact type cannot be
        recovered after successful deletion.
    """
    # Validate input
    if not isinstance(external_id, str) or not external_id.strip():
        raise InvalidInputError("external_id must be a non-empty string")

    # Safely access the database structure
    try:
        suppliers = db.DB.get("suppliers")
        if not suppliers:
            raise DatabaseStructureError("Database structure is invalid: 'suppliers' key not found")
        
        contact_types = suppliers.get("contact_types")
        if not contact_types:
            raise DatabaseStructureError("Database structure is invalid: 'contact_types' key not found")
    except AttributeError:
        raise DatabaseStructureError("Database structure is invalid or corrupted")

    # Find and delete the contact type
    contact_type_id_to_delete = None
    for contact_type_id, contact_type in contact_types.items():
        if contact_type.get("external_id") == external_id:
            contact_type_id_to_delete = contact_type_id
            break
    
    # Raise error if contact type not found
    if contact_type_id_to_delete is None:
        raise ResourceNotFoundError(f"Contact type with external_id '{external_id}' not found")

    # Delete the contact type
    del db.DB["suppliers"]["contact_types"][contact_type_id_to_delete]
    
    # Return success message
    return f"Contact type with external_id '{external_id}' successfully deleted"
