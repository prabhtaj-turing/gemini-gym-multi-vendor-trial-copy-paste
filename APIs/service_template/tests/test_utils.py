import unittest
from ..SimulationEngine import utils
from ..SimulationEngine.db import reset_db

class TestUtils(unittest.TestCase):
    """Test suite for utility functions."""

    def setUp(self):
        """Set up test data."""
        reset_db()

    def test_build_tool_response(self):
        """Test the build_tool_response function."""
        response = utils.build_tool_response(
            entity_id="123",
            message="Success",
            inputs={"param": "value"}
        )
        self.assertTrue(response["success"])
        self.assertEqual(response["message"], "Success")
        self.assertEqual(response["data"]["entity_id"], "123")
        self.assertEqual(response["data"]["params_received"], {"param": "value"})

    def test_perform_action(self):
        """Test the perform_action function."""
        result = utils.perform_action(name="test_entity")
        self.assertIn("entity_id", result)
        self.assertIn("status_message", result)
        self.assertTrue(result["status_message"].startswith("Entity 'test_entity' created successfully"))

if __name__ == '__main__':
    unittest.main()
