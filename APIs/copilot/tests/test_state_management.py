"""
Test cases for state management in the Copilot API.
Tests save_state() and load_state() functions from copilot.SimulationEngine.db module.
"""

import unittest
import copy
import json
import tempfile
import os
from unittest.mock import patch, mock_open

from copilot.SimulationEngine.db import DB, save_state, load_state
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestStateManagement(BaseTestCaseWithErrorHandler):
    """Test cases for state management functions."""

    def setUp(self):
        """Set up test fixtures."""
        self._original_DB_state = copy.deepcopy(DB)
        # Create a test DB state
        self.test_db_state = {
            "workspace_root": "/test_workspace",
            "cwd": "/test_workspace/src",
            "file_system": {
                "/test_workspace": {
                    "path": "/test_workspace",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                },
                "/test_workspace/test_file.txt": {
                    "path": "/test_workspace/test_file.txt",
                    "is_directory": False,
                    "content_lines": ["test content\n"],
                    "size_bytes": 13,
                    "last_modified": "2024-03-19T12:00:00Z"
                }
            },
            "background_processes": {
                "12345": {
                    "pid": 12345,
                    "command": "test command",
                    "exec_dir": "/tmp/test",
                    "stdout_path": "/tmp/test/stdout.log",
                    "stderr_path": "/tmp/test/stderr.log",
                    "exitcode_path": "/tmp/test/exitcode.log",
                    "last_stdout_pos": 0,
                    "last_stderr_pos": 0
                }
            },
            "vscode_extensions_marketplace": ["test.extension"],
            "vscode_context": {"is_new_workspace_creation": True},
            "installed_vscode_extensions": ["installed.extension"],
            "vscode_api_references": [],
            "_next_pid": 12346
        }

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_save_state_successful(self):
        """Test save_state saves DB state to file successfully."""
        # Update DB with test state
        DB.clear()
        DB.update(self.test_db_state)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save state to temporary file
            save_state(temp_filepath)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_filepath))
            
            # Read and verify content
            with open(temp_filepath, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data, self.test_db_state)
            self.assertEqual(saved_data["workspace_root"], "/test_workspace")
            self.assertEqual(saved_data["_next_pid"], 12346)
            self.assertIn("/test_workspace/test_file.txt", saved_data["file_system"])
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_save_state_pretty_format(self):
        """Test save_state creates human-readable JSON with indentation."""
        # Update DB with test state
        DB.clear()
        DB.update(self.test_db_state)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save state to temporary file
            save_state(temp_filepath)
            
            # Read raw content to check formatting
            with open(temp_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should have indentation (multiple spaces/newlines)
            self.assertIn('\n', content)
            self.assertIn('  ', content)  # Should have indentation
            
            # Should be valid JSON
            parsed = json.loads(content)
            self.assertEqual(parsed, self.test_db_state)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_save_state_file_permission_error(self):
        """Test save_state handles file permission errors."""
        # Try to save to an invalid path
        invalid_path = "/root/invalid/path/state.json"
        
        with self.assertRaises(IOError):
            save_state(invalid_path)

    def test_save_state_overwrites_existing_file(self):
        """Test save_state overwrites existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
            # Write initial content
            temp_file.write('{"initial": "content"}')
        
        try:
            # Update DB with test state
            DB.clear()
            DB.update(self.test_db_state)
            
            # Save state to existing file
            save_state(temp_filepath)
            
            # Verify file was overwritten with new content
            with open(temp_filepath, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data, self.test_db_state)
            self.assertNotEqual(saved_data, {"initial": "content"})
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_load_state_successful(self):
        """Test load_state loads state from file successfully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
            json.dump(self.test_db_state, temp_file, indent=2)
        
        try:
            # Clear DB and load state
            DB.clear()
            load_state(temp_filepath)
            
            # Verify DB was updated with loaded state
            self.assertEqual(DB, self.test_db_state)
            self.assertEqual(DB["workspace_root"], "/test_workspace")
            self.assertEqual(DB["_next_pid"], 12346)
            self.assertIn("/test_workspace/test_file.txt", DB["file_system"])
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_load_state_file_not_found(self):
        """Test load_state handles file not found gracefully."""
        # Store original DB state
        original_state = copy.deepcopy(DB)
        
        # Try to load from non-existent file
        with patch('copilot.SimulationEngine.db.print_log') as mock_print_log:
            load_state("/non/existent/file.json")
            
            # Verify warning was logged
            mock_print_log.assert_called_once()
            warning_message = mock_print_log.call_args[0][0]
            self.assertIn("not found", warning_message)
        
        # Verify DB state was preserved
        self.assertEqual(DB, original_state)

    def test_load_state_invalid_json(self):
        """Test load_state handles invalid JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
            temp_file.write("invalid json content {")
        
        try:
            # Store original DB state
            original_state = copy.deepcopy(DB)
            
            # Try to load invalid JSON
            with patch('copilot.SimulationEngine.db.print_log') as mock_print_log:
                load_state(temp_filepath)
                
                # Verify error was logged
                mock_print_log.assert_called_once()
                error_message = mock_print_log.call_args[0][0]
                self.assertIn("Could not decode JSON", error_message)
            
            # Verify DB state was preserved
            self.assertEqual(DB, original_state)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_load_state_empty_file(self):
        """Test load_state handles empty file gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
            # File is empty by default
        
        try:
            # Store original DB state
            original_state = copy.deepcopy(DB)
            
            # Try to load empty file
            with patch('copilot.SimulationEngine.db.print_log') as mock_print_log:
                load_state(temp_filepath)
                
                # Should log JSON decode error
                mock_print_log.assert_called_once()
                error_message = mock_print_log.call_args[0][0]
                self.assertIn("Could not decode JSON", error_message)
            
            # Verify DB state was preserved
            self.assertEqual(DB, original_state)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_load_state_clears_existing_db(self):
        """Test load_state clears existing DB before loading new state."""
        # Add some data to DB
        DB["extra_field"] = "should_be_removed"
        DB["workspace_root"] = "/old/workspace"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
            json.dump(self.test_db_state, temp_file, indent=2)
        
        try:
            # Load state
            load_state(temp_filepath)
            
            # Verify old data was cleared and new data loaded
            self.assertNotIn("extra_field", DB)
            self.assertEqual(DB["workspace_root"], "/test_workspace")
            self.assertEqual(DB, self.test_db_state)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_load_state_unexpected_error(self):
        """Test load_state handles unexpected errors gracefully."""
        original_state = copy.deepcopy(DB)
        
        # Mock the file operations to raise an unexpected error
        with patch('builtins.open', side_effect=PermissionError("Unexpected permission error")):
            with patch('copilot.SimulationEngine.db.print_log') as mock_print_log:
                load_state("/some/file.json")
                
                # Verify error was logged
                mock_print_log.assert_called_once()
                error_message = mock_print_log.call_args[0][0]
                self.assertIn("unexpected error", error_message)
        
        # Verify DB state was preserved
        self.assertEqual(DB, original_state)

    def test_roundtrip_save_and_load(self):
        """Test complete roundtrip: save state, modify DB, then load state."""
        # Set up initial state
        DB.clear()
        DB.update(self.test_db_state)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save current state
            save_state(temp_filepath)
            
            # Modify DB
            DB["workspace_root"] = "/modified/workspace"
            DB["_next_pid"] = 99999
            DB["extra_field"] = "added"
            
            # Load original state
            load_state(temp_filepath)
            
            # Verify state was restored exactly
            self.assertEqual(DB, self.test_db_state)
            self.assertEqual(DB["workspace_root"], "/test_workspace")
            self.assertEqual(DB["_next_pid"], 12346)
            self.assertNotIn("extra_field", DB)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_save_load_complex_data_structures(self):
        """Test save/load with complex nested data structures."""
        complex_state = {
            "workspace_root": "/complex/workspace",
            "cwd": "/complex/workspace",
            "file_system": {
                "/complex/workspace": {
                    "path": "/complex/workspace",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                },
                "/complex/workspace/nested/deep/file.txt": {
                    "path": "/complex/workspace/nested/deep/file.txt",
                    "is_directory": False,
                    "content_lines": [
                        "line with unicode: 测试\n",
                        "line with special chars: !@#$%^&*()\n",
                        "line with quotes: \"double\" 'single'\n"
                    ],
                    "size_bytes": 100,
                    "last_modified": "2024-03-19T12:00:00Z",
                    "metadata": {
                        "nested_dict": {"key": "value"},
                        "nested_list": [1, 2, {"inner": "dict"}]
                    }
                }
            },
            "background_processes": {},
            "_next_pid": 1
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Set complex state and save
            DB.clear()
            DB.update(complex_state)
            save_state(temp_filepath)
            
            # Clear and load
            DB.clear()
            load_state(temp_filepath)
            
            # Verify complex data was preserved
            self.assertEqual(DB, complex_state)
            file_entry = DB["file_system"]["/complex/workspace/nested/deep/file.txt"]
            self.assertIn("测试", file_entry["content_lines"][0])
            self.assertEqual(file_entry["metadata"]["nested_dict"]["key"], "value")
            self.assertEqual(file_entry["metadata"]["nested_list"][2]["inner"], "dict")
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_save_state_with_different_encodings(self):
        """Test save_state handles different character encodings correctly."""
        unicode_state = copy.deepcopy(self.test_db_state)
        unicode_state["file_system"]["/test_workspace/unicode_file.txt"] = {
            "path": "/test_workspace/unicode_file.txt",
            "is_directory": False,
            "content_lines": [
                "English text\n",
                "中文文本\n",
                "Русский текст\n",
                "العربية\n",
                "🌟 emoji content 🚀\n"
            ],
            "size_bytes": 100,
            "last_modified": "2024-03-19T12:00:00Z"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Set unicode state and save
            DB.clear()
            DB.update(unicode_state)
            save_state(temp_filepath)
            
            # Load and verify unicode content
            DB.clear()
            load_state(temp_filepath)
            
            unicode_file = DB["file_system"]["/test_workspace/unicode_file.txt"]
            content_lines = unicode_file["content_lines"]
            self.assertIn("中文文本", content_lines[1])
            self.assertIn("Русский текст", content_lines[2])
            self.assertIn("العربية", content_lines[3])
            self.assertIn("🌟", content_lines[4])
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)


if __name__ == '__main__':
    unittest.main()
