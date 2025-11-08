"""
Test file for recurrence functionality in Google Calendar Events API.
This file demonstrates various recurrence patterns and validates the implementation.
"""

import pytest
from ..SimulationEngine.custom_errors import InvalidInputError
from pydantic import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.recurrence_validator import RecurrenceValidator
from .. import (create_event, update_event)

class TestRecurrenceValidation(BaseTestCaseWithErrorHandler):
    """Test cases for recurrence rule validation."""
    
    def test_valid_daily_recurrence(self):
        """Test creating an event with valid daily recurrence."""
        event = create_event("primary", {
            "summary": "Daily Standup",
            "start": {"dateTime": "2024-01-15T09:00:00Z"},
            "end": {"dateTime": "2024-01-15T09:30:00Z"},
            "recurrence": ["RRULE:FREQ=DAILY;COUNT=5"]
        })
        
        self.assertEqual(event["summary"], "Daily Standup")
        self.assertEqual(event["recurrence"], ["RRULE:FREQ=DAILY;COUNT=5"])
        self.assertIn("id", event)
    
    def test_valid_weekly_recurrence(self):
        """Test creating an event with valid weekly recurrence."""
        event = create_event("primary", {
            "summary": "Weekly Meeting",
            "start": {"dateTime": "2024-01-15T14:00:00Z"},
            "end": {"dateTime": "2024-01-15T15:00:00Z"},
            "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"]
        })
        
        self.assertEqual(event["summary"], "Weekly Meeting")
        self.assertEqual(event["recurrence"], ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR"])
    
    def test_valid_monthly_recurrence(self):
        """Test creating an event with valid monthly recurrence."""
        event = create_event("primary", {
            "summary": "Monthly Review",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "recurrence": ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"]
        })
        
        self.assertEqual(event["summary"], "Monthly Review")
        self.assertEqual(event["recurrence"], ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"])
    
    def test_valid_yearly_recurrence(self):
        """Test creating an event with valid yearly recurrence."""
        event = create_event("primary", {
            "summary": "Annual Review",
            "start": {"dateTime": "2024-01-15T09:00:00Z"},
            "end": {"dateTime": "2024-01-15T10:00:00Z"},
            "recurrence": ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=15"]
        })
        
        self.assertEqual(event["summary"], "Annual Review")
        self.assertEqual(event["recurrence"], ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=15"])
    
    def test_valid_interval_recurrence(self):
        """Test creating an event with interval recurrence."""
        event = create_event("primary", {
            "summary": "Bi-weekly Meeting",
            "start": {"dateTime": "2024-01-15T14:00:00Z"},
            "end": {"dateTime": "2024-01-15T15:00:00Z"},
            "recurrence": ["RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=FR"]
        })
        
        self.assertEqual(event["summary"], "Bi-weekly Meeting")
        self.assertEqual(event["recurrence"], ["RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=FR"])
    
    def test_valid_until_recurrence(self):
        """Test creating an event with until date recurrence."""
        event = create_event("primary", {
            "summary": "Temporary Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "recurrence": ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"]
        })
        
        self.assertEqual(event["summary"], "Temporary Meeting")
        self.assertEqual(event["recurrence"], ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"])
    
    def test_valid_ordinal_byday(self):
        """Test creating an event with ordinal BYDAY values."""
        event = create_event("primary", {
            "summary": "Monthly Board Meeting",
            "start": {"dateTime": "2024-01-15T14:00:00Z"},
            "end": {"dateTime": "2024-01-15T15:00:00Z"},
            "recurrence": ["RRULE:FREQ=MONTHLY;BYDAY=1MO"]
        })
        
        self.assertEqual(event["summary"], "Monthly Board Meeting")
        self.assertEqual(event["recurrence"], ["RRULE:FREQ=MONTHLY;BYDAY=1MO"])
    
    def test_valid_negative_ordinal_byday(self):
        """Test creating an event with negative ordinal BYDAY values."""
        event = create_event("primary", {
            "summary": "Last Friday Meeting",
            "start": {"dateTime": "2024-01-15T14:00:00Z"},
            "end": {"dateTime": "2024-01-15T15:00:00Z"},
            "recurrence": ["RRULE:FREQ=MONTHLY;BYDAY=-1FR"]
        })
        
        self.assertEqual(event["summary"], "Last Friday Meeting")
        self.assertEqual(event["recurrence"], ["RRULE:FREQ=MONTHLY;BYDAY=-1FR"])
    
    def test_multiple_recurrence_rules(self):
        """Test creating an event with multiple recurrence rules."""
        event = create_event("primary", {
            "summary": "Complex Recurring Event",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "recurrence": [
                "RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR",
                "EXDATE:20240115T100000Z"
            ]
        })
        
        self.assertEqual(event["summary"], "Complex Recurring Event")
        self.assertEqual(len(event["recurrence"]), 2)
        self.assertIn("RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR", event["recurrence"])
        self.assertIn("EXDATE:20240115T100000Z", event["recurrence"])

    def test_empty_list_is_valid(self):
        """Test that RecurrenceValidator accepts an empty list."""
        try:
            RecurrenceValidator.validate_recurrence_rules([])
        except InvalidInputError:
            self.fail("validate_recurrence_rules should not raise an error for an empty list.")


class TestRecurrenceValidationErrors(BaseTestCaseWithErrorHandler):
    """Test cases for recurrence validation errors."""
    
    def test_missing_freq(self):
        """Test that missing FREQ parameter raises error."""
        self.assert_error_behavior(
            create_event,
            ValidationError,
            "1 validation error for EventResourceInputModel",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": ["RRULE:COUNT=5"]
            }
        )
    
    def test_invalid_freq(self):
        """Test that invalid FREQ parameter raises error."""
        self.assert_error_behavior(
            create_event,
            ValidationError,
            "Recurrence rule 0 has invalid FREQ 'INVALID'",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": ["RRULE:FREQ=INVALID"]
            }
        )
    
    def test_invalid_interval(self):
        """Test that invalid INTERVAL parameter raises error."""
        self.assert_error_behavior(
            create_event,
            ValidationError,
            "Recurrence rule 0 INTERVAL must be a positive integer",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": ["RRULE:FREQ=DAILY;INTERVAL=0"]
            }
        )
    
    def test_invalid_count(self):
        """Test that invalid COUNT parameter raises error."""
        self.assert_error_behavior(
            create_event,
            ValidationError,
            "Recurrence rule 0 COUNT must be a positive integer",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": ["RRULE:FREQ=DAILY;COUNT=0"]
            }
        )
    
    def test_invalid_until_format(self):
        """Test that invalid UNTIL format raises error."""
        self.assert_error_behavior(
            create_event,
            ValidationError,
            "Recurrence rule 0 UNTIL must be in format YYYYMMDDTHHMMSSZ or YYYYMMDDTHHMMSS",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": ["RRULE:FREQ=DAILY;UNTIL=INVALID"]
            }
        )
    
    def test_invalid_byday(self):
        """Test that invalid BYDAY parameter raises error."""
        self.assert_error_behavior(
            create_event,
            ValidationError,
            "Recurrence rule 0 BYDAY 'INVALID' has invalid day 'INVALID'",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=INVALID"]
            }
        )
    
    def test_invalid_bymonth(self):
        """Test that invalid BYMONTH parameter raises error."""
        self.assert_error_behavior(
            create_event,
            ValidationError,
            "Recurrence rule 0 BYMONTH must be 1-12",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": ["RRULE:FREQ=MONTHLY;BYMONTH=13"]
            }
        )
    
    def test_invalid_bymonthday(self):
        """Test that invalid BYMONTHDAY parameter raises error."""
        self.assert_error_behavior(
            create_event,
            ValidationError,
            "Recurrence rule 0 BYMONTHDAY must be 1-31",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": ["RRULE:FREQ=MONTHLY;BYMONTHDAY=32"]
            }
        )
    
    def test_invalid_recurrence_type(self):
        """Test that invalid recurrence type raises error."""
        self.assert_error_behavior(
            func_to_call=create_event,
            expected_exception_type=ValidationError,
            expected_message="recurrence\n  Input should be a valid list",
            resource={
                "summary": "Invalid Event",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": "not a list"
            }
        )

    def test_non_list_input(self):
        """Test that RecurrenceValidator raises error for non-list input."""
        with self.assertRaisesRegex(InvalidInputError, "Recurrence must be a list of strings"):
            RecurrenceValidator.validate_recurrence_rules("not a list")

    def test_list_with_non_string_element(self):
        """Test that RecurrenceValidator raises error for list with non-string element."""
        with self.assertRaisesRegex(InvalidInputError, "Recurrence rule 1 must be a string"):
            RecurrenceValidator.validate_recurrence_rules(["RRULE:FREQ=DAILY", 123])

    def test_list_with_empty_string_element(self):
        """Test that RecurrenceValidator raises error for list with empty string."""
        with self.assertRaisesRegex(InvalidInputError, "Recurrence rule 0 cannot be empty"):
            RecurrenceValidator.validate_recurrence_rules([" "])


class TestRecurrenceUpdate(BaseTestCaseWithErrorHandler):
    """Test cases for updating recurring events."""
    
    def test_update_event_with_recurrence(self):
        """Test updating an event to add recurrence."""
        # Create a non-recurring event
        event = create_event("primary", {
            "summary": "One-time Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"}
        })
        
        # Update to make it recurring
        updated_event = update_event(event["id"], "primary", {
            "summary": "Weekly Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "recurrence": ["RRULE:FREQ=WEEKLY;COUNT=10"]
        })
        
        self.assertEqual(updated_event["summary"], "Weekly Meeting")
        self.assertEqual(updated_event["recurrence"], ["RRULE:FREQ=WEEKLY;COUNT=10"])
    
    def test_update_recurrence_pattern(self):
        """Test updating the recurrence pattern of an existing recurring event."""
        # Create a recurring event
        event = create_event("primary", {
            "summary": "Daily Meeting",
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "recurrence": ["RRULE:FREQ=DAILY;COUNT=5"]
        })
        
        # Update the recurrence pattern
        updated_event = update_event(event["id"], "primary", {
            "summary": event["summary"],
            "start": {"dateTime": "2024-01-15T10:00:00Z"},
            "end": {"dateTime": "2024-01-15T11:00:00Z"},
            "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=20"]
        })
        
        self.assertEqual(updated_event["recurrence"], ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;COUNT=20"])
        self.assertEqual(updated_event["summary"], "Daily Meeting")  # Should remain unchanged


if __name__ == "__main__":
    # Run some basic tests
    print("Testing recurrence functionality...")
    
    # Test valid recurrence patterns
    test_cases = [
        {
            "name": "Daily for 5 occurrences",
            "recurrence": ["RRULE:FREQ=DAILY;COUNT=5"]
        },
        {
            "name": "Weekly on Monday and Wednesday",
            "recurrence": ["RRULE:FREQ=WEEKLY;BYDAY=MO,WE"]
        },
        {
            "name": "Monthly on the 15th",
            "recurrence": ["RRULE:FREQ=MONTHLY;BYMONTHDAY=15"]
        },
        {
            "name": "Yearly on January 1st",
            "recurrence": ["RRULE:FREQ=YEARLY;BYMONTH=1;BYMONTHDAY=1"]
        },
        {
            "name": "Every 2 weeks",
            "recurrence": ["RRULE:FREQ=WEEKLY;INTERVAL=2"]
        },
        {
            "name": "Until a specific date",
            "recurrence": ["RRULE:FREQ=DAILY;UNTIL=20241231T235959Z"]
        }
    ]
    
    for test_case in test_cases:
        try:
            event = create_event("primary", {
                "summary": test_case["name"],
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "recurrence": test_case["recurrence"]
            })
            print(f"✓ {test_case['name']}: SUCCESS")
        except Exception as e:
            print(f"✗ {test_case['name']}: FAILED - {e}")
