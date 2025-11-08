import unittest
import sys
import os

sys.path.append("APIs")

from google_chat.SimulationEngine.db import DB, CURRENT_USER_ID
from google_chat.SimulationEngine.custom_errors import (
    InvalidSpaceParentFormatError, InvalidFilterFormatError, InvalidEventTypeError,
    InvalidTimeFormatError, SpaceNotFoundError, InvalidPageSizeError, InvalidPageTokenError,
    UserNotMemberError
)
from google_chat.Spaces.SpaceEvents import list


DEFAULT_FILTER = (
    'event_types:"google.workspace.chat.message.v1.created" OR '
    'event_types:"google.workspace.chat.message.v1.updated" OR '
    'event_types:"google.workspace.chat.membership.v1.created"'
)


class TestSpaceEventsList(unittest.TestCase):
    
    def setUp(self):
        """Set up test data before each test"""
        DB.clear()
        DB.update({
            "User": [
                {"name": "users/USER123", "displayName": "Test User"},
                {"name": "users/USER456", "displayName": "Other User"}
            ],
            "Space": [
                {"name": "spaces/TEST_SPACE", "displayName": "Test Space"},
                {"name": "spaces/OTHER_SPACE", "displayName": "Other Space"}
            ],
            "Membership": [
                {"name": "spaces/TEST_SPACE/members/users/USER123", "role": "ROLE_MEMBER"},
                {"name": "spaces/OTHER_SPACE/members/users/USER456", "role": "ROLE_MEMBER"}
            ],
            "SpaceEvent": [
                {
                    "name": "spaces/TEST_SPACE/spaceEvents/1",
                    "eventTime": "2023-08-23T19:20:33+00:00",
                    "eventType": "google.workspace.chat.message.v1.created",
                    "messageCreatedEventData": {"message": {"text": "Hello"}}
                },
                {
                    "name": "spaces/TEST_SPACE/spaceEvents/2",
                    "eventTime": "2023-08-23T20:30:00+00:00",
                    "eventType": "google.workspace.chat.message.v1.updated",
                    "messageUpdatedEventData": {"message": {"text": "Updated"}}
                },
                {
                    "name": "spaces/TEST_SPACE/spaceEvents/3",
                    "eventTime": "2023-08-24T10:15:00+00:00",
                    "eventType": "google.workspace.chat.membership.v1.created",
                    "membershipCreatedEventData": {"membership": {"role": "ROLE_MEMBER"}}
                },
                {
                    "name": "spaces/OTHER_SPACE/spaceEvents/1",
                    "eventTime": "2023-08-23T19:20:33+00:00",
                    "eventType": "google.workspace.chat.message.v1.created",
                    "messageCreatedEventData": {"message": {"text": "Other space"}}
                }
            ]
        })
        
        # Set current user
        CURRENT_USER_ID.clear()
        CURRENT_USER_ID.update({"id": "users/USER123"})
    
    def tearDown(self):
        """Clean up after each test"""
        DB.clear()
        CURRENT_USER_ID.clear()
    
    # --- Input Validation Tests ---
    
    def test_parent_type_validation(self):
        """Test that parent must be a string"""
        with self.assertRaises(TypeError) as context:
            list(123, filter=DEFAULT_FILTER)
        self.assertIn("Argument 'parent' must be a string", str(context.exception))
    
    def test_parent_empty_validation(self):
        """Test that parent cannot be empty"""
        with self.assertRaises(ValueError) as context:
            list("", filter=DEFAULT_FILTER)
        self.assertIn("Argument 'parent' cannot be an empty string", str(context.exception))
    
    def test_parent_format_validation(self):
        """Test parent format validation"""
        # Missing spaces/ prefix
        with self.assertRaises(InvalidSpaceParentFormatError) as context:
            list("TEST_SPACE", filter=DEFAULT_FILTER)
        self.assertIn("not in the expected format 'spaces/{space}'", str(context.exception))
        
        # Extra segments
        with self.assertRaises(InvalidSpaceParentFormatError) as context:
            list("spaces/TEST_SPACE/extra", filter=DEFAULT_FILTER)
        self.assertIn("not in the expected format 'spaces/{space}'", str(context.exception))
        
        # Empty space ID
        with self.assertRaises(InvalidSpaceParentFormatError) as context:
            list("spaces/", filter=DEFAULT_FILTER)
        self.assertIn("not in the expected format 'spaces/{space}'", str(context.exception))
    
    def test_pagesize_type_validation(self):
        """Test that pageSize must be an integer"""
        with self.assertRaises(TypeError) as context:
            list("spaces/TEST_SPACE", pageSize="10", filter=DEFAULT_FILTER)
        self.assertIn("Argument 'pageSize' must be an integer", str(context.exception))
    
    def test_pagesize_range_validation(self):
        """Test pageSize range validation"""
        # Too small
        with self.assertRaises(InvalidPageSizeError) as context:
            list("spaces/TEST_SPACE", pageSize=0, filter=DEFAULT_FILTER)
        self.assertIn("must be between 1 and 1000", str(context.exception))
        
        # Too large
        with self.assertRaises(InvalidPageSizeError) as context:
            list("spaces/TEST_SPACE", pageSize=1001, filter=DEFAULT_FILTER)
        self.assertIn("must be between 1 and 1000", str(context.exception))
    
    def test_pagetoken_type_validation(self):
        """Test that pageToken must be a string"""
        with self.assertRaises(TypeError) as context:
            list("spaces/TEST_SPACE", pageToken=123, filter=DEFAULT_FILTER)
        self.assertIn("Argument 'pageToken' must be a string", str(context.exception))
    
    def test_pagetoken_empty_validation(self):
        """Test that pageToken cannot be empty"""
        with self.assertRaises(ValueError) as context:
            list("spaces/TEST_SPACE", pageToken="", filter=DEFAULT_FILTER)
        self.assertIn("Argument 'pageToken' cannot be an empty string", str(context.exception))
    
    def test_filter_type_validation(self):
        """Test that filter must be a string"""
        with self.assertRaises(TypeError) as context:
            list("spaces/TEST_SPACE", filter=123)
        self.assertIn("Argument 'filter' must be a string", str(context.exception))
    
    def test_filter_empty_validation(self):
        """Test that filter cannot be empty"""
        with self.assertRaises(ValueError) as context:
            list("spaces/TEST_SPACE", filter="")
        self.assertIn("Argument 'filter' cannot be an empty string", str(context.exception))
    
    # --- Access Control Tests ---
    
    def test_no_current_user_id(self):
        """Test error when no current user ID is available"""
        CURRENT_USER_ID.clear()
        
        with self.assertRaises(UserNotMemberError) as context:
            list("spaces/TEST_SPACE", filter=DEFAULT_FILTER)
        self.assertIn("Authentication required to access space events", str(context.exception))
    
    def test_current_user_id_none(self):
        """Test error when current user ID is None"""
        CURRENT_USER_ID.clear()
        CURRENT_USER_ID.update({"id": None})
        
        with self.assertRaises(UserNotMemberError) as context:
            list("spaces/TEST_SPACE", filter=DEFAULT_FILTER)
        self.assertIn("Authentication required to access space events", str(context.exception))
    
    def test_user_not_member_of_space(self):
        """Test error when user is not a member of the space"""
        with self.assertRaises(UserNotMemberError) as context:
            list("spaces/OTHER_SPACE", filter=DEFAULT_FILTER)
        self.assertIn("User must be a member of the space", str(context.exception))
    
    def test_user_member_of_different_space(self):
        """Test access control for different spaces"""
        # USER123 is not a member of OTHER_SPACE
        with self.assertRaises(UserNotMemberError) as context:
            list("spaces/OTHER_SPACE", filter=DEFAULT_FILTER)
        self.assertIn("User must be a member of the space 'spaces/OTHER_SPACE'", str(context.exception))
    
    # --- Space Existence Tests ---
    
    def test_space_not_found(self):
        """Test error when space doesn't exist"""
        with self.assertRaises(SpaceNotFoundError) as context:
            list("spaces/NONEXISTENT_SPACE", filter=DEFAULT_FILTER)
        self.assertIn("Space 'spaces/NONEXISTENT_SPACE' not found", str(context.exception))
    
    # --- Filter Parsing Tests ---
    
    def test_filter_missing_event_type(self):
        """Test error when filter doesn't contain event_type"""
        with self.assertRaises(InvalidFilterFormatError) as context:
            list("spaces/TEST_SPACE", filter='start_time="2023-08-23T19:20:33+00:00"')
        self.assertIn("Filter must include at least one 'event_type' or 'event_types'", str(context.exception))
    
    def test_filter_invalid_event_type(self):
        """Test error when filter contains invalid event type"""
        with self.assertRaises(InvalidEventTypeError) as context:
            list("spaces/TEST_SPACE", filter='event_types:"invalid.event.type"')
        self.assertIn("Invalid event type: 'invalid.event.type'", str(context.exception))
    
    def test_filter_invalid_start_time_format(self):
        """Test error when start_time has invalid format"""
        with self.assertRaises(InvalidTimeFormatError) as context:
            list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created" AND start_time="invalid-time"')
        self.assertIn("Invalid start_time format", str(context.exception))
    
    def test_filter_invalid_end_time_format(self):
        """Test error when end_time has invalid format"""
        with self.assertRaises(InvalidTimeFormatError) as context:
            list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created" AND end_time="invalid-time"')
        self.assertIn("Invalid end_time format", str(context.exception))
    
    def test_filter_valid_event_type_variations(self):
        """Test valid event type variations"""
        # Test event_type (singular)
        result = list("spaces/TEST_SPACE", filter='event_type:"google.workspace.chat.message.v1.created"')
        self.assertIn("spaceEvents", result)
        
        # Test event_types (plural)
        result = list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created"')
        self.assertIn("spaceEvents", result)
    
    # --- Pagination Tests ---
    
    def test_pagination_default_page_size(self):
        """Test default page size (100) when not specified"""
        result = list("spaces/TEST_SPACE", filter=DEFAULT_FILTER)
        self.assertIn("spaceEvents", result)
        self.assertEqual(len(result["spaceEvents"]), 3)  # We have 3 events for TEST_SPACE
    
    def test_pagination_custom_page_size(self):
        """Test custom page size"""
        result = list("spaces/TEST_SPACE", pageSize=1, filter=DEFAULT_FILTER)
        self.assertIn("spaceEvents", result)
        self.assertEqual(len(result["spaceEvents"]), 1)
        self.assertIn("nextPageToken", result)
    
    def test_pagination_with_page_token(self):
        """Test pagination with page token"""
        # Get first page
        result1 = list("spaces/TEST_SPACE", pageSize=2, filter=DEFAULT_FILTER)
        self.assertEqual(len(result1["spaceEvents"]), 2)
        self.assertIn("nextPageToken", result1)
        
        # Get second page
        result2 = list("spaces/TEST_SPACE", pageSize=2, pageToken=result1["nextPageToken"], filter=DEFAULT_FILTER)
        self.assertEqual(len(result2["spaceEvents"]), 1)
        self.assertNotIn("nextPageToken", result2)
    
    def test_pagination_invalid_page_token(self):
        """Test error with invalid page token"""
        with self.assertRaises(InvalidPageTokenError) as context:
            list("spaces/TEST_SPACE", pageToken="invalid", filter=DEFAULT_FILTER)
        self.assertIn("Invalid pageToken", str(context.exception))
    
    def test_pagination_no_next_page(self):
        """Test no next page token when all results fit"""
        result = list("spaces/TEST_SPACE", pageSize=10, filter=DEFAULT_FILTER)
        self.assertEqual(len(result["spaceEvents"]), 3)
        self.assertNotIn("nextPageToken", result)
    
    # --- Filtering Tests ---
    
    def test_filter_by_event_type(self):
        """Test filtering by event type"""
        result = list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created"')
        self.assertEqual(len(result["spaceEvents"]), 1)
        self.assertEqual(result["spaceEvents"][0]["eventType"], "google.workspace.chat.message.v1.created")
    
    def test_filter_by_multiple_event_types(self):
        """Test filtering by multiple event types"""
        result = list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created" AND event_types:"google.workspace.chat.message.v1.updated"')
        self.assertEqual(len(result["spaceEvents"]), 2)
    
    def test_filter_by_time_range(self):
        """Test filtering by time range"""
        result = list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created" AND start_time="2023-08-23T19:00:00+00:00" AND end_time="2023-08-23T21:00:00+00:00"')
        self.assertEqual(len(result["spaceEvents"]), 1)
        self.assertEqual(result["spaceEvents"][0]["eventTime"], "2023-08-23T19:20:33+00:00")
    
    def test_filter_with_start_time_only(self):
        """Test filtering with only start_time"""
        result = list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created" AND start_time="2023-08-24T00:00:00+00:00"')
        self.assertEqual(len(result["spaceEvents"]), 0)  # No events after this time
    
    def test_filter_with_end_time_only(self):
        """Test filtering with only end_time"""
        result = list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created" AND end_time="2023-08-23T21:00:00+00:00"')
        self.assertEqual(len(result["spaceEvents"]), 1)
    
    def test_filter_no_matching_events(self):
        """Test filter that matches no events"""
        result = list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.reaction.v1.created"')
        self.assertEqual(len(result["spaceEvents"]), 0)
    
    # --- Functional Tests ---
    
    def test_successful_list_without_filter(self):
        """Test successful listing without filter"""
        result = list("spaces/TEST_SPACE", filter=DEFAULT_FILTER)
        self.assertIn("spaceEvents", result)
        self.assertEqual(len(result["spaceEvents"]), 3)
        
        # Check that only events from TEST_SPACE are returned
        for event in result["spaceEvents"]:
            self.assertTrue(event["name"].startswith("spaces/TEST_SPACE/spaceEvents/"))
    
    def test_successful_list_with_filter(self):
        """Test successful listing with filter"""
        result = list("spaces/TEST_SPACE", filter='event_types:"google.workspace.chat.message.v1.created"')
        self.assertIn("spaceEvents", result)
        self.assertEqual(len(result["spaceEvents"]), 1)
        self.assertEqual(result["spaceEvents"][0]["eventType"], "google.workspace.chat.message.v1.created")
    
    def test_list_different_spaces(self):
        """Test that events are correctly filtered by space"""
        # Add membership for USER123 to OTHER_SPACE
        DB["Membership"].append({"name": "spaces/OTHER_SPACE/members/users/USER123", "role": "ROLE_MEMBER"})
        
        result = list("spaces/OTHER_SPACE", filter=DEFAULT_FILTER)
        self.assertEqual(len(result["spaceEvents"]), 1)
        self.assertTrue(result["spaceEvents"][0]["name"].startswith("spaces/OTHER_SPACE/spaceEvents/"))
    
    def test_return_structure(self):
        """Test the structure of the returned data"""
        result = list("spaces/TEST_SPACE", filter=DEFAULT_FILTER)
        
        # Check top-level structure
        self.assertIn("spaceEvents", result)
        self.assertIsInstance(result["spaceEvents"], type([]))  # Use type([]) instead of list
        
        # Check event structure
        if result["spaceEvents"]:
            event = result["spaceEvents"][0]
            self.assertIn("name", event)
            self.assertIn("eventTime", event)
            self.assertIn("eventType", event)
    
    # --- Edge Cases ---
    
    def test_empty_space_events(self):
        """Test with space that has no events"""
        # Clear all events
        DB["SpaceEvent"].clear()
        
        result = list("spaces/TEST_SPACE", filter=DEFAULT_FILTER)
        self.assertEqual(len(result["spaceEvents"]), 0)
        self.assertNotIn("nextPageToken", result)
    
    def test_complex_space_name(self):
        """Test with complex space name"""
        DB["Space"].append({"name": "spaces/complex-space_123", "displayName": "Complex Space"})
        DB["Membership"].append({"name": "spaces/complex-space_123/members/users/USER123", "role": "ROLE_MEMBER"})
        DB["SpaceEvent"].append({
            "name": "spaces/complex-space_123/spaceEvents/1",
            "eventTime": "2023-08-23T19:20:33+00:00",
            "eventType": "google.workspace.chat.message.v1.created"
        })
        
        result = list("spaces/complex-space_123", filter=DEFAULT_FILTER)
        self.assertEqual(len(result["spaceEvents"]), 1)
    
    def test_edge_case_pagesize_boundaries(self):
        """Test pageSize boundary values"""
        # Test minimum valid pageSize
        result = list("spaces/TEST_SPACE", pageSize=1, filter=DEFAULT_FILTER)
        self.assertEqual(len(result["spaceEvents"]), 1)
        
        # Test maximum valid pageSize
        result = list("spaces/TEST_SPACE", pageSize=1000, filter=DEFAULT_FILTER)
        self.assertEqual(len(result["spaceEvents"]), 3)


if __name__ == '__main__':
    unittest.main() 