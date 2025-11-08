"""
This module provides functionality for managing individual line items within event
worksheets in the Workday Strategic Sourcing system. It supports retrieving,
updating, and deleting specific line items by their unique identifiers, with
validation to ensure the line items belong to the correct event and worksheet.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from .SimulationEngine import db
from .SimulationEngine.custom_errors import InvalidInputError, LineItemNotFound, LineItemMismatchError, NotFoundError, InvalidIdentifierError

@tool_spec(
    spec={
        'name': 'get_event_worksheet_line_item_by_id',
        'description': """ Retrieves the details of an existing line item. You need to supply the unique line item identifier that 
        
        was returned upon line item creation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to which the line item belongs.'
                },
                'worksheet_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the worksheet to which the line item belongs.'
                },
                'id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the line item to retrieve.'
                }
            },
            'required': [
                'event_id',
                'worksheet_id',
                'id'
            ]
        }
    }
)
def get(event_id: int, worksheet_id: int, id: int) -> Dict[str, Any]:
    """Retrieves the details of an existing line item. You need to supply the unique line item identifier that 
    was returned upon line item creation.

    Args:
        event_id (int): The unique identifier of the event to which the line item belongs.
        worksheet_id (int): The unique identifier of the worksheet to which the line item belongs.
        id (int): The unique identifier of the line item to retrieve.

    Returns:
        Dict[str, Any]: A dictionary containing the line item details, including:
            - type (str): Object type, should always be "line_items"
            - event_id (int): ID of the associated event
            - worksheet_id (int): ID of the associated worksheet
            - attributes (dict): LineItem attributes containing:
                - data (dict): A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:
                    - data_identifier (str): Worksheet column identifier string
                    - value (any): Worksheet line item cell value
            - relationships (dict): Line item relationships containing:
                - worksheet (dict): Associated worksheet containing:
                    - type (str): Object type, should always be "worksheets"
                    - id (int): Worksheet identifier string
    Raises:
        InvalidIdentifierError: If any of the provided identifiers (event_id,
                                              worksheet_id, id) are not positive integers.
        NotFoundError: If the line item is not found or does not belong to the specified event and worksheet.
    """
    # Validate that all provided IDs are positive integers.
    if not all(i > 0 for i in [event_id, worksheet_id, id]):
        raise InvalidIdentifierError("All identifiers must be positive integers.")

    # Safely access the nested line_items dictionary to prevent KeyErrors.
    line_items_table = db.DB.get("events", {}).get("line_items")
    if not line_items_table:
        raise NotFoundError("Line items table not found.")

    # First, try to find the line item using a string key, which is the format
    # after loading from a JSON file.
    line_item = line_items_table.get(str(id))

    # If not found, try a lookup using the integer key, which is the format when
    # the database is created in-memory for tests.
    if not line_item:
        line_item = line_items_table.get(id)

    
    # verify that it belongs to the correct parent event and worksheet.
    if (line_item and
            line_item.get("event_id") == str(event_id) and
            line_item.get("worksheet_id") == worksheet_id):
        return line_item

    raise NotFoundError("Line item not found or does not belong to the specified event and worksheet.")



@tool_spec(
    spec={
        'name': 'update_event_worksheet_line_item_by_id',
        'description': """ Updates the details of an existing line item. You need to supply the unique line item that was returned 
        
        upon line item creation. Please note, that request body must include the id attribute with the value of 
        your line item unique identifier (the same one you passed as argument) """,
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to which the line item belongs.'
                },
                'worksheet_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the worksheet to which the line item belongs.'
                },
                'id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the line item to update.'
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing the updated properties for the line item.',
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
                'id',
                'data'
            ]
        }
    }
)
def patch(event_id: int, worksheet_id: int, id: int, data: Dict) -> Optional[Dict]:
    """Updates the details of an existing line item. You need to supply the unique line item that was returned 
    upon line item creation. Please note, that request body must include the id attribute with the value of 
    your line item unique identifier (the same one you passed as argument)

    Args:
        event_id (int): The unique identifier of the event to which the line item belongs.
        worksheet_id (int): The unique identifier of the worksheet to which the line item belongs.
        id (int): The unique identifier of the line item to update.
        data (Dict): A dictionary containing the updated properties for the line item.
            - type (str): Object type, should always be "line_items"
            - attributes (dict): LineItem attributes containing:
                - data (dict): A hashmap where keys are data identifier strings for the columns in the worksheet, and values are cell values, where each value contains:
                    - data_identifier (str): Worksheet column identifier string
                    - value (Union[str, int, float, bool]): Worksheet line item cell value
            - relationships (dict): Line item relationships containing:
                - worksheet (dict): Associated worksheet containing:
                    - type (str): Object type, should always be "worksheets"
                    - id (int): Worksheet identifier string
    Returns:
        Optional[Dict]: The updated line item data if the update was successful,
            including all current properties of the line item. Returns None if:
            - The line item does not exist
            - The line item does not belong to the specified event and worksheet
            - The provided data does not include the correct line item ID
            The line item may contain any of the following keys:
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
    """
    if id in db.DB["events"]["line_items"] and db.DB["events"]["line_items"][id]["event_id"] == str(event_id) and db.DB["events"]["line_items"][id]["worksheet_id"] == worksheet_id and data.get("id") == id:
        db.DB["events"]["line_items"][id].update(data)
        return db.DB["events"]["line_items"][id]
    else:
        return None

@tool_spec(
    spec={
        'name': 'delete_event_worksheet_line_item_by_id',
        'description': 'Deletes a specific line item from the system.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to which the line item belongs.'
                },
                'worksheet_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the worksheet to which the line item belongs.'
                },
                'id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the line item to delete.'
                }
            },
            'required': [
                'event_id',
                'worksheet_id',
                'id'
            ]
        }
    }
)
def delete(event_id: int, worksheet_id: int, id: int) -> bool:
    """Deletes a specific line item from the system.

    Args:
        event_id (int): The unique identifier of the event to which the line item belongs.
        worksheet_id (int): The unique identifier of the worksheet to which the line item belongs.
        id (int): The unique identifier of the line item to delete.

    Returns:
        bool: True if the line item was successfully deleted.
    
    Raises:
        InvalidInputError: If any of the provided IDs are None or not positive integers.
        LineItemNotFound: If the line item with the specified 'id' does not exist.
        LineItemMismatchError: If the found line item does not belong to the specified event and worksheet.
    """
    # 1. Explicitly validate input for type, nulls, and range.
    if not all(isinstance(val, int) and val > 0 for val in [event_id, worksheet_id, id]):
        raise InvalidInputError("All IDs must be positive integers.")

    # 2. Check for existence first to provide a clear "Not Found" error.
    if id not in db.DB["events"]["line_items"]:
        raise LineItemNotFound(f"Line item with id '{id}' not found.")

    line_item = db.DB["events"]["line_items"][id]

    # 3. Check for ownership/parentage mismatch for a clear authorization/request error.
    if line_item["event_id"] != str(event_id) or line_item["worksheet_id"] != worksheet_id:
        raise LineItemMismatchError(
            f"Line item '{id}' does not belong to the specified event '{event_id}' and worksheet '{worksheet_id}'."
        )

    # 4. If all checks pass, perform the deletion.
    del db.DB["events"]["line_items"][id]
    return True