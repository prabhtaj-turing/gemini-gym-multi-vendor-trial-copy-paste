"""
This module provides comprehensive functionality for managing custom fields in the Workday Strategic Sourcing system.
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Optional, Any
import uuid
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_custom_fields',
        'description': 'Returns a list of custom fields for the specified criteria.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filter': {
                    'type': 'object',
                    'description': """ A dictionary containing field attributes and their desired values for filtering.
                    If None, returns all fields. Supported filters: """,
                    'properties': {
                        'group_id_equals': {
                            'type': 'string',
                            'description': 'ID of the group for which fields should be selected'
                        },
                        'target_object_equals': {
                            'type': 'string',
                            'description': 'Find custom fields by target class name'
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def get(filter: Optional[Dict] = None) -> Dict:
    """
    Returns a list of custom fields for the specified criteria.

    Args:
        filter (Optional[Dict]): A dictionary containing field attributes and their desired values for filtering.
                               If None, returns all fields. Supported filters:
                               - group_id_equals (Optional[str]): ID of the group for which fields should be selected
                               - target_object_equals (Optional[str]): Find custom fields by target class name
    Returns:
        Dict: A list of field objects matching the filter criteria, or all fields if no filter is provided.
            Contains any of the following fields:
                - type (str): Field type
                - id (str): Field identifier string
                - group (str): Field group identifier string
                - name (str): Field name (max 255 characters)
                - attributes (dict): Field attributes containing:
                    - name (str): Field name (max 255 characters)
                    - target_object (str): Field object type string, one of:
                        - "PROJECT"
                        - "RFP"
                        - "SUPPLIER_COMPANY"
                    - data_type (str): OpenAPI data type, one of:
                        - "string"
                        - "number"
                        - "integer"
                        - "boolean"
                        - "array"
                        - "object"
                    - type_description (str): Internal name and meaning of each field, one of:
                        - "Checkbox"
                        - "File"
                        - "Short Text"
                        - "Paragraph"
                        - "Date"
                        - "Integer"
                        - "Currency"
                        - "Decimal"
                        - "Single Select"
                        - "Multiple Select"
                        - "URL"
                        - "Lookup"
                        - "Related"
                    - position (int): Field order position on the UI
                    - required (bool): Identifies whether the field is required
                - relationships (dict): Field relationship containing:
                    - group (dict): Reference to the field group where the field belongs to
                        - data (dict): Field group data containing:
                            - type (str): Object type, should always be "field_groups"
                            - id (int): Field group identifier string
                - links (dict): List of related links containing:
                    - self (str): Normalized link to the resource
    """
    if filter is None:
        return list(db.DB["fields"]["fields"].values())
    else:
        filtered_fields = []
        for field in db.DB["fields"]["fields"].values():
            match = True
            for key, value in filter.items():
                if key not in field or field[key] != value:
                    match = False
                    break
            if match:
                filtered_fields.append(field)
        return filtered_fields

@tool_spec(
    spec={
        'name': 'create_custom_field',
        'description': """ Create a field with given parameters.
        
        For fields with target_object set to RFP, group relationship should be omitted. It is required to specify the relationship for all other target objects. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'new_id': {
                    'type': 'string',
                    'description': 'The unique identifier for the new field. If not provided, the system will generate a new ID.'
                },
                'options': {
                    'type': 'object',
                    'description': 'A dictionary defining the properties, attributes, and relationships for a new custom data field. Must contain the following required fields:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Field type'
                        },
                        'group': {
                            'type': 'string',
                            'description': 'Field group identifier string'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Field name (max 255 characters)'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Field attributes containing the following required fields:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Field name (max 255 characters)'
                                },
                                'target_object': {
                                    'type': 'string',
                                    'description': 'Field object type, one of ["PROJECT", "RFP", "SUPPLIER_COMPANY"].'
                                },
                                'type_description': {
                                    'type': 'string',
                                    'description': 'Internal name and meaning of each field, one of ["Checkbox", "File", "Short Text", "Paragraph", "Date", "Integer", "Currency", "Decimal", "Single Select", "Multiple Select", "URL", "Lookup", "Related"].'
                                },
                                'required': {
                                    'type': 'boolean',
                                    'description': 'Identifies whether the field is required'
                                }
                            },
                            'required': [
                                'name',
                                'target_object',
                                'type_description',
                                'required'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Optional field relationships containing the following key:',
                            'properties': {
                                'group': {
                                    'type': 'object',
                                    'description': 'Contains details about the field group, including:',
                                    'properties': {
                                        'data': {
                                            'type': 'object',
                                            'description': 'Object representing the field group reference with:',
                                            'properties': {
                                                'type': {
                                                    'type': 'string',
                                                    'description': 'The type of the related resource (e.g., "field_groups").'
                                                },
                                                'id': {
                                                    'type': 'integer',
                                                    'description': 'The unique identifier of the related field group.'
                                                }
                                            },
                                            'required': [
                                                'type',
                                                'id'
                                            ]
                                        }
                                    },
                                    'required': [
                                        'data'
                                    ]
                                }
                            },
                            'required': [
                                'group'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'group',
                        'name',
                        'attributes'
                    ]
                }
            },
            'required': []
        }
    }
)
def post(new_id: str = None, options: Dict[str, Any] = {}) -> Optional[Dict[str, Any]]:
    """
    Create a field with given parameters.

    For fields with target_object set to RFP, group relationship should be omitted. It is required to specify the relationship for all other target objects.

    Args:
        new_id (str): The unique identifier for the new field. If not provided, the system will generate a new ID.
        options (Dict[str, Any]): A dictionary defining the properties, attributes, and relationships for a new custom data field. Must contain the following required fields:
            - type (str): Field type
            - group (str): Field group identifier string
            - name (str): Field name (max 255 characters)
            - attributes (Dict[str, Any]): Field attributes containing the following required fields:
                - name (str): Field name (max 255 characters)
                - target_object (str): Field object type, one of ["PROJECT", "RFP", "SUPPLIER_COMPANY"].
                - type_description (str): Internal name and meaning of each field, one of ["Checkbox", "File", "Short Text", "Paragraph", "Date", "Integer", "Currency", "Decimal", "Single Select", "Multiple Select", "URL", "Lookup", "Related"].
                - required (bool): Identifies whether the field is required
            - relationships (Optional[Dict[str, Any]]): Optional field relationships containing the following key:
                - group (Dict[str, Any]): Contains details about the field group, including:
                    - data (Dict[str, Any]): Object representing the field group reference with:
                        - type (str): The type of the related resource (e.g., "field_groups").
                        - id (int): The unique identifier of the related field group.


    Returns:
        Optional[Dict[str, Any]]: The created field object if successful, None if a field with the given ID already exists. Contains any of the following fields:
            - type (str): Field type
                - field_id (str): Field identifier string
                - group (str): Field group identifier string
                - name (str): Field name (max 255 characters)
                - attributes (dict): Field attributes containing:
                    - name (str): Field name (max 255 characters)
                    - target_object (str): Field object type string, one of:
                        - "PROJECT"
                        - "RFP"
                        - "SUPPLIER_COMPANY"
                    - data_type (str): OpenAPI data type, one of:
                        - "string"
                        - "number"
                        - "integer"
                        - "boolean"
                        - "array"
                        - "object"
                    - type_description (str): Internal name and meaning of each field, one of:
                        - "Checkbox"
                        - "File"
                        - "Short Text"
                        - "Paragraph"
                        - "Date"
                        - "Integer"
                        - "Currency"
                        - "Decimal"
                        - "Single Select"
                        - "Multiple Select"
                        - "URL"
                        - "Lookup"
                        - "Related"
                    - position (int): Field order position on the UI
                    - required (bool): Identifies whether the field is required
                - relationships (dict): Field relationship containing:
                    - group (dict): Reference to the field group where the field belongs to
                        - data (dict): Field group data containing:
                            - type (str): Object type, should always be "field_groups"
                            - id (int): Field group identifier string
                - links (dict): List of related links containing:
                    - self (str): Normalized link to the resource
    """
    if new_id is None:
        new_id = str(uuid.uuid4())
    if new_id not in db.DB["fields"]["fields"].keys():
        db.DB["fields"]["fields"][new_id] = options
        return options
    else:
        return None 
