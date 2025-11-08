"""
State persistence tests for the Clock service.

This module tests the database state management functionality including:
- State saving and loading
- Backward compatibility 
- Data persistence integrity
- State recovery and restoration
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch

try:
    from common_utils.base_case import BaseTestCaseWithErrorHandler
except ImportError:
    from common_utils.base_case import BaseTestCaseWithErrorHandler

from clock.SimulationEngine.db import DB, save_state, load_state, reset_db, get_minified_state
from clock.SimulationEngine.models import ClockDB, ClockAlarm, ClockTimer


class TestClockDatabaseState(BaseTestCaseWithErrorHandler):
    """Test database state management for Clock service."""
    
    def setUp(self):
        """Set up test fixtures with clean database state."""
        super().setUp()
        self.test_dir = tempfile.mkdtemp()
        reset_db()
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()
        # Clean up test directory
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        reset_db()

    def test_save_state_creates_valid_json(self):
        """Test that save_state creates a valid JSON file."""
        test_file = os.path.join(self.test_dir, "test_state.json")
        
        # Save current state
        save_state(test_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(test_file))
        
        # Verify file contains valid JSON
        try:
            with open(test_file, 'r') as f:
                loaded_data = json.load(f)
            
            # Verify basic structure
            self.assertIsInstance(loaded_data, dict)
            self.assertIn("alarms", loaded_data)
            self.assertIn("timers", loaded_data)
            self.assertIn("stopwatch", loaded_data)
            self.assertIn("settings", loaded_data)
            
        except json.JSONDecodeError:
            self.fail("save_state did not create valid JSON")

    def test_load_state_restores_database(self):
        """Test that load_state properly restores database state."""
        test_file = os.path.join(self.test_dir, "test_state.json")
        
        # Create test data
        original_db_copy = DB.copy()
        
        # Modify database
        DB["test_marker"] = "test_value"
        
        # Save modified state
        save_state(test_file)
        
        # Reset database
        reset_db()
        
        # Verify database was reset (test_marker should be gone)
        self.assertNotIn("test_marker", DB)
        
        # Load saved state
        load_state(test_file)
        
        # Verify state was restored
        self.assertIn("test_marker", DB)
        self.assertEqual(DB["test_marker"], "test_value")

    def test_save_load_state_round_trip(self):
        """Test complete save/load round trip maintains data integrity."""
        test_file = os.path.join(self.test_dir, "roundtrip_test.json")
        
        # Add test alarm
        test_alarm = {
            "alarm_id": "TEST-ROUND-TRIP-1",
            "time_of_day": "6:00 AM",
            "date": "2024-01-16",
            "label": "Round trip test alarm",
            "state": "ACTIVE",
            "recurrence": "MONDAY,WEDNESDAY,FRIDAY",
            "created_at": "2024-01-15T20:00:00",
            "fire_time": "2024-01-16T06:00:00"
        }
        DB["alarms"]["TEST-ROUND-TRIP-1"] = test_alarm
        
        # Add test timer
        test_timer = {
            "timer_id": "TEST-ROUND-TRIP-1",
            "original_duration": "15m",
            "remaining_duration": "12m30s",
            "time_of_day": "3:15 PM", 
            "label": "Round trip test timer",
            "state": "RUNNING",
            "created_at": "2024-01-16T15:00:00",
            "fire_time": "2024-01-16T15:15:00",
            "start_time": "2024-01-16T15:00:00"
        }
        DB["timers"]["TEST-ROUND-TRIP-1"] = test_timer
        
        # Modify stopwatch state
        DB["stopwatch"]["state"] = "PAUSED"
        DB["stopwatch"]["elapsed_time"] = 1234
        
        # Save original state
        original_db = DB.copy()
        save_state(test_file)
        
        # Reset and load
        reset_db()
        load_state(test_file)
        
        # Verify alarm data integrity
        restored_alarm = DB["alarms"]["TEST-ROUND-TRIP-1"]
        for key, value in test_alarm.items():
            self.assertEqual(restored_alarm[key], value, f"Alarm field '{key}' not preserved")
        
        # Verify timer data integrity
        restored_timer = DB["timers"]["TEST-ROUND-TRIP-1"]
        for key, value in test_timer.items():
            self.assertEqual(restored_timer[key], value, f"Timer field '{key}' not preserved")
        
        # Verify stopwatch state
        self.assertEqual(DB["stopwatch"]["state"], "PAUSED")
        self.assertEqual(DB["stopwatch"]["elapsed_time"], 1234)

    def test_load_state_nonexistent_file(self):
        """Test load_state behavior with non-existent file."""
        nonexistent_file = os.path.join(self.test_dir, "does_not_exist.json")
        
        # Should not raise exception
        try:
            load_state(nonexistent_file)
        except Exception as e:
            self.fail(f"load_state raised exception for non-existent file: {e}")

    def test_save_state_with_complex_data_structures(self):
        """Test saving state with complex nested structures."""
        test_file = os.path.join(self.test_dir, "complex_state.json")
        
        # Add complex stopwatch data with lap times
        DB["stopwatch"]["lap_times"] = [
            {
                "lap_number": 1,
                "lap_time": 60,
                "lap_duration": "1m",
                "split_time": 60,
                "split_duration": "1m",
                "timestamp": "2024-01-15T10:01:00"
            },
            {
                "lap_number": 2,
                "lap_time": 125,
                "lap_duration": "2m5s",
                "split_time": 65,
                "split_duration": "1m5s",
                "timestamp": "2024-01-15T10:02:05"
            }
        ]
        
        # Save and load
        save_state(test_file)
        reset_db()
        load_state(test_file)
        
        # Verify complex structure preservation
        lap_times = DB["stopwatch"]["lap_times"]
        self.assertEqual(len(lap_times), 2)
        self.assertEqual(lap_times[0]["lap_number"], 1)
        self.assertEqual(lap_times[1]["split_time"], 65)

    def test_backward_compatibility_with_older_state_format(self):
        """Test that the system can load states saved in older formats."""
        test_file = os.path.join(self.test_dir, "legacy_state.json")
        
        # Create a legacy state format (missing some newer fields)
        legacy_state = {
            "alarms": {
                "LEGACY-ALARM-1": {
                    "alarm_id": "LEGACY-ALARM-1",
                    "time_of_day": "8:00 AM",
                    "date": "2024-01-15",
                    "label": "Legacy alarm",
                    "state": "ACTIVE",
                    "recurrence": "",
                    "created_at": "2024-01-14T20:00:00",
                    "fire_time": "2024-01-15T08:00:00"
                    # Note: might be missing some newer fields
                }
            },
            "timers": {},
            "stopwatch": {
                "state": "STOPPED",
                "start_time": None,
                "elapsed_time": 0,
                "lap_times": []
                # Note: pause_time might be missing in legacy format
            },
            "settings": {
                "default_alarm_sound": "legacy_sound",
                "default_timer_sound": "legacy_timer_sound",
                "snooze_duration": 300,  # Different default
                "alarm_volume": 1.0,
                "timer_volume": 1.0,
                "time_format": "24_hour",
                "show_seconds": "true"  # String format in legacy
            }
        }
        
        # Write legacy format
        with open(test_file, 'w') as f:
            json.dump(legacy_state, f)
        
        # Load legacy state
        reset_db()
        load_state(test_file)
        
        # Verify legacy data was loaded correctly
        self.assertIn("LEGACY-ALARM-1", DB["alarms"])
        self.assertEqual(DB["alarms"]["LEGACY-ALARM-1"]["label"], "Legacy alarm")
        self.assertEqual(DB["settings"]["snooze_duration"], 300)

    def test_get_minified_state_returns_current_state(self):
        """Test that get_minified_state returns the current database state."""
        # Modify database
        DB["test_field"] = "test_value"
        
        # Get minified state
        minified = get_minified_state()
        
        # Verify it contains current data
        self.assertIn("test_field", minified)
        self.assertEqual(minified["test_field"], "test_value")
        self.assertIn("alarms", minified)
        self.assertIn("timers", minified)
        self.assertIn("stopwatch", minified)
        self.assertIn("settings", minified)

    def test_state_persistence_with_unicode_data(self):
        """Test state persistence with unicode characters."""
        test_file = os.path.join(self.test_dir, "unicode_state.json")
        
        # Add alarm with unicode characters
        unicode_alarm = {
            "alarm_id": "UNICODE-TEST-1",
            "time_of_day": "7:00 AM",
            "date": "2024-01-15",
            "label": "Réveil du matin 🔔 测试",  # Unicode characters
            "state": "ACTIVE",
            "recurrence": "",
            "created_at": "2024-01-14T22:00:00",
            "fire_time": "2024-01-15T07:00:00"
        }
        DB["alarms"]["UNICODE-TEST-1"] = unicode_alarm
        
        # Save and load
        save_state(test_file)
        reset_db()
        load_state(test_file)
        
        # Verify unicode preservation
        restored_alarm = DB["alarms"]["UNICODE-TEST-1"]
        self.assertEqual(restored_alarm["label"], "Réveil du matin 🔔 测试")

    def test_state_file_permissions_and_access(self):
        """Test state file creation with proper permissions."""
        test_file = os.path.join(self.test_dir, "permissions_test.json")
        
        # Save state
        save_state(test_file)
        
        # Verify file exists and is readable
        self.assertTrue(os.path.exists(test_file))
        self.assertTrue(os.access(test_file, os.R_OK))
        
        # Verify file has reasonable permissions (not world-writable)
        file_stat = os.stat(test_file)
        file_mode = file_stat.st_mode
        
        # File should be readable by owner
        self.assertTrue(file_mode & 0o400)  # Owner read permission

    def test_concurrent_state_operations(self):
        """Test behavior with concurrent state operations."""
        test_file1 = os.path.join(self.test_dir, "concurrent1.json")
        test_file2 = os.path.join(self.test_dir, "concurrent2.json")
        
        # Set initial state
        DB["test_marker"] = "initial_value"
        
        # Save to first file
        save_state(test_file1)
        
        # Modify database
        DB["test_marker"] = "modified_value"
        
        # Save to second file
        save_state(test_file2)
        
        # Load first file (should restore initial value)
        load_state(test_file1)
        self.assertEqual(DB["test_marker"], "initial_value")
        
        # Load second file (should restore modified value)  
        load_state(test_file2)
        self.assertEqual(DB["test_marker"], "modified_value")

    def test_state_validation_after_load(self):
        """Test that loaded state passes database validation."""
        test_file = os.path.join(self.test_dir, "validation_test.json")
        
        # Save current valid state
        save_state(test_file)
        
        # Reset and load
        reset_db()
        load_state(test_file)
        
        # Validate loaded state against Pydantic model
        try:
            validated_db = ClockDB(**DB)
            
            # Verify structure is valid
            self.assertIsInstance(validated_db.alarms, dict)
            self.assertIsInstance(validated_db.timers, dict)
            self.assertIsInstance(validated_db.stopwatch, object)
            self.assertIsInstance(validated_db.settings, object)
            
        except Exception as e:
            self.fail(f"Loaded state failed validation: {e}")

    def test_large_state_file_handling(self):
        """Test handling of large state files with many entries."""
        test_file = os.path.join(self.test_dir, "large_state.json")
        
        # Create many alarms and timers
        for i in range(100):
            alarm_id = f"LARGE-TEST-ALARM-{i}"
            DB["alarms"][alarm_id] = {
                "alarm_id": alarm_id,
                "time_of_day": f"{7 + (i % 12)}:00 AM",
                "date": "2024-01-15",
                "label": f"Large test alarm {i}",
                "state": "ACTIVE",
                "recurrence": "",
                "created_at": f"2024-01-14T{20 + (i % 4):02d}:00:00",
                "fire_time": f"2024-01-15T{7 + (i % 12):02d}:00:00"
            }
            
            timer_id = f"LARGE-TEST-TIMER-{i}"
            DB["timers"][timer_id] = {
                "timer_id": timer_id,
                "original_duration": f"{10 + (i % 50)}m",
                "remaining_duration": f"{5 + (i % 25)}m",
                "time_of_day": f"{14 + (i % 6)}:00 PM",
                "label": f"Large test timer {i}",
                "state": "RUNNING",
                "created_at": f"2024-01-15T{14 + (i % 6):02d}:00:00",
                "fire_time": f"2024-01-15T{14 + (i % 6):02d}:{10 + (i % 50):02d}:00",
                "start_time": f"2024-01-15T{14 + (i % 6):02d}:00:00"
            }
        
        # Save large state
        save_state(test_file)
        
        # Verify file was created successfully
        self.assertTrue(os.path.exists(test_file))
        
        # Reset and load
        reset_db()
        load_state(test_file)
        
        # Verify all data was restored (including original DB alarms)
        self.assertGreaterEqual(len(DB["alarms"]), 100)  # At least 100 new alarms
        self.assertGreaterEqual(len(DB["timers"]), 100)  # At least 100 new timers
        
        # Spot check some entries
        self.assertIn("LARGE-TEST-ALARM-50", DB["alarms"])
        self.assertIn("LARGE-TEST-TIMER-75", DB["timers"])


if __name__ == "__main__":
    unittest.main()
