from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List

from common_utils.log_complexity import log_complexity

from .SimulationEngine.db import DB


@log_complexity
@tool_spec(
    spec={
        'name': 'todoWrite',
        'description': 'Create and manage a structured task list.',
        'parameters': {
            'type': 'object',
            'properties': {
                'merge': {
                    'type': 'boolean',
                    'description': "If True, merges the provided todos with the existing list based on item 'id'. If False, replaces the entire list."
                },
                'todos': {
                    'type': 'array',
                    'description': """ A list of todo items. Each item is a dictionary that should contain at least an 'id' key. The dictionary values can be strings, integers, floats, booleans, lists, or nested dictionaries.
                    Expected keys include: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {
                                'type': 'string',
                                'description': 'Unique identifier for the todo item (required).'
                            },
                            'content': {
                                'type': 'string',
                                'description': 'The content of the todo item (required).'
                            },
                            'status': {
                                'type': 'string',
                                'description': 'The status of the todo item (required). Must be one of: "pending", "in_progress", "completed", "cancelled".'
                            }
                        },
                        'required': [
                            'id',
                            'content',
                            'status'
                        ]
                    }
                }
            },
            'required': [
                'merge',
                'todos'
            ]
        }
    }
)
def todo_write(
    merge: bool,
    todos: List[Dict[str, str]],
) -> Dict[str, List[Dict[str, str]]]:
    """Create and manage a structured task list.

    Args:
        merge (bool): If True, merges the provided todos with the existing list based on item 'id'. If False, replaces the entire list.
        todos (List[Dict[str, str]]): A list of todo items. Each item is a dictionary that should contain at least an 'id' key. The dictionary values can be strings, integers, floats, booleans, lists, or nested dictionaries.
            Expected keys include:
            - 'id' (str): Unique identifier for the todo item (required).
            - 'content' (str): The content of the todo item (required).
            - 'status' (str): The status of the todo item (required). Must be one of: "pending", "in_progress", "completed", "cancelled".

    Returns:
        Dict[str, List[Dict[str, str]]]: A dictionary containing the result with the following keys:
            - status (str): A message indicating the result of the operation.
            - todos (List[Dict[str, str]]): The updated list of todo items.

    Raises:
        TypeError: If 'merge' is not a boolean or if 'todos' is not a list.
        ValueError: If 'merge' is True and a todo item in the list is missing the 'id' key.
    """
    if not isinstance(merge, bool):
        raise TypeError("merge must be a boolean")

    if not isinstance(todos, list):
        raise TypeError("todos must be a list of dictionaries")

    if merge:
        # Merge with existing todos
        if "todos" not in DB:
            DB["todos"] = []

        existing_todos = {item["id"]: item for item in DB["todos"]}
        for item in todos:
            if "id" not in item:
                raise ValueError("Each todo item must have an 'id'")
            existing_todos[item["id"]] = item

        DB["todos"] = list(existing_todos.values())
    else:
        # Replace existing todos
        DB["todos"] = todos

    return {"status": "Todos updated successfully.", "todos": DB["todos"]}
