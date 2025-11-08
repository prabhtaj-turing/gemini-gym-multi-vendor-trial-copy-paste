import unittest
import importlib

class TestPackage(unittest.TestCase):
    """Test suite for package health, ensuring modules and tools are importable."""

    def test_service_template_import(self):
        """Test that the main service_template package can be imported."""
        try:
            import service_template
            self.assertIsNotNone(service_template)
        except ImportError as e:
            self.fail(f"Failed to import service_template: {e}")

    def test_tool_import(self):
        """Test that the 'tool' function can be imported from the service."""
        try:
            from service_template import tool
            self.assertTrue(callable(tool))
        except ImportError as e:
            self.fail(f"Failed to import 'tool' from service_template: {e}")

    def test_dynamic_tool_access(self):
        """Test accessing the 'tool' function dynamically via __getattr__."""
        service_template = importlib.import_module('service_template')
        self.assertTrue(hasattr(service_template, 'tool'))
        tool_func = getattr(service_template, 'tool')
        self.assertTrue(callable(tool_func))

if __name__ == '__main__':
    unittest.main()
