from common_utils.tool_spec_decorator import tool_spec
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from .SimulationEngine import custom_errors
from .SimulationEngine import models
from .SimulationEngine import utils
from .SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'azmcp_keyvault_key_create',
        'description': """ Create a new key in an Azure Key Vault.
        
        This function creates a key with the specified name and type in the given vault.
        Key types include RSA (RSA key pair), EC (Elliptic Curve key pair), and OCT (ES cryptographic pair). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either the
                    GUID identifier or the display name of the Azure subscription to use. """
                },
                'vault': {
                    'type': 'string',
                    'description': 'The name of the Key Vault.'
                },
                'key': {
                    'type': 'string',
                    'description': 'The name of the key to retrieve/modify from the Key Vault.'
                },
                'key_type': {
                    'type': 'string',
                    'description': 'The type of key to create (RSA, EC).'
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. """
                },
                'retry_delay': {
                    'type': 'string',
                    'description': """ Initial delay in seconds between retry attempts.
                    For exponential backoff, this value is used as the base.
                    Must be a string representing a non-negative integer. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy.
                    Must be a string representing a non-negative integer. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for
                    failed operations before giving up.
                    Must be a string representing a non-negative integer. """
                },
                'retry_mode': {
                    'type': 'string',
                    'description': """ Retry strategy to use. 'fixed' uses consistent
                    delays, 'exponential' increases delay between attempts. """
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': """ Network operation timeout in seconds.
                    Operations taking longer than this will be cancelled.
                    Must be a string representing a non-negative integer. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can
                    be either the GUID identifier or the display name of your Azure AD tenant. """
                }
            },
            'required': [
                'subscription',
                'vault',
                'key',
                'key_type'
            ]
        }
    }
)
def azmcp_keyvault_key_create(subscription: str, vault: str, key: str, key_type: str, auth_method: Optional[str] = None,
                              retry_delay: Optional[str] = None, retry_max_delay: Optional[str] = None,
                              retry_max_retries: Optional[str] = None, retry_mode: Optional[str] = None,
                              retry_network_timeout: Optional[str] = None, tenant: Optional[str] = None) -> Dict[
    str, Any]:
    """Create a new key in an Azure Key Vault.

    This function creates a key with the specified name and type in the given vault.
    Key types include RSA (RSA key pair), EC (Elliptic Curve key pair), and OCT (ES cryptographic pair).

    Args:
        subscription (str): The Azure subscription ID or name. This can be either the
            GUID identifier or the display name of the Azure subscription to use.
        vault (str): The name of the Key Vault.
        key (str): The name of the key to retrieve/modify from the Key Vault.
        key_type (str): The type of key to create (RSA, EC).
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts.
            For exponential backoff, this value is used as the base.
            Must be a string representing a non-negative integer.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy.
            Must be a string representing a non-negative integer.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for
            failed operations before giving up.
            Must be a string representing a non-negative integer.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent
            delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled.
            Must be a string representing a non-negative integer.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can
            be either the GUID identifier or the display name of your Azure AD tenant.

    Returns:
        Dict[str, Any]: Details of the created key. Contains the following keys:
            key_ops (List[str]): Supported key operations for the key.
            kty (str): The key type (e.g., 'RSA', 'EC', 'OCT').
            attributes (Dict[str, Any]): Attributes of the key, containing:
                enabled (bool): Indicates whether the key is enabled for use.
                exp (Optional[int]): Expiry date in UTC seconds (Unix timestamp).
                nbf (Optional[int]): Not before date in UTC seconds (Unix timestamp),
                    before which the key cannot be used.
                created (int): Creation date in UTC seconds (Unix timestamp).
                updated (int): Last updated date in UTC seconds (Unix timestamp).
                recoveryLevel (str): The recovery level for the key (e.g., 'Purgeable',
                    'Recoverable', 'Recoverable+ProtectedSubscription').

    Raises:
        ResourceNotFoundError: If the specified Azure Key Vault does not exist or
                               if the subscription is not found/accessible.
        ValidationError: If input arguments fail validation (e.g., empty strings for required params,
                         invalid key_type, invalid format for retry parameters).
        ConflictError: If a key with the same name already exists in the vault.
    """
    # --- Input Validation for required string parameters ---
    if not subscription:
        raise custom_errors.ValidationError("Parameter 'subscription' cannot be an empty string.")
    if not vault:
        raise custom_errors.ValidationError("Parameter 'vault' cannot be an empty string.")
    if not key:
        raise custom_errors.ValidationError("Parameter 'key' cannot be an empty string.")

    # --- Input Validation for retry parameters ---
    if retry_delay is not None:
        utils._validate_str_non_negative_int(retry_delay, "retry_delay")
    if retry_max_retries is not None:
        utils._validate_str_non_negative_int(retry_max_retries, "retry_max_retries")
    if retry_max_delay is not None:
        utils._validate_str_non_negative_int(retry_max_delay, "retry_max_delay")
    if retry_network_timeout is not None:
        utils._validate_str_non_negative_int(retry_network_timeout, "retry_network_timeout")

    # Validate key_type (aligns with inputSchema and test expectations for this function)
    allowed_key_types = [member.value for member in models.AllowedKeyTypes]
    kty_upper = key_type.upper()
    if kty_upper not in allowed_key_types:
        raise custom_errors.ValidationError(f"Invalid key_type '{key_type}'. Allowed values are 'RSA', 'EC'.")

    # Validate subscription
    sub_ref = utils.get_subscription_ref(subscription)
    if not sub_ref:
        raise custom_errors.ResourceNotFoundError(
            f"Subscription '{subscription}' not found or the vault is not accessible under it.")

    # Find the Key Vault and its resource group
    found_vault_ref = None
    vault_resource_group_name = None
    resource_groups_list = sub_ref.get("resource_groups", [])

    for rg_ref in resource_groups_list:
        rg_name = rg_ref.get("name")
        if not rg_name:
            continue

        vault_candidate_ref = utils.get_key_vault_ref(subscription, rg_name, vault)
        if vault_candidate_ref:
            found_vault_ref = vault_candidate_ref
            vault_resource_group_name = rg_name
            break

    if not found_vault_ref:
        raise custom_errors.ResourceNotFoundError(f"Key Vault '{vault}' not found in subscription '{subscription}'.")

    # This check is defensive; vault_resource_group_name should be set if found_vault_ref is not None.
    if vault_resource_group_name is None:
        # This situation implies an internal logic inconsistency if reached after a vault is found.
        raise custom_errors.ServiceError("Could not determine resource group for the vault.")

    existing_key_ref = utils.get_key_vault_key_ref(subscription, vault_resource_group_name, vault, key)
    if existing_key_ref:
        raise custom_errors.ConflictError(f"A key with name '{key}' already exists in vault '{vault}'.")

    # Create the new key
    current_timestamp_unix = int(datetime.now(timezone.utc).timestamp())
    key_version_id = utils.new_uuid_str()

    # Ensure vault name from the found reference is used for constructing URIs
    actual_vault_name = found_vault_ref['name']
    vault_uri = f"https://{actual_vault_name}.vault.azure.net"
    kid = f"{vault_uri}/keys/{key}/{key_version_id}"

    key_ops_map = {
        "RSA": [member.value for member in models.KeyOpsRSA],
        "EC": [member.value for member in models.KeyOpsEC]
    }

    new_key_attributes = models.KeyCreateResponseAttributes(
        enabled=True,
        exp=None,
        nbf=None,
        created=current_timestamp_unix,
        updated=current_timestamp_unix,
        recoveryLevel="Recoverable",
    ).model_dump()

    new_key_data = models.KeyVaultKey(
        name=key,
        kid=kid,
        kty=kty_upper,
        key_ops=key_ops_map[kty_upper],
        attributes=new_key_attributes,
        tags=None,
        vault_name=actual_vault_name,
    ).model_dump()

    keys_list_ref = found_vault_ref.setdefault("keys", [])
    added_key_ref = utils.add_item_to_db_list(keys_list_ref, new_key_data, "name")

    if not added_key_ref:
        # This path should ideally not be hit if the preceding conflict check is effective
        # and DB operations are consistent.
        raise custom_errors.ServiceError(
            f"Failed to add key '{key}' to vault '{actual_vault_name}' due to an internal error after conflict check.")

    # Prepare response attributes based on the created key's attributes
    response_attributes = models.KeyCreateResponseAttributes(
        enabled=new_key_attributes["enabled"],
        exp=new_key_attributes["exp"],
        nbf=new_key_attributes["nbf"],
        created=new_key_attributes["created"],
        updated=new_key_attributes["updated"],
        recoveryLevel=new_key_attributes["recoveryLevel"],
    ).model_dump()

    return models.KeyVaultKeyCreateResponse(
        key_ops=new_key_data["key_ops"],
        kty=new_key_data["kty"],
        attributes=response_attributes,
    ).model_dump()


@tool_spec(
    spec={
        'name': 'azmcp_keyvault_key_get',
        'description': """ Get a key from an Azure Key Vault.
        
        This function retrieves and displays details about a specific key in the specified vault. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
                },
                'vault': {
                    'type': 'string',
                    'description': 'The name of the Key Vault.'
                },
                'key': {
                    'type': 'string',
                    'description': 'The name of the key to retrieve/modify from the Key Vault.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': "Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'."
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
                'vault',
                'key'
            ]
        }
    }
)
def azmcp_keyvault_key_get(
        subscription: str,
        vault: str,
        key: str,
        auth_method: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None,
        tenant: Optional[str] = None
) -> Dict[str, Any]:
    """Get a key from an Azure Key Vault.

    This function retrieves and displays details about a specific key in the specified vault.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        vault (str): The name of the Key Vault.
        key (str): The name of the key to retrieve/modify from the Key Vault.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.

    Returns:
        Dict[str, Any]: Details of the retrieved key. This dictionary includes the following fields:
            kid (str): The key identifier (a URI identifying the key).
            key_ops (List[str]): A list of supported cryptographic operations for the key (e.g., 'encrypt', 'decrypt', 'sign', 'verify', 'wrapKey', 'unwrapKey').
            kty (str): The key type (e.g., 'RSA' for RSA, 'EC' for Elliptic Curve).
            attributes (Dict[str, Any]): A dictionary of key attributes, containing:
                enabled (bool): Indicates if the key is enabled and can be used for cryptographic operations.
                exp (Optional[int]): Expiry date as a Unix timestamp (seconds since Epoch UTC). The key cannot be used after this time.
                nbf (Optional[int]): Not-before date as a Unix timestamp (seconds since Epoch UTC). The key cannot be used before this time.
                created (int): Creation date as a Unix timestamp (seconds since Epoch UTC).
                updated (int): Last updated date as a Unix timestamp (seconds since Epoch UTC).
                recoveryLevel (str): Reflects the recovery level configured for the Key Vault (e.g., 'Purgeable', 'Recoverable+Purgeable', 'Recoverable', 'Recoverable+ProtectedSubscription').

    Raises:
        ResourceNotFoundError: If the specified Key Vault or key does not exist, or if the subscription does not exist.
        InvalidInputError: If required parameters (subscription, vault, key) are missing or empty.
    """
    # Validate required inputs
    if not subscription:
        raise custom_errors.InvalidInputError("Subscription ID/name cannot be empty.")
    if not vault:
        raise custom_errors.InvalidInputError("Vault name cannot be empty.")
    if not key:
        raise custom_errors.InvalidInputError("Key name cannot be empty.")

    # Find the subscription by ID or name
    subscriptions_list = DB.get("subscriptions", [])
    sub_data = None
    for sub_data_in_list in subscriptions_list:
        if sub_data_in_list.get("subscriptionId") == subscription or sub_data_in_list.get(
                "displayName") == subscription:
            sub_data = sub_data_in_list.copy()
    if not sub_data:
        raise custom_errors.ResourceNotFoundError(f"Subscription '{subscription}' not found.")

    # Iterate through resource groups in the subscription to find the vault
    found_vault_data = None
    resource_groups = sub_data.get("resource_groups", [])
    for rg_data in resource_groups:
        key_vaults_in_rg = rg_data.get("key_vaults", [])
        vault_data_candidate = utils._find_item_in_list(key_vaults_in_rg, "name", vault)
        if vault_data_candidate:
            found_vault_data = vault_data_candidate
            break  # Vault found, no need to check other RGs

    if not found_vault_data:
        raise custom_errors.ResourceNotFoundError(
            f"Key Vault '{vault}' not found in subscription '{subscription}'."
        )

    # Vault found, now search for the key within this vault
    keys_in_vault = found_vault_data.get("keys", [])
    key_data = utils._find_item_in_list(keys_in_vault, "name", key)

    if not key_data:
        raise custom_errors.ResourceNotFoundError(
            f"Key '{key}' not found in vault '{vault}'."
        )

    # Key found, construct and return its details
    key_attributes_data = key_data.get("attributes")
    key_ops_list = key_data.get("key_ops", [])

    attributes_dict = models.KeyOperationAttributes(
        enabled=key_attributes_data["enabled"],
        exp=key_attributes_data.get("exp"),
        nbf=key_attributes_data.get("nbf"),
        created=key_attributes_data["created"],
        updated=key_attributes_data["updated"],
        recoveryLevel=key_attributes_data.get("recoveryLevel"),
    ).model_dump()

    result = models.KeyDetails(
        kid=key_data["kid"],
        key_ops=key_ops_list,
        kty=key_data["kty"],
        attributes=attributes_dict,
    ).model_dump()

    return result


@tool_spec(
    spec={
        'name': 'azmcp_keyvault_key_list',
        'description': """ List all keys in an Azure Key Vault.
        
        This command retrieves and displays the names of all keys stored in the specified vault. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
                },
                'vault': {
                    'type': 'string',
                    'description': 'The name of the Key Vault.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': "Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'."
                },
                'include_managed': {
                    'type': 'string',
                    'description': 'Whether or not to include managed keys in results.'
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
                'vault'
            ]
        }
    }
)
def azmcp_keyvault_key_list(
        subscription: str,
        vault: str,
        auth_method: Optional[str] = None,
        include_managed: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None,
        tenant: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List all keys in an Azure Key Vault.
    This command retrieves and displays the names of all keys stored in the specified vault.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        vault (str): The name of the Key Vault.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        include_managed (Optional[str]): Whether or not to include managed keys in results.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant.
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a key in the Azure Key Vault. Each dictionary in the list contains the following keys:
            attributes (Dict[str, Any]): The attributes of the key. This dictionary includes fields such as:
                enabled (bool): Specifies whether the key is enabled and can be used for cryptographic operations.
                exp (Optional[int]): Expiry date of the key, as a Unix timestamp (seconds since UTC epoch).
                nbf (Optional[int]): Not-before date of the key, as a Unix timestamp (seconds since UTC epoch). The key cannot be used before this date.
                created (int): Creation date of the key, as a Unix timestamp (seconds since UTC epoch).
                updated (int): Last updated date of the key, as a Unix timestamp (seconds since UTC epoch).
            tags (Optional[Dict[str, str]]): Application-specific metadata as key-value pairs. These are user-defined tags associated with the key.
    Raises:
        ResourceNotFoundError: If the specified Azure Key Vault does not exist under the given subscription, or if the subscription itself is not found.
        InvalidInputError: If any required input parameters (e.g., 'vault', 'subscription') are missing, or if any parameter is provided with an invalid value or format.
    """

    # Validate required parameters
    params_to_validate_required_string = {"subscription": subscription, "vault": vault}
    for param_name, param_value in params_to_validate_required_string.items():
        if param_value is None:
            raise custom_errors.InvalidInputError(f"Parameter '{param_name}' is required.")
        if not param_value:  # Handles empty string
            raise custom_errors.InvalidInputError(f"Parameter '{param_name}' cannot be an empty string.")

    # Validate optional parameters
    _parsed_include_managed = False  # Default behavior: effectively same as include_managed='false'
    if include_managed is not None:
        if not isinstance(include_managed, str) or include_managed.lower() not in ['true', 'false']:
            raise custom_errors.InvalidInputError(
                "Parameter 'include_managed' must be 'true' or 'false' if provided."
            )
        if include_managed.lower() == 'true':
            _parsed_include_managed = True

    # Validate auth_method if provided
    if auth_method is not None:
        allowed_auth_methods = [auth_method.value for auth_method in models.AuthMethod]
        if auth_method not in allowed_auth_methods:
            allowed_str = ", ".join([f"'{v}'" for v in allowed_auth_methods])
            raise custom_errors.InvalidInputError(
                f"Parameter 'auth-method' has an invalid value '{auth_method}'. Allowed values are {allowed_str}."
            )

    # Validate retry-mode if provided
    if retry_mode is not None:
        allowed_retry_modes = [retry_mode.value for retry_mode in models.RetryMode]
        if retry_mode not in allowed_retry_modes:
            allowed_str = ", ".join([f"'{v}'" for v in allowed_retry_modes])
            raise custom_errors.InvalidInputError(
                f"Parameter 'retry-mode' has an invalid value '{retry_mode}'. Allowed values are {allowed_str}."
            )

    # Validate retry numeric string parameters
    if retry_max_retries is not None:
        if not isinstance(retry_max_retries, str):
            raise custom_errors.InvalidInputError(f"Parameter 'retry_max_retries' must be a string.")
        try:
            int(retry_max_retries)
        except ValueError:
            raise custom_errors.InvalidInputError(
                f"Parameter 'retry_max_retries' must be a string representing a valid integer."
            )

    params_to_validate_is_number = {"retry_delay": retry_delay, "retry_max_delay": retry_max_delay,
                                    "retry_network_timeout": retry_network_timeout}
    for param_name, param_value in params_to_validate_is_number.items():
        if param_value is not None:
            if not isinstance(param_value, str):
                raise custom_errors.InvalidInputError(f"Parameter '{param_name}' must be a string.")
            try:
                float(param_value)  # Allows integers and floats
            except ValueError:
                raise custom_errors.InvalidInputError(
                    f"Parameter '{param_name}' must be a string representing a valid number."
                )

    # Validate tenant if provided (ensure it's a string, no other specific format checks from schema)
    if tenant is not None and not isinstance(tenant, str):
        raise custom_errors.InvalidInputError("Parameter 'tenant' must be a string.")

    # Find the subscription
    subscription_data = utils.find_subscription(subscription_id=subscription)
    if not subscription_data:
        raise custom_errors.ResourceNotFoundError(f"Subscription with ID '{subscription}' not found.")

    # Find the Key Vault within the subscription
    key_vault_data = None
    for rg_data in subscription_data.get("resource_groups", []):
        for kv_from_rg in rg_data.get("key_vaults", []):
            if kv_from_rg.get("name") == vault:
                key_vault_data = kv_from_rg
                break
        if key_vault_data:
            break

    if not key_vault_data:
        raise custom_errors.ResourceNotFoundError(
            f"Key Vault '{vault}' not found in subscription '{subscription_data.get('subscriptionId', subscription)}'."
        )

    keys_in_vault_data = key_vault_data.get("keys", [])

    result_list: List[Dict[str, Any]] = []
    for key_entry_data in keys_in_vault_data:
        # Current schema/logic does not differentiate managed keys, so _parsed_include_managed has no filtering effect.
        # If a field like "managed_hsm_key" or similar existed on key_entry_data.attributes,
        # filtering would be:
        # if not _parsed_include_managed and key_entry_data.get("attributes", {}).get("is_managed_key_field", False):
        #     continue

        db_key_attributes = key_entry_data.get("attributes")

        if not isinstance(db_key_attributes, dict):
            continue  # Skip malformed key entry

        output_attributes_dict = models.KeyListItemAttributes(
            enabled=db_key_attributes.get("enabled"),
            exp=db_key_attributes.get("exp"),
            nbf=db_key_attributes.get("nbf"),
            created=db_key_attributes.get("created"),
            updated=db_key_attributes.get("updated"),
        ).model_dump()

        key_list_item = models.KeyListItem(
            attributes=output_attributes_dict,
            tags=key_entry_data.get("tags")
        ).model_dump()
        result_list.append(key_list_item)

    return result_list
