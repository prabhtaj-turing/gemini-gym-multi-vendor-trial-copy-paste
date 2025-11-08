from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, List, Dict, Any, Union

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors
from .SimulationEngine import models
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.models import AzmcpGroupListInput, AzmcpGroupListItem

@tool_spec(
    spec={
        'name': 'azmcp_subscription_list',
        'description': """ List all Azure subscriptions accessible to your account.
        
        This function lists all Azure subscriptions accessible to the account. It optionally allows specifying a tenant and authentication method. Results include subscription names and IDs, returned as a list of dictionaries. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'auth_method': {
                    'type': 'string',
                    'description': "Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'."
                },
                'tenant': {
                    'type': 'string',
                    'description': 'The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.'
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': 'Maximum number of retry attempts for failed operations before giving up.'
                },
                'retry_delay': {
                    'type': 'string',
                    'description': 'Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.'
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': 'Maximum delay in seconds between retries, regardless of the retry strategy.'
                },
                'retry_mode': {
                    'type': 'string',
                    'description': "Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts."
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': 'Network operation timeout in seconds. Operations taking longer than this will be cancelled.'
                }
            },
            'required': []
        }
    }
)
def azmcp_subscription_list(
    auth_method: Optional[str] = None,
    tenant: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all Azure subscriptions accessible to your account.

    This function lists all Azure subscriptions accessible to the account. It optionally allows specifying a tenant and authentication method. Results include subscription names and IDs, returned as a list of dictionaries.

    Args:
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled.

    Returns:
        List[Dict[str, Any]]: A list of Azure subscriptions accessible to the account. Each dictionary in the list represents a subscription and contains the following keys:
            id (str): The subscription ID (GUID).
            subscriptionId (str): The subscription ID (GUID, often duplicated for convenience).
            displayName (str): The friendly name of the subscription.
            state (str): The state of the subscription (e.g., 'Enabled', 'Warned', 'PastDue', 'Disabled').
            tenantId (str): The tenant ID associated with the subscription.

    Raises:
        TenantNotFoundError: If a specified tenant ID is invalid or inaccessible.
        ValidationError: If input arguments fail validation.
    """

    # Input validation for string choice parameters
    ALLOWED_AUTH_METHODS = [member.value for member in models.AuthMethod]
    if auth_method is not None and auth_method not in ALLOWED_AUTH_METHODS:
        raise custom_errors.ValidationError(
            f"Invalid auth_method: '{auth_method}'. Allowed values are: {', '.join(ALLOWED_AUTH_METHODS)}."
        )

    ALLOWED_RETRY_MODES = [member.value for member in models.RetryMode]
    if retry_mode is not None and retry_mode not in ALLOWED_RETRY_MODES:
        raise custom_errors.ValidationError(
            f"Invalid retry_mode: '{retry_mode}'. Allowed values are: {', '.join(ALLOWED_RETRY_MODES)}."
        )

    # Input validation for numeric string parameters
    if retry_max_retries is not None:
        try:
            num = int(retry_max_retries)
            if num < 0:
                raise custom_errors.ValidationError(
                    f"Parameter 'retry_max_retries' must be 0 or greater, but received '{retry_max_retries}' (evaluates to {num})."
                )
        except ValueError:
            raise custom_errors.ValidationError(
                f"Parameter 'retry_max_retries' ('{retry_max_retries}') is not a valid string representation of an integer."
            )
    
    float_strings_to_validate = {"retry_delay": retry_delay, "retry_max_delay": retry_max_delay, "retry_network_timeout": retry_network_timeout}
    for param_name, param_value in float_strings_to_validate.items():
        if param_value is None:
            continue

        try:
            num = float(param_value)
            
            if num < 0:
                raise custom_errors.ValidationError(
                    f"Parameter '{param_name}' must be 0 or greater, but received '{param_value}' (evaluates to {num})."
                )
        except ValueError:
            raise custom_errors.ValidationError(
                f"Parameter '{param_name}' ('{param_value}') is not a valid string representation of a number."
            )
    
    # Additional validation: retry_max_delay should not be less than retry_delay if both are provided
    if retry_delay is not None and retry_max_delay is not None:
        # At this point, if not None, they are valid numeric strings due to prior validation.
        delay_val = float(retry_delay)
        max_delay_val = float(retry_max_delay)
        if max_delay_val < delay_val:
            raise custom_errors.ValidationError(
                f"retry_max_delay ('{retry_max_delay}') cannot be less than retry_delay ('{retry_delay}')."
            )

    # Retrieve subscriptions from the DB; defaults to empty list if 'subscriptions' key is missing or value is None.
    all_subscriptions_data = DB.get("subscriptions") or []
    
    result_subscriptions: List[Dict[str, Any]] = []
    
    for sub_data in all_subscriptions_data:
        
        current_sub_item = models.SubscriptionListItem(
            id= sub_data["subscriptionId"],
            subscriptionId= sub_data["subscriptionId"],
            displayName= sub_data["displayName"],
            state= sub_data["state"],
            tenantId= sub_data["tenantId"],
        ).model_dump()
    
        # Filter by tenant if specified.
        if tenant is not None:
            # Compare the tenantId from the (potentially well-formed) current_sub_item.
            if current_sub_item["tenantId"] == tenant:
                result_subscriptions.append(current_sub_item)
        else: # No tenant filter, include all (well-formed) subscriptions.
            result_subscriptions.append(current_sub_item)

    # If a tenant was specified and no subscriptions were found for it (i.e., result_subscriptions is empty),
    # raise TenantNotFoundError. This uses the default message from the error class,
    # which aligns with the "Source of Truth" and test expectations.
    if tenant is not None and not result_subscriptions:
        raise custom_errors.TenantNotFoundError('The specified Azure tenant was not found or is inaccessible.')
        
    return result_subscriptions



@tool_spec(
    spec={
        'name': 'azmcp_group_list',
        'description': """ List all resource groups in a subscription.
        
        This function retrieves all resource groups available in the specified subscription.
        Results include resource group names and IDs, returned as a list of dictionaries,
        where each dictionary represents a resource group. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either the
                    GUID identifier or the display name of the Azure subscription to use. """
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can
                    be either the GUID identifier or the display name of your Azure AD tenant. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for
                    failed operations before giving up. Expected to be a string representing an integer. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts.
                    For exponential backoff, this value is used as the base. Expected to be a string representing an integer. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. Expected to be a string representing an integer. """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent
                    delays, 'exponential' increases delay between attempts. """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds.
                    Operations taking longer than this will be cancelled. Expected to be a string representing an integer. """
                }
            },
            'required': [
                'subscription'
            ]
        }
    }
)
def azmcp_group_list(
    subscription: str,
    auth_method: Optional[str] = None,
    tenant: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all resource groups in a subscription.
    This function retrieves all resource groups available in the specified subscription.
    Results include resource group names and IDs, returned as a list of dictionaries,
    where each dictionary represents a resource group.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the
            GUID identifier or the display name of the Azure subscription to use.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can
            be either the GUID identifier or the display name of your Azure AD tenant.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for
            failed operations before giving up. Expected to be a string representing an integer.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts.
            For exponential backoff, this value is used as the base. Expected to be a string representing an integer.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy. Expected to be a string representing an integer.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent
            delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled. Expected to be a string representing an integer.
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a
        resource group and contains the following keys:
            name (str): The name of the resource group.
            id (str): The resource ID of the resource group.
            location (str): The Azure region where the resource group is located.
            managedBy (Optional[str]): The ID of the resource that manages this
                resource group, if applicable.
            tags (Optional[Dict[str, str]]): Tags associated with the resource group.
    Raises:
        SubscriptionNotFoundError: If the specified subscription ID is not found.
        ValidationError: If input arguments fail validation.
    """
    raw_args = {
        "subscription": subscription,
        "auth_method": auth_method,
        "tenant": tenant,
        "retry_max_retries": retry_max_retries,
        "retry_delay": retry_delay,
        "retry_max_delay": retry_max_delay,
        "retry_mode": retry_mode,
        "retry_network_timeout": retry_network_timeout,
    }

    try:
        validated_args = AzmcpGroupListInput(**raw_args)
    except PydanticValidationError as e:
        error_detail = e.errors()[0]
        error_type = error_detail.get('type')

        # Standardize message for integer parsing errors to match test expectations
        if error_type == 'int_parsing':
            final_msg = "Input should be a valid integer"
        else:
            final_msg = error_detail['msg']
        raise custom_errors.ValidationError(final_msg)

    # The auth_method, tenant, and retry_* arguments are validated but not used further
    # in this simulated environment as data is fetched directly from the DB.

    found_subscription_data: Optional[Dict[str, Any]] = None

    subscriptions_list = DB.get("subscriptions", [])

    for sub_data_item in subscriptions_list:
        if sub_data_item.get("subscriptionId") == validated_args.subscription or \
           sub_data_item.get("displayName") == validated_args.subscription:
            found_subscription_data = sub_data_item
            break

    if not found_subscription_data:
        raise custom_errors.SubscriptionNotFoundError(
            "The specified Azure subscription was not found or is not accessible."
        )

    resource_groups_data = found_subscription_data.get("resource_groups", [])

    result_list: List[Dict[str, Any]] = []
    for rg_data in resource_groups_data:
        try:
            validated_rg_item = AzmcpGroupListItem(**rg_data)
            result_list.append(validated_rg_item.model_dump())
        except PydanticValidationError as e:
            # This handles cases where the DB data itself is malformed.
            # For this simulation, we'll skip malformed entries, but you could log errors.
            continue

    return result_list