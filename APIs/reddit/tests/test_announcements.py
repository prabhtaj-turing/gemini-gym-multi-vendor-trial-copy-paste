import unittest
import reddit as RedditAPI
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAnnouncementsMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Announcements class."""

    def setUp(self):
        """Set up the test environment before each test."""
        RedditAPI.DB.clear()
        RedditAPI.DB.update(
            {
                "accounts": {},
                "announcements": [],
                "captcha_needed": False,
                "collections": {},
                "comments": {},
                "emoji": {},
                "flair": {},
                "links": {},
                "listings": {},  # Keep if needed by any method logic
                "live_threads": {},
                "messages": {},
                "misc_data": {},  # Keep if needed by any method logic
                "moderation": {},  # Keep if needed by any method logic
                "modmail": {},  # Keep if needed by any method logic
                "modnotes": {},
                "multis": {},
                "search_index": {},  # Keep if needed by any method logic
                "subreddits": {},
                "users": {},
                "widgets": {},
                "wiki": {},
            }
        )

    def tearDown(self):
        """Clean up after each test."""
        # Clear the mock database if necessary
        reset_db()

    def test_get_api_announcements_v1_unread(self):
        """Test getting unread announcements."""
        unread = RedditAPI.Announcements.get_api_announcements_v1_unread()
        # Initial DB state has empty announcements list
        self.assertEqual(unread, [])

    def test_post_api_announcements_v1_read_all(self):
        """Test marking all announcements as read."""
        read_all = RedditAPI.Announcements.post_api_announcements_v1_read_all()
        self.assertEqual(read_all["status"], "all_announcements_marked_read")

    def test_get_api_announcements_v1(self):
        """Test getting all announcements."""
        # Add a mock announcement to the DB for testing
        RedditAPI.DB["announcements"].append({"id": "ann1", "title": "Test"})
        all_anns = RedditAPI.Announcements.get_api_announcements_v1()
        self.assertEqual(len(all_anns), 1)
        self.assertEqual(all_anns[0]["id"], "ann1")

    def test_post_api_announcements_v1_hide(self):
        """Test hiding announcements."""
        # Add a mock announcement first
        RedditAPI.DB["announcements"].append({"id": "ann1", "title": "Test"})
        hide_resp = RedditAPI.Announcements.post_api_announcements_v1_hide(["ann1"])
        self.assertEqual(hide_resp["status"], "announcements_hidden")
        self.assertEqual(hide_resp["ids"], ["ann1"])

    def test_post_api_announcements_v1_read(self):
        """Test marking specific announcements as read."""
        # Add a mock announcement first
        RedditAPI.DB["announcements"].append({"id": "ann1", "title": "Test"})
        read_resp = RedditAPI.Announcements.post_api_announcements_v1_read(["ann1"])
        self.assertEqual(read_resp["status"], "announcements_marked_read")
        self.assertEqual(read_resp["ids"], ["ann1"])


# if __name__ == '__main__':
#     unittest.main()
