from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/ProjectCategoryApi.py
from typing import Dict, Any
from .SimulationEngine.db import DB
from typing import Dict, Any
from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'get_all_project_categories',
        'description': """ Get all project categories.
        
        This method returns all project categories in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_project_categories() -> Dict[str, Any]:
    """
    Get all project categories.

    This method returns all project categories in the system.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - categories (List[Dict[str, Any]]): A list of project categories
                - id (str): The id of the project category
                - name (str): The name of the project category
    """
    return {"categories": list(DB["project_categories"].values())}


@tool_spec(
    spec={
        'name': 'get_project_category_by_id',
        'description': """ Get a project category by id.
        
        This method returns a project category by id. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'cat_id': {
                    'type': 'string',
                    'description': 'The id of the project category'
                }
            },
            'required': [
                'cat_id'
            ]
        }
    }
)
def get_project_category(cat_id: str) -> Dict[str, Any]:
    """
    Get a project category by id.

    This method returns a project category by id.

    Args:
        cat_id (str): The id of the project category

    Returns:
        Dict[str, Any]: A dictionary containing:
            - category (Dict[str, Any]): The project category
                - id (str): The id of the project category
                - name (str): The name of the project category

    Raises:
        TypeError: If the cat_id is not a string
        ValueError: If the cat_id is empty or not found in the database
    """
    # input validation
    if not isinstance(cat_id, str):
        raise TypeError("cat_id must be a string")
    
    if cat_id.strip() == "":
        raise ValueError("cat_id cannot be empty")
    
    # get project category from the database by cat_id
    c = DB["project_categories"].get(cat_id)
    if not c:
        raise ValueError(f"Project category '{cat_id}' not found.")
    return c
