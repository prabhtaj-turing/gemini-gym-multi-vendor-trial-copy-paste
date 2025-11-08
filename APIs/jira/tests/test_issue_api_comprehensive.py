#!/usr/bin/env python3
"""
Comprehensive unit tests for IssueApi functions.
Focuses on testing individual issue-related API functions with proper validation,
error handling, and Pydantic model usage.
"""

import unittest
from unittest.mock import patch, MagicMock
from APIs.jira.SimulationEngine.db import DB
from APIs.jira.SimulationEngine.models import JiraIssueCreationFields, JiraIssueResponse, JiraDB
from APIs.jira.SimulationEngine.custom_errors import (
    EmptyFieldError, ProjectNotFoundError, ValidationError, MissingRequiredFieldError
)
from common_utils.base_case import BaseTestCaseWithErrorHandler
import APIs.jira.IssueApi as IssueApi
from pydantic import ValidationError as PydanticValidationError


class TestIssueApiComprehensive(BaseTestCaseWithErrorHandler):
    """Comprehensive test suite for Issue API functions."""

    def setUp(self):
        """Set up test database state before each test."""
        super().setUp()
        self.original_db_state = DB.copy()
        
        # Ensure we have a test project
        if "TESTPROJ" not in DB.get("projects", {}):
            DB.setdefault("projects", {})["TESTPROJ"] = {
                "key": "TESTPROJ",
                "name": "Test Project",
                "lead": "testuser"
            }
        
        # Ensure users dict exists
        DB.setdefault("users", {})

    def tearDown(self):
        """Restore original database state after each test."""
        DB.clear()
        DB.update(self.original_db_state)
        super().tearDown()

    def validate_db_integrity(self):
        """Helper method to validate database integrity using Pydantic."""
        try:
            validated_db = JiraDB(**DB)
            self.assertIsInstance(validated_db, JiraDB)
        except Exception as e:
            self.fail(f"Database integrity validation failed: {e}")

    def test_create_issue_with_pydantic_validation(self):
        """Test issue creation with comprehensive Pydantic validation."""
        fields = {
            "project": "TESTPROJ",
            "summary": "Test issue with Pydantic validation",
            "issuetype": "Bug",
            "description": "This is a test issue",
            "priority": "High",
            "assignee": {"name": "testuser"},
            "components": ["component1"],
            "due_date": "2024-12-31"
        }
        
        # Validate input using Pydantic before API call
        validated_fields = JiraIssueCreationFields(**fields)
        self.assertEqual(validated_fields.project, "TESTPROJ")
        self.assertEqual(validated_fields.summary, "Test issue with Pydantic validation")
        self.assertEqual(validated_fields.issuetype, "Bug")
        
        # Create issue through API
        result = IssueApi.create_issue(fields)
        
        # Validate response structure
        self.assertIn("id", result)
        self.assertIn("fields", result)
        
        # Validate response using Pydantic
        validated_response = JiraIssueResponse(**result)
        self.assertIsInstance(validated_response, JiraIssueResponse)
        
        # Validate database integrity after operation
        self.validate_db_integrity()

    def test_create_issue_input_validation_errors(self):
        """Test input validation errors for create_issue."""
        # Test missing required fields
        with self.assertRaises((EmptyFieldError, ValueError)):
            IssueApi.create_issue({})
        
        # Test invalid project
        fields = {
            "project": "NONEXISTENT",
            "summary": "Test issue"
        }
        with self.assertRaises(ProjectNotFoundError):
            IssueApi.create_issue(fields)
        
        # Test invalid field types
        fields = {
            "project": "TESTPROJ",
            "summary": 123,  # Should be string
            "issuetype": "Bug"
        }
        with self.assertRaises((TypeError, PydanticValidationError)):
            IssueApi.create_issue(fields)

    def test_get_issue_comprehensive(self):
        """Test get_issue with comprehensive validation."""
        # First create an issue to retrieve
        fields = {
            "project": "TESTPROJ",
            "summary": "Issue to retrieve",
            "issuetype": "Task",
            "description": "Test description",
            "priority": "Medium",
            "assignee": {"name": "testuser"}
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # Retrieve the issue
        retrieved_issue = IssueApi.get_issue(issue_id)
        
        # Validate response structure
        self.assertIn("id", retrieved_issue)
        self.assertIn("fields", retrieved_issue)
        self.assertEqual(retrieved_issue["id"], issue_id)
        
        # Validate using Pydantic
        validated_issue = JiraIssueResponse(**retrieved_issue)
        self.assertEqual(validated_issue.id, issue_id)
        self.assertEqual(validated_issue.fields.summary, "Issue to retrieve")
        
        # Test retrieving non-existent issue
        with self.assertRaises(ValueError):
            IssueApi.get_issue("NONEXISTENT-1")

    def test_update_issue_comprehensive(self):
        """Test update_issue with comprehensive validation."""
        # Create an issue to update
        fields = {
            "project": "TESTPROJ", 
            "summary": "Original summary",
            "issuetype": "Task"
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # Update the issue
        update_fields = {
            "summary": "Updated summary",
            "priority": "High",
            "description": "Updated description"
        }
        
        updated_issue = IssueApi.update_issue(issue_id, update_fields)
        
        # Validate response
        self.assertIn("updated", updated_issue)
        self.assertTrue(updated_issue["updated"])
        self.assertIn("issue", updated_issue)
        
        # Verify changes were applied
        retrieved_issue = IssueApi.get_issue(issue_id)
        self.assertEqual(retrieved_issue["fields"]["summary"], "Updated summary")
        self.assertEqual(retrieved_issue["fields"]["priority"], "High")
        self.assertEqual(retrieved_issue["fields"]["description"], "Updated description")
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_update_issue_comments_append(self):
        """Test that update_issue appends comments instead of replacing them."""
        # Create an issue with initial comments
        fields = {
            "project": "TESTPROJ",
            "summary": "Issue with comments",
            "issuetype": "Task",
            "comments": ["First comment", "Second comment"]
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # Verify initial comments
        self.assertEqual(created_issue["fields"]["comments"], ["First comment", "Second comment"])
        
        # Update the issue to add more comments
        update_fields = {
            "comments": ["Third comment", "Fourth comment"]
        }
        updated_issue = IssueApi.update_issue(issue_id, update_fields)
        
        # Verify comments were appended, not replaced
        expected_comments = ["First comment", "Second comment", "Third comment", "Fourth comment"]
        self.assertEqual(updated_issue["issue"]["fields"]["comments"], expected_comments)
        
        # Verify by retrieving the issue
        retrieved_issue = IssueApi.get_issue(issue_id)
        self.assertEqual(retrieved_issue["fields"]["comments"], expected_comments)
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_update_issue_comments_without_initial_comments(self):
        """Test that update_issue works when issue has no initial comments."""
        # Create an issue without comments
        fields = {
            "project": "TESTPROJ",
            "summary": "Issue without comments",
            "issuetype": "Task"
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # Update the issue to add comments
        update_fields = {
            "comments": ["First comment", "Second comment"]
        }
        updated_issue = IssueApi.update_issue(issue_id, update_fields)
        
        # Verify comments were added
        self.assertEqual(updated_issue["issue"]["fields"]["comments"], ["First comment", "Second comment"])
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_update_issue_preserves_comments_when_not_updated(self):
        """Test that existing comments are preserved when updating other fields."""
        # Create an issue with comments
        fields = {
            "project": "TESTPROJ",
            "summary": "Issue with comments",
            "issuetype": "Task",
            "comments": ["Original comment"]
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # Update other fields without touching comments
        update_fields = {
            "summary": "Updated summary",
            "priority": "High"
        }
        updated_issue = IssueApi.update_issue(issue_id, update_fields)
        
        # Verify comments are preserved
        self.assertEqual(updated_issue["issue"]["fields"]["comments"], ["Original comment"])
        self.assertEqual(updated_issue["issue"]["fields"]["summary"], "Updated summary")
        self.assertEqual(updated_issue["issue"]["fields"]["priority"], "High")
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_update_issue_multiple_comment_updates(self):
        """Test that multiple comment updates continue to append."""
        # Create an issue with initial comment
        fields = {
            "project": "TESTPROJ",
            "summary": "Issue for multiple updates",
            "issuetype": "Task",
            "comments": ["Comment 1"]
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # First update - add more comments
        IssueApi.update_issue(issue_id, {"comments": ["Comment 2"]})
        retrieved = IssueApi.get_issue(issue_id)
        self.assertEqual(retrieved["fields"]["comments"], ["Comment 1", "Comment 2"])
        
        # Second update - add even more comments
        IssueApi.update_issue(issue_id, {"comments": ["Comment 3", "Comment 4"]})
        retrieved = IssueApi.get_issue(issue_id)
        self.assertEqual(retrieved["fields"]["comments"], ["Comment 1", "Comment 2", "Comment 3", "Comment 4"])
        
        # Third update - update other fields, comments should stay
        IssueApi.update_issue(issue_id, {"summary": "Updated"})
        retrieved = IssueApi.get_issue(issue_id)
        self.assertEqual(retrieved["fields"]["comments"], ["Comment 1", "Comment 2", "Comment 3", "Comment 4"])
        self.assertEqual(retrieved["fields"]["summary"], "Updated")
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_delete_issue_comprehensive(self):
        """Test delete_issue with comprehensive validation."""
        # Create an issue to delete
        fields = {
            "project": "TESTPROJ",
            "summary": "Issue to delete", 
            "issuetype": "Task"
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # Verify issue exists
        retrieved_issue = IssueApi.get_issue(issue_id)
        self.assertEqual(retrieved_issue["id"], issue_id)
        
        # Delete the issue
        delete_result = IssueApi.delete_issue(issue_id)
        self.assertIn("deleted", delete_result)
        self.assertTrue(delete_result["deleted"])
        
        # Verify issue no longer exists
        with self.assertRaises(ValueError):
            IssueApi.get_issue(issue_id)
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_assign_issue_comprehensive(self):
        """Test assign_issue with comprehensive validation."""
        # Use an existing user from the DB (jdoe exists in default DB state)
        # Create an issue to assign
        fields = {
            "project": "TESTPROJ",
            "summary": "Issue to assign",
            "issuetype": "Task"
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # Assign the issue to existing user
        assignee = {"name": "jdoe"}
        assign_result = IssueApi.assign_issue(issue_id, assignee)
        
        # Validate response
        self.assertIn("assigned", assign_result)
        self.assertTrue(assign_result["assigned"])
        
        # Verify assignment
        retrieved_issue = IssueApi.get_issue(issue_id)
        self.assertEqual(retrieved_issue["fields"]["assignee"]["name"], "jdoe")
        
        # Test invalid assignee format
        with self.assertRaises((TypeError, ValueError)):
            IssueApi.assign_issue(issue_id, "invalid_assignee_format")

    def test_bulk_issue_operations_comprehensive(self):
        """Test bulk_issue_operation with comprehensive validation."""
        # Create multiple issues for bulk operations
        issue_ids = []
        for i in range(3):
            fields = {
                "project": "TESTPROJ",
                "summary": f"Bulk test issue {i+1}",
                "issuetype": "Task",
                "priority": "Low"
            }
            created_issue = IssueApi.create_issue(fields)
            issue_ids.append(created_issue["id"])
        
        # Perform bulk operations
        issue_updates = [
            {
                "issueId": issue_ids[0],
                "fields": {
                    "summary": "Bulk updated issue 1",
                    "priority": "High"
                }
            },
            {
                "issueId": issue_ids[1],
                "status": "Closed",
                "priority": "Medium"
            },
            {
                "issueId": issue_ids[2],
                "delete": True
            }
        ]
        
        bulk_result = IssueApi.bulk_issue_operation(issue_updates)
        
        # Validate response structure
        self.assertIn("bulkProcessed", bulk_result)
        self.assertIn("updatesCount", bulk_result)
        self.assertIn("successfulUpdates", bulk_result)
        self.assertIn("deletedIssues", bulk_result)
        
        # Verify counts
        self.assertEqual(bulk_result["updatesCount"], 3)
        self.assertEqual(len(bulk_result["successfulUpdates"]), 2)  # 2 updates
        self.assertEqual(len(bulk_result["deletedIssues"]), 1)  # 1 delete
        
        # Verify individual operations
        # Issue 1 should be updated
        updated_issue_1 = IssueApi.get_issue(issue_ids[0])
        self.assertEqual(updated_issue_1["fields"]["summary"], "Bulk updated issue 1")
        self.assertEqual(updated_issue_1["fields"]["priority"], "High")
        
        # Issue 2 should have status and priority updated
        updated_issue_2 = IssueApi.get_issue(issue_ids[1])
        self.assertEqual(updated_issue_2["fields"]["status"], "Closed")
        self.assertEqual(updated_issue_2["fields"]["priority"], "Medium")
        
        # Issue 3 should be deleted
        with self.assertRaises(ValueError):
            IssueApi.get_issue(issue_ids[2])
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_issue_picker_comprehensive(self):
        """Test issue_picker with comprehensive validation and JQL support."""
        # Create test issues
        test_issues = [
            {"project": "TESTPROJ", "summary": "Bug in authentication", "issuetype": "Bug", "priority": "High"},
            {"project": "TESTPROJ", "summary": "Feature request for dashboard", "issuetype": "Story", "priority": "Medium"},
            {"project": "TESTPROJ", "summary": "Authentication improvement", "issuetype": "Task", "priority": "Low"}
        ]
        
        created_issues = []
        for fields in test_issues:
            created_issue = IssueApi.create_issue(fields)
            created_issues.append(created_issue)
        
        # Test text search
        search_result = IssueApi.issue_picker(query="authentication")
        self.assertIn("issues", search_result)
        
        # Should find issues with "authentication" in summary
        found_issue_ids = search_result["issues"]
        self.assertIsInstance(found_issue_ids, list)
        
        # Check that we found some issues with authentication in summary
        auth_found = False
        for issue_id in found_issue_ids:
            if isinstance(issue_id, str):
                issue_data = DB.get("issues", {}).get(issue_id, {})
                summary = issue_data.get("fields", {}).get("summary", "")
                if "authentication" in summary.lower():
                    auth_found = True
                    break
        self.assertTrue(auth_found, "Should find issues with 'authentication' in summary")
        
        # Test JQL search
        jql_result = IssueApi.issue_picker(currentJQL='issuetype = "Bug"')
        self.assertIn("issues", jql_result)
        
        # Should find only Bug type issues
        bug_issue_ids = jql_result["issues"]
        self.assertIsInstance(bug_issue_ids, list)
        
        for issue_id in bug_issue_ids:
            if isinstance(issue_id, str):
                issue_data = DB.get("issues", {}).get(issue_id, {})
                if issue_id in [ci["id"] for ci in created_issues]:
                    self.assertEqual(issue_data.get("fields", {}).get("issuetype"), "Bug")
        
        # Test combined JQL and text search
        combined_result = IssueApi.issue_picker(
            query="authentication",
            currentJQL='priority = "High"'
        )
        self.assertIn("issues", combined_result)

    def test_get_create_meta_comprehensive(self):
        """Test get_create_meta with comprehensive validation."""
        # Test getting all metadata
        all_meta = IssueApi.get_create_meta()
        self.assertIn("projects", all_meta)
        self.assertIsInstance(all_meta["projects"], list)
        
        # Test filtering by project keys
        project_meta = IssueApi.get_create_meta(projectKeys="TESTPROJ")
        self.assertIn("projects", project_meta)
        
        # Should contain only TESTPROJ if it exists
        if project_meta["projects"]:
            project_keys = [p["key"] for p in project_meta["projects"]]
            self.assertIn("TESTPROJ", project_keys)
        
        # Test filtering by issue type names
        type_meta = IssueApi.get_create_meta(issueTypeNames="Bug,Task")
        self.assertIn("projects", type_meta)
    
    def test_get_create_meta_field_metadata_structure(self):
        """Test that get_create_meta returns proper field metadata structure."""
        # Get metadata for the test project
        meta = IssueApi.get_create_meta(projectKeys="TESTPROJ")
        
        self.assertIn("projects", meta)
        self.assertGreater(len(meta["projects"]), 0, "Should have at least one project")
        
        project = meta["projects"][0]
        
        # Verify project structure
        self.assertIn("key", project)
        self.assertIn("name", project)
        self.assertIn("lead", project)
        self.assertIn("issueTypes", project)
        self.assertIsInstance(project["issueTypes"], list)
        
        # Verify issue type structure if available
        if project["issueTypes"]:
            issue_type = project["issueTypes"][0]
            
            # Check issue type has required fields
            self.assertIn("id", issue_type)
            self.assertIn("name", issue_type)
            self.assertIn("fields", issue_type)
            
            # Verify fields metadata structure
            fields = issue_type["fields"]
            self.assertIsInstance(fields, dict)
            
            # Check that required fields are present
            required_fields = ["project", "summary"]
            for field_name in required_fields:
                self.assertIn(field_name, fields, f"Required field '{field_name}' should be in metadata")
            
            # Verify each field has proper metadata structure
            for field_name, field_meta in fields.items():
                self.assertIn("required", field_meta, f"Field '{field_name}' should have 'required' property")
                self.assertIn("name", field_meta, f"Field '{field_name}' should have 'name' property")
                self.assertIn("schema", field_meta, f"Field '{field_name}' should have 'schema' property")
                self.assertIn("hasDefaultValue", field_meta, f"Field '{field_name}' should have 'hasDefaultValue' property")
                
                # Verify types
                self.assertIsInstance(field_meta["required"], bool)
                self.assertIsInstance(field_meta["name"], str)
                self.assertIsInstance(field_meta["schema"], dict)
                self.assertIsInstance(field_meta["hasDefaultValue"], bool)
                
                # Verify schema has type
                self.assertIn("type", field_meta["schema"])
    
    def test_get_create_meta_field_requirements(self):
        """Test that required and optional fields are correctly marked in metadata."""
        meta = IssueApi.get_create_meta(projectKeys="TESTPROJ")
        
        if meta["projects"] and meta["projects"][0]["issueTypes"]:
            fields = meta["projects"][0]["issueTypes"][0]["fields"]
            
            # Verify required fields
            self.assertTrue(fields["project"]["required"], "project should be required")
            self.assertTrue(fields["summary"]["required"], "summary should be required")
            
            # Verify optional fields
            self.assertFalse(fields["description"]["required"], "description should be optional")
            self.assertFalse(fields["priority"]["required"], "priority should be optional")
            self.assertFalse(fields["assignee"]["required"], "assignee should be optional")
            self.assertFalse(fields["status"]["required"], "status should be optional")
    
    def test_get_create_meta_field_defaults(self):
        """Test that fields with defaults are correctly marked in metadata."""
        meta = IssueApi.get_create_meta(projectKeys="TESTPROJ")
        
        if meta["projects"] and meta["projects"][0]["issueTypes"]:
            fields = meta["projects"][0]["issueTypes"][0]["fields"]
            
            # Fields with defaults
            fields_with_defaults = ["issuetype", "description", "priority", "assignee", "status", "comments", "components"]
            for field_name in fields_with_defaults:
                self.assertTrue(
                    fields[field_name]["hasDefaultValue"],
                    f"{field_name} should have a default value"
                )
            
            # Fields without defaults
            fields_without_defaults = ["project", "summary", "created", "updated", "due_date"]
            for field_name in fields_without_defaults:
                self.assertFalse(
                    fields[field_name]["hasDefaultValue"],
                    f"{field_name} should not have a default value"
                )
    
    def test_get_create_meta_field_schemas(self):
        """Test that field schemas are correctly defined in metadata."""
        meta = IssueApi.get_create_meta(projectKeys="TESTPROJ")
        
        if meta["projects"] and meta["projects"][0]["issueTypes"]:
            fields = meta["projects"][0]["issueTypes"][0]["fields"]
            
            # String fields
            string_fields = ["project", "summary", "description", "priority", "status", "issuetype", "created", "updated", "due_date"]
            for field_name in string_fields:
                self.assertEqual(
                    fields[field_name]["schema"]["type"],
                    "string",
                    f"{field_name} should have string type"
                )
            
            # Object fields
            self.assertEqual(fields["assignee"]["schema"]["type"], "object", "assignee should have object type")
            
            # Array fields
            array_fields = ["comments", "components"]
            for field_name in array_fields:
                self.assertEqual(
                    fields[field_name]["schema"]["type"],
                    "array",
                    f"{field_name} should have array type"
                )
                self.assertIn("items", fields[field_name]["schema"])
    
    def test_get_create_meta_all_expected_fields(self):
        """Test that all expected fields are present in the metadata."""
        meta = IssueApi.get_create_meta(projectKeys="TESTPROJ")
        
        if meta["projects"] and meta["projects"][0]["issueTypes"]:
            fields = meta["projects"][0]["issueTypes"][0]["fields"]
            
            # All expected fields based on JiraIssueCreationFields model
            expected_fields = [
                "project", "summary", "issuetype", "description", "priority",
                "assignee", "status", "created", "updated", "due_date",
                "comments", "components"
            ]
            
            for field_name in expected_fields:
                self.assertIn(
                    field_name,
                    fields,
                    f"Field '{field_name}' should be present in metadata"
                )
    
    def test_get_create_meta_multiple_issue_types(self):
        """Test that metadata is provided for multiple issue types."""
        # Create issues with different types
        IssueApi.create_issue(fields={
            "project": "TESTPROJ",
            "summary": "Test Bug",
            "issuetype": "Bug"
        })
        IssueApi.create_issue(fields={
            "project": "TESTPROJ",
            "summary": "Test Task",
            "issuetype": "Task"
        })
        
        meta = IssueApi.get_create_meta(projectKeys="TESTPROJ")
        
        if meta["projects"]:
            project = meta["projects"][0]
            
            # Should have multiple issue types
            self.assertGreater(len(project["issueTypes"]), 0)
            
            # Each issue type should have the same field metadata structure
            for issue_type in project["issueTypes"]:
                self.assertIn("id", issue_type)
                self.assertIn("name", issue_type)
                self.assertIn("fields", issue_type)
                self.assertEqual(len(issue_type["fields"]), 12, "Should have 12 fields")
    
    def test_get_create_meta_filtering_preserves_metadata(self):
        """Test that filtering by issueTypeNames still returns full field metadata."""
        meta = IssueApi.get_create_meta(projectKeys="TESTPROJ", issueTypeNames="Bug")
        
        if meta["projects"] and meta["projects"][0]["issueTypes"]:
            # Should have filtered issue types but full metadata
            for issue_type in meta["projects"][0]["issueTypes"]:
                self.assertIn("fields", issue_type)
                fields = issue_type["fields"]
                
                # Should still have all fields
                self.assertIn("project", fields)
                self.assertIn("summary", fields)
                self.assertIn("priority", fields)
                
                # Each field should have complete metadata
                for field_meta in fields.values():
                    self.assertIn("required", field_meta)
                    self.assertIn("name", field_meta)
                    self.assertIn("schema", field_meta)
                    self.assertIn("hasDefaultValue", field_meta)

    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling across Issue API functions."""
        # Test invalid issue ID formats
        invalid_ids = ["", "   ", None, 123, [], {}]
        
        for invalid_id in invalid_ids:
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises((TypeError, ValueError)):
                    IssueApi.get_issue(invalid_id)
        
        # Test invalid field types in create_issue
        invalid_fields_list = [
            None,  # None fields
            "not a dict",  # String instead of dict
            123,  # Number instead of dict
            [],  # List instead of dict
        ]
        
        for invalid_fields in invalid_fields_list:
            with self.subTest(fields=invalid_fields):
                with self.assertRaises((TypeError, ValueError, MissingRequiredFieldError)):
                    IssueApi.create_issue(invalid_fields)

    def test_database_consistency_after_operations(self):
        """Test that database remains consistent after various operations."""
        initial_issue_count = len(DB.get("issues", {}))
        
        # Perform various operations
        fields = {
            "project": "TESTPROJ",
            "summary": "Consistency test issue",
            "issuetype": "Task"
        }
        created_issue = IssueApi.create_issue(fields)
        issue_id = created_issue["id"]
        
        # Database should have one more issue
        self.assertEqual(len(DB["issues"]), initial_issue_count + 1)
        
        # Update the issue
        IssueApi.update_issue(issue_id, {"summary": "Updated summary"})
        
        # Issue count should remain the same
        self.assertEqual(len(DB["issues"]), initial_issue_count + 1)
        
        # Delete the issue
        IssueApi.delete_issue(issue_id)
        
        # Issue count should return to original
        self.assertEqual(len(DB["issues"]), initial_issue_count)
        
        # Validate final database state
        self.validate_db_integrity()

    def test_memory_usage_and_performance(self):
        """Test memory usage and basic performance characteristics."""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        
        # Record initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create and delete many issues
        for i in range(100):
            fields = {
                "project": "TESTPROJ", 
                "summary": f"Performance test issue {i}",
                "issuetype": "Task"
            }
            created_issue = IssueApi.create_issue(fields)
            
            # Update the issue
            IssueApi.update_issue(created_issue["id"], {"priority": "High"})
            
            # Delete the issue
            IssueApi.delete_issue(created_issue["id"])
        
        # Record final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for 100 operations)
        self.assertLess(memory_increase, 50, 
                       f"Memory usage increased by {memory_increase:.2f}MB, which may indicate a memory leak")
        
        # Validate database integrity after stress test
        self.validate_db_integrity()

    def test_bulk_delete_all_invalid_ids_reported(self):
        """Test that bulk_delete_issues reports ALL invalid IDs, not just the first one."""
        # Create 3 valid issues
        valid_issue_ids = []
        for i in range(3):
            fields = {
                "project": "TESTPROJ",
                "summary": f"Valid issue {i+1}",
                "issuetype": "Task"
            }
            created_issue = IssueApi.create_issue(fields)
            valid_issue_ids.append(created_issue["id"])
        
        # Try to delete mix of valid and multiple invalid IDs
        issue_ids_to_delete = [
            valid_issue_ids[0],
            "NONEXISTENT-1",
            valid_issue_ids[1],
            "NONEXISTENT-2",
            "INVALID-999",
            valid_issue_ids[2],
            "MISSING-777"
        ]
        
        # Should raise ValueError with ALL invalid IDs
        with self.assertRaises(ValueError) as context:
            IssueApi.bulk_delete_issues(issue_ids_to_delete)
        
        error_message = str(context.exception)
        
        # Verify ALL invalid IDs are in the error message
        self.assertIn("NONEXISTENT-1", error_message, "Should report NONEXISTENT-1")
        self.assertIn("NONEXISTENT-2", error_message, "Should report NONEXISTENT-2")
        self.assertIn("INVALID-999", error_message, "Should report INVALID-999")
        self.assertIn("MISSING-777", error_message, "Should report MISSING-777")
        
        # Verify the error message format
        self.assertIn("do not exist", error_message.lower(), "Should have 'do not exist' message")
        
        # Verify valid issues were NOT deleted (transaction should fail)
        for issue_id in valid_issue_ids:
            retrieved_issue = IssueApi.get_issue(issue_id)
            self.assertEqual(retrieved_issue["id"], issue_id, f"Issue {issue_id} should still exist")
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_bulk_delete_all_non_string_ids_reported(self):
        """Test that bulk_delete_issues reports ALL non-string IDs."""
        # Create valid issues
        valid_issue_ids = []
        for i in range(2):
            fields = {
                "project": "TESTPROJ",
                "summary": f"Valid issue for type test {i+1}",
                "issuetype": "Task"
            }
            created_issue = IssueApi.create_issue(fields)
            valid_issue_ids.append(created_issue["id"])
        
        # Mix valid strings with multiple invalid types
        issue_ids_with_invalid_types = [
            valid_issue_ids[0],
            123,  # Integer
            valid_issue_ids[1],
            None,  # None type
            45.67,  # Float
            {"key": "value"},  # Dict
            ["list", "item"]  # List
        ]
        
        # Should raise TypeError with ALL invalid IDs
        with self.assertRaises(TypeError) as context:
            IssueApi.bulk_delete_issues(issue_ids_with_invalid_types)
        
        error_message = str(context.exception)
        
        # Verify ALL non-string IDs are reported
        self.assertIn("123", error_message, "Should report integer 123")
        self.assertIn("None", error_message, "Should report None")
        self.assertIn("45.67", error_message, "Should report float 45.67")
        
        # Verify error message mentions they must be strings
        self.assertIn("must be a list of strings", error_message, "Should specify strings requirement")
        
        # Verify valid issues were NOT deleted
        for issue_id in valid_issue_ids:
            retrieved_issue = IssueApi.get_issue(issue_id)
            self.assertEqual(retrieved_issue["id"], issue_id)
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_bulk_delete_single_invalid_id_still_works(self):
        """Test that bulk_delete_issues works correctly with a single invalid ID."""
        # Create a valid issue
        fields = {"project": "TESTPROJ", "summary": "Valid issue", "issuetype": "Task"}
        created_issue = IssueApi.create_issue(fields)
        valid_id = created_issue["id"]
        
        # Try to delete one valid and one invalid ID
        issue_ids = [valid_id, "SINGLE-INVALID-ID"]
        
        with self.assertRaises(ValueError) as context:
            IssueApi.bulk_delete_issues(issue_ids)
        
        error_message = str(context.exception)
        
        # Should still report the single invalid ID correctly
        self.assertIn("SINGLE-INVALID-ID", error_message)
        self.assertIn("do not exist", error_message.lower())
        
        # Valid issue should not be deleted
        retrieved_issue = IssueApi.get_issue(valid_id)
        self.assertEqual(retrieved_issue["id"], valid_id)

    def test_bulk_delete_all_valid_ids_success(self):
        """Test that bulk_delete_issues successfully deletes when all IDs are valid."""
        # Create multiple valid issues
        issue_ids = []
        for i in range(5):
            fields = {
                "project": "TESTPROJ",
                "summary": f"Issue to delete {i+1}",
                "issuetype": "Task"
            }
            created_issue = IssueApi.create_issue(fields)
            issue_ids.append(created_issue["id"])
        
        # All IDs are valid, should delete successfully
        result = IssueApi.bulk_delete_issues(issue_ids)
        
        # Verify response structure
        self.assertIn("deleted", result)
        self.assertEqual(len(result["deleted"]), 5, "Should delete all 5 issues")
        
        # Verify all messages are present
        for issue_id in issue_ids:
            expected_message = f"Issue '{issue_id}' has been deleted."
            self.assertIn(expected_message, result["deleted"])
        
        # Verify all issues are actually deleted
        for issue_id in issue_ids:
            with self.assertRaises(ValueError):
                IssueApi.get_issue(issue_id)
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_bulk_operation_all_invalid_issue_ids_reported(self):
        """Test that bulk_issue_operation reports ALL non-existent issue IDs."""
        # Create 2 valid issues
        valid_issue_ids = []
        for i in range(2):
            fields = {
                "project": "TESTPROJ",
                "summary": f"Valid bulk op issue {i+1}",
                "issuetype": "Task",
                "priority": "Low"
            }
            created_issue = IssueApi.create_issue(fields)
            valid_issue_ids.append(created_issue["id"])
        
        # Create updates with mix of valid and multiple invalid IDs
        updates = [
            {
                "issueId": valid_issue_ids[0],
                "fields": {"summary": "Updated issue 1"}
            },
            {
                "issueId": "INVALID-OP-1",
                "fields": {"summary": "Invalid update 1"}
            },
            {
                "issueId": valid_issue_ids[1],
                "fields": {"priority": "High"}
            },
            {
                "issueId": "INVALID-OP-2",
                "fields": {"summary": "Invalid update 2"}
            },
            {
                "issueId": "NONEXIST-999",
                "delete": True
            },
            {
                "issueId": "MISSING-888",
                "status": "Closed"
            }
        ]
        
        # Should raise ValueError with ALL invalid IDs
        with self.assertRaises(ValueError) as context:
            IssueApi.bulk_issue_operation(updates)
        
        error_message = str(context.exception)
        
        # Verify ALL invalid IDs are reported
        self.assertIn("INVALID-OP-1", error_message, "Should report INVALID-OP-1")
        self.assertIn("INVALID-OP-2", error_message, "Should report INVALID-OP-2")
        self.assertIn("NONEXIST-999", error_message, "Should report NONEXIST-999")
        self.assertIn("MISSING-888", error_message, "Should report MISSING-888")
        
        # Verify error message format
        self.assertIn("do not exist", error_message.lower())
        
        # Verify valid issues were NOT modified (transaction failed)
        issue_1 = IssueApi.get_issue(valid_issue_ids[0])
        self.assertEqual(issue_1["fields"]["summary"], f"Valid bulk op issue 1", 
                        "Issue 1 should not be modified")
        
        issue_2 = IssueApi.get_issue(valid_issue_ids[1])
        self.assertEqual(issue_2["fields"]["priority"], "Low", 
                        "Issue 2 priority should remain Low")
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_bulk_operation_only_invalid_ids(self):
        """Test bulk_issue_operation when ALL issue IDs are invalid."""
        # Try to operate on entirely non-existent issues
        updates = [
            {"issueId": "FAKE-1", "fields": {"summary": "Update 1"}},
            {"issueId": "FAKE-2", "fields": {"summary": "Update 2"}},
            {"issueId": "FAKE-3", "delete": True},
            {"issueId": "FAKE-4", "status": "Done"}
        ]
        
        with self.assertRaises(ValueError) as context:
            IssueApi.bulk_issue_operation(updates)
        
        error_message = str(context.exception)
        
        # All 4 invalid IDs should be reported
        self.assertIn("FAKE-1", error_message)
        self.assertIn("FAKE-2", error_message)
        self.assertIn("FAKE-3", error_message)
        self.assertIn("FAKE-4", error_message)

    def test_bulk_operation_single_invalid_id_reported(self):
        """Test bulk_issue_operation correctly reports a single invalid ID."""
        # Create one valid issue
        fields = {"project": "TESTPROJ", "summary": "Valid issue", "issuetype": "Task"}
        created_issue = IssueApi.create_issue(fields)
        valid_id = created_issue["id"]
        
        # Mix one valid and one invalid
        updates = [
            {"issueId": valid_id, "fields": {"summary": "Updated"}},
            {"issueId": "SINGLE-INVALID", "fields": {"summary": "Invalid"}}
        ]
        
        with self.assertRaises(ValueError) as context:
            IssueApi.bulk_issue_operation(updates)
        
        error_message = str(context.exception)
        
        # Should report the single invalid ID
        self.assertIn("SINGLE-INVALID", error_message)
        self.assertIn("do not exist", error_message.lower())
        
        # Valid issue should not be modified
        issue = IssueApi.get_issue(valid_id)
        self.assertEqual(issue["fields"]["summary"], "Valid issue")

    def test_bulk_delete_edge_case_empty_string_ids(self):
        """Test bulk_delete_issues handles empty strings in ID list."""
        # Create a valid issue
        fields = {"project": "TESTPROJ", "summary": "Valid issue", "issuetype": "Task"}
        created_issue = IssueApi.create_issue(fields)
        valid_id = created_issue["id"]
        
        # Include empty strings (which are strings, but invalid IDs)
        issue_ids = [valid_id, "", "  ", "INVALID-1"]
        
        # Empty strings should be caught as non-existent
        with self.assertRaises(ValueError) as context:
            IssueApi.bulk_delete_issues(issue_ids)
        
        error_message = str(context.exception)
        # Should report the empty strings and invalid ID as non-existent
        self.assertIn("do not exist", error_message.lower())

    def test_bulk_operations_validation_before_execution(self):
        """Test that bulk operations validate ALL IDs before executing ANY operations."""
        # Create 3 valid issues
        issue_ids = []
        for i in range(3):
            fields = {
                "project": "TESTPROJ",
                "summary": f"Validation test issue {i+1}",
                "issuetype": "Task",
                "priority": "Low"
            }
            created_issue = IssueApi.create_issue(fields)
            issue_ids.append(created_issue["id"])
        
        # Record original state
        original_summaries = []
        for issue_id in issue_ids:
            issue = IssueApi.get_issue(issue_id)
            original_summaries.append(issue["fields"]["summary"])
        
        # Create updates with one invalid ID at the end
        updates = [
            {"issueId": issue_ids[0], "fields": {"summary": "MODIFIED 1"}},
            {"issueId": issue_ids[1], "fields": {"summary": "MODIFIED 2"}},
            {"issueId": issue_ids[2], "fields": {"summary": "MODIFIED 3"}},
            {"issueId": "INVALID-LAST", "fields": {"summary": "Should not process"}}
        ]
        
        # Should fail due to invalid ID
        with self.assertRaises(ValueError):
            IssueApi.bulk_issue_operation(updates)
        
        # Verify NONE of the valid issues were modified
        # This proves validation happens before execution
        for i, issue_id in enumerate(issue_ids):
            issue = IssueApi.get_issue(issue_id)
            self.assertEqual(issue["fields"]["summary"], original_summaries[i],
                           f"Issue {i+1} should not be modified due to failed validation")
        
        # Validate database integrity
        self.validate_db_integrity()

    def test_bulk_delete_large_number_of_invalid_ids(self):
        """Test bulk_delete_issues with a large number of invalid IDs."""
        # Create 2 valid issues
        valid_ids = []
        for i in range(2):
            fields = {"project": "TESTPROJ", "summary": f"Valid {i+1}", "issuetype": "Task"}
            created_issue = IssueApi.create_issue(fields)
            valid_ids.append(created_issue["id"])
        
        # Create list with many invalid IDs
        invalid_ids = [f"INVALID-{i}" for i in range(1, 21)]  # 20 invalid IDs
        issue_ids = valid_ids + invalid_ids
        
        with self.assertRaises(ValueError) as context:
            IssueApi.bulk_delete_issues(issue_ids)
        
        error_message = str(context.exception)
        
        # Verify multiple invalid IDs are in the message (spot check)
        self.assertIn("INVALID-1", error_message)
        self.assertIn("INVALID-10", error_message)
        self.assertIn("INVALID-20", error_message)
        
        # Verify valid issues still exist
        for valid_id in valid_ids:
            issue = IssueApi.get_issue(valid_id)
            self.assertEqual(issue["id"], valid_id)


if __name__ == '__main__':
    unittest.main()
