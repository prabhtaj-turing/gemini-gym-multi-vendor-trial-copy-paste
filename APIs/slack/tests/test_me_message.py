"""
Test cases for the send_me_message function in the Slack Chat API.

This module contains comprehensive test cases for the send_me_message function,
including success scenarios and all error conditions.
"""

import time
from contextlib import contextmanager
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import send_me_message
from ..SimulationEngine.custom_errors import InvalidChannelError, InvalidTextError, UserNotInConversationError, ChannelNotFoundError

# Global DB for testing purposes
DB = {}

@contextmanager
def patch_both_dbs(test_db):
    """Helper to patch both Chat.DB and utils.DB with the same test database."""
    with patch("slack.Chat.DB", test_db), patch("slack.SimulationEngine.utils.DB", test_db):
        yield


class TestMeMessage(BaseTestCaseWithErrorHandler):
    """Test cases for the send_me_message function."""

    def setUp(self):
        """Initialize test state."""
        global DB
        DB.clear()
        DB.update(
            {
                "current_user": {"id": "U123", "name": "user1", "is_admin": True},
                "users": {
                    "U123": {"id": "U123", "name": "user1"},
                    "U456": {"id": "U456", "name": "user2"},
                },
                "channels": {
                    "C123": {
                        "id": "C123",
                        "name": "general",
                        "is_archived": False,
                        "messages": [
                            {
                                "user": "U123",
                                "text": "Hello, World!",
                                "ts": "123456789.12345",
                                "thread_ts": "123456789.12345",
                                "replies": [
                                    {
                                        "user": "U456",
                                        "text": "Reply",
                                        "ts": "123456790.12345",
                                    }
                                ],
                            }
                        ],
                        "conversations": {"members": ["U123"]},
                    },
                    "C456": {
                        "id": "C456",
                        "name": "random",
                        "is_archived": False,
                        "messages": [],
                    },
                    "C789": {
                        "id": "C789",
                        "name": "private-channel",
                        "is_archived": True,
                        "messages": [],
                    },
                },
                "scheduled_messages": [],
                "ephemeral_messages": [],
            }
        )

        # Import exception types
        self.InvalidChannelError = InvalidChannelError
        self.InvalidTextError = InvalidTextError

        # Mock time.time() for consistent timestamps in tests
        self.original_time_time = time.time
        self.mock_timestamp = "1234567890.12345"
        time.time = lambda: float(self.mock_timestamp)

    def tearDown(self):
        """Restore original time.time after each test."""
        time.time = self.original_time_time

    def test_meMessage_success(self):
        """Test successful me message sending."""
        # Use channel C123 (general) which exists in the new setUp
        with patch_both_dbs(DB):
            result = send_me_message("U123", "C123", "Hello!")
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["channel"], "C123")
        self.assertEqual(result["text"], "Hello!")
        self.assertTrue("ts" in result)
        self.assertEqual(result["subtype"], "me_message")

    def test_meMessage_invalid_channel(self):
        """Test that meMessage raises InvalidChannelError for an empty channel string."""
        with self.assertRaises(InvalidChannelError) as context:
            send_me_message(user_id="user123", channel="", text="Hello!")
        self.assertEqual(str(context.exception), "invalid_channel")

    def test_meMessage_invalid_text(self):
        """Test that meMessage raises InvalidTextError for an empty text string."""
        with self.assertRaises(InvalidTextError) as context:
            send_me_message(user_id="user123", channel="C123", text="")
        self.assertEqual(str(context.exception), "invalid_text")

    # Type validation tests
    def test_none_user_id(self):
        """Test that None user_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=send_me_message,
            expected_exception_type=TypeError,
            expected_message="argument 'user_id' must be a string, got nonetype",
            user_id=None,
            channel="C123",
            text="Valid text",
        )

    def test_none_channel(self):
        """Test that None channel raises TypeError."""
        self.assert_error_behavior(
            func_to_call=send_me_message,
            expected_exception_type=TypeError,
            expected_message="argument 'channel' must be a string, got nonetype",
            user_id="U123",
            channel=None,
            text="Valid text",
        )

    def test_none_text(self):
        """Test that None text raises TypeError."""
        self.assert_error_behavior(
            func_to_call=send_me_message,
            expected_exception_type=TypeError,
            expected_message="argument 'text' must be a string, got nonetype",
            user_id="U123",
            channel="C123",
            text=None,
        )

    def test_valid_input_comprehensive(self):
        """Test that valid input is accepted and processed with comprehensive verification."""
        user_id = "U123"
        channel = "C123"
        text = "Hello there!"

        with patch_both_dbs(DB):
            result = send_me_message(user_id=user_id, channel=channel, text=text)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("channel"), channel)
        self.assertEqual(result.get("text"), text)
        self.assertEqual(result.get("ts"), self.mock_timestamp)
        self.assertEqual(result.get("subtype"), "me_message")

        # Verify data was stored in the mock DB
        self.assertIn(channel, DB["channels"])
        self.assertEqual(len(DB["channels"][channel]["messages"]), 2)  # Original + new message
        stored_message = DB["channels"][channel]["messages"][-1]  # Get the last message
        self.assertEqual(stored_message["user"], user_id)
        self.assertEqual(stored_message["text"], text)
        self.assertEqual(stored_message["ts"], self.mock_timestamp)
        self.assertEqual(stored_message["subtype"], "me_message")

    def test_invalid_user_id_type(self):
        """Test that invalid user_id type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=send_me_message,
            expected_exception_type=TypeError,
            expected_message="argument 'user_id' must be a string, got int",
            user_id=123,
            channel="C123",
            text="Valid text",
        )

    def test_invalid_channel_type(self):
        """Test that invalid channel type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=send_me_message,
            expected_exception_type=TypeError,
            expected_message="argument 'channel' must be a string, got list",
            user_id="U123",
            channel=["C123"],
            text="Valid text",
        )

    def test_invalid_text_type(self):
        """Test that invalid text type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=send_me_message,
            expected_exception_type=TypeError,
            expected_message="argument 'text' must be a string, got bool",
            user_id="U123",
            channel="C123",
            text=True,
        )

    def test_me_message_with_channel_name(self):
        """Test send_me_message using channel name."""
        with patch_both_dbs(DB):
            result = send_me_message(user_id="U123", channel="general", text="Me message via name")
            self.assertTrue(result["ok"])
            self.assertEqual(result["channel"], "C123")  # Should return resolved channel ID
            self.assertEqual(result["text"], "Me message via name")
            self.assertEqual(result["subtype"], "me_message")
            
            # Verify message was stored in correct channel
            self.assertEqual(len(DB["channels"]["C123"]["messages"]), 2)  # 1 existing + 1 new
            stored_message = DB["channels"]["C123"]["messages"][-1]
            self.assertEqual(stored_message["text"], "Me message via name")
            self.assertEqual(stored_message["subtype"], "me_message")

    def test_me_message_nonexistent_channel_name(self):
        """Test send_me_message with non-existent channel name."""
        with patch_both_dbs(DB):
            from ..SimulationEngine.custom_errors import ChannelNotFoundError
            self.assert_error_behavior(
                send_me_message, 
                ChannelNotFoundError,
                "Channel 'nonexistent' not found in database.",
                user_id="U123", 
                channel="nonexistent", 
                text="Test"
            )

    def test_me_message_backward_compatible_with_channel_ids(self):
        """Test that send_me_message still works with channel IDs (backward compatibility)."""
        with patch_both_dbs(DB):
            result = send_me_message(user_id="U123", channel="C123", text="Me via ID")
            self.assertTrue(result["ok"])
            self.assertEqual(result["channel"], "C123")
            self.assertEqual(result["subtype"], "me_message")

    # Hash handling tests
    @patch("slack.SimulationEngine.utils.DB", new_callable=lambda: DB)
    @patch("slack.Chat.DB", new_callable=lambda: DB)
    def test_me_message_with_hash_channel_name(self, mock_chat_db, mock_utils_db):
        """Test send_me_message using channel name with hash symbol - should resolve to channel ID."""
        result = send_me_message(user_id="U123", channel="#general", text="Me message via #general")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "C123")  # Should resolve to channel ID
        self.assertEqual(result["text"], "Me message via #general")
        self.assertEqual(result["subtype"], "me_message")

    @patch("slack.SimulationEngine.utils.DB", new_callable=lambda: DB)
    @patch("slack.Chat.DB", new_callable=lambda: DB)
    def test_me_message_with_hash_channel_id(self, mock_chat_db, mock_utils_db):
        """Test send_me_message using channel ID with hash symbol - should resolve to same ID."""
        result = send_me_message(user_id="U123", channel="#C123", text="Me message via #C123")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "C123")  # Should resolve to same channel ID
        self.assertEqual(result["text"], "Me message via #C123")
        self.assertEqual(result["subtype"], "me_message")

    def test_me_message_with_hash_nonexistent_channel(self):
        """Test send_me_message with non-existent channel name starting with hash."""
        with patch_both_dbs(DB):
            from ..SimulationEngine.custom_errors import ChannelNotFoundError
            self.assert_error_behavior(
                send_me_message, 
                ChannelNotFoundError,
                "Channel '#nonexistent' not found in database.",
                user_id="U123", 
                channel="#nonexistent", 
                text="Test"
            )

    def test_me_message_user_not_in_conversation(self):
        """Test that send_me_message raises UserNotInConversationError if user is not in conversation."""
        with patch_both_dbs(DB):
            self.assert_error_behavior(
                send_me_message,
                UserNotInConversationError,
                "User 'U456' is not in conversation 'C123'.",
                user_id="U456",
                channel="C123",
                text="Me message",
            )
    
    def test_me_message_channel_not_found(self):
        """Test that send_me_message raises ChannelNotFoundError if channel is not found."""
        with patch_both_dbs(DB):
            self.assert_error_behavior(
                send_me_message,
                ChannelNotFoundError,
                "Channel 'C999' not found in database.",
                user_id="U123",
                channel="C999",
                text="Me message",
            )