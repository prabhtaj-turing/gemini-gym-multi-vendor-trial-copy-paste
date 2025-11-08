"""
Activities module for youtube.
"""

from typing import Dict, List, Optional, Union
from common_utils.tool_spec_decorator import tool_spec

from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id
from youtube.SimulationEngine.custom_errors import (
    MissingPartParameterError,
    InvalidMaxResultsError,
    InvalidPartParameterError,
    InvalidActivityFilterError,
)


@tool_spec(
    spec={
    "name": "list_activities",
    "description": "Retrieves a list of activities with optional filters. This method allows fetching activities from YouTube based on various criteria such as channel ID, publication date range, and region code. Activities represent various actions that occur on YouTube, such as uploads, likes, comments, etc.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies a comma-separated list of one or more activity resource properties that the API response will include. Valid values are: 'id', 'snippet', and 'contentDetails'. If the parameter identifies a property that contains child properties, the child properties will be included in the response. Cannot be empty or None."
            },
            "channelId": {
                "type": "string",
                "description": "The channelId parameter specifies a YouTube channel ID. The API will only return that channel's activities. Exactly one of 'channelId' or 'mine' must be provided. Defaults to None."
            },
            "mine": {
                "type": "boolean",
                "description": "Set this parameter's value to true to retrieve a feed of the authenticated user's activities. Exactly one of 'channelId' or 'mine' must be provided. Defaults to None."
            },
            "maxResults": {
                "type": "integer",
                "description": "The maxResults parameter specifies the maximum number of items that should be returned in the result set. Must be a positive integer between 1 and 50 if provided. Defaults to None."
            },
            "pageToken": {
                "type": "string",
                "description": "The pageToken parameter identifies a specific page in the result set that should be returned. Defaults to None."
            },
            "publishedAfter": {
                "type": "string",
                "description": "The publishedAfter parameter specifies the earliest date and time that an activity could have occurred. Should be in ISO 8601 format. Defaults to None."
            },
            "publishedBefore": {
                "type": "string",
                "description": "The publishedBefore parameter specifies the latest date and time that an activity could have occurred. Should be in ISO 8601 format. Defaults to None."
            },
            "regionCode": {
                "type": "string",
                "description": "The regionCode parameter instructs the API to select a video chart available in the specified region. Should be a valid ISO 3166-1 alpha-2 country code. Defaults to None."
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
    channelId: Optional[str] = None,
    mine: Optional[bool] = None,
    maxResults: Optional[int] = None,
    pageToken: Optional[str] = None,
    publishedAfter: Optional[str] = None,
    publishedBefore: Optional[str] = None,
    regionCode: Optional[str] = None,
) -> Dict[str, Union[str, int, List[Dict[str, Union[str, int, Dict[str, Union[str, int]]]]]]]:
    """
    Retrieves a list of activities with optional filters.

    This method allows fetching activities from YouTube based on various criteria such as
    channel ID, publication date range, and region code. Activities represent various
    actions that occur on YouTube, such as uploads, likes, comments, etc.

    Args:
        part (str): The part parameter specifies a comma-separated list of one or more
            activity resource properties that the API response will include. Valid values
            are: 'id', 'snippet', and 'contentDetails'. If the parameter identifies a property
            that contains child properties, the child properties will be included in the
            response. Cannot be empty or None.
        channelId (Optional[str]): The channelId parameter specifies a YouTube channel ID.
            The API will only return that channel's activities. Exactly one of 'channelId' or 'mine' must be provided. Defaults to None.
        mine (Optional[bool]): Set this parameter's value to true to retrieve a feed of
            the authenticated user's activities. Exactly one of 'channelId' or 'mine' must be provided. Defaults to None.
        maxResults (Optional[int]): The maxResults parameter specifies the maximum number
            of items that should be returned in the result set. Must be a positive integer
            between 1 and 50 if provided. Defaults to None.
        pageToken (Optional[str]): The pageToken parameter identifies a specific page in
            the result set that should be returned. Defaults to None.
        publishedAfter (Optional[str]): The publishedAfter parameter specifies the earliest
            date and time that an activity could have occurred. Should be in ISO 8601 format. Defaults to None.
        publishedBefore (Optional[str]): The publishedBefore parameter specifies the latest
            date and time that an activity could have occurred. Should be in ISO 8601 format. Defaults to None.
        regionCode (Optional[str]): The regionCode parameter instructs the API to select a
            video chart available in the specified region. Should be a valid ISO 3166-1 alpha-2 country code. Defaults to None.

    Returns:
        Dict[str, Union[str, int, List[Dict[str, Union[str, int, Dict[str, Union[str, int]]]]]]]: A dictionary representing the ActivityListResponse resource, containing:
            - kind (str): Identifies the resource type. Value: "youtube#activityListResponse".
            - etag (str): The ETag of the response.
            - items (List[Dict[str, Union[str, int, Dict[str, Union[str, int]]]]]): A list of activity resources. Each activity resource contains:
                - id (str): The activity's unique ID.
                - kind (str): Identifies the resource type. Value: "youtube#activity".
                - etag (str): The ETag of the activity resource.
                - snippet (Dict[str, Union[str, Dict[str, Dict[str, Union[str, int]]]]]): Contains basic details about the activity (included if 'snippet' in part).
                    - publishedAt (str): The date and time the activity occurred (ISO 8601 format).
                    - channelId (str): The ID of the channel that performed the activity.
                    - title (str): The activity's title.
                    - description (str): The activity's description.
                    - thumbnails (Dict[str, Dict[str, Union[str, int]]]): A map of thumbnail images. Keys are "default", "medium", "high", "standard", "maxres". Each value is a thumbnail object containing:
                        - url (str): The thumbnail image's URL.
                        - width (int): The image's width.
                        - height (int): The image's height.
                    - channelTitle (str): The title of the channel that performed the activity.
                    - type (str): The type of activity. E.g., 'upload', 'like', etc.
                    - groupId (str): The ID of the group of items that the activity belongs to.
                - contentDetails (Dict[str, Dict[str, Union[str, Dict[str, str]]]]): Contains details about the activity's content (if 'contentDetails' in part). The object contains a property that identifies the type of activity.
                    - upload (Dict[str, str]): Present if activity type is 'upload'. Contains:
                        - videoId (str): The ID of the uploaded video.
                    - like (Dict[str, Dict[str, str]]): Present if activity type is 'like'. Contains:
                        - resourceId (Dict[str, str]): Identifies the liked resource. Contains:
                            - kind (str): The resource type (e.g., "youtube#video").
                            - videoId (str): The ID of the liked video.
                    - favorite (Dict[str, Dict[str, str]]): Present if activity type is 'favorite'. Contains:
                        - resourceId (Dict[str, str]): Identifies the favorited resource. Contains:
                            - kind (str): The resource type (e.g., "youtube#video").
                            - videoId (str): The ID of the favorited video.
                    - comment (Dict[str, Dict[str, str]]): Present if activity type is 'comment'. Contains:
                        - resourceId (Dict[str, str]): Identifies the commented resource. Contains:
                            - kind (str): The resource type (e.g., "youtube#video", "youtube#channel").
                            - videoId (str): The ID of the commented video.
                            - channelId (str): The ID of the channel that received the comment on its activity feed.
                    - subscription (Dict[str, Dict[str, str]]): Present if activity type is 'subscription'. Contains:
                        - resourceId (Dict[str, str]): Identifies the subscribed channel. Contains:
                            - kind (str): The resource type ("youtube#channel").
                            - channelId (str): The ID of the subscribed channel.
                    - playlistItem (Dict[str, Union[str, Dict[str, str]]]): Present if activity type is 'playlistItem'. Contains:
                        - resourceId (Dict[str, str]): Identifies the resource added to the playlist. Contains:
                            - kind (str): The resource type (e.g., "youtube#video").
                            - videoId (str): The ID of the video.
                        - playlistId (str): The ID of the playlist.
                        - playlistItemId (str): The ID of the playlist item.
                    - bulletin (Dict[str, Dict[str, str]]): Present if activity type is 'bulletin'. Contains:
                        - resourceId (Dict[str, str]): Identifies the resource associated with the bulletin. Contains:
                            - kind (str): The resource type (e.g., "youtube#video", "youtube#playlist", "youtube#channel").
                            - videoId (str): The ID of the video.
                            - playlistId (str): The ID of the playlist.
                            - channelId (str): The ID of the channel.
                    - social (Dict[str, Union[str, Dict[str, str]]]): Present if activity type is 'social'. Contains:
                        - type (str): The type of social network post.
                        - resourceId (Dict[str, str]): Identifies the resource.
                        - author (str): The author of the post.
                        - imageUrl (str): URL for an image associated with the post.
                        - referenceUrl (str): URL of the original post.
                    - recommendation (Dict[str, Union[str, Dict[str, str]]]): Present if activity type is 'recommendation'. Contains:
                        - reason (str): The reason for the recommendation.
                        - seedResourceId (Dict[str, str]): The resource that caused the recommendation.
                        - resourceId (Dict[str, str]): The recommended resource.
            - nextPageToken (str, optional): Token for retrieving the next page of results.
            - prevPageToken (str, optional): Token for retrieving the previous page of results.
            - pageInfo (Dict[str, int]): Pagination information for the result set.
                - totalResults (int): The total number of results available.
                - resultsPerPage (int): The number of results included in this response.

    Raises:
        MissingPartParameterError: If the 'part' parameter is not provided or is an empty string.
        InvalidPartParameterError: If the 'part' parameter contains invalid values. Valid values
            are 'id', 'snippet', and 'contentDetails'.
        TypeError: If any parameter is of an incorrect type:
            - 'part' is not a string
            - 'channelId' is not a string when provided
            - 'mine' is not a boolean when provided
            - 'maxResults' is not an integer when provided
            - 'pageToken' is not a string when provided
            - 'publishedAfter' is not a string when provided
            - 'publishedBefore' is not a string when provided
            - 'regionCode' is not a string when provided
        InvalidMaxResultsError: If 'maxResults' is provided but is not a positive integer between 1 and 50.
        InvalidActivityFilterError: If the condition that exactly one of 'channelId' or 'mine' must be provided is not met.
        KeyError: If expected keys (e.g., 'activities') are missing from the DB structure.
    """
    # --- Input Validation ---
    if (channelId is not None and mine is not None) or (
        channelId is None and mine is None
    ):
        raise InvalidActivityFilterError(
            "Exactly one of 'channelId' or 'mine' must be provided."
        )

    if not part:
        raise MissingPartParameterError(
            "Parameter 'part' is required and cannot be empty."
        )

    if not isinstance(part, str):
        raise TypeError("Parameter 'part' must be a string.")

    # Validate part parameter values
    valid_parts = ["id", "snippet", "contentDetails"]
    part_components = [p.strip() for p in part.split(",") if p.strip()]

    if not part_components:
        raise InvalidPartParameterError(
            "Parameter 'part' cannot be empty or consist only of whitespace and commas."
        )

    invalid_parts = [p for p in part_components if p not in valid_parts]
    if invalid_parts:
        raise InvalidPartParameterError(
            f"Invalid part parameter values: {', '.join(invalid_parts)}. "
            f"Valid values are: {', '.join(valid_parts)}"
        )

    if channelId is not None and not isinstance(channelId, str):
        raise TypeError("Parameter 'channelId' must be a string if provided.")

    if mine is not None and not isinstance(mine, bool):
        raise TypeError("Parameter 'mine' must be a boolean if provided.")

    if pageToken is not None and not isinstance(pageToken, str):
        raise TypeError("Parameter 'pageToken' must be a string if provided.")

    if publishedAfter is not None and not isinstance(publishedAfter, str):
        raise TypeError("Parameter 'publishedAfter' must be a string if provided.")

    if publishedBefore is not None and not isinstance(publishedBefore, str):
        raise TypeError("Parameter 'publishedBefore' must be a string if provided.")

    if regionCode is not None and not isinstance(regionCode, str):
        raise TypeError("Parameter 'regionCode' must be a string if provided.")

    if maxResults is not None:
        if not isinstance(maxResults, int):
            raise TypeError("Parameter 'maxResults' must be an integer if provided.")
        if not (1 <= maxResults <= 50):
            raise InvalidMaxResultsError(
                "Parameter 'maxResults' must be between 1 and 50, inclusive."
            )
    # --- End of Input Validation ---

    # Raises KeyError if DB or its keys are not structured as expected.
    if "activities" not in DB:
        return {
            "kind": "youtube#activityListResponse",
            "etag": "etag_value",
            "items": [],
            "pageInfo": {
                "totalResults": 0,
                "resultsPerPage": 0,
            },
        }

    activities_list = DB["activities"]
    results = []

    # Ensure we have a list to work with
    if activities_list:
        for activity in activities_list:
            results.append(activity)

    # Apply filters
    if channelId:
        filtered_results = []
        for a in results:
            if (
                isinstance(a, dict)
                and a.get("snippet", {}).get("channelId") == channelId
            ):
                filtered_results.append(a)
        results = filtered_results

    if mine is not None:
        filtered_results = []
        for a in results:
            if isinstance(a, dict) and a.get("mine") == mine:
                filtered_results.append(a)
        results = filtered_results

    if publishedAfter:
        filtered_results = []
        for a in results:
            if isinstance(a, dict):
                published_at = a.get("snippet", {}).get(
                    "publishedAt", "1970-01-01T00:00:00Z"
                )
                if published_at >= publishedAfter:
                    filtered_results.append(a)
        results = filtered_results

    if publishedBefore:
        filtered_results = []
        for a in results:
            if isinstance(a, dict):
                published_at = a.get("snippet", {}).get(
                    "publishedAt", "2099-12-31T23:59:59Z"
                )
                if published_at <= publishedBefore:
                    filtered_results.append(a)
        results = filtered_results

    if regionCode:
        filtered_results = []
        for a in results:
            if (
                isinstance(a, dict)
                and a.get("snippet", {}).get("regionCode") == regionCode
            ):
                filtered_results.append(a)
        results = filtered_results

    # Store total results before pagination
    total_results = len(results)

    # Handle pagination
    start_index = 0
    if pageToken:
        try:
            start_index = int(pageToken)
        except ValueError:
            start_index = 0

    # Set default maxResults if not provided
    if maxResults is None:
        maxResults = 5  # YouTube API default for activities

    # Apply pagination
    end_index = start_index + maxResults
    paginated_results = results[start_index:end_index]

    # Filter each activity item based on the part parameter
    filtered_items = []
    for activity in paginated_results:
        if not isinstance(activity, dict):
            continue

        filtered_activity = {
            "kind": "youtube#activity",
            "etag": activity.get("etag", "etag_value"),
        }

        # Include properties based on part parameter
        if "id" in part_components:
            filtered_activity["id"] = activity.get("id", "")

        if "snippet" in part_components:
            snippet = activity.get("snippet", {})
            filtered_activity["snippet"] = {
                "publishedAt": snippet.get("publishedAt", ""),
                "channelId": snippet.get("channelId", ""),
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "thumbnails": snippet.get("thumbnails", {}),
                "channelTitle": snippet.get("channelTitle", ""),
                "type": snippet.get("type", ""),
                "groupId": snippet.get("groupId", ""),
            }

        if "contentDetails" in part_components:
            content_details = activity.get("contentDetails", {})
            filtered_activity["contentDetails"] = content_details

        filtered_items.append(filtered_activity)

    # Prepare response
    response = {
        "kind": "youtube#activityListResponse",
        "etag": "etag_value",
        "items": filtered_items,
        "pageInfo": {
            "totalResults": total_results,
            "resultsPerPage": len(filtered_items),
        },
    }

    # Add nextPageToken if there are more results
    if end_index < total_results:
        response["nextPageToken"] = str(end_index)

    # Add prevPageToken if we're not on the first page
    if start_index > 0:
        prev_start = max(0, start_index - maxResults)
        response["prevPageToken"] = str(prev_start) if prev_start > 0 else "0"

    return response
