"""
Smoke Tests for Device Setting API

Smoke tests verify that the basic functionality of the device_setting module is operational.
These tests are designed to catch fundamental issues that would prevent the system from working
at all, such as import failures, basic API function calls, and critical data flow.

Smoke tests should run quickly and cover the essential "happy path" scenarios to ensure
the system is ready for more comprehensive testing.
"""

import unittest
from typing import Dict, Any, List
from common_utils.base_case import BaseTestCaseWithErrorHandler
from device_setting.SimulationEngine.db import load_state, DEFAULT_DB_PATH


class TestSmoke(BaseTestCaseWithErrorHandler):
    """Smoke test suite for device_setting API to verify basic operational readiness."""

    def setUp(self):
        """Reset database to defaults before each test for proper isolation."""
        load_state(DEFAULT_DB_PATH)

    # PACKAGE INSTALL AND IMPORT TESTS

    def test_package_import_basic(self):
        """
        Smoke test: Verify the main device_setting package can be imported.

        This test ensures that the package is properly installed and all dependencies
        are available. Import failures here indicate fundamental setup issues.
        """
        import device_setting

        # Verify the package has the expected structure
        self.assertTrue(
            hasattr(device_setting, "__version__")
            or hasattr(device_setting, "__file__")
        )

        # Verify package can be used (has callable attributes)
        package_attributes = dir(device_setting)
        self.assertGreater(
            len(package_attributes), 0, "Package should have accessible attributes"
        )

    def test_core_modules_import(self):
        """
        Smoke test: Verify all core modules can be imported without errors.

        This test checks that the internal module structure is intact and all
        dependencies between modules are properly resolved.
        """
        # Test main API modules
        from device_setting import device_setting
        from device_setting import app_settings

        # Test simulation engine components
        from device_setting.SimulationEngine import enums
        from device_setting.SimulationEngine import models
        from device_setting.SimulationEngine import utils
        from device_setting.SimulationEngine import db

        # Verify modules have expected content
        self.assertTrue(hasattr(device_setting, "open"))
        self.assertTrue(hasattr(device_setting, "get"))
        self.assertTrue(hasattr(app_settings, "get_installed_apps"))
        self.assertTrue(hasattr(utils, "get_setting"))
        self.assertTrue(hasattr(db, "load_state"))

    def test_function_imports_from_main_package(self):
        """
        Smoke test: Verify all main API functions can be imported from the package root.

        This ensures the public API is accessible and the function mapping is working correctly.
        """
        from device_setting import (
            open,
            get,
            on,
            off,
            mute,
            unmute,
            adjust_volume,
            set_volume,
            get_device_insights,
            get_installed_apps,
            get_app_notification_status,
            set_app_notification_status,
        )

        # Verify all functions are callable
        functions_to_test = [
            open,
            get,
            on,
            off,
            mute,
            unmute,
            adjust_volume,
            set_volume,
            get_device_insights,
            get_installed_apps,
            get_app_notification_status,
            set_app_notification_status,
        ]

        for func in functions_to_test:
            self.assertTrue(
                callable(func), f"Function {func.__name__} should be callable"
            )

    # BASIC API USAGE TESTS

    def test_basic_settings_navigation_workflow(self):
        """
        Smoke test: Verify basic settings navigation functions work.

        Tests the open() function which is fundamental for navigating to settings pages.
        This ensures the basic UI navigation simulation is operational.
        """
        from device_setting import open

        # Test opening general settings
        result = open()
        self.assertIsInstance(result, dict, "open() should return a dictionary")
        self.assertIn("result", result, "Response should contain 'result' field")
        self.assertIn("card_id", result, "Response should contain 'card_id' field")
        self.assertIn(
            "action_card_content_passthrough",
            result,
            "Response should contain action card content",
        )

        # Test opening specific settings
        result_wifi = open("WIFI")
        self.assertIsInstance(
            result_wifi, dict, "open('WIFI') should return a dictionary"
        )
        self.assertIn(
            "result",
            result_wifi,
            "WIFI settings response should contain 'result' field",
        )
        self.assertIn(
            "wifi", result_wifi["result"].lower(), "Result should mention wifi settings"
        )

    def test_basic_setting_retrieval_workflow(self):
        """
        Smoke test: Verify basic setting retrieval functions work.

        Tests the get() function which is essential for reading current device state.
        This ensures the data retrieval mechanisms are operational.
        """
        from device_setting import get

        # Test getting a toggle setting
        result_wifi = get("WIFI")
        self.assertIsInstance(
            result_wifi, dict, "get('WIFI') should return a dictionary"
        )
        self.assertIn(
            "setting_type", result_wifi, "Response should contain 'setting_type' field"
        )
        self.assertEqual(
            result_wifi["setting_type"], "WIFI", "Setting type should match request"
        )
        self.assertIn(
            "on_or_off", result_wifi, "WIFI setting should have 'on_or_off' status"
        )
        self.assertIn(
            result_wifi["on_or_off"],
            ["on", "off"],
            "WIFI status should be 'on' or 'off'",
        )

        # Test getting a percentage setting
        result_battery = get("BATTERY")
        self.assertIsInstance(
            result_battery, dict, "get('BATTERY') should return a dictionary"
        )
        self.assertIn(
            "setting_type",
            result_battery,
            "Response should contain 'setting_type' field",
        )
        self.assertEqual(
            result_battery["setting_type"],
            "BATTERY",
            "Setting type should match request",
        )
        self.assertIn(
            "percentage_value", result_battery, "Battery should have 'percentage_value'"
        )
        self.assertIsInstance(
            result_battery["percentage_value"],
            int,
            "Battery percentage should be integer",
        )
        self.assertGreaterEqual(
            result_battery["percentage_value"], 0, "Battery percentage should be >= 0"
        )
        self.assertLessEqual(
            result_battery["percentage_value"],
            100,
            "Battery percentage should be <= 100",
        )

    def test_basic_setting_modification_workflow(self):
        """
        Smoke test: Verify basic setting modification functions work.

        Tests the on()/off() functions which are fundamental for changing device state.
        This ensures the data modification mechanisms are operational.
        """
        from device_setting import on, off, get

        # Test turning a setting on
        result_on = on("WIFI")
        self.assertIsInstance(result_on, dict, "on('WIFI') should return a dictionary")
        self.assertIn("result", result_on, "Response should contain 'result' field")
        self.assertIn("card_id", result_on, "Response should contain 'card_id' field")

        # Verify the setting actually changed by checking its status
        status_after_on = get("WIFI")
        self.assertEqual(
            status_after_on["on_or_off"],
            "on",
            "WIFI should be 'on' after calling on('WIFI')",
        )

        # Test turning a setting off
        result_off = off("WIFI")
        self.assertIsInstance(
            result_off, dict, "off('WIFI') should return a dictionary"
        )
        self.assertIn("result", result_off, "Response should contain 'result' field")

        # Verify the setting actually changed by checking its status
        status_after_off = get("WIFI")
        self.assertEqual(
            status_after_off["on_or_off"],
            "off",
            "WIFI should be 'off' after calling off('WIFI')",
        )

    def test_basic_volume_control_workflow(self):
        """
        Smoke test: Verify basic volume control functions work.

        Tests volume functions which are critical for audio management.
        This ensures the volume control subsystem is operational.
        """
        from device_setting import set_volume, get, mute, unmute

        # Test setting volume to a specific level
        result_set = set_volume(75, "MEDIA")
        self.assertIsInstance(
            result_set, dict, "set_volume() should return a dictionary"
        )
        self.assertIn("result", result_set, "Response should contain 'result' field")

        # Verify volume was actually set by retrieving it
        media_volume = get("MEDIA_VOLUME")
        self.assertIn(
            "percentage_value",
            media_volume,
            "Media volume should have percentage_value",
        )
        self.assertEqual(
            media_volume["percentage_value"], 75, "Media volume should be set to 75%"
        )

        # Test muting
        result_mute = mute("MEDIA")
        self.assertIsInstance(result_mute, dict, "mute() should return a dictionary")
        self.assertIn(
            "result", result_mute, "Mute response should contain 'result' field"
        )

        # Verify volume was muted
        muted_volume = get("MEDIA_VOLUME")
        self.assertEqual(
            muted_volume["percentage_value"], 0, "Media volume should be 0 after muting"
        )

        # Test unmuting
        result_unmute = unmute("MEDIA")
        self.assertIsInstance(
            result_unmute, dict, "unmute() should return a dictionary"
        )
        self.assertIn(
            "result", result_unmute, "Unmute response should contain 'result' field"
        )

        # Verify volume was restored
        unmuted_volume = get("MEDIA_VOLUME")
        self.assertGreater(
            unmuted_volume["percentage_value"],
            0,
            "Media volume should be > 0 after unmuting",
        )

    def test_basic_device_insights_workflow(self):
        """
        Smoke test: Verify device insights functionality works.

        Tests the insights system which provides device status information.
        This ensures the monitoring and reporting subsystem is operational.
        """
        from device_setting import get_device_insights

        # Test getting general device insights
        result = get_device_insights()
        self.assertIsInstance(
            result, dict, "get_device_insights() should return a dictionary"
        )
        self.assertIn("result", result, "Response should contain 'result' field")
        self.assertIn("card_id", result, "Response should contain 'card_id' field")
        self.assertIn(
            "action_card_content_passthrough",
            result,
            "Response should contain action card content",
        )

        # Test getting specific insights
        battery_insights = get_device_insights("BATTERY")
        self.assertIsInstance(
            battery_insights, dict, "Battery insights should return a dictionary"
        )
        self.assertIn(
            "result", battery_insights, "Battery insights should contain 'result' field"
        )

        storage_insights = get_device_insights("STORAGE")
        self.assertIsInstance(
            storage_insights, dict, "Storage insights should return a dictionary"
        )
        self.assertIn(
            "result", storage_insights, "Storage insights should contain 'result' field"
        )

    def test_basic_app_management_workflow(self):
        """
        Smoke test: Verify app management functionality works.

        Tests app-related functions which are essential for notification management.
        This ensures the app management subsystem is operational.
        """
        from device_setting import (
            get_installed_apps,
            get_app_notification_status,
            set_app_notification_status,
        )

        # Test getting installed apps
        apps_result = get_installed_apps()
        self.assertIsInstance(
            apps_result, dict, "get_installed_apps() should return a dictionary"
        )
        self.assertIn("apps", apps_result, "Response should contain 'apps' field")
        self.assertIsInstance(apps_result["apps"], list, "Apps field should be a list")
        self.assertIn("card_id", apps_result, "Response should contain 'card_id' field")

        # If there are apps, test notification management
        if apps_result["apps"]:
            test_app = apps_result["apps"][0]

            # Test getting notification status
            status_result = get_app_notification_status(test_app)
            self.assertIsInstance(
                status_result,
                dict,
                "get_app_notification_status() should return a dictionary",
            )
            self.assertIn(
                "app_name", status_result, "Response should contain 'app_name' field"
            )
            self.assertIn(
                "notifications",
                status_result,
                "Response should contain 'notifications' field",
            )
            self.assertIn(
                status_result["notifications"],
                ["on", "off"],
                "Notification status should be 'on' or 'off'",
            )

            # Test setting notification status
            set_result = set_app_notification_status(test_app, "off")
            self.assertIsInstance(
                set_result,
                dict,
                "set_app_notification_status() should return a dictionary",
            )
            self.assertIn(
                "result", set_result, "Response should contain 'result' field"
            )

            # Verify the change was applied
            updated_status = get_app_notification_status(test_app)
            self.assertEqual(
                updated_status["notifications"],
                "off",
                "Notification status should be updated to 'off'",
            )

    # BASIC ERROR HANDLING SMOKE TESTS

    def test_basic_error_handling_operational(self):
        """
        Smoke test: Verify error handling mechanisms are operational.

        Tests that invalid inputs produce appropriate errors rather than crashes.
        This ensures the error handling infrastructure is working correctly.
        """
        from device_setting import get, on, set_volume

        # Test that errors are properly raised for invalid inputs
        # For smoke tests, we just verify the exception type is correct

        # Test invalid setting type for get()
        with self.assertRaises(ValueError):
            get("INVALID_SETTING_TYPE")

        # Test invalid setting type for on()
        with self.assertRaises(ValueError):
            on("INVALID_TOGGLE_SETTING")

        # Test invalid volume value
        with self.assertRaises(ValueError):
            set_volume(150)  # Invalid volume level

    # END-TO-END WORKFLOW SMOKE TEST

    def test_end_to_end_device_control_workflow(self):
        """
        Smoke test: Verify a complete device control workflow works end-to-end.

        This test simulates a realistic user interaction with the device settings,
        ensuring that the entire system works together cohesively.
        """
        from device_setting import open, get, on, off, set_volume, get_device_insights

        # Step 1: Open WiFi settings (navigation)
        open_result = open("WIFI")
        self.assertIn("result", open_result, "Should be able to open WiFi settings")

        # Step 2: Check current WiFi status (read state)
        initial_wifi_status = get("WIFI")
        self.assertIn(
            "on_or_off", initial_wifi_status, "Should be able to get WiFi status"
        )
        initial_status = initial_wifi_status["on_or_off"]

        # Step 3: Toggle WiFi state (modify state)
        if initial_status == "on":
            toggle_result = off("WIFI")
            expected_new_status = "off"
        else:
            toggle_result = on("WIFI")
            expected_new_status = "on"

        self.assertIn("result", toggle_result, "Should be able to toggle WiFi")

        # Step 4: Verify the change was applied (read state again)
        updated_wifi_status = get("WIFI")
        self.assertEqual(
            updated_wifi_status["on_or_off"],
            expected_new_status,
            "WiFi status should be updated after toggle",
        )

        # Step 5: Set media volume (volume control)
        volume_result = set_volume(65, "MEDIA")
        self.assertIn("result", volume_result, "Should be able to set media volume")

        # Step 6: Verify volume was set
        media_volume = get("MEDIA_VOLUME")
        self.assertEqual(
            media_volume["percentage_value"], 65, "Media volume should be set to 65%"
        )

        # Step 7: Get device insights (monitoring)
        insights_result = get_device_insights()
        self.assertIn(
            "result", insights_result, "Should be able to get device insights"
        )

        # Step 8: Restore original WiFi state (cleanup)
        if initial_status == "on":
            on("WIFI")
        else:
            off("WIFI")

        # Verify restoration
        final_wifi_status = get("WIFI")
        self.assertEqual(
            final_wifi_status["on_or_off"],
            initial_status,
            "WiFi should be restored to original state",
        )

    def test_database_state_consistency(self):
        """
        Smoke test: Verify database state management is working correctly.

        This test ensures that changes persist correctly and the database
        state management infrastructure is operational.
        """
        from device_setting import set_volume, get, on, off

        # Set initial state
        set_volume(50, "RING")
        on("BLUETOOTH")

        # Verify changes are immediately visible
        ring_volume = get("RING_VOLUME")
        bluetooth_status = get("BLUETOOTH")

        self.assertEqual(
            ring_volume["percentage_value"],
            50,
            "Ring volume change should be persistent",
        )
        self.assertEqual(
            bluetooth_status["on_or_off"], "on", "Bluetooth change should be persistent"
        )

        # Make additional changes
        set_volume(80, "RING")
        off("BLUETOOTH")

        # Verify new changes overwrite previous ones correctly
        updated_ring_volume = get("RING_VOLUME")
        updated_bluetooth_status = get("BLUETOOTH")

        self.assertEqual(
            updated_ring_volume["percentage_value"],
            80,
            "Ring volume should be updated to new value",
        )
        self.assertEqual(
            updated_bluetooth_status["on_or_off"],
            "off",
            "Bluetooth should be updated to new state",
        )

    def test_data_type_consistency(self):
        """
        Smoke test: Verify all API functions return consistent data types.

        This test ensures that the API contract is maintained and functions
        return data in the expected format for client applications.
        """
        from device_setting import (
            open,
            get,
            on,
            off,
            set_volume,
            mute,
            unmute,
            adjust_volume,
            get_device_insights,
            get_installed_apps,
            get_app_notification_status,
        )

        # Test that all functions return dictionaries (API contract)
        test_cases = [
            (lambda: open(), "open()"),
            (lambda: open("WIFI"), "open('WIFI')"),
            (lambda: get("WIFI"), "get('WIFI')"),
            (lambda: on("WIFI"), "on('WIFI')"),
            (lambda: off("WIFI"), "off('WIFI')"),
            (lambda: set_volume(50), "set_volume(50)"),
            (lambda: mute(), "mute()"),
            (lambda: unmute(), "unmute()"),
            (lambda: adjust_volume(10), "adjust_volume(10)"),
            (lambda: get_device_insights(), "get_device_insights()"),
            (lambda: get_installed_apps(), "get_installed_apps()"),
        ]

        for test_func, func_name in test_cases:
            result = test_func()
            self.assertIsInstance(
                result, dict, f"{func_name} should return a dictionary"
            )

            # Verify common required fields exist
            if (
                func_name != "get_installed_apps()"
            ):  # get_installed_apps has different structure
                self.assertIn(
                    "card_id", result, f"{func_name} should include 'card_id' field"
                )

        # Test get_installed_apps specific structure
        apps_result = get_installed_apps()
        self.assertIn(
            "apps", apps_result, "get_installed_apps() should have 'apps' field"
        )
        self.assertIsInstance(apps_result["apps"], list, "Apps field should be a list")


if __name__ == "__main__":
    unittest.main()
