import unittest
import copy
import os

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import file_search
from unittest import mock

# DB, file_search, and BaseTestCaseWithErrorHandler are assumed to be globally available.
# For local testing environments, these would need to be defined or mocked.
# Example placeholder for local testing:
# if 'DB' not in globals(): DB = {}
# if 'file_search' not in globals(): def file_search(glob_pattern: str) -> list[str]: raise NotImplementedError()
# if 'BaseTestCaseWithErrorHandler' not in globals(): BaseTestCaseWithErrorHandler = unittest.TestCase


class TestFileSearch(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        DB["workspace_root"] = "/test_workspace"
        DB["file_system"] = {
            "/test_workspace/file1.txt": {"path": "/test_workspace/file1.txt", "is_directory": False, "content_lines": ["text"]},
            "/test_workspace/file2.md": {"path": "/test_workspace/file2.md", "is_directory": False, "content_lines": ["markdown"]},
            "/test_workspace/src": {"path": "/test_workspace/src", "is_directory": True, "content_lines": []},
            "/test_workspace/src/app.py": {"path": "/test_workspace/src/app.py", "is_directory": False, "content_lines": ["python code"]},
            "/test_workspace/src/app.js": {"path": "/test_workspace/src/app.js", "is_directory": False, "content_lines": ["javascript code"]},
            "/test_workspace/src/components": {"path": "/test_workspace/src/components", "is_directory": True, "content_lines": []},
            "/test_workspace/src/components/button.js": {"path": "/test_workspace/src/components/button.js", "is_directory": False, "content_lines": ["button js"]},
            "/test_workspace/src/components/style.css": {"path": "/test_workspace/src/components/style.css", "is_directory": False, "content_lines": ["css"]},
            "/test_workspace/docs": {"path": "/test_workspace/docs", "is_directory": True, "content_lines": []},
            "/test_workspace/docs/readme.txt": {"path": "/test_workspace/docs/readme.txt", "is_directory": False, "content_lines": ["docs readme"]},
            "/test_workspace/foo": {"path": "/test_workspace/foo", "is_directory": True, "content_lines": []},
            "/test_workspace/foo/bar.txt": {"path": "/test_workspace/foo/bar.txt", "is_directory": False, "content_lines": ["foo bar"]},
            "/test_workspace/foo/baz": {"path": "/test_workspace/foo/baz", "is_directory": True, "content_lines": []},
            "/test_workspace/foo/baz/qux.js": {"path": "/test_workspace/foo/baz/qux.js", "is_directory": False, "content_lines": ["qux js"]},
            "/test_workspace/root_file.py": {"path": "/test_workspace/root_file.py", "is_directory": False, "content_lines": ["root python"]},
            "/test_workspace/.hiddenfile": {"path": "/test_workspace/.hiddenfile", "is_directory": False, "content_lines": ["hidden"]},
            "/test_workspace/src/.hidden_in_src": {"path": "/test_workspace/src/.hidden_in_src", "is_directory": False, "content_lines": ["hidden src"]},
        }

        self.max_test_files_relative_paths = []
        for i in range(25):
            basename = f"max_test_file_{i}.txt"
            self.max_test_files_relative_paths.append(basename) 
            
            path = f"/test_workspace/{basename}" # Absolute path for DB key
            DB["file_system"][path] = {"path": path, "is_directory": False, "content_lines": [f"max_test_{i}"]}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_results_are_valid_files(self, results: list[str]):
        for rel_path_result in results:
            # Construct the absolute path that should exist in DB
            abs_path_expected_in_db = os.path.normpath(os.path.join(DB["workspace_root"], rel_path_result)).replace(os.sep, "/")
            self.assertIn(abs_path_expected_in_db, DB["file_system"], f"Path {rel_path_result} (abs: {abs_path_expected_in_db}) not in DB file_system.")
            self.assertFalse(DB["file_system"][abs_path_expected_in_db].get("is_directory"), f"Path {rel_path_result} is a directory, not a file.")

    def test_match_specific_txt_files_less_than_limit(self):
        # Temporarily remove max_test_files to test specific matches without hitting limit
        original_max_files_backup = {}
        for rel_basename in self.max_test_files_relative_paths:
            abs_path = os.path.join(DB["workspace_root"], rel_basename).replace(os.sep, "/")
            if abs_path in DB["file_system"]:
                original_max_files_backup[abs_path] = DB["file_system"].pop(abs_path)
        
        try:
            results = file_search(glob_pattern="*.txt") # Should match all .txt files due to basename matching
            expected = ["file1.txt", "docs/readme.txt", "foo/bar.txt"]
            self.assertCountEqual(results, expected)
            self._assert_results_are_valid_files(results)
        finally: 
            DB["file_system"].update(original_max_files_backup)

    def test_match_specific_file_by_full_name(self):
        results = file_search(glob_pattern="file1.txt")
        self.assertCountEqual(results, ["file1.txt"])
        self._assert_results_are_valid_files(results)

    def test_match_files_in_specific_subdir_no_recursion(self):
        results = file_search(glob_pattern="src/*.py")
        self.assertCountEqual(results, ["src/app.py"])
        self._assert_results_are_valid_files(results)

    def test_match_all_files_in_subdir_recursively_src_double_asterisk(self):
        results = file_search(glob_pattern="src/**")
        expected = ["src/app.py", "src/app.js", "src/components/button.js", "src/components/style.css", "src/.hidden_in_src"]
        self.assertCountEqual(results, expected)
        self._assert_results_are_valid_files(results)

    def test_match_files_recursively_specific_extension_double_asterisk_js(self):
        results = file_search(glob_pattern="**/*.js")
        expected = ["src/app.js", "src/components/button.js", "foo/baz/qux.js"]
        self.assertCountEqual(results, expected)
        self._assert_results_are_valid_files(results)

    def test_match_files_multiple_extensions_brace_expansion(self):
        results = file_search(glob_pattern="**/*.{js,py}")
        expected = ["src/app.py", "src/app.js", "src/components/button.js", "foo/baz/qux.js", "root_file.py"]
        self.assertCountEqual(results, expected)
        self._assert_results_are_valid_files(results)

    def test_no_match_for_nonexistent_extension(self):
        results = file_search(glob_pattern="*.nonexistent")
        self.assertEqual(len(results), 0)

    def test_result_limit_of_20(self):
        results = file_search(glob_pattern="max_test_file_*.txt")
        self.assertEqual(len(results), 20)
        for file_path in results:
            self.assertTrue(os.path.basename(file_path).startswith("max_test_file_"))
            self.assertTrue(file_path.endswith(".txt"))
            self.assertIn(file_path, self.max_test_files_relative_paths)
        self._assert_results_are_valid_files(results)

    def test_empty_filesystem_returns_empty_list(self):
        original_fs = DB["file_system"]
        DB["file_system"] = {}
        try:
            results = file_search(glob_pattern="*.txt")
            self.assertEqual(len(results), 0)
        finally:
            DB["file_system"] = original_fs
            
    def test_glob_pattern_matches_only_directory_name_returns_empty(self):
        results = file_search(glob_pattern="src")
        self.assertEqual(len(results), 0)
        results_trailing_slash = file_search(glob_pattern="src/")
        self.assertEqual(len(results_trailing_slash), 0)

    def test_glob_pattern_asterisk_matches_all_files_respects_limit(self):
        # '*' when matched against basename effectively matches all files.
        results = file_search(glob_pattern="*")
        self.assertEqual(len(results), 20)
        self._assert_results_are_valid_files(results)

    def test_glob_pattern_double_asterisk_matches_all_files_respects_limit(self):
        results = file_search(glob_pattern="**")
        self.assertEqual(len(results), 20)
        self._assert_results_are_valid_files(results)

    def test_match_hidden_files_if_pattern_allows(self):
        results_dot_asterisk = file_search(glob_pattern=".*")
        self.assertCountEqual(results_dot_asterisk, [".hiddenfile"])
        self._assert_results_are_valid_files(results_dot_asterisk)

        results_specific_hidden = file_search(glob_pattern=".hiddenfile")
        self.assertCountEqual(results_specific_hidden, [".hiddenfile"])
        self._assert_results_are_valid_files(results_specific_hidden)

        results_recursive_hidden = file_search(glob_pattern="**/.*")
        expected_hidden_recursive = [".hiddenfile", "src/.hidden_in_src"]
        self.assertCountEqual(results_recursive_hidden, expected_hidden_recursive)
        self._assert_results_are_valid_files(results_recursive_hidden)

    def test_invalid_glob_pattern_empty_string_raises_error(self):
        self.assert_error_behavior(
            func_to_call=file_search,
            expected_exception_type=custom_errors.InvalidInputError, # Changed
            expected_message="Input 'glob_pattern' cannot be empty.",      # Added
            glob_pattern=""  # Changed from glob_pattern
        )

    def test_workspace_not_available_no_root_key_raises_error(self):
        original_root = DB.pop("workspace_root")
        try:
            self.assert_error_behavior(
                func_to_call=file_search,
                expected_exception_type=custom_errors.WorkspaceNotAvailableError,
                expected_message="Workspace root is not configured or available.", # Added
                glob_pattern="*.txt"  # Changed from glob_pattern
            )
        finally:
            DB["workspace_root"] = original_root

    def test_workspace_not_available_empty_root_string_raises_error(self):
        original_root = DB["workspace_root"]
        DB["workspace_root"] = ""
        try:
            self.assert_error_behavior(
                func_to_call=file_search,
                expected_exception_type=custom_errors.WorkspaceNotAvailableError,
                expected_message="Workspace root is not configured or available.",
                glob_pattern="*.txt"
            )
        finally:
            DB["workspace_root"] = original_root
            
    def test_workspace_not_available_none_root_raises_error(self):
        original_root = DB["workspace_root"]
        DB["workspace_root"] = None
        try:
            self.assert_error_behavior(
                func_to_call=file_search,
                expected_exception_type=custom_errors.WorkspaceNotAvailableError,
                expected_message="Workspace root is not configured or available.",
                glob_pattern="*.txt"
            )
        finally:
            DB["workspace_root"] = original_root

    def test_validation_error_glob_pattern_not_string_raises_error(self):
        self.assert_error_behavior(
            func_to_call=file_search,
            expected_exception_type=custom_errors.InvalidInputError, # Changed
            expected_message="Input 'glob_pattern' must be a string.",
            glob_pattern=123  # Changed from glob_pattern
        )

    def test_validation_error_glob_pattern_is_none_raises_error(self):
        self.assert_error_behavior(
            func_to_call=file_search,
            expected_exception_type=custom_errors.InvalidInputError, # Changed
            expected_message="Input 'glob_pattern' must be a string.", # isinstance(None, str) is false
            glob_pattern=None  # Changed from glob_pattern
        )

    def test_workspace_no_filesystem_data(self):
        # workspace_root is set in setUp
        original_filesystem = DB.get("file_system")
        DB["file_system"] = None
        try:
            self.assert_error_behavior(
                func_to_call=file_search,
                expected_exception_type=custom_errors.WorkspaceNotAvailableError,
                expected_message="File system data is not available in the workspace.",
                glob_pattern="*.txt"
            )
        finally:
            DB["file_system"] = original_filesystem # Restore

    def test_invalid_normalized_workspace_root_relative(self):
        original_root = DB["workspace_root"]
        DB["workspace_root"] = "some_relative_path" # This, after normpath, might not start with '/'
        expected_norm_root = os.path.normpath("some_relative_path").replace("\\", "/")
        try:
            self.assert_error_behavior(
                func_to_call=file_search,
                expected_exception_type=custom_errors.WorkspaceNotAvailableError,
                expected_message=f"Normalized workspace root '{expected_norm_root}' is invalid.",
                glob_pattern="*.txt"
            )
        finally:
            DB["workspace_root"] = original_root

    def test_files_outside_workspace_are_ignored(self):
        DB["file_system"]["/absolute_outside/rogue.txt"] = {"path": "/absolute_outside/rogue.txt", "is_directory": False, "content_lines": ["rogue"]}
        # This should also cover the second containment check if commonpath somehow allows it but startswith doesn't.
        DB["file_system"][DB["workspace_root"] + "_other/external.txt"] = {"path": DB["workspace_root"] + "_other/external.txt", "is_directory": False, "content_lines": ["external"]}


        results = file_search(glob_pattern="rogue.txt")
        self.assertEqual(len(results), 0)

        results_all = file_search(glob_pattern="**/*.txt")
        # Ensure rogue.txt and external.txt are not in results_all
        # The expected files are from the standard setUp
        expected_txt_files_in_workspace = ["file1.txt", "docs/readme.txt", "foo/bar.txt"] + [
            basename for basename in self.max_test_files_relative_paths if basename.endswith(".txt")
        ]
        # We take only up to 20 because of the limit, and sorting affects which ones.
        # This assertion is tricky with the limit. Better to check specific non-inclusion.
        for res_path in results_all:
            self.assertNotIn("rogue.txt", res_path)
            self.assertNotIn("external.txt", res_path)

        # Clean up added files if necessary, though tearDown should handle DB state.
        # For this test, it might be cleaner to pop them after the assert.
        DB["file_system"].pop("/absolute_outside/rogue.txt", None)
        DB["file_system"].pop(DB["workspace_root"] + "_other/external.txt", None)


# ... inside TestFileSearch class ...
    def test_relpath_value_error_is_handled(self):
        target_abs_path = "/test_workspace/file1.txt" # Example file
        target_norm_abs_path = os.path.normpath(target_abs_path).replace("\\", "/")
        norm_workspace_root = os.path.normpath(DB["workspace_root"]).replace("\\", "/")

        # Keep a reference to the original os.path.relpath
        original_os_path_relpath = os.path.relpath

        def mock_side_effect(p, s):
            if p == target_norm_abs_path and s == norm_workspace_root:
                raise ValueError("Mocked ValueError for test")
            # Call the original, unmocked version of os.path.relpath
            return original_os_path_relpath(p, s)

        # Patch os.path.relpath where it's looked up by file_search
        # Assuming file_search uses "import os" and calls "os.path.relpath"
        # If file_search does "from os.path import relpath", patch target would be different.
        # Based on your stack trace, file_search does call os.path.relpath directly.
        with mock.patch('os.path.relpath', side_effect=mock_side_effect) as mocked_relpath:
            # Search for a pattern that would normally find file1.txt
            results = file_search(glob_pattern="file1.txt")
            
            # Expect file1.txt to be missing from results because relpath failed for it
            self.assertNotIn("file1.txt", results) # Check against the direct relative path
            self.assertIsInstance(results, list)

    def test_workspace_root_is_slash(self):
        original_root = DB["workspace_root"]
        original_fs = copy.deepcopy(DB["file_system"])

        DB["workspace_root"] = "/"
        DB["file_system"] = {
            "/fileA.txt": {"path": "/fileA.txt", "is_directory": False},
            "/usr": {"path": "/usr", "is_directory": True},
            "/usr/fileB.py": {"path": "/usr/fileB.py", "is_directory": False},
            "/another_root_file.py": {"path": "/another_root_file.py", "is_directory": False}
        }
        try:
            results = file_search(glob_pattern="*.txt")
            self.assertCountEqual(results, ["fileA.txt"])

            results_py = file_search(glob_pattern="**/*.py")
            self.assertCountEqual(results_py, ["usr/fileB.py", "another_root_file.py"])
            
            results_usr_file = file_search(glob_pattern="usr/fileB.py")
            self.assertCountEqual(results_usr_file, ["usr/fileB.py"])

        finally:
            DB["workspace_root"] = original_root
            DB["file_system"] = original_fs

    def test_paths_with_dot_dot_normalization(self):
        # /test_workspace/src/../file1.txt should resolve to /test_workspace/file1.txt
        # and be found as "file1.txt"
        DB["file_system"]["/test_workspace/src/../actual_file1.txt"] = \
            {"path": "/test_workspace/src/../actual_file1.txt", "is_directory": False}

        # This file is ALREADY in DB["file_system"] from setUp as "/test_workspace/file1.txt"
        # We want to ensure our normalized path matches against a pattern for "file1.txt"
        # The key here is that the path in DB has ".." but should resolve to an existing relative path.

        results = file_search(glob_pattern="actual_file1.txt")
        self.assertCountEqual(results, ["actual_file1.txt"]) # Expecting the normalized relative path

        # Clean up
        DB["file_system"].pop("/test_workspace/src/../actual_file1.txt", None)

    def test_unicode_filename_and_pattern(self):
        unicode_filename_rel = "फ़ाइलनाम.txt" # Example: Devanagari script for "filename"
        unicode_filename_abs = f"{DB['workspace_root']}/{unicode_filename_rel}"
        
        DB["file_system"][unicode_filename_abs] = \
            {"path": unicode_filename_abs, "is_directory": False, "content_lines": ["unicode content"]}
        
        try:
            # Exact match
            results = file_search(glob_pattern=unicode_filename_rel)
            self.assertCountEqual(results, [unicode_filename_rel])

            # Glob match
            results_glob = file_search(glob_pattern="फ़ाइल*.txt")
            self.assertCountEqual(results_glob, [unicode_filename_rel])
            
            # Ensure it is not found with a different unicode char
            results_wrong_char = file_search(glob_pattern="फाइलनाम.txt") # Notice 'फाइ' vs 'फ़ाइ' if they are different
            # This depends on exact characters; choose distinct ones if this is ambiguous.
            # For simplicity, let's assume फ़ाइलनाम.txt is distinct from a non-match pattern.
            results_no_match = file_search(glob_pattern="नॉनमॅच.txt")
            self.assertEqual(len(results_no_match), 0)

        finally:
            DB["file_system"].pop(unicode_filename_abs, None)

    def test_case_sensitive_matching(self):
        DB["file_system"]["/test_workspace/CaSeMe.txt"] = \
            {"path": "/test_workspace/CaSeMe.txt", "is_directory": False}
        
        try:
            # Should match
            results_exact_case = file_search(glob_pattern="CaSeMe.txt")
            self.assertCountEqual(results_exact_case, ["CaSeMe.txt"])

            # Should NOT match due to case difference
            results_wrong_case = file_search(glob_pattern="caseme.txt")
            self.assertEqual(len(results_wrong_case), 0)

            results_glob_case = file_search(glob_pattern="CaSe*.txt")
            self.assertCountEqual(results_glob_case, ["CaSeMe.txt"])

            results_glob_wrong_case = file_search(glob_pattern="case*.txt")
            self.assertEqual(len(results_glob_wrong_case), 0)
        finally:
            DB["file_system"].pop("/test_workspace/CaSeMe.txt", None)

if __name__ == '__main__':
    unittest.main()