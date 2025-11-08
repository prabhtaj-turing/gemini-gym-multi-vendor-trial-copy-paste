import unittest
import pytest
import time
import statistics
import gc
import psutil
import os
import threading
from hubspot.SimulationEngine.db import DB, load_state, save_state
from hubspot.SimulationEngine.utils import generate_hubspot_object_id
import tempfile
import json


class TestHubspotPerformance(unittest.TestCase):
    """Performance tests for Hubspot service."""
    
    def setUp(self):
        """Set up test environment."""
        self.process = psutil.Process(os.getpid())
        self.test_db = {
            "marketing_emails": {},
            "transactional_emails": {},
            "campaigns": {},
            "forms": {},
            "templates": {},
            "marketing_events": {},
            "form_global_events": {}
        }
        DB.update(self.test_db)
    
    def tearDown(self):
        """Clean up after each test."""
        # Clean up any test files
        for filename in os.listdir('.'):
            if filename.startswith('test_state_') and filename.endswith('.json'):
                try:
                    os.remove(filename)
                except OSError:
                    pass
    
    def test_utility_functions_performance(self):
        """Test performance of utility functions."""
        print("\nTesting utility functions performance...")
        
        # Test generate_hubspot_object_id performance
        times = []
        for _ in range(1000):
            start_time = time.perf_counter()
            generate_hubspot_object_id()
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        mean_time = statistics.mean(times)
        max_time = max(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0
        
        print(f"  generate_hubspot_object_id - Mean: {mean_time:.6f}s, Max: {max_time:.6f}s, Std: {std_time:.6f}s")
        self.assertLess(mean_time, 0.001, "generate_hubspot_object_id should be very fast")
    
    def test_database_operations_performance(self):
        """Test performance of database operations."""
        print("\nTesting database operations performance...")
        
        # Test adding data performance
        times = []
        for i in range(1000):
            start_time = time.perf_counter()
            DB[f"perf_test_{i}"] = {"value": i, "name": f"Test {i}"}
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        mean_time = statistics.mean(times)
        max_time = max(times)
        
        print(f"  Database add operations - Mean: {mean_time:.6f}s, Max: {max_time:.6f}s")
        self.assertLess(mean_time, 0.001, "Database add operations should be fast")
        
        # Test reading data performance
        times = []
        for i in range(1000):
            start_time = time.perf_counter()
            _ = DB[f"perf_test_{i}"]
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        mean_time = statistics.mean(times)
        max_time = max(times)
        
        print(f"  Database read operations - Mean: {mean_time:.6f}s, Max: {max_time:.6f}s")
        self.assertLess(mean_time, 0.001, "Database read operations should be fast")
        
        # Test updating data performance
        times = []
        for i in range(1000):
            start_time = time.perf_counter()
            DB[f"perf_test_{i}"]["value"] = i * 2
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        
        mean_time = statistics.mean(times)
        max_time = max(times)
        
        print(f"  Database update operations - Mean: {mean_time:.6f}s, Max: {max_time:.6f}s")
        self.assertLess(mean_time, 0.001, "Database update operations should be fast")
        
        # Clean up
        for i in range(1000):
            del DB[f"perf_test_{i}"]
    
    def test_state_persistence_performance(self):
        """Test performance of state persistence operations."""
        print("\nTesting state persistence performance...")
        
        # Prepare test data
        for i in range(100):
            DB[f"persist_test_{i}"] = {"value": i, "name": f"Test {i}"}
        
        # Test save_state performance
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            times = []
            for _ in range(10):
                start_time = time.perf_counter()
                save_state(temp_file)
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            
            mean_time = statistics.mean(times)
            max_time = max(times)
            
            print(f"  save_state operations - Mean: {mean_time:.4f}s, Max: {max_time:.4f}s")
            self.assertLess(mean_time, 0.1, "save_state should be reasonably fast")
            
            # Test load_state performance
            times = []
            for _ in range(10):
                start_time = time.perf_counter()
                load_state(temp_file)
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            
            mean_time = statistics.mean(times)
            max_time = max(times)
            
            print(f"  load_state operations - Mean: {mean_time:.4f}s, Max: {max_time:.4f}s")
            self.assertLess(mean_time, 0.1, "load_state should be reasonably fast")
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_memory_usage_performance(self):
        """Test memory usage under various operations."""
        print("\nTesting memory usage performance...")
        
        # Get initial memory usage
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform operations that might use memory
        for i in range(1000):
            DB[f"memory_test_{i}"] = {
                "value": i,
                "name": f"Memory Test {i}",
                "description": "A longer description to use more memory",
                "metadata": {"created": time.time(), "tags": [f"tag_{j}" for j in range(5)]}
            }
        
        # Get memory usage after operations
        after_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_memory - initial_memory
        
        print(f"  Memory usage - Initial: {initial_memory:.2f}MB, After: {after_memory:.2f}MB, Increase: {memory_increase:.2f}MB")
        
        # Memory increase should be reasonable (less than 100MB for 1000 operations)
        self.assertLess(memory_increase, 100, "Memory usage should be reasonable")
        
        # Clean up
        for i in range(1000):
            del DB[f"memory_test_{i}"]
        
        # Force garbage collection
        gc.collect()
        
        # Check memory after cleanup
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        print(f"  Memory after cleanup: {final_memory:.2f}MB")
    
    def stress_test_memory_usage(self, operation_func, iterations=1000):
        """Test memory usage under stress."""
        print(f"\nStress testing memory usage for {iterations} iterations...")
        
        memory_usage = []
        
        for i in range(iterations):
            memory_before = self.process.memory_info().rss / 1024 / 1024
            
            try:
                operation_func()
            except Exception:
                pass  # Ignore errors for stress testing
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  
            memory_usage.append(memory_after - memory_before)
            
            # Force garbage collection every 100 iterations
            if i % 100 == 0:
                gc.collect()
        
        peak_memory = max(memory_usage)
        avg_memory = statistics.mean(memory_usage)
        
        print(f"  Memory usage - Peak: {peak_memory:.2f}MB, Avg: {avg_memory:.2f}MB")
        return memory_usage
    
    def test_memory_stress_utility_function(self):
        """Stress test memory usage for utility functions."""
        def utility_operation():
            return generate_hubspot_object_id()
        
        memory_usage = self.stress_test_memory_usage(utility_operation, iterations=200)
        
        # Memory usage should be stable
        peak_memory = max(memory_usage)
        self.assertLess(peak_memory, 50, "Memory usage should remain stable under stress")
    
    def test_memory_stress_database_operations(self):
        """Stress test memory usage for database operations."""
        def db_operation():
            test_id = generate_hubspot_object_id()
            DB[f"stress_test_{test_id}"] = {"value": test_id, "timestamp": time.time()}
            if len(DB) > 1000:  # Prevent unlimited growth
                keys_to_remove = list(DB.keys())[:100]
                for key in keys_to_remove:
                    if key.startswith("stress_test_"):
                        del DB[key]
        
        memory_usage = self.stress_test_memory_usage(db_operation, iterations=200)
        
        # Memory usage should be stable
        peak_memory = max(memory_usage)
        self.assertLess(peak_memory, 100, "Memory usage should remain stable under stress")
    
    def test_concurrent_performance(self):
        """Test performance under concurrent access."""
        print("\nTesting concurrent performance...")
        
        results = []
        errors = []
        
        def concurrent_worker(worker_id, iterations):
            """Worker function for concurrent testing."""
            try:
                start_time = time.perf_counter()
                
                for i in range(iterations):
                    # Perform various operations
                    test_id = generate_hubspot_object_id()
                    DB[f"concurrent_{worker_id}_{i}"] = {
                        "worker": worker_id,
                        "iteration": i,
                        "id": test_id,
                        "timestamp": time.time()
                    }
                    
                    # Read data
                    _ = DB[f"concurrent_{worker_id}_{i}"]
                    
                    # Update data
                    DB[f"concurrent_{worker_id}_{i}"]["updated"] = True
                
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                results.append((worker_id, execution_time))
                
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_worker, args=(i, 100))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check for errors
        self.assertEqual(len(errors), 0, f"Concurrent execution errors: {errors}")
        
        # Analyze performance
        execution_times = [result[1] for result in results]
        mean_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        print(f"  Concurrent execution - Mean: {mean_time:.4f}s, Max: {max_time:.4f}s")
        self.assertLess(mean_time, 1.0, "Concurrent execution should be reasonably fast")
        
        # Clean up
        for key in list(DB.keys()):
            if key.startswith("concurrent_"):
                del DB[key]
    
    def test_scalability_performance(self):
        """Test performance scalability with different data sizes."""
        print("\nTesting scalability performance...")
        
        data_sizes = [10, 100, 1000]
        performance_results = {}
        
        for size in data_sizes:
            # Prepare data
            start_time = time.perf_counter()
            for i in range(size):
                DB[f"scalability_{size}_{i}"] = {
                    "value": i,
                    "name": f"Scalability Test {i}",
                    "size": size
                }
            setup_time = time.perf_counter() - start_time
            
            # Test read performance
            start_time = time.perf_counter()
            for i in range(size):
                _ = DB[f"scalability_{size}_{i}"]
            read_time = time.perf_counter() - start_time
            
            # Test update performance
            start_time = time.perf_counter()
            for i in range(size):
                DB[f"scalability_{size}_{i}"]["updated"] = True
            update_time = time.perf_counter() - start_time
            
            performance_results[size] = {
                "setup_time": setup_time,
                "read_time": read_time,
                "update_time": update_time
            }
            
            print(f"  Data size {size}: Setup: {setup_time:.4f}s, Read: {read_time:.4f}s, Update: {update_time:.4f}s")
            
            # Clean up
            for i in range(size):
                del DB[f"scalability_{size}_{i}"]
        
        # Performance should scale reasonably (not exponentially)
        for size in data_sizes[1:]:
            prev_size = data_sizes[data_sizes.index(size) - 1]
            size_ratio = size / prev_size
            
            # Performance increase should be roughly linear
            read_ratio = performance_results[size]["read_time"] / performance_results[prev_size]["read_time"]
            self.assertLess(read_ratio, size_ratio * 2, f"Read performance should scale reasonably for size {size}")
    
    def test_performance_regression(self):
        """Test for performance regression by comparing with baseline."""
        print("\nTesting performance regression...")
        
        # Baseline performance test
        baseline_times = []
        for _ in range(100):
            start_time = time.perf_counter()
            generate_hubspot_object_id()
            end_time = time.perf_counter()
            baseline_times.append(end_time - start_time)
        
        baseline_mean = statistics.mean(baseline_times)
        baseline_std = statistics.stdev(baseline_times) if len(baseline_times) > 1 else 0
        
        print(f"  Baseline performance - Mean: {baseline_mean:.6f}s, Std: {baseline_std:.6f}s")
        
        # Current performance test
        current_times = []
        for _ in range(100):
            start_time = time.perf_counter()
            generate_hubspot_object_id()
            end_time = time.perf_counter()
            current_times.append(end_time - start_time)
        
        current_mean = statistics.mean(current_times)
        current_std = statistics.stdev(current_times) if len(current_times) > 1 else 0
        
        print(f"  Current performance - Mean: {current_mean:.6f}s, Std: {current_std:.6f}s")
        
        # Check for significant regression (more than 50% slower)
        performance_ratio = current_mean / baseline_mean
        print(f"  Performance ratio: {performance_ratio:.2f}x")
        
        self.assertLess(performance_ratio, 1.5, "Performance should not regress significantly")


if __name__ == '__main__':
    unittest.main()
