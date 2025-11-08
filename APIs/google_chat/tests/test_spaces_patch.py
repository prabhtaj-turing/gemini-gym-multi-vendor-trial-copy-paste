import unittest
from unittest.mock import patch
from pydantic import ValidationError

from google_chat.Spaces import patch as spaces_patch
from google_chat.SimulationEngine.custom_errors import (
    InvalidSpaceNameFormatError,
    SpaceNotFoundError,
    InvalidUpdateMaskFieldError,
    InvalidSpaceTypeTransitionError,
    UpdateRestrictedForSpaceTypeError,
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestSpacesPatchValidation(BaseTestCaseWithErrorHandler):
    """Test cases for spaces patch function validation and business logic."""

    def setUp(self):
        """Set up test data before each test."""
        global DB
        DB = {
            "Space": [
                {
                    "name": "spaces/SPACE1",
                    "spaceType": "SPACE",
                    "displayName": "Test Space",
                    "createTime": "2023-01-01T00:00:00Z",
                    "spaceDetails": {"description": "Original description"},
                    "accessSettings": {"audience": "audiences/default"}
                },
                {
                    "name": "spaces/GROUP1",
                    "spaceType": "GROUP_CHAT",
                    "createTime": "2023-01-01T00:00:00Z"
                },
                {
                    "name": "spaces/DM1",
                    "spaceType": "DIRECT_MESSAGE",
                    "createTime": "2023-01-01T00:00:00Z"
                }
            ],
            "Membership": [],
            "Message": []
        }

    @patch("google_chat.Spaces.DB", new_callable=lambda: DB)
    def test_valid_display_name_update(self, mock_db):
        """Test successful display name update for SPACE type."""
        result = spaces_patch(
            name="spaces/SPACE1",
            updateMask="display_name",
            space_updates={"displayName": "Updated Space Name"}
        )
        
        self.assertEqual(result["displayName"], "Updated Space Name")
        self.assertEqual(result["spaceType"], "SPACE")
        self.assertEqual(result["name"], "spaces/SPACE1")

    @patch("google_chat.Spaces.DB", new_callable=lambda: DB)
    def test_valid_space_details_update(self, mock_db):
        """Test successful space details update."""
        result = spaces_patch(
            name="spaces/SPACE1",
            updateMask="space_details",
            space_updates={
                "spaceDetails": {
                    "description": "New description",
                    "guidelines": "New guidelines"
                }
            }
        )
        
        self.assertEqual(result["spaceDetails"]["description"], "New description")
        self.assertEqual(result["spaceDetails"]["guidelines"], "New guidelines")

    @patch("google_chat.Spaces.DB", new_callable=lambda: DB)
    def test_valid_space_type_transition(self, mock_db):
        """Test successful GROUP_CHAT to SPACE transition."""
        result = spaces_patch(
            name="spaces/GROUP1",
            updateMask="space_type,display_name",
            space_updates={
                "spaceType": "SPACE",
                "displayName": "Converted Space"
            }
        )
        
        self.assertEqual(result["spaceType"], "SPACE")
        self.assertEqual(result["displayName"], "Converted Space")

    # Input validation tests
    def test_invalid_name_type(self):
        """Test TypeError for non-string name."""
        self.assert_error_behavior(
            func_to_call=spaces_patch,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=123,
            updateMask="display_name",
            space_updates={"displayName": "Test"}
        )

    def test_empty_name(self):
        """Test ValueError for empty name."""
        self.assert_error_behavior(
            func_to_call=spaces_patch,
            expected_exception_type=ValueError,
            expected_message="Argument 'name' cannot be empty.",
            name="",
            updateMask="display_name",
            space_updates={"displayName": "Test"}
        )

    def test_invalid_name_format(self):
        """Test InvalidSpaceNameFormatError for invalid name format."""
        self.assert_error_behavior(
            func_to_call=spaces_patch,
            expected_exception_type=InvalidSpaceNameFormatError,
            expected_message="Argument 'name' ('invalid/format') is not in the expected format 'spaces/{space}'.",
            name="invalid/format",
            updateMask="display_name",
            space_updates={"displayName": "Test"}
        )

    @patch("google_chat.Spaces.DB", new_callable=lambda: DB)
    def test_space_not_found(self, mock_db):
        """Test SpaceNotFoundError for non-existent space."""
        self.assert_error_behavior(
            func_to_call=spaces_patch,
            expected_exception_type=SpaceNotFoundError,
            expected_message="Space 'spaces/NONEXISTENT' not found.",
            name="spaces/NONEXISTENT",
            updateMask="display_name",
            space_updates={"displayName": "Test"}
        )

    @patch("google_chat.Spaces.DB", new_callable=lambda: DB)
    def test_display_name_update_restricted_for_group_chat(self, mock_db):
        """Test UpdateRestrictedForSpaceTypeError for display name update on GROUP_CHAT."""
        self.assert_error_behavior(
            func_to_call=spaces_patch,
            expected_exception_type=UpdateRestrictedForSpaceTypeError,
            expected_message="displayName update is only supported for spaces of type SPACE. Current space type: GROUP_CHAT",
            name="spaces/GROUP1",
            updateMask="display_name",
            space_updates={"displayName": "Test"}
        )

    @patch("google_chat.Spaces.DB", new_callable=lambda: DB)
    def test_invalid_space_type_transition_space_to_group(self, mock_db):
        """Test InvalidSpaceTypeTransitionError for invalid SPACE to GROUP_CHAT transition."""
        self.assert_error_behavior(
            func_to_call=spaces_patch,
            expected_exception_type=InvalidSpaceTypeTransitionError,
            expected_message="Invalid space type transition from 'SPACE' to 'GROUP_CHAT'. Only GROUP_CHAT -> SPACE transition is supported.",
            name="spaces/SPACE1",
            updateMask="space_type",
            space_updates={"spaceType": "GROUP_CHAT"}
        )

    def test_invalid_update_mask_field(self):
        """Test InvalidUpdateMaskFieldError for invalid field in updateMask."""
        self.assert_error_behavior(
            func_to_call=spaces_patch,
            expected_exception_type=InvalidUpdateMaskFieldError,
            expected_message="Invalid update mask field(s): invalid_field. Valid fields are: access_settings.audience, display_name, permission_settings, space_details, space_history_state, space_type",
            name="spaces/SPACE1",
            updateMask="invalid_field",
            space_updates={"displayName": "Test"}
        )

    def test_description_length_validation(self):
        """Test ValidationError for description exceeding 150 characters (handled by Pydantic)."""
        long_description = "a" * 151  # Exceeds 150 character limit
        self.assert_error_behavior(
            func_to_call=spaces_patch,
            expected_exception_type=ValidationError,
            expected_message="Space description cannot exceed 150 characters",
            name="spaces/SPACE1",
            updateMask="space_details",
            space_updates={"spaceDetails": {"description": long_description}}
        )


if __name__ == "__main__":
    unittest.main() 