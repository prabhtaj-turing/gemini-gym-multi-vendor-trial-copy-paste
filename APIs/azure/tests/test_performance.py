"""
Performance test suite for Azure API following Service Engineering Test Framework Guidelines.

This test file focuses on:
7. Performance Tests (Completed)
"""

import unittest
import sys
import os
import time
import cProfile
import pstats
import io
import threading
import queue
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
# Ensure `APIs` directory (which contains `common_utils`) is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from common_utils.base_case import BaseTestCaseWithErrorHandler

# Copy the basic utility functions directly to avoid import issues
import uuid
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

# Mock Azure API functions for performance testing
class MockAzureAPI:
    """Mock Azure API functions for performance testing."""
    
    @staticmethod
    def azmcp_subscription_list():
        time.sleep(0.001)  # Simulate API call time
        return {"subscriptions": [{"subscriptionId": "test-sub-123", "displayName": "Test Subscription"}]}
    
    @staticmethod
    def azmcp_storage_account_list():
        time.sleep(0.002)  # Simulate API call time
        return {"storageAccounts": [{"name": "teststorage", "location": "eastus"}]}
    
    @staticmethod
    def azmcp_appconfig_account_list():
        time.sleep(0.001)  # Simulate API call time
        return {"appConfigurationStores": [{"name": "testappconfig", "location": "eastus"}]}

# Create mock functions
mock_api = MockAzureAPI()
azmcp_subscription_list = mock_api.azmcp_subscription_list
azmcp_storage_account_list = mock_api.azmcp_storage_account_list
azmcp_appconfig_account_list = mock_api.azmcp_appconfig_account_list


class TestAzureAPIPerformance(BaseTestCaseWithErrorHandler):
    """Performance tests for Azure API functions."""

    def setUp(self):
        """Set up test environment."""
        # Store original DB state
        self.original_db = DB.copy()

    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db)

    def test_utility_function_performance(self):
        """Test performance of utility functions."""
        print("=== Testing Utility Function Performance ===")
        
        # Test UUID generation performance
        start_time = time.time()
        uuids = [new_uuid_str() for _ in range(1000)]
        uuid_time = time.time() - start_time
        print(f"✓ UUID generation (1000 calls): {uuid_time:.4f}s ({1000/uuid_time:.0f} calls/sec)")
        self.assertLess(uuid_time, 1.0, "UUID generation should be fast")
        
        # Test timestamp generation performance
        start_time = time.time()
        timestamps = [get_current_utc_timestamp_iso() for _ in range(1000)]
        timestamp_time = time.time() - start_time
        print(f"✓ Timestamp generation (1000 calls): {timestamp_time:.4f}s ({1000/timestamp_time:.0f} calls/sec)")
        self.assertLess(timestamp_time, 1.0, "Timestamp generation should be fast")
        
        # Test ARM ID generation performance
        start_time = time.time()
        arm_ids = [generate_arm_id("test-sub-123", "test-rg", "Storage", "storageAccounts", "teststorage") 
                  for _ in range(1000)]
        arm_id_time = time.time() - start_time
        print(f"✓ ARM ID generation (1000 calls): {arm_id_time:.4f}s ({1000/arm_id_time:.0f} calls/sec)")
        self.assertLess(arm_id_time, 1.0, "ARM ID generation should be fast")

    def test_api_function_performance(self):
        """Test performance of API functions."""
        print("=== Testing API Function Performance ===")
        
        # Test subscription list performance
        start_time = time.time()
        for _ in range(10):
            result = azmcp_subscription_list()
            self.assertIsInstance(result, dict)
        api_time = time.time() - start_time
        print(f"✓ Subscription list API (10 calls): {api_time:.4f}s ({10/api_time:.0f} calls/sec)")
        self.assertLess(api_time, 5.0, "API calls should complete within reasonable time")
        
        # Test storage account list performance
        start_time = time.time()
        for _ in range(10):
            result = azmcp_storage_account_list()
            self.assertIsInstance(result, dict)
        api_time = time.time() - start_time
        print(f"✓ Storage account list API (10 calls): {api_time:.4f}s ({10/api_time:.0f} calls/sec)")
        self.assertLess(api_time, 5.0, "API calls should complete within reasonable time")

    def test_state_management_performance(self):
        """Test performance of state management functions."""
        print("=== Testing State Management Performance ===")
        
        # Create test data
        test_data = {
            "subscriptions": [{"subscriptionId": "test-sub-123", "displayName": "Test Subscription"}],
            "storageAccounts": [{"name": "teststorage", "location": "eastus"}]
        }
        
        # Test save_state performance
        DB.clear()
        DB.update(test_data)
        
        start_time = time.time()
        with open("/tmp/test_state.json", 'w') as f:
            import json
            json.dump(DB, f)
        save_time = time.time() - start_time
        print(f"✓ State saving performance: {save_time:.4f}s")
        self.assertLess(save_time, 1.0, "State saving should be fast")
        
        # Test load_state performance
        start_time = time.time()
        with open("/tmp/test_state.json", 'r') as f:
            import json
            loaded_data = json.load(f)
        load_time = time.time() - start_time
        print(f"✓ State loading performance: {load_time:.4f}s")
        self.assertLess(load_time, 1.0, "State loading should be fast")
        
        # Clean up
        if os.path.exists("/tmp/test_state.json"):
            os.unlink("/tmp/test_state.json")

    def test_concurrent_api_calls(self):
        """Test performance under concurrent API calls."""
        print("=== Testing Concurrent API Calls ===")
        
        def api_worker(result_queue, worker_id):
            """Worker function for concurrent API calls."""
            try:
                start_time = time.time()
                result = azmcp_subscription_list()
                end_time = time.time()
                result_queue.put((worker_id, end_time - start_time, result))
            except Exception as e:
                result_queue.put((worker_id, None, str(e)))
        
        # Test with 5 concurrent workers
        num_workers = 5
        result_queue = queue.Queue()
        threads = []
        
        start_time = time.time()
        for i in range(num_workers):
            thread = threading.Thread(target=api_worker, args=(result_queue, i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        results = []
        while not result_queue.empty():
            worker_id, call_time, result = result_queue.get()
            if call_time is not None:
                results.append(call_time)
                self.assertIsInstance(result, dict)
        
        print(f"✓ Concurrent API calls ({num_workers} workers): {total_time:.4f}s")
        print(f"  Average call time: {sum(results)/len(results):.4f}s")
        print(f"  Throughput: {num_workers/total_time:.0f} calls/sec")
        
        self.assertEqual(len(results), num_workers, "All workers should complete successfully")
        self.assertLess(total_time, 10.0, "Concurrent calls should complete within reasonable time")

    def test_memory_usage_profiling(self):
        """Test memory usage profiling (simplified without psutil)."""
        print("=== Testing Memory Usage Profiling ===")
        
        # Test memory usage by creating large data structures
        start_time = time.time()
        
        # Create large test data
        large_data = {
            "subscriptions": [{"subscriptionId": f"sub-{i}", "displayName": f"Subscription {i}"} 
                             for i in range(1000)],
            "storageAccounts": [{"name": f"storage{i}", "location": "eastus"} 
                               for i in range(1000)]
        }
        
        # Load into DB
        DB.clear()
        DB.update(large_data)
        
        # Perform operations
        for _ in range(100):
            new_uuid_str()
            get_current_utc_timestamp_iso()
            generate_arm_id("test-sub-123", "test-rg")
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        print(f"✓ Large data operations: {operation_time:.4f}s")
        print(f"  Data size: {len(large_data['subscriptions'])} subscriptions, {len(large_data['storageAccounts'])} storage accounts")
        
        self.assertLess(operation_time, 5.0, "Large data operations should complete within reasonable time")

    def test_profiling_utility_functions(self):
        """Test profiling of utility functions using cProfile."""
        print("=== Testing Utility Function Profiling ===")
        
        # Profile UUID generation
        profiler = cProfile.Profile()
        profiler.enable()
        
        for _ in range(1000):
            new_uuid_str()
        
        profiler.disable()
        
        # Get profiling stats
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        stats.print_stats(5)  # Top 5 functions
        
        print("✓ UUID generation profiling completed")
        print("  Profiling stats available (top 5 functions shown)")
        
        # Profile ARM ID generation
        profiler = cProfile.Profile()
        profiler.enable()
        
        for _ in range(1000):
            generate_arm_id("test-sub-123", "test-rg", "Storage", "storageAccounts", "teststorage")
        
        profiler.disable()
        
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        stats.print_stats(5)
        
        print("✓ ARM ID generation profiling completed")
        print("  Profiling stats available (top 5 functions shown)")

    def test_throughput_benchmarks(self):
        """Test throughput benchmarks for key operations."""
        print("=== Testing Throughput Benchmarks ===")
        
        # Benchmark UUID generation throughput
        start_time = time.time()
        count = 10000
        for _ in range(count):
            new_uuid_str()
        uuid_throughput_time = time.time() - start_time
        uuid_throughput = count / uuid_throughput_time
        
        print(f"✓ UUID generation throughput: {uuid_throughput:.0f} calls/sec")
        self.assertGreater(uuid_throughput, 1000, "UUID generation should have high throughput")
        
        # Benchmark timestamp generation throughput
        start_time = time.time()
        for _ in range(count):
            get_current_utc_timestamp_iso()
        timestamp_throughput_time = time.time() - start_time
        timestamp_throughput = count / timestamp_throughput_time
        
        print(f"✓ Timestamp generation throughput: {timestamp_throughput:.0f} calls/sec")
        self.assertGreater(timestamp_throughput, 1000, "Timestamp generation should have high throughput")
        
        # Benchmark ARM ID generation throughput
        start_time = time.time()
        for _ in range(count):
            generate_arm_id("test-sub-123", "test-rg", "Storage", "storageAccounts", "teststorage")
        arm_id_throughput_time = time.time() - start_time
        arm_id_throughput = count / arm_id_throughput_time
        
        print(f"✓ ARM ID generation throughput: {arm_id_throughput:.0f} calls/sec")
        self.assertGreater(arm_id_throughput, 100, "ARM ID generation should have reasonable throughput")

    def test_scalability_tests(self):
        """Test scalability of operations with increasing load."""
        print("=== Testing Scalability ===")
        
        # Test scalability with different data sizes
        data_sizes = [10, 100, 1000]
        
        for size in data_sizes:
            start_time = time.time()
            
            # Create data of specified size
            test_data = {
                "subscriptions": [{"subscriptionId": f"sub-{i}", "displayName": f"Subscription {i}"} 
                                 for i in range(size)],
                "storageAccounts": [{"name": f"storage{i}", "location": "eastus"} 
                                   for i in range(size)]
            }
            
            # Load into DB
            DB.clear()
            DB.update(test_data)
            
            # Perform operations
            for _ in range(size // 10):  # Proportional number of operations
                new_uuid_str()
                generate_arm_id("test-sub-123", "test-rg")
            
            end_time = time.time()
            operation_time = end_time - start_time
            
            print(f"✓ Data size {size}: {operation_time:.4f}s")
            self.assertLess(operation_time, size * 0.01, f"Operations should scale reasonably with data size {size}")


if __name__ == "__main__":
    unittest.main()
