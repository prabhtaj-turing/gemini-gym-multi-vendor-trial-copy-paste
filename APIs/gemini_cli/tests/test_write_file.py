import json
import os
import sys
from pathlib import Path
from unittest.mock import patch
import datetime

import pytest

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from gemini_cli import write_file  # noqa: E402
from gemini_cli.SimulationEngine import db as sim_db  # noqa: E402
from gemini_cli.SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotAvailableError  # noqa: E402

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "GeminiCliDefaultDB.json"


@pytest.fixture(autouse=True)
def reload_db():
    """Load fresh DB snapshot before each test."""
    sim_db.DB.clear()
    with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
        sim_db.DB.update(json.load(fh))
    yield
    sim_db.DB.clear()


class TestWriteFile:
    """Test suite for write_file function."""

    def test_write_new_file_success(self):
        """Test successfully creating a new file."""
        file_path = "/home/user/project/new_file.txt"
        content = "Hello, World!\nThis is a new file."
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["is_new_file"] is True
        assert result["file_path"] == file_path
        assert result["size_bytes"] == len(content.encode('utf-8'))
        assert result["lines_count"] == 2
        assert "Successfully created and wrote to new file:" in result["message"]
        assert file_path in result["message"]
        
        # Verify file was created in DB
        fs = sim_db.DB["file_system"]
        assert file_path in fs
        assert fs[file_path]["is_directory"] is False
        assert "".join(fs[file_path]["content_lines"]) == content

    def test_overwrite_existing_file_success(self):
        """Test successfully overwriting an existing file."""
        file_path = "/home/user/project/README.md"
        new_content = "# Updated README\n\nThis is the new content."
        
        result = write_file(file_path, new_content)
        
        assert result["success"] is True
        assert result["is_new_file"] is False
        assert result["file_path"] == file_path
        assert result["size_bytes"] == len(new_content.encode('utf-8'))
        assert "Successfully overwrote file:" in result["message"]
        assert file_path in result["message"]
        
        # Verify file was updated in DB
        fs = sim_db.DB["file_system"]
        assert "".join(fs[file_path]["content_lines"]) == new_content

    def test_write_file_with_parent_directories(self):
        """Test creating a file with parent directories that don't exist."""
        file_path = "/home/user/project/deep/nested/structure/file.txt"
        content = "File in nested directory"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["is_new_file"] is True
        
        # Verify parent directories were created
        fs = sim_db.DB["file_system"]
        assert "/home/user/project/deep" in fs
        assert "/home/user/project/deep/nested" in fs
        assert "/home/user/project/deep/nested/structure" in fs
        assert fs["/home/user/project/deep"]["is_directory"] is True
        assert fs["/home/user/project/deep/nested"]["is_directory"] is True
        assert fs["/home/user/project/deep/nested/structure"]["is_directory"] is True

    def test_write_file_empty_content(self):
        """Test writing an empty file - FIXED to not add newline."""
        file_path = "/home/user/project/empty.txt"
        content = ""
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["size_bytes"] == 0
        assert result["lines_count"] == 0  # FIXED: Empty content = 0 lines
        
        # Verify empty file in DB - FIXED: No newline added
        fs = sim_db.DB["file_system"]
        assert fs[file_path]["content_lines"] == []

    def test_write_file_modified_by_user(self):
        """Test writing file with modified_by_user flag."""
        file_path = "/home/user/project/modified.txt"
        content = "User modified content"
        
        result = write_file(file_path, content, modified_by_user=True)
        
        assert result["success"] is True
        assert "Successfully created and wrote to new file:" in result["message"]
        assert "User modified the `content` to be:" in result["message"]
        assert content in result["message"]
        
        # Verify last_edit_params was stored
        last_edit = sim_db.DB["last_edit_params"]
        assert last_edit["tool"] == "write_file"
        assert last_edit["file_path"] == file_path
        assert last_edit["content"] == content
        assert last_edit["modified_by_user"] is True

    def test_write_file_preserves_original_content(self):
        """Test that original content is preserved without modification."""
        file_path = "/home/user/project/preserve_content.txt"
        
        # Test content without trailing newline
        content = "Line 1\nLine 2\nLine 3"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["lines_count"] == 3
        
        # Verify content was preserved exactly
        fs = sim_db.DB["file_system"]
        stored_content = "".join(fs[file_path]["content_lines"])
        assert stored_content == content  # FIXED: No newline added

    def test_write_file_with_trailing_newline(self):
        """Test content that already has trailing newline."""
        file_path = "/home/user/project/with_newline.txt"
        content = "Line 1\nLine 2\nLine 3\n"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["lines_count"] == 3
        
        # Verify content was preserved exactly
        fs = sim_db.DB["file_system"]
        stored_content = "".join(fs[file_path]["content_lines"])
        assert stored_content == content

    def test_write_file_various_line_endings(self):
        """Test writing files with different line ending styles."""
        file_path = "/home/user/project/line_endings.txt"
        
        # Test content with mixed line endings
        content = "Line 1\nLine 2\r\nLine 3\rLine 4"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["lines_count"] == 4
        
        # Verify content was preserved exactly
        fs = sim_db.DB["file_system"]
        stored_content = "".join(fs[file_path]["content_lines"])
        assert stored_content == content

    def test_write_file_unicode_content(self):
        """Test writing file with Unicode characters."""
        file_path = "/home/user/project/unicode.txt"
        content = "Hello 世界! 🌍 Café naïve résumé"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["size_bytes"] == len(content.encode('utf-8'))
        
        # Verify Unicode content was stored correctly
        fs = sim_db.DB["file_system"]
        stored_content = "".join(fs[file_path]["content_lines"])
        assert stored_content == content

    def test_write_file_timezone_aware_timestamps(self):
        """Test that timezone-aware timestamps are used."""
        file_path = "/home/user/project/timestamp_test.txt"
        content = "Testing timezone-aware timestamps"
        
        # Mock timezone-aware datetime
        mock_dt = datetime.datetime(2025, 1, 15, 12, 30, 45, tzinfo=datetime.timezone.utc)
        expected_iso = "2025-01-15T12:30:45+00:00"
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.timezone = datetime.timezone
            
            result = write_file(file_path, content)
            
            assert result["success"] is True
            
            # Verify timezone-aware timestamp was used
            fs = sim_db.DB["file_system"]
            assert fs[file_path]["last_modified"] == expected_iso
            
            # Verify last_edit_params timestamp
            last_edit = sim_db.DB["last_edit_params"]
            assert last_edit["timestamp"] == expected_iso

    def test_write_file_single_line_no_newline(self):
        """Test single line content without newline."""
        file_path = "/home/user/project/single_line.txt"
        content = "Single line without newline"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["lines_count"] == 1
        
        # Verify content preserved exactly
        fs = sim_db.DB["file_system"]
        stored_content = "".join(fs[file_path]["content_lines"])
        assert stored_content == content

    def test_write_file_multiple_empty_lines(self):
        """Test content with multiple empty lines."""
        file_path = "/home/user/project/empty_lines.txt"
        content = "Line 1\n\n\nLine 4"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["lines_count"] == 4
        
        # Verify content preserved exactly
        fs = sim_db.DB["file_system"]
        stored_content = "".join(fs[file_path]["content_lines"])
        assert stored_content == content

    # -------------------- Error Cases --------------------

    def test_invalid_file_path_empty(self):
        """Test error when file_path is empty."""
        with pytest.raises(InvalidInputError, match="'file_path' must be a non-empty string"):
            write_file("", "content")

    def test_invalid_file_path_not_string(self):
        """Test error when file_path is not a string."""
        with pytest.raises(InvalidInputError, match="'file_path' must be a string"):
            write_file(123, "content")  # type: ignore

    def test_invalid_file_path_not_absolute(self):
        """Test relative file paths (now supported)."""
        # Relative paths are now supported, so this should succeed
        result = write_file("relative/path.txt", "content")
        assert result["success"] is True
        assert result["is_new_file"] is True

    def test_invalid_content_not_string(self):
        """Test error when content is not a string."""
        with pytest.raises(InvalidInputError, match="'content' must be a string"):
            write_file("/home/user/project/file.txt", 123)  # type: ignore

    def test_invalid_modified_by_user_not_boolean(self):
        """Test error when modified_by_user is not a boolean."""
        with pytest.raises(InvalidInputError, match="'modified_by_user' must be a boolean or None"):
            write_file("/home/user/project/file.txt", "content", modified_by_user="invalid")  # type: ignore

    def test_file_path_outside_workspace(self):
        """Test path outside workspace (now treated as relative)."""
        # Paths with leading slashes are now treated as relative, so this should succeed
        result = write_file("/outside/workspace/file.txt", "content")
        assert result["success"] is True
        assert result["is_new_file"] is True

    def test_workspace_not_available(self):
        """Test error when workspace_root is not configured."""
        sim_db.DB.clear()  # Clear workspace_root
        
        with pytest.raises(WorkspaceNotAvailableError, match="workspace_root not configured in DB"):
            write_file("/home/user/project/file.txt", "content")

    def test_write_to_directory_path(self):
        """Test error when trying to write to a directory path."""
        directory_path = "/home/user/project"  # This is a directory in the default DB
        
        with pytest.raises(InvalidInputError, match="Path is a directory, not a file"):
            write_file(directory_path, "content")

    def test_write_file_preserves_content_lines_format(self):
        """Test that content_lines are properly formatted in the database."""
        file_path = "/home/user/project/multiline.txt"
        content = "Line 1\nLine 2\nLine 3\n"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        
        # Verify content_lines format
        fs = sim_db.DB["file_system"]
        content_lines = fs[file_path]["content_lines"]
        assert content_lines == ["Line 1\n", "Line 2\n", "Line 3\n"]

    def test_write_file_content_size_calculation(self):
        """Test that content size is calculated correctly for different encodings."""
        file_path = "/home/user/project/encoding_test.txt"
        content = "ASCII text and émojis 🎉"
        
        result = write_file(file_path, content)
        
        expected_size = len(content.encode('utf-8'))
        assert result["size_bytes"] == expected_size
        assert result["size_bytes"] > len(content)  # UTF-8 encoding makes it larger

    def test_write_file_last_edit_params_storage(self):
        """Test that last_edit_params are properly stored."""
        file_path = "/home/user/project/edit_params_test.txt"
        content = "Testing edit params storage"
        
        # Mock timezone-aware datetime
        mock_dt = datetime.datetime(2025, 1, 15, 12, 30, 45, tzinfo=datetime.timezone.utc)
        expected_iso = "2025-01-15T12:30:45+00:00"
        
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.timezone = datetime.timezone
            
            result = write_file(file_path, content, modified_by_user=True)
            
            assert result["success"] is True
            
            # Verify last_edit_params
            last_edit = sim_db.DB["last_edit_params"]
            assert last_edit["tool"] == "write_file"
            assert last_edit["file_path"] == file_path
            assert last_edit["content"] == content
            assert last_edit["modified_by_user"] is True
            assert last_edit["timestamp"] == expected_iso

    def test_write_file_path_normalization(self):
        """Test that file paths are properly normalized."""
        file_path = "/home/user/project/file.txt"
        content = "Testing path normalization"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        assert result["file_path"] == file_path
        
        # Verify the normalized path is used in DB
        fs = sim_db.DB["file_system"]
        assert file_path in fs 

    def test_write_file_metadata_storage(self):
        """Test that metadata is properly stored."""
        file_path = "/home/user/project/metadata_test.txt"
        content = "Testing metadata storage"
        
        result = write_file(file_path, content)
        
        assert result["success"] is True
        file_data = sim_db.DB["file_system"][file_path]
        assert file_data["metadata"] is not None
        assert file_data["metadata"]["attributes"]["is_symlink"] is False
        assert file_data["metadata"]["attributes"]["is_hidden"] is False
        assert file_data["metadata"]["attributes"]["is_readonly"] is False
        assert file_data["metadata"]["timestamps"]["access_time"] is not None
        assert file_data["metadata"]["timestamps"]["modify_time"] is not None
        assert file_data["metadata"]["timestamps"]["change_time"] is not None
        assert file_data["metadata"]["permissions"]["mode"] is not None
        assert file_data["metadata"]["permissions"]["uid"] is not None
        assert file_data["metadata"]["permissions"]["gid"] is not None

    def test_write_file_metadata_storage_with_existing_file(self):
        """Test that metadata is properly stored with existing file."""
        sim_db.DB["file_system"]["/home/user/project/metadata_test.txt"] = {
            "is_directory": False,
            "content_lines": ["content"],
            "metadata": {
                "attributes": {
                    "is_symlink": False,
                    "is_hidden": False,
                    "is_readonly": False,
                },
                "permissions": {
                    "mode": 493,
                    "uid": 1000,
                    "gid": 1000
                },
                "timestamps": {
                    "access_time": "2025-01-01T12:00:00Z",
                    "modify_time": "2025-01-01T12:00:00Z",
                    "change_time": "2025-01-01T12:00:00Z"
                }
            }
        }
        file_path = "/home/user/project/metadata_test.txt"
        content = "Testing metadata storage with existing file"
        
        result = write_file(file_path, content)
        file_data = sim_db.DB["file_system"][file_path]
        assert result["success"] is True
        assert file_data["metadata"] is not None
        assert file_data["metadata"]["attributes"]["is_symlink"] is False
        assert file_data["metadata"]["attributes"]["is_hidden"] is False
        assert file_data["metadata"]["attributes"]["is_readonly"] is False
        assert file_data["metadata"]["timestamps"]["access_time"] is not None

    def test_write_file_path_component_is_file(self):
        sim_db.DB["file_system"]["/home/user/project/file"] = {
            "is_directory": False,
            "content_lines": ["content"],
            "metadata": {
                "attributes": {
                    "is_symlink": False,
                    "is_hidden": False,
                    "is_readonly": False,
                },
            }
        }
        with pytest.raises(InvalidInputError):
            write_file("/home/user/project/file/file2.txt", "content")

    def test_write_file_create_new_directory(self):
        """Test that a new directory is created."""
        write_file("/home/user/project/new_folder/new_file.py","new content")
        assert "/home/user/project/new_folder" in sim_db.DB["file_system"]
        file_data = sim_db.DB["file_system"]["/home/user/project/new_folder"]
        assert file_data["is_directory"] is True
        assert file_data["metadata"] is not None
        assert file_data["metadata"]["attributes"]["is_symlink"] is False
        assert file_data["metadata"]["attributes"]["is_hidden"] is False
        assert file_data["metadata"]["attributes"]["is_readonly"] is False
        assert file_data["metadata"]["permissions"]["mode"] is not None
        assert file_data["metadata"]["permissions"]["uid"] is not None
        assert file_data["metadata"]["permissions"]["gid"] is not None