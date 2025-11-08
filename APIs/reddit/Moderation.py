from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List, Optional

"""
Simulation of /moderation endpoints.
Manages moderation operations and data retrieval.
"""


@tool_spec(
    spec={
        'name': 'get_edited_items',
        'description': 'Retrieves recently edited posts or comments.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_edited() -> List[Dict[str, str]]:
    """
    Retrieves recently edited posts or comments.

    Returns:
        List[Dict[str, str]]:
        - If there are no edited items, returns an empty list.
        - On successful retrieval, returns a list of edited item objects, each containing:
            - id (str): The item ID
            - author (str): The author's username
            - subreddit (str): The subreddit name
            - edited_at (str): The timestamp of the edit
            - content (str): The edited content
    """
    return []


@tool_spec(
    spec={
        'name': 'get_moderation_log',
        'description': 'Retrieves the moderation log for a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_log() -> List[Dict[str, str]]:
    """
    Retrieves the moderation log for a subreddit.

    Returns:
        List[Dict[str, str]]:
        - If there are no log entries, returns an empty list.
        - On successful retrieval, returns a list of moderation log entries, each containing:
            - id (str): The log entry ID
            - action (str): The moderation action taken
            - moderator (str): The moderator's username
            - target (str): The target of the action
            - timestamp (str): When the action occurred
    """
    return []


@tool_spec(
    spec={
        'name': 'get_modqueue_items',
        'description': 'Retrieves items pending moderator action',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_modqueue() -> List[Dict[str, str | bool]]:
    """
    Retrieves items pending moderator action

    Returns:
        List[Dict[str, str | bool]]:
        - If there are no items in the modqueue, returns an empty list.
        - On successful retrieval, returns a list of items, each containing:
            - id (str): The item ID
            - author (str): The author's username
            - subreddit (str): The subreddit name
            - type (str): The type of item (post/comment)
            - reported (bool): Whether the item has been reported
    """
    return []


@tool_spec(
    spec={
        'name': 'get_reported_items',
        'description': 'Retrieves reported posts or comments.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_reports() -> List[Dict[str, str | int]]:
    """
    Retrieves reported posts or comments.

    Returns:
        List[Dict[str, str | int]]:
        - If there are no reported items, returns an empty list.
        - On successful retrieval, returns a list of reported items, each containing:
            - id (str): The item ID
            - author (str): The author's username
            - subreddit (str): The subreddit name
            - report_reason (str): The reason for the report
            - report_count (int): The number of reports
    """
    return []


@tool_spec(
    spec={
        'name': 'get_spam_items',
        'description': 'Retrieves items marked as spam.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_spam() -> List[Dict[str, str]]:
    """
    Retrieves items marked as spam.

    Returns:
        List[Dict[str, str]]:
        - If there are no spam items, returns an empty list.
        - On successful retrieval, returns a list of spam items, each containing:
            - id (str): The item ID
            - author (str): The author's username
            - subreddit (str): The subreddit name
            - marked_as_spam_by (str): The moderator who marked it as spam
            - timestamp (str): When it was marked as spam
    """
    return []


@tool_spec(
    spec={
        'name': 'get_unmoderated_items',
        'description': 'Retrieves posts or comments that are unmoderated.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_unmoderated() -> List[Dict[str, str]]:
    """
    Retrieves posts or comments that are unmoderated.

    Returns:
        List[Dict[str, str]]:
        - If there are no unmoderated items, returns an empty list.
        - On successful retrieval, returns a list of unmoderated items, each containing:
            - id (str): The item ID
            - author (str): The author's username
            - subreddit (str): The subreddit name
            - created_at (str): When the item was created
            - type (str): The type of item (post/comment)
    """
    return []


@tool_spec(
    spec={
        'name': 'get_moderated_items_by_category',
        'description': 'Retrieves moderated listings for a specific category.',
        'parameters': {
            'type': 'object',
            'properties': {
                'location': {
                    'type': 'string',
                    'description': 'The moderation category (e.g., "spam").'
                }
            },
            'required': [
                'location'
            ]
        }
    }
)
def get_about_location(location: str) -> Dict[str, Any]:
    """
    Retrieves moderated listings for a specific category.

    Args:
        location (str): The moderation category (e.g., "spam").

    Returns:
        Dict[str, Any]:
        - If the location is invalid, returns a dictionary with the key "error" and the value "Invalid location.".
        - On successful retrieval, returns a dictionary with the following keys:
            - location (str): The requested category
            - items (List[Dict[str, Any]]): A list of items in the category
    """
    return {"location": location, "items": []}


@tool_spec(
    spec={
        'name': 'accept_moderator_invite',
        'description': 'Accepts an invitation to moderate a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_accept_moderator_invite() -> Dict[str, str]:
    """
    Accepts an invitation to moderate a subreddit.

    Returns:
        Dict[str, str]:
        - On successful acceptance, returns a dictionary with the following keys:
            - status (str): The status of the operation ("moderator_invite_accepted")
    Raises:
        NoPendingInvitationError: if there is no pending invitation
    """
    return {"status": "moderator_invite_accepted"}


@tool_spec(
    spec={
        'name': 'approve_item',
        'description': 'Approves a post or comment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item to approve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_approve(id: str) -> Dict[str, Any]:
    """
    Approves a post or comment.

    Args:
        id (str): The fullname of the item to approve.

    Returns:
        Dict[str, Any]:
        - If the item ID is invalid, returns a dictionary with the key "error" and the value "Invalid item ID.".
        - If the item is already approved, returns a dictionary with the key "error" and the value "Item already approved.".
        - On successful approval, returns a dictionary with the following keys:
            - status (str): The status of the operation ("approved")
            - id (str): The ID of the approved item
    """
    return {"status": "approved", "id": id}


@tool_spec(
    spec={
        'name': 'distinguish_item',
        'description': "Distinguishes a moderator's post or comment.",
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item.'
                },
                'how': {
                    'type': 'string',
                    'description': 'The method of distinction (e.g., "yes", "no", "admin").'
                }
            },
            'required': [
                'id',
                'how'
            ]
        }
    }
)
def post_api_distinguish(id: str, how: str) -> Dict[str, Any]:
    """
    Distinguishes a moderator's post or comment.

    Args:
        id (str): The fullname of the item.
        how (str): The method of distinction (e.g., "yes", "no", "admin").

    Returns:
        Dict[str, Any]:
        - If the item ID is invalid, returns a dictionary with the key "error" and the value "Invalid item ID.".
        - If the distinction method is invalid, returns a dictionary with the key "error" and the value "Invalid distinction method.".
        - On successful distinction, returns a dictionary with the following keys:
            - status (str): The status of the operation ("distinguished")
            - id (str): The ID of the distinguished item
            - how (str): The method of distinction used
    """
    return {"status": "distinguished", "id": id, "how": how}


@tool_spec(
    spec={
        'name': 'ignore_item_reports',
        'description': 'Ignores future reports on a specific item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_ignore_reports(id: str) -> Dict[str, Any]:
    """
    Ignores future reports on a specific item.

    Args:
        id (str): The fullname of the item.

    Returns:
        Dict[str, Any]:
        - If the item ID is invalid, returns a dictionary with the key "error" and the value "Invalid item ID.".
        - If reports are already being ignored, returns a dictionary with the key "error" and the value "Reports already being ignored.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("ignored_reports")
            - id (str): The ID of the item
    """
    return {"status": "ignored_reports", "id": id}


@tool_spec(
    spec={
        'name': 'leave_contributor_status',
        'description': 'Removes the current user from contributor status.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_leavecontributor() -> Dict[str, str]:
    """
    Removes the current user from contributor status.

    Returns:
        Dict[str, str]:
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("left_contributor")
    Raises:
        UserNotContributorError: if the user is not contributor
    """
    return {"status": "left_contributor"}


@tool_spec(
    spec={
        'name': 'leave_moderator_status',
        'description': 'Removes the current user from moderator status.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_leavemoderator() -> Dict[str, str]:
    """
    Removes the current user from moderator status.

    Returns:
        Dict[str, str]:
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("left_moderator")
    Raises:
        UserNotModeratorError: if the user is not a moderator
    """
    return {"status": "left_moderator"}


@tool_spec(
    spec={
        'name': 'remove_item',
        'description': 'Removes a post or comment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item to remove.'
                },
                'spam': {
                    'type': 'boolean',
                    'description': 'Indicates if the item should be marked as spam.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_remove(id: str, spam: Optional[bool] = False) -> Dict[str, Any]:
    """
    Removes a post or comment.

    Args:
        id (str): The fullname of the item to remove.
        spam (Optional[bool]): Indicates if the item should be marked as spam.

    Returns:
        Dict[str, Any]:
        - If the item ID is invalid, returns a dictionary with the key "error" and the value "Invalid item ID.".
        - If the item is already removed, returns a dictionary with the key "error" and the value "Item already removed.".
        - On successful removal, returns a dictionary with the following keys:
            - status (str): The status of the operation ("removed")
            - id (str): The ID of the removed item
            - spam (bool): Whether the item was marked as spam
    """
    return {"status": "removed", "id": id, "spam": spam}


@tool_spec(
    spec={
        'name': 'show_removed_comment',
        'description': 'Re-approves a comment that was removed.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the comment.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_show_comment(id: str) -> Dict[str, Any]:
    """
    Re-approves a comment that was removed.

    Args:
        id (str): The fullname of the comment.

    Returns:
        Dict[str, Any]:
        - If the comment ID is invalid, returns a dictionary with the key "error" and the value "Invalid comment ID.".
        - If the comment is not removed, returns a dictionary with the key "error" and the value "Comment is not removed.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("comment_shown")
            - id (str): The ID of the comment
    """
    return {"status": "comment_shown", "id": id}


@tool_spec(
    spec={
        'name': 'snooze_item_reports',
        'description': 'Snoozes reports on a specific item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_snooze_reports(id: str) -> Dict[str, Any]:
    """
    Snoozes reports on a specific item.

    Args:
        id (str): The fullname of the item.

    Returns:
        Dict[str, Any]:
        - If the item ID is invalid, returns a dictionary with the key "error" and the value "Invalid item ID.".
        - If reports are already snoozed, returns a dictionary with the key "error" and the value "Reports already snoozed.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("reports_snoozed")
            - id (str): The ID of the item
    """
    return {"status": "reports_snoozed", "id": id}


@tool_spec(
    spec={
        'name': 'unignore_item_reports',
        'description': 'Stops ignoring reports on a specific item.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_unignore_reports(id: str) -> Dict[str, Any]:
    """
    Stops ignoring reports on a specific item.

    Args:
        id (str): The fullname of the item.

    Returns:
        Dict[str, Any]:
        - If the item ID is invalid, returns a dictionary with the key "error" and the value "Invalid item ID.".
        - If reports are not being ignored, returns a dictionary with the key "error" and the value "Reports are not being ignored.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("reports_unignored")
            - id (str): The ID of the item
    """
    return {"status": "reports_unignored", "id": id}


@tool_spec(
    spec={
        'name': 'unsnooze_item_reports',
        'description': 'Unsnoozes reports, resuming notifications.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_unsnooze_reports(id: str) -> Dict[str, Any]:
    """
    Unsnoozes reports, resuming notifications.

    Args:
        id (str): The fullname of the item.

    Returns:
        Dict[str, Any]:
        - If the item ID is invalid, returns a dictionary with the key "error" and the value "Invalid item ID.".
        - If reports are not snoozed, returns a dictionary with the key "error" and the value "Reports are not snoozed.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("reports_unsnoozed")
            - id (str): The ID of the item
    """
    return {"status": "reports_unsnoozed", "id": id}


@tool_spec(
    spec={
        'name': 'update_post_crowd_control_level',
        'description': 'Updates the crowd control level for a post.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                },
                'level': {
                    'type': 'integer',
                    'description': 'The new crowd control level.'
                }
            },
            'required': [
                'id',
                'level'
            ]
        }
    }
)
def post_api_update_crowd_control_level(id: str, level: int) -> Dict[str, Any]:
    """
    Updates the crowd control level for a post.

    Args:
        id (str): The fullname of the post.
        level (int): The new crowd control level.

    Returns:
        Dict[str, Any]:
        - If the post ID is invalid, returns a dictionary with the key "error" and the value "Invalid post ID.".
        - If the level is invalid (not between 0 and 3), returns a dictionary with the key "error" and the value "Invalid crowd control level.".
        - On successful update, returns a dictionary with the following keys:
            - status (str): The status of the operation ("crowd_control_updated")
            - id (str): The ID of the post
            - level (int): The new crowd control level
    """
    return {"status": "crowd_control_updated", "id": id, "level": level}


@tool_spec(
    spec={
        'name': 'get_subreddit_stylesheet',
        'description': "Retrieves the subreddit's stylesheet code.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_stylesheet() -> str:
    """
    Retrieves the subreddit's stylesheet code.

    Returns:
        str:
        - If there is no stylesheet, returns an empty string.
        - On successful retrieval, returns the stylesheet code as a string.
    """
    return "/* subreddit stylesheet placeholder */"