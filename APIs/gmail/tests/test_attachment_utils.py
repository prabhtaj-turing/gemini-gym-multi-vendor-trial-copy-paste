# tests/test_attachment_utils.py
import unittest
import os
import tempfile
import base64
from unittest.mock import patch, mock_open

from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler

from gmail.SimulationEngine.attachment_utils import (
    generate_attachment_id,
    calculate_file_checksum,
    calculate_data_checksum,
    create_attachment_from_file,
    create_attachment_from_data,
    get_attachment_from_global_collection,
    get_attachment_metadata_only,
    validate_attachment_structure,
    get_supported_mime_types,
    find_attachment_references_in_message,
    find_attachment_references_in_draft,
    count_total_attachments,
    get_attachment_size_stats
)
from gmail.SimulationEngine.db import DB


class TestAttachmentUtils(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        # Add attachments collection to DB
        DB["attachments"] = {}
        
        # Create temporary files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_text_file = os.path.join(self.temp_dir, "test.txt")
        self.test_image_file = os.path.join(self.temp_dir, "test.jpg")
        
        # Create test files
        with open(self.test_text_file, 'w') as f:
            f.write("Hello, World!")
        
        # Create a simple image file (1x1 pixel PNG)
        png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAHGbWaGEgAAAABJRU5ErkJggg==")
        with open(self.test_image_file, 'wb') as f:
            f.write(png_data)

    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_attachment_id(self):
        """Test attachment ID generation."""
        # Test default prefix
        att_id = generate_attachment_id()
        self.assertTrue(att_id.startswith("att_"))
        self.assertIn("_", att_id)
        
        # Test custom prefix
        att_id = generate_attachment_id("custom")
        self.assertTrue(att_id.startswith("custom_"))
        
        # Test uniqueness
        id1 = generate_attachment_id()
        id2 = generate_attachment_id()
        self.assertNotEqual(id1, id2)

    def test_calculate_file_checksum(self):
        """Test file checksum calculation."""
        checksum = calculate_file_checksum(self.test_text_file)
        self.assertTrue(checksum.startswith("sha256:"))
        
        # Same file should produce same checksum
        checksum2 = calculate_file_checksum(self.test_text_file)
        self.assertEqual(checksum, checksum2)

    def test_calculate_data_checksum(self):
        """Test data checksum calculation."""
        data = b"Hello, World!"
        checksum = calculate_data_checksum(data)
        self.assertTrue(checksum.startswith("sha256:"))
        
        # Same data should produce same checksum
        checksum2 = calculate_data_checksum(data)
        self.assertEqual(checksum, checksum2)

    def test_create_attachment_from_file(self):
        """Test creating attachment from file."""
        attachment = create_attachment_from_file(self.test_text_file)
        
        # Verify structure
        self.assertIn("attachmentId", attachment)
        self.assertIn("filename", attachment)
        self.assertIn("fileSize", attachment)
        self.assertIn("mimeType", attachment)
        self.assertIn("data", attachment)
        self.assertIn("checksum", attachment)
        self.assertIn("uploadDate", attachment)
        self.assertIn("encoding", attachment)
        
        # Verify values
        self.assertEqual(attachment["filename"], "test.txt")
        self.assertEqual(attachment["mimeType"], "text/plain")
        self.assertEqual(attachment["encoding"], "base64")
        self.assertTrue(attachment["fileSize"] > 0)
        self.assertTrue(attachment["checksum"].startswith("sha256:"))

    def test_create_attachment_from_file_custom_id(self):
        """Test creating attachment with custom ID."""
        custom_id = "custom_att_123"
        attachment = create_attachment_from_file(self.test_text_file, custom_id)
        self.assertEqual(attachment["attachmentId"], custom_id)

    def test_create_attachment_from_file_nonexistent(self):
        """Test creating attachment from nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            create_attachment_from_file("/nonexistent/file.txt")

    def test_create_attachment_from_data_string(self):
        """Test creating attachment from string data."""
        data = "Hello, World!"
        filename = "test.txt"
        attachment = create_attachment_from_data(data, filename)
        
        # Verify structure
        self.assertEqual(attachment["filename"], filename)
        self.assertEqual(attachment["mimeType"], "text/plain")
        self.assertEqual(attachment["encoding"], "base64")
        self.assertTrue(attachment["fileSize"] > 0)

    def test_create_attachment_from_data_bytes(self):
        """Test creating attachment from bytes data."""
        data = b"Hello, World!"
        filename = "test.txt"
        attachment = create_attachment_from_data(data, filename)
        
        self.assertEqual(attachment["filename"], filename)
        self.assertEqual(attachment["fileSize"], len(data))

    def test_create_attachment_from_data_custom_mime_type(self):
        """Test creating attachment with custom MIME type."""
        data = "Hello, World!"
        filename = "test.custom"
        mime_type = "application/custom"
        attachment = create_attachment_from_data(data, filename, mime_type)
        
        self.assertEqual(attachment["mimeType"], mime_type)

    def test_get_attachment_from_global_collection(self):
        """Test retrieving attachment from global collection."""
        # Store test attachment
        test_attachment = {
            "attachmentId": "test_att_001",
            "filename": "test.txt",
            "fileSize": 100,
            "mimeType": "text/plain",
            "data": "dGVzdA==",
            "checksum": "sha256:abc123",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        DB["attachments"]["test_att_001"] = test_attachment
        
        # Retrieve attachment
        retrieved = get_attachment_from_global_collection("test_att_001")
        self.assertEqual(retrieved, test_attachment)
        
        # Test nonexistent attachment
        nonexistent = get_attachment_from_global_collection("nonexistent")
        self.assertIsNone(nonexistent)

    def test_get_attachment_metadata_only(self):
        """Test extracting metadata without data field."""
        attachment = {
            "attachmentId": "test_att_001",
            "filename": "test.txt",
            "fileSize": 100,
            "mimeType": "text/plain",
            "data": "very_long_base64_data_here",
            "checksum": "sha256:abc123",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        
        metadata = get_attachment_metadata_only(attachment)
        
        # Should have all fields except data
        self.assertIn("attachmentId", metadata)
        self.assertIn("filename", metadata)
        self.assertIn("fileSize", metadata)
        self.assertNotIn("data", metadata)

    def test_validate_attachment_structure(self):
        """Test attachment structure validation."""
        # Valid attachment
        valid_attachment = {
            "attachmentId": "test_att_001",
            "filename": "test.txt",
            "fileSize": 100,
            "mimeType": "text/plain",
            "data": "dGVzdA==",
            "checksum": "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        self.assertTrue(validate_attachment_structure(valid_attachment))
        
        # Invalid attachment (missing required field)
        invalid_attachment = {
            "attachmentId": "test_att_001",
            "filename": "test.txt"
            # Missing required fields
        }
        self.assertFalse(validate_attachment_structure(invalid_attachment))

    def test_get_supported_mime_types(self):
        """Test getting supported MIME types."""
        mime_types = get_supported_mime_types()
        self.assertIsInstance(mime_types, list)
        self.assertIn("text/plain", mime_types)
        self.assertIn("application/pdf", mime_types)
        self.assertIn("image/jpeg", mime_types)

    def test_find_attachment_references_in_message(self):
        """Test finding attachment references in message."""
        # Create test message with attachments
        message = {
            "id": "msg_001",
            "payload": {
                "mimeType": "multipart/mixed",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "dGVzdA=="}
                    },
                    {
                        "mimeType": "image/jpeg",
                        "filename": "test.jpg",
                        "body": {"attachmentId": "att_001", "size": 1024}
                    },
                    {
                        "mimeType": "application/pdf",
                        "filename": "doc.pdf",
                        "body": {"attachmentId": "att_002", "size": 2048}
                    }
                ]
            }
        }
        
        DB["users"]["me"]["messages"]["msg_001"] = message
        
        attachment_ids = find_attachment_references_in_message("me", "msg_001")
        self.assertEqual(len(attachment_ids), 2)
        self.assertIn("att_001", attachment_ids)
        self.assertIn("att_002", attachment_ids)

    def test_find_attachment_references_in_message_nonexistent(self):
        """Test finding attachments in nonexistent message."""
        attachment_ids = find_attachment_references_in_message("me", "nonexistent")
        self.assertEqual(attachment_ids, [])

    def test_find_attachment_references_in_draft(self):
        """Test finding attachment references in draft."""
        # Create test draft with attachments
        draft = {
            "id": "draft_001",
            "message": {
                "payload": {
                    "mimeType": "multipart/mixed",
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": "dGVzdA=="}
                        },
                        {
                            "mimeType": "image/jpeg",
                            "filename": "test.jpg",
                            "body": {"attachmentId": "att_003", "size": 1024}
                        }
                    ]
                }
            }
        }
        
        DB["users"]["me"]["drafts"]["draft_001"] = draft
        
        attachment_ids = find_attachment_references_in_draft("me", "draft_001")
        self.assertEqual(len(attachment_ids), 1)
        self.assertIn("att_003", attachment_ids)

    def test_count_total_attachments(self):
        """Test counting total attachments."""
        # Initially should be 0
        self.assertEqual(count_total_attachments(), 0)
        
        # Add some attachments
        DB["attachments"]["att_001"] = {"attachmentId": "att_001"}
        DB["attachments"]["att_002"] = {"attachmentId": "att_002"}
        
        self.assertEqual(count_total_attachments(), 2)

    def test_get_attachment_size_stats(self):
        """Test getting attachment size statistics."""
        # Test with no attachments
        stats = get_attachment_size_stats()
        expected_empty_stats = {
            "totalCount": 0,
            "totalSize": 0,
            "averageSize": 0,
            "maxSize": 0,
            "minSize": 0
        }
        self.assertEqual(stats, expected_empty_stats)
        
        # Add test attachments
        DB["attachments"]["att_001"] = {"attachmentId": "att_001", "fileSize": 100}
        DB["attachments"]["att_002"] = {"attachmentId": "att_002", "fileSize": 200}
        DB["attachments"]["att_003"] = {"attachmentId": "att_003", "fileSize": 300}
        
        stats = get_attachment_size_stats()
        self.assertEqual(stats["totalCount"], 3)
        self.assertEqual(stats["totalSize"], 600)
        self.assertEqual(stats["averageSize"], 200)
        self.assertEqual(stats["maxSize"], 300)
        self.assertEqual(stats["minSize"], 100)


if __name__ == "__main__":
    unittest.main() 