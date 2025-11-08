import unittest
import importlib
import os
import sys

class TestPackage(unittest.TestCase):
    """Test suite for package health, ensuring modules and tools are importable."""

    def setUp(self):
        """Set up the Python path for testing."""
        # Add the APIs directory to the Python path
        apis_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        if apis_dir not in sys.path:
            sys.path.insert(0, apis_dir)

    def test_google_search_import(self):
        """Test that the main google_search package can be imported."""
        try:
            import google_search
            self.assertIsNotNone(google_search)
        except ImportError as e:
            self.fail(f"Failed to import google_search: {e}")

    def test_function_imports(self):
        """Test that the 'search_queries' function can be accessed from the service."""
        try:
            import google_search
            # The search function is accessed through __getattr__ mechanism
            search_func = google_search.__getattr__('search_queries')
            self.assertTrue(callable(search_func))
        except Exception as e:
            self.fail(f"Failed to access search function from google_search: {e}")

    def test_dynamic_function_access(self):
        """Test accessing functions dynamically via __getattr__."""
        google_search = importlib.import_module('google_search')
        # Check that the function is in the function map
        self.assertIn('search_queries', google_search._function_map)
        
        # Test accessing the function through __getattr__
        search_func = google_search.__getattr__('search_queries')
        self.assertTrue(callable(search_func))

if __name__ == '__main__':
    unittest.main()
