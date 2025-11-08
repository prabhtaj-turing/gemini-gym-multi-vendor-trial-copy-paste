"""
Test cases for the mark_conversation_read function in the Slack Conversations API.

This module contains comprehensive test cases for the mark_conversation_read function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    ChannelNameMissingError,
    TimestampError,
    UserNotInConversationError,
)
from .. import mark_conversation_read

class TestMarkConversationRead(BaseTestCaseWithErrorHandler):
    """Test cases for the mark_conversation_read function."""

    def setUp(self):
        """Setup method to create a fresh DB for each test."""
        self.test_db = {
            "current_user": {"id": "U456", "is_admin": True},
            "channels": {
                "C123": {
                    "id": "C123",
                    "name": "general",
                    "conversations": {"members": ["U123"]},
                    "is_archived": False,
                    "type": "public_channel",
                },
                "C456": {
                    "id": "C456",
                    "name": "random",
                    "conversations": {"members": ["U456"]},
                    "is_archived": True,
                    "type": "public_channel",
                    "is_open": False,
                },
            },
            "users": {
                "U123": {"id": "U123", "name": "user1"},
                "U456": {"id": "U456", "name": "user2"},
            },
        }
        
        # Start each test with a patch
        self.patcher = patch("slack.Conversations.DB", self.test_db)
        self.mock_db = self.patcher.start()
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")

    def tearDown(self):
        """Clean up after each test."""
        self.patcher.stop()

    def test_mark_read_missing_channel(self):
        """Test that empty channel raises ChannelNameMissingError."""
        self.assert_error_behavior(
            mark_conversation_read,
            ChannelNameMissingError,
            "channel cannot be empty.",
            None,
            channel="",
            ts="1678886400.000000",
        )

    def test_mark_read_missing_timestamp(self):
        """Test that empty timestamp raises TimestampError."""
        self.assert_error_behavior(
            mark_conversation_read,
            TimestampError,
            "timestamp cannot be empty.",
            None,
            channel="C123",
            ts="",
        )

    def test_mark_read_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            mark_conversation_read,
            ChannelNotFoundError,
            "Channel 'C999' not found.",
            None,
            channel="C999",
            ts="1678886400.000000",
        )

    def test_mark_read_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            mark_conversation_read,
            TypeError,
            "channel must be a string.",
            None,
            channel=123,
            ts="1678886400.000000",
        )

    def test_mark_read_invalid_timestamp_type(self):
        """Test that non-string timestamp raises TypeError."""
        self.assert_error_behavior(
            mark_conversation_read,
            TypeError,
            "ts must be a string.",
            None,
            channel="C123",
            ts=123,
        )

    def test_mark_read_invalid_timestamp_value(self):
        """Test that invalid timestamp format raises TimestampError."""
        self.assert_error_behavior(
            mark_conversation_read,
            TimestampError,
            "timestamp is not a valid timestamp.",
            None,
            channel="C123",
            ts="invalid_timestamp",
        )

    def test_mark_read_success(self):
        """Test successful marking of conversation as read."""
        result = mark_conversation_read("C456", "1678886400.000000")
        self.assertTrue(result["ok"])
        self.assertEqual(
            self.test_db["channels"]["C456"]["conversations"]["read_cursor"],
            "1678886400.000000",
        )

    def test_mark_read_not_in_conversation(self):
        """Test that marking read when not in conversation raises UserNotInConversationError."""
        self.test_db["current_user"]["id"] = "U999"
        self.assert_error_behavior(
            mark_conversation_read,
            UserNotInConversationError,
            "Current user is not a member of this channel.",
            None,
            channel="C123",
            ts="1678886400.000000",
        )
        self.test_db["current_user"]["id"] = "U123"

    def test_mark_read_none_channel(self):
        """Test that None channel raises TypeError."""
        self.assert_error_behavior(
            mark_conversation_read,
            TypeError,
            "channel must be a string.",
            None,
            channel=None,
            ts="1678886400.000000",
        )

    def test_mark_read_none_timestamp(self):
        """Test that None timestamp raises TypeError."""
        self.assert_error_behavior(
            mark_conversation_read,
            TypeError,
            "ts must be a string.",
            None,
            channel="C123",
            ts=None,
        )
