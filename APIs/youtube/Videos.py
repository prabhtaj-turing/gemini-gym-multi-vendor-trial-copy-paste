from common_utils.tool_spec_decorator import tool_spec
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id
from typing import Optional, Dict, List, Union
from youtube.SimulationEngine.models import SnippetUpdateModel, StatusUpdateModel, StatisticsUpdateModel, VideoUploadModel
from pydantic import ValidationError
from youtube.SimulationEngine.custom_errors import VideoIdNotFoundError, InvalidVideoIdError
import datetime

"""Handles YouTube video resource API operations."""


@tool_spec(
    spec={
    "name": "list_videos",
    "description": "Retrieves a list of videos with optional filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Must be one of: 'snippet', 'contentDetails', 'statistics', 'status'."
            },
            "chart": {
                "type": "string",
                "description": "Set this parameter to retrieve a list of videos that match the criteria specified by the chart parameter value. Must be \"mostPopular\". Defaults to None. Only one of chart, id, or my_rating must be provided."
            },
            "id": {
                "type": "string",
                "description": "The id parameter specifies a comma-separated list of the YouTube video ID(s) for the resource(s) that are being retrieved. Must be comma separated string of valid video IDs. Defaults to None. Only one of chart, id, or my_rating must be provided."
            },
            "my_rating": {
                "type": "string",
                "description": "Set this parameter to retrieve a list of videos that match the criteria specified by the myRating parameter value. Defaults to None. Only one of chart, id, or my_rating must be provided."
            },
            "max_results": {
                "type": "integer",
                "description": "The maxResults parameter specifies the maximum number of items that should be returned in the result set. Must be an integer between 1 and 50. Defaults to 5."
            },
            "page_token": {
                "type": "string",
                "description": "The pageToken parameter identifies a specific page in the result set that should be returned. Must be an integer greater than 0 and within the range of the total number of results. Defaults to None."
            },
            "user_id": {
                "type": "string",
                "description": "The user_id parameter is required when using my_rating parameter. Must be a valid user ID. Defaults to None."
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
    chart: Optional[str] = None,
    id: Optional[str] = None,
    my_rating: Optional[str] = None,
    max_results: Optional[int] = 5,
    page_token: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, Union[str, int, Dict[str, Union[str, int]]]]]]], Dict[str, int]]]:
    """Retrieves a list of videos with optional filters.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Must be one of: 'snippet', 'contentDetails', 'statistics', 'status'.
        chart (Optional[str]): Set this parameter to retrieve a list of videos that match the criteria specified by the chart parameter value. Must be "mostPopular". Defaults to None. Only one of chart, id, or my_rating must be provided.
        id (Optional[str]): The id parameter specifies a comma-separated list of the YouTube video ID(s) for the resource(s) that are being retrieved. Must be comma separated string of valid video IDs. Defaults to None. Only one of chart, id, or my_rating must be provided.
        my_rating (Optional[str]): Set this parameter to retrieve a list of videos that match the criteria specified by the myRating parameter value. Defaults to None. Only one of chart, id, or my_rating must be provided.
        max_results (Optional[int]): The maxResults parameter specifies the maximum number of items that should be returned in the result set. Must be an integer between 1 and 50. Defaults to 5.
        page_token (Optional[str]): The pageToken parameter identifies a specific page in the result set that should be returned. Must be an integer greater than 0 and within the range of the total number of results. Defaults to None.
        user_id (Optional[str]): The user_id parameter is required when using my_rating parameter. Must be a valid user ID. Defaults to None.

    Returns:
        Dict[str, Union[str, List[Dict[str, Union[str, Dict[str, Union[str, int, Dict[str, Union[str, int]]]]]]], Dict[str, int]]]: A dictionary containing:
            - kind (str): Resource type ("youtube#videoListResponse").
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

            - pageInfo (Dict[str, int]): Pagination details:
                - totalResults (int): Total number of results returned.
                - resultsPerPage (int): Number of results per page.

    Raises:
        ValueError: If the 'part' parameter is not provided or is an empty string.
                    or if the 'part' parameter is not one of the valid parts : ['snippet', 'contentDetails', 'statistics', 'status'].
                    or if more than one of 'chart', 'id', or 'my_rating' is provided.
                    or if the 'chart' parameter is provided but not "mostPopular".
                    or if the 'id' parameter is provided but not a comma separated string of valid video IDs
                    or if the 'user_id' parameter is not provided or not a valid user ID when 'my_rating' is provided
                    or if the 'max_results' parameter is provided but not an integer between 1 and 50.
                    or if the 'page_token' parameter is provided but not an integer greater than 0 and within the range of the total number of results.
        TypeError: If the 'part' parameter is not a string.
                    or if the 'id' parameter is provided but not a string.
                    or if the 'user_id' parameter is provided but not a string.
                    or if the 'my_rating' parameter is provided but not a string.
                    or if the 'max_results' parameter is provided but not an integer.
                    or if the 'page_token' parameter is provided but not an integer.


    """
    if not part or part is None:
        raise ValueError("The 'part' parameter is required.")

    if not isinstance(part, str):
        raise TypeError("The 'part' parameter must be a string.")

    if part not in ["snippet", "contentDetails", "statistics", "status"]:
        raise ValueError("Invalid value for 'part'. Must be one of: 'snippet', 'contentDetails', 'statistics', 'status'.")

    filter_params = [chart, id, my_rating]
    if sum(1 for param in filter_params if param is not None) != 1:
        raise ValueError("Only one of 'chart', 'id', or 'my_rating' can be provided.")
    # Ensure DB["videos"] exists and is a dictionary
    videos = DB.get("videos", {})
    if not isinstance(videos, dict):
        videos = {}
        DB["videos"] = videos

    filtered_videos = []
    for video_id, video_data in videos.items():
        if isinstance(video_data, dict):
            filtered_videos.append(video_data)
        else:
            # Skip invalid video data
            continue

    results = []

    if chart is not None:
        if not isinstance(chart, str):  
            raise TypeError("The 'chart' parameter must be a string.")
        if chart != "mostPopular":
            raise ValueError("Invalid value for 'chart'. Only 'mostPopular' is supported.")

        # Convert viewCount to int for proper sorting
        results = sorted(
            filtered_videos,
            key=lambda v: int(v.get("statistics", {}).get("viewCount", "0")),
            reverse=True,
        )

    elif id is not None:
        if not isinstance(id, str):
            raise TypeError("The 'id' parameter must be a string.")
        id_list = [vid.strip() for vid in id.split(",")]
        for video_id in id_list:
            if video_id not in DB.get("videos", {}):
                raise ValueError(f"Video with ID '{video_id}' not found.")
            else:   
                results.append(DB["videos"][video_id])

    elif my_rating is not None:
        if user_id is None:
            raise ValueError("The 'user_id' parameter is required when using 'my_rating' parameter.")
        if not isinstance(user_id, str):
            raise TypeError("The 'user_id' parameter must be a string.")
        if user_id not in DB.get("users", {}):
            raise ValueError(f"User with ID '{user_id}' not found.")
        if not isinstance(my_rating, str):
            raise TypeError("The 'my_rating' parameter must be a string.")
        #not implemented as the current DB does not store user ratings

    if max_results is not None:
        if not isinstance(max_results, int):
            raise TypeError("The 'max_results' parameter must be an integer.")
        if max_results <= 0 or max_results > 50:
            raise ValueError("The 'max_results' parameter must be greater than 0 and less than 50.")

    if page_token is not None:
        if not isinstance(page_token, int):
            raise TypeError("The 'page_token' parameter must be an integer.")
        if page_token < 1:
            raise ValueError("The 'page_token' parameter must be greater than 0.")
        page_index = page_token - 1
        if page_index*max_results >= len(results):
            raise ValueError("The 'page_token' parameter is out of range.")
        results = results[page_index*max_results:min(page_index*max_results + max_results, len(results))]

    else:
        results = results[:min(max_results, len(results))]

    filtered_results = []

    for result in results:
        filtered_result = {}
        filtered_result["id"] = result["id"]
        if part == "snippet":
            filtered_result["snippet"] = result["snippet"]
        elif part == "contentDetails":
            filtered_result["contentDetails"] = result["contentDetails"]
        elif part == "statistics":
            filtered_result["statistics"] = result["statistics"]
        elif part == "status":
            filtered_result["status"] = result["status"]
        filtered_results.append(filtered_result)

    return {
        "kind": "youtube#videoListResponse",
        "items": filtered_results,
        "pageInfo": {
            "totalResults": len(filtered_results),
            "resultsPerPage": len(filtered_results),
        },
    }


@tool_spec(
    spec={
    "name": "rate_video",
    "description": "Rates a video by adjusting like/dislike counts directly.",
    "parameters": {
        "type": "object",
        "properties": {
            "video_id": {
                "type": "string",
                "description": "The ID of the video to rate."
            },
            "rating": {
                "type": "string",
                "description": "Must be one of: \"like\", \"dislike\", \"none\"."
            },
            "on_behalf_of": {
                "type": "string",
                "description": "Ignored (no user data is stored). Defaults to None."
            }
        },
        "required": [
            "video_id",
            "rating"
        ]
    }
}
)
def rate(
    video_id: str, rating: str, on_behalf_of: Optional[str] = None
) -> Dict[str, bool]:
    """Rates a video by adjusting like/dislike counts directly.

    Args:
        video_id (str): The ID of the video to rate.
        rating (str): Must be one of: "like", "dislike", "none".
        on_behalf_of (Optional[str]): Ignored (no user data is stored). Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary indicating success of the operation:
            - success (bool): True if rating was applied.
    
    Raises:
        ValueError: If video_id or rating is not provided or is an empty string 
                    or if rating is not one of ['like', 'dislike', 'none']
                    or if video_id is not found in the database.
        TypeError: If rating or video_id or on_behalf_of (if provided) is not a string.

    """
    if video_id is None or video_id == "":
        raise ValueError("video_id is required")

    if not isinstance(video_id, str):
        raise TypeError("video_id must be a string")

    if rating is None or rating == "":
        raise ValueError("rating is required")

    if not isinstance(rating, str):
        raise TypeError("rating must be a string")

    if on_behalf_of is not None and not isinstance(on_behalf_of, str):
        raise TypeError("on_behalf_of must be a string")
    
    videos = DB.get("videos", {})

    if video_id not in videos:
        raise ValueError("Video not found")

    if rating not in ["like", "dislike", "none"]:
        raise ValueError("Invalid rating, must be one of ['like', 'dislike', 'none']")

    stats = DB["videos"][video_id].get("statistics", {})

    # Convert string counts to integers for arithmetic operations
    current_likes = int(stats.get("likeCount", "0"))
    current_dislikes = int(stats.get("dislikeCount", "0"))

    if rating == "like":
        current_likes += 1
        # If there was a previous dislike, remove it
        if current_dislikes > 0:
            current_dislikes -= 1
    elif rating == "dislike":
        current_dislikes += 1
        # If there was a previous like, remove it
        if current_likes > 0:
            current_likes -= 1
    elif rating == "none":
        # Remove any existing rating
        if current_likes > 0:
            current_likes -= 1
        if current_dislikes > 0:
            current_dislikes -= 1

    # Convert back to strings for storage
    stats["likeCount"] = str(current_likes)
    stats["dislikeCount"] = str(current_dislikes)

    return {"success": True}


@tool_spec(
    spec={
    "name": "report_video_abuse",
    "description": "Reports a video for abuse.",
    "parameters": {
        "type": "object",
        "properties": {
            "video_id": {
                "type": "string",
                "description": "The ID of the video to report."
            },
            "reason_id": {
                "type": "string",
                "description": "The ID of the reason for reporting the video."
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "The ID of the content owner on whose behalf the report is being made. Defaults to None."
            },
            "secondary_reason_id": {
                "type": "string",
                "description": "More specific reason for reporting abuse, identified by its unique ID. Defaults to None."
            },
            "comments": {
                "type": "string",
                "description": "Provides any additional information that the reporter wants to add. Defaults to None."
            },
            "language": {
                "type": "string",
                "description": "Identifies a language spoken by the reporter. Defaults to None."
            }
        },
        "required": [
            "video_id",
            "reason_id"
        ]
    }
}
)
def report_abuse(
    video_id: str,
    reason_id: str,
    on_behalf_of_content_owner: Optional[str] = None,
    secondary_reason_id: Optional[str] = None,
    comments: Optional[str] = None,
    language: Optional[str] = None

) -> Dict[str, bool]:
    """Reports a video for abuse.

    Args:
        video_id (str): The ID of the video to report.
        reason_id (str): The ID of the reason for reporting the video.
        on_behalf_of_content_owner (Optional[str]): The ID of the content owner on whose behalf the report is being made. Defaults to None.
        secondary_reason_id (Optional[str]): More specific reason for reporting abuse, identified by its unique ID. Defaults to None.
        comments (Optional[str]): Provides any additional information that the reporter wants to add. Defaults to None.
        language (Optional[str]): Identifies a language spoken by the reporter. Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary indicating the result:
            - success (bool): True if the report was accepted.
    """
    # Validate inputs
    if not video_id:
        raise ValueError("video_id is required")
    if not isinstance(video_id, str):
        raise TypeError("video_id must be a string")
    if not reason_id:
        raise ValueError("reason_id is required")
    if not isinstance(reason_id, str):
        raise TypeError("reason_id must be a string")
    if on_behalf_of_content_owner is not None and not isinstance(on_behalf_of_content_owner, str):
        raise TypeError("on_behalf_of_content_owner must be a string")
    if secondary_reason_id is not None and not isinstance(secondary_reason_id, str):
        raise TypeError("secondary_reason_id must be a string")
    if comments is not None and not isinstance(comments, str):
        raise TypeError("comments must be a string")
    if language is not None and not isinstance(language, str):
        raise TypeError("language must be a string")
    if not video_id:
        raise ValueError("video_id is required")
    if video_id not in DB["videos"]:
         raise ValueError("Video not found")

    # Ensure the abuse_reports list exists
    if "abuse_reports" not in DB:
        DB["abuse_reports"] = []

    # Record the abuse report
    report = {
        "video_id": video_id,
        "reason_id": reason_id,
        "on_behalf_of_content_owner": on_behalf_of_content_owner,
        "secondary_reason_id": secondary_reason_id,
        "comments":comments,
        "language": language,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    DB["abuse_reports"].append(report)

    return {"success": True}

@tool_spec(
    spec={
    "name": "delete_video",
    "description": "Deletes a video from the database.",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The ID of the video to delete."
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "The ID of the content owner on whose behalf the deletion is being made. This parameter is currently ignored in the simulation. Defaults to None."
            }
        },
        "required": [
            "id"
        ]
    }
}
)
def delete(id: str, on_behalf_of_content_owner: Optional[str] = None) -> Dict[str, bool]:
    """Deletes a video from the database.
    Args:
        id (str): The ID of the video to delete.
        on_behalf_of_content_owner (Optional[str]): The ID of the content owner on whose behalf the deletion is being made. 
                                                   This parameter is currently ignored in the simulation. Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary indicating success of the operation:
            - success (bool): True if deletion was successful.

    Raises:
        InvalidVideoIdError: If the video ID is not provided, is not a string, or is an empty string.
        VideoIdNotFoundError: If the video with the specified ID is not found in the database.
    """
    # Input validation
    if not id or id.strip() == "":
        raise InvalidVideoIdError("Video ID is required.")
    if id not in DB["videos"]:
        raise VideoIdNotFoundError("Video not found.")

    del DB["videos"][id]
    return {"success": True}


@tool_spec(
    spec={
    "name": "update_video_metadata",
    "description": "Updates a video.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API request is setting. Must be a comma-separated list containing one or more of: 'snippet', 'status', 'statistics'."
            },
            "body": {
                "type": "object",
                "description": "The video resource to update. Consists of the following keys - ",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The ID of the video to update."
                    },
                    "snippet": {
                        "type": "object",
                        "description": "The snippet of the video to update.",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The title of the video."
                            },
                            "description": {
                                "type": "string",
                                "description": "The description of the video."
                            },
                            "thumbnails": {
                                "type": "object",
                                "description": "The thumbnails of the video.",
                                "properties": {
                                    "default": {
                                        "type": "object",
                                        "description": "The default thumbnail of the video.",
                                        "properties": {
                                            "url": {
                                                "type": "string",
                                                "description": "The URL of the default thumbnail."
                                            },
                                            "width": {
                                                "type": "integer",
                                                "description": "The width of the default thumbnail."
                                            },
                                            "height": {
                                                "type": "integer",
                                                "description": "The height of the default thumbnail."
                                            }
                                        },
                                        "required":[]
                                    },
                                    "medium": {
                                        "type": "object",
                                        "description": "The medium thumbnail of the video.",
                                        "properties": {
                                            "url": {
                                                "type": "string",
                                                "description": "The URL of the medium thumbnail."
                                            },
                                            "width": {
                                                "type": "integer",
                                                "description": "The width of the medium thumbnail."
                                            },
                                            "height": {
                                                "type": "integer",
                                                "description": "The height of the medium thumbnail."
                                            }
                                        },
                                        "required": []
                                    },
                                    "high": {
                                        "type": "object",
                                        "description": "The high thumbnail of the video.",
                                        "properties": {
                                            "url": {
                                                "type": "string",
                                                "description": "The URL of the high thumbnail."
                                            },
                                            "width": {
                                                "type": "integer",
                                                "description": "The width of the high thumbnail."
                                            },
                                            "height": {
                                                "type": "integer",
                                                "description": "The height of the high thumbnail."
                                            }
                                        },
                                        "required": []
                                    }
                                },
                                "required": []
                            },
                        },
                        "required": []
                    },
                    "status": {
                        "type": "object",
                        "description": "The status of the video to upload.",
                        "properties": {
                            "uploadStatus": {
                                "type": "string",
                                "description": "The upload status of the video. Must be one of ['processed', 'failed', 'rejected', 'uploaded', 'deleted']."
                            },
                            "privacyStatus": {
                                "type": "string",
                                "description": "The privacy status of the video. Must be one of ['public', 'unlisted', 'private']."
                            },
                            "embeddable": {
                                "type": "boolean",
                                "description": "Whether the video is embeddable."
                            },
                            "madeForKids": {
                                "type": "boolean",
                                "description": "Whether the video is made for kids."
                            }
                        },
                        "required": []
                    },
                    "statistics": {
                        "type": "object",
                        "description": "The statistics of the video to update.",
                        "properties": {
                            "viewCount": {
                                "type": "integer",
                                "description": "The view count of the video."
                            },
                            "likeCount": {
                                "type": "integer",
                                "description": "The like count of the video."
                            },
                            "dislikeCount": {
                                "type": "integer",
                                "description": "The dislike count of the video."
                            },
                            "favoriteCount": {
                                "type": "integer",
                                "description": "The favorite count of the video."
                            }
                        },
                        "required": []
                    }
                },
                "required": [
                    "id"
                ]
            }
        },
        "required": [
            "part",
            "body"
        ]
    }
}
)
def update(
    part: str,
    body: Dict[str, Union[str, Dict[str, Dict[str, Union[str, int]]], Dict[str, Union[str, bool]],Dict[str, int]]]
) -> Dict[str, Union[str, Dict[str, Dict[str, Union[str, int]]], Dict[str, Union[str, bool]],Dict[str, int]]]:
    """Updates a video.

    Args:
        part (str): The part parameter specifies the properties of the record that the API request is setting. Must be a comma-separated list containing one or more of: 'snippet', 'status', 'statistics'.
        body (Dict[str, Union[str, Dict[str, Dict[str, Union[str, int]]], Dict[str, Union[str, bool]],Dict[str, int]]]): The video resource to update. Consists of the following keys -
            - id (str): The ID of the video to update.
            - snippet Optional(Dict[str, Union[str, Dict[str, Union[str, int]]]]): The snippet of the video to update.
                - title Optional(str): The title of the video.
                - description Optional(str): The description of the video.
                - thumbnails Optional(Dict[str, Dict[str, Union[str, int]]]): The thumbnails of the video.
                    - default Optional(Dict[str, Union[str, int]]): The default thumbnail of the video.
                        - url Optional(str): The URL of the default thumbnail.
                        - width Optional(int): The width of the default thumbnail.
                        - height Optional(int): The height of the default thumbnail.
                    - medium Optional(Dict[str, Union[str, int]]): The medium thumbnail of the video.
                        - url Optional(str): The URL of the medium thumbnail.
                        - width Optional(int): The width of the medium thumbnail.
                        - height Optional(int): The height of the medium thumbnail.
                    high Optional(Dict[str, Union[str, int]]): The high thumbnail of the video.
                        - url Optional(str): The URL of the high thumbnail.
                        - width Optional(int): The width of the high thumbnail.
                        - height Optional(int): The height of the high thumbnail.
            - status Optional(Dict[str, Union[str, bool]]): The status of the video to update.
                - uploadStatus Optional(str): The upload status of the video.
                - privacyStatus Optional(str): The privacy status of the video.
                - embeddable Optional(bool): Whether the video is embeddable.
                - madeForKids Optional(bool): Whether the video is made for kids.
            - statistics Optional(Dict[str, int]): The statistics of the video to update.
                - viewCount Optional(int): The view count of the video.
                - likeCount Optional(int): The like count of the video.
                - dislikeCount Optional(int): The dislike count of the video.
                - favoriteCount Optional(int): The favorite count of the video.


    Returns:
        Dict[str, Union[str, Dict[str, Dict[str, Union[str, int]]], Dict[str, Union[str, bool]],Dict[str, int]]]: The updated video resource:
            id (str): The ID of the video.
            snippet (Dict[str, Union[str, Dict[str, Union[str, int]]]]): The snippet of the video.
                - title Optional(str): The title of the video.
                - description Optional(str): The description of the video.
                - thumbnails Optional(Dict[str, Union[str, int]]): The thumbnails of the video.
                    - default Optional(Dict[str, Union[str, int]]): The default thumbnail of the video.
                        - url Optional(str): The URL of the default thumbnail.
                        - width Optional(int): The width of the default thumbnail.
                        - height Optional(int): The height of the default thumbnail.
                    - medium Optional(Dict[str, Union[str, int]]): The medium thumbnail of the video.
                        - url Optional(str): The URL of the medium thumbnail.
                        - width Optional(int): The width of the medium thumbnail.
                        - height Optional(int): The height of the medium thumbnail.
                    high Optional(Dict[str, Union[str, int]]): The high thumbnail of the video.
                        - url Optional(str): The URL of the high thumbnail.
                        - width Optional(int): The width of the high thumbnail.
                        - height Optional(int): The height of the high thumbnail.
            status (Dict[str, Union[str, bool]]): The status of the video.
                - uploadStatus Optional(str): The upload status of the video.
                - privacyStatus Optional(str): The privacy status of the video.
                - embeddable Optional(bool): Whether the video is embeddable.
                - madeForKids Optional(bool): Whether the video is made for kids.
            statistics (Dict[str, int]): The statistics of the video.
                - viewCount Optional(int): The view count of the video.
                - likeCount Optional(int): The like count of the video.
                - dislikeCount Optional(int): The dislike count of the video.
                - favoriteCount Optional(int): The favorite count of the video.

    Raises:
        ValueError: If the 'part' parameter is not provided or is an empty string.
                    or if the 'body' parameter is not provided or does not include the video 'id'.
                    or if the 'part' parameter is not one of the valid parts : ['snippet', 'status', 'statistics'].
                    or if the video with the given id is not found in the database.
        TypeError: If the 'part' parameter is not a string.
        ValidationError: If the 'body' parameter is not of the correct structure as specified in the docstring.
    """
    if not part:
        raise ValueError("The 'part' parameter is required.")
    
    if not isinstance(part, str):
        raise TypeError("The 'part' parameter must be a string.")

    if not body or "id" not in body:
        raise ValueError("The 'body' parameter is required and must include the video 'id'.")

    valid_parts = [
        "snippet",
        "status",
        "statistics",
    ]
    parts_list = [p.strip() for p in part.split(",")]

    for p in parts_list:
        if p not in valid_parts:
            raise ValueError(f"Invalid part parameter, must be one of {valid_parts}")

    video_id = body["id"]
    if video_id not in DB["videos"]:
        raise ValueError(f"Video with given id not found in the database")

    updated_video = DB["videos"][video_id].copy()

    if "snippet" in parts_list:
        try:
            verified_snippet = SnippetUpdateModel(**body["snippet"])
            if "snippet" not in updated_video:
                updated_video["snippet"] = {}
            for key, value in verified_snippet.model_dump().items():
                updated_video["snippet"][key] = value
        except ValidationError as e:
            raise ValueError(f"Invalid snippet structure")

    if "status" in parts_list:
        try:
            verified_status = StatusUpdateModel(**body["status"])
            if "status" not in updated_video:
                updated_video["status"] = {}
            for key, value in verified_status.model_dump().items():
                updated_video["status"][key] = value
        except ValidationError as e:
            raise ValueError(f"Invalid status structure")

    if "statistics" in parts_list:
        try:
            verified_statistics = StatisticsUpdateModel(**body["statistics"])
            if "statistics" not in updated_video:
                updated_video["statistics"] = {}
            for key, value in verified_statistics.model_dump().items():
                updated_video["statistics"][key] = value
        except ValidationError as e:
            raise ValueError(f"Invalid statistics structure")

    DB["videos"][video_id] = updated_video
    return updated_video

@tool_spec(
    spec={
    "name": "upload_video",
    "description": "Uploads a video.",
    "parameters": {
        "type": "object",
        "properties": {
            "body": {
                "type": "object",
                "description": "The video resource to upload.",
                "properties": {
                    "snippet": {
                        "type": "object",
                        "description": "The snippet of the video to upload.",
                        "properties": {
                            "channelId": {
                                "type": "string",
                                "description": "The ID of the channel that the video is uploaded to."
                            },
                            "title": {
                                "type": "string",
                                "description": "The title of the video."
                            },
                            "description": {
                                "type": "string",
                                "description": "The description of the video."
                            },
                            "thumbnails": {
                                "type": "object",
                                "description": "The thumbnails of the video.",
                                "properties": {
                                    "default": {
                                        "type": "object",
                                        "description": "The default thumbnail of the video.",
                                        "properties": {
                                            "url": {
                                                "type": "string",
                                                "description": "The URL of the default thumbnail."
                                            },
                                            "width": {
                                                "type": "integer",
                                                "description": "The width of the default thumbnail."
                                            },
                                            "height": {
                                                "type": "integer",
                                                "description": "The height of the default thumbnail."
                                            }
                                        },
                                        "required": [
                                            "url",
                                            "width",
                                            "height"
                                        ]
                                    },
                                    "medium": {
                                        "type": "object",
                                        "description": "The medium thumbnail of the video.",
                                        "properties": {
                                            "url": {
                                                "type": "string",
                                                "description": "The URL of the medium thumbnail."
                                            },
                                            "width": {
                                                "type": "integer",
                                                "description": "The width of the medium thumbnail."
                                            },
                                            "height": {
                                                "type": "integer",
                                                "description": "The height of the medium thumbnail."
                                            }
                                        },
                                        "required": [
                                            "url",
                                            "width",
                                            "height"
                                        ]
                                    },
                                    "high": {
                                        "type": "object",
                                        "description": "The high thumbnail of the video.",
                                        "properties": {
                                            "url": {
                                                "type": "string",
                                                "description": "The URL of the high thumbnail."
                                            },
                                            "width": {
                                                "type": "integer",
                                                "description": "The width of the high thumbnail."
                                            },
                                            "height": {
                                                "type": "integer",
                                                "description": "The height of the high thumbnail."
                                            }
                                        },
                                        "required": [
                                            "url",
                                            "width",
                                            "height"
                                        ]
                                    }
                                },
                                "required": [
                                    "default",
                                    "medium",
                                    "high"
                                ]
                            },
                            "channelTitle": {
                                "type": "string",
                                "description": "The title of the channel that the video is uploaded to."
                            },
                            "tags": {
                                "type": "array",
                                "description": "The tags of the video.",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "categoryId": {
                                "type": "string",
                                "description": "The ID of the category that the video belongs to."
                            }
                        },
                        "required": [
                            "channelId",
                            "title",
                            "description",
                            "thumbnails",
                            "channelTitle",
                            "tags",
                            "categoryId"
                        ]
                    },
                    "status": {
                        "type": "object",
                        "description": "The status of the video to upload.",
                        "properties": {
                            "uploadStatus": {
                                "type": "string",
                                "description": "The upload status of the video. Must be one of ['processed', 'failed', 'rejected', 'uploaded', 'deleted']."
                            },
                            "privacyStatus": {
                                "type": "string",
                                "description": "The privacy status of the video. Must be one of ['public', 'unlisted', 'private']."
                            },
                            "embeddable": {
                                "type": "boolean",
                                "description": "Whether the video is embeddable."
                            },
                            "madeForKids": {
                                "type": "boolean",
                                "description": "Whether the video is made for kids."
                            }
                        },
                        "required": [
                            "uploadStatus",
                            "privacyStatus",
                            "embeddable",
                            "madeForKids"
                        ]
                    }
                },
                "required": [
                    "snippet",
                    "status"
                ]
            }
        },
        "required": [
            "body"
        ]
    }
}
)
def upload(
    body: Dict[str, Union[Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]], Dict[str, Union[str, bool]]]]
) -> Dict[str, Union[str, Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]], Dict[str, Union[str, bool]],Dict[str, int]]]:
    """Uploads a video.
    Args:
        body (Dict[str, Union[Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]], Dict[str, Union[str, bool]]]]): The video resource to upload.
            snippet (Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]]): The snippet of the video to upload.
                channelId (str): The ID of the channel that the video is uploaded to.
                title (str): The title of the video.
                description (str): The description of the video.
                thumbnails (Dict[str, Dict[str, Union[str, int]]]): The thumbnails of the video.
                    default (Dict[str, Union[str, int]]): The default thumbnail of the video.
                        url (str): The URL of the default thumbnail.
                        width (int): The width of the default thumbnail.
                        height (int): The height of the default thumbnail.
                    medium (Dict[str, Union[str, int]]): The medium thumbnail of the video.
                        url (str): The URL of the medium thumbnail.
                        width (int): The width of the medium thumbnail.
                        height (int): The height of the medium thumbnail.
                    high (Dict[str, Union[str, int]]): The high thumbnail of the video.
                        url (str): The URL of the high thumbnail.
                        width (int): The width of the high thumbnail.
                        height (int): The height of the high thumbnail.
                channelTitle (str): The title of the channel that the video is uploaded to.
                tags (List[str]): The tags of the video.
                categoryId (str): The ID of the category that the video belongs to.
            status (Dict[str, Union[str, bool]]): The status of the video to upload.
                uploadStatus (str): The upload status of the video. Must be one of ['processed', 'failed', 'rejected', 'uploaded', 'deleted'].
                privacyStatus (str): The privacy status of the video. Must be one of ['public', 'unlisted', 'private'].
                embeddable (bool): Whether the video is embeddable.
                madeForKids (bool): Whether the video is made for kids.
        
    Returns:
        Dict[str, Union[str, Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]], Dict[str, Union[str, bool]],Dict[str, int]]]: The uploaded video resource:
            id (str): The ID of the video.
            snippet (Dict[str, Union[str, List[str], Dict[str, Union[str, int]]]]): The snippet of the video.
                publishedAt (str): The date and time the video was published.
                channelId (str): The ID of the channel that the video is uploaded to.
                title (str): The title of the video.
                description (str): The description of the video.
                thumbnails (Dict[str, Dict[str, Union[str, int]]]): The thumbnails of the video.
                    default (Dict[str, Union[str, int]]): The default thumbnail of the video.
                        url (str): The URL of the default thumbnail.
                        width (int): The width of the default thumbnail.
                        height (int): The height of the default thumbnail.
                    medium (Dict[str, Union[str, int]]): The medium thumbnail of the video.
                        url (str): The URL of the medium thumbnail.
                        width (int): The width of the medium thumbnail.
                        height (int): The height of the medium thumbnail.
                    high (Dict[str, Union[str, int]]): The high thumbnail of the video.
                        url (str): The URL of the high thumbnail.
                        width (int): The width of the high thumbnail.
                        height (int): The height of the high thumbnail.
                channelTitle (str): The title of the channel that the video is uploaded to.
                tags (List[str]): The tags of the video.
                categoryId (str): The ID of the category that the video belongs to.
            status (Dict[str, Union[str, bool]]): The status of the video.
                uploadStatus (str): The upload status of the video.
                privacyStatus (str): The privacy status of the video.
                embeddable (bool): Whether the video is embeddable.
                madeForKids (bool): Whether the video is made for kids.
            statistics (Dict[str, int]): The statistics of the video.
                viewCount (int): The view count of the video.
                likeCount (int): The like count of the video.
                commentCount (int): The comment count of the video.
                favoriteCount (int): The favorite count of the video.
    Raises:
        ValueError: If the 'body' parameter is not provided
                    or if the channel_id is not found in the database.
                    or if the category_id is not found in the database.
                    or if the channel_title does not match the channel title in the DB.
                    or if the upload status is not one of ['processed', 'failed', 'rejected', 'uploaded', 'deleted'].
                    or if the privacy status is not one of ['public', 'unlisted', 'private'].
        TypeError: If the 'body' parameter is not a dictionary.
        ValidationError: If the 'body' parameter is not of the correct structure as specified in the docstring.
    """

    if not body:
        raise ValueError("The 'body' parameter is required.")

    if not isinstance(body, dict):
        raise TypeError("The 'body' parameter must be a dictionary.") 

    try:
        verified_video = VideoUploadModel(**body)
    except ValidationError as e:
        raise 

    channels = DB.get("channels", {})
    if body["snippet"]["channelId"] not in channels:
        raise ValueError("Channel not found")

    categories = DB.get("videoCategories", {})
    if body["snippet"]["categoryId"] not in categories:
        raise ValueError("Category not found")

    channel_title = channels[body["snippet"]["channelId"]]["forUsername"]
    if channel_title != body["snippet"]["channelTitle"]:
        raise ValueError("Channel title does not match the channel title in the DB.")

    if body["status"]["uploadStatus"] not in ["processed", "failed", "rejected", "uploaded", "deleted"]:
        raise ValueError("Invalid upload status")

    if body["status"]["privacyStatus"] not in ["public", "unlisted", "private"]:
        raise ValueError("Invalid privacy status")

    video_id = generate_entity_id(entity_type='video')

    if "videos" not in DB:
        DB["videos"] = {}   

    new_video = { "id": video_id }

    for key, value in verified_video.model_dump().items():
        new_video[key] = value

    new_video["snippet"]["publishedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    new_video["statistics"] = {
        "viewCount": 0,
        "likeCount": 0,
        "commentCount": 0,
        "favoriteCount": 0,
    }

    DB["videos"][video_id] = new_video
    return new_video
