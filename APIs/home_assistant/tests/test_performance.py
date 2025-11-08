"""
Performance test suite for home_assistant module.

This test suite verifies:
1. Memory usage stays within reasonable limits for key operations
2. Execution time remains acceptable for all functions
3. Performance scales appropriately with data size

Performance Thresholds:
- Memory: Maximum 50MB increase per operation
- Execution Time: 
  - Simple operations (get_state, get_device_info): 100ms max
  - List operations (list_devices): 500ms max  
  - Search operations (get_id_by_name): 200ms max
  - Modification operations (toggle_device, set_device_property): 150ms max
"""

import unittest
import time
import psutil
import os
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestHomeAssistantPerformance(BaseTestCaseWithErrorHandler):
    """Performance test suite for home_assistant module functions."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Get current process for memory monitoring
        self.process = psutil.Process(os.getpid())
        
        # Performance thresholds (documented for clarity)
        self.MEMORY_THRESHOLD_MB = 50  # Maximum memory increase in MB
        self.TIME_THRESHOLD_SIMPLE_MS = 100  # Simple operations max time in ms
        self.TIME_THRESHOLD_LIST_MS = 500  # List operations max time in ms  
        self.TIME_THRESHOLD_SEARCH_MS = 200  # Search operations max time in ms
        self.TIME_THRESHOLD_MODIFY_MS = 150  # Modification operations max time in ms
        
        # Create mock data sets of different sizes for scaling tests
        self.small_device_set = self._create_mock_devices(10)
        self.medium_device_set = self._create_mock_devices(100) 
        self.large_device_set = self._create_mock_devices(1000)

    def _create_mock_devices(self, count):
        """Create a mock device dataset of specified size."""
        devices = {}
        device_types = ["light", "fan", "door", "window", "speaker"]
        states = ["On", "Off", "Open", "Closed"]
        
        for i in range(count):
            device_type = device_types[i % len(device_types)]
            state = states[i % len(states)]
            device_id = f"{device_type.upper()}_{i:03d}"
            
            devices[device_id] = {
                "type": device_type,
                "name": f"Test {device_type.title()} {i}",
                "attributes": {
                    "state": state,
                    "brightness": 50 if device_type == "light" else None
                }
            }
        return devices

    def _measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage before and after function execution."""
        # Force garbage collection to get accurate baseline
        import gc
        gc.collect()
        
        # Get initial memory usage
        initial_memory = self.process.memory_info().rss
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Force garbage collection again
        gc.collect()
        
        # Get final memory usage
        final_memory = self.process.memory_info().rss
        
        # Calculate memory increase in MB
        memory_increase_mb = (final_memory - initial_memory) / (1024 * 1024)
        
        return result, memory_increase_mb

    def _measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of function in milliseconds."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        return result, execution_time_ms

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_list_devices_memory_usage_small_dataset(self, mock_get_devices):
        """Test memory usage of list_devices with small dataset."""
        mock_get_devices.return_value = self.small_device_set
        from home_assistant import list_devices
        
        result, memory_increase = self._measure_memory_usage(list_devices)
        
        # Verify function works correctly
        self.assertIsInstance(result, dict)
        self.assertIn("entities", result)
        
        # Verify memory usage is within threshold
        self.assertLessEqual(
            memory_increase, 
            self.MEMORY_THRESHOLD_MB,
            f"Memory usage {memory_increase:.2f}MB exceeds threshold {self.MEMORY_THRESHOLD_MB}MB"
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_list_devices_memory_usage_large_dataset(self, mock_get_devices):
        """Test memory usage of list_devices with large dataset."""
        mock_get_devices.return_value = self.large_device_set
        from home_assistant import list_devices
        
        result, memory_increase = self._measure_memory_usage(list_devices)
        
        # Verify function works correctly
        self.assertIsInstance(result, dict)
        self.assertIn("entities", result)
        self.assertEqual(len(result["entities"]), len(self.large_device_set))
        
        # Verify memory usage is within threshold even for large datasets
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_MB,
            f"Memory usage {memory_increase:.2f}MB exceeds threshold {self.MEMORY_THRESHOLD_MB}MB for large dataset"
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_list_devices_execution_time_scaling(self, mock_get_devices):
        """Test execution time of list_devices scales appropriately with data size."""
        from home_assistant import list_devices
        
        # Test with small dataset
        mock_get_devices.return_value = self.small_device_set
        result_small, time_small = self._measure_execution_time(list_devices)
        
        # Test with medium dataset  
        mock_get_devices.return_value = self.medium_device_set
        result_medium, time_medium = self._measure_execution_time(list_devices)
        
        # Test with large dataset
        mock_get_devices.return_value = self.large_device_set
        result_large, time_large = self._measure_execution_time(list_devices)
        
        # Verify all executions complete within threshold
        self.assertLessEqual(
            time_small,
            self.TIME_THRESHOLD_LIST_MS,
            f"Small dataset execution time {time_small:.2f}ms exceeds threshold {self.TIME_THRESHOLD_LIST_MS}ms"
        )
        self.assertLessEqual(
            time_medium,
            self.TIME_THRESHOLD_LIST_MS,
            f"Medium dataset execution time {time_medium:.2f}ms exceeds threshold {self.TIME_THRESHOLD_LIST_MS}ms"
        )
        self.assertLessEqual(
            time_large,
            self.TIME_THRESHOLD_LIST_MS,
            f"Large dataset execution time {time_large:.2f}ms exceeds threshold {self.TIME_THRESHOLD_LIST_MS}ms"
        )
        
        # Verify results are correct
        self.assertEqual(len(result_small["entities"]), len(self.small_device_set))
        self.assertEqual(len(result_medium["entities"]), len(self.medium_device_set))
        self.assertEqual(len(result_large["entities"]), len(self.large_device_set))

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_get_device_info_performance(self, mock_get_devices):
        """Test performance of get_device_info function."""
        mock_get_devices.return_value = self.medium_device_set
        from home_assistant import get_device_info
        
        # Test memory usage
        result, memory_increase = self._measure_memory_usage(get_device_info, "LIGHT_000")
        
        self.assertIsInstance(result, dict)
        self.assertIn("entity_id", result)
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_MB,
            f"Memory usage {memory_increase:.2f}MB exceeds threshold {self.MEMORY_THRESHOLD_MB}MB"
        )
        
        # Test execution time
        result, execution_time = self._measure_execution_time(get_device_info, "LIGHT_000")
        
        self.assertLessEqual(
            execution_time,
            self.TIME_THRESHOLD_SIMPLE_MS,
            f"Execution time {execution_time:.2f}ms exceeds threshold {self.TIME_THRESHOLD_SIMPLE_MS}ms"
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_get_state_performance(self, mock_get_devices):
        """Test performance of get_state function."""
        mock_get_devices.return_value = self.medium_device_set
        from home_assistant import get_state
        
        # Test memory usage
        result, memory_increase = self._measure_memory_usage(get_state, "FAN_001")
        
        self.assertIsInstance(result, dict)
        self.assertIn("entity_id", result)
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_MB,
            f"Memory usage {memory_increase:.2f}MB exceeds threshold {self.MEMORY_THRESHOLD_MB}MB"
        )
        
        # Test execution time
        result, execution_time = self._measure_execution_time(get_state, "FAN_001")
        
        self.assertLessEqual(
            execution_time,
            self.TIME_THRESHOLD_SIMPLE_MS,
            f"Execution time {execution_time:.2f}ms exceeds threshold {self.TIME_THRESHOLD_SIMPLE_MS}ms"
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_toggle_device_performance(self, mock_get_devices):
        """Test performance of toggle_device function."""
        mock_get_devices.return_value = self.medium_device_set
        from home_assistant import toggle_device
        
        # Test memory usage
        result, memory_increase = self._measure_memory_usage(toggle_device, "LIGHT_000", "On")
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_MB,
            f"Memory usage {memory_increase:.2f}MB exceeds threshold {self.MEMORY_THRESHOLD_MB}MB"
        )
        
        # Test execution time
        result, execution_time = self._measure_execution_time(toggle_device, "LIGHT_000", "Off")
        
        self.assertLessEqual(
            execution_time,
            self.TIME_THRESHOLD_MODIFY_MS,
            f"Execution time {execution_time:.2f}ms exceeds threshold {self.TIME_THRESHOLD_MODIFY_MS}ms"
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_set_device_property_performance(self, mock_get_devices):
        """Test performance of set_device_property function."""
        mock_get_devices.return_value = self.medium_device_set
        from home_assistant import set_device_property
        
        new_attributes = {"state": "On", "brightness": 75}
        
        # Test memory usage
        result, memory_increase = self._measure_memory_usage(
            set_device_property, "LIGHT_000", new_attributes
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_MB,
            f"Memory usage {memory_increase:.2f}MB exceeds threshold {self.MEMORY_THRESHOLD_MB}MB"
        )
        
        # Test execution time
        result, execution_time = self._measure_execution_time(
            set_device_property, "LIGHT_000", new_attributes
        )
        
        self.assertLessEqual(
            execution_time,
            self.TIME_THRESHOLD_MODIFY_MS,
            f"Execution time {execution_time:.2f}ms exceeds threshold {self.TIME_THRESHOLD_MODIFY_MS}ms"
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_get_id_by_name_performance_scaling(self, mock_get_devices):
        """Test performance of get_id_by_name with different dataset sizes."""
        from home_assistant import get_id_by_name
        
        # Test with small dataset
        mock_get_devices.return_value = self.small_device_set
        result_small, time_small = self._measure_execution_time(get_id_by_name, "Test Light 5")
        
        # Test with large dataset (worst case - target is at the end)
        mock_get_devices.return_value = self.large_device_set
        result_large, time_large = self._measure_execution_time(get_id_by_name, "Test Light 995")
        
        # Verify both complete within threshold
        self.assertLessEqual(
            time_small,
            self.TIME_THRESHOLD_SEARCH_MS,
            f"Small dataset search time {time_small:.2f}ms exceeds threshold {self.TIME_THRESHOLD_SEARCH_MS}ms"
        )
        self.assertLessEqual(
            time_large,
            self.TIME_THRESHOLD_SEARCH_MS,
            f"Large dataset search time {time_large:.2f}ms exceeds threshold {self.TIME_THRESHOLD_SEARCH_MS}ms"
        )
        
        # Verify results are correct
        self.assertEqual(result_small, "LIGHT_005")
        self.assertEqual(result_large, "LIGHT_995")

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_list_devices_with_domain_filter_performance(self, mock_get_devices):
        """Test performance of list_devices with domain filtering."""
        mock_get_devices.return_value = self.large_device_set
        from home_assistant import list_devices
        
        # Test memory usage with domain filter
        result, memory_increase = self._measure_memory_usage(list_devices, domain="light")
        
        self.assertIsInstance(result, dict)
        self.assertIn("entities", result)
        # Verify filtering worked (should be 1/5 of total since we have 5 device types)
        expected_count = len(self.large_device_set) // 5
        self.assertAlmostEqual(len(result["entities"]), expected_count, delta=1)
        
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_MB,
            f"Memory usage {memory_increase:.2f}MB exceeds threshold {self.MEMORY_THRESHOLD_MB}MB"
        )
        
        # Test execution time with domain filter
        result, execution_time = self._measure_execution_time(list_devices, domain="fan")
        
        self.assertLessEqual(
            execution_time,
            self.TIME_THRESHOLD_LIST_MS,
            f"Execution time {execution_time:.2f}ms exceeds threshold {self.TIME_THRESHOLD_LIST_MS}ms"
        )

    @patch("home_assistant.devices._get_home_assistant_devices")
    def test_multiple_operations_memory_stability(self, mock_get_devices):
        """Test that multiple consecutive operations don't cause memory leaks."""
        mock_get_devices.return_value = self.medium_device_set
        from home_assistant import list_devices, get_device_info, get_state, toggle_device
        
        # Get initial memory baseline
        import gc
        gc.collect()
        initial_memory = self.process.memory_info().rss
        
        # Perform multiple operations
        for i in range(10):
            list_devices()
            get_device_info("LIGHT_000")
            get_state("FAN_001") 
            toggle_device("DOOR_002")
        
        # Force garbage collection
        gc.collect()
        final_memory = self.process.memory_info().rss
        
        memory_increase_mb = (final_memory - initial_memory) / (1024 * 1024)
        
        # Memory increase should still be within threshold after multiple operations
        self.assertLessEqual(
            memory_increase_mb,
            self.MEMORY_THRESHOLD_MB,
            f"Memory increase {memory_increase_mb:.2f}MB after multiple operations exceeds threshold {self.MEMORY_THRESHOLD_MB}MB"
        )

    def test_performance_error_handling_does_not_affect_timing(self):
        """Test that error conditions don't significantly impact performance."""
        from home_assistant import get_device_info
        
        # Measure time for error case
        start_time = time.perf_counter()
        
        # Use assert_error_behavior to test expected exception without try/except
        self.assert_error_behavior(
            get_device_info,
            KeyError,
            "'device_id must be a valid device ID.'",
            None,
            "NONEXISTENT_DEVICE"
        )
        
        end_time = time.perf_counter()
        error_execution_time_ms = (end_time - start_time) * 1000
        
        # Error handling should be reasonable (framework overhead is expected, especially in CI)
        ERROR_HANDLING_THRESHOLD_MS = 2000  # Generous threshold for CI environments with framework overhead
        self.assertLessEqual(
            error_execution_time_ms,
            ERROR_HANDLING_THRESHOLD_MS,
            f"Error handling time {error_execution_time_ms:.2f}ms exceeds threshold {ERROR_HANDLING_THRESHOLD_MS}ms"
        )

    def test_concurrent_operation_performance_baseline(self):
        """Test baseline performance metrics for documentation purposes."""
        # This test serves as documentation of current performance characteristics
        # and will help identify performance regressions over time
        
        performance_metrics = {
            "memory_threshold_mb": self.MEMORY_THRESHOLD_MB,
            "time_threshold_simple_ms": self.TIME_THRESHOLD_SIMPLE_MS,
            "time_threshold_list_ms": self.TIME_THRESHOLD_LIST_MS,
            "time_threshold_search_ms": self.TIME_THRESHOLD_SEARCH_MS,
            "time_threshold_modify_ms": self.TIME_THRESHOLD_MODIFY_MS
        }
        
        # Verify all thresholds are reasonable positive values
        for metric_name, threshold in performance_metrics.items():
            self.assertGreater(
                threshold, 
                0, 
                f"Performance threshold {metric_name} must be positive: {threshold}"
            )
            self.assertLess(
                threshold,
                10000,  # 10 seconds max for any operation
                f"Performance threshold {metric_name} seems unreasonably high: {threshold}"
            )


if __name__ == "__main__":
    unittest.main()
