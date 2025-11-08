"""
Test suite for model classes in the YouTube API simulation.
Covers all Pydantic models from SimulationEngine/models.py with comprehensive validation tests.
"""
import unittest
from datetime import datetime
from typing import Dict, List, Any

from pydantic import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube.SimulationEngine.models import (
    SnippetInputModel,
    ThumbnailObjectModel,
    ThumbnailInputModel,
    TopLevelCommentInputModel,
    ThumbnailRecordUploadModel,
    ThumbnailsUploadModel,
    SnippetUploadModel,
    StatusUploadModel,
    VideoUploadModel
)


class TestSnippetInputModel(BaseTestCaseWithErrorHandler):
    """Test SnippetInputModel validation and functionality."""

    def test_snippet_input_model_allows_extra_fields(self):
        """Test SnippetInputModel allows arbitrary fields (extra='allow')."""
        data_with_extra = {
            "title": "Test Video Title",
            "description": "This is a test video description",
            "tags": ["test", "video", "youtube"],
            "categoryId": "22",
            "customField": "custom_value",
            "anotherField": 123
        }
        
        model = SnippetInputModel(**data_with_extra)
        
        # Should allow extra fields due to ConfigDict(extra="allow")
        self.assertEqual(model.title, "Test Video Title")
        self.assertEqual(model.description, "This is a test video description")
        self.assertEqual(model.customField, "custom_value")
        self.assertEqual(model.anotherField, 123)

    def test_snippet_input_model_empty_data(self):
        """Test SnippetInputModel with no data."""
        model = SnippetInputModel()
        
        # Should work since all fields are allowed but not required
        self.assertIsInstance(model, SnippetInputModel)

    def test_snippet_input_model_unicode_content(self):
        """Test SnippetInputModel with Unicode content."""
        unicode_data = {
            "title": "测试视频标题 🎥",
            "description": "这是一个测试视频描述 with emojis 🎬🎞️",
            "tags": ["测试", "视频", "中文", "unicode"],
            "language": "zh-CN"
        }
        
        model = SnippetInputModel(**unicode_data)
        
        self.assertEqual(model.title, "测试视频标题 🎥")
        self.assertEqual(model.description, "这是一个测试视频描述 with emojis 🎬🎞️")
        self.assertEqual(model.tags, ["测试", "视频", "中文", "unicode"])

    def test_snippet_input_model_various_data_types(self):
        """Test SnippetInputModel with various data types."""
        mixed_data = {
            "string_field": "text",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True,
            "list_field": [1, 2, 3],
            "dict_field": {"nested": "value"},
            "none_field": None
        }
        
        model = SnippetInputModel(**mixed_data)
        
        self.assertEqual(model.string_field, "text")
        self.assertEqual(model.int_field, 42)
        self.assertEqual(model.float_field, 3.14)
        self.assertTrue(model.bool_field)
        self.assertEqual(model.list_field, [1, 2, 3])
        self.assertEqual(model.dict_field, {"nested": "value"})
        self.assertIsNone(model.none_field)


class TestThumbnailObjectModel(BaseTestCaseWithErrorHandler):
    """Test ThumbnailObjectModel validation and functionality."""

    def test_thumbnail_object_model_valid_data(self):
        """Test ThumbnailObjectModel with valid data."""
        valid_data = {
            "url": "https://example.com/thumbnail.jpg",
            "width": 1280,
            "height": 720
        }
        
        model = ThumbnailObjectModel(**valid_data)
        
        self.assertEqual(model.url, "https://example.com/thumbnail.jpg")
        self.assertEqual(model.width, 1280)
        self.assertEqual(model.height, 720)

    def test_thumbnail_object_model_url_validation(self):
        """Test ThumbnailObjectModel URL validation."""
        # Test with various URL formats
        valid_urls = [
            "https://example.com/image.jpg",
            "http://test.com/thumb.png",
            "https://cdn.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                model = ThumbnailObjectModel(url=url, width=640, height=480)
                self.assertEqual(model.url, url)

    def test_thumbnail_object_model_dimension_validation(self):
        """Test ThumbnailObjectModel dimension validation."""
        # Test with various valid dimensions
        valid_dimensions = [
            (320, 240),    # Small
            (640, 480),    # Medium
            (1280, 720),   # HD
            (1920, 1080),  # Full HD
            (3840, 2160)   # 4K
        ]
        
        for width, height in valid_dimensions:
            with self.subTest(width=width, height=height):
                model = ThumbnailObjectModel(
                    url="https://example.com/thumb.jpg",
                    width=width,
                    height=height
                )
                self.assertEqual(model.width, width)
                self.assertEqual(model.height, height)

    def test_thumbnail_object_model_negative_dimensions(self):
        """Test ThumbnailObjectModel with negative dimensions."""
        # Note: The actual model doesn't validate negative dimensions
        # This test demonstrates the current behavior
        model_negative_width = ThumbnailObjectModel(
            url="https://example.com/thumb.jpg",
            width=-1,
            height=480
        )
        self.assertEqual(model_negative_width.width, -1)
        
        model_negative_height = ThumbnailObjectModel(
            url="https://example.com/thumb.jpg",
            width=640,
            height=-1
        )
        self.assertEqual(model_negative_height.height, -1)


class TestThumbnailInputModel(BaseTestCaseWithErrorHandler):
    """Test ThumbnailInputModel validation and functionality."""

    def test_thumbnail_input_model_valid_data(self):
        """Test ThumbnailInputModel with valid thumbnail objects."""
        valid_data = {
            "default": ThumbnailObjectModel(
                url="https://example.com/default.jpg",
                width=120,
                height=90
            ),
            "medium": ThumbnailObjectModel(
                url="https://example.com/medium.jpg", 
                width=320,
                height=180
            ),
            "high": ThumbnailObjectModel(
                url="https://example.com/high.jpg",
                width=480,
                height=360
            )
        }
        
        model = ThumbnailInputModel(**valid_data)
        
        self.assertIsInstance(model.default, ThumbnailObjectModel)
        self.assertIsInstance(model.medium, ThumbnailObjectModel)
        self.assertIsInstance(model.high, ThumbnailObjectModel)
        
        self.assertEqual(model.default.width, 120)
        self.assertEqual(model.medium.width, 320)
        self.assertEqual(model.high.width, 480)

    def test_thumbnail_input_model_missing_required_fields(self):
        """Test ThumbnailInputModel validation with missing required fields."""
        # All three fields are required based on the actual model
        with self.assertRaises(ValidationError):
            ThumbnailInputModel(
                default=ThumbnailObjectModel(
                    url="https://example.com/default.jpg",
                    width=120,
                    height=90
                )
                # Missing medium and high - should raise ValidationError
            )

    def test_thumbnail_input_model_all_fields_required(self):
        """Test that ThumbnailInputModel requires all three thumbnail sizes."""
        # Test that all fields are required
        with self.assertRaises(ValidationError):
            ThumbnailInputModel()  # No data provided


class TestTopLevelCommentInputModel(BaseTestCaseWithErrorHandler):
    """Test TopLevelCommentInputModel validation and functionality."""

    def test_top_level_comment_input_model_with_id(self):
        """Test TopLevelCommentInputModel with optional id field."""
        data_with_id = {
            "id": "comment_123",
            "textDisplay": "This is a great video!",
            "authorDisplayName": "TestUser",
            "videoId": "dQw4w9WgXcQ"
        }
        
        model = TopLevelCommentInputModel(**data_with_id)
        
        self.assertEqual(model.id, "comment_123")
        self.assertEqual(model.textDisplay, "This is a great video!")
        self.assertEqual(model.authorDisplayName, "TestUser")
        self.assertEqual(model.videoId, "dQw4w9WgXcQ")

    def test_top_level_comment_input_model_without_id(self):
        """Test TopLevelCommentInputModel without id field."""
        data_without_id = {
            "textDisplay": "Comment without ID",
            "authorDisplayName": "TestUser"
        }
        
        model = TopLevelCommentInputModel(**data_without_id)
        
        self.assertIsNone(model.id)  # Should default to None
        self.assertEqual(model.textDisplay, "Comment without ID")
        self.assertEqual(model.authorDisplayName, "TestUser")

    def test_top_level_comment_input_model_allows_extra_fields(self):
        """Test TopLevelCommentInputModel allows extra fields (extra='allow')."""
        data_with_extra = {
            "id": "comment_456",
            "textDisplay": "Comment with extra fields",
            "customField": "custom_value",
            "likeCount": 10,
            "publishedAt": "2023-06-01T12:00:00Z",
            "metadata": {"source": "test"}
        }
        
        model = TopLevelCommentInputModel(**data_with_extra)
        
        self.assertEqual(model.id, "comment_456")
        self.assertEqual(model.textDisplay, "Comment with extra fields")
        self.assertEqual(model.customField, "custom_value")
        self.assertEqual(model.likeCount, 10)
        self.assertEqual(model.publishedAt, "2023-06-01T12:00:00Z")
        self.assertEqual(model.metadata, {"source": "test"})

    def test_top_level_comment_input_model_unicode_text(self):
        """Test TopLevelCommentInputModel with Unicode text."""
        unicode_data = {
            "id": "unicode_comment",
            "textDisplay": "很棒的视频！👍 Great content! 🎉",
            "authorDisplayName": "用户测试",
            "language": "zh-CN"
        }
        
        model = TopLevelCommentInputModel(**unicode_data)
        
        self.assertEqual(model.textDisplay, "很棒的视频！👍 Great content! 🎉")
        self.assertEqual(model.authorDisplayName, "用户测试")
        self.assertEqual(model.language, "zh-CN")

    def test_top_level_comment_input_model_empty_data(self):
        """Test TopLevelCommentInputModel with no data."""
        model = TopLevelCommentInputModel()
        
        # Should work since id defaults to None and extra fields are allowed
        self.assertIsNone(model.id)
        self.assertIsInstance(model, TopLevelCommentInputModel)

    def test_top_level_comment_input_model_various_data_types(self):
        """Test TopLevelCommentInputModel with various data types in extra fields."""
        mixed_data = {
            "id": "mixed_data_comment",
            "string_field": "text",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True,
            "list_field": ["tag1", "tag2"],
            "dict_field": {"nested": "value"},
            "none_field": None
        }
        
        model = TopLevelCommentInputModel(**mixed_data)
        
        self.assertEqual(model.id, "mixed_data_comment")
        self.assertEqual(model.string_field, "text")
        self.assertEqual(model.int_field, 42)
        self.assertEqual(model.float_field, 3.14)
        self.assertTrue(model.bool_field)
        self.assertEqual(model.list_field, ["tag1", "tag2"])
        self.assertEqual(model.dict_field, {"nested": "value"})
        self.assertIsNone(model.none_field)


class TestThumbnailRecordUploadModel(BaseTestCaseWithErrorHandler):
    """Test ThumbnailRecordUploadModel validation and functionality."""

    def test_thumbnail_record_upload_model_valid_data(self):
        """Test ThumbnailRecordUploadModel with valid data."""
        valid_data = {
            "url": "https://example.com/uploaded_thumb.jpg",
            "width": 1280,
            "height": 720
        }
        
        model = ThumbnailRecordUploadModel(**valid_data)
        
        self.assertEqual(model.url, "https://example.com/uploaded_thumb.jpg")
        self.assertEqual(model.width, 1280)
        self.assertEqual(model.height, 720)

    def test_thumbnail_record_upload_model_inheritance(self):
        """Test that ThumbnailRecordUploadModel properly inherits from ThumbnailObjectModel."""
        model = ThumbnailRecordUploadModel(
            url="https://example.com/thumb.jpg",
            width=640,
            height=480
        )
        
        # Should have all the same validation as ThumbnailObjectModel
        self.assertIsInstance(model, ThumbnailRecordUploadModel)
        # Verify it behaves like the parent class
        self.assertEqual(model.url, "https://example.com/thumb.jpg")
        self.assertEqual(model.width, 640)
        self.assertEqual(model.height, 480)


class TestThumbnailsUploadModel(BaseTestCaseWithErrorHandler):
    """Test ThumbnailsUploadModel validation and functionality."""

    def test_thumbnails_upload_model_valid_data(self):
        """Test ThumbnailsUploadModel with valid data."""
        valid_data = {
            "default": ThumbnailRecordUploadModel(
                url="https://example.com/default.jpg",
                width=120,
                height=90
            ),
            "medium": ThumbnailRecordUploadModel(
                url="https://example.com/medium.jpg",
                width=320,
                height=180
            ),
            "high": ThumbnailRecordUploadModel(
                url="https://example.com/high.jpg",
                width=480,
                height=360
            )
        }
        
        model = ThumbnailsUploadModel(**valid_data)
        
        self.assertIsInstance(model.default, ThumbnailRecordUploadModel)
        self.assertIsInstance(model.medium, ThumbnailRecordUploadModel)
        self.assertIsInstance(model.high, ThumbnailRecordUploadModel)

    def test_thumbnails_upload_model_missing_required_fields(self):
        """Test ThumbnailsUploadModel validation with missing required fields."""
        # All three fields are required based on the actual model
        with self.assertRaises(ValidationError):
            ThumbnailsUploadModel(
                default=ThumbnailRecordUploadModel(
                    url="https://example.com/default.jpg",
                    width=120,
                    height=90
                )
                # Missing medium and high - should raise ValidationError
            )

    def test_thumbnails_upload_model_all_fields_required(self):
        """Test that ThumbnailsUploadModel requires all three thumbnail fields."""
        # Test that all fields are required
        with self.assertRaises(ValidationError):
            ThumbnailsUploadModel()  # No data provided


class TestSnippetUploadModel(BaseTestCaseWithErrorHandler):
    """Test SnippetUploadModel validation and functionality."""

    def test_snippet_upload_model_valid_data(self):
        """Test SnippetUploadModel with valid data."""
        valid_data = {
            "title": "Test Upload Video",
            "description": "This is a test upload",
            "channelId": "UC1234567890",
            "tags": ["test", "upload"],
            "categoryId": "22",
            "channelTitle": "Test Channel",
            "thumbnails": ThumbnailsUploadModel(
                default=ThumbnailRecordUploadModel(
                    url="https://example.com/default.jpg",
                    width=120,
                    height=90
                ),
                medium=ThumbnailRecordUploadModel(
                    url="https://example.com/medium.jpg",
                    width=320,
                    height=180
                ),
                high=ThumbnailRecordUploadModel(
                    url="https://example.com/high.jpg",
                    width=480,
                    height=360
                )
            )
        }
        
        model = SnippetUploadModel(**valid_data)
        
        self.assertEqual(model.title, "Test Upload Video")
        self.assertEqual(model.channelId, "UC1234567890")
        self.assertEqual(model.description, "This is a test upload")
        self.assertIsInstance(model.thumbnails, ThumbnailsUploadModel)
        self.assertEqual(model.tags, ["test", "upload"])
        self.assertEqual(model.categoryId, "22")
        self.assertEqual(model.channelTitle, "Test Channel")

    def test_snippet_upload_model_missing_required_fields(self):
        """Test SnippetUploadModel validation with missing required fields."""
        # All fields are required based on the actual model
        with self.assertRaises(ValidationError):
            SnippetUploadModel(
                title="Incomplete Upload"
                # Missing other required fields
            )

    def test_snippet_upload_model_unicode_content(self):
        """Test SnippetUploadModel with Unicode content."""
        unicode_thumbnails = ThumbnailsUploadModel(
            default=ThumbnailRecordUploadModel(
                url="https://example.com/default.jpg",
                width=120,
                height=90
            ),
            medium=ThumbnailRecordUploadModel(
                url="https://example.com/medium.jpg",
                width=320,
                height=180
            ),
            high=ThumbnailRecordUploadModel(
                url="https://example.com/high.jpg",
                width=480,
                height=360
            )
        )
        
        unicode_data = {
            "title": "测试上传视频 🎥",
            "description": "这是一个测试上传描述 with emojis 🎬🎞️",
            "channelId": "UC测试频道123",
            "tags": ["测试", "上传", "中文"],
            "categoryId": "22",
            "channelTitle": "测试频道",
            "thumbnails": unicode_thumbnails
        }
        
        model = SnippetUploadModel(**unicode_data)
        
        self.assertEqual(model.title, "测试上传视频 🎥")
        self.assertEqual(model.description, "这是一个测试上传描述 with emojis 🎬🎞️")
        self.assertIn("测试", model.tags)


class TestStatusUploadModel(BaseTestCaseWithErrorHandler):
    """Test StatusUploadModel validation and functionality."""

    def test_status_upload_model_valid_data(self):
        """Test StatusUploadModel with valid data."""
        valid_data = {
            "uploadStatus": "processed",
            "privacyStatus": "public",
            "embeddable": True,
            "madeForKids": False
        }
        
        model = StatusUploadModel(**valid_data)
        
        self.assertEqual(model.uploadStatus, "processed")
        self.assertEqual(model.privacyStatus, "public")
        self.assertTrue(model.embeddable)
        self.assertFalse(model.madeForKids)

    def test_status_upload_model_missing_required_fields(self):
        """Test StatusUploadModel validation with missing required fields."""
        # All fields are required based on the actual model
        with self.assertRaises(ValidationError):
            StatusUploadModel(
                uploadStatus="processed"
                # Missing other required fields
            )

    def test_status_upload_model_privacy_status_validation(self):
        """Test StatusUploadModel privacy status validation."""
        valid_privacy_statuses = ["private", "public", "unlisted"]
        
        for privacy_status in valid_privacy_statuses:
            with self.subTest(privacy_status=privacy_status):
                model = StatusUploadModel(
                    uploadStatus="processed",
                    privacyStatus=privacy_status,
                    embeddable=True,
                    madeForKids=False
                )
                self.assertEqual(model.privacyStatus, privacy_status)

    def test_status_upload_model_boolean_validation(self):
        """Test StatusUploadModel boolean field validation."""
        # Test with StrictBool fields
        model = StatusUploadModel(
            uploadStatus="processed",
            privacyStatus="public",
            embeddable=True,
            madeForKids=False
        )
        
        self.assertIsInstance(model.embeddable, bool)
        self.assertIsInstance(model.madeForKids, bool)
        self.assertTrue(model.embeddable)
        self.assertFalse(model.madeForKids)

    def test_status_upload_model_strict_bool_validation(self):
        """Test StatusUploadModel StrictBool validation."""
        # StrictBool should not accept string representations
        with self.assertRaises(ValidationError):
            StatusUploadModel(
                uploadStatus="processed",
                privacyStatus="public",
                embeddable="true",  # String instead of bool - should fail
                madeForKids=False
            )
        
        with self.assertRaises(ValidationError):
            StatusUploadModel(
                uploadStatus="processed",
                privacyStatus="public",
                embeddable=True,
                madeForKids="false"  # String instead of bool - should fail
            )


class TestVideoUploadModel(BaseTestCaseWithErrorHandler):
    """Test VideoUploadModel validation and functionality."""

    def test_video_upload_model_valid_data(self):
        """Test VideoUploadModel with complete valid data."""
        snippet = SnippetUploadModel(
            title="Test Video Upload",
            description="A comprehensive test video",
            channelId="UC1234567890",
            tags=["test", "video", "upload"],
            categoryId="22",
            channelTitle="Test Channel",
            thumbnails=ThumbnailsUploadModel(
                default=ThumbnailRecordUploadModel(
                    url="https://example.com/default.jpg",
                    width=120,
                    height=90
                ),
                medium=ThumbnailRecordUploadModel(
                    url="https://example.com/medium.jpg",
                    width=320,
                    height=180
                ),
                high=ThumbnailRecordUploadModel(
                    url="https://example.com/high.jpg",
                    width=480,
                    height=360
                )
            )
        )
        
        status = StatusUploadModel(
            uploadStatus="processed",
            privacyStatus="public",
            embeddable=True,
            madeForKids=False
        )
        
        valid_data = {
            "snippet": snippet,
            "status": status
        }
        
        model = VideoUploadModel(**valid_data)
        
        self.assertIsInstance(model.snippet, SnippetUploadModel)
        self.assertIsInstance(model.status, StatusUploadModel)
        self.assertEqual(model.snippet.title, "Test Video Upload")
        self.assertEqual(model.status.privacyStatus, "public")

    def test_video_upload_model_missing_required_fields(self):
        """Test VideoUploadModel validation with missing required fields."""
        # Both snippet and status are required based on the actual model
        with self.assertRaises(ValidationError):
            VideoUploadModel(
                snippet=SnippetUploadModel(
                    title="Incomplete Video",
                    description="Missing status",
                    channelId="UC123",
                    tags=["test"],
                    categoryId="22",
                    channelTitle="Test",
                    thumbnails=ThumbnailsUploadModel(
                        default=ThumbnailRecordUploadModel(
                            url="https://example.com/thumb.jpg",
                            width=120,
                            height=90
                        ),
                        medium=ThumbnailRecordUploadModel(
                            url="https://example.com/thumb.jpg",
                            width=320,
                            height=180
                        ),
                        high=ThumbnailRecordUploadModel(
                            url="https://example.com/thumb.jpg",
                            width=480,
                            height=360
                        )
                    )
                )
                # Missing status - should raise ValidationError
            )

    def test_video_upload_model_nested_validation(self):
        """Test VideoUploadModel validates nested models correctly."""
        # Test with invalid nested snippet data (missing required field)
        with self.assertRaises(ValidationError):
            VideoUploadModel(
                snippet=SnippetUploadModel(
                    title="Test"
                    # Missing other required fields
                ),
                status=StatusUploadModel(
                    uploadStatus="processed",
                    privacyStatus="public",
                    embeddable=True,
                    madeForKids=False
                )
            )

    def test_video_upload_model_unicode_content(self):
        """Test VideoUploadModel with Unicode content."""
        unicode_snippet = SnippetUploadModel(
            title="测试视频上传 🎥",
            description="包含中文和表情符号的测试描述 🎬🎞️",
            channelId="UC测试频道123",
            tags=["测试", "上传", "中文", "🎥"],
            categoryId="22",
            channelTitle="测试频道",
            thumbnails=ThumbnailsUploadModel(
                default=ThumbnailRecordUploadModel(
                    url="https://example.com/default.jpg",
                    width=120,
                    height=90
                ),
                medium=ThumbnailRecordUploadModel(
                    url="https://example.com/medium.jpg",
                    width=320,
                    height=180
                ),
                high=ThumbnailRecordUploadModel(
                    url="https://example.com/high.jpg",
                    width=480,
                    height=360
                )
            )
        )
        
        status = StatusUploadModel(
            uploadStatus="processed",
            privacyStatus="public",
            embeddable=True,
            madeForKids=False
        )
        
        model = VideoUploadModel(snippet=unicode_snippet, status=status)
        
        # Verify Unicode content was properly stored
        self.assertEqual(model.snippet.title, "测试视频上传 🎥")
        self.assertIn("中文和表情符号", model.snippet.description)
        self.assertIn("测试", model.snippet.tags)
        self.assertIn("🎥", model.snippet.tags)


class TestModelSerialization(BaseTestCaseWithErrorHandler):
    """Test model serialization and deserialization."""

    def test_model_to_dict_conversion(self):
        """Test converting models to dictionaries."""
        snippet = SnippetUploadModel(
            title="Test Video",
            description="Test description",
            channelId="UC123",
            tags=["test"],
            categoryId="22",
            channelTitle="Test Channel",
            thumbnails=ThumbnailsUploadModel(
                default=ThumbnailRecordUploadModel(
                    url="https://example.com/default.jpg",
                    width=120,
                    height=90
                ),
                medium=ThumbnailRecordUploadModel(
                    url="https://example.com/medium.jpg",
                    width=320,
                    height=180
                ),
                high=ThumbnailRecordUploadModel(
                    url="https://example.com/high.jpg",
                    width=480,
                    height=360
                )
            )
        )
        
        status = StatusUploadModel(
            uploadStatus="processed",
            privacyStatus="public",
            embeddable=True,
            madeForKids=False
        )
        
        video_model = VideoUploadModel(snippet=snippet, status=status)
        
        # Convert to dict
        video_dict = video_model.model_dump()
        
        self.assertIsInstance(video_dict, dict)
        self.assertIsInstance(video_dict["snippet"], dict)
        self.assertIsInstance(video_dict["status"], dict)
        self.assertEqual(video_dict["snippet"]["title"], "Test Video")
        self.assertEqual(video_dict["status"]["privacyStatus"], "public")

    def test_model_json_serialization(self):
        """Test JSON serialization of models."""
        snippet = SnippetUploadModel(
            title="JSON Test Video",
            description="Testing JSON serialization",
            channelId="UC123",
            tags=["test"],
            categoryId="22",
            channelTitle="Test Channel",
            thumbnails=ThumbnailsUploadModel(
                default=ThumbnailRecordUploadModel(
                    url="https://example.com/default.jpg",
                    width=120,
                    height=90
                ),
                medium=ThumbnailRecordUploadModel(
                    url="https://example.com/medium.jpg",
                    width=320,
                    height=180
                ),
                high=ThumbnailRecordUploadModel(
                    url="https://example.com/high.jpg",
                    width=480,
                    height=360
                )
            )
        )
        
        status = StatusUploadModel(
            uploadStatus="processed",
            privacyStatus="public",
            embeddable=True,
            madeForKids=False
        )
        
        video_model = VideoUploadModel(snippet=snippet, status=status)
        
        # Convert to JSON
        json_str = video_model.model_dump_json()
        
        self.assertIsInstance(json_str, str)
        self.assertIn("JSON Test Video", json_str)
        self.assertIn("Testing JSON serialization", json_str)

    def test_model_validation_error_messages(self):
        """Test that validation errors provide clear messages."""
        # Test with missing required fields
        try:
            VideoUploadModel(
                snippet=SnippetUploadModel(
                    title="Incomplete"
                    # Missing required fields
                )
                # Missing status field
            )
        except ValidationError as e:
            error_str = str(e)
            # Should contain information about the validation errors
            self.assertIn("validation", error_str.lower())

    def test_snippet_input_model_serialization(self):
        """Test SnippetInputModel serialization with extra fields."""
        model = SnippetInputModel(
            title="Test",
            customField="custom_value",
            dynamicData={"key": "value"}
        )
        
        # Convert to dict
        model_dict = model.model_dump()
        
        self.assertIsInstance(model_dict, dict)
        self.assertEqual(model_dict["title"], "Test")
        self.assertEqual(model_dict["customField"], "custom_value")
        self.assertEqual(model_dict["dynamicData"], {"key": "value"})

    def test_top_level_comment_model_serialization(self):
        """Test TopLevelCommentInputModel serialization with extra fields."""
        model = TopLevelCommentInputModel(
            id="comment123",
            textDisplay="Test comment",
            customMetadata={"source": "test"}
        )
        
        # Convert to dict
        model_dict = model.model_dump()
        
        self.assertIsInstance(model_dict, dict)
        self.assertEqual(model_dict["id"], "comment123")
        self.assertEqual(model_dict["textDisplay"], "Test comment")
        self.assertEqual(model_dict["customMetadata"], {"source": "test"})


if __name__ == '__main__':
    unittest.main()
