import unittest
from unittest.mock import patch
from youtube.Memberships import update
from youtube.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

from pydantic import ValidationError


class TestMembershipUpdate(BaseTestCaseWithErrorHandler):
    """Test cases for the Memberships.update function."""

    def setUp(self):
        """Reset the database before each test."""
        DB.clear()
        DB.update({
            "memberships": {
                "member1": {
                    "id": "member1",
                    "snippet": {
                        "memberChannelId": "UC123456789",
                        "hasAccessToLevel": "level1",
                        "mode": "fanFunding"
                    }
                },
                "member2": {
                    "id": "member2",
                    "snippet": {
                        "memberChannelId": "UC987654321",
                        "hasAccessToLevel": "level2",
                        "mode": "sponsors"
                    }
                }
            }
        })

    # ==================== SUCCESSFUL UPDATE TESTS ====================

    def test_update_basic_success(self):
        """Test successful update with valid parameters."""
        snippet_update = {
            "memberChannelId": "UC111222333",
            "hasAccessToLevel": "level3",
            "mode": "sponsors"
        }
        
        result = update(part="snippet", id="member1", snippet=snippet_update)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        self.assertEqual(result["membership"]["id"], "member1")
        self.assertEqual(result["membership"]["snippet"]["memberChannelId"], "UC111222333")
        self.assertEqual(result["membership"]["snippet"]["hasAccessToLevel"], "level3")
        self.assertEqual(result["membership"]["snippet"]["mode"], "sponsors")

    def test_update_partial_snippet(self):
        """Test successful update with partial snippet data."""
        snippet_update = {
            "hasAccessToLevel": "premium"
        }
        
        result = update(part="snippet", id="member1", snippet=snippet_update)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        # Original values should be preserved
        self.assertEqual(result["membership"]["snippet"]["memberChannelId"], "UC123456789")
        self.assertEqual(result["membership"]["snippet"]["mode"], "fanFunding")
        # Updated value should be changed
        self.assertEqual(result["membership"]["snippet"]["hasAccessToLevel"], "premium")

    def test_update_add_new_fields(self):
        """Test successful update adding new fields to snippet."""
        snippet_update = {
            "newField": "newValue",
            "anotherField": 123
        }
        
        result = update(part="snippet", id="member1", snippet=snippet_update)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        # Original values should be preserved
        self.assertEqual(result["membership"]["snippet"]["memberChannelId"], "UC123456789")
        self.assertEqual(result["membership"]["snippet"]["hasAccessToLevel"], "level1")
        self.assertEqual(result["membership"]["snippet"]["mode"], "fanFunding")
        # New fields should be added
        self.assertEqual(result["membership"]["snippet"]["newField"], "newValue")
        self.assertEqual(result["membership"]["snippet"]["anotherField"], 123)

    def test_update_empty_snippet(self):
        """Test successful update with empty snippet."""
        snippet_update = {}
        
        result = update(part="snippet", id="member1", snippet=snippet_update)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        # Original values should be preserved when updating with empty dict
        self.assertEqual(result["membership"]["snippet"]["memberChannelId"], "UC123456789")
        self.assertEqual(result["membership"]["snippet"]["hasAccessToLevel"], "level1")
        self.assertEqual(result["membership"]["snippet"]["mode"], "fanFunding")

    def test_update_database_persistence(self):
        """Test that update persists to database."""
        snippet_update = {
            "memberChannelId": "UC999888777",
            "hasAccessToLevel": "gold"
        }
        
        result = update(part="snippet", id="member1", snippet=snippet_update)
        
        self.assertTrue(result["success"])
        
        # Verify the change is persisted in the database
        stored_membership = DB["memberships"]["member1"]
        self.assertEqual(stored_membership["snippet"]["memberChannelId"], "UC999888777")
        self.assertEqual(stored_membership["snippet"]["hasAccessToLevel"], "gold")
        self.assertEqual(stored_membership["snippet"]["mode"], "fanFunding")  # Should remain unchanged

    def test_update_membership_without_snippet(self):
        """Test updating membership that doesn't have a snippet key."""
        # Add a membership without snippet
        DB["memberships"]["member3"] = {
            "id": "member3"
        }
        
        snippet_update = {
            "memberChannelId": "UC555666777",
            "hasAccessToLevel": "basic",
            "mode": "fanFunding"
        }
        
        result = update(part="snippet", id="member3", snippet=snippet_update)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        self.assertEqual(result["membership"]["snippet"], snippet_update)

    # ==================== ERROR CONDITION TESTS ====================

    def test_update_invalid_part(self):
        """Test update with invalid part parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        result = update(part="invalid", id="member1", snippet=snippet_update)
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Invalid part parameter")
        self.assertNotIn("success", result)
        self.assertNotIn("membership", result)

    def test_update_membership_not_found(self):
        """Test update with non-existent membership ID."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        result = update(part="snippet", id="nonexistent", snippet=snippet_update)
        
        self.assertIn("success", result)
        self.assertFalse(result["success"])
        self.assertNotIn("membership", result)
        self.assertNotIn("error", result)

    # ==================== INPUT VALIDATION TESTS ====================

    def test_update_invalid_part_type(self):
        """Test update with non-string part parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        with self.assertRaises(ValidationError) as context:
            update(part=123, id="member1", snippet=snippet_update)
        
        self.assertIn("Input should be a valid string", str(context.exception))

    def test_update_invalid_id_type(self):
        """Test update with non-string id parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        with self.assertRaises(ValidationError) as context:
            update(part="snippet", id=123, snippet=snippet_update)
        
        self.assertIn("Input should be a valid string", str(context.exception))

    def test_update_invalid_snippet_type(self):
        """Test update with non-dictionary snippet parameter."""
        with self.assertRaises(TypeError) as context:
            update(part="snippet", id="member1", snippet="not_a_dict")
        
        self.assertIn("'snippet' parameter must be a dictionary", str(context.exception))

    def test_update_empty_part(self):
        """Test update with empty part parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        with self.assertRaises(ValueError) as context:
            update(part="", id="member1", snippet=snippet_update)
        
        self.assertIn("'part' parameter cannot be empty", str(context.exception))

    def test_update_whitespace_part(self):
        """Test update with whitespace-only part parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        with self.assertRaises(ValueError) as context:
            update(part="   ", id="member1", snippet=snippet_update)
        
        self.assertIn("'part' parameter cannot be empty", str(context.exception))

    def test_update_empty_id(self):
        """Test update with empty id parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        with self.assertRaises(ValueError) as context:
            update(part="snippet", id="", snippet=snippet_update)
        
        self.assertIn("'id' parameter cannot be empty", str(context.exception))

    def test_update_whitespace_id(self):
        """Test update with whitespace-only id parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        with self.assertRaises(ValueError) as context:
            update(part="snippet", id="   ", snippet=snippet_update)
        
        self.assertIn("'id' parameter cannot be empty", str(context.exception))

    def test_update_none_part(self):
        """Test update with None part parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        with self.assertRaises(ValidationError) as context:
            update(part=None, id="member1", snippet=snippet_update)
        
        self.assertIn("Input should be a valid string", str(context.exception))

    def test_update_none_id(self):
        """Test update with None id parameter."""
        snippet_update = {
            "memberChannelId": "UC123456789"
        }
        
        with self.assertRaises(ValidationError) as context:
            update(part="snippet", id=None, snippet=snippet_update)
        
        self.assertIn("Input should be a valid string", str(context.exception))

    def test_update_none_snippet(self):
        """Test update with None snippet parameter."""
        with self.assertRaises(TypeError) as context:
            update(part="snippet", id="member1", snippet=None)
        
        self.assertIn("'snippet' parameter must be a dictionary", str(context.exception))

    # ==================== EDGE CASE TESTS ====================

    def test_update_with_all_valid_modes(self):
        """Test update with all valid mode values."""
        modes = ["fanFunding", "sponsors"]
        
        for mode in modes:
            snippet_update = {"mode": mode}
            result = update(part="snippet", id="member1", snippet=snippet_update)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["membership"]["snippet"]["mode"], mode)

    def test_update_large_snippet(self):
        """Test update with a large snippet containing many fields."""
        large_snippet = {
            f"field_{i}": f"value_{i}" for i in range(100)
        }
        
        result = update(part="snippet", id="member1", snippet=large_snippet)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        
        # Verify all fields are present
        for i in range(100):
            self.assertEqual(result["membership"]["snippet"][f"field_{i}"], f"value_{i}")

    def test_update_special_characters_in_values(self):
        """Test update with special characters in snippet values."""
        snippet_update = {
            "memberChannelId": "UC!@#$%^&*()",
            "hasAccessToLevel": "level with spaces and symbols: !@#$%",
            "mode": "fanFunding",
            "specialField": "äöü中文🌟"
        }
        
        result = update(part="snippet", id="member1", snippet=snippet_update)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["membership"]["snippet"]["memberChannelId"], "UC!@#$%^&*()")
        self.assertEqual(result["membership"]["snippet"]["hasAccessToLevel"], "level with spaces and symbols: !@#$%")
        self.assertEqual(result["membership"]["snippet"]["specialField"], "äöü中文🌟")

    def test_update_nested_dictionary_values(self):
        """Test update with nested dictionary values in snippet."""
        snippet_update = {
            "nestedData": {
                "subField1": "value1",
                "subField2": {
                    "deepField": "deepValue"
                }
            },
            "listField": [1, 2, 3, "string", {"key": "value"}]
        }
        
        result = update(part="snippet", id="member1", snippet=snippet_update)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["membership"]["snippet"]["nestedData"]["subField1"], "value1")
        self.assertEqual(result["membership"]["snippet"]["nestedData"]["subField2"]["deepField"], "deepValue")
        self.assertEqual(result["membership"]["snippet"]["listField"], [1, 2, 3, "string", {"key": "value"}])

    # ==================== INTEGRATION TESTS ====================

    def test_update_multiple_memberships(self):
        """Test updating multiple memberships in sequence."""
        snippet_update1 = {"hasAccessToLevel": "premium"}
        snippet_update2 = {"mode": "fanFunding"}
        
        result1 = update(part="snippet", id="member1", snippet=snippet_update1)
        result2 = update(part="snippet", id="member2", snippet=snippet_update2)
        
        self.assertTrue(result1["success"])
        self.assertTrue(result2["success"])
        
        # Verify both updates are persisted
        self.assertEqual(DB["memberships"]["member1"]["snippet"]["hasAccessToLevel"], "premium")
        self.assertEqual(DB["memberships"]["member2"]["snippet"]["mode"], "fanFunding")

    def test_update_same_membership_multiple_times(self):
        """Test updating the same membership multiple times."""
        updates = [
            {"hasAccessToLevel": "level1"},
            {"mode": "sponsors"},
            {"memberChannelId": "UC999888777"}
        ]
        
        for snippet_update in updates:
            result = update(part="snippet", id="member1", snippet=snippet_update)
            self.assertTrue(result["success"])
        
        # Verify final state contains all updates
        final_membership = DB["memberships"]["member1"]
        self.assertEqual(final_membership["snippet"]["hasAccessToLevel"], "level1")
        self.assertEqual(final_membership["snippet"]["mode"], "sponsors")
        self.assertEqual(final_membership["snippet"]["memberChannelId"], "UC999888777")


if __name__ == "__main__":
    unittest.main() 