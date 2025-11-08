"""
Test cases for file_utils module
"""

import unittest
import os
import tempfile
import shutil
import base64
from unittest.mock import patch, mock_open

from APIs.common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import file_utils


class TestFileUtils(BaseTestCaseWithErrorHandler):
    """
    Test suite for file_utils module.
    Tests file handling utilities including reading, writing, encoding, and file type detection.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_text_file = os.path.join(self.test_dir, "test.txt")
        self.test_python_file = os.path.join(self.test_dir, "test.py")
        self.test_binary_file = os.path.join(self.test_dir, "test.jpg")
        self.test_nonexistent_file = os.path.join(self.test_dir, "nonexistent.txt")

    def tearDown(self):
        """Clean up after each test method."""
        # Remove the temporary directory and all its contents
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_get_file_extension_with_extension(self):
        """Test getting file extension from file path with extension."""
        self.assertEqual(file_utils.get_file_extension("test.txt"), ".txt")
        self.assertEqual(file_utils.get_file_extension("document.pdf"), ".pdf")
        self.assertEqual(file_utils.get_file_extension("script.py"), ".py")
        self.assertEqual(file_utils.get_file_extension("/path/to/file.json"), ".json")

    def test_get_file_extension_uppercase(self):
        """Test getting file extension handles uppercase extensions."""
        self.assertEqual(file_utils.get_file_extension("TEST.TXT"), ".txt")
        self.assertEqual(file_utils.get_file_extension("Document.PDF"), ".pdf")
        self.assertEqual(file_utils.get_file_extension("SCRIPT.PY"), ".py")

    def test_get_file_extension_no_extension(self):
        """Test getting file extension from file path without extension."""
        self.assertEqual(file_utils.get_file_extension("test"), "")
        self.assertEqual(file_utils.get_file_extension("README"), "")
        self.assertEqual(file_utils.get_file_extension("/path/to/file"), "")

    def test_get_file_extension_multiple_dots(self):
        """Test getting file extension with multiple dots in filename."""
        self.assertEqual(file_utils.get_file_extension("test.backup.txt"), ".txt")
        self.assertEqual(file_utils.get_file_extension("archive.tar.gz"), ".gz")
        self.assertEqual(file_utils.get_file_extension("config.local.json"), ".json")

    def test_get_file_extension_empty_string(self):
        """Test getting file extension from empty string."""
        self.assertEqual(file_utils.get_file_extension(""), "")

    def test_is_text_file_python_files(self):
        """Test text file detection for Python files."""
        self.assertTrue(file_utils.is_text_file("script.py"))
        self.assertTrue(file_utils.is_text_file("module.py"))
        self.assertTrue(file_utils.is_text_file("/path/to/script.PY"))

    def test_is_text_file_web_files(self):
        """Test text file detection for web development files."""
        self.assertTrue(file_utils.is_text_file("index.html"))
        self.assertTrue(file_utils.is_text_file("style.css"))
        self.assertTrue(file_utils.is_text_file("app.js"))
        self.assertTrue(file_utils.is_text_file("component.jsx"))
        self.assertTrue(file_utils.is_text_file("types.ts"))

    def test_is_text_file_config_files(self):
        """Test text file detection for configuration files."""
        self.assertTrue(file_utils.is_text_file("config.json"))
        self.assertTrue(file_utils.is_text_file("settings.yaml"))
        self.assertTrue(file_utils.is_text_file("data.csv"))
        self.assertTrue(file_utils.is_text_file("README.md"))

    def test_is_text_file_binary_files(self):
        """Test text file detection returns False for binary files."""
        self.assertFalse(file_utils.is_text_file("image.jpg"))
        self.assertFalse(file_utils.is_text_file("document.pdf"))
        self.assertFalse(file_utils.is_text_file("archive.zip"))
        self.assertFalse(file_utils.is_text_file("video.mp4"))

    def test_is_text_file_unknown_extension(self):
        """Test text file detection for unknown extensions."""
        self.assertFalse(file_utils.is_text_file("file.unknown"))
        self.assertFalse(file_utils.is_text_file("test"))

    def test_is_binary_file_image_files(self):
        """Test binary file detection for image files."""
        self.assertTrue(file_utils.is_binary_file("photo.jpg"))
        self.assertTrue(file_utils.is_binary_file("image.png"))
        self.assertTrue(file_utils.is_binary_file("logo.gif"))
        self.assertTrue(file_utils.is_binary_file("icon.ico"))

    def test_is_binary_file_document_files(self):
        """Test binary file detection for document files."""
        self.assertTrue(file_utils.is_binary_file("document.pdf"))
        self.assertTrue(file_utils.is_binary_file("spreadsheet.xlsx"))
        self.assertTrue(file_utils.is_binary_file("presentation.pptx"))
        self.assertTrue(file_utils.is_binary_file("text.docx"))

    def test_is_binary_file_archive_files(self):
        """Test binary file detection for archive files."""
        self.assertTrue(file_utils.is_binary_file("archive.zip"))
        self.assertTrue(file_utils.is_binary_file("backup.tar"))
        self.assertTrue(file_utils.is_binary_file("compressed.gz"))
        self.assertTrue(file_utils.is_binary_file("data.7z"))

    def test_is_binary_file_text_files(self):
        """Test binary file detection returns False for text files."""
        self.assertFalse(file_utils.is_binary_file("script.py"))
        self.assertFalse(file_utils.is_binary_file("data.json"))
        self.assertFalse(file_utils.is_binary_file("README.md"))
        self.assertFalse(file_utils.is_binary_file("style.css"))

    def test_is_binary_file_unknown_extension(self):
        """Test binary file detection for unknown extensions."""
        self.assertFalse(file_utils.is_binary_file("file.unknown"))
        self.assertFalse(file_utils.is_binary_file("test"))

    def test_read_file_text_file(self):
        """Test reading a text file."""
        test_content = "Hello, World!\nThis is a test file."
        
        # Create test file
        with open(self.test_text_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        result = file_utils.read_file(self.test_text_file)
        
        self.assertEqual(result, test_content)
        self.assertIsInstance(result, str)

    def test_read_file_python_file(self):
        """Test reading a Python file."""
        test_content = "#!/usr/bin/env python3\nprint('Hello, World!')\n"
        
        # Create test file
        with open(self.test_python_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        result = file_utils.read_file(self.test_python_file)
        
        self.assertEqual(result, test_content)
        self.assertIsInstance(result, str)

    def test_read_file_binary_file(self):
        """Test reading a binary file."""
        # Create a simple binary file (simulated JPEG header)
        test_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01'
        
        with open(self.test_binary_file, 'wb') as f:
            f.write(test_content)
        
        result = file_utils.read_file(self.test_binary_file)
        
        self.assertEqual(result, test_content)
        self.assertIsInstance(result, bytes)

    def test_read_file_nonexistent_file(self):
        """Test reading a non-existent file raises FileNotFoundError."""
        
        self.assert_error_behavior(
            file_utils.read_file,
            FileNotFoundError,
            f"File not found: {self.test_nonexistent_file}",
            file_path=self.test_nonexistent_file
        )

    def test_read_file_empty_text_file(self):
        """Test reading an empty text file."""
        # Create empty test file
        with open(self.test_text_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        result = file_utils.read_file(self.test_text_file)
        
        self.assertEqual(result, "")
        self.assertIsInstance(result, str)

    def test_read_file_unicode_content(self):
        """Test reading a text file with Unicode content."""
        test_content = "Hello, 世界! 🌍 Café résumé naïve"
        
        with open(self.test_text_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        result = file_utils.read_file(self.test_text_file)
        
        self.assertEqual(result, test_content)
        self.assertIsInstance(result, str)

    def test_write_file_text_content(self):
        """Test writing text content to a file."""
        test_content = "Hello, World!\nThis is a test."
        test_file = os.path.join(self.test_dir, "write_test.txt")
        
        file_utils.write_file(test_file, test_content)
        
        # Verify file was created and content is correct
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, test_content)

    def test_write_file_binary_content(self):
        """Test writing binary content to a file."""
        test_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01'
        test_file = os.path.join(self.test_dir, "write_test.jpg")
        
        file_utils.write_file(test_file, test_content)
        
        # Verify file was created and content is correct
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, test_content)

    def test_write_file_creates_directory(self):
        """Test that write_file creates directories if they don't exist."""
        nested_dir = os.path.join(self.test_dir, "nested", "deep", "directory")
        test_file = os.path.join(nested_dir, "test.txt")
        test_content = "Testing directory creation"
        
        file_utils.write_file(test_file, test_content)
        
        # Verify directory and file were created
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, test_content)

    def test_write_file_unicode_content(self):
        """Test writing Unicode text content to a file."""
        test_content = "Hello, 世界! 🌍 Café résumé naïve"
        test_file = os.path.join(self.test_dir, "unicode_test.txt")
        
        file_utils.write_file(test_file, test_content)
        
        # Verify file was created and Unicode content is correct
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, test_content)

    def test_write_file_overwrite_existing(self):
        """Test that write_file overwrites existing files."""
        test_file = os.path.join(self.test_dir, "overwrite_test.txt")
        original_content = "Original content"
        new_content = "New content"
        
        # Create original file
        file_utils.write_file(test_file, original_content)
        self.assertTrue(os.path.exists(test_file))
        
        # Overwrite with new content
        file_utils.write_file(test_file, new_content)
        
        # Verify content was overwritten
        with open(test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, new_content)

    def test_encode_file_to_base64_text_file(self):
        """Test encoding a text file to base64."""
        test_content = "Hello, World!"
        
        # Create test file
        with open(self.test_text_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        result = file_utils.encode_file_to_base64(self.test_text_file)
        
        # Verify it's a valid base64 string
        self.assertIsInstance(result, str)
        
        # Decode and verify content
        decoded_bytes = base64.b64decode(result)
        decoded_content = decoded_bytes.decode('utf-8')
        self.assertEqual(decoded_content, test_content)

    def test_encode_file_to_base64_binary_file(self):
        """Test encoding a binary file to base64."""
        test_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01'
        
        # Create test file
        with open(self.test_binary_file, 'wb') as f:
            f.write(test_content)
        
        result = file_utils.encode_file_to_base64(self.test_binary_file)
        
        # Verify it's a valid base64 string
        self.assertIsInstance(result, str)
        
        # Decode and verify content
        decoded_bytes = base64.b64decode(result)
        self.assertEqual(decoded_bytes, test_content)

    def test_encode_file_to_base64_empty_file(self):
        """Test encoding an empty file to base64."""
        # Create empty test file
        with open(self.test_text_file, 'w', encoding='utf-8') as f:
            f.write("")
        
        result = file_utils.encode_file_to_base64(self.test_text_file)
        
        # Verify it's a valid base64 string (empty content)
        self.assertIsInstance(result, str)
        decoded_bytes = base64.b64decode(result)
        self.assertEqual(decoded_bytes, b"")

    def test_encode_file_to_base64_nonexistent_file(self):
        """Test encoding a non-existent file raises FileNotFoundError."""
        self.assert_error_behavior(
            file_utils.encode_file_to_base64,
            FileNotFoundError,
            f"File not found: {self.test_nonexistent_file}",
            file_path=self.test_nonexistent_file
        )

    def test_decode_base64_to_file_text_content(self):
        """Test decoding base64 string to a text file."""
        original_content = "Hello, World! This is test content."
        base64_string = base64.b64encode(original_content.encode('utf-8')).decode('utf-8')
        test_file = os.path.join(self.test_dir, "decoded_test.txt")
        
        file_utils.decode_base64_to_file(base64_string, test_file)
        
        # Verify file was created and content is correct
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content.decode('utf-8'), original_content)

    def test_decode_base64_to_file_binary_content(self):
        """Test decoding base64 string to a binary file."""
        original_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01'
        base64_string = base64.b64encode(original_content).decode('utf-8')
        test_file = os.path.join(self.test_dir, "decoded_test.jpg")
        
        file_utils.decode_base64_to_file(base64_string, test_file)
        
        # Verify file was created and content is correct
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, original_content)

    def test_decode_base64_to_file_creates_directory(self):
        """Test that decode_base64_to_file creates directories if they don't exist."""
        original_content = "Test content"
        base64_string = base64.b64encode(original_content.encode('utf-8')).decode('utf-8')
        nested_dir = os.path.join(self.test_dir, "nested", "decode")
        test_file = os.path.join(nested_dir, "decoded_test.txt")
        
        file_utils.decode_base64_to_file(base64_string, test_file)
        
        # Verify directory and file were created
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(test_file))

    def test_decode_base64_to_file_empty_content(self):
        """Test decoding empty base64 string to file."""
        base64_string = base64.b64encode(b"").decode('utf-8')
        test_file = os.path.join(self.test_dir, "empty_decoded.txt")
        
        file_utils.decode_base64_to_file(base64_string, test_file)
        
        # Verify file was created and is empty
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, b"")

    @patch('mimetypes.guess_type')
    def test_get_mime_type_known_types(self, mock_guess_type):
        """Test getting MIME type for known file types."""
        # Test cases: (file_path, expected_mime_type)
        test_cases = [
            ("test.txt", "text/plain"),
            ("image.jpg", "image/jpeg"),
            ("document.pdf", "application/pdf"),
            ("data.json", "application/json"),
            ("style.css", "text/css"),
            ("script.js", "text/javascript"),
        ]
        
        for file_path, expected_mime in test_cases:
            mock_guess_type.return_value = (expected_mime, None)
            result = file_utils.get_mime_type(file_path)
            self.assertEqual(result, expected_mime)
            mock_guess_type.assert_called_with(file_path)

    @patch('mimetypes.guess_type')
    def test_get_mime_type_unknown_type(self, mock_guess_type):
        """Test getting MIME type for unknown file type returns default."""
        mock_guess_type.return_value = (None, None)
        
        result = file_utils.get_mime_type("unknown.xyz")
        
        self.assertEqual(result, "application/octet-stream")
        mock_guess_type.assert_called_with("unknown.xyz")

    @patch('mimetypes.guess_type')
    def test_get_mime_type_no_extension(self, mock_guess_type):
        """Test getting MIME type for file without extension."""
        mock_guess_type.return_value = (None, None)
        
        result = file_utils.get_mime_type("README")
        
        self.assertEqual(result, "application/octet-stream")
        mock_guess_type.assert_called_with("README")

    def test_roundtrip_text_file_base64_encoding(self):
        """Test roundtrip: text file -> base64 -> file -> read content matches."""
        original_content = "Hello, World!\nThis is a roundtrip test.\n🌍"
        
        # Write original file
        original_file = os.path.join(self.test_dir, "original.txt")
        file_utils.write_file(original_file, original_content)
        
        # Encode to base64
        base64_encoded = file_utils.encode_file_to_base64(original_file)
        
        # Decode to new file
        decoded_file = os.path.join(self.test_dir, "decoded.txt")
        file_utils.decode_base64_to_file(base64_encoded, decoded_file)
        
        # Read decoded file content
        decoded_content = file_utils.read_file(decoded_file)
        
        # Verify content matches
        self.assertEqual(decoded_content.encode('utf-8').decode('utf-8'), original_content)

    def test_roundtrip_binary_file_base64_encoding(self):
        """Test roundtrip: binary file -> base64 -> file -> read content matches."""
        original_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x02\x03\x04\x05'
        
        # Write original file
        original_file = os.path.join(self.test_dir, "original.jpg")
        file_utils.write_file(original_file, original_content)
        
        # Encode to base64
        base64_encoded = file_utils.encode_file_to_base64(original_file)
        
        # Decode to new file
        decoded_file = os.path.join(self.test_dir, "decoded.jpg")
        file_utils.decode_base64_to_file(base64_encoded, decoded_file)
        
        # Read decoded file content
        decoded_content = file_utils.read_file(decoded_file)
        
        # Verify content matches
        self.assertEqual(decoded_content, original_content)

    def test_file_extension_constants(self):
        """Test that the file extension constants contain expected extensions."""
        # Test some common text extensions
        self.assertIn('.py', file_utils.TEXT_EXTENSIONS)
        self.assertIn('.js', file_utils.TEXT_EXTENSIONS)
        self.assertIn('.json', file_utils.TEXT_EXTENSIONS)
        self.assertIn('.txt', file_utils.TEXT_EXTENSIONS)
        self.assertIn('.md', file_utils.TEXT_EXTENSIONS)
        
        # Test some common binary extensions
        self.assertIn('.jpg', file_utils.BINARY_EXTENSIONS)
        self.assertIn('.png', file_utils.BINARY_EXTENSIONS)
        self.assertIn('.pdf', file_utils.BINARY_EXTENSIONS)
        self.assertIn('.zip', file_utils.BINARY_EXTENSIONS)
        self.assertIn('.exe', file_utils.BINARY_EXTENSIONS)

if __name__ == "__main__":
    unittest.main()
