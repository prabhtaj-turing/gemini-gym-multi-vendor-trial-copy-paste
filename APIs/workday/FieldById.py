"""
This module provides functionality for managing fields by their unique identifiers
in the Workday Strategic Sourcing system. It supports retrieving, updating, and
deleting specific fields using their internal IDs, with robust error handling
for both string and integer ID formats.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, Union
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_field_details_by_id',
        'description': 'Retrieves the details of an existing field using its internal identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The internal identifier of the field to retrieve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get(id: str) -> Optional[Dict[str, Union[str, int, bool, dict, None]]]:
    """Retrieves the details of an existing field using its internal identifier.
    
    Args:
        id (str): The internal identifier of the field to retrieve.

    Returns:
        Optional[Dict[str, Union[str, int, bool, dict, None]]]: The field object containing all its properties or None if the field does not exist. Contains any of the following fields:
            - type (str): Field type
            - id (str): Field identifier string
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
            - relationships (Dict[str, Dict[str, Union[str, int]]]): Field relationship containing:
                - group (Dict[str, Dict[str, Union[str, int]]]): Reference to the field group where the field belongs to
                    - data (Dict[str, Union[str, int]]): Field group data containing:
                        - type (str): Object type, should always be "field_groups"
                        - id (int): Field group identifier string
            - links (Dict[str, str]): List of related links containing:
                - self (str): Normalized link to the resource
    """
    # Input validation
    if id is None:
        return None
    
    # Check if id is a string
    if isinstance(id, str):
        # First try direct string lookup
        if id in db.DB["fields"]["fields"]:
            return db.DB["fields"]["fields"][id]
        
        # Try to convert to int if possible
        try:
            int_id = int(id)
            # Check if the integer key exists
            if int_id in db.DB["fields"]["fields"]:
                return db.DB["fields"]["fields"][int_id]
            # Check if the string version of the integer key exists
            if str(int_id) in db.DB["fields"]["fields"]:
                return db.DB["fields"]["fields"][str(int_id)]
        except (ValueError, TypeError):
            # Not a valid integer string
            pass
    
    # Check if id is an integer
    elif isinstance(id, int):
        # Try direct integer lookup
        if id in db.DB["fields"]["fields"]:
            return db.DB["fields"]["fields"][id]
        
        # Try string version lookup
        str_id = str(id)
        if str_id in db.DB["fields"]["fields"]:
            return db.DB["fields"]["fields"][str_id]
    
    # Not found or invalid type
    return None

@tool_spec(
    spec={
        'name': 'update_field_details_by_id',
        'description': """ Updates the details of an existing field using its internal identifier.
        
        Please note, that request body must include an id attribute with the value of your field unique identifier,the same one you passed as argument. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The internal identifier of the field to update.'
                },
                'options': {
                    'type': 'object',
                    'description': """ A dictionary containing the field properties to update.
                    Must include an 'id' field matching the path parameter. """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Field type'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Field name (max 255 characters)'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Field attributes containing:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Field name (max 255 characters)'
                                },
                                'target_object': {
                                    'type': 'string',
                                    'description': 'Field object type. One of "PROJECT", "RFP", "SUPPLIER_COMPANY".'
                                },
                                'type_description': {
                                    'type': 'string',
                                    'description': 'Internal name and meaning of each field. One of "Checkbox", "File", "Short Text", "Paragraph", "Date", "Integer", "Currency", "Decimal", "Single Select", "Multiple Select", "URL", "Lookup", "Related".'
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
                            'description': 'Field relationship containing:',
                            'properties': {
                                'group': {
                                    'type': 'object',
                                    'description': """ Reference to the field group where the field belongs to.
                                             Note: Must be null for fields with target_object set to RFP, and required for all other fields """,
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': "Object type, should always be 'field_groups'."
                                        },
                                        'id': {
                                            'type': 'string',
                                            'description': 'Field group identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
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
                        'name',
                        'attributes',
                        'relationships'
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
def patch(id: str, options: Dict[str, Union[str, int, bool, dict, None]]) -> Optional[Dict[str, Union[str, int, bool, dict, None]]]:
    """Updates the details of an existing field using its internal identifier.

    Please note, that request body must include an id attribute with the value of your field unique identifier,the same one you passed as argument.

    Args:
        id (str): The internal identifier of the field to update.
        options (Dict[str, Union[str, int, bool, dict, None]]): A dictionary containing the field properties to update.
                        Must include an 'id' field matching the path parameter.
                - type (str): Field type
                - name (str): Field name (max 255 characters)
                - attributes (Dict[str, Union[str, int, bool]]): Field attributes containing:
                    - name (str): Field name (max 255 characters)
                    - target_object (str): Field object type. One of "PROJECT", "RFP", "SUPPLIER_COMPANY".
                    - type_description (str): Internal name and meaning of each field. One of "Checkbox", "File", "Short Text", "Paragraph", "Date", "Integer", "Currency", "Decimal", "Single Select", "Multiple Select", "URL", "Lookup", "Related".
                    - required (bool): Identifies whether the field is required
                - relationships (Dict[str, Dict[str, str]]): Field relationship containing:
                    - group (Dict[str, Union[str, Dict[str, Union[str, int]]]]): Reference to the field group where the field belongs to.
                        Note: Must be null for fields with target_object set to RFP, and required for all other fields
                        - type (str): Object type, should always be 'field_groups'.
                        - id (str): Field group identifier string.
    Returns:
        Optional[Dict[str, Union[str, int, bool, dict, None]]]: The updated field object or None if the field does not exist. Contains any of the following fields:
            - type (str): Field type
            - id (str): Field identifier string
            - group (str): Field group identifier string
            - name (str): Field name (max 255 characters)
            - attributes (Dict[str, Union[str, int, bool]]): Field attributes containing:
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
            - relationships (Dict[str, Dict[str, Union[str, int]]]): Field relationship containing:
                - group (Dict[str, Dict[str, Union[str, int]]]): Reference to the field group where the field belongs to
                    - data (Dict[str, Union[str, int]]): Field group data containing:
                        - type (str): Object type, should always be "field_groups"
                        - id (int): Field group identifier string
            - links (Dict[str, str]): List of related links containing:
                - self (str): Normalized link to the resource
    """
    if str(id) in db.DB["fields"]["fields"]:
        db.DB["fields"]["fields"][id] = options
        return options
    try:
        if int(id) in db.DB["fields"]["fields"]:
            db.DB["fields"]["fields"][int(id)] = options
            return options
        else:
            return None
    except KeyError:
        return None

@tool_spec(
    spec={
        'name': 'delete_field_by_id',
        'description': 'Deletes a field using its internal identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The internal identifier of the field to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: str) -> bool:
    """Deletes a field using its internal identifier.

    Args:
        id (str): The internal identifier of the field to delete.
    
    Returns:
        bool: True if the field was successfully deleted, False if the field does not exist.

    """
    if str(id) in db.DB["fields"]["fields"]:
        del db.DB["fields"]["fields"][str(id)]
        return True
    try:
        if int(id) in db.DB["fields"]["fields"]:
            del db.DB["fields"]["fields"][int(id)]
            return True
        else:
            return False
    except KeyError:
        return False

