import unittest
from typing import Dict, Any

from instagram.SimulationEngine.custom_errors import InvalidMediaIDError, MediaNotFoundError
from instagram.Media import delete_media
from instagram.SimulationEngine.db import DB

from common_utils.base_case import BaseTestCaseWithErrorHandler # Required for type hinting in tests if necessary


delete_media_post = delete_media


class TestDeleteMedia(BaseTestCaseWithErrorHandler):
    """Test suite for the delete_media_post function."""

    def setUp(self):
        """Reset DB state before each test."""
        DB["media"] = {
            "existing_id_123": {"title": "Old Post", "content": "Some content"},
            "another_id_456": {"title": "Another Post", "content": "More content"}
        }

    def test_successful_deletion(self):
        """Test successful deletion of an existing media post."""
        media_id_to_delete = "existing_id_123"
        result = delete_media_post(media_id=media_id_to_delete)
        self.assertEqual(result, {"success": True})
        self.assertNotIn(media_id_to_delete, DB["media"])
        self.assertIn("another_id_456", DB["media"]) # Ensure other items are not affected

    def test_delete_non_existent_media(self):
        """Test attempting to delete a media post that does not exist."""
        non_existent_id = "non_existent_id_789"
        original_media_count = len(DB["media"])
        self.assert_error_behavior(
            func_to_call=delete_media_post,
            expected_exception_type=MediaNotFoundError,
            expected_message="Media with ID 'non_existent_id_789' not found.",
            media_id=non_existent_id
        )
        self.assertEqual(len(DB["media"]), original_media_count) # Ensure DB state is unchanged

    # Basic validation tests
    def test_invalid_media_id_type_integer(self):
        """Test that TypeError is raised if media_id is an integer."""
        self.assert_error_behavior(
            func_to_call=delete_media_post,
            expected_exception_type=TypeError,
            expected_message="Field media_id must be a string.",
            media_id=123
        )

    def test_invalid_media_id_type_list(self):
        """Test that TypeError is raised if media_id is a list."""
        self.assert_error_behavior(
            func_to_call=delete_media_post,
            expected_exception_type=TypeError,
            expected_message="Field media_id must be a string.",
            media_id=["id123"]
        )

    # Edge case tests for non-dictionary arguments
    def test_invalid_media_id_type_none(self):
        """Test that TypeError is raised if media_id is None."""
        self.assert_error_behavior(
            func_to_call=delete_media_post,
            expected_exception_type=TypeError,
            expected_message="Field media_id must be a string.",
            media_id=None
        )

    def test_empty_media_id_string(self):
        """Test that InvalidMediaIDError is raised if media_id is an empty string."""
        self.assert_error_behavior(
            func_to_call=delete_media_post,
            expected_exception_type=InvalidMediaIDError,
            expected_message="Field media_id cannot be empty.",
            media_id=""
        )

    # Pydantic model validation tests are not applicable as there are no dictionary inputs.

    # Error handling tests (covered by type and value validation tests above)

    def test_media_id_with_special_chars(self):
        """Test deletion with a media_id containing special characters (if valid)."""
        special_id = "id-@!#$-_123"
        DB["media"][special_id] = {"data": "special data"}
        result = delete_media_post(media_id=special_id)
        self.assertEqual(result, {"success": True})
        self.assertNotIn(special_id, DB["media"])

    def test_case_sensitivity_of_media_id(self):
        """Test if media_id deletion is case-sensitive (assuming it is)."""
        # Add a specific cased ID
        DB["media"]["CaseSensitiveID"] = {"data": "case sensitive data"}
        
        # Try deleting with different case
        self.assert_error_behavior(
            func_to_call=delete_media_post,
            expected_exception_type=MediaNotFoundError,
            expected_message="Media with ID 'casesensitiveid' not found.",
            media_id="casesensitiveid"
        )

        # Delete with correct case
        result = delete_media_post(media_id="CaseSensitiveID")
        self.assertEqual(result, {"success": True})
        self.assertNotIn("CaseSensitiveID", DB["media"])