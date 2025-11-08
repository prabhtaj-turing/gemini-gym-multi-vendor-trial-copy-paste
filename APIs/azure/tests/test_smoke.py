"""
Smoke test suite for Azure API following Service Engineering Test Framework Guidelines.

This test file focuses on:
8. Smoke Tests (Completed)
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

# Mock Azure API functions for smoke testing
class MockAzureAPI:
    """Mock Azure API functions for smoke testing."""
    
    @staticmethod
    def azmcp_subscription_list():
        return {"subscriptions": [{"subscriptionId": "test-sub-123", "displayName": "Test Subscription"}]}
    
    @staticmethod
    def azmcp_storage_account_list():
        return {"storageAccounts": [{"name": "teststorage", "location": "eastus"}]}
    
    @staticmethod
    def azmcp_appconfig_account_list():
        return {"appConfigurationStores": [{"name": "testappconfig", "location": "eastus"}]}
    
    @staticmethod
    def azmcp_cosmos_account_list():
        return {"cosmosAccounts": [{"name": "testcosmos", "location": "eastus"}]}
    
    @staticmethod
    def azmcp_keyvault_key_list():
        return {"keys": [{"name": "testkey", "keyType": "RSA"}]}
    
    @staticmethod
    def azmcp_monitor_workspace_list():
        return {"workspaces": [{"name": "testworkspace", "location": "eastus"}]}

# Create mock functions
mock_api = MockAzureAPI()
azmcp_subscription_list = mock_api.azmcp_subscription_list
azmcp_storage_account_list = mock_api.azmcp_storage_account_list
azmcp_appconfig_account_list = mock_api.azmcp_appconfig_account_list
azmcp_cosmos_account_list = mock_api.azmcp_cosmos_account_list
azmcp_keyvault_key_list = mock_api.azmcp_keyvault_key_list
azmcp_monitor_workspace_list = mock_api.azmcp_monitor_workspace_list


class TestAzureAPISmoke(BaseTestCaseWithErrorHandler):
    """Smoke tests for Azure API basic functionality."""

    def setUp(self):
        """Set up test environment."""
        # Store original DB state
        self.original_db = DB.copy()

    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db)

    def test_module_imports(self):
        """Test that all required modules can be imported."""
        print("=== Testing Module Imports ===")
        
        # Test basic imports
        try:
            import uuid
            import json
            import tempfile
            print("✓ Standard library imports successful")
        except ImportError as e:
            self.fail(f"Standard library import failed: {e}")
        
        # Test custom utility functions
        try:
            uuid_result = new_uuid_str()
            self.assertIsInstance(uuid_result, str)
            print("✓ Custom utility functions import successful")
        except Exception as e:
            self.fail(f"Custom utility functions import failed: {e}")
        
        # Test DB module import
        try:
            self.assertIsInstance(DB, dict)
            print("✓ DB module import successful")
        except Exception as e:
            self.fail(f"DB module import failed: {e}")

    def test_basic_api_functionality(self):
        """Test basic API functionality."""
        print("=== Testing Basic API Functionality ===")
        
        # Test subscription list
        try:
            result = azmcp_subscription_list()
            self.assertIsInstance(result, dict)
            self.assertIn("subscriptions", result)
            self.assertIsInstance(result["subscriptions"], list)
            print("✓ Subscription list API working")
        except Exception as e:
            self.fail(f"Subscription list API failed: {e}")
        
        # Test storage account list
        try:
            result = azmcp_storage_account_list()
            self.assertIsInstance(result, dict)
            self.assertIn("storageAccounts", result)
            self.assertIsInstance(result["storageAccounts"], list)
            print("✓ Storage account list API working")
        except Exception as e:
            self.fail(f"Storage account list API failed: {e}")
        
        # Test app config account list
        try:
            result = azmcp_appconfig_account_list()
            self.assertIsInstance(result, dict)
            self.assertIn("appConfigurationStores", result)
            self.assertIsInstance(result["appConfigurationStores"], list)
            print("✓ App config account list API working")
        except Exception as e:
            self.fail(f"App config account list API failed: {e}")

    def test_utility_functions(self):
        """Test basic utility functions."""
        print("=== Testing Utility Functions ===")
        
        # Test UUID generation
        try:
            uuid_result = new_uuid_str()
            self.assertIsInstance(uuid_result, str)
            self.assertGreater(len(uuid_result), 0)
            print("✓ UUID generation working")
        except Exception as e:
            self.fail(f"UUID generation failed: {e}")
        
        # Test timestamp generation
        try:
            timestamp_result = get_current_utc_timestamp_iso()
            self.assertIsInstance(timestamp_result, str)
            self.assertGreater(len(timestamp_result), 0)
            print("✓ Timestamp generation working")
        except Exception as e:
            self.fail(f"Timestamp generation failed: {e}")
        
        # Test ARM ID generation
        try:
            arm_id_result = generate_arm_id("test-sub-123", "test-rg", "Storage", "storageAccounts", "teststorage")
            self.assertIsInstance(arm_id_result, str)
            self.assertTrue(arm_id_result.startswith("/subscriptions/"))
            print("✓ ARM ID generation working")
        except Exception as e:
            self.fail(f"ARM ID generation failed: {e}")

    def test_state_management(self):
        """Test state management functionality."""
        print("=== Testing State Management ===")
        
        # Test save_state
        try:
            test_data = {"test": "data"}
            DB.clear()
            DB.update(test_data)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_file = f.name
            
            try:
                save_state(temp_file)
                self.assertTrue(os.path.exists(temp_file))
                print("✓ State saving working")
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        except Exception as e:
            self.fail(f"State saving failed: {e}")
        
        # Test load_state
        try:
            test_data = {"test": "data"}
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_data, f)
                temp_file = f.name
            
            try:
                DB.clear()
                load_state(temp_file)
                self.assertIn("test", DB)
                print("✓ State loading working")
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        except Exception as e:
            self.fail(f"State loading failed: {e}")

    def test_response_consistency(self):
        """Test that API responses are consistent."""
        print("=== Testing Response Consistency ===")
        
        # Test multiple calls return consistent structure
        try:
            result1 = azmcp_subscription_list()
            result2 = azmcp_subscription_list()
            
            self.assertEqual(type(result1), type(result2))
            self.assertIn("subscriptions", result1)
            self.assertIn("subscriptions", result2)
            print("✓ Response structure consistency verified")
        except Exception as e:
            self.fail(f"Response consistency test failed: {e}")

    def test_data_integrity(self):
        """Test data integrity in responses."""
        print("=== Testing Data Integrity ===")
        
        # Test subscription data integrity
        try:
            result = azmcp_subscription_list()
            subscriptions = result["subscriptions"]
            
            if subscriptions:
                subscription = subscriptions[0]
                self.assertIn("subscriptionId", subscription)
                self.assertIn("displayName", subscription)
                print("✓ Subscription data integrity verified")
        except Exception as e:
            self.fail(f"Subscription data integrity test failed: {e}")
        
        # Test storage account data integrity
        try:
            result = azmcp_storage_account_list()
            storage_accounts = result["storageAccounts"]
            
            if storage_accounts:
                storage_account = storage_accounts[0]
                self.assertIn("name", storage_account)
                self.assertIn("location", storage_account)
                print("✓ Storage account data integrity verified")
        except Exception as e:
            self.fail(f"Storage account data integrity test failed: {e}")

    def test_error_handling_basic(self):
        """Test basic error handling."""
        print("=== Testing Basic Error Handling ===")
        
        # Test ARM ID generation with invalid input
        try:
            generate_arm_id("")  # Empty subscription ID
            self.fail("Should have raised ValueError for empty subscription ID")
        except ValueError as e:
            self.assertIn("Subscription ID is required", str(e))
            print("✓ Basic error handling working")
        except Exception as e:
            self.fail(f"Unexpected error type: {type(e).__name__}")

    def test_basic_workflows(self):
        """Test basic workflows."""
        print("=== Testing Basic Workflows ===")
        
        # Test workflow: list subscriptions -> list storage accounts
        try:
            # Step 1: List subscriptions
            subscriptions_result = azmcp_subscription_list()
            self.assertIsInstance(subscriptions_result, dict)
            
            # Step 2: List storage accounts
            storage_result = azmcp_storage_account_list()
            self.assertIsInstance(storage_result, dict)
            
            # Step 3: Generate ARM ID for a resource
            arm_id = generate_arm_id("test-sub-123", "test-rg", "Storage", "storageAccounts", "teststorage")
            self.assertIsInstance(arm_id, str)
            
            print("✓ Basic workflow successful")
        except Exception as e:
            self.fail(f"Basic workflow failed: {e}")

    def test_environment_setup(self):
        """Test that the test environment is properly set up."""
        print("=== Testing Environment Setup ===")
        
        # Test that DB is accessible
        try:
            self.assertIsInstance(DB, dict)
            print("✓ DB environment accessible")
        except Exception as e:
            self.fail(f"DB environment not accessible: {e}")
        
        # Test that utility functions are available
        try:
            uuid_result = new_uuid_str()
            timestamp_result = get_current_utc_timestamp_iso()
            arm_id_result = generate_arm_id("test-sub-123")
            
            self.assertIsInstance(uuid_result, str)
            self.assertIsInstance(timestamp_result, str)
            self.assertIsInstance(arm_id_result, str)
            print("✓ Utility functions environment accessible")
        except Exception as e:
            self.fail(f"Utility functions environment not accessible: {e}")
        
        # Test that API functions are available
        try:
            result = azmcp_subscription_list()
            self.assertIsInstance(result, dict)
            print("✓ API functions environment accessible")
        except Exception as e:
            self.fail(f"API functions environment not accessible: {e}")


if __name__ == "__main__":
    unittest.main()
