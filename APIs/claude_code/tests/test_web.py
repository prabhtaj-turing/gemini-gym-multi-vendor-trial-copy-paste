import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import requests

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from claude_code import web  # noqa: E402
from claude_code.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler  # noqa: E402

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "ClaudeCodeDefaultDB.json"

# Fallback DB structure used when the default DB file doesn't exist
FALLBACK_DB_STRUCTURE = {
    "workspace_root": "/home/user/project",
    "cwd": "/home/user/project",
    "file_system": {},
    "memory_storage": {},
    "last_edit_params": None,
    "background_processes": {},
    "tool_metrics": {}
}


class TestWeb(BaseTestCaseWithErrorHandler):
    """Test cases for the web fetch function."""

    def setUp(self):
        """Set up test database before each test."""
        DB.clear()
        if DB_JSON_PATH.exists():
            with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
                DB.update(json.load(fh))
        else:
            DB.update(FALLBACK_DB_STRUCTURE)

    def test_web_fetch_success(self):
        """Test successful web fetch."""
        with patch('requests.get') as mock_get:
            # Mock successful response
            mock_response = Mock()
            mock_response.text = "Hello, World!"
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = web.web_fetch("https://example.com")
            
            self.assertEqual(result["content"], "Hello, World!")
            self.assertEqual(result["status_code"], 200)
            mock_get.assert_called_once_with("https://example.com", timeout=10)

    def test_web_fetch_invalid_url_type(self):
        """Test error handling for invalid URL type."""
        self.assert_error_behavior(
            func_to_call=web.web_fetch,
            expected_exception_type=TypeError,
            expected_message="url must be a string",
            url=123
        )
        
        self.assert_error_behavior(
            func_to_call=web.web_fetch,
            expected_exception_type=TypeError,
            expected_message="url must be a string",
            url=None
        )
        
        self.assert_error_behavior(
            func_to_call=web.web_fetch,
            expected_exception_type=TypeError,
            expected_message="url must be a string",
            url=["https://example.com"]
        )

    def test_web_fetch_connection_error(self):
        """Test handling of connection errors."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            self.assert_error_behavior(
                func_to_call=web.web_fetch,
                expected_exception_type=ConnectionError,
                expected_message="Could not connect to https://example.com: Connection failed",
                url="https://example.com"
            )

    def test_web_fetch_timeout_error(self):
        """Test handling of timeout errors."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            self.assert_error_behavior(
                func_to_call=web.web_fetch,
                expected_exception_type=ConnectionError,
                expected_message="Could not connect to https://example.com: ",
                url="https://example.com"
            )

    def test_web_fetch_pure_timeout_error_line_41(self):
        """Test handling of pure timeout errors to hit line 41."""
        # Temporarily patch the exception handling to bypass RequestException
        with patch('claude_code.web.requests') as mock_requests:
            # Create a custom timeout that doesn't inherit from RequestException
            class PureTimeout(Exception):
                pass
            
            # Set up the mock to raise our pure timeout
            mock_requests.get.side_effect = PureTimeout("Pure timeout")
            mock_requests.exceptions.Timeout = PureTimeout
            mock_requests.exceptions.RequestException = requests.exceptions.RequestException
            mock_requests.exceptions.HTTPError = requests.exceptions.HTTPError
            
            self.assert_error_behavior(
                func_to_call=web.web_fetch,
                expected_exception_type=TimeoutError,
                expected_message="Request to https://example.com timed out",
                url="https://example.com"
            )

    def test_web_fetch_http_error(self):
        """Test handling of HTTP errors."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            self.assert_error_behavior(
                func_to_call=web.web_fetch,
                expected_exception_type=ConnectionError,
                expected_message="Could not connect to https://example.com/notfound: 404 Not Found",
                url="https://example.com/notfound"
            )

    def test_web_fetch_pure_http_error_line_43(self):
        """Test handling of pure HTTP errors to hit line 43."""
        # Temporarily patch the exception handling to bypass RequestException
        with patch('claude_code.web.requests') as mock_requests:
            # Create a custom HTTP error that doesn't inherit from RequestException
            class PureHTTPError(Exception):
                pass
            
            # Set up the mock to raise our pure HTTP error
            mock_requests.get.side_effect = PureHTTPError("Pure HTTP error")
            mock_requests.exceptions.HTTPError = PureHTTPError
            mock_requests.exceptions.RequestException = requests.exceptions.RequestException
            mock_requests.exceptions.Timeout = requests.exceptions.Timeout
            
            self.assert_error_behavior(
                func_to_call=web.web_fetch,
                expected_exception_type=Exception,
                expected_message="HTTP Error: Pure HTTP error",
                url="https://example.com"
            )

    def test_web_fetch_request_exception(self):
        """Test handling of general request exceptions."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("General request error")
            
            self.assert_error_behavior(
                func_to_call=web.web_fetch,
                expected_exception_type=ConnectionError,
                expected_message="Could not connect to https://example.com: General request error",
                url="https://example.com"
            )

    def test_web_fetch_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = ValueError("Unexpected error")
            
            self.assert_error_behavior(
                func_to_call=web.web_fetch,
                expected_exception_type=Exception,
                expected_message="An unexpected error occurred: Unexpected error",
                url="https://example.com"
            )

    def test_web_fetch_different_status_codes(self):
        """Test web fetch with different HTTP status codes."""
        test_cases = [
            (200, "OK"),
            (201, "Created"),
            (302, "Found"),
            (404, "Not Found"),
            (500, "Internal Server Error")
        ]
        
        for status_code, content in test_cases:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.text = content
                mock_response.status_code = status_code
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                result = web.web_fetch("https://example.com")
                
                self.assertEqual(result["content"], content)
                self.assertEqual(result["status_code"], status_code)

    def test_web_fetch_empty_response(self):
        """Test web fetch with empty response."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = ""
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = web.web_fetch("https://example.com/empty")
            
            self.assertEqual(result["content"], "")
            self.assertEqual(result["status_code"], 200)

    def test_web_fetch_large_response(self):
        """Test web fetch with large response content."""
        large_content = "x" * 10000  # 10KB of content
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = large_content
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = web.web_fetch("https://example.com/large")
            
            self.assertEqual(result["content"], large_content)
            self.assertEqual(result["status_code"], 200)
            self.assertEqual(len(result["content"]), 10000)

    def test_web_fetch_unicode_content(self):
        """Test web fetch with unicode content."""
        unicode_content = "Hello 世界 🌍 café naïve résumé"
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = unicode_content
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = web.web_fetch("https://example.com/unicode")
            
            self.assertEqual(result["content"], unicode_content)
            self.assertEqual(result["status_code"], 200)


if __name__ == "__main__":
    unittest.main()