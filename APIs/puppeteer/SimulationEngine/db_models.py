import datetime as dt
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# ---------------------------
# Internal Storage Models
# ---------------------------

class PageStorage(BaseModel):
    """Internal storage model for a single page within a context."""
    title: Optional[str] = Field(None, description="The title of the page.")
    status: Optional[int] = Field(None, description="The HTTP status code of the page response.")
    loaded_successfully: bool = Field(..., description="Indicates whether the page loaded successfully.")

class ContextStorage(BaseModel):
    """Internal storage model for a browser context."""
    active_page: Optional[str] = Field(None, description="The URL of the currently active page in this context.", min_length=1)
    pages: Dict[str, PageStorage] = Field(default_factory=dict, description="A dictionary of pages open in this context, keyed by URL.")

class ScreenshotStorage(BaseModel):
    """Internal storage model for a screenshot record."""
    id: str = Field(..., description="Unique identifier for the screenshot.", min_length=1)
    timestamp: dt.datetime = Field(..., description="Timestamp when the screenshot was taken.")
    name: str = Field(..., description="A user-defined name for the screenshot.", min_length=1)
    selector: Optional[str] = Field(None, description="The CSS selector for the element that was captured, if any.")
    width: int = Field(..., description="The width of the screenshot viewport.")
    height: int = Field(..., description="The height of the screenshot viewport.")
    file_path: Optional[str] = Field(None, description="The absolute path to the saved screenshot file.")
    image_width: Optional[int] = Field(None, description="The actual width of the saved image.")
    image_height: Optional[int] = Field(None, description="The actual height of the saved image.")
    file_size: Optional[int] = Field(None, description="The size of the screenshot file in bytes.")
    error: Optional[str] = Field(None, description="Any error message captured during the screenshot attempt.")
    error_type: Optional[str] = Field(None, description="The type of error, if one occurred.")

class ScriptResultStorage(BaseModel):
    """Internal storage model for the result of an executed script."""
    data_payload: Any = Field(..., description="The data returned by the script execution.")
    status_message: str = Field(..., description="A message indicating the status of the script execution.")
    elements_processed_count: Optional[int] = Field(None, description="The number of elements processed by the script, if applicable.")

class LaunchOptionsStorage(BaseModel):
    """Internal storage model for browser launch options."""
    headless: bool = Field(..., description="Whether the browser was launched in headless mode.")
    args: List[str] = Field(..., description="A list of command-line arguments passed to the browser instance.")

class PageHistoryStorage(BaseModel):
    """Internal storage model for a page navigation event."""
    id: str = Field(..., description="Unique identifier for the history event.", min_length=1)
    timestamp: dt.datetime = Field(..., description="Timestamp of the navigation event.")
    url: str = Field(..., description="The URL that was navigated to.", min_length=1)
    launch_options: Optional[LaunchOptionsStorage] = Field(None, description="The launch options for this navigation, if it was a new page.")
    allow_dangerous: bool = Field(..., description="Indicates whether dangerous content was allowed.")
    page_title: Optional[str] = Field(None, description="The title of the page after navigation.")
    response_status: Optional[int] = Field(None, description="The HTTP response status of the navigation.")
    loaded_successfully: bool = Field(..., description="Indicates whether the page loaded successfully.")
    error: Optional[str] = Field(None, description="Any error message that occurred during navigation.")
    error_type: Optional[str] = Field(None, description="The type of error, if one occurred.")

# ---------------------------
# Root Database Model
# ---------------------------

class PuppeteerDB(BaseModel):
    """Root model that validates the entire Puppeteer database structure."""
    contexts: Dict[str, ContextStorage] = Field(
        default_factory=dict,
        description="Dictionary of browser contexts, indexed by context name."
    )
    active_context: str = Field(
        ...,
        description="The name of the currently active browser context.",
        min_length=1
    )
    logs: List[str] = Field(
        default_factory=list,
        description="A list of log entries from the browser session."
    )
    screenshots: List[ScreenshotStorage] = Field(
        default_factory=list,
        description="A list of all screenshots taken."
    )
    script_results: List[Optional[ScriptResultStorage]] = Field(
        default_factory=list,
        description="A list of results from executed scripts."
    )
    page_history: List[PageHistoryStorage] = Field(
        default_factory=list,
        description="A chronological history of page navigations."
    )

    class Config:
        str_strip_whitespace = True
