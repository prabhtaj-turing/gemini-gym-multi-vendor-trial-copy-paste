import unittest
import copy
import os

from unittest.mock import patch, MagicMock

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB
from copilot.SimulationEngine import utils 
from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import insert_edit_into_file

class TestStripCodeFences(unittest.TestCase):
    def test_strip_standard_fences_with_lang(self):
        text = "```python\nprint('Hello')\n```"
        self.assertEqual(utils.strip_code_fences_from_llm(text), "print('Hello')")

    def test_strip_standard_fences_no_lang(self):
        text = "```\nprint('Hello')\n```"
        self.assertEqual(utils.strip_code_fences_from_llm(text), "print('Hello')")

    def test_strip_fences_with_leading_trailing_whitespace(self):
        text = "  ```python  \nprint('Hello')\n  ```  "
        self.assertEqual(utils.strip_code_fences_from_llm(text), "print('Hello')")

    def test_strip_fences_no_newline_inside_content(self):
        text = "```print('Hello')```" 
        self.assertEqual(utils.strip_code_fences_from_llm(text), "print('Hello')") # Was failing, assuming utils.strip_code_fences_from_llm is now fixed for this

    def test_no_fences_returns_original_stripped(self):
        text = "  print('Hello')  "
        self.assertEqual(utils.strip_code_fences_from_llm(text), "print('Hello')")

    def test_empty_string(self):
        self.assertEqual(utils.strip_code_fences_from_llm(""), "")

    def test_string_with_only_fences_and_lang_hint(self):
        self.assertEqual(utils.strip_code_fences_from_llm("```\n```"), "")
        self.assertEqual(utils.strip_code_fences_from_llm("```python\n```"), "", 
                         "Failed for '```python\\n```'")
        self.assertEqual(utils.strip_code_fences_from_llm("```python```"), "",
                         "Failed for '```python```'")

    def test_fences_with_only_whitespace_inside(self):
        text = "```python\n   \n```"
        self.assertEqual(utils.strip_code_fences_from_llm(text), "")


class TestInsertEditIntoFileLLM(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.workspace_root = "/test_ws_llm_final" # Changed name slightly
        DB["workspace_root"] = self.workspace_root
        DB["cwd"] = self.workspace_root
        DB["file_system"] = {
            f"{self.workspace_root}/original_file.py": {
                "path": f"{self.workspace_root}/original_file.py", "is_directory": False,
                "content_lines": ["def greet():\n", "    print('Hello Original')\n"],
                "size_bytes": 40, "last_modified": "2024-01-01T00:00:00Z", "is_readonly": False
            },
            f"{self.workspace_root}/empty_for_llm.txt": {
                "path": f"{self.workspace_root}/empty_for_llm.txt", "is_directory": False, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2024-01-01T00:00:00Z", "is_readonly": False
            },
            f"{self.workspace_root}/readonly_llm.txt": {
                "path": f"{self.workspace_root}/readonly_llm.txt", "is_directory": False, 
                "content_lines": ["Read me."], "size_bytes": 8, "last_modified": "2024-01-01T00:00:00Z", "is_readonly": True
            },
            f"{self.workspace_root}/llm_subdir": {
                "path": f"{self.workspace_root}/llm_subdir", "is_directory": True, 
                "content_lines": [], "size_bytes": 0, "last_modified": "2024-01-01T00:00:00Z", "is_readonly": False
            },
            f"{self.workspace_root}/uneditable_placeholder.bin": {
                "path": f"{self.workspace_root}/uneditable_placeholder.bin", "is_directory": False, 
                "content_lines": utils.BINARY_CONTENT_PLACEHOLDER, "size_bytes": 0, 
                "last_modified": "2024-01-01T00:00:00Z", "is_readonly": False
            }
        }
        DB["background_processes"] = {}
        DB["_next_pid"] = 1
        
        # Assuming 'copilot' is a package in python path (e.g. src dir for 'copilot' package is in PYTHONPATH)
        self.mock_call_llm_target = 'copilot.file_system.call_llm'
        self.mock_get_absolute_path_target = 'copilot.file_system.utils.get_absolute_path'


    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _get_abs_path(self, relative_path: str) -> str:
        return f"{self.workspace_root}/{relative_path}"

    # --- Input Validation Tests (expecting status returns) ---
    # (These remain the same as the previously corrected version)
    def test_validation_empty_file_path_returns_status(self):
        result = insert_edit_into_file("", "edit", "explain")
        self.assertEqual(result["status"], "failed_to_apply")
        self.assertEqual(result["file_path"], "")
        self.assertIn("Input Validation Error: file_path must be a non-empty string.", result["message"])

    def test_validation_none_file_path_returns_status(self):
        result = insert_edit_into_file(None, "edit", "explain")
        self.assertEqual(result["status"], "failed_to_apply")
        self.assertEqual(result["file_path"], "None") 
        self.assertIn("Input Validation Error: file_path must be a non-empty string.", result["message"])

    def test_validation_edit_instructions_not_string_returns_status(self):
        result = insert_edit_into_file("file.py", 123, "explain")
        self.assertEqual(result["status"], "failed_to_apply")
        self.assertEqual(result["file_path"], "file.py")
        self.assertIn("Input Validation Error: edit_instructions must be a string.", result["message"])

    def test_validation_empty_explanation_returns_status(self):
        result = insert_edit_into_file("file.py", "edit", "")
        self.assertEqual(result["status"], "failed_to_apply")
        self.assertEqual(result["file_path"], "file.py")
        self.assertIn("Input Validation Error: explanation must be a non-empty string.", result["message"])

    def test_validation_invalid_path_from_get_absolute_path(self):
        simulated_error_message = "Simulated bad path in get_absolute_path"
        with patch(self.mock_get_absolute_path_target, side_effect=ValueError(simulated_error_message)):
            result = insert_edit_into_file("a/problematic/path", "edit", "explain")
        self.assertEqual(result["status"], "failed_to_apply")
        self.assertEqual(result["file_path"], "a/problematic/path")
        self.assertIn(f"Input Validation Error: Invalid file_path 'a/problematic/path': {simulated_error_message}", result["message"])

    # --- File System Pre-check Tests (Status returns or Exceptions) ---
    def test_status_file_not_found(self):
        rel_path = "non_existent.py"
        abs_path = self._get_abs_path(rel_path)
        result = insert_edit_into_file(rel_path, "edit", "explain")
        self.assertEqual(result["status"], "file_not_found")
        self.assertEqual(result["file_path"], abs_path)
        self.assertIn(f"Target file '{rel_path}' (resolved to '{abs_path}') not found", result["message"])

    def test_exception_path_is_directory(self):
        rel_path = "llm_subdir"
        abs_path = self._get_abs_path(rel_path)
        expected_msg = f"Target path '{rel_path}' (resolved to '{abs_path}') is a directory, not a file."
        self.assert_error_behavior(
            func_to_call=insert_edit_into_file, expected_exception_type=custom_errors.EditConflictError,
            expected_message=expected_msg, file_path=rel_path, edit_instructions="any", explanation="any"
        )

    def test_exception_permission_denied_for_readonly_file(self):
        rel_path = "readonly_llm.txt"
        abs_path = self._get_abs_path(rel_path)
        expected_msg = f"File '{rel_path}' (resolved to '{abs_path}') is read-only."
        self.assert_error_behavior(
            func_to_call=insert_edit_into_file, expected_exception_type=custom_errors.PermissionDeniedError,
            expected_message=expected_msg, file_path=rel_path, edit_instructions="edit", explanation="explain"
        )

    def test_exception_uneditable_placeholder_content(self):
        rel_path = "uneditable_placeholder.bin"
        abs_path = self._get_abs_path(rel_path)
        uneditable_reason_from_util = "is binary and content not loaded"
        expected_msg = f"Cannot edit file '{rel_path}' (resolved to '{abs_path}'): existing content is unreadable or a placeholder ({uneditable_reason_from_util})."
        self.assert_error_behavior(
            func_to_call=insert_edit_into_file, expected_exception_type=custom_errors.EditConflictError,
            expected_message=expected_msg, file_path=rel_path, edit_instructions="edit", explanation="explain"
        )
        
    # --- LLM Interaction Tests (Mocked Success Cases) ---
    @patch('copilot.file_system.call_llm')
    def test_mocked_llm_successful_edit_returns_new_content(self, mock_call_llm_func):
        rel_path = "original_file.py"
        abs_path = self._get_abs_path(rel_path)
        # LLM is expected to return the *entire* new file content
        mock_llm_output = (
            "def greet():\n"
            "    print('Hello Original')\n"
            "\n"
            "def farewell():\n"
            "    print('Goodbye New World!')\n"
        )
        mock_call_llm_func.return_value = mock_llm_output
        
        edit_instructions = "Add a new function 'farewell' that prints 'Goodbye New World!' after the existing greet function."
        explanation = "A new function 'farewell' will be added to the file."

        result = insert_edit_into_file(rel_path, edit_instructions, explanation)

        self.assertEqual(result["status"], "success", msg=f"Message: {result.get('message')}")
        self.assertEqual(result["file_path"], abs_path)
        self.assertIn("LLM successfully rewrote file", result["message"])
        mock_call_llm_func.assert_called_once()
        prompt_arg = mock_call_llm_func.call_args[1]['prompt_text']
        self.assertIn("Hello Original", prompt_arg) 
        self.assertIn(explanation, prompt_arg)
        self.assertIn(edit_instructions, prompt_arg)

        expected_content_lines = [
            "def greet():\n", "    print('Hello Original')\n", "\n",
            "def farewell():\n", "    print('Goodbye New World!')\n"
        ]
        self.assertEqual(DB["file_system"][abs_path]["content_lines"], expected_content_lines)
        self.assertNotEqual(DB["file_system"][abs_path]["last_modified"], "2024-01-01T00:00:00Z")

    @patch('copilot.file_system.call_llm')
    def test_mocked_llm_returns_empty_content_clears_file(self, mock_call_llm_func):
        rel_path = "original_file.py"
        abs_path = self._get_abs_path(rel_path)
        mock_call_llm_func.return_value = "" 

        result = insert_edit_into_file(rel_path, "Delete all content.", "Make the file empty.")
        
        self.assertEqual(result["status"], "success", msg=f"Message: {result.get('message')}")
        self.assertEqual(result["file_path"], abs_path)
        self.assertEqual(DB["file_system"][abs_path]["content_lines"], [])
        self.assertEqual(DB["file_system"][abs_path]["size_bytes"], 0)

    @patch('copilot.file_system.call_llm')
    def test_mocked_llm_output_with_fences_gets_stripped(self, mock_call_llm_func):
        rel_path = "empty_for_llm.txt"
        abs_path = self._get_abs_path(rel_path)
        mock_llm_output = "```python\n# New content below\ndef new_func():\n    return True\n```"
        mock_call_llm_func.return_value = mock_llm_output

        result = insert_edit_into_file(rel_path, "Write new Python content.", "Populate the file with a Python function.")

        self.assertEqual(result["status"], "success", msg=f"Message: {result.get('message')}")
        self.assertEqual(result["file_path"], abs_path)
        expected_content_lines = ["# New content below\n", "def new_func():\n", "    return True\n"]
        self.assertEqual(DB["file_system"][abs_path]["content_lines"], expected_content_lines)

    # --- LLM Interaction Tests (Mocked Failure Cases - mapped to status returns) ---
    @patch('copilot.file_system.call_llm')
    def test_mocked_llm_call_raises_value_error_api_key(self, mock_call_llm_func):
        rel_path = "original_file.py"
        abs_path = self._get_abs_path(rel_path)
        mock_call_llm_func.side_effect = ValueError("Mocked API Key Error")

        result = insert_edit_into_file(rel_path, "edit", "explain")
        
        self.assertEqual(result["status"], "failed_to_apply")
        self.assertEqual(result["file_path"], abs_path)
        self.assertIn("LLM interface configuration error - Mocked API Key Error", result["message"])

    @patch('copilot.file_system.call_llm')
    def test_mocked_llm_call_raises_runtime_error_api_failure(self, mock_call_llm_func):
        rel_path = "original_file.py"
        abs_path = self._get_abs_path(rel_path)
        mock_call_llm_func.side_effect = RuntimeError("Mocked LLM API Failure")

        result = insert_edit_into_file(rel_path, "edit", "explain")

        self.assertEqual(result["status"], "failed_to_apply")
        self.assertEqual(result["file_path"], abs_path)
        self.assertIn("LLM generation failed - Mocked LLM API Failure", result["message"])

    @patch('copilot.file_system.call_llm')
    def test_mocked_llm_call_returns_none_safeguard(self, mock_call_llm_func):
        rel_path = "original_file.py"
        abs_path = self._get_abs_path(rel_path)
        mock_call_llm_func.return_value = None 

        result = insert_edit_into_file(rel_path, "edit", "explain")
        self.assertEqual(result["status"], "success") 
        self.assertEqual(DB["file_system"][abs_path]["content_lines"], [])


    @patch('copilot.file_system.call_llm')
    def test_real_llm_successful_edit_adds_content(self, mock_call_llm):
        # Mock LLM response with expected content
        mock_call_llm.return_value = '''def greet():
    print('Hello Original')

def farewell():
    print('Goodbye New World!')
'''
        
        rel_path = "original_file.py"
        abs_path = self._get_abs_path(rel_path)
        
        original_content_str = "".join(DB["file_system"][abs_path]["content_lines"])
        original_last_modified = DB["file_system"][abs_path]["last_modified"]

        # LLM is expected to return the *entire* new file content, including original parts
        edit_instructions = "Add a new function 'farewell' that prints 'Goodbye New World!' after the existing greet function. Preserve the greet function."
        explanation = "A new function 'farewell' will be added to the file, after 'greet'."

        result = insert_edit_into_file(rel_path, edit_instructions, explanation)

        self.assertEqual(result["status"], "success", msg=f"LLM edit failed. Message: {result.get('message')}")
        self.assertEqual(result["file_path"], abs_path)
        self.assertIn("LLM successfully rewrote file", result["message"])
        
        new_content_lines = DB["file_system"][abs_path]["content_lines"]
        new_content_str = "".join(new_content_lines)

        # Verify expected content is present
        self.assertIn("def greet():", new_content_str, "Original greet function missing.")
        self.assertIn("print('Hello Original')", new_content_str, "Original greet content missing.")
        self.assertIn("def farewell():", new_content_str, "New farewell function not found.")
        self.assertIn("print('Goodbye New World!')", new_content_str, "New farewell content not found.")
        
        # Check that content has changed and metadata updated
        self.assertNotEqual(new_content_str, original_content_str, "File content was not changed by the LLM.")
        self.assertNotEqual(DB["file_system"][abs_path]["last_modified"], original_last_modified, "Last modified timestamp was not updated.")
        self.assertTrue(DB["file_system"][abs_path]["size_bytes"] > 0, "File size is unexpectedly zero.")
        
        # Verify LLM was called
        mock_call_llm.assert_called_once()

    @patch('copilot.file_system.call_llm')
    def test_real_llm_output_with_fences_gets_stripped_if_llm_adds_them(self, mock_call_llm):
        # Mock LLM response with code fences that should be stripped
        mock_call_llm.return_value = '''```python
def hello_world():
    return 'Hello, World from LLM!'
```'''
        
        rel_path = "empty_for_llm.txt"
        abs_path = self._get_abs_path(rel_path)

        edit_instructions = "Create a Python script that defines a function `hello_world` which returns the string 'Hello, World from LLM!'."
        explanation = "Populate the file with a simple Python script containing one function."

        result = insert_edit_into_file(rel_path, edit_instructions, explanation)

        self.assertEqual(result["status"], "success", msg=f"Message: {result.get('message')}")
        self.assertEqual(result["file_path"], abs_path)
        
        new_content_lines = DB["file_system"][abs_path]["content_lines"]
        new_content_str = "".join(new_content_lines)

        # Check for expected Python content, assuming fences (if any) were stripped.
        self.assertIn("def hello_world():", new_content_str)
        self.assertIn("return 'Hello, World from LLM!'", new_content_str)
        # Check that fences themselves are not in the final content
        self.assertNotIn("```python", new_content_str, "Opening code fence found in final content.")
        self.assertNotIn("```", new_content_str.strip()[-(3):] if len(new_content_str.strip()) > 3 else new_content_str, 
                         "Closing code fence potentially found in final content.")
        
        # Verify LLM was called
        mock_call_llm.assert_called_once()


    # --- Real LLM Call Tests (Conditional based on API Key) ---
    @patch('copilot.file_system.call_llm')
    def test_real_llm_call_add_new_function(self, mock_call_llm):
        # Mock LLM response with new function added
        mock_call_llm.return_value = '''def greet():
    print('Hello Original')

def farewell():
    print('Goodbye from LLM!')
'''
        
        rel_path = "original_file.py"
        abs_path = self._get_abs_path(rel_path)
        
        original_db_entry = DB["file_system"][abs_path]
        original_modified_timestamp = original_db_entry["last_modified"]

        explanation = "A new Python function named 'farewell' that prints 'Goodbye from LLM!' should be added to the file, preserving existing content."
        edit_instructions = (
            "Add a new function `def farewell(): print('Goodbye from LLM!')` "
            "after the existing `greet` function. Ensure proper Python indentation and a blank line between functions."
        )

        result = insert_edit_into_file(rel_path, edit_instructions, explanation)

        self.assertEqual(result["status"], "success", 
            f"LLM call to add function failed. Message: {result.get('message')}")
        self.assertEqual(result["file_path"], abs_path)
        
        new_content_lines = DB["file_system"][abs_path]["content_lines"]
        new_content_str = "".join(new_content_lines)

        # Verify original content is preserved
        self.assertIn("def greet():", new_content_str)
        self.assertIn("print('Hello Original')", new_content_str)
        
        # Verify new content is added
        self.assertIn("def farewell():", new_content_str)
        self.assertIn("print('Goodbye from LLM!')", new_content_str)
        
        # Verify LLM was called
        mock_call_llm.assert_called_once()
        

    @patch('copilot.file_system.call_llm')
    def test_real_llm_call_simple_edit_produces_change(self, mock_call_llm):
        # Mock LLM response with modified content
        mock_call_llm.return_value = '''def greet():
    print('Hello Updated World')
'''
        
        rel_path = "original_file.py"
        abs_path = self._get_abs_path(rel_path)
        original_content_str = "".join(DB["file_system"][abs_path]["content_lines"])

        explanation = "Modify the print statement in the greet function to say 'Hello Updated World'."
        edit_instructions = "In the greet function, change `print('Hello Original')` to `print('Hello Updated World')`."
        
        result = insert_edit_into_file(rel_path, edit_instructions, explanation)
        
        self.assertEqual(result["status"], "success", f"LLM call for simple edit failed. Message: {result.get('message')}")
        
        new_content_str = "".join(DB["file_system"][abs_path]["content_lines"])
        self.assertNotEqual(new_content_str, original_content_str, "Content was not changed by the LLM.")
        self.assertIn("print('Hello Updated World')", new_content_str)
        self.assertNotIn("print('Hello Original')", new_content_str)
        self.assertIn("def greet():", new_content_str) # Ensure function structure is somewhat preserved
        
        # Verify LLM was called
        mock_call_llm.assert_called_once()

if __name__ == '__main__':
    unittest.main()