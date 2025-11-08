import unittest
import os
from datetime import datetime


from google_meet.tests.common import reset_db
from google_meet import DB
from google_meet import utils
from google_meet.SimulationEngine.db import save_state, load_state
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestSimulationEngineUtils(BaseTestCaseWithErrorHandler):

    def setUp(self):
        reset_db()

    def test_save_and_load_state(self):
        # Add test data
        DB["spaces"]["test_space"] = {"id": "test_space", "name": "Test Space"}
        DB["conferenceRecords"]["conf1"] = {"id": "conf1", "start_time": "2023-01-01T10:00:00Z"}

        # Save the state
        save_state("test_save_load.json")

        # Clear the DB
        DB.clear()
        self.assertEqual(len(DB), 0)

        # Load the state
        load_state("test_save_load.json")

        # Verify data was restored
        self.assertIn("spaces", DB)
        self.assertIn("test_space", DB["spaces"])
        self.assertEqual(DB["spaces"]["test_space"]["name"], "Test Space")

        self.assertIn("conferenceRecords", DB)
        self.assertIn("conf1", DB["conferenceRecords"])
        self.assertEqual(DB["conferenceRecords"]["conf1"]["start_time"], "2023-01-01T10:00:00Z")

        # Clean up
        os.remove("test_save_load.json")

    def test_load_state_file_not_found(self):
        """Test loading state from a non-existent file."""
        with self.assertRaises(FileNotFoundError) as context:
            load_state("nonexistent_file.json")
        self.assertEqual(
            str(context.exception),
            "State file nonexistent_file.json not found. Starting with default state.",
        )

    def test_ensure_exists(self):
        # Setup test data
        DB["test_collection"] = {"item1": {"id": "item1"}}

        # Test existing item
        result = utils.ensure_exists("test_collection", "item1")
        self.assertTrue(result)

        # Test non-existent item
        with self.assertRaises(ValueError):
            utils.ensure_exists("test_collection", "nonexistent_item")

        # Test non-existent collection
        with self.assertRaises(ValueError):
            utils.ensure_exists("nonexistent_collection", "item1")

    def test_paginate_results_basic(self):
        # Create test items
        items = [{"id": f"item{i}"} for i in range(1, 6)]

        # Test with no pagination parameters
        result = utils.paginate_results(items, "test_items")
        self.assertEqual(len(result["test_items"]), 5)
        self.assertNotIn("nextPageToken", result)

        # Test with pageSize parameter
        result = utils.paginate_results(items, "test_items", page_size=2)
        self.assertEqual(len(result["test_items"]), 2)
        self.assertEqual(result["test_items"][0]["id"], "item1")
        self.assertEqual(result["test_items"][1]["id"], "item2")
        self.assertIn("nextPageToken", result)
        self.assertEqual(result["nextPageToken"], "2")

    def test_paginate_results_with_token(self):
        # Create test items
        items = [{"id": f"item{i}"} for i in range(1, 6)]

        # Test with pageToken parameter
        result = utils.paginate_results(
            items, "test_items", page_size=2, page_token="2"
        )
        self.assertEqual(len(result["test_items"]), 2)
        self.assertEqual(result["test_items"][0]["id"], "item3")
        self.assertEqual(result["test_items"][1]["id"], "item4")
        self.assertIn("nextPageToken", result)
        self.assertEqual(result["nextPageToken"], "4")

        # Test with last page
        result = utils.paginate_results(
            items, "test_items", page_size=2, page_token="4"
        )
        self.assertEqual(len(result["test_items"]), 1)
        self.assertEqual(result["test_items"][0]["id"], "item5")
        self.assertNotIn("nextPageToken", result)

    def test_paginate_results_edge_cases(self):
        # Test with empty items list
        result = utils.paginate_results([], "test_items")
        self.assertEqual(len(result["test_items"]), 0)
        self.assertNotIn("nextPageToken", result)

        # Test with invalid pageToken (non-numeric)
        items = [{"id": f"item{i}"} for i in range(1, 4)]
        result = utils.paginate_results(items, "test_items", page_size=2, page_token="invalid")
        self.assertEqual(len(result["test_items"]), 2)
        self.assertEqual(result["test_items"][0]["id"], "item1")
        self.assertEqual(result["test_items"][1]["id"], "item2")

        # Test with pageSize larger than items
        result = utils.paginate_results(items, "test_items", page_size=10)
        self.assertEqual(len(result["test_items"]), 3)
        self.assertNotIn("nextPageToken", result)

    def test_paginate_results_page_size_default(self):
        # Test that default page size is 100
        items = [{"id": f"item{i}"} for i in range(1, 150)]
        result = utils.paginate_results(items, "test_items")
        self.assertEqual(len(result["test_items"]), 100)
        self.assertIn("nextPageToken", result)
        self.assertEqual(result["nextPageToken"], "100")


class TestDatetimeValidationUtils(BaseTestCaseWithErrorHandler):
    """Test the datetime validation utility functions."""

    def test_validate_datetime_string_valid_iso8601_utc(self):
        """Test validation of valid ISO 8601 datetime strings with UTC timezone."""
        valid_datetimes = [
            "2023-01-01T10:00:00Z",
            "2023-12-31T23:59:59Z",
            "2024-02-29T12:30:45Z",  # Leap year
            "2023-06-15T00:00:00Z",
        ]
        
        for dt_str in valid_datetimes:
            with self.subTest(datetime_string=dt_str):
                result = utils.validate_datetime_string(dt_str, "test_field")
                self.assertIsInstance(result, datetime)
                self.assertEqual(result.isoformat() + "Z", dt_str)

    def test_validate_datetime_string_valid_iso8601_local(self):
        """Test validation of valid ISO 8601 datetime strings without timezone."""
        valid_datetimes = [
            "2023-01-01T10:00:00",
            "2023-12-31T23:59:59",
            "2024-02-29T12:30:45",
            "2023-06-15T00:00:00",
        ]
        
        for dt_str in valid_datetimes:
            with self.subTest(datetime_string=dt_str):
                result = utils.validate_datetime_string(dt_str, "test_field")
                self.assertIsInstance(result, datetime)
                self.assertEqual(result.isoformat(), dt_str)

    def test_validate_datetime_string_valid_date_only(self):
        """Test validation accepts valid date-only formats."""
        valid_dates = [
            "2023-01-01",
            "2023-12-31",
            "2024-02-29",  # Leap year
            "2023-06-15",
        ]
        
        for date_str in valid_dates:
            with self.subTest(date_string=date_str):
                result = utils.validate_datetime_string(date_str, "test_field")
                self.assertIsInstance(result, datetime)
                # Verify the date components are correct
                year, month, day = map(int, date_str.split('-'))
                self.assertEqual(result.year, year)
                self.assertEqual(result.month, month)
                self.assertEqual(result.day, day)
                # Time should default to midnight
                self.assertEqual(result.hour, 0)
                self.assertEqual(result.minute, 0)
                self.assertEqual(result.second, 0)

    def test_validate_datetime_string_valid_simple_time(self):
        """Test validation accepts valid simple time formats."""
        valid_simple_times = [
            "10:00",
            "10:05",
            "23:59",
            "00:00",
            "12:30",
            "10:00:00",
            "10:05:30",
            "23:59:59",
            "00:00:00",
        ]
        
        for time_str in valid_simple_times:
            with self.subTest(time_string=time_str):
                result = utils.validate_datetime_string(time_str, "test_field")
                self.assertIsInstance(result, datetime)
                # Verify the time components are correct
                if len(time_str.split(':')) == 2:  # HH:MM
                    hour, minute = map(int, time_str.split(':'))
                    self.assertEqual(result.hour, hour)
                    self.assertEqual(result.minute, minute)
                elif len(time_str.split(':')) == 3:  # HH:MM:SS
                    hour, minute, second = map(int, time_str.split(':'))
                    self.assertEqual(result.hour, hour)
                    self.assertEqual(result.minute, minute)
                    self.assertEqual(result.second, second)

    def test_validate_datetime_string_edge_cases(self):
        """Test validation handles edge cases and malformed strings correctly."""
        edge_cases = [
            ("", "cannot be empty or whitespace only"),  # Empty string
            ("   ", "cannot be empty or whitespace only"),  # Whitespace only
            (None, "must be a string"),  # None value
            (123, "must be a string"),  # Integer
            (123.45, "must be a string"),  # Float
            (True, "must be a string"),  # Boolean
            (False, "must be a string"),  # Boolean
            ([], "must be a string"),  # List
            ({}, "must be a string"),  # Dict
        ]
        
        for edge_case, expected_error in edge_cases:
            with self.subTest(edge_case=repr(edge_case)):
                with self.assertRaises(ValueError) as context:
                    utils.validate_datetime_string(edge_case, "test_field")
                # Should fail with appropriate error message
                self.assertIn(expected_error, str(context.exception))

    def test_validate_datetime_string_invalid_formats(self):
        """Test validation rejects invalid datetime formats."""
        invalid_datetimes = [
            "invalid_string",
            "abc:def",  # Invalid time format
            "12:34:56:78",  # Too many time components
            "25:00",  # Invalid hour in simple time format
            "10:60",  # Invalid minute in simple time format
            "10:00:60",  # Invalid second in simple time format
            "not_a_datetime_at_all",
            "hello world",
        ]
        
        for dt_str in invalid_datetimes:
            with self.subTest(datetime_string=dt_str):
                with self.assertRaises(ValueError) as context:
                    utils.validate_datetime_string(dt_str, "test_field")
                self.assertIn("Invalid test_field format", str(context.exception))

    def test_validate_datetime_string_empty_or_whitespace(self):
        """Test validation rejects empty or whitespace-only strings."""
        invalid_inputs = ["", "   ", "\t", "\n"]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input_value=repr(invalid_input)):
                with self.assertRaises(ValueError) as context:
                    utils.validate_datetime_string(invalid_input, "test_field")
                self.assertIn("cannot be empty or whitespace only", str(context.exception))

    def test_validate_datetime_string_wrong_type(self):
        """Test validation rejects non-string inputs."""
        invalid_inputs = [None, 123, 123.45, True, False, [], {}, datetime.now()]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input_type=type(invalid_input).__name__):
                with self.assertRaises(ValueError) as context:
                    utils.validate_datetime_string(invalid_input, "test_field")
                self.assertIn("must be a string", str(context.exception))


    def test_datetime_validation_error_messages(self):
        """Test that error messages are descriptive and helpful."""
        with self.assertRaises(ValueError) as context:
            utils.validate_datetime_string("invalid", "start_time")
        
        error_msg = str(context.exception)
        self.assertIn("Invalid start_time format", error_msg)
        self.assertIn("ISO 8601 format", error_msg)
        self.assertIn("2023-01-01T10:00:00Z", error_msg)

    def test_datetime_validation_field_name_context(self):
        """Test that error messages include the correct field name."""
        with self.assertRaises(ValueError) as context:
            utils.validate_datetime_string("invalid", "join_time")
        
        error_msg = str(context.exception)
        self.assertIn("Invalid join_time format", error_msg)

    def test_datetime_validation_type_error_context(self):
        """Test that type error messages include the actual type received."""
        with self.assertRaises(ValueError) as context:
            utils.validate_datetime_string(123, "start_time")
        
        error_msg = str(context.exception)
        self.assertIn("start_time must be a string, got int", error_msg)

    def test_datetime_validation_empty_string_context(self):
        """Test that empty string error messages are clear."""
        with self.assertRaises(ValueError) as context:
            utils.validate_datetime_string("   ", "end_time")
        
        error_msg = str(context.exception)
        self.assertIn("end_time cannot be empty or whitespace only", error_msg)


if __name__ == "__main__":
    unittest.main()
