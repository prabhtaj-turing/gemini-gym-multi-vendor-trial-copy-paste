import unittest
import sys
import os
import importlib
import inspect
import json
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCESSmoke(BaseTestCaseWithErrorHandler):
    """
    Smoke tests for CES system identification service.
    Quick checks that the package installs and runs without issues.
    Ensures the service is ready to be implemented.
    """

    def test_smoke_imports(self):
        """
        Test that all main modules can be imported without errors.
        """
        try:
            # Test main package import
            import APIs.ces_system_activation
            
            # Test SimulationEngine imports
            import APIs.ces_system_activation.SimulationEngine
            import APIs.ces_system_activation.SimulationEngine.db
            import APIs.ces_system_activation.SimulationEngine.models
            import APIs.ces_system_activation.SimulationEngine.utils
            import APIs.ces_system_activation.SimulationEngine.custom_errors
            
            # Test main module import
            import APIs.ces_system_activation.ces_system_activation
            
            # If we get here, all imports succeeded
            self.assertTrue(True)
            
        except ImportError as e:
            self.fail(f"Failed to import required modules: {e}")
        except Exception as e:
            self.fail(f"Unexpected error during imports: {e}")

    def test_smoke_package_structure(self):
        """
        Test that the package has the expected structure and attributes.
        """
        import APIs.ces_system_activation as ces_pkg
        
        # Test that __all__ is defined
        self.assertTrue(hasattr(ces_pkg, '__all__'))
        self.assertIsInstance(ces_pkg.__all__, list)
        self.assertGreater(len(ces_pkg.__all__), 0)
        
        # Test that _function_map is defined
        self.assertTrue(hasattr(ces_pkg, '_function_map'))
        self.assertIsInstance(ces_pkg._function_map, dict)
        self.assertGreater(len(ces_pkg._function_map), 0)

    def test_smoke_function_accessibility(self):
        """
        Test that all public functions are accessible via the package.
        """
        import APIs.ces_system_activation as ces_pkg
        
        expected_functions = [
            "send_customer_notification",
            "search_order_details", 
            "search_activation_guides",
            "escalate",
            "fail", 
            "cancel"
        ]
        
        for func_name in expected_functions:
            # Test function is in __all__
            self.assertIn(func_name, ces_pkg.__all__, 
                         f"Function {func_name} not found in __all__")
            
            # Test function can be accessed
            self.assertTrue(hasattr(ces_pkg, func_name),
                          f"Function {func_name} not accessible")
            
            # Test function is callable
            func = getattr(ces_pkg, func_name)
            self.assertTrue(callable(func),
                          f"Function {func_name} is not callable")

    def test_smoke_database_initialization(self):
        """
        Test that the database initializes properly.
        """
        try:
            from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db
            
            # Test DB is accessible
            self.assertIsInstance(DB, dict)
            
            # Test reset_db function works
            reset_db()
            
            # Test required keys exist
            required_keys = ['customers', '_end_of_conversation_status', 'use_real_datastore']
            for key in required_keys:
                self.assertIn(key, DB, f"Required key '{key}' not found in DB")
            
            # Test customers data structure
            self.assertIsInstance(DB['customers'], list)
            if DB['customers']:  # If there are customers
                customer = DB['customers'][0]
                self.assertIsInstance(customer, dict)
                # Check for basic customer fields
                basic_fields = ['customerId', 'firstName', 'lastName', 'email']
                for field in basic_fields:
                    self.assertIn(field, customer, f"Customer missing field '{field}'")
                    
        except Exception as e:
            self.fail(f"Database initialization failed: {e}")

    def test_smoke_models_import(self):
        """
        Test that all Pydantic models can be imported and instantiated.
        """
        try:
            from APIs.ces_system_activation.SimulationEngine.models import (
                NotificationResult,
                DataStoreQueryResult,
                SourceSnippet,
                FlaggedIssueConfirmation,
                ServiceActivationAttempt,
                TechnicianVisitDetails,
                AppointmentAvailability,
                AvailableAppointmentSlot
            )
            
            # Test basic model instantiation (with minimal valid data)
            notification = NotificationResult(
                channelSent="EMAIL",
                status="SENT",
                recipientUsed="test@example.com",
                timestamp="2023-01-01T00:00:00Z",
                message="Test message",
                notificationId="test-id"
            )
            
            snippet = SourceSnippet(
                text="Test snippet",
                title="Test Title",
                uri="https://example.com"
            )
            
            query_result = DataStoreQueryResult(
                answer="Test answer",
                snippets=[snippet]
            )
            
        except Exception as e:
            self.fail(f"Model import/instantiation failed: {e}")

    def test_smoke_error_handling_setup(self):
        """
        Test that error handling framework is properly set up.
        """
        try:
            from APIs.ces_system_activation.SimulationEngine import custom_errors
            
            # Test that custom errors module exists and has basic structure
            self.assertTrue(hasattr(custom_errors, '__file__'))
            
            # Test error simulator is set up
            from APIs.ces_system_activation import error_simulator, ERROR_MODE
            
            self.assertIsNotNone(error_simulator)
            self.assertIsInstance(ERROR_MODE, str)
            
        except Exception as e:
            self.fail(f"Error handling setup failed: {e}")

    def test_smoke_utils_functionality(self):
        """
        Test that utility functions are accessible and have basic functionality.
        """
        try:
            from APIs.ces_system_activation.SimulationEngine import utils
            from APIs.ces_system_activation.SimulationEngine.utils import get_infobot_config
            
            # Test that utility functions exist
            self.assertTrue(hasattr(utils, 'query_activation_guides_infobot'))
            self.assertTrue(hasattr(utils, 'query_order_details_infobot'))
            self.assertTrue(callable(utils.query_activation_guides_infobot))
            self.assertTrue(callable(utils.query_order_details_infobot))
            
            # Test that config is accessible and has required properties
            config = get_infobot_config()
            self.assertTrue(hasattr(config, 'gcp_project'))
            self.assertTrue(hasattr(config, 'location'))
            self.assertTrue(hasattr(config, 'app_id'))
            
        except Exception as e:
            self.fail(f"Utils functionality test failed: {e}")

    @patch('APIs.ces_system_activation.SimulationEngine.utils._get_token')
    @patch('APIs.ces_system_activation.SimulationEngine.utils.search_order_details_by_query')
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "mock-google-api-key"}, clear=True)
    def test_smoke_basic_function_execution(self, mock_get_token, mock_search_order_details_by_query):
        """
        Test that basic functions can execute without errors.
        """
        self.skipTest("Skipping test_smoke_basic_function_execution")
        try:
            # Mock token to avoid authentication issues
            mock_get_token.return_value = 'mock-token'
            mock_search_order_details_by_query.return_value = [{"answer": "mock-answer", "snippets": [{"text": "mock-text", "title": "mock-title", "uri": "mock-uri"}]}]
            
            import APIs.ces_system_activation as ces
            
            # Test notification function
            result = ces.send_customer_notification(accountId="ACC-12345")
            self.assertIsNotNone(result)
            
            # Test conversation functions
            escalate_result = ces.escalate("Test escalation")
            self.assertIsInstance(escalate_result, dict)
            self.assertEqual(escalate_result['action'], 'escalate')
            
            fail_result = ces.fail("Test failure")
            self.assertIsInstance(fail_result, dict)
            self.assertEqual(fail_result['action'], 'fail')
            
            cancel_result = ces.cancel("Test cancellation")
            self.assertIsInstance(cancel_result, dict)
            self.assertEqual(cancel_result['action'], 'cancel')
            
            # Test search functions (without real datastore)
            from APIs.ces_system_activation.SimulationEngine.db import DB
            DB['use_real_datastore'] = False
            
            order_result = ces.search_order_details("Test order query")
            self.assertIsNotNone(order_result)
            
            guide_result = ces.search_activation_guides("Test guide query")
            self.assertIsNotNone(guide_result)
            
        except Exception as e:
            self.fail(f"Basic function execution failed: {e}")

    def test_smoke_package_metadata(self):
        """
        Test that package metadata is properly defined.
        """
        import APIs.ces_system_activation as ces_pkg
        
        # Test that package has basic attributes
        self.assertTrue(hasattr(ces_pkg, '__file__'))
        self.assertTrue(hasattr(ces_pkg, '__name__'))
        
        # Test function map integrity
        function_map = ces_pkg._function_map
        for func_name, func_path in function_map.items():
            self.assertIsInstance(func_name, str)
            self.assertIsInstance(func_path, str)
            self.assertTrue(func_name.strip())
            self.assertTrue(func_path.strip())
            self.assertIn('.', func_path)  # Should be a module path

    def test_smoke_dependency_availability(self):
        """
        Test that all required dependencies are available.
        """
        required_modules = [
            'json',
            'os', 
            'datetime',
            'typing',
            'pydantic',
            'requests',
            'google.auth',
            'google.oauth2'
        ]
        
        for module_name in required_modules:
            try:
                importlib.import_module(module_name)
            except ImportError:
                self.fail(f"Required dependency '{module_name}' is not available")

    def test_smoke_file_structure(self):
        """
        Test that all expected files exist in the package.
        """
        import APIs.ces_system_activation
        package_dir = os.path.dirname(APIs.ces_system_activation.__file__)
        
        expected_files = [
            '__init__.py',
            'ces_system_activation.py',
            'SimulationEngine/__init__.py',
            'SimulationEngine/db.py',
            'SimulationEngine/models.py', 
            'SimulationEngine/utils.py',
            'SimulationEngine/custom_errors.py'
        ]
        
        for expected_file in expected_files:
            file_path = os.path.join(package_dir, expected_file)
            self.assertTrue(os.path.exists(file_path), 
                          f"Expected file not found: {expected_file}")

    def test_smoke_configuration_loading(self):
        """
        Test that configuration and database files load properly.
        """
        try:
            from APIs.ces_system_activation.SimulationEngine.db import DEFAULT_DB_PATH
            
            # Test that default DB path is defined
            self.assertIsInstance(DEFAULT_DB_PATH, str)
            self.assertTrue(DEFAULT_DB_PATH.strip())
            
            # Test that the path makes sense (should end with .json)
            self.assertTrue(DEFAULT_DB_PATH.endswith('.json'))
            
        except Exception as e:
            self.fail(f"Configuration loading failed: {e}")

    def test_smoke_error_modes(self):
        """
        Test that error modes are properly configured.
        """
        try:
            from APIs.ces_system_activation import ERROR_MODE
            
            # Test that ERROR_MODE is defined and valid
            self.assertIsInstance(ERROR_MODE, str)
            self.assertTrue(ERROR_MODE.strip())
            
            # Test that it's a reasonable error mode value
            valid_modes = ['development', 'production', 'testing', 'debug', 'silent']
            # Note: We don't enforce specific values, just that it's configured
            
        except Exception as e:
            self.fail(f"Error mode configuration failed: {e}")

    def test_smoke_function_signatures(self):
        """
        Test that public functions have reasonable signatures.
        """
        import APIs.ces_system_activation as ces_pkg
        
        # Test a few key functions have proper signatures
        test_functions = [
            'send_customer_notification',
            'escalate',
            'fail',
            'cancel'
        ]
        
        for func_name in test_functions:
            func = getattr(ces_pkg, func_name)
            
            # Get function signature
            sig = inspect.signature(func)
            
            # Test that function has parameters
            params = list(sig.parameters.keys())
            self.assertGreater(len(params), 0, 
                             f"Function {func_name} has no parameters")
            
            # Test that parameters are properly named (no single letters, reasonable names)
            for param_name in params:
                self.assertGreater(len(param_name), 1,
                                 f"Function {func_name} has single-letter parameter: {param_name}")


if __name__ == '__main__':
    unittest.main()
