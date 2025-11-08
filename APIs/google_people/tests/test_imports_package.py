"""
Test cases for Imports/Package functionality in Google People API.

This module tests:
1. All module imports work correctly
2. All function imports are available and callable
3. Package structure integrity
4. Dynamic import functionality
5. Error handling for missing imports
"""

import importlib
import sys
import unittest
from pathlib import Path
from typing import Dict, Any

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestImportsPackage(BaseTestCaseWithErrorHandler):
    """Test class for imports and package functionality."""

    def setUp(self):
        """Set up test environment."""
        # Add the parent directory to path for testing
        self.test_root = Path(__file__).parent.parent.parent
        if str(self.test_root) not in sys.path:
            sys.path.insert(0, str(self.test_root))

    def tearDown(self):
        """Clean up after each test."""
        # Remove test paths from sys.path if added
        if str(self.test_root) in sys.path:
            sys.path.remove(str(self.test_root))

    def test_direct_module_imports(self):
        """Test importing modules directly without complex dependencies."""
        print("🔍 Testing direct module imports...")

        print(f"📂 Google People directory: {Path(__file__).parent.parent}")

        # Test individual module imports with full package paths
        modules_to_test = [
            ("google_people.people", "People management module"),
            ("google_people.contact_groups", "Contact groups management module"),
            ("google_people.other_contacts", "Other contacts module"),
            ("google_people.SimulationEngine.db", "Database module"),
            ("google_people.SimulationEngine.utils", "Utilities module"),
            ("google_people.SimulationEngine.models", "Data models module"),
        ]

        import_results = {}

        for module_name, description in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "status": "success",
                    "module": module,
                    "attributes": dir(module)
                }
                self.assertIsNotNone(module, f"Module {module_name} imported but is None")
                print(f"✅ {description}: {module_name}")
            except ImportError as e:
                import_results[module_name] = {
                    "status": "import_error",
                    "error": str(e)
                }
                self.fail(f"Failed to import {module_name}: {e}")
            except Exception as e:
                import_results[module_name] = {
                    "status": "error",
                    "error": str(e)
                }
                self.fail(f"⚠️ {description}: {module_name} - Error: {e}")

        successful_imports = [name for name, result in import_results.items()
                             if result["status"] == "success"]
        
        print(f"📊 Successfully imported {len(successful_imports)}/{len(modules_to_test)} modules")
        self.assertEqual(len(successful_imports), len(modules_to_test))

    def test_main_package_import(self):
        """Test importing the main google_people package."""
        try:
            import google_people
            self.assertIsNotNone(google_people)
            
            # Test that the package has expected attributes
            expected_attributes = ['__version__', '__all__', '_function_map']
            for attr in expected_attributes:
                if hasattr(google_people, attr):
                    print(f"✅ Package has attribute: {attr}")
                    
        except ImportError as e:
            self.fail(f"Failed to import main google_people package: {e}")

    def test_function_imports_from_main_package(self):
        """Test that all functions in _function_map can be imported."""
        try:
            import google_people
            
            # Get the function map
            function_map = getattr(google_people, '_function_map', {})
            self.assertIsInstance(function_map, dict)
            self.assertGreater(len(function_map), 0, "Function map should not be empty")
            
            print(f"📋 Testing {len(function_map)} functions from function map...")
            
            failed_imports = []
            successful_imports = []
            
            for func_name, module_path in function_map.items():
                try:
                    # Test that the function can be accessed via getattr
                    func = getattr(google_people, func_name)
                    self.assertIsNotNone(func, f"Function {func_name} is None")
                    self.assertTrue(callable(func), f"Function {func_name} is not callable")
                    successful_imports.append(func_name)
                    print(f"  ✅ {func_name}")
                except AttributeError as e:
                    failed_imports.append((func_name, str(e)))
                    print(f"  ❌ {func_name}: {e}")
                except Exception as e:
                    failed_imports.append((func_name, str(e)))
                    print(f"  ⚠️ {func_name}: {e}")
            
            print(f"📊 Function import results: {len(successful_imports)} success, {len(failed_imports)} failed")
            
            if failed_imports:
                failed_details = "\n".join([f"  - {name}: {error}" for name, error in failed_imports])
                self.fail(f"Failed to import {len(failed_imports)} functions:\n{failed_details}")
                
        except ImportError as e:
            self.fail(f"Failed to import google_people package: {e}")

    def test_people_module_functions(self):
        """Test specific functions in the people module."""
        expected_people_functions = [
            "get_contact",
            "create_contact", 
            "update_contact",
            "delete_contact",
            "list_connections",
            "search_people",
            "get_batch_get",
            "get_directory_person",
            "list_directory_people",
            "search_directory_people"
        ]
        
        try:
            from google_people import people
            
            missing_functions = []
            for func_name in expected_people_functions:
                if not hasattr(people, func_name):
                    missing_functions.append(func_name)
                else:
                    func = getattr(people, func_name)
                    self.assertTrue(callable(func), f"Function {func_name} is not callable")
            
            if missing_functions:
                self.fail(f"Missing functions in people module: {missing_functions}")
                
        except ImportError as e:
            self.fail(f"Failed to import people module: {e}")

    def test_contact_groups_module_functions(self):
        """Test specific functions in the contact_groups module."""
        expected_contact_group_functions = [
            "get",
            "create",
            "update", 
            "delete",
            "list",
            "modify_members"
        ]
        
        try:
            from google_people import contact_groups
            
            missing_functions = []
            for func_name in expected_contact_group_functions:
                if not hasattr(contact_groups, func_name):
                    missing_functions.append(func_name)
                else:
                    func = getattr(contact_groups, func_name)
                    self.assertTrue(callable(func), f"Function {func_name} is not callable")
            
            if missing_functions:
                self.fail(f"Missing functions in contact_groups module: {missing_functions}")
                
        except ImportError as e:
            self.fail(f"Failed to import contact_groups module: {e}")

    def test_other_contacts_module_functions(self):
        """Test specific functions in the other_contacts module."""
        expected_other_contacts_functions = [
            "get_other_contact",
            "list_other_contacts",
            "search_other_contacts"
        ]
        
        try:
            from google_people import other_contacts
            
            missing_functions = []
            for func_name in expected_other_contacts_functions:
                if not hasattr(other_contacts, func_name):
                    missing_functions.append(func_name)
                else:
                    func = getattr(other_contacts, func_name)
                    self.assertTrue(callable(func), f"Function {func_name} is not callable")
            
            if missing_functions:
                self.fail(f"Missing functions in other_contacts module: {missing_functions}")
                
        except ImportError as e:
            self.fail(f"Failed to import other_contacts module: {e}")

    def test_simulation_engine_imports(self):
        """Test SimulationEngine module imports."""
        simulation_modules = [
            ("google_people.SimulationEngine.db", ["DB", "save_state", "load_state"]),
            ("google_people.SimulationEngine.utils", ["generate_id", "validate_required_fields"]),
            ("google_people.SimulationEngine.models", ["Person", "ContactGroup", "OtherContact", "Name", "EmailAddress"])
        ]
        
        for module_name, expected_attrs in simulation_modules:
            try:
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module)
                
                missing_attrs = []
                for attr_name in expected_attrs:
                    if not hasattr(module, attr_name):
                        missing_attrs.append(attr_name)
                
                if missing_attrs:
                    self.fail(f"Missing attributes in {module_name}: {missing_attrs}")
                    
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")

    def test_pydantic_models_import(self):
        """Test that Pydantic models can be imported and instantiated."""
        try:
            from google_people.SimulationEngine.models import (
                Person, ContactGroup, OtherContact, Name, EmailAddress, PhoneNumber
            )
            
            # Test basic model instantiation
            models_to_test = [
                (Name, {"displayName": "Test User"}),
                (EmailAddress, {"value": "test@example.com"}),
                (PhoneNumber, {"value": "+1-555-123-4567"}),
            ]
            
            for model_class, test_data in models_to_test:
                try:
                    instance = model_class(**test_data)
                    self.assertIsNotNone(instance)
                except Exception as e:
                    self.fail(f"Failed to instantiate {model_class.__name__}: {e}")
                    
        except ImportError as e:
            self.fail(f"Failed to import Pydantic models: {e}")

    def test_error_handling_import(self):
        """Test error handling related imports."""
        try:
            from common_utils.base_case import BaseTestCaseWithErrorHandler
            self.assertIsNotNone(BaseTestCaseWithErrorHandler)
            
        except ImportError as e:
            self.fail(f"Failed to import error handling classes: {e}")

    def test_database_import_and_access(self):
        """Test database import and basic access."""
        try:
            from google_people.SimulationEngine.db import DB
            
            # Test basic DB operations
            self.assertTrue(hasattr(DB, 'get'))
            self.assertTrue(hasattr(DB, 'set'))
            self.assertTrue(hasattr(DB, 'clear'))
            self.assertTrue(hasattr(DB, 'update'))
            
            # Test that methods are callable
            self.assertTrue(callable(DB.get))
            self.assertTrue(callable(DB.set))
            self.assertTrue(callable(DB.clear))
            self.assertTrue(callable(DB.update))
            
        except ImportError as e:
            self.fail(f"Failed to import database: {e}")

    def test_dynamic_function_resolution(self):
        """Test the dynamic function resolution mechanism."""
        try:
            import google_people
            
            # Test __getattr__ mechanism
            func_map = google_people._function_map
            
            for func_name in func_map.keys():
                try:
                    # This should trigger __getattr__
                    func = getattr(google_people, func_name)
                    self.assertIsNotNone(func)
                    self.assertTrue(callable(func))
                except Exception as e:
                    self.fail(f"Dynamic resolution failed for {func_name}: {e}")
                    
        except ImportError as e:
            self.fail(f"Failed to test dynamic function resolution: {e}")

    def test_dir_functionality(self):
        """Test that __dir__ returns expected function names."""
        try:
            import google_people
            
            available_names = dir(google_people)
            function_map_keys = set(google_people._function_map.keys())
            
            # All function map keys should be in dir() output
            missing_in_dir = function_map_keys - set(available_names)
            
            if missing_in_dir:
                self.fail(f"Functions missing from __dir__ output: {missing_in_dir}")
                
        except ImportError as e:
            self.fail(f"Failed to test __dir__ functionality: {e}")

    def test_mutation_imports(self):
        """Test mutation-related imports if they exist."""
        try:
            # Try to import mutation modules
            from google_people.mutations.m01 import (
                contact_groups as mut_contact_groups,
                people as mut_people,
                other_contacts as mut_other_contacts
            )
            
            # Test that mutation modules have expected functions
            mutation_modules = [
                (mut_contact_groups, ["fetch_group_details", "establish_new_contact_group"]),
                (mut_people, ["retrieve_person_by_id", "add_new_person"]),
                (mut_other_contacts, ["retrieve_unlinked_contact", "fetch_all_other_contacts"])
            ]
            
            for module, expected_funcs in mutation_modules:
                for func_name in expected_funcs:
                    if hasattr(module, func_name):
                        func = getattr(module, func_name)
                        self.assertTrue(callable(func), f"Mutation function {func_name} is not callable")
                        
        except ImportError:
            # Mutations might not exist, which is okay
            print("ℹ️ Mutation modules not found (this is acceptable)")

    def test_import_error_handling(self):
        """Test handling of import errors for non-existent modules."""
        with self.assertRaises(ImportError):
            # This should raise ImportError for non-existent module
            importlib.import_module("google_people.non_existent_module")
        
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("google_people.completely.fake.module")

    def test_circular_import_prevention(self):
        """Test that there are no circular import issues."""
        try:
            # Import all main modules together
            import google_people
            from google_people import people, contact_groups, other_contacts
            from google_people.SimulationEngine import db, utils, models
            
            # If we get here without exceptions, no circular imports detected
            self.assertTrue(True)
            
        except ImportError as e:
            if "circular import" in str(e).lower():
                self.fail(f"Circular import detected: {e}")
            else:
                self.fail(f"Import error (possibly circular): {e}")


if __name__ == '__main__':
    unittest.main()
