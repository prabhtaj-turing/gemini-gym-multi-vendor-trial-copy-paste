"""
Project Supplier Contact Relationships by External ID Module

This module provides functionality for managing relationships between projects and supplier
contacts using external identifiers in the Workday Strategic Sourcing system. It supports
operations for adding and removing supplier contacts from projects using external IDs.

The module interfaces with the simulation database to maintain project-supplier contact
relationships, allowing for efficient management of supplier contact assignments to projects
using external identifiers. This is particularly useful when integrating with external
systems that maintain their own identifiers for projects and supplier contacts.

Functions:
    post: Adds supplier contacts to a project using external IDs
    delete: Removes supplier contacts from a project using external IDs
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List

from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'add_supplier_contacts_to_project_by_external_ids',
        'description': """ Adds suppliers to a project using supplier contact external identifiers.
        
        This endpoint links supplier contacts to an existing project by referencing their external identifiers. This is particularly useful for bulk-inviting suppliers already registered in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_external_id': {
                    'type': 'string',
                    'description': 'External ID of the project to which suppliers should be added.'
                },
                'supplier_contact_external_ids': {
                    'type': 'array',
                    'description': 'External IDs of the supplier contacts to add to the project.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'project_external_id',
                'supplier_contact_external_ids'
            ]
        }
    }
)
def post(project_external_id: str, supplier_contact_external_ids: List[str]) -> bool:
    """
    Adds suppliers to a project using supplier contact external identifiers.

    This endpoint links supplier contacts to an existing project by referencing their external identifiers. This is particularly useful for bulk-inviting suppliers already registered in the system.

    Args:
        project_external_id (str): External ID of the project to which suppliers should be added.
        supplier_contact_external_ids (List[str]): External IDs of the supplier contacts to add to the project.

    Returns:
        bool: Returns HTTP 204 No Content on successful addition.

    Raises:
        HTTPError 401: Unauthorized – Missing or invalid API credentials.
    """

    
    for id, project in db.DB["projects"]["projects"].items():
        if project.get("external_id") == project_external_id:
            if "supplier_contacts" not in db.DB["projects"]["projects"][id]:
                db.DB["projects"]["projects"][id]["supplier_contacts"] = []
            db.DB["projects"]["projects"][id]["supplier_contacts"].extend(supplier_contact_external_ids)
            return True
    return False

@tool_spec(
    spec={
        'name': 'remove_supplier_contacts_from_project_by_external_ids',
        'description': """ Removes suppliers from a project using supplier contact external identifiers.
        
        This endpoint disassociates supplier contacts from a specific project using their external IDs. This is commonly used to manage supplier participation in projects dynamically. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_external_id': {
                    'type': 'string',
                    'description': 'External ID of the project from which suppliers are to be removed.'
                },
                'supplier_contact_external_ids': {
                    'type': 'array',
                    'description': 'External IDs of the supplier contacts to remove from the project.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'project_external_id',
                'supplier_contact_external_ids'
            ]
        }
    }
)
def delete(project_external_id: str, supplier_contact_external_ids: List[str]) -> bool:
    """
    Removes suppliers from a project using supplier contact external identifiers.

    This endpoint disassociates supplier contacts from a specific project using their external IDs. This is commonly used to manage supplier participation in projects dynamically.

    Args:
        project_external_id (str): External ID of the project from which suppliers are to be removed.
        supplier_contact_external_ids (List[str]): External IDs of the supplier contacts to remove from the project.

    Returns:
        bool: Returns HTTP 204 No Content on successful removal.

    Raises:
        HTTPError 401: Unauthorized – Missing or invalid API credentials.
        HTTPError 404: Not Found – Contact or project not found.
    """

    for id, project in db.DB["projects"]["projects"].items():
        if project.get("external_id") == project_external_id and "supplier_contacts" in db.DB["projects"]["projects"][id]:
            db.DB["projects"]["projects"][id]["supplier_contacts"] = [
                sid for sid in db.DB["projects"]["projects"][id]["supplier_contacts"] if sid not in supplier_contact_external_ids
            ]
            return True
    return False 