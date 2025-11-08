"""
Test cases for the add_reaction_to_message function in the Slack Reactions API.

This module contains comprehensive test cases for the add_reaction_to_message function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    AlreadyReactionError,
    ChannelNotFoundError,
    MessageNotFoundError,
)
from .. import add_reaction_to_message

class TestAddReactionToMessage(BaseTestCaseWithErrorHandler):
    """Test cases for the add_reaction_to_message function."""

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

    def test_add_reaction_success(self):
        """Test successful addition of reaction to message."""
        with patch("slack.Reactions.DB", DB):
            # Add a new reaction
            result = add_reaction_to_message("U123", "C123", "+1", "1678886300.000000")
            self.assertTrue(result["ok"])
            self.assertEqual(len(DB["channels"]["C123"]["messages"][0]["reactions"]), 1)
            self.assertEqual(
                DB["channels"]["C123"]["messages"][0]["reactions"][0]["name"], "+1"
            )
            self.assertEqual(
                DB["channels"]["C123"]["messages"][0]["reactions"][0]["count"], 1
            )
            self.assertIn(
                "U123", DB["channels"]["C123"]["messages"][0]["reactions"][0]["users"]
            )

    def test_add_reaction_already_exists(self):
        """Test error when user has already reacted with the same emoji."""
        with patch("slack.Reactions.DB", DB):
            # Add initial reaction
            add_reaction_to_message("U123", "C123", "+1", "1678886300.000000")
            
            # Try to add the same reaction again
            self.assert_error_behavior(
                func_to_call=add_reaction_to_message,
                expected_exception_type=AlreadyReactionError,
                expected_message="user has already reacted with this emoji.",
                user_id="U123",
                channel_id="C123",
                name="+1",
                message_ts="1678886300.000000",
            )

    def test_add_reaction_same_emoji_different_user(self):
        """Test adding the same reaction by a different user."""
        with patch("slack.Reactions.DB", DB):
            # Add initial reaction
            add_reaction_to_message("U123", "C123", "+1", "1678886300.000000")
            
            # Add the same reaction by a different user
            result = add_reaction_to_message("U456", "C123", "+1", "1678886300.000000")
            self.assertTrue(result["ok"])
            self.assertEqual(
                len(DB["channels"]["C123"]["messages"][0]["reactions"]), 1
            )  # Still one reaction type
            self.assertEqual(
                DB["channels"]["C123"]["messages"][0]["reactions"][0]["count"], 2
            )  # Count incremented
            self.assertIn(
                "U456", DB["channels"]["C123"]["messages"][0]["reactions"][0]["users"]
            )

    def test_add_different_reaction(self):
        """Test adding a different reaction to the same message."""
        with patch("slack.Reactions.DB", DB):
            # Add initial reaction
            add_reaction_to_message("U123", "C123", "+1", "1678886300.000000")
            
            # Add a different reaction
            result = add_reaction_to_message("U789", "C123", "tada", "1678886300.000000")
            self.assertTrue(result["ok"])
            self.assertEqual(
                len(DB["channels"]["C123"]["messages"][0]["reactions"]), 2
            )  # Two reaction types

    def test_add_reaction_invalid_types(self):
        """Test that invalid parameter types raise TypeError."""
        with patch("slack.Reactions.DB", DB):
            self.assert_error_behavior(
                add_reaction_to_message,
                TypeError,
                "user_id must be a string, got int",
                user_id=123,
                channel_id="C123",
                name="+1",
                message_ts="1678886300.000000",
            )
            self.assert_error_behavior(
                add_reaction_to_message,
                TypeError,
                "channel_id must be a string, got int",
                user_id="U123",
                channel_id=123,
                name="+1",
                message_ts="1678886300.000000",
            )
            self.assert_error_behavior(
                add_reaction_to_message,
                TypeError,
                "name must be a string, got int",
                user_id="U123",
                channel_id="C123",
                name=123,
                message_ts="1678886300.000000",
            )
            self.assert_error_behavior(
                add_reaction_to_message,
                TypeError,
                "message_ts must be a string, got int",
                user_id="U123",
                channel_id="C123",
                name="+1",
                message_ts=123,
            )

    def test_add_reaction_invalid_values(self):
        """Test that invalid parameter values raise appropriate errors."""
        with patch("slack.Reactions.DB", DB):
            self.assert_error_behavior(
                add_reaction_to_message,
                ValueError,
                "user_id cannot be empty or just whitespace",
                user_id="",
                channel_id="C123",
                name="+1",
                message_ts="1678886300.000000",
            )

            self.assert_error_behavior(
                add_reaction_to_message,
                ChannelNotFoundError,
                "channel not found.",
                user_id="U123",
                channel_id="C789",
                name="+1",
                message_ts="1678886300.000000",
            )

            self.assert_error_behavior(
                add_reaction_to_message,
                MessageNotFoundError,
                "message not found.",
                user_id="U123",
                channel_id="C123",
                name="+1",
                message_ts="9999999999.999999",
            )
    
    # Test validation value error when string is just whitespace
    def test_add_reaction_invalid_values_just_whitespace(self):
        """Test that invalid parameter values raise appropriate errors."""
        with patch("slack.Reactions.DB", DB):
            self.assert_error_behavior(
                add_reaction_to_message,
                ValueError,
                "user_id cannot be empty or just whitespace",
                user_id="   ",
                channel_id="C123",
                name="+1",
                message_ts="1678886300.000000",
            )
            self.assert_error_behavior(
                add_reaction_to_message,
                ValueError,
                "channel_id cannot be empty or just whitespace",
                user_id="U123",
                channel_id="   ",
                name="+1",
                message_ts="1678886300.000000",
            )
            self.assert_error_behavior(
                add_reaction_to_message,
                ValueError,
                "name cannot be empty or just whitespace",
                user_id="U123",
                channel_id="C123",
                name="   ",
                message_ts="1678886300.000000",
            )
            self.assert_error_behavior(
                add_reaction_to_message,
                ValueError,
                "message_ts cannot be empty or just whitespace",
                user_id="U123",
                channel_id="C123",
                name="+1",
                message_ts="   ",
            )


if __name__ == "__main__":
    import unittest
    unittest.main()
