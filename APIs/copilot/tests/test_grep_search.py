import copy
import unittest

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import grep_search

class TestGrepSearch(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB["workspace_root"] = "/test_ws"
        DB["cwd"] = "/test_ws"
        DB["file_system"] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _add_file(self, relative_path: str, content_lines_as_read: list[str]):
        """
        Adds a file to the DB.
        content_lines_as_read: list of strings, each representing a line as read by file.readlines()
                               (i.e., typically ending with \n, except possibly the last line).
        """
        if not DB.get("workspace_root"):
            pass

        full_path = f"{DB['workspace_root']}{relative_path if relative_path.startswith('/') else '/' + relative_path}"

        DB["file_system"][full_path] = {
            "path": full_path,
            "is_directory": False,
            "content_lines": content_lines_as_read,
            "size_bytes": sum(len(line.encode('utf-8')) for line in content_lines_as_read),
            "last_modified": "2023-01-01T12:00:00Z"
        }

    def _add_dir(self, relative_path: str):
        if not DB.get("workspace_root"):
            pass

        full_path = f"{DB['workspace_root']}{relative_path if relative_path.startswith('/') else '/' + relative_path}"
        DB["file_system"][full_path] = {
            "path": full_path,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2023-01-01T12:00:00Z"
        }

    # --- Error Condition Tests ---

    def test_invalid_search_pattern_type_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=grep_search,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="search_pattern must be a string.",
            search_pattern=123
        )

    def test_invalid_regex_syntax_raises_invalid_search_pattern_error(self):
        self._add_file("/file1.txt", ["some content\n"])
        self.assert_error_behavior(
            func_to_call=grep_search,
            expected_exception_type=custom_errors.InvalidSearchPatternError,
            expected_message="Invalid search pattern: unterminated character set at position 0",
            search_pattern="["
        )

    def test_empty_search_pattern_error(self):
        self._add_file("/file1.txt", ["some content\n"])
        self.assert_error_behavior(
            func_to_call=grep_search,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Search pattern cannot be empty.",
            search_pattern=""
        )

    def test_workspace_not_available_if_root_missing(self):
        original_root = DB.pop("workspace_root", None)
        try:
            self.assert_error_behavior(
                func_to_call=grep_search,
                expected_exception_type=custom_errors.WorkspaceNotAvailableError,
                expected_message="Workspace is not available or not initialized.",
                search_pattern="test"
            )
        finally:
            if original_root is not None:
                DB["workspace_root"] = original_root

    def test_workspace_not_available_if_root_empty_string(self):
        original_root = DB["workspace_root"]
        DB["workspace_root"] = ""
        try:
            self.assert_error_behavior(
                func_to_call=grep_search,
                expected_exception_type=custom_errors.WorkspaceNotAvailableError,
                expected_message="Workspace is not available or not initialized.",
                search_pattern="test"
            )
        finally:
            DB["workspace_root"] = original_root

    # --- Success and Edge Case Tests ---

    def test_simple_string_match_single_file(self):
        self._add_file("/file1.txt", ["Hello world\n", "This is a test line with world\n"])
        results = grep_search(search_pattern="world")

        self.assertEqual(len(results), 2)
        expected_match1 = {
            "file_path": "/test_ws/file1.txt", "line_number": 1, "line_content": "Hello world",
            "match_start_column": 6, "match_end_column": 11
        }
        expected_match2 = {
            "file_path": "/test_ws/file1.txt", "line_number": 2, "line_content": "This is a test line with world",
            "match_start_column": 25, "match_end_column": 30
        }
        # Results from the same file should be ordered by line number.
        self.assertEqual(results[0], expected_match1)
        self.assertEqual(results[1], expected_match2)

    def test_regex_match_digits(self):
        self._add_file("/data.txt", ["Log entry: 123 items\n", "Error code: 45\n", "No numbers here\n"])
        results = grep_search(search_pattern=r"\d+")

        self.assertEqual(len(results), 2)
        expected_match1 = {
            "file_path": "/test_ws/data.txt", "line_number": 1, "line_content": "Log entry: 123 items",
            "match_start_column": 11, "match_end_column": 14
        }
        expected_match2 = {
            "file_path": "/test_ws/data.txt", "line_number": 2, "line_content": "Error code: 45",
            "match_start_column": 12, "match_end_column": 14
        }
        self.assertIn(expected_match1, results)
        self.assertIn(expected_match2, results)

    def test_match_multiple_files(self):
        self._add_file("/file1.py", ["import os\n", "print('hello')\n"])
        self._add_file("/file2.txt", ["A simple hello message.\n"])
        self._add_file("/file3.md", ["# Hello World\n"])

        results = grep_search(search_pattern="hello")
        self.assertEqual(len(results), 2)

        found_files = {res["file_path"] for res in results}
        self.assertIn("/test_ws/file1.py", found_files)
        self.assertIn("/test_ws/file2.txt", found_files)
        self.assertNotIn("/test_ws/file3.md", found_files)

        expected_py_match = {
            "file_path": "/test_ws/file1.py", "line_number": 2, "line_content": "print('hello')",
            "match_start_column": 7, "match_end_column": 12
        }
        expected_txt_match = {
            "file_path": "/test_ws/file2.txt", "line_number": 1, "line_content": "A simple hello message.",
            "match_start_column": 9, "match_end_column": 14
        }
        self.assertIn(expected_py_match, results)
        self.assertIn(expected_txt_match, results)

    def test_multiple_matches_on_one_line_returns_first(self):
        self._add_file("/repeat.txt", ["test test test\n"])
        results = grep_search(search_pattern="test")
        self.assertEqual(len(results), 3)
        expected = {
            "file_path": "/test_ws/repeat.txt", "line_number": 1, "line_content": "test test test",
            "match_start_column": 0, "match_end_column": 4
        }
        self.assertEqual(results[0], expected)

    def test_search_is_case_sensitive_by_default(self):
        self._add_file("/case.txt", ["Pattern\n", "pattern\n"])
        results = grep_search(search_pattern="Pattern")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["line_number"], 1)
        self.assertEqual(results[0]["line_content"], "Pattern")

    def test_results_limited_to_20(self):
        for i in range(25):
            self._add_file(f"/limit_file_{i}.txt", [f"match line content {i}\n"])
        results = grep_search(search_pattern="match")
        self.assertEqual(len(results), 20)

    def test_results_exactly_20_matches(self):
        for i in range(20):
            self._add_file(f"/exact_20_file_{i}.txt", [f"match line content {i}\n"])
        results = grep_search(search_pattern="match")
        self.assertEqual(len(results), 20)

    def test_results_less_than_20_matches(self):
        self._add_file("/few_matches_1.txt", ["match one\n"])
        self._add_file("/few_matches_2.txt", ["match two\n"])
        results = grep_search(search_pattern="match")
        self.assertEqual(len(results), 2)

    def test_no_files_in_workspace_returns_empty_list(self):
        self.assert_error_behavior(
            func_to_call=grep_search,
            expected_exception_type=custom_errors.WorkspaceNotAvailableError,
            expected_message="Workspace is not available or not initialized.",
            search_pattern="anything"
        )

    def test_only_directories_in_workspace_returns_empty_list(self):
        self._add_dir("/dir1")
        self._add_dir("/foo/bar_dir")
        results = grep_search(search_pattern="anything")
        self.assertEqual(len(results), 0)

    def test_search_in_empty_file_no_matches(self):
        self._add_file("/empty.txt", [])
        results = grep_search(search_pattern="anything")
        self.assertEqual(len(results), 0)

    def test_search_in_file_with_only_empty_lines(self):
        self._add_file("/empty_lines.txt", ["\n", "\n"])

        results_non_empty = grep_search(search_pattern="content")
        self.assertEqual(len(results_non_empty), 0)

        results_empty_regex = grep_search(search_pattern=r"^$")  # Matches empty lines
        self.assertEqual(len(results_empty_regex), 2)
        expected1 = {"file_path": "/test_ws/empty_lines.txt", "line_number": 1, "line_content": "",
                     "match_start_column": 0, "match_end_column": 0}
        expected2 = {"file_path": "/test_ws/empty_lines.txt", "line_number": 2, "line_content": "",
                     "match_start_column": 0, "match_end_column": 0}
        self.assertIn(expected1, results_empty_regex)
        self.assertIn(expected2, results_empty_regex)

    def test_file_with_no_matching_content_returns_empty_list_for_that_file(self):
        self._add_file("/no_match.txt", ["some other text\n", "nothing here\n"])
        self._add_file("/has_match.txt", ["find this pattern\n"])
        results = grep_search(search_pattern="pattern")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["file_path"], "/test_ws/has_match.txt")

    def test_search_pattern_with_regex_metacharacters(self):
        self._add_file("/regex_test.txt", ["line with (parentheses)\n", "dot.separated\n", "star*char\n"])

        results_parens = grep_search(search_pattern=r"\(parentheses\)")
        self.assertEqual(len(results_parens), 1)
        self.assertEqual(results_parens[0]["line_content"], "line with (parentheses)")
        self.assertEqual(results_parens[0]["match_start_column"], 10)
        self.assertEqual(results_parens[0]["match_end_column"], 23)

        results_dot = grep_search(search_pattern=r"dot.separated")
        self.assertEqual(len(results_dot), 1)
        self.assertEqual(results_dot[0]["line_content"], "dot.separated")
        self.assertEqual(results_dot[0]["match_start_column"], 0)
        self.assertEqual(results_dot[0]["match_end_column"], 13)

        results_star = grep_search(search_pattern=r"star\*char")
        self.assertEqual(len(results_star), 1)
        self.assertEqual(results_star[0]["line_content"], "star*char")
        self.assertEqual(results_star[0]["match_start_column"], 0)
        self.assertEqual(results_star[0]["match_end_column"], 9)

    def test_search_with_unicode_pattern_and_content(self):
        self._add_file("/unicode.txt", ["\n", " \n", "Hello rsum\n"])
        results_resume = grep_search(search_pattern="rsum")
        self.assertEqual(len(results_resume), 1)
        self.assertEqual(results_resume[0]["line_content"], "Hello rsum")
        self.assertEqual(results_resume[0]["match_start_column"], 6)
        self.assertEqual(results_resume[0]["match_end_column"], 10)

    def test_line_content_stripping(self):
        self._add_file("/newline_test.txt", ["content with newline\n", "content no newline"])  # Second line has no \n

        results1 = grep_search(search_pattern="content with newline")
        self.assertEqual(len(results1), 1)
        self.assertEqual(results1[0]["line_content"], "content with newline")

        results2 = grep_search(search_pattern="content no newline")
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]["line_content"], "content no newline")

    def test_match_at_start_and_end_of_line(self):
        self._add_file("/edges.txt", ["start middle end\n", "start\n", "end\n"])

        results_start = grep_search(search_pattern="start")
        self.assertEqual(len(results_start), 2)

        match_line1_start = next(
            r for r in results_start if r["line_number"] == 1 and r["file_path"] == "/test_ws/edges.txt")
        self.assertEqual(match_line1_start["match_start_column"], 0)
        self.assertEqual(match_line1_start["match_end_column"], 5)

        match_line2_start = next(
            r for r in results_start if r["line_number"] == 2 and r["file_path"] == "/test_ws/edges.txt")
        self.assertEqual(match_line2_start["match_start_column"], 0)
        self.assertEqual(match_line2_start["match_end_column"], 5)

        results_end = grep_search(search_pattern="end")
        self.assertEqual(len(results_end), 2)

        match_line1_end = next(
            r for r in results_end if r["line_number"] == 1 and r["file_path"] == "/test_ws/edges.txt")
        self.assertEqual(match_line1_end["match_start_column"], 13)
        self.assertEqual(match_line1_end["match_end_column"], 16)

        match_line3_end = next(
            r for r in results_end if r["line_number"] == 3 and r["file_path"] == "/test_ws/edges.txt")
        self.assertEqual(match_line3_end["match_start_column"], 0)
        self.assertEqual(match_line3_end["match_end_column"], 3)

    def test_sorting_of_results_within_file(self):
        # Matches from the same file should appear in line number order.
        self._add_file("/sorted_file.txt", [
            "Line 3 has a match.\n",  # This will be line_number 1
            "No match here.\n",  # This will be line_number 2
            "Line 1 has a match.\n"  # This will be line_number 3
        ])

        results = grep_search(search_pattern="match")
        self.assertEqual(len(results), 3)

        # Filter for this specific file and check line numbers
        file_matches = [r for r in results if r["file_path"] == "/test_ws/sorted_file.txt"]
        self.assertEqual(len(file_matches), 3)

        # The first match found will be on original line 1 (content "Line 3 has a match.")
        self.assertEqual(file_matches[0]["line_number"], 1)
        self.assertEqual(file_matches[0]["line_content"], "Line 3 has a match.")

        # The second match found will be on original line 3 (content "Line 1 has a match.")
        self.assertEqual(file_matches[1]["line_number"], 2)
        self.assertEqual(file_matches[1]["line_content"], "No match here.")

    # --- Bug #953 Fix Tests ---
    def test_dangerous_command_line_patterns_raise_invalid_search_pattern_error(self):
        """Test that patterns resembling command-line arguments raise InvalidSearchPatternError."""
        # Set up workspace for the test
        self._add_file("/test_file.txt", ["Hello world\n"])
        
        # Only test the specific patterns mentioned in the bug report
        dangerous_patterns = [
            "-f /etc/passwd",
            "--file=/etc/passwd"
        ]
        
        for pattern in dangerous_patterns:
            with self.subTest(pattern=pattern):
                self.assert_error_behavior(
                    func_to_call=grep_search,
                    search_pattern=pattern,
                    expected_exception_type=custom_errors.InvalidSearchPatternError,
                    expected_message=f"Search pattern contains potentially dangerous characters that resemble command-line arguments: '{pattern}'"
                )


    def test_valid_patterns_work_correctly(self):
        """Test that valid patterns work correctly and don't trigger false positives."""
        self._add_file("/test_file.txt", ["Hello world\n", "This is a test\n"])
        
        # Test various valid patterns that should work
        valid_patterns = [
            "world",
            "test",
            r"\w+",
            r"Hello\s+world",
            "This is a test",
            r"^Hello",
            r"test$",
            r"[a-z]+",
            r"\d+",
            r"Hello|world"
        ]
        
        for pattern in valid_patterns:
            with self.subTest(pattern=pattern):
                try:
                    result = grep_search(pattern)
                    # Should not raise an exception and should return results
                    self.assertIsInstance(result, list)
                except Exception as e:
                    self.fail(f"Valid pattern '{pattern}' raised unexpected exception: {e}")


    def test_invalid_match_positions_are_skipped(self):
        """Test that invalid match positions are handled gracefully."""
        # This test ensures the function handles edge cases in regex matching
        self._add_file("/test_file.txt", ["Hello world\n"])
        
        # This should work normally
        results = grep_search("Hello")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["match_start_column"], 0)
        self.assertEqual(results[0]["match_end_column"], 5)


if __name__ == '__main__':
    unittest.main()
