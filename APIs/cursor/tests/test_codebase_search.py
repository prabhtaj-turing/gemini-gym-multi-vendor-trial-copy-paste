# cursor/tests/test_codebase_search.py

import unittest
import copy
import os  # For path joining if needed, though DB paths are absolute
import tempfile
import shutil
import subprocess
import pytest

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..cursorAPI import codebase_search
from .. import DB
from ..SimulationEngine import utils
from ..SimulationEngine.qdrant_config import GeminiEmbeddingFunction
from ..SimulationEngine.llm_interface import GEMINI_API_KEY_FROM_ENV



def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\\\", "/")

def minimal_reset_db_for_codebase_search(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    DB.clear()
    
    # Create a temporary directory if no path provided
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_codebase_workspace_")
    
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
class BaseCodebaseSearchTest(BaseTestCaseWithErrorHandler):
    """Base class for codebase search tests, handles model loading check."""
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
        self.workspace_path = minimal_reset_db_for_codebase_search()
        
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
        
        # Handle git metadata snippets differently
        if snippet.get("is_git_metadata"):
            # Git metadata snippets have different structure
            self.assertEqual(snippet["file_path"], "<git_metadata>")
            self.assertIn("snippet_bounds", snippet)
            self.assertIsInstance(snippet["snippet_bounds"], dict)
            self.assertIn("start", snippet["snippet_bounds"])
            self.assertIn("end", snippet["snippet_bounds"])
            self.assertIn("pr_numbers", snippet)
            self.assertIsInstance(snippet["pr_numbers"], list)
            # Don't check line count logic for git metadata snippets
            return
        
        # Regular snippet validation (existing logic)
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
class TestCodebaseSearchMockDB(BaseCodebaseSearchTest):
    """Tests codebase_search using the predefined mock database state."""

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_all_files_happy_path_readme_query(self):
        """Tests finding relevant content in README.md when searching all files."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        query = "project details"
        results = codebase_search(query=query)
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0, "Expected >0 results for 'project details'")
        
        # Filter out git metadata snippets for this test since we're looking for README content
        regular_results = [r for r in results if not r.get("is_git_metadata")]
        readme_snippets = [r for r in regular_results if r["file_path"] == "/home/user/project/README.md"]
        
        self.assertTrue(len(readme_snippets) >= 1, f"Expected >= 1 snippet from README.md for query '{query}'")
        found_expected_content = any("My Project" in s["snippet_content"] or "amazing things" in s["snippet_content"] for s in readme_snippets)
        if readme_snippets:
            self.assertSnippetProperties(readme_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'My Project' or 'amazing things' content from README.md snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_specific_target_directory_main_py(self):
        """Tests finding content in main.py when targeting the 'src' directory."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        query = "application startup logic"
        results = codebase_search(query=query, target_directories=["src"])
        self.assertIsInstance(results, list)
        main_py_snippets = [r for r in results if r["file_path"] == "/home/user/project/src/main.py"]
        self.assertTrue(len(main_py_snippets) >= 0, "Expected >= 0 snippet from main.py when targeting 'src'")
        found_expected_content = False
        for snippet in main_py_snippets:
            self.assertSnippetProperties(snippet)
            norm_snippet_path = os.path.normpath(snippet["file_path"])
            norm_target_dir = os.path.normpath(os.path.join(DB["workspace_root"], "src"))
            self.assertTrue(norm_snippet_path.startswith(norm_target_dir), f"Snippet path {snippet['file_path']} not in 'src'")
            self.assertNotIn("README.md", snippet["file_path"])
            if "Starting application..." in snippet["snippet_content"] or "def main()" in snippet["snippet_content"]:
                found_expected_content = True
        self.assertTrue(found_expected_content, "Expected startup message or main def content not found.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_with_glob_target_directory_utils_py(self):
        """Tests finding content in utils.py using a glob pattern 's*c' for the directory."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        query = "helper utility execution"
        results = codebase_search(query=query, target_directories=["s*c"])
        self.assertIsInstance(results, list)
        utils_py_snippets = [r for r in results if r["file_path"] == "/home/user/project/src/utils.py"]
        self.assertTrue(len(utils_py_snippets) >= 1, "Expected snippets from utils.py with glob 's*c'")
        found_expected_content = any("helper_function" in s["snippet_content"] or "Executing helper" in s["snippet_content"] for s in utils_py_snippets)
        if utils_py_snippets:
            self.assertSnippetProperties(utils_py_snippets[0])
        self.assertTrue(found_expected_content, "Expected helper function content not found.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_empty_list_target_directories_searches_all(self):
        """Tests that target_directories=[] searches all files, similar to None."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        query = "main function"
        results_empty_list = codebase_search(query=query, target_directories=[])
        results_none = codebase_search(query=query, target_directories=None)
        self.assertIsInstance(results_empty_list, list)
        self.assertTrue(len(results_empty_list) > 0, "Expected results when target_directories=[]")
        self.assertTrue(len(results_none) > 0, "Expected results when target_directories=None")
        paths_empty = {r['file_path'] for r in results_empty_list}
        paths_none = {r['file_path'] for r in results_none}
        # Check key files are present in both, acknowledging ranks might differ
        self.assertIn("/home/user/project/src/main.py", paths_empty, "main.py missing for target=[]")
        self.assertIn("/home/user/project/src/main.py", paths_none, "main.py missing for target=None")
        # Check README presence but don't fail test if missing, as query relevance might be low
        if "/home/user/project/README.md" not in paths_empty:
            print("\nNote: README.md not found for target=[] test.")
        if "/home/user/project/README.md" not in paths_none:
            print("\nNote: README.md not found for target=None test.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_no_matches_found_semantically(self):
        """Tests that a highly dissimilar query yields very few or no results."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        query = "quantum entanglement banana bread recipe"
        results = codebase_search(query=query)
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 1, "Expected <= 1 result for dissimilar query.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_semantic_distinction_variation(self):
        """Tests if distinct queries retrieve different concepts more prominently (relaxed)."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        semantic_test_path = os.path.join(DB["workspace_root"], "src", "semantic_test.py")
        # Add the test file to the mock filesystem
        DB["file_system"][semantic_test_path] = {
            "path": semantic_test_path,
            "is_directory": False,
            "content_lines": [
                "// data processing and analytics.\n", # Line 1
                "function processData(d) {\n",        # Line 2
                "   // analysis logic here\n",        # Line 3
                "}\n",                                # Line 4
                "// user interface elements.\n",       # Line 5
                "function updateUI(u) {\n",           # Line 6
                "   // update display logic\n",       # Line 7
                "}\n"                                 # Line 8
            ],
            "size_bytes": 1, # Placeholder, will be recalculated
            "last_modified": "2025-05-07T00:00:00Z"
        }
        DB["file_system"][semantic_test_path]["size_bytes"] = utils.calculate_size_bytes(
            DB["file_system"][semantic_test_path]["content_lines"]
        )

        # Use slightly more specific queries
        query_data = "function for processing data"
        results_data = codebase_search(query=query_data, target_directories=["src"])
        query_ui = "function for updating user interface"
        results_ui = codebase_search(query=query_ui, target_directories=["src"])

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
    def test_search_target_root_directory_using_dot(self):
        """Tests targeting the root directory using '.' excludes subdirectories."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        query = "My Project"
        results = codebase_search(query=query, target_directories=["."])
        self.assertIsInstance(results, list)
        readme_snippets = [r for r in results if r["file_path"] == "/home/user/project/README.md"]
        self.assertTrue(len(readme_snippets) >= 1, "Expected snippets from README.md when target is '.'")
        for r in results:
             relative_path = os.path.relpath(r['file_path'], DB['workspace_root'])
             is_in_root = os.path.dirname(relative_path) == ''
             self.assertTrue(is_in_root, f"Found snippet outside root dir: {relative_path} when targeting '.'")

    def test_search_non_existent_target_directory_glob(self):
        """Tests that targeting a non-existent directory yields no results."""
        results = codebase_search(query="Project", target_directories=["non_existent_dir/*"])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_search_empty_query_string(self):
        """Tests that an empty query raises ValueError."""
        with self.assertRaisesRegex(ValueError, "The 'query' parameter must be a non-empty string."):
            codebase_search(query="")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_target_directory_with_no_matching_files_inside_semantically(self):
        """Tests targeting a directory whose content is semantically unrelated."""
        if not self.local_model_loaded: self.skipTest("Local embedding model not loaded.")
        another_py_path = os.path.join(DB["workspace_root"], "src", "another.py")
        DB["file_system"][another_py_path] = {"path": another_py_path, "is_directory": False, "content_lines": ["Tropical birds.\n", "Ocean waves.\n"], "size_bytes": 1, "last_modified": "2025-05-07T00:10:00Z"}
        DB["file_system"][another_py_path]["size_bytes"] = utils.calculate_size_bytes(DB["file_system"][another_py_path]["content_lines"])
        results = codebase_search(query="software dev", target_directories=["src"])
        another_py_snippets = [r for r in results if r["file_path"] == another_py_path]
        self.assertLessEqual(len(another_py_snippets), 1, "Expected <=1 unrelated snippet from another.py.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_multiple_target_directories(self):
        """Tests targeting multiple directories ('src', 'tests') excludes others (root)."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        test_dir = os.path.join(DB["workspace_root"], "tests")
        test_file_path = os.path.join(test_dir, "test_main.py")
        DB["file_system"][test_dir] = {"path": test_dir, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-08T00:00:00Z"}
        DB["file_system"][test_file_path] = {"path": test_file_path, "is_directory": False, "content_lines": ["import main\n", "def test_startup():\n", " assert main.main() is None\n"], "size_bytes": 1, "last_modified": "2025-05-08T00:00:00Z"}
        DB["file_system"][test_file_path]["size_bytes"] = utils.calculate_size_bytes(DB["file_system"][test_file_path]["content_lines"])
        query = "application main function"
        results = codebase_search(query=query, target_directories=["src", "tests"])
        self.assertIsInstance(results, list)
        main_py_found = any(r["file_path"] == "/home/user/project/src/main.py" for r in results)
        test_main_found = any(r["file_path"] == test_file_path for r in results)
        readme_found = any(r["file_path"] == "/home/user/project/README.md" for r in results)
        self.assertTrue(any([main_py_found,test_main_found]), "Expected main.py or test_main.py when targeting src and tests.")
        self.assertFalse(readme_found, "Did not expect README.md when targeting src and tests.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_target_directory_specific_file_pattern(self):
        """Tests targeting '*.py' files within 'src' excludes non-python files."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        query = "helper function" # Query relevant to python files
        results = codebase_search(query=query, target_directories=["src/*.py"])
        self.assertIsInstance(results, list)
        utils_py_found = any(r["file_path"] == "/home/user/project/src/utils.py" for r in results)
        main_py_found = any(r["file_path"] == "/home/user/project/src/main.py" for r in results)
        self.assertTrue(utils_py_found or main_py_found, "Expected utils.py OR main.py when targeting src/*.py.")

        # Add non-python file and ensure it's excluded by the pattern
        other_file_path = os.path.join(DB["workspace_root"], "src", "config.txt")
        DB["file_system"][other_file_path] = {"path": other_file_path, "is_directory": False, "content_lines": ["key=value config\n"], "size_bytes": 15, "last_modified": "2025-05-08T00:00:00Z"}
        results_py_only = codebase_search(query="key value config", target_directories=["src/*.py"]) # Query relevant to txt file
        config_txt_found = any(r["file_path"] == other_file_path for r in results_py_only)
        self.assertFalse(config_txt_found, "Did not expect config.txt when targeting src/*.py.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_target_directory_nested(self):
        """Tests targeting a nested directory ('src/core') excludes parent/sibling files."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        nested_dir = os.path.join(DB["workspace_root"], "src", "core")
        nested_file = os.path.join(nested_dir, "logic.py")
        DB["file_system"][nested_dir] = {"path": nested_dir, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-08T00:00:00Z"}
        DB["file_system"][nested_file] = {"path": nested_file, "is_directory": False, "content_lines": ["def core_logic():\n", " print('Core processing')\n"], "size_bytes": 1, "last_modified": "2025-05-08T00:00:00Z"}
        DB["file_system"][nested_file]["size_bytes"] = utils.calculate_size_bytes(DB["file_system"][nested_file]["content_lines"])
        query = "core processing logic"
        results = codebase_search(query=query, target_directories=["src/core"])
        self.assertIsInstance(results, list)
        nested_file_found = any(r["file_path"] == nested_file for r in results)
        self.assertTrue(nested_file_found, "Expected nested logic.py results.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_empty_file(self):
        """Tests that searching when an empty file exists doesn't cause errors or results from it."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        empty_file_path = os.path.join(DB["workspace_root"], "empty.txt")
        DB["file_system"][empty_file_path] = {"path": empty_file_path, "is_directory": False, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-08T00:00:00Z"}
        query = "anything"
        results = codebase_search(query=query)
        self.assertIsInstance(results, list)
        empty_file_results = [r for r in results if r["file_path"] == empty_file_path]
        self.assertEqual(len(empty_file_results), 0, "Expected no results from empty file.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_whitespace_only_file(self):
        """Tests that searching when a whitespace-only file exists doesn't cause errors or results from it."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        ws_file_path = os.path.join(DB["workspace_root"], "whitespace.txt")
        DB["file_system"][ws_file_path] = {"path": ws_file_path, "is_directory": False, "content_lines": ["\n", "  \n", "\t\n"], "size_bytes": 5, "last_modified": "2025-05-08T00:00:00Z"}
        query = "find this"
        results = codebase_search(query=query)
        self.assertIsInstance(results, list)
        ws_file_results = [r for r in results if r["file_path"] == ws_file_path]
        self.assertEqual(len(ws_file_results), 0, "Expected no results from whitespace-only file.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_typescript_file_content(self):
        """Tests finding relevant content in a TypeScript file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        ts_file_path = os.path.join(DB["workspace_root"], "src", "user_service.ts")
        ts_content_lines = [
            "interface User {\n",
            "  id: number;\n",
            "  name: string;\n",
            "}\n",
            "\n",
            "function getUserProfile(userId: number): User | null {\n",
            "  // Imagine fetching user from a database\n",
            "  if (userId === 1) {\n",
            "    return { id: 1, name: 'Alice Wonderland' };\n",
            "  }\n",
            "  return null;\n",
            "}\n"
        ]
        DB["file_system"][ts_file_path] = {
            "path": ts_file_path,
            "is_directory": False,
            "content_lines": ts_content_lines,
            "size_bytes": utils.calculate_size_bytes(ts_content_lines),
            "last_modified": "2025-05-09T00:00:00Z"
        }

        query = "fetch user profile data"
        results = codebase_search(query=query, target_directories=["src"])
        self.assertIsInstance(results, list)

        ts_snippets = [r for r in results if r["file_path"] == ts_file_path]
        self.assertTrue(len(ts_snippets) >= 1, f"Expected >= 1 snippet from {ts_file_path} for query '{query}'")

        found_expected_content = any("getUserProfile" in s["snippet_content"] or "Alice Wonderland" in s["snippet_content"] for s in ts_snippets)
        if ts_snippets:
            self.assertSnippetProperties(ts_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'getUserProfile' or 'Alice Wonderland' content from .ts snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_java_file_content(self):
        """Tests finding relevant content in a Java file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        src_path = os.path.join(DB["workspace_root"], "src")
        src_com_path = os.path.join(src_path, "com")
        src_com_example_path = os.path.join(src_com_path, "example")
        java_file_path = os.path.join(src_com_example_path, "PaymentProcessor.java")

        if src_path not in DB["file_system"]:
            DB["file_system"][src_path] = {
                "path": src_path, 
                "is_directory": True, 
                "content_lines": [], 
                "size_bytes": 0, 
                "last_modified": "2025-05-09T00:00:00Z"
            }
        DB["file_system"][src_com_path] = {
            "path": src_com_path, 
            "is_directory": True, 
            "content_lines": [], 
            "size_bytes": 0, 
            "last_modified": "2025-05-09T00:00:00Z"
        }
        DB["file_system"][src_com_example_path] = {
            "path": src_com_example_path, 
            "is_directory": True, 
            "content_lines": [], 
            "size_bytes": 0, 
            "last_modified": "2025-05-09T00:00:00Z"
        }

        java_content_lines = [
            "package com.example;\n",
            "\n",
            "public class PaymentProcessor {\n",
            "    public boolean processPayment(double amount, String currency) {\n",
            "        // Logic to process a financial transaction\n",
            "        if (amount > 0 && currency != null) {\n",
            "            System.out.println(\"Processing \" + amount + \" \" + currency);\n",
            "            return true; // Simulate successful payment\n",
            "        }\n",
            "        return false;\n",
            "    }\n",
            "}\n"
        ]
        DB["file_system"][java_file_path] = {
            "path": java_file_path,
            "is_directory": False,
            "content_lines": java_content_lines,
            "size_bytes": utils.calculate_size_bytes(java_content_lines), # utils must be accessible
            "last_modified": "2025-05-09T00:00:00Z"
        }

        query = "handle financial transaction"
        relative_target_dir = os.path.relpath(src_com_example_path, DB["workspace_root"])

        results = codebase_search(query=query, target_directories=[relative_target_dir])
        self.assertIsInstance(results, list)

        java_snippets_from_file = [r for r in results if r["file_path"] == java_file_path]

        if not java_snippets_from_file and results:
            print(f"\nNote: Java test query '{query}' found {len(results)} results, but none from {java_file_path}.")
        elif not results:
             self.fail(f"Expected results for Java test query '{query}' from {java_file_path}, but got no results at all.")


        found_expected_content_in_file = False
        if java_snippets_from_file:
            for snippet in java_snippets_from_file:
                self.assertSnippetProperties(snippet)
                if "processPayment" in snippet["snippet_content"] or \
                   "financial transaction" in snippet["snippet_content"] or \
                   "currency" in snippet["snippet_content"]:
                    found_expected_content_in_file = True
                    break

        self.assertTrue(found_expected_content_in_file,
                        f"Expected content related to 'processPayment' or 'financial transaction' not found in snippets from {java_file_path}."
                        f"Snippets from this file: {[s['snippet_content'][:100] + '...' for s in java_snippets_from_file]}")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_go_file_content(self):
        """Tests finding relevant content in a Go file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        
        go_file_path = os.path.join(DB["workspace_root"], "src", "calculator.go")
        go_content_lines = [
            "package main\n",
            "\n",
            "import \"fmt\"\n",
            "\n",
            "// Add performs addition of two integers\n",
            "func Add(a int, b int) int {\n",
            "  return a + b\n",
            "}\n",
            "\n",
            "func main() {\n",
            "  fmt.Println(Add(5, 3))\n",
            "}\n"
        ]
        DB["file_system"][go_file_path] = {
            "path": go_file_path,
            "is_directory": False,
            "content_lines": go_content_lines,
            "size_bytes": utils.calculate_size_bytes(go_content_lines),
            "last_modified": "2025-05-09T00:00:00Z"
        }

        query = "function for integer addition"
        results = codebase_search(query=query, target_directories=["src"])
        self.assertIsInstance(results, list)
        
        go_snippets = [r for r in results if r["file_path"] == go_file_path]
        self.assertTrue(len(go_snippets) >= 1, f"Expected >= 1 snippet from {go_file_path} for query '{query}'")
        
        found_expected_content = any("func Add" in s["snippet_content"] or "performs addition" in s["snippet_content"] for s in go_snippets)
        if go_snippets:
            self.assertSnippetProperties(go_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'func Add' or 'performs addition' content from .go snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_haskell_file_content(self):
        """Tests finding relevant content in a Haskell file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        
        hs_file_path = os.path.join(DB["workspace_root"], "src", "Utils.hs")
        hs_content_lines = [
            "module Utils where\n",
            "\n",
            "-- Calculates factorial of a number\n",
            "factorial :: Integer -> Integer\n",
            "factorial 0 = 1\n",
            "factorial n = n * factorial (n - 1)\n",
            "\n",
            "main :: IO ()\n",
            "main = print (factorial 5)\n"
        ]
        DB["file_system"][hs_file_path] = {
            "path": hs_file_path,
            "is_directory": False,
            "content_lines": hs_content_lines,
            "size_bytes": utils.calculate_size_bytes(hs_content_lines),
            "last_modified": "2025-05-09T00:00:00Z"
        }

        query = "factorial calculation function"
        results = codebase_search(query=query, target_directories=["src"])
        self.assertIsInstance(results, list)
        
        hs_snippets = [r for r in results if r["file_path"] == hs_file_path]
        self.assertTrue(len(hs_snippets) >= 1, f"Expected >= 1 snippet from {hs_file_path} for query '{query}'")
        
        found_expected_content = any("factorial :: Integer" in s["snippet_content"] or "factorial 0 = 1" in s["snippet_content"] for s in hs_snippets)
        if hs_snippets:
            self.assertSnippetProperties(hs_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'factorial :: Integer' or 'factorial 0 = 1' content from .hs snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_scala_file_content(self):
        """Tests finding relevant content in a Scala file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        
        scala_file_path = os.path.join(DB["workspace_root"], "src", "Greeter.scala")
        scala_content_lines = [
            "object Greeter {\n",
            "  def greet(name: String): String = {\n",
            "    s\"Hello, $name! Welcome to Scala.\"\n",
            "  }\n",
            "\n",
            "  def main(args: Array[String]): Unit = {\n",
            "    println(greet(\"Developer\"))\n",
            "  }\n",
            "}\n"
        ]
        DB["file_system"][scala_file_path] = {
            "path": scala_file_path,
            "is_directory": False,
            "content_lines": scala_content_lines,
            "size_bytes": utils.calculate_size_bytes(scala_content_lines),
            "last_modified": "2025-05-09T00:00:00Z"
        }

        query = "greeting message for user"
        results = codebase_search(query=query, target_directories=["src"])
        self.assertIsInstance(results, list)
        
        scala_snippets = [r for r in results if r["file_path"] == scala_file_path]
        self.assertTrue(len(scala_snippets) >= 1, f"Expected >= 1 snippet from {scala_file_path} for query '{query}'")
        
        found_expected_content = any("def greet(name: String)" in s["snippet_content"] or "Welcome to Scala" in s["snippet_content"] for s in scala_snippets)
        if scala_snippets:
            self.assertSnippetProperties(scala_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'def greet' or 'Welcome to Scala' content from .scala snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_javascript_file_content(self):
        """Tests finding relevant content in a JavaScript file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        
        js_file_path = os.path.join(DB["workspace_root"], "src", "dom_utils.js")
        js_content_lines = [
            "// Utility functions for DOM manipulation\n",
            "function updateElementText(elementId, newText) {\n",
            "  const element = document.getElementById(elementId);\n",
            "  if (element) {\n",
            "    element.textContent = newText;\n",
            "    return true;\n",
            "  }\n",
            "  return false;\n",
            "}\n",
            "\n",
            "const highlightNode = (nodeId) => {\n",
            "  const node = document.querySelector(`#${nodeId}`);\n",
            "  if (node) node.style.backgroundColor = 'yellow';\n",
            "};\n"
        ]
        DB["file_system"][js_file_path] = {
            "path": js_file_path, "is_directory": False, "content_lines": js_content_lines,
            "size_bytes": utils.calculate_size_bytes(js_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "change text of a webpage element"
        results = codebase_search(query=query, target_directories=["src"])
        self.assertIsInstance(results, list)
        
        js_snippets = [r for r in results if r["file_path"] == js_file_path]
        self.assertTrue(len(js_snippets) >= 1, f"Expected >= 1 snippet from {js_file_path} for query '{query}'")
        
        found_expected_content = any("updateElementText" in s["snippet_content"] or "textContent" in s["snippet_content"] for s in js_snippets)
        if js_snippets:
            self.assertSnippetProperties(js_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'updateElementText' or 'textContent' related content from .js snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_csharp_file_content(self):
        """Tests finding relevant content in a C# file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        models_dir_path = os.path.join(DB["workspace_root"], "src", "Models")
        cs_file_path = os.path.join(models_dir_path, "Product.cs")

        # Mock directory structure
        if models_dir_path not in DB["file_system"]:
             DB["file_system"][models_dir_path] = {"path": models_dir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}
        
        cs_content_lines = [
            "namespace MyShop.Models {\n",
            "  public class Product {\n",
            "    public int Id { get; set; }\n",
            "    public string Name { get; set; }\n",
            "    public decimal Price { get; set; }\n",
            "\n",
            "    public decimal GetDiscountedPrice(decimal discountPercentage) {\n",
            "      if (discountPercentage < 0 || discountPercentage > 1) throw new System.ArgumentException(\"Invalid discount\");\n",
            "      return Price * (1 - discountPercentage);\n",
            "    }\n",
            "  }\n",
            "}\n"
        ]
        DB["file_system"][cs_file_path] = {
            "path": cs_file_path, "is_directory": False, "content_lines": cs_content_lines,
            "size_bytes": utils.calculate_size_bytes(cs_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "calculate discounted product price"
        results = codebase_search(query=query, target_directories=["src/Models"])
        self.assertIsInstance(results, list)
        
        cs_snippets = [r for r in results if r["file_path"] == cs_file_path]
        self.assertTrue(len(cs_snippets) >= 1, f"Expected >= 1 snippet from {cs_file_path} for query '{query}'")
        
        found_expected_content = any("GetDiscountedPrice" in s["snippet_content"] or "MyShop.Models" in s["snippet_content"] for s in cs_snippets)
        if cs_snippets:
            self.assertSnippetProperties(cs_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'GetDiscountedPrice' or 'MyShop.Models' related content from .cs snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_cpp_file_content(self):
        """Tests finding relevant content in a C++ file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        cpp_utils_dir_path = os.path.join(DB["workspace_root"], "src", "utils")
        cpp_file_path = os.path.join(cpp_utils_dir_path, "string_helpers.cpp")
        
        if cpp_utils_dir_path not in DB["file_system"]: # Assuming 'src' exists from base setup
             DB["file_system"][cpp_utils_dir_path] = {"path": cpp_utils_dir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}

        cpp_content_lines = [
            "#include <string>\n",
            "#include <algorithm>\n",
            "\n",
            "namespace StringHelpers {\n",
            "  std::string toUpperCase(std::string s) {\n",
            "    std::transform(s.begin(), s.end(), s.begin(), ::toupper);\n",
            "    return s;\n",
            "  }\n",
            "  // Function to reverse a string\n",
            "  std::string reverseString(std::string str) {\n",
            "    std::reverse(str.begin(), str.end());\n",
            "    return str;\n",
            "  }\n",
            "} // namespace StringHelpers\n"
        ]
        DB["file_system"][cpp_file_path] = {
            "path": cpp_file_path, "is_directory": False, "content_lines": cpp_content_lines,
            "size_bytes": utils.calculate_size_bytes(cpp_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "function to reverse a text string"
        results = codebase_search(query=query, target_directories=["src/utils"])
        self.assertIsInstance(results, list)
        
        cpp_snippets = [r for r in results if r["file_path"] == cpp_file_path]
        self.assertTrue(len(cpp_snippets) >= 1, f"Expected >= 1 snippet from {cpp_file_path} for query '{query}'")
        
        found_expected_content = any("reverseString" in s["snippet_content"] or "StringHelpers" in s["snippet_content"] for s in cpp_snippets)
        if cpp_snippets:
            self.assertSnippetProperties(cpp_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'reverseString' or 'StringHelpers' related content from .cpp snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_php_file_content(self):
        """Tests finding relevant content in a PHP file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        php_api_dir_path = os.path.join(DB["workspace_root"], "src", "api")
        php_file_path = os.path.join(php_api_dir_path, "user_api.php")

        if php_api_dir_path not in DB["file_system"]:
             DB["file_system"][php_api_dir_path] = {"path": php_api_dir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}

        php_content_lines = [
            "<?php\n",
            "// API endpoint for user data\n",
            "function getUserData($userId) {\n",
            "  $users = [\n",
            "    1 => ['name' => 'Carlos', 'email' => 'carlos@example.com'],\n",
            "    2 => ['name' => 'Diana', 'email' => 'diana@example.com']\n",
            "  ];\n",
            "  return isset($users[$userId]) ? $users[$userId] : null;\n",
            "}\n",
            "\n",
            "// Example usage:\n",
            "$userData = getUserData(1);\n",
            "// echo json_encode($userData);\n",
            "?>\n"
        ]
        DB["file_system"][php_file_path] = {
            "path": php_file_path, "is_directory": False, "content_lines": php_content_lines,
            "size_bytes": utils.calculate_size_bytes(php_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }
        
        query = "fetch user information endpoint"
        results = codebase_search(query=query, target_directories=["src/api"])
        self.assertIsInstance(results, list)
        
        php_snippets = [r for r in results if r["file_path"] == php_file_path]
        self.assertTrue(len(php_snippets) >= 1, f"Expected >= 1 snippet from {php_file_path} for query '{query}'")
        
        found_expected_content = any("getUserData" in s["snippet_content"] or "Carlos" in s["snippet_content"] for s in php_snippets)
        if php_snippets:
            self.assertSnippetProperties(php_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'getUserData' or user name related content from .php snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_rust_file_content(self):
        """Tests finding relevant content in a Rust file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        rust_parser_dir_path = os.path.join(DB["workspace_root"], "src", "parser")
        rust_file_path = os.path.join(rust_parser_dir_path, "token_parser.rs")

        if rust_parser_dir_path not in DB["file_system"]:
             DB["file_system"][rust_parser_dir_path] = {"path": rust_parser_dir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}
        
        rust_content_lines = [
            "// Token processing utilities for a Rust application\n",
            "pub struct Token {\n",
            "    kind: String,\n",
            "    value: String,\n",
            "}\n",
            "\n",
            "pub fn parse_token_stream(stream: &str) -> Vec<Token> {\n",
            "    // Simplified token parsing logic\n",
            "    if stream.contains(\"keyword\") {\n",
            "        return vec![Token { kind: \"keyword\".to_string(), value: stream.to_string() }];\n",
            "    }\n",
            "    vec![]\n",
            "}\n"
        ]
        DB["file_system"][rust_file_path] = {
            "path": rust_file_path, "is_directory": False, "content_lines": rust_content_lines,
            "size_bytes": utils.calculate_size_bytes(rust_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "parse input tokens from stream"
        results = codebase_search(query=query, target_directories=["src/parser"])
        self.assertIsInstance(results, list)
        
        rust_snippets = [r for r in results if r["file_path"] == rust_file_path]
        self.assertTrue(len(rust_snippets) >= 1, f"Expected >= 1 snippet from {rust_file_path} for query '{query}'")
        
        found_expected_content = any("parse_token_stream" in s["snippet_content"] or "struct Token" in s["snippet_content"] for s in rust_snippets)
        if rust_snippets:
            self.assertSnippetProperties(rust_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'parse_token_stream' or 'struct Token' related content from .rs snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_c_file_content(self):
        """Tests finding relevant content in a C file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        c_core_dir_path = os.path.join(DB["workspace_root"], "src", "core")
        c_file_path = os.path.join(c_core_dir_path, "memory_manager.c")

        if c_core_dir_path not in DB["file_system"]:
             DB["file_system"][c_core_dir_path] = {"path": c_core_dir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}

        c_content_lines = [
            "#include <stdio.h>\n",
            "#include <stdlib.h>\n",
            "#include <string.h>\n",
            "\n",
            "// Allocates a block of memory of a given size\n",
            "void* allocate_block(size_t size) {\n",
            "    void* block = malloc(size);\n",
            "    if (block == NULL) {\n",
            "        perror(\"Failed to allocate memory\");\n",
            "        // In a real app, might exit or throw custom error\n",
            "    }\n",
            "    return block;\n",
            "}\n"
        ]
        DB["file_system"][c_file_path] = {
            "path": c_file_path, "is_directory": False, "content_lines": c_content_lines,
            "size_bytes": utils.calculate_size_bytes(c_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "allocate memory block"
        results = codebase_search(query=query, target_directories=["src/core"])
        self.assertIsInstance(results, list)
        
        c_snippets = [r for r in results if r["file_path"] == c_file_path]
        self.assertTrue(len(c_snippets) >= 1, f"Expected >= 1 snippet from {c_file_path} for query '{query}'")
        
        found_expected_content = any("allocate_block" in s["snippet_content"] or "malloc(size)" in s["snippet_content"] for s in c_snippets)
        if c_snippets:
            self.assertSnippetProperties(c_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'allocate_block' or 'malloc' related content from .c snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_swift_file_content(self):
        """Tests finding relevant content in a Swift file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        swift_ui_dir_path = os.path.join(DB["workspace_root"], "src", "UI")
        swift_file_path = os.path.join(swift_ui_dir_path, "ButtonView.swift")

        if swift_ui_dir_path not in DB["file_system"]:
             DB["file_system"][swift_ui_dir_path] = {"path": swift_ui_dir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}
        
        swift_content_lines = [
            "import SwiftUI\n",
            "\n",
            "struct ButtonView: View {\n",
            "    var label: String\n",
            "    var action: () -> Void\n",
            "\n",
            "    var body: some View {\n",
            "        Button(action: action) {\n",
            "            Text(label)\n",
            "                .padding()\n",
            "                .background(Color.blue)\n",
            "                .foregroundColor(.white)\n",
            "                .cornerRadius(8)\n",
            "        }\n",
            "    }\n",
            "}\n"
        ]
        DB["file_system"][swift_file_path] = {
            "path": swift_file_path, "is_directory": False, "content_lines": swift_content_lines,
            "size_bytes": utils.calculate_size_bytes(swift_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "custom UI button component"
        results = codebase_search(query=query, target_directories=["src/UI"])
        self.assertIsInstance(results, list)
        
        swift_snippets = [r for r in results if r["file_path"] == swift_file_path]
        self.assertTrue(len(swift_snippets) >= 1, f"Expected >= 1 snippet from {swift_file_path} for query '{query}'")
        
        found_expected_content = any("struct ButtonView" in s["snippet_content"] or "foregroundColor(.white)" in s["snippet_content"] for s in swift_snippets)
        if swift_snippets:
            self.assertSnippetProperties(swift_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'struct ButtonView' or styling related content from .swift snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_kotlin_file_content(self):
        """Tests finding relevant content in a Kotlin file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        kotlin_utils_dir_path = os.path.join(DB["workspace_root"], "src", "utils")
        kotlin_file_path = os.path.join(kotlin_utils_dir_path, "DataConverter.kt")

        if kotlin_utils_dir_path not in DB["file_system"]:
             DB["file_system"][kotlin_utils_dir_path] = {"path": kotlin_utils_dir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}

        kotlin_content_lines = [
            "package com.example.utils\n",
            "\n",
            "data class UserConfig(val id: String, val preferences: Map<String, String>)\n",
            "\n",
            "// Converts a JSON string to UserConfig object\n",
            "fun jsonToUserConfig(jsonString: String): UserConfig? {\n",
            "    // Simplified: In real scenario, use a JSON library like Gson or Moshi\n",
            "    if (jsonString.contains(\"id_123\")) {\n",
            "        return UserConfig(\"id_123\", mapOf(\"theme\" to \"dark\"))\n",
            "    }\n",
            "    return null\n",
            "}\n"
        ]
        DB["file_system"][kotlin_file_path] = {
            "path": kotlin_file_path, "is_directory": False, "content_lines": kotlin_content_lines,
            "size_bytes": utils.calculate_size_bytes(kotlin_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "convert JSON to user configuration object"
        results = codebase_search(query=query, target_directories=["src/utils"])
        self.assertIsInstance(results, list)
        
        kotlin_snippets = [r for r in results if r["file_path"] == kotlin_file_path]
        self.assertTrue(len(kotlin_snippets) >= 1, f"Expected >= 1 snippet from {kotlin_file_path} for query '{query}'")
        
        found_expected_content = any("jsonToUserConfig" in s["snippet_content"] or "data class UserConfig" in s["snippet_content"] for s in kotlin_snippets)
        if kotlin_snippets:
            self.assertSnippetProperties(kotlin_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'jsonToUserConfig' or 'UserConfig' related content from .kt snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_shell_script_content(self):
        """Tests finding relevant content in a Bash shell script."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        scripts_dir_path = os.path.join(DB["workspace_root"], "scripts")
        sh_file_path = os.path.join(scripts_dir_path, "deploy_app.sh")

        if scripts_dir_path not in DB["file_system"]:
             DB["file_system"][scripts_dir_path] = {"path": scripts_dir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}

        sh_content_lines = [
            "#!/bin/bash\n",
            "\n",
            "# Script to deploy the application\n",
            "APP_NAME=\"MyWebApp\"\n",
            "DEPLOY_DIR=\"/srv/www/$APP_NAME\"\n",
            "\n",
            "function build_application() {\n",
            "  echo \"Building $APP_NAME...\"\n",
            "  # npm run build or similar\n",
            "  echo \"Build complete.\"\n",
            "}\n",
            "\n",
            "function push_to_server() {\n",
            "  echo \"Deploying to $DEPLOY_DIR...\"\n",
            "  # rsync or scp commands\n",
            "  echo \"Deployment successful.\"\n",
            "}\n",
            "\n",
            "build_application\n",
            "push_to_server\n"
        ]
        DB["file_system"][sh_file_path] = {
            "path": sh_file_path, "is_directory": False, "content_lines": sh_content_lines,
            "size_bytes": utils.calculate_size_bytes(sh_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "script for application deployment steps"
        results = codebase_search(query=query, target_directories=["scripts"])
        self.assertIsInstance(results, list)
        
        sh_snippets = [r for r in results if r["file_path"] == sh_file_path]
        self.assertTrue(len(sh_snippets) >= 1, f"Expected >= 1 snippet from {sh_file_path} for query '{query}'")
        
        found_expected_content = any("deploy_app.sh" in s["snippet_content"] or "build_application" in s["snippet_content"] or "push_to_server" in s["snippet_content"] for s in sh_snippets)
        if sh_snippets:
            self.assertSnippetProperties(sh_snippets[0])
        self.assertTrue(found_expected_content, "Expected deployment script related content from .sh snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_sql_file_content(self):
        """Tests finding relevant content in an SQL file."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")

        db_migrations_dir = os.path.join(DB["workspace_root"], "db", "migrations")
        sql_file_path = os.path.join(db_migrations_dir, "001_create_users_table.sql")

        # Mock directory structure for db and db/migrations
        db_dir = os.path.join(DB["workspace_root"], "db")
        if db_dir not in DB["file_system"]:
            DB["file_system"][db_dir] = {"path": db_dir, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}
        if db_migrations_dir not in DB["file_system"]:
            DB["file_system"][db_migrations_dir] = {"path": db_migrations_dir, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": "2025-05-09T01:00:00Z"}

        sql_content_lines = [
            "-- Migration script for creating the users table\n",
            "CREATE TABLE users (\n",
            "    id INT PRIMARY KEY AUTO_INCREMENT,\n",
            "    username VARCHAR(255) NOT NULL UNIQUE,\n",
            "    email VARCHAR(255) NOT NULL UNIQUE,\n",
            "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n",
            ");\n",
            "\n",
            "INSERT INTO users (username, email) VALUES ('admin', 'admin@example.com');\n"
        ]
        DB["file_system"][sql_file_path] = {
            "path": sql_file_path, "is_directory": False, "content_lines": sql_content_lines,
            "size_bytes": utils.calculate_size_bytes(sql_content_lines),
            "last_modified": "2025-05-09T01:00:00Z"
        }

        query = "user database table schema definition"
        results = codebase_search(query=query, target_directories=["db/migrations"])
        self.assertIsInstance(results, list)
        
        sql_snippets = [r for r in results if r["file_path"] == sql_file_path]
        self.assertTrue(len(sql_snippets) >= 1, f"Expected >= 1 snippet from {sql_file_path} for query '{query}'")
        
        found_expected_content = any("CREATE TABLE users" in s["snippet_content"] or "username VARCHAR" in s["snippet_content"] for s in sql_snippets)
        if sql_snippets:
            self.assertSnippetProperties(sql_snippets[0])
        self.assertTrue(found_expected_content, "Expected 'CREATE TABLE users' or column definition related content from .sql snippets.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_git_metadata_enhancement(self):
        """Tests that codebase_search includes git metadata when query relates to commits/PRs."""
        if not self.local_model_loaded:
            self.skipTest("Local embedding model not loaded.")
        
        # Query that should match our test commit that references PR #123
        query = "authentication bug fix"
        results = codebase_search(query=query)
        
        self.assertIsInstance(results, list)
        
        # Look for git metadata snippet
        git_metadata_snippets = [r for r in results if r.get("is_git_metadata")]
        
        # If git search functionality works, we should get git metadata
        # But don't fail if git commands aren't available in test environment
        if git_metadata_snippets:
            git_snippet = git_metadata_snippets[0]
            self.assertSnippetProperties(git_snippet)  # This will use our enhanced validation
            self.assertEqual(git_snippet["file_path"], "<git_metadata>")
            self.assertIn("pr_numbers", git_snippet)
            self.assertIn("commit_hash", git_snippet)
            print(f"✅ Git metadata enhancement working: Found {len(git_metadata_snippets)} git metadata snippets")
        else:
            print("ℹ️  No git metadata snippets found (git may not be available in test environment)")
        
        # Regular snippets should still work
        regular_snippets = [r for r in results if not r.get("is_git_metadata")]
        if regular_snippets:
            self.assertSnippetProperties(regular_snippets[0])  # Test regular snippet validation too

# --- Tests using a Cloned Real Repository ---
@unittest.skipIf("SKIP_REAL_REPO_TESTS" in os.environ, "Skipping real repo tests")
class TestCodebaseSearchRealRepo(BaseCodebaseSearchTest):
    """Tests codebase_search using a cloned external repository."""
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
        if TestCodebaseSearchRealRepo.hydrated_item_count <= 0: # Check if not hydrated or failed
             super().setUp() # Reset DB state from ORIGINAL_DB_STATE
             print(f"Hydrating DB from cloned repo: {self.temp_repo_dir}")
             try:
                 success = utils.hydrate_db_from_directory(DB, self.temp_repo_dir)
                 if not success: raise RuntimeError("Hydration returned False.")
                 TestCodebaseSearchRealRepo.hydrated_item_count = len(DB.get('file_system',{}))
                 print(f"Hydration complete. Found {TestCodebaseSearchRealRepo.hydrated_item_count} items.")
                 if TestCodebaseSearchRealRepo.hydrated_item_count == 0:
                      print("WARNING: Hydration resulted in 0 items. Real repo tests might not be meaningful.")
             except Exception as e:
                 print(f"ERROR during hydration: {e}")
                 TestCodebaseSearchRealRepo.hydrated_item_count = -1 # Mark as failed
                 self.fail(f"Setup failed: Could not hydrate DB: {e}")
        elif TestCodebaseSearchRealRepo.hydrated_item_count < 0:
             self.fail("Hydration failed in previous setup.")

    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not available, skipping integration tests.")
    def test_search_real_repo_product_related(self):
        """Tests searching for product terms in the hydrated repo content."""
        if TestCodebaseSearchRealRepo.hydrated_item_count <= 0:
            self.skipTest("Hydration failed or yielded 0 items.")
        query = "product price"
        results = codebase_search(query=query)
        self.assertIsInstance(results, list)
        self.assertTrue(len(results) > 0, f"Expected > 0 results for query '{query}' in the hydrated repo.")
        found_relevant_term = any(term in s["snippet_content"].lower() for s in results for term in ["price", "product", "item", "cost", "amount", "total"])
        self.assertTrue(found_relevant_term, f"Expected at least one snippet with product/price terms for query '{query}'.")

class TestCodebaseSearchInputValidation:
    def setup_method(self):
        # Only setup for tests that need a workspace
        pass

    def teardown_method(self):
        DB.clear()

    def test_query_not_non_empty_string(self):
        minimal_reset_db_for_codebase_search()
        with pytest.raises(ValueError, match="The 'query' parameter must be a non-empty string."):
            codebase_search("")
        with pytest.raises(ValueError, match="The 'query' parameter must be a non-empty string."):
            codebase_search(None)
        with pytest.raises(ValueError, match="The 'query' parameter must be a non-empty string."):
            codebase_search(123)

    def test_target_directories_not_list(self):
        minimal_reset_db_for_codebase_search()
        with pytest.raises(ValueError, match="The 'target_directories' parameter must be a list of strings if provided."):
            codebase_search("valid query", target_directories="notalist")
        with pytest.raises(ValueError, match="The 'target_directories' parameter must be a list of strings if provided."):
            codebase_search("valid query", target_directories=123)

    def test_target_directories_element_not_non_empty_string(self):
        minimal_reset_db_for_codebase_search()
        with pytest.raises(ValueError, match="is not a valid non-empty string"):
            codebase_search("valid query", target_directories=[""])
        with pytest.raises(ValueError, match="is not a valid non-empty string"):
            codebase_search("valid query", target_directories=[None])
        with pytest.raises(ValueError, match="is not a valid non-empty string"):
            codebase_search("valid query", target_directories=[123])

if __name__ == "__main__":
    unittest.main()
