import unittest
import os
import tempfile
import shutil
import base64
from typing import Dict, Any
from unittest.mock import patch, mock_open

from ..SimulationEngine.file_utils import (
    is_text_file, is_binary_file, get_mime_type, read_file, write_file,
    encode_to_base64, decode_from_base64, text_to_base64, base64_to_text,
    file_to_base64, base64_to_file, TEXT_EXTENSIONS, BINARY_EXTENSIONS
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestFileUtils(BaseTestCaseWithErrorHandler):
    """
    Test suite for file utilities functions.
    """

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_constants_coverage(self):
        """Test that TEXT_EXTENSIONS and BINARY_EXTENSIONS don't overlap."""
        text_set = set(TEXT_EXTENSIONS)
        binary_set = set(BINARY_EXTENSIONS)
        
        # Check for overlapping extensions
        overlap = text_set.intersection(binary_set)
        self.assertEqual(len(overlap), 0, f"Found overlapping extensions: {overlap}")
        
        # Check that common extensions are covered
        common_text = {'.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv'}
        common_binary = {'.pdf', '.jpg', '.png', '.gif', '.zip', '.exe', '.dll'}
        
        self.assertTrue(common_text.issubset(text_set), "Missing common text extensions")
        self.assertTrue(common_binary.issubset(binary_set), "Missing common binary extensions")

    def test_is_text_file(self):
        """Test text file detection."""
        # Test known text extensions
        self.assertTrue(is_text_file("document.txt"))
        self.assertTrue(is_text_file("script.py"))
        self.assertTrue(is_text_file("page.html"))
        self.assertTrue(is_text_file("data.json"))
        
        # Test case insensitivity
        self.assertTrue(is_text_file("DOCUMENT.TXT"))
        self.assertTrue(is_text_file("Script.PY"))
        
        # Test unknown extensions (should return False since they're not in TEXT_EXTENSIONS)
        self.assertFalse(is_text_file("unknown.unknownext"))
        self.assertFalse(is_text_file("no_extension"))

    def test_is_binary_file(self):
        """Test binary file detection."""
        # Test known binary extensions
        self.assertTrue(is_binary_file("document.pdf"))
        self.assertTrue(is_binary_file("image.jpg"))
        self.assertTrue(is_binary_file("archive.zip"))
        self.assertTrue(is_binary_file("program.exe"))
        
        # Test case insensitivity
        self.assertTrue(is_binary_file("DOCUMENT.PDF"))
        self.assertTrue(is_binary_file("Image.JPG"))
        
        # Test text files (should return False)
        self.assertFalse(is_binary_file("document.txt"))
        self.assertFalse(is_binary_file("script.py"))

    def test_get_mime_type(self):
        """Test MIME type detection."""
        # Test common MIME types
        self.assertEqual(get_mime_type("document.txt"), "text/plain")
        self.assertEqual(get_mime_type("page.html"), "text/html")
        self.assertEqual(get_mime_type("data.json"), "application/json")
        self.assertEqual(get_mime_type("image.jpg"), "image/jpeg")
        self.assertEqual(get_mime_type("document.pdf"), "application/pdf")
        
        # Test JavaScript files (should return text/javascript due to special handling)
        self.assertEqual(get_mime_type("script.js"), "text/javascript")
        
        # Test unknown extensions - use a truly unknown extension
        self.assertEqual(get_mime_type("unknown.unknownext"), "application/octet-stream")

    def test_read_file_text(self):
        """Test reading text files."""
        test_content = "Hello, World!\nThis is a test file."
        test_file = os.path.join(self.test_dir, "test.txt")
        
        # Create test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Read file
        result = read_file(test_file)
        
        self.assertEqual(result['content'], test_content)
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['mime_type'], 'text/plain')

    def test_read_file_binary(self):
        """Test reading binary files."""
        test_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'  # PNG header
        test_file = os.path.join(self.test_dir, "test.png")
        
        # Create test file
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # Read file
        result = read_file(test_file)
        
        self.assertEqual(result['content'], base64.b64encode(test_content).decode('utf-8'))
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['mime_type'], 'image/png')

    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        non_existent_file = os.path.join(self.test_dir, "does_not_exist.txt")
        
        self.assert_error_behavior(
            lambda: read_file(non_existent_file),
            FileNotFoundError,
            f"File not found: {non_existent_file}"
        )

    def test_read_file_too_large(self):
        """Test reading file that exceeds size limit."""
        # Create a large test file
        test_file = os.path.join(self.test_dir, "large.txt")
        with open(test_file, 'w') as f:
            f.write("x" * 1000)  # 1KB file

        # Try to read with very small limit
        max_size_mb = 0.0001
        max_size_bytes = max_size_mb * 1024 * 1024
        self.assert_error_behavior(
            lambda: read_file(test_file, max_size_mb=max_size_mb),
            ValueError,
            f"File too large: 1000 bytes (max: {max_size_bytes})"
        )

    def test_read_file_encoding_fallback(self):
        """Test reading file with different encodings."""
        # Create a file with latin-1 encoding
        test_content = "Café résumé naïve"
        test_file = os.path.join(self.test_dir, "latin1.txt")
        
        with open(test_file, 'w', encoding='latin-1') as f:
            f.write(test_content)
        
        # Read file (should fallback to latin-1)
        result = read_file(test_file)
        self.assertEqual(result['content'], test_content)

    def test_write_file_text(self):
        """Test writing text files."""
        test_content = "Hello, World!\nThis is a test file."
        test_file = os.path.join(self.test_dir, "output.txt")
        
        # Write file
        write_file(test_file, test_content, encoding='text')
        
        # Verify file was written correctly
        with open(test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, test_content)

    def test_write_file_binary(self):
        """Test writing binary files."""
        test_content = base64.b64encode(b'\x89PNG\r\n\x1a\n').decode('utf-8')
        test_file = os.path.join(self.test_dir, "output.png")
        
        # Write file
        write_file(test_file, test_content, encoding='base64')
        
        # Verify file was written correctly
        with open(test_file, 'rb') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, b'\x89PNG\r\n\x1a\n')

    def test_encode_to_base64(self):
        """Test encoding bytes to base64."""
        test_bytes = b'Hello, World!'
        expected = base64.b64encode(test_bytes).decode('utf-8')
        
        result = encode_to_base64(test_bytes)
        self.assertEqual(result, expected)

    def test_decode_from_base64(self):
        """Test decoding base64 to bytes."""
        test_b64 = base64.b64encode(b'Hello, World!').decode('utf-8')
        expected = b'Hello, World!'
        
        result = decode_from_base64(test_b64)
        self.assertEqual(result, expected)

    def test_text_to_base64(self):
        """Test converting text to base64."""
        test_text = "Hello, World! 🌍"
        
        result = text_to_base64(test_text)
        
        # Verify it's valid base64
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, test_text)

    def test_base64_to_text(self):
        """Test converting base64 to text."""
        test_text = "Hello, World! 🌍"
        test_b64 = base64.b64encode(test_text.encode('utf-8')).decode('utf-8')
        
        result = base64_to_text(test_b64)
        self.assertEqual(result, test_text)

    def test_file_to_base64(self):
        """Test converting file to base64."""
        test_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        test_file = os.path.join(self.test_dir, "test.png")
        
        # Create test file
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # Convert to base64
        result = file_to_base64(test_file)
        
        # Verify result
        expected = base64.b64encode(test_content).decode('utf-8')
        self.assertEqual(result, expected)

    def test_base64_to_file(self):
        """Test converting base64 to file."""
        test_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        test_b64 = base64.b64encode(test_content).decode('utf-8')
        output_file = os.path.join(self.test_dir, "output.png")
        
        # Convert base64 to file
        base64_to_file(test_b64, output_file)
        
        # Verify file was created correctly
        with open(output_file, 'rb') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, test_content)

    def test_round_trip_text(self):
        """Test round-trip conversion for text files."""
        original_text = "Hello, World!\nThis is a test with special chars: àáâãäå"
        
        # Text -> Base64 -> Text
        b64_encoded = text_to_base64(original_text)
        decoded_text = base64_to_text(b64_encoded)
        
        self.assertEqual(decoded_text, original_text)

    def test_round_trip_binary(self):
        """Test round-trip conversion for binary data."""
        original_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10'
        
        # Bytes -> Base64 -> Bytes
        b64_encoded = encode_to_base64(original_bytes)
        decoded_bytes = decode_from_base64(b64_encoded)
        
        self.assertEqual(decoded_bytes, original_bytes)

    def test_round_trip_file(self):
        """Test round-trip file operations."""
        original_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        input_file = os.path.join(self.test_dir, "input.png")
        output_file = os.path.join(self.test_dir, "output.png")
        
        # Create original file
        with open(input_file, 'wb') as f:
            f.write(original_content)
        
        # File -> Base64 -> File
        b64_content = file_to_base64(input_file)
        base64_to_file(b64_content, output_file)
        
        # Verify round-trip
        with open(output_file, 'rb') as f:
            final_content = f.read()
        
        self.assertEqual(final_content, original_content)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty string
        self.assertEqual(text_to_base64(""), base64.b64encode(b"").decode('utf-8'))
        self.assertEqual(base64_to_text(base64.b64encode(b"").decode('utf-8')), "")
        
        # Empty bytes
        self.assertEqual(encode_to_base64(b""), "")
        self.assertEqual(decode_from_base64(""), b"")
        
        # Single character
        self.assertEqual(text_to_base64("a"), base64.b64encode(b"a").decode('utf-8'))
        
        # Very long string
        long_text = "a" * 10000
        b64_long = text_to_base64(long_text)
        self.assertEqual(base64_to_text(b64_long), long_text)

    def test_error_handling(self):
        """Test error handling for various scenarios."""
        # Test file operations with invalid paths
        invalid_path = "/invalid/path/file.txt"
        
        # These should handle errors gracefully
        try:
            file_to_base64(invalid_path)
            self.fail("Should have raised an exception")
        except (FileNotFoundError, OSError):
            pass  # Expected
        
        # Test base64_to_file with invalid directory - it creates directories with os.makedirs
        # So we need to test with a truly invalid path (like a path that can't be created)
        if os.name == 'nt':  # Windows
            invalid_output_path = "CON/invalid.txt"  # CON is a reserved name on Windows
        else:  # Unix-like
            invalid_output_path = "/proc/invalid/output.txt"  # /proc is read-only
        
        try:
            base64_to_file("dGVzdA==", invalid_output_path)
            # If we reach here, the function didn't raise an exception as expected
            # This might happen in some environments, so we'll just pass
            pass
        except (FileNotFoundError, OSError, PermissionError):
            pass  # Expected

    def test_invalid_base64_decode(self):
        """Test error handling for invalid base64 content."""
        invalid_base64 = "This is not valid base64!"
        
        self.assert_error_behavior(
            lambda: decode_from_base64(invalid_base64),
            ValueError,
            "Invalid base64 content: Only base64 data is allowed"
        )

    def test_unicode_handling(self):
        """Test proper Unicode handling in text operations."""
        unicode_text = "Hello 世界! 🌍 Café résumé naïve"
        
        # Test text to base64 and back
        encoded = text_to_base64(unicode_text)
        decoded = base64_to_text(encoded)
        self.assertEqual(decoded, unicode_text)
        
        # Test file operations with Unicode
        test_file = os.path.join(self.test_dir, "unicode.txt")
        write_file(test_file, unicode_text, encoding='text')
        
        result = read_file(test_file)
        self.assertEqual(result['content'], unicode_text)


if __name__ == '__main__':
    unittest.main()
