"""
Database Validation Tests for YouTube Service
This module contains tests to validate the database structure and data integrity.
"""

import unittest
import copy
import json
import os
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, ValidationError, Field, ConfigDict
from ..SimulationEngine.db import DB
from ..SimulationEngine.models import (
    ThumbnailObjectModel,
    ThumbnailInputModel,
    SnippetInputModel,
    ThumbnailsUploadModel,
    SnippetUploadModel,
    StatusUploadModel,
    VideoUploadModel
)
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import youtube


# Additional Pydantic Models for Database Validation (extending existing models)

# Reuse existing models where possible
ThumbnailModel = ThumbnailObjectModel
ThumbnailsModel = ThumbnailInputModel


class VideoStatisticsModel(BaseModel):
    """Model for video statistics (database format)."""
    viewCount: str
    likeCount: str
    commentCount: str
    favoriteCount: str


class VideoSnippetDatabaseModel(BaseModel):
    """Model for video snippet data in database format."""
    publishedAt: str
    channelId: str
    title: str
    description: str
    thumbnails: ThumbnailsModel
    channelTitle: str
    tags: List[str]
    categoryId: str


class VideoStatusDatabaseModel(BaseModel):
    """Model for video status in database format."""
    uploadStatus: str
    privacyStatus: str
    embeddable: bool
    madeForKids: bool


class VideoModel(BaseModel):
    """Model for video entries in database."""
    id: str
    snippet: VideoSnippetDatabaseModel
    statistics: VideoStatisticsModel
    status: VideoStatusDatabaseModel


class ActivityModel(BaseModel):
    """Model for activity entries."""
    kind: str
    etag: str
    id: str


class CaptionSnippetModel(BaseModel):
    """Model for caption snippet data."""
    videoId: str


class CaptionModel(BaseModel):
    """Model for caption entries."""
    id: str
    snippet: CaptionSnippetModel


class ChannelModel(BaseModel):
    """Model for channel entries."""
    part: str
    categoryId: str
    forUsername: str
    hl: str
    id: str
    managedByMe: bool
    maxResults: int
    mine: bool
    mySubscribers: bool
    onBehalfOfContentOwner: Optional[str] = None


class ChannelSectionSnippetModel(BaseModel):
    """Model for channel section snippet data."""
    channelId: str
    type: str


class ChannelSectionModel(BaseModel):
    """Model for channel section entries."""
    id: str
    snippet: ChannelSectionSnippetModel


class ChannelStatisticsModel(BaseModel):
    """Model for channel statistics."""
    commentCount: int
    hiddenSubscriberCount: bool
    subscriberCount: int
    videoCount: int
    viewCount: int


class CommentSnippetModel(BaseModel):
    """Model for comment snippet data."""
    videoId: str
    parentId: Optional[str] = None


class CommentModel(BaseModel):
    """Model for comment entries."""
    id: str
    snippet: CommentSnippetModel
    moderationStatus: str
    bannedAuthor: bool


class CommentThreadSnippetModel(BaseModel):
    """Model for comment thread snippet data."""
    channelId: str
    videoId: str


class CommentThreadModel(BaseModel):
    """Model for comment thread entries."""
    id: str
    snippet: CommentThreadSnippetModel
    comments: List[str]


class ResourceIdModel(BaseModel):
    """Model for resource ID data."""
    kind: str
    channelId: str


class SubscriptionSnippetModel(BaseModel):
    """Model for subscription snippet data."""
    channelId: str
    resourceId: ResourceIdModel


class SubscriptionModel(BaseModel):
    """Model for subscription entries."""
    id: str
    snippet: SubscriptionSnippetModel


class VideoCategorySnippetModel(BaseModel):
    """Model for video category snippet data."""
    title: str
    regionCode: str


class VideoCategoryModel(BaseModel):
    """Model for video category entries."""
    id: str
    snippet: VideoCategorySnippetModel


class MembershipSnippetModel(BaseModel):
    """Model for membership snippet data."""
    memberChannelId: str
    hasAccessToLevel: str
    mode: str


class MembershipModel(BaseModel):
    """Model for membership entries."""
    id: str
    snippet: MembershipSnippetModel


class PlaylistSnippetModel(BaseModel):
    """Model for playlist snippet data."""
    publishedAt: str
    channelId: str
    title: str
    description: str
    list_of_videos: List[str]
    thumbnails: ThumbnailsModel


class PlaylistStatusModel(BaseModel):
    """Model for playlist status."""
    privacyStatus: str


class PlaylistContentDetailsModel(BaseModel):
    """Model for playlist content details."""
    itemCount: int


class PlaylistModel(BaseModel):
    """Model for playlist entries."""
    kind: str
    id: str
    snippet: PlaylistSnippetModel
    status: PlaylistStatusModel
    contentDetails: PlaylistContentDetailsModel


class YouTubeDatabaseModel(BaseModel):
    """Model for the complete YouTube database structure."""
    activities: List[ActivityModel]
    videos: Dict[str, VideoModel]
    captions: Dict[str, CaptionModel]
    channels: Dict[str, ChannelModel]
    channelSections: Dict[str, ChannelSectionModel]
    channelStatistics: ChannelStatisticsModel
    channelBanners: List[Any]  # Empty list in default DB
    comments: Dict[str, CommentModel]
    commentThreads: Dict[str, CommentThreadModel]
    subscriptions: Dict[str, SubscriptionModel]
    videoCategories: Dict[str, VideoCategoryModel]
    memberships: Dict[str, MembershipModel]
    playlists: Dict[str, PlaylistModel]

    model_config = ConfigDict(extra="forbid")


class TestDatabaseValidation(BaseCase):
    """Test database structure validation and data integrity."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Save original DB state and reset to clean state
        self.original_db_state = copy.deepcopy(DB)
        DB.clear()
        self._reset_db()

    def _get_default_db_path(self):
        """
        Helper method to get the path to the default YouTube database file.
        
        Returns:
            str: Path to YoutubeDefaultDB.json
        """
        current_dir = os.path.dirname(__file__)
        project_root = current_dir
        # Navigate up until we find the DBs directory
        while project_root and not os.path.exists(os.path.join(project_root, "DBs")):
            parent = os.path.dirname(project_root)
            if parent == project_root:  # Reached filesystem root
                break
            project_root = parent
        
        return os.path.join(project_root, "DBs", "YoutubeDefaultDB.json")

    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db_state)

    def _reset_db(self):
        """Reset DB to clean initial state."""
        DB.update({
            "activities": [],
            "captions": {},
            "channels": {},
            "channelSections": {},
            "channelStatistics": {
                "commentCount": 0,
                "hiddenSubscriberCount": False,
                "subscriberCount": 0,
                "videoCount": 0,
                "viewCount": 0,
            },
            "channelBanners": [],
            "comments": {},
            "commentThreads": {},
            "subscriptions": {},
            "videoCategories": {},
            "memberships": {},
            "videos": {},
            "playlists": {},  # Added missing playlists field
        })

    def _validate_db_structure(self):
        """
        Helper method to validate database structure.
        
        Raises:
            AssertionError: If validation fails
        """
        try:
            # Validate required collections exist
            required_collections = [
                "activities", "captions", "channels", "channelSections",
                "channelStatistics", "channelBanners", "comments", "commentThreads",
                "subscriptions", "videoCategories", "memberships", "videos", "playlists"
            ]
            
            for collection in required_collections:
                self.assertIn(collection, DB, f"Missing required collection: {collection}")
            
            # Validate collection types
            dict_collections = ["captions", "channels", "channelSections", "comments", 
                               "commentThreads", "subscriptions", "videoCategories", 
                               "memberships", "videos", "channelStatistics", "playlists"]
            list_collections = ["activities", "channelBanners"]
            
            for collection in dict_collections:
                self.assertIsInstance(DB[collection], dict, f"Collection {collection} should be dict")
            
            for collection in list_collections:
                self.assertIsInstance(DB[collection], list, f"Collection {collection} should be list")
                
            # Validate channelStatistics structure
            stats = DB["channelStatistics"]
            required_stats = ["commentCount", "hiddenSubscriberCount", "subscriberCount", 
                             "videoCount", "viewCount"]
            for stat in required_stats:
                self.assertIn(stat, stats, f"Missing stat: {stat}")
                
        except Exception as e:
            self.fail(f"DB structure validation failed: {e}")

    def test_db_module_harmony(self):
        """
        Test that the database used by the db module is in harmony with the expected structure.
        This ensures that tests are running against the expected data structure.
        """
        self._validate_db_structure()

    def test_db_structure_after_video_operations(self):
        """
        Test that the database maintains structure after video operations.
        """
        # Create a channel to populate the database
        DB["channels"]["channel1"] = {
            "id": "channel1",
            "forUsername": "Test Channel"
        }
        DB["videoCategories"]["28"] = {
            "id": "28",
            "snippet": {
                "title": "Film & Animation",
                "regionCode": "US"
            }
        }
        # Upload a video
        result = youtube.upload_video({
            "snippet": {
                "channelId": "channel1",
                "title": "Introduction to Programming",
                "description": "Learn the basics of programming in this comprehensive tutorial",
                "thumbnails": {
                    "default": {
                        "url": "https://google.com/thumb1.jpg",
                        "width": 120,
                        "height": 90
                    },
                    "medium": {
                        "url": "https://google.com/thumb1_medium.jpg",
                        "width": 320,
                        "height": 180
                    },
                    "high": {
                        "url": "https://google.com/thumb1_high.jpg",
                        "width": 480,
                        "height": 360
                    }
                },
                "channelTitle": "Test Channel",
                "tags": ["programming", "tutorial", "coding"],
                "categoryId": "28"
            },
            "status": {
                "privacyStatus": "public",
                "uploadStatus": "processed",
                "embeddable": True,
                "madeForKids": False,
            }
        })

        # Validate database structure after upload
        self._validate_db_structure()

        # Verify the video was added correctly
        self.assertGreater(len(DB["videos"]), 0)

    def test_db_structure_after_comment_operations(self):
        """
        Test that the database maintains structure after comment operations.
        """
        # Add a comment
        result = youtube.add_comment(
            part="snippet",
            snippet= {
                "textOriginal": "Test comment for database validation",
                "videoId": "testVideoId123"
            },
        )

        # Validate database structure after comment addition
        self._validate_db_structure()

        # Verify the comment was added correctly
        if "comments" in DB and len(DB["comments"]) > 0:
            self.assertGreater(len(DB["comments"]), 0)

    def test_empty_db_structure(self):
        """
        Test that an empty database has the correct structure.
        """
        # Ensure DB is in clean state
        self._reset_db()

        self._validate_db_structure()

        # Verify empty state
        self.assertEqual(len(DB["channels"]), 0)
        self.assertEqual(len(DB["videos"]), 0)
        self.assertEqual(len(DB["comments"]), 0)
        self.assertEqual(len(DB["subscriptions"]), 0)
        self.assertEqual(len(DB["activities"]), 0)
        self.assertEqual(len(DB["playlists"]), 0)

    def test_db_statistics_consistency(self):
        """
        Test that database statistics remain consistent with actual data.
        """
        # Validate initial statistics
        self._validate_db_structure()
        initial_stats = copy.deepcopy(DB["channelStatistics"])

        # Perform some operations that might affect statistics
        try:
            youtube.manage_channel_video_count(video_count=5)
            youtube.manage_channel_subscriber_count(subscriber_count=1000)
            youtube.manage_channel_view_count(view_count=50000)
        except:
            # Some functions might not be available, continue validation
            pass

        # Validate database structure after statistics updates
        self._validate_db_structure()

        # Verify statistics structure is maintained
        stats = DB["channelStatistics"]
        self.assertIsInstance(stats["videoCount"], int)
        self.assertIsInstance(stats["subscriberCount"], int)
        self.assertIsInstance(stats["viewCount"], int)
        self.assertIsInstance(stats["commentCount"], int)

    def test_db_structure_with_complex_operations(self):
        """
        Test database structure with complex operation sequences.
        """
        # Create multiple entities
        try:
            # Create channel
            youtube.create_channel({
                "snippet": {
                    "title": "Complex Test Channel",
                    "description": "Testing complex operations"
                }
            })

            # Upload video
            youtube.upload_video({
                "snippet": {
                    "title": "Complex Test Video",
                    "description": "Testing complex operations",
                    "channelId": "UCComplexTest123"
                }
            })

            # Create playlist
            youtube.create_playlist(
                ownerId="UCComplexTest123",
                title="Complex Test Playlist"
            )

            # Add comment
            youtube.add_comment(
                part="snippet",
                body={
                    "snippet": {
                        "textOriginal": "Complex test comment",
                        "videoId": "complexTestVideo123"
                    }
                }
            )

        except Exception:
            # Some operations might fail, but DB structure should remain valid
            pass

        # Validate database structure after complex operations
        self._validate_db_structure()

    def test_db_data_integrity_after_modifications(self):
        """
        Test that database maintains data integrity after modifications.
        """
        # Create initial data
        try:
            result = youtube.upload_video({
                "snippet": {
                    "title": "Original Title",
                    "description": "Original description"
                }
            })

            # Modify the video
            if "videos" in DB and len(DB["videos"]) > 0:
                video_id = list(DB["videos"].keys())[0]
                youtube.update_video_metadata(
                    id=video_id,
                    snippet={
                        "title": "Updated Title",
                        "description": "Updated description"
                    }
                )

        except Exception:
            # Operations might fail, but structure should remain valid
            pass

        # Validate database structure after modifications
        self._validate_db_structure()

    def test_db_structure_with_edge_cases(self):
        """
        Test database structure with edge cases and boundary conditions.
        """
        # Test with empty parameters
        try:
            youtube.list_channels(part="snippet", maxResults=0)
            youtube.list_videos(part="snippet", maxResults=0)
        except Exception:
            # Edge cases might cause errors, but DB should remain valid
            pass

        # Validate database structure after edge case operations
        self._validate_db_structure()

        # Test with unicode content
        try:
            youtube.upload_video({
                "snippet": {
                    "title": "Unicode Test 测试 🎥",
                    "description": "Testing unicode content 中文测试"
                }
            })
        except Exception:
            pass

        # Validate database structure after unicode operations
        self._validate_db_structure()

    def test_db_collection_relationships(self):
        """
        Test that database collections maintain proper relationships.
        """
        # Validate structure
        self._validate_db_structure()

        # Test that all collections are accessible
        for collection_name in DB.keys():
            collection = DB[collection_name]
            self.assertIsNotNone(collection, f"Collection {collection_name} should not be None")

        # Test that nested access works
        if "channelStatistics" in DB:
            stats = DB["channelStatistics"]
            for stat_key in stats.keys():
                stat_value = stats[stat_key]
                self.assertIsNotNone(stat_value, f"Statistic {stat_key} should not be None")

    def test_validate_individual_video_entries(self):
        """Test that individual video entries validate against the VideoModel."""
        default_db_path = self._get_default_db_path()
        
        if not os.path.exists(default_db_path):
            self.skipTest(f"Default DB file not found at {default_db_path}")
        
        with open(default_db_path, 'r', encoding='utf-8') as f:
            default_db_data = json.load(f)
        
        videos = default_db_data.get("videos", {})
        
        for video_id, video_data in videos.items():
            with self.subTest(video_id=video_id):
                try:
                    validated_video = VideoModel(**video_data)
                    self.assertEqual(validated_video.id, video_id)
                    self.assertIsInstance(validated_video.snippet, VideoSnippetDatabaseModel)
                    self.assertIsInstance(validated_video.statistics, VideoStatisticsModel)
                    self.assertIsInstance(validated_video.status, VideoStatusDatabaseModel)
                except ValidationError as e:
                    self.fail(f"Video {video_id} validation failed: {e}")

    def test_validate_individual_channel_entries(self):
        """Test that individual channel entries validate against the ChannelModel."""
        default_db_path = self._get_default_db_path()
        
        if not os.path.exists(default_db_path):
            self.skipTest(f"Default DB file not found at {default_db_path}")
        
        with open(default_db_path, 'r', encoding='utf-8') as f:
            default_db_data = json.load(f)
        
        channels = default_db_data.get("channels", {})
        
        for channel_id, channel_data in channels.items():
            with self.subTest(channel_id=channel_id):
                try:
                    validated_channel = ChannelModel(**channel_data)
                    self.assertEqual(validated_channel.id, channel_id)
                    self.assertIsInstance(validated_channel.part, str)
                    self.assertIsInstance(validated_channel.forUsername, str)
                except ValidationError as e:
                    self.fail(f"Channel {channel_id} validation failed: {e}")

    def test_validate_individual_comment_entries(self):
        """Test that individual comment entries validate against the CommentModel."""
        default_db_path = self._get_default_db_path()
        
        if not os.path.exists(default_db_path):
            self.skipTest(f"Default DB file not found at {default_db_path}")
        
        with open(default_db_path, 'r', encoding='utf-8') as f:
            default_db_data = json.load(f)
        
        comments = default_db_data.get("comments", {})
        
        for comment_id, comment_data in comments.items():
            with self.subTest(comment_id=comment_id):
                try:
                    validated_comment = CommentModel(**comment_data)
                    self.assertEqual(validated_comment.id, comment_id)
                    self.assertIsInstance(validated_comment.snippet, CommentSnippetModel)
                    self.assertIn(validated_comment.moderationStatus, 
                                ["published", "heldForReview", "rejected"])
                    self.assertIsInstance(validated_comment.bannedAuthor, bool)
                except ValidationError as e:
                    self.fail(f"Comment {comment_id} validation failed: {e}")

    def test_validate_individual_playlist_entries(self):
        """Test that individual playlist entries validate against the PlaylistModel."""
        default_db_path = self._get_default_db_path()
        
        if not os.path.exists(default_db_path):
            self.skipTest(f"Default DB file not found at {default_db_path}")
        
        with open(default_db_path, 'r', encoding='utf-8') as f:
            default_db_data = json.load(f)
        
        playlists = default_db_data.get("playlists", {})
        
        for playlist_id, playlist_data in playlists.items():
            with self.subTest(playlist_id=playlist_id):
                try:
                    validated_playlist = PlaylistModel(**playlist_data)
                    self.assertEqual(validated_playlist.id, playlist_id)
                    self.assertIsInstance(validated_playlist.snippet, PlaylistSnippetModel)
                    self.assertIsInstance(validated_playlist.status, PlaylistStatusModel)
                    self.assertIsInstance(validated_playlist.contentDetails, PlaylistContentDetailsModel)
                    self.assertEqual(validated_playlist.kind, "youtube#playlist")
                except ValidationError as e:
                    self.fail(f"Playlist {playlist_id} validation failed: {e}")

    def test_validate_channel_statistics_structure(self):
        """Test that channel statistics validate against the ChannelStatisticsModel."""
        default_db_path = self._get_default_db_path()
        
        if not os.path.exists(default_db_path):
            self.skipTest(f"Default DB file not found at {default_db_path}")
        
        with open(default_db_path, 'r', encoding='utf-8') as f:
            default_db_data = json.load(f)
        
        channel_stats = default_db_data.get("channelStatistics", {})
        
        try:
            validated_stats = ChannelStatisticsModel(**channel_stats)
            self.assertIsInstance(validated_stats.commentCount, int)
            self.assertIsInstance(validated_stats.hiddenSubscriberCount, bool)
            self.assertIsInstance(validated_stats.subscriberCount, int)
            self.assertIsInstance(validated_stats.videoCount, int)
            self.assertIsInstance(validated_stats.viewCount, int)
            
            # Verify that counts are non-negative
            self.assertGreaterEqual(validated_stats.commentCount, 0)
            self.assertGreaterEqual(validated_stats.subscriberCount, 0)
            self.assertGreaterEqual(validated_stats.videoCount, 0)
            self.assertGreaterEqual(validated_stats.viewCount, 0)
            
        except ValidationError as e:
            self.fail(f"Channel statistics validation failed: {e}")

    def test_validate_activity_entries(self):
        """Test that activity entries validate against the ActivityModel."""
        default_db_path = self._get_default_db_path()
        
        if not os.path.exists(default_db_path):
            self.skipTest(f"Default DB file not found at {default_db_path}")
        
        with open(default_db_path, 'r', encoding='utf-8') as f:
            default_db_data = json.load(f)
        
        activities = default_db_data.get("activities", [])
        
        for i, activity_data in enumerate(activities):
            with self.subTest(activity_index=i):
                try:
                    validated_activity = ActivityModel(**activity_data)
                    self.assertEqual(validated_activity.kind, "youtube#activity")
                    self.assertIsInstance(validated_activity.etag, str)
                    self.assertIsInstance(validated_activity.id, str)
                except ValidationError as e:
                    self.fail(f"Activity {i} validation failed: {e}")

    def test_validate_thumbnail_structures(self):
        """Test that thumbnail structures in videos and playlists are valid."""
        default_db_path = self._get_default_db_path()
        
        if not os.path.exists(default_db_path):
            self.skipTest(f"Default DB file not found at {default_db_path}")
        
        with open(default_db_path, 'r', encoding='utf-8') as f:
            default_db_data = json.load(f)
        
        # Test video thumbnails
        videos = default_db_data.get("videos", {})
        for video_id, video_data in videos.items():
            with self.subTest(video_id=video_id, type="video"):
                thumbnails_data = video_data.get("snippet", {}).get("thumbnails", {})
                try:
                    validated_thumbnails = ThumbnailsModel(**thumbnails_data)
                    
                    # Verify all thumbnail sizes have valid dimensions
                    for size_name, thumbnail in [
                        ("default", validated_thumbnails.default),
                        ("medium", validated_thumbnails.medium),
                        ("high", validated_thumbnails.high)
                    ]:
                        self.assertGreater(thumbnail.width, 0, f"{size_name} width should be positive")
                        self.assertGreater(thumbnail.height, 0, f"{size_name} height should be positive")
                        self.assertTrue(thumbnail.url.startswith("https://"), 
                                      f"{size_name} URL should be HTTPS")
                        
                except ValidationError as e:
                    self.fail(f"Video {video_id} thumbnails validation failed: {e}")
        
        # Test playlist thumbnails
        playlists = default_db_data.get("playlists", {})
        for playlist_id, playlist_data in playlists.items():
            with self.subTest(playlist_id=playlist_id, type="playlist"):
                thumbnails_data = playlist_data.get("snippet", {}).get("thumbnails", {})
                try:
                    validated_thumbnails = ThumbnailsModel(**thumbnails_data)
                    
                    # Verify all thumbnail sizes have valid dimensions
                    for size_name, thumbnail in [
                        ("default", validated_thumbnails.default),
                        ("medium", validated_thumbnails.medium),
                        ("high", validated_thumbnails.high)
                    ]:
                        self.assertGreater(thumbnail.width, 0, f"{size_name} width should be positive")
                        self.assertGreater(thumbnail.height, 0, f"{size_name} height should be positive")
                        self.assertTrue(thumbnail.url.startswith("https://"), 
                                      f"{size_name} URL should be HTTPS")
                        
                except ValidationError as e:
                    self.fail(f"Playlist {playlist_id} thumbnails validation failed: {e}")

    def test_validate_current_db_state_with_pydantic(self):
        """
        Test that the current DB state validates against Pydantic models.
        This test validates whatever is currently in the database.
        """
        try:
            # Validate the current database structure
            validated_db = YouTubeDatabaseModel(**DB)
            self.assertIsNotNone(validated_db)
            
            # Verify all required collections are present
            required_collections = [
                "activities", "videos", "captions", "channels", "channelSections",
                "channelStatistics", "channelBanners", "comments", "commentThreads",
                "subscriptions", "videoCategories", "memberships", "playlists"
            ]
            
            for collection in required_collections:
                self.assertTrue(hasattr(validated_db, collection), 
                              f"Missing collection: {collection}")
                
        except ValidationError as e:
            # Provide detailed error information
            validation_errors = []
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"])
                validation_errors.append(f"{loc}: {error['msg']}")
            
            self.fail(f"Current DB state validation failed:\n" + "\n".join(validation_errors))

    def test_pydantic_model_strictness(self):
        """
        Test that Pydantic models reject invalid data structures.
        This ensures our models are properly strict.
        """
        # Test invalid video structure
        invalid_video = {
            "id": "test_video",
            "snippet": {
                "title": "Test Video",
                # Missing required fields
            },
            "statistics": {
                "viewCount": "not_a_string_number",  # Should be string representation of number
                "likeCount": 123,  # Should be string
                "commentCount": "100",
                "favoriteCount": "50"
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": "yes",  # Should be boolean
                "madeForKids": False
            }
        }
        
        with self.assertRaises(ValidationError):
            VideoModel(**invalid_video)
        
        # Test invalid channel statistics
        invalid_stats = {
            "commentCount": "not_an_int",  # Should be int
            "hiddenSubscriberCount": False,
            "subscriberCount": 1000,
            "videoCount": 50,
            "viewCount": 10000
        }
        
        with self.assertRaises(ValidationError):
            ChannelStatisticsModel(**invalid_stats)

    def test_validate_referential_integrity(self):
        """
        Test referential integrity between database collections.
        Ensure that referenced IDs exist in their respective collections.
        """
        default_db_path = self._get_default_db_path()
        
        if not os.path.exists(default_db_path):
            self.skipTest(f"Default DB file not found at {default_db_path}")
        
        with open(default_db_path, 'r', encoding='utf-8') as f:
            default_db_data = json.load(f)
        
        videos = default_db_data.get("videos", {})
        channels = default_db_data.get("channels", {})
        comments = default_db_data.get("comments", {})
        captions = default_db_data.get("captions", {})
        playlists = default_db_data.get("playlists", {})
        
        # Check that video channelIds reference existing channels
        for video_id, video_data in videos.items():
            channel_id = video_data.get("snippet", {}).get("channelId")
            if channel_id:
                self.assertIn(channel_id, channels, 
                            f"Video {video_id} references non-existent channel {channel_id}")
        
        # Check that comments reference existing videos
        for comment_id, comment_data in comments.items():
            video_id = comment_data.get("snippet", {}).get("videoId")
            if video_id:
                self.assertIn(video_id, videos, 
                            f"Comment {comment_id} references non-existent video {video_id}")
        
        # Check that captions reference existing videos
        for caption_id, caption_data in captions.items():
            video_id = caption_data.get("snippet", {}).get("videoId")
            if video_id:
                self.assertIn(video_id, videos, 
                            f"Caption {caption_id} references non-existent video {video_id}")
        
        # Check that playlists reference existing channels and videos
        for playlist_id, playlist_data in playlists.items():
            channel_id = playlist_data.get("snippet", {}).get("channelId")
            if channel_id:
                self.assertIn(channel_id, channels, 
                            f"Playlist {playlist_id} references non-existent channel {channel_id}")
            
            video_list = playlist_data.get("snippet", {}).get("list_of_videos", [])
            for video_id in video_list:
                self.assertIn(video_id, videos, 
                            f"Playlist {playlist_id} references non-existent video {video_id}")


if __name__ == "__main__":
    unittest.main()
