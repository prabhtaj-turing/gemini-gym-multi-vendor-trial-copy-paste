from common_utils.tool_spec_decorator import tool_spec
# APIs/tiktokApi/Business/Video/Publish/__init__.py
import uuid
from typing import Optional, Dict, List, Union
from pydantic import ValidationError
from tiktok.SimulationEngine.db import DB
from tiktok.SimulationEngine.models import PostInfo


@tool_spec(
    spec={
        'name': 'publish_business_video',
        'description': """ Publish a public video post to a TikTok account.
        
        This endpoint allows you to upload and publish a video to your TikTok account with various
        customization options for the post's visibility and interaction settings. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'access_token': {
                    'type': 'string',
                    'description': 'Access token authorized by TikTok creators.'
                },
                'content_type': {
                    'type': 'string',
                    'description': 'Must be "application/json".'
                },
                'business_id': {
                    'type': 'string',
                    'description': 'Application specific unique identifier for the TikTok account.'
                },
                'video_url': {
                    'type': 'string',
                    'description': 'URL of the video to be published.'
                },
                'post_info': {
                    'type': 'object',
                    'description': 'Additional information about the post.',
                    'properties': {
                        'title': {
                            'type': 'string',
                            'description': 'Title of the video.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'Description of the video.'
                        },
                        'tags': {
                            'type': 'array',
                            'description': 'List of tags for the video.',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'thumbnail_url': {
                            'type': 'string',
                            'description': 'URL of the thumbnail for the video.'
                        },
                        'thumbnail_offset': {
                            'type': 'integer',
                            'description': 'Time offset in seconds for video thumbnail.'
                        },
                        'is_ai_generated': {
                            'type': 'boolean',
                            'description': 'Whether the content is AI-generated.'
                        }
                    },
                    'required': [
                        'title',
                        'description',
                        'tags',
                        'thumbnail_url',
                        'thumbnail_offset',
                        'is_ai_generated'
                    ]
                },
                'caption': {
                    'type': 'string',
                    'description': 'Caption text for the video. Defaults to None.'
                },
                'is_brand_organic': {
                    'type': 'boolean',
                    'description': 'Whether the post is organic branded content. Defaults to False.'
                },
                'is_branded_content': {
                    'type': 'boolean',
                    'description': 'Whether the post is branded content. Defaults to False.'
                },
                'disable_comment': {
                    'type': 'boolean',
                    'description': 'Whether to disable comments. Defaults to False.'
                },
                'disable_duet': {
                    'type': 'boolean',
                    'description': 'Whether to disable duet feature. Defaults to False.'
                },
                'disable_stitch': {
                    'type': 'boolean',
                    'description': 'Whether to disable stitch feature. Defaults to False.'
                },
                'upload_to_draft': {
                    'type': 'boolean',
                    'description': 'Whether to save as draft instead of publishing. Defaults to False.'
                }
            },
            'required': [
                'access_token',
                'content_type',
                'business_id',
                'video_url',
                'post_info'
            ]
        }
    }
)
def post(
    access_token: str,
    content_type: str,
    business_id: str,
    video_url: str,
    post_info: Dict[str, Union[str, List[str], int, bool]],
    caption: Optional[str] = None,
    is_brand_organic: Optional[bool] = False,
    is_branded_content: Optional[bool] = False,
    disable_comment: Optional[bool] = False,
    disable_duet: Optional[bool] = False,
    disable_stitch: Optional[bool] = False,
    upload_to_draft: Optional[bool] = False,
) -> Dict[str, Union[int, str, Dict[str, Union[str, List[str], int, bool]]]]:
    """
    Publish a public video post to a TikTok account.

    This endpoint allows you to upload and publish a video to your TikTok account with various
    customization options for the post's visibility and interaction settings.

    Args:
        access_token (str): Access token authorized by TikTok creators.
        content_type (str): Must be "application/json".
        business_id (str): Application specific unique identifier for the TikTok account.
        video_url (str): URL of the video to be published.
        post_info (Dict[str, Union[str, List[str], int, bool]]): Additional information about the post.
            - title (str): Title of the video.
            - description (str): Description of the video.
            - tags (List[str]): List of tags for the video.
            - thumbnail_url (str): URL of the thumbnail for the video.
            - thumbnail_offset (int): Time offset in seconds for video thumbnail.
            - is_ai_generated (bool): Whether the content is AI-generated.
        caption (Optional[str]): Caption text for the video. Defaults to None.
        is_brand_organic (Optional[bool]): Whether the post is organic branded content. Defaults to False.
        is_branded_content (Optional[bool]): Whether the post is branded content. Defaults to False.
        disable_comment (Optional[bool]): Whether to disable comments. Defaults to False.
        disable_duet (Optional[bool]): Whether to disable duet feature. Defaults to False.
        disable_stitch (Optional[bool]): Whether to disable stitch feature. Defaults to False.
        upload_to_draft (Optional[bool]): Whether to save as draft instead of publishing. Defaults to False.

    Returns:
        Dict[str, Union[int, str, Dict[str, Union[str, List[str], int, bool]]]]: A dictionary containing:
            - code (int): HTTP status code (200 for success)
            - message (str): Status message describing the result
            - request_id (str): Unique identifier for the request
            - data (Dict[str, Union[str, List[str], int, bool]]): Publishing information containing:
                - share_id (str): Unique identifier for the published video
                - title (str): Title of the video
                - description (str): Description of the video
                - tags (List[str]): List of tags for the video
                - thumbnail_url (str): URL of the thumbnail
                - thumbnail_offset (int): Time offset for thumbnail
                - is_ai_generated (bool): Whether content is AI-generated
                - caption (Optional[str]): Caption text
                - is_brand_organic (bool): Whether organic branded content
                - is_branded_content (bool): Whether branded content
                - disable_comment (bool): Whether comments disabled
                - disable_duet (bool): Whether duet disabled
                - disable_stitch (bool): Whether stitch disabled
                - upload_to_draft (bool): Whether saved as draft

    Raises:
        TypeError: If any of the required parameters are not the correct type -
                    access_token, content_type, business_id, video_url, caption are not strings,
                    post_info is not a dictionary,
                    is_brand_organic, is_branded_content, disable_comment, disable_duet, disable_stitch, upload_to_draft are not booleans.
        ValueError: If any of the required parameters are missing or empty -
                    access_token, content_type, business_id, video_url, post_info are not provided,
                    or content_type is not "application/json",
                    or access_token, business_id, video_url, caption(if provided) are empty.
        ValidationError: If post_info is not in the mentioned format and fails the pydantic validation.
    """
    # Validate required parameters
    if not access_token:
        raise ValueError("Access-Token is required")
    if not isinstance(access_token, str):   
        raise TypeError("Access-Token must be a string")
    if not access_token.strip():
        raise ValueError("Access-Token must be a non-empty string")

    if not content_type:
        raise ValueError("Content-Type is required")
    if not isinstance(content_type, str):
        raise TypeError("Content-Type must be a string")
    if content_type != "application/json":
        raise ValueError("Content-Type must be application/json")

    if not business_id:
        raise ValueError("business_id is required")
    if not isinstance(business_id, str):
        raise TypeError("business_id must be a string")
    if not business_id.strip():
        raise ValueError("business_id must be a non-empty string")

    if not video_url:
        raise ValueError("video_url is required")
    if not isinstance(video_url, str):
        raise TypeError("video_url must be a string")
    if not video_url.strip():
        raise ValueError("video_url must be a non-empty string")

    if post_info is None:
        raise ValueError("post_info is required")

    if not isinstance(post_info, dict):
        raise TypeError("post_info must be a dictionary")

    # Validate post_info using pydantic
    try:
        validated_post_info = PostInfo(**post_info)
    except ValidationError as e:
        raise e

    # Validate optional parameters
    if caption is not None and not isinstance(caption, str):
        raise TypeError("caption must be a string")
        if not caption.strip():
            raise ValueError("caption must be a non-empty string")


    if is_brand_organic is not None and not isinstance(is_brand_organic, bool):
        raise TypeError("is_brand_organic must be a boolean")

    if is_branded_content is not None and not isinstance(is_branded_content, bool):
        raise TypeError("is_branded_content must be a boolean")

    if disable_comment is not None and not isinstance(disable_comment, bool):
        raise TypeError("disable_comment must be a boolean")

    if disable_duet is not None and not isinstance(disable_duet, bool):
        raise TypeError("disable_duet must be a boolean")

    if disable_stitch is not None and not isinstance(disable_stitch, bool):
        raise TypeError("disable_stitch must be a boolean")

    if upload_to_draft is not None and not isinstance(upload_to_draft, bool):
        raise TypeError("upload_to_draft must be a boolean")

    # Simulate video publishing with actual parameter usage
    share_id = "v_pub_url~" + str(uuid.uuid4())
    
    # Create response data incorporating the validated parameters
    response_data = {
        "share_id": share_id,
        "title": validated_post_info.title,
        "description": validated_post_info.description,
        "tags": validated_post_info.tags,
        "thumbnail_url": validated_post_info.thumbnail_url,
        "thumbnail_offset": validated_post_info.thumbnail_offset,
        "is_ai_generated": validated_post_info.is_ai_generated,
        "caption": caption,
        "is_brand_organic": is_brand_organic,
        "is_branded_content": is_branded_content,
        "disable_comment": disable_comment,
        "disable_duet": disable_duet,
        "disable_stitch": disable_stitch,
        "upload_to_draft": upload_to_draft
    }
    
    return {
        "code": 200,
        "message": "OK",
        "request_id": str(uuid.uuid4()),
        "data": response_data,
    }
