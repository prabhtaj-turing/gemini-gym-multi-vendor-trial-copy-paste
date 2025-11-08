# test_design_core.py
import pytest
import time
from unittest.mock import patch, MagicMock
from canva.Canva.Design.DesignCreation import create_design
from canva.Canva.Design.DesignListing import list_designs
from canva.Canva.Design.DesignRetrieval import get_design, get_design_pages
from canva.SimulationEngine.custom_errors import InvalidAssetIDError, InvalidTitleError, InvalidDesignIDError, InvalidQueryError, InvalidOwnershipError, InvalidSortByError
from canva.SimulationEngine.db import DB
from pydantic import ValidationError


class TestCreateDesign:
    """Test cases for create_design function"""
    
    def setup_method(self):
        """Reset DB before each test"""
        DB.clear()
        DB["Designs"] = {}
    
    def test_create_design_success(self):
        """Test successful design creation with all parameters"""
        design_type = {"type": "preset", "name": "doc"}
        asset_id = "test_asset_123"
        title = "Test Design"
        
        result = create_design(design_type=design_type, asset_id=asset_id, title=title)
        
        assert "id" in result
        assert result["design_type"] == {"type": "preset", "name": "doc"}
        assert result["asset_id"] == asset_id
        assert result["title"] == title
        assert "created_at" in result
        assert "updated_at" in result
        assert result["id"] in DB["Designs"]
    
    def test_create_design_no_parameters(self):
        """Test creating design with no parameters (all optional)"""
        result = create_design()
        
        assert "id" in result
        assert "created_at" in result
        assert "updated_at" in result
        assert result["title"] == "Untitled Design"  # Default title
        assert result["id"] in DB["Designs"]
    
    def test_create_design_partial_parameters(self):
        """Test creating design with only some parameters"""
        # Only title
        result1 = create_design(title="Just a title")
        assert result1["title"] == "Just a title"
        assert result1["asset_id"] is None
        
        # Only design_type
        result2 = create_design(design_type={"type": "preset", "name": "presentation"})
        assert result2["design_type"] == {"type": "preset", "name": "presentation"}
        assert result2["asset_id"] is None
        assert result2["title"] == "Untitled Design"
        
        # Design_type and title (no asset_id)
        result3 = create_design(design_type={"type": "preset", "name": "whiteboard"}, title="Whiteboard Design")
        assert result3["design_type"] == {"type": "preset", "name": "whiteboard"}
        assert result3["title"] == "Whiteboard Design"
        assert result3["asset_id"] is None
    
    def test_create_design_all_presets(self):
        """Test all valid design type presets"""
        valid_presets = ["doc", "whiteboard", "presentation"]
        
        for preset in valid_presets:
            design_type = {"type": "preset", "name": preset}
            result = create_design(design_type=design_type, asset_id="asset_123", title="Test Title")
            assert result["design_type"]["name"] == preset
            assert result["design_type"]["type"] == "preset"
    
    def test_create_design_invalid_design_type_not_dict(self):
        """Test create_design with non-dict design_type"""
        with pytest.raises(TypeError, match="design_type should be a valid dictionary"):
            create_design(design_type="invalid", asset_id="asset_123", title="Title")
    
    def test_create_design_invalid_asset_id_not_string(self):
        """Test create_design with non-string asset_id"""
        with pytest.raises(TypeError, match="asset_id must be a string"):
            create_design(design_type={"type": "preset", "name": "doc"}, asset_id=123, title="Title")
    
    def test_create_design_empty_asset_id(self):
        """Test create_design with empty asset_id"""
        with pytest.raises(InvalidAssetIDError, match="asset_id cannot be empty"):
            create_design(design_type={"type": "preset", "name": "doc"}, asset_id="", title="Title")
    
    def test_create_design_invalid_title_not_string(self):
        """Test create_design with non-string title"""
        with pytest.raises(TypeError, match="title must be a string"):
            create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset_123", title=123)
    
    def test_create_design_title_too_short(self):
        """Test create_design with title too short"""
        with pytest.raises(InvalidTitleError):
            create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset_123", title="")
    
    def test_create_design_title_too_long(self):
        """Test create_design with title too long"""
        long_title = "a" * 256
        with pytest.raises(InvalidTitleError):
            create_design(design_type={"type": "preset", "name": "doc"}, asset_id="asset_123", title=long_title)
    
    def test_create_design_invalid_preset(self):
        """Test create_design with invalid preset"""
        with pytest.raises(ValidationError):
            create_design(design_type={"type": "preset", "name": "invalid_preset"}, asset_id="asset_123", title="Title")
    
    def test_create_design_optional_validation_errors(self):
        """Test that validation errors only occur when parameters are provided"""
        # Should not raise errors when parameters are None/not provided
        result = create_design()
        assert "id" in result
        
        # Should raise error only when invalid parameter is provided
        with pytest.raises(TypeError, match="asset_id must be a string"):
            create_design(asset_id=123)
        
        with pytest.raises(TypeError, match="title must be a string"):
            create_design(title=123)
        
        with pytest.raises(TypeError, match="design_type should be a valid dictionary"):
            create_design(design_type="invalid")


class TestListDesigns:
    """Test cases for list_designs function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["Designs"] = {
            "design1": {
                "id": "design1",
                "title": "First Design",
                "created_at": 1000000000,
                "updated_at": 1000000000,
                "owner": {"user_id": "user1", "team_id": "team1"}
            },
            "design2": {
                "id": "design2", 
                "title": "Second Design",
                "created_at": 1000000001,
                "updated_at": 1000000001,
                "owner": {"user_id": "user2", "team_id": "team2"}
            },
            "design3": {
                "id": "design3",
                "title": "Third Design Alpha",
                "created_at": 1000000002,
                "updated_at": 1000000002,
                "owner": {"user_id": "user1", "team_id": "team1"}
            }
        }
    
    def test_list_designs_all_default(self):
        """Test listing all designs with default parameters"""
        result = list_designs()
        assert len(result) == 3
        assert all("id" in design for design in result)
    
    def test_list_designs_with_query_filter(self):
        """Test listing designs with query filter"""
        result = list_designs(query="Alpha")
        assert len(result) == 1
        assert result[0]["title"] == "Third Design Alpha"
    
    def test_list_designs_ownership_owned(self):
        """Test listing designs with ownership filter"""
        result = list_designs(ownership="owned")
        # All designs have user_id so all are "owned"
        assert len(result) == 3
    
    def test_list_designs_sort_by_modified_descending(self):
        """Test sorting by modified date descending"""
        result = list_designs(sort_by="modified_descending")
        timestamps = [design["updated_at"] for design in result]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_list_designs_sort_by_title_ascending(self):
        """Test sorting by title ascending"""
        result = list_designs(sort_by="title_ascending")
        titles = [design["title"] for design in result]
        assert titles == sorted(titles)
    
    def test_list_designs_invalid_query_too_long(self):
        """Test list_designs with query too long"""
        long_query = "a" * 256
        with pytest.raises(InvalidQueryError):
            list_designs(query=long_query)
    
    def test_list_designs_invalid_ownership(self):
        """Test list_designs with invalid ownership value"""
        with pytest.raises(InvalidOwnershipError):
            list_designs(ownership="invalid")
    
    def test_list_designs_invalid_sort_by(self):
        """Test list_designs with invalid sort_by value"""
        with pytest.raises(InvalidSortByError):
            list_designs(sort_by="invalid_sort")
    
    def test_list_designs_empty_result(self):
        """Test list_designs when no designs match"""
        result = list_designs(query="nonexistent")
        assert result is None
    
    def test_list_designs_with_semantic_search_id_extraction(self):
        """Test that semantic search results are processed and IDs extracted"""
        # Mock the search engine to return specific structure
        with patch('canva.Canva.Design.DesignListing.search_engine_manager') as mock_manager:
            mock_engine = MagicMock()
            # Return results with different ID structures
            mock_engine.search.return_value = [
                {"id": "design1"},  # Direct ID
                {"metadata": {"design_id": "design2"}},  # Nested in metadata
                {"original_json_obj": {"id": "design3"}}  # In original_json_obj
            ]
            mock_manager.get_engine.return_value = mock_engine
            
            result = list_designs(query="test")
            
            # Should extract IDs from different structures
            if result:
                design_ids = {d["id"] for d in result}
                assert design_ids.issubset({"design1", "design2", "design3"})
    
    def test_list_designs_semantic_search_no_id_found(self):
        """Test semantic search when results have no extractable IDs"""
        with patch('canva.Canva.Design.DesignListing.search_engine_manager') as mock_manager:
            mock_engine = MagicMock()
            # Return results without valid ID fields
            mock_engine.search.return_value = [
                {"invalid_field": "value"},
                {"another_field": "data"}
            ]
            mock_manager.get_engine.return_value = mock_engine
            
            result = list_designs(query="test")
            
            # Should return empty list when no IDs can be extracted
            assert result == [] or result is None
    
    def test_list_designs_semantic_search_empty_results(self):
        """Test semantic search returns empty list"""
        with patch('canva.Canva.Design.DesignListing.search_engine_manager') as mock_manager:
            mock_engine = MagicMock()
            # Search returns empty results
            mock_engine.search.return_value = []
            mock_manager.get_engine.return_value = mock_engine
            
            result = list_designs(query="test")
            
            # Should return empty list
            assert result == [] or result is None
    
    def test_list_designs_semantic_search_none_results(self):
        """Test semantic search returns None"""
        with patch('canva.Canva.Design.DesignListing.search_engine_manager') as mock_manager:
            mock_engine = MagicMock()
            # Search returns None
            mock_engine.search.return_value = None
            mock_manager.get_engine.return_value = mock_engine
            
            result = list_designs(query="test")
            
            # Should return empty or None
            assert result is None or result == []
    
    def test_list_designs_semantic_search_error_fallback(self):
        """Test that search engine errors fall back to substring search"""
        with patch('canva.Canva.Design.DesignListing.search_engine_manager') as mock_manager:
            mock_engine = MagicMock()
            # Simulate search engine error
            mock_engine.search.side_effect = Exception("Search engine error")
            mock_manager.get_engine.return_value = mock_engine
            
            result = list_designs(query="First")
            
            # Should fall back to substring search and find "First Design"
            assert result is not None
            assert len(result) == 1
            assert result[0]["title"] == "First Design"
    
    def test_list_designs_ownership_shared(self):
        """Test filtering for shared designs (no user_id)"""
        # Add a shared design
        DB["Designs"]["design_shared"] = {
            "id": "design_shared",
            "title": "Shared Design",
            "created_at": 1000000003,
            "updated_at": 1000000003,
            "owner": {"team_id": "team1"}  # No user_id
        }
        
        result = list_designs(ownership="shared")
        
        # Should only return designs without user_id
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "design_shared"
        assert result[0]["owner"].get("user_id") is None
    
    def test_list_designs_sort_by_modified_ascending(self):
        """Test sorting by modified date ascending"""
        result = list_designs(sort_by="modified_ascending")
        assert result is not None
        timestamps = [design["updated_at"] for design in result]
        assert timestamps == sorted(timestamps)
    
    def test_list_designs_sort_by_title_descending(self):
        """Test sorting by title descending"""
        result = list_designs(sort_by="title_descending")
        assert result is not None
        titles = [design["title"] for design in result]
        assert titles == sorted(titles, reverse=True)
    
    def test_list_designs_combined_filters(self):
        """Test combining query, ownership, and sorting"""
        with patch('canva.Canva.Design.DesignListing.search_engine_manager') as mock_manager:
            mock_engine = MagicMock()
            mock_engine.search.side_effect = Exception("Fallback to substring")
            mock_manager.get_engine.return_value = mock_engine
            
            result = list_designs(query="Design", ownership="owned", sort_by="title_ascending")
            
            # Should apply all filters
            assert result is not None
            # All should be owned
            for design in result:
                assert design["owner"].get("user_id") is not None
            # Should be sorted by title
            titles = [d["title"] for d in result]
            assert titles == sorted(titles)
    
    def test_list_designs_type_validation(self):
        """Test type validation for all parameters"""
        with pytest.raises(TypeError, match="query must be a string"):
            list_designs(query=123)
        
        with pytest.raises(TypeError, match="ownership must be a string"):
            list_designs(ownership=123)
        
        with pytest.raises(TypeError, match="sort_by must be a string"):
            list_designs(sort_by=123)
    
    def test_list_designs_semantic_search_dict_results(self):
        """Test processing dict results from semantic search"""
        with patch('canva.Canva.Design.DesignListing.search_engine_manager') as mock_manager:
            mock_engine = MagicMock()
            # Return dict results
            mock_engine.search.return_value = [
                {"id": "design1", "title": "First Design"}
            ]
            mock_manager.get_engine.return_value = mock_engine
            
            result = list_designs(query="test")
            
            # Should process dict and extract ID
            assert result is not None or result == []


class TestGetDesign:
    """Test cases for get_design function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["Designs"] = {
            "design1": {
                "id": "design1",
                "title": "Test Design",
                "created_at": 1000000000,
                "updated_at": 1000000000
            }
        }
    
    def test_get_design_success(self):
        """Test successful design retrieval"""
        result = get_design("design1")
        assert result is not None
        assert "design" in result
        assert result["design"]["id"] == "design1"
        assert result["design"]["title"] == "Test Design"
    
    def test_get_design_not_found(self):
        """Test get_design with non-existent design_id"""
        result = get_design("nonexistent")
        assert result is None
    
    def test_get_design_invalid_id_not_string(self):
        """Test get_design with non-string design_id"""
        with pytest.raises(TypeError, match="design_id must be a string"):
            get_design(123)
    
    def test_get_design_empty_id(self):
        """Test get_design with empty design_id"""
        with pytest.raises(InvalidDesignIDError, match="design_id cannot be an empty string"):
            get_design("")


class TestGetDesignPages:
    """Test cases for get_design_pages function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["Designs"] = {
            "design1": {
                "id": "design1",
                "pages": {
                    "page1": {"index": 1, "thumbnail": {"width": 100, "height": 100, "url": "url1"}},
                    "page2": {"index": 2, "thumbnail": {"width": 100, "height": 100, "url": "url2"}},
                    "page3": {"index": 3, "thumbnail": {"width": 100, "height": 100, "url": "url3"}}
                }
            },
            "design2": {
                "id": "design2"
                # No pages key
            }
        }
    
    def test_get_design_pages_success(self):
        """Test successful page retrieval"""
        result = get_design_pages("design1")
        assert result is not None
        assert "pages" in result
        assert len(result["pages"]) == 3
    
    def test_get_design_pages_with_offset_and_limit(self):
        """Test page retrieval with pagination"""
        result = get_design_pages("design1", offset=2, limit=1)
        assert result is not None
        assert len(result["pages"]) == 1
    
    def test_get_design_pages_no_pages(self):
        """Test page retrieval for design without pages"""
        result = get_design_pages("design2")
        assert result is None
    
    def test_get_design_pages_design_not_found(self):
        """Test page retrieval for non-existent design"""
        result = get_design_pages("nonexistent")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
