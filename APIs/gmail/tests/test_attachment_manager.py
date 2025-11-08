# tests/test_attachment_manager.py
import unittest
import os
import tempfile
import base64

from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler

from gmail.SimulationEngine.attachment_manager import (
    store_attachment_in_db,
    create_payload_with_attachments,
    create_message_payload_from_files,
    add_attachment_to_message_payload,
    add_attachment_to_draft_payload,
    add_attachment_data_to_message,
    remove_attachment_from_message,
    get_attachment_by_id,
    get_attachment_metadata,
    list_message_attachments,
    list_user_attachments,
    validate_attachment,
    get_attachment_stats,
    get_supported_file_types,
    get_supported_mime_types
)
from gmail.SimulationEngine.db import DB


class TestAttachmentManager(BaseTestCaseWithErrorHandler):
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

    def test_store_attachment_in_db(self):
        """Test storing attachment in database."""
        attachment = {
            "attachmentId": "test_att_001",
            "filename": "test.txt",
            "fileSize": 100,
            "mimeType": "text/plain",
            "data": "dGVzdA==",
            "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        
        store_attachment_in_db(attachment)
        
        # Verify stored in DB
        self.assertIn("test_att_001", DB["attachments"])
        self.assertEqual(DB["attachments"]["test_att_001"], attachment)

    def test_create_payload_with_attachments_no_attachments(self):
        """Test creating payload with no attachments."""
        payload = create_payload_with_attachments("Hello World", [])
        
        expected_data = base64.b64encode("Hello World".encode('utf-8')).decode('utf-8')
        
        self.assertEqual(payload["mimeType"], "text/plain")
        self.assertEqual(len(payload["parts"]), 1)
        self.assertEqual(payload["parts"][0]["mimeType"], "text/plain")
        self.assertEqual(payload["parts"][0]["body"]["data"], expected_data)

    def test_create_payload_with_attachments_with_attachments(self):
        """Test creating payload with attachments."""
        # Store test attachments
        attachment1 = {
            "attachmentId": "att_001",
            "filename": "test.jpg",
            "fileSize": 1024,
            "mimeType": "image/jpeg",
            "data": "base64data",
            "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        attachment2 = {
            "attachmentId": "att_002",
            "filename": "doc.pdf",
            "fileSize": 2048,
            "mimeType": "application/pdf",
            "data": "base64data",
            "checksum": "sha256:f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        
        DB["attachments"]["att_001"] = attachment1
        DB["attachments"]["att_002"] = attachment2
        
        payload = create_payload_with_attachments("Hello World", ["att_001", "att_002"])
        
        self.assertEqual(payload["mimeType"], "multipart/mixed")
        self.assertEqual(len(payload["parts"]), 3)  # 1 text + 2 attachments
        
        # Check text part
        self.assertEqual(payload["parts"][0]["mimeType"], "text/plain")
        
        # Check attachment parts
        self.assertEqual(payload["parts"][1]["mimeType"], "image/jpeg")
        self.assertEqual(payload["parts"][1]["filename"], "test.jpg")
        self.assertEqual(payload["parts"][1]["body"]["attachmentId"], "att_001")
        self.assertEqual(payload["parts"][1]["body"]["size"], 1024)
        
        self.assertEqual(payload["parts"][2]["mimeType"], "application/pdf")
        self.assertEqual(payload["parts"][2]["filename"], "doc.pdf")
        self.assertEqual(payload["parts"][2]["body"]["attachmentId"], "att_002")
        self.assertEqual(payload["parts"][2]["body"]["size"], 2048)

    def test_create_message_payload_from_files(self):
        """Test creating complete message payload from files."""
        payload = create_message_payload_from_files(
            body_text="Hello with attachment",
            file_paths=[self.test_text_file],
            subject="Test Subject",
            to="test@example.com",
            from_email="sender@example.com"
        )
        
        # Check headers
        self.assertIn("headers", payload)
        headers = {h["name"]: h["value"] for h in payload["headers"]}
        self.assertEqual(headers["Subject"], "Test Subject")
        self.assertEqual(headers["To"], "test@example.com")
        self.assertEqual(headers["From"], "sender@example.com")
        
        # Check payload structure
        self.assertEqual(payload["mimeType"], "multipart/mixed")
        self.assertEqual(len(payload["parts"]), 2)  # text + attachment

    def test_create_message_payload_from_files_nonexistent(self):
        """Test creating payload with nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            create_message_payload_from_files(
                body_text="Hello",
                file_paths=["/nonexistent/file.txt"]
            )

    def test_add_attachment_to_message_payload(self):
        """Test adding attachment to existing message."""
        # Create test message
        message = {
            "id": "msg_001",
            "body": "Original message",
            "payload": {
                "mimeType": "text/plain",
                "body": {"data": "T3JpZ2luYWwgbWVzc2FnZQ=="}  # "Original message" in base64
            }
        }
        DB["users"]["me"]["messages"]["msg_001"] = message
        
        # Add attachment
        attachment = add_attachment_to_message_payload("me", "msg_001", self.test_text_file)
        
        # Verify attachment was created and stored
        self.assertIn("attachmentId", attachment)
        self.assertIn(attachment["attachmentId"], DB["attachments"])
        
        # Verify message payload was updated
        updated_message = DB["users"]["me"]["messages"]["msg_001"]
        self.assertEqual(updated_message["payload"]["mimeType"], "multipart/mixed")
        self.assertEqual(len(updated_message["payload"]["parts"]), 2)

    def test_add_attachment_to_draft_payload(self):
        """Test adding attachment to existing draft."""
        # Create test draft
        draft = {
            "id": "draft_001",
            "message": {
                "body": "Draft message",
                "payload": {
                    "mimeType": "text/plain",
                    "body": {"data": "RHJhZnQgbWVzc2FnZQ=="}  # "Draft message" in base64
                }
            }
        }
        DB["users"]["me"]["drafts"]["draft_001"] = draft
        
        # Add attachment
        attachment = add_attachment_to_draft_payload("me", "draft_001", self.test_text_file)
        
        # Verify attachment was created and stored
        self.assertIn("attachmentId", attachment)
        self.assertIn(attachment["attachmentId"], DB["attachments"])
        
        # Verify draft payload was updated
        updated_draft = DB["users"]["me"]["drafts"]["draft_001"]
        self.assertEqual(updated_draft["message"]["payload"]["mimeType"], "multipart/mixed")
        self.assertEqual(len(updated_draft["message"]["payload"]["parts"]), 2)

    def test_add_attachment_data_to_message(self):
        """Test adding attachment from raw data to message."""
        # Create test message
        message = {"id": "msg_001", "body": "Test message"}
        DB["users"]["me"]["messages"]["msg_001"] = message
        
        # Add attachment from data
        data = "Hello, World!"
        filename = "hello.txt"
        attachment = add_attachment_data_to_message("me", "msg_001", data, filename)
        
        # Verify attachment was created
        self.assertEqual(attachment["filename"], filename)
        self.assertEqual(attachment["mimeType"], "text/plain")
        self.assertIn(attachment["attachmentId"], DB["attachments"])

    def test_remove_attachment_from_message(self):
        """Test removing attachment from message."""
        # Create message with attachments
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
        
        # Remove one attachment
        result = remove_attachment_from_message("me", "msg_001", "att_001")
        self.assertTrue(result)
        
        # Verify attachment was removed
        updated_message = DB["users"]["me"]["messages"]["msg_001"]
        attachment_ids = [
            part.get("body", {}).get("attachmentId") 
            for part in updated_message["payload"]["parts"]
        ]
        self.assertNotIn("att_001", attachment_ids)
        self.assertIn("att_002", attachment_ids)

    def test_remove_attachment_from_message_convert_to_single_part(self):
        """Test removing last attachment converts back to single-part."""
        # Create message with one attachment
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
                    }
                ]
            }
        }
        DB["users"]["me"]["messages"]["msg_001"] = message
        
        # Remove the attachment
        result = remove_attachment_from_message("me", "msg_001", "att_001")
        self.assertTrue(result)
        
        # Verify converted back to single-part
        updated_message = DB["users"]["me"]["messages"]["msg_001"]
        self.assertEqual(updated_message["payload"]["mimeType"], "text/plain")
        self.assertIn("body", updated_message["payload"])
        self.assertNotIn("parts", updated_message["payload"])

    def test_get_attachment_by_id(self):
        """Test getting attachment by ID."""
        # Store test attachment
        attachment = {
            "attachmentId": "test_att_001",
            "filename": "test.txt",
            "fileSize": 100,
            "mimeType": "text/plain",
            "data": "dGVzdA==",
            "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        DB["attachments"]["test_att_001"] = attachment
        
        retrieved = get_attachment_by_id("test_att_001")
        self.assertEqual(retrieved, attachment)
        
        # Test nonexistent
        self.assertIsNone(get_attachment_by_id("nonexistent"))

    def test_get_attachment_metadata(self):
        """Test getting attachment metadata without data."""
        # Store test attachment
        attachment = {
            "attachmentId": "test_att_001",
            "filename": "test.txt",
            "fileSize": 100,
            "mimeType": "text/plain",
            "data": "very_long_base64_data",
            "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        DB["attachments"]["test_att_001"] = attachment
        
        metadata = get_attachment_metadata("test_att_001")
        
        self.assertIn("attachmentId", metadata)
        self.assertIn("filename", metadata)
        self.assertNotIn("data", metadata)

    def test_list_message_attachments(self):
        """Test listing attachments for a message."""
        # Create message with attachments
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
                    }
                ]
            }
        }
        DB["users"]["me"]["messages"]["msg_001"] = message
        
        # Store attachment
        attachment = {
            "attachmentId": "att_001",
            "filename": "test.jpg",
            "fileSize": 1024,
            "mimeType": "image/jpeg",
            "data": "base64data",
            "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        DB["attachments"]["att_001"] = attachment
        
        # List attachments without data
        attachments = list_message_attachments("me", "msg_001", include_data=False)
        self.assertEqual(len(attachments), 1)
        self.assertNotIn("data", attachments[0])
        
        # List attachments with data
        attachments = list_message_attachments("me", "msg_001", include_data=True)
        self.assertEqual(len(attachments), 1)
        self.assertIn("data", attachments[0])

    def test_list_user_attachments(self):
        """Test listing all attachments for a user."""
        # Create message with attachment
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
                    }
                ]
            }
        }
        DB["users"]["me"]["messages"]["msg_001"] = message
        
        # Create draft with attachment
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
                            "mimeType": "application/pdf",
                            "filename": "doc.pdf",
                            "body": {"attachmentId": "att_002", "size": 2048}
                        }
                    ]
                }
            }
        }
        DB["users"]["me"]["drafts"]["draft_001"] = draft
        
        # Store attachments
        DB["attachments"]["att_001"] = {
            "attachmentId": "att_001",
            "filename": "test.jpg",
            "fileSize": 1024,
            "mimeType": "image/jpeg",
            "data": "base64data1",
            "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        DB["attachments"]["att_002"] = {
            "attachmentId": "att_002",
            "filename": "doc.pdf",
            "fileSize": 2048,
            "mimeType": "application/pdf",
            "data": "base64data2",
            "checksum": "sha256:f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        
        # List user attachments
        attachments = list_user_attachments("me", include_data=False)
        self.assertEqual(len(attachments), 2)
        
        # Verify no data field
        for attachment in attachments:
            self.assertNotIn("data", attachment)

    def test_validate_attachment(self):
        """Test attachment validation."""
        # Valid attachment
        valid_attachment = {
            "attachmentId": "test_att_001",
            "filename": "test.txt",
            "fileSize": 100,
            "mimeType": "text/plain",
            "data": "dGVzdA==",
            "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "uploadDate": "2024-01-01T00:00:00Z",
            "encoding": "base64"
        }
        self.assertTrue(validate_attachment(valid_attachment))
        
        # Invalid attachment
        invalid_attachment = {"attachmentId": "test_att_001"}
        self.assertFalse(validate_attachment(invalid_attachment))

    def test_get_attachment_stats(self):
        """Test getting attachment statistics for user."""
        # Create attachments
        DB["attachments"]["att_001"] = {
            "attachmentId": "att_001",
            "filename": "test1.txt",
            "fileSize": 100,
            "mimeType": "text/plain"
        }
        DB["attachments"]["att_002"] = {
            "attachmentId": "att_002",
            "filename": "test2.jpg",
            "fileSize": 200,
            "mimeType": "image/jpeg"
        }
        
        # Create message and draft with these attachments
        message = {
            "payload": {
                "parts": [
                    {"body": {"attachmentId": "att_001"}}
                ]
            }
        }
        draft = {
            "message": {
                "payload": {
                    "parts": [
                        {"body": {"attachmentId": "att_002"}}
                    ]
                }
            }
        }
        
        DB["users"]["me"]["messages"]["msg_001"] = message
        DB["users"]["me"]["drafts"]["draft_001"] = draft
        
        stats = get_attachment_stats("me")
        
        self.assertEqual(stats["totalCount"], 2)
        self.assertEqual(stats["totalSize"], 300)
        self.assertEqual(stats["averageSize"], 150)
        self.assertIn("mimeTypeBreakdown", stats)

    def test_get_supported_file_types(self):
        """Test getting supported file types."""
        file_types = get_supported_file_types()
        self.assertIsInstance(file_types, list)
        self.assertIn(".txt", file_types)
        self.assertIn(".pdf", file_types)
        self.assertIn(".jpg", file_types)

    def test_get_supported_mime_types_manager(self):
        """Test getting supported MIME types from manager."""
        mime_types = get_supported_mime_types()
        self.assertIsInstance(mime_types, list)
        self.assertIn("text/plain", mime_types)
        self.assertIn("application/pdf", mime_types)
        self.assertIn("image/jpeg", mime_types)

    def test_error_handling_invalid_user(self):
        """Test error handling for invalid user."""
        self.assert_error_behavior(
            add_attachment_to_message_payload,
            ValueError,
            "User 'nonexistent' does not exist.",
            user_id="nonexistent",
            message_id="msg_001",
            file_path=self.test_text_file
        )

    def test_error_handling_invalid_message(self):
        """Test error handling for invalid message."""
        self.assert_error_behavior(
            add_attachment_to_message_payload,
            ValueError,
            "Message nonexistent not found for user me",
            user_id="me",
            message_id="nonexistent",
            file_path=self.test_text_file
        )

    def test_error_handling_file_not_found(self):
        """Test error handling for non-existent file."""
        # Create a test message first
        DB["users"]["me"]["messages"]["msg_001"] = {
            "id": "msg_001",
            "body": "Test message"
        }
        
        # Test with non-existent file
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.txt")
        
        self.assert_error_behavior(
            add_attachment_to_message_payload,
            FileNotFoundError,
            f"File not found: {nonexistent_file}",
            user_id="me",
            message_id="msg_001",
            file_path=nonexistent_file
        )


if __name__ == "__main__":
    unittest.main() 