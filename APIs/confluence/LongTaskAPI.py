from common_utils.tool_spec_decorator import tool_spec
# APIs/confluence/LongTaskAPI.py
from typing import Dict, List, Any, Optional
from confluence.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'get_long_tasks',
        'description': """ Returns a paginated list of all long-running tasks.
        
        Retrieves a list of task dictionaries for all long-running tasks.
        Note: The 'expand' parameter is accepted for API compatibility but is not currently processed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'expand': {
                    'type': 'string',
                    'description': """ A comma-separated list of properties to expand.
                    Defaults to None.
                    Note: Not implemented. """
                },
                'start': {
                    'type': 'integer',
                    'description': """ The starting index for pagination. Must be >= 0.
                    Defaults to 0. """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of tasks to return. Must be >= 0.
                    Defaults to 100. """
                }
            },
            'required': []
        }
    }
)
def get_long_tasks(
    expand: Optional[str] = None, start: int = 0, limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Returns a paginated list of all long-running tasks.

    Retrieves a list of task dictionaries for all long-running tasks.
    Note: The 'expand' parameter is accepted for API compatibility but is not currently processed.

    Args:
        expand (Optional[str]): A comma-separated list of properties to expand.
            Defaults to None.
            Note: Not implemented.
        start (int): The starting index for pagination. Must be >= 0.
            Defaults to 0.
        limit (int): The maximum number of tasks to return. Must be >= 0.
            Defaults to 100.

    Returns:
        List[Dict[str, Any]]: A list of task dictionaries, each containing:
            - id (str): The unique identifier of the task.
            - status (str): The current status of the task (e.g., "in_progress", "completed", "failed").
            - description (str): A description of the task.

    Raises:
        ValueError: If the start or limit parameters are negative.
    """
    if start < 0 or limit < 0:
        raise ValueError("start and limit must be non-negative")

    tasks = list(DB["long_tasks"].values())
    return tasks[start : start + limit]


@tool_spec(
    spec={
        'name': 'get_long_task_details',
        'description': """ Returns a specific long-running task by its ID.
        
        Retrieves the long-running task dictionary that matches the provided task ID.
        Note: The 'expand' parameter is accepted for API compatibility but is not currently processed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The unique identifier of the task.'
                },
                'expand': {
                    'type': 'string',
                    'description': """ A comma-separated list of properties to expand.
                    Defaults to None. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_long_task(id: str, expand: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns a specific long-running task by its ID.

    Retrieves the long-running task dictionary that matches the provided task ID.
    Note: The 'expand' parameter is accepted for API compatibility but is not currently processed.

    Args:
        id (str): The unique identifier of the task.
        expand (Optional[str]): A comma-separated list of properties to expand.
            Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary representing the task, containing:
            - id (str): The unique identifier of the task.
            - status (str): The current status of the task.
            - description (str): A description of the task.

    Raises:
        TypeError: If the provided id is not a string, or expand is not a string when provided.
        ValueError: If the id is empty, expand is an empty string, or a task with the specified ID is not found.
    """
    if not isinstance(id, str):
        raise TypeError("id must be a string")
    if not id or not id.strip():
        raise ValueError("id must be a non-empty string")
    if expand is not None:
        if not isinstance(expand, str):
            raise TypeError("expand must be a string or None")
        if expand.strip() == "":
            raise ValueError("expand must be a non-empty string or None")

    # Accept expand for compatibility but ignore its value (no assumptions)
    task = DB["long_tasks"].get(id)
    if not task:
        raise ValueError(f"Task with id={id} not found.")
    return task
