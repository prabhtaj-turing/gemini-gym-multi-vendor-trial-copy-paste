import unittest
from pydantic import ValidationError
from youtube.Caption import delete, download, insert, list, update
from youtube.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCaptionDelete(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        DB.clear()
        DB["captions"] = {
            "caption1": {
                "id": "caption1",
                "snippet": {
                    "videoId": "video1",
                    "text": "Test caption text"
                },
                "sync": False
            },
            "caption2": {
                "id": "caption2",
                "snippet": {
                    "videoId": "video2",
                    "text": "Another caption text"
                },
                "sync": True,
                "onBehalfOf": "user1",
                "onBehalfOfContentOwner": "content_owner1"
            }
        }

    # Test id parameter validation
    def test_delete_id_none(self):
        """Test delete with None id"""
        self.assert_error_behavior(
            delete,
            ValueError,
            "ID parameter cannot be None.",
            id=None
        )

    def test_delete_id_not_string(self):
        """Test delete with non-string id"""
        self.assert_error_behavior(
            delete,
            TypeError,
            "ID parameter must be a string.",
            id=123
        )

    def test_delete_id_not_exists(self):
        """Test delete with non-existent id"""
        self.assert_error_behavior(
            delete,
            ValueError,
            "ID does not exist in the database.",
            id="nonexistent"
        )

    # Test success scenarios
    def test_delete_success(self):
        """Test successful deletion"""
        result = delete(id="caption1")
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        
        # Verify caption was actually deleted
        self.assertNotIn("caption1", DB["captions"])

    def test_delete_with_optional_parameters(self):
        """Test delete with optional parameters (should be ignored)"""
        result = delete(
            id="caption2",
            onBehalfOf="user1",
            onBehalfOfContentOwner="content_owner1"
        )
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        
        # Verify caption was actually deleted
        self.assertNotIn("caption2", DB["captions"])


class TestCaptionDownload(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        DB.clear()
        DB["captions"] = {
            "caption1": {
                "id": "caption1",
                "snippet": {
                    "videoId": "video1",
                    "text": "Test caption text"
                }
            }
        }

    # Test id parameter validation
    def test_download_id_none(self):
        """Test download with None id"""
        self.assert_error_behavior(
            download,
            ValueError,
            "Caption ID is required.",
            id=None
        )

    def test_download_id_not_string(self):
        """Test download with non-string id"""
        self.assert_error_behavior(
            download,
            TypeError,
            "Caption ID must be a string.",
            id=123
        )

    def test_download_id_not_found(self):
        """Test download with non-existent caption id"""
        self.assert_error_behavior(
            download,
            ValueError,
            "Caption not found",
            id="nonexistent"
        )

    # Test tfmt parameter validation
    def test_download_tfmt_not_string(self):
        """Test download with non-string tfmt"""
        self.assert_error_behavior(
            download,
            TypeError,
            "Format must be a string.",
            id="caption1",
            tfmt=123
        )

    def test_download_tfmt_unsupported(self):
        """Test download with unsupported tfmt"""
        self.assert_error_behavior(
            download,
            ValueError,
            "Unsupported tfmt format.",
            id="caption1",
            tfmt="unsupported_format"
        )

    # Test tlang parameter validation
    def test_download_tlang_not_string(self):
        """Test download with non-string tlang"""
        self.assert_error_behavior(
            download,
            TypeError,
            "Target language must be a string.",
            id="caption1",
            tlang=123
        )

    # Test onBehalfOf parameter validation
    def test_download_on_behalf_of_not_string(self):
        """Test download with non-string onBehalfOf"""
        self.assert_error_behavior(
            download,
            TypeError,
            "On behalf of must be a string.",
            id="caption1",
            onBehalfOf=123
        )

    def test_download_on_behalf_of_empty(self):
        """Test download with empty onBehalfOf"""
        self.assert_error_behavior(
            download,
            ValueError,
            "On behalf of cannot be empty or consist only of whitespace.",
            id="caption1",
            onBehalfOf="   "
        )

    # Test onBehalfOfContentOwner parameter validation
    def test_download_on_behalf_of_content_owner_not_string(self):
        """Test download with non-string onBehalfOfContentOwner"""
        self.assert_error_behavior(
            download,
            TypeError,
            "On behalf of content owner must be a string.",
            id="caption1",
            onBehalfOfContentOwner=123
        )

    def test_download_on_behalf_of_content_owner_empty(self):
        """Test download with empty onBehalfOfContentOwner"""
        self.assert_error_behavior(
            download,
            ValueError,
            "On behalf of content owner cannot be empty or consist only of whitespace.",
            id="caption1",
            onBehalfOfContentOwner="   "
        )

    # Test success scenarios
    def test_download_default_text(self):
        """Test download returning default caption text"""
        result = download(id="caption1")
        
        self.assertEqual(result, "Test caption text")

    def test_download_with_srt_format(self):
        """Test download with SRT format"""
        result = download(id="caption1", tfmt="srt")
        
        self.assertEqual(result, "SRT format caption content")

    def test_download_with_vtt_format(self):
        """Test download with VTT format"""
        result = download(id="caption1", tfmt="vtt")
        
        self.assertEqual(result, "WebVTT format caption content")

    def test_download_with_sbv_format(self):
        """Test download with SBV format"""
        result = download(id="caption1", tfmt="sbv")
        
        self.assertEqual(result, "SubViewer format caption content")

    def test_download_with_translation(self):
        """Test download with target language"""
        result = download(id="caption1", tlang="es")
        
        self.assertEqual(result, "Simulated translated caption to es")

    def test_download_with_valid_on_behalf_of(self):
        """Test download with valid onBehalfOf"""
        result = download(id="caption1", onBehalfOf="valid_user")
        
        self.assertEqual(result, "Test caption text")

    def test_download_with_valid_on_behalf_of_content_owner(self):
        """Test download with valid onBehalfOfContentOwner"""
        result = download(id="caption1", onBehalfOfContentOwner="valid_owner")
        
        self.assertEqual(result, "Test caption text")


class TestCaptionInsert(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        DB.clear()
        self.valid_snippet = {
            "videoId": "video1",
            "text": "Caption text content"
        }

    # Test part parameter validation
    def test_insert_part_not_string(self):
        """Test insert with non-string part"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "Parameter 'part' must be a string.",
            part=123,
            snippet=self.valid_snippet,
            sync=False
        )

    def test_insert_part_empty(self):
        """Test insert with empty part"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Part parameter cannot be empty or consist only of whitespace.",
            part="   ",
            snippet=self.valid_snippet,
            sync=False
        )

    def test_insert_part_invalid(self):
        """Test insert with invalid part parameter"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Part parameter must be 'snippet'.",
            part="invalid",
            snippet=self.valid_snippet,
            sync=False
        )

    # Test sync parameter validation
    def test_insert_sync_none(self):
        """Test insert with None sync (required parameter)"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Sync parameter is required.",
            part="snippet",
            snippet=self.valid_snippet,
            sync=None
        )

    def test_insert_sync_not_boolean(self):
        """Test insert with non-boolean sync"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "Parameter 'sync' must be a boolean.",
            part="snippet",
            snippet=self.valid_snippet,
            sync="not_boolean"
        )



    # Test snippet parameter validation
    def test_insert_snippet_none(self):
        """Test insert with None snippet"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "Snippet parameter cannot be None.",
            part="snippet",
            snippet=None,
            sync=False
        )

    # Test onBehalfOf parameter validation
    def test_insert_on_behalf_of_not_string(self):
        """Test insert with non-string onBehalfOf"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "On behalf of must be a string.",
            part="snippet",
            snippet=self.valid_snippet,
            sync=False,
            onBehalfOf=123
        )

    # Test onBehalfOfContentOwner parameter validation
    def test_insert_on_behalf_of_content_owner_not_string(self):
        """Test insert with non-string onBehalfOfContentOwner"""
        self.assert_error_behavior(
            insert,
            TypeError,
            "On behalf of content owner must be a string.",
            part="snippet",
            snippet=self.valid_snippet,
            sync=False,
            onBehalfOfContentOwner=123
        )

    # Test Pydantic ValidationError scenarios for snippet
    def test_insert_snippet_missing_videoId(self):
        """Test insert with snippet missing videoId - should raise ValidationError"""
        invalid_snippet = {"text": "Caption text"}
        
        with self.assertRaises(ValidationError) as context:
            insert(part="snippet", snippet=invalid_snippet, sync=False)
        
        error_message = str(context.exception)
        self.assertIn("videoId", error_message)
        self.assertTrue("required" in error_message or "missing" in error_message)

    def test_insert_snippet_missing_text(self):
        """Test insert with snippet missing text - should raise ValidationError"""
        invalid_snippet = {"videoId": "video1"}
        
        with self.assertRaises(ValidationError) as context:
            insert(part="snippet", snippet=invalid_snippet, sync=False)
        
        error_message = str(context.exception)
        self.assertIn("text", error_message)
        self.assertTrue("required" in error_message or "missing" in error_message)

    def test_insert_snippet_empty_videoId(self):
        """Test insert with empty videoId in snippet - should raise ValidationError"""
        invalid_snippet = {"videoId": "   ", "text": "Caption text"}
        
        with self.assertRaises(ValidationError) as context:
            insert(part="snippet", snippet=invalid_snippet, sync=False)
        
        error_message = str(context.exception)
        self.assertIn("videoId must be a non-empty string", error_message)

    def test_insert_snippet_empty_text(self):
        """Test insert with empty text in snippet - should raise ValidationError"""
        invalid_snippet = {"videoId": "video1", "text": "   "}
        
        with self.assertRaises(ValidationError) as context:
            insert(part="snippet", snippet=invalid_snippet, sync=False)
        
        error_message = str(context.exception)
        self.assertIn("text must be a non-empty string", error_message)

    def test_insert_snippet_non_string_videoId(self):
        """Test insert with non-string videoId in snippet - should raise ValidationError"""
        invalid_snippet = {"videoId": 123, "text": "Caption text"}
        
        with self.assertRaises(ValidationError) as context:
            insert(part="snippet", snippet=invalid_snippet, sync=False)
        
        error_message = str(context.exception)
        # More flexible error message checking for Pydantic v2
        self.assertTrue(
            "videoId must be a non-empty string" in error_message or 
            "Input should be a valid string" in error_message or
            "str" in error_message.lower()
        )

    def test_insert_snippet_non_string_text(self):
        """Test insert with non-string text in snippet - should raise ValidationError"""
        invalid_snippet = {"videoId": "video1", "text": 123}
        
        with self.assertRaises(ValidationError) as context:
            insert(part="snippet", snippet=invalid_snippet, sync=False)
        
        error_message = str(context.exception)
        # More flexible error message checking for Pydantic v2
        self.assertTrue(
            "text must be a non-empty string" in error_message or 
            "Input should be a valid string" in error_message or
            "str" in error_message.lower()
        )

    def test_insert_snippet_extra_fields(self):
        """Test insert with extra fields in snippet - should raise ValidationError"""
        invalid_snippet = {
            "videoId": "video1", 
            "text": "Caption text",
            "invalidField": "invalid"
        }
        
        with self.assertRaises(ValidationError) as context:
            insert(part="snippet", snippet=invalid_snippet, sync=False)
        
        error_message = str(context.exception)
        self.assertTrue("extra" in error_message.lower() or "forbidden" in error_message.lower())

    # Test onBehalfOf empty string validation (after snippet validation)
    def test_insert_on_behalf_of_empty_first_check(self):
        """Test insert with empty onBehalfOf (first validation)"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "On behalf of cannot be empty or consist only of whitespace.",
            part="snippet",
            snippet=self.valid_snippet,
            sync=False,
            onBehalfOf="   "
        )

    def test_insert_on_behalf_of_content_owner_empty_first_check(self):
        """Test insert with empty onBehalfOfContentOwner (first validation)"""
        self.assert_error_behavior(
            insert,
            ValueError,
            "On behalf of content owner cannot be empty or consist only of whitespace.",
            part="snippet",
            snippet=self.valid_snippet,
            sync=False,
            onBehalfOfContentOwner="   "
        )

    # Test success scenarios
    def test_insert_success_minimal(self):
        """Test successful insert with minimal parameters"""
        result = insert(
            part="snippet",
            snippet=self.valid_snippet,
            sync=False
        )
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertIn("caption", result)
        self.assertIn("id", result["caption"])
        self.assertEqual(result["caption"]["snippet"]["videoId"], "video1")
        self.assertEqual(result["caption"]["snippet"]["text"], "Caption text content")
        self.assertFalse(result["caption"]["sync"])
        
        # Verify caption was added to DB
        caption_id = result["caption"]["id"]
        self.assertIn(caption_id, DB["captions"])

    def test_insert_success_with_sync_true(self):
        """Test successful insert with sync=True"""
        result = insert(
            part="snippet",
            snippet=self.valid_snippet,
            sync=True
        )
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertTrue(result["caption"]["sync"])

    def test_insert_success_with_all_optional_parameters(self):
        """Test successful insert with all optional parameters"""
        result = insert(
            part="snippet",
            snippet=self.valid_snippet,
            sync=True,
            onBehalfOf="valid_user",
            onBehalfOfContentOwner="valid_owner"
        )
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertEqual(result["caption"]["onBehalfOf"], "valid_user")
        self.assertEqual(result["caption"]["onBehalfOfContentOwner"], "valid_owner")
        self.assertTrue(result["caption"]["sync"])


class TestCaptionList(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        DB.clear()
        DB["videos"] = {
            "video1": {"id": "video1", "title": "Test Video 1"},
            "video2": {"id": "video2", "title": "Test Video 2"}
        }
        DB["captions"] = {
            "caption1": {
                "id": "caption1",
                "snippet": {
                    "videoId": "video1",
                    "text": "Caption 1 text"
                }
            },
            "caption2": {
                "id": "caption2",
                "snippet": {
                    "videoId": "video1",
                    "text": "Caption 2 text"
                },
                "onBehalfOf": "user1"
            },
            "caption3": {
                "id": "caption3",
                "snippet": {
                    "videoId": "video2",
                    "text": "Caption 3 text"
                },
                "onBehalfOfContentOwner": "owner1"
            }
        }

    # Test part parameter validation
    def test_list_part_none(self):
        """Test list with None part"""
        self.assert_error_behavior(
            list,
            ValueError,
            "Part parameter cannot be None.",
            part=None,
            videoId="video1"
        )

    def test_list_part_not_string(self):
        """Test list with non-string part"""
        self.assert_error_behavior(
            list,
            TypeError,
            "Part parameter must be a string.",
            part=123,
            videoId="video1"
        )

    def test_list_part_invalid(self):
        """Test list with invalid part parameter"""
        self.assert_error_behavior(
            list,
            ValueError,
            "Invalid part parameter",
            part="invalid",
            videoId="video1"
        )

    # Test videoId parameter validation
    def test_list_video_id_none(self):
        """Test list with None videoId"""
        self.assert_error_behavior(
            list,
            ValueError,
            "Video ID cannot be None.",
            part="snippet",
            videoId=None
        )

    def test_list_video_id_not_string(self):
        """Test list with non-string videoId"""
        self.assert_error_behavior(
            list,
            TypeError,
            "Video ID must be a string.",
            part="snippet",
            videoId=123
        )

    def test_list_video_id_not_exists(self):
        """Test list with non-existent videoId"""
        self.assert_error_behavior(
            list,
            ValueError,
            "Video ID does not exist in the database.",
            part="snippet",
            videoId="nonexistent"
        )

    # Test id parameter validation
    def test_list_id_not_string(self):
        """Test list with non-string id"""
        self.assert_error_behavior(
            list,
            TypeError,
            "ID must be a string.",
            part="snippet",
            videoId="video1",
            id=123
        )

    def test_list_id_not_exists(self):
        """Test list with non-existent id"""
        self.assert_error_behavior(
            list,
            ValueError,
            "ID does not exist in the database.",
            part="snippet",
            videoId="video1",
            id="nonexistent"
        )

    # Test onBehalfOf parameter validation
    def test_list_on_behalf_of_not_string(self):
        """Test list with non-string onBehalfOf"""
        self.assert_error_behavior(
            list,
            TypeError,
            "On behalf of must be a string.",
            part="snippet",
            videoId="video1",
            onBehalfOf=123
        )

    def test_list_on_behalf_of_empty(self):
        """Test list with empty onBehalfOf"""
        self.assert_error_behavior(
            list,
            ValueError,
            "On behalf of cannot be empty or consist only of whitespace.",
            part="snippet",
            videoId="video1",
            onBehalfOf="   "
        )

    # Test onBehalfOfContentOwner parameter validation
    def test_list_on_behalf_of_content_owner_not_string(self):
        """Test list with non-string onBehalfOfContentOwner"""
        self.assert_error_behavior(
            list,
            TypeError,
            "On behalf of content owner must be a string.",
            part="snippet",
            videoId="video1",
            onBehalfOfContentOwner=123
        )

    def test_list_on_behalf_of_content_owner_empty(self):
        """Test list with empty onBehalfOfContentOwner"""
        self.assert_error_behavior(
            list,
            ValueError,
            "On behalf of content owner cannot be empty or consist only of whitespace.",
            part="snippet",
            videoId="video1",
            onBehalfOfContentOwner="   "
        )

    # Test success scenarios
    def test_list_success_snippet_part(self):
        """Test successful list with snippet part"""
        result = list(part="snippet", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)
        
        # Check that we get snippet data
        for item in result["items"]:
            self.assertIn("snippet", item)
            self.assertNotIn("id", item)
            self.assertEqual(item["snippet"]["videoId"], "video1")

    def test_list_success_id_part(self):
        """Test successful list with id part"""
        result = list(part="id", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)
        
        # Check that we get id data
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertNotIn("snippet", item)

    def test_list_success_with_specific_id(self):
        """Test successful list with specific caption id"""
        result = list(part="snippet", videoId="video1", id="caption1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["snippet"]["text"], "Caption 1 text")

    def test_list_success_with_on_behalf_of_filter(self):
        """Test successful list with onBehalfOf filter"""
        result = list(part="snippet", videoId="video1", onBehalfOf="user1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["snippet"]["text"], "Caption 2 text")

    def test_list_success_with_on_behalf_of_content_owner_filter(self):
        """Test successful list with onBehalfOfContentOwner filter"""
        result = list(part="snippet", videoId="video2", onBehalfOfContentOwner="owner1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["snippet"]["text"], "Caption 3 text")

    def test_list_success_case_insensitive_part(self):
        """Test successful list with case insensitive part"""
        result = list(part="SNIPPET", videoId="video1")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)

    def test_list_success_empty_results(self):
        """Test successful list with no matching captions"""
        result = list(part="snippet", videoId="video2", onBehalfOf="nonexistent_user")
        
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)


class TestCaptionUpdate(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data"""
        DB.clear()
        DB["captions"] = {
            "caption1": {
                "id": "caption1",
                "snippet": {
                    "videoId": "video1",
                    "text": "Original caption text"
                },
                "sync": False
            }
        }

    # Test part parameter validation
    def test_update_part_none(self):
        """Test update with None part"""
        self.assert_error_behavior(
            update,
            ValueError,
            "Part parameter cannot be None.",
            part=None,
            id="caption1"
        )

    def test_update_part_not_string(self):
        """Test update with non-string part"""
        self.assert_error_behavior(
            update,
            TypeError,
            "Part parameter must be a string.",
            part=123,
            id="caption1"
        )

    def test_update_part_invalid(self):
        """Test update with invalid part parameter"""
        self.assert_error_behavior(
            update,
            ValueError,
            "Invalid 'part' parameter. Expected 'snippet'.",
            part="invalid",
            id="caption1"
        )

    # Test id parameter validation
    def test_update_id_none(self):
        """Test update with None id"""
        self.assert_error_behavior(
            update,
            ValueError,
            "ID parameter cannot be None.",
            part="snippet",
            id=None
        )

    def test_update_id_not_string(self):
        """Test update with non-string id"""
        self.assert_error_behavior(
            update,
            TypeError,
            "ID parameter must be a string.",
            part="snippet",
            id=123
        )

    def test_update_id_not_exists(self):
        """Test update with non-existent id"""
        self.assert_error_behavior(
            update,
            ValueError,
            "ID does not exist in the database.",
            part="snippet",
            id="nonexistent"
        )

    # Test onBehalfOf parameter validation
    def test_update_on_behalf_of_not_string(self):
        """Test update with non-string onBehalfOf"""
        self.assert_error_behavior(
            update,
            TypeError,
            "On behalf of must be a string.",
            part="snippet",
            id="caption1",
            onBehalfOf=123
        )

    def test_update_on_behalf_of_empty(self):
        """Test update with empty onBehalfOf"""
        self.assert_error_behavior(
            update,
            ValueError,
            "On behalf of cannot be empty or consist only of whitespace.",
            part="snippet",
            id="caption1",
            onBehalfOf="   "
        )

    # Test onBehalfOfContentOwner parameter validation
    def test_update_on_behalf_of_content_owner_not_string(self):
        """Test update with non-string onBehalfOfContentOwner"""
        self.assert_error_behavior(
            update,
            TypeError,
            "On behalf of content owner must be a string.",
            part="snippet",
            id="caption1",
            onBehalfOfContentOwner=123
        )

    def test_update_on_behalf_of_content_owner_empty(self):
        """Test update with empty onBehalfOfContentOwner"""
        self.assert_error_behavior(
            update,
            ValueError,
            "On behalf of content owner cannot be empty or consist only of whitespace.",
            part="snippet",
            id="caption1",
            onBehalfOfContentOwner="   "
        )

    # Test sync parameter validation
    def test_update_sync_not_boolean(self):
        """Test update with non-boolean sync"""
        self.assert_error_behavior(
            update,
            TypeError,
            "Parameter 'sync' must be a boolean.",
            part="snippet",
            id="caption1",
            sync="not_boolean"
        )

    # Test Pydantic ValidationError scenarios for snippet
    def test_update_snippet_empty_videoId(self):
        """Test update with empty videoId in snippet - should raise ValidationError"""
        invalid_snippet = {"videoId": "   "}
        
        with self.assertRaises(ValidationError) as context:
            update(part="snippet", id="caption1", snippet=invalid_snippet)
        
        error_message = str(context.exception)
        self.assertIn("videoId must be a non-empty string", error_message)

    def test_update_snippet_empty_text(self):
        """Test update with empty text in snippet - should raise ValidationError"""
        invalid_snippet = {"text": "   "}
        
        with self.assertRaises(ValidationError) as context:
            update(part="snippet", id="caption1", snippet=invalid_snippet)
        
        error_message = str(context.exception)
        self.assertIn("text must be a non-empty string", error_message)

    def test_update_snippet_non_string_videoId(self):
        """Test update with non-string videoId in snippet - should raise ValidationError"""
        invalid_snippet = {"videoId": 123}
        
        with self.assertRaises(ValidationError) as context:
            update(part="snippet", id="caption1", snippet=invalid_snippet)
        
        error_message = str(context.exception)
        # More flexible error message checking for Pydantic v2
        self.assertTrue(
            "videoId must be a non-empty string" in error_message or 
            "Input should be a valid string" in error_message or
            "str" in error_message.lower()
        )

    def test_update_snippet_non_string_text(self):
        """Test update with non-string text in snippet - should raise ValidationError"""
        invalid_snippet = {"text": 123}
        
        with self.assertRaises(ValidationError) as context:
            update(part="snippet", id="caption1", snippet=invalid_snippet)
        
        error_message = str(context.exception)
        # More flexible error message checking for Pydantic v2
        self.assertTrue(
            "text must be a non-empty string" in error_message or 
            "Input should be a valid string" in error_message or
            "str" in error_message.lower()
        )

    def test_update_snippet_extra_fields(self):
        """Test update with extra fields in snippet - should raise ValidationError"""
        invalid_snippet = {
            "videoId": "video1", 
            "text": "Updated text",
            "invalidField": "invalid"
        }
        
        with self.assertRaises(ValidationError) as context:
            update(part="snippet", id="caption1", snippet=invalid_snippet)
        
        error_message = str(context.exception)
        self.assertTrue("extra" in error_message.lower() or "forbidden" in error_message.lower())

    # Test success scenarios
    def test_update_success_no_snippet(self):
        """Test successful update with no snippet changes"""
        result = update(part="snippet", id="caption1")
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Caption updated.")

    def test_update_success_with_snippet(self):
        """Test successful update with snippet changes"""
        snippet_update = {"text": "Updated caption text"}
        
        result = update(part="snippet", id="caption1", snippet=snippet_update)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Caption updated.")
        
        # Verify the caption was actually updated
        self.assertEqual(DB["captions"]["caption1"]["snippet"]["text"], "Updated caption text")

    def test_update_success_with_all_parameters(self):
        """Test successful update with all optional parameters"""
        snippet_update = {"videoId": "video2", "text": "Updated caption text"}
        
        result = update(
            part="snippet",
            id="caption1",
            snippet=snippet_update,
            onBehalfOf="valid_user",
            onBehalfOfContentOwner="valid_owner",
            sync=True
        )
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Caption updated.")
        
        # Verify all fields were updated
        caption = DB["captions"]["caption1"]
        self.assertEqual(caption["snippet"]["videoId"], "video2")
        self.assertEqual(caption["snippet"]["text"], "Updated caption text")
        self.assertEqual(caption["onBehalfOf"], "valid_user")
        self.assertEqual(caption["onBehalfOfContentOwner"], "valid_owner")
        self.assertTrue(caption["sync"])

    def test_update_success_case_insensitive_part(self):
        """Test successful update with case insensitive part"""
        result = update(part="SNIPPET", id="caption1")
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])

    def test_update_success_partial_snippet_update(self):
        """Test successful update with partial snippet update (only text)"""
        # Only update text, leave videoId unchanged
        snippet_update = {"text": "Only text updated"}
        
        result = update(part="snippet", id="caption1", snippet=snippet_update)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        
        # Verify only text was updated, videoId remains unchanged
        caption = DB["captions"]["caption1"]
        self.assertEqual(caption["snippet"]["text"], "Only text updated")
        self.assertEqual(caption["snippet"]["videoId"], "video1")  # Should remain unchanged

    def test_update_success_partial_snippet_update_videoId_only(self):
        """Test successful update with partial snippet update (only videoId)"""
        # Only update videoId, leave text unchanged
        snippet_update = {"videoId": "new_video_id"}
        
        result = update(part="snippet", id="caption1", snippet=snippet_update)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        
        # Verify only videoId was updated, text remains unchanged
        caption = DB["captions"]["caption1"]
        self.assertEqual(caption["snippet"]["videoId"], "new_video_id")
        self.assertEqual(caption["snippet"]["text"], "Original caption text")  # Should remain unchanged


if __name__ == '__main__':
    unittest.main()
