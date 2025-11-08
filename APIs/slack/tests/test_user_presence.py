"""
Test cases for user presence functions in the Slack Users API.

This module contains test cases for get_user_presence and set_user_presence functions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import UserNotFoundError, MissingUserIDError
from .. import (get_user_presence, set_user_presence)

class TestUserPresence(BaseTestCaseWithErrorHandler):
    """Test cases for user presence functions."""

    def setUp(self):
        """Set up test database."""
        global DB
        DB = {
            "users": {
                "U123": {
                    "id": "U123",
                    "name": "user1",
                    "team_id": "T123",
                    "profile": {"email": "john.doe@example.com"},
                },
                "U456": {"id": "U456", "name": "user2", "team_id": "T123"},
                "U789": {"id": "U789", "name": "user3", "team_id": "T456"},
            },
        }
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")

    def test_getPresence_success(self):
        """Test successful retrieval of user presence."""
        with patch("slack.Users.DB", DB):
            # Test with explicit user_id
            result = get_user_presence("U123")
            self.assertTrue(result["ok"])
            self.assertEqual(result["presence"], "away")  # Default presence

            # Test with current user
            DB["current_user"] = {"id": "U456"}
            result = get_user_presence()
            self.assertTrue(result["ok"])
            self.assertEqual(result["presence"], "away")  # Default presence

    def test_getPresence_with_custom_presence(self):
        """Test retrieval of user presence with custom presence value."""
        with patch("slack.Users.DB", DB):
            # Set custom presence for a user
            DB["users"]["U123"]["presence"] = "active"
            result = get_user_presence("U123")
            self.assertTrue(result["ok"])
            self.assertEqual(result["presence"], "active")

    def test_getPresence_no_authenticated_user(self):
        """Test behavior when no user_id is provided and no authenticated user exists."""
        with patch("slack.Users.DB", DB):
            # Remove current_user from DB
            if "current_user" in DB:
                del DB["current_user"]
            
            # Test without user_id
            self.assert_error_behavior(
                get_user_presence,
                MissingUserIDError,
                "No user_id provided and no authenticated user found"
            )

    def test_getPresence_user_not_found(self):
        """Test behavior when specified user_id does not exist."""
        with patch("slack.Users.DB", DB):
            # Test with non-existent user_id
            self.assert_error_behavior(
                get_user_presence,
                UserNotFoundError,
                "User with ID U999 not found",
                user_id="U999"
            )

    def test_getPresence_empty_user_id(self):
        """Test behavior with empty user_id string."""
        with patch("slack.Users.DB", DB):
            # Test with empty string
            self.assert_error_behavior(
                get_user_presence,
                MissingUserIDError,
                "No user_id provided and no authenticated user found",
                user_id=""
            )

    def test_getPresence_none_user_id(self):
        """Test behavior with None user_id."""
        with patch("slack.Users.DB", DB):
            # Test with None
            self.assert_error_behavior(
                get_user_presence,
                MissingUserIDError,
                "No user_id provided and no authenticated user found",
                user_id=None
            )

    def test_getPresence_invalid_user_id_type(self):
        """Test behavior with invalid user_id type."""
        with patch("slack.Users.DB", DB):
            # Test with non-string user_id
            self.assert_error_behavior(
                get_user_presence,
                TypeError,
                "user_id must be a string or None",
                user_id=123
            )

    def test_set_presence(self):
        """Test the setPresence function for success and validation errors."""
        with patch("slack.Users.DB", DB):
            # Test success case: set presence to 'away'
            result = set_user_presence("U123", "away")
            self.assertTrue(result["ok"])
            self.assertEqual(DB["users"]["U123"]["presence"], "away")

            # Test success case: set presence back to 'active'
            result = set_user_presence("U123", "active")
            self.assertTrue(result["ok"])
            self.assertEqual(DB["users"]["U123"]["presence"], "active")

            # Test invalid user_id type
            self.assert_error_behavior(
                func_to_call=set_user_presence,
                expected_exception_type=TypeError,
                expected_message="user_id must be a string.",
                user_id=123,
                presence="active"
            )

            # Test empty user_id value
            self.assert_error_behavior(
                func_to_call=set_user_presence,
                expected_exception_type=ValueError,
                expected_message="user_id cannot be an empty string.",
                user_id="",
                presence="active"
            )

            # Test invalid presence type
            self.assert_error_behavior(
                func_to_call=set_user_presence,
                expected_exception_type=TypeError,
                expected_message="presence must be a string.",
                user_id="U123",
                presence=None
            )

            # Test invalid presence value
            self.assert_error_behavior(
                func_to_call=set_user_presence,
                expected_exception_type=ValueError,
                expected_message="presence must be 'active' or 'away'.",
                user_id="U123",
                presence="invalid_status"
            )

            # Test user not found
            self.assert_error_behavior(
                func_to_call=set_user_presence,
                expected_exception_type=UserNotFoundError,
                expected_message="User 'U999' not found.",
                user_id="U999",
                presence="active"
            )
