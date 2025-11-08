from google_calendar import create_secondary_calendar, update_calendar_metadata
import google_calendar.SimulationEngine.db as db_module
from common_utils.base_case import BaseTestCaseWithErrorHandler
import importlib
import sys


class TestUpdateCalendarClearFields(BaseTestCaseWithErrorHandler):
    """Test that update_calendar_metadata can clear optional fields with None."""
    
    def setUp(self):
        """Reset DB before each test."""
        super().setUp()
        
        # Reload modules
        modules_to_reload = ['google_calendar.CalendarsResource']
        for module_name in modules_to_reload:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
        
        global create_secondary_calendar, update_calendar_metadata
        from google_calendar import create_secondary_calendar, update_calendar_metadata
        
        db_module.DB.clear()
        db_module.DB.update({
            "acl_rules": {},
            "calendar_list": {},
            "calendars": {},
            "channels": {},
            "colors": {"calendar": {}, "event": {}},
            "events": {},
        })
        
    def test_update_calendar_with_none_should_clear_description(self):
        """Test that passing description=None in update clears the field.
        
        BUG: update_calendar uses exclude_none=True which drops None values,
        so you cannot clear optional fields. Patch allows None but update doesn't.
        """
        # Create calendar with description
        create_secondary_calendar({
            "id": "test_cal",
            "summary": "Test Calendar",
            "description": "Original description",
            "timeZone": "UTC"
        })
        
        # Update with None description to clear it
        result = update_calendar_metadata(
            "test_cal",
            {
                "summary": "Test Calendar",
                "description": None  # Should clear this field
            }
        )
        
        # CRITICAL: description should be None/cleared
        # This will FAIL if exclude_none=True drops the None value
        self.assertIsNone(result.get("description"),
                         f"description should be cleared when set to None, but got: {result.get('description')}")
        
    def test_update_calendar_with_none_location_clears_field(self):
        """Test that passing location=None clears the location field."""
        # Create calendar with location
        create_secondary_calendar({
            "id": "test_cal2",
            "summary": "Test Calendar 2",
            "location": "New York",
            "timeZone": "America/New_York"
        })
        
        # Update with None location
        result = update_calendar_metadata(
            "test_cal2",
            {
                "summary": "Test Calendar 2",
                "location": None
            }
        )
        
        # Should clear location
        self.assertIsNone(result.get("location"),
                         f"location should be cleared when set to None, but got: {result.get('location')}")
        
    def test_update_allows_clearing_multiple_optional_fields(self):
        """Test that update can clear multiple optional fields at once."""
        # Create calendar with multiple optional fields
        create_secondary_calendar({
            "id": "test_cal3",
            "summary": "Test Calendar 3",
            "description": "Has description",
            "location": "San Francisco",
            "timeZone": "America/Los_Angeles"
        })
        
        # Update with multiple None values
        result = update_calendar_metadata("test_cal3", {
            "summary": "Test Calendar 3",
            "description": None,
            "location": None
        })
        
        # Both should be cleared
        self.assertIsNone(result.get("description"))
        self.assertIsNone(result.get("location"))

