#!/usr/bin/env python3
"""
Simple API Function Mapping Validation Test
This test validates that all function mappings in API __init__.py files point to actual existing functions.
Uses parameterized testing to test all APIs with a single test function.
"""

import os
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Tuple
import time


class SimpleFunctionMappingTest(unittest.TestCase):
    """Simple test class to validate function mappings across all APIs."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.project_root = Path(__file__).parent  # We're in project root now
        cls.apis_dir = cls.project_root / "APIs"  # APIs directory is subdirectory

        # Add project root to Python path for imports
        if str(cls.project_root) not in sys.path:
            sys.path.insert(0, str(cls.project_root))

    def get_all_api_services(self) -> List[str]:
        """Get list of all API services."""
        api_services = []

        for item in self.apis_dir.iterdir():
            if (item.is_dir() and 
                (item / "__init__.py").exists() and 
                item.name != '__pycache__' and
                not item.name.startswith('test_')):
                api_services.append(item.name)

        return sorted(api_services)

    def extract_function_map(self, api_service: str) -> Dict[str, str]:
        """Extract function map from API service's __init__.py file."""
        init_file = self.apis_dir / api_service / "__init__.py"

        if not init_file.exists():
            return {}

        try:
            with open(init_file, 'r', encoding='utf-8') as f:
                content = f.read()

            function_map = {}
            in_function_map = False
            bracket_count = 0

            lines = content.split('\n')
            for line in lines:
                stripped_line = line.strip()

                if '_function_map = {' in stripped_line:
                    in_function_map = True
                    bracket_count = stripped_line.count('{') - stripped_line.count('}')
                    continue

                if in_function_map:
                    bracket_count += stripped_line.count('{') - stripped_line.count('}')

                    if ':' in stripped_line and not stripped_line.startswith('#'):
                        try:
                            parts = stripped_line.split(':', 1)
                            if len(parts) == 2:
                                key = parts[0].strip().strip('"\'')
                                value = parts[1].strip().rstrip(',').strip('"\'')
                                if key and value:
                                    function_map[key] = value
                        except:
                            continue

                    if bracket_count <= 0:
                        break

            return function_map

        except Exception:
            return {}

    def validate_function_mapping_lightweight(self, api_service: str, function_name: str, module_path: str) -> Tuple[bool, str]:
        """
        Lightweight validation that checks file structure and function existence without heavy imports.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path_parts = module_path.split('.')

            # Handle case where function is defined directly in __init__.py (e.g., supabase.get_cost)
            if len(path_parts) == 2:
                service_name = path_parts[0]
                function_name_from_path = path_parts[1]
                
                # Check service name matches
                if service_name != api_service:
                    return False, f"Service name mismatch: expected '{api_service}', got '{service_name}'"
                
                # Check if function exists in the service's __init__.py
                init_file = self.apis_dir / service_name / "__init__.py"
                if init_file.exists():
                    return self._check_function_in_file(init_file, function_name_from_path)
                else:
                    return False, f"__init__.py not found for service '{service_name}'"

            if len(path_parts) < 3:
                return False, f"Module path too short: {module_path}"

            service_name = path_parts[0]
            function_name_from_path = path_parts[-1]
            module_path_parts = path_parts[1:-1]

            # Check service name matches
            if service_name != api_service:
                return False, f"Service name mismatch: expected '{api_service}', got '{service_name}'"

            # Navigate through nested path to find the final Python file
            current_dir = self.apis_dir / service_name

            for part in module_path_parts:
                nested_dir = current_dir / part
                python_file = current_dir / f"{part}.py"

                if nested_dir.is_dir():
                    # It's a directory - continue navigation
                    current_dir = nested_dir
                elif python_file.exists():
                    # Found the Python file - check if function exists in it
                    return self._check_function_in_file(python_file, function_name_from_path)
                else:
                    return False, f"Path component '{part}' not found"

            # If we've navigated through all directories, look for __init__.py or final module
            init_file = current_dir / "__init__.py"
            if init_file.exists():
                return self._check_function_in_file(init_file, function_name_from_path)

            return False, f"No module file found for path: {module_path}"

        except Exception as e:
            return False, f"Unexpected error: {e}"

    def _check_function_in_file(self, file_path: Path, function_name: str) -> Tuple[bool, str]:
        """
        Check if a function name exists in a Python file using text search (no import).
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for function definition patterns
            patterns = [
                f"def {function_name}(",
                f"def {function_name} (",
                f"{function_name} = ",  # For assigned functions
                f"class {function_name}",  # In case it's a class
            ]

            for pattern in patterns:
                if pattern in content:
                    return True, ""

            return False, f"Function '{function_name}' not found in {file_path}"

        except Exception as e:
            return False, f"Error reading file {file_path}: {e}"


class TestAPIFunctionMappings(unittest.TestCase):
    """Test class for API function mappings using dynamic test generation."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.validator = SimpleFunctionMappingTest()
        cls.validator.setUpClass()

    def test_all_function_mappings(self):
        """Test all function mappings across all APIs using fast lightweight validation."""
        start_time = time.time()

        api_services = self.validator.get_all_api_services()

        print(f"\n{'='*60}")
        print("FUNCTION MAPPING VALIDATION")
        print(f"{'='*60}")
        print(f"Testing {len(api_services)} APIs...")

        # Validate all function mappings sequentially (fastest approach)
        total_tests = 0
        passed_tests = 0
        failed_tests = []

        for api_service in api_services:
            function_map = self.validator.extract_function_map(api_service)

            for func_name, module_path in function_map.items():
                total_tests += 1
                is_valid, error_msg = self.validator.validate_function_mapping_lightweight(api_service, func_name, module_path)

                if is_valid:
                    passed_tests += 1
                else:
                    failed_tests.append({
                        'api': api_service,
                        'function': func_name,
                        'path': module_path,
                        'error': error_msg
                    })

        # Calculate timing
        end_time = time.time()
        duration = end_time - start_time

        # Print results
        print(f"\nValidation completed in {duration:.2f} seconds")
        print(f"Total mappings tested: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Speed: {total_tests/duration:.1f} mappings/second")

        if failed_tests:
            print(f"\n{'='*40}")
            print("FAILED FUNCTION MAPPINGS:")
            print(f"{'='*40}")
            for failure in failed_tests:
                print(f"\nAPI: {failure['api']}")
                print(f"Function: {failure['function']}")
                print(f"Path: {failure['path']}")
                print(f"Error: {failure['error']}")

            # Fail the test with a summary
            self.fail(f"{len(failed_tests)} out of {total_tests} function mappings failed validation")
        else:
            print(f"\n🎉 All {total_tests} function mappings are valid!")


if __name__ == "__main__":
    # Run the unittest directly
    unittest.main(verbosity=2)