from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
from typing import Optional, Dict, Any, Union, Literal

from pydantic import ValidationError

from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..SimulationEngine.models import LabelInputModel
from ..SimulationEngine.utils import _resolve_user_id, _next_counter
from ..SimulationEngine import custom_errors

@tool_spec(
    spec={
        'name': 'create_label',
        'description': """ Creates a new label.
        
        Generates a unique ID for the new label and adds it to the user's list
        of labels in the database. The label properties are taken from the `label`
        argument. If no properties are provided, default values are used. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'label': {
                    'type': 'object',
                    'description': """ An optional dictionary containing the properties for the new label.
                    If provided, may contain the following keys (all optional): """,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The display name of the label.'
                        },
                        'messageListVisibility': {
                            'type': 'string',
                            'description': """ The visibility of messages with this label.
                                 Defaults to 'show'. Must be one of: 'show', 'hide'. """
                        },
                        'labelListVisibility': {
                            'type': 'string',
                            'description': """ The visibility of the label in the label list.
                                 Defaults to 'labelShow'. Must be one of: 'labelShow', 'labelShowIfUnread', 'labelHide'. """
                        },
                        'type': {
                            'type': 'string',
                            'description': "The owner type. Defaults to 'user'. Must be 'user' for custom labels."
                        },
                        'color': {
                            'type': 'object',
                            'description': 'The color to assign to the label. If provided, must contain both:',
                            'properties': {
                                'textColor': {
                                    'type': 'string',
                                    'description': 'The text color of the label, represented as a hex string.'
                                },
                                'backgroundColor': {
                                    'type': 'string',
                                    'description': 'The background color represented as a hex string #RRGGBB.'
                                }
                            },
                            'required': [
                                'textColor',
                                'backgroundColor'
                            ]
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def create(
    userId: str = "me", label: Optional[Dict[str, Union[str, Literal['show', 'hide'], Literal['labelShow', 'labelShowIfUnread', 'labelHide'], Literal['user'], Dict[str, str]]]] = None
) -> Dict[str, Union[str, int, Dict[str, str]]]:
    """Creates a new label.

    Generates a unique ID for the new label and adds it to the user's list
    of labels in the database. The label properties are taken from the `label`
    argument. If no properties are provided, default values are used.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        label (Optional[Dict[str, Union[str, Literal['show', 'hide'], Literal['labelShow', 'labelShowIfUnread', 'labelHide'], Literal['user'], Dict[str, str]]]]): An optional dictionary containing the properties for the new label.
            If provided, may contain the following keys (all optional):
            - 'name' (Optional[str]): The display name of the label.
            - 'messageListVisibility' (Optional[str]): The visibility of messages with this label.
                Defaults to 'show'. Must be one of: 'show', 'hide'.
            - 'labelListVisibility' (Optional[str]): The visibility of the label in the label list.
                Defaults to 'labelShow'. Must be one of: 'labelShow', 'labelShowIfUnread', 'labelHide'.
            - 'type' (Optional[str]): The owner type. Defaults to 'user'. Must be 'user' for custom labels.
            - 'color' (Optional[Dict[str, str]]): The color to assign to the label. If provided, must contain both:
                - 'textColor' (str): The text color of the label, represented as a hex string.
                - 'backgroundColor' (str): The background color represented as a hex string #RRGGBB.

    Returns:
        Dict[str, Union[str, int, Dict[str, str]]]: A dictionary representing the created label resource with keys:
            - 'id' (str): The immutable ID of the label.
            - 'name' (str): The display name of the label.
            - 'messageListVisibility' (str): The visibility of messages with this label in the message list.
            - 'labelListVisibility' (str): The visibility of the label in the label list.
            - 'type' (str): The owner type for the label.
            - 'messagesTotal' (int): The total number of messages with the label.
            - 'messagesUnread' (int): The number of unread messages with the label.
            - 'threadsTotal' (int): The total number of threads with the label.
            - 'threadsUnread' (int): The number of unread threads with the label.
            - 'color' (Dict[str, str]): The color assigned to the label.

    Raises:
        TypeError: If `userId` is not a string or label is not a dictionary.
        ValidationError: If the `label` argument is provided and does not conform to the
                                  LabelInputModel structure (e.g., invalid types for keys,
                                  missing required fields in 'color' sub-dictionary, or invalid
                                  enum values for visibility or type fields).
        ValueError: If the specified `userId` does not exist in the database.
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError("userId must be a string.")
    if not userId.strip():
        raise custom_errors.ValidationError(f"Argument 'userId' cannot have only whitespace.")
    if " " in userId:
        raise custom_errors.ValidationError(f"Argument 'userId' cannot have whitespace.")
    if label is None:
        label = {}
    if not isinstance(label, dict):
        raise TypeError("label must be a dictionary.")

    try:
        # Pydantic validates structure, types, and enum values.
        # Defaults from LabelInputModel are applied if keys are missing from `label` or if `label` is None.
        validated_label_data = LabelInputModel(**(label or {}))
    except ValidationError as e:
        # Re-raise Pydantic's ValidationError.
        # It could be caught and re-raised as a custom error type if desired.
        raise e

    # --- Core Function Logic (preserved and adapted) ---
    # Resolve userId to actual database key (also validates user exists)
    resolved_user_id = _resolve_user_id(userId)
    label_id_num = _next_counter("label")
    label_id = f"Label_{label_id_num}"

    # Determine values for new_label using validated data
    # For 'name', apply dynamic default if not provided in input
    name_value = validated_label_data.name
    if name_value is None:
        name_value = f"Label_{label_id_num}"

    # For 'color', always return a dictionary (never None) to match return type contract
    # If color data was provided and valid, use it; otherwise default to empty dict
    final_color_value: Dict[str, str]
    if validated_label_data.color: # Color data was provided and valid
        final_color_value = validated_label_data.color.model_dump()
    elif label is not None and "color" in label and label.get("color") is None: # Input explicitly had "color": null
        final_color_value = {}
    else: # Input `label` was None, or `label` was an empty dict, or `label` did not contain a "color" key.
          # In these cases, original logic `label.get("color", {})` would result in `{}`.
        final_color_value = {}

    new_label = {
        "id": label_id,
        "name": name_value,
        "messageListVisibility": validated_label_data.messageListVisibility,
        "labelListVisibility": validated_label_data.labelListVisibility,
        "type": validated_label_data.type,
        "messagesTotal": 0,
        "messagesUnread": 0,
        "threadsTotal": 0,
        "threadsUnread": 0,
        "color": final_color_value,
    }

    # Store the label in the database using resolved user ID
    DB["users"][resolved_user_id]["labels"][label_id] = new_label


    return new_label


@tool_spec(
    spec={
        'name': 'delete_label',
        'description': """ Immediately and permanently deletes the specified label.
        
        Removes the label identified by the given ID from the user's list of labels.
        This operation cannot be undone. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'id': {
                    'type': 'string',
                    'description': "The ID of the label to delete. Defaults to ''."
                }
            },
            'required': []
        }
    }
)
def delete(userId: str = "me", id: str = "") -> None:
    """Immediately and permanently deletes the specified label.

    Removes the label identified by the given ID from the user's list of labels.
    This operation cannot be undone.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        id (str): The ID of the label to delete. Defaults to ''.

    Returns:
        None.

    Raises:
        TypeError: If `userId` or `id` is not a string.
        ValidationError: If `userId` or `id` are not valid.
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError(f"userId must be a string, but got {type(userId).__name__}.")
    if not isinstance(id, str):
        raise TypeError(f"id must be a string, but got {type(id).__name__}.")
    if not userId.strip():
        raise custom_errors.ValidationError(f"Argument 'userId' cannot have only whitespace.")
    if " " in userId:
        raise custom_errors.ValidationError(f"Argument 'userId' cannot have whitespace.")
    if " " in id:
        raise custom_errors.ValidationError(f"Argument 'id' cannot have whitespace.")

    resolved_user_id = _resolve_user_id(userId)
    
    # Check if label exists and if it's a system label
    existing_label = DB["users"][resolved_user_id]["labels"].get(id)
    if existing_label and existing_label.get("type") == "system":
        raise custom_errors.ValidationError(f"Cannot delete system label '{id}'. System labels are read-only.")
    
    DB["users"][resolved_user_id]["labels"].pop(id, None)
    return None


@tool_spec(
    spec={
        'name': 'get_label',
        'description': """ Gets the specified label.
        
        Retrieves the label resource identified by the given ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'id': {
                    'type': 'string',
                    'description': "The ID of the label to retrieve. Defaults to ''."
                }
            },
            'required': []
        }
    }
)
def get(userId: str = "me", id: str = "") -> Optional[Dict[str, Any]]:
    """Gets the specified label.

    Retrieves the label resource identified by the given ID.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        id (str): The ID of the label to retrieve. Defaults to ''.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the label resource if found with keys:
            - 'id' (str): The unique identifier of the label.
            - 'name' (str): The display name of the label.
            - 'labelListVisibility' (str): The visibility of the label in the label list.
            - 'messageListVisibility' (str): The visibility of the label in the message list.
            - 'type' (str): The owner type for the label.
            - 'messagesTotal' (int): The total number of messages with the label.
            - 'messagesUnread' (int): The number of unread messages with the label.
            - 'threadsTotal' (int): The total number of threads with the label.
            - 'threadsUnread' (int): The number of unread threads with the label.
            - 'color' (Dict[str, str]): The color assigned to the label.
            Returns None if the label is not found.

    Raises:
        TypeError: If `userId` or `id` is not a string.
        ValidationError: If `userId` or `id` are not valid.
    """
    # --- Input Validation ---
    if not isinstance(userId, str):
        raise TypeError(f"userId must be a string, but got {type(userId).__name__}.")
    if not isinstance(id, str):
        raise TypeError(f"id must be a string, but got {type(id).__name__}.")
    if not userId.strip():
        raise custom_errors.ValidationError(f"Argument 'userId' cannot have only whitespace.")
    if any(c.isspace() for c in userId):
        raise custom_errors.ValidationError(f"Argument 'userId' cannot have whitespace.")
    if any(c.isspace() for c in id):
        raise custom_errors.ValidationError(f"Argument 'id' cannot have whitespace.")

    resolved_user_id = _resolve_user_id(userId)
    return DB["users"][resolved_user_id]["labels"].get(id)


@tool_spec(
    spec={
        'name': 'list_labels',
        'description': """ Lists all labels in the user's mailbox.
        
        Retrieves a list of all label resources associated with the specified user. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                }
            },
            'required': []
        }
    }
)
def list(userId: str = "me") -> Dict[str, Any]:
    """Lists all labels in the user's mailbox.

    Retrieves a list of all label resources associated with the specified user.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.

    Returns:
        Dict[str, Any]: A dictionary containing a list of label resources with keys:
            - labels (List[Dict[str, Any]]): List of label dictionaries, each containing:
                - id: The unique identifier of the label.
                - name: The display name of the label.
                - messageListVisibility: The visibility of messages with this label in the message list.
                - labelListVisibility: The visibility of the label in the label list.
                - type: The owner type for the label.
                - messagesTotal: The total number of messages with the label.
                - messagesUnread: The number of unread messages with the label.
                - threadsTotal: The total number of threads with the label.
                - threadsUnread: The number of unread threads with the label.
                - color: The color assigned to the label.

    Raises:
        TypeError: If `userId` is not a string.
        ValidationError: If `userId` is empty or contains only whitespace or whitespace.
    """
    # Input Validation
    if not isinstance(userId,str):
        raise TypeError(f"userId must be a string, but got {type(userId).__name__}.")
    if not userId:
        raise custom_errors.ValidationError(f"userId cannot be empty.")
    if not userId.strip():
        raise custom_errors.ValidationError(f"userId cannot have only whitespace.")
    if " " in userId:
        raise custom_errors.ValidationError(f"userId cannot have whitespace.")
    
    resolved_user_id = _resolve_user_id(userId)
    
    # Get the labels dictionary for the user
    user_data = DB["users"][resolved_user_id]
    if "labels" not in user_data:
        return {"labels": []}
        
    # Get the labels dictionary and convert to list
    labels_dict = user_data["labels"]
    # Convert dictionary values to list, ensuring we get all labels
    labels_list = []
    for label_id, label_data in labels_dict.items():
        # Ensure we have all required fields
        label = {
            "id": label_id,
            "name": label_data.get("name", ""),
            "messageListVisibility": label_data.get("messageListVisibility", "show"),
            "labelListVisibility": label_data.get("labelListVisibility", "labelShow"),
            "type": label_data.get("type", "user"),
            "messagesTotal": label_data.get("messagesTotal", 0),
            "messagesUnread": label_data.get("messagesUnread", 0),
            "threadsTotal": label_data.get("threadsTotal", 0),
            "threadsUnread": label_data.get("threadsUnread", 0),
            "color": label_data.get("color", {})
        }
        labels_list.append(label)
    return {"labels": labels_list}

@tool_spec(
    spec={
        'name': 'update_label',
        'description': """ Updates the specified label.
        
        Modifies an existing label identified by its ID using the properties
        provided in the label argument. This performs a full update, replacing
        the existing label properties with the new ones. Because this is a full
        update, the `label` dictionary must contain all required fields. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'id': {
                    'type': 'string',
                    'description': "The ID of the label to update. Defaults to ''."
                },
                'label': {
                    'type': 'object',
                    'description': """ A label resource object with the full set of updated properties.
                    The following keys are required:
                    If `label` is None, the existing label will be returned without modification. """,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The new display name for the label.'
                        },
                        'labelListVisibility': {
                            'type': 'string',
                            'description': """ The new visibility of the label in the label list.
                                 Must be one of: 'labelShow', 'labelShowIfUnread', 'labelHide'. """
                        },
                        'messageListVisibility': {
                            'type': 'string',
                            'description': """ The new visibility of the label in the message list.
                                 Must be one of: 'show', 'hide'. """
                        },
                        'type': {
                            'type': 'string',
                            'description': """ The owner type for the label. Must be 'user' for custom labels.
                                 System labels cannot have their type changed. """
                        },
                        'color': {
                            'type': 'object',
                            'description': 'The color to assign to the label. If provided, it must contain:',
                            'properties': {
                                'textColor': {
                                    'type': 'string',
                                    'description': 'The text color of the label, represented as a hex string #RRGGBB. Must be a valid hex color.'
                                },
                                'backgroundColor': {
                                    'type': 'string',
                                    'description': 'The background color represented as a hex string #RRGGBB. Must be a valid hex color.'
                                }
                            },
                            'required': [
                                'textColor',
                                'backgroundColor'
                            ]
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def update(
    userId: str = "me", id: str = "", label: Optional[Dict[str, Union[str, Literal['show', 'hide'], Literal['labelShow', 'labelShowIfUnread', 'labelHide'], Literal['user'], Dict[str, str]]]] = None
) -> Dict[str, Union[str, Literal['labelShow', 'labelShowIfUnread', 'labelHide'], Literal['show', 'hide'], Literal['user'], int, Optional[Dict[str, str]]]]:
    """Updates the specified label.

    Modifies an existing label identified by its ID using the properties
    provided in the label argument. This performs a full update, replacing
    the existing label properties with the new ones. Because this is a full
    update, the `label` dictionary must contain all required fields.

    Args:
        userId (str): The user's email address. The special value 'me'
            can be used to indicate the authenticated user. Defaults to 'me'.
        id (str): The ID of the label to update. Defaults to ''.
        label (Optional[Dict[str, Union[str, Literal['show', 'hide'], Literal['labelShow', 'labelShowIfUnread', 'labelHide'], Literal['user'], Dict[str, str]]]]): A label resource object with the full set of updated properties.
            The following keys are required:
            - 'name' (Optional[str]): The new display name for the label.
            - 'labelListVisibility' (Optional[Literal['labelShow', 'labelShowIfUnread', 'labelHide']]): The new visibility of the label in the label list.
                Must be one of: 'labelShow', 'labelShowIfUnread', 'labelHide'.
            - 'messageListVisibility' (Optional[Literal['show', 'hide']]): The new visibility of the label in the message list.
                Must be one of: 'show', 'hide'.
            - 'type' (Optional[Literal['user']]): The owner type for the label. Must be 'user' for custom labels.
                System labels cannot have their type changed.
            - 'color' (Optional[Dict[str, str]]): The color to assign to the label. If provided, it must contain:
                - 'textColor' (str): The text color of the label, represented as a hex string #RRGGBB. Must be a valid hex color.
                - 'backgroundColor' (str): The background color represented as a hex string #RRGGBB.
            If `label` is None, the existing label will be returned without modification.

    Returns:
        Dict[str, Union[str, Literal['labelShow', 'labelShowIfUnread', 'labelHide'], Literal['show', 'hide'], Literal['user'], int, Optional[Dict[str, str]]]]: A dictionary representing the updated label resource with keys:
            - 'id' (str): The unique identifier of the label.
            - 'name' (str): The display name of the label.
            - 'labelListVisibility' (Literal['labelShow', 'labelShowIfUnread', 'labelHide']): The visibility of the label in the label list.
                Must be one of: 'labelShow', 'labelShowIfUnread', 'labelHide'.
            - 'messageListVisibility' (Literal['show', 'hide']): The visibility of the label in the message list.
                Must be one of: 'show', 'hide'.
            - 'type' (Literal['user']): The owner type for the label.
            - 'messagesTotal' (int): The total number of messages with the label.
            - 'messagesUnread' (int): The number of unread messages with the label.
            - 'threadsTotal' (int): The total number of threads with the label.
            - 'threadsUnread' (int): The number of unread threads with the label.
            - 'color' (Optional[Dict[str, str]]): The color assigned to the label with keys:
                - 'textColor' (str): The text color of the label, represented as hex string.
                - 'backgroundColor' (str): The background color represented as hex string #RRGGBB.
                Can be None if no color is assigned.

    Raises:
        TypeError: If userId, id are not strings, or if label is provided but not a dictionary.
        ValueError: If userId is empty or contains whitespace, or if id is empty or the specified userId does not exist in the database
        ValidationError: 
            - If the provided label dictionary contains invalid values for
                labelListVisibility, messageListVisibility, or has invalid color structure.
            - If the provided label dictionary contains an invalid type for the 'type' field.
                Must be 'user' (can't edit system labels).
            - If the provided label dictionary contains an invalid textColor or backgroundColor.
                Must be a valid hex color.
        NotFoundError: If the label with the specified id is not found.
    """
    if not isinstance(userId, str):
        raise TypeError("userId must be a string.")
    if not isinstance(id, str):
        raise TypeError("id must be a string.")
    
    if not userId.strip():
        raise ValueError("userId cannot be empty or contain only whitespace.")
    if " " in userId:
        raise ValueError("userId cannot contain whitespace.")
    if not id.strip():
        raise ValueError("id cannot be empty or contain only whitespace.")
    if " " in id:
        raise ValueError("id cannot contain whitespace.")
    
    if label is not None and not isinstance(label, dict):
        raise TypeError("label must be a dictionary when provided.")
    
    resolved_user_id = _resolve_user_id(userId)
    
    existing = DB["users"][resolved_user_id]["labels"].get(id)
    if not existing:
        raise custom_errors.NotFoundError(f"Label with id '{id}' not found.")
    
    # System labels are read-only and cannot be modified
    if existing.get("type") == "system":
        raise custom_errors.ValidationError(f"Cannot modify system label '{id}'. System labels are read-only.")

    if label is None:
        return existing
    
    try:
        validated_label_data = LabelInputModel(**label)
    except ValidationError as e:
        raise e
    
    name_value = validated_label_data.name
    
    updated_label = {
        "id": existing["id"],
        "name": name_value if name_value is not None else existing.get("name"),
        "messageListVisibility": validated_label_data.messageListVisibility,
        "labelListVisibility": validated_label_data.labelListVisibility,
        "type": validated_label_data.type,
        "messagesTotal": existing.get("messagesTotal", 0),
        "messagesUnread": existing.get("messagesUnread", 0),
        "threadsTotal": existing.get("threadsTotal", 0),
        "threadsUnread": existing.get("threadsUnread", 0),
        "color": validated_label_data.color.model_dump() if validated_label_data.color else existing.get("color", {})
    }
    
    DB["users"][resolved_user_id]["labels"][id] = updated_label
    
    return updated_label


@tool_spec(
    spec={
        'name': 'patch_label',
        'description': """ Updates the specified label. Note: This function is an alias for `update`.
        
        Despite the name `patch`, this function performs a **full update**,
        replacing the existing label properties with the new ones provided. It
        does not perform a partial update. For details on arguments and behavior,
        see the `update` function. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'id': {
                    'type': 'string',
                    'description': "The ID of the label to update/patch. Defaults to ''."
                },
                'label': {
                    'type': 'object',
                    'description': """ A label resource object with the full set of updated properties.
                    The following keys are required:
                    If `label` is None, the existing label will be returned without modification. """,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'The new display name for the label.'
                        },
                        'labelListVisibility': {
                            'type': 'string',
                            'description': """ The new visibility of the label in the label list.
                                 Must be one of: 'labelShow', 'labelShowIfUnread', 'labelHide'. """
                        },
                        'messageListVisibility': {
                            'type': 'string',
                            'description': """ The new visibility of the label in the message list.
                                 Must be one of: 'show', 'hide'. """
                        },
                        'type': {
                            'type': 'string',
                            'description': """ The owner type for the label. Must be 'user' for custom labels.
                                 System labels cannot have their type changed. """
                        },
                        'color': {
                            'type': 'object',
                            'description': 'The color to assign to the label. If provided, it must contain:',
                            'properties': {
                                'textColor': {
                                    'type': 'string',
                                    'description': 'The text color of the label, represented as a hex string.'
                                },
                                'backgroundColor': {
                                    'type': 'string',
                                    'description': 'The background color represented as a hex string #RRGGBB.'
                                }
                            },
                            'required': [
                                'textColor',
                                'backgroundColor'
                            ]
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def patch(
    userId: str = "me", id: str = "", label: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Updates the specified label. Note: This function is an alias for `update`.

    Despite the name `patch`, this function performs a **full update**,
    replacing the existing label properties with the new ones provided. It
    does not perform a partial update. For details on arguments and behavior,
    see the `update` function.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        id (str): The ID of the label to update/patch. Defaults to ''.
        label (Optional[Dict[str, Any]]): A label resource object with the full set of updated properties.
            The following keys are required:
            - 'name' (Optional[str]): The new display name for the label.
            - 'labelListVisibility' (Optional[str]): The new visibility of the label in the label list.
                Must be one of: 'labelShow', 'labelShowIfUnread', 'labelHide'.
            - 'messageListVisibility' (Optional[str]): The new visibility of the label in the message list.
                Must be one of: 'show', 'hide'.
            - 'type' (Optional[str]): The owner type for the label. Must be 'user' for custom labels.
                System labels cannot have their type changed.
            - 'color' (Optional[Dict[str, str]]): The color to assign to the label. If provided, it must contain:
                - 'textColor' (str): The text color of the label, represented as a hex string #RRGGBB. Must be a valid hex color.
                - 'backgroundColor' (str): The background color represented as a hex string #RRGGBB. Must be a valid hex color.
            If `label` is None, the existing label will be returned without modification.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the updated label resource.
            Returns None if the label with the specified ID is not found.

    Raises:
        TypeError: If `userId` or `id` is not a string.
        ValueError: If `id` is an empty string or if the specified `userId` does not exist.
        ValidationError: If the `label` argument is provided and does not conform to the
                        LabelInputModel structure.
    """
    return update(userId, id, label)
