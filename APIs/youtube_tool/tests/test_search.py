"""
Test cases for the Search module in YouTube Tool API simulation.

This module contains comprehensive tests for the search functionality
that uses Gemini AI to search for YouTube content.
"""

import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube_tool.youtube_search import search
from youtube_tool.SimulationEngine import custom_errors
import os
import pytest

SHOULD_SKIP = (os.environ.get("GOOGLE_API_KEY") is None and os.environ.get("GEMINI_API_KEY") is None) or os.environ.get("LIVE_API_URL") is None 

@pytest.mark.skipif(SHOULD_SKIP, reason="YouTube tests are disabled via environment variable")
class TestYouTubeToolSearch(BaseTestCaseWithErrorHandler):
    """Test cases for the YouTube Tool search function."""

    # ============================================================================
    # INPUT VALIDATION TESTS
    # ============================================================================

    def test_search_success_basic(self):
        """Test basic successful search with required parameters."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Sample YouTube search results for Python tutorial"
            expected_results = [
                {"title": "Python Tutorial", "url": "https://youtube.com/watch?v=abc", "like_count": 100, "view_count": 1000, "video_length": "10:30"},
                {"title": "Learn Python", "url": "https://youtube.com/watch?v=def", "like_count": 200, "view_count": 2000, "video_length": "15:45"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("Python tutorial")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, expected_results)
            mock_gemini.assert_called_once()
            mock_extract.assert_called_once()

    def test_search_success_default_result_type(self):
        """Test successful search with default result_type (VIDEO)."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "YouTube videos for JavaScript"
            expected_results = [
                {"title": "JavaScript Basics", "url": "https://youtube.com/watch?v=123", "like_count": 150, "view_count": 1500, "video_length": "12:00"},
                {"title": "Advanced JavaScript", "url": "https://youtube.com/watch?v=456", "like_count": 300, "view_count": 3000, "video_length": "20:15"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("JavaScript")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, expected_results)
            mock_gemini.assert_called_once()
            mock_extract.assert_called_once()
            
            # Check that the call includes "videos" for default VIDEO type
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("videos", call_args)

    def test_search_success_with_result_type_video(self):
        """Test successful search with result_type VIDEO."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "YouTube videos for React tutorial"
            expected_results = [
                {"title": "React Tutorial", "url": "https://youtube.com/watch?v=react1", "like_count": 250, "view_count": 2500, "video_length": "18:30"},
                {"title": "React Hooks", "url": "https://youtube.com/watch?v=react2", "like_count": 400, "view_count": 4000, "video_length": "25:45"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("React tutorial", result_type="VIDEO")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, expected_results)
            mock_gemini.assert_called_once()
            mock_extract.assert_called_once()
            
            # Check that the call includes "videos" when result_type is VIDEO
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("videos", call_args)

    def test_search_success_with_result_type_channel(self):
        """Test successful search with result_type CHANNEL."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "YouTube channels for programming"
            expected_results = [
                {"channel_name": "Programming Hub", "url": "https://youtube.com/c/programming1", "channel_avatar_url": "https://avatar1.jpg", "external_channel_id": "UC123", "snippets": "Great programming content"},
                {"channel_name": "Code Academy", "url": "https://youtube.com/c/programming2", "channel_avatar_url": "https://avatar2.jpg", "external_channel_id": "UC456", "snippets": "Learn to code"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("programming", result_type="CHANNEL")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, expected_results)
            mock_gemini.assert_called_once()
            mock_extract.assert_called_once()
            
            # Check that the call includes "channels" when result_type is CHANNEL
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("channels", call_args)

    def test_search_success_with_result_type_playlist(self):
        """Test successful search with result_type PLAYLIST."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "YouTube playlists for data science"
            expected_results = [
                {"playlist_name": "Data Science Course", "url": "https://youtube.com/playlist?list=123", "channel_name": "Data Expert", "external_playlist_id": "PL123", "playlist_video_ids": ["vid1", "vid2"], "snippets": "Complete data science course"},
                {"playlist_name": "ML Fundamentals", "url": "https://youtube.com/playlist?list=456", "channel_name": "AI Teacher", "external_playlist_id": "PL456", "playlist_video_ids": ["vid3", "vid4"], "snippets": "Machine learning basics"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("data science", result_type="PLAYLIST")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, expected_results)
            mock_gemini.assert_called_once()
            mock_extract.assert_called_once()
            
            # Check that the call includes "playlists" when result_type is PLAYLIST
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("playlists", call_args)

    def test_search_none_query(self):
        """Test search with None query."""
        self.assert_error_behavior(
            search,
            ValueError,
            "query is required.",
            query=None
        )

    def test_search_empty_query(self):
        """Test search with empty query."""
        self.assert_error_behavior(
            search,
            ValueError,
            "query cannot be empty.",
            query=""
        )

    def test_search_whitespace_only_query(self):
        """Test search with whitespace-only query."""
        self.assert_error_behavior(
            search,
            ValueError,
            "query cannot be empty.",
            query="   "
        )

    def test_search_invalid_query_type(self):
        """Test search with invalid query type."""
        self.assert_error_behavior(
            search,
            TypeError,
            "query must be a string.",
            query=123
        )

    def test_search_invalid_result_type_value(self):
        """Test search with invalid result_type value."""
        self.assert_error_behavior(
            search,
            ValueError,
            "result_type must be one of: VIDEO, CHANNEL, PLAYLIST.",
            query="test",
            result_type="INVALID"
        )

    def test_search_invalid_result_type_type(self):
        """Test search with invalid result_type type."""
        self.assert_error_behavior(
            search,
            TypeError,
            "result_type must be a string.",
            query="test",
            result_type=123
        )

    def test_search_case_sensitive_result_type(self):
        """Test that result_type is case sensitive (should be uppercase)."""
        self.assert_error_behavior(
            search,
            ValueError,
            "result_type must be one of: VIDEO, CHANNEL, PLAYLIST.",
            query="test",
            result_type="video"  # lowercase should fail
        )

    # ============================================================================
    # GEMINI RESPONSE TESTS
    # ============================================================================

    def test_search_gemini_response_structure(self):
        """Test that search properly handles Gemini response and extraction."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            raw_response = "1. Python Tutorial - https://youtube.com/watch?v=abc123\n2. Learn Python - https://youtube.com/watch?v=def456"
            mock_gemini.return_value = raw_response
            expected_results = [
                {"title": "Python Tutorial", "url": "https://youtube.com/watch?v=abc123", "like_count": 100, "view_count": 1000, "video_length": "10:30"},
                {"title": "Learn Python", "url": "https://youtube.com/watch?v=def456", "like_count": 200, "view_count": 2000, "video_length": "15:45"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("Python tutorial")
            
            self.assertEqual(result, expected_results)
            mock_gemini.assert_called_once()
            mock_extract.assert_called_once_with(raw_response)

    def test_search_gemini_call_format(self):
        """Test that the Gemini API call is formatted correctly."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "YouTube search results"
            expected_results = [{"title": "AI Video", "url": "https://youtube.com/watch?v=ai1", "like_count": 100, "view_count": 1000, "video_length": "10:30"}]
            mock_extract.return_value = expected_results
            
            result = search("artificial intelligence", result_type="VIDEO")
            
            self.assertEqual(result, expected_results)
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args[0][0]
            
            # Check that the prompt is properly formatted
            self.assertIn("Use @YouTube to search exactly this query", call_args)
            self.assertIn("artificial intelligence", call_args)
            self.assertIn("videos", call_args)
            self.assertIn("do not alter it", call_args)

    def test_search_preserves_query_exactly(self):
        """Test that the search query is passed to Gemini exactly as provided."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Search results"
            expected_results = [{"title": "Advanced Python", "url": "https://youtube.com/watch?v=adv1", "like_count": 100, "view_count": 1000, "video_length": "10:30"}]
            mock_extract.return_value = expected_results
            
            special_query = "Python 3.9+ tutorial: advanced features & best practices"
            result = search(special_query)
            
            self.assertEqual(result, expected_results)
            call_args = mock_gemini.call_args[0][0]
            self.assertIn(special_query, call_args)

    def test_search_different_result_types_formatting(self):
        """Test that different result types are properly formatted in the Gemini call."""
        test_cases = [
            ("VIDEO", "videos"),
            ("CHANNEL", "channels"), 
            ("PLAYLIST", "playlists")
        ]
        
        for input_type, expected_type in test_cases:
            with self.subTest(result_type=input_type):
                with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
                     patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
                    mock_gemini.return_value = "Results"
                    expected_results = [{"title": "Test Item", "url": "https://youtube.com/test"}]
                    mock_extract.return_value = expected_results
                    
                    result = search("test query", result_type=input_type)
                    
                    self.assertEqual(result, expected_results)
                    call_args = mock_gemini.call_args[0][0]
                    self.assertIn(expected_type, call_args)

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================

    def test_search_gemini_response_none(self):
        """Test handling when Gemini returns None."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            mock_gemini.return_value = None
            
            self.assert_error_behavior(
                search,
                custom_errors.APIError,
                "Failed to get search result.",
                query="test query"
            )

    def test_search_extraction_failure(self):
        """Test handling when get_json_response returns None."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Valid response"
            mock_extract.return_value = None
            
            self.assert_error_behavior(
                search,
                custom_errors.ExtractionError,
                "Failed to extract results.",
                query="test query"
            )

    def test_search_gemini_http_error(self):
        """Test handling of HTTP errors from Gemini API."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            mock_gemini.side_effect = Exception("HTTP request failed")
            
            with self.assertRaises(Exception) as context:
                search("test query")
            
            self.assertIn("HTTP request failed", str(context.exception))

    def test_search_gemini_json_decode_error(self):
        """Test handling of JSON decode errors from Gemini API."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            mock_gemini.side_effect = Exception("JSON decode error")
            
            with self.assertRaises(Exception) as context:
                search("test query")
            
            self.assertIn("JSON decode error", str(context.exception))

    # ============================================================================
    # QUERY CONTENT TESTS
    # ============================================================================

    def test_search_handles_special_characters(self):
        """Test that search handles special characters in queries."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results for special characters"
            mock_extract.return_value = [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}]
            
            result = search("C++ programming & algorithms")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}])
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("C++ programming & algorithms", call_args)

    def test_search_handles_unicode_characters(self):
        """Test that search handles unicode characters in queries."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results for unicode query"
            mock_extract.return_value = [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}]
            
            result = search("Python tutorial 🐍")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}])
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("Python tutorial 🐍", call_args)

    def test_search_handles_long_queries(self):
        """Test that search handles very long queries."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results for long query"
            mock_extract.return_value = [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}]
            
            long_query = "machine learning deep learning artificial intelligence neural networks tensorflow pytorch keras scikit-learn pandas numpy matplotlib"
            result = search(long_query)
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}])
            call_args = mock_gemini.call_args[0][0]
            self.assertIn(long_query, call_args)

    def test_search_handles_numeric_queries(self):
        """Test that search handles queries with numbers."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results for numeric query"
            mock_extract.return_value = [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}]
            
            result = search("Python 3.9 tutorial 2024")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}])
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("Python 3.9 tutorial 2024", call_args)

    def test_search_handles_punctuation(self):
        """Test that search handles queries with punctuation."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results for punctuation query"
            mock_extract.return_value = [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}]
            
            result = search("What is machine learning? A beginner's guide!")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}])
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("What is machine learning? A beginner's guide!", call_args)

    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================

    def test_search_full_workflow_video(self):
        """Test complete search workflow for video content."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            raw_response = """1. Python Tutorial for Beginners - https://youtube.com/watch?v=abc123
2. Learn Python Programming - https://youtube.com/watch?v=def456
3. Python Crash Course - https://youtube.com/watch?v=ghi789"""
            mock_gemini.return_value = raw_response
            expected_results = [
                {"title": "Python Tutorial for Beginners", "url": "https://youtube.com/watch?v=abc123", "like_count": 100, "view_count": 1000, "video_length": "10:30"},
                {"title": "Learn Python Programming", "url": "https://youtube.com/watch?v=def456", "like_count": 200, "view_count": 2000, "video_length": "15:45"},
                {"title": "Python Crash Course", "url": "https://youtube.com/watch?v=ghi789", "like_count": 300, "view_count": 3000, "video_length": "20:15"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("Python tutorial", result_type="VIDEO")
            
            self.assertEqual(result, expected_results)
            
            # Verify the call was made with correct parameters
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("Use @YouTube to search exactly this query", call_args)
            self.assertIn("Python tutorial", call_args)
            self.assertIn("videos", call_args)

    def test_search_full_workflow_channel(self):
        """Test complete search workflow for channel content."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            raw_response = """1. Corey Schafer - https://youtube.com/c/CoreySchafer
2. Programming with Mosh - https://youtube.com/c/programmingwithmosh
3. Tech With Tim - https://youtube.com/c/TechWithTim"""
            mock_gemini.return_value = raw_response
            expected_results = [
                {"channel_name": "Corey Schafer", "url": "https://youtube.com/c/CoreySchafer", "channel_avatar_url": "https://avatar1.jpg", "external_channel_id": "UC1", "snippets": "Python tutorials"},
                {"channel_name": "Programming with Mosh", "url": "https://youtube.com/c/programmingwithmosh", "channel_avatar_url": "https://avatar2.jpg", "external_channel_id": "UC2", "snippets": "Programming courses"},
                {"channel_name": "Tech With Tim", "url": "https://youtube.com/c/TechWithTim", "channel_avatar_url": "https://avatar3.jpg", "external_channel_id": "UC3", "snippets": "Tech tutorials"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("programming tutorials", result_type="CHANNEL")
            
            self.assertEqual(result, expected_results)
            
            # Verify the call was made with correct parameters
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("programming tutorials", call_args)
            self.assertIn("channels", call_args)

    def test_search_full_workflow_playlist(self):
        """Test complete search workflow for playlist content."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            raw_response = """1. Complete Python Course - https://youtube.com/playlist?list=abc123
2. Python for Beginners - https://youtube.com/playlist?list=def456"""
            mock_gemini.return_value = raw_response
            expected_results = [
                {"playlist_name": "Complete Python Course", "url": "https://youtube.com/playlist?list=abc123", "channel_name": "Python Academy", "external_playlist_id": "PL123", "playlist_video_ids": ["vid1", "vid2"], "snippets": "Complete Python course"},
                {"playlist_name": "Python for Beginners", "url": "https://youtube.com/playlist?list=def456", "channel_name": "Beginner Coder", "external_playlist_id": "PL456", "playlist_video_ids": ["vid3", "vid4"], "snippets": "Python basics"}
            ]
            mock_extract.return_value = expected_results
            
            result = search("Python course", result_type="PLAYLIST")
            
            self.assertEqual(result, expected_results)
            
            # Verify the call was made with correct parameters
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("Python course", call_args)
            self.assertIn("playlists", call_args)

    # ============================================================================
    # EDGE CASES AND BOUNDARY TESTS
    # ============================================================================

    def test_search_single_character_query(self):
        """Test search with single character query."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results for single character"
            expected_results = [{"title": "R Programming", "url": "https://youtube.com/watch?v=r1", "like_count": 50, "view_count": 500, "video_length": "5:30"}]
            mock_extract.return_value = expected_results
            
            result = search("R")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, expected_results)

    def test_search_whitespace_stripped(self):
        """Test that leading/trailing whitespace is handled."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results"
            expected_results = [{"title": "Python Tutorial", "url": "https://youtube.com/watch?v=py1", "like_count": 100, "view_count": 1000, "video_length": "10:30"}]
            mock_extract.return_value = expected_results
            
            result = search("  Python tutorial  ")
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, expected_results)
            # The query should still be passed with whitespace to Gemini
            call_args = mock_gemini.call_args[0][0]
            self.assertIn("  Python tutorial  ", call_args)

    def test_search_empty_response_from_gemini(self):
        """Test handling of empty response from Gemini."""
        # Test case 1: Gemini returns empty string, get_json_response returns None
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = ""
            mock_extract.return_value = None
                        
            self.assert_error_behavior(search, custom_errors.ExtractionError, 
                "Failed to extract results.", query="test query")

        # Test case 2: Gemini returns empty string, get_json_response returns empty dict
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = ""
            mock_extract.return_value = []
                        
            self.assert_error_behavior(search, custom_errors.ExtractionError, 
                "Failed to extract results.", query="test query")

        # Test case 3: Gemini returns None
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = None
            
            self.assert_error_behavior(search, custom_errors.APIError, 
                "Failed to get search result.", query="test query")

    def test_search_multiple_calls_independence(self):
        """Test that multiple search calls are independent."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.side_effect = ["Raw result 1", "Raw result 2", "Raw result 3"]
            result1_data = [{"title": "Video 1", "url": "https://youtube.com/watch?v=1", "like_count": 10, "view_count": 100, "video_length": "5:00"}]
            result2_data = [{"title": "Video 2", "url": "https://youtube.com/watch?v=2", "like_count": 20, "view_count": 200, "video_length": "6:00"}]
            result3_data = [{"channel_name": "Channel 3", "url": "https://youtube.com/c/channel3", "channel_avatar_url": "https://avatar3.jpg", "external_channel_id": "UC3", "snippets": "Test channel"}]
            mock_extract.side_effect = [result1_data, result2_data, result3_data]
            
            result1 = search("query 1")
            result2 = search("query 2", result_type="VIDEO")
            result3 = search("query 3", result_type="CHANNEL")
            
            self.assertEqual(result1, result1_data)
            self.assertEqual(result2, result2_data)
            self.assertEqual(result3, result3_data)
            self.assertEqual(mock_gemini.call_count, 3)

    # ============================================================================
    # MOCK VERIFICATION TESTS
    # ============================================================================

    def test_search_gemini_called_with_correct_format(self):
        """Test that Gemini is called with the exact expected format."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Test response"
            expected_results = [{"title": "ML Video", "url": "https://youtube.com/watch?v=ml1", "like_count": 100, "view_count": 1000, "video_length": "10:30"}]
            mock_extract.return_value = expected_results
            
            result = search("machine learning", result_type="VIDEO")
            
            self.assertEqual(result, expected_results)
            mock_gemini.assert_called_once()
            call_args = mock_gemini.call_args[0][0]
            
            # Check all required components are in the prompt
            self.assertIn("Use @YouTube to search exactly this query", call_args)
            self.assertIn("videos only", call_args)
            self.assertIn("do not alter it: 'machine learning'", call_args)

    def test_search_gemini_not_called_on_validation_error(self):
        """Test that Gemini is not called when validation fails."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            mock_gemini.return_value = "Should not be called"
            
            with self.assertRaises(ValueError):
                search("")  # Empty query should fail validation
            
            mock_gemini.assert_not_called()

    def test_search_gemini_called_exactly_once(self):
        """Test that Gemini is called exactly once per search."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Single call response"
            expected_results = [{"title": "Test Video", "url": "https://youtube.com/watch?v=test", "like_count": 100, "view_count": 1000, "video_length": "10:30"}]
            mock_extract.return_value = expected_results
            
            result = search("test query")
            
            self.assertEqual(result, expected_results)
            self.assertEqual(mock_gemini.call_count, 1)

    # ============================================================================
    # PARAMETER VALIDATION EDGE CASES
    # ============================================================================

    def test_search_result_type_case_variations(self):
        """Test various case combinations for result_type (should all fail except exact uppercase)."""
        invalid_cases = ["Video", "video", "VIDEO ", " VIDEO", "Channel", "channel", "Playlist", "playlist"]
        
        for invalid_case in invalid_cases:
            with self.subTest(result_type=invalid_case):
                self.assert_error_behavior(
                    search,
                    ValueError,
                    "result_type must be one of: VIDEO, CHANNEL, PLAYLIST.",
                    query="test",
                    result_type=invalid_case
                )

    def test_search_query_with_newlines(self):
        """Test search with newline characters in query."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results with newlines"
            mock_extract.return_value = [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}]
            
            query_with_newlines = "Python tutorial\nfor beginners"
            result = search(query_with_newlines)
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}])
            call_args = mock_gemini.call_args[0][0]
            self.assertIn(query_with_newlines, call_args)

    def test_search_query_with_tabs(self):
        """Test search with tab characters in query."""
        with patch('youtube_tool.SimulationEngine.utils.get_gemini_response') as mock_gemini, \
             patch('youtube_tool.SimulationEngine.utils.get_json_response') as mock_extract:
            mock_gemini.return_value = "Results with tabs"
            mock_extract.return_value = [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}]
            
            query_with_tabs = "Python\ttutorial\tfor\tbeginners"
            result = search(query_with_tabs)
            
            self.assertIsInstance(result, list)
            self.assertEqual(result, [{"title": "video1", "url": "https://youtube.com/watch?v=test1"}])
            call_args = mock_gemini.call_args[0][0]
            self.assertIn(query_with_tabs, call_args)

    def test_search_query_with_videos(self):
        """Test search with videos in query."""
        results = search("cats","VIDEO")
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, Dict)
            self.assertIn("like_count", result)
            self.assertIn("url", result)
            self.assertIn("video_length", result)
            self.assertIn("view_count", result)
            self.assertIn("title", result)

    def test_search_query_with_channels(self):
        """Test search with channels in query."""
        results = search("cats","CHANNEL")
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, Dict)
            self.assertIn("channel_name", result)
            self.assertIn("url", result)

    def test_search_query_with_playlists(self):
        """Test search with playlists in query."""
        results = search("cats","PLAYLIST")
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, Dict)
            self.assertIn("url", result)
            self.assertIn("channel_name", result)
            

            


if __name__ == "__main__":
    unittest.main()
