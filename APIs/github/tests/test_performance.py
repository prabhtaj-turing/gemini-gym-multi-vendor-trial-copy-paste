import unittest
import time
import psutil
import os
import gc
import concurrent.futures

from common_utils.base_case import BaseTestCaseWithErrorHandler
from github.SimulationEngine.db import DB
from github.repositories import (
    create_repository,
    create_branch,
    push_files,
    list_commits,
    search_repositories,
)
from github.pull_requests import create_pull_request, merge_pull_request


class TestGitHubPerformance(BaseTestCaseWithErrorHandler):
    """Performance tests for GitHub API operations."""

    def setUp(self):
        super().setUp()
        self.process = psutil.Process(os.getpid())

        # Minimal seed: single user, inferred CurrentUser, empty tables
        DB.clear()
        DB.update({
            "Users": [
                {
                    "login": "owner",
                    "id": 1,
                    "node_id": "U1",
                    "type": "User",
                    "site_admin": False,
                    "name": "Owner User",
                    "email": "owner@example.com",
                    "public_repos": 0,
                    "public_gists": 0,
                    "followers": 0,
                    "following": 0,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
            ],
            "CurrentUser": {"id": 1, "login": "owner"},
            "Repositories": [],
            "Branches": [],
            "PullRequests": [],
            "RepositoryCollaborators": [],
            "FileContents": {},
        })

        # Create a repository with initial commit and main branch
        repo_resp = create_repository(name="perf-repo", description="Perf repo", private=False, auto_init=True)
        self.repo_name = repo_resp["name"]
        self.owner_login = "owner"
        self.repo = next(r for r in DB["Repositories"] if r["name"] == self.repo_name)
        self.repo_id = self.repo["id"]
        # Ensure collaborator permissions for merges
        DB["RepositoryCollaborators"].append({"repository_id": self.repo_id, "user_id": 1, "permission": "admin"})

    def tearDown(self):
        super().tearDown()
        DB.clear()

    def _main_branch_sha(self):
        default_branch = self.repo.get("default_branch") or "main"
        br = next(b for b in DB["Branches"] if b["repository_id"] == self.repo_id and b["name"] == default_branch)
        return br["commit"]["sha"], default_branch

    def test_memory_usage_core_operations(self):
        """Test memory usage during repeated search and list commits operations."""
        initial_memory = self.process.memory_info().rss

        for _ in range(50):
            search_repositories(query="perf-repo user:owner", sort="stars")
            list_commits(owner=self.owner_login, repo=self.repo_name, sha="main")

        gc.collect()
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory

        self.assertLess(
            memory_increase,
            8 * 1024 * 1024,
            f"Memory increase {memory_increase / 1024 / 1024:.2f}MB exceeds 8MB limit",
        )

    def test_push_response_time(self):
        """Test push_files execution response time."""
        base_sha, _ = self._main_branch_sha()
        # Create feature branch
        create_branch(owner=self.owner_login, repo=self.repo_name, branch="perf-feature", sha=base_sha)

        start_time = time.time()
        result = push_files(
            owner=self.owner_login,
            repo=self.repo_name,
            branch="perf-feature",
            files=[{"path": "README.md", "content": "Hello perf\n"}],
            message="perf: add readme",
        )
        execution_time = time.time() - start_time

        self.assertLess(execution_time, 0.8, f"push_files() took {execution_time:.3f}s, should be < 0.8s")
        self.assertIn("commit_sha", result)

    def test_search_performance_large_dataset(self):
        """Test search performance with a larger repository dataset."""
        # Add additional 500 public repositories (ensure language and score present to avoid None issues)
        for i in range(1, 501):
            DB["Repositories"].append({
                "id": max([r["id"] for r in DB["Repositories"]] + [0]) + 1,
                "node_id": f"R{i}",
                "name": f"perf-repo-{i}",
                "full_name": f"owner/perf-repo-{i}",
                "private": False,
                "owner": {"login": "owner", "id": 1, "type": "User"},
                "description": "",
                "fork": False,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "pushed_at": "2024-01-01T00:00:00Z",
                "default_branch": "main",
                "stargazers_count": 0,
                "watchers_count": 0,
                "forks_count": 0,
                "open_issues_count": 0,
                "language": "Python",
                "score": 0.0,
            })

        start_time = time.time()
        result = search_repositories(query="perf-repo user:owner", per_page=100, sort="stars")
        execution_time = time.time() - start_time

        self.assertLess(execution_time, 1.5, f"search_repositories() took {execution_time:.3f}s, should be < 1.5s")
        self.assertGreaterEqual(result["search_results"]["total_count"], 500)

    def test_concurrent_search(self):
        """Test performance under concurrent search operations."""
        def worker(q):
            return search_repositories(query=q, per_page=100, sort="stars")

        queries = ["perf-repo user:owner", "user:owner", "is:public"]
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(worker, q) for q in queries for _ in range(5)]
            results = [f.result() for f in futures]
        execution_time = time.time() - start_time

        self.assertLess(execution_time, 5.0, f"Concurrent search took {execution_time:.3f}s, should be < 5.0s")
        self.assertTrue(all("search_results" in r for r in results))

    def test_mixed_operations_performance(self):
        """Test performance with mixed operations simulating real usage."""
        base_sha, _ = self._main_branch_sha()
        start_time = time.time()

        for i in range(5):
            # basic read ops
            search_repositories(query="perf-repo user:owner", sort="stars")
            list_commits(owner=self.owner_login, repo=self.repo_name, sha="main")

            # create a short-lived feature branch and PR, then merge
            br_name = f"perf-mix-{i}"
            create_branch(owner=self.owner_login, repo=self.repo_name, branch=br_name, sha=base_sha)
            push_files(
                owner=self.owner_login,
                repo=self.repo_name,
                branch=br_name,
                files=[{"path": f"file-{i}.txt", "content": f"data {i}\n"}],
                message=f"perf mix {i}",
            )
            pr = create_pull_request(owner="owner", repo=self.repo_name, title=f"Mix {i}", head=br_name, base="main")
            merge_pull_request(owner="owner", repo=self.repo_name, pull_number=pr["number"], merge_method="merge")

        execution_time = time.time() - start_time
        self.assertLess(execution_time, 8.0, f"Mixed operations took {execution_time:.3f}s, should be < 8.0s")


if __name__ == "__main__":
    unittest.main()


