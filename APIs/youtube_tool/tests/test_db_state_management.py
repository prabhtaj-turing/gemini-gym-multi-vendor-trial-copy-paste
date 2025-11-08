"""
Comprehensive tests for YouTube Tool SimulationEngine DB state management.
Tests save_state, load_state functions and DB structure validation.
"""

import unittest
import tempfile
import os
import json
import copy
from youtube_tool.SimulationEngine.db import DB, save_state, load_state, DEFAULT_DB_PATH


class TestDBStateManagement(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        # Save original DB state
        self.original_db_state = copy.deepcopy(DB)
        
    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db_state)
        
    def test_default_db_loading(self):
        """Test that default DB is loaded correctly."""
        # Check that DEFAULT_DB_PATH exists
        self.assertTrue(os.path.exists(DEFAULT_DB_PATH), 
                       f"Default DB file should exist at {DEFAULT_DB_PATH}")
        
        # Check that DB is loaded with content
        self.assertIsInstance(DB, dict)
        self.assertGreater(len(DB), 0, "DB should have content from default file")
        
    def test_save_state_creates_file(self):
        """Test that save_state creates a file with correct content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_path = tmp.name
            
        try:
            # Add some test data
            DB["test_searches"] = [
                {"query": "test video", "result_type": "VIDEO", "results": []}
            ]
            DB["recent_searches"] = {
                "search": [
                    {"parameters": {"query": "test", "result_type": "video"}, "result": []}
                ]
            }
            
            # Save state
            save_state(tmp_path)
            
            # Verify file exists and has correct content
            self.assertTrue(os.path.exists(tmp_path))
            
            with open(tmp_path, 'r') as f:
                saved_data = json.load(f)
                
            self.assertIn("test_searches", saved_data)
            self.assertIn("recent_searches", saved_data)
            self.assertEqual(saved_data["test_searches"][0]["query"], "test video")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    def test_load_state_restores_data(self):
        """Test that load_state correctly restores data."""
        test_data = {
            "recent_searches": {
                "search": [
                    {
                        "parameters": {"query": "Python tutorial", "result_type": "VIDEO"},
                        "result": [
                            {
                                "title": "Learn Python",
                                "channel_name": "TechEd",
                                "external_video_id": "abc123",
                                "view_count": "1000000",
                                "like_count": "50000"
                            }
                        ]
                    }
                ]
            },
            "api_config": {
                "max_results": 50,
                "timeout": 30
            },
            "user_preferences": {
                "default_result_type": "VIDEO",
                "save_history": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            json.dump(test_data, tmp)
            tmp_path = tmp.name
            
        try:
            # Load state
            load_state(tmp_path)
            
            # Verify data was loaded correctly
            self.assertIn("recent_searches", DB)
            self.assertIn("api_config", DB)
            self.assertIn("user_preferences", DB)
            
            search_data = DB["recent_searches"]["search"][0]
            self.assertEqual(search_data["parameters"]["query"], "Python tutorial")
            self.assertEqual(search_data["result"][0]["title"], "Learn Python")
            
            self.assertEqual(DB["api_config"]["max_results"], 50)
            self.assertEqual(DB["user_preferences"]["default_result_type"], "VIDEO")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    def test_save_load_roundtrip(self):
        """Test that save/load roundtrip preserves data integrity."""
        # Set up complex test data with unicode
        DB["recent_searches"] = {
            "search": [
                {
                    "parameters": {"query": "测试视频", "result_type": "VIDEO"},
                    "result": [
                        {
                            "title": "Python教程 - 基础编程",
                            "channel_name": "编程学习频道",
                            "external_video_id": "xyz789",
                            "view_count": "500000",
                            "like_count": "25000",
                            "publish_date": "2024-01-15",
                            "video_length": "15:30"
                        }
                    ]
                },
                {
                    "parameters": {"query": "machine learning", "result_type": "PLAYLIST"},
                    "result": [
                        {
                            "playlist_name": "ML Course 2024",
                            "channel_name": "AI Academy", 
                            "external_playlist_id": "PLxyz123",
                            "playlist_video_ids": ["vid1", "vid2", "vid3"]
                        }
                    ]
                }
            ]
        }
        
        original_data = copy.deepcopy(DB)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_path = tmp.name
            
        try:
            # Save and load
            save_state(tmp_path)
            
            # Clear DB and reload
            DB.clear()
            load_state(tmp_path)
            
            # Verify data integrity
            self.assertEqual(DB, original_data)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    def test_save_state_overwrites_existing_file(self):
        """Test that save_state overwrites existing files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            # Write initial data
            initial_data = {"old_data": "should_be_overwritten"}
            json.dump(initial_data, tmp)
            tmp_path = tmp.name
            
        try:
            # Add test data to DB
            DB["new_searches"] = [{"query": "new search", "result_type": "CHANNEL"}]
            
            # Save state (should overwrite)
            save_state(tmp_path)
            
            # Verify file was overwritten
            with open(tmp_path, 'r') as f:
                saved_data = json.load(f)
                
            self.assertNotIn("old_data", saved_data)
            self.assertIn("new_searches", saved_data)
            self.assertEqual(saved_data["new_searches"][0]["query"], "new search")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    def test_save_state_creates_directory_if_not_exists(self):
        """Test that save_state works when parent directories exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "nested", "dir")
            file_path = os.path.join(nested_dir, "test_db.json")
            
            # Create directory first
            os.makedirs(nested_dir, exist_ok=True)
            
            # Add test data
            DB["test_data"] = {"api_calls": 100, "last_search": "test query"}
            
            # Save state
            save_state(file_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(file_path))
            
            with open(file_path, 'r') as f:
                saved_data = json.load(f)
                
            self.assertEqual(saved_data["test_data"]["api_calls"], 100)
            self.assertEqual(saved_data["test_data"]["last_search"], "test query")
      
                
    def test_empty_db_save_load(self):
        """Test saving and loading minimal DB structure."""
        # Clear all data
        DB.clear()
        
        # Add minimal structure
        DB["recent_searches"] = {}
        DB["api_stats"] = {"total_calls": 0}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_path = tmp.name
            
        try:
            save_state(tmp_path)
            
            # Clear and reload
            DB.clear()
            load_state(tmp_path)
            
            # Verify minimal structure is preserved
            self.assertIn("recent_searches", DB)
            self.assertIn("api_stats", DB)
            self.assertEqual(DB["api_stats"]["total_calls"], 0)
            self.assertIsInstance(DB["recent_searches"], dict)
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    def test_load_state_file_not_found(self):
        """Test that load_state raises appropriate error for missing file."""
        non_existent_path = "/path/that/does/not/exist.json"
        
        with self.assertRaises(FileNotFoundError):
            load_state(non_existent_path)
            
    def test_load_state_invalid_json(self):
        """Test that load_state raises appropriate error for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp.write("invalid json content {")
            tmp_path = tmp.name
            
        try:
            with self.assertRaises(json.JSONDecodeError):
                load_state(tmp_path)
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    def test_db_persistence_across_operations(self):
        """Test that DB changes persist correctly."""
        original_size = len(DB)
        
        # Add new data
        DB["test_persistence"] = {
            "searches": ["query1", "query2", "query3"],
            "metadata": {"created": "2024-01-01", "version": "1.0"}
        }
        
        # Verify data was added
        self.assertEqual(len(DB), original_size + 1)
        self.assertIn("test_persistence", DB)
        self.assertEqual(len(DB["test_persistence"]["searches"]), 3)
        
        # Modify existing data
        DB["test_persistence"]["searches"].append("query4")
        DB["test_persistence"]["metadata"]["version"] = "1.1"
        
        # Verify modifications
        self.assertEqual(len(DB["test_persistence"]["searches"]), 4)
        self.assertEqual(DB["test_persistence"]["metadata"]["version"], "1.1")
        
    def test_concurrent_db_operations_simulation(self):
        """Test simulating concurrent DB operations."""
        # Simulate multiple search operations adding to recent_searches
        if "recent_searches" not in DB:
            DB["recent_searches"] = {}
        if "search" not in DB["recent_searches"]:
            DB["recent_searches"]["search"] = []
            
        # Add multiple search results
        for i in range(5):
            search_entry = {
                "parameters": {"query": f"test query {i}", "result_type": "VIDEO"},
                "result": [{"title": f"Video {i}", "external_video_id": f"vid{i}"}]
            }
            DB["recent_searches"]["search"].insert(0, search_entry)
            
        # Verify all searches were added
        self.assertEqual(len(DB["recent_searches"]["search"]), 5)
        
        # Verify order (most recent first)
        self.assertEqual(DB["recent_searches"]["search"][0]["parameters"]["query"], "test query 4")
        self.assertEqual(DB["recent_searches"]["search"][4]["parameters"]["query"], "test query 0")
        
        # Test save/load with this data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_path = tmp.name
            
        try:
            save_state(tmp_path)
            
            # Simulate another operation modifying DB
            DB["recent_searches"]["search"].insert(0, {
                "parameters": {"query": "latest query", "result_type": "CHANNEL"},
                "result": []
            })
            
            # Load previous state (simulating reload)
            load_state(tmp_path)
            
            # Verify the latest query is not present (was overwritten by load)
            first_query = DB["recent_searches"]["search"][0]["parameters"]["query"]
            self.assertNotEqual(first_query, "latest query")
            self.assertEqual(first_query, "test query 4")
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
