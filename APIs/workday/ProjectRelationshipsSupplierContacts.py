"""
This module provides functionality for managing relationships between projects and supplier
contacts in the Workday Strategic Sourcing system.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List

from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'add_supplier_contacts_to_project_by_internal_id',
        'description': 'Adds one or more supplier contacts to a project.',
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the project.'
                },
                'supplier_contact_ids': {
                    'type': 'array',
                    'description': 'A list of supplier contact IDs to add to the project.',
                    'items': {
                        'type': 'integer'
                    }
                }
            },
            'required': [
                'project_id',
                'supplier_contact_ids'
            ]
        }
    }
)
def post(project_id: int, supplier_contact_ids: List[int]) -> bool:
    """
    Adds one or more supplier contacts to a project.

    Args:
        project_id (int): The unique identifier of the project.
        supplier_contact_ids (List[int]): A list of supplier contact IDs to add to the project.

    Returns:
        bool: True if the supplier contacts were successfully added to the project,
              False if the project doesn't exist.
    """
    if str(project_id) in db.DB["projects"]["projects"]:
        if "supplier_contacts" not in db.DB["projects"]["projects"][str(project_id)]:
            db.DB["projects"]["projects"][str(project_id)]["supplier_contacts"] = []
        db.DB["projects"]["projects"][str(project_id)]["supplier_contacts"].extend(supplier_contact_ids)
        return True
    return False

@tool_spec(
    spec={
        'name': 'remove_supplier_contacts_from_project_by_internal_id',
        'description': 'Removes one or more supplier contacts from a project.',
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the project.'
                },
                'supplier_contact_ids': {
                    'type': 'array',
                    'description': 'A list of supplier contact IDs to remove from the project.',
                    'items': {
                        'type': 'integer'
                    }
                }
            },
            'required': [
                'project_id',
                'supplier_contact_ids'
            ]
        }
    }
)
def delete(project_id: int, supplier_contact_ids: List[int]) -> bool:
    """
    Removes one or more supplier contacts from a project.

    Args:
        project_id (int): The unique identifier of the project.
        supplier_contact_ids (List[int]): A list of supplier contact IDs to remove from the project.

    Returns:
        bool: True if the supplier contacts were successfully removed from the project,
              False if the project doesn't exist or has no supplier contacts.
    """
    if str(project_id) in db.DB["projects"]["projects"] and "supplier_contacts" in db.DB["projects"]["projects"][str(project_id)]:
        db.DB["projects"]["projects"][str(project_id)]["supplier_contacts"] = [
            sid for sid in db.DB["projects"]["projects"][str(project_id)]["supplier_contacts"] if sid not in supplier_contact_ids
        ]
        return True
    return False 