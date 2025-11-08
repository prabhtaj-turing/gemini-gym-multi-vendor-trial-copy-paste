
import unittest
from unittest.mock import patch, MagicMock
from ..SimulationEngine.custom_errors import ValidationError, ServiceNotFoundError, ToolNotFoundError
from ..SimulationEngine.models import ToolExplorerDB

class TestFetchDocumentation(unittest.TestCase):

    def setUp(self):
        """Set up mock data and DB patcher for each test."""
        self.mock_db = {
            "services": {
                "mock_service": {
                    "mock_tool": {
                        "name": "mock_tool",
                        "description": "A mock tool for testing documentation retrieval.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "input_param": {
                                    "type": "STRING",
                                    "description": "A test input parameter"
                                },
                                "optional_param": {
                                    "type": "INTEGER",
                                    "description": "An optional parameter"
                                }
                            },
                            "required": ["input_param"]
                        }
                    },
                    "another_tool": {
                        "name": "another_tool",
                        "description": "Another mock tool for testing.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "data": {
                                    "type": "OBJECT",
                                    "description": "Complex data parameter"
                                }
                            },
                            "required": ["data"]
                        }
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

    def test_fetch_documentation_for_valid_tool(self):
        """Test fetching documentation for a valid tool."""
        from .. import fetch_documentation
        doc = fetch_documentation(service_name="mock_service", tool_name="mock_tool")
        self.assertIsInstance(doc, dict)
        self.assertIn("name", doc)
        self.assertIn("description", doc)
        self.assertIn("parameters", doc)
        self.assertEqual(doc["name"], "mock_tool")
        self.assertIn("mock tool for testing", doc["description"])
        self.assertIn("input_param", doc["parameters"]["properties"])
        self.assertEqual(doc["parameters"]["required"], ["input_param"])

    def test_fetch_documentation_for_another_valid_tool(self):
        """Test fetching documentation for another valid tool."""
        from .. import fetch_documentation
        doc = fetch_documentation(service_name="mock_service", tool_name="another_tool")
        self.assertIsInstance(doc, dict)
        self.assertEqual(doc["name"], "another_tool")
        self.assertIn("Another mock tool", doc["description"])
        self.assertIn("data", doc["parameters"]["properties"])

    def test_fetch_documentation_for_invalid_service(self):
        """Test that fetching docs for a non-existent service raises a ServiceNotFoundError."""
        from .. import fetch_documentation
        with self.assertRaises(ServiceNotFoundError) as context:
            fetch_documentation(service_name="non_existent_service", tool_name="mock_tool")
        self.assertIn("Service 'non_existent_service' not found", str(context.exception))

    def test_fetch_documentation_for_invalid_tool(self):
        """Test that fetching docs for a non-existent tool raises a ToolNotFoundError."""
        from .. import fetch_documentation
        with self.assertRaises(ToolNotFoundError) as context:
            fetch_documentation(service_name="mock_service", tool_name="non_existent_tool")
        self.assertIn("Tool 'non_existent_tool' not found in service 'mock_service'", str(context.exception))

    def test_fetch_documentation_with_invalid_params(self):
        """Test that invalid parameters raise a ValidationError."""
        from .. import fetch_documentation
        
        with self.assertRaises(ValidationError) as context:
            fetch_documentation(service_name="", tool_name="mock_tool")
        self.assertIn("Service name must be a non-empty string", str(context.exception))
        
        with self.assertRaises(ValidationError) as context:
            fetch_documentation(service_name="mock_service", tool_name="")
        self.assertIn("Tool name must be a non-empty string", str(context.exception))
        
        with self.assertRaises(ValidationError) as context:
            fetch_documentation(service_name=123, tool_name="mock_tool")
        self.assertIn("Service name must be a non-empty string", str(context.exception))
        
        with self.assertRaises(ValidationError) as context:
            fetch_documentation(service_name="mock_service", tool_name=456)
        self.assertIn("Tool name must be a non-empty string", str(context.exception))

if __name__ == '__main__':
    unittest.main()
