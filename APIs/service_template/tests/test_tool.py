import unittest
from ..entity import tool
from ..SimulationEngine.custom_errors import ValidationError
from pydantic import ValidationError as PydanticValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestTool(BaseTestCaseWithErrorHandler):
    """Test suite for the 'tool' function in the service_template."""

    def test_tool_success(self):
        """Test the 'tool' function with valid inputs."""
        result = tool(
            entity_name="Test Entity",
            complex_param={"config_name": "Test Config", "value": 123}
        )
        self.assertTrue(result['success'])
        self.assertIn('entity_id', result['data'])
        self.assertEqual(result['data']['params_received']['entity_name'], "Test Entity")

    def test_tool_dry_run(self):
        """Test the 'tool' function with is_dry_run=True."""
        result = tool(
            entity_name="Test Entity",
            complex_param={"config_name": "Test Config", "value": 123},
            is_dry_run=True
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['entity_id'], "dry-run-not-created")
        self.assertEqual(result['message'], "Dry run successful. Inputs are valid.")

    def test_tool_invalid_entity_name(self):
        """Test the 'tool' function with an invalid entity_name."""
        # Empty string should fail min_length=1 validation
        self.assert_error_behavior(
            lambda: tool(
                entity_name="",
                complex_param={"config_name": "Test Config", "value": 123}
            ),
            PydanticValidationError,
            "at least 1"
        )

        # Length > 100 should fail max_length=100 validation
        self.assert_error_behavior(
            lambda: tool(
                entity_name="a" * 101,
                complex_param={"config_name": "Test Config", "value": 123}
            ),
            PydanticValidationError,
            "at most 100"
        )

    def test_tool_invalid_complex_param(self):
        """Test the 'tool' function with an invalid complex_param."""
        # Missing required key 'value'
        self.assert_error_behavior(
            lambda: tool(
                entity_name="Test Entity",
                complex_param={"config_name": "Test Config"}
            ),
            PydanticValidationError,
            "Field required"
        )

        # Invalid value (gt=0 constraint)
        self.assert_error_behavior(
            lambda: tool(
                entity_name="Test Entity",
                complex_param={"config_name": "Test Config", "value": -1}
            ),
            PydanticValidationError,
            "greater than 0"
        )

if __name__ == '__main__':
    unittest.main()
