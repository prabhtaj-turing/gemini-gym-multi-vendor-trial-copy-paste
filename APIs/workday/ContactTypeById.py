"""
Contact Type Management by ID Module for Workday Strategic Sourcing API Simulation.

This module provides functionality for managing contact types using their unique
internal identifiers in the Workday Strategic Sourcing system. It supports updating
and deleting contact types, with proper validation and error handling. The module
enables comprehensive contact type management through internal identifiers.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Tuple, Optional, Any
from .SimulationEngine import db
from .SimulationEngine.custom_errors import ContactTypeNotFoundError, ValidationError, ResourceNotFoundError
from .SimulationEngine.models import ContactTypePatchInput

@tool_spec(
    spec={
        'name': 'update_contact_type_by_id',
        'description': 'Updates the details of an existing contact type.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': """ The unique internal identifier of the contact type to update.
                    Must be a positive integer. """
                },
                'body': {
                    'type': 'object',
                    'description': """ A dictionary containing the updated properties for
                    the contact type. The dictionary must include: """,
                    'properties': {
                        'id': {
                            'type': 'integer',
                            'description': 'Contact type identifier (must match the URL parameter)'
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "contact_types"'
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
                        'id',
                        'type',
                        'external_id',
                        'name'
                    ]
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def patch(id: int, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Updates the details of an existing contact type.

    Args:
        id (int): The unique internal identifier of the contact type to update.
            Must be a positive integer.
        body (Optional[Dict[str, Any]]): A dictionary containing the updated properties for
            the contact type. The dictionary must include:
            - id (int): Contact type identifier (must match the URL parameter)
            - type (str): Object type, should always be "contact_types"
            - external_id (str): Contact type external identifier (max 255 characters)
            - name (str): Contact type name (max 255 characters)

    Returns:
        Dict[str, Any]: The updated contact type data
            - id (int): Contact type identifier
            - type (str): Object type, should always be "contact_types"
            - external_id (str): Contact type external identifier (max 255 characters)
            - name (str): Contact type name (max 255 characters)

    Raises:
        ValidationError: If input validation fails or body is missing
        ContactTypeNotFoundError: If contact type with specified ID is not found

    Note:
        The function performs a partial update, meaning only the fields provided
        in the body will be updated. All other fields will remain unchanged.
    """
    try:
        contact_types_data = db.DB["suppliers"]["contact_types"]
        
        # Validate id parameter
        if not isinstance(id, int):
            raise ValidationError("Contact type ID must be an integer")
        
        if id <= 0:
            raise ValidationError("Contact type ID must be a positive integer")
        
        # Check if contact type exists
        contact_type = contact_types_data.get(id)
        if not contact_type:
            raise ContactTypeNotFoundError(f"Contact type with ID {id} not found")
        
        # Validate body parameter
        if body is None:
            raise ValidationError("Body is required")
        
        # Validate required fields in body
        if "id" not in body:
            raise ValidationError("ID field is required in body")
              
        if body["id"] != id:
            raise ValidationError("ID in body must match the URL parameter")
        
        # Use Pydantic model for validation
        validated_body: Optional[ContactTypePatchInput] = None
        # Pydantic will raise ValidationError if 'body' does not match the model
        validated_body = ContactTypePatchInput(**body)

        
        # Convert validated body back to dict for update
        update_data = validated_body.model_dump(exclude_none=True)
        
        contact_type.update(update_data)
        return contact_type
        
    except (ValidationError, ContactTypeNotFoundError):
        # Re-raise custom errors as-is
        raise
    except Exception as e:
        raise ValidationError(str(e))

@tool_spec(
    spec={
        'name': 'delete_contact_type_by_id',
        'description': 'Deletes a contact type from the system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': """ The unique internal identifier of the contact type to delete.
                    Must be a positive integer greater than 0. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: int) -> Tuple[Dict, int]:
    """Deletes a contact type from the system.

    Args:
        id (int): The unique internal identifier of the contact type to delete.
            Must be a positive integer greater than 0.

    Returns:
        Tuple[Dict, int]: A tuple containing:
            - Dict: An empty dictionary if successful
            - int: The HTTP status code:
                - 204: Contact type successfully deleted
                - 404: Contact type not found

    Raises:
        ValidationError: If the id parameter is not a positive integer.
        ResourceNotFoundError: If the contact type with the specified id is not found.
    """
    # Input validation for id parameter
    if not isinstance(id, int):
        raise ValidationError("Contact type ID must be an integer")
    
    if id <= 0:
        raise ValidationError("Contact type ID must be a positive integer")
    
    # Check if contact type exists
    if id not in db.DB["suppliers"]["contact_types"]:
        raise ResourceNotFoundError(f"Contact type with ID {id} not found")
    
    # Delete the contact type
    del db.DB["suppliers"]["contact_types"][id]
    return {}, 204 