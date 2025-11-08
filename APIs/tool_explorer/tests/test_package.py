import unittest
import importlib

class TestPackage(unittest.TestCase):
    """Test suite for package health, ensuring modules and tools are importable."""

    def test_tool_explorer_import(self):
        """Test that the main tool_explorer package can be imported."""
        try:
            import tool_explorer
            self.assertIsNotNone(tool_explorer)
        except ImportError as e:
            self.fail(f"Failed to import tool_explorer: {e}")

    def test_function_imports(self):
        """Test that all functions can be imported from the service."""
        try:
            from tool_explorer import list_services, list_tools, fetch_documentation
            self.assertTrue(callable(list_services))
            self.assertTrue(callable(list_tools))
            self.assertTrue(callable(fetch_documentation))
        except ImportError as e:
            self.fail(f"Failed to import functions from tool_explorer: {e}")

    def test_dynamic_function_access(self):
        """Test accessing functions dynamically via __getattr__."""
        tool_explorer = importlib.import_module('tool_explorer')
        self.assertTrue(hasattr(tool_explorer, 'list_services'))
        self.assertTrue(hasattr(tool_explorer, 'list_tools'))
        self.assertTrue(hasattr(tool_explorer, 'fetch_documentation'))
        
        list_services_func = getattr(tool_explorer, 'list_services')
        self.assertTrue(callable(list_services_func))

if __name__ == '__main__':
    unittest.main()
