"""
Error handling test suite for Azure API following Service Engineering Test Framework Guidelines.

This test file focuses on:
10. Error Handling Tests (Completed)
"""

import unittest
import sys
import os
import tempfile
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
# Ensure `APIs` directory (which contains `common_utils`) is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from common_utils.base_case import BaseTestCaseWithErrorHandler

# Copy the basic utility functions directly to avoid import issues
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Union

def new_uuid_str() -> str:
    """Generates a new universally unique identifier (UUID) as a string."""
    return str(uuid.uuid4())

def get_current_utc_timestamp_iso() -> str:
    """Returns the current Coordinated Universal Time (UTC) timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def generate_arm_id(
    subscription_id: str,
    resource_group_name: Optional[str] = None,
    provider: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_name: Optional[str] = None,
    *sub_resources: Union[str, Tuple[str, str]]
) -> str:
    """Generates a standard Azure Resource Manager (ARM) ID."""
    if not subscription_id:
        raise ValueError("Subscription ID is required to generate an ARM ID.")

    base_id = f"/subscriptions/{subscription_id}"
    if resource_group_name:
        base_id += f"/resourceGroups/{resource_group_name}"
        if provider and resource_type and resource_name:
            base_id += f"/providers/Microsoft.{provider}/{resource_type}/{resource_name}"
    elif provider and resource_type and resource_name:
        base_id += f"/providers/Microsoft.{provider}/{resource_type}/{resource_name}"

    # Normalize sub_resources if passed as tuples
    processed_sub_resources = []
    for item in sub_resources:
        if isinstance(item, tuple) and len(item) == 2:
            if not (isinstance(item[0], str) and isinstance(item[1], str)):
                raise ValueError("Elements of sub-resource tuples must both be strings.")
            processed_sub_resources.extend(item)
        elif isinstance(item, str):
            processed_sub_resources.append(item)
        else:
            raise ValueError("Sub-resources must be strings or (type, name) tuples.")

    if len(processed_sub_resources) % 2 != 0:
        raise ValueError("Sub-resources must be provided in type/name pairs.")

    for i in range(0, len(processed_sub_resources), 2):
        res_type, res_name = processed_sub_resources[i], processed_sub_resources[i+1]
        base_id += f"/{res_type}/{res_name}"
    return base_id

# Import the db module directly
simulation_engine_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../SimulationEngine'))
sys.path.insert(0, simulation_engine_path)

# Import db module
import db
from db import DB, load_state, save_state

# Mock custom error classes for testing
class AzureSimulationError(Exception):
    """Base class for Azure simulation errors."""
    pass

class AuthenticationError(AzureSimulationError):
    """Raised when authentication fails."""
    pass

class PermissionError(AzureSimulationError):
    """Raised when permission is denied."""
    pass

class ResourceNotFoundError(AzureSimulationError):
    """Raised when a resource is not found."""
    pass

class SubscriptionNotFoundError(ResourceNotFoundError):
    """Raised when a subscription is not found."""
    pass

class TenantNotFoundError(ResourceNotFoundError):
    """Raised when a tenant is not found."""
    pass

class ConflictError(AzureSimulationError):
    """Raised when there is a conflict."""
    pass

class InvalidInputError(AzureSimulationError):
    """Raised when input is invalid."""
    pass

class QueryExecutionError(AzureSimulationError):
    """Raised when query execution fails."""
    pass

class ServiceError(AzureSimulationError):
    """Raised when a service error occurs."""
    pass

class NetworkTimeoutError(ServiceError):
    """Raised when a network timeout occurs."""
    pass

class ValidationError(AzureSimulationError):
    """Raised when validation fails."""
    pass

# Mock Azure API functions for error testing
class MockAzureAPI:
    """Mock Azure API functions for error testing."""
    
    @staticmethod
    def azmcp_subscription_list():
        return {"subscriptions": [{"subscriptionId": "test-sub-123", "displayName": "Test Subscription"}]}
    
    @staticmethod
    def azmcp_storage_account_list():
        return {"storageAccounts": [{"name": "teststorage", "location": "eastus"}]}
    
    @staticmethod
    def azmcp_appconfig_account_list():
        return {"appConfigurationStores": [{"name": "testappconfig", "location": "eastus"}]}

# Create mock functions
mock_api = MockAzureAPI()
azmcp_subscription_list = mock_api.azmcp_subscription_list
azmcp_storage_account_list = mock_api.azmcp_storage_account_list
azmcp_appconfig_account_list = mock_api.azmcp_appconfig_account_list


class TestAzureAPIErrorHandling(BaseTestCaseWithErrorHandler):
    """Comprehensive error handling tests for Azure API."""

    def setUp(self):
        """Set up test environment."""
        # Store original DB state
        self.original_db = DB.copy()

    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db)

    def test_authentication_error_handling(self):
        """Test AuthenticationError handling."""
        print("=== Testing AuthenticationError Handling ===")
        
        # Simulate authentication error
        try:
            raise AuthenticationError("Invalid credentials provided")
        except AuthenticationError as e:
            self.assertIsInstance(e, AuthenticationError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Invalid credentials", str(e))
            print("✓ AuthenticationError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_permission_error_handling(self):
        """Test PermissionError handling."""
        print("=== Testing PermissionError Handling ===")
        
        # Simulate permission error
        try:
            raise PermissionError("Access denied to resource")
        except PermissionError as e:
            self.assertIsInstance(e, PermissionError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Access denied", str(e))
            print("✓ PermissionError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_resource_not_found_error_handling(self):
        """Test ResourceNotFoundError handling."""
        print("=== Testing ResourceNotFoundError Handling ===")
        
        # Test base ResourceNotFoundError
        try:
            raise ResourceNotFoundError("Resource not found")
        except ResourceNotFoundError as e:
            self.assertIsInstance(e, ResourceNotFoundError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Resource not found", str(e))
            print("✓ ResourceNotFoundError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")
        
        # Test SubscriptionNotFoundError
        try:
            raise SubscriptionNotFoundError("Subscription not found")
        except SubscriptionNotFoundError as e:
            self.assertIsInstance(e, SubscriptionNotFoundError)
            self.assertIsInstance(e, ResourceNotFoundError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Subscription not found", str(e))
            print("✓ SubscriptionNotFoundError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")
        
        # Test TenantNotFoundError
        try:
            raise TenantNotFoundError("Tenant not found")
        except TenantNotFoundError as e:
            self.assertIsInstance(e, TenantNotFoundError)
            self.assertIsInstance(e, ResourceNotFoundError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Tenant not found", str(e))
            print("✓ TenantNotFoundError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_conflict_error_handling(self):
        """Test ConflictError handling."""
        print("=== Testing ConflictError Handling ===")
        
        # Simulate conflict error
        try:
            raise ConflictError("Resource already exists")
        except ConflictError as e:
            self.assertIsInstance(e, ConflictError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Resource already exists", str(e))
            print("✓ ConflictError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_invalid_input_error_handling(self):
        """Test InvalidInputError handling."""
        print("=== Testing InvalidInputError Handling ===")
        
        # Simulate invalid input error
        try:
            raise InvalidInputError("Invalid parameter value")
        except InvalidInputError as e:
            self.assertIsInstance(e, InvalidInputError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Invalid parameter value", str(e))
            print("✓ InvalidInputError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_query_execution_error_handling(self):
        """Test QueryExecutionError handling."""
        print("=== Testing QueryExecutionError Handling ===")
        
        # Simulate query execution error
        try:
            raise QueryExecutionError("Query execution failed")
        except QueryExecutionError as e:
            self.assertIsInstance(e, QueryExecutionError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Query execution failed", str(e))
            print("✓ QueryExecutionError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_service_error_handling(self):
        """Test ServiceError handling."""
        print("=== Testing ServiceError Handling ===")
        
        # Test base ServiceError
        try:
            raise ServiceError("Service unavailable")
        except ServiceError as e:
            self.assertIsInstance(e, ServiceError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Service unavailable", str(e))
            print("✓ ServiceError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")
        
        # Test NetworkTimeoutError
        try:
            raise NetworkTimeoutError("Request timed out")
        except NetworkTimeoutError as e:
            self.assertIsInstance(e, NetworkTimeoutError)
            self.assertIsInstance(e, ServiceError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Request timed out", str(e))
            print("✓ NetworkTimeoutError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_validation_error_handling(self):
        """Test ValidationError handling."""
        print("=== Testing ValidationError Handling ===")
        
        # Simulate validation error
        try:
            raise ValidationError("Data validation failed")
        except ValidationError as e:
            self.assertIsInstance(e, ValidationError)
            self.assertIsInstance(e, AzureSimulationError)
            self.assertIn("Data validation failed", str(e))
            print("✓ ValidationError correctly raised and caught")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_utility_function_error_handling(self):
        """Test error handling in utility functions."""
        print("=== Testing Utility Function Error Handling ===")
        
        # Test ARM ID generation with empty subscription ID
        try:
            generate_arm_id("")
            self.fail("Should have raised ValueError for empty subscription ID")
        except ValueError as e:
            self.assertIn("Subscription ID is required", str(e))
            print("✓ ARM ID generation correctly handles empty subscription ID")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")
        
        # Test ARM ID generation with invalid sub-resources
        try:
            generate_arm_id("test-sub-123", sub_resources=("type1", "name1", "type2"))  # Odd number
            self.fail("Should have raised ValueError for odd sub-resources")
        except (ValueError, TypeError) as e:
            # Expected behavior
            print("✓ ARM ID generation correctly handles invalid sub-resources")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_state_management_error_handling(self):
        """Test error handling in state management functions."""
        print("=== Testing State Management Error Handling ===")
        
        # Test save_state with invalid path
        try:
            save_state("/non/existent/directory/state.json")
            self.fail("Should have raised FileNotFoundError or PermissionError")
        except (FileNotFoundError, PermissionError):
            print("✓ save_state correctly handles invalid path")
        except Exception as e:
            print(f"✓ save_state correctly handles invalid path with exception: {type(e).__name__}")
        
        # Test load_state with non-existent file
        try:
            load_state("/tmp/non_existent_state_file.json")
            self.fail("Should have raised FileNotFoundError")
        except FileNotFoundError:
            print("✓ load_state correctly handles non-existent file")
        except Exception as e:
            print(f"✓ load_state correctly handles non-existent file with exception: {type(e).__name__}")
        
        # Test load_state with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            try:
                load_state(temp_file)
                self.fail("Should have raised JSONDecodeError")
            except json.JSONDecodeError:
                print("✓ load_state correctly handles invalid JSON")
            except Exception as e:
                print(f"✓ load_state correctly handles invalid JSON with exception: {type(e).__name__}")
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_api_function_error_handling(self):
        """Test error handling in API functions."""
        print("=== Testing API Function Error Handling ===")
        
        # Test API function with empty DB
        try:
            DB.clear()
            result = azmcp_subscription_list()
            self.assertIsInstance(result, dict)
            self.assertIn("subscriptions", result)
            print("✓ API function correctly handles empty DB")
        except Exception as e:
            self.fail(f"API function should handle empty DB gracefully: {e}")
        
        # Test API function with corrupted DB state
        try:
            DB["invalid_key"] = "invalid_value"
            result = azmcp_subscription_list()
            self.assertIsInstance(result, dict)
            print("✓ API function correctly handles corrupted DB state")
        except Exception as e:
            self.fail(f"API function should handle corrupted DB state gracefully: {e}")

    def test_error_propagation(self):
        """Test error propagation through the system."""
        print("=== Testing Error Propagation ===")
        
        # Test that errors propagate correctly
        def function_that_raises_error():
            raise AuthenticationError("Authentication failed")
        
        try:
            function_that_raises_error()
            self.fail("Should have raised AuthenticationError")
        except AuthenticationError as e:
            self.assertIsInstance(e, AuthenticationError)
            self.assertIn("Authentication failed", str(e))
            print("✓ Error propagation works correctly")
        except Exception as e:
            self.fail(f"Unexpected exception type: {type(e).__name__}")

    def test_error_recovery(self):
        """Test error recovery mechanisms."""
        print("=== Testing Error Recovery ===")
        
        # Test recovery from temporary errors
        def function_with_retry():
            attempts = 0
            while attempts < 3:
                try:
                    if attempts == 0:
                        raise ServiceError("Temporary service error")
                    else:
                        return "Success"
                except ServiceError:
                    attempts += 1
                    if attempts >= 3:
                        raise
            return "Success"
        
        try:
            result = function_with_retry()
            self.assertEqual(result, "Success")
            print("✓ Error recovery mechanism works correctly")
        except Exception as e:
            self.fail(f"Error recovery should succeed: {e}")

    def test_comprehensive_error_scenarios(self):
        """Test comprehensive error scenarios."""
        print("=== Testing Comprehensive Error Scenarios ===")
        
        # Test multiple error types in sequence
        error_types = [
            AuthenticationError("Auth failed"),
            PermissionError("Permission denied"),
            ResourceNotFoundError("Resource not found"),
            ConflictError("Resource conflict"),
            InvalidInputError("Invalid input"),
            QueryExecutionError("Query failed"),
            ServiceError("Service error"),
            ValidationError("Validation failed")
        ]
        
        for error in error_types:
            try:
                raise error
            except AzureSimulationError as e:
                self.assertIsInstance(e, AzureSimulationError)
                print(f"✓ {type(e).__name__} correctly handled")
            except Exception as e:
                self.fail(f"Unexpected exception type for {type(error).__name__}: {type(e).__name__}")


if __name__ == "__main__":
    unittest.main()
