#!/usr/bin/env python3
"""
Test cases for the phone API file utility functions.
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import the modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from APIs.phone.SimulationEngine.file_utils import (
    is_text_file, is_binary_file, get_mime_type, validate_file_type,
    generate_attachment_id, calculate_checksum, read_file, write_file,
    encode_to_base64, decode_from_base64, text_to_base64, base64_to_text,
    file_to_base64, base64_to_file, encode_file_to_base64, decode_base64_to_file
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestPhoneFileUtils(BaseTestCaseWithErrorHandler):
    """Test cases for phone API file utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test files
        self.text_file_path = os.path.join(self.test_dir, "test.txt")
        self.binary_file_path = os.path.join(self.test_dir, "test.bin")
        self.json_file_path = os.path.join(self.test_dir, "test.json")
        
        # Create a text file
        with open(self.text_file_path, "w", encoding="utf-8") as f:
            f.write("Hello, World! This is a test text file.")
        
        # Create a binary file
        with open(self.binary_file_path, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")
        
        # Create a JSON file
        with open(self.json_file_path, "w", encoding="utf-8") as f:
            f.write('{"test": "data", "number": 42}')

    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary directory and files
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_is_text_file(self):
        """Test is_text_file function."""
        # Test with text file
        self.assertTrue(is_text_file(self.text_file_path))
        
        # Test with binary file
        self.assertFalse(is_text_file(self.binary_file_path))
        
        # Test with non-existent file - extension-based check, not file existence
        self.assertTrue(is_text_file("non_existent_file.txt"))  # .txt is a text extension
        self.assertFalse(is_text_file("non_existent_file.bin"))  # .bin is not a text extension

    def test_is_binary_file(self):
        """Test is_binary_file function."""
        # Test with binary file
        self.assertTrue(is_binary_file(self.binary_file_path))
        
        # Test with text file
        self.assertFalse(is_binary_file(self.text_file_path))
        
        # Test with non-existent file - extension-based check, not file existence
        self.assertTrue(is_binary_file("non_existent_file.bin"))  # .bin is a binary extension
        self.assertFalse(is_binary_file("non_existent_file.txt"))  # .txt is not a binary extension

    def test_get_mime_type(self):
        """Test get_mime_type function."""
        # Test with text file
        mime_type = get_mime_type(self.text_file_path)
        self.assertIsInstance(mime_type, str)
        self.assertIn("text", mime_type)
        
        # Test with JSON file
        mime_type = get_mime_type(self.json_file_path)
        self.assertIsInstance(mime_type, str)
        self.assertIn("json", mime_type)

    def test_validate_file_type(self):
        """Test validate_file_type function."""
        # Test with valid text file
        self.assertTrue(validate_file_type(self.text_file_path))
        
        # Test with valid JSON file
        self.assertTrue(validate_file_type(self.json_file_path))
        
        # Test with binary file (should pass validation as it's in BINARY_EXTENSIONS)
        self.assertTrue(validate_file_type(self.binary_file_path))

    def test_generate_attachment_id(self):
        """Test generate_attachment_id function."""
        # Test default prefix
        attachment_id = generate_attachment_id()
        self.assertIsInstance(attachment_id, str)
        self.assertTrue(attachment_id.startswith("att"))
        
        # Test custom prefix
        attachment_id = generate_attachment_id("file")
        self.assertIsInstance(attachment_id, str)
        self.assertTrue(attachment_id.startswith("file"))

    def test_calculate_checksum(self):
        """Test calculate_checksum function."""
        # Test with text data
        text_data = b"Hello, World!"
        checksum = calculate_checksum(text_data)
        self.assertIsInstance(checksum, str)
        self.assertTrue(checksum.startswith("sha256:"))
        # SHA-256 hash is 64 chars, plus "sha256:" prefix = 71 chars
        self.assertEqual(len(checksum), 71)
        
        # Test with binary data
        binary_data = b"\x00\x01\x02\x03\x04\x05"
        checksum = calculate_checksum(binary_data)
        self.assertIsInstance(checksum, str)
        self.assertTrue(checksum.startswith("sha256:"))
        self.assertEqual(len(checksum), 71)

    def test_read_file(self):
        """Test read_file function."""
        # Test reading text file
        result = read_file(self.text_file_path)
        self.assertIsInstance(result, dict)
        self.assertIn("content", result)
        self.assertIn("encoding", result)
        self.assertIn("mime_type", result)
        self.assertIn("size_bytes", result)
        self.assertIn("Hello, World!", result["content"])
        
        # Test reading JSON file
        result = read_file(self.json_file_path)
        self.assertIsInstance(result, dict)
        self.assertIn("content", result)
        self.assertIn("test", result["content"])

    def test_write_file(self):
        """Test write_file function."""
        # Test writing text file
        test_content = "This is a test content for write_file"
        test_file_path = os.path.join(self.test_dir, "write_test.txt")
        
        write_file(test_file_path, test_content, encoding="text")
        
        # Verify file was created and contains content
        self.assertTrue(os.path.exists(test_file_path))
        with open(test_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, test_content)

    def test_encode_to_base64(self):
        """Test encode_to_base64 function."""
        # Test with string
        text = "Hello, World!"
        encoded = encode_to_base64(text)
        self.assertIsInstance(encoded, str)
        self.assertNotEqual(encoded, text)
        
        # Test with bytes
        data = b"Binary data"
        encoded = encode_to_base64(data)
        self.assertIsInstance(encoded, str)

    def test_decode_from_base64(self):
        """Test decode_from_base64 function."""
        # Test with base64 encoded string
        original_text = "Hello, World!"
        encoded = encode_to_base64(original_text)
        decoded = decode_from_base64(encoded)
        self.assertEqual(decoded, original_text.encode())

    def test_text_to_base64(self):
        """Test text_to_base64 function."""
        text = "Test text for base64 encoding"
        encoded = text_to_base64(text)
        self.assertIsInstance(encoded, str)
        self.assertNotEqual(encoded, text)

    def test_base64_to_text(self):
        """Test base64_to_text function."""
        text = "Test text for base64 encoding"
        encoded = text_to_base64(text)
        decoded = base64_to_text(encoded)
        self.assertEqual(decoded, text)

    def test_file_to_base64(self):
        """Test file_to_base64 function."""
        # Test with text file
        encoded = file_to_base64(self.text_file_path)
        self.assertIsInstance(encoded, str)
        self.assertNotEqual(encoded, "")

    def test_base64_to_file(self):
        """Test base64_to_file function."""
        # Test with text file
        original_content = "Original content for base64 test"
        test_file_path = os.path.join(self.test_dir, "base64_test.txt")
        
        # Write original content
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(original_content)
        
        # Encode to base64
        encoded = file_to_base64(test_file_path)
        
        # Decode to new file
        new_file_path = os.path.join(self.test_dir, "base64_decoded.txt")
        base64_to_file(encoded, new_file_path)
        
        # Verify content
        self.assertTrue(os.path.exists(new_file_path))
        with open(new_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, original_content)

    def test_encode_file_to_base64(self):
        """Test encode_file_to_base64 function."""
        # Test with text file
        result = encode_file_to_base64(self.text_file_path)
        self.assertIsInstance(result, dict)
        self.assertIn("filename", result)
        self.assertIn("fileSize", result)
        self.assertIn("mimeType", result)
        self.assertIn("data", result)
        self.assertIn("checksum", result)
        self.assertIn("uploadDate", result)
        self.assertIn("encoding", result)

    def test_decode_base64_to_file(self):
        """Test decode_base64_to_file function."""
        # Test with text file
        original_content = "Content for decode test"
        test_file_path = os.path.join(self.test_dir, "decode_test.txt")
        
        # Write original content
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(original_content)
        
        # Encode to base64
        encoded_result = encode_file_to_base64(test_file_path)
        
        # Decode to new file
        new_file_path = os.path.join(self.test_dir, "decode_decoded.txt")
        result = decode_base64_to_file(encoded_result, new_file_path)
        
        # Verify result
        self.assertIsInstance(result, bytes)
        
        # Verify file was created
        self.assertTrue(os.path.exists(new_file_path))
        with open(new_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, original_content)


if __name__ == "__main__":
    unittest.main()
