from typing import Dict, List, Optional, Union
from youtube.SimulationEngine.custom_errors import InvalidPartParameterError, InvalidFilterParameterError
from common_utils.tool_spec_decorator import tool_spec

from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id
from pydantic import ValidationError
from youtube.SimulationEngine.models import UpdateChannelSectionSnippet, InsertChannelSectionSnippet


"""
    Handles YouTube Channel Sections API operations.
    
    This class provides methods to manage channel sections, which are customizable
    sections that appear on a YouTube channel page.
"""


@tool_spec(
    spec={
    "name": "list_channel_sections",
    "description": "Retrieves a list of channel sections with optional filters. Exactly one of channel_id, section_id, or mine must be provided.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. It should be a comma-separated string of valid parts (e.g., \"id,snippet,contentDetails\"). At least one specified part must be valid. An empty string, a string consisting only of commas/whitespace, or a string with no valid parts after parsing will raise an error."
            },
            "channel_id": {
                "type": "string",
                "description": "The channelId parameter specifies a YouTube channel ID. The API will only return that channel's sections. Defaults to None. Must be a non-empty string that uniquely identifies an existing channel in the database. Exactly one of channel_id, section_id, or mine must be provided."
            },
            "hl": {
                "type": "string",
                "description": "The hl parameter instructs the API to retrieve localized resource metadata for a specific application language that the YouTube website supports. Defaults to None."
            },
            "section_id": {
                "type": "string",
                "description": "The section_id parameter specifies a comma-separated list of the YouTube channel section ID(s) for the resource(s) that are being retrieved. Defaults to None. Must be a non-empty string that uniquely identifies existing channel sections in the database. Exactly one of channel_id, section_id, or mine must be provided."
            },
            "mine": {
                "type": "boolean",
                "description": "The mine parameter can be used to instruct the API to only return channel sections owned by the authenticated user. Defaults to None. Must be a boolean. Exactly one of channel_id, section_id, or mine must be provided."
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
def list(
    part: str,
    channel_id: Optional[str] = None,
    hl: Optional[str] = None,
    section_id: Optional[str] = None,
    mine: Optional[bool] = None,
    on_behalf_of_content_owner: Optional[str] = None,
) -> Dict[str, List[Dict[str, Union[str, Dict[str, Union[str, int, List[str]]]]]]]:
    """
    Retrieves a list of channel sections with optional filters.
    Exactly one of channel_id, section_id, or mine must be provided.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include.
              It should be a comma-separated string of valid parts (e.g., "id,snippet,contentDetails").
              At least one specified part must be valid. An empty string, a string consisting only of
              commas/whitespace, or a string with no valid parts after parsing will raise an error.
        channel_id (Optional[str]): The channelId parameter specifies a YouTube channel ID.
                    The API will only return that channel's sections. Defaults to None. Must be a non-empty string that uniquely identifies an existing channel in the database. 
                    Exactly one of channel_id, section_id, or mine must be provided.
        hl (Optional[str]): The hl parameter instructs the API to retrieve localized resource metadata
            for a specific application language that the YouTube website supports. Defaults to None.
        section_id (Optional[str]): The section_id parameter specifies a comma-separated list of the YouTube channel section ID(s)
                    for the resource(s) that are being retrieved. Defaults to None. Must be a non-empty string that uniquely identifies existing channel sections in the database. 
                    Exactly one of channel_id, section_id, or mine must be provided.
        mine (Optional[bool]): The mine parameter can be used to instruct the API to only return channel sections
              owned by the authenticated user. Defaults to None. Must be a boolean. Exactly one of channel_id, section_id, or mine must be provided.
        on_behalf_of_content_owner (Optional[str]): The onBehalfOfContentOwner parameter indicates that the request's
                                     authorization credentials identify a YouTube CMS user who is acting
                                     on behalf of the content owner specified in the parameter value. Defaults to None.

    Returns:
        Dict[str, List[Dict[str, Union[str, Dict[str, Union[str, int, List[str]]]]]]]: A dictionary containing:
            - items (List[Dict[str, Union[str, Dict[str, Union[str, int, List[str]]]]]]): List of channel section objects matching the filter criteria.
            Each channel section object's structure depends on the 'part' parameter and API specifics. Example fields:
                - id (str): Unique section identifier
                - snippet (Dict[str, Union[str, int]]): Section details (channelId, title, position, type)
                    - title (str): Section title
                    - type (str): Section type
                    - channelId (str): Channel ID
                    - position (unsigned int): Section position
                - contentDetails (Dict[str, List[str]]): Additional section content details.
                    - playlists (List[str]): List of playlist IDs
                    - channels (List[str]): List of channel IDs

    Raises:
        TypeError: If any argument is of an incorrect type (e.g., 'part' is not a string,
                   'mine' is not a boolean).
        InvalidPartParameterError: If the 'part' parameter is an empty string, malformed (e.g., consists
                                   only of commas or whitespace), or if none of its comma-separated components
                                   are valid. Valid part components are "id", "snippet", "contentDetails".
        KeyError: If the database interaction leads to a KeyError (e.g., if `DB.get` raises it,
                  potentially indicating the database is not properly initialized or an essential
                  key is missing). This error is propagated from the underlying database access.
        InvalidFilterParameterError: If exactly one of 'channel_id', 'section_id', or 'mine' is not provided.
    """
    

    # --- Core Logic (preserved from original function) ---
    # The original function's initial validation for 'part' (which returned a dict)
    # is now replaced by the more robust validation section above (which raises exceptions).
    # The 'part' string argument itself is passed to the core logic as is; its content validity
    # and basic format are ensured by the preceding checks.

    # --- Input Validation ---
    if not isinstance(part, str):
        raise TypeError("Parameter 'part' must be a string.")
    
    # Check if part is effectively empty after stripping whitespace
    if not part.strip():
        raise InvalidPartParameterError(
            "Parameter 'part' cannot be empty or consist only of whitespace."
        )

    valid_parts = ["id", "snippet", "contentDetails"]
    # Parse 'part' into components: split by comma, strip whitespace from each, filter out empty strings
    # (e.g., from "part1,,part2" or " part1 , part2 ").
    parsed_part_components = [p.strip() for p in part.split(",") if p.strip()]

    if not parsed_part_components:
        # This case handles inputs like "," or ", , ," which result in no valid components after parsing.
        raise InvalidPartParameterError(
            f"Parameter 'part' resulted in no valid components after parsing. Original value: '{part}'"
        )

    if not any(p_comp in valid_parts for p_comp in parsed_part_components):
        raise InvalidPartParameterError(
            f"Invalid part parameter"
        )

    if channel_id is not None and not isinstance(channel_id, str):
        raise TypeError("Parameter 'channel_id' must be a string or None.")
    if hl is not None and not isinstance(hl, str):
        raise TypeError("Parameter 'hl' must be a string or None.")
    if section_id is not None and not isinstance(section_id, str):
        raise TypeError("Parameter 'section_id' must be a string or None.")
    if mine is not None and not isinstance(mine, bool):
        raise TypeError("Parameter 'mine' must be a boolean or None.")
    if on_behalf_of_content_owner is not None and not isinstance(on_behalf_of_content_owner, str):
        raise TypeError("Parameter 'on_behalf_of_content_owner' must be a string or None.")

    provided_filters = [
        channel_id,
        section_id,
        mine
    ]

    num_provided = sum(1 for f in provided_filters if f is not None)

    if num_provided == 0:
        raise InvalidFilterParameterError(
            "Exactly one of 'channelId', 'id', or 'mine' must be provided."
        )
    elif num_provided > 1:
        raise InvalidFilterParameterError(
            f"Only one of 'channel_id', 'section_id', or 'mine' can be provided."
        )
    
    if section_id:
        provided_section_ids = section_id.split(",")
    else:
        provided_section_ids = []

    filtered_sections = []
    # DB is assumed to be an existing database interface object, globally available or imported.
    sections = DB.get("channelSections", {}) # This call might raise KeyError as per original docstring.

    # Apply filters
    for section_id_key, section_data in sections.items():
        if provided_section_ids and section_id_key not in provided_section_ids:
            continue
        if (
            channel_id
            and section_data.get("snippet", {}).get("channelId") != channel_id
        ):
            continue
        
        current_section = {}

        if "id" in parsed_part_components:
            current_section["id"] = section_id_key
            
        if "snippet" in parsed_part_components:
            current_section["snippet"] = section_data.get("snippet", {})
        
        if "contentDetails" in parsed_part_components:
            current_section["contentDetails"] = section_data.get("contentDetails", {})
        
        filtered_sections.append(current_section)
    
        # Note: The mine filter is not applied here.
        # Note: 'on_behalf_of_content_owner' is not used in the provided filtering logic. This is preserved.
        # This behavior (or lack thereof) is preserved.

    return {"items": filtered_sections}


@tool_spec(
    spec={
    "name": "delete_channel_section",
    "description": "Deletes a channel section from the database.",
    "parameters": {
        "type": "object",
        "properties": {
            "section_id": {
                "type": "string",
                "description": "The unique identifier of the channel section to delete."
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "Content owner ID for CMS user operations. Defaults to None."
            }
        },
        "required": [
            "section_id"
        ]
    }
}
)
def delete(
    section_id: str, on_behalf_of_content_owner: Optional[str] = None
) -> Dict[str, bool]:
    """
    Deletes a channel section from the database.

    Args:
        section_id (str): The unique identifier of the channel section to delete.
        on_behalf_of_content_owner (Optional[str]): Content owner ID for CMS user operations. Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary containing: 
        - success (bool): Whether the operation was successful
            
    Raises:
        TypeError: If 'section_id' is not a string.
        KeyError: If the section_id is not found in the database.
        TypeError: If 'on_behalf_of_content_owner' is provided and is not a string.
    """
    # --- Input Validation ---
    if not isinstance(section_id, str):
        raise TypeError("section_id must be a string.")

    if on_behalf_of_content_owner is not None and not isinstance(on_behalf_of_content_owner, str):
        raise TypeError("on_behalf_of_content_owner must be a string if provided.")
    # --- End of Input Validation ---

    # Assuming DB is a dictionary-like structure accessible in this scope.
    # Example: DB = {"channelSections": {"some_id": {}}}
    if section_id not in DB.get("channelSections", {}):
        raise KeyError(
            f"Channel section ID: {section_id} not found in the database."
        )

    del DB["channelSections"][section_id]
    return {"success": True}


@tool_spec(
    spec={
    "name": "insert_channel_section",
    "description": "Inserts a new channel section.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Must be a comma-separated string of valid parts (e.g., \"snippet,contentDetails,statistics\")."
            },
            "snippet": {
                "type": "object",
                "description": "The snippet object contains details about the channel section.",
                "properties": {
                    "channelId": {
                        "type": "string",
                        "description": "The ID of the channel that the section belongs to. Must be a non-empty string that uniquely identifies an existing channel in the database."
                    },
                    "type": {
                        "type": "string",
                        "description": "The type of the section."
                    }
                },
                "required": [
                    "channelId",
                    "type"
                ]
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Currently not used! Defaults to None."
            },
            "on_behalf_of_content_owner_channel": {
                "type": "string",
                "description": "The onBehalfOfContentOwnerChannel parameter specifies the YouTube channel ID of the channel to which the user is being added. Currently not used! Defaults to None."
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
    on_behalf_of_content_owner: Optional[str] = None,
    on_behalf_of_content_owner_channel: Optional[str] = None,
) -> Dict[str, Union[bool, Dict[str, Union[str, Dict[str, str], None]]]]:
    """
    Inserts a new channel section.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Must be a comma-separated string of valid parts (e.g., "snippet,contentDetails,statistics").
        snippet (Dict[str, str]): The snippet object contains details about the channel section.
            - channelId (str): The ID of the channel that the section belongs to. Must be a non-empty string that uniquely identifies an existing channel in the database.
            - type (str): The type of the section.
        on_behalf_of_content_owner (Optional[str]): The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Currently not used! Defaults to None.    
        on_behalf_of_content_owner_channel (Optional[str]): The onBehalfOfContentOwnerChannel parameter specifies the YouTube channel ID of the channel to which the user is being added. Currently not used! Defaults to None.

    Returns:
        Dict[str, Union[bool, Dict[str, Union[str, Dict[str, str], None]]]]: A dictionary containing:
            - success (bool): Whether the operation was successful
            - channelSection (Dict[str, Union[str, Dict[str, str], None]]]): The newly created channel section object
                - id (str): Unique section identifier
                - snippet (Dict[str, str]): Section details (channelId, type)
                    - channelId (str): Channel ID
                    - type (str): Section type
                - onBehalfOfContentOwner (Optional[str]): CMS user information. Must be not empty when provided.
                - onBehalfOfContentOwnerChannel (Optional[str]): YouTube channel ID of the channel to which the user is being added. Must be not empty when provided.

    Raises:
        ValueError: If part parameter is empty, invalid or not provided,
                    if snippet is not provided,
                    or if channelId is not found in the database
                    or if on_behalf_of_content_owner is provided and is empty
                    or if on_behalf_of_content_owner_channel is provided and is empty
        ValidationError: If snippet is malformed 
        TypeError: If part is not a string
                    or if on_behalf_of_content_owner is provided and is not a string
                    or if on_behalf_of_content_owner_channel is provided and is not a string
    """
    if not part:
        raise ValueError("part parameter is required")
    if not snippet:
        raise ValueError("snippet parameter is required")

    if not isinstance(part, str):
        raise TypeError("part must be a string")
    if not part.strip():
        raise ValueError("part cannot be an empty string")
    for p in part.split(","):
        if p not in ["snippet", "statistics", "contentDetails"]:
            raise ValueError("Invalid part parameter value")

    try:
        validated_snippet = InsertChannelSectionSnippet(**snippet)
        if snippet["channelId"] not in DB.get("channels", {}):
            raise ValueError(f"Channel ID: {snippet['channelId']} not found in the database.")
    except ValidationError as e:
        raise e

    new_id = generate_entity_id("channelSection")
    new_section = {"id": new_id, "snippet": validated_snippet.model_dump(), "onBehalfOfContentOwner": None, "onBehalfOfContentOwnerChannel": None}

    if on_behalf_of_content_owner is not None:
        if not isinstance(on_behalf_of_content_owner, str):
            raise TypeError("on_behalf_of_content_owner must be a string")
        if not on_behalf_of_content_owner.strip():
            raise ValueError("on_behalf_of_content_owner cannot be an empty string")
        new_section["onBehalfOfContentOwner"] = on_behalf_of_content_owner

    if on_behalf_of_content_owner_channel is not None:
        if not isinstance(on_behalf_of_content_owner_channel, str):
            raise TypeError("on_behalf_of_content_owner_channel must be a string")
        if not on_behalf_of_content_owner_channel.strip():
            raise ValueError("on_behalf_of_content_owner_channel cannot be an empty string")
        new_section["onBehalfOfContentOwnerChannel"] = on_behalf_of_content_owner_channel

    DB.setdefault("channelSections", {})[new_id] = new_section
    return {"success": True, "channelSection": new_section}
    


@tool_spec(
    spec={
    "name": "update_channel_section",
    "description": "Updates a channel section.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Must be a comma-separated string of valid parts (e.g., \"snippet,contentDetails,statistics\")."
            },
            "section_id": {
                "type": "string",
                "description": "The ID of the channel section to update. Must be a non-empty string that uniquely identifies an existing channel section in the database."
            },
            "snippet": {
                "type": "object",
                "description": "The snippet object contains details about the channel section. Defaults to None.",
                "properties": {
                    "channelId": {
                        "type": "string",
                        "description": "The ID of the channel that the section belongs to. Must be a non-empty string that uniquely identifies an existing channel in the database."
                    },
                    "type": {
                        "type": "string",
                        "description": "The type of the section."
                    }
                },
                "required": []
            },
            "on_behalf_of_content_owner": {
                "type": "string",
                "description": "The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Currently not used ! Defaults to None."
            }
        },
        "required": [
            "part",
            "section_id"
        ]
    }
}
)
def update(
    part: str,
    section_id: str,
    snippet: Optional[Dict[str, str]] = None,
    on_behalf_of_content_owner: Optional[str] = None,
) -> Dict[str, str]:
    """
    Updates a channel section.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Must be a comma-separated string of valid parts (e.g., "snippet,contentDetails,statistics").
        section_id (str): The ID of the channel section to update. Must be a non-empty string that uniquely identifies an existing channel section in the database.
        snippet (Optional[Dict[str, str]]): The snippet object contains details about the channel section. Defaults to None.
            - channelId (Optional[str]): The ID of the channel that the section belongs to. Must be a non-empty string that uniquely identifies an existing channel in the database.
            - type (Optional[str]): The type of the section.
        on_behalf_of_content_owner (Optional[str]): The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. Currently not used ! Defaults to None.

    Returns:
        Dict[str, str]: A dictionary containing:
            - success (str): Success message if the update was successful

    Raises:
        ValueError: If part parameter is empty, invalid or not provided,
                    if section_id is not provided, empty or not present in the database,
                    if on_behalf_of_content_owner is provided and is empty
                    or if snippet is provided and channelId is not found in the database.
        ValidationError: If snippet is malformed 
        TypeError: If part is not a string
                    or if section_id is not a string
                    or if on_behalf_of_content_owner is provided and is not a string
    """
    if not part:
        raise ValueError("part parameter is required")

    if not section_id:
        raise ValueError("section_id parameter is required")

    if not isinstance(part, str):
        raise TypeError("part must be a string")
    if not part.strip():
        raise ValueError("part cannot be an empty string")
    for p in part.split(","):
        if p not in ["snippet", "statistics", "contentDetails"]:
            raise ValueError("Invalid part parameter value")

    if not isinstance(section_id, str):
        raise TypeError("section_id must be a string")
    if not section_id.strip():
        raise ValueError("section_id cannot be an empty string")

    # Check if channel section exists
    sections = DB.get("channelSections", {})
    if section_id not in sections:
        raise ValueError(f"Channel section ID: {section_id} not found in the database.")

    section = sections[section_id]

    if on_behalf_of_content_owner is not None:
        if not isinstance(on_behalf_of_content_owner, str):
            raise TypeError("on_behalf_of_content_owner must be a string")
        if not on_behalf_of_content_owner.strip():
            raise ValueError("on_behalf_of_content_owner cannot be an empty string")
        section["onBehalfOfContentOwner"] = on_behalf_of_content_owner
           
    if snippet is not None:
        try:
            validated_snippet = UpdateChannelSectionSnippet(**snippet)
        except ValidationError as e:
            raise e
        if "channelId" in snippet:
            if snippet["channelId"] not in DB.get("channels", {}):
                raise ValueError(f"Channel ID: {snippet['channelId']} not found in the database.")

        section["snippet"] = validated_snippet

    DB["channelSections"][section_id] = section

    return {"success": f"Channel section ID: {section_id} updated successfully."}
        