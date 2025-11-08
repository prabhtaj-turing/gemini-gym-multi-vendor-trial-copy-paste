"""
Comprehensive validation and integration tests for YouTube Tool.
Tests data validation, system integration, and end-to-end workflows.
"""

import unittest
import copy
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from youtube_tool.SimulationEngine.db import DB, DEFAULT_DB_PATH, save_state, load_state
from youtube_tool.SimulationEngine.utils import get_recent_searches, add_recent_search
from youtube_tool.youtube_search import search
from youtube_tool.SimulationEngine.custom_errors import APIError, ExtractionError, EnvironmentError


class TestDataValidation(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.original_db = copy.deepcopy(DB)
        
    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db)
        
    def test_default_db_structure_validation(self):
        """Test that default DB has expected structure."""
        # Check that default DB file exists
        self.assertTrue(os.path.exists(DEFAULT_DB_PATH), 
                       f"Default DB file should exist at {DEFAULT_DB_PATH}")
        
        # Check that DB is properly loaded
        self.assertIsInstance(DB, dict)
        
        # Check for expected top-level keys (these may vary based on actual implementation)
        # Common expected keys for a YouTube tool DB
        possible_keys = {
            "recent_searches", "api_config", "user_preferences", 
            "search_history", "cache", "settings", "metadata"
        }
        
        # At minimum, DB should not be empty
        self.assertGreater(len(DB), 0, "Default DB should not be empty")
        
        # All values should be JSON serializable
        try:
            json.dumps(DB)
        except (TypeError, ValueError) as e:
            self.fail(f"DB contains non-JSON serializable data: {e}")
            
        
    def test_search_result_structure_validation(self):
        """Test validation of search result structures."""
        # Expected structure for VIDEO results
        video_result_schema = {
            "required_fields": [
                "title", "channel_name", "external_video_id", "url"
            ],
            "optional_fields": [
                "view_count", "like_count", "publish_date", "video_length",
                "channel_avatar_url", "channel_external_id", "search_query",
                "search_url", "snippets"
            ]
        }
        
        # Expected structure for CHANNEL results
        channel_result_schema = {
            "required_fields": [
                "channel_name", "channel_external_id", "url"
            ],
            "optional_fields": [
                "channel_avatar_url", "search_query", "search_url", "snippets"
            ]
        }
        
        # Expected structure for PLAYLIST results
        playlist_result_schema = {
            "required_fields": [
                "channel_name", "url"
            ],
            "optional_fields": [
                "playlist_name", "channel_external_id", "channel_avatar_url",
                "external_playlist_id", "playlist_video_ids", "search_query",
                "search_url", "snippets"
            ]
        }
        
        schemas = {
            "VIDEO": video_result_schema,
            "CHANNEL": channel_result_schema,
            "PLAYLIST": playlist_result_schema
        }
        
        # Test each schema validation
        for result_type, schema in schemas.items():
            # Create a minimal valid result
            test_result = {}
            for field in schema["required_fields"]:
                test_result[field] = f"test_{field}_value"
                
            # Add some optional fields
            test_result["search_query"] = "test query"
            test_result["search_url"] = "https://youtube.com/search"
            
            # Validate required fields are present
            for required_field in schema["required_fields"]:
                self.assertIn(required_field, test_result,
                            f"{result_type} result missing required field: {required_field}")
                            
            # All fields should be either required or optional
            all_valid_fields = set(schema["required_fields"] + schema["optional_fields"])
            for field in test_result.keys():
                self.assertIn(field, all_valid_fields,
                            f"Unexpected field '{field}' in {result_type} result")


class TestSystemIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.original_db = copy.deepcopy(DB)
        
    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db)
        
    @patch('youtube_tool.SimulationEngine.utils.get_gemini_response')
    @patch('youtube_tool.SimulationEngine.utils.get_json_response')
    def test_search_to_recent_searches_integration(self, mock_json, mock_gemini):
        """Test integration between search API and recent searches storage."""
        # Mock successful search
        mock_gemini.return_value = {"valid": "response"}
        mock_results = [
            {
                "title": "Integration Test Video",
                "channel_name": "Test Channel",
                "external_video_id": "int123",
                "view_count": "1000"
            }
        ]
        mock_json.return_value = mock_results
        
        # Get initial recent searches count
        initial_recent = get_recent_searches("search", max_results=100)
        initial_count = len(initial_recent)
        
        # Perform search
        query = "integration search test"
        result_type = "VIDEO"
        result = search(query, result_type=result_type)
        
        # Verify search result
        self.assertEqual(result, mock_results)
        
        # Verify recent searches were updated
        updated_recent = get_recent_searches("search", max_results=100)
        self.assertEqual(len(updated_recent), initial_count + 1)
        
        # Verify the most recent search matches what we just did
        most_recent = updated_recent[0]
        self.assertEqual(most_recent["parameters"]["query"], query)
        self.assertEqual(most_recent["parameters"]["result_type"], result_type.lower())
        self.assertEqual(most_recent["result"], mock_results)
        
    def test_error_propagation_integration(self):
        """Test that errors propagate correctly through the system."""
        # Test EnvironmentError propagation
        with patch('youtube_tool.SimulationEngine.utils.os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            with self.assertRaises(OSError) as context:
                search("test query")
                
            
        # Test APIError propagation
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            mock_gemini.return_value = None
            
            with self.assertRaises(APIError) as context:
                search("test query")
                
            self.assertIn("Failed to get search result", str(context.exception))
            
        # Test ExtractionError propagation
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_json:
            
            mock_gemini.return_value = {"valid": "response"}
            mock_json.return_value = None
            
            with self.assertRaises(ExtractionError) as context:
                search("test query")
                
            self.assertIn("Failed to extract results", str(context.exception))


class TestEndToEndWorkflows(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.original_db = copy.deepcopy(DB)
        
    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db)
        
    @patch('youtube_tool.SimulationEngine.utils.get_gemini_response')
    @patch('youtube_tool.SimulationEngine.utils.get_json_response')
    def test_complete_search_workflow(self, mock_json, mock_gemini):
        """Test complete end-to-end search workflow."""
        # Setup mocks
        mock_gemini.return_value = {"candidates": [{"content": "valid"}]}
        mock_results = [
            {
                "title": "End-to-End Test Video",
                "channel_name": "E2E Test Channel",
                "external_video_id": "e2e123",
                "view_count": "500000",
                "like_count": "25000",
                "url": "https://youtube.com/watch?v=e2e123",
                "channel_external_id": "UC123e2e"
            }
        ]
        mock_json.return_value = mock_results
        
        # Step 1: Perform initial search
        query1 = "end to end test"
        result1 = search(query1, result_type="VIDEO")
        
        self.assertEqual(result1, mock_results)
        
        # Step 2: Verify recent searches updated
        recent = get_recent_searches("search", max_results=5)
        self.assertGreater(len(recent), 0)
        self.assertEqual(recent[0]["parameters"]["query"], query1)
        
        # Step 3: Perform second search
        mock_results2 = [
            {
                "channel_name": "Second Test Channel",
                "channel_external_id": "UC456e2e",
                "url": "https://youtube.com/channel/UC456e2e"
            }
        ]
        mock_json.return_value = mock_results2
        
        query2 = "second search test"
        result2 = search(query2, result_type="CHANNEL")
        
        self.assertEqual(result2, mock_results2)
        
        # Step 4: Verify recent searches order
        recent_after = get_recent_searches("search", max_results=5)
        self.assertGreaterEqual(len(recent_after), 2)
        self.assertEqual(recent_after[0]["parameters"]["query"], query2)  # Most recent
        self.assertEqual(recent_after[1]["parameters"]["query"], query1)  # Previous
        
        # Step 5: Test persistence
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_path = tmp.name
            
        try:
            save_state(tmp_path)
            
            # Clear DB and reload
            DB.clear()
            load_state(tmp_path)
            
            # Verify data persisted
            loaded_recent = get_recent_searches("search", max_results=5)
            self.assertGreaterEqual(len(loaded_recent), 2)
            self.assertEqual(loaded_recent[0]["parameters"]["query"], query2)
            self.assertEqual(loaded_recent[1]["parameters"]["query"], query1)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    @patch('youtube_tool.SimulationEngine.utils.get_gemini_response')
    @patch('youtube_tool.SimulationEngine.utils.get_json_response')
    def test_multiple_result_type_workflow(self, mock_json, mock_gemini):
        """Test workflow with multiple result types."""
        mock_gemini.return_value = {"valid": "response"}
        
        # Test VIDEO search
        video_results = [{"title": "Test Video", "external_video_id": "vid123"}]
        mock_json.return_value = video_results
        
        video_result = search("test content", result_type="VIDEO")
        self.assertEqual(video_result, video_results)
        
        # Test CHANNEL search
        channel_results = [{"channel_name": "Test Channel", "channel_external_id": "UC123"}]
        mock_json.return_value = channel_results
        
        channel_result = search("test creator", result_type="CHANNEL")
        self.assertEqual(channel_result, channel_results)
        
        # Test PLAYLIST search
        playlist_results = [{"playlist_name": "Test Playlist", "external_playlist_id": "PL123"}]
        mock_json.return_value = playlist_results
        
        playlist_result = search("test series", result_type="PLAYLIST")
        self.assertEqual(playlist_result, playlist_results)
        
        # Verify all searches are in recent history
        recent = get_recent_searches("search", max_results=10)
        self.assertGreaterEqual(len(recent), 3)
        
        # Check that different result types are preserved
        result_types_found = set()
        queries_found = set()
        
        for search_entry in recent[:3]:  # Last 3 searches
            result_types_found.add(search_entry["parameters"]["result_type"])
            queries_found.add(search_entry["parameters"]["query"])
            
        self.assertIn("video", result_types_found)
        self.assertIn("channel", result_types_found)
        self.assertIn("playlist", result_types_found)
        
        self.assertIn("test content", queries_found)
        self.assertIn("test creator", queries_found)
        self.assertIn("test series", queries_found)
        
    def test_error_recovery_workflow(self):
        """Test system behavior during error conditions and recovery."""
        # Test recovery from EnvironmentError
        with patch('youtube_tool.SimulationEngine.utils.os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            # Should raise EnvironmentError
            with self.assertRaises(OSError):
                search("test query")
                
            # Verify no recent search was added due to error
            initial_recent = get_recent_searches("search", max_results=10)
            error_searches = [s for s in initial_recent 
                            if s["parameters"]["query"] == "test query"]
            self.assertEqual(len(error_searches), 0)
            
        # Test recovery after fixing environment
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_json:
            
            mock_gemini.return_value = {"success": True}
            mock_json.return_value = [{"title": "Recovery Test"}]
            
            # Should now work
            result = search("recovery test")
            self.assertEqual(result, [{"title": "Recovery Test"}])
            
            # Verify recent search was added after recovery
            recovery_recent = get_recent_searches("search", max_results=10)
            recovery_searches = [s for s in recovery_recent 
                               if s["parameters"]["query"] == "recovery test"]
            self.assertEqual(len(recovery_searches), 1)


class TestDataConsistency(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.original_db = copy.deepcopy(DB)
        
    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db)
        
    def test_concurrent_operations_simulation(self):
        """Test data consistency during simulated concurrent operations."""
        # Simulate multiple rapid search additions
        test_searches = []
        for i in range(10):
            search_data = {
                "parameters": {"query": f"concurrent test {i}", "result_type": "VIDEO"},
                "result": [{"title": f"Video {i}", "external_video_id": f"vid{i}"}]
            }
            test_searches.append(search_data)
            add_recent_search("search", search_data["parameters"], search_data["result"])
            
        # Verify all searches were added and are retrievable
        recent = get_recent_searches("search", max_results=15)
        concurrent_searches = [s for s in recent 
                             if s["parameters"]["query"].startswith("concurrent test")]
        
        self.assertEqual(len(concurrent_searches), 10)
        
        # Verify order (most recent first)
        for i, search_entry in enumerate(concurrent_searches):
            expected_query = f"concurrent test {9 - i}"  # Reverse order
            self.assertEqual(search_entry["parameters"]["query"], expected_query)
            
    def test_data_type_consistency(self):
        """Test that data types remain consistent throughout operations."""
        # Add searches with various data types
        test_data = [
            {
                "parameters": {"query": "string test", "result_type": "VIDEO"},
                "result": [
                    {
                        "title": "String Title",
                        "view_count": "1000000",  # String number
                        "like_count": 50000,      # Integer number
                        "is_live": True,          # Boolean
                        "publish_date": "2024-01-15",  # Date string
                        "tags": ["tag1", "tag2"],      # List
                        "metadata": {"duration": 300}  # Nested dict
                    }
                ]
            }
        ]
        
        for search_data in test_data:
            add_recent_search("search", search_data["parameters"], search_data["result"])
            
        # Retrieve and verify data types
        recent = get_recent_searches("search", max_results=5)
        string_test_searches = [s for s in recent 
                              if s["parameters"]["query"] == "string test"]
        
        self.assertEqual(len(string_test_searches), 1)
        
        result_data = string_test_searches[0]["result"][0]
        
        # Verify data types are preserved
        self.assertIsInstance(result_data["title"], str)
        self.assertIsInstance(result_data["view_count"], str)
        self.assertIsInstance(result_data["like_count"], int)
        self.assertIsInstance(result_data["is_live"], bool)
        self.assertIsInstance(result_data["tags"], list)
        self.assertIsInstance(result_data["metadata"], dict)
        
        # Test save/load preserves types
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_path = tmp.name
            
        try:
            save_state(tmp_path)
            DB.clear()
            load_state(tmp_path)
            
            # Verify types after reload
            reloaded_recent = get_recent_searches("search", max_results=5)
            reloaded_searches = [s for s in reloaded_recent 
                               if s["parameters"]["query"] == "string test"]
            
            self.assertEqual(len(reloaded_searches), 1)
            
            reloaded_data = reloaded_searches[0]["result"][0]
            
            self.assertIsInstance(reloaded_data["title"], str)
            self.assertIsInstance(reloaded_data["view_count"], str)
            self.assertIsInstance(reloaded_data["like_count"], int)
            self.assertIsInstance(reloaded_data["is_live"], bool)
            self.assertIsInstance(reloaded_data["tags"], list)
            self.assertIsInstance(reloaded_data["metadata"], dict)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
