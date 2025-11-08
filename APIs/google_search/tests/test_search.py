import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google_search.SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import search_queries
from .. import search_queries


class TestGoogleSearch(BaseTestCaseWithErrorHandler):
    """Test cases for the Google Search API."""

    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_search_single_query(self, mock_gemini):
        """Test searching with a single query."""
        mock_gemini.return_value = "Sample search result for artificial intelligence"
        
        result = search_queries(queries=["artificial intelligence"])

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["query"], "artificial intelligence")
        self.assertIn("result", result[0])
        self.assertIsInstance(result[0]["result"], str)
        mock_gemini.assert_called_once_with("artificial intelligence")

    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_search_multiple_queries(self, mock_gemini):
        """Test searching with multiple queries."""
        mock_gemini.side_effect = [
            "Sample search result for artificial intelligence",
            "Sample search result for cooking recipes"
        ]
        
        result = search_queries(queries=["artificial intelligence", "cooking recipes"])

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["query"], "artificial intelligence")
        self.assertEqual(result[1]["query"], "cooking recipes")
        self.assertIn("result", result[0])
        self.assertIn("result", result[1])
        self.assertEqual(mock_gemini.call_count, 2)

    def test_search_with_empty_query_raises_error(self):
        """Test that providing an empty query raises an error."""
        self.assert_error_behavior(
            func_to_call=search_queries,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query at index 0 must be a non-empty string.",
            queries=[""]
        )

    def test_search_with_empty_queries_list_raises_error(self):
        """Test that providing an empty queries list raises an error."""
        self.assert_error_behavior(
            func_to_call=search_queries,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Queries must be a non-empty list of strings.",
            queries=[]
        )

    def test_search_with_invalid_query_type_raises_error(self):
        """Test that providing invalid query type raises an error."""
        self.assert_error_behavior(
            func_to_call=search_queries,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query at index 0 must be a non-empty string.",
            queries=[123]
        )

    def test_search_with_invalid_queries_type_raises_error(self):
        """Test that providing invalid queries type raises an error."""
        self.assert_error_behavior(
            func_to_call=search_queries,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Queries must be a non-empty list of strings.",
            queries="not a list"
        )

    def test_search_with_empty_string_in_queries_raises_error(self):
        """Test that providing empty strings in queries list raises an error."""
        self.assert_error_behavior(
            func_to_call=search_queries,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query at index 1 must be a non-empty string.",
            queries=["valid", ""]
        )

    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_search_results_structure(self, mock_gemini):
        """Test that search results have the correct structure."""
        mock_gemini.return_value = "Sample search result for artificial intelligence"
        
        result = search_queries(queries=["artificial intelligence"])

        self.assertGreater(len(result), 0)
        search_result = result[0]

        # Check required fields
        self.assertIn("query", search_result)
        self.assertIn("result", search_result)
        self.assertIsInstance(search_result["result"], str)

    def test_search_with_whitespace_only_query_raises_error(self):
        """Test that providing whitespace-only query raises an error."""
        self.assert_error_behavior(
            func_to_call=search_queries,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query at index 0 must be a non-empty string.",
            queries=["   "]
        )

    def test_search_with_whitespace_only_queries_raises_error(self):
        """Test that providing whitespace-only queries raises an error."""
        self.assert_error_behavior(
            func_to_call=search_queries,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query at index 0 must be a non-empty string.",
            queries=["   ", "valid"]
        )

    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_search_returns_relevant_results(self, mock_gemini):
        """Test that search returns relevant results for different queries."""
        mock_gemini.side_effect = [
            "Sample search result for artificial intelligence",
            "Sample search result for cooking recipes"
        ]
        
        # Test technology-related query
        tech_result = search_queries(queries=["artificial intelligence"])
        self.assertGreater(len(tech_result), 0)
        self.assertIsInstance(tech_result[0]["result"], str)

        # Test cooking-related query
        cooking_result = search_queries(queries=["cooking recipes"])
        self.assertGreater(len(cooking_result), 0)
        self.assertIsInstance(cooking_result[0]["result"], str)

    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_search_handles_special_characters(self, mock_gemini):
        """Test that search handles special characters in queries."""
        mock_gemini.return_value = "Sample search result for iPhone 15 review"
        
        result = search_queries(queries=["iPhone 15 review"])
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["query"], "iPhone 15 review")

    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_search_handles_long_queries(self, mock_gemini):
        """Test that search handles longer queries."""
        long_query = "artificial intelligence machine learning deep learning neural networks"
        mock_gemini.return_value = "Sample search result for long query"
        
        result = search_queries(queries=[long_query])
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["query"], long_query)

    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_search_multiple_queries_different_lengths(self, mock_gemini):
        """Test searching with queries of different lengths."""
        mock_gemini.side_effect = [
            "Sample result for ai",
            "Sample result for artificial intelligence", 
            "Sample result for machine learning and deep learning"
        ]
        
        queries = ["ai", "artificial intelligence", "machine learning and deep learning"]
        result = search_queries(queries=queries)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["query"], "ai")
        self.assertEqual(result[1]["query"], "artificial intelligence")
        self.assertEqual(result[2]["query"], "machine learning and deep learning")

    def test_search_gemini_response_error_handling(self):
        """Test that Gemini API errors are properly handled."""
        with patch('google_search.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            mock_gemini.side_effect = ValueError("API Key not found")
            
            self.assert_error_behavior(
                func_to_call=search_queries,
                expected_exception_type=ValueError,
                expected_message="API Key not found",
                queries=["test query"]
            )

    def test_search_general_exception_handling(self):
        """Test that general exceptions are properly caught."""
        # Mock utils.get_gemini_response to raise a general exception
        with patch('google_search.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            mock_gemini.side_effect = Exception("General error occurred")
            
            self.assert_error_behavior(
                func_to_call=search_queries,
                expected_exception_type=Exception,
                expected_message="General error occurred",
                queries=["test query"]
            )

    def test_search_validation_error_preserved(self):
        """Test that ValidationError exceptions are preserved."""
        # Mock utils.get_gemini_response to raise a ValidationError
        with patch('google_search.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            mock_gemini.side_effect = custom_errors.ValidationError("Invalid search parameters")
            
            self.assert_error_behavior(
                func_to_call=search_queries,
                expected_exception_type=custom_errors.ValidationError,
                expected_message="Invalid search parameters",
                queries=["test query"]
            )

    def test_search_exception_with_multiple_queries(self):
        """Test exception handling with multiple queries."""
        with patch('google_search.SimulationEngine.utils.get_gemini_response') as mock_gemini:
            # First call succeeds, second call fails
            mock_gemini.side_effect = [
                "Valid response for query1",
                Exception("Second query failed")
            ]
            
            self.assert_error_behavior(
                func_to_call=search_queries,
                expected_exception_type=Exception,
                expected_message="Second query failed",
                queries=["query1", "query2"]
            )

    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_search_strips_whitespace_from_queries(self, mock_gemini):
        """Test that whitespace is stripped from queries."""
        mock_gemini.return_value = "Sample search result"
        
        result = search_queries(queries=["  artificial intelligence  "])
        self.assertEqual(result[0]["query"], "artificial intelligence")

    def test_search_with_mixed_valid_invalid_queries(self):
        """Test that mixed valid and invalid queries are handled correctly."""
        self.assert_error_behavior(
            func_to_call=search_queries,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Query at index 1 must be a non-empty string.",
            queries=["valid query", "", "another valid query"]
        )

    @patch('google_search.SimulationEngine.utils.add_recent_search')
    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_add_recent_search_is_called(self, mock_gemini, mock_add_recent_search):
        """Test that add_recent_search is called for a single query."""
        mock_gemini.return_value = "Sample search result"
        
        search_queries(queries=["test query"])

        self.assertTrue(mock_add_recent_search.called)
        self.assertEqual(mock_add_recent_search.call_count, 1)

    @patch('google_search.SimulationEngine.utils.add_recent_search')
    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_add_recent_search_is_called_for_multiple_queries(self, mock_gemini, mock_add_recent_search):
        """Test that add_recent_search is called for each query in a multiple-query search."""
        mock_gemini.side_effect = [
            "Result 1",
            "Result 2"
        ]
        
        search_queries(queries=["query1", "query2"])

        self.assertEqual(mock_add_recent_search.call_count, 2)

    @patch('google_search.SimulationEngine.utils.add_recent_search')
    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_add_recent_search_receives_correct_data(self, mock_gemini, mock_add_recent_search):
        """Test that add_recent_search is called with the correct result data."""
        mock_gemini.return_value = "Sample search result"
        
        search_queries(queries=["test query"])

        expected_result = {
            "query": "test query",
            "result": "Sample search result"
        }
        mock_add_recent_search.assert_called_once_with(expected_result)

    @patch('google_search.SimulationEngine.utils.add_recent_search')
    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_add_recent_search_receives_correct_data_multiple_queries(self, mock_gemini, mock_add_recent_search):
        """Test that add_recent_search is called with correct data for multiple queries."""
        mock_gemini.side_effect = [
            "Result 1",
            "Result 2"
        ]
        
        search_queries(queries=["query1", "query2"])

        expected_calls = [
            unittest.mock.call({"query": "query1", "result": "Result 1"}),
            unittest.mock.call({"query": "query2", "result": "Result 2"})
        ]
        mock_add_recent_search.assert_has_calls(expected_calls, any_order=False)
    
    @patch('google_search.SimulationEngine.utils.add_recent_search')
    @patch('google_search.SimulationEngine.utils.get_gemini_response')
    def test_using_function_alias_works(self, mock_gemini, mock_add_recent_search):
        """Test that add_recent_search is called with correct data for multiple queries."""
        mock_gemini.side_effect = [
            "Result 1",
            "Result 2"
        ]
        
        search_queries(queries=["query1", "query2"])

        expected_calls = [
            unittest.mock.call({"query": "query1", "result": "Result 1"}),
            unittest.mock.call({"query": "query2", "result": "Result 2"})
        ]
        mock_add_recent_search.assert_has_calls(expected_calls, any_order=False)


if __name__ == "__main__":
    unittest.main()
