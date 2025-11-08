import unittest
import os
import reddit as RedditAPI
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestStateManagement(BaseTestCaseWithErrorHandler):
    """Tests for state management functions."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        self.temp_file = "_test_db.json"
        # Add test data to DB
        RedditAPI.DB["users"]["test_user"] = {"id": "u123", "profile": "Test Profile"}

    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary file if it exists
        if os.path.isfile(self.temp_file):
            os.remove(self.temp_file)

    def test_save_state(self):
        """Test saving state to a file."""
        # Save current state
        RedditAPI.save_state(self.temp_file)
        # Verify file was created
        self.assertTrue(os.path.isfile(self.temp_file))

    def test_load_state(self):
        """Test loading state from a file."""
        # First save the state
        RedditAPI.save_state(self.temp_file)

        # Clear DB in memory
        RedditAPI.DB.clear()
        RedditAPI.DB["users"] = {}
        self.assertEqual(len(RedditAPI.DB.get("users", {})), 0)

        # Load state back
        RedditAPI.load_state(self.temp_file)

        # Verify data was restored
        self.assertIn("test_user", RedditAPI.DB.get("users", {}))
        self.assertEqual(RedditAPI.DB["users"]["test_user"]["id"], "u123")
        self.assertEqual(RedditAPI.DB["users"]["test_user"]["profile"], "Test Profile")

    def test_state_persistence(self):
        """Test complete state persistence cycle."""
        # Save state
        RedditAPI.save_state(self.temp_file)

        # Clear DB
        RedditAPI.DB.clear()
        RedditAPI.DB["users"] = {}

        # Load state
        RedditAPI.load_state(self.temp_file)

        # Verify all data was restored
        self.assertIn("test_user", RedditAPI.DB.get("users", {}))
        self.assertEqual(RedditAPI.DB["users"]["test_user"]["id"], "u123")
        self.assertEqual(RedditAPI.DB["users"]["test_user"]["profile"], "Test Profile")


if __name__ == "__main__":
    unittest.main()
