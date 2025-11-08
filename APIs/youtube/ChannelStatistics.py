from typing import Dict, Optional
from common_utils.tool_spec_decorator import tool_spec

from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id


"""
    Handles YouTube Channel Statistics API operations.
    
    This class provides methods to retrieve and update various statistics
    associated with a YouTube channel, such as subscriber count, view count, etc.
"""


@tool_spec(
    spec={
    "name": "manage_channel_comment_count",
    "description": "Retrieves or sets the number of comments for the channel.",
    "parameters": {
        "type": "object",
        "properties": {
            "comment_count": {
                "type": "integer",
                "description": "If provided, sets the comment count to this value. If None, retrieves the current comment count. Defaults to None."
            }
        },
        "required": []
    }
}
)
def comment_count(comment_count: Optional[int] = None) -> Dict[str, int]:
    """
    Retrieves or sets the number of comments for the channel.

    Args:
        comment_count (Optional[int]): If provided, sets the comment count to this value.
                                      If None, retrieves the current comment count. Defaults to None.

    Returns:
        Dict[str, int]: A dictionary containing:
        - If `comment_count` is provided:
            - commentCount (int): The newly set comment count for the channel.
        - If `comment_count` is not provided:
            - commentCount (int): The current number of comments on the channel from the database.
    Raises:
        TypeError: If comment_count(if provided) is not an integer.
        ValueError: If comment_count(if provided) is not a positive integer.
    """
    if comment_count is not None:
        if not isinstance(comment_count, int):
            raise TypeError("Comment count must be an integer.")
        if comment_count < 0:
            raise ValueError("Comment count must be a positive integer.")
        if "channelStatistics" not in DB:
            DB["channelStatistics"] = {}
        DB["channelStatistics"]["commentCount"] = comment_count
        return {"commentCount": comment_count}
    return {
        "commentCount": DB.get("channelStatistics", {}).get("commentCount", 0)
    }


@tool_spec(
    spec={
    "name": "manage_channel_subscriber_visibility",
    "description": "Checks whether the subscriber count is hidden.",
    "parameters": {
        "type": "object",
        "properties": {
            "hidden_subscriber_count": {
                "type": "boolean",
                "description": "If provided, sets whether the subscriber count is hidden. If None, retrieves the current setting. Defaults to None."
            }
        },
        "required": []
    }
}
)
def hidden_subscriber_count(
    hidden_subscriber_count: Optional[bool] = None,
) -> Dict[str, bool]:
    """
    Checks whether the subscriber count is hidden.

    Args:
        hidden_subscriber_count (Optional[bool]): If provided, sets whether the subscriber count is hidden.
                                                 If None, retrieves the current setting. Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary containing:
        - If `hidden_subscriber_count` is provided:
            - hiddenSubscriberCount (bool): The newly set visibility state.
        - If `hidden_subscriber_count` is not provided:
            - hiddenSubscriberCount (bool): The current visibility status from the database.

    Raises:
        TypeError: If hidden_subscriber_count(if provided) is not a boolean.
    """
    if hidden_subscriber_count is not None:
        if not isinstance(hidden_subscriber_count, bool):
            raise TypeError("Hidden subscriber count must be a boolean.")
        if "channelStatistics" not in DB:
            DB["channelStatistics"] = {}
        DB["channelStatistics"]["hiddenSubscriberCount"] = hidden_subscriber_count
        return {"hiddenSubscriberCount": hidden_subscriber_count}
    return {
        "hiddenSubscriberCount": DB.get("channelStatistics", {}).get(
            "hiddenSubscriberCount", False
        )
    }


@tool_spec(
    spec={
    "name": "manage_channel_subscriber_count",
    "description": "Retrieves or sets the number of subscribers of the channel.",
    "parameters": {
        "type": "object",
        "properties": {
            "subscriber_count": {
                "type": "integer",
                "description": "If provided, sets the subscriber count to this value. If None, retrieves the current subscriber count. Defaults to None."
            }
        },
        "required": []
    }
}
)
def subscriber_count(subscriber_count: Optional[int] = None) -> Dict[str, int]:
    """
    Retrieves or sets the number of subscribers of the channel.

    Args:
        subscriber_count (Optional[int]): If provided, sets the subscriber count to this value.
                                         If None, retrieves the current subscriber count. Defaults to None.

    Returns:
        Dict[str, int]: A dictionary containing:
        - If `subscriber_count` is provided:
            - subscriberCount (int): The newly set subscriber count.
        - If `subscriber_count` is not provided:
            - subscriberCount (int): The current subscriber count from the database.

    Raises:
        TypeError: If subscriber_count(if provided) is not an integer.
        ValueError: If subscriber_count(if provided) is not a positive integer.
    """
    if subscriber_count is not None:
        if not isinstance(subscriber_count, int):
            raise TypeError("Subscriber count must be an integer.")
        if subscriber_count < 0:
            raise ValueError("Subscriber count must be a positive integer.")
        if "channelStatistics" not in DB:
            DB["channelStatistics"] = {}
        DB["channelStatistics"]["subscriberCount"] = subscriber_count
        return {"subscriberCount": subscriber_count}
    return {
        "subscriberCount": DB.get("channelStatistics", {}).get("subscriberCount", 0)
    }


@tool_spec(
    spec={
    "name": "manage_channel_video_count",
    "description": "Retrieves or sets the number of videos uploaded to the channel.",
    "parameters": {
        "type": "object",
        "properties": {
            "video_count": {
                "type": "integer",
                "description": "If provided, sets the video count to this value. If None, retrieves the current video count. Defaults to None."
            }
        },
        "required": []
    }
}
)
def video_count(video_count: Optional[int] = None) -> Dict[str, int]:
    """
    Retrieves or sets the number of videos uploaded to the channel.

    Args:
        video_count (Optional[int]): If provided, sets the video count to this value.
                                    If None, retrieves the current video count. Defaults to None.

    Returns:
        Dict[str, int]: A dictionary containing:
        - If `video_count` is provided:
            - videoCount (int): The newly set number of uploaded videos.
        - If `video_count` is not provided:
            - videoCount (int): The current number of videos from the database.

    Raises:
        TypeError: If video_count(if provided) is not an integer.
        ValueError: If video_count(if provided) is not a non-negative integer.
    """
    if video_count is not None:
        if not isinstance(video_count, int):
            raise TypeError("Video count must be an integer.")
        if video_count < 0:
            raise ValueError("Video count must be a non-negative integer.")
        if "channelStatistics" not in DB:
            DB["channelStatistics"] = {}
        DB["channelStatistics"]["videoCount"] = video_count
        return {"videoCount": video_count}
    return {"videoCount": DB.get("channelStatistics", {}).get("videoCount", 0)}


@tool_spec(
    spec={
    "name": "manage_channel_view_count",
    "description": "Retrieves or sets the total view count of the channel.",
    "parameters": {
        "type": "object",
        "properties": {
            "view_count": {
                "type": "integer",
                "description": "If provided, sets the view count to this value. If None, retrieves the current view count. Defaults to None."
            }
        },
        "required": []
    }
}
)
def view_count(view_count: Optional[int] = None) -> Dict[str, int]:
    """
    Retrieves or sets the total view count of the channel.

    Args:
        view_count (Optional[int]): If provided, sets the view count to this value.
                                   If None, retrieves the current view count. Defaults to None.

    Returns:
        Dict[str, int]: A dictionary containing:
        - If `view_count` is provided:
            - viewCount (int): The newly set total number of views.
        - If `view_count` is not provided:
            - viewCount (int): The current total view count from the database.

    Raises:
        TypeError: If view_count(if provided) is not an integer.
        ValueError: If view_count(if provided) is not a positive integer.
    """
    if view_count is not None:
        if not isinstance(view_count, int):
            raise TypeError("View count must be an integer.")
        if view_count < 0:
            raise ValueError("View count must be a positive integer.")
        if "channelStatistics" not in DB:
            DB["channelStatistics"] = {}
        DB["channelStatistics"]["viewCount"] = view_count
        return {"viewCount": view_count}

    return {"viewCount": DB.get("channelStatistics", {}).get("viewCount", 0)}
