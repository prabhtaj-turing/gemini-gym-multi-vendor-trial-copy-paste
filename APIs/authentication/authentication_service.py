"""
Authentication Service - Runtime Authentication Functions

This module provides the core runtime authentication functionality.
It integrates with the authentication_manager in common_utils for configuration.
"""

from common_utils.tool_spec_decorator import tool_spec
import functools
from typing import Callable

# Import from the authentication manager in common_utils (framework integration)
from common_utils.authentication_manager import get_auth_manager

# Import database and errors from this service's SimulationEngine
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import ValidationError, AuthenticationError


@tool_spec(
    spec={
        'name': 'authenticate_service',
        'description': 'Authenticate a service by setting its authentication status to True.',
        'parameters': {
            'type': 'object',
            'properties': {
                'service_name': {
                    'type': 'string',
                    'description': 'The name of the service to authenticate'
                }
            },
            'required': [
                'service_name'
            ]
        }
    }
)
def authenticate_service(service_name: str) -> dict:
    """
    Authenticate a service by setting its authentication status to True.
    
    Args:
        service_name (str): The name of the service to authenticate
        
    Returns:
        dict: A dictionary containing the result of the authentication
        
    Raises:
        ValidationError: If the service_name is invalid
        AuthenticationError: If the service cannot be authenticated
    """
    # Validate input
    if not service_name or not isinstance(service_name, str):
        raise ValidationError("Service name must be a non-empty string")
    
    # Get authentication manager from common_utils (framework integration)
    auth_manager = get_auth_manager()
    
    # Ensure service exists in DB (for service metadata)
    services = DB.get("services", {})
    if service_name not in services:
        raise AuthenticationError(f"Service '{service_name}' not found")
    
    # Set authentication status in framework config
    success = auth_manager.set_service_authenticated(service_name, True)
    if not success:
        raise AuthenticationError(f"Failed to authenticate service '{service_name}'")
    
    return {
        "service": service_name,
        "authenticated": True,
        "message": f"Service '{service_name}' authenticated successfully"
    }


@tool_spec(
    spec={
        'name': 'deauthenticate_service',
        'description': 'Deauthenticate a service by setting its authentication status to False.',
        'parameters': {
            'type': 'object',
            'properties': {
                'service_name': {
                    'type': 'string',
                    'description': 'The name of the service to deauthenticate'
                }
            },
            'required': [
                'service_name'
            ]
        }
    }
)
def deauthenticate_service(service_name: str) -> dict:
    """
    Deauthenticate a service by setting its authentication status to False.
    
    Args:
        service_name (str): The name of the service to deauthenticate
        
    Returns:
        dict: A dictionary containing the result of the deauthentication
        
    Raises:
        ValidationError: If the service_name is invalid
    """
    # Validate input
    if not service_name or not isinstance(service_name, str):
        raise ValidationError("Service name must be a non-empty string")
    
    # Get authentication manager from common_utils (framework integration)
    auth_manager = get_auth_manager()
    
    # Set authentication status in framework config
    success = auth_manager.set_service_authenticated(service_name, False)
    if not success:
        # Still return success even if save failed, as the in-memory state is updated
        pass
    
    return {
        "service": service_name,
        "authenticated": False,
        "message": f"Service '{service_name}' deauthenticated successfully"
    }


@tool_spec(
    spec={
        'name': 'is_service_authenticated',
        'description': """ Checks if a service is authenticated and returns a simple boolean result.
        
        This function checks the runtime authentication state from the framework config.
        It uses the authentication manager to determine if authentication is required. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'service_name': {
                    'type': 'string',
                    'description': """ The name of the service to check. Can be any string,
                    including names of services that don't exist in the system. """
                }
            },
            'required': [
                'service_name'
            ]
        }
    }
)
def is_service_authenticated(service_name: str) -> bool:
    """
    Checks if a service is authenticated and returns a simple boolean result.
    
    This function checks the runtime authentication state from the framework config.
    It uses the authentication manager to determine if authentication is required.
    
    Args:
        service_name (str): The name of the service to check. Can be any string,
            including names of services that don't exist in the system.
        
    Returns:
        bool: True if the service exists and is authenticated (or doesn't need auth), 
              False if authentication is required but not provided.
    """
    # Get authentication manager from common_utils (framework integration)
    auth_manager = get_auth_manager()
    
    # Check if service exists in main DB (for service metadata)
    services = DB.get("services", {})
    if service_name not in services:
        return False
    
    # If authentication is not required for this service, return True
    if not auth_manager.get_auth_enabled(service_name):
        return True
    
    # Check actual authentication status from framework config
    return auth_manager.is_service_authenticated(service_name)


@tool_spec(
    spec={
        'name': 'list_authenticated_services',
        'description': 'List all authenticated services.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_authenticated_services() -> dict:
    """
    List all authenticated services.
    
    Returns:
        dict: A dictionary containing the list of authenticated services
    """
    # Get authentication manager from common_utils (framework integration)
    auth_manager = get_auth_manager()
    
    authenticated_services = []
    
    # Check all services in the auth config
    for service_name, config in auth_manager.service_configs.items():
        if config.get("is_authenticated", False):
            authenticated_services.append(service_name)
    
    return {
        "authenticated_services": authenticated_services,
        "count": len(authenticated_services)
    }


@tool_spec(
    spec={
        'name': 'reset_all_authentication',
        'description': 'Reset authentication status for all services.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def reset_all_authentication() -> dict:
    """
    Reset authentication status for all services.
    
    Returns:
        dict: A dictionary containing the result of the reset operation
    """
    # Get authentication manager from common_utils (framework integration)
    auth_manager = get_auth_manager()
    
    # Reset all authentication in framework config
    success = auth_manager.reset_all_authentication()
    
    return {
        "message": "All services have been deauthenticated",
        "success": success
    }


@tool_spec(
    spec={
        'name': 'create_authenticated_function',
        'description': """ Creates an authenticated version of a function that checks authentication before execution.
        
        This function wraps an existing function with authentication checking logic.
        The wrapped function will only execute if the specified service is authenticated,
        otherwise it raises an AuthenticationError with a helpful message. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'func': {
                    'type': 'object',
                    'description': 'The function to wrap with authentication checking.',
                    'properties': {},
                    'required': []
                },
                'service_name': {
                    'type': 'string',
                    'description': 'The name of the service that needs to be authenticated.'
                }
            },
            'required': [
                'func',
                'service_name'
            ]
        }
    }
)
def create_authenticated_function(func: Callable, service_name: str) -> Callable:
    """
    Creates an authenticated version of a function that checks authentication before execution.
    
    This function wraps an existing function with authentication checking logic.
    The wrapped function will only execute if the specified service is authenticated,
    otherwise it raises an AuthenticationError with a helpful message.
    
    Args:
        func (Callable): The function to wrap with authentication checking.
        service_name (str): The name of the service that needs to be authenticated.
        
    Returns:
        Callable: A new function that checks authentication before execution.
        
    Raises:
        AuthenticationError: If the service is not authenticated when called.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_service_authenticated(service_name):
            raise AuthenticationError(
                f"Service '{service_name}' is not authenticated. "
                f"Please authenticate using authenticate_service('{service_name}') before using this API."
            )
        return func(*args, **kwargs)
    return wrapper