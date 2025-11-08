"""
Test cases for the delete_reminder function in the Slack Reminders API.

This module contains comprehensive test cases for the delete_reminder function,
including success scenarios and all error conditions.
"""

from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    MissingReminderIdError,
    ReminderNotFoundError,
)
from .. import (add_reminder, delete_reminder)

class TestDeleteReminder(BaseTestCaseWithErrorHandler):
    """Test cases for the delete_reminder function."""

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

    def test_delete_reminder_success(self):
        """Test successful deletion of an existing reminder."""
        # Patch the DB in the Reminders module with our test DB
        with patch("slack.Reminders.DB", DB):
            # Add a reminder
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            reminder_id = add_result["reminder"]["id"]

            # Delete the reminder
            result = delete_reminder(reminder_id)
            self.assertTrue(result["ok"])
            self.assertNotIn(reminder_id, DB["reminders"])

    def test_delete_reminder_not_found(self):
        """Test deletion of non-existent reminder raises ReminderNotFoundError."""
        with patch("slack.Reminders.DB", DB):
            # Try to delete a non-existent reminder
            self.assert_error_behavior(
                delete_reminder,
                ReminderNotFoundError,
                "Reminder with ID 'non_existent' not found in database.",
                None,
                "non_existent",
            )

    def test_delete_reminder_already_deleted(self):
        """Test deletion of already deleted reminder raises ReminderNotFoundError."""
        with patch("slack.Reminders.DB", DB):
            # Add a reminder
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            reminder_id = add_result["reminder"]["id"]

            # Delete the reminder
            result = delete_reminder(reminder_id)
            self.assertTrue(result["ok"])

            # Try to delete it again (should fail with ReminderNotFoundError)
            self.assert_error_behavior(
                delete_reminder,
                ReminderNotFoundError,
                f"Reminder with ID '{reminder_id}' not found in database.",
                None,
                reminder_id,
            )

    def test_delete_reminder_missing_id(self):
        """Test deletion with empty reminder_id raises MissingReminderIdError."""
        with patch("slack.Reminders.DB", DB):
            # Test missing reminder id - should raise MissingReminderIdError
            self.assert_error_behavior(
                delete_reminder,
                MissingReminderIdError,
                "reminder_id cannot be empty.",
                None,
                "",
            )

    def test_delete_reminder_invalid_type(self):
        """Test deletion with invalid type raises TypeError."""
        with patch("slack.Reminders.DB", DB):
            # Test invalid type - should raise TypeError
            self.assert_error_behavior(
                delete_reminder,
                TypeError,
                "reminder_id must be a string.",
                None,
                123,
            )

    def test_delete_reminder_none_type(self):
        """Test deletion with None raises TypeError."""
        with patch("slack.Reminders.DB", DB):
            # Test None type - should raise TypeError
            self.assert_error_behavior(
                delete_reminder,
                TypeError,
                "reminder_id must be a string.",
                None,
                None,
            )
