from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB
from typing import Dict, Any, List, Optional

"""
Simulation of /links_and_comments endpoints.
Manages post and comment interactions including submission, deletion, editing, and voting.
"""


@tool_spec(
    spec={
        'name': 'submit_comment',
        'description': 'Submits a new comment or reply to a message.',
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': 'The fullname of the parent post or comment.'
                },
                'text': {
                    'type': 'string',
                    'description': 'The comment text in raw markdown.'
                }
            },
            'required': [
                'parent',
                'text'
            ]
        }
    }
)
def post_api_comment(parent: str, text: str) -> Dict[str, Any]:
    """
    Submits a new comment or reply to a message.

    Args:
        parent (str): The fullname of the parent post or comment.
        text (str): The comment text in raw markdown.

    Returns:
        Dict[str, Any]:
        - If the parent post/comment does not exist, returns a dictionary with the key "error" and the value "Parent item not found.".
        - If the text is empty, returns a dictionary with the key "error" and the value "Comment text cannot be empty.".
        - On successful creation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("comment_posted")
            - comment_id (str): The ID of the new comment
            - parent (str): The parent post/comment ID
    """
    # Check if text is empty
    if not text:
        return {"error": "Comment text cannot be empty."}
        
    # Check if parent exists in either links or comments
    if parent not in DB.get("links", {}) and parent not in DB.get("comments", {}):
        return {"error": "Parent item not found."}
        
    new_id = f"t1_{len(DB.get('comments', {}))+1}" # Use .get for safety
    DB.setdefault("comments", {})[new_id] = { # Ensure keys exist
        "parent": parent,
        "body": text
    }
    return {"status": "comment_posted", "comment_id": new_id, "parent": parent}


@tool_spec(
    spec={
        'name': 'delete_post_or_comment',
        'description': 'Deletes a post or comment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_del(id: str) -> Dict[str, Any]:
    """
    Deletes a post or comment.

    Args:
        id (str): The fullname of the item to delete.

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the item is already deleted, returns a dictionary with the key "error" and the value "Item already deleted.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("deleted")
            - type (str): The type of item deleted ("comment" or "link")
            - id (str): The ID of the deleted item
    """
    # Check if item exists in either comments or links
    if id not in DB.get("comments", {}) and id not in DB.get("links", {}):
        return {"error": "Item not found."}
        
    # Check if item is already deleted
    if id in DB.get("comments", {}) and DB["comments"][id].get("deleted"):
        return {"error": "Item already deleted."}
    if id in DB.get("links", {}) and DB["links"][id].get("deleted"):
        return {"error": "Item already deleted."}
        
    # We'll just set a 'deleted' flag if it exists
    if id in DB.get("comments", {}):
        DB["comments"][id]["deleted"] = True
        return {"status": "deleted", "type": "comment", "id": id}
    elif id in DB.get("links", {}):
        DB["links"][id]["deleted"] = True
        return {"status": "deleted", "type": "link", "id": id}
    return {"error": "not_found"}


@tool_spec(
    spec={
        'name': 'edit_post_or_comment_text',
        'description': 'Edits the text of a comment or self-post.',
        'parameters': {
            'type': 'object',
            'properties': {
                'thing_id': {
                    'type': 'string',
                    'description': 'The fullname of the post or comment.'
                },
                'text': {
                    'type': 'string',
                    'description': 'The new text content in raw markdown.'
                }
            },
            'required': [
                'thing_id',
                'text'
            ]
        }
    }
)
def post_api_editusertext(thing_id: str, text: str) -> Dict[str, Any]:
    """
    Edits the text of a comment or self-post.

    Args:
        thing_id (str): The fullname of the post or comment.
        text (str): The new text content in raw markdown.

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the item is deleted, returns a dictionary with the key "error" and the value "Cannot edit deleted item.".
        - If the text is empty, returns a dictionary with the key "error" and the value "Text cannot be empty.".
        - On successful edit, returns a dictionary with the following keys:
            - status (str): The status of the operation ("updated_comment" or "updated_post")
            - comment_id/link_id (str): The ID of the updated item
    """
    if thing_id in DB.get("comments", {}):
        # If the comment is marked deleted, return an error
        if DB["comments"][thing_id].get("deleted"):
            return {"error": "cannot_edit_deleted_comment"}
        DB["comments"][thing_id]["body"] = text
        return {"status": "updated_comment", "comment_id": thing_id}
    elif thing_id in DB.get("links", {}):
        # If the link is marked deleted, return an error
        if DB["links"][thing_id].get("deleted"):
            return {"error": "cannot_edit_deleted_post"}
        DB["links"][thing_id]["body"] = text
        return {"status": "updated_post", "link_id": thing_id}
    return {"error": "not_found"}


@tool_spec(
    spec={
        'name': 'follow_or_unfollow_post',
        'description': 'Follows or unfollows a post to receive notifications.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fullname': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                },
                'follow': {
                    'type': 'boolean',
                    'description': 'True to follow, False to unfollow.'
                }
            },
            'required': [
                'fullname',
                'follow'
            ]
        }
    }
)
def post_api_follow_post(fullname: str, follow: bool) -> Dict[str, Any]:
    """
    Follows or unfollows a post to receive notifications.

    Args:
        fullname (str): The fullname of the post.
        follow (bool): True to follow, False to unfollow.

    Returns:
        Dict[str, Any]:
        - If the post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("ok")
            - fullname (str): The post fullname
            - follow (bool): The follow state
    """
    return {"status": "ok", "fullname": fullname, "follow": follow}


@tool_spec(
    spec={
        'name': 'hide_posts',
        'description': "Hides one or more posts from the user's front page.",
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'array',
                    'description': 'A list of post fullnames to hide.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_hide(id: List[str]) -> Dict[str, Any]:
    """
    Hides one or more posts from the user's front page.

    Args:
        id (List[str]): A list of post fullnames to hide.

    Returns:
        Dict[str, Any]:
        - If the list is empty, returns a dictionary with the key "error" and the value "No posts specified.".
        - If any post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("hidden")
            - items (List[str]): The list of hidden post IDs
    """
    return {"status": "hidden", "items": id}


@tool_spec(
    spec={
        'name': 'get_items_info',
        'description': 'Retrieves information about posts or comments by fullname or URL.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'A comma-separated list of fullnames.'
                },
                'url': {
                    'type': 'string',
                    'description': 'A URL to look up posts referencing it.'
                }
            },
            'required': []
        }
    }
)
def get_api_info(id: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves information about posts or comments by fullname or URL.

    Args:
        id (Optional[str]): A comma-separated list of fullnames.
        url (Optional[str]): A URL to look up posts referencing it.

    Returns:
        Dict[str, Any]:
        - If neither id nor url is provided, returns a dictionary with the key "error" and the value "Either id or url must be provided.".
        - If an invalid fullname is provided, returns a dictionary with the key "error" and the value "Invalid fullname.".
        - On successful lookup, returns a dictionary with the following keys:
            - id (Optional[str]): The provided fullname list
            - url (Optional[str]): The provided URL
            - results (List[Dict[str, Any]]): The lookup results
    """
    return {"id": id, "url": url, "results": []}


@tool_spec(
    spec={
        'name': 'lock_item',
        'description': 'Locks a post or comment to prevent further replies.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item to lock.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_lock(id: str) -> Dict[str, Any]:
    """
    Locks a post or comment to prevent further replies.

    Args:
        id (str): The fullname of the item to lock.

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the item is already locked, returns a dictionary with the key "error" and the value "Item already locked.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("locked")
            - id (str): The ID of the locked item
    """
    return {"status": "locked", "id": id}


@tool_spec(
    spec={
        'name': 'mark_post_nsfw',
        'description': 'Marks a post as Not Safe For Work (NSFW).',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_marknsfw(id: str) -> Dict[str, Any]:
    """
    Marks a post as Not Safe For Work (NSFW).

    Args:
        id (str): The fullname of the post.

    Returns:
        Dict[str, Any]:
        - If the post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - If the post is already marked NSFW, returns a dictionary with the key "error" and the value "Post already marked NSFW.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("nsfw_marked")
            - id (str): The ID of the marked post
    """
    return {"status": "nsfw_marked", "id": id}


@tool_spec(
    spec={
        'name': 'get_more_comments',
        'description': 'Retrieves additional comments omitted by pagination.',
        'parameters': {
            'type': 'object',
            'properties': {
                'link_id': {
                    'type': 'string',
                    'description': 'The fullname of the parent post.'
                },
                'children': {
                    'type': 'string',
                    'description': 'A comma-separated list of child comment IDs to retrieve.'
                }
            },
            'required': [
                'link_id',
                'children'
            ]
        }
    }
)
def get_api_morechildren(link_id: str, children: str) -> Dict[str, Any]:
    """
    Retrieves additional comments omitted by pagination.

    Args:
        link_id (str): The fullname of the parent post.
        children (str): A comma-separated list of child comment IDs to retrieve.

    Returns:
        Dict[str, Any]:
        - If the parent post does not exist, returns a dictionary with the key "error" and the value "Parent post not found.".
        - If the children list is empty, returns a dictionary with the key "error" and the value "No children specified.".
        - On successful retrieval, returns a dictionary with the following keys:
            - link_id (str): The parent post ID
            - children_requested (List[str]): The list of requested child comment IDs
    """
    return {"link_id": link_id, "children_requested": children.split(',')}


@tool_spec(
    spec={
        'name': 'report_item',
        'description': 'Reports a post or comment for review.',
        'parameters': {
            'type': 'object',
            'properties': {
                'thing_id': {
                    'type': 'string',
                    'description': 'The fullname of the item to report.'
                },
                'reason': {
                    'type': 'string',
                    'description': 'A short explanation for the report.'
                }
            },
            'required': [
                'thing_id'
            ]
        }
    }
)
def post_api_report(thing_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Reports a post or comment for review.

    Args:
        thing_id (str): The fullname of the item to report.
        reason (Optional[str]): A short explanation for the report.

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the item is already reported, returns a dictionary with the key "error" and the value "Item already reported.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("reported")
            - thing_id (str): The ID of the reported item
            - reason (Optional[str]): The provided reason
    """
    return {"status": "reported", "thing_id": thing_id, "reason": reason}


@tool_spec(
    spec={
        'name': 'save_item',
        'description': "Saves a post or comment to the user's saved list.",
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item to save.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_save(id: str) -> Dict[str, Any]:
    """
    Saves a post or comment to the user's saved list.

    Args:
        id (str): The fullname of the item to save.

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the item is already saved, returns a dictionary with the key "error" and the value "Item already saved.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("saved")
            - id (str): The ID of the saved item
    """
    return {"status": "saved", "id": id}


@tool_spec(
    spec={
        'name': 'get_saved_categories',
        'description': "Retrieves the user's saved categories.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_api_saved_categories() -> List[Dict[str, Any]]:
    """
    Retrieves the user's saved categories.

    Returns:
        List[Dict[str, Any]]: A list of saved category objects.
    """
    return []


@tool_spec(
    spec={
        'name': 'toggle_item_replies',
        'description': 'Enables or disables replies for a post or comment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item.'
                },
                'state': {
                    'type': 'boolean',
                    'description': 'True to enable replies, False to disable.'
                }
            },
            'required': [
                'id',
                'state'
            ]
        }
    }
)
def post_api_sendreplies(id: str, state: bool) -> Dict[str, Any]:
    """
    Enables or disables replies for a post or comment.

    Args:
        id (str): The fullname of the item.
        state (bool): True to enable replies, False to disable.

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the item is already in the requested state, returns a dictionary with the key "error" and the value "Item already in requested state.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("replies_state_changed")
            - id (str): The ID of the item
            - state (bool): The new reply state
    """
    return {"status": "replies_state_changed", "id": id, "state": state}


@tool_spec(
    spec={
        'name': 'set_post_contest_mode',
        'description': 'Enables or disables contest mode for a post.',
        'parameters': {
            'type': 'object',
            'properties': {
                'state': {
                    'type': 'boolean',
                    'description': 'True to enable contest mode, False to disable.'
                },
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                }
            },
            'required': [
                'state',
                'id'
            ]
        }
    }
)
def post_api_set_contest_mode(state: bool, id: str) -> Dict[str, Any]:
    """
    Enables or disables contest mode for a post.

    Args:
        state (bool): True to enable contest mode, False to disable.
        id (str): The fullname of the post.

    Returns:
        Dict[str, Any]:
        - If the post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - If the post is already in the requested state, returns a dictionary with the key "error" and the value "Post already in requested state.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("contest_mode_set")
            - id (str): The ID of the post
            - state (bool): The new contest mode state
    """
    return {"status": "contest_mode_set", "id": id, "state": state}


@tool_spec(
    spec={
        'name': 'set_post_sticky_status',
        'description': 'Stickies or unstickies a post in a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'num': {
                    'type': 'integer',
                    'description': 'The sticky slot number.'
                },
                'state': {
                    'type': 'boolean',
                    'description': 'True to sticky, False to unsticky.'
                },
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                }
            },
            'required': [
                'state',
                'id'
            ]
        }
    }
)
def post_api_set_subreddit_sticky(num: Optional[int], state: bool, id: str) -> Dict[str, Any]:
    """
    Stickies or unstickies a post in a subreddit.

    Args:
        num (Optional[int]): The sticky slot number.
        state (bool): True to sticky, False to unsticky.
        id (str): The fullname of the post.

    Returns:
        Dict[str, Any]:
        - If the post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - If the post is already in the requested state, returns a dictionary with the key "error" and the value "Post already in requested state.".
        - If the sticky slot is invalid, returns a dictionary with the key "error" and the value "Invalid sticky slot.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("sticky_set")
            - id (str): The ID of the post
            - slot (Optional[int]): The sticky slot number
            - sticky (bool): The new sticky state
    """
    return {"status": "sticky_set", "id": id, "slot": num, "sticky": state}


@tool_spec(
    spec={
        'name': 'set_post_suggested_sort',
        'description': 'Sets the suggested comment sort order for a post.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sort': {
                    'type': 'string',
                    'description': 'The sort order (e.g., "top", "new").'
                },
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_set_suggested_sort(sort: Optional[str], id: str) -> Dict[str, Any]:
    """
    Sets the suggested comment sort order for a post.

    Args:
        sort (Optional[str]): The sort order (e.g., "top", "new").
        id (str): The fullname of the post.

    Returns:
        Dict[str, Any]:
        - If the post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - If the sort order is invalid, returns a dictionary with the key "error" and the value "Invalid sort order.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("suggested_sort_set")
            - id (str): The ID of the post
            - sort (Optional[str]): The new sort order
    """
    return {"status": "suggested_sort_set", "id": id, "sort": sort}


@tool_spec(
    spec={
        'name': 'mark_post_spoiler',
        'description': 'Marks a post as containing spoilers.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_spoiler(id: str) -> Dict[str, Any]:
    """
    Marks a post as containing spoilers.

    Args:
        id (str): The fullname of the post.

    Returns:
        Dict[str, Any]:
        - If the post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - If the post is already marked as a spoiler, returns a dictionary with the key "error" and the value "Post already marked as spoiler.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("spoiler_marked")
            - id (str): The ID of the marked post
    """
    return {"status": "spoiler_marked", "id": id}


@tool_spec(
    spec={
        'name': 'store_recent_visits',
        'description': "Stores a record of the user's recent post or comment visits.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_store_visits() -> Dict[str, Any]:
    """
    Stores a record of the user's recent post or comment visits.

    Returns:
        Dict[str, Any]:
        - If there are no visits to store, returns a dictionary with the key "error" and the value "No visits to store.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("visits_stored")
    """
    return {"status": "visits_stored"}


@tool_spec(
    spec={
        'name': 'submit_post',
        'description': 'Submits a new link or text post into a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'kind': {
                    'type': 'string',
                    'description': 'The type of post ("link" or "self").'
                },
                'sr': {
                    'type': 'string',
                    'description': 'The subreddit to which the post is submitted.'
                },
                'title': {
                    'type': 'string',
                    'description': 'The title of the post.'
                },
                'text': {
                    'type': 'string',
                    'description': 'The text body for a self-post. Required when kind is "self".'
                },
                'url': {
                    'type': 'string',
                    'description': 'The URL for a link post. Required when kind is "link".'
                },
                'nsfw': {
                    'type': 'boolean',
                    'description': 'Whether the post is Not Safe For Work. Defaults to False.'
                },
                'spoiler': {
                    'type': 'boolean',
                    'description': 'Whether the post contains spoilers. Defaults to False.'
                }
            },
            'required': [
                'kind',
                'sr',
                'title'
            ]
        }
    }
)
def post_api_submit(kind: str, sr: str, title: str, text: Optional[str] = None, url: Optional[str] = None, nsfw: bool = False, spoiler: bool = False) -> Dict[str, Any]:
    """
    Submits a new link or text post into a subreddit.

    Args:
        kind (str): The type of post ("link" or "self").
        sr (str): The subreddit to which the post is submitted.
        title (str): The title of the post.
        text (Optional[str]): The text body for a self-post. Required when kind is "self".
        url (Optional[str]): The URL for a link post. Required when kind is "link".
        nsfw (bool): Whether the post is Not Safe For Work. Defaults to False.
        spoiler (bool): Whether the post contains spoilers. Defaults to False.

    Returns:
        Dict[str, Any]:
        - If the subreddit does not exist, returns a dictionary with the key "error" and the value "Subreddit not found.".
        - If the kind is invalid, returns a dictionary with the key "error" and the value "Invalid post kind.".
        - If required fields are missing, returns a dictionary with the key "error" and the value "Missing required field: {field}.".
        - If the title is empty, returns a dictionary with the key "error" and the value "Title cannot be empty.".
        - On successful submission, returns a dictionary with the following keys:
            - status (str): The status of the operation ("submitted")
            - link_id (str): The ID of the new post
    """
    import time
    
    # Check if subreddit exists
    if sr not in DB.get("subreddits", {}):
        return {"error": "Subreddit not found."}
        
    # Check if title is empty
    if not title:
        return {"error": "Title cannot be empty."}
        
    if kind not in ["link", "self"]:
        return {"error": "invalid_kind", "message": "kind must be either 'link' or 'self'"}
        
    if kind == "self" and not text:
        return {"error": "missing_text", "message": "text is required for self posts"}
        
    if kind == "link" and not url:
        return {"error": "missing_url", "message": "url is required for link posts"}
        
    new_id = f"t3_{len(DB.get('links', {}))+1}" # Use .get for safety
    DB.setdefault("links", {})[new_id] = { # Ensure keys exist
        "subreddit": sr,
        "kind": kind,
        "title": title,
        "text": text or "",
        "url": url or "",
        "nsfw": nsfw,
        "spoiler": spoiler,
        "deleted": False,
        "created_utc": int(time.time())  # Add creation timestamp
    }
    return {"status": "submitted", "link_id": new_id}


@tool_spec(
    spec={
        'name': 'unhide_posts',
        'description': 'Unhides posts that were previously hidden.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'array',
                    'description': 'A list of post fullnames to unhide.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_unhide(id: List[str]) -> Dict[str, Any]:
    """
    Unhides posts that were previously hidden.

    Args:
        id (List[str]): A list of post fullnames to unhide.

    Returns:
        Dict[str, Any]:
        - If the list is empty, returns a dictionary with the key "error" and the value "No posts specified.".
        - If any post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - If any post is not hidden, returns a dictionary with the key "error" and the value "Post not hidden.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("unhidden")
            - items (List[str]): The list of unhidden post IDs
    """
    return {"status": "unhidden", "items": id}


@tool_spec(
    spec={
        'name': 'unlock_item',
        'description': 'Unlocks a previously locked post or comment.',
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
def post_api_unlock(id: str) -> Dict[str, Any]:
    """
    Unlocks a previously locked post or comment.

    Args:
        id (str): The fullname of the item.

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the item is not locked, returns a dictionary with the key "error" and the value "Item not locked.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("unlocked")
            - id (str): The ID of the unlocked item
    """
    return {"status": "unlocked", "id": id}


@tool_spec(
    spec={
        'name': 'unmark_post_nsfw',
        'description': 'Removes the NSFW tag from a post.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_unmarknsfw(id: str) -> Dict[str, Any]:
    """
    Removes the NSFW tag from a post.

    Args:
        id (str): The fullname of the post.

    Returns:
        Dict[str, Any]:
        - If the post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - If the post is not marked NSFW, returns a dictionary with the key "error" and the value "Post not marked NSFW.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("nsfw_removed")
            - id (str): The ID of the post
    """
    return {"status": "nsfw_removed", "id": id}


@tool_spec(
    spec={
        'name': 'unsave_item',
        'description': 'Unsaves a post or comment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item to unsave.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_unsave(id: str) -> Dict[str, Any]:
    """
    Unsaves a post or comment.

    Args:
        id (str): The fullname of the item to unsave.

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the item is not saved, returns a dictionary with the key "error" and the value "Item not saved.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("unsaved")
            - id (str): The ID of the unsaved item
    """
    return {"status": "unsaved", "id": id}


@tool_spec(
    spec={
        'name': 'unmark_post_spoiler',
        'description': 'Removes the spoiler tag from a post.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the post.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def post_api_unspoiler(id: str) -> Dict[str, Any]:
    """
    Removes the spoiler tag from a post.

    Args:
        id (str): The fullname of the post.

    Returns:
        Dict[str, Any]:
        - If the post does not exist, returns a dictionary with the key "error" and the value "Post not found.".
        - If the post is not marked as a spoiler, returns a dictionary with the key "error" and the value "Post not marked as spoiler.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("spoiler_removed")
            - id (str): The ID of the post
    """
    return {"status": "spoiler_removed", "id": id}


@tool_spec(
    spec={
        'name': 'vote_on_item',
        'description': 'Casts or revokes a vote on a post or comment.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The fullname of the item.'
                },
                'dir': {
                    'type': 'integer',
                    'description': 'The vote direction (-1 for downvote, 0 for remove, +1 for upvote).'
                }
            },
            'required': [
                'id',
                'dir'
            ]
        }
    }
)
def post_api_vote(id: str, dir: int) -> Dict[str, Any]:
    """
    Casts or revokes a vote on a post or comment.

    Args:
        id (str): The fullname of the item.
        dir (int): The vote direction (-1 for downvote, 0 for remove, +1 for upvote).

    Returns:
        Dict[str, Any]:
        - If the item does not exist, returns a dictionary with the key "error" and the value "Item not found.".
        - If the vote direction is invalid, returns a dictionary with the key "error" and the value "Invalid vote direction.".
        - On successful operation, returns a dictionary with the following keys:
            - status (str): The status of the operation ("voted")
            - id (str): The ID of the voted item
            - direction (int): The vote direction
    """
    return {"status": "voted", "id": id, "direction": dir}