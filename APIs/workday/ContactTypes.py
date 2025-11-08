"""
Contact Types Management Module for Workday Strategic Sourcing API Simulation.

This module provides functionality for managing contact types in the Workday
Strategic Sourcing system. It supports retrieving a list of all contact types
and creating new contact types with specified parameters. The module enables
comprehensive contact type management and configuration capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Tuple, Optional
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_contact_types',
        'description': 'Retrieves a list of all contact types in the system.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> Tuple[List[Dict], int]:
    """Retrieves a list of all contact types in the system.

    Returns:
        Tuple[List[Dict], int]: A tuple containing:
            - List[Dict]: A list of dictionaries, where each dictionary represents
                a contact type containing:
                - type (str): Object type, should always be "contact_types"
                - id (int): Contact type identifier
                - external_id (str): Contact type external identifier (max 255 characters)
                - name (str): Contact type name (max 255 characters)
            - int: The HTTP status code (200 for success)
    """
    return list(db.DB["suppliers"]["contact_types"].values()), 200

@tool_spec(
    spec={
        'name': 'create_contact_type',
        'description': """ Creates a new contact type with the specified parameters.
        
        This function allows for the creation of a new contact type in the system
        with the provided configuration and properties. The function validates the
        input and ensures all required fields are present. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'body': {
                    'type': 'object',
                    'description': """ A dictionary containing the properties and
                    configuration for the new contact type. The dictionary should
                    include:
                    Defaults to None. """,
                    'properties': {
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
                        'type',
                        'external_id',
                        'name'
                    ]
                }
            },
            'required': []
        }
    }
)
def post(body: Optional[Dict] = None) -> Tuple[Dict, int]:
    """Creates a new contact type with the specified parameters.

    This function allows for the creation of a new contact type in the system
    with the provided configuration and properties. The function validates the
    input and ensures all required fields are present.

    Args:
        body (Optional[Dict]): A dictionary containing the properties and
            configuration for the new contact type. The dictionary should
            include:
            - type (str): Object type, should always be "contact_types"
            - external_id (str): Contact type external identifier (max 255 characters)
            - name (str): Contact type name (max 255 characters)
            Defaults to None.

    Returns:
        Tuple[Dict, int]: A tuple containing:
            - An error message if the body is missing or if required fields are not
                provided in the body. This is a dictionary with the key "error" and the value is the error message.
            - Dict: The created contact type data if successful, including:
                - id (int): System-generated unique identifier
                - All fields provided in the body
            - int: The HTTP status code:
                - 201: Contact type successfully created
                - 400: Invalid request or missing required fields
    """
    if not body:
        return {"error": "Body is required"}, 400
    
    contact_type_id = len(db.DB["suppliers"]["contact_types"]) + 1
    contact_type = {"id": contact_type_id, **body}
    db.DB["suppliers"]["contact_types"][contact_type_id] = contact_type
    return contact_type, 201 