from common_utils.tool_spec_decorator import tool_spec
import uuid
from typing import Dict, Any, Optional
from pydantic import ValidationError
from .SimulationEngine.db import DB
from .SimulationEngine.models import AccessControlRuleModel, AccessControlRuleUpdateModel


@tool_spec(
    spec={
        'name': 'delete_access_control_rule',
        'description': 'Deletes an access control rule from the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The ID of the calendar to delete the rule from.'
                },
                'ruleId': {
                    'type': 'string',
                    'description': 'The ID of the rule to delete.'
                }
            },
            'required': [
                'calendarId',
                'ruleId'
            ]
        }
    }
)
def delete_rule(calendarId: str, ruleId: str) -> Dict[str, Any]:
    """
    Deletes an access control rule from the specified calendar.

    Args:
        calendarId (str): The ID of the calendar to delete the rule from.
        ruleId (str): The ID of the rule to delete.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): Whether the rule was deleted successfully.
            - message (str): A message describing the result of the operation.

    Raises:
        TypeError: If calendarId or ruleId is not a string.
        ValueError: If calendarId or ruleId is None, empty, or whitespace-only,
                   if the rule is not found, or if the rule does not belong to the specified calendar.
    """
    # Comprehensive input validation
    if calendarId is None:
        raise ValueError("calendarId cannot be None")
    if ruleId is None:
        raise ValueError("ruleId cannot be None")

    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string")
    if not isinstance(ruleId, str):
        raise TypeError("ruleId must be a string")

    if not calendarId or not calendarId.strip():
        raise ValueError("calendarId cannot be empty or whitespace-only")
    if not ruleId or not ruleId.strip():
        raise ValueError("ruleId cannot be empty or whitespace-only")

    # In a real API, you'd verify calendarId ownership, etc.
    # We'll assume each rule is keyed by ruleId in DB["acl_rules"].
    if ruleId not in DB["acl_rules"]:
        # Simulate 404 not found
        raise ValueError(f"ACL rule '{ruleId}' not found.")
    rule = DB["acl_rules"][ruleId]
    # Check if the rule belongs to the specified calendar
    if rule.get("calendarId") != calendarId:
        raise ValueError(
            f"ACL rule '{ruleId}' does not belong to calendar '{calendarId}'."
        )

    # Delete the rule
    del DB["acl_rules"][ruleId]
    return {"success": True, "message": f"ACL rule {ruleId} deleted."}


@tool_spec(
    spec={
        'name': 'get_access_control_rule',
        'description': 'Retrieves an access control rule from the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The ID of the calendar to get the rule from.'
                },
                'ruleId': {
                    'type': 'string',
                    'description': 'The ID of the rule to retrieve.'
                }
            },
            'required': [
                'calendarId',
                'ruleId'
            ]
        }
    }
)
def get_rule(calendarId: str, ruleId: str) -> Dict[str, Any]:
    """
    Retrieves an access control rule from the specified calendar.

    Args:
        calendarId (str): The ID of the calendar to get the rule from.
        ruleId (str): The ID of the rule to retrieve.

    Returns:
        Dict[str, Any]: A dictionary containing the rule details:
            - ruleId (str): The ID of the rule.
            - calendarId (str): The ID of the calendar the rule belongs to.
            - scope (Dict[str, str]): The scope of the rule:
                - type (str): The type of scope (e.g., 'user', 'group').
                - value (str): The value of the scope (e.g., email address).
            - role (str): The role assigned by the rule (e.g., 'reader', 'writer').

    Raises:
        TypeError: If calendarId or ruleId is not a string.
        ValueError: If calendarId or ruleId is empty/whitespace, if the rule is not found, 
                   or if the rule does not belong to the specified calendar.
    """
    # Input validation
    if calendarId is None or not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string")
    if ruleId is None or not isinstance(ruleId, str):
        raise TypeError("ruleId must be a string")
    
    if not calendarId.strip():
        raise ValueError("calendarId cannot be empty or whitespace")
    if not ruleId.strip():
        raise ValueError("ruleId cannot be empty or whitespace")
    
    # Business logic validation
    if ruleId not in DB["acl_rules"]:
        raise ValueError(f"ACL rule '{ruleId}' not found.")
    rule = DB["acl_rules"][ruleId]
    if rule.get("calendarId") != calendarId:
        raise ValueError(
            f"ACL rule '{ruleId}' does not belong to calendar '{calendarId}'."
        )
    return rule


@tool_spec(
    spec={
        'name': 'create_access_control_rule',
        'description': 'Creates a new access control rule for the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The ID of the calendar to create the rule for.'
                },
                'sendNotifications': {
                    'type': 'boolean',
                    'description': "Whether to send notifications to the rule's scope. Defaults to True."
                },
                'resource': {
                    'type': 'object',
                    'description': 'The rule details:',
                    'properties': {
                        'role': {
                            'type': 'string',
                            'description': "The role to assign (e.g., 'reader', 'writer')."
                        },
                        'scope': {
                            'type': 'object',
                            'description': 'The scope of the rule:',
                            'properties': {
                                'type': {
                                    'type': 'string',
                                    'description': "The type of scope (e.g., 'user', 'group')."
                                },
                                'value': {
                                    'type': 'string',
                                    'description': 'The value of the scope (e.g., email address).'
                                }
                            },
                            'required': [
                                'type',
                                'value'
                            ]
                        },
                        'ruleId': {
                            'type': 'string',
                            'description': 'The ID of the rule. If not provided, one will be generated.'
                        }
                    },
                    'required': [
                        'role',
                        'scope'
                    ]
                }
            },
            'required': [
                'calendarId'
            ]
        }
    }
)
def create_rule(
    calendarId: str,
    sendNotifications: bool = True,
    resource: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Creates a new access control rule for the specified calendar.

    Args:
        calendarId (str): The ID of the calendar to create the rule for.
        sendNotifications (bool): Whether to send notifications to the rule's scope. Defaults to True.
        resource (Dict[str, Any]): The rule details:
            - role (str): The role to assign (e.g., 'reader', 'writer').
            - scope (Dict[str, str]): The scope of the rule:
                - type (str): The type of scope (e.g., 'user', 'group').
                - value (str): The value of the scope (e.g., email address).
            - ruleId (Optional[str]): The ID of the rule. If not provided, one will be generated.

    Returns:
        Dict[str, Any]: A dictionary containing the created rule with the same structure as the input resource,
        plus the generated ruleId if one was not provided.
            - ruleId (str): The ID of the rule.
            - calendarId (str): The ID of the calendar the rule belongs to.
            - scope (Dict[str, str]): The scope of the rule:
                - type (str): The type of scope (e.g., 'user', 'group').
                - value (str): The value of the scope (e.g., email address).
            - role (str): The role assigned by the rule (e.g., 'reader', 'writer').
            - notificationsSent (bool): Whether notifications were sent to the rule's scope.

    Raises:
        TypeError: If calendarId is not a string, sendNotifications is not a boolean, 
                  or resource is not a dictionary.
        ValueError: If calendarId is empty/whitespace or resource is not provided.
        ValidationError: If resource data doesn't conform to the expected structure,
                        including invalid email addresses in the scope.value field.
    """
    # Input validation
    if calendarId is None or not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string")
    if not isinstance(sendNotifications, bool):
        raise TypeError("sendNotifications must be a boolean")
    
    if not calendarId.strip():
        raise ValueError("calendarId cannot be empty or whitespace")
    
    if resource is None:
        raise ValueError("Resource body is required to create a rule.")
    if not isinstance(resource, dict):
        raise TypeError("resource must be a dictionary")
    
    # Validate resource using Pydantic model
    try:
        validated_resource = AccessControlRuleModel(**resource)
        resource = validated_resource.model_dump()
    except ValidationError as e:
        raise e

    # Create a copy of resource to avoid modifying the original
    rule_data = resource.copy()
    
    # Generate ruleId if not provided or empty
    rule_id = rule_data.get("ruleId") or str(uuid.uuid4())
    rule_data["ruleId"] = rule_id
    rule_data["calendarId"] = calendarId
    
    # Implement sendNotifications functionality
    rule_data["notificationsSent"] = sendNotifications
    
    # Store and return the rule
    DB["acl_rules"][rule_id] = rule_data
    return DB["acl_rules"][rule_id]


@tool_spec(
    spec={
        'name': 'list_access_control_rules',
        'description': 'Lists all access control rules for the specified calendar.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The ID of the calendar to list rules for.'
                },
                'maxResults': {
                    'type': 'integer',
                    'description': 'Maximum number of rules to return. Defaults to 100.'
                },
                'pageToken': {
                    'type': 'string',
                    'description': 'Token for pagination. Not implemented.'
                },
                'showDeleted': {
                    'type': 'boolean',
                    'description': 'Whether to include deleted rules. Not implemented.'
                },
                'syncToken': {
                    'type': 'string',
                    'description': 'Token for synchronization. Not implemented.'
                }
            },
            'required': [
                'calendarId'
            ]
        }
    }
)
def list_rules(
    calendarId: str,
    maxResults: int = 100,
    pageToken: Optional[str] = None,
    showDeleted: bool = False,
    syncToken: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Lists all access control rules for the specified calendar.

    Args:
        calendarId (str): The ID of the calendar to list rules for.
        maxResults (int): Maximum number of rules to return. Defaults to 100.
        pageToken (Optional[str]): Token for pagination. Not implemented.
        showDeleted (bool): Whether to include deleted rules. Not implemented.
        syncToken (Optional[str]): Token for synchronization. Not implemented.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - items (List[Dict[str, Any]]): List of rules matching the criteria with the following structure:
                - ruleId (str): The ID of the rule.
                - calendarId (str): The ID of the calendar the rule belongs to.
                - scope (Dict[str, str]): The scope of the rule:
                    - type (str): The type of scope (e.g., 'user', 'group').
                    - value (str): The value of the scope (e.g., email address).
                - role (str): The role assigned by the rule (e.g., 'reader', 'writer').
            - nextPageToken (None): Always None as pagination is not implemented.

    Raises:
        TypeError: If calendarId is not a string or maxResults is not an integer.
        ValueError: If calendarId is empty/whitespace or maxResults is not positive.
    """
    # Input validation
    if calendarId is None or not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string")
    if not isinstance(maxResults, int):
        raise TypeError("maxResults must be an integer")
    
    if not calendarId.strip():
        raise ValueError("calendarId cannot be empty or whitespace")
    if maxResults <= 0:
        raise ValueError("maxResults must be a positive integer")

    # For simplicity, we won't implement paging or sync tokens thoroughly.
    # We'll just return all ACLs for the specified calendarId.
    # In reality, 'calendarId' would be used to filter which rules are relevant.
    # We'll simulate that each rule has a "calendarId" and we filter by that.

    all_rules = []
    for rule in DB["acl_rules"].values():
        if rule.get("calendarId") == calendarId:
            # If it's "deleted" and showDeleted=False, skip it.
            # We'll just skip that detail for now.
            all_rules.append(rule)

    # Truncate at maxResults
    result = all_rules[:maxResults]
    return {"items": result, "nextPageToken": None}  # Not implemented


@tool_spec(
    spec={
        'name': 'patch_access_control_rule',
        'description': 'Updates specific fields of an existing access control rule.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The ID of the calendar containing the rule.'
                },
                'ruleId': {
                    'type': 'string',
                    'description': 'The ID of the rule to update.'
                },
                'sendNotifications': {
                    'type': 'boolean',
                    'description': 'Whether to send notifications. Defaults to True.'
                },
                'resource': {
                    'type': 'object',
                    'description': 'The fields to update:',
                    'properties': {
                        'role': {
                            'type': 'string',
                            'description': 'New role to assign.'
                        },
                        'scope': {
                            'type': 'object',
                            'description': 'New scope settings.',
                            'properties': {
                                'type': {
                                    'type': 'string',
                                    'description': "The type of scope (e.g., 'user', 'group')."
                                },
                                'value': {
                                    'type': 'string',
                                    'description': 'The value of the scope (e.g., email address).'
                                }
                            },
                            'required': [
                                'type',
                                'value'
                            ]
                        }
                    },
                    'required': [
                        'role',
                        'scope'
                    ]
                }
            },
            'required': [
                'calendarId',
                'ruleId'
            ]
        }
    }
)
def patch_rule(
    calendarId: str,
    ruleId: str,
    sendNotifications: bool = True,
    resource: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Updates specific fields of an existing access control rule.

    Args:
        calendarId (str): The ID of the calendar containing the rule.
        ruleId (str): The ID of the rule to update.
        sendNotifications (bool): Whether to send notifications. Defaults to True.
        resource (Dict[str, Any]): The fields to update:
            - role (str): New role to assign.
            - scope (Dict[str, str]): New scope settings.
                - type (str): The type of scope (e.g., 'user', 'group').
                - value (str): The value of the scope (e.g., email address).

    Returns:
        Dict[str, Any]: The updated rule with all fields, including unchanged ones.
        The rule will have the following structure:
            - ruleId (str): The ID of the rule.
            - calendarId (str): The ID of the calendar the rule belongs to.
            - scope (Dict[str, str]): The scope of the rule:
                - type (str): The type of scope (e.g., 'user', 'group').
                - value (str): The value of the scope (e.g., email address).
            - role (str): The role assigned by the rule (e.g., 'reader', 'writer').

    Raises:
        TypeError: If calendarId or ruleId is not a string, sendNotifications is not a boolean,
                  or resource is not a dictionary.
        ValueError: If calendarId or ruleId is empty/whitespace, rule is not found,
                   or rule does not belong to the specified calendar.
        ValidationError: If resource data doesn't conform to the expected structure,
                        including invalid email addresses in the scope.value field.
    """
    # Input validation
    if calendarId is None or not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string")
    if ruleId is None or not isinstance(ruleId, str):
        raise TypeError("ruleId must be a string")
    if not isinstance(sendNotifications, bool):
        raise TypeError("sendNotifications must be a boolean")
    
    if not calendarId.strip():
        raise ValueError("calendarId cannot be empty or whitespace")
    if not ruleId.strip():
        raise ValueError("ruleId cannot be empty or whitespace")
    
    # Resource validation using Pydantic model
    if resource is not None:
        if not isinstance(resource, dict):
            raise TypeError("resource must be a dictionary")
        
        try:
            validated_resource = AccessControlRuleUpdateModel(**resource)
            resource = validated_resource.model_dump(exclude_unset=True)
        except ValidationError as e:
            raise e
    
    # Business logic validation
    if ruleId not in DB["acl_rules"]:
        raise ValueError(f"ACL rule '{ruleId}' not found.")
    existing = DB["acl_rules"][ruleId]
    if existing.get("calendarId") != calendarId:
        raise ValueError(
            f"ACL rule '{ruleId}' does not belong to calendar '{calendarId}'."
        )
    
    # Apply updates
    for k, v in (resource or {}).items():
        existing[k] = v
    DB["acl_rules"][ruleId] = existing
    return existing


@tool_spec(
    spec={
        'name': 'update_access_control_rule',
        'description': 'Replaces an existing access control rule with new data.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The ID of the calendar containing the rule.'
                },
                'ruleId': {
                    'type': 'string',
                    'description': 'The ID of the rule to update.'
                },
                'sendNotifications': {
                    'type': 'boolean',
                    'description': 'Whether to send notifications. Defaults to True.'
                },
                'resource': {
                    'type': 'object',
                    'description': 'The complete new rule data:',
                    'properties': {
                        'role': {
                            'type': 'string',
                            'description': 'New role to assign.'
                        },
                        'scope': {
                            'type': 'object',
                            'description': 'New scope settings.',
                            'properties': {
                                'type': {
                                    'type': 'string',
                                    'description': "The type of scope (e.g., 'user', 'group')."
                                },
                                'value': {
                                    'type': 'string',
                                    'description': 'The value of the scope (e.g., email address).'
                                }
                            },
                            'required': [
                                'type',
                                'value'
                            ]
                        }
                    },
                    'required': [
                        'role',
                        'scope'
                    ]
                }
            },
            'required': [
                'calendarId',
                'ruleId'
            ]
        }
    }
)
def update_rule(
    calendarId: str,
    ruleId: str,
    sendNotifications: bool = True,
    resource: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Replaces an existing access control rule with new data.

    Args:
        calendarId (str): The ID of the calendar containing the rule.
        ruleId (str): The ID of the rule to update.
        sendNotifications (bool): Whether to send notifications. Defaults to True.
        resource (Dict[str, Any]): The complete new rule data:
            - role (str): New role to assign.
            - scope (Dict[str, str]): New scope settings.
                - type (str): The type of scope (e.g., 'user', 'group').
                - value (str): The value of the scope (e.g., email address).

    Returns:
        Dict[str, Any]: The complete updated rule with the following structure:
            - ruleId (str): The ID of the rule.
            - calendarId (str): The ID of the calendar the rule belongs to.
            - scope (Dict[str, str]): The scope of the rule:
                - type (str): The type of scope (e.g., 'user', 'group').
                - value (str): The value of the scope (e.g., email address).
            - role (str): The role assigned by the rule (e.g., 'reader', 'writer').

    Raises:
        TypeError: If calendarId or ruleId is not a string, if sendNotifications is not a boolean,
                  or if resource is not a dictionary.
        ValueError: If calendarId is empty or None, if ruleId is empty or None,
                   if the rule is not found, if the rule does not belong to the specified calendar,
                   or if the resource body is not provided.
        ValidationError: If resource data doesn't conform to the expected structure,
                        including invalid email addresses in the scope.value field.
    """
    # Input validation
    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string")
    if not isinstance(ruleId, str):
        raise TypeError("ruleId must be a string")
    if not isinstance(sendNotifications, bool):
        raise TypeError("sendNotifications must be a boolean")
    if resource is not None and not isinstance(resource, dict):
        raise TypeError("resource must be a dictionary")
    
    if not calendarId or not calendarId.strip():
        raise ValueError("calendarId cannot be empty or None")
    if not ruleId or not ruleId.strip():
        raise ValueError("ruleId cannot be empty or None")
    if resource is None:
        raise ValueError("Resource body is required for update.")
    
    # Check if rule exists
    if ruleId not in DB["acl_rules"]:
        raise ValueError(f"ACL rule '{ruleId}' not found.")
    
    existing_rule = DB["acl_rules"][ruleId]
    # Check if the rule belongs to the specified calendar
    if existing_rule.get("calendarId") != calendarId:
        raise ValueError(
            f"ACL rule '{ruleId}' does not belong to calendar '{calendarId}'."
        )
    
    # Validate resource using Pydantic model
    try:
        validated_resource = AccessControlRuleModel(**resource)
        resource = validated_resource.model_dump()
    except ValidationError as e:
        raise e
    
    # Security: Only allow specific fields to be updated
    # Extract only the fields we care about for validation
    user_provided_fields = set(resource.keys())
    allowed_fields = {"role", "scope"}
    # Ignore system fields that might be present from previous operations
    system_fields = {"ruleId", "calendarId"}
    
    # Check for invalid fields (excluding system fields)
    invalid_fields = user_provided_fields - allowed_fields - system_fields
    if invalid_fields:
        raise ValueError(f"Invalid fields in resource: {', '.join(sorted(invalid_fields))}. Only 'role' and 'scope' are allowed.")
    
    # Create updated rule with validated data
    updated_rule = {
        "ruleId": ruleId,
        "calendarId": calendarId,
        "role": resource["role"],
        "scope": resource["scope"]
    }
    
    # Store the updated rule
    DB["acl_rules"][ruleId] = updated_rule
    
    # Simulate sendNotifications behavior (in real implementation would send notifications)
    if sendNotifications:
        # In a real implementation, this would trigger notification sending
        pass
    
    return DB["acl_rules"][ruleId]


@tool_spec(
    spec={
        'name': 'watch_access_control_rule_changes',
        'description': 'Sets up a watch for changes to access control rules.',
        'parameters': {
            'type': 'object',
            'properties': {
                'calendarId': {
                    'type': 'string',
                    'description': 'The ID of the calendar to watch.'
                },
                'maxResults': {
                    'type': 'integer',
                    'description': 'Maximum number of rules to return. Defaults to 100.'
                },
                'pageToken': {
                    'type': 'string',
                    'description': 'Token for pagination. Not implemented.'
                },
                'showDeleted': {
                    'type': 'boolean',
                    'description': 'Whether to include deleted rules. Not implemented.'
                },
                'syncToken': {
                    'type': 'string',
                    'description': 'Token for synchronization. Not implemented.'
                },
                'resource': {
                    'type': 'object',
                    'description': 'Watch configuration:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Type of watch (defaults to "web_hook").'
                        },
                        'id': {
                            'type': 'string',
                            'description': 'Channel ID. If not provided, one will be generated.'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'calendarId'
            ]
        }
    }
)
def watch_rules(
    calendarId: str,
    maxResults: int = 100,
    pageToken: Optional[str] = None,
    showDeleted: bool = False,
    syncToken: Optional[str] = None,
    resource: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Sets up a watch for changes to access control rules.

    Args:
        calendarId (str): The ID of the calendar to watch.
        maxResults (int): Maximum number of rules to return. Defaults to 100.
        pageToken (Optional[str]): Token for pagination. Not implemented.
        showDeleted (bool): Whether to include deleted rules. Not implemented.
        syncToken (Optional[str]): Token for synchronization. Not implemented.
        resource (Dict[str, Any]): Watch configuration:
            - type (Optional[str]): Type of watch (defaults to "web_hook").
            - id (Optional[str]): Channel ID. If not provided, one will be generated.

    Returns:
        Dict[str, Any]: A dictionary containing the watch channel details:
            - id (str): The channel ID.
            - type (str): The watch type.
            - resource (str): Always "acl".
            - calendarId (str): The calendar being watched.

    Raises:
        TypeError: If calendarId is not a string, if maxResults is not an integer,
                  if showDeleted is not a boolean, or if resource is not a dictionary.
        ValueError: If calendarId is empty or None, if maxResults is not positive,
                   if the resource body is not provided, or if resource contains invalid fields.
    """
    # Input validation
    if not isinstance(calendarId, str):
        raise TypeError("calendarId must be a string")
    if not isinstance(maxResults, int):
        raise TypeError("maxResults must be an integer")
    if not isinstance(showDeleted, bool):
        raise TypeError("showDeleted must be a boolean")
    if resource is not None and not isinstance(resource, dict):
        raise TypeError("resource must be a dictionary")
    
    if not calendarId or not calendarId.strip():
        raise ValueError("calendarId cannot be empty or None")
    if maxResults <= 0:
        raise ValueError("maxResults must be a positive integer")
    if resource is None:
        raise ValueError("Channel resource is required.")

    # Validate required resource fields with default value
    if "type" not in resource or resource["type"] is None:
        resource["type"] = "web_hook"  # Set default value
    if not isinstance(resource["type"], str) or not resource["type"].strip():
        raise ValueError("Resource type must be a non-empty string")
    
    # Validate optional resource fields
    if "id" in resource:
        if not isinstance(resource["id"], str) or not resource["id"].strip():
            raise ValueError("Resource id must be a non-empty string")
    
    # Security: Only allow specific fields in resource
    allowed_fields = {"type", "id"}
    invalid_fields = set(resource.keys()) - allowed_fields
    if invalid_fields:
        raise ValueError(f"Invalid fields in resource: {', '.join(sorted(invalid_fields))}. Only 'type' and 'id' are allowed.")

    # We'll simulate returning a Channel object. Realistically, you'd return
    # some channel info about push notifications, etc.
    channel_id = resource.get("id") or str(uuid.uuid4())
    
    # Ensure channels key exists in DB
    if "channels" not in DB:
        DB["channels"] = {}
    
    DB["channels"][channel_id] = {
        "id": channel_id,
        "type": resource["type"],
        "resource": "acl",
        "calendarId": calendarId,
    }
    return DB["channels"][channel_id]
