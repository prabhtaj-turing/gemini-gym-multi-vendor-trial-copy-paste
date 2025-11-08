"""
This module provides functionality for describing the schema and field definitions
of projects in the Workday Strategic Sourcing system.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List

from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_project_fields_description',
        'description': 'Retrieves a list of all available fields for project objects.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> List[str]:
    """
    Retrieves a list of all available fields for project objects.

    Returns:
        List[str]: A list of strings representing the field names available in project objects.
                  The list is derived from the fields present in an example project from the database.
                  Returns an empty list if no projects exist in the database.
    """
    if db.DB["projects"]["projects"]:
        example_project = next(iter(db.DB["projects"]["projects"].values()))
        return list(example_project.keys())
    return [] 