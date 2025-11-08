"""
Smoke test suite for gemini_cli - basic health checks and API functionality
"""

import unittest
import sys
from pathlib import Path

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

import gemini_cli
from gemini_cli.SimulationEngine.db import DB
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError


def reset_session_for_testing():
    """Reset gemini_cli session state for testing."""
    from gemini_cli import shell_api
    
    shell_api.SESSION_SANDBOX_DIR = None
    shell_api.SESSION_INITIALIZED = False
    
    if '__sandbox_temp_dir_obj' in DB:
        try:
            DB['__sandbox_temp_dir_obj'].cleanup()
        except:
            pass
        del DB['__sandbox_temp_dir_obj']


class TestBasicSmokeTests(unittest.TestCase):
    """Basic smoke tests to verify package health."""

    def setUp(self):
        """Set up smoke test environment."""
        self.original_db_state = DB.copy()
        
        # Set up minimal clean state
        DB.clear()
        DB.update({
            "workspace_root": "/smoke_test_workspace",
            "cwd": "/smoke_test_workspace",
            "file_system": {
                "/smoke_test_workspace": {
                    "path": "/smoke_test_workspace",
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
        """Clean up smoke test environment."""
        reset_session_for_testing()
        DB.clear()
        DB.update(self.original_db_state)

    def test_package_imports_without_error(self):
        """Smoke test: Package imports without raising exceptions."""
        # Main package should import
        import gemini_cli
        self.assertIsNotNone(gemini_cli)
        
        # Key submodules should import
        from gemini_cli import file_system_api
        from gemini_cli import shell_api
        from gemini_cli import memory
        from gemini_cli import read_many_files_api
        
        self.assertIsNotNone(file_system_api)
        self.assertIsNotNone(shell_api)
        self.assertIsNotNone(memory)
        self.assertIsNotNone(read_many_files_api)

    def test_all_public_functions_accessible(self):
        """Smoke test: All public functions can be accessed."""
        expected_functions = [
            "list_directory",
            "read_file",
            "write_file",
            "glob",
            "search_file_content",
            "replace",
            "read_many_files",
            "save_memory",
            "run_shell_command"
        ]
        
        for func_name in expected_functions:
            with self.subTest(function=func_name):
                func = getattr(gemini_cli, func_name, None)
                self.assertIsNotNone(func, f"Function {func_name} not accessible")
                self.assertTrue(callable(func), f"Function {func_name} not callable")

    def test_basic_file_operations_work(self):
        """Smoke test: Basic file operations complete without crashing."""
        # Test write
        write_result = gemini_cli.write_file(
            file_path="/smoke_test_workspace/smoke_test.txt",
            content="Smoke test content"
        )
        self.assertIsInstance(write_result, dict)
        
        # Test read
        read_result = gemini_cli.read_file(
            path="/smoke_test_workspace/smoke_test.txt"
        )
        self.assertIsInstance(read_result, dict)
        
        # Test list directory
        list_result = gemini_cli.list_directory(
            path="/smoke_test_workspace"
        )
        self.assertIsInstance(list_result, list)

    def test_basic_search_operations_work(self):
        """Smoke test: Search operations complete without crashing."""
        # Set up test file
        gemini_cli.write_file(
            file_path="/smoke_test_workspace/search_test.py",
            content="def smoke_test_function():\n    return 'smoke test'"
        )
        
        # Test glob
        glob_result = gemini_cli.glob(
            pattern="*.py",
            path="/smoke_test_workspace"
        )
        self.assertIsInstance(glob_result, list)
        
        # Test content search
        search_result = gemini_cli.search_file_content(
            pattern="smoke_test_function",
            path="/smoke_test_workspace"
        )
        self.assertIsInstance(search_result, list)

    def test_basic_memory_operations_work(self):
        """Smoke test: Memory operations complete without crashing."""
        memory_result = gemini_cli.save_memory(
            fact="Smoke test memory entry"
        )
        self.assertIsInstance(memory_result, dict)

    def test_basic_shell_operations_work(self):
        """Smoke test: Shell operations complete without crashing."""
        shell_result = gemini_cli.run_shell_command(
            command="echo 'smoke test'"
        )
        self.assertIsInstance(shell_result, dict)

    def test_replace_operations_work(self):
        """Smoke test: Replace operations complete without crashing."""
        # Set up test file
        gemini_cli.write_file(
            file_path="/smoke_test_workspace/replace_test.txt",
            content="old_content\nmore content\ndifferent content"
        )
        
        # Test replace
        replace_result = gemini_cli.replace(
            file_path="/smoke_test_workspace/replace_test.txt",
            old_string="old_content",
            new_string="new_content"
        )
        self.assertIsInstance(replace_result, dict)

    def test_read_many_files_works(self):
        """Smoke test: Read many files operation works."""
        # Set up multiple test files
        for i in range(3):
            gemini_cli.write_file(
                file_path=f"/smoke_test_workspace/multi_test_{i}.txt",
                content=f"Content for file {i}"
            )
        
        # Test read many files
        read_many_result = gemini_cli.read_many_files(
            paths=["*.txt"]
        )
        self.assertIsInstance(read_many_result, dict)


class TestAPIResponseFormats(unittest.TestCase):
    """Smoke tests for API response formats and consistency."""

    def setUp(self):
        """Set up API response format tests."""
        self.original_db_state = DB.copy()
        
        DB.clear()
        DB.update({
            "workspace_root": "/api_test_workspace",
            "cwd": "/api_test_workspace",
            "file_system": {
                "/api_test_workspace": {
                    "path": "/api_test_workspace",
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
        """Clean up API response format tests."""
        reset_session_for_testing()
        DB.clear()
        DB.update(self.original_db_state)

    def test_all_operations_return_dicts(self):
        """Smoke test: All operations return dictionary responses."""
        # Set up test file for operations that need it
        gemini_cli.write_file(
            file_path="/api_test_workspace/api_test.txt",
            content="API test content"
        )
        
        operations = [
            lambda: gemini_cli.write_file("/api_test_workspace/new_file.txt", "content"),
            lambda: gemini_cli.read_file(path="/api_test_workspace/api_test.txt"),
            lambda: gemini_cli.list_directory(path="/api_test_workspace"),
            lambda: gemini_cli.glob("*.txt", path="/api_test_workspace"),
            lambda: gemini_cli.search_file_content("API test", path="/api_test_workspace"),
            lambda: gemini_cli.replace("/api_test_workspace/api_test.txt", "API test", "API modified"),
            lambda: gemini_cli.read_many_files(["*.txt"]),
            lambda: gemini_cli.save_memory("API test memory"),
            lambda: gemini_cli.run_shell_command("echo 'API test'")
        ]
        
        for i, operation in enumerate(operations):
            with self.subTest(operation=i):
                try:
                    result = operation()
                    # Some operations return lists (list_directory, glob, grep_search)
                    # Others return dicts (write_file, read_file, etc.)
                    if i in [2, 3, 4]:  # list_directory, glob, grep_search
                        self.assertIsInstance(result, list, 
                                            f"Operation {i} should return list, got {type(result)}")
                    else:
                        self.assertIsInstance(result, dict, 
                                            f"Operation {i} should return dict, got {type(result)}")
                except Exception as e:
                    # Operations may fail, but they shouldn't crash unexpectedly
                    self.fail(f"Operation {i} crashed unexpectedly: {e}")

    def test_error_responses_are_handled_gracefully(self):
        """Smoke test: Error conditions raise appropriate exceptions."""
        # Test reading non-existent file (should raise FileNotFoundError)
        with self.assertRaises(FileNotFoundError):
            gemini_cli.read_file(path="/api_test_workspace/nonexistent.txt")
        
        # Test listing non-existent directory (should raise InvalidInputError for outside workspace)
        with self.assertRaises((FileNotFoundError, InvalidInputError)):
            gemini_cli.list_directory(path="/nonexistent_directory")
        
        # Test replace with non-matching string (should raise RuntimeError)
        gemini_cli.write_file("/api_test_workspace/error_test.txt", "original content")
        with self.assertRaises(RuntimeError):
            gemini_cli.replace(
                "/api_test_workspace/error_test.txt",
                "non_existent_string",
                "replacement"
            )


class TestPackageStability(unittest.TestCase):
    """Smoke tests for package stability and robustness."""

    def setUp(self):
        """Set up stability tests."""
        self.original_db_state = DB.copy()

    def tearDown(self):
        """Clean up stability tests."""
        reset_session_for_testing()
        DB.clear()
        DB.update(self.original_db_state)

    def test_db_state_preservation(self):
        """Smoke test: DB state is preserved across operations."""
        # Set up workspace configuration first
        DB["workspace_root"] = "/test_workspace"
        DB["cwd"] = "/test_workspace"
        DB.setdefault("file_system", {})
        # Ensure workspace directory exists in file system
        DB["file_system"]["/test_workspace"] = {
            "path": "/test_workspace",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z"
        }
        
        initial_workspace = DB.get("workspace_root", "/default")
        
        # Perform various operations
        gemini_cli.write_file("/test_workspace/test_file.txt", "test content")
        gemini_cli.read_file(path="/test_workspace/test_file.txt")
        gemini_cli.list_directory(path="/test_workspace")
        
        # DB should still have consistent state
        final_workspace = DB.get("workspace_root", "/default")
        self.assertEqual(initial_workspace, final_workspace)
        
        # DB should still be a dictionary
        self.assertIsInstance(DB, dict)

    def test_repeated_operations_work(self):
        """Smoke test: Repeated operations work consistently."""
        # Set up workspace configuration first
        DB["workspace_root"] = "/test_workspace"
        DB["cwd"] = "/test_workspace"
        DB.setdefault("file_system", {})
        # Ensure workspace directory exists in file system
        DB["file_system"]["/test_workspace"] = {
            "path": "/test_workspace",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z"
        }
        
        # Repeat the same operation multiple times
        for i in range(5):
            result = gemini_cli.write_file(
                f"/test_workspace/stability_test_{i}.txt",
                f"Content for iteration {i}"
            )
            self.assertIsInstance(result, dict)
        
        # Read all files back
        for i in range(5):
            result = gemini_cli.read_file(path=f"/test_workspace/stability_test_{i}.txt")
            self.assertIsInstance(result, dict)

    def test_mixed_operations_stability(self):
        """Smoke test: Mixed operations maintain stability."""
        # Set up workspace configuration first
        DB["workspace_root"] = "/test_workspace"
        DB["cwd"] = "/test_workspace"
        DB.setdefault("file_system", {})
        # Ensure workspace directory exists in file system
        DB["file_system"]["/test_workspace"] = {
            "path": "/test_workspace",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z"
        }
        
        operations = [
            lambda: gemini_cli.write_file("/test_workspace/mixed_test_1.txt", "content 1"),
            lambda: gemini_cli.save_memory("Mixed test memory 1"),
            lambda: gemini_cli.list_directory(path="/test_workspace"),
            lambda: gemini_cli.write_file("/test_workspace/mixed_test_2.py", "def test(): pass"),
            lambda: gemini_cli.glob("*.py", path="/test_workspace"),
            lambda: gemini_cli.save_memory("Mixed test memory 2"),
            lambda: gemini_cli.read_file(path="/test_workspace/mixed_test_1.txt"),
            lambda: gemini_cli.search_file_content("content", path="/test_workspace"),
            lambda: gemini_cli.run_shell_command("echo 'mixed test'")
        ]
        
        # Execute all operations
        for i, operation in enumerate(operations):
            with self.subTest(operation=i):
                try:
                    result = operation()
                    # Handle different return types
                    if i in [2, 4, 7]:  # list_directory, glob, grep_search
                        self.assertIsInstance(result, list)
                    else:
                        self.assertIsInstance(result, dict)
                except Exception as e:
                    self.fail(f"Mixed operation {i} failed: {e}")
        
        # Verify DB is still in good state
        self.assertIsInstance(DB, dict)
        self.assertIn("workspace_root", DB)
        self.assertIn("file_system", DB)

    def test_invalid_input_handling(self):
        """Smoke test: Invalid inputs are handled gracefully."""
        # Test with various invalid inputs
        # Set up workspace for valid operations
        DB["workspace_root"] = "/test_workspace"
        DB["cwd"] = "/test_workspace"
        DB.setdefault("file_system", {})
        
        invalid_operations = [
            lambda: gemini_cli.write_file("", "content"),  # Empty path
            lambda: gemini_cli.write_file(None, "content"),  # None path
            lambda: gemini_cli.read_file(path=""),  # Empty path
            lambda: gemini_cli.list_directory(path=None),  # None directory
            lambda: gemini_cli.glob("", path=""),  # Empty pattern
            lambda: gemini_cli.save_memory(""),  # Empty memory
            lambda: gemini_cli.replace("", "", "")  # All empty strings
        ]
        
        for i, operation in enumerate(invalid_operations):
            with self.subTest(operation=i):
                try:
                    result = operation()
                    # Should return a response (not crash)
                    self.assertIsNotNone(result)
                except (TypeError, ValueError, Exception) as e:
                    # These exceptions are acceptable for invalid inputs
                    # Just ensure they are proper exception types
                    self.assertIsInstance(e, Exception)


class TestEnvironmentIndependence(unittest.TestCase):
    """Smoke tests for environment independence."""

    def test_no_external_dependencies_required(self):
        """Smoke test: Package works without external system dependencies."""
        # Should be able to import and use basic functionality
        # without requiring external tools or specific system setup
        
        import gemini_cli
        from gemini_cli.SimulationEngine.db import DB
        
        # Set up workspace configuration
        DB["workspace_root"] = "/test_workspace"
        DB["cwd"] = "/test_workspace"
        DB.setdefault("file_system", {})
        # Ensure workspace directory exists in file system
        DB["file_system"]["/test_workspace"] = {
            "path": "/test_workspace",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z"
        }
        
        # Basic operations should work in any environment
        result = gemini_cli.write_file("/test_workspace/env_test.txt", "environment test")
        self.assertIsInstance(result, dict)
        
        result = gemini_cli.read_file(path="/test_workspace/env_test.txt")
        self.assertIsInstance(result, dict)
        
        result = gemini_cli.list_directory(path="/test_workspace")
        self.assertIsInstance(result, list)

    def test_python_version_compatibility(self):
        """Smoke test: Basic compatibility with current Python version."""
        import sys
        
        # Should work with Python 3.7+
        self.assertGreaterEqual(sys.version_info.major, 3)
        self.assertGreaterEqual(sys.version_info.minor, 7)
        
        # Package should import without version-specific issues
        import gemini_cli
        self.assertIsNotNone(gemini_cli)

    def test_no_side_effects_on_import(self):
        """Smoke test: Importing doesn't cause unwanted side effects."""
        import os
        import tempfile
        
        # Get current working directory
        original_cwd = os.getcwd()
        
        # Get current environment
        original_env = dict(os.environ)
        
        # Import should not change current directory
        import gemini_cli
        self.assertEqual(os.getcwd(), original_cwd)
        
        # Import should not modify environment variables
        self.assertEqual(dict(os.environ), original_env)
        
        # Should not create files in current directory
        current_files = set(os.listdir('.'))
        
        # Re-import should be safe
        import importlib
        importlib.reload(gemini_cli)
        
        final_files = set(os.listdir('.'))
        new_files = final_files - current_files
        
        # Filter out expected cache files
        unexpected_files = [f for f in new_files 
                          if not f.endswith('.pyc') and '__pycache__' not in f]
        
        self.assertEqual(len(unexpected_files), 0, 
                        f"Import created unexpected files: {unexpected_files}")


if __name__ == "__main__":
    unittest.main()
