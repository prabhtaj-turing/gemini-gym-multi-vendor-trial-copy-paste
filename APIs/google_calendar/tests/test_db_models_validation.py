"""
Test suite for validating CalendarDefaultDB against GoogleCalendarDB Pydantic models.

This test ensures that:
1. The CalendarDefaultDB structure matches the GoogleCalendarDB Pydantic model
2. All nested models (ACL rules, events, calendars, etc.) validate correctly
3. Field validators work as expected (datetime, timezone, offset, etc.)

Note: These tests validate the structure and schema, not specific data values
which may change over time.
"""

import pytest
import json
from pathlib import Path
from google_calendar.SimulationEngine.db_models import (
    GoogleCalendarDB,
    EventDateTimeModel,
)


class TestDatabaseModelsValidation:
    """Test suite for database model validation against DefaultDB."""

    @pytest.fixture
    def default_db_data(self):
        """Load the CalendarDefaultDB JSON data."""
        # Get the path to the DefaultDB file
        current_dir = Path(__file__).parent.parent.parent.parent
        db_path = current_dir / "DBs" / "CalendarDefaultDB.json"
        
        with open(db_path, 'r') as f:
            return json.load(f)

    @pytest.fixture
    def calendar_db(self, default_db_data):
        """Create a GoogleCalendarDB instance from the default data."""
        return GoogleCalendarDB(**default_db_data)

    def test_database_loads_successfully(self, default_db_data):
        """Test that the DefaultDB can be loaded into the Pydantic model without errors."""
        db = GoogleCalendarDB(**default_db_data)
        assert db is not None
        assert isinstance(db, GoogleCalendarDB)

    def test_database_has_required_top_level_keys(self, calendar_db):
        """Test that the database contains all expected top-level attributes."""
        assert hasattr(calendar_db, 'acl_rules')
        assert hasattr(calendar_db, 'calendar_list')
        assert hasattr(calendar_db, 'calendars')
        assert hasattr(calendar_db, 'channels')
        assert hasattr(calendar_db, 'colors')
        assert hasattr(calendar_db, 'events')

    def test_acl_rules_are_dicts(self, calendar_db):
        """Test that ACL rules are properly structured as dictionaries."""
        assert isinstance(calendar_db.acl_rules, dict)
        
        # If there are ACL rules, validate their structure
        for rule_id, rule in calendar_db.acl_rules.items():
            assert isinstance(rule_id, str)
            assert hasattr(rule, 'ruleId')
            assert hasattr(rule, 'calendarId')
            assert hasattr(rule, 'scope')
            assert hasattr(rule, 'role')

    def test_acl_role_values_are_valid(self, calendar_db):
        """Test that all ACL roles are from the valid set of roles."""
        valid_roles = ['owner', 'writer', 'reader', 'editor', 'commenter', 'organizer', 'viewer', 'freeBusyReader']
        
        for rule_id, rule in calendar_db.acl_rules.items():
            assert rule.role in valid_roles, f"Invalid role '{rule.role}' in rule {rule_id}"

    def test_calendar_list_structure(self, calendar_db):
        """Test that calendar list entries have required attributes."""
        assert isinstance(calendar_db.calendar_list, dict)
        
        for cal_id, cal in calendar_db.calendar_list.items():
            assert isinstance(cal_id, str)
            assert hasattr(cal, 'id')
            assert hasattr(cal, 'summary')
            assert hasattr(cal, 'primary')

    def test_calendars_structure(self, calendar_db):
        """Test that calendars have required attributes."""
        assert isinstance(calendar_db.calendars, dict)
        
        for cal_id, cal in calendar_db.calendars.items():
            assert isinstance(cal_id, str)
            assert hasattr(cal, 'id')
            assert hasattr(cal, 'summary')

    def test_channels_structure(self, calendar_db):
        """Test that channels have required attributes."""
        assert isinstance(calendar_db.channels, dict)
        
        for channel_id, channel in calendar_db.channels.items():
            assert isinstance(channel_id, str)
            assert hasattr(channel, 'id')
            assert hasattr(channel, 'type')
            assert hasattr(channel, 'resource')

    def test_colors_structure(self, calendar_db):
        """Test that color definitions have required structure."""
        assert hasattr(calendar_db.colors, 'calendar')
        assert hasattr(calendar_db.colors, 'event')
        assert isinstance(calendar_db.colors.calendar, dict)
        assert isinstance(calendar_db.colors.event, dict)
        
        # Validate color structure if colors exist
        for color_id, color in calendar_db.colors.calendar.items():
            assert hasattr(color, 'background')
            assert hasattr(color, 'foreground')
        
        for color_id, color in calendar_db.colors.event.items():
            assert hasattr(color, 'background')
            assert hasattr(color, 'foreground')

    def test_events_structure(self, calendar_db):
        """Test that events have required attributes."""
        assert isinstance(calendar_db.events, dict)
        
        for event_key, event in calendar_db.events.items():
            assert isinstance(event_key, str)
            assert hasattr(event, 'id')
            assert hasattr(event, 'summary')

    def test_event_datetime_fields_when_present(self, calendar_db):
        """Test that event datetime fields, when present, have proper structure."""
        for event_key, event in calendar_db.events.items():
            # If start is present, check its structure
            if event.start is not None:
                assert hasattr(event.start, 'dateTime')
                assert hasattr(event.start, 'offset')
                assert hasattr(event.start, 'timeZone')
            
            # If end is present, check its structure
            if event.end is not None:
                assert hasattr(event.end, 'dateTime')
                assert hasattr(event.end, 'offset')
                assert hasattr(event.end, 'timeZone')

    def test_event_attendees_structure_when_present(self, calendar_db):
        """Test that event attendees, when present, have proper structure."""
        for event_key, event in calendar_db.events.items():
            if event.attendees is not None:
                assert isinstance(event.attendees, list)
                for attendee in event.attendees:
                    assert hasattr(attendee, 'email')

    def test_event_attachments_structure_when_present(self, calendar_db):
        """Test that event attachments, when present, have proper structure."""
        for event_key, event in calendar_db.events.items():
            if hasattr(event, 'attachments') and event.attachments is not None:
                assert isinstance(event.attachments, list)
                for attachment in event.attachments:
                    assert hasattr(attachment, 'fileUrl')

    def test_all_event_datetime_formats_valid(self, calendar_db):
        """Test that all event datetime values follow the expected format."""
        import re
        datetime_format_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'
        offset_pattern = r'^[+-]\d{2}:\d{2}$'
        
        for event_key, event in calendar_db.events.items():
            # Validate start datetime format
            if event.start and event.start.dateTime:
                assert re.match(datetime_format_pattern, event.start.dateTime), \
                    f"Invalid datetime format in event {event_key} start: {event.start.dateTime}"
                
                if event.start.offset:
                    assert re.match(offset_pattern, event.start.offset), \
                        f"Invalid offset format in event {event_key} start: {event.start.offset}"
            
            # Validate end datetime format
            if event.end and event.end.dateTime:
                assert re.match(datetime_format_pattern, event.end.dateTime), \
                    f"Invalid datetime format in event {event_key} end: {event.end.dateTime}"
                
                if event.end.offset:
                    assert re.match(offset_pattern, event.end.offset), \
                        f"Invalid offset format in event {event_key} end: {event.end.offset}"

    def test_event_keys_follow_convention(self, calendar_db):
        """Test that event keys follow the format 'calendarId:eventId'."""
        for event_key, event in calendar_db.events.items():
            if ':' in event_key:
                parts = event_key.split(':', 1)
                assert len(parts) == 2, f"Event key should have exactly 2 parts: {event_key}"
                
                _, event_id = parts
                assert event.id == event_id, \
                    f"Event ID mismatch: key has '{event_id}', event has '{event.id}'"

    def test_acl_rules_reference_valid_calendars(self, calendar_db):
        """Test that ACL rules reference calendars that exist in the database."""
        calendar_ids = set(calendar_db.calendars.keys())
        
        for rule_id, rule in calendar_db.acl_rules.items():
            assert rule.calendarId in calendar_ids, \
                f"ACL rule {rule_id} references non-existent calendar {rule.calendarId}"

    def test_channels_with_calendar_id_reference_valid_calendars(self, calendar_db):
        """Test that channels with calendarId reference calendars that exist."""
        calendar_ids = set(calendar_db.calendars.keys())
        
        for channel_id, channel in calendar_db.channels.items():
            # Some channels might not be associated with a specific calendar
            if channel.calendarId and channel.calendarId.strip():
                assert channel.calendarId in calendar_ids, \
                    f"Channel {channel_id} references non-existent calendar {channel.calendarId}"


class TestEventDateTimeModel:
    """Test suite specifically for EventDateTimeModel validation."""

    def test_valid_datetime_format_accepted(self):
        """Test that valid datetime formats are accepted."""
        dt = EventDateTimeModel(
            dateTime='2025-03-10T09:00:00',
            offset='-03:00',
            timeZone='America/Sao_Paulo'
        )
        assert dt.dateTime == '2025-03-10T09:00:00'
        assert dt.offset == '-03:00'
        assert dt.timeZone == 'America/Sao_Paulo'

    def test_none_values_accepted_for_optional_fields(self):
        """Test that None values are accepted for all optional fields."""
        dt = EventDateTimeModel(dateTime=None, offset=None, timeZone=None)
        assert dt.dateTime is None
        assert dt.offset is None
        assert dt.timeZone is None

    def test_partial_datetime_without_offset_and_timezone(self):
        """Test that datetime can be provided without offset and timezone."""
        dt = EventDateTimeModel(dateTime='2025-03-10T09:00:00')
        assert dt.dateTime == '2025-03-10T09:00:00'
        assert dt.offset is None
        assert dt.timeZone is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])