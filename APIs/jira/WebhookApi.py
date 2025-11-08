from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/WebhookApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _generate_id, _check_empty_field
from .SimulationEngine.models import WebhookInput, WebhookCreateRequest
from typing import List, Dict, Any
from pydantic import ValidationError


@tool_spec(
    spec={
        'name': 'create_webhooks',
        'description': """ Create new webhooks in the system.
        
        This method creates new webhooks with the provided configurations. Each webhook
        will be assigned a unique ID and stored in the system. Webhooks are used to
        receive notifications when specific events occur in Jira. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'webhooks': {
                    'type': 'array',
                    'description': """ A list of webhook configurations to create.
                    Each webhook dictionary must contain: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'url': {
                                'type': 'string',
                                'description': """ The webhook URL endpoint. Must start with http:// or https://
                                             and cannot be empty or whitespace-only. """
                            },
                            'events': {
                                'type': 'array',
                                'description': """ List of event types the webhook subscribes to.
                                                      Must contain at least one valid event. Valid events include:
                                                     - issue_created, issue_updated, issue_deleted, issue_assigned
                                                     - project_created, project_updated, project_deleted
                                                     - user_created, user_updated, user_deleted """,
                                'items': {
                                    'type': 'string'
                                }
                            }
                        },
                        'required': [
                            'url',
                            'events'
                        ]
                    }
                }
            },
            'required': [
                'webhooks'
            ]
        }
    }
)
def create_or_get_webhooks(webhooks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create new webhooks in the system.

    This method creates new webhooks with the provided configurations. Each webhook
    will be assigned a unique ID and stored in the system. Webhooks are used to
    receive notifications when specific events occur in Jira.

    Args:
        webhooks (List[Dict[str, Any]]): A list of webhook configurations to create.
            Each webhook dictionary must contain:
            - url (str): The webhook URL endpoint. Must start with http:// or https://
                        and cannot be empty or whitespace-only.
            - events (List[str]): List of event types the webhook subscribes to.
                                 Must contain at least one valid event. Valid events include:
                                 - issue_created, issue_updated, issue_deleted, issue_assigned
                                 - project_created, project_updated, project_deleted  
                                 - user_created, user_updated, user_deleted

    Returns:
        Dict[str, Any]: A dictionary containing:
            - created (bool): Always True indicating successful creation
            - webhookIds (List[str]): The unique IDs of the created webhooks
            - webhooks (List[Dict[str, Any]]): The complete webhook objects including:
                - id (str): The unique webhook identifier
                - url (str): The webhook URL endpoint  
                - events (List[str]): The subscribed event types

    Raises:
        TypeError: If webhooks is not a list or contains non-dictionary elements
        ValueError: If webhooks list is empty or contains invalid webhook data
        ValidationError: If webhook data doesn't conform to the required structure
                        (e.g., missing required fields, invalid URL format, invalid events)
    """
    # Input validation - Type checking
    if not isinstance(webhooks, list):
        raise TypeError("webhooks parameter must be a list")
    
    if not webhooks:
        raise ValueError("webhooks list cannot be empty")
    
    # Validate each webhook is a dictionary
    for i, webhook in enumerate(webhooks):
        if not isinstance(webhook, dict):
            raise TypeError(f"webhook at index {i} must be a dictionary, got {type(webhook).__name__}")
    
    # Comprehensive validation using Pydantic
    try:
        validated_request = WebhookCreateRequest(webhooks=webhooks)
    except ValidationError as e:
        raise e
    
    # Create webhooks with unique IDs
    created_webhooks = []
    webhook_ids = []
    
    for validated_webhook in validated_request.webhooks:
        # Generate unique webhook ID
        webhook_id = _generate_id("WEBHOOK", DB["webhooks"])
        
        # Create complete webhook object
        webhook_data = {
            "id": webhook_id,
            "url": validated_webhook.url,
            "events": validated_webhook.events
        }
        
        # Store in database
        DB["webhooks"][webhook_id] = webhook_data
        
        # Add to response data
        created_webhooks.append(webhook_data)
        webhook_ids.append(webhook_id)
    
    return {
        "created": True,
        "webhookIds": webhook_ids,
        "webhooks": created_webhooks
    }


@tool_spec(
    spec={
        'name': 'get_all_webhooks',
        'description': 'Get all webhooks.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_webhooks() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all webhooks.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing the webhooks' information.
            - webhooks (List[Dict[str, Any]]): The webhooks' information.
                - id (str): The ID of the webhook.
                - url (str): The URL of the webhook.
                - events (List[str]): The events that the webhook is subscribed to.
    """
    return {"webhooks": list(DB["webhooks"].values())}


@tool_spec(
    spec={
        'name': 'delete_webhooks_by_ids',
        'description': 'Delete webhooks.',
        'parameters': {
            'type': 'object',
            'properties': {
                'webhookIds': {
                    'type': 'array',
                    'description': 'The IDs of the webhooks to delete.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'webhookIds'
            ]
        }
    }
)
def delete_webhooks(webhookIds: List[str]) -> Dict[str, Any]:
    """
    Delete webhooks.

    Args:
        webhookIds (List[str]): The IDs of the webhooks to delete.

    Returns:
        Dict[str, Any]: A dictionary containing the webhooks' information.
            - deleted (List[str]): The IDs of the webhooks that were deleted.
    Raises:
        TypeError: If webhookIds is not a list or contains non-string elements.
    """
    # 1. Type validation - ensures it's a list
    if not isinstance(webhookIds, list):
        raise TypeError("webhookIds must be a list.")
    
    # 2. Content validation - ensures all elements are strings
    if not all(isinstance(wid, str) for wid in webhookIds):
        raise TypeError("All webhookIds must be strings.")

    # 3. Emptiness validation - ensures at least one ID is provided
    err = _check_empty_field("webhookIds", webhookIds)
    if err:
        return {"error": err}

    deleted = []
    for wid in webhookIds:
        if wid in DB["webhooks"]:
            DB["webhooks"].pop(wid)
            deleted.append(wid)

    return {"deleted": deleted}
