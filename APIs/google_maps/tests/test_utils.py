"""
Utility functions test suite for Google Maps API module.

This test suite provides comprehensive testing for all utility functions
in the SimulationEngine directory, including:

1. Database utility functions from utils.py:
   - _create_place: Place creation and validation
   - _haversine_distance: Geographic distance calculations

2. File utility functions from file_utils.py:
   - File type detection (text/binary)
   - MIME type detection
   - File reading/writing operations
   - Base64 encoding/decoding operations

Each utility function is tested for:
- Happy path scenarios (normal expected usage)
- Exception scenarios with proper error handling
- Edge cases and boundary conditions
- Side effects and state changes

Author: Auto-generated utility functions test suite
"""

import unittest
import os
import tempfile
import shutil
import base64
import uuid
import math
from typing import Dict, Any
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestSimulationEngineUtilsDatabase(BaseTestCaseWithErrorHandler):
    """
    Test suite for database utility functions from utils.py.
    
    Purpose: Verify database utility functions work correctly for place
    creation and geographic calculations.
    """
    
    def setUp(self):
        """Set up test fixtures for database utility tests."""
        # Store original database state to restore after tests
        from google_maps.SimulationEngine.db import get_minified_state
        self.original_db_state = get_minified_state().copy()
        
        # Test data for place creation
        self.valid_place_data = {
            'id': f'test_place_{uuid.uuid4().hex[:8]}',
            'name': 'Test Restaurant',
            'rating': 4.5,
            'userRatingCount': 123,
            'formattedAddress': '123 Test Street, Test City, TC 12345',
            'location': {'latitude': 37.7749, 'longitude': -122.4194},
            'primaryType': 'restaurant',
            'types': ['restaurant', 'food', 'establishment']
        }
        
        # Invalid place data for error testing
        self.invalid_place_data_no_id = {
            'name': 'No ID Restaurant',
            'rating': 4.2
        }
        
        # Geographic coordinates for distance testing
        self.test_coordinates = {
            'san_francisco': {'lat': 37.7749, 'lon': -122.4194},
            'new_york': {'lat': 40.7128, 'lon': -74.0060},
            'london': {'lat': 51.5074, 'lon': -0.1278},
            'sydney': {'lat': -33.8688, 'lon': 151.2093},
            'same_point': {'lat': 37.7749, 'lon': -122.4194}  # Same as SF for zero distance test
        }
    
    def tearDown(self):
        """Clean up test fixtures and restore original database state."""
        # Restore original database state
        from google_maps.SimulationEngine.db import DB
        DB.clear()
        DB.update(self.original_db_state)
    
    def test_create_place_happy_path(self):
        """
        Test _create_place with valid place data.
        
        Purpose: Verify place creation works correctly with complete valid data.
        Tests both return value and side effect (database modification).
        """
        from google_maps.SimulationEngine.utils import _create_place
        from google_maps.SimulationEngine.db import DB
        
        # Verify place doesn't exist initially
        self.assertNotIn(self.valid_place_data['id'], DB)
        
        # Create place
        result = _create_place(self.valid_place_data)
        
        # Verify return value
        self.assertIsInstance(result, dict)
        self.assertEqual(result, self.valid_place_data)
        self.assertEqual(result['id'], self.valid_place_data['id'])
        self.assertEqual(result['name'], self.valid_place_data['name'])
        
        # Verify side effect: place was added to database
        self.assertIn(self.valid_place_data['id'], DB)
        stored_place = DB[self.valid_place_data['id']]
        self.assertEqual(stored_place, self.valid_place_data)
    
    def test_create_place_minimal_data(self):
        """
        Test _create_place with minimal required data.
        
        Purpose: Verify place creation works with only required fields.
        Tests that function handles minimal data correctly.
        """
        from google_maps.SimulationEngine.utils import _create_place
        from google_maps.SimulationEngine.db import DB
        
        minimal_place = {'id': f'minimal_{uuid.uuid4().hex[:8]}'}
        
        # Create place with minimal data
        result = _create_place(minimal_place)
        
        # Verify creation successful
        self.assertEqual(result, minimal_place)
        self.assertIn(minimal_place['id'], DB)
        self.assertEqual(DB[minimal_place['id']], minimal_place)
    
    def test_create_place_missing_id_error(self):
        """
        Test _create_place error handling when ID field is missing.
        
        Purpose: Verify appropriate error when required 'id' field is missing.
        Critical because: ID is required for database operations.
        """
        from google_maps.SimulationEngine.utils import _create_place
        
        # Test with place data missing 'id' field
        self.assert_error_behavior(
            _create_place,
            ValueError,
            "Place data must contain an 'id' field.",
            None,
            self.invalid_place_data_no_id
        )
    
    def test_create_place_duplicate_id_error(self):
        """
        Test _create_place error handling when place ID already exists.
        
        Purpose: Verify appropriate error when attempting to create duplicate place.
        Critical because: Duplicate prevention maintains database integrity.
        """
        from google_maps.SimulationEngine.utils import _create_place
        
        # Create initial place
        _create_place(self.valid_place_data)
        
        # Attempt to create place with same ID
        duplicate_place = self.valid_place_data.copy()
        duplicate_place['name'] = 'Duplicate Restaurant'
        
        expected_message = f"Place with id '{self.valid_place_data['id']}' already exists."
        
        self.assert_error_behavior(
            _create_place,
            ValueError,
            expected_message,
            None,
            duplicate_place
        )
    
    def test_haversine_distance_same_point(self):
        """
        Test _haversine_distance with identical coordinates.
        
        Purpose: Verify distance calculation returns zero for same point.
        Tests edge case of zero distance.
        """
        from google_maps.SimulationEngine.utils import _haversine_distance
        
        coords = self.test_coordinates['san_francisco']
        distance = _haversine_distance(
            coords['lat'], coords['lon'],
            coords['lat'], coords['lon']
        )
        
        # Distance should be zero (or very close due to floating point precision)
        self.assertAlmostEqual(distance, 0.0, places=5)
        self.assertIsInstance(distance, float)
    
    def test_haversine_distance_known_locations(self):
        """
        Test _haversine_distance with known geographic locations.
        
        Purpose: Verify distance calculations are reasonably accurate for known locations.
        Tests normal usage with real-world coordinates.
        """
        from google_maps.SimulationEngine.utils import _haversine_distance
        
        # Test San Francisco to New York (approximately 4,100 km)
        sf = self.test_coordinates['san_francisco']
        ny = self.test_coordinates['new_york']
        
        distance = _haversine_distance(sf['lat'], sf['lon'], ny['lat'], ny['lon'])
        
        # Distance should be approximately 4,100,000 meters (4,100 km)
        # Allow reasonable margin for calculation differences
        expected_distance = 4100000  # meters
        tolerance = 100000  # 100 km tolerance
        
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
        self.assertAlmostEqual(distance, expected_distance, delta=tolerance)
    
    def test_haversine_distance_international_locations(self):
        """
        Test _haversine_distance with international coordinates.
        
        Purpose: Verify function works correctly with global coordinates.
        Tests handling of different hemispheres and large distances.
        """
        from google_maps.SimulationEngine.utils import _haversine_distance
        
        # Test London to Sydney (approximately 17,000 km)
        london = self.test_coordinates['london']
        sydney = self.test_coordinates['sydney']
        
        distance = _haversine_distance(
            london['lat'], london['lon'],
            sydney['lat'], sydney['lon']
        )
        
        # Distance should be approximately 17,000,000 meters
        expected_distance = 17000000  # meters
        tolerance = 500000  # 500 km tolerance
        
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
        self.assertAlmostEqual(distance, expected_distance, delta=tolerance)
    
    def test_haversine_distance_boundary_coordinates(self):
        """
        Test _haversine_distance with boundary coordinate values.
        
        Purpose: Verify function handles extreme latitude/longitude values correctly.
        Tests edge cases at coordinate boundaries.
        """
        from google_maps.SimulationEngine.utils import _haversine_distance
        
        # Test with boundary coordinates
        north_pole = (90.0, 0.0)
        south_pole = (-90.0, 0.0)
        
        distance = _haversine_distance(
            north_pole[0], north_pole[1],
            south_pole[0], south_pole[1]
        )
        
        # Distance from North Pole to South Pole should be approximately 20,000 km
        # (half the Earth's circumference)
        expected_distance = 20000000  # meters
        tolerance = 500000  # 500 km tolerance
        
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
        self.assertAlmostEqual(distance, expected_distance, delta=tolerance)
    
    def test_haversine_distance_negative_coordinates(self):
        """
        Test _haversine_distance with negative coordinates.
        
        Purpose: Verify function correctly handles southern and western hemispheres.
        Tests coordinate handling in different hemispheres.
        """
        from google_maps.SimulationEngine.utils import _haversine_distance
        
        # Test with negative coordinates (southern hemisphere)
        sydney = self.test_coordinates['sydney']  # Negative latitude
        sf = self.test_coordinates['san_francisco']  # Positive coordinates
        
        distance = _haversine_distance(
            sydney['lat'], sydney['lon'],
            sf['lat'], sf['lon']
        )
        
        # Should return positive distance regardless of coordinate signs
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
        # Distance should be approximately 12,000 km
        self.assertAlmostEqual(distance, 12000000, delta=1000000)


class TestSimulationEngineFileUtils(BaseTestCaseWithErrorHandler):
    """
    Test suite for file utility functions from file_utils.py.
    
    Purpose: Verify file utility functions work correctly for file operations,
    type detection, and encoding/decoding operations.
    """
    
    def setUp(self):
        """Set up test fixtures for file utility tests."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Test file paths for different file types
        self.test_files = {
            'text_py': os.path.join(self.temp_dir, 'test_script.py'),
            'text_json': os.path.join(self.temp_dir, 'test_data.json'),
            'text_html': os.path.join(self.temp_dir, 'test_page.html'),
            'binary_jpg': os.path.join(self.temp_dir, 'test_image.jpg'),
            'binary_pdf': os.path.join(self.temp_dir, 'test_document.pdf'),
            'unknown_ext': os.path.join(self.temp_dir, 'test_file.unknown'),
            'no_ext': os.path.join(self.temp_dir, 'test_file'),
            'nonexistent': os.path.join(self.temp_dir, 'nonexistent.txt')
        }
        
        # Test content for different scenarios
        self.test_content = {
            'simple_text': 'Hello, World!',
            'multiline_text': 'Line 1\nLine 2\nLine 3',
            'unicode_text': 'Hello 世界 🌍',
            'json_text': '{"name": "test", "value": 123}',
            'html_text': '<html><body><h1>Test</h1></body></html>',
            'python_code': 'def hello():\n    print("Hello, World!")\n',
            'binary_data': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01',
            'empty': ''
        }
        
        # Create test files with content
        self._create_test_files()
    
    def tearDown(self):
        """Clean up test fixtures and temporary files."""
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_files(self):
        """Helper method to create test files with various content types."""
        # Create text files
        with open(self.test_files['text_py'], 'w', encoding='utf-8') as f:
            f.write(self.test_content['python_code'])
        
        with open(self.test_files['text_json'], 'w', encoding='utf-8') as f:
            f.write(self.test_content['json_text'])
        
        with open(self.test_files['text_html'], 'w', encoding='utf-8') as f:
            f.write(self.test_content['html_text'])
        
        # Create binary files
        with open(self.test_files['binary_jpg'], 'wb') as f:
            f.write(self.test_content['binary_data'])
        
        with open(self.test_files['binary_pdf'], 'wb') as f:
            f.write(b'%PDF-1.4\n%test binary content')
        
        # Create file with unknown extension
        with open(self.test_files['unknown_ext'], 'w', encoding='utf-8') as f:
            f.write(self.test_content['simple_text'])
        
        # Create file without extension
        with open(self.test_files['no_ext'], 'w', encoding='utf-8') as f:
            f.write(self.test_content['simple_text'])
    
    def test_is_text_file_python_file(self):
        """
        Test is_text_file with Python file extension.
        
        Purpose: Verify Python files are correctly identified as text files.
        Tests common programming language file detection.
        """
        from google_maps.SimulationEngine.file_utils import is_text_file
        
        result = is_text_file(self.test_files['text_py'])
        
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
    
    def test_is_text_file_various_text_extensions(self):
        """
        Test is_text_file with various text file extensions.
        
        Purpose: Verify different text file types are correctly identified.
        Tests comprehensive text file extension support.
        """
        from google_maps.SimulationEngine.file_utils import is_text_file
        
        text_extensions = ['.py', '.js', '.html', '.json', '.csv', '.txt', '.md', '.sql']
        
        for ext in text_extensions:
            test_path = f'test_file{ext}'
            result = is_text_file(test_path)
            self.assertTrue(result, f"Extension {ext} should be identified as text")
    
    def test_is_text_file_case_insensitive(self):
        """
        Test is_text_file with uppercase extensions.
        
        Purpose: Verify case-insensitive extension handling.
        Tests robustness of extension detection.
        """
        from google_maps.SimulationEngine.file_utils import is_text_file
        
        uppercase_files = ['TEST.PY', 'TEST.JSON', 'TEST.HTML']
        
        for file_path in uppercase_files:
            result = is_text_file(file_path)
            self.assertTrue(result, f"Uppercase extension in {file_path} should be identified as text")
    
    def test_is_binary_file_image_file(self):
        """
        Test is_binary_file with image file extension.
        
        Purpose: Verify image files are correctly identified as binary files.
        Tests common binary file type detection.
        """
        from google_maps.SimulationEngine.file_utils import is_binary_file
        
        result = is_binary_file(self.test_files['binary_jpg'])
        
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
    
    def test_is_binary_file_various_binary_extensions(self):
        """
        Test is_binary_file with various binary file extensions.
        
        Purpose: Verify different binary file types are correctly identified.
        Tests comprehensive binary file extension support.
        """
        from google_maps.SimulationEngine.file_utils import is_binary_file
        
        binary_extensions = ['.jpg', '.pdf', '.exe', '.zip', '.mp3', '.mp4', '.xlsx']
        
        for ext in binary_extensions:
            test_path = f'test_file{ext}'
            result = is_binary_file(test_path)
            self.assertTrue(result, f"Extension {ext} should be identified as binary")
    
    def test_file_type_detection_unknown_extension(self):
        """
        Test file type detection with unknown extensions.
        
        Purpose: Verify behavior with unrecognized file extensions.
        Tests handling of edge cases in file type detection.
        """
        from google_maps.SimulationEngine.file_utils import is_text_file, is_binary_file
        
        # Unknown extension should not be identified as either text or binary
        unknown_result_text = is_text_file(self.test_files['unknown_ext'])
        unknown_result_binary = is_binary_file(self.test_files['unknown_ext'])
        
        self.assertFalse(unknown_result_text)
        self.assertFalse(unknown_result_binary)
        
        # File without extension
        no_ext_result_text = is_text_file(self.test_files['no_ext'])
        no_ext_result_binary = is_binary_file(self.test_files['no_ext'])
        
        self.assertFalse(no_ext_result_text)
        self.assertFalse(no_ext_result_binary)
    
    def test_get_mime_type_text_files(self):
        """
        Test get_mime_type with text file extensions.
        
        Purpose: Verify MIME type detection for text files.
        Tests MIME type accuracy for common text formats.
        """
        from google_maps.SimulationEngine.file_utils import get_mime_type
        
        # Test common text file MIME types
        mime_type_py = get_mime_type(self.test_files['text_py'])
        mime_type_json = get_mime_type(self.test_files['text_json'])
        mime_type_html = get_mime_type(self.test_files['text_html'])
        
        self.assertIsInstance(mime_type_py, str)
        self.assertIsInstance(mime_type_json, str)
        self.assertIsInstance(mime_type_html, str)
        
        # Verify expected MIME types
        self.assertIn('text', mime_type_py)
        self.assertEqual(mime_type_json, 'application/json')
        self.assertEqual(mime_type_html, 'text/html')
    
    def test_get_mime_type_binary_files(self):
        """
        Test get_mime_type with binary file extensions.
        
        Purpose: Verify MIME type detection for binary files.
        Tests MIME type accuracy for common binary formats.
        """
        from google_maps.SimulationEngine.file_utils import get_mime_type
        
        mime_type_jpg = get_mime_type(self.test_files['binary_jpg'])
        mime_type_pdf = get_mime_type(self.test_files['binary_pdf'])
        
        self.assertIsInstance(mime_type_jpg, str)
        self.assertIsInstance(mime_type_pdf, str)
        
        self.assertEqual(mime_type_jpg, 'image/jpeg')
        self.assertEqual(mime_type_pdf, 'application/pdf')
    
    def test_get_mime_type_unknown_extension(self):
        """
        Test get_mime_type with unknown file extension.
        
        Purpose: Verify default MIME type for unknown extensions.
        Tests fallback behavior for unrecognized files.
        """
        from google_maps.SimulationEngine.file_utils import get_mime_type
        
        mime_type = get_mime_type(self.test_files['unknown_ext'])
        
        self.assertEqual(mime_type, 'application/octet-stream')
    
    def test_read_file_text_content(self):
        """
        Test read_file with text file content.
        
        Purpose: Verify text file reading returns correct content and metadata.
        Tests normal text file reading operation.
        """
        from google_maps.SimulationEngine.file_utils import read_file
        
        result = read_file(self.test_files['text_py'])
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn('content', result)
        self.assertIn('encoding', result)
        self.assertIn('mime_type', result)
        self.assertIn('size_bytes', result)
        
        # Verify content
        self.assertEqual(result['content'], self.test_content['python_code'])
        self.assertEqual(result['encoding'], 'text')
        self.assertIn('text', result['mime_type'])
        self.assertGreater(result['size_bytes'], 0)
    
    def test_read_file_binary_content(self):
        """
        Test read_file with binary file content.
        
        Purpose: Verify binary file reading returns base64 encoded content.
        Tests binary file handling and base64 encoding.
        """
        from google_maps.SimulationEngine.file_utils import read_file
        
        result = read_file(self.test_files['binary_jpg'])
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['mime_type'], 'image/jpeg')
        self.assertGreater(result['size_bytes'], 0)
        
        # Verify content is valid base64
        self.assertIsInstance(result['content'], str)
        # Should be able to decode base64 content
        import base64
        decoded_content = base64.b64decode(result['content'])
        self.assertEqual(decoded_content, self.test_content['binary_data'])
    
    def test_read_file_nonexistent_file_error(self):
        """
        Test read_file error handling for nonexistent file.
        
        Purpose: Verify appropriate error when file doesn't exist.
        Critical because: Missing files should produce clear error messages.
        """
        from google_maps.SimulationEngine.file_utils import read_file
        
        self.assert_error_behavior(
            read_file,
            FileNotFoundError,
            f"File not found: {self.test_files['nonexistent']}",
            None,
            self.test_files['nonexistent']
        )
    
    def test_read_file_size_limit_error(self):
        """
        Test read_file error handling for file size limit.
        
        Purpose: Verify appropriate error when file exceeds size limit.
        Critical because: Large files should be rejected with clear error.
        """
        from google_maps.SimulationEngine.file_utils import read_file
        from common_utils.error_handling import get_package_error_mode
        
        # Create a larger test file that will exceed the small limit
        large_test_file = os.path.join(self.temp_dir, 'large_test.txt')
        large_content = 'x' * 2000  # 2KB of content
        with open(large_test_file, 'w', encoding='utf-8') as f:
            f.write(large_content)
        
        # Test with very small size limit that will be exceeded
        small_limit_mb = 0.001  # 1KB limit (1024 bytes)
        
        # Since ValueError message varies based on file size, test error type directly
        current_error_mode = get_package_error_mode()
        
        if current_error_mode == "raise":
            error_occurred = False
            try:
                read_file(large_test_file, small_limit_mb)
            except ValueError as e:
                error_occurred = True
                # Verify it's the correct type of ValueError
                self.assertIn("File too large", str(e))
            
            self.assertTrue(error_occurred, "Expected ValueError when file exceeds size limit")
        elif current_error_mode == "error_dict":
            result = read_file(large_test_file, small_limit_mb)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("exceptionType"), "ValueError")
    
    def test_write_file_text_content(self):
        """
        Test write_file with text content.
        
        Purpose: Verify text file writing works correctly.
        Tests file creation and content verification.
        """
        from google_maps.SimulationEngine.file_utils import write_file
        
        output_file = os.path.join(self.temp_dir, 'output_text.txt')
        test_content = self.test_content['unicode_text']
        
        # Write file
        write_file(output_file, test_content, 'text')
        
        # Verify file was created and has correct content
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, test_content)
    
    def test_write_file_binary_content(self):
        """
        Test write_file with binary content (base64).
        
        Purpose: Verify binary file writing with base64 encoding works correctly.
        Tests base64 decoding and binary file creation.
        """
        from google_maps.SimulationEngine.file_utils import write_file
        
        output_file = os.path.join(self.temp_dir, 'output_binary.bin')
        binary_data = self.test_content['binary_data']
        base64_content = base64.b64encode(binary_data).decode('utf-8')
        
        # Write file
        write_file(output_file, base64_content, 'base64')
        
        # Verify file was created and has correct binary content
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'rb') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, binary_data)
    
    def test_write_file_creates_directories(self):
        """
        Test write_file creates necessary directories.
        
        Purpose: Verify write_file creates parent directories when needed.
        Tests directory creation side effect.
        """
        from google_maps.SimulationEngine.file_utils import write_file
        
        nested_file = os.path.join(self.temp_dir, 'nested', 'deep', 'file.txt')
        test_content = self.test_content['simple_text']
        
        # Verify directory doesn't exist initially
        self.assertFalse(os.path.exists(os.path.dirname(nested_file)))
        
        # Write file
        write_file(nested_file, test_content, 'text')
        
        # Verify directory was created and file written
        self.assertTrue(os.path.exists(os.path.dirname(nested_file)))
        self.assertTrue(os.path.exists(nested_file))
        
        with open(nested_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertEqual(content, test_content)
    
    def test_encode_to_base64_string_input(self):
        """
        Test encode_to_base64 with string input.
        
        Purpose: Verify base64 encoding works correctly with string input.
        Tests string to base64 conversion.
        """
        from google_maps.SimulationEngine.file_utils import encode_to_base64
        
        test_string = self.test_content['unicode_text']
        result = encode_to_base64(test_string)
        
        self.assertIsInstance(result, str)
        
        # Verify encoding is correct by decoding
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, test_string)
    
    def test_encode_to_base64_bytes_input(self):
        """
        Test encode_to_base64 with bytes input.
        
        Purpose: Verify base64 encoding works correctly with bytes input.
        Tests bytes to base64 conversion.
        """
        from google_maps.SimulationEngine.file_utils import encode_to_base64
        
        test_bytes = self.test_content['binary_data']
        result = encode_to_base64(test_bytes)
        
        self.assertIsInstance(result, str)
        
        # Verify encoding is correct by decoding
        decoded = base64.b64decode(result)
        self.assertEqual(decoded, test_bytes)
    
    def test_decode_from_base64_valid_input(self):
        """
        Test decode_from_base64 with valid base64 input.
        
        Purpose: Verify base64 decoding works correctly with valid input.
        Tests base64 to bytes conversion.
        """
        from google_maps.SimulationEngine.file_utils import decode_from_base64
        
        test_data = self.test_content['binary_data']
        base64_string = base64.b64encode(test_data).decode('utf-8')
        
        result = decode_from_base64(base64_string)
        
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, test_data)
    
    def test_text_to_base64_conversion(self):
        """
        Test text_to_base64 conversion function.
        
        Purpose: Verify text to base64 conversion works correctly.
        Tests convenience function for text encoding.
        """
        from google_maps.SimulationEngine.file_utils import text_to_base64, base64_to_text
        
        test_text = self.test_content['unicode_text']
        
        # Convert to base64
        base64_result = text_to_base64(test_text)
        self.assertIsInstance(base64_result, str)
        
        # Convert back to text
        decoded_text = base64_to_text(base64_result)
        self.assertEqual(decoded_text, test_text)
    
    def test_base64_to_text_valid_input(self):
        """
        Test base64_to_text with valid base64 input.
        
        Purpose: Verify base64 to text conversion works correctly.
        Tests decoding of base64 encoded text.
        """
        from google_maps.SimulationEngine.file_utils import base64_to_text
        
        test_text = self.test_content['multiline_text']
        base64_string = base64.b64encode(test_text.encode('utf-8')).decode('utf-8')
        
        result = base64_to_text(base64_string)
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, test_text)
    
    def test_file_to_base64_conversion(self):
        """
        Test file_to_base64 with existing file.
        
        Purpose: Verify file reading and base64 encoding works correctly.
        Tests file to base64 conversion operation.
        """
        from google_maps.SimulationEngine.file_utils import file_to_base64
        
        result = file_to_base64(self.test_files['binary_jpg'])
        
        self.assertIsInstance(result, str)
        
        # Verify result by decoding and comparing
        decoded_content = base64.b64decode(result)
        self.assertEqual(decoded_content, self.test_content['binary_data'])
    
    def test_file_to_base64_nonexistent_file_error(self):
        """
        Test file_to_base64 error handling for nonexistent file.
        
        Purpose: Verify appropriate error when file doesn't exist.
        Critical because: Missing files should produce clear error messages.
        """
        from google_maps.SimulationEngine.file_utils import file_to_base64
        from common_utils.error_handling import get_package_error_mode
        
        # Since OSError message varies by system, test error type directly
        current_error_mode = get_package_error_mode()
        
        if current_error_mode == "raise":
            error_occurred = False
            try:
                file_to_base64(self.test_files['nonexistent'])
            except OSError:
                error_occurred = True
            
            self.assertTrue(error_occurred, "Expected OSError when reading nonexistent file")
        elif current_error_mode == "error_dict":
            result = file_to_base64(self.test_files['nonexistent'])
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("exceptionType"), "OSError")
    
    def test_base64_to_file_conversion(self):
        """
        Test base64_to_file with valid base64 content.
        
        Purpose: Verify base64 decoding and file writing works correctly.
        Tests base64 to file conversion operation.
        """
        from google_maps.SimulationEngine.file_utils import base64_to_file
        
        output_file = os.path.join(self.temp_dir, 'decoded_output.bin')
        test_data = self.test_content['binary_data']
        base64_content = base64.b64encode(test_data).decode('utf-8')
        
        # Convert base64 to file
        base64_to_file(base64_content, output_file)
        
        # Verify file was created with correct content
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'rb') as f:
            written_content = f.read()
        
        self.assertEqual(written_content, test_data)
    
    def test_base64_to_file_creates_directories(self):
        """
        Test base64_to_file creates necessary directories.
        
        Purpose: Verify base64_to_file creates parent directories when needed.
        Tests directory creation side effect.
        """
        from google_maps.SimulationEngine.file_utils import base64_to_file
        
        nested_file = os.path.join(self.temp_dir, 'nested', 'output.bin')
        test_data = self.test_content['binary_data']
        base64_content = base64.b64encode(test_data).decode('utf-8')
        
        # Verify directory doesn't exist initially
        self.assertFalse(os.path.exists(os.path.dirname(nested_file)))
        
        # Convert base64 to file
        base64_to_file(base64_content, nested_file)
        
        # Verify directory was created and file written
        self.assertTrue(os.path.exists(os.path.dirname(nested_file)))
        self.assertTrue(os.path.exists(nested_file))


if __name__ == '__main__':
    # Run all utility function test suites
    unittest.main(verbosity=2)
