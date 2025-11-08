import unittest
from unittest.mock import patch, MagicMock
from ..SimulationEngine.custom_errors import ValidationError, ServiceNotFoundError
from ..SimulationEngine.models import ToolExplorerDB

class TestListTools(unittest.TestCase):

    def setUp(self):
        """Set up mock data and DB patcher for each test."""
        self.mock_db = {
            "services": {
                "test_service": {
                    "tool_one": {
                        "name": "tool_one",
                        "description": "First test tool",
                        "parameters": {"type": "OBJECT", "properties": {}}
                    },
                    "tool_two": {
                        "name": "tool_two",
                        "description": "Second test tool",
                        "parameters": {"type": "OBJECT", "properties": {}}
                    },
                    "tool_three": {
                        "name": "tool_three",
                        "description": "Third test tool",
                        "parameters": {"type": "OBJECT", "properties": {}}
                    }
                },
                "another_service": {
                    "single_tool": {
                        "name": "single_tool",
                        "description": "Only tool",
                        "parameters": {"type": "OBJECT", "properties": {}}
                    }
                }
            }
        }
        
        # Validate the mock DB against the Pydantic model
        try:
            ToolExplorerDB(**self.mock_db)
        except Exception as e:
            self.fail(f"Mock DB setup failed validation: {e}")

        # Start the patcher - patch DB where it's actually used in get_tools
        self.db_patcher = patch('tool_explorer.get_tools.DB', self.mock_db)
        self.mock_db_obj = self.db_patcher.start()
        
    def tearDown(self):
        """Stop the patcher after each test."""
        self.db_patcher.stop()

    def test_list_tools_for_valid_service(self):
        """Test listing tools for a valid, known service."""
        from .. import list_tools
        tools = list_tools(service_name="test_service")
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 3)
        self.assertIn("tool_one", tools)
        self.assertIn("tool_two", tools)
        self.assertIn("tool_three", tools)

    def test_list_tools_for_service_with_single_tool(self):
        """Test listing tools for a service with only one tool."""
        from .. import list_tools
        tools = list_tools(service_name="another_service")
        self.assertIsInstance(tools, list)
        self.assertEqual(len(tools), 1)
        self.assertIn("single_tool", tools)

    def test_list_tools_for_invalid_service(self):
        """Test that listing tools for a non-existent service raises a ServiceNotFoundError."""
        from .. import list_tools
        with self.assertRaises(ServiceNotFoundError) as context:
            list_tools(service_name="non_existent_service")
        self.assertIn("Service 'non_existent_service' not found", str(context.exception))

    def test_list_tools_with_empty_service_name(self):
        """Test that an empty service name raises a ValidationError."""
        from .. import list_tools
        with self.assertRaises(ValidationError) as context:
            list_tools(service_name="")
        self.assertIn("Service name must be a non-empty string", str(context.exception))

    def test_list_tools_with_non_string_service_name(self):
        """Test that a non-string service name raises a ValidationError."""
        from .. import list_tools
        with self.assertRaises(ValidationError) as context:
            list_tools(service_name=123)
        self.assertIn("Service name must be a non-empty string", str(context.exception))

if __name__ == '__main__':
    unittest.main()
