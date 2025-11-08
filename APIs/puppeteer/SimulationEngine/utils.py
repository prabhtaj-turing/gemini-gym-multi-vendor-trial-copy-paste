import os
import datetime
import re
import pathlib
from typing import Dict, Any, List, Optional
from playwright.async_api import async_playwright
from .db import DB 

# Global browser session management
_browser_sessions = {}

def log_action(message: str) -> None:
    """
    Logs an action message with a timestamp to the global DB instance's logs.

    Args:
        message: The message describing the action to log.

    Returns:
        None
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    DB["logs"].append(log_entry)

async def get_or_create_browser_session(context_id="default", launch_options=None, allow_dangerous=False):
    """
    Get existing browser session or create a new one if it doesn't exist.
    This maintains persistent browser instances across operations.
    
    Args:
        context_id: Identifier for the browser context
        launch_options: Browser launch options
        allow_dangerous: Whether to allow dangerous browser arguments
        
    Returns:
        Tuple of (browser, playwright_instance, page) where page is the current active page
    """
    global _browser_sessions
    
    # Check if we have an existing session
    if context_id in _browser_sessions:
        session = _browser_sessions[context_id]
        browser = session["browser"]
        playwright_instance = session["playwright"]
        
        # Check if browser is still connected
        try:
            # Try to get browser contexts to test if browser is alive
            contexts = browser.contexts
            if contexts:
                # Get the active page from the database
                active_context_id = DB.get("active_context", "default")
                contexts_map = DB.get("contexts", {})
                current_context_state = contexts_map.get(active_context_id, {})
                active_page_url = current_context_state.get("active_page")
                
                if active_page_url:
                    # Try to find existing page with this URL
                    for context in contexts:
                        for page in context.pages:
                            if page.url == active_page_url:
                                return browser, playwright_instance, page
                
                # If no existing page found, create a new one
                if contexts:
                    context = contexts[0]
                    page = await context.new_page()
                    if active_page_url:
                        await page.goto(active_page_url)
                    return browser, playwright_instance, page
            else:
                # No contexts exist, create a new one
                context = await browser.new_context()
                page = await context.new_page()
                
                # Update session with new context and page
                _browser_sessions[context_id]["context"] = context
                _browser_sessions[context_id]["page"] = page
                
                return browser, playwright_instance, page
                    
        except Exception:
            # Browser session is dead, remove it and create new one
            try:
                await browser.close()
                await playwright_instance.stop()
            except:
                pass
            del _browser_sessions[context_id]
    
    # Create new browser session
    playwright_instance = await async_playwright().start()
    
    # Handle dangerous arguments
    args = launch_options.get("args", []) if launch_options else []
    if not allow_dangerous:
        for a in args:
            if "no-sandbox" in a or "disable-web-security" in a:
                raise ValueError("Dangerous args blocked by default.")
    
    browser = await playwright_instance.chromium.launch(**launch_options) if launch_options else await playwright_instance.chromium.launch()
    
    # Create browser context and initial page
    context = await browser.new_context()
    page = await context.new_page()
    
    # Store the session
    _browser_sessions[context_id] = {
        "browser": browser,
        "playwright": playwright_instance,
        "context": context,
        "page": page
    }
    
    return browser, playwright_instance, page

async def get_current_page(context_id="default"):
    """
    Get the current active page for the given context.
    
    Args:
        context_id: Browser context identifier
        
    Returns:
        The current page object, or None if no session exists
    """
    global _browser_sessions
    
    if context_id not in _browser_sessions:
        return None
        
    session = _browser_sessions[context_id]
    return session.get("page")

async def close_browser_session(context_id="default"):
    """
    Close and cleanup a browser session.
    
    Args:
        context_id: Browser context identifier
    """
    global _browser_sessions
    
    if context_id in _browser_sessions:
        session = _browser_sessions[context_id]
        try:
            await session["browser"].close()
            await session["playwright"].stop()
        except:
            pass
        del _browser_sessions[context_id]

async def close_all_browser_sessions():
    """Close all active browser sessions."""
    global _browser_sessions
    
    for context_id in list(_browser_sessions.keys()):
        await close_browser_session(context_id)

# Keep the original functions for backward compatibility
async def init_browser_context(launch_options=None, allow_dangerous=False):
    """
    DEPRECATED: Use get_or_create_browser_session instead.
    This function is kept for backward compatibility but creates new instances each time.
    """
    p = await async_playwright().start()
    
    args = launch_options.get("args", []) if launch_options else []
    if not allow_dangerous:
        for a in args:
            if "no-sandbox" in a or "disable-web-security" in a:
                raise ValueError("Dangerous args blocked by default.")
    
    browser = await p.chromium.launch(**launch_options) if launch_options else await p.chromium.launch()
    return browser, p

async def load_page(browser_or_context, url: str):
    """
    Load a page in the browser or context. This function now tries to reuse existing pages when possible.
    Can accept either a browser or context object.
    """
    # Check if we received a browser or context
    if hasattr(browser_or_context, 'contexts'):
        # It's a browser
        browser = browser_or_context
        # Try to find an existing page with this URL
        for context in browser.contexts:
            for page in context.pages:
                if page.url == url:
                    return page
        
        # Create new page if none exists
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
        
        page = await context.new_page()
        response = await page.goto(url)
        
        return page
    else:
        # It's a context
        context = browser_or_context
        # Try to find an existing page with this URL
        for page in context.pages:
            if page.url == url:
                return page
        
        # Create new page
        page = await context.new_page()
        response = await page.goto(url)
        
        return page

async def load_page_persistent(url: str, context_id="default", launch_options=None, allow_dangerous=False):
    """
    Load a page using persistent browser session management.
    This is the new recommended way to load pages.
    
    Args:
        url: URL to navigate to
        context_id: Browser context identifier
        launch_options: Browser launch options
        allow_dangerous: Whether to allow dangerous browser arguments
        
    Returns:
        Dictionary with page and navigation details
    """
    browser, playwright_instance, page = await get_or_create_browser_session(
        context_id=context_id,
        launch_options=launch_options,
        allow_dangerous=allow_dangerous
    )
    
    # Navigate to the URL
    response = await page.goto(url)
    
    return {
        "page": page,
        "browser": browser,
        "playwright": playwright_instance,
        "navigation_details": {
            "page_title": await page.title(),
            "response_status": response.status if response else 0,
            "loaded_successfully": response.ok if response else False
        }
    }

def update_browser_state_from_navigation(nav_details_dict: Dict[str, Any]) -> None:
    """
    Updates the global DB's current context based on navigation details
    and records the navigation in page_history.

    Args:
        nav_details_dict: A dictionary containing navigation information,
                          expected to have keys like 'url', 'page_title',
                          'loaded_successfully', 'timestamp', and optionally 'error' and 'id'.
    """
    active_context_id = DB.get("active_context", "default")
    # Ensure contexts structure exists
    contexts_map = DB.setdefault("contexts", {})
    context = contexts_map.setdefault(active_context_id, {})
    
    context.setdefault("pages", {}) # Ensure pages dict within context exists

    if nav_details_dict.get("loaded_successfully"):
        current_url = nav_details_dict.get("url")
        context["active_page"] = current_url
        page_title = nav_details_dict.get("page_title")
        if current_url and page_title is not None:
            # Store page title under its URL in the 'pages' dictionary
            context["pages"][current_url] = {"page_title": page_title}
    # If navigation failed, active_page and title for that URL are not updated here,
    # preserving the last known good state for active_page or relying on caller logic.

    # Add to page_history
    page_history_list = DB.setdefault("page_history", [])
    
    history_entry = {
        "url": nav_details_dict.get("url"),
        "page_title": nav_details_dict.get("page_title"),
        "timestamp": nav_details_dict.get("timestamp", datetime.datetime.now().isoformat()),
        "loaded_successfully": nav_details_dict.get("loaded_successfully", False),
        "error": nav_details_dict.get("error") # Will be None if 'error' key is missing
    }
    # If an 'id' is provided in nav_details_dict (e.g. from the navigate operation), include it.
    if "id" in nav_details_dict:
        history_entry["id"] = nav_details_dict["id"]
        
    page_history_list.append(history_entry)

def get_operation_by_id(operation_id: str, operation_action_type: str) -> Optional[Dict[str, Any]]:
    """
    Fetches a specific operation record from the DB by its ID and action type.
    Supported action types: "navigate", "screenshot".
    Note: "evaluate" operations are not directly retrievable by ID via this function
    as DB["script_results"] stores only the results, not the full operation with ID.

    Args:
        operation_id: The ID of the operation to retrieve.
        operation_action_type: The type of the operation (e.g., "navigate", "screenshot").

    Returns:
        The matching operation dictionary, or None if not found.
    """
    if not operation_id:
        return None

    source_list_key_map = {
        "navigate": "page_history",
        "screenshot": "screenshots"
        # Add more mappings if other operation types store their details in dedicated lists
    }

    list_key = source_list_key_map.get(operation_action_type)
    if not list_key:
        return None # Unsupported or unknown operation_action_type

    source_list = DB.get(list_key, [])
    for op in source_list:
        if isinstance(op, dict) and op.get("id") == operation_id:
            return op
    return None

def get_recent_navigations(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves a list of the most recent navigation records from DB["page_history"],
    ordered by timestamp (newest first). Assumes 'timestamp' is an ISO format string.

    Args:
        limit: The maximum number of recent navigation records to return.

    Returns:
        A list of navigation record dictionaries.
    """
    page_history = DB.get("page_history", [])
    if not page_history:
        return []
    
    # Filter for valid entries and sort
    # Assumes timestamp is an ISO format string, which sorts correctly lexicographically for recency.
    valid_navs = [nav for nav in page_history if isinstance(nav, dict) and "timestamp" in nav]
    
    try:
        # Sort by timestamp string in descending order (most recent first)
        sorted_navs = sorted(valid_navs, key=lambda x: x["timestamp"], reverse=True)
    except TypeError:
        # This might happen if timestamps are not comparable strings (e.g. mixed types)
        # For robustness, could log an error or return a subset that is sortable.
        # Here, we'll return an empty list or partially sorted if some error occurs.
        # Alternatively, convert to datetime objects for sorting if format is guaranteed.
        return [] # Or handle more gracefully
        
    return sorted_navs[:limit]

def get_failed_operations() -> List[Dict[str, Any]]:
    """
    Retrieves all operations from relevant DB lists (page_history, screenshots)
    that have a non-None 'error' field.
    Note: DB["script_results"] is not checked here as it stores only script outputs,
    and a 'null' entry indicates a script execution failure, but the detailed error
    is part of the original 'evaluate' operation log, not directly in 'script_results'.

    Returns:
        A list containing dictionaries of failed operations.
    """
    failed_ops: List[Dict[str, Any]] = []
    # Define keys for lists in DB that store operation details which might fail
    operation_lists_keys = ["page_history", "screenshots"]
    # Extend this list if other operations (e.g., clicks, fills) store detailed results
    # with an 'error' field in other dedicated lists within DB.
    
    for key in operation_lists_keys:
        ops_list = DB.get(key, [])
        for op in ops_list:
            # Check if 'op' is a dictionary and has an 'error' key with a non-None value
            if isinstance(op, dict) and op.get("error") is not None:
                failed_ops.append(op)
    return failed_ops

def get_screenshots_by_name(name: str) -> List[Dict[str, Any]]:
    """
    Retrieves all screenshot records from DB["screenshots"] with a specific name.

    Args:
        name: The name of the screenshot to filter by.

    Returns:
        A list of screenshot record dictionaries.
    """
    screenshots_list = DB.get("screenshots", [])
    if not name: # Or check if name is empty string if that's not allowed
        return []
    return [s_shot for s_shot in screenshots_list if isinstance(s_shot, dict) and s_shot.get("name") == name]

def get_evaluate_results_containing(keyword: str) -> List[Dict[str, Any]]:
    """
    Retrieves 'evaluate' operations from DB["script_results"] whose 'script_result'
    (if it exists and is string-representable) contains a specific keyword (case-insensitive).

    Args:
        keyword: The keyword to search for in the script results.

    Returns:
        A list of matching 'evaluate' operation dictionaries.
    """
    matching_evaluates: List[Dict[str, Any]] = []
    evaluate_ops_list = DB.get("script_results", [])
    
    if not keyword: # Return empty if keyword is empty or None
        return []

    keyword_lower = keyword.lower()

    for eval_op in evaluate_ops_list:
        if not isinstance(eval_op, dict):
            continue # Skip if not a dictionary
        
        script_result = eval_op.get("script_result")
        if script_result is None:
            continue

        found_keyword = False
        if isinstance(script_result, dict): # If result is a dictionary, search its string values
            for value in script_result.values():
                if isinstance(value, str) and keyword_lower in value.lower():
                    found_keyword = True
                    break
                elif isinstance(value, (int, float, bool)) and keyword_lower == str(value).lower(): # Match exact string form of numbers/bools
                    found_keyword = True
                    break
        elif isinstance(script_result, str): # If result is a string
            if keyword_lower in script_result.lower():
                found_keyword = True
        elif isinstance(script_result, (int, float, bool)): # If result is numeric/boolean
            if keyword_lower == str(script_result).lower():
                found_keyword = True
        
        if found_keyword:
            matching_evaluates.append(eval_op)
            
    return matching_evaluates

def sanitize_filename_component(name_component: str) -> str:
    """
    Sanitizes a string to be a safe component in a filename.
    - Replaces known problematic characters and whitespace with underscores.
    - Collapses multiple underscores.
    - Strips leading/trailing underscores, spaces, periods.
    - Limits length to prevent overly long filenames.
    Returns an empty string if sanitization results in an empty string or input is invalid.
    """
    if not isinstance(name_component, str):
        return ""  # Invalid input type
    
    # Replace characters problematic in most OS filenames and all whitespace with underscore
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F\s]', '_', name_component)
    
    # Collapse multiple underscores resulting from replacements
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores and periods that can be problematic
    sanitized = sanitized.strip('_.')
    
    # Enforce a reasonable maximum length for the filename component
    max_len = 100  # Max length for the sanitized name component
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]
        # Re-strip in case truncation left a problematic character at the end
        sanitized = sanitized.strip('_.')

    # If the name becomes empty after sanitization (e.g., was all invalid chars)
    if not sanitized:
        return ""
        
    return sanitized

def record_screenshot_attempt(
    op_id: str, timestamp: datetime.datetime, name: str, selector: Optional[str],
    input_width: int, input_height: int,
    file_path_val: Optional[str], image_width_val: Optional[int], image_height_val: Optional[int], file_size_val: Optional[int],
    error_msg: Optional[str], error_type_name: Optional[str]
) -> None:
    """Helper to create and store a screenshot record in the DB."""
    record = {
        "id": op_id,
        "timestamp": timestamp,
        "name": name, # Original name parameter
        "selector": selector,
        "width": input_width, # Input/configured width for the operation
        "height": input_height, # Input/configured height for the operation
        "file_path": file_path_val,
        "image_width": image_width_val, # Actual width of the saved image
        "image_height": image_height_val, # Actual height of the saved image
        "file_size": file_size_val,
        "error": error_msg,
        "error_type": error_type_name,
    }
    # Ensure the 'screenshots' list exists in DB
    if "screenshots" not in DB:
        DB["screenshots"] = []
    DB["screenshots"].append(record)

async def get_browser_context(launch_options=None, allow_dangerous=False):
    """
    Create a temporary browser context for backward compatibility.
    This function creates a new browser instance each time it's called.
    
    Args:
        launch_options: Browser launch options
        allow_dangerous: Whether to allow dangerous browser arguments
        
    Returns:
        Browser context object
    """
    p = await async_playwright().start()
    
    args = launch_options.get("args", []) if launch_options else []
    if not allow_dangerous:
        for a in args:
            if "no-sandbox" in a or "disable-web-security" in a:
                raise ValueError("Dangerous args blocked by default.")
    
    browser = await p.chromium.launch(**launch_options) if launch_options else await p.chromium.launch()
    context = await browser.new_context()
    
    # Store playwright instance for cleanup
    context._playwright_instance = p
    
    return context