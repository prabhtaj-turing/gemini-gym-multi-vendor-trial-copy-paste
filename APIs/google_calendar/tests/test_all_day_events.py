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
        
        # Create the test event with required start and end fields
        test_event = {
            "id": event_id,
            "summary": "Original Summary",
            "description": "Original description",
            "start": {
                "dateTime": "2024-03-20T10:00:00",
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": "2024-03-20T11:00:00",
                "timeZone": "UTC"
            }
        }
        DB["events"][("primary:" + event_id)] = test_event
        return test_event

    def test_create_event_all_day_event_success(self):
        event = create_event(
            resource={
                "summary": "Test Event",
                "start": {"date": "2024-01-01"},
                "end": {"date": "2024-01-02"}
            }
        )

        # Assert returned event
        self.assertEqual(event["start"]["date"], "2024-01-01")
        self.assertEqual(event["end"]["date"], "2024-01-02")

        # Assert event is stored correctly in the DB
        event_DB = DB["events"][("my_primary_calendar:" + event["id"])]
        self.assertEqual(event_DB["start"]["date"], "2024-01-01")
        self.assertEqual(event_DB["end"]["date"], "2024-01-02")

    def test_create_event_all_day_event_start_date_and_dateTime_failure(self):
        self.assert_error_behavior(func_to_call=create_event,
                                   expected_exception_type=DateTimeValidationError,
                                   expected_message="Invalid datetime format for Google Calendar (date='2024-01-01', dateTime='2024-01-01T10:00:00Z'): date and dateTime cannot be provided at the same time",
                                   resource={
                                    "summary": "Test Event",
                                    "start": {"date": "2024-01-01", "dateTime": "2024-01-01T10:00:00Z"},
                                    "end": {"date": "2024-01-02"}
                                   })
    
    def test_create_event_all_day_event_end_date_and_dateTime_failure(self):
        self.assert_error_behavior(func_to_call=create_event,
                                   expected_exception_type=DateTimeValidationError,
                                   expected_message="Invalid datetime format for Google Calendar (date='2024-01-02', dateTime='2024-01-02T10:00:00Z'): date and dateTime cannot be provided at the same time",
                                   resource={
                                    "summary": "Test Event",
                                    "start": {"date": "2024-01-01"},
                                    "end": {"date": "2024-01-02", "dateTime": "2024-01-02T10:00:00Z"}
                                   })
    
    def test_create_event_all_day_event_start_date_and_end_dateTime_failure(self):
        self.assert_error_behavior(func_to_call=create_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="Start and end times must either both be date or both be dateTime.",
                                   resource={
                                    "summary": "Test Event",
                                    "start": {"date": "2024-01-01"},
                                    "end": {"dateTime": "2024-01-02T10:00:00Z"}
                                   })
    
    def test_create_event_all_day_event_end_date_and_start_dateTime_failure(self):
        self.assert_error_behavior(func_to_call=create_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="Start and end times must either both be date or both be dateTime.",
                                   resource={
                                    "summary": "Test Event",
                                    "start": {"dateTime": "2024-01-01T10:00:00Z"},
                                    "end": {"date": "2024-01-02"}
                                   })
    
    def test_list_events_instances_all_day_event_success(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        result = list_event_instances(
            eventId="event123",
            timeMin="2024-01-01",
            timeMax="2024-01-04"
        )
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["start"]["date"], "2024-01-02")
        self.assertEqual(result["items"][0]["end"]["date"], "2024-01-03")
    
    def test_list_events_instances_all_day_event_timeMin_and_timeMax_out_of_range(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        result = list_event_instances(
            eventId="event123",
            timeMin="2024-01-04",
            timeMax="2024-01-05"
        )
        print(result)
        self.assertEqual(len(result["items"]), 0)
    
    def test_list_events_all_day_event_success(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        result = list_events(timeMin="2024-01-01T00:00:00Z", timeMax="2024-01-04T00:00:00Z")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["start"]["date"], "2024-01-02")
        self.assertEqual(result["items"][0]["end"]["date"], "2024-01-03")
    
    def test_list_events_all_day_event_timeMin_and_timeMax_out_of_range(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        result = list_events(timeMin="2024-01-04T00:00:00Z", timeMax="2024-01-05T00:00:00Z")
        self.assertEqual(len(result["items"]), 0)

    def test_patch_event_all_day_event_not_start_or_end_success(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        patched_event = patch_event(eventId="event123", calendarId="my_primary_calendar", resource={"summary": "Test Event Updated"})
        self.assertEqual(patched_event["summary"], "Test Event Updated")
        self.assertEqual(patched_event["start"]["date"], "2024-01-02")
        self.assertEqual(patched_event["end"]["date"], "2024-01-03")
    
    def test_patch_event_all_day_event_start_success(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        patched_event = patch_event(eventId="event123", calendarId="my_primary_calendar", resource={"start": {"date": "2024-01-03"}})
        self.assertEqual(patched_event["start"]["date"], "2024-01-03")
        self.assertEqual(patched_event["end"]["date"], "2024-01-03")
    
    def test_patch_event_all_day_event_end_success(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        patched_event = patch_event(eventId="event123", calendarId="my_primary_calendar", resource={"end": {"date": "2024-01-02"}})
        self.assertEqual(patched_event["end"]["date"], "2024-01-02")
        self.assertEqual(patched_event["start"]["date"], "2024-01-02")
    
    def test_patch_event_all_day_event_start_dateTime_and_end_date_failure(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        self.assert_error_behavior(func_to_call=patch_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="Start and end times must either both be date or both be dateTime.",
                                   eventId="event123", calendarId="my_primary_calendar", resource={"start": {"dateTime": "2024-01-03T10:00:00Z"}})
    
    def test_patch_event_all_day_event_end_dateTime_and_start_date_failure(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        self.assert_error_behavior(func_to_call=patch_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="Start and end times must either both be date or both be dateTime.",
                                   eventId="event123", calendarId="my_primary_calendar", resource={"end": {"dateTime": "2024-01-02T10:00:00Z"}})
    
    def test_update_event_all_day_event_not_start_or_end_success(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        updated_event = update_event(eventId="event123", calendarId="my_primary_calendar", resource={
            "summary": "Test Event Updated",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        })
        self.assertEqual(updated_event["summary"], "Test Event Updated")
        self.assertIsNotNone(updated_event.get("start"))
        self.assertIsNotNone(updated_event.get("end"))
    
    def test_update_event_all_day_event_only_start_failure(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="1 validation error for EventResourceInputModel\nend\n  Field required [type=missing, input_value={'start': {'date': '2024-01-03'}}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing",
                                   eventId="event123", calendarId="my_primary_calendar", resource={"start": {"date": "2024-01-03"}})
    
    def test_update_event_all_day_event_only_end_failure(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="1 validation error for EventResourceInputModel\nstart\n  Field required [type=missing, input_value={'end': {'date': '2024-01-02'}}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing",
                                   eventId="event123", calendarId="my_primary_calendar", resource={"end": {"date": "2024-01-02"}})
    
    def test_update_event_all_day_event_start_dateTime_and_end_date_failure(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="1 validation error for EventResourceInputModel\nend\n  Field required [type=missing, input_value={'start': {'dateTime': '2024-01-03T10:00:00Z'}}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing",
                                   eventId="event123", calendarId="my_primary_calendar", resource={"start": {"dateTime": "2024-01-03T10:00:00Z"}})
    
    def test_update_event_all_day_event_end_dateTime_and_start_date_failure(self):
        DB["events"][("my_primary_calendar:event123")] = {
            "id": "event123",
            "summary": "Test Event",
            "description": "Test description",
            "start": {"date": "2024-01-02", "dateTime": None, "timeZone": None},
            "end": {"date": "2024-01-03", "dateTime": None, "timeZone": None}
        }
        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message="1 validation error for EventResourceInputModel\nstart\n  Field required [type=missing, input_value={'end': {'dateTime': '2024-01-02T10:00:00Z'}}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing",
                                   eventId="event123", calendarId="my_primary_calendar", resource={"end": {"dateTime": "2024-01-02T10:00:00Z"}})

    def test_create_and_list_all_day_event_success(self):
        event = create_event(
            resource={
                "summary": "Test Event",
                "start": {"date": "2024-01-10"},
                "end": {"date": "2024-01-10"}
            }
        )
        result = list_events(timeMin="2024-01-09T12:00:00Z", timeMax="2024-01-11T12:00:00Z")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["start"]["date"], "2024-01-10")
        self.assertEqual(result["items"][0]["end"]["date"], "2024-01-10")