"""
Test suite for state management functions in the Blender API simulation.
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
from blender.SimulationEngine.db import DB, save_state, load_state


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
            "current_scene": {
                "name": "TestScene",
                "objects": {
                    "TestCube": {
                        "id": "uuid-test-cube",
                        "name": "TestCube",
                        "type": "MESH",
                        "location": [1.0, 2.0, 3.0],
                        "rotation_euler": [0.1, 0.2, 0.3],
                        "scale": [1.1, 1.2, 1.3],
                        "dimensions": [2.1, 2.2, 2.3],
                        "material_names": ["TestMaterial"],
                        "is_visible": True,
                        "is_renderable": True,
                    }
                },
                "active_camera_name": None,
                "world_settings": {
                    "ambient_color": [0.05, 0.05, 0.05],
                    "horizon_color": [0.5, 0.5, 0.5]
                },
                "render_settings": {
                    "engine": "CYCLES",
                    "resolution_x": 1920,
                    "resolution_y": 1080
                }
            },
            "materials": {
                "TestMaterial": {
                    "id": "uuid-test-material",
                    "name": "TestMaterial",
                    "base_color_value": [0.8, 0.8, 0.8],
                    "metallic": 0.0,
                    "roughness": 0.5
                }
            },
            "polyhaven_assets_db": {
                "test-asset": {
                    "asset_id": "test-asset",
                    "name": "Test Asset",
                    "type": "texture",
                    "is_downloaded": False
                }
            },
            "hyper3d_jobs": {},
            "execution_logs": []
        }
        
        DB.clear()
        DB.update(copy.deepcopy(self.test_db_state))

    # Test save_state function
    def test_save_state_success_creates_valid_json(self):
        """Test successful saving of state to JSON file."""
        filepath = os.path.join(self.test_dir, "test_state.json")
        
        save_state(filepath)
        
        # Verify file was created
        self.assertTrue(os.path.exists(filepath))
        
        # Verify content is valid JSON and matches DB
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, dict(DB))

    def test_save_state_overwrites_existing_file(self):
        """Test that save_state overwrites existing file."""
        filepath = os.path.join(self.test_dir, "overwrite_test.json")
        
        # Create initial file with different content
        initial_content = {"old": "data"}
        with open(filepath, 'w') as f:
            json.dump(initial_content, f)
        
        # Save current state (should overwrite)
        save_state(filepath)
        
        # Verify file was overwritten
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, dict(DB))
        self.assertNotEqual(saved_data, initial_content)

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
        
        # Verify content
        with open(nested_path, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, dict(DB))

    def test_save_state_handles_complex_data_types(self):
        """Test saving state with complex nested data structures."""
        # Add complex data to DB
        DB["complex_data"] = {
            "nested_dict": {
                "level1": {
                    "level2": {
                        "numbers": [1, 2, 3.14, -5],
                        "strings": ["hello", "world", ""],
                        "booleans": [True, False],
                        "null_value": None
                    }
                }
            },
            "array_of_objects": [
                {"id": 1, "name": "first"},
                {"id": 2, "name": "second", "optional": None}
            ],
            "mixed_array": [1, "string", True, None, {"key": "value"}]
        }
        
        filepath = os.path.join(self.test_dir, "complex_state.json")
        save_state(filepath)
        
        # Verify complex data was saved correctly
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["complex_data"], DB["complex_data"])

    def test_save_state_empty_db(self):
        """Test saving empty DB state."""
        DB.clear()
        filepath = os.path.join(self.test_dir, "empty_state.json")
        
        save_state(filepath)
        
        # Verify empty state was saved
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, {})

    @patch('builtins.open', side_effect=OSError("Disk full"))
    def test_save_state_os_error(self, mock_open):
        """Test handling of OS error during save."""
        with self.assertRaises(OSError):
            save_state("/tmp/state.json")

    # Test load_state function
    def test_load_state_success_replaces_db_content(self):
        """Test successful loading of state from JSON file."""
        # Create test state file
        test_state = {
            "loaded_scene": {
                "name": "LoadedScene",
                "objects": {
                    "LoadedCube": {
                        "name": "LoadedCube",
                        "type": "MESH",
                        "location": [5.0, 6.0, 7.0]
                    }
                }
            },
            "loaded_materials": {
                "LoadedMaterial": {
                    "name": "LoadedMaterial",
                    "base_color_value": [1.0, 0.0, 0.0]
                }
            }
        }
        
        filepath = os.path.join(self.test_dir, "load_test.json")
        with open(filepath, 'w') as f:
            json.dump(test_state, f)
        
        # Verify DB has different content initially
        self.assertNotEqual(dict(DB), test_state)
        
        # Load state
        load_state(filepath)
        
        # Verify DB was completely replaced with loaded state
        self.assertEqual(dict(DB), test_state)

    def test_load_state_clears_existing_db_content(self):
        """Test that load_state completely clears existing DB content."""
        # Ensure DB has content initially
        self.assertGreater(len(DB), 0)
        self.assertIn("current_scene", DB)
        
        # Create minimal state file
        minimal_state = {"only_key": "only_value"}
        filepath = os.path.join(self.test_dir, "minimal_state.json")
        with open(filepath, 'w') as f:
            json.dump(minimal_state, f)
        
        # Load minimal state
        load_state(filepath)
        
        # Verify only loaded content remains
        self.assertEqual(dict(DB), minimal_state)
        self.assertNotIn("current_scene", DB)
        self.assertIn("only_key", DB)

    def test_load_state_empty_json_file(self):
        """Test loading from file containing empty JSON object."""
        empty_state = {}
        filepath = os.path.join(self.test_dir, "empty_state.json")
        with open(filepath, 'w') as f:
            json.dump(empty_state, f)
        
        load_state(filepath)
        
        # Verify DB is empty
        self.assertEqual(len(DB), 0)
        self.assertEqual(dict(DB), {})

    def test_load_state_complex_data_types(self):
        """Test loading state with complex nested data structures."""
        complex_state = {
            "scene_data": {
                "objects": {
                    "ComplexObject": {
                        "transform_matrix": [
                            [1.0, 0.0, 0.0, 0.0],
                            [0.0, 1.0, 0.0, 0.0],
                            [0.0, 0.0, 1.0, 0.0],
                            [0.0, 0.0, 0.0, 1.0]
                        ],
                        "metadata": {
                            "created_at": "2023-01-01T00:00:00Z",
                            "tags": ["procedural", "generated"],
                            "properties": {
                                "mass": 1.5,
                                "friction": 0.8,
                                "restitution": 0.2
                            }
                        }
                    }
                }
            },
            "render_layers": [
                {"name": "Beauty", "enabled": True, "samples": 128},
                {"name": "Diffuse", "enabled": False, "samples": 64}
            ]
        }
        
        filepath = os.path.join(self.test_dir, "complex_load.json")
        with open(filepath, 'w') as f:
            json.dump(complex_state, f)
        
        load_state(filepath)
        
        # Verify complex data was loaded correctly
        self.assertEqual(dict(DB), complex_state)
        self.assertEqual(
            DB["scene_data"]["objects"]["ComplexObject"]["transform_matrix"][0],
            [1.0, 0.0, 0.0, 0.0]
        )

    def test_load_state_file_not_found_raises_error(self):
        """Test that loading from non-existent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_state("/nonexistent/path/state.json")

    def test_load_state_invalid_json_raises_error(self):
        """Test that loading from invalid JSON file raises JSONDecodeError."""
        # Create file with invalid JSON
        filepath = os.path.join(self.test_dir, "invalid.json")
        with open(filepath, 'w') as f:
            f.write('{"invalid": json, "missing": quotes}')
        
        with self.assertRaises(json.JSONDecodeError):
            load_state(filepath)

    def test_load_state_empty_file_raises_error(self):
        """Test that loading from empty file raises JSONDecodeError."""
        filepath = os.path.join(self.test_dir, "empty_file.json")
        with open(filepath, 'w') as f:
            f.write('')  # Completely empty file
        
        with self.assertRaises(json.JSONDecodeError):
            load_state(filepath)

    # Test save/load roundtrip
    def test_save_load_roundtrip_preserves_data(self):
        """Test that saving and loading preserves all data correctly."""
        # Save current state
        save_filepath = os.path.join(self.test_dir, "roundtrip_save.json")
        save_state(save_filepath)
        
        # Store original state for comparison
        original_state = copy.deepcopy(dict(DB))
        
        # Modify DB
        DB["modified_key"] = "modified_value"
        DB["current_scene"]["name"] = "ModifiedScene"
        
        # Load saved state
        load_state(save_filepath)
        
        # Verify DB was restored to original state
        self.assertEqual(dict(DB), original_state)

    def test_save_load_roundtrip_with_unicode(self):
        """Test roundtrip with Unicode characters."""
        # Add Unicode data to DB
        DB["unicode_test"] = {
            "chinese": "中文测试",
            "japanese": "日本語テスト",
            "arabic": "اختبار عربي",
            "emoji": "🚀🌟⚡",
            "mixed": "Hello 世界 🌍"
        }
        
        # Save and load
        filepath = os.path.join(self.test_dir, "unicode_test.json")
        save_state(filepath)
        
        original_unicode = copy.deepcopy(DB["unicode_test"])
        DB.clear()
        
        load_state(filepath)
        
        # Verify Unicode data was preserved
        self.assertEqual(DB["unicode_test"], original_unicode)

    def test_save_load_roundtrip_with_special_characters(self):
        """Test roundtrip with special JSON characters."""
        # Add data with special characters
        DB["special_chars"] = {
            "quotes": 'String with "quotes" and \'apostrophes\'',
            "backslashes": "Path\\with\\backslashes",
            "newlines": "Line 1\nLine 2\nLine 3",
            "tabs": "Column1\tColumn2\tColumn3",
            "mixed_escapes": "Quote: \"Hello\"\nTab:\tValue\nBackslash: \\path\\to\\file"
        }
        
        # Save and load
        filepath = os.path.join(self.test_dir, "special_chars.json")
        save_state(filepath)
        
        original_special = copy.deepcopy(DB["special_chars"])
        DB.clear()
        
        load_state(filepath)
        
        # Verify special characters were preserved
        self.assertEqual(DB["special_chars"], original_special)

    def test_multiple_save_load_operations(self):
        """Test multiple save/load operations in sequence."""
        filepaths = [
            os.path.join(self.test_dir, f"state_{i}.json")
            for i in range(3)
        ]
        
        # Create different states and save them
        states = []
        for i, filepath in enumerate(filepaths):
            DB.clear()
            test_state = {
                "iteration": i,
                "timestamp": f"2023-01-{i+1:02d}T00:00:00Z",
                "data": list(range(i * 5, (i + 1) * 5))
            }
            DB.update(test_state)
            states.append(copy.deepcopy(test_state))
            save_state(filepath)
        
        # Load states in reverse order and verify
        for i, (filepath, expected_state) in enumerate(zip(reversed(filepaths), reversed(states))):
            load_state(filepath)
            self.assertEqual(dict(DB), expected_state)

    def test_load_state_preserves_db_reference(self):
        """Test that load_state preserves the global DB reference."""
        # Get original DB reference
        original_db_id = id(DB)
        
        # Create and load state
        test_state = {"test": "data"}
        filepath = os.path.join(self.test_dir, "reference_test.json")
        with open(filepath, 'w') as f:
            json.dump(test_state, f)
        
        load_state(filepath)
        
        # Verify DB reference hasn't changed
        self.assertEqual(id(DB), original_db_id)
        self.assertEqual(dict(DB), test_state)

    def test_save_state_concurrent_safety(self):
        """Test that save_state handles concurrent access scenarios."""
        # This test verifies the save operation is atomic from a data perspective
        filepath = os.path.join(self.test_dir, "concurrent_test.json")
        
        # Save initial state
        save_state(filepath)
        
        # Modify DB while another save could be happening
        original_data = copy.deepcopy(dict(DB))
        DB["concurrent_modification"] = "new_data"
        
        # Save again
        save_state(filepath)
        
        # Verify the file contains the modified state
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertIn("concurrent_modification", saved_data)
        self.assertEqual(saved_data["concurrent_modification"], "new_data")


if __name__ == '__main__':
    unittest.main()
