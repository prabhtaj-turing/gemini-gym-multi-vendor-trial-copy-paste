# instagram/tests/test_media.py

import unittest
import datetime
from instagram.SimulationEngine.custom_errors import UserNotFoundError, InvalidMediaIDError
from pydantic import ValidationError
from instagram import User, Media
import instagram as InstagramAPI
from .test_common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestMediaAPI(BaseTestCaseWithErrorHandler):
    """Test suite for the Instagram API Media functionality."""

    def setUp(self):
        """
        Set up method called before each test.
        Resets the global DB to ensure a clean state for every test.
        """
        reset_db()

    def test_create_media(self):
        """Test creating media for an existing user."""
        user_id = "201"
        User.create_user(user_id, "Media Maker", "mediamaker")
        media = Media.create_media(
            user_id, "http://example.com/image1.jpg", caption="My first pic"
        )
        self.assertNotIn("error", media)
        self.assertEqual(media["user_id"], user_id)
        self.assertEqual(media["caption"], "My first pic")
        self.assertIn(media["id"], InstagramAPI.DB["media"])

    def test_media_timestamp(self):
        """Test that media creation includes a timestamp field."""
        user_id = "201"
        User.create_user(user_id, "Media Maker", "mediamaker")

        # Create media and check timestamp
        media = Media.create_media(user_id, "http://example.com/image1.jpg")
        self.assertIn("timestamp", media)
        self.assertIsInstance(media["timestamp"], str)

        # Verify timestamp is in ISO format
        try:
            # This will raise ValueError if not in ISO format
            datetime.datetime.fromisoformat(media["timestamp"])
        except ValueError:
            self.fail("Timestamp is not in ISO format")

        # Verify timestamp is stored in DB
        self.assertIn("timestamp", InstagramAPI.DB["media"][media["id"]])
        self.assertEqual(
            InstagramAPI.DB["media"][media["id"]]["timestamp"], media["timestamp"]
        )

        # Verify timestamp is included in list_media results
        media_list = Media.list_media()
        media_from_list = next(m for m in media_list if m["id"] == media["id"])
        self.assertIn("timestamp", media_from_list)
        self.assertEqual(media_from_list["timestamp"], media["timestamp"])
    
    def test_create_media_validation_error(self):
        """Test creating media with validation error."""
        self.assert_error_behavior(
            func_to_call=Media.create_media,
            expected_exception_type=ValidationError,
            expected_message="String should have at least 1 character",
            user_id="",
            image_url="http://example.com/image2.jpg"
        )

    def test_create_media_no_user(self):
        """Test creating media for a non-existent user."""
        self.assert_error_behavior(
            func_to_call=Media.create_media,
            expected_exception_type=UserNotFoundError,
            expected_message="User with ID '999' does not exist.",
            user_id="999",
            image_url="http://example.com/image2.jpg"
        )

    def test_list_media(self):
        """Test listing all media."""
        user_id = "202"
        User.create_user(user_id, "Pic Poster", "picposter")
        Media.create_media(user_id, "http://example.com/image1.png")
        Media.create_media(user_id, "http://example.com/image2.png", caption="Second")
        Media.create_media(user_id, "http://example.com/image3.png")
        media_list = Media.list_media()
        self.assertEqual(len(media_list), 3)
        media_ids = {m["id"] for m in media_list}
        self.assertEqual(len(media_ids), 3)  # Ensure unique IDs

    def test_delete_media_type_error(self):
        """Test deleting media with non-string media_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=Media.delete_media,
            expected_exception_type=TypeError,
            expected_message="Field media_id must be a string.",
            media_id=123
        )

    def test_delete_media_empty_string_error(self):
        """Test deleting media with empty string media_id raises InvalidMediaIDError."""
        self.assert_error_behavior(
            func_to_call=Media.delete_media,
            expected_exception_type=InvalidMediaIDError,
            expected_message="Field media_id cannot be empty.",
            media_id=""
        )

if __name__ == "__main__":
    unittest.main()
