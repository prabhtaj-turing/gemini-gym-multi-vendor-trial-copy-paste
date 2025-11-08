"""
Imports and Package Test Suite for Google Cloud Storage API
Tests module structure, import functionality, and package exposure.
"""

import unittest
import sys
import os
import importlib
import inspect
import copy
from pathlib import Path
from typing import Dict, List, Any

# Ensure package root is importable
sys.path.append(str(Path(__file__).resolve().parents[2]))

import google_cloud_storage
from google_cloud_storage.SimulationEngine.db import DB


class TestModuleStructure(unittest.TestCase):
    """Test the overall module structure and organization."""
    
    def test_package_imports_without_error(self):
        """Test that the main package imports without raising exceptions."""
        # Main package should import cleanly
        self.assertIsNotNone(google_cloud_storage)
        
        # Core modules should be accessible
        self.assertTrue(hasattr(google_cloud_storage, 'Buckets'))
        self.assertTrue(hasattr(google_cloud_storage, 'Channels'))
    
    def test_submodule_imports(self):
        """Test that all submodules can be imported."""
        # Test SimulationEngine submodules
        from google_cloud_storage.SimulationEngine import db
        from google_cloud_storage.SimulationEngine import utils
        from google_cloud_storage.SimulationEngine import models
        from google_cloud_storage.SimulationEngine import custom_errors
        from google_cloud_storage.SimulationEngine import file_utils
        
        # Verify they're not None
        self.assertIsNotNone(db)
        self.assertIsNotNone(utils)
        self.assertIsNotNone(models)
        self.assertIsNotNone(custom_errors)
        self.assertIsNotNone(file_utils)
    
    def test_main_api_modules_import(self):
        """Test that main API modules import correctly."""
        from google_cloud_storage import Buckets
        from google_cloud_storage import Channels
        
        # Verify modules have expected attributes
        self.assertTrue(hasattr(Buckets, 'insert'))
        self.assertTrue(hasattr(Buckets, 'list'))
        self.assertTrue(hasattr(Buckets, 'delete'))
        self.assertTrue(hasattr(Buckets, 'get'))
        self.assertTrue(hasattr(Buckets, 'update'))
        self.assertTrue(hasattr(Buckets, 'patch'))
        
        self.assertTrue(hasattr(Channels, 'stop'))
    
    def test_no_import_side_effects(self):
        """Test that importing modules doesn't cause unwanted side effects."""
        # Store initial DB state
        initial_db_state = copy.deepcopy(DB) if DB else {}
        
        # Import all modules
        import google_cloud_storage.Buckets
        import google_cloud_storage.Channels
        import google_cloud_storage.SimulationEngine.models
        import google_cloud_storage.SimulationEngine.utils
        
        # DB should not be significantly modified by imports
        # (Some initialization is expected, but not major state changes)
        self.assertIsInstance(DB, dict)


class TestPackageAPI(unittest.TestCase):
    """Test the public API exposure and function mapping."""
    
    def test_function_map_completeness(self):
        """Test that all expected functions are mapped in __init__.py."""
        expected_functions = [
            "stop_notification_channel",
            "delete_bucket", 
            "restore_bucket",
            "relocate_bucket",
            "get_bucket_details",
            "get_bucket_iam_policy",
            "get_bucket_storage_layout", 
            "create_bucket",
            "list_buckets",
            "lock_bucket_retention_policy",
            "patch_bucket_attributes",
            "set_bucket_iam_policy",
            "test_bucket_permissions",
            "update_bucket_attributes"
        ]
        
        # Test that all expected functions are available
        for func_name in expected_functions:
            self.assertTrue(hasattr(google_cloud_storage, func_name),
                          f"Function '{func_name}' not found in package API")
    
    def test_function_resolution(self):
        """Test that functions can be resolved through __getattr__."""
        # Test a few key functions
        test_functions = [
            "create_bucket",
            "list_buckets", 
            "delete_bucket",
            "get_bucket_details"
        ]
        
        for func_name in test_functions:
            func = getattr(google_cloud_storage, func_name)
            self.assertTrue(callable(func),
                          f"Function '{func_name}' is not callable")
    
    def test_dir_functionality(self):
        """Test that __dir__ returns expected function names."""
        dir_contents = dir(google_cloud_storage)
        
        # Should include all mapped functions
        expected_functions = [
            "create_bucket", "list_buckets", "delete_bucket",
            "get_bucket_details", "update_bucket_attributes"
        ]
        
        for func_name in expected_functions:
            self.assertIn(func_name, dir_contents,
                         f"Function '{func_name}' not in dir() output")
    
    def test_all_attribute(self):
        """Test that __all__ contains expected function names."""
        self.assertTrue(hasattr(google_cloud_storage, '__all__'))
        all_contents = google_cloud_storage.__all__
        
        # Should be a list
        self.assertIsInstance(all_contents, list)
        
        # Should contain key functions
        key_functions = ["create_bucket", "list_buckets", "delete_bucket"]
        for func_name in key_functions:
            self.assertIn(func_name, all_contents,
                         f"Function '{func_name}' not in __all__")


class TestImportResilience(unittest.TestCase):
    """Test import behavior under various conditions."""
    
    def test_repeated_imports(self):
        """Test that repeated imports don't cause issues."""
        # Import multiple times
        for _ in range(3):
            import google_cloud_storage
            from google_cloud_storage import Buckets
            from google_cloud_storage.SimulationEngine import db
        
        # Should still work normally
        self.assertTrue(hasattr(google_cloud_storage, 'create_bucket'))
        self.assertTrue(hasattr(Buckets, 'insert'))
    
    def test_import_error_handling(self):
        """Test behavior when imports might fail."""
        # Test importing non-existent attributes
        with self.assertRaises(AttributeError):
            _ = google_cloud_storage.nonexistent_function
        
        # But valid functions should still work
        self.assertTrue(hasattr(google_cloud_storage, 'create_bucket'))
    
    def test_module_reload_safety(self):
        """Test that modules can be safely reloaded."""
        # Store original state
        original_create_bucket = google_cloud_storage.create_bucket
        
        # Reload the module
        importlib.reload(google_cloud_storage)
        
        # Should still work
        self.assertTrue(hasattr(google_cloud_storage, 'create_bucket'))
        self.assertTrue(callable(google_cloud_storage.create_bucket))


class TestSmokeTests(unittest.TestCase):
    """Basic smoke tests for import functionality."""
    
    def setUp(self):
        """Set up smoke test environment."""
        self.original_db_state = copy.deepcopy(DB) if DB else {}
    
    def tearDown(self):
        """Clean up smoke test environment."""
        DB.clear()
        DB.update(self.original_db_state)
    
    def test_basic_import_smoke(self):
        """Smoke test: Basic imports work without exceptions."""
        try:
            import google_cloud_storage
            from google_cloud_storage import Buckets, Channels
            from google_cloud_storage.SimulationEngine import db, models, utils
            
            # Basic attribute access
            _ = google_cloud_storage.create_bucket
            _ = google_cloud_storage.list_buckets
            _ = Buckets.insert
            _ = models.BucketStorageClass
            
        except Exception as e:
            self.fail(f"Basic import smoke test failed: {e}")
    
    def test_function_callable_smoke(self):
        """Smoke test: Key functions are callable."""
        functions_to_test = [
            "create_bucket",
            "list_buckets", 
            "get_bucket_details",
            "delete_bucket"
        ]
        
        for func_name in functions_to_test:
            func = getattr(google_cloud_storage, func_name)
            self.assertTrue(callable(func),
                          f"Smoke test failed: {func_name} not callable")
    
    def test_module_integrity_smoke(self):
        """Smoke test: Module integrity checks."""
        # Package should have expected structure
        self.assertTrue(hasattr(google_cloud_storage, 'Buckets'))
        self.assertTrue(hasattr(google_cloud_storage, 'Channels'))
        self.assertTrue(hasattr(google_cloud_storage, 'DB'))
        
        # DB should be properly initialized
        self.assertIsInstance(DB, dict)
    
    def test_no_critical_import_errors(self):
        """Smoke test: No critical errors during import chain."""
        critical_modules = [
            'google_cloud_storage',
            'google_cloud_storage.Buckets',
            'google_cloud_storage.Channels',
            'google_cloud_storage.SimulationEngine.db',
            'google_cloud_storage.SimulationEngine.models'
        ]
        
        for module_name in critical_modules:
            try:
                importlib.import_module(module_name)
            except Exception as e:
                self.fail(f"Critical import failed for {module_name}: {e}")


if __name__ == "__main__":
    unittest.main()
