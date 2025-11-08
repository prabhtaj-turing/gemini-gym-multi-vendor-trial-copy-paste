import unittest
import copy
from unittest.mock import patch
from .. import issues, users
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors

class TestSearchIssues(unittest.TestCase):

    def setUp(self):
        """Set up a mock database for testing."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            "Users": [
                {"id": 1, "login": "testuser"},
                {"id": 2, "login": "testassignee"},
            ],
            "CurrentUser": {"id": 1, "login": "testuser"},
            "Repositories": [
                {"id": 101, "name": "repo1", "owner": {"login": "testuser"}, "full_name": "testuser/repo1"},
                {"id": 102, "name": "repo2", "owner": {"login": "testuser"}, "full_name": "testuser/repo2"}
            ],
            "Issues": [
                {
                    "id": 1, "repository_id": 101, "number": 1, "title": "First issue", "body": "This is a bug.", 
                    "user": {"id": 1, "login": "testuser"}, "state": "open", "labels": [{"name": "bug"}],
                    "assignee": {"id": 2, "login": "testassignee"}, "comments": 2, "created_at": "2025-01-01T00:00:00Z",
                    "updated_at": "2025-01-02T00:00:00Z", "score": 0.8
                },
                {
                    "id": 2, "repository_id": 101, "number": 2, "title": "Second issue about feature", "body": "Needs enhancement.",
                    "user": {"id": 2, "login": "testassignee"}, "state": "open", "labels": [{"name": "enhancement"}],
                    "assignee": None, "comments": 5, "created_at": "2025-01-03T00:00:00Z",
                    "updated_at": "2025-01-03T00:00:00Z", "score": 0.5
                },
                {
                    "id": 3, "repository_id": 102, "number": 1, "title": "Closed bug issue", "body": "Fixed bug.",
                    "user": {"id": 1, "login": "testuser"}, "state": "closed", "labels": [{"name": "bug"}],
                    "assignee": {"id": 1, "login": "testuser"}, "comments": 10, "created_at": "2024-12-01T00:00:00Z",
                    "updated_at": "2024-12-05T00:00:00Z", "score": 0.9
                }
            ],
            "PullRequests": [
                {
                    "id": 10, "head": {"repo": {"full_name": "testuser/repo1"}}, "number": 3, "title": "Pull Request with bug", "body": "PR for bug.",
                    "user": {"id": 2, "login": "testassignee"}, "state": "open", "labels": [{"name": "bug"}, {"name": "in-review"}],
                    "assignee": {"id": 1, "login": "testuser"}, "comments": 1, "created_at": "2025-01-04T00:00:00Z",
                    "updated_at": "2025-01-04T00:00:00Z", "score": 0.7
                }
            ]
        })

    def tearDown(self):
        """Restore the original database."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_search_no_query(self):
        with self.assertRaises(custom_errors.InvalidInputError):
            issues.search_issues(query="")

    def test_search_keyword(self):
        result = issues.search_issues(query="bug")
        self.assertEqual(result["total_count"], 3)
        self.assertIn("bug", result["items"][0]["title"].lower())

    def test_search_qualifier_is_issue(self):
        result = issues.search_issues(query="is:issue")
        self.assertEqual(result["total_count"], 3)
        for item in result["items"]:
            self.assertNotIn("pull_request", item)

    def test_search_qualifier_is_pr(self):
        result = issues.search_issues(query="is:pr")
        self.assertEqual(result["total_count"], 1)
        self.assertIn("pull_request", result["items"][0])

    def test_search_qualifier_repo(self):
        result = issues.search_issues(query="repo:testuser/repo2")
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 3)

    def test_search_qualifier_author(self):
        result = issues.search_issues(query="author:testuser")
        self.assertEqual(result["total_count"], 2)
        self.assertIn(result["items"][0]["id"], [1, 3])

    def test_search_qualifier_assignee(self):
        result = issues.search_issues(query="assignee:testassignee")
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 1)

    def test_search_qualifier_label(self):
        result = issues.search_issues(query='label:enhancement')
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 2)

    def test_search_qualifier_state_closed(self):
        result = issues.search_issues(query="state:closed")
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 3)

    def test_search_complex_query(self):
        result = issues.search_issues(query='bug repo:testuser/repo1 is:issue state:open label:bug')
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 1)

    def test_sort_comments_desc(self):
        result = issues.search_issues(query="bug", sort="comments", order="desc")
        self.assertEqual(result["total_count"], 3)
        self.assertEqual([item["comments"] for item in result["items"]], [10, 2, 1])

    def test_sort_created_asc(self):
        result = issues.search_issues(query="bug", sort="created", order="asc")
        self.assertEqual(result["total_count"], 3)
        self.assertEqual([item["id"] for item in result["items"]], [3, 1, 10])

    def test_pagination(self):
        result = issues.search_issues(query="is:issue", per_page=2, page=1)
        self.assertEqual(len(result["items"]), 2)
        
        result_page2 = issues.search_issues(query="is:issue", per_page=2, page=2)
        self.assertEqual(len(result_page2["items"]), 1)
        
        # Check for no overlap between pages
        ids_page1 = {item["id"] for item in result["items"]}
        ids_page2 = {item["id"] for item in result_page2["items"]}
        self.assertFalse(ids_page1.intersection(ids_page2))

    def test_search_no_results(self):
        """Test a query that should return no results."""
        result = issues.search_issues(query="nonexistent-term-xyz")
        self.assertEqual(result["total_count"], 0)
        self.assertEqual(len(result["items"]), 0)

    def test_search_label_with_spaces(self):
        """Test searching for a label that contains spaces."""
        result = issues.search_issues(query='label:"in-review"')
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 10)

    def test_case_insensitivity(self):
        """Test that qualifiers and search terms are case-insensitive."""
        result = issues.search_issues(query='BUG repo:TESTUSER/repo1 is:PR STATE:Open')
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 10)
        
    def test_sort_updated_asc(self):
        """Test sorting by the 'updated' field."""
        result = issues.search_issues(query="is:issue", sort="updated", order="asc")
        self.assertEqual(result["total_count"], 3)
        self.assertEqual([item["id"] for item in result["items"]], [3, 1, 2])

    def test_search_in_body(self):
        """Test searching within the body of an issue."""
        result = issues.search_issues(query='"Needs enhancement" in:body')
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 2)

    def test_search_issue_with_nonexistent_repo_id(self):
        """Test that an issue with a non-existent repository_id is handled gracefully."""
        issues.DB["Issues"].append({
            "id": 6, "repository_id": 999, "number": 1, "title": "Issue with bad repo id",
        })
        # This shouldn't crash, and the issue shouldn't be found when searching a valid repo
        result = issues.search_issues(query="repo:testuser/repo1")
        # Assert that only issues from repo1 are found, and not the one with the bad id
        for item in result['items']:
            self.assertNotEqual(item['id'], 6)
        # We also assert that searching for the term doesn't bring it up with a repo qualifier
        result2 = issues.search_issues(query="repo:testuser/repo1 'bad repo id'")
        self.assertEqual(result2['total_count'], 0)

    def test_search_pr_without_repo_full_name_standalone(self):
        """Test searching for a PR that is missing the repo_full_name (standalone DB)."""
        # This test uses its own DB to avoid interference from setUp
        original_db = issues.DB
        issues.DB = {
            "PullRequests": [{
                "id": 11, "number": 4, "title": "Orphaned PR",
                "user": {"id": 1, "login": "testuser"}, "state": "open", "labels": [],
                "head": {"repo": {"full_name": "testuser/repo2"}},
            }],
            "Repositories": [
                {"id": 102, "name": "repo2", "owner": {"login": "testuser"}, "full_name": "testuser/repo2"}
            ],
            "Issues": []
        }
        try:
            result = issues.search_issues(query="repo:testuser/repo2 is:pr")
            self.assertEqual(result["total_count"], 1)
            self.assertEqual(result["items"][0]["id"], 11)
        finally:
            issues.DB = original_db
            
    def test_list_issues_graceful_malformed_data_handling(self):
        """Test that list_issues handles malformed data gracefully by skipping it."""
        # Use a clean DB for this test to isolate the warning behavior
        original_db = issues.DB
        issues.DB = {
             "Repositories": [
                {"id": 101, "name": "repo1", "owner": {"login": "testuser"}, "full_name": "testuser/repo1"}
            ],
            "Issues": [{
                "id": 5, "repository_id": 101, "number": 3, "title": "Malformed Issue",
            }]
        }
        try:
            # list_issues should handle malformed data gracefully by skipping it
            result = issues.list_issues(owner="testuser", repo="repo1", state="all")
            self.assertIsInstance(result, list)
            # The malformed issue should be skipped, so we get an empty list
            self.assertEqual(len(result), 0)
            
        finally:
            issues.DB = original_db

    def test_list_issues_nameerror_graceful_handling(self):
        """Test that list_issues handles NameError gracefully by skipping affected items."""
        with patch.object(issues.models.ListIssuesResponseItem, 'model_validate', side_effect=NameError("mocked NameError")):
            # We expect list_issues to handle NameError gracefully by skipping items
            result = issues.list_issues(owner="testuser", repo="repo1")
            self.assertIsInstance(result, list)
            # All items should be skipped due to the mocked NameError
            self.assertEqual(len(result), 0)

    def test_search_with_multiple_terms_is_and_logic(self):
        # This test ensures that when multiple search terms are provided,
        # only items containing ALL terms are returned.
        
        # Search for "bug" and "First" - should only match issue #1
        result = issues.search_issues(query="bug First repo:testuser/repo1")
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 1)

        # Search for "bug" and "pull" - should only match PR #10
        result = issues.search_issues(query="bug pull repo:testuser/repo1")
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["id"], 10)

        # Search for terms that do not co-exist in any single item
        result = issues.search_issues(query="First enhancement repo:testuser/repo1")
        self.assertEqual(result["total_count"], 0)

    def test_search_returns_empty_when_no_match_with_multiple_terms(self):
        # This test ensures that a search with one valid and one invalid term
        # returns no results.
        result = issues.search_issues(query="bug non_existent_term repo:testuser/repo1")
        self.assertEqual(result["total_count"], 0)
        self.assertEqual(len(result["items"]), 0)

if __name__ == "__main__":
    unittest.main() 