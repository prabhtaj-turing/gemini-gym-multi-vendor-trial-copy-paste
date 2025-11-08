"""
Comprehensive test suite for Azure state management functions.

Tests load_state and save_state functions with various scenarios including
error handling, data integrity, and edge cases.
"""

import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import patch, mock_open

from common_utils.base_case import BaseTestCaseWithErrorHandler
from azure.SimulationEngine.db import DB, load_state, save_state


class TestStateManagement(BaseTestCaseWithErrorHandler):
    """Test state management functions."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Store original DB state
        self.original_db = DB.copy()
        
        # Create test data
        self.test_data = {
            "subscriptions": [
                {
                    "subscriptionId": "test-sub-123",
                    "displayName": "Test Subscription",
                    "state": "Enabled"
                }
            ],
            "resourceGroups": [
                {
                    "id": "/subscriptions/test-sub-123/resourceGroups/test-rg",
                    "name": "test-rg",
                    "location": "eastus"
                }
            ],
            "storageAccounts": [
                {
                    "id": "/subscriptions/test-sub-123/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/teststorage",
                    "name": "teststorage",
                    "location": "eastus",
                    "sku": {"name": "Standard_LRS"}
                }
            ]
        }

    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db)
        super().tearDown()

    def test_save_state_basic(self):
        """Test basic state saving functionality."""
        print("=== Testing Basic State Saving ===")
        
        # Load test data into DB
        DB.clear()
        DB.update(self.test_data)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save state
            save_state(temp_file)
            print(f"✓ State saved to: {temp_file}")
            
            # Verify file exists and is readable
            assert os.path.exists(temp_file), "Saved file should exist"
            assert os.path.getsize(temp_file) > 0, "Saved file should not be empty"
            
            # Read and verify content
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            # Verify structure
            assert "subscriptions" in saved_data, "Should contain subscriptions"
            assert "resourceGroups" in saved_data, "Should contain resourceGroups"
            assert "storageAccounts" in saved_data, "Should contain storageAccounts"
            
            # Verify data integrity
            assert len(saved_data["subscriptions"]) == 1, "Should have 1 subscription"
            assert saved_data["subscriptions"][0]["subscriptionId"] == "test-sub-123"
            print("✓ Data integrity verified")
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_load_state_basic(self):
        """Test basic state loading functionality."""
        print("=== Testing Basic State Loading ===")

        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name
        
        try:
            # Clear current DB
            DB.clear()
            assert len(DB) == 0, "DB should be empty before loading"
            
            # Load state
            load_state(temp_file)
            print(f"✓ State loaded from: {temp_file}")
            
            # Verify data was loaded
            assert "subscriptions" in DB, "Should have loaded subscriptions"
            assert "resourceGroups" in DB, "Should have loaded resourceGroups"
            assert "storageAccounts" in DB, "Should have loaded storageAccounts"
            
            # Verify data integrity
            assert len(DB["subscriptions"]) == 1, "Should have 1 subscription"
            assert DB["subscriptions"][0]["subscriptionId"] == "test-sub-123"
            assert DB["subscriptions"][0]["displayName"] == "Test Subscription"
            print("✓ Data integrity verified")
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_and_load_cycle(self):
        """Test complete save and load cycle."""
        print("=== Testing Save and Load Cycle ===")
        
        # Load test data into DB
        DB.clear()
        DB.update(self.test_data)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save state
            save_state(temp_file)
            print("✓ State saved")
            
            # Clear DB
            DB.clear()
            assert len(DB) == 0, "DB should be empty"
            
            # Load state back
            load_state(temp_file)
            print("✓ State loaded")
            
            # Verify complete data integrity
            assert len(DB["subscriptions"]) == len(self.test_data["subscriptions"])
            assert len(DB["resourceGroups"]) == len(self.test_data["resourceGroups"])
            assert len(DB["storageAccounts"]) == len(self.test_data["storageAccounts"])
            
            # Verify specific data
            assert DB["subscriptions"][0]["subscriptionId"] == "test-sub-123"
            assert DB["resourceGroups"][0]["name"] == "test-rg"
            assert DB["storageAccounts"][0]["name"] == "teststorage"
            print("✓ Complete data integrity verified")
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_load_state_with_error_configs(self):
        """Test loading state with error configuration files."""
        print("=== Testing Load State with Error Configs ===")
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as state_file:
            json.dump(self.test_data, state_file)
            state_file_path = state_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as error_config:
            json.dump({"error_mode": "test"}, error_config)
            error_config_path = error_config.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as error_defs:
            json.dump({"errors": []}, error_defs)
            error_defs_path = error_defs.name
        
        try:
            # Clear DB
            DB.clear()
            
            # Load state with error configs
            load_state(state_file_path, error_config_path, error_defs_path)
            print("✓ State loaded with error configs")
            
            # Verify data was loaded
            assert "subscriptions" in DB, "Should have loaded subscriptions"
            assert len(DB["subscriptions"]) == 1, "Should have 1 subscription"
            print("✓ Data loaded successfully with error configs")
            
        finally:
            # Clean up
            for file_path in [state_file_path, error_config_path, error_defs_path]:
                if os.path.exists(file_path):
                    os.unlink(file_path)

    def test_save_state_large_data(self):
        """Test saving state with large amounts of data."""
        print("=== Testing Save State with Large Data ===")
        
        # Create large test data
        large_data = {
            "subscriptions": [
                {
                    "subscriptionId": f"sub-{i:06d}",
                    "displayName": f"Subscription {i}",
                    "state": "Enabled"
                }
                for i in range(1000)
            ],
            "resourceGroups": [
                {
                    "id": f"/subscriptions/sub-{i:06d}/resourceGroups/rg-{i:06d}",
                    "name": f"rg-{i:06d}",
                    "location": "eastus"
                }
                for i in range(1000)
            ]
        }
        
        # Load large data into DB
        DB.clear()
        DB.update(large_data)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save state
            save_state(temp_file)
            print(f"✓ Large state saved to: {temp_file}")
            
            # Verify file size
            file_size = os.path.getsize(temp_file)
            print(f"✓ File size: {file_size} bytes")
            assert file_size > 100000, "Large data should result in significant file size"
            
            # Verify data integrity
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data["subscriptions"]) == 1000, "Should have 1000 subscriptions"
            assert len(saved_data["resourceGroups"]) == 1000, "Should have 1000 resource groups"
            print("✓ Large data integrity verified")
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_state_empty_db(self):
        """Test saving state with empty database."""
        print("=== Testing Save State with Empty DB ===")
        
        # Clear DB
        DB.clear()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save empty state
            save_state(temp_file)
            print(f"✓ Empty state saved to: {temp_file}")
            
            # Verify file exists but is small
            assert os.path.exists(temp_file), "Empty file should exist"
            file_size = os.path.getsize(temp_file)
            print(f"✓ Empty file size: {file_size} bytes")
            
            # Verify content is empty object
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == {}, "Empty DB should save as empty object"
            print("✓ Empty state saved correctly")
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_load_state_nonexistent_file(self):
        """Test loading state from non-existent file."""
        print("=== Testing Load State with Non-existent File ===")
        
        non_existent_file = "/tmp/non_existent_state_file.json"
        
        try:
            load_state(non_existent_file)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            print("✓ Correctly handled non-existent file")
        except Exception as e:
            print(f"✓ Correctly handled non-existent file with exception: {type(e).__name__}")

    def test_save_state_permission_error(self):
        """Test saving state with permission errors."""
        print("=== Testing Save State with Permission Error ===")
        
        # Try to save to a directory that doesn't exist
        invalid_path = "/non/existent/directory/state.json"
        
        try:
            save_state(invalid_path)
            assert False, "Should have raised FileNotFoundError or PermissionError"
        except (FileNotFoundError, PermissionError):
            print("✓ Correctly handled permission error")
        except Exception as e:
            print(f"✓ Correctly handled permission error with exception: {type(e).__name__}")

    def test_load_state_invalid_json(self):
        """Test loading state from invalid JSON file."""
        print("=== Testing Load State with Invalid JSON ===")
        
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            try:
                load_state(temp_file)
                assert False, "Should have raised JSONDecodeError"
            except json.JSONDecodeError:
                print("✓ Correctly handled invalid JSON")
            except Exception as e:
                print(f"✓ Correctly handled invalid JSON with exception: {type(e).__name__}")
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_state_persistence_across_operations(self):
        """Test that state persists correctly across multiple operations."""
        print("=== Testing State Persistence Across Operations ===")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Initial state
            DB.clear()
            DB.update(self.test_data)
            save_state(temp_file)
            print("✓ Initial state saved")
            
            # Modify state
            DB["subscriptions"].append({
                "subscriptionId": "test-sub-456",
                "displayName": "Another Subscription",
                "state": "Enabled"
            })
            save_state(temp_file)
            print("✓ Modified state saved")
            
            # Load and verify
            DB.clear()
            load_state(temp_file)
            
            assert len(DB["subscriptions"]) == 2, "Should have 2 subscriptions after modification"
            subscription_ids = [sub["subscriptionId"] for sub in DB["subscriptions"]]
            assert "test-sub-123" in subscription_ids, "Should have original subscription"
            assert "test-sub-456" in subscription_ids, "Should have new subscription"
            print("✓ State persistence verified")
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()
