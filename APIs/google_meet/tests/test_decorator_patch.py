import unittest
from pydantic import ValidationError
from google_meet.Spaces import patch
import sys
import os
from common_utils.base_case import BaseTestCaseWithErrorHandler
# Add the parent directory to sys.path to allow importing the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google_meet import DB
from google_meet.SimulationEngine.custom_errors import SpaceNotFoundError

update_meeting_space = patch

class TestUpdateMeetingSpace(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state before each test."""
        DB.clear()
        DB.update({
            "spaces": {
                "space_123": {
                    "id": "s123",
                    "name": "Original Space Name",
                    "meetingCode": "OLD-CODE",
                    "meetingUri": "https://example.com/meet/old",
                    "accessType": "TRUSTED",
                    "entryPointAccess": "ALL",
                    "customField": "original_value"
                }
            },
            "conferenceRecords": {},
            "recordings": {},
            "transcripts": {},
            "entries": {},
            "participants": {},
            "participantSessions": {},
        })

    def test_valid_update_with_mask(self):
        """Test successful update with a valid update_mask."""
        valid_mask = {
            "meetingCode": "NEW-CODE",
            "accessType": "RESTRICTED",
            "newCustomField": "new_value"
        }
        result = update_meeting_space(name="space_123", update_mask=valid_mask)
        
        self.assertNotIn("error", result)
        self.assertEqual(result["id"], "s123") # Unchanged
        self.assertEqual(result["meetingCode"], "NEW-CODE") # Updated
        self.assertEqual(result["accessType"], "RESTRICTED") # Updated
        self.assertEqual(result["newCustomField"], "new_value") # Added
        self.assertEqual(DB["spaces"]["space_123"]["meetingCode"], "NEW-CODE")

    def test_valid_update_no_mask(self):
        """Test successful call with no update_mask (mask is None)."""
        result = update_meeting_space(name="space_123", update_mask=None)
        self.assertNotIn("error", result)
        self.assertEqual(result["meetingCode"], "OLD-CODE") # Should remain unchanged
        self.assertEqual(DB["spaces"]["space_123"]["meetingCode"], "OLD-CODE")

    def test_invalid_name_type(self):
        """Test that providing a non-string name raises TypeError."""
        self.assert_error_behavior(
            func_to_call=update_meeting_space,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=12345,
            update_mask={"meetingCode": "ANY-CODE"}
        )

    def test_update_mask_not_a_dictionary(self):
        """Test that providing a non-dict update_mask (when not None) raises TypeError."""
        self.assert_error_behavior(
            func_to_call=update_meeting_space,
            expected_exception_type=TypeError,
            expected_message="Argument 'update_mask' must be a dictionary if provided.",
            name="space_123",
            update_mask="not_a_dict"
        )

    def test_update_mask_invalid_known_field_type(self):
        """Test update_mask with a known field having an incorrect data type."""
        invalid_mask = {"meetingCode": 12345} # Should be string
        # Pydantic's error message for type mismatch can be quite detailed.
        # We'll match part of it: "Input should be a valid string"
        self.assert_error_behavior(
            func_to_call=update_meeting_space,
            expected_exception_type=ValidationError,
            expected_message='1 validation error for SpaceUpdateMaskModel\nmeetingCode\n  Input should be a valid string [type=string_type, input_value=12345, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type',
            name="space_123",
            update_mask=invalid_mask
        )

    def test_update_mask_valid_known_field_and_extra_fields(self):
        """Test update_mask with valid known fields and additional arbitrary fields."""
        valid_mask_with_extras = {
            "meetingUri": "https://example.com/meet/new_uri", # Known field
            "customData": {"key": "value"}, # Extra field
            "anotherExtra": 12345 # Extra field
        }
        result = update_meeting_space(name="space_123", update_mask=valid_mask_with_extras)
        self.assertNotIn("error", result)
        self.assertEqual(result["meetingUri"], "https://example.com/meet/new_uri")
        self.assertEqual(result["customData"], {"key": "value"})
        self.assertEqual(result["anotherExtra"], 12345)
        self.assertEqual(DB["spaces"]["space_123"]["meetingUri"], "https://example.com/meet/new_uri")

    def test_space_not_found(self):
        """Test behavior when the specified space name does not exist."""
        self.assert_error_behavior(
            func_to_call=update_meeting_space,
            expected_exception_type=SpaceNotFoundError,
            expected_message="\"Space 'non_existent_space' not found\"",
            name="non_existent_space",
            update_mask={"meetingCode": "ANY"}
        )

    def test_empty_update_mask(self):
        """Test with an empty dictionary for update_mask."""
        original_space = DB["spaces"]["space_123"].copy()
        result = update_meeting_space(name="space_123", update_mask={})
        self.assertNotIn("error", result)
        # Ensure no fields were changed
        self.assertEqual(result, original_space)
        self.assertEqual(DB["spaces"]["space_123"], original_space)

    def test_update_mask_with_none_value_for_optional_field(self):
        """Test update_mask where an optional field is explicitly set to None."""
        # Assuming 'meetingCode' is Optional[str] in SpaceUpdateMaskModel,
        # Pydantic validation will pass `None` as a valid value.
        # The core logic will then update the field to `None`.
        mask_with_none = {"meetingCode": None}
        result = update_meeting_space(name="space_123", update_mask=mask_with_none)
        self.assertNotIn("error", result)
        self.assertIsNone(result["meetingCode"])
        self.assertIsNone(DB["spaces"]["space_123"]["meetingCode"])

# To run these tests (if this script is executed directly):
# if __name__ == '__main__':
#     unittest.main(argv=['first-arg-is-ignored'], exit=False)