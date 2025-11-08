from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.db import DB
from .SimulationEngine import utils
from .SimulationEngine import custom_errors
from .SimulationEngine.models import AzmcpCosmosDatabaseListRetryParams
from .SimulationEngine.models import AzmcpCosmosDatabaseContainerListInputArgs
from .SimulationEngine.models import AzmcpCosmosAccountCreateInputArgs

@tool_spec(
    spec={
        'name': 'azmcp_cosmos_database_list',
        'description': """ List all databases in a Cosmos DB account.
        
        This function retrieves and displays all databases available in the specified Cosmos DB account.
        Results include database names and are returned as a list of dictionaries, where each dictionary
        represents a database resource. """,
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
                    'description': 'The name of the Cosmos DB account to query (e.g., my-cosmos-account).'
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
                    Defaults to None. (not implemented) """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can be
                    either the GUID identifier or the display name of your Azure AD tenant.
                    Defaults to None. (not implemented) """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for failed
                    operations before giving up. Defaults to None. (not implemented) """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts.
                    For exponential backoff, this value is used as the base. Defaults to None. (not implemented) """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. Defaults to None. (not implemented) """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent delays,
                    'exponential' increases delay between attempts. Defaults to None. (not implemented) """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds.
                    Operations taking longer than this will be cancelled. Defaults to None. (not implemented) """
                }
            },
            'required': [
                'subscription',
                'account_name'
            ]
        }
    }
)
def azmcp_cosmos_database_list(
    subscription: str,
    account_name: str,
    auth_method: Optional[str] = None,
    tenant: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all databases in a Cosmos DB account.

    This function retrieves and displays all databases available in the specified Cosmos DB account.
    Results include database names and are returned as a list of dictionaries, where each dictionary
    represents a database resource.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID
            identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the Cosmos DB account to query (e.g., my-cosmos-account).
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
            Defaults to None. (not implemented)
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be
            either the GUID identifier or the display name of your Azure AD tenant.
            Defaults to None. (not implemented)
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed
            operations before giving up. Defaults to None. (not implemented)
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts.
            For exponential backoff, this value is used as the base. Defaults to None. (not implemented)
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy. Defaults to None. (not implemented)
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays,
            'exponential' increases delay between attempts. Defaults to None. (not implemented)
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled. Defaults to None. (not implemented)

    Returns:
        List[Dict[str, Any]]: A list of database resources in the specified Cosmos DB account.
        Each dictionary in the list represents a database and contains the following keys:
            name (str): The user-defined name of the database.
            id (str): The unique resource ID of the database.

    Raises:
        ResourceNotFoundError: If the specified Azure subscription or Cosmos DB account does not exist.
        InvalidInputError: If required input parameters (e.g., 'subscription_id', 'account_name')
            are missing, or if any parameter is malformed or contains an invalid value.
    """
    # 1. Validate required inputs manually
    if not subscription:
        raise custom_errors.InvalidInputError("One or more input parameters are invalid or missing.")
    if not account_name:
        raise custom_errors.InvalidInputError("One or more input parameters are invalid or missing.")

    # 2. Validate optional retry parameters if provided
    retry_params_dict = {
        "retry_max_retries": retry_max_retries,
        "retry_delay": retry_delay,
        "retry_max_delay": retry_max_delay,
        "retry_mode": retry_mode,
        "retry_network_timeout": retry_network_timeout,
    }
    # Filter out None values, as Pydantic model fields are Optional
    # and we only want to validate parameters that were actually passed.
    provided_retry_params = {k: v for k, v in retry_params_dict.items() if v is not None}

    if provided_retry_params:
        try:
            _ = AzmcpCosmosDatabaseListRetryParams(**provided_retry_params)
        except PydanticValidationError:
            raise custom_errors.InvalidInputError("Input arguments failed validation.")

    # Attempt to find the subscription by ID first
    processed_subscription_data = utils.find_subscription(subscription_id=subscription)
    
    if not processed_subscription_data:
        # If not found by ID, assume 'subscription' might be a display name and try to find by that.
        all_subscriptions_in_db = DB.get("subscriptions", [])
        for sub_candidate_data in all_subscriptions_in_db:
            if sub_candidate_data.get("displayName") == subscription:
                subscription_id_from_name_match = sub_candidate_data.get("subscriptionId")
                if subscription_id_from_name_match:
                    processed_subscription_data = utils.find_subscription(subscription_id=subscription_id_from_name_match)
                if processed_subscription_data:
                    break 
    
    if not processed_subscription_data:
        raise custom_errors.ResourceNotFoundError("The specified Azure resource was not found.")

    actual_subscription_id = processed_subscription_data.get("subscriptionId")
    # This check is more for internal consistency of DB data if subscription was found.
    if not actual_subscription_id: # Should ideally not be hit if find_subscription works as expected
        # and DB data is consistent. Raising a generic ResourceNotFound as the subscription effectively isn't usable.
        raise custom_errors.ResourceNotFoundError("The specified Azure resource was not found.")


    cosmos_account_data = None
    for rg_data in processed_subscription_data.get("resource_groups", []):
        rg_name = rg_data.get("name")
        if not rg_name: 
            continue

        current_account_data = utils.find_cosmos_db_account(
            subscription_id=actual_subscription_id,
            resource_group_name=rg_name,
            account_name=account_name
        )
        if current_account_data:
            cosmos_account_data = current_account_data
            break

    if not cosmos_account_data:
        raise custom_errors.ResourceNotFoundError("The specified Azure resource was not found.")

    databases_list: List[Dict[str, Any]] = []
    for db_resource in cosmos_account_data.get("databases", []):
        db_name = db_resource.get("name")
        db_id = db_resource.get("id")

        if db_name is not None and db_id is not None: # Ensure essential fields are present
            databases_list.append({"name": db_name, "id": db_id})

    return databases_list

@tool_spec(
    spec={
        'name': 'azmcp_cosmos_database_container_list',
        'description': """ List all containers in a Cosmos DB database.
        
        This function retrieves and displays all containers within the specified database and Cosmos DB account.
        Results include container names and are returned as a JSON array. Both an account name and a
        database name must be specified. """,
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
                    'description': 'The name of the Cosmos DB account to query (e.g., my-cosmos-account).'
                },
                'database_name': {
                    'type': 'string',
                    'description': 'The name of the database to query (e.g., my-database).'
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. (not implemented) """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts. For
                    exponential backoff, this value is used as the base. (not implemented) """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries, regardless
                    of the retry strategy. (not implemented) """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for failed
                    operations before giving up. (not implemented) """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent delays,
                    'exponential' increases delay between attempts. (not implemented) """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds. Operations
                    taking longer than this will be cancelled. (not implemented) """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can be
                    either the GUID identifier or the display name of your Azure AD tenant. (not implemented) """
                }
            },
            'required': [
                'subscription',
                'account_name',
                'database_name'
            ]
        }
    }
)
def azmcp_cosmos_database_container_list(
    subscription: str,
    account_name: str,
    database_name: str,
    auth_method: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None,
    tenant: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all containers in a Cosmos DB database.
    This function retrieves and displays all containers within the specified database and Cosmos DB account.
    Results include container names and are returned as a JSON array. Both an account name and a
    database name must be specified.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID
            identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the Cosmos DB account to query (e.g., my-cosmos-account).
        database_name (str): The name of the database to query (e.g., my-database).
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. (not implemented)
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For
            exponential backoff, this value is used as the base. (not implemented)
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless
            of the retry strategy. (not implemented)
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed
            operations before giving up. (not implemented)
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays,
            'exponential' increases delay between attempts. (not implemented)
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations
            taking longer than this will be cancelled. (not implemented)
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be
            either the GUID identifier or the display name of your Azure AD tenant. (not implemented)
    Returns:
        List[Dict[str, Any]]: A list of containers in the database. Each dictionary in the list
            represents a container and includes the following keys:
            name (str): The name of the container.
            id (str): The resource ID of the container.
    Raises:
        ResourceNotFoundError: If the specified Cosmos DB account or database does not exist.
        InvalidInputError: If required parameters like account_name or database_name are missing.
        SubscriptionNotFoundError: If the specified Azure subscription is not found.
        ValidationError: If input arguments fail validation.
    """

    input_params_dict = {
        "subscription": subscription,
        "account_name": account_name,
        "database_name": database_name,
        "auth_method": auth_method,
        "retry_delay": retry_delay,
        "retry_max_delay": retry_max_delay,
        "retry_max_retries": retry_max_retries,
        "retry_mode": retry_mode,
        "retry_network_timeout": retry_network_timeout,
        "tenant": tenant
    }

    try:
        validated_args = AzmcpCosmosDatabaseContainerListInputArgs(**input_params_dict)
        subscription_val = validated_args.subscription
        account_name_val = validated_args.account_name
        database_name_val = validated_args.database_name
    except PydanticValidationError:
        raise custom_errors.ValidationError("Input validation failed")

    # 1. Find Subscription
    target_subscription_data = None
    all_subscriptions_in_db = DB.get("subscriptions", [])
    for sub_from_db in all_subscriptions_in_db:
        if sub_from_db.get("subscriptionId") == subscription_val or \
           sub_from_db.get("displayName") == subscription_val:
            target_subscription_data = sub_from_db
            break

    if not target_subscription_data:
        raise custom_errors.SubscriptionNotFoundError() # Uses default message

    # 2. Find Cosmos DB Account
    found_account_data = None
    # To store the name of the resource group for error messages if account is not found.
    # It will hold the name of the last RG searched or the only RG if only one exists.
    searched_rg_name_for_error_msg = None 

    resource_groups_in_sub = target_subscription_data.get("resource_groups", [])
    if not resource_groups_in_sub:
        # If the subscription exists but contains no resource groups, the account cannot be found.
        raise custom_errors.ResourceNotFoundError(
            f"Cosmos DB account '{account_name_val}' not found in subscription '{target_subscription_data.get('subscriptionId')}': The subscription contains no resource groups."
        )

    for rg_data in resource_groups_in_sub:
        searched_rg_name_for_error_msg = rg_data.get("name") 
        for acc_data in rg_data.get("cosmos_db_accounts", []):
            if acc_data.get("name") == account_name_val:
                found_account_data = acc_data
                # The actual RG of the found account is rg_data.get("name")
                break 
        if found_account_data:
            break 

    if not found_account_data:
        # Account not found. searched_rg_name_for_error_msg will be non-None here
        # because resource_groups_in_sub was checked to be non-empty.
        # target_subscription_data.get('subscriptionId') gives the canonical ID.
        raise custom_errors.ResourceNotFoundError(
            f"Cosmos DB account '{account_name_val}' not found in resource group '{searched_rg_name_for_error_msg}' and subscription '{target_subscription_data.get('subscriptionId')}'.")

    # 3. Find Database within the Account
    databases_in_account = found_account_data.get("databases", [])
    found_database_data_copy = utils._find_item_in_list(
        item_list_data=databases_in_account,
        key_name="name",
        key_value=database_name_val
    )

    if not found_database_data_copy:
        raise custom_errors.ResourceNotFoundError(
            f"Cosmos DB database '{database_name_val}' not found in account '{account_name_val}'."
        )

    # 4. Retrieve and Format Containers
    containers_in_database = found_database_data_copy.get("containers", [])
    result_list: List[Dict[str, Any]] = []

    for container_data_item in containers_in_database:
        container_name = container_data_item.get("name")
        container_id = container_data_item.get("id")

        if container_name and container_id:
            result_list.append({
                "name": container_name,
                "id": container_id
            })

    return result_list

@tool_spec(
    spec={
        'name': 'azmcp_cosmos_account_list',
        'description': """ List all Cosmos DB accounts in a subscription.
        
        This command retrieves and displays all Cosmos DB accounts available in the specified subscription. Results include account names and are returned as a JSON array. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': "Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. (not implemented)"
                },
                'tenant': {
                    'type': 'string',
                    'description': 'The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant. (not implemented)'
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': 'Maximum number of retry attempts for failed operations before giving up.(not implemented)'
                },
                'retry_delay': {
                    'type': 'string',
                    'description': 'Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base. (not implemented)'
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': 'Maximum delay in seconds between retries, regardless of the retry strategy. (not implemented)'
                },
                'retry_mode': {
                    'type': 'string',
                    'description': "Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts. (not implemented)"
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': 'Network operation timeout in seconds. Operations taking longer than this will be cancelled. (not implemented)'
                }
            },
            'required': [
                'subscription'
            ]
        }
    }
)
def azmcp_cosmos_account_list(
    subscription: str,
    auth_method: Optional[str] = None,
    tenant: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List all Cosmos DB accounts in a subscription.
    This command retrieves and displays all Cosmos DB accounts available in the specified subscription. Results include account names and are returned as a JSON array.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. (not implemented)
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant. (not implemented)
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up.(not implemented)
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base. (not implemented)    
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy. (not implemented)
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts. (not implemented)
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled. (not implemented)
    Returns:
        List[Dict[str, Any]]: A list of Cosmos DB accounts.
        Each dictionary in the list represents an account and contains the following keys:
            name (str): The name of the Cosmos DB account.
            id (str): The resource ID of the Cosmos DB account.
            location (str): The Azure region where the account is located.
            kind (str): The kind of Cosmos DB account (e.g., GlobalDocumentDB, MongoDB, Cassandra).
    Raises:
        SubscriptionNotFoundError: If the specified subscription ID is not found.
        ValidationError: If input arguments fail validation.
    """
    if not subscription:
        # Corrected error message to match the test expectation.
        raise custom_errors.ValidationError("Subscription ID or name must be provided.")

    if not isinstance(subscription, str):
        raise custom_errors.ValidationError("Subscription must be a string.")

    # Resolve the subscription argument (which can be an ID or name) to a subscription ID
    resolved_subscription_id: Optional[str] = None
    subscriptions_in_db: List[Dict[str, Any]] = DB.get("subscriptions", [])

    for sub_data_item in subscriptions_in_db:
        if sub_data_item.get("subscriptionId") == subscription:
            resolved_subscription_id = subscription
            break
    if not resolved_subscription_id:  # If not found by ID, try by name
        for sub_data_item in subscriptions_in_db:
            if sub_data_item.get("displayName") == subscription:
                resolved_subscription_id = sub_data_item.get("subscriptionId")
                break

    if not resolved_subscription_id:
        raise custom_errors.SubscriptionNotFoundError(
            f"Subscription '{subscription}' not found."
        )

    # Retrieve the subscription data using resolved ID
    # utils.find_subscription returns a copy of the subscription dict, or None
    target_sub_data: Optional[Dict[str, Any]] = utils.find_subscription(
        subscription_id=resolved_subscription_id
    )

    if not target_sub_data:
        # This situation implies an inconsistency if resolved_subscription_id was valid
        # but utils.find_subscription failed.
        raise custom_errors.SubscriptionNotFoundError(
            f"Subscription with ID '{resolved_subscription_id}' could not be retrieved."
        )

    cosmos_accounts_list: List[Dict[str, Any]] = []
    resource_groups: List[Dict[str, Any]] = target_sub_data.get("resource_groups", [])

    for rg_data in resource_groups:
        cosmos_db_accounts_in_rg: List[Dict[str, Any]] = rg_data.get(
            "cosmos_db_accounts", []
        )
        for account_data in cosmos_db_accounts_in_rg:
            account_info: Dict[str, Any] = {
                "name": account_data.get("name"),
                "id": account_data.get("id"),
                "location": account_data.get("location"),
                "kind": account_data.get("kind"),
            }

            # Check if all required fields for the output are present and are strings.
            # If a required field is missing (is None) or not a string, this account should be skipped.
            # This addresses the implicit requirement from the return type List[Dict[str, str]] for these fields.
            if not (
                isinstance(account_info.get("name"), str) and
                isinstance(account_info.get("id"), str) and
                isinstance(account_info.get("location"), str) and
                isinstance(account_info.get("kind"), str)
            ):
                # Skip this account if any of the required fields are missing or not strings.
                continue

            cosmos_accounts_list.append(account_info)

    return cosmos_accounts_list


@tool_spec(
    spec={
        'name': 'azmcp_cosmos_account_create',
        'description': """ Create a new Cosmos DB account in Azure.
        
        This function creates a new Cosmos DB account with the specified parameters in the given
        resource group and subscription. The account will be created with the specified kind
        (GlobalDocumentDB, MongoDB, or Parse) and location. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either the GUID
                    identifier or the display name of the Azure subscription to use. """
                },
                'resource_group': {
                    'type': 'string',
                    'description': """ The name of the resource group where the Cosmos DB account
                    will be created. """
                },
                'account_name': {
                    'type': 'string',
                    'description': """ The name of the Cosmos DB account to create. Must be globally
                    unique across all Azure subscriptions. """
                },
                'location': {
                    'type': 'string',
                    'description': """ The Azure region where the Cosmos DB account will be created
                    (e.g., "eastus", "westus2", "northeurope"). """
                },
                'kind': {
                    'type': 'string',
                    'description': """ The kind of Cosmos DB account to create. Options:
                    'GlobalDocumentDB' (default), 'MongoDB', 'Parse'. Defaults to "GlobalDocumentDB". """
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
                    Defaults to None. (not implemented) """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can be
                    either the GUID identifier or the display name of your Azure AD tenant.
                    Defaults to None. (not implemented) """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for failed
                    operations before giving up. Defaults to None. (not implemented) """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts.
                    For exponential backoff, this value is used as the base. Defaults to None. (not implemented) """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. Defaults to None. (not implemented) """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent delays,
                    'exponential' increases delay between attempts. Defaults to None. (not implemented) """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds.
                    Operations taking longer than this will be cancelled. Defaults to None. (not implemented) """
                }
            },
            'required': [
                'subscription',
                'resource_group',
                'account_name',
                'location'
            ]
        }
    }
)
def azmcp_cosmos_account_create(
    subscription: str,
    resource_group: str,
    account_name: str,
    location: str,
    kind: Optional[str] = "GlobalDocumentDB",
    auth_method: Optional[str] = None,
    tenant: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new Cosmos DB account in Azure.

    This function creates a new Cosmos DB account with the specified parameters in the given
    resource group and subscription. The account will be created with the specified kind
    (GlobalDocumentDB, MongoDB, or Parse) and location.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID
            identifier or the display name of the Azure subscription to use.
        resource_group (str): The name of the resource group where the Cosmos DB account
            will be created.
        account_name (str): The name of the Cosmos DB account to create. Must be globally
            unique across all Azure subscriptions.
        location (str): The Azure region where the Cosmos DB account will be created
            (e.g., "eastus", "westus2", "northeurope").
        kind (Optional[str]): The kind of Cosmos DB account to create. Options:
            'GlobalDocumentDB' (default), 'MongoDB', 'Parse'. Defaults to "GlobalDocumentDB".
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
            Defaults to None. (not implemented)
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be
            either the GUID identifier or the display name of your Azure AD tenant.
            Defaults to None. (not implemented)
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed
            operations before giving up. Defaults to None. (not implemented)
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts.
            For exponential backoff, this value is used as the base. Defaults to None. (not implemented)
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy. Defaults to None. (not implemented)
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays,
            'exponential' increases delay between attempts. Defaults to None. (not implemented)
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled. Defaults to None. (not implemented)

    Returns:
        Dict[str, Any]: Details of the created Cosmos DB account. Contains the following keys:
            name (str): The name of the created Cosmos DB account.
            id (str): The resource ID of the created Cosmos DB account.
            location (str): The Azure region where the account is located.
            kind (str): The kind of Cosmos DB account (e.g., GlobalDocumentDB, MongoDB).
            resource_group_name (str): The name of the resource group containing the account.
            subscription_id (str): The subscription ID where the account was created.
            provisioning_state (str): The provisioning state of the account (e.g., "Succeeded").
            databases (List[Dict]): A list of database resources in the specified Cosmos DB account.
                Each dictionary in the list represents a database and contains the following keys:
                    name (str): The user-defined name of the database.
                    id (str): The unique resource ID of the database.

    Raises:
        ResourceNotFoundError: If the specified Azure subscription or resource group does not exist.
        InvalidInputError: If required input parameters are missing, or if any parameter is
            malformed or contains an invalid value.
        ConflictError: If a Cosmos DB account with the same name already exists in the specified resource group.
        ValidationError: If input arguments fail validation.
    """
    # Validate input parameters using Pydantic model
    input_params_dict = {
        "subscription": subscription,
        "resource_group": resource_group,
        "account_name": account_name,
        "location": location,
        "kind": kind,
        "auth_method": auth_method,
        "tenant": tenant,
        "retry_max_retries": retry_max_retries,
        "retry_delay": retry_delay,
        "retry_max_delay": retry_max_delay,
        "retry_mode": retry_mode,
        "retry_network_timeout": retry_network_timeout
    }

    try:
        validated_args = AzmcpCosmosAccountCreateInputArgs(**input_params_dict)
        subscription_val = validated_args.subscription
        resource_group_val = validated_args.resource_group
        account_name_val = validated_args.account_name
        location_val = validated_args.location
        kind_val = validated_args.kind
    except PydanticValidationError:
        raise custom_errors.ValidationError("Input validation failed")

    # Find the subscription
    target_subscription_data = None
    all_subscriptions_in_db = DB.get("subscriptions", [])
    for sub_from_db in all_subscriptions_in_db:
        if sub_from_db.get("subscriptionId") == subscription_val or sub_from_db.get("displayName") == subscription_val:
            target_subscription_data = sub_from_db
            break

    if not target_subscription_data:
        raise custom_errors.SubscriptionNotFoundError()

    # Find the resource group
    found_resource_group = None
    resource_groups_in_sub = target_subscription_data.get("resource_groups", [])
    for rg_data in resource_groups_in_sub:
        if rg_data.get("name") == resource_group_val:
            found_resource_group = rg_data
            break

    if not found_resource_group:
        raise custom_errors.ResourceNotFoundError(
            f"Resource group '{resource_group_val}' not found in subscription '{target_subscription_data.get('subscriptionId')}'."
        )

    # Check if a Cosmos DB account with the same name already exists in the resource group
    existing_cosmos_accounts = found_resource_group.get("cosmos_db_accounts", [])
    for existing_account in existing_cosmos_accounts:
        if existing_account.get("name") == account_name_val:
            raise custom_errors.ConflictError(
                f"Cosmos DB account '{account_name_val}' already exists in resource group '{resource_group_val}'."
            )

    # Create the new Cosmos DB account
    new_account_id = utils.generate_arm_id(
        subscription_id=target_subscription_data.get("subscriptionId"),
        resource_group_name=resource_group_val,
        provider="DocumentDB",
        resource_type="databaseAccounts",
        resource_name=account_name_val
    )

    new_cosmos_account = {
        "id": new_account_id,
        "name": account_name_val,
        "location": location_val,
        "kind": kind_val,
        "resource_group_name": resource_group_val,
        "subscription_id": target_subscription_data.get("subscriptionId"),
        "provisioning_state": "Succeeded",
        "databases": []
    }

    # Add the new account to the resource group
    found_resource_group.setdefault("cosmos_db_accounts", []).append(new_cosmos_account)

    # Return the created account details
    return {
        "name": new_cosmos_account["name"],
        "id": new_cosmos_account["id"],
        "location": new_cosmos_account["location"],
        "kind": new_cosmos_account["kind"],
        "resource_group_name": new_cosmos_account["resource_group_name"],
        "subscription_id": new_cosmos_account["subscription_id"],
        "provisioning_state": new_cosmos_account["provisioning_state"],
        "databases": new_cosmos_account["databases"]
    }
