import unittest
from unittest.mock import patch
from youtube.Comment import delete
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.custom_errors import InvalidCommentIdError
from common_utils.base_case import BaseTestCaseWithErrorHandler



class TestCommentDelete(BaseTestCaseWithErrorHandler):
    """Test cases for the Comment.delete function."""

    def setUp(self):
        """Reset the database before each test."""
        DB.clear()
        DB.update(
            {
                "comments": {
                    "comment1": {
                        "id": "comment1",
                        "snippet": {
                            "videoId": "video1",
                            "parentId": None,
                            "textDisplay": "Great video!",
                            "authorDisplayName": "John Doe",
                        },
                        "moderationStatus": "published",
                        "bannedAuthor": False,
                    },
                    "comment2": {
                        "id": "comment2",
                        "snippet": {
                            "videoId": "video1",
                            "parentId": "comment1",
                            "textDisplay": "Thanks for sharing!",
                            "authorDisplayName": "Jane Smith",
                        },
                        "moderationStatus": "heldForReview",
                        "bannedAuthor": False,
                    },
                    "comment3": {
                        "id": "comment3",
                        "snippet": {
                            "videoId": "video2",
                            "parentId": None,
                            "textDisplay": "This is spam",
                            "authorDisplayName": "Spammer",
                        },
                        "moderationStatus": "rejected",
                        "bannedAuthor": True,
                    },
                }
            }
        )

    def test_delete_existing_comment_success(self):
        """Test successful deletion of an existing comment."""
        result = delete(comment_id="comment1")
        
        self.assertEqual(result["success"], True)
        self.assertNotIn("comment1", DB["comments"])
        self.assertEqual(len(DB["comments"]), 2)

    def test_delete_nonexistent_comment(self):
        """Test deletion of a non-existent comment returns error."""
        result = delete(comment_id="nonexistent_comment")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Comment not found")
        # Ensure no comments were deleted
        self.assertEqual(len(DB["comments"]), 3)

    def test_delete_comment_invalid_type(self):
        """Test that providing non-string comment_id raises InvalidCommentIdError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidCommentIdError,
            expected_message="Comment ID must be a string.",
            comment_id=123
        )

    def test_delete_comment_empty_string(self):
        """Test that providing empty string comment_id raises InvalidCommentIdError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidCommentIdError,
            expected_message="Comment ID cannot be empty or contain only whitespace.",
            comment_id=""
        )

    def test_delete_comment_whitespace_only(self):
        """Test that providing whitespace-only comment_id raises InvalidCommentIdError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidCommentIdError,
            expected_message="Comment ID cannot be empty or contain only whitespace.",
            comment_id="   "
        )

    def test_delete_comment_none_value(self):
        """Test that providing None as comment_id raises InvalidCommentIdError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=InvalidCommentIdError,
            expected_message="Comment ID must be a string.",
            comment_id=None
        )

    def test_delete_multiple_comments_sequentially(self):
        """Test deleting multiple comments one by one."""
        # Delete first comment
        result1 = delete(comment_id="comment1")
        self.assertEqual(result1["success"], True)
        self.assertNotIn("comment1", DB["comments"])
        self.assertEqual(len(DB["comments"]), 2)

        # Delete second comment
        result2 = delete(comment_id="comment2")
        self.assertEqual(result2["success"], True)
        self.assertNotIn("comment2", DB["comments"])
        self.assertEqual(len(DB["comments"]), 1)

        # Verify remaining comment
        self.assertIn("comment3", DB["comments"])

    def test_delete_comment_preserves_other_comments(self):
        """Test that deleting one comment doesn't affect others."""
        original_comment2 = DB["comments"]["comment2"].copy()
        original_comment3 = DB["comments"]["comment3"].copy()
        
        result = delete(comment_id="comment1")
        
        self.assertEqual(result["success"], True)
        self.assertNotIn("comment1", DB["comments"])
        # Verify other comments remain unchanged
        self.assertEqual(DB["comments"]["comment2"], original_comment2)
        self.assertEqual(DB["comments"]["comment3"], original_comment3)

    def test_delete_comment_with_special_characters(self):
        """Test deleting a comment with special characters in ID."""
        # Add a comment with special characters in ID
        special_id = "comment_with-special.chars@123"
        DB["comments"][special_id] = {
            "id": special_id,
            "snippet": {"textDisplay": "Special comment"},
            "moderationStatus": "published",
            "bannedAuthor": False,
        }
        
        result = delete(comment_id=special_id)
        
        self.assertEqual(result["success"], True)
        self.assertNotIn(special_id, DB["comments"])

    def test_delete_comment_database_consistency(self):
        """Test that database remains consistent after deletion."""
        initial_count = len(DB["comments"])
        
        # Delete existing comment
        result = delete(comment_id="comment2")
        self.assertEqual(result["success"], True)
        self.assertEqual(len(DB["comments"]), initial_count - 1)
        
        # Try to delete the same comment again
        result = delete(comment_id="comment2")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Comment not found")
        # Count should remain the same
        self.assertEqual(len(DB["comments"]), initial_count - 1)


if __name__ == "__main__":
    unittest.main() 