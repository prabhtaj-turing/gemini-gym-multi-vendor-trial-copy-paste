"""
This module provides functionality for retrieving the schema and field definitions
of bids in the Workday Strategic Sourcing system. It enables users to understand
the structure and available fields of bid objects. The module supports comprehensive
bid schema discovery and documentation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List
from .SimulationEngine import db
from .SimulationEngine.custom_errors import DatabaseSchemaError, NotFoundError

@tool_spec(
    spec={
        'name': 'describe_bid_fields',
        'description': """ Returns a list of fields for the bid object with comprehensive error handling.
        
        This function retrieves the field names from the first bid in the database
        to determine the available fields. The function includes proper error handling
        for database schema issues and missing data. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> List[str]:
    """
    Returns a list of fields for the bid object with comprehensive error handling.

    This function retrieves the field names from the first bid in the database
    to determine the available fields. The function includes proper error handling
    for database schema issues and missing data.

    Returns:    
        List[str]: A list of strings, where each string represents a field name
            available in bid objects.

    Raises:
        DatabaseSchemaError: If the database structure is invalid or missing required keys.
        NotFoundError: If no bids exist in the database to determine the schema.

    Note:
        The function uses the first bid in the database as a template to
        determine the available fields. This assumes that all bids share
        the same schema structure. If no bids exist, the function raises
        a NotFoundError to indicate that the schema cannot be determined.
    """
    # Validate database structure
    if not hasattr(db, 'DB') or not isinstance(db.DB, dict):
        raise DatabaseSchemaError("Database is not properly initialized")
    
    if 'events' not in db.DB:
        raise DatabaseSchemaError("Database is missing 'events' collection")
    
    if 'bids' not in db.DB['events']:
        raise DatabaseSchemaError("Database is missing 'bids' collection in events")
    
    # Check if any bids exist
    if not db.DB['events']['bids']:
        raise NotFoundError("No bids found in database to determine schema")
    
    # Get the first bid to determine schema
    first_bid_id = list(db.DB["events"]["bids"].keys())[0]
    first_bid = db.DB["events"]["bids"][first_bid_id]
    
    # Validate that the first bid has a proper structure
    if not isinstance(first_bid, dict):
        raise DatabaseSchemaError("First bid in database has invalid structure")
    
    return list(first_bid.keys())