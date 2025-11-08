from typing import Dict, List, Optional, Union
from common_utils.tool_spec_decorator import tool_spec

from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.utils import generate_random_string, generate_entity_id
from youtube.SimulationEngine.models import MembershipUpdateModel, MembershipInsertModel, MembershipUpdateSnippetModel
from pydantic import ValidationError


"""
    Handles YouTube Memberships API operations.
    
    This class provides methods to manage channel memberships,
    which allow viewers to support their favorite creators with monthly payments.
"""


@tool_spec(
    spec={
    "name": "list_memberships",
    "description": "Retrieves a list of members that match the request criteria for a channel.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Must be 'snippet'."
            },
            "has_access_to_level": {
                "type": "string",
                "description": "The hasAccessToLevel parameter specifies the membership level that the member has access to. Defaults to None."
            },
            "filter_by_member_channel_id": {
                "type": "string",
                "description": "The filterByMemberChannelId parameter specifies a comma-separated list of YouTube channel IDs. The API will only return memberships from those channels. Defaults to None."
            },
            "max_results": {
                "type": "integer",
                "description": "The maxResults parameter specifies the maximum number of items that should be returned in the result set. Defaults to None."
            },
            "mode": {
                "type": "string",
                "description": "The mode parameter specifies the membership mode. Defaults to None."
            },
            "page_token": {
                "type": "string",
                "description": "The pageToken parameter identifies a specific page in the result set that should be returned. (Currently not used in implementation) Defaults to None."
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
    has_access_to_level: Optional[str] = None,
    filter_by_member_channel_id: Optional[str] = None,
    max_results: Optional[int] = None,
    mode: Optional[str] = None,
    page_token: Optional[str] = None,
) -> Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]:
    """
    Retrieves a list of members that match the request criteria for a channel.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. Must be 'snippet'.
        has_access_to_level (Optional[str]): The hasAccessToLevel parameter specifies the membership level that the member has access to. Defaults to None.
        filter_by_member_channel_id (Optional[str]): The filterByMemberChannelId parameter specifies a comma-separated list of YouTube channel IDs. The API will only return memberships from those channels. Defaults to None.
        max_results (Optional[int]): The maxResults parameter specifies the maximum number of items that should be returned in the result set. Defaults to None.
        mode (Optional[str]): The mode parameter specifies the membership mode. Defaults to None.
        page_token (Optional[str]): The pageToken parameter identifies a specific page in the result set that should be returned. (Currently not used in implementation) Defaults to None.

    Returns:
        Dict[str, List[Dict[str, Union[str, Dict[str, str]]]]]: A dictionary containing:
            - items (List[Dict[str, Union[str, Dict[str, str]]]]): A list of membership objects, each containing:
                - id (str): Unique ID of the member
                - snippet (Dict[str, str]): Metadata about the membership containing:
                    - memberChannelId (str): Channel ID of the member
                    - hasAccessToLevel (str): The level the member has access to
                    - mode (str): The mode of the membership (e.g., "fanFunding", "sponsors")

    Raises:
        ValueError: If any of the input parameters are invalid or validation fails.
    """
    # Type validation for part
    if not isinstance(part, str):
        raise ValueError("part must be a string")
    
    if part != "snippet":
        raise ValueError("Invalid part parameter")

    # Validate max_results if provided
    if max_results is not None:
        if not isinstance(max_results, int):
            raise ValueError("max_results must be an integer")
        if max_results <= 0 or max_results > 50:
            raise ValueError("max_results must be a positive integer between 1 and 50")

    # Validate mode if provided
    valid_modes = ["all_current", "updates"]
    if mode is not None:
        if not isinstance(mode, str):
            raise ValueError("mode must be a string")
        if mode not in valid_modes:
            raise ValueError(f"mode must be one of: {', '.join(valid_modes)}")

    # Validate filter_by_member_channel_id if provided
    if filter_by_member_channel_id is not None:
        if not isinstance(filter_by_member_channel_id, str):
            raise ValueError("filter_by_member_channel_id must be a string")
        
        # Split and validate each channel ID
        channel_ids = [cid.strip() for cid in filter_by_member_channel_id.split(",") if cid.strip()]
        if not channel_ids:
            raise ValueError("filter_by_member_channel_id must contain at least one valid channel ID")
        
        # Validate each channel ID format (YouTube channel IDs are typically 24 characters)
        for channel_id in channel_ids:
            if not channel_id or len(channel_id) != 24:
                raise ValueError(f"Invalid channel ID format: {channel_id}. Channel IDs must be 24 characters long.")

    # Validate has_access_to_level if provided
    valid_levels = ["basic", "premium", "vip"]  # Add all valid membership levels
    if has_access_to_level is not None:
        if not isinstance(has_access_to_level, str):
            raise ValueError("has_access_to_level must be a string")
        if has_access_to_level not in valid_levels:
            raise ValueError(f"has_access_to_level must be one of: {', '.join(valid_levels)}")

    filtered_members = __builtins__['list'](DB.get("memberships", {}).values())

    if has_access_to_level:
        filtered_members = [
            member
            for member in filtered_members
            if member.get("snippet", {}).get("hasAccessToLevel") == has_access_to_level
        ]

    if filter_by_member_channel_id:
        channel_ids = [cid.strip() for cid in filter_by_member_channel_id.split(",")]
        filtered_members = [
            member
            for member in filtered_members
            if member.get("snippet", {}).get("memberChannelId") in channel_ids
        ]

    if max_results:
        filtered_members = filtered_members[:max_results]

    if mode:
        filtered_members = [
            member
            for member in filtered_members
            if member.get("snippet", {}).get("mode") == mode
        ]

    return {"items": filtered_members}



@tool_spec(
    spec={
    "name": "create_membership",
    "description": "Creates a new membership.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. Must be a comma-separated string of valid parts, Supported values: \"snippet\"."
            },
            "snippet": {
                "type": "object",
                "description": "The snippet object containing membership details. Expected keys include:",
                "properties": {
                    "memberChannelId": {
                        "type": "string",
                        "description": "Channel ID of the member"
                    },
                    "hasAccessToLevel": {
                        "type": "string",
                        "description": "The level the member has access to"
                    },
                    "mode": {
                        "type": "string",
                        "description": "The mode of the membership"
                    }
                },
                "required": [
                    "memberChannelId",
                    "hasAccessToLevel",
                    "mode"
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
def insert(part: str, snippet: Dict[str, str]) -> Dict[str, Union[bool, Dict[str, Union[str, Dict[str, str]]], str]]:
    """
    Creates a new membership.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include. 
                    Must be a comma-separated string of valid parts, Supported values: "snippet".
        snippet (Dict[str, str]): The snippet object containing membership details. Expected keys include:
                                 - memberChannelId (str): Channel ID of the member
                                 - hasAccessToLevel (str): The level the member has access to
                                 - mode (str): The mode of the membership

    Returns:
        Dict[str, Union[bool, Dict[str,Union[str, Dict[str, str]]], str]]: A dictionary containing:
            - If validation is successful:
                - success (bool): Whether the operation was successful
                - membership (Dict[str, Union[str, Dict[str, str]]]): The created membership object containing only the properties 
                  specified in the part parameter that exist in the membership object:
                    - id (str): Unique ID of the member
                    - snippet (Dict[str, str]): Metadata about the membership containing:
                        - memberChannelId (str): Channel ID of the member
                        - hasAccessToLevel (str): The level the member has access to
                        - mode (str): The mode of the membership
            - If validation fails:
                - error (str): Error message describing the validation issue

    Raises:
        ValidationError: If the input parameters don't meet the validation requirements
    """
    try:
        # Validate input using Pydantic model
        validated_input = MembershipInsertModel.model_validate({"part": part, "snippet": snippet})
        
        # Create membership with validated data
        membership_id = generate_entity_id("member")
        full_membership = {"id": membership_id, "snippet": validated_input.snippet.model_dump()}

        # Save to database
        DB["memberships"][membership_id] = full_membership
        
        # Parse part parameter to control response content
        part_components = [p.strip() for p in part.split(",")]
        response_membership = {}
        
        # Include properties based on part parameter
        for component in part_components:
            if component in full_membership:
                response_membership[component] = full_membership[component]
        
        return {"success": True, "membership": response_membership}
        
    except ValidationError as e:
        # Extract first error message for simplicity
        error_msg = str(e.errors()[0]['msg']) if e.errors() else "Validation error"
        return {"error": error_msg}


@tool_spec(
    spec={
    "name": "delete_membership",
    "description": "Deletes a membership from the channel. This function removes a membership entry from the database based on the provided membership ID. It performs input validation and ensures the membership exists before attempting deletion.",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The unique identifier of the membership to delete. Must be a non-empty string representing a valid membership ID."
            }
        },
        "required": [
            "id"
        ]
    }
}
)
def delete(id: str) -> Dict[str, bool]:
    """
    Deletes a membership from the channel.

    This function removes a membership entry from the database based on the provided
    membership ID. It performs input validation and ensures the membership exists
    before attempting deletion.

    Args:
        id (str): The unique identifier of the membership to delete. Must be a 
                 non-empty string representing a valid membership ID.

    Returns:
        Dict[str, bool]: A dictionary containing:
            - success (bool): Whether the operation was successful

    Raises:
        ValueError: If the membership ID is empty or invalid
        TypeError: If the membership ID is not a string
        KeyError: If the membership with the given ID is not found
    """
    # Input validation
    if not isinstance(id, str):
        raise TypeError("Membership ID must be a string")
    
    if not id or not id.strip():
        raise ValueError("Membership ID cannot be empty")
    
    # Check if membership exists in the database
    if id not in DB.get("memberships", {}):
        raise KeyError("Membership with ID '{}' not found".format(id))
    
    # Delete the membership by removing it from the dictionary
    del DB["memberships"][id]
    return {"success": True}



@tool_spec(
    spec={
    "name": "update_membership",
    "description": "Updates an existing membership.",
    "parameters": {
        "type": "object",
        "properties": {
            "part": {
                "type": "string",
                "description": "The part parameter specifies the properties of the record that the API response will include. It must be set to \"snippet\"."
            },
            "id": {
                "type": "string",
                "description": "The ID of the membership to update. Must be a non-empty string."
            },
            "snippet": {
                "type": "object",
                "description": "The updated snippet object containing membership details. Expected keys include:",
                "properties": {
                    "memberChannelId": {
                        "type": "string",
                        "description": "Channel ID of the member"
                    },
                    "hasAccessToLevel": {
                        "type": "string",
                        "description": "The level the member has access to"
                    },
                    "mode": {
                        "type": "string",
                        "description": "The mode of the membership"
                    }
                },
                "required": []
            }
        },
        "required": [
            "part",
            "id",
            "snippet"
        ]
    }
}
)
def update(part: str, id: str, snippet: Dict[str, str]) -> Dict[str, Union[bool, str, Dict[str, Union[str, Dict[str, str]]]]]:
    """
    Updates an existing membership.

    Args:
        part (str): The part parameter specifies the properties of the record that the API response will include.
                    It must be set to "snippet".
        id (str): The ID of the membership to update. Must be a non-empty string.
        snippet (Dict[str, str]): The updated snippet object containing membership details.
                                   Expected keys include:
                                   - memberChannelId (Optional[str]): Channel ID of the member
                                   - hasAccessToLevel (Optional[str]): The level the member has access to
                                   - mode (Optional[str]): The mode of the membership


    Returns:
        Dict[str, Union[bool, str, Dict[str, Union[str, Dict[str, str]]]]]: A dictionary containing the result of the operation.
            - If successful: Dict[str, Union[bool, Dict[str, Union[str, Dict[str, str]]]]]
                - "success" (bool): True
                - "membership" (Dict[str, Union[str, Dict[str, str]]]): The updated membership object with keys:
                    - "id" (str): The unique ID of the member
                    - "snippet" (Dict[str, str]): Updated metadata about the membership
                        - "memberChannelId" (str): Channel ID of the member
                        - "hasAccessToLevel" (str): The level the member has access to
                        - "mode" (str): The mode of the membership
            - If part is invalid: Dict[str, str]
                - "error" (str): "Invalid part parameter"
            - If membership not found: Dict[str, bool]
                - "success" (bool): False

    Raises:
        ValidationError: If the input parameters fail Pydantic validation.
        TypeError: If the snippet is not a dictionary.
    """
    try:
        # Check if snippet is a dictionary before unpacking
        if not isinstance(snippet, dict):
            raise TypeError("'snippet' parameter must be a dictionary")
            
        # Use Pydantic model for validation
        validated_data = MembershipUpdateModel(part=part, id=id, snippet=MembershipUpdateSnippetModel(**snippet))
        
        if validated_data.part != "snippet":
            return {"error": "Invalid part parameter"}

        memberships = DB.get("memberships", {})
        if validated_data.id not in memberships:
            return {"success": False}

        membership = memberships[validated_data.id]
        if 'snippet' in membership and isinstance(membership.get('snippet'), dict):
            # Only update fields that are not None in the validated snippet
            snippet_data = validated_data.snippet.model_dump(exclude_none=True)
            membership["snippet"].update(snippet_data)
        else:
            membership['snippet'] = validated_data.snippet.model_dump(exclude_none=True)
        
        DB["memberships"][validated_data.id] = membership

        return {"success": True, "membership": membership}
    
    except ValidationError as e:
        # Re-raise ValidationError to be handled by the error handling system
        raise e
