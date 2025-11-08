import unittest
import sys
import os

# Add the parent directory to the path to import the YouTubeAPI
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from youtube import Playlists
from youtube.SimulationEngine.db import DB
from pydantic import ValidationError
from common_utils.error_handling import get_package_error_mode

class BaseTestCaseWithErrorHandler(unittest.TestCase): # Or any TestCase subclass

    def assert_error_behavior(self,
                              func_to_call,
                              expected_exception_type, # The actual exception class, e.g., ValueError
                              expected_message,
                              # You can pass other specific key-value pairs expected
                              # in the dictionary (besides 'exceptionType' and 'message').
                              additional_expected_dict_fields=None,
                              *func_args, **func_kwargs):
        """
        Utility function to test error handling based on the global ERROR_MODE.

        Args:
            self: The TestCase instance.
            func_to_call: The function that might raise an error or return an error dict.
            expected_exception_type (type): The Python class of the exception (e.g., ValueError).
            expected_message (str): The expected error message.
            additional_expected_dict_fields (dict, optional): A dictionary of other
                key-value pairs expected in the error dictionary.
            *func_args: Positional arguments to pass to func_to_call.
            **func_kwargs: Keyword arguments to pass to func_to_call.
        """

        try:
            current_error_mode = get_package_error_mode()
        except NameError:
            self.fail("Global variable ERROR_MODE is not defined. Ensure it's in scope and set.")
            return # Stop further execution of this utility
        if current_error_mode == "raise":
            with self.assertRaises(expected_exception_type) as context:
                func_to_call(*func_args, **func_kwargs)
            if isinstance(context.exception, ValidationError):
                assert expected_message in str(context.exception)
            else:
                self.assertEqual(str(context.exception), expected_message)
        elif current_error_mode == "error_dict":
            result = func_to_call(*func_args, **func_kwargs)

            self.assertIsInstance(result, dict,
                                  f"Function should return a dictionary when ERROR_MODE is 'error_dict'. Got: {type(result)}")

            # Verify the 'exceptionType' field
            self.assertEqual(result.get("exceptionType"), expected_exception_type.__name__,
                             f"Error dictionary 'exceptionType' mismatch. Expected: '{expected_exception_type.__name__}', "
                             f"Got: '{result.get('exceptionType')}'")
            if expected_message:
                self.assertEqual(result.get("message"), expected_message,
                                f"Error dictionary 'message' mismatch. Expected: '{expected_message}', "
                                f"Got: '{result.get('message')}'")

            # Verify any other specified fields in the dictionary
            if additional_expected_dict_fields:
                for key, expected_value in additional_expected_dict_fields.items():
                    self.assertEqual(result.get(key), expected_value,
                                     f"Error dictionary field '{key}' mismatch. Expected: '{expected_value}', "
                                     f"Got: '{result.get(key)}'")
        else:
            self.fail(f"Invalid global ERROR_MODE value: '{current_error_mode}'. "
                      "Expected 'raise' or 'error_dict'.")


class TestPlaylistsMethods(BaseTestCaseWithErrorHandler):
    """Test cases for YouTube playlist-related functions."""

    def setUp(self):
        """Set up test fixtures."""
        DB.clear()
        DB.update({
        "channels": {
        "channel1": {
            "part": "snippet,contentDetails,statistics",
            "categoryId": "10",
            "forUsername": "TechGuru",
            "hl": "en",
            "id": "channel1",
            "managedByMe": False,
            "maxResults": 5,
            "mine": False,
            "mySubscribers": True,
            "onBehalfOfContentOwner": None
        },
        "channel2": {
            "part": "snippet,statistics",
            "categoryId": "20",
            "forUsername": "FoodieFun",
            "hl": "es",
            "id": "channel2",
            "managedByMe": True,
            "maxResults": 10,
            "mine": True,
            "mySubscribers": False,
            "onBehalfOfContentOwner": "CompanyXYZ"
        }},
        "videos": {
        "video1": {
            "id": "video1",
            "snippet": {
                "publishedAt": "2024-03-20T10:00:00Z",
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
                "channelTitle": "TechGuru",
                "tags": ["programming", "tutorial", "coding"],
                "categoryId": "28"
            },
            "statistics": {
                "viewCount": "15000",
                "likeCount": "1200",
                "commentCount": "300",
                "favoriteCount": "500"
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": True,
                "madeForKids": False
            }
        },
        "video2": {
            "id": "video2",
            "snippet": {
                "publishedAt": "2024-03-19T15:30:00Z",
                "channelId": "channel2",
                "title": "Cooking Basics: Pasta Making",
                "description": "Master the art of making homemade pasta from scratch",
                "thumbnails": {
                    "default": {
                        "url": "https://google.com/thumb2.jpg",
                        "width": 120,
                        "height": 90
                    },
                    "medium": {
                        "url": "https://google.com/thumb2_medium.jpg",
                        "width": 320,
                        "height": 180
                    },
                    "high": {
                        "url": "https://google.com/thumb2_high.jpg",
                        "width": 480,
                        "height": 360
                    }
                },
                "channelTitle": "FoodieFun",
                "tags": ["cooking", "pasta", "italian", "food"],
                "categoryId": "26"
            },
            "statistics": {
                "viewCount": "25000",
                "likeCount": "2000",
                "commentCount": "450",
                "favoriteCount": "800"
            },
            "status": {
                "uploadStatus": "processed",
                "privacyStatus": "public",
                "embeddable": True,
                "madeForKids": False
            }
        }},
            "playlists": {
        "PL1234567890": {
            "kind": "youtube#playlist",
            "id": "PL1234567890",
            "snippet": {
                "publishedAt": "2024-01-15T10:00:00Z",
                "channelId": "channel1",
                "title": "Programming Tutorials",
                "description": "A collection of programming tutorials for beginners",
                "list_of_videos": ["video1", "video2"],
                "thumbnails": {
                    "default": {
                        "url": "https://i.ytimg.com/vi/video1/default.jpg",
                        "width": 120,
                        "height": 90
                    },
                    "medium": {
                        "url": "https://i.ytimg.com/vi/video1/mqdefault.jpg",
                        "width": 320,
                        "height": 180
                    },
                    "high": {
                        "url": "https://i.ytimg.com/vi/video1/hqdefault.jpg",
                        "width": 480,
                        "height": 360
                    }
                }
            },
            "status": {
                "privacyStatus": "public"
            },
            "contentDetails": {
                "itemCount": 2
            }
        }}})        

    def test_create_playlist_success(self):
        """Test creating a playlist successfully."""
        result = Playlists.create(
            ownerId="channel1",
            title="My Test Playlist",
            description="A test playlist",
            privacyStatus="public",
            list_of_videos=["video1"]
        )
        self.assertEqual(result["kind"], "youtube#playlist")
        self.assertIn("id", result)
        self.assertEqual(result["snippet"]["title"], "My Test Playlist")
        self.assertEqual(result["snippet"]["description"], "A test playlist")
        self.assertEqual(result["status"]["privacyStatus"], "public")
        self.assertEqual(result["contentDetails"]["itemCount"], 1)

    def test_create_playlist_missing_owner_id(self):
        """Test creating a playlist without owner ID."""
        self.assert_error_behavior(
            Playlists.create, 
            ValueError, 
            "ownerId is required", 
            ownerId="", title="My Test Playlist")

    def test_create_playlist_missing_title(self):
        """Test creating a playlist without title."""
        self.assert_error_behavior(
            Playlists.create, 
            ValueError, 
            "title is required", 
            ownerId="channel1", 
            title="")

    def test_create_playlist_invalid_privacy_status(self):
        """Test creating a playlist with invalid privacy status."""
        self.assert_error_behavior(
            Playlists.create, 
            ValueError, 
            "privacyStatus must be one of ['public', 'private', 'unlisted']", 
            ownerId="channel1", 
            title="My Test Playlist", 
            privacyStatus="invalid")

    def test_create_playlist_video_not_found(self):
        """Test creating a playlist with non-existent video."""
        self.assert_error_behavior(
            Playlists.create, 
            ValueError, 
            "Video with id nonexistent_video not found in the database.", 
            ownerId="channel1",
            title="My Test Playlist",
            list_of_videos=["nonexistent_video"])

    def test_create_playlist_invalid_thumbnails(self):
        """Test creating a playlist with invalid thumbnail format."""
        invalid_thumbnails = {
            "default": {"url": "test.jpg", "width": "invalid", "height": 90}
        }
        with self.assertRaises(ValidationError) as context:
            Playlists.create(ownerId="channel1", title="My Test Playlist", thumbnails=invalid_thumbnails)

    def test_create_playlist_invalid_owner_id(self):
        """Test creating a playlist with invalid owner ID."""
        self.assert_error_behavior(
            Playlists.create, 
            ValueError, 
            "Channel with given ID not found in the database.", 
            ownerId="nonexistent_channel", title="My Test Playlist")

    def test_create_playlist_invalid_owner_id_type(self):
        """Test creating a playlist with invalid owner ID type."""
        self.assert_error_behavior(
            Playlists.create, 
            TypeError, 
            "ownerId must be a string", 
            ownerId=123, title="My Test Playlist")

    def test_create_playlist_invalid_title_type(self):
        """Test creating a playlist with invalid title type."""
        self.assert_error_behavior(
            Playlists.create, 
            TypeError, 
            "title must be a string", 
            ownerId="channel1", title=123)

    def test_create_playlist_invalid_privacy_status_type(self):
        """Test creating a playlist with invalid privacy status type."""
        self.assert_error_behavior(
            Playlists.create, 
            TypeError, 
            "privacyStatus must be a string", 
            ownerId="channel1", title="My Test Playlist", privacyStatus=123)

    def test_create_playlist_invalid_list_of_videos_type(self):
        """Test creating a playlist with invalid list of videos type."""
        self.assert_error_behavior(
            Playlists.create, 
            TypeError, 
            "list_of_videos must be a list", 
            ownerId="channel1", title="My Test Playlist", list_of_videos=123)

    def test_create_playlist_invalid_thumbnails_type(self):
        """Test creating a playlist with invalid thumbnails type."""
        self.assert_error_behavior(
            Playlists.create, 
            TypeError, 
            "thumbnails must be a dictionary", 
            ownerId="channel1", title="My Test Playlist", thumbnails=123)

    def test_list_playlists_all(self):
        """Test listing all playlists."""
        # Create test playlists
        Playlists.create(ownerId="channel1", title="Playlist 1")
        Playlists.create(ownerId="channel2", title="Playlist 2")

        
        result = Playlists.list_playlists()
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 3)

    def test_list_playlists_by_channel_id(self):
        """Test listing playlists by channel ID."""
        # Create test playlists
        Playlists.create(ownerId="channel1", title="Playlist 1")
        Playlists.create(ownerId="channel2", title="Playlist 2")
        
        result = Playlists.list_playlists(channel_id="channel1")
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["snippet"]["channelId"], "channel1")

    def test_list_playlists_empty(self):
        """Test listing playlists when none exist."""
        DB.clear()
        result = Playlists.list_playlists()
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)

    def test_list_playlists_invalid_max_results_type(self):
        """Test listing playlists with invalid max_results type."""
        self.assert_error_behavior(
            Playlists.list_playlists, 
            TypeError, 
            "max_results must be an integer", 
            channel_id="channel1",
            max_results="invalid")

    def test_list_playlists_invalid_max_results_value(self):
        """Test listing playlists with invalid max_results value."""
        self.assert_error_behavior(
            Playlists.list_playlists, 
            ValueError, 
            "max_results must be an integer between 1 and 50", 
            channel_id="channel1",
            max_results=0)

    def test_list_playlists_invalid_channel_id_type(self):
        """Test listing playlists with invalid channel_id type."""
        self.assert_error_behavior(
            Playlists.list_playlists, 
            TypeError, 
            "channel_id must be a string", 
            channel_id=123)

    def test_list_playlists_invalid_channel_id_value(self):
        """Test listing playlists with invalid channel_id value."""
        self.assert_error_behavior(
            Playlists.list_playlists, 
            ValueError, 
            "Channel with given ID not found in the database.", 
            channel_id="nonexistent_channel")

    def test_get_playlist_success(self):
        """Test getting a specific playlist."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Test Playlist")
        playlist_id = created_playlist["id"]
        
        result = Playlists.get(playlist_id)
        self.assertEqual(result["kind"], "youtube#playlist")
        self.assertEqual(result["id"], playlist_id)
        self.assertEqual(result["snippet"]["title"], "Test Playlist")

    def test_get_playlist_not_found(self):
        """Test getting a non-existent playlist."""
        self.assert_error_behavior(
            Playlists.get, 
            ValueError, 
            "Playlist with given ID not found in the database.", 
            playlist_id="nonexistent_id")

    def test_get_playlist_no_id(self):
        """Test getting a playlist without ID."""
        self.assert_error_behavior(
            Playlists.get, 
            ValueError, 
            "playlist_id is required", 
            playlist_id="")

    def test_update_playlist_success(self):
        """Test updating a playlist successfully."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Original Title")
        playlist_id = created_playlist["id"]
        
        # Update the playlist
        result = Playlists.update(
            playlist_id=playlist_id,
            title="Updated Title",
            description="Updated description",
            privacyStatus="private"
        )
        self.assertEqual(result["snippet"]["title"], "Updated Title")
        self.assertEqual(result["snippet"]["description"], "Updated description")
        self.assertEqual(result["status"]["privacyStatus"], "private")

    def test_update_playlist_empty_title(self):
        """Test updating a playlist with empty title."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Original Title")
        playlist_id = created_playlist["id"]
        
        self.assert_error_behavior(
            Playlists.update, 
            ValueError, 
            "title cannot be empty", 
            playlist_id=playlist_id, 
            title="")

    def test_update_playlist_invalid_thumbnails(self):
        """Test updating a playlist with invalid thumbnail format."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Test Playlist")
        playlist_id = created_playlist["id"]
        
        invalid_thumbnails = {
            "default": {"url": "test.jpg", "width": "invalid", "height": 90}
        }
        with self.assertRaises(ValidationError) as context:
            Playlists.update(playlist_id=playlist_id, thumbnails=invalid_thumbnails)

    def test_update_playlist_not_found(self):
        """Test updating a non-existent playlist."""
        self.assert_error_behavior(
            Playlists.update, 
            ValueError, 
            "Playlist with given ID not found in the database.", 
            playlist_id="nonexistent", 
            title="Updated Title")

    def test_update_playlist_invalid_privacy_status(self):
        """Test updating a playlist with invalid privacy status."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Test Playlist")
        playlist_id = created_playlist["id"]
        
        self.assert_error_behavior(
            Playlists.update, 
            ValueError, 
            "privacyStatus must be one of ['public', 'private', 'unlisted']", 
            playlist_id=playlist_id, 
            privacyStatus="invalid")

    def test_delete_playlist_success(self):
        """Test deleting a playlist successfully."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Test Playlist")
        playlist_id = created_playlist["id"]
        
        # Delete the playlist
        result = Playlists.delete(playlist_id)
        self.assertTrue(result)
        self.assertNotIn(playlist_id, DB.get("playlists", {}))

    def test_delete_playlist_not_found(self):
        """Test deleting a non-existent playlist."""
        self.assert_error_behavior(
            Playlists.delete, 
            ValueError, 
            "Playlist with given ID not found in the database.", 
            playlist_id="nonexistent_id")

    def test_delete_playlist_invalid_id_type(self):
        """Test deleting a playlist with invalid ID type."""
        self.assert_error_behavior(
            Playlists.delete, 
            TypeError, 
            "playlist_id must be a string", 
            playlist_id=123)

    def test_add_video_success(self):
        """Test adding a video to a playlist successfully."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Test Playlist")
        playlist_id = created_playlist["id"]
        
        # Add a video to the playlist
        result = Playlists.add_video(playlist_id, "video1")
        self.assertEqual(result["contentDetails"]["itemCount"], 1)
        self.assertIn("video1", result["snippet"]["list_of_videos"])

    def test_add_video_duplicate(self):
        """Test adding a video that's already in the playlist (should work now)."""
        # Create a test playlist with a video
        created_playlist = Playlists.create(
            ownerId="channel1", 
            title="Test Playlist",
            list_of_videos=["video1"]
        )
        playlist_id = created_playlist["id"]
        
        result = Playlists.add_video(playlist_id, "video1")
        self.assertEqual(result["contentDetails"]["itemCount"], 2)
        self.assertEqual(result["snippet"]["list_of_videos"].count("video1"), 2)

    def test_add_video_playlist_not_found(self):
        """Test adding a video to a non-existent playlist."""
        self.assert_error_behavior(
            Playlists.add_video, 
            ValueError, 
            "Playlist with given ID not found in the database.", 
            playlist_id="nonexistent_playlist", 
            video_id="video1")

    def test_add_video_video_not_found(self):
        """Test adding a non-existent video to a playlist."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Test Playlist")
        playlist_id = created_playlist["id"]
        
        self.assert_error_behavior(
            Playlists.add_video, 
            ValueError, 
            "Video with given ID not found in the database.", 
            playlist_id=playlist_id, 
            video_id="nonexistent_video")

    def test_add_video_invalid_playlist_id_type(self):
        """Test adding a video to a playlist with invalid ID type."""
        self.assert_error_behavior(
            Playlists.add_video, 
            TypeError, 
            "playlist_id must be a string", 
            playlist_id=123, video_id="video1")

    def test_add_video_invalid_video_id_type(self):
        """Test adding a video to a playlist with invalid ID type."""
        self.assert_error_behavior(
            Playlists.add_video, 
            TypeError, 
            "video_id must be a string", 
            playlist_id="playlist_id", video_id=123)

    def test_delete_video_success(self):
        """Test removing a video from a playlist successfully."""
        # Create a test playlist with a video
        created_playlist = Playlists.create(
            ownerId="channel1", 
            title="Test Playlist",
            list_of_videos=["video1", "video2"]
        )
        playlist_id = created_playlist["id"]
        
        # Remove a video from the playlist
        result = Playlists.delete_video(playlist_id, "video1")
        self.assertTrue(result)
        
        # Verify video is removed
        updated_playlist = Playlists.get(playlist_id)
        self.assertEqual(updated_playlist["contentDetails"]["itemCount"], 1)
        self.assertNotIn("video1", updated_playlist["snippet"]["list_of_videos"])
        self.assertIn("video2", updated_playlist["snippet"]["list_of_videos"])

    def test_delete_video_playlist_not_found(self):
        """Test removing a video from a non-existent playlist."""
        self.assert_error_behavior(
            Playlists.delete_video, 
            ValueError, 
            "Playlist with given ID not found in the database.", 
            playlist_id="nonexistent_playlist", 
            video_id="video1")

    def test_delete_video_not_in_playlist(self):
        """Test removing a video that's not in the playlist."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Empty Playlist")
        playlist_id = created_playlist["id"]
        
        self.assert_error_behavior(
            Playlists.delete_video, 
            ValueError, 
            "Video with given ID is not in the playlist.", 
            playlist_id=playlist_id, 
            video_id="video1")

    def test_delete_video_invalid_playlist_id_type(self):
        """Test deleting a video from a playlist with invalid ID type."""
        self.assert_error_behavior(
            Playlists.delete_video, 
            TypeError, 
            "playlist_id must be a string", 
            playlist_id=123, video_id="video1")

    def test_delete_video_invalid_video_id_type(self):
        """Test deleting a video from a playlist with invalid ID type."""
        self.assert_error_behavior(
            Playlists.delete_video, 
            TypeError, 
            "video_id must be a string", 
            playlist_id="playlist_id", video_id=123)

    def test_delete_video_invalid_playlist_id_missing(self):
        """Test deleting a video from a playlist with invalid ID type."""
        self.assert_error_behavior(
            Playlists.delete_video, 
            ValueError, 
            "playlist_id is required", 
            playlist_id="", video_id="video1")

    def test_delete_video_invalid_video_id_missing(self):
        """Test deleting a video from a playlist with invalid ID type."""
        self.assert_error_behavior(
            Playlists.delete_video, 
            ValueError, 
            "video_id is required", 
            playlist_id="playlist_id", video_id="")

    def test_reorder_videos_success(self):
        """Test reordering videos in a playlist successfully."""
        # Create a test playlist with videos
        created_playlist = Playlists.create(
            ownerId="channel1", 
            title="Test Playlist",
            list_of_videos=["video1", "video2"]
        )
        playlist_id = created_playlist["id"]
        
        # Reorder videos
        new_order = ["video2", "video1"]
        result = Playlists.reorder(playlist_id, new_order)
        self.assertEqual(result["snippet"]["list_of_videos"], new_order)

    def test_reorder_videos_playlist_not_found(self):
        """Test reordering videos in a non-existent playlist."""
        self.assert_error_behavior(
            Playlists.reorder, 
            ValueError, 
            "Playlist with given ID not found in the database.", 
            playlist_id="nonexistent_playlist", 
            video_order=["video1", "video2"])

    def test_reorder_videos_empty_order(self):
        """Test reordering videos with empty order list."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Test Playlist")
        playlist_id = created_playlist["id"]
        
        self.assert_error_behavior(
            Playlists.reorder, 
            ValueError, 
            "video_order is required", 
            playlist_id=playlist_id, 
            video_order=[])

    def test_reorder_videos_invalid_order(self):
        """Test reordering videos with invalid order."""
        # Create a test playlist with videos
        created_playlist = Playlists.create(
            ownerId="channel1", 
            title="Test Playlist",
            list_of_videos=["video1", "video2"]
        )
        playlist_id = created_playlist["id"]
        
        # Try to reorder with different videos
        self.assert_error_behavior(
            Playlists.reorder, 
            ValueError, 
            "video_order must contain the same videos as the current playlist", 
            playlist_id=playlist_id, 
            video_order=["video1", "video3"])

    def test_reorder_videos_invalid_type(self):
        """Test reordering videos with invalid type."""
        # Create a test playlist
        created_playlist = Playlists.create(ownerId="channel1", title="Test Playlist")
        playlist_id = created_playlist["id"]
        
        # Test with None instead of invalid list type
        self.assert_error_behavior(
            Playlists.reorder, 
            ValueError, 
            "video_order is required", 
            playlist_id=playlist_id, 
            video_order=None)

    def test_reorder_videos_invalid_playlist_id_missing(self):
        """Test reordering videos in a playlist with invalid ID type."""
        self.assert_error_behavior(
            Playlists.reorder, 
            ValueError, 
            "playlist_id is required", 
            playlist_id="", video_order=["video1", "video2"])


if __name__ == "__main__":
    unittest.main() 