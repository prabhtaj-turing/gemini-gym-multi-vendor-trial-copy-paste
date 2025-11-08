# APIs/google_calendar/tests/test_patch_calendar_list_entry_verification.py

import unittest
from unittest.mock import patch
import uuid

from pydantic import ValidationError

from ..SimulationEngine.db import DB
from .. import patch_calendar_list_entry

class TestPatchCalendarListVerification(unittest.TestCase):
    """Test cases for patch_calendar_list_entry function validation and security."""

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
                    "timeZone": "America/New_York"
                }
            },
            "calendars": {},
            "channels": {},
            "colors": {"calendar": {}, "event": {}},
            "events": {}
        })

    # --- Valid Input Tests ---
    def test_valid_patch_with_summary(self):
        """Test successful patch with summary update."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "Updated Summary"}
        )
        self.assertEqual(result["summary"], "Updated Summary")
        self.assertEqual(result["id"], "test_calendar")
        self.assertEqual(result["description"], "Test description")  # Unchanged
        self.assertEqual(result["timeZone"], "America/New_York")  # Unchanged

    def test_valid_patch_with_multiple_fields(self):
        """Test successful patch with multiple field updates."""
        result = patch_calendar_list_entry(
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

    def test_valid_patch_with_empty_resource(self):
        """Test patch with empty resource dictionary (no changes)."""
        original_entry = DB["calendar_list"]["test_calendar"].copy()
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={}
        )
        self.assertEqual(result, original_entry)

    def test_valid_patch_with_none_resource(self):
        """Test patch with None resource (no changes)."""
        original_entry = DB["calendar_list"]["test_calendar"].copy()
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource=None
        )
        self.assertEqual(result, original_entry)

    def test_valid_patch_with_color_rgb_format_true(self):
        """Test patch with colorRgbFormat=True (parameter accepted but not implemented)."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            colorRgbFormat=True,
            resource={"summary": "Updated with color format"}
        )
        self.assertEqual(result["summary"], "Updated with color format")

    # --- TypeError Tests ---
    def test_calendar_id_not_string(self):
        """Test TypeError when calendarId is not a string."""
        with self.assertRaises(TypeError) as cm:
            patch_calendar_list_entry(calendarId=123, resource={})
        self.assertEqual(str(cm.exception), "calendarId must be a string")

    def test_color_rgb_format_not_boolean(self):
        """Test TypeError when colorRgbFormat is not a boolean."""
        with self.assertRaises(TypeError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                colorRgbFormat="true",
                resource={}
            )
        self.assertEqual(str(cm.exception), "colorRgbFormat must be a boolean")

    def test_resource_not_dictionary(self):
        """Test TypeError when resource is not a dictionary."""
        with self.assertRaises(TypeError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource="not a dict"
            )
        self.assertEqual(str(cm.exception), "resource must be a dictionary")

    def test_resource_list_not_dictionary(self):
        """Test TypeError when resource is a list."""
        with self.assertRaises(TypeError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource=["not", "a", "dict"]
            )
        self.assertEqual(str(cm.exception), "resource must be a dictionary")

    # --- ValueError Tests ---
    def test_calendar_id_empty_string(self):
        """Test ValueError when calendarId is empty string."""
        with self.assertRaises(ValueError) as cm:
            patch_calendar_list_entry(calendarId="", resource={})
        self.assertEqual(str(cm.exception), "calendarId cannot be empty or None")

    def test_calendar_id_whitespace_only(self):
        """Test ValueError when calendarId is whitespace only."""
        with self.assertRaises(ValueError) as cm:
            patch_calendar_list_entry(calendarId="   ", resource={})
        self.assertEqual(str(cm.exception), "calendarId cannot be empty or None")

    def test_calendar_not_found(self):
        """Test ValueError when calendar list entry doesn't exist."""
        with self.assertRaises(ValueError) as cm:
            patch_calendar_list_entry(calendarId="nonexistent", resource={})
        self.assertEqual(str(cm.exception), "CalendarList entry 'nonexistent' not found.")

    def test_summary_not_string(self):
        """Test ValueError when summary field is not a string."""
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"summary": 123}
            )
        self.assertIn("Input should be a valid string", str(cm.exception))

    def test_description_not_string(self):
        """Test ValueError when description field is not a string."""
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"description": ["not", "string"]}
            )
        self.assertIn("Input should be a valid string", str(cm.exception),)

    def test_timezone_not_string(self):
        """Test ValueError when timeZone field is not a string."""
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"timeZone": 123}
            )
        self.assertIn("Input should be a valid string", str(cm.exception),)

    def test_id_field_not_string(self):
        """Test ValueError when id field is not a string."""
        with self.assertRaises(ValueError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"id": 123}
            )
        self.assertEqual("Cannot modify the 'id' field of an existing calendar list entry", str(cm.exception))

    # --- Security Tests ---
    def test_cannot_modify_id_field_different_value(self):
        """Test that modifying ID field to different value is prevented."""
        with self.assertRaises(ValueError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"id": "different_id"}
            )
        self.assertEqual(str(cm.exception), "Cannot modify the 'id' field of an existing calendar list entry")

    def test_can_set_id_field_same_value(self):
        """Test that setting ID field to same value is allowed."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={"id": "test_calendar", "summary": "Updated"}
        )
        self.assertEqual(result["id"], "test_calendar")
        self.assertEqual(result["summary"], "Updated")

    def test_patch_description_with_none(self):
        """Test that patching 'description' with None is allowed."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={"description": None}
        )
        self.assertIsNone(result["description"])
        self.assertEqual(result["summary"], "Test Calendar")  # Unchanged

    def test_patch_with_mixed_none_and_valid_values(self):
        """Test patching with a mix of None and valid values."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={
                "summary": "Updated Summary",
                "description": None
            }
        )
        self.assertEqual(result["summary"], "Updated Summary")
        self.assertIsNone(result["description"])

    def test_valid_summary_with_spaces(self):
        """Test that a valid summary with leading/trailing spaces is accepted."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "  Valid Summary  "}
        )
        self.assertEqual(result["summary"], "Valid Summary")

    def test_empty_summary_in_patch(self):
        """Test ValueError for empty summary string in patch."""
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"summary": " "}
            )
        self.assertIn("summary cannot be empty if provided", str(cm.exception))

    def test_empty_description_in_patch(self):
        """Test that an empty description is accepted and returned as an empty string."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={"description": " "}
        )
        self.assertEqual(result["description"], "")

    def test_patch_with_none_timezone(self):
        """Test that a None timezone is accepted."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={"timeZone": None}
        )
        self.assertIsNone(result["timeZone"])

    def test_empty_timezone_in_patch(self):
        """Test ValueError for empty timeZone string in patch."""
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"timeZone": " "}
            )
        self.assertIn("timeZone cannot be empty if provided", str(cm.exception))

    def test_timezone_with_dangerous_chars_in_patch(self):
        """Test ValueError for timeZone with dangerous characters."""
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"timeZone": "America/New_York;"}
            )
        self.assertIn("potentially dangerous command injection pattern", str(cm.exception))

    def test_timezone_with_invalid_chars_in_patch(self):
        """Test ValueError for timeZone with invalid characters."""
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"timeZone": "America/New_York123"}
            )
        self.assertIn("must contain only letters, underscores, and forward slashes", str(cm.exception))

    def test_timezone_too_long_in_patch(self):
        """Test ValueError for a timeZone string that is too long."""
        long_timezone = "A/" + "a" * 50
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"timeZone": long_timezone}
            )
        self.assertIn("timeZone is too long (maximum 50 characters)", str(cm.exception))

    def test_invalid_summary_type_in_patch(self):
        """Test ValueError for invalid summary type in patch."""
        with self.assertRaises(ValidationError):
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"summary": 12345}
            )

    def test_invalid_description_type_in_patch(self):
        """Test ValueError for invalid description type in patch."""
        with self.assertRaises(ValidationError):
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"description": {"text": "not a string"}}
            )

    def test_invalid_timezone_type_in_patch(self):
        """Test ValueError for invalid timeZone type in patch."""
        with self.assertRaises(ValidationError):
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"timeZone": 123.45}
            )

    def test_invalid_timezone_format_in_patch(self):
        """Test ValueError for invalid IANA timeZone format in patch."""
        with self.assertRaises(ValidationError):
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={"timeZone": "Invalid/TimeZone"}
            )

    # --- Edge Cases ---
    def test_multiple_field_type_validations(self):
        """Test multiple field type validations in single call."""
        with self.assertRaises(ValidationError) as cm:
            patch_calendar_list_entry(
                calendarId="test_calendar",
                resource={
                    "summary": 123,  # First invalid field
                    "description": "valid description"
                }
            )
        self.assertIn("Input should be a valid string", str(cm.exception))

    def test_db_persistence(self):
        """Test that changes are persisted to the database."""
        patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "Persisted Summary"}
        )
        
        # Verify change is in DB
        self.assertEqual(DB["calendar_list"]["test_calendar"]["summary"], "Persisted Summary")

    def test_return_complete_entry(self):
        """Test that function returns complete calendar list entry."""
        result = patch_calendar_list_entry(
            calendarId="test_calendar",
            resource={"summary": "New Summary"}
        )
        
        # Should contain all original fields plus updates
        expected_keys = {"id", "summary", "description", "timeZone"}
        self.assertTrue(expected_keys.issubset(set(result.keys())))


if __name__ == "__main__":
    unittest.main() 