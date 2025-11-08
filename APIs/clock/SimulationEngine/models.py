from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, Dict, Any
from enum import Enum
import re
from datetime import datetime

class DateRange(BaseModel):
    """Represents a date range. To represent a single date, make start_date and end_date the same."""
    start_date: Optional[str] = Field(None, description="In the format of YYYY-MM-DD. If using start_date, do not use a date in the past.")
    end_date: Optional[str] = Field(None, description="In the format of YYYY-MM-DD. If using end_date, do not use a date in the past.")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v):
        """Validate that the date is in YYYY-MM-DD format using centralized validation."""
        if v is not None:
            # Import here to avoid circular imports
            from common_utils.datetime_utils import validate_clock_date, InvalidDateTimeFormatError
            try:
                return validate_clock_date(v)
            except InvalidDateTimeFormatError as e:
                # Import here to avoid circular imports
                from clock.SimulationEngine.custom_errors import InvalidDateFormatError
                raise InvalidDateFormatError(v)
        return v

    class Config:
        strict = True


class AlarmFilters(BaseModel):
    """Filters to identify the alarms to be modified."""
    time: Optional[str] = Field(None, description="The time that the alarm will fire, in 12-hour format \"H[:M[:S]]\"")
    label: Optional[str] = Field(None, description="The label of the alarm to filter for")
    date_range: Optional[DateRange] = Field(None, description="Date range to filter alarms")
    alarm_type: Optional[str] = Field(None, description="One of UPCOMING, DISABLED, ACTIVE")
    alarm_ids: Optional[List[str]] = Field(None, description="Alarm ids to filter for")

    @field_validator("alarm_type")
    @classmethod
    def validate_alarm_type(cls, v):
        """Validate alarm type."""
        if v is not None and v not in ["UPCOMING", "DISABLED", "ACTIVE"]:
            raise ValueError("alarm_type must be one of UPCOMING, DISABLED, ACTIVE")
        return v

    class Config:
        strict = True


class AlarmModifications(BaseModel):
    """Modifications to make to the alarms based on the user's request."""
    time: Optional[str] = Field(None, description="New time that the alarm should fire at, in 12-hour format")
    duration_to_add: Optional[str] = Field(None, description="Duration to add to the alarm, e.g. 1h00m00s")
    date: Optional[str] = Field(None, description="Date that the alarm should be updated to, in YYYY-MM-DD format")
    label: Optional[str] = Field(None, description="Label that the alarm should be updated to")
    recurrence: Optional[List[str]] = Field(None, description="Recurrence that the alarm should be updated to")
    state_operation: Optional[str] = Field(None, description="State operation to perform")

    @field_validator("state_operation")
    @classmethod
    def validate_state_operation(cls, v):
        """Validate state operation."""
        if v is not None and v not in ["ENABLE", "DISABLE", "DELETE", "CANCEL", "DISMISS", "STOP", "PAUSE"]:
            raise ValueError("state_operation must be one of ENABLE, DISABLE, DELETE, CANCEL, DISMISS, STOP, PAUSE")
        return v

    @field_validator("recurrence")
    @classmethod
    def validate_recurrence(cls, v):
        """Validate recurrence days."""
        if v is not None:
            valid_days = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]
            for day in v:
                if day not in valid_days:
                    raise ValueError(f"Invalid recurrence day: {day}")
        return v

    class Config:
        strict = True


class TimerFilters(BaseModel):
    """Filters to identify the timers to be modified."""
    duration: Optional[str] = Field(None, description="Duration of the timer, e.g. 2h00m00s")
    label: Optional[str] = Field(None, description="Label of the timer")
    timer_type: Optional[str] = Field(None, description="One of UPCOMING, PAUSED, RUNNING")
    timer_ids: Optional[List[str]] = Field(None, description="Timer ids to filter for")

    @field_validator("timer_type")
    @classmethod
    def validate_timer_type(cls, v):
        """Validate timer type."""
        if v is not None and v not in ["UPCOMING", "PAUSED", "RUNNING"]:
            raise ValueError("timer_type must be one of UPCOMING, PAUSED, RUNNING")
        return v

    class Config:
        strict = True


class TimerModifications(BaseModel):
    """Modifications to make to the timers based on the user's request."""
    duration: Optional[str] = Field(None, description="Duration that the timer should be updated to")
    duration_to_add: Optional[str] = Field(None, description="Duration to add to the timer")
    label: Optional[str] = Field(None, description="Label that the timer should be updated to")
    state_operation: Optional[str] = Field(None, description="State operation to perform")

    @field_validator("state_operation")
    @classmethod
    def validate_state_operation(cls, v):
        """Validate state operation."""
        if v is not None and v not in ["PAUSE", "RESUME", "RESET", "DELETE", "CANCEL", "DISMISS", "STOP"]:
            raise ValueError("state_operation must be one of PAUSE, RESUME, RESET, DELETE, CANCEL, DISMISS, STOP")
        return v

    class Config:
        strict = True


class Alarm(BaseModel):
    """Represents an alarm."""
    time_of_day: Optional[str] = Field(None, description="Time of day the alarm fires")
    alarm_id: Optional[str] = Field(None, description="Unique identifier for the alarm")
    label: Optional[str] = Field(None, description="Label for the alarm")
    state: Optional[str] = Field(None, description="Current state of the alarm")
    date: Optional[str] = Field(None, description="Date the alarm is scheduled for")
    recurrence: Optional[str] = Field(None, description="Recurrence pattern for the alarm")
    fire_time: Optional[str] = Field(None, description="The ISO timestamp for when the alarm is set to fire")

    class Config:
        strict = True


class Timer(BaseModel):
    """Represents a timer."""
    original_duration: Optional[str] = Field(None, description="Original duration of the timer")
    remaining_duration: Optional[str] = Field(None, description="Remaining duration left on the timer")
    time_of_day: Optional[str] = Field(None, description="Time of day the timer will go off")
    timer_id: Optional[str] = Field(None, description="Unique identifier for the timer")
    label: Optional[str] = Field(None, description="Label for the timer")
    state: Optional[str] = Field(None, description="Current state of the timer")
    fire_time: Optional[str] = Field(None, description="The ISO timestamp for when the timer is set to fire")

    class Config:
        strict = True


class ClockResult(BaseModel):
    """The result of clock operations."""
    message: Optional[str] = Field(None, description="Response message")
    action_card_content_passthrough: Optional[str] = Field(None, description="Action card content")
    card_id: Optional[str] = Field(None, description="Card identifier")
    alarm: Optional[List[Alarm]] = Field(None, description="List of alarms")
    timer: Optional[List[Timer]] = Field(None, description="List of timers")

    class Config:
        strict = True


class AlarmCreationInput(BaseModel):
    """Input model for creating alarms."""
    duration: Optional[str] = Field(None, description="Duration of the alarm")
    time: Optional[str] = Field(None, description="Time of day the alarm should fire")
    date: Optional[str] = Field(None, description="Date the alarm is scheduled for")
    label: Optional[str] = Field(None, description="Label for the alarm")
    recurrence: Optional[List[str]] = Field(None, description="Recurrence pattern")

    @field_validator("recurrence")
    @classmethod
    def validate_recurrence(cls, v):
        """Validate recurrence days."""
        if v is not None:
            valid_days = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]
            for day in v:
                if day not in valid_days:
                    raise ValueError(f"Invalid recurrence day: {day}")
        return v

    class Config:
        strict = True


class TimerCreationInput(BaseModel):
    """Input model for creating timers."""
    duration: Optional[str] = Field(None, description="Duration of the timer")
    time: Optional[str] = Field(None, description="Time of day the timer should fire")
    label: Optional[str] = Field(None, description="Label for the timer")

    class Config:
        strict = True


# ========================================
# DATABASE VALIDATION MODELS (Phase 1)
# ========================================

class ClockAlarm(BaseModel):
    """Complete alarm database validation model."""
    alarm_id: str = Field(..., description="Unique identifier for the alarm")
    time_of_day: str = Field(..., description="Time of day when the alarm fires (e.g., '7:00 AM')")
    date: str = Field(..., description="Date the alarm is scheduled for (YYYY-MM-DD)")
    label: str = Field("", description="Label for the alarm")
    state: str = Field(..., description="Current state of the alarm")
    recurrence: str = Field("", description="Recurrence pattern (comma-separated days)")
    created_at: str = Field(..., description="ISO timestamp when alarm was created")
    fire_time: str = Field(..., description="ISO timestamp when alarm is set to fire")

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Validate alarm state."""
        valid_states = ["ACTIVE", "DISABLED", "SNOOZED", "CANCELLED", "FIRING"]
        if v not in valid_states:
            raise ValueError(f"state must be one of {valid_states}")
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v):
        """Validate date format."""
        try:
            from datetime import datetime
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")

    @field_validator("created_at", "fire_time")
    @classmethod
    def validate_iso_timestamp(cls, v):
        """Validate ISO timestamp format."""
        try:
            from datetime import datetime
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("timestamp must be in ISO format")

    class Config:
        strict = True


class ClockTimer(BaseModel):
    """Complete timer database validation model."""
    timer_id: str = Field(..., description="Unique identifier for the timer")
    original_duration: str = Field(..., description="Original duration of the timer")
    remaining_duration: str = Field(..., description="Remaining duration on the timer")
    time_of_day: str = Field(..., description="Time when timer will go off")
    label: str = Field("", description="Label for the timer")
    state: str = Field(..., description="Current state of the timer")
    created_at: str = Field(..., description="ISO timestamp when timer was created")
    fire_time: str = Field(..., description="ISO timestamp when timer will fire")
    start_time: str = Field(..., description="ISO timestamp when timer was started")

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Validate timer state."""
        valid_states = ["RUNNING", "PAUSED", "FINISHED", "RESET", "CANCELLED", "STOPPED"]
        if v not in valid_states:
            raise ValueError(f"state must be one of {valid_states}")
        return v

    @field_validator("original_duration", "remaining_duration")
    @classmethod
    def validate_duration_format(cls, v):
        """Validate duration format."""
        import re
        pattern = r'^(?:\d+h)?(?:\d+m)?(?:\d+s)?$'
        if not re.match(pattern, v) or v == '':
            raise ValueError("duration must be in format like '5h30m20s', '10m', or '45s'")
        return v

    @field_validator("created_at", "fire_time", "start_time")
    @classmethod
    def validate_iso_timestamp(cls, v):
        """Validate ISO timestamp format."""
        try:
            from datetime import datetime
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("timestamp must be in ISO format")

    class Config:
        strict = True


class LapTime(BaseModel):
    """Individual lap time entry for stopwatch."""
    lap_number: int = Field(..., description="Sequential lap number")
    lap_time: int = Field(..., description="Total elapsed time at this lap (seconds)")
    lap_duration: str = Field(..., description="Duration string for total time")
    split_time: int = Field(..., description="Time since previous lap (seconds)")
    split_duration: str = Field(..., description="Duration string for split time")
    timestamp: str = Field(..., description="ISO timestamp when lap was recorded")

    @field_validator("timestamp")
    @classmethod
    def validate_iso_timestamp(cls, v):
        """Validate ISO timestamp format."""
        try:
            from datetime import datetime
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("timestamp must be in ISO format")

    class Config:
        strict = True


class ClockStopwatch(BaseModel):
    """Complete stopwatch database validation model."""
    state: str = Field(..., description="Current state of the stopwatch")
    start_time: Optional[str] = Field(None, description="ISO timestamp when stopwatch was started")
    pause_time: Optional[str] = Field(None, description="ISO timestamp when stopwatch was paused")
    elapsed_time: int = Field(0, description="Elapsed time in seconds")
    lap_times: List[LapTime] = Field(default_factory=list, description="List of recorded lap times")

    @field_validator("state")
    @classmethod
    def validate_state(cls, v):
        """Validate stopwatch state."""
        valid_states = ["STOPPED", "RUNNING", "PAUSED"]
        if v not in valid_states:
            raise ValueError(f"state must be one of {valid_states}")
        return v

    @field_validator("start_time", "pause_time")
    @classmethod
    def validate_iso_timestamp(cls, v):
        """Validate ISO timestamp format."""
        if v is None:
            return v
        try:
            from datetime import datetime
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("timestamp must be in ISO format")

    @field_validator("elapsed_time")
    @classmethod
    def validate_elapsed_time(cls, v):
        """Validate elapsed time is non-negative."""
        if v < 0:
            raise ValueError("elapsed_time must be non-negative")
        return v

    class Config:
        strict = True


class ClockSettings(BaseModel):
    """Complete settings database validation model."""
    default_alarm_sound: str = Field(..., description="Default sound for alarms")
    default_timer_sound: str = Field(..., description="Default sound for timers")
    snooze_duration: int = Field(..., description="Default snooze duration in seconds")
    alarm_volume: float = Field(..., description="Alarm volume (0.0 to 1.0)")
    timer_volume: float = Field(..., description="Timer volume (0.0 to 1.0)")
    time_format: str = Field(..., description="Time format preference")
    show_seconds: Union[bool, str] = Field(..., description="Whether to show seconds in time display")

    @field_validator("snooze_duration")
    @classmethod
    def validate_snooze_duration(cls, v):
        """Validate snooze duration is positive."""
        if v <= 0:
            raise ValueError("snooze_duration must be positive")
        return v

    @field_validator("alarm_volume", "timer_volume")
    @classmethod
    def validate_volume(cls, v):
        """Validate volume is between 0.0 and 1.0."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("volume must be between 0.0 and 1.0")
        return v

    @field_validator("time_format")
    @classmethod
    def validate_time_format(cls, v):
        """Validate time format."""
        valid_formats = ["12_hour", "24_hour"]
        if v not in valid_formats:
            raise ValueError(f"time_format must be one of {valid_formats}")
        return v

    @field_validator("show_seconds")
    @classmethod
    def validate_show_seconds(cls, v):
        """Validate show_seconds is boolean or boolean string."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            if v.lower() in ['true', 'false']:
                return v.lower() == 'true'
            else:
                raise ValueError("show_seconds must be 'true', 'false', or boolean")
        raise ValueError("show_seconds must be boolean or boolean string")

    class Config:
        strict = True


class ClockDB(BaseModel):
    """Complete clock database validation model."""
    alarms: Dict[str, ClockAlarm] = Field(default_factory=dict, description="Dictionary of all alarms")
    timers: Dict[str, ClockTimer] = Field(default_factory=dict, description="Dictionary of all timers")
    stopwatch: ClockStopwatch = Field(..., description="Stopwatch state and data")
    settings: ClockSettings = Field(..., description="Clock application settings")

    @field_validator("alarms")
    @classmethod
    def validate_alarms(cls, v):
        """Validate alarms dictionary structure."""
        if not isinstance(v, dict):
            raise ValueError("alarms must be a dictionary")
        for alarm_id, alarm_data in v.items():
            if not isinstance(alarm_id, str):
                raise ValueError("alarm keys must be strings")
            if alarm_data.alarm_id != alarm_id:
                raise ValueError(f"alarm_id mismatch: key '{alarm_id}' vs data '{alarm_data.alarm_id}'")
        return v

    @field_validator("timers")
    @classmethod
    def validate_timers(cls, v):
        """Validate timers dictionary structure."""
        if not isinstance(v, dict):
            raise ValueError("timers must be a dictionary")
        for timer_id, timer_data in v.items():
            if not isinstance(timer_id, str):
                raise ValueError("timer keys must be strings")
            if timer_data.timer_id != timer_id:
                raise ValueError(f"timer_id mismatch: key '{timer_id}' vs data '{timer_data.timer_id}'")
        return v

    class Config:
        strict = True