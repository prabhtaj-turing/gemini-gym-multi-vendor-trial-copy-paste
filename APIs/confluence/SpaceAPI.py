from common_utils.tool_spec_decorator import tool_spec
# APIs/confluence/SpaceAPI.py
from typing import Dict, List, Any, Optional
from pydantic import ValidationError
from confluence.SimulationEngine.db import DB
from confluence.SimulationEngine.models import SpaceBodyInputModel


@tool_spec(
    spec={
        'name': 'get_spaces',
        'description': """ Returns a paginated list of all spaces.
        
        Retrieves a list of space dictionaries for the provided parameters. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'spaceKey': {
                    'type': 'string',
                    'description': """ A unique identifier to filter spaces by.
                    Must be a non-empty string if provided. Defaults to None. """
                },
                'start': {
                    'type': 'integer',
                    'description': """ The starting index for pagination.
                    Defaults to 0. """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of spaces to return.
                    Defaults to 25. """
                }
            },
            'required': []
        }
    }
)
def get_spaces(
        spaceKey: Optional[str] = None,
        start: int = 0,
        limit: int = 25,
) -> List[Dict[str, str]]:
    """
    Returns a paginated list of all spaces.

    Retrieves a list of space dictionaries for the provided parameters.

    Args:
        spaceKey (Optional[str]): A unique identifier to filter spaces by.
            Must be a non-empty string if provided. Defaults to None.
        start (int): The starting index for pagination.
            Defaults to 0.
        limit (int): The maximum number of spaces to return.
            Defaults to 25.

    Returns:
        List[Dict[str, str]]: A list of space dictionaries, each containing:
            - spaceKey (str): The unique identifier of the space.
            - name (str): The display name of the space.
            - description (str): A description of the space.

    Raises:
        TypeError: If spaceKey is provided and is not a string,
                   or if start or limit are not integers.
        ValueError: If spaceKey is empty or contains only whitespace,
                   or if the start or limit parameters are negative.
    """
    # --- Input Validation ---
    if spaceKey is not None and not isinstance(spaceKey, str):
        raise TypeError(f"spaceKey must be a string or None, got {type(spaceKey).__name__}")
    
    if spaceKey is not None and not spaceKey.strip():
        raise ValueError("spaceKey cannot be empty or contain only whitespace.")

    if not isinstance(start, int):
        raise TypeError(f"start must be an integer, got {type(start).__name__}")
    if start < 0:
        raise ValueError("start parameter cannot be negative.")

    if not isinstance(limit, int):
        raise TypeError(f"limit must be an integer, got {type(limit).__name__}")
    if limit < 0:
        raise ValueError("limit parameter cannot be negative.")
    # --- End Input Validation ---

    # Original core logic (assumes DB is accessible in this scope)
    all_spaces = list(DB["spaces"].values())
    if spaceKey:
        # In Confluence, spaceKey can be repeated, but let's do a simple approach:
        all_spaces = [s for s in all_spaces if s["spaceKey"] == spaceKey]

    return all_spaces[start: start + limit]


@tool_spec(
    spec={
        'name': 'create_space',
        'description': """ Creates a new space.
        
        Creates and returns a new space dictionary from the provided data. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'body': {
                    'type': 'object',
                    'description': 'A dictionary representing the properties for the new space:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Required. The display name of the space.'
                        },
                        'key': {
                            'type': 'string',
                            'description': 'The key for the space. Required if alias is not provided.'
                        },
                        'alias': {
                            'type': 'string',
                            'description': 'Used as identifier in Confluence page URLs. If not provided, key is used.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the space (optional)'
                        }
                    },
                    'required': [
                        'name'
                    ]
                }
            },
            'required': [
                'body'
            ]
        }
    }
)
def create_space(body: Dict[str, str | Optional[str]]) -> Dict[str, str]:
    """
    Creates a new space.

    Creates and returns a new space dictionary from the provided data.

    Args:
        body (Dict[str, str | Optional[str]]): A dictionary representing the properties for the new space:
            - name (str): Required. The display name of the space.
            - key (Optional[str]): The key for the space. Required if alias is not provided.
            - alias (Optional[str]): Used as identifier in Confluence page URLs. If not provided, key is used.
            - description (Optional[str]): The description of the space (optional)

    Returns:
        Dict[str, str]: A dictionary representing the newly created space containing:
            - spaceKey (str): The unique identifier of the space (mirrors body['key']).
            - name (str): The display name of the space.
            - description (str): The description of the space (empty string if not provided).

    Raises:
        pydantic.ValidationError: If the 'body' argument is not a valid dictionary or does not
                                  conform to the SpaceBodyInputModel (e.g., neither 'key' nor 'alias' provided).
        ValueError: If a space with the provided key/alias already exists.
    """
    try:
        validated_body_model = SpaceBodyInputModel.model_validate(body)
    except Exception as e:
        from confluence.SimulationEngine.custom_errors import ValidationError as CustomValidationError
        raise CustomValidationError(f"Invalid request body: {str(e)}")

    # Determine the space key: use key if provided, otherwise use alias
    spaceKey = validated_body_model.key or validated_body_model.alias

    # Set alias: if provided use it, otherwise use the key
    alias = validated_body_model.alias or validated_body_model.key

    if spaceKey in DB["spaces"]:
        raise ValueError(f"Space with key={spaceKey} already exists.")

    new_space = {
        "spaceKey": spaceKey,
        "name": validated_body_model.name,
        "description": validated_body_model.description or "",
    }
    DB["spaces"][spaceKey] = new_space
    return new_space


@tool_spec(
    spec={
        'name': 'create_private_space',
        'description': """ Creates a new private space.
        
        This function behaves identically to create_space and returns a new private space dictionary. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'body': {
                    'type': 'object',
                    'description': 'The properties required to create a new private space.',
                    'properties': {
                        'key': {
                            'type': 'string',
                            'description': 'The unique identifier for the space.'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'The display name of the space.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'An optional description of the space.'
                        }
                    },
                    'required': [
                        'key',
                        'name'
                    ]
                }
            },
            'required': [
                'body'
            ]
        }
    }
)
def create_private_space(body: Dict[str, Any]) -> Dict[str, str]:
    """
    Creates a new private space.

    This function behaves identically to create_space and returns a new private space dictionary.

    Args:
        body (Dict[str, Any]): The properties required to create a new private space.
            - key (str): The unique identifier for the space.
            - name (str): The display name of the space.
            - description (Optional[str]): An optional description of the space.

    Returns:
        Dict[str, str]: A dictionary representing the newly created private space containing:
            - spaceKey (str): The unique identifier of the space.
            - name (str): The display name of the space.
            - description (str): The description of the space (empty string if not provided).

    Raises:
        pydantic.ValidationError: If the 'body' argument is not a valid dictionary or does not
                                  conform to the SpaceBodyInputModel (e.g., 'key' is missing,
                                  or 'key', 'name', 'description' have incorrect types).
        ValueError: If a space with the provided key already exists.
    """
    try:
        validated_body_model = SpaceBodyInputModel.model_validate(body)
    except ValidationError as e:
        raise e

    spaceKey = validated_body_model.key
    if spaceKey in DB["spaces"]:
        raise ValueError(f"Space with key={spaceKey} already exists.")
    new_space = {
        "spaceKey": spaceKey,
        "name": validated_body_model.name,
        "description": validated_body_model.description or "",
    }
    DB["spaces"][spaceKey] = new_space
    return new_space


@tool_spec(
    spec={
        'name': 'update_space',
        'description': """ Updates an existing space.
        
        Updates and returns a space dictionary for the space specified by spaceKey. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'spaceKey': {
                    'type': 'string',
                    'description': 'The unique identifier of the space to update.'
                },
                'body': {
                    'type': 'object',
                    'description': "A data payload with the new values for the space's attributes.",
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The new display name of the space.'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The new description of the space.'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'spaceKey',
                'body'
            ]
        }
    }
)
def update_space(spaceKey: str, body: Dict[str, Any]) -> Dict[str, str]:
    """
    Updates an existing space.

    Updates and returns a space dictionary for the space specified by spaceKey.

    Args:
        spaceKey (str): The unique identifier of the space to update.
        body (Dict[str, Any]): A data payload with the new values for the space's attributes.
            - name (Optional[str]): The new display name of the space.
            - description (Optional[str]): The new description of the space.

    Returns:
        Dict[str, str]: A dictionary representing the updated space containing:
            - spaceKey (str): The unique identifier of the space.
            - name (str): The updated display name of the space.
            - description (str): The updated description of the space.

    Raises:
        ValueError: If no space with the specified spaceKey is found.
    """
    space = DB["spaces"].get(spaceKey)
    if not space:
        raise ValueError(f"Space with key={spaceKey} not found.")
    # Update fields
    if "name" in body:
        space["name"] = body["name"]
    if "description" in body:
        space["description"] = body["description"]
    # ignoring homepage for brevity
    DB["spaces"][spaceKey] = space
    return space


@tool_spec(
    spec={
        'name': 'delete_space',
        'description': """ Deletes a space and tracks the deletion task.
        
        Deletes the space identified by spaceKey and returns a task dictionary that tracks the deletion process.
        Note: The deletion task is marked as complete immediately. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'spaceKey': {
                    'type': 'string',
                    'description': 'The unique identifier of the space to delete.'
                }
            },
            'required': [
                'spaceKey'
            ]
        }
    }
)
def delete_space(spaceKey: str) -> Dict[str, str]:
    """
    Deletes a space and tracks the deletion task.

    Deletes the space identified by spaceKey and returns a task dictionary that tracks the deletion process.
    Note: The deletion task is marked as complete immediately.

    Args:
        spaceKey (str): The unique identifier of the space to delete.

    Returns:
        Dict[str, str]: A dictionary containing:
            - id (str): The task identifier.
            - spaceKey (str): The key of the space being deleted.
            - status (str): The current status of the deletion task ("in_progress" or "complete").
            - description (str): A description of the task.

    Raises:
        ValueError: If no space with the specified spaceKey is found.
    """
    if spaceKey not in DB["spaces"]:
        raise ValueError(f"Space with key={spaceKey} not found.")
    task_id = str(DB["long_task_counter"])
    DB["long_task_counter"] += 1
    DB["deleted_spaces_tasks"][task_id] = {
        "id": task_id,
        "spaceKey": spaceKey,
        "status": "in_progress",
        "description": f"Deleting space '{spaceKey}'",
    }
    # We'll pretend it completes immediately for this simulation:
    del DB["spaces"][spaceKey]
    DB["deleted_spaces_tasks"][task_id]["status"] = "complete"
    return DB["deleted_spaces_tasks"][task_id]

@tool_spec(
    spec={
        'name': 'get_space_details',
        'description': """ Retrieves details about a specific space.
        
        Returns the space dictionary for the provided spaceKey. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'spaceKey': {
                    'type': 'string',
                    'description': 'The unique identifier of the space.'
                }
            },
            'required': [
                'spaceKey'
            ]
        }
    }
)
def get_space(
    spaceKey: str
) -> Dict[str, str]:
    """
    Retrieves details about a specific space.

    Returns the space dictionary for the provided spaceKey.

    Args:
        spaceKey (str): The unique identifier of the space.

    Returns:
        Dict[str, str]: A dictionary representing the space containing:
            - spaceKey (str): The unique identifier of the space.
            - name (str): The display name of the space.
            - description (str): The description of the space.

    Raises:
        TypeError: If spaceKey is not a string.
        ValueError: If spaceKey is empty or contains only whitespace, or if no space with the specified spaceKey is found.
    """
    # Input validation
    if not isinstance(spaceKey, str):
        raise TypeError(f"spaceKey must be a string, but got {type(spaceKey).__name__}.")

    if not spaceKey.strip():
        raise ValueError("spaceKey cannot be empty or contain only whitespace.")

    space = DB["spaces"].get(spaceKey) # type: ignore
    if not space:
        raise ValueError(f"Space with key={spaceKey} not found.")
    return space

@tool_spec(
    spec={
        'name': 'get_space_content',
        'description': """ Retrieves the content within a specific space.
        
        Returns a list of content item dictionaries for the space identified by spaceKey.
        Note: The 'depth' and 'expand' parameters are included for API compatibility but are not fully implemented. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'spaceKey': {
                    'type': 'string',
                    'description': 'The unique identifier of the space. Must be a non-empty string.'
                },
                'depth': {
                    'type': 'string',
                    'description': 'The depth of content to retrieve. Defaults to None.'
                },
                'expand': {
                    'type': 'string',
                    'description': 'A comma-separated list of properties to expand. Defaults to None.'
                },
                'start': {
                    'type': 'integer',
                    'description': """ The starting index for pagination.
                    Defaults to 0. Must be a non-negative integer. """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of content items to return.
                    Defaults to 25. Must be a positive integer. """
                }
            },
            'required': [
                'spaceKey'
            ]
        }
    }
)
def get_space_content(
        spaceKey: str,
        depth: Optional[str] = None,
        expand: Optional[str] = None,
        start: int = 0,
        limit: int = 25,
) -> List[Dict[str, Any]]:
    """
    Retrieves the content within a specific space.

    Returns a list of content item dictionaries for the space identified by spaceKey.
    Note: The 'depth' and 'expand' parameters are included for API compatibility but are not fully implemented.

    Args:
        spaceKey (str): The unique identifier of the space. Must be a non-empty string.
        depth (Optional[str]): The depth of content to retrieve. Defaults to None.
        expand (Optional[str]): A comma-separated list of properties to expand. Defaults to None.
        start (int): The starting index for pagination.
            Defaults to 0. Must be a non-negative integer.
        limit (int): The maximum number of content items to return.
            Defaults to 25. Must be a positive integer.

    Returns:
        List[Dict[str, Any]]: A list of content item dictionaries, each containing:
            - id (str): The unique identifier of the content.
            - type (str): The type of content (e.g., "page", "blogpost").
            - title (str): The title of the content.
            - spaceKey (str): The key of the space containing the content.
            - status (str): The current status of the content.
            - body (Dict[str, Any]): A dictionary representing the content body data containing:
                  - storage (Dict[str, Any]): A dictionary with:
                        - value (str): The content value in storage format.
                        - representation (str): The representation type (e.g., "storage").
            - postingDay (Optional[str]): The posting day for blog posts.
            - link (str): The link to the content.
            - children (Optional[List[Dict[str, Any]]]): A list of child content items.
            - ancestors (Optional[List[Dict[str, Any]]]): A list of ancestor content items.

    Raises:
        TypeError: If 'spaceKey' is not a string.
        TypeError: If 'start' is not an integer.
        TypeError: If 'limit' is not an integer.
        ValueError: If 'spaceKey' is an empty string.
        ValueError: If 'start' is a negative integer.
        ValueError: If 'limit' is not a positive integer.
    """
    # --- Input Validation ---
    if not isinstance(spaceKey, str):
        raise TypeError("spaceKey must be a string.")
    if not spaceKey:
        raise ValueError("spaceKey must not be an empty string.")
    if not isinstance(start, int):
        raise TypeError("start must be an integer.")
    if start < 0:
        raise ValueError("start must be a non-negative integer.")
    if not isinstance(limit, int):
        raise TypeError("limit must be an integer.")
    if limit <= 0:
        raise ValueError("limit must be a positive integer.")

    all_contents = list(DB["contents"].values())
    results = [c for c in all_contents if c.get("spaceKey") == spaceKey]

    # Enrich each content item with _links.webui, children, and ancestors fields
    enriched_results = []
    for content in results[start : start + limit]:
        enriched_content = content.copy()

        # Add webui link to _links object (following official Confluence API structure)
        enriched_content["link"] = enriched_content.get("_links", {}).get("self", "")
        if "_links" in enriched_content:
            del enriched_content["_links"]
        # Add children field: find content items that have this item in their ancestors
        content_id = enriched_content["id"]
        children = []
        for other_content in all_contents:
            if "ancestors" in other_content:
                for ancestor in other_content["ancestors"]:
                    if ancestor.get("id") == content_id:
                        children.append({
                            "id": other_content["id"],
                            "type": other_content.get("type"),
                            "title": other_content.get("title")
                        })
                        break
        enriched_content["children"] = children if children else None

        # Ensure ancestors field exists (keep existing or set to None)
        if "ancestors" not in enriched_content:
            enriched_content["ancestors"] = None

        enriched_results.append(enriched_content)

    return enriched_results

@tool_spec(
    spec={
        'name': 'get_space_content_by_type',
        'description': """ Retrieves content of a specific type within a space.
        
        Returns a list of content item dictionaries matching the specified type for the given spaceKey.
        Note: The function first retrieves all content for the space and then filters by type.
              The 'depth' and 'expand' parameters are accepted for API compatibility but are not fully implemented. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'spaceKey': {
                    'type': 'string',
                    'description': 'The unique identifier of the space.'
                },
                'depth': {
                    'type': 'string',
                    'description': 'The depth of content to retrieve. Defaults to None.'
                },
                'expand': {
                    'type': 'string',
                    'description': 'A comma-separated list of properties to expand. Defaults to None.'
                },
                'type': {
                    'type': 'string',
                    'description': 'The type of content to filter (e.g., "page", "blogpost").'
                },
                'start': {
                    'type': 'integer',
                    'description': """ The starting index for pagination after filtering.
                    Defaults to 0. """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of content items to return after filtering.
                    Defaults to 25. """
                }
            },
            'required': [
                'spaceKey',
                'type'
            ]
        }
    }
)
def get_space_content_of_type(
    spaceKey: str,
    type: str,
    depth: Optional[str] = None,
    expand: Optional[str] = None,
    start: int = 0,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    """
    Retrieves content of a specific type within a space.

    Returns a list of content item dictionaries matching the specified type for the given spaceKey.
    Note: The function first retrieves all content for the space and then filters by type.
          The 'depth' and 'expand' parameters are accepted for API compatibility but are not fully implemented.

    Args:
        spaceKey (str): The unique identifier of the space.
        depth (Optional[str]): The depth of content to retrieve. Defaults to None.
        expand (Optional[str]): A comma-separated list of properties to expand. Defaults to None.
        type (str): The type of content to filter (e.g., "page", "blogpost").
        start (int): The starting index for pagination after filtering.
            Defaults to 0.
        limit (int): The maximum number of content items to return after filtering.
            Defaults to 25.

    Returns:
        List[Dict[str, Any]]: A list of content item dictionaries, each containing:
            - id (str): The unique identifier of the content.
            - type (str): The type of content.
            - title (str): The title of the content.
            - spaceKey (str): The key of the space containing the content.
            - status (str): The current status of the content.
            - body (Dict[str, Any]): A dictionary representing the content body data containing:
                  - storage (Dict[str, Any]): A dictionary with:
                        - value (str): The content value in storage format.
                        - representation (str): The representation type (e.g., "storage").
            - postingDay (Optional[str]): The posting day for blog posts.
            - link (str): The link to the content.
            - children (Optional[List[Dict[str, Any]]]): A list of child content items.
            - ancestors (Optional[List[Dict[str, Any]]]): A list of ancestor content items.

    Raises:
        TypeError: 
            - If 'spaceKey' is not a string.
            - If 'type' is not a string.
            - If 'start' is not an integer.
            - If 'limit' is not an integer.
        ValueError: 
            - If 'spaceKey' is an empty string.
            - If 'type' is an empty string.
            - If 'start' is a negative integer.
            - If 'limit' is not a positive integer.
    """
    # --- Input Validation ---
    if not isinstance(spaceKey, str):
        raise TypeError("spaceKey must be a string.")
    if not spaceKey:
        raise ValueError("spaceKey must not be an empty string.")

    if not isinstance(type, str):
        raise TypeError("type must be a string.")
    if not type:
        raise ValueError("type must not be an empty string.")

    if not isinstance(start, int):
        raise TypeError("start must be an integer.")
    if start < 0:
        raise ValueError("start must be a non-negative integer.")

    if not isinstance(limit, int):
        raise TypeError("limit must be an integer.")
    if limit <= 0:
        raise ValueError("limit must be a positive integer.")
    # --- End Input Validation ---

    # Get all contents and filter by space first
    all_contents = list(DB["contents"].values())
    space_contents = [c for c in all_contents if c.get("spaceKey") == spaceKey]

    # Then filter by type
    filtered = [c for c in space_contents if c.get("type") == type]

    # Enrich each content item with _links.webui, children, and ancestors fields
    enriched_results = []
    for content in filtered[start : start + limit]:
        enriched_content = content.copy()

        # Add webui link to _links object (following official Confluence API structure)
        enriched_content["link"] = enriched_content.get("_links", {}).get("self", "")
        if "_links" in enriched_content:
            del enriched_content["_links"]

        # Add children field: find content items that have this item in their ancestors
        content_id = enriched_content["id"]
        children = []
        for other_content in all_contents:
            if "ancestors" in other_content:
                for ancestor in other_content["ancestors"]:
                    if ancestor.get("id") == content_id:
                        children.append({
                            "id": other_content["id"],
                            "type": other_content.get("type"),
                            "title": other_content.get("title")
                        })
                        break
        enriched_content["children"] = children if children else None

        # Ensure ancestors field exists (keep existing or set to None)
        if "ancestors" not in enriched_content:
            enriched_content["ancestors"] = None

        enriched_results.append(enriched_content)

    return enriched_results
