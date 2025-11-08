import pytest
import unittest
from youtube.SimulationEngine.db import DB
from youtube.Caption import list as caption_list
from youtube.SimulationEngine.error_handling import get_package_error_mode
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCaptionList(BaseTestCaseWithErrorHandler):
    """Test class for Caption.list method with comprehensive error coverage."""

    def setUp(self):
        """Set up test data before each test."""
        DB.clear()
        DB["videos"] = {
            "video1": {
                "id": "video1",
                "snippet": {
                    "title": "Test Video 1",
                    "channelId": "channel1"
                }
            },
            "video2": {
                "id": "video2", 
                "snippet": {
                    "title": "Test Video 2",
                    "channelId": "channel2"
                }
            }
        }
        DB["captions"] = {
            "caption1": {
                "id": "caption1",
                "snippet": {
                    "videoId": "video1"
                  
                }
            },
            "caption2": {
                "id": "caption2",
                "snippet": {
                    "videoId": "video1"
                
                }
            },
            "caption3": {
                "id": "caption3",
                "snippet": {
                    "videoId": "video2",
                   
                }
            }
        }

    # ========== SUCCESS TESTS ==========

    def test_list_captions_with_snippet_part_success(self):
        """Test successful caption listing with snippet part."""
        result = caption_list(part="snippet", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)  # Two captions for video1
        
        # Check that items contain snippet data
        for item in result["items"]:
            self.assertIn("snippet", item)
            self.assertEqual(item["snippet"]["videoId"], "video1")

    def test_list_captions_with_id_part_success(self):
        """Test successful caption listing with id part."""
        result = caption_list(part="id", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)  # Two captions for video1
        
        # Check that items contain only ID data
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertNotIn("snippet", item)

    def test_list_captions_with_specific_caption_id_success(self):
        """Test successful caption listing with specific caption ID filter."""
        result = caption_list(part="snippet", videoId="video1", id="caption1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)  # Only one caption filtered
        self.assertEqual(result["items"][0]["snippet"]["videoId"], "video1")

    def test_list_captions_empty_result_success(self):
        """Test successful caption listing when no captions exist for video."""
        # Add a video with no captions
        DB["videos"]["video3"] = {
            "id": "video3",
            "snippet": {"title": "Video with no captions"}
        }
        
        result = caption_list(part="snippet", videoId="video3")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)  # No captions for video3

    def test_list_captions_with_case_insensitive_part_success(self):
        """Test that part parameter is case insensitive."""
        result1 = caption_list(part="SNIPPET", videoId="video1")
        result2 = caption_list(part="ID", videoId="video1")
        
        self.assertIsInstance(result1, dict)
        self.assertIsInstance(result2, dict)
        self.assertIn("items", result1)
        self.assertIn("items", result2)

    # ========== ERROR TESTS - PART PARAMETER ==========

    def test_list_captions_part_none_error(self):
        """Test that None part parameter raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Part parameter cannot be None.",
            None,
            part=None,
            videoId="video1"
        )

    def test_list_captions_part_invalid_type_error(self):
        """Test that non-string part parameter raises TypeError."""
        self.assert_error_behavior(
            caption_list,
            TypeError,
            "Part parameter must be a string.",
            None,
            part=123,
            videoId="video1"
        )

    def test_list_captions_part_invalid_value_error(self):
        """Test that invalid part parameter raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Invalid part parameter",
            None,
            part="invalid",
            videoId="video1"
        )

    def test_list_captions_part_empty_string_error(self):
        """Test that empty part parameter raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Invalid part parameter",
            None,
            part="",
            videoId="video1"
        )

    def test_list_captions_part_whitespace_only_error(self):
        """Test that whitespace-only part parameter raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Invalid part parameter",
            None,
            part="   ",
            videoId="video1"
        )

    # ========== ERROR TESTS - VIDEO ID PARAMETER ==========

    def test_list_captions_video_id_none_error(self):
        """Test that None videoId parameter raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Video ID cannot be None.",
            None,
            part="snippet",
            videoId=None
        )

    def test_list_captions_video_id_invalid_type_error(self):
        """Test that non-string videoId parameter raises TypeError."""
        self.assert_error_behavior(
            caption_list,
            TypeError,
            "Video ID must be a string.",
            None,
            part="snippet",
            videoId=123
        )

    def test_list_captions_video_id_not_exist_error(self):
        """Test that non-existent videoId raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Video ID does not exist in the database.",
            None,
            part="snippet",
            videoId="nonexistent_video"
        )

    def test_list_captions_video_id_empty_string_error(self):
        """Test that empty videoId raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Video ID does not exist in the database.",
            None,
            part="snippet",
            videoId=""
        )

    def test_list_captions_video_id_whitespace_only_error(self):
        """Test that whitespace-only videoId raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Video ID does not exist in the database.",
            None,
            part="snippet",
            videoId="   "
        )

    # ========== ERROR TESTS - ID PARAMETER ==========

    def test_list_captions_id_invalid_type_error(self):
        """Test that non-string id parameter raises TypeError."""
        self.assert_error_behavior(
            caption_list,
            TypeError,
            "ID must be a string.",
            None,
            part="snippet",
            videoId="video1",
            id=123
        )

    def test_list_captions_id_not_exist_error(self):
        """Test that non-existent id raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "ID does not exist in the database.",
            None,
            part="snippet",
            videoId="video1",
            id="nonexistent_caption"
        )

    def test_list_captions_id_empty_string_error(self):
        """Test that empty id raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "ID does not exist in the database.",
            None,
            part="snippet",
            videoId="video1",
            id=""
        )

    def test_list_captions_id_whitespace_only_error(self):
        """Test that whitespace-only id raises ValueError."""
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "ID does not exist in the database.",
            None,
            part="snippet",
            videoId="video1",
            id="   "
        )

    # ========== ERROR TESTS - ONBEHALFOF PARAMETER ==========

    def test_list_captions_on_behalf_of_invalid_type_error(self):
        """Test that non-string onBehalfOf parameter raises TypeError."""
        self.assert_error_behavior(
            caption_list,
            TypeError,
            "On behalf of must be a string.",
            None,
            part="snippet",
            videoId="video1",
            onBehalfOf=123
        )

    # ========== ERROR TESTS - ONBEHALFOFCONTENTOWNER PARAMETER ==========

    def test_list_captions_on_behalf_of_content_owner_invalid_type_error(self):
        """Test that non-string onBehalfOfContentOwner parameter raises TypeError."""
        self.assert_error_behavior(
            caption_list,
            TypeError,
            "On behalf of content owner must be a string.",
            None,
            part="snippet",
            videoId="video1",
            onBehalfOfContentOwner=123
        )

    # ========== EDGE CASE TESTS ==========

    def test_list_captions_empty_captions_database(self):
        """Test listing captions when captions database is empty."""
        DB["captions"] = {}
        
        result = caption_list(part="snippet", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)

    def test_list_captions_missing_captions_key_in_db(self):
        """Test listing captions when captions key is missing from DB."""
        del DB["captions"]
        
        result = caption_list(part="snippet", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)

    def test_list_captions_with_valid_optional_parameters(self):
        """Test that valid optional string parameters work correctly."""
        result = caption_list(
            part="snippet",
            videoId="video1",
            onBehalfOf="test_user",
            onBehalfOfContentOwner="test_owner"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        # Function should still work with valid optional parameters

    def test_list_captions_case_insensitive_video_id_lookup(self):
        """Test that videoId lookup is case sensitive (as it should be)."""
        # This tests the current behavior - video IDs are case sensitive
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "Video ID does not exist in the database.",
            None,
            part="snippet",
            videoId="VIDEO1"  # Different case
        )

    def test_list_captions_case_insensitive_id_lookup(self):
        """Test that caption ID lookup is case sensitive (as it should be)."""
        # This tests the current behavior - caption IDs are case sensitive
        self.assert_error_behavior(
            caption_list,
            ValueError,
            "ID does not exist in the database.",
            None,
            part="snippet",
            videoId="video1",
            id="CAPTION1"  # Different case
        )

    def test_list_captions_snippet_structure(self):
        """Test that returned snippet contains expected structure."""
        result = caption_list(part="snippet", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        
        for item in result["items"]:
            self.assertIn("snippet", item)
            snippet = item["snippet"]
            self.assertIn("videoId", snippet)
            self.assertEqual(snippet["videoId"], "video1")

    def test_list_captions_id_structure(self):
        """Test that returned id items contain expected structure."""
        result = caption_list(part="id", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertIsInstance(item["id"], str)
            self.assertNotIn("snippet", item)

    def test_list_captions_multiple_videos_isolation(self):
        """Test that captions are properly isolated by video ID."""
        result_video1 = caption_list(part="snippet", videoId="video1")
        result_video2 = caption_list(part="snippet", videoId="video2")
        
        # video1 should have 2 captions
        self.assertEqual(len(result_video1["items"]), 2)
        # video2 should have 1 caption
        self.assertEqual(len(result_video2["items"]), 1)
        
        # Verify videoId in returned items
        for item in result_video1["items"]:
            self.assertEqual(item["snippet"]["videoId"], "video1")
        for item in result_video2["items"]:
            self.assertEqual(item["snippet"]["videoId"], "video2")


if __name__ == "__main__":
    unittest.main()