"""
azure API Simulation Module

This module provides a simulation of the azure API, allowing for testing
and development of azure workflows without requiring actual azure access.
"""
import os
from .SimulationEngine.db import DB, load_state, save_state
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from azure.SimulationEngine import utils

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map
_function_map = {
    # App Configuration (P0)
    "azmcp_appconfig_account_list": "azure.appconfig.azmcp_appconfig_account_list",
    "azmcp_appconfig_kv_delete": "azure.appconfig.azmcp_appconfig_kv_delete",
    "azmcp_appconfig_kv_list": "azure.appconfig.azmcp_appconfig_kv_list",
    "azmcp_appconfig_kv_lock": "azure.appconfig.azmcp_appconfig_kv_lock",
    "azmcp_appconfig_kv_set": "azure.appconfig.azmcp_appconfig_kv_set",
    "azmcp_appconfig_kv_show": "azure.appconfig.azmcp_appconfig_kv_show",
    "azmcp_appconfig_kv_unlock": "azure.appconfig.azmcp_appconfig_kv_unlock",

    # Cosmos DB (P0)
    "azmcp_cosmos_account_list": "azure.cosmos.azmcp_cosmos_account_list",
    "azmcp_cosmos_account_create": "azure.cosmos.azmcp_cosmos_account_create",
    "azmcp_cosmos_database_list": "azure.cosmos.azmcp_cosmos_database_list",
    "azmcp_cosmos_database_container_list": "azure.cosmos.azmcp_cosmos_database_container_list",
    #"azmcp_cosmos_database_container_item_query": "azure.cosmos.azmcp_cosmos_database_container_item_query", currently removed 

    # Key Vault (P0)
    "azmcp_keyvault_key_create": "azure.keyvault.azmcp_keyvault_key_create",
    "azmcp_keyvault_key_get": "azure.keyvault.azmcp_keyvault_key_get",
    "azmcp_keyvault_key_list": "azure.keyvault.azmcp_keyvault_key_list",

    # Monitor (Log Analytics & Health Models - P0)
    # Note: azmcp-monitor-workspace-list, azmcp-monitor-table-list, 
    # azmcp-monitor-table-type-list are implemented in loganalytics.py using their correct azmcp_monitor_* names.
    "azmcp_monitor_healthmodels_entity_gethealth": "azure.monitor.azmcp_monitor_healthmodels_entity_gethealth",
    "azmcp_monitor_workspace_list": "azure.loganalytics.azmcp_monitor_workspace_list",
    "azmcp_monitor_table_list": "azure.loganalytics.azmcp_monitor_table_list",
    "azmcp_monitor_table_type_list": "azure.loganalytics.azmcp_monitor_table_type_list",
    #"azmcp_monitor_log_query": "azure.loganalytics.azmcp_monitor_log_query",

    # Storage (P0)
    "azmcp_storage_account_list": "azure.storage.azmcp_storage_account_list",
    "azmcp_storage_blob_container_list": "azure.storage.azmcp_storage_blob_container_list",
    "azmcp_storage_blob_container_details": "azure.storage.azmcp_storage_blob_container_details",
    "azmcp_storage_blob_list": "azure.storage.azmcp_storage_blob_list",
    "azmcp_storage_table_list": "azure.storage.azmcp_storage_table_list",

    # Azure Resource & Subscription Management (P0)
    "azmcp_subscription_list": "azure.management.azmcp_subscription_list",
    "azmcp_group_list": "azure.management.azmcp_group_list",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())