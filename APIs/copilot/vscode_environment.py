"""
VS Code Environment module for Copilot API.
Provides functions for VS Code specific operations.
"""
from common_utils.tool_spec_decorator import tool_spec
import collections
from typing import Dict, Any, List

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'get_vscode_api',
        'description': """ Get relevant VS Code API references to answer questions about VS Code extension development.
        
        This function gets relevant VS Code API references to answer questions about VS Code
        extension development. It is used when the user asks about VS Code APIs,
        capabilities, or best practices related to developing VS Code extensions.
        It is used in all VS Code extension development workspaces. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The query to search vscode documentation for. Should contain all
                    relevant context. """
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def get_vscode_api(query: str) -> Dict[str, Any]:
    """Get relevant VS Code API references to answer questions about VS Code extension development.

    This function gets relevant VS Code API references to answer questions about VS Code
    extension development. It is used when the user asks about VS Code APIs,
    capabilities, or best practices related to developing VS Code extensions.
    It is used in all VS Code extension development workspaces.

    Args:
        query (str): The query to search vscode documentation for. Should contain all
            relevant context.

    Returns:
        Dict[str, Any]: A dictionary containing the function's results, with the following key:
            api_references (List[Dict[str, Any]]): A list of relevant VS Code API
                references. Each dictionary in this list provides details about an
                API element and includes the following keys:
                name (str): The name of the API element (e.g., class name, function
                    name, property name).
                documentation_summary (str): A summary of the API's documentation
                    or purpose.
                module (str): The VS Code API module or namespace the element
                    belongs to (e.g., 'vscode.window', 'vscode.commands').
                kind (str): The kind of the API element (e.g., 'class', 'function',
                    'interface', 'enum', 'property', 'event').
                signature (Optional[str]): The signature of the function or method,
                    if applicable.
                example_usage (Optional[str]): A brief code example demonstrating
                    the use of the API element.

    Raises:
        QueryTooBroadError: If the query for API references is too vague to yield
            specific or useful results.
        APIDatabaseNotAvailableError: If the VS Code API reference database cannot
            be accessed or is not initialized.
        ValidationError: If input arguments fail validation.
    """
    _MIN_QUERY_LEN_FOR_API_SEARCH = 3
    _MAX_API_RESULTS_THRESHOLD = 20
    _VSCODE_API_DB_KEY = "vscode_api_references"
    _SPECIFIC_TOO_BROAD_TERMS_LOWER = {"generic term"}

    if not isinstance(query, str):
        raise custom_errors.ValidationError(f"Input should be a valid string, query: {type(query)}")
    cleaned_query = query.strip()

    # Check for empty or whitespace-only query
    if not cleaned_query:
        raise custom_errors.QueryTooBroadError("Query is empty or too broad.")

    # Check for specific "too broad" terms (case-insensitive)
    if cleaned_query.lower() in _SPECIFIC_TOO_BROAD_TERMS_LOWER:
        raise custom_errors.QueryTooBroadError(f"Query '{cleaned_query}' is too vague.")

    # This check should logically come after validating the query is not empty or just whitespace.
    if len(cleaned_query) < _MIN_QUERY_LEN_FOR_API_SEARCH:
        raise custom_errors.QueryTooBroadError(
            f"Query '{cleaned_query}' is too short (minimum {_MIN_QUERY_LEN_FOR_API_SEARCH} characters required). Please be more specific."
        )

    api_data = DB.get(_VSCODE_API_DB_KEY)

    if api_data is None:
        raise custom_errors.APIDatabaseNotAvailableError(
            "VS Code API reference database not available."
        )

    if not isinstance(api_data, collections.abc.Sequence) or isinstance(api_data, str):
        raise custom_errors.APIDatabaseNotAvailableError(
            "VS Code API reference database is not available or not correctly initialized (expected a list of API entries)."
        )

    if not all(isinstance(item, dict) for item in api_data):
        raise custom_errors.APIDatabaseNotAvailableError(
            "VS Code API reference database contains malformed entries (non-dictionary items found)."
        )

    query_lower = cleaned_query.lower()
    found_references: List[Dict[str, Any]] = []
    required_keys_in_api_entry = ["name", "documentation_summary", "module", "kind"]

    for item in api_data:
        # Ensure item is a dictionary and has all required string fields with non-empty values.
        if not isinstance(item, dict):
            continue

        is_valid_entry = True
        for req_key in required_keys_in_api_entry:
            # Check for presence, correct type (string), and non-empty string value.
            if not (req_key in item and isinstance(item[req_key], str) and item[req_key].strip()):
                is_valid_entry = False
                break
        if not is_valid_entry:
            continue  # Skip malformed or incomplete entries silently.

        match = False
        # Perform case-insensitive search in relevant fields.
        if query_lower in item["name"].lower():
            match = True
        elif query_lower in item["documentation_summary"].lower():
            match = True
        elif query_lower in item["module"].lower():
            match = True

        if match:
            # Ensure optional fields are either strings or None.
            signature = item.get("signature")
            if signature is not None and not isinstance(signature, str):
                signature = None  # Or log a warning about malformed optional field

            example_usage = item.get("example_usage")
            if example_usage is not None and not isinstance(example_usage, str):
                example_usage = None  # Or log a warning

            # Construct the reference item with all expected fields.
            reference_item = {
                "name": item["name"],
                "documentation_summary": item["documentation_summary"],
                "module": item["module"],
                "kind": item["kind"],
                "signature": signature,
                "example_usage": example_usage,
            }
            found_references.append(reference_item)

    if len(found_references) > _MAX_API_RESULTS_THRESHOLD:
        raise custom_errors.QueryTooBroadError(
            f"Query returned {len(found_references)} results, exceeding the limit of {_MAX_API_RESULTS_THRESHOLD}. "
            "Please refine your query for more specific results."
        )

    return {"api_references": found_references}


@tool_spec(
    spec={
        'name': 'install_extension',
        'description': """ Install an extension in VS Code.
        
        This function installs an extension in Visual Studio Code. It is intended for use
        exclusively as part of a new workspace creation process. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'extension_id': {
                    'type': 'string',
                    'description': """ The unique identifier of the Visual Studio Code extension
                    to be installed (e.g., 'ms-python.python'). """
                }
            },
            'required': [
                'extension_id'
            ]
        }
    }
)
def install_extension(extension_id: str) -> Dict[str, Any]:
    """Install an extension in VS Code.

    This function installs an extension in Visual Studio Code. It is intended for use
    exclusively as part of a new workspace creation process.

    Args:
        extension_id (str): The unique identifier of the Visual Studio Code extension
            to be installed (e.g., 'ms-python.python').

    Returns:
        Dict[str, Any]: The result of the attempt to install a VS Code extension.
            This dictionary contains the following keys:
            extension_id (str): The ID of the extension that was targeted for
                installation.
            status (str): The outcome of the installation attempt (e.g., 'success',
                'failed', 'already_installed', 'not_found').
            message (Optional[str]): An optional message providing more details
                about the installation status, such as an error message if it failed.

    Raises:
        ExtensionNotFoundError: If the specified extension ID cannot be found in the
            VS Code Marketplace or available sources.
        InstallationFailedError: If the extension installation process fails due to
            system issues, permissions, or VS Code internal errors.
        UsageContextError: If this tool is used outside the intended context of a
            new workspace creation process.
        ValidationError: If input arguments fail validation.
    """

    # 1. Usage Context Check
    # The function is intended for use only during new workspace creation.
    if DB['vscode_context'].get('is_new_workspace_creation') is not True:
        raise custom_errors.UsageContextError(
            "Extension installation is only allowed during a new workspace creation process."
        )

    # 2. Input Validation for extension_id
    if not isinstance(extension_id, str) or not extension_id.strip():
        raise custom_errors.ValidationError("Extension ID must be a non-empty string.")

    cleaned_extension_id = extension_id.strip()

    # Validate format: publisher.name (e.g., 'ms-python.python')
    # A simple check for a dot separating two non-empty parts.
    parts = cleaned_extension_id.split('.')
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise custom_errors.ValidationError(
            f"Invalid extension ID format for '{cleaned_extension_id}'. Expected 'publisher.name'."
        )

    # 3. Check if extension exists in the (mock) marketplace
    if ('vscode_extensions_marketplace' not in DB or
            cleaned_extension_id not in [extension['id'] for extension in DB['vscode_extensions_marketplace']]):
        raise custom_errors.ExtensionNotFoundError(
            f"Extension '{cleaned_extension_id}' not found in the marketplace."
        )

    # 4. Check if already installed
    # Assumes DB['installed_extensions'] is a list of strings (extension IDs)
    if cleaned_extension_id in DB['installed_vscode_extensions']:
        return {
            "extension_id": cleaned_extension_id,
            "status": "already_installed",
            "message": f"Extension '{cleaned_extension_id}' is already installed."
        }

    # 5. Simulate Installation Attempt
    if (cleaned_extension_id not in DB["extensions_simulated_install_behavior"] or
            DB["extensions_simulated_install_behavior"][cleaned_extension_id] != "success"):
        raise custom_errors.InstallationFailedError(
            f"Simulated system error prevented installation of '{cleaned_extension_id}'. "
            "This could be due to issues like VS Code CLI unavailability or permission problems."
        )

    if cleaned_extension_id == "ext.installationfailure":
        return {
            "extension_id": cleaned_extension_id,
            "status": "failed",
            "message": f"Installation of extension '{cleaned_extension_id}' failed. "
                       "Simulated reason: Incompatible with current VS Code version or corrupted package."
        }

    # Add to the list of installed extensions in our simulated DB.
    DB['installed_vscode_extensions'].append(cleaned_extension_id)

    return {
        "extension_id": cleaned_extension_id,
        "status": "success",
        "message": f"Extension '{cleaned_extension_id}' installed successfully."
    }