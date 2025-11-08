"""
Simplified test suite for file utility functions in the Media Control Service.
This version can be run directly without complex import dependencies.
"""

import unittest
import os
import tempfile
import base64
import sys
from unittest.mock import Mock, patch, mock_open

# Add the current directory to the path to import file_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'SimulationEngine'))
import file_utils


class TestFileUtilsSimple(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_text_file = os.path.join(self.temp_dir, "test.txt")
        self.test_binary_file = os.path.join(self.temp_dir, "test.bin")
        self.test_python_file = os.path.join(self.temp_dir, "test.py")
        self.test_json_file = os.path.join(self.temp_dir, "test.json")
        
        # Create test files
        with open(self.test_text_file, 'w', encoding='utf-8') as f:
            f.write("Hello, World! This is a test file.")
        
        with open(self.test_binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04\x05')
        
        with open(self.test_python_file, 'w', encoding='utf-8') as f:
            f.write('print("Hello, Python!")')
        
        with open(self.test_json_file, 'w', encoding='utf-8') as f:
            f.write('{"key": "value", "number": 42}')

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    # region File Type Detection Tests
    def test_is_text_file_with_text_extensions(self):
        """Test is_text_file with various text file extensions."""
        text_files = [
            "file.py", "script.js", "document.html", "data.csv", 
            "config.json", "readme.md", "style.css", "query.sql"
        ]
        for file_path in text_files:
            self.assertTrue(file_utils.is_text_file(file_path), f"Failed for {file_path}")

    def test_is_text_file_with_binary_extensions(self):
        """Test is_text_file with binary file extensions."""
        binary_files = [
            "image.jpg", "document.pdf", "video.mp4", "archive.zip",
            "executable.exe", "library.dll", "font.ttf"
        ]
        for file_path in binary_files:
            self.assertFalse(file_utils.is_text_file(file_path), f"Failed for {file_path}")

    def test_is_text_file_with_no_extension(self):
        """Test is_text_file with files that have no extension."""
        no_ext_files = ["file", "script", "document"]
        for file_path in no_ext_files:
            self.assertFalse(file_utils.is_text_file(file_path), f"Failed for {file_path}")

    def test_is_text_file_case_insensitive(self):
        """Test is_text_file with different case extensions."""
        self.assertTrue(file_utils.is_text_file("file.PY"))
        self.assertTrue(file_utils.is_text_file("script.JS"))
        self.assertFalse(file_utils.is_text_file("image.JPG"))

    def test_is_binary_file_with_binary_extensions(self):
        """Test is_binary_file with various binary file extensions."""
        binary_files = [
            "image.jpg", "document.pdf", "video.mp4", "archive.zip",
            "executable.exe", "library.dll", "font.ttf", "audio.mp3"
        ]
        for file_path in binary_files:
            self.assertTrue(file_utils.is_binary_file(file_path), f"Failed for {file_path}")

    def test_is_binary_file_with_text_extensions(self):
        """Test is_binary_file with text file extensions."""
        text_files = [
            "file.py", "script.js", "document.html", "data.csv", 
            "config.json", "readme.md", "style.css"
        ]
        for file_path in text_files:
            self.assertFalse(file_utils.is_binary_file(file_path), f"Failed for {file_path}")

    def test_is_binary_file_with_no_extension(self):
        """Test is_binary_file with files that have no extension."""
        no_ext_files = ["file", "script", "document"]
        for file_path in no_ext_files:
            self.assertFalse(file_utils.is_binary_file(file_path), f"Failed for {file_path}")

    def test_is_binary_file_case_insensitive(self):
        """Test is_binary_file with different case extensions."""
        self.assertTrue(file_utils.is_binary_file("image.JPG"))
        self.assertTrue(file_utils.is_binary_file("document.PDF"))
        self.assertFalse(file_utils.is_binary_file("file.PY"))
    # endregion

    # region MIME Type Tests
    def test_get_mime_type_text_files(self):
        """Test get_mime_type with text files."""
        mime_tests = [
            ("file.py", "text/x-python"),
            ("script.js", "text/javascript"),  # Updated to match actual MIME type
            ("document.html", "text/html"),
            ("data.csv", "text/csv"),
            ("config.json", "application/json"),
            ("style.css", "text/css")
        ]
        for file_path, expected_mime in mime_tests:
            mime_type = file_utils.get_mime_type(file_path)
            self.assertEqual(mime_type, expected_mime, f"Failed for {file_path}")
        
        # Test markdown file separately to handle different MIME type behaviors
        md_mime_type = file_utils.get_mime_type("readme.md")
        # Accept both possible MIME types for markdown files
        self.assertIn(md_mime_type, ["text/markdown", "application/octet-stream"], 
                     f"Unexpected MIME type for readme.md: {md_mime_type}")

    def test_get_mime_type_binary_files(self):
        """Test get_mime_type with binary files."""
        mime_tests = [
            ("image.jpg", "image/jpeg"),
            ("image.png", "image/png"),
            ("document.pdf", "application/pdf"),
            ("video.mp4", "video/mp4"),
            ("audio.mp3", "audio/mpeg"),
            ("archive.zip", "application/zip")
        ]
        for file_path, expected_mime in mime_tests:
            mime_type = file_utils.get_mime_type(file_path)
            self.assertEqual(mime_type, expected_mime, f"Failed for {file_path}")

    def test_get_mime_type_unknown_extension(self):
        """Test get_mime_type with unknown file extension."""
        mime_type = file_utils.get_mime_type("file.unknown")
        self.assertEqual(mime_type, "application/octet-stream")

    def test_get_mime_type_no_extension(self):
        """Test get_mime_type with file that has no extension."""
        mime_type = file_utils.get_mime_type("file")
        self.assertEqual(mime_type, "application/octet-stream")
    # endregion

    # region Read File Tests
    def test_read_file_text_file(self):
        """Test read_file with a text file."""
        result = file_utils.read_file(self.test_text_file)
        self.assertEqual(result['content'], "Hello, World! This is a test file.")
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/plain')
        self.assertIsInstance(result['size_bytes'], int)

    def test_read_file_python_file(self):
        """Test read_file with a Python file."""
        result = file_utils.read_file(self.test_python_file)
        self.assertEqual(result['content'], 'print("Hello, Python!")')
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/x-python')

    def test_read_file_json_file(self):
        """Test read_file with a JSON file."""
        result = file_utils.read_file(self.test_json_file)
        self.assertEqual(result['content'], '{"key": "value", "number": 42}')
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'application/json')

    def test_read_file_binary_file(self):
        """Test read_file with a binary file."""
        result = file_utils.read_file(self.test_binary_file)
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['mime_type'], 'application/octet-stream')
        # Decode base64 and verify content
        decoded_content = base64.b64decode(result['content'])
        self.assertEqual(decoded_content, b'\x00\x01\x02\x03\x04\x05')

    def test_read_file_not_found(self):
        """Test read_file with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            file_utils.read_file("nonexistent_file.txt")

    def test_read_file_too_large(self):
        """Test read_file with file that exceeds size limit."""
        # Create a large file
        large_file = os.path.join(self.temp_dir, "large.txt")
        with open(large_file, 'w') as f:
            f.write("x" * (51 * 1024 * 1024))  # 51MB
        
        with self.assertRaises(ValueError) as cm:
            file_utils.read_file(large_file, max_size_mb=50)
        self.assertIn("File too large", str(cm.exception))

    def test_read_file_with_custom_size_limit(self):
        """Test read_file with custom size limit."""
        # Create a file that's just under the limit
        medium_file = os.path.join(self.temp_dir, "medium.txt")
        with open(medium_file, 'w') as f:
            f.write("x" * (10 * 1024 * 1024))  # 10MB
        
        result = file_utils.read_file(medium_file, max_size_mb=10)
        self.assertEqual(result['encoding'], 'text')

    @patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid utf-8'))
    def test_read_file_unicode_decode_error(self, mock_open):
        """Test read_file with Unicode decode error."""
        with self.assertRaises(ValueError) as cm:
            file_utils.read_file(self.test_text_file)
        self.assertIn("Could not decode file", str(cm.exception))

    def test_read_file_fallback_encodings(self):
        """Test read_file with fallback encodings by creating a file with non-UTF-8 content."""
        # Create a file with latin-1 encoding content
        latin1_file = os.path.join(self.temp_dir, "latin1.txt")
        latin1_content = "latin-1 content with special chars: ñáéíóú"
        
        # Write with latin-1 encoding
        with open(latin1_file, 'w', encoding='latin-1') as f:
            f.write(latin1_content)
        
        # Read with file_utils (should handle the encoding)
        result = file_utils.read_file(latin1_file)
        self.assertEqual(result['content'], latin1_content)
    # endregion

    # region Write File Tests
    def test_write_file_text_content(self):
        """Test write_file with text content."""
        output_file = os.path.join(self.temp_dir, "output.txt")
        content = "This is test content"
        
        file_utils.write_file(output_file, content, encoding='text')
        
        with open(output_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)

    def test_write_file_base64_content(self):
        """Test write_file with base64 content."""
        output_file = os.path.join(self.temp_dir, "output.bin")
        original_content = b'\x00\x01\x02\x03\x04\x05'
        base64_content = base64.b64encode(original_content).decode('utf-8')
        
        file_utils.write_file(output_file, base64_content, encoding='base64')
        
        with open(output_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, original_content)

    def test_write_file_bytes_content_base64(self):
        """Test write_file with bytes content and base64 encoding."""
        output_file = os.path.join(self.temp_dir, "output.bin")
        content = b'\x00\x01\x02\x03\x04\x05'
        
        file_utils.write_file(output_file, content, encoding='base64')
        
        with open(output_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)

    def test_write_file_bytes_content_text(self):
        """Test write_file with bytes content and text encoding."""
        output_file = os.path.join(self.temp_dir, "output.txt")
        content = b'Hello, World!'
        
        file_utils.write_file(output_file, content, encoding='text')
        
        with open(output_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, "Hello, World!")

    def test_write_file_creates_directories(self):
        """Test write_file creates directories if they don't exist."""
        output_file = os.path.join(self.temp_dir, "subdir", "nested", "output.txt")
        content = "Test content"
        
        file_utils.write_file(output_file, content, encoding='text')
        
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
    # endregion

    # region Base64 Encoding/Decoding Tests
    def test_encode_to_base64_string(self):
        """Test encode_to_base64 with string input."""
        text = "Hello, World!"
        result = file_utils.encode_to_base64(text)
        expected = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_encode_to_base64_bytes(self):
        """Test encode_to_base64 with bytes input."""
        data = b'\x00\x01\x02\x03\x04\x05'
        result = file_utils.encode_to_base64(data)
        expected = base64.b64encode(data).decode('utf-8')
        self.assertEqual(result, expected)

    def test_decode_from_base64(self):
        """Test decode_from_base64."""
        original_data = b'\x00\x01\x02\x03\x04\x05'
        base64_data = base64.b64encode(original_data).decode('utf-8')
        result = file_utils.decode_from_base64(base64_data)
        self.assertEqual(result, original_data)

    def test_text_to_base64(self):
        """Test text_to_base64."""
        text = "Hello, World!"
        result = file_utils.text_to_base64(text)
        expected = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_base64_to_text(self):
        """Test base64_to_text."""
        text = "Hello, World!"
        base64_data = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        result = file_utils.base64_to_text(base64_data)
        self.assertEqual(result, text)

    def test_base64_to_text_invalid_base64(self):
        """Test base64_to_text with invalid base64 data."""
        with self.assertRaises(Exception):  # binascii.Error or similar
            file_utils.base64_to_text("invalid_base64_data")
    # endregion

    # region File to Base64 Tests
    def test_file_to_base64(self):
        """Test file_to_base64."""
        result = file_utils.file_to_base64(self.test_binary_file)
        expected = base64.b64encode(b'\x00\x01\x02\x03\x04\x05').decode('utf-8')
        self.assertEqual(result, expected)

    def test_file_to_base64_text_file(self):
        """Test file_to_base64 with text file."""
        result = file_utils.file_to_base64(self.test_text_file)
        expected = base64.b64encode("Hello, World! This is a test file.".encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_file_to_base64_file_not_found(self):
        """Test file_to_base64 with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            file_utils.file_to_base64("nonexistent_file.txt")

    def test_base64_to_file(self):
        """Test base64_to_file."""
        original_data = b'\x00\x01\x02\x03\x04\x05'
        base64_data = base64.b64encode(original_data).decode('utf-8')
        output_file = os.path.join(self.temp_dir, "output.bin")
        
        file_utils.base64_to_file(base64_data, output_file)
        
        with open(output_file, 'rb') as f:
            written_data = f.read()
        self.assertEqual(written_data, original_data)

    def test_base64_to_file_creates_directories(self):
        """Test base64_to_file creates directories if they don't exist."""
        original_data = b'\x00\x01\x02\x03\x04\x05'
        base64_data = base64.b64encode(original_data).decode('utf-8')
        output_file = os.path.join(self.temp_dir, "subdir", "nested", "output.bin")
        
        file_utils.base64_to_file(base64_data, output_file)
        
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'rb') as f:
            written_data = f.read()
        self.assertEqual(written_data, original_data)

    def test_base64_to_file_invalid_base64(self):
        """Test base64_to_file with invalid base64 data."""
        output_file = os.path.join(self.temp_dir, "output.bin")
        with self.assertRaises(Exception):  # binascii.Error or similar
            file_utils.base64_to_file("invalid_base64_data", output_file)
    # endregion

    # region Edge Cases and Error Handling
    def test_read_file_empty_file(self):
        """Test read_file with empty file."""
        empty_file = os.path.join(self.temp_dir, "empty.txt")
        with open(empty_file, 'w') as f:
            pass  # Create empty file
        
        result = file_utils.read_file(empty_file)
        self.assertEqual(result['content'], "")
        self.assertEqual(result['encoding'], 'text')

    def test_write_file_empty_content(self):
        """Test write_file with empty content."""
        output_file = os.path.join(self.temp_dir, "empty_output.txt")
        file_utils.write_file(output_file, "", encoding='text')
        
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "")

    def test_encode_to_base64_empty_string(self):
        """Test encode_to_base64 with empty string."""
        result = file_utils.encode_to_base64("")
        expected = base64.b64encode("".encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_encode_to_base64_empty_bytes(self):
        """Test encode_to_base64 with empty bytes."""
        result = file_utils.encode_to_base64(b"")
        expected = base64.b64encode(b"").decode('utf-8')
        self.assertEqual(result, expected)

    def test_decode_from_base64_empty(self):
        """Test decode_from_base64 with empty base64."""
        result = file_utils.decode_from_base64("")
        self.assertEqual(result, b"")

    def test_file_to_base64_empty_file(self):
        """Test file_to_base64 with empty file."""
        empty_file = os.path.join(self.temp_dir, "empty.bin")
        with open(empty_file, 'wb') as f:
            pass  # Create empty binary file
        
        result = file_utils.file_to_base64(empty_file)
        expected = base64.b64encode(b"").decode('utf-8')
        self.assertEqual(result, expected)

    def test_base64_to_file_empty_base64(self):
        """Test base64_to_file with empty base64."""
        output_file = os.path.join(self.temp_dir, "empty_output.bin")
        file_utils.base64_to_file("", output_file)
        
        with open(output_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b"")

    def test_read_file_special_characters(self):
        """Test read_file with special characters in content."""
        special_file = os.path.join(self.temp_dir, "special.txt")
        special_content = "Hello\nWorld\tTest\nUnicode: 🚀🎉"  # Use \n instead of \r\n for consistency
        with open(special_file, 'w', encoding='utf-8') as f:
            f.write(special_content)
        
        result = file_utils.read_file(special_file)
        self.assertEqual(result['content'], special_content)

    def test_write_file_special_characters(self):
        """Test write_file with special characters."""
        output_file = os.path.join(self.temp_dir, "special_output.txt")
        special_content = "Hello\nWorld\tTest\nUnicode: 🚀🎉"  # Use \n instead of \r\n for consistency
        
        file_utils.write_file(output_file, special_content, encoding='text')
        
        with open(output_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, special_content)
    # endregion

    # region Integration Tests
    def test_full_text_file_workflow(self):
        """Test complete workflow for text file: read -> encode -> decode -> write."""
        # Read original file
        original_result = file_utils.read_file(self.test_text_file)
        original_content = original_result['content']
        
        # Encode to base64
        base64_content = file_utils.text_to_base64(original_content)
        
        # Decode from base64
        decoded_content = file_utils.base64_to_text(base64_content)
        
        # Write to new file
        output_file = os.path.join(self.temp_dir, "workflow_output.txt")
        file_utils.write_file(output_file, decoded_content, encoding='text')
        
        # Verify
        with open(output_file, 'r', encoding='utf-8') as f:
            final_content = f.read()
        self.assertEqual(final_content, original_content)

    def test_full_binary_file_workflow(self):
        """Test complete workflow for binary file: read -> encode -> decode -> write."""
        # Read original file
        original_result = file_utils.read_file(self.test_binary_file)
        original_base64 = original_result['content']
        
        # Decode base64 to get original bytes
        original_bytes = file_utils.decode_from_base64(original_base64)
        
        # Encode back to base64
        new_base64 = file_utils.encode_to_base64(original_bytes)
        
        # Write to new file
        output_file = os.path.join(self.temp_dir, "workflow_output.bin")
        file_utils.base64_to_file(new_base64, output_file)
        
        # Verify
        with open(output_file, 'rb') as f:
            final_bytes = f.read()
        self.assertEqual(final_bytes, original_bytes)

    def test_cross_platform_file_operations(self):
        """Test file operations work across different platforms."""
        # Test with different path separators
        test_content = "Cross-platform test"
        
        # Unix-style path
        unix_path = os.path.join(self.temp_dir, "folder", "file.txt")
        file_utils.write_file(unix_path, test_content, encoding='text')
        result = file_utils.read_file(unix_path)
        self.assertEqual(result['content'], test_content)
        
        # Windows-style path (if on Windows)
        if os.name == 'nt':
            windows_path = os.path.join(self.temp_dir, "folder2", "file.txt").replace('/', '\\')
            file_utils.write_file(windows_path, test_content, encoding='text')
            result = file_utils.read_file(windows_path)
            self.assertEqual(result['content'], test_content)
    # endregion


if __name__ == "__main__":
    unittest.main()
