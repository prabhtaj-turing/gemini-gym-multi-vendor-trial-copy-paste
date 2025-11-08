from typing import Dict, Optional, Union, List
from common_utils.tool_spec_decorator import tool_spec
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import _validate_parameter

"""Handles YouTube search API operations."""

@tool_spec(
    spec={
    "name": "list_searches",
    "description": "Returns a collection of search results that match the query parameters.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies a comma-separated list of one or more search resource properties. Valid values: \"snippet\", \"id\""
            },
            "q": {
                "type": "string",
                "description": "The query term to search for. Defaults to None."
            },
            "channel_id": {
                "type": "string",
                "description": "Filter results to only contain resources created by the specified channel. Defaults to None."
            },
            "channel_type": {
                "type": "string",
                "description": "Filter results to only contain channels of a particular type. Valid values: \"any\", \"show\". Defaults to None."
            },
            "max_results": {
                "type": "integer",
                "description": "The maximum number of items that should be returned in the result set. Valid range: 0-50. Defaults to 25."
            },
            "order": {
                "type": "string",
                "description": "The order in which to sort the returned resources. Valid values: \"relevance\", \"date\", \"rating\", \"title\", \"videoCount\", \"viewCount\". Defaults to \"relevance\"."
            },
            "type": {
                "type": "string",
                "description": "A comma-separated list of resource types that should be included in the search response. Valid values: \"video\", \"channel\", \"playlist\". Defaults to \"video,channel,playlist\"."
            },
            "video_caption": {
                "type": "string",
                "description": "Filter videos based on the presence, absence, or type of captions. Valid values: \"any\", \"closedCaption\", \"none\". Defaults to None."
            },
            "video_category_id": {
                "type": "string",
                "description": "Filter videos by category ID. Defaults to None."
            },
            "video_definition": {
                "type": "string",
                "description": "Filter videos by definition (high or standard). Valid values: \"any\", \"high\", \"standard\". Defaults to None."
            },
            "video_duration": {
                "type": "string",
                "description": "Filter videos by duration. Valid values: \"any\", \"long\", \"medium\", \"short\". Defaults to None."
            },
            "video_embeddable": {
                "type": "string",
                "description": "Filter videos that can be embedded. Valid values: \"any\", \"true\". Defaults to None."
            },
            "video_license": {
                "type": "string",
                "description": "Filter videos by license type. Valid values: \"any\", \"creativeCommon\", \"youtube\". Defaults to None."
            },
            "video_syndicated": {
                "type": "string",
                "description": "Filter videos by syndication status. Valid values: \"any\", \"true\". Defaults to None."
            },
            "video_type": {
                "type": "string",
                "description": "Filter videos by type. Valid values: \"any\", \"episode\", \"movie\". Defaults to None."
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
    q: Optional[str] = None,
    channel_id: Optional[str] = None,
    channel_type: Optional[str] = None,
    max_results: Optional[int] = 25,
    order: Optional[str] = "relevance",
    type: Optional[str] = "video,channel,playlist",
    video_caption: Optional[str] = None,
    video_category_id: Optional[str] = None,
    video_definition: Optional[str] = None,
    video_duration: Optional[str] = None,
    video_embeddable: Optional[str] = None,
    video_license: Optional[str] = None,
    video_syndicated: Optional[str] = None,
    video_type: Optional[str] = None,
) -> Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, Union[str, int, List[str], Dict[str, Union[str, int, bool]]]]]]], Dict[str, int]]]:
    """Returns a collection of search results that match the query parameters.

    Args:
        part (str): The part parameter specifies a comma-separated list of one or more search resource properties.
            Valid values: "snippet", "id"
        q (Optional[str]): The query term to search for. Defaults to None.
        channel_id (Optional[str]): Filter results to only contain resources created by the specified channel. Defaults to None.
        channel_type (Optional[str]): Filter results to only contain channels of a particular type.
            Valid values: "any", "show". Defaults to None.
        max_results (Optional[int]): The maximum number of items that should be returned in the result set.
            Valid range: 0-50. Defaults to 25.
        order (Optional[str]): The order in which to sort the returned resources.
            Valid values: "relevance", "date", "rating", "title", "videoCount", "viewCount". Defaults to "relevance".
        type (Optional[str]): A comma-separated list of resource types that should be included in the search response.
            Valid values: "video", "channel", "playlist". Defaults to "video,channel,playlist".
        video_caption (Optional[str]): Filter videos based on the presence, absence, or type of captions.
            Valid values: "any", "closedCaption", "none". Defaults to None.
        video_category_id (Optional[str]): Filter videos by category ID. Defaults to None.
        video_definition (Optional[str]): Filter videos by definition (high or standard).
            Valid values: "any", "high", "standard". Defaults to None.
        video_duration (Optional[str]): Filter videos by duration.
            Valid values: "any", "long", "medium", "short". Defaults to None.
        video_embeddable (Optional[str]): Filter videos that can be embedded.
            Valid values: "any", "true". Defaults to None.
        video_license (Optional[str]): Filter videos by license type.
            Valid values: "any", "creativeCommon", "youtube". Defaults to None.
        video_syndicated (Optional[str]): Filter videos by syndication status.
            Valid values: "any", "true". Defaults to None.
        video_type (Optional[str]): Filter videos by type.
            Valid values: "any", "episode", "movie". Defaults to None.

    Returns:
         Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, Union[str, int, List[str], Dict[str, Union[str, int, bool]]]]]]], Dict[str, int]]]: A dictionary simulating the YouTube API search list response:
            - kind (str): Resource type ("youtube#searchListResponse").
            - etag (str): Etag of the result set.
            - items (List[Dict[str, Union[str, Dict[str, Union[str, int, List[str], Dict[str, Union[str, int]]]]]]]): List of video resources matching the filters. Each item is a dictionary with the following keys:
                - id (str): The ID of the video.
                - snippet (Optional[Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]]]): The snippet of the video.
                    - publishedAt (str): The date and time the video was published.
                    - channelId (str): The ID of the channel that the video is uploaded to.
                    - title (str): The title of the video.
                    - description (str): The description of the video.
                    - thumbnails (Dict[str, Dict[str, Union[str, int]]]): The thumbnails of the video.
                        - default (Dict[str, Union[str, int]]): The default thumbnail of the video.
                            - url (str): The URL of the default thumbnail.
                            - width (int): The width of the default thumbnail.
                            - height (int): The height of the default thumbnail.
                        - medium (Dict[str, Union[str, int]]): The medium thumbnail of the video.
                            - url (str): The URL of the medium thumbnail.
                            - width (int): The width of the medium thumbnail.
                            - height (int): The height of the medium thumbnail.
                        - high (Dict[str, Union[str, int]]): The high thumbnail of the video.
                            - url (str): The URL of the high thumbnail.
                            - width (int): The width of the high thumbnail.
                            - height (int): The height of the high thumbnail.
                    - channelTitle (str): The title of the channel that the video is uploaded to.
                    - tags (List[str]): The tags of the video.
                    - categoryId (str): The ID of the category that the video belongs to.
                - statistics (Optional[Dict[str, int]]): The statistics of the video.
                    - viewCount (int): The view count of the video.
                    - likeCount (int): The like count of the video.
                    - dislikeCount (int): The dislike count of the video.
                    - commentCount (int): The comment count of the video.
                - status (Optional[Dict[str, Union[str, bool]]]): The status of the video.
                    - uploadStatus (str): The upload status of the video.
                    - privacyStatus (str): The privacy status of the video.
                    - embeddable (bool): Whether the video is embeddable.
                    - madeForKids (bool): Whether the video is made for kids.

            - pageInfo (Dict[str, int]): Includes 'totalResults' and 'resultsPerPage' counts.
                - totalResults (int): Total number of results returned.
                - resultsPerPage (int): Number of results per page.

    Raises:
        ValueError: If any parameter validation fails.
    """
    if not part:
        raise ValueError("The 'part' parameter is required.")

    valid_parts = ["snippet", "id"]
    for p in part.split(","):
        if p.strip() not in valid_parts:
            raise ValueError(f"Invalid part parameter: {p}")

    # Validate max_results
    if max_results is not None:
        if not isinstance(max_results, int):
            raise ValueError("max_results must be an integer")
        if max_results < 0:
            raise ValueError("max_results must be non-negative")

    # Validate order
    valid_orders = ["relevance", "date", "rating", "title", "videoCount", "viewCount"]
    if order not in valid_orders:
        raise ValueError(f"Invalid order parameter: {order}")

    # Validate type
    valid_types = ["video", "channel", "playlist"]
    search_types = [t.strip() for t in type.split(",")] if type else ["video", "channel", "playlist"]
    for t in search_types:
        if t not in valid_types:
            raise ValueError(f"Invalid type parameter: {t}. Valid values are: {', '.join(valid_types)}")

    # Validate parameters using the helper function
    _validate_parameter(channel_type, ["any", "show"], "channel_type")
    _validate_parameter(video_caption, ["any", "closedCaption", "none"], "video_caption")
    _validate_parameter(video_definition, ["any", "high", "standard"], "video_definition")
    _validate_parameter(video_duration, ["any", "long", "medium", "short"], "video_duration")
    _validate_parameter(video_embeddable, ["any", "true"], "video_embeddable")
    _validate_parameter(video_license, ["any", "creativeCommon", "youtube"], "video_license")
    _validate_parameter(video_syndicated, ["any", "true"], "video_syndicated")
    _validate_parameter(video_type, ["any", "episode", "movie"], "video_type")

    # Handle multiple types
    search_types = [t.strip() for t in type.split(",")] if type else ["video", "channel", "playlist"]

    results = []
    for search_type in search_types:
        if search_type == "video":
            videos = DB["videos"].values()
            filtered_videos = videos
            if q:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if q.lower() in v["snippet"]["title"].lower()
                    or q.lower() in v["snippet"]["description"].lower()
                ]
            if channel_id:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if v["snippet"]["channelId"] == channel_id
                ]
            if video_caption:
                if video_caption == "any":
                    filtered_videos = [
                        v
                        for v in filtered_videos
                        if v["contentDetails"]["caption"] == "true"
                    ]
                elif video_caption == "closedCaption":
                    filtered_videos = [
                        v
                        for v in filtered_videos
                        if v["contentDetails"]["caption"] == "true"
                    ]
                elif video_caption == "none":
                    filtered_videos = [
                        v
                        for v in filtered_videos
                        if v["contentDetails"]["caption"] == "false"
                    ]
            if video_category_id:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if v["snippet"]["categoryId"] == video_category_id
                ]
            if video_definition:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if v["contentDetails"]["definition"] == video_definition
                ]
            if video_duration:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if v["contentDetails"]["duration"].startswith(video_duration)
                ]
            if video_embeddable:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if v["status"]["embeddable"] == (video_embeddable == "true")
                ]
            if video_license:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if v["status"]["license"] == video_license
                ]
            if video_syndicated:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if v["status"].get("syndicated", False)
                    == (video_syndicated == "true")
                ]
            if video_type:
                filtered_videos = [
                    v
                    for v in filtered_videos
                    if v["status"].get("type", "") == video_type
                ]

            for video in filtered_videos:
                item = {
                    "kind": "youtube#searchResult",
                    "etag": "etag_value",
                    "id": {"kind": "youtube#video", "videoId": video["id"]},
                }
                if "snippet" in part:
                    snippet = video.get("snippet", {})
                    item["snippet"] = {
                        "channelId": snippet.get("channelId", ""),
                        "title": snippet.get("title", ""),
                        "description": snippet.get("description", ""),
                        "publishedAt": snippet.get("publishedAt", ""),
                        "categoryId": snippet.get("categoryId", ""),
                    }
                results.append(item)

        elif search_type == "channel":
            channels = DB["channels"].values()
            filtered_channels = channels
            if q:
                filtered_channels = [
                    c
                    for c in filtered_channels
                    if q.lower() in c.get("snippet", {}).get("title", "").lower()
                    or q.lower() in c.get("snippet", {}).get("description", "").lower()
                ]
            if channel_id:
                filtered_channels = [
                    c for c in filtered_channels if c["id"] == channel_id
                ]
            if channel_type:
                filtered_channels = [
                    c
                    for c in filtered_channels
                    if c.get("snippet", {}).get("type", "") == channel_type
                ]

            for channel in filtered_channels:
                item = {
                    "kind": "youtube#searchResult",
                    "etag": "etag_value",
                    "id": {"kind": "youtube#channel", "channelId": channel["id"]},
                }
                if "snippet" in part:
                    item["snippet"] = channel.get("snippet", {})
                results.append(item)

        elif search_type == "playlist":
            playlists = DB.get("playlists", {}).values()
            filtered_playlists = playlists
            if q:
                filtered_playlists = [
                    p
                    for p in filtered_playlists
                    if q.lower() in p["snippet"]["title"].lower()
                    or q.lower() in p["snippet"]["description"].lower()
                ]
            if channel_id:
                filtered_playlists = [
                    p
                    for p in filtered_playlists
                    if p["snippet"]["channelId"] == channel_id
                ]

            for playlist in filtered_playlists:
                item = {
                    "kind": "youtube#searchResult",
                    "etag": "etag_value",
                    "id": {"kind": "youtube#playlist", "playlistId": playlist["id"]},
                }
                if "snippet" in part:
                    item["snippet"] = playlist["snippet"]
                results.append(item)

    # Order the results
    if order == "relevance":
        pass  # Default order
    elif order == "viewCount":
        def get_view_count(item):
            if item["id"]["kind"] == "youtube#video":
                video_id = item["id"]["videoId"]
                return int(DB["videos"].get(video_id, {}).get("statistics", {}).get("viewCount", "0"))
            elif item["id"]["kind"] == "youtube#channel":
                channel_id = item["id"]["channelId"]
                return int(DB["channels"].get(channel_id, {}).get("statistics", {}).get("viewCount", "0"))
            return 0  # Default for playlists or other types

        results = sorted(results, key=get_view_count, reverse=True)
    elif order == "date":
        results = sorted(
            results,
            key=lambda x: x.get("snippet", {}).get("publishedAt", "0000-00-00"),
            reverse=True,
        )
    elif order == "title":
        results = sorted(
            results, key=lambda x: x.get("snippet", {}).get("title", "").lower()
        )
    elif order == "rating":
        def get_rating(item):
            if item["id"]["kind"] == "youtube#video":
                video_id = item["id"]["videoId"]
                return int(DB["videos"].get(video_id, {}).get("statistics", {}).get("likeCount", "0"))
            elif item["id"]["kind"] == "youtube#channel":
                channel_id = item["id"]["channelId"]
                return int(DB["channels"].get(channel_id, {}).get("statistics", {}).get("likeCount", "0"))
            return 0  # Default for playlists or other types

        results = sorted(results, key=get_rating, reverse=True)
    elif order == "videoCount":
        def get_video_count(item):
            if item["id"]["kind"] == "youtube#channel":
                channel_id = item["id"]["channelId"]
                return int(DB["channels"].get(channel_id, {}).get("statistics", {}).get("videoCount", "0"))
            return 0  # Default for videos and playlists

        results = sorted(results, key=get_video_count, reverse=True)
    else:
        raise ValueError(f"Invalid order parameter: {order}")

    if max_results:
        results = results[: min(max_results, 50)]

    return {
        "kind": "youtube#searchListResponse",
        "etag": "etag_value",
        "items": results,
        "pageInfo": {"totalResults": len(results), "resultsPerPage": len(results)},
    }

