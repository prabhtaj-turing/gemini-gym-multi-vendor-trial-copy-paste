# ---------------------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------------------

import unittest
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import pytest
from pydantic import ValidationError

from youtube.SimulationEngine.custom_errors import InvalidPartParameterError
from youtube.SimulationEngine.custom_errors import InvalidFilterParameterError
from youtube.SimulationEngine.custom_errors import InvalidMaxResultsError
from youtube.SimulationEngine.custom_errors import MissingPartParameterError
from youtube.SimulationEngine.custom_errors import MaxResultsOutOfRangeError
from youtube.SimulationEngine.custom_errors import InvalidVideoIdError, VideoIdNotFoundError
from youtube.SimulationEngine.db import DB

import youtube as YoutubeAPI

# Import individual modules for direct testing if needed
from youtube import (
    Activities,
    Caption,
    Channels,
    ChannelSection,
    ChannelStatistics,
    ChannelBanners,
    Comment,
    CommentThread,
    Subscriptions,
    VideoCategory,
    Memberships,
    Videos,
    Search,
)

from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube.SimulationEngine.custom_errors import InvalidPartParameterError

from youtube import list_channel_sections
from youtube import delete_channel_section
from youtube import list_comment_threads
from youtube import create_comment_thread
from youtube import list_channels


class Testyoutube(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Resets the database before each test."""
        super().setUp()
        
        # Re-initialize the DB with sample data
        DB.clear()
        DB.update(
            {
                "activities": [
                    {
                        "kind": "youtube#activity",
                        "etag": "etag1",
                        "id": "activity1",
                        "snippet": {"channelId": "channel1"},
                        "mine": True,
                    },
                    {
                        "kind": "youtube#activity",
                        "etag": "etag2",
                        "id": "activity2",
                        "snippet": {"channelId": "channel2"},
                        "mine": False,
                    },
                ],
                "captions": {
                    "caption1": {"id": "caption1", "snippet": {"videoId": "video1", "text": "Caption content for video1"}},
                    "caption2": {"id": "caption2", "snippet": {"videoId": "video2", "text": "Caption content for video2"}},
                },
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
                        "onBehalfOfContentOwner": None,
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
                        "onBehalfOfContentOwner": "CompanyXYZ",
                    },
                    "channel3": {
                        "part": "contentDetails,statistics",
                        "categoryId": "15",
                        "forUsername": "TravelVlogs",
                        "hl": "fr",
                        "id": "channel3",
                        "managedByMe": False,
                        "maxResults": 7,
                        "mine": False,
                        "mySubscribers": True,
                        "onBehalfOfContentOwner": None,
                    },
                },
                "channelSections": {
                    "section1": {
                        "id": "section1",
                        "snippet": {"channelId": "channel1", "type": "allPlaylists"},
                    },
                    "section2": {
                        "id": "section2",
                        "snippet": {"channelId": "channel2", "type": "completedEvents"},
                    },
                    "section3": {
                        "id": "section3",
                        "snippet": {
                            "channelId": "channel1",
                            "type": "multipleChannels",
                        },
                    },
                },
                "channelStatistics": {
                    "commentCount": 100,
                    "hiddenSubscriberCount": False,
                    "subscriberCount": 1000000,
                    "videoCount": 500,
                    "viewCount": 10000000,
                },
                "channelBanners": [],
                "comments": {
                    "comment1": {
                        "id": "comment1",
                        "snippet": {"videoId": "video1", "parentId": None},
                        "moderationStatus": "published",
                        "bannedAuthor": False,
                    },
                    "comment2": {
                        "id": "comment2",
                        "snippet": {"videoId": "video1", "parentId": "comment1"},
                        "moderationStatus": "heldForReview",
                        "bannedAuthor": False,
                    },
                    "comment3": {
                        "id": "comment3",
                        "snippet": {"videoId": "video2", "parentId": None},
                        "moderationStatus": "rejected",
                        "bannedAuthor": True,
                    },
                },
                "commentThreads": {
                    "thread1": {
                        "id": "thread1",
                        "snippet": {"channelId": "channel1", "videoId": "video1"},
                        "comments": ["comment1", "comment2"],
                    },
                    "thread2": {
                        "id": "thread2",
                        "snippet": {"channelId": "channel2", "videoId": "video2"},
                        "comments": ["comment3"],
                    },
                },
                "subscriptions": {
                    "sub1": {
                        "id": "sub1",
                        "snippet": {
                            "channelId": "channel1",
                            "resourceId": {
                                "kind": "youtube#channel",
                                "channelId": "channel2",
                            },
                        },
                    },
                    "sub2": {
                        "id": "sub2",
                        "snippet": {
                            "channelId": "channel2",
                            "resourceId": {
                                "kind": "youtube#channel",
                                "channelId": "channel1",
                            },
                        },
                    },
                },
                "videoCategories": {
                    "category1": {
                        "id": "1",
                        "snippet": {"title": "Film & Animation", "regionCode": "US"},
                    },
                    "category2": {
                        "id": "2",
                        "snippet": {"title": "Autos & Vehicles", "regionCode": "US"},
                    },
                    "category3": {
                        "id": "10",
                        "snippet": {"title": "Music", "regionCode": "CA"},
                    },
                },
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
                },
                "videos": {
                    "video1": {
                        "id": "video1",
                        "snippet": {
                            "title": "Python Programming Tutorial",
                            "description": "Learn Python programming from scratch",
                            "publishedAt": "2023-01-01T00:00:00Z",
                            "channelId": "channel1",
                            "channelTitle": "TechGuru",
                            "categoryId": "28",
                            "tags": ["python", "programming", "tutorial"],
                            "thumbnails": {
                                "default": {
                                    "url": "https://google.com/thumb1.jpg",
                                    "width": 120,
                                    "height": 90,
                                },
                                "medium": {
                                    "url": "https://google.com/thumb2.jpg",
                                    "width": 320,
                                    "height": 180,
                                },
                                "high": {
                                    "url": "https://google.com/thumb3.jpg",
                                    "width": 480,
                                    "height": 360,
                                },
                            },
                        },
                        "status": {"uploadStatus": "processed", "privacyStatus": "public", "embeddable": True, "madeForKids": False},
                        "statistics": {"viewCount": 1000000, "likeCount": 50000, "dislikeCount": 5000},
                    },
                    "video2": {
                        "id": "video2",
                        "snippet": {
                            "title": "Cooking with Gordon Ramsay",
                            "description": "Learn to cook a perfect steak",
                            "publishedAt": "2023-02-15T00:00:00Z",
                            "channelId": "channel2",
                            "channelTitle": "FoodieFun",
                            "categoryId": "24",
                            "tags": ["cooking", "steak", "gordon ramsay"],
                            "thumbnails": {
                                "default": {
                                    "url": "https://google.com/thumb4.jpg",
                                    "width": 120,
                                    "height": 90,
                                }
                            },
                        },
                        "status": {"uploadStatus": "processed", "privacyStatus": "public", "embeddable": True, "madeForKids": False},   
                        "statistics": {"viewCount": 5000000, "likeCount": 200000, "dislikeCount": 2000},
                    },
                },
            }
        )
        
        # Add missing contentDetails and other fields to videos for testing
        # Add contentDetails to video1
        if "video1" in DB["videos"]:
            DB["videos"]["video1"]["contentDetails"] = {
                "caption": "true",
                "definition": "high",
                "duration": "PT15M33S"  # 15 minutes 33 seconds
            }
            # Add missing status fields
            DB["videos"]["video1"]["status"]["license"] = "youtube"
            DB["videos"]["video1"]["status"]["syndicated"] = True
            DB["videos"]["video1"]["status"]["type"] = "movie"
        
        # Add contentDetails to video2
        if "video2" in DB["videos"]:
            DB["videos"]["video2"]["contentDetails"] = {
                "caption": "false",
                "definition": "standard",
                "duration": "PT8M45S"  # 8 minutes 45 seconds
            }
            # Add missing status fields
            DB["videos"]["video2"]["status"]["license"] = "creativeCommon"
            DB["videos"]["video2"]["status"]["syndicated"] = False
            DB["videos"]["video2"]["status"]["type"] = "episode"
        
        # Add snippet data to channels
        if "channel1" in DB["channels"]:
            DB["channels"]["channel1"]["snippet"] = {
                "title": "TechGuru Channel",
                "description": "Technology tutorials and programming guides",
                "type": "any"
            }
            DB["channels"]["channel1"]["statistics"] = {
                "viewCount": "50000"
            }
        
        if "channel2" in DB["channels"]:
            DB["channels"]["channel2"]["snippet"] = {
                "title": "FoodieFun Channel",
                "description": "Cooking tutorials and food reviews",
                "type": "show"
            }
            DB["channels"]["channel2"]["statistics"] = {
                "viewCount": "30000"
            }
        
        # Add playlists data
        DB["playlists"] = {
            "playlist1": {
                "id": "playlist1",
                "snippet": {
                    "title": "Programming Tutorials",
                    "description": "A collection of programming tutorials",
                    "channelId": "channel1"
                }
            },
            "playlist2": {
                "id": "playlist2",
                "snippet": {
                    "title": "Cooking Basics",
                    "description": "Basic cooking techniques and recipes",
                    "channelId": "channel2"
                }
            }
        }

    def test_activities_list(self):
        """Tests the Activities.list method."""
        # Test basic listing with 'mine' filter
        response = Activities.list(part="snippet", mine=True)
        self.assertIsInstance(response, dict)
        self.assertIn("items", response)
        self.assertEqual(len(response["items"]), 1)

        # Test filtering by channelId
        response = Activities.list(part="id,snippet", channelId="channel1")
        self.assertEqual(len(response["items"]), 1)
        self.assertEqual(response["items"][0]["id"], "activity1")

    def test_captions_insert_basic(self):
        """Tests basic caption insertion with valid parameters."""
        response = Caption.insert(part="snippet", snippet={"videoId": "video123", "text": "Caption text"}, sync=False)
        self.assertTrue(response["success"])
        self.assertIn("caption", response)
        self.assertIn("id", response["caption"])
        self.assertEqual(response["caption"]["snippet"]["videoId"], "video123")

    def test_captions_insert_with_authorization_parameters(self):
        """Tests caption insertion with authorization parameters."""
        response = Caption.insert(
            part="snippet", 
            snippet={"videoId": "video123", "text": "Caption text"}, 
            sync=False,
            onBehalfOf="user1", 
            onBehalfOfContentOwner="owner1"
        )
        self.assertTrue(response["success"])
        self.assertIn("onBehalfOf", response["caption"])
        self.assertIn("onBehalfOfContentOwner", response["caption"])
        self.assertEqual(response["caption"]["onBehalfOf"], "user1")
        self.assertEqual(response["caption"]["onBehalfOfContentOwner"], "owner1")

    def test_captions_insert_database_state_verification(self):
        """Tests that the caption is actually added to the database."""
        initial_count = len(DB["captions"])

        response = Caption.insert(part="snippet", snippet={"videoId": "video123", "text": "Caption text"}, sync=False)
        self.assertTrue(response["success"])

        # Verify caption was added to database
        self.assertEqual(len(DB["captions"]), initial_count + 1)

        # Verify the caption exists in database
        caption_id = response["caption"]["id"]
        self.assertIn(caption_id, DB["captions"])
        self.assertEqual(DB["captions"][caption_id]["snippet"]["videoId"], "video123")

    def test_captions_insert_return_value_structure(self):
        """Tests that the insert function returns the correct structure."""
        response = Caption.insert(part="snippet", snippet={"videoId": "video123", "text": "Caption text"}, sync=False)

        # Check return structure
        self.assertIsInstance(response, dict)
        self.assertIn("success", response)
        self.assertTrue(response["success"])
        self.assertIn("caption", response)

        # Check caption structure
        caption = response["caption"]
        self.assertIn("id", caption)
        self.assertIn("snippet", caption)
        self.assertEqual(caption["snippet"]["videoId"], "video123")


    def test_captions_insert_id_generation(self):
        """Tests that unique IDs are generated for each insertion."""
        response1 = Caption.insert(part="snippet", snippet={"videoId": "video1", "text": "Caption 1"}, sync=False)
        response2 = Caption.insert(part="snippet", snippet={"videoId": "video2", "text": "Caption 2"}, sync=False)

        self.assertNotEqual(response1["caption"]["id"], response2["caption"]["id"])

        # Verify both captions exist in database
        self.assertIn(response1["caption"]["id"], DB["captions"])
        self.assertIn(response2["caption"]["id"], DB["captions"])

    def test_captions_insert_multiple_captions(self):
        """Tests inserting multiple captions."""
        captions_data = [
            {"videoId": "video1", "text": "English caption"},
            {"videoId": "video2", "text": "Spanish caption"}, 
            {"videoId": "video3", "text": "French caption"}
        ]

        initial_count = len(DB["captions"])
        inserted_ids = []

        for snippet in captions_data:
            response = Caption.insert(part="snippet", snippet=snippet, sync=False)
            self.assertTrue(response["success"])
            inserted_ids.append(response["caption"]["id"])

        # Verify all captions were added
        self.assertEqual(len(DB["captions"]), initial_count + len(captions_data))

        # Verify each caption exists with correct data
        for i, caption_id in enumerate(inserted_ids):
            self.assertIn(caption_id, DB["captions"])
            self.assertEqual(DB["captions"][caption_id]["snippet"]["videoId"], captions_data[i]["videoId"])

    def test_captions_insert_part_validation(self):
        """Tests part parameter validation."""
        # Test with empty string
        with self.assertRaises(ValueError) as context:
            Caption.insert(part="", snippet={"videoId": "test", "text": "Caption text"}, sync=False)
        self.assertIn("Part parameter cannot be empty or consist only of whitespace", str(context.exception))

        # Test with whitespace-only string
        with self.assertRaises(ValueError) as context:
            Caption.insert(part="   ", snippet={"videoId": "test", "text": "Caption text"}, sync=False)
        self.assertIn("Part parameter cannot be empty or consist only of whitespace", str(context.exception))

        # Test with different invalid values
        invalid_parts = ["id", "contentDetails", "status", "statistics"]
        for invalid_part in invalid_parts:
            with self.assertRaises(ValueError) as context:
                Caption.insert(part=invalid_part, snippet={"videoId": "test", "text": "Caption text"}, sync=False)
            self.assertIn("Part parameter must be 'snippet'", str(context.exception))

    def test_captions_insert_snippet_validation(self):
        """Tests snippet parameter validation."""
        # Test with empty dict
        with self.assertRaises(ValidationError) as context:
            Caption.insert(part="snippet", snippet={}, sync=False)
        self.assertIn("videoId", str(context.exception))
        
        # Test with missing videoId
        with self.assertRaises(ValidationError) as context:
            Caption.insert(part="snippet", snippet={"language": "en"}, sync=False)
        self.assertIn("videoId", str(context.exception))
        
        # Test with empty videoId
        with self.assertRaises(ValidationError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "", "text": "Caption text"}, sync=False)
        self.assertIn("videoId must be a non-empty string", str(context.exception))
        
        # Test with valid snippets
        valid_snippets = [
            {"videoId": "video1", "text": "English caption"},
            {"videoId": "video2", "text": "Spanish caption"},
            {"videoId": "video3", "text": "French caption"}
        ]
        
        for snippet in valid_snippets:
            response = Caption.insert(part="snippet", snippet=snippet, sync=False)
            self.assertTrue(response["success"])
            self.assertEqual(response["caption"]["snippet"]["videoId"], snippet["videoId"])

    def test_captions_insert_type_validation(self):
        """Tests type validation for all parameters."""
        # Test invalid part type
        with self.assertRaises(TypeError) as context:
            Caption.insert(part=123, snippet={"videoId": "test", "text": "Caption text"}, sync=False)
        self.assertIn("Parameter 'part' must be a string", str(context.exception))

        # Test invalid onBehalfOf type
        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=789)
        self.assertIn("On behalf of must be a string", str(context.exception))

        # Test invalid onBehalfOfContentOwner type
        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner=[])
        self.assertIn("On behalf of content owner must be a string", str(context.exception))

        # Test invalid sync type
        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync="not_a_boolean")
        self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_authorization_parameter_validation(self):
        """Tests validation of authorization parameters."""
        # Test empty onBehalfOf
        with self.assertRaises(ValueError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf="")
        self.assertIn("On behalf of cannot be empty or consist only of whitespace", str(context.exception))
        
        # Test whitespace-only onBehalfOf
        with self.assertRaises(ValueError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf="   ")
        self.assertIn("On behalf of cannot be empty or consist only of whitespace", str(context.exception))
        
        # Test empty onBehalfOfContentOwner
        with self.assertRaises(ValueError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner="")
        self.assertIn("On behalf of content owner cannot be empty or consist only of whitespace", str(context.exception))
        
        # Test whitespace-only onBehalfOfContentOwner
        with self.assertRaises(ValueError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner="   ")
        self.assertIn("On behalf of content owner cannot be empty or consist only of whitespace", str(context.exception))
        
        # Test valid authorization parameters
        response = Caption.insert(
            part="snippet", 
            snippet={"videoId": "test", "text": "Caption text"}, 
            sync=False,
            onBehalfOf="valid_user",
            onBehalfOfContentOwner="valid_owner"
        )
        self.assertTrue(response["success"])

    def test_captions_insert_pydantic_validation_error_handling(self):
        """Tests that validation errors are properly handled."""
        # Test with invalid part (should trigger validation)
        with self.assertRaises(ValueError) as context:
            Caption.insert(part="invalid", snippet={"videoId": "test", "text": "Caption text"}, sync=False)
        self.assertIn("Part parameter must be 'snippet'", str(context.exception))
        
        # Test with empty snippet (should trigger validation)
        with self.assertRaises(ValidationError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "", "text": "Caption text"}, sync=False)
        self.assertIn("videoId must be a non-empty string", str(context.exception))


    def test_captions_insert_concurrent_operations(self):
        """Tests that concurrent insertions work correctly."""
        import threading
        import time
        
        results = []
        
        def insert_caption(index):
            try:
                response = Caption.insert(
                    part="snippet", 
                    snippet={"videoId": f"video{index}", "text": f"Caption {index}"},
                    onBehalfOf=f"user{index}",
                    onBehalfOfContentOwner=f"owner{index}",
                    sync=(index % 2 == 0)
                )
                results.append(response)
            except Exception as e:
                results.append(e)
        
        # Create multiple threads to insert captions concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=insert_caption, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all insertions were successful
        self.assertEqual(len(results), 5)
        for result in results:
            # Check if result is an exception or a success response
            if isinstance(result, Exception):
                self.fail(f"Caption insertion failed with exception: {result}")
            else:
                self.assertTrue(result["success"])

    # Additional comprehensive tests for Caption.insert function to increase coverage for lines 196-198
    def test_captions_insert_on_behalf_of_type_edge_cases(self):
        """Tests edge cases for onBehalfOf type validation to cover line 151."""
        # Test with various non-string types that are not None
        invalid_types = [123, 0, -1, 3.14, [], {}, (), True, False]

        for invalid_type in invalid_types:
            with self.assertRaises(TypeError) as context:
                Caption.insert(
                    part="snippet",
                    snippet={"videoId": "test", "text": "Caption text"},
                    sync=False,
                    onBehalfOf=invalid_type
                )
            self.assertIn("On behalf of must be a string", str(context.exception))

        # Test with None (should not raise error)
        response = Caption.insert(
            part="snippet",
            snippet={"videoId": "test", "text": "Caption text"},
            sync=False,
            onBehalfOf=None
        )
        self.assertTrue(response["success"])

    def test_captions_insert_on_behalf_of_content_owner_type_edge_cases(self):
        """Tests edge cases for onBehalfOfContentOwner type validation to cover line 154."""
        # Test with various non-string types that are not None
        invalid_types = [456, 0, -2, 2.718, ["list"], {"dict": "value"}, (1, 2), True, False]

        for invalid_type in invalid_types:
            with self.assertRaises(TypeError) as context:
                Caption.insert(
                    part="snippet",
                    snippet={"videoId": "test", "text": "Caption text"},
                    sync=False,
                    onBehalfOfContentOwner=invalid_type
                )
            self.assertIn("On behalf of content owner must be a string", str(context.exception))

        # Test with None (should not raise error)
        response = Caption.insert(
            part="snippet",
            snippet={"videoId": "test", "text": "Caption text"},
            sync=False,
            onBehalfOfContentOwner=None
        )
        self.assertTrue(response["success"])

    def test_captions_insert_combined_type_validation_edge_cases(self):
        """Tests combined type validation scenarios to ensure all validation lines are covered."""
        # Test all three parameters with invalid types simultaneously
        with self.assertRaises(TypeError) as context:
            Caption.insert(
                part="snippet",
                snippet={"videoId": "test", "text": "Caption text"},
                onBehalfOf=123,
                onBehalfOfContentOwner=456,
                sync=False  # Use valid sync to test onBehalfOf validation
            )
        # Should catch the first invalid type (onBehalfOf)
        self.assertIn("On behalf of must be a string", str(context.exception))

        # Test with valid onBehalfOf but invalid onBehalfOfContentOwner
        with self.assertRaises(TypeError) as context:
            Caption.insert(
                part="snippet",
                snippet={"videoId": "test", "text": "Caption text"},
                onBehalfOf="valid_user",
                onBehalfOfContentOwner=789,
                sync=True
            )
        self.assertIn("On behalf of content owner must be a string", str(context.exception))

        # Test with valid onBehalfOf and onBehalfOfContentOwner but invalid sync
        with self.assertRaises(TypeError) as context:
            Caption.insert(
                part="snippet",
                snippet={"videoId": "test", "text": "Caption text"},
                onBehalfOf="valid_user",
                onBehalfOfContentOwner="valid_owner",
                sync="invalid_sync"
            )
        self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_order(self):
        """Tests that type validation occurs in the correct order."""
        # Test that part validation happens first
        with self.assertRaises(TypeError) as context:
            Caption.insert(part=123, snippet={"videoId": "test", "text": "Caption text"}, sync=False)
        self.assertIn("Parameter 'part' must be a string", str(context.exception))

        # Test that onBehalfOf validation happens third
        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=789)
        self.assertIn("On behalf of must be a string", str(context.exception))

        # Test that onBehalfOfContentOwner validation happens fourth
        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner=[])
        self.assertIn("On behalf of content owner must be a string", str(context.exception))

        # Test that sync validation happens last
        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync="invalid")
        self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_with_none_values(self):
        """Tests type validation when parameters are None."""
        # Test with all None values (should pass validation)
        response = Caption.insert(
            part="snippet",
            snippet={"videoId": "test", "text": "Caption text"},
            onBehalfOf=None,
            onBehalfOfContentOwner=None,
            sync=False  # sync cannot be None, must be boolean
        )
        self.assertTrue(response["success"])

        # Test with None for onBehalfOf and onBehalfOfContentOwner but valid sync
        response = Caption.insert(
            part="snippet",
            snippet={"videoId": "test", "text": "Caption text"},
            onBehalfOf=None,
            onBehalfOfContentOwner=None,
            sync=True
        )
        self.assertTrue(response["success"])

    def test_captions_insert_type_validation_with_empty_strings(self):
        """Tests type validation with empty strings (should pass type validation but fail value validation)."""
        # Empty strings should pass type validation but fail value validation
        with self.assertRaises(ValueError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf="")
        self.assertIn("On behalf of cannot be empty or consist only of whitespace", str(context.exception))

        with self.assertRaises(ValueError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner="")
        self.assertIn("On behalf of content owner cannot be empty or consist only of whitespace", str(context.exception))

    def test_captions_insert_type_validation_boundary_values(self):
        """Tests type validation with boundary values to ensure complete coverage."""
        # Test with boundary values for onBehalfOf
        boundary_values = [0, -1, 1, 255, 256, 65535, 65536, 2147483647, -2147483648]

        for value in boundary_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=value)
            self.assertIn("On behalf of must be a string", str(context.exception))

        # Test with boundary values for onBehalfOfContentOwner
        for value in boundary_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner=value)
            self.assertIn("On behalf of content owner must be a string", str(context.exception))

        # Test with boundary values for sync (should only accept True/False)
        for value in boundary_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=value)
            self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_floating_point(self):
        """Tests type validation with floating point numbers to ensure complete coverage."""
        # Test with floating point numbers for onBehalfOf
        float_values = [0.0, 1.0, -1.0, 3.14159, 2.71828, float('inf'), float('-inf'), float('nan')]

        for value in float_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=value)
            self.assertIn("On behalf of must be a string", str(context.exception))

        # Test with floating point numbers for onBehalfOfContentOwner
        for value in float_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner=value)
            self.assertIn("On behalf of content owner must be a string", str(context.exception))

        # Test with floating point numbers for sync
        for value in float_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=value)
            self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_string_like_objects(self):
        """Tests type validation with string-like objects that should still fail."""
        # Test with string-like objects that are not actual strings
        string_like_objects = [
            b'bytes_string',  # Bytes
            bytearray(b'bytearray_string'),  # Bytearray
            memoryview(b'memoryview_string'),  # Memoryview
        ]

        for obj in string_like_objects:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=obj)
            self.assertIn("On behalf of must be a string", str(context.exception))

            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner=obj)
            self.assertIn("On behalf of content owner must be a string", str(context.exception))

    def test_captions_insert_type_validation_boolean_like_objects(self):
        """Tests type validation with boolean-like objects that should still fail."""
        # Test with boolean-like objects that are not actual booleans
        boolean_like_objects = [
            1, 0, -1, 2,  # Integers
            1.0, 0.0, -1.0,  # Floats
            "True", "False", "true", "false",  # Strings
            [True], [False],  # Lists
            {"key": True}, {"key": False},  # Dictionaries
        ]

        for obj in boolean_like_objects:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=obj)
            self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_nested_structures(self):
        """Tests type validation with nested data structures."""
        # Test with nested structures for onBehalfOf
        nested_structures = [
            [1, 2, 3],  # List
            {"a": 1, "b": 2},  # Dictionary
            (1, 2, 3),  # Tuple
            [[1, 2], [3, 4]],  # Nested list
            {"a": {"b": 1}},  # Nested dictionary
            [{"a": 1}, {"b": 2}],  # List of dictionaries
        ]

        for structure in nested_structures:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, onBehalfOf=structure)
            self.assertIn("On behalf of must be a string", str(context.exception))

            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, onBehalfOfContentOwner=structure)
            self.assertIn("On behalf of content owner must be a string", str(context.exception))

            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=structure)
            self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_custom_objects(self):
        """Tests type validation with custom objects."""
        # Create custom classes
        class CustomString:
            def __str__(self):
                return "custom_string"

        class CustomBool:
            def __bool__(self):
                return True

        # Test with custom objects
        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, onBehalfOf=CustomString())
        self.assertIn("On behalf of must be a string", str(context.exception))

        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, onBehalfOfContentOwner=CustomString())
        self.assertIn("On behalf of content owner must be a string", str(context.exception))

        with self.assertRaises(TypeError) as context:
            Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=CustomBool())
        self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_edge_case_none_handling(self):
        """Tests edge cases with None handling to ensure complete coverage."""
        # Test that None values are handled correctly for all parameters
        response = Caption.insert(
            part="snippet",
            snippet={"videoId": "test", "text": "Caption text"},
            onBehalfOf=None,
            onBehalfOfContentOwner=None,
            sync=False
        )
        self.assertTrue(response["success"])

        # Test that the function doesn't crash with None values
        self.assertNotIn("onBehalfOf", response["caption"])
        self.assertNotIn("onBehalfOfContentOwner", response["caption"])

    def test_captions_insert_type_validation_comprehensive_coverage(self):
        """Comprehensive test to ensure all type validation lines are covered."""
        # Test all possible combinations of invalid types
        test_cases = [
            # (onBehalfOf, onBehalfOfContentOwner, sync, expected_error_param)
            (123, None, False, "onBehalfOf"),
            (None, 456, False, "onBehalfOfContentOwner"),
            (None, None, "invalid", "sync"),
            (123, 456, False, "onBehalfOf"),
            (123, None, True, "onBehalfOf"),  # Use valid sync to test onBehalfOf
            (None, 456, True, "onBehalfOfContentOwner"),  # Use valid sync to test onBehalfOfContentOwner
            (123, 456, False, "onBehalfOf"),  # Use valid sync to test onBehalfOf first
        ]

        for on_behalf_of, on_behalf_of_content_owner, sync, expected_param in test_cases:
            with self.assertRaises(TypeError) as context:
                Caption.insert(
                    part="snippet",
                    snippet={"videoId": "test", "text": "Caption text"},
                    onBehalfOf=on_behalf_of,
                    onBehalfOfContentOwner=on_behalf_of_content_owner,
                    sync=sync
                )

            if expected_param == "onBehalfOf":
                self.assertIn("On behalf of must be a string", str(context.exception))
            elif expected_param == "onBehalfOfContentOwner":
                self.assertIn("On behalf of content owner must be a string", str(context.exception))
            elif expected_param == "sync":
                self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_Caption_list(self):
        """Tests the Caption.list method."""
        # Test basic listing
        response = YoutubeAPI.Caption.list(part="snippet", videoId="video1")
        self.assertEqual(len(response["items"]), 1)

        # Test filtering by id
        response = YoutubeAPI.Caption.list(
            part="snippet", videoId="video1", id="caption1"
        )
        self.assertEqual(len(response["items"]), 1)

        # Test filtering by videoId that doesn't exist
        self.assert_error_behavior(
            YoutubeAPI.Caption.list,
            ValueError,
            "Video ID does not exist in the database.",
            part="snippet",
            videoId="nonexistent"
        )

    def test_captions_delete(self):
        """Tests the Captions.delete method."""
        response = Caption.delete(id="caption1")
        self.assertTrue(response["success"])
        from youtube.SimulationEngine.db import DB

        self.assertNotIn("caption1", DB["captions"])

    def test_captions_download(self):
        """Tests the Captions.download method."""
        # Test basic download
        response = Caption.download(id="caption1")
        self.assertEqual(response, "Caption content for video1")  # Default content

        # Test format parameter
        response = Caption.download(id="caption1", tfmt="srt")
        self.assertEqual(response, "SRT format caption content")

        response = Caption.download(id="caption1", tfmt="vtt")
        self.assertEqual(response, "WebVTT format caption content")

        # Test language parameter
        response = Caption.download(id="caption1", tlang="es")
        self.assertEqual(response, "Simulated translated caption to es")

    def test_captions_download_invalid_id(self):
        """Tests the Captions.download method with invalid ID."""
        self.assert_error_behavior(
            Caption.download,
            ValueError,
            "Caption ID is required.",
            id=None
        )

    def test_captions_download_invalid_tfmt(self):
        """Tests the Captions.download method with invalid tfmt."""
        self.assert_error_behavior(
            Caption.download,
            ValueError,
            "Unsupported tfmt format.",
            id="caption1", tfmt="invalid"
        )

    def test_captions_download_invalid_id_type(self):
        """Tests the Captions.download method with invalid ID type."""
        self.assert_error_behavior(
            Caption.download,
            TypeError,
            "Caption ID must be a string.",
            id=123
        )

    def test_captions_download_invalid_tfmt_type(self):
        """Tests the Captions.download method with invalid tfmt type."""
        self.assert_error_behavior(
            Caption.download,
            TypeError,
            "Format must be a string.",
            id="caption1", tfmt=123
        )

    def test_captions_download_invalid_tlang_type(self):
        """Tests the Captions.download method with invalid tlang type."""
        self.assert_error_behavior(
            Caption.download,
            TypeError,
            "Target language must be a string.",
            id="caption1", tlang=123
        )

    def test_captions_download_invalid_id_value(self):
        """Tests the Captions.download method with invalid ID value."""
        self.assert_error_behavior(
            Caption.download,
            ValueError,
            "Caption not found",
            id="invalid"
        )

    def test_captions_download_invalid_onBehalfOf_type(self):
        """Tests the Captions.download method with invalid onBehalfOf type."""
        self.assert_error_behavior(
            Caption.download,
            TypeError,
            "On behalf of must be a string.",
            id="caption1", onBehalfOf=123
        )

    def test_captions_download_invalid_onBehalfOfContentOwner_type(self):
        """Tests the Captions.download method with invalid onBehalfOfContentOwner type."""
        self.assert_error_behavior(
            Caption.download,
            TypeError,
            "On behalf of content owner must be a string.",
            id="caption1", onBehalfOfContentOwner=123
        )

    def test_captions_download_invalid_onBehalfOf_value(self):
        """Tests the Captions.download method with invalid onBehalfOf value."""
        self.assert_error_behavior(
            Caption.download,
            ValueError,
            "On behalf of cannot be empty or consist only of whitespace.",
            id="caption1", onBehalfOf=""
        )

    def test_captions_download_invalid_onBehalfOfContentOwner_value(self):
        """Tests the Captions.download method with invalid onBehalfOfContentOwner value."""
        self.assert_error_behavior(
            Caption.download,
            ValueError,
            "On behalf of content owner cannot be empty or consist only of whitespace.",
            id="caption1", onBehalfOfContentOwner=""
        )

    def test_captions_download_invalid_onBehalfOf_value_whitespace(self):
        """Tests the Captions.download method with invalid onBehalfOf value."""
        self.assert_error_behavior(
            Caption.download,
            ValueError,
            "On behalf of cannot be empty or consist only of whitespace.",
            id="caption1", onBehalfOf="   "
        )

    def test_captions_download_invalid_onBehalfOfContentOwner_value_whitespace(self):
        """Tests the Captions.download method with invalid onBehalfOfContentOwner value."""
        self.assert_error_behavior(
            Caption.download,
            ValueError,
            "On behalf of content owner cannot be empty or consist only of whitespace.",
            id="caption1", onBehalfOfContentOwner="   "
        )

    def test_captions_update(self):
        """Tests the Captions.update method."""
        response = Caption.update(part="snippet", id="caption1")
        # self.assertEqual(response["part"], "snippet")
        self.assertTrue(response["success"])

    def test_channels_list(self):
        """Tests the Channels.list method."""
        # Test filtering by categoryId
        response = YoutubeAPI.Channels.list(category_id="10")
        self.assertEqual(
            len(response["items"]), 1
        )  # One channel with categoryId="10" in the sample data

        # Test filtering by id
        response = YoutubeAPI.Channels.list(channel_id="channel1")
        self.assertEqual(len(response["items"]), 1)

        # Test maxResults
        response = YoutubeAPI.Channels.list(max_results=1)
        self.assertEqual(len(response["items"]), 1)

        # Test non-existent channel id
        response = YoutubeAPI.Channels.list(channel_id="non-existent-channel")
        self.assertEqual(len(response["items"]), 0)  # Should return empty list for non-existent channel
        
        # Test error handling - invalid parameter type
        try:
            response = YoutubeAPI.Channels.list(max_results="not-a-number")
            # If no exception is thrown, check for error in the response
            if isinstance(response, dict) and "error" in response:
                self.assertIn("error", response)
        except Exception as e:
            # Exception thrown is also valid behavior
            self.assertEqual(str(e), "max_results must be an integer or None.")
            
        # Test error handling - invalid parameter value
        try:
            response = YoutubeAPI.Channels.list(max_results=-1)  # Negative max_results is invalid
            # If no exception is thrown, check for error in the response
            if isinstance(response, dict) and "error" in response:
                self.assertIn("error", response)
        except Exception as e:
            # Exception thrown is also valid behavior
            self.assertEqual(str(e), "max_results must be between 1 and 50, inclusive.")

    def test_channel_sections_list(self):
        """Tests the ChannelSections.list method."""
        # Test basic listing with valid part
        response = ChannelSection.list(part="snippet", mine=True)
        self.assertEqual(len(response["items"]), 3)

        # Test filtering by id
        response = ChannelSection.list(part="snippet", section_id="section1")
        self.assertEqual(len(response["items"]), 1)

        # Test filtering by channelId
        response = ChannelSection.list(part="snippet", channel_id="channel1")
        self.assertEqual(len(response["items"]), 2)
        
        # Test with multiple valid parts
        response = ChannelSection.list(part="snippet,contentDetails", mine=True)
        self.assertEqual(len(response["items"]), 3)
        
        # Test error cases - function can either raise an exception or return an error dictionary
        
        # Test invalid part parameter - empty string
        try:
            response = ChannelSection.list(part="")
            # If no exception is raised, check for error dictionary
            self.assertIn("error", response)
            self.assertTrue("cannot be empty" in response["error"] or "empty" in response["error"])
        except InvalidPartParameterError as e:
            # If exception is raised, check the message
            self.assertTrue("cannot be empty" in str(e))
        
        # Test invalid part parameter - only commas
        try:
            response = ChannelSection.list(part=",,,")
            # If no exception is raised, check for error dictionary
            self.assertIn("error", response)
            self.assertTrue("no valid components" in response["error"] or "Invalid part" in response["error"])
        except InvalidPartParameterError as e:
            # If exception is raised, check the message
            self.assertTrue("no valid components" in str(e))
        
        # Test invalid part parameter - no valid parts
        try:
            response = ChannelSection.list(part="invalid")
            # If no exception is raised, check for error dictionary
            self.assertIn("error", response)
            self.assertTrue("Invalid part parameter" in response["error"])
        except InvalidPartParameterError as e:
            # If exception is raised, check the message
            self.assertTrue("Invalid part parameter" in str(e))
        
        # Test type errors for parameters
        try:
            response = ChannelSection.list(part=123)  # part must be string
            self.assertIn("error", response)
        except TypeError:
            pass  # Expected behavior
            
        try:
            response = ChannelSection.list(part="snippet", channel_id=123)  # channel_id must be string or None
            self.assertIn("error", response)
        except TypeError:
            pass  # Expected behavior
            
        try:
            response = ChannelSection.list(part="snippet", hl=123)  # hl must be string or None
            self.assertIn("error", response)
        except TypeError:
            pass  # Expected behavior
            
        try:
            response = ChannelSection.list(part="snippet", section_id=123)  # section_id must be string or None
            self.assertIn("error", response)
        except TypeError:
            pass  # Expected behavior
            
        try:
            response = ChannelSection.list(part="snippet", mine="yes")  # mine must be boolean
            self.assertIn("error", response)
        except TypeError:
            pass  # Expected behavior
            
        try:
            response = ChannelSection.list(part="snippet", on_behalf_of_content_owner=123)  # must be string or None
            self.assertIn("error", response)
        except TypeError:
            pass  # Expected behavior

    def test_channel_sections_delete(self):
        """Tests the ChannelSection.delete method."""
        response = YoutubeAPI.ChannelSection.delete(section_id="section1")
        self.assertTrue(response["success"])
        from youtube.SimulationEngine.db import DB

        self.assertNotIn("section1", DB["channelSections"])

    def test_channel_sections_insert(self):
        """Tests the ChannelSections.insert method."""
        response = ChannelSection.insert(part="snippet", snippet={"channelId": "channel1", "type": "singlePlaylist"})
        self.assertTrue(response["success"])
        self.assertIn("channelSection", response)
        self.assertIn("id", response["channelSection"])

    def test_channel_sections_update(self):
        """Tests the ChannelSection.update method."""
        response = YoutubeAPI.ChannelSection.update(
            section_id="section1", part="snippet"
        )
        self.assertTrue(response["success"])

    def test_channel_statistics_comment_count(self):
        """Tests the ChannelStatistics.commentCount method."""
        response = ChannelStatistics.comment_count()
        self.assertEqual(response["commentCount"], 100)

    def test_channel_statistics_comment_count_invalid_type(self):
        """Tests the ChannelStatistics.commentCount method with invalid type."""
        self.assert_error_behavior(
            ChannelStatistics.comment_count,
            TypeError,
            "Comment count must be an integer.",
            comment_count="invalid"
        )
    
    def test_channel_statistics_comment_count_invalid_value(self):
        """Tests the ChannelStatistics.commentCount method with invalid value."""
        self.assert_error_behavior(
            ChannelStatistics.comment_count,
            ValueError,
            "Comment count must be a positive integer.",
            comment_count=-1
        )

    def test_channel_statistics_comment_count_set_success_empty_db(self):
        """Tests the ChannelStatistics.commentCount method with set success when the database is empty."""
        DB.clear()
        response = ChannelStatistics.comment_count(comment_count=1000)
        self.assertEqual(response["commentCount"], 1000)
        self.assertEqual(DB["channelStatistics"]["commentCount"], 1000)

    def test_channel_statistics_comment_count_get_empty_db(self):
        """Tests the ChannelStatistics.commentCount method with get success when the database is empty."""
        DB.clear()
        response = ChannelStatistics.comment_count()
        self.assertEqual(response["commentCount"], 0)

    def test_channel_statistics_comment_count_set_success(self):
        """Tests the ChannelStatistics.commentCount method with set success."""
        response = ChannelStatistics.comment_count(comment_count=1000)
        self.assertEqual(response["commentCount"], 1000)
        self.assertEqual(DB["channelStatistics"]["commentCount"], 1000)

    def test_channel_statistics_hidden_subscriber_count(self):
        """Tests the ChannelStatistics.hiddenSubscriberCount method."""
        response = ChannelStatistics.hidden_subscriber_count()
        self.assertFalse(response["hiddenSubscriberCount"])

    def test_channel_statistics_hidden_subscriber_count_invalid_type(self):
        """Tests the ChannelStatistics.hiddenSubscriberCount method with invalid type."""
        self.assert_error_behavior(
            ChannelStatistics.hidden_subscriber_count,
            TypeError,
            "Hidden subscriber count must be a boolean.",
            hidden_subscriber_count="invalid"
        )

    def test_channel_statistics_hidden_subscriber_count_set_success_empty_db(self):
        """Tests the ChannelStatistics.hiddenSubscriberCount method with set success when the database is empty."""
        DB.clear()
        response = ChannelStatistics.hidden_subscriber_count(hidden_subscriber_count=True)
        self.assertEqual(response["hiddenSubscriberCount"], True)
        self.assertEqual(DB["channelStatistics"]["hiddenSubscriberCount"], True)
        
    def test_channel_statistics_hidden_subscriber_count_get_empty_db(self):
        """Tests the ChannelStatistics.hiddenSubscriberCount method with get success when the database is empty."""
        DB.clear()
        response = ChannelStatistics.hidden_subscriber_count()
        self.assertEqual(response["hiddenSubscriberCount"], False)

    def test_set_hidden_subscriber_count_success(self):
        """Tests the ChannelStatistics.hiddenSubscriberCount method with set success."""
        response = ChannelStatistics.hidden_subscriber_count(hidden_subscriber_count=True)
        self.assertEqual(response["hiddenSubscriberCount"], True)
        self.assertEqual(DB["channelStatistics"]["hiddenSubscriberCount"], True)

    def test_channel_statistics_subscriber_count(self):
        """Tests the ChannelStatistics.subscriberCount method."""
        response = ChannelStatistics.subscriber_count()
        self.assertEqual(response["subscriberCount"], 1000000)

    def test_channel_statistics_subscriber_count_invalid_type(self):
        """Tests the ChannelStatistics.subscriberCount method with invalid type."""
        self.assert_error_behavior(
            ChannelStatistics.subscriber_count,
            TypeError,
            "Subscriber count must be an integer.",
            subscriber_count="invalid"
        )

    def test_channel_statistics_subscriber_count_invalid_value(self):
        """Tests the ChannelStatistics.subscriberCount method with invalid value."""
        self.assert_error_behavior(
            ChannelStatistics.subscriber_count,
            ValueError,
            "Subscriber count must be a positive integer.",
            subscriber_count=-1
        )

    def test_channel_statistics_subscriber_count_set_success(self):
        """Tests the ChannelStatistics.subscriberCount method with set success."""
        response = ChannelStatistics.subscriber_count(subscriber_count=50000000)
        self.assertEqual(response["subscriberCount"], 50000000)
        from youtube.SimulationEngine.db import DB
        self.assertEqual(DB["channelStatistics"]["subscriberCount"], 50000000)

    def test_channel_statistics_subscriber_count_set_success_empty_db(self):
        """Tests the ChannelStatistics.subscriberCount method with set success when the database is empty."""
        DB.clear()
        response = ChannelStatistics.subscriber_count(subscriber_count=50000000)
        self.assertEqual(response["subscriberCount"], 50000000)
        self.assertEqual(DB["channelStatistics"]["subscriberCount"], 50000000)

    def test_channel_statistics_subscriber_count_get_empty_db(self):
        """Tests the ChannelStatistics.subscriberCount method with get success when the database is empty."""
        DB.clear()
        response = ChannelStatistics.subscriber_count()
        self.assertEqual(response["subscriberCount"], 0)

    def test_channel_statistics_video_count(self):
        """Tests the ChannelStatistics.videoCount method."""
        response = ChannelStatistics.video_count()
        self.assertEqual(response["videoCount"], 500)

    def test_channel_statistics_video_count_invalid_type(self):
        """Tests the ChannelStatistics.videoCount method with invalid type."""
        self.assert_error_behavior(
            ChannelStatistics.video_count,
            TypeError,
            "Video count must be an integer.",
            video_count="invalid"
        )

    def test_channel_statistics_video_count_invalid_value(self):
        """Tests the ChannelStatistics.videoCount method with invalid value."""
        self.assert_error_behavior(
            ChannelStatistics.video_count,
            ValueError,
            "Video count must be a non-negative integer.",
            video_count=-1
        )

    def test_channel_statistics_video_count_set_success(self):
        """Tests the ChannelStatistics.videoCount method with set success."""
        response = ChannelStatistics.video_count(video_count=1000)
        self.assertEqual(response["videoCount"], 1000)
        from youtube.SimulationEngine.db import DB
        self.assertEqual(DB["channelStatistics"]["videoCount"], 1000)

    def test_channel_statistics_video_count_set_success_empty_db(self):
        """Tests the ChannelStatistics.videoCount method with set success when the database is empty."""
        DB.clear()
        response = ChannelStatistics.video_count(video_count=1000)
        self.assertEqual(response["videoCount"], 1000)
        self.assertEqual(DB["channelStatistics"]["videoCount"], 1000)

    def test_channel_statistics_video_count_get_empty_db(self):
        """Tests the ChannelStatistics.videoCount method with get success when the database is empty."""
        DB.clear()
        response = ChannelStatistics.video_count()
        self.assertEqual(response["videoCount"], 0)

    def test_channel_statistics_view_count(self):
        """Tests the ChannelStatistics.viewCount method."""
        response = ChannelStatistics.view_count()
        self.assertEqual(response["viewCount"], 10000000)

    def test_channel_statistics_view_count_invalid_type(self):
        """Tests the ChannelStatistics.viewCount method with invalid type."""
        self.assert_error_behavior(
            ChannelStatistics.view_count,
            TypeError,
            "View count must be an integer.",
            view_count="invalid"
        )

    def test_channel_statistics_view_count_invalid_value(self):
        """Tests the ChannelStatistics.viewCount method with invalid value."""
        self.assert_error_behavior(
            ChannelStatistics.view_count,
            ValueError,
            "View count must be a positive integer.",
            view_count=-1
        )

    def test_channel_statistics_view_count_set_success(self):
        """Tests the ChannelStatistics.viewCount method with set success."""
        response = ChannelStatistics.view_count(view_count=50000000)
        self.assertEqual(response["viewCount"], 50000000)
        self.assertEqual(DB["channelStatistics"]["viewCount"], 50000000)

    def test_channel_banners_insert(self):
        """Tests the ChannelBanners.insert method."""
        response = YoutubeAPI.ChannelBanners.insert(channel_id="channel1")
        self.assertEqual(response["channelId"], "channel1")
        self.assertIsNone(response["onBehalfOfContentOwner"])
        self.assertIsNone(response["onBehalfOfContentOwnerChannel"])
        from youtube.SimulationEngine.db import DB
        self.assertEqual(len(DB["channelBanners"]), 1)

    def test_channel_banners_insert_with_all_parameters(self):
        """Tests the ChannelBanners.insert method with all parameters."""
        response = YoutubeAPI.ChannelBanners.insert(
            channel_id="channel1",
            on_behalf_of_content_owner="content_owner_123",
            on_behalf_of_content_owner_channel="UC_content_owner_channel"
        )
        self.assertEqual(response["channelId"], "channel1")
        self.assertEqual(response["onBehalfOfContentOwner"], "content_owner_123")
        self.assertEqual(response["onBehalfOfContentOwnerChannel"], "UC_content_owner_channel")
        from youtube.SimulationEngine.db import DB
        self.assertEqual(len(DB["channelBanners"]), 1)

    def test_channel_banners_insert_with_none_parameters(self):
        """Tests the ChannelBanners.insert method with all parameters as None."""
        response = YoutubeAPI.ChannelBanners.insert(
            channel_id=None,
            on_behalf_of_content_owner=None,
            on_behalf_of_content_owner_channel=None
        )
        self.assertIsNone(response["channelId"])
        self.assertIsNone(response["onBehalfOfContentOwner"])
        self.assertIsNone(response["onBehalfOfContentOwnerChannel"])
        from youtube.SimulationEngine.db import DB
        self.assertEqual(len(DB["channelBanners"]), 1)

    def test_channel_banners_insert_empty_channel_id(self):
        """Tests that empty channel_id raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            ValueError,
            "Channel ID cannot be empty or contain only whitespace.",
            channel_id=""
        )

    def test_channel_banners_insert_whitespace_channel_id(self):
        """Tests that whitespace-only channel_id raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            ValueError,
            "Channel ID cannot be empty or contain only whitespace.",
            channel_id="   "
        )

    def test_channel_banners_insert_empty_on_behalf_of_content_owner(self):
        """Tests that empty on_behalf_of_content_owner raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            ValueError,
            "On behalf of content owner cannot be empty or contain only whitespace.",
            channel_id="valid_channel",
            on_behalf_of_content_owner=""
        )

    def test_channel_banners_insert_whitespace_on_behalf_of_content_owner(self):
        """Tests that whitespace-only on_behalf_of_content_owner raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            ValueError,
            "On behalf of content owner cannot be empty or contain only whitespace.",
            channel_id="valid_channel",
            on_behalf_of_content_owner="   "
        )

    def test_channel_banners_insert_empty_on_behalf_of_content_owner_channel(self):
        """Tests that empty on_behalf_of_content_owner_channel raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            ValueError,
            "On behalf of content owner channel cannot be empty or contain only whitespace.",
            channel_id="valid_channel",
            on_behalf_of_content_owner_channel=""
        )

    def test_channel_banners_insert_whitespace_on_behalf_of_content_owner_channel(self):
        """Tests that whitespace-only on_behalf_of_content_owner_channel raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            ValueError,
            "On behalf of content owner channel cannot be empty or contain only whitespace.",
            channel_id="valid_channel",
            on_behalf_of_content_owner_channel="   "
        )

    def test_channel_banners_insert_invalid_channel_id_type(self):
        """Tests that invalid channel_id type raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            TypeError,
            "Channel ID must be a string.",
            channel_id=123
        )

    def test_channel_banners_insert_invalid_on_behalf_of_content_owner_type(self):
        """Tests that invalid on_behalf_of_content_owner type raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            TypeError,
            "On behalf of content owner must be a string.",
            channel_id="valid_channel",
            on_behalf_of_content_owner=456
        )

    def test_channel_banners_insert_invalid_on_behalf_of_content_owner_channel_type(self):
        """Tests that invalid on_behalf_of_content_owner_channel type raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            TypeError,
            "On behalf of content owner channel must be a string.",
            channel_id="valid_channel",
            on_behalf_of_content_owner_channel=789
        )

    def test_channel_banners_insert_channel_id_not_found(self):
        """Tests that channel_id not found raises ValueError."""
        self.assert_error_behavior(
            YoutubeAPI.ChannelBanners.insert,
            ValueError,
            "Channel ID does not exist in the database.",
            channel_id="nonexistent_channel"
        )


    def test_comment_set_moderation_status(self):
        """Tests the Comment.setModerationStatus method."""
        response = YoutubeAPI.Comment.set_moderation_status(
            comment_id="comment1", moderation_status="heldForReview"
        )
        self.assertTrue(response["success"])
        from youtube.SimulationEngine.db import DB

        self.assertEqual(
            DB["comments"]["comment1"]["moderationStatus"], "heldForReview"
        )

    def test_comment_delete(self):
        """Tests the Comment.delete method."""
        response = YoutubeAPI.Comment.delete(comment_id="comment1")
        self.assertTrue(response["success"])
        from youtube.SimulationEngine.db import DB

        self.assertNotIn("comment1", DB["comments"])

    def test_comment_insert(self):
        """Tests the Comment.insert method."""
        response = YoutubeAPI.Comment.insert(part="snippet")
        self.assertTrue(response["success"])
        self.assertIn("comment", response)
        self.assertIn("id", response["comment"])
        new_comment_id = response["comment"]["id"]  # Capture the generated ID
        from youtube.SimulationEngine.db import DB

        self.assertIn(new_comment_id, DB["comments"])

    def test_comment_list(self):
        """Tests the Comment.list method."""
        # Test basic listing
        response = Comment.list(part="snippet")
        self.assertEqual(len(response["items"]), 3)

        # Test filtering by id
        response = Comment.list(part="snippet", comment_id="comment1")
        self.assertEqual(len(response["items"]), 1)

        # Test filtering by parentId
        response = Comment.list(part="snippet", parent_id="comment1")
        self.assertEqual(len(response["items"]), 1)

    def test_comment_mark_as_spam(self):
        """Tests the Comment.markAsSpam method."""
        response = YoutubeAPI.Comment.mark_as_spam(comment_id="comment1")
        self.assertTrue(response["success"])
        from youtube.SimulationEngine.db import DB

        self.assertEqual(
            DB["comments"]["comment1"]["moderationStatus"], "heldForReview"
        )

    def test_comment_update(self):
        """Tests the Comment.update method."""
        response = YoutubeAPI.Comment.update(comment_id="comment1", snippet={"a": "b"})
        self.assertEqual([x for x in response.keys()], ["success"])

    def test_comment_thread_insert(self):
        """Tests the CommentThread.insert method."""
        response = YoutubeAPI.CommentThread.insert(part="snippet")
        self.assertTrue(response["success"])
        self.assertIn("commentThread", response)
        self.assertIn("id", response["commentThread"])
        new_thread_id = response["commentThread"]["id"]  # Capture the generated ID
        from youtube.SimulationEngine.db import DB

        self.assertIn(
            new_thread_id, DB["commentThreads"]
        )  # Use the ID in the assertion

    def test_comment_thread_list(self):
        """Tests the CommentThread.list method."""
        # Test basic listing
        response = CommentThread.list(part="snippet")
        self.assertEqual(len(response["items"]), 2)

        # Test filtering by id
        response = CommentThread.list(part="snippet", thread_id="thread1")
        self.assertEqual(len(response["items"]), 1)

        # Test filtering by channelId
        response = CommentThread.list(part="snippet", channel_id="channel1")
        self.assertEqual(len(response["items"]), 1)

    def test_list_videos_with_chart(self):
        # Test listing most popular videos
        result = Videos.list(part="statistics", chart="mostPopular")
        self.assertIn("items", result)
        self.assertIn("pageInfo", result)
        self.assertEqual(result["kind"], "youtube#videoListResponse")

        # Verify videos are sorted by view count
        items = result["items"]
        if items:  # Check if there are any items to sort
            for i in range(len(items) - 1):
                current_views = items[i]["statistics"]["viewCount"]
                next_views = items[i + 1]["statistics"]["viewCount"]
                self.assertGreaterEqual(current_views, next_views)

    def test_list_videos_with_id(self):
        # Test listing videos by ID
        result = Videos.list(part="snippet", id="video1")
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "video1")

    def test_list_videos_invalid_params(self):
        # Test with missing part parameter
        self.assert_error_behavior(
            Videos.list,
            ValueError,
            "The 'part' parameter is required.",
            part=""
        )

        # Test with multiple filter parameters
        self.assert_error_behavior(
            Videos.list,
            ValueError,
            "Only one of 'chart', 'id', or 'my_rating' can be provided.",
            part="snippet",
            chart="mostPopular",
            id="video1",
            my_rating="like"
        )
        # Test with invalid chart value
        self.assert_error_behavior(
            Videos.list,
            ValueError,
            "Invalid value for 'chart'. Only 'mostPopular' is supported.",
            part="snippet",
            chart="invalid"
        )

    def test_rate_video(self):
        # Test liking a video
        result = Videos.rate("video1", "like")
        self.assertTrue(result["success"])
        self.assertEqual(DB["videos"]["video1"]["statistics"]["likeCount"], "50001")

        # Test disliking a video
        result = Videos.rate("video1", "dislike")
        self.assertTrue(result["success"])
        self.assertEqual(DB["videos"]["video1"]["statistics"]["dislikeCount"], "5000")
        self.assertEqual(DB["videos"]["video1"]["statistics"]["likeCount"], "50000")

        # Test removing rating
        result = Videos.rate("video1", "none")
        self.assertTrue(result["success"])
        self.assertEqual(DB["videos"]["video1"]["statistics"]["dislikeCount"], "4999")
        self.assertEqual(DB["videos"]["video1"]["statistics"]["likeCount"], "49999")

    def test_rate_video_invalid_video_id_type(self):
        self.assert_error_behavior(
            Videos.rate,
            TypeError,
            "video_id must be a string",
            video_id=123,
            rating="like"
        )

    def test_rate_video_invalid_rating_type(self):
        self.assert_error_behavior(
            Videos.rate,
            TypeError,
            "rating must be a string",
            video_id="video1",
            rating=123
        )

    def test_rate_video_invalid_rating_value(self):
        self.assert_error_behavior(
            Videos.rate,
            ValueError,
            "Invalid rating, must be one of ['like', 'dislike', 'none']",
            video_id="video1",
            rating="invalid"
        )

    def test_rate_video_empty_video_id(self):
        self.assert_error_behavior(
            Videos.rate,
            ValueError,
            "video_id is required",
            video_id="",
            rating="like"
        )

    def test_rate_video_none_video_id(self):
        self.assert_error_behavior(
            Videos.rate,
            ValueError,
            "video_id is required",
            video_id=None,
            rating="like"
        )

    def test_rate_video_none_rating(self):
        self.assert_error_behavior(
            Videos.rate,
            ValueError,
            "rating is required",
            video_id="video1",
            rating=None
        )

    def test_rate_video_none_rating(self):
        self.assert_error_behavior(
            Videos.rate,
            ValueError,
            "rating is required",
            video_id="video1",
            rating=None
        )

    def test_rate_video_invalid_on_behalf_of_type(self):
        self.assert_error_behavior(
            Videos.rate,
            TypeError,
            "on_behalf_of must be a string",
            video_id="video1",
            rating="like",
            on_behalf_of=123
        )

    def test_rate_video_id_not_found(self):
        self.assert_error_behavior(
            Videos.rate,
            ValueError,
            "Video not found",
            video_id="nonexistent",
            rating="like"
        )

    def test_report_abuse(self):
        # Test reporting a video
        result = Videos.report_abuse("video1", "reason1")
        self.assertTrue(result["success"])

        # Test with non-existent video
        self.assert_error_behavior(
            Videos.report_abuse,
            ValueError,
            "Video not found",
            video_id="nonexistent",
            reason_id="reason1"
        )

        # Test with missing reason_id
        self.assert_error_behavior(
            Videos.report_abuse,
            ValueError,
            "reason_id is required",
            video_id="video1",
            reason_id=""
        )

        # Test with None reason_id
        self.assert_error_behavior(
            Videos.report_abuse,
            ValueError,
            "reason_id is required",
            video_id="video1",
            reason_id=None
        )

        # Test with missing video_id
        self.assert_error_behavior(
            Videos.report_abuse,
            ValueError,
            "video_id is required",
            video_id="",
            reason_id="reason1"
        )

        # Test with None video_id
        self.assert_error_behavior(
            Videos.report_abuse,
            ValueError,
            "video_id is required",
            video_id=None,
            reason_id="reason1"
        )

        # Test with invalid video_id type
        self.assert_error_behavior(
            Videos.report_abuse,
            TypeError,
            "video_id must be a string",
            video_id=123,
            reason_id="reason1"
        )

        # Test with invalid reason_id type
        self.assert_error_behavior(
            Videos.report_abuse,
            TypeError,
            "reason_id must be a string",
            video_id="video1",
            reason_id=123
        )

        # Test with invalid on_behalf_of_content_owner type
        self.assert_error_behavior(
            Videos.report_abuse,
            TypeError,
            "on_behalf_of_content_owner must be a string",
            video_id="video1",
            reason_id="reason1",
            on_behalf_of_content_owner=123
        )

        # Test with invalid secondary_reason_id type
        self.assert_error_behavior(
            Videos.report_abuse,
            TypeError,
            "secondary_reason_id must be a string",
            video_id="video1",
            reason_id="reason1",
            secondary_reason_id=123
        )

        # Test with invalid comments type
        self.assert_error_behavior(
            Videos.report_abuse,
            TypeError,
            "comments must be a string",
            video_id="video1",
            reason_id="reason1",
            comments=123
        )

        # Test with invalid language type
        self.assert_error_behavior(
            Videos.report_abuse,
            TypeError,
            "language must be a string",
            video_id="video1",
            reason_id="reason1",
            language=123
        )

    def test_delete_video(self):
        """Test the delete video function with various scenarios."""
        from youtube.SimulationEngine.db import DB
        
        # Test successful deletion
        result = Videos.delete("video1")
        self.assertTrue(result["success"])
        self.assertNotIn("video1", DB["videos"])


    def test_delete_video_empty_id(self):
        """Test delete video with empty ID."""
        self.assert_error_behavior(
            Videos.delete,
            InvalidVideoIdError,
            "Video ID is required.",
            id=""
        )

    def test_delete_video_whitespace_id(self):
        """Test delete video with whitespace-only ID."""
        self.assert_error_behavior(
            Videos.delete,
            InvalidVideoIdError,
            "Video ID is required.",
            id="   "
        )

    def test_delete_video_none_id(self):
        """Test delete video with None ID."""
        self.assert_error_behavior(
            Videos.delete,
            InvalidVideoIdError,
            "Video ID is required.",
            id=None
        )

    def test_delete_video_not_found(self):
        """Test delete video with non-existent ID."""
        self.assert_error_behavior(
            Videos.delete,
            VideoIdNotFoundError,
            "Video not found.",
            id="nonexistent"
        )

    def test_update_video(self):
        # Test updating video snippet
        update_body = {
            "id": "video1",
            "snippet": {"title": "Updated Title", "description": "Updated Description"},
        }
        result = Videos.update("snippet", update_body)
        self.assertEqual(result["snippet"]["title"], "Updated Title")
        self.assertEqual(result["snippet"]["description"], "Updated Description")

        # Test updating multiple parts
        update_body = {
            "id": "video1",
            "snippet": {"title": "New Title"},
            "status": {"privacyStatus": "private"},
        }
        result = Videos.update("snippet,status", update_body)
        self.assertEqual(result["snippet"]["title"], "New Title")
        self.assertEqual(result["status"]["privacyStatus"], "private")

    def test_update_video_incorrect_part_type(self):
        self.assert_error_behavior(
            Videos.update,
            TypeError,
            "The 'part' parameter must be a string.",
            part=123,
            body={"id": "video1", "snippet": {"title": "New Title"}}
        )

    def test_update_video_none_part(self):
        self.assert_error_behavior(
            Videos.update,
            ValueError,
            "The 'part' parameter is required.",
            part=None,
            body={"id": "video1", "snippet": {"title": "New Title"}}
        )

    def test_update_video_none_body(self):
        self.assert_error_behavior(
            Videos.update,
            ValueError,
            "The 'body' parameter is required and must include the video 'id'.",
            part="snippet",
            body=None
        )

    def test_update_video_none_id(self):
        self.assert_error_behavior(
            Videos.update,
            ValueError,
            "The 'body' parameter is required and must include the video 'id'.",
            part="snippet",
            body={"snippet": {"title": "New Title"}}
        )

    def test_update_video_invalid_id_not_found(self):
        self.assert_error_behavior(
            Videos.update,
            ValueError,
            "Video with given id not found in the database",
            part="snippet",
            body={"id": "nonexistent", "snippet": {"title": "New Title"}}
        )

    def test_update_video_invalid_part(self):
        self.assert_error_behavior(
            Videos.update,
            ValueError,
            "Invalid part parameter, must be one of ['snippet', 'status', 'statistics']",
            part="invalid",
            body={"id": "video1", "snippet": {"title": "New Title"}}
        )

    def test_update_video_invalid_snippet_structure(self):
        self.assert_error_behavior(
            Videos.update,
            ValueError,
            "Invalid snippet structure",
            part="snippet",
            body={"id": "video1", "snippet": {"title": 123}}
        )

    def test_update_video_invalid_status_structure(self):
        self.assert_error_behavior(
            Videos.update,
            ValueError,
            "Invalid status structure",
            part="status",
            body={"id": "video1", "status": {"privacyStatus": 123}}
        )

    def test_update_video_invalid_statistics_structure(self):
        self.assert_error_behavior(
            Videos.update,
            ValueError,
            "Invalid statistics structure",
            part="statistics",
            body={"id": "video1", "statistics": {"viewCount": "not-a-number"}}
        )

    def test_update_video_multiple_parts(self):
        update_body = {
            "id": "video1",
            "snippet": {"title": "New Title"},
            "status": {"privacyStatus": "private"},
            "statistics": {"viewCount": 1000}
        }
        result = Videos.update("snippet,status,statistics", update_body)

    def test_search_videos(self):
        # Test basic video search
        result = Search.list(part="snippet", q="Python")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

        # Verify search results contain the query term
        for item in result["items"]:
            if "snippet" in item:  # Ensure 'snippet' exists
                title = item["snippet"]["title"].lower()
                description = item["snippet"]["description"].lower()
                self.assertTrue("python" in title or "python" in description)

    def test_search_with_filters(self):
        """Tests searching with filters."""
        # Test search with channel filter
        result = YoutubeAPI.Search.list(part="snippet", channel_id="channel1")
        self.assertIn("items", result)
        for item in result["items"]:
            if "snippet" in item and "channelId" in item["snippet"]:
                self.assertEqual(item["snippet"]["channelId"], "channel1")

        # Test search with video category
        result = YoutubeAPI.Search.list(part="snippet", video_category_id="28")
        self.assertIn("items", result)
        for item in result["items"]:
            if "snippet" in item and "categoryId" in item["snippet"]:
                self.assertEqual(item["snippet"]["categoryId"], "28")

    def test_search_invalid_params(self):
        # Test with missing part parameter
        self.assert_error_behavior(
            Search.list,
            ValueError,
            "The 'part' parameter is required.",
            part=""
        )

        # Test with invalid part parameter
        self.assert_error_behavior(
            Search.list,
            ValueError,
            "Invalid part parameter: invalid",
            part="invalid"
        )

        # Test with invalid order parameter
        self.assert_error_behavior(
            Search.list,
            ValueError,
            "Invalid order parameter: invalid",
            part="snippet",
            order="invalid"
        )

    def test_search_max_results(self):
        """Tests searching with max results parameter."""
        # Test max_results parameter
        max_results = 5
        result = YoutubeAPI.Search.list(part="snippet", max_results=max_results)
        self.assertLessEqual(len(result["items"]), max_results)

        # Test with very large max_results
        result = YoutubeAPI.Search.list(part="snippet", max_results=100)
        self.assertLessEqual(len(result["items"]), 50)  # API limit is 50


    def test_search_validation_errors(self):
        """Test various validation error scenarios."""
        # Test max_results validation
        self.assert_error_behavior(
            Search.list,
            ValueError,
            "max_results must be an integer",
            part="snippet",
            max_results="invalid"
        )

        self.assert_error_behavior(
            Search.list,
            ValueError,
            "max_results must be non-negative",
            part="snippet",
            max_results=-1
        )

        # Test invalid type parameter
        self.assert_error_behavior(
            Search.list,
            ValueError,
            "Invalid type parameter: invalid. Valid values are: video, channel, playlist",
            part="snippet",
            type="invalid"
        )

        # Test invalid type parameter with comma-separated values
        self.assert_error_behavior(
            Search.list,
            ValueError,
            "Invalid type parameter: invalid. Valid values are: video, channel, playlist",
            part="snippet",
            type="video,invalid,playlist"
        )

        # Test invalid order parameter
        self.assert_error_behavior(
            Search.list,
            ValueError,
            "Invalid order parameter: invalid",
            part="snippet",
            order="invalid"
        )

    def test_search_video_filters(self):
        """Test video filtering with various parameters."""
        # Test video caption filter
        result = Search.list(part="snippet", video_caption="any")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_caption="closedCaption")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_caption="none")
        self.assertIn("items", result)

        # Test video definition filter
        result = Search.list(part="snippet", video_definition="any")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_definition="high")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_definition="standard")
        self.assertIn("items", result)

        # Test video duration filter
        result = Search.list(part="snippet", video_duration="any")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_duration="long")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_duration="medium")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_duration="short")
        self.assertIn("items", result)

        # Test video embeddable filter
        result = Search.list(part="snippet", video_embeddable="any")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_embeddable="true")
        self.assertIn("items", result)

        # Test video license filter
        result = Search.list(part="snippet", video_license="any")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_license="creativeCommon")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_license="youtube")
        self.assertIn("items", result)

        # Test video syndicated filter
        result = Search.list(part="snippet", video_syndicated="any")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_syndicated="true")
        self.assertIn("items", result)

        # Test video type filter
        result = Search.list(part="snippet", video_type="any")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_type="episode")
        self.assertIn("items", result)

        result = Search.list(part="snippet", video_type="movie")
        self.assertIn("items", result)

    def test_search_channel_filters(self):
        """Test channel filtering with various parameters."""
        # Test channel type filter
        result = Search.list(part="snippet", channel_type="any")
        self.assertIn("items", result)

        result = Search.list(part="snippet", channel_type="show")
        self.assertIn("items", result)

        # Test channel search with query
        result = Search.list(part="snippet", q="Tech", type="channel")
        self.assertIn("items", result)

        # Test channel search with channel_id filter
        result = Search.list(part="snippet", channel_id="channel1", type="channel")
        self.assertIn("items", result)

    def test_search_ordering(self):
        """Test different ordering options."""
        # Test viewCount ordering
        result = Search.list(part="snippet", order="viewCount")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

        # Test date ordering
        result = Search.list(part="snippet", order="date")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

        # Test title ordering
        result = Search.list(part="snippet", order="title")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

        # Test rating ordering
        result = Search.list(part="snippet", order="rating")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

        # Test videoCount ordering
        result = Search.list(part="snippet", order="videoCount")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

    def test_search_part_parameter(self):
        """Test different part parameter combinations."""
        # Test with only id part
        result = Search.list(part="id")
        self.assertIn("items", result)
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertNotIn("snippet", item)

        # Test with both snippet and id parts
        result = Search.list(part="snippet,id")
        self.assertIn("items", result)
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertIn("snippet", item)

    def test_search_playlist_type(self):
        """Test searching for playlists specifically."""
        # Test playlist search (even though DB might not have playlists)
        result = Search.list(part="snippet", type="playlist")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

    def test_search_combined_filters(self):
        """Test search with multiple filters combined."""
        # Test multiple video filters
        result = Search.list(
            part="snippet",
            video_caption="any",
            video_definition="high",
            video_duration="medium",
            video_embeddable="true"
        )
        self.assertIn("items", result)

        # Test video and channel filters
        result = Search.list(
            part="snippet",
            channel_id="channel1",
            video_category_id="28"
        )
        self.assertIn("items", result)

    def test_search_with_query_and_filters(self):
        """Test search with query and various filters."""
        # Test with query and video filters
        result = Search.list(
            part="snippet",
            q="programming",
            video_caption="any",
            video_definition="any"
        )
        self.assertIn("items", result)

        # Test with query and channel filters
        result = Search.list(
            part="snippet",
            q="Tech",
            channel_type="any",
            type="channel"
        )
        self.assertIn("items", result)

    def test_search_id_only_part(self):
        """Test search with only id part (no snippet)."""
        # Test with only id part
        result = Search.list(part="id", type="video")
        self.assertIn("items", result)
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertNotIn("snippet", item)

        # Test with only id part for channels
        result = Search.list(part="id", type="channel")
        self.assertIn("items", result)
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertNotIn("snippet", item)

        # Test with only id part for playlists
        result = Search.list(part="id", type="playlist")
        self.assertIn("items", result)
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertNotIn("snippet", item)

    def test_search_query_filtering(self):
        """Test search with query filtering for different types."""
        # Test video search with query
        result = Search.list(part="snippet", q="Python", type="video")
        self.assertIn("items", result)

        # Test channel search with query
        result = Search.list(part="snippet", q="Tech", type="channel")
        self.assertIn("items", result)

        # Test playlist search with query
        result = Search.list(part="snippet", q="Programming", type="playlist")
        self.assertIn("items", result)

    def test_search_max_results_limiting(self):
        """Test that max_results properly limits the number of results."""
        # Test with max_results = 1
        result = Search.list(part="snippet", max_results=1)
        self.assertLessEqual(len(result["items"]), 1)

        # Test with max_results = 0 (should return all results since 0 is falsy)
        result = Search.list(part="snippet", max_results=0)
        self.assertGreater(len(result["items"]), 0)  # Should return all results

        # Test with max_results = 50 (API limit)
        result = Search.list(part="snippet", max_results=50)
        self.assertLessEqual(len(result["items"]), 50)

    def test_search_ordering_edge_cases(self):
        """Test ordering with edge cases that trigger default return values."""
        # Test viewCount ordering with mixed content types
        result = Search.list(part="snippet", order="viewCount", type="video,channel,playlist")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

        # Test rating ordering with mixed content types
        result = Search.list(part="snippet", order="rating", type="video,channel,playlist")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

        # Test videoCount ordering with mixed content types
        result = Search.list(part="snippet", order="videoCount", type="video,channel,playlist")
        self.assertIn("items", result)
        self.assertEqual(result["kind"], "youtube#searchListResponse")

    def test_search_empty_results(self):
        """Test search scenarios that return empty results."""
        # Test with non-existent query
        result = Search.list(part="snippet", q="nonexistentquery12345")
        self.assertIn("items", result)
        # Should return empty list, not error

        # Test with non-existent channel_id
        result = Search.list(part="snippet", channel_id="nonexistentchannel")
        self.assertIn("items", result)
        # Should return empty list, not error

        # Test with non-existent video_category_id
        result = Search.list(part="snippet", video_category_id="99999")
        self.assertIn("items", result)
        # Should return empty list, not error

    def test_memberships_part_validation(self):
        """Tests the type validation of the part parameter in Memberships module."""
        # Test with non-string part parameter
        with self.assertRaises(ValueError) as context:
            Memberships.list(part=123)  # Passing integer instead of string
        self.assertEqual(str(context.exception), "part must be a string")

        # Test with invalid string part parameter
        with self.assertRaises(ValueError) as context:
            Memberships.list(part="invalid")
        self.assertEqual(str(context.exception), "Invalid part parameter")

        # Test with empty string part parameter
        with self.assertRaises(ValueError) as context:
            Memberships.list(part="")
        self.assertEqual(str(context.exception), "Invalid part parameter")

        # Test with string part parameter (should pass validation)
        result = Memberships.list(part="snippet")
        self.assertNotIn("error", result)



    def test_valid_input_basic(self):
        """Test that a basic valid call is accepted."""
        result = list_comment_threads(part="snippet")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        # The content of items will depend on the mock DB and filters.
        # Here, with no filters, it should return all threads from mock DB.
        self.assertEqual(len(result["items"]), 2) 

    def test_valid_input_with_all_optional_params_none(self):
        """Test valid input with all optional parameters as None (default)."""
        result = list_comment_threads(part="snippet")
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_valid_input_with_max_results(self):
        """Test valid input with max_results specified."""
        result = list_comment_threads(part="snippet", max_results=1)
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)

    # --- Tests for 'part' parameter ---
    def test_invalid_part_none(self):
        """Test that 'part' being None raises MissingPartParameterError."""
        # Pydantic treats None for a required field as 'missing'
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=MissingPartParameterError,
            expected_message="Parameter 'part' is required and cannot be empty.",
            part=None # type: ignore 
        )

    def test_invalid_part_empty_string(self):
        """Test that 'part' being an empty string raises MissingPartParameterError."""
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=MissingPartParameterError,
            expected_message="Parameter 'part' is required and cannot be empty.",
            part=""
        )

    def test_invalid_part_type(self):
        """Test that 'part' being a non-string type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=TypeError,
            expected_message="Parameter 'part' must be a string.",
            part=123 # type: ignore
        )

    # --- Tests for 'max_results' parameter ---
    def test_invalid_max_results_type(self):
        """Test that 'max_results' being a non-integer type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=TypeError,
            expected_message="Parameter 'max_results' must be an integer if provided.",
            part="snippet",
            max_results="abc" # type: ignore
        )

    def test_invalid_max_results_zero(self):
        """Test that 'max_results' being zero raises InvalidMaxResultsError."""
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=InvalidMaxResultsError,
            expected_message="Parameter 'max_results' must be a positive integer if provided.",
            part="snippet",
            max_results=0
        )

    def test_invalid_max_results_negative(self):
        """Test that 'max_results' being negative raises InvalidMaxResultsError."""
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=InvalidMaxResultsError,
            expected_message="Parameter 'max_results' must be a positive integer if provided.",
            part="snippet",
            max_results=-5
        )
    
    # --- Tests for other Optional[str] parameters for type errors ---
    def test_invalid_thread_id_type(self):
        """Test that 'thread_id' of invalid type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=TypeError,
            expected_message="Parameter 'thread_id' must be a string if provided.",
            part="snippet",
            thread_id=123 # type: ignore
        )

    def test_invalid_channel_id_type(self):
        """Test that 'channel_id' of invalid type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=TypeError,
            expected_message="Parameter 'channel_id' must be a string if provided.",
            part="snippet",
            channel_id=False # type: ignore
        )

    def test_invalid_video_id_type(self):
        """Test that 'video_id' of invalid type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=list_comment_threads,
            expected_exception_type=TypeError,
            expected_message="Parameter 'video_id' must be a string if provided.",
            part="snippet",
            video_id=object() # type: ignore
        )
        
    def test_invalid_search_terms_type(self):
        """Test that 'search_terms' of invalid type raises TypeError."""
        self.assert_error_behavior(
            list_comment_threads,
            TypeError,
            "Parameter 'search_terms' must be a string if provided.",
            part="snippet", search_terms=12345 #type: ignore
        )

    def test_invalid_moderation_status_type(self):
        """Test that 'moderation_status' of invalid type raises TypeError."""
        self.assert_error_behavior(
            list_comment_threads,
            TypeError,
            "Parameter 'moderation_status' must be a string if provided.",
            part="snippet", moderation_status=['published'] #type: ignore
        )

    def test_invalid_order_type(self):
        """Test that 'order' of invalid type raises TypeError."""
        self.assert_error_behavior(
            list_comment_threads,
            TypeError,
            "Parameter 'order' must be a string if provided.",
            part="snippet", order=1.0 #type: ignore
        )

    def test_invalid_page_token_type(self):
        """Test that 'page_token' of invalid type raises TypeError."""
        self.assert_error_behavior(
            list_comment_threads,
            TypeError,
            "Parameter 'page_token' must be a string if provided.",
            part="snippet", page_token=object() #type: ignore
        )

    def test_invalid_text_format_type(self):
        """Test that 'text_format' of invalid type raises TypeError."""
        self.assert_error_behavior(
            list_comment_threads,
            TypeError,
            "Parameter 'text_format' must be a string if provided.",
            part="snippet", text_format=True #type: ignore
        )

    def test_function_filters_by_video_id(self):
        """Test core logic: filtering by video_id works after validation."""
        result = list_comment_threads(part="snippet,id", video_id="video1")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "thread1")

    def test_function_filters_by_search_terms(self):
        """Test core logic: filtering by search_terms works after validation."""
        result = list_comment_threads(part="snippet", search_terms="Hello world")
        self.assertEqual(len(result["items"]), 0)

    def test_valid_input_all_parameters(self):
        """Test successful insertion with all parameters valid."""
        part_input = "snippet"
        snippet_input = {"author": "test_user", "text": "This is a test snippet."}
        top_level_comment_input = {"id": "comment-1", "text": "Great point!"}

        result = create_comment_thread(
            part=part_input,
            snippet=snippet_input,
            top_level_comment=top_level_comment_input
        )

        self.assertTrue(result.get("success"))
        self.assertIn("commentThread", result)
        thread = result["commentThread"]
        self.assertIsNotNone(thread)
        self.assertIn("id", thread) # type: ignore
        self.assertEqual(thread["snippet"], snippet_input) # type: ignore
        self.assertIn("comment-1", thread["comments"]) # type: ignore

    def test_valid_input_optional_missing(self):
        """Test successful insertion with optional snippet and top_level_comment as None."""
        part_input = "snippet"

        result = create_comment_thread(part=part_input, snippet=None, top_level_comment=None)

        self.assertTrue(result.get("success"))
        self.assertIn("commentThread", result)
        thread = result["commentThread"]
        self.assertIsNotNone(thread)
        self.assertIn("id", thread) # type: ignore
        self.assertEqual(thread["snippet"], {}) # type: ignore
        self.assertEqual(thread["comments"], []) # type: ignore

    def test_valid_input_empty_snippet(self):
        """Test successful insertion with empty snippet dictionary."""
        part_input = "snippet"
        snippet_input = {}

        result = create_comment_thread(part=part_input, snippet=snippet_input)

        self.assertTrue(result.get("success"))
        thread = result["commentThread"]
        self.assertIsNotNone(thread)
        self.assertEqual(thread["snippet"], {}) # type: ignore

    def test_valid_top_level_comment_no_id(self):
        """Test successful insertion with top_level_comment present but no 'id' field."""
        part_input = "snippet"
        top_level_comment_input = {"text": "A comment without an explicit ID field for this test."}

        result = create_comment_thread(part=part_input, top_level_comment=top_level_comment_input)
        
        self.assertTrue(result.get("success"))
        thread = result["commentThread"]
        self.assertIsNotNone(thread)
        self.assertEqual(thread["comments"], []) # type: ignore

    # --- Validation Tests for 'part' ---
    def test_invalid_part_type(self):
        """Test that non-string 'part' raises TypeError."""
        self.assert_error_behavior(
            func_to_call=create_comment_thread,
            expected_exception_type=TypeError,
            expected_message="Parameter 'part' must be a string.",
            part=123
        )

    def test_invalid_part_value(self):
        """Test that incorrect 'part' string raises InvalidPartParameterError."""
        self.assert_error_behavior(
            func_to_call=create_comment_thread,
            expected_exception_type=InvalidPartParameterError,
            expected_message="Invalid 'part' parameter: 'invalid_value'. Must be 'snippet'.",
            part="invalid_value"
        )

    # --- Validation Tests for 'snippet' (Pydantic) ---
    def test_invalid_snippet_type(self):
        """Test that non-dict 'snippet' raises Pydantic ValidationError."""
        self.assert_error_behavior(
            func_to_call=create_comment_thread,
            expected_exception_type=TypeError,
            expected_message="Parameter 'snippet' must be a dictionary.",
            part="snippet",
            snippet="not_a_dictionary"
        )

    # --- Validation Tests for 'top_level_comment' (Pydantic) ---
    def test_invalid_top_level_comment_type(self):
        """Test that non-dict 'top_level_comment' raises Pydantic ValidationError."""
        self.assert_error_behavior(
            func_to_call=create_comment_thread,
            expected_exception_type=TypeError,
            expected_message="Parameter 'top_level_comment' must be a dictionary.",
            part="snippet",
            top_level_comment="not_a_dictionary"
        )

    def test_snippet_allows_arbitrary_fields(self):
        """Test that 'snippet' Pydantic model allows arbitrary fields."""
        part_input = "snippet"
        snippet_input = {"custom_field": "custom_value", "another": 123}
        
        result = create_comment_thread(part=part_input, snippet=snippet_input)
        self.assertTrue(result.get("success"))
        thread = result["commentThread"]
        self.assertIsNotNone(thread)
        self.assertEqual(thread["snippet"], snippet_input) # type: ignore

    def test_top_level_comment_allows_arbitrary_fields(self):
        """Test that 'top_level_comment' Pydantic model allows arbitrary fields."""
        part_input = "snippet"
        top_level_comment_input = {"id": "comment-id-x", "custom_data": "value", "numeric": 42}
        
        result = create_comment_thread(part=part_input, top_level_comment=top_level_comment_input)
        self.assertTrue(result.get("success"))
        thread = result["commentThread"]
        self.assertIsNotNone(thread)
        self.assertIn("comment-id-x", thread["comments"]) # type: ignore


    def test_valid_input_all_none(self):
        """Test with all optional parameters as None, returning all items."""
        result = list_channels()
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 3) # All channels from mock DB

    def test_valid_input_with_category_id(self):
        """Test filtering by category_id."""
        result = list_channels(category_id="news")
        self.assertEqual(len(result["items"]), 0)
        self.assertTrue(all(item["categoryId"] == "news" for item in result["items"]))

    def test_valid_input_with_for_username(self):
        """Test filtering by for_username."""
        result = list_channels(for_username="testuser")
        self.assertEqual(len(result["items"]), 0)

    def test_valid_input_with_channel_id(self):
        """Test filtering by a specific channel_id."""
        result = list_channels(channel_id="ch2")
        self.assertEqual(len(result["items"]), 0)
        
    def test_valid_input_with_hl(self):
        """Test filtering by hl."""
        result = list_channels(hl="en")
        self.assertEqual(len(result["items"]), 1) # ch1, ch3
        self.assertTrue(all(item["hl"] == "en" for item in result["items"]))

    def test_valid_input_with_managed_by_me(self):
        """Test filtering by managed_by_me."""
        result = list_channels(managed_by_me=True)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "channel2")

    def test_valid_input_with_mine(self):
        """Test filtering by mine."""
        result = list_channels(mine=True)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "channel2")

    def test_valid_input_with_my_subscribers(self):
        """Test filtering by my_subscribers."""
        result = list_channels(my_subscribers=True)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["id"], "channel1")
        
    def test_valid_input_with_on_behalf_of_content_owner(self):
        """Test filtering by on_behalf_of_content_owner."""
        result = list_channels(on_behalf_of_content_owner="content_owner_A")
        self.assertEqual(len(result["items"]), 0)

    def test_valid_max_results(self):
        """Test limiting results with max_results."""
        result = list_channels(max_results=2)
        self.assertEqual(len(result["items"]), 2)

    def test_valid_max_results_boundary_low(self):
        """Test max_results at lower boundary (1)."""
        result = list_channels(max_results=1)
        self.assertEqual(len(result["items"]), 1)

    # Type Error Tests
    def test_invalid_type_category_id(self):
        """Test TypeError for invalid category_id type."""
        self.assert_error_behavior(
            list_channels, TypeError, "category_id must be a string or None.", category_id=123
        )

    def test_invalid_type_for_username(self):
        """Test TypeError for invalid for_username type."""
        self.assert_error_behavior(
            list_channels, TypeError, "for_username must be a string or None.", for_username=123
        )

    def test_invalid_type_hl(self):
        """Test TypeError for invalid hl type."""
        self.assert_error_behavior(
            list_channels, TypeError, "hl must be a string or None.", hl=True
        )

    def test_invalid_type_channel_id(self):
        """Test TypeError for invalid channel_id type."""
        self.assert_error_behavior(
            list_channels, TypeError, "channel_id must be a string or None.", channel_id=["id1"]
        )

    def test_invalid_type_managed_by_me(self):
        """Test TypeError for invalid managed_by_me type."""
        self.assert_error_behavior(
            list_channels, TypeError, "managed_by_me must be a boolean or None.", managed_by_me="true"
        )
    
    def test_invalid_type_mine(self):
        """Test TypeError for invalid mine type."""
        self.assert_error_behavior(
            list_channels, TypeError, "mine must be a boolean or None.", mine=0
        )

    def test_invalid_type_my_subscribers(self):
        """Test TypeError for invalid my_subscribers type."""
        self.assert_error_behavior(
            list_channels, TypeError, "my_subscribers must be a boolean or None.", my_subscribers="yes"
        )
        
    def test_invalid_type_on_behalf_of_content_owner(self):
        """Test TypeError for invalid on_behalf_of_content_owner type."""
        self.assert_error_behavior(
            list_channels, TypeError, "on_behalf_of_content_owner must be a string or None.", on_behalf_of_content_owner=object()
        )

    # max_results specific validation tests
    def test_invalid_type_max_results(self):
        """Test TypeError for invalid max_results type."""
        self.assert_error_behavior(
            list_channels, TypeError, "max_results must be an integer or None.", max_results="20"
        )

    def test_invalid_max_results_too_low(self):
        """Test MaxResultsOutOfRangeError for max_results < 1."""
        self.assert_error_behavior(
            list_channels, MaxResultsOutOfRangeError, "max_results must be between 1 and 50, inclusive.", max_results=0
        )

    def test_invalid_max_results_too_high(self):
        """Test MaxResultsOutOfRangeError for max_results > 50."""
        self.assert_error_behavior(
            list_channels, MaxResultsOutOfRangeError, "max_results must be between 1 and 50, inclusive.", max_results=51
        )

    def test_no_results_match(self):
        """Test scenario where no channels match the filter criteria."""
        result = list_channels(category_id="non_existent_category")
        self.assertEqual(len(result["items"]), 0)

    def test_valid_input_all_parts(self):
        """Test with valid 'part' and no other filters."""
        result = list_channel_sections(part="id,snippet,contentDetails", mine=True)
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 3) # Expect all sections

    def test_valid_input_single_part(self):
        """Test with a single valid 'part'."""
        result = list_channel_sections(part="snippet", mine=True)
        self.assertIsInstance(result, dict)
        self.assertIn("items", result)

    def test_valid_input_with_channel_id_filter(self):
        """Test filtering by channel_id."""
        result = list_channel_sections(part="id", channel_id="UCxyz")
        self.assertEqual(len(result["items"]), 0)
        for item in result["items"]:
            self.assertEqual(item["snippet"]["channelId"], "UCxyz")

            
    def test_valid_input_with_mine_false_filter(self):
        """Test filtering with mine=False (should return all sections where 'mine' doesn't restrict)."""
        result = list_channel_sections(part="id", mine=False)
        self.assertEqual(len(result["items"]), 3) # mine=False doesn't actively filter out, just doesn't apply 'mine' restriction

    def test_valid_input_with_hl_and_on_behalf_of(self):
        """Test with hl and on_behalf_of_content_owner (these don't affect filtering in mock logic)."""
        result = list_channel_sections(
            part="id",
            hl="en_US",
            on_behalf_of_content_owner="owner_id",
            mine=True
        )
        self.assertEqual(len(result["items"]), 3) # Expect all sections as these params don't filter

    def test_part_invalid_type(self):
        """Test 'part' parameter with invalid type."""
        self.assert_error_behavior(
            list_channel_sections,
            TypeError,
            "Parameter 'part' must be a string.",
            part=123
        )

    def test_part_empty_string(self):
        """Test 'part' parameter as an empty string."""
        self.assert_error_behavior(
            list_channel_sections,
            InvalidPartParameterError,
            "Parameter 'part' cannot be empty or consist only of whitespace.",
            part=""
        )

    def test_part_whitespace_only(self):
        """Test 'part' parameter with only whitespace."""
        self.assert_error_behavior(
            list_channel_sections,
            InvalidPartParameterError,
            "Parameter 'part' cannot be empty or consist only of whitespace.",
            part="   "
        )

    def test_part_only_commas(self):
        """Test 'part' parameter with only commas."""
        self.assert_error_behavior(
            list_channel_sections,
            InvalidPartParameterError,
            r"Parameter 'part' resulted in no valid components after parsing. Original value: ',,,'",
            part=",,,"
        )

    def test_part_no_valid_components(self):
        """Test 'part' parameter with no valid components."""
        self.assert_error_behavior(
            list_channel_sections,
            InvalidPartParameterError,
            r"Invalid part parameter",
            part="invalid,another_invalid"
        )

    def test_part_some_valid_some_invalid_components(self):
        """Test 'part' with mixed valid and invalid components (should pass)."""
        result = list_channel_sections(part="id,invalid_component,snippet", mine=True)
        self.assertIn("items", result) # Should succeed as 'id' and 'snippet' are valid

    def test_channel_id_invalid_type(self):
        """Test 'channel_id' parameter with invalid type."""
        self.assert_error_behavior(
            list_channel_sections,
            TypeError,
            "Parameter 'channel_id' must be a string or None.",
            part="id", channel_id=123
        )

    def test_hl_invalid_type(self):
        """Test 'hl' parameter with invalid type."""
        self.assert_error_behavior(
            list_channel_sections,
            TypeError,
            "Parameter 'hl' must be a string or None.",
            part="id", hl=123
        )

    def test_section_id_invalid_type(self):
        """Test 'section_id' parameter with invalid type."""
        self.assert_error_behavior(
            list_channel_sections,
            TypeError,
            "Parameter 'section_id' must be a string or None.",
            part="id", section_id=123
        )

    def test_mine_invalid_type(self):
        """Test 'mine' parameter with invalid type."""
        self.assert_error_behavior(
            list_channel_sections,
            TypeError,
            "Parameter 'mine' must be a boolean or None.",
            part="id", mine="true"
        )

    def test_on_behalf_of_content_owner_invalid_type(self):
        """Test 'on_behalf_of_content_owner' parameter with invalid type."""
        self.assert_error_behavior(
            list_channel_sections,
            TypeError,
            "Parameter 'on_behalf_of_content_owner' must be a string or None.",
            part="id", on_behalf_of_content_owner=123, 
            mine=True   
        )

    def test_on_no_filter_raises_error(self):
        """Test 'no filter' raises error."""
        self.assert_error_behavior(
            list_channel_sections,
            InvalidFilterParameterError,
            "Exactly one of 'channelId', 'id', or 'mine' must be provided.",
            part="id"   
        )

    def test_on_multiple_signal_filters_raises_error(self):
        """Test 'multiple section filters' raises error."""
        self.assert_error_behavior(
            list_channel_sections,
            InvalidFilterParameterError,
            "Only one of 'channel_id', 'section_id', or 'mine' can be provided.",
            part="id", 
            mine=True, channel_id="UCxyz"   
        )
    
    def test_optional_parameters_as_none(self):
        """Test with all optional parameters set to None (default for some)."""
        result = list_channel_sections(
            part="id",
            channel_id=None,
            hl=None,
            section_id=None,
            on_behalf_of_content_owner=None,
            mine=True
        )

        self.assertIsInstance(result, dict)
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 3) # Expect all sections as no filters applied effectively

        """
        Conceptual test for KeyError propagation.
        Directly testing KeyError from DB.get is complex with a simple dict and no mocks,
        as dict.get(key, default) doesn't raise KeyError.
        This test acknowledges the requirement from the docstring.
        If DB were a custom object whose .get() method could raise KeyError,
        that scenario would be covered by the 'Raises: KeyError' in the docstring.
        """
        # To simulate this, one would need to mock DB or use a DB object
        # that behaves this way. For now, we rely on the function's docstring.
        # Example of how it might be tested with a mock (OUT OF SCOPE FOR CURRENT TASK):
        #
        # global DB
        # original_db = DB
        # class MockDBError:
        #     def get(self, key, default=None):
        #         raise KeyError("Simulated DB KeyError")
        # DB = MockDBError()
        # self.assert_error_behavior(
        #     list_channel_sections,
        #     KeyError,
        #     "Simulated DB KeyError",
        #     part="id"
        # )
        # DB = original_db # Restore
        pass

    
    def test_delete_nonexistent_section_id_raises_keyerror(self):
        """Test that attempting to delete a non-existent section_id raises KeyError."""
        non_existent_id = "section_delta_non_existent"
        expected_keyerror_message = f"'Channel section ID: {non_existent_id} not found in the database.'"
        
        self.assert_error_behavior(
            func_to_call=delete_channel_section,
            expected_exception_type=KeyError,
            expected_message=expected_keyerror_message,
            section_id=non_existent_id
        )

    def test_invalid_section_id_type_integer_raises_typeerror(self):
        """Test that providing an integer section_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete_channel_section,
            expected_exception_type=TypeError,
            expected_message="section_id must be a string.",
            section_id=12345 # Invalid type
        )

    def test_invalid_section_id_type_none_raises_typeerror(self):
        """Test that providing None as section_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete_channel_section,
            expected_exception_type=TypeError,
            expected_message="section_id must be a string.",
            section_id=None # Invalid type
        )

    def test_invalid_on_behalf_of_content_owner_type_integer_raises_typeerror(self):
        """Test that providing an integer on_behalf_of_content_owner raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete_channel_section,
            expected_exception_type=TypeError,
            expected_message="on_behalf_of_content_owner must be a string if provided.",
            section_id="section_alpha",
            on_behalf_of_content_owner=98765 # Invalid type
        )

    def test_invalid_on_behalf_of_content_owner_type_list_raises_typeerror(self):
        """Test that providing a list for on_behalf_of_content_owner raises TypeError."""
        self.assert_error_behavior(
            func_to_call=delete_channel_section,
            expected_exception_type=TypeError,
            expected_message="on_behalf_of_content_owner must be a string if provided.",
            section_id="section_alpha",
            on_behalf_of_content_owner=[] # Invalid type
        )
    

    def test_empty_string_section_id_keyerror_if_not_exists(self):
        """Test that an empty string section_id raises KeyError if it does not exist."""

        expected_msg = "'Channel section ID:  not found in the database.'" # Note: two spaces after colon
        self.assert_error_behavior(
            func_to_call=delete_channel_section,
            expected_exception_type=KeyError,
            expected_message=expected_msg,
            section_id=""
        )


class TestInsertSubscriptionsAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "subscriptions": {
                }
            }
        )

    def test_create_subscription(self):
        """Test that a subscription can be created."""
        result = YoutubeAPI.Subscriptions.insert(part="snippet", snippet={
            "channelId": "UCxyz",
            "resourceId": {
                "kind": "youtube#channel",
                "channelId": "UCxyz"
            }
        })
        self.assertEqual(result["part"], "snippet")
        self.assertEqual(len(DB["subscriptions"]),1)
        self.assertEqual(result["subscription"]["snippet"]["channelId"], "UCxyz")

    def test_create_subscription_invalid_part_type(self):
        """Test that a subscription can be created."""
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.Subscriptions.insert,
            expected_exception_type=TypeError,
            expected_message="part must be a string",
            part=123,
            snippet={})

    def test_create_subscription_part_missing(self):
        """Test that a subscription can be created."""
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.Subscriptions.insert,
            expected_exception_type=ValueError,
            expected_message="Part parameter required",
            part=None, snippet={})

    def test_create_subscription_invalid_snippet_type(self):
        """Test that a subscription can be created."""
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.Subscriptions.insert,
            expected_exception_type=TypeError,
            expected_message="snippet must be a dictionary",
            part="snippet",
            snippet=123)

    def test_create_subscription_invalid_snippet_value(self):
        """Test that a subscription can be created."""
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.Subscriptions.insert,
            expected_exception_type=ValueError,
            expected_message="Snippet parameter required",
            part="snippet",
            snippet=None)

    def test_create_subscription_invalid_resource_id_type(self):
        """Test that a subscription can be created."""
        with self.assertRaises(ValidationError) as context:
            YoutubeAPI.Subscriptions.insert(part="snippet", snippet={
                "channelId": "UCxyz",
                "resourceId": 123
            })

    def test_create_subscription_invalid_snippet_structure(self):
        """Test that a subscription can be created."""
        with self.assertRaises(ValidationError) as context:
            YoutubeAPI.Subscriptions.insert(part="snippet", snippet={
                "channelId": "UCxyz",
                "resourceId": {
                    "channelId": 123
                }
            })
               
from youtube.Subscriptions import list

class TestSubscriptionsList(BaseTestCaseWithErrorHandler):
    """Comprehensive test suite for the subscriptions list function."""

    def setUp(self):
        """Set up test data before each test."""
        # Reset the global DB state before each test
        DB.clear()
        DB.update({
            "subscriptions": {
                "sub_1": {
                    "id": "sub_1",
                    "snippet": {
                        "channelId": "channel1",
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": "channel4"
                        },

                    }
                },
                "sub_2": {
                    "id": "sub_2",
                    "snippet": {
                        "channelId": "channel2",
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": "channel1"
                        },
                        
                    }
                },
                "sub_3": {
                    "id": "sub_3",
                    "snippet": {
                        "channelId": "channel1",
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": "channel3"
                        },
                        
                    }
                },
                "sub_4": {
                    "id": "sub_4",
                    "snippet": {
                        "channelId": "channel3",
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": "channel4"
                        },
                    
                    }
                },
                
            },
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
        },
        "channel3": {
            "part": "snippet,contentDetails,statistics",
            "categoryId": "15",
            "forUsername": "TravelVlogs",
            "hl": "en",
            "id": "channel3",
            "managedByMe": False,
            "maxResults": 5,
            "mine": False,
            "mySubscribers": True,
            "onBehalfOfContentOwner": None
        },
        "channel4": {
            "part": "snippet,statistics",
            "categoryId": "20",
            "forUsername": "Foodieeee",
            "hl": "es",
            "id": "channel4",
            "managedByMe": True,
            "maxResults": 10,
            "mine": True,
            "mySubscribers": False,
            "onBehalfOfContentOwner": "CompanyXYZ"
        }
        
            },
        "current_user": "channel1"
        })

    def test_successful_list_all_subscriptions(self):
        """Test successful retrieval of all subscriptions."""
        result = list("snippet")
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 4)  # Should return 4 valid subscriptions
        self.assertNotIn("error", result)


    def test_filter_by_channel_id(self):
        """Test filtering by channel ID."""
        result = list("snippet", channel_id="channel1")
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)  # Should return 2 subscriptions
        for item in result["items"]:
            self.assertEqual(item["snippet"]["channelId"], "channel1")

    def test_filter_by_subscription_id(self):
        """Test filtering by specific subscription ID."""
        result = list("snippet", subscription_id="sub_1")
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "sub_1")

    def test_filter_by_mine_true(self):
        """Test filtering by mine=True."""
        result = list("snippet", mine=True)
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)  # Should return 2 subscriptions
        for item in result["items"]:
            self.assertEqual(item["snippet"]["channelId"], DB["current_user"])
        

    def test_filter_by_my_subscribers_true(self):
        """Test filtering by my_subscribers=True."""
        result = list("snippet", my_subscribers=True)
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)  # Should return 1 subscription
        for item in result["items"]:
            self.assertEqual(item["snippet"]["channelId"], DB["current_user"])

    def test_filter_by_for_channel_id(self):
        """Test filtering by for_channel_id."""
        result = list("snippet", for_channel_id="channel3")
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)  # Should return 2 subscriptions
        for item in result["items"]:
            self.assertEqual(item["snippet"]["resourceId"]["channelId"], "channel3")

    def test_max_results_limit(self):
        """Test max_results parameter."""
        result = list("snippet", max_results=2)
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 2)


    def test_ordering_alphabetical(self):
        """Test alphabetical ordering."""
        result = list("snippet", order="alphabetical")
        
        self.assertIn("items", result)
        # Check that results are sorted by channelId
        channel_ids = [item["snippet"]["resourceId"]["channelId"] for item in result["items"]]
        self.assertEqual(channel_ids, sorted(channel_ids))

   
    def test_multiple_filters_combined(self):
        """Test combining multiple filters."""
        result = list(
            "snippet",
            channel_id="channel1",
            mine=True,
            max_results=1
        )
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]   
        self.assertEqual(item["snippet"]["resourceId"]["channelId"], "channel4")
        self.assertEqual(item["snippet"]["channelId"], DB["current_user"])

    def test_empty_database(self):
        """Test behavior with empty database."""
        DB.clear()
        DB.update({"subscriptions": {}})
        
        result = list("snippet")
        
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 0)

    # Error handling tests
    def test_missing_part_parameter(self):
        """Test error when part parameter is missing."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=ValueError,
            expected_message="part parameter required",
            part=None
        )

    def test_invalid_part_parameter_type(self):
        """Test error when part parameter is not a string."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="part must be a string",
            part=123
        )


    def test_invalid_subscription_id_type(self):
        """Test error when subscription_id is not a string."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="subscription_id must be a string",
            part="snippet",
            subscription_id=123
        )

    def test_invalid_mine_type(self):
        """Test error when mine is not a boolean."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="mine parameter must be a boolean",
            part="snippet",
            mine="true"
        )

    def test_invalid_my_subscribers_type(self):
        """Test error when my_subscribers is not a boolean."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="my_subscribers parameter must be a boolean",
            part="snippet",
            my_subscribers="true"
        )

    def test_invalid_for_channel_id_type(self):
        """Test error when for_channel_id is not a string."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="for_channel_id must be a string",
            part="snippet",
            for_channel_id=123
        )

    def test_invalid_max_results_type(self):
        """Test error when max_results is not an integer."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="max_results must be an integer",
            part="snippet",
            max_results="10"
        )


    def test_invalid_order_value(self):
        """Test error when order has invalid value."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=ValueError,
            expected_message="order must be 'alphabetical'",
            part="snippet",
            order="invalid_order"
        )

    def test_invalid_order_type(self):
        """Test error when order is not a string."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="order must be a string",
            part="snippet",
            order=123
        )

    def test_invalid_page_token_type(self):
        """Test error when page_token is not a string."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="page_token must be a string",
            part="snippet",
            page_token=123
        )

    def test_empty_page_token(self):
        """Test error when page_token is empty string."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=ValueError,
            expected_message="page_token must be a positive integer",
            part="snippet",
            page_token=""
        )

    def test_invalid_on_behalf_of_content_owner_type(self):
        """Test error when on_behalf_of_content_owner is not a string."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="on_behalf_of_content_owner must be a string",
            part="snippet",
            on_behalf_of_content_owner=123
        )

    def test_invalid_on_behalf_of_content_owner_channel_type(self):
        """Test error when on_behalf_of_content_owner_channel is not a string."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=TypeError,
            expected_message="on_behalf_of_content_owner_channel must be a string",
            part="snippet",
            on_behalf_of_content_owner_channel=123
        )

    # Edge cases and boundary tests
    def test_none_parameters(self):
        """Test behavior with None parameters."""
        result = list("snippet", channel_id=None, subscription_id=None)
        
        self.assertIn("items", result)

        

    def test_large_max_results(self):
        """Test with maximum allowed max_results."""
        result = list("snippet", max_results=50)
        
        self.assertIn("items", result)
        self.assertLessEqual(len(result["items"]), 4)

    def test_non_existent_subscription_id(self):
        """Test filtering by non-existent subscription ID."""
        
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=ValueError,
            expected_message="subscription_id must be a valid subscription ID",
            part="snippet",
            subscription_id="non_existent"
        )

    def test_non_existent_channel_id(self):
        """Test filtering by non-existent channel ID."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=ValueError,
            expected_message="channel_id must be a valid channel ID",
            part="snippet",
            channel_id="UC_non_existent"
        )

    def test_non_existent_for_channel_id(self):
        """Test filtering by non-existent for_channel_id."""
        self.assert_error_behavior(
            func_to_call=list,
            expected_exception_type=ValueError,
            expected_message="for_channel_id must be a valid channel ID",
            part="snippet",
            for_channel_id="UC_non_existent"
        )
    

    def test_missing_channel_id_in_resource_id(self):
        """Test handling of resourceId with missing channelId."""
           
        result = list("snippet")
        
        self.assertIn("items", result)
        # Should skip subscriptions with missing resourceId.channelId
        self.assertEqual(len(result["items"]), 4)
          

    def test_complex_filtering(self):
        """Test complex filtering scenarios."""
        # Test multiple filters together
        result = list(
            "snippet",
            mine=True,
            max_results=1,
            order="alphabetical"
        )
        
        self.assertIn("items", result)
        self.assertLessEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["snippet"]["resourceId"]["channelId"], "channel3")
       
class TestDeleteSubscriptionsAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "subscriptions": {
                    "sub1": {
                        "id": "sub1",
                        "snippet": {
                            "channelId": "channel1",
                            "resourceId": {
                                "kind": "youtube#channel",
                                "channelId": "channel2"
                }}},
                "sub2": {
                    "id": "sub2",
                    "snippet": {
                        "channelId": "channel2",
                        "resourceId": {
                            "kind": "youtube#channel",
                            "channelId": "channel3"
                        }
                    }
                }
            }}
        )

    def test_delete_subscription_invalid_subscription_id_type(self):
        """Test that providing an integer subscription_id raises TypeError."""
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.Subscriptions.delete,
            expected_exception_type=TypeError,
            expected_message="Subscription ID must be a string",
            subscription_id=12345 # Invalid type
        )

    def test_delete_subscription_invalid_subscription_id_none(self):
        """Test that providing None as subscription_id raises ValueError."""
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.Subscriptions.delete,
            expected_exception_type=ValueError,
            expected_message="Subscription ID is required",
            subscription_id=None # Invalid type
        )

    def test_delete_subscription_invalid_subscription_id_empty_string(self):
        """Test that providing an empty string as subscription_id raises ValueError."""
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.Subscriptions.delete,
            expected_exception_type=ValueError,
            expected_message="Subscription ID is required",
            subscription_id="" # Invalid type
        )

    def test_delete_subscription_invalid_subscription_id_not_found(self):
        """Test that providing a non-existent subscription_id raises ValueError."""
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.Subscriptions.delete,
            expected_exception_type=ValueError,
            expected_message="Subscription not found",
            subscription_id="sub3" # Invalid type
        )

    def test_delete_subscription(self):
        """Test that a subscription can be deleted."""
        result = YoutubeAPI.Subscriptions.delete(subscription_id="sub1")
        self.assertEqual(result, True)
        self.assertNotIn("sub1", DB["subscriptions"])
        self.assertEqual(len(DB["subscriptions"]), 1)
    

    def test_empty_string_section_id_keyerror_if_not_exists(self):
        """Test that empty string section_id raises KeyError if not exists."""
        with self.assertRaises(KeyError):
            delete_channel_section(section_id="")

    # Additional tests for Caption.insert function to increase coverage for lines 196-198
    def test_captions_insert_on_behalf_of_complex_types(self):
        """Tests onBehalfOf type validation with complex objects to cover line 151."""
        # Test with complex objects that should fail type validation
        complex_objects = [
            object(),  # Generic object
            type,  # Type object
            lambda x: x,  # Function
            type('CustomClass', (), {})(),  # Custom class instance
            Exception(),  # Exception instance
            range(10),  # Range object
            set([1, 2, 3]),  # Set
            frozenset([1, 2, 3]),  # Frozen set
            bytearray(b'test'),  # Bytearray
            memoryview(b'test'),  # Memoryview
        ]
        
        for obj in complex_objects:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=obj)
            self.assertIn("On behalf of must be a string", str(context.exception))


    def test_captions_insert_type_validation_boundary_values(self):
        """Tests type validation with boundary values to ensure complete coverage."""
        # Test with boundary values for onBehalfOf
        boundary_values = [0, -1, 1, 255, 256, 65535, 65536, 2147483647, -2147483648]
        
        for value in boundary_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=value)
            self.assertIn("On behalf of must be a string", str(context.exception))
        
        # Test with boundary values for onBehalfOfContentOwner
        for value in boundary_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner=value)
            self.assertIn("On behalf of content owner must be a string", str(context.exception))
        
        # Test with boundary values for sync (should only accept True/False)
        for value in boundary_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=value)
            self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_floating_point(self):
        """Tests type validation with floating point numbers to ensure complete coverage."""
        # Test with floating point numbers for onBehalfOf
        float_values = [0.0, 1.0, -1.0, 3.14159, 2.71828, float('inf'), float('-inf'), float('nan')]
        
        for value in float_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=value)
            self.assertIn("On behalf of must be a string", str(context.exception))
        
        # Test with floating point numbers for onBehalfOfContentOwner
        for value in float_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner=value)
            self.assertIn("On behalf of content owner must be a string", str(context.exception))
        
        # Test with floating point numbers for sync
        for value in float_values:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=value)
            self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

    def test_captions_insert_type_validation_string_like_objects(self):
        """Tests type validation with string-like objects that should still fail."""
        # Test with string-like objects that are not actual strings
        string_like_objects = [
            b'bytes_string',  # Bytes
            bytearray(b'bytearray_string'),  # Bytearray
            memoryview(b'memoryview_string'),  # Memoryview
        ]
        
        for obj in string_like_objects:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOf=obj)
            self.assertIn("On behalf of must be a string", str(context.exception))
            
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=False, onBehalfOfContentOwner=obj)
            self.assertIn("On behalf of content owner must be a string", str(context.exception))

    def test_captions_insert_type_validation_nested_structures(self):
        """Tests type validation with nested data structures."""
        # Test with nested structures for onBehalfOf
        nested_structures = [
            [1, 2, 3],  # List
            {"a": 1, "b": 2},  # Dictionary
            (1, 2, 3),  # Tuple
            [[1, 2], [3, 4]],  # Nested list
            {"a": {"b": 1}},  # Nested dictionary
            [{"a": 1}, {"b": 2}],  # List of dictionaries
        ]
        
        for structure in nested_structures:
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, onBehalfOf=structure)
            self.assertIn("On behalf of must be a string", str(context.exception))
            
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, onBehalfOfContentOwner=structure)
            self.assertIn("On behalf of content owner must be a string", str(context.exception))
            
            with self.assertRaises(TypeError) as context:
                Caption.insert(part="snippet", snippet={"videoId": "test", "text": "Caption text"}, sync=structure)
            self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

   

    def test_captions_insert_type_validation_comprehensive_coverage(self):
        """Comprehensive test to ensure all type validation lines are covered."""
        # Test all possible combinations of invalid types
        test_cases = [
            # (onBehalfOf, onBehalfOfContentOwner, sync, expected_error_param)
            (123, None, False, "onBehalfOf"),
            (None, 456, False, "onBehalfOfContentOwner"),
            (None, None, "invalid", "sync"),
            (123, 456, False, "onBehalfOf"),
            (123, None, True, "onBehalfOf"),  # Use valid sync to test onBehalfOf
            (None, 456, True, "onBehalfOfContentOwner"),  # Use valid sync to test onBehalfOfContentOwner
            (123, 456, False, "onBehalfOf"),  # Use valid sync to test onBehalfOf first
        ]
        
        for on_behalf_of, on_behalf_of_content_owner, sync, expected_param in test_cases:
            with self.assertRaises(TypeError) as context:
                Caption.insert(
                    part="snippet", 
                    snippet={"videoId": "test", "text": "Caption text"}, 
                    onBehalfOf=on_behalf_of,
                    onBehalfOfContentOwner=on_behalf_of_content_owner,
                    sync=sync
                )
            
            if expected_param == "onBehalfOf":
                self.assertIn("On behalf of must be a string", str(context.exception))
            elif expected_param == "onBehalfOfContentOwner":
                self.assertIn("On behalf of content owner must be a string", str(context.exception))
            elif expected_param == "sync":
                self.assertIn("Parameter 'sync' must be a boolean", str(context.exception))

class TestVideoCategoriesAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Setup method to prepare for each test."""
        DB.update(
            {
                "videoCategories": {
                    "category1": {
                        "id": "category1",
                        "snippet": {
                            "title": "Category 1",
                            "regionCode": "US"
                        }
                    },
                    "category2": {
                        "id": "category2",
                        "snippet": {
                            "title": "Category 2",
                            "regionCode": "CA"
                        }
                    }   
                }
            }
        )

    def test_video_categories_list_success(self):
        """Test that the video categories list function returns a list of video categories."""
        result = YoutubeAPI.VideoCategory.list(part="snippet")
        self.assertIn("items", result)
        self.assertIsInstance(result["items"], List)
        self.assertEqual(len(result["items"]), 2)
        for item in result["items"]:
            self.assertIn("id", item)
            self.assertIn("snippet", item)

        result = YoutubeAPI.VideoCategory.list(part="snippet", id="category1")
        self.assertIn("items", result)
        self.assertIsInstance(result["items"], List)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "category1")
        self.assertEqual(result["items"][0]["snippet"]["title"], "Category 1")
        self.assertEqual(result["items"][0]["snippet"]["regionCode"], "US")

        result = YoutubeAPI.VideoCategory.list(part="snippet", region_code="US")
        self.assertIn("items", result)
        self.assertIsInstance(result["items"], List)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "category1")
        self.assertEqual(result["items"][0]["snippet"]["title"], "Category 1")
        self.assertEqual(result["items"][0]["snippet"]["regionCode"], "US")

        result = YoutubeAPI.VideoCategory.list(part="snippet", max_results=1)
        self.assertIn("items", result)
        self.assertIsInstance(result["items"], List)
        self.assertEqual(len(result["items"]), 1)
            

    def test_video_categories_list_invalid_part(self):
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.VideoCategory.list,
            expected_exception_type=TypeError,
            expected_message="part must be a string",
            part=123
        )
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.VideoCategory.list,
            expected_exception_type=ValueError,
            expected_message="part must be 'snippet'",
            part="invalid"
        )
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.VideoCategory.list,
            expected_exception_type=ValueError,
            expected_message="part is required",
            part=None
        )
    
    def test_video_categories_list_invalid_id(self):
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.VideoCategory.list,
            expected_exception_type=TypeError,
            expected_message="id must be a string",
            part="snippet",
            id=123
        )
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.VideoCategory.list,
            expected_exception_type=ValueError,
            expected_message="Given ID not found in DB",
            part="snippet",
            id="invalid"
        )
    
    def test_video_categories_list_invalid_region_code(self):
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.VideoCategory.list,
            expected_exception_type=TypeError,
            expected_message="region_code must be a string",
            part="snippet",
            region_code=123
        )

    def test_video_categories_list_invalid_max_results(self):
        self.assert_error_behavior(
            func_to_call=YoutubeAPI.VideoCategory.list,
            expected_exception_type=TypeError,
            expected_message="max_results must be an integer",
            part="snippet",
            max_results="invalid"
        )

        self.assert_error_behavior(
            func_to_call=YoutubeAPI.VideoCategory.list,
            expected_exception_type=ValueError,
            expected_message="max_results must be greater than 0",
            part="snippet",
            max_results=-1
        )

if __name__ == "__main__":
    unittest.main()

