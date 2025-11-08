"""
This module provides functionality for managing line items within event worksheets
in the Workday Strategic Sourcing system. It supports retrieving all line items
for a specific worksheet, creating individual line items, and bulk creating
multiple line items in a single operation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from .SimulationEngine import db

from .SimulationEngine.models import LineItemInput
from .SimulationEngine.custom_errors import ValidationError, NotFoundError, ConflictError
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.custom_errors import DataIntegrityError

@tool_spec(
    spec={
        'name': 'list_event_worksheet_line_items',
        'description': 'Returns a list of line items for the specified criteria.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to which the line items belong.'
                },
                'worksheet_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the worksheet to which the line items belong.'
                }
            },
            'required': [
                'event_id',
                'worksheet_id'
            ]
        }
    }
)
def get(event_id: int, worksheet_id: int) -> List[Dict]:
    """Returns a list of line items for the specified criteria.

    Args:
        event_id (int): The unique identifier of the event to which the line items belong.
        worksheet_id (int): The unique identifier of the worksheet to which the line items belong.

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary represents a line item
            containing any of the following keys:
            - type (str): Object type, should always be "line_items"
            - id (int): LineItem identifier string
            - event_id (str): ID of the associated event
            - worksheet_id (int): ID of the associated worksheet
            - attributes (dict): LineItem attributes containing:
                - data (dict): A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:
                    - data_identifier (str): Worksheet column identifier string
                    - value (any): Worksheet line item cell value
    
    Raises:
        TypeError: If event_id or worksheet_id are not integers.
        ValueError: If event_id or worksheet_id are not positive numbers.
        DataIntegrityError: If a line item object in the database is malformed
                            (e.g., missing 'event_id' or 'worksheet_id' keys).
    """
    # Runtime validation for input type
    if not isinstance(event_id, int):
        raise TypeError(f"Parameter 'event_id' must be an integer, but received type {type(event_id).__name__}.")
    if not isinstance(worksheet_id, int):
        raise TypeError(f"Parameter 'worksheet_id' must be an integer, but received type {type(worksheet_id).__name__}.")

    # Runtime validation for input value range
    if event_id <= 0:
        raise ValueError(f"Parameter 'event_id' must be a positive integer, but was {event_id}.")
    if worksheet_id <= 0:
        raise ValueError(f"Parameter 'worksheet_id' must be a positive integer, but was {worksheet_id}.")

    line_items = []
    for id, line_item in db.DB["events"]["line_items"].items():
        try:
            # Check if the line item matches the provided criteria
            str_event_id = str(event_id)
            if line_item["event_id"] == str_event_id and line_item["worksheet_id"] == worksheet_id:
                line_items.append(line_item)
        except KeyError as e:
            raise DataIntegrityError(
                f"Data integrity issue in line_item '{id}': missing required key {e}."
            ) from e
            
    return line_items

@tool_spec(
    spec={
        'name': 'create_event_worksheet_line_item',
        'description': 'Create a line item with given cell values.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to which the line item will belong.'
                },
                'worksheet_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the worksheet to which the line item will belong.'
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing the properties for the new line item, including:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "line_items"'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'LineItem attributes containing:',
                            'properties': {
                                'data': {
                                    'type': 'object',
                                    'description': 'A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:',
                                    'properties': {
                                        'data_identifier': {
                                            'type': 'string',
                                            'description': 'Worksheet column identifier string'
                                        },
                                        'value': {
                                            'type': 'string',
                                            'description': 'Worksheet line item cell value'
                                        }
                                    },
                                    'required': [
                                        'data_identifier',
                                        'value'
                                    ]
                                }
                            },
                            'required': [
                                'data'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Line item relationships containing:',
                            'properties': {
                                'worksheet': {
                                    'type': 'object',
                                    'description': 'Associated worksheet containing:',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "worksheets"'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Worksheet identifier string'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                }
                            },
                            'required': [
                                'worksheet'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'attributes',
                        'relationships'
                    ]
                }
            },
            'required': [
                'event_id',
                'worksheet_id',
                'data'
            ]
        }
    }
)
def post(event_id: int, worksheet_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a line item with given cell values.

    Args:
        event_id (int): The unique identifier of the event to which the line item will belong.
        worksheet_id (int): The unique identifier of the worksheet to which the line item will belong.
        data (Dict[str, Any]): A dictionary containing the properties for the new line item, including:
            - type (str): Object type, should always be "line_items"
            - attributes (Dict[str, Any]): LineItem attributes containing:
                - data (dict): A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:
                    - data_identifier (str): Worksheet column identifier string
                    - value (Union[str, int, float, bool]): Worksheet line item cell value
            - relationships (dict): Line item relationships containing:
                - worksheet (dict): Associated worksheet containing:
                    - type (str): Object type, should always be "worksheets"
                    - id (int): Worksheet identifier string

    Returns:
        Dict[str, Any]: The created line item data, including:
            - type (str): Object type, should always be "line_items"
            - event_id (str): ID of the associated event
            - worksheet_id (int): ID of the associated worksheet
            - attributes (dict): LineItem attributes containing:
                - data (dict): A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:
                    - data_identifier (str): Worksheet column identifier string
                    - value (Union[str, int, float, bool]): Worksheet line item cell value
            - relationships (dict): Line item relationships containing:
                - worksheet (dict): Associated worksheet containing:
                    - type (str): Object type, should always be "worksheets"
                    - id (int): Worksheet identifier string
    Raises:
        ValidationError: If the input data is malformed or fails validation.
        NotFoundError: If the specified event or worksheet does not exist.
        ConflictError: If the worksheet_id in the URL does not match the id in the payload.
    """
    # Runtime type validation for input parameters
    if not isinstance(event_id, int):
        raise ValidationError(f"event_id must be an integer, got {type(event_id).__name__}")
    
    if event_id < 0:
        raise ValidationError(f"event_id must be non-negative, got {event_id}")
    
    if not isinstance(worksheet_id, int):
        raise ValidationError(f"worksheet_id must be an integer, got {type(worksheet_id).__name__}")
    
    if worksheet_id < 0:
        raise ValidationError(f"worksheet_id must be non-negative, got {worksheet_id}")
    
    if not isinstance(data, dict):
        raise ValidationError(f"data must be a dictionary, got {type(data).__name__}")
    
    # Additional validation for data structure
    if not data:
        raise ValidationError("data cannot be empty")
    
    # 1. Validate the input payload using the Pydantic model
    try:
        validated_data = LineItemInput.model_validate(data)
    except PydanticValidationError as e:
        raise ValidationError(f"Invalid input data format: {e}") from e

    # 2. Check for consistency between URL parameter and payload data
    if worksheet_id != validated_data.relationships.worksheet.id:
        raise ConflictError(
            f"Worksheet ID in URL ({worksheet_id}) does not match "
            f"ID in payload ({validated_data.relationships.worksheet.id})."
        )

    # 3. Check for the existence of parent resources in the database
    # Convert integer event_id to string for database lookup since event IDs are stored as strings
    str_event_id = str(event_id)
    if str_event_id not in db.DB["events"]["events"]:
        raise NotFoundError(f"Event with id '{event_id}' not found.")
    if worksheet_id not in db.DB["events"]["worksheets"]:
        raise NotFoundError(f"Worksheet with id '{worksheet_id}' not found.")

    # 4. Safely create and store the new line item
    new_id = max(db.DB["events"]["line_items"].keys(), default=0) + 1
    
    # Convert the validated Pydantic model to a dict to ensure no extra fields are injected
    new_line_item = validated_data.model_dump()
    
    # Add server-side information
    new_line_item['id'] = new_id
    new_line_item['event_id'] = str_event_id
    
    db.DB["events"]["line_items"][new_id] = new_line_item
    
    return new_line_item

@tool_spec(
    spec={
        'name': 'create_multiple_event_worksheet_line_items',
        'description': 'Creates multiple line items in the specified event worksheet.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to which the line items will belong.'
                },
                'worksheet_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the worksheet to which the line items will belong.'
                },
                'data': {
                    'type': 'array',
                    'description': """ A list of dictionaries, where each dictionary contains
                    the properties for a new line item, including: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'type': {
                                'type': 'string',
                                'description': 'Object type, should always be "line_items"'
                            },
                            'attributes': {
                                'type': 'object',
                                'description': 'LineItem attributes containing:',
                                'properties': {
                                    'data': {
                                        'type': 'object',
                                        'description': 'A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:',
                                        'properties': {
                                            'data_identifier': {
                                                'type': 'string',
                                                'description': 'Worksheet column identifier string'
                                            },
                                            'value': {
                                                'type': 'object',
                                                'description': 'Worksheet line item cell value',
                                                'properties': {},
                                                'required': []
                                            }
                                        },
                                        'required': [
                                            'data_identifier',
                                            'value'
                                        ]
                                    }
                                },
                                'required': [
                                    'data'
                                ]
                            },
                            'relationships': {
                                'type': 'object',
                                'description': 'Line item relationships containing:',
                                'properties': {
                                    'worksheet': {
                                        'type': 'object',
                                        'description': 'Associated worksheet containing:',
                                        'properties': {
                                            'type': {
                                                'type': 'string',
                                                'description': 'Object type, should always be "worksheets"'
                                            },
                                            'id': {
                                                'type': 'integer',
                                                'description': 'Worksheet identifier string'
                                            }
                                        },
                                        'required': [
                                            'type',
                                            'id'
                                        ]
                                    }
                                },
                                'required': [
                                    'worksheet'
                                ]
                            }
                        },
                        'required': [
                            'type',
                            'attributes',
                            'relationships'
                        ]
                    }
                }
            },
            'required': [
                'event_id',
                'worksheet_id',
                'data'
            ]
        }
    }
)
def post_multiple(event_id: int, worksheet_id: int, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Creates multiple line items in the specified event worksheet.

    Args:
        event_id (int): The unique identifier of the event to which the line items will belong.
        worksheet_id (int): The unique identifier of the worksheet to which the line items will belong.
        data (List[Dict[str, Any]]): A list of dictionaries, where each dictionary contains
            the properties for a new line item, including:
            - type (str): Object type, should always be "line_items"
            - attributes (Dict[str, Any]): LineItem attributes containing:
                - data (Dict[str, Any]): A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:
                    - data_identifier (str): Worksheet column identifier string
                    - value (Any): Worksheet line item cell value
            - relationships (Dict[str, Any]): Line item relationships containing:
                - worksheet (Dict[str, Any]): Associated worksheet containing:
                    - type (str): Object type, should always be "worksheets"
                    - id (int): Worksheet identifier string

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a created
            line item containing:
            - type (str): Object type, should always be "line_items"
            - event_id (str): ID of the associated event
            - worksheet_id (int): ID of the associated worksheet
            - attributes (Dict[str, Any]): LineItem attributes containing:
                - data (Dict[str, Any]): A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:
                    - data_identifier (str): Worksheet column identifier string
                    - value (Any): Worksheet line item cell value
            - relationships (Dict[str, Any]): Line item relationships containing:
                - worksheet (Dict[str, Any]): Associated worksheet containing:
                    - type (str): Object type, should always be "worksheets"
                    - id (int): Worksheet identifier string
    
    Raises:
        TypeError: If event_id or worksheet_id are not integers, or if data is not a list.
        ValueError: If event_id or worksheet_id are negative, if the input `data` is None, 
            if any item in the list fails validation against the LineItemInput model, 
            or if an item's internal worksheet ID does not match the worksheet_id provided in the URL.
        NotFoundError: If the specified event_id or worksheet_id does not exist.

    """
    # Runtime type validation for input parameters
    if not isinstance(event_id, int):
        raise TypeError(f"event_id must be an integer, got {type(event_id).__name__}")
    if not isinstance(worksheet_id, int):
        raise TypeError(f"worksheet_id must be an integer, got {type(worksheet_id).__name__}")
    
    # Handle null data before type validation
    if data is None:
        raise ValueError("Request body cannot be null.")
    
    if not isinstance(data, list):
        raise TypeError(f"data must be a list, got {type(data).__name__}")
    
    # Non-negative ID validation
    if event_id < 0:
        raise ValueError(f"event_id must be non-negative, got {event_id}")
    if worksheet_id < 0:
        raise ValueError(f"worksheet_id must be non-negative, got {worksheet_id}")

    # 1. Validate that the parent resources (event and worksheet) exist.
    # Convert integer event_id to string for database lookup since event IDs are stored as strings
    str_event_id = str(event_id)
    if str_event_id not in db.DB["events"]["events"]:
        raise NotFoundError(f"Event with id '{event_id}' not found.")
    if worksheet_id not in db.DB["events"]["worksheets"]:
        raise NotFoundError(f"Worksheet with id '{worksheet_id}' not found.")

    # 2. Handle empty inputs for the data payload.
    if not data:
        return []  # Return an empty list if there's nothing to process.

    created_items = []
    # 3. Iterate through the list, validating and creating each item.
    for i, item_data in enumerate(data):
        try:
            # Validate the structure and types of each item using the Pydantic model.
            validated_item = LineItemInput.model_validate(item_data)

            # Cross-validate the worksheet ID in the payload against the one in the URL.
            if validated_item.relationships.worksheet.id != worksheet_id:
                raise ValueError(
                    f"Payload worksheet id ({validated_item.relationships.worksheet.id}) "
                    f"does not match URL worksheet id ({worksheet_id})."
                )

        except PydanticValidationError as e:
            # Wrap Pydantic's detailed error with context about which item failed.
            raise ValueError(f"Validation failed for line item at index {i}: {e}") from e
        except ValueError as e:
            # Re-raise value errors with context.
            raise ValueError(f"Validation failed for line item at index {i}: {e}") from e

        # 4. Generate a new ID and save the validated line item to the database.
        new_id = max(db.DB["events"]["line_items"].keys(), default=0) + 1
        new_line_item = {
            "id": new_id,
            "event_id": str_event_id,
            "worksheet_id": worksheet_id,
            **validated_item.model_dump()
        }
        db.DB["events"]["line_items"][new_id] = new_line_item
        created_items.append(new_line_item)

    return created_items