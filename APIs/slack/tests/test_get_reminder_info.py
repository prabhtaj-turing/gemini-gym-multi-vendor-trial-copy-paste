"""
Test cases for the get_reminder_info function in the Slack Reminders API.

This module contains comprehensive test cases for the get_reminder_info function,
including success scenarios and all error conditions.
"""

from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    MissingReminderIdError,
    ReminderNotFoundError,
)
from .. import (add_reminder, get_reminder_info)

class TestGetReminderInfo(BaseTestCaseWithErrorHandler):
    """Test cases for the get_reminder_info function."""

    def setUp(self):
        """
        Set up the test environment by assigning a fresh initial state to DB.
        """
        global DB
        DB = {
            "reminders": {},
            "users": {
                "U123": {"id": "U123", "name": "user1", "token": "valid_token_1"},
                "U456": {"id": "U456", "name": "user2", "token": "valid_token_2"},
            },
            "channels": {},
            "files": {},
            "scheduled_messages": [],
            "ephemeral_messages": [],
        }

    def test_get_reminder_info_success(self):
        """Test successful retrieval of reminder information."""
        # Patch the DB in the Reminders module with our test DB
        with patch("slack.Reminders.DB", DB):
            # Add a reminder
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            reminder_id = add_result["reminder"]["id"]

            # Get info about the reminder
            result = get_reminder_info(reminder_id)
            self.assertTrue(result["ok"])
            self.assertEqual(result["reminder"]["id"], reminder_id)
            self.assertEqual(result["reminder"]["text"], "Test reminder")

    def test_get_reminder_info_different_user(self):
        """Test getting info about reminder created by someone else."""
        with patch("slack.Reminders.DB", DB):
            # Add a reminder for U123
            add_result = add_reminder(
                user_id="U123", text="Another reminder", ts="1678886500"
            )
            reminder_id = add_result["reminder"]["id"]
            
            # Get info about the reminder (should work)
            result = get_reminder_info(reminder_id)
            self.assertTrue(result["ok"])
            self.assertEqual(result["reminder"]["id"], reminder_id)
            self.assertEqual(result["reminder"]["text"], "Another reminder")

    def test_get_reminder_info_with_channel(self):
        """Test getting info about reminder with channel_id."""
        with patch("slack.Reminders.DB", DB):
            # Add a reminder with channel_id
            add_result = add_reminder(
                user_id="U123",
                text="Channel reminder",
                ts="1678886600",
                channel_id="C123",
            )
            reminder_id = add_result["reminder"]["id"]
            
            # Get info about the reminder
            result = get_reminder_info(reminder_id)
            self.assertTrue(result["ok"])
            self.assertEqual(result["reminder"]["id"], reminder_id)
            self.assertEqual(result["reminder"]["text"], "Channel reminder")
            self.assertEqual(result["reminder"]["channel_id"], "C123")

    def test_get_reminder_info_missing_id(self):
        """Test getting info with empty reminder_id raises MissingReminderIdError."""
        with patch("slack.Reminders.DB", DB):
            # Test missing reminder id - should raise MissingReminderIdError
            self.assert_error_behavior(
                get_reminder_info,
                MissingReminderIdError,
                "reminder_id cannot be empty.",
                None,
                "",
            )

    def test_get_reminder_info_not_found(self):
        """Test getting info for non-existent reminder raises ReminderNotFoundError."""
        with patch("slack.Reminders.DB", DB):
            # Test not found - should raise ReminderNotFoundError
            self.assert_error_behavior(
                get_reminder_info,
                ReminderNotFoundError,
                "Reminder with ID 'invalid' not found in database.",
                None,
                "invalid",
            )

    def test_get_reminder_info_invalid_type(self):
        """Test getting info with invalid type raises TypeError."""
        with patch("slack.Reminders.DB", DB):
            # Test invalid type - should raise TypeError
            self.assert_error_behavior(
                get_reminder_info,
                TypeError,
                "reminder_id must be a string.",
                None,
                123,
            )

    def test_get_reminder_info_none_type(self):
        """Test getting info with None raises TypeError."""
        with patch("slack.Reminders.DB", DB):
            # Test None type - should raise TypeError
            self.assert_error_behavior(
                get_reminder_info,
                TypeError,
                "reminder_id must be a string.",
                None,
                None,
            )
