import unittest
from ..SimulationEngine.custom_errors import EmptyMessageTextError, EmptySubjectError, InvalidRecipientError
import reddit as RedditAPI
from .common import reset_db
import time
from common_utils.base_case import BaseTestCaseWithErrorHandler
from reddit import compose_message
from reddit.SimulationEngine.db import DB

class TestMessagesMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Messages class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Create a test message that can be used across multiple tests
        compose = RedditAPI.Messages.post_api_compose("someUser@example.com", "Hello", "Body text")
        self.message_id = compose["message_id"]

    def test_block_message(self):
        """Test blocking a message."""
        block = RedditAPI.Messages.post_api_block("msg_1")
        self.assertEqual(block["status"], "blocked")

    def test_collapse_message(self):
        """Test collapsing a message."""
        collapse = RedditAPI.Messages.post_api_collapse_message(["msg_2"])
        self.assertEqual(collapse["status"], "collapsed")

    def test_compose_message(self):
        """Test composing a message with all required fields."""
        # Test successful message composition
        compose = RedditAPI.Messages.post_api_compose(
            "testUser@example.com", "Test Subject", "Test Body"
        )
        self.assertEqual(compose["status"], "message_sent")
        self.assertIn("message_id", compose)

        # Verify message exists in DB with all required fields
        message_id = compose["message_id"]
        message = RedditAPI.DB["messages"][message_id]

        self.assertEqual(message["id"], message_id)
        self.assertEqual(message["to"], "testUser@example.com")
        self.assertEqual(message["from"], "reddit_user")
        self.assertEqual(message["subject"], "Test Subject")
        self.assertEqual(message["text"], "Test Body")
        self.assertIsInstance(message["timestamp"], int)
        self.assertFalse(message["read"])

        # Verify timestamp is recent (within last 5 seconds)
        current_time = int(time.time())
        self.assertLessEqual(abs(current_time - message["timestamp"]), 5)

    def test_compose_message_errors(self):
        """Test error cases for message composition."""
        # Test empty recipient - this should raise InvalidRecipientError

        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=InvalidRecipientError,
            expected_message="Recipient 'to' cannot be empty or consist only of whitespace.",
            to="", subject="Valid Subject", text="Valid Text"
        )

        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=EmptySubjectError,
            expected_message="Subject cannot be empty or consist only of whitespace.",
            to="valid_user@example.com", subject="", text="Valid Text"
        )

        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=EmptyMessageTextError,
            expected_message="Message text cannot be empty or consist only of whitespace.",
            to="valid_user@example.com", subject="Valid Subject", text=""
        )

        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=InvalidRecipientError,
            expected_message="Recipient 'to' cannot be empty or consist only of whitespace.",
            to="   ", subject="Valid Subject", text="Valid Text"
        )
            
        
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=EmptySubjectError,
            expected_message="Subject cannot be empty or consist only of whitespace.",
            to="valid_user@example.com", subject="   ", text="Valid Text"
        )
        
        
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=EmptyMessageTextError,
            expected_message="Message text cannot be empty or consist only of whitespace.",
            to="valid_user@example.com", subject="Valid Subject", text="   "
        )

    def test_delete_message(self):
        """Test deleting a message."""
        del_msg = RedditAPI.Messages.post_api_del_msg(self.message_id)
        self.assertEqual(del_msg["status"], "message_deleted")
        # Verify message is deleted from DB
        self.assertNotIn(self.message_id, RedditAPI.DB["messages"])

    def test_delete_message_errors(self):
        """Test error cases for message deletion."""
        # Test empty message ID
        result = RedditAPI.Messages.post_api_del_msg("")
        self.assertEqual(result["error"], "Invalid message ID.")

        # Test non-existent message ID
        result = RedditAPI.Messages.post_api_del_msg("nonexistent_id")
        self.assertEqual(result["error"], "Message not found.")

    def test_read_all_messages(self):
        """Test marking all messages as read."""
        all_read = RedditAPI.Messages.post_api_read_all_messages()
        self.assertEqual(all_read["status"], "all_messages_marked_read")

    def test_read_specific_messages(self):
        """Test marking specific messages as read."""
        read_some = RedditAPI.Messages.post_api_read_message(["msg_3"])
        self.assertEqual(read_some["status"], "messages_marked_read")

    def test_unblock_subreddit(self):
        """Test unblocking a subreddit."""
        unblock_sr = RedditAPI.Messages.post_api_unblock_subreddit()
        self.assertEqual(unblock_sr["status"], "subreddit_unblocked")

    def test_uncollapse_message(self):
        """Test uncollapsing a message."""
        uncollapse = RedditAPI.Messages.post_api_uncollapse_message(["msg_4"])
        self.assertEqual(uncollapse["status"], "uncollapsed")

    def test_unread_message(self):
        """Test marking messages as unread."""
        unread_msg = RedditAPI.Messages.post_api_unread_message(["msg_5"])
        self.assertEqual(unread_msg["status"], "marked_unread")

    def test_get_inbox(self):
        """Test getting inbox messages."""
        inbox = RedditAPI.Messages.get_message_inbox()
        self.assertIsInstance(inbox, list)
        if inbox:
            message = inbox[0]
            self.assertIn("id", message)
            self.assertIn("to", message)
            self.assertIn("from", message)
            self.assertIn("subject", message)
            self.assertIn("text", message)
            self.assertIn("timestamp", message)
            self.assertIn("read", message)

    def test_get_sent_messages(self):
        """Test getting sent messages."""
        sent = RedditAPI.Messages.get_message_sent()
        self.assertIsInstance(sent, list)
        if sent:
            message = sent[0]
            self.assertIn("id", message)
            self.assertIn("to", message)
            self.assertIn("from", message)
            self.assertIn("subject", message)
            self.assertIn("text", message)
            self.assertIn("timestamp", message)
            self.assertIn("read", message)

    def test_get_unread_messages(self):
        """Test getting unread messages."""
        unrd = RedditAPI.Messages.get_message_unread()
        self.assertIsInstance(unrd, list)
        if unrd:
            message = unrd[0]
            self.assertIn("id", message)
            self.assertIn("to", message)
            self.assertIn("from", message)
            self.assertIn("subject", message)
            self.assertIn("text", message)
            self.assertIn("timestamp", message)
            self.assertIn("read", message)

    def test_get_messages_by_location(self):
        """Test getting messages by location."""
        wh = RedditAPI.Messages.get_message_where("inbox")
        self.assertIsInstance(wh, list)
        if wh:
            message = wh[0]
            self.assertIn("id", message)
            self.assertIn("to", message)
            self.assertIn("from", message)
            self.assertIn("subject", message)
            self.assertIn("text", message)
            self.assertIn("timestamp", message)
            self.assertIn("read", message)


# ================================

    def test_valid_input(self):
        """Test that valid inputs result in a successful message composition."""
        to_user = "recipient@example.com"
        subject_line = "Hello There"
        message_text = "This is a test message."
        
        result = compose_message(to=to_user, subject=subject_line, text=message_text)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "message_sent")
        self.assertIn("message_id", result)
        message_id = result["message_id"]
        self.assertEqual(message_id, "msg_2")  # Second message since setUp creates one
        
        # Verify message stored in DB
        self.assertIn("messages", DB)
        self.assertIn(message_id, DB["messages"])
        stored_message = DB["messages"][message_id]
        self.assertEqual(stored_message["to"], to_user)
        self.assertEqual(stored_message["subject"], subject_line)
        self.assertEqual(stored_message["text"], message_text)

    def test_valid_input_with_leading_trailing_whitespace_preserved(self):
        """Test that leading/trailing whitespace in valid inputs is preserved in storage."""
        to_user = " recipient@example.com " # Whitespace should be preserved
        subject_line = " Important Subject "
        message_text = " Message with spaces "
        
        result = compose_message(to=to_user, subject=subject_line, text=message_text)
        self.assertEqual(result.get("status"), "message_sent")
        message_id = result["message_id"]

        stored_message = DB["messages"][message_id]
        self.assertEqual(stored_message["to"], to_user) # Check preservation
        self.assertEqual(stored_message["subject"], subject_line)
        self.assertEqual(stored_message["text"], message_text)

    # --- Tests for 'to' argument ---
    def test_invalid_to_type(self):
        """Test that a non-string 'to' argument raises TypeError."""
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=TypeError,
            expected_message="Argument 'to' must be a string.",
            to=123, subject="Valid Subject", text="Valid Text"
        )

    def test_empty_to_string(self):
        """Test that an empty 'to' string raises InvalidRecipientError."""
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=InvalidRecipientError,
            expected_message="Recipient 'to' cannot be empty or consist only of whitespace.",
            to="", subject="Valid Subject", text="Valid Text"
        )

    def test_whitespace_to_string(self):
        """Test that a whitespace-only 'to' string raises InvalidRecipientError."""
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=InvalidRecipientError,
            expected_message="Recipient 'to' cannot be empty or consist only of whitespace.",
            to="   ", subject="Valid Subject", text="Valid Text"
        )

    # --- Tests for 'subject' argument ---
    def test_invalid_subject_type(self):
        """Test that a non-string 'subject' argument raises TypeError."""
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=TypeError,
            expected_message="Argument 'subject' must be a string.",
            to="valid_user@example.com", subject=123, text="Valid Text"
        )

    def test_empty_subject_string(self):
        """Test that an empty 'subject' string raises an error."""
        
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=EmptySubjectError,
            expected_message="Subject cannot be empty or consist only of whitespace.",
            to="valid_user@example.com", subject="", text="Valid Text"
        )

    def test_whitespace_subject_string(self):
        """Test that a whitespace-only 'subject' string raises an error."""
        # In the implementation, EmptySubjectError is not properly imported
        # so a NameError is raised instead
        
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=EmptySubjectError,
            expected_message="Subject cannot be empty or consist only of whitespace.",
            to="valid_user@example.com", subject="   ", text="Valid Text"
        )

    # --- Tests for 'text' argument ---
    def test_invalid_text_type(self):
        """Test that a non-string 'text' argument raises TypeError."""
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=TypeError,
            expected_message="Argument 'text' must be a string.",
            to="valid_user@example.com", subject="Valid Subject", text=123
        )

    def test_empty_text_string(self):
        """Test that an empty 'text' string raises EmptyMessageTextError."""
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=EmptyMessageTextError,
            expected_message="Message text cannot be empty or consist only of whitespace.",
            to="valid_user@example.com", subject="Valid Subject", text=""
        )

    def test_whitespace_text_string(self):
        """Test that a whitespace-only 'text' string raises EmptyMessageTextError."""
        self.assert_error_behavior(
            func_to_call=RedditAPI.Messages.post_api_compose,
            expected_exception_type=EmptyMessageTextError,
            expected_message="Message text cannot be empty or consist only of whitespace.",
            to="valid_user@example.com", subject="Valid Subject", text="   "
        )

    def test_subsequent_calls_increment_message_id(self):
        """Test that subsequent calls generate incremental message IDs."""
        # Reset the DB messages for a clean test
        DB["messages"] = {}
        
        # First call should create "msg_1"
        result1 = compose_message(to="user1@example.com", subject="Sub1", text="Text1")
        self.assertEqual(result1["message_id"], "msg_1")
        
        # Second call should create "msg_2"
        result2 = compose_message(to="user2@example.com", subject="Sub2", text="Text2")
        self.assertEqual(result2["message_id"], "msg_2")
        
        self.assertEqual(len(DB["messages"]), 2)



if __name__ == "__main__":
    unittest.main()
