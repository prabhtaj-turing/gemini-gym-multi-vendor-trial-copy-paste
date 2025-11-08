"""
Performance test suite for gemini_cli
"""

import unittest
import time
import gc
import statistics
import sys
from pathlib import Path
from typing import Callable, List

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

import gemini_cli
from gemini_cli.SimulationEngine.db import DB
from gemini_cli.SimulationEngine.models import GeminiCliDB, DatabaseFileSystemEntry


@unittest.skipUnless(PSUTIL_AVAILABLE, "psutil not available")
class TestPerformance(unittest.TestCase):
    """Performance tests for gemini_cli operations."""

    def setUp(self):
        """Set up performance testing environment."""
        self.original_db_state = DB.copy()
        self.process = psutil.Process()
        
        # Set up clean test workspace
        DB.clear()
        DB.update({
            "workspace_root": "/test_workspace",
            "cwd": "/test_workspace",
            "file_system": {
                "/test_workspace": {
                    "path": "/test_workspace",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-01-01T12:00:00Z"
                }
            },
            "memory_storage": {},
            "background_processes": {},
            "tool_metrics": {}
        })

    def tearDown(self):
        """Clean up after performance tests."""
        DB.clear()
        DB.update(self.original_db_state)

    def measure_operation_time(self, operation_func: Callable, iterations: int = 10) -> dict:
        """Measure operation execution time."""
        times = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            try:
                result = operation_func()
                end_time = time.perf_counter()
                times.append(end_time - start_time)
            except Exception:
                # Count failed operations but don't break the test
                end_time = time.perf_counter()
                times.append(end_time - start_time)
        
        return {
            "min_time": min(times),
            "max_time": max(times),
            "avg_time": statistics.mean(times),
            "median_time": statistics.median(times),
            "total_time": sum(times),
            "iterations": iterations
        }

    def stress_test_memory_usage(self, operation_func: Callable, iterations: int = 100) -> List[float]:
        """Test memory usage under stress."""
        memory_usage = []
        
        for i in range(iterations):
            memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
            
            try:
                operation_func()
            except Exception:
                pass  # Ignore errors for stress testing
            
            memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_usage.append(memory_after - memory_before)
            
            # Force garbage collection every 20 iterations
            if i % 20 == 0:
                gc.collect()
        
        return memory_usage

    def test_file_write_performance(self):
        """Test file write operation performance."""
        def write_small_file():
            return gemini_cli.write_file(
                file_path="/test_workspace/perf_test.txt",
                content="Small test content for performance testing."
            )
        
        # Measure time performance
        time_stats = self.measure_operation_time(write_small_file, iterations=50)
        
        # Assertions for reasonable performance
        self.assertLess(time_stats["avg_time"], 0.1, 
                       f"Average write time too slow: {time_stats['avg_time']:.4f}s")
        self.assertLess(time_stats["max_time"], 0.5,
                       f"Maximum write time too slow: {time_stats['max_time']:.4f}s")
        
        print(f"File write performance - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_file_read_performance(self):
        """Test file read operation performance."""
        # Set up test file
        gemini_cli.write_file(
            file_path="/test_workspace/read_perf_test.txt",
            content="Test content for read performance testing.\n" * 100
        )
        
        def read_file():
            return gemini_cli.read_file(file_path="/test_workspace/read_perf_test.txt")
        
        # Measure time performance
        time_stats = self.measure_operation_time(read_file, iterations=50)
        
        # Assertions for reasonable performance
        self.assertLess(time_stats["avg_time"], 0.05,
                       f"Average read time too slow: {time_stats['avg_time']:.4f}s")
        self.assertLess(time_stats["max_time"], 0.2,
                       f"Maximum read time too slow: {time_stats['max_time']:.4f}s")
        
        print(f"File read performance - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_directory_listing_performance(self):
        """Test directory listing performance."""
        # Set up multiple files
        for i in range(20):
            gemini_cli.write_file(
                file_path=f"/test_workspace/file_{i:03d}.txt",
                content=f"Content for file {i}"
            )
        
        def list_directory():
            return gemini_cli.list_directory(directory_path="/test_workspace")
        
        # Measure time performance
        time_stats = self.measure_operation_time(list_directory, iterations=30)
        
        # Assertions for reasonable performance
        self.assertLess(time_stats["avg_time"], 0.1,
                       f"Average listing time too slow: {time_stats['avg_time']:.4f}s")
        
        print(f"Directory listing performance - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_glob_search_performance(self):
        """Test glob search performance."""
        # Set up files with different extensions
        file_types = ['.py', '.txt', '.md', '.json', '.yml']
        for i in range(50):
            ext = file_types[i % len(file_types)]
            gemini_cli.write_file(
                file_path=f"/test_workspace/glob_test_{i:03d}{ext}",
                content=f"Content for glob test file {i}"
            )
        
        def glob_search():
            return gemini_cli.glob(
                pattern="*.py",
                directory_path="/test_workspace"
            )
        
        # Measure time performance
        time_stats = self.measure_operation_time(glob_search, iterations=30)
        
        # Assertions for reasonable performance
        self.assertLess(time_stats["avg_time"], 0.1,
                       f"Average glob time too slow: {time_stats['avg_time']:.4f}s")
        
        print(f"Glob search performance - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_search_content_performance(self):
        """Test content search performance."""
        # Set up files with searchable content
        for i in range(30):
            content = f"""
def function_{i}():
    # This is function {i}
    return "result_{i}"

class Class_{i}:
    def method(self):
        return "method_result_{i}"
"""
            gemini_cli.write_file(
                file_path=f"/test_workspace/search_test_{i:03d}.py",
                content=content
            )
        
        def search_content():
            return gemini_cli.search_file_content(
                pattern="def function_",
                directory_path="/test_workspace"
            )
        
        # Measure time performance
        time_stats = self.measure_operation_time(search_content, iterations=20)
        
        # Assertions for reasonable performance
        self.assertLess(time_stats["avg_time"], 0.2,
                       f"Average search time too slow: {time_stats['avg_time']:.4f}s")
        
        print(f"Content search performance - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_replace_operation_performance(self):
        """Test replace operation performance."""
        # Set up test file with replaceable content
        content = "old_value\n" * 100 + "middle_content\n" + "old_value\n" * 100
        gemini_cli.write_file(
            file_path="/test_workspace/replace_perf_test.txt",
            content=content
        )
        
        def replace_content():
            return gemini_cli.replace(
                file_path="/test_workspace/replace_perf_test.txt",
                old_string="old_value",
                new_string="new_value"
            )
        
        # Measure time performance
        time_stats = self.measure_operation_time(replace_content, iterations=10)
        
        # Assertions for reasonable performance
        self.assertLess(time_stats["avg_time"], 0.1,
                       f"Average replace time too slow: {time_stats['avg_time']:.4f}s")
        
        print(f"Replace operation performance - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_memory_usage_file_operations(self):
        """Test memory usage during file operations."""
        def create_and_read_file():
            content = "Memory test content\n" * 50
            gemini_cli.write_file(
                file_path="/test_workspace/memory_test.txt",
                content=content
            )
            gemini_cli.read_file(file_path="/test_workspace/memory_test.txt")
        
        # Memory stress test
        memory_usage = self.stress_test_memory_usage(
            create_and_read_file,
            iterations=50
        )
        
        # Calculate memory statistics
        peak_memory = max(memory_usage) if memory_usage else 0
        avg_memory = statistics.mean(memory_usage) if memory_usage else 0
        
        print(f"Memory usage - Peak: {peak_memory:.2f}MB, Avg: {avg_memory:.2f}MB")
        
        # Assertions for reasonable memory usage
        self.assertLess(peak_memory, 10.0,
                       f"Peak memory usage too high: {peak_memory:.2f}MB")
        self.assertLess(avg_memory, 2.0,
                       f"Average memory usage too high: {avg_memory:.2f}MB")

    def test_concurrent_operations_performance(self):
        """Test performance of multiple operations in sequence."""
        def multi_operation_workflow():
            # Create file
            gemini_cli.write_file(
                file_path="/test_workspace/concurrent_test.py",
                content="def test(): pass\n"
            )
            
            # Read file
            gemini_cli.read_file(file_path="/test_workspace/concurrent_test.py")
            
            # List directory
            gemini_cli.list_directory(directory_path="/test_workspace")
            
            # Search content
            gemini_cli.search_file_content(
                pattern="def test",
                directory_path="/test_workspace"
            )
            
            # Replace content
            gemini_cli.replace(
                file_path="/test_workspace/concurrent_test.py",
                old_string="def test(): pass",
                new_string="def test():\n    return True"
            )
        
        # Measure performance of workflow
        time_stats = self.measure_operation_time(multi_operation_workflow, iterations=10)
        
        # Assertions for reasonable workflow performance
        self.assertLess(time_stats["avg_time"], 0.5,
                       f"Average workflow time too slow: {time_stats['avg_time']:.4f}s")
        
        print(f"Multi-operation workflow - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_large_file_handling_performance(self):
        """Test performance with larger files."""
        # Create a larger file (1MB of content)
        large_content = "This is a line of content for performance testing.\n" * 20000
        
        def write_large_file():
            return gemini_cli.write_file(
                file_path="/test_workspace/large_perf_test.txt",
                content=large_content
            )
        
        def read_large_file():
            return gemini_cli.read_file(file_path="/test_workspace/large_perf_test.txt")
        
        # Test write performance
        write_stats = self.measure_operation_time(write_large_file, iterations=3)
        self.assertLess(write_stats["avg_time"], 1.0,
                       f"Large file write too slow: {write_stats['avg_time']:.4f}s")
        
        # Test read performance
        read_stats = self.measure_operation_time(read_large_file, iterations=5)
        self.assertLess(read_stats["avg_time"], 0.5,
                       f"Large file read too slow: {read_stats['avg_time']:.4f}s")
        
        print(f"Large file - Write: {write_stats['avg_time']:.4f}s, "
              f"Read: {read_stats['avg_time']:.4f}s")

    def test_memory_operation_performance(self):
        """Test memory storage operation performance."""
        def save_memory_operation():
            return gemini_cli.save_memory(
                fact=f"Performance test memory entry {time.time()}"
            )
        
        # Measure memory operation performance
        time_stats = self.measure_operation_time(save_memory_operation, iterations=20)
        
        # Assertions for reasonable performance
        self.assertLess(time_stats["avg_time"], 0.05,
                       f"Average memory save time too slow: {time_stats['avg_time']:.4f}s")
        
        print(f"Memory operation performance - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_shell_command_performance(self):
        """Test shell command execution performance."""
        def run_simple_command():
            return gemini_cli.run_shell_command(command="echo 'performance test'")
        
        # Measure shell command performance
        time_stats = self.measure_operation_time(run_simple_command, iterations=10)
        
        # Assertions for reasonable performance (shell commands may be slower)
        self.assertLess(time_stats["avg_time"], 0.2,
                       f"Average shell command time too slow: {time_stats['avg_time']:.4f}s")
        
        print(f"Shell command performance - Avg: {time_stats['avg_time']:.4f}s, "
              f"Max: {time_stats['max_time']:.4f}s")

    def test_cpu_usage_during_operations(self):
        """Test CPU usage during intensive operations."""
        # Get initial CPU usage
        initial_cpu = self.process.cpu_percent()
        
        # Perform CPU-intensive operations
        for i in range(10):
            # Create file with substantial content
            content = [f"Line {j}: Content for CPU test\n" for j in range(1000)]
            gemini_cli.write_file(
                file_path=f"/test_workspace/cpu_test_{i}.txt",
                content="".join(content)
            )
            
            # Search through the content
            gemini_cli.search_file_content(
                pattern="Line 500",
                path="/test_workspace"
            )
        
        # Wait a bit for CPU measurement
        time.sleep(0.1)
        final_cpu = self.process.cpu_percent()
        
        # CPU usage should be reasonable (not necessarily low, but not excessive)
        print(f"CPU usage - Initial: {initial_cpu:.1f}%, Final: {final_cpu:.1f}%")
        
        # This is more of an informational test than a strict assertion
        self.assertIsInstance(final_cpu, float)

    @unittest.skipUnless(PSUTIL_AVAILABLE, "psutil not available")
    def test_resource_cleanup(self):
        """Test that resources are properly cleaned up."""
        # Get initial resource usage
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        initial_fds = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
        
        # Perform many operations
        for i in range(50):
            gemini_cli.write_file(
                file_path=f"/test_workspace/cleanup_test_{i}.txt",
                content=f"Content {i}"
            )
            gemini_cli.read_file(path=f"/test_workspace/cleanup_test_{i}.txt")
        
        # Force garbage collection
        gc.collect()
        time.sleep(0.1)
        
        # Check final resource usage
        final_memory = self.process.memory_info().rss / 1024 / 1024
        final_fds = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
        
        memory_growth = final_memory - initial_memory
        fd_growth = final_fds - initial_fds
        
        print(f"Resource usage - Memory growth: {memory_growth:.2f}MB, "
              f"FD growth: {fd_growth}")
        
        # Memory growth should be reasonable
        self.assertLess(memory_growth, 20.0,
                       f"Memory growth too high: {memory_growth:.2f}MB")
        
        # File descriptor growth should be minimal
        self.assertLess(fd_growth, 10,
                       f"File descriptor growth too high: {fd_growth}")


class TestPerformanceWithoutPsutil(unittest.TestCase):
    """Basic performance tests that don't require psutil."""

    def setUp(self):
        """Set up basic performance testing environment."""
        self.original_db_state = DB.copy()
        
        DB.clear()
        DB.update({
            "workspace_root": "/test_workspace",
            "cwd": "/test_workspace", 
            "file_system": {
                "/test_workspace": {
                    "path": "/test_workspace",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-01-01T12:00:00Z"
                }
            },
            "memory_storage": {},
            "background_processes": {},
            "tool_metrics": {}
        })

    def tearDown(self):
        """Clean up after basic performance tests."""
        DB.clear()
        DB.update(self.original_db_state)

    def test_basic_timing_performance(self):
        """Test basic operation timing without psutil."""
        # Test file write timing
        start_time = time.perf_counter()
        result = gemini_cli.write_file(
            file_path="/test_workspace/timing_test.txt",
            content="Basic timing test content"
        )
        end_time = time.perf_counter()
        
        write_time = end_time - start_time
        self.assertLess(write_time, 0.1, f"Write operation too slow: {write_time:.4f}s")
        self.assertTrue(result.get("success", False))
        
        # Test file read timing
        start_time = time.perf_counter()
        read_result = gemini_cli.read_file(path="/test_workspace/timing_test.txt")
        end_time = time.perf_counter()
        
        read_time = end_time - start_time
        self.assertLess(read_time, 0.05, f"Read operation too slow: {read_time:.4f}s")
        self.assertIn("content", read_result)

    def test_bulk_operations_timing(self):
        """Test timing of bulk operations."""
        start_time = time.perf_counter()
        
        # Create multiple files
        for i in range(20):
            gemini_cli.write_file(
                file_path=f"/test_workspace/bulk_{i:03d}.txt",
                content=f"Bulk test content {i}"
            )
        
        end_time = time.perf_counter()
        bulk_time = end_time - start_time
        
        # Should complete bulk operations in reasonable time
        self.assertLess(bulk_time, 2.0, f"Bulk operations too slow: {bulk_time:.4f}s")
        
        # Average time per operation should be reasonable
        avg_time_per_op = bulk_time / 20
        self.assertLess(avg_time_per_op, 0.1, 
                       f"Average time per operation too slow: {avg_time_per_op:.4f}s")

    def test_operation_scalability(self):
        """Test that operations scale reasonably with data size."""
        # Test with small content
        small_content = "Small content"
        start_time = time.perf_counter()
        gemini_cli.write_file(
            file_path="/test_workspace/small.txt",
            content=small_content
        )
        small_time = time.perf_counter() - start_time
        
        # Test with medium content
        medium_content = "Medium content line\n" * 100
        start_time = time.perf_counter()
        gemini_cli.write_file(
            file_path="/test_workspace/medium.txt",
            content=medium_content
        )
        medium_time = time.perf_counter() - start_time
        
        # Medium operation shouldn't be excessively slower than small
        time_ratio = medium_time / small_time if small_time > 0 else 1
        self.assertLess(time_ratio, 50, 
                       f"Medium file operation disproportionately slow: {time_ratio:.2f}x")


@unittest.skipUnless(PSUTIL_AVAILABLE, "psutil not available")
class TestDatabaseValidationPerformance(unittest.TestCase):
    """Test performance of database structure validation."""
    
    def setUp(self):
        """Set up performance testing environment."""
        self.original_db_state = DB.copy() if DB else {}
        
        # Ensure DB has required structure for validation
        if "file_system" not in DB:
            DB["file_system"] = {}
        if "memory_storage" not in DB:
            DB["memory_storage"] = {}
        if "shell_config" not in DB:
            DB["shell_config"] = {}
        if "background_processes" not in DB:
            DB["background_processes"] = {}
        if "tool_metrics" not in DB:
            DB["tool_metrics"] = {}
        if "gitignore_patterns" not in DB:
            DB["gitignore_patterns"] = []
        if "workspace_root" not in DB:
            DB["workspace_root"] = "/home/user/project"
        if "cwd" not in DB:
            DB["cwd"] = "/home/user/project"
        if "_created" not in DB:
            DB["_created"] = "2025-01-15T12:00:00Z"
        if "last_edit_params" not in DB:
            DB["last_edit_params"] = None
    
    def tearDown(self):
        """Restore original database state."""
        DB.clear()
        DB.update(self.original_db_state)
    
    def test_database_validation_performance_with_many_files(self):
        """Test performance of validating database with many file system entries."""
        file_count = 50  # Performance testing with simulated files
        workspace_root = DB.get("workspace_root", "/home/user/project")
        
        # Simulate creating many files by adding them directly to DB
        for i in range(file_count):
            file_path = f"{workspace_root}/perf_test_file_{i:03d}.txt"
            content_lines = [f"# Performance test file {i}\n", f"Content for file {i}\n"]
            DB["file_system"][file_path] = {
                "path": file_path,
                "is_directory": False,
                "content_lines": content_lines,
                "size_bytes": len(''.join(content_lines)),
                "last_modified": "2025-01-15T12:00:00Z"
            }
        
        # Measure validation performance
        validation_times = []
        
        for _ in range(5):  # Run validation 5 times
            start_time = time.time()
            
            try:
                validated_db = GeminiCliDB(**DB)
                # Verify we have the expected number of files (plus any existing ones)
                self.assertGreaterEqual(len(validated_db.file_system), file_count)
            except Exception as e:
                self.fail(f"Database validation failed: {e}")
            
            end_time = time.time()
            validation_times.append(end_time - start_time)
        
        # Performance assertions
        mean_time = statistics.mean(validation_times)
        max_time = max(validation_times)
        
        # Should validate many files in reasonable time
        self.assertLess(mean_time, 2.0, f"Mean validation time too slow: {mean_time:.3f}s")
        self.assertLess(max_time, 5.0, f"Max validation time too slow: {max_time:.3f}s")
        
        print(f"\nDatabase Validation Performance ({file_count} files):")
        print(f"  Mean time: {mean_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  Min time: {min(validation_times):.4f}s")
    
    def test_individual_file_entry_validation_performance(self):
        """Test performance of validating individual file system entries."""
        # Create comprehensive file data
        comprehensive_file_data = {
            "path": "/performance/comprehensive_test.py",
            "is_directory": False,
            "content_lines": [
                "#!/usr/bin/env python3\n",
                "\"\"\"Comprehensive test file for performance validation.\"\"\"\n",
                "\n",
                "import os\n",
                "import sys\n",
                "import json\n",
                "from typing import Dict, Any, List, Optional\n",
                "\n",
                "def main():\n",
                "    \"\"\"Main function for performance testing.\"\"\"\n",
                "    data = {'test': True, 'count': 42}\n",
                "    print(f'Performance test: {data}')\n",
                "\n",
                "if __name__ == '__main__':\n",
                "    main()\n"
            ],
            "size_bytes": 450,
            "last_modified": "2025-01-15T10:00:00Z"
        }
        
        # Measure individual entry validation performance
        validation_times = []
        
        for _ in range(100):  # Validate same entry 100 times
            start_time = time.time()
            
            try:
                validated_entry = DatabaseFileSystemEntry(**comprehensive_file_data)
                self.assertEqual(validated_entry.path, "/performance/comprehensive_test.py")
                self.assertFalse(validated_entry.is_directory)
                self.assertGreater(len(validated_entry.content_lines), 10)
            except Exception as e:
                self.fail(f"File entry validation failed: {e}")
            
            end_time = time.time()
            validation_times.append(end_time - start_time)
        
        # Performance assertions for individual entries
        mean_time = statistics.mean(validation_times)
        max_time = max(validation_times)
        
        # Individual validation should be very fast
        self.assertLess(mean_time, 0.001, f"Mean entry validation too slow: {mean_time:.6f}s")
        self.assertLess(max_time, 0.01, f"Max entry validation too slow: {max_time:.6f}s")
        
        print(f"\nFile Entry Validation Performance (100 iterations):")
        print(f"  Mean time: {mean_time:.6f}s")
        print(f"  Max time: {max_time:.6f}s")
        print(f"  Min time: {min(validation_times):.6f}s")


if __name__ == "__main__":
    unittest.main()
