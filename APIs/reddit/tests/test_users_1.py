import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestUsersMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Users class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Add test user to DB for testing
        RedditAPI.DB.setdefault("users", {})["Smith"] = {
            "profile": "some info",
            "id": "t2_smith",
        }
        self.test_username = "Smith"
        self.test_user_id = "t2_smith"

    def test_block_user(self):
        """Test blocking a user."""
        blk = RedditAPI.Users.post_api_block_user("t2_abc")
        self.assertEqual(blk["status"], "user_blocked")

    def test_add_friend(self):
        """Test adding a friend."""
        fr = RedditAPI.Users.post_api_friend("json", "Bob")
        self.assertEqual(fr["status"], "friend_added")

    def test_report_user(self):
        """Test reporting a user."""
        rep = RedditAPI.Users.post_api_report_user("Alice", reason="Spammy")
        self.assertEqual(rep["status"], "user_reported")

    def test_set_permissions(self):
        """Test setting user permissions."""
        sp = RedditAPI.Users.post_api_setpermissions(
            "Charlie", permissions=["mod", "wiki"]
        )
        self.assertEqual(sp["status"], "permissions_set")

    def test_remove_friend(self):
        """Test removing a friend."""
        unfr = RedditAPI.Users.post_api_unfriend("Bob", type="friend")
        self.assertEqual(unfr["status"], "relationship_removed")

    def test_get_user_data_by_account_ids(self):
        """Test getting user data by account IDs."""
        data = RedditAPI.Users.get_api_user_data_by_account_ids("t2_abc,t2_def")
        self.assertIn("ids", data)

    def test_check_username_availability(self):
        """Test checking username availability."""
        av = RedditAPI.Users.get_api_username_available("RandomName123")
        self.assertTrue(av["available"])

    def test_delete_friend(self):
        """Test deleting a friend."""
        delf = RedditAPI.Users.delete_api_v1_me_friends_username("Alice")
        self.assertEqual(delf["status"], "user_unfriended")

    def test_get_user_trophies(self):
        """Test getting user trophies."""
        trophy = RedditAPI.Users.get_api_v1_user_username_trophies("Bob")
        self.assertIn("trophies", trophy)

    def test_get_user_about(self):
        """Test getting user about info."""
        ab = RedditAPI.Users.get_user_username_about(self.test_username)
        self.assertEqual(ab["status"], "ok")
        self.assertEqual(ab["profile"]["id"], self.test_user_id)

    def test_get_user_comments(self):
        """Test getting user comments."""
        com = RedditAPI.Users.get_user_username_comments(self.test_username)
        self.assertIsInstance(com, list)

    def test_get_user_downvoted(self):
        """Test getting user's downvoted content."""
        dwn = RedditAPI.Users.get_user_username_downvoted()
        self.assertIsInstance(dwn, list)

    def test_get_user_gilded(self):
        """Test getting user's gilded content."""
        gild = RedditAPI.Users.get_user_username_gilded()
        self.assertIsInstance(gild, list)

    def test_get_user_hidden(self):
        """Test getting user's hidden content."""
        hidden = RedditAPI.Users.get_user_username_hidden()
        self.assertIsInstance(hidden, list)

    def test_get_user_overview(self):
        """Test getting user's overview."""
        ov = RedditAPI.Users.get_user_username_overview()
        self.assertIsInstance(ov, list)

    def test_get_user_saved(self):
        """Test getting user's saved content."""
        sav = RedditAPI.Users.get_user_username_saved()
        self.assertIsInstance(sav, list)

    def test_get_user_submitted(self):
        """Test getting user's submitted content."""
        sbm = RedditAPI.Users.get_user_username_submitted()
        self.assertIsInstance(sbm, list)

    def test_get_user_upvoted(self):
        """Test getting user's upvoted content."""
        upv = RedditAPI.Users.get_user_username_upvoted()
        self.assertIsInstance(upv, list)

    def test_get_user_where(self):
        """Test getting user content by where parameter."""
        wh = RedditAPI.Users.get_user_username_where("overview")
        self.assertIsInstance(wh, list)


if __name__ == "__main__":
    unittest.main()
