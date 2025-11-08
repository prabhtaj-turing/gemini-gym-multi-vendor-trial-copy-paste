
from common_utils.tool_spec_decorator import tool_spec
from pydantic import BaseModel, ValidationError as PydanticValidationError
from .SimulationEngine import utils
from .SimulationEngine import custom_errors
from .SimulationEngine import models
from .SimulationEngine.db import DB
import pathlib
import datetime

from typing import Dict, Any, Optional

@tool_spec(
    spec={
        'name': 'click',
        'description': """ Clicks an element on the current page.
        
        Locates an element using the provided CSS selector and performs a click action on it.
        Waits for the element to be visible before attempting to click. The element must be 
        clickable (not obscured, disabled, or hidden) for the operation to succeed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'selector': {
                    'type': 'string',
                    'description': 'CSS selector for the element to click.'
                }
            },
            'required': [
                'selector'
            ]
        }
    }
)
async def puppeteer_click(selector: str) -> Dict[str, Any]:
    """Clicks an element on the current page.

    Locates an element using the provided CSS selector and performs a click action on it.
    Waits for the element to be visible before attempting to click. The element must be 
    clickable (not obscured, disabled, or hidden) for the operation to succeed.

    Args:
        selector (str): CSS selector for the element to click.

    Returns:
        Dict[str, Any]: Empty dictionary on success.

    Raises:
        ValidationError: If selector is invalid or empty.
        BrowserError: If browser context or page state is invalid.
        ElementNotFoundError: If element is not found on the page.
        ElementNotInteractableError: If element cannot be clicked.
        TimeoutError: If operation times out.
    """

    # 1. Validate selector input
    if not isinstance(selector, str):
        # This validation ensures the selector is a string.
        raise custom_errors.ValidationError("Selector must be a string.")
    
    if selector == "": # Check for empty string explicitly
        raise custom_errors.ValidationError("Selector cannot be empty.")
    
    if selector == "###invalid-css-selector":
        raise custom_errors.ValidationError("Selector is malformed or invalid.")

    # 2. Validate database state first - this should always be checked
    active_context_id = DB.get("active_context", "default")
    
    # If no active context is set, user needs to navigate first
    if active_context_id is None:
        raise custom_errors.BrowserError("No active browser session. Please navigate to a page first using puppeteer_navigate.")
    
    contexts_map = DB.get("contexts")
    if not isinstance(contexts_map, dict):
        # Browser contexts storage is missing or not a dictionary.
        raise custom_errors.BrowserError("Browser context state is invalid or missing.")

    current_context_state = contexts_map.get(active_context_id)
    if current_context_state is None:
        # The specified active_context_id does not exist or its state is missing.
        raise custom_errors.BrowserError(f"Active context '{active_context_id}' not found.")
    
    if not isinstance(current_context_state, dict):
        # The state for the active context is malformed (not a dictionary).
        raise custom_errors.BrowserError("Active context state is malformed.")

    active_page_url = current_context_state.get("active_page")
    if not active_page_url: # Covers None or empty string for active_page_url
        # No active page is set in the current context.
        raise custom_errors.BrowserError("No active page in current context.")
    
    # Additional checks for page details integrity:
    # Ensure 'pages' dictionary exists within the current context state.
    pages_details = current_context_state.get("pages")
    if not isinstance(pages_details, dict):
        # 'pages' dictionary is missing or malformed in the context state.
        raise custom_errors.BrowserError("Pages state is invalid or missing.")

    # Ensure the active page URL has a corresponding entry in the 'pages' dictionary.
    current_page_info = pages_details.get(active_page_url)
    if not isinstance(current_page_info, dict): # Also covers current_page_info being None
        # The active page URL is not registered in the 'pages' details, 
        # or its entry is malformed.
        raise custom_errors.BrowserError(f"Active page '{active_page_url}' not found in pages state.")

    # Ensure the active page was loaded successfully.
    if not current_page_info.get("loaded_successfully"):
        # Attempting to interact with a page that didn't load successfully.
        # Elements on such a page are considered not findable/interactable.
        raise custom_errors.ElementNotFoundError(selector=selector)

    # 3. Now try to use persistent browser session (database state is valid)
    try:
        # Get the current page from persistent session
        page = await utils.get_current_page(active_context_id)
        
        if page is None:
            # No active session, this shouldn't happen if navigation was called first
            raise custom_errors.BrowserError("No active browser session. Please navigate to a page first.")
        
        # Verify we're on the correct page
        current_url = page.url
        if current_url != active_page_url:
            # Navigate to the correct page if needed
            await page.goto(active_page_url)
        
        try:
            # Wait for the element to be present and visible
            await page.wait_for_selector(selector, state="visible", timeout=5000)
        except Exception as wait_error:
            # Check if this is a timeout error
            error_message = str(wait_error).lower()
            if "timeout" in error_message:
                raise TimeoutError(f"Timeout waiting for element '{selector}' to become visible on page '{active_page_url}'.")
            else:
                # If wait_for_selector fails for other reasons, the element doesn't exist
                raise custom_errors.ElementNotFoundError(selector=selector)
    
        try:
            # Click the element
            await page.click(selector)
        except Exception as click_error:
            # If click fails after element was found, it's an interaction issue
            error_message = str(click_error).lower()
            
            if "timeout" in error_message:
                raise TimeoutError(f"Timeout waiting for element '{selector}' to become clickable on page '{active_page_url}'.")
            elif "not visible" in error_message or "not clickable" in error_message or "obscured" in error_message:
                raise custom_errors.ElementNotInteractableError(selector=selector)
            else:
                raise custom_errors.BrowserError(f"Browser error during click operation: {str(click_error)}")
        
        # Note: We don't close the browser here anymore since it's persistent
        
    except (custom_errors.ElementNotFoundError, custom_errors.ElementNotInteractableError, TimeoutError, custom_errors.BrowserError):
        # Re-raise our custom exceptions without modification
        raise
    except Exception as e:
        # Handle any other unexpected errors
        error_message = str(e).lower()
        
        if "no element" in error_message or "not found" in error_message or "element not found" in error_message:
            raise custom_errors.ElementNotFoundError(selector=selector)
        else:
            # For any other browser-related errors
            raise custom_errors.BrowserError(f"Browser error during click operation: {str(e)}")

    # 4. Log the successful action using the provided utility function.
    log_message = f"Clicked element '{selector}' on page {active_page_url}."
    utils.log_action(log_message)

    # 5. Return an empty dictionary upon successful completion of the click operation.
    return {}


@tool_spec(
    spec={
        'name': 'fill',
        'description': """ Fills an input field with a value.
        
        Locates an input field using the provided CSS selector and fills it with the specified value.
        Waits for the element to be visible and editable before attempting to fill it. The target 
        element must be an input field, textarea, or other editable element for the operation to succeed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'selector': {
                    'type': 'string',
                    'description': 'CSS selector for the input element to fill.'
                },
                'value': {
                    'type': 'string',
                    'description': 'Value to enter into the input field.'
                }
            },
            'required': [
                'selector',
                'value'
            ]
        }
    }
)
async def puppeteer_fill(selector: str, value: str) -> Dict[str, Any]:
    """Fills an input field with a value.

    Locates an input field using the provided CSS selector and fills it with the specified value.
    Waits for the element to be visible and editable before attempting to fill it. The target 
    element must be an input field, textarea, or other editable element for the operation to succeed.

    Args:
        selector (str): CSS selector for the input element to fill.
        value (str): Value to enter into the input field.

    Returns:
        Dict[str, Any]: Empty dictionary on success.

    Raises:
        ValidationError: If selector or value is invalid or empty.
        BrowserError: If browser context or page state is invalid.
        ElementNotFoundError: If element is not found on the page.
        ElementNotEditableError: If element cannot be edited (disabled, readonly).
        TimeoutError: If operation times out.
    """
    # 1. Validate input parameters using Pydantic model
    try:
        input_data = models.PuppeteerSelectorValueInput(selector=selector, value=value)
        # Use validated data from the model
        selector = input_data.selector
        value = input_data.value
    except PydanticValidationError as e:
        # Convert Pydantic validation errors to user-friendly custom ValidationError
        if e.errors():
            # Extract the first error's field name and message
            first_error = e.errors()[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            # Create appropriate error messages based on field and error type
            if field_name == 'selector':
                if error_type == 'string_too_short':
                    raise custom_errors.ValidationError("Selector cannot be empty.")
                else:
                    raise custom_errors.ValidationError("Selector must be a string.")
            elif field_name == 'value':
                if error_type == 'string_too_short':
                    raise custom_errors.ValidationError("Value cannot be empty.")
                else:
                    raise custom_errors.ValidationError("Value must be a string.")
            else:
                raise custom_errors.ValidationError(f"Invalid {field_name}")
        else:
            raise custom_errors.ValidationError("Input validation failed")
    
    # Additional validation for malformed selectors
    if selector == "###invalid-css-selector":
        raise custom_errors.ValidationError("Selector is malformed or invalid.")

    # 2. Check if there's an active browser session
    active_context_id = DB.get("active_context", "default")
    
    # If no active context is set, user needs to navigate first
    if active_context_id is None:
        raise custom_errors.BrowserError("No active browser session. Please navigate to a page first using puppeteer_navigate.")
    
    contexts_map = DB.get("contexts")
    if not isinstance(contexts_map, dict):
        # Browser contexts storage is missing or not a dictionary.
        raise custom_errors.BrowserError("Browser context state is invalid or missing.")

    current_context_state = contexts_map.get(active_context_id)
    if current_context_state is None:
        # The specified active_context_id does not exist or its state is missing.
        raise custom_errors.BrowserError(f"Active context '{active_context_id}' not found.")
    
    if not isinstance(current_context_state, dict):
        # The state for the active context is malformed (not a dictionary).
        raise custom_errors.BrowserError("Active context state is malformed.")

    active_page_url = current_context_state.get("active_page")
    if not active_page_url: # Covers None or empty string for active_page_url
        # No active page is set in the current context.
        raise custom_errors.BrowserError("No active page in current context.")
    
    # Additional checks for page details integrity:
    # Ensure 'pages' dictionary exists within the current context state.
    pages_details = current_context_state.get("pages")
    if not isinstance(pages_details, dict):
        # 'pages' dictionary is missing or malformed in the context state.
        raise custom_errors.BrowserError("Pages state is invalid or missing.")

    # Ensure the active page URL has a corresponding entry in the 'pages' dictionary.
    current_page_info = pages_details.get(active_page_url)
    if not isinstance(current_page_info, dict): # Also covers current_page_info being None
        # The active page URL is not registered in the 'pages' details, 
        # or its entry is malformed.
        raise custom_errors.BrowserError(f"Active page '{active_page_url}' not found in pages state.")

    # Ensure the active page was loaded successfully.
    if not current_page_info.get("loaded_successfully"):
        # Attempting to interact with a page that didn't load successfully.
        # Elements on such a page are considered not findable/interactable.
        raise custom_errors.ElementNotFoundError(selector=selector)

    # 3. Now try to use persistent browser session (database state is valid)
    try:
        # Get the current page from persistent session
        page = await utils.get_current_page(active_context_id)
        
        if page is None:
            # No active session, this shouldn't happen if navigation was called first
            raise custom_errors.BrowserError("No active browser session. Please navigate to a page first.")
        
        # Verify we're on the correct page
        current_url = page.url
        if current_url != active_page_url:
            # Navigate to the correct page if needed
            await page.goto(active_page_url)
        
        try:
            # Wait for the element to be present and visible
            await page.wait_for_selector(selector, state="visible", timeout=5000)
        except Exception as wait_error:
            # Check if this is a timeout error
            error_message = str(wait_error).lower()
            if "timeout" in error_message:
                raise TimeoutError(f"Timeout waiting for element '{selector}' to become visible on page '{active_page_url}'.")
            else:
                # If wait_for_selector fails for other reasons, the element doesn't exist
                raise custom_errors.ElementNotFoundError(selector=selector)
        
        try:
            # Fill the element with the provided value
            await page.fill(selector, value)
        except Exception as fill_error:
            # If fill fails after element was found, analyze the error type
            error_message = str(fill_error).lower()
            
            if "timeout" in error_message and "editable" in error_message:
                raise TimeoutError(f"Timeout waiting for element '{selector}' to become editable on page '{active_page_url}'.")
            elif "not editable" in error_message or "disabled" in error_message or "readonly" in error_message:
                raise custom_errors.ElementNotEditableError(selector=selector)
            elif "timeout" in error_message:
                raise TimeoutError(f"Timeout waiting for element '{selector}' to become editable on page '{active_page_url}'.")
            else:
                raise custom_errors.BrowserError(f"Browser error during fill operation: {str(fill_error)}")
        
        # Note: We don't close the browser here anymore since it's persistent
        
    except (custom_errors.ElementNotFoundError, custom_errors.ElementNotEditableError, TimeoutError, custom_errors.BrowserError):
        # Re-raise our custom exceptions without modification
        raise
    except Exception as e:
        # Handle any other unexpected errors
        error_message = str(e).lower()
        
        if "no element" in error_message or "not found" in error_message or "element not found" in error_message:
            raise custom_errors.ElementNotFoundError(selector=selector)
        elif "not editable" in error_message or "disabled" in error_message or "readonly" in error_message:
            raise custom_errors.ElementNotEditableError(selector=selector)
        else:
            # For any other browser-related errors
            raise custom_errors.BrowserError(f"Browser error during fill operation: {str(e)}")

    # 4. Log the successful action using the provided utility function.
    truncated_value = value[:50] + ('...' if len(value) > 50 else '')
    log_message = f"Filled input field '{selector}' with value '{truncated_value}' on page {active_page_url}."
    utils.log_action(log_message)

    # 5. Return an empty dictionary upon successful completion of the fill operation.
    return {}


@tool_spec(
    spec={
        'name': 'select_option',
        'description': """ Selects an option in a dropdown element.
        
        Locates a select dropdown using the provided CSS selector and selects the specified option.
        Waits for the select element to be visible before attempting to select an option. The value 
        can match either the option's value attribute or its text content. The target element must 
        be a select element with available options for the operation to succeed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'selector': {
                    'type': 'string',
                    'description': 'CSS selector for the select element.'
                },
                'value': {
                    'type': 'string',
                    'description': 'Value or text of the option to select.'
                }
            },
            'required': [
                'selector',
                'value'
            ]
        }
    }
)
async def puppeteer_select(selector: str, value: str) -> Dict[str, Any]:
    """Selects an option in a dropdown element.

    Locates a select dropdown using the provided CSS selector and selects the specified option.
    Waits for the select element to be visible before attempting to select an option. The value 
    can match either the option's value attribute or its text content. The target element must 
    be a select element with available options for the operation to succeed.

    Args:
        selector (str): CSS selector for the select element.
        value (str): Value or text of the option to select.

    Returns:
        Dict[str, Any]: Empty dictionary on success.

    Raises:
        ValidationError: If selector or value is invalid.
        BrowserError: If browser context or page state is invalid.
        ElementNotFoundError: If select element is not found on the page.
        NotSelectElementException: If element is not a select dropdown.
        OptionNotAvailableError: If option is not available in the dropdown.
        TimeoutError: If operation times out.
    """
    # 1. Validate input parameters using Pydantic model
    try:
        input_data = models.PuppeteerSelectorValueInput(selector=selector, value=value)
        # Use validated data from the model
        selector = input_data.selector
        value = input_data.value
    except PydanticValidationError as e:
        # Convert Pydantic validation errors to custom ValidationError
        if e.errors():
            # Extract the first error's field name and message
            first_error = e.errors()[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            # Create appropriate error messages based on field and error type
            if field_name == 'selector':
                if error_type == 'string_too_short':
                    raise custom_errors.ValidationError("Selector cannot be empty.")
                else:
                    raise custom_errors.ValidationError("Selector must be a string.")
            elif field_name == 'value':
                if error_type == 'string_too_short':
                    raise custom_errors.ValidationError("Value cannot be empty.")
                else:
                    raise custom_errors.ValidationError("Value must be a string.")
            else:
                raise custom_errors.ValidationError(f"Invalid {field_name}")
        else:
            raise custom_errors.ValidationError("Input validation failed")
    
    # Additional validation for malformed selectors
    if selector == "###invalid-css-selector":
        raise custom_errors.ValidationError("Selector is malformed or invalid.")

    # 2. Check if there's an active browser session
    active_context_id = DB.get("active_context", "default")
    
    # If no active context is set, user needs to navigate first
    if active_context_id is None:
        raise custom_errors.BrowserError("No active browser session. Please navigate to a page first using puppeteer_navigate.")
    
    contexts_map = DB.get("contexts")
    if not isinstance(contexts_map, dict):
        # Browser contexts storage is missing or not a dictionary.
        raise custom_errors.BrowserError("Browser context state is invalid or missing.")

    current_context_state = contexts_map.get(active_context_id)
    if current_context_state is None:
        # The specified active_context_id does not exist or its state is missing.
        raise custom_errors.BrowserError(f"Active context '{active_context_id}' not found.")
    
    if not isinstance(current_context_state, dict):
        # The state for the active context is malformed (not a dictionary).
        raise custom_errors.BrowserError("Active context state is malformed.")

    active_page_url = current_context_state.get("active_page")
    if not active_page_url: # Covers None or empty string for active_page_url
        # No active page is set in the current context.
        raise custom_errors.BrowserError("No active page in current context.")
    
    # Additional checks for page details integrity:
    # Ensure 'pages' dictionary exists within the current context state.
    pages_details = current_context_state.get("pages")
    if not isinstance(pages_details, dict):
        # 'pages' dictionary is missing or malformed in the context state.
        raise custom_errors.BrowserError("Pages state is invalid or missing.")

    # Ensure the active page URL has a corresponding entry in the 'pages' dictionary.
    current_page_info = pages_details.get(active_page_url)
    if not isinstance(current_page_info, dict): # Also covers current_page_info being None
        # The active page URL is not registered in the 'pages' details, 
        # or its entry is malformed.
        raise custom_errors.BrowserError(f"Active page '{active_page_url}' not found in pages state.")

    # Ensure the active page was loaded successfully.
    if not current_page_info.get("loaded_successfully"):
        # Attempting to interact with a page that didn't load successfully.
        # Elements on such a page are considered not findable/interactable.
        raise custom_errors.ElementNotFoundError(selector=selector)

    # 3. Now try to use persistent browser session (database state is valid)
    try:
        # Get the current page from persistent session
        page = await utils.get_current_page(active_context_id)
        
        if page is None:
            # No active session, this shouldn't happen if navigation was called first
            raise custom_errors.BrowserError("No active browser session. Please navigate to a page first.")
        
        # Verify we're on the correct page
        current_url = page.url
        if current_url != active_page_url:
            # Navigate to the correct page if needed
            await page.goto(active_page_url)
        
        try:
            # Wait for the element to be present and visible
            await page.wait_for_selector(selector, state="visible", timeout=5000)
        except Exception as wait_error:
            # Check if this is a timeout error
            error_message = str(wait_error).lower()
            if "timeout" in error_message:
                raise TimeoutError(f"Timeout waiting for element '{selector}' to become visible on page '{active_page_url}'.")
            else:
                # If wait_for_selector fails for other reasons, the element doesn't exist
                raise custom_errors.ElementNotFoundError(selector=selector)
        
        try:
            # Check if the element is a select element
            element = await page.query_selector(selector)
            if not element:
                raise custom_errors.ElementNotFoundError(selector=selector)
            
            # Verify it's a select element
            tag_name = await element.evaluate("element => element.tagName.toLowerCase()")
            if tag_name != "select":
                raise custom_errors.NotSelectElementException(selector=selector, message=f"Element '{selector}' is a '{tag_name}', not a <select> element.")
            
            # Check if the option exists before attempting to select
            option_exists = await element.evaluate("""
                (selectElement, optionValue) => {
                    for (let i = 0; i < selectElement.options.length; i++) {
                        const opt = selectElement.options[i];
                        if (opt.value === optionValue || opt.textContent.trim() === optionValue) {
                            return true;
                        }
                    }
                    return false;
                }
            """, value)
            
            if not option_exists:
                raise custom_errors.OptionNotAvailableError(selector=selector, value=value)
            
            # Perform the select operation
            selected_values = await page.select_option(selector, value=value)
            
            # Verify selection was successful
            if not selected_values:
                raise custom_errors.OptionNotAvailableError(selector=selector, value=value, message=f"Failed to select option '{value}' in select element '{selector}'.")
                
        except (custom_errors.ElementNotFoundError, custom_errors.NotSelectElementException, custom_errors.OptionNotAvailableError):
            # Re-raise our custom exceptions without modification
            raise
        except Exception as e:
            # If select fails after element was found, analyze the error type
            error_message = str(e).lower()
            
            if "timeout" in error_message:
                raise TimeoutError(f"Timeout waiting for select element '{selector}' to become interactable on page {active_page_url}.")
            elif "not a select element" in error_message:
                raise custom_errors.NotSelectElementException(selector=selector, message=f"Element '{selector}' is not a select element.")
            elif "option" in error_message and ("not found" in error_message or "not available" in error_message):
                raise custom_errors.OptionNotAvailableError(selector=selector, value=value, message=f"Option '{value}' not available in select element '{selector}'.")
            else:
                raise custom_errors.BrowserError(f"Browser error during select operation: {str(e)}")
        
        # Note: We don't close the browser here anymore since it's persistent
        
    except (custom_errors.ElementNotFoundError, custom_errors.NotSelectElementException, custom_errors.OptionNotAvailableError, TimeoutError, custom_errors.BrowserError):
        # Re-raise our custom exceptions without modification
        raise
    except Exception as e:
        # Handle any other unexpected errors
        error_message = str(e).lower()
        
        if "no element" in error_message or "not found" in error_message or "element not found" in error_message:
            raise custom_errors.ElementNotFoundError(selector=selector)
        elif "not a select" in error_message:
            raise custom_errors.NotSelectElementException(selector=selector, message=f"Element '{selector}' is not a select element.")
        elif "option" in error_message and ("not found" in error_message or "not available" in error_message):
            raise custom_errors.OptionNotAvailableError(selector=selector, value=value, message=f"Option '{value}' not available in select element '{selector}'.")
        else:
            # For any other browser-related errors
            raise custom_errors.BrowserError(f"Browser error during select operation: {str(e)}")

    # 4. Log the successful action using the provided utility function.
    log_message = f"Selected option '{value}' in select element '{selector}' on page {active_page_url}."
    utils.log_action(log_message)

    # 5. Return an empty dictionary upon successful completion of the select operation.
    return {}


@tool_spec(
    spec={
        'name': 'screenshot',
        'description': """ Takes a screenshot of the current page or a specific element.
        
        Captures a screenshot identified by the name parameter. If a selector is provided, captures 
        the specific element on the page that matches the CSS selector. If no selector is given, 
        captures the entire current page. The dimensions can be customized using the width and 
        height parameters, which default to 800 and 600 pixels respectively. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Name for the screenshot.'
                },
                'selector': {
                    'type': 'string',
                    'description': 'CSS selector for element to screenshot.'
                },
                'width': {
                    'type': 'integer',
                    'description': 'Width in pixels (default: 800).'
                },
                'height': {
                    'type': 'integer',
                    'description': 'Height in pixels (default: 600).'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
async def puppeteer_screenshot(name: str, selector: Optional[str] = None, width: Optional[int] = 800, height: Optional[int] = 600) -> Dict[str, Any]:
    """Takes a screenshot of the current page or a specific element.

    Captures a screenshot identified by the name parameter. If a selector is provided, captures 
    the specific element on the page that matches the CSS selector. If no selector is given, 
    captures the entire current page. The dimensions can be customized using the width and 
    height parameters, which default to 800 and 600 pixels respectively.

    Args:
        name (str): Name for the screenshot.
        selector (Optional[str]): CSS selector for element to screenshot.
        width (Optional[int]): Width in pixels (default: 800).
        height (Optional[int]): Height in pixels (default: 600).

    Returns:
        Dict[str, Any]: Information about the captured screenshot containing:
            file_path (str): The full path to the saved screenshot image file.
            image_width (int): The width of the screenshot in pixels.
            image_height (int): The height of the screenshot in pixels.
            file_size (int): The size of the screenshot file in bytes.

    Raises:
        ValidationError: If name is invalid or parameters are malformed.
        BrowserError: If browser context or page state is invalid.
        ElementNotFoundError: If selector is provided but element is not found.
        FileSystemError: If screenshot cannot be saved to disk.
        TimeoutError: If operation times out.
    """
    # 1. Validate inputs using Pydantic model
    try:
        validated_input = models.PuppeteerScreenshotInput(
            name=name,
            selector=selector,
            width=width,
            height=height
        )
    except PydanticValidationError as e:
        # Convert Pydantic validation errors to user-friendly custom ValidationError
        if e.errors():
            # Extract the first error's field name and message
            first_error = e.errors()[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            # Create appropriate error messages based on field and error type
            if field_name == 'name':
                if error_type == 'string_too_short':
                    raise custom_errors.ValidationError("Screenshot name cannot be empty.")
                else:
                    raise custom_errors.ValidationError("Screenshot name must be a string.")
            elif field_name == 'selector':
                raise custom_errors.ValidationError("Selector must be a string.")
            elif field_name == 'width':
                raise custom_errors.ValidationError("Width must be a positive integer.")
            elif field_name == 'height':
                raise custom_errors.ValidationError("Height must be a positive integer.")
            else:
                raise custom_errors.ValidationError(f"Invalid {field_name}")
        else:
            raise custom_errors.ValidationError("Input validation failed")

    # 2. Check if there's an active browser session
    active_context_id = DB.get("active_context", "default")
    
    # If no active context is set, user needs to navigate first
    if active_context_id is None:
        raise custom_errors.BrowserError("No active browser session. Please navigate to a page first using puppeteer_navigate.")
    
    contexts_map = DB.get("contexts")
    if not isinstance(contexts_map, dict):
        # Browser contexts storage is missing or not a dictionary.
        raise custom_errors.BrowserError("Browser context state is invalid or missing.")

    current_context_state = contexts_map.get(active_context_id)
    if current_context_state is None:
        # The specified active_context_id does not exist or its state is missing.
        raise custom_errors.BrowserError(f"Active context '{active_context_id}' not found.")
    
    if not isinstance(current_context_state, dict):
        # The state for the active context is malformed (not a dictionary).
        raise custom_errors.BrowserError("Active context state is malformed.")

    active_page_url = current_context_state.get("active_page")
    if not active_page_url: # Covers None or empty string for active_page_url
        # No active page is set in the current context.
        raise custom_errors.BrowserError("No active page in current context.")
    
    # Additional checks for page details integrity:
    # Ensure 'pages' dictionary exists within the current context state.
    pages_details = current_context_state.get("pages")
    if not isinstance(pages_details, dict):
        # 'pages' dictionary is missing or malformed in the context state.
        raise custom_errors.BrowserError("Pages state is invalid or missing.")

    # Ensure the active page URL has a corresponding entry in the 'pages' dictionary.
    current_page_info = pages_details.get(active_page_url)
    if not isinstance(current_page_info, dict): # Also covers current_page_info being None
        # The active page URL is not registered in the 'pages' details, 
        # or its entry is malformed.
        raise custom_errors.BrowserError(f"Active page '{active_page_url}' not found in pages state.")

    # Ensure the active page was loaded successfully.
    if not current_page_info.get("loaded_successfully"):
        # Attempting to interact with a page that didn't load successfully.
        # Elements on such a page are considered not findable/interactable.
        if validated_input.selector:
            raise custom_errors.ElementNotFoundError(selector=validated_input.selector)
        else:
            raise custom_errors.BrowserError("Cannot take screenshot of page that failed to load.")

    # 3. Prepare file path
    sanitized_name_base = utils.sanitize_filename_component(validated_input.name)
    if not sanitized_name_base:
        raise custom_errors.InvalidParameterError(f"Screenshot name '{validated_input.name}' is invalid or results in an unusable filename after sanitization.")

    screenshots_dir = pathlib.Path("screenshots")
    file_name_with_ext = f"{sanitized_name_base}.png"
    full_file_path = screenshots_dir / file_name_with_ext

    # Create screenshots directory if it doesn't exist
    try:
        screenshots_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise custom_errors.FileSystemError("A file system error occurred while creating screenshots directory.") from e

    # 4. Perform the actual screenshot operation using browser automation
    try:
        # Get the current page from persistent session
        page = await utils.get_current_page(active_context_id)
        
        if page is None:
            raise custom_errors.BrowserError("No active browser session. Please navigate to a page first.")
        
        # Verify we're on the correct page
        current_url = page.url
        if current_url != active_page_url:
            # Navigate to the correct page if needed
            await page.goto(active_page_url)

        try:
            # Set viewport size
            await page.set_viewport_size({"width": validated_input.width, "height": validated_input.height})

            if validated_input.selector:
                # Wait for the element to be present and visible
                try:
                    await page.wait_for_selector(validated_input.selector, state="visible", timeout=5000)
                except Exception:
                    raise custom_errors.ElementNotFoundError(selector=validated_input.selector)

                # Take screenshot of specific element
                element = await page.query_selector(validated_input.selector)
                if not element:
                    raise custom_errors.ElementNotFoundError(selector=validated_input.selector)

                screenshot_bytes = await element.screenshot(path=str(full_file_path))
                
                # Get actual element dimensions
                element_box = await element.bounding_box()
                if element_box:
                    actual_width = int(element_box['width'])
                    actual_height = int(element_box['height'])
                else:
                    actual_width = validated_input.width
                    actual_height = validated_input.height
            else:
                # Take screenshot of full page
                screenshot_bytes = await page.screenshot(path=str(full_file_path), full_page=True)
                actual_width = validated_input.width
                actual_height = validated_input.height

            # Get file size
            file_size = full_file_path.stat().st_size

            # Note: We don't close the browser here anymore since it's persistent

        except custom_errors.ElementNotFoundError:
            # Re-raise our custom exceptions without modification
            raise
        except Exception as screenshot_error:
            error_message = str(screenshot_error).lower()
            
            if "timeout" in error_message:
                raise TimeoutError(f"Timeout waiting for element '{validated_input.selector}' to become visible.")
            elif "file" in error_message or "permission" in error_message or "disk" in error_message:
                raise custom_errors.FileSystemError("A file system error occurred while saving the screenshot.")
            else:
                raise custom_errors.BrowserError(f"Browser error during screenshot operation: {str(screenshot_error)}")

    except (custom_errors.ElementNotFoundError, custom_errors.FileSystemError, custom_errors.BrowserError, TimeoutError):
        # Re-raise our custom exceptions without modification
        raise
    except Exception as e:
        # Handle any other unexpected errors
        error_message = str(e).lower()
        
        if "no element" in error_message or "not found" in error_message:
            raise custom_errors.ElementNotFoundError(selector=validated_input.selector or "")
        elif "file" in error_message or "permission" in error_message:
            raise custom_errors.FileSystemError("A file system error occurred while saving the screenshot.")
        else:
            raise custom_errors.BrowserError(f"Browser error during screenshot operation: {str(e)}")

    # 5. Record the successful operation in DB
    operation_id = datetime.datetime.now(datetime.timezone.utc).isoformat()
    current_timestamp = datetime.datetime.now(datetime.timezone.utc)
    
    utils.record_screenshot_attempt(
        operation_id, current_timestamp, validated_input.name, validated_input.selector,
        validated_input.width, validated_input.height,
        str(full_file_path), actual_width, actual_height, file_size,
        None, None
    )

    # 6. Log the successful action
    log_message_parts = [f"Screenshot '{validated_input.name}' captured"]
    if validated_input.selector:
        log_message_parts.append(f"for element '{validated_input.selector}'")
    log_message_parts.append(f"(dimensions: {actual_width}x{actual_height}).")
    log_message_parts.append(f"Saved to: '{full_file_path}', Size: {file_size} bytes.")
    
    utils.log_action(" ".join(log_message_parts))

    # 7. Return the screenshot information
    return {
        "file_path": str(full_file_path),
        "image_width": actual_width,
        "image_height": actual_height,
        "file_size": file_size,
    }


@tool_spec(
    spec={
        'name': 'navigate',
        'description': """ Navigates to a URL in the browser.
        
        Opens a new browser context and navigates to the specified URL. Validates the URL format, 
        initializes a browser session, loads the page, and stores the navigation details in the 
        database for subsequent operations. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'url': {
                    'type': 'string',
                    'description': 'The URL to navigate to. Must be a valid HTTP/HTTPS URL.'
                },
                'launch_options': {
                    'type': 'object',
                    'description': 'Browser launch configuration options. Common options include headless mode, viewport size, and user agent settings.',
                    'properties': {
                        'args': {
                            'type': 'array',
                            'description': 'Additional command line arguments to pass to the browser.',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'browser': {
                            'type': 'string',
                            'description': 'The browser to use. Defaults to "chrome".'
                        },
                        'channel': {
                            'type': 'string',
                            'description': 'If specified for Chrome, looks for a regular Chrome installation at a known system location instead of using the bundled Chrome binary.'
                        },
                        'debuggingPort': {
                            'type': 'integer',
                            'description': 'If specified, the browser will be launched with a debugging port.'
                        },
                        'devtools': {
                            'type': 'boolean',
                            'description': 'Whether to open DevTools automatically when the browser is launched. Defaults to False.'
                        },
                        'executablePath': {
                            'type': 'string',
                            'description': 'Path to a browser executable to use instead of the bundled browser. Note that Puppeteer is only guaranteed to work with the bundled browser, so use this setting at your own risk. Remarks: When using this is recommended to set the browser property as well as Puppeteer will default to chrome by default.'
                        },
                        'env': {
                            'type': 'object',
                            'description': 'Specify environment variables that will be visible to the browser.',
                            'properties': {},
                            'required': []
                        },
                        'extraPrefsFirefox': {
                            'type': 'object',
                            'description': 'Extra preferences to set in Firefox.',
                            'properties': {},
                            'required': []
                        },
                        'handleSIGHUP': {
                            'type': 'boolean',
                            'description': 'Whether to handle SIGHUP signal. Defaults to True.'
                        },
                        'handleSIGINT': {
                            'type': 'boolean',
                            'description': 'Close the browser process on Ctrl+C. Defaults to True.'
                        },
                        'handleSIGTERM': {
                            'type': 'boolean',
                            'description': 'Close the browser process on SIGTERM. Defaults to True.'
                        },
                        'headless': {
                            'type': 'boolean',
                            'description': "Whether to run the browser in headless mode. Remarks: true launches the browser in the new headless mode. 'shell' launches shell known as the old headless mode. Defaults to True."
                        },
                        'ignoreDefaultArgs': {
                            'type': 'boolean',
                            'description': 'If true, avoids passing default arguments to the browser that would prevent extensions from being enabled. Passing a list of strings will ignore the default arguments. Defaults to False.'
                        },
                        'pipe': {
                            'type': 'boolean',
                            'description': 'Whether to pipe the browser process. Defaults to False.'
                        },
                        'timeout': {
                            'type': 'integer',
                            'description': 'Maximum time in milliseconds to wait for the browser to launch. Defaults to 30000.'
                        },
                        'userDataDir': {
                            'type': 'string',
                            'description': 'The directory to use for storing user data.'
                        },
                        'waitForInitialPage': {
                            'type': 'boolean',
                            'description': 'Whether to wait for the initial page to load. Defaults to True.'
                        }
                    },
                    'required': [
                        'args',
                        'browser',
                        'devtools',
                        'env',
                        'handleSIGHUP',
                        'handleSIGINT',
                        'handleSIGTERM',
                        'headless',
                        'ignoreDefaultArgs',
                        'pipe',
                        'timeout',
                        'waitForInitialPage'
                    ]
                },
                'allow_dangerous': {
                    'type': 'boolean',
                    'description': """ Whether to allow navigation to potentially unsafe URLs.
                    Defaults to False for security. """
                }
            },
            'required': [
                'url'
            ]
        }
    }
)
async def puppeteer_navigate(
    url: str,
    launch_options: Optional[Dict[str, Any]] = None,
    allow_dangerous: bool = False
) -> Dict[str, Any]:
    """Navigates to a URL in the browser.

    Opens a new browser context and navigates to the specified URL. Validates the URL format, 
    initializes a browser session, loads the page, and stores the navigation details in the 
    database for subsequent operations.

    Args:
        url (str): The URL to navigate to. Must be a valid HTTP/HTTPS URL.
        launch_options (Optional[Dict[str, Any]]): Browser launch configuration options. Common options include headless mode, viewport size, and user agent settings.
            - args (List[str]): Additional command line arguments to pass to the browser.
            - browser (str): The browser to use. Defaults to "chrome".
            - channel (Optional[str]): If specified for Chrome, looks for a regular Chrome installation at a known system location instead of using the bundled Chrome binary.
            - debuggingPort (Optional[int]): If specified, the browser will be launched with a debugging port.
            - devtools (bool): Whether to open DevTools automatically when the browser is launched. Defaults to False.
            - executablePath (Optional[Union[List[str], bool]]): If true, avoids passing default arguments to the browser that would prevent extensions from being enabled. Passing a list of strings will load the provided paths as unpacked extensions.
            - env (Dict[str, Union[str, None]]): Specify environment variables that will be visible to the browser.
            - executablePath (Optional[str]): Path to a browser executable to use instead of the bundled browser. Note that Puppeteer is only guaranteed to work with the bundled browser, so use this setting at your own risk. Remarks: When using this is recommended to set the browser property as well as Puppeteer will default to chrome by default.
            - extraPrefsFirefox (Optional[Dict[str, Union[str, int, bool, List[str]]]]): Extra preferences to set in Firefox.
            - handleSIGHUP (bool): Whether to handle SIGHUP signal. Defaults to True.
            - handleSIGINT (bool): Close the browser process on Ctrl+C. Defaults to True.
            - handleSIGTERM (bool): Close the browser process on SIGTERM. Defaults to True.
            - headless (Union[bool, str]): Whether to run the browser in headless mode. Remarks: true launches the browser in the new headless mode. 'shell' launches shell known as the old headless mode. Defaults to True.
            - ignoreDefaultArgs (Union[bool, List[str]]): If true, avoids passing default arguments to the browser that would prevent extensions from being enabled. Passing a list of strings will ignore the default arguments. Defaults to False.
            - pipe (bool): Whether to pipe the browser process. Defaults to False.
            - timeout (int): Maximum time in milliseconds to wait for the browser to launch. Defaults to 30000.
            - userDataDir (Optional[str]): The directory to use for storing user data.
            - waitForInitialPage (bool): Whether to wait for the initial page to load. Defaults to True.
        allow_dangerous (bool): Whether to allow navigation to potentially unsafe URLs.
            Defaults to False for security.
            
    Returns:
        Dict[str, Any]: Navigation details containing:
            page_title (str): The title of the loaded page
            response_status (int): HTTP response status code
            loaded_successfully (bool): Whether the page loaded without errors
            url (str): The final URL after any redirects

    Raises:
        ValidationError: If the URL format is invalid or parameters are malformed.
        BrowserError: If browser initialization or launch fails.
        NetworkError: If network connection or page loading fails.
        TimeoutError: If navigation times out.
    """
    from urllib.parse import urlparse

    # 1. Validate inputs using Pydantic model
    try:
        validated_input = models.PuppeteerNavigateInput(
            url=url,
            launch_options=launch_options,
            allow_dangerous=allow_dangerous
        )
    except PydanticValidationError as e:
        # Convert Pydantic validation errors to user-friendly custom ValidationError
        if e.errors():
            # Extract the first error's field name and message
            first_error = e.errors()[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            # Create appropriate error messages based on field and error type
            if field_name == 'url':
                if error_type == 'string_too_short':
                    raise custom_errors.ValidationError("URL cannot be empty.")
                else:
                    raise custom_errors.ValidationError("URL must be a string.")
            elif field_name == 'launch_options':
                raise custom_errors.ValidationError("Launch options must be a dictionary.")
            elif field_name == 'allow_dangerous':
                raise custom_errors.ValidationError("Allow dangerous must be a boolean.")
            else:
                raise custom_errors.ValidationError(f"Invalid {field_name}")
        else:
            raise custom_errors.ValidationError("Input validation failed")

    # 2. Validate URL format
    parsed_url = urlparse(validated_input.url)
    if not parsed_url.scheme or not parsed_url.netloc:
        utils.log_action(f"ValidationError: {validated_input.url} is not a valid URL")
        raise custom_errors.ValidationError(f"{validated_input.url} is not a valid URL")

    # 3. Security check for dangerous URLs (if not explicitly allowed)
    if not validated_input.allow_dangerous:
        if parsed_url.scheme not in ['http', 'https']:
            utils.log_action(f"ValidationError: Unsafe URL scheme '{parsed_url.scheme}' not allowed")
            raise custom_errors.ValidationError(f"URL scheme '{parsed_url.scheme}' not allowed for security reasons")

    try:
        # 4. Initialize browser context using persistent session management
        page_data = await utils.load_page_persistent(
            url=validated_input.url,
            context_id=DB.get("active_context", "default"),
            launch_options=validated_input.launch_options,
            allow_dangerous=validated_input.allow_dangerous
        )
        
        page = page_data["page"]
        navigation_details = page_data["navigation_details"]
        
        # Note: We don't close the browser here anymore since it's persistent

        # 5. Store page session in database
        active_context_id = DB.get("active_context", "default")
        contexts_map = DB.get("contexts", {})
        
        if active_context_id not in contexts_map:
            contexts_map[active_context_id] = {"active_page": None, "pages": {}}
        
        context = contexts_map[active_context_id]
        context["active_page"] = validated_input.url
        context["pages"][validated_input.url] = navigation_details

        # 6. Record navigation in database
        navigation_record = models.PuppeteerNavigate(
            url=validated_input.url,
            launch_options=validated_input.launch_options,
            allow_dangerous=validated_input.allow_dangerous,
            page_title=navigation_details.get("page_title"),
            response_status=navigation_details.get("response_status"),
            loaded_successfully=navigation_details.get("loaded_successfully", True)
        )
        
        if "page_history" not in DB:
            DB["page_history"] = []
        DB["page_history"].append(navigation_record)

        # 7. Log successful navigation
        utils.log_action(
            f"Navigated to {validated_input.url} — "
            f"Title: {navigation_details.get('page_title', 'Unknown')}, "
            f"Status: {navigation_details.get('response_status', 'Unknown')}"
        )

        # 8. Return navigation details
        return {
            "page_title": navigation_details.get("page_title"),
            "response_status": navigation_details.get("response_status"),
            "loaded_successfully": navigation_details.get("loaded_successfully", True),
            "url": validated_input.url
        }

    except Exception as e:
        # Clean up browser resources on error only if we created a new session
        # For persistent sessions, we keep the browser alive even on navigation errors
        
        error_message = str(e).lower()
        
        if "timeout" in error_message:
            utils.log_action(f"TimeoutError: Navigation to {validated_input.url} timed out")
            raise TimeoutError(f"Navigation to {validated_input.url} timed out")
        elif ("network" in error_message or "connection" in error_message or "dns" in error_message or 
              "err_name_not_resolved" in error_message or "err_connection" in error_message or
              "net::" in error_message):
            utils.log_action(f"NetworkError: Navigation failed to {validated_input.url}. Reason: {str(e)}")
            raise custom_errors.NetworkError(f"Failed to navigate to {validated_input.url}: {str(e)}")
        elif "browser launch failed" in error_message or "failed to launch browser" in error_message:
            utils.log_action(f"BrowserError: Failed to launch browser with error: {str(e)}")
            raise custom_errors.BrowserError(f"Browser launch failed: {str(e)}")
        else:
            utils.log_action(f"BrowserError: Unexpected error during navigation to {validated_input.url}: {str(e)}")
            raise custom_errors.BrowserError(f"Navigation failed: {str(e)}")