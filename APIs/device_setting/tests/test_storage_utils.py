"""
Test storage utility functions
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from common_utils.base_case import BaseTestCaseWithErrorHandler

from device_setting.SimulationEngine.device_insight_utils.storage_utils import (
    set_storage_total_gb,
    set_storage_used_gb,
    set_storage_available_gb,
    set_storage_usage_breakdown,
    calculate_storage_percentage,
    get_storage_status,
    get_storage_insights,
    get_storage_total_gb,
    get_storage_used_gb,
    get_storage_available_gb,
    get_storage_usage_breakdown,
    set_storage_insights
)
from device_setting.SimulationEngine.db import load_state, DEFAULT_DB_PATH
from device_setting.SimulationEngine.utils import set_device_insight_field, get_device_insight_data
from device_setting.SimulationEngine.db import DB
from device_setting.SimulationEngine.enums import Constants


class TestStorageUtils(BaseTestCaseWithErrorHandler):
    """Test cases for storage utility functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset the database to defaults before each test
        load_state(DEFAULT_DB_PATH)

    def tearDown(self):
        """Clean up after each test method."""
        # Reset the database to defaults after each test
        load_state(DEFAULT_DB_PATH)

    def _clear_storage_data(self):
        """Helper method to clear storage data for testing defaults."""
        if (Constants.DEVICE_INSIGHTS.value in DB and 
            Constants.INSIGHTS.value in DB[Constants.DEVICE_INSIGHTS.value] and
            Constants.STORAGE.value in DB[Constants.DEVICE_INSIGHTS.value][Constants.INSIGHTS.value]):
            DB[Constants.DEVICE_INSIGHTS.value][Constants.INSIGHTS.value].pop(Constants.STORAGE.value, None)

    def test_set_and_get_storage_total_gb(self):
        """Test setting and getting total storage capacity."""
        set_storage_total_gb(256)
        self.assertEqual(get_storage_total_gb(), 256)
        
        # Check DB directly
        storage = DB[Constants.DEVICE_INSIGHTS.value][Constants.INSIGHTS.value][Constants.STORAGE.value]
        self.assertEqual(storage[Constants.TOTAL_GB.value], 256)
        self.assertIn(Constants.LAST_UPDATED.value, storage)

    def test_set_storage_total_gb_invalid(self):
        """Test setting total storage with invalid values."""
        self.assert_error_behavior(set_storage_total_gb, ValueError, "Total storage must be a non-negative integer", None, -1)
        self.assert_error_behavior(set_storage_total_gb, ValueError, "Total storage must be a non-negative integer", None, "256")
        self.assert_error_behavior(set_storage_total_gb, ValueError, "Total storage must be a non-negative integer", None, None)

    def test_set_storage_total_gb_int_conversion(self):
        """Test that integers are stored as integers."""
        set_storage_total_gb(128)
        self.assertEqual(get_storage_total_gb(), 128)

    def test_get_storage_total_gb_default(self):
        """Test getting total storage when not set."""
        # Clear storage data to test default behavior
        self._clear_storage_data()
        self.assertEqual(get_storage_total_gb(), 0)

    def test_set_and_get_storage_used_gb(self):
        """Test setting and getting used storage."""
        set_storage_used_gb(128)
        self.assertEqual(get_storage_used_gb(), 128)

    def test_set_storage_used_gb_invalid(self):
        """Test setting used storage with invalid values."""
        self.assert_error_behavior(set_storage_used_gb, ValueError, "Used storage must be a non-negative integer", None, -1)
        self.assert_error_behavior(set_storage_used_gb, ValueError, "Used storage must be a non-negative integer", None, "128")
        self.assert_error_behavior(set_storage_used_gb, ValueError, "Used storage must be a non-negative integer", None, None)

    def test_get_storage_used_gb_default(self):
        """Test getting used storage when not set."""
        # Clear storage data to test default behavior
        self._clear_storage_data()
        self.assertEqual(get_storage_used_gb(), 0)

    def test_set_and_get_storage_available_gb(self):
        """Test setting and getting available storage."""
        set_storage_available_gb(127)
        self.assertEqual(get_storage_available_gb(), 127)

    def test_set_storage_available_gb_invalid(self):
        """Test setting available storage with invalid values."""
        self.assert_error_behavior(set_storage_available_gb, ValueError, "Available storage must be a non-negative integer", None, -1)
        self.assert_error_behavior(set_storage_available_gb, ValueError, "Available storage must be a non-negative integer", None, "127")
        self.assert_error_behavior(set_storage_available_gb, ValueError, "Available storage must be a non-negative integer", None, None)

    def test_get_storage_available_gb_default(self):
        """Test getting available storage when not set."""
        # Clear storage data to test default behavior
        self._clear_storage_data()
        self.assertEqual(get_storage_available_gb(), 0)

    def test_set_and_get_storage_usage_breakdown(self):
        """Test setting and getting storage usage breakdown."""
        breakdown = {
            "apps": 45,
            "photos": 23,
            "videos": 15,
            "documents": 8,
            "system": 12,
            "other": 5
        }
        set_storage_usage_breakdown(breakdown)
        retrieved_breakdown = get_storage_usage_breakdown()
        self.assertEqual(retrieved_breakdown, breakdown)

    def test_set_storage_usage_breakdown_invalid(self):
        """Test setting usage breakdown with invalid values."""
        self.assert_error_behavior(set_storage_usage_breakdown, ValueError, "Usage breakdown must be a dictionary", None, "not a dict")
        self.assert_error_behavior(set_storage_usage_breakdown, ValueError, "Usage breakdown must be a dictionary", None, None)

    def test_get_storage_usage_breakdown_default(self):
        """Test getting usage breakdown when not set."""
        # Clear storage data to test default behavior
        self._clear_storage_data()
        self.assertEqual(get_storage_usage_breakdown(), {})

    def test_set_storage_insights_all_fields(self):
        """Test setting all storage insights at once."""
        insights_data = {
            "total_gb": 512,
            "used_gb": 256,
            "available_gb": 256,
            "usage_breakdown": {
                "apps": 100,
                "photos": 80,
                "videos": 50,
                "system": 20,
                "other": 6
            }
        }
        
        set_storage_insights(**insights_data)
        
        # Verify all insights were set correctly
        self.assertEqual(get_storage_total_gb(), insights_data["total_gb"])
        self.assertEqual(get_storage_used_gb(), insights_data["used_gb"])
        self.assertEqual(get_storage_available_gb(), insights_data["available_gb"])
        self.assertEqual(get_storage_usage_breakdown(), insights_data["usage_breakdown"])

    def test_set_storage_insights_partial_fields(self):
        """Test setting only some storage insights."""
        # Clear storage data first
        self._clear_storage_data()
        
        set_storage_insights(
            total_gb=256,
            used_gb=128
        )
        
        # Verify only specified insights were set
        self.assertEqual(get_storage_total_gb(), 256)
        self.assertEqual(get_storage_used_gb(), 128)
        
        # Verify other insights remain at defaults
        self.assertEqual(get_storage_available_gb(), 0)
        self.assertEqual(get_storage_usage_breakdown(), {})

    def test_set_storage_insights_validation(self):
        """Test validation in set_storage_insights."""
        # Test invalid total_gb
        self.assert_error_behavior(set_storage_insights, ValueError, "Total storage must be a non-negative integer", None, total_gb=-10)
        
        # Test invalid used_gb
        self.assert_error_behavior(set_storage_insights, ValueError, "Used storage must be a non-negative integer", None, used_gb=-5)
        
        # Test invalid available_gb
        self.assert_error_behavior(set_storage_insights, ValueError, "Available storage must be a non-negative integer", None, available_gb=-1)
        
        # Test invalid usage_breakdown
        self.assert_error_behavior(set_storage_insights, ValueError, "Usage breakdown must be a dictionary", None, usage_breakdown="not a dict")

    def test_get_storage_insights_with_data(self):
        """Test getting storage insights when data exists."""
        # Set up test data
        DB[Constants.DEVICE_INSIGHTS.value] = {
            Constants.INSIGHTS.value: {
                Constants.STORAGE.value: {
                    Constants.TOTAL_GB.value: 256,
                    Constants.USED_GB.value: 128,
                    Constants.AVAILABLE_GB.value: 128,
                    Constants.USAGE_BREAKDOWN.value: {"apps": 50, "photos": 30},
                    Constants.LAST_UPDATED.value: "2023-01-01T00:00:00Z"
                }
            }
        }
        
        result = get_storage_insights()
        
        # Verify all insights are returned
        expected_keys = {
            Constants.TOTAL_GB,
            Constants.USED_GB,
            Constants.AVAILABLE_GB,
            Constants.USAGE_BREAKDOWN,
            Constants.LAST_UPDATED
        }
        self.assertEqual(set(result.keys()), expected_keys)

    def test_get_storage_insights_no_data(self):
        """Test getting storage insights when no data exists."""
        # Clear storage data to test default behavior
        self._clear_storage_data()
        result = get_storage_insights()
        self.assertEqual(result, {})

    def test_calculate_storage_percentage_normal(self):
        """Test storage percentage calculation with normal values."""
        set_storage_insights(total_gb=100, used_gb=50)
        percentage = calculate_storage_percentage()
        self.assertEqual(percentage, 50.0)

    def test_calculate_storage_percentage_full(self):
        """Test storage percentage calculation when full."""
        set_storage_insights(total_gb=100, used_gb=100)
        percentage = calculate_storage_percentage()
        self.assertEqual(percentage, 100.0)

    def test_calculate_storage_percentage_empty(self):
        """Test storage percentage calculation when empty."""
        set_storage_insights(total_gb=100, used_gb=0)
        percentage = calculate_storage_percentage()
        self.assertEqual(percentage, 0.0)

    def test_calculate_storage_percentage_zero_total(self):
        """Test storage percentage calculation with zero total."""
        set_storage_insights(total_gb=0, used_gb=50)
        percentage = calculate_storage_percentage()
        self.assertEqual(percentage, 0.0)

    def test_calculate_storage_percentage_no_data(self):
        """Test storage percentage calculation with no data."""
        # Clear storage data to test default behavior
        self._clear_storage_data()
        percentage = calculate_storage_percentage()
        self.assertEqual(percentage, 0.0)

    def test_get_storage_status_normal(self):
        """Test storage status for normal usage."""
        set_storage_insights(total_gb=100, used_gb=30)
        status = get_storage_status()
        self.assertEqual(status, "Normal storage usage")

    def test_get_storage_status_moderate(self):
        """Test storage status for moderate usage."""
        set_storage_insights(total_gb=100, used_gb=70)
        status = get_storage_status()
        self.assertEqual(status, "Moderate storage usage")

    def test_get_storage_status_low(self):
        """Test storage status for low storage."""
        set_storage_insights(total_gb=100, used_gb=85)
        status = get_storage_status()
        self.assertEqual(status, "Low storage")

    def test_get_storage_status_critical(self):
        """Test storage status for critical storage."""
        set_storage_insights(total_gb=100, used_gb=95)
        status = get_storage_status()
        self.assertEqual(status, "Critical storage")

    def test_get_storage_status_boundary_values(self):
        """Test storage status boundary values."""
        # Test boundary at 60%
        set_storage_insights(total_gb=100, used_gb=60)
        status = get_storage_status()
        self.assertEqual(status, "Moderate storage usage")
        
        # Test boundary at 80%
        set_storage_insights(total_gb=100, used_gb=80)
        status = get_storage_status()
        self.assertEqual(status, "Low storage")
        
        # Test boundary at 90%
        set_storage_insights(total_gb=100, used_gb=90)
        status = get_storage_status()
        self.assertEqual(status, "Critical storage")

    def test_get_storage_status_no_data(self):
        """Test storage status with no data."""
        # Clear storage data to test default behavior
        self._clear_storage_data()
        status = get_storage_status()
        self.assertEqual(status, "Normal storage usage")

    def test_database_structure_creation(self):
        """Test that database structure is created correctly."""
        # Start with empty database
        DB.clear()
        
        set_storage_total_gb(256)
        
        # Verify structure was created
        self.assertIn(Constants.DEVICE_INSIGHTS.value, DB)
        self.assertIn(Constants.INSIGHTS.value, DB[Constants.DEVICE_INSIGHTS.value])
        self.assertIn(Constants.STORAGE.value, DB[Constants.DEVICE_INSIGHTS.value][Constants.INSIGHTS.value])

    def test_precision_handling(self):
        """Test handling of integer values."""
        set_storage_used_gb(123)
        self.assertEqual(get_storage_used_gb(), 123)
        
        set_storage_total_gb(1000)
        self.assertEqual(get_storage_total_gb(), 1000)

    def test_large_values(self):
        """Test handling of large storage values."""
        set_storage_insights(
            total_gb=1000000,
            used_gb=500000,
            available_gb=500000
        )
        
        self.assertEqual(get_storage_total_gb(), 1000000)
        self.assertEqual(get_storage_used_gb(), 500000)
        self.assertEqual(get_storage_available_gb(), 500000)
        
        percentage = calculate_storage_percentage()
        self.assertEqual(percentage, 50.0)


if __name__ == '__main__':
    unittest.main() 