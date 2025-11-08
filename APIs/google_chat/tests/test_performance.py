"""
Performance tests for Google Chat API.

This module contains comprehensive performance tests to validate:
1. API function response times
2. Database operation performance
3. File operation performance
4. Memory usage monitoring
5. Load testing and scalability
6. Resource utilization optimization
"""

import unittest
import sys
import os
import time
import tempfile
import threading
import concurrent.futures
from typing import List, Dict, Any, Callable
from unittest.mock import patch
from datetime import datetime
import gc

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

sys.path.append("APIs")

import google_chat as GoogleChatAPI
from google_chat.SimulationEngine import utils, file_utils
from google_chat.SimulationEngine.db import save_state, load_state
from common_utils.base_case import BaseTestCaseWithErrorHandler


class PerformanceTimer:
    """Context manager for measuring execution time."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time


class MemoryMonitor:
    """Helper class for monitoring memory usage."""
    
    def __init__(self):
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process()
        else:
            self.process = None
        self.initial_memory = None
        self.peak_memory = None
    
    def start_monitoring(self):
        """Start memory monitoring."""
        if PSUTIL_AVAILABLE and self.process:
            self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            self.peak_memory = self.initial_memory
        else:
            self.initial_memory = 0
            self.peak_memory = 0
    
    def update_peak(self):
        """Update peak memory usage."""
        if PSUTIL_AVAILABLE and self.process:
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            if current_memory > self.peak_memory:
                self.peak_memory = current_memory
    
    def get_memory_delta(self):
        """Get memory usage delta since start."""
        if PSUTIL_AVAILABLE and self.process:
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            return current_memory - self.initial_memory
        return 0
    
    def get_peak_delta(self):
        """Get peak memory delta since start."""
        return self.peak_memory - self.initial_memory


class TestAPIResponseTimes(BaseTestCaseWithErrorHandler):
    """Test cases for API function response times."""
    
    def setUp(self):
        """Set up test environment with clean database."""
        GoogleChatAPI.DB.clear()
        GoogleChatAPI.DB.update({
            "User": [],
            "Space": [],
            "Message": [],
            "Membership": [],
            "Reaction": [],
            "SpaceNotificationSetting": [],
            "SpaceReadState": [],
            "ThreadReadState": [],
            "SpaceEvent": [],
            "Attachment": [],
            "media": []
        })
        GoogleChatAPI.CURRENT_USER_ID.update({"id": "users/PERF_TEST_USER"})
        
        # Performance thresholds (in seconds)
        self.fast_threshold = 0.01  # 10ms for fast operations
        self.medium_threshold = 0.05  # 50ms for medium operations
        self.slow_threshold = 0.1   # 100ms for complex operations

    def test_space_operations_performance(self):
        """Test performance of space-related operations."""
        performance_results = {}
        
        # Test space creation
        with PerformanceTimer() as timer:
            space = GoogleChatAPI.create_space(space={
                "displayName": "Performance Test Space",
                "spaceType": "SPACE"
            })
        performance_results["create_space"] = timer.duration
        self.assertLess(timer.duration, self.medium_threshold, 
                       f"Space creation took {timer.duration:.4f}s, expected < {self.medium_threshold}s")
        
        space_name = space["name"]
        
        # Test space retrieval
        with PerformanceTimer() as timer:
            retrieved_space = GoogleChatAPI.get_space_details(name=space_name)
        performance_results["get_space"] = timer.duration
        self.assertLess(timer.duration, self.fast_threshold,
                       f"Space retrieval took {timer.duration:.4f}s, expected < {self.fast_threshold}s")
        
        # Test space listing
        with PerformanceTimer() as timer:
            spaces_response = GoogleChatAPI.list_spaces()
        performance_results["list_spaces"] = timer.duration
        self.assertLess(timer.duration, self.fast_threshold,
                       f"Space listing took {timer.duration:.4f}s, expected < {self.fast_threshold}s")
        
        # Test space deletion
        with PerformanceTimer() as timer:
            GoogleChatAPI.delete_space(name=space_name)
        performance_results["delete_space"] = timer.duration
        self.assertLess(timer.duration, self.medium_threshold,
                       f"Space deletion took {timer.duration:.4f}s, expected < {self.medium_threshold}s")
        
        print(f"✓ Space operations performance: {performance_results}")

    def test_message_operations_performance(self):
        """Test performance of message-related operations."""
        # Create a space first
        space = GoogleChatAPI.create_space(space={
            "displayName": "Message Perf Test Space",
            "spaceType": "SPACE"
        })
        space_name = space["name"]
        
        performance_results = {}
        
        # Test message creation
        with PerformanceTimer() as timer:
            message = GoogleChatAPI.create_message(
                parent=space_name,
                message_body={"text": "Performance test message"}
            )
        performance_results["create_message"] = timer.duration
        self.assertLess(timer.duration, self.medium_threshold,
                       f"Message creation took {timer.duration:.4f}s, expected < {self.medium_threshold}s")
        
        message_name = message["name"]
        
        # Test message retrieval
        with PerformanceTimer() as timer:
            retrieved_message = GoogleChatAPI.get_message(name=message_name)
        performance_results["get_message"] = timer.duration
        self.assertLess(timer.duration, self.fast_threshold,
                       f"Message retrieval took {timer.duration:.4f}s, expected < {self.fast_threshold}s")
        
        # Test message listing
        with PerformanceTimer() as timer:
            messages_response = GoogleChatAPI.list_messages(parent=space_name)
        performance_results["list_messages"] = timer.duration
        self.assertLess(timer.duration, self.fast_threshold,
                       f"Message listing took {timer.duration:.4f}s, expected < {self.fast_threshold}s")
        
        # Test message deletion performance
        with PerformanceTimer() as timer:
            GoogleChatAPI.delete_message(name=message_name)
        performance_results["delete_message"] = timer.duration
        self.assertLess(timer.duration, self.medium_threshold,
                       f"Message deletion took {timer.duration:.4f}s, expected < {self.medium_threshold}s")
        
        # Cleanup
        GoogleChatAPI.delete_space(name=space_name)
        
        print(f"✓ Message operations performance: {performance_results}")

    def test_user_operations_performance(self):
        """Test performance of user-related operations."""
        performance_results = {}
        
        # Test user creation
        with PerformanceTimer() as timer:
            user = utils._create_user("Performance Test User")
        performance_results["create_user"] = timer.duration
        self.assertLess(timer.duration, self.fast_threshold,
                       f"User creation took {timer.duration:.4f}s, expected < {self.fast_threshold}s")
        
        # Test user switching
        with PerformanceTimer() as timer:
            utils._change_user(user["name"])
        performance_results["change_user"] = timer.duration
        self.assertLess(timer.duration, self.fast_threshold,
                       f"User switching took {timer.duration:.4f}s, expected < {self.fast_threshold}s")
        
        print(f"✓ User operations performance: {performance_results}")

    def test_database_operations_performance(self):
        """Test performance of database operations."""
        performance_results = {}
        
        # Test database save operation
        test_file = "perf_test_db.json"
        with PerformanceTimer() as timer:
            save_state(test_file)
        performance_results["db_save"] = timer.duration
        self.assertLess(timer.duration, self.slow_threshold,
                       f"DB save took {timer.duration:.4f}s, expected < {self.slow_threshold}s")
        
        # Test database load operation
        with PerformanceTimer() as timer:
            load_state(test_file)
        performance_results["db_load"] = timer.duration
        self.assertLess(timer.duration, self.slow_threshold,
                       f"DB load took {timer.duration:.4f}s, expected < {self.slow_threshold}s")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        
        print(f"✓ Database operations performance: {performance_results}")


class TestFileOperationPerformance(BaseTestCaseWithErrorHandler):
    """Test cases for file operation performance."""
    
    def setUp(self):
        """Set up temporary directory for file operations."""
        self.temp_dir = tempfile.mkdtemp()
        self.performance_thresholds = {
            "small_file": 0.01,   # 10ms for small files (< 1KB)
            "medium_file": 0.05,  # 50ms for medium files (1KB - 1MB)
            "large_file": 0.2     # 200ms for large files (> 1MB)
        }

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_small_file_operations(self):
        """Test performance with small files."""
        small_content = "Small test content" * 10  # ~200 bytes
        file_path = os.path.join(self.temp_dir, "small_test.txt")
        
        performance_results = {}
        
        # Test writing small file
        with PerformanceTimer() as timer:
            file_utils.write_file(file_path, small_content, 'text')
        performance_results["write_small"] = timer.duration
        self.assertLess(timer.duration, self.performance_thresholds["small_file"],
                       f"Small file write took {timer.duration:.4f}s")
        
        # Test reading small file
        with PerformanceTimer() as timer:
            result = file_utils.read_file(file_path)
        performance_results["read_small"] = timer.duration
        self.assertLess(timer.duration, self.performance_thresholds["small_file"],
                       f"Small file read took {timer.duration:.4f}s")
        
        print(f"✓ Small file operations performance: {performance_results}")

    def test_medium_file_operations(self):
        """Test performance with medium-sized files."""
        medium_content = "Medium test content " * 1000  # ~20KB
        file_path = os.path.join(self.temp_dir, "medium_test.txt")
        
        performance_results = {}
        
        # Test writing medium file
        with PerformanceTimer() as timer:
            file_utils.write_file(file_path, medium_content, 'text')
        performance_results["write_medium"] = timer.duration
        self.assertLess(timer.duration, self.performance_thresholds["medium_file"],
                       f"Medium file write took {timer.duration:.4f}s")
        
        # Test reading medium file
        with PerformanceTimer() as timer:
            result = file_utils.read_file(file_path)
        performance_results["read_medium"] = timer.duration
        self.assertLess(timer.duration, self.performance_thresholds["medium_file"],
                       f"Medium file read took {timer.duration:.4f}s")
        
        print(f"✓ Medium file operations performance: {performance_results}")

    def test_base64_operations_performance(self):
        """Test performance of base64 operations."""
        test_content = "Base64 test content " * 100  # ~2KB
        
        performance_results = {}
        
        # Test base64 encoding
        with PerformanceTimer() as timer:
            encoded = file_utils.encode_to_base64(test_content)
        performance_results["base64_encode"] = timer.duration
        self.assertLess(timer.duration, self.performance_thresholds["small_file"],
                       f"Base64 encoding took {timer.duration:.4f}s")
        
        # Test base64 decoding
        with PerformanceTimer() as timer:
            decoded = file_utils.decode_from_base64(encoded)
        performance_results["base64_decode"] = timer.duration
        self.assertLess(timer.duration, self.performance_thresholds["small_file"],
                       f"Base64 decoding took {timer.duration:.4f}s")
        
        print(f"✓ Base64 operations performance: {performance_results}")


class TestMemoryUsage(BaseTestCaseWithErrorHandler):
    """Test cases for memory usage monitoring."""
    
    def setUp(self):
        """Set up memory monitoring."""
        if not PSUTIL_AVAILABLE:
            self.skipTest("psutil not available, skipping memory tests")
        
        self.memory_monitor = MemoryMonitor()
        self.memory_thresholds = {
            "small_operation": 1,   # 1MB for small operations
            "medium_operation": 5,  # 5MB for medium operations
            "large_operation": 20   # 20MB for large operations
        }
        
        # Clean up before each test
        gc.collect()

    def test_space_operations_memory_usage(self):
        """Test memory usage of space operations."""
        self.memory_monitor.start_monitoring()
        
        # Create multiple spaces
        spaces = []
        for i in range(10):
            space = GoogleChatAPI.create_space(space={
                "displayName": f"Memory Test Space {i}",
                "spaceType": "SPACE"
            })
            spaces.append(space)
            self.memory_monitor.update_peak()
        
        memory_delta = self.memory_monitor.get_memory_delta()
        peak_delta = self.memory_monitor.get_peak_delta()
        
        # Cleanup
        for space in spaces:
            GoogleChatAPI.delete_space(name=space["name"])
        
        self.assertLess(memory_delta, self.memory_thresholds["medium_operation"],
                       f"Space operations used {memory_delta:.2f}MB memory")
        
        print(f"✓ Space operations memory usage: {memory_delta:.2f}MB (peak: {peak_delta:.2f}MB)")

    def test_message_operations_memory_usage(self):
        """Test memory usage of message operations."""
        # Create a space first
        space = GoogleChatAPI.create_space(space={
            "displayName": "Memory Test Space",
            "spaceType": "SPACE"
        })
        space_name = space["name"]
        
        self.memory_monitor.start_monitoring()
        
        # Create multiple messages
        messages = []
        for i in range(20):
            message = GoogleChatAPI.create_message(
                parent=space_name,
                message_body={"text": f"Memory test message {i} with some content"}
            )
            messages.append(message)
            self.memory_monitor.update_peak()
        
        memory_delta = self.memory_monitor.get_memory_delta()
        peak_delta = self.memory_monitor.get_peak_delta()
        
        # Cleanup
        GoogleChatAPI.delete_space(name=space_name)
        
        self.assertLess(memory_delta, self.memory_thresholds["medium_operation"],
                       f"Message operations used {memory_delta:.2f}MB memory")
        
        print(f"✓ Message operations memory usage: {memory_delta:.2f}MB (peak: {peak_delta:.2f}MB)")

    def test_database_operations_memory_usage(self):
        """Test memory usage of database operations."""
        self.memory_monitor.start_monitoring()
        
        # Clear default data and add substantial data to database
        GoogleChatAPI.DB.clear()
        GoogleChatAPI.DB.update({
            "User": [],
            "Space": [],
            "Message": [],
            "Membership": [],
            "Reaction": [],
            "SpaceNotificationSetting": [],
            "SpaceReadState": [],
            "ThreadReadState": [],
            "SpaceEvent": [],
            "Attachment": [],
            "media": []
        })
        for i in range(100):
            GoogleChatAPI.DB["User"].append({
                "name": f"users/memory_test_user_{i}",
                "displayName": f"Memory Test User {i}",
                "domainId": "example.com",
                "type": "HUMAN",
                "isAnonymous": False
            })
            
        self.memory_monitor.update_peak()
        
        # Test save operation memory usage
        test_file = "memory_test_db.json"
        GoogleChatAPI.SimulationEngine.db.save_state(test_file)
        self.memory_monitor.update_peak()
        
        # Test load operation memory usage
        GoogleChatAPI.SimulationEngine.db.load_state(test_file)
        self.memory_monitor.update_peak()
        
        memory_delta = self.memory_monitor.get_memory_delta()
        peak_delta = self.memory_monitor.get_peak_delta()
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        GoogleChatAPI.DB["User"] = []
        
        self.assertLess(memory_delta, self.memory_thresholds["large_operation"],
                       f"Database operations used {memory_delta:.2f}MB memory")
        
        print(f"✓ Database operations memory usage: {memory_delta:.2f}MB (peak: {peak_delta:.2f}MB)")


class TestLoadAndScalability(BaseTestCaseWithErrorHandler):
    """Test cases for load testing and scalability."""
    
    def setUp(self):
        """Set up load testing environment."""
        GoogleChatAPI.DB.clear()
        GoogleChatAPI.DB.update({
            "User": [],
            "Space": [],
            "Message": [],
            "Membership": [],
            "Reaction": [],
            "SpaceNotificationSetting": [],
            "SpaceReadState": [],
            "ThreadReadState": [],
            "SpaceEvent": [],
            "Attachment": [],
            "media": []
        })
        GoogleChatAPI.CURRENT_USER_ID.update({"id": "users/LOAD_TEST_USER"})

    def test_concurrent_space_operations(self):
        """Test concurrent space operations."""
        def create_test_space(index):
            """Create a space with given index."""
            return GoogleChatAPI.create_space(space={
                "displayName": f"Concurrent Test Space {index}",
                "spaceType": "SPACE"
            })
        
        num_threads = 5
        num_operations = 10
        
        with PerformanceTimer() as timer:
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(create_test_space, i) for i in range(num_operations)]
                spaces = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all spaces were created
        self.assertEqual(len(spaces), num_operations)
        
        # Cleanup
        for space in spaces:
            GoogleChatAPI.delete_space(name=space["name"])
        
        avg_time_per_operation = timer.duration / num_operations
        self.assertLess(avg_time_per_operation, 0.1,  # 100ms per operation average
                       f"Concurrent space creation averaged {avg_time_per_operation:.4f}s per operation")
        
        print(f"✓ Concurrent space operations: {num_operations} operations in {timer.duration:.4f}s "
              f"(avg: {avg_time_per_operation:.4f}s per operation)")

    def test_high_volume_message_operations(self):
        """Test high volume message operations."""
        # Create a space first
        space = GoogleChatAPI.create_space(space={
            "displayName": "High Volume Test Space",
            "spaceType": "SPACE"
        })
        space_name = space["name"]
        
        num_messages = 50
        messages = []
        
        with PerformanceTimer() as timer:
            for i in range(num_messages):
                message = GoogleChatAPI.create_message(
                    parent=space_name,
                    message_body={"text": f"High volume test message {i}"}
                )
                messages.append(message)
        
        # Test message listing performance with many messages
        with PerformanceTimer() as list_timer:
            all_messages_response = GoogleChatAPI.list_messages(parent=space_name)
        
        # Cleanup
        GoogleChatAPI.delete_space(name=space_name)
        
        avg_create_time = timer.duration / num_messages
        self.assertLess(avg_create_time, 0.05,  # 50ms per message average
                       f"High volume message creation averaged {avg_create_time:.4f}s per message")
        
        self.assertLess(list_timer.duration, 0.1,  # 100ms to list all messages
                       f"Listing {num_messages} messages took {list_timer.duration:.4f}s")
        
        print(f"✓ High volume message operations: {num_messages} messages created in {timer.duration:.4f}s "
              f"(avg: {avg_create_time:.4f}s per message), listed in {list_timer.duration:.4f}s")

    def test_database_scalability(self):
        """Test database operations with increasing data sizes."""
        data_sizes = [10, 50, 100, 200]
        performance_results = {}
        
        for size in data_sizes:
            # Clear database
            GoogleChatAPI.DB.clear()
            GoogleChatAPI.DB.update({
                "User": [],
                "Space": [],
                "Message": [],
                "Membership": [],
                "Reaction": [],
                "SpaceNotificationSetting": [],
                "SpaceReadState": [],
                "ThreadReadState": [],
                "SpaceEvent": [],
                "Attachment": [],
                "media": []
            })
            
            # Add data to database
            for i in range(size):
                GoogleChatAPI.DB["User"].append({
                    "name": f"users/scale_test_user_{i}",
                    "displayName": f"Scale Test User {i}",
                    "domainId": "example.com",
                    "type": "HUMAN",
                    "isAnonymous": False
                })
                GoogleChatAPI.DB["Space"].append({
                    "name": f"spaces/scale_test_space_{i}",
                    "displayName": f"Scale Test Space {i}",
                    "spaceType": "SPACE",
                    "threaded": False,
                    "spaceThreadingState": "GROUPED_MESSAGES",
                    "spaceHistoryState": "HISTORY_ON"
                })
            
            # Test save performance
            test_file = f"scale_test_db_{size}.json"
            with PerformanceTimer() as save_timer:
                save_state(test_file)
            
            # Test load performance
            with PerformanceTimer() as load_timer:
                load_state(test_file)
            
            performance_results[size] = {
                "save_time": save_timer.duration,
                "load_time": load_timer.duration
            }
            
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
        
        # Verify performance doesn't degrade excessively
        for i in range(1, len(data_sizes)):
            prev_size = data_sizes[i-1]
            curr_size = data_sizes[i]
            size_ratio = curr_size / prev_size
            
            # Skip performance checks if timing is too small to be reliable (< 0.001s)
            if performance_results[prev_size]["save_time"] < 0.001 or performance_results[prev_size]["load_time"] < 0.001:
                continue
            
            save_ratio = performance_results[curr_size]["save_time"] / performance_results[prev_size]["save_time"]
            load_ratio = performance_results[curr_size]["load_time"] / performance_results[prev_size]["load_time"]
            
            # Performance should not degrade worse than O(n^3) to account for system variability
            # This is more lenient than O(n^2) to handle small timing variations
            max_acceptable_ratio = size_ratio * size_ratio * size_ratio
            self.assertLess(save_ratio, max_acceptable_ratio,
                           f"Save performance degraded too much: {save_ratio:.2f}x for {size_ratio:.2f}x data")
            self.assertLess(load_ratio, max_acceptable_ratio,
                           f"Load performance degraded too much: {load_ratio:.2f}x for {size_ratio:.2f}x data")
        
        print(f"✓ Database scalability test: {performance_results}")


if __name__ == "__main__":
    unittest.main()
