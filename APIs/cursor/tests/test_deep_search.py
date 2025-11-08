# cursor/tests/test_deep_search.py

import unittest
import copy
import os
import tempfile
import shutil
import subprocess
import pytest

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..cursorAPI import deep_search
from .. import DB
from ..SimulationEngine import utils
from ..SimulationEngine.qdrant_config import GeminiEmbeddingFunction
from ..SimulationEngine.llm_interface import GEMINI_API_KEY_FROM_ENV
from ..SimulationEngine.custom_errors import InvalidInputError

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\\\", "/")

def minimal_reset_db_for_deep_search(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    DB.clear()
    
    # Create a temporary directory if no path provided
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_deep_search_workspace_")
    
    # Normalize workspace path
    workspace_path_for_db = normalize_for_db(workspace_path_for_db)
    
    # Initialize common directory to match workspace path
    utils.update_common_directory(workspace_path_for_db)
    
    DB["workspace_root"] = workspace_path_for_db
    DB["cwd"] = workspace_path_for_db
    DB["file_system"] = {}
    DB["last_edit_params"] = None
    DB["background_processes"] = {}
    DB["_next_pid"] = 1

    # Create root directory entry
    DB["file_system"][workspace_path_for_db] = {
        "path": workspace_path_for_db,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso()
    }
    
    return workspace_path_for_db

GEMINI_API_KEY_IS_AVAILABLE = bool(GEMINI_API_KEY_FROM_ENV)

# --- Base Test Class ---
class BaseDeepSearchTest(BaseTestCaseWithErrorHandler):
    """Base class for deep search tests, handles model loading check."""
    local_model_loaded = False

    @classmethod
    def setUpClass(cls):
        """Checks if the local Sentence Transformer model loaded once per class."""
        if not cls.local_model_loaded:
            cls.local_model_loaded = GeminiEmbeddingFunction._model_instance is not None
            if not cls.local_model_loaded:
                try:
                    print("\nAttempting to load SentenceTransformer model for tests...")
                    _ = GeminiEmbeddingFunction()
                    cls.local_model_loaded = GeminiEmbeddingFunction._model_instance is not None
                    print("Model loaded successfully." if cls.local_model_loaded else "Model instance still None.")
                except Exception as e:
                    print(f"\nWARNING: Failed to load local SentenceTransformer model: {e}")
                    cls.local_model_loaded = False
            if not cls.local_model_loaded: print("\nWARNING: Model failed to load. Tests will be skipped.")

    def setUp(self):
        """Creates a fresh temporary workspace for each test."""
        self.workspace_path = minimal_reset_db_for_deep_search()
        
        # Create a mock file structure for testing
        self._create_mock_file_structure()

    def tearDown(self):
        """Clean up temporary workspace after each test."""
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _create_mock_file_structure(self):
        """Create a mock file structure for testing."""
        # Create README.md
        readme_path = os.path.join(self.workspace_path, "README.md")
        readme_content = [
            "# My Project\n",
            "\n",
            "This is an amazing project that does amazing things.\n",
            "It contains various components and utilities.\n"
        ]
        
        # Create the file on the filesystem
        with open(readme_path, 'w') as f:
            f.writelines(readme_content)
        
        # Create src directory
        src_dir = os.path.join(self.workspace_path, "src")
        os.makedirs(src_dir, exist_ok=True)
        
        # Create main.py
        main_py_path = os.path.join(src_dir, "main.py")
        main_py_content = [
            "#!/usr/bin/env python3\n",
            "\n",
            "def main():\n",
            "    print('Starting application...')\n",
            "    # Application startup logic\n",
            "    return None\n",
            "\n",
            "if __name__ == '__main__':\n",
            "    main()\n"
        ]
        
        # Create the file on the filesystem
        with open(main_py_path, 'w') as f:
            f.writelines(main_py_content)
        
        # Create utils.py
        utils_py_path = os.path.join(src_dir, "utils.py")
        utils_py_content = [
            "def helper_function():\n",
            "    \"\"\"A helper utility function.\"\"\"\n",
            "    print('Executing helper function')\n",
            "    return True\n"
        ]
        
        # Create the file on the filesystem
        with open(utils_py_path, 'w') as f:
            f.writelines(utils_py_content)


    def assertSnippetProperties(self, snippet):
        """Asserts that a result snippet has the expected structure and types."""
        self.assertIsInstance(snippet, dict, "Snippet should be a dictionary.")
        self.assertIn("file_path", snippet)
        self.assertIsInstance(snippet["file_path"], str)
        self.assertTrue(snippet["file_path"], "File path should not be empty")
        self.assertIn("snippet_bounds", snippet)
        self.assertIsInstance(snippet["snippet_bounds"], str)
        bounds_parts = snippet["snippet_bounds"].split(':')
        self.assertEqual(len(bounds_parts), 2, f"Bounds format error: {snippet['snippet_bounds']}")
        self.assertTrue(bounds_parts[0].isdigit() and bounds_parts[1].isdigit(), f"Bounds parts not digits: {snippet['snippet_bounds']}")
        start_line, end_line = int(bounds_parts[0]), int(bounds_parts[1])
        self.assertTrue(1 <= start_line <= end_line, f"Bounds logical error: {start_line}-{end_line}")
        self.assertIn("snippet_content", snippet)
        self.assertIsInstance(snippet["snippet_content"], str)
        # Check line counts with tolerance
        content_lines = snippet["snippet_content"].split('\n') if snippet["snippet_content"] else []
        num_lines_in_content = len(content_lines)
        if num_lines_in_content == 1 and content_lines[0] == '':
            num_lines_in_content = 0
        expected_lines = end_line - start_line + 1
        if expected_lines == 1:
            self.assertIn(num_lines_in_content, [1, 2], f"Line count mismatch for single line snippet: bounds {expected_lines}, content {num_lines_in_content}")
        else:
            self.assertAlmostEqual(num_lines_in_content, expected_lines, delta=1, msg=f"Line count mismatch: bounds {expected_lines}, content {num_lines_in_content}")


# --- Tests using the Mock DB ---
class TestDeepSearchMockDB(BaseDeepSearchTest):
    """Tests deep_search using the predefined mock database state."""

    def test_missing_workspace_root(self):
        """Tests that deep_search raises ValueError if workspace_root is missing."""
        DB.clear()
        # Also clear the common directory to ensure clean state
        if hasattr(utils, 'COMMON_DIRECTORY'):
            utils.COMMON_DIRECTORY = None
        # Now raises WorkspaceNotHydratedError due to validation before ValueError
        from ..SimulationEngine.custom_errors import WorkspaceNotHydratedError
        self.assertRaises(WorkspaceNotHydratedError, deep_search, query="test")

    def test_query_validation(self):
        """Tests the input validation rules for the query parameter."""
        # Test empty string
        self.assertRaisesRegex(InvalidInputError, "Query cannot be empty", deep_search, query="")
        
        # Test whitespace only
        self.assertRaisesRegex(InvalidInputError, "Query cannot be empty", deep_search, query="   ")
        self.assertRaisesRegex(InvalidInputError, "Query cannot be empty", deep_search, query="\t\n")
        
        # Test too short query
        self.assertRaisesRegex(InvalidInputError, "Query must be at least 3 characters", deep_search, query="ab")
        
        # Test too long query
        long_query = "a" * 1001
        self.assertRaisesRegex(InvalidInputError, "Query must not exceed 1000 characters", deep_search, query=long_query)
        
        # Test query with only special characters
        self.assertRaisesRegex(InvalidInputError, "Query must contain at least one alphanumeric character", 
                              deep_search, query="!@#$%^&*()")
        self.assertRaisesRegex(InvalidInputError, "Query must contain at least one alphanumeric character", 
                              deep_search, query="...")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_no_matches_found(self):
        """Tests that a highly dissimilar query yields very few or no results."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        query = "quantum entanglement banana bread recipe"
        results = deep_search(query=query)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 1, "Expected <= 1 result for dissimilar query.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_semantic_distinction_variation(self):
        """Tests if distinct queries retrieve different concepts more prominently (relaxed)."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        semantic_test_path = os.path.join(self.workspace_path, "src", "semantic_test.py")
        
        # Create the semantic test file on the filesystem
        semantic_test_content = [
            "// data processing and analytics.\n", # Line 1
            "function processData(d) {\n",        # Line 2
            "   // analysis logic here\n",        # Line 3
            "}\n",                                # Line 4
            "// user interface elements.\n",       # Line 5
            "function updateUI(u) {\n",           # Line 6
            "   // update display logic\n",       # Line 7
            "}\n"                                 # Line 8
        ]
        
        # Create the file on the filesystem
        with open(semantic_test_path, 'w') as f:
            f.writelines(semantic_test_content)
        
        # Add the test file to the DB
        DB["file_system"][semantic_test_path] = {
            "path": semantic_test_path,
            "is_directory": False,
            "content_lines": semantic_test_content,
            "size_bytes": utils.calculate_size_bytes(semantic_test_content),
            "last_modified": "2025-05-07T00:00:00Z"
        }

        # Use slightly more specific queries
        query_data = "function for processing data"
        results_data = deep_search(query=query_data)
        query_ui = "function for updating user interface"
        results_ui = deep_search(query=query_ui)

        # Check data query results: Ensure *some* result comes from the test file
        data_results_from_file = [s for s in results_data if s["file_path"] == semantic_test_path]
        self.assertTrue(len(data_results_from_file) >= 1,
                        f"Expected at least one result from {semantic_test_path} for data query.")

        # Check UI query results: Ensure *some* result comes from the test file
        ui_results_from_file = [s for s in results_ui if s["file_path"] == semantic_test_path]
        self.assertTrue(len(ui_results_from_file) >= 1,
                        f"Expected at least one result from {semantic_test_path} for UI query.")

        if results_data:
            self.assertIn("processData", results_data[0]["snippet_content"], "Top data result should mention processData")
        if results_ui:
            self.assertIn("updateUI", results_ui[0]["snippet_content"], "Top UI result should mention updateUI")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_empty_query_string(self):
        """Tests that an empty query raises InvalidInputError with the correct message."""
        with self.assertRaises(InvalidInputError) as cm:
            deep_search(query="")
        self.assertEqual(str(cm.exception), "Query cannot be empty or contain only whitespace")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_empty_file(self):
        """Tests that searching when an empty file exists doesn't cause errors or results from it."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        empty_file_path = os.path.join(self.workspace_path, "empty.txt")
        
        # Create empty file on filesystem
        with open(empty_file_path, 'w') as f:
            pass  # Create empty file
        
        # Add to DB
        DB["file_system"][empty_file_path] = {"path": empty_file_path, "is_directory": False, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-08T00:00:00Z"}
        
        query = "anything"
        results = deep_search(query=query)
        self.assertIsInstance(results, list)
        empty_file_results = [r for r in results if r["file_path"] == empty_file_path]
        self.assertEqual(len(empty_file_results), 0, "Expected no results from empty file.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_whitespace_only_file(self):
        """Tests that searching when a whitespace-only file exists doesn't cause errors or results from it."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        ws_file_path = os.path.join(self.workspace_path, "whitespace.txt")
        ws_content = ["\n", "  \n", "\t\n"]
        
        # Create whitespace file on filesystem
        with open(ws_file_path, 'w') as f:
            f.writelines(ws_content)
        
        # Add to DB
        DB["file_system"][ws_file_path] = {"path": ws_file_path, "is_directory": False, "content_lines": ws_content, "size_bytes": 5, "last_modified": "2025-05-08T00:00:00Z"}
        
        query = "find this"
        results = deep_search(query=query)
        self.assertIsInstance(results, list)
        ws_file_results = [r for r in results if r["file_path"] == ws_file_path]
        self.assertEqual(len(ws_file_results), 0, "Expected no results from whitespace-only file.")

# --- Tests using a Cloned Real Repository ---
@unittest.skipIf("SKIP_REAL_REPO_TESTS" in os.environ, "Skipping real repo tests")
class TestDeepSearchRealRepo(BaseDeepSearchTest):
    """Tests deep_search using a cloned external repository."""
    repo_url = "https://github.com/ahmedradwan21/Small-Online-Shop.git"
    temp_repo_dir = None
    repo_cloned_successfully = False
    hydrated_item_count = 0 # Store count after hydration

    @classmethod
    def setUpClass(cls):
        """Clones the repository into a temporary directory once for the class."""
        super().setUpClass()
        if not cls.local_model_loaded: raise unittest.SkipTest("Local embedding model not loaded.")
        cls.temp_repo_dir = tempfile.mkdtemp(prefix="test_repo_")
        print(f"\nCloning {cls.repo_url} into {cls.temp_repo_dir}...")
        try:
            git_executable = shutil.which("git")
            if not git_executable: raise FileNotFoundError("'git' command not found.")
            subprocess.run([git_executable, "clone", "--depth", "1", cls.repo_url, cls.temp_repo_dir], capture_output=True, text=True, timeout=120, check=True)
            print("Clone successful.")
            cls.repo_cloned_successfully = True
        except Exception as e:
            print(f"ERROR cloning repository: {e}")
            cls.repo_cloned_successfully = False
            if os.path.exists(cls.temp_repo_dir): shutil.rmtree(cls.temp_repo_dir)
            cls.temp_repo_dir = None

    @classmethod
    def tearDownClass(cls):
        """Removes the temporary directory after all tests in the class run."""
        if cls.temp_repo_dir and os.path.exists(cls.temp_repo_dir):
            print(f"\nCleaning up temporary repository: {cls.temp_repo_dir}")
            def onerror(func, path, exc_info): print(f"Error removing {path}: {exc_info[1]}")
            shutil.rmtree(cls.temp_repo_dir, onerror=onerror)

    def setUp(self):
        """Hydrates DB from the cloned repo once for the class if not already done."""
        if not self.repo_cloned_successfully: self.skipTest("Repo cloning failed/skipped.")
        # Hydrate only once per class run
        if TestDeepSearchRealRepo.hydrated_item_count <= 0: # Check if not hydrated or failed
             # Create a fresh workspace for the real repo test
             self.workspace_path = self.temp_repo_dir
             utils.update_common_directory(self.workspace_path)
             DB.clear()
             DB["workspace_root"] = self.workspace_path
             DB["cwd"] = self.workspace_path
             DB["file_system"] = {}
             DB["last_edit_params"] = None
             DB["background_processes"] = {}
             DB["_next_pid"] = 1
             
             print(f"Hydrating DB from cloned repo: {self.temp_repo_dir}")
             try:
                 success = utils.hydrate_db_from_directory(DB, self.temp_repo_dir)
                 if not success: raise RuntimeError("Hydration returned False.")
                 TestDeepSearchRealRepo.hydrated_item_count = len(DB.get('file_system',{}))
                 print(f"Hydration complete. Found {TestDeepSearchRealRepo.hydrated_item_count} items.")
                 if TestDeepSearchRealRepo.hydrated_item_count == 0:
                      print("WARNING: Hydration resulted in 0 items. Real repo tests might not be meaningful.")
             except Exception as e:
                 print(f"ERROR during hydration: {e}")
                 TestDeepSearchRealRepo.hydrated_item_count = -1 # Mark as failed
                 self.fail(f"Setup failed: Could not hydrate DB: {e}")
        elif TestDeepSearchRealRepo.hydrated_item_count < 0:
             self.fail("Hydration failed in previous setup.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_real_repo_product_related(self):
        """Tests searching for product terms in the hydrated repo content."""
        if TestDeepSearchRealRepo.hydrated_item_count <= 0:
            self.skipTest("Hydration failed or yielded 0 items.")
        query = "product price"
        results = deep_search(query=query)
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0, f"Expected > 0 results for query '{query}' in the hydrated repo.")
        found_relevant_term = any(term in s["snippet_content"].lower() for s in results for term in ["price", "product", "item", "cost", "amount", "total"])
        self.assertTrue(found_relevant_term, f"Expected at least one snippet with product/price terms for query '{query}'.")


if __name__ == "__main__":
    unittest.main()
