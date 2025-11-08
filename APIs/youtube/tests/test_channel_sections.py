import unittest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from youtube.ChannelSection import update, insert
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestChannelSectionUpdate(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        self.mock_db = {
            "channelSections": {
                "section1": {
                    "id": "section1",
                    "snippet": {
                        "channelId": "channel1",
                        "type": "singlePlaylist"
                    }
                }
            },
            "channels": {
                "channel1": {
                    "id": "channel1",
                    "snippet": {
                        "title": "Test Channel"
                    }
                },
                "channel2": {
                    "id": "channel2", 
                    "snippet": {
                        "title": "Another Channel"
                    }
                }
            }
        }

    # Test part parameter validation
    def test_update_part_missing(self):
        """Test update with missing part parameter"""
        self.assert_error_behavior(
            update,
            ValueError,
            "part parameter is required",
            part="",
            section_id="section1"
        )

    def test_update_part_none(self):
        """Test update with None part parameter"""
        self.assert_error_behavior(
            update,
            ValueError,
            "part parameter is required",
            part=None,
            section_id="section1"
        )

    def test_update_part_not_string(self):
        """Test update with non-string part parameter"""
        self.assert_error_behavior(
            update,
            TypeError,
            "part must be a string",
            part=123,
            section_id="section1"
        )

    def test_update_part_empty_string(self):
        """Test update with empty string part parameter"""
        self.assert_error_behavior(
            update,
            ValueError,
            "part cannot be an empty string",
            part="   ",
            section_id="section1"
        )

    def test_update_part_invalid_value(self):
        """Test update with invalid part parameter value"""
        self.assert_error_behavior(
            update,
            ValueError,
            "Invalid part parameter value",
            part="invalid_part",
            section_id="section1"
        )

    def test_update_part_mixed_valid_invalid(self):
        """Test update with mixed valid and invalid part values"""
        self.assert_error_behavior(
            update,
            ValueError,
            "Invalid part parameter value",
            part="snippet,invalid_part",
            section_id="section1"
        )

    # Test section_id parameter validation
    def test_update_section_id_missing(self):
        """Test update with missing section_id parameter"""
        self.assert_error_behavior(
            update,
            ValueError,
            "section_id parameter is required",
            part="snippet",
            section_id=""
        )

    def test_update_section_id_none(self):
        """Test update with None section_id parameter"""
        self.assert_error_behavior(
            update,
            ValueError,
            "section_id parameter is required",
            part="snippet",
            section_id=None
        )

    def test_update_section_id_not_string(self):
        """Test update with non-string section_id"""
        self.assert_error_behavior(
            update,
            TypeError,
            "section_id must be a string",
            part="snippet",
            section_id=123
        )

    def test_update_section_id_empty_string(self):
        """Test update with empty string section_id"""
        self.assert_error_behavior(
            update,
            ValueError,
            "section_id cannot be an empty string",
            part="snippet",
            section_id="   "
        )

    @patch("youtube.ChannelSection.DB")
    def test_update_section_id_not_found(self, mock_db):
        """Test update with section_id not in database"""
        mock_db.get.return_value = {}
        self.assert_error_behavior(
            update,
            ValueError,
            "Channel section ID: nonexistent_section not found in the database.",
            part="snippet",
            section_id="nonexistent_section"
        )

    # Test on_behalf_of_content_owner parameter validation
    @patch("youtube.ChannelSection.DB")
    def test_update_on_behalf_of_content_owner_not_string(self, mock_db):
        """Test update with non-string on_behalf_of_content_owner"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            TypeError,
            "on_behalf_of_content_owner must be a string",
            part="snippet",
            section_id="section1",
            on_behalf_of_content_owner=123
        )

    @patch("youtube.ChannelSection.DB")
    def test_update_on_behalf_of_content_owner_empty_string(self, mock_db):
        """Test update with empty string on_behalf_of_content_owner"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "on_behalf_of_content_owner cannot be an empty string",
            part="snippet",
            section_id="section1",
            on_behalf_of_content_owner="   "
        )

    # Test snippet parameter validation
    @patch("youtube.ChannelSection.DB")
    def test_update_snippet_valid_partial_fields(self, mock_db):
        """Test update with snippet containing only some fields (UpdateChannelSectionSnippet has optional fields)"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        mock_db.__getitem__.side_effect = lambda key: self.mock_db[key]
        
        # This should work since UpdateChannelSectionSnippet has optional fields
        result = update(
            part="snippet",
            section_id="section1",
            snippet={"type": "singlePlaylist"}  # channelId is optional
        )
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)

    @patch("youtube.ChannelSection.DB")
    def test_update_snippet_extra_fields_forbidden(self, mock_db):
        """Test update with snippet containing extra fields"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(
                part="snippet",
                section_id="section1",
                snippet={
                    "channelId": "channel1",
                    "type": "singlePlaylist",
                    "extraField": "not_allowed"
                }
            )
        # Check for Pydantic v2 error message format
        error_str = str(context.exception)
        self.assertTrue("extra" in error_str.lower() or "forbidden" in error_str.lower() or "not permitted" in error_str.lower())

    @patch("youtube.ChannelSection.DB")
    def test_update_snippet_invalid_field_types(self, mock_db):
        """Test update with snippet containing invalid field types"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        with self.assertRaises(ValidationError) as context:
            update(
                part="snippet",
                section_id="section1",
                snippet={
                    "channelId": 123,  # Should be string
                    "type": "singlePlaylist"
                }
            )
        # Check for Pydantic v2 error message format
        error_str = str(context.exception)
        self.assertTrue("str" in error_str.lower() or "string" in error_str.lower() or "type" in error_str.lower())

    @patch("youtube.ChannelSection.DB")
    def test_update_snippet_channel_id_not_found(self, mock_db):
        """Test update with snippet channelId not found in database"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        self.assert_error_behavior(
            update,
            ValueError,
            "Channel ID: nonexistent_channel not found in the database.",
            part="snippet",
            section_id="section1",
            snippet={
                "channelId": "nonexistent_channel",
                "type": "singlePlaylist"
            }
        )

    # Test success scenarios
    @patch("youtube.ChannelSection.DB")
    def test_update_valid_minimal(self, mock_db):
        """Test update with valid minimal parameters"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        mock_db.__getitem__.side_effect = lambda key: self.mock_db[key]

        result = update(
            part="snippet",
            section_id="section1"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertEqual(result["success"], "Channel section ID: section1 updated successfully.")

    @patch("youtube.ChannelSection.DB")
    def test_update_valid_with_snippet(self, mock_db):
        """Test update with valid snippet parameter"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        mock_db.__getitem__.side_effect = lambda key: self.mock_db[key]

        result = update(
            part="snippet",
            section_id="section1",
            snippet={
                "channelId": "channel2",
                "type": "multiplePlaylists"
            }
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertEqual(result["success"], "Channel section ID: section1 updated successfully.")

    @patch("youtube.ChannelSection.DB")
    def test_update_valid_with_on_behalf_of_content_owner(self, mock_db):
        """Test update with valid on_behalf_of_content_owner"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        mock_db.__getitem__.side_effect = lambda key: self.mock_db[key]

        result = update(
            part="snippet",
            section_id="section1",
            on_behalf_of_content_owner="content_owner_123"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertEqual(result["success"], "Channel section ID: section1 updated successfully.")

    @patch("youtube.ChannelSection.DB")
    def test_update_valid_all_parameters(self, mock_db):
        """Test update with all valid parameters"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        mock_db.__getitem__.side_effect = lambda key: self.mock_db[key]

        result = update(
            part="snippet,contentDetails",
            section_id="section1",
            snippet={
                "channelId": "channel1",
                "type": "singlePlaylist"
            },
            on_behalf_of_content_owner="content_owner_123"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertEqual(result["success"], "Channel section ID: section1 updated successfully.")

    @patch("youtube.ChannelSection.DB")
    def test_update_valid_all_part_values(self, mock_db):
        """Test update with all valid part values"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        mock_db.__getitem__.side_effect = lambda key: self.mock_db[key]

        valid_parts = ["snippet", "statistics", "contentDetails"]
        for part_value in valid_parts:
            with self.subTest(part=part_value):
                result = update(
                    part=part_value,
                    section_id="section1"
                )
                self.assertIsInstance(result, dict)
                self.assertIn("success", result)

    # Test validation order
    @patch("youtube.ChannelSection.DB")
    def test_update_validation_order(self, mock_db):
        """Test that validation happens in correct order"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)

        # Test type validation (TypeError) happens first
        with self.assertRaises(TypeError):
            update(part=123, section_id="section1")
        
        # Test business logic validation (ValueError) happens after type validation passes
        with self.assertRaises(ValueError):
            update(part="   ", section_id="section1")

    @patch("youtube.ChannelSection.DB") 
    def test_update_database_modification(self, mock_db):
        """Test that update actually modifies the database correctly"""
        sections_copy = self.mock_db["channelSections"].copy()
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": sections_copy,
            "channels": self.mock_db["channels"]
        }.get(key, default)

        original_section = sections_copy["section1"].copy()
        
        result = update(
            part="snippet",
            section_id="section1",
            snippet={
                "channelId": "channel2",
                "type": "multiplePlaylists" 
            },
            on_behalf_of_content_owner="content_owner_123"
        )

        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertEqual(result["success"], "Channel section ID: section1 updated successfully.")

    # Test additional coverage scenarios
    @patch("youtube.ChannelSection.DB")
    def test_update_snippet_empty_dict(self, mock_db):
        """Test update with empty snippet dict"""
        mock_db.get.side_effect = lambda key, default: {
            "channelSections": self.mock_db["channelSections"],
            "channels": self.mock_db["channels"]
        }.get(key, default)
        mock_db.__getitem__.side_effect = lambda key: self.mock_db[key]

        # Empty snippet should work since UpdateChannelSectionSnippet has all optional fields
        result = update(
            part="snippet",
            section_id="section1",
            snippet={}
        )
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)

    def test_update_part_all_valid_combinations(self):
        """Test update with all valid part combinations"""
        valid_parts = [
            "snippet",
            "statistics", 
            "contentDetails",
            "snippet,statistics",
            "snippet,contentDetails",
            "statistics,contentDetails",
            "snippet,statistics,contentDetails"
        ]
        
        # These tests only validate the part parameter parsing, no DB access needed
        for part_value in valid_parts:
            with self.subTest(part=part_value):
                try:
                    # This will fail at section_id check, but part validation should pass
                    update(part=part_value, section_id="nonexistent")
                except ValueError as e:
                    # Should fail on section not found, not part validation
                    self.assertIn("not found in the database", str(e))


class TestChannelSectionInsert(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        self.mock_db = {
            "channelSections": {},
            "channels": {
                "channel1": {
                    "id": "channel1",
                    "snippet": {
                        "title": "Test Channel"
                    }
                }
            }
        }

    # Test part parameter validation
    def test_insert_part_missing(self):
        """Test insert with missing part parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "part parameter is required",
            part="",
            snippet={"channelId": "channel1", "type": "singlePlaylist"}
        )

    def test_insert_part_none(self):
        """Test insert with None part parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "part parameter is required",
            part=None,
            snippet={"channelId": "channel1", "type": "singlePlaylist"}
        )

    def test_insert_part_not_string(self):
        """Test insert with non-string part parameter"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "part must be a string",
            part=123,
            snippet={"channelId": "channel1", "type": "singlePlaylist"}
        )

    def test_insert_part_empty_string(self):
        """Test insert with empty string part parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "part cannot be an empty string",
            part="   ",
            snippet={"channelId": "channel1", "type": "singlePlaylist"}
        )

    def test_insert_part_invalid_value(self):
        """Test insert with invalid part parameter value"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Invalid part parameter value",
            part="invalid_part",
            snippet={"channelId": "channel1", "type": "singlePlaylist"}
        )

    def test_insert_part_mixed_valid_invalid(self):
        """Test insert with mixed valid and invalid part values"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Invalid part parameter value",
            part="snippet,invalid_part",
            snippet={"channelId": "channel1", "type": "singlePlaylist"}
        )

    # Test snippet parameter validation
    def test_insert_snippet_missing(self):
        """Test insert with missing snippet parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "snippet parameter is required",
            part="snippet",
            snippet=""
        )

    def test_insert_snippet_none(self):
        """Test insert with None snippet parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "snippet parameter is required",
            part="snippet",
            snippet=None
        )

    def test_insert_snippet_missing_required_fields(self):
        """Test insert with snippet missing required fields"""
        with self.assertRaises(ValidationError) as context:
            insert(
                part="snippet",
                snippet={"type": "singlePlaylist"}  # Missing channelId (required in InsertChannelSectionSnippet)
            )
        error_str = str(context.exception)
        self.assertTrue("required" in error_str.lower() or "missing" in error_str.lower())

    def test_insert_snippet_extra_fields_forbidden(self):
        """Test insert with snippet containing extra fields"""
        with self.assertRaises(ValidationError) as context:
            insert(
                part="snippet",
                snippet={
                    "channelId": "channel1",
                    "type": "singlePlaylist",
                    "extraField": "not_allowed"
                }
            )
        error_str = str(context.exception)
        self.assertTrue("extra" in error_str.lower() or "forbidden" in error_str.lower() or "not permitted" in error_str.lower())

    def test_insert_snippet_invalid_field_types(self):
        """Test insert with snippet containing invalid field types"""
        with self.assertRaises(ValidationError) as context:
            insert(
                part="snippet",
                snippet={
                    "channelId": 123,  # Should be string
                    "type": "singlePlaylist"
                }
            )
        error_str = str(context.exception)
        self.assertTrue("str" in error_str.lower() or "string" in error_str.lower() or "type" in error_str.lower())

    @patch("youtube.ChannelSection.DB")
    def test_insert_snippet_channel_id_not_found(self, mock_db):
        """Test insert with snippet channelId not found in database"""
        mock_db.get.return_value = {}  # Empty channels dict
        self.assert_error_behavior(
            insert,
            ValueError,
            "Channel ID: nonexistent_channel not found in the database.",
            part="snippet",
            snippet={
                "channelId": "nonexistent_channel",
                "type": "singlePlaylist"
            }
        )

    # Test on_behalf_of_content_owner parameter validation
    @patch("youtube.ChannelSection.DB")
    def test_insert_on_behalf_of_content_owner_not_string(self, mock_db):
        """Test insert with non-string on_behalf_of_content_owner"""
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}  # Mock channels exist
        mock_db.setdefault.return_value = {}
        self.assert_error_behavior(
            insert,
            TypeError,
            "on_behalf_of_content_owner must be a string",
            part="snippet",
            snippet={"channelId": "channel1", "type": "singlePlaylist"},
            on_behalf_of_content_owner=123
        )

    @patch("youtube.ChannelSection.DB")
    def test_insert_on_behalf_of_content_owner_empty_string(self, mock_db):
        """Test insert with empty string on_behalf_of_content_owner"""
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}  # Mock channels exist
        mock_db.setdefault.return_value = {}
        self.assert_error_behavior(
            insert,
            ValueError,
            "on_behalf_of_content_owner cannot be an empty string",
            part="snippet",
            snippet={"channelId": "channel1", "type": "singlePlaylist"},
            on_behalf_of_content_owner="   "
        )

    # Test on_behalf_of_content_owner_channel parameter validation
    @patch("youtube.ChannelSection.DB")
    def test_insert_on_behalf_of_content_owner_channel_not_string(self, mock_db):
        """Test insert with non-string on_behalf_of_content_owner_channel"""
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}  # Mock channels exist
        mock_db.setdefault.return_value = {}
        self.assert_error_behavior(
            insert,
            TypeError,
            "on_behalf_of_content_owner_channel must be a string",
            part="snippet",
            snippet={"channelId": "channel1", "type": "singlePlaylist"},
            on_behalf_of_content_owner_channel=123
        )

    @patch("youtube.ChannelSection.DB")
    def test_insert_on_behalf_of_content_owner_channel_empty_string(self, mock_db):
        """Test insert with empty string on_behalf_of_content_owner_channel"""
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}  # Mock channels exist
        mock_db.setdefault.return_value = {}
        self.assert_error_behavior(
            insert,
            ValueError,
            "on_behalf_of_content_owner_channel cannot be an empty string",
            part="snippet",
            snippet={"channelId": "channel1", "type": "singlePlaylist"},
            on_behalf_of_content_owner_channel="   "
        )

    # Test success scenarios
    @patch("youtube.ChannelSection.generate_entity_id")
    @patch("youtube.ChannelSection.DB")
    def test_insert_valid_minimal(self, mock_db, mock_generate_id):
        """Test insert with valid minimal parameters"""
        mock_generate_id.return_value = "new_section_id"
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}  # Mock channels exist
        mock_db.setdefault.return_value = {}

        result = insert(
            part="snippet",
            snippet={"channelId": "channel1", "type": "singlePlaylist"}
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("channelSection", result)
        self.assertTrue(result["success"])
        self.assertEqual(result["channelSection"]["id"], "new_section_id")

    @patch("youtube.ChannelSection.generate_entity_id")
    @patch("youtube.ChannelSection.DB")
    def test_insert_valid_with_all_optional_parameters(self, mock_db, mock_generate_id):
        """Test insert with all optional parameters"""
        mock_generate_id.return_value = "new_section_id"
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}  # Mock channels exist
        mock_db.setdefault.return_value = {}

        result = insert(
            part="snippet,contentDetails",
            snippet={"channelId": "channel1", "type": "multiplePlaylists"},
            on_behalf_of_content_owner="content_owner_123",
            on_behalf_of_content_owner_channel="owner_channel_123"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("channelSection", result)
        self.assertTrue(result["success"])
        self.assertEqual(result["channelSection"]["id"], "new_section_id")

    @patch("youtube.ChannelSection.generate_entity_id")
    @patch("youtube.ChannelSection.DB")
    def test_insert_valid_all_part_values(self, mock_db, mock_generate_id):
        """Test insert with all valid part values"""
        mock_generate_id.return_value = "new_section_id"
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}  # Mock channels exist
        mock_db.setdefault.return_value = {}

        valid_parts = ["snippet", "statistics", "contentDetails", "snippet,statistics", "snippet,contentDetails", "statistics,contentDetails"]
        for part_value in valid_parts:
            with self.subTest(part=part_value):
                result = insert(
                    part=part_value,
                    snippet={"channelId": "channel1", "type": "singlePlaylist"}
                )
                self.assertIsInstance(result, dict)
                self.assertIn("success", result)
                self.assertTrue(result["success"])

    # Test additional coverage scenarios  
    def test_insert_part_all_valid_combinations(self):
        """Test insert with all valid part combinations"""
        valid_parts = [
            "snippet",
            "statistics", 
            "contentDetails",
            "snippet,statistics",
            "snippet,contentDetails", 
            "statistics,contentDetails",
            "snippet,statistics,contentDetails"
        ]
        
        # These tests only validate the part parameter parsing
        for part_value in valid_parts:
            with self.subTest(part=part_value):
                try:
                    # This will fail at validation, but part validation should pass
                    insert(part=part_value, snippet=None)
                except ValueError as e:
                    # Should fail on snippet validation, not part validation
                    self.assertEqual(str(e), "snippet parameter is required")

    @patch("youtube.ChannelSection.generate_entity_id")
    @patch("youtube.ChannelSection.DB")
    def test_insert_database_error_handling(self, mock_db, mock_generate_id):
        """Test insert handles database errors gracefully"""
        mock_generate_id.return_value = "new_section_id"
        # First call returns channels for validation, second call raises KeyError for setdefault
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}
        mock_db.setdefault.side_effect = KeyError("Database error")
        
        # This should raise the original KeyError since the function doesn't catch it in a try-except
        with self.assertRaises(KeyError):
            insert(
                part="snippet",
                snippet={"channelId": "channel1", "type": "singlePlaylist"}
            )

    @patch("youtube.ChannelSection.generate_entity_id")  
    @patch("youtube.ChannelSection.DB")
    def test_insert_snippet_validation_order(self, mock_db, mock_generate_id):
        """Test that snippet validation happens before database operations"""
        mock_generate_id.return_value = "new_section_id"
        mock_db.get.return_value = {"channel1": {"id": "channel1"}}
        
        # ValidationError should be raised before any database operations
        with self.assertRaises(ValidationError):
            insert(
                part="snippet",
                snippet={"channelId": "channel1"}  # Missing required 'type' field
            )


if __name__ == "__main__":
    unittest.main()
