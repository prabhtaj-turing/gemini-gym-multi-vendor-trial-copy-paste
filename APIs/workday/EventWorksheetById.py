"""
This module provides functionality for retrieving specific event worksheets by their
unique identifiers in the Workday Strategic Sourcing system.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional
from .SimulationEngine import db
from .SimulationEngine import custom_errors

@tool_spec(
    spec={
        'name': 'get_event_worksheet_by_id',
        'description': 'Retrieves the details of an existing worksheet. You need to supply the unique worksheet identifier that was returned upon worksheet creation.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to which the worksheet belongs.'
                },
                'id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the worksheet to retrieve.'
                }
            },
            'required': [
                'event_id',
                'id'
            ]
        }
    }
)
def get(event_id: int, id: int) -> Optional[Dict]:
    """Retrieves the details of an existing worksheet. You need to supply the unique worksheet identifier that was returned upon worksheet creation.

    Args:
        event_id (int): The unique identifier of the event to which the worksheet belongs.
        id (int): The unique identifier of the worksheet to retrieve.

    Returns:
        Optional[Dict]: A dictionary containing the worksheet details if found,
            including any of the following keys:
            - type (str): Object type, should always be "worksheets"
            - id (int): Worksheet identifier string
            - event_id (int): ID of the associated event
            - name (str): Name of the worksheet
            - created_by (str): ID of the user who created the worksheet
            - attributes (dict): Worksheet attributes containing:
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
            - links (dict): Related links containing:
                - self (str): URL to the resource
    Raises:
        InvalidInputError: If event_id or id are not positive
                                         integers.
        ResourceNotFoundError: If no worksheet is found for the
                                             given id and event_id.
        DatabaseSchemaError: If the internal database structure
                                           is malformed.
    """
    # 1. Explicit input validation for type, range, and null values.
    if not isinstance(event_id, int) or event_id <= 0:
        raise custom_errors.InvalidInputError(
            f"The event_id must be a positive integer, but received '{event_id}'."
        )
    if not isinstance(id, int) or id <= 0:
        raise custom_errors.InvalidInputError(
            f"The worksheet id must be a positive integer, but received '{id}'."
        )

    # 2. Robust database access with specific error handling.
    try:
        worksheets = db.DB["events"]["worksheets"]
        worksheet = worksheets.get(id)

        # 3. Check for resource existence and correct association.
        if worksheet is None or worksheet.get("event_id") != event_id:
            raise custom_errors.ResourceNotFoundError(
                f"Worksheet with id '{id}' associated with event_id "
                f"'{event_id}' was not found."
            )

        return worksheet

    except KeyError as e:
        # Catches errors if "events" or "worksheets" keys are missing
        # and raises a specific, meaningful exception.
        raise custom_errors.DatabaseSchemaError(
            f"Database schema is malformed. Missing key: {e}"
        ) from e