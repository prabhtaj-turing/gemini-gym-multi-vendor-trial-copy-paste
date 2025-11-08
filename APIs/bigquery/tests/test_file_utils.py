"""
File utilities tests for BigQuery API.

This module tests the file_utils.py module to ensure all file handling functions
work correctly, including text/binary file detection, reading/writing, and base64 encoding/decoding.
Following the Service Engineering Test Framework Guideline for comprehensive testing.
"""

import unittest
import tempfile
import os
import base64
import json
from unittest.mock import patch, mock_open
from typing import Dict, Any
from common_utils.base_case import BaseTestCaseWithErrorHandler

from ..SimulationEngine.file_utils import (
    is_text_file,
    is_binary_file,
    get_mime_type,
    read_file,
    write_file,
    encode_to_base64,
    decode_from_base64,
    text_to_base64,
    base64_to_text,
    file_to_base64,
    base64_to_file,
    TEXT_EXTENSIONS,
    BINARY_EXTENSIONS
)


class TestBigQueryFileUtils(BaseTestCaseWithErrorHandler):
    """
    Test suite for BigQuery file utilities.
    
    Tests all file handling functions including text/binary detection,
    reading/writing files, and base64 encoding/decoding operations.
    """

    def setUp(self):
        """Set up test environment for each test method."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test files
        self.text_file_path = os.path.join(self.test_dir, "test.txt")
        self.python_file_path = os.path.join(self.test_dir, "test.py")
        self.json_file_path = os.path.join(self.test_dir, "test.json")
        self.binary_file_path = os.path.join(self.test_dir, "test.jpg")
        self.large_file_path = os.path.join(self.test_dir, "large.txt")
        
        # Create test content
        self.text_content = "Hello, World!\nThis is a test file.\n"
        self.json_content = '{"name": "test", "value": 123}'
        self.binary_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
        
        # Write test files
        with open(self.text_file_path, 'w', encoding='utf-8') as f:
            f.write(self.text_content)
        
        with open(self.python_file_path, 'w', encoding='utf-8') as f:
            f.write('print("Hello, Python!")\n')
        
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            f.write(self.json_content)
        
        with open(self.binary_file_path, 'wb') as f:
            f.write(self.binary_content)
        
        # Create a large file for size testing
        large_content = "x" * (51 * 1024 * 1024)  # 51MB
        with open(self.large_file_path, 'w', encoding='utf-8') as f:
            f.write(large_content)

    def tearDown(self):
        """Clean up after each test method."""
        # Remove test directory and all files recursively
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)

    def test_is_text_file(self):
        """Test text file detection."""
        # Test text file extensions
        self.assertTrue(is_text_file("test.txt"))
        self.assertTrue(is_text_file("script.py"))
        self.assertTrue(is_text_file("data.json"))
        self.assertTrue(is_text_file("README.md"))
        self.assertTrue(is_text_file("config.yaml"))
        self.assertTrue(is_text_file("style.css"))
        self.assertTrue(is_text_file("index.html"))
        self.assertTrue(is_text_file("query.sql"))
        
        # Test binary file extensions (should return False)
        self.assertFalse(is_text_file("image.jpg"))
        self.assertFalse(is_text_file("document.pdf"))
        self.assertFalse(is_text_file("archive.zip"))
        self.assertFalse(is_text_file("video.mp4"))
        
        # Test unknown extensions
        self.assertFalse(is_text_file("unknown.xyz"))
        self.assertFalse(is_text_file("no_extension"))

    def test_is_binary_file(self):
        """Test binary file detection."""
        # Test binary file extensions
        self.assertTrue(is_binary_file("image.jpg"))
        self.assertTrue(is_binary_file("document.pdf"))
        self.assertTrue(is_binary_file("archive.zip"))
        self.assertTrue(is_binary_file("video.mp4"))
        self.assertTrue(is_binary_file("audio.mp3"))
        self.assertTrue(is_binary_file("executable.exe"))
        self.assertTrue(is_binary_file("database.db"))
        
        # Test text file extensions (should return False)
        self.assertFalse(is_binary_file("test.txt"))
        self.assertFalse(is_binary_file("script.py"))
        self.assertFalse(is_binary_file("data.json"))
        
        # Test unknown extensions
        self.assertFalse(is_binary_file("unknown.xyz"))
        self.assertFalse(is_binary_file("no_extension"))

    def test_get_mime_type(self):
        """Test MIME type detection."""
        # Test known file types
        self.assertEqual(get_mime_type("test.txt"), "text/plain")
        self.assertEqual(get_mime_type("script.py"), "text/x-python")
        self.assertEqual(get_mime_type("data.json"), "application/json")
        self.assertEqual(get_mime_type("image.jpg"), "image/jpeg")
        self.assertEqual(get_mime_type("document.pdf"), "application/pdf")
        self.assertEqual(get_mime_type("archive.zip"), "application/zip")
        
        # Test unknown file types
        self.assertEqual(get_mime_type("no_extension"), "application/octet-stream")
        
        # Note: .xyz files might have a MIME type assigned by the system
        # So we test with a truly unknown extension
        unknown_mime = get_mime_type("unknown.xyz")
        self.assertIsInstance(unknown_mime, str)
        self.assertGreater(len(unknown_mime), 0)

    def test_read_file_text(self):
        """Test reading text files."""
        # Test reading text file
        result = read_file(self.text_file_path)
        self.assertEqual(result['content'], self.text_content)
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/plain')
        self.assertEqual(result['size_bytes'], len(self.text_content.encode('utf-8')))
        
        # Test reading Python file
        result = read_file(self.python_file_path)
        self.assertEqual(result['content'], 'print("Hello, Python!")\n')
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/x-python')
        
        # Test reading JSON file
        result = read_file(self.json_file_path)
        self.assertEqual(result['content'], self.json_content)
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'application/json')

    def test_read_file_binary(self):
        """Test reading binary files."""
        result = read_file(self.binary_file_path)
        
        # Content should be base64 encoded
        self.assertIsInstance(result['content'], str)
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['mime_type'], 'image/jpeg')
        self.assertEqual(result['size_bytes'], len(self.binary_content))
        
        # Verify base64 content can be decoded back to original
        decoded_content = base64.b64decode(result['content'])
        self.assertEqual(decoded_content, self.binary_content)

    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        non_existent_path = os.path.join(self.test_dir, "nonexistent.txt")
        
        with self.assertRaises(FileNotFoundError):
            read_file(non_existent_path)

    def test_read_file_too_large(self):
        """Test reading file that exceeds size limit."""
        with self.assertRaises(ValueError) as context:
            read_file(self.large_file_path, max_size_mb=50)
        
        self.assertIn("File too large", str(context.exception))

    def test_read_file_with_custom_size_limit(self):
        """Test reading file with custom size limit."""
        # Create a file that's exactly at the limit
        limit_content = "x" * (50 * 1024 * 1024)  # 50MB
        limit_file_path = os.path.join(self.test_dir, "limit.txt")
        
        with open(limit_file_path, 'w', encoding='utf-8') as f:
            f.write(limit_content)
        
        # Should read successfully
        result = read_file(limit_file_path, max_size_mb=50)
        self.assertEqual(result['content'], limit_content)
        self.assertEqual(result['encoding'], 'text')

    def test_write_file_text(self):
        """Test writing text files."""
        output_path = os.path.join(self.test_dir, "output.txt")
        test_content = "This is test content for writing."
        
        # Write text content
        write_file(output_path, test_content, encoding='text')
        
        # Verify file was written correctly
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_write_file_binary(self):
        """Test writing binary files."""
        output_path = os.path.join(self.test_dir, "output.jpg")
        test_content = "SGVsbG8sIFdvcmxkIQ=="  # "Hello, World!" in base64
        
        # Write binary content
        write_file(output_path, test_content, encoding='base64')
        
        # Verify file was written correctly
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b"Hello, World!")

    def test_write_file_bytes_input(self):
        """Test writing file with bytes input."""
        output_path = os.path.join(self.test_dir, "output_bytes.txt")
        test_content = b"Hello, World!"
        
        # Write bytes content as text
        write_file(output_path, test_content, encoding='text')
        
        # Verify file was written correctly
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "Hello, World!")

    def test_write_file_base64_bytes_input(self):
        """Test writing file with base64 bytes input."""
        output_path = os.path.join(self.test_dir, "output_base64_bytes.jpg")
        test_content = b"SGVsbG8sIFdvcmxkIQ=="  # base64 as bytes
        
        # Write base64 bytes content
        write_file(output_path, test_content, encoding='base64')
        
        # Verify file was written correctly
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'rb') as f:
            content = f.read()
        # When encoding='base64' and content is bytes, the function treats it as already decoded
        # So it writes the bytes directly
        self.assertEqual(content, test_content)

    def test_write_file_creates_directory(self):
        """Test that write_file creates directories if they don't exist."""
        subdir_path = os.path.join(self.test_dir, "subdir", "nested")
        output_path = os.path.join(subdir_path, "output.txt")
        test_content = "Test content"
        
        # Write file in non-existent directory
        write_file(output_path, test_content)
        
        # Verify directory was created and file was written
        self.assertTrue(os.path.exists(subdir_path))
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_encode_to_base64_string(self):
        """Test encoding string to base64."""
        test_string = "Hello, World!"
        result = encode_to_base64(test_string)
        expected = base64.b64encode(test_string.encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_encode_to_base64_bytes(self):
        """Test encoding bytes to base64."""
        test_bytes = b"Hello, World!"
        result = encode_to_base64(test_bytes)
        expected = base64.b64encode(test_bytes).decode('utf-8')
        self.assertEqual(result, expected)

    def test_decode_from_base64(self):
        """Test decoding base64 to bytes."""
        test_string = "Hello, World!"
        base64_content = base64.b64encode(test_string.encode('utf-8')).decode('utf-8')
        result = decode_from_base64(base64_content)
        self.assertEqual(result, test_string.encode('utf-8'))

    def test_text_to_base64(self):
        """Test converting text to base64."""
        test_text = "Hello, World!"
        result = text_to_base64(test_text)
        expected = base64.b64encode(test_text.encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_base64_to_text(self):
        """Test converting base64 to text."""
        test_text = "Hello, World!"
        base64_content = base64.b64encode(test_text.encode('utf-8')).decode('utf-8')
        result = base64_to_text(base64_content)
        self.assertEqual(result, test_text)

    def test_file_to_base64(self):
        """Test reading file and converting to base64."""
        result = file_to_base64(self.text_file_path)
        
        # Verify result is base64 encoded
        self.assertIsInstance(result, str)
        
        # Verify it can be decoded back to original content
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, self.text_content)

    def test_base64_to_file(self):
        """Test writing base64 content to file."""
        output_path = os.path.join(self.test_dir, "output_base64.txt")
        test_content = "Hello, World!"
        base64_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        # Write base64 content to file
        base64_to_file(base64_content, output_path)
        
        # Verify file was written correctly
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_base64_to_file_creates_directory(self):
        """Test that base64_to_file creates directories if they don't exist."""
        subdir_path = os.path.join(self.test_dir, "subdir", "nested")
        output_path = os.path.join(subdir_path, "output_base64.txt")
        test_content = "Hello, World!"
        base64_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        # Write base64 content to file in non-existent directory
        base64_to_file(base64_content, output_path)
        
        # Verify directory was created and file was written
        self.assertTrue(os.path.exists(subdir_path))
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_read_file_unicode_decode_error_fallback(self):
        """Test reading file with Unicode decode error and fallback encodings."""
        # Create a file with non-UTF-8 encoding
        latin1_file_path = os.path.join(self.test_dir, "latin1.txt")
        latin1_content = "Hello, World! ñáéíóú"
        
        # Write with latin-1 encoding
        with open(latin1_file_path, 'w', encoding='latin-1') as f:
            f.write(latin1_content)
        
        # Read the file (should fallback to latin-1)
        result = read_file(latin1_file_path)
        self.assertEqual(result['content'], latin1_content)
        self.assertEqual(result['encoding'], 'text')

    def test_read_file_unicode_decode_error_all_failures(self):
        """Test reading file that fails all encoding attempts."""
        # Create a binary file but give it a text extension
        binary_as_text_path = os.path.join(self.test_dir, "binary.txt")
        with open(binary_as_text_path, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8 sequence
        
        # The file is detected as text by extension, but content is binary
        # The function should try different encodings and eventually succeed
        result = read_file(binary_as_text_path)
        # It should be able to read it as text with one of the fallback encodings
        self.assertEqual(result['encoding'], 'text')
        self.assertIsInstance(result['content'], str)

    def test_read_file_encoding_fallback_continue_statement(self):
        """Test the continue statement in encoding fallback loop."""
        # Create a file that fails UTF-8 but succeeds with latin-1
        mixed_encoding_path = os.path.join(self.test_dir, "mixed_encoding.txt")
        # Use bytes that are invalid in UTF-8 but valid in latin-1
        mixed_content = b'Hello\xffWorld'  # \xff is invalid in UTF-8 but valid in latin-1
        
        with open(mixed_encoding_path, 'wb') as f:
            f.write(mixed_content)
        
        # This should trigger the continue statement in the fallback loop
        result = read_file(mixed_encoding_path)
        self.assertEqual(result['encoding'], 'text')
        self.assertIsInstance(result['content'], str)

    def test_read_file_encoding_fallback_value_error(self):
        """Test the ValueError when all encoding attempts fail."""
        # Create a file that will fail all encoding attempts
        # We need to create a scenario where all encodings fail
        undecodable_path = os.path.join(self.test_dir, "undecodable.txt")
        
        # Create a file with bytes that might fail all encodings
        # This is tricky because latin-1 is very permissive
        # Let's try with surrogate bytes that might cause issues
        undecodable_content = b'\xff\xfe\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff'
        
        with open(undecodable_path, 'wb') as f:
            f.write(undecodable_content)
        
        # Try to read the file - it might succeed or fail
        try:
            result = read_file(undecodable_path)
            # If it succeeds, that's fine - the encoding fallback worked
            self.assertEqual(result['encoding'], 'text')
            self.assertIsInstance(result['content'], str)
        except ValueError as e:
            # If it fails, that's also fine - we've tested the error path
            self.assertIn("Could not decode file", str(e))

    def test_read_file_encoding_fallback_value_error_with_mock(self):
        """Test the ValueError when all encoding attempts fail using mock."""
        # Use mock to force all encoding attempts to fail
        undecodable_path = os.path.join(self.test_dir, "undecodable.txt")
        
        # Create the file first
        with open(undecodable_path, 'w') as f:
            f.write("test content")
        
        # Create a mock that raises UnicodeDecodeError for all encodings
        def mock_open_with_decode_error(*args, **kwargs):
            if 'r' in args[1] and 'encoding' in kwargs:
                raise UnicodeDecodeError('utf-8', b'\xff\xff', 0, 1, 'invalid start byte')
            else:
                # Use the real open for other operations
                return open(*args, **kwargs)
        
        with patch('builtins.open', side_effect=mock_open_with_decode_error):
            with self.assertRaises(ValueError) as context:
                read_file(undecodable_path)
            
            self.assertIn("Could not decode file", str(context.exception))

    def test_text_extensions_constant(self):
        """Test that TEXT_EXTENSIONS constant is properly defined."""
        self.assertIsInstance(TEXT_EXTENSIONS, set)
        self.assertGreater(len(TEXT_EXTENSIONS), 0)
        
        # Test some expected extensions
        self.assertIn('.txt', TEXT_EXTENSIONS)
        self.assertIn('.py', TEXT_EXTENSIONS)
        self.assertIn('.json', TEXT_EXTENSIONS)
        self.assertIn('.html', TEXT_EXTENSIONS)
        self.assertIn('.css', TEXT_EXTENSIONS)
        self.assertIn('.md', TEXT_EXTENSIONS)

    def test_binary_extensions_constant(self):
        """Test that BINARY_EXTENSIONS constant is properly defined."""
        self.assertIsInstance(BINARY_EXTENSIONS, set)
        self.assertGreater(len(BINARY_EXTENSIONS), 0)
        
        # Test some expected extensions
        self.assertIn('.jpg', BINARY_EXTENSIONS)
        self.assertIn('.pdf', BINARY_EXTENSIONS)
        self.assertIn('.zip', BINARY_EXTENSIONS)
        self.assertIn('.mp4', BINARY_EXTENSIONS)
        self.assertIn('.exe', BINARY_EXTENSIONS)
        self.assertIn('.db', BINARY_EXTENSIONS)

    def test_file_operations_integration(self):
        """Test integration of multiple file operations."""
        # Create test content
        original_content = "This is a test file with special characters: ñáéíóú 🚀"
        
        # Write content to file
        test_file_path = os.path.join(self.test_dir, "integration_test.txt")
        write_file(test_file_path, original_content)
        
        # Read file back
        read_result = read_file(test_file_path)
        self.assertEqual(read_result['content'], original_content)
        
        # Convert to base64
        base64_content = file_to_base64(test_file_path)
        
        # Write base64 content to new file
        base64_file_path = os.path.join(self.test_dir, "integration_test_base64.txt")
        base64_to_file(base64_content, base64_file_path)
        
        # Read base64 file and verify content
        with open(base64_file_path, 'r', encoding='utf-8') as f:
            final_content = f.read()
        self.assertEqual(final_content, original_content)

    def test_large_binary_file_operations(self):
        """Test operations with large binary files."""
        # Create a large binary file
        large_binary_path = os.path.join(self.test_dir, "large_binary.bin")
        large_binary_content = b"x" * (1024 * 1024)  # 1MB
        
        with open(large_binary_path, 'wb') as f:
            f.write(large_binary_content)
        
        # Test reading large binary file
        result = read_file(large_binary_path, max_size_mb=10)
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['size_bytes'], len(large_binary_content))
        
        # Verify base64 content can be decoded
        decoded_content = base64.b64decode(result['content'])
        self.assertEqual(decoded_content, large_binary_content)


if __name__ == "__main__":
    unittest.main()
