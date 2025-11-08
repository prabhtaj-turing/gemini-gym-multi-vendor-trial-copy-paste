"""
Test cases for import validation in the Copilot API.
Tests that all modules and functions can be imported without errors.
"""

import unittest
import importlib
import sys
import os
from pathlib import Path

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestImportsPackage(BaseTestCaseWithErrorHandler):
    """Test cases for import validation."""

    def setUp(self):
        """Set up test fixtures."""
        # Add the copilot directory to path for testing
        self.copilot_dir = Path(__file__).parent.parent
        if str(self.copilot_dir) not in sys.path:
            sys.path.insert(0, str(self.copilot_dir))

    def tearDown(self):
        """Clean up after each test."""
        # Remove copilot directory from path if we added it
        if str(self.copilot_dir) in sys.path:
            sys.path.remove(str(self.copilot_dir))

    def test_main_copilot_module_import(self):
        """Test importing the main copilot module."""
        try:
            import copilot
            self.assertIsNotNone(copilot)
            # Test that the module has expected attributes
            self.assertTrue(hasattr(copilot, '__all__'))
            self.assertTrue(hasattr(copilot, '_function_map'))
        except ImportError as e:
            self.fail(f"Failed to import copilot module: {e}")

    def test_direct_module_imports(self):
        """Test importing modules directly without complex dependencies."""
        print("🔍 Testing direct module imports...")

        modules_to_test = [
            ("copilot.code_intelligence", "Code intelligence module"),
            ("copilot.code_quality_version_control", "Code quality and version control module"),
            ("copilot.command_line", "Command line module"),
            ("copilot.file_system", "File system module"),
            ("copilot.project_setup", "Project setup module"),
            ("copilot.test_file_management", "Test file management module"),
            ("copilot.vscode_environment", "VS Code environment module"),
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
        
        self.assertEqual(len(successful_imports), len(modules_to_test),
                        f"Not all modules imported successfully. Results: {import_results}")

    def test_simulation_engine_imports(self):
        """Test importing SimulationEngine modules."""
        simulation_modules = [
            ("copilot.SimulationEngine.db", "Database module"),
            ("copilot.SimulationEngine.utils", "Utilities module"),
            ("copilot.SimulationEngine.models", "Models module"),
            ("copilot.SimulationEngine.custom_errors", "Custom errors module"),
            ("copilot.SimulationEngine.llm_interface", "LLM interface module"),
        ]

        for module_name, description in simulation_modules:
            try:
                module = importlib.import_module(module_name)
                self.assertIsNotNone(module)
                print(f"✅ {description}: {module_name}")
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")

    def test_function_imports_from_main_module(self):
        """Test importing functions from the main copilot module."""
        try:
            import copilot
            
            # Test function map functions
            function_names = [
                "semantic_search",
                "list_code_usages", 
                "grep_search",
                "file_search",
                "read_file",
                "list_dir",
                "insert_edit_into_file",
                "run_in_terminal",
                "get_terminal_output",
                "get_vscode_api",
                "install_extension",
                "create_new_workspace",
                "get_project_setup_info",
                "create_new_jupyter_notebook",
                "get_errors",
                "get_changed_files",
                "test_search"
            ]
            
            failed_imports = []
            for func_name in function_names:
                try:
                    func = getattr(copilot, func_name)
                    self.assertTrue(callable(func), f"{func_name} is not callable")
                    print(f"✅ Function: {func_name}")
                except AttributeError:
                    failed_imports.append(func_name)
                    print(f"❌ Function: {func_name}")
            
            if failed_imports:
                self.fail(f"Failed to import functions: {failed_imports}")
                
        except ImportError as e:
            self.fail(f"Failed to import copilot module for function testing: {e}")
            
    def test_model_imports(self):
        """Test importing Pydantic models."""
        try:
            from copilot.SimulationEngine.models import (
                DirectoryEntry,
                FileOutlineItem,
                ReadFileResponse,
                JupyterNotebookCreationResponse,
                EditFileResult,
                WebpageContent
            )
            
            models = [
                DirectoryEntry,
                FileOutlineItem,
                ReadFileResponse,
                JupyterNotebookCreationResponse,
                EditFileResult,
                WebpageContent
            ]
            
            for model in models:
                # Test that it's a Pydantic model
                self.assertTrue(hasattr(model, 'model_validate'))
                self.assertTrue(hasattr(model, 'model_dump'))
                print(f"✅ Model: {model.__name__}")
                
        except ImportError as e:
            self.fail(f"Failed to import models: {e}")

    def test_custom_errors_imports(self):
        """Test importing custom error classes."""
        try:
            from copilot.SimulationEngine.custom_errors import (
                FileCreationError,
                JupyterEnvironmentError,
                InvalidRequestError,
                CommandExecutionError,
                TerminalNotAvailableError,
                InvalidInputError,
                DirectoryNotFoundError,
                InvalidLineRangeError,
                FileNotFoundError,
                PermissionDeniedError,
                WorkspaceNotAvailableError,
                InvalidGlobPatternError,
                SearchFailedError,
                ValidationError,
                SymbolNotFoundError,
                IndexingNotCompleteError,
                InvalidTerminalIdError,
                OutputRetrievalError,
                InvalidSearchPatternError,
                EditConflictError,
                InvalidEditFormatError
            )
            
            errors = [
                FileCreationError,
                JupyterEnvironmentError,
                InvalidRequestError,
                CommandExecutionError,
                TerminalNotAvailableError,
                InvalidInputError,
                DirectoryNotFoundError,
                InvalidLineRangeError,
                FileNotFoundError,
                PermissionDeniedError,
                WorkspaceNotAvailableError,
                InvalidGlobPatternError,
                SearchFailedError,
                ValidationError,
                SymbolNotFoundError,
                IndexingNotCompleteError,
                InvalidTerminalIdError,
                OutputRetrievalError,
                InvalidSearchPatternError,
                EditConflictError,
                InvalidEditFormatError
            ]
            
            for error_class in errors:
                # Test that it's an exception class
                self.assertTrue(issubclass(error_class, Exception))
                print(f"✅ Error class: {error_class.__name__}")
                
        except ImportError as e:
            self.fail(f"Failed to import custom errors: {e}")

    def test_db_imports(self):
        """Test importing database components."""
        try:
            from copilot.SimulationEngine.db import DB, save_state, load_state
            
            # Test DB is a dictionary
            self.assertIsInstance(DB, dict)
            
            # Test functions are callable
            self.assertTrue(callable(save_state))
            self.assertTrue(callable(load_state))
            
            print("✅ DB module components imported successfully")
            
        except ImportError as e:
            self.fail(f"Failed to import DB components: {e}")

    def test_utils_function_imports(self):
        """Test importing utility functions."""
        try:
            from copilot.SimulationEngine.utils import (
                get_absolute_path,
                get_current_timestamp_iso,
                get_file_system_entry,
                path_exists,
                is_directory,
                is_file,
                calculate_size_bytes,
                add_line_numbers,
                strip_code_fences_from_llm
            )
            
            utils_functions = [
                get_absolute_path,
                get_current_timestamp_iso,
                get_file_system_entry,
                path_exists,
                is_directory,
                is_file,
                calculate_size_bytes,
                add_line_numbers,
                strip_code_fences_from_llm
            ]
            
            for func in utils_functions:
                self.assertTrue(callable(func))
                print(f"✅ Utility function: {func.__name__}")
                
        except ImportError as e:
            self.fail(f"Failed to import utility functions: {e}")

    def test_no_circular_imports(self):
        """Test that there are no circular import issues."""
        try:
            # Import multiple modules that might have circular dependencies
            import copilot
            import copilot.code_intelligence
            import copilot.file_system
            import copilot.SimulationEngine.utils
            import copilot.SimulationEngine.db
            
            # Test that we can access functions from different modules
            self.assertTrue(hasattr(copilot, 'semantic_search'))
            self.assertTrue(hasattr(copilot.code_intelligence, 'semantic_search'))
            self.assertTrue(hasattr(copilot.file_system, 'file_search'))
            
            print("✅ No circular import issues detected")
            
        except ImportError as e:
            self.fail(f"Circular import issue detected: {e}")

    def test_package_structure_integrity(self):
        """Test that the package structure is intact."""
        # Test that key files exist
        copilot_dir = Path(__file__).parent.parent
        
        required_files = [
            "__init__.py",
            "code_intelligence.py",
            "file_system.py",
            "command_line.py",
            "project_setup.py",
            "SimulationEngine/__init__.py",
            "SimulationEngine/db.py",
            "SimulationEngine/utils.py",
            "SimulationEngine/models.py",
            "SimulationEngine/custom_errors.py",
            "schema.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = copilot_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.fail(f"Missing required files: {missing_files}")
        
        print("✅ Package structure integrity check passed")

    def test_function_map_completeness(self):
        """Test that function map contains all expected functions."""
        try:
            import copilot
            
            # Get the function map
            function_map = copilot._function_map
            
            # Expected functions based on the modules
            expected_functions = {
                "semantic_search", "list_code_usages", "grep_search",
                "file_search", "read_file", "list_dir", "insert_edit_into_file",
                "run_in_terminal", "get_terminal_output",
                "get_vscode_api", "install_extension",
                "create_new_workspace", "get_project_setup_info", "create_new_jupyter_notebook",
                "get_errors", "get_changed_files",
                "test_search"
            }
            
            missing_functions = expected_functions - set(function_map.keys())
            extra_functions = set(function_map.keys()) - expected_functions
            
            if missing_functions:
                self.fail(f"Missing functions in function map: {missing_functions}")
            
            # Extra functions are not necessarily an error, just log them
            if extra_functions:
                print(f"ℹ️ Extra functions in function map: {extra_functions}")
            
            print("✅ Function map completeness check passed")
            
        except ImportError as e:
            self.fail(f"Failed to test function map: {e}")


if __name__ == '__main__':
    unittest.main()
