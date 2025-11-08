"""
Test cases for the kick_from_conversation function in the Slack Conversations API.

This module contains comprehensive test cases for the kick_from_conversation function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    ChannelNameMissingError,
    MissingUserIDError,
    UserNotInConversationError,
)
from .. import kick_from_conversation

class TestKickFromConversation(BaseTestCaseWithErrorHandler):
    """Test cases for the kick_from_conversation function."""

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
                "C789": {
                    "id": "C789",
                    "name": "private-channel",
                    "is_private": True,
                    "type": "private_channel",
                    "conversations": {
                        "members": ["U123", "U456"],
                        "purpose": "Initial Purpose",
                        "topic": "Initial Topic",
                    },
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

    def test_kick_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            kick_from_conversation,
            TypeError,
            "channel must be a string.",
            None,
            123,
            "U123",
        )

    def test_kick_invalid_user_id_type(self):
        """Test that non-string user_id raises TypeError."""
        self.assert_error_behavior(
            kick_from_conversation,
            TypeError,
            "user_id must be a string.",
            None,
            "C123",
            123,
        )

    def test_kick_missing_channel(self):
        """Test that empty channel raises ChannelNameMissingError."""
        self.assert_error_behavior(
            kick_from_conversation,
            ChannelNameMissingError,
            "channel cannot be empty.",
            None,
            "",
            "U123",
        )

    def test_kick_missing_user_id(self):
        """Test that empty user_id raises MissingUserIDError."""
        self.assert_error_behavior(
            kick_from_conversation,
            MissingUserIDError,
            "user_id cannot be empty.",
            None,
            "C123",
            "",
        )

    def test_kick_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            kick_from_conversation,
            ChannelNotFoundError,
            "Channel 'C999' not found.",
            None,
            "C999",
            "U123",
        )

    def test_kick_user_not_in_channel(self):
        """Test that kicking user not in channel raises UserNotInConversationError."""
        self.assert_error_behavior(
            kick_from_conversation,
            UserNotInConversationError,
            "User 'U456' is not in conversation 'C123'.",
            None,
            "C123",
            "U456",
        )

    def test_kick_success(self):
        """Test successful kicking of a user from conversation."""
        result = kick_from_conversation("C789", "U123")
        self.assertTrue(result["ok"])
        self.assertNotIn(
            "U123", self.test_db["channels"]["C789"]["conversations"]["members"]
        )

    def test_kick_none_channel(self):
        """Test that None channel raises TypeError."""
        self.assert_error_behavior(
            kick_from_conversation,
            TypeError,
            "channel must be a string.",
            None,
            None,
            "U123",
        )

    def test_kick_none_user_id(self):
        """Test that None user_id raises TypeError."""
        self.assert_error_behavior(
            kick_from_conversation,
            TypeError,
            "user_id must be a string.",
            None,
            "C123",
            None,
        )
