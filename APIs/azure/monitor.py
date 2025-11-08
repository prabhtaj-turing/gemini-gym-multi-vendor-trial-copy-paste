from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List, Optional

from .SimulationEngine.db import DB
from .SimulationEngine import utils
from .SimulationEngine import custom_errors
from .SimulationEngine import models

@tool_spec(
    spec={
        'name': 'azmcp_monitor_healthmodels_entity_gethealth',
        'description': """ Gets the health of an entity from a specified Azure Monitor Health Model.
        
        This function retrieves the health of a specific entity from an Azure Monitor Health Model.
        It returns detailed entity health information. To perform this operation, the entity identifier,
        the health model name, the Azure resource group, and the subscription must be provided. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'entity': {
                    'type': 'string',
                    'description': 'The entity to get health for.'
                },
                'model_name': {
                    'type': 'string',
                    'description': 'The name of the health model for which to get the health.'
                },
                'resource_group': {
                    'type': 'string',
                    'description': 'The name of the Azure resource group. This is a logical container for Azure resources.'
                },
                'subscription': {
                    'type': 'string',
                    'description': 'The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.'
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
                'entity',
                'model_name',
                'resource_group',
                'subscription'
            ]
        }
    }
)
def azmcp_monitor_healthmodels_entity_gethealth(
    entity: str,
    model_name: str,
    resource_group: str,
    subscription: str,
    auth_method: Optional[str] = None,
    retry_delay: Optional[str] = None,
    retry_max_delay: Optional[str] = None,
    retry_max_retries: Optional[str] = None,
    retry_mode: Optional[str] = None,
    retry_network_timeout: Optional[str] = None,
    tenant: Optional[str] = None
) -> Dict[str, Any]:
    """Gets the health of an entity from a specified Azure Monitor Health Model.

    This function retrieves the health of a specific entity from an Azure Monitor Health Model.
    It returns detailed entity health information. To perform this operation, the entity identifier,
    the health model name, the Azure resource group, and the subscription must be provided.

    Args:
        entity (str): The entity to get health for.
        model_name (str): The name of the health model for which to get the health.
        resource_group (str): The name of the Azure resource group. This is a logical container for Azure resources.
        subscription (str): The Azure subscription ID or name. This can be either the GUID identifier or the display name of the Azure subscription to use.
        auth_method (Optional[str]): Authentication method to use. Options: 'credential' (Azure CLI/managed identity), 'key' (access key), or 'connectionString'. Defaults to None.
        retry_delay (Optional[str]): Initial delay in seconds between retry attempts. For exponential backoff, this value is used as the base. Defaults to None.
        retry_max_delay (Optional[str]): Maximum delay in seconds between retries, regardless of the retry strategy. Defaults to None.
        retry_max_retries (Optional[str]): Maximum number of retry attempts for failed operations before giving up. Defaults to None.
        retry_mode (Optional[str]): Retry strategy to use. 'fixed' uses consistent delays, 'exponential' increases delay between attempts. Defaults to None.
        retry_network_timeout (Optional[str]): Network operation timeout in seconds. Operations taking longer than this will be cancelled. Defaults to None.
        tenant (Optional[str]): The Azure Active Directory tenant ID or name. This can be either the GUID identifier or the display name of your Azure AD tenant. Defaults to None.

    Returns:
        Dict[str, Any]: Health information for the specified entity. This dictionary includes the following keys:
            entityId (str): The ID of the entity whose health is reported.
            healthState (str): The current health state of the entity (e.g., 'Healthy', 'Unhealthy', 'Warning').
            causes (List[Dict[str, Any]]): A list of causes contributing to the health state. Each dictionary in this list represents a cause and contains:
                description (str): Description of the cause.
                severity (str): Severity of the cause (e.g., 'Critical', 'Error', 'Warning', 'Information').
                recommendedActions (List[str]): Recommended actions to address the cause.

    Raises:
        ResourceNotFoundError: If the specified health model or entity does not exist.
        InvalidInputError: If required parameters like entity_id or model_name are missing or invalid.
    """

    # Validate required string parameters for non-emptiness
    if not entity: 
        raise custom_errors.InvalidInputError("Required parameter 'entity' cannot be empty.")
    if not model_name:
        raise custom_errors.InvalidInputError("Required parameter 'model_name' cannot be empty.")
    if not resource_group:
        raise custom_errors.InvalidInputError("Required parameter 'resource_group' cannot be empty.")
    if not subscription:
        raise custom_errors.InvalidInputError("Required parameter 'subscription' cannot be empty.")

    # Validate optional parameters if they are provided
    if auth_method is not None:
        allowed_auth_methods = [member.value for member in models.AuthMethod]
        if auth_method not in allowed_auth_methods:
            allowed_str = ", ".join([f"'{v}'" for v in allowed_auth_methods])
            raise custom_errors.InvalidInputError(
                f"Invalid 'auth_method': '{auth_method}'. Allowed values are {allowed_str}."
            )
    
    if retry_mode is not None:
        allowed_retry_modes = [retry_mode.value for retry_mode in models.RetryMode]
        if retry_mode not in allowed_retry_modes:
            allowed_str = ", ".join([f"'{v}'" for v in allowed_retry_modes])
            raise custom_errors.InvalidInputError(
                f"Invalid 'retry_mode': '{retry_mode}'. Allowed values are {allowed_str}."
            )

    # Validate numeric string parameters
    numeric_params_to_check = {
        "retry_delay": retry_delay,
        "retry_max_delay": retry_max_delay,
        "retry_max_retries": retry_max_retries,
        "retry_network_timeout": retry_network_timeout,
    }

    for param_name, param_value in numeric_params_to_check.items():
        if param_value is not None:
            if not param_value.isdigit(): 
                raise custom_errors.InvalidInputError(f"Parameter '{param_name}' ('{param_value}') must be a string representing a non-negative integer.")
            
    entity_health_info = utils.find_monitor_health_entity(
        subscription_id=subscription,
        resource_group_name=resource_group,
        model_name=model_name,
        entity_id=entity
    )

    if not entity_health_info:
        raise custom_errors.ResourceNotFoundError("The specified Azure resource was not found.")
    
    health_state_entity = models.HealthStateEntity(**entity_health_info)
    return health_state_entity.model_dump()