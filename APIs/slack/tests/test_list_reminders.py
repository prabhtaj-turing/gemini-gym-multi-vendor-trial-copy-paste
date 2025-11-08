"""
Test cases for the list_reminders function in the Slack Reminders API.

This module contains comprehensive test cases for the list_reminders function,
including success scenarios and all error conditions.
"""

from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import MissingUserIDError, UserNotFoundError
from .. import list_reminders

class TestListReminders(BaseTestCaseWithErrorHandler):
    """Test cases for the list_reminders function."""

    def setUp(self):
        """Reset test state before each test by clearing the global DB."""
        global DB
        DB = {
            "users": {},
            "reminders": {}
        }

    # ==============================
    # POSITIVE TEST CASES (Success)
    # ==============================

    def test_valid_user_id_returns_reminders(self):
        """Test list_reminders with a valid user_id successfully returns reminders."""
        # Set up test data
        DB["users"]["valid_user"] = {"name": "Valid User"}
        DB["reminders"]["rem1"] = {
            "creator_id": "valid_user",
            "text": "Test Reminder 1",
        }
        DB["reminders"]["rem2"] = {
            "creator_id": "another_user",
            "text": "Other Reminder",
        }
        DB["reminders"]["rem3"] = {
            "creator_id": "valid_user",
            "text": "Test Reminder 3",
        }

        # Call the function with patching
        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id="valid_user")

        self.assertTrue(response["ok"])
        self.assertNotIn("error", response)
        expected_reminders = [
            {"creator_id": "valid_user", "text": "Test Reminder 1", "id": "rem1"},
            {"creator_id": "valid_user", "text": "Test Reminder 3", "id": "rem3"},
        ]
        self.assertIsInstance(response["reminders"], list)
        # Order might not be guaranteed by dict.items(), so compare contents flexibly
        self.assertEqual(len(response["reminders"]), len(expected_reminders))
        for rem in expected_reminders:
            self.assertIn(rem, response["reminders"])

    def test_valid_user_id_no_reminders(self):
        """Test list_reminders with a valid user_id that has no reminders."""
        # Set up test data
        DB["users"]["user_no_reminders"] = {"name": "User With No Reminders"}

        # Call the function with patching
        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id="user_no_reminders")

        self.assertTrue(response["ok"])
        self.assertEqual(response["reminders"], [])

    def test_reminders_for_user_when_creator_id_defaults(self):
        """Test listing reminders where creator_id might be missing and defaults to user_id."""
        # Set up test data
        DB["users"]["defaulting_user"] = {"name": "Defaulting User"}
        # Reminder where creator_id is explicitly the user
        DB["reminders"]["rem_explicit"] = {
            "creator_id": "defaulting_user",
            "text": "Explicit reminder",
        }
        # Reminder where creator_id is missing; should default to "defaulting_user" during check
        DB["reminders"]["rem_implicit"] = {
            "text": "Implicit reminder for defaulting_user"
        }
        # Reminder for another user
        DB["reminders"]["rem_other"] = {
            "creator_id": "another_user",
            "text": "Other user's reminder",
        }

        # Call the function with patching
        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id="defaulting_user")

        self.assertTrue(response["ok"])
        self.assertIsInstance(response["reminders"], list)

        texts_found = {r["text"] for r in response["reminders"]}
        self.assertIn("Explicit reminder", texts_found)
        self.assertIn("Implicit reminder for defaulting_user", texts_found)
        self.assertEqual(
            len(response["reminders"]),
            2,
            "Should find both explicit and implicit reminders",
        )

    def test_valid_user_id_with_unicode_characters(self):
        """Test list_reminders with valid user_id containing unicode characters."""
        DB["users"]["user_unicode_🤖"] = {"name": "Unicode User"}
        DB["reminders"]["rem1"] = {"creator_id": "user_unicode_🤖", "text": "Unicode reminder"}

        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id="user_unicode_🤖")

        self.assertTrue(response["ok"])
        self.assertEqual(len(response["reminders"]), 1)
        self.assertEqual(response["reminders"][0]["text"], "Unicode reminder")

    def test_reminder_id_gets_added_correctly(self):
        """Test that reminder ID is correctly added to each reminder in response."""
        DB["users"]["test_user"] = {"name": "Test User"}
        DB["reminders"]["custom_id"] = {"creator_id": "test_user", "text": "Test reminder"}

        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id="test_user")

        self.assertTrue(response["ok"])
        self.assertEqual(len(response["reminders"]), 1)
        self.assertEqual(response["reminders"][0]["id"], "custom_id")

    # ================================
    # EXCEPTION TESTS (Input Validation)
    # ================================

    # --- TypeError Tests (Comprehensive) ---
    def test_invalid_user_id_type_integer(self):
        """Test list_reminders with an integer user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id=123
        )

    def test_invalid_user_id_type_none(self):
        """Test list_reminders with None user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id=None
        )

    def test_invalid_user_id_type_float(self):
        """Test list_reminders with a float user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id=123.45
        )

    def test_invalid_user_id_type_list(self):
        """Test list_reminders with a list user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id=["user1", "user2"]
        )

    def test_invalid_user_id_type_dict(self):
        """Test list_reminders with a dict user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id={"user": "id"}
        )

    def test_invalid_user_id_type_boolean(self):
        """Test list_reminders with a boolean user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id=True
        )

    def test_invalid_user_id_type_set(self):
        """Test list_reminders with a set user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id={"user_id"}
        )

    def test_invalid_user_id_type_tuple(self):
        """Test list_reminders with a tuple user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=TypeError,
            expected_message="user_id must be a string.",
            user_id=("user", "id")
        )

    # --- MissingUserIDError Tests (Comprehensive) ---
    def test_empty_user_id_raises_missing_user_id_error(self):
        """Test list_reminders with an empty string user_id raises MissingUserIDError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=MissingUserIDError,
            expected_message="user_id cannot be empty.",
            user_id=""
        )

    def test_whitespace_only_user_id_raises_missing_user_id_error(self):
        """Test list_reminders with whitespace-only user_id raises MissingUserIDError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=MissingUserIDError,
            expected_message="user_id cannot be empty.",
            user_id="   "
        )

    def test_tab_only_user_id_raises_missing_user_id_error(self):
        """Test list_reminders with tab-only user_id raises MissingUserIDError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=MissingUserIDError,
            expected_message="user_id cannot be empty.",
            user_id="\t\t"
        )

    def test_newline_only_user_id_raises_missing_user_id_error(self):
        """Test list_reminders with newline-only user_id raises MissingUserIDError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=MissingUserIDError,
            expected_message="user_id cannot be empty.",
            user_id="\n\r"
        )

    def test_mixed_whitespace_user_id_raises_missing_user_id_error(self):
        """Test list_reminders with mixed whitespace user_id raises MissingUserIDError."""
        self.assert_error_behavior(
            func_to_call=list_reminders,
            expected_exception_type=MissingUserIDError,
            expected_message="user_id cannot be empty.",
            user_id=" \t\n\r "
        )

    # --- UserNotFoundError Tests ---
    def test_user_not_found_in_db_raises_user_not_found_error(self):
        """Test list_reminders when user_id is not in DB raises UserNotFoundError."""
        # Set up test data with existing user
        DB["users"]["existing_user"] = {"name": "Existing User"}

        # Call the function with patching
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                func_to_call=list_reminders,
                expected_exception_type=UserNotFoundError,
                expected_message="User with ID 'unknown_user' not found in database",
                user_id="unknown_user",
            )

    def test_user_not_found_when_users_key_missing_initially(self):
        """Test that function handles when users key is missing and creates it before checking."""
        # Don't initialize DB["users"] to test the defensive code
        DB.pop("users", None)  # Ensure users key doesn't exist

        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                func_to_call=list_reminders,
                expected_exception_type=UserNotFoundError,
                expected_message="User with ID 'nonexistent' not found in database",
                user_id="nonexistent"
            )

        # Verify that the function created the users dict
        self.assertIn("users", DB)
        self.assertIsInstance(DB["users"], dict)

    def test_user_not_found_when_reminders_key_missing_initially(self):
        """Test that function handles when reminders key is missing and creates it."""
        # Set up user but no reminders key
        DB["users"]["test_user"] = {"name": "Test User"}
        DB.pop("reminders", None)  # Ensure reminders key doesn't exist

        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id="test_user")

        # Should succeed and return empty list
        self.assertTrue(response["ok"])
        self.assertEqual(response["reminders"], [])
        
        # Verify that the function created the reminders dict
        self.assertIn("reminders", DB)
        self.assertIsInstance(DB["reminders"], dict)

    # ===============================
    # EDGE CASE TESTS
    # ===============================

    def test_reminder_with_malformed_data_still_gets_processed(self):
        """Test that reminders with unexpected data structure still get processed."""
        DB["users"]["test_user"] = {"name": "Test User"}
        # Reminder with missing expected fields but still has creator_id
        DB["reminders"]["malformed"] = {"creator_id": "test_user"}  # No text field

        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id="test_user")

        self.assertTrue(response["ok"])
        self.assertEqual(len(response["reminders"]), 1)
        self.assertEqual(response["reminders"][0]["id"], "malformed")
        self.assertEqual(response["reminders"][0]["creator_id"], "test_user")

    def test_multiple_reminders_mixed_ownership(self):
        """Test complex scenario with multiple reminders and mixed ownership."""
        DB["users"]["user1"] = {"name": "User One"}
        DB["users"]["user2"] = {"name": "User Two"}
        
        # Various reminder configurations
        DB["reminders"]["rem1"] = {"creator_id": "user1", "text": "User1's reminder"}
        DB["reminders"]["rem2"] = {"creator_id": "user2", "text": "User2's reminder"}
        DB["reminders"]["rem3"] = {"text": "No creator_id - should match user1"}  # No creator_id
        DB["reminders"]["rem4"] = {"creator_id": "user1", "text": "Another user1 reminder"}
        DB["reminders"]["rem5"] = {"creator_id": "other_user", "text": "Other user reminder"}

        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id="user1")

        self.assertTrue(response["ok"])
        # Should get rem1, rem3 (defaults to user1), and rem4
        self.assertEqual(len(response["reminders"]), 3)
        
        reminder_ids = {r["id"] for r in response["reminders"]}
        self.assertEqual(reminder_ids, {"rem1", "rem3", "rem4"})

    def test_very_long_user_id_string(self):
        """Test with a very long but valid user_id string."""
        long_user_id = "a" * 1000  # 1000 character user ID
        DB["users"][long_user_id] = {"name": "Long ID User"}
        
        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id=long_user_id)

        self.assertTrue(response["ok"])
        self.assertEqual(response["reminders"], [])

    def test_user_id_with_special_characters(self):
        """Test user_id with various special characters."""
        special_user_id = "user@domain.com-_+[]{}()!@#$%^&*"
        DB["users"][special_user_id] = {"name": "Special User"}
        
        with patch("slack.Reminders.DB", DB):
            response = list_reminders(user_id=special_user_id)

        self.assertTrue(response["ok"])
        self.assertEqual(response["reminders"], [])
