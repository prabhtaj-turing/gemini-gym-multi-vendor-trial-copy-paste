import unittest
from unittest.mock import patch

from google_chat.Spaces.SpaceEvents import get
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_chat.SimulationEngine.custom_errors import (
    InvalidSpaceEventNameFormatError,
    SpaceEventNotFoundError,
    UserNotMemberError,
)
from google_chat.SimulationEngine.db import DB, CURRENT_USER_ID


class TestSpaceEventsGet(BaseTestCaseWithErrorHandler):
    """Test cases for the SpaceEvents.get function with comprehensive validation and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()

        # Reset database
        DB.clear()
        DB.update({"SpaceEvent": [], "Membership": [], "Space": []})

        # Set up current user
        global CURRENT_USER_ID
        CURRENT_USER_ID.update({"id": "users/USER123"})

        # Sample space event for testing
        self.sample_space_event = {
            "name": "spaces/TEST_SPACE/spaceEvents/EVENT123",
            "eventTime": "2023-10-15T10:30:00Z",
            "eventType": "google.workspace.chat.message.v1.created",
            "messageCreatedEventData": {
                "message": {
                    "name": "spaces/TEST_SPACE/messages/MSG789",
                    "text": "Hello, world!",
                    "createTime": "2023-10-15T10:30:00Z",
                    "sender": {
                        "name": "users/USER123",
                        "displayName": "John Doe",
                        "type": "HUMAN",
                    },
                }
            },
        }

        # Sample membership
        self.sample_membership = {
            "name": "spaces/TEST_SPACE/members/users/USER123",
            "state": "JOINED",
            "role": "ROLE_MEMBER",
            "member": {"name": "users/USER123", "type": "HUMAN"},
        }

    # --- Input Validation Tests ---

    def test_name_type_validation(self):
        """Test that non-string name raises TypeError."""
        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=123,
        )

        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=None,
        )

        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=[],
        )

    def test_name_empty_validation(self):
        """Test that empty string name raises ValueError."""
        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=ValueError,
            expected_message="Argument 'name' cannot be an empty string.",
            name="",
        )

    def test_name_format_validation_invalid_prefix(self):
        """Test that name without 'spaces/' prefix raises InvalidSpaceEventNameFormatError."""
        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=InvalidSpaceEventNameFormatError,
            expected_message="Argument 'name' ('invalid/format') is not in the expected format 'spaces/{space}/spaceEvents/{spaceEvent}'.",
            name="invalid/format",
        )

    def test_name_format_validation_missing_spaceEvents(self):
        """Test that name without 'spaceEvents' raises InvalidSpaceEventNameFormatError."""
        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=InvalidSpaceEventNameFormatError,
            expected_message="Argument 'name' ('spaces/TEST_SPACE/messages/MSG123') is not in the expected format 'spaces/{space}/spaceEvents/{spaceEvent}'.",
            name="spaces/TEST_SPACE/messages/MSG123",
        )

    def test_name_format_validation_missing_event_id(self):
        """Test that name without event ID raises InvalidSpaceEventNameFormatError."""
        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=InvalidSpaceEventNameFormatError,
            expected_message="Argument 'name' ('spaces/TEST_SPACE/spaceEvents/') is not in the expected format 'spaces/{space}/spaceEvents/{spaceEvent}'.",
            name="spaces/TEST_SPACE/spaceEvents/",
        )

    def test_name_format_validation_extra_segments(self):
        """Test that name with extra segments raises InvalidSpaceEventNameFormatError."""
        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=InvalidSpaceEventNameFormatError,
            expected_message="Argument 'name' ('spaces/TEST_SPACE/spaceEvents/EVENT123/extra') is not in the expected format 'spaces/{space}/spaceEvents/{spaceEvent}'.",
            name="spaces/TEST_SPACE/spaceEvents/EVENT123/extra",
        )

    def test_name_format_validation_missing_space_id(self):
        """Test that name without space ID raises InvalidSpaceEventNameFormatError."""
        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=InvalidSpaceEventNameFormatError,
            expected_message="Argument 'name' ('spaces//spaceEvents/EVENT123') is not in the expected format 'spaces/{space}/spaceEvents/{spaceEvent}'.",
            name="spaces//spaceEvents/EVENT123",
        )

    # --- Access Control Tests ---

    def test_no_current_user_id(self):
        """Test that missing current user ID raises UserNotMemberError."""
        # Clear current user ID
        CURRENT_USER_ID.clear()

        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=UserNotMemberError,
            expected_message="Authentication required to access space events.",
            name="spaces/TEST_SPACE/spaceEvents/EVENT123",
        )

    def test_current_user_id_none(self):
        """Test that None current user ID raises UserNotMemberError."""
        CURRENT_USER_ID.update({"id": None})

        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=UserNotMemberError,
            expected_message="Authentication required to access space events.",
            name="spaces/TEST_SPACE/spaceEvents/EVENT123",
        )

    def test_user_not_member_of_space(self):
        """Test that user not being a member raises UserNotMemberError."""
        # Set up current user but no membership
        CURRENT_USER_ID.update({"id": "users/USER123"})

        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=UserNotMemberError,
            expected_message="User must be a member of the space 'spaces/TEST_SPACE' to access its events.",
            name="spaces/TEST_SPACE/spaceEvents/EVENT123",
        )

    def test_user_member_of_different_space(self):
        """Test that membership in different space doesn't grant access."""
        # Add membership to different space
        DB["Membership"].append(
            {
                "name": "spaces/OTHER_SPACE/members/users/USER123",
                "state": "JOINED",
                "role": "ROLE_MEMBER",
                "member": {"name": "users/USER123", "type": "HUMAN"},
            }
        )

        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=UserNotMemberError,
            expected_message="User must be a member of the space 'spaces/TEST_SPACE' to access its events.",
            name="spaces/TEST_SPACE/spaceEvents/EVENT123",
        )

    # --- Space Event Retrieval Tests ---

    def test_space_event_not_found(self):
        """Test that non-existent space event raises SpaceEventNotFoundError."""
        # Add membership but no space event
        DB["Membership"].append(self.sample_membership)

        self.assert_error_behavior(
            func_to_call=get,
            expected_exception_type=SpaceEventNotFoundError,
            expected_message="Space event 'spaces/TEST_SPACE/spaceEvents/NONEXISTENT' not found.",
            name="spaces/TEST_SPACE/spaceEvents/NONEXISTENT",
        )

    def test_successful_space_event_retrieval(self):
        """Test successful space event retrieval."""
        # Add both membership and space event
        DB["Membership"].append(self.sample_membership)
        DB["SpaceEvent"].append(self.sample_space_event)

        result = get("spaces/TEST_SPACE/spaceEvents/EVENT123")

        self.assertEqual(result, self.sample_space_event)
        self.assertEqual(result["name"], "spaces/TEST_SPACE/spaceEvents/EVENT123")
        self.assertEqual(
            result["eventType"], "google.workspace.chat.message.v1.created"
        )
        self.assertIn("messageCreatedEventData", result)

    def test_multiple_space_events_correct_one_returned(self):
        """Test that the correct space event is returned when multiple exist."""
        # Add membership
        DB["Membership"].append(self.sample_membership)

        # Add multiple space events
        event1 = {
            "name": "spaces/TEST_SPACE/spaceEvents/EVENT1",
            "eventTime": "2023-10-15T10:00:00Z",
            "eventType": "google.workspace.chat.message.v1.created",
        }
        event2 = {
            "name": "spaces/TEST_SPACE/spaceEvents/EVENT2",
            "eventTime": "2023-10-15T11:00:00Z",
            "eventType": "google.workspace.chat.message.v1.updated",
        }
        event3 = {
            "name": "spaces/OTHER_SPACE/spaceEvents/EVENT3",
            "eventTime": "2023-10-15T12:00:00Z",
            "eventType": "google.workspace.chat.message.v1.deleted",
        }

        DB["SpaceEvent"].extend([event1, event2, event3])

        # Should return event2
        result = get("spaces/TEST_SPACE/spaceEvents/EVENT2")
        self.assertEqual(result, event2)
        self.assertEqual(result["name"], "spaces/TEST_SPACE/spaceEvents/EVENT2")
        self.assertEqual(
            result["eventType"], "google.workspace.chat.message.v1.updated"
        )

    # --- Different Event Types Tests ---

    def test_membership_created_event(self):
        """Test retrieval of membership created event."""
        DB["Membership"].append(self.sample_membership)

        membership_event = {
            "name": "spaces/TEST_SPACE/spaceEvents/MEMBERSHIP_EVENT",
            "eventTime": "2023-10-15T10:30:00Z",
            "eventType": "google.workspace.chat.membership.v1.created",
            "membershipCreatedEventData": {
                "membership": {
                    "name": "spaces/TEST_SPACE/members/users/NEW_USER",
                    "state": "INVITED",
                    "role": "ROLE_MEMBER",
                    "member": {"name": "users/NEW_USER", "type": "HUMAN"},
                }
            },
        }

        DB["SpaceEvent"].append(membership_event)

        result = get("spaces/TEST_SPACE/spaceEvents/MEMBERSHIP_EVENT")
        self.assertEqual(result, membership_event)
        self.assertIn("membershipCreatedEventData", result)

    def test_reaction_created_event(self):
        """Test retrieval of reaction created event."""
        DB["Membership"].append(self.sample_membership)

        reaction_event = {
            "name": "spaces/TEST_SPACE/spaceEvents/REACTION_EVENT",
            "eventTime": "2023-10-15T10:30:00Z",
            "eventType": "google.workspace.chat.reaction.v1.created",
            "reactionCreatedEventData": {
                "reaction": {
                    "name": "spaces/TEST_SPACE/messages/MSG123/reactions/REACTION1",
                    "emoji": {"unicode": "👍"},
                    "user": {"name": "users/USER123", "type": "HUMAN"},
                }
            },
        }

        DB["SpaceEvent"].append(reaction_event)

        result = get("spaces/TEST_SPACE/spaceEvents/REACTION_EVENT")
        self.assertEqual(result, reaction_event)
        self.assertIn("reactionCreatedEventData", result)

    def test_space_updated_event(self):
        """Test retrieval of space updated event."""
        DB["Membership"].append(self.sample_membership)

        space_event = {
            "name": "spaces/TEST_SPACE/spaceEvents/SPACE_EVENT",
            "eventTime": "2023-10-15T10:30:00Z",
            "eventType": "google.workspace.chat.space.v1.updated",
            "spaceUpdatedEventData": {
                "space": {
                    "name": "spaces/TEST_SPACE",
                    "displayName": "Updated Test Space",
                    "spaceType": "SPACE",
                }
            },
        }

        DB["SpaceEvent"].append(space_event)

        result = get("spaces/TEST_SPACE/spaceEvents/SPACE_EVENT")
        self.assertEqual(result, space_event)
        self.assertIn("spaceUpdatedEventData", result)

    # --- Edge Cases ---

    def test_complex_space_name(self):
        """Test with complex space ID."""
        complex_membership = {
            "name": "spaces/SPACE_WITH_UNDERSCORES_123/members/users/USER123",
            "state": "JOINED",
            "role": "ROLE_MEMBER",
            "member": {"name": "users/USER123", "type": "HUMAN"},
        }

        complex_event = {
            "name": "spaces/SPACE_WITH_UNDERSCORES_123/spaceEvents/COMPLEX_EVENT_456",
            "eventTime": "2023-10-15T10:30:00Z",
            "eventType": "google.workspace.chat.message.v1.created",
        }

        DB["Membership"].append(complex_membership)
        DB["SpaceEvent"].append(complex_event)

        result = get("spaces/SPACE_WITH_UNDERSCORES_123/spaceEvents/COMPLEX_EVENT_456")
        self.assertEqual(result, complex_event)

    def test_empty_space_event_data(self):
        """Test with minimal space event data."""
        DB["Membership"].append(self.sample_membership)

        minimal_event = {
            "name": "spaces/TEST_SPACE/spaceEvents/MINIMAL_EVENT",
            "eventTime": "2023-10-15T10:30:00Z",
            "eventType": "google.workspace.chat.message.v1.deleted",
        }

        DB["SpaceEvent"].append(minimal_event)

        result = get("spaces/TEST_SPACE/spaceEvents/MINIMAL_EVENT")
        self.assertEqual(result, minimal_event)
        self.assertEqual(len(result), 3)  # Only name, eventTime, eventType

    def test_membership_with_different_states(self):
        """Test access with different membership states."""
        # Test with INVITED state
        invited_membership = {
            "name": "spaces/TEST_SPACE/members/users/USER123",
            "state": "INVITED",
            "role": "ROLE_MEMBER",
            "member": {"name": "users/USER123", "type": "HUMAN"},
        }

        DB["Membership"].append(invited_membership)
        DB["SpaceEvent"].append(self.sample_space_event)

        result = get("spaces/TEST_SPACE/spaceEvents/EVENT123")
        self.assertEqual(result, self.sample_space_event)

    def test_membership_with_manager_role(self):
        """Test access with ROLE_MANAGER."""
        manager_membership = {
            "name": "spaces/TEST_SPACE/members/users/USER123",
            "state": "JOINED",
            "role": "ROLE_MANAGER",
            "member": {"name": "users/USER123", "type": "HUMAN"},
        }

        DB["Membership"].append(manager_membership)
        DB["SpaceEvent"].append(self.sample_space_event)

        result = get("spaces/TEST_SPACE/spaceEvents/EVENT123")
        self.assertEqual(result, self.sample_space_event)

    def test_different_user_with_membership(self):
        """Test with different user who has membership."""
        # Change current user
        CURRENT_USER_ID.update({"id": "users/OTHER_USER"})

        # Add membership for the new user
        other_membership = {
            "name": "spaces/TEST_SPACE/members/users/OTHER_USER",
            "state": "JOINED",
            "role": "ROLE_MEMBER",
            "member": {"name": "users/OTHER_USER", "type": "HUMAN"},
        }

        DB["Membership"].append(other_membership)
        DB["SpaceEvent"].append(self.sample_space_event)

        result = get("spaces/TEST_SPACE/spaceEvents/EVENT123")
        self.assertEqual(result, self.sample_space_event)


if __name__ == "__main__":
    unittest.main()
