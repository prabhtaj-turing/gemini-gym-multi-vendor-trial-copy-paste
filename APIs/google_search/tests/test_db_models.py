#!/usr/bin/env python3
"""
Test cases for Google Search database models.
"""

import unittest
from pydantic import ValidationError
from ..SimulationEngine.db_models import WebContent, SearchIndexEntry, GoogleSearchDB


class TestWebContent(unittest.TestCase):
    """Test cases for WebContent model."""

    def test_web_content_valid_data(self):
        """Test WebContent with valid data."""
        content = WebContent(
            url="https://example.com/article",
            title="Test Article",
            snippet="This is a test article",
            content="Full content of the test article",
            publication_time="2024-01-15T10:30:00Z",
            tags=["technology", "innovation"],
            keywords=["tech", "AI"]
        )
        
        self.assertEqual(content.url, "https://example.com/article")
        self.assertEqual(content.title, "Test Article")
        self.assertEqual(content.snippet, "This is a test article")
        self.assertEqual(content.content, "Full content of the test article")
        self.assertEqual(content.publication_time, "2024-01-15T10:30:00Z")
        self.assertEqual(content.tags, ["technology", "innovation"])
        self.assertEqual(content.keywords, ["tech", "AI"])

    def test_web_content_minimal_data(self):
        """Test WebContent with minimal required data."""
        content = WebContent(
            url="https://example.com/article",
            title="Test Article",
            snippet="This is a test article",
            content="Full content of the test article"
        )
        
        self.assertEqual(content.url, "https://example.com/article")
        self.assertEqual(content.title, "Test Article")
        self.assertEqual(content.snippet, "This is a test article")
        self.assertEqual(content.content, "Full content of the test article")
        self.assertIsNone(content.publication_time)
        self.assertEqual(content.tags, [])
        self.assertEqual(content.keywords, [])

    def test_web_content_invalid_url(self):
        """Test WebContent with invalid URL."""
        with self.assertRaises(ValidationError) as context:
            WebContent(
                url="invalid-url",
                title="Test Article",
                snippet="This is a test article",
                content="Full content of the test article"
            )
        self.assertIn("Invalid URL format", str(context.exception))

    def test_web_content_empty_url(self):
        """Test WebContent with empty URL."""
        with self.assertRaises(ValidationError) as context:
            WebContent(
                url="",
                title="Test Article",
                snippet="This is a test article",
                content="Full content of the test article"
            )
        self.assertIn("URL cannot be empty", str(context.exception))

    def test_web_content_empty_title(self):
        """Test WebContent with empty title."""
        with self.assertRaises(ValidationError) as context:
            WebContent(
                url="https://example.com/article",
                title="",
                snippet="This is a test article",
                content="Full content of the test article"
            )
        self.assertIn("Field cannot be empty", str(context.exception))

    def test_web_content_empty_snippet(self):
        """Test WebContent with empty snippet."""
        with self.assertRaises(ValidationError) as context:
            WebContent(
                url="https://example.com/article",
                title="Test Article",
                snippet="",
                content="Full content of the test article"
            )
        self.assertIn("Field cannot be empty", str(context.exception))

    def test_web_content_empty_content(self):
        """Test WebContent with empty content."""
        with self.assertRaises(ValidationError) as context:
            WebContent(
                url="https://example.com/article",
                title="Test Article",
                snippet="This is a test article",
                content=""
            )
        self.assertIn("Field cannot be empty", str(context.exception))

    def test_web_content_invalid_publication_time(self):
        """Test WebContent with invalid publication time."""
        with self.assertRaises(ValidationError) as context:
            WebContent(
                url="https://example.com/article",
                title="Test Article",
                snippet="This is a test article",
                content="Full content of the test article",
                publication_time="invalid-date"
            )
        self.assertIn("Invalid publication time format", str(context.exception))

    def test_web_content_valid_publication_time(self):
        """Test WebContent with valid publication time."""
        content = WebContent(
            url="https://example.com/article",
            title="Test Article",
            snippet="This is a test article",
            content="Full content of the test article",
            publication_time="2024-01-15T10:30:00Z"
        )
        self.assertEqual(content.publication_time, "2024-01-15T10:30:00Z")

    def test_web_content_tags_validation(self):
        """Test WebContent tags validation."""
        content = WebContent(
            url="https://example.com/article",
            title="Test Article",
            snippet="This is a test article",
            content="Full content of the test article",
            tags=["  tech  ", "  innovation  ", ""]  # Empty string should be filtered out
        )
        self.assertEqual(content.tags, ["tech", "innovation"])

    def test_web_content_keywords_validation(self):
        """Test WebContent keywords validation."""
        content = WebContent(
            url="https://example.com/article",
            title="Test Article",
            snippet="This is a test article",
            content="Full content of the test article",
            keywords=["  AI  ", "  ML  ", ""]  # Empty string should be filtered out
        )
        self.assertEqual(content.keywords, ["AI", "ML"])


class TestSearchIndexEntry(unittest.TestCase):
    """Test cases for SearchIndexEntry model."""

    def test_search_index_entry_valid_data(self):
        """Test SearchIndexEntry with valid data."""
        entry = SearchIndexEntry(
            query_terms=["technology", "innovation"],
            content_ids=["content_001", "content_002"],
            relevance_scores={"content_001": 0.95, "content_002": 0.88}
        )
        
        self.assertEqual(entry.query_terms, ["technology", "innovation"])
        self.assertEqual(entry.content_ids, ["content_001", "content_002"])
        self.assertEqual(entry.relevance_scores, {"content_001": 0.95, "content_002": 0.88})

    def test_search_index_entry_empty_query_terms(self):
        """Test SearchIndexEntry with empty query terms."""
        with self.assertRaises(ValidationError) as context:
            SearchIndexEntry(
                query_terms=[],
                content_ids=["content_001"],
                relevance_scores={"content_001": 0.95}
            )
        self.assertIn("Query terms cannot be empty", str(context.exception))

    def test_search_index_entry_query_terms_validation(self):
        """Test SearchIndexEntry query terms validation."""
        entry = SearchIndexEntry(
            query_terms=["  Technology  ", "  Innovation  ", ""],  # Empty string should be filtered out
            content_ids=["content_001"],
            relevance_scores={"content_001": 0.95}
        )
        self.assertEqual(entry.query_terms, ["technology", "innovation"])

    def test_search_index_entry_content_ids_validation(self):
        """Test SearchIndexEntry content IDs validation."""
        entry = SearchIndexEntry(
            query_terms=["technology"],
            content_ids=["  content_001  ", "  content_002  ", ""],  # Empty string should be filtered out
            relevance_scores={"content_001": 0.95, "content_002": 0.88}
        )
        self.assertEqual(entry.content_ids, ["content_001", "content_002"])

    def test_search_index_entry_invalid_relevance_scores(self):
        """Test SearchIndexEntry with invalid relevance scores."""
        with self.assertRaises(ValidationError) as context:
            SearchIndexEntry(
                query_terms=["technology"],
                content_ids=["content_001"],
                relevance_scores={"content_001": 1.5}  # Score > 1.0
            )
        self.assertIn("must be between 0.0 and 1.0", str(context.exception))

    def test_search_index_entry_negative_relevance_scores(self):
        """Test SearchIndexEntry with negative relevance scores."""
        with self.assertRaises(ValidationError) as context:
            SearchIndexEntry(
                query_terms=["technology"],
                content_ids=["content_001"],
                relevance_scores={"content_001": -0.1}  # Score < 0.0
            )
        self.assertIn("must be between 0.0 and 1.0", str(context.exception))

    def test_search_index_entry_valid_relevance_scores(self):
        """Test SearchIndexEntry with valid relevance scores."""
        entry = SearchIndexEntry(
            query_terms=["technology"],
            content_ids=["content_001"],
            relevance_scores={"content_001": 0.0}  # Minimum valid score
        )
        self.assertEqual(entry.relevance_scores, {"content_001": 0.0})


class TestGoogleSearchDB(unittest.TestCase):
    """Test cases for GoogleSearchDB model."""

    def test_google_search_db_valid_data(self):
        """Test GoogleSearchDB with valid data."""
        web_content = {
            "content_001": WebContent(
                url="https://example.com/article1",
                title="Test Article 1",
                snippet="This is a test article",
                content="Full content of the test article"
            )
        }
        
        search_index = {
            "technology": SearchIndexEntry(
                query_terms=["technology"],
                content_ids=["content_001"],
                relevance_scores={"content_001": 0.95}
            )
        }
        
        recent_searches = [
            {"query": "technology trends", "result": "Found 5 articles"},
            {"query": "science news", "result": "Found 3 articles"}
        ]
        
        db = GoogleSearchDB(
            web_content=web_content,
            search_index=search_index,
            recent_searches=recent_searches
        )
        
        self.assertEqual(len(db.web_content), 1)
        self.assertEqual(len(db.search_index), 1)
        self.assertEqual(len(db.recent_searches), 2)

    def test_google_search_db_empty_data(self):
        """Test GoogleSearchDB with empty data."""
        db = GoogleSearchDB()
        
        self.assertEqual(len(db.web_content), 0)
        self.assertEqual(len(db.search_index), 0)
        self.assertEqual(len(db.recent_searches), 0)

    def test_google_search_db_invalid_recent_searches(self):
        """Test GoogleSearchDB with invalid recent searches."""
        with self.assertRaises(ValidationError) as context:
            GoogleSearchDB(
                recent_searches=[
                    {"query": "test"},  # Missing 'result' key
                    {"result": "test"}  # Missing 'query' key
                ]
            )
        self.assertIn("must have \"query\" and \"result\" keys", str(context.exception))

    def test_google_search_db_invalid_recent_searches_type(self):
        """Test GoogleSearchDB with invalid recent searches type."""
        with self.assertRaises(ValidationError) as context:
            GoogleSearchDB(
                recent_searches=[
                    {"query": "test", "result": 123}  # result should be string
                ]
            )
        self.assertIn("Input should be a valid string", str(context.exception))

    def test_google_search_db_valid_recent_searches(self):
        """Test GoogleSearchDB with valid recent searches."""
        db = GoogleSearchDB(
            recent_searches=[
                {"query": "technology trends", "result": "Found 5 articles"},
                {"query": "science news", "result": "Found 3 articles"}
            ]
        )
        
        self.assertEqual(len(db.recent_searches), 2)
        self.assertEqual(db.recent_searches[0]["query"], "technology trends")
        self.assertEqual(db.recent_searches[0]["result"], "Found 5 articles")

    def test_google_search_db_web_content_operations(self):
        """Test GoogleSearchDB web content operations."""
        db = GoogleSearchDB()
        
        # Test add_web_content
        content_id = db.add_web_content(
            url="https://example.com/article",
            title="Test Article",
            snippet="This is a test article",
            content="Full content of the test article",
            publication_time="2024-01-15T10:30:00Z",
            tags=["technology", "innovation"],
            keywords=["tech", "AI"]
        )
        
        self.assertIsNotNone(content_id)
        self.assertIn(content_id, db.web_content)
        
        # Test get_web_content_by_id
        content = db.get_web_content_by_id(content_id)
        self.assertIsNotNone(content)
        self.assertEqual(content.title, "Test Article")
        self.assertEqual(content.url, "https://example.com/article")

    def test_google_search_db_recent_searches_operations(self):
        """Test GoogleSearchDB recent searches operations."""
        db = GoogleSearchDB()
        
        # Test add_recent_search
        db.add_recent_search({"query": "technology trends", "result": "Found 5 articles"})
        db.add_recent_search({"query": "science news", "result": "Found 3 articles"})
        
        # Test get_recent_searches
        recent_searches = db.get_recent_searches()
        self.assertEqual(len(recent_searches), 2)
        self.assertEqual(recent_searches[0]["query"], "science news")  # Most recent first
        self.assertEqual(recent_searches[1]["query"], "technology trends")

    def test_google_search_db_recent_searches_limit(self):
        """Test GoogleSearchDB recent searches limit (50 items)."""
        db = GoogleSearchDB()
        
        # Add more than 50 searches
        for i in range(55):
            db.add_recent_search({"query": f"query_{i}", "result": f"result_{i}"})
        
        # Should only keep 50
        recent_searches = db.get_recent_searches()
        self.assertEqual(len(recent_searches), 50)
        
        # Should keep the most recent ones
        self.assertEqual(recent_searches[0]["query"], "query_54")
        self.assertEqual(recent_searches[49]["query"], "query_5")


if __name__ == "__main__":
    unittest.main()
