import unittest
from unittest.mock import patch, MagicMock
from youtube.Videos import list as list_videos
from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube.SimulationEngine.db import DB


class TestVideosList(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test data for video list tests."""
        DB.clear()
        DB.update({
            "videos": {
                "video1": {
                    "id": "video1",
                    "snippet": {
                        "title": "Test Video 1",
                        "description": "Description 1"
                    },
                    "statistics": {
                        "viewCount": "1000",
                        "likeCount": "100"
                    },
                    "status": {
                        "privacyStatus": "public"
                    },
                    "contentDetails": {
                        "duration": "PT1M30S"
                    }
                },
                "video2": {
                    "id": "video2",
                    "snippet": {
                        "title": "Test Video 2",
                        "description": "Description 2"
                    },
                    "statistics": {
                        "viewCount": "2000",
                        "likeCount": "200"
                    },
                    "status": {
                        "privacyStatus": "public"
                    },
                    "contentDetails": {
                        "duration": "PT2M0S"
                    }
                },
                "video3": {
                    "id": "video3",
                    "snippet": {
                        "title": "Test Video 3",
                        "description": "Description 3"
                    },
                    "statistics": {
                        "viewCount": "500",
                        "likeCount": "50"
                    },
                    "status": {
                        "privacyStatus": "private"
                    },
                    "contentDetails": {
                        "duration": "PT3M0S"
                    }
                }
            },
            "users": {
                "user1": {
                    "id": "user1",
                    "name": "Test User"
                }
            }
        })

    # Test successful scenarios with valid part parameter
    def test_list_videos_with_chart_most_popular(self):
        """Test listing videos with chart=mostPopular parameter."""
        
        result = list_videos(part="snippet", chart="mostPopular")
        
        self.assertEqual(result["kind"], "youtube#videoListResponse")
        self.assertIn("items", result)
        self.assertIn("pageInfo", result)
        self.assertEqual(len(result["items"]), 3)
        
        # Verify videos are sorted by view count in descending order
        items = result["items"]
        self.assertEqual(items[0]["id"], "video2")  # 2000 views
        self.assertEqual(items[1]["id"], "video1")  # 1000 views
        self.assertEqual(items[2]["id"], "video3")  # 500 views

    def test_list_videos_with_single_id(self):
        """Test listing videos with a single video ID."""
        
        result = list_videos(part="snippet", id="video1")
        
        self.assertEqual(result["kind"], "youtube#videoListResponse")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], "video1")

    def test_list_videos_with_multiple_ids(self):
        """Test listing videos with multiple comma-separated video IDs."""
        
        result = list_videos(part="snippet", id="video1,video2")
        
        self.assertEqual(result["kind"], "youtube#videoListResponse")
        self.assertEqual(len(result["items"]), 2)
        video_ids = [item["id"] for item in result["items"]]
        self.assertIn("video1", video_ids)
        self.assertIn("video2", video_ids)

    def test_list_videos_with_my_rating_and_user_id(self):
        """Test listing videos with my_rating parameter and user_id."""
        
        result = list_videos(part="snippet", my_rating="like", user_id="user1")
        
        self.assertEqual(result["kind"], "youtube#videoListResponse")
        self.assertIn("items", result)

    def test_list_videos_with_max_results(self):
        """Test listing videos with max_results parameter."""
        
        result = list_videos(part="snippet", chart="mostPopular", max_results=2)
        
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["pageInfo"]["resultsPerPage"], 2)

    def test_list_videos_with_page_token(self):
        """Test listing videos with page_token parameter."""
        
        result = list_videos(part="snippet", chart="mostPopular", max_results=2, page_token=2)
        
        self.assertEqual(len(result["items"]), 1)  # Only 1 video left on page 2
        self.assertEqual(result["items"][0]["id"], "video3")

    def test_list_videos_with_all_valid_parts(self):
        """Test listing videos with all valid part parameters."""
        
        for part in ["snippet", "contentDetails", "statistics", "status"]:
            result = list_videos(part=part, chart="mostPopular")
            self.assertEqual(result["kind"], "youtube#videoListResponse")
            self.assertIn("items", result)

    def test_list_videos_empty_database(self):
        """Test listing videos when database is empty."""
        DB.clear()
        
        result = list_videos(part="snippet", chart="mostPopular")
        
        self.assertEqual(result["kind"], "youtube#videoListResponse")
        self.assertEqual(len(result["items"]), 0)

    # Test error scenarios - Part parameter validation

    def test_list_videos_none_part_parameter(self):
        """Test error when part parameter is None."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "The 'part' parameter is required.",
            part=None
        )

    def test_list_videos_empty_part_parameter(self):
        """Test error when part parameter is empty string."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "The 'part' parameter is required.",
            part=""
        )

    def test_list_videos_non_string_part_parameter(self):
        """Test error when part parameter is not a string."""
        self.assert_error_behavior(
            list_videos,
            TypeError,
            "The 'part' parameter must be a string.",
            part=123
        )

    def test_list_videos_invalid_part_value(self):
        """Test error when part parameter has invalid value."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "Invalid value for 'part'. Must be one of: 'snippet', 'contentDetails', 'statistics', 'status'.",
            part="invalid_part"
        )

    # Test error scenarios - Filter parameter validation
    def test_list_videos_no_filter_parameter(self):
        """Test error when no filter parameter is provided."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "Only one of 'chart', 'id', or 'my_rating' can be provided.",
            part="snippet"
        )

    def test_list_videos_multiple_filter_parameters(self):
        """Test error when multiple filter parameters are provided."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "Only one of 'chart', 'id', or 'my_rating' can be provided.",
            part="snippet",
            chart="mostPopular",
            id="video1"
        )

    def test_list_videos_all_filter_parameters(self):
        """Test error when all filter parameters are provided."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "Only one of 'chart', 'id', or 'my_rating' can be provided.",
            part="snippet",
            chart="mostPopular",
            id="video1",
            my_rating="like"
        )

    # Test error scenarios - Chart parameter validation
    def test_list_videos_non_string_chart_parameter(self):
        """Test error when chart parameter is not a string."""
        self.assert_error_behavior(
            list_videos,
            TypeError,
            "The 'chart' parameter must be a string.",
            part="snippet",
            chart=123
        )

    def test_list_videos_invalid_chart_value(self):
        """Test error when chart parameter has invalid value."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "Invalid value for 'chart'. Only 'mostPopular' is supported.",
            part="snippet",
            chart="invalid_chart"
        )

    # Test error scenarios - ID parameter validation
    def test_list_videos_non_string_id_parameter(self):
        """Test error when id parameter is not a string."""
        self.assert_error_behavior(
            list_videos,
            TypeError,
            "The 'id' parameter must be a string.",
            part="snippet",
            id=123
        )

    def test_list_videos_id_not_found(self):
        """Test error when video ID is not found in database."""
        
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "Video with ID 'nonexistent' not found.",
            part="snippet",
            id="nonexistent"
        )

    def test_list_videos_partial_id_not_found(self):
        """Test error when one of multiple video IDs is not found."""
        
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "Video with ID 'nonexistent' not found.",
            part="snippet",
            id="video1,nonexistent"
        )

    # Test error scenarios - My rating parameter validation
    def test_list_videos_my_rating_missing_user_id(self):
        """Test error when my_rating is provided without user_id."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "The 'user_id' parameter is required when using 'my_rating' parameter.",
            part="snippet",
            my_rating="like"
        )

    def test_list_videos_non_string_user_id(self):
        """Test error when user_id parameter is not a string."""
        self.assert_error_behavior(
            list_videos,
            TypeError,
            "The 'user_id' parameter must be a string.",
            part="snippet",
            my_rating="like",
            user_id=123
        )

    def test_list_videos_user_id_not_found(self):
        """Test error when user_id is not found in database."""
        
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "User with ID 'nonexistent' not found.",
            part="snippet",
            my_rating="like",
            user_id="nonexistent"
        )

    def test_list_videos_non_string_my_rating(self):
        """Test error when my_rating parameter is not a string."""
        self.assert_error_behavior(
            list_videos,
            TypeError,
            "The 'my_rating' parameter must be a string.",
            part="snippet",
            my_rating=123,
            user_id="user1"
        )

    # Test error scenarios - Max results parameter validation
    def test_list_videos_non_integer_max_results(self):
        """Test error when max_results parameter is not an integer."""
        self.assert_error_behavior(
            list_videos,
            TypeError,
            "The 'max_results' parameter must be an integer.",
            part="snippet",
            chart="mostPopular",
            max_results="invalid"
        )

    def test_list_videos_zero_max_results(self):
        """Test error when max_results parameter is zero."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "The 'max_results' parameter must be greater than 0 and less than 50.",
            part="snippet",
            chart="mostPopular",
            max_results=0
        )

    def test_list_videos_negative_max_results(self):
        """Test error when max_results parameter is negative."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "The 'max_results' parameter must be greater than 0 and less than 50.",
            part="snippet",
            chart="mostPopular",
            max_results=-1
        )

    def test_list_videos_max_results_too_large(self):
        """Test error when max_results parameter exceeds 50."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "The 'max_results' parameter must be greater than 0 and less than 50.",
            part="snippet",
            chart="mostPopular",
            max_results=51
        )

    # Test error scenarios - Page token parameter validation
    def test_list_videos_non_integer_page_token(self):
        """Test error when page_token parameter is not an integer."""
        self.assert_error_behavior(
            list_videos,
            TypeError,
            "The 'page_token' parameter must be an integer.",
            part="snippet",
            chart="mostPopular",
            page_token="invalid"
        )

    def test_list_videos_zero_page_token(self):
        """Test error when page_token parameter is zero."""
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "The 'page_token' parameter must be greater than 0.",
            part="snippet",
            chart="mostPopular",
            page_token=0
        )

    def test_list_videos_page_token_out_of_range(self):
        """Test error when page_token parameter is out of range."""
        
        self.assert_error_behavior(
            list_videos,
            ValueError,
            "The 'page_token' parameter is out of range.",
            part="snippet",
            chart="mostPopular",
            max_results=2,
            page_token=5  # Would require at least 8 videos (5-1)*2, but we only have 3
        )

    # Test edge cases and boundary conditions
    def test_list_videos_max_results_boundary_values(self):
        """Test max_results with boundary values."""
        
        # Test minimum valid value
        result = list_videos(part="snippet", chart="mostPopular", max_results=1)
        self.assertEqual(len(result["items"]), 1)
        
        # Test maximum valid value
        result = list_videos(part="snippet", chart="mostPopular", max_results=49)
        self.assertEqual(len(result["items"]), 3)  # We only have 3 videos

    def test_list_videos_whitespace_in_id_parameter(self):
        """Test handling of whitespace in comma-separated ID parameter."""
        
        result = list_videos(part="snippet", id=" video1 , video2 ")
        
        self.assertEqual(len(result["items"]), 2)
        video_ids = [item["id"] for item in result["items"]]
        self.assertIn("video1", video_ids)
        self.assertIn("video2", video_ids)

if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)