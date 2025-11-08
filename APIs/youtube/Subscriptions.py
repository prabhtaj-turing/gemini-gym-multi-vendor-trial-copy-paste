from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Optional
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id
from typing import Optional, Dict, List, Union
from youtube.SimulationEngine.models import SnippetModel
from pydantic import ValidationError


"""
    Handles YouTube Subscriptions API operations.
    
    This class provides methods to manage subscriptions to YouTube channels,
    including creating, deleting, and listing subscriptions.
"""


@tool_spec(
    spec={
    "name": "create_subscription",
    "description": "Inserts a new subscription.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include."
            },
            "snippet": {
                "type": "object",
                "description": "The snippet object contains details about the subscription.",
                "properties": {
                    "channelId": {
                        "type": "string",
                        "description": "The subscribing channel's ID."
                    },
                    "resourceId": {
                        "type": "object",
                        "description": "The ID of the channel being subscribed to.",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "description": "Type of the resource (e.g., \"youtube#channel\")."
                            },
                            "channelId": {
                                "type": "string",
                                "description": "ID of the subscribed channel."
                            }
                        },
                        "required": [
                            "kind",
                            "channelId"
                        ]
                    }
                },
                "required": [
                    "channelId",
                    "resourceId"
                ]
            }
        },
        "required": [
            "part",
            "snippet"
        ]
    }
}
)
def insert(part: str, snippet: Dict[str, Union[str, Dict[str, str]]]) -> Dict[str, Union[str, Dict[str, Union[str, Dict[str, Union[str, Dict[str, str]]]]]]]:
    """
    Inserts a new subscription.

    Args:
        part(str): The part parameter specifies the properties of the record that the API response will include.
        snippet(Dict[str, Union[str, Dict[str, str]]]): The snippet object contains details about the subscription.
            - channelId(str): The subscribing channel's ID.
            - resourceId(Dict[str, str]): The ID of the channel being subscribed to.
                - kind(str): Type of the resource (e.g., "youtube#channel").
                - channelId(str): ID of the subscribed channel.

    Returns:
        Dict[str, Union[str, Dict[str, Union[str, Dict[str, Union[str, Dict[str, str]]]]]]]: A dictionary containing:
                - subscription (Dict[str, Union[str, Dict[str, Union[str, Dict[str, str]]]]]): The newly created subscription object:
                    - id (str): Unique subscription ID.
                    - snippet (Dict[str, Union[str, Dict[str, str]]]): Metadata about the subscription, including:
                        - channelId (str): The subscribing channel's ID.
                        - resourceId (Dict[str, str]): The ID of the channel being subscribed to.
                            - kind(str): Type of the resource (e.g., "youtube#channel").
                            - channelId(str): ID of the subscribed channel.

                - part (str): The part parameter specifies the subscription resource properties that the API response will include.

    Raises:
        ValueError: If the part or snippet parameter is not provided.
        TypeError: If the part parameter is not a string or the snippet parameter is not a dictionary.
        ValidationError: If the snippet parameter does not match the given schema.
            
    """
    if not part:
        raise ValueError("Part parameter required")

    if not isinstance(part, str):   
        raise TypeError("part must be a string")   

    if not snippet:
        raise ValueError("Snippet parameter required")

    if not isinstance(snippet, dict):
        raise TypeError("snippet must be a dictionary")

    try:
        snippet_model = SnippetModel(**snippet)
    except ValidationError as e:
        raise e

    new_id = generate_entity_id("subscription")
    new_subscription = {
        "id": new_id,
        "snippet": snippet_model.model_dump(),
    }

    DB.setdefault("subscriptions", {})[new_id] = new_subscription

    return {"subscription": new_subscription, "part": part}


@tool_spec(
    spec={
    "name": "delete_subscription",
    "description": "Deletes a subscription.",
    "parameters": {
        "type": "object",
        "properties": {
            "subscription_id": {
                "type": "string",
                "description": "The ID of the subscription to delete."
            }
        },
        "required": [
            "subscription_id"
        ]
    }
}
)
def delete(subscription_id: str) -> bool:
    """
    Deletes a subscription.

    Args:
        subscription_id(str): The ID of the subscription to delete.

    Returns:
        bool: True if the subscription was deleted

    Raises:
        ValueError: If the subscription ID is not provided or is not found in the database.
        TypeError: If the subscription ID is not a string.
    """
    if not subscription_id:
        raise ValueError("Subscription ID is required")

    if not isinstance(subscription_id, str):
        raise TypeError("Subscription ID must be a string")

    subscriptions = DB.get("subscriptions", {})

    if subscription_id not in subscriptions:
        raise ValueError("Subscription not found")

    del DB["subscriptions"][subscription_id]
    return True


@tool_spec(
    spec={
    "name": "list_subscriptions",
    "description": "Retrieves a list of subscriptions with optional filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include."
            },
            "channel_id": {
                "type": "string",
                "description": "The channelId parameter specifies a YouTube channel ID. The API will only return that channel's subscriptions. Defaults to None."
            },
            "subscription_id": {
                "type": "string",
                "description": "The id parameter identifies the subscription that is being retrieved. Defaults to None."
            },
            "mine": {
                "type": "boolean",
                "description": "The mine parameter can be used to instruct the API to only return subscriptions owned by the authenticated user. Defaults to False."
            },
            "my_recent_subscribers": {
                "type": "boolean",
                "description": "The myRecentSubscribers parameter can be used to instruct the API to only return subscriptions to the authenticated user's channel from the last 30 days. Defaults to False."
            },
            "my_subscribers": {
                "type": "boolean",
                "description": "The mySubscribers parameter can be used to instruct the API to only return subscriptions to the authenticated user's channel. Defaults to False."
            },
            "for_channel_id": {
                "type": "string",
                "description": "The forChannelId parameter specifies a YouTube channel ID. The API will only return subscriptions to that channel. Defaults to None."
            },
            "max_results": {
                "type": "integer",
                "description": "The maxResults parameter specifies the maximum number of items that should be returned in the result set. Defaults to 50."
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Defaults to None."
            },
            "on_behalf_of_content_owner_channel": {
                "type": "string",
                "description": "The onBehalfOfContentOwnerChannel parameter specifies the YouTube channel ID of the channel to which the user is being added. Defaults to None."
            },
            "order": {
                "type": "string",
                "description": "The order parameter specifies the order in which the API response should list subscriptions. Currently, only \"alphabetical\" is supported. Defaults to None."
            },
            "page_token": {
                "type": "string",
                "description": "The pageToken parameter identifies a specific page in the result set that should be returned. Defaults to None."
            }
        },
        "required": [
            "part"
        ]
    }
}
)
def list(
    part: str,
    channel_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    mine: bool = False,
    my_recent_subscribers: bool = False,
    my_subscribers: bool = False,
    for_channel_id: Optional[str] = None,
    max_results: Optional[int] = 50,
    on_behalf_of_content_owner: Optional[str] = None,
    on_behalf_of_content_owner_channel: Optional[str] = None,
    order: Optional[str] = None,
    page_token: Optional[str] = None,
) -> Dict[str, List[Dict[str, Union[str, Dict[str, Union[str, Dict[str, str]]]]]]]:
    """
    Retrieves a list of subscriptions with optional filters.

    Args:
        part(str): The part parameter specifies the properties of the record that the API response will include.
        channel_id(Optional[str]): The channelId parameter specifies a YouTube channel ID. The API will only return that channel's subscriptions. Defaults to None.
        subscription_id(Optional[str]): The id parameter identifies the subscription that is being retrieved. Defaults to None.
        mine(bool): The mine parameter can be used to instruct the API to only return subscriptions owned by the authenticated user. Defaults to False.
        my_recent_subscribers(bool): The myRecentSubscribers parameter can be used to instruct the API to only return subscriptions to the authenticated user's channel from the last 30 days. Defaults to False.
        my_subscribers(bool): The mySubscribers parameter can be used to instruct the API to only return subscriptions to the authenticated user's channel. Defaults to False.
        for_channel_id(Optional[str]): The forChannelId parameter specifies a YouTube channel ID. The API will only return subscriptions to that channel. Defaults to None.
        max_results(Optional[int]): The maxResults parameter specifies the maximum number of items that should be returned in the result set. Defaults to 50.
        on_behalf_of_content_owner(Optional[str]): The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Defaults to None.
        on_behalf_of_content_owner_channel(Optional[str]): The onBehalfOfContentOwnerChannel parameter specifies the YouTube channel ID of the channel to which the user is being added. Defaults to None.
        order(Optional[str]): The order parameter specifies the order in which the API response should list subscriptions. Currently, only "alphabetical" is supported. Defaults to None.
        page_token(Optional[str]): The pageToken parameter identifies a specific page in the result set that should be returned. Defaults to None.

    Returns:
        Dict[str, List[Dict[str, Union[str, Dict[str, Union[str, Dict[str, str]]]]]]]: A dictionary containing:
            - items (List[Dict[str, Union[str, Dict[str, Union[str, Dict[str, str]]]]]]): A list of subscription objects matching the filters:
                - id (str): The subscription ID.
                - snippet (Dict[str, Union[str, Dict[str, str]]]): Contains:
                    - channelId (str): The channel that owns the subscription.
                    - resourceId (Dict[str, str]): The channel being subscribed to.
                        - kind (str): Type of the resource (e.g., "youtube#channel").
                        - channelId (str): ID of the subscribed channel.
        
    Raises:
        ValueError: If for_channel_id is not a valid channel ID.
                    If subscription_id is not a valid subscription ID.
                    If channel_id is not a valid channel ID.
                    If on_behalf_of_content_owner_channel is not a valid channel ID.
                    If order is not "alphabetical".
                    If page_token is not a positive integer.
                    If max_results is not a positive integer.
                    If required parameters are not present.

        TypeError: If parameters are not of the correct type.
        
    """
    if not part:
        raise ValueError("part parameter required")

    if not isinstance(part, str):
        raise TypeError("part must be a string")

    if channel_id and not isinstance(channel_id, str):
        raise TypeError("channel_id must be a string")

    if subscription_id and not isinstance(subscription_id, str):
        raise TypeError("subscription_id must be a string")

    if for_channel_id and not isinstance(for_channel_id, str):
        raise TypeError("for_channel_id must be a string")

    if on_behalf_of_content_owner and not isinstance(on_behalf_of_content_owner, str):
        raise TypeError("on_behalf_of_content_owner must be a string")

    if on_behalf_of_content_owner_channel and not isinstance(on_behalf_of_content_owner_channel, str):
        raise TypeError("on_behalf_of_content_owner_channel must be a string")

    if order and not isinstance(order, str):
        raise TypeError("order must be a string")

    if order is not None and order not in ["alphabetical"]:
        raise ValueError("order must be 'alphabetical'")

    if page_token and not isinstance(page_token, str):
        raise TypeError("page_token must be a string")

    if page_token and not page_token.isdigit():
        raise ValueError("page_token must be a positive integer")

    if page_token is not None and not page_token.isdigit():
        raise ValueError("page_token must be a positive integer")

    if max_results and not isinstance(max_results, int):
        raise TypeError("max_results must be an integer")

    if mine is None:
        raise ValueError("mine parameter is required")

    if my_recent_subscribers is None:
        raise ValueError("my_recent_subscribers parameter is required")

    if my_subscribers is None:
        raise ValueError("my_subscribers parameter is required")

    if not isinstance(mine, bool):
        raise TypeError("mine parameter must be a boolean")

    if not isinstance(my_recent_subscribers, bool):
        raise TypeError("my_recent_subscribers parameter must be a boolean")

    if not isinstance(my_subscribers, bool):
        raise TypeError("my_subscribers parameter must be a boolean")

    if max_results and max_results <= 0:
        raise ValueError("max_results must be greater than 0")

    if page_token and not int(page_token) <= 0:
        raise ValueError("page_token must be a positive integer")

    if for_channel_id and for_channel_id not in DB.get("channels", {}):
        raise ValueError("for_channel_id must be a valid channel ID")

    if subscription_id and subscription_id not in DB.get("subscriptions", {}):
        raise ValueError("subscription_id must be a valid subscription ID")

    if channel_id and channel_id not in DB.get("channels", {}):
        raise ValueError("channel_id must be a valid channel ID")
    
    if on_behalf_of_content_owner and on_behalf_of_content_owner_channel not in DB.get("channels", {}):
        raise ValueError("on_behalf_of_content_owner_channel must be a valid channel ID")


    # Get all subscriptions from DB
    subscriptions = DB.get("subscriptions", {})
    filtered_subscriptions = []

    # Convert subscriptions dict to list
    for sub_id, sub_data in subscriptions.items():
        if subscription_id and sub_id != subscription_id:
            continue

        # Get the snippet data
        snippet = sub_data.get("snippet", {})

        # Apply filters
        if channel_id and snippet.get("channelId") != channel_id:
            continue

        subscribing_channel_id = snippet.get("resourceId", {}).get("channelId")

        if (
            for_channel_id
            and subscribing_channel_id != for_channel_id
        ):
            continue

        if mine or my_subscribers or my_recent_subscribers:
            if snippet.get("channelId") != DB.get("current_user", {}):
                continue

        if on_behalf_of_content_owner:
            if snippet.get("channelId") != on_behalf_of_content_owner_channel:
                continue


        filtered_subscriptions.append(sub_data)

    # Apply max_results if specified
    if order:
        if order == "alphabetical":
            filtered_subscriptions.sort(key=lambda x: x.get("snippet", {}).get("resourceId", "").get("channelId",""))

    if page_token:
        if (int(page_token)-1)*max_results > len(filtered_subscriptions):
            filtered_subscriptions = []
        filtered_subscriptions = filtered_subscriptions[(int(page_token)-1)*max_results:min(int(page_token)*max_results, len(filtered_subscriptions))]

    else:
        if max_results and max_results < len(filtered_subscriptions):
            filtered_subscriptions = filtered_subscriptions[:max_results]

    return {"items": filtered_subscriptions}
    