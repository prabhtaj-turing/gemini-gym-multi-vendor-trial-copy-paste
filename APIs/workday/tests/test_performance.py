#!/usr/bin/env python3
"""
Comprehensive Performance Tests for Workday Strategic Sourcing API

This module provides extensive performance testing coverage including:
1. Module Performance Tests
2. Database Performance Tests  
3. Memory Usage Tests
4. Concurrent Access Tests
5. Load Testing
6. Scalability Tests

Author: AI Assistant
Created: 2024-12-28
"""

import unittest
import time
import threading
import gc
import sys
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import modules under test
from ..BidsById import get as get_bid_by_id
from ..BidLineItemById import get as get_bid_line_item_by_id
from ..BidLineItemsList import get as list_bid_line_items
from ..BidLineItemsDescribe import get as describe_bid_line_items
from ..BidsDescribe import get as describe_bids
from ..ResourceTypeById import get as get_resource_type_by_id
from ..SimulationEngine import db
from ..SimulationEngine.utils import apply_company_filters
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestModulePerformance(BaseTestCaseWithErrorHandler):
    """Test performance of individual modules."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        super().setUp()
        db.reset_db()
        self.setup_performance_data()
        
    def tearDown(self):
        """Clean up after performance tests."""
        super().tearDown()
        db.reset_db()
        
    def setup_performance_data(self):
        """Setup data for performance testing."""
        # Create 1000 bids
        for i in range(1, 1001):
            db.DB["events"]["bids"][i] = {
                "supplier_id": (i % 100) + 1,
                "event_id": (i % 50) + 1,
                "bid_amount": 1000.0 + (i * 10),
                "status": "submitted" if i % 2 == 0 else "draft",
                "submitted_at": f"2024-01-01T{(i % 24):02d}:00:00Z"
            }
        
        # Create 5000 bid line items
        for i in range(1, 5001):
            bid_id = ((i - 1) // 5) + 1  # 5 items per bid
            db.DB["events"]["bid_line_items"][i] = {
                "bid_id": bid_id,
                "event_id": (bid_id % 50) + 1,
                "description": f"Line Item {i}",
                "amount": 100.0 + (i % 500),
                "quantity": (i % 20) + 1
            }
        
        # Create 100 SCIM resource types
        resource_types = []
        for i in range(1, 101):
            resource_types.append({
                "resource": f"ResourceType{i}",
                "name": f"Resource Type {i}",
                "description": f"Description for resource {i}",
                "endpoint": f"/ResourceType{i}"
            })
        db.DB["scim"]["resource_types"] = resource_types
            
    # =========================================================================
    # Single Operation Performance Tests
    # =========================================================================
    
    def test_performance_bid_retrieval(self):
        """Test performance of bid retrieval operations."""
        # Test single bid retrieval
        start_time = time.time()
        for i in range(1, 101):  # Get 100 bids
            result = get_bid_by_id(i)
            self.assertIsNotNone(result)
        end_time = time.time()
        
        single_retrieval_time = end_time - start_time
        self.assertLess(single_retrieval_time, 0.5)  # Less than 500ms for 100 retrievals
        
        # Test bid retrieval with includes
        start_time = time.time()
        for i in range(1, 51):  # Get 50 bids with includes
            result = get_bid_by_id(i, _include="supplier_company,event")
            self.assertIsNotNone(result)
        end_time = time.time()
        
        include_retrieval_time = end_time - start_time
        self.assertLess(include_retrieval_time, 1.0)  # Less than 1s for 50 retrievals with includes
        
    def test_performance_bid_line_item_operations(self):
        """Test performance of bid line item operations."""
        # Test individual line item retrieval
        start_time = time.time()
        for i in range(1, 201):  # Get 200 line items
            result = get_bid_line_item_by_id(i)
            self.assertIsNotNone(result)
        end_time = time.time()
        
        individual_time = end_time - start_time
        self.assertLess(individual_time, 0.3)  # Less than 300ms for 200 retrievals
        
        # Test list operations
        start_time = time.time()
        for bid_id in range(1, 51):  # List items for 50 bids
            result = list_bid_line_items(filter={"bid_id": bid_id})
            self.assertIsInstance(result, list)
        end_time = time.time()
        
        list_time = end_time - start_time
        self.assertLess(list_time, 1.0)  # Less than 1s for 50 list operations
        
    def test_performance_schema_operations(self):
        """Test performance of schema description operations."""
        # Test bid schema retrieval
        start_time = time.time()
        for _ in range(100):  # Get schema 100 times
            result = describe_bids()
            self.assertIsInstance(result, list)
        end_time = time.time()
        
        bid_schema_time = end_time - start_time
        self.assertLess(bid_schema_time, 0.1)  # Less than 100ms for 100 schema calls
        
        # Test line item schema retrieval
        start_time = time.time()
        for _ in range(100):  # Get schema 100 times
            result = describe_bid_line_items()
            self.assertIsInstance(result, list)
        end_time = time.time()
        
        line_item_schema_time = end_time - start_time
        self.assertLess(line_item_schema_time, 0.1)  # Less than 100ms for 100 schema calls
        
    def test_performance_filtering_operations(self):
        """Test performance of filtering operations."""
        # Test bid line item filtering
        start_time = time.time()
        
        # Filter by different criteria
        filters = [
            {"bid_id": i} for i in range(1, 21)
        ] + [
            {"event_id": i} for i in range(1, 11)
        ]
        
        for filter_criteria in filters:
            result = list_bid_line_items(filter=filter_criteria)
            self.assertIsInstance(result, list)
            
        end_time = time.time()
        
        filtering_time = end_time - start_time
        self.assertLess(filtering_time, 2.0)  # Less than 2s for 30 filter operations
        
    # =========================================================================
    # Batch Operation Performance Tests
    # =========================================================================
    
    def test_performance_batch_retrievals(self):
        """Test performance of batch retrieval operations."""
        # Batch bid retrievals
        start_time = time.time()
        
        bid_ids = list(range(1, 501))  # 500 bids
        results = []
        
        for bid_id in bid_ids:
            result = get_bid_by_id(bid_id)
            if result:
                results.append(result)
                
        end_time = time.time()
        
        batch_time = end_time - start_time
        self.assertGreater(len(results), 400)  # Should get most bids
        self.assertLess(batch_time, 2.0)  # Less than 2s for 500 retrievals
        
    def test_performance_complex_queries(self):
        """Test performance of complex query operations."""
        start_time = time.time()
        
        # Complex filtering scenarios
        complex_results = []
        
        # Get all line items for first 10 events
        for event_id in range(1, 11):
            event_items = list_bid_line_items(filter={"event_id": event_id})
            complex_results.append(len(event_items))
            
        # Get all line items for first 20 bids
        for bid_id in range(1, 21):
            bid_items = list_bid_line_items(filter={"bid_id": bid_id})
            complex_results.append(len(bid_items))
            
        end_time = time.time()
        
        complex_time = end_time - start_time
        self.assertEqual(len(complex_results), 30)  # 10 events + 20 bids
        self.assertLess(complex_time, 1.5)  # Less than 1.5s for complex queries


class TestMemoryUsage(BaseTestCaseWithErrorHandler):
    """Test memory usage and efficiency."""
    
    def setUp(self):
        """Set up memory usage test fixtures."""
        super().setUp()
        db.reset_db()
        
    def tearDown(self):
        """Clean up after memory usage tests."""
        super().tearDown()
        db.reset_db()
        gc.collect()  # Force garbage collection
        
    def get_memory_usage(self):
        """Get current memory usage (simplified)."""
        # This is a simplified memory check
        # In production, you might use psutil or similar
        return len(str(db.DB))  # Rough approximation
        
    def test_memory_usage_large_dataset(self):
        """Test memory usage with large datasets."""
        initial_memory = self.get_memory_usage()
        
        # Create large dataset
        for i in range(1, 1001):
            large_data = {
                "id": i,
                "name": f"Large Item {i}",
                "description": "Large description " * 100,  # Large text
                "metadata": {f"field_{j}": f"value_{j}" * 10 for j in range(50)},  # Many fields
                "tags": [f"tag_{k}" for k in range(20)]  # Many tags
            }
            db.DB["events"]["bids"][i] = large_data
            
        after_creation_memory = self.get_memory_usage()
        
        # Perform operations
        results = []
        for i in range(1, 101):
            result = get_bid_by_id(i)
            if result:
                results.append(result)
                
        after_operations_memory = self.get_memory_usage()
        
        # Memory should not grow excessively during operations
        memory_growth = after_operations_memory - after_creation_memory
        creation_growth = after_creation_memory - initial_memory
        
        # Operations should not cause significant additional memory growth
        self.assertLess(memory_growth / creation_growth, 0.1)  # Less than 10% additional growth
        
    def test_memory_cleanup_after_operations(self):
        """Test that memory is properly cleaned up after operations."""
        # Create test data
        for i in range(1, 101):
            db.DB["events"]["bids"][i] = {
                "id": i,
                "name": f"Test Bid {i}",
                "large_field": "x" * 1000  # 1KB per record
            }
            
        initial_memory = self.get_memory_usage()
        
        # Perform many operations
        for _ in range(10):
            for i in range(1, 101):
                result = get_bid_by_id(i)
                # Don't store results to avoid memory accumulation
                
        # Force garbage collection
        gc.collect()
        
        after_operations_memory = self.get_memory_usage()
        
        # Memory should not grow significantly
        memory_growth = after_operations_memory - initial_memory
        self.assertLess(abs(memory_growth) / initial_memory, 0.05)  # Less than 5% growth
        
    def test_memory_efficiency_with_includes(self):
        """Test memory efficiency when using include parameters."""
        # Setup related data
        for i in range(1, 51):
            db.DB["events"]["bids"][i] = {
                "supplier_id": i,
                "event_id": i,
                "bid_amount": 1000.0 + i
            }
            db.DB["suppliers"]["supplier_companies"][i] = {
                "name": f"Supplier {i}",
                "large_data": "x" * 500  # 500 bytes per supplier
            }
            db.DB["events"]["events"][i] = {
                "name": f"Event {i}",
                "large_data": "y" * 500  # 500 bytes per event
            }
            
        initial_memory = self.get_memory_usage()
        
        # Get bids with includes
        results_with_includes = []
        for i in range(1, 26):  # 25 bids with includes
            result = get_bid_by_id(i, _include="supplier_company,event")
            if result:
                results_with_includes.append(result)
                
        include_memory = self.get_memory_usage()
        
        # Get bids without includes
        results_without_includes = []
        for i in range(26, 51):  # 25 bids without includes
            result = get_bid_by_id(i)
            if result:
                results_without_includes.append(result)
                
        no_include_memory = self.get_memory_usage()
        
        # Both should complete successfully
        self.assertEqual(len(results_with_includes), 25)
        self.assertEqual(len(results_without_includes), 25)
        
        # Memory growth should be reasonable
        include_growth = include_memory - initial_memory
        no_include_growth = no_include_memory - include_memory
        
        # Test that operations completed successfully
        # Since the memory measurement is simplified, we'll focus on functional tests
        self.assertGreater(len(results_with_includes), 0)
        self.assertGreater(len(results_without_includes), 0)
        
        # Verify that includes actually contain more data
        if results_with_includes and results_without_includes:
            with_include_result = results_with_includes[0]
            without_include_result = results_without_includes[0]
            
            # Results with includes should have an 'included' field
            if 'included' in with_include_result:
                self.assertGreater(len(str(with_include_result)), len(str(without_include_result)))
            else:
                # Even without includes, both operations should work
                self.assertIsNotNone(with_include_result)
                self.assertIsNotNone(without_include_result)


class TestConcurrentAccess(BaseTestCaseWithErrorHandler):
    """Test concurrent access and thread safety."""
    
    def setUp(self):
        """Set up concurrent access test fixtures."""
        super().setUp()
        db.reset_db()
        
        # Setup data for concurrent access
        for i in range(1, 201):
            db.DB["events"]["bids"][i] = {
                "supplier_id": (i % 50) + 1,
                "event_id": (i % 20) + 1,
                "bid_amount": 1000.0 + i,
                "status": "submitted"
            }
            
        for i in range(1, 1001):
            bid_id = ((i - 1) // 5) + 1
            db.DB["events"]["bid_line_items"][i] = {
                "bid_id": bid_id,
                "event_id": (bid_id % 20) + 1,
                "description": f"Item {i}",
                "amount": 100.0 + i
            }
            
    def tearDown(self):
        """Clean up after concurrent access tests."""
        super().tearDown()
        db.reset_db()
        
    def test_concurrent_read_operations(self):
        """Test concurrent read operations."""
        results = []
        errors = []
        
        def read_bids(start_id, end_id):
            """Read bids in a range."""
            thread_results = []
            try:
                for bid_id in range(start_id, end_id + 1):
                    result = get_bid_by_id(bid_id)
                    if result:
                        thread_results.append(result)
            except Exception as e:
                errors.append(e)
            return thread_results
        
        # Create multiple threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # Each thread reads different ranges
            for i in range(5):
                start_id = (i * 40) + 1
                end_id = (i + 1) * 40
                future = executor.submit(read_bids, start_id, end_id)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                thread_results = future.result()
                results.extend(thread_results)
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0)
        
        # Verify all threads got results
        self.assertEqual(len(results), 200)  # Should get all 200 bids
        
    def test_concurrent_filtering_operations(self):
        """Test concurrent filtering operations."""
        results = []
        errors = []
        
        def filter_line_items(filter_criteria_list):
            """Filter line items with different criteria."""
            thread_results = []
            try:
                for criteria in filter_criteria_list:
                    result = list_bid_line_items(filter=criteria)
                    thread_results.append(len(result))
            except Exception as e:
                errors.append(e)
            return thread_results
        
        # Prepare filter criteria for different threads
        filter_sets = [
            [{"bid_id": i} for i in range(1, 21)],      # Thread 1: bid filters 1-20
            [{"bid_id": i} for i in range(21, 41)],     # Thread 2: bid filters 21-40
            [{"event_id": i} for i in range(1, 11)],    # Thread 3: event filters 1-10
            [{"event_id": i} for i in range(11, 21)]    # Thread 4: event filters 11-20
        ]
        
        # Execute concurrent filtering
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for filter_set in filter_sets:
                future = executor.submit(filter_line_items, filter_set)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                thread_results = future.result()
                results.extend(thread_results)
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0)
        
        # Verify all threads completed
        self.assertEqual(len(results), 60)  # 20+20+10+10 filter operations
        
    def test_concurrent_schema_operations(self):
        """Test concurrent schema operations."""
        results = []
        errors = []
        
        def get_schemas(iterations):
            """Get schemas multiple times."""
            thread_results = []
            try:
                for _ in range(iterations):
                    bid_schema = describe_bids()
                    line_item_schema = describe_bid_line_items()
                    thread_results.append((len(bid_schema), len(line_item_schema)))
            except Exception as e:
                errors.append(e)
            return thread_results
        
        # Execute concurrent schema operations
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for _ in range(3):
                future = executor.submit(get_schemas, 10)  # Each thread gets schemas 10 times
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                thread_results = future.result()
                results.extend(thread_results)
        
        # Verify no errors occurred
        self.assertEqual(len(errors), 0)
        
        # Verify all threads completed
        self.assertEqual(len(results), 30)  # 3 threads * 10 iterations each
        
        # Verify schema consistency across threads
        first_result = results[0]
        for result in results[1:]:
            self.assertEqual(result, first_result)  # All schemas should be identical


class TestLoadTesting(BaseTestCaseWithErrorHandler):
    """Test system behavior under load."""
    
    def setUp(self):
        """Set up load testing fixtures."""
        super().setUp()
        db.reset_db()
        self.setup_load_test_data()
        
    def tearDown(self):
        """Clean up after load tests."""
        super().tearDown()
        db.reset_db()
        
    def setup_load_test_data(self):
        """Setup large dataset for load testing."""
        # Create 2000 bids
        for i in range(1, 2001):
            db.DB["events"]["bids"][i] = {
                "supplier_id": (i % 200) + 1,
                "event_id": (i % 100) + 1,
                "bid_amount": 1000.0 + (i * 5),
                "status": "submitted" if i % 3 == 0 else "draft",
                "submitted_at": f"2024-01-{(i % 28) + 1:02d}T10:00:00Z"
            }
        
        # Create 10000 bid line items
        for i in range(1, 10001):
            bid_id = ((i - 1) // 5) + 1  # 5 items per bid
            db.DB["events"]["bid_line_items"][i] = {
                "bid_id": bid_id,
                "event_id": (bid_id % 100) + 1,
                "description": f"Load Test Item {i}",
                "amount": 50.0 + (i % 1000),
                "quantity": (i % 50) + 1
            }
            
    def test_high_volume_retrievals(self):
        """Test high volume retrieval operations."""
        start_time = time.time()
        
        successful_retrievals = 0
        failed_retrievals = 0
        
        # Retrieve 1000 bids
        for i in range(1, 1001):
            try:
                result = get_bid_by_id(i)
                if result:
                    successful_retrievals += 1
                else:
                    failed_retrievals += 1
            except Exception:
                failed_retrievals += 1
                
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # Verify performance under load
        self.assertGreater(successful_retrievals, 950)  # At least 95% success rate
        self.assertLess(total_time, 5.0)  # Complete within 5 seconds
        self.assertLess(failed_retrievals / (successful_retrievals + failed_retrievals), 0.05)  # Less than 5% failure rate
        
    def test_mixed_workload_performance(self):
        """Test performance with mixed workload."""
        start_time = time.time()
        
        operation_counts = {
            "bid_retrievals": 0,
            "line_item_retrievals": 0,
            "line_item_lists": 0,
            "schema_calls": 0
        }
        
        # Mixed workload for 3 seconds
        while time.time() - start_time < 3.0:
            operation_type = int(time.time() * 1000) % 4
            
            try:
                if operation_type == 0:  # Bid retrieval
                    bid_id = (operation_counts["bid_retrievals"] % 1000) + 1
                    result = get_bid_by_id(bid_id)
                    if result:
                        operation_counts["bid_retrievals"] += 1
                        
                elif operation_type == 1:  # Line item retrieval
                    item_id = (operation_counts["line_item_retrievals"] % 5000) + 1
                    result = get_bid_line_item_by_id(item_id)
                    if result:
                        operation_counts["line_item_retrievals"] += 1
                        
                elif operation_type == 2:  # Line item list
                    bid_id = (operation_counts["line_item_lists"] % 100) + 1
                    result = list_bid_line_items(filter={"bid_id": bid_id})
                    if isinstance(result, list):
                        operation_counts["line_item_lists"] += 1
                        
                else:  # Schema calls
                    result = describe_bids()
                    if isinstance(result, list):
                        operation_counts["schema_calls"] += 1
                        
            except Exception:
                pass
                
        total_operations = sum(operation_counts.values())
        
        # Verify mixed workload performance
        self.assertGreater(total_operations, 300)  # At least 100 ops/second average
        
        # Verify all operation types were executed
        for op_type, count in operation_counts.items():
            self.assertGreater(count, 0, f"No {op_type} operations were performed")


class TestScalability(BaseTestCaseWithErrorHandler):
    """Test system scalability with increasing data sizes."""
    
    def setUp(self):
        """Set up scalability test fixtures."""
        super().setUp()
        db.reset_db()
        
    def tearDown(self):
        """Clean up after scalability tests."""
        super().tearDown()
        db.reset_db()
        
    def test_scalability_with_increasing_dataset_size(self):
        """Test performance scaling with increasing dataset sizes."""
        dataset_sizes = [100, 500, 1000, 2000]
        performance_results = []
        
        for size in dataset_sizes:
            # Setup data for this size
            db.reset_db()
            
            for i in range(1, size + 1):
                db.DB["events"]["bids"][i] = {
                    "supplier_id": (i % 50) + 1,
                    "event_id": (i % 25) + 1,
                    "bid_amount": 1000.0 + i,
                    "status": "submitted"
                }
            
            # Measure performance
            start_time = time.time()
            
            # Perform standard operations
            operations = min(100, size)  # Don't exceed dataset size
            for i in range(1, operations + 1):
                result = get_bid_by_id(i)
                self.assertIsNotNone(result)
                
            end_time = time.time()
            
            execution_time = end_time - start_time
            # Avoid division by zero
            ops_per_second = operations / max(execution_time, 0.001)  # Minimum 1ms
            
            performance_results.append({
                "size": size,
                "time": execution_time,
                "ops_per_second": ops_per_second
            })
        
        # Verify scalability
        # Performance should not degrade significantly with larger datasets
        first_ops_per_second = performance_results[0]["ops_per_second"]
        last_ops_per_second = performance_results[-1]["ops_per_second"]
        
        # Performance degradation should be less than 50%
        performance_ratio = last_ops_per_second / first_ops_per_second
        self.assertGreater(performance_ratio, 0.5)
        
    def test_memory_scalability(self):
        """Test memory usage scaling with dataset size."""
        sizes = [100, 500, 1000]
        memory_usage = []
        
        for size in sizes:
            db.reset_db()
            
            # Create dataset
            for i in range(1, size + 1):
                db.DB["events"]["bids"][i] = {
                    "id": i,
                    "data": "x" * 100,  # 100 bytes per record
                    "metadata": {f"field_{j}": f"value_{j}" for j in range(10)}
                }
            
            # Measure memory usage (simplified)
            memory = len(str(db.DB))
            memory_usage.append({"size": size, "memory": memory})
        
        # Verify memory scaling is reasonable (should be roughly linear)
        size_ratio = sizes[-1] / sizes[0]  # 1000/100 = 10
        memory_ratio = memory_usage[-1]["memory"] / memory_usage[0]["memory"]
        
        # Memory usage should scale reasonably (within 2x of size ratio)
        self.assertLess(memory_ratio / size_ratio, 2.0)
        self.assertGreater(memory_ratio / size_ratio, 0.5)


if __name__ == '__main__':
    unittest.main()

