"""
Test suite for get_user_details tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import get_user_details
from ..SimulationEngine.custom_errors import UserNotFoundError, ValidationError as CustomValidationError

class TestGetUserDetails(AirlineBaseTestCase):

    def test_get_user_details_success(self):
        """Test that get_user_details returns correct data for an existing user."""
        user = get_user_details(user_id="mia_li_3668")
        self.assertIsInstance(user, dict)
        self.assertEqual(user["name"]["first_name"], "Mia")
        self.assertEqual(user["email"], "mia.li3818@example.com")

    def test_get_user_details_success_with_whitespace(self):
        """Test that get_user_details returns correct data for an existing user."""
        user = get_user_details(user_id=" mia_li_3668")
        self.assertIsInstance(user, dict)
        self.assertEqual(user["name"]["first_name"], "Mia")
        self.assertEqual(user["email"], "mia.li3818@example.com")

    def test_get_user_details_not_found(self):
        """Test get_user_details for a non-existent user."""
        self.assert_error_behavior(
            get_user_details,
            UserNotFoundError,
            "User with ID 'non_existent_user' not found.",
            None,
            user_id="non_existent_user"
        )

    def test_get_user_details_invalid_id(self):
        """Test get_user_details with an empty user ID."""
        self.assert_error_behavior(
            get_user_details,
            CustomValidationError,
            "User ID must be a non-empty string.",
            None,
            user_id=""
        )

    def test_get_user_details_invalid_user_id_empty_string(self):
        """Test that get_user_details raises CustomValidationError for empty string user_id."""
        self.assert_error_behavior(
            get_user_details,
            CustomValidationError,
            "User ID must be a non-empty string.",
            None,
            user_id=""
        )

    def test_get_user_details_invalid_user_id_none(self):
        """Test that get_user_details raises CustomValidationError for None user_id."""
        self.assert_error_behavior(
            get_user_details,
            CustomValidationError,
            "User ID must be a non-empty string.",
            None,
            user_id=None
        )

    def test_get_user_details_invalid_user_id_integer(self):
        """Test that get_user_details raises CustomValidationError for integer user_id."""
        self.assert_error_behavior(
            get_user_details,
            CustomValidationError,
            "User ID must be a non-empty string.",
            None,
            user_id=123
        )

    def test_get_user_details_invalid_user_id_list(self):
        """Test that get_user_details raises CustomValidationError for list user_id."""
        self.assert_error_behavior(
            get_user_details,
            CustomValidationError,
            "User ID must be a non-empty string.",
            None,
            user_id=["invalid", "user_id"]
        )
    
    def test_get_user_details_invalid_user_id_whitespace(self):
        """Test that get_user_details raises CustomValidationError for whitespace user_id."""
        self.assert_error_behavior(
            get_user_details,
            CustomValidationError,
            "User ID must be a non-empty string.",
            None,
            user_id="   "
        )

if __name__ == '__main__':
    unittest.main()
