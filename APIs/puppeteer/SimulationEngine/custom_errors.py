class PuppeteerError(Exception):
    """Base class for Puppeteer-related errors."""
    pass

class ValidationError(PuppeteerError):
    """Raised when input validation fails."""
    pass

class BrowserError(PuppeteerError):
    """Raised when an issue occurs with the browser instance or context."""
    pass

class ElementNotFoundError(PuppeteerError):
    """Raised when an element specified by a selector is not found on the page."""
    def __init__(self, selector: str, message: str = ""):
        self.selector = selector
        # Ensure the default message format matches test expectations.
        self.message = message or f"Element with selector '{selector}' not found."
        super().__init__(self.message)

class ElementNotInteractableError(PuppeteerError):
    """Raised when a found element is not interactable (e.g., obscured, disabled, not visible)."""
    def __init__(self, selector: str, reason: str = "unknown", message: str = ""):
        self.selector = selector
        self.reason = reason
        self.message = message or f"Element with selector '{selector}' found but not interactable. Reason: {reason}."
        super().__init__(self.message)

class ElementNotEditableError(PuppeteerError):
    """Raised when an element is not editable (for fill operations)."""
    def __init__(self, selector: str, message: str = ""):
        self.selector = selector
        self.message = message or f"Element with selector '{selector}' is not editable."
        super().__init__(self.message)

class NetworkError(PuppeteerError):
    """Raised when a network error occurs during navigation."""
    pass

class InvalidURLError(PuppeteerError):
    """Raised when the provided URL is malformed or invalid."""
    pass

class FileSystemError(PuppeteerError):
    """Raised when an error occurs while writing files to disk."""
    pass

class InvalidParameterError(PuppeteerError):
    """Raised when invalid parameters are provided."""
    pass

class NotSelectElementException(PuppeteerError):
    """Raised when the element found is not a select element."""
    def __init__(self, selector: str, message: str = ""):
        self.selector = selector
        self.message = message or f"Element with selector '{selector}' is not a select element."
        super().__init__(self.message)

class OptionNotAvailableError(PuppeteerError):
    """Raised when the specified option is not available in a select element."""
    def __init__(self, selector: str, value: str, message: str = ""):
        self.selector = selector
        self.value = value
        self.message = message or f"Option with value '{value}' not available in select element '{selector}'."
        super().__init__(self.message)

class JavaScriptExecutionError(PuppeteerError):
    """Raised when JavaScript execution fails in the browser."""
    pass

class SerializationError(PuppeteerError):
    """Raised when the result returned by JavaScript is not JSON-serializable."""
    pass