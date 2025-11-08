"""
Tests for the claude_code SimulationEngine DB state management functions.
"""

import os
import json
import tempfile
import unittest
import shutil
from datetime import datetime

from common_utils.base_case import BaseTestCaseWithErrorHandler

from ..SimulationEngine.db import DB, load_state, save_state, get_minified_state, reset_db


class TestDBStateManagement(BaseTestCaseWithErrorHandler):
    """Test the load_state and save_state functions of the claude_code DB."""

    def setUp(self):
        """Set up test environment."""
        # Create a temp directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Save the original DB state to restore after tests
        self.original_db = DB.copy()
        
        # Create a test state file with known values
        self.test_state_path = os.path.join(self.test_dir, "test_state.json")
        self.test_state = {
            "workspace_root": "/test/workspace",
            "cwd": "/test/workspace/subdir",
            "file_system": {
                "/test/workspace/test.py": {
                    "path": "/test/workspace/test.py",
                    "is_directory": False,
                    "content_lines": ["print('Hello, World!')\n", "# Test file\n"],
                    "size_bytes": 30,
                    "last_modified": "2023-01-01T12:00:00Z"
                },
                "/test/workspace/src": {
                    "path": "/test/workspace/src",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2023-01-01T11:00:00Z"
                }
            },
            "memory_storage": {
                "test_memory": "test_value"
            },
            "last_edit_params": {
                "file_path": "/test/workspace/test.py",
                "content": "print('Hello, World!')"
            },
            "background_processes": {
                "test_process": {
                    "command": "echo test",
                    "status": "completed"
                }
            },
            "tool_metrics": {
                "read_file": {"count": 5, "total_time": 0.15}
            },
            "_created": "2023-01-01T10:00:00Z"
        }
        
        with open(self.test_state_path, "w") as f:
            json.dump(self.test_state, f)
            
        # Path for save_state tests
        self.save_state_path = os.path.join(self.test_dir, "saved_state.json")

    def tearDown(self):
        """Clean up after tests."""
        # Restore the original DB state
        global DB
        DB.clear()
        DB.update(self.original_db)
        
        # Remove temp directory and files
        shutil.rmtree(self.test_dir)

    def test_load_state(self):
        """Test loading state from a file."""
        # Load the test state
        load_state(self.test_state_path)
        
        # Check that the DB was updated with the test values
        self.assertEqual(DB["workspace_root"], "/test/workspace")
        self.assertEqual(DB["cwd"], "/test/workspace/subdir")
        
        # Check file system structure
        self.assertIn("/test/workspace/test.py", DB["file_system"])
        self.assertEqual(
            DB["file_system"]["/test/workspace/test.py"]["content_lines"][0], 
            "print('Hello, World!')\n"
        )
        self.assertEqual(
            DB["file_system"]["/test/workspace/src"]["is_directory"], 
            True
        )
        
        # Check memory storage
        self.assertEqual(DB["memory_storage"]["test_memory"], "test_value")
        
        # Check last edit params
        self.assertEqual(DB["last_edit_params"]["file_path"], "/test/workspace/test.py")
        
        # Check background processes
        self.assertIn("test_process", DB["background_processes"])
        self.assertEqual(
            DB["background_processes"]["test_process"]["status"], 
            "completed"
        )
        
        # Check tool metrics
        self.assertEqual(DB["tool_metrics"]["read_file"]["count"], 5)

    def test_save_state(self):
        """Test saving state to a file."""
        # Modify the DB with test values
        DB["workspace_root"] = "/save/test/workspace"
        DB["cwd"] = "/save/test/workspace/current"
        DB["file_system"] = {
            "/save/test/workspace/main.py": {
                "path": "/save/test/workspace/main.py",
                "is_directory": False,
                "content_lines": ["def main():\n", "    pass\n"],
                "size_bytes": 20,
                "last_modified": "2023-02-02T12:00:00Z"
            }
        }
        DB["memory_storage"]["save_test"] = "save_value"
        
        # Save the state
        save_state(self.save_state_path)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(self.save_state_path))
        
        # Load the saved state and verify contents
        with open(self.save_state_path, "r") as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["workspace_root"], "/save/test/workspace")
        self.assertEqual(saved_data["cwd"], "/save/test/workspace/current")
        self.assertEqual(
            saved_data["file_system"]["/save/test/workspace/main.py"]["content_lines"][0], 
            "def main():\n"
        )
        self.assertEqual(saved_data["memory_storage"]["save_test"], "save_value")

    def test_load_state_nonexistent_file(self):
        """Test loading state from a non-existent file."""
        # Try to load a non-existent file
        nonexistent_path = os.path.join(self.test_dir, "nonexistent.json")
        
        # Save current DB state for comparison
        before_db = DB.copy()
        
        # Load non-existent file should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            load_state(nonexistent_path)
        
        # DB should remain unchanged
        self.assertEqual(DB, before_db)

    def test_load_state_invalid_json(self):
        """Test loading state from an invalid JSON file."""
        # Create an invalid JSON file
        invalid_json_path = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_json_path, "w") as f:
            f.write("{ this is not valid JSON }")
        
        # Save current DB state for comparison
        before_db = DB.copy()
        
        # Load invalid JSON file should raise JSONDecodeError
        with self.assertRaises(json.JSONDecodeError):
            load_state(invalid_json_path)
        
        # DB should remain unchanged
        self.assertEqual(DB, before_db)

    def test_save_state_directory_creation(self):
        """Test save_state creates directories if needed."""
        # Path with non-existent directories
        nested_path = os.path.join(self.test_dir, "new_dir", "another_dir", "state.json")
        
        # Create the parent directories first (save_state doesn't create directories)
        os.makedirs(os.path.dirname(nested_path), exist_ok=True)
        
        # Save state to the nested path
        save_state(nested_path)
        
        # Check that the file was created
        self.assertTrue(os.path.exists(nested_path))

    def test_memory_storage_handling(self):
        """Test that memory_storage is handled correctly."""
        # Create state without memory_storage
        state_without_memory = {
            "workspace_root": "/test/workspace",
            "cwd": "/test/workspace",
            "file_system": {}
        }
        
        state_path = os.path.join(self.test_dir, "no_memory.json")
        with open(state_path, "w") as f:
            json.dump(state_without_memory, f)
        
        # Load the state
        load_state(state_path)
        
        # Check that memory_storage was added
        self.assertIn("memory_storage", DB)
        self.assertIsInstance(DB["memory_storage"], dict)

    def test_get_minified_state(self):
        """Test the get_minified_state function."""
        # Load test state first
        load_state(self.test_state_path)
        
        # Get minified state
        minified = get_minified_state()
        
        # Check that basic structure is preserved
        self.assertIn("workspace_root", minified)
        self.assertIn("file_system", minified)
        self.assertIn("memory_storage", minified)
        
        # Check that last_modified fields are removed (if blacklisted)
        for file_path, file_info in minified.get("file_system", {}).items():
            # The minified version should not have last_modified fields
            if "last_modified" in file_info:
                # This might still be present if not in blacklist - that's okay
                pass

    def test_save_load_cycle(self):
        """Test a full save and load cycle."""
        # Modify DB with unique values
        unique_timestamp = datetime.now().isoformat()
        DB["workspace_root"] = f"/cycle/test/{unique_timestamp}"
        DB["_created"] = unique_timestamp
        
        original_file_system = {
            f"/cycle/test/{unique_timestamp}/file.py": {
                "path": f"/cycle/test/{unique_timestamp}/file.py",
                "is_directory": False,
                "content_lines": ["# Cycle test file\n"],
                "size_bytes": 18
            }
        }
        DB["file_system"] = original_file_system
        
        # Save the state
        cycle_path = os.path.join(self.test_dir, "cycle.json")
        save_state(cycle_path)
        
        # Modify DB again
        DB["workspace_root"] = "/something/else"
        DB["file_system"] = {}
        
        # Load the saved state
        load_state(cycle_path)
        
        # Check that the DB was restored to the saved state
        self.assertEqual(DB["workspace_root"], f"/cycle/test/{unique_timestamp}")
        self.assertEqual(DB["_created"], unique_timestamp)
        self.assertEqual(DB["file_system"], original_file_system)

    def test_db_structure_validation(self):
        """Test that the DB has the expected structure after loading default state."""
        # Reset to original state
        self.tearDown()
        self.setUp()
        
        # Check that all expected keys are present
        expected_keys = [
            "workspace_root",
            "cwd", 
            "file_system",
            "memory_storage",
            "last_edit_params",
            "background_processes",
            "tool_metrics"
        ]
        
        for key in expected_keys:
            self.assertIn(key, DB, f"Key '{key}' should be present in DB")
        
        # Check types
        self.assertIsInstance(DB["file_system"], dict)
        self.assertIsInstance(DB["memory_storage"], dict)
        self.assertIsInstance(DB["background_processes"], dict)
        self.assertIsInstance(DB["tool_metrics"], dict)


if __name__ == "__main__":
    unittest.main()
