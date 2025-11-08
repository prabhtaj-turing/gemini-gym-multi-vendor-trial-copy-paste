from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
from typing import Dict, Any, Optional, Union, List

from pydantic import ValidationError
from datetime import datetime
from .SimulationEngine.models import (
    CreatePostPayload,
    CreatePostResponse,
    UpdatePostPayload,
    UpdatePostRequest,
)
from .SimulationEngine.db import DB
from common_utils.error_handling import handle_api_errors
from .SimulationEngine.custom_errors import PostNotFoundError

"""
API simulation for the '/posts' resource.
"""


@tool_spec(
    spec={
        "name": "create_post",
        "description": "Creates a LinkedIn UGC (User Generated Content) Post. This endpoint allows you to publish new UGC posts containing commentary, media content, optional call-to-action labels, and visibility restrictions. It supports both organic and ad-related content.",
        "parameters": {
            "type": "object",
            "properties": {
                "post_data": {
                    "type": "object",
                    "description": "Dictionary containing UGC (User Generated Content) post fields.",
                    "properties": {
                        "author": {
                            "type": "string",
                            "description": "Uniform Resource Name of the post's author. Must be a Person or Organization Uniform Resource Name.",
                        },
                        "commentary": {
                            "type": "string",
                            "description": "User-generated commentary text for the post.",
                        },
                        "distribution": {
                            "type": "object",
                            "description": "Distribution settings, required.",
                            "properties": {
                                "feedDistribution": {
                                    "type": "string",
                                    "description": "Where to distribute. One of: 'MAIN_FEED', 'NONE'",
                                },
                                "targetEntities": {
                                    "type": "array",
                                    "description": "Targeting facets like geoLocations, industries, etc.",
                                    "items": {
                                        "type": "object",
                                        "properties": {},
                                        "required": [],
                                    },
                                },
                                "thirdPartyDistributionChannels": {
                                    "type": "array",
                                    "description": "External platforms.",
                                    "items": {
                                        "type": "object",
                                        "properties": {},
                                        "required": [],
                                    },
                                },
                            },
                            "required": ["feedDistribution"],
                        },
                        "lifecycleState": {
                            "type": "string",
                            "description": "Content lifecycle state. Must be PUBLISHED for creation. One of: 'DRAFT', 'PUBLISHED', 'PUBLISH_REQUESTED', 'PUBLISH_FAILED'",
                        },
                        "visibility": {
                            "type": "string",
                            "description": "Member network visibility. One of: 'CONNECTIONS', 'PUBLIC', 'LOGGED_IN', 'CONTAINER'",
                        },
                        "contentLandingPage": {
                            "type": "string",
                            "description": "URL opened when the member clicks on the content. Required if the campaign creative has the `WEBSITE_VISIT` objective.",
                        },
                        "adContext": {
                            "type": "object",
                            "description": "Advertising metadata for ads or viral tracking.",
                            "properties": {
                                "dscAdAccount": {
                                    "type": "string",
                                    "description": "Sponsored Account Uniform Resource Name. The Ad Account that created the Direct Sponsored Content (DSC). Required when `isDsc` is true; optional otherwise.",
                                },
                                "dscAdType": {
                                    "type": "string",
                                    "description": "Type of the DSC. Required when `isDsc` is true; optional otherwise. One of: 'VIDEO', 'STANDARD', 'CAROUSEL', 'JOB_POSTING', 'NATIVE_DOCUMENT', 'EVENT'",
                                },
                                "dscName": {
                                    "type": "string",
                                    "description": "Plain text name of the DSC post.",
                                },
                                "dscStatus": {
                                    "type": "string",
                                    "description": "The status of the advertising company content. Required when `isDsc` is true; optional otherwise. One of: 'ACTIVE', 'ARCHIVED'",
                                },
                                "isDsc": {
                                    "type": "boolean",
                                    "description": "Whether or not this post is DSC. A posted DSC is created for the sole purpose of sponsorship.",
                                },
                                "objective": {
                                    "type": "string",
                                    "description": "Campaign objective (e.g., 'WEBSITE_VISIT'). When set to 'WEBSITE_VISIT', contentLandingPage becomes required.",
                                },
                            },
                            "required": [],
                        },
                        "container": {
                            "type": "string",
                            "description": "Uniform Resource Name of the container entity holding the post.",
                        },
                        "content": {
                            "type": "object",
                            "description": "Media content details.",
                            "properties": {
                                "media": {
                                    "type": "object",
                                    "description": "Embedded media.",
                                    "properties": {
                                        "id": {
                                            "type": "string",
                                            "description": "Uniform Resource Name of the media asset.",
                                        },
                                        "title": {
                                            "type": "string",
                                            "description": "Title of the media.",
                                        },
                                        "altText": {
                                            "type": "string",
                                            "description": "Accessible text for the media.",
                                        },
                                    },
                                    "required": ["id", "title"],
                                },
                                "poll": {
                                    "type": "object",
                                    "description": "Poll content (refer to Poll API).",
                                    "properties": {
                                        "question": {
                                            "type": "string",
                                            "description": "Question of the poll.",
                                        },
                                        "settings": {
                                            "type": "object",
                                            "description": "Settings of the poll.",
                                            "properties": {
                                                "voteSelectionType": {
                                                    "type": "object",
                                                    "description": "Type of vote selection.",
                                                    "properties": {},
                                                    "required": [],
                                                },
                                                "duration": {
                                                    "type": "string",
                                                    "description": "Duration of the poll. One of: ONE_DAY, THREE_DAYS, SEVEN_DAYS, FOURTEEN_DAYS",
                                                },
                                                "isVoterVisibleToAuthor": {
                                                    "type": "object",
                                                    "description": "Whether the voter is visible to the author.",
                                                    "properties": {},
                                                    "required": [],
                                                },
                                            },
                                            "required": [
                                                "voteSelectionType",
                                                "duration",
                                                "isVoterVisibleToAuthor",
                                            ],
                                        },
                                        "options": {
                                            "type": "array",
                                            "description": "Options of the poll.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "text": {
                                                        "type": "string",
                                                        "description": "Text of the option.",
                                                    }
                                                },
                                                "required": ["text"],
                                            },
                                        },
                                    },
                                    "required": ["options"],
                                },
                                "multiImage": {
                                    "type": "object",
                                    "description": "Multi-image post (refer to MultiImage API).",
                                    "properties": {
                                        "images": {
                                            "type": "array",
                                            "description": "Images of the multi-image post.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "string",
                                                        "description": "Uniform Resource Name of the image asset.",
                                                    },
                                                    "title": {
                                                        "type": "string",
                                                        "description": "Title of the image.",
                                                    },
                                                    "altText": {
                                                        "type": "string",
                                                        "description": "Accessible text for the image.",
                                                    },
                                                },
                                                "required": ["id", "title"],
                                            },
                                        },
                                        "altText": {
                                            "type": "string",
                                            "description": "Accessible text for the multi-image post.",
                                        },
                                    },
                                    "required": ["images"],
                                },
                                "article": {
                                    "type": "object",
                                    "description": "Article content.",
                                    "properties": {
                                        "description": {
                                            "type": "string",
                                            "description": "Description of the article.",
                                        },
                                        "source": {
                                            "type": "string",
                                            "description": "External article URL.",
                                        },
                                        "thumbnail": {
                                            "type": "string",
                                            "description": "Uniform Resource Name of the thumbnail image.",
                                        },
                                        "thumbnailAltText": {
                                            "type": "string",
                                            "description": "Alt text for the custom thumbnail. If empty, there's none. The length must be less than 4,086 characters.",
                                        },
                                        "title": {
                                            "type": "string",
                                            "description": "Custom or saved title of the article.",
                                        },
                                    },
                                    "required": ["source", "title"],
                                },
                                "carousel": {
                                    "type": "object",
                                    "description": "Carousel content.",
                                    "properties": {
                                        "cards": {
                                            "type": "array",
                                            "description": "The array of cards in the carousel.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "landingPage": {
                                                        "type": "string",
                                                        "description": "The URL to the landing page.",
                                                    },
                                                    "media": {
                                                        "type": "object",
                                                        "description": "The media of the card.",
                                                        "properties": {
                                                            "id": {
                                                                "type": "string",
                                                                "description": "Uniform Resource Name of the media asset.",
                                                            },
                                                            "title": {
                                                                "type": "string",
                                                                "description": "Title of the media.",
                                                            },
                                                            "altText": {
                                                                "type": "string",
                                                                "description": "Accessible text for the media.",
                                                            },
                                                        },
                                                        "required": ["id", "title"],
                                                    },
                                                },
                                                "required": ["landingPage", "media"],
                                            },
                                        }
                                    },
                                    "required": ["cards"],
                                },
                                "celebration": {
                                    "type": "object",
                                    "description": "Celebration content.",
                                    "properties": {
                                        "recipient": {
                                            "type": "array",
                                            "description": "The Uniform Resource Name of the recipient.",
                                            "items": {"type": "string"},
                                        },
                                        "taggedEntities": {
                                            "type": "array",
                                            "description": "The Uniform Resource Name of the tagged entities.",
                                            "items": {"type": "string"},
                                        },
                                        "type": {
                                            "type": "string",
                                            "description": "The type of the celebration. One of: 'CELEBRATE_WELCOME', 'CELEBRATE_AWARD', 'CELEBRATE_ANNIVERSARY', 'CELEBRATE_EVENT', 'CELEBRATE_GRADUATION', 'CELEBRATE_JOB_CHANGE', 'CELEBRATE_KUDOS', 'CELEBRATE_LAUNCH', 'CELEBRATE_CAREER_BREAK', 'CELEBRATE_CERTIFICATE', 'CELEBRATE_EDUCATION', 'CELEBRATE_MILESTONE'",
                                        },
                                        "text": {
                                            "type": "string",
                                            "description": "The text of the celebration.",
                                        },
                                        "media": {
                                            "type": "object",
                                            "description": "The media of the celebration.",
                                            "properties": {
                                                "id": {
                                                    "type": "string",
                                                    "description": "Uniform Resource Name of the media asset.",
                                                },
                                                "title": {
                                                    "type": "string",
                                                    "description": "Title of the media.",
                                                },
                                                "altText": {
                                                    "type": "string",
                                                    "description": "Accessible text for the media.",
                                                },
                                            },
                                            "required": ["id", "title"],
                                        },
                                    },
                                    "required": ["type", "media"],
                                },
                                "reference": {
                                    "type": "object",
                                    "description": "Reference content type (e.g., event, appreciation).",
                                    "properties": {
                                        "id": {
                                            "type": "string",
                                            "description": "The Uniform Resource Name of the reference that represents a reference such as an event (e.g. urn:li:reference:123).",
                                        }
                                    },
                                    "required": ["id"],
                                },
                            },
                            "required": [],
                        },
                        "contentCallToActionLabel": {
                            "type": "string",
                            "description": "Call-to-action label displayed on the creative. One of: 'APPLY', 'DOWNLOAD', 'VIEW_QUOTE', 'LEARN_MORE', 'SIGN_UP', 'SUBSCRIBE', 'REGISTER', 'JOIN', 'ATTEND', 'REQUEST_DEMO', 'SEE_MORE', 'BUY_NOW', 'SHOP_NOW'.",
                        },
                        "isReshareDisabledByAuthor": {
                            "type": "boolean",
                            "description": "If True, disables resharing of the post. Default is False.",
                        },
                        "lifecycleStateInfo": {
                            "type": "object",
                            "description": "Additional lifecycle context:",
                            "properties": {
                                "contentStatus": {
                                    "type": "string",
                                    "description": "The status of the content.",
                                },
                                "isEditedByAuthor": {
                                    "type": "boolean",
                                    "description": "Whether the content was edited by the author.",
                                },
                                "reviewStatus": {
                                    "type": "string",
                                    "description": "Review status of the post.",
                                },
                            },
                            "required": [],
                        },
                        "publishedAt": {
                            "type": "integer",
                            "description": "Epoch timestamp when the content was published.",
                        },
                        "reshareContext": {
                            "type": "object",
                            "description": "Context information for re-shares.",
                            "properties": {
                                "parent": {
                                    "type": "string",
                                    "description": "Uniform Resource Name of the direct parent post.",
                                },
                                "root": {
                                    "type": "string",
                                    "description": "Uniform Resource Name of the top-level ancestor post (read-only).",
                                },
                            },
                            "required": [],
                        },
                    },
                    "required": [
                        "author",
                        "commentary",
                        "distribution",
                        "lifecycleState",
                        "visibility",
                    ],
                }
            },
            "required": ["post_data"],
        },
    }
)
def create_post(
    post_data: Dict[
        str,
        Union[
            str,
            int,
            bool,
            Dict[str, Union[str, int, bool]],
            List[Dict[str, Union[str, int, bool]]],
        ],
    ],
) -> Dict[
    str,
    Union[
        str,
        int,
        bool,
        Dict[str, Union[str, int, bool]],
        List[Dict[str, Union[str, int, bool]]],
    ],
]:
    """
    Creates a LinkedIn UGC (User Generated Content) Post. This endpoint allows you to publish new UGC posts containing commentary, media content, optional call-to-action labels, and visibility restrictions. It supports both organic and ad-related content.

    Args:
        post_data (Dict[str, Union[str, int, bool, Dict[str, Union[str, int, bool]], List[Dict[str, Union[str, int, bool]]]]]): Dictionary containing UGC (User Generated Content) post fields.

            author (str): Uniform Resource Name of the post's author. Must be a Person or Organization Uniform Resource Name.
            commentary (str): User-generated commentary text for the post.
            distribution (Dict[str, Union[str, List[Dict[str, Union[str, int, bool]]]]]): Distribution settings, required.
                - feedDistribution (str): Where to distribute. One of: 'MAIN_FEED', 'NONE'
                - targetEntities (Optional[List[Dict[str, List[str]]]]): Targeting facets like geoLocations, industries, etc.
                - thirdPartyDistributionChannels (Optional[List[Dict[str, Union[str, int, bool]]]]): External platforms.
            lifecycleState (str): Content lifecycle state. Must be PUBLISHED for creation. One of: 'DRAFT', 'PUBLISHED', 'PUBLISH_REQUESTED', 'PUBLISH_FAILED'
            visibility (str): Member network visibility. One of: 'CONNECTIONS', 'PUBLIC', 'LOGGED_IN', 'CONTAINER'
            contentLandingPage (Optional[str]): URL opened when the member clicks on the content. Required if the campaign creative has the `WEBSITE_VISIT` objective.
            adContext (Optional[Dict[str, Union[str, bool]]]): Advertising metadata for ads or viral tracking.
                - dscAdAccount (Optional[str]): Sponsored Account Uniform Resource Name. The Ad Account that created the Direct Sponsored Content (DSC). Required when `isDsc` is true; optional otherwise.
                - dscAdType (Optional[str]): Type of the DSC. Required when `isDsc` is true; optional otherwise. One of: 'VIDEO', 'STANDARD', 'CAROUSEL', 'JOB_POSTING', 'NATIVE_DOCUMENT', 'EVENT'
                - dscName (optional[str]): Plain text name of the DSC post.
                - dscStatus (Optional[str]): The status of the advertising company content. Required when `isDsc` is true; optional otherwise. One of: 'ACTIVE', 'ARCHIVED'
                - isDsc (optional[bool]): Whether or not this post is DSC. A posted DSC is created for the sole purpose of sponsorship.
                - objective (Optional[str]): Campaign objective (e.g., 'WEBSITE_VISIT'). When set to 'WEBSITE_VISIT', contentLandingPage becomes required.
            container (Optional[str]): Uniform Resource Name of the container entity holding the post.
            content (Optional[Dict[str, str]]): Media content details.
                - media (Optional[Dict[str, str]]): Embedded media.
                    - id (str): Uniform Resource Name of the media asset.
                    - title (str): Title of the media.
                    - altText (Optional[str]): Accessible text for the media.
                - poll (Optional[Dict]): Poll content (refer to Poll API).
                    - question (Optional[str]): Question of the poll.
                    - settings (Optional[Dict]): Settings of the poll.
                        - voteSelectionType (optional[str]): Type of vote selection.
                        - duration (str): Duration of the poll. One of: ONE_DAY, THREE_DAYS, SEVEN_DAYS, FOURTEEN_DAYS
                        - isVoterVisibleToAuthor (optional[bool]): Whether the voter is visible to the author.
                    - options ([List[Dict]]): Options of the poll.
                        - text (str): Text of the option.
                - multiImage (Optional[Dict]): Multi-image post (refer to MultiImage API).
                    - images (List[Dict]): Images of the multi-image post.
                        - id (str): Uniform Resource Name of the image asset.
                        - title (str): Title of the image.
                        - altText (Optional[str]): Accessible text for the image.
                    - altText (Optional[str]): Accessible text for the multi-image post.
                - article (Optional[Dict[str, str]]): Article content.
                    - description (Optional[str]): Description of the article.
                    - source (str): External article URL.
                    - thumbnail (Optional[str]): Uniform Resource Name of the thumbnail image.
                    - thumbnailAltText (Optional[str]): Alt text for the custom thumbnail. If empty, there's none. The length must be less than 4,086 characters.
                    - title (str): Custom or saved title of the article.
                - carousel (Optional[Dict]): Carousel content.
                    - cards (List[Dict[str, str]]): The array of cards in the carousel.
                        - landingPage (str): The URL to the landing page.
                        - media (Dict[str, str]): The media of the card.
                            - id (str): Uniform Resource Name of the media asset.
                            - title (str): Title of the media.
                            - altText (Optional[str]): Accessible text for the media.
                - celebration (Optional[Dict]): Celebration content.
                    - recipient (Optional[List[str]]): The Uniform Resource Name of the recipient.
                    - taggedEntities (Optional[List[str]]): The Uniform Resource Name of the tagged entities.
                    - type (str): The type of the celebration. One of: 'CELEBRATE_WELCOME', 'CELEBRATE_AWARD', 'CELEBRATE_ANNIVERSARY', 'CELEBRATE_EVENT', 'CELEBRATE_GRADUATION', 'CELEBRATE_JOB_CHANGE', 'CELEBRATE_KUDOS', 'CELEBRATE_LAUNCH', 'CELEBRATE_CAREER_BREAK', 'CELEBRATE_CERTIFICATE', 'CELEBRATE_EDUCATION', 'CELEBRATE_MILESTONE'
                    - text (Optional[str]): The text of the celebration.
                    - media (Dict[str, str]): The media of the celebration.
                        - id (str): Uniform Resource Name of the media asset.
                        - title (str): Title of the media.
                        - altText (Optional[str]): Accessible text for the media.
                - reference (Optional[Dict]): Reference content type (e.g., event, appreciation).
                    - id (str): The Uniform Resource Name of the reference that represents a reference such as an event (e.g. urn:li:reference:123).
            contentCallToActionLabel (Optional[str]): Call-to-action label displayed on the creative. One of: 'APPLY', 'DOWNLOAD', 'VIEW_QUOTE', 'LEARN_MORE', 'SIGN_UP', 'SUBSCRIBE', 'REGISTER', 'JOIN', 'ATTEND', 'REQUEST_DEMO', 'SEE_MORE', 'BUY_NOW', 'SHOP_NOW'.
            isReshareDisabledByAuthor (Optional[bool]): If True, disables resharing of the post. Default is False.
            lifecycleStateInfo (Optional[Dict[str, Union[str, bool]]]): Additional lifecycle context:
                - contentStatus (Optional[str]): The status of the content.
                - isEditedByAuthor (Optional[bool]): Whether the content was edited by the author.
                - reviewStatus (Optional[str]): Review status of the post.
            publishedAt (Optional[int]): Epoch timestamp when the content was published.
            reshareContext (Optional[Dict[str, Union[str, bool]]]): Context information for re-shares.
                - parent (Optional[str]): Uniform Resource Name of the direct parent post.
                - root (Optional[str]): Uniform Resource Name of the top-level ancestor post (read-only).
    Returns:
        Dict[str, Union[str, int, bool, Dict[str, Union[str, int, bool]], List[Dict[str, Union[str, int, bool]]]]]: The created UGC post resource.

        Resource Fields:
            id (str): Unique Uniform Resource Name for the post (ugcPostUrn or shareUrn).
            author (str): Uniform Resource Name of the post's author.
            commentary (str): Post commentary text.
            content (Dict[str, str]): Media content information, if provided.
            createdAt (int): Epoch timestamp of resource creation.
            lastModifiedAt (int): Epoch timestamp of the last modification.
            lifecycleState (str): Current lifecycle state.
            visibility (str): Visibility setting of the post.
            distribution (Dict[str, str]): Distribution configuration.
            adContext (Dict[str, str]), container (str), contentLandingPage (str),
            contentCallToActionLabel (str), isReshareDisabledByAuthor (bool),
            lifecycleStateInfo (Dict[str, str]), publishedAt (int),
            reshareContext (Dict[str, str]): Present only if specified or applicable.

    Notes:
        - lifecycleState must be "PUBLISHED" at creation time.
        - If contentLandingPage is provided, it must be a valid URL.
        - Call-to-action labels "BUY_NOW" and "SHOP_NOW" are supported only in
          API versions 202504 and later.

    Raises:
        TypeError: If 'post_data' is not a dictionary.
        pydantic.ValidationError: If 'post_data' does not conform to the
            required structure (missing keys, incorrect types, invalid
            visibility value, invalid author Uniform Resource Name format).
    """
    # --- Input Type Check ---
    if not isinstance(post_data, dict):
        raise TypeError(
            f"Expected 'post_data' to be a dictionary, but got {type(post_data).__name__}."
        )

    # --- Validate Request ---
    try:
        validated_data = CreatePostPayload(**post_data)
    except ValidationError as e:
        raise e

    # --- Simulate Post Creation ---
    # Use the dedicated counter to ensure unique ID generation
    post_id = f"urn:li:ugcPost:{DB['next_post_id']}"
    # Increment the counter for next post
    DB['next_post_id'] += 1
    now_ms = int(datetime.utcnow().timestamp() * 1000)

    # Create the resource
    post_resource = validated_data.model_dump()
    post_resource.update(
        {
            "id": post_id,
            "createdAt": now_ms,
            "lastModifiedAt": now_ms,
        }
    )

    # Store in DB
    DB["posts"][post_id] = post_resource

    # --- Return Response ---
    # Validate response structure against our response model for consistency
    response_obj = CreatePostResponse(**post_resource)
    return response_obj.model_dump()


@handle_api_errors()
@tool_spec(
    spec={
        "name": "get_post_by_id",
        "description": "Retrieves a LinkedIn UGC (User Generated Content) post by its identifier with optional field projection and pagination.",
        "parameters": {
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "string",
                    "description": "Unique identifier (URN) of the post to retrieve.",
                },
                "projection": {
                    "type": "string",
                    "description": """Field projection syntax to control which fields are returned.
                        - Accepts a comma-separated list of fields (e.g., "id,author,visibility").
                        - Can optionally be enclosed in parentheses (e.g., "(id,author)").
                        - If omitted, all fields are returned.""",
                },
                "start": {
                    "type": "integer",
                    "description": "Starting index for paginated results. Defaults to 0. Must be a non-negative integer.",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of items to return. Defaults to 10. Must be a positive integer.",
                },
            },
            "required": ["post_id"],
        },
    }
)
def get_post(
    post_id: str,
    projection: Optional[str] = None,
    start: Optional[int] = 0,
    count: Optional[int] = 10,
) -> Dict[
    str,
    Union[
        str,
        int,
        bool,
        float,
        Dict[str, Union[str, int, bool, float]],
        List[Union[str, int, bool, float, Dict[str, Union[str, int, bool, float]]]],
    ],
]:
    """
    Retrieve a LinkedIn UGC (User Generated Content) post by its identifier with optional field projection.

    Args:
        post_id (str): Unique identifier of the post to retrieve.
        projection (Optional[str]): Field projection syntax to control which fields are returned.
            - Accepts a comma-separated list of fields (e.g., "id,author,visibility").
            - Can optionally be enclosed in parentheses (e.g., "(id,author)").
            - If omitted, all fields are returned.
            - Defaults to None.
        start (Optional[int]): Starting index for pagination. Defaults to 0. Must be non-negative.
        count (Optional[int]): Number of items to return. Defaults to 10. Must be positive.

    Returns:
        Dict[str, Union[str, int, bool, float, Dict[str, Union[str, int, bool, float]], List[Union[str, int, bool, float, Dict[str, Union[str, int, bool, float]]]]]]: A dictionary containing the retrieved post resource.
            Possible fields include:
                - id (str): Post's unique identifier.
                - author (str): URN of the post author (e.g., 'urn:li:person:1').
                - commentary (str): Post commentary text.
                - visibility (str): One of 'PUBLIC', 'CONNECTIONS', 'LOGGED_IN', 'CONTAINER'.
                - createdAt (int): Epoch timestamp of resource creation.
                - lastModifiedAt (int): Epoch timestamp of last modification.
                - likes (int): Number of likes.
                - tags (List[str]): List of tags associated with the post.
                - meta (Dict[str, Union[str, int, bool, float]]): Metadata such as creation time.

    Raises:
        TypeError:
            - If 'post_id' is not a string.
            - If 'projection' is provided and is not a string.
            - If 'start' is not an integer.
            - If 'count' is not an integer.
        ValueError:
            - If 'post_id' is not in valid URN format (e.g., 'urn:li:ugcPost:1').
            - If 'start' is a negative integer.
            - If 'count' is not a positive integer (i.e., less than or equal to 0).
        KeyError: If 'post_id' is not found in the database.
    """
    # Input validation for post_id
    if not isinstance(post_id, str):
        raise TypeError("post_id must be a string.")
    
    # Validate URN format for post_id
    if not post_id.startswith("urn:li:ugcPost:") or post_id.count(":") != 3:
        raise ValueError(f"post_id must be in URN format (e.g., 'urn:li:ugcPost:1'), but got '{post_id}'.")
    
    # Additional validation for URN structure
    urn_parts = post_id.split(":")
    if len(urn_parts) != 4 or any(not part for part in urn_parts):
        raise ValueError(f"post_id must be in valid URN format (e.g., 'urn:li:ugcPost:1'), but got '{post_id}'.")

    # Input validation for projection
    if projection is not None and not isinstance(projection, str):
        raise TypeError("projection must be a string or None.")

    # Input validation for start
    if not isinstance(start, int):
        raise TypeError("start must be an integer.")
    if start < 0:
        raise ValueError("start must be a non-negative integer.")

    # Input validation for count
    if not isinstance(count, int):
        raise TypeError("count must be an integer.")
    if count <= 0:
        raise ValueError("count must be a positive integer.")

    # Original core functionality
    if post_id not in DB["posts"]:
        raise KeyError("Post not found with id: " + post_id)

    # Simplified return for example; actual projection logic would be more complex
    # and use the 'projection' argument if provided.
    post_data = DB["posts"][post_id]

    # Basic projection handling (conceptual)
    if projection:
        # Example: projection="id,author" or "(id,author)"
        # Actual parsing logic for projection string is not implemented here
        # but this is where it would be used.
        # For this example, we assume if projection is present, we only return specific fields.
        # This is a placeholder for actual projection logic.
        # A real implementation would parse 'projection' and filter 'post_data'.
        # For simplicity, if projection is provided, we return all data,
        # as the focus is on input validation, not projection implementation.

        if "(" in projection or ")" in projection:
            projection = projection.replace("(", "").replace(")", "")
            projection = projection.split(",")
        else:
            projection = projection.split(",")
        post_data = {key: post_data[key] for key in projection}

    return {"data": post_data}


@tool_spec(
    spec={
        "name": "find_posts_by_author",
        "description": "Searches for and lists posts based on the provided author identifier with pagination.",
        "parameters": {
            "type": "object",
            "properties": {
                "author": {
                    "type": "string",
                    "description": 'The identifier of the author (e.g., "urn:li:person:1" or "urn:li:organization:1") used to filter posts.',
                },
                "start": {
                    "type": "integer",
                    "description": "Starting index for pagination. Must be a non-negative integer. Defaults to 0.",
                },
                "count": {
                    "type": "integer",
                    "description": "Maximum number of posts to return. Must be a non-negative integer. Defaults to 10.",
                },
            },
            "required": ["author"],
        },
    }
)
def find_posts_by_author(
    author: str, start: Optional[int] = 0, count: Optional[int] = 10
) -> Dict[str, Any]:
    """
    Searches for and lists posts based on the provided author identifier with pagination.

    Args:
        author (str): The identifier of the author (e.g., "urn:li:person:1" or "urn:li:organization:1") used to filter posts.
            Must be a non-empty string in valid Uniform Resource Name format with exactly 4 parts separated by colons:
            'urn:li:{type}:{identifier}' where {type} is 'person' or 'organization' and {identifier} is non-empty.
        start (Optional[int]): Starting index for pagination. Must be a non-negative integer. Defaults to 0.
        count (Optional[int]): Maximum number of posts to return. Must be a non-negative integer. Defaults to 10.

    Returns:
        Dict[str, Any]:
        - On successful retrieval, returns a dictionary with the following keys and value types:
            - 'data' (List[Dict[str, Any]]): List of post dictionaries with keys:
                - 'id' (str): Post's unique identifier.
                - 'author' (str): Uniform Resource Name of the post author (e.g., 'urn:li:person:1' or 'urn:li:organization:1').
                - 'commentary' (str): Content of the post.
                - 'visibility' (str): Visibility setting of the post (one of 'PUBLIC', 'CONNECTIONS', 'LOGGED_IN', 'CONTAINER').

    Raises:
        TypeError: If 'author' is not a string.
        TypeError: If 'start' is not an integer.
        TypeError: If 'count' is not an integer.
        ValueError: If 'author' is an empty string, whitespace-only, or not in valid Uniform Resource Name format.
            Valid Uniform Resource Name format: 'urn:li:{type}:{identifier}' with exactly 4 parts and no empty parts.
        ValueError: If 'start' is a negative integer.
        ValueError: If 'count' is a negative integer.
        NameError: If the global DB is not defined (runtime environment error).
        Exception: For any other unexpected errors during post retrieval or filtering.
    """
    # --- Input Validation Start ---
    if not isinstance(author, str):
        raise TypeError(
            f"Argument 'author' must be a string, but got {type(author).__name__}."
        )
    if not isinstance(start, int):
        raise TypeError(
            f"Argument 'start' must be an integer, but got {type(start).__name__}."
        )
    if not isinstance(count, int):
        raise TypeError(
            f"Argument 'count' must be an integer, but got {type(count).__name__}."
        )

    # Validate author format (non-empty and URN-like)
    if not author.strip():
        raise ValueError("Argument 'author' cannot be empty or whitespace-only.")

    # Basic URN format validation (starts with 'urn:li:' and has exactly 3 colons)
    if not author.startswith("urn:li:") or author.count(":") != 3:
        raise ValueError(
            f"Argument 'author' must be in valid Uniform Resource Name format (e.g., 'urn:li:person:1'), but got '{author}'."
        )

    # Additional validation: check that URN has exactly 4 parts and none are empty
    urn_parts = author.split(":")
    if len(urn_parts) != 4 or any(not part for part in urn_parts):
        raise ValueError(
            f"Argument 'author' must be in valid Uniform Resource Name format (e.g., 'urn:li:person:1'), but got '{author}'."
        )

    if start < 0:
        raise ValueError(
            f"Argument 'start' must be a non-negative integer, but got {start}."
        )
    if count < 0:
        raise ValueError(
            f"Argument 'count' must be a non-negative integer, but got {count}."
        )
    # --- Input Validation End ---

    # --- Original Core Logic Start ---
    # Assume DB exists and has the expected structure
    # Filter posts based on the provided author identifier.
    try:
        # Note: This part might raise NameError if DB is not defined in the execution scope
        # or other errors depending on DB's structure. Tests focus on validation above.
        filtered_posts = [post for post in DB["posts"].values() if post.get("author") == author]  # type: ignore[name-defined]
        # Apply pagination to the filtered posts.
        paginated_posts = filtered_posts[start : start + count]
        return {"data": paginated_posts}
    except NameError:
        # Handle case where DB is not defined for conceptual completeness,
        # though tests won't reach here if validation fails.
        # Or re-raise if appropriate for the application context.
        print_log("Warning: Global 'DB' is not defined.")
        return {"data": []}
    except Exception as e:
        # Catch potential errors during filtering/slicing if DB exists but is malformed
        print_log(f"An error occurred during post retrieval: {e}")
        # Depending on requirements, might re-raise or return an error structure
        raise  # Re-raise unexpected errors from core logic


@tool_spec(
    spec={
        "name": "update_post",
        "description": "Updates an existing post in the database.",
        "parameters": {
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "string",
                    "description": "Unique identifier of the post to update.",
                },
                "post_data": {
                    "type": "object",
                    "description": "Dictionary containing updated UGC post fields.",
                    "properties": {
                        "commentary": {
                            "type": "string",
                            "description": "User-generated commentary text for the post.",
                        },
                        "lifecycleState": {
                            "type": "string",
                            "description": "Content lifecycle state. Must be 'PUBLISHED' for updates.",
                        },
                        "contentLandingPage": {
                            "type": "string",
                            "description": "URL opened when the member clicks on the content. Required if the campaign creative has the 'WEBSITE_VISIT' objective.",
                        },
                        "adContext": {
                            "type": "object",
                            "description": "The advertising context representing the ads specific metadata (which is related to ads or viral tracking, rendering, etc.), associated with the post.",
                            "properties": {
                                "dscName": {
                                    "type": "string",
                                    "description": "Plain text name of the Direct Sponsored Content post.",
                                },
                                "dscStatus": {
                                    "type": "string",
                                    "description": "The status of the advertising content, indicating whether it's usable as a Direct Sponsored Content.",
                                },
                            },
                            "required": [],
                        },
                        "contentCallToActionLabel": {
                            "type": "string",
                            "description": "Call-to-action label displayed on the creative. One of: 'APPLY', 'DOWNLOAD', 'VIEW_QUOTE', 'LEARN_MORE', 'SIGN_UP', 'SUBSCRIBE', 'REGISTER', 'JOIN', 'ATTEND', 'REQUEST_DEMO', 'SEE_MORE', 'BUY_NOW', 'SHOP_NOW'",
                        },
                    },
                    "required": [],
                },
            },
            "required": ["post_id", "post_data"],
        },
    }
)
def update_post(
    post_id: str, post_data: Dict[str, str]
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Updates an existing post in the database.

    Args:
        post_id (str): Unique identifier of the post to update.
        post_data (Dict[str, str]): Dictionary containing updated UGC post fields.
            - commentary (Optional[str]): User-generated commentary text for the post.
            - lifecycleState (Optional[str]): Content lifecycle state. Must be `"PUBLISHED"` for updates.
            - contentLandingPage (Optional[str]): URL opened when the member clicks on the content.
                Required if the campaign creative has the `WEBSITE_VISIT` objective.
            - adContext (Optional[Dict[str, str]]): The advertising context representing the ads specific metadata
                (which is related to ads or viral tracking, rendering, etc.), associated with the post.
                - dscName (Optional[str]): Plain text name of the Direct Sponsored Content post.
                - dscStatus (Optional[str]): The status of the advertising content, indicating whether it's usable as a Direct Sponsored Content.
            - contentCallToActionLabel (Optional[str]): Call-to-action label displayed on the creative.
                One of:
                `"APPLY"`, `"DOWNLOAD"`, `"VIEW_QUOTE"`, `"LEARN_MORE"`,
                `"SIGN_UP"`, `"SUBSCRIBE"`, `"REGISTER"`, `"JOIN"`,
                `"ATTEND"`, `"REQUEST_DEMO"`, `"SEE_MORE"`, `"BUY_NOW"`, `"SHOP_NOW"`

    Returns:
        Dict[str, Union[str, Dict[str, str]]]: The updated UGC post resource.

        **Resource Fields:**
            - id (str): Unique Uniform Resource Name for the post (ugcPostUrn or shareUrn).
            - author (str): Uniform Resource Name of the post's author.
            - commentary (str): Post commentary text.
            - content (dict): Media content information, if provided.
            - createdAt (int): Epoch timestamp of resource creation.
            - lastModifiedAt (int): Epoch timestamp of the last modification.
            - lifecycleState (str): Current lifecycle state.
            - visibility (str): Visibility setting of the post.
            - distribution (dict): Distribution configuration.
            - adContext, container, contentLandingPage, contentCallToActionLabel,
              isReshareDisabledByAuthor, lifecycleStateInfo, publishedAt, reshareContext:
              Present only if specified or applicable.

    Notes:
        - `lifecycleState` must be `"PUBLISHED"` for updates.
        - If `contentLandingPage` is provided, it must be a valid URL.
        - Call-to-action labels `"BUY_NOW"` and `"SHOP_NOW"` are supported only in API
          versions 202504 and later.
        - The `lastModifiedAt` timestamp will be automatically updated.

    Raises:
        PostNotFoundError: If no post exists with the given 'post_id'.
        ValidationError: If 'post_id' or 'post_data' do not conform to expected formats or types.
    """

    # Validate input payload
    validated_request = UpdatePostRequest(post_id=post_id, post_data=post_data)

    if validated_request.post_id not in DB["posts"]:
        raise PostNotFoundError(f"Post not found with id: {validated_request.post_id}")

    # Apply only fields explicitly provided (patch behavior)
    update_data = validated_request.post_data.model_dump(exclude_unset=True)

    DB["posts"][validated_request.post_id].update(update_data)
    return {"data": DB["posts"][validated_request.post_id]}


@tool_spec(
    spec={
        "name": "delete_post_by_id",
        "description": "Deletes a post from the database.",
        "parameters": {
            "type": "object",
            "properties": {
                "post_id": {
                    "type": "string",
                    "description": "Unique identifier of the post to delete.",
                }
            },
            "required": ["post_id"],
        },
    }
)
def delete_post(post_id: str) -> Dict[str, Any]:
    """
    Deletes a post from the database.

    Args:
        post_id (str): Unique identifier of the post to delete.

    Returns:
        Dict[str, Any]: It returns a dictionary with the following key and value type:
            - status (str): Success message confirming deletion of the post.

    Raises:
        TypeError: If 'post_id' is not a string.
        KeyError: If 'post_id' is not found in the database.
    """
    # --- Start Validation ---
    if not isinstance(post_id, str):
        raise TypeError(
            f"Argument 'post_id' must be a string, but got {type(post_id).__name__}."
        )
    # --- End Validation ---

    # Original function logic (remains unchanged)
    if post_id not in DB["posts"]:
        raise KeyError("Post not found with id: " + post_id)
    del DB["posts"][post_id]
    return {"status": f"Post {post_id} deleted."}
