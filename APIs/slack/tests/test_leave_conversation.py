"""
Test cases for the leave_conversation function in the Slack Conversations API.

This module contains comprehensive test cases for the leave_conversation function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import (
    ChannelNotFoundError,
    UserNotInConversationError,
)
from .. import leave_conversation

class TestLeaveConversation(BaseTestCaseWithErrorHandler):
    """Test cases for the leave_conversation function."""

    def setUp(self):
        """Reset DB state before each test."""
        self.test_db = {
            "channels": {
                "general": {
                    "id": "general",  # Add id to match channel name
                    "conversations": {
                        "members": ["user1", "user2", "user_to_leave"]
                    },
                },
                "random": {
                    "id": "random",  # Add id to match channel name
                    "conversations": {"members": ["user1"]},
                },
                "empty_members_channel": {  # Channel exists, 'conversations' exists, but 'members' is empty
                    "id": "empty_members_channel",  # Add id to match channel name
                    "conversations": {"members": []},
                },
                "no_conversations_channel": {  # Channel exists, but no 'conversations' key
                    "id": "no_conversations_channel",  # Add id to match channel name
                    # "conversations": {} # This will be set by setdefault
                },
                "channel_with_no_members_key": {
                    "id": "channel_with_no_members_key",  # Add id to match channel name
                    "conversations": {},  # no 'members' key, setdefault will add it
                },
                # Keep some of the original test data for backward compatibility
                "C123": {
                    "id": "C123",
                    "name": "test-channel",
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
                "user1": {"id": "user1", "name": "user1"},
                "user2": {"id": "user2", "name": "user2"},
                "user_to_leave": {"id": "user_to_leave", "name": "user_to_leave"},
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

    # Original tests (keeping for backward compatibility)
    def test_leave_missing_user_id(self):
        """Test that empty user_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            leave_conversation("", "C123")
        self.assertIn("user_id cannot be empty", str(context.exception))

    def test_leave_missing_channel(self):
        """Test that empty channel raises ValueError."""
        with self.assertRaises(ValueError) as context:
            leave_conversation("U123", "")
        self.assertIn("channel cannot be empty", str(context.exception))

    def test_leave_channel_not_found(self):
        """Test that non-existent channel raises ChannelNotFoundError."""
        with self.assertRaises(ChannelNotFoundError) as context:
            leave_conversation("U123", "C999")
        self.assertIn("Channel 'C999' not found", str(context.exception))

    def test_leave_not_in_conversation(self):
        """Test that user not in conversation raises UserNotInConversationError."""
        with self.assertRaises(UserNotInConversationError) as context:
            leave_conversation("U456", "C123")
        self.assertIn(
            "User 'U456' is not in conversation 'C123'", str(context.exception)
        )

    def test_leave_success(self):
        """Test successful leaving of a conversation."""
        result = leave_conversation("U123", "C123")
        self.assertTrue(result["ok"])
        self.assertNotIn(
            "U123", self.test_db["channels"]["C123"]["conversations"]["members"]
        )

    def test_leave_invalid_user_id_type(self):
        """Test that non-string user_id raises TypeError."""
        self.assert_error_behavior(
            leave_conversation,
            TypeError,
            "user_id must be a string, got int.",
            None,
            123,
            "C123",
        )

    def test_leave_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            leave_conversation,
            TypeError,
            "channel must be a string, got int.",
            None,
            "U123",
            123,
        )

    def test_leave_none_user_id(self):
        """Test that None user_id raises TypeError."""
        self.assert_error_behavior(
            leave_conversation,
            TypeError,
            "user_id must be a string, got NoneType.",
            None,
            None,
            "C123",
        )

    def test_leave_none_channel(self):
        """Test that None channel raises TypeError."""
        self.assert_error_behavior(
            leave_conversation,
            TypeError,
            "channel must be a string, got NoneType.",
            None,
            "U123",
            None,
        )

    # New comprehensive tests based on your requirements
    def test_valid_leave_operation(self):
        """Test successfully leaving a channel."""
        result = leave_conversation(user_id="user_to_leave", channel="general")
        self.assertEqual(result, {"ok": True})
        self.assertNotIn(
            "user_to_leave", self.test_db["channels"]["general"]["conversations"]["members"]
        )
        self.assertIn(
            "user1", self.test_db["channels"]["general"]["conversations"]["members"]
        )  # Ensure others remain

    def test_invalid_user_id_type_int(self):
        """Test that user_id of type int raises TypeError."""
        with self.assertRaises(TypeError) as context:
            leave_conversation(user_id=123, channel="general")
        self.assertIn("user_id must be a string", str(context.exception))

    def test_invalid_user_id_type_none(self):
        """Test that user_id of type None raises TypeError."""
        with self.assertRaises(TypeError) as context:
            leave_conversation(user_id=None, channel="general")
        self.assertIn("user_id must be a string", str(context.exception))

    def test_empty_user_id_string(self):
        """Test that an empty string for user_id raises ValueError."""
        with self.assertRaises(ValueError) as context:
            leave_conversation(user_id="", channel="general")
        self.assertIn("user_id cannot be empty", str(context.exception))

    def test_invalid_channel_type_int(self):
        """Test that channel of type int raises TypeError."""
        with self.assertRaises(TypeError) as context:
            leave_conversation(user_id="user1", channel=123)
        self.assertIn("channel must be a string", str(context.exception))

    def test_invalid_channel_type_none(self):
        """Test that channel of type None raises TypeError."""
        with self.assertRaises(TypeError) as context:
            leave_conversation(user_id="user1", channel=None)
        self.assertIn("channel must be a string", str(context.exception))

    def test_empty_channel_string(self):
        """Test that an empty string for channel raises ValueError."""
        with self.assertRaises(ValueError) as context:
            leave_conversation(user_id="user1", channel="")
        self.assertIn("channel cannot be empty", str(context.exception))

    def test_channel_not_found_new(self):
        """Test leaving a non-existent channel raises ChannelNotFoundError."""
        with self.assertRaises(ChannelNotFoundError) as context:
            leave_conversation(user_id="user1", channel="non_existent_channel")
        self.assertIn(
            "Channel 'non_existent_channel' not found", str(context.exception)
        )

    def test_user_not_in_conversation_new(self):
        """Test leaving a channel where the user is not a member raises UserNotInConversationError."""
        with self.assertRaises(UserNotInConversationError) as context:
            leave_conversation(user_id="user_not_member", channel="general")
        self.assertIn(
            "User 'user_not_member' is not in conversation 'general'",
            str(context.exception),
        )

    def test_user_not_in_empty_members_channel(self):
        """Test leaving a channel with an empty members list."""
        with self.assertRaises(UserNotInConversationError) as context:
            leave_conversation(user_id="user1", channel="empty_members_channel")
        self.assertIn(
            "User 'user1' is not in conversation 'empty_members_channel'",
            str(context.exception),
        )

    def test_db_channels_is_not_dict(self):
        """Test behavior when DB['channels'] is not a dictionary."""
        # Temporarily modify the test_db for this specific test
        original_channels = self.test_db["channels"]
        self.test_db["channels"] = "not_a_dict"  # type: ignore
        
        with self.assertRaises(ChannelNotFoundError) as context:
            leave_conversation(user_id="user1", channel="general")
        self.assertIn("Channel 'general' not found", str(context.exception))
        
        # Restore original channels for other tests
        self.test_db["channels"] = original_channels

    def test_leave_channel_with_no_conversations_key(self):
        """Test leaving a channel that has no 'conversations' key."""
        # The fixed implementation handles missing 'conversations' key gracefully
        # by creating it with empty members list, then raising UserNotInConversationError
        with self.assertRaises(UserNotInConversationError) as context:
            leave_conversation(user_id="user1", channel="no_conversations_channel")
        self.assertIn(
            "User 'user1' is not in conversation 'no_conversations_channel'",
            str(context.exception),
        )
        # Verify that conversations and members keys were created
        self.assertIn('conversations', self.test_db["channels"]["no_conversations_channel"])
        self.assertIn('members', self.test_db["channels"]["no_conversations_channel"]['conversations'])

    def test_leave_channel_with_no_members_key(self):
        """Test leaving a channel that has conversations but no 'members' key."""
        with self.assertRaises(UserNotInConversationError) as context:
            leave_conversation(user_id="user1", channel="channel_with_no_members_key")
        self.assertIn(
            "User 'user1' is not in conversation 'channel_with_no_members_key'",
            str(context.exception),
        )
        # Verify that members key was created
        self.assertIn('members', self.test_db["channels"]["channel_with_no_members_key"]['conversations'])

    def test_leave_conversation_member_verification(self):
        """Test that other members remain after one user leaves."""
        # Ensure multiple users are in the channel initially
        initial_members = self.test_db["channels"]["general"]["conversations"]["members"].copy()
        self.assertIn("user1", initial_members)
        self.assertIn("user2", initial_members)
        self.assertIn("user_to_leave", initial_members)
        
        # User leaves
        result = leave_conversation(user_id="user_to_leave", channel="general")
        self.assertTrue(result["ok"])
        
        # Verify the user who left is no longer in the channel
        remaining_members = self.test_db["channels"]["general"]["conversations"]["members"]
        self.assertNotIn("user_to_leave", remaining_members)
        
        # Verify other users are still in the channel
        self.assertIn("user1", remaining_members)
        self.assertIn("user2", remaining_members)

    def test_leave_conversation_handles_empty_conversations_gracefully(self):
        """Test that the function handles channels with empty conversations gracefully."""
        # Test with a channel that has empty conversations object
        empty_conversations_channel = "empty_conversations_channel"
        self.test_db["channels"][empty_conversations_channel] = {
            "id": empty_conversations_channel,
            "conversations": {}  # Empty conversations object
        }
        
        # Should raise UserNotInConversationError, not KeyError
        with self.assertRaises(UserNotInConversationError) as context:
            leave_conversation(user_id="user1", channel=empty_conversations_channel)
        self.assertIn(
            f"User 'user1' is not in conversation '{empty_conversations_channel}'",
            str(context.exception),
        )
        
        # Verify that the conversations structure was properly initialized
        self.assertIn('conversations', self.test_db["channels"][empty_conversations_channel])
        self.assertIn('members', self.test_db["channels"][empty_conversations_channel]['conversations'])
        self.assertEqual(self.test_db["channels"][empty_conversations_channel]['conversations']['members'], [])
