import unittest
import os
import importlib
from pathlib import Path

class PackageStructureTest(unittest.TestCase):
    """Test MongoDB package structure and organization."""
    
    def setUp(self):
        """Set up test environment."""
        self.package_root = Path(__file__).parent.parent
        self.expected_files = {
            '__init__.py',
            'collection_management.py',
            'connection_server_management.py',
            'database_operations.py',
            'data_operations.py'
        }
        self.expected_directories = {
            'SimulationEngine',
            'tests'
        }

    def test_package_root_structure(self):
        """Test that the package root has expected files and directories."""
        actual_items = set(item.name for item in self.package_root.iterdir())
        
        # Check that all expected files exist
        for expected_file in self.expected_files:
            self.assertIn(expected_file, actual_items, 
                         f"Expected file {expected_file} not found in package root")
        
        # Check that all expected directories exist
        for expected_dir in self.expected_directories:
            self.assertIn(expected_dir, actual_items,
                         f"Expected directory {expected_dir} not found in package root")

    def test_simulation_engine_structure(self):
        """Test SimulationEngine directory structure."""
        sim_engine_path = self.package_root / 'SimulationEngine'
        self.assertTrue(sim_engine_path.exists(), "SimulationEngine directory not found")
        self.assertTrue(sim_engine_path.is_dir(), "SimulationEngine is not a directory")
        
        expected_sim_files = {
            '__init__.py',
            'custom_errors.py',
            'db.py',
            'models.py',
            'utils.py',
            'file_utils.py',
            'error_config.json',
            'error_definitions.json'
        }
        
        actual_sim_items = set(item.name for item in sim_engine_path.iterdir() if item.is_file())
        
        for expected_file in expected_sim_files:
            self.assertIn(expected_file, actual_sim_items,
                         f"Expected file {expected_file} not found in SimulationEngine")

    def test_tests_structure(self):
        """Test tests directory structure."""
        tests_path = self.package_root / 'tests'
        self.assertTrue(tests_path.exists(), "tests directory not found")
        self.assertTrue(tests_path.is_dir(), "tests is not a directory")
        
        # Check for __init__.py
        init_file = tests_path / '__init__.py'
        self.assertTrue(init_file.exists(), "__init__.py not found in tests directory")
        
        # Check for test files (should have test_ prefix)
        test_files = [item for item in tests_path.iterdir() 
                     if item.is_file() and item.name.startswith('test_') and item.name.endswith('.py')]
        
        self.assertGreater(len(test_files), 0, "No test files found in tests directory")
        
        # Check for specific test files we expect
        expected_test_files = {
            'test_imports.py',
            'test_package.py'  # This file itself
        }
        
        actual_test_files = set(item.name for item in test_files)
        
        for expected_test in expected_test_files:
            self.assertIn(expected_test, actual_test_files,
                         f"Expected test file {expected_test} not found")

    def test_package_init_completeness(self):
        """Test that __init__.py properly exposes all expected functions."""
        import APIs.mongodb as mongodb_module
        
        # Check that _function_map exists and is properly structured
        self.assertTrue(hasattr(mongodb_module, '_function_map'), 
                       "_function_map not found in mongodb module")
        
        function_map = mongodb_module._function_map
        self.assertIsInstance(function_map, dict, "_function_map should be a dictionary")
        
        # Check that all functions in function_map are accessible
        for func_name in function_map.keys():
            self.assertTrue(hasattr(mongodb_module, func_name),
                          f"Function {func_name} from _function_map not accessible")

    def test_module_imports(self):
        """Test that all main modules can be imported without errors."""
        module_names = [
            'APIs.mongodb.collection_management',
            'APIs.mongodb.connection_server_management',
            'APIs.mongodb.database_operations',
            'APIs.mongodb.data_operations'
        ]
        
        for module_name in module_names:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")

    def test_simulation_engine_imports(self):
        """Test that SimulationEngine components can be imported."""
        sim_engine_modules = [
            'APIs.mongodb.SimulationEngine.custom_errors',
            'APIs.mongodb.SimulationEngine.db',
            'APIs.mongodb.SimulationEngine.models',
            'APIs.mongodb.SimulationEngine.utils',
            'APIs.mongodb.SimulationEngine.file_utils'
        ]
        
        for module_name in sim_engine_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")

    def test_json_config_files_validity(self):
        """Test that JSON configuration files are valid."""
        sim_engine_path = self.package_root / 'SimulationEngine'
        
        json_files = [
            'error_config.json',
            'error_definitions.json'
        ]
        
        for json_file in json_files:
            json_path = sim_engine_path / json_file
            self.assertTrue(json_path.exists(), f"{json_file} not found")
            
            try:
                import json
                with open(json_path, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                self.fail(f"Invalid JSON in {json_file}: {e}")

    def test_static_mutation_configs(self):
        """Test static mutation configuration files."""
        static_configs_path = self.package_root / 'SimulationEngine' / 'static_mutation_configs'
        
        if static_configs_path.exists():
            self.assertTrue(static_configs_path.is_dir(), 
                          "static_mutation_configs should be a directory")
            
            # Check for m01.json
            m01_config = static_configs_path / 'm01.json'
            if m01_config.exists():
                try:
                    import json
                    with open(m01_config, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in m01.json: {e}")

    def test_alternate_fcds(self):
        """Test alternate FCD (Function Call Description) files."""
        alternate_fcds_path = self.package_root / 'SimulationEngine' / 'alternate_fcds'
        
        if alternate_fcds_path.exists():
            self.assertTrue(alternate_fcds_path.is_dir(), 
                          "alternate_fcds should be a directory")
            
            # Check for expected FCD files
            expected_fcds = [
                'concise_mongodb.json',
                'medium_detail_mongodb.json'
            ]
            
            for fcd_file in expected_fcds:
                fcd_path = alternate_fcds_path / fcd_file
                if fcd_path.exists():
                    try:
                        import json
                        with open(fcd_path, 'r') as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        self.fail(f"Invalid JSON in {fcd_file}: {e}")

    def test_package_docstring(self):
        """Test that the main package has proper documentation."""
        import APIs.mongodb as mongodb_module
        
        self.assertIsNotNone(mongodb_module.__doc__, 
                           "Main package should have a docstring")
        self.assertIn("MongoDB", mongodb_module.__doc__,
                     "Package docstring should mention MongoDB")

    def test_all_attribute(self):
        """Test that __all__ attribute is properly defined."""
        import APIs.mongodb as mongodb_module
        
        self.assertTrue(hasattr(mongodb_module, '__all__'),
                       "Package should define __all__ attribute")
        
        all_items = mongodb_module.__all__
        self.assertIsInstance(all_items, list, "__all__ should be a list")
        
        # Check that all items in __all__ are actually accessible
        for item in all_items:
            self.assertTrue(hasattr(mongodb_module, item),
                          f"Item {item} in __all__ is not accessible")

    def test_no_circular_imports(self):
        """Test that there are no circular import issues."""
        try:
            # Try importing the main package
            import APIs.mongodb
            
            # Try importing all submodules
            from APIs.mongodb import collection_management
            from APIs.mongodb import connection_server_management
            from APIs.mongodb import database_operations
            from APIs.mongodb import data_operations
            from APIs.mongodb.SimulationEngine import utils
            from APIs.mongodb.SimulationEngine import custom_errors
            from APIs.mongodb.SimulationEngine import db
            from APIs.mongodb.SimulationEngine import models
            
        except ImportError as e:
            if "circular import" in str(e).lower():
                self.fail(f"Circular import detected: {e}")
            else:
                # Re-raise if it's a different import error
                raise


if __name__ == '__main__':
    unittest.main()
