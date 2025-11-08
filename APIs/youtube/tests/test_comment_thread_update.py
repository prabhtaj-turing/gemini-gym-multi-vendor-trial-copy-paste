import unittest
from unittest.mock import patch
from pydantic import ValidationError

from ..SimulationEngine.db import DB
from ..CommentThread import update
from ..CommentThread import list as list_comments_thread
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestCommentThreadUpdate(BaseTestCaseWithErrorHandler):
    """Test cases for the CommentThread.update function with Pydantic validation."""

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
                            "title": "Original Thread Title",
                        },
                        "comments": ["comment1", "comment2"],
                    },
                    "thread2": {
                        "id": "thread2",
                        "snippet": {
                            "channelId": "channel2",
                            "videoId": "video2",
                            "title": "Another Thread",
                        },
                        "comments": ["comment3"],
                    },
                    "thread3": {
                        "id": "thread3",
                        "snippet": {"channelId": "channel3", "videoId": "video3"},
                        "comments": [],
                    },
                }
            }
        )

    # ==================== SUCCESSFUL UPDATE TESTS ====================

    def test_update_snippet_only(self):
        """Test updating only the snippet field."""
        new_snippet = {
            "channelId": "channel2",
            "videoId": "video2",
            "title": "Updated Thread Title",
            "description": "Updated description",
        }

        result = update(thread_id="thread1", snippet=new_snippet)

        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(DB["commentThreads"]["thread1"]["snippet"], new_snippet)
        # Ensure other fields remain unchanged
        self.assertEqual(
            DB["commentThreads"]["thread1"]["comments"], ["comment1", "comment2"]
        )

    def test_update_comments_only(self):
        """Test updating only the comments field."""
        new_comments = ["comment4", "comment5", "comment6"]

        result = update(thread_id="thread1", comments=new_comments)

        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(DB["commentThreads"]["thread1"]["comments"], new_comments)
        # Ensure other fields remain unchanged
        self.assertEqual(
            DB["commentThreads"]["thread1"]["snippet"]["channelId"], "channel1"
        )

    def test_update_all_fields(self):
        """Test updating all fields simultaneously."""
        new_snippet = {
            "channelId": "channel3",
            "videoId": "video3",
            "title": "Completely Updated Thread",
            "description": "New description",
        }
        new_comments = ["comment7", "comment8"]

        result = update(thread_id="thread2", snippet=new_snippet, comments=new_comments)

        self.assertEqual(result["success"], "Thread ID: thread2 updated successfully.")
        self.assertEqual(DB["commentThreads"]["thread2"]["snippet"], new_snippet)
        self.assertEqual(DB["commentThreads"]["thread2"]["comments"], new_comments)

    def test_update_snippet_with_additional_fields(self):
        """Test updating snippet with additional fields beyond the standard ones."""
        new_snippet = {
            "channelId": "channel1",
            "videoId": "video1",
            "title": "Updated title",
            "description": "Updated description",
            "totalReplyCount": 5,
            "publishedAt": "2024-01-01T00:00:00Z",
            "customField": "custom_value",
        }

        result = update(thread_id="thread1", snippet=new_snippet)

        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(DB["commentThreads"]["thread1"]["snippet"], new_snippet)
        self.assertEqual(
            DB["commentThreads"]["thread1"]["snippet"]["customField"], "custom_value"
        )

    def test_update_comments_various_lists(self):
        """Test updating comments with various list configurations."""
        # Test with single comment
        result = update(thread_id="thread1", comments=["single_comment"])
        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(
            DB["commentThreads"]["thread1"]["comments"], ["single_comment"]
        )

        # Test with multiple comments
        result = update(
            thread_id="thread1", comments=["comment1", "comment2", "comment3"]
        )
        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(
            DB["commentThreads"]["thread1"]["comments"],
            ["comment1", "comment2", "comment3"],
        )

    def test_update_empty_comments_list(self):
        """Test updating with empty comments list."""
        result = update(thread_id="thread1", comments=[])

        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(DB["commentThreads"]["thread1"]["comments"], [])

    def test_update_preserves_existing_fields(self):
        """Test that updating one field preserves other existing fields."""
        original_snippet = DB["commentThreads"]["thread1"]["snippet"].copy()
        original_comments = DB["commentThreads"]["thread1"]["comments"].copy()

        # Update only snippet
        result = update(thread_id="thread1", snippet={"channelId": "updated_channel"})

        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(
            DB["commentThreads"]["thread1"]["snippet"], {"channelId": "updated_channel"}
        )
        self.assertEqual(DB["commentThreads"]["thread1"]["comments"], original_comments)

    def test_update_multiple_threads(self):
        """Test updating multiple different threads."""
        # Update thread1
        result1 = update(thread_id="thread1", snippet={"channelId": "new_channel1"})

        # Update thread2
        result2 = update(thread_id="thread2", comments=["new_comment1", "new_comment2"])

        # Update thread3
        result3 = update(
            thread_id="thread3",
            snippet={"videoId": "new_video"},
            comments=["new_comment3"],
        )

        # Verify all updates were successful
        self.assertEqual(result1["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(result2["success"], "Thread ID: thread2 updated successfully.")
        self.assertEqual(result3["success"], "Thread ID: thread3 updated successfully.")

        # Verify the changes were applied correctly
        self.assertEqual(
            DB["commentThreads"]["thread1"]["snippet"]["channelId"], "new_channel1"
        )
        self.assertEqual(
            DB["commentThreads"]["thread2"]["comments"],
            ["new_comment1", "new_comment2"],
        )
        self.assertEqual(
            DB["commentThreads"]["thread3"]["snippet"]["videoId"], "new_video"
        )
        self.assertEqual(DB["commentThreads"]["thread3"]["comments"], ["new_comment3"])

    # ==================== VALIDATION ERROR TESTS ====================

    def test_update_empty_thread_id(self):
        """Test updating with empty thread ID."""
        result = update(thread_id="", snippet={"channelId": "channel1"})

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])
        self.assertIn("thread_id cannot be empty", result["error"])

    def test_update_whitespace_thread_id(self):
        """Test updating with whitespace-only thread ID."""
        result = update(thread_id="   ", snippet={"channelId": "channel1"})

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])
        self.assertIn("thread_id cannot be empty", result["error"])

    def test_update_no_parameters(self):
        """Test updating with no update parameters provided."""
        result = update(thread_id="thread1")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "No update parameters provided")

    def test_update_all_parameters_none(self):
        """Test updating with all parameters explicitly set to None."""
        result = update(thread_id="thread1", snippet=None, comments=None)

        self.assertIn("error", result)
        self.assertEqual(result["error"], "No update parameters provided")

    def test_update_nonexistent_thread_id(self):
        """Test updating a thread that doesn't exist."""
        result = update(
            thread_id="nonexistent_thread", snippet={"channelId": "channel1"}
        )

        self.assertIn("error", result)
        self.assertEqual(
            result["error"], "Thread ID: nonexistent_thread not found in the database."
        )

    def test_update_invalid_comments_type(self):
        """Test updating with invalid comments type (not a list)."""
        result = update(thread_id="thread1", comments="not_a_list")  # type: ignore

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])

    def test_update_invalid_comments_content(self):
        """Test updating with invalid comment IDs in comments list."""
        result = update(
            thread_id="thread1",
            comments=["valid_comment", 123, "another_valid"],  # type: ignore
        )

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])

    # ==================== EDGE CASES ====================

    def test_update_empty_snippet(self):
        """Test updating with empty snippet dictionary."""
        result = update(thread_id="thread1", snippet={})

        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(DB["commentThreads"]["thread1"]["snippet"], {})

    def test_update_snippet_with_none_values(self):
        """Test updating snippet with None values."""
        snippet_with_none = {"channelId": None, "videoId": None, "title": "Valid title"}

        result = update(thread_id="thread1", snippet=snippet_with_none)

        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertEqual(DB["commentThreads"]["thread1"]["snippet"], snippet_with_none)

    def test_update_returns_complete_thread_object(self):
        """Test that update returns the complete updated thread object."""
        new_snippet = {"channelId": "new_channel", "videoId": "new_video"}
        new_comments = ["new_comment1", "new_comment2"]

        result = update(thread_id="thread1", snippet=new_snippet, comments=new_comments)

        self.assertEqual(result["success"], "Thread ID: thread1 updated successfully.")
        self.assertIn("commentThread", result)

        returned_thread = result["commentThread"]
        self.assertEqual(returned_thread["id"], "thread1")
        self.assertEqual(returned_thread["snippet"], new_snippet)
        self.assertEqual(returned_thread["comments"], new_comments)

    # ==================== TYPE VALIDATION TESTS ====================

    def test_update_invalid_snippet_type(self):
        """Test updating with invalid snippet type (not a dict)."""
        result = update(thread_id="thread1", snippet="not_a_dict")  # type: ignore

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])
        self.assertIn("snippet must be a dictionary", result["error"])

    def test_update_invalid_thread_id_type(self):
        """Test updating with invalid thread ID type (not a string)."""
        result = update(
            thread_id=123, snippet={"channelId": "channel1"}  # type: ignore
        )

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])


    def test_update_invalid_part_type(self):
        """Test updating with invalid part type (not a string)."""
        self.assert_error_behavior(
            func_to_call=list_comments_thread,
            expected_exception_type=TypeError,
            expected_message="Parameter 'part' must be a string.",
            part=123
        )

if __name__ == "__main__":
    unittest.main()
