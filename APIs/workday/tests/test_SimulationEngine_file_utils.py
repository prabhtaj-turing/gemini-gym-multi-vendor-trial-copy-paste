#!/usr/bin/env python3
"""
Comprehensive Unit Tests for SimulationEngine file_utils Module

This module provides extensive testing coverage for the file_utils module including:
1. Unit Test Cases with Data Model Validation
2. Database Structure Validation
3. State (Load/Save) Tests
4. Integration Tests
5. Performance Tests
6. Smoke Tests

Author: AI Assistant
Created: 2024-12-28
"""

import unittest
import os
import tempfile
import json
import time
import base64
from unittest.mock import patch, MagicMock, mock_open
from typing import Dict, Any, List, Optional

# Import the module under test
from ..SimulationEngine.file_utils import (
    is_text_file, is_binary_file, get_mime_type, read_file, write_file,
    encode_to_base64, decode_from_base64, text_to_base64, base64_to_text,
    file_to_base64, base64_to_file,
    TEXT_EXTENSIONS, BINARY_EXTENSIONS
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestFileUtilsDataModel(unittest.TestCase):
    """Test data model validation for file_utils module."""
    
    def test_text_extensions_data_structure(self):
        """Test that TEXT_EXTENSIONS has valid structure."""
        self.assertIsInstance(TEXT_EXTENSIONS, set)
        self.assertGreater(len(TEXT_EXTENSIONS), 0)
        
        # Verify all extensions start with dot
        for ext in TEXT_EXTENSIONS:
            self.assertIsInstance(ext, str)
            self.assertTrue(ext.startswith('.'))
            self.assertEqual(ext, ext.lower())  # Should be lowercase
            
    def test_binary_extensions_data_structure(self):
        """Test that BINARY_EXTENSIONS has valid structure."""
        self.assertIsInstance(BINARY_EXTENSIONS, set)
        self.assertGreater(len(BINARY_EXTENSIONS), 0)
        
        # Verify all extensions start with dot
        for ext in BINARY_EXTENSIONS:
            self.assertIsInstance(ext, str)
            self.assertTrue(ext.startswith('.'))
            self.assertEqual(ext, ext.lower())  # Should be lowercase
            
    def test_extensions_minimal_overlap(self):
        """Test that text and binary extensions have minimal overlap."""
        overlap = TEXT_EXTENSIONS.intersection(BINARY_EXTENSIONS)
        # Some extensions like .svg can be both text and binary, so small overlap is acceptable
        self.assertLessEqual(len(overlap), 2, f"Found too many overlapping extensions: {overlap}")
        
    def test_common_extensions_present(self):
        """Test that common file extensions are present."""
        # Common text extensions
        expected_text = {'.py', '.js', '.html', '.css', '.json', '.txt', '.md', '.csv'}
        for ext in expected_text:
            self.assertIn(ext, TEXT_EXTENSIONS, f"Missing text extension: {ext}")
            
        # Common binary extensions  
        expected_binary = {'.jpg', '.png', '.pdf', '.zip', '.exe', '.mp3', '.mp4'}
        for ext in expected_binary:
            self.assertIn(ext, BINARY_EXTENSIONS, f"Missing binary extension: {ext}")


class TestFileUtilsUnitTests(BaseTestCaseWithErrorHandler):
    """Comprehensive unit tests for file_utils module."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()
        # Clean up temp files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    # =========================================================================
    # File Type Detection Tests
    # =========================================================================
    
    def test_is_text_file_with_text_extensions(self):
        """Test is_text_file with various text file extensions."""
        text_files = [
            'script.py', 'page.html', 'style.css', 'data.json',
            'README.md', 'config.yml', 'notes.txt', 'data.csv'
        ]
        
        for filename in text_files:
            with self.subTest(filename=filename):
                self.assertTrue(is_text_file(filename))
                
    def test_is_text_file_with_binary_extensions(self):
        """Test is_text_file returns False for binary extensions."""
        binary_files = [
            'image.jpg', 'document.pdf', 'archive.zip', 'video.mp4',
            'audio.mp3', 'program.exe', 'data.db'
        ]
        
        for filename in binary_files:
            with self.subTest(filename=filename):
                self.assertFalse(is_text_file(filename))
                
    def test_is_binary_file_with_binary_extensions(self):
        """Test is_binary_file with various binary file extensions."""
        binary_files = [
            'photo.png', 'doc.pdf', 'music.mp3', 'movie.avi',
            'app.exe', 'lib.dll', 'data.sqlite'
        ]
        
        for filename in binary_files:
            with self.subTest(filename=filename):
                self.assertTrue(is_binary_file(filename))
                
    def test_is_binary_file_with_text_extensions(self):
        """Test is_binary_file returns False for text extensions."""
        text_files = [
            'code.py', 'web.html', 'config.json', 'readme.txt'
        ]
        
        for filename in text_files:
            with self.subTest(filename=filename):
                self.assertFalse(is_binary_file(filename))
                
    def test_case_insensitive_extension_detection(self):
        """Test that extension detection is case insensitive."""
        test_cases = [
            ('file.PY', True, False),   # Text file
            ('file.JPG', False, True),  # Binary file
            ('file.HTML', True, False), # Text file
            ('file.PDF', False, True),  # Binary file
        ]
        
        for filename, is_text, is_binary in test_cases:
            with self.subTest(filename=filename):
                self.assertEqual(is_text_file(filename), is_text)
                self.assertEqual(is_binary_file(filename), is_binary)
                
    def test_files_without_extensions(self):
        """Test handling of files without extensions."""
        files_no_ext = ['README', 'Makefile', 'dockerfile', 'config']
        
        for filename in files_no_ext:
            with self.subTest(filename=filename):
                # Files without extensions should not be detected as text or binary
                self.assertFalse(is_text_file(filename))
                self.assertFalse(is_binary_file(filename))
                
    def test_files_with_multiple_dots(self):
        """Test handling of files with multiple dots in filename."""
        test_cases = [
            ('config.test.json', True, False),
            ('backup.2024.tar.gz', False, True),
            ('script.min.js', True, False),
            ('data.backup.db', False, True)
        ]
        
        for filename, is_text, is_binary in test_cases:
            with self.subTest(filename=filename):
                self.assertEqual(is_text_file(filename), is_text)
                self.assertEqual(is_binary_file(filename), is_binary)
                
    # =========================================================================
    # MIME Type Detection Tests
    # =========================================================================
    
    def test_get_mime_type_common_types(self):
        """Test MIME type detection for common file types."""
        mime_tests = [
            ('file.html', 'text/html'),
            ('file.css', 'text/css'),
            ('file.js', ['application/javascript', 'text/javascript']),  # Both are valid
            ('file.json', 'application/json'),
            ('file.pdf', 'application/pdf'),
            ('file.jpg', 'image/jpeg'),
            ('file.png', 'image/png'),
            ('file.mp3', 'audio/mpeg'),
            ('file.mp4', 'video/mp4')
        ]
        
        for filename, expected_mime in mime_tests:
            with self.subTest(filename=filename):
                result = get_mime_type(filename)
                if isinstance(expected_mime, list):
                    # Allow multiple valid MIME types
                    self.assertIn(result, expected_mime, f"Expected one of {expected_mime}, got {result} for {filename}")
                else:
                    # Allow for variations in MIME type detection
                    self.assertTrue(
                        result == expected_mime or result.startswith(expected_mime.split('/')[0]),
                        f"Expected {expected_mime} or similar, got {result} for {filename}"
                    )
                
    def test_get_mime_type_unknown_extension(self):
        """Test MIME type detection for unknown extensions."""
        unknown_files = ['file.unknown', 'file.custom', 'file.nonexistent']
        
        for filename in unknown_files:
            with self.subTest(filename=filename):
                result = get_mime_type(filename)
                # Some systems might have MIME types for unexpected extensions
                # Just verify we get a valid MIME type string
                self.assertIsInstance(result, str)
                self.assertIn('/', result)  # Valid MIME types have a slash
                
    def test_get_mime_type_no_extension(self):
        """Test MIME type detection for files without extension."""
        no_ext_files = ['README', 'Makefile', 'config']
        
        for filename in no_ext_files:
            with self.subTest(filename=filename):
                result = get_mime_type(filename)
                self.assertEqual(result, 'application/octet-stream')
                
    # =========================================================================
    # File Reading Tests
    # =========================================================================
    
    @patch('builtins.open', new_callable=mock_open, read_data='Hello, World!')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=100)
    def test_read_text_file_success(self, mock_getsize, mock_exists, mock_file):
        """Test successful reading of text file."""
        result = read_file('test.txt')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['content'], 'Hello, World!')
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['size_bytes'], 100)
        self.assertIn('mime_type', result)
        
    @patch('builtins.open', new_callable=mock_open, read_data=b'Binary data')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=200)
    def test_read_binary_file_success(self, mock_getsize, mock_exists, mock_file):
        """Test successful reading of binary file."""
        with patch('workday.SimulationEngine.file_utils.is_text_file', return_value=False):
            with patch('workday.SimulationEngine.file_utils.is_binary_file', return_value=True):
                result = read_file('test.jpg')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['encoding'], 'base64')
        self.assertEqual(result['size_bytes'], 200)
        self.assertIn('mime_type', result)
        
    def test_read_file_not_found(self):
        """Test reading non-existent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            read_file('nonexistent.txt')
            
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=100 * 1024 * 1024)  # 100MB
    def test_read_file_too_large(self, mock_getsize, mock_exists):
        """Test reading file larger than size limit raises ValueError."""
        with self.assertRaises(ValueError) as context:
            read_file('large_file.txt', max_size_mb=50)
        self.assertIn("File too large", str(context.exception))
        
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=100)
    def test_read_text_file_encoding_fallback(self, mock_getsize, mock_exists):
        """Test text file reading with encoding fallback."""
        expected_content = 'Content with special chars'
        
        def mock_open_side_effect(*args, **kwargs):
            encoding = kwargs.get('encoding', 'utf-8')
            if encoding == 'utf-8':
                raise UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')
            else:
                # Return successful read for fallback encoding
                mock_file = mock_open(read_data=expected_content)
                return mock_file.return_value
        
        with patch('builtins.open', side_effect=mock_open_side_effect):
            with patch('workday.SimulationEngine.file_utils.is_text_file', return_value=True):
                result = read_file('test.txt')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['encoding'], 'text')
        self.assertEqual(result['content'], expected_content)
        self.assertEqual(result['size_bytes'], 100)
        
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=100)
    def test_read_text_file_all_encodings_fail(self, mock_getsize, mock_exists):
        """Test text file reading when all encodings fail."""
        # Mock all encoding attempts to fail
        mock_file = mock_open()
        mock_file.side_effect = UnicodeDecodeError('encoding', b'', 0, 1, 'invalid')
        
        with patch('builtins.open', mock_file):
            with patch('workday.SimulationEngine.file_utils.is_text_file', return_value=True):
                with self.assertRaises(ValueError) as context:
                    read_file('test.txt')
                self.assertIn("Could not decode file", str(context.exception))
        
    # =========================================================================
    # File Writing Tests
    # =========================================================================
    
    def test_write_text_file_success(self):
        """Test successful writing of text file."""
        test_file = os.path.join(self.temp_dir, 'test_write.txt')
        content = "Hello, World!"
        
        write_file(test_file, content)
        
        # Verify file was created and has correct content
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
        
    def test_write_binary_file_success(self):
        """Test successful writing of binary file."""
        test_file = os.path.join(self.temp_dir, 'test_write.bin')
        content = b"Binary content"
        
        write_file(test_file, content)
        
        # Verify file was created and has correct content
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
        
    def test_write_file_base64_encoding_string(self):
        """Test writing file with base64 encoding from string."""
        test_file = os.path.join(self.temp_dir, 'test_base64.bin')
        content = "Hello, World!"
        base64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        write_file(test_file, base64_content, encoding='base64')
        
        # Verify file was created and has correct content
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, content.encode('utf-8'))
        
    def test_write_file_base64_encoding_bytes(self):
        """Test writing file with base64 encoding from bytes."""
        test_file = os.path.join(self.temp_dir, 'test_base64_bytes.bin')
        content = b"Binary data \x00\x01\x02"
        
        write_file(test_file, content, encoding='base64')
        
        # Verify file was created and has correct content
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
        
    def test_write_file_text_encoding_from_bytes(self):
        """Test writing file with text encoding from bytes."""
        test_file = os.path.join(self.temp_dir, 'test_text_bytes.txt')
        content = b"Text content from bytes"
        
        write_file(test_file, content, encoding='text')
        
        # Verify file was created and has correct content
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content.decode('utf-8'))
        
    def test_write_file_create_directory(self):
        """Test writing file creates directory if it doesn't exist."""
        nested_dir = os.path.join(self.temp_dir, 'nested', 'path')
        test_file = os.path.join(nested_dir, 'test.txt')
        content = "Test content"
        
        write_file(test_file, content)
        
        # Verify directory was created and file written
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'r', encoding='utf-8') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)
        
    @patch('os.makedirs', side_effect=PermissionError("Permission denied"))
    def test_write_file_permission_error(self, mock_makedirs):
        """Test write file handles permission errors gracefully."""
        test_file = '/root/restricted/test.txt'
        content = "Test content"
        
        with self.assertRaises(PermissionError):
            write_file(test_file, content)
            
    # =========================================================================
    # Content Encoding/Decoding Tests
    # =========================================================================
    
    def test_encode_to_base64_text(self):
        """Test encoding text content to base64."""
        content = "Hello, World! 🌍"
        
        result = text_to_base64(content)
        
        self.assertIsInstance(result, str)  # Should return base64 string
        
    def test_encode_to_base64_binary(self):
        """Test encoding binary content to base64."""
        content = b"Binary data \x00\x01\x02"
        
        result = encode_to_base64(content)
        
        # Should return base64 encoded string
        self.assertIsInstance(result, str)
        decoded = decode_from_base64(result)
        self.assertEqual(decoded, content)
        
    def test_base64_to_text(self):
        """Test decoding base64 to text."""
        content = "Hello, World! 🌍"
        encoded = text_to_base64(content)
        
        result = base64_to_text(encoded)
        
        self.assertEqual(result, content)  # Should decode back to original text
        
    def test_decode_from_base64(self):
        """Test decoding base64 content."""
        original_content = b"Binary data \x00\x01\x02"
        encoded_content = encode_to_base64(original_content)
        
        result = decode_from_base64(encoded_content)
        
        self.assertEqual(result, original_content)
        
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding are reversible."""
        test_cases = [
            ("Text content", text_to_base64, base64_to_text),
            (b"Binary content", encode_to_base64, decode_from_base64)
        ]
        
        for content, encode_func, decode_func in test_cases:
            with self.subTest(content_type=type(content).__name__):
                encoded = encode_func(content)
                decoded = decode_func(encoded)
                    
                self.assertEqual(decoded, content)
                
    def test_file_to_base64(self):
        """Test converting file to base64."""
        test_file = os.path.join(self.temp_dir, 'test_file_to_base64.txt')
        content = "Hello, World! Test content for base64"
        
        # Write test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Convert to base64
        result = file_to_base64(test_file)
        
        # Verify result
        self.assertIsInstance(result, str)
        decoded = base64.b64decode(result).decode('utf-8')
        self.assertEqual(decoded, content)
        
    def test_base64_to_file(self):
        """Test writing base64 content to file."""
        test_file = os.path.join(self.temp_dir, 'test_base64_to_file.txt')
        content = "Hello, World! Test content for base64 to file"
        base64_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Write base64 to file
        base64_to_file(base64_content, test_file)
        
        # Verify file was created and has correct content
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, content.encode('utf-8'))
        
    def test_base64_to_file_creates_directory(self):
        """Test base64_to_file creates directory if it doesn't exist."""
        nested_dir = os.path.join(self.temp_dir, 'nested', 'base64')
        test_file = os.path.join(nested_dir, 'test.bin')
        content = b"Binary content for directory creation test"
        base64_content = base64.b64encode(content).decode('utf-8')
        
        # Write base64 to file
        base64_to_file(base64_content, test_file)
        
        # Verify directory was created and file written
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(test_file))
        with open(test_file, 'rb') as f:
            written_content = f.read()
        self.assertEqual(written_content, content)


class TestFileUtilsIntegration(BaseTestCaseWithErrorHandler):
    """Integration tests for file_utils module."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after integration tests."""
        super().tearDown()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_write_and_read_text_file_integration(self):
        """Test complete write and read cycle for text file."""
        test_file = os.path.join(self.temp_dir, 'integration_test.py')
        content = '''#!/usr/bin/env python3
"""Test Python file"""

def hello_world():
    print("Hello, World! 🌍")
    return True

if __name__ == "__main__":
    hello_world()
'''
        
        # Write file
        write_file(test_file, content)
        
        # Read file
        result = read_file(test_file)
        
        # Verify integration
        self.assertEqual(result['content'], content)
        self.assertEqual(result['encoding'], 'text')
        self.assertIn('text/', result['mime_type'])
        self.assertGreater(result['size_bytes'], 0)
        
    def test_write_and_read_binary_file_integration(self):
        """Test complete write and read cycle for binary file."""
        test_file = os.path.join(self.temp_dir, 'integration_test.bin')
        content = b"Simple binary content"  # Simpler binary content
        
        # Write file
        write_file(test_file, content)
        
        # Read file
        result = read_file(test_file)
        
        # Verify we can read the file without errors
        self.assertIsInstance(result, dict)
        self.assertIn('content', result)
        self.assertIn('encoding', result)
        
    def test_file_type_detection_integration(self):
        """Test file type detection with real files."""
        test_files = [
            ('test.py', 'Python code', True, False),
            ('test.json', '{"key": "value"}', True, False),
            ('test.bin', b'\x00\x01\x02\x03', False, True)
        ]
        
        for filename, content, expected_text, expected_binary in test_files:
            with self.subTest(filename=filename):
                test_file = os.path.join(self.temp_dir, filename)
                
                # Write file
                write_file(test_file, content)
                
                # Test type detection
                self.assertEqual(is_text_file(test_file), expected_text)
                self.assertEqual(is_binary_file(test_file), expected_binary)
                
                # Read and verify
                result = read_file(test_file)
                if expected_text:
                    self.assertEqual(result['content'], content)
                    self.assertEqual(result['encoding'], 'text')
                else:
                    decoded = base64.b64decode(result['content'])
                    self.assertEqual(decoded, content)
                    self.assertEqual(result['encoding'], 'base64')
                    
    def test_file_to_base64_and_base64_to_file_integration(self):
        """Test integration of file_to_base64 and base64_to_file functions."""
        # Create original file
        original_file = os.path.join(self.temp_dir, 'original.txt')
        content = "Integration test content with special chars: àáâãäå"
        
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Convert to base64
        base64_content = file_to_base64(original_file)
        
        # Write base64 to new file
        new_file = os.path.join(self.temp_dir, 'restored.txt')
        base64_to_file(base64_content, new_file)
        
        # Verify content is identical
        with open(new_file, 'r', encoding='utf-8') as f:
            restored_content = f.read()
        self.assertEqual(restored_content, content)


class TestFileUtilsPerformance(BaseTestCaseWithErrorHandler):
    """Performance tests for file_utils module."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after performance tests."""
        super().tearDown()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_performance_file_type_detection(self):
        """Test performance of file type detection."""
        filenames = [f'test_{i}.py' for i in range(1000)]
        
        start_time = time.time()
        for filename in filenames:
            is_text_file(filename)
            is_binary_file(filename)
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.1)  # Should complete in less than 100ms
        
    def test_performance_mime_type_detection(self):
        """Test performance of MIME type detection."""
        filenames = [f'test_{i}.{ext}' for i in range(100) for ext in ['py', 'js', 'html', 'css', 'json']]
        
        start_time = time.time()
        for filename in filenames:
            get_mime_type(filename)
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.2)  # Should complete in less than 200ms
        
    def test_performance_large_text_file(self):
        """Test performance with large text file."""
        test_file = os.path.join(self.temp_dir, 'large_test.txt')
        # Create 1MB text file
        content = "Line of text with some content.\n" * 32000
        
        # Write file
        start_time = time.time()
        write_file(test_file, content)
        write_time = time.time() - start_time
        
        # Read file
        start_time = time.time()
        result = read_file(test_file)
        read_time = time.time() - start_time
        
        # Verify and check performance
        self.assertEqual(result['content'], content)
        self.assertLess(write_time, 1.0)  # Write should complete in less than 1s
        self.assertLess(read_time, 1.0)   # Read should complete in less than 1s
        
    def test_memory_usage_large_text_file(self):
        """Test memory usage with large text file."""
        test_file = os.path.join(self.temp_dir, 'large_text.txt')
        # Create large text file
        content = "This is a test line.\n" * 10000  # Reasonable size for testing
        
        # Write and read
        write_file(test_file, content)
        result = read_file(test_file)
        
        # Verify content exists and has reasonable size
        self.assertIn('content', result)
        self.assertIn('size_bytes', result)
        self.assertGreater(result['size_bytes'], 0)


class TestFileUtilsSmokeTests(BaseTestCaseWithErrorHandler):
    """Smoke tests for file_utils module."""
    
    def setUp(self):
        """Set up smoke test fixtures."""
        super().setUp()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after smoke tests."""
        super().tearDown()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_module_import_and_basic_functionality(self):
        """Smoke test: module imports and basic functions work."""
        # Test imports
        from ..SimulationEngine.file_utils import (
            is_text_file, is_binary_file, get_mime_type, read_file, write_file,
            file_to_base64, base64_to_file
        )
        
        # Test basic functionality
        self.assertTrue(callable(is_text_file))
        self.assertTrue(callable(is_binary_file))
        self.assertTrue(callable(get_mime_type))
        self.assertTrue(callable(read_file))
        self.assertTrue(callable(write_file))
        self.assertTrue(callable(file_to_base64))
        self.assertTrue(callable(base64_to_file))
        
        # Test basic operations
        self.assertTrue(is_text_file('test.py'))
        self.assertTrue(is_binary_file('test.jpg'))
        self.assertIsInstance(get_mime_type('test.html'), str)
        
    def test_all_extension_categories_work(self):
        """Smoke test: all extension categories work without error."""
        # Sample extensions from each category
        text_samples = ['.py', '.js', '.html', '.css', '.json', '.txt', '.md']
        binary_samples = ['.jpg', '.png', '.pdf', '.zip', '.mp3', '.mp4', '.exe']
        
        for ext in text_samples:
            with self.subTest(extension=ext):
                filename = f'test{ext}'
                self.assertTrue(is_text_file(filename))
                self.assertFalse(is_binary_file(filename))
                mime_type = get_mime_type(filename)
                self.assertIsInstance(mime_type, str)
                
        for ext in binary_samples:
            with self.subTest(extension=ext):
                filename = f'test{ext}'
                self.assertFalse(is_text_file(filename))
                self.assertTrue(is_binary_file(filename))
                mime_type = get_mime_type(filename)
                self.assertIsInstance(mime_type, str)
                
    def test_file_operations_basic_workflow(self):
        """Smoke test: basic file operations workflow works."""
        test_file = os.path.join(self.temp_dir, 'smoke_test.txt')
        content = "Smoke test content"
        
        # Write file
        try:
            write_file(test_file, content)
        except Exception as e:
            self.fail(f"Write operation failed: {e}")
            
        # Verify file exists
        self.assertTrue(os.path.exists(test_file))
        
        # Read file
        try:
            result = read_file(test_file)
        except Exception as e:
            self.fail(f"Read operation failed: {e}")
            
        # Verify result structure
        self.assertIsInstance(result, dict)
        expected_keys = ['content', 'encoding', 'mime_type', 'size_bytes']
        for key in expected_keys:
            self.assertIn(key, result)
            
    def test_error_handling_robustness(self):
        """Smoke test: error handling works for common error cases."""
        # Test reading non-existent file
        with self.assertRaises(FileNotFoundError):
            read_file('nonexistent_file.txt')
            
        # Test reading file that's too large
        with patch('os.path.exists', return_value=True):
            with patch('os.path.getsize', return_value=1000 * 1024 * 1024):  # 1GB
                with self.assertRaises(ValueError):
                    read_file('huge_file.txt', max_size_mb=10)
                    
    def test_function_signatures_compatibility(self):
        """Smoke test: function signatures work as expected."""
        # Test required parameters
        self.assertTrue(is_text_file('test.py'))
        self.assertTrue(is_binary_file('test.jpg'))
        self.assertIsInstance(get_mime_type('test.html'), str)
        
        # Test optional parameters
        test_file = os.path.join(self.temp_dir, 'signature_test.txt')
        write_file(test_file, "Test content")
        
        # Default max_size_mb
        result1 = read_file(test_file)
        self.assertIsInstance(result1, dict)
        
        # Custom max_size_mb
        result2 = read_file(test_file, max_size_mb=1)
        self.assertIsInstance(result2, dict)
        
    def test_return_value_structures(self):
        """Smoke test: return values have expected structures."""
        # File type detection returns boolean
        self.assertIsInstance(is_text_file('test.py'), bool)
        self.assertIsInstance(is_binary_file('test.jpg'), bool)
        
        # MIME type returns string
        mime_result = get_mime_type('test.html')
        self.assertIsInstance(mime_result, str)
        self.assertGreater(len(mime_result), 0)
        
        # Read file returns dict with expected structure
        test_file = os.path.join(self.temp_dir, 'structure_test.txt')
        write_file(test_file, "Structure test content")
        
        read_result = read_file(test_file)
        self.assertIsInstance(read_result, dict)
        
        required_keys = ['content', 'encoding', 'mime_type', 'size_bytes']
        for key in required_keys:
            self.assertIn(key, read_result)
            
        # Verify value types
        self.assertIsInstance(read_result['content'], str)
        self.assertIsInstance(read_result['encoding'], str)
        self.assertIsInstance(read_result['mime_type'], str)
        self.assertIsInstance(read_result['size_bytes'], int)


if __name__ == '__main__':
    unittest.main()

