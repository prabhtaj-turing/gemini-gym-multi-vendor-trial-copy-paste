"""
Test cases for the complete_reminder function in the Slack Reminders API.

This module contains comprehensive test cases for the complete_reminder function,
including success scenarios and all error conditions.
"""

from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    MissingReminderIdError,
    ReminderNotFoundError,
    MissingCompleteTimestampError,
    InvalidCompleteTimestampError,
    ReminderAlreadyCompleteError,
)
from .. import (add_reminder, complete_reminder)

class TestCompleteReminder(BaseTestCaseWithErrorHandler):
    """Test cases for the complete_reminder function."""

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

    def test_complete_reminder_success(self):
        """Test successful completion of a reminder."""
        # Patch the DB in the Reminders module with our test DB
        with patch("slack.Reminders.DB", DB):
            # Add a reminder
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            self.assertTrue(add_result["ok"])
            reminder_id = add_result["reminder"]["id"]

            # Complete the reminder
            result = complete_reminder(reminder_id, "1678886600")
            self.assertTrue(result["ok"])

            # Check directly in the DB that the reminder was completed
            self.assertIsNotNone(DB["reminders"][reminder_id]["complete_ts"])
            self.assertEqual(DB["reminders"][reminder_id]["complete_ts"], "1678886600")

    def test_complete_reminder_already_completed(self):
        """Test completing an already completed reminder raises ReminderAlreadyCompleteError."""
        with patch("slack.Reminders.DB", DB):
            # Add a reminder
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            reminder_id = add_result["reminder"]["id"]

            # Complete the reminder
            result = complete_reminder(reminder_id, "1678886600")
            self.assertTrue(result["ok"])

            # Try to complete it again (should raise ReminderAlreadyCompleteError)
            self.assert_error_behavior(
                complete_reminder,
                ReminderAlreadyCompleteError,
                f"Reminder with ID '{reminder_id}' is already marked as complete.",
                None,
                reminder_id,
                "1678886601",
            )

    def test_complete_reminder_missing_id(self):
        """Test completing with empty reminder_id raises MissingReminderIdError."""
        with patch("slack.Reminders.DB", DB):
            # Test missing reminder_id - should raise MissingReminderIdError
            self.assert_error_behavior(
                complete_reminder,
                MissingReminderIdError,
                "reminder_id cannot be empty.",
                None,
                "",
                "1678886600",
            )

    def test_complete_reminder_missing_timestamp(self):
        """Test completing with empty complete_ts raises MissingCompleteTimestampError."""
        with patch("slack.Reminders.DB", DB):
            # Add a reminder first
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            reminder_id = add_result["reminder"]["id"]

            # Test missing complete_ts - should raise MissingCompleteTimestampError
            self.assert_error_behavior(
                complete_reminder,
                MissingCompleteTimestampError,
                "complete_ts cannot be empty.",
                None,
                reminder_id,
                "",
            )

    def test_complete_reminder_invalid_timestamp(self):
        """Test completing with invalid complete_ts raises InvalidCompleteTimestampError."""
        with patch("slack.Reminders.DB", DB):
            # Add a reminder first
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            reminder_id = add_result["reminder"]["id"]

            # Test invalid complete_ts - should raise InvalidCompleteTimestampError
            self.assert_error_behavior(
                complete_reminder,
                InvalidCompleteTimestampError,
                "complete_ts must be a string representing a valid numeric timestamp, got: 'invalid'",
                None,
                reminder_id,
                "invalid",
            )

    def test_complete_reminder_not_found(self):
        """Test completing non-existent reminder raises ReminderNotFoundError."""
        with patch("slack.Reminders.DB", DB):
            # Test not found - should raise ReminderNotFoundError
            self.assert_error_behavior(
                complete_reminder,
                ReminderNotFoundError,
                "Reminder with ID 'invalid' not found in database.",
                None,
                "invalid",
                "1678886600",
            )

    def test_complete_reminder_invalid_id_type(self):
        """Test completing with invalid reminder_id type raises TypeError."""
        with patch("slack.Reminders.DB", DB):
            # Test invalid type for reminder_id - should raise TypeError
            self.assert_error_behavior(
                complete_reminder,
                TypeError,
                "reminder_id must be a string.",
                None,
                123,
                "1678886600",
            )

    def test_complete_reminder_invalid_timestamp_type(self):
        """Test completing with invalid complete_ts type raises TypeError."""
        with patch("slack.Reminders.DB", DB):
            # Add a reminder first
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            reminder_id = add_result["reminder"]["id"]

            # Test invalid type for complete_ts - should raise TypeError
            self.assert_error_behavior(
                complete_reminder,
                TypeError,
                "complete_ts must be a string.",
                None,
                reminder_id,
                1678886600,
            )

    def test_complete_reminder_none_types(self):
        """Test completing with None values raises TypeError."""
        with patch("slack.Reminders.DB", DB):
            # Test None reminder_id
            self.assert_error_behavior(
                complete_reminder,
                TypeError,
                "reminder_id must be a string.",
                None,
                None,
                "1678886600",
            )

            # Add a reminder for the timestamp test
            add_result = add_reminder(
                user_id="U123", text="Test reminder", ts="1678886400"
            )
            reminder_id = add_result["reminder"]["id"]

            # Test None complete_ts
            self.assert_error_behavior(
                complete_reminder,
                TypeError,
                "complete_ts must be a string.",
                None,
                reminder_id,
                None,
            )

    def test_complete_reminder_edge_case_timestamps(self):
        """Test completing with edge case timestamp values."""
        with patch("slack.Reminders.DB", DB):
            # Add reminders for testing
            add_result1 = add_reminder(
                user_id="U123", text="Test reminder 1", ts="1678886400"
            )
            reminder_id1 = add_result1["reminder"]["id"]

            add_result2 = add_reminder(
                user_id="U123", text="Test reminder 2", ts="1678886500"
            )
            reminder_id2 = add_result2["reminder"]["id"]

            add_result3 = add_reminder(
                user_id="U123", text="Test reminder 3", ts="1678886600"
            )
            reminder_id3 = add_result3["reminder"]["id"]

            # Test valid float timestamp
            result = complete_reminder(reminder_id1, "1678886400.5")
            self.assertTrue(result["ok"])

            # Test negative timestamp (should work as it's still numeric)
            result = complete_reminder(reminder_id2, "-1678886400")
            self.assertTrue(result["ok"])

            # Test zero timestamp
            result = complete_reminder(reminder_id3, "0")
            self.assertTrue(result["ok"])
