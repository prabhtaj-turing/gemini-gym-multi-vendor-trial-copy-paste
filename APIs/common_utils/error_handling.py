from common_utils.print_log import print_log
"""
Error handling for API modules.

This module provides a decorator to handle errors in API functions.

Configuration:
- OVERWRITE_ERROR_MODE: Controls error handling mode ("raise" or "error_dict")
- PRINT_ERROR_REPORTS: Controls whether error reports are printed to stdout
  - Set to "true", "1", "yes", or "on" to enable printing
  - Set to "false", "0", "no", or "off" to disable printing (default)
  - Any other value uses the package default (disabled)

By default, error reports are NOT printed to avoid cluttering user output.
Users can enable printing for debugging purposes by setting the PRINT_ERROR_REPORTS environment variable.
"""

from contextlib import contextmanager
import os
import functools
import sys
import datetime
import traceback
import inspect
import importlib
import types
import json
from typing import Optional, Dict, Any

ENV_VAR_PACKAGE_ERROR_MODE = "OVERWRITE_ERROR_MODE"
ENV_VAR_PRINT_ERROR_REPORTS = "PRINT_ERROR_REPORTS"
VALID_ERROR_MODES = {"raise", "error_dict"}
PACKAGE_DEFAULT_ERROR_MODE = "raise"
PACKAGE_DEFAULT_PRINT_ERROR_REPORTS = False

_global_override = None
_context_stack = []


def get_package_error_mode() -> str:
    """
    Determines the error handling mode for the entire package:
    1. Environment Variable (ENV_VAR_PACKAGE_ERROR_MODE)
    2. Package-wide default constant (PACKAGE_DEFAULT_ERROR_MODE)
    
    Priority: context > global > environment > default
    """
    if _context_stack:
       return _context_stack[-1]
    if _global_override:
        return _global_override
    env_mode = os.environ.get(ENV_VAR_PACKAGE_ERROR_MODE, "").lower()
    if env_mode in VALID_ERROR_MODES:
        return env_mode
    return PACKAGE_DEFAULT_ERROR_MODE

def set_package_error_mode(mode: str):
    """
    Set global error mode override.
    """
    global _global_override
    if mode not in VALID_ERROR_MODES:
        raise ValueError(f"Invalid error mode: {mode}")
    _global_override = mode


def reset_package_error_mode():
    """Reset to use environment variable."""
    global _global_override, _context_stack
    _global_override = None
    _context_stack.clear()


@contextmanager
def temporary_error_mode(mode: str):
    """Temporarily override error mode within context."""
    global _context_stack
    
    if mode not in VALID_ERROR_MODES:
        raise ValueError(f"Invalid error mode: {mode}")
    
    _context_stack.append(mode)
    try:
        yield
    finally:
        _context_stack.pop()


def get_print_error_reports() -> bool:
    """
    Determines whether error reports should be printed to stdout:
    1. Environment Variable (ENV_VAR_PRINT_ERROR_REPORTS)
    2. Package-wide default constant (PACKAGE_DEFAULT_PRINT_ERROR_REPORTS)
    """
    env_print = os.environ.get(ENV_VAR_PRINT_ERROR_REPORTS, "").lower()
    if env_print in ("true", "1", "yes", "on"):
        return True
    elif env_print in ("false", "0", "no", "off"):
        return False
    return PACKAGE_DEFAULT_PRINT_ERROR_REPORTS

def _get_exception_origin(tb_or_frames):
    if not tb_or_frames:
        return None, None
    frames = (
        traceback.extract_tb(tb_or_frames)
        if hasattr(tb_or_frames, "tb_frame")
        else tb_or_frames
    )
    if not frames:
        return None, None
    last_frame = frames[-1]
    module_name = None
    try:
        module_obj = inspect.getmodule(last_frame.filename)
        module_name = module_obj.__name__ if module_obj else last_frame.filename.split("/")[-1].replace(".py", "")  # Fallback
    except Exception:
        module_name = last_frame.filename.split("/")[-1].replace(".py", "")  # Fallback
    return module_name, last_frame.name

def _format_mini_traceback(tb_or_frames, max_frames=5):
    if not tb_or_frames:
        return []
    frames = (
        traceback.extract_tb(tb_or_frames)
        if hasattr(tb_or_frames, "tb_frame")
        else tb_or_frames
    )
    if not frames:
        return []
    return [
        f'  File "{f.filename}", line {f.lineno}, in {f.name}\n    {f.line}'
        for f in frames[-max_frames:]
    ]


def process_caught_exception(
    caught_exception: Exception,
    func_module_name: str,  # The module name context from the calling function
    include_mini_traceback_for_causes: bool = True,
    original_func_path: Optional[str] = None,  # NEW: Optional path to the original function
    service_name: Optional[str] = None  
):
    """
    Centralized function to process a caught exception, generate a report,
    and handle it based on the package error mode.
    Returns the error report dictionary if mode is error_dict, otherwise re-raises.
    If original_func_path is provided, the 'module' and 'function' fields in the report
    will reflect this path, overriding what is derived from the traceback (which might point to a wrapper).
    """
    # Get the current exception info from sys.exc_info()
    exc_type, exc_value, tb = sys.exc_info()

    # Determine the primary origin from the traceback
    primary_module_from_tb, primary_function_from_tb = _get_exception_origin(tb)

    # NEW LOGIC: Use original_func_path if provided, otherwise fallback to traceback origin
    report_module = func_module_name  # Default to what the decorator passed
    report_function = primary_function_from_tb

    if original_func_path:
        parts = original_func_path.rsplit('.', 1)
        if len(parts) == 2:
            report_module = parts[0]
            report_function = parts[1]
        else:  # Handle cases where it might be just a function name if no module specified
            report_function = original_func_path
            # Try to infer module from primary_module_from_tb if original_func_path was just a function name
            if not report_module and primary_module_from_tb:
                report_module = primary_module_from_tb.split('.')
        
    module_parts = report_module.split('.')
    if len(module_parts) > 1:
        report_module = module_parts[-1]

    exc_type_module = (
        exc_type.__module__
        if exc_type.__module__ not in ("builtins", None)
        else ""
    )
    exc_type_name = f"{exc_type_module}{'.' if exc_type_module else ''}{exc_type.__name__}"

    report = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "message": str(exc_value),
        "exceptionType": exc_type_name,
        "status": "error"
    }

    return report

def load_service_error_format_adapter(service_name: Optional[str]) -> Optional[types.FunctionType]:
    """
    Load the service formatter for the given service name.

    Args:
        service_name(Optional[str]): The name of the service to load the formatter for.
            If not provided, the default error formatter will be used.

    Returns:
        (Optional[types.FunctionType]): The service formatter function. If no formatter is found, None is returned.
    """
    if not service_name:
        return None
    try:
        module = importlib.import_module(f"APIs.{service_name}.SimulationEngine.error_format_adapter")
        return getattr(module, "error_format_adapter", None)
    except (ImportError, AttributeError):
        return None
        
def error_format_handler(
        caught_exception: Exception, 
        func_module_name: str,  
        include_mini_traceback_for_causes: bool = True,
        original_func_path: Optional[str] = None, 
        service_name: Optional[str] = None
    ) -> Dict[str, Any]:
    """
    Format the error for the given service.

    Args:
        caught_exception(Exception): The exception to format.
        func_module_name(str): The module name of the function that raised the error.
        service_name(Optional[str]): The name of the service to format the error for.
        original_func_path(Optional[str]): The path to the original function that raised the error.
        include_mini_traceback_for_causes(bool): Whether to include a mini traceback for causes.
    
    Returns:
        (Dict[str, Any]): The formatted error.
    """

    if service_name:
        current_behavior_mode = get_service_level_error_mode(service_name)
    else:
        current_behavior_mode = get_package_error_mode()

    formatted_error = None
    service_name = func_module_name.split('.')[0]
    service_formatter = load_service_error_format_adapter(service_name)

    if isinstance(service_formatter, types.FunctionType):
        try:
            formatted_error = service_formatter(caught_exception)
        except Exception:
            pass  # fallback to default if custom formatter breaks

    if not formatted_error:
        formatted_error = process_caught_exception(caught_exception, func_module_name, include_mini_traceback_for_causes, original_func_path, service_name)

    if current_behavior_mode == "error_dict":
        return formatted_error
    else:  # Default to "raise"
        # Check if error reports should be printed based on configuration
        if get_print_error_reports():

            print_log(
                f"--- SDK Error Report (Behavior: raise, Module: {func_module_name}, EffectiveMode: {current_behavior_mode}) ---"
            )
            print_log(json.dumps(formatted_error, indent=2))
            print_log("-------------------------------")
        raise caught_exception # Re-raise the original exception


def get_service_level_error_mode(service_name: str) -> str:
    """
    Get error mode for a specific service with priority:
    1. Context override (highest priority)
    2. Service-specific override (if ErrorManager is active)
    3. Global override
    4. Environment variable
    5. Default (lowest priority)
    
    Args:
        service_name: Name of the service (e.g., "gmail", "github")
        
    Returns:
        Error mode string ("raise" or "error_dict")
    """
    # First check for context override (highest priority)
    if _context_stack:
        return _context_stack[-1]
    
    # Then check for service-specific override from ErrorManager
    try:
        from .error_manager import get_error_manager
        error_manager = get_error_manager()
        if error_manager._is_active and service_name in error_manager.service_configs:
            service_config = error_manager.service_configs[service_name]
            if "error_mode" in service_config:
                return service_config["error_mode"]
    except (ImportError, AttributeError):
        # ErrorManager not available or not properly initialized
        pass
    
    # Fall back to standard package error mode
    return get_package_error_mode()


# --- The Decorator ---
def handle_api_errors(include_mini_traceback_for_causes=True):
    def decorator(func_to_decorate):
        @functools.wraps(func_to_decorate)
        def wrapper(*args, **kwargs):
            func_module_name = func_to_decorate.__module__
            service_name = None
            try:
                # e.g. APIs.gmail.service -> gmail
                # or gmail.mutations... -> gmail
                parts = func_module_name.split('.')
                candidate = None
                
                # If path starts with APIs, service is the second part
                if len(parts) > 1 and parts[0] == 'APIs':
                    candidate = parts[1]
                # Otherwise, service is the first part
                elif parts:
                    candidate = parts[0]

                # Exclude common utils from being treated as a service
                if candidate and candidate != 'common_utils':
                    service_name = candidate
            except:
                # Fallback if module name is not as expected
                pass

            try:
                return func_to_decorate(*args, **kwargs)
            except Exception as caught_exception:
                # Call the centralized processing function.
                # For natural errors, original_func_path is None,
                # so the module/function will be derived from the traceback.
                return error_format_handler(
                    caught_exception,
                    func_module_name,
                    include_mini_traceback_for_causes,
                    original_func_path=None,  # Pass None explicitly for natural errors
                    service_name=service_name
                )

        return wrapper

    return decorator