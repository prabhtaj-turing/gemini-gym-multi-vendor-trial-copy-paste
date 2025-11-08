"""
AdminUsers resource for Slack API simulation.
"""
from common_utils.tool_spec_decorator import tool_spec
import hashlib
import random
import string
import base64
from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors
from .SimulationEngine.models import validate_email
from typing import Optional, Dict, Any


@tool_spec(
    spec={
        'name': 'invite_admin_user',
        'description': 'Invites a user to a Slack workspace.',
        'parameters': {
            'type': 'object',
            'properties': {
                'email': {
                    'type': 'string',
                    'description': """ Email address of the user to invite. Must be a non-empty string
                    and a valid email format. """
                },
                'channel_ids': {
                    'type': 'string',
                    'description': """ Comma-separated list of channel IDs to add the user to.
                    If provided, must be a string. Defaults to None. """
                },
                'real_name': {
                    'type': 'string',
                    'description': """ Full name of the user. If provided, must be a string.
                    if not provided it is extracted from the email. """
                },
                'team_id': {
                    'type': 'string',
                    'description': """ ID of the team to invite the user to. If provided, must be a string.
                    Defaults to None. """
                }
            },
            'required': [
                'email'
            ]
        }
    }
)
def invite(
        email: str,
        channel_ids: Optional[str] = None,
        real_name: Optional[str] = None,
        team_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Invites a user to a Slack workspace.

    Args:
        email (str): Email address of the user to invite. Must be a non-empty string
                     and a valid email format.
        channel_ids (Optional[str]): Comma-separated list of channel IDs to add the user to.
                                     If provided, must be a string. Defaults to None.
        real_name (Optional[str]): Full name of the user. If provided, must be a string.
                                   if not provided it is extracted from the email.
        team_id (Optional[str]): ID of the team to invite the user to. If provided, must be a string.
                                 Defaults to None.

    Returns:
        Dict[str, Any]: Dictionary containing the result of the invitation with keys:
            - 'ok' (bool): True always, incase of error specific error will be raised
            - 'user' (Dict[str, Any]): Dictionary with user details:
                - 'id' (str): Unique user ID.
                - 'team_id' (Optional[str]): Team ID of the user.
                - 'name' (str): Username derived from the email.
                - 'real_name' (str): Full name of the user.
                - 'profile' (Dict[str, Any]): User profile information:
                    - 'email' (str): User's email address.
                    - 'display_name' (str): Display name for the user.
                    - 'image' (str): Base64-encoded profile image.
                    - 'image_crop_x' (int): X coordinate for image cropping.
                    - 'image_crop_y' (int): Y coordinate for image cropping.
                    - 'image_crop_w' (int): Width of the cropped image.
                    - 'title' (str): User's title.
                - 'is_admin' (bool): Whether the user is an admin.
                - 'is_bot' (bool): Whether the user is a bot.
                - 'deleted' (bool): Whether the user account is deleted.
                - 'presence' (str): User's presence status.

    Raises:
        TypeError: If 'email' is not a string.
                   If 'channel_ids' is provided and is not a string.
                   If 'real_name' is provided and is not a string.
                   If 'team_id' is provided and is not a string.
        ValueError: If 'email' is an empty string or not in a valid format.
        UserAlreadyInvitedError: If the user is already invited
    """
    # --- Input Validation ---
    if not isinstance(email, str):
        raise TypeError("email must be a string.")
    if not email:
        raise ValueError("email cannot be empty.")
    
    # Use pydantic email validation
    try:
        validate_email(email)
    except Exception as e:
        # Extract the actual validation error message from pydantic
        error_str = str(e)
        if "validation error" in error_str.lower():
            # Extract the specific error message after the validation details
            lines = error_str.split('\n')
            for line in lines:
                if "value is not a valid email address:" in line:
                    # Extract the message after the colon and before the bracket
                    specific_error = line.split("value is not a valid email address:")[-1].strip()
                    # Remove the type/input information in brackets
                    if "[type=" in specific_error:
                        specific_error = specific_error.split("[type=")[0].strip()
                    raise ValueError(f"email format is invalid ({specific_error.rstrip('.')})")
        raise ValueError("email format is invalid")

    if channel_ids is not None and not isinstance(channel_ids, str):
        raise TypeError("channel_ids must be a string if provided.")

    if real_name is not None and not isinstance(real_name, str):
        raise TypeError("real_name must be a string if provided.")

    if team_id is not None and not isinstance(team_id, str):
        raise TypeError("team_id must be a string if provided.")
    # --- End of Input Validation ---

    # --- Original Core Logic ---

    for user_data_existing in DB["users"].values():
        if user_data_existing.get("profile", {}).get("email") == email:
            email = user_data_existing.get("profile", {}).get("email")
            raise custom_errors.UserAlreadyInvitedError(f"User with {email} is already invited")

    base_id = hashlib.sha1(email.encode()).hexdigest()[:8].upper()
    user_id = f"U{base_id}"

    if user_id in DB["users"]:
        random.seed(base_id)
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=2))
        user_id = f"{user_id}{suffix}"

    user_data = {
        "id": user_id,
        "team_id": team_id,
        "name": email.split("@")[0],
        "real_name": real_name or email.split("@")[0].title(),
        "profile": {
            "email": email,
            "display_name": (real_name or email.split("@")[0]).title(),
            "image": base64.b64encode(random.randbytes(32)).decode('utf-8'),
            "image_crop_x": 0,
            "image_crop_y": 0,
            "image_crop_w": 100,
            "title": "Invited User"
        },
        "is_admin": False,
        "is_bot": False,
        "deleted": False,
        "presence": "away"
    }

    DB["users"][user_id] = user_data
    if channel_ids:
        channel_list = []
        
        for channel_id_item in channel_ids.split(","):
            channel_id_item = channel_id_item.strip()
            # remove empty strings
            if not channel_id_item:
                continue
            channel_list.append(channel_id_item)

        for channel_id_item in channel_list:
            # Ensure channel exists before trying to add members
            if channel_id_item not in DB["channels"]:
                DB["channels"][channel_id_item] = {  # Initialize channel if not existing
                    "id": channel_id_item,
                    "name": f"channel_{channel_id_item}",
                    "is_private": False,
                    "team_id": None,
                    "conversations": {
                        "id": f"C{channel_id_item[1:]}",  # Generate conversation ID
                        "read_cursor": 0,
                        "members": [],
                        "topic": "",
                        "purpose": ""
                    },
                    "messages": [],
                    "files": {}
                }

            # Original logic for adding to conversations members
            if "conversations" not in DB["channels"][channel_id_item]:
                DB["channels"][channel_id_item]["conversations"] = {}  # Should not happen if initialized above
            if "members" not in DB["channels"][channel_id_item]["conversations"]:
                DB["channels"][channel_id_item]['conversations']["members"] = []

            if user_id not in DB["channels"][channel_id_item]['conversations']["members"]:
                DB["channels"][channel_id_item]['conversations']["members"].append(user_id)
    return {"ok": True, "user": user_data}
