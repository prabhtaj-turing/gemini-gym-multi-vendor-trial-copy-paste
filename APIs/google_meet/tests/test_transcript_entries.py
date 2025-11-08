import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler

from google_meet.tests.common import reset_db
from google_meet import Entries
from google_meet import DB


class TestTranscriptEntries(BaseTestCaseWithErrorHandler):

    def setUp(self):
        reset_db()
        # Create test transcript for parent reference
        DB["transcripts"]["trans1"] = {
            "id": "trans1",
            "parent": "conf1",
            "start_time": "10:00",
            "language_code": "en-US",
        }

    def test_entry_get(self):
        # Test getting an entry that exists
        DB["entries"]["entry1"] = {
            "id": "entry1",
            "parent": "trans1",
            "start_time": "10:15",
            "text": "Test entry text",
            "speaker": "User 1",
        }

        result = Entries.get("entry1")
        self.assertEqual(result["id"], "entry1")
        self.assertEqual(result["parent"], "trans1")
        self.assertEqual(result["text"], "Test entry text")
        self.assertEqual(result["speaker"], "User 1")

        # Test getting an entry that doesn't exist
        with self.assertRaises(ValueError) as cm:
            Entries.get("nonexistent_entry")
        self.assertEqual(str(cm.exception), "Entry nonexistent_entry not found")

    def test_entry_get_invalid_input_types(self):
        # Test with non-string input types
        with self.assertRaises(TypeError) as cm:
            Entries.get(123)
        self.assertEqual(str(cm.exception), "Entry name must be a string, got int")

        with self.assertRaises(TypeError) as cm:
            Entries.get(None)
        self.assertEqual(str(cm.exception), "Entry name must be a string, got NoneType")

        with self.assertRaises(TypeError) as cm:
            Entries.get([])
        self.assertEqual(str(cm.exception), "Entry name must be a string, got list")

        with self.assertRaises(TypeError) as cm:
            Entries.get({})
        self.assertEqual(str(cm.exception), "Entry name must be a string, got dict")

    def test_entry_get_empty_or_whitespace_names(self):
        # Test with empty string
        with self.assertRaises(ValueError) as cm:
            Entries.get("")
        self.assertEqual(str(cm.exception), "Entry name is required and cannot be empty or whitespace-only")

        # Test with whitespace-only strings
        with self.assertRaises(ValueError) as cm:
            Entries.get("   ")
        self.assertEqual(str(cm.exception), "Entry name is required and cannot be empty or whitespace-only")

        with self.assertRaises(ValueError) as cm:
            Entries.get("\t\n  ")
        self.assertEqual(str(cm.exception), "Entry name is required and cannot be empty or whitespace-only")

    def test_entry_list_basic(self):
        # Create multiple entries for the transcript
        DB["entries"]["entry1"] = {
            "id": "entry1",
            "parent": "trans1",
            "start_time": "10:15",
            "text": "First entry",
        }
        DB["entries"]["entry2"] = {
            "id": "entry2",
            "parent": "trans1",
            "start_time": "10:20",
            "text": "Second entry",
        }
        DB["entries"]["entry3"] = {
            "id": "entry3",
            "parent": "trans1",
            "start_time": "10:25",
            "text": "Third entry",
        }

        # List all entries for the transcript
        result = Entries.list("trans1")
        self.assertEqual(len(result["entries"]), 3)

        # Check entries are sorted by start_time
        self.assertEqual(result["entries"][0]["id"], "entry1")
        self.assertEqual(result["entries"][1]["id"], "entry2")
        self.assertEqual(result["entries"][2]["id"], "entry3")

    def test_entry_list_pagination(self):
        # Create several entries
        for i in range(1, 6):
            DB["entries"][f"entry{i}"] = {
                "id": f"entry{i}",
                "parent": "trans1",
                "start_time": f"10:{15+i}",
                "text": f"Entry {i}",
            }

        # Test pageSize parameter
        result = Entries.list("trans1", pageSize=2)
        self.assertEqual(len(result["entries"]), 2)
        self.assertIn("nextPageToken", result)
        self.assertEqual(result["entries"][0]["id"], "entry1")
        self.assertEqual(result["entries"][1]["id"], "entry2")

        # Test pageToken parameter
        result = Entries.list("trans1", pageSize=2, pageToken=result["nextPageToken"])
        self.assertEqual(len(result["entries"]), 2)
        self.assertIn("nextPageToken", result)
        self.assertEqual(result["entries"][0]["id"], "entry3")
        self.assertEqual(result["entries"][1]["id"], "entry4")

        # Test reaching the end of pagination
        result = Entries.list("trans1", pageSize=2, pageToken=result["nextPageToken"])
        self.assertEqual(len(result["entries"]), 1)
        self.assertNotIn("nextPageToken", result)
        self.assertEqual(result["entries"][0]["id"], "entry5")

    def test_entry_list_with_different_parents(self):
        # Create entries for different transcripts
        DB["entries"]["entry1"] = {
            "id": "entry1",
            "parent": "trans1",
            "start_time": "10:15",
            "text": "Entry for trans1",
        }
        DB["entries"]["entry2"] = {
            "id": "entry2",
            "parent": "trans1",
            "start_time": "10:20",
            "text": "Another entry for trans1",
        }
        DB["entries"]["entry3"] = {
            "id": "entry3",
            "parent": "trans2",
            "start_time": "11:15",
            "text": "Entry for trans2",
        }

        # List entries for trans1
        result = Entries.list("trans1")
        self.assertEqual(len(result["entries"]), 2)
        self.assertEqual(result["entries"][0]["id"], "entry1")
        self.assertEqual(result["entries"][1]["id"], "entry2")

        # List entries for trans2
        result = Entries.list("trans2")
        self.assertEqual(len(result["entries"]), 1)
        self.assertEqual(result["entries"][0]["id"], "entry3")

        # List entries for non-existent transcript
        result = Entries.list("nonexistent_transcript")
        self.assertEqual(len(result["entries"]), 0)

    def test_entry_list_with_complex_content(self):
        # Create entries with more complex data
        DB["entries"]["entry1"] = {
            "id": "entry1",
            "parent": "trans1",
            "start_time": "10:15",
            "text": "Hello, how are you?",
            "speaker": "User 1",
            "confidence": 0.95,
            "duration": "PT5S",  # 5 seconds
        }
        DB["entries"]["entry2"] = {
            "id": "entry2",
            "parent": "trans1",
            "start_time": "10:20",
            "text": "I'm doing well, thank you!",
            "speaker": "User 2",
            "confidence": 0.87,
            "duration": "PT3S",  # 3 seconds
        }

        # List entries
        result = Entries.list("trans1")
        self.assertEqual(len(result["entries"]), 2)

        # Check detailed properties are preserved
        self.assertEqual(result["entries"][0]["text"], "Hello, how are you?")
        self.assertEqual(result["entries"][0]["speaker"], "User 1")
        self.assertEqual(result["entries"][0]["confidence"], 0.95)
        self.assertEqual(result["entries"][0]["duration"], "PT5S")

        self.assertEqual(result["entries"][1]["text"], "I'm doing well, thank you!")
        self.assertEqual(result["entries"][1]["speaker"], "User 2")
        self.assertEqual(result["entries"][1]["confidence"], 0.87)
        self.assertEqual(result["entries"][1]["duration"], "PT3S")

    def test_entry_list_parameter_validation(self):
        """Test parameter validation for the list function."""

        # Test with empty parent string - validation fails, causes TypeError on re-raise
        with self.assertRaises(TypeError):
            Entries.list("", pageSize=100)
        
        # Test with invalid pageSize (less than 1) - validation fails, causes TypeError on re-raise
        with self.assertRaises(TypeError):
            Entries.list("trans1", pageSize=0)
        
        # Test with negative pageSize - validation fails, causes TypeError on re-raise
        with self.assertRaises(TypeError):
            Entries.list("trans1", pageSize=-1)


if __name__ == "__main__":
    unittest.main()
