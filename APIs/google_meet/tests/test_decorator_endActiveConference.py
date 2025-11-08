import unittest
from typing import Dict, Any

from google_meet.Spaces import endActiveConference
from google_meet.SimulationEngine.db import DB
from google_meet.SimulationEngine.custom_errors import SpaceNotFoundError

from common_utils.base_case import BaseTestCaseWithErrorHandler

# Alias for the function to be tested.
# In a real scenario, this would be: from your_module import endActiveConference
# For this self-contained example, we assign the refactored function to the alias.
end_active_conference_in_space = endActiveConference

class TestEndActiveConference(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state (DB) before each test."""
        # Reset DB to empty state
        DB.clear()
        DB.update({
            "conferenceRecords": {},
            "recordings": {},
            "transcripts": {},
            "entries": {},
            "participants": {},
            "participantSessions": {},
            "spaces": {
                "space_with_active_conf": {
                    "id": "space1",
                    "name": "Space With Active Conference",
                    "activeConference": {"id": "conf123", "details": "Ongoing meeting"}
                },
                "space_without_conf": {
                    "id": "space2",
                    "name": "Space Without Conference"
                },
                "another_space_with_conf": { # For testing modification isolation
                    "id": "space3",
                    "activeConference": {"id": "conf456"}
                }
            }
        })

    def test_valid_input_ends_conference_successfully(self):
        """Test ending an active conference when one exists."""
        space_name = "space_with_active_conf"
        result = end_active_conference_in_space(space_name)
        self.assertEqual(result, {"message": "Active conference ended"})
        self.assertNotIn("activeConference", DB["spaces"][space_name],
                         "activeConference field should be removed from the space.")
        # Ensure other spaces are not affected
        self.assertIn("activeConference", DB["spaces"]["another_space_with_conf"])


    def test_valid_input_no_active_conference_to_end(self):
        """Test ending a conference when no active conference exists in the space."""
        space_name = "space_without_conf"
        result = end_active_conference_in_space(space_name)
        self.assertEqual(result, {"message": "No active conference to end"})
        self.assertNotIn("activeConference", DB["spaces"][space_name],
                         "activeConference field should remain absent.")

    def test_valid_input_space_not_found(self):
        """Test attempting to end a conference in a non-existent space."""
        space_name = "non_existent_space"
        self.assert_error_behavior(
            func_to_call=end_active_conference_in_space,
            expected_exception_type=SpaceNotFoundError,
            expected_message='"Space \'non_existent_space\' not found"',
            name=space_name
        )

    def test_invalid_name_type_integer(self):
        """Test that providing an integer for 'name' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=end_active_conference_in_space,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=123
        )

    def test_invalid_name_type_list(self):
        """Test that providing a list for 'name' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=end_active_conference_in_space,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=["space_name"]
        )

    def test_invalid_name_type_none(self):
        """Test that providing None for 'name' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=end_active_conference_in_space,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=None
        )

    def test_empty_string_name_space_exists(self):
        """Test with an empty string name if the space "" exists and has a conference."""
        global DB
        DB["spaces"][""] = {"activeConference": {"id": "conf_empty"}}
        result = end_active_conference_in_space("")
        self.assertEqual(result, {"message": "Active conference ended"})
        self.assertNotIn("activeConference", DB["spaces"][""])

    def test_empty_string_name_space_not_found(self):
        """Test with an empty string name if the space "" does not exist."""
        self.assert_error_behavior(
            func_to_call=end_active_conference_in_space,
            expected_exception_type=SpaceNotFoundError,
            expected_message='"Space \'\' not found"',
            name=""
        )

# To run these tests (if saved as a .py file):
# python -m unittest your_file_name.py
