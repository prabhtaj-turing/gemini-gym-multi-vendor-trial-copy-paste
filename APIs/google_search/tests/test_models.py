import unittest
from pydantic import ValidationError
from ..SimulationEngine.models import PerQueryResult, SearchResults, SearchResponse, WebContent, SearchIndex, GoogleSearchDB

class TestModels(unittest.TestCase):
    """Test suite for the Pydantic models."""

    def test_per_query_result(self):
        """Test the PerQueryResult model."""
        # Valid data
        PerQueryResult(index="1", snippet="test", source_title="Test Source")
        # Invalid data
        with self.assertRaises(ValidationError):
            PerQueryResult(index="1", snippet="test", source_title="")

    def test_search_results(self):
        """Test the SearchResults model."""
        # Valid data
        SearchResults(query="test", results=[{"index": "1", "snippet": "test", "source_title": "Test Source"}])
        # Invalid data
        with self.assertRaises(ValidationError):
            SearchResults(query="test", results=[])

    def test_search_response(self):
        """Test the SearchResponse model."""
        # Valid data
        SearchResponse(search_results=[{"query": "test", "results": [{"index": "1", "snippet": "test", "source_title": "Test Source"}]}])
        # Invalid data
        with self.assertRaises(ValidationError):
            SearchResponse(search_results=[])

    def test_web_content(self):
        """Test the WebContent model."""
        WebContent(url="http://test.com", title="Test", snippet="test", content="test")

    def test_search_index(self):
        """Test the SearchIndex model."""
        SearchIndex(query_terms=["test"], content_ids=["1"], relevance_scores={"1": 1.0})

    def test_google_search_db(self):
        """Test the GoogleSearchDB model."""
        GoogleSearchDB(
            web_content={"1": {"url": "http://test.com", "title": "Test", "snippet": "test", "content": "test"}},
            search_index={"test": {"query_terms": ["test"], "content_ids": ["1"], "relevance_scores": {"1": 1.0}}},
            recent_searches=["test"]
        )

if __name__ == '__main__':
    unittest.main()
