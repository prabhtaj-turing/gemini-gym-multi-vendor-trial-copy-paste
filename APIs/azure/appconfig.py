from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any, Optional

from .SimulationEngine.db import DB
from .SimulationEngine import utils
from .SimulationEngine.models import LockedAppConfigKeyValueItem, AuthMethod
from .SimulationEngine import custom_errors
from .SimulationEngine import models

@tool_spec(
    spec={
        'name': 'azmcp_appconfig_kv_lock',
        'description': """ Lock a key-value in an App Configuration store.
        
        This function sets a key-value in an App Configuration store to read-only mode,
        preventing any modifications to its value. It requires an account name and key
        to be specified. Optionally, a label can be provided to lock a specific
        labeled version of the key-value. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
                },
                'account_name': {
                    'type': 'string',
                    'description': 'The name of the App Configuration store (e.g., my-appconfig).'
                },
                'key': {
                    'type': 'string',
                    'description': 'The name of the key to access within the App Configuration store.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': "Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. Defaults to None."
                },
                'tenant': {
                    'type': 'string',
                    'description': 'The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant. Defaults to None.'
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': 'Maximum number of retry attempts for failed operations before giving up. Defaults to None.'
                },
                'retry_delay': {
                    'type': 'string',
                    'description': 'Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base. Defaults to None.'
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': 'Maximum delay in seconds between retries, regardless of the retry strategy. Defaults to None.'
                },
                'retry_mode': {
                    'type': 'string',
                    'description': "Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts. Defaults to None."
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': 'Network operation timeout in seconds. Operations taking longer than this will be cancelled. Defaults to None.'
                },
                'label': {
                    'type': 'string',
                    'description': 'The label to apply to the configuration key. Labels are used to group and organize settings. Defaults to None.'
                }
            },
            'required': [
                'subscription',
                'account_name',
                'key'
            ]
        }
    }
)
def azmcp_appconfig_kv_lock(
    subscription: str, 
    account_name: str, 
    key: str,          
    auth_method: Optional[str] = None,
    tenant: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None,
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """Lock a key-value in an App Configuration store.

    This function sets a key-value in an App Configuration store to read-only mode,
    preventing any modifications to its value. It requires an account name and key
    to be specified. Optionally, a label can be provided to lock a specific
    labeled version of the key-value.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the App Configuration store (e.g., my-appconfig).
        key (str): The name of the key to access within the App Configuration store.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant. Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up. Defaults to None.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base. Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts. Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled. Defaults to None.
        label (Optional[str]): The label to apply to the configuration key. Labels are used to group and organize settings. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing the details of the locked key-value item with the following keys:
            key (str): The key of the configuration setting.
            value (str): The value of the configuration setting.
            label (Optional[str]): The label of the configuration setting. This can be null if the key-value does not have an assigned label.
            content_type (Optional[str]): The content type of the key-value's value. This can be null if no content type is set.
            etag (str): An opaque string representing the state of the key-value, used for optimistic concurrency control.
            last_modified (str): The Coordinated Universal Time (UTC) timestamp of when the key-value was last modified, in ISO 8601 format.
            locked (bool): A boolean flag indicating whether the key-value is locked. This will be true for a successfully locked item.

    Raises:
        ResourceNotFoundError: If the specified App Configuration store, or the key-value identified by the given key and label, does not exist.
        InvalidInputError: If required parameters such as 'account_name' or 'key' are missing, or if any parameter has an invalid format.
        ConflictError: If the specified key-value is already locked.
    """

    # 1. Input Validation
    if subscription is None:
        raise custom_errors.InvalidInputError("Parameter 'subscription' is required.")
    if subscription == "":
        raise custom_errors.InvalidInputError("Parameter 'subscription' cannot be empty.")

    if account_name is None:
        raise custom_errors.InvalidInputError("Parameter 'account_name' is required.")
    if account_name == "":
        raise custom_errors.InvalidInputError("Parameter 'account_name' cannot be empty.")

    if key is None:
        raise custom_errors.InvalidInputError("Parameter 'key' is required.")
    if key == "":
        raise custom_errors.InvalidInputError("Parameter 'key' cannot be empty.")

    # Authentication and retry parameters are not used in this simulation's direct DB manipulation
    # but are part of the signature for interface consistency with potential real Azure SDKs.

    # 2. Find Subscription
    sub_ref = utils.get_subscription_ref(subscription_id=subscription)
    if not sub_ref:
        raise custom_errors.ResourceNotFoundError(
            f"Subscription '{subscription}' not found."
        )

    # 3. Find the App Configuration Store's resource group
    found_rg_name_for_store = None
    resource_groups_list_ref = sub_ref.get("resource_groups", [])
    for rg_iter_ref in resource_groups_list_ref:
        app_config_stores_list_ref = rg_iter_ref.setdefault("app_config_stores", [])
        store_ref_candidate = utils._get_item_ref_in_list(
            app_config_stores_list_ref, "name", account_name
        )
        if store_ref_candidate:
            found_rg_name_for_store = rg_iter_ref.get("name")
            break 

    if not found_rg_name_for_store:
      raise custom_errors.ResourceNotFoundError(
            f"App Configuration store '{account_name}' not found in subscription '{subscription}'."
        )
      
    # 4. Get a reference to the key-value item
    target_kv_item_ref = utils.get_app_config_key_value_ref(
        subscription_id=subscription,
        resource_group_name=found_rg_name_for_store,
        store_name=account_name,
        key=key,
        label=label
    )
    
    # 5. Check if the key-value item was found
    # Use 'None' for display when label is None, as expected by tests
    label_for_error_msg = f"'{label}'" if label is not None else "'None'"
    
    if not target_kv_item_ref:
        raise custom_errors.ResourceNotFoundError(
            f"Key-value item with key '{key}' and label {label_for_error_msg} not found in App Configuration store '{account_name}'."
        )

    # 6. Lock Logic: Check if already locked, then lock it.
    if target_kv_item_ref.get("locked", False):
        raise custom_errors.ConflictError(
            f"Key-value item with key '{key}' and label {label_for_error_msg} is already locked."
        )

    target_kv_item_ref["locked"] = True
    target_kv_item_ref["last_modified"] = utils.get_current_utc_timestamp_iso()
    target_kv_item_ref["etag"] = utils.new_uuid_str() 

    # 7. Construct and return the result dictionary
    result = LockedAppConfigKeyValueItem(
        key=target_kv_item_ref["key"],
        value=target_kv_item_ref["value"],
        label=target_kv_item_ref.get("label"), 
        content_type=target_kv_item_ref.get("content_type"), 
        etag=target_kv_item_ref["etag"],
        last_modified=target_kv_item_ref["last_modified"],
        locked=target_kv_item_ref["locked"]
    )
    
    return result.model_dump()

@tool_spec(
    spec={
        'name': 'azmcp_appconfig_kv_delete',
        'description': """ Delete a key-value pair from an App Configuration store.
        
        This command removes the specified key-value pair from the store.
        If a label is specified, only the labeled version is deleted. If no label is specified, the key-value with the matching
        key and the default label will be deleted. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
                },
                'account_name': {
                    'type': 'string',
                    'description': 'The name of the App Configuration store (e.g., my-appconfig).'
                },
                'key': {
                    'type': 'string',
                    'description': 'The name of the key to access within the App Configuration store.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': "Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'."
                },
                'label': {
                    'type': 'string',
                    'description': 'The label to apply to the configuration key. Labels are used to group and organize settings.'
                },
                'retry_delay': {
                    'type': 'string',
                    'description': 'Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.'
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': 'Maximum delay in seconds between retries, regardless of the retry strategy.'
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': 'Maximum number of retry attempts for failed operations before giving up.'
                },
                'retry_mode': {
                    'type': 'string',
                    'description': "Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts."
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': 'Network operation timeout in seconds. Operations taking longer than this will be cancelled.'
                },
                'tenant': {
                    'type': 'string',
                    'description': 'The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.'
                }
            },
            'required': [
                'subscription',
                'account_name',
                'key'
            ]
        }
    }
)
def azmcp_appconfig_kv_delete(
    subscription: str,
    account_name: str,
    key: str,
    auth_method: Optional[str] = None,
    label: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None,
    tenant: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete a key-value pair from an App Configuration store.

    This command removes the specified key-value pair from the store.
    If a label is specified, only the labeled version is deleted. If no label is specified, the key-value with the matching
    key and the default label will be deleted.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the App Configuration store (e.g., my-appconfig).
        key (str): The name of the key to access within the App Configuration store.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        label (Optional[str]): The label to apply to the configuration key. Labels are used to group and organize settings.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.

    Returns:
        Dict[str, Any]: An empty dictionary.

    Raises:
        ResourceNotFoundError: The specified App Configuration store was not found, or the key-value pair (with the specified key and label, if provided) does not exist in the store.
        InvalidInputError: One or more required input parameters are missing or invalid. For example, 'account_name' or 'key' might be empty, or a parameter might have an incorrect format.
    """
    # Validate required input parameters
    if subscription is None:
        raise custom_errors.InvalidInputError("Subscription is required.")
    if not subscription: # Catches empty string ""
        raise custom_errors.InvalidInputError("Subscription cannot be empty.")

    if account_name is None:
        raise custom_errors.InvalidInputError("Account name is required.")
    if not account_name: # Catches empty string ""
        raise custom_errors.InvalidInputError("Account name cannot be empty.")

    if key is None:
        raise custom_errors.InvalidInputError("Key is required.")
    if not key: # Catches empty string ""
        raise custom_errors.InvalidInputError("Key cannot be empty.")
    
    # The 'auth_method', 'retry_*', and 'tenant' parameters are not used in this simulation's core logic.

    # Find the subscription.
    target_subscription_data = utils.find_subscription(subscription_id=subscription)
    if not target_subscription_data:
        raise custom_errors.ResourceNotFoundError(f"Subscription '{subscription}' not found.")

    # Find the App Configuration store.
    found_rg_name_for_store = None
    store_actually_exists = False
    for rg_data in target_subscription_data.get("resource_groups", []):
        current_rg_name = rg_data["name"]
        store_data = utils.find_app_config_store(
            subscription_id=subscription,
            resource_group_name=current_rg_name,
            store_name=account_name
        )
        if store_data:
            found_rg_name_for_store = current_rg_name
            store_actually_exists = True
            break
    
    if not store_actually_exists:
        raise custom_errors.ResourceNotFoundError(
            f"App Configuration store '{account_name}' not found in subscription '{subscription}'."
        )

    # Attempt to delete the key-value pair using the utility function.
    # `utils.delete_app_config_kv` returns True if deleted, False if not found.
    # Store existence is already confirmed, so False from `delete_app_config_kv` means the KV itself was not found.
    deleted = utils.delete_app_config_kv(
        subscription_id=subscription,
        resource_group_name=found_rg_name_for_store,
        store_name=account_name,
        key=key,
        label=label
    )

    if not deleted:
        # Key-value pair was not found in the store.
        if label is not None:
            message = f"Key-value with key '{key}' and label '{label}' not found in store '{account_name}'."
        else:
            message = f"Key-value with key '{key}' and default label not found in store '{account_name}'."
        raise custom_errors.ResourceNotFoundError(message)

    # Operation was successful. Return empty dictionary as per Source of Truth.
    return {}


@tool_spec(
    spec={
        'name': 'azmcp_appconfig_account_list',
        'description': """ List all App Configuration stores in a subscription.
        
        This function retrieves and displays all App Configuration stores available in the
        specified subscription. The results are returned as a list of dictionaries,
        where each dictionary contains details of an App Configuration store,
        including its name, ID, and location. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either
                    the GUID identifier or the display name of the Azure subscription to use. """
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options:
                    'credential' (Azure CLI/managed identity), 'key' (access key),
                    or 'connectionString'. Defaults to None. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name.
                    This can be either the GUID identifier or the display name of your
                    Azure AD tenant. Defaults to None. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for
                    failed operations before giving up. Defaults to None. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry
                    attempts. For exponential backoff, this value is used as the base.
                    Defaults to None. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. Defaults to None. """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses
                    consistent delays, 'exponential' increases delay between attempts.
                    Defaults to None. """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in
                    seconds. Operations taking longer than this will be cancelled.
                    Defaults to None. """
                }
            },
            'required': [
                'subscription'
            ]
        }
    }
)
def azmcp_appconfig_account_list(
    subscription: str,
    auth_method: Optional[str] = None,
    tenant: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all App Configuration stores in a subscription.

    This function retrieves and displays all App Configuration stores available in the
    specified subscription. The results are returned as a list of dictionaries,
    where each dictionary contains details of an App Configuration store,
    including its name, ID, and location.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either
            the GUID identifier or the display name of the Azure subscription to use.
        auth_method (Optional[str]): Authentication method to use. Options:
            'credential' (Azure CLI/managed identity), 'key' (access key),
            or 'connectionString'. Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name.
            This can be either the GUID identifier or the display name of your
            Azure AD tenant. Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for
            failed operations before giving up. Defaults to None.
        retry_delay (Optional[str]): Initial delay in seconds between retry
            attempts. For exponential backoff, this value is used as the base.
            Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses
            consistent delays, 'exponential' increases delay between attempts.
            Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in
            seconds. Operations taking longer than this will be cancelled.
            Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of App Configuration stores. Each dictionary
        in the list represents an App Configuration store and contains the
        following keys:
            name (str): The name of the App Configuration store.
            id (str): The resource ID of the App Configuration store.
            location (str): The Azure region where the store is located.

    Raises:
        SubscriptionNotFoundError: If the specified subscription ID is not found.
        ValidationError: If input arguments fail validation.
    """
    # Validate subscription argument
    if not isinstance(subscription, str) or not subscription.strip():
        # Changed message to match test expectation for empty string.
        # This also implies that if subscription is None, this same error will be raised.
        raise custom_errors.ValidationError("Subscription ID or name must be provided.")

    # The optional arguments (auth_method, tenant, retry_*) are not used in this simulation's
    # core logic for listing resources from the DB, as they pertain to external interactions
    # or behaviors not modeled here. They are part of the function signature for API compatibility.

    # Access subscriptions data from the DB
    all_subscriptions_in_db = DB.get("subscriptions")

    # Find the target subscription by ID or display name
    target_subscription_data: Optional[Dict[str, Any]] = None
    for sub_in_db in all_subscriptions_in_db:
        if sub_in_db.get("subscriptionId") == subscription or sub_in_db.get("displayName") == subscription:
            target_subscription_data = sub_in_db
            break
    
    if target_subscription_data is None:
        raise custom_errors.SubscriptionNotFoundError(f"Subscription '{subscription}' not found.")

    # Prepare the list to hold App Configuration store details
    app_config_stores_list: List[Dict[str, Any]] = []

    # Get resource groups from the found subscription
    current_resource_groups = target_subscription_data.get("resource_groups")
    
    for rg_data in current_resource_groups:
        
        app_config_stores_in_rg_data = rg_data.get("app_config_stores")
        
        current_app_config_stores: List[Dict[str, Any]] = []
        if app_config_stores_in_rg_data is None:
            # No App Configuration stores in this resource group, or key is missing/None.
            pass # current_app_config_stores remains empty
        elif not isinstance(app_config_stores_in_rg_data, list):
            # Malformed app_config_stores for this RG. Skip this RG's stores.
            pass # current_app_config_stores remains empty
        else:
            current_app_config_stores = app_config_stores_in_rg_data

        for store_data in current_app_config_stores:
            if not isinstance(store_data, dict):
                # Skip malformed App Configuration store entries
                continue

            store_name = store_data.get("name")
            store_id = store_data.get("id")
            store_location = store_data.get("location")

            app_config_store_item = models.AppConfigStoreListItem(
                name=store_name,
                id=store_id,
                location=store_location
            )
            app_config_stores_list.append(app_config_store_item.model_dump())

    return app_config_stores_list

@tool_spec(
    spec={
        'name': 'azmcp_appconfig_kv_list',
        'description': """ List all key-values in an App Configuration store.
        
        This command retrieves and displays all key-value pairs
        from the specified store. Each key-value includes its key, value, label, content type, ETag, last modified
        time, and lock status. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either the GUID
                    identifier or the display name of the Azure subscription to use. """
                },
                'account_name': {
                    'type': 'string',
                    'description': 'The name of the App Configuration store (e.g., my-appconfig).'
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. """
                },
                'key': {
                    'type': 'string',
                    'description': """ Specifies the key filter, if any, to be used when retrieving
                    key-values. The filter can be an exact match, for example a filter of "foo"
                    would get all key-values with a key of "foo", or the filter can include a '*'
                    character at the end of the string for wildcard searches (e.g., 'App*').
                    If omitted all keys will be retrieved. """
                },
                'label': {
                    'type': 'string',
                    'description': """ Specifies the label filter, if any, to be used when retrieving
                    key-values. The filter can be an exact match, for example a filter of "foo"
                    would get all key-values with a label of "foo", or the filter can include a '*'
                    character at the end of the string for wildcard searches (e.g., 'Prod*').
                    This filter is case-sensitive. If omitted, all labels will be retrieved. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts. For
                    exponential backoff, this value is used as the base. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries, regardless
                    of the retry strategy. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for failed
                    operations before giving up. """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent delays,
                    'exponential' increases delay between attempts. """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds. Operations
                    taking longer than this will be cancelled. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can be
                    either the GUID identifier or the display name of your Azure AD tenant. """
                }
            },
            'required': [
                'subscription',
                'account_name'
            ]
        }
    }
)
def azmcp_appconfig_kv_list(
        subscription: str,
        account_name: str,
        auth_method: Optional[str] = None,
        key: Optional[str] = None,
        label: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None,
        tenant: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """List all key-values in an App Configuration store.
    This command retrieves and displays all key-value pairs
    from the specified store. Each key-value includes its key, value, label, content type, ETag, last modified
    time, and lock status.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID
            identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the App Configuration store (e.g., my-appconfig).
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        key (Optional[str]): Specifies the key filter, if any, to be used when retrieving
            key-values. The filter can be an exact match, for example a filter of "foo"
            would get all key-values with a key of "foo", or the filter can include a '*'
            character at the end of the string for wildcard searches (e.g., 'App*').
            If omitted all keys will be retrieved.
        label (Optional[str]): Specifies the label filter, if any, to be used when retrieving
            key-values. The filter can be an exact match, for example a filter of "foo"
            would get all key-values with a label of "foo", or the filter can include a '*'
            character at the end of the string for wildcard searches (e.g., 'Prod*').
            This filter is case-sensitive. If omitted, all labels will be retrieved.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For
            exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless
            of the retry strategy.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed
            operations before giving up.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays,
            'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations
            taking longer than this will be cancelled.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be
            either the GUID identifier or the display name of your Azure AD tenant.
    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing the function's results, with the
          following key:
          key_value_items (List[Dict[str, Any]]): A list of key-value items. Each item is a
            dictionary representing a key-value and contains the following fields:
            key (str): The unique name of the key.
            value (str): The value associated with the key.
            label (Optional[str]): The label associated with the key-value. If no label is
              assigned, this will be null (represented as `None` in Python).
            content_type (Optional[str]): The content type of the value (e.g.,
              'application/json', 'text/plain'). If not set, this will be null
              (represented as `None` in Python).
            etag (str): An opaque string representing the version of the key-value, used for
              optimistic concurrency control.
            last_modified (str): The Coordinated Universal Time (UTC) timestamp of the last
              modification, in ISO 8601 format (e.g., 'YYYY-MM-DDTHH:mm:ssZ').
            locked (bool): A boolean flag indicating whether the key-value is locked and
              cannot be modified or deleted.
    Raises:
        ResourceNotFoundError: If the specified Azure App Configuration store does not exist.
        InvalidInputError: If any of the input parameters are invalid (e.g., missing required parameters, incorrect format, or out-of-range values).
        SubscriptionNotFoundError: If the specified subscription does not exist.
    """
    # Parameter validation for required arguments
    if not subscription:
        raise custom_errors.InvalidInputError("Subscription ID or name must be provided.")
    if not account_name:
        raise custom_errors.InvalidInputError("App Configuration store name (account_name) must be provided.")

    # Validate auth_method if provided
    if auth_method is not None and auth_method not in ['credential', 'key', 'connectionString']:
        raise custom_errors.InvalidInputError(
            "auth_method must be one of: 'credential', 'key', or 'connectionString'"
        )

    # Validate retry parameters if provided
    if retry_delay is not None:
        try:
            retry_delay_float = float(retry_delay)
            if retry_delay_float <= 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_delay must be a positive number")

    if retry_max_delay is not None:
        try:
            retry_max_delay_float = float(retry_max_delay)
            if retry_max_delay_float <= 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_delay must be a positive number")

    if retry_max_retries is not None:
        try:
            retry_max_retries_int = int(retry_max_retries)
            if retry_max_retries_int < 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_retries must be a non-negative integer")

    if retry_mode is not None and retry_mode not in ['fixed', 'exponential']:
        raise custom_errors.InvalidInputError("retry_mode must be either 'fixed' or 'exponential'")

    if retry_network_timeout is not None:
        try:
            retry_network_timeout_float = float(retry_network_timeout)
            if retry_network_timeout_float <= 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_network_timeout must be a positive number")

    # Validate key and label patterns if provided
    if key is not None and not isinstance(key, str):
        raise custom_errors.InvalidInputError("key must be a string")

    if label is not None and not isinstance(label, str):
        raise custom_errors.InvalidInputError("label must be a string")

    # Validate tenant if provided
    if tenant is not None and not isinstance(tenant, str):
        raise custom_errors.InvalidInputError("tenant must be a string")

    subscriptions_list = DB.get("subscriptions", [])
    sub_data_found = None
    for s_data_item in subscriptions_list:
        if s_data_item.get("subscriptionId") == subscription or s_data_item.get("displayName") == subscription:
            sub_data_found = s_data_item
            break

    if not sub_data_found:
        raise custom_errors.SubscriptionNotFoundError(f"Subscription '{subscription}' not found.")

    app_config_store_data = None
    resource_groups_in_sub = sub_data_found.get("resource_groups", [])
    for rg_data in resource_groups_in_sub:
        app_config_stores_in_rg = rg_data.get("app_config_stores", [])
        for store_item_data in app_config_stores_in_rg:
            if store_item_data.get("name") == account_name:
                app_config_store_data = store_item_data
                break
        if app_config_store_data:
            break

    if not app_config_store_data:
        raise custom_errors.ResourceNotFoundError(
            f"App Configuration store '{account_name}' not found in subscription '{subscription}'."
        )

    all_kv_items_in_store = app_config_store_data.get("key_values", [])
    filtered_kv_data_list = utils.filter_app_config_key_values(
        key_value_list_data=all_kv_items_in_store,
        key_filter=key,
        label_filter=label
    )

    output_key_value_items = []
    for kv_item_data in filtered_kv_data_list:
        output_item = {
            "key": kv_item_data.get("key"),
            "value": kv_item_data.get("value"),
            "label": kv_item_data.get("label"),
            "content_type": kv_item_data.get("content_type"),
            "etag": kv_item_data.get("etag"),
            "last_modified": kv_item_data.get("last_modified"),
            "locked": kv_item_data.get("locked", False)
        }
        output_key_value_items.append(output_item)

    return {"key_value_items": output_key_value_items}

@tool_spec(
    spec={
        'name': 'azmcp_appconfig_kv_unlock',
        'description': """ Unlock a key-value setting in an App Configuration store.
        
        This command removes the read-only mode from a key-value setting, allowing modifications to its value.
        It requires an account name and key to be specified. Optionally, a label can be specified to unlock
        a specific labeled version of the setting; otherwise, the setting with the default label will be unlocked. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'account_name': {
                    'type': 'string',
                    'description': 'The name of the App Configuration store (e.g., my-appconfig).'
                },
                'key': {
                    'type': 'string',
                    'description': 'The name of the key to access within the App Configuration store.'
                },
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': "Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'."
                },
                'label': {
                    'type': 'string',
                    'description': 'The label to apply to the configuration key. Labels are used to group and organize settings.'
                },
                'retry_delay': {
                    'type': 'string',
                    'description': 'Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.'
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': 'Maximum delay in seconds between retries, regardless of the retry strategy.'
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': 'Maximum number of retry attempts for failed operations before giving up.'
                },
                'retry_mode': {
                    'type': 'string',
                    'description': "Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts."
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': 'Network operation timeout in seconds. Operations taking longer than this will be cancelled.'
                },
                'tenant': {
                    'type': 'string',
                    'description': 'The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.'
                }
            },
            'required': [
                'account_name',
                'key',
                'subscription'
            ]
        }
    }
)
def azmcp_appconfig_kv_unlock(
        account_name: str,
        key: str,
        subscription: str,
        auth_method: Optional[str] = None,
        label: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None,
        tenant: Optional[str] = None
) -> Dict[str, Any]:
    """Unlock a key-value setting in an App Configuration store.
    This command removes the read-only mode from a key-value setting, allowing modifications to its value.
    It requires an account name and key to be specified. Optionally, a label can be specified to unlock
    a specific labeled version of the setting; otherwise, the setting with the default label will be unlocked.
    Args:
        account_name (str): The name of the App Configuration store (e.g., my-appconfig).
        key (str): The name of the key to access within the App Configuration store.
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        label (Optional[str]): The label to apply to the configuration key. Labels are used to group and organize settings.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.
    Returns:
        Dict[str, Any]: A dictionary containing the details of the unlocked key-value item with the following keys:
            key (str): The key of the configuration setting.
            value (str): The value of the configuration setting.
            label (Optional[str]): The label of the configuration setting. If null, it's the default label.
            content_type (Optional[str]): The content type of the value.
            etag (str): The ETag for optimistic concurrency control.
            last_modified (str): The timestamp of the last modification in ISO 8601 format.
            locked (bool): Indicates if the key-value is locked (will be false after successful unlock).
    Raises:
        ResourceNotFoundError: If the specified App Configuration store, key, or key with the specified label does not exist.
        InvalidInputError: If required parameters like 'account_name' or 'key' are missing or malformed.
        ConflictError: If the specified key-value setting is already unlocked.
        SubscriptionNotFoundError: If the specified subscription does not exist.
    """
    # Validate required parameters
    if not isinstance(account_name, str) or not account_name.strip():
        raise custom_errors.InvalidInputError("App Configuration store name ('account_name') must be a non-empty string.")

    if not isinstance(key, str) or not key.strip():
        raise custom_errors.InvalidInputError("Key name ('key') must be a non-empty string.")

    if not isinstance(subscription, str) or not subscription.strip():
        raise custom_errors.InvalidInputError("Subscription ID or name ('subscription') must be a non-empty string.")

    # Validate optional parameters if provided
    if auth_method is not None:
        if not isinstance(auth_method, str) or auth_method not in ['credential', 'key', 'connectionString']:
            raise custom_errors.InvalidInputError("auth_method must be one of: 'credential', 'key', 'connectionString'")

    if label is not None:
        if not isinstance(label, str):
            raise custom_errors.InvalidInputError("label must be a string")

    # Validate retry parameters if provided
    if retry_delay is not None:
        try:
            float(retry_delay)
        except ValueError:
            raise custom_errors.InvalidInputError("retry_delay must be a valid number")

    if retry_max_delay is not None:
        try:
            float(retry_max_delay)
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_delay must be a valid number")

    if retry_max_retries is not None:
        try:
            int(retry_max_retries)
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_retries must be a valid integer")

    if retry_mode is not None:
        if not isinstance(retry_mode, str) or retry_mode not in ['fixed', 'exponential']:
            raise custom_errors.InvalidInputError("retry_mode must be either 'fixed' or 'exponential'")

    if retry_network_timeout is not None:
        try:
            float(retry_network_timeout)
        except ValueError:
            raise custom_errors.InvalidInputError("retry_network_timeout must be a valid number")

    if tenant is not None:
        if not isinstance(tenant, str) or not tenant.strip():
            raise custom_errors.InvalidInputError("tenant must be a non-empty string")

    # --- Resolve Subscription ---
    resolved_subscription_ref = None
    subscriptions_list = DB.get("subscriptions", [])

    for sub_in_db in subscriptions_list:
        if sub_in_db.get("subscriptionId") == subscription or sub_in_db.get("displayName") == subscription:
            resolved_subscription_ref = sub_in_db
            break

    if not resolved_subscription_ref:
        raise custom_errors.SubscriptionNotFoundError(f"Subscription '{subscription}' not found.")

    # --- Find App Configuration Store ---
    target_store_ref = None
    for rg_ref in resolved_subscription_ref.get("resource_groups", []):
        for store_in_rg_ref in rg_ref.get("app_config_stores", []):
            if store_in_rg_ref.get("name") == account_name:
                target_store_ref = store_in_rg_ref
                break
        if target_store_ref:
            break

    if not target_store_ref:
        raise custom_errors.ResourceNotFoundError(
            f"App Configuration store '{account_name}' not found in subscription '{subscription}'."
        )

    # --- Find Key-Value Item ---
    kv_item_ref = None
    key_values_list_ref = target_store_ref.setdefault("key_values", [])

    for item_ref in key_values_list_ref:
        if item_ref.get("key") == key and item_ref.get("label") == label:
            kv_item_ref = item_ref
            break

    label_display_for_error = f"'{label}'" if label is not None else "(none)"
    if not kv_item_ref:
        raise custom_errors.ResourceNotFoundError(
            f"Key-value with key '{key}' and label {label_display_for_error} not found in App Configuration store '{account_name}'."
        )

    # --- Unlock Logic ---
    # If 'locked' is False or missing (schema default is False), it's already unlocked.
    if not kv_item_ref.get("locked", False):
        raise custom_errors.ConflictError(
            f"Key-value '{key}' with label {label_display_for_error} in store '{account_name}' is already unlocked."
        )

    kv_item_ref["locked"] = False
    kv_item_ref["last_modified"] = utils.get_current_utc_timestamp_iso()
    kv_item_ref["etag"] = utils.new_uuid_str()

    # --- Prepare Return Value ---
    return {
        "key": kv_item_ref["key"],
        "value": kv_item_ref["value"],  # Assumed to exist and be a string per AppConfigKeyValueItem schema
        "label": kv_item_ref.get("label"),
        "content_type": kv_item_ref.get("content_type"),
        "etag": kv_item_ref["etag"],
        "last_modified": kv_item_ref["last_modified"],
        "locked": kv_item_ref["locked"],  # Will be False
    }

@tool_spec(
    spec={
        'name': 'azmcp_appconfig_kv_set',
        'description': """ Set a key-value setting in an App Configuration store.
        
        This function sets a key-value setting in an App Configuration store. It creates or
        updates a key-value setting with the specified value. An account name, key, and
        value must be specified. Optionally, a label can be specified; otherwise, the
        default label is used. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either the
                    GUID identifier or the display name of the Azure subscription to use. """
                },
                'account_name': {
                    'type': 'string',
                    'description': 'The name of the App Configuration store (e.g., my-appconfig).'
                },
                'key': {
                    'type': 'string',
                    'description': 'The name of the key to access within the App Configuration store.'
                },
                'value': {
                    'type': 'string',
                    'description': 'The value to set for the configuration key.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. """
                },
                'label': {
                    'type': 'string',
                    'description': """ The label to apply to the configuration key. Labels are
                    used to group and organize settings. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts.
                    For exponential backoff, this value is used as the base. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for
                    failed operations before giving up. """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent
                    delays, 'exponential' increases delay between attempts. """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds.
                    Operations taking longer than this will be cancelled. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can
                    be either the GUID identifier or the display name of your Azure AD tenant. """
                }
            },
            'required': [
                'subscription',
                'account_name',
                'key',
                'value'
            ]
        }
    }
)
def azmcp_appconfig_kv_set(
        subscription: str,
        account_name: str,
        key: str,
        value: str,
        auth_method: Optional[str] = None,
        label: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None,
        tenant: Optional[str] = None
) -> Dict[str, Any]:
    """Set a key-value setting in an App Configuration store.
    This function sets a key-value setting in an App Configuration store. It creates or
    updates a key-value setting with the specified value. An account name, key, and
    value must be specified. Optionally, a label can be specified; otherwise, the
    default label is used.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the
            GUID identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the App Configuration store (e.g., my-appconfig).
        key (str): The name of the key to access within the App Configuration store.
        value (str): The value to set for the configuration key.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        label (Optional[str]): The label to apply to the configuration key. Labels are
            used to group and organize settings.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts.
            For exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for
            failed operations before giving up.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent
            delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can
            be either the GUID identifier or the display name of your Azure AD tenant.
    Returns:
        Dict[str, Any]: A dictionary containing the details of the created or updated
            key-value item, with the following keys:
            key (str): The key of the configuration setting.
            value (str): The value of the configuration setting.
            label (Optional[str]): The label of the configuration setting. A null or
                empty string typically represents 'no label'.
            content_type (Optional[str]): The content type of the value (e.g.,
                'application/json', 'text/plain'). If not set by the user, it
                might be inferred by the service.
            etag (str): An opaque ETag value used for optimistic concurrency control.
                This value changes whenever the key-value is updated, helping
                prevent accidental overwrites.
            last_modified (str): The timestamp of the last modification, in ISO 8601
                format (e.g., 'YYYY-MM-DDTHH:mm:ssZ').
            locked (bool): A boolean indicating whether the key-value is locked.
                Locked key-values cannot be modified or deleted until explicitly
                unlocked.
    Raises:
        ResourceNotFoundError: If the specified App Configuration store (account-name)
            or subscription does not exist.
        InvalidInputError: If required parameters such as 'account_name', 'key', or
            'value' are missing, or if provided parameters are malformed.
        ConflictError: If attempting to update a key-value that is locked and the
            operation is not permitted, or if an ETag mismatch occurs during an
            optimistic concurrency update.
        ServiceError: If an unexpected error occurs within the Azure App Configuration
            service during the operation.
    """
    # Validate required input parameters
    if not(isinstance(subscription, str) and subscription.strip()):
        raise custom_errors.InvalidInputError("Subscription ID or name must be provided as a non-empty string.")

    if not(isinstance(account_name, str) and account_name.strip()):
        raise custom_errors.InvalidInputError("App Configuration store name (account_name) must be provided as a non-empty string.")

    if not(isinstance(key, str) and key.strip()):
        raise custom_errors.InvalidInputError("Configuration key must be provided as a non-empty string.")

    if value is None or not isinstance(value, str):
        raise custom_errors.InvalidInputError("Configuration value must be provided as a string.")

    # Validate optional parameters
    if auth_method is not None:
        if not isinstance(auth_method, str):
            raise custom_errors.InvalidInputError("auth_method must be a string.")
        try:
            auth_method = AuthMethod(auth_method)
        except ValueError:
            valid_methods = [method.value for method in AuthMethod]
            raise custom_errors.InvalidInputError(
                f"Invalid auth_method. Must be one of: {', '.join(valid_methods)}"
            )

    if label is not None and not isinstance(label, str):
        raise custom_errors.InvalidInputError("label must be a string.")

    # Validate retry parameters
    if retry_delay is not None:
        try:
            retry_delay = float(retry_delay)
            if retry_delay <= 0:
                raise custom_errors.InvalidInputError("retry_delay must be greater than 0.")
        except ValueError:
            raise custom_errors.InvalidInputError("retry_delay must be a valid number string.")

    if retry_max_delay is not None:
        try:
            retry_max_delay = float(retry_max_delay)
            if retry_max_delay <= 0:
                raise custom_errors.InvalidInputError("retry_max_delay must be a positive number.")
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_delay must be a valid number string.")

    if retry_max_retries is not None:
        try:
            retry_max_retries = int(retry_max_retries)
            if retry_max_retries < 1:
                raise custom_errors.InvalidInputError("retry_max_retries must be at least 1.")
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_retries must be a valid integer string.")

    if retry_mode is not None:
        if not isinstance(retry_mode, str):
            raise custom_errors.InvalidInputError("retry_mode must be a string.")
        valid_retry_modes = ['fixed', 'exponential']
        if retry_mode not in valid_retry_modes:
            raise custom_errors.InvalidInputError(f"retry_mode must be one of: {', '.join(valid_retry_modes)}")

    if retry_network_timeout is not None:
        try:
            retry_network_timeout = float(retry_network_timeout)
            if retry_network_timeout <= 0:
                raise custom_errors.InvalidInputError("retry_network_timeout must be a positive number.")
        except ValueError:
            raise custom_errors.InvalidInputError("retry_network_timeout must be a valid number string.")

    if tenant is not None and not isinstance(tenant, str):
        raise custom_errors.InvalidInputError("tenant must be a string.")

    # Find the subscription
    subscription_ref = utils.get_subscription_ref(subscription)
    if not subscription_ref:
        raise custom_errors.ResourceNotFoundError(f"Subscription '{subscription}' not found.")

    target_store_ref = None
    resource_group_name_of_store = None

    for rg_ref in subscription_ref.get("resource_groups", []):
        app_config_stores_list = rg_ref.setdefault("app_config_stores", [])
        for store_item_ref in app_config_stores_list:
            if store_item_ref.get("name") == account_name:
                target_store_ref = store_item_ref
                resource_group_name_of_store = rg_ref.get("name")
                break
        if target_store_ref:
            break

    if not target_store_ref or not resource_group_name_of_store:
        raise custom_errors.ResourceNotFoundError(
            f"App Configuration store '{account_name}' not found in subscription '{subscription}'."
        )

    existing_kv_ref = utils.get_app_config_key_value_ref(
        subscription_id=subscription,
        resource_group_name=resource_group_name_of_store,
        store_name=account_name,
        key=key,
        label=label
    )

    if existing_kv_ref and existing_kv_ref.get("locked", False):
        label_display = f"'{label}'" if label is not None else "(No Label)"
        raise custom_errors.ConflictError(
            f"The key-value '{key}' with label {label_display} is locked and cannot be modified."
        )

    kv_data_to_upsert = models.AppConfigKeyValueUpsertData(
        key=key,
        value=value,
        label=label
    )

    operation_successful = utils.update_or_create_app_config_kv(
        subscription_id=subscription,
        resource_group_name=resource_group_name_of_store,
        store_name=account_name,
        kv_data_to_upsert=kv_data_to_upsert.model_dump()
    )

    if not operation_successful:
        raise custom_errors.ServiceError(
            f"Failed to set key-value '{key}' in App Configuration store '{account_name}'. "
            "An unexpected error occurred during the update/create operation."
        )

    final_kv_item = utils.find_app_config_key_value(
        subscription_id=subscription,
        resource_group_name=resource_group_name_of_store,
        store_name=account_name,
        key=key,
        label=label
    )

    if not final_kv_item:
        raise custom_errors.ServiceError(
            f"Failed to retrieve key-value '{key}' after setting it. "
            "The set operation appeared successful, but the item could not be found subsequently."
        )

    result = models.SetAppConfigKeyValueItem(
        key=final_kv_item.get("key"),
        value=final_kv_item.get("value"),
        label=final_kv_item.get("label"),
        content_type=final_kv_item.get("content_type"),
        etag=final_kv_item.get("etag"),
        last_modified=final_kv_item.get("last_modified"),
        locked=final_kv_item.get("locked", False)
    )
    
    return result.model_dump()

@tool_spec(
    spec={
        'name': 'azmcp_appconfig_kv_show',
        'description': """ Show a specific key-value setting in an App Configuration store.
        
        This function retrieves and displays the value, label, content type, ETag,
        last modified time, and lock status for a specific key-value setting.
        An account name and key must be specified. Optionally, a label can be
        specified; if no label is provided, the setting with the default label
        will be retrieved. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either the GUID
                    identifier or the display name of the Azure subscription to use. """
                },
                'account_name': {
                    'type': 'string',
                    'description': 'The name of the App Configuration store (e.g., my-appconfig).'
                },
                'key': {
                    'type': 'string',
                    'description': 'The name of the key to access within the App Configuration store.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
                    Defaults to None. """
                },
                'label': {
                    'type': 'string',
                    'description': """ The label to apply to the configuration key. Labels are used
                    to group and organize settings. Defaults to None, which implies the default
                    label. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts. For
                    exponential backoff, this value is used as the base. Defaults to None. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. Defaults to None. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for failed
                    operations before giving up. Defaults to None. """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent delays,
                    'exponential' increases delay between attempts. Defaults to None. """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds.
                    Operations taking longer than this will be cancelled. Defaults to None. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can be
                    either the GUID identifier or the display name of your Azure AD tenant.
                    Defaults to None. """
                }
            },
            'required': [
                'subscription',
                'account_name',
                'key'
            ]
        }
    }
)
def azmcp_appconfig_kv_show(
        subscription: str,
        account_name: str,
        key: str,
        auth_method: Optional[str] = None,
        label: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None,
        tenant: Optional[str] = None
) -> Dict[str, Any]:
    """Show a specific key-value setting in an App Configuration store.
    This function retrieves and displays the value, label, content type, ETag,
    last modified time, and lock status for a specific key-value setting.
    An account name and key must be specified. Optionally, a label can be
    specified; if no label is provided, the setting with the default label
    will be retrieved.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID
            identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the App Configuration store (e.g., my-appconfig).
        key (str): The name of the key to access within the App Configuration store.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
            Defaults to None.
        label (Optional[str]): The label to apply to the configuration key. Labels are used
            to group and organize settings. Defaults to None, which implies the default
            label.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For
            exponential backoff, this value is used as the base. Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy. Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed
            operations before giving up. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays,
            'exponential' increases delay between attempts. Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled. Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be
            either the GUID identifier or the display name of your Azure AD tenant.
            Defaults to None.
    Returns:
        Dict[str, Any]: Details of the specific key-value item. Contains the following keys:
            key (str): The key of the configuration setting.
            value (str): The value of the configuration setting.
            label (Optional[str]): The label of the configuration setting. If not
                specified, it implies the null label (often represented as '\\0').
            content_type (Optional[str]): The content type of the value.
            etag (str): The ETag for optimistic concurrency control.
            last_modified (str): The timestamp of the last modification (ISO 8601 format).
            locked (bool): Indicates if the key-value is locked.
    Raises:
        ResourceNotFoundError: If the specified App Configuration store, key, or label
            does not exist.
        InvalidInputError: If required parameters like account-name or key are missing.
        ServiceError: If there is an issue with the Azure App Configuration service.
        ValidationError: If input arguments fail validation.
    """
    # Validate required inputs
    if not subscription or not isinstance(subscription, str):
        raise custom_errors.InvalidInputError("Subscription ID or name must be provided as a non-empty string.")
    if not account_name or not isinstance(account_name, str):
        raise custom_errors.InvalidInputError(
            "App Configuration store name (account_name) must be provided as a non-empty string.")
    if not key or not isinstance(key, str):
        raise custom_errors.InvalidInputError("Key must be provided as a non-empty string.")

    # Validate auth_method if provided
    allowed_auth_methods = ['credential', 'key', 'connectionString']
    if auth_method is not None:
        if not isinstance(auth_method, str):
            raise custom_errors.ValidationError("auth_method must be a string.")
        if auth_method not in allowed_auth_methods:
            raise custom_errors.ValidationError(
                f"Invalid auth_method: '{auth_method}'. Allowed values are {allowed_auth_methods}."
            )

    # Validate label if provided
    if label is not None and not isinstance(label, str):
        raise custom_errors.ValidationError("label must be a string.")

    # Validate retry parameters if provided
    if retry_delay is not None:
        try:
            retry_delay = float(retry_delay)
            if retry_delay < 0:
                raise custom_errors.ValidationError('Value for retry_delay must be non-negative.')
        except ValueError:
            raise custom_errors.ValidationError("retry_delay must be a valid number string.")

    if retry_max_delay is not None:
        try:
            float(retry_max_delay)
        except ValueError:
            raise custom_errors.ValidationError("retry_max_delay must be a valid number string.")

    if retry_max_retries is not None:
        try:
            int(retry_max_retries)
        except ValueError:
            raise custom_errors.ValidationError("retry_max_retries must be a valid integer string.")

    if retry_mode is not None:
        if not isinstance(retry_mode, str):
            raise custom_errors.ValidationError("retry_mode must be a string.")
        if retry_mode not in ['fixed', 'exponential']:
            raise custom_errors.ValidationError("retry_mode must be either 'fixed' or 'exponential'.")

    if retry_network_timeout is not None:
        try:
            float(retry_network_timeout)
        except ValueError:
            raise custom_errors.ValidationError("retry_network_timeout must be a valid number string.")

    # Validate tenant if provided
    if tenant is not None and not isinstance(tenant, str):
        raise custom_errors.ValidationError("tenant must be a string.")

    # Validate account_name format
    if not account_name.replace('-', '').replace('_', '').isalnum():
        raise custom_errors.ValidationError(
            "App Configuration store name (account_name) can only contain letters, numbers, hyphens, and underscores."
        )

    subscription_data = utils.find_subscription(subscription_id=subscription)
    if not subscription_data:
        raise custom_errors.SubscriptionNotFoundError(
            f"Subscription '{subscription}' not found."
        )

    found_store_data: Optional[Dict[str, Any]] = None
    resource_groups: List[Dict[str, Any]] = subscription_data.get("resource_groups", [])

    for rg_data in resource_groups:
        app_config_stores: List[Dict[str, Any]] = rg_data.get("app_config_stores", [])
        for store_item in app_config_stores:
            if store_item.get("name") == account_name:
                found_store_data = store_item
                break
        if found_store_data:
            break

    if not found_store_data:
        raise custom_errors.ResourceNotFoundError(
            f"App Configuration store '{account_name}' not found in subscription '{subscription}'."
        )

    # Find the key-value item in the store
    key_values_list: List[Dict[str, Any]] = found_store_data.get("key_values", [])
    found_kv_item: Optional[Dict[str, Any]] = None
    for kv_item in key_values_list:
        if kv_item.get("key") == key and kv_item.get("label") == label:
            found_kv_item = kv_item
            break

    if not found_kv_item:
        label_description = f"and label '{label}'" if label is not None else "and default (null) label"
        raise custom_errors.ResourceNotFoundError(
            f"Key-value with key '{key}' {label_description} not found in App Configuration store '{account_name}'."
        )

    result = {
        "key": found_kv_item.get("key"),
        "value": found_kv_item.get("value"),
        "label": found_kv_item.get("label"),
        "content_type": found_kv_item.get("content_type"),
        "etag": found_kv_item.get("etag"),
        "last_modified": found_kv_item.get("last_modified"),
        "locked": found_kv_item.get("locked", False)
    }

    if result["key"] is None or result["value"] is None or result["etag"] is None or result["last_modified"] is None:
        raise custom_errors.ServiceError(
            f"Retrieved key-value item for key '{key}' in store '{account_name}' is incomplete or malformed."
        )

    return result
