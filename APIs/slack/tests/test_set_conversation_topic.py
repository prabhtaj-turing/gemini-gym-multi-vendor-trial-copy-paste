"""
Test cases for the set_conversation_topic function in the Slack Conversations API.

This module contains comprehensive test cases for the set_conversation_topic function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    ChannelNameMissingError,
    UserNotInConversationError,
)
from .. import set_conversation_topic

class TestSetConversationTopic(BaseTestCaseWithErrorHandler):
    """Test cases for the set_conversation_topic function."""

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

    def test_setConversationTopic_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            set_conversation_topic,
            TypeError,
            "channel must be a string.",
            None,
            123,
            "new_topic",
        )

    def test_setConversationTopic_invalid_topic_type(self):
        """Test that non-string topic raises TypeError."""
        self.assert_error_behavior(
            set_conversation_topic,
            TypeError,
            "topic must be a string.",
            None,
            "C123",
            123,
        )

    def test_setConversationTopic_missing_channel(self):
        """Test that empty channel raises ChannelNameMissingError."""
        self.assert_error_behavior(
            set_conversation_topic,
            ChannelNameMissingError,
            "channel cannot be empty.",
            None,
            "",
            "new_topic",
        )

    def test_setConversationTopic_missing_topic(self):
        """Test that empty topic raises ValueError."""
        self.assert_error_behavior(
            set_conversation_topic,
            ValueError,
            "topic cannot be empty.",
            None,
            "C123",
            "",
        )

    def test_setConversationTopic_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            set_conversation_topic,
            ChannelNotFoundError,
            "Channel 'C999' not found.",
            None,
            "C999",
            "new_topic",
        )

    def test_setConversationTopic_success(self):
        """Test successful setting of conversation topic."""
        result = set_conversation_topic("C789", "new_topic")
        self.assertTrue(result["ok"])
        self.assertEqual(
            self.test_db["channels"]["C789"]["conversations"]["topic"], "new_topic"
        )

    def test_setConversationTopic_not_in_conversation(self):
        """Test that user not in conversation cannot set topic."""
        self.test_db["current_user"]["id"] = "U999"
        self.assert_error_behavior(
            set_conversation_topic,
            UserNotInConversationError,
            "Current user is not a member of this channel.",
            None,
            "C123",
            "new_topic",
        )
        self.test_db["current_user"]["id"] = "U456"

    def test_setConversationTopic_not_admin(self):
        """Test that non-admin user cannot set topic."""
        self.test_db["current_user"]["is_admin"] = False
        self.assert_error_behavior(
            set_conversation_topic,
            PermissionError,
            "You are not authorized to set the topic of this channel.",
            None,
            "C456",
            "new_topic",
        )
        self.test_db["current_user"]["is_admin"] = True

    def test_setConversationTopic_none_channel(self):
        """Test that None channel raises TypeError."""
        self.assert_error_behavior(
            set_conversation_topic,
            TypeError,
            "channel must be a string.",
            None,
            None,
            "new_topic",
        )

    def test_setConversationTopic_none_topic(self):
        """Test that None topic raises TypeError."""
        self.assert_error_behavior(
            set_conversation_topic,
            TypeError,
            "topic must be a string.",
            None,
            "C123",
            None,
        )
