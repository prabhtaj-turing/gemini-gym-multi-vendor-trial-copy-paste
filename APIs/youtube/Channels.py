from typing import Dict, List, Optional, Union
from pydantic import BaseModel, validator, ValidationError

from common_utils.tool_spec_decorator import tool_spec

from youtube.SimulationEngine.custom_errors import MaxResultsOutOfRangeError
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id
from youtube.SimulationEngine.models import ChannelUpdateProperties

"""
    Handles YouTube Channels API operations.
    
    This class provides methods to manage YouTube channels, including retrieving
    channel information, creating new channels, and updating channel metadata.
"""



@tool_spec(
    spec={
    "name": "list_channels",
    "description": "Retrieves a list of channels with optional filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "category_id": {
                "type": "string",
                "description": "The categoryId parameter specifies a YouTube guide category ID. The API response will only include channels from that category. Defaults to None."
            },
            "for_username": {
                "type": "string",
                "description": "The forUsername parameter specifies a YouTube username. The API response will only include the channel associated with that username. Defaults to None."
            },
            "hl": {
                "type": "string",
                "description": "The hl parameter instructs the API to retrieve localized resource metadata for a specific application language that the YouTube website supports. Defaults to None."
            },
            "channel_id": {
                "type": "string",
                "description": "The id parameter specifies a comma-separated list of the YouTube channel ID(s) for the resource(s) that are being retrieved. Defaults to None."
            },
            "managed_by_me": {
                "type": "boolean",
                "description": "The managedByMe parameter can be used to instruct the API to only return channels that the user is allowed to manage. Defaults to None."
            },
            "max_results": {
                "type": "integer",
                "description": "The maxResults parameter specifies the maximum number of items that should be returned in the result set. The value must be between 1 and 50, inclusive. Defaults to None. If not provided, all matching results are returned."
            },
            "mine": {
                "type": "boolean",
                "description": "The mine parameter can be used to instruct the API to only return channels owned by the authenticated user. Defaults to None."
            },
            "my_subscribers": {
                "type": "boolean",
                "description": "The mySubscribers parameter can be used to instruct the API to only return channels to which the authenticated user has subscribed. Defaults to None."
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Defaults to None."
            }
        },
        "required": []
    }
}
)
def list(
    category_id: Optional[str] = None,
    for_username: Optional[str] = None,
    hl: Optional[str] = None,
    channel_id: Optional[str] = None,
    managed_by_me: Optional[bool] = None,
    max_results: Optional[int] = None,
    mine: Optional[bool] = None,
    my_subscribers: Optional[bool] = None,
    on_behalf_of_content_owner: Optional[str] = None,
) -> Dict[str, List[Dict[str, Union[str, bool]]]]:
    """
    Retrieves a list of channels with optional filters.

    Args:
        category_id (Optional[str]): The categoryId parameter specifies a YouTube guide category ID.
                     The API response will only include channels from that category. Defaults to None.
        for_username (Optional[str]): The forUsername parameter specifies a YouTube username.
                      The API response will only include the channel associated with that username. Defaults to None.
        hl (Optional[str]): The hl parameter instructs the API to retrieve localized resource metadata
            for a specific application language that the YouTube website supports. Defaults to None.
        channel_id (Optional[str]): The id parameter specifies a comma-separated list of the YouTube channel ID(s)
                    for the resource(s) that are being retrieved. Defaults to None.
        managed_by_me (Optional[bool]): The managedByMe parameter can be used to instruct the API
                       to only return channels that the user is allowed to manage. Defaults to None.
        max_results (Optional[int]): The maxResults parameter specifies the maximum number of items
                     that should be returned in the result set. The value must be between 1 and 50, inclusive. Defaults to None. If not provided, all matching results are returned.
        mine (Optional[bool]): The mine parameter can be used to instruct the API to only return
              channels owned by the authenticated user. Defaults to None.
        my_subscribers (Optional[bool]): The mySubscribers parameter can be used to instruct the API
                        to only return channels to which the authenticated user has subscribed. Defaults to None.
        on_behalf_of_content_owner (Optional[str]): The onBehalfOfContentOwner parameter indicates that the
                                   request's authorization credentials identify a YouTube CMS user
                                   who is acting on behalf of the content owner specified
                                   in the parameter value. Defaults to None.

    Returns:
        Dict[str, List[Dict[str, Union[str, bool]]]]: A dictionary containing:
            - items (List[Dict[str, Union[str, bool]]]): List of channel objects matching the filter criteria.
              Returns an empty list if no channels exist in the system or no channels match the filter criteria.
            Each channel object contains:
                - id (str): Unique channel identifier
                - categoryId (str): Channel category ID
                - forUsername (str): Channel username
                - hl (str): Language setting
                - managedByMe (bool): Whether channel is managed by authenticated user
                - mine (bool): Whether channel is owned by authenticated user
                - mySubscribers (bool): Whether authenticated user is subscribed to channel
                - onBehalfOfContentOwner (str): CMS user information

    Raises:
        TypeError: If any input argument has an incorrect type.
        ValueError: If any string argument is empty or contains only whitespace.
        MaxResultsOutOfRangeError: If max_results is provided and is not between 1 and 50 (inclusive).
        KeyError: If the database is not properly initialized or a critical key is missing
                  (propagated from DB access).
    """

    # Input Validation
    if category_id is not None:
        if not isinstance(category_id, str):
            raise TypeError("category_id must be a string or None.")
        if not category_id.strip():
            raise ValueError("category_id cannot be an empty string.")
    if for_username is not None:
        if not isinstance(for_username, str):
            raise TypeError("for_username must be a string or None.")
        if not for_username.strip():
            raise ValueError("for_username cannot be an empty string.")
    if hl is not None:
        if not isinstance(hl, str):
            raise TypeError("hl must be a string or None.")
        if not hl.strip():
            raise ValueError("hl cannot be an empty string.")
    if channel_id is not None:
        if not isinstance(channel_id, str):
            raise TypeError("channel_id must be a string or None.")
        if not channel_id.strip():
            raise ValueError("channel_id cannot be an empty string.")
    if managed_by_me is not None and not isinstance(managed_by_me, bool):
        raise TypeError("managed_by_me must be a boolean or None.")
    if mine is not None and not isinstance(mine, bool):
        raise TypeError("mine must be a boolean or None.")
    if my_subscribers is not None and not isinstance(my_subscribers, bool):
        raise TypeError("my_subscribers must be a boolean or None.")
    if on_behalf_of_content_owner is not None:
        if not isinstance(on_behalf_of_content_owner, str):
            raise TypeError("on_behalf_of_content_owner must be a string or None.")
        if not on_behalf_of_content_owner.strip():
            raise ValueError("on_behalf_of_content_owner cannot be an empty string.")

    if max_results is not None:
        if not isinstance(max_results, int):
            raise TypeError("max_results must be an integer or None.")
        if not (1 <= max_results <= 50):
            raise MaxResultsOutOfRangeError(
                "max_results must be between 1 and 50, inclusive."
            )

    # Core Logic (original logic preserved, error dictionary returns removed)
    # A KeyError from DB.get will propagate naturally.
    channels = DB.get("channels", {})
    results = []

    channel_id_list = (
        [cid.strip() for cid in channel_id.split(",") if cid.strip()]
        if channel_id
        else None
    )

    for channel_data in channels.values():
        if category_id is not None and channel_data.get("categoryId") != category_id:
            continue
        if for_username is not None and channel_data.get("forUsername") != for_username:
            continue
        if channel_id_list and channel_data.get("id") not in channel_id_list:
            continue
        if hl is not None and channel_data.get("hl") != hl:
            continue
        if (
            managed_by_me is not None
            and channel_data.get("managedByMe") != managed_by_me
        ):
            continue
        if mine is not None and channel_data.get("mine") != mine:
            continue
        if (
            my_subscribers is not None
            and channel_data.get("mySubscribers") != my_subscribers
        ):
            continue
        if (
            on_behalf_of_content_owner is not None
            and channel_data.get("onBehalfOfContentOwner") != on_behalf_of_content_owner
        ):
            continue

        results.append(channel_data)

    if max_results is not None:  # max_results is validated to be between 1 and 50
        results = results[:max_results]
    # The original code had `results = results[: min(max_results, 50)]`.
    # Since max_results is now guaranteed to be <= 50 (if not None),
    # min(max_results, 50) simplifies to max_results.

    return {"items": results}


@tool_spec(
    spec={
    "name": "create_channel",
    "description": "Creates a new channel resource in the database.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Must be a comma-separated list containing one or more of: 'snippet', 'statistics', 'contentDetails'."
            },
            "category_id": {
                "type": "string",
                "description": "The categoryId parameter specifies a YouTube guide category ID for the new channel. Defaults to None."
            },
            "for_username": {
                "type": "string",
                "description": "The forUsername parameter specifies a YouTube username for the new channel. Defaults to None."
            },
            "hl": {
                "type": "string",
                "description": "The hl parameter instructs the API to retrieve localized resource metadata for a specific application language that the YouTube website supports. Defaults to None."
            },
            "channel_id": {
                "type": "string",
                "description": "The id parameter specifies the YouTube channel ID for the new channel. Currently not used! Defaults to None."
            },
            "managed_by_me": {
                "type": "boolean",
                "description": "The managedByMe parameter indicates whether the channel is managed by the authenticated user. Defaults to None."
            },
            "max_results": {
                "type": "integer",
                "description": "The maxResults parameter specifies the maximum number of items that should be returned in the result set. Defaults to None."
            },
            "mine": {
                "type": "boolean",
                "description": "The mine parameter indicates whether the channel is owned by the authenticated user. Defaults to None."
            },
            "my_subscribers": {
                "type": "boolean",
                "description": "The mySubscribers parameter indicates whether the authenticated user has subscribed to the channel. Defaults to None."
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Defaults to None."
            }
        },
        "required": [
            "part"
        ]
    }
}
)
def insert(
    part: str,
    category_id: Optional[str] = None,
    for_username: Optional[str] = None,
    hl: Optional[str] = None,
    channel_id: Optional[str] = None,
    managed_by_me: Optional[bool] = None,
    max_results: Optional[int] = None,
    mine: Optional[bool] = None,
    my_subscribers: Optional[bool] = None,
    on_behalf_of_content_owner: Optional[str] = None,
) -> Dict[str, Union[bool, Dict[str, Union[str, int, bool]]]]:
    """
    Creates a new channel resource in the database.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Must be a comma-separated list containing one or more of: 'snippet', 'statistics', 'contentDetails'.
        category_id (Optional[str]): The categoryId parameter specifies a YouTube guide category ID for the new channel. Defaults to None.
        for_username (Optional[str]): The forUsername parameter specifies a YouTube username for the new channel. Defaults to None.
        hl (Optional[str]): The hl parameter instructs the API to retrieve localized resource metadata for a specific application language that the YouTube website supports. Defaults to None.
        channel_id (Optional[str]): The id parameter specifies the YouTube channel ID for the new channel. Currently not used! Defaults to None.
        managed_by_me (Optional[bool]): The managedByMe parameter indicates whether the channel is managed by the authenticated user. Defaults to None.
        max_results (Optional[int]): The maxResults parameter specifies the maximum number of items that should be returned in the result set. Defaults to None.
        mine (Optional[bool]): The mine parameter indicates whether the channel is owned by the authenticated user. Defaults to None.
        my_subscribers (Optional[bool]): The mySubscribers parameter indicates whether the authenticated user has subscribed to the channel. Defaults to None.
        on_behalf_of_content_owner (Optional[str]): The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Defaults to None.

    Returns:
        Dict[str, Union[bool, Dict[str, Union[str, int, bool]]]]: A dictionary containing:
                - success (bool): Whether the operation was successful
                - channel (Dict[str, Union[str, int, bool]]): The newly created channel object with all properties
                    - id (str): Unique channel identifier
                    - part (str): The part parameter specifies the channel resource properties that the API response will include. Must be a comma-separated list of the following values: snippet, statistics, contentDetails
                    - categoryId (str): Channel category ID. Must be one of the ids in the videoCategories database.
                    - forUsername (str): Channel username. Must be not empty when provided.
                    - hl (str): Language setting. Must be one of: af, az, id, ms, bs, ca, cs, da, de, et, en-IN, en-GB, en, es, es-419, es-US, eu, fil, fr, fr-CA, gl, hr, zu, is, it, sw, lv, lt, hu, nl, no, uz, pl, pt-PT, pt, ro, sq, sk, sl, sr-Latn, fi, sv, vi, tr, be, bg, ky, kk, mk, mn, ru, sr, uk, el, hy, iw, ur, ar, fa, ne, mr, hi, as, bn, pa, gu, or, ta, te, kn, ml, si, th, lo, my, ka, am, km
                    - managedByMe (bool): Whether channel is managed by authenticated user
                    - maxResults (int): The maximum number of items that should be returned in the result set. Must be a positive integer when provided.
                    - mine (bool): Whether channel is owned by authenticated user
                    - mySubscribers (bool): Whether authenticated user is subscribed to channel
                    - onBehalfOfContentOwner (str): CMS user information. Must be not empty when provided.

    Raises:
        ValueError: If part is empty or invalid or not provided,
                    or if category_id is empty or not found in the database when it is provided,
                    or if for_username is empty when it is provided,
                    or if hl is empty or invalid when it is provided,
                    or if channel_id is empty or already exists in the database when it is provided,
                    or if max_results is negative when it is provided
                    or if on_behalf_of_content_owner is empty when it is provided.
        TypeError: If part is not a string,
                    or if category_id is not a string when it is provided,
                    or if for_username is not a string when it is provided,
                    or if hl is not a string when it is provided,
                    or if channel_id is not a string when it is provided,
                    or if managed_by_me is not a boolean when it is provided,
                    or if max_results is not an integer when it is provided,
                    or if mine is not a boolean when it is provided,
                    or if my_subscribers is not a boolean when it is provided,
                    or if on_behalf_of_content_owner is not a string when it is provided.
    """
    if not part:
        raise ValueError("part parameter is required")

    if not isinstance(part, str):
        raise TypeError("part must be a string")
    if not part.strip():
        raise ValueError("part cannot be an empty string")
    for p in part.split(","):
        if p not in ["snippet", "statistics", "contentDetails"]:
            raise ValueError("Invalid part parameter value")

    new_channel = {}
    if category_id is not None:
        if not isinstance(category_id, str):
            raise TypeError("category_id must be a string or None.")
        if not category_id.strip():
            raise ValueError("category_id cannot be an empty string.")
        if category_id not in [x["id"] for x in DB.get("videoCategories", {}).values()]:
            raise ValueError("Invalid category_id, category not found in the database.")
        new_channel["categoryId"] = category_id

    if for_username is not None:
        if not isinstance(for_username, str):
            raise TypeError("for_username must be a string or None.")
        if not for_username.strip():
            raise ValueError("for_username cannot be an empty string.")
        new_channel["forUsername"] = for_username

    if hl is not None:
        if not isinstance(hl, str):
            raise TypeError("hl must be a string or None.")
        if not hl.strip():
            raise ValueError("hl cannot be an empty string.")
        if hl not in [
    "af", "az", "id", "ms", "bs", "ca", "cs", "da", "de", "et",
    "en-IN", "en-GB", "en", "es", "es-419", "es-US", "eu", "fil",
    "fr", "fr-CA", "gl", "hr", "zu", "is", "it", "sw", "lv", "lt",
    "hu", "nl", "no", "uz", "pl", "pt-PT", "pt", "ro", "sq", "sk",
    "sl", "sr-Latn", "fi", "sv", "vi", "tr", "be", "bg", "ky", "kk",
    "mk", "mn", "ru", "sr", "uk", "el", "hy", "iw", "ur", "ar", "fa",
    "ne", "mr", "hi", "as", "bn", "pa", "gu", "or", "ta", "te", "kn",
    "ml", "si", "th", "lo", "my", "ka", "am", "km"]:
            raise ValueError("Invalid hl value, must be one of: af, az, id, ms, bs, ca, cs, da, de, et, en-IN, en-GB, en, es, es-419, es-US, eu, fil, fr, fr-CA, gl, hr, zu, is, it, sw, lv, lt, hu, nl, no, uz, pl, pt-PT, pt, ro, sq, sk, sl, sr-Latn, fi, sv, vi, tr, be, bg, ky, kk, mk, mn, ru, sr, uk, el, hy, iw, ur, ar, fa, ne, mr, hi, as, bn, pa, gu, or, ta, te, kn, ml, si, th, lo, my, ka, am, km")
        new_channel["hl"] = hl

    if channel_id is not None:
        if not isinstance(channel_id, str):
            raise TypeError("channel_id must be a string or None.")
        if not channel_id.strip():
            raise ValueError("channel_id cannot be an empty string.")
        if channel_id in DB.get("channels", {}):
            raise ValueError("channel_id already exists in the database.")
        new_channel["id"] = channel_id
    else:
        new_channel["id"] = generate_entity_id("channel")

    if managed_by_me is not None:
        if not isinstance(managed_by_me, bool):
            raise TypeError("managed_by_me must be a boolean or None.")
        new_channel["managedByMe"] = managed_by_me

    if max_results is not None:
        if not isinstance(max_results, int):
            raise TypeError("max_results must be an integer or None.")
        if max_results < 0:
            raise ValueError("max_results cannot be negative.")
        new_channel["maxResults"] = max_results

    if mine is not None:
        if not isinstance(mine, bool):
            raise TypeError("mine must be a boolean or None.")
        new_channel["mine"] = mine

    if my_subscribers is not None:
        if not isinstance(my_subscribers, bool):
            raise TypeError("my_subscribers must be a boolean or None.")
        new_channel["mySubscribers"] = my_subscribers

    if on_behalf_of_content_owner is not None:
        if not isinstance(on_behalf_of_content_owner, str):
            raise TypeError("on_behalf_of_content_owner must be a string or None.")
        if not on_behalf_of_content_owner.strip():
            raise ValueError("on_behalf_of_content_owner cannot be an empty string.")
        new_channel["onBehalfOfContentOwner"] = on_behalf_of_content_owner

    DB.setdefault("channels", {})[new_channel["id"]] = new_channel
    return {"success": True, "channel": new_channel}



@tool_spec(
    spec={
    "name": "update_channel_metadata",
    "description": "Updates metadata of a YouTube channel.",
    "parameters": {
        "type": "object",
        "properties": {
            "channel_id": {
                "type": "string",
                "description": "The unique identifier of the channel to update."
            },
            "properties": {
                "type": "object",
                "description": "Key-value pairs of channel properties to update. Must be a dictionary with at least one valid property. Valid properties include:",
                "properties": {
                    "categoryId": {
                        "type": "string",
                        "description": "Channel category ID. Must be one of the ids in the videoCategories database."
                    },
                    "forUsername": {
                        "type": "string",
                        "description": "Channel username. Must be not empty when provided."
                    },
                    "hl": {
                        "type": "string",
                        "description": "Language setting. Must be one of: af, az, id, ms, bs, ca, cs, da, de, et, en-IN, en-GB, en, es, es-419, es-US, eu, fil, fr, fr-CA, gl, hr, zu, is, it, sw, lv, lt, hu, nl, no, uz, pl, pt-PT, pt, ro, sq, sk, sl, sr-Latn, fi, sv, vi, tr, be, bg, ky, kk, mk, mn, ru, sr, uk, el, hy, iw, ur, ar, fa, ne, mr, hi, as, bn, pa, gu, or, ta, te, kn, ml, si, th, lo, my, ka, am, km"
                    },
                    "managedByMe": {
                        "type": "boolean",
                        "description": "Whether channel is managed by authenticated user"
                    },
                    "maxResults": {
                        "type": "integer",
                        "description": "The maximum number of items that should be returned in the result set. Must be a positive integer when provided."
                    },
                    "mine": {
                        "type": "boolean",
                        "description": "Whether channel is owned by authenticated user"
                    },
                    "mySubscribers": {
                        "type": "boolean",
                        "description": "Whether authenticated user is subscribed to channel"
                    },
                    "onBehalfOfContentOwner": {
                        "type": "string",
                        "description": "CMS user information. Must be not empty when provided."
                    }
                },
                "required": []
            }
        },
        "required": [
            "channel_id",
            "properties"
        ]
    }
}
)
def update(channel_id: str, properties: Dict[str, Union[str, int, bool]]) -> Dict[str, Union[bool, Dict[str, Union[str, int, bool]]]]:

    """
    Updates metadata of a YouTube channel.

    Args:
        channel_id (str): The unique identifier of the channel to update.
        properties (Dict[str, Union[str, int, bool]]): Key-value pairs of channel properties to update. Must be a dictionary with at least one valid property. Valid properties include:
            - categoryId (Optional[str]): Channel category ID. Must be one of the ids in the videoCategories database.
            - forUsername (Optional[str]): Channel username. Must be not empty when provided.
            - hl (Optional[str]): Language setting. Must be one of: af, az, id, ms, bs, ca, cs, da, de, et, en-IN, en-GB, en, es, es-419, es-US, eu, fil, fr, fr-CA, gl, hr, zu, is, it, sw, lv, lt, hu, nl, no, uz, pl, pt-PT, pt, ro, sq, sk, sl, sr-Latn, fi, sv, vi, tr, be, bg, ky, kk, mk, mn, ru, sr, uk, el, hy, iw, ur, ar, fa, ne, mr, hi, as, bn, pa, gu, or, ta, te, kn, ml, si, th, lo, my, ka, am, km
            - managedByMe (Optional[bool]): Whether channel is managed by authenticated user
            - maxResults (Optional[int]): The maximum number of items that should be returned in the result set. Must be a positive integer when provided.
            - mine (Optional[bool]): Whether channel is owned by authenticated user
            - mySubscribers (Optional[bool]): Whether authenticated user is subscribed to channel
            - onBehalfOfContentOwner (Optional[str]): CMS user information. Must be not empty when provided.


    Returns:
        Dict[str, Union[bool, Dict[str, Union[str, int, bool]]]]: A dictionary containing:
                - success (bool): Whether the operation was successful
                - channel (Dict[str, Union[str, int, bool]]): The updated channel object with all properties
                    - id (str): Unique channel identifier
                    - categoryId (str): Channel category ID
                    - forUsername (str): Channel username
                    - hl (str): Language setting
                    - managedByMe (bool): Whether channel is managed by authenticated user
                    - maxResults (int): The maximum number of items that should be returned in the result set. Must be a positive integer when provided.
                    - mine (bool): Whether channel is owned by authenticated user
                    - mySubscribers (bool): Whether authenticated user is subscribed to channel
                    - onBehalfOfContentOwner (str): CMS user information. Must be not empty when provided.

    Raises:
        ValueError: If channel_id is empty or not found in the database,
                    or if category_id is empty or not found in the database when it is provided,
                    or if for_username is empty when it is provided,
                    or if hl is empty or invalid when it is provided,
                    or if max_results is negative when it is provided,
                    or if on_behalf_of_content_owner is empty when it is provided,
                    or if no update parameters are provided.
        TypeError: If channel_id is not a string,
                    or if properties is not a dictionary.
        ValidationError: If any property has invalid type or value (from Pydantic validation).
    """
    # Input Validation for channel_id
    if not isinstance(channel_id, str):
        raise TypeError("channel_id must be a string")
    if not channel_id.strip():
        raise ValueError("channel_id cannot be an empty string")

    # Check if channel exists
    channels = DB.get("channels", {})
    if channel_id not in channels:
        raise ValueError(f"Channel ID: {channel_id} not found in the database.")

    # Check if properties is provided
    if not properties:
        raise ValueError("No update parameters provided")

    # Validate properties using Pydantic model
    try:
        validated_properties = ChannelUpdateProperties(**properties)
    except ValidationError as e:
        # Re-raise ValidationError for proper handling by the framework
        raise e

    if "categoryId" in properties:
        if properties["categoryId"] not in [x["id"] for x in DB.get("videoCategories", {}).values()]:
            raise ValueError("Invalid categoryId, category not found in the database.")

    channel_to_update = channels[channel_id]
    for key, value in validated_properties.model_dump().items():
        if value is not None:
            channel_to_update[key] = value
    DB["channels"][channel_id] = channel_to_update
    
    return {"success": True, "channel": channel_to_update}
