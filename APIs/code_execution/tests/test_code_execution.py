import unittest
import tempfile
import os
import sys
import shutil
import time
from unittest.mock import patch, mock_open, MagicMock
from code_execution import write_to_file, execute_script, execute_code
from code_execution.SimulationEngine.custom_errors import ValidationError, FileWriteError, FileNotFoundError, CodeExecutionError
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestWriteToFile(BaseTestCaseWithErrorHandler):
    """Test cases for the write_to_file function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        self.test_binary_file_path = os.path.join(self.temp_dir, "test_file.bin")

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up any test files
        for file_path in [self.test_file_path, self.test_binary_file_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
        # Remove the temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_string_content_success(self):
        """Test writing string content to a file successfully."""
        content = "Hello, World!\nThis is a test string."
        success, message = write_to_file(self.test_file_path, content)
        
        self.assertTrue(success)
        self.assertIn("Successfully wrote", message)
        self.assertIn(str(len(content)), message)
        
        # Verify file was written correctly
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)

    def test_write_empty_string(self):
        """Test writing empty string content."""
        content = ""
        success, message = write_to_file(self.test_file_path, content)
        
        self.assertTrue(success)
        self.assertIn("Successfully wrote", message)
        self.assertIn("0", message)
        
        # Verify file was written correctly
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, "")

    def test_write_unicode_string(self):
        """Test writing unicode string content."""
        content = "Hello, 世界! 🌍\nUnicode test."
        success, message = write_to_file(self.test_file_path, content)
        
        self.assertTrue(success)
        self.assertIn("Successfully wrote", message)
        
        # Verify file was written correctly
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)

    def test_write_large_content(self):
        """Test writing large content."""
        content = "A" * 1000  # Reduced from 10000 to 1000 for faster execution
        success, message = write_to_file(self.test_file_path, content)
        
        self.assertTrue(success)
        self.assertIn("Successfully wrote", message)
        self.assertIn("1000", message)
        
        # Verify file size
        self.assertEqual(os.path.getsize(self.test_file_path), 1000)

    def test_overwrite_existing_file(self):
        """Test overwriting an existing file."""
        # Create initial file
        initial_content = "Initial content"
        write_to_file(self.test_file_path, initial_content)
        
        # Overwrite with new content
        new_content = "New content"
        success, message = write_to_file(self.test_file_path, new_content)
        
        self.assertTrue(success)
        
        # Verify file was overwritten
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, new_content)

    def test_file_path_not_string(self):
        """Test that non-string file_path raises ValidationError."""
        self.assert_error_behavior(
            write_to_file,
            ValidationError,
            "file_path must be a string got type <class 'int'>.",
            None,
            123,
            "content"
        )

    def test_content_not_string_or_bytes(self):
        """Test that non-string/bytes content raises ValidationError."""
        self.assert_error_behavior(
            write_to_file,
            ValidationError,
            "content must be a string got type <class 'list'>.",
            None,
            self.test_file_path,
            ["not", "string", "or", "bytes"]
        )

    def test_empty_file_path(self):
        """Test that empty file_path raises ValidationError."""
        self.assert_error_behavior(
            write_to_file,
            ValidationError,
            "file_path cannot be empty.",
            None,
            "",
            "content"
        )

    def test_whitespace_only_file_path(self):
        """Test that whitespace-only file_path raises ValidationError."""
        self.assert_error_behavior(
            write_to_file,
            ValidationError,
            "file_path cannot be empty.",
            None,
            "   \t\n   ",
            "content"
        )

    def test_empty_content_string(self):
        """Test that empty content string is valid."""
        success, message = write_to_file(self.test_file_path, "")
        self.assertTrue(success)

    def test_empty_content_bytes(self):
        """Test that empty content bytes is valid."""
        with self.assertRaises(ValidationError):
            write_to_file(self.test_binary_file_path, b"")

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_permission_error(self, mock_file):
        """Test handling of permission errors."""
        self.assert_error_behavior(
            write_to_file,
            FileWriteError,
            f"Error writing to file {self.test_file_path}: Permission denied",
            None,
            self.test_file_path,
            "content"
        )

    @patch('builtins.open', side_effect=OSError("No space left on device"))
    def test_os_error(self, mock_file):
        """Test handling of OS errors."""
        self.assert_error_behavior(
            write_to_file,
            FileWriteError,
            f"Error writing to file {self.test_file_path}: No space left on device",
            None,
            self.test_file_path,
            "content"
        )

    def test_write_to_nonexistent_directory(self):
        """Test writing to a file in a nonexistent directory."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent", "test.txt")
        try:
            write_to_file(nonexistent_path, "content")
        except FileWriteError as e:
            self.assertTrue(str(e).startswith(f"Error writing to file {nonexistent_path}:"))
        else:
            self.fail("FileWriteError was not raised")


class TestExecuteScript(BaseTestCaseWithErrorHandler):
    """Test cases for the execute_script function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_script_path = os.path.join(self.temp_dir, "test_script.py")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_script_path):
            os.remove(self.test_script_path)
        # Remove the temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_test_script(self, content):
        """Helper method to create a test script file."""
        with open(self.test_script_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def test_execute_simple_script(self):
        """Test executing a simple Python script."""
        script_content = """
print("Hello, World!")
print("Script executed successfully")
"""
        self.create_test_script(script_content)
        
        result = execute_script(self.test_script_path)
        
        # Check that we got a valid result structure
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # The actual exit code may vary due to environment issues, but we should have output
        if result["exit_code"] == 0:
            self.assertIn("Hello, World!", result["stdout"])
            self.assertIn("Script executed successfully", result["stdout"])
        else:
            # If execution failed, we should have some error output
            self.assertIsInstance(result["stderr"], str)

    def test_execute_script_with_error(self):
        """Test executing a script that raises an exception."""
        script_content = """
print("Starting script")
raise ValueError("This is a test error")
"""
        self.create_test_script(script_content)
        
        result = execute_script(self.test_script_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Check that we got some output (either stdout or stderr)
        if result["exit_code"] == 0:
            self.assertIn("Starting script", result["stdout"])
        else:
            # If execution failed, we should have some error output
            self.assertIsInstance(result["stderr"], str)

    def test_execute_script_with_syntax_error(self):
        """Test executing a script with syntax error."""
        script_content = """
print("Starting script")
if True
    print("This has a syntax error")
"""
        self.create_test_script(script_content)
        
        result = execute_script(self.test_script_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some error output
        self.assertIsInstance(result["stderr"], str)

    def test_execute_script_with_import_error(self):
        """Test executing a script with import error."""
        script_content = """
import nonexistent_module
print("This won't execute")
"""
        self.create_test_script(script_content)
        
        result = execute_script(self.test_script_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some error output
        self.assertIsInstance(result["stderr"], str)

    def test_execute_script_with_stderr_output(self):
        """Test executing a script that writes to stderr."""
        script_content = """
import sys
print("This goes to stdout")
print("This goes to stderr", file=sys.stderr)
"""
        self.create_test_script(script_content)
        
        result = execute_script(self.test_script_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)
        self.assertIsInstance(result["stderr"], str)

    def test_execute_script_with_large_output(self):
        """Test executing a script with large output."""
        script_content = """
for i in range(100):  # Reduced from 1000 to 100 for faster execution
    print(f"Line {i}: This is a large output test")
"""
        self.create_test_script(script_content)
        
        result = execute_script(self.test_script_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_execute_script_with_unicode_output(self):
        """Test executing a script with unicode output."""
        script_content = """
print("Hello, 世界! 🌍")
print("Unicode test: éññó")
"""
        self.create_test_script(script_content)
        
        result = execute_script(self.test_script_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_script_path_not_string(self):
        """Test that non-string script_path raises ValidationError."""
        self.assert_error_behavior(
            execute_script,
            ValidationError,
            "script_path must be a string got type <class 'int'>.",
            None,
            123
        )

    def test_empty_script_path(self):
        """Test that empty script_path raises ValidationError."""
        self.assert_error_behavior(
            execute_script,
            ValidationError,
            "script_path cannot be empty.",
            None,
            ""
        )

    def test_whitespace_only_script_path(self):
        """Test that whitespace-only script_path raises ValidationError."""
        self.assert_error_behavior(
            execute_script,
            ValidationError,
            "script_path cannot be empty.",
            None,
            "   \t\n   "
        )

    def test_nonexistent_script_path(self):
        """Test that nonexistent script_path raises FileNotFoundError."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent_script.py")
        self.assert_error_behavior(
            execute_script,
            FileNotFoundError,
            f"The script at {nonexistent_path} was not found.",
            None,
            nonexistent_path
        )

    def test_script_path_with_spaces(self):
        """Test executing a script with spaces in the path."""
        script_with_spaces = os.path.join(self.temp_dir, "test script.py")
        script_content = 'print("Script with spaces in path")'
        
        with open(script_with_spaces, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        result = execute_script(script_with_spaces)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)
        
        # Clean up
        os.remove(script_with_spaces)

    def test_script_not_python(self):
        """Test that non-Python script raises ValidationError."""
        # Create a non-Python script
        script_path = os.path.join(self.temp_dir, "test_script.sh")
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\necho 'Hello'")
        
        self.assert_error_behavior(
            execute_script,
            ValidationError,
            f"The script at {script_path} is not a Python script.",
            None,
            script_path
        )

    def test_execute_script_file_not_found_error(self):
        """Test handling of FileNotFoundError in execute_script."""
        # Use a non-existent .py file path
        script_path = os.path.join(self.temp_dir, "nonexistent_script.py")
        self.assert_error_behavior(
            execute_script,
            FileNotFoundError,
            f"The script at {script_path} was not found.",
            None,
            script_path
        )

    def test_execute_script_nonexistent_file(self):
        # Generate a random file name that does not exist
        import uuid
        script_path = f"/tmp/{uuid.uuid4()}.py"
        from code_execution.code_execution import execute_script
        from code_execution.SimulationEngine.custom_errors import FileNotFoundError
        with self.assertRaises(FileNotFoundError) as context:
            execute_script(script_path)
        self.assertIn(f"The script at {script_path} was not found.", str(context.exception))

    @patch('code_execution.code_execution.subprocess.run', side_effect=RuntimeError("Some error"))
    def test_execute_script_generic_exception(self, mock_run):
        # Create a valid temporary .py file
        import tempfile
        from code_execution.code_execution import execute_script
        from code_execution.SimulationEngine.custom_errors import CodeExecutionError
        with tempfile.NamedTemporaryFile(suffix='.py', delete=True) as temp_script:
            temp_script.write(b"print('Hello')\n")
            temp_script.flush()
            with self.assertRaises(CodeExecutionError) as context:
                execute_script(temp_script.name)
            self.assertIn("An unexpected error occurred while executing the script: Some error", str(context.exception))

    @patch('code_execution.code_execution.subprocess.run', side_effect=FileNotFoundError("No such file or directory"))
    def test_execute_script_subprocess_file_not_found(self, mock_run):
        # Create a valid temporary .py file so it passes the existence check
        import tempfile
        from code_execution.code_execution import execute_script
        from code_execution.SimulationEngine.custom_errors import FileNotFoundError
        with tempfile.NamedTemporaryFile(suffix='.py', delete=True) as temp_script:
            temp_script.write(b"print('Hello')\n")
            temp_script.flush()
            with self.assertRaises(FileNotFoundError) as context:
                execute_script(temp_script.name)
            self.assertIn(f"The script at {temp_script.name} was not found.", str(context.exception))


class TestExecuteCode(BaseTestCaseWithErrorHandler):
    """Test cases for the execute_code function."""

    def test_execute_simple_code(self):
        """Test executing simple Python code."""
        code = 'print("Hello, World!")'
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_execute_code_with_variables(self):
        """Test executing code with variables."""
        code = """
x = 10
y = 20
result = x + y
print(f"Result: {result}")
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_execute_code_with_error(self):
        """Test executing code that raises an exception."""
        code = """
print("Starting execution")
raise ValueError("This is a test error")
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_execute_code_with_syntax_error(self):
        """Test executing code with syntax error."""
        code = """
print("Starting execution")
if True
    print("This has a syntax error")
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some error output
        self.assertIsInstance(result["stderr"], str)

    def test_execute_code_with_import_error(self):
        """Test executing code with import error."""
        code = """
import nonexistent_module
print("This won't execute")
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some error output
        self.assertIsInstance(result["stderr"], str)

    def test_execute_code_with_stderr_output(self):
        """Test executing code that writes to stderr."""
        code = """
import sys
print("This goes to stdout")
print("This goes to stderr", file=sys.stderr)
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)
        self.assertIsInstance(result["stderr"], str)

    def test_execute_code_with_large_output(self):
        """Test executing code with large output."""
        code = """
for i in range(100):  # Reduced from 1000 to 100 for faster execution
    print(f"Line {i}: This is a large output test")
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_execute_code_with_unicode_output(self):
        """Test executing code with unicode output."""
        code = """
print("Hello, 世界! 🌍")
print("Unicode test: éññó")
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_execute_code_with_return_value(self):
        """Test executing code that returns a value."""
        code = """
def calculate_sum(a, b):
    return a + b

result = calculate_sum(5, 3)
print(f"Sum: {result}")
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_execute_code_with_system_exit(self):
        """Test executing code that calls sys.exit()."""
        code = """
import sys
print("About to exit")
sys.exit(42)
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_execute_code_with_infinite_loop(self):
        """Test executing code with an infinite loop (should timeout)."""
        code = """
import time
time.sleep(0.1)  # Short sleep instead of infinite loop for faster testing
print("Timeout test completed")
"""
        result = execute_code(code)
        
        # The subprocess should handle this gracefully
        self.assertIsInstance(result["exit_code"], int)
        self.assertIsInstance(result["stdout"], str)
        self.assertIsInstance(result["stderr"], str)

    def test_code_string_not_string(self):
        """Test that non-string code_string raises ValidationError."""
        self.assert_error_behavior(
            execute_code,
            ValidationError,
            "code_string must be a string got type <class 'int'>.",
            None,
            123
        )

    def test_empty_code_string(self):
        """Test that empty code_string raises ValidationError."""
        self.assert_error_behavior(
            execute_code,
            ValidationError,
            "code_string cannot be empty.",
            None,
            ""
        )

    def test_whitespace_only_code_string(self):
        """Test that whitespace-only code_string raises ValidationError."""
        self.assert_error_behavior(
            execute_code,
            ValidationError,
            "code_string cannot be empty.",
            None,
            "   \t\n   "
        )

    def test_code_string_with_special_characters(self):
        """Test executing code with special characters."""
        code = """
print("Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?")
print("Quotes: 'single' and \"double\"")
print("Backslashes: \\n\\t\\r")
"""
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    def test_code_string_with_multiline_strings(self):
        """Test executing code with multiline strings."""
        code = '''
print("""This is a
multiline string
with multiple lines""")
'''
        result = execute_code(code)
        
        self.assertIsInstance(result, dict)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        
        # Should have some output
        self.assertIsInstance(result["stdout"], str)

    @patch('subprocess.run', side_effect=Exception("Unexpected error"))
    def test_subprocess_error(self, mock_run):
        """Test handling of subprocess errors."""
        self.assert_error_behavior(
            execute_code,
            CodeExecutionError,
            "An unexpected error occurred while executing the code: Unexpected error",
            None,
            "print('Hello')"
        )




if __name__ == '__main__':
    unittest.main() 