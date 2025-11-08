import copy
import unittest

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import list_code_usages

class TestListCodeUsages(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB['workspace_root'] = "/test_workspace"
        DB['cwd'] = "/test_workspace"
        DB['file_system'] = {
            "/test_workspace/main.py": {
                "path": "/test_workspace/main.py", "is_directory": False,
                "content_lines": [
                    "def hello():\n",  # Line 1
                    "    print(\"Hello\")\n",  # Line 2
                    "\n",  # Line 3
                    "def my_function(a, b):\n",  # Line 4
                    "    return a + b\n",  # Line 5
                    "\n",  # Line 6
                    "class MyClass:\n",  # Line 7
                    "    def method(self):\n",  # Line 8
                    "        pass\n",  # Line 9
                    "    # End of class\n",  # Line 10
                    "hello()\n",  # Line 11
                    "my_function(1, 2)\n",  # Line 12
                    "x = MyClass()\n",  # Line 13
                    "x.method()\n"  # Line 14
                ],
                "size_bytes": 200, "last_modified": "2023-01-01T10:00:00Z"
            },
            "/test_workspace/utils.py": {
                "path": "/test_workspace/utils.py", "is_directory": False,
                "content_lines": [
                    "from main import my_function\n",  # Line 1
                    "\n",  # Line 2
                    "def utility_call():\n",  # Line 3
                    "    my_function(3,4)\n"  # Line 4
                ],
                "size_bytes": 100, "last_modified": "2023-01-01T10:05:00Z"
            },
            "/test_workspace/empty.py": {
                "path": "/test_workspace/empty.py", "is_directory": False,
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T10:10:00Z"
            },
            "/test_workspace/src": {
                "path": "/test_workspace/src", "is_directory": True,
                "content_lines": [], "size_bytes": 0, "last_modified": "2023-01-01T09:00:00Z"
            },
            "/test_workspace/comment_file.py": {
                "path": "/test_workspace/comment_file.py", "is_directory": False,
                "content_lines": [
                    "# This is a comment\n",  # Line 1
                    "print('hello')\n"  # Line 2
                ],
                "size_bytes": 50, "last_modified": "2023-01-01T10:15:00Z"
            }
        }
        DB['code_symbols_index'] = {
            "/test_workspace/main.py": {
                "1:5": {  # def hello
                    "symbol_name": "hello",
                    "usages": [
                        {"file_path": "/test_workspace/main.py", "start_line": 1, "end_line": 1, "start_column": 5,
                         "end_column": 9, "usage_type": "definition", "snippet": "def hello():"},
                        {"file_path": "/test_workspace/main.py", "start_line": 11, "end_line": 11, "start_column": 1,
                         "end_column": 7, "usage_type": "reference", "snippet": "hello()"}
                    ]
                },
                "4:5": {  # def my_function
                    "symbol_name": "my_function",
                    "usages": [
                        {"file_path": "/test_workspace/main.py", "start_line": 4, "end_line": 4, "start_column": 5,
                         "end_column": 15, "usage_type": "definition", "snippet": "def my_function(a, b):"},
                        {"file_path": "/test_workspace/main.py", "start_line": 12, "end_line": 12, "start_column": 1,
                         "end_column": 15, "usage_type": "reference", "snippet": "my_function(1, 2)"},
                        {"file_path": "/test_workspace/utils.py", "start_line": 1, "end_line": 1, "start_column": 17,
                         "end_column": 27, "usage_type": "import", "snippet": "from main import my_function"},
                        {"file_path": "/test_workspace/utils.py", "start_line": 4, "end_line": 4, "start_column": 5,
                         "end_column": 19, "usage_type": "reference", "snippet": "my_function(3,4)"}
                    ]
                },
                "7:7": {  # class MyClass
                    "symbol_name": "MyClass",
                    "usages": [
                        {"file_path": "/test_workspace/main.py", "start_line": 7, "end_line": 7, "start_column": 7,
                         "end_column": 13, "usage_type": "definition", "snippet": "class MyClass:"},
                        {"file_path": "/test_workspace/main.py", "start_line": 13, "end_line": 13, "start_column": 5,
                         "end_column": 13, "usage_type": "reference", "snippet": "x = MyClass()"}
                    ]
                },
                "8:10": {  # MyClass.method (for null column test)
                    "symbol_name": "method",
                    "usages": [
                        {"file_path": "/test_workspace/main.py", "start_line": 8, "end_line": 8, "start_column": 10,
                         "end_column": 15, "usage_type": "definition", "snippet": "def method(self):"},
                        {"file_path": "/test_workspace/main.py", "start_line": 14, "end_line": 14, "start_column": None,
                         "end_column": None, "usage_type": "reference", "snippet": "x.method()"}
                    ]
                }
            },
            "/test_workspace/utils.py": {
                # Note: This will overwrite if main.py also had entries for utils.py. Let's ensure structure is correct.
                "3:5": {  # def utility_call in utils.py
                    "symbol_name": "utility_call",
                    "usages": []  # No usages for this specific symbol
                }
            }
        }
        DB['code_indexing_status'] = 'complete'

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    # --- Success Cases ---
    def test_list_usages_success_multiple_usages(self):
        file_path = "/test_workspace/main.py"
        line_number = 4
        column_number = 5  # 'my_function'

        expected_usages = DB['code_symbols_index'][file_path][f"{line_number}:{column_number}"]["usages"]

        result = list_code_usages(file_path, line_number, column_number)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(expected_usages))

        # Sort for comparison as order might not be guaranteed
        key_func = lambda x: (
            x['file_path'], x['start_line'], x['start_column'] if x['start_column'] is not None else -1)
        self.assertListEqual(sorted(result, key=key_func), sorted(expected_usages, key=key_func))

    def test_list_usages_success_class_symbol(self):
        file_path = "/test_workspace/main.py"
        line_number = 7
        column_number = 7  # 'MyClass'
        expected_usages = DB['code_symbols_index'][file_path][f"{line_number}:{column_number}"]["usages"]

        result = list_code_usages(file_path, line_number, column_number)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(expected_usages))
        key_func = lambda x: (
            x['file_path'], x['start_line'], x['start_column'] if x['start_column'] is not None else -1)
        self.assertListEqual(sorted(result, key=key_func), sorted(expected_usages, key=key_func))

    def test_list_usages_success_optional_columns_null(self):
        file_path = "/test_workspace/main.py"
        line_number = 8
        column_number = 10  # 'method'
        expected_usages = DB['code_symbols_index'][file_path][f"{line_number}:{column_number}"]["usages"]

        result = list_code_usages(file_path, line_number, column_number)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(expected_usages))

        found_null_column_usage = False
        for usage in result:
            if usage["start_column"] is None and usage["end_column"] is None:
                self.assertEqual(usage["snippet"], "x.method()")
                found_null_column_usage = True
                break
        self.assertTrue(found_null_column_usage, "Expected a usage with null columns was not found.")

    def test_list_usages_success_symbol_with_no_usages_found_in_index(self):
        file_path = "/test_workspace/utils.py"  # utility_call is in utils.py
        line_number = 3
        column_number = 5  # 'utility_call'

        result = list_code_usages(file_path, line_number, column_number)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_list_usages_success_with_relative_path_resolves_correctly(self):
        DB['cwd'] = "/test_workspace"  # Ensure CWD is set for relative path resolution
        relative_file_path = "main.py"
        line_number = 1
        column_number = 5  # 'hello'

        expected_usages = DB['code_symbols_index']["/test_workspace/main.py"][f"{line_number}:{column_number}"][
            "usages"]

        result = list_code_usages(relative_file_path, line_number, column_number)
        self.assertIsInstance(result, list)
        key_func = lambda x: (
            x['file_path'], x['start_line'], x['start_column'] if x['start_column'] is not None else -1)
        self.assertListEqual(sorted(result, key=key_func), sorted(expected_usages, key=key_func))

    # --- Error Cases: InvalidInputError ---
    def test_invalid_input_empty_file_path(self):
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File path cannot be empty.",
            file_path="", line_number=1, column_number=1
        )

    def test_invalid_input_non_existent_file_path(self):
        path = "/test_workspace/non_existent.py"
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"File not found: {path}",
            file_path=path, line_number=1, column_number=1
        )

    def test_invalid_input_file_path_is_directory(self):
        path = "/test_workspace/src"
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Path is a directory, not a file: {path}",
            file_path=path, line_number=1, column_number=1
        )

    def test_invalid_input_line_number_zero(self):
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Line number must be positive.",
            file_path="/test_workspace/main.py", line_number=0, column_number=1
        )

    def test_invalid_input_line_number_negative(self):
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Line number must be positive.",
            file_path="/test_workspace/main.py", line_number=-1, column_number=1
        )

    def test_invalid_input_column_number_zero(self):
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Column number must be positive.",
            file_path="/test_workspace/main.py", line_number=1, column_number=0
        )

    def test_invalid_input_column_number_negative(self):
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Column number must be positive.",
            file_path="/test_workspace/main.py", line_number=1, column_number=-1
        )

    def test_invalid_input_line_number_out_of_bounds_too_high(self):
        file_path = "/test_workspace/main.py"
        num_lines = len(DB['file_system'][file_path]['content_lines'])
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Line number {num_lines + 1} is out of bounds for file {file_path} ({num_lines} lines).",
            file_path=file_path, line_number=num_lines + 1, column_number=1
        )

    def test_invalid_input_column_number_out_of_bounds_too_high(self):
        file_path = "/test_workspace/main.py"
        line_number = 1  # "def hello():\n"
        line_content_len = len(DB['file_system'][file_path]['content_lines'][line_number - 1].rstrip('\n'))
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Column number {line_content_len + 1} is out of bounds for line {line_number} in file {file_path} (length {line_content_len}).",
            file_path=file_path, line_number=line_number, column_number=line_content_len + 1
        )

    def test_invalid_input_line_number_out_of_bounds_for_empty_file(self):
        file_path = "/test_workspace/empty.py"
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Line number 1 is out of bounds for file {file_path} (0 lines).",
            file_path=file_path, line_number=1, column_number=1
        )

    # --- Error Cases: SymbolNotFoundError ---
    def test_symbol_not_found_valid_file_location_not_in_index(self):
        file_path = "/test_workspace/main.py"
        line, col = 2, 5  # 'print' - assume not an indexed symbol for usages
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.SymbolNotFoundError,
            expected_message=f"No symbol found at {file_path}:{line}:{col}.",
            file_path=file_path, line_number=line, column_number=col
        )

    def test_symbol_not_found_location_is_comment(self):
        file_path = "/test_workspace/comment_file.py"
        line, col = 1, 1
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.SymbolNotFoundError,
            expected_message="No symbol data available for file /test_workspace/comment_file.py.",
            file_path=file_path, line_number=line, column_number=col
        )

    def test_symbol_not_found_location_is_whitespace(self):
        file_path = "/test_workspace/main.py"
        line, col = 3, 1  # Empty line
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Column number 1 is out of bounds for line 3 in file /test_workspace/main.py '
                             '(length 0).',
            file_path=file_path, line_number=line, column_number=col
        )

    def test_symbol_not_found_file_path_not_in_symbol_index_altogether(self):
        new_file_path = "/test_workspace/unindexed_file.py"
        DB['file_system'][new_file_path] = {
            "path": new_file_path, "is_directory": False,
            "content_lines": ["print('test')\n"], "size_bytes": 10, "last_modified": "2023-01-01T12:00:00Z"
        }
        # Ensure new_file_path is NOT a key in DB['code_symbols_index']
        if new_file_path in DB['code_symbols_index']:
            del DB['code_symbols_index'][new_file_path]

        line, col = 1, 1
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.SymbolNotFoundError,
            expected_message=f"No symbol data available for file {new_file_path}.",
            file_path=new_file_path, line_number=line, column_number=col
        )

    def test_invalid_input_file_path_not_in_symbol_index_altogether(self):
        new_file_path = "/test_workspace/unindexed_file.py"
        DB['file_system'][new_file_path] = {
            "path": new_file_path, "is_directory": False,
            "content_lines": ["print('test')\n"], "size_bytes": 10, "last_modified": "2023-01-01T12:00:00Z"
        }
        # Ensure new_file_path is NOT a key in DB['code_symbols_index']
        if new_file_path in DB['code_symbols_index']:
            del DB['code_symbols_index'][new_file_path]

        line, col = 1, 1
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.SymbolNotFoundError,
            expected_message=f"No symbol data available for file {new_file_path}.",
            file_path=new_file_path, line_number=line, column_number=col
        )

    def test_invalid_input_file_path_format(self):
        invalid_path = "invalid/path/with/../traversal/../../etc/passwd"
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File not found: /test_workspace/invalid/etc/passwd",
            file_path=invalid_path, line_number=1, column_number=1
        )

    def test_invalid_input_file_with_binary_content(self):
        binary_file_path = "/test_workspace/binary_file.py"
        DB['file_system'][binary_file_path] = {
            "path": binary_file_path, "is_directory": False,
            "content_lines": [],  # Empty list to trigger out of bounds error
            "size_bytes": 100, "last_modified": "2023-01-01T12:00:00Z"
        }
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Line number 1 is out of bounds for file {binary_file_path} (0 lines).",
            file_path=binary_file_path, line_number=1, column_number=1
        )

    def test_invalid_input_file_with_large_content(self):
        large_file_path = "/test_workspace/large_file.py"
        DB['file_system'][large_file_path] = {
            "path": large_file_path, "is_directory": False,
            "content_lines": [],  # Empty list instead of placeholder
            "size_bytes": 1000000, "last_modified": "2023-01-01T12:00:00Z"
        }
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Line number 1 is out of bounds for file {large_file_path} (0 lines).",
            file_path=large_file_path, line_number=1, column_number=1
        )

    def test_invalid_input_file_with_error_content(self):
        error_file_path = "/test_workspace/error_file.py"
        DB['file_system'][error_file_path] = {
            "path": error_file_path, "is_directory": False,
            "content_lines": [],  # Empty list instead of placeholder
            "size_bytes": 100, "last_modified": "2023-01-01T12:00:00Z"
        }
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"Line number 1 is out of bounds for file {error_file_path} (0 lines).",
            file_path=error_file_path, line_number=1, column_number=1
        )

    def test_invalid_input_file_with_invalid_content_format(self):
        invalid_format_file_path = "/test_workspace/invalid_format.py"
        DB['file_system'][invalid_format_file_path] = {
            "path": invalid_format_file_path, "is_directory": False,
            "content_lines": "not a list",  # Should be a list
            "size_bytes": 100, "last_modified": "2023-01-01T12:00:00Z"
        }
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"File content is not in expected format: {invalid_format_file_path}",
            file_path=invalid_format_file_path, line_number=1, column_number=1
        )

    def test_invalid_input_file_with_empty_content_lines(self):
        empty_content_file_path = "/test_workspace/empty_content.py"
        DB['file_system'][empty_content_file_path] = {
            "path": empty_content_file_path, "is_directory": False,
            "content_lines": None,  # Should be a list
            "size_bytes": 0, "last_modified": "2023-01-01T12:00:00Z"
        }
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=f"File content is not in expected format: {empty_content_file_path}",
            file_path=empty_content_file_path, line_number=1, column_number=1
        )

    # --- Error Cases: IndexingNotCompleteError ---
    def test_indexing_not_complete(self):
        DB['code_indexing_status'] = 'incomplete'
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.IndexingNotCompleteError,
            expected_message="Codebase indexing is not yet complete. Please try again later.",
            file_path="/test_workspace/main.py", line_number=1, column_number=1
        )

    def test_invalid_input_file_path_not_string(self):
        # file_path is not a string, triggers ValueError in os.path.join
        # The error message will start with "Invalid file path:"
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="File path cannot be empty.",
            file_path=None, line_number=1, column_number=1
        )

    def test_invalid_input_relative_path_cwd_not_set(self):
        # Remove cwd from DB to simulate missing CWD
        if 'cwd' in DB:
            del DB['cwd']
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message="Current working directory is not configured.",
            file_path="main.py", line_number=1, column_number=5
        )

    def test_symbol_not_found_line_is_comment(self):
        file_path = "/test_workspace/comment_file.py"
        line, col = 1, 2  # On the comment line, valid column
        # Ensure the file is in code_symbols_index but the symbol is not present
        DB['code_symbols_index'][file_path] = {}
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.SymbolNotFoundError,
            expected_message=f"Element at {file_path}:{line}:{col} is not a symbol (e.g., comment or whitespace).",
            file_path=file_path, line_number=line, column_number=col
        )

    def test_symbol_not_found_line_is_whitespace(self):
        file_path = "/test_workspace/main.py"
        line, col = 3, 1  # Line 3 is whitespace, valid column
        # Ensure the file is in code_symbols_index but the symbol is not present
        if file_path not in DB['code_symbols_index']:
            DB['code_symbols_index'][file_path] = {}
        self.assert_error_behavior(
            func_to_call=list_code_usages,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message='Column number 1 is out of bounds for line 3 in file /test_workspace/main.py '
                             '(length 0).',
            file_path=file_path, line_number=line, column_number=col
        )

    def test_list_usages_symbol_entry_without_usages_key(self):
        file_path = "/test_workspace/main.py"
        line_number = 1
        column_number = 5
        # Remove the "usages" key from the symbol entry
        symbol_key = f"{line_number}:{column_number}"
        symbol_data = DB['code_symbols_index'][file_path][symbol_key]
        if "usages" in symbol_data:
            del symbol_data["usages"]
        result = list_code_usages(file_path, line_number, column_number)
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
