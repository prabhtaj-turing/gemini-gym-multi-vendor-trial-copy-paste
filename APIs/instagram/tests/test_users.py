# instagram/tests/test_users.py

import unittest
from instagram import User
import instagram as InstagramAPI
from .test_common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler
from instagram.SimulationEngine.custom_errors import (
    UserAlreadyExistsError,
    EmptyUsernameError,
    UserNotFoundError
)


class TestUserAPI(BaseTestCaseWithErrorHandler):
    """Test suite for the Instagram API User functionality."""

    def setUp(self):
        """
        Set up method called before each test.
        Resets the global DB to ensure a clean state for every test.
        """
        reset_db()

    def test_create_user(self):
        """Test creating a new user."""
        user = User.create_user("101", "Alice", "alice")
        self.assertEqual(user["id"], "101")
        self.assertEqual(user["username"], "alice")
        self.assertIn("101", InstagramAPI.DB["users"])
        self.assert_error_behavior(
            func_to_call=User.create_user,
            expected_exception_type=UserAlreadyExistsError,
            expected_message="User with ID '101' already exists.",
            user_id="101", name="Alice Twin", username="alice2"
        )


    def test_get_user(self):
        """Test retrieving an existing user."""
        User.create_user("102", "Bob", "bob")  # Create user first
        user = User.get_user("102")
        self.assertEqual(user["id"], "102")
        self.assertEqual(user["name"], "Bob")
        self.assertNotIn("error", user)

    def test_get_user_not_found(self):
        """Test retrieving a non-existent user."""
        self.assert_error_behavior(
            func_to_call=User.get_user,
            expected_exception_type=UserNotFoundError,
            expected_message="User with ID '999' does not exist.",
            user_id="999"
        )

        

    def test_list_users(self):
        """Test listing all users."""
        User.create_user("101", "Alice", "alice")
        User.create_user("102", "Bob", "bob")
        users = User.list_users()
        self.assertEqual(len(users), 2)
        # Check if user IDs are present in the list
        user_ids = {u["id"] for u in users}
        self.assertIn("101", user_ids)
        self.assertIn("102", user_ids)

    def test_delete_user(self):
        """Test deleting a user."""
        User.create_user("103", "Charlie", "charlie")
        self.assertIn("103", InstagramAPI.DB["users"])
        result = User.delete_user("103")
        self.assertTrue(result.get("success"))
        self.assertNotIn("103", InstagramAPI.DB["users"])

    def test_delete_user_not_found(self):
        """Test deleting a non-existent user raises UserNotFoundError."""
        self.assert_error_behavior(
            func_to_call=User.delete_user,
            expected_exception_type=UserNotFoundError,
            expected_message="User with ID '999' does not exist.",
            user_id="999"
        )


    def test_delete_user_with_invalid_input_type(self):
        """Test delete_user with non-string input."""
        self.assert_error_behavior(
            func_to_call=User.delete_user,
            expected_exception_type=TypeError,
            expected_message="Argument user_id must be a string.",
            user_id=12345
        )
        self.assert_error_behavior(
            func_to_call=User.delete_user,
            expected_exception_type=TypeError,
            expected_message="Argument user_id must be a string.",
            user_id=None
        )
        self.assert_error_behavior(
            func_to_call=User.delete_user,
            expected_exception_type=TypeError,
            expected_message="Argument user_id must be a string.",
            user_id=["user_id"]
        )

    def test_delete_user_with_empty_string(self):
        """Test delete_user with empty string input raises ValueError."""
        self.assert_error_behavior(
            func_to_call=User.delete_user,
            expected_exception_type=ValueError,
            expected_message="Field user_id cannot be empty.",
            user_id=""
        )

    def test_delete_user_with_whitespace_only_string(self):
        """Test delete_user with whitespace-only string input raises ValueError."""
        self.assert_error_behavior(
            func_to_call=User.delete_user,
            expected_exception_type=ValueError,
            expected_message="Field user_id cannot be empty.",
            user_id="   "
        )

    def test_get_user_id_by_username_success(self):
        """Test finding user ID by username successfully (case-insensitive)."""
        User.create_user("102", "Bob", "bob")
        User.create_user("104", "David", "DAVID")
        User.create_user("105", "Eve", "eVe")

        # Test exact match
        self.assertEqual(User.get_user_id_by_username("bob"), "102")
        # Test case-insensitivity (lowercase input)
        self.assertEqual(User.get_user_id_by_username("david"), "104")
        # Test case-insensitivity (mixed case input)
        self.assertEqual(User.get_user_id_by_username("Eve"), "105")
        # Test case-insensitivity (uppercase input)
        self.assertEqual(User.get_user_id_by_username("BOB"), "102")

    def test_get_user_id_by_username_not_found(self):
        """Test that UserNotFoundError is raised for non-existent usernames."""
        User.create_user("101", "Alice", "alice")
        self.assert_error_behavior(
            func_to_call=User.get_user_id_by_username,
            expected_exception_type=UserNotFoundError,
            expected_message="User with username 'nonexistent' does not exist.",
            username="nonexistent"
        )

    def test_get_user_id_by_username_from_empty_database(self):
        """Test getting a user ID from an empty database."""
        self.assert_error_behavior(
            func_to_call=User.get_user_id_by_username,
            expected_exception_type=UserNotFoundError,
            expected_message="User with username 'any_user' does not exist.",
            username="any_user"
        )

    def test_get_user_id_by_username_with_invalid_input_type(self):
        """Test get_user_id_by_username with non-string input."""
        self.assert_error_behavior(
            func_to_call=User.get_user_id_by_username,
            expected_exception_type=TypeError,
            expected_message="Username must be a string.",
            username=12345
        )
        self.assert_error_behavior(
            func_to_call=User.get_user_id_by_username,
            expected_exception_type=TypeError,
            expected_message="Username must be a string.",
            username=None
        )
        self.assert_error_behavior(
            func_to_call=User.get_user_id_by_username,
            expected_exception_type=TypeError,
            expected_message="Username must be a string.",
            username=["bob"]
        )

    def test_get_user_id_by_username_with_empty_or_whitespace_string(self):
        """Test get_user_id_by_username with an empty or whitespace-only string."""
        self.assert_error_behavior(
            func_to_call=User.get_user_id_by_username,
            expected_exception_type=EmptyUsernameError,
            expected_message="Field username cannot be empty.",
            username=""
        )
        self.assert_error_behavior(
            func_to_call=User.get_user_id_by_username,
            expected_exception_type=EmptyUsernameError,
            expected_message="Field username cannot be empty.",
            username="   "
        )


    def test_get_user_id_by_username_with_leading_trailing_whitespace(self):
        """Test that usernames with leading/trailing whitespace are stripped and found."""
        User.create_user("102", "Bob", "bob")
        # Whitespace should be stripped, so " bob " should find "bob"
        result = User.get_user_id_by_username(" bob ")
        self.assertEqual(result, "102")
        
        # Test with various whitespace
        result = User.get_user_id_by_username("  bob  ")
        self.assertEqual(result, "102")
        
        result = User.get_user_id_by_username("\tbob\n")
        self.assertEqual(result, "102")


if __name__ == "__main__":
    unittest.main()
