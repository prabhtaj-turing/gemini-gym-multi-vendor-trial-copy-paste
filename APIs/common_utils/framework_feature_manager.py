"""
Generic Meta Framework for configuring and managing API utilities via flexible JSON path-to-consumer mappings.
"""

import os
import json
from .print_log import print_log
from .models import FrameworkFeatureConfig  # Import the config model for validation
from .search_engine.engine import search_engine_manager

class FrameworkFeatureManager:
    """
    A flexible framework configuration manager that applies and rolls back configuration
    by mapping JSON field paths to consumer and rollback functions.

    Usage:
        manager = FrameworkFeatureManager(
            config_path="path/to/config.json",
            config_path_action_map={
                "mutation": {
                    "apply": MutationManager.apply_config,
                    "rollback": MutationManager.rollback_config,
                },
                "error": {
                    "apply": ErrorManager.apply_config,
                    "rollback": ErrorManager.rollback_config,
                },
                "some.deep.setting": {
                    "apply": some_function,
                    "rollback": some_rollback_function,
                },
            }
        )
        manager.apply_config()
        manager.rollback_config()
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(FrameworkFeatureManager, cls).__new__(cls)
        return cls.instance

    def __init__(self, config_path_action_map: dict):
        """
        :param config_path: Path to the JSON config file.
        :param config_path_action_map: Dict mapping JSON field paths (dot-separated) to dicts with 'apply' and 'rollback' callables.
                         Each 'apply' function should accept (config_value).
                         Each 'rollback' function should accept no arguments.
        """
        self.config_path = ""
        self.config_path_action_map = config_path_action_map
        self._is_active = False
        self._applied_paths = []

        # Validate that all 'apply' and 'rollback' fields are callables (if present)
        for path, funcs in self.config_path_action_map.items():
            if "apply" in funcs and not callable(funcs["apply"]):
                raise TypeError(f"Mapping for '{path}' has non-callable 'apply': {funcs['apply']!r}")
            if "rollback" in funcs and not callable(funcs["rollback"]):
                raise TypeError(f"Mapping for '{path}' has non-callable 'rollback': {funcs['rollback']!r}")

        # Validate config at initialization using class utility
        #self._load_and_validate_config(self.config_path)

    @classmethod
    def _load_and_validate_config(cls, config_path: str) -> dict:
        """
        Utility to check file existence, load JSON, and validate with FrameworkFeatureConfig.
        Returns the loaded config dict if valid, else raises.
        """

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, "r") as f:
            config = json.load(f)
        try:
            FrameworkFeatureConfig.model_validate(config)
        except Exception as e:
            raise ValueError(f"Framework config validation failed: {e}")
        return config

    def set_config_path(self, config_path: str):
        # Use class utility for file existence and validation
        self._load_and_validate_config(config_path)
        self.config_path = config_path

    def apply_config(self, config = None):
        """
        Loads the config file and applies configuration using the mapped consumer functions.
        Validates the config using FrameworkFeatureConfig before applying.
        """
        if self._is_active:
            print_log("Warning: A configuration is already active. Rollback before applying a new one.")
            return
        if not self.config_path and not config:
            print_log("Error: config_path not set and no config object is passed, please set it using set_config_path function or pass a config object")

        # Use class utility for file existence and validation
        if not config: 
            config = self._load_and_validate_config(self.config_path)
        try:
            FrameworkFeatureConfig.model_validate(config)
        except Exception as e:
            raise ValueError(f"Framework config validation failed: {e}")

        self._applied_paths.clear()
        for path, funcs in self.config_path_action_map.items():
            apply_fn = funcs.get("apply")
            if not callable(apply_fn):
                raise TypeError(f"Mapping for '{path}' does not have a callable 'apply' function.")
            value = self._get_by_path(config, path)
            if value is not None:
                apply_fn(value)
                self._applied_paths.append(path)

        # Reapply authentication decorators after all configurations are applied
        # This ensures that authentication decorators are applied when the auth manager is fully configured
        if "authentication" in self._applied_paths:
            from .authentication_manager import AuthenticationManager
            AuthenticationManager.reapply_decorators()

        self._is_active = True

    def rollback_config(self):
        """
        Calls rollback functions for all applied configs, in reverse order.
        """
        if not self._is_active:
            return

        for path in reversed(self._applied_paths):
            funcs = self.config_path_action_map.get(path, {})
            rollback_fn = funcs.get("rollback")
            if rollback_fn is not None and not callable(rollback_fn):
                raise TypeError(f"Mapping for '{path}' does not have a callable 'rollback' function.")
            if callable(rollback_fn):
                rollback_fn()
        self._applied_paths.clear()
        self._is_active = False

    @staticmethod
    def _get_by_path(config: dict, path: str):
        """
        Retrieves a value from a nested dict using a dot-separated path.
        """
        keys = path.split(".")
        val = config
        for key in keys:
            if isinstance(val, dict) and key in val:
                val = val[key]
            else:
                return None
        return val

# Example: Provide a global instance with default mutation manager mapping
from .mutation_manager import MutationManager
from .authentication_manager import AuthenticationManager
from .error_simulation_manager import ErrorSimulationManager
from .error_manager import ErrorManager
from .search_engine.engine import search_engine_manager

framework_feature_manager = FrameworkFeatureManager(
    config_path_action_map={
        "authentication": {
            "apply": AuthenticationManager.apply_config,
            "rollback": AuthenticationManager.rollback_config,
        },
        "mutation": {
            "apply": MutationManager.apply_config,
            "rollback": MutationManager.rollback_config,
        },
        "search_engine": {
            "apply": search_engine_manager.apply_config,
            "rollback": search_engine_manager.rollback_config,
        },
        "error": {
            "apply": ErrorSimulationManager.apply_config,
            "rollback": ErrorSimulationManager.rollback_config,
        },
        "error_mode": {
            "apply": ErrorManager.apply_config,
            "rollback": ErrorManager.rollback_config,
        },
    }
)