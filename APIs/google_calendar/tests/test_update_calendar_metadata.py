from pydantic import ValidationError

from ..SimulationEngine.db import DB
from .. import create_secondary_calendar, update_calendar_metadata
from ..SimulationEngine.custom_errors import ResourceNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUpdateCalendarMetadata(BaseTestCaseWithErrorHandler):
    def setUp(self):
        DB.clear()
        DB.update({
            "acl_rules": {},
            "calendar_list": {},
            "calendars": {},
            "channels": {},
            "colors": {"calendar": {}, "event": {}},
            "events": {},
        })
        # seed defaults similar to main suite
        primary_cal = {
            "id": "my_primary_calendar",
            "summary": "My Primary Calendar",
            "description": "Default primary calendar",
            "timeZone": "UTC",
            "primary": True,
        }
        secondary_cal = {
            "id": "secondary",
            "summary": "Secondary Calendar",
            "description": "Secondary calendar",
            "timeZone": "UTC",
            "primary": False,
        }
        DB["calendar_list"]["my_primary_calendar"] = primary_cal
        DB["calendar_list"]["secondary"] = secondary_cal
        DB["calendars"]["my_primary_calendar"] = primary_cal.copy()
        DB["calendars"]["secondary"] = secondary_cal.copy()

    def test_transactional_integrity(self):
        created = create_secondary_calendar({
            "summary": "Test Calendar",
            "description": "Test description",
            "timeZone": "America/New_York",
        })
        cal_id = created["id"]

        # ensure present in both stores
        if cal_id not in DB["calendar_list"]:
            DB["calendar_list"][cal_id] = created.copy()
        if cal_id not in DB["calendars"]:
            DB["calendars"][cal_id] = created.copy()

        updated = update_calendar_metadata(calendarId=cal_id, resource={
            "summary": "Updated Calendar",
            "description": "Updated description",
            "timeZone": "Europe/London",
        })

        assert updated["summary"] == "Updated Calendar"
        assert updated["description"] == "Updated description"
        assert updated["timeZone"] == "Europe/London"

        assert DB["calendar_list"].get(cal_id, {}).get("summary") == "Updated Calendar"
        assert DB["calendars"].get(cal_id, {}).get("summary") == "Updated Calendar"

    def test_mass_assignment_prevention(self):
        created = create_secondary_calendar({
            "summary": "Test Calendar",
            "description": "Test description",
            "timeZone": "America/New_York",
        })
        cal_id = created["id"]

        try:
            update_calendar_metadata(calendarId=cal_id, resource={
                "summary": "Updated Calendar",
                "primary": True,
            })
            raise AssertionError("ValidationError not raised")
        except ValidationError as e:
            assert "Extra inputs are not permitted" in str(e)

    def test_invalid_summary_type(self):
        created = create_secondary_calendar({
            "summary": "Test Calendar",
            "description": "Test description",
            "timeZone": "America/New_York",
        })
        cal_id = created["id"]

        try:
            update_calendar_metadata(calendarId=cal_id, resource={"summary": 123})
            raise AssertionError("ValidationError not raised")
        except ValidationError as e:
            assert "Input should be a valid string" in str(e)

    def test_empty_summary(self):
        created = create_secondary_calendar({
            "summary": "Test Calendar",
            "description": "Test description",
            "timeZone": "America/New_York",
        })
        cal_id = created["id"]

        try:
            update_calendar_metadata(calendarId=cal_id, resource={"summary": ""})
            raise AssertionError("ValidationError not raised")
        except ValidationError as e:
            assert "Summary cannot be empty" in str(e)

    def test_invalid_timezone(self):
        created = create_secondary_calendar({
            "summary": "Test Calendar",
            "description": "Test description",
            "timeZone": "America/New_York",
        })
        cal_id = created["id"]

        try:
            update_calendar_metadata(calendarId=cal_id, resource={"summary": "Updated Calendar", "timeZone": "Invalid/Timezone"})
            raise AssertionError("ValidationError not raised")
        except ValidationError as e:
            assert "Invalid IANA time zone: 'Invalid/Timezone'. Must be a valid IANA time zone" in str(e)

    def test_calendar_validation_uses_calendars_not_calendar_list(self):
        """Test that update_calendar_metadata validates against DB['calendars'] not DB['calendar_list'].
        
        This test verifies the fix for bug #1056 where the function was incorrectly
        validating against calendar_list instead of calendars.
        """
        # Create a calendar that exists in calendar_list but NOT in calendars
        test_cal_id = "test_calendar_validation"
        calendar_data = {
            "id": test_cal_id,
            "summary": "Test Calendar",
            "description": "Test description",
            "timeZone": "UTC",
            "primary": False
        }
        
        # Add to calendar_list but NOT to calendars
        DB["calendar_list"][test_cal_id] = calendar_data.copy()
        # Intentionally NOT adding to DB["calendars"]
        
        # This should fail because the calendar doesn't exist in DB["calendars"]
        self.assert_error_behavior(
            func_to_call=lambda: update_calendar_metadata(calendarId=test_cal_id, resource={
                "summary": "Updated Calendar"
            }),
            expected_exception_type=ResourceNotFoundError,
            expected_message=f"Calendar '{test_cal_id}' not found."
        )
        
        # Now add the calendar to DB["calendars"] and it should work
        DB["calendars"][test_cal_id] = calendar_data.copy()
        
        # This should now succeed
        result = update_calendar_metadata(calendarId=test_cal_id, resource={
            "summary": "Updated Calendar"
        })
        
        assert result["summary"] == "Updated Calendar"
        assert result["id"] == test_cal_id


