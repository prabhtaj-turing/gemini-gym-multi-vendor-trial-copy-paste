from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB
from typing import Dict, Any, List
import string

"""
Simulation of /subreddits endpoints.
Manages subreddit-related operations and settings.
"""


@tool_spec(
    spec={
        'name': 'get_banned_users',
        'description': 'Retrieves a list of banned users in a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_banned() -> List[str]:
    """
    Retrieves a list of banned users in a subreddit.

    Returns:
        List[str]:
        - If there are no banned users, returns an empty list.
        - On successful retrieval, returns a list of banned user identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_approved_submitters',
        'description': 'Retrieves a list of approved submitters in a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_contributors() -> List[str]:
    """
    Retrieves a list of approved submitters in a subreddit.

    Returns:
        List[str]:
        - If there are no approved submitters, returns an empty list.
        - On successful retrieval, returns a list of contributor usernames.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_subreddit_moderators',
        'description': 'Retrieves a list of moderators in a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_moderators() -> List[str]:
    """
    Retrieves a list of moderators in a subreddit.

    Returns:
        List[str]:
        - If there are no moderators, returns an empty list.
        - On successful retrieval, returns a list of moderator usernames.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_muted_users',
        'description': 'Retrieves a list of muted users in a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_muted() -> List[str]:
    """
    Retrieves a list of muted users in a subreddit.

    Returns:
        List[str]:
        - If there are no muted users, returns an empty list.
        - On successful retrieval, returns a list of muted user identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_wiki_banned_users',
        'description': 'Retrieves a list of users banned from wiki edits.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_wikibanned() -> List[str]:
    """
    Retrieves a list of users banned from wiki edits.

    Returns:
        List[str]:
        - If there are no wiki-banned users, returns an empty list.
        - On successful retrieval, returns a list of wiki-banned user identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_approved_wiki_contributors',
        'description': 'Retrieves a list of approved wiki contributors.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_about_wikicontributors() -> List[str]:
    """
    Retrieves a list of approved wiki contributors.

    Returns:
        List[str]:
        - If there are no wiki contributors, returns an empty list.
        - On successful retrieval, returns a list of wiki contributor usernames.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_users_by_category',
        'description': 'Retrieves user lists based on a specified category.',
        'parameters': {
            'type': 'object',
            'properties': {
                'where': {
                    'type': 'string',
                    'description': 'The category (e.g., "banned", "moderators").'
                }
            },
            'required': [
                'where'
            ]
        }
    }
)
def get_about_where(where: str) -> Dict[str, Any]:
    """
    Retrieves user lists based on a specified category.

    Args:
        where (str): The category (e.g., "banned", "moderators").

    Returns:
        Dict[str, Any]:
        - If the category is invalid, returns a dictionary with the key "error" and the value "Invalid category.".
        - On successful retrieval, returns a dictionary with the following keys:
            - where (str): The requested category
            - users (List[str]): A list of user identifiers for the category
    """
    return {"where": where, "users": []}


@tool_spec(
    spec={
        'name': 'delete_subreddit_banner',
        'description': "Deletes the subreddit's banner image.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_delete_sr_banner() -> Dict[str, Any]:
    """
    Deletes the subreddit's banner image.

    Returns:
        Dict[str, Any]:
        - If the banner does not exist, returns a dictionary with the key "error" and the value "Banner not found.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("sr_banner_deleted")
    """
    return {"status": "sr_banner_deleted"}


@tool_spec(
    spec={
        'name': 'delete_subreddit_header',
        'description': "Deletes the subreddit's header image.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_delete_sr_header() -> Dict[str, Any]:
    """
    Deletes the subreddit's header image.

    Returns:
        Dict[str, Any]:
        - If the header does not exist, returns a dictionary with the key "error" and the value "Header not found.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("sr_header_deleted")
    """
    return {"status": "sr_header_deleted"}


@tool_spec(
    spec={
        'name': 'delete_subreddit_icon',
        'description': "Deletes the subreddit's icon image.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def post_api_delete_sr_icon() -> Dict[str, Any]:
    """
    Deletes the subreddit's icon image.

    Returns:
        Dict[str, Any]:
        - If the icon does not exist, returns a dictionary with the key "error" and the value "Icon not found.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("sr_icon_deleted")
    """
    return {"status": "sr_icon_deleted"}


@tool_spec(
    spec={
        'name': 'delete_subreddit_stylesheet_image',
        'description': 'Deletes a subreddit stylesheet image.',
        'parameters': {
            'type': 'object',
            'properties': {
                'img_name': {
                    'type': 'string',
                    'description': 'The name or key of the image to remove.'
                }
            },
            'required': [
                'img_name'
            ]
        }
    }
)
def post_api_delete_sr_img(img_name: str) -> Dict[str, Any]:
    """
    Deletes a subreddit stylesheet image.

    Args:
        img_name (str): The name or key of the image to remove.

    Returns:
        Dict[str, Any]:
        - If the image does not exist, returns a dictionary with the key "error" and the value "Image not found.".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("sr_image_deleted")
            - img_name (str): The name of the deleted image
    """
    return {"status": "sr_image_deleted", "img_name": img_name}


@tool_spec(
    spec={
        'name': 'recommend_related_subreddits',
        'description': 'Suggests related subreddits based on provided names.',
        'parameters': {
            'type': 'object',
            'properties': {
                'srnames': {
                    'type': 'string',
                    'description': 'A comma-separated list of subreddit names.'
                }
            },
            'required': [
                'srnames'
            ]
        }
    }
)
def get_api_recommend_sr_srnames(srnames: str) -> Dict[str, Any]:
    """
    Suggests related subreddits based on provided names.

    Args:
        srnames (str): A comma-separated list of subreddit names.

    Returns:
        Dict[str, Any]:
        - If the input is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit names.".
        - On successful retrieval, returns a dictionary with the following keys:
            - recommendations_for (List[str]): The list of input subreddit names
            - recommendations (List[str]): A list of recommended subreddit names
    """
    return {"recommendations_for": srnames.split(','), "recommendations": []}


@tool_spec(
    spec={
        'name': 'search_subreddit_names',
        'description': 'Checks for subreddit name availability or suggests names.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The search term for subreddit names.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def get_api_search_reddit_names(query: str) -> Dict[str, Any]:
    """
    Checks for subreddit name availability or suggests names.

    Args:
        query (str): The search term for subreddit names.

    Returns:
        Dict[str, Any]:
        - If the query is invalid, returns a dictionary with the key "error" and the value "Invalid search query.".
        - On successful check, returns a dictionary with the following keys:
            - query (str): The search query
            - available (bool): Whether the name is available
    """
    return {"query": query, "available": True}


@tool_spec(
    spec={
        'name': 'search_subreddits_by_title_description',
        'description': 'Searches for subreddits by name, title and description.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The search keyword(s).'
                },
                'exact': {
                    'type': 'boolean',
                    'description': 'If True, an exact match for the query will be performed. Defaults to False.'
                },
                'include_over18': {
                    'type': 'boolean',
                    'description': 'If True, results will include subreddits marked as "over 18". Defaults to False.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def post_api_search_subreddits(query: str, exact: bool = False, include_over18: bool = False) -> Dict[str, Any]:
    """
    Searches for subreddits by name, title and description.

    Args:
        query (str): The search keyword(s).
        exact (bool): If True, an exact match for the query will be performed. Defaults to False.
        include_over18 (bool): If True, results will include subreddits marked as "over 18". Defaults to False.

    Returns:
        Dict[str, Any]: On successful search, returns a dictionary with the following keys:
            - query (str): The search query
            - results (List[Dict[str, Any]]): A list of matching subreddit, each containing:
                - name (str): The subreddit name
                - title (str): The subreddit title
                - description (str): The subreddit description
                - subscribers (int): The number of subscribers
                - created_utc (int): The creation timestamp in UTC
                - over18 (bool): Whether the subreddit is marked as "over 18"
                - spoilers_enabled (bool): Whether spoilers are enabled for the subreddit
                - public_description (str): The public description of the subreddit
                - subreddit_type (str): The type of subreddit (e.g., "public", "restricted")
                - restrict_posting (bool): Whether posting is restricted
                - restrict_commenting (bool): Whether commenting is restricted
                - restrict_media (bool): Whether media is restricted

    Raises:
        TypeError:
            - If the query is not a string.
            - If exact or include_over18 are not booleans.
        ValueError:
            - If the query is empty or None
            - If the query is too long (over 50 characters)
            - If the query contains non-printable characters.
    """
    # Check for type
    if not isinstance(query, str):
        raise TypeError("Query must be a string.")
    if not isinstance(exact, bool):
        raise TypeError("'exact' must be a boolean.")
    if not isinstance(include_over18, bool):
        raise TypeError("'include_over18' must be a boolean.")

    # Check for None or empty input
    if query is None or not query.strip():
        raise ValueError("No search query provided.")

    # Clean the input
    query_clean = query.strip()

    # Check for maximum length (50 characters as per specification)
    if len(query_clean) > 50:
        raise ValueError("Search query too long. Maximum 50 characters allowed.")

    # Check for printable characters only
    if not all(char in string.printable for char in query_clean):
        raise ValueError("Search query contains invalid characters.")

    # Search for subreddit names in the database
    subreddits = DB.get("subreddits", {})
    results = []

    # Convert query to lowercase for case-insensitive search
    query_lower = query_clean.lower()

    for subreddit_name, subreddit_data in subreddits.items():
        # Filter for "over 18" subreddits
        if not include_over18 and subreddit_data.get("over18", False):
            continue

        name_lower = subreddit_name.lower()
        title_lower = subreddit_data.get("title", "").lower()
        description_lower = subreddit_data.get("description", "").lower()

        match = False
        if exact:
            if (query_lower == name_lower or
                query_lower == title_lower or
                query_lower == description_lower):
                match = True
        else:

            if (query_lower in name_lower or
                query_lower in title_lower or
                query_lower in description_lower):
                match = True

        if match:
            result = {
                "name": subreddit_name,
                "title": subreddit_data.get("title", ""),
                "description": subreddit_data.get("description", ""),
                "subscribers": subreddit_data.get("subscribers", -1),
                "created_utc": subreddit_data.get("created_utc", 0),
                "over18": subreddit_data.get("over18", False),
                "spoilers_enabled": subreddit_data.get("spoilers_enabled", False),
                "public_description": subreddit_data.get("public_description", ""),
                "subreddit_type": subreddit_data.get("subreddit_type", ""),
                "restrict_posting": subreddit_data.get("restrict_posting", False),
                "restrict_commenting": subreddit_data.get("restrict_commenting", False),
                "restrict_media": subreddit_data.get("restrict_media", False)
            }
            results.append(result)

    return {"query": query_clean, "results": results}


@tool_spec(
    spec={
        'name': 'create_or_edit_subreddit',
        'description': 'Creates or edits a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the subreddit.'
                },
                'title': {
                    'type': 'string',
                    'description': 'The title of the subreddit.'
                }
            },
            'required': [
                'name',
                'title'
            ]
        }
    }
)
def post_api_site_admin(name: str, title: str) -> Dict[str, Any]:
    """
    Creates or edits a subreddit.

    Args:
        name (str): The name of the subreddit.
        title (str): The title of the subreddit.

    Returns:
        Dict[str, Any]:
        - If the name is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit name.".
        - If the title is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit title.".
        - On successful creation/editing, returns a dictionary with the following keys:
            - status (str): The status of the operation ("subreddit_created_or_edited")
            - name (str): The subreddit name
            - title (str): The subreddit title
    """
    DB.setdefault("subreddits", {})[name] = {"title": title} # Ensure keys exist
    return {"status": "subreddit_created_or_edited", "name": name, "title": title}


@tool_spec(
    spec={
        'name': 'get_subreddit_submit_text',
        'description': 'Retrieves the submission text (sidebar text) for a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sr': {
                    'type': 'string',
                    'description': 'The name of the subreddit.'
                }
            },
            'required': [
                'sr'
            ]
        }
    }
)
def get_api_submit_text(sr: str) -> Dict[str, Any]:
    """
    Retrieves the submission text (sidebar text) for a subreddit.

    Args:
        sr (str): The name of the subreddit.

    Returns:
        Dict[str, Any]:
        - If the subreddit is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit.".
        - On successful retrieval, returns a dictionary with the following keys:
            - subreddit (str): The subreddit name
            - submit_text (str): The submission text
    """
    return {"subreddit": sr, "submit_text": "Welcome to the subreddit!"}


@tool_spec(
    spec={
        'name': 'get_subreddit_autocomplete_suggestions_legacy',
        'description': 'Provides autocomplete suggestions for subreddits (legacy).',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'A partial subreddit name.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def get_api_subreddit_autocomplete(query: str) -> List[str]:
    """
    Provides autocomplete suggestions for subreddits (legacy).

    Args:
        query (str): A partial subreddit name.

    Returns:
        List[str]:
        - If the query is invalid, returns an empty list.
        - On successful retrieval, returns a list of suggested subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_subreddit_autocomplete_suggestions',
        'description': 'Provides autocomplete suggestions for subreddits (v2).',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_api_subreddit_autocomplete_v2() -> List[str]:
    """
    Provides autocomplete suggestions for subreddits (v2).

    Returns:
        List[str]:
        - If there are no suggestions, returns an empty list.
        - On successful retrieval, returns a list of suggested subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'update_subreddit_stylesheet',
        'description': "Updates the subreddit's stylesheet.",
        'parameters': {
            'type': 'object',
            'properties': {
                'op': {
                    'type': 'string',
                    'description': 'The operation (typically "save").'
                },
                'stylesheet_contents': {
                    'type': 'string',
                    'description': 'The new stylesheet code.'
                }
            },
            'required': [
                'op',
                'stylesheet_contents'
            ]
        }
    }
)
def post_api_subreddit_stylesheet(op: str, stylesheet_contents: str) -> Dict[str, Any]:
    """
    Updates the subreddit's stylesheet.

    Args:
        op (str): The operation (typically "save").
        stylesheet_contents (str): The new stylesheet code.

    Returns:
        Dict[str, Any]:
        - If the operation is invalid, returns a dictionary with the key "error" and the value "Invalid operation.".
        - If the stylesheet is invalid, returns a dictionary with the key "error" and the value "Invalid stylesheet.".
        - On successful update, returns a dictionary with the following keys:
            - status (str): The status of the operation ("stylesheet_saved")
            - op (str): The operation performed
            - contents (str): The saved stylesheet contents
    """
    return {"status": "stylesheet_saved", "op": op, "contents": stylesheet_contents}


@tool_spec(
    spec={
        'name': 'subscribe_or_unsubscribe_subreddit',
        'description': 'Subscribes or unsubscribes the user from a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'Either "sub" or "unsub".'
                },
                'sr_name': {
                    'type': 'string',
                    'description': 'The name of the subreddit.'
                }
            },
            'required': [
                'action',
                'sr_name'
            ]
        }
    }
)
def post_api_subscribe(action: str, sr_name: str) -> Dict[str, Any]:
    """
    Subscribes or unsubscribes the user from a subreddit.

    Args:
        action (str): Either "sub" or "unsub".
        sr_name (str): The name of the subreddit.

    Returns:
        Dict[str, Any]:
        - If the action is invalid, returns a dictionary with the key "error" and the value "Invalid action.".
        - If the subreddit is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit.".
        - On successful subscription/unsubscription, returns a dictionary with the following keys:
            - status (str): The status of the operation ("subscribed" or "unsubscribed")
            - action (str): The action performed
            - subreddit (str): The subreddit name
    """
    return {"status": "subscribed", "action": action, "subreddit": sr_name}


@tool_spec(
    spec={
        'name': 'upload_subreddit_stylesheet_image',
        'description': "Uploads an image for a subreddit's stylesheet.",
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name/key for the image.'
                },
                'file': {
                    'type': 'object',
                    'description': 'The image file data, which may include:',
                    'properties': {
                        'filepath': {
                            'type': 'string',
                            'description': 'Local path to the image file.'
                        },
                        'mimetype': {
                            'type': 'string',
                            'description': 'MIME type of the image (e.g., "image/png").'
                        },
                        'data': {
                            'type': 'string',
                            'description': 'Raw binary content of the image.'
                        },
                        'upload_type': {
                            'type': 'string',
                            'description': 'The type of image being uploaded. Valid values are "img", "header", "icon", and "banner".'
                        }
                    },
                    'required': [
                        'filepath'
                    ]
                }
            },
            'required': [
                'name',
                'file'
            ]
        }
    }
)
def post_api_upload_sr_img(name: str, file: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uploads an image for a subreddit's stylesheet.

    Args:
        name (str): The name/key for the image.
        file (Dict[str, Any]): The image file data, which may include:
            - filepath (str): Local path to the image file.
            - mimetype (Optional[str]): MIME type of the image (e.g., "image/png").
            - data (Optional[bytes]): Raw binary content of the image.
            - upload_type (Optional[str]): The type of image being uploaded. Valid values are "img", "header", "icon", and "banner".

    Returns:
        Dict[str, Any]:
        - If the name is invalid, returns a dictionary with the key "error" and the value "Invalid image name.".
        - If the file is invalid, returns a dictionary with the key "error" and the value "Invalid image file.".
        - On successful upload, returns a dictionary with the following keys:
            - status (str): The status of the operation ("image_uploaded")
            - img_name (str): The name of the uploaded image
    """
    return {"status": "image_uploaded", "img_name": name}


@tool_spec(
    spec={
        'name': 'get_subreddit_post_requirements',
        'description': 'Retrieves submission requirements for a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subreddit': {
                    'type': 'string',
                    'description': 'The name of the subreddit.'
                }
            },
            'required': [
                'subreddit'
            ]
        }
    }
)
def get_api_v1_subreddit_post_requirements(subreddit: str) -> Dict[str, Any]:
    """
    Retrieves submission requirements for a subreddit.

    Args:
        subreddit (str): The name of the subreddit.

    Returns:
        Dict[str, Any]:
        - If the subreddit is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit.".
        - On successful retrieval, returns a dictionary with the following keys:
            - subreddit (str): The subreddit name
            - requirements (Dict[str, Any]): A dictionary of post requirements, containing:
                - title_required (bool): Whether a title is required
    """
    return {"subreddit": subreddit, "requirements": {"title_required": True}}


@tool_spec(
    spec={
        'name': 'get_subreddit_info',
        'description': 'Retrieves information about a specific subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subreddit': {
                    'type': 'string',
                    'description': 'The name of the subreddit.'
                }
            },
            'required': [
                'subreddit'
            ]
        }
    }
)
def get_r_subreddit_about(subreddit: str) -> Dict[str, Any]:
    """
    Retrieves information about a specific subreddit.

    Args:
        subreddit (str): The name of the subreddit.

    Returns:
        Dict[str, Any]:
        - If the subreddit is invalid, returns a dictionary with the key "error" and the value "Invalid subreddit.".
        - On successful retrieval, returns a dictionary with the following keys:
            - subreddit (str): The subreddit name
            - info (Dict[str, Any]): A dictionary containing subreddit information
    """
    info = DB.get("subreddits", {}).get(subreddit, {"title": "Untitled Subreddit"}) # Use .get for safety
    return {"subreddit": subreddit, "info": info}


@tool_spec(
    spec={
        'name': 'get_subreddit_editing_settings',
        'description': 'Retrieves the subreddit editing settings.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_r_subreddit_about_edit() -> Dict[str, Any]:
    """
    Retrieves the subreddit editing settings.

    Returns:
        Dict[str, Any]:
        - If the settings are not available, returns a dictionary with the key "error" and the value "Settings not found.".
        - On successful retrieval, returns a dictionary with the following keys:
            - edit_info (str): The editing settings information
    """
    return {"edit_info": "placeholder"}


@tool_spec(
    spec={
        'name': 'get_subreddit_rules',
        'description': 'Retrieves the moderation rules of a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_r_subreddit_about_rules() -> List[Dict[str, Any]]:
    """
    Retrieves the moderation rules of a subreddit.

    Returns:
        List[Dict[str, Any]]:
        - If there are no rules, returns an empty list.
        - On successful retrieval, returns a list of rule objects, each containing:
            - short_name (str): The rule's short name
            - description (str): The rule's description
            - created_utc (int): The creation timestamp
    """
    return []


@tool_spec(
    spec={
        'name': 'get_subreddit_traffic_stats',
        'description': 'Retrieves traffic statistics for a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_r_subreddit_about_traffic() -> Dict[str, Any]:
    """
    Retrieves traffic statistics for a subreddit.

    Returns:
        Dict[str, Any]:
        - If the statistics are not available, returns a dictionary with the key "error" and the value "Statistics not found.".
        - On successful retrieval, returns a dictionary with the following keys:
            - traffic_stats (List[Dict[str, Any]]): A list of traffic statistics
    """
    return {"traffic_stats": []}


@tool_spec(
    spec={
        'name': 'get_subreddit_sidebar',
        'description': 'Retrieves the sidebar content for the subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_sidebar() -> str:
    """
    Retrieves the sidebar content for the subreddit.

    Returns:
        str:
        - If the sidebar is empty, returns an empty string.
        - On successful retrieval, returns the sidebar content as a string.
    """
    return "Sidebar content"


@tool_spec(
    spec={
        'name': 'get_stickied_post_ids',
        'description': 'Retrieves the identifiers of stickied posts.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_sticky() -> List[str]:
    """
    Retrieves the identifiers of stickied posts.

    Returns:
        List[str]:
        - If there are no stickied posts, returns an empty list.
        - On successful retrieval, returns a list of stickied post IDs.
    """
    return ["t3_sticky1"]


@tool_spec(
    spec={
        'name': 'get_default_subreddits',
        'description': 'Retrieves the list of default subreddits.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subreddits_default() -> List[str]:
    """
    Retrieves the list of default subreddits.

    Returns:
        List[str]:
        - If there are no default subreddits, returns an empty list.
        - On successful retrieval, returns a list of default subreddit names.
    """
    return ["r/Python", "r/learnprogramming"]


@tool_spec(
    spec={
        'name': 'get_gold_subreddits',
        'description': 'Retrieves gold-exclusive subreddits.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subreddits_gold() -> List[str]:
    """
    Retrieves gold-exclusive subreddits.

    Returns:
        List[str]:
        - If there are no gold subreddits, returns an empty list.
        - On successful retrieval, returns a list of gold subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_my_contributor_subreddits',
        'description': 'Retrieves subreddits where the user is an approved contributor.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subreddits_mine_contributor() -> List[str]:
    """
    Retrieves subreddits where the user is an approved contributor.

    Returns:
        List[str]:
        - If there are no contributor subreddits, returns an empty list.
        - On successful retrieval, returns a list of subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_my_moderator_subreddits',
        'description': 'Retrieves subreddits where the user is a moderator.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subreddits_mine_moderator() -> List[str]:
    """
    Retrieves subreddits where the user is a moderator.

    Returns:
        List[str]:
        - If there are no moderator subreddits, returns an empty list.
        - On successful retrieval, returns a list of subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_my_streaming_subreddits',
        'description': 'Retrieves subreddits related to streaming content.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subreddits_mine_streams() -> List[str]:
    """
    Retrieves subreddits related to streaming content.

    Returns:
        List[str]:
        - If there are no streaming subreddits, returns an empty list.
        - On successful retrieval, returns a list of subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_my_subscribed_subreddits',
        'description': 'Retrieves subreddits the user is subscribed to.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subreddits_mine_subscriber() -> List[str]:
    """
    Retrieves subreddits the user is subscribed to.

    Returns:
        List[str]:
        - If there are no subscribed subreddits, returns an empty list.
        - On successful retrieval, returns a list of subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_my_subreddits_by_category',
        'description': 'Retrieves subreddits based on a specified category.',
        'parameters': {
            'type': 'object',
            'properties': {
                'where': {
                    'type': 'string',
                    'description': 'The category (e.g., "contributor", "moderator").'
                }
            },
            'required': [
                'where'
            ]
        }
    }
)
def get_subreddits_mine_where(where: str) -> List[str]:
    """
    Retrieves subreddits based on a specified category.

    Args:
        where (str): The category (e.g., "contributor", "moderator").

    Returns:
        List[str]:
        - If the category is invalid, returns an empty list.
        - If there are no subreddits in the category, returns an empty list.
        - On successful retrieval, returns a list of subreddit names for the specified category.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_new_subreddits',
        'description': 'Retrieves newly created subreddits.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subreddits_new() -> List[str]:
    """
    Retrieves newly created subreddits.

    Returns:
        List[str]:
        - If there are no new subreddits, returns an empty list.
        - On successful retrieval, returns a list of new subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_popular_subreddits',
        'description': 'Retrieves popular subreddits.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subreddits_popular() -> List[str]:
    """
    Retrieves popular subreddits.

    Returns:
        List[str]:
        - If there are no popular subreddits, returns an empty list.
        - On successful retrieval, returns a list of popular subreddit names.
    """
    return ["r/AskReddit", "r/funny", "r/pics"]


@tool_spec(
    spec={
        'name': 'search_subreddits_by_name_or_topic',
        'description': 'Searches for subreddits by name or topic.',
        'parameters': {
            'type': 'object',
            'properties': {
                'q': {
                    'type': 'string',
                    'description': 'The search query.'
                }
            },
            'required': [
                'q'
            ]
        }
    }
)
def get_subreddits_search(q: str) -> List[str]:
    """
    Searches for subreddits by name or topic.

    Args:
        q (str): The search query.

    Returns:
        List[str]:
        - If the query is invalid, returns an empty list.
        - If no subreddits match the query, returns an empty list.
        - On successful search, returns a list of matching subreddit names.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_subreddits_by_category',
        'description': 'Retrieves subreddits based on a specified category.',
        'parameters': {
            'type': 'object',
            'properties': {
                'where': {
                    'type': 'string',
                    'description': 'The category (e.g., "popular", "new").'
                }
            },
            'required': [
                'where'
            ]
        }
    }
)
def get_subreddits_where(where: str) -> List[str]:
    """
    Retrieves subreddits based on a specified category.

    Args:
        where (str): The category (e.g., "popular", "new").

    Returns:
        List[str]:
        - If the category is invalid, returns an empty list.
        - If there are no subreddits in the category, returns an empty list.
        - On successful retrieval, returns a list of subreddit names for the specified category.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_newest_users',
        'description': 'Retrieves the newest registered users.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_users_new() -> List[str]:
    """
    Retrieves the newest registered users.

    Returns:
        List[str]:
        - If there are no new users, returns an empty list.
        - On successful retrieval, returns a list of new user identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_popular_users',
        'description': 'Retrieves popular users.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_users_popular() -> List[str]:
    """
    Retrieves popular users.

    Returns:
        List[str]:
        - If there are no popular users, returns an empty list.
        - On successful retrieval, returns a list of popular user identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'search_users_by_name',
        'description': 'Searches for users by name.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_users_search() -> List[str]:
    """
    Searches for users by name.

    Returns:
        List[str]:
        - If there are no matching users, returns an empty list.
        - On successful search, returns a list of matching user identifiers.
    """
    return []


@tool_spec(
    spec={
        'name': 'get_users_by_list_category',
        'description': 'Retrieves users based on a specified category.',
        'parameters': {
            'type': 'object',
            'properties': {
                'where': {
                    'type': 'string',
                    'description': 'The user category (e.g., "new", "popular").'
                }
            },
            'required': [
                'where'
            ]
        }
    }
)
def get_users_where(where: str) -> List[str]:
    """
    Retrieves users based on a specified category.

    Args:
        where (str): The user category (e.g., "new", "popular").

    Returns:
        List[str]:
        - If the category is invalid, returns an empty list.
        - If there are no users in the category, returns an empty list.
        - On successful retrieval, returns a list of user identifiers for the specified category.
    """
    return []