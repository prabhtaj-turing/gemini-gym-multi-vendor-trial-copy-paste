import unittest
import sys
import os
import time
import statistics
import psutil
import gc
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from common_utils.base_case import BaseTestCaseWithErrorHandler
from contacts.SimulationEngine.db import DB
import contacts.contacts as contacts
from .. import create_contact, delete_contact, get_contact, list_contacts, search_contacts, update_contact

class TestPerformance(BaseTestCaseWithErrorHandler):
    """
    Test suite for performance testing of the contacts API.
    """

    def setUp(self):
        """
        Set up test data for performance tests.
        """
        # Clear the database and add some initial data
        DB.clear()
        DB.update({
            "myContacts": {
                "people/c12345": {
                    "resourceName": "people/c12345",
                    "etag": "etag123",
                    "names": [{"givenName": "John", "familyName": "Doe"}],
                    "emailAddresses": [{"value": "john.doe@example.com", "type": "work"}],
                    "phoneNumbers": [{"value": "+1234567890", "type": "mobile"}]
                }
            },
            "otherContacts": {},
            "directory": {}
        })

    def tearDown(self):
        """
        Clean up after performance tests.
        """
        DB.clear()
        gc.collect()  # Force garbage collection

    def test_list_contacts_performance(self):
        """
        Test performance of list_contacts operation.
        """
        # Create additional contacts for testing
        for i in range(50):
            create_contact(
                given_name=f"PerfContact{i}",
                family_name="Test",
                email=f"perf{i}@example.com"
            )
        
        # Measure performance with different max_results values
        test_cases = [10, 25, 50, 100]
        
        for max_results in test_cases:
            start_time = time.time()
            result = list_contacts(max_results=max_results)
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Performance assertions
            self.assertLess(execution_time, 1.0, 
                          f"list_contacts with max_results={max_results} took too long: {execution_time:.3f}s")
            self.assertIn("contacts", result)
            self.assertLessEqual(len(result["contacts"]), max_results)

    def test_create_contact_performance(self):
        """
        Test performance of create_contact operation.
        """
        # Measure performance of creating multiple contacts
        execution_times = []
        
        for i in range(20):
            start_time = time.time()
            result = create_contact(
                given_name=f"PerfCreate{i}",
                family_name="Test",
                email=f"perfcreate{i}@example.com"
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            self.assertEqual(result["status"], "success")
        
        # Performance assertions
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        self.assertLess(avg_time, 0.1, f"Average create_contact time too high: {avg_time:.3f}s")
        self.assertLess(max_time, 0.5, f"Maximum create_contact time too high: {max_time:.3f}s")

    def test_get_contact_performance(self):
        """
        Test performance of get_contact operation.
        """
        # Create a contact to retrieve
        create_result = create_contact(
            given_name="PerfGet",
            family_name="Test",
            email="perfget@example.com"
        )
        contact_id = create_result["contact"]["resourceName"]
        
        # Measure performance of multiple retrievals
        execution_times = []
        
        for _ in range(50):
            start_time = time.time()
            result = get_contact(contact_id)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            self.assertEqual(result["resourceName"], contact_id)
        
        # Performance assertions
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        self.assertLess(avg_time, 0.01, f"Average get_contact time too high: {avg_time:.3f}s")
        self.assertLess(max_time, 0.1, f"Maximum get_contact time too high: {max_time:.3f}s")

    def test_update_contact_performance(self):
        """
        Test performance of update_contact operation.
        """
        # Create a contact to update
        create_result = create_contact(
            given_name="PerfUpdate",
            family_name="Test",
            email="perfupdate@example.com"
        )
        contact_id = create_result["contact"]["resourceName"]
        
        # Measure performance of multiple updates
        execution_times = []
        
        for i in range(20):
            start_time = time.time()
            result = update_contact(
                contact_id,
                given_name=f"Updated{i}"
            )
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            self.assertEqual(result["names"][0]["givenName"], f"Updated{i}")
        
        # Performance assertions
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        self.assertLess(avg_time, 0.05, f"Average update_contact time too high: {avg_time:.3f}s")
        self.assertLess(max_time, 0.2, f"Maximum update_contact time too high: {max_time:.3f}s")

    def test_delete_contact_performance(self):
        """
        Test performance of delete_contact operation.
        """
        # Create multiple contacts to delete
        contact_ids = []
        for i in range(20):
            create_result = create_contact(
                given_name=f"PerfDelete{i}",
                family_name="Test",
                email=f"perfdelete{i}@example.com"
            )
            contact_ids.append(create_result["contact"]["resourceName"])
        
        # Measure performance of deleting contacts
        execution_times = []
        
        for contact_id in contact_ids:
            start_time = time.time()
            result = delete_contact(contact_id)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            self.assertEqual(result["status"], "success")
        
        # Performance assertions
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        self.assertLess(avg_time, 0.05, f"Average delete_contact time too high: {avg_time:.3f}s")
        self.assertLess(max_time, 0.2, f"Maximum delete_contact time too high: {max_time:.3f}s")

    def test_search_contacts_performance(self):
        """
        Test performance of search_contacts operation.
        """
        # Create contacts with searchable content
        for i in range(30):
            create_contact(
                given_name=f"Search{i}",
                family_name="Test",
                email=f"search{i}@example.com"
            )
        
        # Measure performance of different search queries
        search_queries = ["Search", "Test", "search", "nonexistent"]
        execution_times = []
        
        for query in search_queries:
            start_time = time.time()
            result = search_contacts(query)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
            
            self.assertIn("results", result)
        
        # Performance assertions
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        self.assertLess(avg_time, 0.1, f"Average search_contacts time too high: {avg_time:.3f}s")
        self.assertLess(max_time, 0.5, f"Maximum search_contacts time too high: {max_time:.3f}s")

    def test_bulk_operations_performance(self):
        """
        Test performance of bulk operations.
        """
        # Measure bulk create performance
        start_time = time.time()
        contact_ids = []
        
        for i in range(100):
            result = create_contact(
                given_name=f"Bulk{i}",
                family_name="Test",
                email=f"bulk{i}@example.com"
            )
            contact_ids.append(result["contact"]["resourceName"])
        
        create_time = time.time() - start_time
        
        # Measure bulk update performance
        start_time = time.time()
        for contact_id in contact_ids[:50]:  # Update first 50
            update_contact(contact_id, given_name="UpdatedBulk")
        update_time = time.time() - start_time
        
        # Measure bulk delete performance
        start_time = time.time()
        for contact_id in contact_ids:
            delete_contact(contact_id)
        delete_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(create_time, 10.0, f"Bulk create took too long: {create_time:.3f}s")
        self.assertLess(update_time, 5.0, f"Bulk update took too long: {update_time:.3f}s")
        self.assertLess(delete_time, 5.0, f"Bulk delete took too long: {delete_time:.3f}s")

    def test_memory_usage_performance(self):
        """
        Test memory usage during operations.
        """
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform operations
        contact_ids = []
        for i in range(50):
            result = create_contact(
                given_name=f"Memory{i}",
                family_name="Test",
                email=f"memory{i}@example.com"
            )
            contact_ids.append(result["contact"]["resourceName"])
        
        # Get memory usage after operations
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - initial_memory
        
        # Clean up
        for contact_id in contact_ids:
            delete_contact(contact_id)
        
        # Memory assertions
        self.assertLess(memory_increase, 100.0, f"Memory usage increased too much: {memory_increase:.2f}MB")

    def test_concurrent_operation_simulation_performance(self):
        """
        Test performance under simulated concurrent operations.
        """
        # Simulate rapid sequential operations (not truly concurrent but tests system stability)
        start_time = time.time()
        
        # Create contacts rapidly
        contact_ids = []
        for i in range(50):
            result = create_contact(
                given_name=f"Concurrent{i}",
                family_name="Test",
                email=f"concurrent{i}@example.com"
            )
            contact_ids.append(result["contact"]["resourceName"])
        
        # Perform mixed operations rapidly
        for i, contact_id in enumerate(contact_ids):
            if i % 3 == 0:  # Update every third contact
                update_contact(contact_id, given_name=f"Updated{i}")
            elif i % 3 == 1:  # Search for every third contact
                search_contacts(f"Concurrent{i}")
            # Leave the rest as is
        
        # Delete all contacts
        for contact_id in contact_ids:
            delete_contact(contact_id)
        
        total_time = time.time() - start_time
        
        # Performance assertions
        self.assertLess(total_time, 15.0, f"Concurrent operations took too long: {total_time:.3f}s")

    def test_large_dataset_performance(self):
        """
        Test performance with larger datasets.
        """
        # Create a larger dataset
        start_time = time.time()
        contact_ids = []
        
        for i in range(200):
            result = create_contact(
                given_name=f"Large{i}",
                family_name="Dataset",
                email=f"large{i}@example.com",
                phone=f"+1{i:09d}"
            )
            contact_ids.append(result["contact"]["resourceName"])
        
        create_time = time.time() - start_time
        
        # Test search performance on large dataset
        start_time = time.time()
        search_result = search_contacts("Large")
        search_time = time.time() - start_time
        
        # Test list performance on large dataset
        start_time = time.time()
        list_result = list_contacts(max_results=100)
        list_time = time.time() - start_time
        
        # Clean up
        for contact_id in contact_ids:
            delete_contact(contact_id)
        
        # Performance assertions
        self.assertLess(create_time, 20.0, f"Large dataset creation took too long: {create_time:.3f}s")
        self.assertLess(search_time, 2.0, f"Large dataset search took too long: {search_time:.3f}s")
        self.assertLess(list_time, 1.0, f"Large dataset list took too long: {list_time:.3f}s")

    def test_response_time_consistency(self):
        """
        Test that response times are consistent across multiple calls.
        """
        # Create a contact for testing
        create_result = create_contact(
            given_name="Consistency",
            family_name="Test",
            email="consistency@example.com"
        )
        contact_id = create_result["contact"]["resourceName"]
        
        # Measure response times for the same operation multiple times
        execution_times = []
        
        for _ in range(20):
            start_time = time.time()
            get_contact(contact_id)
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
        
        # Calculate statistics
        avg_time = statistics.mean(execution_times)
        std_dev = statistics.stdev(execution_times)
        
        # Consistency assertions
        self.assertLess(std_dev, 0.01, f"Response time too inconsistent: std_dev={std_dev:.6f}s")
        self.assertLess(avg_time, 0.01, f"Average response time too high: {avg_time:.6f}s")

    def test_error_handling_performance(self):
        """
        Test performance of error handling scenarios.
        """
        # Measure performance of operations that should fail
        execution_times = []
        
        for _ in range(20):
            start_time = time.time()
            try:
                get_contact("people/nonexistent")
            except Exception:
                pass  # Expected to fail
            end_time = time.time()
            
            execution_time = end_time - start_time
            execution_times.append(execution_time)
        
        # Performance assertions for error handling
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        self.assertLess(avg_time, 0.01, f"Error handling too slow: {avg_time:.6f}s")
        self.assertLess(max_time, 0.1, f"Error handling too slow: {max_time:.6f}s")

if __name__ == '__main__':
    unittest.main()
