"""
FCCheckersManager - Configuration manager for function validation.

This module provides a centralized manager for controlling validation behavior
across different services and functions. It supports:
- Global enable/disable of validation
- Control over whether validation errors raise exceptions
- Per-service validation configuration
- Per-function validation configuration
- Custom CSV logging paths
- Singleton pattern for consistent configuration
"""

import os
from typing import Dict, Optional, Tuple, Any


class FCCheckersManager:
    """
    Manages validation and logging configuration for function checkers.
    
    The manager uses a hierarchical configuration system:
    1. Global settings (apply to all services/functions)
    2. Service-level settings (override global for a specific service)
    3. Function-level settings (override service/global for a specific function)
    """
    
    DEFAULT_CSV_PATH = os.path.join("logs", "validation_errors.csv")
    
    def __init__(self):
        """Initialize the manager with default settings."""
        # Global validation flag (disabled by default)
        self._global_validation_enabled = False
        self._global_validation_overridden = False
        
        # Global logging flag
        self._global_logging_enabled = True

        # Global error raising flag
        self._global_raise_errors = True
        
        # Skip logging validation errors when function also raises (for negative tests)
        self._skip_negative_tests = True
        
        # Global CSV path (can be overridden per service/function)
        self._global_csv_path = self.DEFAULT_CSV_PATH
        
        # Service-level configuration: {service_name: {"enabled": bool, "log_to_csv": bool, "csv_path": str, "raise_errors": bool}}
        self._service_config: Dict[str, Dict[str, Any]] = {}
        
        # Function-level configuration: {(service_name, function_name): {"enabled": bool, "log_to_csv": bool, "csv_path": str, "raise_errors": bool}}
        self._function_config: Dict[Tuple[str, str], Dict[str, Any]] = {}
    
    def set_global_validation(self, enabled: bool):
        """
        Enable or disable validation globally.
        
        Args:
            enabled: True to enable validation, False to disable
        """
        self._global_validation_enabled = enabled
        self._global_validation_overridden = True
    
    def set_global_logging(self, enabled: bool, csv_path: Optional[str] = None):
        """
        Enable or disable CSV logging globally.
        
        Args:
            enabled: True to enable logging, False to disable
            csv_path: Optional custom path for the CSV file
        """
        self._global_logging_enabled = enabled
        if csv_path is not None:
            self._global_csv_path = csv_path

    def set_global_raise_errors(self, enabled: bool):
        """
        Control whether validation errors raise exceptions globally.

        Args:
            enabled: True to raise exceptions when validation fails, False to suppress
        """
        self._global_raise_errors = enabled
    
    def set_skip_negative_tests(self, skip: bool):
        """
        Control whether to skip logging validation errors when function also raises.
        
        When enabled (default), if input validation fails AND the function itself raises an error,
        the validation errors are NOT logged. This prevents clutter from negative test cases.
        
        Args:
            skip: True to skip logging for negative tests, False to always log
        """
        self._skip_negative_tests = skip
    
    def should_skip_negative_tests(self) -> bool:
        """Check if negative test validation errors should be skipped."""
        return self._skip_negative_tests
    
    def configure_service(
        self,
        service_name: str,
        enabled: Optional[bool] = None,
        log_to_csv: Optional[bool] = None,
        csv_path: Optional[str] = None,
        raise_errors: Optional[bool] = None
    ):
        """
        Configure validation settings for a specific service.
        
        Args:
            service_name: Name of the service
            enabled: Whether to enable validation for this service (None = use global)
            log_to_csv: Whether to log errors to CSV (None = use global)
            csv_path: Custom CSV path for this service (None = use global)
            raise_errors: Whether to raise validation errors (None = use global)
        """
        if service_name not in self._service_config:
            self._service_config[service_name] = {}
        
        if enabled is not None:
            self._service_config[service_name]["enabled"] = enabled
        if log_to_csv is not None:
            self._service_config[service_name]["log_to_csv"] = log_to_csv
        if csv_path is not None:
            self._service_config[service_name]["csv_path"] = csv_path
        if raise_errors is not None:
            self._service_config[service_name]["raise_errors"] = raise_errors
    
    def configure_function(
        self,
        service_name: str,
        function_name: str,
        enabled: Optional[bool] = None,
        log_to_csv: Optional[bool] = None,
        csv_path: Optional[str] = None,
        raise_errors: Optional[bool] = None
    ):
        """
        Configure validation settings for a specific function.
        
        Args:
            service_name: Name of the service
            function_name: Name of the function
            enabled: Whether to enable validation for this function (None = use service/global)
            log_to_csv: Whether to log errors to CSV (None = use service/global)
            csv_path: Custom CSV path for this function (None = use service/global)
            raise_errors: Whether to raise validation errors (None = use service/global)
        """
        key = (service_name, function_name)
        if key not in self._function_config:
            self._function_config[key] = {}
        
        if enabled is not None:
            self._function_config[key]["enabled"] = enabled
        if log_to_csv is not None:
            self._function_config[key]["log_to_csv"] = log_to_csv
        if csv_path is not None:
            self._function_config[key]["csv_path"] = csv_path
        if raise_errors is not None:
            self._function_config[key]["raise_errors"] = raise_errors
    
    def should_validate(self, service_name: str, function_name: str) -> bool:
        """
        Determine if validation should be performed for a given service/function.
        
        Priority order (highest to lowest):
        1. Function-level configuration
        2. Service-level configuration
        3. Global configuration
        
        Args:
            service_name: Name of the service
            function_name: Name of the function
        
        Returns:
            True if validation should be performed, False otherwise
        """
        # If global validation has been explicitly overridden, respect that setting for all functions
        if self._global_validation_overridden:
            return self._global_validation_enabled

        # Check function-level configuration first
        key = (service_name, function_name)
        if key in self._function_config and "enabled" in self._function_config[key]:
            return self._function_config[key]["enabled"]
        
        # Check service-level configuration
        if service_name in self._service_config and "enabled" in self._service_config[service_name]:
            return self._service_config[service_name]["enabled"]
        
        # Fall back to global configuration
        return self._global_validation_enabled
    
    def get_logging_preferences(self, service_name: str, function_name: str) -> Tuple[bool, str]:
        """
        Get logging preferences for a given service/function.
        
        Priority order (highest to lowest):
        1. Function-level configuration
        2. Service-level configuration
        3. Global configuration
        
        Args:
            service_name: Name of the service
            function_name: Name of the function
        
        Returns:
            Tuple of (log_to_csv, csv_path)
        """
        log_to_csv = self._global_logging_enabled
        csv_path = self._global_csv_path
        
        # Check service-level configuration
        if service_name in self._service_config:
            service_cfg = self._service_config[service_name]
            if "log_to_csv" in service_cfg:
                log_to_csv = service_cfg["log_to_csv"]
            if "csv_path" in service_cfg:
                csv_path = service_cfg["csv_path"]
        
        # Check function-level configuration (highest priority)
        key = (service_name, function_name)
        if key in self._function_config:
            func_cfg = self._function_config[key]
            if "log_to_csv" in func_cfg:
                log_to_csv = func_cfg["log_to_csv"]
            if "csv_path" in func_cfg:
                csv_path = func_cfg["csv_path"]
        
        return log_to_csv, csv_path

    def should_raise_errors(self, service_name: str, function_name: str) -> bool:
        """
        Determine whether validation errors should raise exceptions.

        Priority order (highest to lowest):
        1. Function-level configuration
        2. Service-level configuration
        3. Global configuration
        """

        key = (service_name, function_name)
        if key in self._function_config and "raise_errors" in self._function_config[key]:
            return self._function_config[key]["raise_errors"]

        if service_name in self._service_config and "raise_errors" in self._service_config[service_name]:
            return self._service_config[service_name]["raise_errors"]

        return self._global_raise_errors
    
    def disable_service(self, service_name: str):
        """
        Convenience method to disable validation for a specific service.
        
        Args:
            service_name: Name of the service to disable
        """
        self.configure_service(service_name, enabled=False)
    
    def enable_service(self, service_name: str):
        """
        Convenience method to enable validation for a specific service.
        
        Args:
            service_name: Name of the service to enable
        """
        self.configure_service(service_name, enabled=True)
    
    def disable_function(self, service_name: str, function_name: str):
        """
        Convenience method to disable validation for a specific function.
        
        Args:
            service_name: Name of the service
            function_name: Name of the function to disable
        """
        self.configure_function(service_name, function_name, enabled=False)
    
    def enable_function(self, service_name: str, function_name: str):
        """
        Convenience method to enable validation for a specific function.
        
        Args:
            service_name: Name of the service
            function_name: Name of the function to enable
        """
        self.configure_function(service_name, function_name, enabled=True)
    
    def reset(self):
        """Reset all configuration to defaults."""
        self._global_validation_enabled = False
        self._global_validation_overridden = False
        self._global_logging_enabled = True
        self._global_raise_errors = True
        self._global_csv_path = self.DEFAULT_CSV_PATH
        self._service_config.clear()
        self._function_config.clear()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current configuration.
        
        Returns:
            Dictionary containing the current configuration state
        """
        return {
            "global": {
                "validation_enabled": self._global_validation_enabled,
                "validation_overridden": self._global_validation_overridden,
                "logging_enabled": self._global_logging_enabled,
                "csv_path": self._global_csv_path,
                "raise_errors": self._global_raise_errors
            },
            "services": self._service_config.copy(),
            "functions": {
                f"{service}::{func}": config
                for (service, func), config in self._function_config.items()
            }
        }


# Singleton instance
_fc_checkers_manager_instance: Optional[FCCheckersManager] = None


def get_fc_checkers_manager() -> FCCheckersManager:
    """
    Get the singleton instance of FCCheckersManager.
    
    Returns:
        The global FCCheckersManager instance
    """
    global _fc_checkers_manager_instance
    if _fc_checkers_manager_instance is None:
        _fc_checkers_manager_instance = FCCheckersManager()
    return _fc_checkers_manager_instance


def reset_fc_checkers_manager():
    """
    Reset the singleton instance (useful for testing).
    Creates a fresh manager with default settings.
    """
    global _fc_checkers_manager_instance
    _fc_checkers_manager_instance = FCCheckersManager()

