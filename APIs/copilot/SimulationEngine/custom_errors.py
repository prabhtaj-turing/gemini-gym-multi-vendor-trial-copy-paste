class FileCreationError(Exception):
    """If the notebook file cannot be created at the intended location (e.g., due to permission issues, invalid path, or disk full)."""
    pass
class JupyterEnvironmentError(Exception):
    """If there's an issue with the Jupyter environment setup in VS Code, or required dependencies (like the Jupyter extension itself) are missing or misconfigured."""
    pass
class InvalidRequestError(Exception):
    """If the request to create a notebook is made in an inappropriate context (e.g., if not explicitly requested by the user as per description)."""
    pass
class CommandExecutionError(Exception):
    """
    Raised when a shell command fails to execute for reasons like
    command not found, syntax error, or critical runtime errors during execution.
    """
    pass
class TerminalNotAvailableError(Exception):
    """
    Raised if a terminal instance cannot be allocated or accessed.
    """
    pass
class InvalidInputError(Exception):
    """
    Raised if required parameters are missing or invalid, or if input arguments
    fail validation. This can also include issues with command formatting,
    like failing to disable pagers for commands that require it.
    """
    pass
class DirectoryNotFoundError(Exception):
    """Raised when a specified directory path does not exist or is not a directory."""
    pass
class InvalidLineRangeError(Exception):
    """Raised when the specified line range is invalid."""
    pass
class FileNotFoundError(Exception):
    """Raised if the specified file path does not exist."""
    pass
class PermissionDeniedError(Exception):
    """Raised if there is no permission to read the specified file."""
    pass
class WorkspaceNotAvailableError(Exception):
    """Custom error for when the user's workspace cannot be accessed."""
    pass
class InvalidGlobPatternError(Exception):
    """Custom error for when a provided glob pattern is malformed or invalid."""
    pass
class SearchFailedError(Exception):
    """Custom error for when the search operation fails for an unexpected reason."""
    pass
class ValidationError(Exception):
    """Custom error for when input arguments fail validation."""
    pass
class SymbolNotFoundError(Exception):
    """
    Raised when no symbol is found at the specified file_path, line_number,
    and column_number, or if the identified element is not a symbol
    for which usages can be determined (e.g., a comment).
    """
    pass
class IndexingNotCompleteError(Exception):
    """
    Raised when the codebase is not yet fully indexed,
    preventing usage lookups. The client may retry after a delay.
    """
    pass
class InvalidTerminalIdError(Exception):
    """
    Raised when terminal id is not valid.
    """
    pass
class OutputRetrievalError(Exception):
    """
    Raised when output for a shell command could not be retrieved.
    """
class InvalidSearchPatternError(Exception):
    """Custom error for when the search string or pattern is invalid (e.g., an invalid regular expression if supported)."""
    pass
class EditConflictError(Exception):
    """
    Raised when the provided edit instructions are ambiguous,
    conflict with the current file content significantly,
    or cannot be reliably applied by the system.
    """
    pass
class InvalidEditFormatError(Exception):
    """
    Raised if the format of the edit instructions is invalid
    or does not conform to expected patterns.
    """
class NetworkError(Exception):
    """
    If there is a network issue preventing fetching the
    webpage (e.g., DNS resolution failure, timeout, no internet
    connection).
    """
    pass
class InvalidURLError(Exception):
    """If the provided URL is malformed, unsupported, or invalid."""
    pass
class HTTPError(Exception):
    """
    If an HTTP error status code (4xx or 5xx client/server
    errors) is received from the web server.
    """

    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
class ContentExtractionError(Exception):
    """
    If the main content cannot be reliably extracted from the webpage,
    or the page format is unsupported.
    """
    pass
class TooLargeError(Exception):
    """If the webpage content is too large to process."""
    pass
class InstallationFailedError(Exception):
    """If the extension installation process fails due to system issues, permissions, or VS Code internal errors."""
    pass
class UsageContextError(Exception):
    """If this tool is used outside the intended context of a new workspace creation process."""
    pass
class ExtensionNotFoundError(Exception):
    """If the specified extension ID cannot be found in the VS Code Marketplace or available sources."""
    pass
class ToolConfigurationError(Exception):
    """
    If the linter, compiler, or language server required to get errors
    is not configured correctly, not found, or fails to run.
    """
    pass
  

class AnalysisFailedError(Exception):
    """
    If analysis of the file could not be completed for other reasons.
    """
    pass
  

class QueryTooBroadError(Exception):
    """If the query for API references is too vague to yield specific or useful results."""
    pass
class ProjectConfigurationError(Exception):
    """If project configuration or conventions needed to determine test/source relationships are missing, ambiguous, or invalid."""
    pass
class SearchLogicError(Exception):
    """If an internal error occurs within the test search logic."""
    pass
  
    
class APIDatabaseNotAvailableError(Exception):
    """If the VS Code API reference database cannot be accessed or is not initialized."""
    pass
class WorkspaceNotInitializedError(Exception):
    """If a tool is called without a workspace being properly initialized or 'create_new_workspace' (or equivalent) having been successfully run first."""
    pass

class ProjectTypeOrLanguageNotFoundError(Exception):
    """If setup information for the specified project type or language combination is not available."""
    pass

class ConfigurationError(Exception):
    """If there's an issue fetching or generating the project setup information."""
    pass

class GitRepositoryNotFoundError(Exception):
    """If the current workspace is not a git repository, or git command is not found."""
    pass

class GitCommandError(Exception):
    """If there is an error executing the underlying git diff command (e.g., due to merge conflicts, corrupted repository)."""
