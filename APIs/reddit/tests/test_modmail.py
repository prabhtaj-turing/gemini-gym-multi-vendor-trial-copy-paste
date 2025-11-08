import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestModmailMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Modmail class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Create a test conversation that can be used across multiple tests
        conv = RedditAPI.Modmail.get_api_mod_conversations()
        self.conversation_id = (
            conv["conversations"][0]["id"] if conv["conversations"] else "test_conv"
        )

    def test_bulk_read(self):
        """Test bulk reading conversations."""
        pass

    def test_get_conversations(self):
        """Test getting conversations."""
        pass

    def test_get_conversation_by_id(self):
        """Test getting conversation by ID."""
        pass

    def test_approve_conversation(self):
        """Test approving a conversation."""
        pass

    def test_archive_conversation(self):
        """Test archiving a conversation."""
        pass

    def test_disapprove_conversation(self):
        """Test disapproving a conversation."""
        pass

    def test_delete_highlight(self):
        """Test deleting highlight."""
        pass

    def test_mute_user(self):
        """Test muting a user."""
        pass

    def test_temp_ban(self):
        """Test issuing a temporary ban."""
        pass

    def test_unarchive_conversation(self):
        """Test unarchiving a conversation."""
        pass

    def test_unban_user(self):
        """Test unbanning a user."""
        pass

    def test_unmute_user(self):
        """Test unmuting a user."""
        pass

    def test_mark_conversations_read(self):
        """Test marking conversations as read."""
        pass

    def test_get_subreddits(self):
        """Test getting subreddits."""
        pass

    def test_mark_conversations_unread(self):
        """Test marking conversations as unread."""
        pass

    def test_get_unread_count(self):
        """Test getting unread count."""
        pass
