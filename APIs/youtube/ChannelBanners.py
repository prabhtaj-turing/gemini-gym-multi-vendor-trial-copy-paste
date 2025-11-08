from typing import Dict, List, Optional, Union
from common_utils.tool_spec_decorator import tool_spec

from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id

"""
    Handles YouTube Channel Banners API operations.
    
    This class provides methods to manage channel banner images,
    which are the large banner images that appear at the top of a YouTube channel page.
"""


@tool_spec(
    spec={
    "name": "insert_channel_banner",
    "description": "Inserts a new channel banner into the YouTube channel. This function creates a new channel banner resource and stores it in the database. Channel banners are the large banner images that appear at the top of a YouTube channel page.",
    "parameters": {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "The ID of the channel for which to insert a banner. Must be a non-empty string if provided. Example: \"UC_x5XG1OV2P6uZZ5FSM9Ttw\". Defaults to None."
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Must be a non-empty string if provided. Defaults to None."
            },
            "on_behalf_of_content_owner_channel": {
                "type": "string",
                "description": "The onBehalfOfContentOwnerChannel parameter specifies the YouTube channel ID of the channel to which the user is being added. Must be a non-empty string if provided. Defaults to None."
            }
        },
        "required": []
    }
}
)
def insert(
    channel_id: Optional[str] = None,
    on_behalf_of_content_owner: Optional[str] = None,
    on_behalf_of_content_owner_channel: Optional[str] = None,
) -> Dict[str, Union[str, None]]:
    """
    Inserts a new channel banner into the YouTube channel.

    This function creates a new channel banner resource and stores it in the database.
    Channel banners are the large banner images that appear at the top of a YouTube channel page.

    Args:
        channel_id (Optional[str]): The ID of the channel for which to insert a banner.
            Must be a non-empty string if provided. Example: "UC_x5XG1OV2P6uZZ5FSM9Ttw". Defaults to None.
        on_behalf_of_content_owner (Optional[str]): The onBehalfOfContentOwner parameter 
            indicates that the request's authorization credentials identify a YouTube CMS user 
            who is acting on behalf of the content owner specified in the parameter value.
            Must be a non-empty string if provided. Defaults to None.
        on_behalf_of_content_owner_channel (Optional[str]): The onBehalfOfContentOwnerChannel 
            parameter specifies the YouTube channel ID of the channel to which the user is 
            being added. Must be a non-empty string if provided. Defaults to None.

    Returns:
        Dict[str, Union[str, None]]: A dictionary containing the newly created banner resource with keys:
            - channelId (Optional[str]): The ID of the channel for which the banner was inserted
            - onBehalfOfContentOwner (Optional[str]): The content owner on whose behalf the 
              operation was performed
            - onBehalfOfContentOwnerChannel (Optional[str]): The YouTube channel ID of the 
              channel to which the user was added

    Raises:
        TypeError: If any of the provided string parameters are not strings
        ValueError: If any of the provided string parameters are empty strings or contain 
                   only whitespace characters or if the channel_id does not exist in the database
    """
    if channel_id is not None and (not isinstance(channel_id, str)):
        raise TypeError("Channel ID must be a string.")
    if on_behalf_of_content_owner is not None and (not isinstance(on_behalf_of_content_owner, str)):
        raise TypeError("On behalf of content owner must be a string.")
    if on_behalf_of_content_owner_channel is not None and (not isinstance(on_behalf_of_content_owner_channel, str)):
        raise TypeError("On behalf of content owner channel must be a string.")
    
    # Additional input validation for empty strings and whitespace
    if channel_id is not None and (not channel_id.strip()):
        raise ValueError("Channel ID cannot be empty or contain only whitespace.")
    
    if on_behalf_of_content_owner is not None and (not on_behalf_of_content_owner.strip()):
        raise ValueError("On behalf of content owner cannot be empty or contain only whitespace.")
    
    if on_behalf_of_content_owner_channel is not None and (not on_behalf_of_content_owner_channel.strip()):
        raise ValueError("On behalf of content owner channel cannot be empty or contain only whitespace.")

    if channel_id is not None:
        if channel_id not in DB.get("channels", {}):
            raise ValueError("Channel ID does not exist in the database.")
    
    # Create the new banner resource
    new_banner = {
        "channelId": channel_id,
        "onBehalfOfContentOwner": on_behalf_of_content_owner,
        "onBehalfOfContentOwnerChannel": on_behalf_of_content_owner_channel,
    }
    
    # Store in database
    DB.setdefault("channelBanners", []).append(new_banner)
    
    return new_banner