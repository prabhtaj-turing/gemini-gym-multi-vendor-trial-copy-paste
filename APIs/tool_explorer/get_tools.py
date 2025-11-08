"""
Tool Explorer Service Implementation

This service provides functionality to explore and discover available tools
across different services in the project.
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Any

from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import (
    ValidationError,
    ServiceNotFoundError,
    ToolNotFoundError,
)


@tool_spec(
    spec={
        'name': 'list_services',
        'description': 'Lists all available services in the project.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_services() -> List[str]:
    """
    Lists all available services in the project.

    Returns:
        List[str]: A list of service names.
    """
    if "services" not in DB or not DB["services"]:
        return []
    return list(DB["services"].keys())


@tool_spec(
    spec={
        'name': 'list_tools',
        'description': 'Lists all available tools for a given service.',
        'parameters': {
            'type': 'object',
            'properties': {
                'service_name': {
                    'type': 'string',
                    'description': 'The name of the service.'
                }
            },
            'required': [
                'service_name'
            ]
        }
    }
)
def list_tools(service_name: str) -> List[str]:
    """
    Lists all available tools for a given service.

    Args:
        service_name (str): The name of the service.

    Returns:
        List[str]: A list of tool names for the specified service.
        
    Raises:
        ValidationError: If the service_name is not a string or is empty.
        ServiceNotFoundError: If the service is not found.
    """
    if not isinstance(service_name, str) or not service_name:
        raise ValidationError("Service name must be a non-empty string.")
    if service_name not in DB.get("services", {}):
        raise ServiceNotFoundError(f"Service '{service_name}' not found.")
    return list(DB["services"][service_name].keys())


@tool_spec(
    spec={
        'name': 'fetch_documentation',
        'description': 'Fetches the full FCSpec documentation for a specific tool.',
        'parameters': {
            'type': 'object',
            'properties': {
                'service_name': {
                    'type': 'string',
                    'description': 'The name of the service.'
                },
                'tool_name': {
                    'type': 'string',
                    'description': 'The name of the tool.'
                }
            },
            'required': [
                'service_name',
                'tool_name'
            ]
        }
    }
)
def fetch_documentation(service_name: str, tool_name: str) -> Dict[str, Any]:
    """
    Fetches the full FCSpec documentation for a specific tool.

    Args:
        service_name (str): The name of the service.
        tool_name (str): The name of the tool.

    Returns:
        Dict[str, Any]: A dictionary representing the tool's full FCSpec with the following structure:
        - name (str): The name of the function, matching the `tool_name`.
        - description (str): A detailed, multi-line description of what the function does, 
          its purpose, and any important notes.
        - parameters (Dict[str, Any]): An object describing the function's parameters, conforming 
          to the JSON Schema specification. It contains:
            - type (str): The type of the container for the parameters, which is always "object".
            - properties (Dict[str, Dict[str, Any]]): A dictionary where each key is a parameter 
              name. The value is another dictionary describing that specific parameter, which includes:
                - type (str): The JSON schema type of the parameter (e.g., "string", "integer", "boolean", "array", "object").
                - description (str): A detailed explanation of the parameter, what it's used for, 
                  and any constraints or default values.
                - items (Dict[str, Any], optional): If the parameter `type` is "array", this object 
                  describes the type of items contained within the array.
                - properties (Dict[str, Any], optional): If the parameter `type` is "object", this 
                  describes the nested properties of that object.
                - required (List[str], optional): If the parameter `type` is "object", this lists 
                  any nested properties that are required.
            - required (List[str], optional): A list of strings, where each string is the name of a 
              parameter that is mandatory for the function call. This key is omitted if no parameters are required.
        
    Raises:
        ValidationError: If service_name or tool_name are invalid.
        ServiceNotFoundError: If the service is not found.
        ToolNotFoundError: If the tool is not found.
    """
    if not isinstance(service_name, str) or not service_name:
        raise ValidationError("Service name must be a non-empty string.")
    if not isinstance(tool_name, str) or not tool_name:
        raise ValidationError("Tool name must be a non-empty string.")

    service = DB.get("services", {}).get(service_name)
    if not service:
        raise ServiceNotFoundError(f"Service '{service_name}' not found.")

    tool = service.get(tool_name)
    if not tool:
        raise ToolNotFoundError(f"Tool '{tool_name}' not found in service '{service_name}'.")

    return tool