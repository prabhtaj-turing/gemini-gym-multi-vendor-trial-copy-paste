"""Tests for grep_search function."""

import os
import sys
from pathlib import Path
import fnmatch
import unittest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli.file_system_api import grep_search
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotAvailableError
from gemini_cli.SimulationEngine.db import DB


class TestGrepSearch(unittest.TestCase):
    """Test cases for grep_search function."""

    def setUp(self):
        """Set up test environment with mock filesystem."""
        DB.clear()
        
        # Mock workspace root
        workspace_root = "/Users/user/workspace"
        DB["workspace_root"] = workspace_root
        
        # Mock file system with content
        DB["file_system"] = {
            workspace_root: {
                "path": workspace_root,
                "is_directory": True,
                "size_bytes": 0,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": []
            },
            f"{workspace_root}/README.md": {
                "path": f"{workspace_root}/README.md",
                "is_directory": False,
                "size_bytes": 150,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": """# Project Title

This is a sample project with Python code.

## Installation

Run `pip install -r requirements.txt` to install dependencies.

## Usage

Import the main function from the module:

```python
from myproject import main_function
```
""".splitlines(keepends=True)
            },
            f"{workspace_root}/main.py": {
                "path": f"{workspace_root}/main.py",
                "is_directory": False,
                "size_bytes": 200,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": """#!/usr/bin/env python3
\"\"\"Main module for the application.\"\"\"

import sys
import os
from typing import List, Dict, Any

def main_function() -> None:
    \"\"\"Entry point for the application.\"\"\"
    print("Hello, World!")
    return None

def helper_function(data: List[str]) -> Dict[str, Any]:
    \"\"\"Helper function to process data.\"\"\"
    return {"processed": data}

if __name__ == "__main__":
    main_function()
""".splitlines(keepends=True)
            },
            f"{workspace_root}/src/utils.py": {
                "path": f"{workspace_root}/src/utils.py",
                "is_directory": False,
                "size_bytes": 100,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": """\"\"\"Utility functions.\"\"\"

def utility_function():
    \"\"\"A utility function.\"\"\"
    pass

class UtilityClass:
    \"\"\"A utility class.\"\"\"
    def method(self):
        return "method result"
""".splitlines(keepends=True)
            },
            f"{workspace_root}/src": {
                "path": f"{workspace_root}/src",
                "is_directory": True,
                "size_bytes": 0,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": []
            },
            f"{workspace_root}/tests/test_main.py": {
                "path": f"{workspace_root}/tests/test_main.py",
                "is_directory": False,
                "size_bytes": 150,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": """\"\"\"Tests for main module.\"\"\"

import unittest
from main import main_function

class TestMain(unittest.TestCase):
    def test_main_function(self):
        \"\"\"Test main function.\"\"\"
        self.assertIsNone(main_function())
""".splitlines(keepends=True)
            },
            f"{workspace_root}/tests": {
                "path": f"{workspace_root}/tests",
                "is_directory": True,
                "size_bytes": 0,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": []
            },
            f"{workspace_root}/package.json": {
                "path": f"{workspace_root}/package.json",
                "is_directory": False,
                "size_bytes": 80,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": """{
  "name": "test-project",
  "version": "1.0.0",
  "description": "A test project",
  "main": "index.js"
}""".splitlines(keepends=True)
            },
            f"{workspace_root}/node_modules/some-module/index.js": {
                "path": f"{workspace_root}/node_modules/some-module/index.js",
                "is_directory": False,
                "size_bytes": 50,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": """module.exports = function() {
    return "Hello from module";
};""".splitlines(keepends=True)
            },
            f"{workspace_root}/node_modules": {
                "path": f"{workspace_root}/node_modules",
                "is_directory": True,
                "size_bytes": 0,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": []
            },
            f"{workspace_root}/node_modules/some-module": {
                "path": f"{workspace_root}/node_modules/some-module",
                "is_directory": True,
                "size_bytes": 0,
                "last_modified": "2024-01-01T00:00:00Z",
                "content_lines": []
            }
        }

    def tearDown(self):
        """Clean up after tests."""
        DB.clear()

    def test_grep_search_basic_pattern(self):
        """Test basic pattern matching."""
        workspace_root = DB["workspace_root"]
        
        # Search for "function" pattern
        results = grep_search("function")
        
        # Should find matches in main.py, utils.py, and test_main.py
        self.assertGreater(len(results), 0)
        
        # Verify structure of results
        for result in results:
            self.assertIn('filePath', result)
            self.assertIn('lineNumber', result)
            self.assertIn('line', result)
            self.assertIsInstance(result['lineNumber'], int)
            self.assertGreater(result['lineNumber'], 0)

    def test_grep_search_case_insensitive(self):
        """Test case insensitive pattern matching."""
        # Search for "FUNCTION" (uppercase) should match "function" in files
        results = grep_search("FUNCTION")
        
        # Should find matches despite case difference
        self.assertGreater(len(results), 0)

    def test_grep_search_regex_pattern(self):
        """Test regex pattern matching."""
        # Search for function definitions with regex
        results = grep_search(r"def\s+\w+\s*\(")
        
        # Should find function definitions
        self.assertGreater(len(results), 0)
        
        # Verify all matches contain "def"
        for result in results:
            self.assertIn("def", result['line'])

    def test_grep_search_with_path(self):
        """Test searching within specific directory."""
        workspace_root = DB["workspace_root"]
        src_path = f"{workspace_root}/src"
        
        # Search for "class" pattern in src directory
        results = grep_search("class", path=src_path)
        
        # Should find matches only in src directory
        for result in results:
            self.assertTrue('utils.py' in result['filePath'])

    def test_grep_search_returns_workspace_relative_path(self):
        """Test that grep search returns workspace relative path."""
        workspace_root = DB["workspace_root"]
        src_path = f"{workspace_root}/src"
        
        # Search for "class" pattern in src directory
        results = grep_search("class", path=src_path)
        for result in results:
            self.assertTrue(result['filePath'].startswith('src/'))

    def test_grep_search_returns_workspace_relative_path_with_subdirectories(self):
        """Test that grep search returns workspace relative path with subdirectories."""
        workspace_root = DB["workspace_root"]
        path = f"{workspace_root}/"
        
        # Search for "utility" pattern in root directory which is only in src/utils.py
        results = grep_search("utility", path=path)
        for result in results:
            self.assertEqual(result['filePath'], 'src/utils.py')

    def test_grep_search_with_include_filter(self):
        """Test include filter for specific file types."""
        # Search for "import" pattern in Python files only
        results = grep_search("import", include="*.py")
        
        # Should find matches only in .py files
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertTrue(result['filePath'].endswith('.py'))

    def test_grep_search_with_brace_expansion(self):
        """Test include filter with brace expansion."""
        # Search for "test" pattern in Python and JavaScript files
        results = grep_search("test", include="*.{py,js}")
        
        # Should find matches in both .py and .js files
        self.assertGreater(len(results), 0)
        
        # Verify file extensions
        found_extensions = set()
        for result in results:
            _, ext = os.path.splitext(result['filePath'])
            found_extensions.add(ext)
        
        # Should have found at least one of the expected extensions
        self.assertTrue(found_extensions.intersection({'.py', '.js'}))

    def test_grep_search_no_matches(self):
        """Test pattern with no matches."""
        results = grep_search("nonexistent_pattern_xyz")
        
        # Should return empty list
        self.assertEqual(len(results), 0)

    def test_grep_search_ignores_directories(self):
        """Test that node_modules and other directories are ignored."""
        # Search for "module" pattern - should ignore node_modules
        results = grep_search("module")
        
        # Should not find matches in node_modules directory
        for result in results:
            self.assertNotIn('node_modules', result['filePath'])

    def test_grep_search_binary_files_ignored(self):
        """Test that binary files are ignored."""
        workspace_root = DB["workspace_root"]
        
        # Add a binary file to the filesystem
        DB["file_system"][f"{workspace_root}/image.jpg"] = {
            "path": f"{workspace_root}/image.jpg",
            "is_directory": False,
            "size_bytes": 1000,
            "last_modified": "2024-01-01T00:00:00Z",
            "content_lines": ["binary content with text"]
        }
        
        # Search for "text" pattern
        results = grep_search("text")
        
        # Should not find matches in binary files
        for result in results:
            self.assertNotIn('image.jpg', result['filePath'])

    def test_grep_search_sorting(self):
        """Test that results are sorted by file path and line number."""
        results = grep_search("def")
        
        # Should be sorted by file path, then by line number
        if len(results) > 1:
            for i in range(len(results) - 1):
                curr = results[i]
                next_result = results[i + 1]
                
                # If same file, line numbers should be in order
                if curr['filePath'] == next_result['filePath']:
                    self.assertLessEqual(curr['lineNumber'], next_result['lineNumber'])
                else:
                    # File paths should be in order
                    self.assertLess(curr['filePath'], next_result['filePath'])

    def test_grep_search_match_positions(self):
        """Test that results contain the expected pattern."""
        results = grep_search("def")
        
        for result in results:
            line_content = result['line']
            
            # Line content should contain the pattern (case insensitive)
            self.assertIn('def', line_content.lower())

    # Error handling tests
    def test_grep_search_empty_pattern(self):
        """Test error handling for empty pattern."""
        with self.assertRaises(InvalidInputError) as cm:
            grep_search("")
        self.assertIn("non-empty string", str(cm.exception))

    def test_grep_search_non_string_pattern(self):
        """Test error handling for non-string pattern."""
        with self.assertRaises(InvalidInputError) as cm:
            grep_search(123)
        self.assertIn("non-empty string", str(cm.exception))

    def test_grep_search_invalid_regex(self):
        """Test error handling for invalid regex pattern."""
        with self.assertRaises(InvalidInputError) as cm:
            grep_search("[invalid_regex")
        self.assertIn("Invalid regular expression pattern", str(cm.exception))

    def test_grep_search_invalid_path_type(self):
        """Test error handling for invalid path type."""
        with self.assertRaises(InvalidInputError) as cm:
            grep_search("test", path=123)
        self.assertIn("string or None", str(cm.exception))

    def test_grep_search_empty_path(self):
        """Test empty path (now supported - maps to workspace root)."""
        results = grep_search("test", path="")
        # Should work and return search results from workspace root
        self.assertIsInstance(results, list)

    def test_grep_search_relative_path(self):
        """Test relative path (now supported)."""
        # Since relative/path doesn't exist, this should raise FileNotFoundError
        with self.assertRaises(FileNotFoundError) as cm:
            grep_search("test", path="relative/path")
        self.assertIn("Search path does not exist", str(cm.exception))

    def test_grep_search_path_outside_workspace(self):
        """Test path outside workspace (now treated as relative)."""
        # Paths with leading slashes are now treated as relative, so this creates
        # a path like workspace_root/outside/workspace which doesn't exist
        with self.assertRaises(FileNotFoundError) as cm:
            grep_search("test", path="/outside/workspace")
        self.assertIn("Search path does not exist", str(cm.exception))

    def test_grep_search_invalid_include_type(self):
        """Test error handling for invalid include type."""
        with self.assertRaises(InvalidInputError) as cm:
            grep_search("test", include=123)
        self.assertIn("non-empty string or None", str(cm.exception))

    def test_grep_search_empty_include(self):
        """Test error handling for empty include."""
        with self.assertRaises(InvalidInputError) as cm:
            grep_search("test", include="")
        self.assertIn("non-empty string or None", str(cm.exception))

    def test_grep_search_workspace_not_available(self):
        """Test error handling when workspace is not configured."""
        # Clear workspace configuration
        if "workspace_root" in DB:
            del DB["workspace_root"]
        
        with self.assertRaises(WorkspaceNotAvailableError) as cm:
            grep_search("test")
        self.assertIn("workspace_root not configured", str(cm.exception))

    def test_grep_search_path_not_found(self):
        """Test error handling for non-existent path."""
        workspace_root = DB["workspace_root"]
        
        with self.assertRaises(FileNotFoundError) as cm:
            grep_search("test", path=f"{workspace_root}/nonexistent")
        self.assertIn("Search path does not exist", str(cm.exception))

    def test_grep_search_path_not_directory(self):
        """Test error handling for path that is not a directory."""
        workspace_root = DB["workspace_root"]
        
        with self.assertRaises(NotADirectoryError) as cm:
            grep_search("test", path=f"{workspace_root}/main.py")
        self.assertIn("Search path is not a directory", str(cm.exception))

    def test_grep_search_complex_regex(self):
        """Test complex regex patterns."""
        # Search for import statements with regex (without ^ anchor since we're matching within lines)
        results = grep_search(r"import\s+\w+")
        
        # Should find import statements
        self.assertGreater(len(results), 0)
        
        # Verify matches contain "import" (case insensitive since our search is case insensitive)
        for result in results:
            self.assertIn('import', result['line'].lower())

    def test_grep_search_multiline_content(self):
        """Test searching in multiline content."""
        # Search for docstring pattern
        results = grep_search('"""')
        
        # Should find docstring markers
        self.assertGreater(len(results), 0)
        
        # Verify matches contain triple quotes
        for result in results:
            self.assertIn('"""', result['line'])


if __name__ == '__main__':
    unittest.main() 