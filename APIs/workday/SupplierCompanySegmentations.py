"""
Supplier Company Segmentation Management Module

This module provides functionality for managing supplier company segmentations in the
Workday Strategic Sourcing system. It supports operations for retrieving existing
segmentations and creating new ones.

The module interfaces with the simulation database to provide comprehensive
segmentation management capabilities, allowing users to:
- Retrieve all existing supplier company segmentations
- Create new supplier company segmentations with custom parameters
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List, Tuple, Union, Optional
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_supplier_company_segmentations',
        'description': """ Returns a list of supplier company segmentations.
        
        This function retrieves all supplier company segmentation definitions,
        including label, order, and slug metadata used for categorization or
        filtering of supplier companies. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> Tuple[List[Dict[str, Any]], int]:
    """
    Returns a list of supplier company segmentations.

    This function retrieves all supplier company segmentation definitions,
    including label, order, and slug metadata used for categorization or
    filtering of supplier companies.

    Returns:
        Tuple[List[Dict[str, Any]], int]: A tuple containing:
            - List[Dict[str, Any]]: List of segmentation objects, where each object contains:
                - id (int): Unique identifier for the segmentation.
                - label (str): Display label (≤ 255 characters).
                - order (int): UI display order.
                - slug (Optional[str]): Optional slug identifier (≤ 255 characters).
            - int: HTTP status code (200 for success).

    Raises:
        HTTPException: 401 Unauthorized if authentication credentials are missing or invalid.
    """


    return list(db.DB["suppliers"]["supplier_company_segmentations"].values()), 200

@tool_spec(
    spec={
        'name': 'create_supplier_company_segmentation',
        'description': """ Creates a new supplier company segmentation.
        
        This function registers a new segmentation category used to organize supplier
        companies within the platform. The segmentation is defined by a label, display order,
        and optional slug for programmatic reference. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'body': {
                    'type': 'object',
                    'description': 'Payload defining the segmentation details.',
                    'properties': {
                        'label': {
                            'type': 'string',
                            'description': 'Required. Display label for the segmentation (≤ 255 characters).'
                        },
                        'order': {
                            'type': 'integer',
                            'description': 'Required. UI display ordering index.'
                        },
                        'slug': {
                            'type': 'string',
                            'description': 'Optional programmatic identifier (≤ 255 characters).'
                        }
                    },
                    'required': [
                        'label',
                        'order'
                    ]
                }
            },
            'required': []
        }
    }
)
def post(body: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
    """
    Creates a new supplier company segmentation.

    This function registers a new segmentation category used to organize supplier
    companies within the platform. The segmentation is defined by a label, display order,
    and optional slug for programmatic reference.

    Args:
        body (Optional[Dict[str, Any]]): Payload defining the segmentation details.
            - label (str): Required. Display label for the segmentation (≤ 255 characters).
            - order (int): Required. UI display ordering index.
            - slug (Optional[str]): Optional programmatic identifier (≤ 255 characters).

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing:
            - Dict[str, Any], Dict[str, str]: The dict contains
                - id (int): Unique identifier of the new segmentation.
                - label (str): Segmentation label.
                - order (int): Display order.
                - slug (Optional[str]): Optional slug string.
            - int: HTTP status code (201 for success, 400 for error).

    Raises:
        HTTPException: 401 Unauthorized if the request lacks valid authentication.
        HTTPException: 409 Conflict if a segmentation with the same slug or label already exists.
    """

    if not body:
        return {"error": "Body is required"}, 400
    segmentation_id = len(db.DB["suppliers"]["supplier_company_segmentations"]) + 1
    segmentation = {"id": segmentation_id, **body}
    db.DB["suppliers"]["supplier_company_segmentations"][segmentation_id] = segmentation
    return segmentation, 201