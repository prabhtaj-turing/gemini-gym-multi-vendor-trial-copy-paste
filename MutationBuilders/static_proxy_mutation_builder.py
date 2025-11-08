import json
import os
import shutil
import ast
import re
import textwrap
import sys
import logging
from tqdm import tqdm

logging = logging.getLogger("mutation_engine")

class StaticProxyMutationBuilder: # pragma: no cover
    """
    Generates a "proxy" mutation for a service.
    Instead of refactoring the original function body, this creates a new 
    function that calls the original with the renamed arguments.
    """
    def __init__(self, service_name, config_name, regenerate=True, include_original_functions=True, include_unmutated_functions=False):
        self.service_name = service_name
        self.config_name = config_name
        self.regenerate = regenerate
        self.include_original_functions = include_original_functions
        self.include_unmutated_functions = include_unmutated_functions
        self.api_root_dir = os.path.abspath(os.path.join('APIs', self.service_name))
        
        config_path = os.path.join(self.api_root_dir, 'SimulationEngine', 'static_mutation_configs', f"{config_name}.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.mutation_name = self.config['mutation_name']
        self.mutation_path = os.path.join(self.api_root_dir, 'mutations', self.mutation_name)

    def _setup_directories(self):
        if os.path.exists(self.mutation_path):
            shutil.rmtree(self.mutation_path)
        os.makedirs(self.mutation_path)

    def _get_api_details(self):
        """
        Parse the API's __init__.py and all referenced modules (including __init__.py in subfolders)
        to extract function signatures and docstrings for all functions referenced in _function_map.
        Handles both direct .py files and folder-based modules with __init__.py.
        """
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

        original_function_map = ast.literal_eval(function_map_node)

        for tool_name, func_path in original_function_map.items():
            path_parts = func_path.split('.')
            if len(path_parts) > 2:
                actual_func_name = path_parts[-1]
                module_path_parts = path_parts[1:-1]
                # Try to resolve to a .py file first
                relative_file_path = os.path.join(*module_path_parts) + ".py"
                file_path = os.path.join(self.api_root_dir, relative_file_path)
                full_module_path = '.'.join(path_parts[:-1])

                found = False
                if os.path.exists(file_path):
                    # It's a .py file
                    with open(file_path, 'r') as f:
                        module_content = f.read()
                    module_tree = ast.parse(module_content)
                    found = True
                else:
                    # Try as a package with __init__.py
                    relative_folder_path = os.path.join(*module_path_parts)
                    init_file_path = os.path.join(self.api_root_dir, relative_folder_path, '__init__.py')
                    if os.path.exists(init_file_path):
                        with open(init_file_path, 'r') as f:
                            module_content = f.read()
                        module_tree = ast.parse(module_content)
                        # For clarity, set the file path to the __init__.py
                        relative_file_path = os.path.join(relative_folder_path, '__init__.py')
                        found = True

                if found:
                    for func_node in ast.walk(module_tree):
                        if isinstance(func_node, ast.FunctionDef) and func_node.name == actual_func_name:
                            # --- Begin: Extract default values and argument order ---
                            args = []
                            # Handle all argument types, including positional, *, kwonly, vararg, kwarg
                            func_args = func_node.args
                            # Positional args (before *)
                            pos_args = func_args.args
                            # kwonly args (after *)
                            kwonly_args = func_args.kwonlyargs
                            # Defaults for positional args
                            pos_defaults = func_args.defaults
                            # Defaults for kwonly args
                            kw_defaults = func_args.kw_defaults
                            # *args and **kwargs
                            vararg = func_args.vararg
                            kwarg = func_args.kwarg

                            # Map positional args to their defaults
                            num_pos_args = len(pos_args)
                            num_pos_defaults = len(pos_defaults)
                            for i, arg in enumerate(pos_args):
                                arg_name = arg.arg
                                if i >= num_pos_args - num_pos_defaults:
                                    default_value_node = pos_defaults[i - (num_pos_args - num_pos_defaults)]
                                    try:
                                        default_value = ast.literal_eval(default_value_node)
                                    except Exception:
                                        default_value = None
                                    args.append({'name': arg_name, 'default': default_value, 'default_node': default_value_node, 'kind': 'positional'})
                                else:
                                    args.append({'name': arg_name, 'default': None, 'default_node': None, 'kind': 'positional'})

                            # Handle the star marker for keyword-only arguments
                            if (kwonly_args or vararg or kwarg) and (not getattr(func_args, "posonlyargs", None) or len(getattr(func_args, "posonlyargs", [])) == 0):
                                # Insert '*' marker if there are kwonlyargs and no posonlyargs
                                args.append({'name': '*', 'default': None, 'default_node': None, 'kind': 'star'})

                            # Keyword-only args (after *)
                            for i, arg in enumerate(kwonly_args):
                                arg_name = arg.arg
                                default_value_node = kw_defaults[i]
                                if default_value_node is not None:
                                    try:
                                        default_value = ast.literal_eval(default_value_node)
                                    except Exception:
                                        default_value = None
                                else:
                                    default_value = None
                                args.append({'name': arg_name, 'default': default_value, 'default_node': default_value_node, 'kind': 'kwonly'})

                            # *args
                            if vararg is not None:
                                args.append({'name': vararg.arg, 'default': None, 'default_node': None, 'kind': 'vararg'})

                            # **kwargs
                            if kwarg is not None:
                                args.append({'name': kwarg.arg, 'default': None, 'default_node': None, 'kind': 'kwarg'})

                            signatures[tool_name] = {
                                'args': args,  # List of dicts: {'name', 'default', 'default_node', 'kind'}
                                'file': relative_file_path,
                                'module': full_module_path,
                                'docstring': ast.get_docstring(func_node),
                                'actual_func_name': actual_func_name  # Add the real function name for import
                            }
        return signatures, original_function_map

    def _refactor_docstring(self, docstring_content, arg_map):
        if not docstring_content:
            return '"""TODO: Add docstring."""'
            
        lines = docstring_content.split('\n')
        new_lines = []
        in_args_section = False
        in_raises_section = False
        
        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith('Args:'):
                in_args_section = True
                in_raises_section = False
            elif stripped_line.startswith('Raises:'):
                in_args_section = False
                in_raises_section = True
            elif not line.startswith(' ') and stripped_line:
                in_args_section = False
                in_raises_section = False

            modified_line = line
            if in_args_section:
                for old_arg, new_arg in arg_map.items():
                    pattern = r'^(\s+)' + re.escape(old_arg) + r'(\s*[:(])'
                    if re.match(pattern, modified_line):
                        modified_line = re.sub(pattern, r'\1' + new_arg + r'\2', modified_line, 1)
                        break 
            elif in_raises_section:
                for old_arg, new_arg in arg_map.items():
                    pattern = r'\b' + re.escape(old_arg) + r'\b'
                    modified_line = re.sub(pattern, new_arg, modified_line)

            new_lines.append(modified_line)
            
        dedented_content = textwrap.dedent("\n".join(new_lines)).strip()
        return f'"""\n{dedented_content}\n"""'

    def _ast_node_to_source(self, node):
        """
        Convert an AST node representing a default value to its source code representation.
        """
        # Python 3.9+ has ast.unparse
        try:
            import ast
            if hasattr(ast, "unparse"):
                return ast.unparse(node)
        except Exception:
            pass
        # Fallback for simple literals
        try:
            return repr(ast.literal_eval(node))
        except Exception:
            return "..."  # fallback for complex defaults

    def _generate_proxy_function(self, func_config, original_info):
        original_name = func_config['original_name']
        new_name = func_config['new_name']

        # Build mapping from original arg name to new arg name
        arg_map = {arg['original_name']: arg['new_name'] for arg in func_config.get('args', [])}

        # Build a mapping from new arg name to original arg name for reverse lookup
        new_to_original = {arg['new_name']: arg['original_name'] for arg in func_config.get('args', [])}

        # Get the original argument list with default values and kinds
        original_args = original_info['args']  # List of dicts: {'name', 'default', 'default_node', 'kind'}

        # Build the new argument list, preserving order, default values, and special markers
        new_args_with_defaults = []
        for orig_arg in original_args:
            kind = orig_arg.get('kind')
            orig_name = orig_arg['name']
            if kind == 'star':
                new_args_with_defaults.append('*')
                continue
            if kind == 'vararg':
                # *args
                new_args_with_defaults.append(f"*{orig_name}")
                continue
            if kind == 'kwarg':
                # **kwargs
                new_args_with_defaults.append(f"**{orig_name}")
                continue
            if orig_name in arg_map:
                new_name = arg_map[orig_name]
                if orig_arg['default_node'] is not None:
                    default_src = self._ast_node_to_source(orig_arg['default_node'])
                    new_args_with_defaults.append(f"{new_name}={default_src}")
                else:
                    new_args_with_defaults.append(f"{new_name}")
            # else: skip arguments not in mutation config

        # Build the function signature
        if len(', '.join(new_args_with_defaults)) > 80:
            args_str = ",\n    ".join(new_args_with_defaults)
            new_signature = f"def {func_config['new_name']}(\n    {args_str}\n):"
        else:
            new_signature = f"def {func_config['new_name']}({', '.join(new_args_with_defaults)}):"

        docstring = self._refactor_docstring(original_info.get('docstring'), arg_map)

        # Build the call argument list for the original function
        call_args_list = []
        for orig_arg in original_args:
            kind = orig_arg.get('kind')
            orig_name = orig_arg['name']
            if kind == 'star':
                continue  # not an argument
            if kind == 'vararg':
                call_args_list.append(f"*{orig_name}")
                continue
            if kind == 'kwarg':
                call_args_list.append(f"**{orig_name}")
                continue
            if orig_name in arg_map:
                new_name = arg_map[orig_name]
                call_args_list.append(f"{orig_name}={new_name}")

        # Use the actual function name for the call and import
        actual_func_name = original_info.get('actual_func_name', func_config['original_name'])

        # Use lazy import to avoid circular import issues
        lazy_import = f"    from {original_info['module']} import {actual_func_name}"
        
        if len(f"    return {actual_func_name}({', '.join(call_args_list)})") > 100:
            call_args_str = ",\n        ".join(call_args_list)
            function_body = f"{lazy_import}\n    return {actual_func_name}(\n        {call_args_str}\n    )"
        else:
            function_body = f"{lazy_import}\n    return {actual_func_name}({', '.join(call_args_list)})"

        # No top-level import statement needed since we use lazy imports
        full_proxy_code = f"{new_signature}\n{textwrap.indent(docstring, '    ')}\n{function_body}\n"
        
        return full_proxy_code

    def _process_files(self, signatures, functions_to_mutate):
        files_to_create = {}

        for func_config in functions_to_mutate:
            original_func_name = func_config['original_name']
            if original_func_name in signatures:
                original_info = signatures[original_func_name]
                original_file_name = original_info['file']

                proxy_code = self._generate_proxy_function(func_config, original_info)
                
                if original_file_name not in files_to_create:
                    files_to_create[original_file_name] = []
                
                files_to_create[original_file_name].append(proxy_code)

        for file_name, proxy_codes in files_to_create.items():
            dest_path = os.path.join(self.mutation_path, file_name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write("# This file is automatically generated by the MutationBuilder\n\n")
                f.write('\n\n'.join(proxy_codes))

    def _create_init_file(self, signatures, original_function_map, functions_to_mutate):
        imports = {}
        for func in functions_to_mutate:
            original_func_name = func['original_name']
            if original_func_name in signatures:
                original_file_base = signatures[original_func_name]['file'].replace('.py', '').replace(os.sep, '.')
                if original_file_base not in imports:
                    imports[original_file_base] = []
                imports[original_file_base].append(func['new_name'])

        init_content = ''
        for file_base, func_names in sorted(imports.items()):
            init_content += f"from .{file_base} import {', '.join(sorted(func_names))}\n"
        if init_content:
            init_content += '\n'
        
        mutated_function_map = {}
        for func in functions_to_mutate:
            original_func_name = func['original_name']
            if original_func_name in signatures:
                original_file_base = signatures[original_func_name]['file'].replace('.py', '').replace(os.sep, '.')
                mutated_function_map[func['new_name']] = f"{self.service_name}.mutations.{self.mutation_name}.{original_file_base}.{func['new_name']}"

        # Get the set of mutated function names
        mutated_original_names = {func['original_name'] for func in functions_to_mutate}

        # Check for name collisions
        if self.include_original_functions or self.include_unmutated_functions:
            mutated_keys = set(mutated_function_map.keys())
            original_keys = set(original_function_map.keys())
            common_keys = mutated_keys.intersection(original_keys)
            if common_keys:
                raise ValueError(f"Function name collision detected in '{self.service_name}' mutation '{self.mutation_name}': {', '.join(common_keys)}")

        final_content = init_content

        # Build the final function map
        final_content += '_function_map = {\n'
        
        # Add mutated functions first
        for name, path in sorted(mutated_function_map.items()):
            final_content += f"    '{name}': '{path}',\n"
        
        # Add original functions if flag is set
        if self.include_original_functions:
            for name, path in sorted(original_function_map.items()):
                final_content += f"    '{name}': '{path}',\n"
        
        # Add unmutated functions if flag is set (functions that exist in original but have no mutation)
        if self.include_unmutated_functions:
            for name, path in sorted(original_function_map.items()):
                if name not in mutated_original_names:
                    final_content += f"    '{name}': '{path}',\n"
        
        final_content += '}\n'
        
        with open(os.path.join(self.mutation_path, '__init__.py'), 'w') as f:
            f.write(final_content)

    def build(self):
        if not self.regenerate and os.path.exists(self.mutation_path):
            logging.info(f"Proxy Mutation '{self.mutation_name}' already exists at: {self.mutation_path}. Skipping.")
            return

        self._setup_directories()
        signatures, original_function_map = self._get_api_details()

        valid_function_names = signatures.keys()
        filtered_functions_config = [
            func for func in self.config['functions']
            if func['original_name'] in valid_function_names
        ]

        self._process_files(signatures, filtered_functions_config)
        self._create_init_file(signatures, original_function_map, filtered_functions_config)
        logging.info(f"Proxy Mutation '{self.mutation_name}' created successfully at: {self.mutation_path}")


if __name__ == '__main__': # pragma: no cover
    # --- Configuration ---
    REGENERATE_PROXIES = True  # Set to False to skip existing mutation directories
    INCLUDE_ORIGINAL_FUNCTIONS = False
    INCLUDE_UNMUTATED_FUNCTIONS = True  # New flag to include functions without mutations
    MUTATION_NAME = "m01"
    # -------------------

    all_services = [d for d in os.listdir('APIs') if os.path.isdir(os.path.join('APIs', d))]
    all_services.remove('common_utils')

    api_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'APIs'))
    sys.path.insert(0, api_dir)

    for service in tqdm(["retail"], desc="Building proxy mutations", unit="service"):
        logging.info(f"--- Building proxy mutation for service: {service} ---")
        try:
            builder = StaticProxyMutationBuilder(
                service_name=service, 
                config_name=MUTATION_NAME,
                regenerate=REGENERATE_PROXIES,
                include_original_functions=INCLUDE_ORIGINAL_FUNCTIONS,
                include_unmutated_functions=INCLUDE_UNMUTATED_FUNCTIONS
            )
            builder.build()
            logging.info(f"--- Successfully built proxy mutation for {service} ---\n")
        except FileNotFoundError:
            logging.warning(f"No {MUTATION_NAME} config found for {service}, skipping proxy generation.")
        except Exception as e:
            logging.error(f"An unexpected error occurred for {service}: {e}\n")