"""
Test cases for the list_users function in the Slack Users API.

This module contains comprehensive test cases for the list_users function.
"""

import os
import base64
from unittest.mock import patch
from typing import List
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import InvalidCursorValueError
from .. import list_users

class TestListUsers(BaseTestCaseWithErrorHandler):
    """Test cases for the list_users function."""

    def setUp(self):
        """Reset test state (mock DB) before each test."""
        # Set up test data
        self.test_db = {
            "users": {
                "U001": {"id": "U001", "name": "Alice", "team_id": "T1"},
                "U002": {"id": "U002", "name": "Bob", "team_id": "T1"},
                "U003": {"id": "U003", "name": "Charlie", "team_id": "T2"},
                "U004": {"id": "U004", "name": "David", "team_id": "T1"},
                "U005": {"id": "U005", "name": "Eve"},  # No team_id
                # Keep some original test data for backward compatibility
                "U123": {
                    "id": "U123",
                    "name": "user1",
                    "team_id": "T123",
                    "profile": {"email": "john.doe@example.com"},
                },
                "U456": {"id": "U456", "name": "user2", "team_id": "T123"},
                "U789": {"id": "U789", "name": "user3", "team_id": "T456"},
            },
        }
        
        # Start each test with a patch
        self.patcher = patch("slack.Users.DB", self.test_db)
        self.mock_db = self.patcher.start()
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")

    def tearDown(self):
        """Restore original DB state after test."""
        self.patcher.stop()

    # New comprehensive tests based on your requirements
    def test_valid_input_default_parameters(self):
        """Test with default parameters, expecting first 100 (or all if less) users."""
        result = list_users()
        self.assertTrue(result["ok"])
        self.assertIsInstance(result["members"], list)
        self.assertEqual(
            len(result["members"]), 8
        )  # All users (U001-U005 + U123, U456, U789)
        self.assertIsNone(result["response_metadata"]["next_cursor"])

    def test_valid_input_with_limit(self):
        """Test with a specific limit."""
        result = list_users(limit=2)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 2)
        # Check that we get the first 2 users (order may vary based on dict iteration)
        self.assertIsNotNone(result["response_metadata"]["next_cursor"])
        
        # Verify the cursor is properly base64 encoded
        cursor = result["response_metadata"]["next_cursor"]
        decoded = base64.b64decode(cursor).decode("utf-8")
        self.assertTrue(decoded.startswith("user:"))

    def test_valid_input_with_team_id(self):
        """Test filtering by team_id."""
        result = list_users(team_id="T1")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 3)  # U001, U002, U004
        member_ids = sorted([m["id"] for m in result["members"]])
        self.assertEqual(member_ids, ["U001", "U002", "U004"])
        self.assertIsNone(
            result["response_metadata"]["next_cursor"]
        )  # All T1 users fit

    def test_valid_input_with_team_id_and_limit_pagination(self):
        """Test filtering by team_id with pagination."""
        result = list_users(team_id="T1", limit=1)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 1)
        
        # Get first user for T1
        first_user_id = result["members"][0]["id"]
        self.assertIn(first_user_id, ["U001", "U002", "U004"])  # Should be one of T1 users
        self.assertIsNotNone(result["response_metadata"]["next_cursor"])

        # Test second page
        cursor = result["response_metadata"]["next_cursor"]
        result_page2 = list_users(team_id="T1", limit=1, cursor=cursor)
        self.assertTrue(result_page2["ok"])
        self.assertEqual(len(result_page2["members"]), 1)
        
        second_user_id = result_page2["members"][0]["id"]
        self.assertIn(second_user_id, ["U001", "U002", "U004"])
        self.assertNotEqual(first_user_id, second_user_id)  # Should be different user

    def test_valid_input_include_locale(self):
        """Test with include_locale set to True."""
        result = list_users(include_locale=True, limit=1)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 1)
        self.assertIn("locale", result["members"][0])
        self.assertEqual(result["members"][0]["locale"], "en-US")

    def test_valid_input_empty_result(self):
        """Test with a team_id that has no users."""
        result = list_users(team_id="T_NON_EXISTENT")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 0)
        self.assertIsNone(result["response_metadata"]["next_cursor"])

    def test_valid_input_cursor_at_end(self):
        """Test when cursor points to a non-existent user ID."""
        # Create base64 cursor for a non-existent user ID
        cursor = base64.b64encode("user:U999".encode("utf-8")).decode("utf-8")
        with self.assertRaises(InvalidCursorValueError) as context:
            list_users(cursor=cursor)  # Cursor points to non-existent user
        self.assertEqual(
            str(context.exception), "User ID U999 not found in users list"
        )

    def test_valid_input_cursor_beyond_end(self):
        """Test when cursor points to another non-existent user ID."""
        # Create base64 cursor for another non-existent user ID
        cursor = base64.b64encode("user:U888".encode("utf-8")).decode("utf-8")
        with self.assertRaises(InvalidCursorValueError) as context:
            list_users(cursor=cursor)  # Cursor points to non-existent user
        self.assertEqual(
            str(context.exception), "User ID U888 not found in users list"
        )

    # --- Validation Error Tests ---
    def test_invalid_cursor_type(self):
        """Test that invalid cursor type raises TypeError."""
        self.assert_error_behavior(
            list_users,
            TypeError,
            "cursor must be a string or None.",
            cursor=123,  # Not a string
        )

    def test_invalid_include_locale_type(self):
        """Test that invalid include_locale type raises TypeError."""
        self.assert_error_behavior(
            list_users,
            TypeError,
            "include_locale must be a boolean.",
            include_locale="not a bool",
        )

    def test_invalid_limit_type(self):
        """Test that invalid limit type raises TypeError."""
        self.assert_error_behavior(
            list_users, TypeError, "limit must be an integer.", limit="not an int"
        )

    def test_invalid_limit_value_zero(self):
        """Test that limit <= 0 raises ValueError."""
        self.assert_error_behavior(
            list_users, ValueError, "limit must be a positive integer.", limit=0
        )

    def test_invalid_limit_value_negative(self):
        """Test that limit <= 0 raises ValueError for negative limit."""
        self.assert_error_behavior(
            list_users, ValueError, "limit must be a positive integer.", limit=-10
        )

    def test_invalid_limit_value_too_large(self):
        """Test that limit > 1000 raises ValueError."""
        self.assert_error_behavior(
            list_users, ValueError, "limit must be no larger than 1000.", limit=1001
        )

    def test_invalid_limit_type_bool_true(self):
        """Test that boolean True for limit raises TypeError."""
        self.assert_error_behavior(
            list_users, TypeError, "limit must be an integer.", limit=True
        )

    def test_invalid_limit_type_bool_false(self):
        """Test that boolean False for limit raises TypeError."""
        self.assert_error_behavior(
            list_users, TypeError, "limit must be an integer.", limit=False
        )

    def test_invalid_team_id_type(self):
        """Test that invalid team_id type raises TypeError."""
        self.assert_error_behavior(
            list_users,
            TypeError,
            "team_id must be a string or None.",
            team_id=12345,  # Not a string
        )

    # --- Original Core Logic Error Handling Test ---
    def test_core_logic_invalid_cursor_format(self):
        """Test original behavior for cursor that cannot be converted to int."""
        with self.assertRaises(InvalidCursorValueError) as context:
            list_users(cursor="not-a-valid-cursor")
        self.assertEqual(str(context.exception), "Invalid base64 cursor format")

    def test_core_logic_invalid_cursor_negative(self):
        """Test original behavior for cursor that converts to negative int."""
        with self.assertRaises(InvalidCursorValueError) as context:
            # Create base64 cursor with invalid format (not starting with "user:")
            cursor = base64.b64encode("invalid:-1".encode("utf-8")).decode("utf-8")
            list_users(cursor=cursor)
        self.assertEqual(str(context.exception), "Invalid cursor format")

    def test_pagination_next_cursor_logic(self):
        """Test that next_cursor is None when all items are fetched."""
        # Case 1: limit is greater than remaining items
        # First get some users to establish a cursor position
        result_first = list_users(limit=5)
        if result_first["response_metadata"]["next_cursor"]:
            cursor = result_first["response_metadata"]["next_cursor"]
            result = list_users(cursor=cursor, limit=10)  # Large limit for remaining
            self.assertTrue(result["ok"])
            # Should get remaining users and no next cursor
            self.assertIsNone(result["response_metadata"]["next_cursor"])

        # Case 2: Test with exact limit
        total_users = len(self.test_db["users"])
        result = list_users(limit=total_users)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), total_users)
        self.assertIsNone(result["response_metadata"]["next_cursor"])

    # Original tests (keeping for backward compatibility)
    def test_list_users_success(self):
        """Test successful listing of users with default parameters."""
        result = list_users()
        self.assertTrue(result["ok"])
        self.assertIn("members", result)  # Should return 'members' not 'users'
        self.assertIn("response_metadata", result)
        self.assertGreaterEqual(len(result["members"]), 3)  # At least original test users

        # Verify response structure
        self.assertIsInstance(result["members"], list)
        self.assertIsInstance(result["response_metadata"], dict)

    def test_list_users_with_team_filter(self):
        """Test listing users filtered by team_id."""
        # Filter by team T123 (should return U123, U456)
        result = list_users(team_id="T123")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 2)

        # Filter by team T456 (should return U789)
        result = list_users(team_id="T456")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 1)
        self.assertEqual(result["members"][0]["id"], "U789")

        # Filter by non-existent team
        result = list_users(team_id="T999")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 0)

    def test_list_users_with_pagination(self):
        """Test pagination functionality."""
        # Test with limit
        result = list_users(limit=2)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 2)
        self.assertIsNotNone(result["response_metadata"]["next_cursor"])

        # Test with cursor
        cursor = result["response_metadata"]["next_cursor"]
        result = list_users(cursor=cursor, limit=2)
        self.assertTrue(result["ok"])
        self.assertLessEqual(len(result["members"]), 2)  # Might be less if near end

    def test_list_users_with_locale(self):
        """Test including locale information."""
        result = list_users(include_locale=True)
        self.assertTrue(result["ok"])

        # Check that locale is added to each user
        for user in result["members"]:
            self.assertIn("locale", user)
            self.assertEqual(user["locale"], "en-US")

    def test_list_users_invalid_cursor_format_original(self):
        """Test invalid cursor format (non-base64 string)."""
        with self.assertRaises(InvalidCursorValueError) as context:
            list_users(cursor="invalid")
        self.assertEqual(str(context.exception), "Invalid base64 cursor format")

    def test_list_users_negative_cursor_original(self):
        """Test invalid cursor format (not starting with user:)."""
        with self.assertRaises(InvalidCursorValueError) as context:
            # Create base64 cursor with invalid format (not starting with "user:")
            cursor = base64.b64encode("invalid:-1".encode("utf-8")).decode("utf-8")
            list_users(cursor=cursor)
        self.assertEqual(str(context.exception), "Invalid cursor format")

    def test_list_users_empty_db(self):
        """Test listing users when DB is empty."""
        empty_db = {"users": {}}
        with patch("slack.Users.DB", empty_db):
            result = list_users()
            self.assertTrue(result["ok"])
            self.assertEqual(len(result["members"]), 0)
            self.assertIsNone(result["response_metadata"]["next_cursor"])

    def test_list_users_edge_cases(self):
        """Test edge cases for pagination."""
        # Test cursor pointing to non-existent user
        cursor = base64.b64encode("user:U999".encode("utf-8")).decode("utf-8")
        with self.assertRaises(InvalidCursorValueError) as context:
            list_users(cursor=cursor)  # Non-existent user
        self.assertEqual(
            str(context.exception), "User ID U999 not found in users list"
        )

        # Test large limit
        result = list_users(limit=1000)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), len(self.test_db["users"]))  # All users
        self.assertIsNone(result["response_metadata"]["next_cursor"])

    def test_list_users_none_values(self):
        """Test with None values for optional parameters."""
        result = list_users(cursor=None, team_id=None, include_locale=False)
        self.assertTrue(result["ok"])
        self.assertIsInstance(result["members"], list)
        self.assertIn("response_metadata", result)

    def test_list_users_team_filter_with_pagination(self):
        """Test team filtering combined with pagination."""
        # Get T1 users with limit
        result = list_users(team_id="T1", limit=2)
        self.assertTrue(result["ok"])
        self.assertLessEqual(len(result["members"]), 2)
        
        # All returned users should be from T1
        for user in result["members"]:
            self.assertEqual(user.get("team_id"), "T1")

    def test_list_users_no_team_id_users(self):
        """Test users without team_id are included in general listing."""
        result = list_users()
        self.assertTrue(result["ok"])
        
        # Should include U005 which has no team_id
        user_ids = [user["id"] for user in result["members"]]
        self.assertIn("U005", user_ids)

    def test_list_users_boundary_conditions(self):
        """Test boundary conditions for limit values."""
        # Test minimum valid limit
        result = list_users(limit=1)
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["members"]), 1)
        
        # Test maximum valid limit
        result = list_users(limit=1000)
        self.assertTrue(result["ok"])
        self.assertLessEqual(len(result["members"]), 1000)

    # --- Tests for Pagination Sorting Bug Fix ---

    def test_list_users_consistent_sorting_bug_fix(self):
        """Test that users are consistently sorted by ID for reliable pagination."""
        # Get all users to verify they are sorted by ID
        result = list_users()
        self.assertTrue(result["ok"])
        
        # Extract user IDs and verify they are sorted
        user_ids = [user["id"] for user in result["members"]]
        sorted_user_ids = sorted(user_ids)
        
        # Users should be returned in sorted order by ID
        self.assertEqual(user_ids, sorted_user_ids)

    def test_list_users_pagination_consistency_bug_fix(self):
        """Test that pagination is consistent across multiple calls."""
        # Test with small limit to force pagination
        result1 = list_users(limit=3)
        self.assertTrue(result1["ok"])
        self.assertEqual(len(result1["members"]), 3)
        
        # Get the first page user IDs
        first_page_ids = [user["id"] for user in result1["members"]]
        
        # Get second page using cursor
        cursor = result1["response_metadata"]["next_cursor"]
        self.assertIsNotNone(cursor)
        
        result2 = list_users(cursor=cursor, limit=3)
        self.assertTrue(result2["ok"])
        second_page_ids = [user["id"] for user in result2["members"]]
        
        # Verify no overlap between pages
        self.assertFalse(any(user_id in first_page_ids for user_id in second_page_ids))
        
        # Verify second page is also sorted
        self.assertEqual(second_page_ids, sorted(second_page_ids))

    def test_list_users_pagination_completeness_bug_fix(self):
        """Test that pagination covers all users without skipping or duplicating."""
        all_user_ids = set()
        cursor = None
        page_count = 0
        
        # Paginate through all users
        while True:
            if cursor:
                result = list_users(cursor=cursor, limit=2)
            else:
                result = list_users(limit=2)
            
            self.assertTrue(result["ok"])
            page_count += 1
            
            # Collect user IDs from this page
            page_user_ids = [user["id"] for user in result["members"]]
            
            # Verify no duplicates within this page
            self.assertEqual(len(page_user_ids), len(set(page_user_ids)))
            
            # Verify no duplicates across pages
            for user_id in page_user_ids:
                self.assertNotIn(user_id, all_user_ids, f"User {user_id} appears in multiple pages")
                all_user_ids.add(user_id)
            
            # Check if there are more pages
            cursor = result["response_metadata"]["next_cursor"]
            if not cursor:
                break
                
            # Safety check to prevent infinite loops
            self.assertLess(page_count, 10, "Too many pages, possible infinite loop")
        
        # Verify we got all users
        expected_user_ids = set(self.test_db["users"].keys())
        self.assertEqual(all_user_ids, expected_user_ids)

    def test_list_users_team_filter_sorting_bug_fix(self):
        """Test that team filtering also maintains consistent sorting."""
        # Test with team T1
        result = list_users(team_id="T1")
        self.assertTrue(result["ok"])
        
        # Verify all returned users are from T1
        for user in result["members"]:
            self.assertEqual(user["team_id"], "T1")
        
        # Verify users are sorted by ID
        user_ids = [user["id"] for user in result["members"]]
        self.assertEqual(user_ids, sorted(user_ids))
        
        # Should get U001, U002, U004 in sorted order
        expected_ids = ["U001", "U002", "U004"]
        self.assertEqual(user_ids, expected_ids)

    def test_list_users_pagination_with_team_filter_bug_fix(self):
        """Test that pagination works correctly with team filtering."""
        # Get first page of T1 users
        result1 = list_users(team_id="T1", limit=2)
        self.assertTrue(result1["ok"])
        self.assertEqual(len(result1["members"]), 2)
        
        # Verify first page is sorted
        first_page_ids = [user["id"] for user in result1["members"]]
        self.assertEqual(first_page_ids, sorted(first_page_ids))
        
        # Get second page
        cursor = result1["response_metadata"]["next_cursor"]
        self.assertIsNotNone(cursor)
        
        result2 = list_users(team_id="T1", cursor=cursor, limit=2)
        self.assertTrue(result2["ok"])
        second_page_ids = [user["id"] for user in result2["members"]]
        
        # Verify second page is also sorted
        self.assertEqual(second_page_ids, sorted(second_page_ids))
        
        # Verify no overlap
        self.assertFalse(any(user_id in first_page_ids for user_id in second_page_ids))
        
        # Verify all users are from T1
        for user in result1["members"] + result2["members"]:
            self.assertEqual(user["team_id"], "T1")

    def test_list_users_database_order_independence_bug_fix(self):
        """Test that pagination works regardless of database iteration order."""
        # Create a test DB with users in non-alphabetical order
        unordered_db = {
            "users": {
                "U999": {"id": "U999", "name": "Zoe", "team_id": "T1"},
                "U111": {"id": "U111", "name": "Alice", "team_id": "T1"},
                "U555": {"id": "U555", "name": "Mike", "team_id": "T1"},
                "U333": {"id": "U333", "name": "John", "team_id": "T1"},
            }
        }
        
        with patch("slack.Users.DB", unordered_db):
            # Get all users - should be sorted by ID regardless of DB order
            result = list_users()
            self.assertTrue(result["ok"])
            
            user_ids = [user["id"] for user in result["members"]]
            expected_order = ["U111", "U333", "U555", "U999"]
            self.assertEqual(user_ids, expected_order)
            
            # Test pagination with this unordered DB
            result1 = list_users(limit=2)
            self.assertTrue(result1["ok"])
            self.assertEqual(len(result1["members"]), 2)
            
            # First page should be U111, U333
            first_page_ids = [user["id"] for user in result1["members"]]
            self.assertEqual(first_page_ids, ["U111", "U333"])
            
            # Second page should be U555, U999
            cursor = result1["response_metadata"]["next_cursor"]
            result2 = list_users(cursor=cursor, limit=2)
            self.assertTrue(result2["ok"])
            second_page_ids = [user["id"] for user in result2["members"]]
            self.assertEqual(second_page_ids, ["U555", "U999"])

    def test_list_users_cursor_stability_bug_fix(self):
        """Test that cursors remain stable across multiple calls."""
        # Get first page
        result1 = list_users(limit=2)
        self.assertTrue(result1["ok"])
        cursor1 = result1["response_metadata"]["next_cursor"]
        
        # Get first page again - should be identical
        result2 = list_users(limit=2)
        self.assertTrue(result2["ok"])
        cursor2 = result2["response_metadata"]["next_cursor"]
        
        # Cursors should be identical
        self.assertEqual(cursor1, cursor2)
        
        # User lists should be identical
        self.assertEqual([user["id"] for user in result1["members"]], 
                        [user["id"] for user in result2["members"]])

    def test_list_users_edge_case_empty_id_bug_fix(self):
        """Test handling of users with empty or missing IDs."""
        # Create test DB with user having empty ID
        edge_case_db = {
            "users": {
                "U001": {"id": "U001", "name": "Alice", "team_id": "T1"},
                "U002": {"id": "", "name": "Bob", "team_id": "T1"},  # Empty ID
                "U003": {"id": "U003", "name": "Charlie", "team_id": "T1"},
                "U004": {"id": None, "name": "David", "team_id": "T1"},  # None ID
            }
        }
        
        with patch("slack.Users.DB", edge_case_db):
            result = list_users()
            self.assertTrue(result["ok"])
            
            # Should handle edge cases gracefully
            user_ids = [user.get("id") for user in result["members"]]
            # Users with empty/None IDs should be sorted to the beginning
            # Note: None values are converted to empty strings for sorting but remain None in the result
            self.assertEqual(user_ids, ["", None, "U001", "U003"])
