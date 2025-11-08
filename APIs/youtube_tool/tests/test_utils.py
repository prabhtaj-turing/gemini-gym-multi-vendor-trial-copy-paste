import json
import os
import sys
import unittest
import requests
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from youtube_tool.SimulationEngine import utils
from common_utils.base_case import BaseTestCaseWithErrorHandler
from youtube_tool.SimulationEngine.custom_errors import EnvironmentError

class TestYouTubeToolUtils(BaseTestCaseWithErrorHandler):
    """Test cases for the YouTube Tool utility functions."""
    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        utils.DB = {}
    
    def test_get_json_response_returns_correct_list(self):
        """Test that get_json_response returns a list."""
            
        gemini_output = {
                            "codeOutputState": {
                                "executionTrace": {
                                    "executions": [
                                        {
                                            "jsonOutput": "[{\"title\": \"Test Video\", \"url\": \"https://youtube.com/watch?v=test_video_id\", \"channel_name\": \"Test Channel\", \"view_count\": 1000}]"
                                        }
                                    ]
                                }
                            }
                        }
                                                    
        results = utils.get_json_response(gemini_output)
        self.assertIsInstance(results, list)
        self.assertEqual(results, [{"title": "Test Video", "url": "https://youtube.com/watch?v=test_video_id", "channel_name": "Test Channel", "view_count": 1000}])


    def test_get_json_response_returns_empty_list(self):
        """Test that get_json_response returns an empty list when there is no jsonOutput."""
            
        gemini_output = {
            "codeOutputState": {
                "executionTrace": {
                    "executions": [
                        {
                            "key": "value"
                        }
                    ]
                }
            }
        }
                                                    
        results = utils.get_json_response(gemini_output)
        self.assertIsInstance(results, list)
        self.assertEqual(results, [])

    def test_get_json_response_incorrect_structure_gemini_output(self):
        """Test that get_json_response returns None when the gemini output has incorrect structure."""
        gemini_output = """
        {
            "key": "value"
        }
        """
        results = utils.get_json_response(gemini_output)
        self.assertIsNone(results)

    def test_get_json_response_returns_none(self):
        """Test that get_json_response returns None when the gemini output is not a valid JSON."""
        gemini_output = []
        results = utils.get_json_response(gemini_output)
        self.assertIsNone(results)

        gemini_output = 123
        results = utils.get_json_response(gemini_output)
        self.assertIsNone(results)

    def test_get_recent_searches(self):
        """Test that get_recent_searches returns the correct list of recent searches."""
        recent_searches = utils.get_recent_searches()
        self.assertIsInstance(recent_searches, list)
        self.assertEqual(recent_searches, [])

    def test_add_recent_search(self):
        """Test that add_recent_search adds the search query to the recent searches list."""
        utils.add_recent_search(endpoint="search", parameters={"query": "test_query", "result_type": "VIDEO"}, result=[{"title": "Test Video", "url": "https://youtube.com/watch?v=test_video_id", "channel_name": "Test Channel", "view_count": 1000}])
        recent_searches = utils.get_recent_searches()
        self.assertEqual(recent_searches, [{"parameters": {"query": "test_query", "result_type": "VIDEO"}, "result": [{"title": "Test Video", "url": "https://youtube.com/watch?v=test_video_id", "channel_name": "Test Channel", "view_count": 1000}]}])

    def test_get_recent_searches_with_max_results(self):
        """Test that get_recent_searches returns the correct list of recent searches with max results."""
        utils.add_recent_search(endpoint="search", parameters={"query": "test_query", "result_type": "VIDEO"}, result=[{"title": "Test Video", "url": "https://youtube.com/watch?v=test_video_id", "channel_name": "Test Channel", "view_count": 1000}])
        utils.add_recent_search(endpoint="search", parameters={"query": "test_query2", "result_type": "VIDEO"}, result=[{"title": "Test Video 2", "url": "https://youtube.com/watch?v=test_video_id_2", "channel_name": "Test Channel 2", "view_count": 2000}])
        utils.add_recent_search(endpoint="search", parameters={"query": "test_query3", "result_type": "VIDEO"}, result=[{"title": "Test Video 3", "url": "https://youtube.com/watch?v=test_video_id_3", "channel_name": "Test Channel 3", "view_count": 3000}])
        recent_searches = utils.get_recent_searches(max_results=2)
        self.assertEqual(recent_searches, [{"parameters": {"query": "test_query3", "result_type": "VIDEO"}, "result": [{"title": "Test Video 3", "url": "https://youtube.com/watch?v=test_video_id_3", "channel_name": "Test Channel 3", "view_count": 3000}]}, {"parameters": {"query": "test_query2", "result_type": "VIDEO"}, "result": [{"title": "Test Video 2", "url": "https://youtube.com/watch?v=test_video_id_2", "channel_name": "Test Channel 2", "view_count": 2000}]}])


class TestUtils(BaseTestCaseWithErrorHandler):
    """Test cases for YouTube Tool utility functions."""
    
    def setUp(self):
        """Set up the test environment."""
        super().setUp()
        utils.DB = {}
        # Reset global variable
        utils.Global_result = None
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_api_key', 'LIVE_API_URL': 'https://api.test.com/'})
    @patch('requests.post')
    def test_get_gemini_response_success(self, mock_post):
        """Test successful Gemini API response."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.json.return_value = {"candidates": [{"content": {"parts": {"text": "response"}}}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = utils.get_gemini_response("test query")
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_gemini_response_missing_api_key(self):
        """Test OSError when API key is missing."""
        with self.assertRaises(OSError) as context:
            utils.get_gemini_response("test query")
        
        self.assertIn("Google API Key not found", str(context.exception))
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_api_key'}, clear=True)
    def test_get_gemini_response_missing_live_api_url(self):
        """Test OSError when LIVE_API_URL is missing."""
        with self.assertRaises(OSError) as context:
            utils.get_gemini_response("test query")
        
        self.assertIn("Live API URL not found", str(context.exception))
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_api_key', 'LIVE_API_URL': 'https://api.test.com/'})
    @patch('requests.post')
    def test_get_gemini_response_request_exception(self, mock_post):
        """Test handling of requests.RequestException."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")
        
        result = utils.get_gemini_response("test query")
        
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_api_key', 'LIVE_API_URL': 'https://api.test.com/'})
    @patch('requests.post')
    def test_get_gemini_response_json_decode_error(self, mock_post):
        """Test handling of JSON decode error."""
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = utils.get_gemini_response("test query")
        
        self.assertIsNone(result)
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_api_key', 'LIVE_API_URL': 'https://api.test.com/'})
    @patch('requests.post')
    def test_get_gemini_response_http_error(self, mock_post):
        """Test handling of HTTP error status codes."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response
        
        result = utils.get_gemini_response("test query")
        
        self.assertIsNone(result)
    
    def test_extract_youtube_results_success(self):
        """Test successful extraction of YouTube results."""
        response = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {},
                            {},
                            {
                                'structuredData': {
                                    'multiStepPlanInfo': {
                                        'multiStepPlan': {
                                            'steps': [
                                                {},
                                                {},
                                                {
                                                    'blocks': [
                                                        {
                                                            'codeOutputState': {
                                                                'executionTrace': {
                                                                    'executions': [
                                                                        {
                                                                            'jsonOutput': '{"videos": [{"title": "Test Video", "id": "123"}]}'
                                                                        }
                                                                    ]
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        result = utils.extract_youtube_results(response)
        expected = {"videos": [{"title": "Test Video", "id": "123"}]}
        self.assertEqual(result, expected)
    
    def test_extract_youtube_results_none_input(self):
        """Test extract_youtube_results with None input."""
        result = utils.extract_youtube_results(None)
        self.assertIsNone(result)
    
    def test_extract_youtube_results_invalid_type(self):
        """Test extract_youtube_results with non-dict input."""
        result = utils.extract_youtube_results("not a dict")
        self.assertIsNone(result)
        
        result = utils.extract_youtube_results([1, 2, 3])
        self.assertIsNone(result)
    
    def test_extract_youtube_results_missing_keys(self):
        """Test extract_youtube_results with missing required keys."""
        incomplete_response = {
            'candidates': [
                {
                    'content': {
                        'parts': [{},{},{}] # Missing the required structure
                    }
                }
            ]
        }
        
        result = utils.extract_youtube_results(incomplete_response)
        self.assertIsNone(result)
    
    def test_extract_youtube_results_invalid_json(self):
        """Test extract_youtube_results with invalid JSON in jsonOutput."""
        response = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {},
                            {},
                            {
                                'structuredData': {
                                    'multiStepPlanInfo': {
                                        'multiStepPlan': {
                                            'steps': [
                                                {},
                                                {},
                                                {
                                                    'blocks': [
                                                        {
                                                            'codeOutputState': {
                                                                'executionTrace': {
                                                                    'executions': [
                                                                        {
                                                                            'jsonOutput': 'invalid json{'
                                                                        }
                                                                    ]
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
        
        result = utils.extract_youtube_results(response)
        self.assertIsNone(result)
    
    def test_find_and_print_executions_with_dict(self):
        """Test find_and_print_executions with dictionary containing executionTrace."""
        test_data = {
            "executionTrace": {
                "executions": [
                    {"jsonOutput": "test output 1"},
                    {"jsonOutput": "test output 2"}
                ]
            }
        }
        
        utils.find_and_print_executions(test_data)
        
        # The function should set Global_result to the JSON representation of the last execution
        expected = json.dumps({"jsonOutput": "test output 2"}, indent=2)
        self.assertEqual(utils.Global_result, expected)
    
    def test_find_and_print_executions_with_nested_dict(self):
        """Test find_and_print_executions with nested dictionary structure."""
        test_data = {
            "outer": {
                "inner": {
                    "executionTrace": {
                        "executions": [
                            {"jsonOutput": "nested output"}
                        ]
                    }
                }
            }
        }
        
        utils.find_and_print_executions(test_data)
        
        expected = json.dumps({"jsonOutput": "nested output"}, indent=2)
        self.assertEqual(utils.Global_result, expected)
    
    def test_find_and_print_executions_with_list(self):
        """Test find_and_print_executions with list containing executionTrace."""
        test_data = [
            {
                "executionTrace": {
                    "executions": [
                        {"jsonOutput": "list output"}
                    ]
                }
            }
        ]
        
        utils.find_and_print_executions(test_data)
        
        expected = json.dumps({"jsonOutput": "list output"}, indent=2)
        self.assertEqual(utils.Global_result, expected)
    
    def test_find_and_print_executions_with_json_string(self):
        """Test find_and_print_executions with JSON string containing executionTrace."""
        embedded_data = {
            "executionTrace": {
                "executions": [
                    {"jsonOutput": "string embedded output"}
                ]
            }
        }
        test_data = json.dumps(embedded_data)
        
        utils.find_and_print_executions(test_data)
        
        expected = json.dumps({"jsonOutput": "string embedded output"}, indent=2)
        self.assertEqual(utils.Global_result, expected)
    
    def test_find_and_print_executions_with_invalid_json_string(self):
        """Test find_and_print_executions with invalid JSON string."""
        test_data = "not valid json{"
        
        # Should not raise an exception and Global_result should remain unchanged
        original_result = utils.Global_result
        utils.find_and_print_executions(test_data)
        self.assertEqual(utils.Global_result, original_result)
    
    def test_find_and_print_executions_with_no_executions(self):
        """Test find_and_print_executions with no executionTrace."""
        test_data = {
            "someOtherKey": "someValue",
            "nested": {
                "moreData": "value"
            }
        }
        
        original_result = utils.Global_result
        utils.find_and_print_executions(test_data)
        self.assertEqual(utils.Global_result, original_result)
    
    def test_find_and_print_executions_with_primitive_types(self):
        """Test find_and_print_executions with primitive types."""
        # Test with integer
        utils.find_and_print_executions(42)
        
        # Test with boolean
        utils.find_and_print_executions(True)
        
        # Test with None
        utils.find_and_print_executions(None)
        
        # Should not raise exceptions
        self.assertTrue(True)  # If we reach here, no exceptions were raised
    
    def test_get_recent_searches_with_endpoint_parameter(self):
        """Test get_recent_searches with specific endpoint."""
        # Add searches for different endpoints
        utils.add_recent_search("search", {"query": "test"}, [{"title": "Video 1"}])
        utils.add_recent_search("trending", {"category": "music"}, [{"title": "Video 2"}])
        
        search_results = utils.get_recent_searches("search")
        trending_results = utils.get_recent_searches("trending")
        
        self.assertEqual(len(search_results), 1)
        self.assertEqual(len(trending_results), 1)
        self.assertEqual(search_results[0]["parameters"]["query"], "test")
        self.assertEqual(trending_results[0]["parameters"]["category"], "music")
    
    def test_get_recent_searches_empty_endpoint(self):
        """Test get_recent_searches with non-existent endpoint."""
        results = utils.get_recent_searches("nonexistent")
        self.assertEqual(results, [])
    
    
    def test_add_recent_search_max_limit(self):
        """Test that add_recent_search maintains max 50 entries per endpoint."""
        # Add 52 searches to test the limit
        for i in range(52):
            utils.add_recent_search("search", {"query": f"test{i}"}, [{"title": f"Video {i}"}])
        
        results = utils.get_recent_searches("search", max_results=100)
        self.assertEqual(len(results), 50)  # Should be limited to 50
        
        # Most recent should be first
        self.assertEqual(results[0]["parameters"]["query"], "test51")
        self.assertEqual(results[49]["parameters"]["query"], "test2")


if __name__ == "__main__":
    unittest.main()
