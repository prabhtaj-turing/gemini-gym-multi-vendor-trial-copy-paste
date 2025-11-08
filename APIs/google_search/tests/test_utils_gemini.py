import unittest
from unittest.mock import patch, MagicMock
from ..SimulationEngine import utils

class TestUtilsGemini(unittest.TestCase):
    """Test suite for the Gemini API call in utils."""

    @patch('requests.post')
    @patch('os.getenv')
    @patch('APIs.google_search.SimulationEngine.utils.get_google_api_key')
    def test_get_gemini_response(self, mock_get_google_api_key, mock_os_getenv, mock_requests_post):
        """Test the get_gemini_response function."""
        # Mock the environment variables and API key
        mock_os_getenv.return_value = "http://dummy_url"
        mock_get_google_api_key.return_value = "dummy_key"
        
        # Mock the requests.post call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "Mocked response"
                    }]
                }
            }]
        }
        mock_requests_post.return_value = mock_response

        # Call the function
        response = utils.get_gemini_response("test query")

        # Assert that the function returned the mocked response
        self.assertEqual(response, "Mocked response")

if __name__ == '__main__':
    unittest.main()
