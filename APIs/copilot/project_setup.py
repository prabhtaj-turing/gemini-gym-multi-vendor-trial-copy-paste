"""
Project Setup module for Copilot API.
Provides functions for project creation and setup.
"""

from common_utils.tool_spec_decorator import tool_spec
import os
import json
from typing import Dict, Any, List, Optional


from .SimulationEngine.db import DB
from .SimulationEngine import utils
from .SimulationEngine import custom_errors


@tool_spec(
    spec={
        'name': 'create_new_workspace',
        'description': """ Get steps to help the user create any project in a VS Code workspace.
        
        Use this tool to help users set up new projects, including TypeScript-based projects, Model Context Protocol (MCP) servers, VS Code extensions, Next.js projects, Vite projects, or any other project. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The query to use to generate the new workspace. This should be a clear and concise description of the workspace the user wants to create.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def create_new_workspace(query: str) -> Dict[str, Any]:
    """Get steps to help the user create any project in a VS Code workspace.

    Use this tool to help users set up new projects, including TypeScript-based projects, Model Context Protocol (MCP) servers, VS Code extensions, Next.js projects, Vite projects, or any other project.

    Args:
        query (str): The query to use to generate the new workspace. This should be a clear and concise description of the workspace the user wants to create.

    Returns:
        Dict[str, Any]: A dictionary containing the function's results.
                        Expected structure:
                        {
                            "query": str, // The original query provided by the user
                            "summary": str,  // Summary of the project plan from the LLM
                            "steps": List[Dict[str, Any]] // Parsed steps from the LLM to create the project
                        }

    Raises:
        custom_errors.ValidationError: If input arguments fail validation (e.g., query is not a non-empty string).
        custom_errors.WorkspaceNotAvailableError: If the workspace root is not configured.
        RuntimeError: If the LLM call fails or returns an unparsable response.
    """
    # Validate query: must be a non-empty string
    if not isinstance(query, str) or not query.strip():
        raise custom_errors.ValidationError("Query must be a non-empty string.")

    # Check for workspace_root configuration
    workspace_root_path = DB.get("workspace_root")
    if not workspace_root_path:
        raise custom_errors.WorkspaceNotAvailableError("Workspace root is not configured.")
    # Further validation could check if workspace_root_path exists in DB['file_system'] and is a directory.
    # For now, we rely on tests to set up a valid workspace_root if not testing its absence.

    current_cwd = DB.get("cwd", "/")  # Default to root if not set
    # workspace_root is already fetched and validated as workspace_root_path
    # Use workspace_root_path consistently.
    workspace_root = workspace_root_path

    # Prompt for the LLM to generate a project creation plan
    prompt = f"""You are an expert assistant guiding users to set up new software projects in a VS Code-like environment.
    The user's current working directory is: "{current_cwd}"
    The workspace root is: "{workspace_root}"
    
    User's project creation query: "{query}"
    
    Your goal is to provide a plan to create this project. The plan should consist of:
    1. A concise overall summary of the project to be created.
    2. A list of actionable steps.
    
    Output Format:
    Please provide the summary first, prefixed with "Summary: ".
    Then, on a new line, use the exact separator "----STEPS_SEPARATOR----".
    Finally, provide the list of steps as a valid JSON array of objects. Each object in the array represents one step and must follow this structure:
      {{
        "type": "instruction" | "terminal_command" | "file_creation",
        "description": "A human-readable description of this step.",
        "details": {{
          // For "terminal_command":
          //   "command": "The shell command to execute. Example: 'mkdir my-project && cd my-project'"
          // For "file_creation":
          //   "file_path": "Relative path for the new file (e.g., 'src/index.js' or 'my-project/README.md'). Assume paths are relative to the CWD unless a command in a previous step changes the directory.",
          //   "content": "The full content for the new file."
          // For "instruction":
          //   "text": "General guidance or information for the user."
        }}
      }}

    Example for "terminal_command" details: {{"command": "npm install lodash"}}
    Example for "file_creation" details: {{"file_path": "config.json", "content": "{{\\"theme\\": \\"dark\\"}}"}}
    Example for "instruction" details: {{"text": "Ensure you have Python 3.8+ installed."}}
    
    If the query is too vague or ambiguous to generate a concrete plan, the summary should explain this, and the steps list should be empty or contain a single instructional step guiding the user to clarify.
    
    Generate the response now:
    """

    try:
        # Call the LLM to get the project creation plan
        raw_llm_response = utils.call_llm(
            prompt_text=prompt,
            temperature=0.3,
            timeout_seconds=120
        )
    except RuntimeError as e:
        # Propagate LLM call errors (e.g., network issues, API key problems)
        raise RuntimeError(f"LLM call failed during project creation planning: {e}") from e

    if not isinstance(raw_llm_response, str):
        response_type = type(raw_llm_response).__name__
        response_snippet = str(raw_llm_response)[:200] if raw_llm_response is not None else "None"
        # This error message helps diagnose issues if the LLM (or its stub) returns unexpected types.
        raise RuntimeError(
            f"LLM call returned an invalid response type: {response_type}. Expected string. Response snippet: {response_snippet}"
        )

    # Define the separator used in the LLM's output format
    separator = "----STEPS_SEPARATOR----"
    if separator not in raw_llm_response:
        raise RuntimeError(
            f"LLM response format error: Separator '{separator}' not found. Response snippet: {raw_llm_response[:500]}"
        )

    # Split the response into summary and steps parts
    parts = raw_llm_response.split(separator, 1)
    if len(parts) != 2:
        raise RuntimeError(
            f"LLM response format error: Could not split response into summary and steps. Response snippet: {raw_llm_response[:500]}"
        )

    summary_part = parts[0].strip()
    steps_json_part = parts[1].strip()

    # Extract the summary, removing the "Summary: " prefix if present
    summary_prefix = "Summary: "
    if summary_part.startswith(summary_prefix):
        extracted_summary = summary_part[len(summary_prefix):].strip()
    else:
        # If the prefix is missing, use the whole part as summary.
        extracted_summary = summary_part

    # Clean potential markdown code fences from the JSON part of the response
    cleaned_steps_json_part = utils.strip_code_fences_from_llm(steps_json_part)

    extracted_steps: List[Dict[str, Any]]
    try:
        # Parse the JSON string containing the list of steps
        parsed_steps = json.loads(cleaned_steps_json_part)
        if not isinstance(parsed_steps, list):
            # Ensure the parsed JSON is a list as expected
            raise ValueError("Parsed steps from LLM are not a list.")

        extracted_steps = parsed_steps
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse LLM steps JSON: {e}. JSON part snippet: {cleaned_steps_json_part[:500]}") from e
    except ValueError as e:
        raise RuntimeError(
            f"LLM steps JSON structure error: {e}. JSON part snippet: {cleaned_steps_json_part[:500]}") from e

    # Return the structured project creation plan
    return {
        "query": query,  # Include the original query
        "summary": extracted_summary,  # Use 'summary' key
        "steps": extracted_steps,  # Use 'steps' key
    }

@tool_spec(
    spec={
        'name': 'get_project_setup_info',
        'description': """ Provides project setup information for a Visual Studio Code workspace based on a project type and programming language.
        
        This tool provides project setup information for a Visual Studio Code workspace based on a project type and programming language. This tool must not be called without first calling the tool to create a workspace. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_type': {
                    'type': 'string',
                    'description': "The type of the project (e.g., 'typescript_server', 'vscode_extension', 'python_datascience')."
                },
                'language': {
                    'type': 'string',
                    'description': "The primary programming language of the project (e.g., 'typescript', 'python')."
                }
            },
            'required': [
                'project_type',
                'language'
            ]
        }
    }
)
def get_project_setup_info(project_type: str, language: str) -> Dict[str, Any]:
    """Provides project setup information for a Visual Studio Code workspace based on a project type and programming language.

    This tool provides project setup information for a Visual Studio Code workspace based on a project type and programming language. This tool must not be called without first calling the tool to create a workspace.

    Args:
        project_type (str): The type of the project (e.g., 'typescript_server', 'vscode_extension', 'python_datascience').
        language (str): The primary programming language of the project (e.g., 'typescript', 'python').

    Returns:
        Dict[str, Any]: A dictionary containing detailed setup information for the specified project type and language. It includes the following keys:
            project_type (str): The type of the project (e.g., 'typescript_server', 'vscode_extension', 'python_datascience').
            language (str): The primary programming language of the project.
            recommended_extensions (List[Dict[str, str]]): A list of recommended VS Code extensions. Each dictionary in the list contains:
                id (str): The unique identifier of the extension (e.g., 'dbaeumer.vscode-eslint').
                name (str): The display name of the extension.
                reason (str): A brief explanation why this extension is recommended.
            key_configuration_files (List[Dict[str, Any]]): Information about essential configuration files for the project. Each dictionary in the list contains:
                file_name_pattern (str): The typical name or pattern of the configuration file (e.g., 'tsconfig.json', '.vscode/launch.json').
                purpose (str): The role or purpose of this configuration file in the project.
                example_content_snippet (Optional[str]): A brief example or template snippet for the file content, if applicable.
            common_tasks (Optional[List[Dict[str, str]]]): Common development tasks and how to perform them. If present, each dictionary in the list contains:
                name (str): Name of the task (e.g., 'Build', 'Run Tests', 'Start Debug Server').
                command_suggestion (str): A suggested command or steps to perform the task.
            debugging_tips (Optional[List[str]]): A list of tips or common configurations for debugging this type of project in VS Code. This key may be absent if no specific tips are available.

    Raises:
        WorkspaceNotInitializedError: If this tool is called without a workspace being properly initialized or 'create_new_workspace' (or equivalent) having been successfully run first.
        ProjectTypeOrLanguageNotFoundError: If setup information for the specified project type or language combination is not available.
        ConfigurationError: If there's an issue fetching or generating the project setup information.
        ValidationError: If input arguments fail validation.
    """
    # Validate project_type
    if not isinstance(project_type, str):
        raise custom_errors.ValidationError("Input validation failed: 'project_type' must be a string.")
    if not project_type.strip():
        raise custom_errors.ValidationError("Input validation failed: 'project_type' must be a non-empty string.")

    # Validate language
    if not isinstance(language, str):
        raise custom_errors.ValidationError("Input validation failed: 'language' must be a string.")
    if not language.strip():
        raise custom_errors.ValidationError("Input validation failed: 'language' must be a non-empty string.")

    if not DB.get("workspace_root"):
        raise custom_errors.WorkspaceNotInitializedError(
            "Workspace is not initialized. Please create or load a workspace first."
        )

    # Use stripped, lowercased versions for lookup, but original values for display/return.
    project_type_cleaned = project_type.strip()
    language_cleaned = language.strip()
    lookup_key = (project_type_cleaned.lower(), language_cleaned.lower())

    setup_details = utils._PROJECT_SETUP_DATA.get(lookup_key)

    if setup_details is None:
        # Use original, uncleaned input values for the error message as per test expectations.
        raise custom_errors.ProjectTypeOrLanguageNotFoundError(
            f"Setup information for project type '{project_type}' and language '{language}' is not available."
        )

    try:
        result = {
            "project_type": project_type,  # Use original casing from input
            "language": language,  # Use original casing from input
            "recommended_extensions": setup_details.get("recommended_extensions", []),
            "key_configuration_files": setup_details.get("key_configuration_files", []),
            "common_tasks": setup_details.get("common_tasks"),  # Will be None if key is missing or value is None
            "debugging_tips": setup_details.get("debugging_tips"),  # Will be None if key is missing or value is None
        }
        if not isinstance(result["recommended_extensions"], list):
            raise TypeError("'recommended_extensions' must be a list.")
        if not isinstance(result["key_configuration_files"], list):
            raise TypeError("'key_configuration_files' must be a list.")
        if result["common_tasks"] is not None and not isinstance(result["common_tasks"], list):
            raise TypeError("'common_tasks' must be a list or None.")
        if result["debugging_tips"] is not None and not isinstance(result["debugging_tips"], list):
            raise TypeError("'debugging_tips' must be a list or None.")

    except (KeyError, TypeError) as e:
        raise custom_errors.ConfigurationError(
            f"Internal error: Failed to construct project setup information due to malformed data for '{project_type}/{language}'. Details: {e}"
        )
    except Exception as e:
        raise custom_errors.ConfigurationError(
            f"An unexpected error occurred while generating project setup information: {e}"
        )

    return result

@tool_spec(
    spec={
        'name': 'create_new_jupyter_notebook',
        'description': """ Generates a new Jupyter Notebook (.ipynb) in VS Code.
        
        Generates a new Jupyter Notebook (.ipynb) in VS Code. Jupyter Notebooks
        are interactive documents commonly used for data exploration, analysis,
        visualization, and combining code with narrative text. This tool should
        only be called when the user explicitly requests to create a new Jupyter
        Notebook. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def create_new_jupyter_notebook() -> Dict[str, Any]:
    """Generates a new Jupyter Notebook (.ipynb) in VS Code.

    Generates a new Jupyter Notebook (.ipynb) in VS Code. Jupyter Notebooks
    are interactive documents commonly used for data exploration, analysis,
    visualization, and combining code with narrative text. This tool should
    only be called when the user explicitly requests to create a new Jupyter
    Notebook.

    Returns:
        Dict[str, Any]: Information about the newly created Jupyter Notebook. Contains the following keys:
            file_path (str): The absolute file path of the newly created .ipynb notebook file.
            status (str): Status of the creation operation, typically 'success' if no error is raised.
            message (Optional[str]): A confirmation message or additional details regarding the notebook creation.

    Raises:
        FileCreationError: If the notebook file cannot be created at the intended location (e.g., due to permission issues, invalid path, or disk full).
        JupyterEnvironmentError: If there's an issue with the Jupyter environment setup in VS Code, or required dependencies (like the Jupyter extension itself) are missing or misconfigured.
        InvalidRequestError: If the request to create a notebook is made in an inappropriate context (e.g., if not explicitly requested by the user as per description).
    """
    workspace_root = DB.get("workspace_root")
    if not workspace_root:
        raise custom_errors.JupyterEnvironmentError(
            "Cannot create Jupyter Notebook: Workspace root is not configured."
        )

    # Determine the directory for the new notebook.
    # Default to current working directory (cwd), or workspace_root if cwd is not set.
    target_dir_str = DB.get("cwd", workspace_root)

    try:
        # Resolve to an absolute path and ensure it's a directory within the workspace.
        abs_target_dir = utils.get_absolute_path(target_dir_str)
        if not utils.is_directory(abs_target_dir):
            raise custom_errors.FileCreationError(
                f"Cannot create notebook: The target location '{abs_target_dir}' is not a directory."
            )
    except ValueError as e:
        # Raised by get_absolute_path if path is invalid (e.g., outside workspace).
        raise custom_errors.FileCreationError(
            f"Cannot create notebook: Target directory path '{target_dir_str}' is invalid: {e}"
        )

    # Generate a unique filename (e.g., Untitled.ipynb, Untitled-1.ipynb, ...)
    base_filename = "Untitled"
    extension = ".ipynb"
    counter = 0
    
    current_notebook_name = f"{base_filename}{extension}" # Initial attempt: "Untitled.ipynb"
    final_notebook_abs_path = ""

    while True:
        # Construct the prospective absolute path for the new notebook.
        # os.path.join handles paths correctly, abs_target_dir is already absolute.
        prospective_abs_path = os.path.normpath(os.path.join(abs_target_dir, current_notebook_name))
        
        try:
            # utils.path_exists calls utils.get_absolute_path internally,
            # which validates the path against the workspace and normalizes it.
            if not utils.path_exists(prospective_abs_path):
                # Path does not exist. We need the canonical version of this path.
                # utils.get_absolute_path will provide this and perform final validation.
                final_notebook_abs_path = utils.get_absolute_path(prospective_abs_path)
                break 
            # If path_exists returns True, the file already exists; continue loop.
        except ValueError as e:
            # This error from utils.get_absolute_path (called by utils.path_exists or by us)
            # means the constructed path is outside the workspace or otherwise invalid.
            raise custom_errors.FileCreationError(
                f"Generated notebook path '{prospective_abs_path}' is invalid or outside workspace: {e}"
            )

        counter += 1
        current_notebook_name = f"{base_filename}-{counter}{extension}"
        
        if counter > 1000:  # Safety break to prevent an infinite loop.
            raise custom_errors.FileCreationError(
                "Could not determine a unique notebook name after 1000 attempts. "
                f"Please check the directory '{abs_target_dir}'."
            )

    # Get the default content for the new notebook.
    notebook_content_lines = utils._get_minimal_ipynb_content_lines()
    content_size_bytes = utils.calculate_size_bytes(notebook_content_lines)
    timestamp = utils.get_current_timestamp_iso()

    # Ensure DB["file_system"] exists.
    if "file_system" not in DB:
        DB["file_system"] = {}
    
    # Add the new notebook to the in-memory file system (DB).
    DB["file_system"][final_notebook_abs_path] = {
        "path": final_notebook_abs_path,
        "is_directory": False,
        "content_lines": notebook_content_lines,
        "size_bytes": content_size_bytes,
        "last_modified": timestamp,
    }

    # Prepare the success response.
    notebook_basename = os.path.basename(final_notebook_abs_path)
    # Get the directory part of the final path for the message.
    final_notebook_dir = os.path.dirname(final_notebook_abs_path)
    success_message = (
        f"Jupyter Notebook '{notebook_basename}' created successfully in '{final_notebook_dir}'."
    )
    
    return {
        "file_path": final_notebook_abs_path,
        "status": "success",
        "message": success_message
    }