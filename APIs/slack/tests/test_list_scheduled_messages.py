"""
Test cases for the list_scheduled_messages function in the Slack Chat API.

This module contains comprehensive test cases for the list_scheduled_messages function,
including success scenarios and all error conditions.
"""

from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import db
from ..SimulationEngine.custom_errors import (
    InvalidCursorFormatError,
    InvalidTimestampFormatError,
    InvalidLimitValueError,
    CursorOutOfBoundsError
)
from .. import list_scheduled_messages
sample_messages = [
    {
        "id": "msg1",
        "channel": "C123",
        "post_at": 1600000100,
        "text": "Message 1",
    },
    {
        "id": "msg2",
        "channel": "C123",
        "post_at": 1600000150,
        "text": "Message 2",
    },
    {
        "id": "msg3",
        "channel": "C456",
        "post_at": 1600000200,
        "text": "Message 3",
    },
    {
        "id": "msg4",
        "channel": "C123",
        "post_at": 1600000250,
        "text": "Message 4",
    },
    {
        "id": "msg5",
        "channel": "C456",
        "post_at": 1600000300,
        "text": "Message 5",
    },
]


class TestListScheduledMessagesValidation(BaseTestCaseWithErrorHandler):
    """Test cases for the list_scheduled_messages function."""

    def setUp(self):
        db.DB["scheduled_messages"] = list(sample_messages)

    def tearDown(self):
        db.DB["scheduled_messages"] = []

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_channel_type(self, mock_decorator_mode, mock_base_case_mode):
        """Test that invalid channel type raises TypeError."""
        self.assert_error_behavior(
            list_scheduled_messages,
            TypeError,
            "channel must be a string or None, got int",
            channel=123,
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_cursor_type(self, mock_decorator_mode, mock_base_case_mode):
        """Test that invalid cursor type raises TypeError."""
        self.assert_error_behavior(
            list_scheduled_messages,
            TypeError,
            "cursor must be a string or None, got int",
            cursor=123,
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_latest_type(self, mock_decorator_mode, mock_base_case_mode):
        self.assert_error_behavior(
            list_scheduled_messages,
            TypeError,
            "latest must be a string or None, got int",
            latest=12345,
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_limit_type(self, mock_decorator_mode, mock_base_case_mode):
        self.assert_error_behavior(
            list_scheduled_messages,
            TypeError,
            "limit must be an integer or None, got str",
            limit="not-an-int",
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_limit_type_bool_true(self, mock_decorator_mode, mock_base_case_mode):
        """Test that boolean True for limit raises TypeError."""
        self.assert_error_behavior(
            list_scheduled_messages,
            TypeError,
            "limit must be an integer or None, got bool",
            limit=True,
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_limit_type_bool_false(self, mock_decorator_mode, mock_base_case_mode):
        """Test that boolean False for limit raises TypeError."""
        self.assert_error_behavior(
            list_scheduled_messages,
            TypeError,
            "limit must be an integer or None, got bool",
            limit=False,
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_oldest_type(self, mock_decorator_mode, mock_base_case_mode):
        self.assert_error_behavior(
            list_scheduled_messages,
            TypeError,
            "oldest must be a string or None, got list",
            oldest=[],
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_team_id_type(self, mock_decorator_mode, mock_base_case_mode):
        self.assert_error_behavior(
            list_scheduled_messages,
            TypeError,
            "team_id must be a string or None, got bool",
            team_id=True,
        )

    # --- Value/Format Validation Tests (These should raise exceptions) ---
    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_cursor_format_non_numeric(
        self, mock_decorator_mode, mock_base_case_mode
    ):
        self.assert_error_behavior(
            list_scheduled_messages,
            InvalidCursorFormatError,
            "cursor 'abc' is not a valid integer string.",
            cursor="abc",
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_cursor_format_negative(
        self, mock_decorator_mode, mock_base_case_mode
    ):
        self.assert_error_behavior(
            list_scheduled_messages,
            InvalidCursorFormatError,
            "cursor '-1' is not a valid integer string.",
            cursor="-1",
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_latest_format(self, mock_decorator_mode, mock_base_case_mode):
        self.assert_error_behavior(
            list_scheduled_messages,
            InvalidTimestampFormatError,
            "latest timestamp 'not-a-timestamp' is not a valid numeric string.",
            latest="not-a-timestamp",
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_oldest_format(self, mock_decorator_mode, mock_base_case_mode):
        self.assert_error_behavior(
            list_scheduled_messages,
            InvalidTimestampFormatError,
            "oldest timestamp 'invalid' is not a valid numeric string.",
            oldest="invalid",
        )

    @patch("common_utils.base_case.get_package_error_mode", return_value="raise")
    @patch(
        "common_utils.error_handling.get_package_error_mode",
        return_value="raise",
    )
    def test_invalid_limit_value_negative(
        self, mock_decorator_mode, mock_base_case_mode
    ):
        self.assert_error_behavior(
            list_scheduled_messages,
            InvalidLimitValueError,
            "limit must be a non-negative integer, got -5",
            limit=-5,
        )

    def test_valid_input_all_none(self):
        result = list_scheduled_messages()
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), len(sample_messages))
        self.assertIsNone(result["response_metadata"]["next_cursor"])

    def test_valid_input_with_channel_filter(self):
        result = list_scheduled_messages(channel="C123")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), 3)
        self.assertTrue(
            all(msg["channel"] == "C123" for msg in result["scheduled_messages"])
        )

    def test_valid_input_with_oldest_filter(self):
        result = list_scheduled_messages(oldest=str(1600000150))
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), 4)  # msg2, msg3, msg4, msg5
        # Messages should be ordered chronologically, so msg2 (1600000150) should be first
        self.assertEqual(result["scheduled_messages"][0]["id"], "msg2")

    def test_valid_input_with_latest_filter(self):
        result = list_scheduled_messages(latest=str(1600000150))
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), 2)
        self.assertEqual(result["scheduled_messages"][-1]["id"], "msg2")

    def test_valid_input_with_limit(self):
        result = list_scheduled_messages(limit=2)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), 2)
        self.assertEqual(result["scheduled_messages"][0]["id"], "msg1")
        self.assertEqual(result["response_metadata"]["next_cursor"], "2")

    def test_valid_input_with_limit_and_cursor(self):
        result = list_scheduled_messages(limit=2, cursor="1")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), 2)
        self.assertEqual(result["scheduled_messages"][0]["id"], "msg2")
        self.assertEqual(result["scheduled_messages"][1]["id"], "msg3")
        self.assertEqual(result["response_metadata"]["next_cursor"], "3")

    def test_valid_input_with_float_timestamp_strings(self):
        result = list_scheduled_messages(oldest="1600000000.0", latest="1600000200.999")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), 3)
        self.assertEqual(result["scheduled_messages"][0]["id"], "msg1")
        self.assertEqual(result["scheduled_messages"][-1]["id"], "msg3")

    def test_valid_input_limit_greater_than_items(self):
        result = list_scheduled_messages(limit=100)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), len(sample_messages))
        self.assertIsNone(result["response_metadata"]["next_cursor"])

    def test_valid_input_cursor_at_end(self):
        result = list_scheduled_messages(cursor=str(len(sample_messages) - 1), limit=2)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), 1)
        self.assertEqual(result["scheduled_messages"][0]["id"], "msg5")
        self.assertIsNone(result["response_metadata"]["next_cursor"])

    def test_runtime_error_cursor_out_of_bounds(self):
        """Test cursor that is valid format but out of bounds for current data."""

        # Case 1: Cursor is out of bounds with existing data

        with self.assertRaises(CursorOutOfBoundsError) as context:
            list_scheduled_messages(cursor="100", limit=5)
        self.assertEqual(str(context.exception), "invalid_cursor_out_of_bounds")

        # Case 2: Cursor is "0" and data is empty
        db.DB["scheduled_messages"] = []

        with self.assertRaises(CursorOutOfBoundsError) as context:
            list_scheduled_messages(cursor="0", limit=5)
        self.assertEqual(str(context.exception), "invalid_cursor_out_of_bounds")

    def test_runtime_error_cursor_out_of_bounds_after_filter(self):
        """Test cursor out of bounds after messages are filtered."""
        db.DB["scheduled_messages"] = [
            {
                "id": "msg_single",
                "channel": "C_SINGLE",
                "post_at": 1700000000,
                "text": "Single Message",
            }
        ]
        # After filtering for "C_SINGLE", filtered_messages has 1 item. Cursor "1" is len(filtered_messages).
        with self.assertRaises(CursorOutOfBoundsError) as context:
            list_scheduled_messages(channel="C_SINGLE", cursor="1", limit=1)
        self.assertEqual(str(context.exception), "invalid_cursor_out_of_bounds")

    def test_no_messages_in_db(self):
        db.DB["scheduled_messages"] = []
        result = list_scheduled_messages()
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), 0)
        self.assertIsNone(result["response_metadata"]["next_cursor"])

    def test_exact_limit_no_next_cursor(self):
        result = list_scheduled_messages(limit=len(sample_messages))
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["scheduled_messages"]), len(sample_messages))
        self.assertIsNone(result["response_metadata"]["next_cursor"])

        result_with_cursor = list_scheduled_messages(cursor="2", limit=3)
        self.assertTrue(result_with_cursor["ok"])
        self.assertEqual(len(result_with_cursor["scheduled_messages"]), 3)
        self.assertIsNone(result_with_cursor["response_metadata"]["next_cursor"])
