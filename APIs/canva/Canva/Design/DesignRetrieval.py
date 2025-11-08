from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/Design/DesignRetrieval.py
"""
This module provides design retrieval functionality for Canva.

It includes functions for retrieving design metadata and design pages with pagination support.
"""

from typing import Optional, Dict, Any, List, Union

from canva.SimulationEngine.db import DB
from canva.SimulationEngine.custom_errors import InvalidDesignIDError


@tool_spec(
    spec={
        'name': 'get_design',
        'description': 'Retrieves metadata for a single design.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_id': {
                    'type': 'string',
                    'description': 'The ID of the design. Must be a non-empty string.'
                }
            },
            'required': [
                'design_id'
            ]
        }
    }
)
def get_design(design_id: str) -> Optional[Dict[str, Union[str, Dict]]]:
    """
    Retrieves metadata for a single design.

    Args:
        design_id (str): The ID of the design. Must be a non-empty string.

    Returns:
        Optional[Dict[str, Union[str, Dict]]]: If found, returns:
            - design (Dict):
                - id (str)
                - title (str, optional)
                - created_at (int)
                - updated_at (int)
                - thumbnail (Optional[Dict[str, Union[str, int]]])
                - owner (Dict): { user_id, team_id }
                - urls (Dict): { edit_url, view_url }
                - page_count (int, optional)
        Otherwise, returns None.

    Raises:
        TypeError: If `design_id` is not a string.
        InvalidDesignIDError: If `design_id` is an empty string.
    """
    # --- Input Validation ---
    if not isinstance(design_id, str):
        raise TypeError("design_id must be a string.")
    if not design_id: # Check for empty string
        raise InvalidDesignIDError("design_id cannot be an empty string.")
    # --- End of Input Validation ---

    design = DB["Designs"].get(design_id)
    if design:
        return {"design": design}
    return None


@tool_spec(
    spec={
        'name': 'get_design_pages',
        'description': 'Retrieves pages from a design, with support for pagination.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_id': {
                    'type': 'string',
                    'description': 'The ID of the design to retrieve pages from.'
                },
                'offset': {
                    'type': 'integer',
                    'description': """ The index of the first page to return (1-based). Default is 1.
                    Min: 1, Max: 500. """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The number of pages to return. Default is 50.
                    Min: 1, Max: 200. """
                }
            },
            'required': [
                'design_id'
            ]
        }
    }
)
def get_design_pages(
    design_id: str, offset: int = 1, limit: int = 50
) -> Optional[Dict[str, List[Dict[str, Union[str, int, Dict]]]]]:
    """
    Retrieves pages from a design, with support for pagination.

    Args:
        design_id (str): The ID of the design to retrieve pages from.
        offset (int): The index of the first page to return (1-based). Default is 1.
                      Min: 1, Max: 500.
        limit (int): The number of pages to return. Default is 50.
                     Min: 1, Max: 200.

    Returns:
        Optional[Dict[str, List[Dict[str, Union[str, int, Dict]]]]]: If pages are found, returns:
            - pages (list of dicts):
                - index (int)
                - thumbnail (Optional[Dict[str, Union[str, int]]]):
                    - width (int)
                    - height (int)
                    - url (str)
        Otherwise, returns None.
    """
    design = DB["Designs"].get(design_id)
    if design and "pages" in design:
        pages = list(design["pages"].values())
        offset = (
            max(1, min(offset, len(pages))) - 1
        )  # Ensure offset is within valid range
        limit = max(1, min(limit, 200))  # Ensure limit is within allowed range
        return {"pages": pages[offset : offset + limit]}
    return None
