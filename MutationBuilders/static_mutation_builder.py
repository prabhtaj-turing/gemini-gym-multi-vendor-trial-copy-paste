# NOTE: This file is NOT used as of now due to some issues with the code.

import json
import os
import shutil
import ast
import re
import libcst as cst
from libcst.metadata import ParentNodeProvider
import sys

class StaticMutationBuilder: # pragma: no cover
    """
    Generates a mutation for a service by refactoring tool and test files
    based on a given JSON configuration.
    """
    def __init__(self, service_name, config_name):
        self.service_name = service_name
        self.config_name = config_name
        self.api_root_dir = os.path.abspath(os.path.join('APIs', self.service_name))
        
        config_path = os.path.join(self.api_root_dir, 'SimulationEngine', 'static_mutation_configs', f"{config_name}.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.mutation_name = self.config['mutation_name']
        self.mutation_path = os.path.join(self.api_root_dir, 'mutations', self.mutation_name)
        self.tests_path = os.path.join(self.mutation_path, 'tests')

    def _setup_directories(self):
        if os.path.exists(self.mutation_path):
            shutil.rmtree(self.mutation_path)
        os.makedirs(self.mutation_path)

    def _get_function_map(self):
        function_map = {}
        init_path = os.path.join(self.api_root_dir, '__init__.py')
        with open(init_path, 'r') as f:
            init_content = f.read()
            try:
                tree = ast.parse(init_content, filename=init_path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == '_function_map':
                                if isinstance(node.value, ast.Dict):
                                    for key_node, val_node in zip(node.value.keys, node.value.values):
                                        if isinstance(key_node, ast.Constant) and isinstance(val_node, ast.Constant):
                                            key = key_node.value
                                            val = val_node.value
                                            val_parts = val.split('.')
                                            if len(val_parts) > 2:
                                                full_module_path = '.'.join(val_parts[:-1])
                                                relative_file_path = os.path.join(*val_parts[1:-1]) + ".py"
                                                function_map[key] = {'file': relative_file_path, 'module': full_module_path}
            except Exception as e:
                raise RuntimeError(f"Failed to parse {init_path} for _function_map: {e}")
        return function_map

    def _run_codemod(self, file_path, transformer):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = cst.parse_module(source_code)
            wrapper = cst.MetadataWrapper(tree)
            modified_tree = wrapper.visit(transformer)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_tree.code)
        except cst.ParserSyntaxError as e:
            print(f"\n--- CST PARSE ERROR ---")
            print(f"Failed to parse file: {file_path}")
            print(f"Transformer: {transformer.__class__.__name__}")
            print(f"LibCST Error: {e}")
            print(f"-----------------------\n")
            raise
        except Exception as e:
            print(f"\n--- CODEMOD ERROR ---")
            print(f"An error occurred while processing file: {file_path}")
            print(f"Transformer: {transformer.__class__.__name__}")
            print(f"Error: {e}")
            print(f"---------------------\n")
            raise

    def _process_files(self, function_map, functions_to_mutate):
        files_to_process = []

        # Collect and copy tool files
        for func_config in functions_to_mutate:
            original_func_name = func_config['original_name']
            if original_func_name in function_map:
                original_file = function_map[original_func_name]['file']
                source_path = os.path.join(self.api_root_dir, original_file)
                dest_path = os.path.join(self.mutation_path, original_file)
                if os.path.exists(source_path) and (source_path, dest_path) not in files_to_process:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy(source_path, dest_path)
                    files_to_process.append((source_path, dest_path))

        # Collect and copy test files
        source_tests_path = os.path.join(self.api_root_dir, 'tests')
        if os.path.exists(source_tests_path):
            if not os.path.exists(self.tests_path):
                 shutil.copytree(source_tests_path, self.tests_path, dirs_exist_ok=True)

            for root, _, files in os.walk(source_tests_path):
                for file in files:
                    if file.endswith('.py'):
                        source_file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(source_file_path, source_tests_path)
                        dest_file_path = os.path.join(self.tests_path, relative_path)
                        if (source_file_path, dest_file_path) not in files_to_process:
                            files_to_process.append((source_file_path, dest_file_path))
        
        # STEP 1: Resolve all imports
        for source_path, dest_path in files_to_process:
            resolver = ImportResolver(self.service_name, function_map, source_path, self.api_root_dir)
            self._run_codemod(dest_path, resolver)

        # STEP 2: Apply mutations
        for _, dest_path in files_to_process:
            mutator = RenameFunctionAndArgs(functions_to_mutate, self.service_name, self.mutation_name, function_map)
            self._run_codemod(dest_path, mutator)

    def _create_init_file(self, function_map, functions_to_mutate):
        imports = {}
        for func in functions_to_mutate:
            original_func_name = func['original_name']
            if original_func_name in function_map:
                original_file_base = function_map[original_func_name]['file'].replace('.py', '').replace(os.sep, '.')
                if original_file_base not in imports:
                    imports[original_file_base] = []
                imports[original_file_base].append(func['new_name'])

        init_content = ''
        for file_base, func_names in sorted(imports.items()):
            init_content += f"from .{file_base} import {', '.join(sorted(func_names))}\n"
        if init_content:
            init_content += '\n'
        
        function_map_content = '_function_map = {\n'
        sorted_functions = sorted(functions_to_mutate, key=lambda x: x['new_name'])
        for func in sorted_functions:
            original_func_name = func['original_name']
            if original_func_name in function_map:
                original_file_base = function_map[original_func_name]['file'].replace('.py', '').replace(os.sep, '.')
                function_map_content += f"    '{func['new_name']}': '{self.service_name}.mutations.{self.mutation_name}.{original_file_base}.{func['new_name']}',\n"
        function_map_content += '}\n'
        
        with open(os.path.join(self.mutation_path, '__init__.py'), 'w') as f:
            f.write(init_content + function_map_content)

    def build(self):
        self._setup_directories()
        function_map = self._get_function_map()

        valid_function_names = function_map.keys()
        filtered_functions_config = [
            func for func in self.config['functions']
            if func['original_name'] in valid_function_names
        ]

        self._process_files(function_map, filtered_functions_config)
        self._create_init_file(function_map, filtered_functions_config)
        print(f"Mutation '{self.mutation_name}' created successfully at: {self.mutation_path}")


class ImportResolver(cst.CSTTransformer): # pragma: no cover
    def __init__(self, service_name, function_map, original_file_path, api_root_dir):
        self.service_name = service_name
        self.function_map = function_map
        self.original_file_path = original_file_path
        self.api_root_dir = api_root_dir

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        if not original_node.relative:
            return updated_node

        if not original_node.module:
            if not isinstance(original_node.names, cst.ImportStar):
                target_module = None
                all_names_in_same_module = True
                for name_node in updated_node.names:
                    func_name = name_node.name.value
                    if func_name in self.function_map:
                        module_of_func = self.function_map[func_name]['module']
                        if target_module is None:
                            target_module = module_of_func
                        elif target_module != module_of_func:
                            all_names_in_same_module = False
                            break
                    else:
                        all_names_in_same_module = False
                        break
                
                if all_names_in_same_module and target_module:
                    new_module_node = cst.parse_expression(target_module)
                    return updated_node.with_changes(module=new_module_node, relative=[])

        original_dir = os.path.dirname(self.original_file_path)
        level = len(original_node.relative)
        
        base_path = original_dir
        for _ in range(level - 1):
            base_path = os.path.dirname(base_path)
        
        path_parts = []
        if original_node.module:
            module_str = cst.Module([cst.Expr(original_node.module)]).code.strip()
            path_parts = module_str.split('.')
        
        imported_module_path = os.path.normpath(os.path.join(base_path, *path_parts))
        
        if not imported_module_path.startswith(self.api_root_dir):
            return updated_node

        relative_to_root = os.path.relpath(imported_module_path, self.api_root_dir)
        
        if os.path.isdir(imported_module_path):
            module_path_parts = relative_to_root.split(os.sep)
        else:
            module_path_parts = os.path.splitext(relative_to_root)[0].split(os.sep)

        if module_path_parts == ['.'] or module_path_parts == ['']:
            new_module_str = self.service_name
        else:
            new_module_str = f"{self.service_name}.{'.'.join(module_path_parts)}"

        new_module_node = cst.parse_expression(new_module_str)
        return updated_node.with_changes(module=new_module_node, relative=[])


class RenameFunctionAndArgs(cst.CSTTransformer): # pragma: no cover
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, functions_config, service_name, mutation_name, function_map):
        super().__init__()
        self.functions_config = {item['original_name']: item for item in functions_config}
        self.new_name_to_orig_config = {item['new_name']: item for item in functions_config}
        self.service_name = service_name
        self.mutation_name = mutation_name
        self.function_map = function_map
        self.mutated_modules = {
            path['module'].split('.')[1]
            for func_config in self.functions_config.values()
            for func_name, path in function_map.items()
            if func_config['original_name'] == func_name
        }
        self.current_function_config = None
        self.arg_map = {}

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        if node.name.value in self.functions_config:
            self.current_function_config = self.functions_config[node.name.value]
            self.arg_map = {arg['original_name']: arg['new_name'] for arg in self.current_function_config.get('args', [])}
        return True

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        if original_node.name.value in self.functions_config:
            config = self.functions_config[original_node.name.value]
            changes = {"name": cst.Name(config['new_name'])}
            
            if self.arg_map:
                changes["params"] = updated_node.params.with_changes(
                    params=tuple(
                        p.with_changes(name=cst.Name(self.arg_map[p.name.value])) if p.name.value in self.arg_map else p
                        for p in updated_node.params.params
                    )
                )
                if (body := updated_node.body) and body.body:
                    first_stmt = body.body[0]
                    if (isinstance(first_stmt, cst.SimpleStatementLine) and first_stmt.body and
                        isinstance(first_stmt.body[0], cst.Expr) and isinstance(first_stmt.body[0].value, cst.SimpleString)):
                        docstring_node = first_stmt.body[0].value
                        try:
                            docstring_content = ast.literal_eval(docstring_node.value)
                            new_docstring_content = self._refactor_docstring(docstring_content, self.arg_map)
                            if new_docstring_content != docstring_content:
                                quotes = '"""' if '"""' in docstring_node.value else "'''"
                                new_docstring_literal = f"{quotes}{new_docstring_content}{quotes}"
                                new_string_node = cst.SimpleString(value=new_docstring_literal)
                                changes["body"] = body.with_changes(body=(first_stmt.with_changes(body=(first_stmt.body[0].with_changes(value=new_string_node),)),) + body.body[1:])
                        except Exception:
                            pass

            self.current_function_config = None
            self.arg_map = {}
            return updated_node.with_changes(**changes)
        return updated_node

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
        parent = self.get_metadata(ParentNodeProvider, original_node)

        if original_node.value in self.functions_config:
            if not isinstance(parent, (cst.FunctionDef, cst.ImportAlias, cst.Attribute)):
                new_name = self.functions_config[original_node.value]['new_name']
                return updated_node.with_changes(value=new_name)

        if self.current_function_config and original_node.value in self.arg_map:
            if isinstance(parent, cst.Attribute) and parent.attr == original_node:
                return updated_node
            return updated_node.with_changes(value=self.arg_map[original_node.value])

        return updated_node

    @staticmethod
    def _refactor_docstring(docstring_content, arg_map):
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
            
        return '\n'.join(new_lines)

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        if original_node.relative:
            return updated_node 

        module_node = updated_node.module
        if module_node is None:
            return updated_node

        module_str = cst.Module([cst.Expr(module_node)]).code.strip()
        if not module_str.startswith(self.service_name):
            return updated_node

        if f"{self.service_name}.SimulationEngine" in module_str:
            return updated_node

        new_module_str = None
        if module_str == self.service_name:
            if any(isinstance(name, cst.ImportAlias) and name.name.value in self.mutated_modules for name in updated_node.names):
                new_module_str = f"{self.service_name}.mutations.{self.mutation_name}"
        elif isinstance(updated_node.names, cst.ImportStar):
            if module_str.split('.')[-1] in self.mutated_modules:
                rest = module_str[len(self.service_name) + 1:]
                new_module_str = f"{self.service_name}.mutations.{self.mutation_name}.{rest}"
        
        if new_module_str:
            return updated_node.with_changes(module=cst.parse_expression(new_module_str))

        new_names = [
            name.with_changes(name=cst.Name(self.functions_config[name.name.value]['new_name']))
            if isinstance(name, cst.ImportAlias) and name.name.value in self.functions_config else name
            for name in updated_node.names
        ]
        if new_names != list(updated_node.names):
            if module_str == self.service_name:
                new_module_str = f"{self.service_name}.mutations.{self.mutation_name}"
            else:
                rest = module_str[len(self.service_name) + 1:]
                new_module_str = f"{self.service_name}.mutations.{self.mutation_name}.{rest}"
            return updated_node.with_changes(module=cst.parse_expression(new_module_str), names=tuple(new_names))

        return updated_node

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        func_name = ""
        if isinstance(original_node.func, cst.Name):
            func_name = original_node.func.value
        elif isinstance(original_node.func, cst.Attribute):
            func_name = original_node.func.attr.value

        # Case 1: Direct call to a mutated function
        if func_name in self.functions_config:
            config = self.functions_config[func_name]
            arg_map = {arg['original_name']: arg['new_name'] for arg in config.get('args', [])}
            changes = {}
            
            if arg_map:
                changes["args"] = tuple(
                    arg.with_changes(keyword=cst.Name(arg_map[arg.keyword.value]))
                    if arg.keyword and arg.keyword.value in arg_map else arg
                    for arg in updated_node.args
                )

            new_func_name = config['new_name']
            if isinstance(original_node.func, cst.Name):
                changes["func"] = cst.Name(new_func_name)
            elif isinstance(original_node.func, cst.Attribute):
                changes["func"] = updated_node.func.with_changes(attr=cst.Name(new_func_name))
            
            if changes:
                return updated_node.with_changes(**changes)

        # Case 2: Call to assert_error_behavior
        if "assert_error_behavior" in func_name and updated_node.args:
            func_under_test_node = updated_node.args[0].value
            if isinstance(func_under_test_node, cst.Name):
                func_under_test_new_name = func_under_test_node.value
                
                func_config = self.new_name_to_orig_config.get(func_under_test_new_name)
                
                if func_config:
                    arg_map = {arg['original_name']: arg['new_name'] for arg in func_config.get('args', [])}
                    if arg_map:
                        new_args = list(updated_node.args)
                        changed = False
                        for i, arg in enumerate(new_args):
                            if arg.keyword and arg.keyword.value in arg_map:
                                new_args[i] = arg.with_changes(keyword=cst.Name(arg_map[arg.keyword.value]))
                                changed = True
                        
                        if changed:
                            return updated_node.with_changes(args=tuple(new_args))

        # Case 3: Call to patch
        if "patch" in func_name and updated_node.args:
            arg = updated_node.args[0]
            if isinstance(arg.value, cst.SimpleString):
                path = arg.value.value.strip("'\"")
                for func, config in self.functions_config.items():
                    if path.endswith(f".{func}"):
                        base, _, _ = path.rpartition('.')
                        new_base = f"{self.service_name}.mutations.{self.mutation_name}.{base[len(self.service_name)+1:]}"
                        new_path = f"'{new_base}.{config['new_name']}'"
                        return updated_node.with_changes(args=(arg.with_changes(value=cst.SimpleString(new_path)),) + updated_node.args[1:])
        
        return updated_node

if __name__ == '__main__': # pragma: no cover
    # --- Configuration ---
    SERVICES_TO_PROCESS = ["azure"] 
    MUTATION_NAME = "m01"
    # -------------------
    
    sys.path.insert(0, os.path.abspath('APIs'))

    for service in SERVICES_TO_PROCESS:
        print(f"--- Building mutation for service: {service} ---")
        try:
            builder = StaticMutationBuilder(service_name=service, config_name=MUTATION_NAME)
            builder.build()
            print(f"--- Successfully built mutation for {service} ---\n")
        except FileNotFoundError as e:
            print(f"Error building mutation for {service}: {e}\n")
        except Exception as e:
            print(f"An unexpected error occurred for {service}: {e}\n")