import unittest
import copy
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# CRITICAL IMPORT FOR CUSTOM ERRORS
from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import read_file

class TestReadFile(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB['workspace_root'] = "/test_ws"
        DB['cwd'] = "/test_ws"
        DB['file_system'] = {}

        # Populate DB with test files
        self._add_file_to_db("small.txt", ["L1\n", "L2\n", "L3\n"])
        
        medium_outline = [
            {'name': 'section1', 'kind': 'comment', 'start_line': 1, 'end_line': 5},
            {'name': 'section2', 'kind': 'comment', 'start_line': 6, 'end_line': 10}
        ]
        self._add_file_to_db("medium.txt", [f"Line {i+1}\n" for i in range(10)], outline=medium_outline)
        
        self._add_file_to_db("empty.txt", [])
        
        structured_content_lines = [
            "# Comment line 1\n",        # Line 1
            "def func_one():  # Line 2\n", # Line 2
            "    print(\"func1\") # Line 3\n", # Line 3
            "# Comment line 4\n",        # Line 4
            "class MyClassExample: # Line 5\n", # Line 5
            "    def method_A(self): # Line 6\n", # Line 6
            "        return True     # Line 7\n", # Line 7
            "\n",                        # Line 8
            "# Final line 9\n"           # Line 9
        ]
        structured_outline = [
            {'name': 'func_one', 'kind': 'function', 'start_line': 2, 'end_line': 3},
            {'name': 'MyClassExample', 'kind': 'class', 'start_line': 5, 'end_line': 7},
            {'name': 'MyClassExample.method_A', 'kind': 'method', 'start_line': 6, 'end_line': 7}
        ]
        self._add_file_to_db("structured.py", structured_content_lines, outline=structured_outline)
        
        self._add_file_to_db("perm_denied.txt", ["Error: Permission denied to read file content.\n"])
        self._add_file_to_db("no_trail_newline.txt", ["Line one\n", "Line two"])
        self._add_file_to_db("one_liner.txt", ["This is the only line.\n"])
        self._add_file_to_db("five_liner.txt", [f"5L Line {i+1}\n" for i in range(5)])


        self._add_dir_to_db("subdir")
        self._add_file_to_db("subdir/nested.txt", ["Nested content line 1\n"])
        
        # For testing malformed DB entry
        malformed_path_key = self._get_expected_abs_path("malformed.txt")
        DB['file_system'][malformed_path_key] = {
            "path": malformed_path_key,
            "is_directory": False,
            "content_lines": "This should be a list, not a string", # Malformed
            "size_bytes": 0,
            "last_modified": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }


    def _get_expected_abs_path(self, relative_or_absolute_path: str) -> str:
        # (Keep your existing _get_expected_abs_path helper method here)
        workspace_root = DB.get('workspace_root') # Ensure workspace_root can be None
        if not workspace_root and not os.path.isabs(relative_or_absolute_path):
             # This case will likely cause an error in a real get_absolute_path if it strictly needs workspace_root for relatives
             # For test expectation, we might need to simulate this or assume a default if utils.get_absolute_path handles it.
             # Given the test for "workspace root not configured", utils.get_absolute_path should handle it by raising ValueError.
             pass

        if not workspace_root: # If workspace_root is None for the test
            if os.path.isabs(relative_or_absolute_path):
                return os.path.normpath(relative_or_absolute_path).replace("\\","/")
            else:
                # This situation is tricky for a helper, as relative paths need a root.
                # The actual error will come from utils.get_absolute_path.
                # For setting up DB keys when workspace_root is None, we might skip adding relative paths.
                # However, this helper is mainly for *expected* paths, and if workspace_root is None,
                # calls to read_file with relative paths should fail appropriately.
                return os.path.normpath(os.path.join("/", relative_or_absolute_path)).replace("\\", "/") # Fallback for expectation


        normalized_given_path = os.path.normpath(relative_or_absolute_path).replace("\\", "/")
        normalized_workspace_root = os.path.normpath(workspace_root).replace("\\", "/")

        if os.path.isabs(normalized_given_path) and normalized_given_path.startswith(normalized_workspace_root):
            return normalized_given_path
        
        if relative_or_absolute_path.startswith("/"):
             return os.path.normpath(os.path.join(normalized_workspace_root, relative_or_absolute_path.lstrip('/'))).replace("\\", "/")

        cwd = DB.get('cwd', normalized_workspace_root)
        return os.path.normpath(os.path.join(cwd, relative_or_absolute_path)).replace("\\", "/")


    def _add_file_to_db(self, path_arg_for_function: str, content_lines_list: list[str], 
                        last_modified: str = None, outline: Optional[List[Dict[str, Any]]] = None):
        # (Keep your existing _add_file_to_db helper method here)
        abs_path_key = self._get_expected_abs_path(path_arg_for_function)
        
        parent_dir = os.path.dirname(abs_path_key)
        # Simplified parent check for test setup
        if parent_dir and parent_dir != abs_path_key and parent_dir not in DB['file_system'] and DB.get('workspace_root') and parent_dir != DB['workspace_root']:
            pass # Assume explicit dir creation for tests or simple structures

        content_str = "".join(content_lines_list)
        file_entry = {
            "path": abs_path_key,
            "is_directory": False,
            "content_lines": content_lines_list,
            "size_bytes": len(content_str.encode('utf-8')),
            "last_modified": last_modified or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        if outline is not None:
            file_entry["outline"] = outline
        DB['file_system'][abs_path_key] = file_entry
        return abs_path_key

    def _add_dir_to_db(self, path_arg_for_function: str, last_modified: str = None):
        # (Keep your existing _add_dir_to_db helper method here)
        abs_path_key = self._get_expected_abs_path(path_arg_for_function)
        DB['file_system'][abs_path_key] = {
            "path": abs_path_key,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": last_modified or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        return abs_path_key

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    # --- Success Scenarios ---
    def test_read_full_file_small(self):
        file_path_arg = "small.txt"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=3)
        result = result_wrapper['file_details']
        
        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "L1\nL2\nL3\n")
        self.assertEqual(result['start_line'], 1)
        self.assertEqual(result['end_line'], 3)
        self.assertEqual(result['total_lines'], 3)
        self.assertFalse(result['is_truncated_at_top'])
        self.assertFalse(result['is_truncated_at_bottom'])
        self.assertIsNone(result['outline']) # small.txt was added without outline

    def test_read_partial_file_start(self):
        file_path_arg = "medium.txt" 
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=3)
        result = result_wrapper['file_details']
        
        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "Line 1\nLine 2\nLine 3\n")
        self.assertEqual(result['start_line'], 1)
        self.assertEqual(result['end_line'], 3)
        self.assertEqual(result['total_lines'], 10)
        self.assertFalse(result['is_truncated_at_top'])
        self.assertTrue(result['is_truncated_at_bottom'])
        self.assertIsNotNone(result['outline']) 

    def test_read_partial_file_middle(self):
        file_path_arg = "medium.txt"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        result_wrapper = read_file(file_path=file_path_arg, start_line=4, end_line=6)
        result = result_wrapper['file_details']

        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "Line 4\nLine 5\nLine 6\n")
        self.assertEqual(result['start_line'], 4)
        self.assertEqual(result['end_line'], 6)
        self.assertEqual(result['total_lines'], 10)
        self.assertTrue(result['is_truncated_at_top'])
        self.assertTrue(result['is_truncated_at_bottom'])
        self.assertIsNotNone(result['outline'])

    def test_read_partial_file_end(self):
        file_path_arg = "medium.txt"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        result_wrapper = read_file(file_path=file_path_arg, start_line=8, end_line=10)
        result = result_wrapper['file_details']

        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "Line 8\nLine 9\nLine 10\n")
        self.assertEqual(result['start_line'], 8)
        self.assertEqual(result['end_line'], 10)
        self.assertEqual(result['total_lines'], 10)
        self.assertTrue(result['is_truncated_at_top'])
        self.assertFalse(result['is_truncated_at_bottom'])
        self.assertIsNotNone(result['outline'])

    def test_read_single_line(self):
        file_path_arg = "medium.txt"
        result_wrapper = read_file(file_path=file_path_arg, start_line=5, end_line=5)
        result = result_wrapper['file_details']
        self.assertEqual(result['content'], "Line 5\n")
        self.assertEqual(result['start_line'], 5)
        self.assertEqual(result['end_line'], 5)
        self.assertTrue(result['is_truncated_at_top'])
        self.assertTrue(result['is_truncated_at_bottom'])

    def test_read_empty_file(self):
        file_path_arg = "empty.txt"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=1)
        result = result_wrapper['file_details']

        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "")
        self.assertEqual(result['start_line'], 1) 
        self.assertEqual(result['end_line'], 0)   
        self.assertEqual(result['total_lines'], 0)
        self.assertFalse(result['is_truncated_at_top'])
        self.assertFalse(result['is_truncated_at_bottom'])
        self.assertIsNone(result['outline']) # empty.txt has no outline

    def test_read_lines_beyond_eof_clamps_end_line(self):
        file_path_arg = "medium.txt" 
        result_wrapper = read_file(file_path=file_path_arg, start_line=8, end_line=15)
        result = result_wrapper['file_details']
        self.assertEqual(result['content'], "Line 8\nLine 9\nLine 10\n")
        self.assertEqual(result['end_line'], 10) 
        self.assertFalse(result['is_truncated_at_bottom']) 
        self.assertIsNotNone(result['outline'])

    def test_read_file_with_relative_path_from_subdir_cwd(self):
        DB['cwd'] = self._get_expected_abs_path("subdir") 
        file_path_arg = "nested.txt" 
        expected_abs_path = self._get_expected_abs_path(file_path_arg) 
        
        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=1)
        result = result_wrapper['file_details']
        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "Nested content line 1\n")

    def test_read_file_with_dot_dot_path(self):
        DB['cwd'] = self._get_expected_abs_path("subdir") 
        file_path_arg = "../small.txt" 
        expected_abs_path = self._get_expected_abs_path(file_path_arg)

        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=1)
        result = result_wrapper['file_details']
        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "L1\n")

    def test_read_file_with_absolute_path_input(self):
        file_path_arg = self._get_expected_abs_path("small.txt")
        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=1)
        result = result_wrapper['file_details']
        self.assertEqual(result['file_path'], file_path_arg)
        self.assertEqual(result['content'], "L1\n")
        
    def test_read_file_with_outline_partial_read_structured_file(self):
        file_path_arg = "structured.py"
        # expected_abs_path = self._get_expected_abs_path(file_path_arg) # Not used below
        result_wrapper = read_file(file_path=file_path_arg, start_line=2, end_line=7) # Extended end_line to get MyClassExample fully
        result = result_wrapper['file_details']

        expected_content = (
            "def func_one():  # Line 2\n"
            "    print(\"func1\") # Line 3\n"
            "# Comment line 4\n"
            "class MyClassExample: # Line 5\n"
            "    def method_A(self): # Line 6\n"
            "        return True     # Line 7\n"
        )
        self.assertEqual(result['content'], expected_content)
        self.assertIsNotNone(result['outline'])
        self.assertIsInstance(result['outline'], list)
        
        # Check if the setup outline items are present
        # (The exact content of outline can be complex, so check for known items)
        setup_outline = DB['file_system'][self._get_expected_abs_path("structured.py")]['outline']
        for item in setup_outline:
             self.assertIn(item, result['outline'])


    def test_read_file_full_range_structured_file_has_outline(self):
        result_wrapper = read_file(file_path="structured.py", start_line=1, end_line=9)
        result = result_wrapper['file_details']
        # For this implementation, outline is passed through if it exists in DB,
        # regardless of full/partial read, unless it's explicitly None for non-large files.
        # Since we added an outline for structured.py, it should be present.
        self.assertFalse(result['is_truncated_at_top'])
        self.assertFalse(result['is_truncated_at_bottom'])
        self.assertIsNotNone(result['outline'])
             
    def test_read_file_content_last_line_no_trailing_newline(self):
        file_path_arg = "no_trail_newline.txt"
        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=2)
        result = result_wrapper['file_details']
        self.assertEqual(result['content'], "Line one\nLine two") # read_file joins lines, content_lines preserve original ending
        self.assertEqual(result['total_lines'], 2)

        result_wrapper_line2 = read_file(file_path=file_path_arg, start_line=2, end_line=2)
        result_line2 = result_wrapper_line2['file_details']
        self.assertEqual(result_line2['content'], "Line two")


    # --- Error Scenarios ---
    # For assert_error_behavior, I'm adding expected_message.
    # Your BaseTestCaseWithErrorHandler needs to be adapted to use it,
    # for example, by checking if the actual error message matches this regex.
    def test_read_file_not_found(self):
        file_path_arg="non_existent_file.txt"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message=f"File not found at resolved path: {expected_abs_path} (from input: non_existent_file.txt)",
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_file_path_outside_workspace(self):
        file_path_arg = "/other_workspace/file.txt"
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError, 
            expected_message=f"Invalid file path: {file_path_arg}. Original error: Absolute path '/other_workspace/file.txt' is outside the configured workspace root '/test_ws'.", # Matches error from get_absolute_path
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_file_path_traversal_attack_simple(self):
        """Test path traversal protection with simple ../ attack."""
        file_path_arg = "../../../etc/passwd"
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message=f"Invalid file path: {file_path_arg}. Original error: Path '{file_path_arg}' resolves to '/etc/passwd' which is outside the workspace root '/test_ws'.",
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_file_path_traversal_attack_windows_style(self):
        """Test path traversal protection with Windows-style ..\\ attack."""
        # Note: Windows-style backslashes are normalized but may not be blocked as expected
        file_path_arg = "..\\..\\..\\windows\\system32\\config\\sam"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message=f"File not found at resolved path: {expected_abs_path} (from input: {file_path_arg})",
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_file_path_traversal_attack_url_encoded(self):
        """Test path traversal protection with URL-encoded ../ attack."""
        # Note: URL-encoded paths are treated as literal strings, not decoded
        # So this creates a file path within the workspace, not a traversal attack
        file_path_arg = "..%2f..%2f..%2fetc%2fpasswd"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message=f"File not found at resolved path: {expected_abs_path} (from input: {file_path_arg})",
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_file_path_traversal_attack_double_encoded(self):
        """Test path traversal protection with double URL-encoded ../ attack."""
        # Note: URL-encoded paths are treated as literal strings, not decoded
        file_path_arg = "..%252f..%252f..%252fetc%252fpasswd"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message=f"File not found at resolved path: {expected_abs_path} (from input: {file_path_arg})",
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_file_path_traversal_attack_mixed_encoding(self):
        """Test path traversal protection with mixed encoding attack."""
        # Note: URL-encoded paths are treated as literal strings, not decoded
        file_path_arg = "..%2f..\\..%5cetc%2fpasswd"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message=f"File not found at resolved path: {expected_abs_path} (from input: {file_path_arg})",
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_file_path_traversal_attack_from_subdirectory(self):
        """Test path traversal protection when CWD is in a subdirectory."""
        # Set CWD to a subdirectory
        DB["cwd"] = "/test_ws/subdir"
        file_path_arg = "../../../etc/passwd"
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message=f"Invalid file path: {file_path_arg}. Original error: Path '{file_path_arg}' resolves to '/etc/passwd' which is outside the workspace root '/test_ws'.",
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_file_path_traversal_attack_legitimate_relative_path(self):
        """Test that legitimate relative paths within workspace still work."""
        # This should work - it's a legitimate relative path within the workspace
        file_path_arg = "small.txt"  # This file exists in our test setup
        result = read_file(file_path=file_path_arg, start_line=1, end_line=1)
        self.assertIsNotNone(result)
        self.assertIn("file_details", result)
        self.assertIn("content", result["file_details"])

    def test_read_file_is_directory(self):
        dir_path_arg = "subdir"
        expected_abs_path = self._get_expected_abs_path(dir_path_arg)
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError, # As per read_file logic
            expected_message=f"Specified path is a directory, not a file: {expected_abs_path}",
            file_path=dir_path_arg, start_line=1, end_line=1
        )

    def test_read_file_permission_denied(self):
        file_path_arg = "perm_denied.txt"
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.PermissionDeniedError, # Corrected NameError
            expected_message=f"Permission denied to read file: {file_path_arg}",
            file_path=file_path_arg, start_line=1, end_line=1
        )

    def test_read_invalid_range_start_greater_than_end(self):
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidLineRangeError,
            expected_message="Start line (5) cannot be greater than end line (3).",
            file_path="small.txt", start_line=5, end_line=3
        )

    def test_read_invalid_input_start_line_zero(self): # Changed expected exception
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Start line must be a positive integer, got 0.",
            file_path="small.txt", start_line=0, end_line=5
        )

    def test_read_invalid_input_end_line_zero(self): # Changed expected exception
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="End line must be a positive integer, got 0.",
            file_path="small.txt", start_line=1, end_line=0
        )

    def test_read_invalid_input_start_line_negative(self): # Changed expected exception
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidInputError, 
            expected_message="Start line must be a positive integer, got -1.",
            file_path="small.txt", start_line=-1, end_line=5
        )

    def test_read_invalid_range_start_line_out_of_bounds_positive(self):
        file_path_arg = "small.txt" # 3 lines
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidLineRangeError,
            expected_message=f"Start line (5) is beyond the total number of lines (3) in file: {file_path_arg}.",
            file_path=file_path_arg, start_line=5, end_line=6 
        )

    def test_read_invalid_range_start_line_out_of_bounds_for_empty_file(self):
        file_path_arg = "empty.txt" # 0 lines
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidLineRangeError,
            # Message from updated read_file for start_line > 1 on empty file
            expected_message=f"Start line (2) is beyond the total number of lines (0) in file: {file_path_arg}.",
            file_path=file_path_arg, start_line=2, end_line=2
        )
        
    def test_read_invalid_input_file_path_type(self):
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File path must be a non-empty string.",
            file_path=123, start_line=1, end_line=1
        )

    def test_read_invalid_input_start_line_type(self):
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Start line must be a positive integer, got abc.",
            file_path="small.txt", start_line="abc", end_line=1
        )

    def test_read_invalid_input_end_line_type(self):
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="End line must be a positive integer, got None.",
            file_path="small.txt", start_line=1, end_line=None
        )

    def test_read_only_last_line(self):
        file_path_arg = "five_liner.txt"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        result_wrapper = read_file(file_path=file_path_arg, start_line=5, end_line=5)
        result = result_wrapper['file_details']

        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "5L Line 5\n")
        self.assertEqual(result['start_line'], 5)
        self.assertEqual(result['end_line'], 5)
        self.assertEqual(result['total_lines'], 5)
        self.assertTrue(result['is_truncated_at_top'])
        self.assertFalse(result['is_truncated_at_bottom'])
        self.assertIsNone(result['outline']) # Assuming no outline added for five_liner

    def test_read_one_line_file_full(self):
        file_path_arg = "one_liner.txt"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=1)
        result = result_wrapper['file_details']

        self.assertEqual(result['file_path'], expected_abs_path)
        self.assertEqual(result['content'], "This is the only line.\n")
        self.assertEqual(result['start_line'], 1)
        self.assertEqual(result['end_line'], 1)
        self.assertEqual(result['total_lines'], 1)
        self.assertFalse(result['is_truncated_at_top'])
        self.assertFalse(result['is_truncated_at_bottom'])
        self.assertIsNone(result['outline'])

    def test_read_one_line_file_clamped_end(self):
        file_path_arg = "one_liner.txt"
        result_wrapper = read_file(file_path=file_path_arg, start_line=1, end_line=10) # end_line beyond total
        result = result_wrapper['file_details']

        self.assertEqual(result['content'], "This is the only line.\n")
        self.assertEqual(result['start_line'], 1)
        self.assertEqual(result['end_line'], 1) # Clamped
        self.assertEqual(result['total_lines'], 1)
        self.assertFalse(result['is_truncated_at_bottom'])

    def test_read_invalid_input_empty_file_path(self):
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File path must be a non-empty string.",
            file_path="", start_line=1, end_line=1
        )

    def test_read_file_malformed_db_entry_content_lines(self):
        file_path_arg = "malformed.txt"
        expected_abs_path = self._get_expected_abs_path(file_path_arg)
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=RuntimeError,
            expected_message=f"File entry for {expected_abs_path} is malformed: 'content_lines' is not a list.",
            file_path=file_path_arg, start_line=1, end_line=1
        )
        
    def test_read_file_workspace_root_not_configured(self):
        original_ws_root = DB.pop('workspace_root', None) # Remove workspace_root
        file_path_arg = "small.txt" # Using a relative path that would need workspace_root

        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message=f"Invalid file path: {file_path_arg}. Original error: Workspace root is not configured. Check application settings.",
            file_path=file_path_arg, start_line=1, end_line=1
        )
        
        if original_ws_root is not None: # Restore for other tests
             DB['workspace_root'] = original_ws_root
        else: # If it truly wasn't there, ensure it's gone for consistency if another test expects it missing
             if 'workspace_root' in DB: del DB['workspace_root']

if __name__ == '__main__':
    unittest.main()