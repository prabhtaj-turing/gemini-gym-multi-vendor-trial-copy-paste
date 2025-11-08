"""
Test suite for validating the claude_code database structure and constraints.
"""

import unittest
import json
import os
from datetime import datetime

from common_utils.base_case import BaseTestCaseWithErrorHandler

from ..SimulationEngine.db import DB, reset_db


class TestDatabaseValidation(BaseTestCaseWithErrorHandler):
    """
    Test suite for validating the claude_code database against expected structure and constraints.
    """

    @classmethod
    def setUpClass(cls):
        """Load the sample database data once for all tests."""
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'DBs', 'ClaudeCodeDefaultDB.json')
        try:
            with open(db_path, 'r') as f:
                cls.sample_db_data = json.load(f)
        except FileNotFoundError:
            # Use fallback structure if sample DB doesn't exist
            cls.sample_db_data = {
                "workspace_root": "/home/user/project",
                "cwd": "/home/user/project",
                "file_system": {},
                "memory_storage": {},
                "last_edit_params": None,
                "background_processes": {},
                "tool_metrics": {}
            }

    def test_required_db_fields_presence(self):
        """Test that all required database fields are present."""
        required_fields = [
            "workspace_root",
            "cwd", 
            "file_system",
            "memory_storage",
            "last_edit_params",
            "background_processes",
            "tool_metrics"
        ]
        
        for field in required_fields:
            self.assertIn(field, self.sample_db_data, f"Required field '{field}' missing from sample DB")
            self.assertIn(field, DB, f"Required field '{field}' missing from DB module")

    def test_db_module_harmony(self):
        """Test that the database used by the db module matches expected structure."""
        # Check that DB has the same structure as sample
        for key in self.sample_db_data.keys():
            self.assertIn(key, DB, f"Key '{key}' from sample DB not found in DB module")

    def test_workspace_root_validation(self):
        """Test workspace_root field validation."""
        self.assertIsInstance(self.sample_db_data["workspace_root"], str)
        self.assertIsInstance(DB["workspace_root"], str)
        self.assertTrue(len(self.sample_db_data["workspace_root"]) > 0, "workspace_root should not be empty")
        self.assertTrue(os.path.isabs(self.sample_db_data["workspace_root"]), "workspace_root should be absolute path")

    def test_cwd_validation(self):
        """Test current working directory field validation."""
        self.assertIsInstance(self.sample_db_data["cwd"], str)
        self.assertIsInstance(DB["cwd"], str)
        self.assertTrue(len(self.sample_db_data["cwd"]) > 0, "cwd should not be empty")
        self.assertTrue(os.path.isabs(self.sample_db_data["cwd"]), "cwd should be absolute path")
        
        # cwd should be within or equal to workspace_root
        workspace_root = self.sample_db_data["workspace_root"]
        cwd = self.sample_db_data["cwd"]
        self.assertTrue(
            cwd.startswith(workspace_root) or cwd == workspace_root,
            f"cwd '{cwd}' should be within workspace_root '{workspace_root}'"
        )

    def test_file_system_structure_validation(self):
        """Test file_system structure and field validation."""
        file_system = self.sample_db_data["file_system"]
        self.assertIsInstance(file_system, dict)
        
        for file_path, file_info in file_system.items():
            # Test file path is absolute
            self.assertTrue(os.path.isabs(file_path), f"File path '{file_path}' should be absolute")
            
            # Test required file_info fields
            required_fields = ["path", "is_directory", "content_lines", "size_bytes"]
            for field in required_fields:
                self.assertIn(field, file_info, f"Required field '{field}' missing in file_info for {file_path}")
            
            # Test field types
            self.assertIsInstance(file_info["path"], str)
            self.assertIsInstance(file_info["is_directory"], bool)
            self.assertIsInstance(file_info["content_lines"], list)
            self.assertIsInstance(file_info["size_bytes"], int)
            
            # Test path consistency
            self.assertEqual(file_info["path"], file_path, "path field should match dictionary key")
            
            # Test size_bytes is non-negative
            self.assertGreaterEqual(file_info["size_bytes"], 0, "size_bytes should be non-negative")
            
            # Test content_lines for non-directories
            if not file_info["is_directory"]:
                for line in file_info["content_lines"]:
                    self.assertIsInstance(line, str, "All content_lines should be strings")
            else:
                # Directories should have empty content_lines
                self.assertEqual(len(file_info["content_lines"]), 0, "Directories should have empty content_lines")
                self.assertEqual(file_info["size_bytes"], 0, "Directories should have size_bytes of 0")

    def test_file_system_path_hierarchy(self):
        """Test that file system paths form a valid hierarchy."""
        file_system = self.sample_db_data["file_system"]
        workspace_root = self.sample_db_data["workspace_root"]
        
        # All paths should be within workspace_root
        for file_path in file_system.keys():
            self.assertTrue(
                file_path.startswith(workspace_root),
                f"File path '{file_path}' should be within workspace_root '{workspace_root}'"
            )
        
        # Check parent-child relationships
        directories = {path: info for path, info in file_system.items() if info["is_directory"]}
        files = {path: info for path, info in file_system.items() if not info["is_directory"]}
        
        for file_path in files.keys():
            parent_dir = os.path.dirname(file_path)
            if parent_dir != workspace_root and parent_dir in file_system:
                self.assertTrue(
                    file_system[parent_dir]["is_directory"],
                    f"Parent '{parent_dir}' of file '{file_path}' should be a directory"
                )

    def test_memory_storage_validation(self):
        """Test memory_storage structure validation."""
        memory_storage = self.sample_db_data["memory_storage"]
        self.assertIsInstance(memory_storage, dict)
        
        # All values should be JSON serializable
        try:
            json.dumps(memory_storage)
        except (TypeError, ValueError) as e:
            self.fail(f"memory_storage should be JSON serializable: {e}")

    def test_last_edit_params_validation(self):
        """Test last_edit_params structure validation."""
        last_edit_params = self.sample_db_data["last_edit_params"]
        
        if last_edit_params is not None:
            self.assertIsInstance(last_edit_params, dict)
            
            # If present, should have file_path and content
            if "file_path" in last_edit_params:
                self.assertIsInstance(last_edit_params["file_path"], str)
                self.assertTrue(os.path.isabs(last_edit_params["file_path"]), "file_path should be absolute")
            
            if "content" in last_edit_params:
                self.assertIsInstance(last_edit_params["content"], str)

    def test_background_processes_validation(self):
        """Test background_processes structure validation."""
        background_processes = self.sample_db_data["background_processes"]
        self.assertIsInstance(background_processes, dict)
        
        for process_id, process_info in background_processes.items():
            self.assertIsInstance(process_id, str, "Process ID should be string")
            self.assertIsInstance(process_info, dict, "Process info should be dictionary")
            
            # Common fields that might be present
            if "command" in process_info:
                self.assertIsInstance(process_info["command"], str)
            if "status" in process_info:
                self.assertIsInstance(process_info["status"], str)
            if "pid" in process_info:
                self.assertIsInstance(process_info["pid"], int)
                self.assertGreater(process_info["pid"], 0, "PID should be positive")

    def test_tool_metrics_validation(self):
        """Test tool_metrics structure validation."""
        tool_metrics = self.sample_db_data["tool_metrics"]
        self.assertIsInstance(tool_metrics, dict)
        
        for tool_name, metrics in tool_metrics.items():
            self.assertIsInstance(tool_name, str, "Tool name should be string")
            self.assertIsInstance(metrics, dict, "Metrics should be dictionary")
            
            # Common metric fields
            if "count" in metrics:
                self.assertIsInstance(metrics["count"], int)
                self.assertGreaterEqual(metrics["count"], 0, "Count should be non-negative")
            
            if "total_time" in metrics:
                self.assertIsInstance(metrics["total_time"], (int, float))
                self.assertGreaterEqual(metrics["total_time"], 0, "Total time should be non-negative")
            
            if "errors" in metrics:
                self.assertIsInstance(metrics["errors"], int)
                self.assertGreaterEqual(metrics["errors"], 0, "Errors should be non-negative")

    def test_timestamp_format_validation(self):
        """Test that timestamp fields follow ISO format."""
        def validate_timestamp(timestamp_str, field_name):
            if timestamp_str is not None:
                try:
                    # Try to parse as ISO format
                    datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError as e:
                    self.fail(f"Timestamp field '{field_name}' has invalid format '{timestamp_str}': {e}")

        # Check timestamps in file_system
        for file_path, file_info in self.sample_db_data["file_system"].items():
            if "last_modified" in file_info:
                validate_timestamp(file_info["last_modified"], f"last_modified for {file_path}")
            if "created" in file_info:
                validate_timestamp(file_info["created"], f"created for {file_path}")

        # Check global timestamps
        if "_created" in self.sample_db_data:
            validate_timestamp(self.sample_db_data["_created"], "_created")

    def test_optional_fields_validation(self):
        """Test validation of optional fields when present."""
        # Test gitignore_patterns if present
        if "gitignore_patterns" in self.sample_db_data:
            patterns = self.sample_db_data["gitignore_patterns"]
            self.assertIsInstance(patterns, list)
            for pattern in patterns:
                self.assertIsInstance(pattern, str)

        # Test shell_config if present
        if "shell_config" in self.sample_db_data:
            shell_config = self.sample_db_data["shell_config"]
            self.assertIsInstance(shell_config, dict)

    def test_data_consistency_validation(self):
        """Test data consistency across related fields."""
        file_system = self.sample_db_data["file_system"]
        
        # Check that current working directory exists in file_system if it's not workspace_root
        cwd = self.sample_db_data["cwd"]
        workspace_root = self.sample_db_data["workspace_root"]
        
        if cwd != workspace_root and cwd in file_system:
            self.assertTrue(
                file_system[cwd]["is_directory"],
                f"Current working directory '{cwd}' should be a directory"
            )

        # Check that workspace_root exists in file_system
        if workspace_root in file_system:
            self.assertTrue(
                file_system[workspace_root]["is_directory"],
                f"Workspace root '{workspace_root}' should be a directory"
            )

        # Validate that last_edit_params file_path exists in file_system if specified
        last_edit_params = self.sample_db_data.get("last_edit_params")
        if last_edit_params and "file_path" in last_edit_params:
            edited_file = last_edit_params["file_path"]
            if edited_file in file_system:
                self.assertFalse(
                    file_system[edited_file]["is_directory"],
                    f"Last edited file '{edited_file}' should not be a directory"
                )

    def test_json_serialization(self):
        """Test that the entire database is JSON serializable."""
        try:
            # Test sample DB
            json.dumps(self.sample_db_data)
        except (TypeError, ValueError) as e:
            self.fail(f"Sample database should be JSON serializable: {e}")

        try:
            # Test current DB
            json.dumps(DB)
        except (TypeError, ValueError) as e:
            self.fail(f"Current database should be JSON serializable: {e}")

    def test_db_size_constraints(self):
        """Test that database doesn't exceed reasonable size limits."""
        # Test total file count
        file_count = len(self.sample_db_data["file_system"])
        self.assertLessEqual(file_count, 10000, "File system should not exceed 10,000 files")
        
        # Test individual file content size
        for file_path, file_info in self.sample_db_data["file_system"].items():
            if not file_info["is_directory"]:
                content_size = sum(len(line.encode('utf-8')) for line in file_info["content_lines"])
                self.assertLessEqual(
                    content_size, 
                    20 * 1024 * 1024,  # 20MB limit
                    f"File '{file_path}' content exceeds 20MB limit"
                )


if __name__ == '__main__':
    unittest.main()
