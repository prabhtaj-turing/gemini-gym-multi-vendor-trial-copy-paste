"""
Unit tests for file utility functions in Google Docs API simulation.

This module tests all file handling utility functions including file type detection,
reading/writing, encoding/decoding, and base64 operations.
"""

import unittest
import os
import tempfile
import base64
from unittest.mock import patch, MagicMock

from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_docs.SimulationEngine.file_utils import (
    is_text_file, is_binary_file, get_mime_type,
    read_file, write_file, encode_to_base64, decode_from_base64,
    text_to_base64, base64_to_text, file_to_base64, base64_to_file
)


class TestGoogleDocsFileUtils(BaseTestCaseWithErrorHandler):
    """Test suite for file utility functions."""

    def setUp(self):
        """Set up test environment with temporary test files."""
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Text file
        self.text_file_path = os.path.join(self.temp_dir, "test.txt")
        with open(self.text_file_path, 'w', encoding='utf-8') as f:
            f.write("Hello, World! This is a test text file.")
        
        # Binary file (create a simple binary file)
        self.binary_file_path = os.path.join(self.temp_dir, "test.bin")
        with open(self.binary_file_path, 'wb') as f:
            f.write(b"\x00\x01\x02\x03\x04\x05")
        
        # JSON file
        self.json_file_path = os.path.join(self.temp_dir, "test.json")
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            f.write('{"key": "value", "number": 42}')
        
        # Large file for size testing
        self.large_file_path = os.path.join(self.temp_dir, "large.txt")
        large_content = "x" * (51 * 1024 * 1024)  # 51MB
        with open(self.large_file_path, 'w', encoding='utf-8') as f:
            f.write(large_content)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_is_text_file(self):
        """Test is_text_file function."""
        self.assertTrue(is_text_file(self.text_file_path))
        self.assertTrue(is_text_file(self.json_file_path))
        self.assertFalse(is_text_file(self.binary_file_path))
        # Test with non-existent file - extension-based check, not file existence
        self.assertTrue(is_text_file("non_existent_file.txt"))
        self.assertFalse(is_text_file("non_existent_file.bin"))

    def test_is_binary_file(self):
        """Test is_binary_file function."""
        self.assertFalse(is_binary_file(self.text_file_path))
        self.assertFalse(is_binary_file(self.json_file_path))
        self.assertTrue(is_binary_file(self.binary_file_path))
        # Test with non-existent file - extension-based check, not file existence
        self.assertTrue(is_binary_file("non_existent_file.jpg"))
        self.assertFalse(is_binary_file("non_existent_file.txt"))

    def test_get_mime_type(self):
        """Test get_mime_type function."""
        self.assertEqual(get_mime_type(self.text_file_path), "text/plain")
        self.assertEqual(get_mime_type(self.json_file_path), "application/json")
        self.assertEqual(get_mime_type(self.binary_file_path), "application/octet-stream")
        # Test with non-existent file
        self.assertEqual(get_mime_type("non_existent.txt"), "text/plain")

    def test_read_file_text(self):
        """Test read_file function with text file."""
        result = read_file(self.text_file_path)
        
        self.assertIn("content", result)
        self.assertIn("encoding", result)
        self.assertIn("mime_type", result)
        self.assertIn("size_bytes", result)
        
        self.assertEqual(result["content"], "Hello, World! This is a test text file.")
        self.assertEqual(result["encoding"], "text")
        self.assertEqual(result["mime_type"], "text/plain")
        self.assertIsInstance(result["size_bytes"], int)

    def test_read_file_binary(self):
        """Test read_file function with binary file."""
        result = read_file(self.binary_file_path)
        
        self.assertIn("content", result)
        self.assertIn("encoding", result)
        self.assertIn("mime_type", result)
        self.assertIn("size_bytes", result)
        
        self.assertEqual(result["encoding"], "base64")
        self.assertEqual(result["mime_type"], "application/octet-stream")
        self.assertIsInstance(result["size_bytes"], int)
        
        # Verify base64 content can be decoded
        decoded_content = base64.b64decode(result["content"])
        self.assertEqual(decoded_content, b"\x00\x01\x02\x03\x04\x05")

    def test_read_file_large_file_error(self):
        """Test read_file function with file too large."""
        with self.assertRaises(ValueError):
            read_file(self.large_file_path, max_size_mb=50)

    def test_read_file_nonexistent(self):
        """Test read_file function with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            read_file("non_existent_file.txt")

    def test_write_file_text(self):
        """Test write_file function with text content."""
        test_file_path = os.path.join(self.temp_dir, "write_test.txt")
        test_content = "This is test content for writing"
        
        write_file(test_file_path, test_content, encoding="text")
        
        # Verify file was written
        self.assertTrue(os.path.exists(test_file_path))
        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_write_file_base64(self):
        """Test write_file function with base64 content."""
        test_file_path = os.path.join(self.temp_dir, "write_test.bin")
        test_content = base64.b64encode(b"Binary test content").decode('utf-8')
        
        write_file(test_file_path, test_content, encoding="base64")
        
        # Verify file was written
        self.assertTrue(os.path.exists(test_file_path))
        with open(test_file_path, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b"Binary test content")

    def test_write_file_bytes_content(self):
        """Test write_file function with bytes content."""
        test_file_path = os.path.join(self.temp_dir, "write_test_bytes.txt")
        test_content = b"Bytes test content"
        
        write_file(test_file_path, test_content, encoding="text")
        
        # Verify file was written
        self.assertTrue(os.path.exists(test_file_path))
        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, "Bytes test content")

    def test_encode_to_base64_string(self):
        """Test encode_to_base64 function with string input."""
        test_string = "Hello, World!"
        result = encode_to_base64(test_string)
        
        # Verify result is base64 encoded
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, test_string)

    def test_encode_to_base64_bytes(self):
        """Test encode_to_base64 function with bytes input."""
        test_bytes = b"Hello, World!"
        result = encode_to_base64(test_bytes)
        
        # Verify result is base64 encoded
        decoded = base64.b64decode(result)
        self.assertEqual(decoded, test_bytes)

    def test_decode_from_base64(self):
        """Test decode_from_base64 function."""
        test_string = "Hello, World!"
        encoded = base64.b64encode(test_string.encode('utf-8')).decode('utf-8')
        
        result = decode_from_base64(encoded)
        
        # Verify result is decoded correctly
        self.assertEqual(result.decode('utf-8'), test_string)

    def test_text_to_base64(self):
        """Test text_to_base64 function."""
        test_text = "Test text content"
        result = text_to_base64(test_text)
        
        # Verify result is base64 encoded
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, test_text)

    def test_base64_to_text(self):
        """Test base64_to_text function."""
        test_text = "Test text content"
        encoded = base64.b64encode(test_text.encode('utf-8')).decode('utf-8')
        
        result = base64_to_text(encoded)
        
        # Verify result is decoded correctly
        self.assertEqual(result, test_text)

    def test_file_to_base64(self):
        """Test file_to_base64 function."""
        result = file_to_base64(self.text_file_path)
        
        # Verify result is base64 encoded
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, "Hello, World! This is a test text file.")

    def test_base64_to_file(self):
        """Test base64_to_file function."""
        test_file_path = os.path.join(self.temp_dir, "base64_test.txt")
        test_content = "Base64 test content"
        encoded = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        base64_to_file(encoded, test_file_path)
        
        # Verify file was written
        self.assertTrue(os.path.exists(test_file_path))
        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_file_operations_with_different_encodings(self):
        """Test file operations with different text encodings."""
        # Test with Latin-1 encoding
        latin1_file = os.path.join(self.temp_dir, "latin1.txt")
        latin1_content = "Café résumé naïve"
        
        with open(latin1_file, 'w', encoding='latin-1') as f:
            f.write(latin1_content)
        
        # Read the file
        result = read_file(latin1_file)
        self.assertEqual(result["content"], latin1_content)
        self.assertEqual(result["encoding"], "text")

    def test_directory_creation(self):
        """Test that write_file creates directories as needed."""
        nested_dir = os.path.join(self.temp_dir, "nested", "subdir")
        test_file_path = os.path.join(nested_dir, "test.txt")
        test_content = "Test content"
        
        write_file(test_file_path, test_content)
        
        # Verify directory was created and file was written
        self.assertTrue(os.path.exists(test_file_path))
        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, test_content)


if __name__ == "__main__":
    unittest.main()
