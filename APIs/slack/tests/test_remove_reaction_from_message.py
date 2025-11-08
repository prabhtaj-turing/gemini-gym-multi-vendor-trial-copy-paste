"""
Test cases for the remove_reaction_from_message function in the Slack Reactions API.

This module contains comprehensive test cases for the remove_reaction_from_message function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ReactionNotFoundError,
    UserHasNotReactedError,
    ChannelNotFoundError,
    MessageNotFoundError,
    MissingRequiredArgumentsError,
)
from .. import remove_reaction_from_message

class TestRemoveReactionFromMessage(BaseTestCaseWithErrorHandler):
    """Test cases for the remove_reaction_from_message function."""

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

    def test_remove_reaction_success(self):
        """Test successful removal of reaction from message."""
        with patch("slack.Reactions.DB", DB):
            # Remove an existing reaction
            result = remove_reaction_from_message(
                "U01234567", "+1", "C456", "1678886400.000000"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(
                len(DB["channels"]["C456"]["messages"][0]["reactions"]), 0
            )  # check empty

    def test_remove_reaction_already_removed(self):
        """Test error when trying to remove a reaction that's already been removed."""
        with patch("slack.Reactions.DB", DB):
            # Remove reaction first time
            remove_reaction_from_message("U01234567", "+1", "C456", "1678886400.000000")
            
            # Try removing same reaction again - should raise ReactionNotFoundError
            self.assert_error_behavior(
                remove_reaction_from_message,
                ReactionNotFoundError,
                "Reaction '+1' not found on message with timestamp '1678886400.000000'.",
                None,
                "U01234567", "+1", "C456", "1678886400.000000"
            )

    def test_remove_reaction_user_not_reacted(self):
        """Test error when user tries to remove a reaction they haven't made."""
        with patch("slack.Reactions.DB", DB):
            # Test removing a reaction by a user who hasn't reacted
            self.assert_error_behavior(
                remove_reaction_from_message,
                UserHasNotReactedError,
                "User 'U999' has not reacted with '+1' on this message.",
                None,
                "U999", "+1", "C456", "1678886400.000000"
            )

    def test_remove_nonexistent_reaction(self):
        """Test error when trying to remove a reaction that doesn't exist."""
        with patch("slack.Reactions.DB", DB):
            # Test removing a non-existent reaction
            self.assert_error_behavior(
                remove_reaction_from_message,
                ReactionNotFoundError,
                "Reaction 'nonexistent' not found on message with timestamp '1678886400.000000'.",
                None,
                "U01234567", "nonexistent", "C456", "1678886400.000000"
            )

    def test_remove_reaction_channel_not_found(self):
        """Test error when channel doesn't exist."""
        with patch("slack.Reactions.DB", DB):
            # Test channel not found
            self.assert_error_behavior(
                remove_reaction_from_message,
                ChannelNotFoundError,
                "Channel with ID 'C789' not found.",
                None,
                "U01234567", "+1", "C789", "1678886400.000000"
            )

    def test_remove_reaction_message_not_found(self):
        """Test error when message doesn't exist."""
        with patch("slack.Reactions.DB", DB):
            # Test message not found
            self.assert_error_behavior(
                remove_reaction_from_message,
                MessageNotFoundError,
                "Message with timestamp '9999999999.999999' not found in channel 'C456'.",
                None,
                "U01234567", "+1", "C456", "9999999999.999999"
            )

    def test_remove_reaction_missing_required_arguments(self):
        """Test error when required arguments are missing or empty."""
        with patch("slack.Reactions.DB", DB):
            # Test missing reaction name
            self.assert_error_behavior(
                remove_reaction_from_message,
                MissingRequiredArgumentsError,
                "Required arguments cannot be empty: name",
                None,
                "U01234567", "", "C456", "1678886400.000000"
            )

    def test_remove_reaction_invalid_types(self):
        """Test that invalid parameter types raise TypeError."""
        with patch("slack.Reactions.DB", DB):
            self.assert_error_behavior(
                remove_reaction_from_message,
                TypeError,
                "user_id must be a string.",
                None,
                123, "+1", "C456", "1678886400.000000"
            )
            
            self.assert_error_behavior(
                remove_reaction_from_message,
                TypeError,
                "name must be a string.",
                None,
                "U01234567", 123, "C456", "1678886400.000000"
            )
            
            self.assert_error_behavior(
                remove_reaction_from_message,
                TypeError,
                "channel_id must be a string.",
                None,
                "U01234567", "+1", 123, "1678886400.000000"
            )
            
            self.assert_error_behavior(
                remove_reaction_from_message,
                TypeError,
                "message_ts must be a string.",
                None,
                "U01234567", "+1", "C456", 123
            )


if __name__ == "__main__":
    import unittest
    unittest.main()
