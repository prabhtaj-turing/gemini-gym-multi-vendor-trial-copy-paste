"""
This module provides functionality for managing awards and award line items in the Workday
Strategic Sourcing system. It supports operations for retrieving awards, filtering them
by various criteria, and managing award line items with their associated details.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any, Optional
from .SimulationEngine import db
from .SimulationEngine.custom_errors import ResourceNotFoundError, ValidationError
from .SimulationEngine.models import SUPPORTED_INCLUDES, AwardsGetInputModel
from pydantic import ValidationError as PydanticValidationError
import copy

@tool_spec(
    spec={
        'name': 'list_awards_with_filters',
        'description': """ Retrieve a list of awards based on specified filter criteria.
        
        This function supports filtering awards by their state and update timestamps.
        Multiple filters can be combined to narrow down the results. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filter_state_equals': {
                    'type': 'array',
                    'description': """ List of states to filter awards by.
                    Valid states include: "draft", "confirmed", "awaiting_requisition_sync", "requisition_created". """,
                    'items': {
                        'type': 'string'
                    }
                },
                'filter_updated_at_from': {
                    'type': 'string',
                    'description': 'Return awards updated on or after the specified timestamp.'
                },
                'filter_updated_at_to': {
                    'type': 'string',
                    'description': 'Return awards updated on or before the specified timestamp.'
                }
            },
            'required': []
        }
    }
)
def get(
    filter_state_equals: Optional[List[str]] = None,
    filter_updated_at_from: Optional[str] = None,
    filter_updated_at_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve a list of awards based on specified filter criteria.

    This function supports filtering awards by their state and update timestamps.
    Multiple filters can be combined to narrow down the results.

    Args:
        filter_state_equals (Optional[List[str]]): List of states to filter awards by.
            Valid states include: "draft", "confirmed", "awaiting_requisition_sync", "requisition_created".
        filter_updated_at_from (Optional[str]): Return awards updated on or after the specified timestamp.
        filter_updated_at_to (Optional[str]): Return awards updated on or before the specified timestamp.

    Returns:
        List[Dict[str, Any]]: A list of award dictionaries, where each award contains any of the following keys:
            - type (str): Object type, should always be "awards"
            - id (int): Unique identifier for the award
            - attributes (dict): Award attributes containing:
                - title (str): Award title (max 255 characters)
                - external_id (str): Award ID in your internal database (max 255 characters)
                - state (str): Award state, one of: "draft", "confirmed", "awaiting_requisition_sync", "requisition_created"
                - updated_at (str): Timestamp of the last update
                - pros (str): Pros associated with award option
                - cons (str): Cons associated with award option
            - relationships (dict): Award relationships containing:
                - creator (dict): Project creator information
                - project (dict): Associated project information
            - links (dict): Related links containing:
                - self (str): URL to the resource
            - Other award-specific attributes as defined in the system

    Raises:
        ValidationError: If any input parameters are invalid or contain unsupported values.
    """
    # Validate input parameters using Pydantic model
    try:
        validated_input = AwardsGetInputModel(
            filter_state_equals=filter_state_equals,
            filter_updated_at_from=filter_updated_at_from,
            filter_updated_at_to=filter_updated_at_to
        )
    except PydanticValidationError as e:
        # Convert Pydantic validation errors to custom ValidationError
        if e.errors():
            first_error = e.errors()[0]
            field_name = str(first_error['loc'][0])
            error_msg = first_error['msg']
            raise ValidationError(f"Invalid {field_name}: {error_msg}")
        else:
            raise ValidationError("Input validation failed")
    
    results = db.DB["awards"]["awards"][:]

    if validated_input.filter_state_equals:
        results = [
            award
            for award in results
            if award.get("attributes", {}).get("state") in validated_input.filter_state_equals
        ]

    if validated_input.filter_updated_at_from:
        results = [
            award
            for award in results
            if award.get("attributes", {}).get("updated_at", "") >= validated_input.filter_updated_at_from
        ]

    if validated_input.filter_updated_at_to:
        results = [
            award
            for award in results
            if award.get("attributes", {}).get("updated_at", "") <= validated_input.filter_updated_at_to
        ]

    return results

@tool_spec(
    spec={
        'name': 'list_award_line_items_for_award',
        'description': 'Retrieve line items associated with a specific award.',
        'parameters': {
            'type': 'object',
            'properties': {
                'award_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the award to retrieve line items for.'
                },
                'filter_is_quoted_equals': {
                    'type': 'boolean',
                    'description': """ Filter line items by their quoted status.
                    True for quoted items, False for non-quoted items. """
                },
                'filter_line_item_type_equals': {
                    'type': 'array',
                    'description': """ Return awards line items with specified line item types.
                    Valid types include: "STANDARD", "GOODS", "SERVICES". """,
                    'items': {
                        'type': 'string'
                    }
                },
                '_include': {
                    'type': 'string',
                    'description': """ Use the _include parameter to request related resources along with the primary resource.
                    Supported includes: "supplier_company", "worksheet". """
                }
            },
            'required': [
                'award_id'
            ]
        }
    }
)
def get_award_line_items(
    award_id: int,
    filter_is_quoted_equals: Optional[bool] = None,
    filter_line_item_type_equals: Optional[List[str]] = None,
    _include: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve line items associated with a specific award.

    Args:
        award_id (int): The unique identifier of the award to retrieve line items for.
        filter_is_quoted_equals (Optional[bool]): Filter line items by their quoted status.
            True for quoted items, False for non-quoted items.
        filter_line_item_type_equals (Optional[List[str]]): Return awards line items with specified line item types.
            Valid types include: "STANDARD", "GOODS", "SERVICES".
        _include (Optional[str]): Use the _include parameter to request related resources along with the primary resource.
            Supported includes: "supplier_company", "worksheet".

    Returns:
        List[Dict[str, Any]]: A list of award line item dictionaries, where each may contain any of the following keys:
            - type (str): Object type, always "award_line_items"
            - id (int): Unique identifier for the award line item
            - award_id (int): Associated award identifier
            - description (str): Description of the line item
            - amount (float): Amount of the award line item
            - attributes (dict): Award line item attributes containing:
                - data (dict): Worksheet column data with:
                    - data_identifier (str): Worksheet column identifier
                    - value (any): Cell value for the line item
                - allocated_quantity (int): Quantity allocated for the line item
                - sought_quantity (int): Quantity sought for the line item
                - price (float): Unit price of the line item
                - total_spend (float): Total spend for the line item
                - net_savings (float): Net savings amount
                - net_savings_percentage (float): Net savings as a percentage
                - line_item_type (str): Type of line item ("STANDARD", "GOODS", or "SERVICES")
                - is_quoted (bool): Whether the line item has been quoted
            - relationships (dict): Related resources containing:
                - supplier_company (dict): Associated supplier company with:
                    - type (str): Always "supplier_companies"
                    - id (int): Supplier company identifier
                - worksheet (dict): Associated worksheet with:
                    - type (str): Always "worksheets"
                    - id (int): Worksheet identifier
            - Any other award line item-specific attributes as defined in the system
    """
    results = [
        item
        for item in db.DB["awards"]["award_line_items"]
        if item.get("award_id") == award_id
    ]

    if filter_is_quoted_equals is not None:
        results = [
            item
            for item in results
            if item.get("is_quoted") == filter_is_quoted_equals
        ]

    if filter_line_item_type_equals:
        results = [
            item
            for item in results
            if item.get("line_item_type") in filter_line_item_type_equals
        ]

    if _include:
        # Simulate include logic
        pass

    return results

@tool_spec(
    spec={
        'name': 'get_award_line_item_by_id',
        'description': 'Retrieve details of a specific award line item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the award line item to retrieve.'
                },
                '_include': {
                    'type': 'string',
                    'description': """ Use the _include parameter to request related resources along with the primary resource.
                    Supported includes: "supplier_company" and "worksheet". """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_award_line_item(
    id: str,
    _include: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve details of a specific award line item.

    Args:
        id (str): The unique identifier of the award line item to retrieve.
        _include (Optional[str]): Use the _include parameter to request related resources along with the primary resource.
            Supported includes: "supplier_company" and "worksheet".

    Returns:
        Optional[Dict[str, Any]]: The award line item object if found, None otherwise.
            The object may contain any of the following keys:
            - type (str): Object type, always "award_line_items"
            - id (int): Unique identifier for the award line item
            - award_id (int): Associated award identifier
            - description (str): Description of the line item
            - amount (float): Amount of the award line item
            - attributes (dict): Award line item attributes containing:
                - data (dict): Worksheet column data with:
                    - data_identifier (str): Worksheet column identifier
                    - value (any): Cell value for the line item
                - allocated_quantity (int): Quantity allocated for the line item
                - sought_quantity (int): Quantity sought for the line item
                - price (float): Unit price of the line item
                - total_spend (float): Total spend for the line item
                - net_savings (float): Net savings amount
                - net_savings_percentage (float): Net savings as a percentage
                - line_item_type (str): Type of line item ("STANDARD", "GOODS", or "SERVICES")
                - is_quoted (bool): Whether the line item has been quoted
            - relationships (dict): Related resources containing:
                - supplier_company (dict): Associated supplier company with:
                    - type (str): Always "supplier_companies"
                    - id (int): Supplier company identifier
                - worksheet (dict): Associated worksheet with:
                    - type (str): Always "worksheets"
                    - id (int): Worksheet identifier

    Raises:
        TypeError: If 'id' or '_include' are not strings.
        ValidationError: If 'id' is an empty string, or if '_include'
            contains unsupported or malformed values.
        ResourceNotFoundError: If no award line item exists with the specified ID.
    """
    # 1. --- Validate `id` parameter ---
    if not isinstance(id, str):
        raise TypeError("URL parameter 'id' must be a string.")
    if not id.strip():
        raise ValidationError("URL parameter 'id' cannot be empty.")

    # 2. --- Validate `_include` parameter ---
    requested_includes = set()
    if _include is not None:
        if not isinstance(_include, str):
            raise TypeError("Query parameter '_include' must be a string.")
        requested_includes = {val.strip() for val in _include.split(',') if val.strip()}
        
        unsupported = requested_includes - SUPPORTED_INCLUDES
        if unsupported:
            # FIX: Sort the list of supported values for a deterministic error message.
            sorted_supported = sorted(list(SUPPORTED_INCLUDES))
            raise ValidationError(
                f"Unsupported value(s) in '_include' parameter: {unsupported}. "
                f"Supported values are: {sorted_supported}."
            )

    # 3. --- Find the Award Line Item ---
    target_item = None
    try:
        target_id = int(id)
    except ValueError:
        raise ResourceNotFoundError(f"Award Line Item with ID '{id}' not found.")

    for item in db.DB["awards"]["award_line_items"]:
        if item.get("id") == target_id:
            target_item = copy.deepcopy(item)
            break
    
    if target_item is None:
        raise ResourceNotFoundError(f"Award Line Item with ID '{id}' not found.")

    # 4. --- Handle `_include` logic ---
    if not requested_includes or 'relationships' not in target_item:
        return target_item

    if "supplier_company" in requested_includes:
        company_id = target_item.get('relationships', {}).get('supplier_company', {}).get('id')
        if company_id:
            company_data = db.DB['suppliers']['supplier_companies'].get(str(company_id))
            # FIX: Only embed the data if it was actually found.
            if company_data:
                target_item['relationships']['supplier_company'] = company_data

    if "worksheet" in requested_includes:
        worksheet_id = target_item.get('relationships', {}).get('worksheet', {}).get('id')
        if worksheet_id:
            worksheet_data = db.DB['events']['worksheets'].get(str(worksheet_id))
            # FIX: Only embed the data if it was actually found.
            if worksheet_data:
                target_item['relationships']['worksheet'] = worksheet_data
            
    return target_item
