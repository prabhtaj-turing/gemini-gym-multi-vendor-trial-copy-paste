#!/usr/bin/env python3
"""
Tests for terminal models module.

This module tests the Pydantic models in terminal.SimulationEngine.models module.
"""

import unittest
import os
import sys
from pydantic import ValidationError

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from terminal.SimulationEngine.models import (
    FileSystemEntry,
    TerminalDB,
    DatabaseFileSystemEntry,
    validate_iso_8601_string
)
from terminal.SimulationEngine.custom_errors import InvalidDateTimeFormatError


class TestTerminalModels(unittest.TestCase):
    """Test cases for terminal models module."""

    def test_validate_iso_8601_string_valid(self):
        """Test validate_iso_8601_string with valid ISO 8601 strings."""
        # Test with Z suffix
        result = validate_iso_8601_string("2024-01-01T00:00:00Z")
        self.assertEqual(result, "2024-01-01T00:00:00Z")
        
        # Test with timezone offset
        result = validate_iso_8601_string("2024-01-01T00:00:00+00:00")
        self.assertEqual(result, "2024-01-01T00:00:00+00:00")
        
        # Test with None (should return None)
        result = validate_iso_8601_string(None)
        self.assertIsNone(result)

    def test_validate_iso_8601_string_invalid(self):
        """Test validate_iso_8601_string with invalid inputs."""
        # Test with invalid format
        with self.assertRaises(InvalidDateTimeFormatError):
            validate_iso_8601_string("2024-13-01T00:00:00Z")
        
        # Test with non-string type
        with self.assertRaises(InvalidDateTimeFormatError):
            validate_iso_8601_string(123)
        
        # Test with invalid string
        with self.assertRaises(InvalidDateTimeFormatError):
            validate_iso_8601_string("not a datetime")

    def test_file_system_entry_creation(self):
        """Test FileSystemEntry model creation."""
        # Test with all required fields
        entry = FileSystemEntry(
            path="/workspace/file.txt",
            is_directory=False,
            content_lines=["line1\n", "line2\n"],
            size_bytes=12,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        self.assertEqual(entry.path, "/workspace/file.txt")
        self.assertFalse(entry.is_directory)
        self.assertEqual(entry.content_lines, ["line1\n", "line2\n"])
        self.assertEqual(entry.size_bytes, 12)
        self.assertEqual(entry.last_modified, "2024-01-01T00:00:00Z")

    def test_file_system_entry_defaults(self):
        """Test FileSystemEntry default values."""
        entry = FileSystemEntry(
            path="/workspace/file.txt",
            is_directory=False,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        # Default values
        self.assertEqual(entry.content_lines, [])
        self.assertEqual(entry.size_bytes, 0)

    def test_file_system_entry_forbids_extra_fields(self):
        """Test FileSystemEntry rejects extra fields."""
        with self.assertRaises(ValidationError):
            FileSystemEntry(
                path="/workspace/file.txt",
                is_directory=False,
                last_modified="2024-01-01T00:00:00Z",
                extra_field="not_allowed"
            )

    def test_terminal_db_creation(self):
        """Test TerminalDB model creation."""
        db = TerminalDB(
            workspace_root="/workspace",
            cwd="/workspace",
            file_system={
                "/workspace": {
                    "path": "/workspace",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-01-01T00:00:00Z"
                }
            },
            environment={},
            background_processes={},
            _next_pid=1
        )
        
        self.assertEqual(db.workspace_root, "/workspace")
        self.assertEqual(db.cwd, "/workspace")
        self.assertEqual(db.next_pid, 1)

    def test_terminal_db_with_alias(self):
        """Test TerminalDB with _next_pid alias."""
        db = TerminalDB(
            workspace_root="/workspace",
            cwd="/workspace",
            file_system={},
            _next_pid=5
        )
        
        self.assertEqual(db.next_pid, 5)

    def test_terminal_db_defaults(self):
        """Test TerminalDB default values."""
        db = TerminalDB(
            workspace_root="/workspace",
            cwd="/workspace",
            file_system={}
        )
        
        self.assertEqual(db.environment, {})
        self.assertEqual(db.background_processes, {})
        self.assertEqual(db.next_pid, 1)

    def test_terminal_db_file_system_validation(self):
        """Test TerminalDB file_system validator."""
        # Test with missing 'path' field
        with self.assertRaises(ValidationError) as context:
            TerminalDB(
                workspace_root="/workspace",
                cwd="/workspace",
                file_system={
                    "/workspace/file.txt": {
                        "is_directory": False,
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": "2024-01-01T00:00:00Z"
                    }
                }
            )
        
        self.assertIn("missing 'path' field", str(context.exception))

    def test_terminal_db_file_system_path_mismatch(self):
        """Test TerminalDB file_system validator with path mismatch."""
        # Test with path key not matching entry path
        with self.assertRaises(ValidationError) as context:
            TerminalDB(
                workspace_root="/workspace",
                cwd="/workspace",
                file_system={
                    "/workspace/file.txt": {
                        "path": "/workspace/different.txt",  # Mismatch!
                        "is_directory": False,
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": "2024-01-01T00:00:00Z"
                    }
                }
            )
        
        self.assertIn("doesn't match entry path", str(context.exception))

    def test_terminal_db_file_system_missing_required_fields(self):
        """Test TerminalDB file_system validator with missing required fields."""
        # Test with missing 'is_directory' field
        with self.assertRaises(ValidationError) as context:
            TerminalDB(
                workspace_root="/workspace",
                cwd="/workspace",
                file_system={
                    "/workspace/file.txt": {
                        "path": "/workspace/file.txt",
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": "2024-01-01T00:00:00Z"
                    }
                }
            )
        
        self.assertIn("missing required field 'is_directory'", str(context.exception))

    def test_terminal_db_path_validation(self):
        """Test TerminalDB workspace_root and cwd validators."""
        # Test with empty workspace_root
        with self.assertRaises(ValidationError):
            TerminalDB(
                workspace_root="",
                cwd="/workspace",
                file_system={}
            )
        
        # Test with empty cwd
        with self.assertRaises(ValidationError):
            TerminalDB(
                workspace_root="/workspace",
                cwd="",
                file_system={}
            )

    def test_database_file_system_entry_creation(self):
        """Test DatabaseFileSystemEntry model creation."""
        entry = DatabaseFileSystemEntry(
            path="/workspace/file.txt",
            is_directory=False,
            content_lines=["data\n"],
            size_bytes=5,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        self.assertEqual(entry.path, "/workspace/file.txt")
        self.assertFalse(entry.is_directory)
        self.assertEqual(entry.content_lines, ["data\n"])
        self.assertEqual(entry.size_bytes, 5)

    def test_database_file_system_entry_path_validation(self):
        """Test DatabaseFileSystemEntry path validator."""
        # Test with empty path
        with self.assertRaises(ValidationError):
            DatabaseFileSystemEntry(
                path="",
                is_directory=False,
                last_modified="2024-01-01T00:00:00Z"
            )

    def test_database_file_system_entry_content_lines_validation(self):
        """Test DatabaseFileSystemEntry content_lines validator."""
        # Test directory with non-empty content_lines (should fail)
        with self.assertRaises(ValidationError) as context:
            DatabaseFileSystemEntry(
                path="/workspace/dir",
                is_directory=True,
                content_lines=["should be empty\n"],
                last_modified="2024-01-01T00:00:00Z"
            )
        
        self.assertIn("Directories should have empty content_lines", str(context.exception))

    def test_database_file_system_entry_size_bytes_validation(self):
        """Test DatabaseFileSystemEntry size_bytes validator."""
        # Test with negative size_bytes
        with self.assertRaises(ValidationError) as context:
            DatabaseFileSystemEntry(
                path="/workspace/file.txt",
                is_directory=False,
                size_bytes=-1,
                last_modified="2024-01-01T00:00:00Z"
            )
        
        self.assertIn("size_bytes must be non-negative", str(context.exception))

    def test_database_file_system_entry_last_modified_validation(self):
        """Test DatabaseFileSystemEntry last_modified validator."""
        # Test with invalid timestamp
        with self.assertRaises((ValidationError, InvalidDateTimeFormatError)):
            DatabaseFileSystemEntry(
                path="/workspace/file.txt",
                is_directory=False,
                last_modified="invalid timestamp"
            )

    def test_terminal_db_forbids_extra_fields(self):
        """Test TerminalDB rejects extra fields."""
        with self.assertRaises(ValidationError):
            TerminalDB(
                workspace_root="/workspace",
                cwd="/workspace",
                file_system={},
                extra_field="not_allowed"
            )

    def test_database_file_system_entry_forbids_extra_fields(self):
        """Test DatabaseFileSystemEntry rejects extra fields."""
        with self.assertRaises(ValidationError):
            DatabaseFileSystemEntry(
                path="/workspace/file.txt",
                is_directory=False,
                last_modified="2024-01-01T00:00:00Z",
                extra_field="not_allowed"
            )

    def test_terminal_db_serialization(self):
        """Test TerminalDB serialization."""
        db = TerminalDB(
            workspace_root="/workspace",
            cwd="/workspace",
            file_system={
                "/workspace": {
                    "path": "/workspace",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-01-01T00:00:00Z"
                }
            }
        )
        
        data = db.model_dump()
        self.assertEqual(data["workspace_root"], "/workspace")
        self.assertEqual(data["cwd"], "/workspace")
        self.assertIn("/workspace", data["file_system"])

    def test_terminal_db_deserialization(self):
        """Test TerminalDB deserialization."""
        data = {
            "workspace_root": "/workspace",
            "cwd": "/workspace",
            "file_system": {
                "/workspace": {
                    "path": "/workspace",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-01-01T00:00:00Z"
                }
            }
        }
        
        db = TerminalDB.model_validate(data)
        self.assertEqual(db.workspace_root, "/workspace")
        self.assertEqual(db.cwd, "/workspace")


if __name__ == '__main__':
    unittest.main()
