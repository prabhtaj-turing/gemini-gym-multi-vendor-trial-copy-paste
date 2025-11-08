import unittest
import asyncio
import copy
from unittest.mock import patch, AsyncMock, MagicMock

# Import the base test case
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function and dependencies with correct paths
from ..puppeteerAPI import puppeteer_click
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB


class TestPuppeteerClick(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            'active_context': 'default_context', 
            'contexts': {
                'default_context': {
                    'active_page': 'http://example.com/currentpage', 
                    'pages': {
                        'http://example.com/currentpage': {
                            'page_title': 'Current Test Page', 
                            'status': 200, 
                            'loaded_successfully': True
                        }
                    }
                }
            }, 
            'logs': [], 
            'page_history': [], 
            'screenshots': [], 
            'script_results': []
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

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_click_successful(self, mock_get_page):
        """Test successful click operation."""
        # Mock page for persistent session
        mock_page = AsyncMock()
        mock_page.url = 'http://example.com/currentpage'
        mock_get_page.return_value = mock_page
        
        async def test_coro():
            selector = '#my-button'
            result = await puppeteer_click(selector=selector)
            
            # Verify return value
            self.assertEqual(result, {}, 'Expected an empty dictionary on successful click.')
            
            # Verify browser interactions
            mock_page.wait_for_selector.assert_called_once_with(selector, state="visible", timeout=5000)
            mock_page.click.assert_called_once_with(selector)
            
            # Verify logging
            self.assertEqual(len(DB['logs']), 1, 'Expected one log entry.')
            active_page_url = DB['contexts']['default_context']['active_page']
            expected_log_message_content = f"Clicked element '{selector}' on page {active_page_url}."
            self.assertTrue(DB['logs'][0].endswith(f'] {expected_log_message_content}'), 
                          f"Log message mismatch. Expected to end with: '] {expected_log_message_content}', Got: '{DB['logs'][0]}'")

        self.run_async_test(test_coro())

    def test_click_empty_selector_raises_validationerror(self):
        """Test that empty selector raises ValidationError."""
        async def async_call():
            return await puppeteer_click(selector='')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Selector cannot be empty.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on validation error.')

    def test_click_non_string_selector_raises_validationerror(self):
        """Test that non-string selector raises ValidationError."""
        async def async_call():
            return await puppeteer_click(selector=123)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Selector must be a string.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on validation error.')

    def test_click_malformed_selector_raises_validationerror(self):
        """Test that malformed selector raises ValidationError."""
        malformed_selector = '###invalid-css-selector'
        
        async def async_call():
            return await puppeteer_click(selector=malformed_selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Selector is malformed or invalid.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on validation error.')

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_click_element_not_found_raises_elementnotfounderror(self, mock_get_page):
        """Test that element not found raises ElementNotFoundError."""
        # Mock page for persistent session
        mock_page = AsyncMock()
        mock_page.url = 'http://example.com/currentpage'
        mock_page.wait_for_selector.side_effect = Exception("Element not found")
        mock_get_page.return_value = mock_page
        
        selector = '#non-existent-element'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ElementNotFoundError,
            expected_message="Element with selector '#non-existent-element' not found."
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created if element not found.')

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_click_timeout_raises_timeouterror(self, mock_get_page):
        """Test that timeout raises TimeoutError."""
        # Mock page for persistent session
        mock_page = AsyncMock()
        mock_page.url = 'http://example.com/currentpage'
        mock_page.wait_for_selector.return_value = None  # Success
        mock_page.click.side_effect = Exception("Timeout waiting for element to become clickable")
        mock_get_page.return_value = mock_page
        
        selector = '#slow-element'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=TimeoutError,
            expected_message="Timeout waiting for element '#slow-element' to become clickable on page 'http://example.com/currentpage'."
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on timeout.')

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_click_element_not_interactable_raises_elementnotinteractableerror(self, mock_get_page):
        """Test that non-interactable element raises ElementNotInteractableError."""
        # Mock page for persistent session
        mock_page = AsyncMock()
        mock_page.url = 'http://example.com/currentpage'
        mock_page.wait_for_selector.return_value = None  # Success
        mock_page.click.side_effect = Exception("Element not clickable")
        mock_get_page.return_value = mock_page
        
        selector = '#disabled-button'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ElementNotInteractableError,
            expected_message="Element with selector '#disabled-button' found but not interactable. Reason: unknown."
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created if element not interactable.')

    def test_click_no_active_page_set_raises_browsererror(self):
        """Test that no active page raises BrowserError."""
        DB['contexts']['default_context']['active_page'] = None
        selector = '#button-on-nonexistent-page'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="No active page in current context."
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created if no active page.')

    def test_click_invalid_active_context_id_raises_browsererror(self):
        """Test that invalid active context raises BrowserError."""
        DB['active_context'] = 'context_that_does_not_exist'
        selector = '#button-in-invalid-context'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Active context 'context_that_does_not_exist' not found."
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created if active context is invalid.')

    def test_click_page_not_loaded_successfully_raises_elementnotfounderror(self):
        """Test that page not loaded successfully raises ElementNotFoundError."""
        DB['contexts']['default_context']['pages']['http://example.com/currentpage']['loaded_successfully'] = False
        selector = '#button-on-failed-page'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ElementNotFoundError,
            expected_message="Element with selector '#button-on-failed-page' not found."
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created if page not loaded successfully.')

    def test_click_missing_contexts_raises_browsererror(self):
        """Test that missing contexts raises BrowserError."""
        del DB['contexts']
        selector = '#button-no-contexts'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Browser context state is invalid or missing."
        )
        self.assertEqual(len(DB['logs']), 0)

    def test_click_malformed_contexts_raises_browsererror(self):
        """Test that malformed contexts raises BrowserError."""
        DB['contexts'] = "not_a_dict"
        selector = '#button-malformed-contexts'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Browser context state is invalid or missing."
        )
        self.assertEqual(len(DB['logs']), 0)

    def test_click_malformed_context_state_raises_browsererror(self):
        """Test that malformed context state raises BrowserError."""
        DB['contexts']['default_context'] = "not_a_dict"
        selector = '#button-malformed-context'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Active context state is malformed."
        )
        self.assertEqual(len(DB['logs']), 0)

    def test_click_missing_pages_raises_browsererror(self):
        """Test that missing pages raises BrowserError."""
        del DB['contexts']['default_context']['pages']
        selector = '#button-missing-pages'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Pages state is invalid or missing."
        )
        self.assertEqual(len(DB['logs']), 0)

    def test_click_malformed_pages_raises_browsererror(self):
        """Test that malformed pages raises BrowserError."""
        DB['contexts']['default_context']['pages'] = "not_a_dict"
        selector = '#button-malformed-pages'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Pages state is invalid or missing."
        )
        self.assertEqual(len(DB['logs']), 0)

    def test_click_missing_active_page_info_raises_browsererror(self):
        """Test that missing active page info raises BrowserError."""
        del DB['contexts']['default_context']['pages']['http://example.com/currentpage']
        selector = '#button-missing-page-info'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Active page 'http://example.com/currentpage' not found in pages state."
        )
        self.assertEqual(len(DB['logs']), 0)

    def test_click_malformed_active_page_info_raises_browsererror(self):
        """Test that malformed active page info raises BrowserError."""
        DB['contexts']['default_context']['pages']['http://example.com/currentpage'] = "not_a_dict"
        selector = '#button-malformed-page-info'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Active page 'http://example.com/currentpage' not found in pages state."
        )
        self.assertEqual(len(DB['logs']), 0)

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_click_browser_error_during_operation_raises_browsererror(self, mock_get_page):
        """Test that browser error during operation raises BrowserError."""
        # Mock page for persistent session
        mock_page = AsyncMock()
        mock_page.url = 'http://example.com/currentpage'
        mock_page.wait_for_selector.return_value = None  # Success
        mock_page.click.side_effect = Exception("Some browser error")
        mock_get_page.return_value = mock_page
        
        selector = '#button-browser-error'
        
        async def async_call():
            return await puppeteer_click(selector=selector)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Browser error during click operation: Some browser error"
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')


if __name__ == '__main__':
    unittest.main()