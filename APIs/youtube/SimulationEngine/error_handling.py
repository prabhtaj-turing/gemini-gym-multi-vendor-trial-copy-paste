# api_error_handler.py (Your original file)

import os
import functools
import sys
import datetime
import traceback
import inspect
import json
from typing import Optional

ENV_VAR_PACKAGE_ERROR_MODE = "OVERWRITE_ERROR_MODE"
VALID_ERROR_MODES = {"raise", "error_dict"}
PACKAGE_DEFAULT_ERROR_MODE = "raise"


def get_package_error_mode() -> str:
    """
    Determines the error handling mode for the entire package:
    1. Environment Variable (ENV_VAR_PACKAGE_ERROR_MODE)
    2. Package-wide default constant (PACKAGE_DEFAULT_ERROR_MODE)
    """
    env_mode = os.environ.get(ENV_VAR_PACKAGE_ERROR_MODE, "").upper()
    if env_mode in VALID_ERROR_MODES:
        return env_mode
    return PACKAGE_DEFAULT_ERROR_MODE


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
    original_func_path: Optional[str] = None  # NEW: Optional path to the original function
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
        "exceptionType": exc_type_name,
        "message": str(exc_value),
        "module": report_module,      # Use the potentially overridden module
        "function": report_function,  # Use the potentially overridden function
        "traceback": traceback.format_exception(exc_type, exc_value, tb),
        "causes": [],
    }

    # Populate causes (same logic as before)
    current_chain_link = caught_exception.__cause__
    if (
        not current_chain_link
        and caught_exception.__context__ is not caught_exception.__cause__
    ):
        current_chain_link = caught_exception.__context__

    processed_causes = {id(caught_exception)}
    while (
        current_chain_link
        and id(current_chain_link) not in processed_causes
    ):
        processed_causes.add(id(current_chain_link))
        cause_exc_type = type(current_chain_link)
        cause_tb = current_chain_link.__traceback__
        cause_module_origin, cause_function_origin = _get_exception_origin(
            cause_tb
        )
        cause_exc_type_m = (
            cause_exc_type.__module__
            if cause_exc_type.__module__ not in ("builtins", None)
            else ""
        )
        cause_exc_type_n = f"{cause_exc_type_m}{'.' if cause_exc_type_m else ''}{cause_exc_type.__name__}"
        cause_entry = {
            "exceptionType": cause_exc_type_n,
            "message": str(current_chain_link),
            "module": cause_module_origin,
            "function": cause_function_origin,
        }
        if include_mini_traceback_for_causes and cause_tb:
            cause_entry["miniTraceback"] = _format_mini_traceback(cause_tb)
        report["causes"].append(cause_entry)
        next_cause = current_chain_link.__cause__
        next_context = current_chain_link.__context__
        current_chain_link = next_cause or (
            next_context if next_context is not next_cause else None
        )


    current_behavior_mode = get_package_error_mode()

    if current_behavior_mode == "error_dict":
        return report
    else:  # Default to "raise"
        print(
            f"--- SDK Error Report (Behavior: raise, Module: {report_module}, EffectiveMode: {current_behavior_mode}) ---"
        )
        print(json.dumps(report, indent=2))
        print("-------------------------------")
        raise caught_exception # Re-raise the original exception


# --- The Decorator ---
def handle_api_errors(include_mini_traceback_for_causes=True):
    def decorator(func_to_decorate):
        @functools.wraps(func_to_decorate)
        def wrapper(*args, **kwargs):
            func_module_name = func_to_decorate.__module__

            try:
                return func_to_decorate(*args, **kwargs)
            except Exception as caught_exception:
                # Call the centralized processing function.
                # For natural errors, original_func_path is None,
                # so the module/function will be derived from the traceback.
                return process_caught_exception(
                    caught_exception,
                    func_module_name,
                    include_mini_traceback_for_causes,
                    original_func_path=None  # Pass None explicitly for natural errors
                )

        return wrapper

    return decorator