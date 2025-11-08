from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/StatusCategoryApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import MissingRequiredFieldError
from typing import Any, Dict

@tool_spec(
    spec={
        'name': 'get_all_status_categories',
        'description': """ Get all status categories.
        
        This method returns all status categories in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_status_categories() -> Dict[str, Any]:
    """
    Get all status categories.

    This method returns all status categories in the system.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - statusCategories (List[Optional[Dict[str, Any]]]): A list of status categories
                - id (str): The id of the status category
                - name (str): The name of the status category
                - description (str): The description of the status category
                - color (str): The color of the status category
                Or empty list if no status categories are found.
    """
    if "status_categories" not in DB:
        DB["status_categories"] = {}
    return {"statusCategories": list(DB["status_categories"].values())}


@tool_spec(
    spec={
        'name': 'get_status_category_by_id',
        'description': """ Get a status category by id.
        
        This method returns a status category by id. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'cat_id': {
                    'type': 'string',
                    'description': 'The id of the status category'
                }
            },
            'required': [
                'cat_id'
            ]
        }
    }
)
def get_status_category(cat_id: str) -> Dict[str, Any]:
    """
    Get a status category by id.

    This method returns a status category by id.

    Args:
        cat_id (str): The id of the status category

    Returns:
        Dict[str, Any]: A dictionary containing:
            - statusCategory (Dict[str, Any]): The status category
                - id (str): The id of the status category
                - name (str): The name of the status category
                - description (str): The description of the status category
                - color (str): The color of the status category

    Raises:
        MissingRequiredFieldError: If cat_id is not provided.
        TypeError: If cat_id is not a string.
        ValueError: If the status category is not found
    """
    if not cat_id:
        raise MissingRequiredFieldError(field_name="cat_id")
    if not isinstance(cat_id, str):
        raise TypeError("cat_id must be a string")

    if "status_categories" not in DB:
        DB["status_categories"] = {}

    if cat_id not in DB["status_categories"]:
        raise ValueError(f"Status category '{cat_id}' not found.")
    
    return {"statusCategory": DB["status_categories"][cat_id]}
