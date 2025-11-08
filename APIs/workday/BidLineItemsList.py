"""
This module provides functionality for retrieving and filtering bid line items in the
Workday Strategic Sourcing system. It supports comprehensive filtering capabilities
to enable precise retrieval of bid line items based on specific criteria.
"""
from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine import db
from typing import Optional, Any, List, Dict
from .SimulationEngine.models import BidLineItemsListGetInput


@tool_spec(
    spec={
        'name': 'list_all_bid_line_items',
        'description': """ Returns a list of all bid line items.
        
        This function returns all bid line items in the system, with the option to
        filter the results based on specific criteria. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filter': {
                    'type': 'object',
                    'description': """ A dictionary containing field-value pairs to filter
                    the bid line items. Filter bid line items by multiple criteria. Only one filter per attribute is supported.
                    For best performance, we recommend 5 or less filters.
                    Possible filter keys: """,
                    'properties': {
                        'bid_id_equals': {
                            'type': 'integer',
                            'description': 'Find bid line items by a specific bid ID.'
                        },
                        'event_id_equals': {
                            'type': 'integer',
                            'description': 'Find bid line items by a specific event ID.'
                        }
                    },
                    'required': [
                        'bid_id_equals',
                        'event_id_equals'
                    ]
                }
            },
            'required': []
        }
    }
)
def get(filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Returns a list of all bid line items.

    This function returns all bid line items in the system, with the option to
    filter the results based on specific criteria. 

    Args:
        filter (Optional[Dict[str, Any]]): A dictionary containing field-value pairs to filter
            the bid line items. Filter bid line items by multiple criteria. Only one filter per attribute is supported.
            For best performance, we recommend 5 or less filters.
            Possible filter keys:
            - bid_id_equals (int): Find bid line items by a specific bid ID.
            - event_id_equals (int): Find bid line items by a specific event ID.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a bid line item.
            Each bid line item contains its associated fields and values as defined
            in the system. If a filter is provided, only items matching all specified
            criteria are returned.
            The dictionary keys can be any of the following:
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

    Raises:
        ValueError: If input validation fails, including:
            - Invalid filter field names (only "bid_id", "status", "event_id" are allowed)
            - Pydantic validation errors for the filter parameter

    Note:
        The filtering is case-sensitive and requires exact matches for all specified
        fields. If a field specified in the filter does not exist in a bid line item,
        that item will be excluded from the results.
    """
    # Input validation using Pydantic
    try:
        validated = BidLineItemsListGetInput(filter=filter)
    except Exception as e:
        raise ValueError(f"Input validation error: {e}")
    allowed_fields = {"bid_id", "status", "event_id"}
    if validated.filter:
        for key in validated.filter:
            if key not in allowed_fields:
                raise ValueError(f"Unknown filter field: {key}")
    items = list(db.DB["events"]["bid_line_items"].values())
    if validated.filter:
        filtered_items = []
        for item in items:
            match = True
            for key, value in validated.filter.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                filtered_items.append(item)
        items = filtered_items
    return items