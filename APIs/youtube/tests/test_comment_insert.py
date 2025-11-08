import unittest
from unittest.mock import patch
from youtube.Comment import insert
from youtube.SimulationEngine.db import DB
from youtube.SimulationEngine.custom_errors import InvalidCommentInsertError
from common_utils.base_case import BaseTestCaseWithErrorHandler

from pydantic import ValidationError


class TestCommentInsert(BaseTestCaseWithErrorHandler):
    """Test cases for the Comment.insert function."""

    def setUp(self):
        """Reset the database before each test."""
        DB.clear()
        DB.update({
            "comments": {
                "existing_comment": {
                    "id": "existing_comment",
                    "snippet": {
                        "videoId": "video1",
                        "parentId": None,
                        "textDisplay": "Existing comment",
                        "authorDisplayName": "Test User",
                    },
                    "moderationStatus": "published",
                    "bannedAuthor": False,
                }
            }
        })

    # ==================== SUCCESSFUL INSERTION TESTS ====================

    def test_insert_basic_success(self):
        """Test successful insertion with minimal parameters."""
        result = insert(part="snippet")
        
        self.assertTrue(result["success"])
        self.assertIn("comment", result)
        self.assertIn("id", result["comment"])
        self.assertEqual(result["comment"]["snippet"], {})
        self.assertEqual(result["comment"]["moderationStatus"], "published")
        self.assertEqual(result["comment"]["bannedAuthor"], False)

    def test_insert_with_snippet_success(self):
        """Test successful insertion with snippet data."""
        snippet_data = {
            "videoId": "video123",
            "textDisplay": "Great video!",
            "authorDisplayName": "John Doe"
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertIn("comment", result)
        self.assertEqual(result["comment"]["snippet"], snippet_data)
        self.assertEqual(result["comment"]["moderationStatus"], "published")

    def test_insert_with_moderation_status_success(self):
        """Test successful insertion with different moderation status."""
        result = insert(part="snippet", moderation_status="heldForReview")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["moderationStatus"], "heldForReview")

    def test_insert_with_banned_author_success(self):
        """Test successful insertion with banned author."""
        result = insert(part="snippet", banned_author=True)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["bannedAuthor"], True)

    def test_insert_with_all_parameters_success(self):
        """Test successful insertion with all parameters."""
        snippet_data = {
            "videoId": "video456",
            "parentId": "parent123",
            "textDisplay": "This is a reply",
            "authorDisplayName": "Jane Smith"
        }
        result = insert(
            part="snippet,moderationStatus,bannedAuthor",
            snippet=snippet_data,
            moderation_status="rejected",
            banned_author=True
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)
        self.assertEqual(result["comment"]["moderationStatus"], "rejected")
        self.assertEqual(result["comment"]["bannedAuthor"], True)

    def test_insert_with_complex_snippet_success(self):
        """Test successful insertion with complex snippet containing extra fields."""
        snippet_data = {
            "videoId": "video789",
            "textDisplay": "Complex comment",
            "authorDisplayName": "Complex User",
            "customField": "custom_value",
            "nestedData": {"key": "value"},
            "listData": [1, 2, 3]
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    def test_insert_multiple_part_components_success(self):
        """Test successful insertion with multiple part components."""
        result = insert(part="id,snippet,moderationStatus")
        
        self.assertTrue(result["success"])
        self.assertIn("id", result["comment"])
        self.assertIn("snippet", result["comment"])
        self.assertIn("moderationStatus", result["comment"])

    def test_insert_database_initialization(self):
        """Test that function initializes database structure if needed."""
        DB.clear()  # Remove comments key entirely
        
        result = insert(part="snippet")
        
        self.assertTrue(result["success"])
        self.assertIn("comments", DB)
        self.assertIn(result["comment"]["id"], DB["comments"])

    def test_insert_generates_unique_ids(self):
        """Test that multiple insertions generate unique IDs."""
        result1 = insert(part="snippet")
        result2 = insert(part="snippet")
        
        self.assertTrue(result1["success"])
        self.assertTrue(result2["success"])
        self.assertNotEqual(result1["comment"]["id"], result2["comment"]["id"])

    def test_insert_stores_in_database(self):
        """Test that inserted comment is properly stored in database."""
        result = insert(part="snippet", snippet={"videoId": "test_video"})
        
        self.assertTrue(result["success"])
        comment_id = result["comment"]["id"]
        self.assertIn(comment_id, DB["comments"])
        self.assertEqual(DB["comments"][comment_id], result["comment"])

    # ==================== PART PARAMETER VALIDATION TESTS ====================

    def test_insert_part_empty_string(self):
        """Test that empty part parameter raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part="")
        self.assertIn("part parameter cannot be empty", str(context.exception))

    def test_insert_part_whitespace_only(self):
        """Test that whitespace-only part parameter raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part="   ")
        self.assertIn("part parameter cannot be empty", str(context.exception))

    def test_insert_part_invalid_type(self):
        """Test that non-string part parameter raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part=123)  # type: ignore
        self.assertIn("Input should be a valid string", str(context.exception))

    def test_insert_part_invalid_component(self):
        """Test that any non-empty part component is now valid."""
        result = insert(part="invalid_component")
        self.assertTrue(result["success"])

    def test_insert_part_mixed_valid_invalid(self):
        """Test that mixed part components are now all valid."""
        result = insert(part="snippet,invalid_component")
        self.assertTrue(result["success"])

    def test_insert_part_comma_separated_valid(self):
        """Test that comma-separated valid part components work."""
        result = insert(part="snippet,moderationStatus")
        
        self.assertTrue(result["success"])

    def test_insert_part_with_spaces(self):
        """Test that part parameter with spaces around commas works."""
        result = insert(part="snippet, moderationStatus , bannedAuthor")
        
        self.assertTrue(result["success"])

    def test_insert_part_empty_components(self):
        """Test that part parameter with empty components returns error."""
        result = insert(part="snippet,,moderationStatus")
        
        # Should still work as empty components are filtered out
        self.assertTrue(result["success"])

    def test_insert_part_only_commas(self):
        """Test that part parameter with only commas raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part=",,,")
        self.assertIn("part parameter must contain at least one component", str(context.exception))

    # ==================== MODERATION STATUS VALIDATION TESTS ====================

    def test_insert_moderation_status_valid_values(self):
        """Test all valid moderation status values."""
        valid_statuses = ["heldForReview", "published", "rejected"]
        
        for status in valid_statuses:
            result = insert(part="snippet", moderation_status=status)
            self.assertTrue(result["success"], f"Failed for status: {status}")
            self.assertEqual(result["comment"]["moderationStatus"], status)

    def test_insert_moderation_status_invalid_value(self):
        """Test that invalid moderation status raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part="snippet", moderation_status="invalid_status")
        self.assertIn("moderation_status must be one of", str(context.exception))

    def test_insert_moderation_status_invalid_type(self):
        """Test that non-string moderation status raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part="snippet", moderation_status=123)  # type: ignore
        self.assertIn("Input should be a valid string", str(context.exception))

    def test_insert_moderation_status_none(self):
        """Test that None moderation status raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part="snippet", moderation_status=None)  # type: ignore
        self.assertIn("Input should be a valid string", str(context.exception))

    # ==================== BANNED AUTHOR VALIDATION TESTS ====================

    def test_insert_banned_author_valid_values(self):
        """Test valid banned author values."""
        for banned_value in [True, False]:
            result = insert(part="snippet", banned_author=banned_value)
            self.assertTrue(result["success"], f"Failed for banned_author: {banned_value}")
            self.assertEqual(result["comment"]["bannedAuthor"], banned_value)

    def test_insert_banned_author_invalid_type(self):
        """Test that non-boolean banned author raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part="snippet", banned_author="true") # type: ignore
        self.assertIn("Input should be a valid boolean", str(context.exception))

    def test_insert_banned_author_none(self):
        """Test that None banned author raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part="snippet", banned_author=None)  # type: ignore
        self.assertIn("Input should be a valid boolean", str(context.exception))

    # ==================== SNIPPET VALIDATION TESTS ====================

    def test_insert_snippet_invalid_type(self):
        """Test that non-dict snippet raises InvalidCommentInsertError."""
        with self.assertRaises(InvalidCommentInsertError) as context:
            insert(part="snippet", snippet="not_a_dict")  # type: ignore
        self.assertIn("snippet must be a dictionary", str(context.exception))

    def test_insert_snippet_none(self):
        """Test that None snippet works (should default to empty dict)."""
        result = insert(part="snippet", snippet=None)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], {})

    def test_insert_snippet_empty_dict(self):
        """Test that empty dict snippet works."""
        result = insert(part="snippet", snippet={})
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], {})

    def test_insert_snippet_with_optional_fields(self):
        """Test snippet with optional fields."""
        snippet_data = {
            "videoId": "video123",
            "parentId": "parent456",
            "textDisplay": "Test comment",
            "authorDisplayName": "Test Author"
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    def test_insert_snippet_with_extra_fields(self):
        """Test snippet with extra fields (should be allowed)."""
        snippet_data = {
            "videoId": "video123",
            "customField": "custom_value",
            "extraData": {"nested": "value"}
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    # ==================== EDGE CASE TESTS ====================

    def test_insert_with_unicode_characters(self):
        """Test insertion with unicode characters in snippet."""
        snippet_data = {
            "textDisplay": "测试评论 🎥 emoji test",
            "authorDisplayName": "用户名"
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    def test_insert_with_very_long_strings(self):
        """Test insertion with very long strings."""
        long_text = "x" * 10000
        snippet_data = {
            "textDisplay": long_text,
            "authorDisplayName": "Long Name " + "x" * 1000
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    def test_insert_with_special_characters(self):
        """Test insertion with special characters."""
        snippet_data = {
            "textDisplay": "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "authorDisplayName": "User@domain.com"
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    def test_insert_with_numeric_values_in_snippet(self):
        """Test insertion with numeric values in snippet."""
        snippet_data = {
            "videoId": "video123",
            "likeCount": 42,
            "timestamp": 1234567890,
            "rating": 4.5
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    def test_insert_with_boolean_values_in_snippet(self):
        """Test insertion with boolean values in snippet."""
        snippet_data = {
            "videoId": "video123",
            "isReply": True,
            "isEdited": False,
            "canReply": True
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    def test_insert_with_list_values_in_snippet(self):
        """Test insertion with list values in snippet."""
        snippet_data = {
            "videoId": "video123",
            "tags": ["funny", "educational", "tutorial"],
            "mentions": ["@user1", "@user2"]
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    def test_insert_with_nested_dict_in_snippet(self):
        """Test insertion with nested dictionary in snippet."""
        snippet_data = {
            "videoId": "video123",
            "author": {
                "name": "John Doe",
                "avatar": "https://example.com/avatar.jpg",
                "verified": True
            },
            "metadata": {
                "createdAt": "2024-01-01T00:00:00Z",
                "device": "mobile"
            }
        }
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["comment"]["snippet"], snippet_data)

    # ==================== MULTIPLE PARAMETER COMBINATION TESTS ====================

    def test_insert_all_parameters_combination(self):
        """Test all possible parameter combinations."""
        test_cases = [
            {"part": "snippet"},
            {"part": "snippet", "moderation_status": "heldForReview"},
            {"part": "snippet", "banned_author": True},
            {"part": "snippet", "snippet": {"videoId": "test"}},
            {"part": "snippet,moderationStatus", "moderation_status": "rejected"},
            {"part": "snippet,bannedAuthor", "banned_author": True},
            {"part": "id,snippet,moderationStatus,bannedAuthor", "moderation_status": "published", "banned_author": False},
        ]
        
        for i, params in enumerate(test_cases):
            result = insert(**params)
            self.assertTrue(result["success"], f"Failed for test case {i}: {params}")

    # ==================== PERFORMANCE AND STRESS TESTS ====================

    def test_insert_multiple_comments_performance(self):
        """Test inserting multiple comments for performance."""
        results = []
        for i in range(100):
            result = insert(
                part="snippet",
                snippet={"videoId": f"video{i}", "textDisplay": f"Comment {i}"}
            )
            results.append(result)
        
        # All insertions should succeed
        for i, result in enumerate(results):
            self.assertTrue(result["success"], f"Failed for comment {i}")
        
        # All should have unique IDs
        ids = [result["comment"]["id"] for result in results]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate IDs found")

    def test_insert_preserves_existing_comments(self):
        """Test that new insertions don't affect existing comments."""
        initial_comment_count = len(DB["comments"])
        existing_comment = DB["comments"]["existing_comment"].copy()
        
        result = insert(part="snippet", snippet={"videoId": "new_video"})
        
        self.assertTrue(result["success"])
        self.assertEqual(len(DB["comments"]), initial_comment_count + 1)
        self.assertEqual(DB["comments"]["existing_comment"], existing_comment)


if __name__ == "__main__":
    unittest.main() 