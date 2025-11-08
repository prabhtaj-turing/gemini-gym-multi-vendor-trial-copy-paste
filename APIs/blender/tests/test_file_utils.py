"""
Comprehensive test suite for SimulationEngine.file_utils.py
Tests all file utility functions including file type detection, I/O operations, and encoding/decoding.
"""
import base64
import binascii
import os
import tempfile
import unittest
import shutil
from unittest.mock import patch, mock_open

from common_utils.base_case import BaseTestCaseWithErrorHandler
from blender.SimulationEngine import file_utils


class TestFileTypeDetection(BaseTestCaseWithErrorHandler):
    """Test file type detection functions."""

    def test_is_text_file_basic_extensions(self):
        """Test is_text_file with basic text file extensions."""
        text_files = [
            "script.py", "config.json", "page.html", "style.css",
            "notes.txt", "README.md", "data.csv", "script.js",
            "code.cpp", "schema.sql", "settings.ini", "script.sh"
        ]
        
        for filename in text_files:
            with self.subTest(filename=filename):
                self.assertTrue(file_utils.is_text_file(filename), 
                              f"Expected {filename} to be detected as text file")

    def test_is_text_file_case_insensitive(self):
        """Test is_text_file is case insensitive."""
        test_cases = [
            ("SCRIPT.PY", True),
            ("CONFIG.JSON", True),
            ("NOTES.TXT", True),
            ("file.PY", True),
            ("FILE.py", True)
        ]
        
        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                result = file_utils.is_text_file(filename)
                self.assertEqual(result, expected)

    def test_is_text_file_with_paths(self):
        """Test is_text_file with full file paths."""
        test_paths = [
            "/path/to/script.py",
            "C:\\Users\\test\\config.json",
            "../relative/path/notes.txt",
            "./local/file.js"
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                self.assertTrue(file_utils.is_text_file(path))

    def test_is_binary_file_basic_extensions(self):
        """Test is_binary_file with basic binary file extensions."""
        binary_files = [
            "image.jpg", "photo.png", "document.pdf", "archive.zip",
            "video.mp4", "audio.mp3", "program.exe", "database.db",
            "font.ttf", "model.blend"
        ]
        
        for filename in binary_files:
            with self.subTest(filename=filename):
                self.assertTrue(file_utils.is_binary_file(filename),
                              f"Expected {filename} to be detected as binary file")

    def test_is_binary_file_case_insensitive(self):
        """Test is_binary_file is case insensitive."""
        test_cases = [
            ("IMAGE.JPG", True),
            ("DOCUMENT.PDF", True),
            ("VIDEO.MP4", True),
            ("file.JPG", True),
            ("FILE.jpg", True)
        ]
        
        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                result = file_utils.is_binary_file(filename)
                self.assertEqual(result, expected)

    def test_svg_file_classification(self):
        """Test that SVG files are correctly classified as text files."""
        # SVG is both in TEXT_EXTENSIONS and BINARY_EXTENSIONS
        # but is_text_file should be checked first
        self.assertTrue(file_utils.is_text_file("image.svg"))
        self.assertTrue(file_utils.is_binary_file("image.svg"))  # This is also true

    def test_unknown_extension(self):
        """Test files with unknown extensions."""
        unknown_files = [
            "file.xyz", "document.unknown", "test.abc123"
        ]
        
        for filename in unknown_files:
            with self.subTest(filename=filename):
                self.assertFalse(file_utils.is_text_file(filename))
                self.assertFalse(file_utils.is_binary_file(filename))

    def test_no_extension(self):
        """Test files with no extension."""
        no_ext_files = [
            "README", "Makefile", "Dockerfile", "script"
        ]
        
        for filename in no_ext_files:
            with self.subTest(filename=filename):
                self.assertFalse(file_utils.is_text_file(filename))
                self.assertFalse(file_utils.is_binary_file(filename))

    def test_get_mime_type_common_files(self):
        """Test get_mime_type for common file types."""
        mime_tests = [
            ("script.py", "text/x-python"),
            ("config.json", "application/json"),
            ("page.html", "text/html"),
            ("style.css", "text/css"),
            ("notes.txt", "text/plain"),
            ("image.jpg", "image/jpeg"),
            ("photo.png", "image/png"),
            ("document.pdf", "application/pdf"),
            ("video.mp4", "video/mp4"),
            ("audio.mp3", "audio/mpeg")
        ]
        
        for filename, expected_mime in mime_tests:
            with self.subTest(filename=filename):
                result = file_utils.get_mime_type(filename)
                self.assertEqual(result, expected_mime)

    def test_extension_constants_coverage(self):
        """Test that extension constants contain expected values."""
        # Test TEXT_EXTENSIONS
        expected_text_extensions = [
            '.py', '.js', '.html', '.css', '.json', '.txt', '.md',
            '.csv', '.sql', '.xml', '.yaml', '.ini', '.sh'
        ]
        
        for ext in expected_text_extensions:
            with self.subTest(ext=ext):
                self.assertIn(ext, file_utils.TEXT_EXTENSIONS)

        # Test BINARY_EXTENSIONS
        expected_binary_extensions = [
            '.jpg', '.png', '.pdf', '.zip', '.mp4', '.mp3',
            '.exe', '.db', '.ttf', '.blend'
        ]
        
        for ext in expected_binary_extensions:
            with self.subTest(ext=ext):
                self.assertIn(ext, file_utils.BINARY_EXTENSIONS)


class TestFileIO(BaseTestCaseWithErrorHandler):
    """Test file I/O operations."""

    def setUp(self):
        """Set up temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def _create_test_file(self, filename, content, mode='w', encoding='utf-8'):
        """Helper method to create test files."""
        filepath = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if 'b' in mode:
            with open(filepath, mode) as f:
                f.write(content)
        else:
            with open(filepath, mode, encoding=encoding) as f:
                f.write(content)
        return filepath

    def test_read_file_text_utf8(self):
        """Test reading UTF-8 text file."""
        content = "Hello, World!\nThis is a test file.\n中文测试"
        filepath = self._create_test_file("test.txt", content)
        
        result = file_utils.read_file(filepath)
        
        # On Windows, file content might have \r\n while our original content has \n
        # So we compare by reading the actual file content to see what was written
        with open(filepath, 'r', encoding='utf-8') as f:
            actual_file_content = f.read()
        
        self.assertEqual(result["content"], actual_file_content)
        self.assertEqual(result["encoding"], "text")
        self.assertEqual(result["mime_type"], "text/plain")
        # Calculate expected size based on actual file size
        actual_file_size = os.path.getsize(filepath)
        self.assertEqual(result["size_bytes"], actual_file_size)

    def test_read_file_text_with_fallback_encoding(self):
        """Test reading text file with fallback encoding."""
        # Create file with Latin-1 content
        content_bytes = b"Caf\xe9 - This is Latin-1 content"
        filepath = os.path.join(self.test_dir, "latin1.txt")
        with open(filepath, 'wb') as f:
            f.write(content_bytes)
        
        result = file_utils.read_file(filepath)
        
        self.assertEqual(result["encoding"], "text")
        self.assertIn("Café", result["content"])

    def test_read_file_binary(self):
        """Test reading binary file."""
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        filepath = os.path.join(self.test_dir, "test.png")
        with open(filepath, 'wb') as f:
            f.write(binary_content)
        
        result = file_utils.read_file(filepath)
        
        self.assertEqual(result["encoding"], "base64")
        self.assertEqual(result["mime_type"], "image/png")
        self.assertEqual(result["size_bytes"], len(binary_content))
        
        # Verify base64 content can be decoded back
        decoded = base64.b64decode(result["content"])
        self.assertEqual(decoded, binary_content)

    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        with self.assertRaises(FileNotFoundError) as cm:
            file_utils.read_file("/nonexistent/file.txt")
        self.assertIn("File not found", str(cm.exception))

    def test_read_file_too_large(self):
        """Test reading file that exceeds size limit."""
        content = "x" * 1000  # 1KB content
        filepath = self._create_test_file("large.txt", content)
        
        with self.assertRaises(ValueError) as cm:
            file_utils.read_file(filepath, max_size_mb=0.0001)  # Very small limit
        self.assertIn("File too large", str(cm.exception))

    def test_read_file_empty(self):
        """Test reading empty file."""
        filepath = self._create_test_file("empty.txt", "")
        
        result = file_utils.read_file(filepath)
        
        self.assertEqual(result["content"], "")
        self.assertEqual(result["size_bytes"], 0)
        self.assertEqual(result["encoding"], "text")

    def test_write_file_text(self):
        """Test writing text file."""
        content = "Hello, World!\nThis is a test.\n中文测试"
        filepath = os.path.join(self.test_dir, "output.txt")
        
        file_utils.write_file(filepath, content, encoding="text")
        
        # Verify file was written correctly
        with open(filepath, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)

    def test_write_file_text_creates_directories(self):
        """Test that write_file creates missing directories."""
        content = "Test content"
        filepath = os.path.join(self.test_dir, "subdir", "nested", "file.txt")
        
        file_utils.write_file(filepath, content, encoding="text")
        
        # Verify file and directories were created
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_write_file_binary_from_base64_string(self):
        """Test writing binary file from base64 string."""
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        base64_content = base64.b64encode(binary_content).decode('utf-8')
        filepath = os.path.join(self.test_dir, "output.png")
        
        file_utils.write_file(filepath, base64_content, encoding="base64")
        
        # Verify file was written correctly
        with open(filepath, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, binary_content)

    def test_write_file_binary_from_bytes(self):
        """Test writing binary file from bytes directly."""
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        filepath = os.path.join(self.test_dir, "output.png")
        
        file_utils.write_file(filepath, binary_content, encoding="base64")
        
        # Verify file was written correctly
        with open(filepath, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, binary_content)

    def test_write_file_text_from_bytes(self):
        """Test writing text file from bytes."""
        content_bytes = "Hello, World!".encode('utf-8')
        filepath = os.path.join(self.test_dir, "output.txt")
        
        file_utils.write_file(filepath, content_bytes, encoding="text")
        
        # Verify file was written correctly
        with open(filepath, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, "Hello, World!")

    def test_write_file_overwrites_existing(self):
        """Test that writing overwrites existing file."""
        filepath = os.path.join(self.test_dir, "overwrite.txt")
        
        # Write initial content
        file_utils.write_file(filepath, "Original content", "text")
        
        # Overwrite with new content
        file_utils.write_file(filepath, "New content", "text")
        
        # Verify only new content remains
        with open(filepath, 'r') as f:
            content = f.read()
        self.assertEqual(content, "New content")


class TestEncodingDecoding(BaseTestCaseWithErrorHandler):
    """Test encoding and decoding functions."""

    def test_encode_to_base64_from_string(self):
        """Test base64 encoding from string."""
        text = "Hello, World! 中文测试"
        result = file_utils.encode_to_base64(text)
        
        # Verify it's valid base64 and can be decoded
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, text)

    def test_encode_to_base64_from_bytes(self):
        """Test base64 encoding from bytes."""
        data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        result = file_utils.encode_to_base64(data)
        
        # Verify it's valid base64 and can be decoded
        decoded = base64.b64decode(result)
        self.assertEqual(decoded, data)

    def test_decode_from_base64(self):
        """Test base64 decoding to bytes."""
        original_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        base64_data = base64.b64encode(original_data).decode('utf-8')
        
        result = file_utils.decode_from_base64(base64_data)
        
        self.assertEqual(result, original_data)
        self.assertIsInstance(result, bytes)

    def test_text_to_base64(self):
        """Test text to base64 conversion."""
        text = "Hello, World! 中文测试"
        result = file_utils.text_to_base64(text)
        
        # Verify it can be decoded back
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, text)

    def test_base64_to_text(self):
        """Test base64 to text conversion."""
        text = "Hello, World! 中文测试"
        base64_data = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
        result = file_utils.base64_to_text(base64_data)
        
        self.assertEqual(result, text)

    def test_encode_decode_roundtrip(self):
        """Test encoding and decoding roundtrip."""
        test_data = [
            "Simple text",
            "Text with unicode: 中文测试 🚀",
            "",  # Empty string
            "Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?",
            "Line\nbreaks\r\nand\ttabs"
        ]
        
        for text in test_data:
            with self.subTest(text=text):
                # String -> Base64 -> String
                encoded = file_utils.text_to_base64(text)
                decoded = file_utils.base64_to_text(encoded)
                self.assertEqual(decoded, text)
                
                # Also test via encode/decode functions
                encoded2 = file_utils.encode_to_base64(text)
                decoded2 = file_utils.decode_from_base64(encoded2).decode('utf-8')
                self.assertEqual(decoded2, text)

    def test_binary_data_roundtrip(self):
        """Test binary data encoding/decoding roundtrip."""
        test_data = [
            b'',  # Empty bytes
            b'\x00\x01\x02\x03',  # Binary data with null bytes
            b'\xff' * 100,  # Repeated byte pattern
            "Hello World".encode('utf-8'),  # UTF-8 text as bytes
        ]
        
        for data in test_data:
            with self.subTest(data=data):
                encoded = file_utils.encode_to_base64(data)
                decoded = file_utils.decode_from_base64(encoded)
                self.assertEqual(decoded, data)


class TestFileBase64Operations(BaseTestCaseWithErrorHandler):
    """Test file-to-base64 and base64-to-file operations."""

    def setUp(self):
        """Set up temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_file_to_base64(self):
        """Test reading file and converting to base64."""
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        filepath = os.path.join(self.test_dir, "test.png")
        with open(filepath, 'wb') as f:
            f.write(binary_content)
        
        result = file_utils.file_to_base64(filepath)
        
        # Verify result can be decoded back to original content
        decoded = base64.b64decode(result)
        self.assertEqual(decoded, binary_content)

    def test_base64_to_file(self):
        """Test writing base64 content to file."""
        binary_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        base64_data = base64.b64encode(binary_content).decode('utf-8')
        filepath = os.path.join(self.test_dir, "subdir", "output.png")
        
        file_utils.base64_to_file(base64_data, filepath)
        
        # Verify file was written correctly and directory was created
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, binary_content)

    def test_file_base64_roundtrip(self):
        """Test file -> base64 -> file roundtrip."""
        original_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x12\x34\x56\x78'
        original_file = os.path.join(self.test_dir, "original.png")
        roundtrip_file = os.path.join(self.test_dir, "roundtrip.png")
        
        # Create original file
        with open(original_file, 'wb') as f:
            f.write(original_content)
        
        # File -> Base64 -> File
        base64_data = file_utils.file_to_base64(original_file)
        file_utils.base64_to_file(base64_data, roundtrip_file)
        
        # Verify roundtrip file matches original
        with open(roundtrip_file, 'rb') as f:
            roundtrip_content = f.read()
        self.assertEqual(roundtrip_content, original_content)

    def test_file_to_base64_text_file(self):
        """Test file_to_base64 with text file."""
        text_content = "Hello, World!\n中文测试"
        filepath = os.path.join(self.test_dir, "test.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        result = file_utils.file_to_base64(filepath)
        
        # Verify result can be decoded back to original content
        decoded = base64.b64decode(result).decode('utf-8')
        # Normalize line endings since Windows might change \n to \r\n
        expected_content = text_content.replace('\n', os.linesep)
        self.assertEqual(decoded, expected_content)

    def test_base64_to_file_creates_directories(self):
        """Test that base64_to_file creates missing directories."""
        binary_content = b'\x89PNG\r\n\x1a\n'
        base64_data = base64.b64encode(binary_content).decode('utf-8')
        nested_path = os.path.join(self.test_dir, "deep", "nested", "path", "file.png")
        
        file_utils.base64_to_file(base64_data, nested_path)
        
        # Verify file and directories were created
        self.assertTrue(os.path.exists(nested_path))
        with open(nested_path, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, binary_content)


class TestEdgeCases(BaseTestCaseWithErrorHandler):
    """Test edge cases and special scenarios."""

    def setUp(self):
        """Set up temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_empty_file_operations(self):
        """Test operations with empty files."""
        # Empty text file
        empty_text_file = os.path.join(self.test_dir, "empty.txt")
        with open(empty_text_file, 'w') as f:
            pass  # Create empty file
        
        result = file_utils.read_file(empty_text_file)
        self.assertEqual(result["content"], "")
        self.assertEqual(result["size_bytes"], 0)
        
        # Empty binary file
        empty_binary_file = os.path.join(self.test_dir, "empty.bin")
        with open(empty_binary_file, 'wb') as f:
            pass  # Create empty file
        
        base64_result = file_utils.file_to_base64(empty_binary_file)
        self.assertEqual(base64_result, "")  # Empty bytes encode to empty string

    def test_large_file_handling(self):
        """Test handling of larger files within limits."""
        # Create 1MB file
        large_content = "x" * (1024 * 1024)
        filepath = os.path.join(self.test_dir, "large.txt")
        with open(filepath, 'w') as f:
            f.write(large_content)
        
        result = file_utils.read_file(filepath, max_size_mb=2)  # 2MB limit
        
        self.assertEqual(len(result["content"]), 1024 * 1024)
        self.assertEqual(result["encoding"], "text")

    def test_unicode_filename_handling(self):
        """Test handling of Unicode characters in filenames."""
        unicode_filename = os.path.join(self.test_dir, "测试文件.txt")
        content = "Unicode filename test"
        
        file_utils.write_file(unicode_filename, content, "text")
        
        self.assertTrue(os.path.exists(unicode_filename))
        result = file_utils.read_file(unicode_filename)
        self.assertEqual(result["content"], content)

    def test_special_characters_in_content(self):
        """Test handling of special characters in file content."""
        special_content = "Special chars: \x00\x01\x02\x03\xff\xfe\xfd"
        filepath = os.path.join(self.test_dir, "special.txt")
        
        # Write as binary since it contains null bytes
        with open(filepath, 'wb') as f:
            f.write(special_content.encode('latin-1'))
        
        # Should be read as binary since it has .txt but contains problematic bytes
        result = file_utils.read_file(filepath)
        # The function should handle this gracefully, either as text or binary

    def test_very_long_filename(self):
        """Test handling of very long filenames."""
        long_name = "a" * 200 + ".txt"
        filepath = os.path.join(self.test_dir, long_name)
        content = "Long filename test"
        
        try:
            file_utils.write_file(filepath, content, "text")
            result = file_utils.read_file(filepath)
            self.assertEqual(result["content"], content)
        except OSError:
            # Some systems have filename length limits, which is acceptable
            pass


if __name__ == '__main__':
    unittest.main()
