"""
Call LLM API Service

This package provides LLM-specific functionality for interacting with Google Generative AI models,
including text generation, function calling, and docstring-to-tool conversion.

Functions:
    - make_tool_from_docstring: Converts Python docstrings to Google AI Tool objects
    - generate_llm_response: Generates text responses from LLM models
    - generate_llm_response_with_tools: Generates responses with function calling capabilities
"""
import os
from common_utils.init_utils import create_error_simulator, resolve_function_import
from common_utils.error_handling import get_package_error_mode
from . import llm_execution

# Get the directory of the current file
_INIT_PY_DIR = os.path.dirname(__file__)

# Create error simulator using the utility function
error_simulator = create_error_simulator(_INIT_PY_DIR)

# Get the error mode for the package
ERROR_MODE = get_package_error_mode()

# Function map - only LLM functions
_function_map = {
    "make_tool_from_docstring": "call_llm.llm_execution.make_tool_from_docstring",
    "generate_llm_response": "call_llm.llm_execution.generate_llm_response",
    "generate_llm_response_with_tools": "call_llm.llm_execution.generate_llm_response_with_tools",
}

def __getattr__(name: str):
    return resolve_function_import(name, _function_map, error_simulator)

def __dir__():
    return sorted(set(globals().keys()) | set(_function_map.keys()))

__all__ = list(_function_map.keys())