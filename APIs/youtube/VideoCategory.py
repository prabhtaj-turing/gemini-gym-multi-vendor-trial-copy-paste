from typing import Dict, List, Optional, Union
from common_utils.tool_spec_decorator import tool_spec
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id

"""
    Handles YouTube Video Categories API operations.
    
    This class provides methods to retrieve information about video categories,
    which are used to organize videos on YouTube.
"""


@tool_spec(
    spec={
    "name": "list_video_categories",
    "description": "Retrieves a list of video categories with optional filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Must be 'snippet'."
            },
            "id": {
                "type": "string",
                "description": "The id parameter identifies the video category that is being retrieved. Defaults to None."
            },
            "region_code": {
                "type": "string",
                "description": "The regionCode parameter instructs the API to select a video category available in the specified region. Defaults to None."
            },
            "max_results": {
                "type": "integer",
                "description": "The maximum number of items that should be returned in the result set. Defaults to None."
            }
        },
        "required": [
            "part"
        ]
    }
}
)
def list(
    part: str,
    id: Optional[str] = None,
    region_code: Optional[str] = None,
    max_results: Optional[int] = None,
) -> Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]:
    """
    Retrieves a list of video categories with optional filters.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Must be 'snippet'.
        id (Optional[str]): The id parameter identifies the video category that is being retrieved. Defaults to None.
        region_code (Optional[str]): The regionCode parameter instructs the API to select a video category available in the specified region. Defaults to None.
        max_results (Optional[int]): The maximum number of items that should be returned in the result set. Defaults to None.

    Returns:
        Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]: A dictionary containing:
            - items: A list of video category resources, each containing:
                - id (str): The ID of the video category.
                - snippet (Dict[str, str]): Metadata for the category, including:
                    - title (str): Name of the video category.
                    - regionCode (str): The region where the category is available.

    Raises:
        TypeError: If the part parameter is not a string
                    or if id is provided but not a string
                    or if region_code is provided but not a string
                    or if max_results is provided but not an integer
        ValueError: If the part parameter is None or not 'snippet'
                    or if id is provided but not found in DB
                    or if max_results is provided but less than 0

    """
    if part is None:
        raise ValueError("part is required")
    if not isinstance(part, str):
        raise TypeError("part must be a string")
    if part != "snippet":
        raise ValueError("part must be 'snippet'")

    categories = DB.get("videoCategories",{})
    result_categories = [info for name,info in categories.items()]

    if id is not None:
        if not isinstance(id, str):
            raise TypeError("id must be a string")
        if id not in categories:
            raise ValueError(f"Given ID not found in DB")
        result_categories = [
            category for category in result_categories if category.get("id") == id
        ]

    if region_code is not None:
        if not isinstance(region_code, str):
            raise TypeError("region_code must be a string")
        result_categories = [
            category
            for category in result_categories
            if category.get("snippet", {}).get("regionCode") == region_code
        ]

    if max_results is not None:
        if not isinstance(max_results, int):
            raise TypeError("max_results must be an integer")
        if max_results < 0:
            raise ValueError("max_results must be greater than 0")
        max_results = min(max_results, len(result_categories))
        result_categories = result_categories[:max_results]

    return {"items": result_categories}
