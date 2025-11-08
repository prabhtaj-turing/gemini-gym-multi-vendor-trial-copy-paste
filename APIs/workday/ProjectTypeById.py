"""
Project Type Management by ID Module

This module provides functionality for managing project types using their unique internal
identifiers in the Workday Strategic Sourcing system. It supports operations for retrieving
project type details.

The module interfaces with the simulation database to provide access to project type
definitions, which include configuration settings, default values, and metadata for
different types of projects in the system.

Functions:
    get: Retrieves project type details by ID
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, Any

from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_project_type_by_id',
        'description': 'Retrieves detailed information about a specific project type using its unique identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'Unique identifier of the project type.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get(id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves detailed information about a specific project type using its unique identifier.

    Args:
        id (int): Unique identifier of the project type.

    Returns:
        Optional[Dict[str, Any]]: Details of the specified project type if found else None. If Found, It can contain the following keys:
            - type (str): Always "project_types".
            - id (int): Unique ID of the project type.
            - attributes (Dict[str, str]): It can contain the following keys:
                - name (str): Full name of the project type.
                - shortcode (str): 4-character code representing the project type.
    """

    return db.DB["projects"]["project_types"].get(id, None) 