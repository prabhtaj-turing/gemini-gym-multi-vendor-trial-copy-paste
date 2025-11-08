"""
File Utilities Tests for MySQL API

This module tests file utility functions for comprehensive coverage
as required by the Service Engineering Test Framework Guidelines.
"""

import unittest
import os
import sys
import tempfile
import base64
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestFileUtils(BaseTestCaseWithErrorHandler):
    """
    Test file utility functions for comprehensive coverage.
    """

    def setUp(self):
        super().setUp()
        self.test_dir = tempfile.mkdtemp(prefix="mysql_file_utils_test_")
        # Import file_utils here to avoid module loading issues
        from mysql.SimulationEngine import file_utils
        self.file_utils = file_utils

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        super().tearDown()

    def _create_test_file(self, filename, content, encoding='utf-8', is_binary=False):
        """Helper to create test files"""
        filepath = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if is_binary:
            with open(filepath, 'wb') as f:
                if isinstance(content, str):
                    f.write(content.encode(encoding))
                else:
                    f.write(content)
        else:
            with open(filepath, 'w', encoding=encoding) as f:
                f.write(content)
        
        return filepath

    def test_is_text_file_common_extensions(self):
        """Test is_text_file with common text file extensions"""
        text_files = [
            'script.py', 'app.js', 'style.css', 'page.html', 'data.json',
            'config.yml', 'README.md', 'file.txt', 'query.sql', 'test.java'
        ]
        
        for filename in text_files:
            with self.subTest(filename=filename):
                self.assertTrue(self.file_utils.is_text_file(filename))

    def test_is_text_file_case_insensitive(self):
        """Test is_text_file handles case insensitive extensions"""
        self.assertTrue(self.file_utils.is_text_file('FILE.PY'))
        self.assertTrue(self.file_utils.is_text_file('Script.JS'))
        self.assertTrue(self.file_utils.is_text_file('Config.JSON'))

    def test_is_text_file_no_extension(self):
        """Test is_text_file with files that have no extension"""
        self.assertFalse(self.file_utils.is_text_file('filename'))
        self.assertFalse(self.file_utils.is_text_file('path/to/filename'))

    def test_is_binary_file_common_extensions(self):
        """Test is_binary_file with common binary file extensions"""
        binary_files = [
            'image.jpg', 'photo.png', 'document.pdf', 'data.xlsx',
            'video.mp4', 'audio.mp3', 'archive.zip', 'app.exe'
        ]
        
        for filename in binary_files:
            with self.subTest(filename=filename):
                self.assertTrue(self.file_utils.is_binary_file(filename))

    def test_is_binary_file_case_insensitive(self):
        """Test is_binary_file handles case insensitive extensions"""
        self.assertTrue(self.file_utils.is_binary_file('IMAGE.JPG'))
        self.assertTrue(self.file_utils.is_binary_file('Document.PDF'))
        self.assertTrue(self.file_utils.is_binary_file('Video.MP4'))

    def test_is_binary_file_no_extension(self):
        """Test is_binary_file with files that have no extension"""
        self.assertFalse(self.file_utils.is_binary_file('filename'))
        self.assertFalse(self.file_utils.is_binary_file('path/to/filename'))

    def test_get_mime_type_common_types(self):
        """Test get_mime_type returns correct MIME types"""
        test_cases = [
            ('file.txt', 'text/plain'),
            ('file.json', 'application/json'),
            ('file.html', 'text/html'),
            ('file.css', 'text/css'),
            ('file.js', 'text/javascript'),
            ('image.jpg', 'image/jpeg'),
            ('image.png', 'image/png'),
            ('document.pdf', 'application/pdf'),
            ('file.unknown_ext', 'application/octet-stream'),  # Default fallback
        ]
        
        for filename, expected_mime in test_cases:
            with self.subTest(filename=filename):
                actual_mime = self.file_utils.get_mime_type(filename)
                self.assertEqual(actual_mime, expected_mime)

    def test_get_mime_type_no_extension(self):
        """Test get_mime_type with files that have no extension"""
        mime_type = self.file_utils.get_mime_type('filename')
        self.assertEqual(mime_type, 'application/octet-stream')

    def test_read_file_text_utf8(self):
        """Test reading UTF-8 text files"""
        content = "Hello, World!\nThis is a test file with UTF-8 content: 你好"
        filepath = self._create_test_file('test.txt', content)
        
        result = self.file_utils.read_file(filepath)
        
        self.assertEqual(result['content'], content)
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/plain')
        self.assertEqual(result['size_bytes'], len(content.encode('utf-8')))

    def test_read_file_text_alternative_encoding(self):
        """Test reading text files with alternative encodings"""
        content = "Hello with special chars: café, naïve, résumé"
        filepath = self._create_test_file('test.txt', content, encoding='latin-1')
        
        # Mock UTF-8 to fail, forcing alternative encoding
        original_open = open
        
        def mock_open_func(file, mode='r', **kwargs):
            if 'utf-8' in kwargs.get('encoding', ''):
                def failing_read():
                    raise UnicodeDecodeError('utf-8', b'', 0, 1, 'test error')
                mock = original_open(file, mode, **kwargs)
                mock.read = failing_read
                return mock
            return original_open(file, mode, **kwargs)
        
        with patch('builtins.open', side_effect=mock_open_func):
            result = self.file_utils.read_file(filepath)
        
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/plain')

    def test_read_file_binary(self):
        """Test reading binary files"""
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00'  # PNG header
        filepath = self._create_test_file('test.png', binary_content, is_binary=True)
        
        result = self.file_utils.read_file(filepath)
        
        expected_b64 = base64.b64encode(binary_content).decode('utf-8')
        self.assertEqual(result['content'], expected_b64)
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['mime_type'], 'image/png')
        self.assertEqual(result['size_bytes'], len(binary_content))

    def test_read_file_not_exists(self):
        """Test reading non-existent file"""
        with self.assertRaises(FileNotFoundError) as context:
            self.file_utils.read_file('/nonexistent/path/file.txt')
        
        self.assertIn("File not found", str(context.exception))

    def test_read_file_too_large(self):
        """Test reading file that exceeds size limit"""
        filepath = self._create_test_file('large.txt', 'x' * 100)  # Small file
        
        with self.assertRaises(ValueError) as context:
            self.file_utils.read_file(filepath, max_size_mb=0.00001)  # Very small limit
        
        self.assertIn("File too large", str(context.exception))

    def test_write_file_text_content(self):
        """Test writing text content to file"""
        content = "Hello, World!\nThis is test content."
        filepath = os.path.join(self.test_dir, 'output', 'test.txt')
        
        self.file_utils.write_file(filepath, content, encoding='text')
        
        # Verify file was created and content is correct
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)

    def test_write_file_bytes_as_text(self):
        """Test writing bytes content as text"""
        content_bytes = "Hello, bytes!".encode('utf-8')
        filepath = os.path.join(self.test_dir, 'test_bytes.txt')
        
        self.file_utils.write_file(filepath, content_bytes, encoding='text')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, "Hello, bytes!")

    def test_write_file_base64_string(self):
        """Test writing base64 string content"""
        original_content = b"Binary data: \x89PNG\r\n\x1a\n"
        b64_content = base64.b64encode(original_content).decode('utf-8')
        filepath = os.path.join(self.test_dir, 'binary_output.bin')
        
        self.file_utils.write_file(filepath, b64_content, encoding='base64')
        
        # Verify binary content was written correctly
        with open(filepath, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, original_content)

    def test_write_file_base64_bytes(self):
        """Test writing bytes content as base64"""
        original_content = b"Binary bytes data"
        filepath = os.path.join(self.test_dir, 'binary_bytes.bin')
        
        self.file_utils.write_file(filepath, original_content, encoding='base64')
        
        with open(filepath, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, original_content)

    def test_encode_to_base64_string(self):
        """Test encoding string to base64"""
        text = "Hello, Base64!"
        expected = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
        result = self.file_utils.encode_to_base64(text)
        self.assertEqual(result, expected)

    def test_encode_to_base64_bytes(self):
        """Test encoding bytes to base64"""
        data = b"Binary data"
        expected = base64.b64encode(data).decode('utf-8')
        
        result = self.file_utils.encode_to_base64(data)
        self.assertEqual(result, expected)

    def test_decode_from_base64(self):
        """Test decoding base64 to bytes"""
        original_data = b"Original binary data"
        b64_data = base64.b64encode(original_data).decode('utf-8')
        
        result = self.file_utils.decode_from_base64(b64_data)
        self.assertEqual(result, original_data)

    def test_text_to_base64(self):
        """Test converting text to base64"""
        text = "Convert this text"
        expected = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
        result = self.file_utils.text_to_base64(text)
        self.assertEqual(result, expected)

    def test_base64_to_text(self):
        """Test converting base64 to text"""
        original_text = "Original text content"
        b64_text = base64.b64encode(original_text.encode('utf-8')).decode('utf-8')
        
        result = self.file_utils.base64_to_text(b64_text)
        self.assertEqual(result, original_text)

    def test_file_to_base64(self):
        """Test reading file and converting to base64"""
        binary_data = b'\x89PNG\r\n\x1a\n\x00\x00test_png_data'
        filepath = self._create_test_file('test.png', binary_data, is_binary=True)
        
        result = self.file_utils.file_to_base64(filepath)
        expected = base64.b64encode(binary_data).decode('utf-8')
        self.assertEqual(result, expected)

    def test_file_to_base64_text_file(self):
        """Test reading text file and converting to base64"""
        text_content = "Text file content"
        filepath = self._create_test_file('text.txt', text_content)
        
        result = self.file_utils.file_to_base64(filepath)
        expected = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_base64_to_file(self):
        """Test writing base64 content to file"""
        original_data = b"Binary file content with special bytes: \x00\x01\x02"
        b64_content = base64.b64encode(original_data).decode('utf-8')
        output_filepath = os.path.join(self.test_dir, 'output', 'binary_output.bin')
        
        self.file_utils.base64_to_file(b64_content, output_filepath)
        
        # Verify file was created with correct content
        self.assertTrue(os.path.exists(output_filepath))
        with open(output_filepath, 'rb') as f:
            written_data = f.read()
        self.assertEqual(written_data, original_data)

    def test_round_trip_text_file(self):
        """Test complete round trip: text file -> base64 -> file"""
        original_content = "Round trip test content\nWith multiple lines\nAnd special chars: äöü"
        original_filepath = self._create_test_file('original.txt', original_content)
        
        # Read file as base64
        b64_content = self.file_utils.file_to_base64(original_filepath)
        
        # Write base64 back to new file
        new_filepath = os.path.join(self.test_dir, 'round_trip.txt')
        self.file_utils.base64_to_file(b64_content, new_filepath)
        
        # Verify content is identical
        with open(new_filepath, 'r', encoding='utf-8') as f:
            final_content = f.read()
        self.assertEqual(final_content, original_content)

    def test_round_trip_binary_file(self):
        """Test complete round trip: binary file -> base64 -> file"""
        original_data = bytes([i for i in range(256)])  # All possible byte values
        original_filepath = self._create_test_file('original.bin', original_data, is_binary=True)
        
        # Read file as base64
        b64_content = self.file_utils.file_to_base64(original_filepath)
        
        # Write base64 back to new file
        new_filepath = os.path.join(self.test_dir, 'round_trip.bin')
        self.file_utils.base64_to_file(b64_content, new_filepath)
        
        # Verify content is identical
        with open(new_filepath, 'rb') as f:
            final_data = f.read()
        self.assertEqual(final_data, original_data)

    def test_directory_creation(self):
        """Test that directories are created when writing files"""
        filepath = os.path.join(self.test_dir, 'deep', 'nested', 'directory', 'file.txt')
        content = "Test directory creation"
        
        self.file_utils.write_file(filepath, content, encoding='text')
        
        # Verify file exists and directory was created
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(os.path.isdir(os.path.dirname(filepath)))
        
        with open(filepath, 'r') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)

    def test_error_handling_base64_to_text_invalid_utf8(self):
        """Test error handling when base64 decodes to invalid UTF-8"""
        # Create base64 that decodes to invalid UTF-8 bytes
        invalid_utf8_bytes = b'\xff\xfe\x00\x00'
        invalid_b64 = base64.b64encode(invalid_utf8_bytes).decode('utf-8')
        
        with self.assertRaises(UnicodeDecodeError):
            self.file_utils.base64_to_text(invalid_b64)

    def test_file_utils_constants(self):
        """Test that file extension constants are properly defined"""
        # Test some common text extensions exist
        self.assertIn('.py', self.file_utils.TEXT_EXTENSIONS)
        self.assertIn('.js', self.file_utils.TEXT_EXTENSIONS)
        self.assertIn('.json', self.file_utils.TEXT_EXTENSIONS)
        
        # Test some common binary extensions exist
        self.assertIn('.jpg', self.file_utils.BINARY_EXTENSIONS)
        self.assertIn('.pdf', self.file_utils.BINARY_EXTENSIONS)
        self.assertIn('.exe', self.file_utils.BINARY_EXTENSIONS)
        
        # Test that extensions are defined (note: some files like .svg and .ts can be both)
        overlap = self.file_utils.TEXT_EXTENSIONS & self.file_utils.BINARY_EXTENSIONS
        # Allow known ambiguous extensions (.svg and .ts can be both text and binary)
        expected_overlap = {'.svg', '.ts'}  # SVG can be text/xml or binary, TS can be TypeScript or Transport Stream
        self.assertEqual(overlap, expected_overlap, f"Unexpected overlap in extensions: {overlap - expected_overlap}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
