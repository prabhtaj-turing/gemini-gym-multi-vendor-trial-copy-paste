from common_utils.tool_spec_decorator import tool_spec
# gmail/Users/Settings/SendAs/SmimeInfo.py
import builtins
from typing import Optional, Dict, Any

# Use relative imports (go up FOUR levels)
from ....SimulationEngine.db import DB
from ....SimulationEngine.utils import _ensure_user, _next_counter
from common_utils.utils import validate_email_util

@tool_spec(
    spec={
        'name': 'list_send_as_smime_info',
        'description': """ Lists the S/MIME info for a specific 'Send as' alias.
        
        Retrieves all S/MIME certificate configurations associated with the given
        user ID and 'Send as' email address from the database. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'send_as_email': {
                    'type': 'string',
                    'description': """ The email address of the 'Send as' alias.
                    Defaults to ''. """
                }
            },
            'required': []
        }
    }
)
def list(userId: str = "me", send_as_email: str = "") -> Dict[str, Any]:
    """Lists the S/MIME info for a specific 'Send as' alias.

    Retrieves all S/MIME certificate configurations associated with the given
    user ID and 'Send as' email address from the database.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        send_as_email (str): The email address of the 'Send as' alias.
                       Defaults to ''.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'smimeInfo' (List[Dict[str, Any]]): List of S/MIME info resources.
            If the 'Send as' alias is not found or has no S/MIME info, the list
            within the dictionary will be empty. Otherwise, the list will contain
            dictionaries with the S/MIME properties as defined in the database.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    if send_as_email != '':
        validate_email_util(send_as_email, "send_as_email")
    send_as_entry = DB["users"][userId]["settings"]["sendAs"].get(send_as_email)
    if send_as_entry is None:
        return {"smimeInfo": []}
    smime_info_dict = send_as_entry.setdefault("smimeInfo", {})
    return {"smimeInfo": builtins.list(smime_info_dict.values())}


@tool_spec(
    spec={
        'name': 'get_send_as_smime_info',
        'description': """ Gets the specified S/MIME info for a specific 'Send as' alias.
        
        Retrieves a specific S/MIME certificate configuration identified by its ID,
        associated with the given user ID and 'Send as' email address. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'send_as_email': {
                    'type': 'string',
                    'description': """ The email address of the 'Send as' alias.
                    Defaults to ''. """
                },
                'smime_id': {
                    'type': 'string',
                    'description': "The ID of the S/MIME info to retrieve. Defaults to ''."
                }
            },
            'required': []
        }
    }
)
def get(
    userId: str = "me", send_as_email: str = "", smime_id: str = ""
) -> Optional[Dict[str, Any]]:
    """Gets the specified S/MIME info for a specific 'Send as' alias.

    Retrieves a specific S/MIME certificate configuration identified by its ID,
    associated with the given user ID and 'Send as' email address.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        send_as_email (str): The email address of the 'Send as' alias.
                       Defaults to ''.
        smime_id (str): The ID of the S/MIME info to retrieve. Defaults to ''.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the S/MIME info resource if found,
        otherwise None. The dictionary contains:
            - 'id' (str): The ID of the S/MIME info.
            - Other S/MIME properties as defined in the database.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    if send_as_email != '':
        validate_email_util(send_as_email, "send_as_email")
    send_as_entry = DB["users"][userId]["settings"]["sendAs"].get(send_as_email)
    if not send_as_entry:
        return None
    return send_as_entry.setdefault("smimeInfo", {}).get(smime_id)


@tool_spec(
    spec={
        'name': 'insert_send_as_smime_info',
        'description': """ Inserts a new S/MIME info configuration for the specified 'Send as' alias.
        
        Creates and stores a new S/MIME certificate configuration. Generates a
        unique ID for the new S/MIME info. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': "The user's email address. The special value 'me' can be used to indicate the authenticated user. Defaults to 'me'."
                },
                'send_as_email': {
                    'type': 'string',
                    'description': "The email address of the 'Send as' alias to associate the S/MIME info with. Defaults to ''."
                },
                'smime': {
                    'type': 'object',
                    'description': "An optional dictionary containing the S/MIME properties, defaults to None. If this dictionary is provided, it must contain 'encryptedKey' and may optionally contain other S/MIME properties.",
                    'properties': {
                        'encryptedKey': {
                            'type': 'string',
                            'description': 'The encrypted key for the S/MIME certificate.'
                        }
                    },
                    'required': [
                        'encryptedKey'
                    ]
                }
            },
            'required': []
        }
    }
)
def insert(
    userId: str = "me", send_as_email: str = "", smime: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Inserts a new S/MIME info configuration for the specified 'Send as' alias.

    Creates and stores a new S/MIME certificate configuration. Generates a
    unique ID for the new S/MIME info.

    Args:
        userId (str): The user's email address. The special value 'me' can be used to indicate the authenticated user. Defaults to 'me'.
        send_as_email (str): The email address of the 'Send as' alias to associate the S/MIME info with. Defaults to ''.
        smime (Optional[Dict[str, str]]): An optional dictionary containing the S/MIME properties, defaults to None. If this dictionary is provided, it must contain 'encryptedKey' and may optionally contain other S/MIME properties.
            - 'encryptedKey' (str): The encrypted key for the S/MIME certificate.

    Returns:
        Dict[str, Any]: A dictionary representing the newly inserted S/MIME info resource with keys:
            - 'id' (str): The ID of the S/MIME info.
            - 'encryptedKey' (str): The encrypted key for the S/MIME certificate.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    if send_as_email != '':
        validate_email_util(send_as_email, "send_as_email")
    smime = smime or {}
    send_as_entry = DB["users"][userId]["settings"]["sendAs"].setdefault(
        send_as_email, {}
    )
    smime_dict = send_as_entry.setdefault("smimeInfo", {})
    sid_num = _next_counter("smime")
    sid = f"smime_{sid_num}"
    new_smime = {
        "id": sid,
        "encryptedKey": smime.get("encryptedKey", ""),
    }
    smime_dict[sid] = new_smime
    return new_smime


@tool_spec(
    spec={
        'name': 'update_send_as_smime_info',
        'description': """ Updates the specified S/MIME info.
        
        Modifies an existing S/MIME certificate configuration identified by its ID.
        This performs a full update, replacing existing properties. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': "The user's email address. The special value 'me' can be used to indicate the authenticated user. Defaults to 'me'."
                },
                'send_as_email': {
                    'type': 'string',
                    'description': "The email address of the 'Send as' alias associated with the S/MIME info. Defaults to ''."
                },
                'id': {
                    'type': 'string',
                    'description': "The ID of the S/MIME info to update. Defaults to ''."
                },
                'smime': {
                    'type': 'object',
                    'description': "An optional dictionary containing the properties to update, defaults to None. If this dictionary is provided, it must contain 'encryptedKey' and may optionally contain other S/MIME properties.",
                    'properties': {
                        'encryptedKey': {
                            'type': 'string',
                            'description': 'The encrypted key for the S/MIME certificate.'
                        }
                    },
                    'required': [
                        'encryptedKey'
                    ]
                }
            },
            'required': []
        }
    }
)
def update(
    userId: str = "me",
    send_as_email: str = "",
    id: str = "",
    smime: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """Updates the specified S/MIME info.

    Modifies an existing S/MIME certificate configuration identified by its ID.
    This performs a full update, replacing existing properties.

    Args:
        userId (str): The user's email address. The special value 'me' can be used to indicate the authenticated user. Defaults to 'me'.
        send_as_email (str): The email address of the 'Send as' alias associated with the S/MIME info. Defaults to ''.
        id (str): The ID of the S/MIME info to update. Defaults to ''.
        smime (Optional[Dict[str, str]]): An optional dictionary containing the properties to update, defaults to None. If this dictionary is provided, it must contain 'encryptedKey' and may optionally contain other S/MIME properties.
            - 'encryptedKey' (str): The encrypted key for the S/MIME certificate.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the updated S/MIME info resource if found and
        updated, otherwise None. The dictionary contains:
            - 'id' (str): The ID of the S/MIME info.
            - Other S/MIME properties as defined in the database.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    smime = smime or {}
    if send_as_email != '':
        validate_email_util(send_as_email, "send_as_email")
    send_as_entry = DB["users"][userId]["settings"]["sendAs"].get(send_as_email)
    if not send_as_entry:
        return None
    smime_dict = send_as_entry.setdefault("smimeInfo", {})
    existing = smime_dict.get(id)
    if not existing:
        return None
    existing.update(smime)
    return existing


@tool_spec(
    spec={
        'name': 'patch_send_as_smime_info',
        'description': """ Updates the specified S/MIME info. Alias for update.
        
        This function is an alias for the `update` function. It modifies an
        existing S/MIME certificate configuration. Note: Implemented as a full update. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': "The user's email address. The special value 'me' can be used to indicate the authenticated user. Defaults to 'me'."
                },
                'send_as_email': {
                    'type': 'string',
                    'description': "The email address of the 'Send as' alias. Defaults to ''."
                },
                'id': {
                    'type': 'string',
                    'description': "The ID of the S/MIME info to update/patch. Defaults to ''."
                },
                'smime': {
                    'type': 'object',
                    'description': "An optional dictionary containing the properties to update, defaults to None. If this dictionary is provided, it must contain 'encryptedKey' and may optionally contain other S/MIME properties.",
                    'properties': {
                        'encryptedKey': {
                            'type': 'string',
                            'description': 'The encrypted key for the S/MIME certificate.'
                        }
                    },
                    'required': [
                        'encryptedKey'
                    ]
                }
            },
            'required': []
        }
    }
)
def patch(
    userId: str = "me",
    send_as_email: str = "",
    id: str = "",
    smime: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """Updates the specified S/MIME info. Alias for update.

    This function is an alias for the `update` function. It modifies an
    existing S/MIME certificate configuration. Note: Implemented as a full update.

    Args:
        userId (str): The user's email address. The special value 'me' can be used to indicate the authenticated user. Defaults to 'me'.
        send_as_email (str): The email address of the 'Send as' alias. Defaults to ''.
        id (str): The ID of the S/MIME info to update/patch. Defaults to ''.
        smime (Optional[Dict[str, str]]): An optional dictionary containing the properties to update, defaults to None. If this dictionary is provided, it must contain 'encryptedKey' and may optionally contain other S/MIME properties.
            - 'encryptedKey' (str): The encrypted key for the S/MIME certificate.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the updated S/MIME info resource if found and
        updated, otherwise None. The dictionary contains:
            - 'id' (str): The ID of the S/MIME info.
            - Other S/MIME properties as defined in the database.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    if send_as_email != '':
        validate_email_util(send_as_email, "send_as_email")
    return update(userId, send_as_email, id, smime)


@tool_spec(
    spec={
        'name': 'delete_send_as_smime_info',
        'description': """ Deletes the specified S/MIME certificate configuration.
        
        Removes the S/MIME info identified by its ID from the specified
        'Send as' alias configuration. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'send_as_email': {
                    'type': 'string',
                    'description': """ The email address of the 'Send as' alias from which
                    to delete the S/MIME info. Defaults to ''. """
                },
                'id': {
                    'type': 'string',
                    'description': "The ID of the S/MIME info to delete. Defaults to ''."
                }
            },
            'required': []
        }
    }
)
def delete(userId: str = "me", send_as_email: str = "", id: str = "") -> None:
    """Deletes the specified S/MIME certificate configuration.

    Removes the S/MIME info identified by its ID from the specified
    'Send as' alias configuration.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        send_as_email (str): The email address of the 'Send as' alias from which
                       to delete the S/MIME info. Defaults to ''.
        id (str): The ID of the S/MIME info to delete. Defaults to ''.

    Returns:
        None.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    if send_as_email != '':
        validate_email_util(send_as_email, "send_as_email")
    send_as_entry = DB["users"][userId]["settings"]["sendAs"].get(send_as_email)
    if send_as_entry:
        smime_dict = send_as_entry.setdefault("smimeInfo", {})
        smime_dict.pop(id, None)


@tool_spec(
    spec={
        'name': 'set_default_send_as_smime_info',
        'description': """ Sets the specified S/MIME certificate as the default for the alias.
        
        Marks the S/MIME info identified by `id` as the default configuration
        for the given 'Send as' alias, removing the default status from any other
        S/MIME configurations for that alias. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'userId': {
                    'type': 'string',
                    'description': """ The user's email address. The special value 'me'
                    can be used to indicate the authenticated user. Defaults to 'me'. """
                },
                'send_as_email': {
                    'type': 'string',
                    'description': "The email address of the 'Send as' alias. Defaults to ''."
                },
                'id': {
                    'type': 'string',
                    'description': "The ID of the S/MIME info to set as default. Defaults to ''."
                }
            },
            'required': []
        }
    }
)
def setDefault(
    userId: str = "me", send_as_email: str = "", id: str = ""
) -> Optional[Dict[str, Any]]:
    """Sets the specified S/MIME certificate as the default for the alias.

    Marks the S/MIME info identified by `id` as the default configuration
    for the given 'Send as' alias, removing the default status from any other
    S/MIME configurations for that alias.

    Args:
        userId (str): The user's email address. The special value 'me'
                can be used to indicate the authenticated user. Defaults to 'me'.
        send_as_email (str): The email address of the 'Send as' alias. Defaults to ''.
        id (str): The ID of the S/MIME info to set as default. Defaults to ''.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the S/MIME info resource that was set as
        default, if found. Returns None if the 'Send as' alias or the
        specific S/MIME info ID is not found. The dictionary contains:
            - 'id' (str): The ID of the S/MIME info.
            - Other S/MIME properties as defined in the database.

    Raises:
        KeyError: If the specified `userId` does not exist in the database.
    """
    _ensure_user(userId)
    if send_as_email != '':
        validate_email_util(send_as_email, "send_as_email")
    send_as_entry = DB["users"][userId]["settings"]["sendAs"].get(send_as_email)
    if not send_as_entry:
        return None
    smime_dict = send_as_entry.setdefault("smimeInfo", {})
    existing = smime_dict.get(id)
    if not existing:
        return None
    for _, val in smime_dict.items():
        val.pop("default", None)
    existing["default"] = True
    return existing
