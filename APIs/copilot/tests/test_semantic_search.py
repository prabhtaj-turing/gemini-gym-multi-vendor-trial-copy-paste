import copy
import unittest

from unittest.mock import patch

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB
from copilot.SimulationEngine.utils import get_mock_timestamp, add_file_to_db, MAX_FILE_SIZE_BYTES
from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import semantic_search

class TestSemanticSearch(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.workspace_root = "/test_ws"
        DB["workspace_root"] = self.workspace_root
        DB["cwd"] = self.workspace_root
        DB["file_system"] = {
            self.workspace_root: {
                "path": self.workspace_root,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": get_mock_timestamp()
            }
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_empty_workspace_returns_empty_list(self):
        results = semantic_search(query="any query")
        self.assertEqual(results, [])

    def test_small_workspace_one_file_returns_full_content(self):
        add_file_to_db(self.workspace_root, "/file1.py", "def hello():\n  return 'world'")
        expected_result = [
            {'file_path': '/test_ws/file1.py', 'snippet': "def hello():\n  return 'world'", 'start_line': 1,
             'end_line': 2, 'relevance_score': None}]
        self.assertListEqual(semantic_search(query="hello"), expected_result)

    def test_small_workspace_multiple_files_returns_full_content(self):
        add_file_to_db(self.workspace_root, "/file1.txt", "content of file1")
        add_file_to_db(self.workspace_root, "/docs/readme.md", "# Title\nSome markdown content.")
        expected_result = [
            {'file_path': '/test_ws/file1.txt', 'snippet': 'content of file1', 'start_line': 1, 'end_line': 1,
             'relevance_score': None},
            {'file_path': '/test_ws/docs/readme.md', 'snippet': '# Title\nSome markdown content.', 'start_line': 1,
             'end_line': 2, 'relevance_score': None}]
        self.assertListEqual(semantic_search(query="content"), expected_result)

    def test_large_workspace_returns_snippets(self):
        add_file_to_db(self.workspace_root, "/src/main.py", "line1\nline2 query_term\nline3\nline4")
        add_file_to_db(self.workspace_root, "/src/utils.py", "other content")
        expected_result = [
            {'file_path': '/test_ws/src/main.py', 'snippet': 'line1\nline2 query_term\nline3\nline4', 'start_line': 1,
             'end_line': 4, 'relevance_score': None},
            {'file_path': '/test_ws/src/utils.py', 'snippet': 'other content', 'start_line': 1, 'end_line': 1,
             'relevance_score': None}]
        self.assertListEqual(semantic_search(query="query_term"), expected_result)

    def test_query_matches_multiple_files_large_workspace(self):
        add_file_to_db(self.workspace_root, "/file1.py", "relevant code here")
        add_file_to_db(self.workspace_root, "/file2.txt", "more relevant text")
        add_file_to_db(self.workspace_root, "/other.py", "unrelated")
        expected_result = [
            {'file_path': '/test_ws/file1.py', 'snippet': 'relevant code here', 'start_line': 1, 'end_line': 1,
             'relevance_score': None},
            {'file_path': '/test_ws/file2.txt', 'snippet': 'more relevant text', 'start_line': 1, 'end_line': 1,
             'relevance_score': None},
            {'file_path': '/test_ws/other.py', 'snippet': 'unrelated', 'start_line': 1, 'end_line': 1,
             'relevance_score': None}]
        self.assertListEqual(semantic_search(query="relevant"), expected_result)

    def test_query_no_match_returns_empty_list(self):
        add_file_to_db(self.workspace_root, "/file1.py", "some python code")
        results = semantic_search(query="non_existent_term")
        expected_result = [
            {'file_path': '/test_ws/file1.py', 'snippet': 'some python code', 'start_line': 1, 'end_line': 1,
             'relevance_score': None}]
        self.assertEqual(results, expected_result)

    def test_ignored_files_not_searched_small_workspace(self):
        add_file_to_db(self.workspace_root, "/.git/config", "core.editor=vim")
        add_file_to_db(self.workspace_root, "/app.pyc", "compiled_python_bytes")
        add_file_to_db(self.workspace_root, "/main.py", "actual_content")
        expected_result = [
            {'file_path': '/test_ws/main.py', 'snippet': 'actual_content', 'start_line': 1, 'end_line': 1,
             'relevance_score': None}]
        self.assertListEqual(semantic_search(query="actual_content"), expected_result)

    def test_ignored_files_not_searched_large_workspace(self):
        add_file_to_db(self.workspace_root, "/.git/config", "core.editor=vim relevant_term")
        add_file_to_db(self.workspace_root, "/src/main.py", "actual_content with relevant_term")
        add_file_to_db(self.workspace_root, "/src/utils.py", "other stuff to make it large")
        expected_result = [
            {'file_path': '/test_ws/src/main.py', 'snippet': 'actual_content with relevant_term', 'start_line': 1,
             'end_line': 1, 'relevance_score': None},
            {'file_path': '/test_ws/src/utils.py', 'snippet': 'other stuff to make it large', 'start_line': 1,
             'end_line': 1, 'relevance_score': None}]
        self.assertListEqual(semantic_search(query="relevant_term"), expected_result)

    def test_result_structure_and_line_numbers(self):
        add_file_to_db(self.workspace_root, "/file.txt", "line one\nline two has target\nline three")
        add_file_to_db(self.workspace_root, "/another.txt", "make it large")
        expected_result = [
            {'file_path': '/test_ws/file.txt', 'snippet': 'line one\nline two has target\nline three', 'start_line': 1,
             'end_line': 3, 'relevance_score': None},
            {'file_path': '/test_ws/another.txt', 'snippet': 'make it large', 'start_line': 1, 'end_line': 1,
             'relevance_score': None}]
        self.assertListEqual(semantic_search(query="target"), expected_result)

    # --- Error Cases ---
    def test_workspace_not_available_error_if_no_root(self):
        DB.pop("workspace_root", None)
        self.assert_error_behavior(
            semantic_search,
            query="any_query",
            expected_exception_type=custom_errors.WorkspaceNotAvailableError,
            expected_message="Workspace root is not configured. Workspace may not be initialized."
        )

    def test_workspace_not_available_error_if_no_filesystem(self):
        DB.pop("file_system", None)
        self.assert_error_behavior(
            semantic_search,
            query="any_query",
            expected_exception_type=custom_errors.WorkspaceNotAvailableError,
            expected_message="Workspace file system is not available or empty. Workspace may not be indexed."
        )

    def test_workspace_not_available_error_if_filesystem_is_not_dict(self):
        DB["file_system"] = []
        self.assert_error_behavior(
            semantic_search,
            query="any_query",
            expected_exception_type=custom_errors.WorkspaceNotAvailableError,
            expected_message="Workspace file system is not available or empty. Workspace may not be indexed."
        )

    def test_validation_error_for_invalid_query_type_int(self):
        self.assert_error_behavior(
            semantic_search,
            query=123,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query must be a non-empty string."
        )

    def test_validation_error_for_invalid_query_type_none(self):
        self.assert_error_behavior(
            semantic_search,
            query=None,  # Invalid type
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query must be a non-empty string."
        )

    def test_validation_error_for_empty_query_string(self):
        self.assert_error_behavior(
            semantic_search,
            query="",
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query must be a non-empty string."
        )

    def test_file_with_non_absolute_path_is_skipped(self):
        DB["file_system"]["relative.py"] = {
            "path": "relative.py",
            "is_directory": False,
            "content_lines": ["print('hi')"],
            "size_bytes": 12,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="hi")
        self.assertEqual(results, [])

    def test_file_outside_workspace_root_is_skipped(self):
        DB["file_system"]["/other_ws/file.py"] = {
            "path": "/other_ws/file.py",
            "is_directory": False,
            "content_lines": ["print('hi')"],
            "size_bytes": 12,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="hi")
        self.assertEqual(results, [])

    def test_file_with_valueerror_in_relpath_is_skipped(self):
        # Simulate ValueError by making path and root on different drives (Windows style)
        DB["file_system"]["D:\\file.py"] = {
            "path": "D:\\file.py",
            "is_directory": False,
            "content_lines": ["print('hi')"],
            "size_bytes": 12,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="hi")
        self.assertEqual(results, [])

    def test_file_with_binary_content_placeholder_is_skipped(self):
        from copilot.SimulationEngine import utils as se_utils
        DB["file_system"]["/test_ws/file.bin"] = {
            "path": "/test_ws/file.bin",
            "is_directory": False,
            "content_lines": se_utils.BINARY_CONTENT_PLACEHOLDER,
            "size_bytes": 12,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    def test_file_with_large_file_content_placeholder_is_skipped(self):
        from copilot.SimulationEngine import utils as se_utils
        DB["file_system"]["/test_ws/large.txt"] = {
            "path": "/test_ws/large.txt",
            "is_directory": False,
            "content_lines": se_utils.LARGE_FILE_CONTENT_PLACEHOLDER,
            "size_bytes": 12,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    def test_file_with_error_reading_content_placeholder_is_skipped(self):
        from copilot.SimulationEngine import utils as se_utils
        DB["file_system"]["/test_ws/error.txt"] = {
            "path": "/test_ws/error.txt",
            "is_directory": False,
            "content_lines": se_utils.ERROR_READING_CONTENT_PLACEHOLDER,
            "size_bytes": 12,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    def test_file_with_content_lines_none_is_treated_as_empty(self):
        DB["file_system"]["/test_ws/empty.txt"] = {
            "path": "/test_ws/empty.txt",
            "is_directory": False,
            "content_lines": None,
            "size_bytes": 0,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    def test_file_with_missing_size_bytes_uses_calculate_size_bytes(self):
        DB["file_system"]["/test_ws/file.txt"] = {
            "path": "/test_ws/file.txt",
            "is_directory": False,
            "content_lines": ["abc", "def"],
            # size_bytes missing
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="abc")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["snippet"], "abcdef")

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_returns_not_relevant(self, mock_call_llm):
        # Force large workspace
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": 1000000,
            "last_modified": get_mock_timestamp()
        }
        mock_call_llm.return_value = "NOT_RELEVANT"
        results = semantic_search(query="something")
        expected_result = [{'end_line': 2,
                            'file_path': '/test_ws/file1.txt',
                            'relevance_score': None,
                            'snippet': 'line1line2',
                            'start_line': 1}]
        self.assertEqual(results, expected_result)

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_returns_relevant_with_invalid_score(self, mock_call_llm):
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": 1000000,
            "last_modified": get_mock_timestamp()
        }
        mock_call_llm.return_value = "RELEVANT: 1,2,1.5"  # Invalid score (>1.0)
        results = semantic_search(query="something")
        expected_result = [
            {'end_line': 2,
             'file_path': '/test_ws/file1.txt',
             'relevance_score': None,
             'snippet': 'line1line2',
             'start_line': 1
             }
        ]
        self.assertEqual(results, expected_result)

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_returns_relevant_with_invalid_line_numbers(self, mock_call_llm):
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": 1000000,
            "last_modified": get_mock_timestamp()
        }
        mock_call_llm.return_value = "RELEVANT: 0,2,0.9"  # Invalid start_line (<=0)
        results = semantic_search(query="something")
        expected_result = [{'end_line': 2,
                            'file_path': '/test_ws/file1.txt',
                            'relevance_score': None,
                            'snippet': 'line1line2',
                            'start_line': 1}]
        self.assertEqual(results, expected_result)

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_returns_unexpected_format(self, mock_call_llm):
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": 1000000,
            "last_modified": get_mock_timestamp()
        }
        mock_call_llm.return_value = "SOMETHING ELSE"
        results = semantic_search(query="something")
        expected_result = [
            {'end_line': 2,
             'file_path': '/test_ws/file1.txt',
             'relevance_score': None,
             'snippet': 'line1line2',
             'start_line': 1
             }
        ]
        self.assertEqual(results, expected_result)

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_raises_runtime_error(self, mock_call_llm):
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": 1000000,
            "last_modified": get_mock_timestamp()
        }
        mock_call_llm.side_effect = RuntimeError("LLM failed")
        results = semantic_search(query="something")
        expected_result = [{'end_line': 2,
                            'file_path': '/test_ws/file1.txt',
                            'relevance_score': None,
                            'snippet': 'line1line2',
                            'start_line': 1}]
        self.assertEqual(results, expected_result)

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_raises_other_exception(self, mock_call_llm):
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }
        mock_call_llm.side_effect = Exception("Unexpected error")
        with self.assertRaises(custom_errors.SearchFailedError):
            semantic_search(query="something")

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_truncates_content(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_LLM_CONTENT_CHARS_PER_FILE
        long_content = ["a" * (MAX_LLM_CONTENT_CHARS_PER_FILE + 10)]
        DB["file_system"]["/test_ws/long.txt"] = {
            "path": "/test_ws/long.txt",
            "is_directory": False,
            "content_lines": long_content,
            "size_bytes": 1000000,
            "last_modified": get_mock_timestamp()
        }
        # Return a valid relevant response
        mock_call_llm.return_value = "RELEVANT: 1,1,0.9"
        results = semantic_search(query="a")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["file_path"], "/test_ws/long.txt")

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_results_are_sorted_by_relevance_score(self, mock_call_llm):
        # Add two files, both relevant, but different scores
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": 1000000,
            "last_modified": get_mock_timestamp()
        }
        DB["file_system"]["/test_ws/file2.txt"] = {
            "path": "/test_ws/file2.txt",
            "is_directory": False,
            "content_lines": ["lineA", "lineB"],
            "size_bytes": 1000000,
            "last_modified": get_mock_timestamp()
        }

        # Return different scores for each file
        def side_effect(prompt, **kwargs):
            if "file1.txt" in prompt:
                return "RELEVANT: 1,2,0.5"
            else:
                return "RELEVANT: 1,2,0.9"

        mock_call_llm.side_effect = side_effect
        results = semantic_search(query="line")
        self.assertEqual(results[0]["file_path"], "/test_ws/file1.txt")
        self.assertEqual(results[1]["file_path"], "/test_ws/file2.txt")

    def test_directory_entry_is_skipped(self):
        DB["file_system"]["/test_ws/dir"] = {
            "path": "/test_ws/dir",
            "is_directory": True,
            "content_lines": ["should not matter"],
            "size_bytes": 10,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_skips_file_with_only_whitespace(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_FILE_SIZE_BYTES
        DB["file_system"]["/test_ws/white.txt"] = {
            "path": "/test_ws/white.txt",
            "is_directory": False,
            "content_lines": ["   \n", "\t\n"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }
        # LLM should not be called at all, but if it is, return NOT_RELEVANT
        mock_call_llm.return_value = "NOT_RELEVANT"
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_returns_start_line_gt_max_lines(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_FILE_SIZE_BYTES
        DB["file_system"]["/test_ws/file.txt"] = {
            "path": "/test_ws/file.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }
        mock_call_llm.return_value = "RELEVANT: 5,6,0.9"  # start_line > max_lines
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_returns_end_line_lt_start_line(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_FILE_SIZE_BYTES
        DB["file_system"]["/test_ws/file.txt"] = {
            "path": "/test_ws/file.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }
        mock_call_llm.return_value = "RELEVANT: 2,1,0.9"  # end_line < start_line
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_returns_start_line_gt_end_line_after_adjustment(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_FILE_SIZE_BYTES
        DB["file_system"]["/test_ws/file.txt"] = {
            "path": "/test_ws/file.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }
        # start_line is valid, end_line is too large, will be adjusted to 2, but start_line > end_line after adjustment
        mock_call_llm.return_value = "RELEVANT: 3,10,0.9"
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_max_files_to_process_limit(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_FILES_TO_PROCESS_WITH_LLM_LARGE_WORKSPACE, MAX_FILE_SIZE_BYTES
        for i in range(MAX_FILES_TO_PROCESS_WITH_LLM_LARGE_WORKSPACE + 2):
            DB["file_system"][f"/test_ws/file{i}.txt"] = {
                "path": f"/test_ws/file{i}.txt",
                "is_directory": False,
                "content_lines": [f"line{i}"],
                "size_bytes": MAX_FILE_SIZE_BYTES + 1,
                "last_modified": get_mock_timestamp()
            }
        mock_call_llm.return_value = "RELEVANT: 1,1,0.9"
        results = semantic_search(query="line")
        self.assertEqual(len(results), MAX_FILES_TO_PROCESS_WITH_LLM_LARGE_WORKSPACE)

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_some_files_raise_exception_some_valid(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_FILE_SIZE_BYTES
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }
        DB["file_system"]["/test_ws/file2.txt"] = {
            "path": "/test_ws/file2.txt",
            "is_directory": False,
            "content_lines": ["lineA", "lineB"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }

        def side_effect(prompt, **kwargs):
            if "file1.txt" in prompt:
                raise RuntimeError("fail")
            else:
                return "RELEVANT: 1,2,0.9"

        mock_call_llm.side_effect = side_effect
        results = semantic_search(query="line")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["file_path"], "/test_ws/file2.txt")

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_multiple_files_some_valid_some_skipped(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_FILE_SIZE_BYTES
        DB["file_system"]["/test_ws/file1.txt"] = {
            "path": "/test_ws/file1.txt",
            "is_directory": False,
            "content_lines": ["line1", "line2"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }
        DB["file_system"]["/test_ws/file2.txt"] = {
            "path": "/test_ws/file2.txt",
            "is_directory": False,
            "content_lines": ["lineA", "lineB"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }
        DB["file_system"]["/test_ws/file3.txt"] = {
            "path": "/test_ws/file3.txt",
            "is_directory": False,
            "content_lines": ["lineX", "lineY"],
            "size_bytes": MAX_FILE_SIZE_BYTES + 1,
            "last_modified": get_mock_timestamp()
        }

        def side_effect(prompt, **kwargs):
            if "file1.txt" in prompt:
                return "RELEVANT: 1,2,0.8"
            elif "file2.txt" in prompt:
                return "NOT_RELEVANT"
            else:
                raise RuntimeError("fail")

        mock_call_llm.side_effect = side_effect
        results = semantic_search(query="line")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["file_path"], "/test_ws/file1.txt")

    def test_file_with_empty_content_lines_is_skipped(self):
        DB["file_system"]["/test_ws/empty.txt"] = {
            "path": "/test_ws/empty.txt",
            "is_directory": False,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="anything")
        self.assertEqual(results, [])

    def test_file_with_content_lines_all_empty_strings_is_skipped(self):
        DB["file_system"]["/test_ws/empty.txt"] = {
            "path": "/test_ws/empty.txt",
            "is_directory": False,
            "content_lines": ["", ""],
            "size_bytes": 0,
            "last_modified": get_mock_timestamp()
        }
        results = semantic_search(query="anything")
        expected_result = [{'end_line': 2,
                            'file_path': '/test_ws/empty.txt',
                            'relevance_score': None,
                            'snippet': '',
                            'start_line': 1}]
        self.assertEqual(results, expected_result)

    @patch("copilot.SimulationEngine.utils.call_llm")
    def test_llm_all_files_not_relevant(self, mock_call_llm):
        from copilot.SimulationEngine.utils import MAX_FILE_SIZE_BYTES
        for i in range(3):
            DB["file_system"][f"/test_ws/file{i}.txt"] = {
                "path": f"/test_ws/file{i}.txt",
                "is_directory": False,
                "content_lines": [f"line{i}"],
                "size_bytes": MAX_FILE_SIZE_BYTES + 1,
                "last_modified": get_mock_timestamp()
            }
        mock_call_llm.return_value = "NOT_RELEVANT"
        results = semantic_search(query="line")
        self.assertEqual(results, [])

    def test_sorting_with_none_relevance_score(self):
        # Simulate small workspace, so relevance_score is None
        add_file_to_db(self.workspace_root, "/file1.txt", "content1")
        add_file_to_db(self.workspace_root, "/file2.txt", "content2")
        results = semantic_search(query="content")
        # Should not error, and both results should be present
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r["relevance_score"] is None for r in results))


if __name__ == '__main__':
    unittest.main()
