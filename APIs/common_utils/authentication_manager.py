"""
Framework Feature Manager for Authentication.

This manager completely replaces the old auth_configs.json system with the new 
centralized default_framework_config.json approach. It provides the same authentication
functionality but integrates with the meta-framework.
"""
import os
import json
import copy
from typing import Dict, List, Optional
from pathlib import Path
from .utils import discover_services


class AuthenticationManager:
    """
    Central authentication orchestrator that manages authentication configuration
    and runtime state for all services through the meta-framework.
    """
    
    def __init__(self):
        """Initialize authentication manager with state tracking."""
        # Service configurations - will be populated by apply_config
        self.service_configs = {}
        
        # State tracking for proper rollback
        self._previous_config: Optional[dict] = None
        self._current_config: Optional[dict] = None
        
        # Initialize with default values
        self._reset_to_defaults()
    
    def _reset_to_defaults(self):
        """Reset to default authentication configuration."""
        # Read environment variable at reset time
        self.AUTH_ENFORCEMENT = os.getenv("AUTH_ENFORCEMENT", "FALSE").upper()
        self.global_auth_enabled = (self.AUTH_ENFORCEMENT == "TRUE")
        
        # Clear service configs (will be repopulated by framework)
        self.service_configs = {}
        
    # --- Framework Feature Manager Interface ---
    
    @classmethod 
    def apply_meta_config(cls, config: dict, services: list[str]):
        """
        Applies authentication configuration from the meta-framework.
        This completely replaces the old auth_configs.json system.
        
        Args:
            config: The authentication section of the framework config
            services: List of discovered services from the framework
        """
        # Get or create the singleton instance
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        
        instance = cls._instance
        
        # Also update the global auth_manager instance
        global auth_manager
        auth_manager = instance
        
        # Apply global and service-specific overrides
        global_config = config.get("global", {})
        service_configs = config.get("services", {})
        
        # Reset service configs
        instance.service_configs = {}
        
        for service_name in services:
            # Start with default settings
            service_auth_settings = {
                "authentication_enabled": False,
                "excluded_functions": [],
                "is_authenticated": False
            }
            
            # Apply global config first
            if 'authentication_enabled' in global_config:
                service_auth_settings['authentication_enabled'] = global_config['authentication_enabled']
            if 'excluded_functions' in global_config:
                service_auth_settings['excluded_functions'] = global_config['excluded_functions'].copy()
            
            # Override with service-specific config
            service_override = service_configs.get(service_name, {})
            if 'authentication_enabled' in service_override:
                service_auth_settings['authentication_enabled'] = service_override['authentication_enabled']
            if 'excluded_functions' in service_override:
                service_auth_settings['excluded_functions'] = service_override['excluded_functions'].copy()
            
            instance.service_configs[service_name] = service_auth_settings
    
    @classmethod
    def revert_meta_config(cls):
        """
        Reverts the authentication configuration to default state.
        """
        if hasattr(cls, '_instance'):
            cls._instance.service_configs = {}
    
    @classmethod
    def apply_config(cls, config: dict):
        """
        Framework integration method - applies authentication config from framework.
        This method is called by the FrameworkFeatureManager.
        """
        # Get or create the singleton instance
        instance = cls.get_instance()
        
        # Save the current config for rollback
        if instance._current_config is not None:
            instance._previous_config = copy.deepcopy(instance._current_config)
        else:
            # Build the previous config from the original config state (before applying new config)
            # This ensures rollback restores the original configuration, not runtime state
            instance._previous_config = {
                "global": {"authentication_enabled": instance.global_auth_enabled},
                "services": {
                    service_name: {
                        "authentication_enabled": config.get("services", {}).get(service_name, {}).get("authentication_enabled", False),
                        "excluded_functions": config.get("services", {}).get(service_name, {}).get("excluded_functions", []),
                        "is_authenticated": config.get("services", {}).get(service_name, {}).get("is_authenticated", False)
                    }
                    for service_name in discover_services()
                    if service_name in config.get("services", {})
                }
            }
        
        # Save the new config as current
        instance._current_config = copy.deepcopy(config)
        
        # Apply the new configuration
        instance._apply_config_internal(config)
        
        # Update the global auth_manager reference
        global auth_manager
        auth_manager = instance
        
        print(f"✅ AuthenticationManager.apply_config completed - {len(instance.service_configs)} services configured")
    
    def _apply_config_internal(self, config: dict):
        """
        Internal method to apply configuration
        """
        # Get services internally
        services = discover_services()
        
        # Apply global configuration - always check environment variable at config time
        global_config = config.get("global", {})
        env_auth_enabled = os.environ.get("AUTH_ENFORCEMENT", "FALSE").upper() == "TRUE"
        config_auth_enabled = global_config.get("authentication_enabled", False)
        
        # Environment variable overrides config file
        self.global_auth_enabled = env_auth_enabled or config_auth_enabled
        self.AUTH_ENFORCEMENT = self.global_auth_enabled
        
        # Apply service configurations
        service_configs = config.get("services", {})
        self.service_configs = {}  # Reset first
        
        for service_name in services:
            if service_name in service_configs:
                service_config = service_configs[service_name]
                self.service_configs[service_name] = {
                    "authentication_enabled": service_config.get("authentication_enabled", False),
                    "excluded_functions": service_config.get("excluded_functions", []),
                    "is_authenticated": service_config.get("is_authenticated", False)
                }
        
        # Note: Decorator reapplication is now handled by the framework manager
        # after all configurations are applied
    
    @classmethod
    def reapply_decorators(cls):
        """
        Reapply authentication decorators to already-imported modules.
        This should be called by the framework manager after all configurations are applied.
        """
        instance = cls.get_instance()
        # Get all configured services
        services = list(instance.service_configs.keys())
        instance._reapply_decorators_to_imported_modules(services)
    
    @classmethod
    def rollback_config(cls):
        """
        Framework integration method - rollback authentication config.
        This method is called by the FrameworkFeatureManager.
        """
        # Get the singleton instance
        instance = cls.get_instance()
        
        if instance._previous_config is not None:
            # Restore previous config
            rollback_config = instance._previous_config
            instance._current_config = instance._previous_config
            instance._previous_config = None
            
            # Apply the rollback config
            instance._apply_config_internal(rollback_config)
        else:
            # If no previous config, reset to defaults
            instance._current_config = None
            instance._reset_to_defaults()
        
        # Update the global auth_manager reference
        global auth_manager
        auth_manager = instance
        
        print("✅ AuthenticationManager.rollback_config completed")
    
    # --- Backward-compatible methods for direct usage (not through framework) ---
    
    @classmethod
    def apply_config_direct(cls, config: dict):
        """
        Direct usage method - for backward compatibility when not using framework.
        """
        services = discover_services()
        cls.apply_meta_config(config, services)
    
    @classmethod
    def rollback_config_direct(cls):
        """
        Direct usage method - for backward compatibility when not using framework.
        """
        cls.revert_meta_config()
    
    # --- Runtime Authentication Methods (replaces old auth_manager) ---
    
    @classmethod
    def get_instance(cls):
        """Get the singleton authentication manager instance."""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance
    
    def get_auth_enabled(self, service_name: str) -> bool:
        """Check if authentication is required for a service."""
        service_config = self.service_configs.get(service_name, {})
        return service_config.get("authentication_enabled", False)
    
    def get_excluded_functions(self, service_name: str) -> List[str]:
        """Get list of functions excluded from authentication for a service."""
        service_config = self.service_configs.get(service_name, {})
        return service_config.get("excluded_functions", [])
    
    def is_service_authenticated(self, service_name: str) -> bool:
        """Check service authentication status."""
        service_config = self.service_configs.get(service_name, {})
        return service_config.get("is_authenticated", False)
    
    def set_service_authenticated(self, service_name: str, authenticated: bool) -> bool:
        """Set service authentication status."""
        if service_name not in self.service_configs:
            self.service_configs[service_name] = {
                "authentication_enabled": False,
                "excluded_functions": [],
                "is_authenticated": authenticated
            }
        else:
            self.service_configs[service_name]["is_authenticated"] = authenticated
        return True
    
    def reset_all_authentication(self) -> bool:
        """Reset authentication status for all services to False."""
        for service_name in self.service_configs:
            self.service_configs[service_name]["is_authenticated"] = False
        return True
    
    def should_apply_auth(self, service_name: str, function_name: str) -> bool:
        """
        Determine if authentication should be applied to a function.
        This is the core decision logic used by the decorator system.
        """
        # 1. Check global auth (from environment variable)
        if not self.global_auth_enabled:
            return False
        
        # 2. Check service auth (from framework config)
        if not self.get_auth_enabled(service_name):
            return False
        
        # 3. Check function exclusions (from framework config)
        excluded_functions = self.get_excluded_functions(service_name)
        if function_name in excluded_functions:
            return False
        
        # 4. Apply authentication
        return True
    
    def get_config_summary(self) -> Dict:
        """Get summary of current authentication configuration for debugging."""
        return {
            "global_auth_enabled": self.global_auth_enabled,
            "auth_enforcement_env": self.AUTH_ENFORCEMENT,
            "services_count": len(self.service_configs),
            "services": {
                name: {
                    "auth_enabled": config.get("authentication_enabled", False),
                    "excluded_count": len(config.get("excluded_functions", [])),
                    "is_authenticated": config.get("is_authenticated", False)
                }
                for name, config in self.service_configs.items()
            }
        }
    
    def _reapply_decorators_to_imported_modules(self, services: list[str]):
        """
        Reapplies authentication decorators to already-imported service modules.
        This fixes the issue where changing authentication config doesn't affect 
        already-imported functions.
        """
        import sys
        import importlib
        
        for service_name in services:
            # Check if the service module is already imported
            if service_name in sys.modules:
                try:
                    service_module = sys.modules[service_name]
                    
                    # Get the original function map to know which functions to redecorate
                    if hasattr(service_module, '_function_map'):
                        function_map = service_module._function_map
                        
                        # Import necessary decorating functions
                        from .init_utils import apply_decorators
                        
                        # Get error simulator if available
                        error_simulator = getattr(service_module, 'error_simulator', None)
                        
                        # Only proceed if we have an error simulator
                        if error_simulator:
                            # Reapply decorators to each function
                            for func_name, fqn in function_map.items():
                                if hasattr(service_module, func_name):
                                    # Get the current function (might be decorated or not)
                                    current_func = getattr(service_module, func_name)
                                    
                                    # Try to get the original undecorated function
                                    original_func = getattr(current_func, '__wrapped__', current_func)
                                    
                                    # Apply fresh decorators
                                    decorated_func = apply_decorators(
                                        original_func=original_func,
                                        service_name=service_name,
                                        function_name=func_name,
                                        fully_qualified_name=fqn,
                                        error_simulator=error_simulator
                                    )
                                    
                                    # Replace the function on the module
                                    setattr(service_module, func_name, decorated_func)
                except Exception as e:
                    # If redecorating fails for any service, continue with others
                    pass


# Initialize the global auth_manager
auth_manager = None

def get_auth_manager():
    """Get the current authentication manager instance."""
    global auth_manager
    if auth_manager is None:
        auth_manager = AuthenticationManager()
    return auth_manager

# Initialize the global instance
auth_manager = AuthenticationManager()