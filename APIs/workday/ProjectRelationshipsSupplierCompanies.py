"""
This module provides functionality for managing relationships between projects and supplier
companies in the Workday Strategic Sourcing system. 
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List

from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'add_supplier_companies_to_project',
        'description': 'Adds one or more supplier companies to a project.',
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the project.'
                },
                'supplier_ids': {
                    'type': 'array',
                    'description': """ A list of supplier company IDs to add to the project.
                    For optimal performance, it's recommended to add 10 or fewer
                    suppliers in a single request. """,
                    'items': {
                        'type': 'integer'
                    }
                }
            },
            'required': [
                'project_id',
                'supplier_ids'
            ]
        }
    }
)
def post(project_id: int, supplier_ids: List[int]) -> bool:
    """
    Adds one or more supplier companies to a project.

    Args:
        project_id (int): The unique identifier of the project.
        supplier_ids (List[int]): A list of supplier company IDs to add to the project.
                                 For optimal performance, it's recommended to add 10 or fewer
                                 suppliers in a single request.

    Returns:
        bool: True if the suppliers were successfully added to the project,
              False if the project doesn't exist.
    """
    if str(project_id) in db.DB["projects"]["projects"]:
        if "supplier_companies" not in db.DB["projects"]["projects"][str(project_id)]:
            db.DB["projects"]["projects"][str(project_id)]["supplier_companies"] = []
        db.DB["projects"]["projects"][str(project_id)]["supplier_companies"].extend(supplier_ids)
        return True
    return False

@tool_spec(
    spec={
        'name': 'remove_supplier_companies_from_project',
        'description': 'Removes one or more supplier companies from a project.',
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the project.'
                },
                'supplier_ids': {
                    'type': 'array',
                    'description': 'A list of supplier company IDs to remove from the project.',
                    'items': {
                        'type': 'integer'
                    }
                }
            },
            'required': [
                'project_id',
                'supplier_ids'
            ]
        }
    }
)
def delete(project_id: int, supplier_ids: List[int]) -> bool:
    """
    Removes one or more supplier companies from a project.

    Args:
        project_id (int): The unique identifier of the project.
        supplier_ids (List[int]): A list of supplier company IDs to remove from the project.

    Returns:
        bool: True if the suppliers were successfully removed from the project,
              False if the project doesn't exist or has no supplier companies.
    """
    if str(project_id) in db.DB["projects"]["projects"] and "supplier_companies" in db.DB["projects"]["projects"][str(project_id)]:
        db.DB["projects"]["projects"][str(project_id)]["supplier_companies"] = [
            sid for sid in db.DB["projects"]["projects"][str(project_id)]["supplier_companies"] if sid not in supplier_ids
        ]
        return True
    return False 