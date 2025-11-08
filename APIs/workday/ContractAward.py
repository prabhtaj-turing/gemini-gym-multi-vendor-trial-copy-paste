"""
This module provides functionality for managing contract awards and their associated
line items in the Workday Strategic Sourcing system. It supports operations for
retrieving award details, listing awards, and managing award line items. The module
enables comprehensive contract award tracking and management capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any
from .SimulationEngine import db
from .SimulationEngine import custom_errors

@tool_spec(
    spec={
        'name': 'list_contract_awards',
        'description': """ Retrieves a list of all contract awards in the Workday Strategic Sourcing system.
        
        This function returns all available contract awards, providing comprehensive
        information about each award including their associated data and configurations.
        The function enables complete visibility into all awards and their current status. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_awards() -> List[Dict[str, Any]]:
    """Retrieves a list of all contract awards in the Workday Strategic Sourcing system.

    This function returns all available contract awards, providing comprehensive
    information about each award including their associated data and configurations.
    The function enables complete visibility into all awards and their current status.

    Returns:
        List[Dict[str, Any]]: 
            A list of award dictionaries. Each dictionary contains all the 
            details of an award, including:
            - award_id (int): Unique identifier of the award
            - contract_id (int): ID of the associated contract
            - supplier_id (int): ID of the winning supplier
            - status (str): Current status of the award
            - award_date (str): Date of award issuance
            - start_date (str): Contract start date
            - end_date (str): Contract end date
            - total_value (float): Total award value
            - currency (str): Currency of the award value
            - created_at (str): Timestamp of award creation
            - updated_at (str): Timestamp of last update

    Raises:
        NotFoundError: If the 'contracts' or 'awards'
            keys are missing from the database, indicating a corrupted or
            invalid database state.
    """
    try:
        return list(db.DB["contracts"]["awards"].values())
    except KeyError as e:
        raise custom_errors.NotFoundError(
            f"Database is missing expected structure: {e}. "
            "Could not retrieve awards."
        ) from e

@tool_spec(
    spec={
        'name': 'get_contract_award_by_id',
        'description': """ Retrieves detailed information about a specific contract award.
        
        This function returns comprehensive information about a contract award,
        including all its associated data and configurations. The function provides
        complete visibility into award details and associated metrics. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The unique internal identifier of the award to retrieve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_award(id: int) -> Dict:
    """Retrieves detailed information about a specific contract award.

    This function returns comprehensive information about a contract award,
    including all its associated data and configurations. The function provides
    complete visibility into award details and associated metrics.

    Args:
        id (int): The unique internal identifier of the award to retrieve.

    Returns:
        Dict: A dictionary containing all the details of the requested award,
            including:
            - award_id (int): Unique identifier of the award
            - contract_id (int): ID of the associated contract
            - supplier_id (int): ID of the winning supplier
            - status (str): Current status of the award
            - award_date (str): Date of award issuance
            - start_date (str): Contract start date
            - end_date (str): Contract end date
            - total_value (float): Total award value
            - currency (str): Currency of the award value
            - created_at (str): Timestamp of award creation
            - updated_at (str): Timestamp of last update
            - metrics (Dict): Award-specific performance metrics
            - configurations (Dict): Award-specific settings and options

    Raises:
        TypeError: If the provided id is not an integer.
        ValueError: If the provided id is not a positive integer.
        KeyError: If no award is found with the specified ID.

    Note:
        The returned data is read-only and should not be modified directly.
    """
    # Validate input type
    if not isinstance(id, int):
        raise TypeError(f"Award ID must be an integer, got {type(id).__name__}.")
    
    # Validate input value
    if id <= 0:
        raise ValueError(f"Award ID must be a positive integer, got {id}.")
    
    if id not in db.DB["contracts"]["awards"]:
        raise KeyError(f"Award with id {id} not found.")
    return db.DB["contracts"]["awards"][id]

@tool_spec(
    spec={
        'name': 'list_contract_award_line_items',
        'description': """ Retrieves a list of line items associated with a specific contract award.
        
        This function returns all line items that are linked to the specified award ID,
        allowing for detailed analysis of award components and their associated data.
        The line items provide granular information about the award's components. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'award_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the award for which to retrieve
                    line items. """
                }
            },
            'required': [
                'award_id'
            ]
        }
    }
)
def list_contract_award_line_items(award_id: int) -> List[Dict]:
    """Retrieves a list of line items associated with a specific contract award.

    This function returns all line items that are linked to the specified award ID,
    allowing for detailed analysis of award components and their associated data.
    The line items provide granular information about the award's components.

    Args:
        award_id (int): The unique identifier of the award for which to retrieve
            line items.

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary represents a
            line item containing:
            - line_item_id (int): Unique identifier of the line item
            - award_id (int): ID of the associated award
            - item_name (str): Name of the line item
            - quantity (int): Quantity of items
            - unit_price (float): Price per unit
            - total_price (float): Total price for the line item
            - currency (str): Currency of the prices
            - description (str): Detailed description of the line item
            - created_at (str): Timestamp of line item creation
            - updated_at (str): Timestamp of last update

    Raises:
        TypeError: If the provided award_id is not an integer.
        ValueError: If the provided award_id is not a positive integer.

    Note:
        The function returns an empty list if no line items are found for the
        specified award. The returned data is read-only and should not be modified
        directly.
    """
    # Validate input type
    if not isinstance(award_id, int):
        raise TypeError(f"Award ID must be an integer, got {type(award_id).__name__}.")
    
    # Validate input value
    if award_id <= 0:
        raise ValueError(f"Award ID must be a positive integer, got {award_id}.")
    
    return [item for item in db.DB["contracts"]["award_line_items"] if item.get("award_id") == award_id]

@tool_spec(
    spec={
        'name': 'get_contract_award_line_item_by_id',
        'description': """ Retrieves detailed information about a specific award line item.
        
        This function returns comprehensive information about a contract award line
        item, including all its associated data and configurations. The function
        provides complete visibility into line item details and associated metrics. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the award line item to retrieve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_contract_award_line_item(id: str) -> Dict:
    """Retrieves detailed information about a specific award line item.

    This function returns comprehensive information about a contract award line
    item, including all its associated data and configurations. The function
    provides complete visibility into line item details and associated metrics.

    Args:
        id (str): The unique identifier of the award line item to retrieve.

    Returns:
        Dict: A dictionary containing all the details of the requested line item,
            including:
            - line_item_id (int): Unique identifier of the line item
            - award_id (int): ID of the associated award
            - item_name (str): Name of the line item
            - quantity (int): Quantity of items
            - unit_price (float): Price per unit
            - total_price (float): Total price for the line item
            - currency (str): Currency of the prices
            - description (str): Detailed description of the line item
            - created_at (str): Timestamp of line item creation
            - updated_at (str): Timestamp of last update
            - configurations (Dict): Line item-specific settings and options

    Raises:
        KeyError: If no award line item is found with the specified ID.

    Note:
        The returned data is read-only and should not be modified directly.
    """
    for item in db.DB["contracts"]["award_line_items"]:
        if item.get("id") == id:
            return item
    raise KeyError(f"Award line item with id {id} not found.") 