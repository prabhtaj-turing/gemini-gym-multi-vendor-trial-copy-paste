"""
Test cases for the get_message_reactions function in the Slack Reactions API.

This module contains comprehensive test cases for the get_message_reactions function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    MessageNotFoundError,
)
from .. import get_message_reactions

class TestGetMessageReactions(BaseTestCaseWithErrorHandler):
    """Test cases for the get_message_reactions function."""

    def setUp(self):
        """Setup method to create a fresh DB for each test."""
        global DB
        from ..SimulationEngine.db import DB
        DB.clear()
        DB.update(
            {
                "channels": {
                    "C123": {
                        "messages": [
                            {
                                "ts": "1678886300.000000",
                                "user": "U01234567",
                                "text": "Hello!",
                                "reactions": [],
                            }
                        ]
                    },
                    "C456": {
                        "messages": [
                            {
                                "ts": "1678886400.000000",
                                "user": "U01234568",
                                "text": "Another message.",
                                "reactions": [
                                    {
                                        "name": "+1",
                                        "users": ["U01234567"],
                                        "count": 1,
                                    }
                                ],
                            }
                        ]
                    },
                },
                "users": {
                    "U01234567": {"id": "U01234567", "name": "user1"},
                    "U01234568": {"id": "U01234568", "name": "user2"},
                },
                "files": {},
                "scheduled_messages": [],
                "ephemeral_messages": [],
            }
        )

    def test_get_reactions_summary(self):
        """Test getting reactions summary (default behavior)."""
        with patch("slack.Reactions.DB", DB):
            # Get reactions (summary)
            result = get_message_reactions(
                channel_id="C456", message_ts="1678886400.000000"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["reactions"], {"+1": 1})  # Check summary

    def test_get_reactions_full(self):
        """Test getting full reaction details."""
        with patch("slack.Reactions.DB", DB):
            # Get reactions (full)
            result = get_message_reactions("C456", "1678886400.000000", full=True)
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["reactions"]), 1)
            self.assertEqual(result["reactions"][0]["name"], "+1")
            self.assertEqual(result["reactions"][0]["count"], 1)
            self.assertEqual(result["reactions"][0]["users"], ["U01234567"])

    def test_get_reactions_invalid_types(self):
        """Test that invalid parameter types raise TypeError."""
        with patch("slack.Reactions.DB", DB):
            # Test invalid channel_id type
            self.assert_error_behavior(
                get_message_reactions,
                TypeError,
                "channel_id must be a string.",
                channel_id=123,
                message_ts="1678886400.000000",
            )

            # Test invalid message_ts type
            self.assert_error_behavior(
                get_message_reactions,
                TypeError,
                "message_ts must be a string.",
                channel_id="C456",
                message_ts=123,
            )

            # Test invalid full type
            self.assert_error_behavior(
                get_message_reactions,
                TypeError,
                "full must be a boolean.",
                channel_id="C456",
                message_ts="1678886400.000000",
                full="true",
            )

    def test_get_reactions_invalid_values(self):
        """Test that invalid parameter values raise appropriate errors."""
        with patch("slack.Reactions.DB", DB):
            # Test missing channel
            self.assert_error_behavior(
                get_message_reactions,
                ValueError,
                "channel_id cannot be empty.",
                channel_id="",
                message_ts="1678886400.000000",
            )

            # Test missing ts
            self.assert_error_behavior(
                get_message_reactions,
                ValueError,
                "message_ts cannot be empty.",
                channel_id="C456",
                message_ts="",
            )

            # Test channel not found
            self.assert_error_behavior(
                get_message_reactions,
                ChannelNotFoundError,
                f"Channel with ID 'C789' not found.",
                channel_id="C789",
                message_ts="1678886400.000000",
            )

            # Test message not found
            self.assert_error_behavior(
                get_message_reactions,
                MessageNotFoundError,
                "Message with timestamp '9999999999.999999' not found in channel 'C456'.",
                channel_id="C456",
                message_ts="9999999999.999999",
            )

    def test_message_ts_none_string_does_not_match_missing_ts(self):
        """Test that message_ts='None' doesn't match messages without ts field.
        
        This test ensures that the bug where str(msg.get('ts')) == 'None'
        would incorrectly match messages missing the 'ts' field is fixed.
        """
        with patch("slack.Reactions.DB", DB):
            # Add a message without a 'ts' field
            DB["channels"]["C123"]["messages"].append({
                "user": "U01234567",
                "text": "Message without timestamp",
                "reactions": [
                    {
                        "name": "bug",
                        "users": ["U01234567"],
                        "count": 1,
                    }
                ]
            })
            
            # Should raise MessageNotFoundError, not match the message without ts
            self.assert_error_behavior(
                get_message_reactions,
                MessageNotFoundError,
                "Message with timestamp 'None' not found in channel 'C123'.",
                channel_id="C123",
                message_ts="None",
            )

    def test_message_without_ts_field_is_skipped(self):
        """Test that messages without ts field are properly skipped during lookup.
        
        This ensures that only messages with valid ts fields are matched,
        and messages missing the ts key don't cause issues.
        """
        with patch("slack.Reactions.DB", DB):
            # Add a message without 'ts' field before a valid message
            DB["channels"]["C123"]["messages"].insert(0, {
                "user": "U01234567",
                "text": "Message without timestamp",
                "reactions": []
            })
            
            # Should still find the valid message with ts field
            result = get_message_reactions(
                channel_id="C123",
                message_ts="1678886300.000000"
            )
            
            self.assertTrue(result["ok"])
            self.assertEqual(result["reactions"], {})  # Empty reactions


if __name__ == "__main__":
    import unittest
    unittest.main()
