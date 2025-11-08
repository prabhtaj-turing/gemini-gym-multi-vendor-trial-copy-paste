"""
File utility function tests for the Clock service.

This module tests all file utility functions in the Clock service's file_utils module.
These are shared helper functions for reading/writing files and encoding/decoding.

Test Categories:
- File type detection tests
- MIME type detection tests  
- File reading and writing tests
- Base64 encoding/decoding tests
- Error handling tests
- File permission and access tests
"""

import unittest
import tempfile
import os
import base64
from unittest.mock import patch, mock_open, MagicMock

try:
    from common_utils.base_case import BaseTestCaseWithErrorHandler
except ImportError:
    from common_utils.base_case import BaseTestCaseWithErrorHandler

from clock.SimulationEngine import file_utils


class TestFileUtils(BaseTestCaseWithErrorHandler):
    """Test Clock service file utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()

    def test_is_text_file_text_extensions(self):
        """Test text file detection for various text extensions."""
        text_files = [
            "script.py", "code.js", "style.css", "document.html",
            "data.json", "config.yaml", "readme.md", "query.sql",
            "script.sh", "notes.txt", "log.csv"
        ]
        
        for filename in text_files:
            with self.subTest(filename=filename):
                self.assertTrue(file_utils.is_text_file(filename))

    def test_is_text_file_case_insensitive(self):
        """Test that file extension checking is case insensitive."""
        self.assertTrue(file_utils.is_text_file("Script.PY"))
        self.assertTrue(file_utils.is_text_file("Document.HTML"))
        self.assertTrue(file_utils.is_text_file("Config.JSON"))

    def test_is_binary_file_binary_extensions(self):
        """Test binary file detection for various binary extensions."""
        binary_files = [
            "image.jpg", "photo.png", "document.pdf", "archive.zip",
            "audio.mp3", "video.mp4", "program.exe", "library.dll",
            "database.db", "font.ttf", "model.obj"
        ]
        
        for filename in binary_files:
            with self.subTest(filename=filename):
                self.assertTrue(file_utils.is_binary_file(filename))

    def test_is_binary_file_case_insensitive(self):
        """Test that binary file extension checking is case insensitive."""
        self.assertTrue(file_utils.is_binary_file("Image.JPG"))
        self.assertTrue(file_utils.is_binary_file("Document.PDF"))
        self.assertTrue(file_utils.is_binary_file("Archive.ZIP"))

    def test_file_type_detection_unknown_extension(self):
        """Test file type detection for unknown extensions."""
        unknown_file = "unknown.xyz"
        self.assertFalse(file_utils.is_text_file(unknown_file))
        self.assertFalse(file_utils.is_binary_file(unknown_file))

    def test_get_mime_type(self):
        """Test MIME type detection."""
        mime_tests = [
            ("document.html", "text/html"),
            ("style.css", "text/css"),
            ("script.js", "text/javascript"),  # Actual MIME type returned
            ("data.json", "application/json"),
            ("image.png", "image/png"),
            ("document.pdf", "application/pdf"),
        ]
        
        for filename, expected_mime in mime_tests:
            with self.subTest(filename=filename):
                mime_type = file_utils.get_mime_type(filename)
                self.assertEqual(mime_type, expected_mime)

    def test_get_mime_type_unknown(self):
        """Test MIME type for unknown file extension."""
        mime_type = file_utils.get_mime_type("unknown.xyz")
        # mimetypes library may guess some extensions, fallback only when None
        self.assertTrue(mime_type in ["chemical/x-xyz", "application/octet-stream"])

    def test_read_file_text_success(self):
        """Test reading a text file successfully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "Hello, World!\nThis is a test file."
            f.write(test_content)
            f.flush()
            
            try:
                result = file_utils.read_file(f.name)
                
                self.assertEqual(result['content'], test_content)
                self.assertEqual(result['encoding'], 'text')
                self.assertEqual(result['mime_type'], 'text/plain')
                self.assertGreater(result['size_bytes'], 0)
            finally:
                os.unlink(f.name)

    def test_read_file_binary_success(self):
        """Test reading a binary file successfully."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            test_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
            f.write(test_data)
            f.flush()
            
            try:
                result = file_utils.read_file(f.name)
                
                # Decode the base64 content and verify
                decoded_content = base64.b64decode(result['content'])
                self.assertEqual(decoded_content, test_data)
                self.assertEqual(result['encoding'], 'base64')
                self.assertEqual(result['mime_type'], 'image/jpeg')
                self.assertEqual(result['size_bytes'], len(test_data))
            finally:
                os.unlink(f.name)

    def test_read_file_nonexistent(self):
        """Test reading a nonexistent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            file_utils.read_file("nonexistent_file.txt")

    def test_read_file_too_large(self):
        """Test reading a file larger than max_size_mb raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            f.flush()
            
            try:
                # Try to read with very small max size
                with self.assertRaises(ValueError) as cm:
                    file_utils.read_file(f.name, max_size_mb=0)
                
                self.assertIn("File too large", str(cm.exception))
            finally:
                os.unlink(f.name)

    def test_read_file_encoding_fallback(self):
        """Test file reading with encoding fallback."""
        # Create a file with Latin-1 encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # Write some Latin-1 encoded text
            latin1_content = "Café résumé naïve".encode('latin-1')
            f.write(latin1_content)
            f.flush()
            
            try:
                # Mock the UTF-8 read to fail, then succeed with latin-1
                original_open = open
                
                def mock_open_side_effect(filename, mode='r', **kwargs):
                    if 'encoding' in kwargs and kwargs['encoding'] == 'utf-8':
                        raise UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
                    return original_open(filename, mode, **kwargs)
                
                with patch('builtins.open', side_effect=mock_open_side_effect):
                    result = file_utils.read_file(f.name)
                    self.assertEqual(result['encoding'], 'text')
                    self.assertIsInstance(result['content'], str)
                    
            finally:
                os.unlink(f.name)

    def test_write_file_text(self):
        """Test writing a text file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            test_content = "Hello, World!\nTest content."
            
            file_utils.write_file(file_path, test_content, encoding='text')
            
            # Verify the file was written correctly
            with open(file_path, 'r') as f:
                written_content = f.read()
            
            self.assertEqual(written_content, test_content)

    def test_write_file_binary_base64(self):
        """Test writing a binary file from base64 content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.bin")
            test_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
            base64_content = base64.b64encode(test_data).decode('utf-8')
            
            file_utils.write_file(file_path, base64_content, encoding='base64')
            
            # Verify the file was written correctly
            with open(file_path, 'rb') as f:
                written_data = f.read()
            
            self.assertEqual(written_data, test_data)

    def test_write_file_creates_directories(self):
        """Test that write_file creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "subdir", "nested", "test.txt")
            test_content = "Test content"
            
            file_utils.write_file(nested_path, test_content)
            
            self.assertTrue(os.path.exists(nested_path))
            with open(nested_path, 'r') as f:
                self.assertEqual(f.read(), test_content)

    def test_encode_to_base64_string(self):
        """Test encoding string to base64."""
        test_string = "Hello, World!"
        result = file_utils.encode_to_base64(test_string)
        
        # Decode and verify
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, test_string)

    def test_encode_to_base64_bytes(self):
        """Test encoding bytes to base64."""
        test_bytes = b"Hello, World!"
        result = file_utils.encode_to_base64(test_bytes)
        
        # Decode and verify
        decoded = base64.b64decode(result)
        self.assertEqual(decoded, test_bytes)

    def test_decode_from_base64(self):
        """Test decoding from base64."""
        test_string = "Hello, World!"
        base64_content = base64.b64encode(test_string.encode('utf-8')).decode('utf-8')
        
        result = file_utils.decode_from_base64(base64_content)
        self.assertEqual(result.decode('utf-8'), test_string)

    def test_text_to_base64(self):
        """Test text to base64 conversion."""
        test_text = "Hello, World!"
        result = file_utils.text_to_base64(test_text)
        
        # Should be equivalent to encode_to_base64
        expected = file_utils.encode_to_base64(test_text)
        self.assertEqual(result, expected)

    def test_base64_to_text(self):
        """Test base64 to text conversion."""
        test_text = "Hello, World!"
        base64_content = file_utils.text_to_base64(test_text)
        
        result = file_utils.base64_to_text(base64_content)
        self.assertEqual(result, test_text)

    def test_file_to_base64(self):
        """Test reading file and converting to base64."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_data = b"Hello, World!"
            f.write(test_data)
            f.flush()
            
            try:
                result = file_utils.file_to_base64(f.name)
                
                # Decode and verify
                decoded = base64.b64decode(result)
                self.assertEqual(decoded, test_data)
            finally:
                os.unlink(f.name)

    def test_base64_to_file(self):
        """Test writing base64 content to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.bin")
            test_data = b"Hello, World!"
            base64_content = base64.b64encode(test_data).decode('utf-8')
            
            file_utils.base64_to_file(base64_content, file_path)
            
            # Verify the file was written correctly
            with open(file_path, 'rb') as f:
                written_data = f.read()
            
            self.assertEqual(written_data, test_data)

    def test_base64_to_file_creates_directories(self):
        """Test that base64_to_file creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "subdir", "test.bin")
            test_data = b"Hello, World!"
            base64_content = base64.b64encode(test_data).decode('utf-8')
            
            file_utils.base64_to_file(base64_content, nested_path)
            
            self.assertTrue(os.path.exists(nested_path))
            with open(nested_path, 'rb') as f:
                self.assertEqual(f.read(), test_data)

    def test_write_file_bytes_as_text(self):
        """Test writing bytes content as text."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            test_bytes = b"Hello, World!"
            
            file_utils.write_file(file_path, test_bytes, encoding='text')
            
            # Verify the file was written correctly
            with open(file_path, 'r') as f:
                written_content = f.read()
            
            self.assertEqual(written_content, test_bytes.decode('utf-8'))

    def test_constants_coverage(self):
        """Test that file extension constants are accessible."""
        # Test that constants are defined and not empty
        self.assertIsInstance(file_utils.TEXT_EXTENSIONS, set)
        self.assertGreater(len(file_utils.TEXT_EXTENSIONS), 0)
        
        self.assertIsInstance(file_utils.BINARY_EXTENSIONS, set)
        self.assertGreater(len(file_utils.BINARY_EXTENSIONS), 0)
        
        # Test some expected extensions
        self.assertIn('.py', file_utils.TEXT_EXTENSIONS)
        self.assertIn('.js', file_utils.TEXT_EXTENSIONS)
        self.assertIn('.html', file_utils.TEXT_EXTENSIONS)
        
        self.assertIn('.jpg', file_utils.BINARY_EXTENSIONS)
        self.assertIn('.png', file_utils.BINARY_EXTENSIONS)
        self.assertIn('.pdf', file_utils.BINARY_EXTENSIONS)
