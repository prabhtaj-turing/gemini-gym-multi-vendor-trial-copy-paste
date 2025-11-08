"""
Bid Line Item Management by ID Module

This module provides functionality for managing individual bid line items in the
Workday Strategic Sourcing system using their unique identifiers. It supports
operations for retrieving specific bid line items.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_bid_line_item_by_id',
        'description': """ Retrieves the details of an existing bid line item.
        
        This function locates a specific bid line item using its unique identifier
        and returns its complete details if found. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the bid line item to retrieve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get(id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves the details of an existing bid line item.

    This function locates a specific bid line item using its unique identifier
    and returns its complete details if found.

    Args:
        id (int): The unique identifier of the bid line item to retrieve.

    Returns:
        Optional[Dict[str, Any]]: If found, returns a dictionary containing the
            bid line item details including any of the following keys:
                - "type" (str): Object type, should always be "bid_line_items"
                - "id" (int): The unique identifier of the bid line item
                - "bid_id" (int): The ID of the associated bid
                - "event_id" (int): The ID of the associated event
                - "description" (str): Description of the line item
                - "amount" (float): The amount of the bid line item
                - "attributes" (dict): Bid line item attributes containing:
                    - "data" (dict): A hashmap where keys are data identifier strings for worksheet columns and values are cell values
                        - "data_identifier" (str): Worksheet column identifier string
                        - "value" (any): Bid line item cell value
                    - "updated_at" (str): Last modification date in ISO 8601 format
                - "relationships" (dict): Bid line item relationships containing:
                    - "event" (dict): Associated event with:
                        - "type" (str): Always "events"
                        - "id" (int): Event identifier
                    - "bid" (dict): Associated bid with:
                        - "type" (str): Always "bids"
                        - "id" (int): Bid identifier
                    - "line_item" (dict): Associated line item with:
                        - "type" (str): Always "line_items"
                        - "id" (int): Line item identifier
                    - "worksheets" (dict): Associated worksheet with:
                        - "type" (str): Always "worksheets"
                        - "id" (int): Worksheet identifier
                - Any other bid line item-specific attributes as defined in the system
            
            If not found, returns None.
    """
    if id in db.DB["events"]["bid_line_items"]:
        return db.DB["events"]["bid_line_items"][id]
    else:
        return None