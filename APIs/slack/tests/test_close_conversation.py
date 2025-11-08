"""
Test cases for the close_conversation function in the Slack Conversations API.

This module contains comprehensive test cases for the close_conversation function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    NotAllowedError,
)
from .. import close_conversation

class TestCloseConversation(BaseTestCaseWithErrorHandler):
    """Test cases for the close_conversation function."""

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
                "C4": {
                    "id": "C4",
                    "name": "marketing-im",
                    "type": "im",
                    "is_archived": False,
                    "is_open": True,
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

    def test_close_missing_channel(self):
        """Test that empty channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            close_conversation,
            ChannelNotFoundError,
            "Channel parameter is required",
            None,
            "",
        )

    def test_close_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            close_conversation,
            ChannelNotFoundError,
            "Channel C999 not found",
            None,
            "C999",
        )

    def test_close_not_allowed(self):
        """Test that closing non-IM channel raises NotAllowedError."""
        self.assert_error_behavior(
            close_conversation,
            NotAllowedError,
            "Cannot close channel C123: operation only allowed for direct messages",
            None,
            "C123",
        )

    def test_close_success_im_channel(self):
        """Test successfully closing a direct message channel."""
        result = close_conversation("C4")
        self.assertTrue(result["ok"])
        self.assertFalse(self.test_db["channels"]["C4"]["is_open"])

    def test_close_channel_type_int(self):
        """Test that non-string channel parameter raises TypeError."""
        self.assert_error_behavior(
            close_conversation,
            TypeError,
            "channel must be a string, got int",
            None,
            123,
        )

    def test_close_channel_type_none(self):
        """Test that None channel parameter raises TypeError."""
        self.assert_error_behavior(
            close_conversation,
            TypeError,
            "channel must be a string, got NoneType",
            None,
            None,
        )

    def test_close_channel_type_list(self):
        """Test that list channel parameter raises TypeError."""
        self.assert_error_behavior(
            close_conversation,
            TypeError,
            "channel must be a string, got list",
            None,
            ["C123"],
        )
