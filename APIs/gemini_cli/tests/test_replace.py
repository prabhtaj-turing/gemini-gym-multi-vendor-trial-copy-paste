"""Tests for the replace function in gemini_cli.file_system_api."""

import pytest
import datetime
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli.file_system_api import replace  # noqa: E402
from gemini_cli.SimulationEngine.db import DB  # noqa: E402
from gemini_cli.SimulationEngine.custom_errors import (  # noqa: E402
    InvalidInputError,
    WorkspaceNotAvailableError,
)


class TestReplace:
    """Test suite for the replace function."""

    def setup_method(self):
        """Set up test database before each test."""
        # Clear the database
        DB.clear()
        
        # Set up workspace
        DB["workspace_root"] = "/workspace"
        DB["file_system"] = {
            "/workspace": {
                "path": "/workspace",
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": "2024-01-01T12:00:00Z",
            },
            "/workspace/test.py": {
                "path": "/workspace/test.py",
                "is_directory": False,
                "content_lines": [
                    "def hello():\n",
                    "    print('Hello, World!')\n",
                    "    return 'success'\n",
                ],
                "size_bytes": 56,
                "last_modified": "2024-01-01T12:00:00Z",
            },
            "/workspace/multi.py": {
                "path": "/workspace/multi.py",
                "is_directory": False,
                "content_lines": [
                    "def func1():\n",
                    "    print('old')\n",
                    "def func2():\n",
                    "    print('old')\n",
                    "def func3():\n",
                    "    print('old')\n",
                ],
                "size_bytes": 74,
                "last_modified": "2024-01-01T12:00:00Z",
            },
        }

    def test_basic_single_replacement(self):
        """Test basic single string replacement."""
        result = replace(
            file_path="/workspace/test.py",
            old_string="    print('Hello, World!')",
            new_string="    print('Hello, Python!')",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        assert result["is_new_file"] is False
        assert "Modified file 'test.py' (1 replacements)" in result["message"]
        assert "Hello, Python!" in result["content_preview"]
        
        # Verify file was updated in DB
        updated_content = "".join(DB["file_system"]["/workspace/test.py"]["content_lines"])
        assert "Hello, Python!" in updated_content
        assert "Hello, World!" not in updated_content

    def test_multiple_replacements(self):
        """Test replacing multiple occurrences."""
        result = replace(
            file_path="/workspace/multi.py",
            old_string="    print('old')",
            new_string="    print('new')",
            expected_replacements=3,
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 3
        assert result["is_new_file"] is False
        assert "Modified file 'multi.py' (3 replacements)" in result["message"]
        
        # Verify all occurrences were replaced
        updated_content = "".join(DB["file_system"]["/workspace/multi.py"]["content_lines"])
        assert updated_content.count("print('new')") == 3
        assert "print('old')" not in updated_content

    def test_create_new_file(self):
        """Test creating a new file with empty old_string."""
        result = replace(
            file_path="/workspace/new_file.py",
            old_string="",
            new_string="def new_function():\n    return 'new'\n",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 0
        assert result["is_new_file"] is True
        assert "Created file 'new_file.py'" in result["message"]
        assert "def new_function():" in result["content_preview"]
        
        # Verify file was created in DB
        assert "/workspace/new_file.py" in DB["file_system"]
        new_file = DB["file_system"]["/workspace/new_file.py"]
        assert new_file["is_directory"] is False
        content = "".join(new_file["content_lines"])
        assert "def new_function():" in content

    def test_create_new_file_with_parent_directory(self):
        """Test creating a new file in a non-existent parent directory."""
        result = replace(
            file_path="/workspace/subdir/new_file.py",
            old_string="",
            new_string="# New file in subdir\n",
        )
        
        assert result["success"] is True
        assert result["is_new_file"] is True
        
        # Verify parent directory was created
        assert "/workspace/subdir" in DB["file_system"]
        parent_dir = DB["file_system"]["/workspace/subdir"]
        assert parent_dir["is_directory"] is True
        
        # Verify file was created
        assert "/workspace/subdir/new_file.py" in DB["file_system"]

    def test_string_with_context_replacement(self):
        """Test replacement with context (like the TypeScript version expects)."""
        result = replace(
            file_path="/workspace/test.py",
            old_string="def hello():\n    print('Hello, World!')\n    return 'success'",
            new_string="def hello():\n    print('Hello, Universe!')\n    return 'updated'",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        
        # Verify replacement with context
        updated_content = "".join(DB["file_system"]["/workspace/test.py"]["content_lines"])
        assert "Hello, Universe!" in updated_content
        assert "return 'updated'" in updated_content

    def test_no_matches_found_error(self):
        """Test error when old_string is not found."""
        with pytest.raises(RuntimeError, match="Expected 1 occurrence but found 0"):
            replace(
                file_path="/workspace/test.py",
                old_string="nonexistent_string",
                new_string="replacement",
            )

    def test_wrong_number_of_matches_error(self):
        """Test error when found occurrences don't match expected."""
        with pytest.raises(RuntimeError, match="Expected 5 occurrences but found 3"):
            replace(
                file_path="/workspace/multi.py",
                old_string="    print('old')",
                new_string="    print('new')",
                expected_replacements=5,
            )

    def test_file_not_found_error(self):
        """Test error when trying to edit non-existent file."""
        with pytest.raises(FileNotFoundError, match="File '/workspace/nonexistent.py' not found"):
            replace(
                file_path="/workspace/nonexistent.py",
                old_string="something",
                new_string="replacement",
            )

    def test_create_existing_file_error(self):
        """Test error when trying to create a file that already exists."""
        with pytest.raises(FileExistsError, match="already exists. Cannot create existing file"):
            replace(
                file_path="/workspace/test.py",
                old_string="",  # Empty old_string means create new file
                new_string="new content",
            )

    def test_replace_with_no_trailing_newline(self):
        """Test replacement with no trailing newline."""
        DB["file_system"]["/workspace/test1.py"] = {
            "path": "/workspace/test1.py",
            "is_directory": False,
            "content_lines": [
                "print('Hello, World!')",
            ],
            "size_bytes": 19,
            "last_modified": "2024-01-01T12:00:00Z",
        }
        result = replace(
            file_path="/workspace/test1.py",
            old_string="print('Hello, World!')",
            new_string="print('Hello, Python!')",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        assert result["is_new_file"] is False
        assert "Modified file 'test1.py' (1 replacements)" in result["message"]
        assert "Hello, Python!" in result["content_preview"]
        
        # Verify file was updated in DB
        updated_content = "".join(DB["file_system"]["/workspace/test1.py"]["content_lines"])
        assert "Hello, Python!" in updated_content
        assert updated_content.endswith("\n") is False

    def test_replace_with_no_whitespace_normalization(self):
        """Test replacement with no whitespace normalization."""
        # Add file with mixed whitespace
        DB["file_system"]["/workspace/whitespace.py"] = {
            "path": "/workspace/whitespace.py",
            "is_directory": False,
            "content_lines": [
                "def\ttab_function():\n",  # Tab
                "    print('test')\n",      # Spaces
            ],
            "size_bytes": 35,
            "last_modified": "2024-01-01T12:00:00Z",
        }
        result = replace(
            file_path="/workspace/whitespace.py",
            old_string="def    tab_function():",  # Spaces instead of tab
            new_string="def space_function():",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        assert result["is_new_file"] is False
        assert "Modified file 'whitespace.py' (1 replacements)" in result["message"]
        assert "def space_function():" in result["content_preview"]
        
        # Verify file was updated in DB
        updated_content = "".join(DB["file_system"]["/workspace/whitespace.py"]["content_lines"])
        assert "def space_function():" in updated_content
        assert "def    tab_function():" not in updated_content
        assert "    print('test')" in updated_content

    def test_replace_with_multiple_lines_replacement(self):
        """Test replacement with multiple lines replacement."""
        DB["file_system"]["/workspace/multi.py"] = {
            "path": "/workspace/multi.py",
            "is_directory": False,
            "content_lines": [
                "\tprint('old')\n",
                "\tprint('old1')\n",
                "\tprint('old2')",
            ],
            "size_bytes": 74,
            "last_modified": "2024-01-01T12:00:00Z",
        }
        result = replace(
            file_path="/workspace/multi.py",
            old_string="\tprint('old')\n\tprint('old1')\n\tprint('old2')",
            new_string="\tprint('new')\n\tprint('new1')\n\tprint('new2')",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        assert result["is_new_file"] is False
        assert "new" in result["content_preview"]
        assert "new1" in result["content_preview"]
        assert "new2" in result["content_preview"]
        assert "old" not in result["content_preview"]
        assert "old1" not in result["content_preview"]
        assert "old2" not in result["content_preview"]
        
        updated_content = "".join(DB["file_system"]["/workspace/multi.py"]["content_lines"])
        assert updated_content.endswith("\n") is False
        assert "\n\t" in updated_content



    def test_directory_target_error(self):
        """Test error when file_path points to a directory."""
        with pytest.raises(IsADirectoryError, match="Path '/workspace' is a directory"):
            replace(
                file_path="/workspace",
                old_string="something",
                new_string="replacement",
            )

    def test_invalid_file_path_parameter(self):
        """Test validation of file_path parameter."""
        with pytest.raises(InvalidInputError, match="'file_path' must be a non-empty string"):
            replace(
                file_path="",
                old_string="old",
                new_string="new",
            )
        
        with pytest.raises(InvalidInputError, match="'file_path' must be a string"):
            replace(
                file_path=None,  # type: ignore
                old_string="old",
                new_string="new",
            )

    def test_invalid_old_string_parameter(self):
        """Test validation of old_string parameter."""
        with pytest.raises(InvalidInputError, match="'old_string' must be a string"):
            replace(
                file_path="/workspace/test.py",
                old_string=123,  # type: ignore
                new_string="new",
            )

    def test_invalid_new_string_parameter(self):
        """Test validation of new_string parameter."""
        with pytest.raises(InvalidInputError, match="'new_string' must be a string"):
            replace(
                file_path="/workspace/test.py",
                old_string="old",
                new_string=None,  # type: ignore
            )

    def test_invalid_expected_replacements_parameter(self):
        """Test validation of expected_replacements parameter."""
        with pytest.raises(InvalidInputError, match="'expected_replacements' must be a positive integer"):
            replace(
                file_path="/workspace/test.py",
                old_string="old",
                new_string="new",
                expected_replacements=0,
            )
        
        with pytest.raises(InvalidInputError, match="'expected_replacements' must be a positive integer"):
            replace(
                file_path="/workspace/test.py",
                old_string="old",
                new_string="new",
                expected_replacements=-1,
            )

    def test_relative_path_error(self):
        """Test relative file paths (now supported, but this file doesn't exist)."""
        with pytest.raises(FileNotFoundError, match="not found"):
            replace(
                file_path="relative/path.py",
                old_string="old",
                new_string="new",
            )

    def test_workspace_not_configured_error(self):
        """Test error when workspace_root is not configured."""
        DB.clear()  # Remove workspace configuration
        
        with pytest.raises(WorkspaceNotAvailableError, match="workspace_root not configured"):
            replace(
                file_path="/workspace/test.py",
                old_string="old",
                new_string="new",
            )

    def test_path_outside_workspace_error(self):
        """Test path outside workspace (now treated as relative, file doesn't exist)."""
        with pytest.raises(FileNotFoundError, match="not found"):
            replace(
                file_path="/outside/file.py",
                old_string="old",
                new_string="new",
            )

    def test_whitespace_preservation(self):
        """Test that whitespace is preserved correctly."""
        result = replace(
            file_path="/workspace/test.py",
            old_string="def hello():\n    print('Hello, World!')",
            new_string="def hello():\n        print('Hello, World!')",  # Added extra indentation
        )
        
        assert result["success"] is True
        
        # Verify whitespace is preserved
        updated_content = "".join(DB["file_system"]["/workspace/test.py"]["content_lines"])
        assert "        print('Hello, World!')" in updated_content  # 8 spaces

    def test_empty_file_replacement(self):
        """Test replacement in an empty file."""
        # Create empty file
        DB["file_system"]["/workspace/empty.py"] = {
            "path": "/workspace/empty.py",
            "is_directory": False,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-01-01T12:00:00Z",
        }
        
        # Should get 0 occurrences for any non-empty string
        with pytest.raises(RuntimeError, match="Expected 1 occurrence but found 0"):
            replace(
                file_path="/workspace/empty.py",
                old_string="anything",
                new_string="replacement",
            )

    def test_multiline_replacement(self):
        """Test replacement with multiline strings."""
        multiline_old = """def hello():
    print('Hello, World!')
    return 'success'"""
        
        multiline_new = """def hello():
    print('Goodbye, World!')
    return 'farewell'"""
        
        result = replace(
            file_path="/workspace/test.py",
            old_string=multiline_old,
            new_string=multiline_new,
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        
        # Verify multiline replacement
        updated_content = "".join(DB["file_system"]["/workspace/test.py"]["content_lines"])
        assert "Goodbye, World!" in updated_content
        assert "return 'farewell'" in updated_content

    def test_special_characters_replacement(self):
        """Test replacement with special characters."""
        # Add file with special characters
        DB["file_system"]["/workspace/special.py"] = {
            "path": "/workspace/special.py",
            "is_directory": False,
            "content_lines": [
                "# Special chars: @#$%^&*()\n",
                "regex = r'\\d+'\n",
                "quote = \"It's a 'test'\"\n",
            ],
            "size_bytes": 50,
            "last_modified": "2024-01-01T12:00:00Z",
        }
        
        result = replace(
            file_path="/workspace/special.py",
            old_string="regex = r'\\d+'",
            new_string="regex = r'\\w+'",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        
        # Verify special characters handled correctly
        updated_content = "".join(DB["file_system"]["/workspace/special.py"]["content_lines"])
        assert "regex = r'\\w+'" in updated_content

    def test_unicode_replacement(self):
        """Test replacement with Unicode characters."""
        # Add file with Unicode
        DB["file_system"]["/workspace/unicode.py"] = {
            "path": "/workspace/unicode.py",
            "is_directory": False,
            "content_lines": [
                "# Unicode: π ≈ 3.14\n",
                "greeting = '你好世界'\n",
            ],
            "size_bytes": 40,
            "last_modified": "2024-01-01T12:00:00Z",
        }
        
        result = replace(
            file_path="/workspace/unicode.py",
            old_string="greeting = '你好世界'",
            new_string="greeting = 'Hello World'",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1
        
        # Verify Unicode replacement
        updated_content = "".join(DB["file_system"]["/workspace/unicode.py"]["content_lines"])
        assert "Hello World" in updated_content
        assert "你好世界" not in updated_content

    def test_content_preview_truncation(self):
        """Test that content preview is truncated for long content."""
        long_content = "def long_function():\n" + "    # " + "x" * 300 + "\n    pass\n"
        
        result = replace(
            file_path="/workspace/new_long.py",
            old_string="",
            new_string=long_content,
        )
        
        assert result["success"] is True
        assert result["is_new_file"] is True
        assert len(result["content_preview"]) <= 203  # 200 + "..."
        assert result["content_preview"].endswith("...")

    def test_file_size_calculation(self):
        """Test that file size is calculated correctly."""
        content = "def test():\n    return 'test'\n"
        
        result = replace(
            file_path="/workspace/size_test.py",
            old_string="",
            new_string=content,
        )
        
        assert result["success"] is True
        
        # Verify file size in DB
        file_entry = DB["file_system"]["/workspace/size_test.py"]
        expected_size = len(content.encode('utf-8'))
        assert file_entry["size_bytes"] == expected_size

    def test_timestamp_updated(self):
        """Test that file timestamp is updated after replacement."""
        original_timestamp = DB["file_system"]["/workspace/test.py"]["last_modified"]
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.datetime(2024, 6, 15, 14, 30, 0)
            mock_datetime.now.return_value.isoformat.return_value = "2024-06-15T14:30:00"
            
            result = replace(
                file_path="/workspace/test.py",
                old_string="print('Hello, World!')",
                new_string="print('Hello, Test!')",
            )
        
        assert result["success"] is True
        
        # Verify timestamp was updated
        updated_timestamp = DB["file_system"]["/workspace/test.py"]["last_modified"]
        assert updated_timestamp != original_timestamp
        assert "2024-06-15T14:30:00Z" in updated_timestamp

    def test_self_correction_basic_unescaping(self):
        """Test self-correction with basic string unescaping."""
        # Test with escaped quotes
        result = replace(
            file_path="/workspace/test.py",
            old_string="    print(\\'Hello, World!\\')",  # Escaped quotes
            new_string="    print('Hello, Python!')",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1

    def test_self_correction_whitespace_normalization(self):
        """Test self-correction with whitespace normalization."""
        # Add file with mixed whitespace
        DB["file_system"]["/workspace/whitespace.py"] = {
            "path": "/workspace/whitespace.py",
            "is_directory": False,
            "content_lines": [
                "def\ttab_function():\n",  # Tab
                "    print('test')\n",      # Spaces
            ],
            "size_bytes": 35,
            "last_modified": "2024-01-01T12:00:00Z",
        }
        
        # Try to match with different whitespace
        result = replace(
            file_path="/workspace/whitespace.py",
            old_string="def    tab_function():",  # Spaces instead of tab
            new_string="def space_function():",
        )
        
        assert result["success"] is True
        assert result["replacements_made"] == 1

    def test_modified_by_user_true(self):
        """Test replace with modified_by_user set to True."""
        result = replace(
            file_path="/workspace/test.py",
            old_string="    print('Hello, World!')",
            new_string="    print('Hello, User!')",
            modified_by_user=True,
        )
        
        assert result["success"] is True
        assert result["modified_by_user"] is True
        assert "User modified the new_string content to be" in result["message"]
        assert "Hello, User!" in result["message"]

    def test_modified_by_user_false(self):
        """Test replace with modified_by_user set to False."""
        result = replace(
            file_path="/workspace/test.py",
            old_string="    print('Hello, World!')",
            new_string="    print('Hello, System!')",
            modified_by_user=False,
        )
        
        assert result["success"] is True
        assert result["modified_by_user"] is False
        assert "User modified" not in result["message"]

    def test_modified_by_user_none_default(self):
        """Test replace with modified_by_user not specified (None)."""
        result = replace(
            file_path="/workspace/test.py",
            old_string="    print('Hello, World!')",
            new_string="    print('Hello, Default!')",
        )
        
        assert result["success"] is True
        assert result["modified_by_user"] is False
        assert "User modified" not in result["message"]

    def test_modified_by_user_with_new_file_creation(self):
        """Test modified_by_user with new file creation."""
        result = replace(
            file_path="/workspace/user_modified.py",
            old_string="",
            new_string="# User created this file\nprint('hello')\n",
            modified_by_user=True,
        )
        
        assert result["success"] is True
        assert result["is_new_file"] is True
        assert result["modified_by_user"] is True
        assert "User modified the new_string content to be" in result["message"]

    def test_invalid_modified_by_user_parameter(self):
        """Test validation of modified_by_user parameter."""
        with pytest.raises(InvalidInputError, match="'modified_by_user' must be a boolean or None"):
            replace(
                file_path="/workspace/test.py",
                old_string="old",
                new_string="new",
                modified_by_user="not_a_boolean",  # type: ignore
            )
        
        with pytest.raises(InvalidInputError, match="'modified_by_user' must be a boolean or None"):
            replace(
                file_path="/workspace/test.py",
                old_string="old",
                new_string="new",
                modified_by_user=1,  # type: ignore
            ) 