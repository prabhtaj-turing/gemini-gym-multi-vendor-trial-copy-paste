"""
Error simulation configuration management utilities for API modules.

This module provides utilities for managing central error simulation configuration 
across all API modules. It includes functions for applying and rolling back 
central error simulation configurations to existing error simulators.
"""

import sys
import json
import os
from typing import Dict, Optional, Union, Any

# --- Pydantic Validation ---
from .models import CentralConfig
from common_utils.ErrorSimulation import ErrorSimulator

class ErrorSimulationManager:
    """
    Manages error simulation configuration for the framework feature.
    Handles applying and rolling back error simulation configurations.
    """
    
    # Class-level state tracking
    _is_active = False
    _applied_config: Optional[Dict] = None
    _APPLY_CENTRAL_CONFIG = False
    _central_config_cache: Optional[Dict] = None

    @staticmethod
    def _get_central_config(config_path: Optional[str] = None) -> Optional[Dict]:
        """
        Loads and validates the central configuration file.
        """
        if config_path is None:
            config_path = os.environ.get("FRAMEWORK_CONFIG_PATH", "default_framework_config.json")

        if not os.path.exists(config_path):
            return None

        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            CentralConfig.model_validate(config_data)
            return config_data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Could not parse or validate config file at '{config_path}': {e}")
            return None

    @classmethod
    def apply_config(cls, config: Dict[str, Any]) -> bool:
        """
        Applies an error simulation configuration globally.
        This method assumes it always receives the 'error' slice of the configuration.
        """
        if not isinstance(config, dict):
            print(f"Error: apply_config expects a dictionary, but received {type(config)}")
            return False

        cls._APPLY_CENTRAL_CONFIG = True
        
        # The received config is the slice, so we wrap it to create the full
        # structure expected by other parts of the system (e.g., ErrorSimulator).
        config_to_apply = {"error": config}

        cls._central_config_cache = config_to_apply
        print(f"Central error config cache has been set.")

        print("Scanning for already-loaded simulators to update...")
        # The `config` parameter is the error slice, which contains the "services" key.
        service_configs = config.get("services", {})
        if not isinstance(service_configs, dict):
            print(f"Warning: 'services' key in error config is not a dictionary. Skipping updates.")
            service_configs = {}

        for module in list(sys.modules.values()):
            if hasattr(module, 'error_simulator') and isinstance(getattr(module, 'error_simulator'), ErrorSimulator):
                simulator = getattr(module, 'error_simulator')
                service_name = getattr(simulator, 'service_name', None)

                if service_name and service_name in service_configs:
                    print(f"  - Updating already-loaded simulator for '{service_name}'...")
                    # Pass the full wrapped config to the simulator
                    simulator.load_central_config(central_config=cls._central_config_cache, service_name=service_name)
        
        cls._is_active = True
        cls._applied_config = config # Store the raw slice
        print("✅ Error simulation configuration applied successfully")
        return True

    @classmethod
    def rollback_config(cls) -> bool:
        """
        Rolls back the global error simulation configuration.
        """
        if not cls._is_active:
            return True
            
        print("Rolling back central error configuration...")
        cls._central_config_cache = None
        cls._APPLY_CENTRAL_CONFIG = False

        for module in list(sys.modules.values()):
            if hasattr(module, 'error_simulator') and isinstance(getattr(module, 'error_simulator'), ErrorSimulator):
                simulator = getattr(module, 'error_simulator')
                print(f"  - Reverting simulator for '{getattr(simulator, 'service_name', 'unknown_service')}'...")
                simulator.reload_initial_config()
        
        cls._is_active = False
        cls._applied_config = None
        print("Rollback complete.")
        return True

    @classmethod
    def get_active_central_config(cls) -> Optional[Dict]:
        """Returns the currently active (cached) central error configuration."""
        return cls._central_config_cache

    @classmethod
    def should_apply_central_config(cls) -> bool:
        """Check if a central configuration is available."""
        return cls._APPLY_CENTRAL_CONFIG

    @classmethod
    def apply_central_config_to_simulator(cls, error_simulator: ErrorSimulator, service_name: str):
        """Applies the active central config to a specific error simulator instance."""
        active_config = cls.get_active_central_config()
        
        if active_config:
            print(f"Applying central config (from cache) to '{service_name}'...")
            error_simulator.load_central_config(central_config=active_config, service_name=service_name)
        else:
            print(f"Info: No active central error configuration to apply to '{service_name}'.")

    # --- Methods for old FrameworkFeature compatibility ---
    @classmethod
    def apply_meta_config(cls, config: Dict[str, Any], services: list[str] = None):
        cls.apply_config(config)
    
    @classmethod
    def revert_meta_config(cls):
        cls.rollback_config()

# --- Backward Compatibility Shims ---
# These functions delegate to the manager class to support old code.

def get_central_config(config_path: Optional[str] = None) -> Optional[Dict]:
    return ErrorSimulationManager._get_central_config(config_path)

def apply_config(config: Union[str, Dict]) -> bool:
    # This shim maintains the old signature, but the underlying manager
    # now strictly expects a dictionary (the error slice).
    if isinstance(config, str):
        # To maintain compatibility, we can load the file and get the error slice.
        full_config = ErrorSimulationManager._get_central_config(config)
        error_slice = full_config.get("error") if full_config else None
        if error_slice is None:
            return False
        return ErrorSimulationManager.apply_config(error_slice)
    
    # If it's a dict, we assume it's the slice as per the new design.
    # However, old code might pass the full dict. We can check for the 'error' key
    # to provide one last layer of compatibility.
    if isinstance(config, dict) and "error" in config and len(config) == 1:
        return ErrorSimulationManager.apply_config(config['error'])
        
    return ErrorSimulationManager.apply_config(config)


def rollback_config() -> bool:
    return ErrorSimulationManager.rollback_config()

def get_active_central_config() -> Optional[Dict]:
    return ErrorSimulationManager.get_active_central_config()

def should_apply_central_config() -> bool:
    return ErrorSimulationManager.should_apply_central_config()

def apply_central_config_to_simulator(error_simulator: ErrorSimulator, service_name: str):
    ErrorSimulationManager.apply_central_config_to_simulator(error_simulator, service_name)

# Global instance for backward compatibility
error_simulation_manager = ErrorSimulationManager()
