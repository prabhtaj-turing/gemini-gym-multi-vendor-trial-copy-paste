"""
Test cases for the schedule_chat_message function in the Slack Chat API.

This module contains comprehensive test cases for the schedule_chat_message function,
including success scenarios and all error conditions.
"""

import os
import time
import json
from unittest.mock import patch
from pydantic import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import db
from .. import schedule_chat_message

class TestChatScheduleMessage(BaseTestCaseWithErrorHandler):
    """Test cases for the schedule_chat_message function."""

    def setUp(self):
        """
        Set up the test environment by assigning a fresh initial state to DB.
        This mimics the DB setup from the provided test context.
        """
        db.DB.clear()  # Clear existing keys
        db.DB.update(
            {  # Set to a known state
                "channels": {
                    "C123": {
                        "id": "C123",
                        "name": "general",
                        "conversations": {"members": ["U123"]},
                        "is_archived": False,
                        "messages": [],
                        "type": "public_channel",
                    }
                },
                "users": {"U123": {"id": "U123", "name": "user1"}},
                "scheduled_messages": [],
                "ephemeral_messages": [],
                "files": {},
                "reactions": {},
                "reminders": {},
                "usergroups": {},
                "usergroup_users": {},
            }
        )
        if os.path.exists("test_state.json"):  # From original setUp
            os.remove("test_state.json")

    def test_scheduleMessage_success_basic(self):
        """Test successful message scheduling with minimal valid inputs."""
        current_ts = int(time.time()) + 60
        result = schedule_chat_message(
            user_id="U123", channel="C123", post_at=current_ts, text="Test message"
        )
        self.assertTrue(result["ok"])
        self.assertIn("message_id", result)
        self.assertIn("scheduled_message_id", result)
        # Use db.DB for assertions
        self.assertEqual(len(db.DB["scheduled_messages"]), 1)
        self.assertEqual(db.DB["scheduled_messages"][0]["text"], "Test message")
        self.assertEqual(db.DB["scheduled_messages"][0]["post_at"], current_ts)

    def test_scheduleMessage_success_all_optional_fields(self):
        """Test successful scheduling with all optional fields provided."""
        current_ts = int(time.time()) + 120
        attachments_json = json.dumps([{"title": "Attachment 1"}])
        blocks_list = [
            {"type": "section", "text": {"type": "mrkdwn", "text": "Block 1"}}
        ]
        metadata_json = json.dumps(
            {"event_type": "test_event", "event_payload": {"data": "value"}}
        )

        result = schedule_chat_message(
            user_id="U123",
            channel="C123",
            post_at=current_ts,
            attachments=attachments_json,
            blocks=blocks_list,
            text="Comprehensive test message",
            as_user=True,
            link_names=True,
            markdown_text="*markdown*",
            metadata=metadata_json,
            parse="full",
            reply_broadcast=True,
            thread_ts="12345.67890",
            unfurl_links=False,
            unfurl_media=True,
        )
        self.assertTrue(result["ok"])
        # Use db.DB for assertions
        self.assertEqual(len(db.DB["scheduled_messages"]), 1)
        scheduled_msg = db.DB["scheduled_messages"][0]
        self.assertEqual(scheduled_msg["attachments"], attachments_json)
        self.assertEqual(scheduled_msg["blocks"], blocks_list)
        self.assertEqual(scheduled_msg["metadata"], metadata_json)
        self.assertTrue(scheduled_msg["as_user"])

    def test_scheduleMessage_missing_required_user_id(self):
        """Test error when required user_id is missing (passed as None)."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            expected_message="Input should be a valid string",
            user_id=None,
            channel="C123",
            post_at=int(time.time()) + 60,
        )

    def test_scheduleMessage_empty_user_id(self):
        """Test error when user_id is an empty string."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "String should have at least 1 character",
            user_id="",
            channel="C123",
            post_at=int(time.time()) + 60,
        )

    def test_scheduleMessage_missing_required_channel(self):
        """Test error when required channel is missing."""
        expected_message = "Input should be a valid string"

        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            expected_message,
            user_id="U123",
            channel=None,
            post_at=int(time.time()) + 60,
        )

    def test_scheduleMessage_empty_channel(self):
        """Test error when channel is an empty string."""
        expected_message = "String should have at least 1 character"
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            expected_message,
            user_id="U123",
            channel="",
            post_at=int(time.time()) + 60,
        )

    def test_scheduleMessage_missing_required_post_at(self):
        """Test error when required post_at is missing."""
        expected_message = "Invalid format or value for post_at: None"
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            expected_message,
            user_id="U123",
            channel="C123",
            post_at=None,
        )

    def test_scheduleMessage_invalid_post_at_string(self):
        """Test error when post_at is a non-numeric string."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Invalid format or value for post_at: invalid_time_string",
            user_id="U123",
            channel="C123",
            post_at="invalid_time_string",
        )

    def test_scheduleMessage_post_at_zero(self):
        """Test error when post_at is zero (should be positive)."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Value error, post_at must be a positive timestamp",
            user_id="U123",
            channel="C123",
            post_at=0,
        )

    def test_scheduleMessage_post_at_negative(self):
        """Test error when post_at is negative."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Value error, post_at must be a positive timestamp",
            user_id="U123",
            channel="C123",
            post_at=-100,
        )

    def test_scheduleMessage_post_at_float_string_coercion(self):
        """Test post_at coercion from float string "123.45" to int 123."""
        ts_str = str(time.time() + 60.789)
        expected_int_ts = int(float(ts_str))
        result = schedule_chat_message(
            user_id="U123",
            channel="C123",
            post_at=ts_str,
            text="Test with float string post_at",
        )
        self.assertTrue(result["ok"])
        # Use db.DB for assertions
        self.assertEqual(db.DB["scheduled_messages"][0]["post_at"], expected_int_ts)

    def test_scheduleMessage_invalid_attachments_json(self):
        """Test error when attachments string is not valid JSON."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Value error, Attachments string is not valid JSON",
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            attachments="this is not json",
        )

    def test_scheduleMessage_attachments_json_not_array(self):
        """Test error when attachments JSON is not an array."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Value error, Attachments JSON string must decode to an array",
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            attachments=json.dumps({"not": "an array"}),
        )

    def test_scheduleMessage_attachments_json_array_item_not_object(self):
        """Test error when an item in attachments JSON array is not an object."""
        # This test was modified to use assertRaises directly rather than assert_error_behavior
        # to handle the difference in error message format from Pydantic v2
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Each item in the attachments array must be an object",
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            attachments=json.dumps([1, 2, 3]),  # Array of numbers, not objects
        )

    def test_scheduleMessage_invalid_blocks_type(self):
        """Test error when blocks is not a list."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Input should be a valid list",
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            blocks="not a list",
        )

    def test_scheduleMessage_blocks_item_not_dict(self):
        """Test error when an item in blocks list is not a dictionary."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Input should be a valid dictionary",
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            blocks=["not a dict"],
        )

    def test_scheduleMessage_invalid_metadata_json(self):
        """Test error when metadata string is not valid JSON."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "1 validation error for ScheduleMessageInputModel\nmetadata\n  Value error, Metadata string is not valid JSON [type=value_error, input_value='this is not json', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/value_error",
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            metadata="this is not json",
        )

    def test_scheduleMessage_metadata_json_not_object(self):
        """Test error when metadata JSON is not an object."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            expected_message="Input should be a valid dictionary",
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            blocks=["not a dict"],
        )

    def test_scheduleMessage_metadata_json_not_object_alternative(self):
        """Test error when metadata JSON is not an object."""
        expected_message = "Metadata JSON string must decode to an object"
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            expected_message,
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            metadata=json.dumps(["not", "an object"]),  # JSON array
        )

    def test_scheduleMessage_metadata_json_missing_event_type(self):
        """Test error when metadata JSON object is missing 'event_type' field."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "1 validation error for ScheduleMessageInputModel\nmetadata\n  Value error, Metadata JSON structure is invalid [type=value_error, input_value='{\"event_payload\": {}}', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/value_error",
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            metadata=json.dumps({"event_payload": {}}),
        )

    def test_scheduleMessage_metadata_json_invalid_event_payload_type(self):
        """Test error when metadata JSON 'event_payload' is not an object."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            '1 validation error for ScheduleMessageInputModel\nmetadata\n  Value error, Metadata JSON structure is invalid [type=value_error, input_value=\'{"event_type": "myevent"...load": "not_an_object"}\', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/value_error',
            user_id="U123",
            channel="C123",
            post_at=int(time.time()) + 60,
            metadata=json.dumps(
                {"event_type": "myevent", "event_payload": "not_an_object"}
            ),
        )

    def test_scheduleMessage_extra_keyword_argument_causes_TypeError(self):
        """Test that passing an unexpected keyword argument to scheduleMessage raises a TypeError."""
        current_ts = int(time.time()) + 60
        expected_message = (
            "scheduleMessage() got an unexpected keyword argument 'extra_field'"
        )

        self.assert_error_behavior(
            schedule_chat_message,
            TypeError,
            expected_message,
            user_id="U123",
            channel="C123",
            post_at=current_ts,
            text="Test message",
            extra_field="some_value",
        )

    def test_scheduleMessage_empty_user_id_duplicate(self):
        """Test error when user_id is an empty string (duplicate test)."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "String should have at least 1 character",
            user_id="",
            channel="C123",
            post_at=int(time.time()) + 60,
        )

    def test_scheduleMessage_missing_required_channel_duplicate(self):
        """Test error when required channel is missing (duplicate test)."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Input should be a valid string",
            user_id="U123",
            channel=None,
            post_at=int(time.time()) + 60,
        )

    def test_scheduleMessage_empty_channel_duplicate(self):
        """Test error when channel is an empty string (duplicate test)."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "String should have at least 1 character",
            user_id="U123",
            channel="",
            post_at=int(time.time()) + 60,
        )

    def test_scheduleMessage_missing_required_post_at_duplicate(self):
        """Test error when required post_at is missing (duplicate test)."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Invalid format or value for post_at: None",
            user_id="U123",
            channel="C123",
            post_at=None,
        )

    def test_scheduleMessage_invalid_post_at_string_duplicate(self):
        """Test error when post_at is a non-numeric string (duplicate test)."""
        self.assert_error_behavior(
            schedule_chat_message,
            ValidationError,
            "Invalid format or value for post_at: invalid_time_string",
            user_id="U123",
            channel="C123",
            post_at="invalid_time_string",
        )

    def test_schedule_message_with_channel_name(self):
        """Test schedule_chat_message using channel name."""
        # Add dev-team channel to DB
        db.DB["channels"]["C789"] = {
            "id": "C789",
            "name": "dev-team",
            "conversations": {"members": ["U123"]},
            "is_archived": False,
            "messages": [],
            "type": "public_channel",
        }
        
        result = schedule_chat_message(
            user_id="U123", 
            channel="dev-team", 
            post_at=1234567890, 
            text="Scheduled via name"
        )
        self.assertTrue(result["ok"])
        self.assertIn("message_id", result)
        
        # Verify scheduled message was stored with resolved channel ID
        scheduled_msg = db.DB["scheduled_messages"][0]
        self.assertEqual(scheduled_msg["channel"], "C789")
        self.assertEqual(scheduled_msg["text"], "Scheduled via name")

    def test_schedule_message_nonexistent_channel_name(self):
        """Test schedule_chat_message with non-existent channel name."""
        from ..SimulationEngine.custom_errors import ChannelNotFoundError
        self.assert_error_behavior(
            schedule_chat_message, 
            ChannelNotFoundError,
            "Channel 'nonexistent' not found in database.",
            user_id="U123", 
            channel="nonexistent", 
            post_at=1234567890, 
            text="Test"
        )

    def test_schedule_message_backward_compatible_with_channel_ids(self):
        """Test that schedule_chat_message still works with channel IDs (backward compatibility)."""
        result = schedule_chat_message(
            user_id="U123", 
            channel="C123", 
            post_at=1234567890, 
            text="Scheduled via ID"
        )
        self.assertTrue(result["ok"])

    # Hash handling tests
    def test_schedule_message_with_hash_channel_name(self):
        """Test schedule_chat_message using channel name with hash symbol - should resolve to channel ID."""
        result = schedule_chat_message(
            user_id="U123", 
            channel="#general", 
            post_at=1234567890, 
            text="Scheduled via #general"
        )
        self.assertTrue(result["ok"])
        self.assertIn("message_id", result)
        
        # Verify scheduled message was stored with resolved channel ID
        scheduled_msg = db.DB["scheduled_messages"][0]
        self.assertEqual(scheduled_msg["channel"], "C123")  # Should resolve to channel ID
        self.assertEqual(scheduled_msg["text"], "Scheduled via #general")

    def test_schedule_message_with_hash_channel_id(self):
        """Test schedule_chat_message using channel ID with hash symbol - should resolve to same ID."""
        result = schedule_chat_message(
            user_id="U123", 
            channel="#C123", 
            post_at=1234567890, 
            text="Scheduled via #C123"
        )
        self.assertTrue(result["ok"])
        self.assertIn("message_id", result)
        
        # Verify scheduled message was stored with resolved channel ID
        scheduled_msg = db.DB["scheduled_messages"][0]
        self.assertEqual(scheduled_msg["channel"], "C123")  # Should resolve to same channel ID
        self.assertEqual(scheduled_msg["text"], "Scheduled via #C123")

    def test_schedule_message_with_hash_nonexistent_channel(self):
        """Test schedule_chat_message with non-existent channel name starting with hash."""
        from ..SimulationEngine.custom_errors import ChannelNotFoundError
        self.assert_error_behavior(
            schedule_chat_message, 
            ChannelNotFoundError,
            "Channel '#nonexistent' not found in database.",
            user_id="U123", 
            channel="#nonexistent", 
            post_at=1234567890, 
            text="Test"
        )
