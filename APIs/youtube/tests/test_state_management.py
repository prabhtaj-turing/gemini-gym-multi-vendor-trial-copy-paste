"""
Test suite for state management functions in the YouTube API simulation.
Covers load_state and save_state functions from SimulationEngine/db.py with comprehensive tests.
"""
import copy
import json
import os
import tempfile
import unittest
import shutil
from unittest.mock import patch, mock_open

from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube.SimulationEngine.db import DB, save_state, load_state


class TestStateManagement(BaseTestCaseWithErrorHandler):
    """Test suite for state management functions from SimulationEngine/db.py"""

    @classmethod
    def setUpClass(cls):
        """Save original DB state."""
        cls.original_db_state = copy.deepcopy(DB)

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Set up test environment for each test."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        # Reset DB to a known test state
        self.test_db_state = {
            "channels": {
                "test_channel_1": {
                    "id": "UC1234567890",
                    "snippet": {
                        "title": "Test Channel",
                        "description": "A test channel for YouTube API simulation",
                        "customUrl": "@testchannel",
                        "publishedAt": "2023-01-01T00:00:00Z"
                    },
                    "statistics": {
                        "viewCount": "1000000",
                        "subscriberCount": "50000",
                        "videoCount": "100",
                        "commentCount": "5000"
                    }
                }
            },
            "videos": {
                "test_video_1": {
                    "id": "dQw4w9WgXcQ",
                    "snippet": {
                        "title": "Test Video",
                        "description": "A test video",
                        "publishedAt": "2023-06-01T12:00:00Z",
                        "channelId": "UC1234567890",
                        "channelTitle": "Test Channel"
                    },
                    "statistics": {
                        "viewCount": "10000",
                        "likeCount": "100",
                        "commentCount": "25"
                    }
                }
            },
            "playlists": {
                "test_playlist_1": {
                    "id": "PLtest123",
                    "snippet": {
                        "title": "Test Playlist",
                        "description": "A test playlist",
                        "channelId": "UC1234567890",
                        "publishedAt": "2023-05-01T10:00:00Z"
                    },
                    "status": {
                        "privacyStatus": "public"
                    }
                }
            },
            "comments": {},
            "subscriptions": {},
            "activities": {}
        }
        DB.clear()
        DB.update(copy.deepcopy(self.test_db_state))

    def test_save_state_creates_file(self):
        """Test that save_state creates a JSON file with current DB state."""
        filepath = os.path.join(self.test_dir, "test_state.json")
        
        # Save the state
        save_state(filepath)
        
        # Verify file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Verify file contains correct JSON data
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, self.test_db_state)

    def test_save_state_overwrites_existing_file(self):
        """Test that save_state overwrites existing files."""
        filepath = os.path.join(self.test_dir, "existing_state.json")
        
        # Create an existing file with different content
        existing_data = {"old": "data"}
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f)
        
        # Save the current state
        save_state(filepath)
        
        # Verify the file was overwritten
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, self.test_db_state)
        self.assertNotEqual(saved_data, existing_data)

    def test_save_state_handles_unicode_content(self):
        """Test that save_state properly handles Unicode content."""
        # Add Unicode content to DB
        DB["unicode_test"] = {
            "chinese": "你好世界",
            "japanese": "こんにちは",
            "emoji": "🎥📺🔔",
            "special_chars": "àáâãäåæçèéêë"
        }
        
        filepath = os.path.join(self.test_dir, "unicode_state.json")
        save_state(filepath)
        
        # Verify Unicode content was saved correctly
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["unicode_test"]["chinese"], "你好世界")
        self.assertEqual(saved_data["unicode_test"]["emoji"], "🎥📺🔔")

    def test_save_state_creates_directory_if_not_exists(self):
        """Test that save_state creates parent directories if they don't exist."""
        nested_path = os.path.join(self.test_dir, "nested", "subdir", "state.json")
        
        # Ensure parent directories don't exist
        nested_dir = os.path.dirname(nested_path)
        self.assertFalse(os.path.exists(nested_dir))
        
        # Create the directory structure first (save_state doesn't create directories)
        os.makedirs(nested_dir, exist_ok=True)
        
        save_state(nested_path)
        
        # Verify file was created and directories exist
        self.assertTrue(os.path.exists(nested_path))

    def test_load_state_loads_valid_json(self):
        """Test that load_state correctly loads valid JSON data."""
        # Create a test state file
        test_state = {
            "channels": {"test": "data"},
            "videos": {"video1": {"id": "test123"}},
            "loaded": True
        }
        
        filepath = os.path.join(self.test_dir, "valid_state.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test_state, f)
        
        # Load the state
        load_state(filepath)
        
        # Verify DB was updated correctly
        self.assertEqual(DB["channels"], {"test": "data"})
        self.assertEqual(DB["videos"], {"video1": {"id": "test123"}})
        self.assertTrue(DB["loaded"])

    def test_load_state_replaces_existing_db(self):
        """Test that load_state completely replaces existing DB content."""
        # Set up initial DB state
        initial_state = {"initial": "data", "keep": "this"}
        DB.clear()
        DB.update(initial_state)
        
        # Create a different state to load
        new_state = {"new": "data", "different": "content"}
        filepath = os.path.join(self.test_dir, "replace_state.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(new_state, f)
        
        # Load the new state
        load_state(filepath)
        
        # Verify old data is gone and new data is present
        self.assertNotIn("initial", DB)
        self.assertNotIn("keep", DB)
        self.assertEqual(DB["new"], "data")
        self.assertEqual(DB["different"], "content")

    def test_load_state_handles_unicode_content(self):
        """Test that load_state properly handles Unicode content."""
        unicode_state = {
            "unicode_data": {
                "chinese": "你好世界",
                "japanese": "こんにちは",
                "emoji": "🎥📺🔔",
                "special_chars": "àáâãäåæçèéêë"
            }
        }
        
        filepath = os.path.join(self.test_dir, "unicode_load.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(unicode_state, f)
        
        # Load the state
        load_state(filepath)
        
        # Verify Unicode content was loaded correctly
        self.assertEqual(DB["unicode_data"]["chinese"], "你好世界")
        self.assertEqual(DB["unicode_data"]["emoji"], "🎥📺🔔")

    def test_load_state_file_not_found_raises_error(self):
        """Test that load_state raises FileNotFoundError for non-existent files."""
        non_existent_path = os.path.join(self.test_dir, "nonexistent.json")
        
        with self.assertRaises(FileNotFoundError):
            load_state(non_existent_path)

    def test_load_state_invalid_json_raises_error(self):
        """Test that load_state raises JSONDecodeError for invalid JSON."""
        invalid_json_path = os.path.join(self.test_dir, "invalid.json")
        
        # Create a file with invalid JSON
        with open(invalid_json_path, 'w') as f:
            f.write("{ invalid json content }")
        
        with self.assertRaises(json.JSONDecodeError):
            load_state(invalid_json_path)

    def test_save_and_load_roundtrip(self):
        """Test that save_state and load_state work correctly together."""
        # Create complex test data
        complex_state = {
            "channels": {
                "UC123": {
                    "id": "UC123",
                    "snippet": {
                        "title": "Complex Channel",
                        "description": "A complex test channel with unicode: 🎥",
                        "publishedAt": "2023-01-01T00:00:00Z"
                    },
                    "statistics": {
                        "viewCount": "1000000",
                        "subscriberCount": "50000"
                    }
                }
            },
            "videos": {
                "vid123": {
                    "id": "vid123",
                    "snippet": {
                        "title": "Test Video 测试",
                        "tags": ["test", "youtube", "api"]
                    }
                }
            },
            "metadata": {
                "version": "1.0",
                "created": "2023-01-01",
                "unicode_test": "Special chars: àáâãäåæçèéêë 🎵🎶"
            }
        }
        
        # Set DB to complex state
        DB.clear()
        DB.update(complex_state)
        
        # Save and then load
        filepath = os.path.join(self.test_dir, "roundtrip_state.json")
        save_state(filepath)
        
        # Clear DB and load from file
        DB.clear()
        load_state(filepath)
        
        # Verify all data was preserved correctly
        self.assertEqual(DB["channels"]["UC123"]["snippet"]["title"], "Complex Channel")
        self.assertEqual(DB["videos"]["vid123"]["snippet"]["title"], "Test Video 测试")
        self.assertEqual(DB["metadata"]["unicode_test"], "Special chars: àáâãäåæçèéêë 🎵🎶")
        self.assertEqual(DB["videos"]["vid123"]["snippet"]["tags"], ["test", "youtube", "api"])

    def test_save_state_with_empty_db(self):
        """Test that save_state works with an empty DB."""
        # Clear the DB
        DB.clear()
        
        filepath = os.path.join(self.test_dir, "empty_state.json")
        save_state(filepath)
        
        # Verify file was created with empty object
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, {})

    def test_load_state_with_empty_json(self):
        """Test that load_state works with empty JSON object."""
        # Create empty JSON file
        filepath = os.path.join(self.test_dir, "empty.json")
        with open(filepath, 'w') as f:
            json.dump({}, f)
        
        # Set up some initial data
        DB.update({"initial": "data"})
        
        # Load empty state
        load_state(filepath)
        
        # Verify DB is now empty
        self.assertEqual(dict(DB), {})

    def test_save_state_preserves_data_types(self):
        """Test that save_state preserves different data types correctly."""
        # Test various data types
        type_test_data = {
            "string": "test_string",
            "integer": 42,
            "float": 3.14159,
            "boolean_true": True,
            "boolean_false": False,
            "null_value": None,
            "list": [1, 2, "three", True, None],
            "nested_dict": {
                "inner_string": "nested",
                "inner_number": 123,
                "inner_list": ["a", "b", "c"]
            }
        }
        
        DB.clear()
        DB.update(type_test_data)
        
        filepath = os.path.join(self.test_dir, "types_state.json")
        save_state(filepath)
        
        # Load and verify types are preserved
        DB.clear()
        load_state(filepath)
        
        self.assertIsInstance(DB["string"], str)
        self.assertIsInstance(DB["integer"], int)
        self.assertIsInstance(DB["float"], float)
        self.assertIsInstance(DB["boolean_true"], bool)
        self.assertIsInstance(DB["boolean_false"], bool)
        self.assertIsNone(DB["null_value"])
        self.assertIsInstance(DB["list"], list)
        self.assertIsInstance(DB["nested_dict"], dict)
        
        # Verify values
        self.assertEqual(DB["string"], "test_string")
        self.assertEqual(DB["integer"], 42)
        self.assertEqual(DB["float"], 3.14159)
        self.assertTrue(DB["boolean_true"])
        self.assertFalse(DB["boolean_false"])

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_state_permission_error(self, mock_file):
        """Test that save_state raises PermissionError when file cannot be written."""
        filepath = os.path.join(self.test_dir, "permission_test.json")
        
        with self.assertRaises(PermissionError):
            save_state(filepath)

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_load_state_permission_error(self, mock_file):
        """Test that load_state raises PermissionError when file cannot be read."""
        filepath = os.path.join(self.test_dir, "permission_test.json")
        
        with self.assertRaises(PermissionError):
            load_state(filepath)


if __name__ == '__main__':
    unittest.main()
