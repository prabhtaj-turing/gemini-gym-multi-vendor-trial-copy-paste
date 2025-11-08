# """
# Test to verify that the common file system properly handles file deletions
# and that the dehydration process is leak-proof.
# """

# import json
# import os
# import sys
# import tempfile
# import shutil
# from pathlib import Path

# import pytest

# # Ensure package root is importable when tests run via py.test
# sys.path.append(str(Path(__file__).resolve().parents[2]))

# from gemini_cli.SimulationEngine import db as sim_db
# from gemini_cli.SimulationEngine.utils import (
#     update_common_directory, 
#     get_common_directory,
#     hydrate_file_system_from_common_directory,
#     dehydrate_file_system_to_common_directory
# )

# # Import gemini_cli functions (these will be wrapped if environment variable is set)
# from gemini_cli import write_file, list_directory

# DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


# class TestDeletionLeakProof:
#     """Test that file deletions are properly handled without leaks."""

#     @pytest.fixture(autouse=True)
#     def setup_test_environment(self):
#         """Set up isolated test environment."""
#         # Enable common file system for these tests
#         os.environ['GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM'] = 'true'
        
#         # Create temporary directory for testing
#         self.temp_dir = tempfile.mkdtemp(prefix="test_deletion_leak_")
#         self.original_common_dir = get_common_directory()
        
#         # Update to use our test directory
#         update_common_directory(self.temp_dir)
        
#         # Load fresh DB snapshot but clear file_system entries that conflict with our test paths
#         sim_db.DB.clear()
#         with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
#             default_db = json.load(fh)
#             # Update workspace_root and cwd to match our temp directory
#             default_db["workspace_root"] = self.temp_dir
#             default_db["cwd"] = self.temp_dir
#             # Clear file_system so we start with a clean slate
#             default_db["file_system"] = {}
#             sim_db.DB.update(default_db)
            
#         yield
        
#         # Cleanup
#         try:
#             update_common_directory(self.original_common_dir)
#         except:
#             pass
        
#         try:
#             shutil.rmtree(self.temp_dir)
#         except:
#             pass
            
#         # Restore common file system setting for other tests
#         # (conftest.py sets it to 'false' by default for tests)
#         os.environ['GEMINI_CLI_ENABLE_COMMON_FILE_SYSTEM'] = 'false'
        
#         sim_db.DB.clear()

#     def test_file_deletion_reflected_in_common_directory(self):
#         """Test that deleted files are removed from common directory."""
        
#         # Step 1: Create some test files in the simulation DB using paths relative to common directory
#         test_file_1 = os.path.join(self.temp_dir, "test_file_1.txt")
#         test_file_2 = os.path.join(self.temp_dir, "test_file_2.txt")
        
#         # Add files to DB
#         sim_db.DB["file_system"][test_file_1] = {
#             "path": test_file_1,
#             "is_directory": False,
#             "content_lines": ["Hello World 1\n"],
#             "size_bytes": 14,
#             "last_modified": "2025-01-15T10:00:00Z"
#         }
        
#         sim_db.DB["file_system"][test_file_2] = {
#             "path": test_file_2,
#             "is_directory": False,
#             "content_lines": ["Hello World 2\n"],
#             "size_bytes": 14,
#             "last_modified": "2025-01-15T10:00:00Z"
#         }
        
#         # Step 2: Dehydrate to common directory (both files should appear)
#         dehydrate_file_system_to_common_directory()
        
#         # Verify both files exist in common directory (paths are already correct)
#         assert os.path.exists(test_file_1), "Test file 1 should exist in common directory"
#         assert os.path.exists(test_file_2), "Test file 2 should exist in common directory"
        
#         # Verify content
#         with open(test_file_1, "r") as f:
#             assert f.read() == "Hello World 1\n"
#         with open(test_file_2, "r") as f:
#             assert f.read() == "Hello World 2\n"
        
#         # Step 3: Delete one file from the simulation DB
#         del sim_db.DB["file_system"][test_file_1]
        
#         # Step 4: Dehydrate again (deleted file should be removed from common directory)
#         dehydrate_file_system_to_common_directory()
        
#         # Step 5: Verify that the deleted file is gone from common directory
#         assert not os.path.exists(test_file_1), "Deleted file should NOT exist in common directory"
#         assert os.path.exists(test_file_2), "Remaining file should still exist in common directory"
        
#         # Verify remaining file content is intact
#         with open(test_file_2, "r") as f:
#             assert f.read() == "Hello World 2\n"

#     def test_directory_deletion_reflected_in_common_directory(self):
#         """Test that deleted directories are removed from common directory."""
        
#         # Step 1: Create a directory structure using paths relative to common directory
#         test_dir = os.path.join(self.temp_dir, "test_dir")
#         test_file_in_dir = os.path.join(self.temp_dir, "test_dir", "file.txt")
        
#         # Add directory and file to DB
#         sim_db.DB["file_system"][test_dir] = {
#             "path": test_dir,
#             "is_directory": True,
#             "content_lines": [],
#             "size_bytes": 0,
#             "last_modified": "2025-01-15T10:00:00Z"
#         }
        
#         sim_db.DB["file_system"][test_file_in_dir] = {
#             "path": test_file_in_dir,
#             "is_directory": False,
#             "content_lines": ["File in directory\n"],
#             "size_bytes": 18,
#             "last_modified": "2025-01-15T10:00:00Z"
#         }
        
#         # Step 2: Dehydrate to common directory
#         dehydrate_file_system_to_common_directory()
        
#         # Verify directory and file exist (paths are already correct)
#         assert os.path.exists(test_dir), "Test directory should exist in common directory"
#         assert os.path.isdir(test_dir), "Test directory should be a directory"
#         assert os.path.exists(test_file_in_dir), "File in directory should exist in common directory"
        
#         # Step 3: Delete the entire directory structure from DB
#         del sim_db.DB["file_system"][test_dir]
#         del sim_db.DB["file_system"][test_file_in_dir]
        
#         # Step 4: Dehydrate again
#         dehydrate_file_system_to_common_directory()
        
#         # Step 5: Verify directory and file are gone
#         assert not os.path.exists(test_dir), "Deleted directory should NOT exist in common directory"
#         assert not os.path.exists(test_file_in_dir), "File in deleted directory should NOT exist in common directory"

#     def test_hydrate_dehydrate_cycle_with_deletions(self):
#         """Test complete hydrate-dehydrate cycle handles deletions correctly."""
        
#         # Step 1: Create initial file structure in common directory
#         test_files = [
#             ("file1.txt", "Content 1\n"),
#             ("file2.txt", "Content 2\n"), 
#             ("subdir/file3.txt", "Content 3\n")
#         ]
        
#         for rel_path, content in test_files:
#             full_path = os.path.join(self.temp_dir, rel_path)
#             os.makedirs(os.path.dirname(full_path), exist_ok=True)
#             with open(full_path, "w") as f:
#                 f.write(content)
        
#         # Step 2: Hydrate from common directory
#         hydrate_file_system_from_common_directory()
        
#         # Verify files are in DB (use actual paths from temp directory)
#         file1_db_path = os.path.join(self.temp_dir, "file1.txt")
#         file2_db_path = os.path.join(self.temp_dir, "file2.txt")
#         file3_db_path = os.path.join(self.temp_dir, "subdir", "file3.txt")
        
#         assert file1_db_path in sim_db.DB["file_system"]
#         assert file2_db_path in sim_db.DB["file_system"]
#         assert file3_db_path in sim_db.DB["file_system"]
        
#         # Step 3: Delete one file from DB
#         del sim_db.DB["file_system"][file2_db_path]
        
#         # Step 4: Dehydrate back to common directory
#         dehydrate_file_system_to_common_directory()
        
#         # Step 5: Verify deletion is reflected in common directory
#         file1_path = os.path.join(self.temp_dir, "file1.txt")
#         file2_path = os.path.join(self.temp_dir, "file2.txt")
#         file3_path = os.path.join(self.temp_dir, "subdir", "file3.txt")
        
#         assert os.path.exists(file1_path), "File 1 should still exist"
#         assert not os.path.exists(file2_path), "File 2 should be deleted"
#         assert os.path.exists(file3_path), "File 3 should still exist"
        
#         # Verify content of remaining files
#         with open(file1_path, "r") as f:
#             assert f.read() == "Content 1\n"
#         with open(file3_path, "r") as f:
#             assert f.read() == "Content 3\n"

#     def test_wrapped_function_handles_deletions(self):
#         """Test that wrapped functions properly handle deletions via hydrate/dehydrate."""
        
#         # This test verifies that when using wrapped functions (like write_file with common file system enabled),
#         # the hydrate/dehydrate cycle properly handles deletions
        
#         # Step 1: Manually create some files in common directory
#         file1_path = os.path.join(self.temp_dir, "will_remain.txt")
#         file2_path = os.path.join(self.temp_dir, "will_be_deleted.txt")
        
#         os.makedirs(os.path.dirname(file1_path), exist_ok=True)
        
#         with open(file1_path, "w") as f:
#             f.write("This file will remain\n")
#         with open(file2_path, "w") as f:
#             f.write("This file will be deleted\n")
        
#         # Step 2: Use a wrapped function (write_file) to create a new file
#         # This should: hydrate (load existing files) -> execute (create new file) -> dehydrate (save all)
#         new_file_abs_path = os.path.join(self.temp_dir, "new_file.txt")
#         write_file(new_file_abs_path, "New file content\n")
        
#         # Verify all files exist in common directory after the first wrapped operation
#         new_file_path = new_file_abs_path
#         assert os.path.exists(file1_path), "Original file 1 should exist after wrapped operation"
#         assert os.path.exists(file2_path), "Original file 2 should exist after wrapped operation"
#         assert os.path.exists(new_file_path), "New file should exist after wrapped operation"
        
#         # Step 3: Manually delete a file from the DB (simulating a file operation that removes it)
#         # In real usage, this would happen through a file operation like delete_file()
#         del sim_db.DB["file_system"][file2_path]
        
#         # Step 4: Use another wrapped function (list_directory) 
#         # This should: hydrate (overwrite DB with common directory) -> execute (list files) -> dehydrate (save current DB state)
#         # Since we deleted a file from DB but it still exists in common directory, 
#         # the hydration will bring it back, then dehydration will preserve it
#         files = list_directory(self.temp_dir)
        
#         # Step 5: After the wrapped function, the deleted file should be restored because hydration loaded it back
#         # This is actually correct behavior - if we want to delete from common directory, 
#         # we need to delete and then call a wrapped function
#         assert os.path.exists(file1_path), "File 1 should still exist"
#         assert os.path.exists(file2_path), "File 2 should be restored by hydration"
#         assert os.path.exists(new_file_path), "New file should still exist"
        
#         # Step 6: Now test proper deletion - delete from DB and immediately dehydrate
#         del sim_db.DB["file_system"][file2_path]
#         dehydrate_file_system_to_common_directory()
        
#         # Step 7: Now the file should be properly deleted from common directory
#         assert os.path.exists(file1_path), "File 1 should still exist"
#         assert not os.path.exists(file2_path), "File 2 should now be deleted from common directory"
#         assert os.path.exists(new_file_path), "New file should still exist"
        
#         # Step 8: Use wrapped function again to verify the deletion persists
#         files_after_deletion = list_directory(self.temp_dir)
#         file_names = [f["name"] for f in files_after_deletion]
#         assert "will_remain.txt" in file_names
#         assert "will_be_deleted.txt" not in file_names, "Deleted file should not appear in list"
#         assert "new_file.txt" in file_names 