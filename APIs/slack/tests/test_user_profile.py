"""
Test cases for user profile management functions in the Slack Users API.

This module contains test cases for set_user_profile and related profile functions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import UserNotFoundError, MissingUserIDError, InvalidProfileError
from .. import set_user_profile

class TestUserProfile(BaseTestCaseWithErrorHandler):
    """Test cases for user profile management functions."""

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

    def test_set_user_profile_success(self):
        """Test setting a valid user profile."""
        with patch("slack.Users.DB", DB):
            profile = {
                "display_name": "John D.",
                "real_name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "status_emoji": ":smile:",
                "status_text": "Working",
                "title": "Engineer",
                "team": "T123",
                "skype": "john.doe.skype",
                "first_name": "John",
                "last_name": "Doe"
            }
            result = set_user_profile(profile, "U123")
            self.assertTrue(result["ok"])
            for k, v in profile.items():
                self.assertEqual(result["profile"][k], v)

    def test_set_user_profile_partial_fields(self):
        """Test setting a profile with only some fields provided."""
        with patch("slack.Users.DB", DB):
            profile = {"display_name": "JD", "email": "jd@example.com"}
            result = set_user_profile(profile, "U123")
            self.assertTrue(result["ok"])
            self.assertEqual(result["profile"]["display_name"], "JD")
            self.assertEqual(result["profile"]["email"], "jd@example.com")

    def test_set_user_profile_invalid_user_id_type(self):
        """Test error when user_id is not a string."""
        with patch("slack.Users.DB", DB):
            self.assert_error_behavior(
                set_user_profile,
                TypeError,
                "user_id must be a string",
                profile={"display_name": "JD"},
                user_id=123
            )

    def test_set_user_profile_empty_user_id(self):
        """Test error when user_id is empty."""
        with patch("slack.Users.DB", DB):
            self.assert_error_behavior(
                set_user_profile,
                MissingUserIDError,
                "user_id cannot be empty",
                profile={"display_name": "JD"},
                user_id=""
            )

    def test_set_user_profile_user_not_found(self):
        """Test error when user_id does not exist."""
        with patch("slack.Users.DB", DB):
            self.assert_error_behavior(
                set_user_profile,
                UserNotFoundError,
                "User with ID U999 not found",
                profile={"display_name": "JD"},
                user_id="U999"
            )

    def test_set_user_profile_invalid_profile_type(self):
        """Test error when profile is not a dict."""
        with patch("slack.Users.DB", DB):
            self.assert_error_behavior(
                set_user_profile,
                InvalidProfileError,
                "profile must be a dictionary",
                profile=[("display_name", "JD")],
                user_id="U123"
            )

    def test_set_user_profile_invalid_email_format(self):
        """Test error when email format is invalid."""
        with patch("slack.Users.DB", DB):
            self.assert_error_behavior(
                set_user_profile,
                InvalidProfileError,
                "Invalid profile data: 1 validation error for UserProfile\nemail\n  value is not a valid email address: An email address must have an @-sign. [type=value_error, input_value='not-an-email', input_type=str]",
                profile={"email": "not-an-email"},
                user_id="U123"
            )

    def test_set_user_profile_invalid_phone_format(self):
        """Test error when phone format is invalid."""
        with patch("slack.Users.DB", DB):
            self.assert_error_behavior(
                set_user_profile,
                InvalidProfileError,
                "Invalid profile data: 1 validation error for UserProfile\nphone\n  Invalid phone number format (type=value_error)",
                profile={"phone": "not-a-phone"},
                user_id="U123"
            )

    def test_set_user_profile_forbidden_extra_fields(self):
        """Test error when profile contains fields not allowed by the model."""
        with patch("slack.Users.DB", DB):
            self.assert_error_behavior(
                set_user_profile,
                InvalidProfileError,
                "Invalid profile data: 1 validation error for UserProfile\nextra_field\n  extra fields not permitted (type=value_error.extra)\n",
                profile={"display_name": "JD", "extra_field": "forbidden"},
                user_id="U123"
            )

    def test_set_user_profile_unknown_validation_error(self):
        """Test handling of unknown validation errors (else branch)."""
        # Make sure 'U123' exists in the DB for this test
        DB["users"]["U123"] = {"id": "U123", "name": "testuser"}
        with patch("slack.Users.DB", DB):
            try:
                set_user_profile(profile={"display_name": 123}, user_id="U123")
            except InvalidProfileError as e:
                # Remove the last line if it starts with 'For further information visit'
                msg = str(e)
                msg = "\n".join(line for line in msg.splitlines() if not line.strip().startswith("For further information visit"))
                expected = (
                    "Invalid profile data: 1 validation error for UserProfile\n"
                    "display_name\n"
                    "  Input should be a valid string [type=string_type, input_value=123, input_type=int]"
                )
                self.assertEqual(msg.strip(), expected)
            else:
                self.fail("InvalidProfileError not raised")

    def test_set_user_profile_creates_profile_key(self):
        """Test that set_user_profile creates the 'profile' key if missing."""
        # User exists but has no 'profile' key
        DB["users"]["U999"] = {"id": "U999", "name": "no_profile_user"}
        with patch("slack.Users.DB", DB):
            result = set_user_profile(
                profile={"display_name": "Test User"},
                user_id="U999"
            )
            self.assertTrue(result["ok"])
            self.assertIn("profile", DB["users"]["U999"])
            self.assertEqual(DB["users"]["U999"]["profile"]["display_name"], "Test User")
