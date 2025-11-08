import traceback
from typing import Any, Dict, Union
import datetime
def error_format_adapter(error: Exception) -> Dict[str, Any]:
    """
    Format the error for the airline service.

    Args:
        error(Exception): The error to format.

    Returns:
        (Union[str, Dict[str, Any]]): The formatted error.

    Raises:
        ValueError: If the error is not an Exception or a dict.
    """
    if isinstance(error, Exception):
        return {
                "status": "error",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
                "message": str(error),
            }
    else:
        raise ValueError(f"Invalid error type: {type(error)}")