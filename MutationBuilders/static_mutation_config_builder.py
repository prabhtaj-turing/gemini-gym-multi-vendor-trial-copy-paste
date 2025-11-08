import json
import os
import ast
import re
import logging
from tqdm import tqdm
import google.generativeai as genai
from copy import deepcopy
import sys
import traceback

logging = logging.getLogger("mutation_engine")

class StaticMutationConfigBuilder:
    def __init__(self, service_name, mutation_name, regenerate=False, sync_latest=True):
        """
        :param service_name: Name of the API service
        :param mutation_name: Name of the mutation config
        :param regenerate: Force regenerate the config (overrides sync_latest)
        :param sync_latest: If True (default), will sync and update only changed/new functions
        """
        self.service_name = service_name
        self.mutation_name = mutation_name
        self.regenerate = regenerate
        self.sync_latest = sync_latest
        self.api_root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'APIs', self.service_name))
        self.config_path = os.path.join(self.api_root_dir, 'SimulationEngine', 'static_mutation_configs', f"{self.mutation_name}.json")


    def _unwrap_all(self, func, max_depth=10):
        seen = set()
        for _ in range(max_depth):
            if func in seen:
                break
            seen.add(func)

            # Unwrap __wrapped__ (standard way)
            if hasattr(func, '__wrapped__'):
                func = func.__wrapped__
                continue

            # Fallback: scan __closure__
            closure = getattr(func, '__closure__', None)
            if closure:
                for cell in closure:
                    try:
                        val = cell.cell_contents
                        if callable(val) and val not in seen:
                            func = val
                            break
                    except Exception:
                        continue
                else:
                    break
            else:
                break
        return func

    def _get_function_signatures(self):
        """
        Extracts function signatures and docstrings for all functions referenced in the _function_map
        of the main __init__.py, by importing the function and using the inspect and ast modules
        to get the function definition and docstring.

        Returns:
            dict: { tool_name: { 'args': [...], 'file': ..., 'docstring': ... } }
        """
        import importlib
        import inspect
        import ast

        signatures = {}
        init_path = os.path.join(self.api_root_dir, '__init__.py')
        if not os.path.exists(init_path):
            raise FileNotFoundError(f"Could not find __init__.py at {self.api_root_dir}")

        with open(init_path, 'r') as f:
            init_content = f.read()

        tree = ast.parse(init_content)
        function_map_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '_function_map':
                        function_map_node = node.value
                        break
                if function_map_node:
                    break

        if not function_map_node or not isinstance(function_map_node, ast.Dict):
            raise ValueError(f"_function_map not found or not a dict in {init_path}")

        function_map = ast.literal_eval(function_map_node)

        for tool_name, func_path in function_map.items():
            # func_path is like "clock.StopwatchApi.start_stopwatch" or "clock.StopwatchApi.moduleA.ModuleB.start_stopwatch"
            if '.' not in func_path:
                continue  # Not a valid module path

            *module_parts, func_name = func_path.split('.')
            module_str = '.'.join(module_parts)
            try:
                module = importlib.import_module(module_str, package=self.service_name)
                func = getattr(module, func_name)
                unwrapped_func = self._unwrap_all(func)
                source = inspect.getsource(unwrapped_func)
                func_ast = ast.parse(source)

                # Find the function definition node
                funcdef_node = None
                for node in ast.walk(func_ast):
                    if isinstance(node, ast.FunctionDef) and node.name == func_name:
                        funcdef_node = node
                        break

                if funcdef_node is not None:
                    # Get all argument names, including positional, kwonly, and varargs/kwargs
                    args = []
                    # Positional and keyword arguments
                    for arg in funcdef_node.args.args:
                        args.append(arg.arg)
                    # *args
                    if funcdef_node.args.vararg:
                        args.append(f"*{funcdef_node.args.vararg.arg}")
                    # Keyword-only arguments
                    for arg in funcdef_node.args.kwonlyargs:
                        args.append(arg.arg)
                    # **kwargs
                    if funcdef_node.args.kwarg:
                        args.append(f"**{funcdef_node.args.kwarg.arg}")
                    docstring = ast.get_docstring(funcdef_node)
                else:
                    # Fallback: try to get signature from inspect (may miss kwonly)
                    try:
                        sig = inspect.signature(unwrapped_func)
                        args = [p.name for p in sig.parameters.values()]
                    except Exception:
                        args = []
                    docstring = None

                # Try to get the file where the function is defined
                try:
                    file_path = inspect.getfile(func)
                    rel_file = os.path.relpath(file_path, self.api_root_dir)
                except Exception:
                    rel_file = None

                signatures[tool_name] = {
                    'args': args,
                    'file': rel_file,
                    'docstring': docstring
                }
            except Exception as e:
                logging.warning(f"Could not import or inspect '{func_path}' for tool '{tool_name}': {e}")

        return signatures

    def _generate_prompt(self, signatures, existing_func_configs=None):
        """
        Generate a prompt for the LLM. If existing_func_configs is provided, include the previous
        mutated names for functions and arguments, and ask the model to preserve them if possible.
        """
        prompt = f"""
        Given the following function signatures and docstrings from the '{self.service_name}' API, generate a mutation configuration named '{self.mutation_name}'.

        For each function, create a new, unique, and descriptive name.
        For each argument in every function, also provide a new, unique, and descriptive name.

        If a previous mutation configuration is provided for a function, please try to keep the same mutated function and argument names as before, unless the function signature has changed in a way that makes it impossible (e.g., new or removed arguments). If a new argument is present, generate a new name for it. If an argument is removed, do not include it.

        The output should be in a simple markdown format. Do not use JSON.

        Example format:
        # Mutation: {self.mutation_name}

        ## Function: original_function_name -> new_function_name
        - original_arg_1 -> new_arg_1
        - original_arg_2 -> new_arg_2

        ## Function: another_function -> mutated_function
        - arg_a -> param_a
        - arg_b -> param_b

        Here are the function details:
        """

        for func_name, details in signatures.items():
            prompt += f"\n---\n"
            prompt += f"Function: {func_name}\n"
            prompt += f"File: {details['file']}\n"
            prompt += f"Arguments: {details['args']}\n"
            if details['docstring']:
                prompt += f"Docstring:\n{details['docstring']}\n"
            # If we have an existing config for this function, include it
            if existing_func_configs and func_name in existing_func_configs:
                prev_func = existing_func_configs[func_name]
                prompt += f"Previous mutation config for this function:\n"
                prompt += f"  Mutated function name: {prev_func.get('new_name','')}\n"
                prompt += f"  Mutated argument names:\n"
                for arg in prev_func.get("args", []):
                    prompt += f"    - {arg.get('original_name','')} -> {arg.get('new_name','')}\n"

        prompt += "\n---\nPlease generate the complete mutation configuration in the specified markdown format."

        logging.debug("--- PROMPT ---")
        logging.debug(prompt)
        logging.debug("--- END PROMPT ---")
        return prompt

    def _parse_markdown_to_json(self, markdown_text):
        config = {
            "mutation_name": self.mutation_name,
            "functions": []
        }
        
        current_function = None
        
        for line in markdown_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            func_match = re.match(r'##\s*Function:\s*(\w+)\s*->\s*(\w+)', line)
            if func_match:
                if current_function:
                    config["functions"].append(current_function)
                current_function = {
                    "original_name": func_match.group(1),
                    "new_name": func_match.group(2),
                    "args": []
                }
                continue

            arg_match = re.match(r'-\s*(\w+)\s*->\s*(\w+)', line)
            if arg_match and current_function:
                current_function["args"].append({
                    "original_name": arg_match.group(1),
                    "new_name": arg_match.group(2)
                })
                continue
        
        if current_function:
            config["functions"].append(current_function)
            
        return config

    def _load_existing_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                try:
                    return json.load(f)
                except Exception as e:
                    logging.warning(f"Could not load existing config: {e}")
        return None

    def _function_signature_changed(self, old_func, new_func):
        # Compare argument names and count
        if old_func is None:
            return True
        if old_func.get("args") is None or new_func.get("args") is None:
            return True
        old_args = [a["original_name"] for a in old_func.get("args",[])]
        new_args = new_func.get("args",[])
        # Safely handle empty new_args
        if not new_args:
            return old_args != []
        if isinstance(new_args[0], dict):
            # Already in config format
            new_args = [a["original_name"] for a in new_args]
        # else, new_args is just a list of arg names
        if old_args != new_args:
            return True
        return False

    def _merge_configs(self, old_config, new_functions):
        """
        Merge new_functions (list of config function dicts) into old_config (dict).
        Only update/replace functions that are new or changed.
        """
        merged = deepcopy(old_config)
        merged_funcs = {f["original_name"]: f for f in merged.get("functions", [])}
        for new_func in new_functions:
            merged_funcs[new_func["original_name"]] = new_func
        merged["functions"] = list(merged_funcs.values())
        return merged

    def build(self):
        # If not syncing latest and not regenerating, skip if config exists
        if not self.regenerate and not self.sync_latest and os.path.exists(self.config_path):
            logging.info(f"Config file {self.config_path} already exists. Skipping.")
            return

        signatures = self._get_function_signatures()
        if not signatures:
            logging.info(f"No function signatures found for service '{self.service_name}'. Skipping.")
            return

        # Load existing config if present
        existing_config = self._load_existing_config()
        existing_funcs_map = {}
        if existing_config and "functions" in existing_config:
            for f in existing_config["functions"]:
                existing_funcs_map[f["original_name"]] = f

        # If not regenerating and sync_latest is True, only update changed/new functions
        to_update_signatures = {}
        to_update_existing_func_configs = {}
        if not self.regenerate and self.sync_latest and existing_config:
            # Only update if function is new or signature changed
            for func_name, details in signatures.items():
                # Compose a dummy config function dict for comparison
                dummy_func = {
                    "original_name": func_name,
                    "args": [{"original_name": arg, "new_name": ""} for arg in details["args"]]
                }
                old_func = existing_funcs_map.get(func_name)
                if old_func is None or self._function_signature_changed(old_func, dummy_func):
                    to_update_signatures[func_name] = details
                    if old_func is not None:
                        to_update_existing_func_configs[func_name] = old_func
            # Also, check for removed functions (not present in signatures anymore)
            removed_funcs = set(existing_funcs_map.keys()) - set(signatures.keys())
            if not to_update_signatures and not removed_funcs:
                logging.info(f"No changes detected in function signatures for '{self.service_name}'. Skipping.")
                return
        else:
            # Regenerate all
            to_update_signatures = signatures
            to_update_existing_func_configs = None

        # If nothing to update and no removed functions, skip
        if not to_update_signatures and (not self.regenerate and self.sync_latest):
            logging.info(f"No new or changed functions to update for '{self.service_name}'. Skipping.")
            return

        # Generate prompt for only the changed/new functions, and pass previous mutated names if available
        prompt = self._generate_prompt(to_update_signatures, existing_func_configs=to_update_existing_func_configs)
        logging.info(f"Generating mutation configuration for '{self.service_name}' using Gemini 2.5 Pro...")
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(prompt)
        
        try:
            markdown_response = response.text
            logging.debug("--- MODEL RESPONSE ---")
            logging.debug(markdown_response)
            logging.debug("--- END MODEL RESPONSE ---")

            config_data = self._parse_markdown_to_json(markdown_response)
            
            if not config_data["functions"]:
                raise ValueError("Failed to parse any functions from the model's response.")

            # If merging, update only changed/new functions and remove deleted ones
            if existing_config and not self.regenerate and self.sync_latest:
                # Remove deleted functions
                merged_config = deepcopy(existing_config)
                merged_config["functions"] = [
                    f for f in merged_config.get("functions", [])
                    if f["original_name"] in signatures
                ]
                # Merge/replace updated functions
                merged_config = self._merge_configs(merged_config, config_data["functions"])
                config_data = merged_config

            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logging.info(f"Successfully created mutation config: {self.config_path}")

        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            logging.error(f"Error processing the model's response for {self.service_name}: {e}")
            logging.error("Full response from the model was:")
            logging.error(response.text)

if __name__ == '__main__':
    # --- Configuration ---
    REGENERATE_CONFIGS = False  # Set to True to overwrite all configs
    SYNC_LATEST = True         # Set to False to skip sync/merge and only use regenerate flag
    MUTATION_NAME = "m01"
    # -------------------

    api_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'APIs'))
    print("api_dir", api_dir)
    sys.path.append(api_dir)

    all_services = [d for d in os.listdir(api_dir) if os.path.isdir(os.path.join(api_dir, d))]

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API key not provided. Please set the GEMINI_API_KEY environment variable.")
    genai.configure(api_key=api_key)

    for service in tqdm(["shopify"], desc="Building configs", unit="service"):
        logging.info(f"\n--- Building config for service: {service} ---")
        try:
            builder = StaticMutationConfigBuilder(
                service_name=service, 
                mutation_name=MUTATION_NAME,
                regenerate=REGENERATE_CONFIGS,
                sync_latest=SYNC_LATEST
            )
            builder.build()
            logging.info(f"--- Successfully built config for {service} ---\n")
        except (ValueError, FileNotFoundError) as e:
            logging.error(f"Error building config for {service}: {e}\n")
        except Exception as e:
            logging.error(f"An unexpected error occurred for {service}: {e}\n")