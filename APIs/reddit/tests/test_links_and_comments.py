import unittest
import reddit as RedditAPI
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestLinksAndCommentsMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the LinksAndComments class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Create test subreddit
        RedditAPI.DB.setdefault("subreddits", {})["testsub"] = {
            "name": "testsub",
            "description": "Test subreddit",
        }
        # Create a test post that can be used across multiple tests
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "self", "testsub", "My Title", text="Body text"
        )
        self.link_id = subm["link_id"]

    def test_comment_operations(self):
        """Test comment creation, deletion, and editing."""
        # Create a comment
        c = RedditAPI.LinksAndComments.post_api_comment("t3_1", "Hello World")
        self.assertIn("comment_id", c)
        comment_id = c["comment_id"]

        # Delete the comment
        d = RedditAPI.LinksAndComments.post_api_del(comment_id)
        self.assertEqual(d["status"], "deleted")

        # Try editing the deleted comment
        e = RedditAPI.LinksAndComments.post_api_editusertext(comment_id, "Edited text")
        self.assertEqual(e.get("error"), "cannot_edit_deleted_comment")

    def test_submit_self_post(self):
        """Test submitting a self post."""
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "self", "testsub", "My Title", text="Body text"
        )
        self.assertEqual(subm["status"], "submitted")
        self.assertIn("link_id", subm)

    def test_submit_link_post(self):
        """Test submitting a link post."""
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "link", "testsub", "My Link", url="https://example.com"
        )
        self.assertEqual(subm["status"], "submitted")
        self.assertIn("link_id", subm)

    def test_submit_nsfw_post(self):
        """Test submitting an NSFW post."""
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "self", "testsub", "NSFW Title", text="NSFW Content", nsfw=True
        )
        self.assertEqual(subm["status"], "submitted")

    def test_submit_spoiler_post(self):
        """Test submitting a spoiler post."""
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "self", "testsub", "Spoiler Title", text="Spoiler Content", spoiler=True
        )
        self.assertEqual(subm["status"], "submitted")

    def test_submit_nsfw_spoiler_post(self):
        """Test submitting a post with both NSFW and spoiler flags."""
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "self",
            "testsub",
            "NSFW Spoiler Title",
            text="Content",
            nsfw=True,
            spoiler=True,
        )
        self.assertEqual(subm["status"], "submitted")

    def test_submit_invalid_kind(self):
        """Test submitting with invalid kind."""
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "invalid", "testsub", "Title", text="Body"
        )
        self.assertEqual(subm["error"], "invalid_kind")

    def test_submit_missing_text(self):
        """Test submitting self post without text."""
        subm = RedditAPI.LinksAndComments.post_api_submit("self", "testsub", "Title")
        self.assertEqual(subm["error"], "missing_text")

    def test_submit_missing_url(self):
        """Test submitting link post without URL."""
        subm = RedditAPI.LinksAndComments.post_api_submit("link", "testsub", "Title")
        self.assertEqual(subm["error"], "missing_url")

    def test_submit_empty_title(self):
        """Test submitting post with empty title."""
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "self", "testsub", "", text="Body"
        )
        self.assertEqual(subm["error"], "Title cannot be empty.")

    def test_submit_nonexistent_subreddit(self):
        """Test submitting post to nonexistent subreddit."""
        subm = RedditAPI.LinksAndComments.post_api_submit(
            "self", "nonexistent", "Title", text="Body"
        )
        self.assertEqual(subm["error"], "Subreddit not found.")

    def test_follow_post(self):
        """Test following a post."""
        f = RedditAPI.LinksAndComments.post_api_follow_post(self.link_id, True)
        self.assertEqual(f["follow"], True)

    def test_hide_posts(self):
        """Test hiding posts."""
        hide = RedditAPI.LinksAndComments.post_api_hide([self.link_id, "t3_3"])
        self.assertEqual(hide["status"], "hidden")

    def test_get_info(self):
        """Test getting post info."""
        info = RedditAPI.LinksAndComments.get_api_info(id=self.link_id)
        self.assertIn("results", info)

    def test_lock_post(self):
        """Test locking a post."""
        lock = RedditAPI.LinksAndComments.post_api_lock(self.link_id)
        self.assertEqual(lock["status"], "locked")

    def test_mark_nsfw(self):
        """Test marking a post as NSFW."""
        nsfw = RedditAPI.LinksAndComments.post_api_marknsfw(self.link_id)
        self.assertEqual(nsfw["status"], "nsfw_marked")

    def test_get_more_children(self):
        """Test getting more children."""
        more = RedditAPI.LinksAndComments.get_api_morechildren(self.link_id, "c1,c2")
        self.assertIn("children_requested", more)

    def test_report_post(self):
        """Test reporting a post."""
        rep = RedditAPI.LinksAndComments.post_api_report(self.link_id, "Inappropriate")
        self.assertEqual(rep["status"], "reported")

    def test_save_post(self):
        """Test saving a post."""
        saved = RedditAPI.LinksAndComments.post_api_save(self.link_id)
        self.assertEqual(saved["status"], "saved")

    def test_get_saved_categories(self):
        """Test getting saved categories."""
        cats = RedditAPI.LinksAndComments.get_api_saved_categories()
        self.assertIsInstance(cats, list)

    def test_set_replies_state(self):
        """Test setting replies state."""
        sr = RedditAPI.LinksAndComments.post_api_sendreplies(self.link_id, False)
        self.assertEqual(sr["status"], "replies_state_changed")

    def test_set_contest_mode(self):
        """Test setting contest mode."""
        cmode = RedditAPI.LinksAndComments.post_api_set_contest_mode(True, self.link_id)
        self.assertEqual(cmode["status"], "contest_mode_set")

    def test_set_sticky(self):
        """Test setting post as sticky."""
        sticky = RedditAPI.LinksAndComments.post_api_set_subreddit_sticky(
            None, True, self.link_id
        )
        self.assertEqual(sticky["status"], "sticky_set")

    def test_set_suggested_sort(self):
        """Test setting suggested sort."""
        ssort = RedditAPI.LinksAndComments.post_api_set_suggested_sort(
            "top", self.link_id
        )
        self.assertEqual(ssort["status"], "suggested_sort_set")

    def test_mark_spoiler(self):
        """Test marking post as spoiler."""
        spoiler = RedditAPI.LinksAndComments.post_api_spoiler(self.link_id)
        self.assertEqual(spoiler["status"], "spoiler_marked")

    def test_store_visits(self):
        """Test storing visits."""
        visits = RedditAPI.LinksAndComments.post_api_store_visits()
        self.assertEqual(visits["status"], "visits_stored")

    def test_unhide_posts(self):
        """Test unhiding posts."""
        unh = RedditAPI.LinksAndComments.post_api_unhide([self.link_id])
        self.assertEqual(unh["status"], "unhidden")

    def test_unlock_post(self):
        """Test unlocking a post."""
        unl = RedditAPI.LinksAndComments.post_api_unlock(self.link_id)
        self.assertEqual(unl["status"], "unlocked")

    def test_unmark_nsfw(self):
        """Test unmarking NSFW."""
        unnsfw = RedditAPI.LinksAndComments.post_api_unmarknsfw(self.link_id)
        self.assertEqual(unnsfw["status"], "nsfw_removed")

    def test_unsave_post(self):
        """Test unsaving a post."""
        unsv = RedditAPI.LinksAndComments.post_api_unsave(self.link_id)
        self.assertEqual(unsv["status"], "unsaved")

    def test_unmark_spoiler(self):
        """Test unmarking spoiler."""
        unsp = RedditAPI.LinksAndComments.post_api_unspoiler(self.link_id)
        self.assertEqual(unsp["status"], "spoiler_removed")

    def test_vote(self):
        """Test voting on a post."""
        vot = RedditAPI.LinksAndComments.post_api_vote(self.link_id, 1)
        self.assertEqual(vot["status"], "voted")


if __name__ == "__main__":
    unittest.main()
