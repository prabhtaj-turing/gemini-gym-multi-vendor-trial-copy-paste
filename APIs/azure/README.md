# Azure API Simulation

This module provides a comprehensive simulation of Azure cloud services API, allowing for testing and development of Azure workflows without requiring actual Azure access.

## Overview

The Azure API simulation includes multiple Azure services and provides a realistic environment for testing Azure-related functionality. It supports various Azure services including App Configuration, Cosmos DB, Key Vault, Monitor, Storage, and Resource Management.

## Components

### App Configuration (P0)
- **Account Management**: List App Configuration accounts
- **Key-Value Operations**: 
  - List, get, set, delete key-value pairs
  - Lock/unlock key-value pairs
  - Manage configuration settings

### Cosmos DB (P0)
- **Account Management**: Create and list Cosmos DB accounts
- **Database Operations**: List databases and containers
- **Container Management**: List containers within databases

### Key Vault (P0)
- **Key Management**: Create, get, and list cryptographic keys
- **Secure Storage**: Manage sensitive configuration data

### Monitor (P0)
- **Health Models**: Get entity health information
- **Log Analytics**: 
  - List workspaces, tables, and table types
  - Query monitoring data
- **Workspace Management**: Manage monitoring workspaces

### Storage (P0)
- **Account Management**: List storage accounts
- **Blob Storage**: 
  - List blob containers and blobs
  - Get container details
- **Table Storage**: List storage tables

### Resource Management (P0)
- **Subscription Management**: List Azure subscriptions
- **Resource Groups**: List resource groups

## Key Functions

### App Configuration
- `azmcp_appconfig_account_list` - List App Configuration accounts
- `azmcp_appconfig_kv_list` - List key-value pairs
- `azmcp_appconfig_kv_set` - Set key-value pairs
- `azmcp_appconfig_kv_get` - Get key-value pairs
- `azmcp_appconfig_kv_delete` - Delete key-value pairs
- `azmcp_appconfig_kv_lock` - Lock key-value pairs
- `azmcp_appconfig_kv_unlock` - Unlock key-value pairs

### Cosmos DB
- `azmcp_cosmos_account_list` - List Cosmos DB accounts
- `azmcp_cosmos_account_create` - Create Cosmos DB account
- `azmcp_cosmos_database_list` - List databases
- `azmcp_cosmos_database_container_list` - List containers

### Key Vault
- `azmcp_keyvault_key_create` - Create cryptographic keys
- `azmcp_keyvault_key_get` - Get key information
- `azmcp_keyvault_key_list` - List keys

### Monitor
- `azmcp_monitor_healthmodels_entity_gethealth` - Get entity health
- `azmcp_monitor_workspace_list` - List monitoring workspaces
- `azmcp_monitor_table_list` - List monitoring tables
- `azmcp_monitor_table_type_list` - List table types

### Storage
- `azmcp_storage_account_list` - List storage accounts
- `azmcp_storage_blob_container_list` - List blob containers
- `azmcp_storage_blob_container_details` - Get container details
- `azmcp_storage_blob_list` - List blobs
- `azmcp_storage_table_list` - List storage tables

### Resource Management
- `azmcp_subscription_list` - List Azure subscriptions
- `azmcp_group_list` - List resource groups

## Usage

The Azure API simulation provides a realistic environment for testing Azure workflows. All functions return simulated data that mimics real Azure API responses, allowing developers to test their Azure integration code without requiring actual Azure credentials or resources.

## Error Handling

The module includes comprehensive error simulation that can be configured to test various error scenarios, including network failures, authentication errors, and service-specific errors.

## Testing

The module includes a comprehensive test suite in the `tests/` directory that validates the functionality of all Azure service simulations.

## Dependencies

- `common_utils` - Shared utilities for error handling and simulation
- `SimulationEngine` - Database and state management for simulations 