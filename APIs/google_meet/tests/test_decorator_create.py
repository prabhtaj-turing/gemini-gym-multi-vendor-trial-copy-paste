import unittest
from typing import Dict, Any
from pydantic import BaseModel as PydanticBaseModel, ValidationError
import os

from google_meet.SimulationEngine.models import SpaceContentModel
from google_meet.SimulationEngine.custom_errors import InvalidSpaceNameError
from google_meet import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_meet.tests.common import reset_db
from google_meet import create_meeting_space

# --- Test Class for create_meeting_space ---
class TestCreateMeetingSpace(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset DB and error mode before each test."""
        reset_db()
        # Reset error mode to default
        if "OVERWRITE_ERROR_MODE" in os.environ:
            del os.environ["OVERWRITE_ERROR_MODE"]

    def test_create_space_success(self):
        """Test successful creation of a meeting space with valid inputs."""
        space_name = "MyTestSpace"
        space_content = {
            "meetingCode": "xyz-789",
            "meetingUri": "https://meet.example.com/xyz-789",
            "accessType": "PRIVATE"
        }
        result = create_meeting_space(space_name=space_name, space_content=space_content)
        self.assertEqual(result, {"message": f"Space {space_name} created successfully"})
        self.assertIn(space_name, DB["spaces"])
        self.assertEqual(DB["spaces"][space_name]["meetingCode"], "xyz-789")
        self.assertEqual(DB["spaces"][space_name]["meetingUri"], "https://meet.example.com/xyz-789")
        self.assertEqual(DB["spaces"][space_name]["accessType"], "PRIVATE")

    def test_invalid_space_name_type(self):
        """Test TypeError if space_name is not a string."""
        space_content = {"meetingCode": "a", "meetingUri": "b", "accessType": "c"}
        self.assert_error_behavior(
            func_to_call=create_meeting_space,
            expected_exception_type=TypeError,
            expected_message="space_name must be a string.",
            space_name=12345, # Invalid type
            space_content=space_content
        )

    def test_empty_space_name(self):
        """Test InvalidSpaceNameError if space_name is an empty string."""
        space_content = {"meetingCode": "a", "meetingUri": "b", "accessType": "c"}
        self.assert_error_behavior(
            func_to_call=create_meeting_space,
            expected_exception_type=InvalidSpaceNameError,
            expected_message="space_name cannot be empty or whitespace.",
            space_name="", # Empty string
            space_content=space_content
        )

    def test_whitespace_space_name(self):
        """Test InvalidSpaceNameError if space_name consists only of whitespace."""
        space_content = {"meetingCode": "a", "meetingUri": "b", "accessType": "c"}
        self.assert_error_behavior(
            func_to_call=create_meeting_space,
            expected_exception_type=InvalidSpaceNameError,
            expected_message="space_name cannot be empty or whitespace.",
            space_name="   ", # Whitespace only
            space_content=space_content
        )

    def test_invalid_space_content_type(self):
        """Test TypeError if space_content is not a dictionary."""
        self.assert_error_behavior(
            func_to_call=create_meeting_space,
            expected_exception_type=TypeError,
            expected_message="space_content must be a dictionary.",
            space_name="ValidSpaceName",
            space_content="this is not a dictionary" # Invalid type
        )

    def test_pydantic_validation_missing_meeting_code(self):
        """Test ValidationError if space_content is missing 'meetingCode'."""
        invalid_content = {
            # "meetingCode" is missing
            "meetingUri": "https://meet.example.com/valid",
            "accessType": "PUBLIC"
        }
        self.assert_error_behavior(
            func_to_call=create_meeting_space,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for SpaceContentModel\nmeetingCode\n  Field required [type=missing, input_value={'meetingUri': 'https://m... 'accessType': 'PUBLIC'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing",
            space_name="TestValidation",
            space_content=invalid_content
        )

    def test_pydantic_validation_invalid_type_meeting_code(self):
        """Test ValidationError if space_content 'meetingCode' has an invalid type."""
        invalid_content = {
            "meetingCode": 123, # Should be string
            "meetingUri": "https://meet.example.com/valid",
            "accessType": "PUBLIC"
        }
        self.assert_error_behavior(
            func_to_call=create_meeting_space,
            expected_exception_type=ValidationError,
            expected_message='1 validation error for SpaceContentModel\nmeetingCode\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type',
            space_name="TestValidation",
            space_content=invalid_content
        )

    def test_pydantic_validation_all_fields_invalid(self):
        """Test ValidationError if multiple fields in space_content are invalid/missing."""
        invalid_content = {
            "meetingCode": 123, # Invalid type
            # "meetingUri" is missing
            "accessType": True # Invalid type
        }
        self.assert_error_behavior(
            func_to_call=create_meeting_space,
            expected_exception_type=ValidationError,
            expected_message="3 validation errors for SpaceContentModel\nmeetingCode\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type\nmeetingUri\n  Field required [type=missing, input_value={'meetingCode': 123, 'accessType': True}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing\naccessType\n  Input should be a valid string [type=string_type, input_value=True, input_type=bool]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type", # Check start of message
            space_name="TestMultiValidation",
            space_content=invalid_content
        )

    def test_create_space_with_extra_fields_in_content(self):
        """Test successful creation even if space_content has extra fields (Pydantic default: ignore)."""
        space_name = "SpaceWithExtras"
        space_content = {
            "meetingCode": "extra-123",
            "meetingUri": "https://meet.example.com/extra-123",
            "accessType": "OPEN",
            "extraField1": "someValue",
            "anotherExtra": 12345
        }
        result = create_meeting_space(space_name=space_name, space_content=space_content)
        self.assertEqual(result, {"message": f"Space {space_name} created successfully"})
        self.assertIn(space_name, DB["spaces"])
        self.assertEqual(DB["spaces"][space_name]["meetingCode"], "extra-123")
        # Check that extra fields are not in the dumped model
        self.assertNotIn("extraField1", DB["spaces"][space_name])
        self.assertNotIn("anotherExtra", DB["spaces"][space_name])

    def test_db_not_initialized_error(self):
        """Test KeyError when DB['spaces'] is not properly initialized."""
        space_name = "TestSpace"
        space_content = {
            "meetingCode": "test-123",
            "meetingUri": "https://meet.example.com/test-123",
            "accessType": "PUBLIC"
        }
        
        # Temporarily remove 'spaces' from DB to simulate uninitialized structure
        original_spaces = None
        if "spaces" in DB:
            original_spaces = DB["spaces"]
            del DB["spaces"]
        
        try:
            self.assert_error_behavior(
                func_to_call=create_meeting_space,
                expected_exception_type=KeyError,
                expected_message="'spaces'",
                space_name=space_name,
                space_content=space_content
            )
        finally:
            # Restore DB structure to avoid affecting other tests
            if original_spaces is not None:
                DB["spaces"] = original_spaces
            else:
                DB["spaces"] = {}

    def test_error_dict_mode_type_error(self):
        """Test TypeError behavior when ERROR_MODE is 'error_dict'."""
        os.environ["OVERWRITE_ERROR_MODE"] = "error_dict"
        space_content = {"meetingCode": "a", "meetingUri": "b", "accessType": "c"}
        expected_msg = "space_name must be a string."
        
        self.assert_error_behavior(
            func_to_call=create_meeting_space,
            expected_exception_type=TypeError,
            expected_message=expected_msg,
            space_name=12345, # Invalid type
            space_content=space_content
        )
        
        # Also verify the returned dictionary structure directly for one case
        result = create_meeting_space(space_name=12345, space_content=space_content)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("exceptionType"), TypeError.__name__)
        self.assertEqual(result.get("message"), expected_msg)

if __name__ == "__main__":
    unittest.main()
