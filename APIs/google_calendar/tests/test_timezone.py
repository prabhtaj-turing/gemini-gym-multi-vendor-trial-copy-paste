# APIs/google_calendar/Tests/test_Calendar.py

import uuid
import tempfile
from pydantic import ValidationError
from datetime import datetime
from unittest.mock import patch


from ..SimulationEngine.db import (
    DB,
    save_state,
    load_state,
)


from common_utils.base_case import BaseTestCaseWithErrorHandler
from common_utils.datetime_utils import DateTimeValidationError
from ..SimulationEngine.custom_errors import (
    InvalidInputError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
)


from ..CalendarListResource import DB as CalendarListResourceDB
from .. import (clear_primary_calendar, create_access_control_rule, create_calendar_list_entry, create_event, create_secondary_calendar, delete_access_control_rule, delete_calendar_list_entry, delete_event, delete_secondary_calendar, get_access_control_rule, get_calendar_and_event_colors, get_calendar_list_entry, get_calendar_metadata, get_event, import_event, list_access_control_rules, list_calendar_list_entries, list_event_instances, list_events, move_event, patch_access_control_rule, patch_calendar_list_entry, patch_calendar_metadata, patch_event, quick_add_event, stop_notification_channel, update_access_control_rule, update_calendar_list_entry, update_calendar_metadata, update_event, watch_access_control_rule_changes, watch_calendar_list_changes, watch_event_changes)

class TestCalendarAPI(BaseTestCaseWithErrorHandler):
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
        # Add default primary and secondary calendars
        primary_cal = {
            "id": "my_primary_calendar",
            "summary": "My Primary Calendar",
            "description": "Default primary calendar",
            "timeZone": "UTC",
            "primary": True
        }
        secondary_cal = {
            "id": "secondary",
            "summary": "Secondary Calendar",
            "description": "Secondary calendar",
            "timeZone": "UTC",
            "primary": False
        }
        DB["calendar_list"]["my_primary_calendar"] = primary_cal
        DB["calendar_list"]["secondary"] = secondary_cal
        DB["calendars"]["my_primary_calendar"] = primary_cal.copy()
        DB["calendars"]["secondary"] = secondary_cal.copy()

    def setup_test_event(self, event_id="event123"):
        """Create a test event with the specified ID for patch_event tests"""
        # Ensure the primary calendar exists
        if "primary" not in DB["calendar_list"]:
            DB["calendar_list"]["primary"] = {
                "id": "primary",
                "summary": "Primary Calendar",
                "description": "Default primary calendar",
                "timeZone": "UTC",
            }
        
        # Create the test event
        test_event = {
            "id": event_id,
            "summary": "Original Summary",
            "description": "Original description"
        }
        DB["events"][f"primary:{event_id}"] = test_event
        return test_event

    def test_create_event_datetime_YYYY_MM_DDTHH_MM_SSZ_no_timezone_success(self):
        """Test that create_event uses the datetime in RFC 3339 YYYY-MM-DDTHH:MM:SSZ format if the timezone is not provided."""
        event = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00Z"},
                "end": {"dateTime": "2024-01-01T11:00:00Z"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00+00:00")
        self.assertIsNone(event["start"]["timeZone"])
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00+00:00")
        self.assertIsNone(event["end"]["timeZone"])

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T10:00:00")
        self.assertEqual(event_DB["start"]["offset"], "+00:00")
        self.assertIsNone(event_DB["start"]["timeZone"])
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T11:00:00")
        self.assertEqual(event_DB["end"]["offset"], "+00:00")
        self.assertIsNone(event_DB["end"]["timeZone"])
    
    def test_create_event_datetime_YYYY_MM_DDTHH_MM_SS_HH_MM_no_timezone_success(self):
        """Test that create_event uses the datetime in ISO 8601 UTC Offset format if the timezone is not provided."""
        event = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00+03:00"},
                "end": {"dateTime": "2024-01-01T11:00:00+03:00"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00+03:00")
        self.assertIsNone(event["start"]["timeZone"])
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00+03:00")
        self.assertIsNone(event["end"]["timeZone"])

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T07:00:00")
        self.assertEqual(event_DB["start"]["offset"], "+03:00")
        self.assertIsNone(event_DB["start"]["timeZone"])
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T08:00:00")
        self.assertEqual(event_DB["end"]["offset"], "+03:00")
        self.assertIsNone(event_DB["end"]["timeZone"])
    
    def test_create_event_datetime_YYYY_MM_DDTHH_MM_SS_no_timezone_failure(self):
        """Test that create_event raises an error if the datetime is in RFC 3339 YYYY-MM-DDTHH:MM:SS format and the timezone is not provided."""
        self.assert_error_behavior(func_to_call=create_event,
                                   expected_exception_type=DateTimeValidationError,
                                   expected_message="Invalid datetime format for Google Calendar (dateTime='2024-01-01T10:00:00'): If timeZone is not provided, dateTime must have timezone information.",
                                   resource={
                                       "summary": "Test Event",
                                       "start": {"dateTime": "2024-01-01T10:00:00"},
                                       "end": {"dateTime": "2024-01-01T11:00:00"},
                                   })
    
    def test_create_event_datetime_YYYY_MM_DDTHH_MM_SSZ_with_timezone_success(self):
        """Test that create_event uses the datetime in ISO 8601 UTC Z format if the timezone is provided."""
        event = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00Z", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-01-01T11:00:00Z", "timeZone": "America/New_York"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00+00:00")
        self.assertEqual(event["start"]["timeZone"], "America/New_York")
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00+00:00")
        self.assertEqual(event["end"]["timeZone"], "America/New_York")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T10:00:00")
        self.assertEqual(event_DB["start"]["offset"], "+00:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T11:00:00")
        self.assertEqual(event_DB["end"]["offset"], "+00:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/New_York")
    
    def test_create_event_datetime_YYYY_MM_DDTHH_MM_SS_HH_MM_with_timezone_success(self):
        """Test that create_event uses the datetime in RFC 3339 YYYY-MM-DDTHH:MM:SS+/-HH:MM format if the timezone is provided."""
        event = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00+03:00", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-01-01T11:00:00+03:00", "timeZone": "America/New_York"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00+03:00")
        self.assertEqual(event["start"]["timeZone"], "America/New_York")
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00+03:00")
        self.assertEqual(event["end"]["timeZone"], "America/New_York")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T07:00:00")
        self.assertEqual(event_DB["start"]["offset"], "+03:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T08:00:00")
        self.assertEqual(event_DB["end"]["offset"], "+03:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/New_York")
    
    def test_create_event_datetime_YYYY_MM_DDTHH_MM_SS_with_timezone_success(self):
        """Test that create_event uses the datetime in RFC 3339 YYYY-MM-DDTHH:MM:SS format if the timezone is provided."""
        event = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-01-01T11:00:00", "timeZone": "America/New_York"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00-05:00")
        self.assertEqual(event["start"]["timeZone"], "America/New_York")
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00-05:00")
        self.assertEqual(event["end"]["timeZone"], "America/New_York")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T15:00:00")
        self.assertEqual(event_DB["start"]["offset"], "-05:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T16:00:00")
        self.assertEqual(event_DB["end"]["offset"], "-05:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/New_York")
    
    def test_get_event_converts_to_local_timezone(self):
        """Test that get_event converts the datetime back to the original timezone."""
        DB["events"]["my_primary_calendar:event123"] = {
            "id": "event123",
            "summary": "Original Summary",
            "description": "Original description",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
        }

        event = get_event(eventId="event123")
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T07:00:00-03:00")
        self.assertEqual(event["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T08:00:00-03:00")
        self.assertEqual(event["end"]["timeZone"], "America/Sao_Paulo")
    
    def test_import_event_datetime_YYYY_MM_DDTHH_MM_SSZ_no_timezone_success(self):
        """Test that import_event uses the datetime in RFC 3339 YYYY-MM-DDTHH:MM:SSZ format if the timezone is not provided."""
        event = import_event(
            calendarId="my_primary_calendar",
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00Z"},
                "end": {"dateTime": "2024-01-01T11:00:00Z"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00Z")
        self.assertIsNone(event["start"].get("timeZone"))
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00Z")
        self.assertIsNone(event["end"].get("timeZone"))

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T10:00:00")
        self.assertEqual(event_DB["start"]["offset"], "+00:00")
        self.assertIsNone(event_DB["start"]["timeZone"])
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T11:00:00")
        self.assertEqual(event_DB["end"]["offset"], "+00:00")
        self.assertIsNone(event_DB["end"]["timeZone"])
    
    def test_import_event_datetime_YYYY_MM_DDTHH_MM_SS_HH_MM_no_timezone_success(self):
        """Test that import_event uses the datetime in RFC 3339 YYYY-MM-DDTHH:MM:SS+/-HH:MM format if the timezone is not provided."""
        event = import_event(
            calendarId="my_primary_calendar",
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00+03:00"},
                "end": {"dateTime": "2024-01-01T11:00:00+03:00"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00+03:00")
        self.assertIsNone(event["start"].get("timeZone"))
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00+03:00")
        self.assertIsNone(event["end"].get("timeZone"))

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T07:00:00")
        self.assertEqual(event_DB["start"]["offset"], "+03:00")
        self.assertIsNone(event_DB["start"]["timeZone"])
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T08:00:00")
        self.assertEqual(event_DB["end"]["offset"], "+03:00")
        self.assertIsNone(event_DB["end"]["timeZone"])
    
    def test_import_event_datetime_YYYY_MM_DDTHH_MM_SS_no_timezone_failure(self):
        """Test that import_event raises an error if the datetime is in RFC 3339 YYYY-MM-DDTHH:MM:SS format and the timezone is not provided."""
        self.assert_error_behavior(func_to_call=import_event,
                                   expected_exception_type=DateTimeValidationError,
                                   expected_message="If timeZone is not provided, dateTime must have timezone information.",
                                   calendarId="my_primary_calendar",
                                   resource={
                                       "summary": "Test Event",
                                       "start": {"dateTime": "2024-01-01T10:00:00"},
                                       "end": {"dateTime": "2024-01-01T11:00:00"},
                                   })
    
    def test_import_event_datetime_YYYY_MM_DDTHH_MM_SSZ_with_timezone_success(self):
        """Test that import_event uses the datetime in RFC 3339 YYYY-MM-DDTHH:MM:SSZ format if the timezone is provided."""
        event = import_event(
            calendarId="my_primary_calendar",
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00Z", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-01-01T11:00:00Z", "timeZone": "America/New_York"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00Z")
        self.assertEqual(event["start"]["timeZone"], "America/New_York")
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00Z")
        self.assertEqual(event["end"]["timeZone"], "America/New_York")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T10:00:00")
        self.assertEqual(event_DB["start"]["offset"], "+00:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T11:00:00")
        self.assertEqual(event_DB["end"]["offset"], "+00:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/New_York")
    
    def test_import_event_datetime_YYYY_MM_DDTHH_MM_SS_HH_MM_with_timezone_success(self):
        """Test that import_event uses the datetime in RFC 3339 YYYY-MM-DDTHH:MM:SS+/-HH:MM format if the timezone is provided."""
        event = import_event(
            calendarId="my_primary_calendar",
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00+03:00", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-01-01T11:00:00+03:00", "timeZone": "America/New_York"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00+03:00")
        self.assertEqual(event["start"]["timeZone"], "America/New_York")
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00+03:00")
        self.assertEqual(event["end"]["timeZone"], "America/New_York")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T07:00:00")
        self.assertEqual(event_DB["start"]["offset"], "+03:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T08:00:00")
        self.assertEqual(event_DB["end"]["offset"], "+03:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/New_York")
    
    def test_import_event_datetime_YYYY_MM_DDTHH_MM_SS_with_timezone_success(self):
        """Test that import_event uses the datetime in RFC 3339 YYYY-MM-DDTHH:MM:SS format if the timezone is provided."""
        event = import_event(
            calendarId="my_primary_calendar",
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-01-01T11:00:00", "timeZone": "America/New_York"},
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["dateTime"], "2024-01-01T10:00:00")
        self.assertEqual(event["start"]["timeZone"], "America/New_York")
        self.assertEqual(event["end"]["dateTime"], "2024-01-01T11:00:00")
        self.assertEqual(event["end"]["timeZone"], "America/New_York")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{event["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T15:00:00")
        self.assertEqual(event_DB["start"]["offset"], "-05:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T16:00:00")
        self.assertEqual(event_DB["end"]["offset"], "-05:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/New_York")
    
    def test_list_event_instances_datetime_converts_to_local_timezone(self):
        """Test that list_event_instances converts the datetime to the local timezone."""
        DB["events"]["my_primary_calendar:event123"] = {
            "id": "event123",
            "summary": "Original Summary",
            "description": "Original description",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
        }

        result = list_event_instances(calendarId="my_primary_calendar", eventId="event123")
        self.assertEqual(result["items"][0]["start"]["dateTime"], "2024-01-01T07:00:00-03:00")
        self.assertEqual(result["items"][0]["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(result["items"][0]["end"]["dateTime"], "2024-01-01T08:00:00-03:00")
        self.assertEqual(result["items"][0]["end"]["timeZone"], "America/Sao_Paulo")
    
    def test_list_events_converts_to_local_timezone(self):
        """Test that list_events converts the datetime to the local timezone."""
        DB["events"]["my_primary_calendar:event123"] = {
            "id": "event123",
            "summary": "Original Summary",
            "description": "Original description",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
        }
        result = list_events()
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["start"]["dateTime"], "2024-01-01T10:00:00+00:00")
        self.assertEqual(result["items"][0]["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(result["items"][0]["end"]["dateTime"], "2024-01-01T11:00:00+00:00")
        self.assertEqual(result["items"][0]["end"]["timeZone"], "America/Sao_Paulo")
    
    def test_list_events_converts_to_calendar_timezone_by_default(self):
        """Test that list_events converts the datetime to the calendar timezone by default."""
        DB["events"]["my_primary_calendar:event123"] = {
            "id": "event123",
            "summary": "Original Summary",
            "description": "Original description",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
        }
        result = list_events()
        self.assertEqual(result["items"][0]["start"]["dateTime"], "2024-01-01T10:00:00+00:00")
        self.assertEqual(result["items"][0]["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(result["items"][0]["end"]["dateTime"], "2024-01-01T11:00:00+00:00")
        self.assertEqual(result["items"][0]["end"]["timeZone"], "America/Sao_Paulo")

    def test_list_events_converts_to_calendar_timezone_not_string_failure(self):
        """Test that list_events converts the datetime to the calendar timezone by default."""
        self.assert_error_behavior(func_to_call=list_events,
                                   expected_exception_type=TypeError,
                                   expected_message="timeZone must be a string if provided.",
                                   timeZone=123)

    def test_list_events_converts_to_calendar_timezone_empty_string_failure(self):
        """Test that list_events converts the datetime to the calendar timezone by default."""
        self.assert_error_behavior(func_to_call=list_events,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="timeZone cannot be empty or whitespace.",
                                   timeZone="")

    def test_list_events_converts_to_calendar_timezone_invalid_format_failure(self):
        """Test that list_events converts the datetime to the calendar timezone by default."""
        self.assert_error_behavior(func_to_call=list_events,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="timeZone must be in format 'Continent/City' (e.g., 'America/New_York').",
                                   timeZone="invalid_timezone_IANA")

    def test_list_events_converts_to_calendar_keeps_original_timezone(self):
        """Test that list_events converts the datetime to the calendar timezone by default."""
        DB["events"]["my_primary_calendar:event123"] = {
            "id": "event123",
            "summary": "Original Summary",
            "description": "Original description",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
        }
        result = list_events(timeZone="Europe/Brussels")
        self.assertEqual(result["items"][0]["start"]["dateTime"], "2024-01-01T11:00:00+01:00")
        self.assertEqual(result["items"][0]["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(result["items"][0]["end"]["dateTime"], "2024-01-01T12:00:00+01:00")
        self.assertEqual(result["items"][0]["end"]["timeZone"], "America/Sao_Paulo")
    
    def test_move_event_converts_to_local_timezone(self):
        """Test that move_event converts the datetime to the local timezone."""
        DB["events"]["my_primary_calendar:event123"] = {
            "id": "event123",
            "summary": "Original Summary",
            "description": "Original description",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
        }
        result = move_event(calendarId="my_primary_calendar", eventId="event123", destination="my_secondary_calendar")
        
        # Assert returned event
        self.assertEqual(result["start"]["dateTime"], "2024-01-01T07:00:00-03:00")
        self.assertEqual(result["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(result["end"]["dateTime"], "2024-01-01T08:00:00-03:00")
        self.assertEqual(result["end"]["timeZone"], "America/Sao_Paulo")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_secondary_calendar:{result["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2024-01-01T10:00:00")
        self.assertEqual(event_DB["start"]["offset"], "-03:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(event_DB["end"]["dateTime"], "2024-01-01T11:00:00")
        self.assertEqual(event_DB["end"]["offset"], "-03:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/Sao_Paulo")

    def test_patch_event_converts_to_local_timezone(self):
        """Test that patch_event converts the datetime to the local timezone."""
        DB["events"]["my_primary_calendar:event123"] = {
            "id": "event123",
            "summary": "Original Summary",
            "description": "Original description",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
        }
        result = patch_event(calendarId="my_primary_calendar", eventId="event123", resource={
            "start": {"dateTime": "2025-01-01T07:00:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2025-01-01T08:00:00", "timeZone": "America/Sao_Paulo"},
        })

        # Assert returned event
        self.assertEqual(result["start"]["dateTime"], "2025-01-01T07:00:00-03:00")
        self.assertEqual(result["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(result["end"]["dateTime"], "2025-01-01T08:00:00-03:00")
        self.assertEqual(result["end"]["timeZone"], "America/Sao_Paulo")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{result["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2025-01-01T10:00:00")
        self.assertEqual(event_DB["start"]["offset"], "-03:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(event_DB["end"]["dateTime"], "2025-01-01T11:00:00")
        self.assertEqual(event_DB["end"]["offset"], "-03:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/Sao_Paulo")
    
    def test_update_event_converts_to_local_timezone(self):
        """Test that update_event converts the datetime to the local timezone."""
        DB["events"]["my_primary_calendar:event123"] = {
            "id": "event123",
            "summary": "Original Summary",
            "description": "Original description",
            "start": {"dateTime": "2024-01-01T10:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2024-01-01T11:00:00", "offset": "-03:00", "timeZone": "America/Sao_Paulo"},
        }

        result = update_event(calendarId="my_primary_calendar", eventId="event123", resource={
            "start": {"dateTime": "2025-01-01T07:00:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": "2025-01-01T08:00:00", "timeZone": "America/Sao_Paulo"},
        })

        # Assert returned event
        self.assertEqual(result["start"]["dateTime"], "2025-01-01T07:00:00-03:00")
        self.assertEqual(result["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(result["end"]["dateTime"], "2025-01-01T08:00:00-03:00")
        self.assertEqual(result["end"]["timeZone"], "America/Sao_Paulo")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][f'my_primary_calendar:{result["id"]}']
        self.assertEqual(event_DB["start"]["dateTime"], "2025-01-01T10:00:00")
        self.assertEqual(event_DB["start"]["offset"], "-03:00")
        self.assertEqual(event_DB["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(event_DB["end"]["dateTime"], "2025-01-01T11:00:00")
        self.assertEqual(event_DB["end"]["offset"], "-03:00")
        self.assertEqual(event_DB["end"]["timeZone"], "America/Sao_Paulo")
    
    def test_create_event_with_complies_with_daylight_saving_time(self):
        """Test that create_event complies with daylight saving time."""
        event_before_DST = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-03-09T10:00:00", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-03-09T11:00:00", "timeZone": "America/New_York"},
            }
        )

        event_after_DST = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-03-11T10:00:00", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-03-11T11:00:00", "timeZone": "America/New_York"},
            }
        )

        print(event_before_DST)
        self.assertEqual(event_before_DST["start"]["dateTime"], "2024-03-09T10:00:00-05:00")
        self.assertEqual(event_before_DST["end"]["dateTime"], "2024-03-09T11:00:00-05:00")
        self.assertEqual(event_before_DST["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_before_DST["end"]["timeZone"], "America/New_York")
        self.assertEqual(event_after_DST["start"]["dateTime"], "2024-03-11T10:00:00-04:00")
        self.assertEqual(event_after_DST["end"]["dateTime"], "2024-03-11T11:00:00-04:00")
        self.assertEqual(event_after_DST["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_after_DST["end"]["timeZone"], "America/New_York")
    
    def test_create_and_list_events_different_timezones_filtering_by_timemin_timemax(self):
        """Test that create_event and list_events work with different timezones."""
        event_1 = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00", "timeZone": "America/Sao_Paulo"},
                "end": {"dateTime": "2024-01-01T11:00:00", "timeZone": "America/Sao_Paulo"},
            }
        )

        event_2 = create_event(
            resource={
                "summary": "Test Event",
                "start": {"dateTime": "2024-01-01T10:00:00", "timeZone": "America/New_York"},
                "end": {"dateTime": "2024-01-01T11:00:00", "timeZone": "America/New_York"},
            }
        )
        
        self.assertEqual(event_1["start"]["dateTime"], "2024-01-01T10:00:00-03:00")
        self.assertEqual(event_1["start"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(event_1["end"]["dateTime"], "2024-01-01T11:00:00-03:00")
        self.assertEqual(event_1["end"]["timeZone"], "America/Sao_Paulo")
        self.assertEqual(event_2["start"]["dateTime"], "2024-01-01T10:00:00-05:00")
        self.assertEqual(event_2["start"]["timeZone"], "America/New_York")
        self.assertEqual(event_2["end"]["dateTime"], "2024-01-01T11:00:00-05:00")
        self.assertEqual(event_2["end"]["timeZone"], "America/New_York")

        listed_events_1 = list_events(timeMin="2024-01-01T09:30:00-03:00", timeMax="2024-01-01T11:30:00-03:00")
        self.assertEqual(len(listed_events_1["items"]), 1)
        self.assertEqual(listed_events_1["items"][0]["id"], event_1["id"])

        listed_events_2 = list_events(timeMin="2024-01-01T09:30:00-05:00", timeMax="2024-01-01T11:30:00-05:00")
        self.assertEqual(len(listed_events_2["items"]), 1)
        self.assertEqual(listed_events_2["items"][0]["id"], event_2["id"])

    # ===== Timezone Awareness Tests for list_events =====
    
    def test_list_events_timeMin_timeMax_with_Z_suffix_success(self):
        """Test that list_events accepts timeMin/timeMax with Z suffix (UTC format)."""
        result = list_events(
            timeMin="2024-04-01T00:00:00Z",
            timeMax="2024-04-01T23:59:59Z"
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
    
    def test_list_events_timeMin_timeMax_with_offset_success(self):
        """Test that list_events accepts timeMin/timeMax with timezone offset."""
        result = list_events(
            timeMin="2024-04-01T00:00:00+05:00",
            timeMax="2024-04-01T23:59:59-05:00"
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
    
    def test_list_events_timeMin_timeMax_without_timezone_fails(self):
        """Test that list_events rejects timeMin/timeMax without timezone information."""
        # Test timeMin without timezone
        with self.assertRaises(InvalidInputError) as cm:
            list_events(timeMin="2024-04-01T00:00:00")
        self.assertIn("timeMin must be a valid RFC 3339 datetime string.", str(cm.exception))
        
        # Test timeMax without timezone
        with self.assertRaises(InvalidInputError) as cm:
            list_events(timeMax="2024-04-01T23:59:59")
        self.assertIn("timeMax must be a valid RFC 3339 datetime string.", str(cm.exception))
    
    def test_list_events_timeMin_timeMax_mixed_formats_success(self):
        """Test that list_events accepts mixed timezone formats."""
        result = list_events(
            timeMin="2024-04-01T00:00:00Z",
            timeMax="2024-04-01T23:59:59+05:00"
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
    
    def test_list_events_timeMin_timeMax_various_offsets_success(self):
        """Test that list_events accepts various timezone offsets."""
        test_cases = [
            ("2024-04-01T00:00:00+00:00", "2024-04-01T23:59:59+00:00"),  # UTC
            ("2024-04-01T00:00:00+01:00", "2024-04-01T23:59:59+01:00"),  # +1 hour
            ("2024-04-01T00:00:00-01:00", "2024-04-01T23:59:59-01:00"),  # -1 hour
            ("2024-04-01T00:00:00+05:30", "2024-04-01T23:59:59+05:30"),  # +5:30 (India)
            ("2024-04-01T00:00:00-08:00", "2024-04-01T23:59:59-08:00"),  # -8 hours (PST)
        ]
        
        for timeMin, timeMax in test_cases:
            with self.subTest(timeMin=timeMin, timeMax=timeMax):
                result = list_events(timeMin=timeMin, timeMax=timeMax)
                self.assertIsInstance(result, dict)
                self.assertIn("items", result)
    
    def test_list_events_timeMin_timeMax_invalid_formats_fail(self):
        """Test that list_events rejects invalid datetime formats."""
        invalid_formats = [
            "2024-04-01T00:00:00",  # No timezone
            "2024-04-01 00:00:00",  # Space instead of T
            "2024/04/01T00:00:00Z",  # Wrong date separator
            "2024-04-01T00:00:00+5:00",  # Missing leading zero in offset
            "invalid-date",  # Completely invalid
        ]
        
        for invalid_format in invalid_formats:
            with self.subTest(format=invalid_format):
                with self.assertRaises(InvalidInputError) as cm:
                    list_events(timeMin=invalid_format)
                # Check that we get an appropriate error message
                error_msg = str(cm.exception)
                self.assertTrue(
                    "timeMin must be a valid RFC 3339 datetime string." in error_msg or 
                    "Invalid datetime format" in error_msg,
                    f"Expected timezone-aware or invalid format error, got: {error_msg}"
                )
    
    def test_list_events_timeMin_timeMax_valid_formats_success(self):
        """Test that list_events accepts valid datetime formats."""
        valid_formats = [
            "2024-04-01T00:00:00Z",  # UTC with Z
            "2024-04-01T00:00:00+00:00",  # UTC with offset
            "2024-04-01T00:00:00+05:00",  # With colon in offset
        ]
        
        for valid_format in valid_formats:
            with self.subTest(format=valid_format):
                result = list_events(timeMin=valid_format)
                self.assertIsInstance(result, dict)
                self.assertIn("items", result)
    
    def test_list_events_timeMin_timeMax_edge_cases(self):
        """Test edge cases for timeMin/timeMax parsing."""
        # Test with milliseconds
        result = list_events(
            timeMin="2024-04-01T00:00:00.000Z",
            timeMax="2024-04-01T23:59:59.999Z"
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        
        # Test with different timezone offsets
        result = list_events(
            timeMin="2024-04-01T00:00:00.123+05:30",
            timeMax="2024-04-01T23:59:59.456-08:00"
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
    
    def test_list_events_original_colab_example(self):
        """Test the original Colab example that was failing."""
        # This is the exact example from the bug report
        result = list_events(
            timeMin="2024-04-01T00:00:00Z",
            timeMax="2024-04-01T23:59:59Z"
        )
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
    
    def test_list_events_timezone_awareness_error_messages(self):
        """Test that error messages are clear and helpful."""
        # Test timeMin error message
        with self.assertRaises(InvalidInputError) as cm:
            list_events(timeMin="2024-04-01T00:00:00")
        error_msg = str(cm.exception)
        self.assertEqual("timeMin must be a valid RFC 3339 datetime string.", error_msg)
        
        # Test timeMax error message
        with self.assertRaises(InvalidInputError) as cm:
            list_events(timeMax="2024-04-01T23:59:59")
        error_msg = str(cm.exception)
        self.assertEqual("timeMax must be a valid RFC 3339 datetime string.", error_msg)

    # ===== Bug #1143: Timezone Consistency Tests =====
    
    def test_bug_1143_timezone_consistency_utc_events(self):
        """Test Bug #1143: UTC events maintain timezone consistency between create and list operations."""
        # Create UTC event (ending with 'Z')
        utc_event_data = {
            "summary": "UTC Event",
            "start": {"dateTime": "2024-01-15T15:00:00Z"},
            "end": {"dateTime": "2024-01-15T16:00:00Z"}
        }
        
        created_event = create_event(calendarId="primary", resource=utc_event_data)
        listed_events = list_events(calendarId="primary")
        
        self.assertEqual(len(listed_events['items']), 1)
        listed_event = listed_events['items'][0]
        
        # Check timezone field consistency
        self.assertEqual(created_event['start']['timeZone'], listed_event['start']['timeZone'])
        self.assertEqual(created_event['end']['timeZone'], listed_event['end']['timeZone'])
        
        # For UTC events, timeZone should be None
        self.assertIsNone(created_event['start']['timeZone'])
        self.assertIsNone(created_event['end']['timeZone'])
        self.assertIsNone(listed_event['start']['timeZone'])
        self.assertIsNone(listed_event['end']['timeZone'])
        
        # Check that datetime is converted to calendar timezone but timeZone field is preserved
        self.assertTrue(created_event['start']['dateTime'].endswith('+00:00'))
        self.assertTrue(listed_event['start']['dateTime'].endswith('+00:00'))  # UTC calendar

    def test_bug_1143_timezone_consistency_specific_timezone_events(self):
        """Test Bug #1143: Events with specific timezones maintain timezone consistency between create and list operations."""
        # Create event with specific timezone
        la_event_data = {
            "summary": "LA Event",
            "start": {"dateTime": "2024-01-15T10:00:00", "timeZone": "America/Los_Angeles"},
            "end": {"dateTime": "2024-01-15T11:00:00", "timeZone": "America/Los_Angeles"}
        }
        
        created_event = create_event(calendarId="primary", resource=la_event_data)
        listed_events = list_events(calendarId="primary")
        
        self.assertEqual(len(listed_events['items']), 1)
        listed_event = listed_events['items'][0]
        
        # Check timezone field consistency
        self.assertEqual(created_event['start']['timeZone'], listed_event['start']['timeZone'])
        self.assertEqual(created_event['end']['timeZone'], listed_event['end']['timeZone'])
        
        # timeZone field should be preserved as original
        self.assertEqual(created_event['start']['timeZone'], "America/Los_Angeles")
        self.assertEqual(created_event['end']['timeZone'], "America/Los_Angeles")
        self.assertEqual(listed_event['start']['timeZone'], "America/Los_Angeles")
        self.assertEqual(listed_event['end']['timeZone'], "America/Los_Angeles")
        
        # Check that datetime is converted to calendar timezone but timeZone field is preserved
        self.assertTrue(created_event['start']['dateTime'].endswith('-08:00'))  # LA offset
        self.assertTrue(listed_event['start']['dateTime'].endswith('+00:00'))  # UTC offset

    def test_bug_1143_timezone_consistency_with_custom_timezone_parameter(self):
        """Test Bug #1143: Timezone consistency is maintained when using custom timeZone parameter in list_events."""
        # Create event with specific timezone
        event_data = {
            "summary": "Mixed Timezone Event",
            "start": {"dateTime": "2024-01-15T14:00:00", "timeZone": "Europe/London"},
            "end": {"dateTime": "2024-01-15T15:00:00", "timeZone": "Europe/London"}
        }
        
        created_event = create_event(calendarId="primary", resource=event_data)
        
        # List with different timezone parameter
        listed_events = list_events(calendarId="primary", timeZone="Asia/Tokyo")
        
        self.assertEqual(len(listed_events['items']), 1)
        listed_event = listed_events['items'][0]
        
        # Check timezone field consistency - should be preserved as original
        self.assertEqual(created_event['start']['timeZone'], listed_event['start']['timeZone'])
        self.assertEqual(created_event['end']['timeZone'], listed_event['end']['timeZone'])
        
        # timeZone field should be preserved as original (Europe/London)
        self.assertEqual(created_event['start']['timeZone'], "Europe/London")
        self.assertEqual(listed_event['start']['timeZone'], "Europe/London")
        
        # Check that datetime is converted to requested timezone (Asia/Tokyo)
        self.assertTrue(created_event['start']['dateTime'].endswith('+00:00'))  # UTC offset
        self.assertTrue(listed_event['start']['dateTime'].endswith('+09:00'))  # Tokyo offset

    def test_bug_1143_reproduction_scenario(self):
        """Test Bug #1143: Reproduce the exact scenario described in the bug report."""
        # This test reproduces the exact issue described in the bug report
        # where create_event and list_events showed different timezones
        
        # Scenario 1: UTC event
        utc_event = create_event(calendarId="primary", resource={
            "summary": "UTC Event",
            "start": {"dateTime": "2024-01-15T15:00:00Z"},
            "end": {"dateTime": "2024-01-15T16:00:00Z"}
        })
        
        # Scenario 2: Event with specific timezone
        tz_event = create_event(calendarId="primary", resource={
            "summary": "Timezone Event",
            "start": {"dateTime": "2024-01-15T10:00:00", "timeZone": "America/Los_Angeles"},
            "end": {"dateTime": "2024-01-15T11:00:00", "timeZone": "America/Los_Angeles"}
        })
        
        # List all events
        all_events = list_events(calendarId="primary")
        self.assertEqual(len(all_events['items']), 2)
        
        # Find our events
        utc_listed = next(e for e in all_events['items'] if e['summary'] == "UTC Event")
        tz_listed = next(e for e in all_events['items'] if e['summary'] == "Timezone Event")
        
        # Verify timezone consistency for UTC event
        self.assertEqual(utc_event['start']['timeZone'], utc_listed['start']['timeZone'])
        self.assertEqual(utc_event['end']['timeZone'], utc_listed['end']['timeZone'])
        self.assertIsNone(utc_event['start']['timeZone'])
        self.assertIsNone(utc_listed['start']['timeZone'])
        
        # Verify timezone consistency for timezone event
        self.assertEqual(tz_event['start']['timeZone'], tz_listed['start']['timeZone'])
        self.assertEqual(tz_event['end']['timeZone'], tz_listed['end']['timeZone'])
        self.assertEqual(tz_event['start']['timeZone'], "America/Los_Angeles")
        self.assertEqual(tz_listed['start']['timeZone'], "America/Los_Angeles")
        
        # Verify that datetime conversion still works (different offsets due to calendar timezone)
        self.assertTrue(utc_event['start']['dateTime'].endswith('+00:00'))
        self.assertTrue(utc_listed['start']['dateTime'].endswith('+00:00'))
        self.assertTrue(tz_event['start']['dateTime'].endswith('-08:00'))
        self.assertTrue(tz_listed['start']['dateTime'].endswith('+00:00'))

    def test_bug_1143_timezone_field_preservation_with_multiple_events(self):
        """Test Bug #1143: Timezone fields are preserved correctly with multiple events of different timezones."""
        # Create events with different timezones
        events_data = [
            {
                "summary": "UTC Event",
                "start": {"dateTime": "2024-01-15T12:00:00Z"},
                "end": {"dateTime": "2024-01-15T13:00:00Z"}
            },
            {
                "summary": "LA Event",
                "start": {"dateTime": "2024-01-15T09:00:00", "timeZone": "America/Los_Angeles"},
                "end": {"dateTime": "2024-01-15T10:00:00", "timeZone": "America/Los_Angeles"}
            },
            {
                "summary": "London Event",
                "start": {"dateTime": "2024-01-15T17:00:00", "timeZone": "Europe/London"},
                "end": {"dateTime": "2024-01-15T18:00:00", "timeZone": "Europe/London"}
            }
        ]
        
        created_events = []
        for event_data in events_data:
            created_events.append(create_event(calendarId="primary", resource=event_data))
        
        # List all events
        listed_events = list_events(calendarId="primary")
        self.assertEqual(len(listed_events['items']), 3)
        
        # Verify timezone field consistency for each event
        for i, created_event in enumerate(created_events):
            listed_event = next(e for e in listed_events['items'] if e['summary'] == created_event['summary'])
            
            # timeZone field should be consistent
            self.assertEqual(created_event['start']['timeZone'], listed_event['start']['timeZone'])
            self.assertEqual(created_event['end']['timeZone'], listed_event['end']['timeZone'])
            
            # Verify specific timezone values
            if created_event['summary'] == "UTC Event":
                self.assertIsNone(created_event['start']['timeZone'])
                self.assertIsNone(listed_event['start']['timeZone'])
            elif created_event['summary'] == "LA Event":
                self.assertEqual(created_event['start']['timeZone'], "America/Los_Angeles")
                self.assertEqual(listed_event['start']['timeZone'], "America/Los_Angeles")
            elif created_event['summary'] == "London Event":
                self.assertEqual(created_event['start']['timeZone'], "Europe/London")
                self.assertEqual(listed_event['start']['timeZone'], "Europe/London")
