from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB
from typing import Dict, Any, Optional

"""
Simulation of /emoji endpoints.
Manages emoji operations for subreddits.
"""

@tool_spec(
    spec={
        'name': 'add_subreddit_emoji',
        'description': 'Adds a new emoji to a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subreddit': {
                    'type': 'string',
                    'description': 'The name of the subreddit.'
                },
                'name': {
                    'type': 'string',
                    'description': "Name of the emoji to be created. It can be alphanumeric without any special characters except '-' & '_' and cannot exceed 24 characters."
                },
                's3_key': {
                    'type': 'string',
                    'description': 'S3 key of the uploaded image which can be obtained from the S3 url. This is of the form subreddit/hash_value.'
                },
                'mod_flair_only': {
                    'type': 'boolean',
                    'description': 'Whether the emoji is only available for moderator flair. Defaults to False.'
                },
                'post_flair_allowed': {
                    'type': 'boolean',
                    'description': 'Whether the emoji can be used in post flair. Defaults to True.'
                },
                'user_flair_allowed': {
                    'type': 'boolean',
                    'description': 'Whether the emoji can be used in user flair. Defaults to True.'
                },
                'css': {
                    'type': 'string',
                    'description': 'CSS styling for the emoji.'
                }
            },
            'required': [
                'subreddit',
                'name',
                's3_key'
            ]
        }
    }
)
def post_api_v1_subreddit_emoji_json(
    subreddit: str, 
    name: str, 
    s3_key: str,
    mod_flair_only: bool = False,
    post_flair_allowed: bool = True,
    user_flair_allowed: bool = True,
    css: Optional[str] = None
) -> Dict[str, Any]:
    """
    Adds a new emoji to a subreddit.

    Args:
        subreddit (str): The name of the subreddit.
        name (str): Name of the emoji to be created. It can be alphanumeric without any special characters except '-' & '_' and cannot exceed 24 characters.
        s3_key (str): S3 key of the uploaded image which can be obtained from the S3 url. This is of the form subreddit/hash_value.
        mod_flair_only (bool): Whether the emoji is only available for moderator flair. Defaults to False.
        post_flair_allowed (bool): Whether the emoji can be used in post flair. Defaults to True.
        user_flair_allowed (bool): Whether the emoji can be used in user flair. Defaults to True.
        css (Optional[str]): CSS styling for the emoji.

    Returns:
        Dict[str, Any]:
        - If the emoji name is already in use, returns a dictionary with the key "error" and the value "Emoji name already in use".
        - If the name is invalid (contains special characters or exceeds 24 characters), returns a dictionary with the key "error" and the value "Invalid emoji name".
        - On successful addition, returns a dictionary with the following keys:
            - status (str): The status of the operation ("success")
            - subreddit (str): The name of the subreddit
            - emoji_name (str): The name of the added emoji
            - mod_flair_only (bool): Whether the emoji is mod-only
            - post_flair_allowed (bool): Whether the emoji can be used in post flair
            - user_flair_allowed (bool): Whether the emoji can be used in user flair
    """
    # Validate emoji name
    if len(name) > 24:
        return {"error": "Invalid emoji name"}
    if not all(c.isalnum() or c in ['-', '_'] for c in name):
        return {"error": "Invalid emoji name"}
        
    sub_emojis = DB.setdefault("emoji", {}).setdefault(subreddit, {}) # Ensure keys exist
    if name in sub_emojis:
        return {"error": "Emoji name already in use"}
        
    sub_emojis[name] = {
        "css": css or "", 
        "s3_key": s3_key,
        "mod_flair_only": mod_flair_only,
        "post_flair_allowed": post_flair_allowed,
        "user_flair_allowed": user_flair_allowed
    }
    
    return {
        "status": "success", 
        "subreddit": subreddit, 
        "emoji_name": name,
        "mod_flair_only": mod_flair_only,
        "post_flair_allowed": post_flair_allowed,
        "user_flair_allowed": user_flair_allowed
    }

@tool_spec(
    spec={
        'name': 'delete_subreddit_emoji',
        'description': 'Removes an existing emoji from a subreddit.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subreddit': {
                    'type': 'string',
                    'description': 'The name of the subreddit.'
                },
                'emoji_name': {
                    'type': 'string',
                    'description': 'The name of the emoji to delete.'
                }
            },
            'required': [
                'subreddit',
                'emoji_name'
            ]
        }
    }
)
def delete_api_v1_subreddit_emoji_emoji_name(subreddit: str, emoji_name: str) -> Dict[str, Any]:
    """
    Removes an existing emoji from a subreddit.

    Args:
        subreddit (str): The name of the subreddit.
        emoji_name (str): The name of the emoji to delete.

    Returns:
        Dict[str, Any]:
        - If the emoji is not found, returns a dictionary with the key "error" and the value "Emoji not found".
        - On successful deletion, returns a dictionary with the following keys:
            - status (str): The status of the operation ("deleted")
            - emoji_name (str): The name of the deleted emoji
            - s3_key (str): The S3 key of the deleted emoji
    """
    sub_emojis = DB.get("emoji", {}).get(subreddit, {})
    if emoji_name not in sub_emojis:
        return {"error": "Emoji not found"}
    s3_key = sub_emojis[emoji_name].get("s3_key")
    del sub_emojis[emoji_name]
    # Optional: remove subreddit key if empty
    if not sub_emojis and subreddit in DB.get("emoji", {}):
        del DB["emoji"][subreddit]
    return {"status": "deleted", "emoji_name": emoji_name, "s3_key": s3_key}

@tool_spec(
    spec={
        'name': 'get_emoji_s3_upload_lease',
        'description': 'Acquires and returns an upload lease to an S3 temporary bucket.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filepath': {
                    'type': 'string',
                    'description': 'The name and extension of the image file (e.g. "image1.png").'
                },
                'mimetype': {
                    'type': 'string',
                    'description': 'The MIME type of the image (e.g. "image/png").'
                }
            },
            'required': [
                'filepath',
                'mimetype'
            ]
        }
    }
)
def post_api_v1_subreddit_emoji_asset_upload_s3_json(filepath: str, mimetype: str) -> Dict[str, Any]:
    """
    Acquires and returns an upload lease to an S3 temporary bucket.

    Args:
        filepath (str): The name and extension of the image file (e.g. "image1.png").
        mimetype (str): The MIME type of the image (e.g. "image/png").

    Returns:
        Dict[str, Any]: A dictionary containing:
            - credentials (Dict[str, str]): Temporary credentials for uploading assets to S3:
                - access_key_id (str): The access key ID
                - secret_access_key (str): The secret access key
                - session_token (str): The session token
            - s3_url (str): The S3 URL to which the asset should be uploaded
            - key (str): The key (path) to be used for uploading, incorporating the provided filepath
    """
    # Simulated S3 upload lease details.
    lease = {
        "credentials": {
            "access_key_id": "EXAMPLEACCESSKEY",
            "secret_access_key": "EXAMPLESECRETACCESSKEY",
            "session_token": "EXAMPLESESSIONTOKEN"
        },
        "s3_url": "https://s3-temp-bucket.example.com/upload",
        "key": f"temp/{filepath}"
    }
    return lease

@tool_spec(
    spec={
        'name': 'set_subreddit_emoji_custom_size',
        'description': 'Sets a custom display size for a subreddit emoji.',
        'parameters': {
            'type': 'object',
            'properties': {
                'emoji_name': {
                    'type': 'string',
                    'description': 'The name of the emoji.'
                },
                'width': {
                    'type': 'integer',
                    'description': 'The desired width in pixels.'
                },
                'height': {
                    'type': 'integer',
                    'description': 'The desired height in pixels.'
                }
            },
            'required': [
                'emoji_name',
                'width',
                'height'
            ]
        }
    }
)
def post_api_v1_subreddit_emoji_custom_size(emoji_name: str, width: int, height: int) -> Dict[str, Any]:
    """
    Sets a custom display size for a subreddit emoji.

    Args:
        emoji_name (str): The name of the emoji.
        width (int): The desired width in pixels.
        height (int): The desired height in pixels.

    Returns:
        Dict[str, Any]: A dictionary with the following keys:
            - status (str): The status of the operation ("custom_size_updated")
            - emoji_name (str): The name of the emoji
            - width (int): The new width in pixels
            - height (int): The new height in pixels
    """
    # For simplicity, let's say we store it in a dictionary.
    # We'll just confirm the request is recognized.
    # Note: This mock doesn't know which subreddit the emoji belongs to.
    return {
        "status": "custom_size_updated",
        "emoji_name": emoji_name,
        "width": width,
        "height": height
    }

@tool_spec(
    spec={
        'name': 'get_all_subreddit_emojis',
        'description': 'Retrieves all emojis for a specified subreddit.',
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
def get_api_v1_subreddit_emojis_all(subreddit: str) -> Dict[str, Any]:
    """
    Retrieves all emojis for a specified subreddit.

    Args:
        subreddit (str): The name of the subreddit.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - subreddit (str): The name of the subreddit
            - emojis (Dict[str, Dict[str, Any]]): A dictionary of emoji details, where each emoji has:
                - css (str): CSS styling for the emoji
                - s3_key (str): S3 key of the emoji image
                - mod_flair_only (bool): Whether the emoji is mod-only
                - post_flair_allowed (bool): Whether the emoji can be used in post flair
                - user_flair_allowed (bool): Whether the emoji can be used in user flair
    """
    sub_emojis = DB.get("emoji", {}).get(subreddit, {})
    return {"subreddit": subreddit, "emojis": sub_emojis}