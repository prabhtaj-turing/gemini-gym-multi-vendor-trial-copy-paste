import unittest
import datetime
import pathlib
import copy
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError as PydanticValidationError

# Import the base test case
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function and dependencies
from ..puppeteerAPI import puppeteer_screenshot
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB


class TestPuppeteerScreenshot(BaseTestCaseWithErrorHandler):
    """Test suite for puppeteer_screenshot function."""

    def setUp(self):
        """Set up test environment before each test."""
        self._original_DB_state = copy.deepcopy(DB)
        # Clear the database before each test
        DB.clear()
        
        # Set up a valid browser context and page state for persistent sessions
        DB["active_context"] = "test_context"
        DB["contexts"] = {
            "test_context": {
                "active_page": "https://example.com",
                "pages": {
                    "https://example.com": {
                        "loaded_successfully": True,
                        "page_title": "Test Page"
                    }
                }
            }
        }
        DB["screenshots"] = []
        DB["logs"] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def run_async_test(self, coro):
        """Helper to run async tests in sync test methods."""
        try:
            # Try to get the current event loop
            import asyncio
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
            import asyncio
            return asyncio.run(coro)

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    @patch('puppeteer.SimulationEngine.utils.record_screenshot_attempt')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_screenshot_full_page_success(self, mock_log, mock_record, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test successful full page screenshot using persistent browser session."""
        # Mock page for persistent session
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "test_screenshot"
        
        # Mock file operations
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_size = 12345
        mock_stat.return_value = mock_stat_obj
        
        # Mock page operations
        mock_page.set_viewport_size = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
        
        async def async_call():
            return await puppeteer_screenshot("test screenshot")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify the result
        self.assertEqual(result["file_path"], str(pathlib.Path("screenshots") / "test_screenshot.png"))
        self.assertEqual(result["image_width"], 800)  # Default width
        self.assertEqual(result["image_height"], 600)  # Default height
        self.assertEqual(result["file_size"], 12345)
        
        # Verify browser operations
        mock_page.set_viewport_size.assert_called_once_with({"width": 800, "height": 600})
        mock_page.screenshot.assert_called_once_with(path=str(pathlib.Path("screenshots") / "test_screenshot.png"), full_page=True)
        
        # Verify logging and recording
        mock_record.assert_called_once()
        mock_log.assert_called_once()

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    @patch('puppeteer.SimulationEngine.utils.record_screenshot_attempt')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_screenshot_element_success(self, mock_log, mock_record, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test successful element screenshot using persistent browser session."""
        # Mock page and element for persistent session
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_element = AsyncMock()
        
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "element_screenshot"
        
        # Mock file operations
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_size = 8765
        mock_stat.return_value = mock_stat_obj
        
        # Mock page and element operations
        mock_page.set_viewport_size = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_element.screenshot = AsyncMock(return_value=b"fake_element_screenshot")
        mock_element.bounding_box = AsyncMock(return_value={"width": 200, "height": 150})
        
        async def async_call():
            return await puppeteer_screenshot("element screenshot", selector="#test-element", width=1024, height=768)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify the result
        self.assertEqual(result["file_path"], str(pathlib.Path("screenshots") / "element_screenshot.png"))
        self.assertEqual(result["image_width"], 200)  # Element width
        self.assertEqual(result["image_height"], 150)  # Element height
        self.assertEqual(result["file_size"], 8765)
        
        # Verify browser operations
        mock_page.wait_for_selector.assert_called_once_with("#test-element", state="visible", timeout=5000)
        mock_element.screenshot.assert_called_once_with(path=str(pathlib.Path("screenshots") / "element_screenshot.png"))

    def test_screenshot_validation_error_empty_name(self):
        """Test validation error for empty name."""
        async def async_call():
            return await puppeteer_screenshot("")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Screenshot name cannot be empty."
        )

    def test_screenshot_validation_error_invalid_width(self):
        """Test validation error for invalid width."""
        async def async_call():
            return await puppeteer_screenshot("test", width=0)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Width must be a positive integer."
        )

    def test_screenshot_validation_error_invalid_height(self):
        """Test validation error for invalid height."""
        async def async_call():
            return await puppeteer_screenshot("test", height=-1)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Height must be a positive integer."
        )

    def test_screenshot_browser_error_no_active_context(self):
        """Test browser error when no active context exists."""
        # Clear the active context to simulate no browser session
        DB["active_context"] = None
        
        async def async_call():
            return await puppeteer_screenshot("test")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        # Should raise BrowserError asking user to navigate first
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="No active browser session. Please navigate to a page first using puppeteer_navigate."
        )

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    def test_screenshot_element_not_found_wait_fails(self, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test element not found error when wait_for_selector fails."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "test"
        
        # Mock page operations - wait_for_selector raises exception
        mock_page.set_viewport_size = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Element not found"))
        
        async def async_call():
            return await puppeteer_screenshot("test", selector="#missing-element")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ElementNotFoundError,
            expected_message="Element with selector '#missing-element' not found."
        )

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    def test_screenshot_element_not_found_query_fails(self, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test element not found error when query_selector returns None."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "test"
        
        # Mock page operations - query_selector returns None
        mock_page.set_viewport_size = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)
        
        async def async_call():
            return await puppeteer_screenshot("test", selector="#missing-element")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ElementNotFoundError,
            expected_message="Element with selector '#missing-element' not found."
        )

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    def test_screenshot_timeout_error(self, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test timeout error during screenshot operation."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "test"
    
        # Mock page operations - screenshot raises timeout error
        mock_page.set_viewport_size = AsyncMock()
        mock_page.screenshot = AsyncMock(side_effect=Exception("timeout waiting for screenshot"))
    
        async def async_call():
            return await puppeteer_screenshot("test")
    
        def sync_wrapper():
            return self.run_async_test(async_call())
    
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=TimeoutError,
            expected_message="Timeout waiting for element 'None' to become visible."
        )

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    def test_screenshot_filesystem_error_during_save(self, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test filesystem error during screenshot save."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "test"
    
        # Mock page operations - screenshot raises file error
        mock_page.set_viewport_size = AsyncMock()
        mock_page.screenshot = AsyncMock(side_effect=Exception("permission denied"))
    
        async def async_call():
            return await puppeteer_screenshot("test")
    
        def sync_wrapper():
            return self.run_async_test(async_call())
    
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.FileSystemError,
            expected_message="A file system error occurred while saving the screenshot."
        )

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    @patch('puppeteer.SimulationEngine.utils.record_screenshot_attempt')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_screenshot_element_no_bounding_box(self, mock_log, mock_record, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test element screenshot when element has no bounding box."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_element = AsyncMock()
        
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "test"
        
        # Mock file operations
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_size = 12345
        mock_stat.return_value = mock_stat_obj
        
        # Mock page and element operations - no bounding box
        mock_page.set_viewport_size = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_element.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock_element.bounding_box = AsyncMock(return_value=None)  # No bounding box
        
        async def async_call():
            return await puppeteer_screenshot("test", selector="#element", width=1000, height=800)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Should use default dimensions when no bounding box
        self.assertEqual(result["image_width"], 1000)
        self.assertEqual(result["image_height"], 800)

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    @patch('puppeteer.SimulationEngine.utils.record_screenshot_attempt')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_screenshot_custom_dimensions(self, mock_log, mock_record, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test screenshot with custom dimensions."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "custom_size"
        
        # Mock file operations
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_size = 54321
        mock_stat.return_value = mock_stat_obj
        
        # Mock page operations
        mock_page.set_viewport_size = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
        
        async def async_call():
            return await puppeteer_screenshot("custom size", width=1920, height=1080)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify custom dimensions
        mock_page.set_viewport_size.assert_called_once_with({"width": 1920, "height": 1080})
        self.assertEqual(result["image_width"], 1920)
        self.assertEqual(result["image_height"], 1080)

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    @patch('puppeteer.SimulationEngine.utils.record_screenshot_attempt')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_screenshot_special_characters_in_name(self, mock_log, mock_record, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test screenshot with special characters in name."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "test_screenshot_with_special_chars"
        
        # Mock file operations
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_size = 98765
        mock_stat.return_value = mock_stat_obj
        
        # Mock page operations
        mock_page.set_viewport_size = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
        
        async def async_call():
            return await puppeteer_screenshot("test/screenshot:with*special<chars>")
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        result = sync_wrapper()
        
        # Verify sanitization was called
        mock_sanitize.assert_called_once_with("test/screenshot:with*special<chars>")
        self.assertIn("test_screenshot_with_special_chars.png", result["file_path"])

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.stat')
    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    @patch('puppeteer.SimulationEngine.utils.sanitize_filename_component')
    @patch('puppeteer.SimulationEngine.utils.record_screenshot_attempt')
    @patch('puppeteer.SimulationEngine.utils.log_action')
    def test_screenshot_database_recording(self, mock_log, mock_record, mock_sanitize, mock_get_page, mock_stat, mock_mkdir):
        """Test that screenshot operations are properly recorded in database."""
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        
        mock_get_page.return_value = mock_page
        mock_sanitize.return_value = "test_record"
        
        # Mock file operations
        mock_stat_obj = MagicMock()
        mock_stat_obj.st_size = 11111
        mock_stat.return_value = mock_stat_obj
        
        # Mock page operations
        mock_page.set_viewport_size = AsyncMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
        
        async def async_call():
            return await puppeteer_screenshot("test record", width=1024, height=768)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        sync_wrapper()
        
        # Verify database recording was called
        mock_record.assert_called_once()
        args, kwargs = mock_record.call_args
        self.assertEqual(args[2], "test record")  # name
        self.assertEqual(args[4], 1024)  # width
        self.assertEqual(args[5], 768)  # height


if __name__ == '__main__':
    unittest.main()
