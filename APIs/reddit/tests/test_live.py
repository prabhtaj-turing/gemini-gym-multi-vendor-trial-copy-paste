import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestLiveMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Live class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Create a test live thread that can be used across multiple tests
        crt = RedditAPI.Live.post_api_live_create("My Live Thread")
        self.live_id = crt["thread_id"]

    def test_get_live_by_id(self):
        """Test getting live threads by ID."""
        data = RedditAPI.Live.get_api_live_by_id_names("live_1,live_2")
        self.assertIn("live_threads_requested", data)

    def test_create_live_thread(self):
        """Test creating a live thread."""
        # Test successful creation
        crt = RedditAPI.Live.post_api_live_create("Test Live Thread")
        self.assertEqual(crt["status"], "live_thread_created")
        self.assertIn("thread_id", crt)

        # Test empty title
        empty_title = RedditAPI.Live.post_api_live_create("")
        self.assertEqual(empty_title["error"], "Title cannot be empty.")

        # Test title too long
        long_title = "x" * 121  # 121 characters
        long_title_result = RedditAPI.Live.post_api_live_create(long_title)
        self.assertEqual(long_title_result["error"], "Title too long.")

        # Test title at maximum length (120 characters)
        max_length_title = "x" * 120
        max_length_result = RedditAPI.Live.post_api_live_create(max_length_title)
        self.assertEqual(max_length_result["status"], "live_thread_created")
        self.assertIn("thread_id", max_length_result)

    def test_get_happening_now(self):
        """Test getting currently happening live threads."""
        hap = RedditAPI.Live.get_api_live_happening_now()
        self.assertIn("featured_live_thread", hap)

    def test_accept_contributor_invite(self):
        """Test accepting contributor invite."""
        acc_contrib = RedditAPI.Live.post_api_live_thread_accept_contributor_invite(
            self.live_id
        )
        self.assertEqual(acc_contrib["status"], "contributor_invite_accepted")

    def test_close_thread(self):
        """Test closing a live thread."""
        close_t = RedditAPI.Live.post_api_live_thread_close_thread(self.live_id)
        self.assertEqual(close_t["status"], "thread_closed")
        # Verify closed status in DB
        self.assertTrue(RedditAPI.DB["live_threads"][self.live_id].get("closed"))

    def test_delete_update(self):
        """Test deleting a live thread update."""
        del_up = RedditAPI.Live.post_api_live_thread_delete_update("upd_1")
        self.assertEqual(del_up["status"], "update_deleted")

    def test_edit_thread(self):
        """Test editing a live thread."""
        edit = RedditAPI.Live.post_api_live_thread_edit(description="New Desc")
        self.assertEqual(edit["status"], "thread_edited")

    def test_hide_discussion(self):
        """Test hiding live thread discussion."""
        hide_d = RedditAPI.Live.post_api_live_thread_hide_discussion()
        self.assertEqual(hide_d["status"], "discussion_hidden")

    def test_invite_contributor(self):
        """Test inviting a contributor."""
        inv_c = RedditAPI.Live.post_api_live_thread_invite_contributor("user123")
        self.assertEqual(inv_c["status"], "contributor_invited")

    def test_leave_contributor(self):
        """Test leaving as a contributor."""
        leave_c = RedditAPI.Live.post_api_live_thread_leave_contributor()
        self.assertEqual(leave_c["status"], "left_as_contributor")

    def test_report_thread(self):
        """Test reporting a live thread."""
        rep = RedditAPI.Live.post_api_live_thread_report(self.live_id)
        self.assertEqual(rep["status"], "live_thread_reported")

    def test_remove_contributor(self):
        """Test removing a contributor."""
        rm = RedditAPI.Live.post_api_live_thread_rm_contributor("user123")
        self.assertEqual(rm["status"], "contributor_removed")

    def test_remove_contributor_invite(self):
        """Test removing a contributor invite."""
        rm_inv = RedditAPI.Live.post_api_live_thread_rm_contributor_invite("userABC")
        self.assertEqual(rm_inv["status"], "invite_revoked")

    def test_set_contributor_permissions(self):
        """Test setting contributor permissions."""
        set_perm = RedditAPI.Live.post_api_live_thread_set_contributor_permissions(
            "userX"
        )
        self.assertEqual(set_perm["status"], "permissions_set")

    def test_strike_update(self):
        """Test striking an update."""
        strike = RedditAPI.Live.post_api_live_thread_strike_update("upd_2")
        self.assertEqual(strike["status"], "update_struck")

    def test_unhide_discussion(self):
        """Test unhiding discussion."""
        unhide = RedditAPI.Live.post_api_live_thread_unhide_discussion()
        self.assertEqual(unhide["status"], "discussion_unhidden")

    def test_update_thread(self):
        """Test updating a live thread."""
        update = RedditAPI.Live.post_api_live_thread_update("New update body")
        self.assertEqual(update["status"], "update_added")

    def test_get_thread(self):
        """Test getting live thread details."""
        get_th = RedditAPI.Live.get_live_thread(self.live_id)
        self.assertIn("info", get_th)
        self.assertEqual(get_th["info"]["title"], "My Live Thread")

    def test_get_thread_about(self):
        """Test getting thread about information."""
        about = RedditAPI.Live.get_live_thread_about()
        self.assertIn("about", about)

    def test_get_thread_contributors(self):
        """Test getting thread contributors."""
        contribs = RedditAPI.Live.get_live_thread_contributors()
        self.assertIsInstance(contribs, list)

    def test_get_thread_discussions(self):
        """Test getting thread discussions."""
        disc = RedditAPI.Live.get_live_thread_discussions()
        self.assertIsInstance(disc, list)

    def test_get_update_details(self):
        """Test getting update details."""
        up_det = RedditAPI.Live.get_live_thread_updates_update_id("upd_2")
        self.assertIsInstance(up_det, dict)


if __name__ == "__main__":
    unittest.main()
