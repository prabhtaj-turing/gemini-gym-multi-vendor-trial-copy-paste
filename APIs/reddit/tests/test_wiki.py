import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestWikiMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Wiki class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Create a test wiki page for use across tests
        edit = RedditAPI.Wiki.post_api_wiki_edit("mypage", "Some content")
        self.wiki_page = "mypage"
        self.wiki_content = "Some content"
        self.wiki_revision = "rev0"

    def test_add_editor(self):
        """Test adding a wiki editor."""
        add_ed = RedditAPI.Wiki.post_api_wiki_alloweditor_add(self.wiki_page, "userX")
        self.assertEqual(add_ed["status"], "editor_added")

    def test_remove_editor(self):
        """Test removing a wiki editor."""
        del_ed = RedditAPI.Wiki.post_api_wiki_alloweditor_del(self.wiki_page, "userX")
        self.assertEqual(del_ed["status"], "editor_removed")

    def test_editor_action(self):
        """Test wiki editor action."""
        act = RedditAPI.Wiki.post_api_wiki_alloweditor_act("add")
        self.assertEqual(act["status"], "wiki_editor_action")

    def test_edit_wiki_page(self):
        """Test editing a wiki page."""
        edit = RedditAPI.Wiki.post_api_wiki_edit(self.wiki_page, self.wiki_content)
        self.assertEqual(edit["status"], "wiki_page_edited")
        # Verify edit in DB
        self.assertEqual(
            RedditAPI.DB["wiki"]["default_subreddit"][self.wiki_page]["content"],
            self.wiki_content,
        )

    def test_hide_revision(self):
        """Test hiding a wiki revision."""
        hide = RedditAPI.Wiki.post_api_wiki_hide(self.wiki_page, "rev1")
        self.assertEqual(hide["status"], "revision_hidden")

    def test_revert_wiki_page(self):
        """Test reverting a wiki page."""
        rev = RedditAPI.Wiki.post_api_wiki_revert(self.wiki_page, self.wiki_revision)
        self.assertEqual(rev["status"], "wiki_page_reverted")

    def test_get_wiki_discussions(self):
        """Test getting wiki discussions."""
        disc = RedditAPI.Wiki.get_wiki_discussions_page(self.wiki_page)
        self.assertIn("discussions", disc)

    def test_get_wiki_pages(self):
        """Test getting all wiki pages."""
        pages = RedditAPI.Wiki.get_wiki_pages()
        self.assertIsInstance(pages, list)
        self.assertIn(self.wiki_page, pages)  # Check if created page is listed

    def test_get_all_revisions(self):
        """Test getting all wiki revisions."""
        all_rev = RedditAPI.Wiki.get_wiki_revisions()
        self.assertIsInstance(all_rev, list)

    def test_get_page_revisions(self):
        """Test getting revisions for a specific page."""
        pg_rev = RedditAPI.Wiki.get_wiki_revisions_page(self.wiki_page)
        self.assertIn("revisions", pg_rev)

    def test_get_page_settings(self):
        """Test getting wiki page settings."""
        pg_set = RedditAPI.Wiki.get_wiki_settings_page(self.wiki_page)
        self.assertIn("settings", pg_set)

    def test_get_wiki_page(self):
        """Test getting a wiki page."""
        pg = RedditAPI.Wiki.get_wiki_page(self.wiki_page)
        self.assertIn("content", pg)
        self.assertEqual(
            pg["content"], self.wiki_content
        )  # Check content after edits/reverts


if __name__ == "__main__":
    unittest.main()
