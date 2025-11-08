from common_utils.tool_spec_decorator import tool_spec
# gmail/Users/History.py
# Use relative import to ensure the correct DB instance is used
from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import _ensure_user, get_history_id
from typing import Optional, Dict, Any, List


@tool_spec(
    spec={
        'name': 'list_history_records',
        'description': """ Lists the history of all changes to the given mailbox.
        
        Retrieves a list of mailbox history records for the specified user.
        Note: Filtering parameters (`start_history_id`, `label_id`,
        `history_types`) and pagination (`page_token`) are included
        for API compatibility but are not fully implemented. The function currently returns
        stored history records up to `max_results`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'max_results': {
                    'type': 'integer',
                    'description': """ The maximum number of history records to return.
                    Defaults to 100. """
                },
                'page_token': {
                    'type': 'string',
                    'description': """ Page token to retrieve a specific page of results.
                    Defaults to ''. (Currently ignored). """
                },
                'start_history_id': {
                    'type': 'string',
                    'description': """ Returns history records after the specified
                    `start_history_id`. Defaults to ''. (Currently ignored). """
                },
                'label_id': {
                    'type': 'string',
                    'description': """ History records specific to the specified label in uppercase.
                    Defaults to ''. (Currently ignored). """
                },
                'history_types': {
                    'type': 'array',
                    'description': """ History types to retrieve. Defaults to None.
                    (Currently ignored). """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': []
        }
    }
)
def list(
    userId: str = "me",
    max_results: int = 100,
    page_token: str = "",
    start_history_id: str = "",
    label_id: str = "",
    history_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Lists the history of all changes to the given mailbox.

    Retrieves a list of mailbox history records for the specified user.
    Note: Filtering parameters (`start_history_id`, `label_id`,
    `history_types`) and pagination (`page_token`) are included
    for API compatibility but are not fully implemented. The function currently returns
    stored history records up to `max_results`.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        max_results (int): The maximum number of history records to return.
                     Defaults to 100.
        page_token (str): Page token to retrieve a specific page of results.
                    Defaults to ''. (Currently ignored).
        start_history_id (str): Returns history records after the specified
                         `start_history_id`. Defaults to ''. (Currently ignored).
        label_id (str): History records specific to the specified label in uppercase.
                  Defaults to ''. (Currently ignored).
        history_types (Optional[List[str]]): History types to retrieve. Defaults to None.
                       (Currently ignored).

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'history' (List[Dict]): List of history records.
            - 'nextPageToken' (Optional[str]): Token for retrieving the next page of results.
                Currently always None.
            - 'historyId' (str): The current history ID of the mailbox.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    history_data = DB["users"][userId]["history"]

    return {
        "history": history_data[:max_results],
        "nextPageToken": None,
        "historyId": get_history_id(userId),
    }
