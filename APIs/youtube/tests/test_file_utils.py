"""
Test cases for YouTube SimulationEngine file_utils module.

This module tests all file utility functions including file type detection,
file reading/writing, and base64 encoding/decoding operations.
"""

import unittest
import os
import tempfile
import shutil
import base64
from unittest.mock import patch, mock_open

from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube.SimulationEngine import file_utils


class TestFileUtils(BaseTestCaseWithErrorHandler):
    """Test cases for file utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_text_content = "Hello, World! 🌍\nThis is a test file with unicode."
        self.test_binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00'
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_is_text_file_with_text_extensions(self):
        """Test is_text_file returns True for text file extensions."""
        text_files = [
            'test.py', 'script.js', 'style.css', 'data.json', 'README.md',
            'config.yaml', 'app.html', 'query.sql', 'build.sh', 'data.csv'
        ]
        
        for file_path in text_files:
            with self.subTest(file_path=file_path):
                self.assertTrue(file_utils.is_text_file(file_path))

    def test_is_text_file_with_binary_extensions(self):
        """Test is_text_file returns False for binary file extensions."""
        binary_files = [
            'image.jpg', 'document.pdf', 'archive.zip', 'audio.mp3',
            'video.mp4', 'executable.exe', 'library.dll', 'data.db'
        ]
        
        for file_path in binary_files:
            with self.subTest(file_path=file_path):
                self.assertFalse(file_utils.is_text_file(file_path))

    def test_is_text_file_case_insensitive(self):
        """Test is_text_file is case insensitive."""
        self.assertTrue(file_utils.is_text_file('TEST.PY'))
        self.assertTrue(file_utils.is_text_file('Script.JS'))
        self.assertFalse(file_utils.is_text_file('IMAGE.JPG'))

    def test_is_text_file_unknown_extension(self):
        """Test is_text_file returns False for unknown extensions."""
        self.assertFalse(file_utils.is_text_file('test.unknownext'))
        self.assertFalse(file_utils.is_text_file('file_with_no_extension'))

    def test_is_binary_file_with_binary_extensions(self):
        """Test is_binary_file returns True for binary file extensions."""
        binary_files = [
            'image.png', 'document.docx', 'spreadsheet.xlsx', 'archive.rar',
            'music.wav', 'movie.avi', 'program.bin', 'database.sqlite'
        ]
        
        for file_path in binary_files:
            with self.subTest(file_path=file_path):
                self.assertTrue(file_utils.is_binary_file(file_path))

    def test_is_binary_file_with_text_extensions(self):
        """Test is_binary_file returns False for text file extensions."""
        text_files = [
            'script.py', 'style.scss', 'config.toml', 'note.txt'
        ]
        
        for file_path in text_files:
            with self.subTest(file_path=file_path):
                self.assertFalse(file_utils.is_binary_file(file_path))

    def test_is_binary_file_case_insensitive(self):
        """Test is_binary_file is case insensitive."""
        self.assertTrue(file_utils.is_binary_file('IMAGE.PNG'))
        self.assertTrue(file_utils.is_binary_file('Document.PDF'))
        self.assertFalse(file_utils.is_binary_file('SCRIPT.PY'))

    def test_get_mime_type_common_types(self):
        """Test get_mime_type returns correct MIME types."""
        mime_tests = [
            ('test.html', 'text/html'),
            ('script.js', 'text/javascript'),
            ('data.json', 'application/json'),
            ('image.png', 'image/png'),
            ('document.pdf', 'application/pdf'),
            ('style.css', 'text/css'),
        ]
        
        for file_path, expected_mime in mime_tests:
            with self.subTest(file_path=file_path):
                result = file_utils.get_mime_type(file_path)
                self.assertEqual(result, expected_mime)

    def test_get_mime_type_unknown_extension(self):
        """Test get_mime_type returns default for unknown extensions."""
        result = file_utils.get_mime_type('file.unknownext')
        self.assertEqual(result, 'application/octet-stream')

    def test_read_file_text_file_success(self):
        """Test reading a text file successfully."""
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(self.test_text_content)
        
        result = file_utils.read_file(test_file)
        
        self.assertEqual(result['content'], self.test_text_content)
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/plain')
        self.assertGreater(result['size_bytes'], 0)

    def test_read_file_binary_file_success(self):
        """Test reading a binary file successfully."""
        test_file = os.path.join(self.temp_dir, 'test.png')
        with open(test_file, 'wb') as f:
            f.write(self.test_binary_content)
        
        result = file_utils.read_file(test_file)
        
        expected_content = base64.b64encode(self.test_binary_content).decode('utf-8')
        self.assertEqual(result['content'], expected_content)
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['mime_type'], 'image/png')
        self.assertEqual(result['size_bytes'], len(self.test_binary_content))

    def test_read_file_not_found(self):
        """Test read_file raises FileNotFoundError for non-existent file."""
        non_existent_file = os.path.join(self.temp_dir, 'does_not_exist.txt')
        
        with self.assertRaises(FileNotFoundError) as context:
            file_utils.read_file(non_existent_file)
        
        self.assertIn('File not found', str(context.exception))

    def test_read_file_size_limit_exceeded(self):
        """Test read_file raises ValueError when file exceeds size limit."""
        test_file = os.path.join(self.temp_dir, 'large_test.txt')
        large_content = 'x' * (2 * 1024 * 1024)  # 2MB content
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(large_content)
        
        with self.assertRaises(ValueError) as context:
            file_utils.read_file(test_file, max_size_mb=1)  # 1MB limit
        
        self.assertIn('File too large', str(context.exception))

    def test_read_file_unicode_decode_fallback(self):
        """Test read_file handles unicode decode errors with fallback encodings."""
        test_file = os.path.join(self.temp_dir, 'latin1_test.txt')
        latin1_content = 'Café résumé naïve'.encode('latin-1')
        
        with open(test_file, 'wb') as f:
            f.write(latin1_content)
        
        result = file_utils.read_file(test_file)
        
        self.assertEqual(result['encoding'], 'text')
        self.assertIn('Café', result['content'])

    def test_read_file_unicode_decode_failure(self):
        """Test read_file raises ValueError when all encoding attempts fail."""
        test_file = os.path.join(self.temp_dir, 'binary_as_text.py')  # .py extension but binary content
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xfe\x00\x01\x02\x03')  # Invalid unicode bytes
        
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'mock')):
            with self.assertRaises(ValueError) as context:
                file_utils.read_file(test_file)
            
            self.assertIn('Could not decode file', str(context.exception))

    def test_write_file_text_content(self):
        """Test writing text content to file."""
        test_file = os.path.join(self.temp_dir, 'subdir', 'output.txt')
        
        file_utils.write_file(test_file, self.test_text_content, 'text')
        
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, self.test_text_content)

    def test_write_file_base64_content(self):
        """Test writing base64 content to file."""
        test_file = os.path.join(self.temp_dir, 'output.bin')
        base64_content = base64.b64encode(self.test_binary_content).decode('utf-8')
        
        file_utils.write_file(test_file, base64_content, 'base64')
        
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, self.test_binary_content)

    def test_write_file_bytes_content_as_text(self):
        """Test writing bytes content as text."""
        test_file = os.path.join(self.temp_dir, 'output.txt')
        bytes_content = self.test_text_content.encode('utf-8')
        
        file_utils.write_file(test_file, bytes_content, 'text')
        
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, self.test_text_content)

    def test_write_file_bytes_content_as_base64(self):
        """Test writing bytes content as base64."""
        test_file = os.path.join(self.temp_dir, 'output.bin')
        
        file_utils.write_file(test_file, self.test_binary_content, 'base64')
        
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, self.test_binary_content)

    def test_encode_to_base64_string_input(self):
        """Test encode_to_base64 with string input."""
        test_string = "Hello, World!"
        result = file_utils.encode_to_base64(test_string)
        expected = base64.b64encode(test_string.encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_encode_to_base64_bytes_input(self):
        """Test encode_to_base64 with bytes input."""
        test_bytes = b"Hello, World!"
        result = file_utils.encode_to_base64(test_bytes)
        expected = base64.b64encode(test_bytes).decode('utf-8')
        self.assertEqual(result, expected)

    def test_decode_from_base64(self):
        """Test decode_from_base64 function."""
        test_string = "Hello, World!"
        encoded = base64.b64encode(test_string.encode('utf-8')).decode('utf-8')
        
        result = file_utils.decode_from_base64(encoded)
        
        self.assertEqual(result, test_string.encode('utf-8'))
        self.assertIsInstance(result, bytes)

    def test_text_to_base64(self):
        """Test text_to_base64 function."""
        test_text = "Hello, 世界!"
        result = file_utils.text_to_base64(test_text)
        expected = base64.b64encode(test_text.encode('utf-8')).decode('utf-8')
        self.assertEqual(result, expected)

    def test_base64_to_text(self):
        """Test base64_to_text function."""
        test_text = "Hello, 世界!"
        encoded = base64.b64encode(test_text.encode('utf-8')).decode('utf-8')
        
        result = file_utils.base64_to_text(encoded)
        
        self.assertEqual(result, test_text)

    def test_file_to_base64(self):
        """Test file_to_base64 function."""
        test_file = os.path.join(self.temp_dir, 'test.bin')
        with open(test_file, 'wb') as f:
            f.write(self.test_binary_content)
        
        result = file_utils.file_to_base64(test_file)
        expected = base64.b64encode(self.test_binary_content).decode('utf-8')
        
        self.assertEqual(result, expected)

    def test_base64_to_file(self):
        """Test base64_to_file function."""
        test_file = os.path.join(self.temp_dir, 'subdir', 'output.bin')
        base64_content = base64.b64encode(self.test_binary_content).decode('utf-8')
        
        file_utils.base64_to_file(base64_content, test_file)
        
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            content = f.read()
        self.assertEqual(content, self.test_binary_content)

    def test_roundtrip_text_to_base64_and_back(self):
        """Test roundtrip conversion: text -> base64 -> text."""
        original_text = "Hello, World! 🌍\nMultiline text with unicode."
        
        # Convert to base64
        base64_content = file_utils.text_to_base64(original_text)
        
        # Convert back to text
        recovered_text = file_utils.base64_to_text(base64_content)
        
        self.assertEqual(recovered_text, original_text)

    def test_roundtrip_file_operations(self):
        """Test roundtrip file operations: file -> base64 -> file."""
        original_file = os.path.join(self.temp_dir, 'original.bin')
        recovered_file = os.path.join(self.temp_dir, 'recovered.bin')
        
        # Write original file
        with open(original_file, 'wb') as f:
            f.write(self.test_binary_content)
        
        # Convert file to base64
        base64_content = file_utils.file_to_base64(original_file)
        
        # Write base64 back to file
        file_utils.base64_to_file(base64_content, recovered_file)
        
        # Verify content is identical
        with open(recovered_file, 'rb') as f:
            recovered_content = f.read()
        
        self.assertEqual(recovered_content, self.test_binary_content)

    def test_empty_file_handling(self):
        """Test handling of empty files."""
        empty_text_file = os.path.join(self.temp_dir, 'empty.txt')
        empty_binary_file = os.path.join(self.temp_dir, 'empty.bin')
        
        # Create empty files
        open(empty_text_file, 'w').close()
        open(empty_binary_file, 'wb').close()
        
        # Test reading empty text file
        result = file_utils.read_file(empty_text_file)
        self.assertEqual(result['content'], '')
        self.assertEqual(result['size_bytes'], 0)
        
        # Test reading empty binary file
        result = file_utils.read_file(empty_binary_file)
        self.assertEqual(result['content'], '')  # Empty base64
        self.assertEqual(result['size_bytes'], 0)

    def test_write_file_creates_directories(self):
        """Test write_file creates necessary directories."""
        nested_file = os.path.join(self.temp_dir, 'a', 'b', 'c', 'nested.txt')
        
        file_utils.write_file(nested_file, "test content", 'text')
        
        self.assertTrue(os.path.exists(nested_file))
        self.assertTrue(os.path.isdir(os.path.dirname(nested_file)))

    def test_base64_invalid_input_handling(self):
        """Test handling of invalid base64 input."""
        invalid_base64 = "This is not base64!"
        
        with self.assertRaises(Exception):  # base64.binascii.Error or ValueError
            file_utils.decode_from_base64(invalid_base64)
        
        with self.assertRaises(Exception):
            file_utils.base64_to_text(invalid_base64)


if __name__ == '__main__':
    unittest.main()
