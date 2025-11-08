"""
This module provides functionality for managing bid line items in the Workday Strategic Sourcing system.
It supports operations for retrieving line items associated with specific bids, enabling detailed
analysis and management of bid components.
"""

from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine import db
from typing import Dict, Any, List, Optional

@tool_spec(
    spec={
        'name': 'list_bid_line_items_for_bid',
        'description': """ Returns a list of line items associated with a specific bid.
        
        This function returns all line items that are linked to the specified bid ID,
        allowing for detailed analysis of bid components and their associated data. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'bid_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the bid for which to retrieve line items.'
                }
            },
            'required': [
                'bid_id'
            ]
        }
    }
)
def get(bid_id: int) -> List[Optional[Dict[str, Any]]]:
    """Returns a list of line items associated with a specific bid.

    This function returns all line items that are linked to the specified bid ID,
    allowing for detailed analysis of bid components and their associated data.

    Args:
        bid_id (int): The unique identifier of the bid for which to retrieve line items.

    Returns:
        List[Optional[Dict[str, Any]]]: A list of dictionaries, where each dictionary represents a line item
            associated with the specified bid. Each line item includes any of the following keys:
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
            
            If the bid_id is not found, returns an empty list.

    Raises:
        ValueError: If bid_id is None
        TypeError: If bid_id is not an integer

    """
    if bid_id is None:
        raise ValueError("Bid ID is required")

    if not isinstance(bid_id, int):
        raise TypeError("Bid ID must be an integer")

    return [item for item in db.DB["events"]["bid_line_items"].values() if item.get("bid_id") == bid_id]
