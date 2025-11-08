from common_utils.tool_spec_decorator import tool_spec
from azure.SimulationEngine import custom_errors, models, utils
from azure.SimulationEngine.db import DB
from azure.SimulationEngine.models import AuthMethod, RetryMode
from typing import List, Dict, Any, Optional

@tool_spec(
    spec={
        'name': 'azmcp_monitor_table_list',
        'description': """ List all tables in a Log Analytics workspace.
        
        This function lists all tables in a specified Log Analytics workspace. It requires the workspace
        identifier and returns the names and schemas of the tables. This information can be utilized
        for constructing KQL (Kusto Query Language) queries. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_group': {
                    'type': 'string',
                    'description': 'The name of the Azure resource group. This is a logical container for Azure resources.'
                },
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
                },
                'table_type': {
                    'type': 'string',
                    'description': "The type of table to query. Options: 'CustomLog', 'AzureMetrics', etc."
                },
                'workspace': {
                    'type': 'string',
                    'description': 'The Log Analytics workspace ID or name. This can be either the unique identifier (GUID) or the display name of your workspace.'
                },
                'auth_method': {
                    'type': 'string',
                    'description': "Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. Defaults to None."
                },
                'retry_delay': {
                    'type': 'string',
                    'description': 'Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base. Defaults to None.'
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': 'Maximum delay in seconds between retries, regardless of the retry strategy. Defaults to None.'
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': 'Maximum number of retry attempts for failed operations before giving up. Defaults to None.'
                },
                'retry_mode': {
                    'type': 'string',
                    'description': "Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts. Defaults to None."
                },
                'retry_network_timeout': {
                    'type': 'string',
                    'description': 'Network operation timeout in seconds. Operations taking longer than this will be cancelled. Defaults to None.'
                },
                'tenant': {
                    'type': 'string',
                    'description': 'The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant. Defaults to None.'
                }
            },
            'required': [
                'resource_group',
                'subscription',
                'table_type',
                'workspace'
            ]
        }
    }
)
def azmcp_monitor_table_list(
    resource_group: str,
    subscription: str,
    table_type: str,
    workspace: str,
    auth_method: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None,
    tenant: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all tables in a Log Analytics workspace.

    This function lists all tables in a specified Log Analytics workspace. It requires the workspace
    identifier and returns the names and schemas of the tables. This information can be utilized
    for constructing KQL (Kusto Query Language) queries.

    Args:
        resource_group (str): The name of the Azure resource group. This is a logical container for Azure resources.
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        table_type (str): The type of table to query. Options: 'CustomLog', 'AzureMetrics', etc.
        workspace (str): The Log Analytics workspace ID or name. This can be either the unique identifier (GUID) or the display name of your workspace.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. Defaults to None.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base. Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy. Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts. Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled. Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant. Defaults to None.

    Returns:
        List[Dict[str, Any]]: A list of tables in the Log Analytics workspace. Each dictionary in the list represents a table and contains the following keys:
            name (str): The name of the table.
            id (str): The resource ID of the table.
            timespan (str): The retention period for the table data (e.g., 'P90D' for 90 days).
            schema (Dict[str, Any]): The schema definition for the table. This dictionary contains:
                name (str): The name of the table (repeated for clarity within the schema object).
                displayName (str): The display name of the table.
                columns (List[Dict[str, str]]): A list of columns. Each column dictionary details a column in the table and contains:
                    name (str): The name of the column.
                    type (str): The data type of the column (e.g., 'string', 'datetime', 'real').

    Raises:
        ResourceNotFoundError: If the specified Log Analytics workspace does not exist or if dependent resources like subscription or resource group are not found.
        InvalidInputError: If required parameters such as 'subscription_id', 'workspace_name', or 'resource_group_name' are missing or provided with invalid values.
    """
    # Validate required string arguments
    if not subscription:
        raise custom_errors.InvalidInputError("Parameter 'subscription' is required and cannot be empty.")
    if not resource_group:
        raise custom_errors.InvalidInputError("Parameter 'resource_group' is required and cannot be empty.")
    if not workspace:
        raise custom_errors.InvalidInputError("Parameter 'workspace' is required and cannot be empty.")
    if not table_type:
        raise custom_errors.InvalidInputError("Parameter 'table_type' is required and cannot be empty.")

    # Find subscription
    actual_subscription_id_guid: Optional[str] = None
    sub_obj_data: Optional[Dict[str, Any]] = None
    
    found_sub_by_id = utils.find_subscription(subscription_id=subscription)
    if found_sub_by_id:
        sub_obj_data = found_sub_by_id
        actual_subscription_id_guid = found_sub_by_id.get("subscriptionId")
    else:
        all_subs_data = DB.get("subscriptions", [])
        for sub_candidate_data in all_subs_data:
            if sub_candidate_data.get("displayName") == subscription:
                sub_obj_data = sub_candidate_data
                actual_subscription_id_guid = sub_candidate_data.get("subscriptionId")
                break
    
    if not sub_obj_data or not actual_subscription_id_guid:
        raise custom_errors.ResourceNotFoundError(f"Subscription '{subscription}' not found.")

    # Find resource group
    rg_obj_data = utils.find_resource_group(
        subscription_id=actual_subscription_id_guid,
        resource_group_name=resource_group
    )
    if not rg_obj_data:
        raise custom_errors.ResourceNotFoundError(
            f"Resource group '{resource_group}' not found in subscription '{subscription}'."
        )

    # Find Log Analytics workspace
    workspace_obj_data: Optional[Dict[str, Any]] = None
    
    found_ws_by_name = utils.find_log_analytics_workspace(
        subscription_id=actual_subscription_id_guid,
        resource_group_name=resource_group,
        workspace_name=workspace
    )

    if found_ws_by_name:
        workspace_obj_data = found_ws_by_name
    else:
        workspaces_in_rg = rg_obj_data.get("log_analytics_workspaces", [])
        for ws_candidate_data in workspaces_in_rg:
            if ws_candidate_data.get("id") == workspace or \
               ws_candidate_data.get("customerId") == workspace:
                workspace_obj_data = ws_candidate_data
                break
    
    if not workspace_obj_data:
        raise custom_errors.ResourceNotFoundError(f"Log Analytics workspace '{workspace}' not found in resource group '{resource_group}' for subscription '{subscription}'.")

    # List and filter tables
    result_tables: List[Dict[str, Any]] = []
    # Corrected: Ensure all_tables_in_workspace is a list, even if workspace_obj_data["tables"] is None.
    all_tables_in_workspace = workspace_obj_data.get("tables") or []


    for table_data in all_tables_in_workspace:
        table_name = table_data.get("name")
        if not table_name: 
            continue

        matches_filter = False
        if table_type == "CustomLog":
            if table_name.endswith("_CL"):
                matches_filter = True
        elif table_type == "AzureMetrics": 
            if table_name == "AzureMetrics":
                matches_filter = True
        else: 
            if table_name == table_type:
                matches_filter = True
        
        if matches_filter:
            # Corrected: Ensure schema_details_data is a dict, even if table_data["schema_details"] is None.
            schema_details_data = table_data.get("schema_details") or {}
            
            output_schema_columns: List[Dict[str, str]] = []
            db_columns = schema_details_data.get("columns")
            for col_data in (db_columns or []): 
                col_name = col_data.get("name")
                col_type = col_data.get("type")
                if col_name and col_type: 
                     output_schema_columns.append({"name": col_name, "type": col_type})

            schema_name = schema_details_data.get("name") or table_name
            schema_display_name = schema_details_data.get("displayName") or table_name

            output_schema = models.LogAnalyticsTableSchemaReturn(
                name=schema_name,
                displayName=schema_display_name,
                columns=output_schema_columns
            ).model_dump()
            
            table_id = table_data.get("id")
            table_timespan = table_data.get("timespan")

            if table_id is not None and table_timespan is not None:
                result_tables.append(models.LogAnalyticsTableListItemReturn(
                    name=table_name,
                    id=table_id,
                    timespan=table_timespan,
                    schema=output_schema
                ).model_dump())

    return result_tables


@tool_spec(
    spec={
        'name': 'azmcp_monitor_table_type_list',
        'description': """ List available table types in a Log Analytics workspace. Returns table type names.
        
        This function lists the available table types within a specified Log Analytics workspace.
        It returns a list containing the names of these table types. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either the GUID
                    identifier or the display name of the Azure subscription to use. """
                },
                'workspace': {
                    'type': 'string',
                    'description': """ The Log Analytics workspace ID or name. This can be either the
                    unique identifier (GUID) or the display name of your workspace. """
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
                    'description': """ Initial delay in seconds between retry attempts.
                    For exponential backoff, this value is used as the base. """
                },
                'retry_max_delay': {
                    'type': 'string',
                    'description': """ Maximum delay in seconds between retries,
                    regardless of the retry strategy. """
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
                }
            },
            'required': [
                'subscription',
                'workspace'
            ]
        }
    }
)
def azmcp_monitor_table_type_list(
        subscription: str,
        workspace: str,
        auth_method: Optional[str] = None,
        tenant: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None
) -> List[str]:
    """List available table types in a Log Analytics workspace. Returns table type names.

    This function lists the available table types within a specified Log Analytics workspace.
    It returns a list containing the names of these table types.

    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID
            identifier or the display name of the Azure subscription to use.
        workspace (str): The Log Analytics workspace ID or name. This can be either the
            unique identifier (GUID) or the display name of your workspace.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be
            either the GUID identifier or the display name of your Azure AD tenant.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed
            operations before giving up.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts.
            For exponential backoff, this value is used as the base.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent
            delays, 'exponential' increases delay between attempts.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled.

    Returns:
        List[str]: A list of available table type names in the Log Analytics workspace
            (e.g., 'AzureDiagnostics', 'CustomLogs').

    Raises:
        ResourceNotFoundError: If the specified Log Analytics workspace does not exist.
        InvalidInputError: If required parameter 'workspace_name' is missing or if any
            optional parameter has an invalid value.
        ServiceError: If there is an issue with the Azure Monitor Log Analytics service.
    """

    if not subscription:
        raise custom_errors.InvalidInputError("The subscription ID or name cannot be empty.")
    if not workspace:
        raise custom_errors.InvalidInputError("The Log Analytics workspace ID or name cannot be empty.")

    # Validate auth_method if provided
    if auth_method is not None:
        if not isinstance(auth_method, str):
            raise custom_errors.InvalidInputError("auth_method must be a string.")
        try:
            auth_method = AuthMethod(auth_method)
        except ValueError:
            valid_methods = [method.value for method in AuthMethod]
            raise custom_errors.InvalidInputError(f"Invalid auth_method. Must be one of: {', '.join(valid_methods)}")

    # Validate tenant if provided
    if tenant is not None and not tenant.strip():
        raise custom_errors.InvalidInputError("The tenant ID or name cannot be empty if provided.")

    # Validate retry parameters if provided
    if retry_max_retries is not None:
        try:
            max_retries = int(retry_max_retries)
            if max_retries < 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_retries must be a non-negative integer.")

    if retry_delay is not None:
        try:
            delay = float(retry_delay)
            if delay <= 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_delay must be a positive number.")

    if retry_max_delay is not None:
        try:
            max_delay = float(retry_max_delay)
            if max_delay <= 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_max_delay must be a positive number.")

    if retry_mode is not None:
        if not isinstance(retry_mode, str):
            raise custom_errors.InvalidInputError("retry_mode must be a string.")
        try:
            retry_mode = RetryMode(retry_mode)
        except ValueError:
            valid_modes = [mode.value for mode in RetryMode]
            raise custom_errors.InvalidInputError(f"Invalid retry_mode. Must be one of: {', '.join(valid_modes)}")

    if retry_network_timeout is not None:
        try:
            timeout = float(retry_network_timeout)
            if timeout <= 0:
                raise ValueError
        except ValueError:
            raise custom_errors.InvalidInputError("retry_network_timeout must be a positive number.")

    subscriptions_list = DB.get("subscriptions", [])
    target_sub_data = None
    for sub_in_db in subscriptions_list:
        if sub_in_db.get("subscriptionId") == subscription or sub_in_db.get("displayName") == subscription:
            target_sub_data = sub_in_db
            break

    if not target_sub_data:
        raise custom_errors.SubscriptionNotFoundError(
            f"Subscription '{subscription}' not found."
        )

    found_workspace_data = None
    for rg_data in target_sub_data.get("resource_groups", []):
        for ws_item in rg_data.get("log_analytics_workspaces", []):
            if ws_item.get("name") == workspace or ws_item.get("id") == workspace:
                found_workspace_data = ws_item
                break
        if found_workspace_data:
            break

    if not found_workspace_data:
        raise custom_errors.ResourceNotFoundError(
            f"Log Analytics workspace '{workspace}' not found in subscription '{subscription}'."
        )

    raw_table_types = found_workspace_data.get("available_table_types")

    if raw_table_types is None:
        return []

    if not isinstance(raw_table_types, list) or not all(isinstance(item, str) for item in raw_table_types):
        raise custom_errors.ServiceError(
            f"Log Analytics workspace '{workspace}' contains malformed table type data."
        )

    return raw_table_types


@tool_spec(
    spec={
        'name': 'azmcp_monitor_workspace_list',
        'description': """ List Log Analytics workspaces in a subscription.
        
        This command retrieves all Log Analytics workspaces available in the specified Azure subscription,
        displaying their names, IDs, and other key properties. Use this command to identify
        workspaces before querying their logs or tables. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'subscription': {
                    'type': 'string',
                    'description': """ The Azure subscription ID or name. This can be either the GUID
                    identifier or the display name of the Azure subscription to use. """
                },
                'auth_method': {
                    'type': 'string',
                    'description': """ Authentication method to use. Options: 'credential'
                    (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
                    Defaults to None. """
                },
                'tenant': {
                    'type': 'string',
                    'description': """ The Azure Active Directory tenant ID or name. This can be
                    either the GUID identifier or the display name of your Azure AD tenant.
                    Defaults to None. """
                },
                'retry_max_retries': {
                    'type': 'string',
                    'description': """ Maximum number of retry attempts for failed
                    operations before giving up. Defaults to None. """
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
                'subscription'
            ]
        }
    }
)
def azmcp_monitor_workspace_list(
        subscription: str,
        auth_method: Optional[str] = None,
        tenant: Optional[str] = None,
        retry_max_retries: Optional[str] = None,
        retry_delay: Optional[str] = None,
        retry_max_delay: Optional[str] = None,
        retry_mode: Optional[str] = None,
        retry_network_timeout: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List Log Analytics workspaces in a subscription.
    This command retrieves all Log Analytics workspaces available in the specified Azure subscription,
    displaying their names, IDs, and other key properties. Use this command to identify
    workspaces before querying their logs or tables.
    Args:
        subscription (str): The Azure subscription ID or name. This can be either the GUID
            identifier or the display name of the Azure subscription to use.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential'
            (Azure CLI/managed identity), 'key' (access key), or 'connectionString'.
            Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be
            either the GUID identifier or the display name of your Azure AD tenant.
            Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed
            operations before giving up. Defaults to None.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts.
            For exponential backoff, this value is used as the base. Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries,
            regardless of the retry strategy. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent
            delays, 'exponential' increases delay between attempts. Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds.
            Operations taking longer than this will be cancelled. Defaults to None.
    Returns:
        List[Dict[str, Any]]: A list of Log Analytics workspaces. Each dictionary in the
        list represents a workspace and contains the following keys:
            name (str): The name of the Log Analytics workspace.
            id (str): The Azure Resource Manager (ARM) ID of the workspace.
            location (str): The Azure region where the workspace is located.
            customerId (str): The unique identifier for the workspace customer.
            sku (Dict[str, str]): Stock Keeping Unit (SKU) details for the workspace.
                This dictionary contains:
                name (str): The name of the SKU (e.g., 'PerGB2018', 'Standalone').
            provisioningState (str): The provisioning state of the workspace
                (e.g., 'Succeeded', 'Creating', 'Failed').
    Raises:
        SubscriptionNotFoundError: If the specified subscription ID is not found.
        InvalidInputError: If input arguments fail validation.
    """

    if not subscription:
        raise custom_errors.InvalidInputError("Subscription argument cannot be empty.")

    if retry_mode is not None:
        allowed_modes = [mode.value for mode in models.RetryMode]
        if retry_mode not in allowed_modes:
            # Avoid nesting an f-string inside another f-string
            allowed_values = ", ".join("'{}'".format(m) for m in allowed_modes)
            raise custom_errors.InvalidInputError(
                f"Invalid value for retry_mode. Allowed values are {allowed_values}."
            )


    if retry_max_retries is not None:
        try:
            _ = int(retry_max_retries)
        except ValueError:
            raise custom_errors.InvalidInputError(
                "Invalid format for retry_max_retries. Must be a string representing an integer."
            )

    retry_floats_to_validate = {
        "retry_delay": retry_delay,
        "retry_max_delay": retry_max_delay,
        "retry_network_timeout": retry_network_timeout
    }
    for param_name, param_value in retry_floats_to_validate.items():
        if param_value is None:
            continue

        try:
            _ = float(param_value)
            stripped_param_value = param_value.strip()
            if stripped_param_value == '.' and len(stripped_param_value) == 1:

                raise ValueError(
                    "Input consisting of only a dot (possibly with whitespace) is not a valid number representation."
                )
        except ValueError:
            raise custom_errors.InvalidInputError(
                f"Invalid format for {param_name}. Must be a string representing a number."
            )

    sub_by_id = utils.find_subscription(subscription_id=subscription)
    if sub_by_id:
        subscription_data = sub_by_id
    else:
        subscriptions_list = DB.get("subscriptions", [])
        subscription_data = None
        for sub_data_iter in subscriptions_list:
            if sub_data_iter.get("displayName") == subscription:
                subscription_data = sub_data_iter.copy()
                break

    if not subscription_data:
        raise custom_errors.SubscriptionNotFoundError("The specified Azure subscription was not found or is not accessible.")

    collected_workspaces: List[Dict[str, Any]] = []

    resource_groups = subscription_data.get("resource_groups") or []
    for rg_data in resource_groups:
        log_analytics_workspaces_in_rg = rg_data.get("log_analytics_workspaces") or []

        for ws_data in log_analytics_workspaces_in_rg:
            try:
                workspace_info = models.AzmcpMonitorWorkspaceListItem(
                    name=ws_data.get("name"),
                    id=ws_data.get("id"),
                    location=ws_data.get("location"),
                    customerId=ws_data.get("customerId"),
                    sku=models.LogAnalyticsWorkspaceSku(name=ws_data.get("sku").get("name")),
                    provisioningState=ws_data.get("provisioningState")
                )
            except:
                continue
            collected_workspaces.append(workspace_info.model_dump())

    return collected_workspaces

