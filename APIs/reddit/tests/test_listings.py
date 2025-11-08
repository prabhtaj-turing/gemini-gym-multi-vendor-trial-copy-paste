import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestListingsMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Listings class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()

    def test_get_best(self):
        """Test getting best listings."""
        best = RedditAPI.Listings.get_best(after="t3_1", limit=10)
        self.assertEqual(best["listing_type"], "best")
        self.assertIn("items", best)

    def test_get_by_id(self):
        """Test getting listings by ID."""
        by_id = RedditAPI.Listings.get_by_id_names("t3_abc,t3_def")
        self.assertEqual(by_id["listing_type"], "by_id")
        self.assertIn("items", by_id)

    def test_get_comments_article(self):
        """Test getting comments for an article."""
        com = RedditAPI.Listings.get_comments_article("article123")
        self.assertEqual(com["article"], "article123")
        self.assertIn("comments", com)

    def test_get_controversial(self):
        """Test getting controversial listings."""
        contr = RedditAPI.Listings.get_controversial(after="t3_2")
        self.assertEqual(contr["listing_type"], "controversial")
        self.assertIn("items", contr)

    def test_get_duplicates_article(self):
        """Test getting duplicate articles."""
        dup = RedditAPI.Listings.get_duplicates_article("articleXYZ")
        self.assertEqual(dup["article"], "articleXYZ")
        self.assertIn("duplicates", dup)

    def test_get_hot(self):
        """Test getting hot listings."""
        hot = RedditAPI.Listings.get_hot(limit=5)
        self.assertEqual(hot["listing_type"], "hot")
        self.assertIn("items", hot)

    def test_get_new(self):
        """Test getting new listings."""
        new = RedditAPI.Listings.get_new()
        self.assertEqual(new["listing_type"], "new")
        self.assertIn("items", new)

    def test_get_rising(self):
        """Test getting rising listings."""
        ris = RedditAPI.Listings.get_rising()
        self.assertEqual(ris["listing_type"], "rising")
        self.assertIn("items", ris)

    def test_get_top(self):
        """Test getting top listings."""
        top = RedditAPI.Listings.get_top(t="day")
        self.assertEqual(top["listing_type"], "top")
        self.assertEqual(top["timeframe"], "day")
        self.assertIn("items", top)

    def test_get_sort(self):
        """Test getting sorted listings."""
        srt = RedditAPI.Listings.get_sort("hot")
        self.assertEqual(srt["listing_type"], "hot")
        self.assertIn("items", srt)


if __name__ == "__main__":
    unittest.main()
