"""
Performance Tests for GitHub Actions Module

These tests measure execution time, memory usage, throughput, and other
performance characteristics of the GitHub Actions simulation engine.
Performance tests help identify bottlenecks and ensure scalability.
"""

import unittest
import time
import gc
import sys
import os
import threading
import concurrent.futures
from datetime import datetime, timezone
from typing import Dict, Any, List
import tracemalloc

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add the parent directory to the path to import github_actions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PerformanceTestMixin:
    """Mixin class providing performance measurement utilities."""

    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time

    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage during function execution."""
        tracemalloc.start()
        gc.collect()  # Clean up before measurement

        start_memory = tracemalloc.get_traced_memory()[0]
        result = func(*args, **kwargs)
        end_memory = tracemalloc.get_traced_memory()[0]

        tracemalloc.stop()
        memory_delta = end_memory - start_memory
        return result, memory_delta

    def get_process_memory(self):
        """Get current process memory usage."""
        if not PSUTIL_AVAILABLE:
            # Fallback to a simple alternative
            return 0  # Return 0 if psutil not available
        process = psutil.Process(os.getpid())
        return process.memory_info().rss  # Resident Set Size in bytes

    def ensure_repository_exists(self, owner, repo):
        """Ensure a repository exists for testing (test isolation helper)."""
        from github_actions.SimulationEngine import utils
        from github_actions.SimulationEngine.db import DB

        # Check if database has been cleared by another test
        if "repositories" not in DB:
            DB["repositories"] = {}
        if "next_repo_id" not in DB:
            DB["next_repo_id"] = 1
        if "next_workflow_id" not in DB:
            DB["next_workflow_id"] = 100
        if "next_run_id" not in DB:
            DB["next_run_id"] = 1000

        if not utils.get_repository(owner, repo):
            owner_data = {
                "login": owner,
                "id": 1,
                "node_id": "MDQ6VXNlcjE=",
                "type": "User",
                "site_admin": False,
            }
            utils.add_repository(owner_data, repo)

            # Add a default workflow for testing
            workflow_data = {
                "name": f"Test Workflow for {owner}/{repo}",
                "path": ".github/workflows/test.yml",
                "state": "active",
            }
            utils.add_or_update_workflow(owner, repo, workflow_data)

        return True

    def _safe_call(self, func, *args, **kwargs):
        """Safely call an API function with guaranteed repository existence."""
        # COMPLETELY RESET DATABASE before every API call to ensure clean state
        from github_actions.SimulationEngine.db import DB
        from github_actions.SimulationEngine import utils

        # Extract owner/repo from common argument patterns
        owner, repo = None, None
        if len(args) >= 2:
            owner, repo = args[0], args[1]
        elif "owner" in kwargs and "repo" in kwargs:
            owner, repo = kwargs["owner"], kwargs["repo"]

        if owner and repo:
            # FORCE complete database reset and reinitialization
            DB.clear()
            DB["repositories"] = {}
            DB["next_repo_id"] = 1
            DB["next_workflow_id"] = 100
            DB["next_run_id"] = 1000
            DB["next_job_id"] = 1

            # Force create repository with error handling
            try:
                owner_data = {
                    "login": owner,
                    "id": 1,
                    "node_id": "MDQ6VXNlcjE=",
                    "type": "User",
                    "site_admin": False,
                }
                repo_result = utils.add_repository(owner_data, repo)

                # Force create workflow
                workflow_data = {
                    "name": f"Test Workflow for {owner}/{repo}",
                    "path": ".github/workflows/test.yml",
                    "state": "active",
                }
                workflow_result = utils.add_or_update_workflow(
                    owner, repo, workflow_data
                )

                # Verify repository was actually created
                if not utils.get_repository(owner, repo):
                    # If repository creation silently failed, try a different approach
                    print(
                        f"WARNING: Repository {owner}/{repo} creation failed silently"
                    )
            except Exception as e:
                # Repository creation failed, let's manually add to DB
                print(f"Repository creation failed: {e}")
                # Fallback: directly add minimal data to DB
                repo_key = f"{owner.lower()}/{repo.lower()}"
                DB["repositories"][repo_key] = {
                    "id": 1,
                    "node_id": "MDQ6VXNlcjE=",
                    "name": repo,
                    "owner": owner_data,
                    "private": False,
                    "workflows": {
                        "100": {
                            "id": 100,
                            "name": f"Test Workflow for {owner}/{repo}",
                            "path": ".github/workflows/test.yml",
                            "state": "active",
                        }
                    },
                    "workflow_runs": {},
                }

        return func(*args, **kwargs)


class TestAPIResponseTimes(unittest.TestCase, PerformanceTestMixin):
    """Test response times for API operations."""

    def setUp(self):
        """Set up test environment with sample data."""
        from github_actions.SimulationEngine.db import DB
        from github_actions.SimulationEngine import utils

        # Clear and initialize database
        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 100
        DB["next_run_id"] = 1000

        # Create test repository
        self.owner = "perftest"
        self.repo = "perftest-repo"

        self.ensure_repository_exists(self.owner, self.repo)

        # Add multiple workflows for testing
        for i in range(10):
            workflow_data = {
                "name": f"Performance Test Workflow {i}",
                "path": f".github/workflows/perf-test-{i}.yml",
                "state": "active",
            }
            utils.add_or_update_workflow(self.owner, self.repo, workflow_data)

    def test_list_workflows_response_time(self):
        """Test response time for listing workflows."""
        from github_actions import list_workflows_module

        # Ensure repository exists (test isolation)
        self.ensure_repository_exists(self.owner, self.repo)

        result, execution_time = self.measure_execution_time(
            list_workflows_module.list_workflows, self.owner, self.repo
        )

        self.assertIsInstance(result, dict)
        self.assertLess(
            execution_time,
            1.0,
            f"list_workflows took {execution_time:.3f}s, expected < 1.0s",
        )
        print(f"list_workflows execution time: {execution_time:.3f}s")


class TestMemoryUsage(unittest.TestCase, PerformanceTestMixin):
    """Test memory usage characteristics."""

    def setUp(self):
        """Set up test environment."""
        from github_actions.SimulationEngine.db import DB
        from github_actions.SimulationEngine import utils
        from github_actions.SimulationEngine.models import ActorType

        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 100
        DB["next_run_id"] = 1000

        self.owner = "memtest"
        self.repo = "memtest-repo"

        # Forcefully create repository in database
        repo_key = f"{self.owner.lower()}/{self.repo.lower()}"
        owner_data = {
            "login": self.owner,
            "id": 1,
            "node_id": "U_NODE_1",
            "type": ActorType.USER.value,
            "site_admin": False,
        }

        DB["repositories"][repo_key] = {
            "id": 1,
            "node_id": "MDQ6VXNlcjE=",
            "name": self.repo,
            "owner": owner_data,
            "private": False,
            "workflows": {},
            "workflow_runs": {},
        }

    def test_workflow_creation_memory_usage(self):
        """Test memory usage when creating workflows."""
        from github_actions.SimulationEngine import utils

        def create_workflow():
            workflow_data = {
                "name": "Memory Test Workflow",
                "path": ".github/workflows/memtest.yml",
                "state": "active",
            }
            return utils.add_or_update_workflow(self.owner, self.repo, workflow_data)

        result, memory_delta = self.measure_memory_usage(create_workflow)

        self.assertIsInstance(result, dict)
        # Memory usage should be reasonable (less than 1MB for single workflow)
        self.assertLess(
            memory_delta,
            1024 * 1024,
            f"Single workflow creation used {memory_delta} bytes, expected < 1MB",
        )
        print(f"Workflow creation memory usage: {memory_delta} bytes")


class TestDatabasePerformance(unittest.TestCase, PerformanceTestMixin):
    """Test database operation performance."""

    def setUp(self):
        """Set up test environment with sample data."""
        from github_actions.SimulationEngine.db import DB
        from github_actions.SimulationEngine import utils

        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 100
        DB["next_run_id"] = 1000

        self.owner = "dbperf"
        self.repo = "dbperf-repo"

        self.ensure_repository_exists(self.owner, self.repo)

    def test_bulk_workflow_insertion_performance(self):
        """Test performance of inserting many workflows."""
        from github_actions.SimulationEngine import utils

        def insert_bulk_workflows():
            for i in range(100):
                workflow_data = {
                    "name": f"Bulk Workflow {i}",
                    "path": f".github/workflows/bulk-{i}.yml",
                    "state": "active",
                }
                utils.add_or_update_workflow(self.owner, self.repo, workflow_data)

        result, execution_time = self.measure_execution_time(insert_bulk_workflows)

        # Should complete within reasonable time (< 5 seconds for 100 workflows)
        self.assertLess(
            execution_time,
            5.0,
            f"Inserting 100 workflows took {execution_time:.3f}s, expected < 5.0s",
        )
        print(f"Bulk workflow insertion (100 items): {execution_time:.3f}s")

    def test_workflow_search_performance(self):
        """Test performance of searching workflows."""
        from github_actions.SimulationEngine import utils
        from github_actions import list_workflows_module

        # Add many workflows first
        for i in range(50):
            workflow_data = {
                "name": f"Search Test Workflow {i}",
                "path": f".github/workflows/search-{i}.yml",
                "state": "active",
            }
            utils.add_or_update_workflow(self.owner, self.repo, workflow_data)

        # Test search performance
        result, execution_time = self.measure_execution_time(
            list_workflows_module.list_workflows, self.owner, self.repo
        )

        self.assertIsInstance(result, dict)
        self.assertLess(
            execution_time,
            1.0,
            f"Searching 50 workflows took {execution_time:.3f}s, expected < 1.0s",
        )
        print(f"Workflow search performance (50 items): {execution_time:.3f}s")

    def test_database_state_save_performance(self):
        """Test performance of saving database state."""
        from github_actions.SimulationEngine import db, utils

        # Add substantial data first
        for i in range(20):
            workflow_data = {
                "name": f"Save Test Workflow {i}",
                "path": f".github/workflows/save-{i}.yml",
                "state": "active",
            }
            utils.add_or_update_workflow(self.owner, self.repo, workflow_data)

        def save_database():
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False) as f:
                db.save_state(f.name)
            return True

        result, execution_time = self.measure_execution_time(save_database)

        self.assertLess(
            execution_time,
            2.0,
            f"Database save took {execution_time:.3f}s, expected < 2.0s",
        )
        print(f"Database save performance: {execution_time:.3f}s")


class TestConcurrencyPerformance(unittest.TestCase, PerformanceTestMixin):
    """Test concurrent operation performance."""

    def setUp(self):
        """Set up test environment."""
        from github_actions.SimulationEngine.db import DB
        from github_actions.SimulationEngine import utils

        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 100
        DB["next_run_id"] = 1000

        self.owner = "concurrency"
        self.repo = "concurrency-repo"

        self.ensure_repository_exists(self.owner, self.repo)

        # Add a workflow for testing
        workflow_data = {
            "name": "Concurrency Test Workflow",
            "path": ".github/workflows/concurrency.yml",
            "state": "active",
        }
        utils.add_or_update_workflow(self.owner, self.repo, workflow_data)


class TestScalabilityPerformance(unittest.TestCase, PerformanceTestMixin):
    """Test scalability with larger datasets."""

    def setUp(self):
        """Set up test environment."""
        from github_actions.SimulationEngine.db import DB
        from github_actions.SimulationEngine import utils

        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 100
        DB["next_run_id"] = 1000

        self.owner = "scalability"
        self.repo = "scalability-repo"

        self.ensure_repository_exists(self.owner, self.repo)

    def test_large_workflow_list_performance(self):
        """Test performance with large number of workflows."""
        from github_actions.SimulationEngine import utils
        from github_actions import list_workflows_module

        # Create many workflows
        start_time = time.perf_counter()
        for i in range(200):
            workflow_data = {
                "name": f"Large Scale Workflow {i}",
                "path": f".github/workflows/large-{i}.yml",
                "state": "active",
            }
            utils.add_or_update_workflow(self.owner, self.repo, workflow_data)

        creation_time = time.perf_counter() - start_time
        print(f"Creating 200 workflows: {creation_time:.3f}s")

        # Test listing performance
        result, execution_time = self.measure_execution_time(
            list_workflows_module.list_workflows,
            self.owner,
            self.repo,
            per_page=100,  # Set to maximum allowed per_page
        )

        self.assertIsInstance(result, dict)
        # We can only get 100 per page max, so we'll get the first 100
        self.assertEqual(len(result["workflows"]), 100)
        self.assertLess(
            execution_time,
            2.0,
            f"Listing 200 workflows took {execution_time:.3f}s, expected < 2.0s",
        )
        print(f"Listing 200 workflows: {execution_time:.3f}s")


class TestDataTransformationPerformance(unittest.TestCase, PerformanceTestMixin):
    """Test performance of data transformation operations."""

    def test_model_serialization_performance(self):
        """Test performance of Pydantic model serialization."""
        from github_actions.SimulationEngine.models import WorkflowRun, RepositoryBrief

        # Create complex model instances
        def create_and_serialize_models():
            workflows = []
            for i in range(50):
                repo_brief = RepositoryBrief(
                    id=1,
                    node_id="MDEwOlJlcG9zaXRvcnkx",
                    name="test-repo",
                    full_name="test/test-repo",
                    private=False,
                    owner={
                        "login": "test",
                        "id": 1,
                        "node_id": "MDQ6VXNlcjE=",
                        "type": "User",
                        "site_admin": False,
                    },
                    html_url="https://github.com/test/test-repo",
                    description="Test repository",
                    fork=False,
                    url="https://api.github.com/repos/test/test-repo",
                )

                workflow_run = WorkflowRun(
                    id=i,
                    node_id=f"MDEwOldvcmtmbG93UnVu{i}",
                    workflow_id=100,
                    head_sha=f"sha{i:040d}",
                    head_branch="main",
                    path=".github/workflows/test.yml",
                    run_number=i + 1,
                    event="push",
                    status="completed",
                    conclusion="success",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    run_attempt=1,
                    run_started_at=datetime.now(timezone.utc),
                    repository=repo_brief,
                    repo_owner_login="test",
                    repo_name="test-repo",
                )
                # Convert to dict (serialization)
                workflows.append(workflow_run.model_dump())
            return workflows

        result, execution_time = self.measure_execution_time(
            create_and_serialize_models
        )

        self.assertEqual(len(result), 50)
        self.assertLess(
            execution_time,
            1.0,
            f"Serializing 50 WorkflowRun models took {execution_time:.3f}s, expected < 1.0s",
        )
        print(f"Model serialization performance (50 items): {execution_time:.3f}s")

    def test_file_encoding_performance(self):
        """Test performance of file encoding operations."""
        from github_actions.SimulationEngine import file_utils

        # Create test content of various sizes
        test_data = [b"small content", b"medium content" * 100, b"large content" * 1000]

        for i, content in enumerate(test_data):
            with self.subTest(size=f"size_{i}"):
                # Test encoding performance
                result, execution_time = self.measure_execution_time(
                    file_utils.encode_to_base64, content
                )

                self.assertIsInstance(result, str)
                self.assertLess(
                    execution_time,
                    0.1,
                    f"Encoding {len(content)} bytes took {execution_time:.3f}s, expected < 0.1s",
                )
                print(f"Encoding {len(content)} bytes: {execution_time:.4f}s")

                # Test decoding performance
                decode_result, decode_time = self.measure_execution_time(
                    file_utils.decode_from_base64, result
                )

                self.assertEqual(decode_result, content)
                self.assertLess(
                    decode_time,
                    0.1,
                    f"Decoding {len(result)} chars took {decode_time:.3f}s, expected < 0.1s",
                )
                print(f"Decoding {len(result)} chars: {decode_time:.4f}s")


class TestPerformanceRegression(unittest.TestCase, PerformanceTestMixin):
    """Test for performance regressions in common operations."""

    def setUp(self):
        """Set up comprehensive test environment."""
        from github_actions.SimulationEngine.db import DB
        from github_actions.SimulationEngine import utils

        DB.clear()
        DB["repositories"] = {}
        DB["next_repo_id"] = 1
        DB["next_workflow_id"] = 100
        DB["next_run_id"] = 1000

        # Create multiple repositories and workflows
        for repo_idx in range(5):
            owner = f"perfowner{repo_idx}"
            repo = f"perfrepo{repo_idx}"

            self.ensure_repository_exists(owner, repo)

            # Add workflows to each repo
            for wf_idx in range(10):
                workflow_data = {
                    "name": f"Regression Test Workflow {wf_idx}",
                    "path": f".github/workflows/regression-{wf_idx}.yml",
                    "state": "active",
                }
                utils.add_or_update_workflow(owner, repo, workflow_data)


if __name__ == "__main__":
    # Check if psutil is available for memory monitoring
    try:
        import psutil
    except ImportError:
        print("Warning: psutil not available, some memory tests may be skipped")

    unittest.main(verbosity=2)
