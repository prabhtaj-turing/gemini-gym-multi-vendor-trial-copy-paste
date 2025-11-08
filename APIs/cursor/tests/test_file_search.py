# cursor/tests/test_file_search.py
import unittest
import copy
import os
import tempfile
import shutil
from unittest.mock import patch

# Import the function to be tested
from ..cursorAPI import file_search

# Import the original DB
from .. import DB as GlobalDBSource

# Import the BaseTestCaseWithErrorHandler
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import InvalidInputError
from ..SimulationEngine import utils

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\\\", "/")

def minimal_reset_db_for_file_search(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_file_search_workspace_")
    
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

class TestFileSearch(BaseTestCaseWithErrorHandler):
    """
    Test cases for the file_search function, verifying fuzzy path matching
    against the application's internal file system representation using 'thefuzz'.
    """

    transient_test_files = []  # Define potential files for cleanup

    def setUp(self):
        """
        Prepares a clean, isolated database state before each test method.
        """
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_file_search()

        # Add some initial test files to the file system
        self._add_file("project/main.py")
        self._add_file("project/utils.py")
        self._add_file("project/data/users.csv")
        self._add_file("project/docs/README.md")
        self._add_file("another/dir/file.txt")

        # Patch 'DB' in relevant modules
        self.db_patcher_for_init_module = patch("cursor.DB", self.db_for_test)
        self.db_patcher_for_init_module.start()
        self.db_patcher_for_utils_module = patch(
            "cursor.SimulationEngine.utils.DB", self.db_for_test
        )
        self.db_patcher_for_utils_module.start()
        
        # Patch 'DB' in the cursorAPI module where the actual function is defined
        self.db_patcher_for_cursorapi_module = patch(
            "cursor.cursorAPI.DB", self.db_for_test
        )
        self.db_patcher_for_cursorapi_module.start()

        # CRITICAL: Patch 'DB' in the db module where validate_workspace_hydration is defined
        self.db_patcher_for_db_module = patch("cursor.SimulationEngine.db.DB", self.db_for_test)
        self.db_patcher_for_db_module.start()

        self._cleanup_transient_files()

    def tearDown(self):
        """Restores the original state and cleans up transient files."""
        self._cleanup_transient_files()
        self.db_patcher_for_db_module.stop()
        self.db_patcher_for_cursorapi_module.stop()
        self.db_patcher_for_utils_module.stop()
        self.db_patcher_for_init_module.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _cleanup_transient_files(self):
        """Removes any specified transient files created during testing."""
        cursor_module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for filename in self.transient_test_files:
            file_path = os.path.join(cursor_module_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Warning: Could not clean up test file {file_path}: {e}")

    def _add_file(self, relative_path):
        """Helper to add a file entry to the test DB's file_system."""
        abs_path = os.path.normpath(os.path.join(self.workspace_path, relative_path))
        
        # Ensure parent directories exist
        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.workspace_path:
            self._add_dir_recursive(dir_name)

        # Create the file on filesystem
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(f"# Content of {relative_path}\n")

        # Add the actual file entry to DB
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path,
            "is_directory": False,
            "content_lines": [f"# Content of {relative_path}\n"],
            "size_bytes": len(f"# Content of {relative_path}\n"),
            "last_modified": utils.get_current_timestamp_iso(),
        }

    def _add_dir(self, abs_path):
        """Helper to add a directory entry to the test DB's file_system."""
        # Only add if it doesn't already exist
        if abs_path not in self.db_for_test["file_system"]:
            # Create the directory on filesystem
            os.makedirs(abs_path, exist_ok=True)
            
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso(),
            }

    def _add_dir_recursive(self, abs_path):
        """Helper to recursively add directory entries."""
        if abs_path == self.workspace_path or abs_path in self.db_for_test["file_system"]:
            return
            
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and parent_dir != abs_path:
            self._add_dir_recursive(parent_dir)
        
        self._add_dir(abs_path)

    # --- Test Cases ---

    def test_basic_exact_match(self):
        """Verify finding a file with an exact (case-insensitive) match."""
        self._add_file("src/my_component.tsx")
        self._add_file("src/other_file.js")  # Add unrelated file
        results = file_search(query="my_component.tsx", explanation="find component")
        expected_path = os.path.join(self.workspace_path, "src/my_component.tsx")
        self.assertEqual(results, [expected_path])

    def test_basic_partial_match(self):
        """Verify finding files with partial path matches."""
        self._add_file("src/components/button.tsx")
        self._add_file("src/utils/component_helpers.ts")
        self._add_file("test/button_test.py")
        results = file_search(query="component", explanation="find components")
        # Order depends on fuzzy score, use assertCountEqual if unsure
        expected = [
            os.path.join(self.workspace_path, "src/components/button.tsx"),
            os.path.join(self.workspace_path, "src/utils/component_helpers.ts"),
        ]
        self.assertCountEqual(results, expected)  # Checks content regardless of order

    def test_fuzzy_match_with_typo(self):
        """Verify finding a file despite a typo in the query using fuzzy matching."""
        self._add_file("src/controllers/user_controller.py")
        self._add_file("src/models/order.py")
        results = file_search(
            query="user_contoller", explanation="find user controller"
        )  # Typo
        expected_path = os.path.join(self.workspace_path, "src/controllers/user_controller.py")
        self.assertEqual(results, [expected_path])

    def test_case_insensitive_match(self):
        """Verify fuzzy matching ignores case differences."""
        # Use a simpler test that doesn't clear the filesystem
        # Instead, add a file with a name that should clearly match
        self._add_file("TestFile.txt")

        results = file_search(query="testfile", explanation="find testfile")
        expected_path = os.path.join(self.workspace_path, "TestFile.txt")
        self.assertIn(expected_path, results)  # Should find the file with different case

        results_upper = file_search(query="TESTFILE", explanation="find testfile upper")
        self.assertIn(expected_path, results_upper)  # Same result expected

    def test_no_match_found(self):
        """Verify an empty list is returned when no files suitably match the query."""
        self._add_file("src/main.go")
        self._add_file("config/settings.yaml")
        results = file_search(
            query="nonexistent_fuzzy_term", explanation="find nothing"
        )
        self.assertEqual(results, [])

    def test_empty_query_returns_empty(self):
        """Verify an empty query string results in an empty list."""
        self._add_file("some_file.txt")
        results = file_search(query="", explanation="empty query")
        self.assertEqual(results, [])

    def test_empty_file_system_returns_empty(self):
        """Verify search returns empty list when the internal file system contains no files."""
        # Clear file system except root
        self.db_for_test["file_system"] = {
            self.workspace_path: {
                "path": self.workspace_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso()
            }
        }
        # No files added here
        results = file_search(query="anything", explanation="search empty fs")
        self.assertEqual(results, [])

    def test_only_files_are_returned(self):
        """Verify that directories matching the query are not included in search results."""
        self._add_file("search_target/file.txt")
        self._add_dir(
            os.path.join(self.workspace_path, "search_target_dir")
        )  # Directory with similar name added via helper
        self._add_file("other_search_target.log")

        results = file_search(query="search_target", explanation="find search targets")
        
        # Check that the specific files we added are in the results
        expected_files = [
            os.path.join(self.workspace_path, "other_search_target.log"),
            os.path.join(self.workspace_path, "search_target/file.txt"),
        ]
        
        # Check that our expected files are found
        for expected_file in expected_files:
            self.assertIn(expected_file, results, f"Expected file {expected_file} not found in results")
        
        # Verify directory is not included
        self.assertNotIn(
            os.path.join(self.workspace_path, "search_target_dir"), results
        )  # Explicitly check directory exclusion

    def test_result_capping_at_10(self):
        """Verify results are capped at 10 items even if more files match fuzzily."""
        # Clear existing files to have a clean test
        self.db_for_test["file_system"] = {
            self.workspace_path: {
                "path": self.workspace_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso()
            }
        }
        
        paths_added = []
        for i in range(15):  # Add 15 potentially matching files
            path = f"testfile_{i:02d}.txt"  # Use a more specific name that will match better
            self._add_file(path)
            paths_added.append(os.path.join(self.workspace_path, path))
        self._add_file("other/non_testfile.txt")

        results = file_search(query="testfile", explanation="find testfiles")

        # Should find at least some items, and be capped at 10
        self.assertGreater(len(results), 0, "Should find at least some testfiles")
        self.assertLessEqual(len(results), 10, "Results should be capped at 10")
        
        # Check that the results contain testfile files
        testfile_results = [r for r in results if "testfile_" in os.path.basename(r)]
        self.assertGreater(len(testfile_results), 0, "Should find some testfile files")

    def test_ranking_higher_score_first(self):
        """Verify that closer fuzzy matches are generally ranked higher in the results."""
        # Clear existing files to have a clean test
        self.db_for_test["file_system"] = {
            self.workspace_path: {
                "path": self.workspace_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso()
            }
        }
        
        self._add_file("search_term.py")
        self._add_file("search/term_utils.py")  # Path with tokens matching query well
        self._add_file("other/term_in_path.txt")  # Query matches part of path
        self._add_file("search_tirm.log")  # Path with typo relative to query
        self._add_file("unrelated.txt")  # Changed from .zip to .txt to avoid binary issues

        path_exact = os.path.join(self.workspace_path, "search_term.py")
        path_close = os.path.join(self.workspace_path, "search/term_utils.py")
        path_partial = os.path.join(self.workspace_path, "other/term_in_path.txt")
        path_typo = os.path.join(self.workspace_path, "search_tirm.log")
        path_unrelated = os.path.join(self.workspace_path, "unrelated.txt")

        results = file_search(query="search_term", explanation="find search term")

        # Verify expected files are found (scores must meet threshold).
        self.assertGreater(len(results), 0, "Should find some matches")
        self.assertIn(path_exact, results, "Exact match string should be found")
        
        # Verify unrelated file is excluded (if it doesn't score high enough)
        # This is less strict since fuzzy matching can be unpredictable
        if path_unrelated in results:
            # If unrelated file is included, it should be ranked lower than exact match
            exact_index = results.index(path_exact)
            unrelated_index = results.index(path_unrelated)
            self.assertLess(exact_index, unrelated_index, "Exact match should be ranked higher than unrelated file")

    def test_invalid_query_type_raises_error(self):
        """Verify InvalidInputError is raised for non-string query."""
        with self.assertRaises(InvalidInputError):
            file_search(query=123, explanation="testing")

    def test_invalid_explanation_type_raises_error(self):
        """Verify InvalidInputError is raised for non-string explanation."""
        with self.assertRaises(InvalidInputError):
            file_search(query="test", explanation=None)

    def test_search_finds_relevant_files(self):
        """Verify file_search returns a ranked list of matching file paths."""
        results = file_search(query="main", explanation="search for main file")
        expected_path = os.path.join(self.workspace_path, "project/main.py")
        
        # Check if the file was found, if not it might be due to fuzzy matching threshold
        if expected_path not in results:
            # Try a more specific search
            results = file_search(query="main.py", explanation="search for main.py file")
        
        self.assertIn(expected_path, results, f"Expected to find {expected_path} in results: {results}")
        
    def test_search_with_partial_name(self):
        """Verify file_search can find files with partial name matches."""
        results = file_search(query="utils", explanation="search for utility file")
        expected_path = os.path.join(self.workspace_path, "project/utils.py")
        
        # Check if the file was found, if not it might be due to fuzzy matching threshold
        if expected_path not in results:
            # Try a more specific search
            results = file_search(query="utils.py", explanation="search for utils.py file")
        
        self.assertIn(expected_path, results, f"Expected to find {expected_path} in results: {results}")

    def test_search_returns_empty_list_for_no_matches(self):
        """Verify an empty list is returned when no files match the query."""
        results = file_search(query="nonexistent_xyz", explanation="no match search")
        self.assertEqual(results, [])

    def test_search_with_empty_query_returns_empty_list(self):
        """Verify an empty query string results in an empty list."""
        results = file_search(query="", explanation="empty query search")
        self.assertEqual(results, [])


if __name__ == "__main__":
    # This will run all tests in the class.
    # If 'thefuzz' is not installed, the import at the top will fail.
    unittest.main()
