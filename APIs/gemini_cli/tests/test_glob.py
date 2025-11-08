import json
import os
import sys
from pathlib import Path
from unittest.mock import patch
import datetime
import unittest

import pytest

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli import glob  # noqa: E402
from gemini_cli.SimulationEngine import db as sim_db  # noqa: E402
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotAvailableError  # noqa: E402
from gemini_cli.SimulationEngine.db import DB
from gemini_cli.SimulationEngine.file_utils import filter_gitignore 
import tempfile
import shutil

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


@pytest.fixture(autouse=True)
def reload_db():
    """Load fresh DB snapshot before each test."""
    sim_db.DB.clear()
    with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
        sim_db.DB.update(json.load(fh))


class TestGlob:
    """Test cases for the glob function."""

    def test_glob_basic_pattern_matching(self):
        """Test basic glob pattern matching functionality."""
        # Test matching Python files
        result = glob("*.py")
        py_files = [f for f in result if f.endswith(".py")]
        assert len(py_files) > 0
        assert "/home/user/project/src/main.py" in result
        assert "/home/user/project/src/utils.py" in result

    def test_glob_markdown_files(self):
        """Test matching markdown files."""
        result = glob("*.md")
        md_files = [f for f in result if f.endswith(".md")]
        assert len(md_files) > 0
        assert "/home/user/project/README.md" in result
        assert "/home/user/project/docs/api.md" in result

    def test_glob_recursive_pattern(self):
        """Test recursive glob patterns with **."""
        result = glob("**/*.py")
        assert "/home/user/project/src/main.py" in result
        assert "/home/user/project/src/utils.py" in result
        assert "/home/user/project/tests/test_main.py" in result

    def test_glob_with_specific_path(self):
        """Test glob with specific search path."""
        result = glob("*.py", path="/home/user/project/src")
        assert "/home/user/project/src/main.py" in result
        assert "/home/user/project/src/utils.py" in result
        # Should not include files from other directories
        assert "/home/user/project/tests/test_main.py" not in result

    def test_glob_case_sensitive_matching(self):
        """Test case-sensitive pattern matching."""
        # Add a file with mixed case to test
        sim_db.DB["file_system"]["/home/user/project/Test.PY"] = {
            "path": "/home/user/project/Test.PY",
            "is_directory": False,
            "content_lines": ["# Test file\n"],
            "size_bytes": 12,
            "last_modified": "2025-01-15T10:45:00Z"
        }

        # Case-insensitive (default)
        result = glob("*.py", case_sensitive=False)
        assert "/home/user/project/Test.PY" in result

        # Case-sensitive
        result = glob("*.py", case_sensitive=True)
        assert "/home/user/project/Test.PY" not in result

        result = glob("*.PY", case_sensitive=True)
        assert "/home/user/project/Test.PY" in result

    def test_glob_respect_git_ignore_disabled(self):
        """Test glob with git ignore disabled."""
        # Add a file that would normally be ignored
        sim_db.DB["file_system"]["/home/user/project/debug.log"] = {
            "path": "/home/user/project/debug.log",
            "is_directory": False,
            "content_lines": ["Log content\n"],
            "size_bytes": 12,
            "last_modified": "2025-01-15T10:45:00Z"
        }

        # With git ignore enabled (default), .log files should be filtered out
        result = glob("*.log", respect_git_ignore=True)
        assert "/home/user/project/debug.log" not in result

        # With git ignore disabled, .log files should be included
        result = glob("*.log", respect_git_ignore=False)
        assert "/home/user/project/debug.log" in result

    def test_glob_sorting_by_modification_time(self):
        """Test that files are sorted by modification time (newest first)."""
        # Add files with different modification times
        now = datetime.datetime.utcnow()
        recent_time = now - datetime.timedelta(hours=2)
        old_time = now - datetime.timedelta(days=5)

        sim_db.DB["file_system"]["/home/user/project/recent.txt"] = {
            "path": "/home/user/project/recent.txt",
            "is_directory": False,
            "content_lines": ["Recent content\n"],
            "size_bytes": 15,
            "last_modified": recent_time.isoformat() + "Z"
        }

        sim_db.DB["file_system"]["/home/user/project/old.txt"] = {
            "path": "/home/user/project/old.txt",
            "is_directory": False,
            "content_lines": ["Old content\n"],
            "size_bytes": 12,
            "last_modified": old_time.isoformat() + "Z"
        }

        result = glob("*.txt")
        
        # Recent files should come first, then older files alphabetically
        recent_index = result.index("/home/user/project/recent.txt")
        old_index = result.index("/home/user/project/old.txt")
        
        # Recent file should come before old file
        assert recent_index < old_index

    def test_glob_no_matches(self):
        """Test glob with pattern that matches no files."""
        result = glob("*.xyz")
        assert result == []

    def test_glob_empty_pattern(self):
        """Test glob with empty pattern."""
        with pytest.raises(InvalidInputError, match="'pattern' must be a non-empty string"):
            glob("")

    def test_glob_non_string_pattern(self):
        """Test glob with non-string pattern."""
        with pytest.raises(InvalidInputError, match="'pattern' must be a non-empty string"):
            glob(123)

    def test_glob_invalid_path_type(self):
        """Test glob with invalid path type."""
        with pytest.raises(InvalidInputError, match="'path' must be a string or None"):
            glob("*.py", path=123)

    def test_glob_empty_path(self):
        """Test glob with empty path (now supported - maps to workspace root)."""
        result = glob("*.py", path="")
        # Should work and return files from workspace root
        assert isinstance(result, list)
        py_files = [f for f in result if f.endswith(".py")]
        assert len(py_files) > 0

    def test_glob_relative_path(self):
        """Test glob with relative path (now supported)."""
        result = glob("*.py", path="src")
        # Should work and return files from src directory
        assert isinstance(result, list)
        # Should find Python files in src directory
        assert "/home/user/project/src/main.py" in result
        assert "/home/user/project/src/utils.py" in result

    def test_glob_path_outside_workspace(self):
        """Test glob with path outside workspace (now treated as relative)."""
        # Paths with leading slashes are now treated as relative, so this creates
        # a path like workspace_root/outside/workspace which doesn't exist
        with pytest.raises(FileNotFoundError, match="Search path does not exist"):
            glob("*.py", path="/outside/workspace")

    def test_glob_invalid_case_sensitive_type(self):
        """Test glob with invalid case_sensitive type."""
        with pytest.raises(InvalidInputError, match="'case_sensitive' must be a boolean or None"):
            glob("*.py", case_sensitive="true")

    def test_glob_invalid_respect_git_ignore_type(self):
        """Test glob with invalid respect_git_ignore type."""
        with pytest.raises(InvalidInputError, match="'respect_git_ignore' must be a boolean or None"):
            glob("*.py", respect_git_ignore="true")

    def test_glob_workspace_not_available(self):
        """Test glob when workspace_root is not configured."""
        # Clear the workspace_root
        original_workspace_root = sim_db.DB.get("workspace_root")
        sim_db.DB.pop("workspace_root", None)

        with pytest.raises(WorkspaceNotAvailableError, match="workspace_root not configured in DB"):
            glob("*.py")

        # Restore for other tests
        sim_db.DB["workspace_root"] = original_workspace_root

    def test_glob_path_not_found(self):
        """Test glob with path that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Search path does not exist"):
            glob("*.py", path="/home/user/project/nonexistent")

    def test_glob_path_not_directory(self):
        """Test glob with path that points to a file."""
        with pytest.raises(NotADirectoryError, match="Search path is not a directory"):
            glob("*.py", path="/home/user/project/README.md")

    def test_glob_pattern_with_subdirectories(self):
        """Test glob patterns that include subdirectories."""
        result = glob("src/*.py")
        assert "/home/user/project/src/main.py" in result
        assert "/home/user/project/src/utils.py" in result
        # Should not include files from other directories
        assert "/home/user/project/tests/test_main.py" not in result

    def test_glob_all_files_pattern(self):
        """Test glob with pattern that matches all files."""
        result = glob("**/*")
        # Should include all files but not directories
        files = [f for f in result if not sim_db.DB["file_system"][f].get("is_directory", False)]
        assert len(files) > 0
        assert "/home/user/project/README.md" in result
        assert "/home/user/project/src/main.py" in result

    def test_glob_json_files(self):
        """Test glob matching JSON files."""
        result = glob("*.json")
        assert "/home/user/project/package.json" in result

    def test_glob_with_question_mark_wildcard(self):
        """Test glob with ? wildcard."""
        # Add files to test single character wildcard
        sim_db.DB["file_system"]["/home/user/project/file1.txt"] = {
            "path": "/home/user/project/file1.txt",
            "is_directory": False,
            "content_lines": ["Content 1\n"],
            "size_bytes": 10,
            "last_modified": "2025-01-15T10:45:00Z"
        }

        sim_db.DB["file_system"]["/home/user/project/file2.txt"] = {
            "path": "/home/user/project/file2.txt",
            "is_directory": False,
            "content_lines": ["Content 2\n"],
            "size_bytes": 10,
            "last_modified": "2025-01-15T10:46:00Z"
        }

        result = glob("file?.txt")
        assert "/home/user/project/file1.txt" in result
        assert "/home/user/project/file2.txt" in result

    def test_glob_alphabetical_sorting_for_old_files(self):
        """Test that old files are sorted alphabetically."""
        # Add old files with different names
        old_time = datetime.datetime.utcnow() - datetime.timedelta(days=5)

        sim_db.DB["file_system"]["/home/user/project/zebra.txt"] = {
            "path": "/home/user/project/zebra.txt",
            "is_directory": False,
            "content_lines": ["Zebra content\n"],
            "size_bytes": 14,
            "last_modified": old_time.isoformat() + "Z"
        }

        sim_db.DB["file_system"]["/home/user/project/apple.txt"] = {
            "path": "/home/user/project/apple.txt",
            "is_directory": False,
            "content_lines": ["Apple content\n"],
            "size_bytes": 14,
            "last_modified": old_time.isoformat() + "Z"
        }

        result = glob("*.txt")
        
        # Find the indices of our test files
        apple_index = result.index("/home/user/project/apple.txt")
        zebra_index = result.index("/home/user/project/zebra.txt")
        
        # Apple should come before zebra (alphabetical order for old files)
        assert apple_index < zebra_index

    def test_glob_gitignore_patterns(self):
        """Test basic gitignore pattern filtering."""
        # Add files that should be ignored
        sim_db.DB["file_system"]["/home/user/project/cache.pyc"] = {
            "path": "/home/user/project/cache.pyc",
            "is_directory": False,
            "content_lines": ["compiled python\n"],
            "size_bytes": 16,
            "last_modified": "2025-01-15T10:45:00Z"
        }

        sim_db.DB["file_system"]["/home/user/project/.DS_Store"] = {
            "path": "/home/user/project/.DS_Store",
            "is_directory": False,
            "content_lines": ["system file\n"],
            "size_bytes": 12,
            "last_modified": "2025-01-15T10:45:00Z"
        }

        # These should be filtered out by gitignore
        result = glob("*", respect_git_ignore=True)
        assert "/home/user/project/cache.pyc" not in result
        assert "/home/user/project/.DS_Store" not in result

        # But should be included when gitignore is disabled
        result = glob("*", respect_git_ignore=False)
        assert "/home/user/project/cache.pyc" in result
        assert "/home/user/project/.DS_Store" in result 


class TestFilterGitignore(unittest.TestCase):
    """Test that filter_gitignore matches against full relative path, not just basename."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_db_state = DB.copy()
        self.temp_dir = tempfile.mkdtemp(prefix="test_gitignore_")
        
        DB.clear()
        DB.update({
            "workspace_root": self.temp_dir,
            "cwd": self.temp_dir,
            "file_system": {},
            "gitignore_patterns": []
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        DB.clear()
        DB.update(self.original_db_state)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_gitignore_matches_full_path_not_basename(self):
        """Test that *.log pattern matches src/logs/debug.log (full path matching)."""
        # Create test file structure
        files = [
            (os.path.join(self.temp_dir, "src", "logs", "debug.log"), {"size": 100}),
            (os.path.join(self.temp_dir, "src", "logs", "error.log"), {"size": 200}),
            (os.path.join(self.temp_dir, "src", "main.py"), {"size": 300}),
            (os.path.join(self.temp_dir, "README.md"), {"size": 400}),
        ]
        
        # Set gitignore pattern to ignore all .log files
        DB["gitignore_patterns"] = ["*.log"]
        
        # Filter files
        filtered = filter_gitignore(files, self.temp_dir)
        
        # Should filter out both log files regardless of their directory depth
        filtered_paths = [path for path, _ in filtered]
        
        # Verify .log files are filtered out
        self.assertNotIn(os.path.join(self.temp_dir, "src", "logs", "debug.log"), filtered_paths)
        self.assertNotIn(os.path.join(self.temp_dir, "src", "logs", "error.log"), filtered_paths)
        
        # Verify other files remain
        self.assertIn(os.path.join(self.temp_dir, "src", "main.py"), filtered_paths)
        self.assertIn(os.path.join(self.temp_dir, "README.md"), filtered_paths)
    
    def test_gitignore_pattern_with_subdirectories(self):
        """Test that patterns correctly match files in subdirectories."""
        files = [
            (os.path.join(self.temp_dir, "tests", "unit", "test_api.py"), {"size": 100}),
            (os.path.join(self.temp_dir, "tests", "integration", "test_db.py"), {"size": 200}),
            (os.path.join(self.temp_dir, "src", "api.py"), {"size": 300}),
        ]
        
        # Pattern to ignore all test_*.py files (need wildcard for subdirectories)
        DB["gitignore_patterns"] = ["**/test_*.py"]
        
        filtered = filter_gitignore(files, self.temp_dir)
        filtered_paths = [path for path, _ in filtered]
        
        # Both test files should be filtered out
        self.assertNotIn(os.path.join(self.temp_dir, "tests", "unit", "test_api.py"), filtered_paths)
        self.assertNotIn(os.path.join(self.temp_dir, "tests", "integration", "test_db.py"), filtered_paths)
        
        # Non-test file should remain
        self.assertIn(os.path.join(self.temp_dir, "src", "api.py"), filtered_paths)
    
    def test_gitignore_pattern_specific_path(self):
        """Test that patterns work with wildcards in paths."""
        files = [
            (os.path.join(self.temp_dir, "src", "app.log"), {"size": 100}),
            (os.path.join(self.temp_dir, "src", "logs", "debug.log"), {"size": 200}),
            (os.path.join(self.temp_dir, "tests", "test.log"), {"size": 300}),
        ]
        
        # Pattern to ignore all .log files anywhere
        # Note: fnmatch doesn't support directory-specific patterns like gitignore does
        # This is a limitation of using fnmatch vs proper gitignore implementation
        DB["gitignore_patterns"] = ["*.log"]
        
        filtered = filter_gitignore(files, self.temp_dir)
        filtered_paths = [path for path, _ in filtered]
        
        # All .log files should be filtered
        self.assertNotIn(os.path.join(self.temp_dir, "src", "app.log"), filtered_paths)
        self.assertNotIn(os.path.join(self.temp_dir, "src", "logs", "debug.log"), filtered_paths)
        self.assertNotIn(os.path.join(self.temp_dir, "tests", "test.log"), filtered_paths)
    
    def test_gitignore_multiple_patterns(self):
        """Test that multiple patterns work correctly."""
        files = [
            (os.path.join(self.temp_dir, "src", "main.py"), {"size": 100}),
            (os.path.join(self.temp_dir, "build", "output.js"), {"size": 200}),
            (os.path.join(self.temp_dir, "logs", "debug.log"), {"size": 300}),
            (os.path.join(self.temp_dir, "README.md"), {"size": 400}),
        ]
        
        # Multiple patterns
        DB["gitignore_patterns"] = ["*.log", "build/*"]
        
        filtered = filter_gitignore(files, self.temp_dir)
        filtered_paths = [path for path, _ in filtered]
        
        # .log and build/* should be filtered
        self.assertNotIn(os.path.join(self.temp_dir, "logs", "debug.log"), filtered_paths)
        self.assertNotIn(os.path.join(self.temp_dir, "build", "output.js"), filtered_paths)
        
        # Others should remain
        self.assertIn(os.path.join(self.temp_dir, "src", "main.py"), filtered_paths)
        self.assertIn(os.path.join(self.temp_dir, "README.md"), filtered_paths)
    
    def test_gitignore_case_insensitive(self):
        """Test that pattern matching is case-insensitive."""
        files = [
            (os.path.join(self.temp_dir, "Debug.LOG"), {"size": 100}),
            (os.path.join(self.temp_dir, "error.Log"), {"size": 200}),
            (os.path.join(self.temp_dir, "main.py"), {"size": 300}),
        ]
        
        DB["gitignore_patterns"] = ["*.log"]
        
        filtered = filter_gitignore(files, self.temp_dir)
        filtered_paths = [path for path, _ in filtered]
        
        # Case-insensitive matching should filter both
        self.assertNotIn(os.path.join(self.temp_dir, "Debug.LOG"), filtered_paths)
        self.assertNotIn(os.path.join(self.temp_dir, "error.Log"), filtered_paths)
        self.assertIn(os.path.join(self.temp_dir, "main.py"), filtered_paths)
    
    def test_gitignore_directory_pattern(self):
        """Test that directory patterns (ending with /) work correctly."""
        files = [
            (os.path.join(self.temp_dir, "node_modules", "package", "index.js"), {"size": 100}),
            (os.path.join(self.temp_dir, "node_modules", "lib.js"), {"size": 200}),
            (os.path.join(self.temp_dir, "src", "app.js"), {"size": 300}),
        ]
        
        # Pattern to ignore node_modules directory
        DB["gitignore_patterns"] = ["node_modules/"]
        
        filtered = filter_gitignore(files, self.temp_dir)
        filtered_paths = [path for path, _ in filtered]
        
        # Files in node_modules should be filtered
        self.assertNotIn(os.path.join(self.temp_dir, "node_modules", "package", "index.js"), filtered_paths)
        self.assertNotIn(os.path.join(self.temp_dir, "node_modules", "lib.js"), filtered_paths)
        
        # Files outside node_modules should remain
        self.assertIn(os.path.join(self.temp_dir, "src", "app.js"), filtered_paths)


class TestGlobRelativePathSupport(unittest.TestCase):
    """Test that glob function accepts both relative and absolute paths."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_db_state = DB.copy()
        self.temp_dir = tempfile.mkdtemp(prefix="test_glob_")
        
        # Create test directory structure
        os.makedirs(os.path.join(self.temp_dir, "src", "utils"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "tests"), exist_ok=True)
        
        # Create test files
        test_files = [
            "src/main.py",
            "src/utils/helper.py",
            "tests/test_main.py",
            "README.md"
        ]
        
        for file_path in test_files:
            full_path = os.path.join(self.temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write("test content")
        
        # Set up DB
        DB.clear()
        file_system = {}
        
        # Add directories
        for dir_path in [self.temp_dir, 
                         os.path.join(self.temp_dir, "src"),
                         os.path.join(self.temp_dir, "src", "utils"),
                         os.path.join(self.temp_dir, "tests")]:
            file_system[dir_path] = {
                "path": dir_path,
                "is_directory": True,
                "last_modified": datetime.datetime.now().isoformat()
            }
        
        # Add files
        for file_path in test_files:
            full_path = os.path.join(self.temp_dir, file_path)
            file_system[full_path] = {
                "path": full_path,
                "is_directory": False,
                "content_lines": ["test content\n"],
                "size_bytes": 12,
                "last_modified": datetime.datetime.now().isoformat()
            }
        
        DB.update({
            "workspace_root": self.temp_dir,
            "cwd": self.temp_dir,
            "file_system": file_system,
            "gitignore_patterns": []
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        DB.clear()
        DB.update(self.original_db_state)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_glob_with_relative_path(self):
        """Test that glob accepts relative paths (Bug Fix #2)."""
        # This should work without raising "path must be an absolute path" error
        result = glob("*.py", path="src")
        
        # Should find Python files in src directory
        self.assertIsInstance(result, list)
        result_basenames = [os.path.basename(p) for p in result]
        self.assertIn("main.py", result_basenames)
    
    def test_glob_with_absolute_path(self):
        """Test that glob still accepts absolute paths."""
        src_path = os.path.join(self.temp_dir, "src")
        result = glob("*.py", path=src_path)
        
        self.assertIsInstance(result, list)
        result_basenames = [os.path.basename(p) for p in result]
        self.assertIn("main.py", result_basenames)
    
    def test_glob_with_nested_relative_path(self):
        """Test that glob accepts nested relative paths."""
        result = glob("*.py", path="src/utils")
        
        self.assertIsInstance(result, list)
        result_basenames = [os.path.basename(p) for p in result]
        self.assertIn("helper.py", result_basenames)
    
    def test_glob_with_none_path(self):
        """Test that glob works with path=None (searches workspace root)."""
        result = glob("*.md", path=None)
        
        self.assertIsInstance(result, list)
        result_basenames = [os.path.basename(p) for p in result]
        self.assertIn("README.md", result_basenames)
    
    def test_glob_with_dot_path(self):
        """Test that glob accepts '.' as current directory."""
        result = glob("*.md", path=".")
        
        self.assertIsInstance(result, list)
        result_basenames = [os.path.basename(p) for p in result]
        self.assertIn("README.md", result_basenames)
    
    def test_glob_pattern_matching(self):
        """Test that glob correctly matches patterns."""
        # Find all Python files
        result = glob("**/*.py", path=None)
        
        self.assertIsInstance(result, list)
        # Should find at least the test files we created
        self.assertGreater(len(result), 0)
        
        # All results should be .py files
        for file_path in result:
            self.assertTrue(file_path.endswith('.py'))
    
    def test_glob_with_gitignore_filtering(self):
        """Test that glob respects gitignore patterns."""
        # Add gitignore pattern with wildcard for subdirectories
        DB["gitignore_patterns"] = ["**/test_*.py"]
        
        # Find all Python files with gitignore enabled
        result = glob("*.py", path="tests", respect_git_ignore=True)
        
        # test_main.py should be filtered out
        result_basenames = [os.path.basename(p) for p in result]
        self.assertNotIn("test_main.py", result_basenames)
    
    def test_glob_without_gitignore_filtering(self):
        """Test that glob can disable gitignore filtering."""
        # Add gitignore pattern with wildcard
        DB["gitignore_patterns"] = ["**/test_*.py"]
        
        # Find all Python files with gitignore disabled
        result = glob("*.py", path="tests", respect_git_ignore=False)
        
        # test_main.py should be included
        result_basenames = [os.path.basename(p) for p in result]
        self.assertIn("test_main.py", result_basenames)
    
    def test_glob_outside_workspace_raises_error(self):
        """Test that glob raises error for paths outside workspace."""
        # resolve_workspace_path will treat /outside/workspace as relative path
        # and resolve it to workspace_root/outside/workspace, which won't exist
        with self.assertRaises(FileNotFoundError):
            glob("*.py", path="/outside/workspace")
    
    def test_glob_nonexistent_path_raises_error(self):
        """Test that glob raises FileNotFoundError for nonexistent paths."""
        with self.assertRaises(FileNotFoundError):
            glob("*.py", path="nonexistent")
    
    def test_glob_file_path_raises_error(self):
        """Test that glob raises NotADirectoryError when path is a file."""
        # Add a file to the path parameter (should be directory)
        with self.assertRaises(NotADirectoryError):
            glob("*.py", path="README.md")
    
    def test_glob_path_outside_workspace_after_resolution(self):
        """Test that glob catches paths that resolve outside workspace."""
        # This tests the _is_within_workspace check after resolve_workspace_path
        # We need to mock resolve_workspace_path to return a path outside workspace
        from unittest.mock import patch
        
        # Mock resolve_workspace_path to return a path outside workspace
        with patch('gemini_cli.file_system_api.resolve_workspace_path') as mock_resolve:
            # Return a path that's definitely outside the workspace
            mock_resolve.return_value = "/completely/different/path"
            
            # This should raise InvalidInputError because path is outside workspace
            with self.assertRaises(InvalidInputError) as context:
                glob("*.py", path="some_path")
            
            self.assertIn("workspace", str(context.exception).lower())


class TestGlobAndGitignoreIntegration(unittest.TestCase):
    """Integration tests for glob with gitignore filtering."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.original_db_state = DB.copy()
        self.temp_dir = tempfile.mkdtemp(prefix="test_integration_")
        
        # Create comprehensive test structure
        structure = {
            "src/app.py": "app code",
            "src/logs/debug.log": "debug logs",
            "src/logs/error.log": "error logs",
            "tests/unit/test_app.py": "unit tests",
            "tests/integration/test_api.py": "integration tests",
            "build/output.js": "build output",
            "docs/README.md": "documentation",
        }
        
        file_system = {}
        
        # Create files and directories
        for file_path, content in structure.items():
            full_path = os.path.join(self.temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            
            # Add to file system
            file_system[full_path] = {
                "path": full_path,
                "is_directory": False,
                "content_lines": [content + "\n"],
                "size_bytes": len(content),
                "last_modified": datetime.datetime.now().isoformat()
            }
        
        # Add all directories
        all_dirs = set()
        for file_path in structure.keys():
            parts = file_path.split('/')
            for i in range(len(parts)):
                dir_path = '/'.join(parts[:i+1]) if i < len(parts)-1 else '/'.join(parts[:i])
                if dir_path:
                    all_dirs.add(os.path.join(self.temp_dir, dir_path))
        
        all_dirs.add(self.temp_dir)
        for dir_path in all_dirs:
            if dir_path not in file_system:
                file_system[dir_path] = {
                    "path": dir_path,
                    "is_directory": True,
                    "last_modified": datetime.datetime.now().isoformat()
                }
        
        DB.clear()
        DB.update({
            "workspace_root": self.temp_dir,
            "cwd": self.temp_dir,
            "file_system": file_system,
            "gitignore_patterns": ["*.log", "build/*", "**/test_*.py"]
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        DB.clear()
        DB.update(self.original_db_state)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_glob_filters_log_files_in_subdirectories(self):
        """Test that *.log pattern filters log files in any subdirectory."""
        result = glob("**/*", path="src", respect_git_ignore=True)
        
        # Should not include any .log files
        for file_path in result:
            self.assertFalse(file_path.endswith('.log'), 
                           f"Log file {file_path} was not filtered by gitignore")
    
    def test_glob_filters_test_files_with_prefix(self):
        """Test that test_*.py pattern filters test files in any location."""
        result = glob("**/*.py", path=None, respect_git_ignore=True)
        
        # Should not include test_*.py files
        for file_path in result:
            basename = os.path.basename(file_path)
            self.assertFalse(basename.startswith('test_'), 
                           f"Test file {basename} was not filtered by gitignore")
    
    def test_glob_filters_build_directory(self):
        """Test that build/* pattern filters entire build directory."""
        result = glob("**/*", path=None, respect_git_ignore=True)
        
        # Should not include anything from build/
        for file_path in result:
            rel_path = os.path.relpath(file_path, self.temp_dir)
            self.assertFalse(rel_path.startswith('build'), 
                           f"Build file {rel_path} was not filtered by gitignore")
    
    def test_glob_without_gitignore_includes_all(self):
        """Test that disabling gitignore includes all matching files."""
        result_with_ignore = glob("**/*.log", path=None, respect_git_ignore=True)
        result_without_ignore = glob("**/*.log", path=None, respect_git_ignore=False)
        
        # Without gitignore should find more files
        self.assertGreaterEqual(len(result_without_ignore), len(result_with_ignore))
        
        # With gitignore should filter .log files
        self.assertEqual(len(result_with_ignore), 0)
        
        # Without gitignore should include .log files
        self.assertGreater(len(result_without_ignore), 0)


if __name__ == "__main__":
    unittest.main()

