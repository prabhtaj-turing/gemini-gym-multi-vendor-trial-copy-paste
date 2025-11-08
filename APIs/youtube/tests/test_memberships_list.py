import unittest
from unittest.mock import patch
from youtube.Memberships import list as memberships_list
from common_utils.base_case import BaseTestCaseWithErrorHandler



class TestMembershipsList(BaseTestCaseWithErrorHandler):
    """Test cases for the Memberships.list function to cover missing lines."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()

    def test_max_results_invalid_type(self):
        """Test max_results validation with non-integer type."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", max_results="invalid")
        self.assertEqual(str(context.exception), "max_results must be an integer")

    def test_max_results_zero(self):
        """Test max_results validation with zero value."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", max_results=0)
        self.assertEqual(str(context.exception), "max_results must be a positive integer between 1 and 50")

    def test_max_results_negative(self):
        """Test max_results validation with negative value."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", max_results=-5)
        self.assertEqual(str(context.exception), "max_results must be a positive integer between 1 and 50")

    def test_max_results_too_large(self):
        """Test max_results validation with value greater than 50."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", max_results=51)
        self.assertEqual(str(context.exception), "max_results must be a positive integer between 1 and 50")

    def test_mode_invalid_type(self):
        """Test mode validation with non-string type."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", mode=123)
        self.assertEqual(str(context.exception), "mode must be a string")

    def test_mode_invalid_value(self):
        """Test mode validation with invalid mode value."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", mode="invalid_mode")
        self.assertEqual(str(context.exception), "mode must be one of: all_current, updates")

    def test_mode_valid_values(self):
        """Test mode validation with valid mode values."""
        # Test with "all_current"
        result = memberships_list(part="snippet", mode="all_current")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

        # Test with "updates"
        result = memberships_list(part="snippet", mode="updates")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_filter_by_member_channel_id_invalid_type(self):
        """Test filter_by_member_channel_id validation with non-string type."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id=123)
        self.assertEqual(str(context.exception), "filter_by_member_channel_id must be a string")

    def test_filter_by_member_channel_id_empty_string(self):
        """Test filter_by_member_channel_id validation with empty string."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id="")
        self.assertEqual(str(context.exception), "filter_by_member_channel_id must contain at least one valid channel ID")

    def test_filter_by_member_channel_id_only_whitespace(self):
        """Test filter_by_member_channel_id validation with only whitespace."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id="   ")
        self.assertEqual(str(context.exception), "filter_by_member_channel_id must contain at least one valid channel ID")

    def test_filter_by_member_channel_id_only_commas(self):
        """Test filter_by_member_channel_id validation with only commas."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id=",,,")
        self.assertEqual(str(context.exception), "filter_by_member_channel_id must contain at least one valid channel ID")

    def test_filter_by_member_channel_id_invalid_format(self):
        """Test filter_by_member_channel_id validation with invalid channel ID format."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id="invalid_id")
        self.assertEqual(str(context.exception), "Invalid channel ID format: invalid_id. Channel IDs must be 24 characters long.")

    def test_filter_by_member_channel_id_too_short(self):
        """Test filter_by_member_channel_id validation with channel ID that's too short."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id="short")
        self.assertEqual(str(context.exception), "Invalid channel ID format: short. Channel IDs must be 24 characters long.")

    def test_filter_by_member_channel_id_too_long(self):
        """Test filter_by_member_channel_id validation with channel ID that's too long."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id="this_channel_id_is_much_too_long_for_validation")
        self.assertEqual(str(context.exception), "Invalid channel ID format: this_channel_id_is_much_too_long_for_validation. Channel IDs must be 24 characters long.")

    def test_filter_by_member_channel_id_multiple_invalid(self):
        """Test filter_by_member_channel_id validation with multiple invalid channel IDs."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id="invalid1,invalid2")
        self.assertEqual(str(context.exception), "Invalid channel ID format: invalid1. Channel IDs must be 24 characters long.")

    def test_filter_by_member_channel_id_mixed_valid_invalid(self):
        """Test filter_by_member_channel_id validation with mix of valid and invalid channel IDs."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", filter_by_member_channel_id="UC1234567890123456789012,invalid")
        self.assertEqual(str(context.exception), "Invalid channel ID format: invalid. Channel IDs must be 24 characters long.")

    def test_has_access_to_level_invalid_type(self):
        """Test has_access_to_level validation with non-string type."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", has_access_to_level=123)
        self.assertEqual(str(context.exception), "has_access_to_level must be a string")

    def test_has_access_to_level_invalid_value(self):
        """Test has_access_to_level validation with invalid level value."""
        with self.assertRaises(ValueError) as context:
            memberships_list(part="snippet", has_access_to_level="invalid_level")
        self.assertEqual(str(context.exception), "has_access_to_level must be one of: basic, premium, vip")

    def test_has_access_to_level_valid_values(self):
        """Test has_access_to_level validation with valid level values."""
        # Test with "basic"
        result = memberships_list(part="snippet", has_access_to_level="basic")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

        # Test with "premium"
        result = memberships_list(part="snippet", has_access_to_level="premium")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

        # Test with "vip"
        result = memberships_list(part="snippet", has_access_to_level="vip")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_filter_by_member_channel_id_valid_format(self):
        """Test filter_by_member_channel_id validation with valid channel ID format."""
        result = memberships_list(part="snippet", filter_by_member_channel_id="UC1234567890123456789012")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_filter_by_member_channel_id_multiple_valid(self):
        """Test filter_by_member_channel_id validation with multiple valid channel IDs."""
        result = memberships_list(
            part="snippet", 
            filter_by_member_channel_id="UC1234567890123456789012,UC9876543210987654321098"
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_filter_by_member_channel_id_with_whitespace(self):
        """Test filter_by_member_channel_id validation with whitespace around channel IDs."""
        result = memberships_list(
            part="snippet", 
            filter_by_member_channel_id="  UC1234567890123456789012  ,  UC9876543210987654321098  "
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_combined_filters(self):
        """Test the function with multiple filters combined."""
        result = memberships_list(
            part="snippet",
            has_access_to_level="basic",
            mode="all_current",
            max_results=10
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_all_parameters_none(self):
        """Test the function with all optional parameters as None."""
        result = memberships_list(part="snippet")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)


if __name__ == "__main__":
    unittest.main() 