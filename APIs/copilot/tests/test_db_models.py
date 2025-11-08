"""
Comprehensive tests for db_models.py
Testing all Pydantic models, validators, and helper methods.
Target: ~90% code coverage
"""

import pytest
from pydantic import ValidationError
from APIs.copilot.SimulationEngine.db_models import (
    FileSystemItem,
    BackgroundProcess,
    VSCodeExtension,
    VSCodeContext,
    VSCodeAPIReference,
    CopilotDB
)


class TestFileSystemItem:
    """Tests for FileSystemItem model."""
    
    def test_valid_file(self):
        """Test creating a valid file item."""
        file_item = FileSystemItem(
            path="/home/user/project/test.py",
            is_directory=False,
            content_lines=["import sys", "print('hello')"],
            size_bytes=28,
            last_modified="2024-03-19T12:00:00Z"
        )
        assert file_item.path == "/home/user/project/test.py"
        assert not file_item.is_directory
        assert len(file_item.content_lines) == 2
        assert file_item.size_bytes == 28
    
    def test_valid_directory(self):
        """Test creating a valid directory item."""
        dir_item = FileSystemItem(
            path="/home/user/project",
            is_directory=True,
            content_lines=[],
            size_bytes=0,
            last_modified="2024-03-19T12:00:00Z"
        )
        assert dir_item.is_directory
        assert len(dir_item.content_lines) == 0
        assert dir_item.size_bytes == 0
    
    def test_default_values(self):
        """Test default values for optional fields."""
        item = FileSystemItem(
            path="/test",
            is_directory=False,
            last_modified="2024-03-19T12:00:00Z"
        )
        assert item.content_lines == []
        assert item.size_bytes == 0
        assert item.is_readonly is False
    
    def test_invalid_timestamp_format(self):
        """Test that invalid timestamp format is rejected."""
        with pytest.raises((ValidationError, Exception)) as exc_info:
            FileSystemItem(
                path="/test",
                is_directory=False,
                last_modified="invalid-timestamp"
            )
        error_str = str(exc_info.value)
        assert "Invalid timestamp format" in error_str or "InvalidDateTimeFormatError" in error_str
    
    def test_empty_timestamp(self):
        """Test that empty timestamp is rejected."""
        with pytest.raises(ValidationError):
            FileSystemItem(
                path="/test",
                is_directory=False,
                last_modified=""
            )
    
    def test_relative_path_rejected(self):
        """Test that relative paths are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FileSystemItem(
                path="relative/path",
                is_directory=False,
                last_modified="2024-03-19T12:00:00Z"
            )
        assert "must be absolute" in str(exc_info.value)
    
    def test_empty_path_rejected(self):
        """Test that empty path is rejected."""
        with pytest.raises(ValidationError):
            FileSystemItem(
                path="",
                is_directory=False,
                last_modified="2024-03-19T12:00:00Z"
            )
    
    def test_directory_with_content_rejected(self):
        """Test that directories cannot have content lines."""
        with pytest.raises(ValidationError) as exc_info:
            FileSystemItem(
                path="/test",
                is_directory=True,
                content_lines=["some content"],
                last_modified="2024-03-19T12:00:00Z"
            )
        assert "should not have content_lines" in str(exc_info.value)
    
    def test_timestamp_normalization(self):
        """Test that timestamps are normalized to ISO 8601 Z format."""
        # Space-separated format
        item = FileSystemItem(
            path="/test",
            is_directory=False,
            last_modified="2024-03-19 12:00:00"
        )
        assert item.last_modified == "2024-03-19T12:00:00Z"
        
        # With timezone offset
        item2 = FileSystemItem(
            path="/test2",
            is_directory=False,
            last_modified="2024-03-19T12:00:00+05:30"
        )
        assert item2.last_modified == "2024-03-19T06:30:00Z"  # Converted to UTC
    
    def test_negative_size_rejected(self):
        """Test that negative size is rejected."""
        with pytest.raises(ValidationError):
            FileSystemItem(
                path="/test",
                is_directory=False,
                size_bytes=-1,
                last_modified="2024-03-19T12:00:00Z"
            )
    
    def test_extra_fields_allowed(self):
        """Test that extra fields like metadata are allowed."""
        item = FileSystemItem(
            path="/test",
            is_directory=False,
            last_modified="2024-03-19T12:00:00Z",
            metadata={"custom": "field", "nested": {"key": "value"}}
        )
        assert item.path == "/test"
        # Extra fields are stored and accessible
        assert hasattr(item, 'metadata') or 'metadata' in item.__pydantic_extra__


class TestBackgroundProcess:
    """Tests for BackgroundProcess model."""
    
    def test_valid_process(self):
        """Test creating a valid background process."""
        process = BackgroundProcess(
            pid=12345,
            command="sleep 10",
            exec_dir="/tmp/exec_12345",
            stdout_path="/tmp/exec_12345/stdout.log",
            stderr_path="/tmp/exec_12345/stderr.log",
            exitcode_path="/tmp/exec_12345/exitcode.log",
            last_stdout_pos=0,
            last_stderr_pos=0
        )
        assert process.pid == 12345
        assert process.command == "sleep 10"
        assert process.exec_dir == "/tmp/exec_12345"
    
    def test_default_positions(self):
        """Test default values for stdout/stderr positions."""
        process = BackgroundProcess(
            pid=1,
            command="test",
            exec_dir="/tmp",
            stdout_path="/tmp/stdout.log",
            stderr_path="/tmp/stderr.log",
            exitcode_path="/tmp/exitcode.log"
        )
        assert process.last_stdout_pos == 0
        assert process.last_stderr_pos == 0
    
    def test_invalid_pid_zero(self):
        """Test that PID must be >= 1."""
        with pytest.raises(ValidationError):
            BackgroundProcess(
                pid=0,
                command="test",
                exec_dir="/tmp",
                stdout_path="/tmp/stdout.log",
                stderr_path="/tmp/stderr.log",
                exitcode_path="/tmp/exitcode.log"
            )
    
    def test_invalid_pid_negative(self):
        """Test that negative PIDs are rejected."""
        with pytest.raises(ValidationError):
            BackgroundProcess(
                pid=-1,
                command="test",
                exec_dir="/tmp",
                stdout_path="/tmp/stdout.log",
                stderr_path="/tmp/stderr.log",
                exitcode_path="/tmp/exitcode.log"
            )
    
    def test_empty_command_rejected(self):
        """Test that empty command is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            BackgroundProcess(
                pid=1,
                command="",
                exec_dir="/tmp",
                stdout_path="/tmp/stdout.log",
                stderr_path="/tmp/stderr.log",
                exitcode_path="/tmp/exitcode.log"
            )
        assert "cannot be empty" in str(exc_info.value)
    
    def test_empty_exec_dir_rejected(self):
        """Test that empty exec_dir is rejected."""
        with pytest.raises(ValidationError):
            BackgroundProcess(
                pid=1,
                command="test",
                exec_dir="",
                stdout_path="/tmp/stdout.log",
                stderr_path="/tmp/stderr.log",
                exitcode_path="/tmp/exitcode.log"
            )
    
    def test_negative_positions_rejected(self):
        """Test that negative positions are rejected."""
        with pytest.raises(ValidationError):
            BackgroundProcess(
                pid=1,
                command="test",
                exec_dir="/tmp",
                stdout_path="/tmp/stdout.log",
                stderr_path="/tmp/stderr.log",
                exitcode_path="/tmp/exitcode.log",
                last_stdout_pos=-1
            )


class TestVSCodeModels:
    """Tests for VSCode-related models."""
    
    def test_vscode_extension_all_fields(self):
        """Test VSCodeExtension with all fields."""
        ext = VSCodeExtension(
            id="ms-python.python",
            name="Python",
            version="2024.1.0",
            description="Python language support",
            publisher="Microsoft"
        )
        assert ext.id == "ms-python.python"
        assert ext.name == "Python"
        assert ext.version == "2024.1.0"
    
    def test_vscode_extension_minimal(self):
        """Test VSCodeExtension with minimal fields."""
        ext = VSCodeExtension()
        assert ext.id is None
        assert ext.name is None
    
    def test_vscode_context_default(self):
        """Test VSCodeContext with default value."""
        ctx = VSCodeContext()
        assert ctx.is_new_workspace_creation is True
    
    def test_vscode_context_explicit(self):
        """Test VSCodeContext with explicit value."""
        ctx = VSCodeContext(is_new_workspace_creation=False)
        assert ctx.is_new_workspace_creation is False
    
    def test_vscode_api_reference(self):
        """Test VSCodeAPIReference model."""
        ref = VSCodeAPIReference(
            api_name="window.showInformationMessage",
            description="Show information message",
            url="https://code.visualstudio.com/api"
        )
        assert ref.api_name == "window.showInformationMessage"
    
    def test_vscode_extension_with_all_optional_fields(self):
        """Test VSCodeExtension with various combinations of optional fields."""
        ext = VSCodeExtension(
            id="test.extension",
            name="Test Extension",
            publisher="Test Publisher"
        )
        assert ext.id == "test.extension"
        assert ext.version is None  # Not provided
        assert ext.description is None  # Not provided


class TestCopilotDB:
    """Tests for CopilotDB main model."""
    
    def test_minimal_valid_database(self):
        """Test creating a minimal valid database."""
        db = CopilotDB(
            workspace_root="/home/user/project",
            cwd="/home/user/project",
            file_system={
                "/home/user/project": {
                    "path": "/home/user/project",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                }
            },
            background_processes={},
            _next_pid=1
        )
        assert db.workspace_root == "/home/user/project"
        assert db.cwd == "/home/user/project"
        assert len(db.file_system) == 1
        assert db.next_pid == 1
    
    def test_database_with_vscode_fields(self):
        """Test database with VSCode fields."""
        db = CopilotDB(
            workspace_root="/home/user/project",
            cwd="/home/user/project",
            file_system={
                "/home/user/project": {
                    "path": "/home/user/project",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                }
            },
            background_processes={},
            vscode_extensions_marketplace=["test.extension"],
            vscode_context={"is_new_workspace_creation": True},
            installed_vscode_extensions=["installed.extension"],
            vscode_api_references=[],
            _next_pid=1
        )
        assert len(db.vscode_extensions_marketplace) == 1
        assert db.vscode_context.is_new_workspace_creation is True
    
    def test_empty_workspace_path_rejected(self):
        """Test that empty workspace_root is rejected."""
        with pytest.raises(ValidationError):
            CopilotDB(
                workspace_root="",
                cwd="/home/user/project",
                file_system={},
                _next_pid=1
            )
    
    def test_relative_workspace_path_rejected(self):
        """Test that relative workspace_root is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CopilotDB(
                workspace_root="relative/path",
                cwd="/home/user/project",
                file_system={},
                _next_pid=1
            )
        assert "must be absolute" in str(exc_info.value)
    
    def test_workspace_root_not_in_filesystem(self):
        """Test that workspace_root must exist in file_system."""
        with pytest.raises(ValidationError) as exc_info:
            CopilotDB(
                workspace_root="/home/user/project",
                cwd="/home/user/project",
                file_system={},  # Empty, missing workspace_root
                _next_pid=1
            )
        assert "must exist in file_system" in str(exc_info.value)
    
    def test_workspace_root_not_directory(self):
        """Test that workspace_root must be a directory."""
        with pytest.raises(ValidationError) as exc_info:
            CopilotDB(
                workspace_root="/home/user/project",
                cwd="/home/user/project",
                file_system={
                    "/home/user/project": {
                        "path": "/home/user/project",
                        "is_directory": False,  # Should be True
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": "2024-03-19T12:00:00Z"
                    }
                },
                _next_pid=1
            )
        assert "must be a directory" in str(exc_info.value)
    
    def test_cwd_outside_workspace(self):
        """Test that cwd must be within workspace_root."""
        with pytest.raises(ValidationError) as exc_info:
            CopilotDB(
                workspace_root="/home/user/project",
                cwd="/home/other/location",  # Outside workspace
                file_system={
                    "/home/user/project": {
                        "path": "/home/user/project",
                        "is_directory": True,
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": "2024-03-19T12:00:00Z"
                    }
                },
                _next_pid=1
            )
        assert "must be within workspace_root" in str(exc_info.value)
    
    def test_process_pid_mismatch(self):
        """Test that background process PID must match dictionary key."""
        with pytest.raises(ValidationError) as exc_info:
            CopilotDB(
                workspace_root="/home/user/project",
                cwd="/home/user/project",
                file_system={
                    "/home/user/project": {
                        "path": "/home/user/project",
                        "is_directory": True,
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": "2024-03-19T12:00:00Z"
                    }
                },
                background_processes={
                    "12345": {
                        "pid": 99999,  # Mismatch with key
                        "command": "test",
                        "exec_dir": "/tmp/test",
                        "stdout_path": "/tmp/test/stdout.log",
                        "stderr_path": "/tmp/test/stderr.log",
                        "exitcode_path": "/tmp/test/exitcode.log",
                        "last_stdout_pos": 0,
                        "last_stderr_pos": 0
                    }
                },
                _next_pid=1
            )
        assert "does not match key" in str(exc_info.value)
    
    def test_process_invalid_key(self):
        """Test that process key must be a valid integer string."""
        with pytest.raises(ValidationError) as exc_info:
            CopilotDB(
                workspace_root="/home/user/project",
                cwd="/home/user/project",
                file_system={
                    "/home/user/project": {
                        "path": "/home/user/project",
                        "is_directory": True,
                        "content_lines": [],
                        "size_bytes": 0,
                        "last_modified": "2024-03-19T12:00:00Z"
                    }
                },
                background_processes={
                    "invalid": {  # Non-integer key
                        "pid": 1,
                        "command": "test",
                        "exec_dir": "/tmp/test",
                        "stdout_path": "/tmp/test/stdout.log",
                        "stderr_path": "/tmp/test/stderr.log",
                        "exitcode_path": "/tmp/test/exitcode.log",
                        "last_stdout_pos": 0,
                        "last_stderr_pos": 0
                    }
                },
                _next_pid=1
            )
        assert "must be a valid integer" in str(exc_info.value)
    
    def test_get_next_pid(self):
        """Test get_next_pid helper method."""
        db = CopilotDB(
            workspace_root="/home/user/project",
            cwd="/home/user/project",
            file_system={
                "/home/user/project": {
                    "path": "/home/user/project",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                }
            },
            _next_pid=1000
        )
        
        # First call
        pid1 = db.get_next_pid()
        assert pid1 == 1000
        assert db.next_pid == 1001
        
        # Second call
        pid2 = db.get_next_pid()
        assert pid2 == 1001
        assert db.next_pid == 1002
    
    def test_complex_database_structure(self):
        """Test complex database with multiple files and processes."""
        db = CopilotDB(
            workspace_root="/home/user/complex",
            cwd="/home/user/complex/src",
            file_system={
                "/home/user/complex": {
                    "path": "/home/user/complex",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                },
                "/home/user/complex/src": {
                    "path": "/home/user/complex/src",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                },
                "/home/user/complex/main.py": {
                    "path": "/home/user/complex/main.py",
                    "is_directory": False,
                    "content_lines": ["import sys", "print('hello')"],
                    "size_bytes": 28,
                    "last_modified": "2024-03-20T10:30:00Z"
                }
            },
            background_processes={
                "1001": {
                    "pid": 1001,
                    "command": "npm run dev",
                    "exec_dir": "/tmp/npm_1001",
                    "stdout_path": "/tmp/npm_1001/stdout.log",
                    "stderr_path": "/tmp/npm_1001/stderr.log",
                    "exitcode_path": "/tmp/npm_1001/exitcode.log",
                    "last_stdout_pos": 0,
                    "last_stderr_pos": 0
                }
            },
            _next_pid=1002
        )
        
        assert len(db.file_system) == 3
        assert len(db.background_processes) == 1
        assert db.next_pid == 1002
    
    def test_model_dump_with_alias(self):
        """Test that model_dump preserves aliases."""
        db = CopilotDB(
            workspace_root="/home/user/project",
            cwd="/home/user/project",
            file_system={
                "/home/user/project": {
                    "path": "/home/user/project",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                }
            },
            _next_pid=100
        )
        
        # Dump with aliases
        dumped = db.model_dump(by_alias=True)
        assert "_next_pid" in dumped
        assert dumped["_next_pid"] == 100
    
    def test_all_vscode_fields_optional(self):
        """Test that all VSCode fields have proper defaults."""
        db = CopilotDB(
            workspace_root="/home/user/project",
            cwd="/home/user/project",
            file_system={
                "/home/user/project": {
                    "path": "/home/user/project",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                }
            },
            _next_pid=1
            # All VSCode fields should get defaults
        )
        assert db.workspace_root == "/home/user/project"
        assert db.vscode_extensions_marketplace == []
        assert db.vscode_context.is_new_workspace_creation is True
        assert db.installed_vscode_extensions == []
        assert db.vscode_api_references == []


class TestModelIntegration:
    """Integration tests for models working together."""
    
    def test_full_database_lifecycle(self):
        """Test creating, modifying, and dumping a full database."""
        # Create
        db = CopilotDB(
            workspace_root="/test",
            cwd="/test",
            file_system={
                "/test": {
                    "path": "/test",
                    "is_directory": True,
                    "content_lines": [],
                    "size_bytes": 0,
                    "last_modified": "2024-03-19T12:00:00Z"
                }
            },
            _next_pid=1
        )
        
        # Modify
        next_pid = db.get_next_pid()
        assert next_pid == 1
        
        # Dump
        dumped = db.model_dump(by_alias=True, exclude_unset=True)
        assert dumped["workspace_root"] == "/test"
        assert dumped["_next_pid"] == 2  # Incremented
        
        # Reload
        db2 = CopilotDB.model_validate(dumped)
        assert db2.next_pid == 2

