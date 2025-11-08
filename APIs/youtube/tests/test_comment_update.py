import unittest
from unittest.mock import patch
from pydantic import ValidationError

from youtube.SimulationEngine.db import DB
from youtube.Comment import update, mark_as_spam
from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube.SimulationEngine.custom_errors import InvalidCommentIdError



class TestCommentUpdate(BaseTestCaseWithErrorHandler):
    """Test cases for the Comment.update function with Pydantic validation."""

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

    # ==================== SUCCESSFUL UPDATE TESTS ====================

    def test_update_snippet_only(self):
        """Test updating only the snippet field."""
        new_snippet = {
            "videoId": "video2",
            "parentId": "comment1",
            "textDisplay": "Updated comment text",
            "authorDisplayName": "Updated Author",
        }

        result = update(comment_id="comment1", snippet=new_snippet)

        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(DB["comments"]["comment1"]["snippet"], new_snippet)
        # Ensure other fields remain unchanged
        self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], "published")
        self.assertEqual(DB["comments"]["comment1"]["bannedAuthor"], False)

    def test_update_moderation_status_only(self):
        """Test updating only the moderation status."""
        result = update(comment_id="comment1", moderation_status="heldForReview")

        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(
            DB["comments"]["comment1"]["moderationStatus"], "heldForReview"
        )
        # Ensure other fields remain unchanged
        self.assertEqual(DB["comments"]["comment1"]["snippet"]["videoId"], "video1")
        self.assertEqual(DB["comments"]["comment1"]["bannedAuthor"], False)

    def test_update_banned_author_only(self):
        """Test updating only the banned author status."""
        result = update(comment_id="comment1", banned_author=True)

        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(DB["comments"]["comment1"]["bannedAuthor"], True)
        # Ensure other fields remain unchanged
        self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], "published")
        self.assertEqual(DB["comments"]["comment1"]["snippet"]["videoId"], "video1")

    def test_update_all_fields(self):
        """Test updating all fields simultaneously."""
        new_snippet = {
            "videoId": "video3",
            "parentId": "comment2",
            "textDisplay": "Completely updated comment",
            "authorDisplayName": "New Author",
        }

        result = update(
            comment_id="comment2",
            snippet=new_snippet,
            moderation_status="rejected",
            banned_author=True,
        )

        self.assertEqual(
            result["success"], "Comment ID: comment2 updated successfully."
        )
        self.assertEqual(DB["comments"]["comment2"]["snippet"], new_snippet)
        self.assertEqual(DB["comments"]["comment2"]["moderationStatus"], "rejected")
        self.assertEqual(DB["comments"]["comment2"]["bannedAuthor"], True)

    def test_update_snippet_with_additional_fields(self):
        """Test updating snippet with additional fields beyond the standard ones."""
        new_snippet = {
            "videoId": "video1",
            "parentId": None,
            "textDisplay": "Updated text",
            "authorDisplayName": "Updated Author",
            "likeCount": 100,
            "publishedAt": "2024-01-01T00:00:00Z",
            "customField": "custom_value",
        }

        result = update(comment_id="comment1", snippet=new_snippet)

        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(DB["comments"]["comment1"]["snippet"], new_snippet)
        self.assertEqual(
            DB["comments"]["comment1"]["snippet"]["customField"], "custom_value"
        )

    def test_update_moderation_status_all_valid_values(self):
        """Test updating moderation status with all valid values."""
        valid_statuses = ["heldForReview", "published", "rejected"]

        for status in valid_statuses:
            result = update(comment_id="comment1", moderation_status=status)

            self.assertEqual(
                result["success"], "Comment ID: comment1 updated successfully."
            )
            self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], status)

    def test_update_banned_author_true_false(self):
        """Test updating banned author with both True and False values."""
        # Test setting to True
        result = update(comment_id="comment1", banned_author=True)
        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(DB["comments"]["comment1"]["bannedAuthor"], True)

        # Test setting to False
        result = update(comment_id="comment1", banned_author=False)
        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(DB["comments"]["comment1"]["bannedAuthor"], False)

    # ==================== VALIDATION ERROR TESTS ====================

    def test_update_empty_comment_id(self):
        """Test updating with empty comment ID."""
        result = update(comment_id="", snippet={"videoId": "video1"})

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])
        self.assertIn("comment_id cannot be empty", result["error"])

    def test_update_whitespace_comment_id(self):
        """Test updating with whitespace-only comment ID."""
        result = update(comment_id="   ", snippet={"videoId": "video1"})

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])
        self.assertIn("comment_id cannot be empty", result["error"])

    def test_update_invalid_moderation_status(self):
        """Test updating with invalid moderation status."""
        result = update(comment_id="comment1", moderation_status="invalid_status")

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])
        self.assertIn("moderation_status must be one of", result["error"])

    def test_update_no_parameters(self):
        """Test updating with no update parameters provided."""
        result = update(comment_id="comment1")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "No update parameters provided")

    def test_update_all_parameters_none(self):
        """Test updating with all parameters explicitly set to None."""
        result = update(
            comment_id="comment1",
            snippet=None,
            moderation_status=None,
            banned_author=None,
        )

        self.assertIn("error", result)
        self.assertEqual(result["error"], "No update parameters provided")

    def test_update_nonexistent_comment_id(self):
        """Test updating a comment that doesn't exist."""
        result = update(comment_id="nonexistent_comment", snippet={"videoId": "video1"})

        self.assertIn("error", result)
        self.assertEqual(
            result["error"],
            "Comment ID: nonexistent_comment not found in the database.",
        )

    # ==================== EDGE CASES ====================

    def test_update_empty_snippet(self):
        """Test updating with empty snippet dictionary."""
        result = update(comment_id="comment1", snippet={})

        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(DB["comments"]["comment1"]["snippet"], {})

    def test_update_snippet_with_none_values(self):
        """Test updating snippet with None values."""
        snippet_with_none = {
            "videoId": None,
            "parentId": None,
            "textDisplay": "Valid text",
        }

        result = update(comment_id="comment1", snippet=snippet_with_none)

        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(DB["comments"]["comment1"]["snippet"], snippet_with_none)

    def test_update_preserves_existing_fields(self):
        """Test that updating one field preserves other existing fields."""
        original_snippet = DB["comments"]["comment1"]["snippet"].copy()
        original_moderation_status = DB["comments"]["comment1"]["moderationStatus"]
        original_banned_author = DB["comments"]["comment1"]["bannedAuthor"]

        # Update only snippet
        result = update(comment_id="comment1", snippet={"videoId": "updated_video"})

        self.assertEqual(
            result["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(
            DB["comments"]["comment1"]["snippet"], {"videoId": "updated_video"}
        )
        self.assertEqual(
            DB["comments"]["comment1"]["moderationStatus"], original_moderation_status
        )
        self.assertEqual(
            DB["comments"]["comment1"]["bannedAuthor"], original_banned_author
        )

    def test_update_multiple_comments(self):
        """Test updating multiple different comments."""
        # Update comment1
        result1 = update(comment_id="comment1", moderation_status="heldForReview")

        # Update comment2
        result2 = update(comment_id="comment2", banned_author=True)

        # Update comment3
        result3 = update(
            comment_id="comment3",
            snippet={"videoId": "video3"},
            moderation_status="published",
            banned_author=False,
        )

        # Verify all updates were successful
        self.assertEqual(
            result1["success"], "Comment ID: comment1 updated successfully."
        )
        self.assertEqual(
            result2["success"], "Comment ID: comment2 updated successfully."
        )
        self.assertEqual(
            result3["success"], "Comment ID: comment3 updated successfully."
        )

        # Verify the changes were applied correctly
        self.assertEqual(
            DB["comments"]["comment1"]["moderationStatus"], "heldForReview"
        )
        self.assertEqual(DB["comments"]["comment2"]["bannedAuthor"], True)
        self.assertEqual(DB["comments"]["comment3"]["snippet"]["videoId"], "video3")
        self.assertEqual(DB["comments"]["comment3"]["moderationStatus"], "published")
        self.assertEqual(DB["comments"]["comment3"]["bannedAuthor"], False)

    # ==================== TYPE VALIDATION TESTS ====================

    def test_update_invalid_snippet_type(self):
        """Test updating with invalid snippet type (not a dict)."""
        result = update(comment_id="comment1", snippet="not_a_dict")  # type: ignore

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])

    def test_update_invalid_moderation_status_type(self):
        """Test updating with invalid moderation status type (not a string)."""
        result = update(comment_id="comment1", moderation_status=123)  # type: ignore

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])

    def test_update_invalid_banned_author_type(self):
        """Test updating with invalid banned author type (not a boolean)."""
        result = update(comment_id="comment1", banned_author="not_a_boolean")  # type: ignore

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])

    def test_update_invalid_comment_id_type(self):
        """Test updating with invalid comment ID type (not a string)."""
        result = update(comment_id=123, snippet={"videoId": "video1"})  # type: ignore

        self.assertIn("error", result)
        self.assertIn("Validation error", result["error"])

    def test_mark_as_spam_invalid_comment_id_type(self):
        """Test mark_as_spam with invalid comment ID type (not a string)."""
        self.assert_error_behavior(
            mark_as_spam,
            TypeError,
            "comment_id must be a non-empty string",
            comment_id=123,
        )
    
    def test_mark_as_spam_invalid_comment_id_value_empty(self):
        """Test mark_as_spam with invalid comment ID value (empty string)."""
        self.assert_error_behavior(
            mark_as_spam,
            ValueError,
            "comment_id cannot be empty or contain only whitespace",
            comment_id="",
        )
    
    def test_mark_as_spam_invalid_comment_id_value_whitespace(self):
        """Test mark_as_spam with invalid comment ID value (whitespace)."""
        self.assert_error_behavior(
            mark_as_spam,
            ValueError,
            "comment_id cannot be empty or contain only whitespace",
            comment_id="    ",
        )

    def test_mark_as_spam_invalid_comment_id_value_none(self):
        """Test mark_as_spam with invalid comment ID value (None)."""
        self.assert_error_behavior(
            mark_as_spam,
            ValueError,
            "comment_id is required",
            comment_id=None,
        )

    def test_mark_as_spam_invalid_comment_id_value_not_found(self):
        """Test mark_as_spam with invalid comment ID value (not found in the database)."""
        self.assert_error_behavior(
            mark_as_spam,
            InvalidCommentIdError,
            "Comment not found in the database.",
            comment_id="comment4",
        )

    def test_mark_as_spam_success(self):
        """Test mark_as_spam with valid comment ID."""
        result = mark_as_spam(comment_id="comment1")
        self.assertEqual(result["success"], True)
        self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], "heldForReview")


if __name__ == "__main__":
    unittest.main()
