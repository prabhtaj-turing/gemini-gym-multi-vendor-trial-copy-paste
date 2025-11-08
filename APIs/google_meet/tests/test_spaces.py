import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler

from google_meet.tests.common import reset_db
from google_meet import Spaces
from google_meet import DB
from google_meet.SimulationEngine.custom_errors import SpaceNotFoundError, InvalidSpaceNameError, SpaceAlreadyExistsError


class TestSpaces(BaseTestCaseWithErrorHandler):
    """
    Test cases for the Spaces API.

    These tests verify the functionality of the spaces API, including:
    - Getting space details
    - Updating space details
    - Creating new spaces
    - Managing active conferences
    - Error handling for non-existent spaces
    """

    def setUp(self):
        """Set up a clean database state for testing."""
        reset_db()

    def test_spaces_get(self):
        """Test retrieving space details."""
        # Create a test space
        test_space = {"field1": "value1"}
        DB["spaces"]["test_space"] = test_space

        # Test getting an existing space
        result = Spaces.get("test_space")
        self.assertEqual(result, test_space)

        # The KeyError string representation has extra quotes added
        space_name = "nonexistent_space"
        expected_message = f'"Space with name \'{space_name}\' not found."'
        self.assert_error_behavior(
            func_to_call=Spaces.get,
            expected_exception_type=KeyError,
            expected_message=expected_message,
            name=space_name
        )

    def test_spaces_patch(self):
        """Test updating space details."""
        # Create a test space
        test_space = {"field1": "value1", "field2": "value2"}
        DB["spaces"]["test_space"] = test_space.copy()

        # Test updating an existing space
        update_mask = {"field1": "field2"}
        result = Spaces.patch("test_space", update_mask)
        self.assertEqual(result["field1"], "field2")
        self.assertEqual(DB["spaces"]["test_space"]["field1"], "field2")

        # Test updating a non-existent space
        self.assert_error_behavior(
            func_to_call=Spaces.patch,
            expected_exception_type=SpaceNotFoundError,
            expected_message="\"Space 'nonexistent_space' not found\"",
            name="nonexistent_space"
        )

        self.assert_error_behavior(
            func_to_call=Spaces.patch,
            expected_exception_type=InvalidSpaceNameError,
            expected_message="Space name cannot be empty or whitespace.",
            name=" "
        )

    def test_spaces_create(self):
        """Test creating a new space."""
        # Define test space content
        space_content = {
            "meetingCode": "abc-mnop-xyz",
            "meetingUri": "https://meet.google.com/abc-mnop-xyz",
            "accessType": "TRUSTED",
            "entryPointAccess": "ALL",
        }

        # Test creating a new space
        result = Spaces.create(space_name="space", space_content=space_content)
        self.assertIn("message", result)
        self.assertIn(list(DB["spaces"].keys())[0], result["message"])

        # Test creating a space that already exists
        self.assert_error_behavior(
            func_to_call=Spaces.create,
            expected_exception_type=SpaceAlreadyExistsError,
            expected_message="Space 'space' already exists.",
            space_name="space",
            space_content=space_content,
        )

    def test_spaces_endActiveConference(self):
        """Test ending an active conference in a space."""
        # Create a test space with an active conference
        test_space = {"activeConference": "conf_id"}
        DB["spaces"]["test_space"] = test_space.copy()

        # Test ending an active conference
        result = Spaces.endActiveConference("test_space")
        self.assertEqual(result, {"message": "Active conference ended"})
        self.assertNotIn("activeConference", DB["spaces"]["test_space"])

        # Test ending when no active conference exists
        result = Spaces.endActiveConference("test_space")
        self.assertEqual(result, {"message": "No active conference to end"})

        # Test ending conference in non-existent space
        self.assert_error_behavior(
            func_to_call=Spaces.endActiveConference,
            expected_exception_type=SpaceNotFoundError,
            expected_message='"Space \'nonexistent_space\' not found"',
            name="nonexistent_space"
        )


if __name__ == "__main__":
    unittest.main()
