from common_utils.print_log import print_log
"""
Call logger for API modules.

This module provides a decorator to log function calls to a JSON file.
"""

import json
import functools
import threading
import os
import uuid

# A thread-safe lock to prevent race conditions when multiple calls
# from different threads try to write to the log file simultaneously.
_log_lock = threading.Lock()
RUNTIME_ID = str(uuid.uuid4())

# Get the output directory for the call logs
current_dir = os.path.dirname(__file__)
api_dir = os.path.dirname(current_dir)
gen_agents_dir = os.path.dirname(api_dir)
OUTPUT_DIR = os.path.join(gen_agents_dir, "call_logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(OUTPUT_DIR, f"call_log_{RUNTIME_ID}.json")
_log_file_initialized = False  # Ensures file is cleared only once per process

def set_runtime_id(runtime_id: str):
    """Set a custom runtime ID and update the log file path"""
    global RUNTIME_ID, LOG_FILE_PATH, _log_file_initialized
    RUNTIME_ID = runtime_id
    LOG_FILE_PATH = os.path.join(OUTPUT_DIR, f"call_log_{RUNTIME_ID}.json")
    _log_file_initialized = False  # Reset for new runtime id

def clear_log_file():
    """Clear the current log file to start fresh"""
    global LOG_FILE_PATH, _log_file_initialized
    try:
        if os.path.exists(LOG_FILE_PATH):
            os.remove(LOG_FILE_PATH)
    except (IOError, OSError) as e:
        print_log(f"Warning: Failed to clear log file: {e}")
    _log_file_initialized = True

def log_function_call(package_name: str, flattened_name: str):
    """
    A decorator factory that creates a decorator to log function calls to a JSON file.

    This decorator captures the function's arguments and its response (or any
    exception raised) and logs them in a structured format. All function calls
    within the same runtime will append to the same log file.

    Args:
        package_name (str): The package name for the JSON key (e.g., 'gdrive').
        flattened_name (str): The flattened function name for the JSON key (e.g., 'get_user_profile').
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            global _log_file_initialized
            # Combine positional and keyword arguments into a single dictionary.
            # We use repr() to get a string representation, which is safe for
            # objects that are not directly JSON serializable.
            param_dict = {f"arg_{i}": repr(arg) for i, arg in enumerate(args)}
            param_dict.update({key: repr(value) for key, value in kwargs.items()})

            response_data = None
            entry_name = f"{package_name}.{flattened_name}"
            try:
                # Execute the original function to get its result.
                result = func(*args, **kwargs)
                # Store the string representation of the function's response.
                try: 
                    json.dumps(result)
                    response_data = {"status": "success", "return_value": result}
                except Exception as e:
                    response_data = {"status": "success", "return_value": repr(result)}
                # Return the actual result to the original caller.
                return result
            except Exception as e:
                # If the function raises an exception, log the error message.
                response_data = {
                    "status": "error",
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                }
                # Re-raise the exception to not alter the program's control flow.
                raise
            finally:
                # Construct the log entry in the desired format:
                # { "flattened_path": { "param_dict": {...}, "response": "..." } }
                log_entry = {
                    "function_name": entry_name,
                    "param_dict": param_dict,
                    "response": response_data
                }

                # Use a lock to safely append the new log entry to the JSON file.
                with _log_lock:
                    # On first log write in this process, clear the file if it exists
                    if not _log_file_initialized:
                        if os.path.exists(LOG_FILE_PATH):
                            try:
                                os.remove(LOG_FILE_PATH)
                            except (IOError, OSError) as e:
                                print_log(f"Warning: Failed to clear log file: {e}")
                        _log_file_initialized = True
                    log_data = []
                    try:
                        # Check if the log file exists and has content
                        if os.path.exists(LOG_FILE_PATH):
                            file_size = os.path.getsize(LOG_FILE_PATH)
                            if file_size > 0:
                                with open(LOG_FILE_PATH, "r") as f:
                                    # Load existing log data. If file is malformed, start fresh.
                                    try:
                                        log_data = json.load(f)
                                        if not isinstance(log_data, list):
                                            log_data = [] # Reset if the file doesn't contain a list.
                                    except (json.JSONDecodeError, ValueError):
                                        # Handle any JSON parsing errors, including empty files
                                        log_data = []
                            # If file exists but is empty (file_size == 0), log_data remains []
                        # Note: We don't delete existing files here since we want to append within the same runtime
                        # If you want to start fresh each time, delete the file before the first call
                    except (IOError, FileNotFoundError, OSError):
                        # If there are any file system errors, start with an empty list.
                        log_data = []

                    # Append the new entry for the current function call.
                    log_data.append(log_entry)

                    # Write the updated list back to the file.
                    try:
                        with open(LOG_FILE_PATH, "w") as f:
                            json.dump(log_data, f, indent=4)
                    except (IOError, OSError) as e:
                        # Log the error but don't fail the function call
                        print_log(f"Warning: Failed to write to call log file: {e}")

        return wrapper
    return decorator
