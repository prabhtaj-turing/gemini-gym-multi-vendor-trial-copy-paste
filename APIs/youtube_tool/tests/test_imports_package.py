"""
Comprehensive tests for YouTube Tool package imports and structure.
Tests direct module imports, function imports, and package integrity.
"""

import unittest
import sys
import importlib
import inspect
from pathlib import Path


class TestYouTubeToolImports(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        # Add the youtube_tool directory to path
        youtube_tool_dir = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(youtube_tool_dir))
        
    def test_direct_module_imports(self):
        """Test importing YouTube Tool modules directly."""
        print("🔍 Testing direct YouTube Tool module imports...")
        
        # Test main package import
        youtube_tool_dir = Path(__file__).parent.parent.parent
        print(f"📂 YouTube Tool directory: {youtube_tool_dir}")
        
        # Test individual module imports
        modules_to_test = [
            ("youtube_tool", "Main YouTube Tool package"),
            ("youtube_tool.SimulationEngine", "SimulationEngine package"),
            ("youtube_tool.SimulationEngine.db", "Database module"),
            ("youtube_tool.SimulationEngine.utils", "Utilities module"),
            ("youtube_tool.SimulationEngine.models", "Models module"),
            ("youtube_tool.SimulationEngine.custom_errors", "Custom errors module"),
            ("youtube_tool.youtube_search", "YouTube search module"),
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
        self.assertGreater(len(successful_imports), 0, "No modules imported successfully")
        
    def test_function_imports(self):
        """Test importing specific functions from YouTube Tool modules."""
        print("🔍 Testing function imports...")
        
        function_imports = [
            ("youtube_tool.youtube_search.search", "Main search function"),
            ("youtube_tool.SimulationEngine.utils.get_gemini_response", "Gemini API function"),
            ("youtube_tool.SimulationEngine.utils.extract_youtube_results", "Results extraction function"),
            ("youtube_tool.SimulationEngine.utils.get_json_response", "JSON response parser"),
            ("youtube_tool.SimulationEngine.utils.get_recent_searches", "Recent searches getter"),
            ("youtube_tool.SimulationEngine.utils.add_recent_search", "Recent searches adder"),
            ("youtube_tool.SimulationEngine.utils.find_and_print_executions", "Execution finder"),
            ("youtube_tool.SimulationEngine.db.save_state", "DB save function"),
            ("youtube_tool.SimulationEngine.db.load_state", "DB load function"),
        ]
        
        for import_path, description in function_imports:
            try:
                module_path, function_name = import_path.rsplit('.', 1)
                module = importlib.import_module(module_path)
                function = getattr(module, function_name)
                self.assertTrue(callable(function), 
                              f"{import_path} is not callable")
                print(f"✅ {description}: {import_path}")
            except (ImportError, AttributeError) as e:
                self.fail(f"Failed to import {import_path}: {e}")
                
    def test_simulation_engine_components(self):
        """Test SimulationEngine components are accessible."""
        print("🔍 Testing SimulationEngine components...")
        
        import youtube_tool.SimulationEngine as sim_engine
        
        # Check expected attributes
        expected_attributes = ["db", "utils", "models", "custom_errors"]
        for attr in expected_attributes:
            self.assertTrue(hasattr(sim_engine, attr), 
                          f"SimulationEngine missing attribute: {attr}")
            
        # Test accessing components
        self.assertIsNotNone(sim_engine.db)
        self.assertIsNotNone(sim_engine.utils)
        self.assertIsNotNone(sim_engine.models)
        self.assertIsNotNone(sim_engine.custom_errors)
        
    def test_package_structure_integrity(self):
        """Test that the package structure is intact."""
        print("🔍 Testing package structure integrity...")
        
        import youtube_tool
        
        # Test main package attributes
        main_attributes = ["youtube_search"]
        for attr in main_attributes:
            self.assertTrue(hasattr(youtube_tool, attr), 
                          f"Main package missing attribute: {attr}")
            
        # Test SimulationEngine structure
        import youtube_tool.SimulationEngine as sim_engine
        expected_simulation_attributes = ["db", "utils", "models", "custom_errors"]
        for attr in expected_simulation_attributes:
            self.assertTrue(hasattr(sim_engine, attr), 
                          f"SimulationEngine missing expected attribute: {attr}")
            
    def test_function_signatures(self):
        """Test that key functions have expected signatures."""
        print("🔍 Testing function signatures...")
        
        import youtube_tool.youtube_search as search_module
        import youtube_tool.SimulationEngine.utils as utils
        import youtube_tool.SimulationEngine.db as db
        
        # Test key function signatures
        function_signatures = {
            search_module.search: ["query", "result_type"],
            utils.get_gemini_response: ["query_text"],
            utils.extract_youtube_results: ["response"],
            utils.get_json_response: ["gemini_output"],
            utils.get_recent_searches: ["endpoint", "max_results"],
            utils.add_recent_search: ["endpoint", "parameters", "result"],
            db.save_state: ["filepath"],
            db.load_state: ["filepath"],
        }
        
        for func, expected_params in function_signatures.items():
            sig = inspect.signature(func)
            actual_params = list(sig.parameters.keys())
            
            for expected_param in expected_params:
                self.assertIn(expected_param, actual_params, 
                            f"Function {func.__name__} missing expected parameter: {expected_param}")
                            
    def test_custom_errors_import(self):
        """Test that custom error classes can be imported."""
        print("🔍 Testing custom error imports...")
        
        try:
            from youtube_tool.SimulationEngine.custom_errors import (
                APIError, ExtractionError, EnvironmentError
            )
            
            # Test that they are proper exception classes
            self.assertTrue(issubclass(APIError, Exception))
            self.assertTrue(issubclass(ExtractionError, Exception))
            self.assertTrue(issubclass(EnvironmentError, Exception))
            
            # Test instantiation
            api_error = APIError("Test API error")
            self.assertEqual(str(api_error), "Test API error")
            
            extraction_error = ExtractionError("Test extraction error")
            self.assertEqual(str(extraction_error), "Test extraction error")
            
            env_error = EnvironmentError("Test environment error")
            self.assertEqual(str(env_error), "Test environment error")
            
        except ImportError as e:
            self.fail(f"Could not import custom errors: {e}")
            
    def test_cross_module_dependencies(self):
        """Test that modules can access each other correctly."""
        print("🔍 Testing cross-module dependencies...")
        
        # Test that search module can access utilities
        import youtube_tool.youtube_search as search
        import youtube_tool.SimulationEngine.utils as utils
        import youtube_tool.SimulationEngine.db as db
        
        # Test DB access
        self.assertIsNotNone(db.DB)
        self.assertIsInstance(db.DB, dict)
        
        # Test utils access (these require environment variables so we just test they're callable)
        self.assertTrue(callable(utils.get_gemini_response))
        self.assertTrue(callable(utils.extract_youtube_results))
        self.assertTrue(callable(utils.get_recent_searches))
        self.assertTrue(callable(utils.add_recent_search))
        
        # Test search function access
        self.assertTrue(callable(search.search))
                
    def test_recursive_imports(self):
        """Test that there are no circular import issues."""
        print("🔍 Testing for circular import issues...")
        
        # Import multiple modules in different orders
        import_sequences = [
            ["youtube_tool", "youtube_tool.SimulationEngine", "youtube_tool.youtube_search"],
            ["youtube_tool.SimulationEngine.db", "youtube_tool.SimulationEngine.utils", "youtube_tool.SimulationEngine.custom_errors"],
        ]
        
        for sequence in import_sequences:
            for module_name in sequence:
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    self.fail(f"Circular import detected with sequence {sequence}: {e}")
                    
    def test_module_attributes_consistency(self):
        """Test that module attributes are consistent."""
        print("🔍 Testing module attributes consistency...")
        
        import youtube_tool.SimulationEngine.db as db
        import youtube_tool.SimulationEngine.utils as utils
        
        # Test that DB is accessible from both db module and utils
        self.assertIs(db.DB, utils.DB, "DB object should be the same across modules")
        
        # Test that save_state and load_state work with the same DB
        original_db = dict(db.DB)
        
        # Modify DB through utils module context
        db.DB["test_consistency"] = {"value": "test"}
        
        # Verify change is visible in both modules
        self.assertIn("test_consistency", db.DB)
        self.assertIn("test_consistency", utils.DB)
        
        # Restore original DB
        db.DB.clear()
        db.DB.update(original_db)
        

if __name__ == '__main__':
    unittest.main()
