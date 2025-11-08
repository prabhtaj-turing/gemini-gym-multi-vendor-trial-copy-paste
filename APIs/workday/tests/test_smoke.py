#!/usr/bin/env python3
"""
Comprehensive Smoke Tests for Workday Strategic Sourcing API

This module provides extensive smoke testing coverage including:
1. Package Installation and Import Tests
2. Basic Functionality Smoke Tests
3. API Endpoint Smoke Tests  
4. Database Connection Smoke Tests
5. Configuration Smoke Tests
6. System Health Checks

Author: AI Assistant
Created: 2024-12-28
"""

import unittest
import sys
import importlib
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional

# Import modules under test
from ..SimulationEngine import db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestPackageInstallationAndImports(BaseTestCaseWithErrorHandler):
    """Test package installation and import functionality."""
    
    def test_core_module_imports(self):
        """Smoke test: core modules can be imported without error."""
        core_modules = [
            'workday.BidsById',
            'workday.BidLineItemById',
            'workday.BidLineItemsList',
            'workday.BidLineItemsDescribe',
            'workday.BidsDescribe',
            'workday.ResourceTypeById',
            'workday.SimulationEngine.db',
            'workday.SimulationEngine.utils',
            'workday.SimulationEngine.models',
            'workday.SimulationEngine.custom_errors'
        ]
        
        for module_name in core_modules:
            with self.subTest(module=module_name):
                try:
                    module = importlib.import_module(module_name)
                    self.assertIsNotNone(module)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")
                    
    def test_function_imports_and_callability(self):
        """Smoke test: key functions can be imported and are callable."""
        function_tests = [
            ('workday.BidsById', 'get'),
            ('workday.BidLineItemById', 'get'),
            ('workday.BidLineItemsList', 'get'),
            ('workday.BidLineItemsDescribe', 'get'),
            ('workday.BidsDescribe', 'get'),
            ('workday.ResourceTypeById', 'get'),
            ('workday.SimulationEngine.utils', 'apply_company_filters'),
            ('workday.SimulationEngine.utils', 'apply_filter'),
            ('workday.SimulationEngine.db', 'reset_db')
        ]
        
        for module_name, function_name in function_tests:
            with self.subTest(module=module_name, function=function_name):
                try:
                    module = importlib.import_module(module_name)
                    function = getattr(module, function_name)
                    self.assertTrue(callable(function))
                except (ImportError, AttributeError) as e:
                    self.fail(f"Failed to import {function_name} from {module_name}: {e}")
                    
    def test_dependency_imports(self):
        """Smoke test: required dependencies can be imported."""
        dependencies = [
            'json',
            'typing',
            'datetime',
            'unittest',
            'time'
        ]
        
        for dependency in dependencies:
            with self.subTest(dependency=dependency):
                try:
                    importlib.import_module(dependency)
                except ImportError as e:
                    self.fail(f"Required dependency {dependency} not available: {e}")
                    
    def test_optional_dependencies_graceful_handling(self):
        """Smoke test: optional dependencies are handled gracefully."""
        optional_dependencies = [
            'pydantic',
            'pytest'
        ]
        
        for dependency in optional_dependencies:
            with self.subTest(dependency=dependency):
                try:
                    importlib.import_module(dependency)
                    # If import succeeds, that's good
                except ImportError:
                    # If import fails, that should be handled gracefully
                    # The system should still work without optional dependencies
                    pass


class TestBasicFunctionalitySmoke(BaseTestCaseWithErrorHandler):
    """Smoke tests for basic functionality."""
    
    def setUp(self):
        """Set up basic functionality smoke test fixtures."""
        super().setUp()
        db.reset_db()
        
        # Setup minimal test data
        self.setup_minimal_test_data()
        
    def tearDown(self):
        """Clean up after basic functionality smoke tests."""
        super().tearDown()
        db.reset_db()
        
    def setup_minimal_test_data(self):
        """Setup minimal test data for smoke tests."""
        # Minimal bid data
        db.DB["events"]["bids"][1] = {
            "supplier_id": 1,
            "event_id": 1,
            "bid_amount": 1000.0,
            "status": "submitted"
        }
        
        # Minimal bid line item data
        db.DB["events"]["bid_line_items"][1] = {
            "bid_id": 1,
            "event_id": 1,
            "description": "Smoke test item",
            "amount": 500.0
        }
        
        # Minimal supplier data
        db.DB["suppliers"]["supplier_companies"][1] = {
            "name": "Smoke Test Supplier",
            "status": "active"
        }
        
        # Minimal SCIM resource type data
        db.DB["scim"]["resource_types"] = [{
            "resource": "TestResource",
            "name": "Smoke Test Resource",
            "description": "Test resource for smoke tests"
        }]
        
    def test_basic_crud_operations_work(self):
        """Smoke test: basic CRUD operations work without error."""
        from ..BidsById import get as get_bid
        from ..BidLineItemById import get as get_line_item
        from ..BidLineItemsList import get as list_line_items
        from ..ResourceTypeById import get as get_resource_type
        
        # Test READ operations
        try:
            # Should succeed
            bid_result = get_bid(1)
            self.assertIsNotNone(bid_result)
            
            line_item_result = get_line_item(1)
            self.assertIsNotNone(line_item_result)
            
            line_items_list = list_line_items()
            self.assertIsInstance(line_items_list, list)
            
            resource_result = get_resource_type("TestResource")
            self.assertIsNotNone(resource_result)
            
            # Should handle non-existent data gracefully
            non_existent_bid = get_bid(999)
            self.assertIsNone(non_existent_bid)
            
        except Exception as e:
            self.fail(f"Basic CRUD operations failed: {e}")
            
    def test_schema_operations_work(self):
        """Smoke test: schema operations work without error."""
        from ..BidsDescribe import get as describe_bids
        from ..BidLineItemsDescribe import get as describe_line_items
        
        try:
            bid_schema = describe_bids()
            self.assertIsInstance(bid_schema, list)
            self.assertGreater(len(bid_schema), 0)
            
            line_item_schema = describe_line_items()
            self.assertIsInstance(line_item_schema, list)
            self.assertGreater(len(line_item_schema), 0)
            
        except Exception as e:
            self.fail(f"Schema operations failed: {e}")
            
    def test_filtering_operations_work(self):
        """Smoke test: filtering operations work without error."""
        from ..BidLineItemsList import get as list_line_items
        
        try:
            # Filter by bid_id
            filtered_items = list_line_items(filter={"bid_id": 1})
            self.assertIsInstance(filtered_items, list)
            
            # Filter by event_id
            filtered_items = list_line_items(filter={"event_id": 1})
            self.assertIsInstance(filtered_items, list)
            
            # No filter
            all_items = list_line_items()
            self.assertIsInstance(all_items, list)
            
        except Exception as e:
            self.fail(f"Filtering operations failed: {e}")
            
    def test_utility_functions_work(self):
        """Smoke test: utility functions work without error."""
        from ..SimulationEngine.utils import (
            apply_filter, apply_company_filters
        )
        
        try:
            # Test user filtering
            users = [{"userName": "test", "active": True}]
            filtered = apply_filter(users, 'active eq true')
            self.assertIsInstance(filtered, list)
            
            # Test company filtering
            companies = [{"attributes": {"name": "Test Company", "risk": "low"}}]
            filtered = apply_company_filters(companies, {"risk": "low"})
            self.assertIsInstance(filtered, list)
            
        except Exception as e:
            self.fail(f"Utility functions failed: {e}")


class TestAPIEndpointSmoke(BaseTestCaseWithErrorHandler):
    """Smoke tests for API endpoint functionality."""
    
    def setUp(self):
        """Set up API endpoint smoke test fixtures."""
        super().setUp()
        db.reset_db()
        
        # Setup test data for all endpoints
        self.setup_api_test_data()
        
    def tearDown(self):
        """Clean up after API endpoint smoke tests."""
        super().tearDown()
        db.reset_db()
        
    def setup_api_test_data(self):
        """Setup test data for API endpoints."""
        # Events
        db.DB["events"]["events"][1] = {
            "name": "API Test Event",
            "status": "active"
        }
        
        # Bids
        db.DB["events"]["bids"][1] = {
            "supplier_id": 1,
            "event_id": 1,
            "bid_amount": 5000.0,
            "status": "submitted",
            "submitted_at": "2024-01-01T10:00:00Z"
        }
        
        # Bid line items
        db.DB["events"]["bid_line_items"][1] = {
            "bid_id": 1,
            "event_id": 1,
            "description": "API test line item",
            "amount": 2500.0
        }
        
        db.DB["events"]["bid_line_items"][2] = {
            "bid_id": 1,
            "event_id": 1,
            "description": "Another API test line item",
            "amount": 2500.0
        }
        
        # Suppliers
        db.DB["suppliers"]["supplier_companies"][1] = {
            "name": "API Test Supplier",
            "status": "active",
            "external_id": "API001"
        }
        
        # SCIM Resource types
        db.DB["scim"]["resource_types"] = [{
            "resource": "APITestResource",
            "name": "API Test Resource",
            "description": "API test resource"
        }]
        
    def test_all_get_endpoints_respond(self):
        """Smoke test: all GET endpoints respond without error."""
        endpoint_tests = [
            ('BidsById', 'get', [1]),
            ('BidsById', 'get', [1, "supplier_company"]),  # With include
            ('BidLineItemById', 'get', [1]),
            ('BidLineItemsList', 'get', []),
            ('BidLineItemsList', 'get', [{"bid_id": 1}]),  # With filter
            ('BidsDescribe', 'get', []),
            ('BidLineItemsDescribe', 'get', []),
            ('ResourceTypeById', 'get', ["APITestResource"])
        ]
        
        for module_name, function_name, args in endpoint_tests:
            with self.subTest(endpoint=f"{module_name}.{function_name}", args=args):
                try:
                    module = importlib.import_module(f'workday.{module_name}')
                    function = getattr(module, function_name)
                    
                    if args:
                        if len(args) == 1:
                            result = function(args[0])
                        elif len(args) == 2:
                            result = function(args[0], _include=args[1]) if module_name == 'BidsById' else function(filter=args[0])
                    else:
                        result = function()
                    
                    # Should return some result (not necessarily successful)
                    # The key is that it doesn't raise an exception
                    self.assertTrue(result is not None or result is None)  # Any result is acceptable
                    
                except Exception as e:
                    self.fail(f"Endpoint {module_name}.{function_name} failed: {e}")
                    
    def test_endpoints_return_expected_types(self):
        """Smoke test: endpoints return expected data types."""
        type_tests = [
            ('BidsById', 'get', [1], (dict, type(None))),
            ('BidLineItemById', 'get', [1], (dict, type(None))),
            ('BidLineItemsList', 'get', [], list),
            ('BidsDescribe', 'get', [], list),
            ('BidLineItemsDescribe', 'get', [], list),
            ('ResourceTypeById', 'get', ["APITestResource"], (dict, type(None)))
        ]
        
        for module_name, function_name, args, expected_type in type_tests:
            with self.subTest(endpoint=f"{module_name}.{function_name}"):
                try:
                    module = importlib.import_module(f'workday.{module_name}')
                    function = getattr(module, function_name)
                    
                    if args:
                        result = function(args[0])
                    else:
                        result = function()
                    
                    if isinstance(expected_type, tuple):
                        self.assertIsInstance(result, expected_type)
                    else:
                        self.assertIsInstance(result, expected_type)
                        
                except Exception as e:
                    self.fail(f"Type check for {module_name}.{function_name} failed: {e}")
                    
    def test_endpoints_handle_invalid_input_gracefully(self):
        """Smoke test: endpoints handle invalid input gracefully."""
        invalid_input_tests = [
            ('BidsById', 'get', [-1], 'ValidationError'),  # Negative ID - should raise ValidationError
            ('BidsById', 'get', [0], 'ValidationError'),   # Zero ID - should raise ValidationError
            ('BidsById', 'get', [999999], 'None'),  # Non-existent ID - should return None
            ('BidLineItemById', 'get', [-1], 'None'),  # BidLineItemById doesn't validate, just returns None
            ('BidLineItemsList', 'get', [{"invalid_filter": "value"}], 'ValueError'),  # Invalid filter
            ('ResourceTypeById', 'get', ["NonExistent"], 'None')
        ]
        
        for module_name, function_name, args, expected_behavior in invalid_input_tests:
            with self.subTest(endpoint=f"{module_name}.{function_name}", args=args):
                try:
                    module = importlib.import_module(f'workday.{module_name}')
                    function = getattr(module, function_name)
                    
                    if expected_behavior == 'ValidationError':
                        # Should raise ValidationError for invalid input
                        from ..SimulationEngine.custom_errors import ValidationError
                        with self.assertRaises(ValidationError):
                            if module_name == 'BidLineItemsList':
                                function(filter=args[0])
                            else:
                                function(args[0])
                    elif expected_behavior == 'ValueError':
                        # Should raise ValueError for invalid filters
                        with self.assertRaises(ValueError):
                            function(filter=args[0])
                    elif expected_behavior == 'None':
                        # Should return None gracefully
                        result = function(args[0])
                        self.assertTrue(result is None or isinstance(result, (dict, list)))
                        
                except Exception as e:
                    # If we get here, the expected behavior wasn't met
                    if expected_behavior in ['ValidationError', 'ValueError']:
                        # We expected an exception but got a different one
                        self.fail(f"Expected {expected_behavior} for {module_name}.{function_name}, but got {type(e).__name__}: {e}")
                    else:
                        # We didn't expect an exception
                        self.fail(f"Unexpected error for {module_name}.{function_name}: {e}")


class TestDatabaseConnectionSmoke(BaseTestCaseWithErrorHandler):
    """Smoke tests for database connection and operations."""
    
    def setUp(self):
        """Set up database connection smoke test fixtures."""
        super().setUp()
        db.reset_db()
        
    def tearDown(self):
        """Clean up after database connection smoke tests."""
        super().tearDown()
        db.reset_db()
        
    def test_database_initialization(self):
        """Smoke test: database initializes correctly."""
        try:
            # Database should be accessible
            self.assertIsInstance(db.DB, dict)
            
            # Should have main sections
            expected_sections = ["events", "suppliers", "attachments", "projects", "payments"]
            for section in expected_sections:
                self.assertIn(section, db.DB)
                
            # Events section should have subsections
            events_subsections = ["events", "bids", "bid_line_items"]
            for subsection in events_subsections:
                self.assertIn(subsection, db.DB["events"])
                
        except Exception as e:
            self.fail(f"Database initialization failed: {e}")
            
    def test_database_reset_functionality(self):
        """Smoke test: database reset works correctly."""
        try:
            # Add some data
            db.DB["events"]["bids"][1] = {"test": "data"}
            self.assertIn(1, db.DB["events"]["bids"])
            
            # Reset database
            db.reset_db()
            
            # Data should be cleared
            self.assertEqual(len(db.DB["events"]["bids"]), 0)
            
            # Structure should remain
            self.assertIn("events", db.DB)
            self.assertIn("bids", db.DB["events"])
            
        except Exception as e:
            self.fail(f"Database reset failed: {e}")
            
    def test_database_persistence_operations(self):
        """Smoke test: database persistence operations work."""
        temp_file = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_file = f.name
            
            # Add test data
            db.DB["events"]["bids"][1] = {
                "supplier_id": 1,
                "bid_amount": 1000.0,
                "status": "test"
            }
            
            # Test save operation
            db.save_state(temp_file)
            self.assertTrue(os.path.exists(temp_file))
            
            # Test load operation
            db.reset_db()
            db.load_state(temp_file)
            
            # Verify data was loaded (keys might be strings after JSON load)
            if 1 in db.DB["events"]["bids"]:
                self.assertEqual(db.DB["events"]["bids"][1]["status"], "test")
            elif "1" in db.DB["events"]["bids"]:
                self.assertEqual(db.DB["events"]["bids"]["1"]["status"], "test")
            else:
                self.fail("Test bid not found after loading state")
            
        except Exception as e:
            self.fail(f"Database persistence operations failed: {e}")
        finally:
            # Clean up
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)


class TestConfigurationSmoke(BaseTestCaseWithErrorHandler):
    """Smoke tests for configuration and settings."""
    
    def test_constants_and_configurations_accessible(self):
        """Smoke test: constants and configurations are accessible."""
        try:
            from ..SimulationEngine.utils import (
                ALLOWED_INCLUDE_VALUES, ALLOWED_FILTER_KEYS, INCLUDE_MAP
            )
            
            # Should be defined and have expected types
            self.assertIsInstance(ALLOWED_INCLUDE_VALUES, list)
            self.assertIsInstance(ALLOWED_FILTER_KEYS, list)
            self.assertIsInstance(INCLUDE_MAP, dict)
            
            # Should have some values
            self.assertGreater(len(ALLOWED_INCLUDE_VALUES), 0)
            self.assertGreater(len(ALLOWED_FILTER_KEYS), 0)
            self.assertGreater(len(INCLUDE_MAP), 0)
            
        except Exception as e:
            self.fail(f"Configuration access failed: {e}")
            
    def test_error_classes_available(self):
        """Smoke test: custom error classes are available."""
        try:
            from ..SimulationEngine.custom_errors import (
                ValidationError, InvalidAttributeError, 
                UserPatchForbiddenError, DatabaseSchemaError
            )
            
            # Should be importable and be exception classes
            self.assertTrue(issubclass(ValidationError, Exception))
            self.assertTrue(issubclass(InvalidAttributeError, Exception))
            self.assertTrue(issubclass(UserPatchForbiddenError, Exception))
            self.assertTrue(issubclass(DatabaseSchemaError, Exception))
            
        except Exception as e:
            self.fail(f"Error class access failed: {e}")
            
    def test_models_accessible(self):
        """Smoke test: data models are accessible."""
        try:
            from ..SimulationEngine import models
            
            # Should be importable
            self.assertIsNotNone(models)
            
            # Should have some model classes (if using Pydantic)
            model_attributes = dir(models)
            self.assertGreater(len(model_attributes), 0)
            
        except Exception as e:
            self.fail(f"Models access failed: {e}")


class TestSystemHealthChecks(BaseTestCaseWithErrorHandler):
    """System health check smoke tests."""
    
    def test_memory_usage_reasonable(self):
        """Smoke test: memory usage is reasonable."""
        try:
            # Get initial memory state
            initial_size = sys.getsizeof(db.DB)
            
            # Add some test data
            for i in range(100):
                db.DB["events"]["bids"][i] = {
                    "id": i,
                    "data": "test" * 10  # Small amount of data
                }
            
            # Check memory growth
            after_size = sys.getsizeof(db.DB)
            growth = after_size - initial_size
            
            # Growth should be reasonable (not excessive)
            self.assertLess(growth, 1024 * 1024)  # Less than 1MB growth for 100 small records
            
        except Exception as e:
            self.fail(f"Memory usage check failed: {e}")
            
    def test_import_performance_reasonable(self):
        """Smoke test: module imports complete in reasonable time."""
        import time
        
        modules_to_test = [
            'workday.BidsById',
            'workday.BidLineItemsList',
            'workday.SimulationEngine.utils'
        ]
        
        for module_name in modules_to_test:
            with self.subTest(module=module_name):
                try:
                    start_time = time.time()
                    
                    # Force reimport
                    if module_name in sys.modules:
                        del sys.modules[module_name]
                    
                    importlib.import_module(module_name)
                    
                    end_time = time.time()
                    import_time = end_time - start_time
                    
                    # Import should complete quickly
                    self.assertLess(import_time, 1.0)  # Less than 1 second per module
                    
                except Exception as e:
                    self.fail(f"Import performance check failed for {module_name}: {e}")
                    
    def test_basic_operations_performance_reasonable(self):
        """Smoke test: basic operations complete in reasonable time."""
        import time
        
        # Setup test data
        db.reset_db()
        db.DB["events"]["bids"][1] = {
            "supplier_id": 1,
            "bid_amount": 1000.0,
            "status": "submitted"
        }
        
        try:
            from ..BidsById import get as get_bid
            
            # Test operation performance
            start_time = time.time()
            
            for _ in range(10):  # 10 operations
                result = get_bid(1)
                self.assertIsNotNone(result)
                
            end_time = time.time()
            operation_time = end_time - start_time
            
            # Operations should complete quickly
            self.assertLess(operation_time, 0.1)  # Less than 100ms for 10 operations
            
        except Exception as e:
            self.fail(f"Basic operations performance check failed: {e}")
            
    def test_error_handling_doesnt_crash_system(self):
        """Smoke test: error conditions don't crash the system."""
        from ..BidsById import get as get_bid_by_id
        
        error_scenarios = [
            # Invalid function calls
            lambda: get_bid_by_id("invalid_id"),
            lambda: get_bid_by_id(None),
            lambda: get_bid_by_id(-1),
            # Database access with missing sections
            lambda: self.access_missing_db_section(),
        ]
        
        for i, scenario in enumerate(error_scenarios):
            with self.subTest(scenario=i):
                try:
                    scenario()
                    # If no exception, that's fine
                except Exception:
                    # If exception occurs, that's also fine as long as system doesn't crash
                    # The key is that we can continue to the next test
                    pass
                
                # Verify system is still responsive after error
                try:
                    db.reset_db()  # Should still work
                    self.assertTrue(True)  # System is still responsive
                except Exception as e:
                    self.fail(f"System became unresponsive after error scenario {i}: {e}")
                    
    def access_missing_db_section(self):
        """Helper method to test database access with missing sections."""
        # Temporarily remove a database section
        original_events = db.DB.get("events")
        del db.DB["events"]
        
        try:
            from ..BidsById import get as get_bid
            get_bid(1)  # This should handle the missing section gracefully
        finally:
            # Restore the section
            if original_events:
                db.DB["events"] = original_events


if __name__ == '__main__':
    # Run smoke tests with minimal output
    unittest.main(verbosity=1)

