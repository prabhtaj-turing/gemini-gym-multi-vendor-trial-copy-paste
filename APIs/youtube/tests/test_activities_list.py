import pytest
from unittest.mock import patch
from youtube.Activities import list as activities_list
from youtube.SimulationEngine.custom_errors import (
    MissingPartParameterError,
    InvalidMaxResultsError,
    InvalidPartParameterError,
    InvalidActivityFilterError,
)
from youtube.SimulationEngine.db import DB


class TestActivitiesList:
    """Test suite for Activities.list function."""

    def setup_method(self):
        """Set up test data before each test."""
        # Reset DB state
        DB.clear()
        DB.update(
            {
                "activities": [
                    {
                        "kind": "youtube#activity",
                        "etag": "etag1",
                        "id": "activity1",
                        "snippet": {
                            "publishedAt": "2024-03-20T10:00:00Z",
                            "channelId": "channel1",
                            "title": "Test Activity 1",
                            "description": "Description for activity 1",
                            "thumbnails": {
                                "default": {
                                    "url": "https://example.com/thumb1.jpg",
                                    "width": 120,
                                    "height": 90,
                                }
                            },
                            "channelTitle": "Test Channel 1",
                            "type": "upload",
                            "groupId": "group1",
                            "regionCode": "US",
                        },
                        "contentDetails": {"upload": {"videoId": "video1"}},
                        "mine": True,
                    },
                    {
                        "kind": "youtube#activity",
                        "etag": "etag2",
                        "id": "activity2",
                        "snippet": {
                            "publishedAt": "2024-03-21T15:30:00Z",
                            "channelId": "channel2",
                            "title": "Test Activity 2",
                            "description": "Description for activity 2",
                            "thumbnails": {
                                "default": {
                                    "url": "https://example.com/thumb2.jpg",
                                    "width": 120,
                                    "height": 90,
                                }
                            },
                            "channelTitle": "Test Channel 2",
                            "type": "like",
                            "groupId": "group2",
                            "regionCode": "CA",
                        },
                        "contentDetails": {
                            "like": {
                                "resourceId": {
                                    "kind": "youtube#video",
                                    "videoId": "video2",
                                }
                            }
                        },
                        "mine": False,
                    },
                    {
                        "kind": "youtube#activity",
                        "etag": "etag3",
                        "id": "activity3",
                        "snippet": {
                            "publishedAt": "2024-03-19T08:00:00Z",
                            "channelId": "channel3",
                            "title": "Test Activity 3",
                            "description": "Description for activity 3",
                            "thumbnails": {},
                            "channelTitle": "Test Channel 3",
                            "type": "comment",
                            "groupId": "group3",
                            "regionCode": "UK",
                        },
                        "contentDetails": {
                            "comment": {
                                "resourceId": {
                                    "kind": "youtube#video",
                                    "videoId": "video3",
                                }
                            }
                        },
                        "mine": True,
                    },
                ]
            }
        )

    def test_basic_functionality(self):
        """Test basic functionality with all parts."""
        result = activities_list(part="id,snippet,contentDetails", channelId="channel1")

        assert result["kind"] == "youtube#activityListResponse"
        assert "etag" in result
        assert "items" in result
        assert "pageInfo" in result
        assert len(result["items"]) == 1  # Filtered by channelId

        # Check that all parts are included
        for item in result["items"]:
            assert "id" in item
            assert "snippet" in item
            assert "contentDetails" in item
            assert item["kind"] == "youtube#activity"
            assert "etag" in item

    def test_part_parameter_id_only(self):
        """Test that only id is returned when part='id'."""
        result = activities_list(part="id", mine=True)

        assert len(result["items"]) == 2
        for item in result["items"]:
            assert "id" in item
            assert "snippet" not in item
            assert "contentDetails" not in item
            assert item["kind"] == "youtube#activity"  # Always included
            assert "etag" in item  # Always included

    def test_part_parameter_snippet_only(self):
        """Test that only snippet is returned when part='snippet'."""
        result = activities_list(part="snippet", mine=True)

        assert len(result["items"]) == 2
        for item in result["items"]:
            assert "id" not in item
            assert "snippet" in item
            assert "contentDetails" not in item
            assert item["kind"] == "youtube#activity"  # Always included
            assert "etag" in item  # Always included

            # Check snippet structure
            snippet = item["snippet"]
            assert "publishedAt" in snippet
            assert "channelId" in snippet
            assert "title" in snippet
            assert "description" in snippet
            assert "thumbnails" in snippet
            assert "channelTitle" in snippet
            assert "type" in snippet
            assert "groupId" in snippet

    def test_part_parameter_content_details_only(self):
        """Test that only contentDetails is returned when part='contentDetails'."""
        result = activities_list(part="contentDetails", mine=True)

        assert len(result["items"]) == 2
        for item in result["items"]:
            assert "id" not in item
            assert "snippet" not in item
            assert "contentDetails" in item
            assert item["kind"] == "youtube#activity"  # Always included
            assert "etag" in item  # Always included

    def test_part_parameter_multiple_parts(self):
        """Test that multiple parts work correctly."""
        result = activities_list(part="id,snippet", mine=True)

        assert len(result["items"]) == 2
        for item in result["items"]:
            assert "id" in item
            assert "snippet" in item
            assert "contentDetails" not in item
            assert item["kind"] == "youtube#activity"
            assert "etag" in item

    def test_part_parameter_with_spaces(self):
        """Test that part parameter handles spaces correctly."""
        result = activities_list(part="id, snippet, contentDetails", mine=True)

        assert len(result["items"]) == 2
        for item in result["items"]:
            assert "id" in item
            assert "snippet" in item
            assert "contentDetails" in item

    def test_missing_part_parameter(self):
        """Test that missing part parameter raises MissingPartParameterError."""
        with pytest.raises(MissingPartParameterError) as exc_info:
            activities_list(part="", mine=True)
        assert "Parameter 'part' is required and cannot be empty." in str(
            exc_info.value
        )

    def test_none_part_parameter(self):
        """Test that None part parameter raises MissingPartParameterError."""
        with pytest.raises(MissingPartParameterError) as exc_info:
            activities_list(part=None, mine=True)  # type: ignore
        assert "Parameter 'part' is required and cannot be empty." in str(
            exc_info.value
        )

    def test_invalid_part_parameter(self):
        """Test that invalid part parameter raises InvalidPartParameterError."""
        with pytest.raises(InvalidPartParameterError) as exc_info:
            activities_list(part="invalid", mine=True)
        assert "Invalid part parameter values: invalid" in str(exc_info.value)
        assert "Valid values are: id, snippet, contentDetails" in str(exc_info.value)

    def test_invalid_filter_parameter(self):
        """Test that providing no filters or multiple filters raises an error."""
        # Test with no filters
        with pytest.raises(InvalidActivityFilterError) as exc_info_none:
            activities_list(part="id")
        assert "Exactly one of 'channelId' or 'mine' must be provided." in str(
            exc_info_none.value
        )

        # Test with multiple filters
        with pytest.raises(InvalidActivityFilterError) as exc_info_both:
            activities_list(part="id", channelId="some_channel", mine=True)
        assert "Exactly one of 'channelId' or 'mine' must be provided." in str(
            exc_info_both.value
        )

    def test_mixed_valid_invalid_parts(self):
        """Test that mixed valid and invalid parts raises InvalidPartParameterError."""
        with pytest.raises(InvalidPartParameterError) as exc_info:
            activities_list(part="id,invalid,snippet", mine=True)
        assert "Invalid part parameter values: invalid" in str(exc_info.value)

    def test_empty_part_components(self):
        """Test that empty part components raise InvalidPartParameterError."""
        with pytest.raises(InvalidPartParameterError) as exc_info:
            activities_list(part=",,,", mine=True)
        assert (
            "Parameter 'part' cannot be empty or consist only of whitespace and commas."
            in str(exc_info.value)
        )

    def test_whitespace_only_part(self):
        """Test that whitespace-only part parameter raises InvalidPartParameterError."""
        with pytest.raises(InvalidPartParameterError) as exc_info:
            activities_list(part="   ", mine=True)
        assert (
            "Parameter 'part' cannot be empty or consist only of whitespace and commas."
            in str(exc_info.value)
        )

    def test_part_parameter_type_validation(self):
        """Test that non-string part parameter raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            activities_list(part=123, mine=True)  # type: ignore
        assert "Parameter 'part' must be a string." in str(exc_info.value)

    def test_channel_id_filter_with_parts(self):
        """Test channelId filter works correctly with part parameter."""
        result = activities_list(part="id,snippet", channelId="channel1")

        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == "activity1"
        assert result["items"][0]["snippet"]["channelId"] == "channel1"

    def test_max_results_with_parts(self):
        """Test maxResults parameter works correctly with part parameter."""
        result = activities_list(part="id", maxResults=2, mine=True)

        assert len(result["items"]) == 2
        assert result["pageInfo"]["resultsPerPage"] == 2
        assert result["pageInfo"]["totalResults"] == 2

    def test_pagination_with_parts(self):
        """Test pagination works correctly with part parameter."""
        # First page
        result = activities_list(part="id", maxResults=1, mine=True)
        assert len(result["items"]) == 1
        assert "nextPageToken" in result
        assert "prevPageToken" not in result

        # Second page
        result = activities_list(
            part="id", maxResults=1, pageToken=result["nextPageToken"], mine=True
        )
        assert len(result["items"]) == 1
        assert "prevPageToken" in result
        assert "nextPageToken" not in result  # There are only 2 'mine=True' items

    def test_empty_activities_db(self):
        """Test behavior when activities list is empty."""
        DB["activities"] = []
        result = activities_list(part="id", mine=True)

        assert result["kind"] == "youtube#activityListResponse"
        assert result["items"] == []
        assert result["pageInfo"]["totalResults"] == 0
        assert result["pageInfo"]["resultsPerPage"] == 0

    def test_missing_activities_key(self):
        """Test behavior when activities key is missing from DB."""
        del DB["activities"]
        result = activities_list(part="id", mine=True)

        assert result["kind"] == "youtube#activityListResponse"
        assert result["items"] == []
        assert result["pageInfo"]["totalResults"] == 0
        assert result["pageInfo"]["resultsPerPage"] == 0

    def test_response_structure(self):
        """Test that response has correct structure."""
        result = activities_list(part="id", mine=True)

        # Check top-level structure
        assert isinstance(result, dict)
        assert result["kind"] == "youtube#activityListResponse"
        assert "etag" in result
        assert "items" in result
        assert "pageInfo" in result

        # Check pageInfo structure
        page_info = result["pageInfo"]
        assert "totalResults" in page_info
        assert "resultsPerPage" in page_info
        assert isinstance(page_info["totalResults"], int)
        assert isinstance(page_info["resultsPerPage"], int)

        # Check items structure
        assert isinstance(result["items"], list)
        for item in result["items"]:
            assert isinstance(item, dict)
            assert item["kind"] == "youtube#activity"
            assert "etag" in item

    def test_invalid_max_results_error(self):
        """Test that invalid maxResults raises InvalidMaxResultsError."""
        with pytest.raises(InvalidMaxResultsError):
            activities_list(part="id", maxResults=0, mine=True)

        with pytest.raises(InvalidMaxResultsError):
            activities_list(part="id", maxResults=51, mine=True)

    def test_type_validation_errors(self):
        """Test comprehensive type validation for all parameters."""
        # Test channelId type validation
        with pytest.raises(TypeError) as exc_info:
            activities_list(part="id", channelId=123)  # type: ignore
        assert "Parameter 'channelId' must be a string if provided." in str(
            exc_info.value
        )

        # Test mine type validation
        with pytest.raises(TypeError) as exc_info:
            activities_list(part="id", mine="true")  # type: ignore
        assert "Parameter 'mine' must be a boolean if provided." in str(exc_info.value)

        # Test pageToken type validation
        with pytest.raises(TypeError) as exc_info:
            activities_list(part="id", pageToken=123, mine=True)  # type: ignore
        assert "Parameter 'pageToken' must be a string if provided." in str(
            exc_info.value
        )

        # Test publishedAfter type validation
        with pytest.raises(TypeError) as exc_info:
            activities_list(part="id", publishedAfter=123, mine=True)  # type: ignore
        assert "Parameter 'publishedAfter' must be a string if provided." in str(
            exc_info.value
        )

        # Test publishedBefore type validation
        with pytest.raises(TypeError) as exc_info:
            activities_list(part="id", publishedBefore=123, mine=True)  # type: ignore
        assert "Parameter 'publishedBefore' must be a string if provided." in str(
            exc_info.value
        )

        # Test regionCode type validation
        with pytest.raises(TypeError) as exc_info:
            activities_list(part="id", regionCode=123, mine=True)  # type: ignore
        assert "Parameter 'regionCode' must be a string if provided." in str(
            exc_info.value
        )

        # Test maxResults type validation
        with pytest.raises(TypeError) as exc_info:
            activities_list(part="id", maxResults="5", mine=True)  # type: ignore
        assert "Parameter 'maxResults' must be an integer if provided." in str(
            exc_info.value
        )

    def test_published_date_filters_with_parts(self):
        """Test publishedAfter and publishedBefore filters work correctly."""
        # Test publishedAfter filter
        result = activities_list(
            part="id,snippet", publishedAfter="2024-03-20T00:00:00Z", mine=True
        )
        assert len(result["items"]) == 1  # only activity1 (mine=True)

        # Test publishedBefore filter - should only include activity3 (2024-03-19)
        result = activities_list(
            part="id,snippet", publishedBefore="2024-03-20T00:00:00Z", mine=True
        )
        assert len(result["items"]) == 1  # only activity3
        assert result["items"][0]["id"] == "activity3"

        # Test publishedBefore with a later date to include activity1 as well
        result = activities_list(
            part="id,snippet", publishedBefore="2024-03-20T12:00:00Z", mine=True
        )
        assert len(result["items"]) == 2  # activity1 and activity3

    def test_default_max_results(self):
        """Test that default maxResults is applied when not specified."""
        result = activities_list(part="id", mine=True)
        # Should return all 2 'mine=True' activities since default is 5
        assert len(result["items"]) == 2
        assert result["pageInfo"]["resultsPerPage"] == 2

    def test_mine_filter_true(self):
        """Test mine=True filter returns only user's activities."""
        result = activities_list(part="id,snippet", mine=True)
        assert len(result["items"]) == 2  # activity1 and activity3 have mine=True
        for item in result["items"]:
            assert item["id"] in ["activity1", "activity3"]

    def test_mine_filter_false(self):
        """Test mine=False filter returns only non-user activities."""
        result = activities_list(part="id,snippet", mine=False)
        assert len(result["items"]) == 1  # only activity2 has mine=False
        assert result["items"][0]["id"] == "activity2"

    def test_region_code_filter(self):
        """Test regionCode filter works correctly."""
        result = activities_list(part="id,snippet", regionCode="US", channelId="channel1")
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == "activity1"

        result = activities_list(part="id,snippet", regionCode="CA", channelId="channel2")
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == "activity2"

        # Test non-existent region
        result = activities_list(part="id,snippet", regionCode="XX", channelId="channel1")
        assert len(result["items"]) == 0

    def test_invalid_page_token_handling(self):
        """Test that invalid pageToken is handled gracefully."""
        result = activities_list(part="id", pageToken="invalid", mine=True)
        # Should start from beginning when pageToken is invalid
        assert len(result["items"]) == 2

    def test_non_dict_activities_handling(self):
        """Test handling of non-dict items in activities list."""
        # Add some non-dict items to test robustness
        DB["activities"].extend(["not_a_dict", 123, None])
        result = activities_list(part="id", mine=True)
        # Should still return only the valid dict activities
        assert len(result["items"]) == 2

    def test_activities_without_snippet_or_content_details(self):
        """Test handling of activities missing snippet or contentDetails."""
        DB["activities"] = [
            {
                "kind": "youtube#activity",
                "etag": "etag_minimal",
                "id": "minimal_activity",
                "mine": True
                # Missing snippet and contentDetails
            }
        ]
        result = activities_list(part="id,snippet,contentDetails", mine=True)
        assert len(result["items"]) == 1
        item = result["items"][0]
        assert item["id"] == "minimal_activity"
        assert "snippet" in item
        assert "contentDetails" in item
        # Should have empty/default values for missing fields
        assert item["snippet"]["publishedAt"] == ""
        assert item["snippet"]["channelId"] == ""

    def test_pagination_edge_cases(self):
        """Test pagination edge cases and token generation."""
        # Test when pageToken points to exact end
        result = activities_list(part="id", maxResults=3, pageToken="3", mine=True)
        assert len(result["items"]) == 0
        assert "nextPageToken" not in result

        # Test prevPageToken generation
        result = activities_list(part="id", maxResults=2, pageToken="2", mine=True)
        assert len(result["items"]) == 0
        assert "prevPageToken" in result
        assert result["prevPageToken"] == "0"

    def test_combined_filters(self):
        """Test multiple filters working together."""
        result = activities_list(
            part="id,snippet",
            channelId="channel1",
            publishedAfter="2024-03-19T00:00:00Z",
            maxResults=1,
        )
        assert len(result["items"]) == 1
        assert result["items"][0]["id"] == "activity1"
        assert result["items"][0]["snippet"]["channelId"] == "channel1"
