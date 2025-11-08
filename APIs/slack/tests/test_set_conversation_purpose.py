"""
Test cases for the set_conversation_purpose function in the Slack Conversations API.

This module contains comprehensive test cases for the set_conversation_purpose function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    ChannelNameMissingError,
    MissingPurposeError,
    UserNotInConversationError,
)
from .. import set_conversation_purpose

class TestSetConversationPurpose(BaseTestCaseWithErrorHandler):
    """Test cases for the set_conversation_purpose function."""

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

    def test_setPurpose_missing_channel(self):
        """Test that empty channel raises ChannelNameMissingError."""
        self.assert_error_behavior(
            set_conversation_purpose,
            ChannelNameMissingError,
            "channel cannot be empty.",
            None,
            "",
            "new_purpose",
        )

    def test_setPurpose_missing_purpose(self):
        """Test that empty purpose raises MissingPurposeError."""
        self.assert_error_behavior(
            set_conversation_purpose,
            MissingPurposeError,
            "purpose cannot be empty.",
            None,
            "C123",
            "",
        )

    def test_setPurpose_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            set_conversation_purpose,
            ChannelNotFoundError,
            "Channel 'C999' not found.",
            None,
            "C999",
            "new_purpose",
        )

    def test_setPurpose_invalid_purpose_type(self):
        """Test that non-string purpose raises TypeError."""
        self.assert_error_behavior(
            set_conversation_purpose,
            TypeError,
            "purpose must be a string.",
            None,
            "C123",
            123,
        )

    def test_setPurpose_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            set_conversation_purpose,
            TypeError,
            "channel must be a string.",
            None,
            123,
            "new_purpose",
        )

    def test_setPurpose_not_admin(self):
        """Test that non-admin user cannot set purpose."""
        self.test_db["current_user"]["is_admin"] = False
        self.assert_error_behavior(
            set_conversation_purpose,
            PermissionError,
            "You are not authorized to set the purpose of this channel.",
            None,
            "C123",
            "new_purpose",
        )
        self.test_db["current_user"]["is_admin"] = True

    def test_setPurpose_not_in_conversation(self):
        """Test that user not in conversation cannot set purpose."""
        self.test_db["current_user"]["id"] = "U999"
        self.assert_error_behavior(
            set_conversation_purpose,
            UserNotInConversationError,
            "You are not a member of this channel.",
            None,
            "C123",
            "new_purpose",
        )
        self.test_db["current_user"]["id"] = "U456"

    def test_setPurpose_success(self):
        """Test successful setting of conversation purpose."""
        result = set_conversation_purpose("C789", "new_purpose")
        self.assertTrue(result["ok"])
        self.assertEqual(
            self.test_db["channels"]["C789"]["conversations"]["purpose"], "new_purpose"
        )

    def test_setPurpose_none_channel(self):
        """Test that None channel raises TypeError."""
        self.assert_error_behavior(
            set_conversation_purpose,
            TypeError,
            "channel must be a string.",
            None,
            None,
            "new_purpose",
        )

    def test_setPurpose_none_purpose(self):
        """Test that None purpose raises TypeError."""
        self.assert_error_behavior(
            set_conversation_purpose,
            TypeError,
            "purpose must be a string.",
            None,
            "C123",
            None,
        )
