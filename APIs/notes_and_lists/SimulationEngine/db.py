
import json
from typing import Dict, Any
from copy import deepcopy


DB: Dict[str, Any] = {
    "notes": {
        "note_1": {
            "id": "note_1",
            "title": "Meeting Notes",
            "content": "Action items:\n- Finalize Q3 budget\n- Schedule team offsite\n- Update project timeline",
            "created_at": "2023-10-15T09:30:00Z",
            "updated_at": "2023-10-16T14:22:00Z",
            "content_history": [
                "Action items:\n- Finalize Q3 budget"
            ]
        },
        "note_2": {
            "id": "note_2",
            "title": "Recipe Ideas",
            "content": "Dinner options:\n1. Mushroom risotto\n2. Lentil curry\n3. Salmon with roasted vegetables",
            "created_at": "2023-10-10T18:45:00Z",
            "updated_at": "2023-10-12T11:30:00Z",
            "content_history": []
        },
        "note_3": {
            "id": "note_3",
            "title": "Book Summary: Atomic Habits",
            "content": "Key takeaways:\n- Habits are compound interest of self-improvement\n- Make cues obvious and rewards satisfying\n- Focus on systems rather than goals",
            "created_at": "2023-10-05T15:10:00Z",
            "updated_at": "2023-10-05T15:10:00Z",
            "content_history": []
        }
    },
    "lists": {
        "list_1": {
            "id": "list_1",
            "title": "Weekly Groceries",
            "items": {
                "item_1a": {
                    "id": "item_1a",
                    "content": "Milk",
                    "completed": False,
                    "created_at": "2023-10-17T08:15:00Z",
                    "updated_at": "2023-10-17T08:15:00Z"
                },
                "item_1b": {
                    "id": "item_1b",
                    "content": "Eggs",
                    "completed": False,
                    "created_at": "2023-10-17T08:15:00Z",
                    "updated_at": "2023-10-17T08:15:00Z"
                },
                "item_1c": {
                    "id": "item_1c",
                    "content": "Bread",
                    "completed": True,
                    "created_at": "2023-10-17T08:15:00Z",
                    "updated_at": "2023-10-17T08:15:00Z"
                }
            },
            "created_at": "2023-10-17T08:15:00Z",
            "updated_at": "2023-10-17T08:15:00Z",
            "item_history": {}
        },
        "list_2": {
            "id": "list_2",
            "title": "Project Tasks",
            "items": {
                "item_2a": {
                    "id": "item_2a",
                    "content": "Design API endpoints",
                    "completed": False,
                    "created_at": "2023-10-14T10:30:00Z",
                    "updated_at": "2023-10-14T10:30:00Z"
                },
                "item_2b": {
                    "id": "item_2b",
                    "content": "Write documentation",
                    "completed": False,
                    "created_at": "2023-10-14T10:30:00Z",
                    "updated_at": "2023-10-16T13:45:00Z"
                },
                "item_2c": {
                    "id": "item_2c",
                    "content": "Test authentication flow",
                    "completed": True,
                    "created_at": "2023-10-15T11:20:00Z",
                    "updated_at": "2023-10-15T11:20:00Z"
                }
            },
            "created_at": "2023-10-14T10:30:00Z",
            "updated_at": "2023-10-16T13:45:00Z",
            "item_history": {
                "item_2b": [
                    "Create documentation"
                ]
            }
        },
        "list_3": {
            "id": "list_3",
            "title": "Birthday Party Planning",
            "items": {
                "item_3a": {
                    "id": "item_3a",
                    "content": "Send invitations",
                    "completed": False,
                    "created_at": "2023-10-01T14:00:00Z",
                    "updated_at": "2023-10-05T16:30:00Z"
                },
                "item_3b": {
                    "id": "item_3b",
                    "content": "Order cake",
                    "completed": True,
                    "created_at": "2023-10-01T14:00:00Z",
                    "updated_at": "2023-10-01T14:00:00Z"
                }
            },
            "created_at": "2023-10-01T14:00:00Z",
            "updated_at": "2023-10-05T16:30:00Z",
            "item_history": {
                "item_3a": [
                    "Create guest list",
                    "Prepare invitations"
                ]
            }
        }
    },
    "operation_log": {
        "op_1": {
            "id": "op_1",
            "operation_type": "create_note",
            "target_id": "note_1",
            "parameters": {
                "title": "Meeting Notes",
                "text_content": "Action items:\n- Finalize Q3 budget"
            },
            "timestamp": "2023-10-15T09:30:00Z",
            "snapshot": {
                "id": "note_1",
                "title": None,
                "content": "",
                "created_at": "2023-10-15T09:30:00Z",
                "updated_at": "2023-10-15T09:30:00Z",
                "content_history": []
            }
        },
        "op_2": {
            "id": "op_2",
            "operation_type": "update_note",
            "target_id": "note_1",
            "parameters": {
                "update_type": "APPEND",
                "text_content": "\n- Schedule team offsite\n- Update project timeline"
            },
            "timestamp": "2023-10-16T14:22:00Z",
            "snapshot": {
                "id": "note_1",
                "title": "Meeting Notes",
                "content": "Action items:\n- Finalize Q3 budget",
                "created_at": "2023-10-15T09:30:00Z",
                "updated_at": "2023-10-15T09:30:00Z",
                "content_history": [
                    "Action items:\n- Finalize Q3 budget"
                ]
            }
        },
        "op_3": {
            "id": "op_3",
            "operation_type": "add_to_list",
            "target_id": "list_2",
            "parameters": {
                "list_id": "list_2",
                "elements_to_add": [
                    "Test authentication flow"
                ],
                "is_bulk_mutation": False
            },
            "timestamp": "2023-10-15T11:20:00Z",
            "snapshot": {
                "id": "list_2",
                "title": "Project Tasks",
                "items": {
                    "item_2a": {
                        "id": "item_2a",
                        "content": "Design API endpoints",
                        "completed": False,
                        "created_at": "2023-10-14T10:30:00Z",
                        "updated_at": "2023-10-14T10:30:00Z"
                    },
                    "item_2b": {
                        "id": "item_2b",
                        "content": "Create documentation",
                        "completed": False,
                        "created_at": "2023-10-14T10:30:00Z",
                        "updated_at": "2023-10-14T10:30:00Z"
                    }
                },
                "created_at": "2023-10-14T10:30:00Z",
                "updated_at": "2023-10-14T10:30:00Z",
                "item_history": {}
            }
        }
    },
    "title_index": {
        "Meeting Notes": [
            "note_1"
        ],
        "Recipe Ideas": [
            "note_2"
        ],
        "Book Summary: Atomic Habits": [
            "note_3"
        ],
        "Weekly Groceries": [
            "list_1"
        ],
        "Project Tasks": [
            "list_2"
        ],
        "Birthday Party Planning": [
            "list_3"
        ]
    },
    "content_index": {
        "budget": [
            "note_1"
        ],
        "risotto": [
            "note_2"
        ],
        "habits": [
            "note_3"
        ],
        "milk": [
            "list_1"
        ],
        "documentation": [
            "list_2"
        ],
        "invitations": [
            "list_3"
        ]
    }
}

# A snapshot of the initial state of the DB for resetting purposes.
_INITIAL_DB_STATE = deepcopy(DB)

def reset_db():
    """Reset database to initial state"""
    global DB
    DB.clear()
    DB.update(deepcopy(_INITIAL_DB_STATE))

def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.
    
    Args:
        filepath (str): Path to save the state file.
            Must be a valid file path with write permissions.
    
    Raises:
        IOError: If the file cannot be written.
        json.JSONDecodeError: If the state cannot be serialized to JSON.
    
    Example:
        >>> save_state("./state.json")
    """
    with open(filepath, 'w') as f:
        json.dump(DB, f, indent=2)

def load_state(filepath: str = 'DBs/NotesAndListsDefaultDB.json') -> None:
    """Load state from a JSON file.
    """
    global DB
    with open(filepath, 'r') as f:
        new_data = json.load(f)
        DB.clear()
        DB.update(new_data)


def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
