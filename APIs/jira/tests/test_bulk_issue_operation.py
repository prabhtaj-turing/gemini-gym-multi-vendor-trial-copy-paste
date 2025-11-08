import pytest
from jira.SimulationEngine.models import BulkIssueUpdateModel, BulkIssueOperationRequestModel
from jira.SimulationEngine.db import DB
import jira as JiraAPI


class TestBulkIssueOperation:
    """Test cases for bulk_issue_operation function."""

    def setup_method(self):
        """Set up test data before each test."""
        # Reset the global DB state before each test
        DB.clear()
        DB.update({
            "issues": {
                "ISSUE-1": {
                    "id": "ISSUE-1",
                    "fields": {
                        "project": "TEST",
                        "summary": "Test Issue 1",
                        "description": "Test Description 1",
                        "issuetype": "Task",
                        "priority": "Medium",
                        "status": "Open",
                        "assignee": {"name": "user1"}
                    }
                },
                "ISSUE-2": {
                    "id": "ISSUE-2",
                    "fields": {
                        "project": "TEST",
                        "summary": "Test Issue 2",
                        "description": "Test Description 2",
                        "issuetype": "Bug",
                        "priority": "High",
                        "status": "In Progress",
                        "assignee": {"name": "user2"}
                    }
                },
                "ISSUE-3": {
                    "id": "ISSUE-3",
                    "fields": {
                        "project": "TEST",
                        "summary": "Test Issue 3",
                        "description": "Test Description 3",
                        "issuetype": "Task",
                        "priority": "Low",
                        "status": "Open",
                        "assignee": {"name": "user3"},
                        "sub-tasks": [
                            {"id": "SUBTASK-1", "name": "Subtask 1"},
                            {"id": "SUBTASK-2", "name": "Subtask 2"}
                        ]
                    }
                },
                "SUBTASK-1": {
                    "id": "SUBTASK-1",
                    "fields": {
                        "project": "TEST",
                        "summary": "Subtask 1",
                        "description": "Subtask 1 Description",
                        "issuetype": "Subtask",
                        "priority": "Low",
                        "status": "Open",
                        "assignee": {"name": "user3"}
                    }
                },
                "SUBTASK-2": {
                    "id": "SUBTASK-2",
                    "fields": {
                        "project": "TEST",
                        "summary": "Subtask 2",
                        "description": "Subtask 2 Description",
                        "issuetype": "Subtask",
                        "priority": "Low",
                        "status": "Open",
                        "assignee": {"name": "user3"}
                    }
                }
            }
        })

    def test_bulk_update_success(self):
        """Test successful bulk update operations."""
        updates = [
            {
                "issueId": "ISSUE-1",
                "summary": "Updated Summary 1",
                "status": "In Progress"
            },
            {
                "issueId": "ISSUE-2",
                "priority": "Critical",
                "description": "Updated Description 2"
            }
        ]
        
        result = JiraAPI.IssueApi.bulk_issue_operation(updates)
        
        assert result["bulkProcessed"] is True
        assert result["updatesCount"] == 2
        assert result["successfulUpdates"] == ["ISSUE-1", "ISSUE-2"]
        assert result["deletedIssues"] == []
        
        # Verify the updates were actually applied
        assert DB["issues"]["ISSUE-1"]["fields"]["summary"] == "Updated Summary 1"
        assert DB["issues"]["ISSUE-1"]["fields"]["status"] == "In Progress"
        assert DB["issues"]["ISSUE-2"]["fields"]["priority"] == "Critical"
        assert DB["issues"]["ISSUE-2"]["fields"]["description"] == "Updated Description 2"

    def test_bulk_delete_success(self):
        """Test successful bulk delete operations."""
        updates = [
            {
                "issueId": "ISSUE-1",
                "delete": True
            },
            {
                "issueId": "ISSUE-2",
                "delete": True
            }
        ]
        
        result = JiraAPI.IssueApi.bulk_issue_operation(updates)
        
        assert result["bulkProcessed"] is True
        assert result["updatesCount"] == 2
        assert result["successfulUpdates"] == []
        assert result["deletedIssues"] == ["ISSUE-1", "ISSUE-2"]
        
        # Verify the issues were actually deleted
        assert "ISSUE-1" not in DB["issues"]
        assert "ISSUE-2" not in DB["issues"]

    def test_bulk_delete_with_subtasks_success(self):
        """Test successful bulk delete with subtask deletion."""
        updates = [
            {
                "issueId": "ISSUE-3",
                "delete": True,
                "deleteSubtasks": True
            }
        ]
        
        result = JiraAPI.IssueApi.bulk_issue_operation(updates)
        
        assert result["bulkProcessed"] is True
        assert result["updatesCount"] == 1
        assert result["successfulUpdates"] == []
        assert result["deletedIssues"] == ["ISSUE-3"]
        
        # Verify the issue and subtasks were actually deleted
        assert "ISSUE-3" not in DB["issues"]
        assert "SUBTASK-1" not in DB["issues"]
        assert "SUBTASK-2" not in DB["issues"]

    def test_bulk_delete_with_subtasks_failure(self):
        """Test bulk delete failure when subtasks exist and deleteSubtasks is False."""
        updates = [
            {
                "issueId": "ISSUE-3",
                "delete": True,
                "deleteSubtasks": False
            }
        ]
        
        with pytest.raises(ValueError, match="Subtasks exist for issue 'ISSUE-3', cannot delete"):
            JiraAPI.IssueApi.bulk_issue_operation(updates)
        
        # Verify the issue and subtasks were NOT deleted
        assert "ISSUE-3" in DB["issues"]
        assert "SUBTASK-1" in DB["issues"]
        assert "SUBTASK-2" in DB["issues"]

    def test_mixed_operations_success(self):
        """Test mixed update and delete operations."""
        updates = [
            {
                "issueId": "ISSUE-1",
                "summary": "Updated Summary",
                "status": "Closed"
            },
            {
                "issueId": "ISSUE-2",
                "delete": True
            }
        ]
        
        result = JiraAPI.IssueApi.bulk_issue_operation(updates)
        
        assert result["bulkProcessed"] is True
        assert result["updatesCount"] == 2
        assert result["successfulUpdates"] == ["ISSUE-1"]
        assert result["deletedIssues"] == ["ISSUE-2"]
        
        # Verify the update was applied and delete was performed
        assert DB["issues"]["ISSUE-1"]["fields"]["summary"] == "Updated Summary"
        assert DB["issues"]["ISSUE-1"]["fields"]["status"] == "Closed"
        assert "ISSUE-2" not in DB["issues"]

    def test_issue_not_found(self):
        """Test error when issue does not exist."""
        updates = [
            {
                "issueId": "NONEXISTENT-1",
                "summary": "Updated Summary"
            }
        ]
        
        with pytest.raises(ValueError, match="The following issue\\(s\\) do not exist: NONEXISTENT-1"):
            JiraAPI.IssueApi.bulk_issue_operation(updates)

    def test_invalid_input_type(self):
        """Test error when input is not a list."""
        with pytest.raises(TypeError, match="issueUpdates must be a list"):
            JiraAPI.IssueApi.bulk_issue_operation("not a list")

    def test_empty_input(self):
        """Test error when input list is empty."""
        with pytest.raises(ValueError, match="issueUpdates cannot be empty"):
            JiraAPI.IssueApi.bulk_issue_operation([])

    def test_pydantic_validation_error(self):
        """Test Pydantic validation error handling."""
        updates = [
            {
                "issueId": "ISSUE-1",
                "invalid_field": "invalid_value"  # This should cause validation error
            }
        ]
        
        with pytest.raises(Exception):  # Should raise ValidationError
            JiraAPI.IssueApi.bulk_issue_operation(updates)

    def test_fields_object_update(self):
        """Test update using the fields object."""
        updates = [
            {
                "issueId": "ISSUE-1",
                "fields": {
                    "summary": "Updated via fields",
                    "priority": "High",
                    "assignee": {"name": "newuser"}
                }
            }
        ]
        
        result = JiraAPI.IssueApi.bulk_issue_operation(updates)
        
        assert result["bulkProcessed"] is True
        assert result["updatesCount"] == 1
        assert result["successfulUpdates"] == ["ISSUE-1"]
        assert result["deletedIssues"] == []
        
        # Verify the fields were updated
        assert DB["issues"]["ISSUE-1"]["fields"]["summary"] == "Updated via fields"
        assert DB["issues"]["ISSUE-1"]["fields"]["priority"] == "High"
        assert DB["issues"]["ISSUE-1"]["fields"]["assignee"]["name"] == "newuser"

    def test_individual_fields_override_fields_object(self):
        """Test that individual fields override fields object values."""
        updates = [
            {
                "issueId": "ISSUE-1",
                "fields": {
                    "summary": "Fields object summary",
                    "priority": "Low"
                },
                "summary": "Individual field summary",  # This should override
                "status": "Closed"  # This should be added
            }
        ]
        
        result = JiraAPI.IssueApi.bulk_issue_operation(updates)
        
        assert result["bulkProcessed"] is True
        assert result["updatesCount"] == 1
        assert result["successfulUpdates"] == ["ISSUE-1"]
        assert result["deletedIssues"] == []
        
        # Verify individual fields took precedence
        assert DB["issues"]["ISSUE-1"]["fields"]["summary"] == "Individual field summary"
        assert DB["issues"]["ISSUE-1"]["fields"]["status"] == "Closed"
        assert DB["issues"]["ISSUE-1"]["fields"]["priority"] == "Low"  # From fields object 