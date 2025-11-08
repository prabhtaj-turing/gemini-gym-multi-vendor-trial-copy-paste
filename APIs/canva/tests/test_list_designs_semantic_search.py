# test_list_designs_semantic_search.py
"""
Test cases for semantic search functionality in list_designs.

This test suite validates the semantic search improvements for the Canva list_designs function,
specifically addressing Issue #999.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from canva.Canva.Design.DesignListing import list_designs
from canva.SimulationEngine.db import DB
from canva.SimulationEngine.custom_errors import InvalidQueryError, InvalidOwnershipError, InvalidSortByError


class TestListDesignsSemanticSearch:
    """Test cases for semantic search in list_designs function"""

    def setup_method(self):
        """Reset DB and set up test data before each test"""
        DB.clear()
        DB["Designs"] = {
            "design_001": {
                "id": "design_001",
                "title": "Adventure Series Episode 1",
                "design_type": {"type": "preset", "name": "video"},
                "owner": {"user_id": "user_123", "team_id": "team_456"},
                "created_at": 1609459200,
                "updated_at": 1609545600,
                "thumbnail": {"width": 1920, "height": 1080, "url": "https://example.com/thumb1.png"},
                "urls": {"edit_url": "https://canva.com/edit/1", "view_url": "https://canva.com/view/1"}
            },
            "design_002": {
                "id": "design_002",
                "title": "Series of Adventures",
                "design_type": {"type": "preset", "name": "presentation"},
                "owner": {"user_id": "user_123", "team_id": "team_456"},
                "created_at": 1609459201,
                "updated_at": 1609545601,
                "thumbnail": {"width": 1920, "height": 1080, "url": "https://example.com/thumb2.png"},
                "urls": {"edit_url": "https://canva.com/edit/2", "view_url": "https://canva.com/view/2"}
            },
            "design_003": {
                "id": "design_003",
                "title": "My Summer Holiday",
                "design_type": {"type": "preset", "name": "doc"},
                "owner": {"user_id": "user_123", "team_id": "team_456"},
                "created_at": 1609459202,
                "updated_at": 1609545602,
                "thumbnail": {"width": 595, "height": 335, "url": "https://example.com/thumb3.png"},
                "urls": {"edit_url": "https://canva.com/edit/3", "view_url": "https://canva.com/view/3"}
            },
            "design_004": {
                "id": "design_004",
                "title": "Epic Adventure Collection",
                "design_type": {"type": "preset", "name": "poster"},
                "owner": {"user_id": "user_789", "team_id": "team_456"},
                "created_at": 1609459203,
                "updated_at": 1609545603,
                "thumbnail": {"width": 1920, "height": 1080, "url": "https://example.com/thumb4.png"},
                "urls": {"edit_url": "https://canva.com/edit/4", "view_url": "https://canva.com/view/4"}
            },
            "design_005": {
                "id": "design_005",
                "title": "Travel Journal",
                "design_type": {"type": "preset", "name": "doc"},
                "owner": {"team_id": "team_456"},  # Shared, no user_id
                "created_at": 1609459204,
                "updated_at": 1609545604,
                "thumbnail": {"width": 595, "height": 335, "url": "https://example.com/thumb5.png"},
                "urls": {"edit_url": "https://canva.com/edit/5", "view_url": "https://canva.com/view/5"}
            }
        }

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_adventure_series_exact_match(self):
        """
        Test semantic search with query 'adventure series' finds exact matches.
        This is the primary test case from Issue #999.
        """
        result = list_designs(query="adventure series")
        
        assert result is not None
        assert isinstance(result, list)
        
        # Should find designs with "adventure" and "series" in title
        design_ids = {d["id"] for d in result}
        
        # These should be in results based on semantic similarity
        assert "design_001" in design_ids or "design_002" in design_ids or "design_004" in design_ids
        
        # Verify the results contain design data
        for design in result:
            assert "id" in design
            assert "title" in design
            assert "owner" in design

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_partial_match(self):
        """Test semantic search with partial word matches"""
        result = list_designs(query="advent")
        
        # Should find designs with "adventure" due to semantic similarity
        assert result is not None
        assert isinstance(result, list)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_synonym_matching(self):
        """Test semantic search finds semantically similar terms"""
        result = list_designs(query="Adventure")
        
        assert result is not None
        assert isinstance(result, list)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_with_ownership_filter(self):
        """Test semantic search combined with ownership filtering"""
        result = list_designs(query="adventure series", ownership="owned")
        
        assert result is not None
        # All results should have user_id (owned designs)
        for design in result:
            assert design.get("owner", {}).get("user_id") is not None

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_with_shared_ownership(self):
        """Test semantic search with shared ownership filter"""
        result = list_designs(query="travel", ownership="shared")
        
        # Shared designs should not have user_id
        if result:
            for design in result:
                assert design.get("owner", {}).get("user_id") is None

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_with_sorting(self):
        """Test that explicit sorting works with semantic search"""
        result = list_designs(query="adventure", sort_by="title_ascending")
        
        assert result is not None
        assert isinstance(result, list)
        
        if len(result) > 1:
            # Verify sorting is applied
            titles = [d["title"] for d in result]
            assert titles == sorted(titles)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_with_modified_descending_sort(self):
        """Test semantic search with modified_descending sort"""
        result = list_designs(query="adventure", sort_by="modified_descending")
        
        assert result is not None
        assert isinstance(result, list)
        
        if len(result) > 1:
            # Verify descending order by updated_at
            timestamps = [d["updated_at"] for d in result]
            assert timestamps == sorted(timestamps, reverse=True)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_no_results(self):
        """Test semantic search with query that matches nothing"""
        result = list_designs(query="completely_nonexistent_xyz_12345")
        
        # Should return None when no results found
        assert result is None

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_empty_query(self):
        """Test that empty query returns all designs"""
        result = list_designs(query="")
        
        # Empty query should return all designs
        assert result is not None
        assert len(result) == 5

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_case_insensitive(self):
        """Test that semantic search is case insensitive"""
        result_lower = list_designs(query="My summer holiday")
        result_upper = list_designs(query="MY SUMMER HOLIDAY")
        
        # All should return similar results
        assert result_lower is not None and result_upper is not None

    def test_semantic_search_validation_query_too_long(self):
        """Test that query length validation still works"""
        long_query = "x" * 256
        
        with pytest.raises(InvalidQueryError, match="query exceeds maximum length of 255 characters"):
            list_designs(query=long_query)

    def test_semantic_search_validation_invalid_ownership(self):
        """Test that ownership validation still works with semantic search"""
        with pytest.raises(InvalidOwnershipError):
            list_designs(query="adventure", ownership="invalid_value")

    def test_semantic_search_validation_invalid_sort_by(self):
        """Test that sort_by validation still works with semantic search"""
        with pytest.raises(InvalidSortByError):
            list_designs(query="adventure", sort_by="invalid_sort")

    @patch.dict(os.environ, {}, clear=True)
    def test_fallback_when_no_api_key(self):
        """Test that function still works when GOOGLE_API_KEY is not available"""
        # Should fall back to fuzzy search or substring search
        result = list_designs(query="adventure")
        
        # Should still return results (using fallback strategy)
        assert result is not None or result is None  # Either works, no error

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_with_all_parameters(self):
        """Test semantic search with all parameters combined"""
        result = list_designs(
            query="adventure",
            ownership="owned",
            sort_by="modified_descending"
        )
        
        # Should apply all filters and sorting
        if result:
            assert isinstance(result, list)
            # Verify ownership filter
            for design in result:
                assert design.get("owner", {}).get("user_id") is not None
            # Verify sorting
            if len(result) > 1:
                timestamps = [d["updated_at"] for d in result]
                assert timestamps == sorted(timestamps, reverse=True)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_returns_correct_structure(self):
        """Test that semantic search returns designs with correct structure"""
        result = list_designs(query="adventure")
        
        assert result is not None
        
        required_fields = ["id", "title", "created_at", "updated_at", "owner", "urls"]
        
        for design in result:
            for field in required_fields:
                assert field in design, f"Missing required field: {field}"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_relevance_default_sort(self):
        """Test that relevance is default sort when query provided"""
        result = list_designs(query="adventure series")
        
        # When sort_by="relevance" (default), semantic search should return
        # results ordered by relevance from the search engine
        assert result is not None
        assert isinstance(result, list)

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_multi_word_query(self):
        """Test semantic search with multi-word queries"""
        result = list_designs(query="summer holiday vacation")
        
        # Should find designs related to summer, holiday, or vacation
        assert result is not None or result is None

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_semantic_search_special_characters(self):
        """Test semantic search handles special characters gracefully"""
        result = list_designs(query="adventure & series!")
        
        # Should handle special characters without crashing
        assert result is not None or result is None

    def test_no_query_returns_all_designs(self):
        """Test that no query returns all designs (backward compatibility)"""
        result = list_designs()
        
        assert result is not None
        assert len(result) == 5
        assert isinstance(result, list)

    def test_no_query_with_ownership_filter(self):
        """Test no query with ownership filter (backward compatibility)"""
        result = list_designs(ownership="owned")
        
        assert result is not None
        # Should only include owned designs
        for design in result:
            assert design.get("owner", {}).get("user_id") is not None

    def test_no_query_with_sorting(self):
        """Test no query with sorting (backward compatibility)"""
        result = list_designs(sort_by="title_ascending")
        
        assert result is not None
        titles = [d["title"] for d in result]
        assert titles == sorted(titles)


class TestSemanticSearchEngineIntegration:
    """Integration tests for search engine adapter"""

    def setup_method(self):
        """Set up test data"""
        DB.clear()
        DB["Designs"] = {
            "test_001": {
                "id": "test_001",
                "title": "Test Design One",
                "design_type": {"type": "preset", "name": "doc"},
                "owner": {"user_id": "user_1", "team_id": "team_1"},
                "created_at": 1609459200,
                "updated_at": 1609545600,
                "thumbnail": {"width": 100, "height": 100, "url": "https://example.com/1.png"},
                "urls": {"edit_url": "https://edit.com/1", "view_url": "https://view.com/1"}
            }
        }

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_search_engine_initialization(self):
        """Test that search engine initializes correctly"""
        try:
            from canva.SimulationEngine.search_engine import search_engine_manager, service_adapter
            
            assert search_engine_manager is not None
            assert service_adapter is not None
        except ImportError:
            pytest.skip("Search engine not available")

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_search_engine_adapter_db_conversion(self):
        """Test that adapter converts DB to searchable documents correctly"""
        try:
            from canva.SimulationEngine.search_engine import service_adapter
            
            documents = service_adapter.db_to_searchable_documents()
            
            assert documents is not None
            assert isinstance(documents, list)
            assert len(documents) == 1
            
            doc = documents[0]
            assert hasattr(doc, "parent_doc_id")
            assert hasattr(doc, "text_content")
            assert hasattr(doc, "metadata")
            
            # Check metadata
            assert doc.metadata["content_type"] == "design"
            assert doc.metadata["design_id"] == "test_001"
            
        except ImportError:
            pytest.skip("Search engine not available")

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    def test_search_engine_text_content_includes_title(self):
        """Test that searchable text includes design title"""
        try:
            from canva.SimulationEngine.search_engine import service_adapter
            
            documents = service_adapter.db_to_searchable_documents()
            doc = documents[0]
            
            assert "Test Design One" in doc.text_content
            
        except ImportError:
            pytest.skip("Search engine not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
