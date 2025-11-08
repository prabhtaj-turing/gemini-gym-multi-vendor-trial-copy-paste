# File: APIs/azure/SimulationEngine/utils.py

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Union
from . import custom_errors

# --- Global DB Access --- 
from .db import DB # This will be the global dictionary (loaded from JSON)

# Pydantic model imports removed as they are not directly used in util logic for DB dict interaction

# --- Consistency Maintenance Functions ---

def new_uuid_str() -> str:
    """Generates a new universally unique identifier (UUID) as a string.

    Returns:
        str: A new UUID formatted as a string.
    """
    return str(uuid.uuid4())

def get_current_utc_timestamp_iso() -> str:
    """Returns the current Coordinated Universal Time (UTC) timestamp in ISO 8601 format.

    The timestamp is formatted as YYYY-MM-DDTHH:MM:SS.ffffffZ (e.g., 2023-10-27T10:30:00.123456Z).

    Returns:
        str: The current UTC timestamp as an ISO 8601 formatted string with 'Z' suffix.
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def generate_arm_id(
    subscription_id: str,
    resource_group_name: Optional[str] = None,
    provider: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_name: Optional[str] = None,
    *sub_resources: Union[str, Tuple[str, str]] # Accepts ("type", "name") or "type", "name"
) -> str:
    """
    Generates a standard Azure Resource Manager (ARM) ID.

    Args:
        subscription_id: The GUID of the subscription.
        resource_group_name: The name of the resource group. If None, ID is at subscription level.
        provider: The Azure resource provider (e.g., "Storage", "KeyVault"). Do not include "Microsoft." prefix.
        resource_type: The plural type of the resource (e.g., "storageAccounts", "vaults").
        resource_name: The name of the resource.
        *sub_resources: A sequence of sub-resource type/name pairs.
                        Can be passed as individual strings ("type1", "name1", "type2", "name2")
                        or as tuples (("type1", "name1"), ("type2", "name2")).

    Returns:
        str: A string representing the ARM ID.

    Raises:
        ValueError: If `subscription_id` is not provided.
        ValueError: If `sub_resources` are provided with an odd number of elements (not in pairs).
        ValueError: If elements within `sub_resources` tuples are not strings.
        ValueError: If `sub_resources` contains items that are not strings or (type, name) tuples.
    """
    if not subscription_id:
        raise ValueError("Subscription ID is required to generate an ARM ID.")

    base_id = f"/subscriptions/{subscription_id}"
    if resource_group_name:
        base_id += f"/resourceGroups/{resource_group_name}"
        if provider and resource_type and resource_name:
            base_id += f"/providers/Microsoft.{provider}/{resource_type}/{resource_name}"
    elif provider and resource_type and resource_name: # Subscription-level resource
        base_id += f"/providers/Microsoft.{provider}/{resource_type}/{resource_name}"

    # Normalize sub_resources if passed as tuples
    processed_sub_resources = []
    for item in sub_resources:
        if isinstance(item, tuple) and len(item) == 2:
            if not (isinstance(item[0], str) and isinstance(item[1], str)):
                raise ValueError("Elements of sub-resource tuples must both be strings.")
            processed_sub_resources.extend(item)
        elif isinstance(item, str):
            processed_sub_resources.append(item)
        else:
            raise ValueError("Sub-resources must be strings or (type, name) tuples.")

    if len(processed_sub_resources) % 2 != 0:
        raise ValueError("Sub-resources must be provided in type/name pairs.")

    for i in range(0, len(processed_sub_resources), 2):
        res_type, res_name = processed_sub_resources[i], processed_sub_resources[i+1]
        base_id += f"/{res_type}/{res_name}"
    return base_id

# --- Utility/Interaction Functions (Finders) ---
# These operate on the global `DB` dictionary and return copies of found items (as dicts).

def _find_item_in_list(
    item_list_data: List[Dict[str, Any]],
    key_name: str,
    key_value: str
) -> Optional[Dict[str, Any]]:
    """Finds a dictionary (as a copy) within a list of dictionaries by a key-value pair.

    This is a generic helper for read-only operations as it returns a copy of the found item.

    Args:
        item_list_data: The list of dictionaries to search within.
        key_name: The key (field name) in each dictionary to check against `key_value`.
        key_value: The value to match for the given `key_name`.

    Returns:
        Optional[Dict[str, Any]]: A copy of the first dictionary found that matches the criteria, 
                                   or None if no match is found.
    """
    for item_data in item_list_data:
        if item_data.get(key_name) == key_value:
            return item_data.copy()
    return None

def _get_item_ref_in_list(
    item_list_ref: List[Dict[str, Any]],
    key_name: str,
    key_value: str
) -> Optional[Dict[str, Any]]:
    """Finds a direct reference to a dictionary within a list of dictionaries by a key-value pair.

    USE WITH CAUTION: This function returns a direct reference to an item in the list. 
    Modifying the returned dictionary will directly modify the item within the global DB.

    Args:
        item_list_ref: The list of dictionaries (direct reference) to search within.
        key_name: The key (field name) in each dictionary to check against `key_value`.
        key_value: The value to match for the given `key_name`.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the first dictionary found that matches 
                                   the criteria, or None if no match is found.
    """
    for item_ref in item_list_ref:
        if item_ref.get(key_name) == key_value:
            return item_ref
    return None

# --- Top-Level Finders ---
def find_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
    """Finds an Azure subscription by its ID from the global DB.

    This function searches the top-level 'subscriptions' list in the DB.
    It returns a copy of the subscription data if found.

    Args:
        subscription_id: The unique identifier (GUID) of the Azure subscription.

    Returns:
        Optional[Dict[str, Any]]: A copy of the subscription dictionary if found, otherwise None.
    """
    subscriptions = DB.get("subscriptions", [])
    return _find_item_in_list(subscriptions, "subscriptionId", subscription_id)

def get_subscription_ref(subscription_id: str) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to an Azure subscription dictionary in the global DB.

    USE WITH CAUTION: Modifying the returned dictionary directly modifies the global DB state.
    If the 'subscriptions' list does not exist in the DB, it will be initialized as an empty list.

    Args:
        subscription_id: The unique identifier (GUID) of the Azure subscription.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the subscription dictionary if found, 
                                   otherwise None.
    """
    if "subscriptions" not in DB or DB["subscriptions"] is None: 
        DB["subscriptions"] = []
    subscriptions_ref = DB["subscriptions"] 
    return _get_item_ref_in_list(subscriptions_ref, "subscriptionId", subscription_id)

def find_subscription_by_id_or_name(subscription_identifier: str) -> Optional[Dict[str, Any]]:
    """
    Finds a subscription by its ID or display name.
    Tries to find by ID first using utils.find_subscription.
    If not found, iterates through all subscriptions to find by display name.
    Returns a copy of the subscription dictionary if found, otherwise None.
    """
    # Try finding by ID first (utils.find_subscription returns a copy)
    sub_data = find_subscription(subscription_identifier)
    if sub_data:
        return sub_data

    # If not found by ID, try finding by display name
    # Ensures all_subs is a list, even if 'subscriptions' key is missing or DB["subscriptions"] is None.
    all_subs = DB.get("subscriptions", []) 
        
    for s_dict in all_subs: # s_dict is a reference to an item in DB["subscriptions"]
        if s_dict.get("displayName") == subscription_identifier:
            return s_dict.copy() # Return a copy to match behavior of utils.find_subscription
    return None

def find_resource_group(
    subscription_id: str,
    resource_group_name: str
) -> Optional[Dict[str, Any]]:
    """Finds an Azure resource group by name within a specific subscription.

    This function first finds the subscription and then searches its 'resource_groups' list.
    It returns a copy of the resource group data if found.

    Args:
        subscription_id: The ID of the subscription containing the resource group.
        resource_group_name: The name of the resource group to find.

    Returns:
        Optional[Dict[str, Any]]: A copy of the resource group dictionary if found, otherwise None.
    """
    sub_data = find_subscription(subscription_id)
    if not sub_data:
        return None
    resource_groups = sub_data.get("resource_groups", [])
    return _find_item_in_list(resource_groups, "name", resource_group_name)

def get_resource_group_ref(
    subscription_id: str,
    resource_group_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a resource group dictionary within its subscription.

    USE WITH CAUTION: Modifying the returned dictionary directly modifies the global DB state.
    If the 'resource_groups' list does not exist in the parent subscription, it will be initialized.

    Args:
        subscription_id: The ID of the subscription containing the resource group.
        resource_group_name: The name of the resource group.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the resource group dictionary if found, 
                                   otherwise None.
    """
    sub_ref = get_subscription_ref(subscription_id)
    if not sub_ref:
        return None
    # Ensure 'resource_groups' list exists in the subscription_ref and get a direct reference
    rgs_ref = sub_ref.setdefault("resource_groups", [])
    return _get_item_ref_in_list(rgs_ref, "name", resource_group_name)

# --- Resource Finders (using the reference getters for modification paths) ---

# Example: App Configuration
def find_app_config_store(
    subscription_id: str, resource_group_name: str, store_name: str
) -> Optional[Dict[str, Any]]:
    """Finds an App Configuration store by name within a specific resource group and subscription.

    Returns a copy of the App Configuration store data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        store_name: The name of the App Configuration store.

    Returns:
        Optional[Dict[str, Any]]: A copy of the store dictionary if found, otherwise None.
    """
    rg_data = find_resource_group(subscription_id, resource_group_name)
    if not rg_data: return None
    return _find_item_in_list(rg_data.get("app_config_stores", []), "name", store_name)

def get_app_config_store_ref(
    subscription_id: str, resource_group_name: str, store_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to an App Configuration store dictionary.
    
    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'app_config_stores' list in the parent resource group if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        store_name: The name of the App Configuration store.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the store dictionary if found, otherwise None.
    """
    rg_ref = get_resource_group_ref(subscription_id, resource_group_name)
    if not rg_ref: return None
    # Ensure list exists in rg_ref and get a direct reference
    stores_ref = rg_ref.setdefault("app_config_stores", [])
    return _get_item_ref_in_list(stores_ref, "name", store_name)

def find_app_config_key_value(
    subscription_id: str, resource_group_name: str, store_name: str,
    key: str, label: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Finds an App Configuration key-value item by key and label within a store.
    
    Returns a copy of the key-value item data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        store_name: The name of the App Configuration store.
        key: The key of the key-value item.
        label: Optional. The label of the key-value item. Defaults to None (null label).

    Returns:
        Optional[Dict[str, Any]]: A copy of the key-value dictionary if found, otherwise None.
    """
    store_data = find_app_config_store(subscription_id, resource_group_name, store_name)
    if not store_data: return None
    for kv_data in store_data.get("key_values", []):
        if kv_data.get("key") == key and kv_data.get("label") == label:
            return kv_data.copy()
    return None

def get_app_config_key_value_ref(
    subscription_id: str, resource_group_name: str, store_name: str,
    key: str, label: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to an App Configuration key-value item dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'key_values' list in the parent store if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        store_name: The name of the App Configuration store.
        key: The key of the key-value item.
        label: Optional. The label of the key-value item. Defaults to None (null label).

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the key-value dictionary if found, otherwise None.
    """
    store_ref = get_app_config_store_ref(subscription_id, resource_group_name, store_name)
    if not store_ref: return None
    # Ensure list exists in store_ref and get a direct reference
    kvs_ref = store_ref.setdefault("key_values", [])
    for kv_ref in kvs_ref:
        if kv_ref.get("key") == key and kv_ref.get("label") == label:
            return kv_ref
    return None

# Finders for other resource types would follow a similar pattern:
# find_X, get_X_ref, find_Y_in_X, get_Y_in_X_ref

# Example: Storage Account and Blob Container
def find_storage_account(
    subscription_id: str, resource_group_name: str, account_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Storage Account by name within a specific resource group and subscription.

    Returns a copy of the Storage Account data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Storage Account.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Storage Account dictionary if found, otherwise None.
    """
    rg_data = find_resource_group(subscription_id, resource_group_name)
    if not rg_data: return None
    return _find_item_in_list(rg_data.get("storage_accounts", []), "name", account_name)

def get_storage_account_ref(
    subscription_id: str, resource_group_name: str, account_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Storage Account dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'storage_accounts' list in the parent resource group if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Storage Account.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Storage Account dictionary if found, otherwise None.
    """
    rg_ref = get_resource_group_ref(subscription_id, resource_group_name)
    if not rg_ref: return None
    # Ensure list exists in rg_ref and get a direct reference
    accounts_ref = rg_ref.setdefault("storage_accounts", [])
    return _get_item_ref_in_list(accounts_ref, "name", account_name)

def find_blob_container(
    subscription_id: str, resource_group_name: str, account_name: str, container_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Blob Container by name within a specific Storage Account.

    Returns a copy of the Blob Container data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Storage Account.
        container_name: The name of the Blob Container.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Blob Container dictionary if found, otherwise None.
    """
    sa_data = find_storage_account(subscription_id, resource_group_name, account_name)
    if not sa_data: return None
    return _find_item_in_list(sa_data.get("blob_containers", []), "name", container_name)

def get_blob_container_ref(
    subscription_id: str, resource_group_name: str, account_name: str, container_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Blob Container dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'blob_containers' list in the parent Storage Account if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Storage Account.
        container_name: The name of the Blob Container.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Blob Container dictionary if found, otherwise None.
    """
    sa_ref = get_storage_account_ref(subscription_id, resource_group_name, account_name)
    if not sa_ref: return None
    # Ensure list exists in sa_ref and get a direct reference
    containers_ref = sa_ref.setdefault("blob_containers", [])
    return _get_item_ref_in_list(containers_ref, "name", container_name)

# (Add more finders for KeyVault, CosmosDB, ServiceBus, etc. as needed, following the pattern)

# --- Cosmos DB Finders ---
def find_cosmos_db_account(
    subscription_id: str, resource_group_name: str, account_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Cosmos DB Account by name within a specific resource group and subscription.

    Returns a copy of the Cosmos DB Account data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Cosmos DB Account.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Cosmos DB Account dictionary if found, otherwise None.
    """
    rg_data = find_resource_group(subscription_id, resource_group_name)
    if not rg_data: return None
    return _find_item_in_list(rg_data.get("cosmos_db_accounts", []), "name", account_name)

def get_cosmos_db_account_ref(
    subscription_id: str, resource_group_name: str, account_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Cosmos DB Account dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'cosmos_db_accounts' list in the parent resource group if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Cosmos DB Account.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Cosmos DB Account dictionary if found, otherwise None.
    """
    rg_ref = get_resource_group_ref(subscription_id, resource_group_name)
    if not rg_ref: return None
    # Ensure list exists in rg_ref and get a direct reference
    accounts_ref = rg_ref.setdefault("cosmos_db_accounts", [])
    return _get_item_ref_in_list(accounts_ref, "name", account_name)

def find_cosmos_db_database(
    subscription_id: str, resource_group_name: str, account_name: str, database_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Cosmos DB Database by name within a specific Cosmos DB Account.

    Returns a copy of the Cosmos DB Database data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Cosmos DB Account.
        database_name: The name of the Cosmos DB Database.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Cosmos DB Database dictionary if found, otherwise None.
    """
    account_data = find_cosmos_db_account(subscription_id, resource_group_name, account_name)
    if not account_data: return None
    return _find_item_in_list(account_data.get("databases", []), "name", database_name)

def get_cosmos_db_database_ref(
    subscription_id: str, resource_group_name: str, account_name: str, database_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Cosmos DB Database dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'databases' list in the parent Cosmos DB Account if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Cosmos DB Account.
        database_name: The name of the Cosmos DB Database.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Cosmos DB Database dictionary if found, otherwise None.
    """
    account_ref = get_cosmos_db_account_ref(subscription_id, resource_group_name, account_name)
    if not account_ref: return None
    # Ensure list exists in account_ref and get a direct reference
    databases_ref = account_ref.setdefault("databases", [])
    return _get_item_ref_in_list(databases_ref, "name", database_name)

def find_cosmos_db_container(
    subscription_id: str, resource_group_name: str, account_name: str, database_name: str, container_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Cosmos DB Container by name within a specific Cosmos DB Database.

    Returns a copy of the Cosmos DB Container data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Cosmos DB Account.
        database_name: The name of the Cosmos DB Database.
        container_name: The name of the Cosmos DB Container.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Cosmos DB Container dictionary if found, otherwise None.
    """
    db_data = find_cosmos_db_database(subscription_id, resource_group_name, account_name, database_name)
    if not db_data: return None
    return _find_item_in_list(db_data.get("containers", []), "name", container_name)

def get_cosmos_db_container_ref(
    subscription_id: str, resource_group_name: str, account_name: str, database_name: str, container_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Cosmos DB Container dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'containers' list in the parent Cosmos DB Database if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Cosmos DB Account.
        database_name: The name of the Cosmos DB Database.
        container_name: The name of the Cosmos DB Container.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Cosmos DB Container dictionary if found, 
                                   otherwise None.
    """
    db_ref = get_cosmos_db_database_ref(subscription_id, resource_group_name, account_name, database_name)
    if not db_ref: return None
    # Ensure list exists in db_ref and get a direct reference
    containers_ref = db_ref.setdefault("containers", [])
    return _get_item_ref_in_list(containers_ref, "name", container_name)

# --- Key Vault Finders ---
def find_key_vault(
    subscription_id: str, resource_group_name: str, vault_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Key Vault by name within a specific resource group and subscription.

    Returns a copy of the Key Vault data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        vault_name: The name of the Key Vault.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Key Vault dictionary if found, otherwise None.
    """
    rg_data = find_resource_group(subscription_id, resource_group_name)
    if not rg_data: return None
    return _find_item_in_list(rg_data.get("key_vaults", []), "name", vault_name)

def get_key_vault_ref(
    subscription_id: str, resource_group_name: str, vault_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Key Vault dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'key_vaults' list in the parent resource group if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        vault_name: The name of the Key Vault.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Key Vault dictionary if found, otherwise None.
    """
    rg_ref = get_resource_group_ref(subscription_id, resource_group_name)
    if not rg_ref: return None
    # Ensure list exists in rg_ref and get a direct reference
    vaults_ref = rg_ref.setdefault("key_vaults", [])
    return _get_item_ref_in_list(vaults_ref, "name", vault_name)

def find_key_vault_key(
    subscription_id: str, resource_group_name: str, vault_name: str, key_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Key Vault Key by name within a specific Key Vault.

    Returns a copy of the Key Vault Key data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        vault_name: The name of the Key Vault.
        key_name: The name of the Key Vault Key.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Key Vault Key dictionary if found, otherwise None.
    """
    vault_data = find_key_vault(subscription_id, resource_group_name, vault_name)
    if not vault_data: return None
    return _find_item_in_list(vault_data.get("keys", []), "name", key_name)

def get_key_vault_key_ref(
    subscription_id: str, resource_group_name: str, vault_name: str, key_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Key Vault Key dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'keys' list in the parent Key Vault if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        vault_name: The name of the Key Vault.
        key_name: The name of the Key Vault Key.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Key Vault Key dictionary if found, otherwise None.
    """
    vault_ref = get_key_vault_ref(subscription_id, resource_group_name, vault_name)
    if not vault_ref: return None
    # Ensure list exists in vault_ref and get a direct reference
    keys_ref = vault_ref.setdefault("keys", [])
    return _get_item_ref_in_list(keys_ref, "name", key_name)

# --- Log Analytics / Monitor Finders ---
def find_log_analytics_workspace(
    subscription_id: str, resource_group_name: str, workspace_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Log Analytics Workspace by name within a specific resource group and subscription.

    Returns a copy of the Log Analytics Workspace data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        workspace_name: The name of the Log Analytics Workspace.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Workspace dictionary if found, otherwise None.
    """
    rg_data = find_resource_group(subscription_id, resource_group_name)
    if not rg_data: return None
    return _find_item_in_list(rg_data.get("log_analytics_workspaces", []), "name", workspace_name)

def get_log_analytics_workspace_ref(
    subscription_id: str, resource_group_name: str, workspace_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Log Analytics Workspace dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'log_analytics_workspaces' list in the parent resource group if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        workspace_name: The name of the Log Analytics Workspace.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Workspace dictionary if found, otherwise None.
    """
    rg_ref = get_resource_group_ref(subscription_id, resource_group_name)
    if not rg_ref: return None
    # Ensure list exists in rg_ref and get a direct reference
    workspaces_ref = rg_ref.setdefault("log_analytics_workspaces", [])
    return _get_item_ref_in_list(workspaces_ref, "name", workspace_name)

def find_log_analytics_table(
    subscription_id: str, resource_group_name: str, workspace_name: str, table_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Log Analytics Table by name within a specific Log Analytics Workspace.

    Returns a copy of the Log Analytics Table data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        workspace_name: The name of the Log Analytics Workspace.
        table_name: The name of the Log Analytics Table.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Table dictionary if found, otherwise None.
    """
    ws_data = find_log_analytics_workspace(subscription_id, resource_group_name, workspace_name)
    if not ws_data: return None
    return _find_item_in_list(ws_data.get("tables", []), "name", table_name)

def get_log_analytics_table_ref(
    subscription_id: str, resource_group_name: str, workspace_name: str, table_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Log Analytics Table dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'tables' list in the parent Log Analytics Workspace if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        workspace_name: The name of the Log Analytics Workspace.
        table_name: The name of the Log Analytics Table.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Table dictionary if found, otherwise None.
    """
    ws_ref = get_log_analytics_workspace_ref(subscription_id, resource_group_name, workspace_name)
    if not ws_ref: return None
    # Ensure list exists in ws_ref and get a direct reference
    tables_ref = ws_ref.setdefault("tables", [])
    return _get_item_ref_in_list(tables_ref, "name", table_name)

def find_monitor_health_model(
    subscription_id: str, resource_group_name: str, model_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Monitor Health Model by name within a specific resource group and subscription.

    Returns a copy of the Monitor Health Model data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        model_name: The name of the Monitor Health Model.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Model dictionary if found, otherwise None.
    """
    rg_data = find_resource_group(subscription_id, resource_group_name)
    if not rg_data: return None
    return _find_item_in_list(rg_data.get("monitor_health_models", []), "name", model_name)

def get_monitor_health_model_ref(
    subscription_id: str, resource_group_name: str, model_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Monitor Health Model dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'monitor_health_models' list in the parent resource group if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        model_name: The name of the Monitor Health Model.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Model dictionary if found, otherwise None.
    """
    rg_ref = get_resource_group_ref(subscription_id, resource_group_name)
    if not rg_ref: return None
    # Ensure list exists in rg_ref and get a direct reference
    models_ref = rg_ref.setdefault("monitor_health_models", [])
    return _get_item_ref_in_list(models_ref, "name", model_name)

def find_monitor_health_entity(
    subscription_id: str, resource_group_name: str, model_name: str, entity_id: str
) -> Optional[Dict[str, Any]]:
    """Finds a Monitor Health Entity by ID within a specific Monitor Health Model.

    Returns a copy of the Monitor Health Entity data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        model_name: The name of the Monitor Health Model.
        entity_id: The ID of the Monitor Health Entity.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Entity dictionary if found, otherwise None.
    """
    model_data = find_monitor_health_model(subscription_id, resource_group_name, model_name)
    if not model_data: return None
    return _find_item_in_list(model_data.get("entities", []), "entityId", entity_id)

def get_monitor_health_entity_ref(
    subscription_id: str, resource_group_name: str, model_name: str, entity_id: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Monitor Health Entity dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'entities' list in the parent Monitor Health Model if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        model_name: The name of the Monitor Health Model.
        entity_id: The ID of the Monitor Health Entity.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Entity dictionary if found, otherwise None.
    """
    model_ref = get_monitor_health_model_ref(subscription_id, resource_group_name, model_name)
    if not model_ref: return None
    # Ensure list exists in model_ref and get a direct reference
    entities_ref = model_ref.setdefault("entities", [])
    return _get_item_ref_in_list(entities_ref, "entityId", entity_id)

# --- Storage Blob and Table Finders ---
def find_storage_blob(
    subscription_id: str, resource_group_name: str, account_name: str, container_name: str, blob_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Storage Blob by name within a specific Blob Container.

    Returns a copy of the Storage Blob data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Storage Account.
        container_name: The name of the Blob Container.
        blob_name: The name of the Storage Blob.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Blob dictionary if found, otherwise None.
    """
    container_data = find_blob_container(subscription_id, resource_group_name, account_name, container_name)
    if not container_data: return None
    return _find_item_in_list(container_data.get("blobs", []), "name", blob_name)

def get_storage_blob_ref(
    subscription_id: str, resource_group_name: str, account_name: str, container_name: str, blob_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Storage Blob dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'blobs' list in the parent Blob Container if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Storage Account.
        container_name: The name of the Blob Container.
        blob_name: The name of the Storage Blob.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Blob dictionary if found, otherwise None.
    """
    container_ref = get_blob_container_ref(subscription_id, resource_group_name, account_name, container_name)
    if not container_ref: return None
    # Ensure list exists in container_ref and get a direct reference
    blobs_ref = container_ref.setdefault("blobs", [])
    return _get_item_ref_in_list(blobs_ref, "name", blob_name)

def find_storage_table(
    subscription_id: str, resource_group_name: str, account_name: str, table_name: str
) -> Optional[Dict[str, Any]]:
    """Finds a Storage Table by name within a specific Storage Account.

    Returns a copy of the Storage Table data if found.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Storage Account.
        table_name: The name of the Storage Table.

    Returns:
        Optional[Dict[str, Any]]: A copy of the Table dictionary if found, otherwise None.
    """
    sa_data = find_storage_account(subscription_id, resource_group_name, account_name)
    if not sa_data: return None
    return _find_item_in_list(sa_data.get("tables", []), "TableName", table_name)

def get_storage_table_ref(
    subscription_id: str, resource_group_name: str, account_name: str, table_name: str
) -> Optional[Dict[str, Any]]:
    """Gets a direct reference to a Storage Table dictionary.

    USE WITH CAUTION: Modifies the global DB state if the returned reference is altered.
    Initializes 'tables' list in the parent Storage Account if not present.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        account_name: The name of the Storage Account.
        table_name: The name of the Storage Table.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the Table dictionary if found, otherwise None.
    """
    sa_ref = get_storage_account_ref(subscription_id, resource_group_name, account_name)
    if not sa_ref: return None
    # Ensure list exists in sa_ref and get a direct reference
    tables_ref = sa_ref.setdefault("tables", [])
    return _get_item_ref_in_list(tables_ref, "TableName", table_name)

# (Add more finders for KeyVault, CosmosDB, ServiceBus, etc. as needed, following the pattern)


# --- Generic DB List Modification Utils ---
# These now operate on a direct list reference and specific item data.

def add_item_to_db_list(
    parent_item_list_ref: List[Dict[str, Any]],
    new_item_data: Dict[str, Any],
    unique_key_field: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Adds a new item (dictionary) to a referenced list if it doesn't already exist.

    This function directly modifies the `parent_item_list_ref` by appending `new_item_data`.
    If `unique_key_field` is provided, it checks for an existing item with the same value 
    in that field before adding, preventing duplicates. 

    Args:
        parent_item_list_ref: A direct reference to the list within the DB to which the item should be added.
        new_item_data: The dictionary representing the new item to add.
        unique_key_field: Optional. The name of the field to check for uniqueness. 
                          If None, the item is added without a uniqueness check.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the newly added item if successful. 
                                   Returns None if `unique_key_field` is provided and an item 
                                   with the same unique key value already exists, or if the 
                                   `new_item_data` does not contain the `unique_key_field`.
    """
    if unique_key_field:
        key_value_to_check = new_item_data.get(unique_key_field)
        if key_value_to_check is not None: # Ensure the new item has the unique key
            existing_item = _get_item_ref_in_list(parent_item_list_ref, unique_key_field, key_value_to_check)
            if existing_item:
                return None  # Item already exists

    parent_item_list_ref.append(new_item_data)
    return new_item_data # Return reference to the newly added item


def update_item_in_db_list(
    item_list_ref: List[Dict[str, Any]],
    update_payload: Dict[str, Any],
    unique_key_field: str, 
    unique_key_value: Any  
) -> Optional[Dict[str, Any]]:
    """Updates an existing item (dictionary) within a referenced list.

    Finds the item in `item_list_ref` where the `unique_key_field` matches `unique_key_value`,
    and then updates it with the contents of `update_payload`.
    This function directly modifies the item within `item_list_ref`.

    Args:
        item_list_ref: A direct reference to the list of dictionaries to search within.
        update_payload: A dictionary containing the key-value pairs to update in the found item.
        unique_key_field: The name of the field used to identify the item to update.
        unique_key_value: The value of the `unique_key_field` for the item to update.

    Returns:
        Optional[Dict[str, Any]]: A direct reference to the updated item if found and updated, 
                                   otherwise None.
    """
    item_to_update = _get_item_ref_in_list(item_list_ref, unique_key_field, unique_key_value)
    
    if item_to_update:
        item_to_update.update(update_payload)
        return item_to_update
    return None


def delete_item_from_db_list(
    parent_item_list_ref: List[Dict[str, Any]],
    primary_key_field: str,
    primary_key_value: Any,
    secondary_key_field: Optional[str] = None,
    secondary_key_value: Optional[Any] = None
) -> bool:
    """Deletes an item (dictionary) from a referenced list based on key matching.

    Finds an item in `parent_item_list_ref` where `primary_key_field` matches `primary_key_value`.
    If `secondary_key_field` and `secondary_key_value` are also provided, the item must match these too.
    This function directly modifies `parent_item_list_ref` by removing the item.

    Args:
        parent_item_list_ref: A direct reference to the list of dictionaries to delete from.
        primary_key_field: The primary field name to identify the item to delete.
        primary_key_value: The value of the `primary_key_field` for the item to delete.
        secondary_key_field: Optional. A secondary field name for more specific matching.
        secondary_key_value: Optional. The value of the `secondary_key_field` if used.

    Returns:
        bool: True if an item was successfully found and deleted, False otherwise.
    """
    item_to_delete_index = -1
    for i, item_ref in enumerate(parent_item_list_ref):
        if item_ref.get(primary_key_field) == primary_key_value:
            if secondary_key_field:
                if item_ref.get(secondary_key_field) == secondary_key_value:
                    item_to_delete_index = i
                    break
            else:
                item_to_delete_index = i
                break
    
    if item_to_delete_index != -1:
        del parent_item_list_ref[item_to_delete_index]
        return True
    return False

# --- Specific Resource Modification Utils (examples using generic helpers) ---

# AppConfig Key-Value Upsert
def update_or_create_app_config_kv(
    subscription_id: str, resource_group_name: str, store_name: str,
    kv_data_to_upsert: Dict[str, Any] 
) -> bool:
    """Updates an existing App Configuration key-value item or creates it if it does not exist.

    This function manages the `etag` and `last_modified` fields automatically.
    It also ensures the `app_config_store_name` is correctly set on the item.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        store_name: The name of the App Configuration store.
        kv_data_to_upsert: A dictionary containing the key-value data to upsert.
                           Must include "key". "label" can be None for the null label.
                           Other fields like "value", "locked", "content_type" will be 
                           updated or set to defaults if not provided during creation.

    Returns:
        bool: True if the operation (update or create) was successful. 
              False if the parent App Configuration store is not found.

    Raises:
        ValueError: If "key" is not present in `kv_data_to_upsert`.
    """
    key = kv_data_to_upsert.get("key")
    label = kv_data_to_upsert.get("label")

    if key is None:
        raise ValueError("Key is required for AppConfig key-value.")

    store_ref = get_app_config_store_ref(subscription_id, resource_group_name, store_name)
    if not store_ref:
        return False # Store not found
    
    kvs_list_ref = store_ref.setdefault("key_values", [])
    existing_kv_ref = _get_item_ref_in_list(kvs_list_ref, "key", key)
    # Refine to check label if label is provided for existing check
    if label is not None and existing_kv_ref and existing_kv_ref.get("label") != label:
        # if key matches but label doesn't, search specifically for key+label for update
        specific_existing_kv_ref = None
        for item_in_list in kvs_list_ref:
            if item_in_list.get("key") == key and item_in_list.get("label") == label:
                specific_existing_kv_ref = item_in_list
                break
        existing_kv_ref = specific_existing_kv_ref
    elif label is None and existing_kv_ref and existing_kv_ref.get("label") is not None:
        # if key matches but existing has a label and we are looking for null label
        specific_existing_kv_ref = None
        for item_in_list in kvs_list_ref:
            if item_in_list.get("key") == key and item_in_list.get("label") is None:
                specific_existing_kv_ref = item_in_list
                break
        existing_kv_ref = specific_existing_kv_ref

    current_time_iso = get_current_utc_timestamp_iso()
    new_etag = new_uuid_str()

    system_managed_updates = {
        "last_modified": current_time_iso,
        "etag": new_etag,
        "app_config_store_name": store_name
    }

    if existing_kv_ref: # Update existing
        update_payload = {**kv_data_to_upsert, **system_managed_updates}
        # Update the item directly as existing_kv_ref is a reference to the item in the list
        existing_kv_ref.update(update_payload)
    else: # Create new
        full_new_kv_data = {
            "key": key,
            "value": kv_data_to_upsert.get("value"),
            "label": label,
            "content_type": kv_data_to_upsert.get("content_type"),
            "locked": kv_data_to_upsert.get("locked", False),
            **system_managed_updates
        }
        add_item_to_db_list(kvs_list_ref, full_new_kv_data, "key") # Add to the list
    return True


def delete_app_config_kv(
    subscription_id: str, resource_group_name: str, store_name: str,
    key: str, label: Optional[str] = None
) -> bool:
    """Deletes an App Configuration key-value item from a store.

    The item is identified by its key and optional label.

    Args:
        subscription_id: The ID of the subscription.
        resource_group_name: The name of the resource group.
        store_name: The name of the App Configuration store.
        key: The key of the key-value item to delete.
        label: Optional. The label of the key-value item to delete. If None, targets the null label.

    Returns:
        bool: True if the item was successfully found and deleted. 
              False if the store is not found, the key-values list doesn't exist, 
              or the specific key-value item is not found.
    """
    store_ref = get_app_config_store_ref(subscription_id, resource_group_name, store_name)
    if not store_ref:
        return False # Store not found
    kvs_list_ref = store_ref.get("key_values")
    if not kvs_list_ref:
        return False # No key-values to delete from

    # Need to find the specific item to delete by key and label
    item_deleted = False
    for i in range(len(kvs_list_ref) - 1, -1, -1): # Iterate backwards for safe deletion
        kv_item = kvs_list_ref[i]
        if kv_item.get("key") == key and kv_item.get("label") == label:
            del kvs_list_ref[i]
            item_deleted = True
            break # Assuming key+label is unique
    return item_deleted


# --- Specific Logic Helpers ---

def check_resource_name_conflict(
    parent_collection_list_data: List[Dict[str, Any]],
    name_to_check: str,
    name_field: str = "name"
) -> bool:
    """Checks if a given name already exists in a list of dictionaries, based on a specified field.

    This is useful for validating if a new resource name would conflict with existing ones 
    within the same collection (e.g., checking if a resource group name is unique within a subscription).

    Args:
        parent_collection_list_data: The list of dictionaries representing the collection of resources.
        name_to_check: The name to check for potential conflict.
        name_field: The key in each dictionary that holds the name identifier (defaults to "name").

    Returns:
        bool: True if a dictionary with the same name in the specified `name_field` exists, 
              indicating a conflict. False otherwise.
    """
    return any(item_data.get(name_field) == name_to_check for item_data in parent_collection_list_data)


def filter_app_config_key_values(
    key_value_list_data: List[Dict[str, Any]],
    key_filter: Optional[str] = None,
    label_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Filters a list of App Configuration key-value items based on key and label criteria.

    Supports exact matches and wildcard searches (using '*' at the end of the filter string) 
    for both key and label filters. The label filter has special handling for the null label 
    (represented as '\0' in the filter string to match items where label is None).

    Args:
        key_value_list_data: A list of dictionaries, where each dictionary represents an 
                             App Configuration key-value item.
        key_filter: Optional. The filter string for the key. If None, all keys match.
        label_filter: Optional. The filter string for the label. If None, all labels match. 
                      Use '\0' to explicitly filter for null labels.

    Returns:
        List[Dict[str, Any]]: A new list containing copies of the key-value item dictionaries 
                               that match the filter criteria.
    """
    results = []
    for kv_item_data in key_value_list_data:
        key_match = True
        if key_filter is not None:
            item_key = kv_item_data.get('key', '')
            if key_filter.endswith('*'):
                key_match = item_key.startswith(key_filter[:-1])
            else:
                key_match = item_key == key_filter

        label_match = True
        if label_filter is not None:
            item_label = kv_item_data.get('label') # This can be None
            if label_filter == r'\0': # Special case for null label matching
                label_match = item_label is None
            elif label_filter.endswith('*'):
                lf_prefix = label_filter[:-1]
                if item_label is None: # Wildcard does not match None unless it's just '*'
                    label_match = (lf_prefix == "") # Only if key_filter is '*'
                else:
                    label_match = item_label.startswith(lf_prefix)
            else:
                label_match = item_label == label_filter
        
        if key_match and label_match:
            results.append(kv_item_data.copy())
    return results

def _validate_str_non_negative_int(param_value: str, param_name: str) -> int:
    """
    Validates if a string parameter represents a non-negative integer.
    Returns the integer value if valid, otherwise raises custom_errors.ValidationError.
    """
    try:
        val = int(param_value)
        if val < 0:
            # This ValueError will be caught by the same except block below.
            raise ValueError("Value cannot be negative.")
        return val
    except ValueError:
        raise custom_errors.ValidationError(
            f"Invalid format for '{param_name}'. Must be a string representing a non-negative integer."
        )

def get_subscription_data_by_id_or_name(
        subscription_identifier: str,
        all_subscriptions_data: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Finds a subscription's data dictionary by its ID or display name.

    Args:
        subscription_identifier: The subscription ID (GUID) or display name.
        all_subscriptions_data: A list of all subscription data dictionaries from the DB.

    Returns:
        Optional[Dict[str, Any]]: The subscription data dictionary if found, otherwise None.
    """
    # Attempt to find by subscriptionId first
    for sub_data in all_subscriptions_data:
        if sub_data.get("subscriptionId") == subscription_identifier:
            return sub_data

    # If not found by ID, attempt to find by displayName
    for sub_data in all_subscriptions_data:
        if sub_data.get("displayName") == subscription_identifier:
            return sub_data

    return None
