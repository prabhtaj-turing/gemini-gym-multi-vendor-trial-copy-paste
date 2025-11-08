"""
Database validation tests for the Clock service.

This module contains tests that validate the integrity and structure of the Clock database
against the defined Pydantic models. These tests ensure that the database maintains
consistency and follows the expected schema.

Test Categories:
- Model validation tests
- Database structure validation 
- Data integrity tests
- Schema compliance tests
"""

import unittest
from datetime import datetime
from typing import Dict, Any
import json

try:
    from common_utils.base_case import BaseTestCaseWithErrorHandler
except ImportError:
    from common_utils.base_case import BaseTestCaseWithErrorHandler

from clock.SimulationEngine.db import DB, reset_db
from clock.SimulationEngine.models import (
    ClockDB, ClockAlarm, ClockTimer, ClockStopwatch, 
    ClockSettings, LapTime
)
from pydantic import ValidationError


class TestClockDatabaseValidation(BaseTestCaseWithErrorHandler):
    """Test database validation for Clock service."""
    
    def setUp(self):
        """Set up test fixtures with clean database state."""
        super().setUp()
        reset_db()
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()
        reset_db()

    def test_complete_database_validation_success(self):
        """Test that the complete database validates successfully against ClockDB model."""
        try:
            # Validate the entire database structure
            validated_db = ClockDB(**DB)
            
            # Verify database structure
            self.assertIsInstance(validated_db.alarms, dict)
            self.assertIsInstance(validated_db.timers, dict)
            self.assertIsInstance(validated_db.stopwatch, ClockStopwatch)
            self.assertIsInstance(validated_db.settings, ClockSettings)
            
            # Verify alarms structure
            for alarm_id, alarm_data in validated_db.alarms.items():
                self.assertIsInstance(alarm_data, ClockAlarm)
                self.assertEqual(alarm_data.alarm_id, alarm_id)
            
            # Verify timers structure  
            for timer_id, timer_data in validated_db.timers.items():
                self.assertIsInstance(timer_data, ClockTimer)
                self.assertEqual(timer_data.timer_id, timer_id)
                
        except ValidationError as e:
            self.fail(f"Database validation failed: {e}")

    def test_individual_alarm_model_validation(self):
        """Test individual alarm data validation."""
        # Get first alarm from DB for testing
        alarms = DB.get("alarms", {})
        if not alarms:
            self.skipTest("No alarms in database to validate")
        
        alarm_id, alarm_data = next(iter(alarms.items()))
        
        try:
            validated_alarm = ClockAlarm(**alarm_data)
            
            # Verify required fields
            self.assertEqual(validated_alarm.alarm_id, alarm_id)
            self.assertIsNotNone(validated_alarm.time_of_day)
            self.assertIsNotNone(validated_alarm.date)
            self.assertIsNotNone(validated_alarm.state)
            self.assertIsNotNone(validated_alarm.created_at)
            self.assertIsNotNone(validated_alarm.fire_time)
            
            # Verify field types
            self.assertIsInstance(validated_alarm.alarm_id, str)
            self.assertIsInstance(validated_alarm.time_of_day, str)
            self.assertIsInstance(validated_alarm.date, str)
            self.assertIsInstance(validated_alarm.label, str)
            self.assertIsInstance(validated_alarm.state, str)
            self.assertIsInstance(validated_alarm.recurrence, str)
            
        except ValidationError as e:
            self.fail(f"Alarm validation failed for {alarm_id}: {e}")

    def test_individual_timer_model_validation(self):
        """Test individual timer data validation."""
        timers = DB.get("timers", {})
        if not timers:
            self.skipTest("No timers in database to validate")
        
        timer_id, timer_data = next(iter(timers.items()))
        
        try:
            validated_timer = ClockTimer(**timer_data)
            
            # Verify required fields
            self.assertEqual(validated_timer.timer_id, timer_id)
            self.assertIsNotNone(validated_timer.original_duration)
            self.assertIsNotNone(validated_timer.remaining_duration)
            self.assertIsNotNone(validated_timer.state)
            self.assertIsNotNone(validated_timer.created_at)
            self.assertIsNotNone(validated_timer.fire_time)
            self.assertIsNotNone(validated_timer.start_time)
            
            # Verify field types
            self.assertIsInstance(validated_timer.timer_id, str)
            self.assertIsInstance(validated_timer.original_duration, str)
            self.assertIsInstance(validated_timer.remaining_duration, str)
            self.assertIsInstance(validated_timer.label, str)
            self.assertIsInstance(validated_timer.state, str)
            
        except ValidationError as e:
            self.fail(f"Timer validation failed for {timer_id}: {e}")

    def test_stopwatch_model_validation(self):
        """Test stopwatch data validation."""
        stopwatch_data = DB.get("stopwatch", {})
        if not stopwatch_data:
            self.skipTest("No stopwatch data in database to validate")
        
        try:
            validated_stopwatch = ClockStopwatch(**stopwatch_data)
            
            # Verify required fields
            self.assertIsNotNone(validated_stopwatch.state)
            self.assertIsInstance(validated_stopwatch.elapsed_time, int)
            self.assertIsInstance(validated_stopwatch.lap_times, list)
            
            # Verify state is valid
            self.assertIn(validated_stopwatch.state, ["STOPPED", "RUNNING", "PAUSED"])
            
            # Verify elapsed time is non-negative
            self.assertGreaterEqual(validated_stopwatch.elapsed_time, 0)
            
        except ValidationError as e:
            self.fail(f"Stopwatch validation failed: {e}")

    def test_settings_model_validation(self):
        """Test settings data validation."""
        settings_data = DB.get("settings", {})
        if not settings_data:
            self.skipTest("No settings data in database to validate")
        
        try:
            validated_settings = ClockSettings(**settings_data)
            
            # Verify required fields exist
            self.assertIsNotNone(validated_settings.default_alarm_sound)
            self.assertIsNotNone(validated_settings.default_timer_sound)
            self.assertIsNotNone(validated_settings.snooze_duration)
            self.assertIsNotNone(validated_settings.alarm_volume)
            self.assertIsNotNone(validated_settings.timer_volume)
            self.assertIsNotNone(validated_settings.time_format)
            
            # Verify data types and ranges
            self.assertIsInstance(validated_settings.snooze_duration, int)
            self.assertGreater(validated_settings.snooze_duration, 0)
            
            self.assertIsInstance(validated_settings.alarm_volume, (int, float))
            self.assertTrue(0.0 <= validated_settings.alarm_volume <= 1.0)
            
            self.assertIsInstance(validated_settings.timer_volume, (int, float))
            self.assertTrue(0.0 <= validated_settings.timer_volume <= 1.0)
            
            self.assertIn(validated_settings.time_format, ["12_hour", "24_hour"])
            
        except ValidationError as e:
            self.fail(f"Settings validation failed: {e}")

    def test_database_integrity_id_consistency(self):
        """Test that alarm and timer IDs are consistent between keys and data."""
        # Test alarms
        alarms = DB.get("alarms", {})
        for alarm_id, alarm_data in alarms.items():
            self.assertEqual(alarm_id, alarm_data.get("alarm_id"), 
                           f"Alarm ID mismatch: key '{alarm_id}' vs data '{alarm_data.get('alarm_id')}'")
        
        # Test timers
        timers = DB.get("timers", {})
        for timer_id, timer_data in timers.items():
            self.assertEqual(timer_id, timer_data.get("timer_id"),
                           f"Timer ID mismatch: key '{timer_id}' vs data '{timer_data.get('timer_id')}'")

    def test_alarm_state_validation(self):
        """Test that alarm states are valid."""
        valid_states = ["ACTIVE", "DISABLED", "SNOOZED", "CANCELLED", "FIRING"]
        
        alarms = DB.get("alarms", {})
        for alarm_id, alarm_data in alarms.items():
            state = alarm_data.get("state")
            self.assertIn(state, valid_states, 
                         f"Invalid alarm state '{state}' for alarm {alarm_id}")

    def test_timer_state_validation(self):
        """Test that timer states are valid."""
        valid_states = ["RUNNING", "PAUSED", "FINISHED", "RESET", "CANCELLED", "STOPPED"]
        
        timers = DB.get("timers", {})
        for timer_id, timer_data in timers.items():
            state = timer_data.get("state")
            self.assertIn(state, valid_states, 
                         f"Invalid timer state '{state}' for timer {timer_id}")

    def test_date_format_validation(self):
        """Test that dates are in correct YYYY-MM-DD format."""
        alarms = DB.get("alarms", {})
        for alarm_id, alarm_data in alarms.items():
            date_str = alarm_data.get("date")
            if date_str:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    self.fail(f"Invalid date format '{date_str}' for alarm {alarm_id}")

    def test_iso_timestamp_validation(self):
        """Test that timestamps are in valid ISO format."""
        # Test alarm timestamps
        alarms = DB.get("alarms", {})
        for alarm_id, alarm_data in alarms.items():
            for field in ["created_at", "fire_time"]:
                timestamp = alarm_data.get(field)
                if timestamp:
                    try:
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        self.fail(f"Invalid timestamp '{timestamp}' in field '{field}' for alarm {alarm_id}")
        
        # Test timer timestamps
        timers = DB.get("timers", {})
        for timer_id, timer_data in timers.items():
            for field in ["created_at", "fire_time", "start_time"]:
                timestamp = timer_data.get(field)
                if timestamp:
                    try:
                        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except ValueError:
                        self.fail(f"Invalid timestamp '{timestamp}' in field '{field}' for timer {timer_id}")

    def test_duration_format_validation(self):
        """Test that durations are in correct format."""
        import re
        duration_pattern = r'^(?:\d+h)?(?:\d+m)?(?:\d+s)?$'
        
        timers = DB.get("timers", {})
        for timer_id, timer_data in timers.items():
            for field in ["original_duration", "remaining_duration"]:
                duration = timer_data.get(field)
                if duration and duration != "0s":  # Allow "0s" for finished timers
                    self.assertRegex(duration, duration_pattern,
                                   f"Invalid duration format '{duration}' in field '{field}' for timer {timer_id}")

    def test_pydantic_model_creation_with_valid_data(self):
        """Test creating Pydantic models with valid sample data."""
        # Test ClockAlarm creation
        alarm_data = {
            "alarm_id": "TEST-ALARM-1",
            "time_of_day": "7:00 AM",
            "date": "2024-01-15",
            "label": "Test alarm",
            "state": "ACTIVE",
            "recurrence": "MONDAY,TUESDAY",
            "created_at": "2024-01-14T22:30:00",
            "fire_time": "2024-01-15T07:00:00"
        }
        
        try:
            alarm = ClockAlarm(**alarm_data)
            self.assertEqual(alarm.alarm_id, "TEST-ALARM-1")
            self.assertEqual(alarm.state, "ACTIVE")
        except ValidationError as e:
            self.fail(f"Failed to create ClockAlarm with valid data: {e}")
        
        # Test ClockTimer creation
        timer_data = {
            "timer_id": "TEST-TIMER-1",
            "original_duration": "25m",
            "remaining_duration": "20m",
            "time_of_day": "2:45 PM",
            "label": "Test timer",
            "state": "RUNNING",
            "created_at": "2024-01-15T14:20:00",
            "fire_time": "2024-01-15T14:45:00",
            "start_time": "2024-01-15T14:20:00"
        }
        
        try:
            timer = ClockTimer(**timer_data)
            self.assertEqual(timer.timer_id, "TEST-TIMER-1")
            self.assertEqual(timer.state, "RUNNING")
        except ValidationError as e:
            self.fail(f"Failed to create ClockTimer with valid data: {e}")

    def test_pydantic_model_validation_errors(self):
        """Test that Pydantic models properly reject invalid data."""
        # Test invalid alarm state
        invalid_alarm_data = {
            "alarm_id": "TEST-ALARM-1",
            "time_of_day": "7:00 AM",
            "date": "2024-01-15",
            "label": "Test alarm",
            "state": "INVALID_STATE",  # Invalid state
            "recurrence": "",
            "created_at": "2024-01-14T22:30:00",
            "fire_time": "2024-01-15T07:00:00"
        }
        
        with self.assertRaises(ValidationError):
            ClockAlarm(**invalid_alarm_data)
        
        # Test invalid date format
        invalid_date_data = {
            "alarm_id": "TEST-ALARM-2",
            "time_of_day": "7:00 AM",
            "date": "01/15/2024",  # Invalid format
            "label": "Test alarm",
            "state": "ACTIVE",
            "recurrence": "",
            "created_at": "2024-01-14T22:30:00",
            "fire_time": "2024-01-15T07:00:00"
        }
        
        with self.assertRaises(ValidationError):
            ClockAlarm(**invalid_date_data)
        
        # Test invalid timer state
        invalid_timer_data = {
            "timer_id": "TEST-TIMER-1",
            "original_duration": "25m",
            "remaining_duration": "20m",
            "time_of_day": "2:45 PM",
            "label": "Test timer",
            "state": "INVALID_STATE",  # Invalid state
            "created_at": "2024-01-15T14:20:00",
            "fire_time": "2024-01-15T14:45:00",
            "start_time": "2024-01-15T14:20:00"
        }
        
        with self.assertRaises(ValidationError):
            ClockTimer(**invalid_timer_data)

    def test_settings_validation_edge_cases(self):
        """Test settings validation with edge cases."""
        # Test volume validation
        invalid_volume_settings = {
            "default_alarm_sound": "chime",
            "default_timer_sound": "bell", 
            "snooze_duration": 600,
            "alarm_volume": 1.5,  # Invalid - above 1.0
            "timer_volume": 0.7,
            "time_format": "12_hour",
            "show_seconds": False
        }
        
        with self.assertRaises(ValidationError):
            ClockSettings(**invalid_volume_settings)
        
        # Test snooze duration validation
        invalid_snooze_settings = {
            "default_alarm_sound": "chime",
            "default_timer_sound": "bell",
            "snooze_duration": 0,  # Invalid - must be positive
            "alarm_volume": 0.8,
            "timer_volume": 0.7,
            "time_format": "12_hour", 
            "show_seconds": False
        }
        
        with self.assertRaises(ValidationError):
            ClockSettings(**invalid_snooze_settings)


if __name__ == "__main__":
    unittest.main()
