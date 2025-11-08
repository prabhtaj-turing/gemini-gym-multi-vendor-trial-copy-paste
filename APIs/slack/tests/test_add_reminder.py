"""
Test cases for the add_reminder function in the Slack Reminders API.

This module contains comprehensive test cases for the add_reminder function,
including success scenarios and all error conditions.
"""

from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import add_reminder

class TestAddReminder(BaseTestCaseWithErrorHandler):
    """Test cases for the add_reminder function."""
    
    def setUp(self):
        """Reset DB state and other relevant states before each test."""
        global DB
        DB = {
            "users": {
                "test_user_1": {"name": "Test User One"},
                "test_user_2": {"name": "Test User Two"},
            },
            "reminders": {},
        }

    def test_valid_input_all_fields_provided(self):
        """Test successful reminder creation when all arguments are valid and channel_id is provided."""
        # Patch DB to ensure our test user exists
        with patch("slack.Reminders.DB", DB):
            result = add_reminder(
                user_id="test_user_1",
                text="Remember to test all fields",
                ts="1678886400",
                channel_id="general_channel",
            )
            self.assertTrue(result.get("ok"), "Request should be successful.")
            self.assertIn("reminder", result, "Response should contain reminder data.")
            reminder = result["reminder"]
            self.assertEqual(reminder["user_id"], "test_user_1")
            self.assertEqual(reminder["text"], "Remember to test all fields")
            self.assertEqual(reminder["time"], "1678886400")
            self.assertEqual(reminder["channel_id"], "general_channel")
            self.assertIn(
                reminder["id"],
                DB.get("reminders", {}),
                "Reminder should be stored in DB.",
            )

    def test_valid_input_channel_id_omitted(self):
        """Test successful creation with channel_id omitted (should default to None)."""
        with patch("slack.Reminders.DB", DB):
            result = add_reminder(
                user_id="test_user_1",
                text="Test with channel_id omitted",
                ts="1678886401.789",
            )
            self.assertTrue(result.get("ok"))
            reminder = result["reminder"]
            self.assertIsNone(
                reminder["channel_id"], "channel_id should be None if omitted."
            )
            self.assertIn(reminder["id"], DB.get("reminders", {}))

    def test_valid_input_channel_id_explicitly_none(self):
        """Test successful creation with channel_id explicitly set to None."""
        with patch("slack.Reminders.DB", DB):
            result = add_reminder(
                user_id="test_user_1",
                text="Test with channel_id as None",
                ts="1678886402",
                channel_id=None,
            )
            self.assertTrue(result.get("ok"))
            reminder = result["reminder"]
            self.assertIsNone(
                reminder["channel_id"], "channel_id should be None if passed as None."
            )
            self.assertIn(reminder["id"], DB.get("reminders", {}))

    def test_valid_input_channel_id_empty_string(self):
        """Test successful creation with channel_id as an empty string."""
        with patch("slack.Reminders.DB", DB):
            result = add_reminder(
                user_id="test_user_1",
                text="Test with channel_id as empty string",
                ts="1678886403",
                channel_id="",
            )
            self.assertTrue(result.get("ok"))
            reminder = result["reminder"]
            self.assertEqual(
                reminder["channel_id"],
                "",
                "channel_id should be an empty string if passed as such.",
            )
            self.assertIn(reminder["id"], DB.get("reminders", {}))

    # --- Validation Error Tests for user_id ---
    def test_error_user_id_python_missing_arg(self):
        """Test Python TypeError when user_id (required positional arg) is completely missing from call."""
        with self.assertRaisesRegex(
            TypeError, "required positional argument:.*'user_id'"
        ):
            add_reminder(text="some text", ts="12345")

    def test_error_user_id_none(self):
        """Test TypeError when user_id is None."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                func_to_call=add_reminder,
                expected_exception_type=TypeError,
                expected_message="user_id must be a string.",
                user_id=None,
                text="text",
                ts="123",
            )

    def test_error_user_id_empty(self):
        """Test ValueError for empty user_id."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                add_reminder,
                ValueError,
                "user_id cannot be empty.",
                user_id="",
                text="text",
                ts="123",
            )

    def test_error_user_id_wrong_type(self):
        """Test TypeError for user_id with incorrect type."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "user_id must be a string.",
                user_id=12345,
                text="text",
                ts="123",
            )

    # --- Validation Error Tests for text ---
    def test_error_text_python_missing_arg(self):
        """Test Python TypeError when text (required positional arg) is missing."""
        with self.assertRaisesRegex(TypeError, "required positional argument:.*'text'"):
            add_reminder(user_id="uid", ts="12345")

    def test_error_text_none(self):
        """Test TypeError for text=None."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "text must be a string.",
                user_id="uid",
                text=None,
                ts="123",
            )

    def test_error_text_empty(self):
        """Test ValueError for empty text."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                add_reminder,
                ValueError,
                "text cannot be empty.",
                user_id="uid",
                text="",
                ts="123",
            )

    def test_error_text_wrong_type(self):
        """Test TypeError for text with incorrect type."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "text must be a string.",
                user_id="uid",
                text=True,
                ts="123",
            )

    # --- Validation Error Tests for ts ---
    def test_error_ts_python_missing_arg(self):
        """Test Python TypeError when ts (required positional arg) is missing."""
        with self.assertRaisesRegex(TypeError, "required positional argument:.*'ts'"):
            add_reminder(user_id="uid", text="text")

    def test_error_ts_none(self):
        """Test TypeError for ts=None."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "ts must be a string.",
                user_id="uid",
                text="text",
                ts=None,
            )

    def test_error_ts_empty(self):
        """Test InvalidTimestampFormatError for empty ts."""
        with patch("slack.Reminders.DB", DB):
            from slack.SimulationEngine.custom_errors import InvalidTimestampFormatError

            self.assert_error_behavior(
                add_reminder,
                InvalidTimestampFormatError,
                "ts cannot be empty.",
                user_id="uid",
                text="text",
                ts="",
            )

    def test_error_ts_wrong_type(self):
        """Test TypeError for ts with incorrect type."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "ts must be a string.",
                user_id="uid",
                text="text",
                ts=123.45,
            )

    def test_error_ts_invalid_format(self):
        """Test InvalidTimestampFormatError for ts with invalid numeric string format."""
        with patch("slack.Reminders.DB", DB):
            from slack.SimulationEngine.custom_errors import InvalidTimestampFormatError

            self.assert_error_behavior(
                add_reminder,
                InvalidTimestampFormatError,
                "ts must be a string representing a valid numeric timestamp (e.g., '1678886400' or '1678886400.5'), got: 'not-a-number'",
                user_id="uid",
                text="text",
                ts="not-a-number",
            )

    # --- Validation Error Tests for channel_id ---
    def test_error_channel_id_wrong_type(self):
        """Test TypeError for channel_id with incorrect type (when not None)."""
        with patch("slack.Reminders.DB", DB):
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "channel_id must be a string or None.",
                user_id="uid",
                text="text",
                ts="123",
                channel_id=12345,
            )

    def test_core_logic_error_user_not_found(self):
        """Test UserNotFoundError raised when user_id is valid but not in DB."""
        with patch("slack.Reminders.DB", DB):
            from slack.SimulationEngine.custom_errors import UserNotFoundError

            self.assert_error_behavior(
                add_reminder,
                UserNotFoundError,
                "User with ID 'unknown_user' not found in database.",
                None,
                user_id="unknown_user",
                text="This reminder won't be created",
                ts="1234567890",
            )
            # Verify that no reminder was added to the DB for this failed case
            self.assertFalse(
                any(
                    r["user_id"] == "unknown_user"
                    for r in DB.get("reminders", {}).values()
                ),
                "No reminder for 'unknown_user' should be in DB.",
            )

    def test_add_reminder_type_validation(self):
        """Test type validation for all parameters of add function."""
        with patch("slack.Reminders.DB", DB):
            # Test non-string user_id
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "user_id must be a string.",
                None,
                user_id=123,
                text="Test",
                ts="1678886400",
            )

            # Test None user_id
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "user_id must be a string.",
                None,
                user_id=None,
                text="Test",
                ts="1678886400",
            )

            # Test non-string text
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "text must be a string.",
                None,
                user_id="test_user_1",
                text=123,
                ts="1678886400",
            )

            # Test None text
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "text must be a string.",
                None,
                user_id="test_user_1",
                text=None,
                ts="1678886400",
            )

            # Test non-string ts
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "ts must be a string.",
                None,
                user_id="test_user_1",
                text="Test",
                ts=1678886400,
            )

            # Test None ts
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "ts must be a string.",
                None,
                user_id="test_user_1",
                text="Test",
                ts=None,
            )

            # Test non-string/non-None channel_id
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "channel_id must be a string or None.",
                None,
                user_id="test_user_1",
                text="Test",
                ts="1678886400",
                channel_id=123,
            )

            # Test list channel_id
            self.assert_error_behavior(
                add_reminder,
                TypeError,
                "channel_id must be a string or None.",
                None,
                user_id="test_user_1",
                text="Test",
                ts="1678886400",
                channel_id=["C123"],
            )

    def test_add_reminder_value_validation(self):
        """Test value validation for parameters of add function."""
        with patch("slack.Reminders.DB", DB):
            from slack.SimulationEngine.custom_errors import InvalidTimestampFormatError

            # Test empty user_id
            self.assert_error_behavior(
                add_reminder,
                ValueError,
                "user_id cannot be empty.",
                None,
                user_id="",
                text="Test",
                ts="1678886400",
            )

            # Test empty text
            self.assert_error_behavior(
                add_reminder,
                ValueError,
                "text cannot be empty.",
                None,
                user_id="test_user_1",
                text="",
                ts="1678886400",
            )

            # Test empty ts
            self.assert_error_behavior(
                add_reminder,
                InvalidTimestampFormatError,
                "ts cannot be empty.",
                None,
                user_id="test_user_1",
                text="Test",
                ts="",
            )

            # Test invalid timestamp format - non-numeric
            self.assert_error_behavior(
                add_reminder,
                InvalidTimestampFormatError,
                "ts must be a string representing a valid numeric timestamp (e.g., '1678886400' or '1678886400.5'), got: 'invalid'",
                None,
                user_id="test_user_1",
                text="Test",
                ts="invalid",
            )

            # Test invalid timestamp format - special characters
            self.assert_error_behavior(
                add_reminder,
                InvalidTimestampFormatError,
                "ts must be a string representing a valid numeric timestamp (e.g., '1678886400' or '1678886400.5'), got: '123abc'",
                None,
                user_id="test_user_1",
                text="Test",
                ts="123abc",
            )

            # Test that channel_id can be empty string (this should work)
            result = add_reminder(
                user_id="test_user_1", text="Test", ts="1678886400", channel_id=""
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["reminder"]["channel_id"], "")

            # Test that channel_id can be None (this should work)
            result = add_reminder(
                user_id="test_user_1", text="Test2", ts="1678886500", channel_id=None
            )
            self.assertTrue(result["ok"])
            self.assertIsNone(result["reminder"]["channel_id"])

    def test_add_reminder_timestamp_edge_cases(self):
        """Test edge cases for timestamp validation."""
        with patch("slack.Reminders.DB", DB):
            # Test valid integer timestamp
            result = add_reminder(user_id="test_user_1", text="Test", ts="1678886400")
            self.assertTrue(result["ok"])

            # Test valid float timestamp
            result = add_reminder(user_id="test_user_1", text="Test", ts="1678886400.5")
            self.assertTrue(result["ok"])

            # Test negative timestamp (should work as it's still numeric)
            result = add_reminder(user_id="test_user_1", text="Test", ts="-1678886400")
            self.assertTrue(result["ok"])

            # Test zero timestamp
            result = add_reminder(user_id="test_user_1", text="Test", ts="0")
            self.assertTrue(result["ok"])

            # Test whitespace in timestamp (Python's float() actually accepts this)
            result = add_reminder(user_id="test_user_1", text="Test", ts=" 1678886400 ")
            self.assertTrue(result["ok"])

            # Test invalid format with letters mixed in
            from slack.SimulationEngine.custom_errors import InvalidTimestampFormatError

            self.assert_error_behavior(
                add_reminder,
                InvalidTimestampFormatError,
                "ts must be a string representing a valid numeric timestamp (e.g., '1678886400' or '1678886400.5'), got: '123.45.67'",
                None,
                user_id="test_user_1",
                text="Test",
                ts="123.45.67",
            )
