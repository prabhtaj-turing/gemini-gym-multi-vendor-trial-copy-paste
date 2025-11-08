# cursor/tests/test_list_dir.py
import unittest
import copy
import os
import tempfile
import shutil
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotHydratedError

# Import the function to be tested from cursorAPI
from ..cursorAPI import list_dir

# Import the original DB to create fresh copies for each test run
from .. import DB as GlobalDBSource
from ..SimulationEngine import utils

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\", "/")

def minimal_reset_db_for_list_dir(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_list_dir_workspace_")
    
    # Normalize workspace path
    workspace_path_for_db = normalize_for_db(workspace_path_for_db)
    
    # Initialize common directory to match workspace path
    utils.update_common_directory(workspace_path_for_db)
    
    db_state = {
        "workspace_root": workspace_path_for_db,
        "cwd": workspace_path_for_db,
        "file_system": {},
        "last_edit_params": None,
        "background_processes": {},
        "_next_pid": 1
    }

    # Create root directory entry
    db_state["file_system"][workspace_path_for_db] = {
        "path": workspace_path_for_db,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso()
    }
    
    return workspace_path_for_db, db_state


class TestListDir(BaseTestCaseWithErrorHandler):
    """
    Test cases for the list_dir function, which lists directory contents
    based on the application's internal file system representation.
    """

    # Define filenames that might be created by functions under test, for cleanup.
    transient_test_files = [
        "test_db.json",
        "test_persistence.json",
        "test_state.json",
    ]  # Example

    def setUp(self):
        """
        Prepares a clean, isolated database state before each test method.
        This involves creating a deep copy of the original database structure and
        patching the DB object used by the application modules to point to this copy.
        """
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_list_dir()

        # Patch 'DB' directly in the module where 'list_dir' is defined ('cursor.cursorAPI')
        self.db_patcher_for_cursorapi_module = patch("cursor.cursorAPI.DB", self.db_for_test)
        self.db_patcher_for_cursorapi_module.start()

        # Also patch 'DB' in the 'utils' module, in case list_dir calls utility
        # functions that access the DB.
        self.db_patcher_for_utils_module = patch(
            "cursor.SimulationEngine.utils.DB", self.db_for_test
        )
        self.db_patcher_for_utils_module.start()

        # Patch 'DB' in the init module for consistency
        self.db_patcher_for_init_module = patch("cursor.DB", self.db_for_test)
        self.db_patcher_for_init_module.start()

        # CRITICAL: Patch 'DB' in the db module where validate_workspace_hydration is defined
        self.db_patcher_for_db_module = patch("cursor.SimulationEngine.db.DB", self.db_for_test)
        self.db_patcher_for_db_module.start()

        self._cleanup_transient_files()

    def tearDown(self):
        """
        Restores the original state after each test method and cleans up transient files.
        This involves stopping the DB patchers.
        """
        self._cleanup_transient_files()
        self.db_patcher_for_db_module.stop()
        self.db_patcher_for_init_module.stop()
        self.db_patcher_for_utils_module.stop()
        self.db_patcher_for_cursorapi_module.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _cleanup_transient_files(self):
        """
        Removes any specified transient files that might have been created.
        The path is constructed relative to the main project directory structure.
        """
        # __file__ is '.../APIs/cursor/tests/test_list_dir.py'
        # os.path.dirname(os.path.dirname(__file__)) is '.../APIs/cursor/'
        cursor_module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        for filename in self.transient_test_files:
            file_path = os.path.join(cursor_module_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Warning: Could not clean up test file {file_path}: {e}")

    def _add_file_to_mock_db(self, path: str, size_bytes: int = 0, last_modified: str = "T1"):
        """Adds a file to the test DB."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))

        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.workspace_path and dir_name not in self.db_for_test["file_system"]:
            self._add_dir_to_mock_db(dir_name)

        # Create the file on filesystem
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write("test content")  # Simple content to avoid binary detection
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path,
            "is_directory": False,
            "content_lines": ["test content\n"],
            "size_bytes": size_bytes,
            "last_modified": last_modified,
        }
        return abs_path

    def _add_dir_to_mock_db(self, path: str, last_modified: str = "T1"):
        """Adds a directory to the test DB."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))

        if abs_path not in self.db_for_test["file_system"]:
            # Create the directory on filesystem
            os.makedirs(abs_path, exist_ok=True)
            
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": last_modified,
            }
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and parent_dir != abs_path and parent_dir != self.workspace_path and parent_dir not in self.db_for_test["file_system"]:
            self._add_dir_to_mock_db(parent_dir)
        return abs_path

    def _get_expected_item(self, path, name, is_directory, size, modified_timestamp):
        """Helper to consistently create expected dictionary structures for directory items."""
        return {
            "path": path,
            "name": name,
            "is_directory": is_directory,
            "size_bytes": size,
            "last_modified": modified_timestamp,
        }

    def test_list_workspace_root_with_empty_path(self):
        """Verify listing workspace root when relative_workspace_path is an empty string."""
        self._add_file_to_mock_db("file1.txt", size_bytes=10, last_modified="T1")
        self._add_dir_to_mock_db("dir1", last_modified="T2")
        
        # Call list_dir first to trigger hydration
        actual_items = list_dir(relative_workspace_path="")
        
        # Now get the actual values from DB after hydration
        file1_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "file1.txt")]
        dir1_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "dir1")]
        
        expected_items = [
            self._get_expected_item(
                os.path.join(self.workspace_path, "dir1"), 
                "dir1", 
                True, 
                dir1_entry["size_bytes"], 
                dir1_entry["last_modified"]
            ),
            self._get_expected_item(
                os.path.join(self.workspace_path, "file1.txt"), 
                "file1.txt", 
                False, 
                file1_entry["size_bytes"], 
                file1_entry["last_modified"]
            ),
        ]
        self.assertCountEqual(actual_items, expected_items)

    def test_list_workspace_root_with_dot_path(self):
        """Verify listing workspace root when relative_workspace_path is '.'."""
        self._add_file_to_mock_db("another.log", size_bytes=20, last_modified="T3")
        
        # Call list_dir first to trigger hydration
        actual_items = list_dir(relative_workspace_path=".")
        
        # Now get the actual values from DB after hydration
        file_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "another.log")]
        
        expected_items = [
            self._get_expected_item(
                os.path.join(self.workspace_path, "another.log"), 
                "another.log", 
                False, 
                file_entry["size_bytes"], 
                file_entry["last_modified"]
            ),
        ]
        self.assertCountEqual(actual_items, expected_items)

    def test_list_valid_subdirectory(self):
        """Verify listing contents of a valid subdirectory."""
        self._add_dir_to_mock_db("src", last_modified="T1")
        self._add_file_to_mock_db("src/main.py", size_bytes=100, last_modified="T2")
        self._add_dir_to_mock_db("src/components_dir", last_modified="T3")
        self._add_file_to_mock_db("README.md", size_bytes=50, last_modified="T4")
        
        # Call list_dir first to trigger hydration
        actual_items = list_dir(relative_workspace_path="src")
        
        # Now get the actual values from DB after hydration
        main_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "src/main.py")]
        comp_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "src/components_dir")]
        
        expected_items = [
            self._get_expected_item(
                os.path.join(self.workspace_path, "src/components_dir"), 
                "components_dir", 
                True, 
                comp_entry["size_bytes"], 
                comp_entry["last_modified"]
            ),
            self._get_expected_item(
                os.path.join(self.workspace_path, "src/main.py"), 
                "main.py", 
                False, 
                main_entry["size_bytes"], 
                main_entry["last_modified"]
            ),
        ]
        self.assertCountEqual(actual_items, expected_items)

    def test_list_empty_directory_returns_empty_list(self):
        """Verify listing an existing but empty directory returns an empty list."""
        self._add_dir_to_mock_db("empty_folder", last_modified="T1")
        # Add a file in a subdirectory to make sure we only get direct children
        # Note: We should NOT add the subdirectory itself to the empty_folder
        # since we want empty_folder to be empty
        self._add_dir_to_mock_db("empty_folder/sub")
        self._add_file_to_mock_db("empty_folder/sub/file.txt", last_modified="T2")
        
        # Remove the subdirectory from the empty_folder to make it truly empty
        # We need to remove it from the DB after creating it
        sub_path = os.path.join(self.workspace_path, "empty_folder/sub")
        if sub_path in self.db_for_test["file_system"]:
            del self.db_for_test["file_system"][sub_path]
        
        # Also remove the file from the sub directory
        file_path = os.path.join(self.workspace_path, "empty_folder/sub/file.txt")
        if file_path in self.db_for_test["file_system"]:
            del self.db_for_test["file_system"][file_path]
        
        # Remove the sub directory from filesystem too
        import shutil
        if os.path.exists(sub_path):
            shutil.rmtree(sub_path)
        
        actual_items = list_dir(relative_workspace_path="empty_folder")
        self.assertEqual(actual_items, [])

    def test_list_nonexistent_directory_raises_file_not_found_error(self):
        """Verify listing a non-existent directory path raises FileNotFoundError."""
        # No specific file system setup needed, as the path won't be found.
        with self.assertRaises(FileNotFoundError):
            list_dir(relative_workspace_path="folder_does_not_exist")

    def test_list_path_that_is_a_file_raises_not_a_directory_error(self):
        """Verify listing a path that points to a file raises NotADirectoryError."""
        self._add_file_to_mock_db("config.ini", size_bytes=10, last_modified="T1")
        
        with self.assertRaises(NotADirectoryError):
            list_dir(relative_workspace_path="config.ini")

    def test_list_only_direct_children_are_listed(self):
        """Verify that only direct children of the specified directory are listed, not grandchildren."""
        self._add_dir_to_mock_db("lib", last_modified="T1")
        self._add_file_to_mock_db("lib/core.js", size_bytes=200, last_modified="T2")
        self._add_dir_to_mock_db("lib/modules", last_modified="T3")
        self._add_file_to_mock_db("lib/modules/parser.js", size_bytes=50, last_modified="T4")
        
        # Call list_dir first to trigger hydration
        actual_items = list_dir(relative_workspace_path="lib")
        
        # Now get the actual values from DB after hydration
        core_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "lib/core.js")]
        modules_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "lib/modules")]
        
        expected_items = [
            self._get_expected_item(
                os.path.join(self.workspace_path, "lib/core.js"), 
                "core.js", 
                False, 
                core_entry["size_bytes"], 
                core_entry["last_modified"]
            ),
            self._get_expected_item(
                os.path.join(self.workspace_path, "lib/modules"), 
                "modules", 
                True, 
                modules_entry["size_bytes"], 
                modules_entry["last_modified"]
            ),
        ]
        self.assertCountEqual(actual_items, expected_items)

    def test_list_path_with_leading_slash_is_handled(self):
        """Verify listing a subdirectory path provided with a leading slash."""
        self._add_dir_to_mock_db("assets", last_modified="T1")
        self._add_file_to_mock_db("assets/image.png", size_bytes=5, last_modified="T2")
        
        # Call list_dir first to trigger hydration
        actual_items = list_dir(relative_workspace_path="/assets")
        
        # Now get the actual values from DB after hydration
        image_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "assets/image.png")]
        
        expected_items = [
            self._get_expected_item(
                os.path.join(self.workspace_path, "assets/image.png"), 
                "image.png", 
                False, 
                image_entry["size_bytes"], 
                image_entry["last_modified"]
            ),
        ]
        self.assertCountEqual(actual_items, expected_items)

    def test_list_path_with_trailing_slash_is_handled(self):
        """Verify listing a subdirectory path provided with a trailing slash."""
        self._add_dir_to_mock_db("docs", last_modified="T1")
        self._add_file_to_mock_db("docs/guide.md", size_bytes=15, last_modified="T2")
        
        # Call list_dir first to trigger hydration
        actual_items = list_dir(relative_workspace_path="docs/")
        
        # Now get the actual values from DB after hydration
        guide_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "docs/guide.md")]
        
        expected_items = [
            self._get_expected_item(
                os.path.join(self.workspace_path, "docs/guide.md"), 
                "guide.md", 
                False, 
                guide_entry["size_bytes"], 
                guide_entry["last_modified"]
            ),
        ]
        self.assertCountEqual(actual_items, expected_items)

    def test_raises_value_error_if_workspace_root_not_configured(self):
        """Verify ValueError is raised if 'workspace_root' is missing from DB configuration."""
        # We need to patch the DB to remove workspace_root BEFORE the decorator runs
        # The @with_common_file_system decorator checks for workspace_root first
        
        # Create a test DB without workspace_root
        invalid_db = {
            "cwd": "/tmp/test",
            "file_system": {},
            "last_edit_params": None,
            "background_processes": {},
            "_next_pid": 1
        }
        
        # Patch the DB to use the invalid state
        with patch("cursor.cursorAPI.DB", invalid_db):
            with self.assertRaisesRegex(ValueError, "Workspace root is not configured"):
                list_dir(relative_workspace_path="src")

    def test_raises_value_error_for_path_outside_workspace(self):
        """Verify ValueError is raised if relative path attempts to navigate outside workspace_root."""
        # This is the key part of the error message we expect from list_dir
        expected_message_substring = "which is outside the permitted workspace"

        with self.assertRaises(ValueError) as cm:
            list_dir(relative_workspace_path="../../sensitive_data")

        actual_exception_message = str(cm.exception)
        is_present = expected_message_substring in actual_exception_message

        self.assertTrue(
            is_present,
            msg=f"Expected substring '{expected_message_substring}' not found in actual message '{actual_exception_message}'",
        )

        # Also verify other parts of the more specific message if needed
        self.assertIn("../../sensitive_data", actual_exception_message)

    def test_list_dir_accepts_explanation_argument(self):
        """Verify that the optional 'explanation' argument is accepted and does not affect results."""
        self._add_file_to_mock_db("data.json", size_bytes=10, last_modified="T1")
        
        # Call list_dir first to trigger hydration
        actual_items = list_dir(
            relative_workspace_path="",
            explanation="User is exploring the root directory.",
        )
        
        # Now get the actual values from DB after hydration
        data_entry = self.db_for_test["file_system"][os.path.join(self.workspace_path, "data.json")]
        
        expected_items = [
            self._get_expected_item(
                os.path.join(self.workspace_path, "data.json"), 
                "data.json", 
                False, 
                data_entry["size_bytes"], 
                data_entry["last_modified"]
            ),
        ]
        self.assertCountEqual(actual_items, expected_items)

    def test_invalid_path_type_raises_invalid_input_error(self):
        """Verify InvalidInputError is raised for non-string path."""
        with self.assertRaises(InvalidInputError):
            list_dir(relative_workspace_path=123)

    def test_invalid_explanation_type_raises_invalid_input_error(self):
        """Verify InvalidInputError is raised for non-string explanation."""
        with self.assertRaises(InvalidInputError):
            list_dir(relative_workspace_path=".", explanation={"desc": "invalid"})

    def test_unhydrated_workspace_raises_workspace_not_hydrated_error(self):
        """Verify WorkspaceNotHydratedError is raised when workspace is not hydrated."""
        # Create an unhydrated DB state
        empty_db = {
            "workspace_root": "",
            "cwd": "",
            "file_system": {},
            "last_edit_params": None,
            "background_processes": {},
            "_next_pid": 1
        }
        
        with patch("cursor.cursorAPI.DB", empty_db):
            with patch("cursor.SimulationEngine.db.DB", empty_db):
                with self.assertRaises(WorkspaceNotHydratedError):
                    list_dir(relative_workspace_path=".")

    def test_partial_hydration_raises_workspace_not_hydrated_error(self):
        """Verify WorkspaceNotHydratedError is raised with partial hydration."""
        # Test with workspace_root but no file_system
        partially_hydrated_db = {
            "workspace_root": "/some/path",
            "cwd": "/some/path", 
            "file_system": {},
            "last_edit_params": None,
            "background_processes": {},
            "_next_pid": 1
        }
        
        with patch("cursor.cursorAPI.DB", partially_hydrated_db):
            with patch("cursor.SimulationEngine.db.DB", partially_hydrated_db):
                with self.assertRaises(WorkspaceNotHydratedError):
                    list_dir(relative_workspace_path=".")


if __name__ == "__main__":
    unittest.main()
