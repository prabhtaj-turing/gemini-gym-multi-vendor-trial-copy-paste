"""
Comprehensive tests for the device_setting porting functionality.
Tests validation, error handling, and data transformation.
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add the project root to the path to import Scripts package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from Scripts.porting.port_device_setting import port_device_setting_db, normalize_timestamp, transform_device_settings, transform_installed_apps, transform_device_insights


class TestDeviceSettingPorting:
    """Test suite for device_setting porting functionality."""
    
    def get_valid_base_data(self):
        """Get a valid base device setting structure for testing."""
        return {
            "device_settings": {
                "device_id": "test_device_001",
                "settings": {
                    "WIFI": {
                        "on_or_off": "on",
                        "last_updated": "2025-08-05T17:13:00Z"
                    },
                    "BLUETOOTH": {
                        "on_or_off": "off",
                        "last_updated": "2025-08-05T17:13:00Z"
                    },
                    "BRIGHTNESS": {
                        "percentage_value": 50,
                        "last_updated": "2025-08-05T17:13:00Z"
                    }
                }
            },
            "installed_apps": {
                "device_id": "test_device_001",
                "apps": {
                    "Gmail": {
                        "notifications": {
                            "value": "on",
                            "last_updated": "2025-08-05T17:13:00Z"
                        }
                    }
                }
            },
            "device_insights": {
                "device_id": "test_device_001",
                "insights": {
                    "BATTERY": {
                        "percentage": 80,
                        "charging_status": "charging",
                        "estimated_time_remaining": "2 hours",
                        "last_updated": "2025-08-05T17:13:00Z"
                    }
                }
            }
        }

    def test_brightness_percentage_over_100_transformation(self):
        """Test that BRIGHTNESS percentage_value > 100 gets clamped to 100."""
        data = self.get_valid_base_data()
        data["device_settings"]["settings"]["BRIGHTNESS"]["percentage_value"] = 101
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["settings"]["BRIGHTNESS"]["percentage_value"] == 100
        assert "Validation successful" in message

    def test_media_volume_percentage_under_0_transformation(self):
        """Test that MEDIA_VOLUME percentage_value < 0 gets clamped to 0."""
        data = self.get_valid_base_data()
        data["device_settings"]["settings"]["MEDIA_VOLUME"] = {
            "percentage_value": -5,
            "last_updated": "2025-08-05T17:13:00Z"
        }
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["settings"]["MEDIA_VOLUME"]["percentage_value"] == 0
        assert "Validation successful" in message

    def test_invalid_on_or_off_value_transformation(self):
        """Test that invalid on_or_off values get transformed to 'off'."""
        data = self.get_valid_base_data()
        data["device_settings"]["settings"]["WIFI"]["on_or_off"] = "invalid"
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["settings"]["WIFI"]["on_or_off"] == "off"
        assert "Validation successful" in message

    def test_uppercase_on_or_off_transformation(self):
        """Test that uppercase on_or_off values get normalized properly."""
        data = self.get_valid_base_data()
        data["device_settings"]["settings"]["WIFI"]["on_or_off"] = "ON"
        data["device_settings"]["settings"]["BLUETOOTH"]["on_or_off"] = "OFF"
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["settings"]["WIFI"]["on_or_off"] == "on"
        assert result["device_settings"]["settings"]["BLUETOOTH"]["on_or_off"] == "off"
        assert "Validation successful" in message

    def test_invalid_charging_status_transformation(self):
        """Test that invalid charging_status values get transformed to 'not_charging'."""
        data = self.get_valid_base_data()
        data["device_insights"]["insights"]["BATTERY"]["charging_status"] = "maybe_charging"
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_insights"]["insights"]["BATTERY"]["charging_status"] == "not_charging"
        assert "Validation successful" in message

    def test_uppercase_charging_status_transformation(self):
        """Test that uppercase charging_status values get normalized properly."""
        data = self.get_valid_base_data()
        data["device_insights"]["insights"]["BATTERY"]["charging_status"] = "CHARGING"
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_insights"]["insights"]["BATTERY"]["charging_status"] == "charging"
        assert "Validation successful" in message

    def test_timestamp_format_consistency_validation(self):
        """Test that timestamps are normalized to ISO format with Z suffix."""
        data = self.get_valid_base_data()
        
        # Test various timestamp formats across different sections
        # Device settings timestamps
        data["device_settings"]["settings"]["WIFI"]["last_updated"] = "2025-08-05T17:13:00"  # No timezone
        data["device_settings"]["settings"]["BLUETOOTH"]["last_updated"] = "2025-08-05T17:13:00+00:00"  # UTC offset
        data["device_settings"]["settings"]["BRIGHTNESS"]["last_updated"] = "2025-08-05T17:13:00Z"  # Already correct
        
        # Add media volume with different timezone
        data["device_settings"]["settings"]["MEDIA_VOLUME"] = {
            "percentage_value": 50,
            "last_updated": "2025-08-05T17:13:00+05:00"  # Non-UTC timezone
        }
        
        # Installed apps timestamps
        data["installed_apps"]["apps"]["Gmail"]["notifications"]["last_updated"] = "2025-08-05T17:13:00-03:00"  # Negative offset
        
        # Add another app with different format
        data["installed_apps"]["apps"]["Slack"] = {
            "notifications": {
                "value": "on",
                "last_updated": "2025-08-05T17:13:00.123Z"  # With milliseconds
            }
        }
        
        # Device insights timestamps
        data["device_insights"]["insights"]["BATTERY"]["last_updated"] = "2025-08-05T17:13:00+02:00"  # Different offset
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # All timestamps should be normalized to Z format
        settings = result["device_settings"]["settings"]
        assert settings["WIFI"]["last_updated"].endswith("Z")
        assert settings["BLUETOOTH"]["last_updated"].endswith("Z")
        assert settings["BRIGHTNESS"]["last_updated"].endswith("Z")
        assert settings["MEDIA_VOLUME"]["last_updated"].endswith("Z")
        
        # Verify specific expected transformations
        assert settings["BLUETOOTH"]["last_updated"] == "2025-08-05T17:13:00Z"  # +00:00 → Z
        assert settings["BRIGHTNESS"]["last_updated"] == "2025-08-05T17:13:00Z"  # Already Z
        
        # App notifications timestamps
        apps = result["installed_apps"]["apps"]
        assert apps["Gmail"]["notifications"]["last_updated"].endswith("Z")
        assert apps["Slack"]["notifications"]["last_updated"].endswith("Z")
        
        # Device insights timestamps
        insights = result["device_insights"]["insights"]
        assert insights["BATTERY"]["last_updated"].endswith("Z")
        
        # Basic validation that all timestamps end with Z
        # (The actual format validation should be done in the porting function)
        
        assert "Validation successful" in message

    def test_timestamp_edge_cases(self):
        """Test timestamp normalization with edge cases and invalid formats."""
        data = self.get_valid_base_data()
        
        # Test empty and invalid timestamps
        data["device_settings"]["settings"]["WIFI"]["last_updated"] = ""  # Empty string
        data["device_settings"]["settings"]["BLUETOOTH"]["last_updated"] = "invalid_timestamp"  # Invalid format
        
        # Test various valid formats that should be normalized
        data["device_settings"]["settings"]["BRIGHTNESS"]["last_updated"] = "2025-08-05T17:13:00.456789Z"  # High precision
        
        data["installed_apps"]["apps"]["Gmail"]["notifications"]["last_updated"] = "2025-12-31T23:59:59+00:00"  # Edge date
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        
        settings = result["device_settings"]["settings"]
        
        # Empty and invalid timestamps should get current timestamp with Z
        assert settings["WIFI"]["last_updated"].endswith("Z")
        assert settings["BLUETOOTH"]["last_updated"].endswith("Z")
        
        # Valid timestamps should be preserved/normalized
        assert settings["BRIGHTNESS"]["last_updated"].endswith("Z")
        assert "2025-08-05T17:13:00" in settings["BRIGHTNESS"]["last_updated"]
        
        # Edge date should be normalized
        gmail_timestamp = result["installed_apps"]["apps"]["Gmail"]["notifications"]["last_updated"]
        assert gmail_timestamp == "2025-12-31T23:59:59Z"
        
        assert "Validation successful" in message

    def test_timestamp_normalization_function_edge_cases(self):
        """Test the normalize_timestamp function directly with edge cases."""
        
        # Test cases with expected behavior
        test_cases = [
            # (input, should_end_with_Z, specific_expected)
            ("2025-08-05T17:13:00Z", True, "2025-08-05T17:13:00Z"),  # Already correct
            ("2025-08-05T17:13:00+00:00", True, "2025-08-05T17:13:00Z"),  # UTC offset to Z
            ("2025-08-05T17:13:00", True, None),  # No timezone, should get Z
            ("", True, None),  # Empty, should get current time with Z
            ("invalid", True, None),  # Invalid, should get current time with Z
            (None, True, None),  # None, should get current time with Z
        ]
        
        for input_ts, should_end_with_z, expected in test_cases:
            result = normalize_timestamp(input_ts)
            
            if should_end_with_z:
                assert result.endswith("Z"), f"Expected Z suffix for input '{input_ts}', got '{result}'"
            
            if expected:
                assert result == expected, f"Expected '{expected}' for input '{input_ts}', got '{result}'"
            
            # Basic check that result has Z suffix
            # (Detailed format validation should be in the porting function)
            assert len(result) >= 19, f"Timestamp too short for input '{input_ts}': '{result}'"

    def test_unknown_setting_type_filtered_out(self):
        """Test that unknown setting types are filtered out and not included in ported json."""
        data = self.get_valid_base_data()
        data["device_settings"]["settings"]["UNKNOWN_SETTING"] = {
            "on_or_off": "on",
            "last_updated": "2025-08-05T17:13:00Z"
        }
        data["device_settings"]["settings"]["INVALID_VOLUME"] = {
            "percentage_value": 50,
            "last_updated": "2025-08-05T17:13:00Z"
        }
        
        result, message = port_device_setting_db(json.dumps(data))
        
        # Should succeed but unknown settings should be filtered out
        assert result is not None, f"Porting failed: {message}"
        assert "UNKNOWN_SETTING" not in result["device_settings"]["settings"]
        assert "INVALID_VOLUME" not in result["device_settings"]["settings"]
        # Known settings should still be present
        assert "WIFI" in result["device_settings"]["settings"]
        assert "BLUETOOTH" in result["device_settings"]["settings"]
        assert "BRIGHTNESS" in result["device_settings"]["settings"]
        assert "Validation successful" in message

    def test_bluetooth_uppercase_on_or_off_transformation(self):
        """Test that BLUETOOTH on_or_off 'ON' gets normalized to 'on'."""
        data = self.get_valid_base_data()
        data["device_settings"]["settings"]["BLUETOOTH"]["on_or_off"] = "ON"
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["settings"]["BLUETOOTH"]["on_or_off"] == "on"
        assert "Validation successful" in message

    def test_bluetooth_invalid_value_transformation(self):
        """Test that BLUETOOTH invalid on_or_off values get transformed to 'off'."""
        data = self.get_valid_base_data()
        
        # Test various invalid values
        invalid_values = ["invalid", "maybe", "sometimes", "auto", "1.5", "null", "undefined"]
        
        for invalid_value in invalid_values:
            data["device_settings"]["settings"]["BLUETOOTH"]["on_or_off"] = invalid_value
            
            result, message = port_device_setting_db(json.dumps(data))
            
            assert result is not None, f"Porting failed for '{invalid_value}': {message}"
            assert result["device_settings"]["settings"]["BLUETOOTH"]["on_or_off"] == "off", \
                f"Expected 'off' for invalid value '{invalid_value}', got '{result['device_settings']['settings']['BLUETOOTH']['on_or_off']}'"
            assert "Validation successful" in message

    def test_device_id_consistency_across_sections(self):
        """Test that device_id is consistent across all sections."""
        data = self.get_valid_base_data()
        device_id = "consistent_device_123"
        
        data["device_settings"]["device_id"] = device_id
        data["installed_apps"]["device_id"] = device_id
        data["device_insights"]["device_id"] = device_id
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["device_id"] == device_id
        assert result["installed_apps"]["device_id"] == device_id
        assert result["device_insights"]["device_id"] == device_id

    def test_invalid_notification_value_transformation(self):
        """Test that invalid notification values get transformed to 'off'."""
        data = self.get_valid_base_data()
        data["installed_apps"]["apps"]["Gmail"]["notifications"]["value"] = "maybe"
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["installed_apps"]["apps"]["Gmail"]["notifications"]["value"] == "off"
        assert "Validation successful" in message

    def test_missing_device_id_handling(self):
        """Test handling of missing device_id fields."""
        data = self.get_valid_base_data()
        del data["device_settings"]["device_id"]
        del data["installed_apps"]["device_id"] 
        del data["device_insights"]["device_id"]
        
        result, message = port_device_setting_db(json.dumps(data))
        
        # Should add default device_id to all sections
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["device_id"] == "google_pixel_9_a"
        assert result["installed_apps"]["device_id"] == "google_pixel_9_a"
        assert result["device_insights"]["device_id"] == "google_pixel_9_a"
        assert "Validation successful" in message

    def test_inconsistent_device_id_handling(self):
        """Test handling of inconsistent device_id fields across sections."""
        data = self.get_valid_base_data()
        data["device_settings"]["device_id"] = "primary_device_123"
        data["installed_apps"]["device_id"] = "different_device_456"
        data["device_insights"]["device_id"] = "another_device_789"
        
        result, message = port_device_setting_db(json.dumps(data))
        
        # Should use device_settings device_id for all sections
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["device_id"] == "primary_device_123"
        assert result["installed_apps"]["device_id"] == "primary_device_123"
        assert result["device_insights"]["device_id"] == "primary_device_123"
        assert "Validation successful" in message

    def test_partial_missing_device_id_handling(self):
        """Test handling when only some sections are missing device_id."""
        data = self.get_valid_base_data()
        data["device_settings"]["device_id"] = "main_device_999"
        del data["installed_apps"]["device_id"]  # Missing in apps
        del data["device_insights"]["device_id"]  # Missing in insights
        
        result, message = port_device_setting_db(json.dumps(data))
        
        # Should use device_settings device_id for all sections
        assert result is not None, f"Porting failed: {message}"
        assert result["device_settings"]["device_id"] == "main_device_999"
        assert result["installed_apps"]["device_id"] == "main_device_999"
        assert result["device_insights"]["device_id"] == "main_device_999"
        assert "Validation successful" in message

    def test_empty_json_structure(self):
        """Test passing completely empty {} JSON returns valid empty DB structure."""
        empty_data = "{}"
        
        result, message = port_device_setting_db(empty_data)
        
        assert result is not None, f"Empty JSON processing failed: {message}"
        assert "device_settings" in result
        assert "installed_apps" in result
        assert "device_insights" in result
        # Should get default device_id for all sections
        assert result["device_settings"]["device_id"] == "google_pixel_9_a"
        assert result["installed_apps"]["device_id"] == "google_pixel_9_a"
        assert result["device_insights"]["device_id"] == "google_pixel_9_a"
        assert "Validation successful" in message

    def test_corrupted_json_parsing_error(self):
        """Test that corrupted/invalid JSON string catches JSON parsing error."""
        corrupted_json = '{"device_settings": {"invalid": json}'
        
        result, message = port_device_setting_db(corrupted_json)
        
        assert result is None
        assert "Invalid JSON" in message

    def test_battery_percentage_over_100_transformation(self):
        """Test that battery percentage > 100 gets clamped to 100."""
        data = self.get_valid_base_data()
        data["device_insights"]["insights"]["BATTERY"]["percentage"] = 150
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_insights"]["insights"]["BATTERY"]["percentage"] == 100

    def test_battery_percentage_under_0_transformation(self):
        """Test that battery percentage < 0 gets clamped to 0."""
        data = self.get_valid_base_data()
        data["device_insights"]["insights"]["BATTERY"]["percentage"] = -10
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        assert result["device_insights"]["insights"]["BATTERY"]["percentage"] == 0

    def test_charging_status_normalization(self):
        """Test charging status normalization from various formats."""
        data = self.get_valid_base_data()
        
        # Test various charging status inputs
        test_cases = [
            ("charging", "charging"),
            ("CHARGING", "charging"),
            ("charge", "charging"),
            ("not charging", "not_charging"),
            ("NOT_CHARGING", "not_charging"),
            ("discharging", "not_charging")
        ]
        
        for input_status, expected_output in test_cases:
            data["device_insights"]["insights"]["BATTERY"]["charging_status"] = input_status
            result, message = port_device_setting_db(json.dumps(data))
            
            assert result is not None, f"Porting failed for {input_status}: {message}"
            assert result["device_insights"]["insights"]["BATTERY"]["charging_status"] == expected_output

    def test_notification_value_normalization(self):
        """Test notification value normalization from various formats."""
        data = self.get_valid_base_data()
        
        # Test various notification value inputs
        test_cases = [
            ("ON", "on"),
            ("True", "on"),
            ("1", "on"),
            ("yes", "on"),
            ("OFF", "off"),
            ("False", "off"),
            ("0", "off"),
            ("no", "off")
        ]
        
        for input_value, expected_output in test_cases:
            data["installed_apps"]["apps"]["Gmail"]["notifications"]["value"] = input_value
            result, message = port_device_setting_db(json.dumps(data))
            
            assert result is not None, f"Porting failed for {input_value}: {message}"
            assert result["installed_apps"]["apps"]["Gmail"]["notifications"]["value"] == expected_output

    def test_timestamp_normalization_function(self):
        """Test the normalize_timestamp function with various input formats."""
        test_cases = [
            ("2025-08-05T17:13:00Z", "2025-08-05T17:13:00Z"),  # Already correct
            ("2025-08-05T17:13:00+00:00", "2025-08-05T17:13:00Z"),  # UTC offset
        ]
        
        for input_ts, expected in test_cases:
            result = normalize_timestamp(input_ts)
            
            if isinstance(expected, str):
                assert result == expected
            else:  # expected is True, meaning we just check it ends with Z
                assert result.endswith("Z")
                assert len(result) >= 19  # Minimum ISO format length

        # Test empty string and None cases
        result_empty = normalize_timestamp("")
        result_none = normalize_timestamp(None)
        assert result_empty.endswith("Z")
        assert result_none.endswith("Z")

    def test_transform_functions_with_none_input(self):
        """Test transformation functions handle None/empty inputs gracefully."""
        assert transform_device_settings(None) == {}
        assert transform_device_settings({}) == {}
        
        assert transform_installed_apps(None) == {}
        assert transform_installed_apps({}) == {}
        
        assert transform_device_insights(None) == {}
        assert transform_device_insights({}) == {}

    def test_complex_nested_data_transformation(self):
        """Test complex nested data with multiple settings requiring transformation."""
        data = {
            "device_settings": {
                "device_id": "complex_test_device",
                "settings": {
                    "BRIGHTNESS": {"percentage_value": 101, "last_updated": "2025-08-05T17:13:00"},
                    "MEDIA_VOLUME": {"percentage_value": -10, "last_updated": "2025-08-05T17:13:00+05:00"},
                    "WIFI": {"on_or_off": "TRUE", "last_updated": "2025-08-05T17:13:00Z"},
                    "BLUETOOTH": {"on_or_off": "FALSE", "last_updated": ""}
                }
            },
            "installed_apps": {
                "device_id": "complex_test_device",
                "apps": {
                    "App1": {"notifications": {"value": "YES", "last_updated": "2025-08-05T17:13:00"}},
                    "App2": {"notifications": {"value": "0", "last_updated": "2025-08-05T17:13:00Z"}}
                }
            },
            "device_insights": {
                "device_id": "complex_test_device",
                "insights": {
                    "BATTERY": {
                        "percentage": 101,
                        "charging_status": "CHARGE",
                        "last_updated": "2025-08-05T17:13:00"
                    }
                }
            }
        }
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Complex transformation failed: {message}"
        
        # Verify transformations
        settings = result["device_settings"]["settings"]
        assert settings["BRIGHTNESS"]["percentage_value"] == 100  # Clamped from 101
        assert settings["MEDIA_VOLUME"]["percentage_value"] == 0   # Clamped from -10
        assert settings["WIFI"]["on_or_off"] == "on"             # Normalized from TRUE
        assert settings["BLUETOOTH"]["on_or_off"] == "off"        # Normalized from FALSE
        
        # All timestamps should end with Z
        for setting in settings.values():
            assert setting["last_updated"].endswith("Z")
        
        # Verify app notifications
        apps = result["installed_apps"]["apps"]
        assert apps["App1"]["notifications"]["value"] == "on"     # Normalized from YES
        assert apps["App2"]["notifications"]["value"] == "off"    # Normalized from 0
        
        # Verify insights
        battery = result["device_insights"]["insights"]["BATTERY"]
        assert battery["percentage"] == 100                       # Clamped from 101
        assert battery["charging_status"] == "charging"           # Normalized from CHARGE

    def test_unknown_insight_type_filtered_out(self):
        """Test that unknown insight types are filtered out and not included in ported json."""
        data = self.get_valid_base_data()
        data["device_insights"]["insights"]["UNKNOWN_INSIGHT"] = {
            "percentage": 50,
            "last_updated": "2025-08-05T17:13:00Z"
        }
        data["device_insights"]["insights"]["INVALID_METRIC"] = {
            "value": "some_value",
            "last_updated": "2025-08-05T17:13:00Z"
        }
        
        result, message = port_device_setting_db(json.dumps(data))
        
        # Should succeed but unknown insights should be filtered out
        assert result is not None, f"Porting failed: {message}"
        assert "UNKNOWN_INSIGHT" not in result["device_insights"]["insights"]
        assert "INVALID_METRIC" not in result["device_insights"]["insights"]
        # Known insights should still be present
        assert "BATTERY" in result["device_insights"]["insights"]
        assert "Validation successful" in message

    def test_mixed_valid_and_invalid_settings(self):
        """Test filtering works correctly when mix of valid and invalid settings are provided."""
        data = {
            "device_settings": {
                "device_id": "test_device_mixed",
                "settings": {
                    "WIFI": {"on_or_off": "on", "last_updated": "2025-08-05T17:13:00Z"},  # Valid
                    "BLUETOOTH": {"on_or_off": "off", "last_updated": "2025-08-05T17:13:00Z"},  # Valid
                    "UNKNOWN_SETTING": {"on_or_off": "on", "last_updated": "2025-08-05T17:13:00Z"},  # Invalid
                    "BRIGHTNESS": {"percentage_value": 75, "last_updated": "2025-08-05T17:13:00Z"},  # Valid
                    "FAKE_VOLUME": {"percentage_value": 50, "last_updated": "2025-08-05T17:13:00Z"}  # Invalid
                }
            },
            "installed_apps": {
                "device_id": "test_device_mixed",
                "apps": {
                    "Gmail": {"notifications": {"value": "on", "last_updated": "2025-08-05T17:13:00Z"}}  # Valid (apps are not filtered)
                }
            },
            "device_insights": {
                "device_id": "test_device_mixed",
                "insights": {
                    "BATTERY": {"percentage": 80, "charging_status": "charging", "last_updated": "2025-08-05T17:13:00Z"},  # Valid
                    "UNKNOWN_INSIGHT": {"value": "test", "last_updated": "2025-08-05T17:13:00Z"},  # Invalid
                    "STORAGE": {"total_gb": 256, "used_gb": 100, "last_updated": "2025-08-05T17:13:00Z"}  # Valid
                }
            }
        }
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # Valid settings should be present
        settings = result["device_settings"]["settings"]
        assert "WIFI" in settings
        assert "BLUETOOTH" in settings  
        assert "BRIGHTNESS" in settings
        
        # Invalid settings should be filtered out
        assert "UNKNOWN_SETTING" not in settings
        assert "FAKE_VOLUME" not in settings
        
        # Apps should not be filtered (any app name is valid)
        assert "Gmail" in result["installed_apps"]["apps"]
        
        # Valid insights should be present
        insights = result["device_insights"]["insights"]
        assert "BATTERY" in insights
        assert "STORAGE" in insights
        
        # Invalid insights should be filtered out
        assert "UNKNOWN_INSIGHT" not in insights
        
        assert "Validation successful" in message

    def test_empty_sections_after_filtering(self):
        """Test that sections with only invalid settings become empty after filtering."""
        data = {
            "device_settings": {
                "device_id": "test_device_empty",
                "settings": {
                    "UNKNOWN_SETTING_1": {"on_or_off": "on", "last_updated": "2025-08-05T17:13:00Z"},
                    "UNKNOWN_SETTING_2": {"percentage_value": 50, "last_updated": "2025-08-05T17:13:00Z"}
                }
            },
            "installed_apps": {
                "device_id": "test_device_empty",
                "apps": {}
            },
            "device_insights": {
                "device_id": "test_device_empty",
                "insights": {
                    "UNKNOWN_INSIGHT_1": {"value": "test", "last_updated": "2025-08-05T17:13:00Z"},
                    "UNKNOWN_INSIGHT_2": {"percentage": 50, "last_updated": "2025-08-05T17:13:00Z"}
                }
            }
        }
        
        result, message = port_device_setting_db(json.dumps(data))
        
        assert result is not None, f"Porting failed: {message}"
        
        # All sections should exist but settings/insights should be empty
        assert "device_settings" in result
        assert "settings" in result["device_settings"]
        assert len(result["device_settings"]["settings"]) == 0
        
        assert "device_insights" in result
        assert "insights" in result["device_insights"]
        assert len(result["device_insights"]["insights"]) == 0
        
        assert "Validation successful" in message


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
