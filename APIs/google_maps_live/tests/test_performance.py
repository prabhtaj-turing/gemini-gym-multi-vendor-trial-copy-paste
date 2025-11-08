# google_maps_live/tests/test_performance.py
import unittest
import time
import gc
import statistics
import psutil
import os
import tempfile
import json
from typing import Callable, List
from unittest.mock import patch

from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_maps_live.SimulationEngine.utils import (
    parse_json_from_gemini_response,
    get_location_from_env,
    add_recent_search,
    get_recent_searches
)
from google_maps_live.SimulationEngine.db import DB, save_state, load_state
from google_maps_live.SimulationEngine.models import TravelMode, UserLocation, Place


class PerformanceTest(BaseTestCaseWithErrorHandler):
    """Performance tests for google_maps_live API operations."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.process = psutil.Process()
        
        # Store original DB state
        self.original_db = DB.copy()
        
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.test_filepath = os.path.join(self.test_dir, 'test_db.json')
        
        # Clear DB for clean testing
        DB.clear()
        DB['recent_searches'] = {}
        DB['user_locations'] = {}

    def tearDown(self):
        """Clean up test environment."""
        super().tearDown()
        
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db)
        
        # Clean up test files
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        if os.path.exists(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)
        
        # Force garbage collection
        gc.collect()

    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def stress_test_memory_usage(self, operation_func: Callable, iterations: int = 1000) -> List[float]:
        """Test memory usage under stress."""
        memory_usage = []
        
        for i in range(iterations):
            memory_before = self.get_memory_usage_mb()
            
            try:
                operation_func()
            except Exception:
                pass  # Ignore errors for stress testing
            
            memory_after = self.get_memory_usage_mb()
            memory_usage.append(memory_after - memory_before)
            
            # Force garbage collection every 100 iterations
            if i % 100 == 0:
                gc.collect()
        
        print(f"Memory usage - Peak: {max(memory_usage):.2f}MB, Avg: {statistics.mean(memory_usage):.2f}MB")
        return memory_usage

    def test_parse_json_performance(self):
        """Test performance of JSON parsing operations."""
        simple_json = '{"key": "value", "number": 42, "array": [1, 2, 3]}'
        complex_json = '{"map_url": "https://maps.google.com", "travel_mode": "driving", "routes": [{"route_id": "route_1"}]}'
        
        # Test simple JSON parsing performance
        start_time = time.time()
        for _ in range(1000):
            parse_json_from_gemini_response(simple_json)
        simple_time = time.time() - start_time
        
        # Test complex JSON parsing performance
        start_time = time.time()
        for _ in range(1000):
            parse_json_from_gemini_response(complex_json)
        complex_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(simple_time, 1.0, f"Simple JSON parsing took {simple_time:.3f}s, should be under 1s")
        self.assertLess(complex_time, 2.0, f"Complex JSON parsing took {complex_time:.3f}s, should be under 2s")
        
        print(f"JSON Parsing Performance:")
        print(f"  Simple JSON (1000 iterations): {simple_time:.3f}s")
        print(f"  Complex JSON (1000 iterations): {complex_time:.3f}s")

    def test_location_env_performance(self):
        """Test performance of environment variable location resolution."""
        test_env = {
            'MY_HOME': '123 Home St, Mountain View, CA',
            'MY_LOCATION': '456 Current Ave, Palo Alto, CA',
            'MY_WORK': '789 Work Blvd, San Francisco, CA'
        }
        
        with patch.dict(os.environ, test_env):
            start_time = time.time()
            for _ in range(1000):
                get_location_from_env('MY_HOME')
                get_location_from_env('MY_LOCATION')
                get_location_from_env('MY_WORK')
            total_time = time.time() - start_time
            
            self.assertLess(total_time, 1.0, f"Location resolution took {total_time:.3f}s, should be under 1s")
            print(f"Location Resolution Performance (3000 operations): {total_time:.3f}s")

    def test_recent_search_performance(self):
        """Test performance of recent search operations."""
        test_params = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        test_result = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        
        # Test add_recent_search performance
        start_time = time.time()
        for i in range(1000):
            add_recent_search(f"test_endpoint_{i}", test_params, test_result)
        add_time = time.time() - start_time
        
        # Test get_recent_searches performance
        start_time = time.time()
        for i in range(1000):
            get_recent_searches("test_endpoint_0")
        get_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(add_time, 2.0, f"Adding recent searches took {add_time:.3f}s, should be under 2s")
        self.assertLess(get_time, 1.0, f"Getting recent searches took {get_time:.3f}s, should be under 1s")
        
        print(f"Recent Search Performance:")
        print(f"  Add operations (1000): {add_time:.3f}s")
        print(f"  Get operations (1000): {get_time:.3f}s")

    def test_db_operations_performance(self):
        """Test performance of database operations."""
        test_data = {
            "user_locations": {
                "home": {"lat": 37.7749, "lng": -122.4194, "name": "Home"},
                "work": {"lat": 37.7849, "lng": -122.4094, "name": "Work"}
            },
            "recent_searches": ["San Francisco", "New York", "London"],
            "favorites": {
                "places": ["Golden Gate Bridge", "Alcatraz"],
                "routes": ["home_to_work", "work_to_gym"]
            }
        }
        
        # Test save_state performance
        DB.update(test_data)
        start_time = time.time()
        for _ in range(100):
            save_state(self.test_filepath)
        save_time = time.time() - start_time
        
        # Test load_state performance
        start_time = time.time()
        for _ in range(100):
            load_state(self.test_filepath)
        load_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(save_time, 5.0, f"Saving state took {save_time:.3f}s, should be under 5s")
        self.assertLess(load_time, 5.0, f"Loading state took {load_time:.3f}s, should be under 5s")
        
        print(f"Database Operations Performance:")
        print(f"  Save operations (100): {save_time:.3f}s")
        print(f"  Load operations (100): {load_time:.3f}s")

    def test_model_validation_performance(self):
        """Test performance of Pydantic model validation."""
        test_place_data = {
            "id": "place_123",
            "name": "Sample Restaurant",
            "description": "A great place to eat",
            "rating": "4.2",
            "url": "https://example.com/restaurant",
            "map_url": "https://maps.google.com/place",
            "review_count": 150,
            "user_rating_count": 150,
            "address": "123 Main St, City, CA",
            "phone_number": "+1-555-0123"
        }
        
        # Test Place model validation performance
        start_time = time.time()
        for _ in range(1000):
            Place(**test_place_data)
        place_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(place_time, 2.0, f"Place validation took {place_time:.3f}s, should be under 2s")
        print(f"Model Validation Performance:")
        print(f"  Place validation (1000): {place_time:.3f}s")

    def test_memory_usage_stress(self):
        """Test memory usage under stress conditions."""
        # Test memory usage for repeated JSON parsing
        memory_usage = self.stress_test_memory_usage(
            lambda: parse_json_from_gemini_response('{"test": "data", "number": 42}'),
            iterations=200
        )
        
        # Memory usage should be reasonable
        peak_memory = max(memory_usage)
        avg_memory = statistics.mean(memory_usage)
        
        self.assertLess(peak_memory, 50.0, f"Peak memory usage {peak_memory:.2f}MB is too high")
        self.assertLess(avg_memory, 10.0, f"Average memory usage {avg_memory:.2f}MB is too high")
        
        print(f"Memory Stress Test Results:")
        print(f"  Peak memory usage: {peak_memory:.2f}MB")
        print(f"  Average memory usage: {avg_memory:.2f}MB")

    def test_concurrent_operations_performance(self):
        """Test performance under concurrent-like operations."""
        start_time = time.time()
        
        for i in range(100):
            # Add recent search
            add_recent_search(f"endpoint_{i}", {"param": f"value_{i}"}, {"result": f"data_{i}"})
            
            # Get recent searches
            get_recent_searches(f"endpoint_{i}")
            
            # Parse JSON
            parse_json_from_gemini_response(f'{{"iteration": {i}, "data": "test"}}')
            
            # Validate model
            if i % 10 == 0:  # Every 10th iteration
                Place(
                    id=f"place_{i}",
                    name=f"Place {i}",
                    rating="4.0",
                    review_count=100,
                    user_rating_count=100,
                    address=f"Address {i}",
                    phone_number="+1-555-0000"
                )
        
        total_time = time.time() - start_time
        
        # Performance assertion
        self.assertLess(total_time, 10.0, f"Concurrent operations took {total_time:.3f}s, should be under 10s")
        print(f"Concurrent Operations Performance (400 operations): {total_time:.3f}s")

    def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        # Create large dataset
        large_data = {}
        for i in range(1000):
            large_data[f'location_{i}'] = {
                'lat': 37.7749 + (i * 0.001),
                'lng': -122.4194 + (i * 0.001),
                'name': f'Location {i}',
                'metadata': {
                    'created_at': f'2024-01-{i%28+1:02d}T00:00:00Z',
                    'tags': [f'tag_{j}' for j in range(i % 5 + 1)]
                }
            }
        
        # Test save performance with large dataset
        DB.update(large_data)
        start_time = time.time()
        save_state(self.test_filepath)
        save_time = time.time() - start_time
        
        # Test load performance with large dataset
        DB.clear()
        start_time = time.time()
        load_state(self.test_filepath)
        load_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(save_time, 5.0, f"Saving large dataset took {save_time:.3f}s, should be under 5s")
        self.assertLess(load_time, 5.0, f"Loading large dataset took {load_time:.3f}s, should be under 5s")
        
        print(f"Large Dataset Performance:")
        print(f"  Save (1000 locations): {save_time:.3f}s")
        print(f"  Load (1000 locations): {load_time:.3f}s")

    def test_enum_operations_performance(self):
        """Test performance of enum operations."""
        # Test TravelMode enum operations
        start_time = time.time()
        for _ in range(10000):
            TravelMode.DRIVING
            TravelMode.WALKING
            TravelMode.BICYCLING
            TravelMode.TRANSIT
            TravelMode.values()
            TravelMode.names()
        travel_mode_time = time.time() - start_time
        
        # Test UserLocation enum operations
        start_time = time.time()
        for _ in range(10000):
            UserLocation.MY_HOME
            UserLocation.MY_LOCATION
            UserLocation.MY_WORK
            UserLocation.values()
            UserLocation.names()
        user_location_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(travel_mode_time, 1.0, f"TravelMode operations took {travel_mode_time:.3f}s, should be under 1s")
        self.assertLess(user_location_time, 1.0, f"UserLocation operations took {user_location_time:.3f}s, should be under 1s")
        
        print(f"Enum Operations Performance (10000 iterations each):")
        print(f"  TravelMode: {travel_mode_time:.3f}s")
        print(f"  UserLocation: {user_location_time:.3f}s")

    def test_memory_leak_detection(self):
        """Test for potential memory leaks."""
        initial_memory = self.get_memory_usage_mb()
        
        # Perform operations that might cause memory leaks
        for i in range(100):
            # Create and process data
            test_data = {
                "locations": [{"lat": 37.7749 + i*0.001, "lng": -122.4194 + i*0.001} for _ in range(100)],
                "searches": [f"search_{j}" for j in range(100)]
            }
            
            # Add to recent searches
            add_recent_search(f"test_{i}", test_data, {"result": "data"})
            
            # Parse JSON
            parse_json_from_gemini_response(json.dumps(test_data))
            
            # Force garbage collection every 10 iterations
            if i % 10 == 0:
                gc.collect()
        
        # Force final garbage collection
        gc.collect()
        
        final_memory = self.get_memory_usage_mb()
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100.0, 
                       f"Memory increased by {memory_increase:.2f}MB, potential memory leak detected")
        
        print(f"Memory Leak Detection:")
        print(f"  Initial memory: {initial_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Memory increase: {memory_increase:.2f}MB")


if __name__ == '__main__':
    unittest.main()
