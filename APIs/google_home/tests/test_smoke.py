import unittest
import sys
import os
import tempfile
import shutil

# Add the parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestGoogleHomeSmoke(BaseTestCaseWithErrorHandler):
    """Smoke tests for Google Home API - quick sanity checks for package installation and basic functionality."""

    def setUp(self):
        super().setUp()
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, 'test_state.json')

        # Set up minimal DB state
        from google_home.SimulationEngine.db import DB
        DB.clear()
        DB['structures'] = {
            'Home': {
                'name': 'Home',
                'rooms': {
                    'Living': {
                        'name': 'Living',
                        'devices': {
                            'LIGHT': [
                                {
                                    'id': 'light-smoke',
                                    'names': ['Smoke Lamp'],
                                    'types': ['LIGHT'],
                                    'traits': ['OnOff'],
                                    'room_name': 'Living',
                                    'structure': 'Home',
                                    'toggles_modes': [],
                                    'device_state': [{'name': 'on', 'value': False}],
                                }
                            ]
                        },
                    }
                },
            }
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        super().tearDown()

    def test_package_import_success(self):
        """Test that the google_home package can be imported without errors."""
        try:
            import google_home
            self.assertIsNotNone(google_home)
        except ImportError as e:
            self.fail(f"Failed to import Google Home package: {e}")

    def test_module_import_success(self):
        """Test that core modules can be imported without errors."""
        modules_to_test = [
            'google_home',
            'google_home.SimulationEngine',
            'google_home.SimulationEngine.db',
            'google_home.SimulationEngine.utils',
            'google_home.SimulationEngine.models',
            'google_home.devices_api',
            'google_home.get_devices_api',
            'google_home.get_all_devices_api',
            'google_home.details_api',
            'google_home.run_api',
            'google_home.mutate_api',
            'google_home.mutate_traits_api',
            'google_home.view_schedules_api',
            'google_home.cancel_schedules_api',
            'google_home.search_home_events_api',
            'google_home.generate_home_automation_api',
            'google_home.see_devices_api',
        ]

        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    module = __import__(module_name, fromlist=['*'])
                    self.assertIsNotNone(module)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")

    def test_public_functions_available(self):
        """Test that public API functions are available and callable."""
        import google_home

        for func_name in google_home.__all__:
            with self.subTest(function=func_name):
                self.assertTrue(hasattr(google_home, func_name), f"Function {func_name} not available")
                func = getattr(google_home, func_name)
                self.assertTrue(callable(func), f"Function {func_name} is not callable")

    def test_basic_function_usage_no_errors(self):
        """Test that basic API functions can be called without raising errors."""
        from google_home import devices, get_devices

        try:
            result = devices()
            self.assertIsInstance(result, dict)
            self.assertIn('devices', result)
        except Exception as e:
            self.fail(f"devices() failed: {e}")

        try:
            result = get_devices()
            self.assertIsInstance(result, dict)
            self.assertIn('devices', result)
        except Exception as e:
            self.fail(f"get_devices() failed: {e}")

    def test_database_operations_no_errors(self):
        """Test that database operations work without errors."""
        from google_home.SimulationEngine.db import DB, save_state, load_state

        try:
            self.assertIsInstance(DB, dict)
            self.assertIn('structures', DB)
        except Exception as e:
            self.fail(f"Database access failed: {e}")

        try:
            save_state(self.test_file_path)
            self.assertTrue(os.path.exists(self.test_file_path))
        except Exception as e:
            self.fail(f"save_state failed: {e}")

        try:
            load_state(self.test_file_path)
        except Exception as e:
            self.fail(f"load_state failed: {e}")

    def test_package_structure_integrity(self):
        """Test that the package structure is intact and all required components exist."""
        import google_home

        self.assertTrue(hasattr(google_home, '__all__'))
        self.assertIsInstance(google_home.__all__, list)

        for func_name in google_home.__all__:
            self.assertTrue(hasattr(google_home, func_name), f"Function {func_name} not available")
            func = getattr(google_home, func_name)
            self.assertTrue(callable(func), f"Function {func_name} is not callable")

    def test_dependencies_available(self):
        """Test that all required dependencies are available."""
        required_modules = [
            'pydantic', 're', 'uuid', 'datetime', 'typing', 'os', 'json', 'mimetypes'
        ]

        for module_name in required_modules:
            with self.subTest(module=module_name):
                try:
                    __import__(module_name)
                except ImportError as e:
                    self.fail(f"Required dependency {module_name} not available: {e}")


if __name__ == '__main__':
    unittest.main()


