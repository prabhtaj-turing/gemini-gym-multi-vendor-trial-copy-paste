"""Comprehensive tests for common file system functionality in utils.py"""

import unittest
import tempfile
import shutil
import os
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli.SimulationEngine.utils import (
    update_common_directory,
    get_common_directory,
    hydrate_file_system_from_common_directory,
    dehydrate_file_system_to_common_directory,
    with_common_file_system,
    set_enable_common_file_system
)
from gemini_cli.SimulationEngine.db import DB
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError


class TestCommonDirectoryConfig(unittest.TestCase):
    """Test cases for common directory configuration functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Enable common file system for tests
        set_enable_common_file_system(True)
        
        try:
            self.original_common_dir = get_common_directory()
        except RuntimeError:
            # No common directory is set initially (this is expected with default = None)
            self.original_common_dir = None
            
        self.test_dir = tempfile.mkdtemp(prefix="test_common_dir_")
        
        # Ensure the original common directory exists for testing (if it was set)
        if self.original_common_dir and not os.path.exists(self.original_common_dir):
            try:
                os.makedirs(self.original_common_dir, exist_ok=True)
            except PermissionError:
                # Skip if we don't have permission to create the directory
                pass
            
        # For unittest tests, we need to set up a common directory
        # Use the test_dir as a base for creating a common directory
        if self.original_common_dir is None:
            test_common_dir = os.path.join(self.test_dir, "common")
            os.makedirs(test_common_dir, exist_ok=True)
            update_common_directory(test_common_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original common directory (if there was one)
        if self.original_common_dir is not None:
            try:
                update_common_directory(self.original_common_dir)
            except:
                pass
        
        # Clean up test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_get_common_directory(self):
        """Test getting the current common directory."""
        current_dir = get_common_directory()
        self.assertIsInstance(current_dir, str)
        # Note: Directory may not exist if it's a default path like '/content'
        # We just verify we can get the configured value
        self.assertGreater(len(current_dir), 0)
    
    def test_update_common_directory_valid_path(self):
        """Test updating common directory with a valid path."""
        update_common_directory(self.test_dir)
        self.assertEqual(get_common_directory(), self.test_dir)
    
    def test_update_common_directory_rejects_missing_dir(self):
        """Test that update_common_directory rejects missing directories."""
        new_dir = os.path.join(self.test_dir, "new_subdir")
        self.assertFalse(os.path.exists(new_dir))
        
        with self.assertRaises(InvalidInputError) as context:
            update_common_directory(new_dir)
        
        self.assertIn("does not exist", str(context.exception))
    
    def test_update_common_directory_invalid_input(self):
        """Test update_common_directory with invalid input."""
        # Test empty string
        with self.assertRaises(InvalidInputError):
            update_common_directory("")
        
        # Test None
        with self.assertRaises(InvalidInputError):
            update_common_directory(None)
        
        # Test non-string
        with self.assertRaises(InvalidInputError):
            update_common_directory(123)
    
    def test_update_common_directory_unwritable_dir(self):
        """Test update_common_directory with unwritable directory."""
        # Create a directory and remove write permissions
        unwritable_dir = os.path.join(self.test_dir, "unwritable")
        os.makedirs(unwritable_dir)
        os.chmod(unwritable_dir, 0o444)  # Read-only
        try:
            with self.assertRaises(InvalidInputError):
                update_common_directory(unwritable_dir)
        finally:
            # Restore permissions for cleanup
            os.chmod(unwritable_dir, 0o755)


class TestFileSystemHydration(unittest.TestCase):
    """Test cases for file system hydration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Enable common file system for tests
        set_enable_common_file_system(True)
        
        try:
            self.original_common_dir = get_common_directory()
        except RuntimeError:
            # No common directory is set initially (this is expected with default = None)
            self.original_common_dir = None
            
        self.test_dir = tempfile.mkdtemp(prefix="test_hydration_")
        self.original_db_state = DB.copy()
        
        # Create test file structure
        self.create_test_files()
        update_common_directory(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original state
        DB.clear()
        DB.update(self.original_db_state)
        
        # Restore original common directory (if there was one)
        if self.original_common_dir is not None:
            try:
                update_common_directory(self.original_common_dir)
            except:
                pass
        
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_files(self):
        """Create test file structure."""
        # Create a simple text file
        with open(os.path.join(self.test_dir, "test.txt"), "w") as f:
            f.write("Hello World\n")
        
        # Create a subdirectory with a file
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "nested.txt"), "w") as f:
            f.write("Nested content\n")
        
        # Create an empty file
        with open(os.path.join(self.test_dir, "empty.txt"), "w") as f:
            pass
    
    def test_hydrate_file_system_success(self):
        """Test successful file system hydration."""
        # Clear file_system before test
        DB["file_system"] = {}
        
        hydrate_file_system_from_common_directory()
        
        # Check that file_system was populated
        self.assertIn("file_system", DB)
        file_system = DB["file_system"]
        
        # Should have 5 entries: root dir, subdir, and 3 files
        self.assertEqual(len(file_system), 5)
        
        # Check root directory (now uses absolute path of test_dir)
        root_path = self.test_dir
        self.assertIn(root_path, file_system)
        self.assertTrue(file_system[root_path]["is_directory"])
        
        # Check text file (now uses absolute path)
        test_file = os.path.join(self.test_dir, "test.txt")
        self.assertIn(test_file, file_system)
        self.assertFalse(file_system[test_file]["is_directory"])
        self.assertEqual(file_system[test_file]["size_bytes"], 12)
        self.assertEqual(file_system[test_file]["content_lines"], ["Hello World\n"])
        
        # Check subdirectory (now uses absolute path)
        subdir_path = os.path.join(self.test_dir, "subdir")
        self.assertIn(subdir_path, file_system)
        self.assertTrue(file_system[subdir_path]["is_directory"])
        
        # Check nested file (now uses absolute path)
        nested_file = os.path.join(self.test_dir, "subdir", "nested.txt")
        self.assertIn(nested_file, file_system)
        self.assertEqual(file_system[nested_file]["content_lines"], ["Nested content\n"])
        
        # Check empty file (now uses absolute path)
        empty_file = os.path.join(self.test_dir, "empty.txt")
        self.assertIn(empty_file, file_system)
        self.assertEqual(file_system[empty_file]["size_bytes"], 0)
        self.assertEqual(file_system[empty_file]["content_lines"], [])
        
        # Verify workspace_root and cwd are set to the common directory
        self.assertEqual(DB["workspace_root"], self.test_dir)
        self.assertEqual(DB["cwd"], self.test_dir)
    
    def test_hydrate_nonexistent_directory(self):
        """Test hydration with nonexistent common directory."""
        # Create a directory and then delete it to simulate missing directory
        nonexistent_dir = os.path.join(self.test_dir, "will_be_deleted")
        os.makedirs(nonexistent_dir)
        update_common_directory(nonexistent_dir)
        
        # Now delete the directory to simulate missing directory
        shutil.rmtree(nonexistent_dir)
        
        with self.assertRaises(FileNotFoundError):
            hydrate_file_system_from_common_directory()
    
    def test_hydrate_file_instead_of_directory(self):
        """Test update_common_directory rejects file path."""
        test_file = os.path.join(self.test_dir, "not_a_dir.txt")
        with open(test_file, "w") as f:
            f.write("content")
        
        with self.assertRaises(InvalidInputError) as context:
            update_common_directory(test_file)
        
        self.assertIn("not a directory", str(context.exception))


class TestFileSystemDehydration(unittest.TestCase):
    """Test cases for file system dehydration functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Enable common file system for tests
        set_enable_common_file_system(True)
        
        try:
            self.original_common_dir = get_common_directory()
        except RuntimeError:
            # No common directory is set initially (this is expected with default = None)
            self.original_common_dir = None
            
        self.test_dir = tempfile.mkdtemp(prefix="test_dehydration_")
        self.original_db_state = DB.copy()
        
        update_common_directory(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original state
        DB.clear()
        DB.update(self.original_db_state)
        
        # Restore original common directory (if there was one)
        if self.original_common_dir is not None:
            try:
                update_common_directory(self.original_common_dir)
            except:
                pass
        
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_dehydrate_empty_file_system(self):
        """Test dehydration with empty file_system."""
        DB["file_system"] = {}
        
        # Should not raise an error
        dehydrate_file_system_to_common_directory()
        
        # Common directory should still exist
        self.assertTrue(os.path.isdir(self.test_dir))


class TestCommonFileSystemDecorator(unittest.TestCase):
    """Test cases for the with_common_file_system decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Enable common file system for tests
        set_enable_common_file_system(True)
        
        try:
            self.original_common_dir = get_common_directory()
        except RuntimeError:
            # No common directory is set initially (this is expected with default = None)
            self.original_common_dir = None
            
        self.test_dir = tempfile.mkdtemp(prefix="test_decorator_")
        self.original_db_state = DB.copy()
        
        # Create a simple test file
        with open(os.path.join(self.test_dir, "test.txt"), "w") as f:
            f.write("Original content\n")
        
        update_common_directory(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original state
        DB.clear()
        DB.update(self.original_db_state)
        
        # Restore original common directory (if there was one)
        if self.original_common_dir is not None:
            try:
                update_common_directory(self.original_common_dir)
            except:
                pass
        
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @with_common_file_system
        def test_function():
            """Test function docstring."""
            return "test_result"
        
        self.assertEqual(test_function.__name__, "test_function")
        self.assertEqual(test_function.__doc__, "Test function docstring.")
    
    def test_decorator_hydrates_and_dehydrates(self):
        """Test that decorator properly hydrates before and dehydrates after function execution."""
        # Clear file_system initially
        DB["file_system"] = {}
        
        @with_common_file_system
        def modify_file_system():
            # Check that file_system was hydrated
            self.assertIn("file_system", DB)
            self.assertGreater(len(DB["file_system"]), 0)
            
            # Modify file_system (use absolute physical path)
            physical_file_path = os.path.join(self.test_dir, "new_file.txt")
            DB["file_system"][physical_file_path] = {
                "path": physical_file_path,
                "is_directory": False,
                "content_lines": ["New content\n"],
                "size_bytes": 12,
                "last_modified": "2025-01-15T12:00:00Z"
            }
            return "success"
        
        # Execute function
        result = modify_file_system()
        
        # Check function result
        self.assertEqual(result, "success")
        
        # Check that new file was created by dehydration (check physical path)
        expected_file_path = os.path.join(self.test_dir, "new_file.txt")
        self.assertTrue(os.path.isfile(expected_file_path))
        
        with open(expected_file_path, "r") as f:
            self.assertEqual(f.read(), "New content\n")
    
    def test_decorator_handles_function_exceptions(self):
        """Test that decorator properly handles exceptions in wrapped functions."""
        @with_common_file_system
        def failing_function():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            failing_function()
    
    def test_decorator_handles_missing_common_directory(self):
        """Test that decorator handles missing common directory."""
        # Create a directory and then delete it to simulate missing directory
        nonexistent_dir = os.path.join(self.test_dir, "will_be_deleted")
        os.makedirs(nonexistent_dir)
        update_common_directory(nonexistent_dir)
        
        # Now delete the directory to simulate missing directory
        shutil.rmtree(nonexistent_dir)
        
        @with_common_file_system
        def test_function():
            return "should not execute"
        
        with self.assertRaises(FileNotFoundError):
            test_function()


class TestIntegration(unittest.TestCase):
    """Integration tests for common file system functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Enable common file system for tests
        set_enable_common_file_system(True)
        
        try:
            self.original_common_dir = get_common_directory()
        except RuntimeError:
            # No common directory is set initially (this is expected with default = None)
            self.original_common_dir = None
            
        self.test_dir = tempfile.mkdtemp(prefix="test_integration_")
        self.original_db_state = DB.copy()
        
        update_common_directory(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original state
        DB.clear()
        DB.update(self.original_db_state)
        
        # Restore original common directory (if there was one)
        if self.original_common_dir is not None:
            try:
                update_common_directory(self.original_common_dir)
            except:
                pass
        
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_hydrate_dehydrate_cycle(self):
        """Test complete hydrate -> modify -> dehydrate cycle."""
        # Create initial files
        initial_file = os.path.join(self.test_dir, "initial.txt")
        with open(initial_file, "w") as f:
            f.write("Initial content\n")
        
        # Hydrate
        hydrate_file_system_from_common_directory()
        
        # Verify initial state (use absolute physical path)
        physical_initial_file = os.path.join(self.test_dir, "initial.txt")
        self.assertIn(physical_initial_file, DB["file_system"])
        self.assertEqual(DB["file_system"][physical_initial_file]["content_lines"], ["Initial content\n"])
        
        # Modify file_system (use absolute physical path)
        physical_modified_file = os.path.join(self.test_dir, "modified.txt")
        DB["file_system"][physical_modified_file] = {
            "path": physical_modified_file,
            "is_directory": False,
            "content_lines": ["Modified content\n"],
            "size_bytes": 17,
            "last_modified": "2025-01-15T12:00:00Z"
        }
        
        # Update existing file (use absolute physical path)
        DB["file_system"][physical_initial_file]["content_lines"] = ["Updated content\n"]
        
        # Dehydrate
        dehydrate_file_system_to_common_directory()
        
        # Verify physical files (check expected physical locations)
        expected_initial_file = os.path.join(self.test_dir, "initial.txt")
        expected_modified_file = os.path.join(self.test_dir, "modified.txt")
        
        self.assertTrue(os.path.isfile(expected_initial_file))
        self.assertTrue(os.path.isfile(expected_modified_file))
        
        with open(expected_initial_file, "r") as f:
            self.assertEqual(f.read(), "Updated content\n")
        
        with open(expected_modified_file, "r") as f:
            self.assertEqual(f.read(), "Modified content\n")
        
        # Hydrate again to verify round-trip
        DB["file_system"] = {}
        hydrate_file_system_from_common_directory()
        
        # Verify round-trip using logical paths
        self.assertIn(physical_initial_file, DB["file_system"])
        self.assertIn(physical_modified_file, DB["file_system"])
        self.assertEqual(DB["file_system"][physical_initial_file]["content_lines"], ["Updated content\n"])
        self.assertEqual(DB["file_system"][physical_modified_file]["content_lines"], ["Modified content\n"])

    def test_end_to_end_common_file_system_demo(self):
        """Demonstrate complete common file system workflow with verbose output."""
        
        # Create initial demo file
        demo_file_path = os.path.join(self.test_dir, "demo.txt")
        with open(demo_file_path, "w") as f:
            f.write("Initial demo content\n")
        
        # Step 1: Configure common directory (already done in setUp)
        print(f"\n✅ Demo Step 1: Common directory set to {self.test_dir}")
        
        # Step 2: Define a function that works with files
        @with_common_file_system
        def demo_file_operation():
            """Example function that reads and modifies files."""
            
            # At this point, the decorator has automatically:
            # - Hydrated file_system from common directory
            # - We can now work with files in memory
            
            print(f"✅ Demo Step 2: File system hydrated - {len(DB['file_system'])} items loaded")
            
            # Read existing file (use absolute physical path)
            physical_demo_file_path = os.path.join(self.test_dir, "demo.txt")
            if physical_demo_file_path in DB["file_system"]:
                original_content = "".join(DB["file_system"][physical_demo_file_path]["content_lines"])
                print(f"✅ Demo Step 3: Read existing file content: '{original_content.strip()}'")
            
            # Modify existing file in memory (use absolute physical path)
            DB["file_system"][physical_demo_file_path]["content_lines"] = ["Modified demo content\n"]
            print("✅ Demo Step 4: Modified existing file in memory")
            
            # Add new file in memory (use absolute physical path)
            physical_new_file_path = os.path.join(self.test_dir, "new_demo_file.txt")
            DB["file_system"][physical_new_file_path] = {
                "path": physical_new_file_path,
                "is_directory": False,
                "content_lines": ["This is a new file created in memory\n"],
                "size_bytes": 35,
                "last_modified": "2025-01-15T12:00:00Z"
            }
            print("✅ Demo Step 5: Added new file in memory")
            
            return "Demo operation completed"
        
        # Step 3: Execute the wrapped function
        result = demo_file_operation()
        print(f"✅ Demo Step 6: Function executed - {result}")
        
        # At this point, the decorator has automatically:
        # - Dehydrated the file_system back to the common directory
        # - All changes are now persisted to physical files
        
        # Step 4: Verify changes were persisted
        demo_file_physical = os.path.join(self.test_dir, "demo.txt")
        new_file_physical = os.path.join(self.test_dir, "new_demo_file.txt")
        
        # Check modified file
        with open(demo_file_physical, "r") as f:
            modified_content = f.read()
        self.assertEqual(modified_content, "Modified demo content\n")
        print(f"✅ Demo Step 7: Verified modified file: '{modified_content.strip()}'")
        
        # Check new file
        self.assertTrue(os.path.isfile(new_file_physical))
        with open(new_file_physical, "r") as f:
            new_content = f.read()
        self.assertEqual(new_content, "This is a new file created in memory\n")
        print(f"✅ Demo Step 8: Verified new file: '{new_content.strip()}'")
        
        print("\n🎉 End-to-end demo completed successfully!")
        print("   - Common directory configuration ✅")
        print("   - Automatic hydration before function ✅")
        print("   - In-memory file operations ✅")
        print("   - Automatic dehydration after function ✅")
        print("   - Changes persisted to physical files ✅")


if __name__ == '__main__':
    unittest.main() 