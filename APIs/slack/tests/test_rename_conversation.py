"""
Test cases for the rename_conversation function in the Slack Conversations API.

This module contains comprehensive test cases for the rename_conversation function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    ChannelNameMissingError,
    ChannelNameTakenError,
)
from .. import rename_conversation

class TestRenameConversation(BaseTestCaseWithErrorHandler):
    """Test cases for the rename_conversation function."""

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

    def test_rename_missing_channel(self):
        """Test that empty channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            rename_conversation,
            ChannelNotFoundError,
            "Channel parameter is required",
            None,
            "",
            "new_name",
        )

    def test_rename_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            rename_conversation,
            ChannelNotFoundError,
            "Channel C999 not found",
            None,
            "C999",
            "new_name",
        )

    def test_rename_name_taken(self):
        """Test that already taken name raises ChannelNameTakenError."""
        self.assert_error_behavior(
            rename_conversation,
            ChannelNameTakenError,
            "Channel name 'random' is already taken",
            None,
            "C123",
            "random",  # "random" is already taken by C456
        )

    def test_rename_success(self):
        """Test successful renaming of a channel."""
        result = rename_conversation("C123", "new_name")
        self.assertTrue(result["ok"])
        self.assertEqual(self.test_db["channels"]["C123"]["name"], "new_name")

    def test_rename_empty_name(self):
        """Test that empty name parameter raises ChannelNameMissingError."""
        self.assert_error_behavior(
            rename_conversation,
            ChannelNameMissingError,
            "Name parameter is required and cannot be empty",
            None,
            "C123",
            "",
        )

    def test_rename_whitespace_only_name(self):
        """Test that whitespace-only name parameter raises ChannelNameMissingError."""
        self.assert_error_behavior(
            rename_conversation,
            ChannelNameMissingError,
            "Name parameter is required and cannot be empty",
            None,
            "C123",
            "   ",
        )

    def test_rename_channel_type_int(self):
        """Test that non-string channel parameter raises TypeError."""
        self.assert_error_behavior(
            rename_conversation,
            TypeError,
            "channel must be a string, got int",
            None,
            123,
            "new_name",
        )

    def test_rename_channel_type_none(self):
        """Test that None channel parameter raises TypeError."""
        self.assert_error_behavior(
            rename_conversation,
            TypeError,
            "channel must be a string, got NoneType",
            None,
            None,
            "new_name",
        )

    def test_rename_name_type_int(self):
        """Test that non-string name parameter raises TypeError."""
        self.assert_error_behavior(
            rename_conversation,
            TypeError,
            "name must be a string, got int",
            None,
            "C123",
            123,
        )

    def test_rename_name_type_none(self):
        """Test that None name parameter raises TypeError."""
        self.assert_error_behavior(
            rename_conversation,
            TypeError,
            "name must be a string, got NoneType",
            None,
            "C123",
            None,
        )

    def test_rename_name_type_list(self):
        """Test that list name parameter raises TypeError."""
        self.assert_error_behavior(
            rename_conversation,
            TypeError,
            "name must be a string, got list",
            None,
            "C123",
            ["new_name"],
        )
