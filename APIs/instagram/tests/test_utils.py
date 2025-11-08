"""
Instagram SimulationEngine Utility Functions Test Suite

This test suite validates all utility functions from the SimulationEngine directory,
ensuring they work correctly under normal conditions and handle error cases properly.
These utilities are critical for file operations, encoding/decoding, and data handling.
"""

import unittest
import os
import tempfile
import base64

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestInstagramFileUtils(BaseTestCaseWithErrorHandler):
    """
    Test suite for Instagram file utility functions.

    These tests verify file detection, reading, writing, and encoding/decoding
    functionality works correctly. Critical for file handling operations
    throughout the Instagram simulation system.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Import file utils module
        import instagram.SimulationEngine.file_utils as file_utils

        self.file_utils = file_utils

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

        # Test data
        self.test_text = "Hello, World! This is a test file.\nWith multiple lines.\n"
        self.test_binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        self.test_base64 = base64.b64encode(self.test_binary_data).decode("utf-8")

        # Create test files
        self.text_file = os.path.join(self.temp_dir, "test.txt")
        self.python_file = os.path.join(self.temp_dir, "test.py")
        self.binary_file = os.path.join(self.temp_dir, "test.png")
        self.nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")

        # Write test files
        with open(self.text_file, "w", encoding="utf-8") as f:
            f.write(self.test_text)

        with open(self.python_file, "w", encoding="utf-8") as f:
            f.write("# Python test file\nprint('Hello, World!')\n")

        with open(self.binary_file, "wb") as f:
            f.write(self.test_binary_data)

    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestFileTypeDetection(TestInstagramFileUtils):
    """Test file type detection utility functions."""

    def test_is_text_file_with_common_text_extensions(self):
        """
        Test is_text_file with common text file extensions.

        Verifies that common text file extensions are correctly identified
        as text files. This is essential for proper file handling.
        """
        text_files = [
            "test.txt",
            "script.py",
            "code.js",
            "style.css",
            "data.json",
            "readme.md",
            "config.yml",
            "database.sql",
            "markup.html",
        ]

        for filename in text_files:
            with self.subTest(filename=filename):
                result = self.file_utils.is_text_file(filename)
                self.assertTrue(result, f"{filename} should be detected as text file")

    def test_is_text_file_with_uppercase_extensions(self):
        """
        Test is_text_file with uppercase extensions.

        Verifies that file extension detection is case-insensitive,
        which is important for cross-platform compatibility.
        """
        uppercase_files = ["FILE.TXT", "SCRIPT.PY", "STYLE.CSS"]

        for filename in uppercase_files:
            with self.subTest(filename=filename):
                result = self.file_utils.is_text_file(filename)
                self.assertTrue(result, f"{filename} should be detected as text file")

    def test_is_binary_file_with_common_binary_extensions(self):
        """
        Test is_binary_file with common binary file extensions.

        Verifies that common binary file extensions are correctly identified
        as binary files. Critical for proper file encoding/decoding.
        """
        binary_files = [
            "image.png",
            "photo.jpg",
            "document.pdf",
            "archive.zip",
            "audio.mp3",
            "video.mp4",
            "executable.exe",
            "library.dll",
        ]

        for filename in binary_files:
            with self.subTest(filename=filename):
                result = self.file_utils.is_binary_file(filename)
                self.assertTrue(result, f"{filename} should be detected as binary file")

    def test_is_binary_file_with_uppercase_extensions(self):
        """
        Test is_binary_file with uppercase extensions.

        Verifies that binary file detection is case-insensitive.
        """
        uppercase_binary = ["IMAGE.PNG", "PHOTO.JPG", "DOCUMENT.PDF"]

        for filename in uppercase_binary:
            with self.subTest(filename=filename):
                result = self.file_utils.is_binary_file(filename)
                self.assertTrue(result, f"{filename} should be detected as binary file")

    def test_unknown_extension_detection(self):
        """
        Test file type detection with unknown extensions.

        Verifies that files with unknown extensions return False for both
        text and binary detection, ensuring predictable behavior.
        """
        unknown_files = ["file.unknown", "test.xyz", "data.customext"]

        for filename in unknown_files:
            with self.subTest(filename=filename):
                is_text = self.file_utils.is_text_file(filename)
                is_binary = self.file_utils.is_binary_file(filename)
                self.assertFalse(is_text, f"{filename} should not be detected as text")
                self.assertFalse(
                    is_binary, f"{filename} should not be detected as binary"
                )

    def test_file_without_extension(self):
        """
        Test file type detection for files without extensions.

        Verifies that files without extensions are handled gracefully.
        """
        no_ext_files = ["README", "Makefile", "dockerfile"]

        for filename in no_ext_files:
            with self.subTest(filename=filename):
                is_text = self.file_utils.is_text_file(filename)
                is_binary = self.file_utils.is_binary_file(filename)
                self.assertFalse(is_text, f"{filename} should not be detected as text")
                self.assertFalse(
                    is_binary, f"{filename} should not be detected as binary"
                )


class TestMimeTypeDetection(TestInstagramFileUtils):
    """Test MIME type detection utility functions."""

    def test_get_mime_type_for_common_files(self):
        """
        Test MIME type detection for common file types.

        Verifies that common file types return appropriate MIME types,
        which is important for proper content handling and HTTP responses.
        """
        mime_tests = [
            ("test.txt", "text/plain"),
            ("test.html", "text/html"),
            ("test.css", "text/css"),
            ("test.js", "text/javascript"),
            ("test.json", "application/json"),
            ("test.png", "image/png"),
            ("test.jpg", "image/jpeg"),
            ("test.pdf", "application/pdf"),
        ]

        for filename, expected_mime in mime_tests:
            with self.subTest(filename=filename):
                result = self.file_utils.get_mime_type(filename)
                self.assertEqual(
                    result,
                    expected_mime,
                    f"MIME type for {filename} should be {expected_mime}",
                )

    def test_get_mime_type_for_unknown_extension(self):
        """
        Test MIME type detection for unknown file extensions.

        Verifies that unknown extensions return the default MIME type,
        ensuring graceful handling of unrecognized files.
        """
        unknown_files = ["file.unknown", "test.fakext", "data.customext"]

        for filename in unknown_files:
            with self.subTest(filename=filename):
                result = self.file_utils.get_mime_type(filename)
                self.assertEqual(
                    result,
                    "application/octet-stream",
                    f"Unknown file {filename} should return default MIME type",
                )

    def test_get_mime_type_case_insensitive(self):
        """
        Test MIME type detection is case-insensitive.

        Verifies that MIME type detection works regardless of case,
        important for cross-platform compatibility.
        """
        case_tests = [
            ("FILE.TXT", "text/plain"),
            ("IMAGE.PNG", "image/png"),
            ("DOCUMENT.PDF", "application/pdf"),
        ]

        for filename, expected_mime in case_tests:
            with self.subTest(filename=filename):
                result = self.file_utils.get_mime_type(filename)
                self.assertEqual(
                    result,
                    expected_mime,
                    f"MIME type detection should be case-insensitive for {filename}",
                )


class TestFileReading(TestInstagramFileUtils):
    """Test file reading utility functions."""

    def test_read_text_file_success(self):
        """
        Test successful reading of text files.

        Verifies that text files are read correctly with proper metadata,
        including content, encoding, MIME type, and file size.
        """
        result = self.file_utils.read_file(self.text_file)

        # Verify return structure
        self.assertIsInstance(result, dict, "read_file should return a dictionary")
        self.assertIn("content", result, "Result should contain 'content' key")
        self.assertIn("encoding", result, "Result should contain 'encoding' key")
        self.assertIn("mime_type", result, "Result should contain 'mime_type' key")
        self.assertIn("size_bytes", result, "Result should contain 'size_bytes' key")

        # Verify content
        self.assertEqual(
            result["content"], self.test_text, "File content should match original text"
        )
        self.assertEqual(
            result["encoding"], "text", "Text file should have 'text' encoding"
        )
        self.assertEqual(
            result["mime_type"], "text/plain", "Text file should have correct MIME type"
        )
        self.assertGreater(
            result["size_bytes"], 0, "File size should be greater than 0"
        )

    def test_read_binary_file_success(self):
        """
        Test successful reading of binary files.

        Verifies that binary files are read and base64 encoded correctly,
        with appropriate metadata for binary content handling.
        """
        result = self.file_utils.read_file(self.binary_file)

        # Verify return structure
        self.assertIsInstance(result, dict, "read_file should return a dictionary")
        self.assertIn("content", result, "Result should contain 'content' key")
        self.assertIn("encoding", result, "Result should contain 'encoding' key")
        self.assertIn("mime_type", result, "Result should contain 'mime_type' key")
        self.assertIn("size_bytes", result, "Result should contain 'size_bytes' key")

        # Verify binary content handling
        self.assertEqual(
            result["encoding"], "base64", "Binary file should have 'base64' encoding"
        )
        self.assertEqual(
            result["mime_type"], "image/png", "PNG file should have correct MIME type"
        )

        # Verify base64 content can be decoded back to original
        decoded_content = base64.b64decode(result["content"])
        self.assertEqual(
            decoded_content,
            self.test_binary_data,
            "Base64 decoded content should match original binary data",
        )

    def test_read_file_with_custom_max_size(self):
        """
        Test reading files with custom maximum size limits.

        Verifies that custom size limits are respected and files
        within the limit are read successfully.
        """
        # Test with a reasonable max size (1MB)
        result = self.file_utils.read_file(self.text_file, max_size_mb=1)

        self.assertIsInstance(result, dict, "Should successfully read small file")
        self.assertEqual(
            result["content"],
            self.test_text,
            "Content should be read correctly with custom max size",
        )

    def test_read_nonexistent_file_error(self):
        """
        Test reading nonexistent file raises FileNotFoundError.

        Verifies that attempting to read a file that doesn't exist
        raises the appropriate exception with correct error message.
        """
        expected_message = f"File not found: {self.nonexistent_file}"
        self.assert_error_behavior(
            self.file_utils.read_file,
            FileNotFoundError,
            expected_message,
            None,  # No additional dict fields
            self.nonexistent_file,
        )

    def test_read_file_too_large_error(self):
        """
        Test reading file that exceeds size limit raises ValueError.

        Verifies that files exceeding the maximum size limit
        raise ValueError with appropriate error message.
        """
        # Create a larger test file to ensure it exceeds the limit
        large_content = "x" * 2000  # 2KB content
        large_file = os.path.join(self.temp_dir, "large_test.txt")
        with open(large_file, "w", encoding="utf-8") as f:
            f.write(large_content)

        # Set small max size to trigger error
        max_size_mb = 0.001  # 1KB limit
        file_size = os.path.getsize(large_file)
        max_size_bytes = max_size_mb * 1024 * 1024

        expected_message = f"File too large: {file_size} bytes (max: {max_size_bytes})"
        self.assert_error_behavior(
            self.file_utils.read_file,
            ValueError,
            expected_message,
            None,  # No additional dict fields
            large_file,
            max_size_mb,
        )


class TestFileWriting(TestInstagramFileUtils):
    """Test file writing utility functions."""

    def test_write_text_file_success(self):
        """
        Test successful writing of text files.

        Verifies that text content is written correctly to files
        and can be read back with the same content.
        """
        test_content = "This is test content for writing.\nWith multiple lines."
        output_file = os.path.join(self.temp_dir, "write_test.txt")

        # Write file (should not raise exceptions)
        self.file_utils.write_file(output_file, test_content, encoding="text")

        # Verify file was created
        self.assertTrue(os.path.exists(output_file), "Output file should be created")

        # Verify content by reading back
        with open(output_file, "r", encoding="utf-8") as f:
            written_content = f.read()

        self.assertEqual(
            written_content, test_content, "Written content should match original text"
        )

    def test_write_binary_file_success(self):
        """
        Test successful writing of binary files using base64 encoding.

        Verifies that base64 encoded content is correctly decoded
        and written as binary data.
        """
        output_file = os.path.join(self.temp_dir, "write_test.png")

        # Write binary file using base64 encoding
        self.file_utils.write_file(output_file, self.test_base64, encoding="base64")

        # Verify file was created
        self.assertTrue(
            os.path.exists(output_file), "Binary output file should be created"
        )

        # Verify content by reading back as binary
        with open(output_file, "rb") as f:
            written_data = f.read()

        self.assertEqual(
            written_data,
            self.test_binary_data,
            "Written binary data should match original",
        )

    def test_write_file_creates_directories(self):
        """
        Test that write_file creates necessary parent directories.

        Verifies that the write function creates parent directories
        when they don't exist, enabling writing to nested paths.
        """
        nested_file = os.path.join(self.temp_dir, "subdir", "nested", "test.txt")
        test_content = "Content in nested directory"

        # Write to nested path (should create directories)
        self.file_utils.write_file(nested_file, test_content, encoding="text")

        # Verify file and directories were created
        self.assertTrue(os.path.exists(nested_file), "Nested file should be created")
        self.assertTrue(
            os.path.isdir(os.path.dirname(nested_file)),
            "Parent directories should be created",
        )

        # Verify content
        with open(nested_file, "r", encoding="utf-8") as f:
            written_content = f.read()

        self.assertEqual(
            written_content,
            test_content,
            "Content should be written correctly in nested path",
        )

    def test_write_bytes_as_text(self):
        """
        Test writing bytes content with text encoding.

        Verifies that byte content is properly converted to text
        when using text encoding mode.
        """
        test_bytes = b"Test bytes content"
        output_file = os.path.join(self.temp_dir, "bytes_as_text.txt")

        # Write bytes with text encoding
        self.file_utils.write_file(output_file, test_bytes, encoding="text")

        # Verify content
        with open(output_file, "r", encoding="utf-8") as f:
            written_content = f.read()

        expected_content = test_bytes.decode("utf-8")
        self.assertEqual(
            written_content,
            expected_content,
            "Bytes should be decoded to text correctly",
        )

    def test_write_string_as_base64(self):
        """
        Test writing string content with base64 encoding.

        Verifies that string content passed with base64 encoding
        is properly decoded and written as binary data.
        """
        test_string = "Test string content"
        test_base64 = base64.b64encode(test_string.encode("utf-8")).decode("utf-8")
        output_file = os.path.join(self.temp_dir, "string_as_base64.bin")

        # Write string as base64
        self.file_utils.write_file(output_file, test_base64, encoding="base64")

        # Verify content by reading as binary
        with open(output_file, "rb") as f:
            written_data = f.read()

        expected_data = test_string.encode("utf-8")
        self.assertEqual(
            written_data,
            expected_data,
            "Base64 string should be decoded to correct binary data",
        )


class TestBase64Utilities(TestInstagramFileUtils):
    """Test base64 encoding and decoding utility functions."""

    def test_encode_to_base64_with_string(self):
        """
        Test base64 encoding of string content.

        Verifies that string content is properly encoded to base64
        and can be decoded back to the original string.
        """
        test_string = "Hello, World! This is a test string with special chars: éñ中文"

        result = self.file_utils.encode_to_base64(test_string)

        # Verify result is string
        self.assertIsInstance(result, str, "encode_to_base64 should return string")

        # Verify it's valid base64 by decoding
        decoded = base64.b64decode(result).decode("utf-8")
        self.assertEqual(
            decoded, test_string, "Base64 encoded string should decode back to original"
        )

    def test_encode_to_base64_with_bytes(self):
        """
        Test base64 encoding of bytes content.

        Verifies that byte content is properly encoded to base64
        and can be decoded back to the original bytes.
        """
        result = self.file_utils.encode_to_base64(self.test_binary_data)

        # Verify result is string
        self.assertIsInstance(result, str, "encode_to_base64 should return string")

        # Verify it's valid base64 by decoding
        decoded = base64.b64decode(result)
        self.assertEqual(
            decoded,
            self.test_binary_data,
            "Base64 encoded bytes should decode back to original",
        )

    def test_decode_from_base64_success(self):
        """
        Test successful base64 decoding.

        Verifies that valid base64 strings are correctly decoded
        back to their original byte representation.
        """
        test_string = "Test content for base64 decoding"
        test_base64 = base64.b64encode(test_string.encode("utf-8")).decode("utf-8")

        result = self.file_utils.decode_from_base64(test_base64)

        # Verify result is bytes
        self.assertIsInstance(result, bytes, "decode_from_base64 should return bytes")

        # Verify content
        decoded_string = result.decode("utf-8")
        self.assertEqual(
            decoded_string, test_string, "Decoded content should match original string"
        )

    def test_decode_from_base64_invalid_error(self):
        """
        Test base64 decoding with invalid input raises error.

        Verifies that invalid base64 strings raise appropriate
        exceptions during decoding.
        """
        invalid_base64 = "InvalidBase64=="  # Invalid padding format

        # Invalid base64 should raise binascii.Error (or a subclass)
        import binascii

        expected_message = "Invalid base64-encoded string: number of data characters (13) cannot be 1 more than a multiple of 4"
        self.assert_error_behavior(
            self.file_utils.decode_from_base64,
            binascii.Error,
            expected_message,
            None,  # No additional dict fields
            invalid_base64,
        )

    def test_text_to_base64_conversion(self):
        """
        Test text to base64 conversion utility.

        Verifies that the text_to_base64 function correctly
        converts text strings to base64 encoding.
        """
        test_text = "Hello, World! Special characters: éñ中文"

        result = self.file_utils.text_to_base64(test_text)

        # Verify result is string
        self.assertIsInstance(result, str, "text_to_base64 should return string")

        # Verify correctness by manual decoding
        decoded = base64.b64decode(result).decode("utf-8")
        self.assertEqual(
            decoded, test_text, "text_to_base64 should produce decodable base64"
        )

    def test_base64_to_text_conversion(self):
        """
        Test base64 to text conversion utility.

        Verifies that the base64_to_text function correctly
        converts base64 strings back to text.
        """
        test_text = "Hello, World! Special characters: éñ中文"
        test_base64 = base64.b64encode(test_text.encode("utf-8")).decode("utf-8")

        result = self.file_utils.base64_to_text(test_base64)

        # Verify result is string
        self.assertIsInstance(result, str, "base64_to_text should return string")

        # Verify content
        self.assertEqual(
            result, test_text, "base64_to_text should correctly decode to original text"
        )

    def test_base64_to_text_invalid_utf8_error(self):
        """
        Test base64_to_text with non-UTF8 content raises error.

        Verifies that base64 content that doesn't represent valid
        UTF-8 text raises appropriate decoding errors.
        """
        # Create base64 of invalid UTF-8 sequence
        invalid_utf8_bytes = b"\xff\xfe\xfd"
        invalid_base64 = base64.b64encode(invalid_utf8_bytes).decode("utf-8")

        self.assert_error_behavior(
            self.file_utils.base64_to_text,
            UnicodeDecodeError,
            "'utf-8' codec can't decode byte 0xff in position 0: invalid start byte",
            None,  # No additional dict fields
            invalid_base64,
        )


class TestFileBase64Operations(TestInstagramFileUtils):
    """Test file and base64 conversion utility functions."""

    def test_file_to_base64_success(self):
        """
        Test successful conversion of file to base64.

        Verifies that files are correctly read and converted
        to base64 encoding for transmission or storage.
        """
        result = self.file_utils.file_to_base64(self.binary_file)

        # Verify result is string
        self.assertIsInstance(result, str, "file_to_base64 should return string")

        # Verify correctness by decoding back
        decoded_data = base64.b64decode(result)
        self.assertEqual(
            decoded_data,
            self.test_binary_data,
            "file_to_base64 should produce correct base64 encoding",
        )

    def test_file_to_base64_nonexistent_file_error(self):
        """
        Test file_to_base64 with nonexistent file raises error.

        Verifies that attempting to convert a nonexistent file
        raises FileNotFoundError with appropriate message.
        """
        expected_message = (
            f"[Errno 2] No such file or directory: '{self.nonexistent_file}'"
        )
        self.assert_error_behavior(
            self.file_utils.file_to_base64,
            FileNotFoundError,
            expected_message,
            None,  # No additional dict fields
            self.nonexistent_file,
        )

    def test_base64_to_file_success(self):
        """
        Test successful conversion of base64 to file.

        Verifies that base64 encoded content is correctly
        decoded and written to a file.
        """
        output_file = os.path.join(self.temp_dir, "base64_output.png")

        # Convert base64 to file
        self.file_utils.base64_to_file(self.test_base64, output_file)

        # Verify file was created
        self.assertTrue(
            os.path.exists(output_file), "base64_to_file should create output file"
        )

        # Verify content by reading back
        with open(output_file, "rb") as f:
            written_data = f.read()

        self.assertEqual(
            written_data,
            self.test_binary_data,
            "base64_to_file should write correct binary data",
        )

    def test_base64_to_file_creates_directories(self):
        """
        Test base64_to_file creates necessary parent directories.

        Verifies that the function creates parent directories
        when writing to nested paths.
        """
        nested_output = os.path.join(self.temp_dir, "nested", "dir", "output.bin")

        # Convert base64 to nested file path
        self.file_utils.base64_to_file(self.test_base64, nested_output)

        # Verify file and directories were created
        self.assertTrue(
            os.path.exists(nested_output),
            "base64_to_file should create file in nested path",
        )
        self.assertTrue(
            os.path.isdir(os.path.dirname(nested_output)),
            "base64_to_file should create parent directories",
        )

        # Verify content
        with open(nested_output, "rb") as f:
            written_data = f.read()

        self.assertEqual(
            written_data,
            self.test_binary_data,
            "Content should be written correctly in nested path",
        )

    def test_base64_to_file_invalid_base64_error(self):
        """
        Test base64_to_file with invalid base64 raises error.

        Verifies that invalid base64 input raises appropriate
        exceptions during file writing.
        """
        output_file = os.path.join(self.temp_dir, "invalid_output.bin")
        invalid_base64 = "InvalidBase64=="  # Invalid character count

        import binascii

        expected_message = "Invalid base64-encoded string: number of data characters (13) cannot be 1 more than a multiple of 4"
        self.assert_error_behavior(
            self.file_utils.base64_to_file,
            binascii.Error,
            expected_message,
            None,  # No additional dict fields
            invalid_base64,
            output_file,
        )


class TestFileUtilsIntegration(TestInstagramFileUtils):
    """Integration tests for file utility functions working together."""

    def test_complete_file_round_trip_text(self):
        """
        Test complete round trip: write → read → verify for text files.

        Verifies that text content written with write_file can be
        read back correctly with read_file, ensuring data integrity.
        """
        original_content = "This is a comprehensive test\nWith multiple lines\nAnd special chars: éñ中文"
        test_file = os.path.join(self.temp_dir, "roundtrip.txt")

        # Write file
        self.file_utils.write_file(test_file, original_content, encoding="text")

        # Read file back
        result = self.file_utils.read_file(test_file)

        # Verify round trip integrity
        self.assertEqual(
            result["content"],
            original_content,
            "Round trip content should match original",
        )
        self.assertEqual(
            result["encoding"], "text", "Round trip should preserve text encoding"
        )
        self.assertEqual(
            result["mime_type"],
            "text/plain",
            "Round trip should detect correct MIME type",
        )

    def test_complete_file_round_trip_binary(self):
        """
        Test complete round trip: write → read → verify for binary files.

        Verifies that binary content written with write_file can be
        read back correctly with read_file, ensuring data integrity.
        """
        original_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x01\x02\x03\x04"
        original_base64 = base64.b64encode(original_data).decode("utf-8")
        test_file = os.path.join(self.temp_dir, "roundtrip.png")

        # Write binary file
        self.file_utils.write_file(test_file, original_base64, encoding="base64")

        # Read file back
        result = self.file_utils.read_file(test_file)

        # Verify round trip integrity
        self.assertEqual(
            result["encoding"], "base64", "Round trip should preserve base64 encoding"
        )
        self.assertEqual(
            result["mime_type"],
            "image/png",
            "Round trip should detect correct MIME type",
        )

        # Verify binary content integrity
        decoded_data = base64.b64decode(result["content"])
        self.assertEqual(
            decoded_data,
            original_data,
            "Round trip binary content should match original",
        )

    def test_base64_conversion_round_trip(self):
        """
        Test complete base64 conversion round trip.

        Verifies that data converted to base64 and back maintains
        complete integrity through the conversion process.
        """
        original_text = "Test content with special characters: éñ中文🚀"

        # Text → Base64 → Text
        base64_result = self.file_utils.text_to_base64(original_text)
        text_result = self.file_utils.base64_to_text(base64_result)

        self.assertEqual(
            text_result, original_text, "Text base64 round trip should preserve content"
        )

        # Bytes → Base64 → Bytes
        original_bytes = original_text.encode("utf-8")
        base64_bytes = self.file_utils.encode_to_base64(original_bytes)
        decoded_bytes = self.file_utils.decode_from_base64(base64_bytes)

        self.assertEqual(
            decoded_bytes,
            original_bytes,
            "Bytes base64 round trip should preserve content",
        )

    def test_file_base64_conversion_round_trip(self):
        """
        Test file to base64 and back conversion round trip.

        Verifies that files converted to base64 and written back
        maintain complete data integrity.
        """
        # File → Base64 → File
        original_base64 = self.file_utils.file_to_base64(self.binary_file)
        output_file = os.path.join(self.temp_dir, "roundtrip_file.png")

        self.file_utils.base64_to_file(original_base64, output_file)

        # Verify files are identical
        with open(self.binary_file, "rb") as f:
            original_data = f.read()

        with open(output_file, "rb") as f:
            roundtrip_data = f.read()

        self.assertEqual(
            roundtrip_data,
            original_data,
            "File base64 round trip should preserve all data",
        )

    def test_mixed_encoding_operations(self):
        """
        Test operations with mixed encoding types.

        Verifies that utility functions handle mixed encoding
        scenarios correctly without data corruption.
        """
        # Create mixed content scenario
        text_content = "Mixed content test"
        binary_content = text_content.encode("utf-8")
        base64_content = base64.b64encode(binary_content).decode("utf-8")

        # Test various conversion paths
        # String → Base64 → Bytes → Base64 → String
        step1 = self.file_utils.text_to_base64(text_content)
        step2 = self.file_utils.decode_from_base64(step1)
        step3 = self.file_utils.encode_to_base64(step2)
        step4 = self.file_utils.base64_to_text(step3)

        self.assertEqual(
            step4, text_content, "Mixed encoding operations should preserve content"
        )

        # Verify intermediate steps
        self.assertEqual(
            step2, binary_content, "Intermediate binary step should be correct"
        )
        self.assertEqual(step1, step3, "Base64 representations should be consistent")


if __name__ == "__main__":
    # Configure test runner for utility function testing
    unittest.main(verbosity=2, buffer=True)
