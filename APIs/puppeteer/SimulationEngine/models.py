from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# --- Base Models for common structures ---

class ToolInputSchema(BaseModel):
    """Base model for the input schema of a Puppeteer tool."""
    type: str
    properties: Dict[str, Any]
    required: Optional[List[str]] = None

class ToolReturnsSchema(BaseModel):
    """Base model for the returns schema of a Puppeteer tool."""
    description: str
    type: str

class ToolRaisesSchema(BaseModel):
    """Base model for the raises schema of a Puppeteer tool."""
    error_name: str
    description: str

# --- Individual Tool Models (representing records of operations) ---

class PuppeteerNavigate(BaseModel):
    """Represents a 'puppeteer_navigate' operation."""
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.now)
    url: str
    launch_options: Optional[Dict[str, Any]] = None
    allow_dangerous: bool = False
    # Return details
    page_title: Optional[str] = None
    response_status: Optional[int] = None
    loaded_successfully: Optional[bool] = None
    # Error details
    error: Optional[str] = None
    error_type: Optional[str] = None

class PuppeteerScreenshot(BaseModel):
    """Represents a 'puppeteer_screenshot' operation."""
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.now)
    name: str
    selector: Optional[str] = None
    width: int = 800
    height: int = 600
    # Return details
    file_path: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    file_size: Optional[int] = None
    # Error details
    error: Optional[str] = None
    error_type: Optional[str] = None

class PuppeteerClick(BaseModel):
    """Represents a 'puppeteer_click' operation."""
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.now)
    selector: str
    # Error details
    error: Optional[str] = None
    error_type: Optional[str] = None

class PuppeteerEvaluate(BaseModel):
    """Represents a 'puppeteer_evaluate' operation."""
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.now)
    script: str
    # Return details
    script_result: Optional[Dict[str, Any]] = None
    # Error details
    error: Optional[str] = None
    error_type: Optional[str] = None

# --- Helper Models for DB State ---

class PageInfo(BaseModel):
    """Represents metadata for a specific page (URL) within a context."""
    title: Optional[str] = None
    status: Optional[int] = None  # HTTP status from navigation
    loaded_successfully: Optional[bool] = None
    # Add other relevant metadata as needed based on Puppeteer navigate results

class BrowserContextState(BaseModel):
    """Represents the state of a single browser context."""
    active_page: Optional[str] = None  # URL of the currently active page in this context
    pages: Dict[str, PageInfo] = Field(default_factory=dict) # Metadata for pages in this context, keyed by URL

# --- Main Database Model (Reflecting db.py structure) ---

class PuppeteerDB(BaseModel):
    """
    Main Pydantic class representing the in-memory simulation state.
    """
    contexts: Dict[str, BrowserContextState] = Field(
        default_factory=lambda: {"default": BrowserContextState()}
    )
    active_context: str = "default"
    logs: List[str] = Field(default_factory=list) # Chronological log of action descriptions
    screenshots: List[PuppeteerScreenshot] = Field(default_factory=list) # List of screenshot operation records
    script_results: List[Optional[Dict[str, Any]]] = Field(default_factory=list) # List of results from puppeteer_evaluate
    page_history: List[PuppeteerNavigate] = Field(default_factory=list) # List of navigation operation records

class PuppeteerSelectorValueInput(BaseModel):
    """Input model for Puppeteer functions that require a selector and value (fill, select)."""
    selector: str = Field(
        ...,
        min_length=1,
        description="CSS selector for the target element"
    )
    value: str = Field(
        ..., # Ellipsis means the field is required. Empty string is a valid string.
        description="Value to use (fill value or option to select)"
    )

    class Config:
        extra = 'forbid' # Disallow any extra fields not defined in the model

class PuppeteerScreenshotInput(BaseModel):
    """Input model for Puppeteer screenshot function."""
    name: str = Field(
        ...,
        min_length=1,
        description="Name for the screenshot file"
    )
    selector: Optional[str] = Field(
        None,
        description="CSS selector for element to screenshot (optional, full page if not provided)"
    )
    width: int = Field(
        800,
        gt=0,
        description="Width in pixels for the screenshot"
    )
    height: int = Field(
        600,
        gt=0,
        description="Height in pixels for the screenshot"
    )

    class Config:
        extra = 'forbid' # Disallow any extra fields not defined in the model

class PuppeteerNavigateInput(BaseModel):
    """Input model for Puppeteer navigate function."""
    url: str = Field(
        ...,
        min_length=1,
        description="URL to navigate to"
    )
    launch_options: Optional[Dict[str, Any]] = Field(
        None,
        description="Browser launch options (optional)"
    )
    allow_dangerous: bool = Field(
        False,
        description="Whether to allow navigation to potentially dangerous URLs"
    )

    class Config:
        extra = 'forbid' # Disallow any extra fields not defined in the model