"""Test suite for read_many_files API function."""

import pytest
from unittest.mock import patch
import os
import tempfile
import json
import sys
from pathlib import Path

# Add the APIs directory to Python path so we can import from gemini_cli
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "APIs"))

from gemini_cli.read_many_files_api import read_many_files
from gemini_cli.SimulationEngine.file_utils import DEFAULT_EXCLUDES
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotAvailableError
from gemini_cli.SimulationEngine.db import DB

import unittest
from unittest.mock import patch, MagicMock
import os

from gemini_cli.SimulationEngine.db import DB
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


@pytest.fixture(autouse=True)
def setup_test_workspace():
    """Set up a test workspace with sample files."""
    DB.clear()
    
    # Create test workspace
    workspace_root = "/workspace"
    DB["workspace_root"] = workspace_root
    DB["file_system"] = {
        workspace_root: {
            "path": workspace_root,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        # Text files
        f"{workspace_root}/README.md": {
            "path": f"{workspace_root}/README.md",
            "is_directory": False,
            "content_lines": ["# Test Project\n", "This is a test.\n"],
            "size_bytes": 30,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        f"{workspace_root}/package.json": {
            "path": f"{workspace_root}/package.json",
            "is_directory": False,
            "content_lines": ['{"name": "test"}\n'],
            "size_bytes": 16,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        # Source directory
        f"{workspace_root}/src": {
            "path": f"{workspace_root}/src",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        f"{workspace_root}/src/main.py": {
            "path": f"{workspace_root}/src/main.py",
            "is_directory": False,
            "content_lines": ["def main():\n", "    print('Hello World')\n"],
            "size_bytes": 35,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        f"{workspace_root}/src/utils.py": {
            "path": f"{workspace_root}/src/utils.py",
            "is_directory": False,
            "content_lines": ["def helper():\n", "    return True\n"],
            "size_bytes": 28,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        # Test directory
        f"{workspace_root}/tests": {
            "path": f"{workspace_root}/tests",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        f"{workspace_root}/tests/test_main.py": {
            "path": f"{workspace_root}/tests/test_main.py",
            "is_directory": False,
            "content_lines": ["def test_main():\n", "    assert True\n"],
            "size_bytes": 30,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        # Node modules (should be excluded by default)
        f"{workspace_root}/node_modules": {
            "path": f"{workspace_root}/node_modules",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        f"{workspace_root}/node_modules/package.js": {
            "path": f"{workspace_root}/node_modules/package.js",
            "is_directory": False,
            "content_lines": ["// module code\n"],
            "size_bytes": 15,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        # Binary/image files
        f"{workspace_root}/image.png": {
            "path": f"{workspace_root}/image.png",
            "is_directory": False,
            "content_lines": ["\x89PNG\r\n\x1a\n"],  # PNG header
            "size_bytes": 100,
            "last_modified": "2024-01-01T12:00:00Z",
        },
        f"{workspace_root}/document.pdf": {
            "path": f"{workspace_root}/document.pdf",
            "is_directory": False,
            "content_lines": ["%PDF-1.4\n"],  # PDF header
            "size_bytes": 200,
            "last_modified": "2024-01-01T12:00:00Z",
        },
    }
    
    yield
    DB.clear()


class TestReadManyFiles:
    """Test suite for read_many_files function."""

    def test_read_single_text_file(self):
        """Test reading a single text file."""
        result = read_many_files(paths=["README.md"])
        
        assert result["success"] is True
        assert result["total_files_processed"] == 1
        assert len(result["content_parts"]) == 1
        assert "--- README.md ---" in result["content_parts"][0]
        assert "# Test Project" in result["content_parts"][0]
        assert "This is a test." in result["content_parts"][0]
        assert result["processed_files"] == ["README.md"]

    def test_read_multiple_text_files(self):
        """Test reading multiple text files."""
        result = read_many_files(paths=["README.md", "package.json"])
        
        assert result["success"] is True
        assert result["total_files_processed"] == 2
        assert len(result["content_parts"]) == 2
        
        # Check that both files are included with separators
        content_str = "".join(result["content_parts"])
        assert "--- README.md ---" in content_str
        assert "--- package.json ---" in content_str
        assert "# Test Project" in content_str
        assert '"name": "test"' in content_str

    def test_glob_pattern_matching(self):
        """Test glob pattern matching for multiple files."""
        result = read_many_files(paths=["src/*.py"])
        
        assert result["success"] is True
        assert result["total_files_processed"] == 2
        assert set(result["processed_files"]) == {"src/main.py", "src/utils.py"}
        
        content_str = "".join(result["content_parts"])
        assert "--- src/main.py ---" in content_str
        assert "--- src/utils.py ---" in content_str
        assert "def main():" in content_str
        assert "def helper():" in content_str

    def test_recursive_glob_patterns(self):
        """Test recursive glob patterns."""
        result = read_many_files(paths=["**/*.py"])
        
        assert result["success"] is True
        assert result["total_files_processed"] == 3
        expected_files = {"src/main.py", "src/utils.py", "tests/test_main.py"}
        assert set(result["processed_files"]) == expected_files

    def test_include_patterns(self):
        """Test include patterns functionality."""
        result = read_many_files(
            paths=["README.md"],
            include=["src/*.py"]
        )
        
        assert result["success"] is True
        assert result["total_files_processed"] == 3
        expected_files = {"README.md", "src/main.py", "src/utils.py"}
        assert set(result["processed_files"]) == expected_files

    def test_exclude_patterns(self):
        """Test exclude patterns functionality."""
        result = read_many_files(
            paths=["**/*.py"],
            exclude=["tests/**"]
        )
        
        assert result["success"] is True
        assert result["total_files_processed"] == 2
        expected_files = {"src/main.py", "src/utils.py"}
        assert set(result["processed_files"]) == expected_files

    def test_default_excludes_enabled(self):
        """Test that default excludes work when enabled."""
        result = read_many_files(
            paths=["**/*.js"],
            useDefaultExcludes=True
        )
        
        assert result["success"] is True
        # Should not find the file in node_modules
        assert result["total_files_processed"] == 0
        assert "node_modules" not in str(result["processed_files"])

    def test_default_excludes_disabled(self):
        """Test that default excludes can be disabled."""
        result = read_many_files(
            paths=["**/*.js"],
            useDefaultExcludes=False
        )
        
        assert result["success"] is True
        # Should find the file in node_modules when default excludes are off
        assert result["total_files_processed"] == 1
        assert "node_modules/package.js" in result["processed_files"]

    def test_image_file_explicitly_requested(self):
        """Test that image files are processed when explicitly requested."""
        result = read_many_files(paths=["image.png"])
        
        assert result["success"] is True
        assert result["total_files_processed"] == 1
        assert result["processed_files"] == ["image.png"]
        
        # Should contain base64 data structure
        content_part = result["content_parts"][0]
        assert isinstance(content_part, dict)
        assert "inlineData" in content_part
        assert "data" in content_part["inlineData"]
        assert "mimeType" in content_part["inlineData"]

    def test_image_file_not_explicitly_requested(self):
        """Test that image files are skipped when not explicitly requested."""
        result = read_many_files(paths=["*"])  # This would match image.png but not explicitly
        
        assert result["success"] is True
        # Should skip the image file
        assert "image.png" not in result["processed_files"]
        
        # Check skipped files
        skipped_paths = [f["path"] for f in result["skipped_files"]]
        assert "image.png" in skipped_paths

    def test_pdf_file_explicitly_requested(self):
        """Test that PDF files are processed when explicitly requested."""
        result = read_many_files(paths=["document.pdf"])
        
        assert result["success"] is True
        assert result["total_files_processed"] == 1
        assert result["processed_files"] == ["document.pdf"]
        
        # Should contain base64 data structure
        content_part = result["content_parts"][0]
        assert isinstance(content_part, dict)
        assert "inlineData" in content_part

    def test_no_files_found(self):
        """Test behavior when no files match the patterns."""
        result = read_many_files(paths=["nonexistent/**/*.xyz"])
        
        assert result["success"] is True
        assert result["total_files_processed"] == 0
        assert result["total_files_found"] == 0
        assert "No files matching the criteria were found" in result["message"]

    def test_empty_paths_parameter(self):
        """Test error handling for empty paths parameter."""
        with pytest.raises(InvalidInputError, match="'paths' must be a non-empty list"):
            read_many_files(paths=[])

    def test_invalid_paths_parameter_type(self):
        """Test error handling for invalid paths parameter type."""
        with pytest.raises(InvalidInputError, match="'paths' must be a non-empty list"):
            read_many_files(paths="not_a_list")  # type: ignore

    def test_invalid_include_parameter_type(self):
        """Test error handling for invalid include parameter type."""
        with pytest.raises(InvalidInputError, match="'include' must be a list"):
            read_many_files(paths=["README.md"], include="not_a_list")  # type: ignore

    def test_invalid_exclude_parameter_type(self):
        """Test error handling for invalid exclude parameter type."""
        with pytest.raises(InvalidInputError, match="'exclude' must be a list"):
            read_many_files(paths=["README.md"], exclude="not_a_list")  # type: ignore

    def test_workspace_not_available(self):
        """Test error when workspace_root is not configured."""
        DB.clear()  # Clear workspace_root
        
        with pytest.raises(WorkspaceNotAvailableError, match="workspace_root not configured"):
            read_many_files(paths=["README.md"])

    def test_file_processing_with_separators(self):
        """Test that file content is properly separated."""
        result = read_many_files(paths=["README.md", "package.json"])
        
        assert result["success"] is True
        assert len(result["content_parts"]) == 2
        
        # Check separator format
        readme_content = result["content_parts"][0]
        json_content = result["content_parts"][1]
        
        assert readme_content.startswith("--- README.md ---\n\n")
        assert readme_content.endswith("\n\n")
        assert json_content.startswith("--- package.json ---\n\n")
        assert json_content.endswith("\n\n")

    def test_recursive_parameter_functionality(self):
        """Test recursive parameter behavior."""
        # Test with recursive=True (default)
        result_recursive = read_many_files(paths=["**/*.py"], recursive=True)
        
        # Test with recursive=False - should still work since ** is in the pattern
        result_non_recursive = read_many_files(paths=["**/*.py"], recursive=False)
        
        # Both should find files since the pattern includes **
        assert result_recursive["total_files_processed"] > 0
        assert result_non_recursive["total_files_processed"] > 0

    def test_respect_git_ignore_parameter(self):
        """Test respect_git_ignore parameter (simplified for simulation)."""
        # Test both values to ensure parameter is accepted
        result_with_gitignore = read_many_files(
            paths=["README.md"], 
            respect_git_ignore=True
        )
        result_without_gitignore = read_many_files(
            paths=["README.md"], 
            respect_git_ignore=False
        )
        
        # Both should work in simulation environment
        assert result_with_gitignore["success"] is True
        assert result_without_gitignore["success"] is True

    def test_file_extension_patterns(self):
        """Test patterns that match specific file extensions."""
        result = read_many_files(paths=["*.md"])
        
        assert result["success"] is True
        assert result["total_files_processed"] == 1
        assert result["processed_files"] == ["README.md"]

    def test_complex_mixed_patterns(self):
        """Test complex scenarios with mixed patterns."""
        result = read_many_files(
            paths=["README.md", "src/**/*.py"],
            include=["package.json"],
            exclude=["**/test_*"]
        )
        
        assert result["success"] is True
        expected_files = {"README.md", "src/main.py", "src/utils.py", "package.json"}
        assert set(result["processed_files"]) == expected_files
        # test_main.py should be excluded
        assert "tests/test_main.py" not in result["processed_files"]

    def test_skipped_files_reporting(self):
        """Test that skipped files are properly reported."""
        result = read_many_files(paths=["*"])  # This will match images but not explicitly request them
        
        assert result["success"] is True
        assert len(result["skipped_files"]) > 0
        
        # Find the skipped image file
        skipped_image = next((f for f in result["skipped_files"] if f["path"] == "image.png"), None)
        assert skipped_image is not None
        assert "not explicitly requested" in skipped_image["reason"]

    def test_file_discovery_error_handling(self):
        """Test error handling during file discovery."""
        # Clear the DB to simulate an error condition
        original_db = DB.copy()
        DB.clear()
        # Set workspace_root but clear file_system to simulate a corrupted state
        DB["workspace_root"] = "/workspace"
        DB["file_system"] = None  # This will cause an error
        
        try:
            result = read_many_files(paths=["*.py"])
            
            # The function should handle the error gracefully
            assert result["success"] is False
            assert "Error during file search" in result["message"]
            assert result["total_files_processed"] == 0
        finally:
            # Restore the original DB state
            DB.clear()
            DB.update(original_db)

    def test_parameter_validation_edge_cases(self):
        """Test edge cases in parameter validation."""
        # Test empty string in paths
        with pytest.raises(InvalidInputError):
            read_many_files(paths=[""])
        
        # Test non-string in paths
        with pytest.raises(InvalidInputError):
            read_many_files(paths=[123])  # type: ignore
        
        # Test invalid boolean parameters
        with pytest.raises(InvalidInputError):
            read_many_files(paths=["README.md"], recursive="not_bool")  # type: ignore
        
        with pytest.raises(InvalidInputError):
            read_many_files(paths=["README.md"], useDefaultExcludes="not_bool")  # type: ignore 


class TestReadManyFilesMissingLines(unittest.TestCase):
    """Target read_many_files_api.py lines 83, 90, 99, 152-153, 193, 219."""
    
    def setUp(self):
        self.original_db_state = dict(DB)
        DB.clear()
        DB.update({
            'workspace_root': '/test/workspace',
            'cwd': '/test/workspace',
            'file_system': {}
        })
    
    def tearDown(self):
        DB.clear()
        DB.update(self.original_db_state)
    
    def test_read_many_files_validation_error(self):
        """Test error handling in read_many_files_api (lines 83, 90, 99)."""
        from gemini_cli.read_many_files_api import read_many_files
        
        # Test with invalid input that should trigger validation errors
        with self.assertRaises(InvalidInputError):
            read_many_files(None)  # Invalid input - should raise exception
        
        with self.assertRaises(InvalidInputError):
            read_many_files([])  # Empty list - should raise exception
    
    def test_read_many_files_nonexistent_files(self):
        """Test read_many_files with nonexistent files (lines 152-153, 193, 219)."""
        from gemini_cli.read_many_files_api import read_many_files
        
        result = read_many_files(['nonexistent1.txt', 'nonexistent2.txt'])
        self.assertIsInstance(result, dict)

