"""
Performance Tests for Device Setting API

This test suite verifies that key functions and operations in the device_setting module
perform within acceptable memory and execution time limits.

Memory Thresholds:
- Core functions: 10MB maximum memory increase
- Bulk operations: 25MB maximum memory increase
- App operations: 15MB maximum memory increase

Execution Time Thresholds:
- Simple operations: 0.1 seconds maximum
- Complex operations: 0.5 seconds maximum
- Bulk operations: 1.0 seconds maximum
"""

import unittest
import time
import psutil
import os
from typing import Callable, Any
from common_utils.base_case import BaseTestCaseWithErrorHandler
from device_setting import (
    open,
    get,
    on,
    off,
    mute,
    unmute,
    adjust_volume,
    set_volume,
    get_device_insights,
    get_installed_apps,
    get_app_notification_status,
    set_app_notification_status,
)
from device_setting.SimulationEngine.db import load_state, DEFAULT_DB_PATH


class TestPerformance(BaseTestCaseWithErrorHandler):
    """Performance test suite for device_setting API functions."""

    # Memory thresholds in MB
    MEMORY_THRESHOLD_CORE_FUNCTIONS = 10.0
    MEMORY_THRESHOLD_BULK_OPERATIONS = 25.0
    MEMORY_THRESHOLD_APP_OPERATIONS = 15.0

    # Execution time thresholds in seconds
    TIME_THRESHOLD_SIMPLE_OPERATIONS = 0.1
    TIME_THRESHOLD_COMPLEX_OPERATIONS = 0.5
    TIME_THRESHOLD_BULK_OPERATIONS = 1.0

    def setUp(self):
        """Reset database to defaults before each test for proper isolation."""
        load_state(DEFAULT_DB_PATH)
        # Force garbage collection to get accurate memory measurements
        import gc

        gc.collect()

    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage of the process in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024

    def _measure_execution_time(
        self, func: Callable, *args, **kwargs
    ) -> tuple[Any, float]:
        """
        Measure execution time of a function.

        Args:
            func: Function to measure
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Tuple of (function_result, execution_time_seconds)
        """
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

    def _measure_memory_usage(
        self, func: Callable, *args, **kwargs
    ) -> tuple[Any, float]:
        """
        Measure memory usage increase of a function.

        Args:
            func: Function to measure
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Tuple of (function_result, memory_increase_mb)
        """
        import gc

        gc.collect()
        memory_before = self._get_memory_usage_mb()

        result = func(*args, **kwargs)

        gc.collect()
        memory_after = self._get_memory_usage_mb()

        memory_increase = memory_after - memory_before
        return result, memory_increase

    # MEMORY USAGE TESTS

    def test_memory_usage_open_settings(self):
        """Verify open() function memory usage is within limits."""
        result, memory_increase = self._measure_memory_usage(open, "WIFI")

        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"open() used {memory_increase:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

    def test_memory_usage_get_setting(self):
        """Verify get() function memory usage is within limits."""
        result, memory_increase = self._measure_memory_usage(get, "BATTERY")

        self.assertIsInstance(result, dict)
        self.assertIn("setting_type", result)
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"get() used {memory_increase:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

    def test_memory_usage_toggle_setting(self):
        """Verify on() and off() functions memory usage is within limits."""
        # Test on() function
        result_on, memory_increase_on = self._measure_memory_usage(on, "WIFI")
        self.assertIsInstance(result_on, dict)
        self.assertLessEqual(
            memory_increase_on,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"on() used {memory_increase_on:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

        # Test off() function
        result_off, memory_increase_off = self._measure_memory_usage(off, "WIFI")
        self.assertIsInstance(result_off, dict)
        self.assertLessEqual(
            memory_increase_off,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"off() used {memory_increase_off:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

    def test_memory_usage_volume_operations(self):
        """Verify volume control functions memory usage is within limits."""
        # Test set_volume
        result_set, memory_increase_set = self._measure_memory_usage(
            set_volume, 50, "MEDIA"
        )
        self.assertIsInstance(result_set, dict)
        self.assertLessEqual(
            memory_increase_set,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"set_volume() used {memory_increase_set:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

        # Test adjust_volume
        result_adjust, memory_increase_adjust = self._measure_memory_usage(
            adjust_volume, 10, "MEDIA"
        )
        self.assertIsInstance(result_adjust, dict)
        self.assertLessEqual(
            memory_increase_adjust,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"adjust_volume() used {memory_increase_adjust:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

        # Test mute
        result_mute, memory_increase_mute = self._measure_memory_usage(mute, "MEDIA")
        self.assertIsInstance(result_mute, dict)
        self.assertLessEqual(
            memory_increase_mute,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"mute() used {memory_increase_mute:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

        # Test unmute
        result_unmute, memory_increase_unmute = self._measure_memory_usage(
            unmute, "MEDIA"
        )
        self.assertIsInstance(result_unmute, dict)
        self.assertLessEqual(
            memory_increase_unmute,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"unmute() used {memory_increase_unmute:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

    def test_memory_usage_device_insights(self):
        """Verify get_device_insights() function memory usage is within limits."""
        result, memory_increase = self._measure_memory_usage(
            get_device_insights, "BATTERY"
        )

        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
            f"get_device_insights() used {memory_increase:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
        )

    def test_memory_usage_app_operations(self):
        """Verify app-related functions memory usage is within limits."""
        # Test get_installed_apps
        result_apps, memory_increase_apps = self._measure_memory_usage(
            get_installed_apps
        )
        self.assertIsInstance(result_apps, dict)
        self.assertIn("apps", result_apps)
        self.assertLessEqual(
            memory_increase_apps,
            self.MEMORY_THRESHOLD_APP_OPERATIONS,
            f"get_installed_apps() used {memory_increase_apps:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_APP_OPERATIONS}MB",
        )

        # Get an app name for testing
        app_names = result_apps.get("apps", [])
        if app_names:
            app_name = app_names[0]

            # Test get_app_notification_status
            result_status, memory_increase_status = self._measure_memory_usage(
                get_app_notification_status, app_name
            )
            self.assertIsInstance(result_status, dict)
            self.assertIn("app_name", result_status)
            self.assertLessEqual(
                memory_increase_status,
                self.MEMORY_THRESHOLD_APP_OPERATIONS,
                f"get_app_notification_status() used {memory_increase_status:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_APP_OPERATIONS}MB",
            )

            # Test set_app_notification_status
            result_set_status, memory_increase_set_status = self._measure_memory_usage(
                set_app_notification_status, app_name, "off"
            )
            self.assertIsInstance(result_set_status, dict)
            self.assertIn("result", result_set_status)
            self.assertLessEqual(
                memory_increase_set_status,
                self.MEMORY_THRESHOLD_APP_OPERATIONS,
                f"set_app_notification_status() used {memory_increase_set_status:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_APP_OPERATIONS}MB",
            )

    def test_memory_usage_bulk_volume_operations(self):
        """Verify bulk volume operations memory usage is within limits."""
        # Test muting all volumes
        result_mute_all, memory_increase_mute_all = self._measure_memory_usage(mute)
        self.assertIsInstance(result_mute_all, dict)
        self.assertLessEqual(
            memory_increase_mute_all,
            self.MEMORY_THRESHOLD_BULK_OPERATIONS,
            f"mute() all volumes used {memory_increase_mute_all:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_BULK_OPERATIONS}MB",
        )

        # Test unmuting all volumes
        result_unmute_all, memory_increase_unmute_all = self._measure_memory_usage(
            unmute
        )
        self.assertIsInstance(result_unmute_all, dict)
        self.assertLessEqual(
            memory_increase_unmute_all,
            self.MEMORY_THRESHOLD_BULK_OPERATIONS,
            f"unmute() all volumes used {memory_increase_unmute_all:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_BULK_OPERATIONS}MB",
        )

        # Test adjusting all volumes
        result_adjust_all, memory_increase_adjust_all = self._measure_memory_usage(
            adjust_volume, 5
        )
        self.assertIsInstance(result_adjust_all, dict)
        self.assertLessEqual(
            memory_increase_adjust_all,
            self.MEMORY_THRESHOLD_BULK_OPERATIONS,
            f"adjust_volume() all volumes used {memory_increase_adjust_all:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_BULK_OPERATIONS}MB",
        )

    # EXECUTION TIME TESTS

    def test_execution_time_open_settings(self):
        """Verify open() function execution time is within limits."""
        result, execution_time = self._measure_execution_time(open, "BLUETOOTH")

        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertLessEqual(
            execution_time,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"open() took {execution_time:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )

    def test_execution_time_get_setting(self):
        """Verify get() function execution time is within limits."""
        result, execution_time = self._measure_execution_time(get, "MEDIA_VOLUME")

        self.assertIsInstance(result, dict)
        self.assertIn("setting_type", result)
        self.assertLessEqual(
            execution_time,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"get() took {execution_time:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )

    def test_execution_time_toggle_settings(self):
        """Verify on() and off() functions execution time is within limits."""
        # Test on() function
        result_on, execution_time_on = self._measure_execution_time(on, "BLUETOOTH")
        self.assertIsInstance(result_on, dict)
        self.assertLessEqual(
            execution_time_on,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"on() took {execution_time_on:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )

        # Test off() function
        result_off, execution_time_off = self._measure_execution_time(off, "BLUETOOTH")
        self.assertIsInstance(result_off, dict)
        self.assertLessEqual(
            execution_time_off,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"off() took {execution_time_off:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )

    def test_execution_time_volume_operations(self):
        """Verify volume control functions execution time is within limits."""
        # Test set_volume
        result_set, execution_time_set = self._measure_execution_time(
            set_volume, 75, "RING"
        )
        self.assertIsInstance(result_set, dict)
        self.assertLessEqual(
            execution_time_set,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"set_volume() took {execution_time_set:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )

        # Test adjust_volume
        result_adjust, execution_time_adjust = self._measure_execution_time(
            adjust_volume, -10, "RING"
        )
        self.assertIsInstance(result_adjust, dict)
        self.assertLessEqual(
            execution_time_adjust,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"adjust_volume() took {execution_time_adjust:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )

        # Test mute
        result_mute, execution_time_mute = self._measure_execution_time(mute, "RING")
        self.assertIsInstance(result_mute, dict)
        self.assertLessEqual(
            execution_time_mute,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"mute() took {execution_time_mute:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )

        # Test unmute
        result_unmute, execution_time_unmute = self._measure_execution_time(
            unmute, "RING"
        )
        self.assertIsInstance(result_unmute, dict)
        self.assertLessEqual(
            execution_time_unmute,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"unmute() took {execution_time_unmute:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )

    def test_execution_time_device_insights(self):
        """Verify get_device_insights() function execution time is within limits."""
        result, execution_time = self._measure_execution_time(
            get_device_insights, "STORAGE"
        )

        self.assertIsInstance(result, dict)
        self.assertIn("result", result)
        self.assertLessEqual(
            execution_time,
            self.TIME_THRESHOLD_COMPLEX_OPERATIONS,
            f"get_device_insights() took {execution_time:.3f}s, exceeds limit of {self.TIME_THRESHOLD_COMPLEX_OPERATIONS}s",
        )

    def test_execution_time_app_operations(self):
        """Verify app-related functions execution time is within limits."""
        # Test get_installed_apps
        result_apps, execution_time_apps = self._measure_execution_time(
            get_installed_apps
        )
        self.assertIsInstance(result_apps, dict)
        self.assertIn("apps", result_apps)
        self.assertLessEqual(
            execution_time_apps,
            self.TIME_THRESHOLD_COMPLEX_OPERATIONS,
            f"get_installed_apps() took {execution_time_apps:.3f}s, exceeds limit of {self.TIME_THRESHOLD_COMPLEX_OPERATIONS}s",
        )

        # Get an app name for testing
        app_names = result_apps.get("apps", [])
        if app_names:
            app_name = app_names[0]

            # Test get_app_notification_status
            result_status, execution_time_status = self._measure_execution_time(
                get_app_notification_status, app_name
            )
            self.assertIsInstance(result_status, dict)
            self.assertIn("app_name", result_status)
            self.assertLessEqual(
                execution_time_status,
                self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
                f"get_app_notification_status() took {execution_time_status:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
            )

            # Test set_app_notification_status
            result_set_status, execution_time_set_status = self._measure_execution_time(
                set_app_notification_status, app_name, "on"
            )
            self.assertIsInstance(result_set_status, dict)
            self.assertIn("result", result_set_status)
            self.assertLessEqual(
                execution_time_set_status,
                self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
                f"set_app_notification_status() took {execution_time_set_status:.3f}s, exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
            )

    def test_execution_time_bulk_operations(self):
        """Verify bulk operations execution time is within limits."""
        # Test muting all volumes
        result_mute_all, execution_time_mute_all = self._measure_execution_time(mute)
        self.assertIsInstance(result_mute_all, dict)
        self.assertLessEqual(
            execution_time_mute_all,
            self.TIME_THRESHOLD_BULK_OPERATIONS,
            f"mute() all volumes took {execution_time_mute_all:.3f}s, exceeds limit of {self.TIME_THRESHOLD_BULK_OPERATIONS}s",
        )

        # Test unmuting all volumes
        result_unmute_all, execution_time_unmute_all = self._measure_execution_time(
            unmute
        )
        self.assertIsInstance(result_unmute_all, dict)
        self.assertLessEqual(
            execution_time_unmute_all,
            self.TIME_THRESHOLD_BULK_OPERATIONS,
            f"unmute() all volumes took {execution_time_unmute_all:.3f}s, exceeds limit of {self.TIME_THRESHOLD_BULK_OPERATIONS}s",
        )

        # Test setting all volumes
        result_set_all, execution_time_set_all = self._measure_execution_time(
            set_volume, 80
        )
        self.assertIsInstance(result_set_all, dict)
        self.assertLessEqual(
            execution_time_set_all,
            self.TIME_THRESHOLD_BULK_OPERATIONS,
            f"set_volume() all volumes took {execution_time_set_all:.3f}s, exceeds limit of {self.TIME_THRESHOLD_BULK_OPERATIONS}s",
        )

        # Test adjusting all volumes
        result_adjust_all, execution_time_adjust_all = self._measure_execution_time(
            adjust_volume, -5
        )
        self.assertIsInstance(result_adjust_all, dict)
        self.assertLessEqual(
            execution_time_adjust_all,
            self.TIME_THRESHOLD_BULK_OPERATIONS,
            f"adjust_volume() all volumes took {execution_time_adjust_all:.3f}s, exceeds limit of {self.TIME_THRESHOLD_BULK_OPERATIONS}s",
        )

    # EXCEPTION BEHAVIOR TESTS FOR PERFORMANCE EDGE CASES

    def test_error_behavior_performance(self):
        """Test that error handling is efficient and doesn't cause performance issues."""
        # These tests focus on ensuring error handling doesn't cause memory leaks or excessive delays

        # Test a few key error cases
        error_test_cases = [
            lambda: get("INVALID_SETTING"),
            lambda: set_volume(150),
            lambda: get_app_notification_status("NonExistentApp"),
        ]

        for i, test_case in enumerate(error_test_cases):
            case_memory_before = self._get_memory_usage_mb()
            case_start = time.perf_counter()

            # Simply verify that the exception is raised correctly
            with self.assertRaises(ValueError):
                test_case()

            case_end = time.perf_counter()
            case_memory_after = self._get_memory_usage_mb()

            case_time = case_end - case_start
            case_memory_increase = case_memory_after - case_memory_before

            # Use more reasonable thresholds for error handling
            # Error handling can be slower than normal operations due to validation
            self.assertLessEqual(
                case_time,
                0.5,  # 500ms is reasonable for error handling including validation
                f"Error case {i+1} took {case_time:.3f}s, exceeds limit of 0.5s",
            )

            # Verify error handling doesn't consume excessive memory
            self.assertLessEqual(
                case_memory_increase,
                self.MEMORY_THRESHOLD_CORE_FUNCTIONS,
                f"Error case {i+1} used {case_memory_increase:.2f}MB, exceeds limit of {self.MEMORY_THRESHOLD_CORE_FUNCTIONS}MB",
            )

    # STRESS TESTS FOR REPEATED OPERATIONS

    def test_repeated_operations_performance(self):
        """Test performance under repeated operations to check for memory leaks or degradation."""
        # Perform multiple consecutive operations
        operations_count = 10

        start_memory = self._get_memory_usage_mb()
        start_time = time.perf_counter()

        # Perform repeated operations
        for i in range(operations_count):
            # Alternate between different operations
            get("WIFI")
            on("AIRPLANE_MODE")
            off("AIRPLANE_MODE")
            set_volume(50 + (i % 5) * 10, "MEDIA")

        end_time = time.perf_counter()
        end_memory = self._get_memory_usage_mb()

        total_time = end_time - start_time
        memory_increase = end_memory - start_memory

        # Check that repeated operations don't cause excessive memory growth
        self.assertLessEqual(
            memory_increase,
            self.MEMORY_THRESHOLD_BULK_OPERATIONS,
            f"Repeated operations caused {memory_increase:.2f}MB memory increase, exceeds limit of {self.MEMORY_THRESHOLD_BULK_OPERATIONS}MB",
        )

        # Check that repeated operations complete in reasonable time
        average_time_per_operation = total_time / (
            operations_count * 4
        )  # 4 operations per iteration
        self.assertLessEqual(
            average_time_per_operation,
            self.TIME_THRESHOLD_SIMPLE_OPERATIONS,
            f"Average time per operation {average_time_per_operation:.3f}s exceeds limit of {self.TIME_THRESHOLD_SIMPLE_OPERATIONS}s",
        )


if __name__ == "__main__":
    unittest.main()
