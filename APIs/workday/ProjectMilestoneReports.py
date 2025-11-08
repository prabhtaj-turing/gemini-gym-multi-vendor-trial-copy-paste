"""
Project Milestone Reports Module

This module provides functionality for managing and retrieving project milestone reports
in the Workday Strategic Sourcing system. It supports operations for retrieving both the
report entries and the associated schema definitions.

The module interfaces with the simulation database to provide access to project milestone
report data, which includes comprehensive information about project milestones, their
status, completion dates, and associated metadata.

Functions:
    get_entries: Retrieves a list of all project milestone report entries
    get_schema: Retrieves the schema definition for project milestone reports
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, List
from .SimulationEngine import db
from .SimulationEngine.custom_errors import (
    DatabaseSchemaError, 
    ResourceNotFoundError,
    InvalidInputError
)


@tool_spec(
    spec={
        'name': 'list_project_milestone_report_entries',
        'description': 'Retrieves a list of project milestone report entries.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> List[Dict[str, Any]]:
    """
    Retrieves a list of project milestone report entries.

    Returns:
        List[Dict[str, Any]]: A list of milestone entries.
            Each entry contains:
                - id (int): Unique identifier of the milestone report entry.
                - type (str): Always "project_milestone_report_entries".
                - attributes (Dict[str, Any]): Attributes of the milestone report entry.

    Raises:
        DatabaseSchemaError: When database structure is invalid.
        ResourceNotFoundError: When the requested resource is not found.
        InvalidInputError: For unexpected internal errors.
    """
    try:
        reports_db = db.DB.get("reports")
        if reports_db is None:
            raise DatabaseSchemaError("Database 'reports' section not found")

        entries = reports_db.get("project_milestone_reports_entries")
        if entries is None:
            raise ResourceNotFoundError("Project milestone reports entries not found in database")

        if not isinstance(entries, list):
            raise DatabaseSchemaError("Project milestone reports entries must be a list")

        response_entries = []
        for entry in entries:
            if isinstance(entry, dict):
                response_entries.append({
                    "id": entry.get("id", 0),
                    "type": "project_milestone_report_entries",
                    "attributes": entry.get("attributes", {})
                })

        return response_entries

    except (DatabaseSchemaError, ResourceNotFoundError, InvalidInputError):
        raise
    except Exception as e:
        raise InvalidInputError(f"Unexpected error in get_entries: {str(e)}")

@tool_spec(
    spec={
        'name': 'get_project_milestone_report_schema',
        'description': """ Retrieves the schema definition for project milestone reports.
        
        This endpoint provides metadata describing the fields available in project milestone reporting. 
        Useful for dynamically rendering forms or parsing report data. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Retrieves the schema definition for project milestone reports.

    This endpoint provides metadata describing the fields available in project milestone reporting. 
    Useful for dynamically rendering forms or parsing report data.

    Returns:
        Dict[str, Any]: A schema describing project milestone report fields. It can contain the following keys:
            - id (str): Identifier for the schema object, always "project_milestone_schemas".
            - type (str): Always "project_milestone_schemas".
            - attributes (Dict[str, Any]):
                - fields (List[Dict[str, str]]): A list of schema fields.
                    - type (str): Field type.
                        - Enum: "text", "date", "integer", "select", "string"
                    - name (str): Name of the field.

    Raises:
        DatabaseSchemaError: When database structure is invalid.
        ResourceNotFoundError: When requested resource is not found.
        InvalidInputError: When input parameters are invalid.
    """
    
    try:
        # Access database with error handling
        try:
            reports_db = db.DB.get("reports")
            if reports_db is None:
                raise DatabaseSchemaError("Database 'reports' section not found")
            
            schema = reports_db.get("project_milestone_reports_schema")
            if schema is None:
                raise DatabaseSchemaError("Project milestone reports schema not found in database")
            
            if not isinstance(schema, dict):
                raise DatabaseSchemaError("Project milestone reports schema must be a dictionary")
                
        except (KeyError, AttributeError) as e:
            raise DatabaseSchemaError(f"Database access error: {str(e)}")
        
        return schema
        
    except (DatabaseSchemaError, ResourceNotFoundError, InvalidInputError):
        # Re-raise these specific errors
        raise
    except Exception as e:
        raise InvalidInputError(f"Unexpected error in get_schema: {str(e)}") 