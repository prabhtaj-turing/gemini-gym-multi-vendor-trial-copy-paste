"""
Comprehensive test suite for home_assistant module imports and public functions.

This test suite verifies:
1. Module imports work correctly
2. Public functions are available and callable
3. Required dependencies are installed
"""

import unittest
import sys
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestHomeAssistantImports(BaseTestCaseWithErrorHandler):
    """Test suite for home_assistant module imports and public function availability."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Store original modules to restore after tests
        self.original_modules = sys.modules.copy()

        # Mock database to avoid dependency issues during testing
        self.mock_db_data = {
            "environment": {
                "home_assistant": {
                    "devices": {
                        "LIGHT_001": {
                            "type": "light",
                            "name": "Living Room Light",
                            "attributes": {"state": "Off", "brightness": 50},
                        },
                        "FAN_001": {
                            "type": "fan",
                            "name": "Bedroom Fan",
                            "attributes": {"state": "On"},
                        },
                    }
                }
            }
        }

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original modules
        sys.modules.clear()
        sys.modules.update(self.original_modules)

    def test_module_import_home_assistant_main(self):
        """Test that the main home_assistant module can be imported."""
        import home_assistant

        self.assertTrue(hasattr(home_assistant, "__all__"))
        self.assertIsInstance(home_assistant.__all__, list)
        self.assertGreater(len(home_assistant.__all__), 0)

    def test_module_import_home_assistant_devices(self):
        """Test that the home_assistant.devices module can be imported."""
        import home_assistant.devices

        # Verify the module has expected attributes
        self.assertTrue(hasattr(home_assistant.devices, "list_devices"))
        self.assertTrue(hasattr(home_assistant.devices, "get_device_info"))
        self.assertTrue(hasattr(home_assistant.devices, "get_state"))
        self.assertTrue(hasattr(home_assistant.devices, "toggle_device"))
        self.assertTrue(hasattr(home_assistant.devices, "set_device_property"))
        self.assertTrue(hasattr(home_assistant.devices, "get_id_by_name"))

    def test_module_import_simulation_engine(self):
        """Test that SimulationEngine submodules can be imported."""
        import home_assistant.SimulationEngine
        import home_assistant.SimulationEngine.db
        import home_assistant.SimulationEngine.utils
        import home_assistant.SimulationEngine.file_utils

        # Verify key components exist
        self.assertTrue(hasattr(home_assistant.SimulationEngine.db, "DB"))
        self.assertTrue(
            hasattr(home_assistant.SimulationEngine.utils, "allowed_states")
        )

    def test_module_import_all_public_exports(self):
        """Test that all public exports from __init__.py can be imported."""
        from home_assistant import (
            get_state,
            toggle_device,
            list_devices,
            get_id_by_name,
            get_device_info,
            set_device_property,
        )

        # Verify all functions are callable
        self.assertTrue(callable(get_state))
        self.assertTrue(callable(toggle_device))
        self.assertTrue(callable(list_devices))
        self.assertTrue(callable(get_id_by_name))
        self.assertTrue(callable(get_device_info))
        self.assertTrue(callable(set_device_property))

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_public_function_list_devices_callable(self, mock_get_devices):
        """Test that list_devices function is callable with valid arguments."""
        mock_get_devices.return_value = self.mock_db_data["environment"][
            "home_assistant"
        ]["devices"]

        from home_assistant import list_devices

        # Test with no arguments
        result = list_devices()
        self.assertIsInstance(result, dict)
        self.assertIn("entities", result)

        # Test with domain filter
        result_with_domain = list_devices(domain="light")
        self.assertIsInstance(result_with_domain, dict)
        self.assertIn("entities", result_with_domain)

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_public_function_get_device_info_callable(self, mock_get_devices):
        """Test that get_device_info function is callable with valid arguments."""
        mock_get_devices.return_value = self.mock_db_data["environment"][
            "home_assistant"
        ]["devices"]

        from home_assistant import get_device_info

        # Test with valid device ID
        result = get_device_info("LIGHT_001")
        self.assertIsInstance(result, dict)
        self.assertIn("entity_id", result)
        self.assertIn("state", result)

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_public_function_get_state_callable(self, mock_get_devices):
        """Test that get_state function is callable with valid arguments."""
        mock_get_devices.return_value = self.mock_db_data["environment"][
            "home_assistant"
        ]["devices"]

        from home_assistant import get_state

        # Test with valid entity ID
        result = get_state("LIGHT_001")
        self.assertIsInstance(result, dict)
        self.assertIn("entity_id", result)
        self.assertIn("state", result)

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_public_function_toggle_device_callable(self, mock_get_devices):
        """Test that toggle_device function is callable with valid arguments."""
        mock_get_devices.return_value = self.mock_db_data["environment"][
            "home_assistant"
        ]["devices"]

        from home_assistant import toggle_device

        # Test with entity ID only (cycling)
        result = toggle_device("LIGHT_001")
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)

        # Test with specific state
        result_with_state = toggle_device("LIGHT_001", "On")
        self.assertIsInstance(result_with_state, dict)
        self.assertIn("status", result_with_state)

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_public_function_set_device_property_callable(self, mock_get_devices):
        """Test that set_device_property function is callable with valid arguments."""
        mock_get_devices.return_value = self.mock_db_data["environment"][
            "home_assistant"
        ]["devices"]

        from home_assistant import set_device_property

        # Test with valid arguments
        new_attributes = {"state": "On", "brightness": 75}
        result = set_device_property("LIGHT_001", new_attributes)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_public_function_get_id_by_name_callable(self, mock_get_devices):
        """Test that get_id_by_name function is callable with valid arguments."""
        mock_get_devices.return_value = self.mock_db_data["environment"][
            "home_assistant"
        ]["devices"]

        from home_assistant import get_id_by_name

        # Test with valid device name
        result = get_id_by_name("Living Room Light")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "LIGHT_001")

    def test_public_function_error_handling_get_state_invalid_entity(self):
        """Test error handling for get_state with invalid entity ID."""
        from home_assistant import get_state

        # Test with invalid entity ID - should raise ValueError
        self.assert_error_behavior(
            get_state,
            ValueError,
            "entity_id must be a valid device ID.",
            None,  # no additional expected dict fields
            "INVALID_DEVICE",
        )

    def test_public_function_error_handling_get_device_info_invalid_device(self):
        """Test error handling for get_device_info with invalid device ID."""
        from home_assistant import get_device_info

        # Test with invalid device ID - should raise KeyError
        self.assert_error_behavior(
            get_device_info,
            KeyError,
            "'device_id must be a valid device ID.'",
            None,  # no additional expected dict fields
            "INVALID_DEVICE",
        )

    def test_public_function_error_handling_toggle_device_invalid_entity(self):
        """Test error handling for toggle_device with invalid entity ID."""
        from home_assistant import toggle_device

        # Test with invalid entity ID - should raise ValueError
        self.assert_error_behavior(
            toggle_device,
            ValueError,
            "Entity 'INVALID_DEVICE' not found.",
            None,  # no additional expected dict fields
            "INVALID_DEVICE",
        )

    def test_public_function_error_handling_set_device_property_missing_entity(self):
        """Test error handling for set_device_property with missing entity ID."""
        from home_assistant import set_device_property

        # Test with empty entity ID - should raise ValueError
        self.assert_error_behavior(
            set_device_property,
            ValueError,
            "Missing required field: entity_id",
            None,  # no additional expected dict fields
            "",  # empty entity_id
            {"state": "On"},
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_public_function_error_handling_set_device_property_invalid_attributes(
        self, mock_get_devices
    ):
        """Test error handling for set_device_property with invalid attributes."""
        mock_get_devices.return_value = self.mock_db_data["environment"][
            "home_assistant"
        ]["devices"]
        from home_assistant import set_device_property

        # Test with invalid attributes type - should raise TypeError
        self.assert_error_behavior(
            set_device_property,
            TypeError,
            "new_attributes must be a dictionary.",
            None,  # no additional expected dict fields
            "LIGHT_001",
            "not_a_dict",  # invalid attributes
        )

    def test_public_function_error_handling_get_id_by_name_not_found(self):
        """Test error handling for get_id_by_name with non-existent name."""
        from home_assistant import get_id_by_name

        # Test with non-existent name - should raise ValueError
        self.assert_error_behavior(
            get_id_by_name,
            ValueError,
            "No device found with name 'Non-existent Device'.",
            None,  # no additional expected dict fields
            "Non-existent Device",
        )

    def test_dependencies_typing_module(self):
        """Test that typing module is available."""
        import typing

        # Verify common typing constructs are available
        self.assertTrue(hasattr(typing, "Dict"))
        self.assertTrue(hasattr(typing, "List"))
        self.assertTrue(hasattr(typing, "Optional"))
        self.assertTrue(hasattr(typing, "Union"))
        self.assertTrue(hasattr(typing, "Literal"))

    def test_dependencies_common_utils_modules(self):
        """Test that required common_utils modules are available."""
        from common_utils.tool_spec_decorator import tool_spec
        from common_utils.print_log import print_log
        from common_utils.error_handling import get_package_error_mode
        from common_utils.init_utils import (
            create_error_simulator,
            resolve_function_import,
        )

        # Verify key functions are callable
        self.assertTrue(callable(tool_spec))
        self.assertTrue(callable(print_log))
        self.assertTrue(callable(get_package_error_mode))
        self.assertTrue(callable(create_error_simulator))
        self.assertTrue(callable(resolve_function_import))

    def test_dependencies_standard_library_modules(self):
        """Test that required standard library modules are available."""
        import importlib
        import os
        import json
        import tempfile

        # Verify key functions/classes are available
        self.assertTrue(hasattr(importlib, "import_module"))
        self.assertTrue(hasattr(os, "path"))
        self.assertTrue(hasattr(json, "loads"))
        self.assertTrue(hasattr(tempfile, "mktemp"))

    def test_module_structure_integrity(self):
        """Test that the module structure is intact and accessible."""
        import home_assistant

        # Verify __all__ contains expected functions
        expected_functions = [
            "get_state",
            "toggle_device",
            "list_devices",
            "get_id_by_name",
            "get_device_info",
            "set_device_property",
        ]

        for func_name in expected_functions:
            self.assertIn(
                func_name,
                home_assistant.__all__,
                f"Function {func_name} not in __all__",
            )
            self.assertTrue(
                hasattr(home_assistant, func_name),
                f"Function {func_name} not accessible via module",
            )

    def test_simulation_engine_components_available(self):
        """Test that SimulationEngine components are properly accessible."""
        from home_assistant.SimulationEngine.db import DB
        from home_assistant.SimulationEngine.utils import (
            allowed_states,
            _get_device_type,
        )

        # Verify DB has expected methods
        self.assertTrue(hasattr(DB, "get"))

        # Verify allowed_states is properly structured
        self.assertIsInstance(allowed_states, dict)
        self.assertGreater(len(allowed_states), 0)

        # Verify utility functions are callable
        self.assertTrue(callable(_get_device_type))


if __name__ == "__main__":
    unittest.main()
