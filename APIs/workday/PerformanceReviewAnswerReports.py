"""
Performance Review Answer Reports Module

This module provides functionality for managing and retrieving performance review answer reports
in the Workday Strategic Sourcing system. It supports operations for retrieving both the
report entries and the associated schema definitions.

The module interfaces with the simulation database to provide access to performance review
answer report data, which includes detailed information about answers provided in performance
reviews and their associated metadata.

Functions:
    get_entries: Retrieves a list of all performance review answer report entries
    get_schema: Retrieves the schema definition for performance review answer reports
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Any
from .SimulationEngine import db
from .SimulationEngine.custom_errors import DatabaseSchemaError

@tool_spec(
    spec={
        'name': 'list_performance_review_answer_report_entries',
        'description': """ Retrieves a list of performance review answer entries.
        
        This endpoint returns detailed entries from performance review responses, useful for 
        evaluation analysis, tracking progress, and generating summaries. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> List[Dict[str, Any]]:
    """
    Retrieves a list of performance review answer entries.

    This endpoint returns detailed entries from performance review responses, useful for 
    evaluation analysis, tracking progress, and generating summaries.

    Returns:
        List[Dict[str, Any]]: List of performance review answer report entries.
            Each entry contains:
                - id (int): Unique identifier for the report entry
                - answer (str): The answer content for the performance review
                - [Additional fields may be present based on review configuration]

    Raises:
        DatabaseSchemaError: If the database structure is corrupted or inaccessible
    """
    try:
        # Validate database structure
        if not isinstance(db.DB, dict):
            raise DatabaseSchemaError("Database is not properly initialized")
        
        if "reports" not in db.DB:
            raise DatabaseSchemaError("Reports section not found in database")
        
        reports_data = db.DB["reports"]
        if not isinstance(reports_data, dict):
            raise DatabaseSchemaError("Reports data is not properly structured")
        
        # Get entries with fallback to empty list
        entries = reports_data.get('performance_review_answer_reports_entries', [])
        
        # Validate that entries is a list
        if not isinstance(entries, list):
            raise DatabaseSchemaError("Performance review answer reports entries is not a list")
        
        return entries
        
    except (KeyError, AttributeError) as e:
        raise DatabaseSchemaError(f"Database access error: {str(e)}")

@tool_spec(
    spec={
        'name': 'get_performance_review_answer_report_schema',
        'description': """ Retrieves the schema for performance review answer reports.
        
        This schema outlines the structure of performance review answers returned by the API,
        including field names and their respective data types. Useful for dynamic rendering or processing of answer entries. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Retrieves the schema for performance review answer reports.

    This schema outlines the structure of performance review answers returned by the API,
    including field names and their respective data types. Useful for dynamic rendering or processing of answer entries.

    Returns:
        Dict[str, Any]: Performance review answer schema definition.
            The schema structure may include:
                - type (str): Schema type identifier (e.g., "object")
                - properties (Dict[str, Any]): Field definitions with their data types

    Raises:
        DatabaseSchemaError: If the database structure is corrupted or inaccessible
    """
    try:
        schema = db.DB["reports"].get('performance_review_answer_reports_schema', {})
        if not isinstance(schema, dict):
            raise DatabaseSchemaError("Performance review answer reports schema must be a dictionary")
        return schema
    except KeyError:
        return {}
    except Exception as e:
        raise DatabaseSchemaError(f"Failed to retrieve performance review answer schema: {str(e)}") 