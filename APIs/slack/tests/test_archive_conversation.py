"""
Test cases for the archive_conversation function in the Slack Conversations API.

This module contains comprehensive test cases for the archive_conversation function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import ChannelNotFoundError
from .. import archive_conversation

class TestArchiveConversation(BaseTestCaseWithErrorHandler):
    """Test cases for the archive_conversation function."""

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

    def test_archive_empty_channel(self):
        """Test that empty channel raises ValueError."""
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=ValueError,
            expected_message="Argument 'channel' cannot be an empty string.",
            channel="",
        )

    def test_archive_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=ChannelNotFoundError,
            expected_message="Channel 'missing_channel' not found.",
            channel="missing_channel",
        )

    def test_channel_not_string_type_error(self):
        """Test that a non-string channel ID raises TypeError."""
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=TypeError,
            expected_message="Argument 'channel' must be a string, got int.",
            channel=123,
        )

    def test_channel_none_type_error(self):
        """Test that a None channel ID raises TypeError."""
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=TypeError,
            expected_message="Argument 'channel' must be a string, got NoneType.",
            channel=None,
        )

    def test_archive_success(self):
        """Test successful archiving of a channel."""
        result = archive_conversation("C123")
        self.assertTrue(result["ok"])
        self.assertTrue(self.test_db["channels"]["C123"]["is_archived"])

    def test_archiving_already_archived_channel(self):
        """Test archiving a channel that is already archived (should still succeed and set flags)."""
        result = archive_conversation(channel="C456")
        self.assertTrue(result.get("ok"))
        self.assertTrue(self.test_db["channels"]["C456"]["is_archived"])
        self.assertFalse(self.test_db["channels"]["C456"]["is_open"])

    def test_archive_channel_list_type(self):
        """Test that list channel parameter raises TypeError."""
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=TypeError,
            expected_message="Argument 'channel' must be a string, got list.",
            channel=["C123"],
        )

    def test_archive_channels_none(self):
        """Test that DB['channels'] = None raises ChannelNotFoundError instead of TypeError."""
        # Set channels to None to simulate the bug scenario
        self.test_db["channels"] = None
        
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=ChannelNotFoundError,
            expected_message="Channel 'C123' not found.",
            channel="C123",
        )

    def test_archive_channels_not_dict(self):
        """Test that DB['channels'] is not a dict raises ChannelNotFoundError."""
        # Set channels to a non-dict value
        self.test_db["channels"] = "not_a_dict"
        
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=ChannelNotFoundError,
            expected_message="Channel 'C123' not found.",
            channel="C123",
        )

    def test_archive_channels_missing_key(self):
        """Test that missing 'channels' key raises ChannelNotFoundError."""
        # Remove channels key entirely
        del self.test_db["channels"]
        
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=ChannelNotFoundError,
            expected_message="Channel 'C123' not found.",
            channel="C123",
        )

    def test_archive_channels_empty_dict(self):
        """Test that empty channels dict raises ChannelNotFoundError."""
        # Set channels to empty dict
        self.test_db["channels"] = {}
        
        self.assert_error_behavior(
            func_to_call=archive_conversation,
            expected_exception_type=ChannelNotFoundError,
            expected_message="Channel 'C123' not found.",
            channel="C123",
        )
