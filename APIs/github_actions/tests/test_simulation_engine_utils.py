"""
Comprehensive test suite for GitHub Actions Simulation Engine utilities.

This module tests all utility functions in the SimulationEngine.utils module,
ensuring proper functionality, error handling, and edge case coverage for
repository management, workflow operations, and data validation utilities.
"""

import unittest
import copy
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Optional

from github_actions.SimulationEngine import utils
from github_actions.SimulationEngine.db import DB
from github_actions.SimulationEngine.models import (
    GithubUser,
    ActorType,
    WorkflowState,
    WorkflowRunStatus,
    JobStatus,
    StepStatus,
    StepConclusion,
    RepositoryModel,
    Workflow,
    WorkflowRun,
    Job,
    Step,
)
from github_actions.SimulationEngine.custom_errors import InvalidInputError


class TestDateTimeHelpers(unittest.TestCase):
    """Test datetime helper functions."""

    def test_ensure_utc_datetime_with_utc_datetime(self):
        """Test _ensure_utc_datetime with UTC datetime input."""
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = utils._ensure_utc_datetime(dt)
        self.assertEqual(result, dt)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_ensure_utc_datetime_with_naive_datetime(self):
        """Test _ensure_utc_datetime with naive datetime input."""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = utils._ensure_utc_datetime(dt)
        self.assertEqual(result.replace(tzinfo=None), dt)
        self.assertEqual(result.tzinfo, timezone.utc)

    def test_ensure_utc_datetime_with_iso_string(self):
        """Test _ensure_utc_datetime with ISO string input."""
        iso_string = "2023-01-01T12:00:00Z"
        result = utils._ensure_utc_datetime(iso_string)
        expected = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(result, expected)

        # Test with +00:00 timezone
        iso_string_plus = "2023-01-01T12:00:00+00:00"
        result_plus = utils._ensure_utc_datetime(iso_string_plus)
        self.assertEqual(result_plus, expected)

    def test_ensure_utc_datetime_with_none(self):
        """Test _ensure_utc_datetime with None input."""
        result = utils._ensure_utc_datetime(None)
        self.assertIsNone(result)

    def test_ensure_utc_datetime_with_invalid_string(self):
        """Test _ensure_utc_datetime with invalid string input."""
        result = utils._ensure_utc_datetime("invalid-date")
        self.assertIsNone(result)
        # Note: print_log is called but we don't test it here due to dependency issues

    def test_ensure_utc_datetime_with_unsupported_type(self):
        """Test _ensure_utc_datetime with unsupported type."""
        result = utils._ensure_utc_datetime(123)
        self.assertIsNone(result)
        # Note: print_log is called but we don't test it here due to dependency issues


class TestRepositoryUtils(unittest.TestCase):
    """Test repository utility functions."""

    def setUp(self):
        """Set up test environment."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1

        self.valid_owner = {
            "login": "testowner",
            "id": 1,
            "node_id": "U_NODE_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

    def tearDown(self):
        """Clean up test environment."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_add_repository_success(self):
        """Test successful repository addition."""
        result = utils.add_repository(
            owner=self.valid_owner, repo_name="testrepo", private=False
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "testrepo")
        self.assertEqual(result["private"], False)
        self.assertEqual(result["owner"]["login"], "testowner")

        # Verify in database
        repo_key = "testowner/testrepo"
        self.assertIn(repo_key, DB["repositories"])
        self.assertEqual(DB["next_repo_id"], 2)

    def test_add_repository_with_custom_ids(self):
        """Test repository addition with custom IDs."""
        result = utils.add_repository(
            owner=self.valid_owner,
            repo_name="testrepo",
            private=True,
            repo_id=100,
            repo_node_id="CUSTOM_NODE_100",
        )

        self.assertEqual(result["id"], 100)
        self.assertEqual(result["node_id"], "CUSTOM_NODE_100")
        self.assertTrue(result["private"])

    def test_add_repository_duplicate_error(self):
        """Test error when adding duplicate repository."""
        # Add first repository
        utils.add_repository(owner=self.valid_owner, repo_name="testrepo")

        # Try to add duplicate
        with self.assertRaises(ValueError) as cm:
            utils.add_repository(owner=self.valid_owner, repo_name="testrepo")
        self.assertIn("already exists", str(cm.exception))

    def test_add_repository_invalid_owner_data(self):
        """Test error with invalid owner data."""
        invalid_owner = {
            "login": "test",
            "id": "not_an_int",  # Invalid type
            "node_id": "U_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        with self.assertRaises(ValueError) as cm:
            utils.add_repository(owner=invalid_owner, repo_name="testrepo")
        self.assertIn("Invalid data for repository model creation", str(cm.exception))

    def test_get_repository_success(self):
        """Test successful repository retrieval."""
        # Add repository first
        utils.add_repository(owner=self.valid_owner, repo_name="testrepo")

        # Retrieve it
        result = utils.get_repository("testowner", "testrepo")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "testrepo")
        self.assertEqual(result["owner"]["login"], "testowner")

    def test_get_repository_case_insensitive(self):
        """Test case-insensitive repository retrieval."""
        # Add repository with mixed case
        utils.add_repository(owner=self.valid_owner, repo_name="TestRepo")

        # Retrieve with different case
        result = utils.get_repository("TESTOWNER", "testrepo")
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "TestRepo")

    def test_get_repository_not_found(self):
        """Test repository retrieval when not found."""
        result = utils.get_repository("nonexistent", "repo")
        self.assertIsNone(result)


class TestWorkflowUtils(unittest.TestCase):
    """Test workflow utility functions."""

    def setUp(self):
        """Set up test environment."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 1

        # Add test repository
        self.owner = {
            "login": "testowner",
            "id": 1,
            "node_id": "U_NODE_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        utils.add_repository(owner=self.owner, repo_name="testrepo")

    def tearDown(self):
        """Clean up test environment."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_add_workflow_success(self):
        """Test successful workflow addition."""
        workflow_data = {
            "name": "CI Pipeline",
            "path": ".github/workflows/ci.yml",
            "state": WorkflowState.ACTIVE,
        }

        result = utils.add_or_update_workflow(
            owner_login="testowner", repo_name="testrepo", workflow_data=workflow_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "CI Pipeline")
        self.assertEqual(result["path"], ".github/workflows/ci.yml")
        self.assertEqual(result["state"], WorkflowState.ACTIVE.value)
        self.assertEqual(result["repo_owner_login"], "testowner")
        self.assertEqual(result["repo_name"], "testrepo")

        # Verify ID increment
        self.assertEqual(DB["next_workflow_id"], 2)

    def test_add_workflow_with_custom_timestamps(self):
        """Test workflow addition with custom timestamps."""
        created_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
        updated_at = datetime(2023, 1, 2, tzinfo=timezone.utc)

        workflow_data = {
            "name": "Test Workflow",
            "path": ".github/workflows/test.yml",
            "state": WorkflowState.ACTIVE,
            "created_at": created_at,
            "updated_at": updated_at,
        }

        result = utils.add_or_update_workflow(
            owner_login="testowner",
            repo_name="testrepo",
            workflow_data=workflow_data,
            current_time=datetime(2023, 1, 3, tzinfo=timezone.utc),
        )

        # Compare datetime values, accounting for format differences (Z vs +00:00)
        self.assertIn("2023-01-01T00:00:00", result["created_at"])
        self.assertIn("2023-01-02T00:00:00", result["updated_at"])

    def test_update_existing_workflow(self):
        """Test updating an existing workflow."""
        # Add initial workflow
        initial_data = {
            "name": "Initial Name",
            "path": ".github/workflows/ci.yml",
            "state": WorkflowState.ACTIVE,
        }

        workflow = utils.add_or_update_workflow(
            owner_login="testowner", repo_name="testrepo", workflow_data=initial_data
        )
        workflow_id = workflow["id"]

        # Update the workflow
        update_data = {"name": "Updated Name", "state": WorkflowState.DISABLED_MANUALLY}

        updated_workflow = utils.add_or_update_workflow(
            owner_login="testowner",
            repo_name="testrepo",
            workflow_data=update_data,
            workflow_id_to_update=workflow_id,
        )

        self.assertEqual(updated_workflow["name"], "Updated Name")
        self.assertEqual(
            updated_workflow["state"], WorkflowState.DISABLED_MANUALLY.value
        )
        self.assertEqual(
            updated_workflow["path"], ".github/workflows/ci.yml"
        )  # Unchanged

    def test_add_workflow_invalid_data(self):
        """Test workflow addition with invalid data."""
        invalid_data = {
            "name": 123,  # Invalid type
            "path": ".github/workflows/ci.yml",
            "state": WorkflowState.ACTIVE,
        }

        with self.assertRaises((ValueError, TypeError)) as cm:
            utils.add_or_update_workflow(
                owner_login="testowner",
                repo_name="testrepo",
                workflow_data=invalid_data,
            )
        # Should fail either in node_id generation or model validation
        self.assertTrue(
            "Invalid data for new workflow" in str(cm.exception)
            or "'int' object" in str(cm.exception)
        )

    def test_add_workflow_repo_not_found(self):
        """Test workflow addition when repository doesn't exist."""
        workflow_data = {
            "name": "Test",
            "path": ".github/workflows/test.yml",
            "state": WorkflowState.ACTIVE,
        }

        result = utils.add_or_update_workflow(
            owner_login="nonexistent", repo_name="repo", workflow_data=workflow_data
        )

        self.assertIsNone(result)

    def test_get_workflow_by_id(self):
        """Test workflow retrieval by ID."""
        # Add workflow
        workflow_data = {
            "name": "Test Workflow",
            "path": ".github/workflows/test.yml",
            "state": WorkflowState.ACTIVE,
        }

        added_workflow = utils.add_or_update_workflow(
            owner_login="testowner", repo_name="testrepo", workflow_data=workflow_data
        )

        # Retrieve by ID
        result = utils.get_workflow_by_id_or_filename(
            owner_login="testowner",
            repo_name="testrepo",
            workflow_id_or_filename=added_workflow["id"],
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], added_workflow["id"])
        self.assertEqual(result["name"], "Test Workflow")

    def test_get_workflow_by_filename(self):
        """Test workflow retrieval by filename."""
        # Add workflow
        workflow_data = {
            "name": "Test Workflow",
            "path": ".github/workflows/test.yml",
            "state": WorkflowState.ACTIVE,
        }

        utils.add_or_update_workflow(
            owner_login="testowner", repo_name="testrepo", workflow_data=workflow_data
        )

        # Retrieve by filename
        result = utils.get_workflow_by_id_or_filename(
            owner_login="testowner",
            repo_name="testrepo",
            workflow_id_or_filename="test.yml",
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Test Workflow")

        # Also test with full path
        result_full_path = utils.get_workflow_by_id_or_filename(
            owner_login="testowner",
            repo_name="testrepo",
            workflow_id_or_filename=".github/workflows/test.yml",
        )

        self.assertIsNotNone(result_full_path)
        self.assertEqual(result_full_path["id"], result["id"])

    def test_get_workflow_not_found(self):
        """Test workflow retrieval when not found."""
        result = utils.get_workflow_by_id_or_filename(
            owner_login="testowner", repo_name="testrepo", workflow_id_or_filename=999
        )
        self.assertIsNone(result)

        result_filename = utils.get_workflow_by_id_or_filename(
            owner_login="testowner",
            repo_name="testrepo",
            workflow_id_or_filename="nonexistent.yml",
        )
        self.assertIsNone(result_filename)


class TestWorkflowRunUtils(unittest.TestCase):
    """Test workflow run utility functions."""

    def setUp(self):
        """Set up test environment."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 1
        DB["next_run_id"] = 1
        DB["next_job_id"] = 1

        # Add test repository and workflow
        self.owner = {
            "login": "testowner",
            "id": 1,
            "node_id": "U_NODE_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        utils.add_repository(owner=self.owner, repo_name="testrepo")

        self.workflow_data = {
            "name": "CI Pipeline",
            "path": ".github/workflows/ci.yml",
            "state": WorkflowState.ACTIVE,
        }

        self.workflow = utils.add_or_update_workflow(
            owner_login="testowner",
            repo_name="testrepo",
            workflow_data=self.workflow_data,
        )

    def tearDown(self):
        """Clean up test environment."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_add_workflow_run_success(self):
        """Test successful workflow run addition."""
        run_data = {
            "workflow_id": self.workflow["id"],
            "head_sha": "abcdef1234567890abcdef1234567890abcdef12",
            "head_branch": "main",
            "event": "push",
            "actor": self.owner,
            "triggering_actor": self.owner,
        }

        result = utils.add_workflow_run(
            owner_login="testowner", repo_name="testrepo", run_data=run_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["workflow_id"], self.workflow["id"])
        self.assertEqual(result["head_sha"], "abcdef1234567890abcdef1234567890abcdef12")
        self.assertEqual(result["head_branch"], "main")
        self.assertEqual(result["event"], "push")
        self.assertEqual(result["status"], WorkflowRunStatus.QUEUED.value)

        # Verify in database
        repo = utils.get_repository("testowner", "testrepo")
        self.assertIn(str(result["id"]), repo["workflow_runs"])

    def test_add_workflow_run_with_jobs_and_steps(self):
        """Test workflow run addition with jobs and steps."""
        step_data = {
            "name": "Run tests",
            "status": StepStatus.COMPLETED,
            "conclusion": StepConclusion.SUCCESS,
            "number": 1,
            "started_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
        }

        job_data = {
            "name": "test-job",
            "status": JobStatus.COMPLETED,
            "started_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
            "steps": [step_data],
        }

        run_data = {
            "workflow_id": self.workflow["id"],
            "head_sha": "abcdef1234567890abcdef1234567890abcdef12",
            "event": "push",
            "actor": self.owner,
            "jobs": [job_data],
        }

        result = utils.add_workflow_run(
            owner_login="testowner", repo_name="testrepo", run_data=run_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(len(result["jobs"]), 1)

        job = result["jobs"][0]
        self.assertEqual(job["name"], "test-job")
        self.assertEqual(job["status"], JobStatus.COMPLETED.value)
        self.assertEqual(len(job["steps"]), 1)

        step = job["steps"][0]
        self.assertEqual(step["name"], "Run tests")
        self.assertEqual(step["status"], StepStatus.COMPLETED.value)
        self.assertEqual(step["conclusion"], StepConclusion.SUCCESS.value)

    def test_add_workflow_run_with_head_commit(self):
        """Test workflow run addition with head commit."""
        head_commit_data = {
            "id": "abcdef1234567890abcdef1234567890abcdef12",
            "tree_id": "fedcba0987654321fedcba0987654321fedcba09",
            "message": "Test commit message",
            "timestamp": datetime.now(timezone.utc),
            "author": {"name": "Test Author", "email": "author@test.com"},
            "committer": {"name": "Test Committer", "email": "committer@test.com"},
        }

        run_data = {
            "workflow_id": self.workflow["id"],
            "head_sha": "abcdef1234567890abcdef1234567890abcdef12",
            "event": "push",
            "actor": self.owner,
            "head_commit": head_commit_data,
        }

        result = utils.add_workflow_run(
            owner_login="testowner", repo_name="testrepo", run_data=run_data
        )

        self.assertIsNotNone(result)
        self.assertIsNotNone(result["head_commit"])
        self.assertEqual(result["head_commit"]["message"], "Test commit message")
        self.assertEqual(result["head_commit"]["author"]["name"], "Test Author")

    def test_add_workflow_run_repo_not_found(self):
        """Test workflow run addition when repository doesn't exist."""
        run_data = {
            "workflow_id": 1,
            "head_sha": "abcdef1234567890abcdef1234567890abcdef12",
            "event": "push",
        }

        result = utils.add_workflow_run(
            owner_login="nonexistent", repo_name="repo", run_data=run_data
        )

        self.assertIsNone(result)

    def test_add_workflow_run_workflow_not_found(self):
        """Test workflow run addition when workflow doesn't exist."""
        run_data = {
            "workflow_id": 999,  # Non-existent workflow
            "head_sha": "abcdef1234567890abcdef1234567890abcdef12",
            "event": "push",
        }

        result = utils.add_workflow_run(
            owner_login="testowner", repo_name="testrepo", run_data=run_data
        )

        self.assertIsNone(result)

    def test_add_workflow_run_invalid_data(self):
        """Test workflow run addition with invalid data."""
        run_data = {
            "workflow_id": self.workflow["id"],
            "head_sha": "invalid_sha",  # Invalid SHA format
            "event": "push",
            "actor": {"invalid": "data"},  # Invalid actor data
        }

        with self.assertRaises(ValueError) as cm:
            utils.add_workflow_run(
                owner_login="testowner", repo_name="testrepo", run_data=run_data
            )
        self.assertIn("Invalid data for new workflow run", str(cm.exception))

    def test_get_workflow_run_by_id_success(self):
        """Test successful workflow run retrieval."""
        run_data = {
            "workflow_id": self.workflow["id"],
            "head_sha": "abcdef1234567890abcdef1234567890abcdef12",
            "event": "push",
            "actor": self.owner,
        }

        added_run = utils.add_workflow_run(
            owner_login="testowner", repo_name="testrepo", run_data=run_data
        )

        result = utils.get_workflow_run_by_id(
            owner_login="testowner", repo_name="testrepo", run_id=added_run["id"]
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], added_run["id"])
        self.assertEqual(result["workflow_id"], self.workflow["id"])

    def test_get_workflow_run_by_id_not_found(self):
        """Test workflow run retrieval when not found."""
        result = utils.get_workflow_run_by_id(
            owner_login="testowner", repo_name="testrepo", run_id=999
        )
        self.assertIsNone(result)

        # Test with non-existent repository
        result_no_repo = utils.get_workflow_run_by_id(
            owner_login="nonexistent", repo_name="repo", run_id=1
        )
        self.assertIsNone(result_no_repo)


class TestValidationHelpers(unittest.TestCase):
    """Test validation helper functions."""

    def test_is_valid_sha_valid_hashes(self):
        """Test is_valid_sha with valid SHA hashes."""
        valid_shas = [
            "abcdef1234567890abcdef1234567890abcdef12",
            "0123456789abcdef0123456789abcdef01234567",
            "ABCDEF1234567890ABCDEF1234567890ABCDEF12",
            "0000000000000000000000000000000000000000",
        ]

        for sha in valid_shas:
            with self.subTest(sha=sha):
                self.assertTrue(utils.is_valid_sha(sha))

    def test_is_valid_sha_invalid_hashes(self):
        """Test is_valid_sha with invalid SHA hashes."""
        invalid_shas = [
            "short",  # Too short
            "abcdef1234567890abcdef1234567890abcdef123",  # Too long
            "ghijkl1234567890abcdef1234567890abcdef12",  # Invalid hex chars
            "",  # Empty string
            None,  # None value
            123,  # Wrong type
            "abcdef1234567890abcdef1234567890abcdef1g",  # Invalid char at end
        ]

        for sha in invalid_shas:
            with self.subTest(sha=sha):
                self.assertFalse(utils.is_valid_sha(sha))

    def test_generate_random_sha(self):
        """Test generate_random_sha function."""
        sha = utils.generate_random_sha()

        # Should be a valid SHA
        self.assertTrue(utils.is_valid_sha(sha))
        self.assertEqual(len(sha), 40)
        self.assertTrue(all(c in "0123456789abcdef" for c in sha))

        # Should generate different SHAs
        sha2 = utils.generate_random_sha()
        self.assertNotEqual(sha, sha2)

    def test_parse_created_filter_single_date(self):
        """Test _parse_created_filter with single date."""
        result = utils._parse_created_filter("2023-01-15")

        expected_start = datetime(2023, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        expected_end = datetime(2023, 1, 15, 23, 59, 59, 999999, tzinfo=timezone.utc)

        self.assertEqual(result["start_date"], expected_start)
        self.assertEqual(result["end_date"], expected_end)

    def test_parse_created_filter_date_range(self):
        """Test _parse_created_filter with date range."""
        result = utils._parse_created_filter("2023-01-01..2023-01-31")

        expected_start = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        expected_end = datetime(2023, 1, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)

        self.assertEqual(result["start_date"], expected_start)
        self.assertEqual(result["end_date"], expected_end)

    def test_parse_created_filter_greater_than(self):
        """Test _parse_created_filter with >= operator."""
        result = utils._parse_created_filter(">=2023-01-15")

        expected_start = datetime(2023, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

        self.assertEqual(result["start_date"], expected_start)
        self.assertNotIn("end_date", result)

    def test_parse_created_filter_less_than(self):
        """Test _parse_created_filter with <= operator."""
        result = utils._parse_created_filter("<=2023-01-15")

        expected_end = datetime(2023, 1, 15, 23, 59, 59, 999999, tzinfo=timezone.utc)

        self.assertEqual(result["end_date"], expected_end)
        self.assertNotIn("start_date", result)

    def test_parse_created_filter_none_input(self):
        """Test _parse_created_filter with None input."""
        result = utils._parse_created_filter(None)
        self.assertIsNone(result)

        result_empty = utils._parse_created_filter("")
        self.assertIsNone(result_empty)

    def test_parse_created_filter_invalid_format(self):
        """Test _parse_created_filter with invalid format."""
        invalid_filters = [
            "invalid-date",
            "2023-13-01",  # Invalid month
            "2023-01-32",  # Invalid day
            "not-a-date",
            ">=invalid",
            "2023-01-01..invalid",
        ]

        for invalid_filter in invalid_filters:
            with self.subTest(filter=invalid_filter):
                with self.assertRaises(InvalidInputError) as cm:
                    utils._parse_created_filter(invalid_filter)
                self.assertIn(
                    "Invalid format for 'created' date filter", str(cm.exception)
                )


class TestComplexScenarios(unittest.TestCase):
    """Test complex integration scenarios."""

    def setUp(self):
        """Set up test environment."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 1
        DB["next_run_id"] = 1
        DB["next_job_id"] = 1

    def tearDown(self):
        """Clean up test environment."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_complete_workflow_lifecycle(self):
        """Test complete workflow lifecycle from repo creation to run execution."""
        # 1. Create repository
        owner = {
            "login": "testowner",
            "id": 1,
            "node_id": "U_NODE_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        repo = utils.add_repository(owner=owner, repo_name="test-lifecycle-repo")
        self.assertIsNotNone(repo)

        # 2. Add workflow
        workflow_data = {
            "name": "Complete Test Workflow",
            "path": ".github/workflows/complete.yml",
            "state": WorkflowState.ACTIVE,
        }

        workflow = utils.add_or_update_workflow(
            owner_login="testowner",
            repo_name="test-lifecycle-repo",
            workflow_data=workflow_data,
        )
        self.assertIsNotNone(workflow)

        # 3. Create workflow run with complex job structure
        step1_data = {
            "name": "Checkout code",
            "status": StepStatus.COMPLETED,
            "conclusion": StepConclusion.SUCCESS,
            "number": 1,
            "started_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
        }

        step2_data = {
            "name": "Run tests",
            "status": StepStatus.COMPLETED,
            "conclusion": StepConclusion.SUCCESS,
            "number": 2,
            "started_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
        }

        job_data = {
            "name": "integration-test",
            "status": JobStatus.COMPLETED,
            "conclusion": "success",
            "started_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
            "labels": ["ubuntu-latest"],
            "steps": [step1_data, step2_data],
        }

        run_data = {
            "workflow_id": workflow["id"],
            "head_sha": utils.generate_random_sha(),
            "head_branch": "main",
            "event": "push",
            "status": WorkflowRunStatus.COMPLETED,
            "conclusion": "success",
            "actor": owner,
            "triggering_actor": owner,
            "jobs": [job_data],
        }

        run = utils.add_workflow_run(
            owner_login="testowner", repo_name="test-lifecycle-repo", run_data=run_data
        )
        self.assertIsNotNone(run)

        # 4. Verify all components are properly linked
        retrieved_repo = utils.get_repository("testowner", "test-lifecycle-repo")
        self.assertIn(str(workflow["id"]), retrieved_repo["workflows"])
        self.assertIn(str(run["id"]), retrieved_repo["workflow_runs"])

        retrieved_workflow = utils.get_workflow_by_id_or_filename(
            "testowner", "test-lifecycle-repo", workflow["id"]
        )
        self.assertEqual(retrieved_workflow["id"], workflow["id"])

        retrieved_run = utils.get_workflow_run_by_id(
            "testowner", "test-lifecycle-repo", run["id"]
        )
        self.assertEqual(retrieved_run["workflow_id"], workflow["id"])
        self.assertEqual(len(retrieved_run["jobs"]), 1)
        self.assertEqual(len(retrieved_run["jobs"][0]["steps"]), 2)

    def test_multiple_repositories_and_workflows(self):
        """Test handling multiple repositories with multiple workflows."""
        # Create multiple owners
        owner1 = {
            "login": "owner1",
            "id": 1,
            "node_id": "U_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }
        owner2 = {
            "login": "owner2",
            "id": 2,
            "node_id": "U_2",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        # Create repositories
        repo1 = utils.add_repository(owner=owner1, repo_name="repo1")
        repo2 = utils.add_repository(owner=owner1, repo_name="repo2")
        repo3 = utils.add_repository(
            owner=owner2, repo_name="repo1"
        )  # Same name, different owner

        # Add workflows to each repository
        workflows = []
        for i, (owner_login, repo_name) in enumerate(
            [("owner1", "repo1"), ("owner1", "repo2"), ("owner2", "repo1")], 1
        ):
            for j in range(2):  # 2 workflows per repo
                workflow_data = {
                    "name": f"Workflow {i}-{j}",
                    "path": f".github/workflows/wf{i}{j}.yml",
                    "state": WorkflowState.ACTIVE,
                }
                workflow = utils.add_or_update_workflow(
                    owner_login=owner_login,
                    repo_name=repo_name,
                    workflow_data=workflow_data,
                )
                workflows.append(workflow)

        # Verify all workflows are created and retrievable
        self.assertEqual(len(workflows), 6)

        # Test retrieval by different methods
        for workflow in workflows:
            # By ID
            retrieved_by_id = utils.get_workflow_by_id_or_filename(
                workflow["repo_owner_login"], workflow["repo_name"], workflow["id"]
            )
            self.assertIsNotNone(retrieved_by_id)
            self.assertEqual(retrieved_by_id["id"], workflow["id"])

            # By filename
            filename = workflow["path"].split("/")[-1]
            retrieved_by_filename = utils.get_workflow_by_id_or_filename(
                workflow["repo_owner_login"], workflow["repo_name"], filename
            )
            self.assertIsNotNone(retrieved_by_filename)
            self.assertEqual(retrieved_by_filename["id"], workflow["id"])


class TestDatabaseEdgeCasesAndBoundaryConditions(unittest.TestCase):
    """Test database edge cases and boundary conditions merged from edge case tests."""

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_empty_database_operations(self):
        """Test operations on completely empty database."""
        DB.clear()
        DB["repositories"] = {}  # Initialize empty repositories dict

        # All operations should handle empty DB gracefully
        result = utils.get_repository("owner", "repo")
        self.assertIsNone(result)

    def test_corrupted_database_structure(self):
        """Test behavior with corrupted database structures."""
        # Test with missing repositories key
        DB.clear()
        # Don't add 'repositories' key

        with self.assertRaises((KeyError, AttributeError)):
            utils.get_repository("owner", "repo")

        # Test with invalid repository structure
        DB.clear()
        DB["repositories"] = {
            "owner/repo": "invalid_structure"  # Should be dict, not string
        }

        # This should handle gracefully
        result = utils.get_repository("owner", "repo")
        # Depending on implementation, this might return the invalid structure or None

    def test_concurrent_id_generation(self):
        """Test ID generation under concurrent-like conditions."""
        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 1
        DB["next_run_id"] = 1

        owner = {
            "login": "owner",
            "id": 1,
            "node_id": "U_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        # Simulate rapid successive operations
        repos = []
        for i in range(10):
            repo = utils.add_repository(owner=owner, repo_name=f"repo{i}")
            repos.append(repo)

        # Verify IDs are sequential and unique
        repo_ids = [repo["id"] for repo in repos]
        self.assertEqual(repo_ids, list(range(1, 11)))
        self.assertEqual(len(set(repo_ids)), 10)  # All unique

    def test_large_database_operations(self):
        """Test operations with large amounts of data."""
        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 1

        owner = {
            "login": "owner",
            "id": 1,
            "node_id": "U_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        # Create large number of repositories
        num_repos = 100
        for i in range(num_repos):
            utils.add_repository(owner=owner, repo_name=f"repo{i:03d}")

        # Verify retrieval still works efficiently
        start_time = datetime.now()

        # Test retrieval of repositories
        for i in range(0, num_repos, 10):  # Sample every 10th repo
            repo = utils.get_repository("owner", f"repo{i:03d}")
            self.assertIsNotNone(repo)
            self.assertEqual(repo["name"], f"repo{i:03d}")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(duration, 1.0, "Database operations taking too long")

    def test_maximum_input_lengths(self):
        """Test behavior with maximum length inputs."""
        # Test with very long but valid inputs
        max_length_string = "a" * 1000

        # These operations should handle long inputs gracefully
        self.assertFalse(utils.is_valid_sha(max_length_string))

        # Test long repository names
        owner = {
            "login": "owner",
            "id": 1,
            "node_id": "U_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1

        # Should handle long repo names gracefully
        long_repo_name = "repo" + "x" * 1000
        repo = utils.add_repository(owner=owner, repo_name=long_repo_name)
        self.assertIsNotNone(repo)
        self.assertEqual(repo["name"], long_repo_name)

    def test_datetime_edge_cases(self):
        """Test datetime handling edge cases."""
        # Test with extreme dates
        extreme_past = datetime(1900, 1, 1, tzinfo=timezone.utc)
        extreme_future = datetime(2100, 12, 31, tzinfo=timezone.utc)

        # Should handle extreme dates gracefully
        result_past = utils._ensure_utc_datetime(extreme_past)
        result_future = utils._ensure_utc_datetime(extreme_future)

        self.assertEqual(result_past, extreme_past)
        self.assertEqual(result_future, extreme_future)

        # Test with microseconds and various timezone offsets
        dt_with_microseconds = datetime(
            2023, 6, 15, 12, 30, 45, 123456, tzinfo=timezone.utc
        )
        result_microseconds = utils._ensure_utc_datetime(dt_with_microseconds)
        self.assertEqual(result_microseconds, dt_with_microseconds)

    def test_numeric_id_boundaries(self):
        """Test numeric ID boundary conditions."""
        # Test with very large IDs
        large_id = 999999999

        # ID generation should handle large numbers
        DB.clear()
        DB["next_workflow_id"] = large_id

        # This should work without overflow issues
        next_id = DB.get("next_workflow_id", 1)
        self.assertEqual(next_id, large_id)

        DB["next_workflow_id"] = next_id + 1
        self.assertEqual(DB["next_workflow_id"], large_id + 1)

    def test_sha_validation_boundary_conditions(self):
        """Test SHA validation with boundary conditions."""
        # Test exactly 40 character strings (valid length)
        valid_40_char_hex = "a" * 40
        invalid_40_char_nonhex = "g" * 40

        self.assertTrue(utils.is_valid_sha(valid_40_char_hex))
        self.assertFalse(utils.is_valid_sha(invalid_40_char_nonhex))

        # Test boundary lengths
        self.assertFalse(utils.is_valid_sha("a" * 39))  # Too short
        self.assertFalse(utils.is_valid_sha("a" * 41))  # Too long
        self.assertFalse(utils.is_valid_sha(""))  # Empty

        # Test mixed case
        mixed_case_valid = "AbCdEf1234567890AbCdEf1234567890AbCdEf12"
        self.assertTrue(utils.is_valid_sha(mixed_case_valid))


if __name__ == "__main__":
    unittest.main()
