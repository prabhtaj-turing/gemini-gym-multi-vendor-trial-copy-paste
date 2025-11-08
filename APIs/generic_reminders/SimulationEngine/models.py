"""
Pydantic models for the Generic Reminders service.

This module contains all the data validation models and schema definitions
used throughout the service.
"""

from typing import Dict, Optional, List, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
import re
from .custom_errors import ValidationError, InvalidDateTimeFormatError


class BaseReminderModel(BaseModel):
    """Base model with common validation logic."""

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"
        # Validate assignment to catch errors early
        validate_assignment = True

    @validator("*", pre=True)
    def handle_empty_strings(cls, v):
        """Convert empty strings to None for optional fields."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class CreateReminderInput(BaseReminderModel):
    """
    Pydantic model for validating create reminder input parameters.
    """

    title: str = Field(..., description="The title of the reminder. Required.")
    description: Optional[str] = Field(
        None, description="Additional description for the reminder"
    )
    start_date: Optional[str] = Field(
        None, description="Scheduled date in YYYY-MM-DD format"
    )
    time_of_day: Optional[str] = Field(
        None, description="Scheduled time in hh:mm:ss format"
    )
    am_pm_or_unknown: Optional[str] = Field(
        None, description="AM/PM indicator or UNKNOWN"
    )
    end_date: Optional[str] = Field(
        None, description="End date for recurring reminders"
    )
    repeat_every_n: Optional[int] = Field(0, description="Number of repeat intervals")
    repeat_interval_unit: Optional[str] = Field(
        None, description="Unit of repeat intervals. Accepts values in any case (e.g., 'minute', 'MINUTE', 'Minute')"
    )
    days_of_week: Optional[List[str]] = Field(
        None, description="Days of week for recurring reminders. Accepts values in any case (e.g., 'monday', 'MONDAY', 'Monday')"
    )
    weeks_of_month: Optional[List[str]] = Field(
        None, description="Weeks of month for recurring reminders. Accepts numeric strings '1'-'5' or word forms ('FIRST', 'SECOND', etc.)"
    )
    days_of_month: Optional[List[str]] = Field(
        None, description="Days of month for recurring reminders. Accepts both 'DAY_5' format and plain numbers like '5'"
    )
    occurrence_count: Optional[int] = Field(
        None, description="Number of times reminder should recur"
    )

    @validator("start_date", "end_date")
    def validate_date_format(cls, v):
        """Validate date format is YYYY-MM-DD using centralized validation."""
        if v is not None:
            # Import here to avoid circular imports
            from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
            try:
                return validate_date_only(v)
            except InvalidDateTimeFormatError as e:
                # Import here to avoid circular imports
                from generic_reminders.SimulationEngine.custom_errors import InvalidDateTimeFormatError as RemindersInvalidDateTimeFormatError
                raise RemindersInvalidDateTimeFormatError(str(e))
        return v

    @validator("time_of_day")
    def validate_time_format(cls, v):
        """Validate time format is hh:mm:ss."""
        if v is not None:
            if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$", v):
                raise ValueError("must be in hh:mm:ss format")
        return v

    @validator("am_pm_or_unknown")
    def validate_am_pm(cls, v):
        """Validate AM/PM indicator."""
        if v is not None:
            if v not in ["AM", "PM", "UNKNOWN"]:
                raise ValueError("must be AM, PM, or UNKNOWN")
        return v

    @validator("repeat_every_n")
    def validate_repeat_every_n(cls, v):
        """Validate repeat interval number."""
        if v is not None and v < 0:
            raise ValueError("must be non-negative")
        return v

    @validator("repeat_interval_unit")
    def validate_repeat_unit(cls, v):
        """Validate repeat interval unit. Accepts values in any case (e.g., 'minute', 'MINUTE', 'Minute')."""
        if v is not None:
            valid_units = ["MINUTE", "HOUR", "DAY", "WEEK", "MONTH", "YEAR"]
            v_upper = v.upper()
            if v_upper not in valid_units:
                raise ValueError("must be one of MINUTE, HOUR, DAY, WEEK, MONTH, YEAR")

        return v

    @validator("days_of_week")
    def validate_days_of_week(cls, v):
        """Validate days of week. Accepts values in any case (e.g., 'monday', 'MONDAY', 'Monday')."""
        if v is not None:
            valid_days = {
                "SUNDAY",
                "MONDAY",
                "TUESDAY",
                "WEDNESDAY",
                "THURSDAY",
                "FRIDAY",
                "SATURDAY",
            }
            for day in v:
                if day.upper() not in valid_days:
                    raise ValueError(f"Invalid day of week: {day}")
        return v

    @validator("weeks_of_month")
    def validate_weeks_of_month(cls, v):
        """Validate weeks of month. Accepts numeric strings '1'-'5' or word forms."""
        if v is not None:
            valid_weeks = ["FIRST", "SECOND", "THIRD", "FOURTH", "LAST"]
            numeric_to_word = {
                "1": "FIRST",
                "2": "SECOND", 
                "3": "THIRD",
                "4": "FOURTH",
                "5": "LAST"
            }
            for week in v:
                # Check if it's valid (numeric string or word form)
                if week not in numeric_to_word and week.upper() not in valid_weeks:
                    raise ValueError(f"Invalid week of month: {week}")
        return v

    @validator("days_of_month")
    def validate_days_of_month(cls, v):
        """Validate days of month. Accepts both 'DAY_5' format and plain numbers like '5'. Case-insensitive for DAY_X format."""
        if v is not None:
            valid_days = [f"DAY_{i}" for i in range(1, 32)] + ["LAST"]
            for day in v:
                # Check if it's valid in any accepted format
                is_valid = (
                    day in valid_days or  # Already in DAY_X or LAST format
                    day.upper() == "LAST" or  # LAST in any case
                    (day.isdigit() and 1 <= int(day) <= 31) or  # Plain number 1-31
                    (day.upper().startswith("DAY_") and len(day) > 4 and 
                     day.upper()[4:].isdigit() and 1 <= int(day.upper()[4:]) <= 31)  # DAY_X format
                )
                
                if not is_valid:
                    raise ValueError(f"Invalid day of month: {day}")
        return v

    @validator("occurrence_count")
    def validate_occurrence_count(cls, v):
        """Validate occurrence count."""
        if v is not None and v <= 0:
            raise ValueError("must be positive")
        return v

    @root_validator(skip_on_failure=True)
    def validate_data_consistency(cls, values):
        """Validate consistency between related fields."""
        start_date = values.get("start_date")
        end_date = values.get("end_date")
        repeat_every_n = values.get("repeat_every_n")
        repeat_interval_unit = values.get("repeat_interval_unit")
        occurrence_count = values.get("occurrence_count")

        # Check if recurring parameters are consistent
        if repeat_every_n is not None and repeat_every_n > 0:
            if not repeat_interval_unit:
                raise ValueError(
                    "repeat_interval_unit is required when repeat_every_n > 0"
                )

        # Check if end_date is after start_date
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if end_dt < start_dt:
                    raise ValueError("end_date must >= start_date")
            except ValueError as e:
                if "does not match format" in str(e):
                    raise ValueError("Invalid date format. Expected YYYY-MM-DD.")
                raise

        # Check if occurrence_count makes sense with repeat settings
        if occurrence_count is not None and occurrence_count > 0:
            if repeat_every_n is None or repeat_every_n == 0:
                raise ValueError("occurrence_count requires repeat_every_n > 0")

        return values


class ModifyReminderInput(BaseReminderModel):
    """
    Pydantic model for validating modify reminder input parameters.
    """

    # Reminder modification fields
    title: Optional[str] = Field(None, description="New title for the reminder")
    description: Optional[str] = Field(
        None, description="New description for the reminder"
    )
    start_date: Optional[str] = Field(
        None, description="New start date in YYYY-MM-DD format"
    )
    time_of_day: Optional[str] = Field(None, description="New time in hh:mm:ss format")
    am_pm_or_unknown: Optional[str] = Field(None, description="New AM/PM indicator")
    end_date: Optional[str] = Field(
        None, description="New end date for recurring reminders"
    )
    repeat_every_n: Optional[int] = Field(
        None, description="New repeat interval number"
    )
    repeat_interval_unit: Optional[str] = Field(
        None, description="New repeat interval unit. Accepts values in any case (e.g., 'minute', 'MINUTE', 'Minute')"
    )
    days_of_week: Optional[List[str]] = Field(
        None, description="New days of week for recurrence. Accepts values in any case (e.g., 'monday', 'MONDAY', 'Monday')"
    )
    weeks_of_month: Optional[List[str]] = Field(
        None, description="New weeks of month for recurrence. Accepts numeric strings '1'-'5' or word forms ('FIRST', 'SECOND', etc.)"
    )
    days_of_month: Optional[List[str]] = Field(
        None, description="New days of month for recurrence. Accepts both 'DAY_5' format and plain numbers like '5'"
    )
    occurrence_count: Optional[int] = Field(None, description="New occurrence count")
    completed: Optional[bool] = Field(None, description="Mark reminders as completed")
    deleted: Optional[bool] = Field(None, description="Mark reminders as deleted")

    # Search parameters
    reminder_ids: Optional[List[str]] = Field(
        None, description="Specific reminder IDs to modify"
    )
    retrieval_query: Optional[Dict[str, Any]] = Field(
        None, description="Query to find reminders to modify"
    )

    # Operation parameters
    is_bulk_mutation: bool = Field(True, description="Whether this is a bulk operation")

    # Validators for reminder modification fields
    @validator("start_date", "end_date")
    def validate_date_format(cls, v):
        """Validate date format is YYYY-MM-DD using centralized validation."""
        if v is not None:
            # Import here to avoid circular imports
            from common_utils.datetime_utils import validate_date_only, InvalidDateTimeFormatError
            try:
                return validate_date_only(v)
            except InvalidDateTimeFormatError as e:
                # Import here to avoid circular imports
                from generic_reminders.SimulationEngine.custom_errors import InvalidDateTimeFormatError as RemindersInvalidDateTimeFormatError
                raise RemindersInvalidDateTimeFormatError(str(e))
        return v

    @validator("time_of_day")
    def validate_time_format(cls, v):
        """Validate time format is hh:mm:ss."""
        if v is not None:
            if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$", v):
                raise ValueError("must be in hh:mm:ss format")
        return v

    @validator("am_pm_or_unknown")
    def validate_am_pm(cls, v):
        """Validate AM/PM indicator."""
        if v is not None:
            if v not in ["AM", "PM", "UNKNOWN"]:
                raise ValueError("must be AM, PM, or UNKNOWN")
        return v

    @validator("repeat_every_n")
    def validate_repeat_every_n(cls, v):
        """Validate repeat interval number."""
        if v is not None and v < 0:
            raise ValueError("must be non-negative")
        return v

    @validator("repeat_interval_unit")
    def validate_repeat_unit(cls, v):
        """Validate repeat interval unit. Accepts values in any case (e.g., 'minute', 'MINUTE', 'Minute')."""
        if v is not None:
            valid_units = ["MINUTE", "HOUR", "DAY", "WEEK", "MONTH", "YEAR"]
            v_upper = v.upper()
            if v_upper not in valid_units:
                raise ValueError("must be one of MINUTE, HOUR, DAY, WEEK, MONTH, YEAR")

        return v

    @validator("days_of_week")
    def validate_days_of_week(cls, v):
        """Validate days of week. Accepts values in any case (e.g., 'monday', 'MONDAY', 'Monday')."""
        if v is not None:
            valid_days = {
                "SUNDAY",
                "MONDAY",
                "TUESDAY",
                "WEDNESDAY",
                "THURSDAY",
                "FRIDAY",
                "SATURDAY",
            }
            for day in v:
                if day.upper() not in valid_days:
                    raise ValueError(f"Invalid day of week: {day}")
        return v

    @validator("weeks_of_month")
    def validate_weeks_of_month(cls, v):
        """Validate weeks of month. Accepts numeric strings '1'-'5' or word forms."""
        if v is not None:
            valid_weeks = ["FIRST", "SECOND", "THIRD", "FOURTH", "LAST"]
            numeric_to_word = {
                "1": "FIRST",
                "2": "SECOND", 
                "3": "THIRD",
                "4": "FOURTH",
                "5": "LAST"
            }
            for week in v:
                # Check if it's valid (numeric string or word form)
                if week not in numeric_to_word and week.upper() not in valid_weeks:
                    raise ValueError(f"Invalid week of month: {week}")
        return v

    @validator("days_of_month")
    def validate_days_of_month(cls, v):
        """Validate days of month. Accepts both 'DAY_5' format and plain numbers like '5'. Case-insensitive for DAY_X format."""
        if v is not None:
            valid_days = [f"DAY_{i}" for i in range(1, 32)] + ["LAST"]
            for day in v:
                # Check if it's valid in any accepted format
                is_valid = (
                    day in valid_days or  # Already in DAY_X or LAST format
                    day.upper() == "LAST" or  # LAST in any case
                    (day.isdigit() and 1 <= int(day) <= 31) or  # Plain number 1-31
                    (day.upper().startswith("DAY_") and len(day) > 4 and 
                     day.upper()[4:].isdigit() and 1 <= int(day.upper()[4:]) <= 31)  # DAY_X format
                )
                
                if not is_valid:
                    raise ValueError(f"Invalid day of month: {day}")
        return v

    @validator("occurrence_count")
    def validate_occurrence_count(cls, v):
        """Validate occurrence count."""
        if v is not None and v <= 0:
            raise ValueError("must be positive")
        return v

    @validator("reminder_ids")
    def validate_reminder_ids(cls, v):
        """Validate reminder IDs."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("must be a list")
            if len(v) == 0:
                raise ValueError("cannot be empty")
            if not all(isinstance(rid, str) for rid in v):
                raise ValueError("All reminder_ids must be strings")
            # Check for duplicate IDs
            if len(v) != len(set(v)):
                raise ValueError("reminder_ids must be unique - duplicate IDs found")
        return v

    @validator("retrieval_query")
    def validate_retrieval_query_dict(cls, v):
        """Validate retrieval query dictionary."""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("must be a dict")
            # Validate using RetrievalQuery model
            try:
                RetrievalQuery(**v)
            except Exception as e:
                raise ValueError(f"Invalid retrieval query: {str(e)}")
        return v

    @root_validator(skip_on_failure=True)
    def validate_search_parameters(cls, values):
        """Validate search parameters."""
        reminder_ids = values.get("reminder_ids")
        retrieval_query = values.get("retrieval_query")

        if reminder_ids is not None and retrieval_query is not None:
            raise ValueError("Provide either reminder_ids or retrieval_query, not both")

        if reminder_ids is None and retrieval_query is None:
            raise ValueError("Must provide either reminder_ids or retrieval_query")

        return values


class RetrievalQuery(BaseReminderModel):
    """
    Pydantic model for retrieval query parameters to search for reminders.
    """

    query: Optional[str] = Field(None, description="Keyword search query")
    from_date: Optional[str] = Field(
        None, description="Start date in YYYY-MM-DD format"
    )
    from_time_of_day: Optional[str] = Field(
        None, description="Start time in hh:mm:ss format"
    )
    to_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    to_time_of_day: Optional[str] = Field(
        None, description="End time in hh:mm:ss format"
    )
    include_completed: Optional[bool] = Field(
        False, description="Include completed reminders"
    )
    is_recurring: Optional[bool] = Field(
        False, description="Filter for recurring reminders only"
    )
    include_deleted: Optional[bool] = Field(
        False, description="Include deleted reminders"
    )

    @validator("from_date", "to_date")
    def validate_date_format(cls, v):
        """Validate date format is YYYY-MM-DD."""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @validator("from_time_of_day", "to_time_of_day")
    def validate_time_format(cls, v):
        """Validate time format is hh:mm:ss."""
        if v is not None:
            if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$", v):
                raise ValueError("Time must be in hh:mm:ss format")
        return v


class ReminderModel(BaseReminderModel):
    """
    Pydantic model for a complete reminder object.
    """

    id: str = Field(..., description="Unique reminder identifier")
    title: Optional[str] = Field(None, description="Reminder title")
    description: Optional[str] = Field(None, description="Reminder description")
    start_date: Optional[str] = Field(
        None, description="Scheduled date in YYYY-MM-DD format"
    )
    time_of_day: Optional[str] = Field(
        None, description="Scheduled time in hh:mm:ss format"
    )
    am_pm_or_unknown: Optional[str] = Field(None, description="AM/PM indicator")
    end_date: Optional[str] = Field(
        None, description="End date for recurring reminders"
    )
    repeat_every_n: int = Field(0, description="Repeat interval number")
    repeat_interval_unit: Optional[str] = Field(
        None, description="Repeat interval unit"
    )
    days_of_week: Optional[List[str]] = Field(
        None, description="Days of week for recurrence"
    )
    weeks_of_month: Optional[List[str]] = Field(
        None, description="Weeks of month for recurrence"
    )
    days_of_month: Optional[List[str]] = Field(
        None, description="Days of month for recurrence"
    )
    occurrence_count: Optional[int] = Field(None, description="Number of occurrences")
    completed: bool = Field(False, description="Whether reminder is completed")
    deleted: bool = Field(False, description="Whether reminder is deleted")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    schedule: str = Field(..., description="Human-readable schedule string")
    uri: str = Field(..., description="Reminder URI")


class OperationModel(BaseReminderModel):
    """
    Pydantic model for operation tracking objects.
    """

    id: str = Field(..., description="Unique operation identifier")
    operation_type: str = Field(..., description="Type of operation (create, modify, delete)")
    reminder_id: str = Field(..., description="ID of the affected reminder")
    original_data: Optional[Dict[str, Any]] = Field(None, description="Original reminder data (for modify operations)")
    timestamp: str = Field(..., description="Operation timestamp")


class CountersModel(BaseReminderModel):
    """
    Pydantic model for database counters.
    """

    reminder: int = Field(0, description="Reminder ID counter")
    operation: int = Field(0, description="Operation ID counter")


class GenericRemindersDB(BaseReminderModel):
    """
    Pydantic model for the complete Generic Reminders database structure.
    """

    reminders: Dict[str, ReminderModel] = Field(default_factory=dict, description="Dictionary of reminder objects keyed by ID")
    operations: Dict[str, OperationModel] = Field(default_factory=dict, description="Dictionary of operation objects keyed by ID")
    counters: CountersModel = Field(default_factory=CountersModel, description="ID counters for generating unique IDs")


# Backward compatibility wrapper functions
def validate_create_reminder_input(
    title: str,
    description: Optional[str] = None,
    start_date: Optional[str] = None,
    time_of_day: Optional[str] = None,
    am_pm_or_unknown: Optional[str] = None,
    end_date: Optional[str] = None,
    repeat_every_n: Optional[int] = 0,
    repeat_interval_unit: Optional[str] = None,
    days_of_week: Optional[List[str]] = None,
    weeks_of_month: Optional[List[str]] = None,
    days_of_month: Optional[List[str]] = None,
    occurrence_count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validate input parameters for creating a reminder.

    This is a backward compatibility wrapper around the CreateReminderInput Pydantic model.

    Returns:
        Dict[str, Any]: Validated input data.

    Raises:
        ValidationError: If any validation fails.
    """
    try:
        # Create the Pydantic model instance
        model = CreateReminderInput(
            title=title,
            description=description,
            start_date=start_date,
            time_of_day=time_of_day,
            am_pm_or_unknown=am_pm_or_unknown,
            end_date=end_date,
            repeat_every_n=repeat_every_n,
            repeat_interval_unit=repeat_interval_unit,
            days_of_week=days_of_week,
            weeks_of_month=weeks_of_month,
            days_of_month=days_of_month,
            occurrence_count=occurrence_count,
        )
        # Return dict with all fields to maintain backward compatibility
        return model.dict()
    except Exception as e:
        # Convert Pydantic validation errors to our custom ValidationError
        error_message = str(e)
        # Handle specific field validation errors
        if "validation error" in error_message.lower():
            # Handle centralized datetime validation errors
            if (
                "start_date" in error_message
                and "Invalid date format" in error_message
                and "Expected YYYY-MM-DD format" in error_message
            ):
                raise InvalidDateTimeFormatError("Input validation failed: start_date must be in YYYY-MM-DD format")
            elif (
                "end_date" in error_message
                and "Invalid date format" in error_message
                and "Expected YYYY-MM-DD format" in error_message
            ):
                raise InvalidDateTimeFormatError("Input validation failed: end_date must be in YYYY-MM-DD format")
            # Handle other specific field validation errors
            elif (
                "time_of_day" in error_message
                and "must be in hh:mm:ss format" in error_message
            ):
                raise ValidationError("time_of_day must be in hh:mm:ss format")
            elif (
                "am_pm_or_unknown" in error_message
                and "must be AM, PM, or UNKNOWN" in error_message
            ):
                raise ValidationError("am_pm_or_unknown must be AM, PM, or UNKNOWN")
            elif (
                "repeat_every_n" in error_message
                and "must be non-negative" in error_message
            ):
                raise ValidationError("repeat_every_n must be non-negative")
            elif (
                "repeat_interval_unit" in error_message
                and "must be one of" in error_message
            ):
                raise ValidationError(
                    "repeat_interval_unit must be one of MINUTE, HOUR, DAY, WEEK, MONTH, YEAR"
                )
            elif (
                "occurrence_count" in error_message
                and "must be positive" in error_message
            ):
                raise ValidationError("occurrence_count must be positive")
            elif "end_date must >= start_date" in error_message:
                raise ValidationError("end_date must >= start_date")
            elif (
                "repeat_interval_unit is required when repeat_every_n > 0"
                in error_message
            ):
                raise ValidationError(
                    "repeat_interval_unit is required when repeat_every_n > 0"
                )
            elif "occurrence_count requires repeat_every_n > 0" in error_message:
                raise ValidationError("occurrence_count requires repeat_every_n > 0")
            elif "Invalid day of week:" in error_message:
                # Extract the specific error message
                if "Invalid day of week:" in error_message:
                    import re

                    match = re.search(r"Invalid day of week: (\w+)", error_message)
                    if match:
                        raise ValidationError(f"Invalid day of week: {match.group(1)}")
                raise ValidationError(error_message)
            elif "Invalid week of month:" in error_message:
                raise ValidationError(error_message)
            elif "Invalid day of month:" in error_message:
                raise ValidationError(error_message)

        raise ValidationError(error_message)


def validate_modify_reminder_input(
    title: Optional[str] = None,
    description: Optional[str] = None,
    start_date: Optional[str] = None,
    time_of_day: Optional[str] = None,
    am_pm_or_unknown: Optional[str] = None,
    end_date: Optional[str] = None,
    repeat_every_n: Optional[int] = None,
    repeat_interval_unit: Optional[str] = None,
    days_of_week: Optional[List[str]] = None,
    weeks_of_month: Optional[List[str]] = None,
    days_of_month: Optional[List[str]] = None,
    occurrence_count: Optional[int] = None,
    completed: Optional[bool] = None,
    deleted: Optional[bool] = None,
    reminder_ids: Optional[List[str]] = None,
    retrieval_query: Optional[Dict[str, Any]] = None,
    is_bulk_mutation: bool = False,
) -> Dict[str, Any]:
    """
    Validate input parameters for modifying reminders.

    This is a backward compatibility wrapper around the ModifyReminderInput Pydantic model.

    Returns:
        Dict[str, Any]: Validated input data with only non-None values.

    Raises:
        ValidationError: If any validation fails.
    """
    try:
        # Create the Pydantic model instance
        model = ModifyReminderInput(
            title=title,
            description=description,
            start_date=start_date,
            time_of_day=time_of_day,
            am_pm_or_unknown=am_pm_or_unknown,
            end_date=end_date,
            repeat_every_n=repeat_every_n,
            repeat_interval_unit=repeat_interval_unit,
            days_of_week=days_of_week,
            weeks_of_month=weeks_of_month,
            days_of_month=days_of_month,
            occurrence_count=occurrence_count,
            completed=completed,
            deleted=deleted,
            reminder_ids=reminder_ids,
            retrieval_query=retrieval_query,
            is_bulk_mutation=is_bulk_mutation,
        )
        # Return dict with all fields to maintain backward compatibility
        return model.dict()
    except Exception as e:
        # Convert Pydantic validation errors to our custom ValidationError
        error_message = str(e)
        # Handle specific validation errors with backward compatible messages
        if "Provide either reminder_ids or retrieval_query, not both" in error_message:
            raise ValidationError(
                "Provide either reminder_ids or retrieval_query, not both"
            )
        elif "Must provide either reminder_ids or retrieval_query" in error_message:
            raise ValidationError("Must provide either reminder_ids or retrieval_query")
        elif "reminder_ids" in error_message and "cannot be empty" in error_message:
            raise ValidationError("reminder_ids cannot be empty")
        elif "reminder_ids" in error_message and (
            "must be strings" in error_message
            or "All reminder_ids must be strings" in error_message
        ):
            raise ValidationError("All reminder_ids must be strings")
        elif "reminder_ids must be unique" in error_message:
            raise ValidationError("reminder_ids must be unique - duplicate IDs found")
        elif "retrieval_query" in error_message and (
            "must be a dict" in error_message or "must be a dictionary" in error_message
        ):
            raise ValidationError("retrieval_query must be a dict")
        elif "Invalid retrieval query:" in error_message:
            raise ValidationError(error_message)

        # Handle Pydantic validation errors - look for specific field errors
        if "validation error" in error_message.lower():
            # Check for reminder_ids type error
            if "reminder_ids" in error_message:
                if "int" in error_message and "str" in error_message:
                    raise ValidationError("All reminder_ids must be strings")
                elif "list" in error_message:
                    raise ValidationError("reminder_ids must be a list")
                elif "empty" in error_message:
                    raise ValidationError("reminder_ids cannot be empty")
                elif "unique" in error_message:
                    raise ValidationError("reminder_ids must be unique - duplicate IDs found")
            # Check for retrieval_query type error
            elif "retrieval_query" in error_message:
                if "dict" in error_message or "str" in error_message:
                    raise ValidationError("retrieval_query must be a dict")

        # Handle common field validation errors
        if "validation error" in error_message.lower():
            # Handle centralized datetime validation errors
            if (
                "start_date" in error_message
                and "Invalid date format" in error_message
                and "Expected YYYY-MM-DD format" in error_message
            ):
                raise InvalidDateTimeFormatError("Input validation failed: start_date must be in YYYY-MM-DD format")
            elif (
                "end_date" in error_message
                and "Invalid date format" in error_message
                and "Expected YYYY-MM-DD format" in error_message
            ):
                raise InvalidDateTimeFormatError("Input validation failed: end_date must be in YYYY-MM-DD format")
            # Handle other specific field validation errors
            elif (
                "time_of_day" in error_message
                and "must be in hh:mm:ss format" in error_message
            ):
                raise ValidationError("time_of_day must be in hh:mm:ss format")
            elif (
                "am_pm_or_unknown" in error_message
                and "must be AM, PM, or UNKNOWN" in error_message
            ):
                raise ValidationError("am_pm_or_unknown must be AM, PM, or UNKNOWN")
            elif (
                "repeat_every_n" in error_message
                and "must be non-negative" in error_message
            ):
                raise ValidationError("repeat_every_n must be non-negative")
            elif (
                "repeat_interval_unit" in error_message
                and "must be one of" in error_message
            ):
                raise ValidationError(
                    "repeat_interval_unit must be one of MINUTE, HOUR, DAY, WEEK, MONTH, YEAR"
                )
            elif (
                "occurrence_count" in error_message
                and "must be positive" in error_message
            ):
                raise ValidationError("occurrence_count must be positive")
            elif "completed" in error_message and "boolean" in error_message:
                raise ValidationError("completed must be a boolean")
            elif "deleted" in error_message and "boolean" in error_message:
                raise ValidationError("deleted must be a boolean")
            elif "is_bulk_mutation" in error_message and "boolean" in error_message:
                raise ValidationError("is_bulk_mutation must be a boolean")
            elif "reminder_ids" in error_message and "must be a list" in error_message:
                raise ValidationError("reminder_ids must be a list")
            elif "reminder_ids" in error_message and "must be strings" in error_message:
                raise ValidationError("All reminder_ids must be strings")
            elif (
                "retrieval_query" in error_message and "must be a dict" in error_message
            ):
                raise ValidationError("retrieval_query must be a dict")

        raise ValidationError(error_message)


def validate_retrieval_query(query_data: Dict[str, Any]) -> RetrievalQuery:
    """
    Validate a retrieval query dictionary.

    This function maintains backward compatibility while using the new Pydantic model.

    Args:
        query_data (Dict[str, Any]): Raw query data

    Returns:
        RetrievalQuery: Validated query object

    Raises:
        ValidationError: If validation fails
    """
    try:
        return RetrievalQuery(**query_data)
    except Exception as e:
        raise ValidationError(f"Invalid retrieval query: {str(e)}")


# Legacy validation functions (kept for backward compatibility)
def validate_type(value: Any, expected_type: type, param_name: str) -> None:
    """
    Validate that a value is of the expected type.

    Args:
        value: The value to validate
        expected_type: The expected type
        param_name: Name of the parameter for error messages

    Raises:
        ValidationError: If the type is incorrect
    """
    if not isinstance(value, expected_type):
        type_name = (
            "string" if expected_type.__name__ == "str" else expected_type.__name__
        )
        raise ValidationError(f"{param_name} must be a {type_name}")


def validate_optional_type(value: Any, expected_type: type, param_name: str) -> None:
    """
    Validate that an optional value is of the expected type if not None.

    Args:
        value: The value to validate
        expected_type: The expected type
        param_name: Name of the parameter for error messages

    Raises:
        ValidationError: If the type is incorrect
    """
    if value is not None:
        validate_type(value, expected_type, param_name)


def validate_date_format(date_str: str, param_name: str) -> None:
    """
    Validate date format is YYYY-MM-DD.

    Args:
        date_str: Date string to validate
        param_name: Name of the parameter for error messages

    Raises:
        ValidationError: If date format is invalid
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"{param_name} must be in YYYY-MM-DD format")


def validate_time_format(time_str: str, param_name: str) -> None:
    """
    Validate time format is hh:mm:ss.

    Args:
        time_str: Time string to validate
        param_name: Name of the parameter for error messages

    Raises:
        ValidationError: If time format is invalid
    """
    try:
        datetime.strptime(time_str, "%H:%M:%S")
    except ValueError:
        raise ValidationError(f"{param_name} must be in hh:mm:ss format")


def validate_optional_date(date_str: Optional[str], param_name: str) -> None:
    """
    Validate optional date format is YYYY-MM-DD.

    Args:
        date_str: Date string to validate (can be None)
        param_name: Name of the parameter for error messages

    Raises:
        ValidationError: If date format is invalid
    """
    if date_str is not None:
        validate_type(date_str, str, param_name)
        validate_date_format(date_str, param_name)


def validate_optional_time(time_str: Optional[str], param_name: str) -> None:
    """
    Validate optional time format is hh:mm:ss.

    Args:
        time_str: Time string to validate (can be None)
        param_name: Name of the parameter for error messages

    Raises:
        ValidationError: If time format is invalid
    """
    if time_str is not None:
        validate_type(time_str, str, param_name)
        validate_time_format(time_str, param_name)


def validate_date_range(from_date: Optional[str], to_date: Optional[str]) -> None:
    """
    Validate that from_date is not after to_date.

    Args:
        from_date: Start date
        to_date: End date

    Raises:
        ValidationError: If date range is invalid
    """
    if from_date is not None and to_date is not None:
        if from_date > to_date:
            raise ValidationError("from_date cannot be after to_date")


def validate_time_range(from_time: Optional[str], to_time: Optional[str]) -> None:
    """
    Validate that from_time is not after to_time.

    Args:
        from_time: Start time
        to_time: End time

    Raises:
        ValidationError: If time range is invalid
    """
    if from_time is not None and to_time is not None:
        if from_time > to_time:
            raise ValidationError("from_time_of_day cannot be after to_time_of_day")


def validate_string_list(
    value: List[str], param_name: str, allow_empty: bool = False
) -> None:
    """
    Validate that a value is a list of strings.

    Args:
        value: The value to validate
        param_name: Name of the parameter for error messages
        allow_empty: Whether to allow empty lists

    Raises:
        ValidationError: If validation fails
    """
    validate_type(value, list, param_name)

    if not allow_empty and not value:
        raise ValidationError(f"{param_name} cannot be empty")

    if not all(isinstance(item, str) for item in value):
        raise ValidationError(f"All {param_name} must be strings")
