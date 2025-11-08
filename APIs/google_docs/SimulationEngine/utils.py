"""
Utility functions for Google Docs API simulation.
"""
from .db import DB

def _ensure_user(userId: str = "me") -> None:
    """Ensure that the user entry exists in DB, creating if necessary.
    
    Args:
        userId (str): The ID of the user to ensure exists.
    """
    if userId not in DB['users']:
        DB['users'][userId] = {
            'about': {
                'user': {
                    'emailAddress': f'{userId}@example.com',
                    'displayName': f'User {userId}'
                },
                'storageQuota': {
                    'limit': '10000000000',
                    'usage': '0'
                }
            },
            'files': {},
            'drives': {},
            'comments': {},
            'replies': {},
            'labels': {},
            'accessproposals': {},
            'counters': {
                'file': 0,
                'drive': 0,
                'comment': 0,
                'reply': 0,
                'label': 0,
                'accessproposal': 0,
                'revision': 0
            }
        }

def _ensure_file(fileId: str, userId: str = "me") -> None:
    """Ensure file exists in the user's files.
    
    Args:
        fileId (str): The ID of the file to ensure exists.
        userId (str): The ID of the user who owns the file.
    """
    _ensure_user(userId)

    if fileId not in DB['users'][userId]['files']:
        DB['users'][userId]['files'][fileId] = {}

    # Ensure global collections exist
    for collection in ['comments', 'replies', 'labels', 'accessproposals']:
        if collection not in DB['users'][userId]:
            DB['users'][userId][collection] = {}

def _next_counter(counter_name: str, userId: str = "me") -> int:
    """Retrieve the next counter value from DB['users'][userId]['counters'][counter_name].
    
    Args:
        counter_name (str): The name of the counter to increment.
        userId (str): The ID of the user whose counter to increment.
        
    Returns:
        int: The next counter value.
    """
    current_val = DB['users'][userId]['counters'].get(counter_name, 0)
    new_val = current_val + 1
    DB['users'][userId]['counters'][counter_name] = new_val
    return new_val 