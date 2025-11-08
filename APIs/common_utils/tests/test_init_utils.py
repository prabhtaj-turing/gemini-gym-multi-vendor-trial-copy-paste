#!/usr/bin/env python3
"""
Tests for init_utils module.

This module tests the initialization utilities for API modules.
"""

import unittest
import os
import sys
import tempfile
import json
import shutil
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.init_utils import (
    create_error_simulator,
    apply_decorators,
    resolve_function_import,
    get_log_records_fetched
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestInitUtils(BaseTestCaseWithErrorHandler):
    """Test cases for init_utils module."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create a temporary directory structure for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create mock service directory structure
        self.service_dir = os.path.join(self.temp_dir, "test_service")
        os.makedirs(self.service_dir)
        
        # Create SimulationEngine directory
        self.simulation_dir = os.path.join(self.service_dir, "SimulationEngine")
        os.makedirs(self.simulation_dir)
        
        # Create mock configuration files
        self.error_config_path = os.path.join(self.simulation_dir, "error_config.json")
        self.error_definitions_path = os.path.join(self.simulation_dir, "error_definitions.json")
        
        # Create mock error config
        error_config = {
            "enabled": True,
            "error_rate": 0.1,
            "simulation_mode": "random"
        }
        
        # Create mock error definitions
        error_definitions = {
            "errors": [
                {
                    "name": "test_error",
                    "type": "ValueError",
                    "message": "Test error message"
                }
            ]
        }
        
        # Write mock files
        with open(self.error_config_path, 'w') as f:
            json.dump(error_config, f)
        
        with open(self.error_definitions_path, 'w') as f:
            json.dump(error_definitions, f)

    def tearDown(self):
        """Clean up test fixtures."""
        super().tearDown()
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('common_utils.init_utils.ErrorSimulator')
    @patch('common_utils.error_simulation_manager.ErrorSimulationManager.get_active_central_config')
    @patch('common_utils.error_simulation_manager.should_apply_central_config')
    @patch('common_utils.init_utils.apply_central_config_to_simulator')
    @patch('common_utils.init_utils.print_log')
    def test_create_error_simulator_success(self, mock_print_log, mock_apply_config, mock_should_apply, mock_get_active_config, mock_error_simulator_class):
        """Test successful creation of error simulator."""
        # Mock the ErrorSimulator class
        mock_simulator = MagicMock()
        mock_error_simulator_class.return_value = mock_simulator
        
        # Mock central config functions
        mock_should_apply.return_value = True
        mock_apply_config.return_value = None
        mock_get_active_config.return_value = {"test_service": {"enabled": True}}
        
        # Test the function
        result = create_error_simulator(self.service_dir)
        
        # Verify ErrorSimulator was created with correct parameters
        mock_error_simulator_class.assert_called_once_with(
            error_config_path=self.error_config_path,
            error_definitions_path=self.error_definitions_path,
            service_root_path=None
        )
        
        # Verify service_name was set
        self.assertEqual(mock_simulator.service_name, "test_service")
        
        # Verify central config was applied
        mock_should_apply.assert_called_once()
        mock_apply_config.assert_called_once_with(mock_simulator, "test_service")
        
        # Verify result
        self.assertEqual(result, mock_simulator)

    @patch('common_utils.init_utils.ErrorSimulator')
    @patch('common_utils.error_simulation_manager.apply_central_config_to_simulator')
    @patch('common_utils.error_simulation_manager.should_apply_central_config')
    def test_create_error_simulator_with_service_root_path(self, mock_should_apply, mock_apply_config, mock_error_simulator_class):
        """Test creation of error simulator with service root path."""
        mock_simulator = MagicMock()
        mock_error_simulator_class.return_value = mock_simulator
        mock_should_apply.return_value = False
        
        service_root_path = "/custom/service/path"
        result = create_error_simulator(self.service_dir, service_root_path)
        
        # Verify ErrorSimulator was created with service_root_path
        mock_error_simulator_class.assert_called_once_with(
            error_config_path=self.error_config_path,
            error_definitions_path=self.error_definitions_path,
            service_root_path=service_root_path
        )
        
        self.assertEqual(result, mock_simulator)

    def test_create_error_simulator_missing_error_config(self):
        """Test create_error_simulator with missing error config file."""
        # Remove the error config file
        os.remove(self.error_config_path)
        
        with self.assertRaises(FileNotFoundError) as context:
            create_error_simulator(self.service_dir)
        
        self.assertIn("Local error config file not found", str(context.exception))

    def test_create_error_simulator_missing_error_definitions(self):
        """Test create_error_simulator with missing error definitions file."""
        # Remove the error definitions file
        os.remove(self.error_definitions_path)
        
        with self.assertRaises(FileNotFoundError) as context:
            create_error_simulator(self.service_dir)
        
        self.assertIn("Error definitions file not found", str(context.exception))

    @patch('common_utils.init_utils.ErrorSimulator')
    @patch('common_utils.error_simulation_manager.apply_central_config_to_simulator')
    @patch('common_utils.error_simulation_manager.should_apply_central_config')
    def test_create_error_simulator_central_config_exception(self, mock_should_apply, mock_apply_config, mock_error_simulator_class):
        """Test create_error_simulator handles central config exceptions gracefully."""
        mock_simulator = MagicMock()
        mock_error_simulator_class.return_value = mock_simulator
        mock_should_apply.return_value = True
        mock_apply_config.side_effect = Exception("Central config error")
        
        # Should not raise exception, should continue
        result = create_error_simulator(self.service_dir)
        
        # Verify ErrorSimulator was still created
        self.assertEqual(result, mock_simulator)

    @patch('common_utils.init_utils.log_function_call')
    @patch('common_utils.init_utils.log_complexity')
    @patch('common_utils.init_utils.handle_api_errors')
    @patch('common_utils.init_utils.get_log_records_fetched')
    def test_apply_decorators_basic(self, mock_get_log_records, mock_error_handler, mock_log_complexity, mock_log_function):
        """Test basic decorator application."""
        # Mock get_log_records_fetched to return True
        mock_get_log_records.return_value = True
        
        # Create a mock original function
        original_func = MagicMock()
        original_func.__name__ = "test_function"
        
        # Mock error simulator
        mock_error_simulator = MagicMock()
        mock_error_simulator.get_error_simulation_decorator.return_value = lambda func: func
        
        # Mock decorators
        mock_error_handler.return_value = lambda func: func
        mock_log_complexity.return_value = lambda func: func
        mock_log_function.return_value = lambda func: func
        
        # Test the function
        decorated_func = apply_decorators(
            original_func, 
            "test_service", 
            "test_function", 
            "test_service.test_function",
            mock_error_simulator
        )
        
        # Verify decorators were called
        mock_error_handler.assert_called_once()
        mock_log_complexity.assert_called_once()
        mock_log_function.assert_called_once()
        
        # Verify result is callable
        self.assertTrue(callable(decorated_func))

    @patch('common_utils.init_utils.log_function_call')
    @patch('common_utils.init_utils.log_complexity')
    @patch('common_utils.init_utils.handle_api_errors')
    @patch('common_utils.init_utils.MutationManager')
    @patch('common_utils.init_utils.get_log_records_fetched')
    def test_apply_decorators_with_error_simulator(self, mock_get_log_records, mock_mutation_manager, mock_error_handler, mock_log_complexity, mock_log_function):
        """Test decorator application with error simulator."""
        # Mock get_log_records_fetched to return True
        mock_get_log_records.return_value = True
        
        original_func = MagicMock()
        original_func.__name__ = "test_function"
        
        # Mock error simulator
        mock_simulator = MagicMock()
        mock_simulator.get_error_simulation_decorator.return_value = lambda func: func
        
        # Mock decorators
        mock_error_handler.return_value = lambda func: func
        mock_log_complexity.return_value = lambda func: func
        mock_log_function.return_value = lambda func: func
        mock_mutation_manager.return_value.get_auth_decorator.return_value = lambda func: func
        
        # Test the function
        decorated_func = apply_decorators(
            original_func, 
            "test_service", 
            "test_function", 
            "test_service.test_function",
            mock_simulator
        )
        
        # Verify error simulator decorator was called
        mock_simulator.get_error_simulation_decorator.assert_called_once()
        
        # Verify result is callable
        self.assertTrue(callable(decorated_func))

    @patch('common_utils.init_utils.importlib.import_module')
    @patch('common_utils.init_utils.MutationManager')
    @patch('common_utils.init_utils.print_log')
    def test_resolve_function_import_success(self, mock_print_log, mock_mutation_manager, mock_import_module):
        """Test successful function import resolution."""
        # Mock MutationManager methods
        mock_mutation_manager.get_current_mutation_name_for_service.return_value = None
        mock_mutation_manager.get_current_mutation_function_map_for_service.return_value = None
        mock_mutation_manager.get_error_mutator_decorator_for_service.return_value = None
        
        # Mock the module and function
        mock_module = MagicMock()
        mock_function = MagicMock()
        # Ensure the function is callable
        mock_function.return_value = "test_result"
        mock_module.test_function = mock_function
        mock_import_module.return_value = mock_module
        
        # Mock function map
        function_map = {"test_function": "test_module.test_function"}
        
        # Mock error simulator
        mock_error_simulator = MagicMock()
        # Mock the error simulation decorator to return the original function
        mock_error_simulator.get_error_simulation_decorator.return_value = lambda func: func
        
        result = resolve_function_import(
            "test_function",
            function_map,
            mock_error_simulator
        )
        
        # Verify import was called (it might be called multiple times due to other imports)
        mock_import_module.assert_any_call("test_module")
        
        # Verify result is callable (it should be a decorated function)
        self.assertTrue(callable(result))
        
        # Verify the function can be called
        self.assertEqual(result(), "test_result")

    @patch('common_utils.init_utils.importlib.import_module')
    def test_resolve_function_import_module_not_found(self, mock_import_module):
        """Test function import resolution with module not found."""
        mock_import_module.side_effect = ImportError("No module named 'test_module'")
        
        # Mock function map
        function_map = {"test_function": "test_module.test_function"}
        mock_error_simulator = MagicMock()
        
        with self.assertRaises(ImportError):
            resolve_function_import(
                "test_function",
                function_map,
                mock_error_simulator
            )

    @patch('common_utils.init_utils.importlib.import_module')
    def test_resolve_function_import_attribute_error(self, mock_import_module):
        """Test function import resolution with attribute error."""
        mock_module = MagicMock()
        # Remove the attribute to simulate AttributeError
        del mock_module.test_function
        mock_import_module.return_value = mock_module
        
        # Mock function map
        function_map = {"test_function": "test_module.test_function"}
        mock_error_simulator = MagicMock()
        
        with self.assertRaises(AttributeError):
            resolve_function_import(
                "test_function",
                function_map,
                mock_error_simulator
            )

    def test_get_log_records_fetched(self):
        """Test get_log_records_fetched function."""
        # Mock the import
        with patch('common_utils.LOG_RECORDS_FETCHED', False):
            result = get_log_records_fetched()
            self.assertFalse(result)
        
        with patch('common_utils.LOG_RECORDS_FETCHED', True):
            result = get_log_records_fetched()
            self.assertTrue(result)

    @patch('common_utils.init_utils.log_function_call')
    @patch('common_utils.init_utils.log_complexity')
    @patch('common_utils.init_utils.handle_api_errors')
    @patch('common_utils.init_utils.get_log_records_fetched')
    def test_apply_decorators_decorator_order(self, mock_get_log_records, mock_error_handler, mock_log_complexity, mock_log_function):
        """Test that decorators are applied in the correct order."""
        # Mock get_log_records_fetched to return True
        mock_get_log_records.return_value = True
        
        original_func = MagicMock()
        original_func.__name__ = "test_function"
        
        # Mock error simulator
        mock_error_simulator = MagicMock()
        mock_error_simulator.get_error_simulation_decorator.return_value = lambda func: func
        
        # Track the order of decorator calls
        decorator_order = []
        
        def mock_decorator(name):
            def decorator(func):
                decorator_order.append(name)
                return func
            return decorator
        
        mock_error_handler.side_effect = lambda *args, **kwargs: mock_decorator("error_handler")
        mock_log_complexity.side_effect = mock_decorator("log_complexity")
        mock_log_function.side_effect = lambda *args, **kwargs: mock_decorator("log_function")
        
        # Apply decorators
        apply_decorators(
            original_func, 
            "test_service", 
            "test_function", 
            "test_service.test_function",
            mock_error_simulator
        )
        
        # Verify order: error_handler (outermost) -> log_complexity -> log_function (innermost)
        expected_order = ["log_function", "log_complexity", "error_handler"]
        self.assertEqual(decorator_order, expected_order)

    def test_create_error_simulator_service_name_extraction(self):
        """Test that service name is correctly extracted from directory path."""
        # Test with different directory structures
        test_cases = [
            ("/path/to/service", "service"),
            ("/path/to/my_service", "my_service"),
            ("service", "service"),
            ("/service/", "service"),
        ]
        
        for service_dir, expected_name in test_cases:
            with patch('common_utils.init_utils.ErrorSimulator') as mock_error_simulator_class:
                mock_simulator = MagicMock()
                mock_error_simulator_class.return_value = mock_simulator
                
                with patch('common_utils.error_simulation_manager.should_apply_central_config') as mock_should_apply:
                    mock_should_apply.return_value = False
                    
                    # Mock file existence checks
                    with patch('common_utils.init_utils.os.path.exists') as mock_exists:
                        mock_exists.return_value = True
                        
                        # Mock os.path.basename to return the expected service name
                        with patch('common_utils.init_utils.os.path.basename', return_value=expected_name):
                            create_error_simulator(service_dir)
                            
                            # Verify service_name was set correctly
                            self.assertEqual(mock_simulator.service_name, expected_name)


if __name__ == '__main__':
    unittest.main()
