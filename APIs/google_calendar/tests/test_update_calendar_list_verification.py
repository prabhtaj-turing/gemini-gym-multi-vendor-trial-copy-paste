# APIs/google_calendar/tests/test_update_calendar_list_entry_verification.py

import unittest
from unittest.mock import patch
import uuid

from ..SimulationEngine.db import DB
from .. import update_calendar_list_entry

class TestUpdateCalendarListVerification(unittest.TestCase):
    """Test cases for update_calendar_list_entry function validation and security."""

    def setUp(self):
        """Set up test data before each test."""
        DB.clear()
        DB.update({
            "acl_rules": {},
            "calendar_list": {
                "primary": {
                    "id": "primary",
                    "summary": "Primary Calendar",
                    "description": "Default primary calendar",
                    "timeZone": "UTC",
                    "primary": True
                },
                "test_calendar": {
                    "id": "test_calendar",
                    "summary": "Test Calendar",
                    "description": "Test description",
                    "timeZone": "America/New_York",
                    "customField": "existing_value"
                }
            },
            "calendars": {},
            "channels": {},
            "colors": {"calendar": {}, "event": {}},
            "events": {}
        })

    # --- Valid Input Tests ---
    def test_valid_update_with_summary(self):
        """Test successful update with summary only."""
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "Updated Summary"}
        )
        self.assertEqual(result["summary"], "Updated Summary")
        self.assertEqual(result["id"], "test_calendar")
        # Should not contain old fields (full replacement)
        self.assertNotIn("description", result)
        self.assertNotIn("timeZone", result)
        self.assertNotIn("customField", result)

    def test_valid_update_with_multiple_fields(self):
        """Test successful update with multiple field updates."""
        result = update_calendar_list_entry(
            calendarId="primary",
            resource={
                "summary": "New Primary Summary",
                "description": "New description",
                "timeZone": "Europe/London"
            }
        )
        self.assertEqual(result["summary"], "New Primary Summary")
        self.assertEqual(result["description"], "New description")
        self.assertEqual(result["timeZone"], "Europe/London")
        self.assertEqual(result["id"], "primary")

    def test_valid_update_replaces_entire_entry(self):
        """Test that update replaces entire entry (not merge like patch)."""
        # Original entry has customField
        original_entry = DB["calendar_list"]["test_calendar"]
        self.assertIn("customField", original_entry)
        
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "Only Summary"}
        )
        
        # Result should only have id and summary
        self.assertEqual(len(result), 2)
        self.assertEqual(result["id"], "test_calendar")
        self.assertEqual(result["summary"], "Only Summary")
        self.assertNotIn("customField", result)
        self.assertNotIn("description", result)
        self.assertNotIn("timeZone", result)

    def test_valid_update_with_color_rgb_format_true(self):
        """Test update with colorRgbFormat=True (parameter accepted but not implemented)."""
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            colorRgbFormat=True,
            resource={"summary": "Updated with color format"}
        )
        self.assertEqual(result["summary"], "Updated with color format")

    def test_valid_update_with_additional_field(self):
        """Test update with additional custom field."""
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource={
                "summary": "New Summary",
                "customField": "custom value"
            }
        )
        self.assertEqual(result["customField"], "custom value")
        self.assertEqual(result["summary"], "New Summary")

    def test_valid_update_with_same_id_in_resource(self):
        """Test update with matching id in resource is allowed."""
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource={
                "id": "test_calendar",
                "summary": "Updated Summary"
            }
        )
        self.assertEqual(result["id"], "test_calendar")
        self.assertEqual(result["summary"], "Updated Summary")

    # --- TypeError Tests ---
    def test_calendar_id_not_string(self):
        """Test TypeError when calendarId is not a string."""
        with self.assertRaises(TypeError) as cm:
            update_calendar_list_entry(calendarId=123, resource={"summary": "test"})
        self.assertEqual(str(cm.exception), "calendarId must be a string")

    def test_color_rgb_format_not_boolean(self):
        """Test TypeError when colorRgbFormat is not a boolean."""
        with self.assertRaises(TypeError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                colorRgbFormat="true",
                resource={"summary": "test"}
            )
        self.assertEqual(str(cm.exception), "colorRgbFormat must be a boolean")

    def test_resource_not_dictionary(self):
        """Test TypeError when resource is not a dictionary."""
        with self.assertRaises(TypeError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                resource="not a dict"
            )
        self.assertEqual(str(cm.exception), "resource must be a dictionary")

    def test_resource_list_not_dictionary(self):
        """Test TypeError when resource is a list."""
        with self.assertRaises(TypeError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                resource=["not", "a", "dict"]
            )
        self.assertEqual(str(cm.exception), "resource must be a dictionary")

    # --- ValueError Tests ---
    def test_calendar_id_empty_string(self):
        """Test ValueError when calendarId is empty string."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(calendarId="", resource={"summary": "test"})
        self.assertEqual(str(cm.exception), "calendarId cannot be empty or None")

    def test_calendar_id_whitespace_only(self):
        """Test ValueError when calendarId is whitespace only."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(calendarId="   ", resource={"summary": "test"})
        self.assertEqual(str(cm.exception), "calendarId cannot be empty or None")

    def test_resource_is_none(self):
        """Test ValueError when resource is None."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(calendarId="test_calendar", resource=None)
        self.assertEqual(str(cm.exception), "Resource is required for full update.")

    def test_calendar_not_found(self):
        """Test ValueError when calendar list entry doesn't exist."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(calendarId="nonexistent", resource={"summary": "test"})
        self.assertEqual(str(cm.exception), "CalendarList entry 'nonexistent' not found.")

    def test_summary_not_string(self):
        """Test ValueError when summary field is not a string."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                resource={"summary": 123}
            )
        self.assertEqual(str(cm.exception), "Field 'summary' must be a string")

    def test_description_not_string(self):
        """Test ValueError when description field is not a string."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                resource={"description": ["not", "string"]}
            )
        self.assertEqual(str(cm.exception), "Field 'description' must be a string")

    def test_timezone_not_string(self):
        """Test ValueError when timeZone field is not a string."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                resource={"timeZone": 123}
            )
        self.assertEqual(str(cm.exception), "Field 'timeZone' must be a string")

    def test_id_field_not_string(self):
        """Test ValueError when id field is not a string."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                resource={"id": 123}
            )
        self.assertEqual(str(cm.exception), "Field 'id' must be a string")

    # --- Security Tests ---
    def test_cannot_set_different_id_field(self):
        """Test that setting ID field to different value is prevented."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                resource={"id": "different_id", "summary": "test"}
            )
        self.assertEqual(str(cm.exception), "Cannot set 'id' field to a different value than calendarId")

    # --- Edge Cases ---
    def test_update_with_none_values(self):
        """Test update with None values in resource."""
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource={"customField": None}
        )
        self.assertIsNone(result["customField"])
        self.assertEqual(result["id"], "test_calendar")

    def test_update_with_empty_resource_dict(self):
        """Test update with empty resource dictionary."""
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource={}
        )
        # Should only contain the id field
        self.assertEqual(len(result), 1)
        self.assertEqual(result["id"], "test_calendar")

    def test_multiple_field_type_validations(self):
        """Test multiple field type validations in single call."""
        with self.assertRaises(ValueError) as cm:
            update_calendar_list_entry(
                calendarId="test_calendar",
                resource={
                    "summary": 123,  # First invalid field
                    "description": "valid description"
                }
            )
        self.assertEqual(str(cm.exception), "Field 'summary' must be a string")

    def test_db_persistence(self):
        """Test that changes are persisted to the database."""
        update_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "Persisted Summary"}
        )
        
        # Verify change is in DB and old fields are gone
        db_entry = DB["calendar_list"]["test_calendar"]
        self.assertEqual(db_entry["summary"], "Persisted Summary")
        self.assertEqual(db_entry["id"], "test_calendar")
        self.assertNotIn("description", db_entry)  # Should be gone (full replacement)
        self.assertNotIn("customField", db_entry)  # Should be gone (full replacement)

    def test_input_resource_not_modified(self):
        """Test that the original input resource dictionary is not modified."""
        original_resource = {"summary": "Original Summary"}
        original_copy = original_resource.copy()
        
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource=original_resource
        )
        
        # Original resource should be unchanged
        self.assertEqual(original_resource, original_copy)
        # Result should have the id added
        self.assertIn("id", result)
        self.assertEqual(result["id"], "test_calendar")

    def test_return_complete_entry(self):
        """Test that function returns complete calendar list entry."""
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "New Summary", "description": "New Description"}
        )
        
        # Should contain all provided fields plus id
        expected_keys = {"id", "summary", "description"}
        self.assertEqual(set(result.keys()), expected_keys)

    def test_update_vs_patch_behavior(self):
        """Test that update replaces entire entry (unlike patch which merges)."""
        # Setup: calendar has multiple fields
        original_fields = set(DB["calendar_list"]["test_calendar"].keys())
        self.assertGreater(len(original_fields), 2)  # Has more than just id
        
        # Update with only one field
        result = update_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "Only Summary"}
        )
        
        # Result should only have id and summary (full replacement)
        self.assertEqual(set(result.keys()), {"id", "summary"})
        self.assertEqual(result["summary"], "Only Summary")
        self.assertEqual(result["id"], "test_calendar")


if __name__ == "__main__":
    unittest.main() 