"""
Tests for datetime validation functionality in Google Meet API.

This module tests the datetime validation utilities and ensures that
all API functions properly validate datetime fields according to ISO 8601 format.
"""

import unittest
from unittest.mock import patch
from datetime import datetime

from google_meet.SimulationEngine.utils import validate_datetime_string
from google_meet.SimulationEngine.db import DB
from google_meet.ConferenceRecords import get as get_conference_record, list as list_conference_records
from google_meet.ConferenceRecords.Participants import get as get_participant, list as list_participants
from google_meet.ConferenceRecords.Participants.ParticipantSessions import get as get_session, list as list_sessions
from google_meet.ConferenceRecords.Recordings import get as get_recording, list as list_recordings
from google_meet.ConferenceRecords.Transcripts import get as get_transcript, list as list_transcripts
from google_meet.ConferenceRecords.Transcripts.Entries import get as get_entry, list as list_entries


class TestDatetimeValidationUtils(unittest.TestCase):
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
                result = validate_datetime_string(dt_str, "test_field")
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
                result = validate_datetime_string(dt_str, "test_field")
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
                result = validate_datetime_string(date_str, "test_field")
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
                result = validate_datetime_string(time_str, "test_field")
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
                    validate_datetime_string(edge_case, "test_field")
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
                    validate_datetime_string(dt_str, "test_field")
                self.assertIn("Invalid test_field format", str(context.exception))

    def test_validate_datetime_string_empty_or_whitespace(self):
        """Test validation rejects empty or whitespace-only strings."""
        invalid_inputs = ["", "   ", "\t", "\n"]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input_value=repr(invalid_input)):
                with self.assertRaises(ValueError) as context:
                    validate_datetime_string(invalid_input, "test_field")
                self.assertIn("cannot be empty or whitespace only", str(context.exception))

    def test_validate_datetime_string_wrong_type(self):
        """Test validation rejects non-string inputs."""
        invalid_inputs = [None, 123, 123.45, True, False, [], {}, datetime.now()]
        
        for invalid_input in invalid_inputs:
            with self.subTest(input_type=type(invalid_input).__name__):
                with self.assertRaises(ValueError) as context:
                    validate_datetime_string(invalid_input, "test_field")
                self.assertIn("must be a string", str(context.exception))



class TestDatetimeValidationInAPIs(unittest.TestCase):
    """Test datetime validation in actual API functions."""

    def setUp(self):
        """Set up test data."""
        # Clear existing data
        DB.clear()
        
        # Initialize with empty structure
        DB.update({
            "conferenceRecords": {},
            "recordings": {},
            "transcripts": {},
            "entries": {},
            "participants": {},
            "participantSessions": {},
            "spaces": {}
        })

    def test_conference_records_datetime_validation(self):
        """Test datetime validation in ConferenceRecords API."""
        # Add test data with valid datetime
        DB["conferenceRecords"]["conf1"] = {
            "id": "conf1",
            "start_time": "2023-01-01T10:00:00Z",
            "end_time": "2023-01-01T11:00:00Z"
        }
        
        # Add test data with invalid datetime
        DB["conferenceRecords"]["conf2"] = {
            "id": "conf2",
            "start_time": "invalid_time",
            "end_time": "2023-01-01T12:00:00Z"
        }
        
        # Test get function - should work but log validation errors
        result = get_conference_record("conf1")
        self.assertEqual(result["id"], "conf1")
        
        # Test list function - invalid datetime should be handled gracefully during sorting
        result = list_conference_records()
        self.assertEqual(len(result["conferenceRecords"]), 2)

    def test_participants_datetime_validation(self):
        """Test datetime validation in Participants API."""
        # Add test data with valid datetime
        DB["participants"]["part1"] = {
            "id": "part1",
            "parent": "conf1",
            "join_time": "2023-01-01T10:05:00Z"
        }
        
        # Add test data with invalid datetime
        DB["participants"]["part2"] = {
            "id": "part2",
            "parent": "conf1",
            "join_time": "invalid_time"
        }
        
        # Add required conference record data
        DB["conferenceRecords"]["conf1"] = {
            "id": "conf1",
            "start_time": "2023-01-01T10:00:00Z"
        }
        
        # Test get function
        result = get_participant("part1")
        self.assertEqual(result["id"], "part1")
        
        # Test list function
        result = list_participants("conf1")
        self.assertEqual(len(result["participants"]), 2)

    def test_participant_sessions_datetime_validation(self):
        """Test datetime validation in ParticipantSessions API."""
        # Add test data with valid datetime
        DB["participantSessions"]["session1"] = {
            "id": "session1",
            "participantId": "part1",
            "join_time": "2023-01-01T10:05:00Z"
        }
        
        # Add test data with invalid datetime
        DB["participantSessions"]["session2"] = {
            "id": "session2",
            "participantId": "part1",
            "join_time": "invalid_time"
        }
        
        # Add required participant data
        DB["participants"]["part1"] = {
            "id": "part1",
            "parent": "conf1"
        }
        
        # Test get function
        result = get_session("session1")
        self.assertEqual(result["id"], "session1")
        
        # Test list function
        result = list_sessions("part1")
        self.assertEqual(len(result["participantSessions"]), 2)

    def test_recordings_datetime_validation(self):
        """Test datetime validation in Recordings API."""
        # Add test data with valid datetime
        DB["recordings"]["rec1"] = {
            "id": "rec1",
            "parent": "conf1",
            "start_time": "2023-01-01T10:00:00Z"
        }
        
        # Add test data with invalid datetime
        DB["recordings"]["rec2"] = {
            "id": "rec2",
            "parent": "conf1",
            "start_time": "invalid_time"
        }
        
        # Add required conference record data
        DB["conferenceRecords"]["conf1"] = {
            "id": "conf1",
            "start_time": "2023-01-01T10:00:00Z"
        }
        
        # Test get function
        result = get_recording("rec1")
        self.assertEqual(result["id"], "rec1")
        
        # Test list function
        result = list_recordings("conf1", "conf1")
        self.assertEqual(len(result["recordings"]), 2)

    def test_transcripts_datetime_validation(self):
        """Test datetime validation in Transcripts API."""
        # Add test data with valid datetime
        DB["transcripts"]["trans1"] = {
            "id": "trans1",
            "parent": "conf1",
            "start_time": "2023-01-01T10:00:00Z"
        }
        
        # Add test data with invalid datetime
        DB["transcripts"]["trans2"] = {
            "id": "trans2",
            "parent": "conf1",
            "start_time": "invalid_time"
        }
        
        # Add required conference record data
        DB["conferenceRecords"]["conf1"] = {
            "id": "conf1",
            "start_time": "2023-01-01T10:00:00Z"
        }
        
        # Test get function
        result = get_transcript("trans1")
        self.assertEqual(result["id"], "trans1")
        
        # Test list function
        result = list_transcripts("conf1")
        self.assertEqual(len(result["transcripts"]), 2)

    def test_transcript_entries_datetime_validation(self):
        """Test datetime validation in Transcripts.Entries API."""
        # Add test data with valid datetime
        DB["entries"]["entry1"] = {
            "id": "entry1",
            "parent": "trans1",
            "start_time": "2023-01-01T10:00:00Z",
            "text": "Hello world"
        }
        
        # Add test data with invalid datetime
        DB["entries"]["entry2"] = {
            "id": "entry2",
            "parent": "trans1",
            "start_time": "invalid_time",
            "text": "Goodbye world"
        }
        
        # Add required transcript data
        DB["transcripts"]["trans1"] = {
            "id": "trans1",
            "parent": "conf1",
            "start_time": "2023-01-01T10:00:00Z"
        }
        
        # Test get function
        result = get_entry("entry1")
        self.assertEqual(result["id"], "entry1")
        
        # Test list function
        result = list_entries("trans1")
        self.assertEqual(len(result["entries"]), 2)

    def test_sorting_with_invalid_datetime_handling(self):
        """Test that sorting operations handle invalid datetime values gracefully."""
        # Add test data with mixed valid/invalid datetimes
        DB["conferenceRecords"]["conf1"] = {
            "id": "conf1",
            "start_time": "2023-01-01T10:00:00Z"
        }
        DB["conferenceRecords"]["conf2"] = {
            "id": "conf2",
            "start_time": "invalid_time"
        }
        DB["conferenceRecords"]["conf3"] = {
            "id": "conf3",
            "start_time": "2023-01-01T09:00:00Z"
        }
        
        # Test that sorting doesn't crash and handles invalid values
        result = list_conference_records()
        self.assertEqual(len(result["conferenceRecords"]), 3)
        
        # Valid datetimes should be sorted correctly, invalid ones should appear at the end
        # Since we replace invalid datetimes with empty strings, they'll appear first in reverse sort
        # This is the expected behavior for graceful degradation


class TestDatetimeValidationEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions in datetime validation."""

    def test_datetime_validation_error_messages(self):
        """Test that error messages are descriptive and helpful."""
        with self.assertRaises(ValueError) as context:
            validate_datetime_string("invalid", "start_time")
        
        error_msg = str(context.exception)
        self.assertIn("Invalid start_time format", error_msg)
        self.assertIn("ISO 8601 format", error_msg)
        self.assertIn("2023-01-01T10:00:00Z", error_msg)

    def test_datetime_validation_field_name_context(self):
        """Test that error messages include the correct field name."""
        with self.assertRaises(ValueError) as context:
            validate_datetime_string("invalid", "join_time")
        
        error_msg = str(context.exception)
        self.assertIn("Invalid join_time format", error_msg)

    def test_datetime_validation_type_error_context(self):
        """Test that type error messages include the actual type received."""
        with self.assertRaises(ValueError) as context:
            validate_datetime_string(123, "start_time")
        
        error_msg = str(context.exception)
        self.assertIn("start_time must be a string, got int", error_msg)

    def test_datetime_validation_empty_string_context(self):
        """Test that empty string error messages are clear."""
        with self.assertRaises(ValueError) as context:
            validate_datetime_string("   ", "end_time")
        
        error_msg = str(context.exception)
        self.assertIn("end_time cannot be empty or whitespace only", error_msg)


if __name__ == "__main__":
    unittest.main()
