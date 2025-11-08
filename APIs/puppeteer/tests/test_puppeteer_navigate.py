import unittest
import asyncio
import copy
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from urllib.parse import urlparse

# Import the base test case
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function and dependencies
from ..puppeteerAPI import puppeteer_navigate
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB


class TestPuppeteerNavigate(BaseTestCaseWithErrorHandler):
    """Comprehensive test suite for puppeteer_navigate function."""

    def setUp(self):
        """Set up test environment before each test."""
        self._original_DB_state = copy.deepcopy(DB)
        # Clear the database state
        DB.clear()
        DB.update({
            "contexts": {"default": {"active_page": None, "pages": {}}},
            "active_context": "default",
            "page_history": [],
            "logs": []
        })

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def run_async_test(self, coro):
        """Helper to run async tests in sync test methods."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, use asyncio.create_task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result()
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # No event loop exists, create a new one
            return asyncio.run(coro)

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_success_basic(self, mock_log, mock_load_page_persistent):
        """Test successful navigation to a basic URL using persistent browser session."""
        test_url = "https://example.com"
        
        # Mock the persistent browser session
        mock_page_data = {
            "page": AsyncMock(),
            "navigation_details": {
                "page_title": "Example Domain",
                "response_status": 200,
                "loaded_successfully": True
            }
        }
        
        mock_load_page_persistent.return_value = mock_page_data
        
        async def async_call():
            return await puppeteer_navigate(test_url)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify the result
        self.assertEqual(result["page_title"], "Example Domain")
        self.assertEqual(result["response_status"], 200)
        self.assertTrue(result["loaded_successfully"])
        self.assertEqual(result["url"], test_url)
        
        # Verify database state
        self.assertEqual(DB["contexts"]["default"]["active_page"], test_url)
        self.assertIn(test_url, DB["contexts"]["default"]["pages"])
        self.assertEqual(len(DB["page_history"]), 1)
        
        # Verify logging
        mock_log.assert_called_once()
        log_call = mock_log.call_args[0][0]
        self.assertIn("Navigated to https://example.com", log_call)
        self.assertIn("Title: Example Domain", log_call)
        self.assertIn("Status: 200", log_call)

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_success_with_launch_options(self, mock_log, mock_load_page_persistent):
        """Test successful navigation with custom launch options using persistent browser session."""
        test_url = "https://github.com"
        launch_options = {"headless": False, "viewport": {"width": 1920, "height": 1080}}
        
        mock_page_data = {
            "page": AsyncMock(),
            "navigation_details": {
                "page_title": "GitHub",
                "response_status": 200,
                "loaded_successfully": True
            }
        }
        
        mock_load_page_persistent.return_value = mock_page_data
        
        async def async_call():
            return await puppeteer_navigate(test_url, launch_options=launch_options)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify the result
        self.assertEqual(result["page_title"], "GitHub")
        self.assertEqual(result["response_status"], 200)
        self.assertEqual(result["url"], test_url)
        
        # Verify launch options were passed correctly
        mock_load_page_persistent.assert_called_once_with(
            url=test_url,
            context_id="default",
            launch_options=launch_options,
            allow_dangerous=False
        )

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_success_allow_dangerous(self, mock_log, mock_load_page_persistent):
        """Test successful navigation with allow_dangerous=True using persistent browser session."""
        test_url = "ftp://files.example.com"
        
        mock_page_data = {
            "page": AsyncMock(),
            "navigation_details": {
                "page_title": "FTP Server",
                "response_status": 200,
                "loaded_successfully": True
            }
        }
        
        mock_load_page_persistent.return_value = mock_page_data
        
        async def async_call():
            return await puppeteer_navigate(test_url, allow_dangerous=True)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify the result
        self.assertEqual(result["page_title"], "FTP Server")
        self.assertEqual(result["url"], test_url)

    # Validation Error Tests
    def test_navigate_validation_error_empty_url(self):
        """Test validation error for empty URL."""
        async def async_call():
            return await puppeteer_navigate("")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="URL cannot be empty."
        )

    def test_navigate_validation_error_invalid_url_format(self):
        """Test validation error for invalid URL format."""
        async def async_call():
            return await puppeteer_navigate("not-a-url")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="not-a-url is not a valid URL"
        )

    def test_navigate_validation_error_missing_scheme(self):
        """Test validation error for URL missing scheme."""
        async def async_call():
            return await puppeteer_navigate("example.com")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="example.com is not a valid URL"
        )

    def test_navigate_validation_error_unsafe_scheme(self):
        """Test validation error for unsafe URL scheme."""
        async def async_call():
            return await puppeteer_navigate("javascript:alert('xss')")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="javascript:alert('xss') is not a valid URL"
        )

    def test_navigate_validation_error_file_scheme(self):
        """Test validation error for file:// scheme without allow_dangerous."""
        async def async_call():
            return await puppeteer_navigate("file:///etc/passwd")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="file:///etc/passwd is not a valid URL"
        )

    def test_navigate_validation_error_invalid_launch_options(self):
        """Test validation error for invalid launch options."""
        async def async_call():
            return await puppeteer_navigate("https://example.com", launch_options="invalid")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Launch options must be a dictionary."
        )

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_browser_error_init_failure(self, mock_log, mock_load_page_persistent):
        """Test browser error when session creation fails."""
        test_url = "https://example.com"
    
        # Mock session creation failure
        mock_load_page_persistent.side_effect = Exception("Failed to create browser session")
    
        async def async_call():
            return await puppeteer_navigate(test_url)
    
        def sync_wrapper():
            return self.run_async_test(async_call())
    
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Navigation failed: Failed to create browser session"
        )

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_browser_error_page_load_failure(self, mock_log, mock_load_page_persistent):
        """Test browser error when page loading fails."""
        test_url = "https://example.com"
        
        mock_load_page_persistent.side_effect = Exception("Page load failed")
        
        async def async_call():
            return await puppeteer_navigate(test_url)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Navigation failed: Page load failed"
        )

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_network_error_connection_failed(self, mock_log, mock_load_page_persistent):
        """Test network error when connection fails."""
        test_url = "https://nonexistent.example.com"
        
        mock_load_page_persistent.side_effect = Exception("net::ERR_NAME_NOT_RESOLVED")
        
        async def async_call():
            return await puppeteer_navigate(test_url)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.NetworkError,
            expected_message="Failed to navigate to https://nonexistent.example.com: net::ERR_NAME_NOT_RESOLVED"
        )

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_network_error_dns_failure(self, mock_log, mock_load_page_persistent):
        """Test network error for DNS resolution failure."""
        test_url = "https://invalid-domain-name.test"
        
        mock_load_page_persistent.side_effect = Exception("DNS resolution failed")
        
        async def async_call():
            return await puppeteer_navigate(test_url)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.NetworkError,
            expected_message="Failed to navigate to https://invalid-domain-name.test: DNS resolution failed"
        )

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_timeout_error(self, mock_log, mock_load_page_persistent):
        """Test timeout error during navigation."""
        test_url = "https://slow.example.com"
        
        mock_load_page_persistent.side_effect = Exception("timeout waiting for page load")
        
        async def async_call():
            return await puppeteer_navigate(test_url)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=TimeoutError,
            expected_message="Navigation to https://slow.example.com timed out"
        )

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_redirect_handling(self, mock_log, mock_load_page_persistent):
        """Test navigation with redirects using persistent browser session."""
        test_url = "https://redirect.example.com"
        final_url = "https://final.example.com"
        
        mock_page_data = {
            "page": AsyncMock(),
            "navigation_details": {
                "page_title": "Final Page",
                "response_status": 200,
                "loaded_successfully": True
            }
        }
        
        mock_load_page_persistent.return_value = mock_page_data
        
        async def async_call():
            return await puppeteer_navigate(test_url)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify the result
        self.assertEqual(result["page_title"], "Final Page")
        self.assertEqual(result["response_status"], 200)
        self.assertTrue(result["loaded_successfully"])

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_special_characters_in_url(self, mock_log, mock_load_page_persistent):
        """Test navigation with special characters in URL using persistent browser session."""
        test_url = "https://example.com/search?q=hello%20world&lang=en"
        
        mock_page_data = {
            "page": AsyncMock(),
            "navigation_details": {
                "page_title": "Search Results",
                "response_status": 200,
                "loaded_successfully": True
            }
        }
        
        mock_load_page_persistent.return_value = mock_page_data
        
        async def async_call():
            return await puppeteer_navigate(test_url)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify the result
        self.assertEqual(result["page_title"], "Search Results")
        self.assertEqual(result["url"], test_url)

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_database_state_management(self, mock_log, mock_load_page_persistent):
        """Test that database state is properly managed during navigation."""
        test_url = "https://database.example.com"
        
        mock_page_data = {
            "page": AsyncMock(),
            "navigation_details": {
                "page_title": "Database Test",
                "response_status": 200,
                "loaded_successfully": True
            }
        }
        
        mock_load_page_persistent.return_value = mock_page_data
        
        async def async_call():
            return await puppeteer_navigate(test_url)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify database state was updated correctly
        self.assertEqual(DB["contexts"]["default"]["active_page"], test_url)
        self.assertIn(test_url, DB["contexts"]["default"]["pages"])
        page_info = DB["contexts"]["default"]["pages"][test_url]
        self.assertEqual(page_info["page_title"], "Database Test")
        
        # Verify page history was recorded
        self.assertEqual(len(DB["page_history"]), 1)
        history_entry = DB["page_history"][0]
        self.assertEqual(history_entry.url, test_url)
        self.assertEqual(history_entry.page_title, "Database Test")

    @patch('puppeteer.SimulationEngine.utils.load_page_persistent')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_navigate_multiple_navigations(self, mock_log, mock_load_page_persistent):
        """Test multiple navigations maintain proper state."""
        urls = ["https://first.example.com", "https://second.example.com"]
        
        def mock_load_side_effect(url, **kwargs):
            if url == urls[0]:
                return {
                    "page": AsyncMock(),
                    "navigation_details": {
                        "page_title": "First Page",
                        "response_status": 200,
                        "loaded_successfully": True
                    }
                }
            else:
                return {
                    "page": AsyncMock(),
                    "navigation_details": {
                        "page_title": "Second Page",
                        "response_status": 200,
                        "loaded_successfully": True
                    }
                }
        
        mock_load_page_persistent.side_effect = mock_load_side_effect
        
        for url in urls:
            async def async_call():
                return await puppeteer_navigate(url)
            
            def sync_wrapper():
                return self.run_async_test(async_call())
            
            result = sync_wrapper()
            
            # Verify each navigation
            self.assertEqual(DB["contexts"]["default"]["active_page"], url)
            self.assertIn(url, DB["contexts"]["default"]["pages"])
        
        # Verify final state
        self.assertEqual(len(DB["page_history"]), 2)
        self.assertEqual(DB["contexts"]["default"]["active_page"], urls[1])


if __name__ == '__main__':
    unittest.main()
