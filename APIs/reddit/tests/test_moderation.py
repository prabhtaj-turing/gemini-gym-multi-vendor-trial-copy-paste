import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestModerationMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Moderation class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()

    def test_get_about_edited(self):
        """Test getting edited items."""
        edited = RedditAPI.Moderation.get_about_edited()
        self.assertIsInstance(edited, list)

    def test_get_about_log(self):
        """Test getting moderation log."""
        log = RedditAPI.Moderation.get_about_log()
        self.assertIsInstance(log, list)

    def test_get_about_modqueue(self):
        """Test getting modqueue."""
        mq = RedditAPI.Moderation.get_about_modqueue()
        self.assertIsInstance(mq, list)

    def test_get_about_reports(self):
        """Test getting reported items."""
        rep_list = RedditAPI.Moderation.get_about_reports()
        self.assertIsInstance(rep_list, list)

    def test_get_about_spam(self):
        """Test getting spam items."""
        spam = RedditAPI.Moderation.get_about_spam()
        self.assertIsInstance(spam, list)

    def test_get_about_unmoderated(self):
        """Test getting unmoderated items."""
        unmod = RedditAPI.Moderation.get_about_unmoderated()
        self.assertIsInstance(unmod, list)

    def test_get_about_location(self):
        """Test getting items by location."""
        loc = RedditAPI.Moderation.get_about_location("spam")
        self.assertEqual(loc["location"], "spam")
        self.assertIn("items", loc)

    def test_accept_moderator_invite(self):
        """Test accepting moderator invite."""
        acc_inv = RedditAPI.Moderation.post_api_accept_moderator_invite()
        self.assertEqual(acc_inv["status"], "moderator_invite_accepted")

    def test_approve(self):
        """Test approving an item."""
        app = RedditAPI.Moderation.post_api_approve("t3_abc")
        self.assertEqual(app["status"], "approved")

    def test_distinguish(self):
        """Test distinguishing an item."""
        dist = RedditAPI.Moderation.post_api_distinguish("t1_xyz", "yes")
        self.assertEqual(dist["status"], "distinguished")

    def test_ignore_reports(self):
        """Test ignoring reports."""
        ign = RedditAPI.Moderation.post_api_ignore_reports("t3_111")
        self.assertEqual(ign["status"], "ignored_reports")

    def test_leave_contributor(self):
        """Test leaving as contributor."""
        lc = RedditAPI.Moderation.post_api_leavecontributor()
        self.assertEqual(lc["status"], "left_contributor")

    def test_leave_moderator(self):
        """Test leaving as moderator."""
        lm = RedditAPI.Moderation.post_api_leavemoderator()
        self.assertEqual(lm["status"], "left_moderator")

    def test_remove(self):
        """Test removing an item."""
        rm_ = RedditAPI.Moderation.post_api_remove("t3_r1")
        self.assertEqual(rm_["status"], "removed")

    def test_show_comment(self):
        """Test showing a comment."""
        show_c = RedditAPI.Moderation.post_api_show_comment("t1_c2")
        self.assertEqual(show_c["status"], "comment_shown")

    def test_snooze_reports(self):
        """Test snoozing reports."""
        snz = RedditAPI.Moderation.post_api_snooze_reports("t3_abc")
        self.assertEqual(snz["status"], "reports_snoozed")

    def test_unignore_reports(self):
        """Test unignoring reports."""
        unign = RedditAPI.Moderation.post_api_unignore_reports("t3_abc")
        self.assertEqual(unign["status"], "reports_unignored")

    def test_unsnooze_reports(self):
        """Test unsnoozing reports."""
        unsz = RedditAPI.Moderation.post_api_unsnooze_reports("t3_abc")
        self.assertEqual(unsz["status"], "reports_unsnoozed")

    def test_update_crowd_control(self):
        """Test updating crowd control level."""
        ccl = RedditAPI.Moderation.post_api_update_crowd_control_level("t3_abc", 2)
        self.assertEqual(ccl["status"], "crowd_control_updated")

    def test_get_stylesheet(self):
        """Test getting subreddit stylesheet."""
        style = RedditAPI.Moderation.get_stylesheet()
        self.assertIn("subreddit stylesheet", style)


if __name__ == "__main__":
    unittest.main()
