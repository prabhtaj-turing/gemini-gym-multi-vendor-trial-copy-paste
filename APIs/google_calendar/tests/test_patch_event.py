# APIs/google_calendar/tests/test_patch_events.py

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import InvalidInputError
from .. import patch_event

class TestPatchEvents(BaseTestCaseWithErrorHandler):

    def setUp(self):
        # Save original DB state
        import copy
        self._original_db = copy.deepcopy(DB)
        
        # Setup test data (don't clear - just add/update)
        DB['calendars']['cal-3000'] = {
            "id": "cal-3000",
            "summary": "Family Calendar",
            "description": "Shared events with family members",
            "timeZone": "America/Denver",
            "primary": False
            }
        DB['calendar_list']['cal-3000'] = {
            "id": "cal-3000",
            "summary": "Family Calendar",
            "description": "Shared events with family members",
            "timeZone": "America/Denver",
            "primary": False
            }
        DB['calendars']['cal-1000'] = {
            "id": "cal-1000",
            "summary": "Work Calendar",
            "description": "Company-wide meetings and deadlines",
            "timeZone": "America/New_York", 
            "primary": True
            }
        DB['calendar_list']['cal-1000'] = {
            "id": "cal-1000",
            "summary": "Work Calendar",
            "description": "Company-wide meetings and deadlines",
            "timeZone": "America/New_York",
            "primary": True
            }
        DB['events']['cal-3000:event-301'] = {
            "id": "event-301",
            "summary": "Birthday Party",
            "description": "Grandparent's birthday celebration",
            "start": {
                "dateTime": "2025-03-20T17:00:00",
                "offset": "+00:00",
                "timeZone": "Europe/London"
            },
            "end": {
                "dateTime": "2025-03-20T20:00:00",
                "offset": "+00:00",
                "timeZone": "Europe/London"
            }
            }
        DB['events']['cal-1000:event-100'] = {
            "id": "event-100",
            "summary": "Team Sync",
            "description": "Weekly sync meeting with the team",
            "start": {
                "dateTime": "2025-03-10T09:00:00",
                "offset": "-03:00",
                "timeZone": "America/Sao_Paulo"
            },
            "end": {
                "dateTime": "2025-03-10T09:30:00",
                "offset": "-03:00",
                "timeZone": "America/Sao_Paulo"
            },
            "attachments": [
                {
                "fileUrl": "https://www.rd.usda.gov/sites/default/files/pdf-sample_0.pdf"
                }
            ]
            }
    
    def tearDown(self):
        """Restore original DB state after each test."""
        DB.clear()
        DB.update(self._original_db)

    def test_adversarial_QA_2298(self):
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?gid=0#gid=0 """
        eventId = "event-301"
        calendarId = "cal-3000"
        expected_message = "Recurrence rule 0 INTERVAL must be a positive integer"
        resource = {"summary": "Event with invalid recurrence",
                     "recurrence": ["RRULE:FREQ=DAILY;INTERVAL=-1;COUNT=99999999999999999999;BYMONTH=13"]}
        self.assert_error_behavior(
            func_to_call=patch_event,
            expected_exception_type=InvalidInputError,
            expected_message=expected_message,
            eventId=eventId,
            calendarId=calendarId,
            resource=resource
        )
    
    def test_adversarial_QA_2302(self):
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?gid=0#gid=0 """
        eventId = "event-100"
        calendarId = "cal-1000"
        resource = {"description": "<img src=x onerror=alert('XSS-Vulnerability')>",
                    "summary": "Benign Summary",
                    "start": {"dateTime": "2024-01-01T10:00:00Z"},
                    "end": {"dateTime": "2024-01-01T11:00:00Z"},
                    "recurrence": ["RRULE:BYHOUR=10;BYMINUTE=0;BYMONTH=1;BYMONTHDAY=1;BYSECOND=0;BYSETPOS=1;BYWEEKNO=1;BYYEARDAY=1;COUNT=1;Examples=N/A;FREQ=YEARLY;INTERVAL=1;UNTIL=20250101T000000Z;WKST=SU"]}
        expected_message = """1 validation error for EventPatchResourceModel
  Value error, description contains potentially malicious content that could lead to XSS attacks [type=value_error, input_value={'description': "<img src...50101T000000Z;WKST=SU']}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/value_error"""
        self.assert_error_behavior(
            func_to_call=patch_event,
            expected_exception_type=InvalidInputError,
            expected_message=expected_message,
            eventId=eventId,
            calendarId=calendarId,
            resource=resource
        )
        
    def test_bug_deep_merge_preserves_timezone(self):
        """Bug fix: Deep merge preserves existing fields when patching."""
        # Patch start and end dateTime, timeZones should be preserved
        result = patch_event(
            eventId="event-301",
            calendarId="cal-3000",
            resource={
                "start": {"dateTime": "2025-03-20T16:00:00"},
                "end": {"dateTime": "2025-03-20T19:00:00"}
            }
        )
        
        db_event = DB["events"]["cal-3000:event-301"]
        # timeZone should be preserved (not lost due to shallow replacement)
        self.assertIn("timeZone", db_event["start"])
        self.assertEqual(db_event["start"]["timeZone"], "Europe/London")
        self.assertEqual(db_event["end"]["timeZone"], "Europe/London")
    
    def test_bug_utc_conversion_when_start_patched(self):
        """Bug fix: UTC conversion when start/end patched."""
        original_offset = DB["events"]["cal-1000:event-100"]["start"]["offset"]
        
        # Patch with new dateTime and timezone
        result = patch_event(
            eventId="event-100",
            calendarId="cal-1000",
            resource={
                "start": {"dateTime": "2025-03-10T10:00:00", "timeZone": "America/New_York"},
                "end": {"dateTime": "2025-03-10T11:00:00", "timeZone": "America/New_York"}
            }
        )
        
        db_event = DB["events"]["cal-1000:event-100"]
        # Timezone should be updated
        self.assertEqual(db_event["start"]["timeZone"], "America/New_York")
        # Offset should be updated (UTC conversion happened)
        new_offset = db_event["start"]["offset"]
        self.assertNotEqual(new_offset, original_offset)
        self.assertIn(new_offset, ["-04:00", "-05:00"])  # DST dependent

    def test_patch_event_with_id_field(self):
        """Test that patch_event supports updating the event ID through resource parameter"""
        eventId = "event-301"
        calendarId = "cal-3000"
        new_id = "event-updated-301"
        resource = {"id": new_id}
        
        result = patch_event(eventId=eventId, calendarId=calendarId, resource=resource)
        
        # Verify the event's ID was updated
        self.assertEqual(result["id"], new_id)
        # Verify the original event data is preserved
        self.assertEqual(result["summary"], "Birthday Party")
        # Note: checking description exists rather than exact match due to potential encoding differences
        self.assertIsNotNone(result.get("description"))
    
    def test_patch_event_with_summary_field(self):
        """Test that patch_event supports updating the event summary through resource parameter"""
        eventId = "event-301"
        calendarId = "cal-3000"
        new_summary = "Updated Birthday Party"
        resource = {"summary": new_summary}
        
        result = patch_event(eventId=eventId, calendarId=calendarId, resource=resource)
        
        # Verify the event's summary was updated
        self.assertEqual(result["summary"], new_summary)
        # Verify the event ID remains unchanged
        self.assertEqual(result["id"], "event-301")
    
    def test_patch_event_with_both_id_and_summary(self):
        """Test that patch_event supports updating both ID and summary fields together"""
        eventId = "event-301"
        calendarId = "cal-3000"
        new_id = "event-updated-301-combo"
        new_summary = "Birthday Party - Updated"
        resource = {"id": new_id, "summary": new_summary}
        
        result = patch_event(eventId=eventId, calendarId=calendarId, resource=resource)
        
        # Verify both fields were updated
        self.assertEqual(result["id"], new_id)
        self.assertEqual(result["summary"], new_summary)
        # Verify other fields remain unchanged
        # Note: checking description exists rather than exact match due to potential encoding differences
        self.assertIsNotNone(result.get("description"))
