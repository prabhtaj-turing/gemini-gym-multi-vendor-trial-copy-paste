#!/usr/bin/env python3
"""
Comprehensive test cases for the list_event_instances function in Google Calendar API.
"""

import uuid
from datetime import datetime

from common_utils.base_case import BaseTestCaseWithErrorHandler
from common_utils.datetime_utils import DateTimeValidationError
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import InvalidInputError, ResourceNotFoundError
from .. import list_event_instances, list_events

class TestListEventInstancesComprehensive(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """
        Runs before each test. Clear and reset DB to a known state.
        """
        DB.clear()
        DB.update(
            {
                "acl_rules": {},
                "calendar_list": {},
                "calendars": {},
                "channels": {},
                "colors": {"calendar": {}, "event": {}},
                "events": {},
            }
        )
        # Add default primary calendar
        DB["calendar_list"]["primary"] = {
            "id": "primary",
            "summary": "Primary Calendar",
            "description": "Default primary calendar",
            "timeZone": "UTC",
            "primary": True
        }
        
        # Create a test event for most tests
        self.test_event = {
            "id": "test-event-id",
            "summary": "Test Recurring Event",
            "description": "A test event for instance listing",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "attendees": [
                {"email": "attendee1@example.com", "displayName": "Attendee 1"},
                {"email": "attendee2@example.com", "displayName": "Attendee 2"},
                {"email": "attendee3@example.com", "displayName": "Attendee 3"},
            ]
        }
        DB["events"]["primary:test-event-id"] = self.test_event

    # ======================================================================================================================
    # Basic Functionality Tests
    # ======================================================================================================================

    def test_list_event_instances_valid_basic(self):
        """Test basic functionality with valid parameters."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertIn("nextPageToken", result)
        self.assertEqual(len(result["items"]), 1)
        self.assertIsNone(result["nextPageToken"])
        self.assertEqual(result["items"][0]["id"], "test-event-id")
        self.assertEqual(result["items"][0]["summary"], "Test Recurring Event")

    def test_list_event_instances_with_timezone(self):
        """Test functionality with timezone parameter."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            timeZone="America/New_York"
        )
        
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["timeZone"], "America/New_York")

    def test_list_event_instances_with_max_attendees(self):
        """Test functionality with maxAttendees parameter."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            maxAttendees=2
        )
        
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(len(result["items"][0]["attendees"]), 2)
        self.assertEqual(result["items"][0]["attendees"][0]["email"], "attendee1@example.com")
        self.assertEqual(result["items"][0]["attendees"][1]["email"], "attendee2@example.com")

    def test_list_event_instances_with_all_parameters(self):
        """Test functionality with all valid parameters."""
        result = list_event_instances(
            alwaysIncludeEmail=True,
            calendarId="primary",
            eventId="test-event-id",
            maxAttendees=1,
            maxResults=10,
            originalStart="2024-01-01T10:00:00Z",
            pageToken="test-token",
            showDeleted=False,
            timeMax="2024-12-31T23:59:59Z",
            timeMin="2024-01-01T00:00:00Z",
            timeZone="Europe/London"
        )
        
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["timeZone"], "Europe/London")
        self.assertEqual(len(result["items"][0]["attendees"]), 1)

    # ======================================================================================================================
    # TypeError Tests
    # ======================================================================================================================

    def test_always_include_email_invalid_type(self):
        """Test TypeError for non-boolean alwaysIncludeEmail."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "alwaysIncludeEmail must be a boolean",
            alwaysIncludeEmail="not-a-bool",
            calendarId="primary",
            eventId="test-event-id"
        )

    def test_calendar_id_invalid_type(self):
        """Test TypeError for non-string calendarId."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "calendarId must be a string",
            calendarId=123,
            eventId="test-event-id"
        )

    def test_event_id_invalid_type(self):
        """Test TypeError for non-string eventId."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "eventId must be a string",
            calendarId="primary",
            eventId=123
        )

    def test_max_attendees_invalid_type(self):
        """Test TypeError for non-integer maxAttendees."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "maxAttendees must be an integer",
            calendarId="primary",
            eventId="test-event-id",
            maxAttendees="not-an-int"
        )

    def test_max_results_invalid_type(self):
        """Test TypeError for non-integer maxResults."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "maxResults must be an integer",
            calendarId="primary",
            eventId="test-event-id",
            maxResults="not-an-int"
        )

    def test_original_start_invalid_type(self):
        """Test TypeError for non-string originalStart."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "originalStart must be a string",
            calendarId="primary",
            eventId="test-event-id",
            originalStart=123
        )

    def test_page_token_invalid_type(self):
        """Test TypeError for non-string pageToken."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "pageToken must be a string",
            calendarId="primary",
            eventId="test-event-id",
            pageToken=123
        )

    def test_show_deleted_invalid_type(self):
        """Test TypeError for non-boolean showDeleted."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "showDeleted must be a boolean",
            calendarId="primary",
            eventId="test-event-id",
            showDeleted="not-a-bool"
        )

    def test_time_max_invalid_type(self):
        """Test TypeError for non-string timeMax."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "timeMax must be a string",
            calendarId="primary",
            eventId="test-event-id",
            timeMax=123
        )

    def test_time_min_invalid_type(self):
        """Test TypeError for non-string timeMin."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "timeMin must be a string",
            calendarId="primary",
            eventId="test-event-id",
            timeMin=123
        )

    def test_time_zone_invalid_type(self):
        """Test TypeError for non-string timeZone."""
        self.assert_error_behavior(
            list_event_instances,
            TypeError,
            "timeZone must be a string",
            calendarId="primary",
            eventId="test-event-id",
            timeZone=123
        )

    # ======================================================================================================================
    # InvalidInputError Tests
    # ======================================================================================================================

    def test_calendar_id_empty_string(self):
        """Test InvalidInputError for empty calendarId."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "calendarId cannot be empty or whitespace",
            calendarId="",
            eventId="test-event-id"
        )

    def test_calendar_id_whitespace(self):
        """Test InvalidInputError for whitespace calendarId."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "calendarId cannot be empty or whitespace",
            calendarId="   ",
            eventId="test-event-id"
        )

    def test_event_id_empty_string(self):
        """Test InvalidInputError for empty eventId."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "eventId cannot be empty or whitespace",
            calendarId="primary",
            eventId=""
        )

    def test_event_id_whitespace(self):
        """Test InvalidInputError for whitespace eventId."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "eventId cannot be empty or whitespace",
            calendarId="primary",
            eventId="   "
        )

    def test_max_attendees_negative(self):
        """Test InvalidInputError for negative maxAttendees."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "maxAttendees cannot be negative",
            calendarId="primary",
            eventId="test-event-id",
            maxAttendees=-1
        )

    def test_max_results_zero(self):
        """Test InvalidInputError for zero maxResults."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "maxResults must be a positive integer",
            calendarId="primary",
            eventId="test-event-id",
            maxResults=0
        )

    def test_max_results_negative(self):
        """Test InvalidInputError for negative maxResults."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "maxResults must be a positive integer",
            calendarId="primary",
            eventId="test-event-id",
            maxResults=-5
        )

    def test_original_start_empty_string(self):
        """Test InvalidInputError for empty originalStart."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "originalStart cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            originalStart=""
        )

    def test_original_start_whitespace(self):
        """Test InvalidInputError for whitespace originalStart."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "originalStart cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            originalStart="   "
        )

    def test_original_start_invalid_format(self):
        """Test InvalidInputError for invalid originalStart format."""
        with self.assertRaises(InvalidInputError) as cm:
            list_event_instances(
                calendarId="primary",
                eventId="test-event-id",
                originalStart="invalid-date"
            )
        self.assertIn("originalStart must be a valid RFC 3339 datetime string.", str(cm.exception))

    def test_page_token_empty_string(self):
        """Test InvalidInputError for empty pageToken."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "pageToken cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            pageToken=""
        )

    def test_page_token_whitespace(self):
        """Test InvalidInputError for whitespace pageToken."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "pageToken cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            pageToken="   "
        )

    def test_time_max_empty_string(self):
        """Test InvalidInputError for empty timeMax."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeMax cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            timeMax=""
        )

    def test_time_max_whitespace(self):
        """Test InvalidInputError for whitespace timeMax."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeMax cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            timeMax="   "
        )

    def test_time_max_invalid_format(self):
        """Test InvalidInputError for invalid timeMax format."""
        with self.assertRaises(InvalidInputError) as cm:
            list_event_instances(
                calendarId="primary",
                eventId="test-event-id",
                timeMax="invalid-date"
            )
        self.assertIn("timeMax must be a valid RFC 3339 datetime string.", str(cm.exception))

    def test_time_min_empty_string(self):
        """Test InvalidInputError for empty timeMin."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeMin cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            timeMin=""
        )

    def test_time_min_whitespace(self):
        """Test InvalidInputError for whitespace timeMin."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeMin cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            timeMin="   "
        )

    def test_time_min_invalid_format(self):
        """Test InvalidInputError for invalid timeMin format."""
        with self.assertRaises(InvalidInputError) as cm:
            list_event_instances(
                calendarId="primary",
                eventId="test-event-id",
                timeMin="invalid-date"
            )
        self.assertIn("timeMin must be a valid RFC 3339 datetime string.", str(cm.exception))

    def test_time_zone_empty_string(self):
        """Test InvalidInputError for empty timeZone."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeZone cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            timeZone=""
        )

    def test_time_zone_whitespace(self):
        """Test InvalidInputError for whitespace timeZone."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeZone cannot be empty or whitespace",
            calendarId="primary",
            eventId="test-event-id",
            timeZone="   "
        )

    def test_time_zone_invalid_format(self):
        """Test InvalidInputError for invalid timeZone format."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeZone must be in format 'Continent/City' (e.g., 'America/New_York')",
            calendarId="primary",
            eventId="test-event-id",
            timeZone="InvalidTimezone"
        )

    def test_time_range_inconsistent(self):
        """Test InvalidInputError for timeMin >= timeMax."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeMin must be earlier than timeMax",
            calendarId="primary",
            eventId="test-event-id",
            timeMin="2024-12-31T23:59:59Z",
            timeMax="2024-01-01T00:00:00Z"
        )

    def test_time_range_equal(self):
        """Test InvalidInputError for timeMin == timeMax."""
        self.assert_error_behavior(
            list_event_instances,
            InvalidInputError,
            "timeMin must be earlier than timeMax",
            calendarId="primary",
            eventId="test-event-id",
            timeMin="2024-01-01T12:00:00Z",
            timeMax="2024-01-01T12:00:00Z"
        )

    # ======================================================================================================================
    # ResourceNotFoundError Tests
    # ======================================================================================================================

    def test_event_not_found(self):
        """Test ResourceNotFoundError for non-existent event."""
        self.assert_error_behavior(
            list_event_instances,
            ResourceNotFoundError,
            "Event 'nonexistent-event' not found in calendar 'primary'.",
            calendarId="primary",
            eventId="nonexistent-event"
        )

    def test_event_not_found_different_calendar(self):
        """Test ResourceNotFoundError for event in different calendar."""
        self.assert_error_behavior(
            list_event_instances,
            ResourceNotFoundError,
            "Calendar 'secondary' not found.",
            calendarId="secondary",
            eventId="test-event-id"
        )

    def test_list_events_calendar_not_found(self):
        """Test ResourceNotFoundError when calendarId does not exist."""
        self.assert_error_behavior(
            list_events,
            ResourceNotFoundError,
            "Calendar 'nonexistent_calendar' not found.",
            calendarId="nonexistent_calendar"
        )

    # ======================================================================================================================
    # Edge Cases and Special Scenarios
    # ======================================================================================================================

    def test_event_without_attendees(self):
        """Test with event that has no attendees."""
        # Create event without attendees
        event_no_attendees = {
            "id": "no-attendees-event",
            "summary": "Event without attendees",
            "start": {"dateTime": "2024-01-01T14:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "end": {"dateTime": "2024-01-01T15:00:00", "offset": "+00:00", "timeZone": "Europe/London"}
        }
        DB["events"]["primary:no-attendees-event"] = event_no_attendees
        
        result = list_event_instances(
            calendarId="primary",
            eventId="no-attendees-event",
            maxAttendees=5
        )
        
        self.assertEqual(len(result["items"]), 1)
        self.assertNotIn("attendees", result["items"][0])

    def test_event_with_non_list_attendees(self):
        """Test with event that has attendees field but not as list."""
        # Create event with non-list attendees
        event_bad_attendees = {
            "id": "bad-attendees-event",
            "summary": "Event with bad attendees",
            "start": {"dateTime": "2024-01-01T16:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "end": {"dateTime": "2024-01-01T17:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "attendees": "not-a-list"
        }
        DB["events"]["primary:bad-attendees-event"] = event_bad_attendees
        
        result = list_event_instances(
            calendarId="primary",
            eventId="bad-attendees-event",
            maxAttendees=2
        )
        
        self.assertEqual(len(result["items"]), 1)
        # Should not crash, attendees field should remain unchanged
        self.assertEqual(result["items"][0]["attendees"], "not-a-list")

    def test_max_attendees_zero(self):
        """Test maxAttendees = 0 (should return empty attendees list)."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            maxAttendees=0
        )
        
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(len(result["items"][0]["attendees"]), 0)

    def test_max_attendees_greater_than_available(self):
        """Test maxAttendees greater than available attendees."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            maxAttendees=10
        )
        
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(len(result["items"][0]["attendees"]), 3)  # Original count

    def test_valid_timezone_formats(self):
        """Test various valid timezone formats."""
        valid_timezones = [
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
            "UTC/GMT"
        ]
        
        for tz in valid_timezones:
            result = list_event_instances(
                calendarId="primary",
                eventId="test-event-id",
                timeZone=tz
            )
            self.assertEqual(result["items"][0]["timeZone"], tz)

    def test_valid_datetime_formats(self):
        """Test various valid ISO datetime formats."""
        valid_datetimes = [
            "2024-01-01T10:00:00Z",
            "2024-06-15T12:30:45Z",
            "2024-12-30T12:00:00Z"
        ]
        
        print(DB["events"])
        for dt in valid_datetimes:
            result = list_event_instances(
                calendarId="primary",
                eventId="test-event-id",
                originalStart=dt,
                timeMin=dt,
                timeMax="2024-12-31T23:59:59Z"
            )
            # Only the first datetime should match and return 1 item
            if dt == "2024-01-01T10:00:00Z":
                self.assertEqual(len(result["items"]), 1)
            else:
                self.assertEqual(len(result["items"]), 0)

    def test_none_parameters(self):
        """Test that None values for optional parameters work correctly."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            maxAttendees=None,
            originalStart=None,
            pageToken=None,
            timeMax=None,
            timeMin=None,
            timeZone=None
        )
        
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(len(result["items"][0]["attendees"]), 3)  # All attendees
        self.assertNotIn("timeZone", result["items"][0])  # No timezone applied 

    # ======================================================================================================================
    # Additional Comprehensive Tests for Full Coverage
    # ======================================================================================================================

    def test_calendar_not_found(self):
        """Test ResourceNotFoundError for non-existent calendar."""
        self.assert_error_behavior(
            list_event_instances,
            ResourceNotFoundError,
            "Calendar 'cal-9999' not found.",
            calendarId="cal-9999",
            eventId="test-event-id"
        )

    def test_time_min_excludes_event(self):
        """Test that timeMin excludes events that start before the specified time."""
        # Create an event that starts before timeMin
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            timeMin="2024-01-01T12:00:00Z"  # After the event start time
        )
        self.assertEqual(len(result["items"]), 0)

    def test_time_max_excludes_event(self):
        """Test that timeMax excludes events that end after the specified time."""
        # Create an event that ends after timeMax
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            timeMax="2024-01-01T10:30:00Z"  # Before the event end time
        )
        self.assertEqual(len(result["items"]), 0)

    def test_time_min_max_includes_event(self):
        """Test that timeMin and timeMax together include events within the range."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            timeMin="2024-01-01T09:00:00Z",
            timeMax="2024-01-01T12:00:00Z"
        )
        self.assertEqual(len(result["items"]), 1)

    def test_original_start_matches(self):
        """Test that originalStart matching includes the event."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            originalStart="2024-01-01T10:00:00Z"
        )
        self.assertEqual(len(result["items"]), 1)

    def test_original_start_no_match(self):
        """Test that originalStart not matching excludes the event."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            originalStart="2024-01-01T11:00:00Z"
        )
        self.assertEqual(len(result["items"]), 0)

    def test_show_deleted_false_excludes_cancelled(self):
        """Test that showDeleted=False excludes cancelled events."""
        # Create a cancelled event
        cancelled_event = {
            "id": "cancelled-event",
            "summary": "Cancelled Event",
            "start": {"dateTime": "2024-01-01T14:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "end": {"dateTime": "2024-01-01T15:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "status": "cancelled"
        }
        DB["events"]["primary:cancelled-event"] = cancelled_event
        
        result = list_event_instances(
            calendarId="primary",
            eventId="cancelled-event",
            showDeleted=False
        )
        self.assertEqual(len(result["items"]), 0)

    def test_show_deleted_true_includes_cancelled(self):
        """Test that showDeleted=True includes cancelled events."""
        # Create a cancelled event
        cancelled_event = {
            "id": "cancelled-event",
            "summary": "Cancelled Event",
            "start": {"dateTime": "2024-01-01T14:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "end": {"dateTime": "2024-01-01T15:00:00", "offset": "+00:00", "timeZone": "Europe/London"},
            "status": "cancelled"
        }
        DB["events"]["primary:cancelled-event"] = cancelled_event
        
        result = list_event_instances(
            calendarId="primary",
            eventId="cancelled-event",
            showDeleted=True
        )
        self.assertEqual(len(result["items"]), 1)

    def test_event_with_malformed_datetime(self):
        """Test handling of events with malformed datetime strings."""
        # Create an event with malformed datetime
        malformed_event = {
            "id": "malformed-event",
            "summary": "Malformed Event",
            "start": {"dateTime": "invalid-datetime", "offset": "+00:00", "timeZone": "Europe/London"},
            "end": {"dateTime": "2024-01-01T15:00:00", "offset": "+00:00", "timeZone": "Europe/London"}
        }
        DB["events"]["primary:malformed-event"] = malformed_event
        
        self.assert_error_behavior(
            func_to_call=list_event_instances,
            expected_exception_type=DateTimeValidationError,
            expected_message="Invalid dateTime",
            calendarId="primary",
            eventId="malformed-event",
            timeMin="2024-01-01T10:00:00Z"
        )

    def test_event_without_start_end_times(self):
        """Test handling of events without start/end times."""
        # Create an event without start/end times
        no_time_event = {
            "id": "no-time-event",
            "summary": "No Time Event"
        }
        DB["events"]["primary:no-time-event"] = no_time_event
        
        # Should not crash, should handle gracefully
        result = list_event_instances(
            calendarId="primary",
            eventId="no-time-event",
            timeMin="2024-01-01T10:00:00Z"
        )
        # Should return the event since time filtering fails gracefully
        self.assertEqual(len(result["items"]), 1)

    def test_max_results_limiting(self):
        """Test that maxResults properly limits the number of returned items."""
        # In this mock implementation, we only return 1 item max, but test the logic
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            maxResults=1
        )
        self.assertEqual(len(result["items"]), 1)
        self.assertLessEqual(len(result["items"]), 1)

    def test_page_token_handling(self):
        """Test that pageToken is handled correctly (though ignored in mock)."""
        result = list_event_instances(
            calendarId="primary",
            eventId="test-event-id",
            pageToken="some-token"
        )
        self.assertEqual(len(result["items"]), 1)
        self.assertIsNone(result["nextPageToken"])

    def test_all_parameters_combined(self):
        """Test all parameters combined in a single call."""
        result = list_event_instances(
            alwaysIncludeEmail=True,
            calendarId="primary",
            eventId="test-event-id",
            maxAttendees=2,
            maxResults=10,
            originalStart="2024-01-01T10:00:00Z",
            pageToken="test-token",
            showDeleted=False,
            timeMax="2024-12-31T23:59:59Z",
            timeMin="2024-01-01T00:00:00Z",
            timeZone="Europe/London"
        )
        
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["timeZone"], "Europe/London")
        self.assertEqual(len(result["items"][0]["attendees"]), 2)

    def test_empty_calendar_list_handling(self):
        """Test handling when calendar_list is empty."""
        DB["calendar_list"] = {}
        
        self.assert_error_behavior(
            list_event_instances,
            ResourceNotFoundError,
            "Calendar 'cal-1000' not found.",
            calendarId="cal-1000",
            eventId="test-event-id"
        )

    def test_empty_events_handling(self):
        """Test handling when events dict is empty."""
        DB["events"] = {}
        
        self.assert_error_behavior(
            list_event_instances,
            ResourceNotFoundError,
            "Event 'test-event-id' not found in calendar 'primary'.",
            calendarId="primary",
            eventId="test-event-id"
        ) 