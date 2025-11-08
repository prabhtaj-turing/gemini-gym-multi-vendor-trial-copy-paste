"""
Test cases for the open_conversation function in the Slack Conversations API.

This module contains comprehensive test cases for the open_conversation function,
including success scenarios and all error conditions.
"""

import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import CurrentUserNotSetError
from .. import open_conversation

class TestOpenConversation(BaseTestCaseWithErrorHandler):
    """Test cases for the open_conversation function."""

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
                    "messages": [],
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
                        "is_im": False,
                        "is_mpim": True,
                    },
                    "messages": [],
                },
            },
            "users": {
                "U123": {"id": "U123", "name": "user1"},
                "U456": {"id": "U456", "name": "user2"},
                "U789": {"id": "U789", "name": "user3"},
                "U999": {"id": "U999", "name": "user4"},
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

    def test_open_missing_channel_or_users(self):
        """Test that missing both channel and users raises ValueError."""
        self.assert_error_behavior(
            open_conversation,
            ValueError,
            "either channel or users must be provided",
            None,
        )

    def test_open_both_channel_and_users(self):
        """Test that providing both channel and users raises ValueError."""
        self.assert_error_behavior(
            open_conversation,
            ValueError,
            "provide either channel or users, not both",
            None,
            channel="C123",
            users="U456",
        )

    def test_open_resume_existing_conversation(self):
        """Test resuming an existing conversation by channel."""
        result = open_conversation(channel="C123")
        self.assertTrue(result["ok"])
        self.assertEqual(result["channel"]["id"], "C123")

    def test_open_resume_nonexistent_conversation(self):
        """Test resuming non-existent conversation raises ValueError."""
        self.assert_error_behavior(
            open_conversation,
            ValueError,
            "channel not found",
            None,
            channel="C999",
        )

    def test_open_create_new_conversation(self):
        """Test creating a new conversation with users."""
        result = open_conversation(users="U123,U456")
        self.assertTrue(result["ok"])
        self.assertIn("channel", result)
        self.assertIn("id", result["channel"])

    def test_open_prevent_creation(self):
        """Test preventing creation of new conversation."""
        self.assert_error_behavior(
            open_conversation,
            ValueError,
            "conversation not found",
            None,
            users="U999,U888",
            prevent_creation=True,
        )

    def test_open_invalid_channel_type(self):
        """Test that non-string channel raises TypeError."""
        self.assert_error_behavior(
            open_conversation,
            TypeError,
            "channel must be a string",
            None,
            channel=123,
        )

    def test_open_invalid_users_type(self):
        """Test that non-string users raises TypeError."""
        self.assert_error_behavior(
            open_conversation,
            TypeError,
            "users must be a string",
            None,
            users=456,
        )

    def test_open_invalid_prevent_creation_type(self):
        """Test that non-boolean prevent_creation raises TypeError."""
        self.assert_error_behavior(
            open_conversation,
            TypeError,
            "prevent_creation must be a boolean",
            None,
            users="U123",
            prevent_creation="not_bool",
        )

    def test_open_invalid_return_im_type(self):
        """Test that non-boolean return_im raises TypeError."""
        self.assert_error_behavior(
            open_conversation,
            TypeError,
            "return_im must be a boolean",
            None,
            users="U123",
            return_im="not_bool",
        )

    def test_open_return_im_false_minimal_response(self):
        """Test return_im=False returns minimal channel info."""
        result = open_conversation(channel="C123", return_im=False)
        self.assertTrue(result["ok"])
        self.assertIn("channel", result)
        self.assertIn("id", result["channel"])
        self.assertNotIn("conversations", result["channel"])
        self.assertNotIn("messages", result["channel"])

    def test_open_return_im_true_full_response(self):
        """Test return_im=True returns full channel definition."""
        result = open_conversation(channel="C123", return_im=True)
        self.assertTrue(result["ok"])
        self.assertIn("channel", result)
        full_channel = result["channel"]
        self.assertIn("id", full_channel)
        self.assertIn("name", full_channel)
        self.assertIn("conversations", full_channel)
        self.assertIn("messages", full_channel)

    def test_open_conversation_no_current_user_set(self):
        """Test that CurrentUserNotSetError is raised when no current user is set."""
        with patch(
            "slack.Conversations.DB",
            {"channels": {}, "users": {"U123": {"id": "U123", "name": "test"}}},
        ):
            self.assert_error_behavior(
                open_conversation,
                CurrentUserNotSetError,
                "No current user is set. Please set a current user first using set_current_user(user_id).",
                None,
                users="U123",
            )

    def test_open_current_user_auto_inclusion(self):
        """Test that current user is automatically included when creating conversations."""
        result = open_conversation(users="U789", return_im=True)
        self.assertTrue(result["ok"])
        
        channel = result["channel"]
        members = channel["conversations"]["members"]
        
        # Should include both current user (U456) and specified user (U789)
        self.assertIn("U456", members)  # current user
        self.assertIn("U789", members)  # specified user
        self.assertEqual(len(members), 2)
        self.assertTrue(channel["conversations"]["is_im"])
        self.assertFalse(channel["conversations"]["is_mpim"])

    def test_open_conversation_current_user_already_in_list(self):
        """Test when current user is explicitly included in users parameter."""
        result = open_conversation(users="U456,U789", return_im=True)
        self.assertTrue(result["ok"])
        
        channel = result["channel"]
        members = channel["conversations"]["members"]
        
        # Should not duplicate current user
        self.assertEqual(members.count("U456"), 1)
        self.assertIn("U789", members)
        self.assertEqual(len(members), 2)
        self.assertTrue(channel["conversations"]["is_im"])

    def test_open_conversation_multi_user_auto_inclusion(self):
        """Test current user auto-inclusion with multiple users (MPIM)."""
        result = open_conversation(users="U789,U999", return_im=True)
        self.assertTrue(result["ok"])
        
        channel = result["channel"]
        members = channel["conversations"]["members"]
        
        # Should include current user plus the two specified users
        self.assertIn("U456", members)  # current user
        self.assertIn("U789", members)  # specified user 1
        self.assertIn("U999", members)  # specified user 2
        self.assertEqual(len(members), 3)
        self.assertFalse(channel["conversations"]["is_im"])
        self.assertTrue(channel["conversations"]["is_mpim"])

    # --- Tests for User Field Assignment Bug Fix ---

    def test_open_conversation_user_field_current_user_first(self):
        """Test that user field is correctly set when current user is first in sorted list."""
        # Current user U456 should be first alphabetically when sorted with U789
        result = open_conversation(users="U789", return_im=True)
        self.assertTrue(result["ok"])
        
        channel = result["channel"]
        conversations = channel["conversations"]
        
        # Should be a 2-person DM
        self.assertTrue(conversations["is_im"])
        self.assertFalse(conversations["is_mpim"])
        
        # The user field should be the other user (U789), not the current user (U456)
        self.assertEqual(conversations["user"], "U789")
        self.assertNotEqual(conversations["user"], "U456")  # Should not be current user

    def test_open_conversation_user_field_current_user_last(self):
        """Test that user field is correctly set when current user is last in sorted list."""
        # Use a user ID that comes before U456 alphabetically and doesn't have existing conversation
        result = open_conversation(users="U999", return_im=True)
        self.assertTrue(result["ok"])
        
        channel = result["channel"]
        conversations = channel["conversations"]
        
        # Should be a 2-person DM
        self.assertTrue(conversations["is_im"])
        self.assertFalse(conversations["is_mpim"])
        
        # The user field should be the other user (U999), not the current user (U456)
        self.assertEqual(conversations["user"], "U999")
        self.assertNotEqual(conversations["user"], "U456")  # Should not be current user

    def test_open_conversation_user_field_edge_case_same_letter(self):
        """Test user field assignment with users having similar IDs."""
        # Test with a different user to create a proper 2-person DM
        result = open_conversation(users="U789", return_im=True)
        self.assertTrue(result["ok"])
        
        channel = result["channel"]
        conversations = channel["conversations"]
        
        # Should be a 2-person DM
        self.assertTrue(conversations["is_im"])
        self.assertFalse(conversations["is_mpim"])
        
        # The user field should be the other user (U789), not the current user (U456)
        self.assertEqual(conversations["user"], "U789")
        self.assertNotEqual(conversations["user"], "U456")  # Should not be current user

    def test_open_conversation_user_field_verification_bug_fix(self):
        """Test that the bug fix correctly identifies the other user."""
        # Test the specific scenario mentioned in the bug report
        # Current user is U456, other user is U789
        # After sorting: [U456, U789] - current user is first
        result = open_conversation(users="U789", return_im=True)
        self.assertTrue(result["ok"])
        
        channel = result["channel"]
        conversations = channel["conversations"]
        members = conversations["members"]
        
        # Verify the members are sorted correctly
        self.assertEqual(members, ["U456", "U789"])  # Sorted alphabetically
        
        # The user field should be U789 (the other user), not U456 (current user)
        self.assertEqual(conversations["user"], "U789")
        
        # Verify this is the correct behavior (other user, not current user)
        self.assertNotEqual(conversations["user"], "U456")  # Not current user
        self.assertEqual(conversations["user"], "U789")     # Is the other user

    def test_open_conversation_user_field_not_present_in_mpim(self):
        """Test that user field is not present in multi-person DMs."""
        # Create a 3-person conversation (MPIM)
        result = open_conversation(users="U123,U789", return_im=True)
        self.assertTrue(result["ok"])
        
        channel = result["channel"]
        conversations = channel["conversations"]
        
        # Should be an MPIM, not IM
        self.assertFalse(conversations["is_im"])
        self.assertTrue(conversations["is_mpim"])
        
        # User field should not be present in MPIMs
        self.assertNotIn("user", conversations)

    def test_open_conversation_user_field_consistency(self):
        """Test that user field assignment is consistent across different scenarios."""
        # Test multiple 2-person conversations to ensure consistency
        # Use users that don't have existing conversations
        test_cases = [
            ("U999", "U999"),  # Current user first alphabetically (U456 < U999)
            ("U789", "U789"),  # Current user first alphabetically (U456 < U789)
        ]
        
        for other_user, expected_user_field in test_cases:
            result = open_conversation(users=other_user, return_im=True)
            self.assertTrue(result["ok"])
            
            channel = result["channel"]
            conversations = channel["conversations"]
            
            # Should be a 2-person DM
            self.assertTrue(conversations["is_im"])
            self.assertFalse(conversations["is_mpim"])
            
            # User field should be the other user, not current user
            self.assertEqual(conversations["user"], expected_user_field)
            self.assertNotEqual(conversations["user"], "U456")  # Not current user
