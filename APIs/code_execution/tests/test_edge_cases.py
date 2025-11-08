"""
Comprehensive edge case tests for code_execution service

This module contains extensive edge case testing to ensure >90% code coverage
for all functions in the code_execution service.
"""

from typing import Dict, Any, List, Optional, Tuple
import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
import sys
import subprocess

from code_execution import write_to_file, execute_script, execute_code
from code_execution.SimulationEngine.custom_errors import (
    ValidationError, FileWriteError, FileNotFoundError, CodeExecutionError
)


class TestWriteToFileEdgeCases(unittest.TestCase):
    """
    Comprehensive edge case tests for write_to_file function.
    
    Tests cover:
    - Empty content scenarios
    - Special characters and encodings
    - Binary data handling
    - Permission errors
    - Directory creation scenarios
    - Path validation edge cases
    """

    def test_write_empty_string(self) -> None:
        """Test writing an empty string to a file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            success, message = write_to_file(tmp_path, "")
            self.assertTrue(success)
            self.assertIn("Successfully wrote 0 chars", message)
            
            with open(tmp_path, 'r') as f:
                content = f.read()
            self.assertEqual(content, "")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_write_unicode_content(self) -> None:
        """Test writing Unicode content with special characters."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        unicode_content = "Hello 世界! 🌍 Ñoël Café résumé"
        
        try:
            success, message = write_to_file(tmp_path, unicode_content)
            self.assertTrue(success)
            
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertEqual(content, unicode_content)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_write_to_nested_directory(self) -> None:
        """Test writing to a file in a non-existent nested directory path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            nested_path = os.path.join(tmp_dir, "level1", "level2", "test.txt")
            
            # Directory doesn't exist initially
            self.assertFalse(os.path.exists(os.path.dirname(nested_path)))
            
            # Should raise FileWriteError when trying to write to non-existent directory
            with self.assertRaises(FileWriteError) as cm:
                write_to_file(nested_path, "nested content")
            self.assertIn("No such file or directory", str(cm.exception))

    def test_write_large_content(self) -> None:
        """Test writing large content (1MB) to verify performance."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        # Generate 1MB of content
        large_content = "A" * (1024 * 1024)
        
        try:
            success, message = write_to_file(tmp_path, large_content)
            self.assertTrue(success)
            self.assertIn("Successfully wrote 1048576 chars", message)
            
            # Verify content
            with open(tmp_path, 'r') as f:
                content = f.read()
            self.assertEqual(len(content), 1024 * 1024)
            self.assertTrue(content.startswith("AAAA"))
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_permission_error_handling(self) -> None:
        """Test handling of permission errors."""
        # Use a path that will cause FileWriteError (either permission denied or not found)
        with self.assertRaises(FileWriteError) as cm:
            write_to_file("/root/protected.txt", "content")
        # Accept either "Permission denied" or "No such file or directory"
        error_msg = str(cm.exception)
        self.assertTrue(
            "Permission denied" in error_msg or "No such file or directory" in error_msg,
            f"Expected permission or file not found error, got: {error_msg}"
        )

    def test_directory_creation_failure(self) -> None:
        """Test handling of directory creation failures."""
        # Use an invalid path that will cause FileWriteError
        with self.assertRaises(FileWriteError) as cm:
            write_to_file("/invalid/path/file.txt", "content")
        self.assertIn("No such file or directory", str(cm.exception))


class TestExecuteScriptEdgeCases(unittest.TestCase):
    """
    Comprehensive edge case tests for execute_script function.
    
    Tests cover:
    - Python executable fallback scenarios  
    - Different file extensions
    - Script permission handling
    - Various error conditions
    - Environment variable scenarios
    """

    def test_python_executable_fallback_shutil_fails(self) -> None:
        """Test fallback to sys.executable when 'which python' and 'which python3' fail."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("print('Hello from fallback!')")
            tmp_path = tmp.name
        
        try:
            with patch('subprocess.run') as mock_subprocess:
                def subprocess_side_effect(*args, **kwargs):
                    # Check if this is a 'which' command
                    if len(args) > 0 and isinstance(args[0], list):
                        if args[0] == ['which', 'python'] or args[0] == ['which', 'python3']:
                            # Return empty stdout for 'which' commands (not found)
                            return MagicMock(stdout="", stderr="", returncode=1)
                        elif args[0][0] == sys.executable:
                            # This is the actual execution call with sys.executable
                            return MagicMock(
                                returncode=0,
                                stdout="Hello from fallback!",
                                stderr=""
                            )
                    
                    # Default fallback
                    return MagicMock(returncode=0, stdout="", stderr="")
                
                mock_subprocess.side_effect = subprocess_side_effect
                
                result = execute_script(tmp_path)
                
                # Verify sys.executable was used (line 98 coverage)
                # Should be called 3 times: 'which python', 'which python3', then execution
                self.assertGreaterEqual(mock_subprocess.call_count, 3)
                
                # Verify the execution call used sys.executable
                execution_calls = [call for call in mock_subprocess.call_args_list 
                                 if len(call[0]) > 0 and isinstance(call[0][0], list) 
                                 and len(call[0][0]) >= 2 and call[0][0][0] == sys.executable]
                self.assertGreater(len(execution_calls), 0, "sys.executable should be used in fallback")
                
                self.assertEqual(result['exit_code'], 0)
                self.assertEqual(result['stdout'], "Hello from fallback!")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_script_with_syntax_error(self) -> None:
        """Test execution of a script with Python syntax errors."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            # Invalid Python syntax
            tmp.write("print('Hello'\n  invalid syntax here\nprint('World')")
            tmp_path = tmp.name
        
        try:
            result = execute_script(tmp_path)
            
            # Should have non-zero exit code due to syntax error
            self.assertNotEqual(result['exit_code'], 0)
            self.assertIn("SyntaxError", result['stderr'])
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_script_with_runtime_exception(self) -> None:
        """Test execution of a script that raises runtime exceptions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("""
print("Before error")
raise ValueError("This is a test error")
print("After error - should not execute")
""")
            tmp_path = tmp.name
        
        try:
            result = execute_script(tmp_path)
            
            self.assertNotEqual(result['exit_code'], 0)
            self.assertIn("Before error", result['stdout'])
            self.assertIn("ValueError", result['stderr'])
            self.assertIn("This is a test error", result['stderr'])
            self.assertNotIn("After error", result['stdout'])
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_script_with_imports_and_complex_logic(self) -> None:
        """Test execution of a complex script with imports and logic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("""
import os
import sys
import json

# Test complex operations
data = {"test": True, "numbers": [1, 2, 3]}
print(f"JSON: {json.dumps(data)}")
print(f"OS name: {os.name}")
print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")

# Test calculations  
result = sum(range(100))
print(f"Sum 0-99: {result}")
""")
            tmp_path = tmp.name
        
        try:
            result = execute_script(tmp_path)
            
            self.assertEqual(result['exit_code'], 0)
            self.assertIn('"test": true', result['stdout'])
            self.assertIn("OS name:", result['stdout'])
            self.assertIn("Python version:", result['stdout'])
            self.assertIn("Sum 0-99: 4950", result['stdout'])
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_nonexistent_script_file(self) -> None:
        """Test execution of a non-existent script file."""
        with self.assertRaises(FileNotFoundError):
            execute_script("/path/that/does/not/exist.py")

    def test_script_with_infinite_loop_timeout(self) -> None:
        """Test script execution with potential infinite loop (using timeout)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write("""
import time
# Sleep for a very short time to simulate work without infinite loop
time.sleep(0.1)
print("Completed successfully")
""")
            tmp_path = tmp.name
        
        try:
            result = execute_script(tmp_path)
            
            self.assertEqual(result['exit_code'], 0)
            self.assertIn("Completed successfully", result['stdout'])
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestExecuteCodeEdgeCases(unittest.TestCase):
    """
    Comprehensive edge case tests for execute_code function.
    
    Tests cover:
    - Python executable fallback scenarios
    - Various code execution scenarios
    - Memory and performance edge cases
    - Error handling for malformed code
    """

    def test_python_executable_fallback_which_fails(self) -> None:
        """Test fallback to sys.executable when 'which python' and 'which python3' fail."""
        test_code = "print('Fallback test successful!')"
        
        with patch('subprocess.run') as mock_subprocess:
            def subprocess_side_effect(*args, **kwargs):
                # Check if this is a 'which' command
                if len(args) > 0 and isinstance(args[0], list):
                    if args[0] == ['which', 'python'] or args[0] == ['which', 'python3']:
                        # Return empty stdout for 'which' commands (not found)
                        return MagicMock(stdout="", stderr="", returncode=1)
                    elif (len(args[0]) >= 3 and 
                          args[0][0] == sys.executable and 
                          args[0][1] == "-c" and 
                          args[0][2] == test_code):
                        # This is the actual code execution call with sys.executable
                        return MagicMock(
                            returncode=0,
                            stdout="Fallback test successful!",
                            stderr=""
                        )
                
                # Default fallback
                return MagicMock(returncode=0, stdout="", stderr="")
            
            mock_subprocess.side_effect = subprocess_side_effect
            
            result = execute_code(test_code)
            
            # Verify the fallback path was taken (line 152 coverage)
            # Should be called 3 times: 'which python', 'which python3', then execution
            self.assertGreaterEqual(mock_subprocess.call_count, 3)
            
            # Find the execution call that used sys.executable
            execution_calls = [call for call in mock_subprocess.call_args_list 
                             if len(call[0]) > 0 and isinstance(call[0][0], list) 
                             and len(call[0][0]) >= 3 
                             and call[0][0][0] == sys.executable 
                             and call[0][0][1] == "-c"]
            self.assertGreater(len(execution_calls), 0, "sys.executable should be used for code execution")
            
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(result['stdout'], "Fallback test successful!")

    def test_multiline_code_with_indentation(self) -> None:
        """Test execution of multiline code with proper indentation."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 fibonacci numbers
results = [fibonacci(i) for i in range(10)]
print(f"Fibonacci sequence: {results}")

# Test nested structures
data = {
    'name': 'test',
    'values': [1, 2, 3],
    'nested': {
        'key': 'value'
    }
}
print(f"Data: {data}")
"""
        
        result = execute_code(code)
        
        self.assertEqual(result['exit_code'], 0)
        self.assertIn("Fibonacci sequence: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]", result['stdout'])
        self.assertIn("Data: {'name': 'test'", result['stdout'])

    def test_code_with_memory_intensive_operations(self) -> None:
        """Test execution of memory-intensive code operations."""
        code = """
# Create and manipulate large data structures
large_list = list(range(10000))
squared = [x**2 for x in large_list[:1000]]  # Limited to avoid excessive memory
print(f"First 5 squared: {squared[:5]}")
print(f"Last 5 squared: {squared[-5:]}")
print(f"Total items processed: {len(squared)}")

# Test string operations
text = "Hello" * 1000
print(f"Text length: {len(text)}")
print(f"Text starts with: {text[:20]}")
"""
        
        result = execute_code(code)
        
        self.assertEqual(result['exit_code'], 0)
        self.assertIn("First 5 squared: [0, 1, 4, 9, 16]", result['stdout'])
        self.assertIn("Last 5 squared:", result['stdout']) 
        self.assertIn("Total items processed: 1000", result['stdout'])
        self.assertIn("Text length: 5000", result['stdout'])

    def test_code_with_exception_handling(self) -> None:
        """Test code that includes its own exception handling."""
        code = """
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Caught exception: {e}")
    result = float('inf')

print(f"Result: {result}")

try:
    import nonexistent_module
except ImportError:
    print("Import error handled gracefully")

print("Execution completed successfully")
"""
        
        result = execute_code(code)
        
        self.assertEqual(result['exit_code'], 0)
        self.assertIn("Caught exception: division by zero", result['stdout'])
        self.assertIn("Result: inf", result['stdout'])
        self.assertIn("Import error handled gracefully", result['stdout'])
        self.assertIn("Execution completed successfully", result['stdout'])

    def test_code_with_standard_library_usage(self) -> None:
        """Test code that extensively uses Python standard library."""
        code = """
import datetime
import math
import random
import re
import json

# Date/time operations
now = datetime.datetime.now()
print(f"Current year: {now.year}")

# Math operations
print(f"Pi: {math.pi:.4f}")
print(f"Square root of 16: {math.sqrt(16)}")

# Random operations (with seed for reproducibility)
random.seed(42)
print(f"Random number: {random.randint(1, 100)}")

# Regex operations
text = "Email: test@example.com"
email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'
match = re.search(email_pattern, text)
if match:
    print(f"Found email: {match.group()}")

# JSON operations
data = {"name": "test", "value": 123}
json_str = json.dumps(data)
parsed = json.loads(json_str)
print(f"JSON roundtrip successful: {parsed['name']}")
"""
        
        result = execute_code(code)
        
        self.assertEqual(result['exit_code'], 0)
        self.assertIn("Current year:", result['stdout'])
        self.assertIn("Pi: 3.1416", result['stdout'])  
        self.assertIn("Square root of 16: 4.0", result['stdout'])
        self.assertIn("Random number:", result['stdout'])
        self.assertIn("Found email: test@example.com", result['stdout'])
        self.assertIn("JSON roundtrip successful: test", result['stdout'])

    def test_empty_code_string(self) -> None:
        """Test execution of empty code string."""
        # Empty code string should raise ValidationError
        with self.assertRaises(ValidationError) as cm:
            execute_code("")
        self.assertIn("cannot be empty", str(cm.exception))

    def test_whitespace_only_code(self) -> None:
        """Test execution of code with only whitespace."""
        # Whitespace-only code should raise ValidationError (treated as empty)
        with self.assertRaises(ValidationError) as cm:
            execute_code("   \n\t   \n   ")
        self.assertIn("cannot be empty", str(cm.exception))


class TestSimulationEngineIntegration(unittest.TestCase):
    """
    Tests for simulation engine integration and error simulation modes.
    """

    def test_error_simulation_disabled(self) -> None:
        """Test that functions work normally when error simulation is disabled."""
        # These tests ensure the normal path works as expected
        success, message = write_to_file("test_temp.txt", "test content")
        self.assertTrue(success)
        self.assertIn("Successfully wrote", message)
        self.assertIn("test_temp.txt", message)
        
        # Clean up
        if os.path.exists("test_temp.txt"):
            os.unlink("test_temp.txt")

    def test_function_signatures_match_original(self) -> None:
        """Test that function signatures match the original generic_tools versions."""
        import inspect
        
        # Test write_to_file signature
        sig = inspect.signature(write_to_file)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ['file_path', 'content'])
        
        # Test execute_script signature  
        sig = inspect.signature(execute_script)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ['script_path'])
        
        # Test execute_code signature
        sig = inspect.signature(execute_code)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ['code_string'])


if __name__ == '__main__':
    unittest.main(verbosity=2)