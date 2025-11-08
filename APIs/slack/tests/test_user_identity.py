"""
Test cases for user identity and lookup functions in the Slack Users API.

This module contains test cases for get_user_identity and lookup_user_by_email functions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import UserNotFoundError, MissingUserIDError, EmptyEmailError
from .. import (get_user_identity, lookup_user_by_email)

class TestUserIdentity(BaseTestCaseWithErrorHandler):
    """Test cases for user identity functions."""

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

    def test_identity(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Get identity (success case)
            result = get_user_identity("U123")
            self.assertTrue(result["ok"])
            self.assertEqual(result["user"]["id"], "U123")
            self.assertEqual(result["team"]["id"], "T123")

            # Test invalid user_id - should raise UserNotFoundError or return error dict
            self.assert_error_behavior(
                get_user_identity,
                UserNotFoundError,
                "User with ID 'invalid_user' not found.",
                user_id="invalid_user"
            )

            # Test user not found - should raise UserNotFoundError or return error dict
            self.assert_error_behavior(
                get_user_identity,
                UserNotFoundError,
                "User with ID 'U999' not found.",
                user_id="U999"
            )

            # Test missing user id - should raise MissingUserIDError or return error dict
            self.assert_error_behavior(
                get_user_identity,
                MissingUserIDError,
                "user_id cannot be empty.",
                user_id=""
            )

            # Test non-string user_id - should raise TypeError or return error dict
            self.assert_error_behavior(
                get_user_identity,
                TypeError,
                "user_id must be a string.",
                user_id=123
            )

    def test_lookupByEmail(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Lookup existing user
            result = lookup_user_by_email("john.doe@example.com")
            self.assertTrue(result["ok"])
            self.assertEqual(result["user"]["profile"]["email"], "john.doe@example.com")

            # Lookup non-existent user - should raise UserNotFoundError
            self.assert_error_behavior(
                lookup_user_by_email,
                UserNotFoundError,
                "User with email not found",
                email="nonexistent@example.com",
            )

            self.assert_error_behavior(
                lookup_user_by_email,
                EmptyEmailError,
                "email cannot be empty.",
                email="",
            )
