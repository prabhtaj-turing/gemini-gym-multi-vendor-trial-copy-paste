from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, List, Optional
from .SimulationEngine import custom_errors
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine.db import DB
from .SimulationEngine.models import AzmcpStorageBlobContainerDetailsInput, AzmcpStorageBlobContainerDetailsOutput
from azure.SimulationEngine import utils
from azure.SimulationEngine.db import DB
from azure.SimulationEngine.models import AuthMethod, StorageAccountKind, StorageTableListItem, RetryMode, OutputBlobItem, StorageBlobProperties
from azure.SimulationEngine.utils import get_subscription_data_by_id_or_name
from .SimulationEngine.models import StorageAccountListItem, AzureSku, RetryModesOps
from .SimulationEngine.models import StorageBlobContainerListItem



@tool_spec(
    spec={
        'name': 'azmcp_storage_blob_container_details',
        'description': """ Gets detailed properties of a storage container including metadata, lease status, and access level.
        
        This function gets detailed properties of a storage container, including its metadata,
        lease status, and access level. It requires an account-name and container-name
        for identification of the target container. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
                },
                'account_name': {
                    'type': 'string',
                    'description': "The name of the Azure Storage account. This is the unique name you chose for your storage account (e.g., 'mystorageaccount')."
                },
                'container_name': {
                    'type': 'string',
                    'description': 'The name of the container to access within the storage account.'
                },
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
            'required': [
                'subscription',
                'account_name',
                'container_name'
            ]
        }
    }
)
def azmcp_storage_blob_container_details(
    subscription: str,
    account_name: str,
    container_name: str,
    auth_method: Optional[str] = None,
    tenant: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None
) -> Dict[str, Any]:
    """Gets detailed properties of a storage container including metadata, lease status, and access level.

    This function gets detailed properties of a storage container, including its metadata,
    lease status, and access level. It requires an account-name and container-name
    for identification of the target container.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the Azure Storage account. This is the unique name you chose for your storage account (e.g., 'mystorageaccount').
        container_name (str): The name of the container to access within the storage account.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled.

    Returns:
        Dict[str, Any]: A dictionary containing the detailed properties of the storage container. It includes the following keys:
            name (str): The name of the container.
            lastModified (str): Timestamp of the last modification (ISO 8601 format).
            etag (str): The ETag of the container.
            leaseStatus (str): The lease status of the container (e.g., 'locked', 'unlocked').
            leaseState (str): The lease state of the container (e.g., 'available', 'leased', 'expired', 'breaking', 'broken').
            publicAccess (Optional[str]): The level of public access for the container (e.g., 'blob', 'container', or null if no public access).
            hasImmutabilityPolicy (bool): Indicates if the container has an immutability policy.
            hasLegalHold (bool): Indicates if the container has a legal hold.
            metadata (Optional[Dict[str, str]]): User-defined metadata for the container.

    Raises:
        ResourceNotFoundError: If the specified storage account or container does not exist.
        InvalidInputError: If required parameters `account_name` or `container_name` are missing or empty.
        ValidationError: If input arguments fail type or other Pydantic validation.
        ServiceError: If the data is malformed and fails output validation.
    """
    # Prepare arguments for Pydantic validation
    # If None is passed for required string fields, Pydantic treats it as a type error.
    # To align with tests expecting "missing" or "Field required" errors,
    # we remove these keys from the dict passed to Pydantic if their value is None.
    pydantic_input_args = {
        "subscription": subscription,
        "account_name": account_name,
        "container_name": container_name,
        "auth_method": auth_method,
        "tenant": tenant,
        "retry_max_retries": retry_max_retries,
        "retry_delay": retry_delay,
        "retry_max_delay": retry_max_delay,
        "retry_mode": retry_mode,
        "retry_network_timeout": retry_network_timeout,
    }

    # For required fields, if None was passed, remove them so Pydantic sees them as 'missing'
    if subscription is None:
        pydantic_input_args.pop("subscription", None)
    if account_name is None:
        pydantic_input_args.pop("account_name", None)
    if container_name is None:
        pydantic_input_args.pop("container_name", None)

    try:
        # AzmcpStorageBlobContainerDetailsInput is expected to be in the global scope
        validated_args = AzmcpStorageBlobContainerDetailsInput(**pydantic_input_args)
        subscription = validated_args.subscription
        account_name = validated_args.account_name
        container_name = validated_args.container_name
        # Optional args can be accessed from validated_args if their validated form is needed
    except PydanticValidationError as e:
        for error in e.errors():
            field_name = error['loc'][0] if error['loc'] and isinstance(error['loc'], tuple) else ''
            error_type = error['type']

            if field_name == 'account_name':
                if error_type == 'missing':
                    raise custom_errors.InvalidInputError("Required parameter 'account_name' is missing.")
                elif error_type == 'string_too_short': 
                    raise custom_errors.InvalidInputError("Required parameter 'account_name' cannot be empty.")
            elif field_name == 'container_name':
                if error_type == 'missing':
                    raise custom_errors.InvalidInputError("Required parameter 'container_name' is missing.")
                elif error_type == 'string_too_short':
                    raise custom_errors.InvalidInputError("Required parameter 'container_name' cannot be empty.")
        
        # If the error was not one of the custom-mapped InvalidInputErrors above,
        # raise a generic ValidationError using the first Pydantic error message.
        # This assumes e.errors() is not empty, which is true if PydanticValidationError was caught.
        first_error_msg = e.errors()[0]['msg']
        raise custom_errors.ValidationError(first_error_msg)

    target_subscription_obj = None
    for sub_obj_in_db in DB.get("subscriptions", []):
        if sub_obj_in_db.get("subscriptionId") == subscription or sub_obj_in_db.get("displayName") == subscription:
            target_subscription_obj = sub_obj_in_db
            break
    
    if not target_subscription_obj:
        raise custom_errors.ResourceNotFoundError(f"Storage account '{account_name}' not found.")

    found_container_data = None
    storage_account_exists_in_subscription = False

    for rg_obj in target_subscription_obj.get("resource_groups", []):
        for sa_obj in rg_obj.get("storage_accounts", []):
            if sa_obj.get("name") == account_name:
                storage_account_exists_in_subscription = True
                for cont_obj in sa_obj.get("blob_containers", []):
                    if cont_obj.get("name") == container_name:
                        # Ensure container belongs to the correct storage account (already implied by structure but good for clarity)
                        if cont_obj.get("account_name") == account_name:
                            found_container_data = cont_obj
                            break 
                if found_container_data:
                    break 
        if found_container_data:
            break 

    if not found_container_data:
        if storage_account_exists_in_subscription:
            raise custom_errors.ResourceNotFoundError(
                f"Container '{container_name}' not found in storage account '{account_name}'."
            )
        else:
            raise custom_errors.ResourceNotFoundError(f"Storage account '{account_name}' not found.")

    name_val = found_container_data.get("name")
    last_modified_val = found_container_data.get("lastModified")
    etag_val = found_container_data.get("etag")

    if name_val is None or last_modified_val is None or etag_val is None:
         raise custom_errors.ServiceError(
             f"Incomplete data for container '{container_name}' in account '{account_name}'. "
             "Essential properties (name, lastModified, or etag) are missing from the stored data."
         )

    lease_status_val = found_container_data.get("leaseStatus", "unlocked")
    lease_state_val = found_container_data.get("leaseState", "available")
    public_access_val = found_container_data.get("publicAccess") 
    has_immutability_policy_val = found_container_data.get("hasImmutabilityPolicy", False)
    has_legal_hold_val = found_container_data.get("hasLegalHold", False)
    metadata_val = found_container_data.get("metadata")

    try:
        # Use the Pydantic model to validate and structure the output data
        result_model = AzmcpStorageBlobContainerDetailsOutput(
            name=name_val,
            lastModified=last_modified_val,
            etag=etag_val,
            leaseStatus=lease_status_val,
            leaseState=lease_state_val,
            publicAccess=public_access_val,
            hasImmutabilityPolicy=has_immutability_policy_val,
            hasLegalHold=has_legal_hold_val,
            metadata=metadata_val,
        )
        # Convert the model to a dictionary for the return value
        # Using model_dump() is the standard for Pydantic V2
        return result_model.model_dump()
    except PydanticValidationError as e:
        # This handles cases where data from the DB is malformed and fails output validation
        raise custom_errors.ServiceError(f"Failed to serialize container properties due to invalid data: {e}")

@tool_spec(
    spec={
        'name': 'azmcp_storage_blob_list',
        'description': """ List all blobs in a Storage container.
        
        This command retrieves and displays all blobs available in the specified
        container and Storage account. Results include blob names, sizes, and
        content types, returned as a JSON array. Requires account-name and
        container-name. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be
                    either the GUID identifier or the display name of the Azure
                    subscription to use. """
                },
                'account_name': {
                    'type': 'string',
                    'description': """ The name of the Azure Storage account. This is the
                    unique name you chose for your storage account (e.g.,
                    'mystorageaccount'). """
                },
                'container_name': {
                    'type': 'string',
                    'description': """ The name of the container to access within the
                    storage account. """
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options:
                    'credential' (Azure CLI/managed identity), 'key' (access key),
                    or 'connectionString'. Defaults to None. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry
                    attempts. For exponential backoff, this value is used as the base.
                    Defaults to None. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between
                    retries, regardless of the retry strategy. Defaults to None. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts
                    for failed operations before giving up. Defaults to None. """
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
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name.
                    This can be either the GUID identifier or the display name of your
                    Azure AD tenant. Defaults to None. """
                }
            },
            'required': [
                'subscription',
                'account_name',
                'container_name'
            ]
        }
    }
)
def azmcp_storage_blob_list(
        subscription: str,
        account_name: str,
        container_name: str,
        auth_method: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None,
        tenant: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all blobs in a Storage container.

    This command retrieves and displays all blobs available in the specified
    container and Storage account. Results include blob names, sizes, and
    content types, returned as a JSON array. Requires account-name and
    container-name.

    Args:
        subscription (str): The Azure subscription ID or name. This can be
            either the GUID identifier or the display name of the Azure
            subscription to use.
        account_name (str): The name of the Azure Storage account. This is the
            unique name you chose for your storage account (e.g.,
            'mystorageaccount').
        container_name (str): The name of the container to access within the
            storage account.
        auth_method (Optional[str]): Authentication method to use. Options:
            'credential' (Azure CLI/managed identity), 'key' (access key),
            or 'connectionString'. Defaults to None.
        retry_delay (Optional[str]): Initial delay in seconds between retry
            attempts. For exponential backoff, this value is used as the base.
            Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between
            retries, regardless of the retry strategy. Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts
            for failed operations before giving up. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses
            consistent delays, 'exponential' increases delay between attempts.
            Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in
            seconds. Operations taking longer than this will be cancelled.
            Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name.
            This can be either the GUID identifier or the display name of your
            Azure AD tenant. Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary
        represents a blob in the container. Each blob dictionary contains the
        following keys:
            name (str): The name of the blob.
            properties (Dict[str, Any]): A dictionary containing blob properties.
                This dictionary includes:
                lastModified (str): Timestamp of the last modification, in
                    ISO 8601 format.
                etag (str): The ETag of the blob, representing its version.
                contentLength (int): The size of the blob in bytes.
                contentType (str): The content type of the blob (e.g.,
                    'application/octet-stream').
                blobType (str): The type of blob (e.g., 'BlockBlob',
                    'PageBlob', 'AppendBlob').
                leaseStatus (str): The lease status of the blob (e.g.,
                    'locked', 'unlocked').
                accessTier (Optional[str]): The access tier of the blob (e.g.,
                    'Hot', 'Cool', 'Archive'), if applicable.
                metadata (Optional[Dict[str, str]]): A dictionary of
                    user-defined metadata for the blob, where keys are
                    metadata names (str) and values are metadata values (str).

    Raises:
        ResourceNotFoundError: If the specified storage account or container
            does not exist.
        InvalidInputError: If required parameters like `account_name` or
            `container_name` are missing or invalid.
        SubscriptionNotFoundError: If the specified subscription does not exist.
    """
    # Validate required input parameters
    if not subscription or not isinstance(subscription, str):
        raise custom_errors.InvalidInputError("The 'subscription' argument is required and must be a string.")

    if not account_name or not isinstance(account_name, str):
        raise custom_errors.InvalidInputError("The 'account_name' argument is required and must be a string.")

    if not container_name or not isinstance(container_name, str):
        raise custom_errors.InvalidInputError("The 'container_name' argument is required and must be a string.")

    # Validate auth_method if provided
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

    # Validate retry parameters if provided
    if retry_delay is not None:
        try:
            delay = float(retry_delay)
            if delay < 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_delay must be a non-negative number.")

    if retry_max_delay is not None:
        try:
            max_delay = float(retry_max_delay)
            if max_delay < 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_delay must be a non-negative number.")

    if retry_max_retries is not None:
        try:
            max_retries = int(retry_max_retries)
            if max_retries < 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_retries must be a non-negative integer.")

    if retry_mode is not None:
        if not isinstance(retry_mode, str):
            raise custom_errors.InvalidInputError("retry_mode must be a string.")
        try:
            retry_mode = RetryMode(retry_mode)
        except ValueError:
            valid_modes = [mode.value for mode in RetryMode]
            raise custom_errors.InvalidInputError(
                f"Invalid retry_mode. Must be one of: {', '.join(valid_modes)}"
            )

    if retry_network_timeout is not None:
        try:
            timeout = float(retry_network_timeout)
            if timeout <= 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_network_timeout must be a positive number.")

    # Validate tenant if provided
    if tenant is not None:
        if not (isinstance(tenant, str) and tenant.strip()):
            raise custom_errors.InvalidInputError("The 'tenant' argument must be a non empty string.")

    sub_data = utils.find_subscription(subscription_id=subscription)
    if not sub_data:
        raise custom_errors.SubscriptionNotFoundError(f"Subscription '{subscription}' not found.")

    found_storage_account_dict = None
    resource_group_of_account = None

    for rg_item in sub_data.get("resource_groups", []):
        rg_name = rg_item.get("name")
        if not rg_name:
            continue

        storage_account_candidate = utils.find_storage_account(
            subscription_id=subscription,
            resource_group_name=rg_name,
            account_name=account_name
        )
        if storage_account_candidate:
            found_storage_account_dict = storage_account_candidate
            resource_group_of_account = rg_name
            break  # Storage account found

    if not found_storage_account_dict:
        raise custom_errors.ResourceNotFoundError(
            f"Storage account '{account_name}' not found in subscription '{subscription}'."
        )

    found_container_dict = utils.find_blob_container(
        subscription_id=subscription,
        resource_group_name=resource_group_of_account,
        account_name=account_name,
        container_name=container_name
    )

    if not found_container_dict:
        raise custom_errors.ResourceNotFoundError(
            f"Container '{container_name}' not found in storage account '{account_name}' "
            f"(Resource Group: '{resource_group_of_account}')."
        )

    # Extract and format blobs from the container
    result_list: List[Dict[str, Any]] = []
    blobs_list_from_db = found_container_dict.get("blobs", [])

    for blob_data_from_db in blobs_list_from_db:
        db_properties = blob_data_from_db.get("properties")
        # Ensure db_properties is a dictionary for safe access, default to empty if not
        if not isinstance(db_properties, dict):
            db_properties = {}

        db_metadata = blob_data_from_db.get("metadata")
        if db_metadata is not None and not isinstance(db_metadata, dict):
            db_metadata = None

        output_blob_item = OutputBlobItem(
            name=blob_data_from_db.get("name"),
            properties=StorageBlobProperties(
                lastModified=db_properties.get("lastModified"),
                etag=db_properties.get("etag"),
                contentLength=db_properties.get("contentLength"),
                contentType=db_properties.get("contentType"),
                blobType=db_properties.get("blobType"),
                leaseStatus=db_properties.get("leaseStatus"),
                accessTier=db_properties.get("accessTier")
            ),
            metadata=db_metadata
        )
        result_list.append(output_blob_item.model_dump())

    return result_list

@tool_spec(
    spec={
        'name': 'azmcp_storage_table_list',
        'description': """ List all tables in a Storage account.
        
        This function retrieves and displays all tables available in the specified Storage
        account. Results include table names and are returned as a list of dictionaries.
        It requires an account name and subscription ID. This function is used to explore
        Storage resources or to verify table existence before performing operations on
        specific tables. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either
                    the GUID identifier or the display name of the Azure subscription to use. """
                },
                'account_name': {
                    'type': 'string',
                    'description': """ The name of the Azure Storage account. This is the unique
                    name you chose for your storage account (e.g., 'mystorageaccount'). """
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options:
                    'credential' (Azure CLI/managed identity), 'key' (access key),
                    or 'connectionString'. Defaults to None. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This
                    can be either the GUID identifier or the display name of your Azure AD
                    tenant. Defaults to None. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for
                    failed operations before giving up. Defaults to None. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts.
                    For exponential backoff, this value is used as the base. Defaults to None. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. Defaults to None. """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent
                    delays, 'exponential' increases delay between attempts. Defaults to None. """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds.
                    Operations taking longer than this will be cancelled. Defaults to None. """
                }
            },
            'required': [
                'subscription',
                'account_name'
            ]
        }
    }
)
def azmcp_storage_table_list(
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
    """List all tables in a Storage account.

    This function retrieves and displays all tables available in the specified Storage
    account. Results include table names and are returned as a list of dictionaries.
    It requires an account name and subscription ID. This function is used to explore
    Storage resources or to verify table existence before performing operations on
    specific tables.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either
            the GUID identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the Azure Storage account. This is the unique
            name you chose for your storage account (e.g., 'mystorageaccount').
        auth_method (Optional[str]): Authentication method to use. Options:
            'credential' (Azure CLI/managed identity), 'key' (access key),
            or 'connectionString'. Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This
            can be either the GUID identifier or the display name of your Azure AD
            tenant. Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for
            failed operations before giving up. Defaults to None.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts.
            For exponential backoff, this value is used as the base. Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent
            delays, 'exponential' increases delay between attempts. Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled. Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a
            table in the storage account. Each dictionary contains the following
            key:
            TableName (str): The name of the table.

    Raises:
        ResourceNotFoundError: Raised if the specified storage account does not exist,
            or if the Table service is not supported or enabled for the account.
        ServiceError: Raised if an unexpected error occurs within the Azure Table
            Storage service during the operation.
        ValidationError: If input arguments fail validation.
        SubscriptionNotFoundError: Raised if the specified subscription does not exist.
    """
    # Validate required inputs
    if not subscription or not isinstance(subscription, str):
        raise custom_errors.ValidationError("Subscription ID or name must be provided as a non-empty string.")
    if not account_name or not isinstance(account_name, str):
        raise custom_errors.ValidationError("Storage account name must be provided as a non-empty string.")

    # Validate optional parameters
    if auth_method is not None:
        if not isinstance(auth_method, str):
            raise custom_errors.ValidationError("auth_method must be a string.")
        try:
            auth_method = AuthMethod(auth_method)
        except ValueError:
            valid_methods = [method.value for method in AuthMethod]
            raise custom_errors.ValidationError(
                f"Invalid auth_method. Must be one of: {', '.join(valid_methods)}"
            )

    if tenant is not None and not isinstance(tenant, str):
        raise custom_errors.ValidationError("tenant must be a string.")

    # Validate retry parameters
    if retry_max_retries is not None:
        try:
            max_retries = int(retry_max_retries)
            if max_retries < 0:
                raise ValueError
        except ValueError:
            raise custom_errors.ValidationError("retry_max_retries must be a non-negative integer.")

    if retry_delay is not None:
        try:
            delay = float(retry_delay)
            if delay < 0:
                raise ValueError
        except ValueError:
            raise custom_errors.ValidationError("retry_delay must be a non-negative number.")

    if retry_max_delay is not None:
        try:
            max_delay = float(retry_max_delay)
            if max_delay < 0:
                raise ValueError
        except ValueError:
            raise custom_errors.ValidationError("retry_max_delay must be a non-negative number.")

    if retry_mode is not None:
        if not isinstance(retry_mode, str):
            raise custom_errors.ValidationError("retry_mode must be a string.")
        valid_retry_modes = ['fixed', 'exponential']
        if retry_mode not in valid_retry_modes:
            raise custom_errors.ValidationError(
                f"Invalid retry_mode. Must be one of: {', '.join(valid_retry_modes)}"
            )

    if retry_network_timeout is not None:
        try:
            timeout = float(retry_network_timeout)
            if timeout <= 0:
                raise ValueError
        except ValueError:
            raise custom_errors.ValidationError("retry_network_timeout must be a positive number.")

    # Retrieve all subscriptions from the DB to allow lookup by ID or name
    all_subscriptions_data = DB.get("subscriptions", [])

    # Find the specified subscription by ID or name using the helper
    subscription_data = get_subscription_data_by_id_or_name(subscription, all_subscriptions_data)

    if not subscription_data:
        raise custom_errors.SubscriptionNotFoundError(f"Subscription '{subscription}' not found or is invalid.")

    actual_subscription_id = subscription_data.get("subscriptionId")
    # This check is for data integrity; subscriptionId is mandatory per schema.
    if not actual_subscription_id:
        raise custom_errors.ServiceError(
            f"Internal error: Subscription data for '{subscription}' is missing its 'subscriptionId'."
        )

    found_storage_account_data = None
    resource_groups_in_sub = subscription_data.get("resource_groups", [])
    for rg_data in resource_groups_in_sub:
        rg_name = rg_data.get("name")
        if rg_name:  # Ensure resource group has a name
            storage_account = utils.find_storage_account(
                subscription_id=actual_subscription_id,
                resource_group_name=rg_name,
                account_name=account_name
            )
            if storage_account:
                found_storage_account_data = storage_account
                break  # Stop searching once the account is found

    if not found_storage_account_data:
        raise custom_errors.ResourceNotFoundError(
            f"Storage account '{account_name}' not found in subscription '{subscription}' (resolved ID: '{actual_subscription_id}')."
        )

    account_kind = found_storage_account_data.get("kind")
    try:
        account_kind = StorageAccountKind(account_kind)
    except ValueError:
        raise custom_errors.ServiceError(
            f"Invalid storage account kind '{account_kind}' for account '{account_name}'."
        )

    tables_list_from_db = found_storage_account_data.get("tables", [])

    result_list: List[Dict[str, Any]] = []
    for table_db_item in tables_list_from_db:
        table_name = table_db_item.get("TableName")
        if table_name:
            result_list.append(StorageTableListItem(TableName=table_name).model_dump())

    return result_list


@tool_spec(
    spec={
        'name': 'azmcp_storage_account_list',
        'description': """ List all Storage accounts in a subscription.
        
        This command retrieves all Storage accounts available in the specified
        subscription. Results include account names and are returned as a JSON array. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be
                    either the GUID identifier or the display name of the Azure
                    subscription to use. """
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options:
                    'credential' (Azure CLI/managed identity), 'key' (access key),
                    or 'connectionString'. Defaults to None. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry
                    attempts. For exponential backoff, this value is used as the base.
                    Defaults to None. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between
                    retries, regardless of the retry strategy. Defaults to None. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts
                    for failed operations before giving up. Defaults to None. """
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
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name.
                    This can be either the GUID identifier or the display name of your
                    Azure AD tenant. Defaults to None. """
                }
            },
            'required': [
                'subscription'
            ]
        }
    }
)
def azmcp_storage_account_list(
    subscription: str,
    auth_method: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None,
    tenant: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """List all Storage accounts in a subscription.
    This command retrieves all Storage accounts available in the specified
    subscription. Results include account names and are returned as a JSON array.
    Args:
        subscription (str): The Azure subscription ID or name. This can be
            either the GUID identifier or the display name of the Azure
            subscription to use.
        auth_method (Optional[str]): Authentication method to use. Options:
            'credential' (Azure CLI/managed identity), 'key' (access key),
            or 'connectionString'. Defaults to None.
        retry_delay (Optional[str]): Initial delay in seconds between retry
            attempts. For exponential backoff, this value is used as the base.
            Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between
            retries, regardless of the retry strategy. Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts
            for failed operations before giving up. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses
            consistent delays, 'exponential' increases delay between attempts.
            Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in
            seconds. Operations taking longer than this will be cancelled.
            Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name.
            This can be either the GUID identifier or the display name of your
            Azure AD tenant. Defaults to None.
    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing the function's results.
            The key 'storage_accounts' holds the list of storage accounts.
            storage_accounts (List[Dict[str, Any]]): A list of Storage accounts.
                Each dictionary in the list represents a storage account and
                includes the following key-value pairs:
                name (str): The name of the storage account.
                id (str): The Azure Resource Manager ID of the storage account.
                location (str): The Azure region where the storage account is located.
                kind (str): The kind of storage account (e.g., 'StorageV2',
                    'BlobStorage', 'FileStorage').
                sku (Dict[str, str]): Stock Keeping Unit (SKU) details for the
                    storage account. This dictionary contains:
                    name (str): The name of the SKU (e.g., 'Standard_LRS',
                        'Premium_ZRS').
                    tier (str): The tier of the SKU (e.g., 'Standard', 'Premium').
                provisioningState (str): The provisioning state of the storage
                    account (e.g., 'Succeeded', 'Creating').
                primaryEndpoints (Dict[str, str]): A dictionary of primary service
                    endpoint URIs for the storage account. Keys are service types
                    (e.g., 'blob', 'queue', 'table', 'file'), and values are
                    their corresponding URIs.
    Raises:
        SubscriptionNotFoundError: If the specified subscription ID is not found.
        ValidationError: If input arguments fail validation.
    """
    # --- Input Validation ---
    if not subscription:
        # Updated message to match test expectation for empty subscription ID.
        raise custom_errors.ValidationError("Subscription ID cannot be empty.")

    # Validate retry_delay
    if retry_delay is not None:
        try:
            int(retry_delay)  # Check if it can be converted to an integer
        except ValueError:
            raise custom_errors.ValidationError(
                f"Invalid value for retry_delay: '{retry_delay}'. Must be an integer string."
            )

    # Validate retry_max_retries
    if retry_max_retries is not None:
        try:
            int(retry_max_retries)
        except ValueError:
            # Consistent error messaging style
            raise custom_errors.ValidationError(
                f"Invalid value for retry_max_retries: '{retry_max_retries}'. Must be an integer string."
            )

    # Validate retry_max_delay
    if retry_max_delay is not None:
        try:
            int(retry_max_delay)
        except ValueError:
            raise custom_errors.ValidationError(
                f"Invalid value for retry_max_delay: '{retry_max_delay}'. Must be an integer string."
            )

    # Validate retry_network_timeout
    if retry_network_timeout is not None:
        try:
            int(retry_network_timeout)
        except ValueError:
            raise custom_errors.ValidationError(
                f"Invalid value for retry_network_timeout: '{retry_network_timeout}'. Must be an integer string."
            )

    # Validate retry_mode
    if retry_mode is not None:
        allowed_retry_modes = [mode.value for mode in RetryModesOps]
        if retry_mode not in allowed_retry_modes:
            raise custom_errors.ValidationError(
                f"Invalid retry_mode: '{retry_mode}'. Allowed values are: {', '.join(allowed_retry_modes)}."
            )
    # --- End Input Validation ---

    # Retrieve all subscriptions from the DB
    subscriptions_in_db = DB.get("subscriptions", [])
    selected_subscription_data = None  # Will hold a copy of the found subscription data

    # Iterate through subscriptions to find a match for the provided identifier and tenant
    for sub_candidate_data_ref in subscriptions_in_db:
        # Check if the current candidate matches the provided subscription identifier (ID or name)
        matches_identifier = (sub_candidate_data_ref.get("subscriptionId") == subscription or
                              sub_candidate_data_ref.get("displayName") == subscription)

        if not matches_identifier:
            continue

        # If a tenant is specified, the subscription must also match this tenant
        if tenant:
            if sub_candidate_data_ref.get("tenantId") == tenant:
                selected_subscription_data = sub_candidate_data_ref.copy()  # Found, make a copy and break
                break
            # If tenant doesn't match, continue search; another subscription might match identifier and tenant
        else:  # Tenant not specified, so this subscription is a match
            selected_subscription_data = sub_candidate_data_ref.copy()  # Found, make a copy and break
            break

    if not selected_subscription_data:
        # If no subscription was selected, raise an error.
        # The error message format is aligned with the failing tests' expectations.
        expected_error_message = f"The specified Azure subscription '{subscription}' was not found or is not accessible."
        if tenant:
            subscription_exists_in_any_tenant = any(
                s.get("subscriptionId") == subscription or s.get("displayName") == subscription
                for s in subscriptions_in_db
            )
            if subscription_exists_in_any_tenant:
                 # This specific message for "found but wrong tenant" is kept from original logic.
                 # Current failing tests do not cover this exact scenario.
                 raise custom_errors.SubscriptionNotFoundError(
                    f"Subscription '{subscription}' was found, but it does not belong to the specified tenant '{tenant}'."
                )
            else: # Subscription not found in any tenant, and a tenant was specified.
                raise custom_errors.SubscriptionNotFoundError(expected_error_message)
        else: # Subscription not found, and no tenant was specified.
            raise custom_errors.SubscriptionNotFoundError(expected_error_message)

    subscription_data = selected_subscription_data
    all_storage_accounts: List[Dict[str, Any]] = []

    for rg_data in subscription_data.get("resource_groups", []):
        for sa_data in rg_data.get("storage_accounts", []):
            sa_name = sa_data['name']
            sa_id = sa_data['id']
            sa_location = sa_data['location']
            sa_kind = sa_data['kind']

            db_sku_data = sa_data['sku']
            sku_name = db_sku_data['name']
            sku_tier_from_db = db_sku_data.get('tier')
            output_sku_tier = sku_tier_from_db if sku_tier_from_db is not None else ""

            # Use the AzureSku model for validation and transformation
            sku_model = AzureSku(name=sku_name, tier=output_sku_tier)
            output_sku = sku_model.model_dump()

            prov_state_from_db = sa_data.get('provisioningState')
            output_prov_state = prov_state_from_db if prov_state_from_db is not None else ""

            endpoints_from_db = sa_data.get('primaryEndpoints')
            output_endpoints = endpoints_from_db if endpoints_from_db is not None else {}

            # Create a Pydantic model instance for validation
            storage_account_item = StorageAccountListItem(
                name=sa_name,
                id=sa_id,
                location=sa_location,
                kind=sa_kind,
                sku=AzureSku(**output_sku),
                provisioningState=output_prov_state,
                primaryEndpoints=output_endpoints,
            )
            # Convert the validated model to a dict and append to the list
            all_storage_accounts.append(storage_account_item.model_dump())

    return {"storage_accounts": all_storage_accounts}

@tool_spec(
    spec={
        'name': 'azmcp_storage_blob_container_list',
        'description': """ List all containers in a Storage account.
        
        This command retrieves and displays all containers available in the specified account.
        Results include container names and are returned as a JSON array. Requires account-name. """,
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
                    'description': """ The name of the Azure Storage account. This is the unique name
                    you chose for your storage account (e.g., 'mystorageaccount'). """
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can be
                    either the GUID identifier or the display name of your Azure AD tenant. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for failed
                    operations before giving up. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts. For
                    exponential backoff, this value is used as the base. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent delays,
                    'exponential' increases delay between attempts. """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds.
                    Operations taking longer than this will be cancelled. """
                }
            },
            'required': [
                'subscription',
                'account_name'
            ]
        }
    }
)
def azmcp_storage_blob_container_list(
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
    """List all containers in a Storage account.
    This command retrieves and displays all containers available in the specified account.
    Results include container names and are returned as a JSON array. Requires account-name.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID
            identifier or the display name of the Azure subscription to use.
        account_name (str): The name of the Azure Storage account. This is the unique name
            you chose for your storage account (e.g., 'mystorageaccount').
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be
            either the GUID identifier or the display name of your Azure AD tenant.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed
            operations before giving up.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For
            exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays,
            'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled.
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a blob
            container in the storage account and contains the following keys:
            name (str): The name of the container.
            lastModified (str): Timestamp of the last modification (ISO 8601 format).
            etag (str): The ETag of the container.
            leaseStatus (str): The lease status of the container.
            publicAccess (Optional[str]): The level of public access for the container.
    Raises:
        ResourceNotFoundError: If the specified storage account does not exist or if the subscription is not found.
        InvalidInputError: If the required parameter 'account-name' is missing or invalid.
    """
    # Validate required 'account_name'
    if not account_name:
        raise custom_errors.InvalidInputError("Required parameter 'account-name' is missing or invalid.")

    # The auth_method, tenant, and retry_* parameters are not used in this simulation context

    # Find the subscription by ID or name using the helper
    sub_data = utils.find_subscription_by_id_or_name(subscription)

    if not sub_data:
        # If subscription not found, raise ResourceNotFoundError.
        raise custom_errors.ResourceNotFoundError(
            f"Subscription '{subscription}' not found."
        )

    # Search for the storage account within the found subscription's resource groups
    storage_account_data = None
    resolved_subscription_id = sub_data.get("subscriptionId")

    resource_groups = sub_data.get("resource_groups") or []
    for rg in resource_groups:
        storage_accounts_in_rg = rg.get("storage_accounts") or []
        found_sa = utils._find_item_in_list(storage_accounts_in_rg, "name", account_name)
        if found_sa:
            if found_sa.get("subscription_id") == resolved_subscription_id:
                storage_account_data = found_sa
                break  # Storage account found

    if not storage_account_data:
        raise custom_errors.ResourceNotFoundError(
            f"Storage account '{account_name}' not found in subscription '{subscription}'."
        )

    # Retrieve blob containers from the storage account
    blob_containers_list_data = storage_account_data.get("blob_containers") or []

    result_list: List[Dict[str, Any]] = []
    for container_data in blob_containers_list_data:
        lease_status = container_data.get("leaseStatus")
        if lease_status is None:
            lease_status = "unlocked"

        try:
            # Use the Pydantic model to validate and structure the data
            container_item = StorageBlobContainerListItem(
                name=container_data.get("name"),
                lastModified=container_data.get("lastModified"),
                etag=container_data.get("etag"),
                leaseStatus=lease_status,
                publicAccess=container_data.get("publicAccess")
            )
            # Convert the validated model to a dictionary for the final output
            result_list.append(container_item.model_dump(exclude_none=True))

        except PydanticValidationError:
            # If the data from the DB is malformed, skip this entry,
            # preserving the original logic of skipping invalid items.
            continue

    return result_list