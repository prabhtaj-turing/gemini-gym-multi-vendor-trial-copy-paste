"""
This module provides functionality for managing worksheets within events in the
Workday Strategic Sourcing system.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from .SimulationEngine import db
from .SimulationEngine.custom_errors import InvalidInputError, DatabaseStructureError

@tool_spec(
    spec={
        'name': 'list_event_worksheets',
        'description': 'Returns a list of all worksheets.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to which the worksheets belong.'
                }
            },
            'required': [
                'event_id'
            ]
        }
    }
)
def get(event_id: int) -> List[Dict[str, Any]]:
    """Returns a list of all worksheets.

    Args:
        event_id (int): The unique identifier of the event to which the worksheets belong.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a worksheet
            containing any of the following keys:
            - type (str): Object type, should always be "worksheets"
            - id (int): Worksheet identifier string
            - event_id (int): ID of the associated event
            - name (str): Name of the worksheet
            - created_by (str): ID of the user who created the worksheet
            - attributes (Dict[str, Any]): Worksheet attributes containing:
                - title (str): Worksheet title (max 255 characters)
                - budget (float): Budget for worksheet
                - notes (str): Notes specific to worksheet
                - updated_at (str): Last modification date-time
                - worksheet_type (str): Worksheet type enum ("standard", "goods", "services")
                - columns (list): List of column field values, each containing:
                    - id (str): Column identifier string
                    - name (str): Column field name
                    - data_identifier (str): Data identifier for line items
                    - mapping_key (str): Column field mapping key
            - links (Dict[str, Any]): Related links containing:
                - self (str): URL to the resource
    Raises:
        InvalidInputError: If event_id is not a positive integer.
        DatabaseStructureError: If the underlying worksheets data structure is not found.
    """
    # Validate input: Ensure event_id is a positive integer.
    if not isinstance(event_id, int) or event_id <= 0:
        raise InvalidInputError("Input 'event_id' must be a positive integer.")

    try:
        # Safely access the dictionary of all worksheets.
        all_worksheets = db.DB["events"]["worksheets"]

        # Use a list comprehension for efficient and safe filtering.
        # .get("event_id") prevents a KeyError if an entry is missing the key.
        return [
            worksheet for worksheet in all_worksheets.values()
            if worksheet.get("event_id") == event_id
        ]

    except KeyError:
        # Raise a custom error if the 'worksheets' key doesn't exist.
        raise DatabaseStructureError(
            'Could not find "worksheets" in the event database.'
        )