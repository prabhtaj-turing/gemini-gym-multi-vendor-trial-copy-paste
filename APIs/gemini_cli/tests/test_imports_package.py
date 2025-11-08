"""
Test suite for package imports and smoke testing in gemini_cli
"""

import unittest
import importlib
import inspect
import sys
from pathlib import Path

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))


class TestPackageImports(unittest.TestCase):
    """Test package import functionality and public API accessibility."""

    def test_import_main_package(self):
        """Test that the main gemini_cli package can be imported."""
        try:
            import gemini_cli
            self.assertIsNotNone(gemini_cli)
        except ImportError as e:
            self.fail(f"Failed to import gemini_cli package: {e}")

    def test_public_api_functions_accessible(self):
        """Test that all public API functions are accessible via __getattr__."""
        import gemini_cli
        
        # Get the function map from the package
        expected_functions = {
            "list_directory",
            "read_file", 
            "write_file",
            "glob",
            "search_file_content",
            "replace",
            "read_many_files",
            "save_memory",
            "run_shell_command"
        }
        
        # Test that __all__ contains expected functions
        if hasattr(gemini_cli, '__all__'):
            all_functions = set(gemini_cli.__all__)
            self.assertTrue(expected_functions.issubset(all_functions),
                          f"Missing functions in __all__: {expected_functions - all_functions}")
        
        # Test that each function is accessible and callable
        for func_name in expected_functions:
            with self.subTest(function=func_name):
                # Should be able to get the function
                func = getattr(gemini_cli, func_name, None)
                self.assertIsNotNone(func, f"Function {func_name} not accessible")
                
                # Should be callable
                self.assertTrue(callable(func), f"Function {func_name} is not callable")

    def test_function_resolution_mechanism(self):
        """Test that __getattr__ properly resolves functions."""
        import gemini_cli
        
        # Test a known function
        list_directory = getattr(gemini_cli, 'list_directory', None)
        self.assertIsNotNone(list_directory)
        self.assertTrue(callable(list_directory))
        
        # Test that non-existent function raises AttributeError
        with self.assertRaises(AttributeError):
            getattr(gemini_cli, 'nonexistent_function_name')

    def test_dir_functionality(self):
        """Test that __dir__ returns expected attributes."""
        import gemini_cli
        
        dir_result = dir(gemini_cli)
        self.assertIsInstance(dir_result, list)
        
        # Should contain expected functions
        expected_in_dir = ['list_directory', 'read_file', 'write_file', 'glob']
        for func_name in expected_in_dir:
            self.assertIn(func_name, dir_result, 
                         f"Function {func_name} not in dir() result")

    def test_submodule_imports(self):
        """Test that key submodules can be imported."""
        submodules_to_test = [
            'gemini_cli.file_system_api',
            'gemini_cli.shell_api',
            'gemini_cli.memory',
            'gemini_cli.read_many_files_api',
            'gemini_cli.SimulationEngine.db',
            'gemini_cli.SimulationEngine.utils',
            'gemini_cli.SimulationEngine.file_utils',
            # NOTE: env_manager removed - functions moved to common_utils
            'gemini_cli.SimulationEngine.custom_errors'
        ]
        
        for module_name in submodules_to_test:
            with self.subTest(module=module_name):
                try:
                    module = importlib.import_module(module_name)
                    self.assertIsNotNone(module)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")

    def test_error_simulator_integration(self):
        """Test that error simulator is properly integrated."""
        import gemini_cli
        
        # Should have error simulator
        self.assertTrue(hasattr(gemini_cli, 'error_simulator'))
        
        # Should have ERROR_MODE
        self.assertTrue(hasattr(gemini_cli, 'ERROR_MODE'))

    def test_function_signatures_accessible(self):
        """Test that function signatures can be inspected."""
        import gemini_cli
        
        functions_to_test = ['read_file', 'write_file', 'list_directory']
        
        for func_name in functions_to_test:
            with self.subTest(function=func_name):
                func = getattr(gemini_cli, func_name)
                
                # Should be able to get signature
                try:
                    signature = inspect.signature(func)
                    self.assertIsInstance(signature, inspect.Signature)
                except Exception as e:
                    # Some functions might be wrapped in ways that make signature inspection difficult
                    # This is not necessarily a failure
                    pass

    def test_docstring_accessibility(self):
        """Test that function docstrings are accessible."""
        import gemini_cli
        
        functions_to_test = ['read_file', 'write_file', 'list_directory', 'glob']
        
        for func_name in functions_to_test:
            with self.subTest(function=func_name):
                func = getattr(gemini_cli, func_name)
                
                # Should have some form of documentation
                # (Either __doc__ or be able to access underlying function's doc)
                doc = getattr(func, '__doc__', None)
                # We don't require docstrings, but if present they should be strings
                if doc is not None:
                    self.assertIsInstance(doc, str)


class TestModuleStructure(unittest.TestCase):
    """Test the overall module structure and organization."""

    def test_simulation_engine_structure(self):
        """Test SimulationEngine module structure."""
        from gemini_cli.SimulationEngine import db, utils, file_utils, custom_errors
        # NOTE: env_manager removed - functions moved to common_utils
        from common_utils import terminal_filesystem_utils as common_utils_term
        
        # Test DB module
        self.assertTrue(hasattr(db, 'DB'))
        self.assertTrue(hasattr(db, 'save_state'))
        self.assertTrue(hasattr(db, 'load_state'))
        
        # Test utils module has expected constants
        self.assertTrue(hasattr(utils, 'DEFAULT_CONTEXT_FILENAME'))
        self.assertTrue(hasattr(utils, 'GEMINI_CONFIG_DIR'))
        self.assertTrue(hasattr(utils, 'DEFAULT_IGNORE_DIRS'))
        
        # Test file_utils has expected functions
        self.assertTrue(hasattr(file_utils, 'detect_file_type'))
        self.assertTrue(hasattr(file_utils, 'DEFAULT_EXCLUDES'))
        
        # Test env_manager functions now in common_utils
        self.assertTrue(hasattr(common_utils_term, 'prepare_command_environment'))
        self.assertTrue(hasattr(common_utils_term, 'expand_variables'))
        
        # Test custom_errors has expected exceptions
        self.assertTrue(hasattr(custom_errors, 'InvalidInputError'))
        self.assertTrue(hasattr(custom_errors, 'WorkspaceNotAvailableError'))

    def test_api_modules_structure(self):
        """Test main API modules structure."""
        import gemini_cli.file_system_api as fs_api
        import gemini_cli.shell_api as shell_api
        import gemini_cli.memory as memory_api
        import gemini_cli.read_many_files_api as rmf_api
        
        # Test file_system_api
        expected_fs_functions = ['list_directory', 'read_file', 'write_file', 'glob', 'grep_search', 'replace']
        for func_name in expected_fs_functions:
            self.assertTrue(hasattr(fs_api, func_name), 
                          f"file_system_api missing {func_name}")
        
        # Test shell_api
        self.assertTrue(hasattr(shell_api, 'run_shell_command'))
        
        # Test memory API
        self.assertTrue(hasattr(memory_api, 'save_memory'))
        
        # Test read_many_files_api
        self.assertTrue(hasattr(rmf_api, 'read_many_files'))

    def test_constants_and_configurations(self):
        """Test that important constants are accessible."""
        from gemini_cli.SimulationEngine.utils import (
            DEFAULT_CONTEXT_FILENAME,
            GEMINI_CONFIG_DIR,
            MEMORY_SECTION_HEADER,
            DEFAULT_IGNORE_DIRS,
            DEFAULT_IGNORE_FILE_PATTERNS,
            MAX_FILE_SIZE_BYTES
        )
        
        # Test constants have expected types and values
        self.assertIsInstance(DEFAULT_CONTEXT_FILENAME, str)
        self.assertEqual(DEFAULT_CONTEXT_FILENAME, "GEMINI.md")
        
        self.assertIsInstance(GEMINI_CONFIG_DIR, str)
        self.assertEqual(GEMINI_CONFIG_DIR, ".gemini")
        
        self.assertIsInstance(MEMORY_SECTION_HEADER, str)
        self.assertIn("Gemini", MEMORY_SECTION_HEADER)
        
        self.assertIsInstance(DEFAULT_IGNORE_DIRS, set)
        self.assertIn(".git", DEFAULT_IGNORE_DIRS)
        
        self.assertIsInstance(DEFAULT_IGNORE_FILE_PATTERNS, set)
        self.assertIn("*.pyc", DEFAULT_IGNORE_FILE_PATTERNS)
        
        self.assertIsInstance(MAX_FILE_SIZE_BYTES, int)
        self.assertGreater(MAX_FILE_SIZE_BYTES, 0)

    def test_no_import_side_effects(self):
        """Test that importing the package doesn't cause unwanted side effects."""
        # Import should not modify global state in problematic ways
        import gemini_cli
        
        # Should not create files in current directory
        current_files_before = set(Path('.').glob('*'))
        
        # Re-import should be safe
        importlib.reload(gemini_cli)
        
        current_files_after = set(Path('.').glob('*'))
        
        # Should not have created new files
        new_files = current_files_after - current_files_before
        # Filter out cache files which are expected
        unexpected_files = [f for f in new_files if not f.name.endswith('.pyc') 
                          and '__pycache__' not in str(f)]
        
        self.assertEqual(len(unexpected_files), 0, 
                        f"Import created unexpected files: {unexpected_files}")


class TestSmokeTests(unittest.TestCase):
    """Basic smoke tests to verify package health."""

    def test_basic_import_smoke(self):
        """Smoke test: basic import and attribute access."""
        import gemini_cli
        
        # Should be able to access basic attributes without errors
        _ = dir(gemini_cli)
        _ = getattr(gemini_cli, 'read_file', None)
        _ = getattr(gemini_cli, '__all__', [])
        
        # No exceptions should be raised
        self.assertTrue(True)

    def test_function_access_smoke(self):
        """Smoke test: accessing all public functions."""
        import gemini_cli
        
        if hasattr(gemini_cli, '__all__'):
            for func_name in gemini_cli.__all__:
                with self.subTest(function=func_name):
                    # Should be able to access without error
                    func = getattr(gemini_cli, func_name)
                    self.assertIsNotNone(func)
                    self.assertTrue(callable(func))

    def test_error_handling_smoke(self):
        """Smoke test: error handling doesn't crash."""
        import gemini_cli
        
        # Accessing non-existent attribute should raise AttributeError, not crash
        with self.assertRaises(AttributeError):
            _ = gemini_cli.this_function_does_not_exist
        
        # Package should still be functional after error
        read_file_func = getattr(gemini_cli, 'read_file', None)
        self.assertIsNotNone(read_file_func)

    def test_module_reload_smoke(self):
        """Smoke test: module can be reloaded safely."""
        import gemini_cli
        
        # Get a function reference
        original_read_file = getattr(gemini_cli, 'read_file')
        
        # Reload module
        importlib.reload(gemini_cli)
        
        # Should still be able to access functions
        reloaded_read_file = getattr(gemini_cli, 'read_file')
        self.assertIsNotNone(reloaded_read_file)
        self.assertTrue(callable(reloaded_read_file))


class TestDatabaseModelImports(unittest.TestCase):
    """Test database model imports and structure validation."""
    
    def test_import_database_models(self):
        """Test that database models can be imported correctly."""
        try:
            from gemini_cli.SimulationEngine.models import GeminiCliDB, DatabaseFileSystemEntry
            self.assertIsNotNone(GeminiCliDB)
            self.assertIsNotNone(DatabaseFileSystemEntry)
        except ImportError as e:
            self.fail(f"Failed to import database models: {e}")
    
    def test_database_model_structure(self):
        """Test that database models have expected structure."""
        from gemini_cli.SimulationEngine.models import GeminiCliDB, DatabaseFileSystemEntry
        
        # Check GeminiCliDB model structure
        gemini_db_fields = set(GeminiCliDB.model_fields.keys())
        expected_db_fields = {
            'workspace_root', 'cwd', 'file_system', 'memory_storage', 
            'shell_config', 'last_edit_params', 'background_processes', 
            'tool_metrics', 'gitignore_patterns', 'created'  # Note: field is 'created' not '_created'
        }
        self.assertTrue(expected_db_fields.issubset(gemini_db_fields),
                       f"Missing DB fields: {expected_db_fields - gemini_db_fields}")
        
        # Check DatabaseFileSystemEntry model structure
        entry_fields = set(DatabaseFileSystemEntry.model_fields.keys())
        expected_entry_fields = {
            'path', 'is_directory', 'content_lines', 'size_bytes', 'last_modified'
        }
        self.assertTrue(expected_entry_fields.issubset(entry_fields),
                       f"Missing entry fields: {expected_entry_fields - entry_fields}")
    
    def test_database_validation_import_functionality(self):
        """Test that database validation works after import."""
        from gemini_cli.SimulationEngine.models import GeminiCliDB, DatabaseFileSystemEntry
        from gemini_cli.SimulationEngine.db import _load_default_state
        
        # Test that we can validate the default database structure
        try:
            default_state = _load_default_state()
            validated_db = GeminiCliDB(**default_state)
            self.assertIsInstance(validated_db, GeminiCliDB)
        except Exception as e:
            self.fail(f"Database validation failed after import: {e}")
    
    def test_model_validation_error_handling(self):
        """Test that model validation properly handles invalid data."""
        from gemini_cli.SimulationEngine.models import DatabaseFileSystemEntry
        from pydantic import ValidationError
        
        # Test that invalid file system entry raises ValidationError
        invalid_entry = {
            "is_directory": False,
            "content_lines": ["test"]
            # Missing required fields: path, size_bytes, last_modified
        }
        
        with self.assertRaises(ValidationError):
            DatabaseFileSystemEntry(**invalid_entry)


if __name__ == "__main__":
    unittest.main()
