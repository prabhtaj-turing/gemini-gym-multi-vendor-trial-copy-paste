import unittest
from unittest.mock import patch
from youtube.SimulationEngine.db import DB
from youtube.Memberships import delete
from common_utils.base_case import BaseTestCaseWithErrorHandler



class TestMembershipsDelete(BaseTestCaseWithErrorHandler):
    """Test cases for the Memberships.delete function."""

    def setUp(self):
        """Reset the database before each test."""
        DB.clear()
        DB.update({
            "memberships": {
                "member1": {
                    "id": "member1",
                    "snippet": {
                        "memberChannelId": "channel1",
                        "hasAccessToLevel": "level1",
                        "mode": "fanFunding",
                    },
                },
                "member2": {
                    "id": "member2",
                    "snippet": {
                        "memberChannelId": "channel2",
                        "hasAccessToLevel": "level2",
                        "mode": "sponsors",
                    },
                },
                "member3": {
                    "id": "member3",
                    "snippet": {
                        "memberChannelId": "channel3",
                        "hasAccessToLevel": "level1",
                        "mode": "fanFunding",
                    },
                },
            }
        })

    # ==================== SUCCESSFUL DELETION TESTS ====================

    def test_delete_existing_membership_success(self):
        """Test successful deletion of an existing membership."""
        result = delete("member1")
        
        # Verify the response
        self.assertEqual(result["success"], True)
        
        # Verify the membership was removed from the database
        self.assertNotIn("member1", DB["memberships"])
        
        # Verify other memberships are still there
        self.assertIn("member2", DB["memberships"])
        self.assertIn("member3", DB["memberships"])
        self.assertEqual(len(DB["memberships"]), 2)

    def test_delete_different_membership_ids(self):
        """Test deletion of different membership IDs."""
        # Delete member2
        result = delete("member2")
        self.assertEqual(result["success"], True)
        self.assertNotIn("member2", DB["memberships"])
        self.assertEqual(len(DB["memberships"]), 2)
        
        # Delete member3
        result = delete("member3")
        self.assertEqual(result["success"], True)
        self.assertNotIn("member3", DB["memberships"])
        self.assertEqual(len(DB["memberships"]), 1)
        
        # Verify member1 is still there
        self.assertIn("member1", DB["memberships"])

    def test_delete_last_membership(self):
        """Test deletion of the last membership in the database."""
        # Delete all but one membership
        delete("member1")
        delete("member2")
        
        # Delete the last membership
        result = delete("member3")
        self.assertEqual(result["success"], True)
        self.assertEqual(len(DB["memberships"]), 0)

    # ==================== ERROR HANDLING TESTS ====================

    def test_delete_empty_id(self):
        """Test that empty membership ID raises ValueError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=ValueError,
            expected_message="Membership ID cannot be empty",
            id=""
        )

    def test_delete_whitespace_id(self):
        """Test that whitespace-only membership ID raises ValueError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=ValueError,
            expected_message="Membership ID cannot be empty",
            id="   "
        )

    def test_delete_none_id(self):
        """Test that None membership ID raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Membership ID must be a string",
            id=None
        )

    def test_delete_integer_id(self):
        """Test that integer membership ID raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Membership ID must be a string",
            id=123
        )

    def test_delete_list_id(self):
        """Test that list membership ID raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Membership ID must be a string",
            id=["member1"]
        )

    def test_delete_dict_id(self):
        """Test that dict membership ID raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Membership ID must be a string",
            id={"id": "member1"}
        )

    def test_delete_boolean_id(self):
        """Test that boolean membership ID raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=TypeError,
            expected_message="Membership ID must be a string",
            id=True
        )

    def test_delete_nonexistent_id(self):
        """Test that non-existent membership ID raises KeyError."""
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=KeyError,
            expected_message="\"Membership with ID 'nonexistent_member' not found\"",
            id="nonexistent_member"
        )

    def test_delete_already_deleted_id(self):
        """Test that attempting to delete an already deleted membership raises KeyError."""
        # First deletion should succeed
        result = delete("member1")
        self.assertEqual(result["success"], True)
        
        # Second deletion should raise KeyError
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=KeyError,
            expected_message="\"Membership with ID 'member1' not found\"",
            id="member1"
        )

    # ==================== EDGE CASES ====================

    def test_delete_with_special_characters_in_id(self):
        """Test deletion with special characters in membership ID."""
        # Add a membership with special characters
        special_id = "member_with-special.chars@123"
        DB["memberships"][special_id] = {
            "id": special_id,
            "snippet": {
                "memberChannelId": "channel_special",
                "hasAccessToLevel": "level_special",
                "mode": "fanFunding",
            },
        }
        
        # Delete the membership
        result = delete(special_id)
        self.assertEqual(result["success"], True)
        self.assertNotIn(special_id, DB["memberships"])

    def test_delete_with_unicode_characters_in_id(self):
        """Test deletion with Unicode characters in membership ID."""
        # Add a membership with Unicode characters
        unicode_id = "member_测试_🎵"
        DB["memberships"][unicode_id] = {
            "id": unicode_id,
            "snippet": {
                "memberChannelId": "channel_unicode",
                "hasAccessToLevel": "level_unicode",
                "mode": "sponsors",
            },
        }
        
        # Delete the membership
        result = delete(unicode_id)
        self.assertEqual(result["success"], True)
        self.assertNotIn(unicode_id, DB["memberships"])

    def test_delete_with_very_long_id(self):
        """Test deletion with very long membership ID."""
        # Add a membership with a very long ID
        long_id = "member_" + "x" * 1000
        DB["memberships"][long_id] = {
            "id": long_id,
            "snippet": {
                "memberChannelId": "channel_long",
                "hasAccessToLevel": "level_long",
                "mode": "fanFunding",
            },
        }
        
        # Delete the membership
        result = delete(long_id)
        self.assertEqual(result["success"], True)
        self.assertNotIn(long_id, DB["memberships"])

    def test_delete_with_empty_memberships_db(self):
        """Test deletion when memberships database is empty."""
        # Clear the memberships database
        DB["memberships"] = {}
        
        # Attempt to delete should raise KeyError
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=KeyError,
            expected_message="\"Membership with ID 'member1' not found\"",
            id="member1"
        )

    def test_delete_with_missing_memberships_key(self):
        """Test deletion when memberships key is missing from database."""
        # Remove the memberships key entirely
        if "memberships" in DB:
            del DB["memberships"]
        
        # Attempt to delete should raise KeyError
        self.assert_error_behavior(
            func_to_call=delete,
            expected_exception_type=KeyError,
            expected_message="\"Membership with ID 'member1' not found\"",
            id="member1"
        )

    # ==================== DATABASE STATE TESTS ====================

    def test_delete_preserves_other_db_collections(self):
        """Test that deletion only affects memberships, not other database collections."""
        # Add other collections to the database
        DB.update({
            "channels": {"channel1": {"id": "channel1"}},
            "videos": {"video1": {"id": "video1"}},
            "comments": {"comment1": {"id": "comment1"}},
        })
        
        # Delete a membership
        result = delete("member1")
        self.assertEqual(result["success"], True)
        
        # Verify other collections are untouched
        self.assertIn("channels", DB)
        self.assertIn("videos", DB)
        self.assertIn("comments", DB)
        self.assertEqual(DB["channels"]["channel1"]["id"], "channel1")
        self.assertEqual(DB["videos"]["video1"]["id"], "video1")
        self.assertEqual(DB["comments"]["comment1"]["id"], "comment1")

    def test_delete_returns_correct_response_format(self):
        """Test that delete returns the correct response format."""
        result = delete("member1")
        
        # Verify response structure
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 1)
        self.assertIn("success", result)
        self.assertIsInstance(result["success"], bool)
        self.assertEqual(result["success"], True)

    def test_delete_multiple_sequential_deletions(self):
        """Test multiple sequential deletions."""
        # Delete all memberships one by one
        result1 = delete("member1")
        self.assertEqual(result1["success"], True)
        self.assertEqual(len(DB["memberships"]), 2)
        
        result2 = delete("member2")
        self.assertEqual(result2["success"], True)
        self.assertEqual(len(DB["memberships"]), 1)
        
        result3 = delete("member3")
        self.assertEqual(result3["success"], True)
        self.assertEqual(len(DB["memberships"]), 0)


if __name__ == "__main__":
    unittest.main() 