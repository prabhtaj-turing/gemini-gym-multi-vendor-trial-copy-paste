"""
This module provides functionality for managing field groups in the Workday
Strategic Sourcing system. It supports retrieving a list of all field groups
and creating new field groups with specified parameters. The module enables
comprehensive field group management and configuration capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Optional
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_field_groups',
        'description': 'Returns a list of field groups.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> List[Dict]:
    """Returns a list of field groups.

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary represents
            a field group containing any of the following fields:
                - type (str): Object type, should always be "field_groups"
                - id (str): Field group identifier string
                - fields (List[str]): List of field IDs belonging to this group
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
    return list(db.DB["fields"]["field_groups"].values())

@tool_spec(
    spec={
        'name': 'create_field_group',
        'description': 'Creates a new field group with the specified parameters.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the field group to be created.'
                },
                'description': {
                    'type': 'string',
                    'description': """ A detailed description of the field group.
                    Defaults to an empty string. """
                },
                'data': {
                    'type': 'object',
                    'description': "A dictionary defining the new field group's structure and attributes. Must contain the following required fields:",
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "field_groups"'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Field group name (max 255 characters)'
                        },
                        'fields': {
                            'type': 'array',
                            'description': 'List of field IDs belonging to this group',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Field group attributes containing the following required fields:',
                            'properties': {
                                'target_object': {
                                    'type': 'string',
                                    'description': 'Field group object type string, one of ["PROJECT", "SUPPLIER_COMPANY", "RFP"].'
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
                        'name',
                        'fields',
                        'attributes'
                    ]
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def post(name: str, description: str = "", data: Dict = {}) -> Dict:
    """Creates a new field group with the specified parameters.

    Args:
        name (str): The name of the field group to be created.
        description (str, optional): A detailed description of the field group.
            Defaults to an empty string.
        data (Dict, optional): A dictionary defining the new field group's structure and attributes. Must contain the following required fields:
            - type (str): Object type, should always be "field_groups"
            - name (str): Field group name (max 255 characters)
            - fields (List[str]): List of field IDs belonging to this group
            - attributes (dict): Field group attributes containing the following required fields:
                - target_object (str): Field group object type string, one of ["PROJECT", "SUPPLIER_COMPANY", "RFP"].
                - name (str): Field group name (max 255 characters)

    Returns:
        Dict: The created field group data, including:
            - type (str): Object type, should always be "field_groups"
            - id (str): Field group identifier string
            - fields (List[str]): List of field IDs belonging to this group
            - name (str): Field group name (max 255 characters)
            - description (str): Field group description (max 255 characters)
            - attributes (dict): Field group attributes containing:
                - target_object (str): Field group object type string, one of ["PROJECT", "SUPPLIER_COMPANY", "RFP"].
                - name (str): Field group name (max 255 characters)
                - position (int): Field group position on the UI
    """
    new_id = str(max(map(int, db.DB.get("fields", {}).get("field_groups", {}).keys()), default=0) + 1)
    new_field_group = {"id": new_id, "name": name, "description": description}
    db.DB["fields"]["field_groups"][new_id] = new_field_group
    return new_field_group
