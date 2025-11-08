"""
Test suite for transfer_to_human_agents tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import transfer_to_human_agents
from ..SimulationEngine.custom_errors import ValidationError as CustomValidationError

class TestTransferToHumanAgents(AirlineBaseTestCase):

    def test_transfer_to_human_agents_success(self):
        """Test a successful transfer to human agents."""
        result = transfer_to_human_agents(summary="User is having trouble with payment and requests assistance.")
        self.assertEqual(result, "Transfer successful")

    def test_transfer_to_human_agents_empty_summary(self):
        """Test that transfer raises an error for an empty summary."""
        self.assert_error_behavior(
            transfer_to_human_agents,
            CustomValidationError,
            "Summary must be a non-empty string.",
            None,
            summary=""
        )
        
    def test_transfer_to_human_agents_non_string_summary(self):
        """Test that transfer raises an error for a non-string summary."""
        self.assert_error_behavior(
            transfer_to_human_agents,
            CustomValidationError,
            "Summary must be a non-empty string.",
            None,
            summary=12345
        )

    def test_transfer_to_human_agents_whitespace_only(self):
        """Test that transfer raises an error for a whitespace-only summary."""
        self.assert_error_behavior(
            transfer_to_human_agents,
            CustomValidationError,
            "Summary must be a non-empty string.",
            None,
            summary="  "
        )

if __name__ == '__main__':
    unittest.main()