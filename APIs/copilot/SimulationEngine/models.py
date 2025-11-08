from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any


class JupyterNotebookCreationResponse(BaseModel):
    """
    Information about the newly created Jupyter Notebook.
    """
    file_path: str = Field(
        ...,
        description="The absolute file path of the newly created .ipynb notebook file."
    )
    status: str = Field(
        ...,
        description="Status of the creation operation, typically 'success' if no error is raised."
    )
    message: Optional[str] = Field(
        None,
        description="A confirmation message or additional details regarding the notebook creation."
    )


class DirectoryEntry(BaseModel):
    """
    Details of a file or directory entry.
    """
    name: str = Field(..., description="The name of the file or subdirectory. Directory names end with a '/' suffix.")
    type: Literal['file', 'directory'] = Field(..., description="The type of the entry, either 'file' or 'directory'.")
    path: str = Field(..., description="The full path to the file or directory entry.")


class FileOutlineItem(BaseModel):
    """
    Describes a structural element within a file outline.
    """
    name: str  # Name of the symbol or section (e.g., function name, class name, heading)
    kind: str  # Type of symbol or section (e.g., 'function', 'class', 'module', 'section')
    start_line: int  # Start line of the symbol/section in the file
    end_line: int  # End line of the symbol/section in the file

      
class ReadFileResponse(BaseModel):
    """
    Represents the response from reading a file segment.
    """
    file_path: str  # The path of the file that was read
    content: str  # The content of the requested line range of the file
    start_line: int  # The starting line number (1-based) of the returned content
    end_line: int  # The ending line number (1-based) of the returned content
    total_lines: int  # The total number of lines in the file
    is_truncated_at_top: bool  # True if the returned content does not start from the beginning of the file
    is_truncated_at_bottom: bool  # True if the returned content does not reach the end of the file
    outline: Optional[List[FileOutlineItem]] = None  # An optional outline of the file structure


class WebpageContent(BaseModel):
    """
    A dictionary that contains the main content and metadata
    from the fetched web page.
    """
    title: Optional[str] = Field(None, description="The title of the webpage, if successfully extracted.")
    main_content_text: str = Field(..., description="The extracted main textual content of the webpage. This is usually cleaned of boilerplate like navigation and ads.")
    status_code: int = Field(..., description="The HTTP status code received when fetching the page (e.g., 200 for success).")
    content_type: Optional[str] = Field(None, description="The Content-Type header of the response, if available (e.g., 'text/html; charset=utf-8').")


class EditFileResult(BaseModel):
    """
    Represents the result of an attempt to edit a file.
    Corresponds to the return dictionary of `insert_edit_into_file`.
    """
    file_path: str = Field(
        ...,
        description="The path of the file that was targeted for editing."
    )
    status: Literal['success', 'partially_applied', 'failed_to_apply', 'file_not_found'] = Field(
        ...,
        description="Status of the edit operation."
    )
    message: Optional[str] = Field(
        default=None,
        description="A message providing more details, e.g., if the edit could not be applied cleanly, or specific changes made. May include warnings if parts of the edit were ambiguous."
    )

