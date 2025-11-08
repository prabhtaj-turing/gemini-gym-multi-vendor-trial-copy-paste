"""
Test cases for the get_user_info function in the Slack Users API.

This module contains test cases for getting detailed user information.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import UserNotFoundError
from .. import get_user_info

class TestUserInfo(BaseTestCaseWithErrorHandler):
    """Test cases for the get_user_info function."""

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

    def test_info(self):
        # Patch the DB in the Users module with our test DB
        with patch("slack.Users.DB", DB):
            # Test empty user_id
            with self.assertRaises(ValueError) as context:
                get_user_info("")
            self.assertEqual(str(context.exception), "Invalid user ID")

            # Test non-string user_id
            with self.assertRaises(ValueError) as context:
                get_user_info(123)
            self.assertEqual(str(context.exception), "Invalid user ID")

            # Test None user_id
            with self.assertRaises(ValueError) as context:
                get_user_info(None)
            self.assertEqual(str(context.exception), "Invalid user ID")

            # Test valid user_id
            result = get_user_info("U123")
            self.assertTrue(result["ok"])
            self.assertEqual(result["user"]["id"], "U123")
            self.assertEqual(result["user"]["name"], "user1")

            # Test non-existent user_id
            with self.assertRaises(UserNotFoundError) as context:
                get_user_info("U999")
            self.assertEqual(str(context.exception), "User not found")

            # Test invalid include_locale type (string)
            with self.assertRaises(TypeError) as context:
                get_user_info("U123", include_locale="true")
            self.assertEqual(str(context.exception), "include_locale must be a boolean")

            # Test invalid include_locale type (number)
            with self.assertRaises(TypeError) as context:
                get_user_info("U123", include_locale=1)
            self.assertEqual(str(context.exception), "include_locale must be a boolean")

            # Test invalid include_locale type (None)
            with self.assertRaises(TypeError) as context:
                get_user_info("U123", include_locale=None)
            self.assertEqual(str(context.exception), "include_locale must be a boolean")

            # Test valid include_locale (True)
            result = get_user_info("U123", include_locale=True)
            self.assertTrue(result["ok"])
            self.assertEqual(result["user"]["id"], "U123")
            self.assertEqual(result["user"]["locale"], "en-US")

            # Test valid include_locale (False)
            result = get_user_info("U123", include_locale=False)
            self.assertTrue(result["ok"])
            self.assertEqual(result["user"]["id"], "U123")
            # Since the locale was added in the previous test, it will still be present
            self.assertEqual(result["user"]["locale"], "en-US")

            # Test user with no profile data
            DB["users"]["U789"] = {"id": "U789", "name": "user3"}
            result = get_user_info("U789")
            self.assertTrue(result["ok"])
            self.assertEqual(result["user"]["id"], "U789")
            self.assertEqual(result["user"]["name"], "user3")
            self.assertNotIn("locale", result["user"])

            # Test user with profile data
            DB["users"]["U456"] = {
                "id": "U456",
                "name": "user2",
                "profile": {"email": "user2@example.com", "display_name": "User Two"},
            }
            result = get_user_info("U456")
            self.assertTrue(result["ok"])
            self.assertEqual(result["user"]["id"], "U456")
            self.assertEqual(result["user"]["name"], "user2")
            self.assertEqual(result["user"]["profile"]["email"], "user2@example.com")
            self.assertEqual(result["user"]["profile"]["display_name"], "User Two")
