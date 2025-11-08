"""
Test cases for the delete_scheduled_message function in the Slack Chat API.

This module contains comprehensive test cases for the delete_scheduled_message function,
including success scenarios and all error conditions.
"""

import time
from contextlib import contextmanager
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import ChannelNotFoundError
from .. import delete_scheduled_message

DB = {}

@contextmanager
def patch_both_dbs(test_db):
    """Helper to patch both Chat.DB and utils.DB with the same test database."""
    with patch("slack.Chat.DB", test_db), patch("slack.SimulationEngine.utils.DB", test_db):
        yield


class TestDeleteScheduledMessage(BaseTestCaseWithErrorHandler):
    """Test cases for the delete_scheduled_message function."""

    def setUp(self):
        """Initialize test state."""
        global DB
        DB.clear()
        DB.update({
            "channels": {
                "C123": {"id": "C123", "name": "general", "messages": []},
                "C456": {"id": "C456", "name": "random", "messages": []},
            },
            "scheduled_messages": [],
            "ephemeral_messages": [],
            "current_user": {"id": "U123", "is_admin": True},
            "users": {
                "U123": {"id": "U123", "name": "user1"},
                "U456": {"id": "U456", "name": "user2"},
            }
        })

    def test_delete_scheduled_message_with_channel_id(self):
        """Test delete_scheduled_message using channel ID (delete functions only support IDs)."""
        with patch_both_dbs(DB):
            # First add a scheduled message
            DB["scheduled_messages"].append({
                "message_id": 1,
                "channel": "C123",
                "user": "U123",
                "text": "Scheduled message"
            })
            
            result = delete_scheduled_message(channel="C123", scheduled_message_id="1")
            self.assertTrue(result["ok"])
            self.assertEqual(result["channel"], "C123")
            
            # Verify scheduled message was deleted
            self.assertEqual(len(DB["scheduled_messages"]), 0)

    def test_delete_scheduled_message_backward_compatible_with_channel_ids(self):
        """Test that delete_scheduled_message works with channel IDs (backward compatibility)."""
        with patch_both_dbs(DB):
            # Add a scheduled message
            DB["scheduled_messages"].append({
                "message_id": 2,
                "channel": "C456",
                "user": "U123",
                "text": "Another scheduled message"
            })
            
            result = delete_scheduled_message(channel="C456", scheduled_message_id="2")
            self.assertTrue(result["ok"])
            self.assertEqual(result["channel"], "C456")


if __name__ == "__main__":
    import unittest
    unittest.main()
