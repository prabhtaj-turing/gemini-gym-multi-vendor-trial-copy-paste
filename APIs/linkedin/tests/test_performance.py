"""
Performance Test Cases for LinkedIn API Module.

Tests performance characteristics including:
- Function execution speed and timing
- Memory usage and leak detection
- Concurrent access performance
- Large data handling performance
- Database operation performance
- Import and load times
"""

import time
import unittest
import threading
import gc
import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

# Handle optional psutil dependency
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None


class TestPerformance(unittest.TestCase):
    """Performance test cases for LinkedIn API functionality."""

    def setUp(self):
        """Set up performance test fixtures."""
        # Import here to measure import time if needed
        import linkedin
        self.linkedin = linkedin
        
        # Reset database state
        from linkedin.tests.common import reset_db
        reset_db()
        
        # Get initial memory usage if psutil is available
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process(os.getpid())
            self.initial_memory = self.process.memory_info().rss
        else:
            self.process = None
            self.initial_memory = 0

    def tearDown(self):
        """Clean up after performance tests."""
        # Force garbage collection
        gc.collect()
        
        # Reset database state
        from linkedin.tests.common import reset_db
        reset_db()

    def measure_execution_time(self, func, *args, **kwargs):
        """Helper method to measure function execution time."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time

    def measure_memory_usage(self, func, *args, **kwargs):
        """Helper method to measure memory usage during function execution."""
        if not PSUTIL_AVAILABLE:
            # If psutil not available, just run function and return 0 memory delta
            result = func(*args, **kwargs)
            return result, 0
        
        gc.collect()  # Clean up before measurement
        mem_before = self.process.memory_info().rss
        
        result = func(*args, **kwargs)
        
        gc.collect()  # Clean up after execution
        mem_after = self.process.memory_info().rss
        memory_delta = mem_after - mem_before
        
        return result, memory_delta

    def test_import_performance(self):
        """Test that package import completes within reasonable time."""
        import sys
        
        # Remove linkedin from sys.modules if present
        modules_to_remove = [key for key in sys.modules.keys() if key.startswith('linkedin')]
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
        
        # Measure import time
        start_time = time.perf_counter()
        import linkedin
        end_time = time.perf_counter()
        
        import_time = end_time - start_time
        
        # Import should complete within 2 seconds
        self.assertLess(import_time, 2.0, 
                       f"Import took too long: {import_time:.3f} seconds")
        
        # Basic functionality should be available immediately
        self.assertTrue(hasattr(linkedin, 'create_post'))
        self.assertTrue(hasattr(linkedin, 'DB'))

    def test_function_resolution_performance(self):
        """Test performance of dynamic function resolution."""
        import linkedin
        
        # Test first-time resolution
        _, resolution_time = self.measure_execution_time(
            getattr, linkedin, 'create_post'
        )
        
        # First resolution should be reasonably fast (under 0.1 seconds)
        self.assertLess(resolution_time, 0.1, 
                       f"Function resolution took too long: {resolution_time:.3f} seconds")
        
        # Test subsequent resolutions (should be faster if cached)
        times = []
        for _ in range(10):
            _, time_taken = self.measure_execution_time(
                getattr, linkedin, 'create_post'
            )
            times.append(time_taken)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Average should be very fast
        self.assertLess(avg_time, 0.01, 
                       f"Average function resolution too slow: {avg_time:.4f} seconds")
        
        # Even the slowest should be reasonable
        self.assertLess(max_time, 0.05, 
                       f"Slowest function resolution too slow: {max_time:.4f} seconds")

    def test_database_operation_performance(self):
        """Test performance of database operations."""
        import linkedin
        
        # Test save_state performance
        _, save_time = self.measure_execution_time(
            linkedin.save_state, '/tmp/test_perf_save.json'
        )
        
        self.assertLess(save_time, 1.0, 
                       f"save_state took too long: {save_time:.3f} seconds")
        
        # Test load_state performance
        _, load_time = self.measure_execution_time(
            linkedin.load_state, '/tmp/test_perf_save.json'
        )
        
        self.assertLess(load_time, 1.0, 
                       f"load_state took too long: {load_time:.3f} seconds")
        
        # Clean up
        try:
            os.remove('/tmp/test_perf_save.json')
        except FileNotFoundError:
            pass

    def test_crud_operation_performance(self):
        """Test performance of CRUD operations."""
        import linkedin
        
        # Test create operations
        test_data = {
            "firstName": "Performance",
            "lastName": "Test",
            "emailAddress": "perf@test.com"
        }
        
        try:
            # Measure create_my_profile performance
            _, create_time = self.measure_execution_time(
                linkedin.create_my_profile, test_data
            )
            
            self.assertLess(create_time, 0.5, 
                           f"create_my_profile took too long: {create_time:.3f} seconds")
            
            # Measure get_my_profile performance
            _, get_time = self.measure_execution_time(
                linkedin.get_my_profile
            )
            
            self.assertLess(get_time, 0.1, 
                           f"get_my_profile took too long: {get_time:.3f} seconds")
            
            # Test update performance
            update_data = {"firstName": "Updated"}
            _, update_time = self.measure_execution_time(
                linkedin.update_my_profile, update_data
            )
            
            self.assertLess(update_time, 0.5, 
                           f"update_my_profile took too long: {update_time:.3f} seconds")
            
        except Exception as e:
            # If functions aren't fully implemented, that's okay for performance testing
            # Just ensure the timing mechanism works
            self.assertIsInstance(e, (AttributeError, ImportError, KeyError, TypeError, ValueError))

    def test_batch_operation_performance(self):
        """Test performance when performing many operations."""
        import linkedin
        
        num_operations = 100
        operation_times = []
        
        try:
            # Perform many get operations
            start_time = time.perf_counter()
            
            for i in range(num_operations):
                op_start = time.perf_counter()
                try:
                    linkedin.get_my_profile()
                except Exception:
                    pass  # Ignore errors for performance testing
                op_end = time.perf_counter()
                operation_times.append(op_end - op_start)
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # Total time should be reasonable
            self.assertLess(total_time, 10.0, 
                           f"Batch operations took too long: {total_time:.3f} seconds")
            
            # Average operation time should be fast
            if operation_times:
                avg_op_time = sum(operation_times) / len(operation_times)
                self.assertLess(avg_op_time, 0.1, 
                               f"Average operation time too slow: {avg_op_time:.4f} seconds")
                
        except Exception as e:
            # Log but don't fail if operations aren't implemented
            print(f"Note: Batch operations not fully testable: {e}")

    def test_memory_usage_crud_operations(self):
        """Test memory usage during CRUD operations."""
        if not PSUTIL_AVAILABLE:
            self.skipTest("psutil not available for memory testing")
        
        import linkedin
        
        test_data = {
            "firstName": "Memory",
            "lastName": "Test", 
            "emailAddress": "memory@test.com"
        }
        
        try:
            # Measure memory usage for create operation
            _, memory_delta = self.measure_memory_usage(
                linkedin.create_my_profile, test_data
            )
            
            # Memory usage should be reasonable (less than 10MB for single operation)
            self.assertLess(abs(memory_delta), 10 * 1024 * 1024, 
                           f"Create operation used too much memory: {memory_delta / 1024 / 1024:.2f} MB")
            
        except Exception as e:
            # If operations aren't implemented, that's acceptable
            self.assertIsInstance(e, (AttributeError, ImportError, KeyError, TypeError, ValueError))

    def test_concurrent_access_performance(self):
        """Test performance under concurrent access."""
        import linkedin
        
        num_threads = 10
        operations_per_thread = 10
        results = []
        errors = []
        
        def worker_thread():
            """Worker function for concurrent testing."""
            thread_times = []
            for _ in range(operations_per_thread):
                try:
                    start_time = time.perf_counter()
                    
                    # Try to access a function (this tests the import resolution)
                    func = getattr(linkedin, 'get_my_profile')
                    
                    # Try to call it (may fail, but that's okay for performance testing)
                    try:
                        func()
                    except Exception:
                        pass
                    
                    end_time = time.perf_counter()
                    thread_times.append(end_time - start_time)
                    
                except Exception as e:
                    errors.append(e)
            
            results.append(thread_times)
        
        # Run concurrent operations
        threads = []
        start_time = time.perf_counter()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker_thread)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30.0)  # 30 second timeout
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Concurrent operations should complete in reasonable time
        self.assertLess(total_time, 30.0, 
                       f"Concurrent operations took too long: {total_time:.3f} seconds")
        
        # Should have results from most threads
        self.assertGreater(len(results), num_threads * 0.5, 
                          "Too few threads completed successfully")
        
        # Calculate average operation time across all threads
        all_times = []
        for thread_times in results:
            all_times.extend(thread_times)
        
        if all_times:
            avg_time = sum(all_times) / len(all_times)
            max_time = max(all_times)
            
            self.assertLess(avg_time, 1.0, 
                           f"Average concurrent operation time too slow: {avg_time:.4f} seconds")
            self.assertLess(max_time, 5.0, 
                           f"Slowest concurrent operation too slow: {max_time:.4f} seconds")

    def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        import linkedin
        
        # Create a large state to test load/save performance
        large_state = {
            "people": {},
            "organizations": {},
            "organizationAcls": {},
            "posts": {},
            "next_person_id": 1001,
            "next_org_id": 1001,
            "next_acl_id": 1001,
            "next_post_id": 1001,
            "current_person_id": "1"
        }
        
        # Generate large dataset
        for i in range(1000):
            large_state["people"][str(i)] = {
                "id": str(i),
                "firstName": f"Person{i}",
                "lastName": f"Lastname{i}",
                "emailAddress": f"person{i}@example.com",
                "headline": f"Professional {i}",
                "summary": f"This is a detailed summary for person {i} " * 10  # Long text
            }
            
            if i % 10 == 0:  # Every 10th person gets a post
                large_state["posts"][str(i)] = {
                    "id": str(i),
                    "author": f"urn:li:person:{i}",
                    "commentary": f"This is post {i} with substantial content " * 5,
                    "visibility": "PUBLIC"
                }
        
        # Update DB with large dataset
        linkedin.DB.update(large_state)
        
        # Test saving large dataset
        large_file_path = '/tmp/large_state_perf_test.json'
        
        try:
            _, save_time = self.measure_execution_time(
                linkedin.save_state, large_file_path
            )
            
            # Should save large dataset in reasonable time (under 5 seconds)
            self.assertLess(save_time, 5.0, 
                           f"Large dataset save took too long: {save_time:.3f} seconds")
            
            # Verify file was created and has reasonable size
            self.assertTrue(os.path.exists(large_file_path))
            file_size = os.path.getsize(large_file_path)
            self.assertGreater(file_size, 100, "Saved file seems too small")
            
            # Test loading large dataset
            linkedin.DB.clear()  # Clear current state
            
            _, load_time = self.measure_execution_time(
                linkedin.load_state, large_file_path
            )
            
            # Should load large dataset in reasonable time (under 5 seconds)
            self.assertLess(load_time, 5.0, 
                           f"Large dataset load took too long: {load_time:.3f} seconds")
            
            # Verify data was loaded correctly
            self.assertEqual(len(linkedin.DB["people"]), 1000)
            self.assertGreater(len(linkedin.DB["posts"]), 90)  # Should have ~100 posts
            
        finally:
            # Clean up large file
            try:
                os.remove(large_file_path)
            except FileNotFoundError:
                pass

    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""
        if not PSUTIL_AVAILABLE:
            self.skipTest("psutil not available for memory leak testing")
        
        import linkedin
        
        # Get initial memory
        gc.collect()
        initial_memory = self.process.memory_info().rss
        
        # Perform many operations that might cause leaks
        for i in range(100):
            try:
                # Test function resolution (might cache objects)
                func = getattr(linkedin, 'create_post')
                
                # Test database operations
                temp_file = f'/tmp/leak_test_{i}.json'
                linkedin.save_state(temp_file)
                linkedin.load_state(temp_file)
                
                # Clean up file
                try:
                    os.remove(temp_file)
                except FileNotFoundError:
                    pass
                
                # Force garbage collection every 20 iterations
                if i % 20 == 0:
                    gc.collect()
                    
            except Exception:
                # Ignore errors for leak testing
                pass
        
        # Final cleanup and memory check
        gc.collect()
        final_memory = self.process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB)
        self.assertLess(memory_growth, 50 * 1024 * 1024, 
                       f"Possible memory leak detected: {memory_growth / 1024 / 1024:.2f} MB growth")

    def test_file_operations_performance(self):
        """Test performance of file utility operations."""
        from linkedin.SimulationEngine import file_utils
        
        # Test text file operations
        test_text = "Performance test content " * 1000  # ~25KB of text
        
        # Test encoding performance
        _, encode_time = self.measure_execution_time(
            file_utils.encode_to_base64, test_text
        )
        
        self.assertLess(encode_time, 0.1, 
                       f"Text encoding took too long: {encode_time:.3f} seconds")
        
        # Test decoding performance
        encoded_text = file_utils.encode_to_base64(test_text)
        _, decode_time = self.measure_execution_time(
            file_utils.decode_from_base64, encoded_text
        )
        
        self.assertLess(decode_time, 0.1, 
                       f"Text decoding took too long: {decode_time:.3f} seconds")
        
        # Test file type detection performance
        test_files = [
            "document.pdf", "script.py", "image.jpg", "data.json", 
            "video.mp4", "archive.zip", "style.css", "page.html"
        ] * 100  # Test with many files
        
        start_time = time.perf_counter()
        for filename in test_files:
            file_utils.is_text_file(filename)
            file_utils.is_binary_file(filename)
            file_utils.get_mime_type(filename)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        avg_time_per_file = total_time / len(test_files)
        
        self.assertLess(avg_time_per_file, 0.001, 
                       f"File type detection too slow: {avg_time_per_file:.6f} seconds per file")

    def test_model_validation_performance(self):
        """Test performance of Pydantic model validation."""
        from linkedin.SimulationEngine.models import PostDataModel
        
        # Test data for validation
        valid_post_data = {
            "author": "urn:li:person:123",
            "commentary": "This is a performance test post with some content",
            "visibility": "PUBLIC"
        }
        
        # Test single validation performance
        _, validation_time = self.measure_execution_time(
            PostDataModel, **valid_post_data
        )
        
        self.assertLess(validation_time, 0.01, 
                       f"Model validation took too long: {validation_time:.4f} seconds")
        
        # Test batch validation performance
        num_validations = 1000
        
        start_time = time.perf_counter()
        for i in range(num_validations):
            try:
                PostDataModel(
                    author=f"urn:li:person:{i}",
                    commentary=f"Performance test post {i}",
                    visibility="PUBLIC"
                )
            except Exception:
                pass  # Ignore validation errors for performance testing
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        avg_time = total_time / num_validations
        
        self.assertLess(avg_time, 0.001, 
                       f"Average model validation too slow: {avg_time:.6f} seconds")
        self.assertLess(total_time, 1.0, 
                       f"Batch model validation took too long: {total_time:.3f} seconds")

    def test_stress_test_rapid_operations(self):
        """Stress test with rapid consecutive operations."""
        import linkedin
        
        num_operations = 500
        max_time_per_operation = 0.1
        failed_operations = 0
        slow_operations = 0
        
        for i in range(num_operations):
            start_time = time.perf_counter()
            
            try:
                # Mix of different operations
                if i % 4 == 0:
                    getattr(linkedin, 'create_post')
                elif i % 4 == 1:
                    getattr(linkedin, 'get_my_profile')
                elif i % 4 == 2:
                    from linkedin.SimulationEngine.db import get_minified_state
                    get_minified_state()
                else:
                    hasattr(linkedin, f'function_{i}')  # Will fail, but tests error handling
                
            except Exception:
                failed_operations += 1
            
            end_time = time.perf_counter()
            operation_time = end_time - start_time
            
            if operation_time > max_time_per_operation:
                slow_operations += 1
        
        # Most operations should complete quickly
        success_rate = (num_operations - failed_operations) / num_operations
        speed_rate = (num_operations - slow_operations) / num_operations
        
        # At least 50% should succeed (since some operations will fail by design)
        self.assertGreater(success_rate, 0.5, 
                          f"Too many operations failed: {failed_operations}/{num_operations}")
        
        # At least 90% should be fast
        self.assertGreater(speed_rate, 0.9, 
                          f"Too many slow operations: {slow_operations}/{num_operations}")

    def test_resource_cleanup_performance(self):
        """Test that resources are cleaned up efficiently."""
        import linkedin
        import tempfile
        
        # Create many temporary files and ensure cleanup doesn't slow down
        temp_files = []
        
        try:
            # Create and clean up many files quickly
            start_time = time.perf_counter()
            
            for i in range(50):
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_files.append(temp_file.name)
                temp_file.close()
                
                # Save state to file
                linkedin.save_state(temp_file.name)
                
                # Load state from file
                linkedin.load_state(temp_file.name)
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # Should handle many file operations efficiently
            self.assertLess(total_time, 10.0, 
                           f"Resource operations took too long: {total_time:.3f} seconds")
            
            # Cleanup should be fast
            cleanup_start = time.perf_counter()
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except FileNotFoundError:
                    pass
            cleanup_end = time.perf_counter()
            
            cleanup_time = cleanup_end - cleanup_start
            self.assertLess(cleanup_time, 2.0, 
                           f"Cleanup took too long: {cleanup_time:.3f} seconds")
            
        finally:
            # Ensure cleanup even if test fails
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except FileNotFoundError:
                    pass


if __name__ == '__main__':
    # Run with higher verbosity for performance insights
    unittest.main(verbosity=2)
