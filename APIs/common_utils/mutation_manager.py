from common_utils.print_log import print_log
import os
import json
import re
import functools
from typing import Optional, Callable, Any
import sys
import importlib
import shutil
from .utils import discover_services

class MutationManager:
    _mutation_names = {}
    _original_function_maps = {}
    _schema_backup_dir = os.path.join(os.path.dirname(__file__), "..", "..", ".mutation_backups")
    _service_mutation_backup = {}

    @classmethod
    def apply_meta_config(cls, config: dict, services: list[str]):
        """
        Applies mutation configuration from the meta-framework.
        
        Args:
            config: The mutation section of the framework config
            services: List of discovered services from the framework
        """
        cls._service_mutation_backup = {}

        global_config = config.get("global", {})
        service_configs = config.get("services", {})

        for service in services:
            # 1. Backup the current state before making any changes
            cls._service_mutation_backup[service] = cls.get_current_mutation_name_for_service(service)

            # 2. Determine the mutation to apply
            service_specific_config = service_configs.get(service)

            if service_specific_config is not None:
                mutation_name = service_specific_config.get("mutation_name")
                function_mutation_overrides = service_specific_config.get("function_mutation_overrides")
            else:
                mutation_name = global_config.get("mutation_name")
                function_mutation_overrides = global_config.get("function_mutation_overrides")

            # 3. Write function mutation overrides to static config if provided and run the mutation builder
            if mutation_name:
                cls._write_static_mutation_config(service, mutation_name, function_mutation_overrides)
                cls._run_static_proxy_mutation_builder(service, mutation_name)
                cls._run_fcspec_generate_package_mutation_schema(service, mutation_name)
                cls.set_current_mutation_name_for_service(service, mutation_name)

    @classmethod
    def _write_static_mutation_config(cls, service_name: str, mutation_name: str, function_mutation_overrides: Optional[list]):
        """
        Writes function mutation overrides to the static mutation config file.
        """
        service_root = cls._get_service_root(service_name)
        config_dir = os.path.join(service_root, "SimulationEngine", "static_mutation_configs")
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, f"{mutation_name}.json")
        
        # Load existing config if it exists
        config = {"mutation_name": mutation_name, "functions": []}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError):
                config = {"functions": []}

        # Handle None for function_mutation_overrides
        if function_mutation_overrides is None:
            function_mutation_overrides = []

        # Build a mapping from original_name to override for quick lookup
        override_map = {override.get("original_name"): override for override in function_mutation_overrides if override.get("original_name")}

        # Prepare a new list of functions, replacing in-place and preserving order
        new_functions = []
        used_overrides = set()
        for func in config.get("functions", []):
            orig_name = func.get("original_name")
            if orig_name in override_map:
                # Replace with the override, preserving order
                override = override_map[orig_name]
                new_functions.append({
                    "original_name": override.get("original_name"),
                    "new_name": override.get("new_name"),
                    "args": override.get("args", [])
                })
                used_overrides.add(orig_name)
            else:
                # Keep the original function if not overridden
                new_functions.append(func)
        # Append any new overrides that weren't in the original list
        for override in function_mutation_overrides:
            orig_name = override.get("original_name")
            if orig_name and orig_name not in used_overrides:
                new_functions.append({
                    "original_name": override.get("original_name"),
                    "new_name": override.get("new_name"),
                    "args": override.get("args", [])
                })
        config["functions"] = new_functions

        # Write the config file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print_log(f"Written static mutation config for {service_name} mutation {mutation_name} to {config_path}")

    @classmethod
    def _run_static_proxy_mutation_builder(cls, service_name: str, mutation_name: str):
        """
        Runs the static proxy mutation builder for the specified services.
        """
        try:
            from Scripts.static_proxy_mutation_builder import StaticProxyMutationBuilder
            
            builder = StaticProxyMutationBuilder(
                service_name=service_name, 
                    config_name=mutation_name,
                    regenerate=True,
                    include_original_functions=False,
                    include_unmutated_functions=True
                )
            builder.build()
        except ImportError as e:
            import traceback
            print_log(f"Could not import static_proxy_mutation_builder: {e}")
            print_log(f"Full stack trace:\n{traceback.format_exc()}")
        except Exception as e:
            import traceback
            print_log(f"Error running static_proxy_mutation_builder: {e}")
            print_log(f"Full stack trace:\n{traceback.format_exc()}")

    @classmethod
    def _run_fcspec_generate_package_mutation_schema(cls, service_name: str, mutation_name: str):
        """
        Runs FCSpec.py generate_package_schema.
        """
        try:
            from Scripts.FCSpec import generate_schemas_for_package_mutations
            
            generate_schemas_for_package_mutations(service_name, [mutation_name])
            print_log("Successfully ran FCSpec.py generate_package_schema")
        except ImportError as e:
            print_log(f"Could not import FCSpec: {e}")
        except Exception as e:
            print_log(f"Error running FCSpec.py generate_package_schema: {e}")

    @classmethod
    def revert_meta_config(cls):
        """
        Reverts mutations applied by the meta-framework to their original state.
        """
        for service_name, original_mutation in cls._service_mutation_backup.items():
            cls.set_current_mutation_name_for_service(service_name, original_mutation)
        cls._service_mutation_backup = {}
    
    @classmethod
    def apply_config(cls, config: dict):
        """
        Backward-compatible method for direct usage (not through meta-framework).
        """
        services = discover_services()
        cls.apply_meta_config(config, services)
    
    @classmethod
    def rollback_config(cls):
        """
        Backward-compatible method for direct usage (not through meta-framework).
        """
        cls.revert_meta_config()

    @staticmethod
    def _get_service_root(service_name: str) -> str:
        # Go up two directories from this file, then into the service_name directory
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', service_name))

    @staticmethod
    def _get_mutation_root(service_name: str) -> str:
        return os.path.join(MutationManager._get_service_root(service_name), 'mutations')

    @staticmethod
    def _get_mutation_module_path(service_name: str) -> str:
        return f"{service_name}.mutations"

    @classmethod
    def _validate_and_generate_mutation_path_for_service(cls, service_name: str, mutation_name: Optional[str]):
        if mutation_name:
            function_map = cls._get_function_map_for_service_mutation(service_name, mutation_name)
            if function_map == {}:
                cls._run_static_proxy_mutation_builder(service_name, mutation_name)
                cls._run_fcspec_generate_package_mutation_schema(service_name, mutation_name)

    @staticmethod
    def _get_schema_path(service_name: str) -> str:
        # Path to the original schema file for the service
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Schemas", f"{service_name}.json"))

    @staticmethod
    def _get_mutation_schema_path(service_name: str, mutation_name: str) -> str:
        # Path to the mutated schema file for the service
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "MutationSchemas", mutation_name, f"{service_name}.json"))

    @staticmethod
    def _get_schema_backup_path(service_name: str) -> str:
        # Path to the backup of the original schema file
        os.makedirs(MutationManager._schema_backup_dir, exist_ok=True)
        return os.path.join(MutationManager._schema_backup_dir, f"{service_name}.json")

    @staticmethod
    def _backup_schema_file(service_name: str):
        orig_schema = MutationManager._get_schema_path(service_name)
        backup_schema = MutationManager._get_schema_backup_path(service_name)
        if os.path.exists(orig_schema) and not os.path.exists(backup_schema):
            shutil.copy2(orig_schema, backup_schema)

    @staticmethod
    def _replace_schema_with_mutation(service_name: str, mutation_name: str):
        orig_schema = MutationManager._get_schema_path(service_name)
        mutation_schema = MutationManager._get_mutation_schema_path(service_name, mutation_name)
        if os.path.exists(mutation_schema):
            shutil.copy2(mutation_schema, orig_schema)

    @staticmethod
    def _restore_schema_file(service_name: str):
        orig_schema = MutationManager._get_schema_path(service_name)
        backup_schema = MutationManager._get_schema_backup_path(service_name)
        if os.path.exists(backup_schema):
            shutil.copy2(backup_schema, orig_schema)
            os.remove(backup_schema)

    @staticmethod
    def set_current_mutation_name_for_service(service_name: str, mutation_name: Optional[str]):
        """
        Sets or clears the mutation for the API simulation for a given service.
        Also overrides the _function_map in the service module so that __getattr__ uses the mutated function map.
        Stores the original _function_map for proper revert.
        Also handles schema file backup and replacement.
        """
        MutationManager._validate_and_generate_mutation_path_for_service(service_name, mutation_name)
        MutationManager._mutation_names[service_name] = mutation_name

        # --- SCHEMA BACKUP/REPLACE LOGIC ---
        if mutation_name:
            # Backup the original schema if not already backed up
            MutationManager._backup_schema_file(service_name)
            # Replace with the mutated schema if it exists
            MutationManager._replace_schema_with_mutation(service_name, mutation_name)
        else:
            # Restore the original schema if backup exists
            MutationManager._restore_schema_file(service_name)

        service_mod = sys.modules.get(service_name)
        if not service_mod:
            return

        # Store the original _function_map if not already stored, BEFORE removing any attrs
        if service_name not in MutationManager._original_function_maps:
            try:
                orig_map = getattr(importlib.import_module(service_name), "_function_map", None)
                if orig_map is not None:
                    # Store a copy to avoid mutation
                    MutationManager._original_function_maps[service_name] = dict(orig_map)
            except Exception:
                pass

        # Helper to import a function from a fully qualified name, regardless of module depth
        def import_func_from_fqn(fqn):
            parts = fqn.split('.')
            for i in range(len(parts)-1, 0, -1):
                module_path = '.'.join(parts[:i])
                attr_chain = parts[i:]
                try:
                    mod = importlib.import_module(module_path)
                    obj = mod
                    for attr in attr_chain:
                        obj = getattr(obj, attr)
                    return obj
                except Exception:
                    continue
            # fallback: try importing the module up to the last part, then get the last attr
            try:
                module_path = '.'.join(parts[:-1])
                attr_name = parts[-1]
                mod = importlib.import_module(module_path)
                return getattr(mod, attr_name)
            except Exception:
                return None

        # Remove all function names from the service module's globals if present
        all_function_names = MutationManager._get_all_function_names(service_name)
        for attr in list(vars(service_mod)):
            if attr in all_function_names:
                try:
                    delattr(service_mod, attr)
                except Exception:
                    pass
        # Remove _function_map from the service module so it can't be used by __getattr__ until we set it below
        try:
            delattr(service_mod, "_function_map")
        except Exception:
            pass

        # Now, override the _function_map in the service module
        if mutation_name:
            # Load the mutation's _function_map
            mutation_module_path = f"{service_name}.mutations.{mutation_name}"
            try:
                mutation_module = importlib.import_module(mutation_module_path)
                mutation_function_map = getattr(mutation_module, "_function_map", {})
                # Override the service's _function_map
                setattr(service_mod, "_function_map", dict(mutation_function_map))
            except Exception:
                pass
        else:
            # Restore the original _function_map from our backup
            orig_map = MutationManager._original_function_maps.get(service_name)
            if orig_map is not None:
                try:
                    setattr(service_mod, "_function_map", dict(orig_map))
                except Exception:
                    pass

    @staticmethod
    def revert_current_mutation_for_service(service_name: str):
        """
        Resets the function map to its default state, clearing any active mutations for the service.
        Also removes _function_map from the service module before restoring.
        Also restores the original schema file.
        """
        MutationManager.set_current_mutation_name_for_service(service_name, None)

    @staticmethod
    def get_current_mutation_name_for_service(service_name: str) -> Optional[str]:
        """
        Gets the current mutation name for the given service.
        """
        return MutationManager._mutation_names.get(service_name, None)


    @staticmethod
    def _get_function_map_for_service_mutation(service_name: str, mutation_name: str) -> dict:
        """
        Gets the function map for the given service and mutation.
        """
        try:
            mutation_module_path = f"{service_name}.mutations.{mutation_name}"
            mutation_module = importlib.import_module(mutation_module_path)
            return getattr(mutation_module, "_function_map", {})
        except Exception as e:
            print_log(f"Error getting function map for service {service_name} and mutation {mutation_name}: {e}")
            return {}
    
    @staticmethod
    def _get_all_function_names(service_name: str) -> set[str]:
        """
        Gets all function names from all mutations for the service,
        and also includes those from the service root's _function_map.
        """
        all_function_names = set()
        mutation_root = MutationManager._get_mutation_root(service_name)
        mutation_module_path = MutationManager._get_mutation_module_path(service_name)
        service_root = MutationManager._get_service_root(service_name)

        # Include function names from the service root's _function_map
        try:
            service_module = importlib.import_module(service_name)
            all_function_names.update(getattr(service_module, "_function_map", {}).keys())
        except Exception:
            pass

        # Include function names from all mutation modules
        if os.path.isdir(mutation_root):
            for mutation_name in os.listdir(mutation_root):
                mutation_path = os.path.join(mutation_root, mutation_name)
                if os.path.isdir(mutation_path):
                    try:
                        mutation_module = importlib.import_module(
                            f"{mutation_module_path}.{mutation_name}",
                            package=service_root
                        )
                        all_function_names.update(getattr(mutation_module, "_function_map", {}).keys())
                    except Exception:
                        pass
        return all_function_names
    
    @staticmethod
    def get_current_mutation_function_map_for_service(service_name: str) -> dict:
        """
        Gets the function map for the given service.
        """
        mutation_name = MutationManager.get_current_mutation_name_for_service(service_name)
        if not mutation_name:
            return {}
        mutation_module_path = f"{service_name}.mutations.{mutation_name}"
        mutation_module = importlib.import_module(mutation_module_path)
        return getattr(mutation_module, "_function_map", {})

    @staticmethod
    def get_error_mutator_decorator_for_service(service_name: str) -> Callable:
        """
        Returns a decorator that modifies function error messages based on the active mutation for the given service.
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    mutation_name = MutationManager.get_current_mutation_name_for_service(service_name)
                    if not mutation_name: # pragma: no cover
                        raise e

                    service_root = MutationManager._get_service_root(service_name)
                    config_path = os.path.join(
                        service_root,
                        "SimulationEngine", "static_mutation_configs",
                        f"{mutation_name}.json"
                    )

                    if not os.path.exists(config_path):
                        raise e # Config is optional, raise original error

                    with open(config_path, 'r') as f:
                        config = json.load(f)

                    # Find the config for the decorated function by its public (mutated) name
                    func_config = next((f for f in config.get('functions', []) if f['new_name'] == func.__name__), None)

                    if func_config:
                        error_message = str(e)

                        # Special case: If the error is about an unexpected keyword argument,
                        # do NOT rename argument names in the error message.
                        # Example: "got an unexpected keyword argument 'new_user_identifier'"
                        if (
                            isinstance(e, TypeError)
                            and "got an unexpected keyword argument" in error_message
                        ):
                            # Only rename the function name, not argument names
                            original_func_name = func_config.get('original_name')
                            new_func_name = func_config.get('new_name')
                            if original_func_name and new_func_name:
                                error_message = re.sub(r'\b' + re.escape(original_func_name) + r'\b', new_func_name, error_message)
                        else:
                            # Rename arguments
                            if func_config.get('args'):
                                arg_map = {arg['original_name']: arg['new_name'] for arg in func_config['args']}
                                for old_arg, new_arg in arg_map.items():
                                    error_message = re.sub(r'\b' + re.escape(old_arg) + r'\b', new_arg, error_message)

                            # Rename function name
                            original_func_name = func_config.get('original_name')
                            new_func_name = func_config.get('new_name')
                            if original_func_name and new_func_name:
                                error_message = re.sub(r'\b' + re.escape(original_func_name) + r'\b', new_func_name, error_message)

                        if error_message != str(e):
                            raise type(e)(error_message) from e

                    # If no config or no changes, raise original error
                    raise e # pragma: no cover
            return wrapper
        return decorator

# --- Set default mutations from environment variables or a JSON file at module level ---
_service_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_this_dir = os.path.abspath(os.path.dirname(__file__))
for entry in os.listdir(_service_root_dir):
    entry_path = os.path.join(_service_root_dir, entry)
    # Only consider directories that are not this file's directory and not common_utils
    if (
        os.path.isdir(entry_path)
        and entry_path != _this_dir
        and entry != os.path.basename(_this_dir)
        and entry != "common_utils"
        and not entry.startswith("__")
    ):
        env_var = f"{entry.upper()}_MUTATION_NAME"
        mutation_name = os.environ.get(env_var)
        if mutation_name:
            print(f"Setting {env_var} to {mutation_name}")
            MutationManager.set_current_mutation_name_for_service(entry, mutation_name)
