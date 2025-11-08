"""
This module provides functionality for retrieving and managing bids using their unique
internal identifiers in the Workday Strategic Sourcing system. It supports detailed
bid information retrieval with optional inclusion of related data. The module ensures
efficient bid lookup and comprehensive data access through direct ID-based queries.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, List, Any
from .SimulationEngine import db
from .SimulationEngine.custom_errors import ValidationError

@tool_spec(
    spec={
        'name': 'get_bid_by_id',
        'description': 'Retrieves the details of an existing bid. You need to supply the unique bid identifier that was returned upon bid creation.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': """ The unique internal identifier of the bid to retrieve. This ID is
                    typically returned when the bid is created in the system. Must be a
                    positive integer between 1 and 999,999,999. """
                },
                '_include': {
                    'type': 'string',
                    'description': """ A comma-separated string specifying additional
                    related data to include in the response. Common options include:
                    - 'event': Include associated event details
                    - 'supplier_company': Include supplier information
                    - 'supplier_companies': Include supplier companies (alternative)
                    - 'events': Include events (alternative)
                    Must be a valid string with max 500 characters, no duplicates allowed.
                    Defaults to None. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get(id: int, _include: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves the details of an existing bid. You need to supply the unique bid identifier that was returned upon bid creation.

    Args:
        id (int): The unique internal identifier of the bid to retrieve. This ID is
            typically returned when the bid is created in the system. Must be a
            positive integer between 1 and 999,999,999.
        _include (Optional[str]): A comma-separated string specifying additional
            related data to include in the response. Common options include:
            - 'event': Include associated event details
            - 'supplier_company': Include supplier information
            - 'supplier_companies': Include supplier companies (alternative)
            - 'events': Include events (alternative)
            Must be a valid string with max 500 characters, no duplicates allowed.
            Defaults to None.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing all the details of the requested bid,
            structured as follows:
            - data (Dict[str, Any]): Main resource object containing:
                - type (str): Object type, should always be "bids"
                - id (str): Bid identifier string
                - attributes (Dict[str, Any]): Bid attributes containing:
                    - supplier_id (int): ID of the submitting supplier
                    - bid_amount (float): Total bid amount
                    - intend_to_bid (bool): Identifies whether the supplier intends to bid on the event
                    - intend_to_bid_answered_at (str): Most recent time the supplier updated intend_to_bid
                    - status (str): Current bid status, one of:
                        - "award_retracted"
                        - "awarded"
                        - "draft"
                        - "rejected"
                        - "rejection_retracted"
                        - "resubmitted"
                        - "revising"
                        - "submitted"
                        - "unclaimed"
                        - "update_requested"
                    - submitted_at (str): First time the supplier submitted their bid
                    - resubmitted_at (str): Most recent time the supplier submitted their bid
                - links (Dict[str, str]): Links object containing:
                    - self (str): URL to the resource itself
            - included (List[Dict[str, Any]]): Array of included resources, each containing:
                - type (str): Object type, should always be "events" or "supplier_companies"
                - id (int): Resource identifier string
                - attributes (Dict[str, Any]): Resource-specific attributes containing all the data for the included resource
                - links (Dict[str, str]): Links object containing:
                    - self (str): URL to the resource itself
        Returns None if no bid is found with the specified ID.

    Raises:
        ValidationError: If the bid ID is invalid (not a positive integer, out of range)
                       or if the _include parameter is invalid (invalid options, duplicates, etc.)

    Note:
        The function performs a direct lookup in the database using the provided ID.
        If the bid does not exist, the function returns None rather than raising an
        exception. The function is optimized for quick lookups using the bid's
        primary key.
    """
    # Validate id parameter using simple validation
    try:
        if not isinstance(id, int):
            raise ValidationError(f"Bid ID must be a valid integer")
        
        if id <= 0:
            raise ValidationError(f"Bid ID must be a positive integer")
        
        if id > 999999999:
            raise ValidationError(f"Bid ID must be less than or equal to 999,999,999")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid bid ID: {id}. {str(e)}")
    
    # Validate _include parameter using simple validation
    try:
        if _include is not None:
            if not isinstance(_include, str):
                raise ValidationError(f"Invalid _include parameter: {_include}")
            
            # Check for empty or whitespace-only strings
            if not _include.strip():
                raise ValidationError("_include parameter cannot be empty or contain only whitespace")
            
            # Check length limit
            if len(_include) > 500:
                raise ValidationError(f"_include parameter is too long (max 500 characters), got {len(_include)} characters")
            
            # Define valid include options
            valid_include_options = {'event', 'supplier_company', 'supplier_companies', 'events'}
            
            # Validate individual include options
            include_options = [option.strip().lower() for option in _include.split(',') if option.strip()]
            
            for option in include_options:
                if option not in valid_include_options:
                    raise ValidationError(
                        f"Invalid include option '{option}'. Valid options are: {', '.join(sorted(valid_include_options))}"
                    )
            
            # Check for duplicate options
            if len(include_options) != len(set(include_options)):
                raise ValidationError("_include parameter contains duplicate options")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid _include parameter: {_include}. {str(e)}")
    
    # Perform database lookup
    if id in db.DB["events"]["bids"]:
        bid = db.DB["events"]["bids"][id].copy()
        bid["id"] = id
        
        # Handle _include parameter to add related data in JSON API format
        if _include:
            included_resources = []
            include_options = [option.strip().lower() for option in _include.split(',') if option.strip()]
            
            for option in include_options:
                if option in ['event', 'events'] and 'event_id' in bid:
                    event_id = bid['event_id']
                    # Convert event_id to string for database lookup since event IDs are stored as strings
                    str_event_id = str(event_id)
                    if str_event_id in db.DB["events"]["events"]:
                        event_data = db.DB["events"]["events"][str_event_id].copy()
                        included_resources.append({
                            "type": "events",
                            "id": event_id,
                            "attributes": event_data,
                            "links": {
                                "self": f"https://api.us.workdayspend.com/services/events/v1/events/{event_id}"
                            }
                        })
                
                elif option in ['supplier_company', 'supplier_companies'] and 'supplier_id' in bid:
                    supplier_id = bid['supplier_id']
                    if supplier_id in db.DB["suppliers"]["supplier_companies"]:
                        supplier_data = db.DB["suppliers"]["supplier_companies"][supplier_id].copy()
                        included_resources.append({
                            "type": "supplier_companies",
                            "id": supplier_id,
                            "attributes": supplier_data,
                            "links": {
                                "self": f"https://api.us.workdayspend.com/services/events/v1/supplier_companies/{supplier_id}"
                            }
                        })
            
            # Return JSON API format with data and included arrays
            if included_resources:
                return {
                    "data": {
                        "type": "bids",
                        "id": str(id),
                        "attributes": bid,
                        "links": {
                            "self": f"https://api.us.workdayspend.com/services/events/v1/bids/{id}"
                        }
                    },
                    "included": included_resources
                }
        
        # Return standard format when no include parameter or no included resources
        return {
            "data": {
                "type": "bids",
                "id": str(id),
                "attributes": bid,
                "links": {
                    "self": f"https://api.us.workdayspend.com/services/events/v1/bids/{id}"
                }
            }
        }
    else:
        return None