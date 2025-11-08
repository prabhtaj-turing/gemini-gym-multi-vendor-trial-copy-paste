"""
Test cases for the join_conversation function in the Slack Conversations API.

This module contains comprehensive test cases for the join_conversation function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    ChannelNameMissingError,
    MissingUserIDError,
    UserNotFoundError,
)
from .. import join_conversation

class TestJoinConversation(BaseTestCaseWithErrorHandler):
    """Test cases for the join_conversation function."""

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

    def test_join_invalid_user_id_type(self):
        """Test that non-string user_id raises TypeError."""
        self.assert_error_behavior(
            join_conversation,
            TypeError,
            "user_id must be a string.",
            None,
            user_id=123,
            channel="C123",
        )

    def test_join_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            join_conversation,
            TypeError,
            "channel must be a string.",
            None,
            user_id="U123",
            channel=123,
        )

    def test_join_missing_user_id(self):
        """Test that empty user_id raises MissingUserIDError."""
        self.assert_error_behavior(
            join_conversation,
            MissingUserIDError,
            "user_id cannot be empty.",
            None,
            user_id="",
            channel="C123",
        )

    def test_join_missing_channel(self):
        """Test that empty channel raises ChannelNameMissingError."""
        self.assert_error_behavior(
            join_conversation,
            ChannelNameMissingError,
            "channel cannot be empty.",
            None,
            user_id="U123",
            channel="",
        )

    def test_join_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            join_conversation,
            ChannelNotFoundError,
            "Channel 'C999' not found.",
            None,
            user_id="U123",
            channel="C999",
        )

    def test_join_success(self):
        """Test successful joining of a conversation."""
        result = join_conversation("U456", "C123")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"], "C123")
        self.assertIn(
            "U456", self.test_db["channels"]["C123"]["conversations"]["members"]
        )

    def test_join_creates_members_if_missing(self):
        """Test that join creates members list if missing."""
        # Simulate missing "conversations" and "members" keys
        temp_channel_data = self.test_db["channels"]["C123"].copy()
        if "conversations" in temp_channel_data:
            del temp_channel_data["conversations"]

        with patch.dict(self.test_db["channels"], {"C123": temp_channel_data}):
            result = join_conversation("U456", "C123")
            self.assertTrue(result["ok"])
            self.assertEqual(result["channel"], "C123")
            # Check the state after the call
            self.assertIn(
                "U456", self.test_db["channels"]["C123"]["conversations"]["members"]
            )

    def test_join_already_in_channel(self):
        """Test joining a channel user is already in."""
        result = join_conversation("U123", "C123")
        self.assertFalse(result["ok"])

    def test_join_none_user_id(self):
        """Test that None user_id raises TypeError."""
        self.assert_error_behavior(
            join_conversation,
            TypeError,
            "user_id must be a string.",
            None,
            user_id=None,
            channel="C123",
        )

    def test_join_none_channel(self):
        """Test that None channel raises TypeError."""
        self.assert_error_behavior(
            join_conversation,
            TypeError,
            "channel must be a string.",
            None,
            user_id="U123",
            channel=None,
        )

    def test_join_user_not_found(self):
        """Test that non-existent user raises UserNotFoundError."""
        self.assert_error_behavior(
            join_conversation,
            UserNotFoundError,
            "User 'U999' not found.",
            None,
            user_id="U999",
            channel="C123",
        )
