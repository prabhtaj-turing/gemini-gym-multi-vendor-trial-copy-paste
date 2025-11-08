"""
Test suite for SimulationEngine utility functions.

This test suite verifies:
1. Device type detection and device retrieval utilities from utils.py
2. File handling utilities from file_utils.py that provide core functionality
3. Proper error handling and edge cases for all utility functions
4. Data structure validation and type checking
"""

import unittest
import tempfile
import os
import base64
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from home_assistant.SimulationEngine.utils import (
    allowed_states,
    _get_device_type,
    _get_home_assistant_devices,
)
from home_assistant.SimulationEngine.file_utils import (
    is_text_file,
    is_binary_file,
    get_mime_type,
    read_file,
    write_file,
    encode_to_base64,
    decode_from_base64,
    text_to_base64,
    base64_to_text,
    file_to_base64,
    base64_to_file,
)
from home_assistant.SimulationEngine.db import DB


class TestSimulationEngineUtils(BaseTestCaseWithErrorHandler):
    """Test suite for SimulationEngine utility functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Store original DB state to restore after each test
        self.original_db_state = DB.copy()

        # Clear DB to ensure clean state for each test
        DB.clear()

        # Sample device data for testing
        self.sample_devices = {
            "LIGHT_001": {
                "type": "light",
                "name": "Living Room Light",
                "attributes": {"state": "On", "brightness": 75},
            },
            "fan.bedroom": {
                "type": "fan",
                "name": "Bedroom Fan",
                "attributes": {"state": "Off"},
            },
            "door.front": {"type": "door", "attributes": {"state": "Closed"}},
            "device_no_type": {
                "name": "Unknown Device",
                "attributes": {"state": "Unknown"},
            },
        }

        # Set up DB with test data
        DB.update({"environment": {"home_assistant": {"devices": self.sample_devices}}})

        # Create temporary directory and files for file utils testing
        self.temp_dir = tempfile.mkdtemp()
        self.temp_text_file = os.path.join(self.temp_dir, "test.txt")
        self.temp_binary_file = os.path.join(self.temp_dir, "test.jpg")
        self.temp_python_file = os.path.join(self.temp_dir, "test.py")

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db_state)

        # Clean up temporary files and directory
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    # =============================================================================
    # Tests for utils.py functions
    # =============================================================================

    def test_allowed_states_data_structure_integrity(self):
        """
        UTILS TEST: Verify allowed_states dictionary has proper structure and content.

        This test ensures the allowed_states constant contains expected device types
        with valid state lists, which is critical for device state validation.
        """
        # Verify allowed_states is a dictionary
        self.assertIsInstance(
            allowed_states, dict, "allowed_states must be a dictionary"
        )

        # Verify it contains expected device types
        expected_device_types = [
            "light",
            "fan",
            "pump",
            "sprinkler",
            "door",
            "window",
            "wifi",
            "frame",
            "speaker",
            "clock",
            "tv",
            "alarm",
            "vacuum",
            "pet_feeder",
            "curtain",
        ]

        for device_type in expected_device_types:
            self.assertIn(
                device_type,
                allowed_states,
                f"Device type '{device_type}' should be in allowed_states",
            )

            # Verify each device type has a list of states
            states = allowed_states[device_type]
            self.assertIsInstance(
                states, list, f"States for {device_type} must be a list"
            )
            self.assertGreater(
                len(states), 0, f"States for {device_type} must not be empty"
            )

            # Verify all states are strings
            for state in states:
                self.assertIsInstance(
                    state, str, f"State '{state}' for {device_type} must be a string"
                )
                self.assertGreater(
                    len(state), 0, f"State for {device_type} must not be empty string"
                )

        # Verify specific expected states for critical device types
        self.assertEqual(allowed_states["light"], ["On", "Off"])
        self.assertEqual(
            allowed_states["door"], ["Open", "Closed", "Locked", "Unlocked"]
        )
        self.assertEqual(allowed_states["window"], ["Open", "Closed"])

    def test_get_device_type_with_explicit_type_field(self):
        """
        UTILS TEST: Verify _get_device_type returns device type from type field.

        This test ensures the function correctly extracts device type from the
        device dictionary when the 'type' field is present.
        """
        devices = self.sample_devices

        # Test device with explicit type field
        device_type = _get_device_type("LIGHT_001", devices)
        self.assertEqual(
            device_type, "light", "Should return lowercase device type from type field"
        )

        # Test device with uppercase type field (should be lowercased)
        devices_with_uppercase = {
            "TEST_DEVICE": {"type": "LIGHT", "attributes": {"state": "On"}}
        }
        device_type = _get_device_type("TEST_DEVICE", devices_with_uppercase)
        self.assertEqual(
            device_type,
            "light",
            "Should return lowercase device type even if type field is uppercase",
        )

    def test_get_device_type_fallback_to_entity_prefix(self):
        """
        UTILS TEST: Verify _get_device_type falls back to entity ID prefix when type field missing.

        This test ensures the function extracts device type from entity ID prefix
        when the device doesn't have an explicit 'type' field.
        """
        devices = self.sample_devices

        # Test device without type field - should extract from entity_id prefix
        device_type = _get_device_type("fan.bedroom", devices)
        self.assertEqual(
            device_type, "fan", "Should extract device type from entity_id prefix"
        )

        # Test with missing device - should still extract from entity_id
        device_type = _get_device_type("switch.kitchen", {})
        self.assertEqual(
            device_type,
            "switch",
            "Should extract device type from entity_id even if device not found",
        )

        # Test complex entity_id with multiple dots
        device_type = _get_device_type("sensor.temperature.outdoor", {})
        self.assertEqual(
            device_type, "sensor", "Should extract first part before dot as device type"
        )

    def test_get_device_type_handles_missing_device(self):
        """
        UTILS TEST: Verify _get_device_type handles missing devices gracefully.

        This test ensures the function doesn't raise errors when the entity_id
        is not found in the devices dictionary.
        """
        devices = self.sample_devices

        # Test with nonexistent entity_id
        device_type = _get_device_type("nonexistent.device", devices)
        self.assertEqual(
            device_type,
            "nonexistent",
            "Should extract type from entity_id for missing devices",
        )

        # Test with simple entity_id (no dots)
        device_type = _get_device_type("simple_device", devices)
        self.assertEqual(
            device_type,
            "simple_device",
            "Should return entire entity_id if no dots present",
        )

    def test_get_home_assistant_devices_returns_devices_from_db(self):
        """
        UTILS TEST: Verify _get_home_assistant_devices returns correct devices from DB.

        This test ensures the function correctly retrieves device data from the
        database following the expected path structure.
        """
        # Test with populated DB
        devices = _get_home_assistant_devices()

        self.assertIsInstance(devices, dict, "Should return a dictionary")
        self.assertEqual(
            devices,
            self.sample_devices,
            "Should return devices from DB environment structure",
        )

        # Verify specific devices are present
        self.assertIn("LIGHT_001", devices)
        self.assertIn("fan.bedroom", devices)
        self.assertEqual(devices["LIGHT_001"]["type"], "light")

    def test_get_home_assistant_devices_handles_missing_db_structure(self):
        """
        UTILS TEST: Verify _get_home_assistant_devices handles missing DB structure gracefully.

        This test ensures the function returns empty dict when database structure
        is incomplete or missing, preventing runtime errors.
        """
        # Test with empty DB
        DB.clear()
        devices = _get_home_assistant_devices()
        self.assertEqual(devices, {}, "Should return empty dict for empty DB")

        # Test with partial DB structure - missing home_assistant
        DB.update({"environment": {}})
        devices = _get_home_assistant_devices()
        self.assertEqual(
            devices, {}, "Should return empty dict when home_assistant section missing"
        )

        # Test with partial DB structure - missing devices
        DB.update({"environment": {"home_assistant": {}}})
        devices = _get_home_assistant_devices()
        self.assertEqual(
            devices, {}, "Should return empty dict when devices section missing"
        )

        # Test with no environment section
        DB.clear()
        DB.update({"other_section": {"data": "value"}})
        devices = _get_home_assistant_devices()
        self.assertEqual(
            devices, {}, "Should return empty dict when environment section missing"
        )

    # =============================================================================
    # Tests for file_utils.py functions
    # =============================================================================

    def test_is_text_file_recognizes_text_extensions(self):
        """
        FILE UTILS TEST: Verify is_text_file correctly identifies text file extensions.

        This test ensures the function properly categorizes files as text based
        on their extensions, which is critical for proper file handling.
        """
        # Test common text file extensions
        text_files = [
            "script.py",
            "config.json",
            "style.css",
            "page.html",
            "readme.md",
            "data.csv",
            "script.js",
            "code.cpp",
        ]

        for file_path in text_files:
            self.assertTrue(
                is_text_file(file_path),
                f"File {file_path} should be recognized as text file",
            )

        # Test case insensitivity
        self.assertTrue(is_text_file("FILE.TXT"), "Should handle uppercase extensions")
        self.assertTrue(
            is_text_file("script.PY"), "Should handle mixed case extensions"
        )

    def test_is_text_file_rejects_binary_extensions(self):
        """
        FILE UTILS TEST: Verify is_text_file correctly rejects binary file extensions.

        This test ensures the function doesn't incorrectly classify binary files
        as text files, preventing encoding issues.
        """
        # Test common binary file extensions
        binary_files = [
            "image.jpg",
            "document.pdf",
            "archive.zip",
            "audio.mp3",
            "video.mp4",
            "executable.exe",
            "database.db",
        ]

        for file_path in binary_files:
            self.assertFalse(
                is_text_file(file_path),
                f"File {file_path} should not be recognized as text file",
            )

    def test_is_binary_file_recognizes_binary_extensions(self):
        """
        FILE UTILS TEST: Verify is_binary_file correctly identifies binary file extensions.

        This test ensures the function properly categorizes files as binary based
        on their extensions for appropriate handling.
        """
        # Test common binary file extensions
        binary_files = [
            "photo.png",
            "document.docx",
            "data.xlsx",
            "movie.avi",
            "song.wav",
            "program.exe",
            "package.deb",
        ]

        for file_path in binary_files:
            self.assertTrue(
                is_binary_file(file_path),
                f"File {file_path} should be recognized as binary file",
            )

    def test_is_binary_file_rejects_text_extensions(self):
        """
        FILE UTILS TEST: Verify is_binary_file correctly rejects text file extensions.

        This test ensures the function doesn't incorrectly classify text files
        as binary files.
        """
        # Test text file extensions
        text_files = ["code.py", "config.json", "style.css", "page.html"]

        for file_path in text_files:
            self.assertFalse(
                is_binary_file(file_path),
                f"File {file_path} should not be recognized as binary file",
            )

    def test_get_mime_type_returns_correct_types(self):
        """
        FILE UTILS TEST: Verify get_mime_type returns appropriate MIME types.

        This test ensures the function returns correct MIME types for different
        file extensions, which is important for proper content handling.
        """
        # Test common MIME types
        mime_tests = [
            ("file.txt", "text/plain"),
            ("page.html", "text/html"),
            ("data.json", "application/json"),
            ("image.jpg", "image/jpeg"),
            ("document.pdf", "application/pdf"),
        ]

        for file_path, expected_mime in mime_tests:
            mime_type = get_mime_type(file_path)
            self.assertEqual(
                mime_type,
                expected_mime,
                f"MIME type for {file_path} should be {expected_mime}",
            )

    def test_get_mime_type_handles_unknown_extensions(self):
        """
        FILE UTILS TEST: Verify get_mime_type handles unknown file extensions.

        This test ensures the function provides a fallback MIME type for
        unrecognized file extensions.
        """
        unknown_file = "file.unknownext"
        mime_type = get_mime_type(unknown_file)
        self.assertEqual(
            mime_type,
            "application/octet-stream",
            "Unknown extensions should return default MIME type",
        )

    def test_read_file_success_text_file(self):
        """
        FILE UTILS TEST: Verify read_file successfully reads text files.

        This test ensures the function correctly reads text files and returns
        proper metadata including content, encoding, and file information.
        """
        # Create test text file
        test_content = "Hello, World!\nThis is a test file."
        with open(self.temp_text_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Read the file
        result = read_file(self.temp_text_file)

        # Verify result structure and content
        self.assertIsInstance(result, dict, "Should return a dictionary")
        self.assertIn("content", result)
        self.assertIn("encoding", result)
        self.assertIn("mime_type", result)
        self.assertIn("size_bytes", result)

        self.assertEqual(
            result["content"], test_content, "Content should match original"
        )
        self.assertEqual(result["encoding"], "text", "Encoding should be 'text'")
        self.assertEqual(
            result["mime_type"], "text/plain", "MIME type should be text/plain"
        )
        self.assertGreater(result["size_bytes"], 0, "Size should be greater than 0")

    def test_read_file_success_binary_file(self):
        """
        FILE UTILS TEST: Verify read_file successfully reads binary files as base64.

        This test ensures the function correctly reads binary files and encodes
        them as base64 for safe transmission and storage.
        """
        # Create test binary file (simple image-like data)
        test_binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"
        with open(self.temp_binary_file, "wb") as f:
            f.write(test_binary_data)

        # Read the file
        result = read_file(self.temp_binary_file)

        # Verify result structure
        self.assertIsInstance(result, dict, "Should return a dictionary")
        self.assertEqual(
            result["encoding"], "base64", "Binary files should use base64 encoding"
        )
        self.assertEqual(
            result["mime_type"], "image/jpeg", "Should detect correct MIME type"
        )

        # Verify content can be decoded back to original
        decoded_content = base64.b64decode(result["content"])
        self.assertEqual(
            decoded_content, test_binary_data, "Decoded content should match original"
        )

    def test_read_file_error_handling_nonexistent_file(self):
        """
        FILE UTILS TEST: Verify read_file handles nonexistent files properly.

        This test ensures the function raises appropriate exceptions when
        attempting to read files that don't exist.
        """
        nonexistent_file = "/path/to/nonexistent/file.txt"

        self.assert_error_behavior(
            read_file,
            FileNotFoundError,
            f"File not found: {nonexistent_file}",
            None,
            nonexistent_file,
        )

    def test_read_file_error_handling_file_too_large(self):
        """
        FILE UTILS TEST: Verify read_file handles oversized files properly.

        This test ensures the function raises appropriate exceptions when
        files exceed the maximum size limit.
        """
        # Create a file that's larger than 1MB (using max_size_mb=1 for testing)
        large_content = "x" * (2 * 1024 * 1024)  # 2MB of data
        large_file = os.path.join(self.temp_dir, "large.txt")
        with open(large_file, "w") as f:
            f.write(large_content)

        # Try to read with 1MB limit
        expected_size = 2 * 1024 * 1024
        max_size = 1 * 1024 * 1024

        self.assert_error_behavior(
            read_file,
            ValueError,
            f"File too large: {expected_size} bytes (max: {max_size})",
            None,
            large_file,
            1,  # max_size_mb=1
        )

    def test_write_file_success_text_mode(self):
        """
        FILE UTILS TEST: Verify write_file successfully writes text content.

        This test ensures the function correctly writes text content to files
        and creates necessary directory structure.
        """
        test_content = "Hello, World!\nThis is test content."
        test_file = os.path.join(self.temp_dir, "subdir", "test_write.txt")

        # Write the file
        write_file(test_file, test_content, "text")

        # Verify file was created and content is correct
        self.assertTrue(os.path.exists(test_file), "File should be created")

        with open(test_file, "r", encoding="utf-8") as f:
            written_content = f.read()

        self.assertEqual(
            written_content, test_content, "Written content should match original"
        )

    def test_write_file_success_base64_mode(self):
        """
        FILE UTILS TEST: Verify write_file successfully writes base64 content.

        This test ensures the function correctly decodes and writes base64
        content as binary data.
        """
        # Create base64 encoded content
        original_data = b"This is binary test data"
        base64_content = base64.b64encode(original_data).decode("utf-8")
        test_file = os.path.join(self.temp_dir, "test_binary_write.bin")

        # Write the file
        write_file(test_file, base64_content, "base64")

        # Verify file was created and content is correct
        self.assertTrue(os.path.exists(test_file), "File should be created")

        with open(test_file, "rb") as f:
            written_data = f.read()

        self.assertEqual(
            written_data, original_data, "Written binary data should match original"
        )

    def test_encode_to_base64_handles_string_input(self):
        """
        FILE UTILS TEST: Verify encode_to_base64 correctly encodes string input.

        This test ensures the function properly converts string content to
        base64 encoding for safe transmission.
        """
        test_string = "Hello, World!"
        encoded = encode_to_base64(test_string)

        # Verify it's a valid base64 string
        self.assertIsInstance(encoded, str, "Should return a string")

        # Verify it can be decoded back to original
        decoded = base64.b64decode(encoded).decode("utf-8")
        self.assertEqual(decoded, test_string, "Decoded content should match original")

    def test_encode_to_base64_handles_bytes_input(self):
        """
        FILE UTILS TEST: Verify encode_to_base64 correctly encodes bytes input.

        This test ensures the function properly converts binary data to
        base64 encoding.
        """
        test_bytes = b"Binary test data"
        encoded = encode_to_base64(test_bytes)

        # Verify it's a valid base64 string
        self.assertIsInstance(encoded, str, "Should return a string")

        # Verify it can be decoded back to original
        decoded = base64.b64decode(encoded)
        self.assertEqual(decoded, test_bytes, "Decoded content should match original")

    def test_decode_from_base64_success(self):
        """
        FILE UTILS TEST: Verify decode_from_base64 correctly decodes base64 content.

        This test ensures the function properly converts base64 strings back
        to binary data.
        """
        original_data = b"Test binary data for decoding"
        base64_string = base64.b64encode(original_data).decode("utf-8")

        decoded = decode_from_base64(base64_string)

        self.assertIsInstance(decoded, bytes, "Should return bytes")
        self.assertEqual(decoded, original_data, "Decoded data should match original")

    def test_decode_from_base64_error_handling_incorrect_padding(self):
        """
        FILE UTILS TEST: Verify decode_from_base64 handles incorrect padding properly.

        This test ensures the function raises appropriate exceptions when
        given base64 input with incorrect padding.
        """
        # Base64 requires proper padding - "abc" has incorrect padding
        invalid_padding_input = "abc"

        self.assert_error_behavior(
            decode_from_base64,
            Exception,  # binascii.Error: Incorrect padding
            "Incorrect padding",
            None,
            invalid_padding_input,
        )

    def test_text_to_base64_conversion(self):
        """
        FILE UTILS TEST: Verify text_to_base64 correctly converts text to base64.

        This test ensures the convenience function properly handles text to
        base64 conversion.
        """
        test_text = "Hello, Base64 World!"
        base64_result = text_to_base64(test_text)

        # Verify round-trip conversion
        decoded_text = base64_to_text(base64_result)
        self.assertEqual(
            decoded_text, test_text, "Round-trip conversion should preserve text"
        )

    def test_base64_to_text_conversion(self):
        """
        FILE UTILS TEST: Verify base64_to_text correctly converts base64 to text.

        This test ensures the convenience function properly handles base64 to
        text conversion with proper UTF-8 decoding.
        """
        test_text = "Hello, Text World!"
        base64_input = base64.b64encode(test_text.encode("utf-8")).decode("utf-8")

        decoded_text = base64_to_text(base64_input)
        self.assertEqual(
            decoded_text, test_text, "Should correctly decode base64 to text"
        )

    def test_file_to_base64_reads_and_encodes_file(self):
        """
        FILE UTILS TEST: Verify file_to_base64 correctly reads file and returns base64.

        This test ensures the function properly reads any file type and converts
        it to base64 encoding for transmission or storage.
        """
        # Create test file with binary content
        test_data = b"Binary file content for base64 encoding"
        test_file = os.path.join(self.temp_dir, "test_file_to_base64.bin")
        with open(test_file, "wb") as f:
            f.write(test_data)

        # Convert file to base64
        base64_result = file_to_base64(test_file)

        # Verify result
        self.assertIsInstance(base64_result, str, "Should return a string")

        # Verify it can be decoded back to original content
        decoded_data = base64.b64decode(base64_result)
        self.assertEqual(
            decoded_data, test_data, "Decoded data should match original file content"
        )

    def test_base64_to_file_writes_decoded_content(self):
        """
        FILE UTILS TEST: Verify base64_to_file correctly writes base64 content to file.

        This test ensures the function properly decodes base64 content and
        writes it as binary data to a file.
        """
        # Create base64 content
        original_data = b"Test data for base64 to file conversion"
        base64_content = base64.b64encode(original_data).decode("utf-8")
        output_file = os.path.join(self.temp_dir, "output_from_base64.bin")

        # Write base64 content to file
        base64_to_file(base64_content, output_file)

        # Verify file was created and content is correct
        self.assertTrue(os.path.exists(output_file), "Output file should be created")

        with open(output_file, "rb") as f:
            written_data = f.read()

        self.assertEqual(
            written_data, original_data, "Written data should match original"
        )


if __name__ == "__main__":
    unittest.main()
