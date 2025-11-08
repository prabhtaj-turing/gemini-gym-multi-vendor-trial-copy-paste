from common_utils.print_log import print_log
"""
Error simulation for API modules.

This module provides a class to simulate errors in API functions.
"""
import random
import json
import builtins
import sys
import os
import ast
# import types # Not strictly used by original _resolve_function_paths but often kept
import inspect
from typing import Dict, Type, Optional
import functools

RESOLVE_PATHS_DEBUG_MODE = False # Enable for detailed logs

class ErrorSimulator:
    def __init__(
        self,
        error_config_path="error_config.json",
        error_definitions_path="error_definitions.json",
        max_errors_per_run: Optional[int] = None,
        service_root_path: Optional[str] = None,
    ):
        self.error_config_path = error_config_path
        self.error_definitions_path = error_definitions_path
        
        # Store the initial local configuration paths for rollback
        self._initial_error_config_path = error_config_path
        self._initial_error_definitions_path = error_definitions_path
        self._initial_max_errors_per_run = max_errors_per_run
        
        self.error_config, raw_definitions = self._load_configurations(
            error_config_path, error_definitions_path
        )
        self.max_errors_per_run = max_errors_per_run
        self.current_error_count = 0
        self.error_simulation_tracker = self._initialize_tracker()

        # Using service_root_path logic similar to original for _function_map
        # If service_root_path is None (as passed from zendesk/__init__.py),
        # self._function_map becomes {} if _load_function_maps can't find/parse a map.
        # This is fine if error_definitions.json uses FQNs, as raw_key will be used by _resolve_function_paths.
        self._function_map = (
            self._load_function_maps(service_root_path) if service_root_path else {}
        )
        if RESOLVE_PATHS_DEBUG_MODE:
            print_log(f"DEBUG: ErrorSimulator.__init__: service_root_path='{service_root_path}'. Loaded self._function_map with {len(self._function_map)} entries. Keys: {list(self._function_map.keys())}")
        
        self.error_definitions = self._resolve_function_paths(raw_definitions) # Uses original _resolve_function_paths
        
        if RESOLVE_PATHS_DEBUG_MODE:
            if not self.error_definitions and raw_definitions:
                print_log(f"CRITICAL DEBUG: ErrorSimulator.__init__: self.error_definitions is EMPTY after _resolve_function_paths, but raw_definitions was not. Path resolution likely failed.")
            else:
                print_log(f"DEBUG: ErrorSimulator.__init__: Loaded {len(self.error_definitions)} resolved error definitions. Keys: {list(self.error_definitions.keys())}")

    # --- Methods from YOUR ORIGINAL WORKING ErrorSimulator ---
    def _infer_service_root_path(self, caller_file: str) -> str:
        path_parts = caller_file.split(os.sep)
        if "SimulationEngine" in path_parts:
            idx = path_parts.index("SimulationEngine")
            return os.sep.join(path_parts[:idx])
        return os.path.dirname(caller_file)

    def _load_function_maps(self, package_root_path: str) -> Dict[str, str]:
        """
        Loads the _function_map from the given package's __init__.py, but ONLY if it is hard-coded
        as a dict literal (e.g. _function_map = { ... }). Ignores all other assignments, including
        calls to mutation_manager.load_function_map() or any dynamic assignment.
        """
        import ast
        import os

        function_map = {}
        if not package_root_path:  # Guard for None or empty path
            if RESOLVE_PATHS_DEBUG_MODE:
                print_log(f"DEBUG: _load_function_maps: package_root_path is None/empty. Returning empty map.")
            return function_map

        init_file = os.path.join(package_root_path, "__init__.py")
        if not os.path.isfile(init_file):
            if RESOLVE_PATHS_DEBUG_MODE:
                print_log(f"DEBUG: _load_function_maps: No __init__.py at {init_file} to extract _function_map.")
            return function_map
        try:
            with open(init_file, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == "_function_map"
                        ):
                            # Only accept if the value is a dict literal (hard-coded)
                            if isinstance(node.value, ast.Dict):
                                value = ast.literal_eval(node.value)
                                function_map.update(value)
                                if RESOLVE_PATHS_DEBUG_MODE:
                                    print_log(f"DEBUG: _load_function_maps: Loaded _function_map from {init_file}")
                            else:
                                # Ignore ALL non-dict assignments (dynamic, function call, etc)
                                if RESOLVE_PATHS_DEBUG_MODE:
                                    print_log(f"DEBUG: _load_function_maps: Skipping _function_map assignment (not a dict literal) in {init_file}")
        except Exception as e:
            print_log(f"[WARN] ErrorSimulator: Failed to parse _function_map from {init_file}: {e}")
        return function_map

    def _resolve_function_paths(self, raw_definitions: dict) -> dict: # FROM YOUR ORIGINAL
        if RESOLVE_PATHS_DEBUG_MODE: print_log(f"DEBUG: _resolve_function_paths (original logic) called with {len(raw_definitions)} raw definitions.")
        updated = {}
        all_paths = set()
        EXCLUDED_MODULES = {"dbm", "dbm.gnu", "gdbm", "shelve", "email", "tkinter", "unittest", "pydoc"} # Added unittest, pydoc

        modules_to_inspect = dict(sys.modules) 

        for mod_name, module_obj in modules_to_inspect.items():
            if not module_obj or not hasattr(module_obj, "__name__"):
                continue
            
            # Using mod_name from dict key, which is usually the canonical import path
            if any(excluded_part in mod_name for excluded_part in EXCLUDED_MODULES):
                # if RESOLVE_PATHS_DEBUG_MODE: print(f"DEBUG: _resolve_function_paths: Skipping excluded module: {mod_name}")
                continue
            
            # Optional: Add more filtering here if necessary, e.g., for performance on very large environments
            # However, the original didn't have much more, so try to keep it similar.
            # if RESOLVE_PATHS_DEBUG_MODE and "zendesk" in mod_name: # Only print for relevant modules
            #    print(f"DEBUG: _resolve_function_paths: Inspecting module: {mod_name}")

            try:
                for name, obj in inspect.getmembers(module_obj):
                    member_module_name = getattr(obj, '__module__', None)
                    
                    # Add function if it's defined in the current module
                    if inspect.isfunction(obj): # This covers functions and non-bound methods
                        if member_module_name == mod_name:
                            all_paths.add(f"{mod_name}.{name}")
                    elif inspect.isclass(obj):
                        if member_module_name == mod_name: # Class defined in this module
                            for fname, fobj in inspect.getmembers(obj, inspect.isfunction): # inspect.isfunction gets methods
                                method_module_name = getattr(fobj, '__module__', None)
                                # Check if method's module is the class's module (which is mod_name)
                                if method_module_name == mod_name:
                                    all_paths.add(f"{mod_name}.{obj.__name__}.{fname}")
            except Exception as e:
                # if RESOLVE_PATHS_DEBUG_MODE: print(f"DEBUG: _resolve_function_paths: Error inspecting module {mod_name}: {e}")
                continue
        
        if RESOLVE_PATHS_DEBUG_MODE:
            print_log(f"DEBUG: _resolve_function_paths (original logic): Collected {len(all_paths)} FQNs.")
            # To see all collected paths if needed:
            # for p in sorted(list(all_paths)):
            # print(f"     {p}")


        for raw_key, definitions in raw_definitions.items():
            resolved_key = self._function_map.get(raw_key, raw_key) # self._function_map is likely {} if service_root_path=None
            if RESOLVE_PATHS_DEBUG_MODE: print_log(f"DEBUG: _resolve_function_paths (original logic): Resolving raw_key '{raw_key}' as '{resolved_key}'")
            
            if resolved_key in all_paths:
                updated[resolved_key] = definitions
                if RESOLVE_PATHS_DEBUG_MODE: print_log(f"DEBUG: _resolve_function_paths (original logic): Direct match for '{resolved_key}'.")
            else:
                matched = False
                # Original suffix fallback (more useful if resolved_key is not a full FQN)
                for full_path_candidate in all_paths:
                    if full_path_candidate.endswith("." + resolved_key) or full_path_candidate == resolved_key : # check for "package." + "module.func" or "module.Class.method"
                        updated[full_path_candidate] = definitions
                        matched = True
                        if RESOLVE_PATHS_DEBUG_MODE: print_log(f"DEBUG: _resolve_function_paths (original logic): Suffix/Exact fallback match for '{resolved_key}' with '{full_path_candidate}'.")
                        break
                if not matched and RESOLVE_PATHS_DEBUG_MODE:
                    print_log(f"[WARNING] ErrorSimulator (original logic): Could not resolve function path: '{raw_key}' (tried as '{resolved_key}')")
        
        if RESOLVE_PATHS_DEBUG_MODE: print_log(f"DEBUG: _resolve_function_paths (original logic): Returning {len(updated)} resolved definitions.")
        return updated
    # --- End of methods from ORIGINAL WORKING ErrorSimulator ---

    def _load_configurations(self, config_path, definitions_path):
        error_config, error_definitions = {}, {}
        try:
            with open(config_path) as cf: error_config = json.load(cf)
        except FileNotFoundError: print_log(f"[WARN] Config file {config_path} not found.")
        except json.JSONDecodeError as e: print_log(f"[WARN] Invalid JSON in {config_path}: {e}")
        try:
            with open(definitions_path) as df: error_definitions = json.load(df)
        except FileNotFoundError: print_log(f"[WARN] Definitions file {definitions_path} not found.")
        except json.JSONDecodeError as e: print_log(f"[WARN] Invalid JSON in {definitions_path}: {e}")
        return error_config, error_definitions

    def _initialize_tracker(self) -> Dict[str, Dict[str, float]]:
        return {et:{"count":0,"probability":c.get("probability",0.0)} for et,c in self.error_config.items() if et != 'max_errors_per_run'}
    
    def load_central_config(self, central_config: dict = None, central_config_path: str = None, service_name: str = None):
        """
        Loads a central configuration file and stores the different levels
        of configuration separately to enforce a strict hierarchy.
        Args:
            central_config (dict): A pre-loaded dictionary of the configuration.
            central_config_path (str): The path to the central JSON config file.
            service_name (str): The name of the service to load settings for.
        """
        if central_config is None and central_config_path is None:
            raise ValueError("Either central_config or central_config_path must be provided")

        if central_config is None:
            try:
                with open(central_config_path) as cf:
                    full_config = json.load(cf)
            except FileNotFoundError:
                print(f"[INFO] Central config file not found at {central_config_path}. Using local configs.")
                return
            except json.JSONDecodeError as e:
                print(f"[WARN] Invalid JSON in {central_config_path}: {e}. Using local configs.")
                return
        else:
            full_config = central_config

        # print(f"DEBUG: Full config: {full_config}")
        if "error" in full_config:
            error_section_config = full_config.get("error", full_config)
            global_config = error_section_config.get("global", {})
            services_config = error_section_config.get("services", {})
        elif "global" in full_config or "services" in full_config:
            error_section_config = full_config
            global_config = error_section_config.get("global", {})
            services_config = error_section_config.get("services", {})
        else:
            print(f"[WARN] Invalid central config: {full_config}")
            return
        
        if global_config:
            self.error_config = global_config

        service_config_found = False
        # Look for the service in the services subsection
        if service_name and service_name in services_config:
            service_config = services_config[service_name]
            service_config_found = True

            if "config" in service_config:
                self.error_config = service_config["config"]
                # print(f"DEBUG: Error config: {self.error_config}")
            
            if "max_errors_per_run" in service_config:
                max_errors = service_config.get("max_errors_per_run")
                if max_errors is not None:
                    self.max_errors_per_run = max_errors
            
            print(f"[INFO] Loaded central error configuration for service: '{service_name}'")
            # print(f"DEBUG: Error config: {self.error_config}")
        elif service_name:
            print(f"[INFO] No specific error configuration found for service: '{service_name}' in central config. Using existing/local settings.")
            # Do not re-initialize if no config is loaded for the requested service
            return

        # Re-initialize the tracker and counter if a new configuration was loaded.
        # This will reset probabilities and counts for the new session.
        if service_config_found:
            self.error_simulation_tracker = self._initialize_tracker()
            self.max_errors_per_run = service_config.get('config', {}).get('max_errors_per_run', None)
            # print(f"DEBUG: Max errors per run: {self.max_errors_per_run}")
            self.current_error_count = 0
        
    def _get_exception_class(self, name: str) -> Type[Exception]:
        if hasattr(builtins, name): return getattr(builtins, name)
        raise ValueError(f"Unknown built-in exception: {name}")

    def _select_error_type(self, func_path: str) -> Optional[str]:
        # (Logic from our previous refactored version - this part was generally fine)
        errors = self.error_definitions.get(func_path, [])
        if not errors: return None
        eligible_with_limit, eligible_by_probability = [], []
        random_value = random.random()
        for err_details in errors:
            err_type = err_details["exception"]
            config = self.error_config.get(err_type, {})
            tracker = self.error_simulation_tracker.get(err_type)
            if not tracker:
                 if err_type in self.error_config:
                     self.error_simulation_tracker[err_type] = {"count": 0, "probability": config.get("probability", 0.0)}
                     tracker = self.error_simulation_tracker[err_type]
                 else: continue
            count = tracker.get("count", 0)
            prob = tracker.get("probability", config.get("probability", 0.0))
            limit = config.get("num_errors_simulated")
            if limit is not None and count < limit: eligible_with_limit.append((err_type, limit - count, prob))
            elif limit is None and random_value < prob : eligible_by_probability.append((err_type, prob))
        if eligible_with_limit:
            eligible_with_limit.sort(key=lambda x: (-x[1], -x[2]))
            return eligible_with_limit[0][0]
        if eligible_by_probability:
            eligible_by_probability.sort(key=lambda x: -x[1])
            return eligible_by_probability[0][0]
        return None

    def _dampen_probability(self, error_type: str):
        if error_type not in self.error_simulation_tracker or error_type not in self.error_config: return
        tracker, config = self.error_simulation_tracker[error_type], self.error_config[error_type]
        dampen_factor = config.get("dampen_factor")
        if dampen_factor is not None: # Check explicitly for None
            tracker["probability"] *= (1 - dampen_factor)
            tracker["probability"] = max(0.0, min(1.0, tracker["probability"]))
            
    def get_error_simulation_decorator(self, full_func_path: str):
        """
        Returns a decorator that wraps a function with error simulation logic
        for the given full_func_path.
        """
        # RESOLVE_PATHS_DEBUG_MODE is a global flag you can define in ErrorSimulation.py
        # if RESOLVE_PATHS_DEBUG_MODE: (using a more direct check here for clarity)
        #     # ... (debug prints as before) ...

        if full_func_path not in self.error_definitions: # No definition, no simulation
            def identity_decorator(original_func):
                @functools.wraps(original_func)
                def no_op_wrapper(*args, **kwargs):
                    return original_func(*args, **kwargs)
                return no_op_wrapper
            return identity_decorator

        # Has definitions, return the actual simulating decorator
        def decorator(original_func):
            @functools.wraps(original_func)
            def wrapper(*args, **kwargs):
                # 1. Check if simulation should be skipped (max errors per run)
                if (
                    self.max_errors_per_run is not None
                    and self.current_error_count >= self.max_errors_per_run
                ):
                    return original_func(*args, **kwargs)
                
                # 2. Select an error type to inject for this function call
                error_type_to_inject = self._select_error_type(full_func_path)
                if not error_type_to_inject:
                    return original_func(*args, **kwargs) # No error selected based on probability/limits
                
                # 3. Get details for the selected error
                selected_error_details = next(
                    (d for d in self.error_definitions.get(full_func_path, []) 
                     if d["exception"] == error_type_to_inject), 
                    None
                )
                if not selected_error_details:
                    # This should ideally not happen if _select_error_type returned a valid type
                    # for which definitions exist.
                    return original_func(*args, **kwargs) 
                
                # 4. Prepare and raise the simulated exception
                exception_class = self._get_exception_class(error_type_to_inject)
                
                # Ensure tracker entry exists for counting
                if error_type_to_inject not in self.error_simulation_tracker:
                     self.error_simulation_tracker[error_type_to_inject] = {
                         "count": 0, 
                         "probability": self.error_config.get(error_type_to_inject, {}).get("probability", 0.0)
                     }
                self.error_simulation_tracker[error_type_to_inject]["count"] += 1
                self.current_error_count += 1
                
                # Dampen probability if applicable
                if self.error_config.get(error_type_to_inject, {}).get("num_errors_simulated") is None:
                    self._dampen_probability(error_type_to_inject)
                
                simulated_exception = exception_class(
                    selected_error_details.get("message", f"Simulated {error_type_to_inject}")
                )
                
                # The `handle_api_errors` decorator (applied in __init__.py)
                # will catch and process this exception.
                raise simulated_exception 
                
            return wrapper
        return decorator

    # --- Programmatic API Methods (load_error_config, etc.) ---
    def load_error_config(self, new_config_path: str, preserve_counts: bool = False):
        try:
            with open(new_config_path) as cf: new_config = json.load(cf)
        except FileNotFoundError: print_log(f"[WARN] load_error_config: File not found {new_config_path}."); return
        except json.JSONDecodeError as e: print_log(f"[WARN] load_error_config: Invalid JSON in {new_config_path}: {e}."); return
        self.error_config = new_config; self.error_config_path = new_config_path
        # print(f"DEBUG: Error config: {self.error_config}")
        if preserve_counts:
            new_tracker = {}
            for et,cd in self.error_config.items():
                ptd=self.error_simulation_tracker.get(et,{}); new_tracker[et]={"count":ptd.get("count",0),"probability":cd.get("probability",0.0)}
            self.error_simulation_tracker = new_tracker
        else: self.error_simulation_tracker = self._initialize_tracker(); self.current_error_count = 0

    def load_error_definitions(self, new_definitions_path: str):
        try:
            with open(new_definitions_path) as df: raw_definitions = json.load(df)
        except FileNotFoundError: print_log(f"[WARN] load_error_definitions: File not found {new_definitions_path}."); return
        except json.JSONDecodeError as e: print_log(f"[WARN] load_error_definitions: Invalid JSON in {new_definitions_path}: {e}."); return
        self.error_definitions_path = new_definitions_path
        self.error_definitions = self._resolve_function_paths(raw_definitions) # Uses original logic
        if RESOLVE_PATHS_DEBUG_MODE: print_log(f"DEBUG: load_error_definitions: self.error_definitions updated. Keys: {list(self.error_definitions.keys())}")

    # (Rest of API methods: update_error_probability, update_dampen_factor, etc. as before)
    def update_error_probability(self, error_type: str, new_probability: float): # Changed to new_probability
        if error_type not in self.error_config: self.error_config[error_type] = {} 
        if not (0.0 <= new_probability <= 1.0): raise ValueError("Probability must be between 0.0 and 1.0") 
        self.error_config[error_type]["probability"] = new_probability 
        self.error_simulation_tracker.setdefault(error_type, {"count":0})["probability"] = new_probability 

    def update_dampen_factor(self, error_type: str, new_factor: float): # Changed to new_factor
        if error_type not in self.error_config: self.error_config[error_type] = {} 
        if not (0.0 <= new_factor <= 1.0): raise ValueError("Dampen factor must be between 0.0 and 1.0") 
        self.error_config[error_type]["dampen_factor"] = new_factor 

    def update_num_errors_simulated(self, error_type: str, num_errors_simulated: Optional[int]): 
        if error_type not in self.error_config: self.error_config[error_type] = {} 
        if num_errors_simulated is None: self.error_config[error_type]["num_errors_simulated"] = None 
        else:
            if num_errors_simulated < 0: raise ValueError("num_errors_simulated must be >= 0 or None") 
            self.error_config[error_type]["num_errors_simulated"] = int(num_errors_simulated) 

    def set_max_errors_per_run(self, max_errors: int): 
        if max_errors < 0: raise ValueError("max_errors_per_run must be non-negative") 
        self.max_errors_per_run = max_errors 
        
    def reset_probabilities(self): 
        for et, cfg in self.error_config.items(): 
            self.error_simulation_tracker.setdefault(et, {"count":0})["probability"] = cfg.get("probability",0.0) 
                
    def get_current_error_count(self) -> int: return self.current_error_count 
    
    def add_or_update_error_type(self, error_type: str, probability: float, dampen_factor: float, num_errors_simulated: Optional[int] = None): # Kept standardized names here
        if not (0.0 <= probability <= 1.0): raise ValueError("Probability must be between 0.0 and 1.0") 
        if not (0.0 <= dampen_factor <= 1.0): raise ValueError("Dampen factor must be between 0.0 and 1.0") 
        
        self.error_config[error_type] = { 
            "probability": probability,
            "dampen_factor": dampen_factor,
        }
        if num_errors_simulated is not None: 
            if num_errors_simulated < 0: raise ValueError("num_errors_simulated must be >= 0 or None") 
            self.error_config[error_type]["num_errors_simulated"] = num_errors_simulated 
        
        self.error_simulation_tracker.setdefault(error_type, {"count":0})["probability"] = probability 
        if "count" not in self.error_simulation_tracker[error_type]: self.error_simulation_tracker[error_type]["count"] = 0 
        
    def get_debug_state(self) -> Dict[str, Dict]: 
        debug_state = { 
            "current_probabilities": {}, 
            "dampen_factors": {}, 
            "error_limits": {}, 
            "total_errors_simulated": self.current_error_count, 
            # "resolved_error_definitions_keys" was removed as requested
        }
        for et, config_data in self.error_config.items(): 
            if et != 'max_errors_per_run':
                tracker_data = self.error_simulation_tracker.get(et, {"count": 0, "probability": config_data.get("probability", 0.0)})
                debug_state["current_probabilities"][et] = tracker_data.get("probability")
                debug_state["dampen_factors"][et] = config_data.get("dampen_factor", 0.0) 
                limit = config_data.get("num_errors_simulated") 
                debug_state["error_limits"][et] = {"count": tracker_data["count"], "limit": limit, 
                                                "limit_reached": (False if limit is None else tracker_data["count"] >= limit)} 
            else:
                tracker_data = None
        return debug_state 
    
    def reload_initial_config(self):
        """
        Reloads the initial local configuration that was set during initialization.
        This ensures rollback restores the exact original local state.
        """
        # Reload from the original local configuration files
        self.error_config, raw_definitions = self._load_configurations(
            self._initial_error_config_path, self._initial_error_definitions_path
        )
        self.max_errors_per_run = self._initial_max_errors_per_run
        self.error_simulation_tracker = self._initialize_tracker()
        self.current_error_count = 0
        self.error_definitions = self._resolve_function_paths(raw_definitions)
        
        print(f"[INFO] Reloaded initial local configuration from {self._initial_error_config_path}")