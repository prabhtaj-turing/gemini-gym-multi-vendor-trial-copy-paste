import unittest
import os
import shutil
import base64
from ..SimulationEngine import file_utils

class TestFileUtils(unittest.TestCase):
    """Test suite for file utility functions."""

    def setUp(self):
        """Set up test files."""
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)
        self.text_file = os.path.join(self.test_dir, "test.txt")
        self.binary_file = os.path.join(self.test_dir, "test.bin")

        with open(self.text_file, "w") as f:
            f.write("hello world")

        with open(self.binary_file, "wb") as f:
            f.write(b"\x01\x02\x03")

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_read_text_file(self):
        """Test reading a text file."""
        data = file_utils.read_file(self.text_file)
        self.assertEqual(data['content'], "hello world")
        self.assertEqual(data['encoding'], 'text')

    def test_read_binary_file(self):
        """Test reading a binary file."""
        data = file_utils.read_file(self.binary_file)
        decoded_content = base64.b64decode(data['content'])
        self.assertEqual(decoded_content, b"\x01\x02\x03")
        self.assertEqual(data['encoding'], 'base64')

    def test_write_text_file(self):
        """Test writing a text file."""
        new_file = os.path.join(self.test_dir, "new.txt")
        file_utils.write_file(new_file, "new content")
        with open(new_file, "r") as f:
            self.assertEqual(f.read(), "new content")
        os.remove(new_file)

    def test_write_binary_file(self):
        """Test writing a binary file."""
        new_file = os.path.join(self.test_dir, "new.bin")
        content = base64.b64encode(b"new binary").decode('utf-8')
        file_utils.write_file(new_file, content, encoding='base64')
        with open(new_file, "rb") as f:
            self.assertEqual(f.read(), b"new binary")
        os.remove(new_file)

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            file_utils.read_file("nonexistent.txt")

    def test_read_oversized_file(self):
        """Test reading a file that is too large."""
        oversized_file = os.path.join(self.test_dir, "oversized.bin")
        with open(oversized_file, "wb") as f:
            f.write(b"\x00" * (1024 * 1024 + 1)) # 1MB + 1 byte
        
        with self.assertRaises(ValueError):
            file_utils.read_file(oversized_file, max_size_mb=1)
        
    def test_base64_conversions(self):
        """Test base64 conversion functions."""
        text = "hello world"
        base64_text = file_utils.text_to_base64(text)
        self.assertEqual(file_utils.base64_to_text(base64_text), text)

        file_content = b"some file content"
        base64_file = os.path.join(self.test_dir, "base64.txt")
        file_utils.base64_to_file(file_utils.encode_to_base64(file_content), base64_file)
        
        self.assertEqual(file_utils.file_to_base64(base64_file), file_utils.encode_to_base64(file_content))

if __name__ == '__main__':
    unittest.main()
