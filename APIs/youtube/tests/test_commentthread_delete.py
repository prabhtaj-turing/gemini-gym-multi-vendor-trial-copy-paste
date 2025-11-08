import unittest
from unittest.mock import patch
from youtube.CommentThread import delete
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.custom_errors import InvalidThreadIDError
from common_utils.base_case import BaseTestCaseWithErrorHandler



class TestCommentThreadDelete(BaseTestCaseWithErrorHandler):
    """Test cases for the CommentThread.delete function."""

    def setUp(self):
        """Reset the database before each test."""
        DB.clear()
        DB.update(
            {
                "commentThreads": {
                    "thread1": {
                        "id": "thread1",
                        "snippet": {
                            "channelId": "channel1",
                            "videoId": "video1",
                            "title": "First Thread",
                        },
                        "comments": ["comment1", "comment2"],
                    },
                    "thread2": {
                        "id": "thread2",
                        "snippet": {
                            "channelId": "channel2",
                            "videoId": "video2",
                            "title": "Second Thread",
                        },
                        "comments": ["comment3", "comment4"],
                    },
                    "thread3": {
                        "id": "thread3",
                        "snippet": {
                            "channelId": "channel3",
                            "videoId": "video3",
                            "title": "Third Thread",
                        },
                        "comments": ["comment5"],
                    },
                }
            }
        )

    def test_delete_existing_thread_success(self):
        """Test successful deletion of an existing comment thread."""
        result = delete(thread_id="thread1")
        
        self.assertEqual(result["success"], "Thread deleted successfully")
        self.assertNotIn("thread1", DB["commentThreads"])
        self.assertEqual(len(DB["commentThreads"]), 2)

    def test_delete_nonexistent_thread(self):
        """Test deletion of a non-existent comment thread returns error."""
        result = delete(thread_id="nonexistent_thread")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Thread not found")
        # Ensure no threads were deleted
        self.assertEqual(len(DB["commentThreads"]), 3)

    def test_delete_thread_invalid_type(self):
        """Test that providing non-string thread_id raises InvalidThreadIDError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidThreadIDError,
            expected_message="Thread ID must be a string.",
            thread_id=123
        )

    def test_delete_thread_empty_string(self):
        """Test that providing empty string thread_id raises InvalidThreadIDError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidThreadIDError,
            expected_message="Thread ID cannot be empty or contain only whitespace.",
            thread_id=""
        )

    def test_delete_thread_whitespace_only(self):
        """Test that providing whitespace-only thread_id raises InvalidThreadIDError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidThreadIDError,
            expected_message="Thread ID cannot be empty or contain only whitespace.",
            thread_id="   "
        )

    def test_delete_thread_none_value(self):
        """Test that providing None as thread_id raises InvalidThreadIDError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidThreadIDError,
            expected_message="Thread ID must be a string.",
            thread_id=None
        )

    def test_delete_thread_tabs_and_newlines(self):
        """Test that providing thread_id with only tabs and newlines raises InvalidThreadIDError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidThreadIDError,
            expected_message="Thread ID cannot be empty or contain only whitespace.",
            thread_id="\t\n\r"
        )

    def test_delete_multiple_threads_sequentially(self):
        """Test deleting multiple comment threads one by one."""
        # Delete first thread
        result1 = delete(thread_id="thread1")
        self.assertEqual(result1["success"], "Thread deleted successfully")
        self.assertNotIn("thread1", DB["commentThreads"])
        self.assertEqual(len(DB["commentThreads"]), 2)

        # Delete second thread
        result2 = delete(thread_id="thread2")
        self.assertEqual(result2["success"], "Thread deleted successfully")
        self.assertNotIn("thread2", DB["commentThreads"])
        self.assertEqual(len(DB["commentThreads"]), 1)

        # Verify remaining thread
        self.assertIn("thread3", DB["commentThreads"])

    def test_delete_thread_preserves_other_threads(self):
        """Test that deleting one thread doesn't affect others."""
        original_thread2 = DB["commentThreads"]["thread2"].copy()
        original_thread3 = DB["commentThreads"]["thread3"].copy()
        
        result = delete(thread_id="thread1")
        
        self.assertEqual(result["success"], "Thread deleted successfully")
        self.assertNotIn("thread1", DB["commentThreads"])
        # Verify other threads remain unchanged
        self.assertEqual(DB["commentThreads"]["thread2"], original_thread2)
        self.assertEqual(DB["commentThreads"]["thread3"], original_thread3)

    def test_delete_thread_with_special_characters(self):
        """Test deleting a thread with special characters in ID."""
        # Add a thread with special characters in ID
        special_id = "thread_with-special.chars@123"
        DB["commentThreads"][special_id] = {
            "id": special_id,
            "snippet": {
                "channelId": "channel_special",
                "videoId": "video_special",
                "title": "Special Thread",
            },
            "comments": ["comment_special"],
        }
        
        result = delete(thread_id=special_id)
        
        self.assertEqual(result["success"], "Thread deleted successfully")
        self.assertNotIn(special_id, DB["commentThreads"])

    def test_delete_thread_database_consistency(self):
        """Test that database remains consistent after deletion."""
        initial_count = len(DB["commentThreads"])
        
        # Delete existing thread
        result = delete(thread_id="thread2")
        self.assertEqual(result["success"], "Thread deleted successfully")
        self.assertEqual(len(DB["commentThreads"]), initial_count - 1)
        
        # Try to delete the same thread again
        result = delete(thread_id="thread2")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Thread not found")
        # Count should remain the same
        self.assertEqual(len(DB["commentThreads"]), initial_count - 1)

    def test_delete_thread_with_empty_comments_list(self):
        """Test deleting a thread with empty comments list."""
        # Add a thread with empty comments
        empty_thread_id = "empty_thread"
        DB["commentThreads"][empty_thread_id] = {
            "id": empty_thread_id,
            "snippet": {
                "channelId": "channel_empty",
                "videoId": "video_empty",
                "title": "Empty Thread",
            },
            "comments": [],
        }
        
        result = delete(thread_id=empty_thread_id)
        
        self.assertEqual(result["success"], "Thread deleted successfully")
        self.assertNotIn(empty_thread_id, DB["commentThreads"])

    def test_delete_thread_with_unicode_characters(self):
        """Test deleting a thread with unicode characters in ID."""
        # Add a thread with unicode characters in ID
        unicode_id = "thread_unicode_测试_🎥"
        DB["commentThreads"][unicode_id] = {
            "id": unicode_id,
            "snippet": {
                "channelId": "channel_unicode",
                "videoId": "video_unicode",
                "title": "Unicode Thread",
            },
            "comments": ["comment_unicode"],
        }
        
        result = delete(thread_id=unicode_id)
        
        self.assertEqual(result["success"], "Thread deleted successfully")
        self.assertNotIn(unicode_id, DB["commentThreads"])

    def test_delete_thread_empty_database(self):
        """Test deletion when database is empty."""
        DB.clear()
        DB.update({"commentThreads": {}})
        
        result = delete(thread_id="any_thread")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Thread not found")

    def test_delete_thread_missing_commentthreads_key(self):
        """Test deletion when commentThreads key is missing from database."""
        DB.clear()
        
        result = delete(thread_id="any_thread")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Thread not found")

    def test_delete_thread_float_as_string(self):
        """Test that providing float as thread_id raises InvalidThreadIDError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidThreadIDError,
            expected_message="Thread ID must be a string.",
            thread_id=123.45
        )

    def test_delete_thread_list_as_string(self):
        """Test that providing list as thread_id raises InvalidThreadIDError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidThreadIDError,
            expected_message="Thread ID must be a string.",
            thread_id=["thread1"]
        )

    def test_delete_thread_dict_as_string(self):
        """Test that providing dict as thread_id raises InvalidThreadIDError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidThreadIDError,
            expected_message="Thread ID must be a string.",
            thread_id={"id": "thread1"}
        )


if __name__ == "__main__":
    unittest.main() 