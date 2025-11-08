import unittest
from unittest.mock import patch, MagicMock
from ..SimulationEngine.models import ToolExplorerDB

class TestListServices(unittest.TestCase):

    def setUp(self):
        """Set up mock data and DB patcher for each test."""
        self.mock_db = {
            "services": {
                "service1": {
                    "tool_a": {
                        "name": "tool_a",
                        "description": "Test tool A",
                        "parameters": {"type": "OBJECT", "properties": {}}
                    }
                },
                "service2": {
                    "tool_b": {
                        "name": "tool_b",
                        "description": "Test tool B",
                        "parameters": {"type": "OBJECT", "properties": {}}
                    },
                    "tool_c": {
                        "name": "tool_c",
                        "description": "Test tool C",
                        "parameters": {"type": "OBJECT", "properties": {}}
                    }
                },
                "service3": {
                    "tool_d": {
                        "name": "tool_d",
                        "description": "Test tool D",
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

    def test_list_services(self):
        """Test that list_services returns a list of strings."""
        from .. import list_services
        services = list_services()
        
        self.assertIsInstance(services, list)
        self.assertEqual(len(services), 3)
        for service in services:
            self.assertIsInstance(service, str)
        self.assertEqual(set(services), {"service1", "service2", "service3"})

    def test_list_services_contains_known_service(self):
        """Test that a known service is in the list."""
        from .. import list_services
        services = list_services()
        self.assertIn("service1", services)
        self.assertIn("service2", services)

    def test_list_services_with_empty_db(self):
        """Test list_services returns empty list when DB is empty."""
        # Stop current patcher and start new one with empty DB
        self.db_patcher.stop()
        empty_db = {"services": {}}
        self.db_patcher = patch('tool_explorer.get_tools.DB', empty_db)
        self.db_patcher.start()
        
        from .. import list_services
        services = list_services()
        self.assertEqual(services, [])

    def test_list_services_with_no_services_key(self):
        """Test list_services returns empty list when no services key."""
        # Stop current patcher and start new one with DB without services key
        self.db_patcher.stop()
        no_services_db = {}
        self.db_patcher = patch('tool_explorer.get_tools.DB', no_services_db)
        self.db_patcher.start()
        
        from .. import list_services
        services = list_services()
        self.assertEqual(services, [])


if __name__ == '__main__':
    unittest.main()