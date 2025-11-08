"""
Error Manager for the framework feature system.

This module provides centralized error handling configuration management
that integrates with the framework feature system.
"""

from typing import Dict, Any
from .print_log import print_log
from .error_handling import (
    get_package_error_mode, 
    set_package_error_mode, 
    reset_package_error_mode,
    temporary_error_mode,
    VALID_ERROR_MODES
)

class ErrorManager:
    """
    Manages error handling configuration for the framework.
    
    This manager handles:
    - Global error mode configuration (raise/error_dict)
    - Service-specific error mode overrides
    - Error reporting configuration
    - Error simulation settings
    """
    
    _instance = None
    _is_active = False
    _original_error_mode = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.global_config = {}
            self.service_configs = {}
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance."""
        return cls()
    
    def get_error_mode(self, service_name: str = None):
        """
        Get the current error mode.
        
        Checks for a service-specific override, then falls back to the global mode.
        
        Args:
            service_name: Name of the service to get the error mode for. If None, returns the global error mode.
        """
        if service_name and service_name in self.service_configs:
            service_config = self.service_configs[service_name]
            if "error_mode" in service_config:
                return service_config["error_mode"]
        
        # Fallback to the global error mode
        return get_package_error_mode()
    
    def set_error_mode(self, mode: str):
        """
        Set global error mode override.
        
        Args:
            mode: Error mode to set ("raise" or "error_dict")
        """
        set_package_error_mode(mode)
        print_log(f"ErrorManager: Set global error mode to: {mode}")
    
    def reset_error_mode(self):
        """Reset error mode to use environment variable."""
        reset_package_error_mode()
        print_log("ErrorManager: Reset error mode to environment variable")
    
    @property
    def temporary_error_mode(self):
        """
        Access to the temporary_error_mode context manager from error_handling.
        
        Usage:
            with error_manager.temporary_error_mode("raise"):
                # code here uses raise mode
                pass
        """
        return temporary_error_mode
    
    @classmethod
    def apply_config(cls, config: Dict[str, Any]):
        """
        Apply error handling configuration.
        
        Args:
            config: Configuration dictionary with global and service-specific settings
        """
        # Get or create the singleton instance
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        
        instance = cls._instance
        
        if instance._is_active:
            print_log("Warning: Error configuration is already active. Rollback before applying a new one.")
            return
        
        # Store original state for rollback
        instance._original_error_mode = get_package_error_mode()
        
        # Apply global configuration
        global_config = config.get("global", {})
        if global_config:
            instance._apply_global_config(global_config)
        
        # Apply service-specific configurations
        services_config = config.get("services", {})
        if services_config:
            instance._apply_service_configs(services_config)
        
        instance.global_config = global_config
        instance._is_active = True
        
        print_log(f"✅ Error configuration applied. Global mode: {get_package_error_mode()}")
    
    @classmethod
    def apply_meta_config(cls, config: Dict[str, Any], services: list = None):
        """
        Apply error handling configuration (meta interface for framework feature system).
        
        Args:
            config: Configuration dictionary with global and service-specific settings
            services: List of available services (unused in error manager, kept for interface compatibility)
        """
        cls.apply_config(config)
    
    @classmethod
    def revert_meta_config(cls):
        """
        Revert error handling configuration (meta interface for framework feature system).
        """
        cls.rollback_config()
    
    def _apply_global_config(self, global_config: Dict[str, Any]):
        """Apply global error handling configuration."""
        # Set error mode
        if "error_mode" in global_config:
            mode = global_config["error_mode"]
            if mode in VALID_ERROR_MODES:
                set_package_error_mode(mode)
                print_log(f"Set global error mode to: {mode}")
    
    def _apply_service_configs(self, services_config: Dict[str, Any]):
        """Apply service-specific error configurations."""
        for service_name, service_config in services_config.items():
            # Validate service configuration
            if not isinstance(service_config, dict):
                print_log(f"Warning: Invalid service config for {service_name}, skipping")
                continue
            
            # Validate error_mode if present
            if "error_mode" in service_config:
                mode = service_config["error_mode"]
                if mode not in VALID_ERROR_MODES:
                    print_log(f"Warning: Invalid error_mode '{mode}' for service {service_name}, skipping")
                    continue
            
            # Store the validated configuration
            self.service_configs[service_name] = service_config.copy()
            print_log(f"Configured error handling for service: {service_name}")
    
    @classmethod
    def rollback_config(cls):
        """Rollback error handling configuration to original state."""
        # Get or create the singleton instance
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        
        instance = cls._instance
        
        if not instance._is_active:
            return
        
        # Restore original error mode
        if instance._original_error_mode:
            set_package_error_mode(instance._original_error_mode)
        
        # Clear stored configurations
        instance.global_config = {}
        instance.service_configs = {}
        instance._is_active = False
        
        print_log("✅ Error configuration rolled back")


# Initialize the global error_manager
error_manager = None

def get_error_manager():
    """Get the current error manager instance."""
    global error_manager
    if error_manager is None:
        error_manager = ErrorManager()
    return error_manager

# Initialize the global instance
error_manager = ErrorManager()
