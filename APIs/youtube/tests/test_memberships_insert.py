import unittest
from unittest.mock import patch
from youtube.Memberships import insert
from youtube.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

from pydantic import ValidationError


class TestMembershipsInsert(BaseTestCaseWithErrorHandler):
    """Test cases for the Memberships.insert function."""

    def setUp(self):
        """Reset the database before each test."""
        DB.clear()
        DB.update({
            "memberships": {}
        })

    # ==================== SUCCESSFUL INSERTION TESTS ====================

    def test_insert_basic_success_snippet_only(self):
        """Test successful insertion with snippet part only."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        self.assertIn("snippet", result["membership"])
        self.assertNotIn("id", result["membership"])  # ID should not be in response for snippet-only part
        self.assertEqual(result["membership"]["snippet"]["memberChannelId"], "UC123456789")
        self.assertEqual(result["membership"]["snippet"]["hasAccessToLevel"], "level1")
        self.assertEqual(result["membership"]["snippet"]["mode"], "fanFunding")

    def test_insert_basic_success_id_only(self):
        """Test successful insertion with id part only."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="id", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        self.assertIn("id", result["membership"])
        self.assertNotIn("snippet", result["membership"])  # Snippet should not be in response for id-only part
        self.assertIsInstance(result["membership"]["id"], str)

    def test_insert_success_id_and_snippet(self):
        """Test successful insertion with both id and snippet parts."""
        snippet_data = {
            "memberChannelId": "UC987654321",
            "hasAccessToLevel": "level2",
            "mode": "sponsors"
        }
        
        result = insert(part="id,snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        self.assertIn("id", result["membership"])
        self.assertIn("snippet", result["membership"])
        self.assertIsInstance(result["membership"]["id"], str)
        self.assertEqual(result["membership"]["snippet"]["memberChannelId"], "UC987654321")
        self.assertEqual(result["membership"]["snippet"]["hasAccessToLevel"], "level2")
        self.assertEqual(result["membership"]["snippet"]["mode"], "sponsors")

    def test_insert_success_comma_separated_with_spaces(self):
        """Test successful insertion with comma-separated parts including spaces."""
        snippet_data = {
            "memberChannelId": "UC111222333",
            "hasAccessToLevel": "level3",
            "mode": "fanFunding"
        }
        
        result = insert(part="id, snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertIn("membership", result)
        self.assertIn("id", result["membership"])
        self.assertIn("snippet", result["membership"])

    def test_insert_success_sponsors_mode(self):
        """Test successful insertion with sponsors mode."""
        snippet_data = {
            "memberChannelId": "UC444555666",
            "hasAccessToLevel": "premium",
            "mode": "sponsors"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["membership"]["snippet"]["mode"], "sponsors")

    def test_insert_success_fanfunding_mode(self):
        """Test successful insertion with fanFunding mode."""
        snippet_data = {
            "memberChannelId": "UC777888999",
            "hasAccessToLevel": "basic",
            "mode": "fanFunding"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["membership"]["snippet"]["mode"], "fanFunding")

    def test_insert_success_database_storage(self):
        """Test that the membership is correctly stored in the database."""
        snippet_data = {
            "memberChannelId": "UC000111222",
            "hasAccessToLevel": "gold",
            "mode": "sponsors"
        }
        
        result = insert(part="id,snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        membership_id = result["membership"]["id"]
        
        # Verify the membership is stored in the database
        self.assertIn(membership_id, DB["memberships"])
        stored_membership = DB["memberships"][membership_id]
        self.assertEqual(stored_membership["id"], membership_id)
        self.assertEqual(stored_membership["snippet"]["memberChannelId"], "UC000111222")
        self.assertEqual(stored_membership["snippet"]["hasAccessToLevel"], "gold")
        self.assertEqual(stored_membership["snippet"]["mode"], "sponsors")

    def test_insert_multiple_memberships(self):
        """Test inserting multiple memberships."""
        snippet_data1 = {
            "memberChannelId": "UC111",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        snippet_data2 = {
            "memberChannelId": "UC222",
            "hasAccessToLevel": "level2",
            "mode": "sponsors"
        }
        
        result1 = insert(part="id,snippet", snippet=snippet_data1)
        result2 = insert(part="id,snippet", snippet=snippet_data2)
        
        self.assertTrue(result1["success"])
        self.assertTrue(result2["success"])
        self.assertNotEqual(result1["membership"]["id"], result2["membership"]["id"])
        
        # Verify both are stored in database
        self.assertEqual(len(DB["memberships"]), 2)

    # ==================== VALIDATION ERROR TESTS ====================

    def test_insert_error_empty_part(self):
        """Test insertion with empty part parameter."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="", snippet=snippet_data)
        
        self.assertIn("error", result)
        self.assertIn("part cannot be empty", result["error"])

    def test_insert_error_whitespace_only_part(self):
        """Test insertion with whitespace-only part parameter."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="   ", snippet=snippet_data)
        
        self.assertIn("error", result)
        self.assertIn("part cannot be empty", result["error"])

    def test_insert_error_empty_component_in_part(self):
        """Test insertion with empty component in comma-separated part."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="id,,snippet", snippet=snippet_data)
        
        self.assertIn("error", result)
        self.assertIn("cannot contain empty components", result["error"])

    def test_insert_error_missing_member_channel_id(self):
        """Test insertion with missing memberChannelId in snippet."""
        snippet_data = {
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertIn("error", result)

    def test_insert_error_empty_member_channel_id(self):
        """Test insertion with empty memberChannelId in snippet."""
        snippet_data = {
            "memberChannelId": "",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertIn("error", result)
        self.assertIn("memberChannelId cannot be empty", result["error"])

    def test_insert_error_whitespace_member_channel_id(self):
        """Test insertion with whitespace-only memberChannelId in snippet."""
        snippet_data = {
            "memberChannelId": "   ",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertIn("error", result)
        self.assertIn("memberChannelId cannot be empty", result["error"])

    def test_insert_error_missing_has_access_to_level(self):
        """Test insertion with missing hasAccessToLevel in snippet."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "mode": "fanFunding"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertIn("error", result)

    def test_insert_error_empty_has_access_to_level(self):
        """Test insertion with empty hasAccessToLevel in snippet."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "",
            "mode": "fanFunding"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertIn("error", result)
        self.assertIn("hasAccessToLevel cannot be empty", result["error"])

    def test_insert_error_missing_mode(self):
        """Test insertion with missing mode in snippet."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1"
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertIn("error", result)

    def test_insert_error_empty_mode(self):
        """Test insertion with empty mode in snippet."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": ""
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertIn("error", result)
        self.assertIn("mode cannot be empty", result["error"])


    def test_insert_error_non_string_part(self):
        """Test insertion with non-string part parameter."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part=123, snippet=snippet_data)
        
        self.assertIn("error", result)
        self.assertIn("Input should be a valid string", result["error"])

    def test_insert_error_non_dict_snippet(self):
        """Test insertion with non-dictionary snippet parameter."""
        result = insert(part="snippet", snippet="not_a_dict")
        
        self.assertIn("error", result)

    def test_insert_error_none_snippet(self):
        """Test insertion with None snippet parameter."""
        result = insert(part="snippet", snippet=None)
        
        self.assertIn("error", result)

    # ==================== EDGE CASE TESTS ====================

    def test_insert_success_with_extra_snippet_fields(self):
        """Test insertion with extra fields in snippet (should be allowed)."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding",
            "extraField": "extraValue",
            "anotherField": 123
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["membership"]["snippet"]["extraField"], "extraValue")
        self.assertEqual(result["membership"]["snippet"]["anotherField"], 123)

    def test_insert_success_trimming_whitespace(self):
        """Test that whitespace is trimmed from snippet fields."""
        snippet_data = {
            "memberChannelId": "  UC123456789  ",
            "hasAccessToLevel": "  level1  ",
            "mode": "  fanFunding  "
        }
        
        result = insert(part="snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["membership"]["snippet"]["memberChannelId"], "UC123456789")
        self.assertEqual(result["membership"]["snippet"]["hasAccessToLevel"], "level1")
        self.assertEqual(result["membership"]["snippet"]["mode"], "fanFunding")

    def test_insert_success_unknown_part_component(self):
        """Test insertion with unknown part component (should be ignored)."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="id,snippet,unknownPart", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertIn("id", result["membership"])
        self.assertIn("snippet", result["membership"])
        self.assertNotIn("unknownPart", result["membership"])  # Should be ignored

    def test_insert_success_duplicate_part_components(self):
        """Test insertion with duplicate part components."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="id,snippet,id,snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertIn("id", result["membership"])
        self.assertIn("snippet", result["membership"])

    def test_insert_success_case_sensitivity(self):
        """Test that part components are case-sensitive."""
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="ID,SNIPPET", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        # Since ID and SNIPPET don't match 'id' and 'snippet', they should be ignored
        self.assertNotIn("id", result["membership"])
        self.assertNotIn("snippet", result["membership"])
        self.assertEqual(result["membership"], {})

    # ==================== INTEGRATION TESTS ====================

    def test_insert_database_integration(self):
        """Test that insertions properly interact with the database."""
        initial_count = len(DB["memberships"])
        
        snippet_data = {
            "memberChannelId": "UC123456789",
            "hasAccessToLevel": "level1",
            "mode": "fanFunding"
        }
        
        result = insert(part="id,snippet", snippet=snippet_data)
        
        self.assertTrue(result["success"])
        self.assertEqual(len(DB["memberships"]), initial_count + 1)
        
        # Verify the stored data matches the response
        membership_id = result["membership"]["id"]
        stored_membership = DB["memberships"][membership_id]
        self.assertEqual(stored_membership["id"], result["membership"]["id"])
        self.assertEqual(stored_membership["snippet"], result["membership"]["snippet"])


if __name__ == "__main__":
    unittest.main() 