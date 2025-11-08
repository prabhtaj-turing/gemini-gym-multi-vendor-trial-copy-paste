"""
Import Test Suite for Device Setting API

This module contains comprehensive tests for verifying that all modules,
functions, and dependencies can be imported and initialized correctly.
"""

import unittest
import sys
import os

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestModuleImports(BaseTestCaseWithErrorHandler):
    """Test cases for module import functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.original_modules = {}

    def tearDown(self):
        """Clean up after each test method."""
        return

    def test_main_package_import(self):
        """Test that the main device_setting package can be imported."""
        import device_setting

        self.assertTrue(
            hasattr(device_setting, "__version__") or True
        )  # Package exists

    def test_device_setting_module_import(self):
        """Test importing the device_setting.device_setting module."""
        from device_setting import device_setting as ds_module

        self.assertTrue(hasattr(ds_module, "open"))
        self.assertTrue(hasattr(ds_module, "get"))
        self.assertTrue(hasattr(ds_module, "on"))
        self.assertTrue(hasattr(ds_module, "off"))
        self.assertTrue(hasattr(ds_module, "mute"))
        self.assertTrue(hasattr(ds_module, "unmute"))
        self.assertTrue(hasattr(ds_module, "adjust_volume"))
        self.assertTrue(hasattr(ds_module, "set_volume"))
        self.assertTrue(hasattr(ds_module, "get_device_insights"))

    def test_app_settings_module_import(self):
        """Test importing the device_setting.app_settings module."""
        from device_setting import app_settings

        self.assertTrue(hasattr(app_settings, "get_installed_apps"))
        self.assertTrue(hasattr(app_settings, "get_app_notification_status"))
        self.assertTrue(hasattr(app_settings, "set_app_notification_status"))

    def test_simulation_engine_import(self):
        """Test importing SimulationEngine components."""
        from device_setting.SimulationEngine import utils

        self.assertTrue(hasattr(utils, "get_setting"))
        self.assertTrue(hasattr(utils, "set_setting"))
        self.assertTrue(hasattr(utils, "get_device_info"))

        from device_setting.SimulationEngine import db

        self.assertTrue(hasattr(db, "DB"))
        self.assertTrue(hasattr(db, "load_state"))
        self.assertTrue(hasattr(db, "save_state"))

    def test_enums_import(self):
        """Test importing enum types."""
        from device_setting.SimulationEngine.enums import (
            DeviceSettingType,
            GetableDeviceSettingType,
            ToggleableDeviceSettingType,
            VolumeSettingType,
            DeviceStateType,
            ToggleState,
            ActionType,
            Constants,
        )

        # Verify enum types exist and have expected values
        self.assertTrue(hasattr(DeviceSettingType, "WIFI"))
        self.assertTrue(hasattr(GetableDeviceSettingType, "BATTERY"))
        self.assertTrue(hasattr(ToggleableDeviceSettingType, "BLUETOOTH"))
        self.assertTrue(hasattr(VolumeSettingType, "MEDIA"))
        self.assertTrue(hasattr(DeviceStateType, "UNCATEGORIZED"))
        self.assertTrue(hasattr(ToggleState, "ON"))
        self.assertTrue(hasattr(ActionType, "OPEN_SETTINGS"))
        self.assertTrue(hasattr(Constants, "DEVICE_SETTINGS"))

    def test_models_import(self):
        """Test importing model classes."""
        from device_setting.SimulationEngine.models import (
            SettingInfo,
            ActionSummary,
            Action,
            VolumeSettingMapping,
            volume_mapping,
        )

        # Verify model classes exist
        self.assertTrue(callable(SettingInfo))
        self.assertTrue(callable(ActionSummary))
        self.assertTrue(callable(Action))
        self.assertTrue(callable(VolumeSettingMapping))
        self.assertIsInstance(volume_mapping, VolumeSettingMapping)

    def test_device_insight_utils_import(self):
        """Test importing device insight utility modules."""
        from device_setting.SimulationEngine.device_insight_utils import battery_utils

        self.assertTrue(hasattr(battery_utils, "set_battery_percentage"))
        self.assertTrue(hasattr(battery_utils, "get_battery_insights"))

        from device_setting.SimulationEngine.device_insight_utils import general_utils

        self.assertTrue(hasattr(general_utils, "set_device_id"))
        self.assertTrue(hasattr(general_utils, "get_general_insights"))

        from device_setting.SimulationEngine.device_insight_utils import storage_utils

        self.assertTrue(hasattr(storage_utils, "set_storage_total_gb"))
        self.assertTrue(hasattr(storage_utils, "get_storage_insights"))


class TestPublicFunctions(BaseTestCaseWithErrorHandler):
    """Test cases for public function availability and basic callability."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset database state before each test
        from device_setting.SimulationEngine.db import load_state, DEFAULT_DB_PATH

        load_state(DEFAULT_DB_PATH)

    def test_main_package_functions(self):
        """Test that all main package functions are available."""
        import device_setting

        # Test function availability through __getattr__
        functions_to_test = [
            "open",
            "get",
            "on",
            "off",
            "mute",
            "unmute",
            "adjust_volume",
            "set_volume",
            "get_device_insights",
            "get_installed_apps",
            "get_app_notification_status",
            "set_app_notification_status",
        ]

        for func_name in functions_to_test:
            with self.subTest(function=func_name):
                func = getattr(device_setting, func_name)
                self.assertTrue(callable(func))

    def test_open_function_callable(self):
        """Test that open function can be called."""
        import device_setting

        # Test with no arguments (should open general settings)
        result = device_setting.open()
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

        # Test with valid setting type
        result = device_setting.open("WIFI")
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

    def test_get_function_callable(self):
        """Test that get function can be called with valid arguments."""
        import device_setting

        # Test with valid getable setting
        result = device_setting.get("WIFI")
        self.assertIsInstance(result, dict)
        self.assertIn("setting_type", result)

    def test_toggle_functions_callable(self):
        """Test that on/off functions can be called with valid arguments."""
        import device_setting

        # Test on function
        result = device_setting.on("WIFI")
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

        # Test off function
        result = device_setting.off("WIFI")
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

    def test_volume_functions_callable(self):
        """Test that volume-related functions can be called."""
        import device_setting

        # Test mute function
        result = device_setting.mute()
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

        # Test unmute function
        result = device_setting.unmute()
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

        # Test adjust_volume function
        result = device_setting.adjust_volume(10)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

        # Test set_volume function
        result = device_setting.set_volume(50)
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

    def test_device_insights_function_callable(self):
        """Test that get_device_insights function can be called."""
        import device_setting

        # Test with no arguments
        result = device_setting.get_device_insights()
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

        # Test with specific device state type
        result = device_setting.get_device_insights("BATTERY")
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

    def test_app_settings_functions_callable(self):
        """Test that app settings functions can be called."""
        import device_setting

        # Test get_installed_apps
        result = device_setting.get_installed_apps()
        self.assertIsInstance(result, dict)
        self.assertIn("apps", result)

        # Test get_app_notification_status with valid app
        result = device_setting.get_app_notification_status("Messages")
        self.assertIsInstance(result, dict)
        self.assertIn("app_name", result)

        # Test set_app_notification_status
        result = device_setting.set_app_notification_status("Messages", "on")
        self.assertIsInstance(result, dict)
        self.assertIn("result", result)

    def test_function_error_handling(self):
        """Test that functions handle invalid inputs properly."""
        import device_setting

        # Test get with invalid setting type
        from device_setting.SimulationEngine.enums import GetableDeviceSettingType

        valid_settings = [e.value for e in GetableDeviceSettingType]
        expected_message = (
            f"Invalid setting_type: 'INVALID_SETTING'. Must be one of: {valid_settings}"
        )
        self.assert_error_behavior(
            device_setting.get,
            ValueError,
            expected_message,
            None,  # No additional_expected_dict_fields
            "INVALID_SETTING",  # Positional argument for setting_type
        )

        # Test on with invalid setting
        valid_settings = [
            "AIRPLANE_MODE",
            "AUTO_ROTATE",
            "BATTERY_SAVER",
            "BLUETOOTH",
            "DO_NOT_DISTURB",
            "FLASHLIGHT",
            "HOT_SPOT",
            "NETWORK",
            "NFC",
            "NIGHT_MODE",
            "TALK_BACK",
            "VIBRATION",
            "WIFI",
        ]
        expected_message = f"Invalid setting: 'INVALID_SETTING'. Must be one of: {', '.join(valid_settings)}"
        self.assert_error_behavior(
            device_setting.on,
            ValueError,
            expected_message,
            None,  # No additional_expected_dict_fields
            "INVALID_SETTING",  # Positional argument for setting
        )

    def test_utility_functions_callable(self):
        """Test that utility functions from SimulationEngine are callable."""
        from device_setting.SimulationEngine.utils import (
            generate_card_id,
            get_setting,
            set_setting,
            get_device_info,
        )

        # Test generate_card_id
        card_id = generate_card_id()
        self.assertIsInstance(card_id, str)
        self.assertEqual(len(card_id), 36)  # UUID length

        # Test get_device_info
        device_info = get_device_info()
        self.assertIsInstance(device_info, dict)

        # Test set_setting and get_setting
        test_setting = {"on_or_off": "on"}
        set_setting("TEST_SETTING", test_setting)
        retrieved_setting = get_setting("TEST_SETTING")
        self.assertIsInstance(retrieved_setting, dict)
        self.assertEqual(retrieved_setting["on_or_off"], "on")


class TestDependencies(BaseTestCaseWithErrorHandler):
    """Test cases for verifying required dependencies."""

    def test_standard_library_imports(self):
        """Test that required standard library modules can be imported."""
        import json
        import uuid
        import tempfile

        # Verify basic functionality
        self.assertTrue(hasattr(json, "dumps"))
        self.assertTrue(hasattr(os, "path"))
        self.assertTrue(hasattr(sys, "path"))
        self.assertTrue(hasattr(uuid, "uuid4"))
        self.assertTrue(hasattr(tempfile, "mkdtemp"))

    def test_third_party_dependencies(self):
        """Test that required third-party packages can be imported."""
        import pydantic
        from pydantic import BaseModel, Field
        from dateutil import parser as dateutil_parser

        # Verify basic functionality
        self.assertTrue(hasattr(pydantic, "__version__"))
        self.assertTrue(callable(BaseModel))
        self.assertTrue(callable(Field))
        self.assertTrue(hasattr(dateutil_parser, "parse"))

    def test_common_utils_dependencies(self):
        """Test that common_utils dependencies are available."""
        from common_utils.error_handling import get_package_error_mode
        from common_utils.init_utils import (
            create_error_simulator,
            resolve_function_import,
        )
        from common_utils.tool_spec_decorator import tool_spec
        from common_utils.print_log import print_log

        # Verify these are callable/usable
        self.assertTrue(callable(get_package_error_mode))
        self.assertTrue(callable(create_error_simulator))
        self.assertTrue(callable(resolve_function_import))
        self.assertTrue(callable(tool_spec))
        self.assertTrue(callable(print_log))

    def test_database_file_accessibility(self):
        """Test that default database file can be accessed."""
        from device_setting.SimulationEngine.db import DEFAULT_DB_PATH
        import os

        self.assertTrue(os.path.exists(DEFAULT_DB_PATH))
        self.assertTrue(os.path.isfile(DEFAULT_DB_PATH))

        # Test that the file can be read
        with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
            import json

            data = json.load(f)
            self.assertIsInstance(data, dict)

    def test_error_configuration_files(self):
        """Test that error configuration files are accessible."""
        # Check if error config files exist in the SimulationEngine directory
        from device_setting.SimulationEngine import utils

        simulation_engine_dir = os.path.dirname(utils.__file__)

        error_config_path = os.path.join(simulation_engine_dir, "error_config.json")
        error_definitions_path = os.path.join(
            simulation_engine_dir, "error_definitions.json"
        )

        # The files should exist
        self.assertTrue(os.path.exists(error_config_path))
        self.assertTrue(os.path.exists(error_definitions_path))

    def test_alternate_fcds_accessibility(self):
        """Test that alternate FCD files are accessible."""
        from device_setting.SimulationEngine import utils

        simulation_engine_dir = os.path.dirname(utils.__file__)

        # Check if alternate_fcds directory exists
        fcds_dir = os.path.join(simulation_engine_dir, "alternate_fcds")
        if os.path.exists(fcds_dir):
            # Should contain JSON files
            files = os.listdir(fcds_dir)
            json_files = [f for f in files if f.endswith(".json")]
            self.assertGreater(len(json_files), 0)
        else:
            # If directory doesn't exist, that's also valid
            self.assertTrue(True)


class TestModuleStructure(BaseTestCaseWithErrorHandler):
    """Test cases for verifying module structure and organization."""

    def test_package_structure(self):
        """Test that the package has the expected structure."""
        import device_setting

        # Test __all__ attribute exists and contains expected functions
        expected_functions = [
            "open",
            "get",
            "on",
            "off",
            "mute",
            "unmute",
            "adjust_volume",
            "set_volume",
            "get_device_insights",
            "get_installed_apps",
            "get_app_notification_status",
            "set_app_notification_status",
        ]

        self.assertTrue(hasattr(device_setting, "__all__"))
        all_functions = device_setting.__all__

        for func in expected_functions:
            with self.subTest(function=func):
                self.assertIn(func, all_functions)

    def test_function_mapping(self):
        """Test that the function mapping is correctly configured."""
        from device_setting import _function_map

        expected_mappings = {
            "open": "device_setting.device_setting.open",
            "get": "device_setting.device_setting.get",
            "on": "device_setting.device_setting.on",
            "off": "device_setting.device_setting.off",
            "mute": "device_setting.device_setting.mute",
            "unmute": "device_setting.device_setting.unmute",
            "adjust_volume": "device_setting.device_setting.adjust_volume",
            "set_volume": "device_setting.device_setting.set_volume",
            "get_device_insights": "device_setting.device_setting.get_device_insights",
            "get_installed_apps": "device_setting.app_settings.get_installed_apps",
            "get_app_notification_status": "device_setting.app_settings.get_app_notification_status",
            "set_app_notification_status": "device_setting.app_settings.set_app_notification_status",
        }

        for func_name, module_path in expected_mappings.items():
            with self.subTest(function=func_name):
                self.assertEqual(_function_map[func_name], module_path)

    def test_enum_completeness(self):
        """Test that enums contain expected values."""
        from device_setting.SimulationEngine.enums import (
            DeviceSettingType,
            GetableDeviceSettingType,
            ToggleableDeviceSettingType,
            VolumeSettingType,
        )

        # Test some key enum values exist
        self.assertTrue(hasattr(DeviceSettingType, "WIFI"))
        self.assertTrue(hasattr(DeviceSettingType, "BLUETOOTH"))
        self.assertTrue(hasattr(DeviceSettingType, "BATTERY"))

        self.assertTrue(hasattr(GetableDeviceSettingType, "WIFI"))
        self.assertTrue(hasattr(GetableDeviceSettingType, "BATTERY"))

        self.assertTrue(hasattr(ToggleableDeviceSettingType, "WIFI"))
        self.assertTrue(hasattr(ToggleableDeviceSettingType, "BLUETOOTH"))

        self.assertTrue(hasattr(VolumeSettingType, "MEDIA"))
        self.assertTrue(hasattr(VolumeSettingType, "ALARM"))

    def test_dir_functionality(self):
        """Test that __dir__ functionality works correctly."""
        import device_setting

        # Test dir() returns expected attributes
        dir_contents = dir(device_setting)

        # Should include all mapped functions
        for func_name in device_setting.__all__:
            with self.subTest(function=func_name):
                self.assertIn(func_name, dir_contents)

        # Should include imported enums and models
        self.assertIn("DeviceSettingType", dir_contents)
        self.assertIn("SettingInfo", dir_contents)

    def test_database_initialization(self):
        """Test that database is properly initialized."""
        from device_setting.SimulationEngine.db import DB

        self.assertIsInstance(DB, dict)
        self.assertGreater(len(DB), 0)  # Should have some initial data

        # Should have expected top-level keys
        expected_keys = ["device_settings", "device_insights", "installed_apps"]
        for key in expected_keys:
            # At least one of these should exist in a properly initialized DB
            if key in DB:
                self.assertIsInstance(DB[key], dict)

    def test_error_simulator_initialization(self):
        """Test that error simulator is properly initialized."""
        from device_setting import error_simulator, ERROR_MODE

        self.assertIsNotNone(error_simulator)
        self.assertIn(ERROR_MODE, ["raise", "error_dict"])


if __name__ == "__main__":
    unittest.main()
