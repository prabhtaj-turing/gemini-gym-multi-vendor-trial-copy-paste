
from ..SimulationEngine.db import (
    DB,
    save_state,
    load_state,
)


from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import (create_secondary_calendar, get_calendar_metadata, patch_calendar_metadata)

class TestPatchCalendar(BaseTestCaseWithErrorHandler):
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
        DB["calendar_list"]["primary"] = {
            "id": "primary",
            "summary": "Primary Calendar",
            "description": "Default primary calendar",
            "timeZone": "UTC",
            "primary": True
        }
        DB["calendar_list"]["secondary"] = {
            "id": "secondary",
            "summary": "Secondary Calendar",
            "description": "Secondary calendar",
            "timeZone": "UTC",
        }
        # Ensure calendars storage is also set up
        DB["calendars"]["primary"] = DB["calendar_list"]["primary"].copy()
        DB["calendars"]["secondary"] = DB["calendar_list"]["secondary"].copy()

    # ======================================================================================================================
    # Comprehensive Test Cases for patch_calendar_metadata Function
    # ======================================================================================================================

    def test_patch_calendar_metadata_valid_single_field(self):
        """Test patching a calendar with a single valid field."""
        cal_id = "test_calendar_patch_1"
        # Create a test calendar
        create_secondary_calendar({
            "id": cal_id,
            "summary": "Original Summary",
            "description": "Original Description",
            "timeZone": "UTC"
        })
        
        # Patch with just summary
        result = patch_calendar_metadata(
            cal_id, {"summary": "Updated Summary"}
        )
        
        self.assertEqual(result["summary"], "Updated Summary")
        self.assertEqual(result["description"], "Original Description")  # Should remain unchanged
        self.assertEqual(result["timeZone"], "UTC")  # Should remain unchanged
        self.assertEqual(result["id"], cal_id)

    def test_patch_calendar_metadata_valid_multiple_fields(self):
        """Test patching a calendar with multiple valid fields."""
        cal_id = "test_calendar_patch_2"
        # Create a test calendar
        create_secondary_calendar({
            "id": cal_id,
            "summary": "Original Summary",
            "description": "Original Description",
            "timeZone": "UTC"
        })
        
        # Patch with multiple fields
        result = patch_calendar_metadata(
            cal_id, {
                "summary": "Updated Summary", 
                "description": "Updated Description",
                "timeZone": "America/New_York"
            }
        )
        
        self.assertEqual(result["summary"], "Updated Summary")
        self.assertEqual(result["description"], "Updated Description")
        self.assertEqual(result["timeZone"], "America/New_York")
        self.assertEqual(result["id"], cal_id)

    def test_patch_calendar_metadata_with_none_resource(self):
        """Test patching a calendar with None resource returns existing calendar."""
        cal_id = "test_calendar_patch_3"
        # Create a test calendar
        original = create_secondary_calendar({
            "id": cal_id,
            "summary": "Original Summary",
            "description": "Original Description",
            "timeZone": "UTC"
        })
        
        # Patch with None resource
        result = patch_calendar_metadata(cal_id, None)
        
        self.assertEqual(result["summary"], "Original Summary")
        self.assertEqual(result["description"], "Original Description")
        self.assertEqual(result["timeZone"], "UTC")
        self.assertEqual(result["id"], cal_id)

    def test_patch_calendar_metadata_with_empty_resource(self):
        """Test patching a calendar with empty resource dictionary."""
        cal_id = "test_calendar_patch_4"
        # Create a test calendar
        create_secondary_calendar({
            "id": cal_id,
            "summary": "Original Summary",
            "description": "Original Description",
            "timeZone": "UTC"
        })
        
        # Patch with empty resource
        result = patch_calendar_metadata(cal_id, {})
        
        # Should return unchanged calendar
        self.assertEqual(result["summary"], "Original Summary")
        self.assertEqual(result["description"], "Original Description")
        self.assertEqual(result["timeZone"], "UTC")
        self.assertEqual(result["id"], cal_id)

    def test_patch_calendar_metadata_with_none_values(self):
        """Test patching calendar fields with None values to clear them."""
        cal_id = "test_calendar_patch_5"
        # Create a test calendar
        create_secondary_calendar({
            "id": cal_id,
            "summary": "Original Summary",
            "description": "Original Description",
            "timeZone": "UTC"
        })
        
        # Patch with None values
        result = patch_calendar_metadata(
            cal_id, {"description": None}
        )
        
        self.assertEqual(result["summary"], "Original Summary")  # Should remain unchanged
        self.assertIsNone(result["description"])  # Should be cleared
        self.assertEqual(result["timeZone"], "UTC")  # Should remain unchanged

    # Error Tests
    def test_patch_calendar_metadata_invalid_calendar_id_type(self):
        """Test TypeError for non-string calendarId."""
        self.assert_error_behavior(
            patch_calendar_metadata,
            TypeError,
            "calendarId must be a string.",
            calendarId=123,
            resource={"summary": "Test"}
        )

    def test_patch_calendar_metadata_nonexistent_calendar(self):
        """Test ValueError for nonexistent calendar."""
        self.assert_error_behavior(
            patch_calendar_metadata,
            ValueError,
            "Calendar 'nonexistent_calendar' not found.",
            calendarId="nonexistent_calendar",
            resource={"summary": "Test"}
        )

    def test_patch_calendar_metadata_invalid_resource_type(self):
        """Test TypeError for non-dictionary resource."""
        cal_id = "primary"  # Use existing calendar
        self.assert_error_behavior(
            patch_calendar_metadata,
            TypeError,
            "resource must be a dictionary.",
            calendarId=cal_id,
            resource="not_a_dictionary"
        )

    def test_patch_calendar_metadata_disallowed_field(self):
        """Test ValueError for disallowed field in resource."""
        cal_id = "primary"  # Use existing calendar
        self.assert_error_behavior(
            patch_calendar_metadata,
            ValueError,
            "Field 'id' is not allowed for calendar patching. Allowed fields: description, summary, timeZone",
            calendarId=cal_id,
            resource={"id": "malicious_id_change"}
        )

    def test_patch_calendar_metadata_multiple_disallowed_fields(self):
        """Test ValueError for multiple disallowed fields."""
        cal_id = "primary"  # Use existing calendar
        self.assert_error_behavior(
            patch_calendar_metadata,
            ValueError,
            "Field 'malicious_field' is not allowed for calendar patching. Allowed fields: description, summary, timeZone",
            calendarId=cal_id,
            resource={
                "summary": "Valid summary",
                "malicious_field": "should not be allowed"
            }
        )

    def test_patch_calendar_metadata_invalid_field_type_summary(self):
        """Test TypeError for invalid type in summary field."""
        cal_id = "primary"  # Use existing calendar
        self.assert_error_behavior(
            patch_calendar_metadata,
            TypeError,
            "Field 'summary' must be a string, got int.",
            calendarId=cal_id,
            resource={"summary": 123}
        )

    def test_patch_calendar_metadata_invalid_field_type_description(self):
        """Test TypeError for invalid type in description field."""
        cal_id = "primary"  # Use existing calendar
        self.assert_error_behavior(
            patch_calendar_metadata,
            TypeError,
            "Field 'description' must be a string, got bool.",
            calendarId=cal_id,
            resource={"description": False}
        )

    def test_patch_calendar_metadata_invalid_field_type_timezone(self):
        """Test TypeError for invalid type in timeZone field."""
        cal_id = "primary"  # Use existing calendar
        self.assert_error_behavior(
            patch_calendar_metadata,
            TypeError,
            "Field 'timeZone' must be a string, got list.",
            calendarId=cal_id,
            resource={"timeZone": ["UTC"]}
        )

    def test_patch_calendar_metadata_empty_timezone(self):
        """Test ValueError for empty timeZone string."""
        cal_id = "primary"  # Use existing calendar
        self.assert_error_behavior(
            patch_calendar_metadata,
            ValueError,
            "timeZone cannot be an empty string.",
            calendarId=cal_id,
            resource={"timeZone": ""}
        )

    def test_patch_calendar_metadata_whitespace_timezone(self):
        """Test ValueError for whitespace-only timeZone string."""
        cal_id = "primary"  # Use existing calendar
        self.assert_error_behavior(
            patch_calendar_metadata,
            ValueError,
            "timeZone cannot be an empty string.",
            calendarId=cal_id,
            resource={"timeZone": "   "}
        )

    def test_patch_calendar_metadata_security_mass_assignment_prevention(self):
        """Test that mass assignment vulnerability is prevented."""
        cal_id = "primary"  # Use existing calendar
        
        # Try to inject sensitive fields that shouldn't be modifiable
        sensitive_fields = ["id", "etag", "kind", "owner", "accessRole", "malicious_field"]
        
        for field in sensitive_fields:
            with self.assertRaises(ValueError) as cm:
                patch_calendar_metadata(
                    cal_id, {field: "malicious_value"}
                )
            self.assertIn(f"Field '{field}' is not allowed for calendar patching", str(cm.exception))

    def test_patch_calendar_metadata_data_persistence(self):
        """Test that patches are properly persisted in both DB storage locations."""
        # Use an existing calendar to avoid test isolation issues
        cal_id = "primary"
        
        # Store the original state for cleanup
        original_summary = DB["calendar_list"][cal_id]["summary"]
        
        # Patch the calendar
        try:
            patched_result = patch_calendar_metadata(
                cal_id, {"summary": "Patched Summary for Persistence Test"}
            )
        except Exception as e:
            self.fail(f"Calendar patching failed: {e}")
        
        # Verify patch result has the new value
        self.assertEqual(patched_result["summary"], "Patched Summary for Persistence Test")
        self.assertEqual(patched_result["id"], cal_id)
        
        # MAIN TEST: Verify that the patch updates BOTH storage locations immediately
        # This is what we're actually testing - that our patch_calendar_metadata function
        # correctly updates both DB["calendar_list"] and DB["calendars"]
        self.assertEqual(
            DB["calendar_list"][cal_id]["summary"], 
            "Patched Summary for Persistence Test",
            "patch_calendar_metadata should update calendar_list storage"
        )
        self.assertEqual(
            DB["calendars"][cal_id]["summary"], 
            "Patched Summary for Persistence Test",
            "patch_calendar_metadata should update calendars storage"
        )
        
        # Verify retrieval also works
        retrieved = get_calendar_metadata(cal_id)
        self.assertEqual(retrieved["summary"], "Patched Summary for Persistence Test")
        
        # Clean up: restore original summary to avoid affecting other tests
        patch_calendar_metadata(
            cal_id, {"summary": original_summary}
        )

    # Edge Cases
    def test_patch_calendar_metadata_unicode_values(self):
        """Test patching with Unicode characters in field values."""
        cal_id = "test_calendar_unicode"
        # Create a test calendar
        create_secondary_calendar({
            "id": cal_id,
            "summary": "Original Summary",
            "timeZone": "UTC"
        })
        
        # Patch with Unicode values
        result = patch_calendar_metadata(
            cal_id, {
                "summary": "📅 Calendar with Emojis 🎉",
                "description": "Καλημέρα (Greek) - こんにちは (Japanese)"
            }
        )
        
        self.assertEqual(result["summary"], "📅 Calendar with Emojis 🎉")
        self.assertEqual(result["description"], "Καλημέρα (Greek) - こんにちは (Japanese)")

    def test_patch_calendar_metadata_long_field_values(self):
        """Test patching with very long field values."""
        cal_id = "test_calendar_long_values"
        # Create a test calendar
        create_secondary_calendar({
            "id": cal_id,
            "summary": "Original Summary",
            "timeZone": "UTC"
        })
        
        # Create very long strings
        long_summary = "A" * 1000
        long_description = "B" * 2000
        
        # Patch with long values
        result = patch_calendar_metadata(
            cal_id, {
                "summary": long_summary,
                "description": long_description
            }
        )
        
        self.assertEqual(result["summary"], long_summary)
        self.assertEqual(result["description"], long_description) 