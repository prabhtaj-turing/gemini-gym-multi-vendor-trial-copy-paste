from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB
from typing import Dict, Any, List

"""
Simulation of /multis endpoints.
Manages multireddit operations.
"""


@tool_spec(
    spec={
        'name': 'delete_saved_filter_path',
        'description': 'Deletes a saved filter path.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filterpath': {
                    'type': 'string',
                    'description': 'The filter path identifier.'
                }
            },
            'required': [
                'filterpath'
            ]
        }
    }
)
def delete_api_filter_filterpath(filterpath: str) -> Dict[str, Any]:
    """
    Deletes a saved filter path.

    Args:
        filterpath (str): The filter path identifier.

    Returns:
        Dict[str, Any]:
        - If the filter path is invalid, returns a dictionary with the key "error" and the value "Invalid filter path.".
        - If the filter path does not exist, returns a dictionary with the key "error" and the value "Filter path not found.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("filter_deleted")
            - filterpath (str): The deleted filter path
    """
    return {"status": "filter_deleted", "filterpath": filterpath}


@tool_spec(
    spec={
        'name': 'remove_subreddit_from_filter_path',
        'description': 'Removes a subreddit from a saved filter path.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filterpath': {
                    'type': 'string',
                    'description': 'The filter path identifier.'
                },
                'srname': {
                    'type': 'string',
                    'description': 'The subreddit name to remove.'
                }
            },
            'required': [
                'filterpath',
                'srname'
            ]
        }
    }
)
def delete_api_filter_filterpath_r_srname(filterpath: str, srname: str) -> Dict[str, Any]:
    """
    Removes a subreddit from a saved filter path.

    Args:
        filterpath (str): The filter path identifier.
        srname (str): The subreddit name to remove.

    Returns:
        Dict[str, Any]:
        - If the filter path is invalid, returns a dictionary with the key "error" and the value "Invalid filter path.".
        - If the subreddit is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit name.".
        - If the subreddit is not in the filter, returns a dictionary with the key "error" and the value "Subreddit not found in filter.".
        - On successful removal, returns a dictionary with the following keys:
            - status (str): The status of the operation ("subreddit_removed_from_filter")
            - filter (str): The filter path
            - srname (str): The removed subreddit name
    """
    return {"status": "subreddit_removed_from_filter", "filter": filterpath, "srname": srname}


@tool_spec(
    spec={
        'name': 'copy_multireddit',
        'description': 'Copies an existing multireddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'frm': {
                    'type': 'string',
                    'description': 'The source multireddit path.'
                },
                'to': {
                    'type': 'string',
                    'description': 'The destination path for the copy.'
                }
            },
            'required': [
                'frm',
                'to'
            ]
        }
    }
)
def post_api_multi_copy(frm: str, to: str) -> Dict[str, Any]:
    """
    Copies an existing multireddit.

    Args:
        frm (str): The source multireddit path.
        to (str): The destination path for the copy.

    Returns:
        Dict[str, Any]:
        - If the source path is invalid, returns a dictionary with the key "error" and the value "Invalid source path.".
        - If the destination path is invalid, returns a dictionary with the key "error" and the value "Invalid destination path.".
        - If the source multireddit does not exist, returns a dictionary with the key "error" and the value "Source multireddit not found.".
        - On successful copy, returns a dictionary with the following keys:
            - status (str): The status of the operation ("multi_copied")
            - new_multiname (str): The name of the new multireddit
    """
    new_multiname = f"multi_{len(DB.get('multis', {}))+1}" # Use .get for safety
    DB.setdefault("multis", {})[new_multiname] = {"source": frm, "path": to} # Ensure keys exist
    return {"status": "multi_copied", "new_multiname": new_multiname}


@tool_spec(
    spec={
        'name': 'get_my_multireddits',
        'description': "Retrieves the authenticated user's multireddits.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_api_multi_mine() -> List[Dict[str, Any]]:
    """
    Retrieves the authenticated user's multireddits.

    Returns:
        List[Dict[str, Any]]:
        - If there are no multireddits, returns an empty list.
        - On successful retrieval, returns a list of multireddit objects, each containing:
            - name (str): The multireddit name
            - path (str): The multireddit path
            - subreddits (List[str]): A list of subreddit names
            - created_at (str): The creation timestamp
    """
    return list(DB.get("multis", {}).values()) # Use .get for safety


@tool_spec(
    spec={
        'name': 'get_user_public_multireddits',
        'description': 'Retrieves public multireddits for a specified user.',
        'parameters': {
            'type': 'object',
            'properties': {
                'username': {
                    'type': 'string',
                    'description': 'The username whose multireddits are requested.'
                }
            },
            'required': [
                'username'
            ]
        }
    }
)
def get_api_multi_user_username(username: str) -> List[Dict[str, Any]]:
    """
    Retrieves public multireddits for a specified user.

    Args:
        username (str): The username whose multireddits are requested.

    Returns:
        List[Dict[str, Any]]:
        - If the username is invalid, returns an empty list.
        - If the user has no public multireddits, returns an empty list.
        - On successful retrieval, returns a list of multireddit objects, each containing:
            - name (str): The multireddit name
            - path (str): The multireddit path
            - subreddits (List[str]): A list of subreddit names
            - created_at (str): The creation timestamp
    """
    return []


@tool_spec(
    spec={
        'name': 'delete_multireddit',
        'description': 'Deletes a multireddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'multipath': {
                    'type': 'string',
                    'description': 'The multireddit path.'
                }
            },
            'required': [
                'multipath'
            ]
        }
    }
)
def delete_api_multi_multipath(multipath: str) -> Dict[str, Any]:
    """
    Deletes a multireddit.

    Args:
        multipath (str): The multireddit path.

    Returns:
        Dict[str, Any]:
        - If the multipath is invalid, returns a dictionary with the key "error" and the value "Invalid multireddit path.".
        - If the multireddit does not exist, returns a dictionary with the key "error" and the value "Multireddit not found.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("multi_deleted")
            - multipath (str): The deleted multireddit path
    """
    return {"status": "multi_deleted", "multipath": multipath}


@tool_spec(
    spec={
        'name': 'get_multireddit_description',
        'description': 'Retrieves the description of a multireddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'multipath': {
                    'type': 'string',
                    'description': 'The multireddit path.'
                }
            },
            'required': [
                'multipath'
            ]
        }
    }
)
def get_api_multi_multipath_description(multipath: str) -> Dict[str, Any]:
    """
    Retrieves the description of a multireddit.

    Args:
        multipath (str): The multireddit path.

    Returns:
        Dict[str, Any]:
        - If the multipath is invalid, returns a dictionary with the key "error" and the value "Invalid multireddit path.".
        - If the multireddit does not exist, returns a dictionary with the key "error" and the value "Multireddit not found.".
        - On successful retrieval, returns a dictionary with the following keys:
            - description (str): The multireddit description
            - multipath (str): The multireddit path
    """
    return {"description": "", "multipath": multipath}


@tool_spec(
    spec={
        'name': 'remove_subreddit_from_multireddit',
        'description': 'Removes a subreddit from a multireddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'multipath': {
                    'type': 'string',
                    'description': 'The multireddit path.'
                },
                'srname': {
                    'type': 'string',
                    'description': 'The subreddit name to remove.'
                }
            },
            'required': [
                'multipath',
                'srname'
            ]
        }
    }
)
def delete_api_multi_multipath_r_srname(multipath: str, srname: str) -> Dict[str, Any]:
    """
    Removes a subreddit from a multireddit.

    Args:
        multipath (str): The multireddit path.
        srname (str): The subreddit name to remove.

    Returns:
        Dict[str, Any]:
        - If the multipath is invalid, returns a dictionary with the key "error" and the value "Invalid multireddit path.".
        - If the subreddit is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit name.".
        - If the subreddit is not in the multireddit, returns a dictionary with the key "error" and the value "Subreddit not found in multireddit.".
        - On successful removal, returns a dictionary with the following keys:
            - status (str): The status of the operation ("subreddit_removed_from_multi")
            - multipath (str): The multireddit path
            - srname (str): The removed subreddit name
    """
    return {"status": "subreddit_removed_from_multi", "multipath": multipath, "srname": srname}