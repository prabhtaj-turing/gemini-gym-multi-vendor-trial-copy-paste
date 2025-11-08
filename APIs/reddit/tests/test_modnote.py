import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestModnoteMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Modnote class."""

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
        # Add a test note to DB for testing get
        RedditAPI.DB.setdefault("modnotes", {}).setdefault("testuser", []).append(
            {"note_id": "n1", "content": "Be kind"}
        )

    def test_delete_note(self):
        """Test deleting a modnote."""
        d = RedditAPI.Modnote.delete_api_mod_notes("note123")
        self.assertEqual(d["status"], "note_deleted")

    def test_get_recent_notes(self):
        """Test getting recent modnotes."""
        rec = RedditAPI.Modnote.get_api_mod_notes_recent("testuser", "somesub")
        self.assertIn("notes", rec)
        self.assertEqual(len(rec["notes"]), 1)
        self.assertEqual(rec["notes"][0]["note_id"], "n1")


if __name__ == "__main__":
    unittest.main()
