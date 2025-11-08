"""
Project Types Management Module

This module provides functionality for managing project types in the Workday Strategic
Sourcing system. It supports operations for retrieving all available project types.

The module interfaces with the simulation database to provide access to project type
definitions, which include configuration settings, default values, and metadata for
different types of projects in the system.

Functions:
    get: Retrieves a list of all project types
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Any

from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_project_types',
        'description': """ Retrieves a list of all available project types in the system.
        
        Each project type includes a name and a short code. This information is useful for categorizing and identifying different types of projects in workflows and project planning. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> List[Dict[str, Any]]:
    """
    Retrieves a list of all available project types in the system.

    Each project type includes a name and a short code. This information is useful for categorizing and identifying different types of projects in workflows and project planning.

    Returns:
        List[Dict[str, Any]]: A list of project types. Each project type is a dictionary containing the following fields:
            - type (str): Always "project_types".
            - id (int): Unique identifier of the project type.
            - attributes (Dict[str, str]):
                - name (str): Name of the project type.
                - shortcode (str): 4-character short code for the type.
            - links (Dict[str, str]):
                - self (str): Link to the current resource listing.
            - meta (Dict[str, int]):
                - count (int): Total number of project types returned.

    """
    return list(db.DB["projects"]["project_types"].values()) 