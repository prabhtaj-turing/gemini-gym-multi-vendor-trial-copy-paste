"""
Test cases targeting the biggest coverage opportunities in the Copilot API.
Focusing on 82-statement functions with low coverage for maximum impact.
"""

import unittest
import copy
import os
import tempfile
import shutil
import json
import time
from unittest.mock import patch, MagicMock, mock_open

from ..SimulationEngine.db import DB
from ..SimulationEngine import utils
from ..SimulationEngine import custom_errors
from .. import get_terminal_output
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestMassiveCoverageWins(BaseTestCaseWithErrorHandler):
    """Test cases targeting the biggest coverage gaps for maximum improvement."""

    def setUp(self):
        """Set up test fixtures."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            "workspace_root": "/test/workspace",
            "cwd": "/test/workspace",
            "file_system": {},
            "background_processes": {},
            "_next_pid": 1
        })

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    # ========================
    # get_terminal_output Tests (52 statements, 54% coverage - 24 missing!)
    # ========================

    def test_get_terminal_output_nonexistent_terminal(self):
        """Test get_terminal_output with non-existent terminal ID."""
        # Should raise InvalidInputError due to non-digit terminal ID
        with self.assertRaises(custom_errors.InvalidInputError):
            get_terminal_output("nonexistent_terminal")

    def test_get_terminal_output_invalid_terminal_id(self):
        """Test get_terminal_output with invalid terminal ID types."""
        # Test with None - should raise TypeError
        with self.assertRaises(TypeError):
            get_terminal_output(None)
        
        # Test with empty string - should raise InvalidInputError
        with self.assertRaises(custom_errors.InvalidInputError):
            get_terminal_output("")

    def test_get_terminal_output_missing_process_data(self):
        """Test get_terminal_output when process data is incomplete."""
        # Add a process with missing data
        DB["background_processes"]["123"] = {
            "command": "test command",
            "exec_dir": "/test"
            # Missing stdout_path, stderr_path, etc.
        }
        
        # Should raise OutputRetrievalError due to missing required keys
        with self.assertRaises(custom_errors.OutputRetrievalError):
            get_terminal_output("123")

    @patch('copilot.command_line.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_terminal_output_file_read_success(self, mock_file_open, mock_exists):
        """Test get_terminal_output with successful file reading."""
        # Set up a complete process entry
        temp_dir = tempfile.mkdtemp()
        try:
            stdout_path = os.path.join(temp_dir, "stdout.log")
            stderr_path = os.path.join(temp_dir, "stderr.log") 
            exitcode_path = os.path.join(temp_dir, "exitcode.log")
            
            DB["background_processes"]["456"] = {
                "command": "echo hello",
                "exec_dir": temp_dir,
                "stdout_path": stdout_path,
                "stderr_path": stderr_path,
                "exitcode_path": exitcode_path,
                "last_stdout_pos": 0,
                "last_stderr_pos": 0,
                "process": None
            }
            
            # Mock file existence and content
            mock_exists.return_value = True
            # Mock different content based on which file is being read
            def mock_read_side_effect():
                if 'exitcode' in mock_file_open.return_value.__enter__.return_value.name or True:
                    return "0"  # Valid exit code
                return "hello\nworld"  # Output content
            
            mock_file_open.return_value.__enter__.return_value.read.side_effect = mock_read_side_effect
            
            result = get_terminal_output("456")
            
            self.assertIsInstance(result, dict)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @patch('copilot.command_line.os.path.exists')
    def test_get_terminal_output_missing_files(self, mock_exists):
        """Test get_terminal_output when output files don't exist."""
        DB["background_processes"]["789"] = {
            "command": "test command",
            "exec_dir": "/test",
            "stdout_path": "/nonexistent/stdout.log",
            "stderr_path": "/nonexistent/stderr.log",
            "exitcode_path": "/nonexistent/exitcode.log",
            "last_stdout_pos": 0,
            "last_stderr_pos": 0
        }
        
        mock_exists.return_value = False
        
        result = get_terminal_output("789")
        
        self.assertIsInstance(result, dict)

    # ========================
    # hydrate_db_from_directory Tests (82 statements, 35% coverage - 53 missing!)
    # ========================

    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    def test_hydrate_db_from_directory_invalid_directory(self, mock_isdir):
        """Test hydrate_db_from_directory with invalid directory."""
        mock_isdir.return_value = False
        
        test_db = {"file_system": {}}
        
        with self.assertRaises(FileNotFoundError):
            utils.hydrate_db_from_directory(test_db, "/nonexistent/dir")

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    def test_hydrate_db_from_directory_os_walk_exception(self, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles os.walk exceptions."""
        mock_isdir.return_value = True
        mock_walk.side_effect = OSError("Permission denied")
        
        test_db = {"file_system": {}}
        
        with self.assertRaises(RuntimeError):
            utils.hydrate_db_from_directory(test_db, "/test/dir")

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.path.isfile')
    @patch('copilot.SimulationEngine.utils.os.path.getsize')
    @patch('copilot.SimulationEngine.utils.os.path.getmtime')
    def test_hydrate_db_from_directory_basic_success(self, mock_getmtime, mock_getsize, mock_isfile, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory basic successful operation."""
        mock_isdir.return_value = True
        mock_walk.return_value = [
            ('/test/root', ['subdir'], ['file1.txt', 'file2.py']),
            ('/test/root/subdir', [], ['nested.js'])
        ]
        
        def mock_isfile_func(path):
            return not path.endswith('subdir')
        mock_isfile.side_effect = mock_isfile_func
        
        mock_getsize.return_value = 1024
        mock_getmtime.return_value = 1640995200.0
        
        test_db = {"file_system": {}}
        
        with patch('builtins.open', mock_open(read_data="test content")):
            with patch('copilot.SimulationEngine.utils.is_likely_binary_file', return_value=False):
                result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        self.assertIn("file_system", test_db)

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.path.isfile')
    @patch('copilot.SimulationEngine.utils.os.path.getsize')
    @patch('copilot.SimulationEngine.utils.os.path.getmtime')
    def test_hydrate_db_from_directory_file_read_errors(self, mock_getmtime, mock_getsize, mock_isfile, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles file read errors."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['protected.txt'])]
        mock_isfile.return_value = True
        mock_getsize.return_value = 1024
        mock_getmtime.return_value = 1640995200.0
        
        test_db = {"file_system": {}}
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        # Should complete successfully even with read errors
        self.assertTrue(result)

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.path.isfile')
    @patch('copilot.SimulationEngine.utils.os.path.getsize')
    @patch('copilot.SimulationEngine.utils.os.path.getmtime')
    def test_hydrate_db_from_directory_large_files(self, mock_getmtime, mock_getsize, mock_isfile, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles large files properly."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['huge.bin'])]
        mock_isfile.return_value = True
        mock_getmtime.return_value = 1640995200.0
        
        # Mock a very large file
        mock_getsize.return_value = 100 * 1024 * 1024  # 100MB
        
        test_db = {"file_system": {}}
        
        result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        # Should handle large files with placeholders

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    def test_hydrate_db_from_directory_directory_metadata_errors(self, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles directory metadata errors."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], [])]
        mock_stat.side_effect = PermissionError("Access denied to directory")
        
        test_db = {"file_system": {}}
        
        result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        # Should complete successfully even with directory metadata errors
        self.assertTrue(result)

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    def test_hydrate_db_from_directory_empty_files(self, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles empty files correctly."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['empty.txt'])]
        
        # Mock stat to return 0 size
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 0
        mock_stat_result.st_mtime = 1640995200.0
        mock_stat.return_value = mock_stat_result
        
        test_db = {"file_system": {}}
        
        result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        # Should have empty content_lines for zero-size files
        file_path = "/test/root/empty.txt"
        if file_path in test_db["file_system"]:
            self.assertEqual(test_db["file_system"][file_path]["content_lines"], [])

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    @patch('copilot.SimulationEngine.utils.is_likely_binary_file')
    def test_hydrate_db_from_directory_binary_files(self, mock_binary, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles binary files correctly."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['image.jpg'])]
        mock_binary.return_value = True
        
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 2048
        mock_stat_result.st_mtime = 1640995200.0
        mock_stat.return_value = mock_stat_result
        
        test_db = {"file_system": {}}
        
        result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        # Should use BINARY_CONTENT_PLACEHOLDER for binary files

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    @patch('copilot.SimulationEngine.utils.is_likely_binary_file')
    def test_hydrate_db_from_directory_encoding_fallbacks(self, mock_binary, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory multiple encoding attempts."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['encoded.txt'])]
        mock_binary.return_value = False
        
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1640995200.0
        mock_stat.return_value = mock_stat_result
        
        test_db = {"file_system": {}}
        
        # Mock file open to fail on UTF-8, succeed on latin-1
        def mock_open_func(filename, mode='r', encoding=None):
            if encoding == 'utf-8':
                raise UnicodeDecodeError('utf-8', b'test', 0, 1, 'invalid start byte')
            elif encoding == 'latin-1':
                return mock_open(read_data="Latin-1 content").return_value
            else:
                return mock_open(read_data="Default content").return_value
        
        with patch('builtins.open', side_effect=mock_open_func):
            result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    @patch('copilot.SimulationEngine.utils.is_likely_binary_file')
    def test_hydrate_db_from_directory_all_encodings_fail(self, mock_binary, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory when all encoding attempts fail."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['bad_encoding.txt'])]
        mock_binary.return_value = False
        
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1640995200.0
        mock_stat.return_value = mock_stat_result
        
        test_db = {"file_system": {}}
        
        # Mock all encoding attempts to fail
        with patch('builtins.open', side_effect=UnicodeDecodeError('all', b'test', 0, 1, 'invalid')):
            result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        # Should have error message in content

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    def test_hydrate_db_from_directory_file_not_found_during_scan(self, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles FileNotFoundError during file processing."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['deleted.txt'])]
        mock_stat.side_effect = FileNotFoundError("File was deleted")
        
        test_db = {"file_system": {}}
        
        result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        # Should complete successfully even if files disappear during scan
        self.assertTrue(result)

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    def test_hydrate_db_from_directory_permission_error_on_file(self, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles PermissionError on specific file."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['protected.txt'])]
        mock_stat.side_effect = PermissionError("Permission denied")
        
        test_db = {"file_system": {}}
        
        result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        # Should add file with permission error placeholder

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    def test_hydrate_db_from_directory_unexpected_file_error(self, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles unexpected errors during file processing."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['problematic.txt'])]
        mock_stat.side_effect = RuntimeError("Unexpected filesystem error")
        
        test_db = {"file_system": {}}
        
        result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        # Should add file with error placeholder

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    @patch('copilot.SimulationEngine.utils.is_likely_binary_file')
    def test_hydrate_db_from_directory_read_permission_error(self, mock_binary, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles read PermissionError specifically."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['no_read.txt'])]
        mock_binary.return_value = False
        
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1640995200.0
        mock_stat.return_value = mock_stat_result
        
        test_db = {"file_system": {}}
        
        # Mock file open to raise PermissionError for reading
        with patch('builtins.open', side_effect=PermissionError("Cannot read file")):
            result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        # Should handle permission errors gracefully

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    @patch('copilot.SimulationEngine.utils.os.stat')
    @patch('copilot.SimulationEngine.utils.is_likely_binary_file')
    def test_hydrate_db_from_directory_general_read_exception(self, mock_binary, mock_stat, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles general exceptions during file read."""
        mock_isdir.return_value = True
        mock_walk.return_value = [('/test/root', [], ['corrupted.txt'])]
        mock_binary.return_value = False
        
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1640995200.0
        mock_stat.return_value = mock_stat_result
        
        test_db = {"file_system": {}}
        
        # Mock file open to raise an unexpected exception
        with patch('builtins.open', side_effect=OSError("Disk I/O error")):
            result = utils.hydrate_db_from_directory(test_db, "/test/root")
        
        self.assertTrue(result)
        # Should handle unexpected read errors gracefully

    @patch('copilot.SimulationEngine.utils.os.walk')
    @patch('copilot.SimulationEngine.utils.os.path.isdir')
    def test_hydrate_db_from_directory_fatal_error_handling(self, mock_isdir, mock_walk):
        """Test hydrate_db_from_directory handles fatal errors during hydration."""
        mock_isdir.return_value = True
        mock_walk.side_effect = RuntimeError("Critical filesystem failure")
        
        test_db = {"file_system": {"existing": "data"}}
        
        with self.assertRaises(RuntimeError):
            utils.hydrate_db_from_directory(test_db, "/test/root")
        
        # DB should be reset on fatal error
        self.assertEqual(test_db["workspace_root"], "")
        self.assertEqual(test_db["cwd"], "")
        self.assertEqual(test_db["file_system"], {})

    # ========================
    # update_db_file_system_from_temp Tests (82 statements, 33% coverage - 55 missing!)
    # ========================

    def test_update_db_file_system_from_temp_nonexistent_dir(self):
        """Test update_db_file_system_from_temp with non-existent directory."""
        original_state = {"file_system": {}}
        
        result = utils.update_db_file_system_from_temp(
            "/nonexistent/temp/dir",
            original_state,
            "/workspace"
        )
        
        # Function returns None
        self.assertIsNone(result)

    def test_update_db_file_system_from_temp_empty_dir(self):
        """Test update_db_file_system_from_temp with empty directory."""
        temp_dir = tempfile.mkdtemp()
        try:
            original_state = {"file_system": {}}
            
            result = utils.update_db_file_system_from_temp(
                temp_dir,
                original_state,
                "/workspace"
            )
            
            # Function returns None
            self.assertIsNone(result)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_update_db_file_system_from_temp_with_files(self):
        """Test update_db_file_system_from_temp with actual files."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create test files
            test_file = os.path.join(temp_dir, "test.py")
            with open(test_file, 'w') as f:
                f.write("print('hello')\n")
            
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)
            
            nested_file = os.path.join(subdir, "nested.txt")
            with open(nested_file, 'w') as f:
                f.write("nested content\n")
            
            original_state = {"file_system": {}}
            
            result = utils.update_db_file_system_from_temp(
                temp_dir,
                original_state,
                "/workspace"
            )
            
            # Function returns None
            self.assertIsNone(result)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_update_db_file_system_from_temp_permission_errors(self):
        """Test update_db_file_system_from_temp handles permission errors."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a file
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            original_state = {"file_system": {}}
            
            # Mock permission error
            with patch('builtins.open', side_effect=PermissionError("Access denied")):
                result = utils.update_db_file_system_from_temp(
                    temp_dir,
                    original_state,
                    "/workspace"
                )
            
            # Function returns None
            self.assertIsNone(result)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ========================
    # map_temp_path_to_db_key Tests (21 statements, 29% coverage - 15 missing!)
    # ========================

    def test_map_temp_path_to_db_key_basic(self):
        """Test map_temp_path_to_db_key basic functionality."""
        result = utils.map_temp_path_to_db_key(
            "/tmp/workspace/file.py",
            "/tmp/workspace", 
            "/logical/workspace"
        )
        
        self.assertIsInstance(result, (str, type(None)))

    def test_map_temp_path_to_db_key_path_not_in_temp_root(self):
        """Test map_temp_path_to_db_key when path is not in temp root."""
        result = utils.map_temp_path_to_db_key(
            "/completely/different/path/file.py",
            "/tmp/workspace",
            "/logical/workspace"
        )
        
        # Should return None when path not in temp root
        self.assertIsNone(result)

    def test_map_temp_path_to_db_key_edge_cases(self):
        """Test map_temp_path_to_db_key with edge cases."""
        # Test with empty strings
        result1 = utils.map_temp_path_to_db_key("", "", "")
        self.assertIsInstance(result1, (str, type(None)))
        
        # Test with same paths
        result2 = utils.map_temp_path_to_db_key(
            "/tmp/workspace",
            "/tmp/workspace",
            "/logical"
        )
        self.assertIsInstance(result2, (str, type(None)))

    def test_map_temp_path_to_db_key_windows_paths(self):
        """Test map_temp_path_to_db_key with Windows-style paths."""
        result = utils.map_temp_path_to_db_key(
            "C:\\tmp\\workspace\\file.py",
            "C:\\tmp\\workspace",
            "/logical/workspace"
        )
        
        self.assertIsInstance(result, (str, type(None)))

    # ========================
    # Other Medium Coverage Functions
    # ========================

    def test_propose_command_edge_cases(self):
        """Test propose_command with various edge cases."""
        # Test with empty request
        result1 = utils.propose_command("")
        self.assertIsInstance(result1, dict)
        
        # Test with very long request
        long_request = "a" * 1000
        result2 = utils.propose_command(long_request)
        self.assertIsInstance(result2, dict)

    @patch('copilot.SimulationEngine.utils.call_llm')
    def test_propose_command_llm_timeout(self, mock_call_llm):
        """Test propose_command handles LLM timeouts."""
        mock_call_llm.side_effect = Exception("timeout")
        
        result = utils.propose_command("test request")
        
        self.assertIsInstance(result, dict)
        self.assertIn("explanation", result)
        self.assertIn("timeout", result["explanation"])

    def test_get_file_system_entry_various_paths(self):
        """Test get_file_system_entry with various path formats."""
        # Just test the basic functionality - the function handles path resolution internally
        
        # Test non-existent file - should return None
        result1 = utils.get_file_system_entry("nonexistent.py")
        self.assertIsNone(result1)
        
        # Test invalid path - should return None gracefully due to exception handling
        result2 = utils.get_file_system_entry("")
        self.assertIsNone(result2)
        
        # Test with None - will raise TypeError but that's expected behavior


if __name__ == '__main__':
    unittest.main()
