import unittest
from ..users import transfer_to_human_agents
from ..SimulationEngine.custom_errors import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestTransferToHumanAgents(BaseTestCaseWithErrorHandler):
    def test_transfer_to_human_agents_success(self):
        """Test that the function returns the correct message on success."""
        summary = "The user is having trouble booking a flight."
        result = transfer_to_human_agents(summary)
        self.assertEqual(result, "Transfer successful")

    def test_transfer_to_human_agents_empty_summary(self):
        """Test that the function raises a validation error for an empty summary."""
        self.assert_error_behavior(
            transfer_to_human_agents,
            ValidationError,
            "Summary must be a non-empty string.",
            summary=""
        )
        
    def test_transfer_to_human_agents_non_string_summary(self):
        """Test that transfer raises an error for a non-string summary."""
        self.assert_error_behavior(
            transfer_to_human_agents,
            ValidationError,
            "Summary must be a non-empty string.",
            summary=12345
        )

if __name__ == '__main__':
    unittest.main() 