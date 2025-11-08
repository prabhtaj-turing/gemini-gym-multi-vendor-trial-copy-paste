class InvalidInputError(Exception):
    """
    Raised when the input is invalid.
    """
    pass

class MermaidSyntaxError(Exception):
    """
    Raised when the Mermaid syntax is invalid.
    """

class LastEditNotFoundError(Exception):
    """
    Raised when no previous edit information is found to perform a fix.
    """
    pass

class FileNotInWorkspaceError(Exception):
    """
    Raised when a target file for an operation is not found in the workspace.
    """
    pass

class LintFixingError(Exception):
    """
    Raised when an error occurs during the lint fixing process.
    """
    pass

class FailedToApplyLintFixesError(Exception):
    """
    Raised when the lint fixes are not applied successfully.
    """
    pass

class ValidationError(Exception):
    pass

class CommandExecutionError(Exception):
    """
    Raised when an external command fails to execute or returns a non-zero exit code.
    """
    pass

class LLMGenerationError(Exception):
    """
    Raised when an LLM fails to generate a response.
    """
    pass

class MetadataError(Exception):
    """
    Raised when a metadata operation fails.
    """
    pass

class WorkspaceNotHydratedError(Exception):
    """
    Raised when a file-system-dependent operation is attempted on an unhydrated workspace.
    The workspace must be initialized with workspace_root and file_system content before
    these operations can be performed.
    """
    pass

