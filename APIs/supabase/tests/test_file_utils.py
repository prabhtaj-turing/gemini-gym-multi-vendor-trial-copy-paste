import unittest
import os
import shutil
import tempfile
import base64
from unittest.mock import patch

from ..SimulationEngine import file_utils
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestFileUtils(BaseTestCaseWithErrorHandler):
    """Test cases for file utility functions."""

    def setUp(self):
        """Set up a temporary directory for file tests."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Remove the temporary directory after tests."""
        shutil.rmtree(self.test_dir)

    def test_is_text_file(self):
        """Test detection of text files."""
        self.assertTrue(file_utils.is_text_file('test.txt'))
        self.assertTrue(file_utils.is_text_file('test.py'))
        self.assertTrue(file_utils.is_text_file('TEST.HTML'))
        self.assertFalse(file_utils.is_text_file('test.png'))
        self.assertFalse(file_utils.is_text_file('test.zip'))
        self.assertFalse(file_utils.is_text_file('test'))

    def test_is_binary_file(self):
        """Test detection of binary files."""
        self.assertTrue(file_utils.is_binary_file('test.jpg'))
        self.assertTrue(file_utils.is_binary_file('test.pdf'))
        self.assertTrue(file_utils.is_binary_file('TEST.EXE'))
        self.assertFalse(file_utils.is_binary_file('test.txt'))
        self.assertFalse(file_utils.is_binary_file('test.json'))
        self.assertFalse(file_utils.is_binary_file('test'))

    def test_get_mime_type(self):
        """Test MIME type guessing."""
        self.assertEqual(file_utils.get_mime_type('test.txt'), 'text/plain')
        self.assertEqual(file_utils.get_mime_type('test.json'), 'application/json')
        self.assertEqual(file_utils.get_mime_type('test.jpg'), 'image/jpeg')
        self.assertEqual(file_utils.get_mime_type('test.unknown'), 'application/octet-stream')

    def test_write_and_read_text_file(self):
        """Test writing and reading a text file."""
        file_path = os.path.join(self.test_dir, 'test.txt')
        content = "Hello, World!\nThis is a test with Unicode: éàç"
        
        file_utils.write_file(file_path, content, encoding='text')
        
        result = file_utils.read_file(file_path)
        
        self.assertEqual(result['content'], content)
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/plain')
        self.assertEqual(result['size_bytes'], len(content.encode('utf-8')))

    def test_write_and_read_binary_file(self):
        """Test writing and reading a binary file with base64 encoding."""
        file_path = os.path.join(self.test_dir, 'test.bin')
        binary_content = b'\x01\x02\x03\x04\x05'
        base64_content = base64.b64encode(binary_content).decode('utf-8')
        
        file_utils.write_file(file_path, base64_content, encoding='base64')
        
        result = file_utils.read_file(file_path)
        
        self.assertEqual(result['content'], base64_content)
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['mime_type'], 'application/octet-stream')
        self.assertEqual(result['size_bytes'], len(binary_content))

    def test_read_file_not_found(self):
        """Test reading a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            file_utils.read_file('non_existent_file.txt')

    @patch('os.path.getsize')
    def test_read_file_too_large(self, mock_getsize):
        """Test reading a file that exceeds the size limit."""
        file_path = os.path.join(self.test_dir, 'large_file.txt')
        with open(file_path, 'w') as f:
            f.write('dummy content')
            
        mock_getsize.return_value = 2 * 1024 * 1024  # 2MB
        
        with self.assertRaises(ValueError):
            file_utils.read_file(file_path, max_size_mb=1)

    def test_base64_conversions(self):
        """Test base64 encoding and decoding functions."""
        text = "Hello Base64"
        encoded = file_utils.text_to_base64(text)
        self.assertIsInstance(encoded, str)
        
        decoded = file_utils.base64_to_text(encoded)
        self.assertEqual(decoded, text)

    def test_file_to_base64_and_back(self):
        """Test converting a file to base64 and writing it back."""
        # Test with text file
        text_path = os.path.join(self.test_dir, 'source.txt')
        text_content = "File to Base64 test"
        with open(text_path, 'w') as f:
            f.write(text_content)
            
        base64_content = file_utils.file_to_base64(text_path)
        
        dest_path = os.path.join(self.test_dir, 'dest.txt')
        file_utils.base64_to_file(base64_content, dest_path)
        
        with open(dest_path, 'r') as f:
            self.assertEqual(f.read(), text_content)

        # Test with binary file
        bin_path = os.path.join(self.test_dir, 'source.bin')
        bin_content = b'\x0a\x0b\x0c'
        with open(bin_path, 'wb') as f:
            f.write(bin_content)
        
        base64_bin_content = file_utils.file_to_base64(bin_path)

        dest_bin_path = os.path.join(self.test_dir, 'dest.bin')
        file_utils.base64_to_file(base64_bin_content, dest_bin_path)

        with open(dest_bin_path, 'rb') as f:
            self.assertEqual(f.read(), bin_content)


if __name__ == '__main__':
    unittest.main()
