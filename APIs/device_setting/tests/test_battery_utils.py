"""
Test battery utility functions
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from device_setting.SimulationEngine.device_insight_utils.battery_utils import (
    set_battery_percentage,
    set_battery_charging_status,
    set_battery_estimated_time_remaining,
    set_battery_health_status,
    set_battery_temperature_status,
    get_battery_insights
)
from device_setting.SimulationEngine.utils import set_device_insight_field, get_device_insight_data
from device_setting.SimulationEngine.db import load_state, DEFAULT_DB_PATH, DB
from device_setting.SimulationEngine.enums import Constants


class TestBatteryUtils(unittest.TestCase):
    """Test cases for battery utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Load default state and then clear battery data
        load_state(DEFAULT_DB_PATH)
        # Clear battery data specifically for testing
        if (Constants.DEVICE_INSIGHTS.value in DB and 
            Constants.INSIGHTS.value in DB[Constants.DEVICE_INSIGHTS.value] and
            Constants.BATTERY.value in DB[Constants.DEVICE_INSIGHTS.value][Constants.INSIGHTS.value]):
            DB[Constants.DEVICE_INSIGHTS.value][Constants.INSIGHTS.value].pop(Constants.BATTERY.value, None)

    def tearDown(self):
        """Clean up after tests."""
        load_state(DEFAULT_DB_PATH)

    def test_set_and_get_battery_percentage(self):
        """Test setting and getting battery percentage."""
        set_battery_percentage(80)
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.PERCENTAGE.value), 80)
        self.assertIn("last_updated", insights)

    def test_set_battery_percentage_invalid_negative(self):
        """Test setting battery percentage with negative value."""
        with self.assertRaises(ValueError):
            set_battery_percentage(-1)

    def test_set_battery_percentage_invalid_high(self):
        """Test setting battery percentage with value over 100."""
        with self.assertRaises(ValueError):
            set_battery_percentage(101)

    def test_set_battery_percentage_invalid_string(self):
        """Test setting battery percentage with string value."""
        with self.assertRaises(ValueError):
            set_battery_percentage("abc")

    def test_set_battery_percentage_invalid_float(self):
        """Test setting battery percentage with float value."""
        with self.assertRaises(ValueError):
            set_battery_percentage(50.5)

    def test_set_battery_percentage_valid_zero(self):
        """Test setting battery percentage with zero value."""
        set_battery_percentage(0)
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.PERCENTAGE.value), 0)

    def test_get_battery_percentage_default(self):
        """Test getting battery percentage when not set."""
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.PERCENTAGE.value), None)

    def test_set_and_get_battery_charging_status(self):
        """Test setting and getting battery charging status."""
        set_battery_charging_status("charging")
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.CHARGING_STATUS.value), "charging")
        
        set_battery_charging_status("not_charging")
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.CHARGING_STATUS.value), "not_charging")

    def test_get_battery_charging_status_default(self):
        """Test getting battery charging status when not set."""
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.CHARGING_STATUS.value), None)

    def test_set_battery_charging_status_invalid(self):
        """Test setting battery charging status with invalid value."""
        with self.assertRaises(ValueError):
            set_battery_charging_status("invalid_status")

    def test_set_and_get_battery_estimated_time_remaining(self):
        """Test setting and getting battery estimated time remaining."""
        set_battery_estimated_time_remaining(120)  # 120 minutes
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.ESTIMATED_TIME_REMAINING.value), 120)
        
        set_battery_estimated_time_remaining(30)  # 30 minutes
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.ESTIMATED_TIME_REMAINING.value), 30)

    def test_get_battery_estimated_time_remaining_default(self):
        """Test getting battery estimated time remaining when not set."""
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.ESTIMATED_TIME_REMAINING.value), None)

    def test_set_battery_estimated_time_remaining_none(self):
        """Test setting battery estimated time remaining to None."""
        set_battery_estimated_time_remaining(None)
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.ESTIMATED_TIME_REMAINING.value), None)

    def test_set_battery_estimated_time_remaining_invalid_negative(self):
        """Test setting battery estimated time remaining with negative value."""
        with self.assertRaises(ValueError):
            set_battery_estimated_time_remaining(-10)

    def test_set_and_get_battery_health(self):
        """Test setting and getting battery health."""
        set_battery_health_status("good")
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.HEALTH.value), "good")
        
        set_battery_health_status("poor")
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.HEALTH.value), "poor")

    def test_get_battery_health_default(self):
        """Test getting battery health when not set."""
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.HEALTH.value), None)

    def test_set_battery_health_invalid(self):
        """Test setting battery health with invalid value."""
        with self.assertRaises(ValueError):
            set_battery_health_status("invalid_health")

    def test_set_and_get_battery_temperature(self):
        """Test setting and getting battery temperature."""
        set_battery_temperature_status("normal")
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.TEMPERATURE.value), "normal")
        
        set_battery_temperature_status("hot")
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.TEMPERATURE.value), "hot")

    def test_get_battery_temperature_default(self):
        """Test getting battery temperature when not set."""
        insights = get_battery_insights()
        self.assertEqual(insights.get(Constants.TEMPERATURE.value), None)

    def test_set_battery_temperature_invalid(self):
        """Test setting battery temperature with invalid value."""
        with self.assertRaises(ValueError):
            set_battery_temperature_status("invalid_temperature")

    def test_get_battery_insights_empty(self):
        """Test getting battery insights when no data is set."""
        insights = get_battery_insights()
        self.assertEqual(insights, {})

    def test_timestamp_format(self):
        """Test that timestamps are properly formatted."""
        set_battery_percentage(50)
        insights = get_battery_insights()
        self.assertIn(Constants.LAST_UPDATED.value, insights)
        
        # Check that timestamp is a valid ISO format
        timestamp = insights[Constants.LAST_UPDATED.value]
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"Invalid timestamp format: {timestamp}")

    def test_structure_creation(self):
        """Test that database structure is created properly."""
        set_battery_percentage(42)
        from device_setting.SimulationEngine.db import DB
        
        self.assertIn(Constants.DEVICE_INSIGHTS.value, DB)
        self.assertIn(Constants.INSIGHTS.value, DB[Constants.DEVICE_INSIGHTS.value])
        self.assertIn(Constants.BATTERY.value, DB[Constants.DEVICE_INSIGHTS.value][Constants.INSIGHTS.value])

    def test_error_handling_missing_database(self):
        """Test error handling when database is missing."""
        # Should handle gracefully and return empty dict
        insights = get_battery_insights()
        self.assertEqual(insights, {})


if __name__ == '__main__':
    unittest.main() 