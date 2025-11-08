from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
# APIs/google_chat/Spaces/Messages/Reactions.py

import re
import sys
import os
import uuid
from typing import List, Dict, Any, Optional, Union
from google_chat.SimulationEngine.models import ReactionInput
from google_chat.SimulationEngine.custom_errors import *
from pydantic import BaseModel, ValidationError, model_validator

sys.path.append("APIs")

from google_chat.SimulationEngine.db import DB



@tool_spec(
    spec={
        "name": "add_message_reaction",
        "description": "Creates a reaction and adds it to a message.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent": {
                    "description": "Resource name of the message to which the reaction is added.\nFormat: \"spaces/{space}/messages/{message}\"",
                    "type": "string"
                },
                "reaction": {
                    "description": "The Reaction resource to create with fields:",
                    "type": "object",
                    "properties": {
                        "name": {
                            "description": "Identifier. The resource name of the reaction.",
                            "type": "string"
                        },
                        "emoji": {
                            "description": "Emoji metadata for the reaction.",
                            "type": "object",
                            "properties": {
                                "unicode": {
                                    "description": "A basic emoji represented by a unicode string.",
                                    "type": "string"
                                },
                                "customEmoji": {
                                    "description": "Custom emoji details.",
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "description": "Identifier. Format: customEmojis/{customEmoji}",
                                            "type": "string"
                                        },
                                        "uid": {
                                            "description": "Unique key for the custom emoji.",
                                            "type": "string"
                                        },
                                        "emojiName": {
                                            "description": "User-defined emoji name.",
                                            "type": "string"
                                        },
                                        "temporaryImageUri": {
                                            "description": "Temporary image URL.",
                                            "type": "string"
                                        },
                                        "payload": {
                                            "description": "Payload containing emoji image.",
                                            "type": "object",
                                            "properties": {
                                                "fileContent": {
                                                    "description": "Image binary data.",
                                                    "type": "string"
                                                },
                                                "filename": {
                                                    "description": "Image file name (.png, .jpg, .gif).",
                                                    "type": "string"
                                                }
                                            },
                                            "required": [
                                                "fileContent",
                                                "filename"
                                            ]
                                        }
                                    },
                                    "required": [
                                        "name",
                                        "uid"
                                    ]
                                }
                            },
                            "required": [
                                "customEmoji"
                            ]
                        },
                        "user": {
                            "description": "User details.",
                            "type": "object",
                            "properties": {
                                "name": {
                                    "description": "Format: users/{user}",
                                    "type": "string"
                                },
                                "displayName": {
                                    "description": "User's display name.",
                                    "type": "string"
                                },
                                "domainId": {
                                    "description": "Workspace domain ID.",
                                    "type": "string"
                                },
                                "type": {
                                    "description": "Enum: TYPE_UNSPECIFIED, HUMAN, BOT",
                                    "type": "string"
                                },
                                "isAnonymous": {
                                    "description": "True if user is deleted or hidden.",
                                    "type": "boolean"
                                }
                            },
                            "required": [
                                "name",
                                "displayName",
                                "domainId",
                                "type",
                                "isAnonymous"
                            ]
                        }
                    },
                    "required": [
                        "name",
                        "emoji",
                        "user"
                    ]
                }
            },
            "required": [
                "parent",
                "reaction"
            ]
        }
    }
)
def create(
    parent: str,
    reaction: Dict[
        str,
        Union[
            str,
            bool,
            Dict[str, Union[str, bool, Optional[str], Dict[str, Union[str, Optional[str]]]]]
        ]
    ]
) -> Dict[
    str,
    Union[
        str,
        bool,
        Dict[
            str,
            Union[
                str,
                bool,
                Optional[str],
                Dict[str, Union[str, Optional[str]]]
            ]
        ]
    ]
]:
    """
    Creates a reaction and adds it to a message.

    Args:
        parent (str): Resource name of the message to which the reaction is added.
            Format: "spaces/{space}/messages/{message}"

        reaction (Dict[str, Union[str, bool, Dict[str, Union[str, bool, Optional[str], Dict[str, Union[str, Optional[str]]]]]]]): The Reaction resource to create with fields:
            - name (str): Identifier. The resource name of the reaction.
            - emoji (Dict[str, Union[str, Dict]]): Emoji metadata for the reaction.
                - unicode (Optional[str]): A basic emoji represented by a unicode string.
                - customEmoji (Dict[str, str]): Custom emoji details.
                    - name (str): Identifier. Format: customEmojis/{customEmoji}
                    - uid (str): Unique key for the custom emoji.
                    - emojiName (Optional[str]): User-defined emoji name.
                    - temporaryImageUri (Optional[str]): Temporary image URL.
                    - payload (Optional[Dict[str, str]]): Payload containing emoji image.
                        - fileContent (str): Image binary data.
                        - filename (str): Image file name (.png, .jpg, .gif).
            - user (Dict[str, Union[str, bool]]): User details.
                - name (str): Format: users/{user}
                - displayName (str): User's display name.
                - domainId (str): Workspace domain ID.
                - type (str): Enum: TYPE_UNSPECIFIED, HUMAN, BOT
                - isAnonymous (bool): True if user is deleted or hidden.

    Returns:
        Dict[str, Union[str, bool, Dict[str, Union[str, bool, Optional[str], Dict[str, Union[str, Optional[str]]]]]]]: A Dictionary representing the created Reaction resource with the following fields:
            - name (str): Resource name of the created reaction.
            - emoji (Dict[str, Any]):
                - unicode (str): If provided.
                - customEmoji (Dict[str, Any]):
                    - name (str)
                    - emojiName (str), if provided.
                    - uid (str): Output only. Generated unique identifier.
                    - temporaryImageUri (str): Output only. Temporary image URL.
            - user (Dict[str, Any]):
                - name (str): Required. Format: users/{user}
                - displayName (str): Output only. User's display name.
                - domainId (str): Output only. Workspace domain ID.
                - type (str): Enum: TYPE_UNSPECIFIED, HUMAN, BOT
                - isAnonymous (bool): Output only. True if user is deleted or hidden.

        Returns an empty Dict if the parent format is invalid or validation fails.
    Raises:
        TypeError: If argument parent is not string.
        InvalidParentFormatError: If parent argument is invalid.
    """

    # Validate parent format
    if not isinstance(parent, str):
        raise TypeError("Argument 'parent' must be a string.")

    if not re.match(r"^spaces/[^/]+/messages/[^/]+$", parent):
        raise InvalidParentFormatError(f"Invalid parent format: {parent}")

    # Validate reaction input using Pydantic
    try:
        validated_reaction = ReactionInput.model_validate(reaction)
    except ValidationError as e:
        return {}

    # Generate reaction ID and name
    new_id = str(len(DB["Reaction"]) + 1)
    reaction_name = f"{parent}/reactions/{new_id}"

    # Construct full reaction with Output-only fields
    new_reaction = {
        "name": reaction_name,
        "emoji": {},
        "user": {
            "name": validated_reaction.user.name,
            "displayName": f"User {validated_reaction.user.name.split('/')[-1]}",  # Simulated
            "domainId": "domain-id",  # Simulated
            "type": "HUMAN",  # Simulated
            "isAnonymous": False  # Simulated
        }
    }

    if validated_reaction.emoji.unicode:
        new_reaction["emoji"]["unicode"] = validated_reaction.emoji.unicode

    if validated_reaction.emoji.customEmoji:
        ce = validated_reaction.emoji.customEmoji
        new_reaction["emoji"]["customEmoji"] = {
            "name": ce.name,
            "emojiName": ce.emojiName,
            "uid": str(uuid.uuid4()),  # Simulated unique ID
            "temporaryImageUri": "https://example.com/temp-image.png",  # Simulated
            "payload": {
                "fileContent": ce.payload.fileContent,
                "filename": ce.payload.filename
            }
        }

    # Insert into DB
    DB["Reaction"].append(new_reaction)
    return new_reaction


@tool_spec(
    spec={
        'name': 'list_message_reactions',
        'description': 'Lists reactions to a message.',
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': "Required. The resource name of the message to list reactions for.\nFormat: \"spaces/{space}/messages/{message}\""
                },
                'pageSize': {
                    'type': 'integer',
                    'description': "Optional. Maximum number of reactions to return. \nDefaults to None (internally defaults to 25). Maximum value is 200."
                },
                'pageToken': {
                    'type': 'string',
                    'description': "Optional. Token from a previous list call to retrieve the next page.\nDefaults to None."
                },
                'filter': {
                    'type': 'string',
                    'description': "Optional. Filter reactions by emoji or user fields. Examples:\n- emoji.unicode = \"🙂\"\n- emoji.custom_emoji.uid = \"XYZ\"\n- user.name = \"users/USER123\"\n- (emoji.unicode = \"🙂\" OR emoji.unicode = \"👍\") AND user.name = \"users/USER123\"\nDefaults to None."
                }
            },
            'required': [
                'parent'
            ]
        }
    }
)
def list(
    parent: str,
    pageSize: Optional[int] = None,
    pageToken: Optional[str] = None,
    filter: Optional[str] = None,
) -> Dict[str, Union[str, List]]:
    """
    Lists reactions to a message.

    Args:
        parent (str): Required. The resource name of the message to list reactions for.
            Format: "spaces/{space}/messages/{message}"
        pageSize (Optional[int]): Optional. Maximum number of reactions to return. 
            Defaults to None (internally defaults to 25). Maximum value is 200.
        pageToken (Optional[str]): Optional. Token from a previous list call to retrieve the next page.
            Defaults to None.
        filter (Optional[str]): Optional. Filter reactions by emoji or user fields. Examples:
            - emoji.unicode = "🙂"
            - emoji.custom_emoji.uid = "XYZ"
            - user.name = "users/USER123"
            - (emoji.unicode = "🙂" OR emoji.unicode = "👍") AND user.name = "users/USER123"
            Defaults to None.

    Returns:
        Dict[str, Union[str, List]]: A Dictionary with the following structure:
            - reactions (List[Dict[str, Union[str, Dict]]]): List of Reaction resources, each including:
                - name (str): Resource name of the reaction.
                - user (Dict[str, Union[str, bool]]):
                    - name (str): Resource name of the user.
                    - displayName (str): Output only. User's display name.
                    - domainId (str): Output only. User's domain ID.
                    - type (str): Enum. User type: TYPE_UNSPECIFIED, HUMAN, BOT.
                    - isAnonymous (bool): Output only. Whether the user is anonymous.
                - emoji (Dict[str, Union[str, Dict[str, Union[str, Dict[str, str]]]]]):
                    - unicode (str): Optional. Unicode emoji.
                    - customEmoji (Dict[str, Union[str, Dict[str, str]]]):
                        - name (str): Identifier. Format: customEmojis/{customEmoji}
                        - uid (str): Output only. Unique key.
                        - emojiName (str): Optional. Custom name, must be formatted correctly.
                        - temporaryImageUri (str): Output only. Temporary image URI.
                        - payload (Dict[str, str]):
                            - fileContent (str): Required. Image binary data.
                            - filename (str): Required. File name (.png, .jpg, .gif).
            - nextPageToken (str, optional): Omitted if this is the last page.

    Raises:
        ValueError: If `parent` or `pageSize` have invalid values.
        TypeError: If `parent`, `pageSize`, `pageToken`, or `filter` have invalid types.
    """

    # Input validation
    if parent is None:
        raise ValueError("Argument 'parent' cannot be None.")
    if not isinstance(parent, str):
        raise TypeError(f"Argument 'parent' must be a string, got {type(parent).__name__}.")
    if not parent.strip():
        raise ValueError("Argument 'parent' cannot be empty or contain only whitespace.")
    # Validate parent format using regex
    if not re.match(r"^spaces/[^/]+/messages/[^/]+$", parent):
        raise ValueError(
            f"Invalid parent format: '{parent}'. Expected 'spaces/{{space}}/messages/{{message}}'"
        )

    if pageSize is not None:
        if not isinstance(pageSize, int):
            raise TypeError(
                f"Argument 'pageSize' must be an integer, got {type(pageSize).__name__}."
            )
        if pageSize < 0:
            raise ValueError("Argument 'pageSize' cannot be negative.")

    if pageToken is not None and not isinstance(pageToken, str):
        raise TypeError(
            f"Argument 'pageToken' must be a string, got {type(pageToken).__name__}."
        )

    if filter is not None and not isinstance(filter, str):
        raise TypeError(
            f"Argument 'filter' must be a string, got {type(filter).__name__}."
        )

    # Default pageSize
    if pageSize is None:
        pageSize = 25
    if pageSize > 200:
        pageSize = 200

    # parse pageToken => offset
    offset = 0
    if pageToken:
        try:
            off = int(pageToken)
            if off >= 0:
                offset = off
        except ValueError:
            # Inform the caller of an invalid pageToken format
            raise ValueError(f"Invalid pageToken value: '{pageToken}'. Expected an integer string.")

    # 1) collect all reactions for parent
    all_rxns = []
    for r in DB["Reaction"]:
        if r["name"].startswith(parent + "/reactions/"):
            all_rxns.append(r)

    # 2) apply filter if provided
    # The doc says we can do expressions like:
    #   user.name = "users/USERA" OR user.name = "users/USERB"
    #   emoji.unicode = "🙂" OR emoji.custom_emoji.uid = "XYZ"
    #   AND between user and emoji
    # We'll do a minimal approach:
    def _reaction_matches_filter(rxn: Dict[str, Any], tokens: List[str]) -> bool:
        """
        Parses filter tokens and determines if a reaction matches the filter criteria.
        
        This function evaluates filter expressions of the form "field = value" with
        support for AND/OR operators. It follows Google Chat API filtering rules:
        - OR operators can be used within the same field type
        - AND operators can be used between different field types
        - Supported fields: user.name, emoji.unicode, emoji.custom_emoji.uid
        
        Args:
            rxn (Dict[str, Any]): The reaction object to evaluate against the filter.
                Must contain 'user' and 'emoji' Dictionaries with appropriate fields.
            tokens (List[str]): The tokenized filter string split by whitespace.
                Expected format: ["field", "=", "\"value\"", "operator", "field", "=", "\"value\"", ...]
                Example: ["emoji.unicode", "=", "\"🙂\"", "AND", "user.name", "=", "\"users/USER111\""]
        
        Returns:
            bool: True if the reaction matches the filter criteria, False otherwise.
                Returns True for empty expression lists (no filtering applied).
        
        Raises:
            TypeError: If rxn is not a Dict or tokens is not a list.
            ValueError: If rxn or tokens is None.
        
        Note:
            This implementation handles basic filter parsing and does not support
            parentheses or complex nested expressions. Invalid filter syntax
            results in False being returned rather than raising exceptions.
        """
        # Input validation
        if rxn is None:
            raise ValueError("Argument 'rxn' cannot be None.")
        if tokens is None:
            raise ValueError("Argument 'tokens' cannot be None.")
        if not isinstance(rxn, Dict):
            raise TypeError("Argument 'rxn' must be a Dictionary.")
        if type(tokens).__name__ != 'list':
            raise TypeError("Argument 'tokens' must be a list.")
        
        # Handle empty tokens list
        if not tokens:
            return True
            
        # We'll parse out expressions of the form (field, "=", value) plus "AND"/"OR" in between.
        expressions = []
        operators = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t.upper() in ("AND", "OR"):
                operators.append(t.upper())
                i += 1
            else:
                # expect something like "field", "=", "\"value\""
                if i + 2 < len(tokens) and tokens[i + 1] == "=":
                    field = tokens[i]
                    val = tokens[i + 2].strip('"')
                    expressions.append((field, val))
                    i += 3
                else:
                    # invalid parse => raise error
                    raise ValueError(f"Invalid filter syntax near '{' '.join(tokens[i:])}'.")

        # We then interpret them in a naive way:
        # - For each expression, check if rxn satisfies it.
        # - If we see "AND", we require both. If we see "OR", we require either. The doc has constraints about grouping.
        # We'll do a simplistic approach:
        if not expressions:
            return True

        # We'll handle them in sequence: expression1 (operator) expression2 (operator) expression3 ...
        # For the doc: "OR" can appear among the same field type, "AND" can appear between different field types
        # We'll apply a partial approach: if any "OR", we treat them as "field matches any of these" if same field, or fail if different.

        # We'll group expressions by field to handle the doc's constraints (only OR within the same field).
        # Then AND across different fields. This is still simplistic but closer to the doc's rules.
        # e.g. user.name = "users/USER111" OR user.name = "users/USER222"
        # AND emoji.unicode = "🙂" OR emoji.unicode = "👍"

        # We'll transform expressions + operators into groups.
        # Example: [("emoji.unicode", "🙂"), OR, ("emoji.unicode", "👍"), AND, ("user.name", "users/USER111")]

        # We'll do a single pass to group by AND:
        groups = []  # each group is a list of expressions that are OR'ed together
        current_group = [expressions[0]]  # start
        for idx, op in enumerate(operators):
            expr = expressions[idx + 1]
            if op == "OR":
                # add to current group
                current_group.append(expr)
            elif op == "AND":
                # finish the current group, start a new group
                groups.append(current_group)
                current_group = [expr]
            else:
                # unknown => skip
                raise ValueError(f"Unsupported operator '{op}' in filter expression.")
        # add last group
        groups.append(current_group)

        # Now we have groups of OR expressions, we require each group to match (AND).
        # e.g. group1 => [("emoji.unicode","🙂"),("emoji.unicode","👍")] => means rxn must have emoji.unicode that is either "🙂" or "👍"
        # group2 => [("user.name","users/USER111")] => must match as well
        for group in groups:
            # They all share the same field or doc says "OR with same field"? We'll allow them to share the same field or be different, but doc focuses on same field for OR. We'll do an "OR" check among them.
            matched_this_group = False
            for field, val in group:
                if _matches_expression(rxn, field, val):
                    matched_this_group = True
                    break
            if not matched_this_group:
                return False

        return True

    def _matches_expression(rxn: Dict, field: str, val: str) -> bool:
        """
        Check if a single reaction satisfies a specific field expression.
        
        This function evaluates whether a reaction object matches a given field-value
        expression used in Google Chat API filtering, such as user.name = "users/USER111",
        emoji.unicode = "🙂", or emoji.custom_emoji.uid = "ABC".
        
        Args:
            rxn (Dict): The reaction object to evaluate with expected structure:
                - user (Dict): User information containing:
                    - name (str): User resource name in format "users/{user}"
                    - displayName (str): User's display name  
                    - domainId (str): User's domain ID
                    - type (str): User type (TYPE_UNSPECIFIED, HUMAN, BOT)
                    - isAnonymous (bool): Whether user is anonymous
                - emoji (Dict): Emoji information containing:
                    - unicode (str): Optional. Unicode emoji string
                    - custom_emoji (Dict): Optional. Custom emoji with:
                        - uid (str): Unique identifier for custom emoji
                        - name (str): Custom emoji resource name
                        - emojiName (str): Display name of custom emoji
            field (str): The field path to check. Supported values:
                - "user.name": Matches against user resource name
                - "emoji.unicode": Matches against unicode emoji string  
                - "emoji.custom_emoji.uid": Matches against custom emoji UID
            val (str): The expected value to match against the specified field.
                Can be any string including empty string for filtering comparisons.
        
        Returns:
            bool: True if the reaction's specified field matches the given value,
                False if no match is found or if the field is not supported.
                Unknown fields gracefully return False for filtering compatibility.
        
        Raises:
            TypeError: If rxn is not a Dict, field is not a string, or val is not a string.
            ValueError: If rxn, field, or val is None, or if field is empty/whitespace.
        """
        # Input validation
        if rxn is None:
            raise ValueError("Argument 'rxn' cannot be None.")
        if field is None:
            raise ValueError("Argument 'field' cannot be None.")
        if val is None:
            raise ValueError("Argument 'val' cannot be None.")
        
        if not isinstance(rxn, Dict):
            raise TypeError(f"Argument 'rxn' must be a Dict, got {type(rxn).__name__}.")
        if not isinstance(field, str):
            raise TypeError(f"Argument 'field' must be a string, got {type(field).__name__}.")
        if not isinstance(val, str):
            raise TypeError(f"Argument 'val' must be a string, got {type(val).__name__}.")
        
        if not field.strip():
            raise ValueError("Argument 'field' cannot be empty or contain only whitespace.")
        # Note: val can be empty string for valid filtering comparisons
        
        # Field-specific matching with safe Dictionary access
        if field == "user.name":
            user_data = rxn.get("user")
            if not isinstance(user_data, Dict):
                return False
            return user_data.get("name") == val
        elif field == "emoji.unicode":
            emoji_data = rxn.get("emoji")
            if not isinstance(emoji_data, Dict):
                return False
            return emoji_data.get("unicode") == val
        elif field == "emoji.custom_emoji.uid":
            emoji_data = rxn.get("emoji")
            if not isinstance(emoji_data, Dict):
                return False
            custom_emoji_data = emoji_data.get("custom_emoji")
            if not isinstance(custom_emoji_data, Dict):
                return False
            return custom_emoji_data.get("uid") == val
        else:
            # Unknown field - return False (no match) for graceful filtering behavior
            return False

    if filter:
        # We'll parse a few patterns for demonstration.
        # Real logic would fully parse parentheses and multiple AND/OR expressions.
        # e.g. "emoji.unicode = \"🙂\" AND user.name = \"users/USER111\""
        # We'll handle basic ( X = "val" ) statements with AND or OR, ignoring parentheses.
        tokens = filter.split()
        # e.g. tokens => ["emoji.unicode", "=", "\"🙂\"", "AND", "user.name", "=", "\"users/USER111\""]
        # We'll do a naive pass
        filtered = []
        for rxn in all_rxns:
            if _reaction_matches_filter(rxn, tokens):
                filtered.append(rxn)
        all_rxns = filtered

    # 3) pagination
    total = len(all_rxns)
    end = offset + pageSize
    page_items = all_rxns[offset:end]
    next_token = None
    if end < total:
        next_token = str(end)

    # Build result
    result: Dict[str, Any] = {"reactions": page_items}
    if next_token:
        result["nextPageToken"] = next_token
    return result


@tool_spec(
    spec={
        'name': 'delete_message_reaction',
        'description': 'Deletes a reaction by its resource name.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': "Required. The resource name of the reaction to delete.\nFormat: \"spaces/{space}/messages/{message}/reactions/{reaction}\""
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def delete(name: str) -> Dict:
    """
    Deletes a reaction by its resource name.

    Args:
        name (str): Required. The resource name of the reaction to delete.
            Format: "spaces/{space}/messages/{message}/reactions/{reaction}"

    Returns:
        Dict: An empty Dictionary is always returned, regardless of whether the reaction
            was found and deleted or not. This does not indicate success or failure of
            the deletion operation - check the console output for actual status.

    Raises:
        TypeError: If name is not a string.
        ValueError: If name is None, empty, or does not match the required format.
    """
    # Input validation
    if name is None:
        raise ValueError("Argument 'name' cannot be None.")
    
    if not isinstance(name, str):
        raise TypeError(f"Argument 'name' must be a string, got {type(name).__name__}.")
    
    if not name.strip():
        raise ValueError("Argument 'name' cannot be empty or contain only whitespace.")
    
    # Validate format: "spaces/{space}/messages/{message}/reactions/{reaction}"
    parts = name.split("/")
    if (len(parts) != 6 or 
        parts[0] != "spaces" or 
        parts[2] != "messages" or 
        parts[4] != "reactions" or
        not parts[1] or  # space id
        not parts[3] or  # message id  
        not parts[5]):   # reaction id
        raise ValueError(
            f"Invalid name format: '{name}'. Expected format: "
            "'spaces/{{space}}/messages/{{message}}/reactions/{{reaction}}'"
        )

    # Find and remove from DB
    for r in DB["Reaction"]:
        if r.get("name") == name:
            DB["Reaction"].remove(r)
            return {}
    return {}
