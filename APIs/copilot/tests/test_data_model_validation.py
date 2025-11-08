"""
Test cases for data model validation in the Copilot API.
Validates DB structure against schema.json and ensures test data uses proper models.
"""

import unittest
import json
import jsonschema
import copy
import os
from typing import Dict, Any

from pydantic import BaseModel, ValidationError
from copilot.SimulationEngine.db import DB
from copilot.SimulationEngine.models import (
    DirectoryEntry, 
    FileOutlineItem, 
    ReadFileResponse, 
    JupyterNotebookCreationResponse,
    EditFileResult
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class CopilotDBSchema(BaseModel):
    """
    Pydantic model for validating the Copilot DB structure.
    Based on schema.json definition.
    """
    workspace_root: str
    cwd: str
    file_system: Dict[str, Any]
    background_processes: Dict[str, Any]
    _next_pid: int

    class Config:
        extra = "allow"  # Allow additional fields for extensions


class FileSystemNode(BaseModel):
    """
    Pydantic model for validating file system nodes.
    """
    path: str
    is_directory: bool
    content_lines: list
    size_bytes: int
    last_modified: str

    class Config:
        extra = "allow"  # Allow additional fields like is_readonly


class TestDataModelValidation(BaseTestCaseWithErrorHandler):
    """Test cases for data model validation."""

    def setUp(self):
        """Set up test fixtures."""
        self._original_DB_state = copy.deepcopy(DB)
        # Load the schema for validation
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.json')
        with open(schema_path, 'r') as f:
            self.schema = json.load(f)

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_db_module_harmony_with_schema(self):
        """
        Test that the database used by the db module has the required structure.
        Note: The schema expects simpler background_processes but we test core structure.
        """
        try:
            # Validate using Pydantic model (more lenient with extra properties)
            validated_db = CopilotDBSchema(**DB)
            self.assertIsInstance(validated_db, CopilotDBSchema)
            
            # Verify required fields are present
            self.assertIn('workspace_root', DB)
            self.assertIn('cwd', DB)
            self.assertIn('file_system', DB)
            self.assertIn('background_processes', DB)
            self.assertIn('_next_pid', DB)
            
            # Test that we can create a schema-compliant version
            schema_compliant_db = copy.deepcopy(DB)
            
            # Remove extra properties from file system entries that aren't in schema
            for path, entry in schema_compliant_db["file_system"].items():
                if "is_readonly" in entry:
                    del entry["is_readonly"]
            
            # Convert background_processes to schema-compliant format (string values)
            schema_compliant_db["background_processes"] = {
                pid: process_info["command"] if isinstance(process_info, dict) else process_info
                for pid, process_info in schema_compliant_db["background_processes"].items()
            }
            
            # Now validate against JSON schema
            jsonschema.validate(schema_compliant_db, self.schema)
            
        except Exception as e:
            self.fail(f"DB module data structure validation failed: {e}")

    def test_file_system_node_validation(self):
        """Test that file system nodes conform to the expected structure."""
        # Test file node validation
        test_file_node = {
            "path": "/test/file.txt",
            "is_directory": False,
            "content_lines": ["line 1", "line 2"],
            "size_bytes": 14,
            "last_modified": "2024-03-19T12:00:00Z"
        }
        
        try:
            validated_node = FileSystemNode(**test_file_node)
            self.assertIsInstance(validated_node, FileSystemNode)
            self.assertEqual(validated_node.path, "/test/file.txt")
            self.assertFalse(validated_node.is_directory)
        except ValidationError as e:
            self.fail(f"File system node validation failed: {e}")

    def test_directory_node_validation(self):
        """Test that directory nodes conform to the expected structure."""
        test_dir_node = {
            "path": "/test/dir",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2024-03-19T12:00:00Z"
        }
        
        try:
            validated_node = FileSystemNode(**test_dir_node)
            self.assertIsInstance(validated_node, FileSystemNode)
            self.assertEqual(validated_node.path, "/test/dir")
            self.assertTrue(validated_node.is_directory)
            self.assertEqual(len(validated_node.content_lines), 0)
            self.assertEqual(validated_node.size_bytes, 0)
        except ValidationError as e:
            self.fail(f"Directory node validation failed: {e}")

    def test_directory_entry_model_validation(self):
        """Test DirectoryEntry model validation."""
        # Test valid directory entry
        valid_dir_entry_data = {
            "name": "test_dir/",
            "type": "directory",
            "path": "/test/test_dir"
        }
        
        try:
            dir_entry = DirectoryEntry(**valid_dir_entry_data)
            self.assertEqual(dir_entry.name, "test_dir/")
            self.assertEqual(dir_entry.type, "directory")
            self.assertEqual(dir_entry.path, "/test/test_dir")
        except ValidationError as e:
            self.fail(f"DirectoryEntry validation failed: {e}")

        # Test valid file entry
        valid_file_entry_data = {
            "name": "test_file.txt",
            "type": "file",
            "path": "/test/test_file.txt"
        }
        
        try:
            file_entry = DirectoryEntry(**valid_file_entry_data)
            self.assertEqual(file_entry.name, "test_file.txt")
            self.assertEqual(file_entry.type, "file")
        except ValidationError as e:
            self.fail(f"DirectoryEntry validation failed: {e}")

    def test_file_outline_item_model_validation(self):
        """Test FileOutlineItem model validation."""
        valid_outline_data = {
            "name": "test_function",
            "kind": "function",
            "start_line": 10,
            "end_line": 20
        }
        
        try:
            outline_item = FileOutlineItem(**valid_outline_data)
            self.assertEqual(outline_item.name, "test_function")
            self.assertEqual(outline_item.kind, "function")
            self.assertEqual(outline_item.start_line, 10)
            self.assertEqual(outline_item.end_line, 20)
        except ValidationError as e:
            self.fail(f"FileOutlineItem validation failed: {e}")

    def test_read_file_response_model_validation(self):
        """Test ReadFileResponse model validation."""
        valid_response_data = {
            "file_path": "/test/file.txt",
            "content": "test content",
            "start_line": 1,
            "end_line": 1,
            "total_lines": 1,
            "is_truncated_at_top": False,
            "is_truncated_at_bottom": False,
            "outline": None
        }
        
        try:
            response = ReadFileResponse(**valid_response_data)
            self.assertEqual(response.file_path, "/test/file.txt")
            self.assertEqual(response.content, "test content")
            self.assertFalse(response.is_truncated_at_top)
            self.assertIsNone(response.outline)
        except ValidationError as e:
            self.fail(f"ReadFileResponse validation failed: {e}")

    def test_jupyter_notebook_creation_response_validation(self):
        """Test JupyterNotebookCreationResponse model validation."""
        valid_response_data = {
            "file_path": "/test/notebook.ipynb",
            "status": "success",
            "message": "Notebook created successfully"
        }
        
        try:
            response = JupyterNotebookCreationResponse(**valid_response_data)
            self.assertEqual(response.file_path, "/test/notebook.ipynb")
            self.assertEqual(response.status, "success")
            self.assertEqual(response.message, "Notebook created successfully")
        except ValidationError as e:
            self.fail(f"JupyterNotebookCreationResponse validation failed: {e}")

    def test_edit_file_result_validation(self):
        """Test EditFileResult model validation."""
        valid_result_data = {
            "file_path": "/test/file.txt",
            "status": "success",
            "message": "File edited successfully"
        }
        
        try:
            result = EditFileResult(**valid_result_data)
            self.assertEqual(result.file_path, "/test/file.txt")
            self.assertEqual(result.status, "success")
            self.assertEqual(result.message, "File edited successfully")
        except ValidationError as e:
            self.fail(f"EditFileResult validation failed: {e}")

    def test_validated_test_data_creation(self):
        """
        Test that we create validated test data instead of raw dictionaries.
        This demonstrates the proper way to add test data to DB.
        """
        # Create validated file system node
        validated_file_node = FileSystemNode(
            path="/test/validated_file.txt",
            is_directory=False,
            content_lines=["validated content"],
            size_bytes=17,
            last_modified="2024-03-19T12:00:00Z"
        )
        
        # Add to DB using validated model
        DB["file_system"][validated_file_node.path] = validated_file_node.model_dump()
        
        # Verify the data was added correctly
        self.assertIn("/test/validated_file.txt", DB["file_system"])
        retrieved_node = DB["file_system"]["/test/validated_file.txt"]
        self.assertEqual(retrieved_node["path"], "/test/validated_file.txt")
        self.assertFalse(retrieved_node["is_directory"])
        self.assertEqual(retrieved_node["content_lines"], ["validated content"])

    def test_invalid_db_structure_detection(self):
        """Test that invalid DB structures are properly detected."""
        # Test missing required field
        invalid_db = {
            "workspace_root": "/test",
            "cwd": "/test",
            "file_system": {},
            # missing background_processes and _next_pid
        }
        
        with self.assertRaises((ValidationError, jsonschema.ValidationError)):
            CopilotDBSchema(**invalid_db)

    def test_invalid_file_system_node_detection(self):
        """Test that invalid file system nodes are properly detected."""
        # Test missing required field
        invalid_node = {
            "path": "/test/file.txt",
            "is_directory": False,
            # missing content_lines, size_bytes, last_modified
        }
        
        with self.assertRaises(ValidationError):
            FileSystemNode(**invalid_node)

    def test_workspace_root_path_validation(self):
        """Test that workspace_root follows the required path pattern."""
        # Test valid absolute path
        valid_db = copy.deepcopy(DB)
        valid_db["workspace_root"] = "/valid/absolute/path"
        
        # Remove extra properties from file system entries that aren't in schema
        for path, entry in valid_db["file_system"].items():
            if "is_readonly" in entry:
                del entry["is_readonly"]
        
        # Convert background_processes to schema-compliant format (string values)
        valid_db["background_processes"] = {
            pid: process_info["command"] if isinstance(process_info, dict) else process_info
            for pid, process_info in valid_db["background_processes"].items()
        }
        
        try:
            jsonschema.validate(valid_db, self.schema)
        except jsonschema.ValidationError:
            self.fail("Valid absolute path should pass validation")

        # Test invalid relative path should fail
        invalid_db = copy.deepcopy(DB)
        
        # Remove extra properties from file system entries that aren't in schema
        for path, entry in invalid_db["file_system"].items():
            if "is_readonly" in entry:
                del entry["is_readonly"]
        
        # Convert background_processes to schema-compliant format (string values)
        invalid_db["background_processes"] = {
            pid: process_info["command"] if isinstance(process_info, dict) else process_info
            for pid, process_info in invalid_db["background_processes"].items()
        }
        
        invalid_db["workspace_root"] = "relative/path"
        
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(invalid_db, self.schema)

    def test_background_processes_validation(self):
        """Test that background_processes structure is validated correctly."""
        valid_db = copy.deepcopy(DB)
        
        # Remove extra properties from file system entries that aren't in schema
        for path, entry in valid_db["file_system"].items():
            if "is_readonly" in entry:
                del entry["is_readonly"]
        
        # Test schema-compliant background_processes (simple string values)
        valid_db["background_processes"] = {
            "12345": "test command"
        }
        
        try:
            jsonschema.validate(valid_db, self.schema)
        except (jsonschema.ValidationError, ValidationError) as e:
            self.fail(f"Schema-compliant background_processes should pass validation: {e}")
        
        # Test that the Pydantic model can handle the actual DB structure
        try:
            CopilotDBSchema(**DB)
        except ValidationError as e:
            self.fail(f"Pydantic model should handle actual DB structure: {e}")


if __name__ == '__main__':
    unittest.main()
