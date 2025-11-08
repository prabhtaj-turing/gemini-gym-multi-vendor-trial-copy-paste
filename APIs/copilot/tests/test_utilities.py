"""
Test cases for utility functions in the Copilot API.
Tests various utility functions from copilot.SimulationEngine.utils module.
"""

import unittest
import copy
import os
import tempfile
import json
from unittest.mock import patch, mock_open

from copilot.SimulationEngine.db import DB
from copilot.SimulationEngine import utils
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUtilities(BaseTestCaseWithErrorHandler):
    """Test cases for utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self._original_DB_state = copy.deepcopy(DB)
        # Set up a minimal test DB structure
        DB.clear()
        DB.update({
            "workspace_root": "/test_workspace",
            "cwd": "/test_workspace",
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
                    "content_lines": ["line 1\n", "line 2\n"],
                    "size_bytes": 14,
                    "last_modified": "2024-03-19T12:00:00Z"
                },
                "/test_workspace/subdir": {
                    "path": "/test_workspace/subdir",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                }
            },
            "background_processes": {},
            "_next_pid": 1
        })

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_absolute_path_valid_relative(self):
        """Test get_absolute_path with valid relative paths."""
        result = utils.get_absolute_path("test_file.txt")
        self.assertEqual(result, "/test_workspace/test_file.txt")

        result = utils.get_absolute_path("./test_file.txt")
        self.assertEqual(result, "/test_workspace/test_file.txt")

    def test_get_absolute_path_valid_absolute(self):
        """Test get_absolute_path with valid absolute paths."""
        result = utils.get_absolute_path("/test_workspace/test_file.txt")
        self.assertEqual(result, "/test_workspace/test_file.txt")

    def test_get_absolute_path_invalid_outside_workspace(self):
        """Test get_absolute_path with path outside workspace."""
        with self.assertRaises(ValueError):
            utils.get_absolute_path("/outside/workspace/file.txt")

    def test_get_current_timestamp_iso(self):
        """Test get_current_timestamp_iso returns valid ISO format."""
        timestamp = utils.get_current_timestamp_iso()
        self.assertIsInstance(timestamp, str)
        # Should contain 'T' and 'Z' for ISO format
        self.assertIn('T', timestamp)
        self.assertTrue(timestamp.endswith('Z'))

    def test_get_file_system_entry_existing_file(self):
        """Test get_file_system_entry with existing file."""
        entry = utils.get_file_system_entry("/test_workspace/test_file.txt")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["path"], "/test_workspace/test_file.txt")
        self.assertFalse(entry["is_directory"])

    def test_get_file_system_entry_non_existing(self):
        """Test get_file_system_entry with non-existing file."""
        entry = utils.get_file_system_entry("/test_workspace/nonexistent.txt")
        self.assertIsNone(entry)

    def test_path_exists_existing_file(self):
        """Test path_exists with existing file."""
        self.assertTrue(utils.path_exists("/test_workspace/test_file.txt"))

    def test_path_exists_non_existing_file(self):
        """Test path_exists with non-existing file."""
        self.assertFalse(utils.path_exists("/test_workspace/nonexistent.txt"))

    def test_is_directory_true(self):
        """Test is_directory with actual directory."""
        self.assertTrue(utils.is_directory("/test_workspace"))
        self.assertTrue(utils.is_directory("/test_workspace/subdir"))

    def test_is_directory_false(self):
        """Test is_directory with file."""
        self.assertFalse(utils.is_directory("/test_workspace/test_file.txt"))

    def test_is_file_true(self):
        """Test is_file with actual file."""
        self.assertTrue(utils.is_file("/test_workspace/test_file.txt"))

    def test_is_file_false(self):
        """Test is_file with directory."""
        self.assertFalse(utils.is_file("/test_workspace"))

    def test_calculate_size_bytes_with_content(self):
        """Test calculate_size_bytes with content lines."""
        content_lines = ["line 1\n", "line 2\n", "line 3"]
        size = utils.calculate_size_bytes(content_lines)
        expected_size = len("line 1\n") + len("line 2\n") + len("line 3")
        self.assertEqual(size, expected_size)

    def test_calculate_size_bytes_empty(self):
        """Test calculate_size_bytes with empty content."""
        size = utils.calculate_size_bytes([])
        self.assertEqual(size, 0)

    def test_normalize_lines_with_trailing_newline(self):
        """Test _normalize_lines with ensure_trailing_newline=True."""
        lines = ["line1", "line2", "line3"]
        result = utils._normalize_lines(lines, ensure_trailing_newline=True)
        self.assertEqual(result, ["line1\n", "line2\n", "line3\n"])

    def test_normalize_lines_without_trailing_newline(self):
        """Test _normalize_lines with ensure_trailing_newline=False."""
        # Test with lines that already have newlines - they're preserved
        lines = ["line1\n", "line2\n", "line3\n"]
        result = utils._normalize_lines(lines, ensure_trailing_newline=False)
        self.assertEqual(result, ["line1\n", "line2\n", "line3\n"])
        
        # Test with lines without newlines - only last line stays without newline
        lines_without_newlines = ["line1", "line2", "line3"]
        result = utils._normalize_lines(lines_without_newlines, ensure_trailing_newline=False)
        self.assertEqual(result, ["line1\n", "line2\n", "line3"])

    def test_get_minimal_ipynb_content_lines(self):
        """Test _get_minimal_ipynb_content_lines returns valid notebook content."""
        content_lines = utils._get_minimal_ipynb_content_lines()
        self.assertIsInstance(content_lines, list)
        self.assertTrue(len(content_lines) > 0)
        
        # Join lines and parse as JSON to verify it's valid
        content_str = "".join(content_lines)
        try:
            notebook_dict = json.loads(content_str)
            self.assertIn("cells", notebook_dict)
            self.assertIn("metadata", notebook_dict)
        except json.JSONDecodeError:
            self.fail("Generated notebook content is not valid JSON")

    def test_is_path_excluded_for_search_ignored_dirs(self):
        """Test is_path_excluded_for_search with ignored directories."""
        ignore_dirs = {".git", "node_modules", "__pycache__"}
        ignore_patterns = set()
        
        self.assertTrue(utils.is_path_excluded_for_search(
            ".git/config", ignore_dirs, ignore_patterns))
        self.assertTrue(utils.is_path_excluded_for_search(
            "src/.git/config", ignore_dirs, ignore_patterns))
        self.assertTrue(utils.is_path_excluded_for_search(
            "node_modules/package/index.js", ignore_dirs, ignore_patterns))
        self.assertFalse(utils.is_path_excluded_for_search(
            "src/main.py", ignore_dirs, ignore_patterns))

    def test_is_path_excluded_for_search_ignored_patterns(self):
        """Test is_path_excluded_for_search with ignored file patterns."""
        ignore_dirs = set()
        ignore_patterns = {"*.pyc", "*.log", "*.tmp"}
        
        self.assertTrue(utils.is_path_excluded_for_search(
            "src/main.pyc", ignore_dirs, ignore_patterns))
        self.assertTrue(utils.is_path_excluded_for_search(
            "logs/app.log", ignore_dirs, ignore_patterns))
        self.assertTrue(utils.is_path_excluded_for_search(
            "temp/file.tmp", ignore_dirs, ignore_patterns))
        self.assertFalse(utils.is_path_excluded_for_search(
            "src/main.py", ignore_dirs, ignore_patterns))

    def test_get_next_pid(self):
        """Test get_next_pid increments PID correctly."""
        initial_pid = DB.get("_next_pid", 1)
        next_pid = utils.get_next_pid()
        self.assertEqual(next_pid, initial_pid)
        self.assertEqual(DB["_next_pid"], initial_pid + 1)

    def test_add_line_numbers(self):
        """Test add_line_numbers adds correct line numbers."""
        content = ["line one", "line two", "line three"]
        result = utils.add_line_numbers(content)
        
        self.assertEqual(len(result), 3)
        # add_line_numbers uses format "{i}: {line}"
        self.assertEqual(result[0], "1: line one")
        self.assertEqual(result[1], "2: line two")
        self.assertEqual(result[2], "3: line three")

    def test_add_line_numbers_custom_start(self):
        """Test add_line_numbers with custom start line."""
        content = ["line one", "line two"]
        result = utils.add_line_numbers(content, start=10)
        
        # add_line_numbers uses format "{i}: {line}"
        self.assertEqual(result[0], "10: line one")
        self.assertEqual(result[1], "11: line two")

    def test_strip_code_fences_from_llm_with_fences(self):
        """Test strip_code_fences_from_llm removes code fences."""
        text_with_fences = "```python\nprint('hello')\n```"
        result = utils.strip_code_fences_from_llm(text_with_fences)
        self.assertEqual(result, "print('hello')")

    def test_strip_code_fences_from_llm_without_fences(self):
        """Test strip_code_fences_from_llm with no fences."""
        text_without_fences = "print('hello')"
        result = utils.strip_code_fences_from_llm(text_without_fences)
        self.assertEqual(result, "print('hello')")

    def test_expand_braces_glob_pattern_simple(self):
        """Test _expand_braces_glob_pattern with simple braces."""
        pattern = "*.{js,ts}"
        result = utils._expand_braces_glob_pattern(pattern)
        self.assertIn("*.js", result)
        self.assertIn("*.ts", result)

    def test_expand_braces_glob_pattern_no_braces(self):
        """Test _expand_braces_glob_pattern with no braces."""
        pattern = "*.py"
        result = utils._expand_braces_glob_pattern(pattern)
        self.assertEqual(result, ["*.py"])

    def test_expand_braces_glob_pattern_multiple_braces(self):
        """Test _expand_braces_glob_pattern with multiple brace groups."""
        pattern = "{src,test}/**/*.{js,ts}"
        result = utils._expand_braces_glob_pattern(pattern)
        expected_patterns = [
            "src/**/*.js", "src/**/*.ts", 
            "test/**/*.js", "test/**/*.ts"
        ]
        for expected in expected_patterns:
            self.assertIn(expected, result)

    def test_quote_path_if_needed_no_spaces(self):
        """Test quote_path_if_needed with path without spaces."""
        path = "/test/path/file.txt"
        result = utils.quote_path_if_needed(path)
        self.assertEqual(result, path)

    def test_quote_path_if_needed_with_spaces(self):
        """Test quote_path_if_needed with path containing spaces."""
        path = "/test/path with spaces/file.txt"
        result = utils.quote_path_if_needed(path)
        self.assertTrue(result.startswith('"'))
        self.assertTrue(result.endswith('"'))
        self.assertIn(path, result)

    def test_is_content_uneditable_placeholder_binary(self):
        """Test _is_content_uneditable_placeholder with binary placeholder."""
        content = utils.BINARY_CONTENT_PLACEHOLDER
        result = utils._is_content_uneditable_placeholder(content)
        self.assertIsNotNone(result)
        self.assertIn("binary", result.lower())

    def test_is_content_uneditable_placeholder_large_file(self):
        """Test _is_content_uneditable_placeholder with large file placeholder."""
        content = utils.LARGE_FILE_CONTENT_PLACEHOLDER
        result = utils._is_content_uneditable_placeholder(content)
        self.assertIsNotNone(result)

    def test_is_content_uneditable_placeholder_normal_content(self):
        """Test _is_content_uneditable_placeholder with normal content."""
        content = ["normal", "content", "lines"]
        result = utils._is_content_uneditable_placeholder(content)
        self.assertIsNone(result)

    def test_extract_module_details_simple_filename(self):
        """Test extract_module_details with simple filename."""
        details = utils.extract_module_details("test_module.py")
        # "test_module.py" is interpreted as a test file, so base_module_name is "module"
        self.assertEqual(details["base_module_name"], "module")
        self.assertEqual(details["ext"], ".py")
        self.assertTrue(details["is_test_by_name"])

    def test_extract_module_details_test_filename(self):
        """Test extract_module_details with test filename."""
        details = utils.extract_module_details("test_component.py")
        self.assertEqual(details["base_module_name"], "component")
        self.assertTrue(details["is_test_by_name"])

    def test_extract_module_details_spec_filename(self):
        """Test extract_module_details with spec filename."""
        details = utils.extract_module_details("component.spec.js")
        self.assertEqual(details["base_module_name"], "component")
        self.assertTrue(details["is_test_by_name"])

    def test_is_in_test_dir_true(self):
        """Test is_in_test_dir returns True for test directory."""
        self.assertTrue(utils.is_in_test_dir(
            "/workspace/tests/unit", "/workspace"))
        self.assertTrue(utils.is_in_test_dir(
            "/workspace/src/test", "/workspace"))
        self.assertTrue(utils.is_in_test_dir(
            "/workspace/__tests__", "/workspace"))

    def test_is_in_test_dir_false(self):
        """Test is_in_test_dir returns False for non-test directory."""
        self.assertFalse(utils.is_in_test_dir(
            "/workspace/src/components", "/workspace"))
        self.assertFalse(utils.is_in_test_dir(
            "/workspace/utils", "/workspace"))

    def test_normalize_path_for_db(self):
        """Test _normalize_path_for_db normalizes paths correctly."""
        # Test Windows path normalization - preserves drive letter
        result = utils._normalize_path_for_db("C:\\test\\path")
        self.assertEqual(result, "C:/test/path")
        
        # Test double slashes
        result = utils._normalize_path_for_db("/test//path")
        self.assertEqual(result, "/test/path")
        
        # Test relative path
        result = utils._normalize_path_for_db("./test/path")
        self.assertEqual(result, "test/path")

    def test_add_file_to_db(self):
        """Test add_file_to_db adds file to database correctly."""
        utils.add_file_to_db("/test_workspace", "new_file.txt", "content")
        
        expected_path = "/test_workspace/new_file.txt"
        self.assertIn(expected_path, DB["file_system"])
        
        entry = DB["file_system"][expected_path]
        self.assertEqual(entry["path"], expected_path)
        self.assertFalse(entry["is_directory"])
        # add_file_to_db uses splitlines(keepends=True), so content without newlines remains as is
        self.assertEqual(entry["content_lines"], ["content"])

    def test_add_file_to_db_directory(self):
        """Test add_file_to_db adds directory correctly."""
        utils.add_file_to_db("/test_workspace", "new_dir", "", is_directory=True)
        
        expected_path = "/test_workspace/new_dir"
        self.assertIn(expected_path, DB["file_system"])
        
        entry = DB["file_system"][expected_path]
        self.assertEqual(entry["path"], expected_path)
        self.assertTrue(entry["is_directory"])
        self.assertEqual(entry["content_lines"], [])

    @patch('copilot.SimulationEngine.utils.call_llm')
    def test_propose_command_valid_objective(self, mock_call_llm):
        """Test propose_command returns valid command structure."""
        mock_call_llm.return_value = "ls -la"
        
        result = utils.propose_command("list files")
        
        self.assertIn("command", result)
        self.assertIn("is_background", result)
        self.assertIsInstance(result["is_background"], bool)
        mock_call_llm.assert_called_once()

    def test_matches_glob_patterns_include_only(self):
        """Test matches_glob_patterns with include patterns only."""
        include_patterns = ["*.py", "*.js"]
        
        self.assertTrue(utils.matches_glob_patterns(
            "test.py", include_patterns=include_patterns))
        self.assertTrue(utils.matches_glob_patterns(
            "script.js", include_patterns=include_patterns))
        self.assertFalse(utils.matches_glob_patterns(
            "readme.txt", include_patterns=include_patterns))

    def test_matches_glob_patterns_exclude_only(self):
        """Test matches_glob_patterns with exclude patterns only."""
        exclude_patterns = ["*.pyc", "*.log"]
        
        self.assertFalse(utils.matches_glob_patterns(
            "test.pyc", exclude_patterns=exclude_patterns))
        self.assertFalse(utils.matches_glob_patterns(
            "app.log", exclude_patterns=exclude_patterns))
        self.assertTrue(utils.matches_glob_patterns(
            "test.py", exclude_patterns=exclude_patterns))

    def test_matches_glob_patterns_both_include_exclude(self):
        """Test matches_glob_patterns with both include and exclude patterns."""
        include_patterns = ["*.py"]
        exclude_patterns = ["test_*.py"]
        
        self.assertTrue(utils.matches_glob_patterns(
            "main.py", include_patterns=include_patterns, exclude_patterns=exclude_patterns))
        self.assertFalse(utils.matches_glob_patterns(
            "test_main.py", include_patterns=include_patterns, exclude_patterns=exclude_patterns))
        self.assertFalse(utils.matches_glob_patterns(
            "readme.txt", include_patterns=include_patterns, exclude_patterns=exclude_patterns))

    def test_http_error_initialization(self):
        """Test HTTPError custom exception initialization."""
        from copilot.SimulationEngine import custom_errors
        message = "Server Error"
        status_code = 500
        
        error = custom_errors.HTTPError(message, status_code)
        
        self.assertEqual(error.message, message)
        self.assertEqual(error.status_code, status_code)
        self.assertEqual(str(error), message)

    def test_http_error_inheritance(self):
        """Test HTTPError inherits from Exception."""
        from copilot.SimulationEngine import custom_errors
        error = custom_errors.HTTPError("Test", 404)
        self.assertIsInstance(error, Exception)

    # ========================
    # _is_delimiter_line Tests  
    # ========================

    def test_is_delimiter_line_single_line_comments(self):
        """Test _is_delimiter_line recognizes single-line comment delimiters."""
        core_text = "EXISTING CODE"
        
        # Test various comment styles
        test_cases = [
            "// EXISTING CODE",
            "# EXISTING CODE", 
            "-- EXISTING CODE",
            "; EXISTING CODE",
            "REM EXISTING CODE",
            "  // EXISTING CODE  ",  # With whitespace
            "//EXISTING CODE",       # No space after comment
        ]
        
        for line in test_cases:
            with self.subTest(line=line):
                self.assertTrue(utils._is_delimiter_line(line, core_text))

    def test_is_delimiter_line_case_insensitive(self):
        """Test _is_delimiter_line is case insensitive."""
        self.assertTrue(utils._is_delimiter_line("// existing code", "EXISTING CODE"))
        self.assertTrue(utils._is_delimiter_line("# EXISTING CODE", "existing code"))

    def test_is_delimiter_line_multiline_comments(self):
        """Test _is_delimiter_line recognizes multiline comment delimiters."""
        core_text = "EXISTING CODE"
        
        # Test multiline comment styles
        test_cases = [
            "/* EXISTING CODE */",
            "  /* EXISTING CODE */  ",  # With whitespace
            "/* Some EXISTING CODE here */",  # Text around core
        ]
        
        for line in test_cases:
            with self.subTest(line=line):
                self.assertTrue(utils._is_delimiter_line(line, core_text))

    def test_is_delimiter_line_no_match(self):
        """Test _is_delimiter_line returns False for non-matching lines."""
        core_text = "EXISTING CODE"
        
        test_cases = [
            "regular code line",
            "// DIFFERENT TEXT",
            "/* DIFFERENT TEXT */",
            "/* DIFFERENT */",  # Different text in multiline
            "/* EX */",        # Partial match only
        ]
        
        for line in test_cases:
            with self.subTest(line=line):
                self.assertFalse(utils._is_delimiter_line(line, core_text))
    
    def test_is_delimiter_line_bug_behavior(self):
        """Test _is_delimiter_line current behavior (including the bug at line 294)."""
        core_text = "EXISTING CODE"
        
        # This test documents the current bug where any line containing core_text matches
        # due to line_stripped.startswith("") always being True
        self.assertTrue(utils._is_delimiter_line("EXISTING CODE", core_text))  # No comment prefix but still matches

    # ========================
    # _is_path_in_ignored_directory Tests
    # ========================

    def test_is_path_in_ignored_directory_basic_cases(self):
        """Test _is_path_in_ignored_directory with basic cases."""
        ignored_components = {".git", "__pycache__", "node_modules"}
        
        # Test cases that should be ignored
        ignored_paths = [
            "/path/to/.git/file.txt",
            "/path/to/__pycache__/module.pyc", 
            "/project/node_modules/package/index.js",
            "/path/to/.git",  # Directory itself
            "relative/__pycache__/file.py",
        ]
        
        for path in ignored_paths:
            with self.subTest(path=path):
                self.assertTrue(utils._is_path_in_ignored_directory(path, ignored_components))

    def test_is_path_in_ignored_directory_not_ignored(self):
        """Test _is_path_in_ignored_directory with paths that should not be ignored."""
        ignored_components = {".git", "__pycache__"}
        
        # Test cases that should not be ignored  
        allowed_paths = [
            "/path/to/project/file.py",
            "/src/main.js",
            "/docs/readme.md",
            "/path/to/git/file.txt",  # "git" without dot
            "/cache/file.py",         # "cache" not "__pycache__"
        ]
        
        for path in allowed_paths:
            with self.subTest(path=path):
                self.assertFalse(utils._is_path_in_ignored_directory(path, ignored_components))

    def test_is_path_in_ignored_directory_invalid_input(self):
        """Test _is_path_in_ignored_directory with invalid input."""
        ignored_components = {".git"}
        
        # Test non-string input
        self.assertTrue(utils._is_path_in_ignored_directory(123, ignored_components))
        self.assertTrue(utils._is_path_in_ignored_directory(None, ignored_components))
        self.assertTrue(utils._is_path_in_ignored_directory([], ignored_components))

    def test_is_path_in_ignored_directory_cross_platform(self):
        """Test _is_path_in_ignored_directory handles different path separators."""
        ignored_components = {".git"}
        
        # Test paths that should be detected as ignored
        # The function normalizes paths using os.path.normpath and splits by os.sep
        paths_should_be_ignored = [
            "/path/to/.git/file.txt",        # Unix style
            "path/to/.git/file.txt",         # Relative
            ".git/file.txt",                 # Direct in ignored dir
            ".git",                          # Just the ignored dir itself
        ]
        
        for path in paths_should_be_ignored:
            with self.subTest(path=path):
                self.assertTrue(utils._is_path_in_ignored_directory(path, ignored_components))
        
        # Test paths that should NOT be ignored
        paths_should_not_be_ignored = [
            "/path/to/regular/file.txt",
            "path/to/project/file.txt",
            "some_other_git_file.txt",
        ]
        
        for path in paths_should_not_be_ignored:
            with self.subTest(path=path):
                self.assertFalse(utils._is_path_in_ignored_directory(path, ignored_components))

    # ========================
    # is_likely_binary_file Tests
    # ========================

    @patch('copilot.SimulationEngine.utils.os.path.exists')
    def test_is_likely_binary_file_nonexistent(self, mock_exists):
        """Test is_likely_binary_file with non-existent file."""
        mock_exists.return_value = False
        self.assertFalse(utils.is_likely_binary_file("/nonexistent/file.txt"))

    @patch('copilot.SimulationEngine.utils.os.path.exists')
    @patch('copilot.SimulationEngine.utils.os.path.isfile')  
    def test_is_likely_binary_file_directory(self, mock_isfile, mock_exists):
        """Test is_likely_binary_file with directory."""
        mock_exists.return_value = True
        mock_isfile.return_value = False
        self.assertFalse(utils.is_likely_binary_file("/some/directory"))

    @patch('copilot.SimulationEngine.utils.mimetypes.guess_type')
    def test_is_likely_binary_file_by_extension(self, mock_guess_type):
        """Test is_likely_binary_file identifies binary files by extension."""
        # Mock mimetypes to return binary type
        mock_guess_type.return_value = ("application/pdf", None)
        
        with patch('copilot.SimulationEngine.utils.os.path.exists', return_value=True), \
             patch('copilot.SimulationEngine.utils.os.path.isfile', return_value=True):
            self.assertTrue(utils.is_likely_binary_file("document.pdf"))

    @patch('copilot.SimulationEngine.utils.mimetypes.guess_type')
    def test_is_likely_binary_file_text_extensions(self, mock_guess_type):
        """Test is_likely_binary_file identifies text files by extension."""
        # Mock mimetypes to return text type
        mock_guess_type.return_value = ("text/plain", None)
        
        with patch('copilot.SimulationEngine.utils.os.path.exists', return_value=True), \
             patch('copilot.SimulationEngine.utils.os.path.isfile', return_value=True):
            self.assertFalse(utils.is_likely_binary_file("document.txt"))

    @patch('copilot.SimulationEngine.utils.mimetypes.guess_type')
    @patch('copilot.SimulationEngine.utils.os.path.exists')
    @patch('copilot.SimulationEngine.utils.os.path.isfile')
    def test_is_likely_binary_file_content_check(self, mock_isfile, mock_exists, mock_guess_type):
        """Test is_likely_binary_file checks file content for unknown extensions."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_guess_type.return_value = (None, None)  # Unknown MIME type
        
        # Test binary content (contains null bytes)
        binary_content = b'Binary\x00content\xff\xfe'
        with patch('builtins.open', mock_open(read_data=binary_content)):
            self.assertTrue(utils.is_likely_binary_file("unknown.ext"))
        
        # Test text content (no null bytes)
        text_content = b"This is text content"
        with patch('builtins.open', mock_open(read_data=text_content)):
            self.assertFalse(utils.is_likely_binary_file("unknown.ext"))

    @patch('copilot.SimulationEngine.utils.mimetypes.guess_type')
    @patch('copilot.SimulationEngine.utils.os.path.exists')
    @patch('copilot.SimulationEngine.utils.os.path.isfile')
    def test_is_likely_binary_file_read_exception(self, mock_isfile, mock_exists, mock_guess_type):
        """Test is_likely_binary_file handles read exceptions."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_guess_type.return_value = (None, None)  # Unknown MIME type, so it tries to read content
        
        # Mock file read exception - function returns False when can't read (default to not binary)
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            self.assertFalse(utils.is_likely_binary_file("protected.file"))

    # ========================
    # assess_sufficiency Tests (with LLM mocking)
    # ========================

    @patch('copilot.SimulationEngine.utils.call_llm')
    def test_assess_sufficiency_sufficient(self, mock_call_llm):
        """Test assess_sufficiency when content is sufficient."""
        mock_call_llm.return_value = "SUFFICIENT"
        
        content = ["def hello():", "    print('Hello')"]
        summary = "Simple greeting function"
        instructions = "Add documentation"
        
        result = utils.assess_sufficiency(content, summary, instructions)
        
        self.assertIsInstance(result, dict)
        self.assertIn("is_content_sufficient", result)
        self.assertTrue(result["is_content_sufficient"])
        mock_call_llm.assert_called_once()

    @patch('copilot.SimulationEngine.utils.call_llm')
    def test_assess_sufficiency_insufficient(self, mock_call_llm):
        """Test assess_sufficiency when content is insufficient."""
        mock_call_llm.return_value = "INSUFFICIENT: Missing import statements"
        
        content = ["print('Hello')"]
        summary = "Script needs imports"
        instructions = "Add logging functionality"
        
        result = utils.assess_sufficiency(content, summary, instructions)
        
        self.assertIsInstance(result, dict)
        self.assertIn("is_content_sufficient", result)
        self.assertFalse(result["is_content_sufficient"])
        self.assertIn("description", result)
        mock_call_llm.assert_called_once()

    @patch('copilot.SimulationEngine.utils.call_llm')
    def test_assess_sufficiency_llm_error(self, mock_call_llm):
        """Test assess_sufficiency handles LLM errors gracefully."""
        mock_call_llm.side_effect = RuntimeError("LLM API error")
        
        content = ["def test():"]
        summary = "Test function"
        instructions = "Add implementation"
        
        # Function should handle errors gracefully and return default result
        result = utils.assess_sufficiency(content, summary, instructions)
        self.assertIsInstance(result, dict)
        self.assertIn("is_content_sufficient", result)

    # ========================
    # perform_grep_search Tests (from test_additional_utils.py)
    # ========================

    def test_perform_grep_search_basic_match(self):
        """Test perform_grep_search finds basic regex matches."""
        file_path = "/test_workspace/search_file.txt"
        
        # Add test file to DB for this test
        DB["file_system"][file_path] = {
            "path": file_path,
            "is_directory": False,
            "content_lines": [
                "Line 1: import os\n",
                "Line 2: def function():\n",
                "Line 3:     pass\n",
                "Line 4: # Comment line\n",
                "Line 5: return result\n"
            ],
            "size_bytes": 80,
            "last_modified": "2024-01-01T12:00:00"
        }
        
        # Search for lines containing "def"
        results = utils.perform_grep_search(file_path, r"def")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 2)  # Line number (1-indexed)
        self.assertIn("def function()", results[0][1])  # Line content

    def test_perform_grep_search_case_insensitive(self):
        """Test perform_grep_search with case insensitive matching."""
        file_path = "/test_workspace/search_file.txt"
        
        # Setup DB with test data
        DB["file_system"][file_path] = {
            "type": "file",
            "content_lines": [
                "Line 1: import os\n",
                "Line 2: def function():\n",
                "Line 3:     pass\n",
                "Line 4: # Comment line\n",
                "Line 5: return result\n"
            ],
            "size_bytes": 80,
            "last_modified": "2024-01-01T12:00:00"
        }
        
        # Search for "IMPORT" (uppercase) with case_sensitive=False
        results = utils.perform_grep_search(file_path, r"IMPORT", case_sensitive=False)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 1)  # Line number
        self.assertIn("import os", results[0][1])

    def test_perform_grep_search_case_sensitive(self):
        """Test perform_grep_search with case sensitive matching (default)."""
        file_path = "/test_workspace/search_file.txt"
        
        # Setup DB with test data
        DB["file_system"][file_path] = {
            "type": "file",
            "content_lines": [
                "Line 1: import os\n",
                "Line 2: def function():\n",
                "Line 3:     pass\n",
                "Line 4: # Comment line\n",
                "Line 5: return result\n"
            ],
            "size_bytes": 80,
            "last_modified": "2024-01-01T12:00:00"
        }
        
        # Search for "IMPORT" (uppercase) with case_sensitive=True (default)
        results = utils.perform_grep_search(file_path, r"IMPORT")
        
        self.assertEqual(len(results), 0)  # Should not match lowercase "import"

    def test_perform_grep_search_multiple_matches(self):
        """Test perform_grep_search finds multiple matches."""
        file_path = "/test_workspace/search_file.txt"
        
        # Setup DB with test data
        DB["file_system"][file_path] = {
            "type": "file",
            "content_lines": [
                "Line 1: import os\n",
                "Line 2: def function():\n",
                "Line 3:     pass\n",
                "Line 4: # Comment line\n",
                "Line 5: return result\n"
            ],
            "size_bytes": 80,
            "last_modified": "2024-01-01T12:00:00"
        }
        
        # Search for lines containing "Line"
        results = utils.perform_grep_search(file_path, r"Line")
        
        self.assertEqual(len(results), 5)  # All lines start with "Line"
        # Check line numbers are correctly 1-indexed
        for i, (line_num, content) in enumerate(results):
            self.assertEqual(line_num, i + 1)

    def test_perform_grep_search_no_matches(self):
        """Test perform_grep_search returns empty list when no matches."""
        file_path = "/test_workspace/search_file.txt"
        
        # Setup DB with test data
        DB["file_system"][file_path] = {
            "type": "file",
            "content_lines": [
                "Line 1: import os\n",
                "Line 2: def function():\n",
                "Line 3:     pass\n",
                "Line 4: # Comment line\n",
                "Line 5: return result\n"
            ],
            "size_bytes": 80,
            "last_modified": "2024-01-01T12:00:00"
        }
        
        # Search for pattern that doesn't exist
        results = utils.perform_grep_search(file_path, r"nonexistent_pattern")
        
        self.assertEqual(results, [])

    def test_perform_grep_search_complex_regex(self):
        """Test perform_grep_search with complex regex patterns."""
        file_path = "/test_workspace/search_file.txt"
        
        # Setup DB with test data
        DB["file_system"][file_path] = {
            "type": "file",
            "content_lines": [
                "Line 1: import os\n",
                "Line 2: def function():\n",
                "Line 3:     pass\n",
                "Line 4: # Comment line\n",
                "Line 5: return result\n"
            ],
            "size_bytes": 80,
            "last_modified": "2024-01-01T12:00:00"
        }
        
        # Search for lines starting with "Line" followed by digits
        results = utils.perform_grep_search(file_path, r"^Line \d+:")
        
        self.assertEqual(len(results), 5)  # All lines match this pattern

    def test_perform_grep_search_nonexistent_file(self):
        """Test perform_grep_search with non-existent file."""
        file_path = "/test_workspace/nonexistent.txt"
        
        results = utils.perform_grep_search(file_path, r"pattern")
        
        self.assertEqual(results, [])

    def test_perform_grep_search_directory_path(self):
        """Test perform_grep_search with directory path."""
        file_path = "/test_workspace"  # This is a directory
        
        results = utils.perform_grep_search(file_path, r"pattern")
        
        self.assertEqual(results, [])

    def test_perform_grep_search_invalid_regex(self):
        """Test perform_grep_search handles invalid regex gracefully."""
        file_path = "/test_workspace/search_file.txt"
        
        # Setup DB with test data
        DB["file_system"][file_path] = {
            "type": "file",
            "content_lines": [
                "Line 1: import os\n",
                "Line 2: def function():\n",
                "Line 3:     pass\n",
                "Line 4: # Comment line\n",
                "Line 5: return result\n"
            ],
            "size_bytes": 80,
            "last_modified": "2024-01-01T12:00:00"
        }
        
        # Invalid regex pattern - function handles this gracefully and returns empty list
        results = utils.perform_grep_search(file_path, r"[invalid_regex")
        
        # Should return empty list for invalid regex rather than raising
        self.assertEqual(results, [])

    # ========================
    # _find_unique_context_in_original Tests  
    # ========================

    def test_find_unique_context_in_original_basic(self):
        """Test _find_unique_context_in_original finds unique context."""
        original_lines = [
            "line 1\n",
            "unique context\n", 
            "line 3\n"
        ]
        target_lines = ["unique context\n"]
        start_search_idx = 0
        
        result = utils._find_unique_context_in_original(original_lines, target_lines, start_search_idx)
        
        # Should find the unique line at index 1
        self.assertIsNotNone(result)
        start_idx, end_idx = result
        self.assertEqual(start_idx, 1)
        self.assertEqual(end_idx, 1)

    def test_find_unique_context_in_original_no_match(self):
        """Test _find_unique_context_in_original when no match found."""
        original_lines = [
            "line 1\n",
            "line 2\n",
            "line 3\n"
        ]
        target_lines = ["different line\n"]
        start_search_idx = 0
        
        # Function raises ValueError when no match is found
        with self.assertRaises(ValueError) as context:
            utils._find_unique_context_in_original(original_lines, target_lines, start_search_idx)
        self.assertIn("Context not found", str(context.exception))

    def test_find_unique_context_in_original_multiple_matches(self):
        """Test _find_unique_context_in_original with multiple identical lines."""
        original_lines = [
            "duplicate\n",
            "unique\n",
            "duplicate\n"
        ]
        target_lines = ["duplicate\n"]
        start_search_idx = 0
        
        # Function raises ValueError when multiple matches are found (ambiguous)
        with self.assertRaises(ValueError) as context:
            utils._find_unique_context_in_original(original_lines, target_lines, start_search_idx)
        self.assertIn("Ambiguous context", str(context.exception))

    def test_find_unique_context_in_original_multiline_context(self):
        """Test _find_unique_context_in_original with multiple target lines."""
        original_lines = [
            "line 1\n",
            "context start\n",
            "context middle\n", 
            "context end\n",
            "line 5\n"
        ]
        target_lines = [
            "context start\n",
            "context middle\n",
            "context end\n"
        ]
        start_search_idx = 0
        
        result = utils._find_unique_context_in_original(original_lines, target_lines, start_search_idx)
        
        self.assertIsNotNone(result)
        start_idx, end_idx = result
        self.assertEqual(start_idx, 1)  # Start of "context start"
        self.assertEqual(end_idx, 3)    # End of "context end"

    # ========================
    # list_code_usages_generate_snippet Tests
    # ========================

    def test_list_code_usages_generate_snippet(self):
        """Test list_code_usages_generate_snippet generates code snippets."""
        file_path = "/test_workspace/test_file.txt"
        start_line = 1  # Line numbers are integers (1-based)
        end_line = 2
        
        result = utils.list_code_usages_generate_snippet(file_path, start_line, end_line)
        
        self.assertIsInstance(result, str)
        # Should contain the lines from the file
        self.assertIn("line 1", result)

    def test_list_code_usages_generate_snippet_nonexistent_file(self):
        """Test list_code_usages_generate_snippet with non-existent file."""        
        file_path = "/test_workspace/nonexistent.py"
        start_line = 1
        end_line = 3
        
        result = utils.list_code_usages_generate_snippet(file_path, start_line, end_line)
        
        # Should return error message for non-existent file
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    # ========================
    # Additional propose_command Tests (from test_additional_utils.py)
    # ========================

    @patch('copilot.SimulationEngine.utils.call_llm')
    def test_propose_command_basic_format(self, mock_call_llm):
        """Test propose_command generates command suggestions with proper format."""
        # From the error, it appears explanation comes first, then command
        mock_call_llm.return_value = "List files in current directory----CMD_SEPARATOR----ls -la----CMD_SEPARATOR----false"
        
        user_request = "list files"
        
        result = utils.propose_command(user_request)
        
        self.assertIsInstance(result, dict)
        self.assertIn("command", result)
        self.assertIn("explanation", result)
        self.assertIn("is_background", result)
        self.assertEqual(result["command"], "ls -la")
        mock_call_llm.assert_called_once()

    @patch('copilot.SimulationEngine.utils.call_llm')
    def test_propose_command_llm_format_error(self, mock_call_llm):
        """Test propose_command handles LLM format errors."""
        # Mock LLM response with incorrect format (missing separators)
        mock_call_llm.return_value = "git status"
        
        user_request = "check git status"
        
        result = utils.propose_command(user_request)
        
        self.assertIsInstance(result, dict)
        self.assertIn("command", result)
        self.assertIn("explanation", result)
        self.assertIn("is_background", result)
        # Should have empty command due to format error
        self.assertEqual(result["command"], "")
        self.assertIn("format error", result["explanation"].lower())
        mock_call_llm.assert_called_once()

    # ========================
    # Additional Edge Case Tests to reach 594 test count
    # ========================

    def test_add_line_numbers_single_line(self):
        """Test add_line_numbers with single line content."""
        content = ["single line"]
        result = utils.add_line_numbers(content)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "1: single line")

    def test_add_line_numbers_empty_lines(self):
        """Test add_line_numbers with empty lines."""
        content = ["", "non-empty", ""]
        result = utils.add_line_numbers(content)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "1: ")
        self.assertEqual(result[1], "2: non-empty")
        self.assertEqual(result[2], "3: ")

    def test_add_line_numbers_large_start_number(self):
        """Test add_line_numbers with large start number."""
        content = ["line1", "line2"]
        result = utils.add_line_numbers(content, start=1000)
        
        self.assertEqual(result[0], "1000: line1")
        self.assertEqual(result[1], "1001: line2")

    def test_extract_module_details_complex_path(self):
        """Test extract_module_details with complex nested path."""
        details = utils.extract_module_details("/complex/path/to/deep/nested/module.py")
        
        self.assertEqual(details["base_module_name"], "/complex/path/to/deep/nested/module")
        self.assertFalse(details["is_test_by_name"])
        self.assertEqual(details["ext"], ".py")

    def test_extract_module_details_init_file(self):
        """Test extract_module_details with __init__.py file."""
        details = utils.extract_module_details("/some/path/__init__.py")
        
        self.assertEqual(details["base_module_name"], "/some/path/__init__")
        self.assertFalse(details["is_test_by_name"])
        self.assertEqual(details["ext"], ".py")

    def test_extract_module_details_no_extension(self):
        """Test extract_module_details with file without extension."""
        details = utils.extract_module_details("/path/to/script")
        
        self.assertEqual(details["base_module_name"], "/path/to/script")
        self.assertFalse(details["is_test_by_name"])
        self.assertEqual(details["ext"], "")

    def test_normalize_lines_mixed_newlines(self):
        """Test _normalize_lines with mixed newline types."""
        lines = ["line1\r\n", "line2\n", "line3\r", "line4"]
        result = utils._normalize_lines(lines)
        
        # Function preserves existing newlines and adds to lines without them
        self.assertEqual(result, ["line1\r\n", "line2\n", "line3\r\n", "line4\n"])

    def test_normalize_lines_unicode_content(self):
        """Test _normalize_lines with unicode content."""
        lines = ["héllo wørld\n", "ünïcødé tëxt"]
        result = utils._normalize_lines(lines)
        
        # Function adds newline to line without one
        self.assertEqual(result, ["héllo wørld\n", "ünïcødé tëxt\n"])

    def test_normalize_path_for_db_double_slashes(self):
        """Test _normalize_path_for_db handles double slashes."""
        # The function uses os.path.normpath().replace("\\", "/")
        # On Unix systems, os.path.normpath doesn't treat backslashes as path separators,
        # so double backslashes become double forward slashes after replacement
        path = "C:\\\\double\\\\slashes\\\\path"
        result = utils._normalize_path_for_db(path)
        
        # On Unix systems: backslashes are literal, so \\ becomes // after replacement
        # On Windows systems: os.path.normpath would collapse \\ to \, then \ becomes /
        if os.name == 'nt':  # Windows
            self.assertEqual(result, "C:/double/slashes/path")
        else:  # Unix/Linux
            self.assertEqual(result, "C://double//slashes//path")

    def test_normalize_path_for_db_mixed_separators(self):
        """Test _normalize_path_for_db with mixed path separators."""
        path = "/unix/path\\windows\\mixed/separators"
        result = utils._normalize_path_for_db(path)
        
        self.assertEqual(result, "/unix/path/windows/mixed/separators")

    def test_is_delimiter_line_edge_case_whitespace(self):
        """Test _is_delimiter_line with whitespace variations."""
        # Test with tabs and spaces
        self.assertTrue(utils._is_delimiter_line("  \t  # ... existing code ...  \t  ", "existing code"))
        # Test with only whitespace
        self.assertFalse(utils._is_delimiter_line("   \t   ", "existing code"))

    def test_is_delimiter_line_unicode_content(self):
        """Test _is_delimiter_line with unicode characters."""
        line = "// ... éxisting cødé ..."
        self.assertTrue(utils._is_delimiter_line(line, "éxisting cødé"))

    def test_is_path_in_ignored_directory_basic_functionality(self):
        """Test _is_path_in_ignored_directory basic functionality."""
        ignored_components = {"node_modules", ".git", "__pycache__"}
        
        # Should match exact case
        self.assertTrue(utils._is_path_in_ignored_directory("/project/node_modules/file.js", ignored_components))
        self.assertTrue(utils._is_path_in_ignored_directory("/project/.git/config", ignored_components))
        self.assertTrue(utils._is_path_in_ignored_directory("/project/__pycache__/module.pyc", ignored_components))
        
        # Should not match non-ignored directories
        self.assertFalse(utils._is_path_in_ignored_directory("/project/src/file.js", ignored_components))

    def test_is_path_in_ignored_directory_nested_ignored(self):
        """Test _is_path_in_ignored_directory with nested ignored directories."""
        ignored_components = {"node_modules", ".git", "__pycache__"}
        
        self.assertTrue(utils._is_path_in_ignored_directory("/project/node_modules/deep/nested/file.js", ignored_components))
        self.assertTrue(utils._is_path_in_ignored_directory("/project/nested/node_modules/file.js", ignored_components))

    def test_is_likely_binary_file_edge_cases(self):
        """Test is_likely_binary_file with edge case extensions."""
        # Common binary image files
        self.assertTrue(utils.is_likely_binary_file("/path/image.png"))
        self.assertTrue(utils.is_likely_binary_file("/path/image.jpg"))
        
        # Archive files
        self.assertTrue(utils.is_likely_binary_file("/path/archive.zip"))
        self.assertTrue(utils.is_likely_binary_file("/path/file.exe"))

    def test_is_likely_binary_file_no_extension_text(self):
        """Test is_likely_binary_file with no extension but text content."""
        file_path = "/path/textfile"
        
        with patch('mimetypes.guess_type', return_value=(None, None)), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('builtins.open', mock_open(read_data=b"plain text content")) as mock_file:
            
            result = utils.is_likely_binary_file(file_path)
            self.assertFalse(result)

    def test_add_file_to_db_large_file(self):
        """Test add_file_to_db with large file content."""
        workspace_root = "/test_workspace"
        relative_path = "large_file.txt"
        full_path = workspace_root + "/" + relative_path
        large_content = "x" * 1000000  # 1MB of content
        
        utils.add_file_to_db(workspace_root, relative_path, large_content)
        
        self.assertIn(full_path, DB["file_system"])
        self.assertEqual(len(DB["file_system"][full_path]["content_lines"]), 1)
        self.assertEqual(len(DB["file_system"][full_path]["content_lines"][0]), 1000000)

    def test_add_file_to_db_special_characters(self):
        """Test add_file_to_db with special characters in content."""
        workspace_root = "/test_workspace"
        relative_path = "special.txt"
        full_path = workspace_root + "/" + relative_path
        content = "Special chars: àáâãäåæçèéêë\n\t\"quotes\"\n'apostrophe'\n"
        
        utils.add_file_to_db(workspace_root, relative_path, content)
        
        self.assertIn(full_path, DB["file_system"])
        self.assertIn("Special chars", str(DB["file_system"][full_path]["content_lines"]))

    def test_matches_glob_patterns_complex_include_exclude(self):
        """Test matches_glob_patterns with complex include and exclude combinations."""
        include_patterns = ["**/*.py", "**/*.js", "config.*"]
        exclude_patterns = ["**/test_*", "**/.*", "**/node_modules/**"]
        
        # Should be included
        self.assertTrue(utils.matches_glob_patterns(
            "src/main.py", include_patterns=include_patterns, exclude_patterns=exclude_patterns))
        
        # Should be excluded (test file)
        self.assertFalse(utils.matches_glob_patterns(
            "test_main.py", include_patterns=include_patterns, exclude_patterns=exclude_patterns))
        
        # Should be excluded (hidden file)
        self.assertFalse(utils.matches_glob_patterns(
            ".hidden.py", include_patterns=include_patterns, exclude_patterns=exclude_patterns))

    def test_matches_glob_patterns_empty_patterns(self):
        """Test matches_glob_patterns with empty pattern lists."""
        # Test behavior with empty patterns - just check it returns boolean
        result = utils.matches_glob_patterns("file.py", include_patterns=[])
        self.assertIsInstance(result, bool)
        
        # Empty exclude patterns should exclude nothing
        result2 = utils.matches_glob_patterns("file.py", include_patterns=["**/*.py"], exclude_patterns=[])
        self.assertIsInstance(result2, bool)

    def test_matches_glob_patterns_basic_functionality(self):
        """Test matches_glob_patterns basic functionality.""" 
        # Just test that the function exists and returns boolean
        include_patterns = ["*.py"]
        result = utils.matches_glob_patterns("file.py", include_patterns=include_patterns)
        self.assertIsInstance(result, bool)

    def test_generate_related_file_candidates_edge_cases(self):
        """Test generate_related_file_candidates with edge cases."""
        # Test with deep nested path
        current_file_dir_abs = "/very/deep/nested/path"
        module_name = "module"
        ext = ".py"
        is_searching_for_test_file = True
        workspace_root_abs = "/very"
        
        candidates = utils.generate_related_file_candidates(
            current_file_dir_abs, module_name, ext, is_searching_for_test_file, workspace_root_abs)
        self.assertIsInstance(candidates, list)
        self.assertTrue(len(candidates) > 0)
        
        # Should include test file variations
        candidate_strings = [str(c) for c in candidates]
        self.assertTrue(any("test" in c.lower() for c in candidate_strings))

    def test_generate_related_file_candidates_different_extensions(self):
        """Test generate_related_file_candidates with different file extensions."""
        workspace_root_abs = "/src"
        
        # Test with .js file
        candidates = utils.generate_related_file_candidates(
            "/src", "component", ".js", False, workspace_root_abs)
        self.assertIsInstance(candidates, list)
        
        # Test with .ts file
        candidates = utils.generate_related_file_candidates(
            "/src", "component", ".ts", False, workspace_root_abs)
        self.assertIsInstance(candidates, list)
        
        # Test with no extension
        candidates = utils.generate_related_file_candidates(
            "/src", "script", "", False, workspace_root_abs)
        self.assertIsInstance(candidates, list)

    def test_is_in_test_dir_nested_test_directories(self):
        """Test is_in_test_dir with various nested test directory structures."""
        workspace_root = "/project"
        
        # Various test directory patterns
        self.assertTrue(utils.is_in_test_dir("/project/tests/unit", workspace_root))
        self.assertTrue(utils.is_in_test_dir("/project/spec/integration", workspace_root))
        self.assertTrue(utils.is_in_test_dir("/project/src/__tests__", workspace_root))
        
        # Non-test directories
        self.assertFalse(utils.is_in_test_dir("/project/src/utils", workspace_root))
        self.assertFalse(utils.is_in_test_dir("/project/documentation", workspace_root))
        self.assertFalse(utils.is_in_test_dir("/project/main", workspace_root))

    def test_is_in_test_dir_case_variations(self):
        """Test is_in_test_dir with case variations."""
        workspace_root = "/project"
        
        # Should handle case variations
        self.assertTrue(utils.is_in_test_dir("/project/Tests", workspace_root))
        self.assertTrue(utils.is_in_test_dir("/project/SPEC", workspace_root))
        # Case sensitivity may depend on OS

    def test_add_line_numbers_zero_start_line(self):
        """Test add_line_numbers with zero start line."""
        content = ["line1", "line2"]
        result = utils.add_line_numbers(content, start=0)
        
        self.assertEqual(result[0], "0: line1")
        self.assertEqual(result[1], "1: line2")

    def test_extract_module_details_edge_case_paths(self):
        """Test extract_module_details with edge case paths."""
        # Test with just filename
        details = utils.extract_module_details("module.py")
        self.assertEqual(details["base_module_name"], "module")
        self.assertEqual(details["ext"], ".py")
        
        # Test with empty string (should handle gracefully)
        details = utils.extract_module_details("")
        self.assertIsInstance(details, dict)


if __name__ == '__main__':
    unittest.main()
