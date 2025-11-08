"""
Performance test suite for Google Maps API module.

This test suite validates:
1. Memory usage of key functions stays within reasonable limits
2. Execution time of operations meets performance requirements
3. Performance behavior under various load conditions
4. Error handling performance using BaseTestCaseWithErrorHandler

Performance Thresholds:
- Memory usage: < 50MB per operation for most functions
- Execution time: < 1 second for most operations
- Bulk operations: < 5 seconds for large datasets
- Database operations: < 100ms for single operations

Author: Auto-generated performance test suite
"""

import unittest
import time
import psutil
import os
import tempfile
import uuid
from typing import Dict, Any, List
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_maps.SimulationEngine.utils import _create_place
from google_maps.SimulationEngine.db import DB
from pydantic import ValidationError


class TestGoogleMapsPerformance(BaseTestCaseWithErrorHandler):
    """Performance test case for Google Maps core functions."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data before all tests in this class."""
        # Add test data to the DB
        place_with_photo = {
            "id": "test_place",
            "name": "Test Place with Photo",
            "photos": [
                {
                    "name": "places/test_place/photos/test_photo",
                    "widthPx": 1024,
                    "heightPx": 768,
                }
            ],
        }
        place_simple = {"id": "test_place_id", "name": "Test Place Simple"}
        if "test_place" not in DB:
            _create_place(place_with_photo)
        if "test_place_id" not in DB:
            _create_place(place_simple)

    def setUp(self):
        """Set up test fixtures and performance monitoring."""
        # Get current process for memory monitoring
        self.process = psutil.Process(os.getpid())
        
        # Performance thresholds (documented for clarity)
        self.memory_limits = {
            'light_operation': 10 * 1024 * 1024,    # 10MB for simple operations
            'medium_operation': 25 * 1024 * 1024,   # 25MB for moderate operations  
            'heavy_operation': 50 * 1024 * 1024,    # 50MB for complex operations
            'bulk_operation': 100 * 1024 * 1024     # 100MB for bulk operations
        }
        
        self.time_limits = {
            'fast_operation': 0.1,      # 100ms for simple operations
            'medium_operation': 0.5,     # 500ms for moderate operations
            'slow_operation': 1.0,       # 1 second for complex operations
            'bulk_operation': 5.0        # 5 seconds for bulk operations
        }
        
        # Test data for various scenarios
        self.test_data = {
            'simple_request': {'input': 'test'},
            'complex_request': {
                'input': 'complex search query with multiple terms and filters',
                'languageCode': 'en',
                'regionCode': 'US',
                'includeQueryPredictions': True,
                'includePureServiceAreaBusinesses': True,
                'origin': {'latitude': 37.7749, 'longitude': -122.4194},
                'locationRestriction': {
                    'circle': {
                        'center': {'latitude': 37.7749, 'longitude': -122.4194},
                        'radius': 5000
                    }
                }
            },
            'nearby_request': {
                'locationRestriction': {
                    'circle': {
                        'center': {'latitude': 37.7749, 'longitude': -122.4194},
                        'radius': 1000
                    }
                },
                'maxResultCount': 20,
                'includedTypes': ['restaurant', 'cafe', 'food']
            },
            'text_search_request': {
                'textQuery': 'restaurants near downtown',
                'pageSize': 20,
                'languageCode': 'en',
                'regionCode': 'US'
            },
            'photo_request': 'places/test_place/photos/test_photo/media'
        }
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """
        Measure memory usage of a function execution.
        
        Returns:
            tuple: (result, memory_used_bytes)
        """
        # Get memory before execution
        memory_before = self.process.memory_info().rss
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Get memory after execution
        memory_after = self.process.memory_info().rss
        memory_used = memory_after - memory_before
        
        return result, memory_used
    
    def measure_execution_time(self, func, *args, **kwargs):
        """
        Measure execution time of a function.
        
        Returns:
            tuple: (result, execution_time_seconds)
        """
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        return result, execution_time
    
    def test_places_autocomplete_memory_usage(self):
        """Test memory usage of Places autocomplete function."""
        from google_maps.Places import autocomplete
        
        # Test simple request
        result, memory_used = self.measure_memory_usage(
            autocomplete, self.test_data['simple_request']
        )
        
        self.assertIsInstance(result, dict)
        self.assertLessEqual(
            memory_used, 
            self.memory_limits['light_operation'],
            f"Simple autocomplete used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['light_operation'] / 1024 / 1024:.2f}MB"
        )
        
        # Test complex request
        result, memory_used = self.measure_memory_usage(
            autocomplete, self.test_data['complex_request']
        )
        
        self.assertIsInstance(result, dict)
        self.assertLessEqual(
            memory_used,
            self.memory_limits['medium_operation'],
            f"Complex autocomplete used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['medium_operation'] / 1024 / 1024:.2f}MB"
        )
    
    def test_places_autocomplete_execution_time(self):
        """Test execution time of Places autocomplete function."""
        from google_maps.Places import autocomplete
        
        # Test simple request
        result, execution_time = self.measure_execution_time(
            autocomplete, self.test_data['simple_request']
        )
        
        self.assertIsInstance(result, dict)
        self.assertLessEqual(
            execution_time,
            self.time_limits['fast_operation'],
            f"Simple autocomplete took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['fast_operation']:.3f}s"
        )
        
        # Test complex request
        result, execution_time = self.measure_execution_time(
            autocomplete, self.test_data['complex_request']
        )
        
        self.assertIsInstance(result, dict)
        self.assertLessEqual(
            execution_time,
            self.time_limits['medium_operation'],
            f"Complex autocomplete took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['medium_operation']:.3f}s"
        )
    
    def test_places_search_nearby_memory_usage(self):
        """Test memory usage of Places searchNearby function."""
        from google_maps.Places import searchNearby
        
        result, memory_used = self.measure_memory_usage(
            searchNearby, self.test_data['nearby_request']
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('places', result)
        self.assertLessEqual(
            memory_used,
            self.memory_limits['medium_operation'],
            f"searchNearby used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['medium_operation'] / 1024 / 1024:.2f}MB"
        )
    
    def test_places_search_nearby_execution_time(self):
        """Test execution time of Places searchNearby function."""
        from google_maps.Places import searchNearby
        
        result, execution_time = self.measure_execution_time(
            searchNearby, self.test_data['nearby_request']
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('places', result)
        self.assertLessEqual(
            execution_time,
            self.time_limits['medium_operation'],
            f"searchNearby took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['medium_operation']:.3f}s"
        )
    
    def test_places_search_text_memory_usage(self):
        """Test memory usage of Places searchText function."""
        from google_maps.Places import searchText
        
        result, memory_used = self.measure_memory_usage(
            searchText, self.test_data['text_search_request']
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('places', result)
        self.assertLessEqual(
            memory_used,
            self.memory_limits['medium_operation'],
            f"searchText used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['medium_operation'] / 1024 / 1024:.2f}MB"
        )
    
    def test_places_search_text_execution_time(self):
        """Test execution time of Places searchText function."""
        from google_maps.Places import searchText
        
        result, execution_time = self.measure_execution_time(
            searchText, self.test_data['text_search_request']
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('places', result)
        self.assertLessEqual(
            execution_time,
            self.time_limits['medium_operation'],
            f"searchText took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['medium_operation']:.3f}s"
        )
    
    def test_places_get_memory_usage(self):
        """Test memory usage of Places get function."""
        from google_maps.Places import get
        
        result, memory_used = self.measure_memory_usage(
            get, 'places/test_place_id'
        )
        
        # Result may be None if place doesn't exist, which is expected
        self.assertLessEqual(
            memory_used,
            self.memory_limits['light_operation'],
            f"Places.get used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['light_operation'] / 1024 / 1024:.2f}MB"
        )
    
    def test_places_get_execution_time(self):
        """Test execution time of Places get function."""
        from google_maps.Places import get
        
        result, execution_time = self.measure_execution_time(
            get, 'places/test_place_id'
        )
        
        # Result may be None if place doesn't exist, which is expected
        self.assertLessEqual(
            execution_time,
            self.time_limits['fast_operation'],
            f"Places.get took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['fast_operation']:.3f}s"
        )
    
    def test_photos_get_media_memory_usage(self):
        """Test memory usage of Photos getMedia function."""
        from google_maps.Places.Photos import getMedia
        
        result, memory_used = self.measure_memory_usage(
            getMedia, self.test_data['photo_request'], maxWidthPx=800
        )
        
        self.assertIsInstance(result, list)
        self.assertLessEqual(
            memory_used,
            self.memory_limits['light_operation'],
            f"getMedia used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['light_operation'] / 1024 / 1024:.2f}MB"
        )
    
    def test_photos_get_media_execution_time(self):
        """Test execution time of Photos getMedia function."""
        from google_maps.Places.Photos import getMedia
        
        result, execution_time = self.measure_execution_time(
            getMedia, self.test_data['photo_request'], maxWidthPx=800
        )
        
        self.assertIsInstance(result, list)
        self.assertLessEqual(
            execution_time,
            self.time_limits['fast_operation'],
            f"getMedia took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['fast_operation']:.3f}s"
        )


class TestGoogleMapsUtilityPerformance(BaseTestCaseWithErrorHandler):
    """Performance test case for Google Maps utility functions."""
    
    def setUp(self):
        """Set up test fixtures and performance monitoring."""
        self.process = psutil.Process(os.getpid())
        
        # Performance thresholds for utility functions
        self.memory_limits = {
            'math_operation': 1 * 1024 * 1024,     # 1MB for math operations
            'db_operation': 10 * 1024 * 1024,      # 10MB for database operations
            'bulk_db_operation': 50 * 1024 * 1024  # 50MB for bulk database operations
        }
        
        self.time_limits = {
            'math_operation': 0.001,     # 1ms for math operations
            'db_operation': 0.1,         # 100ms for database operations
            'bulk_db_operation': 1.0     # 1 second for bulk operations
        }
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function execution."""
        memory_before = self.process.memory_info().rss
        result = func(*args, **kwargs)
        memory_after = self.process.memory_info().rss
        memory_used = memory_after - memory_before
        return result, memory_used
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
    
    def test_haversine_distance_memory_usage(self):
        """Test memory usage of haversine distance calculation."""
        from google_maps.SimulationEngine.utils import _haversine_distance
        
        result, memory_used = self.measure_memory_usage(
            _haversine_distance, 37.7749, -122.4194, 37.7849, -122.4094
        )
        
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
        self.assertLessEqual(
            memory_used,
            self.memory_limits['math_operation'],
            f"_haversine_distance used {memory_used / 1024:.2f}KB, "
            f"exceeds limit of {self.memory_limits['math_operation'] / 1024:.2f}KB"
        )
    
    def test_haversine_distance_execution_time(self):
        """Test execution time of haversine distance calculation."""
        from google_maps.SimulationEngine.utils import _haversine_distance
        
        result, execution_time = self.measure_execution_time(
            _haversine_distance, 37.7749, -122.4194, 37.7849, -122.4094
        )
        
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)
        self.assertLessEqual(
            execution_time,
            self.time_limits['math_operation'],
            f"_haversine_distance took {execution_time * 1000:.3f}ms, "
            f"exceeds limit of {self.time_limits['math_operation'] * 1000:.3f}ms"
        )
    
    def test_create_place_memory_usage(self):
        """Test memory usage of place creation."""
        from google_maps.SimulationEngine.utils import _create_place
        from google_maps.SimulationEngine.db import DB
        
        place_data = {
            'id': f'perf_test_{uuid.uuid4().hex[:8]}',
            'name': 'Performance Test Place',
            'rating': 4.5,
            'location': {'latitude': 37.7749, 'longitude': -122.4194}
        }
        
        result, memory_used = self.measure_memory_usage(
            _create_place, place_data
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], place_data['id'])
        self.assertIn(place_data['id'], DB)
        self.assertLessEqual(
            memory_used,
            self.memory_limits['db_operation'],
            f"_create_place used {memory_used / 1024:.2f}KB, "
            f"exceeds limit of {self.memory_limits['db_operation'] / 1024:.2f}KB"
        )
    
    def test_create_place_execution_time(self):
        """Test execution time of place creation."""
        from google_maps.SimulationEngine.utils import _create_place
        from google_maps.SimulationEngine.db import DB
        
        place_data = {
            'id': f'perf_test_{uuid.uuid4().hex[:8]}',
            'name': 'Performance Test Place',
            'rating': 4.5,
            'location': {'latitude': 37.7749, 'longitude': -122.4194}
        }
        
        result, execution_time = self.measure_execution_time(
            _create_place, place_data
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], place_data['id'])
        self.assertIn(place_data['id'], DB)
        self.assertLessEqual(
            execution_time,
            self.time_limits['db_operation'],
            f"_create_place took {execution_time * 1000:.3f}ms, "
            f"exceeds limit of {self.time_limits['db_operation'] * 1000:.3f}ms"
        )


class TestGoogleMapsDbPerformance(BaseTestCaseWithErrorHandler):
    """Performance test case for Google Maps database operations."""
    
    def setUp(self):
        """Set up test fixtures and performance monitoring."""
        self.process = psutil.Process(os.getpid())
        
        # Performance thresholds for database operations
        self.memory_limits = {
            'state_operation': 20 * 1024 * 1024,   # 20MB for save/load operations
            'query_operation': 10 * 1024 * 1024    # 10MB for query operations
        }
        
        self.time_limits = {
            'state_operation': 0.5,     # 500ms for save/load operations
            'query_operation': 0.1      # 100ms for query operations
        }
        
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.temp_filepath = self.temp_file.name
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_filepath):
            os.unlink(self.temp_filepath)
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function execution."""
        memory_before = self.process.memory_info().rss
        result = func(*args, **kwargs)
        memory_after = self.process.memory_info().rss
        memory_used = memory_after - memory_before
        return result, memory_used
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
    
    def test_save_state_memory_usage(self):
        """Test memory usage of database state saving."""
        from google_maps.SimulationEngine.db import save_state
        
        result, memory_used = self.measure_memory_usage(
            save_state, self.temp_filepath
        )
        
        self.assertIsNone(result)  # save_state returns None
        self.assertTrue(os.path.exists(self.temp_filepath))
        self.assertLessEqual(
            memory_used,
            self.memory_limits['state_operation'],
            f"save_state used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['state_operation'] / 1024 / 1024:.2f}MB"
        )
    
    def test_save_state_execution_time(self):
        """Test execution time of database state saving."""
        from google_maps.SimulationEngine.db import save_state
        
        result, execution_time = self.measure_execution_time(
            save_state, self.temp_filepath
        )
        
        self.assertIsNone(result)  # save_state returns None
        self.assertTrue(os.path.exists(self.temp_filepath))
        self.assertLessEqual(
            execution_time,
            self.time_limits['state_operation'],
            f"save_state took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['state_operation']:.3f}s"
        )
    
    def test_load_state_memory_usage(self):
        """Test memory usage of database state loading."""
        from google_maps.SimulationEngine.db import save_state, load_state
        
        # First save a state to load
        save_state(self.temp_filepath)
        
        result, memory_used = self.measure_memory_usage(
            load_state, self.temp_filepath
        )
        
        self.assertIsNone(result)  # load_state returns None
        self.assertLessEqual(
            memory_used,
            self.memory_limits['state_operation'],
            f"load_state used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['state_operation'] / 1024 / 1024:.2f}MB"
        )
    
    def test_load_state_execution_time(self):
        """Test execution time of database state loading."""
        from google_maps.SimulationEngine.db import save_state, load_state
        
        # First save a state to load
        save_state(self.temp_filepath)
        
        result, execution_time = self.measure_execution_time(
            load_state, self.temp_filepath
        )
        
        self.assertIsNone(result)  # load_state returns None
        self.assertLessEqual(
            execution_time,
            self.time_limits['state_operation'],
            f"load_state took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['state_operation']:.3f}s"
        )
    
    def test_get_minified_state_memory_usage(self):
        """Test memory usage of getting minified state."""
        from google_maps.SimulationEngine.db import get_minified_state
        
        result, memory_used = self.measure_memory_usage(
            get_minified_state
        )
        
        self.assertIsInstance(result, dict)
        self.assertLessEqual(
            memory_used,
            self.memory_limits['query_operation'],
            f"get_minified_state used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['query_operation'] / 1024 / 1024:.2f}MB"
        )
    
    def test_get_minified_state_execution_time(self):
        """Test execution time of getting minified state."""
        from google_maps.SimulationEngine.db import get_minified_state
        
        result, execution_time = self.measure_execution_time(
            get_minified_state
        )
        
        self.assertIsInstance(result, dict)
        self.assertLessEqual(
            execution_time,
            self.time_limits['query_operation'],
            f"get_minified_state took {execution_time * 1000:.3f}ms, "
            f"exceeds limit of {self.time_limits['query_operation'] * 1000:.3f}ms"
        )


class TestGoogleMapsBulkPerformance(BaseTestCaseWithErrorHandler):
    """Performance test case for Google Maps bulk operations."""
    
    def setUp(self):
        """Set up test fixtures and performance monitoring."""
        self.process = psutil.Process(os.getpid())
        
        # Performance thresholds for bulk operations
        self.memory_limits = {
            'bulk_search': 100 * 1024 * 1024,    # 100MB for bulk searches
            'bulk_create': 50 * 1024 * 1024      # 50MB for bulk creation
        }
        
        self.time_limits = {
            'bulk_search': 2.0,     # 2 seconds for bulk searches  
            'bulk_create': 1.0      # 1 second for bulk creation
        }
        
        # Generate test data for bulk operations
        self.bulk_places = []
        for i in range(10):  # Create 10 test places
            self.bulk_places.append({
                'id': f'bulk_test_{uuid.uuid4().hex[:8]}',
                'name': f'Bulk Test Place {i}',
                'rating': 4.0 + (i % 5) * 0.2,
                'formattedAddress': f'{i}00 Test St, Test City, TC 1234{i}',
                'location': {
                    'latitude': 37.7749 + (i * 0.001),
                    'longitude': -122.4194 + (i * 0.001)
                },
                'primaryType': 'restaurant',
                'types': ['restaurant', 'food', 'establishment']
            })
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function execution."""
        memory_before = self.process.memory_info().rss
        result = func(*args, **kwargs)
        memory_after = self.process.memory_info().rss
        memory_used = memory_after - memory_before
        return result, memory_used
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
    
    def test_bulk_place_creation_memory_usage(self):
        """Test memory usage of creating multiple places."""
        from google_maps.SimulationEngine.utils import _create_place
        from google_maps.SimulationEngine.db import DB
        
        def create_bulk_places():
            results = []
            for place_data in self.bulk_places:
                if place_data['id'] not in DB:
                    results.append(_create_place(place_data))
            return results
        
        results, memory_used = self.measure_memory_usage(create_bulk_places)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertLessEqual(
            memory_used,
            self.memory_limits['bulk_create'],
            f"Bulk place creation used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['bulk_create'] / 1024 / 1024:.2f}MB"
        )
    
    def test_bulk_place_creation_execution_time(self):
        """Test execution time of creating multiple places."""
        from google_maps.SimulationEngine.utils import _create_place
        from google_maps.SimulationEngine.db import DB
        
        def create_bulk_places():
            results = []
            for place_data in self.bulk_places:
                if place_data['id'] not in DB:
                    results.append(_create_place(place_data))
            return results
        
        results, execution_time = self.measure_execution_time(create_bulk_places)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertLessEqual(
            execution_time,
            self.time_limits['bulk_create'],
            f"Bulk place creation took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['bulk_create']:.3f}s"
        )
    
    def test_bulk_search_operations_memory_usage(self):
        """Test memory usage of multiple search operations."""
        from google_maps.Places import searchText, searchNearby
        
        def perform_bulk_searches():
            results = []
            
            # Perform multiple text searches
            for i in range(5):
                request = {'textQuery': f'test query {i}'}
                results.append(searchText(request))
            
            # Perform multiple nearby searches  
            for i in range(5):
                request = {
                    'locationRestriction': {
                        'circle': {
                            'center': {
                                'latitude': 37.7749 + (i * 0.01),
                                'longitude': -122.4194 + (i * 0.01)
                            },
                            'radius': 1000
                        }
                    }
                }
                results.append(searchNearby(request))
            
            return results
        
        results, memory_used = self.measure_memory_usage(perform_bulk_searches)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 10)  # 5 text + 5 nearby searches
        self.assertLessEqual(
            memory_used,
            self.memory_limits['bulk_search'],
            f"Bulk search operations used {memory_used / 1024 / 1024:.2f}MB, "
            f"exceeds limit of {self.memory_limits['bulk_search'] / 1024 / 1024:.2f}MB"
        )
    
    def test_bulk_search_operations_execution_time(self):
        """Test execution time of multiple search operations."""
        from google_maps.Places import searchText, searchNearby
        
        def perform_bulk_searches():
            results = []
            
            # Perform multiple text searches
            for i in range(5):
                request = {'textQuery': f'test query {i}'}
                results.append(searchText(request))
            
            # Perform multiple nearby searches  
            for i in range(5):
                request = {
                    'locationRestriction': {
                        'circle': {
                            'center': {
                                'latitude': 37.7749 + (i * 0.01),
                                'longitude': -122.4194 + (i * 0.01)
                            },
                            'radius': 1000
                        }
                    }
                }
                results.append(searchNearby(request))
            
            return results
        
        results, execution_time = self.measure_execution_time(perform_bulk_searches)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 10)  # 5 text + 5 nearby searches
        self.assertLessEqual(
            execution_time,
            self.time_limits['bulk_search'],
            f"Bulk search operations took {execution_time:.3f}s, "
            f"exceeds limit of {self.time_limits['bulk_search']:.3f}s"
        )


class TestGoogleMapsPerformanceErrorHandling(BaseTestCaseWithErrorHandler):
    """Performance test case for error handling scenarios."""
    
    def setUp(self):
        """Set up test fixtures and performance monitoring."""
        self.process = psutil.Process(os.getpid())
        
        # Performance thresholds for error scenarios
        self.memory_limits = {
            'error_operation': 5 * 1024 * 1024  # 5MB for error handling
        }
        
        self.time_limits = {
            'error_operation': 0.1  # 100ms for error handling
        }
    
    def measure_memory_usage_with_error(self, func, expected_exception, expected_message, *args, **kwargs):
        """Measure memory usage when function is expected to raise an error."""
        memory_before = self.process.memory_info().rss
        
        # Use assert_error_behavior to handle expected exceptions
        self.assert_error_behavior(func, expected_exception, expected_message, None, *args, **kwargs)
        
        memory_after = self.process.memory_info().rss
        memory_used = memory_after - memory_before
        
        return memory_used
    
    def measure_execution_time_with_error(self, func, expected_exception, expected_message, *args, **kwargs):
        """Measure execution time when function is expected to raise an error."""
        start_time = time.perf_counter()
        
        # Use assert_error_behavior to handle expected exceptions
        self.assert_error_behavior(func, expected_exception, expected_message, None, *args, **kwargs)
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        return execution_time
    
    def test_invalid_place_format_error_performance(self):
        """Test performance of error handling for invalid place format."""
        from google_maps.Places import get
        
        expected_message = "name must start with 'places/'"
        
        # Test memory usage during error
        memory_used = self.measure_memory_usage_with_error(
            get, ValueError, expected_message, 'invalid_format'
        )
        
        self.assertLessEqual(
            memory_used,
            self.memory_limits['error_operation'],
            f"Error handling used {memory_used / 1024:.2f}KB, "
            f"exceeds limit of {self.memory_limits['error_operation'] / 1024:.2f}KB"
        )
        
        # Test execution time during error
        execution_time = self.measure_execution_time_with_error(
            get, ValueError, expected_message, 'invalid_format'
        )
        
        self.assertLessEqual(
            execution_time,
            self.time_limits['error_operation'],
            f"Error handling took {execution_time * 1000:.3f}ms, "
            f"exceeds limit of {self.time_limits['error_operation'] * 1000:.3f}ms"
        )
    
    def test_missing_photo_dimensions_error_performance(self):
        """Test performance of error handling for missing photo dimensions."""
        from google_maps.Places.Photos import getMedia
        
        expected_message = "Invalid request data: Value error, At least one of maxWidthPx or maxHeightPx must be specified."
        
        # Test memory usage during error
        memory_used = self.measure_memory_usage_with_error(
            getMedia, ValueError, expected_message, 'places/test/photos/test/media'
        )
        
        self.assertLessEqual(
            memory_used,
            self.memory_limits['error_operation'],
            f"Error handling used {memory_used / 1024:.2f}KB, "
            f"exceeds limit of {self.memory_limits['error_operation'] / 1024:.2f}KB"
        )
        
        # Test execution time during error
        execution_time = self.measure_execution_time_with_error(
            getMedia, ValueError, expected_message, 'places/test/photos/test/media'
        )
        
        self.assertLessEqual(
            execution_time,
            self.time_limits['error_operation'],
            f"Error handling took {execution_time * 1000:.3f}ms, "
            f"exceeds limit of {self.time_limits['error_operation'] * 1000:.3f}ms"
        )
    
    def test_missing_text_query_error_performance(self):
        """Test performance of error handling for missing text query."""
        from google_maps.Places import searchText
        
        expected_message = "Field required"
        
        # Test memory usage during error
        memory_used = self.measure_memory_usage_with_error(
            searchText, ValidationError, expected_message, {}
        )
        
        self.assertLessEqual(
            memory_used,
            self.memory_limits['error_operation'],
            f"Error handling used {memory_used / 1024:.2f}KB, "
            f"exceeds limit of {self.memory_limits['error_operation'] / 1024:.2f}KB"
        )
        
        # Test execution time during error
        execution_time = self.measure_execution_time_with_error(
            searchText, ValidationError, expected_message, {}
        )
        
        self.assertLessEqual(
            execution_time,
            self.time_limits['error_operation'],
            f"Error handling took {execution_time * 1000:.3f}ms, "
            f"exceeds limit of {self.time_limits['error_operation'] * 1000:.3f}ms"
        )


if __name__ == '__main__':
    # Run all performance test suites
    unittest.main(verbosity=2)
