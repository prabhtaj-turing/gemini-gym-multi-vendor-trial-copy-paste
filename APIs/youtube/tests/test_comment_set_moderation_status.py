import unittest
from unittest.mock import patch
from youtube.SimulationEngine.db import DB
from youtube.Comment import set_moderation_status
from youtube.SimulationEngine.custom_errors import (
    InvalidCommentIdError,
    InvalidModerationStatusError,
    InvalidBanAuthorError,
)
from common_utils.base_case import BaseTestCaseWithErrorHandler



class TestCommentSetModerationStatus(BaseTestCaseWithErrorHandler):
    """Test cases for the Comment.set_moderation_status function."""

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

    # ==================== SUCCESSFUL MODERATION TESTS ====================

    def test_set_moderation_status_to_published(self):
        """Test setting moderation status to published."""
        result = set_moderation_status("comment1", "published")

        self.assertTrue(result["success"])
        self.assertIn("comment", result)
        self.assertEqual(result["comment"]["id"], "comment1")
        self.assertEqual(result["comment"]["moderationStatus"], "published")
        self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], "published")

    def test_set_moderation_status_to_held_for_review(self):
        """Test setting moderation status to heldForReview."""
        result = set_moderation_status("comment1", "heldForReview")

        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "heldForReview")
        self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], "heldForReview")

    def test_set_moderation_status_to_rejected(self):
        """Test setting moderation status to rejected."""
        result = set_moderation_status("comment1", "rejected")

        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "rejected")
        self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], "rejected")

    def test_set_moderation_status_with_ban_author_false(self):
        """Test setting moderation status with ban_author=False."""
        result = set_moderation_status("comment1", "rejected", ban_author=False)

        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "rejected")
        self.assertEqual(result["comment"]["bannedAuthor"], False)
        self.assertEqual(DB["comments"]["comment1"]["bannedAuthor"], False)

    def test_set_moderation_status_with_ban_author_true_and_rejected(self):
        """Test setting moderation status to rejected with ban_author=True."""
        result = set_moderation_status("comment1", "rejected", ban_author=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "rejected")
        self.assertEqual(result["comment"]["bannedAuthor"], True)
        self.assertEqual(DB["comments"]["comment1"]["bannedAuthor"], True)

    def test_set_moderation_status_with_ban_author_true_and_published(self):
        """Test setting moderation status to published with ban_author=True (should not ban)."""
        result = set_moderation_status("comment1", "published", ban_author=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "published")
        # Author should not be banned because status is not "rejected"
        self.assertEqual(result["comment"]["bannedAuthor"], False)
        self.assertEqual(DB["comments"]["comment1"]["bannedAuthor"], False)

    def test_set_moderation_status_preserves_other_fields(self):
        """Test that setting moderation status preserves other comment fields."""
        original_snippet = DB["comments"]["comment1"]["snippet"].copy()
        
        result = set_moderation_status("comment1", "heldForReview")

        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], original_snippet)
        self.assertEqual(DB["comments"]["comment1"]["snippet"], original_snippet)

    def test_set_moderation_status_multiple_comments(self):
        """Test setting moderation status on multiple different comments."""
        # Set comment1 to heldForReview
        result1 = set_moderation_status("comment1", "heldForReview")
        self.assertTrue(result1["success"])
        self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], "heldForReview")

        # Set comment2 to rejected with ban
        result2 = set_moderation_status("comment2", "rejected", ban_author=True)
        self.assertTrue(result2["success"])
        self.assertEqual(DB["comments"]["comment2"]["moderationStatus"], "rejected")
        self.assertEqual(DB["comments"]["comment2"]["bannedAuthor"], True)

        # Set comment3 to published
        result3 = set_moderation_status("comment3", "published")
        self.assertTrue(result3["success"])
        self.assertEqual(DB["comments"]["comment3"]["moderationStatus"], "published")

    # ==================== VALIDATION ERROR TESTS ====================

    def test_set_moderation_status_invalid_comment_id_type(self):
        """Test that non-string comment_id raises InvalidCommentIdError."""
        self.assert_error_behavior(
            func_to_call=set_moderation_status,
            expected_exception_type=InvalidCommentIdError,
            expected_message="comment_id must be a non-empty string",
            comment_id=123,  # type: ignore
            moderation_status="published"
        )

    def test_set_moderation_status_empty_comment_id(self):
        """Test that empty comment_id raises InvalidCommentIdError."""
        self.assert_error_behavior(
            func_to_call=set_moderation_status,
            expected_exception_type=InvalidCommentIdError,
            expected_message="comment_id must be a non-empty string",
            comment_id="",
            moderation_status="published"
        )

    def test_set_moderation_status_whitespace_comment_id(self):
        """Test that whitespace-only comment_id raises InvalidCommentIdError."""
        self.assert_error_behavior(
            func_to_call=set_moderation_status,
            expected_exception_type=InvalidCommentIdError,
            expected_message="comment_id must be a non-empty string",
            comment_id="   ",
            moderation_status="published"
        )

    def test_set_moderation_status_invalid_moderation_status_type(self):
        """Test that non-string moderation_status raises InvalidModerationStatusError."""
        self.assert_error_behavior(
            func_to_call=set_moderation_status,
            expected_exception_type=InvalidModerationStatusError,
            expected_message="moderation_status must be one of 'heldForReview', 'published', 'rejected'",
            comment_id="comment1",
            moderation_status=123  # type: ignore
        )

    def test_set_moderation_status_invalid_moderation_status_value(self):
        """Test that invalid moderation_status value raises InvalidModerationStatusError."""
        self.assert_error_behavior(
            func_to_call=set_moderation_status,
            expected_exception_type=InvalidModerationStatusError,
            expected_message="moderation_status must be one of 'heldForReview', 'published', 'rejected'",
            comment_id="comment1",
            moderation_status="invalid_status"
        )

    def test_set_moderation_status_invalid_ban_author_type(self):
        """Test that non-boolean ban_author raises InvalidBanAuthorError."""
        self.assert_error_behavior(
            func_to_call=set_moderation_status,
            expected_exception_type=InvalidBanAuthorError,
            expected_message="ban_author must be a boolean or None",
            comment_id="comment1",
            moderation_status="published",
            ban_author="true"  # type: ignore
        )

    def test_set_moderation_status_invalid_ban_author_string(self):
        """Test that string ban_author raises InvalidBanAuthorError."""
        self.assert_error_behavior(
            func_to_call=set_moderation_status,
            expected_exception_type=InvalidBanAuthorError,
            expected_message="ban_author must be a boolean or None",
            comment_id="comment1",
            moderation_status="published",
            ban_author="false"  # type: ignore
        )

    def test_set_moderation_status_invalid_ban_author_number(self):
        """Test that numeric ban_author raises InvalidBanAuthorError."""
        self.assert_error_behavior(
            func_to_call=set_moderation_status,
            expected_exception_type=InvalidBanAuthorError,
            expected_message="ban_author must be a boolean or None",
            comment_id="comment1",
            moderation_status="published",
            ban_author=1  # type: ignore
        )

    # ==================== COMMENT NOT FOUND TESTS ====================

    def test_set_moderation_status_nonexistent_comment(self):
        """Test that nonexistent comment_id returns error message."""
        result = set_moderation_status("nonexistent_comment", "published")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Comment not found")

    def test_set_moderation_status_comment_not_in_db(self):
        """Test behavior when comment is not in database."""
        # Clear the comments from DB
        DB["comments"] = {}
        
        result = set_moderation_status("comment1", "published")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Comment not found")

    def test_set_moderation_status_missing_comments_key(self):
        """Test behavior when comments key is missing from DB."""
        # Remove comments key from DB
        if "comments" in DB:
            del DB["comments"]
        
        result = set_moderation_status("comment1", "published")

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Comment not found")

    # ==================== EDGE CASES ====================

    def test_set_moderation_status_all_valid_statuses(self):
        """Test all valid moderation status values."""
        valid_statuses = ["heldForReview", "published", "rejected"]
        
        for status in valid_statuses:
            result = set_moderation_status("comment1", status)
            self.assertTrue(result["success"])
            self.assertEqual(result["comment"]["moderationStatus"], status)
            self.assertEqual(DB["comments"]["comment1"]["moderationStatus"], status)

    def test_set_moderation_status_case_sensitivity(self):
        """Test that moderation status is case sensitive."""
        # Test with different case variations
        invalid_cases = ["Published", "PUBLISHED", "heldforReview", "REJECTED"]
        
        for invalid_status in invalid_cases:
            self.assert_error_behavior(
                func_to_call=set_moderation_status,
                expected_exception_type=InvalidModerationStatusError,
                expected_message="moderation_status must be one of 'heldForReview', 'published', 'rejected'",
                comment_id="comment1",
                moderation_status=invalid_status
            )

    def test_set_moderation_status_with_special_comment_ids(self):
        """Test with special characters in comment IDs."""
        # Add a comment with special characters
        special_comment_id = "comment_with-special.chars_123"
        DB["comments"][special_comment_id] = {
            "id": special_comment_id,
            "snippet": {"videoId": "video1"},
            "moderationStatus": "published",
            "bannedAuthor": False,
        }
        
        result = set_moderation_status(special_comment_id, "heldForReview")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "heldForReview")

    def test_set_moderation_status_returns_complete_comment(self):
        """Test that the function returns the complete comment object."""
        result = set_moderation_status("comment1", "heldForReview", ban_author=True)
        
        self.assertTrue(result["success"])
        self.assertIn("comment", result)
        
        comment = result["comment"]
        self.assertEqual(comment["id"], "comment1")
        self.assertIn("snippet", comment)
        self.assertEqual(comment["moderationStatus"], "heldForReview")
        self.assertEqual(comment["bannedAuthor"], False)  # Should not be banned for heldForReview

    # ==================== PARAMETER COMBINATION TESTS ====================

    def test_set_moderation_status_all_parameters_valid(self):
        """Test with all parameters provided and valid."""
        result = set_moderation_status(
            comment_id="comment1",
            moderation_status="rejected",
            ban_author=True
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "rejected")
        self.assertEqual(result["comment"]["bannedAuthor"], True)

    def test_set_moderation_status_default_ban_author(self):
        """Test that ban_author defaults to None when not provided."""
        result = set_moderation_status("comment1", "rejected")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "rejected")
        # When ban_author is None (default), bannedAuthor should remain as it was originally
        self.assertEqual(result["comment"]["bannedAuthor"], False)

    def test_set_moderation_status_explicit_none_ban_author(self):
        """Test that explicitly passing None for ban_author works correctly."""
        result = set_moderation_status("comment1", "rejected", ban_author=None)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "rejected")
        # When ban_author is explicitly None, bannedAuthor should remain as it was originally
        self.assertEqual(result["comment"]["bannedAuthor"], False)

    def test_set_moderation_status_ban_author_only_effective_with_rejected(self):
        """Test that ban_author only takes effect when moderation_status is rejected."""
        # Test with published status
        result = set_moderation_status("comment1", "published", ban_author=True)
        self.assertEqual(result["comment"]["bannedAuthor"], False)
        
        # Test with heldForReview status
        result = set_moderation_status("comment1", "heldForReview", ban_author=True)
        self.assertEqual(result["comment"]["bannedAuthor"], False)
        
        # Test with rejected status
        result = set_moderation_status("comment1", "rejected", ban_author=True)
        self.assertEqual(result["comment"]["bannedAuthor"], True)


if __name__ == "__main__":
    unittest.main() 