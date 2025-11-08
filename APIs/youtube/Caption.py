from common_utils.tool_spec_decorator import tool_spec

from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id

from pydantic import ValidationError
from typing import Optional, Dict, List, Union

from youtube.SimulationEngine.models import CaptionSnippetModel, CaptionUpdateSnippetModel


"""
    Handles YouTube Caption API operations.
    
    This class provides methods to manage video captions, including uploading,
    downloading, updating, and deleting caption tracks.
"""


@tool_spec(
    spec={
    "name": "delete_caption",
    "description": "Deletes a caption.",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The id parameter identifies the caption track that is being deleted."
            },
            "onBehalfOf": {
                "type": "string",
                "description": "The onBehalfOf parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the onBehalfOfContentOwner parameter. (Currently not used in implementation) Defaults to None."
            },
            "onBehalfOfContentOwner": {
                "type": "string",
                "description": "The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. (Currently not used in implementation) Defaults to None."
            }
        },
        "required": [
            "id"
        ]
    }
}
)
def delete(
    id: str,
    onBehalfOf: Optional[str] = None,
    onBehalfOfContentOwner: Optional[str] = None,
) -> Dict[str, bool]:
    """
    Deletes a caption.

    Args:
        id (str): The id parameter identifies the caption track that is being deleted.
        onBehalfOf (Optional[str]): The onBehalfOf parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the onBehalfOfContentOwner parameter. (Currently not used in implementation) Defaults to None.
        onBehalfOfContentOwner (Optional[str]): The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. (Currently not used in implementation) Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary containing:
            - success (bool): True if deletion is successful

    Raises:
        ValueError: If the caption ID does not exist in the database.
    """
    if id is None:
        raise ValueError("ID parameter cannot be None.")
    
    if not isinstance(id, str):
        raise TypeError("ID parameter must be a string.")
    
    if id not in DB.get("captions", {}):
        raise ValueError("ID does not exist in the database.")

    del DB["captions"][id]
    return {"success": True}


@tool_spec(
    spec={
    "name": "download_caption",
    "description": "Downloads a caption track.",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The ID of the caption to be downloaded."
            },
            "onBehalfOf": {
                "type": "string",
                "description": "CMS user making the request on behalf of the content owner. Defaults to None."
            },
            "onBehalfOfContentOwner": {
                "type": "string",
                "description": "Content owner the user is acting on behalf of. Defaults to None."
            },
            "tfmt": {
                "type": "string",
                "description": "Desired format of the caption file ('srt', 'vtt', 'sbv'). Defaults to None."
            },
            "tlang": {
                "type": "string",
                "description": "Target language for translation. Defaults to None."
            }
        },
        "required": [
            "id"
        ]
    }
}
)
def download(
    id: str,
    onBehalfOf: Optional[str] = None,
    onBehalfOfContentOwner: Optional[str] = None,
    tfmt: Optional[str] = None,
    tlang: Optional[str] = None,
) -> str:
    """
    Downloads a caption track.

    Args:
        id (str): The ID of the caption to be downloaded.
        onBehalfOf (Optional[str]): CMS user making the request on behalf of the content owner. Defaults to None.
        onBehalfOfContentOwner (Optional[str]): Content owner the user is acting on behalf of. Defaults to None.
        tfmt (Optional[str]): Desired format of the caption file ('srt', 'vtt', 'sbv'). Defaults to None.
        tlang (Optional[str]): Target language for translation. Defaults to None.

    Returns:
        str: Caption content or translated content.

    Raises:
        ValueError: If caption id is not found in the database
                    or tfmt(if provided) is unsupported 
                    or id parameter is None.

        TypeError: If caption ID is not a string
                    or ifmt(if provided) is not a string
                    or tlang(if provided) is not a string
                    or onBehalfOf(if provided) is not a string
                    or onBehalfOfContentOwner(if provided) is not a string.
    """
    if id is None:
        raise ValueError("Caption ID is required.")
    
    if not isinstance(id, str):
        raise TypeError("Caption ID must be a string.")
    
    if id not in DB.get("captions", {}):
        raise ValueError("Caption not found")

    caption = DB["captions"][id]

    format_mapping = {
        "srt": "SRT format caption content",
        "vtt": "WebVTT format caption content", 
        "sbv": "SubViewer format caption content",
    }
    if tfmt is not None:
        if not isinstance(tfmt, str):
            raise TypeError("Format must be a string.")
        if tfmt not in format_mapping:
            raise ValueError("Unsupported tfmt format.")
        return format_mapping[tfmt]

    if tlang is not None:
        if not isinstance(tlang, str):
            raise TypeError("Target language must be a string.")       
        return f"Simulated translated caption to {tlang}"


    if onBehalfOf is not None:
        if not isinstance(onBehalfOf, str):
            raise TypeError("On behalf of must be a string.")
        if not onBehalfOf.strip():
            raise ValueError("On behalf of cannot be empty or consist only of whitespace.")
        # Note: onBehalfOf is not used in the implementation

    if onBehalfOfContentOwner is not None:
        if not isinstance(onBehalfOfContentOwner, str):
            raise TypeError("On behalf of content owner must be a string.")
        if not onBehalfOfContentOwner.strip():
            raise ValueError("On behalf of content owner cannot be empty or consist only of whitespace.")
        # Note: onBehalfOfContentOwner is not used in the implementation

    return caption.get("snippet", {}).get("text", "Caption content")


@tool_spec(
    spec={
    "name": "insert_caption",
    "description": "Inserts a new caption track for a video.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Supported values : 'snippet'."
            },
            "snippet": {
                "type": "object",
                "description": "The snippet object contains details about the caption track.",
                "properties": {
                    "videoId": {
                        "type": "string",
                        "description": "The ID that YouTube uses to uniquely identify the video that the caption track is associated with."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text of the caption track"
                    }
                },
                "required": [
                    "videoId",
                    "text"
                ]
            },
            "onBehalfOf": {
                "type": "string",
                "description": "The onBehalfOf parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the onBehalfOfContentOwner parameter. Defaults to None."
            },
            "onBehalfOfContentOwner": {
                "type": "string",
                "description": "The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Defaults to None."
            },
            "sync": {
                "type": "boolean",
                "description": "The sync parameter indicates whether the caption track should be synchronized with the video. Defaults to False."
            }
        },
        "required": [
            "part",
            "snippet"
        ]
    }
}
)
def insert(
    part: str,
    snippet: Dict[str, str],
    onBehalfOf: Optional[str] = None,
    onBehalfOfContentOwner: Optional[str] = None,
    sync: bool = False,
) -> Dict[str, Union[bool, Dict[str, Union[str, Dict[str, str], bool]]]]:
    """
    Inserts a new caption track for a video.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Supported values : 'snippet'.
        snippet (Dict[str, str]): The snippet object contains details about the caption track.
            - videoId (str): The ID that YouTube uses to uniquely identify the video that the caption track is associated with.
            - text (str): The text of the caption track
         
        onBehalfOf (Optional[str]): The onBehalfOf parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the onBehalfOfContentOwner parameter. Defaults to None.
        onBehalfOfContentOwner (Optional[str]): The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Defaults to None.
        sync (bool): The sync parameter indicates whether the caption track should be synchronized with the video. Defaults to False.


    Returns:
        Dict[str, Union[bool, Dict[str, Union[str, Dict[str, str], bool]]]]: A dictionary containing:
            - success (bool): True if caption was successfully inserted
            - caption (Dict[str, Union[str, Dict[str, str], bool]]): The created caption object containing:
                - id (str): Generated unique caption ID
                - snippet (Dict[str, str]]): The caption track's metadata containing:
                    - videoId (str): The ID that YouTube uses to uniquely identify the video that the caption track is associated with
                    - text (str): The text of the caption track
                - sync (bool): The sync parameter indicates whether the caption track should be synchronized with the video
                - onBehalfOf (Optional[str]): The onBehalfOf parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the onBehalfOfContentOwner parameter.
                - onBehalfOfContentOwner (Optional[str]): The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value.

    Raises:
        ValueError: If the part parameter is not provided, empty or not 'snippet'
                    or if the sync parameter is not provided
                    or if the snippet parameter is not provided
                    or if the onBehalfOf is provided but is empty or consist only of whitespace
                    or if the onBehalfOfContentOwner is provided but is empty or consist only of whitespace
        TypeError: If any parameter has an invalid type.
        ValidationError: If the input parameters fail Pydantic validation.
    """
    if part is None:
        raise ValueError("Part parameter cannot be None.")
    
    if not isinstance(part, str):
        raise TypeError("Parameter 'part' must be a string.")
    
    if not part.strip():
        raise ValueError("Part parameter cannot be empty or consist only of whitespace.")
    
    if part.strip().lower() != 'snippet':
        raise ValueError("Part parameter must be 'snippet'.")

    if sync is None:
        raise ValueError("Sync parameter is required.")

    if snippet is None:
        raise ValueError("Snippet parameter cannot be None.")
       
    
    if not isinstance(sync, bool):
        raise TypeError("Parameter 'sync' must be a boolean.")
    
    try:
        validated_snippet = CaptionSnippetModel(**snippet)
        snippet_dict = validated_snippet.model_dump()
    except ValidationError as e:
        raise e
    
    # Generate new caption ID
    new_id = generate_entity_id("caption")

    # Create new caption object with proper structure
    new_caption = {
        "id": new_id,
        "snippet": snippet_dict,
        "sync": sync
    }

    # Add optional parameters if provided
    if onBehalfOf is not None:
        if not isinstance(onBehalfOf, str):
            raise TypeError("On behalf of must be a string.")
        
        if not onBehalfOf.strip():
            raise ValueError("On behalf of cannot be empty or consist only of whitespace.")

        new_caption["onBehalfOf"] = onBehalfOf

    if onBehalfOfContentOwner is not None:
        if not isinstance(onBehalfOfContentOwner, str):
            raise TypeError("On behalf of content owner must be a string.")
        
        if not onBehalfOfContentOwner.strip():
            raise ValueError("On behalf of content owner cannot be empty or consist only of whitespace.")

        new_caption["onBehalfOfContentOwner"] = onBehalfOfContentOwner

    new_caption["sync"] = sync

    if "captions" not in DB:
        DB["captions"] = {}
    DB["captions"][new_id] = new_caption

    return {"success": True, "caption": new_caption}


@tool_spec(
    spec={
    "name": "list_captions",
    "description": "Retrieves a list of captions.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Supported values: 'id', 'snippet'."
            },
            "videoId": {
                "type": "string",
                "description": "ID of the video to retrieve captions for. Must be a non-empty string and present in the database."
            },
            "id": {
                "type": "string",
                "description": "Specific caption ID to filter results. Must be a non-empty string and present in the database if provided. Defaults to None."
            },
            "onBehalfOf": {
                "type": "string",
                "description": "CMS user making the request on behalf of the content owner. Must be a non-empty string if provided. Defaults to None."
            },
            "onBehalfOfContentOwner": {
                "type": "string",
                "description": "Content owner the user is acting on behalf of. Must be a non-empty string if provided. Defaults to None."
            }
        },
        "required": [
            "part",
            "videoId"
        ]
    }
}
)
def list(
    part: str,
    videoId: str,
    id: Optional[str] = None,
    onBehalfOf: Optional[str] = None,
    onBehalfOfContentOwner: Optional[str] = None,
) -> Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]:
    """
    Retrieves a list of captions.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Supported values: 'id', 'snippet'.
        videoId (str): ID of the video to retrieve captions for. Must be a non-empty string and present in the database.
        id (Optional[str]): Specific caption ID to filter results. Must be a non-empty string and present in the database if provided. Defaults to None.
        onBehalfOf (Optional[str]): CMS user making the request on behalf of the content owner. Must be a non-empty string if provided. Defaults to None.
        onBehalfOfContentOwner (Optional[str]): Content owner the user is acting on behalf of. Must be a non-empty string if provided. Defaults to None.

    Returns:
        Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]: A dictionary containing:
            - items (List[Dict[str, Union[str, Dict[str, str]]]]): A list of caption objects, each containing:
                - id Optional[str]: Caption ID
                or
                - snippet Optional[Dict[str, str]]: Caption metadata containing at least:
                    - videoId (str): The ID of the video the caption belongs to

    Raises:
        ValueError: If 'part' is not valid or none
                    or if the part parameter is not 'id' or 'snippet'
                    or if the video ID is none
                    or if the video ID does not exist in the database
                    or if the id is provided but does not exist in the database
                    or if the onBehalfOf is provided but is empty or consist only of whitespace
                    or if the onBehalfOfContentOwner is provided but is empty or consist only of whitespace
        TypeError: If any of the provided string parameters are not strings

    """
    if part is None:
        raise ValueError("Part parameter cannot be None.")

    if not isinstance(part, str):
        raise TypeError("Part parameter must be a string.")
    
    if part.strip().lower() not in ["id", "snippet"]:
        raise ValueError("Invalid part parameter")
    
    if videoId is None:
        raise ValueError("Video ID cannot be None.")
    
    if not isinstance(videoId, str):
        raise TypeError("Video ID must be a string.")
    
    if videoId not in DB.get("videos", {}):
        raise ValueError("Video ID does not exist in the database.")

    captions = [
        cap
        for cap in DB.get("captions", {}).values()
        if cap.get("snippet", {}).get("videoId") == videoId
    ]
    if id is not None:
        if not isinstance(id, str):
            raise TypeError("ID must be a string.")
        
        if id not in DB.get("captions", {}):
            raise ValueError("ID does not exist in the database.")
        
        captions = [cap for cap in captions if cap["id"] == id]

    if onBehalfOf is not None:
        if not isinstance(onBehalfOf, str):
            raise TypeError("On behalf of must be a string.")

        if not onBehalfOf.strip():
            raise ValueError("On behalf of cannot be empty or consist only of whitespace.")
        
        captions = [cap for cap in captions if cap.get("onBehalfOf") == onBehalfOf]

    if onBehalfOfContentOwner is not None:
        if not isinstance(onBehalfOfContentOwner, str):
            raise TypeError("On behalf of content owner must be a string.")

        if not onBehalfOfContentOwner.strip():
            raise ValueError("On behalf of content owner cannot be empty or consist only of whitespace.")
        
        captions = [cap for cap in captions if cap.get("onBehalfOfContentOwner") == onBehalfOfContentOwner]

    if part.strip().lower() == "id":
        return {"items": [{"id": cap["id"]} for cap in captions]}
    elif part.strip().lower() == "snippet":
        return {"items": [{"snippet": cap["snippet"]} for cap in captions]}


@tool_spec(
    spec={
    "name": "update_caption",
    "description": "Updates a caption resource.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Supported values: 'snippet'."
            },
            "id": {
                "type": "string",
                "description": "The id parameter identifies the caption track that is being updated."
            },
            "snippet": {
                "type": "object",
                "description": "The snippet object contains details about the caption track. Defaults to None. Contains the following fields:",
                "properties": {
                    "videoId": {
                        "type": "string",
                        "description": "The ID that YouTube uses to uniquely identify the video that the caption track is associated with. Must be a non-empty string and present in the database if provided."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text of the caption track. Must be a non-empty string if provided."
                    }
                },
                "required": []
            },
            "onBehalfOf": {
                "type": "string",
                "description": "CMS user making the request on behalf of the content owner. Must be a non-empty string if provided. Defaults to None."
            },
            "onBehalfOfContentOwner": {
                "type": "string",
                "description": "Content owner the user is acting on behalf of. Must be a non-empty string if provided. Defaults to None."
            },
            "sync": {
                "type": "boolean",
                "description": "The sync parameter indicates whether the caption track should be synchronized with the video. Must be a boolean if provided. Defaults to None."
            }
        },
        "required": [
            "part",
            "id"
        ]
    }
}
)
def update(
    part: str,
    id: str,
    snippet: Optional[Dict[str, str]] = None,
    onBehalfOf: Optional[str] = None,
    onBehalfOfContentOwner: Optional[str] = None,
    sync: Optional[bool] = None,
) -> Dict[str, Union[bool, str]]:
    """
    Updates a caption resource.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Supported values: 'snippet'.
        id (str): The id parameter identifies the caption track that is being updated.
        snippet (Optional[Dict[str, str]]): The snippet object contains details about the caption track. Defaults to None. Contains the following fields:
            - videoId (Optional[str]): The ID that YouTube uses to uniquely identify the video that the caption track is associated with. Must be a non-empty string and present in the database if provided.
            - text (Optional[str]): The text of the caption track. Must be a non-empty string if provided.
        onBehalfOf (Optional[str]): CMS user making the request on behalf of the content owner. Must be a non-empty string if provided. Defaults to None.
        onBehalfOfContentOwner (Optional[str]): Content owner the user is acting on behalf of. Must be a non-empty string if provided. Defaults to None.
        sync (Optional[bool]): The sync parameter indicates whether the caption track should be synchronized with the video. Must be a boolean if provided. Defaults to None.


    Returns:
        Dict[str, Union[bool, str]]: A dictionary containing:
                - success (bool): True if caption was successfully updated
                - message (str): Confirmation message "Caption updated."

    Raises:
        ValueError: If 'part' is not provided or not 'snippet'
                    or if the id is not provided or does not exist in the database
                    or if the onBehalfOf is provided but is empty or consist only of whitespace
                    or if the onBehalfOfContentOwner is provided but is empty or consist only of whitespace
                    or if the sync is provided but is not a boolean
        TypeError: If any of the provided string parameters are not strings
        ValidationError: If the input parameters fail Pydantic validation.
    """
    if part is None:
        raise ValueError("Part parameter cannot be None.")
    
    if not isinstance(part, str):
        raise TypeError("Part parameter must be a string.")
    
    if part.strip().lower() not in ["snippet"]:
        raise ValueError("Invalid 'part' parameter. Expected 'snippet'.")

    if id is None:
        raise ValueError("ID parameter cannot be None.")
    
    if not isinstance(id, str):
        raise TypeError("ID parameter must be a string.")

    if id not in DB.get("captions", {}):
        raise ValueError("ID does not exist in the database.")

    caption = DB["captions"][id]
    
    if snippet is not None:
        try:
            validated_snippet = CaptionUpdateSnippetModel(**snippet)
            snippet_dict = validated_snippet.model_dump()
            for key, value in snippet_dict.items():
                if value is not None:
                    caption["snippet"][key] = value
        except ValidationError as e:
            raise e

    if onBehalfOf is not None:
        if not isinstance(onBehalfOf, str):
            raise TypeError("On behalf of must be a string.")

        if not onBehalfOf.strip():
            raise ValueError("On behalf of cannot be empty or consist only of whitespace.")
        
        caption["onBehalfOf"] = onBehalfOf
        
    if onBehalfOfContentOwner is not None:
        if not isinstance(onBehalfOfContentOwner, str):
            raise TypeError("On behalf of content owner must be a string.")
        
        if not onBehalfOfContentOwner.strip():
            raise ValueError("On behalf of content owner cannot be empty or consist only of whitespace.")
        
        caption["onBehalfOfContentOwner"] = onBehalfOfContentOwner 

    if sync is not None:
        if not isinstance(sync, bool):
            raise TypeError("Parameter 'sync' must be a boolean.")
        
        caption["sync"] = sync

    DB["captions"][id] = caption

    return {"success": True, "message": "Caption updated."}
