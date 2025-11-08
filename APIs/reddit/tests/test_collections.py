import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestCollectionsMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Collections class."""

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
        # Create a test collection that can be used across multiple tests
        resp = RedditAPI.Collections.post_api_v1_collections_create_collection(
            "MyTitle", "t5_testsub"
        )
        self.collection_id = resp["collection_id"]

    def test_create_collection(self):
        """Test creating a new collection."""
        resp = RedditAPI.Collections.post_api_v1_collections_create_collection(
            "TestCollection", "t5_testsub"
        )
        self.assertEqual(resp["status"], "collection_created")
        self.assertIn("collection_id", resp)

    def test_get_collection(self):
        """Test getting collection details."""
        get_resp = RedditAPI.Collections.get_api_v1_collections_collection(
            self.collection_id
        )
        self.assertEqual(get_resp["title"], "MyTitle")

    def test_add_post_to_collection(self):
        """Test adding a post to a collection."""
        add_post = RedditAPI.Collections.post_api_v1_collections_add_post_to_collection(
            self.collection_id, "t3_postX"
        )
        self.assertEqual(add_post["status"], "success")
        get_resp = RedditAPI.Collections.get_api_v1_collections_collection(
            self.collection_id
        )
        self.assertIn("t3_postX", get_resp.get("links", []))

    def test_remove_post_from_collection(self):
        """Test removing a post from a collection."""
        # First add a post
        RedditAPI.Collections.post_api_v1_collections_add_post_to_collection(
            self.collection_id, "t3_postX"
        )
        # Then remove it
        rm_post = (
            RedditAPI.Collections.post_api_v1_collections_remove_post_in_collection(
                "t3_postX", self.collection_id
            )
        )
        self.assertEqual(rm_post["status"], "success")
        get_resp = RedditAPI.Collections.get_api_v1_collections_collection(
            self.collection_id
        )
        self.assertNotIn("t3_postX", get_resp.get("links", []))

    def test_reorder_collection(self):
        """Test reordering posts in a collection."""
        reorder = RedditAPI.Collections.post_api_v1_collections_reorder_collection(
            self.collection_id, ["t3_A", "t3_B"]
        )
        self.assertEqual(reorder["status"], "success")
        get_resp = RedditAPI.Collections.get_api_v1_collections_collection(
            self.collection_id
        )
        self.assertEqual(get_resp.get("links", []), ["t3_A", "t3_B"])

    def test_get_subreddit_collections(self):
        """Test getting collections for a subreddit."""
        subcolls = RedditAPI.Collections.get_api_v1_collections_subreddit_collections(
            "t5_testsub"
        )
        self.assertEqual(len(subcolls), 1)
        self.assertIn(self.collection_id, subcolls[0])
        self.assertEqual(subcolls[0][self.collection_id]["title"], "MyTitle")

    def test_update_collection_description(self):
        """Test updating collection description."""
        desc_upd = (
            RedditAPI.Collections.post_api_v1_collections_update_collection_description(
                self.collection_id, "Desc"
            )
        )
        self.assertEqual(desc_upd["status"], "success")
        self.assertEqual(desc_upd["new_description"], "Desc")

    def test_update_collection_display_layout(self):
        """Test updating collection display layout."""
        disp_upd = RedditAPI.Collections.post_api_v1_collections_update_collection_display_layout(
            self.collection_id, "GALLERY"
        )
        self.assertEqual(disp_upd["status"], "success")
        self.assertEqual(disp_upd["display_layout"], "GALLERY")

    def test_update_collection_title(self):
        """Test updating collection title."""
        title_upd = (
            RedditAPI.Collections.post_api_v1_collections_update_collection_title(
                self.collection_id, "NewTitle"
            )
        )
        self.assertEqual(title_upd["status"], "success")
        self.assertEqual(title_upd["new_title"], "NewTitle")
        get_resp = RedditAPI.Collections.get_api_v1_collections_collection(
            self.collection_id
        )
        self.assertEqual(get_resp["title"], "NewTitle")

    def test_delete_collection(self):
        """Test deleting a collection."""
        del_resp = RedditAPI.Collections.post_api_v1_collections_delete_collection(
            self.collection_id
        )
        self.assertEqual(del_resp["status"], "collection_deleted")
        get_resp = RedditAPI.Collections.get_api_v1_collections_collection(
            self.collection_id
        )
        self.assertEqual(get_resp.get("error"), "Collection not found")


if __name__ == "__main__":
    unittest.main()
