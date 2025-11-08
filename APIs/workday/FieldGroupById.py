"""
This module provides functionality for managing field groups by their unique
identifiers in the Workday Strategic Sourcing system. It supports retrieving,
updating, and deleting specific field groups using their internal IDs.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, Optional, Union
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_field_group_by_id',
        'description': """ Retrieves the details of a specific field group by its ID.
        
        This function returns the complete details of a field group identified by its
        unique identifier. The function supports both string and integer ID formats. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the field group to retrieve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get(id: str) -> Optional[Dict]:
    """Retrieves the details of a specific field group by its ID.

    This function returns the complete details of a field group identified by its
    unique identifier. The function supports both string and integer ID formats.

    Args:
        id (str): The unique identifier of the field group to retrieve.

    Returns:
        Optional[Dict]: A dictionary containing the field group details if found,
            including any of the following fields:
                - type (str): Object type, should always be "field_groups"
                - id (str): Field group identifier string
                - fields (List): List of fields belonging to this group
                - name (str): Field group name (max 255 characters)
                - description (str): Field group description (max 255 characters)
                - attributes (dict): Field group attributes containing:
                    - target_object (str): Field group object type string, one of:
                        - "PROJECT"
                        - "SUPPLIER_COMPANY"
                        - "RFP"
                    - name (str): Field group name (max 255 characters)
                    - position (int): Field group position on the UI
    """
    if id in db.DB["fields"]["field_groups"]:
        return db.DB["fields"]["field_groups"][id]
    else:
        return None

@tool_spec(
    spec={
        'name': 'update_field_group_by_id',
        'description': 'Updates the details of an existing field group.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the field group to update.'
                },
                'options': {
                    'type': 'object',
                    'description': """ A dictionary containing the updated properties for the
                    field group, including any of the following fields: """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "field_groups"'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Field group identifier string. Same as the id parameter.'
                        },
                        'fields': {
                            'type': 'array',
                            'description': 'List of field identifiers belonging to this group',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Field group name (max 255 characters)'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'Field group description (max 255 characters)'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Field group attributes containing:',
                            'properties': {
                                'target_object': {
                                    'type': 'string',
                                    'description': 'Field group object type string, one of ["PROJECT", "RFP", "SUPPLIER_COMPANY"]'
                                },
                                'name': {
                                    'type': 'string',
                                    'description': 'Field group name (max 255 characters)'
                                }
                            },
                            'required': [
                                'target_object',
                                'name'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'id',
                        'fields',
                        'name',
                        'description',
                        'attributes'
                    ]
                }
            },
            'required': [
                'id',
                'options'
            ]
        }
    }
)
def patch(id: str, options: Dict[str, Any]) -> Optional[Dict]:
    """Updates the details of an existing field group.

    Args:
        id (str): The unique identifier of the field group to update.
        options (Dict[str, Any]): A dictionary containing the updated properties for the
            field group, including any of the following fields:
            - type (str): Object type, should always be "field_groups"
            - id (int): Field group identifier string. Same as the id parameter.
            - fields (List[str]): List of field identifiers belonging to this group
            - name (str): Field group name (max 255 characters)
            - description (str): Field group description (max 255 characters)
            - attributes (dict): Field group attributes containing:
                - target_object (str): Field group object type string, one of ["PROJECT", "RFP", "SUPPLIER_COMPANY"]
                - name (str): Field group name (max 255 characters)

    Returns:
        Optional[Dict]: The updated field group data if the update was successful,
            including all current properties of the field group. 
            - type (str): Object type, should always be "field_groups"
            - id (str): Field group identifier string
            - fields (List): List of fields belonging to this group
            - name (str): Field group name (max 255 characters)
            - description (str): Field group description (max 255 characters)
            - attributes (dict): Field group attributes containing:
                - target_object (str): Field group object type string, one of ["PROJECT", "RFP", "SUPPLIER_COMPANY"]
                - name (str): Field group name (max 255 characters)
                - position (int): Field group position on the UI
            
            Returns None if:
            - The field group does not exist
            - The ID format is invalid
    """
    if id in db.DB["fields"]["field_groups"]:
        db.DB["fields"]["field_groups"][id] = options
        return options
    else:
        return None

@tool_spec(
    spec={
        'name': 'delete_field_group_by_id',
        'description': 'Deletes a specific field group from the system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the field group to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: str) -> bool:
    """Deletes a specific field group from the system.

    Args:
        id (str): The unique identifier of the field group to delete.

    Returns:
        bool: True if the field group was successfully deleted, False if:
            - The field group does not exist
            - The ID format is invalid
    """
    if id in db.DB["fields"]["field_groups"]:
        del db.DB["fields"]["field_groups"][id]
        return True
    else:
        return False