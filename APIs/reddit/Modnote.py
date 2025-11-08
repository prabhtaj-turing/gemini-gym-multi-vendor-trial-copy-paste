from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB
from typing import Dict, Any

"""
Simulation of /modnote endpoints.
Manages moderator notes.
"""

@tool_spec(
    spec={
        'name': 'delete_moderator_note',
        'description': 'Deletes a moderator note.',
        'parameters': {
            'type': 'object',
            'properties': {
                'note_id': {
                    'type': 'string',
                    'description': 'The identifier of the note to delete.'
                }
            },
            'required': [
                'note_id'
            ]
        }
    }
)
def delete_api_mod_notes(note_id: str) -> Dict[str, Any]:
    """
    Deletes a moderator note.

    Args:
        note_id (str): The identifier of the note to delete.

    Returns:
        Dict[str, Any]:
        - If the note ID is invalid, returns a dictionary with the key "error" and the value "Invalid note ID.".
        - If the note does not exist, returns a dictionary with the key "error" and the value "Note not found.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("note_deleted")
            - note_id (str): The ID of the deleted note
    """
    return {"status": "note_deleted", "note_id": note_id}

@tool_spec(
    spec={
        'name': 'get_recent_moderator_notes_for_user',
        'description': 'Retrieves recent moderator notes for a user in a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user': {
                    'type': 'string',
                    'description': 'The username for whom to retrieve notes.'
                },
                'subreddit': {
                    'type': 'string',
                    'description': 'The subreddit identifier.'
                }
            },
            'required': [
                'user',
                'subreddit'
            ]
        }
    }
)
def get_api_mod_notes_recent(user: str, subreddit: str) -> Dict[str, Any]:
    """
    Retrieves recent moderator notes for a user in a subreddit.

    Args:
        user (str): The username for whom to retrieve notes.
        subreddit (str): The subreddit identifier.

    Returns:
        Dict[str, Any]:
        - If the user is invalid, returns a dictionary with the key "error" and the value "Invalid username.".
        - If the subreddit is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit.".
        - On successful retrieval, returns a dictionary with the following keys:
            - user (str): The username
            - subreddit (str): The subreddit identifier
            - notes (List[Dict[str, Any]]): A list of moderator notes, each containing:
                - id (str): The note ID
                - text (str): The note content
                - created_at (str): The timestamp of note creation
                - moderator (str): The moderator who created the note
    """
    return {"user": user, "subreddit": subreddit, "notes": DB.get("modnotes", {}).get(user, [])} # Use .get for safety