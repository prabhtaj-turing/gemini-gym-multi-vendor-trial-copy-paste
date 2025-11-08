from google_docs import create_document
import google_docs.SimulationEngine.db as db_module
from common_utils.base_case import BaseTestCaseWithErrorHandler
from freezegun import freeze_time
import importlib
import sys


class TestCreateDocumentTimestamps(BaseTestCaseWithErrorHandler):
    """Test that create_document uses current time for timestamps, not fixed values."""
    
    def setUp(self):
        """Reset DB before each test."""
        super().setUp()
        
        # Reload modules to ensure fresh DB references
        modules_to_reload = ['google_docs.Documents']
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
        
        # Reload imports
        global create_document
        from google_docs import create_document
        
        db_module.DB.clear()
        db_module.DB.update({
            "users": {
                "me": {
                    "about": {
                        "user": {
                            "emailAddress": "test@example.com",
                            "displayName": "Test User"
                        }
                    },
                    "files": {},
                    "counters": {"file": 0, "document": 0}
                }
            }
        })
        
    @freeze_time("2024-01-15T10:30:45Z")
    def test_created_document_has_current_timestamp(self):
        """Test that newly created document has current time, not hardcoded timestamp.
        
        BUG: Function returns hardcoded timestamp "2025-03-11T09:00:00Z" instead
        of using the current time. This makes all documents appear to be created
        at the same fixed time.
        """
        doc, status = create_document(title="Test Doc")
        
        # Verify document was created successfully
        self.assertEqual(status, 200)
        self.assertEqual(doc["name"], "Test Doc")
        
        # CRITICAL: Timestamps should reflect the current frozen time
        # This will FAIL if using hardcoded timestamps
        self.assertEqual(doc["createdTime"], "2024-01-15T10:30:45Z",
                        f"Expected createdTime to be current time (2024-01-15T10:30:45Z), got {doc['createdTime']}")
        self.assertEqual(doc["modifiedTime"], "2024-01-15T10:30:45Z",
                        f"Expected modifiedTime to match createdTime at creation, got {doc['modifiedTime']}")
        
    @freeze_time("2023-06-20T14:15:30Z")
    def test_multiple_documents_have_different_timestamps_when_created_at_different_times(self):
        """Test that documents created at different times have different timestamps."""
        # Create first document at frozen time
        doc1, _ = create_document(title="First Doc")
        first_timestamp = doc1["createdTime"]
        
        # Move time forward
        with freeze_time("2023-06-20T16:45:00Z"):
            doc2, _ = create_document(title="Second Doc")
            second_timestamp = doc2["createdTime"]
        
        # Timestamps should be different
        # This will FAIL if using hardcoded timestamps (both would be "2025-03-11T09:00:00Z")
        self.assertNotEqual(first_timestamp, second_timestamp,
                           "Documents created at different times should have different timestamps")
        self.assertEqual(first_timestamp, "2023-06-20T14:15:30Z")
        self.assertEqual(second_timestamp, "2023-06-20T16:45:00Z")
        
    @freeze_time("2024-12-25T00:00:00Z")
    def test_created_and_modified_time_are_same_at_creation(self):
        """Test that createdTime and modifiedTime are the same when document is first created."""
        doc, _ = create_document(title="New Doc")
        
        # At creation, both timestamps should be identical and match current time
        self.assertEqual(doc["createdTime"], doc["modifiedTime"],
                        "createdTime and modifiedTime should be identical at creation")
        self.assertEqual(doc["createdTime"], "2024-12-25T00:00:00Z",
                        "Both timestamps should reflect current time at creation")

