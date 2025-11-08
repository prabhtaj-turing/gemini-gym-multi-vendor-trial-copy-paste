import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestMultisMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Multis class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Create a test multi for use across tests
        cp = RedditAPI.Multis.post_api_multi_copy("source/path", "dest/path")
        self.multi_path = f"user/test/{cp['new_multiname']}"

    def test_delete_filter(self):
        """Test deleting a filter."""
        df = RedditAPI.Multis.delete_api_filter_filterpath("filterA")
        self.assertEqual(df["status"], "filter_deleted")

    def test_remove_subreddit_from_filter(self):
        """Test removing a subreddit from a filter."""
        rf = RedditAPI.Multis.delete_api_filter_filterpath_r_srname("filterA", "subX")
        self.assertEqual(rf["status"], "subreddit_removed_from_filter")

    def test_copy_multi(self):
        """Test copying a multi."""
        cp = RedditAPI.Multis.post_api_multi_copy("source/path", "dest/path")
        self.assertEqual(cp["status"], "multi_copied")
        self.assertIn("new_multiname", cp)
        # Verify creation in DB
        self.assertIn(cp["new_multiname"], RedditAPI.DB["multis"])

    def test_get_my_multis(self):
        """Test getting user's multis."""
        mine = RedditAPI.Multis.get_api_multi_mine()
        self.assertIsInstance(mine, list)
        self.assertTrue(len(mine) > 0)  # Since we created one

    def test_get_user_multis(self):
        """Test getting another user's multis."""
        userm = RedditAPI.Multis.get_api_multi_user_username("someUser")
        self.assertIsInstance(userm, list)

    def test_delete_multi(self):
        """Test deleting a multi."""
        dmulti = RedditAPI.Multis.delete_api_multi_multipath(self.multi_path)
        self.assertEqual(dmulti["status"], "multi_deleted")

    def test_get_multi_description(self):
        """Test getting multi description."""
        desc = RedditAPI.Multis.get_api_multi_multipath_description(self.multi_path)
        self.assertIn("description", desc)

    def test_remove_subreddit_from_multi(self):
        """Test removing a subreddit from a multi."""
        rm_sr = RedditAPI.Multis.delete_api_multi_multipath_r_srname(
            "user/mypath", "mysub"
        )
        self.assertEqual(rm_sr["status"], "subreddit_removed_from_multi")


if __name__ == "__main__":
    unittest.main()
