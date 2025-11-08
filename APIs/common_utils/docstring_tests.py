from common_utils.print_log import print_log
"""
Docstring tests for API modules.

This module provides a unittest test case to validate the structure of docstrings for functions
exposed in a package's _function_map.

For individual API docstring tests, use the test_docstrings.py script which executes this module.
"""
#%%
from datetime import datetime
import os
import ast
import unittest
import docstring_parser
import csv
import glob
import tempfile
import json
from typing import List, Tuple, Dict, Optional
import re

# Import FCSpec with absolute path
import sys

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Scripts')
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from FCSpec import process_single_function

# Import schema validator
SCHEMA_VALIDATOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Scripts')
if SCHEMA_VALIDATOR_DIR not in sys.path:
    sys.path.insert(0, SCHEMA_VALIDATOR_DIR)

from schema_validator import validate_single_schema_file

# This script is now designed to be run directly.
# The configuration is handled in the `if __name__ == "__main__"` block.
google_gen_ai_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
REPORTS_DIR = os.path.join(google_gen_ai_dir, "docstring_reports")

class TestDocstringStructure(unittest.TestCase):
    """
    A unittest test case to validate the structure of docstrings for functions
    exposed in a package's _function_map.
    This class is dynamically configured by the main runner.
    """
    # --- Class-level variables to be populated by the runner ---
    package_path: Optional[str] = None
    function_map: Dict[str, str] = {}
    package_root: Optional[str] = None
    package_name: Optional[str] = None
    reports_dir: Optional[str] = REPORTS_DIR  # Directory for individual CSV reports

    # --- Constants ---
    _FAILED_PARSE_KEYWORDS = [
        "Args:", "Arguments:", "Parameters:",
        "Returns:", "Raises:", "Yields:"
    ]

    @classmethod
    def setUpClass(cls):
        """
        Set up the test environment for a specific package.
        This runs once before all tests in the class for the configured package.
        It locates the package, ensures it's valid, and loads the _function_map.
        """
        if not cls.package_path or not os.path.isdir(cls.package_path):
            raise FileNotFoundError(f"Package directory for testing not found or not configured: '{cls.package_path}'")

        cls.package_root = os.path.dirname(os.path.abspath(cls.package_path))
        cls.package_name = os.path.basename(cls.package_path)

        init_path = os.path.join(cls.package_path, "__init__.py")
        if not os.path.isfile(init_path):
            raise FileNotFoundError(f"__init__.py not found in test package '{cls.package_path}'")

        cls.function_map = cls._get_variable_from_file(init_path, "_function_map")
        if not isinstance(cls.function_map, dict) or not cls.function_map:
            # This will cause tests to be skipped for this class instance, which is desired.
            cls.function_map = {}
            print_log(f"WARNING: Could not find a valid '_function_map' in '{init_path}'. Skipping package '{cls.package_name}'.")

    def test_docstring_structures(self):
        """
        Validates every function in the _function_map for the configured package.
        This test will fail with a summary of all docstring issues for the package.
        """
        if not self.function_map:
            self.skipTest(f"No functions to test for package '{self.package_name}'.")

        failed_functions = []
        total_functions = len(self.function_map)
        
        for public_name, fqn in self.function_map.items():
            try:
                self._test_single_function_docstring(public_name, fqn)
            except AssertionError as e:
                failed_functions.append((public_name, fqn, str(e)))
        
        # Generate the individual CSV report for this package
        self._generate_csv_report(failed_functions, total_functions)
        
        # Provide a summary failure message if any tests failed
        if failed_functions:
            message = f"\n\nDocstring validation summary for '{self.package_name}': {len(failed_functions)}/{total_functions} functions failed:"
            for public_name, fqn, error in failed_functions:
                message += f"\n\n{public_name} ({fqn}):\n{error}"
            message += f"\n\nTotal failures for this package: {len(failed_functions)} out of {total_functions} functions"
            self.fail(message)

    def test_docstring_to_fc_schema(self):
        """
        Validates that all type specifications in docstrings have proper parentheses.
        This test checks for missing parentheses where types are specified before ":" but not in parentheses.
        """
        if not self.function_map:
            self.skipTest(f"No functions to test for package '{self.package_name}'.")

        # Use a dictionary to track failures per function to avoid duplicates
        function_failures = {}  # {function_name: {fqn: str, errors: List[str]}}
        total_functions = len(self.function_map)
        
        for public_name, fqn in self.function_map.items():
            # Initialize function entry if not exists
            if public_name not in function_failures:
                function_failures[public_name] = {'fqn': fqn, 'errors': []}
            
            # Test FC schema generation for the function
            try:
                self._test_single_function_fc_schema(public_name, fqn)
            except AssertionError as e:
                function_failures[public_name]['errors'].append(f"Docstring validation:\n  {str(e)}")

            # Generate FC schema for the function
            try:
                schema = process_single_function((public_name, fqn, self.package_root))
                if schema is None:
                    function_failures[public_name]['errors'].append("Schema generation failed")
                else:
                    # Find invalid array definitions in the schema
                    if "parameters" in schema and "properties" in schema["parameters"]:
                        invalid_params = self.find_invalid_array_definitions(schema["parameters"]["properties"])
                        if invalid_params:
                            function_failures[public_name]['errors'].append(f"Invalid schema: missing 'items' property in arrays: {invalid_params}")

            except Exception as e:
                function_failures[public_name]['errors'].append(f"Schema generation exception: {str(e)}")
        
        # Filter out functions with no errors
        failed_functions = {name: data for name, data in function_failures.items() if data['errors']}
        
        # Provide a summary failure message if any tests failed
        if failed_functions:
            failed_count = len(failed_functions)
            message = self._build_failure_summary(failed_functions, failed_count, total_functions)
            self.fail(message)

    def test_generate_and_validate_schema(self):
        """
        Generates a schema for the current package using FCSpec and validates it using schema_validator.
        This test ensures that the generated schema passes all validation checks.
        """
        if not self.function_map:
            self.skipTest(f"No functions to test for package '{self.package_name}'.")

        # Generate schemas for all functions in the package
        all_schemas = []
        failed_functions = []
        
        for public_name, fqn in self.function_map.items():
            try:
                schema = process_single_function((public_name, fqn, self.package_root))
                if schema is not None:
                    all_schemas.append(schema)
                else:
                    failed_functions.append(f"{public_name}: Schema generation failed")
            except Exception as e:
                failed_functions.append(f"{public_name}: Schema generation exception - {str(e)}")
        
        if not all_schemas:
            self.fail(f"No schemas were generated for package '{self.package_name}'. Failed functions: {failed_functions}")
        
        # Create a temporary file to store the generated schema
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(all_schemas, temp_file, indent=2, ensure_ascii=False)
            temp_file_path = temp_file.name
        
        try:
            # Validate the generated schema using schema_validator
            # Pass the package name explicitly to avoid temporary filename in error messages
            validation_errors = validate_single_schema_file(temp_file_path, self.package_name)
            
            if validation_errors:
                error_message = f"Generated schema for package '{self.package_name}' failed validation:\n"
                for i, error in enumerate(validation_errors, 1):
                    error_message += f"  {i}. {error}\n"
                
                if failed_functions:
                    error_message += f"\nAdditionally, {len(failed_functions)} functions failed schema generation:\n"
                    for failed_func in failed_functions:
                        error_message += f"  • {failed_func}\n"
                
                self.fail(error_message)
            else:
                print_log(f"✅ Generated schema for package '{self.package_name}' passed all validation checks")
                
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass  # File might already be deleted
    
    def _build_failure_summary(self, failed_functions: dict, failed_count: int, total_functions: int) -> str:
        """Builds a failure summary message for the package."""
        message = f"\n\nFC Schema validation summary for '{self.package_name}': {failed_count}/{total_functions} functions failed:"
        for func_name, func_data in failed_functions.items():
            message += f"\n\n{func_name} ({func_data['fqn']}):"
            for error in func_data['errors']:
                # Clean up the error message formatting
                error_lines = error.strip().split('\n')
                for line in error_lines:
                    if line.strip():  # Only add non-empty lines
                        message += f"\n  {line.strip()}"
        return message


    def _generate_csv_report(self, failed_functions: List[Tuple[str, str, str]], total_functions: int):
        """
        Generates a CSV report of docstring validation results for the current package.
        """
        if not self.reports_dir:
            print_log("WARNING: Reports directory not set. Skipping CSV generation.")
            return

        os.makedirs(self.reports_dir, exist_ok=True)
        
        csv_filename = os.path.join(self.reports_dir, f"docstring_validation_{self.package_name}.csv")
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Service', 'Function_Name', 'Full_Path', 'Function_Source', 'Status', 'Error_Count', 'Error_Details']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            all_functions = set(self.function_map.keys())
            failed_function_names = {item[0] for item in failed_functions}

            # Write failed functions
            for public_name, fqn, error in failed_functions:
                error_lines = [line.strip() for line in error.split('\n') if line.strip() and line.strip()[0].isdigit()]
                error_count = len(error_lines) if error_lines else 1
                
                writer.writerow({
                    'Service': self.package_name,
                    'Function_Name': public_name,
                    'Full_Path': fqn,
                    'Function_Source': self._extract_function_source_text(fqn, self.package_root),
                    'Status': 'FAILED',
                    'Error_Count': error_count,
                    'Error_Details': error.replace('\n', '; ').replace('  ', ' ')
                })
            
            # # Write passed functions
            # passed_functions = all_functions - failed_function_names
            # for public_name in passed_functions:
            #     fqn = self.function_map[public_name]
            #     writer.writerow({
            #         'Service': self.package_name,
            #         'Function_Name': public_name,
            #         'Full_Path': fqn,
            #         'Function_Source': self._extract_function_source_text(fqn, self.package_root),
            #         'Status': 'PASSED',
            #         'Error_Count': 0,
            #         'Error_Details': ''
            #     })
        
        print_log(f"\n📊 Individual CSV report for '{self.package_name}' generated: {csv_filename}")

    def _test_single_function_docstring(self, public_name: str, fqn: str):
        """
        Tests a single function's docstring. This is an internal helper method.
        An AssertionError from this method is caught and aggregated.
        """
        errors = []
        source_path = self._resolve_function_source_path(fqn, self.package_root)

        if not source_path:
            errors.append("Could not resolve the source file path.")
        else:
            func_node = self._extract_specific_function_node(source_path, fqn)
            if not func_node:
                errors.append(f"Could not find function definition in '{os.path.basename(source_path)}'.")
            else:
                is_valid, validation_errors = self._validate_function_docstring(func_node, public_name)
                if not is_valid:
                    errors.extend(validation_errors)
        
        if errors:
            error_message = ""
            for i, error in enumerate(errors, 1):
                error_message += f"  {i}. {error}\n"
            # This assertion is caught by the main test method
            raise AssertionError(error_message.strip())

    def _test_single_function_fc_schema(self, public_name: str, fqn: str):
        """
        Tests a single function's docstring for FC schema compliance.
        This is an internal helper method that checks for missing parentheses in type specifications.
        An AssertionError from this method is caught and aggregated.
        """
        errors = []
        source_path = self._resolve_function_source_path(fqn, self.package_root)

        if not source_path:
            errors.append("Could not resolve the source file path.")
        else:
            func_node = self._extract_specific_function_node(source_path, fqn)
            if not func_node:
                errors.append(f"Could not find function definition in '{os.path.basename(source_path)}'.")
            else:
                is_valid, validation_errors = self._validate_function_docstring_for_fc_schema(func_node, public_name)
                if not is_valid:
                    errors.extend(validation_errors)
        
        if errors:
            error_message = ""
            for i, error in enumerate(errors, 1):
                error_message += f"  {i}. {error}\n"
            # This assertion is caught by the main test method
            raise AssertionError(error_message.strip())

    # The static helper methods (_extract_function_source_text, find_source_file, 
    # find_function_in_ast, extract_function_from_file, _validate_function_docstring,
    # _get_variable_from_file, _resolve_function_source_path, _extract_specific_function_node)
    # from the original file are unchanged and should be included here.
    # For brevity, they are omitted from this code block but are assumed to be present.

    @staticmethod
    def _extract_function_source_text(full_path, api_root):
        """
        Extract the actual function source code text from the source file.
        """
        if not full_path:
            return ''
        
        try:
            # Split the full path to get parts
            parts = full_path.split('.')
            if len(parts) < 2:
                return ''
            
            # Get function name (last part)
            function_name = parts[-1]
            
            # Get module parts (everything except function name)
            module_parts = parts[:-1]
            
            # Find the source file
            source_file = TestDocstringStructure.find_source_file(module_parts, api_root)
            if not source_file:
                return f"Source file not found for {full_path}"
            
            # Extract function text from source file
            function_text = TestDocstringStructure.extract_function_from_file(source_file, function_name, full_path)
            return function_text
            
        except Exception as e:
            return f"Error extracting function: {str(e)}"
    
    @staticmethod
    def find_source_file(module_parts, api_root):
        """
        Find the actual source file for the module.
        """
        # Try different combinations to find the source file
        for i in range(len(module_parts), 0, -1):
            potential_module = module_parts[:i]
            remaining_parts = module_parts[i:]
            
            # Build potential file paths
            potential_paths = []
            
            # Path 1: direct .py file
            if remaining_parts:
                file_path = os.path.join(api_root, *potential_module, f"{remaining_parts[0]}.py")
                potential_paths.append(file_path)
            
            # Path 2: __init__.py in module directory
            init_path = os.path.join(api_root, *potential_module, "__init__.py")
            potential_paths.append(init_path)
            
            # Path 3: module.py in parent directory
            if potential_module:
                parent_dir = os.path.join(api_root, *potential_module[:-1])
                module_file = os.path.join(parent_dir, f"{potential_module[-1]}.py")
                potential_paths.append(module_file)
            
            # Check if any of these files exist
            for path in potential_paths:
                if os.path.exists(path):
                    return path
        
        return None

    @staticmethod
    def find_function_in_ast(tree, function_name, full_path):
        """
        Find the function node in the AST.
        """
        # Split full path to understand the structure
        parts = full_path.split('.')
        
        # If it's a simple function (module.function)
        if len(parts) == 2:
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                    return node
        
        # If it's a class method (module.class.method)
        elif len(parts) == 3:
            class_name = parts[1]
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for child in node.body:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == function_name:
                            return child
        
        # If it's a nested module (module.submodule.function)
        elif len(parts) >= 3:
            # For nested modules, we need to look for the function directly
            # The function might be in the current file even if the path suggests it's nested
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                    return node
        
        return None
    
    @staticmethod
    def extract_function_from_file(source_file, function_name, full_path):
        """
        Extract the function source code text from a file.
        """
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Parse the AST
            tree = ast.parse(source_code, filename=source_file)
            
            # Find the function
            function_node = TestDocstringStructure.find_function_in_ast(tree, function_name, full_path)
            
            if function_node:
                # Get the function source code
                # We need to get the exact lines from the original source
                lines = source_code.split('\n')
                start_line = function_node.lineno - 1  # AST uses 1-based indexing
                end_line = function_node.end_lineno if hasattr(function_node, 'end_lineno') else start_line + 1
                
                # Extract the function lines
                function_lines = lines[start_line:end_line]
                return '\n'.join(function_lines)
            else:
                # Try a more flexible search - look for any function with this name
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                        lines = source_code.split('\n')
                        start_line = node.lineno - 1
                        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                        function_lines = lines[start_line:end_line]
                        return '\n'.join(function_lines)
                
                return f"Function '{function_name}' not found in {source_file}"
                
        except Exception as e:
            return f"Error reading {source_file}: {str(e)}"

    @staticmethod
    def _validate_function_docstring(node: ast.FunctionDef, func_name: str) -> Tuple[bool, List[str]]:
        """
        Performs comprehensive validation on a function's docstring.

        This version correctly handles positional, keyword-only, *args, and **kwargs,
        and forbids variable-length arguments as a preliminary check.
        It also validates the 'Returns' section against the function's return type hint.
        """
        errors = []

        # --- PRELIMINARY CHECK: Forbid *args and **kwargs ---
        if node.args.vararg:
            errors.append(f"Function uses a variable-length positional argument ('*{node.args.vararg.arg}'), which is forbidden.")
        if node.args.kwarg:
            errors.append(f"Function uses a variable-length keyword argument ('**{node.args.kwarg.arg}'), which is forbidden.")
        
        if errors:
            return False, errors # Stop immediately to prevent misleading secondary errors.
        
        docstring_text = ast.get_docstring(node)
        if not docstring_text:
            return False, ["Function is missing a docstring."]

        try:
            parsed_doc = docstring_parser.parse(docstring_text)
            full_description = ((parsed_doc.short_description or "") + "\n" + (parsed_doc.long_description or "")).strip()
            if any(keyword in full_description for keyword in TestDocstringStructure._FAILED_PARSE_KEYWORDS):
                errors.append("Potentially malformed docstring: An 'Args' or 'Returns' keyword was found in the main description, indicating a parsing failure.")

            # --- MODIFICATION: Collect all named arguments, including keyword-only ---
            sig_args = {}
            all_arg_nodes = node.args.args + node.args.kwonlyargs
            for arg_node in all_arg_nodes:
                if arg_node.arg not in ["self", "cls"]:
                    sig_args[arg_node.arg] = arg_node
            # --- END MODIFICATION ---

            doc_args_map = {param.arg_name: param for param in parsed_doc.params}

            # Check for mismatches
            missing_in_doc = set(sig_args.keys()) - set(doc_args_map.keys())
            for arg_name in missing_in_doc:
                errors.append(f"Argument '{arg_name}' is in the function signature but not documented.")
            
            extra_in_doc = set(doc_args_map.keys()) - set(sig_args.keys())
            for arg_name in extra_in_doc:
                errors.append(f"Argument '{arg_name}' is documented but not found in the function signature.")

            # For arguments that are in both, perform deeper checks
            for arg_name, sig_arg_node in sig_args.items():
                if arg_name in doc_args_map:
                    doc_param = doc_args_map[arg_name]
                    
                    if not doc_param.description:
                        errors.append(f"Documented argument '{arg_name}' is missing a description.")

                    # Type validation logic
                    sig_annotation_node = sig_arg_node.annotation
                    doc_type_str = doc_param.type_name

                    if sig_annotation_node and doc_type_str:
                        sig_type_str = ast.unparse(sig_annotation_node)
                        if sig_type_str.replace(" ", "") != doc_type_str.replace(" ", ""):
                            errors.append(f"Type mismatch for argument '{arg_name}': signature is '{sig_type_str}', docstring is '{doc_type_str}'.")
                    elif sig_annotation_node and not doc_type_str:
                        errors.append(f"Documented argument '{arg_name}' is missing a type specification (e.g., '(str)').")
                    elif not sig_annotation_node and doc_type_str:
                        errors.append(f"Argument '{arg_name}' has a type in the docstring but is missing a type hint in the function signature.")
            
            # --- VALIDATE RETURNS SECTION ---
            sig_return_node = node.returns
            doc_returns = parsed_doc.returns
            
            sig_return_type_str = None
            if sig_return_node:
                sig_return_type_str = ast.unparse(sig_return_node)

            # Scenario 1: Function signature has a return type annotation.
            if sig_return_type_str:
                if sig_return_type_str == 'None':
                    # If signature returns None, docstring can be missing or also say None.
                    # It's an error only if the docstring specifies a *different* type.
                    if doc_returns:
                        doc_type = doc_returns.type_name
                        if doc_type is not None and doc_type.lower() != 'none':
                            errors.append(f"Function is type-hinted to return 'None', but docstring specifies a return type of '{doc_type}'.")
                else:
                    # Signature has a real return type.
                    if not doc_returns:
                        errors.append("Function has a return type hint but is missing a 'Returns' section in the docstring.")
                    else:
                        if not doc_returns.type_name:
                            errors.append("The 'Returns' section in the docstring is missing a type specification.")
                        elif doc_returns.type_name.replace(" ", "") != sig_return_type_str.replace(" ", ""):
                            errors.append(f"Return type mismatch: signature is '{sig_return_type_str}', docstring is '{doc_returns.type_name}'.")
                        
                        if not doc_returns.description:
                            errors.append("The 'Returns' section is missing a description of the return value.")

            # Scenario 2: Function signature does NOT have a return type annotation.
            else:
                # Check for explicit return statements with values. This suggests a missing annotation.
                has_return_with_value = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(node))
                if has_return_with_value:
                    errors.append("Function appears to return a value but is missing a return type hint in the signature.")
                
                if doc_returns:
                    errors.append("Function has a 'Returns' section in the docstring but is missing a return type hint in the signature.")

        except Exception as e:
            errors.append(f"The docstring_parser library failed with a critical exception: {e}")
            
        return not errors, errors

    @staticmethod
    def _validate_function_docstring_for_fc_schema(node: ast.FunctionDef, func_name: str) -> Tuple[bool, List[str]]:
        """
        Performs FC schema validation on a function's docstring.

        This function uses a dynamically generated regular expression to find
        formatting errors where a type hint is not correctly enclosed in
        parentheses. It is carefully constrained to operate ONLY within the 'Args:'
        section and ONLY on lines containing a colon, to avoid false positives
        in multi-line descriptions.
        """
        errors = []
        docstring_text = ast.get_docstring(node)

        if not docstring_text:
            return False, [f"Function '{func_name}' is missing a docstring."]

        common_types = [
            'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set', 'bytes',
            'complex', 'object', 'Any', 'Union', 'Optional', 'Literal', 'List', 'Dict', 'Tuple',
            'Set', 'FrozenSet', 'Deque', 'Counter', 'ChainMap', 'Text', 'ByteString', 'BinaryIO',
        ]

        type_alternation_str = '|'.join(common_types)
        error_pattern = re.compile(
            fr"^\s*(?:[-*]\s+)?([\w'\"`]+)\s+({type_alternation_str})\s*(\[|:)"
        )

        in_args_section = False
        section_end_pattern = re.compile(r"^\s*(Returns|Yields|Raises|Example|Note|See Also):", re.IGNORECASE)

        for line in docstring_text.splitlines():
            if re.match(r"^\s*Args:", line, re.IGNORECASE):
                in_args_section = True
                continue

            if in_args_section:
                if section_end_pattern.match(line) or (line.strip() and not line.startswith(' ')):
                    in_args_section = False

            if in_args_section:
                # --- THIS IS THE FIX ---
                # A line can only be a parameter definition if it has a colon.
                # This prevents the regex from checking prose description lines.
                if ":" not in line:
                    continue

                match = error_pattern.search(line)
                if match:
                    param_name = match.group(1).strip("'\"`")
                    matched_type = match.group(2)
                    error_msg = (
                        f"Invalid docstring format in function '{func_name}' for parameter '{param_name}'. "
                        f"The type hint '{matched_type}' appears to be part of the name. "
                        f"Ensure all type hints are enclosed in parentheses. "
                        f"Example: '{param_name} ({matched_type}): ...'"
                    )
                    errors.append(error_msg)

        return not errors, errors

    @staticmethod
    def find_invalid_array_definitions(params, path=""):
        """
        Check if parameters contain invalid array definitions.
        An array is invalid if it has type "array" but is missing the "items" property.
        Returns a list of invalid parameter paths.
        """
        invalid_params = []
        
        if not isinstance(params, dict):
            return invalid_params
            
        for key, value in params.items():
            current_path = f"{path}.{key}" if path else key
            
            # Only check dictionary values for arrays
            if isinstance(value, dict):
                # Check if this is an array without items
                if value.get("type") == "array" and "items" not in value:
                    invalid_params.append(current_path)
                
                # Recursively check nested objects
                nested_invalid = TestDocstringStructure.find_invalid_array_definitions(value, current_path)
                invalid_params.extend(nested_invalid)
        return invalid_params

    @staticmethod
    def _validate_docstring_format_consistency(docstring_text: str, func_name: str) -> List[str]:
        """
        Validates that docstring follows Google format consistently.
        
        Args:
            docstring_text (str): The docstring text to validate
            func_name (str): Name of the function being validated
            
        Returns:
            List[str]: List of Google format consistency errors found
        """
        errors = []
        lines = docstring_text.split('\n')
        
        # Check if docstring uses Google format indicators
        if TestDocstringStructure._is_google_format(docstring_text):
            errors.extend(TestDocstringStructure._validate_google_format(lines, func_name))
        else:
            errors.append(f"Function '{func_name}' should use Google format docstring style")
            
        return errors

    @staticmethod
    def _is_google_format(docstring_text: str) -> bool:
        """
        Checks if the docstring uses Google format indicators.
        
        Args:
            docstring_text (str): The docstring text to analyze
            
        Returns:
            bool: True if Google format is detected, False otherwise
        """
        text_lower = docstring_text.lower()
        
        # Google format indicators
        google_indicators = [
            'args:', 'arguments:', 'parameters:',
            'returns:', 'raises:', 'yields:',
            'note:', 'example:', 'see also:'
        ]
        
        return any(indicator in text_lower for indicator in google_indicators)

    @staticmethod
    def _validate_google_format(lines: List[str], func_name: str) -> List[str]:
        """
        Validates Google format docstring consistency.
        
        Args:
            lines (List[str]): Lines of the docstring
            func_name (str): Name of the function being validated
            
        Returns:
            List[str]: List of Google format validation errors
        """
        errors = []
        
        # Check for consistent section headers
        section_headers = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.endswith(':') and line_stripped[:-1].lower() in [
                'args', 'arguments', 'parameters', 'returns', 'raises', 'yields',
                'note', 'example', 'see also', 'todo', 'warning', 'deprecated'
            ]:
                section_headers.append((i, line_stripped))
        
        # Check for consistent indentation in sections
        for i, header in section_headers:
            # Validate args section only
            if header != 'args:':
                continue
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('    '):
                    errors.append(f"Function '{func_name}' Google format: Section '{header}' should be followed by indented content")
        
        # Check for consistent parameter formatting
        for i, line in enumerate(lines):
            if ':' in line and any(header in line.lower() for header in ['args:', 'arguments:', 'parameters:']):
                # Look for parameter definitions in the next few lines
                for j in range(i + 1, min(i + 5, len(lines))):
                    param_line = lines[j].strip()
                    if param_line and not param_line.startswith('    '):
                        break
                    if ':' in param_line and not param_line.startswith('    '):
                        errors.append(f"Function '{func_name}' Google format: Parameter definitions should be indented")
                        break
        
        return errors

    # --- Static Helper Methods ---

    @staticmethod
    def _get_variable_from_file(filepath: str, variable_name: str) -> Optional[Dict]:
        """Safely extracts a variable from a Python file using AST parsing.
        
        Args:
            filepath (str): Path to the Python file to parse
            variable_name (str): Name of the variable to extract
            
        Returns:
            Optional[Dict]: The value of the variable if found and successfully parsed, None otherwise
        """
        if not os.path.exists(filepath): return None
        with open(filepath, "r", encoding="utf-8") as source_file:
            source_code = source_file.read()
        try:
            tree = ast.parse(source_code, filename=filepath)
        except SyntaxError: return None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == variable_name:
                        try: return ast.literal_eval(node.value)
                        except (ValueError, SyntaxError): return None
            elif isinstance(node, ast.AnnAssign):
                if node.target.id == variable_name:
                    try: return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError): return None
        return None

    @staticmethod
    def _resolve_function_source_path(qualified_name: str, package_root: str) -> Optional[str]:
        """Converts a fully qualified name to a file path.
        
        Args:
            qualified_name (str): The fully qualified name of the function (e.g., 'module.submodule.function')
            package_root (str): The root directory of the package
            
        Returns:
            Optional[str]: The resolved file path if found, None otherwise
        """
        parts = qualified_name.split('.')
        for i in range(len(parts) - 1, 0, -1):
            module_parts = parts[:i]
            potential_path = os.path.join(package_root, *module_parts)
            if os.path.isfile(potential_path + ".py"): return potential_path + ".py"
            init_file = os.path.join(potential_path, "__init__.py")
            if os.path.isfile(init_file): return init_file
        return None

    @staticmethod
    def _extract_specific_function_node(filepath: str, fqn: str) -> Optional[ast.FunctionDef]:
        with open(filepath, "r", encoding="utf-8") as f:
            source_code = f.read()
        tree = ast.parse(source_code, filename=filepath)
        target_path = fqn.split('.')
        function_name, class_name = target_path[-1], target_path[-2] if len(target_path) > 1 else None
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        if class_name == module_name: class_name = None
        nodes_to_check = tree.body
        if class_name:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    nodes_to_check = node.body; break
        for node in nodes_to_check:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                return node
        return None


def run_tests_for_package(package_path: str, reports_dir: str = REPORTS_DIR):
    """
    Configures and runs the unittest suite for a single package.
    
    Args:
        package_path: The absolute path to the package to test.
        reports_dir: The directory where the CSV report should be saved.
    """
    print_log("-" * 70)
    print_log(f"Configuring tests for package: {os.path.basename(package_path)}")

    # Dynamically configure the class variables before tests are loaded
    TestDocstringStructure.package_path = package_path
    TestDocstringStructure.reports_dir = reports_dir

    # Load tests from the now-configured class
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestDocstringStructure))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

def merge_csv_reports(reports_dir: str, merged_file_path: str):
    """
    Merges all individual docstring CSV reports into a single file.
    
    Args:
        reports_dir: The directory containing the individual CSV reports.
        merged_file_path: The path for the final merged CSV file.
    """
    print_log("-" * 70)
    print_log("Merging all CSV reports...")

    csv_files = glob.glob(os.path.join(reports_dir, "docstring_validation_*.csv"))
    if not csv_files:
        print_log("No individual CSV reports found to merge.")
        return

    all_rows = []
    header = []

    for i, filename in enumerate(csv_files):
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            if i == 0:
                header = next(reader)
                all_rows.extend(list(reader))
            else:
                next(reader)  # Skip header
                all_rows.extend(list(reader))

    with open(merged_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(all_rows)

    print_log(f"✅ Merged report successfully created at: {merged_file_path}")
    print_log(f"   - Total reports merged: {len(csv_files)}")
    print_log(f"   - Total functions logged: {len(all_rows)}")

#%%
if __name__ == "__main__":

    # --- SCRIPT CONFIGURATION ---
    API_DIR = "PATH_TO_API_DIR"
    OUTPUT_DIR = "PATH_TO_OUTPUT_DIR"

    # 1. Ensure absolute path for API_DIR
    API_DIR = os.path.abspath(API_DIR)

    # 2. Ensure absolute path for OUTPUT_DIR
    OUTPUT_DIR = os.path.abspath(OUTPUT_DIR)
    # Delete all files in REPORTS_BASE_DIR if it exists
    if os.path.exists(OUTPUT_DIR):
        for file in os.listdir(OUTPUT_DIR):
            os.remove(os.path.join(OUTPUT_DIR, file))

    # --- MAIN EXECUTION LOGIC ---
    if not os.path.isdir(API_DIR):
        raise FileNotFoundError(f"The specified package root directory does not exist: '{API_DIR}'. Please create it and place your packages inside.")
    
    # Find all valid package directories to test
    packages_to_test = [
        os.path.join(API_DIR, d)
        for d in os.listdir(API_DIR)
        if os.path.isdir(os.path.join(API_DIR, d)) and\
           os.path.exists(os.path.join(API_DIR, d, "__init__.py"))
    ]

    if not packages_to_test:
        print_log(f"No packages with an '__init__.py' file found in '{API_DIR}'.")
    else:
        # Run tests for each package found
        for pkg_path in packages_to_test:
            run_tests_for_package(pkg_path, OUTPUT_DIR)
        
        # After all tests are run, merge the generated CSV files
        # Output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_merged_report = os.path.join(OUTPUT_DIR, f"merged_docstring_validation_{timestamp}.csv")
        merge_csv_reports(OUTPUT_DIR, final_merged_report)
# %%
