import unittest
from unittest.mock import patch
from google_chat.Spaces.Messages import delete
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_chat.SimulationEngine.custom_errors import (
    InvalidMessageNameFormatError, UserNotMemberError, MessageNotFoundError, 
    MessageHasRepliesError
)


class TestMessagesDeleteValidation(BaseTestCaseWithErrorHandler):
    """Test cases for the messages delete function with comprehensive validation and edge cases."""
    
    def setUp(self):
        """Reset test state (DB and CURRENT_USER_ID) before each test."""
        # Import here to avoid circular imports
        from google_chat.SimulationEngine.db import DB, CURRENT_USER_ID
        
        # Reset DB state
        DB.clear()
        DB.update({
            "Space": [],
            "Membership": [],
            "Message": [],
            "Reaction": [],
            "Attachment": []
        })
        
        # Reset current user
        CURRENT_USER_ID.clear()
        CURRENT_USER_ID.update({"id": "test_user_123"})
        
        # Store references for test access
        self.DB = DB
        self.CURRENT_USER_ID = CURRENT_USER_ID
        
        # Set up test data
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Set up common test data for all tests."""
        # Create test space
        self.test_space = "spaces/SPACE123"
        self.test_message_name = f"{self.test_space}/messages/MSG456"
        
        # Add test space to DB
        self.DB["Space"].append({
            "name": self.test_space,
            "displayName": "Test Space"
        })
        
        # Add test user membership
        self.DB["Membership"].append({
            "name": f"{self.test_space}/members/{self.CURRENT_USER_ID['id']}",
            "member": f"users/{self.CURRENT_USER_ID['id']}"
        })
        
        # Add test message
        self.DB["Message"].append({
            "name": self.test_message_name,
            "text": "Test message",
            "createTime": "2023-01-01T00:00:00Z",
            "sender": {"name": f"users/{self.CURRENT_USER_ID['id']}", "type": "HUMAN"},
            "thread": {"name": f"{self.test_space}/threads/THREAD789"}
        })
    
    # --- Input Validation Tests ---
    
    def test_invalid_name_type_non_string(self):
        """Test that non-string 'name' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=123
        )
    
    def test_invalid_name_type_none(self):
        """Test that None 'name' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=None
        )
    
    def test_invalid_name_type_list(self):
        """Test that list 'name' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=["spaces", "test", "messages", "123"]
        )
    
    def test_invalid_name_empty_string(self):
        """Test that empty string 'name' raises ValueError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=ValueError,
            expected_message="Argument 'name' cannot be empty.",
            name=""
        )
    
    def test_invalid_name_whitespace_only(self):
        """Test that whitespace-only 'name' raises InvalidMessageNameFormatError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidMessageNameFormatError,
            expected_message="Argument 'name' ('   ') is not in the expected format 'spaces/{space}/messages/{message}'.",
            name="   "
        )
    
    def test_invalid_name_format_no_spaces_prefix(self):
        """Test 'name' without 'spaces/' prefix raises InvalidMessageNameFormatError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidMessageNameFormatError,
            expected_message="Argument 'name' ('test/messages/123') is not in the expected format 'spaces/{space}/messages/{message}'.",
            name="test/messages/123"
        )
    
    def test_invalid_name_format_no_messages_part(self):
        """Test 'name' without 'messages' part raises InvalidMessageNameFormatError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidMessageNameFormatError,
            expected_message="Argument 'name' ('spaces/test/123') is not in the expected format 'spaces/{space}/messages/{message}'.",
            name="spaces/test/123"
        )
    
    def test_invalid_name_format_too_many_parts(self):
        """Test 'name' with too many parts raises InvalidMessageNameFormatError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidMessageNameFormatError,
            expected_message="Argument 'name' ('spaces/test/messages/123/extra') is not in the expected format 'spaces/{space}/messages/{message}'.",
            name="spaces/test/messages/123/extra"
        )
    
    def test_invalid_name_format_trailing_slash(self):
        """Test 'name' with trailing slash raises InvalidMessageNameFormatError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidMessageNameFormatError,
            expected_message="Argument 'name' ('spaces/test/messages/123/') is not in the expected format 'spaces/{space}/messages/{message}'.",
            name="spaces/test/messages/123/"
        )
    
    def test_invalid_name_format_empty_space_id(self):
        """Test 'name' with empty space ID raises InvalidMessageNameFormatError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidMessageNameFormatError,
            expected_message="Argument 'name' ('spaces//messages/123') is not in the expected format 'spaces/{space}/messages/{message}'.",
            name="spaces//messages/123"
        )
    
    def test_invalid_name_format_empty_message_id(self):
        """Test 'name' with empty message ID raises InvalidMessageNameFormatError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidMessageNameFormatError,
            expected_message="Argument 'name' ('spaces/test/messages/') is not in the expected format 'spaces/{space}/messages/{message}'.",
            name="spaces/test/messages/"
        )
    
    def test_invalid_force_type_string(self):
        """Test that string 'force' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Argument 'force' must be a boolean or None.",
            name=self.test_message_name,
            force="true"
        )
    
    def test_invalid_force_type_integer(self):
        """Test that integer 'force' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Argument 'force' must be a boolean or None.",
            name=self.test_message_name,
            force=1
        )
    
    def test_invalid_force_type_list(self):
        """Test that list 'force' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Argument 'force' must be a boolean or None.",
            name=self.test_message_name,
            force=[True]
        )
    
    # --- Authorization Tests ---
    
    def test_user_not_member_of_space(self):
        """Test that user who is not a member of the space cannot delete messages."""
        # Remove user from membership
        self.DB["Membership"].clear()
        
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=UserNotMemberError,
            expected_message=f"User {self.CURRENT_USER_ID['id']} is not a member of {self.test_space}.",
            name=self.test_message_name
        )
    
    def test_no_current_user_id(self):
        """Test behavior when CURRENT_USER_ID is None."""
        self.CURRENT_USER_ID.clear()
        
        # Since no user ID is set, authorization check should be bypassed
        result = delete(name=self.test_message_name)
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_current_user_id_empty_dict(self):
        """Test behavior when CURRENT_USER_ID is an empty dict."""
        self.CURRENT_USER_ID.clear()
        
        # Since no user ID is set, authorization check should be bypassed
        result = delete(name=self.test_message_name)
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    # --- Core Logic Tests ---
    
    def test_message_not_found(self):
        """Test that trying to delete a non-existent message raises MessageNotFoundError."""
        non_existent_name = f"{self.test_space}/messages/NONEXISTENT"
        
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=MessageNotFoundError,
            expected_message=f"Message '{non_existent_name}' not found.",
            name=non_existent_name
        )
    
    def test_successful_deletion_simple_message(self):
        """Test successful deletion of a simple message without replies."""
        # Remove thread info to make it a simple message
        for msg in self.DB["Message"]:
            if msg.get("name") == self.test_message_name:
                msg.pop("thread", None)
                break
        
        result = delete(name=self.test_message_name)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_successful_deletion_with_force_none(self):
        """Test successful deletion when force=None (default behavior)."""
        # Remove thread info to make it a simple message
        for msg in self.DB["Message"]:
            if msg.get("name") == self.test_message_name:
                msg.pop("thread", None)
                break
        
        result = delete(name=self.test_message_name, force=None)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_successful_deletion_with_force_false(self):
        """Test successful deletion when force=False and no replies."""
        # Remove thread info to make it a simple message
        for msg in self.DB["Message"]:
            if msg.get("name") == self.test_message_name:
                msg.pop("thread", None)
                break
        
        result = delete(name=self.test_message_name, force=False)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_message_with_replies_force_false(self):
        """Test that deleting a message with replies fails when force=False."""
        # Add a reply message
        reply_name = f"{self.test_space}/messages/REPLY123"
        self.DB["Message"].append({
            "name": reply_name,
            "text": "Reply message",
            "createTime": "2023-01-01T01:00:00Z",
            "sender": {"name": f"users/{self.CURRENT_USER_ID['id']}", "type": "HUMAN"},
            "thread": {"name": f"{self.test_space}/threads/THREAD789"}  # Same thread as original
        })
        
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=MessageHasRepliesError,
            expected_message=f"Message '{self.test_message_name}' has 1 threaded replies. Set force=True to delete them.",
            name=self.test_message_name,
            force=False
        )
    
    def test_message_with_replies_force_none(self):
        """Test that deleting a message with replies fails when force=None."""
        # Add a reply message
        reply_name = f"{self.test_space}/messages/REPLY123"
        self.DB["Message"].append({
            "name": reply_name,
            "text": "Reply message",
            "createTime": "2023-01-01T01:00:00Z",
            "sender": {"name": f"users/{self.CURRENT_USER_ID['id']}", "type": "HUMAN"},
            "thread": {"name": f"{self.test_space}/threads/THREAD789"}  # Same thread as original
        })
        
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=MessageHasRepliesError,
            expected_message=f"Message '{self.test_message_name}' has 1 threaded replies. Set force=True to delete them.",
            name=self.test_message_name,
            force=None
        )
    
    def test_message_with_multiple_replies_force_false(self):
        """Test that deleting a message with multiple replies fails when force=False."""
        # Add multiple reply messages
        for i in range(3):
            reply_name = f"{self.test_space}/messages/REPLY{i}"
            self.DB["Message"].append({
                "name": reply_name,
                "text": f"Reply message {i}",
                "createTime": f"2023-01-01T0{i}:00:00Z",
                "sender": {"name": f"users/{self.CURRENT_USER_ID['id']}", "type": "HUMAN"},
                "thread": {"name": f"{self.test_space}/threads/THREAD789"}  # Same thread as original
            })
        
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=MessageHasRepliesError,
            expected_message=f"Message '{self.test_message_name}' has 3 threaded replies. Set force=True to delete them.",
            name=self.test_message_name,
            force=False
        )
    
    def test_successful_deletion_with_replies_force_true(self):
        """Test successful deletion with replies when force=True."""
        # Add reply messages
        reply_names = []
        for i in range(2):
            reply_name = f"{self.test_space}/messages/REPLY{i}"
            reply_names.append(reply_name)
            self.DB["Message"].append({
                "name": reply_name,
                "text": f"Reply message {i}",
                "createTime": f"2023-01-01T0{i}:00:00Z",
                "sender": {"name": f"users/{self.CURRENT_USER_ID['id']}", "type": "HUMAN"},
                "thread": {"name": f"{self.test_space}/threads/THREAD789"}  # Same thread as original
            })
        
        result = delete(name=self.test_message_name, force=True)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify original message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
        
        # Verify all replies were deleted
        for reply_name in reply_names:
            remaining_replies = [m for m in self.DB["Message"] if m.get("name") == reply_name]
            self.assertEqual(len(remaining_replies), 0)
    
    def test_message_without_thread_info(self):
        """Test deletion of message without thread information."""
        # Remove thread info from test message
        for msg in self.DB["Message"]:
            if msg.get("name") == self.test_message_name:
                msg.pop("thread", None)
                break
        
        result = delete(name=self.test_message_name)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_message_with_empty_thread_info(self):
        """Test deletion of message with empty thread information."""
        # Set empty thread info
        for msg in self.DB["Message"]:
            if msg.get("name") == self.test_message_name:
                msg["thread"] = {}
                break
        
        result = delete(name=self.test_message_name)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_message_with_thread_name_none(self):
        """Test deletion of message with thread name as None."""
        # Set thread name to None
        for msg in self.DB["Message"]:
            if msg.get("name") == self.test_message_name:
                msg["thread"] = {"name": None}
                break
        
        result = delete(name=self.test_message_name)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_message_with_thread_name_empty_string(self):
        """Test deletion of message with thread name as empty string."""
        # Set thread name to empty string
        for msg in self.DB["Message"]:
            if msg.get("name") == self.test_message_name:
                msg["thread"] = {"name": ""}
                break
        
        result = delete(name=self.test_message_name)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == self.test_message_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_edge_case_no_messages_in_db(self):
        """Test deletion when there are no messages in the database."""
        # Clear all messages
        self.DB["Message"].clear()
        
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=MessageNotFoundError,
            expected_message=f"Message '{self.test_message_name}' not found.",
            name=self.test_message_name
        )
    
    def test_edge_case_empty_db(self):
        """Test deletion when the database is completely empty."""
        # Clear entire DB
        self.DB.clear()
        
        # When DB is empty, authorization check fails first (no memberships exist)
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=UserNotMemberError,
            expected_message=f"User {self.CURRENT_USER_ID['id']} is not a member of {self.test_space}.",
            name=self.test_message_name
        )
    
    def test_edge_case_client_assigned_message_id(self):
        """Test deletion with client-assigned message ID."""
        client_msg_name = f"{self.test_space}/messages/client-custom-id"
        
        # Add message with client-assigned ID
        self.DB["Message"].append({
            "name": client_msg_name,
            "text": "Message with client ID",
            "createTime": "2023-01-01T00:00:00Z",
            "sender": {"name": f"users/{self.CURRENT_USER_ID['id']}", "type": "HUMAN"},
            "clientAssignedMessageId": "client-custom-id"
        })
        
        result = delete(name=client_msg_name)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == client_msg_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_edge_case_special_characters_in_name(self):
        """Test deletion with special characters in message name."""
        special_msg_name = f"{self.test_space}/messages/MSG-123_test.456"
        
        # Add message with special characters
        self.DB["Message"].append({
            "name": special_msg_name,
            "text": "Message with special chars",
            "createTime": "2023-01-01T00:00:00Z",
            "sender": {"name": f"users/{self.CURRENT_USER_ID['id']}", "type": "HUMAN"}
        })
        
        result = delete(name=special_msg_name)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == special_msg_name]
        self.assertEqual(len(remaining_messages), 0)
    
    def test_edge_case_very_long_message_name(self):
        """Test deletion with very long message name."""
        long_id = "a" * 200  # Very long ID
        long_msg_name = f"{self.test_space}/messages/{long_id}"
        
        # Add message with long name
        self.DB["Message"].append({
            "name": long_msg_name,
            "text": "Message with long name",
            "createTime": "2023-01-01T00:00:00Z",
            "sender": {"name": f"users/{self.CURRENT_USER_ID['id']}", "type": "HUMAN"}
        })
        
        result = delete(name=long_msg_name)
        
        # Verify return value
        self.assertIsNone(result)
        
        # Verify message was deleted
        remaining_messages = [m for m in self.DB["Message"] if m.get("name") == long_msg_name]
        self.assertEqual(len(remaining_messages), 0)


if __name__ == '__main__':
    unittest.main() 