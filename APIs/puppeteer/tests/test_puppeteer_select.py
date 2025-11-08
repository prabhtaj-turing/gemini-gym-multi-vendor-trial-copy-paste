import unittest
import asyncio
import copy
from unittest.mock import patch, AsyncMock, MagicMock

# Import the base test case
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the function and dependencies with correct paths
from ..puppeteerAPI import puppeteer_select
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB


class TestPuppeteerSelect(BaseTestCaseWithErrorHandler):

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
    def test_select_successful_by_value(self, mock_get_page):
        """Test successful select operation using option value with persistent browser session."""
        # Mock page for persistent session
        mock_page = AsyncMock()
        mock_page.url = "http://example.com/currentpage"
        mock_element = AsyncMock()
        
        mock_get_page.return_value = mock_page
        mock_page.query_selector.return_value = mock_element
        mock_element.evaluate.side_effect = [
            "select",  # tag name check
            True       # option exists check
        ]
        mock_page.select_option.return_value = ["option1"]  # successful selection
        
        async def test_coro():
            selector = '#my-select'
            value = 'option1'
            result = await puppeteer_select(selector=selector, value=value)
            
            # Verify return value
            self.assertEqual(result, {}, 'Expected an empty dictionary on successful select.')
            
            # Verify browser interactions
            mock_page.wait_for_selector.assert_called_once_with(selector, state="visible", timeout=5000)
            mock_page.query_selector.assert_called_once_with(selector)
            mock_page.select_option.assert_called_once_with(selector, value=value)
            
            # Verify logging
            self.assertEqual(len(DB['logs']), 1, 'Expected one log entry.')
            active_page_url = DB['contexts']['default_context']['active_page']
            expected_log_message_content = f"Selected option '{value}' in select element '{selector}' on page {active_page_url}."
            self.assertTrue(DB['logs'][0].endswith(f'] {expected_log_message_content}'), 
                          f"Log message mismatch. Expected to end with: '] {expected_log_message_content}', Got: '{DB['logs'][0]}'")

        self.run_async_test(test_coro())

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_select_successful_by_text(self, mock_get_page):
        """Test successful select operation using option text with persistent browser session."""
        # Mock page for persistent session
        mock_page = AsyncMock()
        mock_page.url = "http://example.com/currentpage"
        mock_element = AsyncMock()
        
        mock_get_page.return_value = mock_page
        mock_page.query_selector.return_value = mock_element
        mock_element.evaluate.side_effect = [
            "select",  # tag name check
            True       # option exists check
        ]
        mock_page.select_option.return_value = ["option_text"]  # successful selection
        
        async def test_coro():
            selector = '#my-select'
            value = 'Option Text'
            result = await puppeteer_select(selector=selector, value=value)
            
            # Verify return value
            self.assertEqual(result, {}, 'Expected an empty dictionary on successful select.')
            
            # Verify browser interactions
            mock_page.wait_for_selector.assert_called_once_with(selector, state="visible", timeout=5000)
            mock_page.query_selector.assert_called_once_with(selector)
            mock_page.select_option.assert_called_once_with(selector, value=value)
            
            # Verify logging
            self.assertEqual(len(DB['logs']), 1, 'Expected one log entry.')
            active_page_url = DB['contexts']['default_context']['active_page']
            expected_log_message_content = f"Selected option '{value}' in select element '{selector}' on page {active_page_url}."
            self.assertTrue(DB['logs'][0].endswith(f'] {expected_log_message_content}'), 
                          f"Log message mismatch. Expected to end with: '] {expected_log_message_content}', Got: '{DB['logs'][0]}'")

        self.run_async_test(test_coro())

    def test_select_empty_selector_raises_validationerror(self):
        """Test that empty selector raises ValidationError."""
        async def async_call():
            return await puppeteer_select(selector='', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Selector cannot be empty.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on validation error.')

    def test_select_non_string_selector_raises_validationerror(self):
        """Test that non-string selector raises ValidationError."""
        async def async_call():
            return await puppeteer_select(selector=123, value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Selector must be a string.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on validation error.')

    def test_select_non_string_value_raises_validationerror(self):
        """Test that non-string value raises ValidationError."""
        async def async_call():
            return await puppeteer_select(selector='#select', value=123)
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ValidationError,
            expected_message='Value must be a string.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on validation error.')

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_select_element_not_found_raises_elementnotfounderror(self, mock_get_page):
        """Test that element not found raises ElementNotFoundError."""
        # Mock page for persistent session with element not found error
        mock_page = AsyncMock()
        mock_page.url = "http://example.com/currentpage"
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Element not found"))
        mock_get_page.return_value = mock_page
        
        async def async_call():
            return await puppeteer_select(selector='#nonexistent', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ElementNotFoundError,
            expected_message="Element with selector '#nonexistent' not found."
        )

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_select_not_select_element_raises_notselectelementerror(self, mock_get_page):
        """Test that non-select element raises NotSelectElementException."""
        # Mock page for persistent session with non-select element
        mock_page = AsyncMock()
        mock_page.url = "http://example.com/currentpage"
        mock_page.wait_for_selector = AsyncMock()
        mock_element = AsyncMock()
        mock_element.evaluate = AsyncMock(return_value="div")  # Not a select element
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_get_page.return_value = mock_page
        
        async def async_call():
            return await puppeteer_select(selector='#not-select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.NotSelectElementException,
            expected_message="Element '#not-select' is a 'div', not a <select> element."
        )

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_select_option_not_available_raises_optionnotavailableerror(self, mock_get_page):
        """Test that unavailable option raises OptionNotAvailableError."""
        # Mock page for persistent session with option not available
        mock_page = AsyncMock()
        mock_page.url = "http://example.com/currentpage"
        mock_page.wait_for_selector = AsyncMock()
        mock_element = AsyncMock()
        mock_element.evaluate = AsyncMock(side_effect=[
            "select",  # First call for tag name check
            False      # Second call for option existence check
        ])
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        mock_get_page.return_value = mock_page
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='nonexistent-option')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.OptionNotAvailableError,
            expected_message="Option with value 'nonexistent-option' not available in select element '#select'."
        )

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_select_timeout_waiting_for_element_raises_timeouterror(self, mock_get_page):
        """Test that timeout waiting for element raises TimeoutError."""
        # Mock page for persistent session with timeout error
        mock_page = AsyncMock()
        mock_page.url = "http://example.com/currentpage"
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("timeout waiting for element"))
        mock_get_page.return_value = mock_page
        
        async def async_call():
            return await puppeteer_select(selector='#slow-select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=TimeoutError,
            expected_message="Timeout waiting for element '#slow-select' to become visible on page 'http://example.com/currentpage'."
        )

    def test_select_no_active_page_set_raises_browsererror(self):
        """Test that no active page raises BrowserError."""
        # Clear active page to simulate no browser session
        DB['contexts']['default_context']['active_page'] = None
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="No active page in current context."
        )

    def test_select_invalid_active_context_id_raises_browsererror(self):
        """Test that invalid active context ID raises BrowserError."""
        # Set invalid context ID
        DB['active_context'] = 'invalid_context'
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Active context 'invalid_context' not found."
        )

    def test_select_page_not_loaded_successfully_raises_elementnotfounderror(self):
        """Test that page not loaded successfully raises ElementNotFoundError."""
        # Set page as not loaded successfully
        DB['contexts']['default_context']['pages']['http://example.com/currentpage']['loaded_successfully'] = False
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.ElementNotFoundError,
            expected_message="Element with selector '#select' not found."
        )

    def test_select_missing_contexts_raises_browsererror(self):
        """Test that missing contexts raises BrowserError."""
        del DB['contexts']
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message='Browser context state is invalid or missing.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')

    def test_select_malformed_contexts_raises_browsererror(self):
        """Test that malformed contexts raises BrowserError."""
        DB['contexts'] = "not_a_dict"
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message='Browser context state is invalid or missing.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')

    def test_select_malformed_context_state_raises_browsererror(self):
        """Test that malformed context state raises BrowserError."""
        DB['contexts']['default_context'] = "not_a_dict"
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message='Active context state is malformed.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')

    def test_select_missing_pages_raises_browsererror(self):
        """Test that missing pages raises BrowserError."""
        del DB['contexts']['default_context']['pages']
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message='Pages state is invalid or missing.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')

    def test_select_malformed_pages_raises_browsererror(self):
        """Test that malformed pages raises BrowserError."""
        DB['contexts']['default_context']['pages'] = "not_a_dict"
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message='Pages state is invalid or missing.'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')

    def test_select_missing_active_page_info_raises_browsererror(self):
        """Test that missing active page info raises BrowserError."""
        del DB['contexts']['default_context']['pages']['http://example.com/currentpage']
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Active page 'http://example.com/currentpage' not found in pages state."
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')

    def test_select_malformed_active_page_info_raises_browsererror(self):
        """Test that malformed active page info raises BrowserError."""
        DB['contexts']['default_context']['pages']['http://example.com/currentpage'] = "not_a_dict"
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message="Active page 'http://example.com/currentpage' not found in pages state."
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')

    @patch('puppeteer.SimulationEngine.utils.get_current_page')
    def test_select_browser_error_during_operation_raises_browsererror(self, mock_get_page):
        """Test that browser error during operation raises BrowserError."""
        # Mock page for persistent session with browser error
        mock_page = AsyncMock()
        mock_page.url = "http://example.com/currentpage"
        mock_element = AsyncMock()
        
        mock_get_page.return_value = mock_page
        mock_page.query_selector.return_value = mock_element
        mock_element.evaluate.side_effect = [
            "select",  # tag name check
            True       # option exists check
        ]
        mock_page.select_option.side_effect = Exception("Browser automation error")
        
        async def async_call():
            return await puppeteer_select(selector='#select', value='option1')
        
        def sync_wrapper():
            return self.run_async_test(async_call())
        
        self.assert_error_behavior(
            func_to_call=sync_wrapper,
            expected_exception_type=custom_errors.BrowserError,
            expected_message='Browser error during select operation: Browser automation error'
        )
        self.assertEqual(len(DB['logs']), 0, 'No log entry should be created on browser error.')


if __name__ == '__main__':
    unittest.main()
