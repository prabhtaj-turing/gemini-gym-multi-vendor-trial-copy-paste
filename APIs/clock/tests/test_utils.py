"""
Utility function tests for the Clock service.

This module tests all utility functions in the Clock service's utils module.
These are shared helper functions that provide core functionality for
time parsing, validation, filtering, and data manipulation.

Test Categories:
- Time parsing and formatting tests
- Duration parsing and conversion tests
- Validation function tests
- Filter and search function tests
- ID generation tests
- Date and time calculation tests
"""


import pytest
from clock.SimulationEngine.db import DB
from clock.SimulationEngine.utils import (
    _set_stopwatch_elapsed_time,
    _parse_duration,
    _seconds_to_duration
)


import unittest
from datetime import datetime, timedelta, time as dt_time
from unittest.mock import patch, MagicMock

try:
    from common_utils.base_case import BaseTestCaseWithErrorHandler
except ImportError:
    from common_utils.base_case import BaseTestCaseWithErrorHandler

from clock.SimulationEngine import utils
from clock.SimulationEngine.db import DB, reset_db


class TestClockUtils(BaseTestCaseWithErrorHandler):
    """Test Clock service utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        reset_db()
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()
        reset_db()

    # ========================================
    # Duration Parsing Tests
    # ========================================

    def test_parse_duration_valid_formats(self):
        """Test parsing valid duration formats."""
        test_cases = [
            ("5h", 18000),      # 5 hours = 18000 seconds
            ("30m", 1800),      # 30 minutes = 1800 seconds  
            ("45s", 45),        # 45 seconds = 45 seconds
            ("2h30m", 9000),    # 2h30m = 9000 seconds
            ("1h15m30s", 4530), # 1h15m30s = 4530 seconds
            ("10m20s", 620),    # 10m20s = 620 seconds
            ("3h45s", 10845),   # 3h45s = 10845 seconds
        ]
        
        for duration_str, expected_seconds in test_cases:
            with self.subTest(duration=duration_str):
                result = utils._parse_duration(duration_str)
                self.assertEqual(result, expected_seconds)

    def test_parse_duration_invalid_formats(self):
        """Test parsing invalid duration formats."""
        invalid_durations = [
            "invalid",    # No numbers
            "5x",         # Invalid unit
            "5h5h",       # Duplicate units
            "-5m",        # Negative duration
            "5.5h",       # Decimal numbers
        ]
        
        for invalid_duration in invalid_durations:
            with self.subTest(duration=invalid_duration):
                with self.assertRaises(ValueError):
                    utils._parse_duration(invalid_duration)
    
    def test_parse_duration_empty_string(self):
        """Test parsing empty duration string returns 0."""
        # Empty string returns 0 (handled specially)
        result = utils._parse_duration("")
        self.assertEqual(result, 0)

    def test_parse_duration_zero_duration(self):
        """Test that zero duration raises ValueError."""
        with self.assertRaises(ValueError):
            utils._parse_duration("0s")
        
        with self.assertRaises(ValueError):
            utils._parse_duration("0h0m0s")

    def test_seconds_to_duration_conversion(self):
        """Test converting seconds back to duration string."""
        test_cases = [
            (3600, "1h"),        # 1 hour
            (1800, "30m"),       # 30 minutes
            (45, "45s"),         # 45 seconds
            (3661, "1h1m1s"),    # 1h1m1s
            (7200, "2h"),        # 2 hours
            (0, "0s"),           # Zero seconds
        ]
        
        for seconds, expected_duration in test_cases:
            with self.subTest(seconds=seconds):
                result = utils._seconds_to_duration(seconds)
                self.assertEqual(result, expected_duration)

    # ========================================
    # Time Parsing Tests
    # ========================================

    def test_parse_time_24_hour_format(self):
        """Test parsing 24-hour time formats."""
        test_cases = [
            ("14:30", (14, 30, 0)),
            ("09:15:30", (9, 15, 30)),
            ("23:59:59", (23, 59, 59)),
            ("00:00:00", (0, 0, 0)),
            ("12:00", (12, 0, 0)),
        ]
        
        for time_str, expected in test_cases:
            with self.subTest(time=time_str):
                result = utils._parse_time(time_str)
                self.assertEqual(result, expected)

    def test_parse_time_12_hour_format(self):
        """Test parsing 12-hour time formats with AM/PM."""
        test_cases = [
            ("7:30 AM", (7, 30, 0)),
            ("7:30 PM", (19, 30, 0)),
            ("12:00 AM", (0, 0, 0)),    # Midnight
            ("12:00 PM", (12, 0, 0)),   # Noon
            ("11:59 PM", (23, 59, 0)),
            ("6:00AM", (6, 0, 0)),      # No space
            ("8:30pm", (20, 30, 0)),    # Lowercase
        ]
        
        for time_str, expected in test_cases:
            with self.subTest(time=time_str):
                result = utils._parse_time(time_str)
                self.assertEqual(result, expected)

    def test_parse_time_invalid_formats(self):
        """Test parsing invalid time formats."""
        invalid_times = [
            "",           # Empty string
            "25:00",      # Invalid hour
            "12:60",      # Invalid minute
            "12:30:60",   # Invalid second
            "12:30 XM",   # Invalid AM/PM
            "not a time", # Not a time
            "12",         # Missing minutes
            "12:30:45:10", # Too many components
        ]
        
        for invalid_time in invalid_times:
            with self.subTest(time=invalid_time):
                with self.assertRaises(ValueError):
                    utils._parse_time(invalid_time)

    def test_format_time_12_hour(self):
        """Test formatting time in 12-hour format."""
        test_cases = [
            ((7, 30, 0), "7:30 AM"),
            ((19, 30, 0), "7:30 PM"),
            ((0, 0, 0), "12:00 AM"),     # Midnight
            ((12, 0, 0), "12:00 PM"),    # Noon
            ((14, 15, 30), "2:15:30 PM"), # With seconds
        ]
        
        for (hour, minute, second), expected in test_cases:
            with self.subTest(time=(hour, minute, second)):
                result = utils._format_time(hour, minute, second, use_12_hour=True)
                self.assertEqual(result, expected)

    def test_format_time_24_hour(self):
        """Test formatting time in 24-hour format."""
        test_cases = [
            ((7, 30, 0), "07:30"),
            ((19, 30, 0), "19:30"),
            ((0, 0, 0), "00:00"),
            ((14, 15, 30), "14:15:30"), # With seconds
        ]
        
        for (hour, minute, second), expected in test_cases:
            with self.subTest(time=(hour, minute, second)):
                result = utils._format_time(hour, minute, second, use_12_hour=False)
                self.assertEqual(result, expected)

    # ========================================
    # Validation Function Tests
    # ========================================

    def test_check_required_fields(self):
        """Test checking for required fields in payload."""
        payload = {"field1": "value1", "field2": "value2"}
        
        # All required fields present
        result = utils._check_required_fields(payload, ["field1", "field2"])
        self.assertIsNone(result)
        
        # Missing required fields
        result = utils._check_required_fields(payload, ["field1", "field3"])
        self.assertIsNotNone(result)
        self.assertIn("field3", result)

    def test_check_required_fields_with_non_dict(self):
        """Test _check_required_fields with non-dict payload."""
        # Should handle gracefully
        result = utils._check_required_fields("not a dict", ["field"])
        self.assertIsNotNone(result)  # Should return an error message

    def test_check_empty_field(self):
        """Test checking for empty field values."""
        test_cases = [
            ("field", None, "field"),      # None value
            ("field", "", "field"),        # Empty string
            ("field", [], "field"),        # Empty list
            ("field", {}, "field"),        # Empty dict
            ("field", set(), "field"),     # Empty set
            ("field", "value", ""),        # Non-empty value
            ("field", [1, 2], ""),         # Non-empty list
        ]
        
        for field_name, value, expected in test_cases:
            with self.subTest(field=field_name, value=value):
                result = utils._check_empty_field(field_name, value)
                self.assertEqual(result, expected)

    def test_validate_recurrence(self):
        """Test recurrence validation."""
        # Valid recurrence patterns
        valid_patterns = [
            ["MONDAY"],
            ["MONDAY", "WEDNESDAY", "FRIDAY"],
            ["SUNDAY", "SATURDAY"],
            [],  # Empty list is valid
        ]
        
        for pattern in valid_patterns:
            with self.subTest(pattern=pattern):
                result = utils._validate_recurrence(pattern)
                self.assertTrue(result)
        
        # Invalid recurrence patterns
        invalid_patterns = [
            ["INVALID_DAY"],
            ["MONDAY", "INVALID"],
            ["monday"],  # Lowercase not allowed
        ]
        
        for pattern in invalid_patterns:
            with self.subTest(pattern=pattern):
                result = utils._validate_recurrence(pattern)
                self.assertFalse(result)

    # ========================================
    # ID Generation Tests
    # ========================================

    def test_generate_id(self):
        """Test simple ID generation."""
        existing = {"ALARM-1": {}, "ALARM-2": {}}
        
        new_id = utils._generate_id("ALARM", existing)
        self.assertEqual(new_id, "ALARM-3")
        
        # Test with empty dictionary
        new_id = utils._generate_id("TIMER", {})
        self.assertEqual(new_id, "TIMER-1")

    def test_generate_unique_id(self):
        """Test unique ID generation with UUID."""
        id1 = utils._generate_unique_id("TEST")
        id2 = utils._generate_unique_id("TEST")
        
        # Should be different
        self.assertNotEqual(id1, id2)
        
        # Should start with prefix
        self.assertTrue(id1.startswith("TEST-"))
        self.assertTrue(id2.startswith("TEST-"))

    # ========================================
    # Time Calculation Tests
    # ========================================

    @patch('clock.SimulationEngine.utils.datetime')
    def test_calculate_alarm_time_with_duration(self, mock_datetime):
        """Test calculating alarm time from duration."""
        # Mock current time
        mock_now = datetime(2024, 1, 15, 14, 30, 0)
        mock_datetime.now.return_value = mock_now
        
        # Test with duration
        result = utils._calculate_alarm_time(duration="30m")
        expected = mock_now + timedelta(seconds=1800)  # 30 minutes
        self.assertEqual(result, expected)

    @patch('clock.SimulationEngine.utils.datetime')
    def test_calculate_alarm_time_with_time(self, mock_datetime):
        """Test calculating alarm time from specific time."""
        # Mock current time (2:30 PM)
        mock_now = datetime(2024, 1, 15, 14, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.combine.side_effect = datetime.combine
        mock_datetime.strptime.side_effect = datetime.strptime
        
        # Test with time later today
        result = utils._calculate_alarm_time(time="16:00")  # 4:00 PM
        expected = datetime(2024, 1, 15, 16, 0, 0)
        self.assertEqual(result, expected)

    @patch('clock.SimulationEngine.utils.datetime')
    def test_calculate_timer_time(self, mock_datetime):
        """Test calculating timer fire time and duration."""
        # Mock current time
        mock_now = datetime(2024, 1, 15, 14, 30, 0)
        mock_datetime.now.return_value = mock_now
        
        # Test with duration
        fire_time, duration = utils._calculate_timer_time(duration="15m")
        expected_fire_time = mock_now + timedelta(seconds=900)  # 15 minutes
        self.assertEqual(fire_time, expected_fire_time)
        self.assertEqual(duration, 900)

    def test_calculate_alarm_time_no_params(self):
        """Test that calculate_alarm_time raises error with no parameters."""
        with self.assertRaises(ValueError):
            utils._calculate_alarm_time()

    def test_calculate_timer_time_no_params(self):
        """Test that calculate_timer_time raises error with no parameters."""
        with self.assertRaises(ValueError):
            utils._calculate_timer_time()

    # ========================================
    # Filter Function Tests  
    # ========================================

    def test_filter_alarms(self):
        """Test filtering alarms by various criteria."""
        # Setup test alarms
        alarms = {
            "ALARM-1": {
                "alarm_id": "ALARM-1",
                "time_of_day": "7:00 AM",
                "label": "Morning alarm",
                "state": "ACTIVE",
                "date": "2024-01-15",
                "fire_time": "2024-01-15T07:00:00"
            },
            "ALARM-2": {
                "alarm_id": "ALARM-2",
                "time_of_day": "8:30 AM",
                "label": "Meeting reminder",
                "state": "DISABLED",
                "date": "2024-01-15",
                "fire_time": "2024-01-15T08:30:00"
            }
        }
        
        # Test filter by label
        filters = {"label": "Morning alarm"}
        result = utils._filter_alarms(alarms, filters)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["alarm_id"], "ALARM-1")
        
        # Test filter by state
        filters = {"alarm_type": "DISABLED"}
        result = utils._filter_alarms(alarms, filters)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["alarm_id"], "ALARM-2")

    def test_filter_timers(self):
        """Test filtering timers by various criteria."""
        # Setup test timers
        timers = {
            "TIMER-1": {
                "timer_id": "TIMER-1",
                "original_duration": "25m",
                "label": "Pomodoro",
                "state": "RUNNING"
            },
            "TIMER-2": {
                "timer_id": "TIMER-2", 
                "original_duration": "10m",
                "label": "Break timer",
                "state": "PAUSED"
            }
        }
        
        # Test filter by duration
        filters = {"duration": "25m"}
        result = utils._filter_timers(timers, filters)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["timer_id"], "TIMER-1")
        
        # Test filter by state
        filters = {"timer_type": "PAUSED"}
        result = utils._filter_timers(timers, filters)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["timer_id"], "TIMER-2")

    def test_alarm_matches_filter(self):
        """Test individual alarm matching against filters."""
        alarm = {
            "alarm_id": "TEST-ALARM",
            "time_of_day": "7:00 AM",
            "label": "Test alarm",
            "state": "ACTIVE",
            "date": "2024-01-15"
        }
        
        # Should match
        self.assertTrue(utils._alarm_matches_filter(alarm, {"label": "Test alarm"}))
        self.assertTrue(utils._alarm_matches_filter(alarm, {"time": "7:00 AM"}))
        
        # Should not match
        self.assertFalse(utils._alarm_matches_filter(alarm, {"label": "Different alarm"}))
        self.assertFalse(utils._alarm_matches_filter(alarm, {"time": "8:00 AM"}))

    def test_timer_matches_filter(self):
        """Test individual timer matching against filters."""
        timer = {
            "timer_id": "TEST-TIMER",
            "original_duration": "25m",
            "label": "Test timer",
            "state": "RUNNING"
        }
        
        # Should match
        self.assertTrue(utils._timer_matches_filter(timer, {"label": "Test timer"}))
        self.assertTrue(utils._timer_matches_filter(timer, {"duration": "25m"}))
        
        # Should not match
        self.assertFalse(utils._timer_matches_filter(timer, {"label": "Different timer"}))
        self.assertFalse(utils._timer_matches_filter(timer, {"duration": "30m"}))

    # ========================================
    # Current Time Function Tests
    # ========================================

    def test_get_current_time(self):
        """Test getting current time."""
        result = utils._get_current_time()
        self.assertIsInstance(result, datetime)
        
        # Should be close to actual current time (within 1 second)
        now = datetime.now()
        time_diff = abs((result - now).total_seconds())
        self.assertLess(time_diff, 1.0)

    # ========================================
    # Alarm State Function Tests
    # ========================================

    @patch('clock.SimulationEngine.utils.datetime')
    def test_get_alarm_state_firing(self, mock_datetime):
        """Test alarm state determination when alarm should be firing."""
        # Mock current time
        mock_now = datetime(2024, 1, 15, 7, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
        
        alarm = {
            "state": "ACTIVE",
            "fire_time": "2024-01-15T07:00:00"  # Same as current time
        }
        
        result = utils._get_alarm_state(alarm)
        self.assertEqual(result, "FIRING")

    @patch('clock.SimulationEngine.utils.datetime')
    def test_get_alarm_state_not_firing(self, mock_datetime):
        """Test alarm state determination when alarm is not firing."""
        # Mock current time  
        mock_now = datetime(2024, 1, 15, 6, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromisoformat.side_effect = datetime.fromisoformat
        
        alarm = {
            "state": "ACTIVE",
            "fire_time": "2024-01-15T07:00:00"  # Future time
        }
        
        result = utils._get_alarm_state(alarm)
        self.assertEqual(result, "ACTIVE")

    def test_get_alarm_state_non_active(self):
        """Test alarm state determination for non-active alarms."""
        alarm = {
            "state": "DISABLED",
            "fire_time": "2024-01-15T07:00:00"
        }
        
        result = utils._get_alarm_state(alarm)
        self.assertEqual(result, "DISABLED")

    # ========================================
    # Edge Cases and Error Handling Tests
    # ========================================

    def test_parse_duration_edge_cases(self):
        """Test duration parsing edge cases."""
        # Single unit maximum values
        self.assertEqual(utils._parse_duration("24h"), 86400)     # 24 hours
        self.assertEqual(utils._parse_duration("59m"), 3540)      # 59 minutes
        self.assertEqual(utils._parse_duration("59s"), 59)        # 59 seconds
        
        # Large durations
        self.assertEqual(utils._parse_duration("100h"), 360000)   # 100 hours

    def test_parse_time_edge_cases(self):
        """Test time parsing edge cases."""
        # Boundary times
        self.assertEqual(utils._parse_time("00:00"), (0, 0, 0))
        self.assertEqual(utils._parse_time("23:59"), (23, 59, 0))
        self.assertEqual(utils._parse_time("12:00 AM"), (0, 0, 0))
        self.assertEqual(utils._parse_time("12:00 PM"), (12, 0, 0))

    def test_filter_functions_empty_input(self):
        """Test filter functions with empty input."""
        # Empty alarms
        result = utils._filter_alarms({}, {"label": "test"})
        self.assertEqual(len(result), 0)
        
        # Empty timers
        result = utils._filter_timers({}, {"label": "test"})
        self.assertEqual(len(result), 0)

    def test_id_generation_consistency(self):
        """Test that ID generation is consistent for same input."""
        existing = {"ITEM-1": {}, "ITEM-2": {}}
        
        id1 = utils._generate_id("TEST", existing)
        id2 = utils._generate_id("TEST", existing)
        
        # Should generate same ID for same input
        self.assertEqual(id1, id2)
        self.assertEqual(id1, "TEST-3")

class TestSetStopwatchElapsedTime:
    """Test the _set_stopwatch_elapsed_time utility function"""
    
    def setup_method(self):
        """Reset DB before each test"""
        DB.clear()
        DB.update({
            "alarms": {},
            "timers": {},
            "stopwatch": {}
        })
    
    def test_set_stopwatch_elapsed_time_basic(self):
        """Test basic functionality of setting elapsed time"""
        result = _set_stopwatch_elapsed_time("10m30s")
        
        assert result["state"] == "PAUSED"
        assert result["start_time"] is None
        assert result["pause_time"] is None
        assert result["elapsed_time"] == 630  # 10*60 + 30 = 630 seconds
        assert result["lap_times"] == []
        
        # Check DB was updated
        assert DB["stopwatch"]["elapsed_time"] == 630
        assert DB["stopwatch"]["state"] == "PAUSED"
    
    def test_set_stopwatch_elapsed_time_various_formats(self):
        """Test various duration formats"""
        test_cases = [
            ("5m", 300),          # 5 minutes = 300 seconds
            ("1h30m", 5400),      # 1 hour 30 minutes = 5400 seconds
            ("2h15m45s", 8145),   # 2h 15m 45s = 8145 seconds
            ("45s", 45),          # 45 seconds
            ("0s", 0),            # 0 seconds
            ("120s", 120),        # 120 seconds
        ]
        
        for duration_str, expected_seconds in test_cases:
            result = _set_stopwatch_elapsed_time(duration_str)
            assert result["elapsed_time"] == expected_seconds, f"Failed for {duration_str}"
    
    def test_set_stopwatch_elapsed_time_invalid_format(self):
        """Test invalid duration formats raise ValueError"""
        invalid_formats = [
            "invalid",
            "10x30y",
            "",       # Empty string
            "10m30",  # Missing 's'
            "25:30",  # Wrong format
            "-5m",    # Negative
        ]
        
        for invalid_format in invalid_formats:
            with pytest.raises(ValueError, match="Invalid elapsed_time format"):
                _set_stopwatch_elapsed_time(invalid_format)
    
    def test_set_stopwatch_elapsed_time_overwrites_existing(self):
        """Test that setting elapsed time overwrites existing stopwatch data"""
        # Set initial stopwatch data
        DB["stopwatch"] = {
            "state": "RUNNING",
            "start_time": "2024-01-01T10:00:00",
            "pause_time": None,
            "elapsed_time": 1000,
            "lap_times": ["5m00s", "10m30s"]
        }
        
        # Set new elapsed time
        result = _set_stopwatch_elapsed_time("15m")
        
        # Should overwrite everything
        assert result["state"] == "PAUSED"
        assert result["start_time"] is None
        assert result["pause_time"] is None
        assert result["elapsed_time"] == 900  # 15 minutes
        assert result["lap_times"] == []  # Cleared
        
        # Check DB was updated
        assert DB["stopwatch"]["elapsed_time"] == 900
        assert DB["stopwatch"]["state"] == "PAUSED"
        assert DB["stopwatch"]["lap_times"] == []
    
    def test_set_stopwatch_elapsed_time_no_existing_stopwatch(self):
        """Test setting elapsed time when no stopwatch exists in DB"""
        # Remove stopwatch from DB
        if "stopwatch" in DB:
            del DB["stopwatch"]
        
        result = _set_stopwatch_elapsed_time("2h")
        
        assert result["elapsed_time"] == 7200  # 2 hours
        assert "stopwatch" in DB
        assert DB["stopwatch"]["elapsed_time"] == 7200
    
    def test_set_stopwatch_elapsed_time_zero_duration(self):
        """Test setting zero elapsed time"""
        result = _set_stopwatch_elapsed_time("0s")
        
        assert result["elapsed_time"] == 0
        assert result["state"] == "PAUSED"
        assert DB["stopwatch"]["elapsed_time"] == 0
    
    def test_set_stopwatch_elapsed_time_large_duration(self):
        """Test setting large elapsed time"""
        # 24 hours
        result = _set_stopwatch_elapsed_time("24h")
        
        assert result["elapsed_time"] == 86400  # 24 * 60 * 60
        assert DB["stopwatch"]["elapsed_time"] == 86400
    
    def test_set_stopwatch_elapsed_time_preserves_other_db_data(self):
        """Test that setting elapsed time doesn't affect alarms or timers"""
        # Set up some alarm and timer data
        DB.update({
            "alarms": {"alarm1": {"time": "10:00"}},
            "timers": {"timer1": {"duration": "5m"}}
        })
        
        _set_stopwatch_elapsed_time("10m")
        
        # Other data should be preserved
        assert "alarm1" in DB["alarms"]
        assert "timer1" in DB["timers"]
        assert DB["alarms"]["alarm1"]["time"] == "10:00"
        assert DB["timers"]["timer1"]["duration"] == "5m"


class TestUtilityFunctionIntegration:
    """Test integration of utility function with other stopwatch operations"""
    
    def setup_method(self):
        """Reset DB before each test"""
        DB.clear()
        DB.update({
            "alarms": {},
            "timers": {},
            "stopwatch": {}
        })
    
    def test_utility_function_with_stopwatch_operations(self):
        """Test that utility function works well with stopwatch API operations"""
        from clock.StopwatchApi import start_stopwatch, show_stopwatch, pause_stopwatch
        
        # Set elapsed time using utility function
        _set_stopwatch_elapsed_time("30m")
        
        # Verify initial state
        assert DB["stopwatch"]["elapsed_time"] == 1800  # 30 minutes
        assert DB["stopwatch"]["state"] == "PAUSED"
        
        # Start the stopwatch (should resume from PAUSED state)
        start_result = start_stopwatch()
        assert "Stopwatch resumed" in start_result["message"]  # Should be "resumed" not "started"
        assert DB["stopwatch"]["state"] == "RUNNING"
        
        # Show stopwatch (should handle vendor data correctly)
        show_result = show_stopwatch()
        assert "30m" in show_result["message"]
        
        # Pause the stopwatch
        pause_result = pause_stopwatch()
        assert "Stopwatch paused" in pause_result["message"]
        assert DB["stopwatch"]["state"] == "PAUSED"
    
    def test_utility_function_duration_parsing_consistency(self):
        """Test that utility function uses same duration parsing as other functions"""
        # Test that _set_stopwatch_elapsed_time uses same parsing as _parse_duration
        test_duration = "1h15m30s"
        
        # Parse using utility function
        stopwatch_data = _set_stopwatch_elapsed_time(test_duration)
        utility_seconds = stopwatch_data["elapsed_time"]
        
        # Parse directly
        direct_seconds = _parse_duration(test_duration)
        
        assert utility_seconds == direct_seconds
        
        # Also check formatting consistency
        formatted_duration = _seconds_to_duration(utility_seconds)
        assert "1h15m30s" == formatted_duration or "1h15m" in formatted_duration

if __name__ == "__main__":
    unittest.main()