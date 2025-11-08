"""
Generic Reminders SimulationEngine

This module contains the simulation engine components for the Generic Reminders service,
including error simulation, database interface, models, and utilities.
"""

from .db import DB, save_state, load_state, reset_db
from .models import (
    # Pydantic models
    BaseReminderModel,
    CreateReminderInput,
    ModifyReminderInput,
    RetrievalQuery,
    ReminderModel,
    OperationModel,
    CountersModel,
    GenericRemindersDB,
    # Backward compatibility functions
    validate_create_reminder_input,
    validate_modify_reminder_input,
    validate_retrieval_query,
    # Legacy validation functions
    validate_type,
    validate_optional_type,
    validate_date_format,
    validate_time_format,
    validate_optional_date,
    validate_optional_time,
    validate_date_range,
    validate_time_range,
    validate_string_list,
)
from .utils import (
    save_reminder_to_db,
    search_reminders,
    get_reminder_by_id,
    get_reminders_by_ids,
    track_operation,
    undo_operation,
    is_future_datetime,
    is_boring_title,
    format_schedule_string,
)
from .custom_errors import (
    ValidationError,
    ReminderNotFoundError,
    InvalidTimeError,
    OperationNotFoundError,
)
from common_utils.ErrorSimulation import ErrorSimulator
from common_utils.error_handling import handle_api_errors, get_package_error_mode
from common_utils.log_complexity import log_complexity

__all__ = [
    # Database
    "DB",
    "save_state",
    "load_state",
    "reset_db",
    # Pydantic models
    "BaseReminderModel",
    "CreateReminderInput",
    "ModifyReminderInput",
    "RetrievalQuery",
    "ReminderModel",
    "OperationModel",
    "CountersModel",
    "GenericRemindersDB",
    # Backward compatibility validation functions
    "validate_create_reminder_input",
    "validate_modify_reminder_input",
    "validate_retrieval_query",
    # Legacy validation functions
    "validate_type",
    "validate_optional_type",
    "validate_date_format",
    "validate_time_format",
    "validate_optional_date",
    "validate_optional_time",
    "validate_date_range",
    "validate_time_range",
    "validate_string_list",
    # Utilities
    "save_reminder_to_db",
    "search_reminders",
    "get_reminder_by_id",
    "get_reminders_by_ids",
    "track_operation",
    "undo_operation",
    "is_future_datetime",
    "is_boring_title",
    "format_schedule_string",
    # Errors
    "ValidationError",
    "ReminderNotFoundError",
    "InvalidTimeError",
    "OperationNotFoundError",
    # Error simulation
    "ErrorSimulator",
    "handle_api_errors",
    "get_package_error_mode",
    "log_complexity",
]
from . import utils
