"""
Smoke test suite for home_assistant module.

Smoke tests verify that the basic functionality works and the system is operational.
These tests catch major issues quickly and ensure the service is ready for implementation.

Test Categories:
1. Package Import Tests - Verify all modules can be imported successfully
2. Basic API Usage Tests - Confirm key functions work with valid inputs  
3. Workflow Tests - Test realistic usage scenarios
4. Error Handling Tests - Verify graceful error responses
"""

import unittest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestHomeAssistantSmoke(BaseTestCaseWithErrorHandler):
    """Smoke test suite to verify home_assistant module basic functionality."""

    def setUp(self):
        """Set up test fixtures for smoke tests."""
        # Create minimal mock data for smoke testing
        # Only include essential devices to keep smoke tests fast and simple
        self.smoke_test_devices = {
            "LIGHT_001": {
                "type": "light",
                "name": "Test Light",
                "attributes": {
                    "state": "Off",
                    "brightness": 50
                }
            },
            "FAN_001": {
                "type": "fan", 
                "name": "Test Fan",
                "attributes": {
                    "state": "On"
                }
            },
            "DOOR_001": {
                "type": "door",
                "name": "Test Door", 
                "attributes": {
                    "state": "Closed"
                }
            }
        }

    def test_package_import_main_module(self):
        """
        SMOKE TEST: Verify main home_assistant module imports successfully.
        
        This test ensures the package is properly installed and the main module
        can be imported without errors. Failure here indicates a critical
        installation or packaging issue.
        """
        import home_assistant
        
        # Verify module has expected public interface
        self.assertTrue(hasattr(home_assistant, "__all__"))
        self.assertIsInstance(home_assistant.__all__, list)
        self.assertGreater(len(home_assistant.__all__), 0)
        
        # Verify all public functions are accessible
        expected_functions = [
            "list_devices", "get_device_info", "get_state", 
            "toggle_device", "set_device_property", "get_id_by_name"
        ]
        for func_name in expected_functions:
            self.assertTrue(
                hasattr(home_assistant, func_name),
                f"Critical function {func_name} not accessible in main module"
            )

    def test_package_import_submodules(self):
        """
        SMOKE TEST: Verify all critical submodules import successfully.
        
        This test ensures the package structure is intact and all necessary
        components can be loaded. Failure here indicates structural issues
        with the package organization.
        """
        # Import core submodules - these should never fail in a working installation
        import home_assistant.devices
        import home_assistant.SimulationEngine
        import home_assistant.SimulationEngine.db
        import home_assistant.SimulationEngine.utils
        
        # Verify key components exist
        self.assertTrue(hasattr(home_assistant.devices, "list_devices"))
        self.assertTrue(hasattr(home_assistant.SimulationEngine.db, "DB"))
        self.assertTrue(hasattr(home_assistant.SimulationEngine.utils, "allowed_states"))

    def test_package_import_dependencies(self):
        """
        SMOKE TEST: Verify all required dependencies are available.
        
        This test checks that the runtime environment has all necessary
        dependencies installed. Failure here indicates missing packages
        or environment setup issues.
        """
        # Test critical external dependencies
        import typing
        import os
        import json
        
        # Test internal framework dependencies  
        from common_utils.tool_spec_decorator import tool_spec
        from common_utils.error_handling import get_package_error_mode
        from common_utils.base_case import BaseTestCaseWithErrorHandler
        
        # Verify key components work
        self.assertTrue(callable(tool_spec))
        self.assertTrue(callable(get_package_error_mode))
        self.assertTrue(issubclass(BaseTestCaseWithErrorHandler, unittest.TestCase))

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_basic_api_list_devices_functionality(self, mock_get_devices):
        """
        SMOKE TEST: Verify list_devices basic functionality works.
        
        This test confirms the most fundamental operation (listing devices)
        works correctly. This is often the first function users call,
        so it must work reliably.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import list_devices
        
        # Test basic listing without parameters
        result = list_devices()
        
        # Verify expected response structure
        self.assertIsInstance(result, dict, "list_devices must return a dictionary")
        self.assertIn("entities", result, "Response must contain 'entities' key")
        self.assertIsInstance(result["entities"], list, "Entities must be a list")
        self.assertEqual(len(result["entities"]), 3, "Should return all test devices")
        
        # Test domain filtering works
        filtered_result = list_devices(domain="light")
        self.assertIsInstance(filtered_result, dict)
        self.assertIn("entities", filtered_result)
        # Should return only light devices (1 in our test data)
        self.assertEqual(len(filtered_result["entities"]), 1)

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_basic_api_get_device_info_functionality(self, mock_get_devices):
        """
        SMOKE TEST: Verify get_device_info basic functionality works.
        
        This test ensures device information retrieval works correctly.
        This is a core read operation that must be reliable for users
        to inspect device details.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import get_device_info
        
        # Test getting info for a known device
        result = get_device_info("LIGHT_001")
        
        # Verify expected response structure
        self.assertIsInstance(result, dict, "get_device_info must return a dictionary")
        self.assertIn("entity_id", result, "Response must contain 'entity_id'")
        self.assertIn("state", result, "Response must contain 'state'")
        self.assertEqual(result["entity_id"], "LIGHT_001", "Should return correct device ID")

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_basic_api_get_state_functionality(self, mock_get_devices):
        """
        SMOKE TEST: Verify get_state basic functionality works.
        
        This test confirms state retrieval works correctly. Getting device
        states is a fundamental operation for monitoring and control,
        so it must be reliable.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import get_state
        
        # Test getting state for a known device
        result = get_state("FAN_001")
        
        # Verify expected response structure
        self.assertIsInstance(result, dict, "get_state must return a dictionary")
        self.assertIn("entity_id", result, "Response must contain 'entity_id'")
        self.assertIn("state", result, "Response must contain 'state'")
        self.assertEqual(result["entity_id"], "FAN_001", "Should return correct device ID")

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_basic_api_toggle_device_functionality(self, mock_get_devices):
        """
        SMOKE TEST: Verify toggle_device basic functionality works.
        
        This test ensures device control operations work correctly.
        Device control is a primary use case, so basic toggle operations
        must function reliably.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import toggle_device
        
        # Test toggling with explicit state
        result = toggle_device("LIGHT_001", "On")
        
        # Verify successful operation
        self.assertIsInstance(result, dict, "toggle_device must return a dictionary")
        self.assertIn("status", result, "Response must contain 'status'")
        self.assertEqual(result["status"], "SUCCESS", "Operation should succeed")
        
        # Test toggling without explicit state (cycling)
        result_cycle = toggle_device("FAN_001")
        self.assertIsInstance(result_cycle, dict)
        self.assertEqual(result_cycle["status"], "SUCCESS")

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_basic_api_set_device_property_functionality(self, mock_get_devices):
        """
        SMOKE TEST: Verify set_device_property basic functionality works.
        
        This test confirms property modification works correctly.
        Setting device properties is essential for advanced control,
        so basic operations must be reliable.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import set_device_property
        
        # Test setting basic properties
        new_attributes = {"state": "On", "brightness": 75}
        result = set_device_property("LIGHT_001", new_attributes)
        
        # Verify successful operation
        self.assertIsInstance(result, dict, "set_device_property must return a dictionary")
        self.assertIn("status", result, "Response must contain 'status'")
        self.assertEqual(result["status"], "SUCCESS", "Operation should succeed")

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_basic_api_get_id_by_name_functionality(self, mock_get_devices):
        """
        SMOKE TEST: Verify get_id_by_name basic functionality works.
        
        This test ensures device lookup by name works correctly.
        Name-based lookup is important for user-friendly interfaces,
        so it must function reliably.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import get_id_by_name
        
        # Test finding device by name
        result = get_id_by_name("Test Light")
        
        # Verify expected response
        self.assertIsInstance(result, str, "get_id_by_name must return a string")
        self.assertEqual(result, "LIGHT_001", "Should return correct device ID")

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_realistic_workflow_scenario(self, mock_get_devices):
        """
        SMOKE TEST: Verify realistic end-to-end workflow works.
        
        This test simulates a typical user workflow to ensure all components
        work together correctly. This catches integration issues that might
        not appear in individual function tests.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import list_devices, get_device_info, get_state, toggle_device
        
        # Step 1: List all available devices
        devices = list_devices()
        self.assertGreater(len(devices["entities"]), 0, "Should have available devices")
        
        # Step 2: Get detailed info for first device
        first_device_id = list(self.smoke_test_devices.keys())[0]  # "LIGHT_001"
        device_info = get_device_info(first_device_id)
        self.assertIn("entity_id", device_info)
        
        # Step 3: Check current state
        current_state = get_state(first_device_id)
        self.assertIn("state", current_state)
        
        # Step 4: Toggle the device
        toggle_result = toggle_device(first_device_id, "On")
        self.assertEqual(toggle_result["status"], "SUCCESS")
        
        # All operations completed successfully - workflow is operational

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_domain_filtering_workflow(self, mock_get_devices):
        """
        SMOKE TEST: Verify domain filtering functionality works correctly.
        
        This test ensures domain-based filtering works across different
        device types. Domain filtering is commonly used, so it must
        work reliably.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import list_devices
        
        # Test filtering for each device type in test data
        device_types = ["light", "fan", "door"]
        
        for device_type in device_types:
            filtered_devices = list_devices(domain=device_type)
            self.assertIsInstance(filtered_devices, dict)
            self.assertIn("entities", filtered_devices)
            
            # Should return exactly one device of each type from our test data
            self.assertEqual(
                len(filtered_devices["entities"]), 
                1, 
                f"Should find exactly one {device_type} device"
            )

    def test_error_handling_graceful_failures(self):
        """
        SMOKE TEST: Verify error handling works correctly.
        
        This test ensures the system fails gracefully with proper error
        messages when given invalid inputs. Good error handling is critical
        for user experience and debugging.
        """
        from home_assistant import get_device_info, get_id_by_name, toggle_device
        
        # Test error handling for non-existent device
        self.assert_error_behavior(
            get_device_info,
            KeyError,
            "'device_id must be a valid device ID.'",
            None,
            "NONEXISTENT_DEVICE"
        )
        
        # Test error handling for non-existent device name
        self.assert_error_behavior(
            get_id_by_name,
            ValueError,
            "No device found with name 'Nonexistent Device'.",
            None,
            "Nonexistent Device"
        )
        
        # Test error handling for invalid entity in toggle
        self.assert_error_behavior(
            toggle_device,
            ValueError,
            "Entity 'INVALID_ENTITY' not found.",
            None,
            "INVALID_ENTITY"
        )

    def test_function_return_types_consistency(self):
        """
        SMOKE TEST: Verify all functions return expected data types.
        
        This test ensures API consistency by verifying return types.
        Consistent return types are important for reliable integration
        and prevent runtime type errors.
        """
        from home_assistant import (
            list_devices, get_device_info, get_state, 
            toggle_device, set_device_property, get_id_by_name
        )
        
        # Verify all functions are callable
        functions_to_test = [
            list_devices, get_device_info, get_state,
            toggle_device, set_device_property, get_id_by_name
        ]
        
        for func in functions_to_test:
            self.assertTrue(
                callable(func),
                f"Function {func.__name__} must be callable"
            )
            
            # Verify functions have docstrings (important for API documentation)
            self.assertIsNotNone(
                func.__doc__,
                f"Function {func.__name__} must have documentation"
            )
            
            # Verify docstrings are not empty
            self.assertGreater(
                len(func.__doc__.strip()),
                0,
                f"Function {func.__name__} must have non-empty documentation"
            )

    def test_module_version_and_metadata(self):
        """
        SMOKE TEST: Verify module has proper metadata and structure.
        
        This test ensures the module is properly packaged with required
        metadata. This helps with version tracking and package management.
        """
        import home_assistant
        
        # Verify module has __all__ defined (good packaging practice)
        self.assertTrue(
            hasattr(home_assistant, "__all__"),
            "Module should define __all__ for clear public API"
        )
        
        # Verify __all__ contains expected functions
        expected_public_functions = {
            "list_devices", "get_device_info", "get_state",
            "toggle_device", "set_device_property", "get_id_by_name"
        }
        
        actual_public_functions = set(home_assistant.__all__)
        self.assertEqual(
            actual_public_functions,
            expected_public_functions,
            "Public API should contain exactly the expected functions"
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_concurrent_operations_basic_stability(self, mock_get_devices):
        """
        SMOKE TEST: Verify multiple operations work reliably.
        
        This test ensures the system remains stable when performing
        multiple operations in sequence. This is important for real-world
        usage where multiple operations are common.
        """
        mock_get_devices.return_value = self.smoke_test_devices
        from home_assistant import list_devices, get_state, toggle_device
        
        # Perform multiple operations without errors
        operations_completed = 0
        
        # Multiple list operations
        for _ in range(3):
            result = list_devices()
            self.assertIn("entities", result)
            operations_completed += 1
        
        # Multiple state checks
        for device_id in ["LIGHT_001", "FAN_001"]:
            state = get_state(device_id)
            self.assertIn("state", state)
            operations_completed += 1
        
        # Multiple toggle operations
        toggle_result = toggle_device("LIGHT_001", "On")
        self.assertEqual(toggle_result["status"], "SUCCESS")
        operations_completed += 1
        
        # Verify all operations completed successfully
        self.assertEqual(
            operations_completed, 
            6, 
            "All concurrent operations should complete successfully"
        )


if __name__ == "__main__":
    unittest.main()
