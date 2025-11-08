"""
Test File Management module for Copilot API.
Provides functions for test file operations.
"""
from common_utils.tool_spec_decorator import tool_spec
import os
from typing import Any, Optional, Tuple
from typing import Dict, List

import pytest

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine import utils
from copilot.SimulationEngine.db import DB
from copilot.SimulationEngine.utils import extract_module_details, is_in_test_dir, generate_related_file_candidates


@pytest.mark.skip(reason="Not a test function")
@tool_spec(
    spec={
        'name': 'test_search',
        'description': """ For a source code file, find the file that contains the tests. For a test file find the file that contains the code under test.
        
        This function processes a given `file_path`. If `file_path` points to a source code file, the function searches for the file containing its tests.
        Conversely, if `file_path` points to a test file, the function searches for the file containing the code under test.
        The outcome of this search, including the path to the related file (if found), the type of relationship, and a confidence score, is returned. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'file_path': {
                    'type': 'string',
                    'description': 'The absolute path to the source code file or test file for which to find its related counterpart.'
                }
            },
            'required': [
                'file_path'
            ]
        }
    }
)
def test_search(file_path: str) -> Dict[str, Any]:
    """For a source code file, find the file that contains the tests. For a test file find the file that contains the code under test.

    This function processes a given `file_path`. If `file_path` points to a source code file, the function searches for the file containing its tests.
    Conversely, if `file_path` points to a test file, the function searches for the file containing the code under test.
    The outcome of this search, including the path to the related file (if found), the type of relationship, and a confidence score, is returned.

    Args:
        file_path (str): The absolute path to the source code file or test file for which to find its related counterpart.

    Returns:
        Dict[str, Any]: A dictionary containing details of the identified related file with the following keys:
            input_file_path (str): The path of the input file (either source or test) for which a related file was searched.
            related_file_path (Optional[str]): The path to the corresponding test file (if input was source) or source file (if input was test). Null if no confidently related file is found.
            relationship_type (Optional[str]): Describes the identified relationship, e.g., 'test_file_for_source' or 'source_file_for_test'. Null if no related file is found.
            confidence_score (Optional[float]): A score between 0.0 and 1.0 indicating the confidence in the match, if applicable and calculable. Null otherwise.

    Raises:
        FileNotFoundError: If the input file path provided in `file_path` does not exist in the workspace.
        ProjectConfigurationError: If project configuration or conventions needed to determine test/source relationships are missing, ambiguous, or invalid.
        SearchLogicError: If an internal error occurs within the test search logic.
        ValidationError: If input arguments fail validation.
    """
    # --- Input Validation ---
    if not isinstance(file_path, str):
        raise custom_errors.ValidationError("Input 'file_path' must be a string")
    if not file_path:  # Check after type check
        raise custom_errors.ValidationError("Input 'file_path' cannot be empty")

    # --- Configuration Checks ---
    workspace_root_from_db = DB.get("workspace_root")
    if not workspace_root_from_db:
        raise custom_errors.ProjectConfigurationError("Workspace root is not configured.")

    normalized_workspace_root = utils._normalize_path_for_db(workspace_root_from_db)

    # --- Path Resolution and Initial Validation ---
    abs_input_path: str
    try:
        abs_input_path = utils.get_absolute_path(file_path)
    except ValueError as e:
        raise custom_errors.ProjectConfigurationError(str(e)) from e

    try:
        if not utils.path_exists(abs_input_path):
            raise custom_errors.FileNotFoundError(f"File not found: {abs_input_path}")

        if not utils.is_file(abs_input_path):
            raise custom_errors.ProjectConfigurationError(
                f"Input path must be a file, not a directory: {abs_input_path}")
    except (AttributeError, TypeError) as e:
        raise custom_errors.SearchLogicError(
            f"Internal error processing file system data for path {abs_input_path}"
        ) from e

    # --- Core Logic ---
    input_filename = os.path.basename(abs_input_path)
    input_file_dir_abs = utils._normalize_path_for_db(os.path.dirname(abs_input_path))

    module_details = extract_module_details(input_filename)

    is_input_test_by_name = module_details["is_test_by_name"]
    is_input_in_test_dir = is_in_test_dir(input_file_dir_abs, normalized_workspace_root)

    is_input_likely_test = is_input_test_by_name or is_input_in_test_dir

    module_name_for_matching = module_details["base_module_name"]
    current_ext = module_details["ext"]

    potential_candidates: List[Tuple[str, float]] = []
    relationship_type: Optional[str] = None

    if is_input_likely_test:
        relationship_type = "source_file_for_test"
        if module_name_for_matching:
            potential_candidates = generate_related_file_candidates(
                input_file_dir_abs, module_name_for_matching, current_ext,
                is_searching_for_test_file=False, workspace_root_abs=normalized_workspace_root
            )
    else:
        relationship_type = "test_file_for_source"
        if module_name_for_matching:
            potential_candidates = generate_related_file_candidates(
                input_file_dir_abs, module_name_for_matching, current_ext,
                is_searching_for_test_file=True, workspace_root_abs=normalized_workspace_root
            )

    valid_matches: List[Tuple[str, float]] = []
    for cand_path, conf in potential_candidates:
        try:
            if cand_path != abs_input_path and utils.path_exists(cand_path) and utils.is_file(cand_path):
                valid_matches.append((cand_path, conf))
        except (AttributeError, TypeError):
            pass

    valid_matches.sort(key=lambda x: x[1], reverse=True)

    result: Dict[str, Any] = {
        "input_file_path": abs_input_path,
        "related_file_path": None,
        "relationship_type": None,
        "confidence_score": None,
    }

    if valid_matches:
        best_match_path, best_confidence = valid_matches[0]
        result["related_file_path"] = utils._normalize_path_for_db(best_match_path)
        result["relationship_type"] = relationship_type
        result["confidence_score"] = best_confidence

    if result["related_file_path"] is None:
        result["relationship_type"] = None

    return result
