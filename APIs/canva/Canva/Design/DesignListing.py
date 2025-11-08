from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/Design/DesignListing.py
"""
This module provides design listing functionality for Canva.

It includes functions for listing and filtering user designs with sorting options.
"""

from typing import Optional, List, Dict, Any, Union

from canva.SimulationEngine.db import DB
from canva.SimulationEngine.custom_errors import (
    InvalidQueryError, 
    InvalidOwnershipError, 
    InvalidSortByError
)
from canva.SimulationEngine.search_engine import search_engine_manager

@tool_spec(
    spec={
        'name': 'list_designs',
        'description': 'Lists user-owned and shared designs, optionally filtered and sorted.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Search term to filter designs by title (max length: 255). Supports semantic search for fuzzy matching.'
                },
                'ownership': {
                    'type': 'string',
                    'description': """ Filter by ownership - "any", "owned", or "shared".
                    Defaults to "any". """
                },
                'sort_by': {
                    'type': 'string',
                    'description': """ Sort options - "relevance", "modified_descending", "modified_ascending",
                    "title_descending", "title_ascending". Defaults to "relevance". """
                }
            },
            'required': []
        }
    }
)
def list_designs(
    query: Optional[str] = None,
    ownership: str = "any",
    sort_by: str = "relevance",
) -> Optional[List[Dict[str, Union[str, int, Dict]]]]:
    """
    Lists user-owned and shared designs, optionally filtered and sorted.

    Args:
        query (Optional[str]): Search term to filter designs by title (max length: 255).
                               Supports semantic search for fuzzy and contextual matching.
        ownership (str): Filter by ownership - "any", "owned", or "shared".
                               Defaults to "any".
        sort_by (str): Sort options - "relevance", "modified_descending", "modified_ascending",
                       "title_descending", "title_ascending". Defaults to "relevance".

    Returns:
        Optional[List[Dict[str, Union[str, int, Dict]]]]: A list of design metadata entries, each containing:
            - id (str)
            - title (str)
            - created_at (int)
            - updated_at (int)
            - thumbnail (Optional[Dict[str, Union[str, int]]])
            - owner (Dict): { user_id, team_id }
            - urls (Dict): { edit_url, view_url }
        Returns None if no designs are found after filtering.

    Raises:
        TypeError: If 'query' (when not None), 'ownership', or 'sort_by' are not strings.
        InvalidQueryError: If 'query' exceeds the maximum length of 255 characters.
        InvalidOwnershipError: If 'ownership' is not one of the allowed values
                               ("any", "owned", "shared").
        InvalidSortByError: If 'sort_by' is not one of the allowed values
                            ("relevance", "modified_descending", "modified_ascending",
                             "title_descending", "title_ascending").
    """
    # --- Input Validation ---
    # Validate 'query'
    if query is not None:
        if not isinstance(query, str):
            raise TypeError("query must be a string.")
        if len(query) > 255:
            raise InvalidQueryError("query exceeds maximum length of 255 characters.")

    # Validate 'ownership'
    if not isinstance(ownership, str):
        raise TypeError("ownership must be a string.")
    allowed_ownership_values = ["any", "owned", "shared"]
    if ownership not in allowed_ownership_values:
        raise InvalidOwnershipError(
            f"ownership must be one of {allowed_ownership_values}. Received: '{ownership}'"
        )

    # Validate 'sort_by'
    if not isinstance(sort_by, str):
        raise TypeError("sort_by must be a string.")
    allowed_sort_by_values = [
        "relevance",
        "modified_descending",
        "modified_ascending",
        "title_descending",
        "title_ascending",
    ]
    if sort_by not in allowed_sort_by_values:
        raise InvalidSortByError(
            f"sort_by must be one of {allowed_sort_by_values}. Received: '{sort_by}'"
        )
    # --- End of Input Validation ---

    # --- Core Logic with Semantic Search ---
    designs = list(DB["Designs"].values())
    
    # Filtering by search query with semantic search (score_threshold: 0.5)
    if query:
        try:
            # Get the semantic search engine (configured in search_engine_config.json)
            engine = search_engine_manager.get_engine()
            
            # Perform semantic search with content_type filter
            search_filter = {"content_type": "design"}
            search_results = engine.search(query, filter=search_filter)
 
            # Extract design IDs from search results
            # The search engine returns the original_json_obj which contains the full design dict
            if search_results:
                matching_ids = set()
                
                for result in search_results:
                    design_id = None
                    
                    # The result is the original_json_obj (design dict) from the adapter
                    if isinstance(result, dict):
                        # Direct ID from the design object
                        design_id = result.get("id")
                        
                        # Fallback: check nested structures
                        if not design_id:
                            design_id = result.get("metadata", {}).get("design_id")
                        if not design_id and "original_json_obj" in result:
                            design_id = result["original_json_obj"].get("id")
                    
                    if design_id:
                        matching_ids.add(design_id)
                
                # Filter designs to only include matching ones from semantic search
                if matching_ids:
                    designs = [d for d in designs if d.get("id") in matching_ids]
                else:
                    # Semantic search returned results but no IDs extracted - return empty
                    designs = []
            else:
                # Semantic search returned no results - return empty list
                designs = []

        except Exception as e:
            # On error, fall back to substring search for backward compatibility
            designs = [d for d in designs if query.lower() in d["title"].lower()]

    # Filtering by ownership
    if ownership == "owned":
        designs = [d for d in designs if d.get("owner", {}).get("user_id")]
    elif ownership == "shared":
        designs = [d for d in designs if not d.get("owner", {}).get("user_id")]

    # Sorting options
    # "relevance" is the default and implies no specific sort here,
    # or a sort handled by the data source if `DB` were a real database.
    # Since "relevance" implies no specific key-based sort in this Python code,
    # we only handle other explicit sort options.
    if sort_by == "modified_descending":
        designs.sort(key=lambda x: x["updated_at"], reverse=True)
    elif sort_by == "modified_ascending":
        designs.sort(key=lambda x: x["updated_at"], reverse=False)
    elif sort_by == "title_descending":
        designs.sort(key=lambda x: x["title"], reverse=True)
    elif sort_by == "title_ascending":
        designs.sort(key=lambda x: x["title"], reverse=False)

    # Original return behavior: returns None if designs list is empty
    return designs if designs else None
