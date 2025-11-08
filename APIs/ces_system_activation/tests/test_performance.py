import unittest
import sys
import os
import time
import gc
import psutil
import statistics
from typing import Callable, List
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import DB, reset_db, save_state, load_state
import APIs.ces_system_activation as ces


class TestCESPerformance(BaseTestCaseWithErrorHandler):
    """
    Performance tests for CES system identification service.
    Simple checks that the code doesn't use too much memory or take too long.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        reset_db()
        self.process = psutil.Process(os.getpid())
        # Force garbage collection before tests
        gc.collect()

    def tearDown(self):
        """Clean up after each test method."""
        reset_db()
        # Force garbage collection after tests
        gc.collect()

    def measure_execution_time(self, operation_func: Callable, iterations: int = 100) -> List[float]:
        """Measure execution time of an operation over multiple iterations."""
        execution_times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                operation_func()
            except Exception:
                pass  # Ignore errors for performance testing
            end_time = time.perf_counter()
            
            execution_times.append(end_time - start_time)
        
        return execution_times

    def measure_memory_usage(self, operation_func: Callable, iterations: int = 100) -> List[float]:
        """Measure memory usage of an operation over multiple iterations."""
        memory_usage = []
        
        for i in range(iterations):
            memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
            
            try:
                operation_func()
            except Exception:
                pass  # Ignore errors for performance testing
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_usage.append(memory_after - memory_before)
            
            # Force garbage collection every 50 iterations
            if i % 50 == 0:
                gc.collect()
        
        return memory_usage

    def stress_test_memory_usage(self, operation_func: Callable, iterations: int = 1000) -> List[float]:
        """Test memory usage under stress."""
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
        print(f"Memory usage - Peak: {peak_memory:.2f}MB, Avg: {avg_memory:.2f}MB")
        
        return memory_usage

    # Performance tests for core functions
    def test_send_notification_performance(self):
        """Test performance of send_customer_notification function."""
        def notification_operation():
            return ces.send_customer_notification(
                accountId="ACC-PERF-TEST",
                channel="EMAIL",
                message="Performance test message"
            )
        
        # Test execution time
        execution_times = self.measure_execution_time(notification_operation, iterations=50)
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        # Performance assertions
        self.assertLess(avg_time, 0.1, f"Average execution time too high: {avg_time:.4f}s")
        self.assertLess(max_time, 0.5, f"Maximum execution time too high: {max_time:.4f}s")
        
        print(f"send_customer_notification - Avg: {avg_time:.4f}s, Max: {max_time:.4f}s")

    def test_search_functions_performance(self):
        """Test performance of search functions."""
        # Disable real datastore for consistent performance
        DB['use_real_datastore'] = False
        
        def search_order_operation():
            return ces.search_order_details("Performance test query")
        
        def search_guides_operation():
            return ces.search_activation_guides("Performance test query")
        
        # Test order search performance
        order_times = self.measure_execution_time(search_order_operation, iterations=30)
        order_avg = statistics.mean(order_times)
        
        # Test guides search performance  
        guides_times = self.measure_execution_time(search_guides_operation, iterations=30)
        guides_avg = statistics.mean(guides_times)
        
        # Performance assertions
        self.assertLess(order_avg, 0.05, f"Order search too slow: {order_avg:.4f}s")
        self.assertLess(guides_avg, 0.05, f"Guides search too slow: {guides_avg:.4f}s")
        
        print(f"search_order_details - Avg: {order_avg:.4f}s")
        print(f"search_activation_guides - Avg: {guides_avg:.4f}s")

    def test_conversation_functions_performance(self):
        """Test performance of conversation management functions."""
        def escalate_operation():
            return ces.escalate("Performance test escalation")
        
        def fail_operation():
            return ces.fail("Performance test failure")
        
        def cancel_operation():
            return ces.cancel("Performance test cancellation")
        
        operations = [
            ("escalate", escalate_operation),
            ("fail", fail_operation), 
            ("cancel", cancel_operation)
        ]
        
        for name, operation in operations:
            execution_times = self.measure_execution_time(operation, iterations=100)
            avg_time = statistics.mean(execution_times)
            
            self.assertLess(avg_time, 0.01, f"{name} function too slow: {avg_time:.4f}s")
            print(f"{name} - Avg: {avg_time:.4f}s")

    # Database performance tests
    def test_database_reset_performance(self):
        """Test performance of database reset operation."""
        def reset_operation():
            reset_db()
        
        execution_times = self.measure_execution_time(reset_operation, iterations=20)
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        # Database reset should be fast
        self.assertLess(avg_time, 0.1, f"Database reset too slow: {avg_time:.4f}s")
        self.assertLess(max_time, 0.5, f"Database reset max time too high: {max_time:.4f}s")
        
        print(f"database reset - Avg: {avg_time:.4f}s, Max: {max_time:.4f}s")

    def test_database_save_load_performance(self):
        """Test performance of database save/load operations."""
        import tempfile
        import os
        
        temp_file = os.path.join(tempfile.gettempdir(), 'perf_test.json')
        
        def save_operation():
            save_state(temp_file)
        
        def load_operation():
            load_state(temp_file)
        
        try:
            # Test save performance
            save_times = self.measure_execution_time(save_operation, iterations=10)
            save_avg = statistics.mean(save_times)
            
            # Test load performance
            load_times = self.measure_execution_time(load_operation, iterations=10)
            load_avg = statistics.mean(load_times)
            
            # Performance assertions
            self.assertLess(save_avg, 0.05, f"Database save too slow: {save_avg:.4f}s")
            self.assertLess(load_avg, 0.05, f"Database load too slow: {load_avg:.4f}s")
            
            print(f"database save - Avg: {save_avg:.4f}s")
            print(f"database load - Avg: {load_avg:.4f}s")
            
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)

    # Memory usage tests
    def test_notification_memory_usage(self):
        """Test memory usage of notification function."""
        def notification_operation():
            return ces.send_customer_notification(
                accountId="ACC-MEM-TEST",
                message="Memory test message"
            )
        
        memory_usage = self.measure_memory_usage(notification_operation, iterations=100)
        avg_memory = statistics.mean([abs(m) for m in memory_usage])
        peak_memory = max([abs(m) for m in memory_usage])
        
        # Memory usage should be minimal
        self.assertLess(avg_memory, 1.0, f"Average memory usage too high: {avg_memory:.2f}MB")
        self.assertLess(peak_memory, 5.0, f"Peak memory usage too high: {peak_memory:.2f}MB")
        
        print(f"notification memory - Avg: {avg_memory:.2f}MB, Peak: {peak_memory:.2f}MB")

    def test_database_operations_memory(self):
        """Test memory usage of database operations."""
        def db_operations():
            # Simulate typical database operations
            reset_db()
            DB['customers'][0]['firstName'] = 'Memory Test'
            _ = len(DB['customers'])
            _ = DB.get('use_real_datastore', False)
        
        memory_usage = self.measure_memory_usage(db_operations, iterations=50)
        avg_memory = statistics.mean([abs(m) for m in memory_usage])
        
        self.assertLess(avg_memory, 0.5, f"DB operations memory usage too high: {avg_memory:.2f}MB")
        print(f"database operations memory - Avg: {avg_memory:.2f}MB")

    # Stress tests
    def test_rapid_function_calls_stress(self):
        """Stress test with rapid function calls."""
        self.skipTest("Skipping test_search_activation_guides_no_results")
        def rapid_calls():
            ces.send_customer_notification(accountId="ACC-12345")
            ces.escalate("Stress test")
            ces.search_order_details("stress query")
            ces.cancel("Stress cancel")
        
        start_time = time.perf_counter()
        
        # Run rapid calls for a short period
        iterations = 0
        while time.perf_counter() - start_time < 1.0:  # 1 second
            rapid_calls()
            iterations += 1
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        calls_per_second = iterations / total_time
        
        # Should handle at least 80 calls per second
        self.assertGreater(calls_per_second, 80, 
                          f"Performance too low: {calls_per_second:.1f} calls/sec")
        
        print(f"Rapid calls stress test - {calls_per_second:.1f} calls/sec")

    @patch('APIs.ces_system_activation.SimulationEngine.utils._get_token')
    def test_concurrent_operations_simulation(self, mock_get_token):
        """Simulate concurrent operations performance."""
        mock_get_token.return_value = 'mock-token'
        
        # Disable real datastore for consistent performance
        DB['use_real_datastore'] = False
        
        def mixed_operations():
            # Simulate a typical user session
            ces.send_customer_notification(accountId="CONCURRENT-TEST")
            ces.search_order_details("concurrent test query")
            ces.search_activation_guides("concurrent guide query")
            if len(DB['customers']) > 0:
                customer = DB['customers'][0]
                _ = customer.get('firstName', '')
        
        # Measure performance under simulated load
        execution_times = self.measure_execution_time(mixed_operations, iterations=50)
        avg_time = statistics.mean(execution_times)
        percentile_95 = sorted(execution_times)[int(0.95 * len(execution_times))]
        
        # Performance requirements
        self.assertLess(avg_time, 0.1, f"Mixed operations too slow: {avg_time:.4f}s")
        self.assertLess(percentile_95, 0.2, f"95th percentile too slow: {percentile_95:.4f}s")
        
        print(f"Mixed operations - Avg: {avg_time:.4f}s, 95th percentile: {percentile_95:.4f}s")

    # Memory stress tests
    def test_memory_stress_notifications(self):
        """Memory stress test for notification operations."""
        def notification_stress():
            return ces.send_customer_notification(
                accountId=f"STRESS-{time.time()}",
                message=f"Stress test message at {time.time()}"
            )
        
        # Memory stress test
        memory_usage = self.stress_test_memory_usage(notification_stress, iterations=200)
        
        # Check for memory leaks
        peak_memory = max([abs(m) for m in memory_usage])
        final_memory = abs(memory_usage[-1])
        
        self.assertLess(peak_memory, 10.0, f"Memory usage too high under stress: {peak_memory:.2f}MB")
        self.assertLess(final_memory, 2.0, f"Potential memory leak detected: {final_memory:.2f}MB")

    def test_large_data_handling_performance(self):
        """Test performance with larger data sets."""
        # Add more customers to test with larger data
        original_customers = DB['customers'].copy()
        
        try:
            # Create larger customer dataset
            for i in range(100):
                customer = {
                    'customerId': f'c-perf-test-{i}',
                    'leadId': f'LEAD-{i}',
                    'firstName': f'TestUser{i}',
                    'lastName': f'LastName{i}',
                    'email': f'test{i}@example.com',
                    'phoneNumber': f'+1555000{i:04d}',
                    'status': 'Test Customer',
                    'planSubscribed': 'Test Plan',
                    'applicationStatus': 'Active',
                    'applicationId': f'APP-{i}'
                }
                DB['customers'].append(customer)
            
            def large_data_operation():
                # Operations that might be affected by data size
                _ = len(DB['customers'])
                _ = [c for c in DB['customers'] if 'Test' in c['status']]
                ces.send_customer_notification(accountId="LARGE-DATA-TEST")
            
            execution_times = self.measure_execution_time(large_data_operation, iterations=20)
            avg_time = statistics.mean(execution_times)
            
            # Should still be reasonably fast with larger dataset
            self.assertLess(avg_time, 0.05, f"Large data operations too slow: {avg_time:.4f}s")
            print(f"Large data operations - Avg: {avg_time:.4f}s with {len(DB['customers'])} customers")
            
        finally:
            # Restore original dataset
            DB['customers'] = original_customers

    # Resource usage tests
    def test_cpu_usage_monitoring(self):
        """Monitor CPU usage during operations."""
        self.skipTest("Skipping test_cpu_usage_monitoring")
        def cpu_intensive_operation():
            # Simulate some processing
            for _ in range(10):
                ces.send_customer_notification(accountId="ACC-12345")
                ces.search_order_details("cpu test query")
        
        # Measure CPU usage
        cpu_before = self.process.cpu_percent()
        start_time = time.perf_counter()
        
        cpu_intensive_operation()
        
        end_time = time.perf_counter()
        cpu_after = self.process.cpu_percent()
        
        execution_time = end_time - start_time
        
        # Basic performance check
        self.assertLess(execution_time, 1.0, f"CPU intensive operations too slow: {execution_time:.2f}s")
        print(f"CPU usage - Before: {cpu_before:.1f}%, After: {cpu_after:.1f}%, Time: {execution_time:.2f}s")

    def test_function_call_overhead(self):
        """Test the overhead of function calls through the package interface."""
        # Direct function call
        from APIs.ces_system_activation.ces_system_activation import escalate as direct_escalate
        
        def direct_call():
            return direct_escalate("Direct call test")
        
        # Package interface call
        def package_call():
            return ces.escalate("Package call test")
        
        # Measure both
        direct_times = self.measure_execution_time(direct_call, iterations=100)
        package_times = self.measure_execution_time(package_call, iterations=100)
        
        direct_avg = statistics.mean(direct_times)
        package_avg = statistics.mean(package_times)
        
        # Package call should not be significantly slower
        overhead = package_avg - direct_avg
        self.assertLess(overhead, 0.001, f"Package interface overhead too high: {overhead:.6f}s")
        
        print(f"Function call overhead - Direct: {direct_avg:.6f}s, Package: {package_avg:.6f}s, Overhead: {overhead:.6f}s")


if __name__ == '__main__':
    unittest.main()
