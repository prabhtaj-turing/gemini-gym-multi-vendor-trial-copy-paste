# tests/test_file_utils.py
import unittest
import os
import tempfile
import base64

from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler

from gmail.SimulationEngine.file_utils import (
    is_text_file,
    is_binary_file,
    get_mime_type,
    validate_file_type,
    generate_attachment_id,
    calculate_checksum,
    read_file,
    write_file,
    encode_to_base64,
    decode_from_base64,
    text_to_base64,
    base64_to_text,
    file_to_base64,
    base64_to_file,
    encode_file_to_base64,
    decode_base64_to_file,
    FileProcessor,
    TEXT_EXTENSIONS,
    BINARY_EXTENSIONS,
    SUPPORTED_MIME_TYPES
)


class TestFileUtils(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        
        # Create temporary files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_text_file = os.path.join(self.temp_dir, "test.txt")
        self.test_python_file = os.path.join(self.temp_dir, "test.py")
        self.test_image_file = os.path.join(self.temp_dir, "test.jpg")
        self.test_pdf_file = os.path.join(self.temp_dir, "test.pdf")
        self.test_unsupported_file = os.path.join(self.temp_dir, "test.unsupported")
        
        # Create test files
        with open(self.test_text_file, 'w', encoding='utf-8') as f:
            f.write("Hello, World! This is a test file.")
        
        with open(self.test_python_file, 'w', encoding='utf-8') as f:
            f.write("print('Hello, Python!')")
        
        # Create a simple image file (1x1 pixel PNG)
        png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAHGbWaGEgAAAABJRU5ErkJggg==")
        with open(self.test_image_file, 'wb') as f:
            f.write(png_data)
        
        # Create a simple PDF file (minimal PDF structure)
        pdf_data = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000125 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n203\n%%EOF"
        with open(self.test_pdf_file, 'wb') as f:
            f.write(pdf_data)
        
        # Create unsupported file
        with open(self.test_unsupported_file, 'w') as f:
            f.write("unsupported content")

    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_is_text_file(self):
        """Test text file detection."""
        self.assertTrue(is_text_file(self.test_text_file))
        self.assertTrue(is_text_file(self.test_python_file))
        self.assertFalse(is_text_file(self.test_image_file))
        self.assertFalse(is_text_file(self.test_pdf_file))
        
        # Test with extensions
        self.assertTrue(is_text_file("test.js"))
        self.assertTrue(is_text_file("test.html"))
        self.assertTrue(is_text_file("test.css"))
        self.assertTrue(is_text_file("test.json"))
        self.assertFalse(is_text_file("test.exe"))

    def test_is_binary_file(self):
        """Test binary file detection."""
        self.assertFalse(is_binary_file(self.test_text_file))
        self.assertFalse(is_binary_file(self.test_python_file))
        self.assertTrue(is_binary_file(self.test_image_file))
        self.assertTrue(is_binary_file(self.test_pdf_file))
        
        # Test with extensions
        self.assertTrue(is_binary_file("test.jpg"))
        self.assertTrue(is_binary_file("test.pdf"))
        self.assertTrue(is_binary_file("test.zip"))
        self.assertFalse(is_binary_file("test.txt"))

    def test_get_mime_type(self):
        """Test MIME type detection."""
        self.assertEqual(get_mime_type(self.test_text_file), "text/plain")
        self.assertEqual(get_mime_type(self.test_python_file), "text/x-python")
        self.assertEqual(get_mime_type(self.test_image_file), "image/jpeg")
        self.assertEqual(get_mime_type(self.test_pdf_file), "application/pdf")
        
        # Test unknown extension
        self.assertEqual(get_mime_type(self.test_unsupported_file), "application/octet-stream")

    def test_validate_file_type(self):
        """Test file type validation for Gmail attachments."""
        self.assertTrue(validate_file_type(self.test_text_file))
        self.assertTrue(validate_file_type(self.test_python_file))
        self.assertTrue(validate_file_type(self.test_image_file))
        self.assertTrue(validate_file_type(self.test_pdf_file))
        
        # Unsupported file should return False
        self.assertFalse(validate_file_type(self.test_unsupported_file))

    def test_generate_attachment_id(self):
        """Test attachment ID generation."""
        # Test default prefix
        att_id = generate_attachment_id()
        self.assertTrue(att_id.startswith("att_"))
        
        # Test custom prefix
        att_id = generate_attachment_id("custom")
        self.assertTrue(att_id.startswith("custom_"))
        
        # Test uniqueness
        id1 = generate_attachment_id()
        id2 = generate_attachment_id()
        self.assertNotEqual(id1, id2)

    def test_calculate_checksum(self):
        """Test checksum calculation."""
        data = b"Hello, World!"
        checksum = calculate_checksum(data)
        self.assertTrue(checksum.startswith("sha256:"))
        
        # Same data should produce same checksum
        checksum2 = calculate_checksum(data)
        self.assertEqual(checksum, checksum2)
        
        # Different data should produce different checksum
        checksum3 = calculate_checksum(b"Different data")
        self.assertNotEqual(checksum, checksum3)

    def test_read_file_text(self):
        """Test reading text files."""
        result = read_file(self.test_text_file)
        
        self.assertEqual(result["encoding"], "text")
        self.assertEqual(result["mime_type"], "text/plain")
        self.assertIn("Hello, World!", result["content"])
        self.assertTrue(result["size_bytes"] > 0)

    def test_read_file_binary(self):
        """Test reading binary files."""
        result = read_file(self.test_image_file)
        
        self.assertEqual(result["encoding"], "base64")
        self.assertEqual(result["mime_type"], "image/jpeg")
        self.assertIsInstance(result["content"], str)  # base64 encoded
        self.assertTrue(result["size_bytes"] > 0)

    def test_read_file_nonexistent(self):
        """Test reading nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            read_file("/nonexistent/file.txt")

    def test_read_file_size_limit(self):
        """Test file size limit."""
        # Create large file
        large_file = os.path.join(self.temp_dir, "large.txt")
        with open(large_file, 'w') as f:
            f.write("x" * (2 * 1024 * 1024))  # 2MB file
        
        # Should work with default limit
        result = read_file(large_file)
        self.assertIsNotNone(result)
        
        # Should fail with small limit
        with self.assertRaises(ValueError):
            read_file(large_file, max_size_mb=1)

    def test_write_file_text(self):
        """Test writing text files."""
        output_file = os.path.join(self.temp_dir, "output.txt")
        content = "Hello, Output!"
        
        write_file(output_file, content, "text")
        
        # Verify file was written
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_write_file_base64(self):
        """Test writing base64 files."""
        output_file = os.path.join(self.temp_dir, "output.bin")
        original_data = b"Hello, Binary!"
        base64_content = base64.b64encode(original_data).decode('utf-8')
        
        write_file(output_file, base64_content, "base64")
        
        # Verify file was written
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'rb') as f:
            self.assertEqual(f.read(), original_data)

    def test_encode_decode_base64(self):
        """Test base64 encoding and decoding."""
        original_text = "Hello, World!"
        original_bytes = original_text.encode('utf-8')
        
        # Test string encoding
        encoded = encode_to_base64(original_text)
        decoded = decode_from_base64(encoded)
        self.assertEqual(decoded, original_bytes)
        
        # Test bytes encoding
        encoded = encode_to_base64(original_bytes)
        decoded = decode_from_base64(encoded)
        self.assertEqual(decoded, original_bytes)

    def test_text_base64_conversion(self):
        """Test text to base64 conversion utilities."""
        original_text = "Hello, World!"
        
        # Convert to base64
        base64_text = text_to_base64(original_text)
        self.assertIsInstance(base64_text, str)
        
        # Convert back to text
        decoded_text = base64_to_text(base64_text)
        self.assertEqual(decoded_text, original_text)

    def test_file_base64_conversion(self):
        """Test file to base64 conversion utilities."""
        # Convert file to base64
        base64_content = file_to_base64(self.test_text_file)
        self.assertIsInstance(base64_content, str)
        
        # Convert back to file
        output_file = os.path.join(self.temp_dir, "output_from_base64.txt")
        base64_to_file(base64_content, output_file)
        
        # Verify content matches
        with open(self.test_text_file, 'rb') as f1, open(output_file, 'rb') as f2:
            self.assertEqual(f1.read(), f2.read())

    def test_encode_file_to_base64(self):
        """Test comprehensive file encoding."""
        result = encode_file_to_base64(self.test_text_file)
        
        # Verify structure
        self.assertIn("filename", result)
        self.assertIn("fileSize", result)
        self.assertIn("mimeType", result)
        self.assertIn("data", result)
        self.assertIn("checksum", result)
        self.assertIn("uploadDate", result)
        self.assertIn("encoding", result)
        
        # Verify values
        self.assertEqual(result["filename"], "test.txt")
        self.assertEqual(result["mimeType"], "text/plain")
        self.assertEqual(result["encoding"], "base64")
        self.assertTrue(result["checksum"].startswith("sha256:"))

    def test_encode_file_to_base64_nonexistent(self):
        """Test encoding nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            encode_file_to_base64("/nonexistent/file.txt")

    def test_encode_file_to_base64_unsupported(self):
        """Test encoding unsupported file type."""
        with self.assertRaises(ValueError):
            encode_file_to_base64(self.test_unsupported_file)

    def test_decode_base64_to_file(self):
        """Test decoding base64 attachment to file."""
        # First encode a file
        encoded_result = encode_file_to_base64(self.test_text_file)
        
        # Create attachment data structure
        attachment_data = {
            "data": encoded_result["data"],
            "filename": encoded_result["filename"],
            "mimeType": encoded_result["mimeType"]
        }
        
        # Decode to new file
        output_file = os.path.join(self.temp_dir, "decoded_output.txt")
        decoded_bytes = decode_base64_to_file(attachment_data, output_file)
        
        # Verify file was created and content matches
        self.assertTrue(os.path.exists(output_file))
        with open(self.test_text_file, 'rb') as f1, open(output_file, 'rb') as f2:
            self.assertEqual(f1.read(), f2.read())
        
        # Verify returned bytes
        with open(self.test_text_file, 'rb') as f:
            self.assertEqual(decoded_bytes, f.read())

    def test_decode_base64_to_file_missing_data(self):
        """Test decoding attachment without data field."""
        attachment_data = {"filename": "test.txt"}
        
        with self.assertRaises(ValueError):
            decode_base64_to_file(attachment_data, "output.txt")

    def test_file_processor_class(self):
        """Test FileProcessor class functionality."""
        processor = FileProcessor(max_size_mb=10)
        
        # Test encoding
        result = processor.encode_file_to_base64(self.test_text_file)
        self.assertIn("filename", result)
        
        # Test decoding
        output_file = os.path.join(self.temp_dir, "processor_output.txt")
        decoded_bytes = processor.decode_base64_to_file(result, output_file)
        self.assertIsInstance(decoded_bytes, bytes)
        
        # Test validation
        self.assertTrue(processor.validate_file_type(self.test_text_file))
        self.assertFalse(processor.validate_file_type(self.test_unsupported_file))
        
        # Test ID generation
        att_id = processor.generate_attachment_id()
        self.assertTrue(att_id.startswith("att_"))
        
        # Test checksum
        checksum = processor.calculate_checksum(b"test")
        self.assertTrue(checksum.startswith("sha256:"))
        
        # Test file size validation
        self.assertTrue(processor.validate_file_size(self.test_text_file))
        
        # Test file info
        info = processor.get_file_info(self.test_text_file)
        self.assertIn("filename", info)
        self.assertIn("fileSize", info)
        self.assertIn("mimeType", info)
        self.assertIn("isTextFile", info)
        self.assertIn("isBinaryFile", info)
        self.assertIn("isSupported", info)
        self.assertIn("withinSizeLimit", info)
        self.assertIn("extension", info)
        
        # Test supported MIME types
        mime_types = processor.get_supported_mime_types()
        self.assertIsInstance(mime_types, list)
        self.assertIn("text/plain", mime_types)

    def test_file_processor_size_limit(self):
        """Test FileProcessor with custom size limit."""
        processor = FileProcessor(max_size_mb=1)  # 1MB limit
        
        # Create file larger than limit
        large_file = os.path.join(self.temp_dir, "large.txt")
        with open(large_file, 'w') as f:
            f.write("x" * (2 * 1024 * 1024))  # 2MB file
        
        # Should fail validation
        self.assertFalse(processor.validate_file_size(large_file))
        
        # File info should indicate it's over limit
        info = processor.get_file_info(large_file)
        self.assertFalse(info["withinSizeLimit"])

    def test_extensions_and_mime_types_coverage(self):
        """Test that extension sets and MIME types are comprehensive."""
        # Test that we have good coverage of common file types
        self.assertIn(".py", TEXT_EXTENSIONS)
        self.assertIn(".js", TEXT_EXTENSIONS)
        self.assertIn(".html", TEXT_EXTENSIONS)
        self.assertIn(".css", TEXT_EXTENSIONS)
        self.assertIn(".json", TEXT_EXTENSIONS)
        self.assertIn(".md", TEXT_EXTENSIONS)
        
        self.assertIn(".jpg", BINARY_EXTENSIONS)
        self.assertIn(".png", BINARY_EXTENSIONS)
        self.assertIn(".pdf", BINARY_EXTENSIONS)
        self.assertIn(".zip", BINARY_EXTENSIONS)
        self.assertIn(".mp4", BINARY_EXTENSIONS)
        
        # Test MIME types
        self.assertIn("text/plain", SUPPORTED_MIME_TYPES)
        self.assertIn("application/pdf", SUPPORTED_MIME_TYPES)
        self.assertIn("image/jpeg", SUPPORTED_MIME_TYPES)
        self.assertIn("application/json", SUPPORTED_MIME_TYPES)
        
        # Verify no overlap between text and binary extensions
        overlap = TEXT_EXTENSIONS.intersection(BINARY_EXTENSIONS)
        self.assertEqual(len(overlap), 0, f"Found overlapping extensions: {overlap}")


if __name__ == "__main__":
    unittest.main() 