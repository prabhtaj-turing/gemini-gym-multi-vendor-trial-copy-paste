import importlib, sys
from typing import Dict, Any, Type
from pydantic import BaseModel, create_model, ValidationError
from pathlib import Path
import re
from zoneinfo import ZoneInfo
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]  # repo root
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

def build_central_db_model(module_name: str) -> Type[BaseModel]:
    """
    Dynamically load all Pydantic models from a module and wrap them
    into a single 'CentralDB' model that represents the whole service schema.

    Args:
        module_name (str): Python module path, e.g. 'APIs.google_calendar.SimulationEngine.models'

    Returns:
        Type[BaseModel]: Central Pydantic model for validating the entire DB.
    """
    module = importlib.import_module(module_name)

    # Extract all Pydantic BaseModel subclasses from the module
    models: Dict[str, Type[BaseModel]] = {
        name: obj
        for name, obj in vars(module).items()
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel
    }

    if not models:
        raise ValueError(f"No Pydantic models found in {module_name}")

    # Dynamically create the central DB model
    CentralDB = create_model(
        "CentralDB",
        **{name: (obj, None) for name, obj in models.items()}  # all models optional top-level
    )

    return CentralDB


def validate_with_default_schema(schema_module: str, ported_db: dict) -> tuple[bool, str]:
    """
    Validate a ported DB dict against the dynamically built central model.
    """
    CentralDBModel = build_central_db_model(schema_module)
    try:
        CentralDBModel.model_validate(ported_db)
        return True, "Validation successful"
    except ValidationError as e:
        return False, str(e)

# DateTime and TimeZone Helpers
class DateTimeValidationError(Exception):
    """Custom exception for datetime validation errors."""
    pass

def is_datetime_of_format(datetime_str: str, format_type: str) -> bool:
    """
    Checks if a datetime string is of a given format.

    Args:
        datetime_str (str): The datetime string to check
        format_type (str): The expected format type
    
    Returns:
        bool: True if the datetime string is of the given format, False otherwise
    
    Raises:
        DateTimeValidationError: If the format_type is not supported
    
    Example:
        >>> is_datetime_of_format("2024-03-15T14:30:45Z", "ISO_8601_UTC_Z")
        True
        >>> is_datetime_of_format("2024-03-15 14:30:45", "ISO_8601_UTC_Z")
        False
    """    
    if format_type == "ISO_8601_UTC_Z":
        return re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$', datetime_str) is not None
    elif format_type == "ISO_8601_UTC_OFFSET":
        return re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$', datetime_str) is not None
    elif format_type == "ISO_8601_WITH_TIMEZONE":
        return re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', datetime_str) is not None
    else:
        raise DateTimeValidationError(f"Unsupported format type: {format_type}")

def is_timezone_valid(timezone: str) -> bool:
    """
    Checks if a timezone string is valid in the IANA format.

    Args:
        timezone (str): The timezone string to check
    
    Returns:
        bool: True if the timezone string is valid, False otherwise
    
    Example:
        >>> is_timezone_valid("America/Sao_Paulo")
        True
        >>> is_timezone_valid("invalid_timezone")
        False
    """
    try:
        ZoneInfo(timezone)
        return True
    except Exception:
        return False

def local_to_UTC(resource: Dict[str, str]) -> Dict[str, str]:
    """
    Converts a datetime string from a local timezone to UTC timezone.

    Args:
        resource (Dict[str, str]): A dictionary with the following keys:
            - dateTime (str): The datetime string to convert. If the datetime string has timezone information, the datetime string is converted based on this timezone information.
            - timeZone (Optional[str]): The timezone to use in IANA format (e.g. "America/Sao_Paulo"). This timezone information is used to convert the datetime string only if the datetime string does not have timezone information. Default to None.
    
    Returns:
        A dictionary with the following elements:
            - dateTime (str): The datetime string in UTC timezone and in the naive format "YYYY-MM-DDTHH:MM:SS"
            - offset (str): The offset of the datetime string from UTC in the format "+/-HH:SS" (e.g. "+03:00" or "-04:00"). None if the datetime string has timezone information.
            - timeZone (Optional[str]): The local timezone in IANA format. None if the datetime string has timezone information.
    
    Raises:
        DateTimeValidationError: If the datetime string is invalid; or
                                 timezone is invalid; or
                                 nor the datetime have timezone info nor the timezone is provided.
    
    Example:
        >>> local_to_UTC({"dateTime": "2024-03-15T14:30:45Z"})
        {"dateTime": "2024-03-15T14:30:45", "offset": "+00:00", "timeZone": None}
        >>> local_to_UTC({"dateTime": "2024-03-15 14:30:45", "timeZone": "America/Sao_Paulo"})
        {"dateTime": "2024-03-15T17:30:45", "offset": "-03:00", "timeZone": "America/Sao_Paulo"}
    """
    dateTime = resource.get("dateTime")
    timeZone = resource.get("timeZone")

    if not dateTime or not isinstance(dateTime, str):
        raise DateTimeValidationError("dateTime must be a string")
    
    if not is_datetime_of_format(dateTime, "ISO_8601_UTC_Z") and not is_datetime_of_format(dateTime, "ISO_8601_UTC_OFFSET") and not is_datetime_of_format(dateTime, "ISO_8601_WITH_TIMEZONE"):
        raise DateTimeValidationError("Invalid dateTime")
    
    if timeZone and not is_timezone_valid(timeZone):
        raise DateTimeValidationError("Invalid timeZone")
        
    # Convert the datetime string to UTC timezone
    if is_datetime_of_format(dateTime, "ISO_8601_UTC_Z"):
        dateTime_obj = datetime.fromisoformat(dateTime).replace(tzinfo=timezone.utc)
        dateTime_UTC = dateTime_obj.strftime("%Y-%m-%dT%H:%M:%S")
        offset = "+00:00"
        return {"dateTime": dateTime_UTC, "offset": offset, "timeZone": timeZone}
    elif is_datetime_of_format(dateTime, "ISO_8601_UTC_OFFSET"):
        dateTime_obj = datetime.fromisoformat(dateTime).astimezone(timezone.utc)
        dateTime_UTC = dateTime_obj.strftime("%Y-%m-%dT%H:%M:%S")
        offset = dateTime[-6:]
        return {"dateTime": dateTime_UTC, "offset": offset, "timeZone": timeZone}
    elif is_datetime_of_format(dateTime, "ISO_8601_WITH_TIMEZONE"):
        if timeZone:
            dateTime_obj = datetime.fromisoformat(dateTime).replace(tzinfo=ZoneInfo(timeZone))
            offset = dateTime_obj.isoformat()[-6:]
            dateTime_UTC = dateTime_obj.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            return {"dateTime": dateTime_UTC, "offset": offset, "timeZone": timeZone}
        else:
            raise DateTimeValidationError("If timeZone is not provided, dateTime must have timezone information.")