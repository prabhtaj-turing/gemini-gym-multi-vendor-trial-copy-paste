import copy
import unittest

from common_utils.base_case import BaseTestCaseWithErrorHandler
from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB

from .. import list_dir
from unittest.mock import patch

class TestListDir(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB["workspace_root"] = "/test_workspace"
        DB["cwd"] = "/test_workspace" # Default CWD
        DB["file_system"] = {
            # Workspace root entry
            "/test_workspace": {
                "path": "/test_workspace", "is_directory": True, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:00:00Z"
            },
            # Files in root
            "/test_workspace/file1.txt": {
                "path": "/test_workspace/file1.txt", "is_directory": False, 
                "content_lines": ["content"], "size_bytes": 7, "last_modified": "2023-01-01T00:01:00Z"
            },
            "/test_workspace/another_file.log": {
                "path": "/test_workspace/another_file.log", "is_directory": False, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:02:00Z"
            },
            # Subdirectory 1
            "/test_workspace/subdir1": {
                "path": "/test_workspace/subdir1", "is_directory": True, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:03:00Z"
            },
            "/test_workspace/subdir1/file2.txt": {
                "path": "/test_workspace/subdir1/file2.txt", "is_directory": False, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:04:00Z"
            },
            "/test_workspace/subdir1/nested_dir": { # Empty nested directory
                "path": "/test_workspace/subdir1/nested_dir", "is_directory": True, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:05:00Z"
            },
            # Empty subdirectory in root
            "/test_workspace/empty_subdir": {
                "path": "/test_workspace/empty_subdir", "is_directory": True, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:06:00Z"
            },
            # Subdirectory 2 (for .. tests)
            "/test_workspace/subdir2": {
                "path": "/test_workspace/subdir2", "is_directory": True, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:07:00Z"
            },
            "/test_workspace/subdir2/file3.txt": {
                "path": "/test_workspace/subdir2/file3.txt", "is_directory": False, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:08:00Z"
            },
            # Directory for testing files_only
            "/test_workspace/files_only_dir": {
                "path": "/test_workspace/files_only_dir", "is_directory": True,
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:09:00Z"
            },
            "/test_workspace/files_only_dir/f1.txt": {
                "path": "/test_workspace/files_only_dir/f1.txt", "is_directory": False,
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:10:00Z"
            },
            "/test_workspace/files_only_dir/f2.dat": {
                "path": "/test_workspace/files_only_dir/f2.dat", "is_directory": False,
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:11:00Z"
            },
            # Directory for testing dirs_only
            "/test_workspace/dirs_only_dir": {
                "path": "/test_workspace/dirs_only_dir", "is_directory": True,
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:12:00Z"
            },
            "/test_workspace/dirs_only_dir/sub1": {
                "path": "/test_workspace/dirs_only_dir/sub1", "is_directory": True,
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:13:00Z"
            },
            "/test_workspace/dirs_only_dir/sub2_folder": { # Name with underscore
                "path": "/test_workspace/dirs_only_dir/sub2_folder", "is_directory": True,
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:14:00Z"
            },
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def assert_dir_listing_equal(self, actual_listing, expected_listing):
        self.assertIsInstance(actual_listing, list, "Listing should be a list.")
        self.assertEqual(len(actual_listing), len(expected_listing), 
                         f"Number of items mismatch. Got {len(actual_listing)}, expected {len(expected_listing)}."
                         f"\nActual: {actual_listing}\nExpected: {expected_listing}")
        
        actual_sorted = sorted(actual_listing, key=lambda x: x['path'])
        expected_sorted = sorted(expected_listing, key=lambda x: x['path'])

        for i in range(len(actual_sorted)):
            actual_item = actual_sorted[i]
            expected_item = expected_sorted[i]
            self.assertIsInstance(actual_item, dict, f"Actual item at index {i} is not a dict: {actual_item}")
            self.assertIsInstance(expected_item, dict, f"Expected item at index {i} is not a dict: {expected_item}")
            
            # Check all required keys are present
            self.assertIn('name', actual_item, f"Key 'name' missing in actual item: {actual_item}")
            self.assertIn('type', actual_item, f"Key 'type' missing in actual item: {actual_item}")
            self.assertIn('path', actual_item, f"Key 'path' missing in actual item: {actual_item}")

            self.assertEqual(actual_item.get('name'), expected_item.get('name'), f"Item 'name' mismatch at index {i}")
            self.assertEqual(actual_item.get('type'), expected_item.get('type'), f"Item 'type' mismatch at index {i}")
            self.assertEqual(actual_item.get('path'), expected_item.get('path'), f"Item 'path' mismatch at index {i}")
            # Check for unexpected keys
            self.assertEqual(len(actual_item.keys()), 3, f"Actual item has unexpected keys: {actual_item}")


    # --- Success Cases ---
    def test_list_empty_directory(self):
        result = list_dir("empty_subdir") # Relative to /test_workspace
        self.assert_dir_listing_equal(result, [])

    def test_list_directory_with_files_only(self):
        result = list_dir("files_only_dir")
        expected = [
            {"name": "f1.txt", "type": "file", "path": "/test_workspace/files_only_dir/f1.txt"},
            {"name": "f2.dat", "type": "file", "path": "/test_workspace/files_only_dir/f2.dat"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_directory_with_subdirectories_only(self):
        result = list_dir("dirs_only_dir")
        expected = [
            {"name": "sub1/", "type": "directory", "path": "/test_workspace/dirs_only_dir/sub1"},
            {"name": "sub2_folder/", "type": "directory", "path": "/test_workspace/dirs_only_dir/sub2_folder"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_directory_with_mixed_content_root_via_dot(self):
        DB["cwd"] = "/test_workspace"
        result = list_dir(".") 
        expected = [
            {"name": "file1.txt", "type": "file", "path": "/test_workspace/file1.txt"},
            {"name": "another_file.log", "type": "file", "path": "/test_workspace/another_file.log"},
            {"name": "subdir1/", "type": "directory", "path": "/test_workspace/subdir1"},
            {"name": "empty_subdir/", "type": "directory", "path": "/test_workspace/empty_subdir"},
            {"name": "subdir2/", "type": "directory", "path": "/test_workspace/subdir2"},
            {"name": "files_only_dir/", "type": "directory", "path": "/test_workspace/files_only_dir"},
            {"name": "dirs_only_dir/", "type": "directory", "path": "/test_workspace/dirs_only_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_subdirectory_mixed_content(self):
        result = list_dir("subdir1") # Relative to /test_workspace
        expected = [
            {"name": "file2.txt", "type": "file", "path": "/test_workspace/subdir1/file2.txt"},
            {"name": "nested_dir/", "type": "directory", "path": "/test_workspace/subdir1/nested_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)
        
    def test_list_deeply_nested_empty_directory(self):
        result = list_dir("subdir1/nested_dir") # This dir is empty
        self.assert_dir_listing_equal(result, [])

    def test_list_absolute_path(self):
        result = list_dir("/test_workspace/subdir1")
        expected = [
            {"name": "file2.txt", "type": "file", "path": "/test_workspace/subdir1/file2.txt"},
            {"name": "nested_dir/", "type": "directory", "path": "/test_workspace/subdir1/nested_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_relative_path_dot_slash_prefix(self):
        DB["cwd"] = "/test_workspace"
        result = list_dir("./subdir1")
        expected = [
            {"name": "file2.txt", "type": "file", "path": "/test_workspace/subdir1/file2.txt"},
            {"name": "nested_dir/", "type": "directory", "path": "/test_workspace/subdir1/nested_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_relative_path_double_dot(self):
        DB["cwd"] = "/test_workspace/subdir1/nested_dir"
        result = list_dir("..") 
        expected = [
            {"name": "file2.txt", "type": "file", "path": "/test_workspace/subdir1/file2.txt"},
            {"name": "nested_dir/", "type": "directory", "path": "/test_workspace/subdir1/nested_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_relative_path_multiple_double_dots(self):
        DB["cwd"] = "/test_workspace/subdir1/nested_dir"
        result = list_dir("../../") 
        expected = [
            {"name": "file1.txt", "type": "file", "path": "/test_workspace/file1.txt"},
            {"name": "another_file.log", "type": "file", "path": "/test_workspace/another_file.log"},
            {"name": "subdir1/", "type": "directory", "path": "/test_workspace/subdir1"},
            {"name": "empty_subdir/", "type": "directory", "path": "/test_workspace/empty_subdir"},
            {"name": "subdir2/", "type": "directory", "path": "/test_workspace/subdir2"},
            {"name": "files_only_dir/", "type": "directory", "path": "/test_workspace/files_only_dir"},
            {"name": "dirs_only_dir/", "type": "directory", "path": "/test_workspace/dirs_only_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_path_with_trailing_slash(self):
        result = list_dir("subdir1/")
        expected = [
            {"name": "file2.txt", "type": "file", "path": "/test_workspace/subdir1/file2.txt"},
            {"name": "nested_dir/", "type": "directory", "path": "/test_workspace/subdir1/nested_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_path_with_multiple_internal_slashes_normalized(self):
        result = list_dir("/test_workspace///subdir1//")
        expected = [
            {"name": "file2.txt", "type": "file", "path": "/test_workspace/subdir1/file2.txt"},
            {"name": "nested_dir/", "type": "directory", "path": "/test_workspace/subdir1/nested_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)
        
    def test_list_path_empty_string_resolves_to_cwd(self):
        DB["cwd"] = "/test_workspace/subdir1"
        result = list_dir("") 
        expected = [
            {"name": "file2.txt", "type": "file", "path": "/test_workspace/subdir1/file2.txt"},
            {"name": "nested_dir/", "type": "directory", "path": "/test_workspace/subdir1/nested_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)

    def test_list_root_directory_when_workspace_is_actual_root(self):
        original_ws_root = DB["workspace_root"]
        original_cwd = DB["cwd"]
        original_fs = copy.deepcopy(DB["file_system"])

        DB["workspace_root"] = "/"
        DB["cwd"] = "/"
        DB["file_system"] = {
            "/": {"path": "/", "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:00:00Z"},
            "/root_file.txt": {"path": "/root_file.txt", "is_directory": False, "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:01:00Z"},
            "/root_dir": {"path": "/root_dir", "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:02:00Z"},
            "/root_dir/sub_file.sh": {"path": "/root_dir/sub_file.sh", "is_directory": False, "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T00:03:00Z"}, # Not a direct child of /
        }
        
        try:
            result = list_dir("/")
            expected = [
                {"name": "root_file.txt", "type": "file", "path": "/root_file.txt"},
                {"name": "root_dir/", "type": "directory", "path": "/root_dir"},
            ]
            self.assert_dir_listing_equal(result, expected)
        finally:
            DB["workspace_root"] = original_ws_root
            DB["cwd"] = original_cwd
            DB["file_system"] = original_fs


    # --- DirectoryNotFoundError Cases ---
    def test_path_does_not_exist_raises_dirnotfound(self):
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="non_existent_dir",
            expected_exception_type=custom_errors.DirectoryNotFoundError,
            expected_message="Directory '/test_workspace/non_existent_dir' not found or is not a directory."
        )

    def test_path_is_file_raises_dirnotfound(self):
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="file1.txt",
            expected_exception_type=custom_errors.DirectoryNotFoundError,
            expected_message="Path 'file1.txt' (resolved to '/test_workspace/file1.txt') is not a directory."
        )

    def test_path_relative_resolves_to_non_existent_raises_dirnotfound(self):
        DB["cwd"] = "/test_workspace/subdir1"
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="non_existent_sub",
            expected_exception_type=custom_errors.DirectoryNotFoundError,
            expected_message="Directory '/test_workspace/subdir1/non_existent_sub' not found or is not a directory."
        )

    def test_path_outside_workspace_absolute_raises_invalid_input(self):
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="/outside_workspace/some_dir",
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Absolute path '/outside_workspace/some_dir' is outside the configured workspace root '/test_workspace'."
        )

    def test_path_outside_workspace_relative_dot_dot_raises_dirnotfound(self):
        DB["cwd"] = "/test_workspace" 
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="../another_project", 
            expected_exception_type=custom_errors.DirectoryNotFoundError,
            # Path traversal is now blocked early with improved security, but list_dir converts ValueError to DirectoryNotFoundError
            expected_message="Invalid path '../another_project': Path '../another_project' resolves to '/another_project' which is outside the workspace root '/test_workspace'."
        )
        
    def test_path_resolves_to_file_via_empty_string_and_cwd_is_file_raises_dirnotfound(self):
        DB["cwd"] = "/test_workspace/file1.txt"
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="", 
            expected_exception_type=custom_errors.DirectoryNotFoundError,
            expected_message="Path '' (resolved to '/test_workspace/file1.txt') is not a directory."
        )


    # --- ValidationError Cases ---
    def test_path_is_none_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_dir,
            path=None,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input path must be a string." 
        )

    def test_path_is_int_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_dir,
            path=123,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input path must be a string."
        )

    def test_path_is_list_raises_validation_error(self):
        self.assert_error_behavior(
            func_to_call=list_dir,
            path=[],
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input path must be a string."
        )

    def test_list_dir_path_is_dictionary(self):
        """Test list_dir with a dictionary as path."""
        self.assert_error_behavior(
            func_to_call=list_dir,
            path={},
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input path must be a string." # Based on your list_dir code
        )

    def test_list_dir_path_is_boolean(self):
        """Test list_dir with a boolean as path."""
        self.assert_error_behavior(
            func_to_call=list_dir,
            path=True,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Input path must be a string." # Based on your list_dir code
        )

    def test_list_dir_workspace_root_not_configured(self):
        """Test list_dir when workspace_root is not configured in DB."""
        original_db_state = copy.deepcopy(DB)
        DB.pop("workspace_root", None) # Remove workspace_root
        DB.pop("cwd", None) # Also remove cwd as it might fallback to workspace_root

        try:
            self.assert_error_behavior(
                func_to_call=list_dir,
                path="any_valid_path_string",
                expected_exception_type=custom_errors.DirectoryNotFoundError,
                expected_message="Cannot list directory: Workspace root is not configured."
            )
        finally:
            DB.clear()
            DB.update(original_db_state) # Restore original DB state

    def test_list_dir_absolute_input_path_outside_workspace(self):
        """Test list_dir with an absolute input path that is outside the workspace."""
        # Assumes workspace_root is "/test_workspace" from the main setUp
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="/completely_other_root/some_dir",
            expected_exception_type=custom_errors.InvalidInputError,
            # This message comes from utils.get_absolute_path via ValueError
            expected_message="Absolute path '/completely_other_root/some_dir' is outside the configured workspace root '/test_workspace'."
        )

    @patch('copilot.SimulationEngine.utils.get_absolute_path')
    def test_list_dir_generic_value_error_from_get_absolute_path(self, mock_get_absolute_path):
        """Test list_dir when utils.get_absolute_path raises a generic ValueError."""
        mock_get_absolute_path.side_effect = ValueError("A very generic and unexpected ValueError")
        
        input_path = "some_test_path"
        self.assert_error_behavior(
            func_to_call=list_dir,
            path=input_path,
            expected_exception_type=custom_errors.DirectoryNotFoundError,
            expected_message=f"Invalid path 'some_test_path': A very generic and unexpected ValueError"
        )

    def test_list_dir_relative_path_resolves_outside_workspace_unmodified_utils(self):
        """
        Test list_dir with a relative path resolving outside workspace.
        With improved path traversal protection, the path is now blocked early
        in get_absolute_path before it can resolve outside the workspace.
        """
        DB["cwd"] = "/test_workspace" # Default CWD for this test
        
        # This path, from /test_workspace, resolves to /another_project
        path_input_relative = "../another_project"
        resolved_abs_path = "/another_project" # How it resolves initially

        self.assert_error_behavior(
            func_to_call=list_dir,
            path=path_input_relative,
            expected_exception_type=custom_errors.DirectoryNotFoundError,
            # Path traversal is now blocked early with improved security, but list_dir converts ValueError to DirectoryNotFoundError
            expected_message=f"Invalid path '{path_input_relative}': Path '{path_input_relative}' resolves to '{resolved_abs_path}' which is outside the workspace root '/test_workspace'."
        )

    def test_list_dir_empty_path_when_cwd_is_file(self):
        """Test list_dir with an empty path when CWD is set to a file path."""
        original_cwd = DB.get("cwd")
        DB["cwd"] = "/test_workspace/file1.txt" # Set CWD to an existing file

        try:
            self.assert_error_behavior(
                func_to_call=list_dir,
                path="", # Empty path, should resolve to CWD
                expected_exception_type=custom_errors.DirectoryNotFoundError,
                # Message from `if not utils.is_directory(abs_path):`
                expected_message="Path '' (resolved to '/test_workspace/file1.txt') is not a directory."
            )
        finally:
            DB["cwd"] = original_cwd # Restore CWD

    def test_list_dir_with_special_character_names(self):
        """Test listing directories and files with spaces or special characters in their names."""
        original_fs_state = copy.deepcopy(DB["file_system"])
        
        # Add items with special names
        DB["file_system"]["/test_workspace/dir with spaces"] = {
            "path": "/test_workspace/dir with spaces", "is_directory": True, "last_modified": "2023-01-01T12:00:00Z"
        }
        DB["file_system"]["/test_workspace/dir with spaces/file name with spaces.txt"] = {
            "path": "/test_workspace/dir with spaces/file name with spaces.txt", "is_directory": False, "last_modified": "2023-01-01T12:01:00Z"
        }
        DB["file_system"]["/test_workspace/@dir_special!"] = { # Directory
            "path": "/test_workspace/@dir_special!", "is_directory": True, "last_modified": "2023-01-01T12:02:00Z"
        }
        DB["file_system"]["/test_workspace/@dir_special!/file_#.log"] = { # File in it
            "path": "/test_workspace/@dir_special!/file_#.log", "is_directory": False, "last_modified": "2023-01-01T12:03:00Z"
        }

        try:
            # Test 1: Listing directory with spaces in its name
            result1 = list_dir("/test_workspace/dir with spaces")
            expected1 = [
                {"name": "file name with spaces.txt", "type": "file", "path": "/test_workspace/dir with spaces/file name with spaces.txt"},
            ]
            self.assert_dir_listing_equal(result1, expected1)

            # Test 2: Listing directory whose name contains special characters
            result2 = list_dir("/test_workspace/@dir_special!")
            expected2 = [
                {"name": "file_#.log", "type": "file", "path": "/test_workspace/@dir_special!/file_#.log"},
            ]
            self.assert_dir_listing_equal(result2, expected2)

            # Test 3: Ensure these special-named directories appear correctly when listing their parent
            DB["cwd"] = "/test_workspace"
            root_listing = list_dir(".") # List /test_workspace
            
            found_dir_with_spaces = any(
                item["name"] == "dir with spaces/" and \
                item["type"] == "directory" and \
                item["path"] == "/test_workspace/dir with spaces"
                for item in root_listing
            )
            found_dir_special_chars = any(
                item["name"] == "@dir_special!/" and \
                item["type"] == "directory" and \
                item["path"] == "/test_workspace/@dir_special!"
                for item in root_listing
            )

            self.assertTrue(found_dir_with_spaces, "Directory 'dir with spaces/' not found or incorrect in root listing.")
            self.assertTrue(found_dir_special_chars, "Directory '@dir_special!/' not found or incorrect in root listing.")

        finally:
            DB["file_system"] = original_fs_state # Restore original file system

    def test_list_dir_workspace_root_directly_as_absolute_path(self):
        """Test listing the workspace root using its full absolute path."""
        original_cwd = DB.get("cwd")
        DB["cwd"] = "/test_workspace/subdir1" 
        
        try:
            result = list_dir("/test_workspace") # Use the absolute path to workspace root
            # Expected content should match what's directly under /test_workspace
            # This list is based on the original setUp data in the user's test file.
            expected = [
                {"name": "another_file.log", "type": "file", "path": "/test_workspace/another_file.log"},
                {"name": "dirs_only_dir/", "type": "directory", "path": "/test_workspace/dirs_only_dir"},
                {"name": "empty_subdir/", "type": "directory", "path": "/test_workspace/empty_subdir"},
                {"name": "file1.txt", "type": "file", "path": "/test_workspace/file1.txt"},
                {"name": "files_only_dir/", "type": "directory", "path": "/test_workspace/files_only_dir"},
                {"name": "subdir1/", "type": "directory", "path": "/test_workspace/subdir1"},
                {"name": "subdir2/", "type": "directory", "path": "/test_workspace/subdir2"},
            ]
            self.assert_dir_listing_equal(result, expected)
        finally:
            if original_cwd is not None:
                DB["cwd"] = original_cwd
            else: # Should not happen if setUp defines it
                DB.pop("cwd", None)

    # --- Bug #954 Fix Tests ---
    def test_list_dir_path_with_null_bytes_raises_invalid_input(self):
        """Test list_dir with path containing null bytes raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="test\x00file",
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Path contains null bytes, which are not allowed."
        )

    def test_list_dir_excessive_path_traversal_raises_invalid_input(self):
        """Test list_dir with excessive path traversal attempts raises InvalidInputError."""
        self.assert_error_behavior(
            func_to_call=list_dir,
            path="../../../etc/passwd",
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Path traversal attempt detected. Access denied."
        )

    def test_list_dir_reasonable_dot_dot_usage_allowed(self):
        """Test list_dir with reasonable use of .. is allowed."""
        DB["cwd"] = "/test_workspace/subdir1/nested_dir"
        result = list_dir("../..")  # Should be allowed (only 2 ..)
        expected = [
            {"name": "file1.txt", "type": "file", "path": "/test_workspace/file1.txt"},
            {"name": "another_file.log", "type": "file", "path": "/test_workspace/another_file.log"},
            {"name": "subdir1/", "type": "directory", "path": "/test_workspace/subdir1"},
            {"name": "empty_subdir/", "type": "directory", "path": "/test_workspace/empty_subdir"},
            {"name": "subdir2/", "type": "directory", "path": "/test_workspace/subdir2"},
            {"name": "files_only_dir/", "type": "directory", "path": "/test_workspace/files_only_dir"},
            {"name": "dirs_only_dir/", "type": "directory", "path": "/test_workspace/dirs_only_dir"},
        ]
        self.assert_dir_listing_equal(result, expected)

# Standard unittest runner
if __name__ == '__main__':
    unittest.main()