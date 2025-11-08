from common_utils.tool_spec_decorator import tool_spec
# APIs/hubspot/FormGlobalEvents.py
from typing import Optional, Dict, Any, List, Union
import uuid
from hubspot.SimulationEngine.db import DB
from hubspot.SimulationEngine.custom_errors import (
    InvalidSubscriptionIdTypeError,
    EmptySubscriptionIdError,
    SubscriptionNotFoundError,
    InvalidActiveParameterError,
)
from hubspot.SimulationEngine.models import CreateSubscriptionModel, SubscriptionDetails
from pydantic import ValidationError


@tool_spec(
    spec={
        'name': 'get_form_global_event_subscription_definitions',
        'description': 'Get all global form event subscription definitions.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subscription_definitions() -> List[Dict[str, Union[str, bool]]]:
    """
    Get all global form event subscription definitions.

    Returns:
        List[Dict[str, Union[str, bool]]]: A list of all global form event subscription definitions.
            - subscription_id(str): The id of the subscription definition.
            - name(str): The name of the subscription definition.
            - description(str): The description of the subscription definition.
            - frequency(str): The frequency of the subscription (e.g., Daily, Weekly, Monthly, Quarterly).
            - active(bool): Whether the subscription definition is active.
    """
    return DB["subscription_definitions"]


@tool_spec(
    spec={
        'name': 'create_form_global_event_subscription',
        'description': 'Creates a new webhook subscription for global form events.',
        'parameters': {
            'type': 'object',
            'properties': {
            'endpoint': {
                'type': 'string',
                'description': 'The endpoint of the subscription definition. Optional.'
            },
            'subscriptionDetails': {
                'type': 'object',
                'description': 'The subscription details of the subscription definition. Optional. Defaults to None.',
                'properties': {
                    'contact_id': {
                        'type': 'string',
                        'description': 'The id of the contact. Optional.'
                    },
                    'subscribed': {
                        'type': 'boolean',
                        'description': 'Whether the contact is subscribed to the subscription. Optional.'
                    },
                    'opt_in_date': {
                        'type': 'string',
                        'description': 'The date the contact opted in to the subscription. Optional.'
                    }
                },
                'required': []
            }
            },
            'required': ['endpoint']
        }
        }
)
def create_subscription(
    endpoint: Optional[str], subscriptionDetails: Optional[Dict[str, Union[str, bool, None]]] = None
) -> Dict[str, Union[str, bool, None, Dict[str, Union[str, bool, None]]]]:
    """
    Creates a new webhook subscription for global form events.

    Args:
        endpoint(Optional[str]): The endpoint of the subscription definition. Optional.
        subscriptionDetails(Optional[Dict[str, Union[str, bool, None]]]): The subscription details of the subscription definition. Optional. Defaults to None.
            - contact_id(Optional[str]): The id of the contact. Optional.
            - subscribed(Optional[bool]): Whether the contact is subscribed to the subscription. Optional.
            - opt_in_date(Optional[str]): The date the contact opted in to the subscription. Optional.

    Returns:
        Dict[str, Union[str, bool, None, Dict[str, Union[str, bool, None]]]]: The new webhook subscription for global form events.
            - id(str): The id of the subscription definition.
            - endpoint(Optional[str]): The endpoint of the subscription definition. Can be None.
            - subscriptionDetails(Dict[str, Union[str, bool, None]]): The subscription details of the subscription definition.
                - contact_id(Optional[str]): The id of the contact. Can be None.
                - subscription_id(str): The id of the subscription.
                - subscribed(Optional[bool]): Whether the contact is subscribed to the subscription. Can be None.
                - opt_in_date(Optional[str]): The date the contact opted in to the subscription. Can be None.
            - active(bool): Whether the subscription definition is active.

    Raises:
        ValidationError: If the input data is invalid (from Pydantic validation).
    """
    # Handle case where subscriptionDetails is None
    if subscriptionDetails is None:
        subscriptionDetails = {}
    
    # Validate input using Pydantic model
    validated_data = CreateSubscriptionModel(endpoint=endpoint, subscriptionDetails=subscriptionDetails or {})

    new_subscription_id = str(uuid.uuid4())
    
    # Handle case where subscriptionDetails is None after validation
    subscription_details_dict = {}
    if validated_data.subscriptionDetails is not None:
        # Pydantic will have already converted the dict to a SubscriptionDetails model
        subscription_details_dict = validated_data.subscriptionDetails.model_dump()
    
    # Add the subscription_id to the subscriptionDetails as seen in the database
    subscription_details_dict["subscription_id"] = new_subscription_id
    
    new_subscription = {
        "id": new_subscription_id,
        "endpoint": validated_data.endpoint,
        "subscriptionDetails": subscription_details_dict,
        "active": True,  # Initially active
    }
    DB["subscriptions"][new_subscription_id] = new_subscription
    return new_subscription


@tool_spec(
    spec={
        'name': 'get_form_global_event_subscriptions',
        'description': 'Gets all webhook subscriptions for global form events.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_subscriptions() -> List[Dict[str, Union[str, bool, None, Dict[str, Union[str, bool, None]]]]]:
    """
    Gets all webhook subscriptions for global form events.

    Returns:
        List[Dict[str, Union[str, bool, None, Dict[str, Union[str, bool, None]]]]]: A list of all webhook subscriptions for global form events.
            - id(str): The id of the subscription.
            - endpoint(Optional[str]): The endpoint of the subscription. Can be None.
            - subscriptionDetails(Dict[str, Union[str, bool, None]]): The subscription details of the subscription.
                - contact_id(str): The id of the contact.
                - subscription_id(str): The id of the subscription.
                - subscribed(bool): Whether the contact is subscribed to the subscription.
                - opt_in_date(Optional[str]): The date the contact opted in to the subscription. Can be None.
            - active(bool): Whether the subscription is active.
    """
    return list(DB["subscriptions"].values())


@tool_spec(
    spec={
        'name': 'delete_form_global_event_subscription',
        'description': 'Deletes (unsubscribes) a webhook subscription.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subscriptionId': {
                    'type': 'string',
                    'description': 'The unique identifier of the subscription to delete. Must be a non-empty string that exists in the subscription database.'
                }
            },
            'required': [
                'subscriptionId'
            ]
        }
    }
)
def delete_subscription(subscriptionId: str) -> None:
    """
    Deletes (unsubscribes) a webhook subscription.

    Args:
        subscriptionId(str): The unique identifier of the subscription to delete. Must be a non-empty string that exists in the subscription database.

    Returns:
        None

    Raises:
        InvalidSubscriptionIdTypeError: If subscriptionId is not a string.
        EmptySubscriptionIdError: If subscriptionId is empty or contains only whitespace.
        SubscriptionNotFoundError: If the subscription with the given id is not found.
    """
    # Input validation
    if not isinstance(subscriptionId, str):
        raise InvalidSubscriptionIdTypeError(f"subscriptionId must be a string, got {type(subscriptionId).__name__}")
    
    if not subscriptionId or not subscriptionId.strip():
        raise EmptySubscriptionIdError("subscriptionId cannot be empty or contain only whitespace")
    
    # Check if subscription exists
    if subscriptionId not in DB["subscriptions"]:
        raise SubscriptionNotFoundError(f"Subscription with id '{subscriptionId}' not found")
    
    del DB["subscriptions"][subscriptionId]


@tool_spec(
    spec={
        'name': 'update_form_global_event_subscription',
        'description': 'Updates (specifically, activates or deactivates) a webhook subscription.',
        'parameters': {
            'type': 'object',
            'properties': {
                'subscriptionId': {
                    'type': 'string',
                    'description': 'The id of the subscription definition. Must be a non-empty string.'
                },
                'active': {
                    'type': 'boolean',
                    'description': 'Whether the subscription definition is active.'
                }
            },
            'required': [
                'subscriptionId',
                'active'
            ]
        }
    }
)
def update_subscription(subscriptionId: str, active: bool) -> Dict[str, Union[str, bool, Dict[str, Union[str, bool]]]]:
    """
    Updates (specifically, activates or deactivates) a webhook subscription.

    Args:
        subscriptionId(str): The id of the subscription definition. Must be a non-empty string.
        active(bool): Whether the subscription definition is active.

    Returns:
        Dict[str, Union[str, bool, Dict[str, Union[str, bool]]]]: The updated webhook subscription.
            - id(str): The id of the subscription definition.
            - endpoint(str): The endpoint of the subscription definition.
            - subscriptionDetails(Dict[str, Union[str, bool]]): The subscription details of the subscription definition.
                - contact_id(str): The id of the contact.
                - subscription_id(str): The id of the subscription.
                - subscribed(bool): Whether the contact is subscribed to the subscription.
                - opt_in_date(str): The date the contact opted in to the subscription.
            - active(bool): Whether the subscription definition is active.

    Raises:
        InvalidSubscriptionIdTypeError: If subscriptionId is not a string.
        EmptySubscriptionIdError: If subscriptionId is empty or contains only whitespace.
        InvalidActiveParameterError: If active is not a boolean.
        SubscriptionNotFoundError: If the subscription with the given id is not found.
    """
    # Input validation for subscriptionId
    if not isinstance(subscriptionId, str):
        raise InvalidSubscriptionIdTypeError(f"subscriptionId must be a string, got {type(subscriptionId).__name__}")
    
    if not subscriptionId or not subscriptionId.strip():
        raise EmptySubscriptionIdError("subscriptionId cannot be empty or contain only whitespace")

    # Input validation for active parameter
    if not isinstance(active, bool):
        raise InvalidActiveParameterError(f"active must be a boolean, got {type(active).__name__}")

    # Check if subscription exists
    if subscriptionId not in DB["subscriptions"]:
        raise SubscriptionNotFoundError(f"Subscription with id '{subscriptionId}' not found")

    subscription = DB["subscriptions"][subscriptionId]
    subscription["active"] = active
    return subscription
