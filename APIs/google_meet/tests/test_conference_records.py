import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler

from google_meet.tests.common import reset_db
from google_meet import ConferenceRecords
from google_meet import DB


class TestConferenceRecords(BaseTestCaseWithErrorHandler):

    def setUp(self):
        reset_db()

    def test_conference_records_get(self):
        # Test successful case
        DB["conferenceRecords"]["conf1"] = {"field": "value"}
        result = ConferenceRecords.get("conf1")
        self.assertEqual(result, {"field": "value"})

        # Test not found case
        with self.assertRaises(KeyError) as context:
            ConferenceRecords.get("nonexistent_conf")
        self.assertEqual(context.exception.args[0], "Conference record not found: nonexistent_conf")

        # Test empty name case
        with self.assertRaises(ValueError) as context:
            ConferenceRecords.get("")
        self.assertEqual(context.exception.args[0], "Conference record name is required and cannot be empty or whitespace-only")

        # Test whitespace-only name case
        with self.assertRaises(ValueError) as context:
            ConferenceRecords.get("   ")
        self.assertEqual(context.exception.args[0], "Conference record name is required and cannot be empty or whitespace-only")

        # Test invalid type cases
        with self.assertRaises(TypeError) as context:
            ConferenceRecords.get(123)
        self.assertEqual(context.exception.args[0], "Conference record name must be a string, got int")

        with self.assertRaises(TypeError) as context:
            ConferenceRecords.get(None)
        self.assertEqual(context.exception.args[0], "Conference record name must be a string, got NoneType")

        with self.assertRaises(TypeError) as context:
            ConferenceRecords.get(["invalid", "list"])
        self.assertEqual(context.exception.args[0], "Conference record name must be a string, got list")

    def test_conference_records_list(self):
        # Test successful case
        DB["conferenceRecords"]["conf1"] = {"name": "conf1"}
        DB["conferenceRecords"]["conf2"] = {"name": "conf2"}
        result = ConferenceRecords.list()
        self.assertEqual(len(result["conferenceRecords"]), 2)

        # Test with filter
        result = ConferenceRecords.list(filter="conf1")
        self.assertEqual(len(result["conferenceRecords"]), 1)
        self.assertEqual(result["conferenceRecords"][0]["name"], "conf1")

        # Test with pageSize
        result = ConferenceRecords.list(pageSize=1)
        self.assertEqual(len(result["conferenceRecords"]), 1)
        self.assertIn("nextPageToken", result)

        # Test with pageToken
        DB["conferenceRecords"]["conf3"] = {"name": "conf3"}
        result = ConferenceRecords.list(pageSize=1, pageToken="1")
        self.assertEqual(len(result["conferenceRecords"]), 1)
        self.assertIn("nextPageToken", result)

    def test_conference_records_list_validation(self):
        # Test TypeError for invalid pageSize type
        with self.assertRaises(TypeError) as context:
            ConferenceRecords.list(pageSize="invalid")
        self.assertEqual(str(context.exception), "pageSize must be an integer")

        # Test ValueError for invalid pageSize (zero)
        with self.assertRaises(ValueError) as context:
            ConferenceRecords.list(pageSize=0)
        self.assertEqual(str(context.exception), "pageSize must be positive")

        # Test ValueError for invalid pageSize (negative)
        with self.assertRaises(ValueError) as context:
            ConferenceRecords.list(pageSize=-1)
        self.assertEqual(str(context.exception), "pageSize must be positive")

        # Test TypeError for invalid pageToken type
        with self.assertRaises(TypeError) as context:
            ConferenceRecords.list(pageToken=123)
        self.assertEqual(str(context.exception), "pageToken must be a string")

        # Test ValueError for empty pageToken (after stripping)
        with self.assertRaises(ValueError) as context:
            ConferenceRecords.list(pageToken="   ")
        self.assertEqual(str(context.exception), "pageToken cannot be empty")

        # Test TypeError for invalid filter type
        with self.assertRaises(TypeError) as context:
            ConferenceRecords.list(filter=123)
        self.assertEqual(str(context.exception), "filter must be a string")

        # Test ValueError for empty filter (after stripping)
        with self.assertRaises(ValueError) as context:
            ConferenceRecords.list(filter="   ")
        self.assertEqual(str(context.exception), "Filter cannot be empty")

    def test_conference_records_list_empty_result(self):
        # Test empty result
        result = ConferenceRecords.list()
        self.assertEqual(result["conferenceRecords"], [])
        self.assertNotIn("nextPageToken", result)

    def test_conference_records_list_sorting(self):
        # Test that records are sorted by start_time in descending order
        DB["conferenceRecords"]["conf1"] = {
            "id": "conf1",
            "start_time": "2023-01-01T10:00:00Z",
        }
        DB["conferenceRecords"]["conf2"] = {
            "id": "conf2", 
            "start_time": "2023-01-01T12:00:00Z",
        }
        DB["conferenceRecords"]["conf3"] = {
            "id": "conf3",
            "start_time": "2023-01-01T11:00:00Z",
        }

        result = ConferenceRecords.list()
        records = result["conferenceRecords"]
        
        # Should be sorted by start_time in descending order (most recent first)
        self.assertEqual(records[0]["id"], "conf2")  # 12:00 (most recent)
        self.assertEqual(records[1]["id"], "conf3")  # 11:00
        self.assertEqual(records[2]["id"], "conf1")  # 10:00 (oldest)

    def test_conference_records_list_filter_edge_cases(self):
        # Test filter with whitespace handling
        DB["conferenceRecords"]["conf1"] = {"name": "test conference"}
        DB["conferenceRecords"]["conf2"] = {"name": "another meeting"}
        
        # Test filter that finds a match
        result = ConferenceRecords.list(filter="test")
        self.assertEqual(len(result["conferenceRecords"]), 1)
        self.assertEqual(result["conferenceRecords"][0]["name"], "test conference")
        
        # Test filter that finds no matches
        result = ConferenceRecords.list(filter="nonexistent")
        self.assertEqual(len(result["conferenceRecords"]), 0)
        
        # Test case sensitivity
        result = ConferenceRecords.list(filter="TEST")
        self.assertEqual(len(result["conferenceRecords"]), 0)  # Should be case-sensitive

    def test_conference_records_list_pagination_edge_cases(self):
        # Setup test data
        for i in range(5):
            DB["conferenceRecords"][f"conf{i}"] = {
                "id": f"conf{i}",
                "start_time": f"2023-01-0{i+1}T10:00:00Z"
            }
        
        # Test pageSize larger than total records
        result = ConferenceRecords.list(pageSize=10)
        self.assertEqual(len(result["conferenceRecords"]), 5)
        self.assertNotIn("nextPageToken", result)
        
        # Test valid pageToken
        result = ConferenceRecords.list(pageSize=2, pageToken="2")
        self.assertEqual(len(result["conferenceRecords"]), 2)
        
        # Test pageToken at end of results
        result = ConferenceRecords.list(pageSize=3, pageToken="4")
        self.assertEqual(len(result["conferenceRecords"]), 1)

    def test_conference_records_list_missing_start_time(self):
        # Test records without start_time field
        DB["conferenceRecords"]["conf1"] = {
            "id": "conf1",
            "start_time": "2023-01-01T10:00:00Z",
        }
        DB["conferenceRecords"]["conf2"] = {
            "id": "conf2",
            # No start_time field
        }
        DB["conferenceRecords"]["conf3"] = {
            "id": "conf3",
            "start_time": "2023-01-01T12:00:00Z",
        }

        result = ConferenceRecords.list()
        records = result["conferenceRecords"]
        
        # Records without start_time should be sorted with empty string (appear last)
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["id"], "conf3")  # Latest time
        self.assertEqual(records[1]["id"], "conf1")  # Earlier time
        self.assertEqual(records[2]["id"], "conf2")  # No start_time (empty string)

    def test_conference_records_list_valid_string_inputs(self):
        # Test that valid string inputs with whitespace are handled correctly
        DB["conferenceRecords"]["conf1"] = {"name": "test conference"}
        
        # Test filter with leading/trailing whitespace (should be stripped)
        result = ConferenceRecords.list(filter="  test  ")
        self.assertEqual(len(result["conferenceRecords"]), 1)
        
        # Test pageToken with leading/trailing whitespace (should be stripped)
        result = ConferenceRecords.list(pageToken="  0  ")
        # Should not raise an error and should work correctly


if __name__ == "__main__":
    unittest.main()
