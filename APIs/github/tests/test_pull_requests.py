import unittest
import copy
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Union
from github.SimulationEngine.models import (
    User, Repository, PullRequest, PullRequestItemComment, Commit,
    BaseUser, PullRequestBranchInfo, CommitNested, GitActor, Tree, CommitParent,
    RepositoryCollaborator, CommitFileChange, AddPullRequestReviewCommentResponse, PullRequestResponse
)
from github.SimulationEngine.db import DB
from github.SimulationEngine.custom_errors import (
    NotFoundError, MethodNotAllowedError, ConflictError, ValidationError,
    ForbiddenError, UnprocessableEntityError
)
from github.SimulationEngine.utils import iso_now
from github.SimulationEngine import utils
from github.pull_requests import (
    get_pull_request_files, get_pull_request_status, get_pull_request_reviews,
    merge_pull_request, update_pull_request_branch, add_pull_request_review_comment,
    list_pull_requests, update_pull_request, create_pull_request_review
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCreatePullRequestReview(BaseTestCaseWithErrorHandler): # type: ignore
    @classmethod
    def setUpClass(cls):
        cls.original_db = copy.deepcopy(DB)

    @classmethod
    def tearDownClass(cls):
        DB.clear()
        DB.update(cls.original_db)

    def setUp(self):
        self.DB = DB
        self.DB.clear()
        self.now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        self.owner_user_data_simple = { "id": 1, "login": "owner_login" }
        self.reviewer_user_data_simple = { "id": 2, "login": "reviewer_login" }
        self.pr_author_user_data_simple = { "id": 3, "login": "pr_author_login" }
        
        # Use base64-like node_ids to match NODE_ID_PATTERN = r"^[A-Za-z0-9+/=]+$"
        self.full_owner_user_data = {
            "id": 1, "login": "owner_login", "node_id": "dXNlcl9ub2RlXzE=", "type": "User", "site_admin": False,
            "name": "Repo Owner", "email": "owner@example.com", "created_at": self.now_iso, "updated_at": self.now_iso,
        }
        self.full_reviewer_user_data = {
            "id": 2, "login": "reviewer_login", "node_id": "dXNlcl9ub2RlXzI=", "type": "User", "site_admin": False,
            "name": "Test Reviewer", "email": "reviewer@example.com", "created_at": self.now_iso, "updated_at": self.now_iso,
        }
        self.full_pr_author_user_data = {
            "id": 3, "login": "pr_author_login", "node_id": "dXNlcl9ub2RlXzM=", "type": "User", "site_admin": False,
             "name": "PR Author", "email": "pr_author@example.com", "created_at": self.now_iso, "updated_at": self.now_iso,
        }
        self.full_no_permission_user_data = {
            "id": 4, "login": "no_perm_user", "node_id": "dXNlcl9ub2RlXzQ=", "type": "User", "site_admin": False,
            "name": "No Permission User", "email": "noperm@example.com", "created_at": self.now_iso, "updated_at": self.now_iso,
        }
        self.full_read_permission_user_data = {
            "id": 5, "login": "read_perm_user", "node_id": "dXNlcl9ub2RlXzU=", "type": "User", "site_admin": False,
            "name": "Read Permission User", "email": "readperm@example.com", "created_at": self.now_iso, "updated_at": self.now_iso,
        }

        self.DB["Users"] = [
            copy.deepcopy(self.full_owner_user_data),
            copy.deepcopy(self.full_reviewer_user_data),
            copy.deepcopy(self.full_pr_author_user_data),
            copy.deepcopy(self.full_no_permission_user_data),
            copy.deepcopy(self.full_read_permission_user_data),
        ]

        self.repo_data = {
            "id": 101, "node_id": "cmVwb19ub2RlXzEwMQ==", "name": "test-repo", "full_name": "owner_login/test-repo",
            "private": False, "owner": {"id": self.owner_user_data_simple["id"], "login": self.owner_user_data_simple["login"]},
            "description": "Test repository", "fork": False, "created_at": self.now_iso, "updated_at": self.now_iso, "pushed_at": self.now_iso,
            "size": 100, "stargazers_count": 0, "watchers_count": 0, "language": "Python", "has_issues": True,
            "has_projects": True, "has_downloads": True, "has_wiki": True, "has_pages": False, "forks_count": 0,
            "archived": False, "disabled": False, "open_issues_count": 1, "license": None, "allow_forking": True,
            "is_template": False, "web_commit_signoff_required": False, "topics": [], "visibility": "public",
            "default_branch": "main", "forks": 0, "open_issues": 1, "watchers": 0,
            "html_url": "https://github.com/owner_login/test-repo",
        }
        self.DB["Repositories"] = [copy.deepcopy(self.repo_data)]

        self.commit_head_sha = "abcdef1234567890abcdef1234567890abcdef12"
        self.commit_base_sha = "fedcba0987654321fedcba0987654321fedcba09"
        self.commit_older_sha = "1234567890abcdef1234567890abcdef12345678"

        self.DB["Commits"] = [
            {
                "sha": self.commit_head_sha.lower(), "node_id": "Q19OT0RFX2FiY2RlZjEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkwYWJjZGVmMTI=", "repository_id": self.repo_data["id"],
                "commit": {"author": {"name": "test", "email": "test@example.com", "date": self.now_iso},
                           "committer": {"name": "test", "email": "test@example.com", "date": self.now_iso},
                           "message": "Head commit", "tree": {"sha": "tree_sha_head"}},
                "parents": [{"sha": self.commit_base_sha.lower()}], "author": None, "committer": None,
            },
            {
                "sha": self.commit_base_sha.lower(), "node_id": "Q19OT0RFX2ZlZGNiYTA5ODc2NTQzMjFmZWRjYmEwOTg3NjU0MzIxZmVkY2JhMDk=", "repository_id": self.repo_data["id"],
                "commit": {"author": {"name": "test", "email": "test@example.com", "date": self.now_iso},
                           "committer": {"name": "test", "email": "test@example.com", "date": self.now_iso},
                           "message": "Base commit", "tree": {"sha": "tree_sha_base"}},
                "parents": [], "author": None, "committer": None,
            },
            {
                "sha": self.commit_older_sha.lower(), "node_id": "Q19OT0RFXzEyMzQ1Njc4OTBhYmNkZWYxMjM0NTY3ODkwYWJjZGVmMTIzNDU2Nzg=", "repository_id": self.repo_data["id"],
                "commit": {"author": {"name": "test", "email": "test@example.com", "date": self.now_iso},
                           "committer": {"name": "test", "email": "test@example.com", "date": self.now_iso},
                           "message": "Older commit", "tree": {"sha": "tree_sha_older"}},
                "parents": [{"sha": self.commit_base_sha.lower()}], "author": None, "committer": None,
            }
        ]

        self.pr_data = {
            "id": 201, "node_id": "cHJfbm9kZV8yMDE=", "number": 1,
            "title": "Test PR", 
            "user": {"id": self.pr_author_user_data_simple["id"], "login": self.pr_author_user_data_simple["login"]},
            "labels": [], "state": "open", "locked": False, "assignee": None, "assignees": [], "milestone": None,
            "created_at": self.now_iso, "updated_at": self.now_iso, "closed_at": None, "merged_at": None,
            "body": "PR body", "author_association": "CONTRIBUTOR", "draft": False, "merged": False,
            "head": {"label": "pr_author_login:feature", "ref": "feature", "sha": self.commit_head_sha.lower(),
                     "user": {"id": self.pr_author_user_data_simple["id"], "login": self.pr_author_user_data_simple["login"]},
                     "repo": copy.deepcopy(self.repo_data)},
            "base": {"label": "owner_login:main", "ref": "main", "sha": self.commit_base_sha.lower(),
                     "user": {"id": self.owner_user_data_simple["id"], "login": self.owner_user_data_simple["login"]},
                     "repo": copy.deepcopy(self.repo_data)},
        }
        self.DB["PullRequests"] = [copy.deepcopy(self.pr_data)]
        self.DB["RepositoryCollaborators"] = [
            {"repository_id": self.repo_data["id"], "user_id": self.reviewer_user_data_simple["id"], "permission": "write"},
            {"repository_id": self.repo_data["id"], "user_id": self.owner_user_data_simple["id"], "permission": "admin"},
            {"repository_id": self.repo_data["id"], "user_id": self.full_read_permission_user_data["id"], "permission": "read"},
        ]

        self.DB["PullRequestReviews"] = []
        self.DB["PullRequestReviewComments"] = []
        self.DB["CurrentUser"] = copy.deepcopy(self.full_reviewer_user_data)

    def _set_current_user(self, user_dict_full):
        self.DB["CurrentUser"] = copy.deepcopy(user_dict_full)

    def _assert_review_response(self, response, expected_state, expected_body,
                                expected_commit_id, pr_id, reviewer_id, reviewer_login,
                                expected_author_association="COLLABORATOR", has_submitted_at=True):
        self.assertIsInstance(response, dict)
        self.assertIn("id", response)
        self.assertIsInstance(response["id"], int)
        self.assertTrue(response["id"] > 0)
        self.assertIn("node_id", response)
        self.assertIsInstance(response["node_id"], str)
        
        self.assertIn("pull_request_id", response)
        self.assertEqual(response["pull_request_id"], pr_id)

        self.assertEqual(response["state"], expected_state)
        
        self.assertIn("body", response) 
        self.assertEqual(response["body"], expected_body)

        self.assertEqual(response["commit_id"], expected_commit_id.lower())
        self.assertEqual(response["author_association"], expected_author_association)

        self.assertIn("user", response)
        self.assertEqual(response["user"]["id"], reviewer_id)
        self.assertEqual(response["user"]["login"], reviewer_login)
        self.assertEqual(set(response["user"].keys()), {"id", "login"})


        self.assertIn("submitted_at", response)
        if has_submitted_at:
            self.assertIsNotNone(response["submitted_at"])
            self.assertIsInstance(response["submitted_at"], str)
            datetime.fromisoformat(response["submitted_at"].replace("Z", "+00:00"))
        else:
            self.assertIsNone(response["submitted_at"])


        reviews_in_db = [r for r in self.DB["PullRequestReviews"] if r["id"] == response["id"]]
        self.assertEqual(len(reviews_in_db), 1)
        db_review = reviews_in_db[0]
        self.assertEqual(db_review["id"], response["id"])
        self.assertEqual(db_review["state"], expected_state)
        self.assertIn("body", db_review)
        self.assertEqual(db_review["body"], expected_body)
        self.assertEqual(db_review["commit_id"], expected_commit_id.lower())
        self.assertEqual(db_review["pull_request_id"], pr_id)
        self.assertEqual(db_review["user"]["id"], reviewer_id)
        self.assertEqual(set(db_review["user"].keys()), {"id", "login"})
        
        self.assertIn("submitted_at", db_review)
        if has_submitted_at:
            self.assertIsNotNone(db_review["submitted_at"])
            self.assertIsInstance(db_review["submitted_at"], str)
        else:
            self.assertIsNone(db_review["submitted_at"])

    def test_create_pending_review_minimal(self):
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1
        )
        self._assert_review_response(response, "PENDING", None, self.commit_head_sha,
                                     self.pr_data["id"], self.reviewer_user_data_simple["id"], self.reviewer_user_data_simple["login"],
                                     expected_author_association="COLLABORATOR", has_submitted_at=False)
        self.assertEqual(len(self.DB["PullRequestReviewComments"]), 0)

    def test_create_pending_review_with_body(self):
        review_body = "This is a pending review body."
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1, body=review_body
        )
        self._assert_review_response(response, "PENDING", review_body, self.commit_head_sha,
                                     self.pr_data["id"], self.reviewer_user_data_simple["id"], self.reviewer_user_data_simple["login"],
                                     expected_author_association="COLLABORATOR", has_submitted_at=False)

    def test_create_approve_review(self):
        review_body = "Looks good to me!"
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            body=review_body, event="APPROVE"
        )
        self._assert_review_response(response, "APPROVED", review_body, self.commit_head_sha,
                                     self.pr_data["id"], self.reviewer_user_data_simple["id"], self.reviewer_user_data_simple["login"],
                                     expected_author_association="COLLABORATOR")

    def test_create_request_changes_review(self):
        review_body = "Please address these points."
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            body=review_body, event="REQUEST_CHANGES"
        )
        self._assert_review_response(response, "CHANGES_REQUESTED", review_body, self.commit_head_sha,
                                     self.pr_data["id"], self.reviewer_user_data_simple["id"], self.reviewer_user_data_simple["login"],
                                     expected_author_association="COLLABORATOR")

    def test_create_comment_review(self):
        review_body = "Just a general comment."
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            body=review_body, event="COMMENT"
        )
        self._assert_review_response(response, "COMMENTED", review_body, self.commit_head_sha,
                                     self.pr_data["id"], self.reviewer_user_data_simple["id"], self.reviewer_user_data_simple["login"],
                                     expected_author_association="COLLABORATOR")

    def test_create_review_with_specific_commit_id(self):
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            commit_id=self.commit_older_sha, event="APPROVE"
        )
        self._assert_review_response(response, "APPROVED", None, self.commit_older_sha,
                                     self.pr_data["id"], self.reviewer_user_data_simple["id"], self.reviewer_user_data_simple["login"],
                                     expected_author_association="COLLABORATOR")

    def test_create_review_with_single_comment_using_position(self):
        comment_data = [{"path": "file1.py", "body": "Comment on line via position.", "position": 5}]
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review with one comment.", comments=comment_data
        )
        self._assert_review_response(response, "COMMENTED", "Review with one comment.", self.commit_head_sha,
                                     self.pr_data["id"], self.reviewer_user_data_simple["id"], self.reviewer_user_data_simple["login"],
                                     expected_author_association="COLLABORATOR")

        comments_in_db = self.DB["PullRequestReviewComments"]
        self.assertEqual(len(comments_in_db), 1)
        db_comment = comments_in_db[0] 
        self.assertEqual(db_comment["path"], comment_data[0]["path"])
        self.assertEqual(db_comment["body"], comment_data[0]["body"])
        self.assertEqual(db_comment["position"], comment_data[0]["position"])
        self.assertEqual(db_comment["pull_request_review_id"], response["id"])
        self.assertEqual(db_comment["pull_request_id"], self.pr_data["id"])
        self.assertEqual(db_comment["commit_id"], self.commit_head_sha.lower())
        self.assertEqual(db_comment["user"]["id"], self.reviewer_user_data_simple["id"])
        self.assertEqual(set(db_comment["user"].keys()), {"id", "login"})
        self.assertIn("created_at", db_comment)
        self.assertIsInstance(db_comment["created_at"], str) 
        datetime.fromisoformat(db_comment["created_at"].replace("Z", "+00:00"))
        self.assertIn("updated_at", db_comment)
        self.assertIsInstance(db_comment["updated_at"], str)
        datetime.fromisoformat(db_comment["updated_at"].replace("Z", "+00:00"))

    def test_create_review_with_multiline_comment(self):
        comment_data = [{"path": "file3.md", "body": "Multi-line comment.",
                         "line": 15, "start_line": 12, "side": "RIGHT", "start_side": "LEFT"}]
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review with multi-line comment.", comments=comment_data
        )
        self._assert_review_response(response, "COMMENTED", "Review with multi-line comment.", self.commit_head_sha,
                                     self.pr_data["id"], self.reviewer_user_data_simple["id"], self.reviewer_user_data_simple["login"],
                                     expected_author_association="COLLABORATOR")
        comments_in_db = self.DB["PullRequestReviewComments"]
        self.assertEqual(len(comments_in_db), 1)
        db_comment = comments_in_db[0] 
        self.assertEqual(db_comment["line"], comment_data[0]["line"])
        self.assertEqual(db_comment["start_line"], comment_data[0]["start_line"])
        self.assertEqual(db_comment["side"], comment_data[0]["side"])
        self.assertEqual(db_comment["start_side"], comment_data[0]["start_side"])
        self.assertIn("created_at", db_comment)
        self.assertIsInstance(db_comment["created_at"], str) 
        datetime.fromisoformat(db_comment["created_at"].replace("Z", "+00:00"))

    # --- BEGIN: diff_hunk coverage tests (integration with create_pull_request_review) ---

    def test_start_line_and_end_line_present(self):
        # Must provide 'line' as well for validation to pass, and 'end_line' is ignored by model, only 'start_line' and 'line' used
        comment = {"path": "file.py", "body": "test", "start_line": 10, "end_line": 15, "line": 12}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        # The model uses start_line and line, not end_line, so diff_hunk reflects 10-12
        self.assertEqual(db_comment["diff_hunk"], "@@ -10,... +15,... @@ file.py (lines 10-15)")

    def test_only_start_line_and_end_line_present(self):
        # Must provide 'line' as well for validation to pass, end_line is ignored
        comment = {"path": "file.py", "body": "test", "start_line": 5, "end_line": 8, "line": 8}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        self.assertEqual(db_comment["diff_hunk"], "@@ -5,... +8,... @@ file.py (lines 5-8)")

    def test_start_line_and_line_present_no_end_line(self):
        # Must provide 'line' and 'start_line', no 'end_line'
        comment = {"path": "file.py", "body": "test", "start_line": 20, "line": 25}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        self.assertEqual(db_comment["diff_hunk"], "@@ -20,... +25,... @@ file.py (lines 20-25)")

    def test_only_start_line_and_line_present(self):
        comment = {"path": "file.py", "body": "test", "start_line": 7, "line": 9}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        self.assertEqual(db_comment["diff_hunk"], "@@ -7,... +9,... @@ file.py (lines 7-9)")

    def test_line_present_no_start_or_end_line(self):
        comment = {"path": "file.py", "body": "test", "line": 30}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        self.assertEqual(db_comment["diff_hunk"], "@@ -30,1 +30,1 @@ file.py (line 30)")

    def test_only_line_present(self):
        comment = {"path": "file.py", "body": "test", "line": 42}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        self.assertEqual(db_comment["diff_hunk"], "@@ -42,1 +42,1 @@ file.py (line 42)")

    def test_position_present_no_line_start_or_end(self):
        comment = {"path": "file.py", "body": "test", "position": 5}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        self.assertEqual(db_comment["diff_hunk"], "@@ ... +... @@ file.py (position 5)")

    def test_no_line_or_position_info_empty_comment(self):
        comment = {"path": "file.py", "body": "test"}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    def test_no_line_or_position_info_with_other_keys(self):
        comment = {"path": "file.py", "body": "A comment"}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    def test_all_relevant_fields_are_none(self):
        comment = {"path": "file.py", "body": "test", "start_line": None, "end_line": None, "line": None, "position": None}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    # --- Fall-through logic tests ---

    def test_only_start_line_present_fallback_to_position(self):
        # start_line present but no line, should raise ValidationError
        comment = {"path": "file.py", "body": "test", "start_line": 55, "position": 6}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    def test_only_start_line_present_fallback_to_no_info(self):
        # start_line present but no line or position, should raise ValidationError
        comment = {"path": "file.py", "body": "test", "start_line": 50}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    def test_only_end_line_present_fallback_to_line(self):
        # end_line present, line present, should use line
        comment = {"path": "file.py", "body": "test", "end_line": 70, "line": 75}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        self.assertEqual(db_comment["diff_hunk"], "@@ -75,1 +75,1 @@ file.py (line 75)")

    def test_only_end_line_present_fallback_to_position(self):
        # end_line present, position present, but no line, should use position
        comment = {"path": "file.py", "body": "test", "end_line": 65, "position": 7}
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="Review", comments=[comment]
        )
        db_comment = self.DB["PullRequestReviewComments"][-1]
        self.assertEqual(db_comment["diff_hunk"], "@@ ... +... @@ file.py (position 7)")

    def test_only_end_line_present_fallback_to_no_info(self):
        # end_line present, but no line or position, should raise ValidationError
        comment = {"path": "file.py", "body": "test", "end_line": 60}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    # --- Tests with zero values ---

    def test_zero_values_for_start_and_end_line(self):
        # line, start_line, and end_line must be >= 1, so this should raise ValidationError
        comment = {"path": "file.py", "body": "test", "start_line": 0, "end_line": 0, "line": 0}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    def test_zero_value_for_line(self):
        # line must be >= 1, so this should raise ValidationError
        comment = {"path": "file.py", "body": "test", "line": 0}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    def test_zero_value_for_position(self):
        # position must be >= 1, so this should raise ValidationError
        comment = {"path": "file.py", "body": "test", "position": 0}
        with self.assertRaises(ValidationError):
            create_pull_request_review(
                owner="owner_login", repo="test-repo", pull_number=1,
                event="COMMENT", body="Review", comments=[comment]
            )

    # --- END: diff_hunk coverage tests ---

    def test_author_association_owner(self):
        self._set_current_user(self.full_owner_user_data)
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1, event="APPROVE"
        )
        self._assert_review_response(response, "APPROVED", None, self.commit_head_sha,
                                     self.pr_data["id"], self.owner_user_data_simple["id"], self.owner_user_data_simple["login"],
                                     expected_author_association="OWNER")

    def test_author_association_pr_author_as_reviewer_not_collaborator(self):
        self._set_current_user(self.full_pr_author_user_data)
        self.DB["RepositoryCollaborators"] = [
            c for c in self.DB["RepositoryCollaborators"] if c["user_id"] != self.pr_author_user_data_simple["id"]
        ]
        response = create_pull_request_review(
            owner="owner_login", repo="test-repo", pull_number=1, event="APPROVE"
        )
        self._assert_review_response(response, "APPROVED", None, self.commit_head_sha,
                                     self.pr_data["id"], self.pr_author_user_data_simple["id"], self.pr_author_user_data_simple["login"],
                                     expected_author_association="CONTRIBUTOR")
    def test_author_association_none_gets_forbidden(self):
        self._set_current_user(self.full_no_permission_user_data)
        self.DB["RepositoryCollaborators"] = [
            c for c in self.DB["RepositoryCollaborators"] if c["user_id"] != self.full_no_permission_user_data["id"]
        ]
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ForbiddenError,
            expected_message="User no_perm_user does not have sufficient permissions to review pull request #1 in owner_login/test-repo.",
            owner="owner_login", repo="test-repo", pull_number=1, event="APPROVE"
        )

    def test_invalid_event_type(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Invalid event type: 'INVALID_EVENT'. Must be one of: APPROVE, REQUEST_CHANGES, COMMENT.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="INVALID_EVENT", body="A body"
        )

    def test_request_changes_missing_body(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Body is required when event is 'REQUEST_CHANGES'.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="REQUEST_CHANGES"
        )
    
    def test_comment_event_missing_body(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Body is required when event is 'COMMENT'.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT"
        )

    def test_invalid_comment_structure_missing_path(self):
        comments = [{"body": "test", "position": 1}]
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Invalid structure for comment at index 0: path: Field required",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="body", comments=comments
        )

    def test_invalid_comment_structure_missing_body(self):
        comments = [{"path": "file.py", "position": 1}]
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Invalid structure for comment at index 0: body: Field required",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="body", comments=comments
        )

    def test_invalid_comment_structure_missing_position_and_line(self):
        comments = [{"path": "file.py", "body": "test"}]
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Invalid structure for comment at index 0: General: Value error, Either 'position' or 'line' must be provided for a comment.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="body", comments=comments
        )

    def test_invalid_comment_structure_start_line_without_line(self):
        comments = [{"path": "file.py", "body": "test", "start_line": 1, "position": 1}]
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Invalid structure for comment at index 0: General: Value error, 'line' must be provided when 'start_line' is present.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="body", comments=comments
        )

    def test_invalid_comment_structure_start_line_greater_than_line(self):
        comments = [{"path": "file.py", "body": "test", "line": 1, "start_line": 5}]
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Invalid structure for comment at index 0: General: Value error, 'start_line' must be less than or equal to 'line'.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="body", comments=comments
        )

    def test_invalid_commit_id_format_too_short(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Invalid commit_id SHA format: 'invalid-sha'. Must be 40 hex characters.",
            owner="owner_login", repo="test-repo", pull_number=1,
            commit_id="invalid-sha"
        )

    def test_invalid_commit_id_format_not_hex(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Invalid commit_id SHA format: 'gggggggggggggggggggggggggggggggggggggggg'. Must be 40 hex characters.",
            owner="owner_login", repo="test-repo", pull_number=1,
            commit_id="g" * 40
        )

    def test_repo_not_found_bad_owner(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=NotFoundError,
            expected_message="Repository 'nonexistent_owner/test-repo' not found.",
            owner="nonexistent_owner", repo="test-repo", pull_number=1
        )
    
    def test_repo_not_found_bad_repo_name(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=NotFoundError,
            expected_message="Repository 'owner_login/nonexistent-repo' not found.",
            owner="owner_login", repo="nonexistent-repo", pull_number=1
        )

    def test_pull_request_not_found(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=NotFoundError,
            expected_message="Pull request #999 not found in 'owner_login/test-repo'.",
            owner="owner_login", repo="test-repo", pull_number=999
        )

    def test_commit_id_not_found_in_repo(self):
        non_existent_sha = "0000000000000000000000000000000000000000"
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=UnprocessableEntityError,
            expected_message=f"Commit SHA '{non_existent_sha}' not found in repository 'owner_login/test-repo'.",
            owner="owner_login", repo="test-repo", pull_number=1,
            commit_id=non_existent_sha, event="APPROVE"
        )

    def test_forbidden_no_write_permission_user_with_read_only(self):
        self._set_current_user(self.full_read_permission_user_data)
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ForbiddenError,
            expected_message="User read_perm_user does not have sufficient permissions to review pull request #1 in owner_login/test-repo.",
            owner="owner_login", repo="test-repo", pull_number=1, event="APPROVE"
        )

    def test_review_on_locked_pr(self):
        self.DB["PullRequests"][0]["locked"] = True
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=UnprocessableEntityError,
            expected_message="Pull request #1 is locked.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="APPROVE", body="Trying to review locked PR"
        )
        self.DB["PullRequests"][0]["locked"] = False

    def test_invalid_owner_type(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Owner must be a string.",
            owner=123, # Invalid type for owner
            repo="test-repo",
            pull_number=1
        )

    def test_invalid_repo_type(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Repo must be a string.",
            owner="owner_login", 
            repo=123, # Invalid type for repo
            pull_number=1
        )

    def test_invalid_pull_number_type(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Pull number must be an integer.",
            owner="owner_login",
            repo="test-repo",
            pull_number="1" # Invalid type for pull_number (string)
        )
        
    def test_pull_number_non_positive_zero(self):
                self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=NotFoundError,
            expected_message="Pull request #0 not found (must be positive).",
            owner="owner_login", repo="test-repo", pull_number=0
        )

    def test_pull_number_non_positive_negative(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=NotFoundError,
            expected_message="Pull request #-1 not found (must be positive).",
            owner="owner_login", repo="test-repo", pull_number=-1
        )
    
    def test_comments_not_a_list(self):
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="'comments' must be a list of comment objects.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="body", comments="not a list"
        )

    def test_comment_in_list_not_a_dict(self):
        comments = ["not a dict"]
        self.assert_error_behavior(
            func_to_call=create_pull_request_review,
            expected_exception_type=ValidationError,
            expected_message="Comment at index 0 must be a dictionary.",
            owner="owner_login", repo="test-repo", pull_number=1,
            event="COMMENT", body="body", comments=comments
        )

class TestListPullRequests(BaseTestCaseWithErrorHandler):

    @classmethod
    def setUpClass(cls):
        cls.original_db = copy.deepcopy(DB)

    @classmethod
    def tearDownClass(cls):
        DB.clear()
        DB.update(cls.original_db)

    def setUp(self):
        self.DB = DB
        self.DB.clear()
        self.now = datetime.now(timezone.utc)

        # Users
        self.user1 = self._create_db_user(id=1, login='user1', type='User')
        self.user2 = self._create_db_user(id=2, login='user2', type='User')
        self.org1 = self._create_db_user(id=3, login='org1', type='Organization')
        self.DB['Users'] = [self.user1, self.user2, self.org1]

        # Repositories
        self.repo1_user1 = self._create_db_repo(id=101, name='repo1', owner_login='user1', full_name='user1/repo1', default_branch='main')
        self.repo2_org1 = self._create_db_repo(id=102, name='repo2', owner_login='org1', full_name='org1/repo2', default_branch='master')
        self.repo1_fork_user2 = self._create_db_repo(id=103, name='repo1', owner_login='user2', full_name='user2/repo1', fork=True, default_branch='main')
        self.DB['Repositories'] = [self.repo1_user1, self.repo2_org1, self.repo1_fork_user2]
        
        # Initialize DB keys that will be populated by helpers or tests
        self.DB['PullRequests'] = []
        self.DB['Labels'] = []
        self.DB['Milestones'] = []

        # Labels
        self.label_bug = self._create_db_label(id=1, name='bug', color='d73a4a', description='Something isn\'t working')
        self.label_enhancement = self._create_db_label(id=2, name='enhancement', color='a2eeef', description='New feature or request')
        self.DB['Labels'] = [self.label_bug, self.label_enhancement]

        # Milestone
        self.milestone_v1 = self._create_db_milestone(
            id=1, number=1, title='v1.0', state='open',
            open_issues=2, closed_issues=1,
            created_at=self._iso_timestamp(self.now - timedelta(days=30)),
            updated_at=self._iso_timestamp(self.now - timedelta(days=2)),
            repo_id=self.repo1_user1['id'] # Important: Link milestone to a repository
        )
        self.DB['Milestones'] = [self.milestone_v1]

        # Pull Requests for user1/repo1
        self.pr1 = self._create_db_pr(id=1, number=1, title='Feat: Cool new feature', repo_full_name='user1/repo1', head_repo_full_name='user1/repo1', head_branch='feature1', base_branch='main', user_login='user1', state='open', created_at=self._iso_timestamp(self.now - timedelta(days=5)), updated_at=self._iso_timestamp(self.now - timedelta(days=1)), comments=5, labels=[self.label_enhancement], milestone_id=self.milestone_v1['id'])
        self.pr2 = self._create_db_pr(id=2, number=2, title='Fix: Critical bug', repo_full_name='user1/repo1', head_repo_full_name='user1/repo1', head_branch='fix1', base_branch='main', user_login='user2', state='closed', merged=True, created_at=self._iso_timestamp(self.now - timedelta(days=10)), updated_at=self._iso_timestamp(self.now - timedelta(days=8)), closed_at=self._iso_timestamp(self.now - timedelta(days=8)), merged_at=self._iso_timestamp(self.now - timedelta(days=8)), comments=2, labels=[self.label_bug], merged_by_login='user1')
        self.pr3 = self._create_db_pr(id=3, number=3, title='Refactor: Legacy code', repo_full_name='user1/repo1', head_repo_full_name='user2/repo1', head_branch='feature_from_fork', base_branch='main', user_login='user2', state='open', created_at=self._iso_timestamp(self.now - timedelta(days=40)), updated_at=self._iso_timestamp(self.now - timedelta(days=2)), comments=10, assignees_logins=['user1'])
        self.pr4 = self._create_db_pr(id=4, number=4, title='Docs: Update README', repo_full_name='user1/repo1', head_repo_full_name='user1/repo1', head_branch='docs_update', base_branch='develop', user_login='user1', state='open', created_at=self._iso_timestamp(self.now - timedelta(days=2)), updated_at=self._iso_timestamp(self.now - timedelta(days=2)), comments=0)
        self.pr5 = self._create_db_pr(id=5, number=5, title='Old Feature', repo_full_name='user1/repo1', head_repo_full_name='user1/repo1', head_branch='old_feature', base_branch='main', user_login='user1', state='open', created_at=self._iso_timestamp(self.now - timedelta(days=60)), updated_at=self._iso_timestamp(self.now - timedelta(days=35)), comments=1)
        self.pr6 = self._create_db_pr(id=6, number=6, title='Wontfix: Minor issue', repo_full_name='user1/repo1', head_repo_full_name='user1/repo1', head_branch='minor_issue_branch', base_branch='main', user_login='user2', state='closed', merged=False, created_at=self._iso_timestamp(self.now - timedelta(days=20)), updated_at=self._iso_timestamp(self.now - timedelta(days=18)), closed_at=self._iso_timestamp(self.now - timedelta(days=18)), comments=3)
        self.DB['PullRequests'] = [self.pr1, self.pr2, self.pr3, self.pr4, self.pr5, self.pr6]

    def _iso_timestamp(self, dt_obj: datetime) -> str:
        return dt_obj.isoformat().replace('+00:00', 'Z')

    def _get_user_by_login(self, login: str) -> Dict[str, Any]:
        # Ensure users are available, especially if helpers are called before full setUp in some contexts
        users_to_search = self.DB.get('Users', [])
        if not users_to_search and hasattr(self, 'user1') and hasattr(self, 'user2') and hasattr(self, 'org1'):
             users_to_search = [self.user1, self.user2, self.org1] # Fallback to initially defined users

        for user in users_to_search:
            if user['login'] == login:
                # Use a node_id that matches the pattern: only A-Za-z0-9+/=
                return {
                    'login': user['login'], 'id': user['id'], 
                    'node_id': f"TWFuVXNlcj{user['id']}=", # "ManUser{id}=" in base64-like, matches pattern
                    'type': user.get('type', 'User'), 
                    'site_admin': user.get('site_admin', False)
                }
        raise ValueError(f"User '{login}' not found in DB setup. Available users: {[u['login'] for u in users_to_search]}")

    def _get_repo_by_full_name(self, full_name: str) -> Dict[str, Any]:
        repos_to_search = self.DB.get('Repositories', [])
        if not repos_to_search and hasattr(self, 'repo1_user1'): # Fallback
            repos_to_search = [self.repo1_user1, self.repo2_org1, self.repo1_fork_user2]

        for repo_data_in_db in repos_to_search:
            if repo_data_in_db.get('full_name') == full_name: # Safe access with .get()
                # Ensure owner login exists in the simplified repo owner data
                owner_login_from_repo = repo_data_in_db.get('owner', {}).get('login')
                if not owner_login_from_repo:
                    raise ValueError(f"Repo '{full_name}' has malformed owner data in DB.")
                owner_user_obj = self._get_user_by_login(owner_login_from_repo)
                
                # Construct a full repo object similar to what the API might return
                return {
                    'id': repo_data_in_db['id'], 
                    'node_id': f"UkVQT19OT0RFX0lE_{repo_data_in_db['id']}==", # matches pattern
                    'name': repo_data_in_db['name'], 
                    'full_name': repo_data_in_db['full_name'], 
                    'private': repo_data_in_db.get('private', False),
                    'owner': owner_user_obj, # Use the full user object for owner
                    'description': repo_data_in_db.get('description'), 
                    'fork': repo_data_in_db.get('fork', False),
                    'created_at': repo_data_in_db.get('created_at', self._iso_timestamp(self.now)),
                    'updated_at': repo_data_in_db.get('updated_at', self._iso_timestamp(self.now)),
                    'pushed_at': repo_data_in_db.get('pushed_at', self._iso_timestamp(self.now)),
                    'language': repo_data_in_db.get('language'), 
                    'stargazers_count': repo_data_in_db.get('stargazers_count', 0),
                    'watchers_count': repo_data_in_db.get('watchers_count', 0), 
                    'forks_count': repo_data_in_db.get('forks_count', 0),
                    'open_issues_count': repo_data_in_db.get('open_issues_count', 0),
                    'visibility': repo_data_in_db.get('visibility', 'public'),
                    'default_branch': repo_data_in_db.get('default_branch', 'main')
                }
        raise ValueError(f"Repo '{full_name}' not found in DB setup. Available repos: {[r.get('full_name') for r in repos_to_search]}")

    def _create_db_user(self, id: int, login: str, **kwargs: Any) -> Dict[str, Any]:
        user_data: Dict[str, Any] = {
            'id': id, 'login': login, 'node_id': f"TWFuVXNlcj{id}=", # matches pattern
            'type': 'User', 'site_admin': False
        }
        user_data.update(kwargs)
        return user_data

    def _create_db_repo(self, id: int, name: str, owner_login: str, full_name: str, **kwargs: Any) -> Dict[str, Any]:
        # This helper assumes self.user1, self.user2, self.org1 are already defined if it's called during setUp
        owner_obj = self._get_user_by_login(owner_login) # Leverages existing user objects
        
        repo_data: Dict[str, Any] = {
            'id': id, 'node_id': f"UkVQT19OT0RFX0lE_{id}==", # matches pattern
            'name': name, 'full_name': full_name,
            'private': False, 
            'owner': {'id': owner_obj['id'], 'login': owner_obj['login']}, # Simplified owner for DB storage
            'description': 'A test repository', 'fork': False,
            'created_at': self._iso_timestamp(self.now - timedelta(days=365)),
            'updated_at': self._iso_timestamp(self.now - timedelta(days=10)),
            'pushed_at': self._iso_timestamp(self.now - timedelta(days=5)),
            'size': 1024, 'stargazers_count': 10, 'watchers_count': 5, 'language': 'Python',
            'has_issues': True, 'has_projects': True, 'has_downloads': True, 'has_wiki': True, 'has_pages': False,
            'forks_count': 2, 'archived': False, 'disabled': False, 'open_issues_count': 3,
            'default_branch': 'main', 'visibility': 'public',
        }
        repo_data.update(kwargs)
        return repo_data

    def _create_db_label(self, id: int, name: str, **kwargs: Any) -> Dict[str, Any]:
        label_data: Dict[str, Any] = {
            'id': id, 'node_id': f"TEFCRUxfTk9ERV9JRF8{id}=", # matches pattern
            'name': name, 'color': 'ffffff',
            'description': '', 'default': False,
        }
        label_data.update(kwargs)
        return label_data

    def _create_db_milestone(self, id: int, number: int, title: str, repo_id: int, **kwargs: Any) -> Dict[str, Any]:
        # Pop 'creator_login' to avoid passing it in **kwargs to update if it's not a direct field of the milestone
        creator_login_val = kwargs.pop('creator_login', 'user1')
        creator_user_obj = self._get_user_by_login(creator_login_val)
        
        milestone_data: Dict[str, Any] = {
            'id': id, 'node_id': f"TUlMRVNUT05FX05PREVfSUQ_{id}=", # matches pattern
            'number': number, 'title': title,
            'repository_id': repo_id, # For internal linking, not directly in output PR.milestone object graph
            'description': f'Milestone {title}',
            'creator': {'login': creator_user_obj['login'], 'id': creator_user_obj['id']}, # Simplified for DB storage
            'open_issues': kwargs.get('open_issues', 0), # Allow override via kwargs
            'closed_issues': kwargs.get('closed_issues', 0),
            'state': kwargs.get('state', 'open'),
            'created_at': kwargs.get('created_at', self._iso_timestamp(self.now - timedelta(days=10))),
            'updated_at': kwargs.get('updated_at', self._iso_timestamp(self.now - timedelta(days=1))),
            'closed_at': kwargs.get('closed_at', None),
            'due_on': kwargs.get('due_on', None),
        }
        # Apply remaining kwargs, allowing specific overrides for fields like open_issues, state, etc.
        milestone_data.update(kwargs) 
        return milestone_data

    def _create_db_pr(self, id: int, number: int, title: str,
                      repo_full_name: str, head_repo_full_name: str, head_branch: str, base_branch: str,
                      user_login: str, state: str,
                      created_at: str, updated_at: str, **kwargs: Any) -> Dict[str, Any]:

        pr_user_obj = self._get_user_by_login(user_login)
        head_repo_full_obj = self._get_repo_by_full_name(head_repo_full_name) # This will be the full repo dict
        base_repo_full_obj = self._get_repo_by_full_name(repo_full_name)   # This will be the full repo dict

        # The head.user and base.user in PR output are owners of the respective repos
        head_owner_full_obj = head_repo_full_obj['owner'] 
        base_owner_full_obj = base_repo_full_obj['owner']

        # Handle labels by extracting from kwargs and formatting
        labels_input_list = kwargs.pop('labels', None)
        labels_data_list = []
        if labels_input_list:
            labels_data_list = [
                {
                    'id': lbl['id'], 'node_id': lbl['node_id'], 'name': lbl['name'],
                    'color': lbl['color'], 'description': lbl['description'], 'default': lbl['default']
                } for lbl in labels_input_list
            ]

        # Handle milestone by extracting ID from kwargs and fetching/formatting
        milestone_id_val = kwargs.pop('milestone_id', None)
        milestone_data_obj = None
        if milestone_id_val:
            db_milestone_item = next((m for m in self.DB.get('Milestones', []) if m['id'] == milestone_id_val), None)
            if db_milestone_item:
                milestone_creator_login_val = db_milestone_item.get('creator', {}).get('login')
                milestone_creator_full_obj = self._get_user_by_login(milestone_creator_login_val) if milestone_creator_login_val else None
                
                milestone_data_obj = {
                    'id': db_milestone_item['id'], 'node_id': db_milestone_item['node_id'], 
                    'number': db_milestone_item['number'], 'title': db_milestone_item['title'], 
                    'description': db_milestone_item.get('description'),
                    'creator': milestone_creator_full_obj, # Use the full user object
                    'open_issues': db_milestone_item['open_issues'], 
                    'closed_issues': db_milestone_item['closed_issues'],
                    'state': db_milestone_item['state'], 'created_at': db_milestone_item['created_at'],
                    'updated_at': db_milestone_item['updated_at'], 
                    'closed_at': db_milestone_item.get('closed_at'),
                    'due_on': db_milestone_item.get('due_on')
                }

        # Handle assignees
        assignees_logins_list = kwargs.pop('assignees_logins', None)
        primary_assignee_obj = None
        assignees_data_obj_list = []
        if assignees_logins_list:
            for alogin in assignees_logins_list:
                assignees_data_obj_list.append(self._get_user_by_login(alogin))
            if assignees_data_obj_list:
                primary_assignee_obj = assignees_data_obj_list[0] # First assignee is the primary one

        # Handle merged_by
        merged_by_login_val = kwargs.pop('merged_by_login', None)
        merged_by_data_full_obj = self._get_user_by_login(merged_by_login_val) if merged_by_login_val else None

        # Define the base PR structure with defaults
        pr_data_dict: Dict[str, Any] = {
            'id': id, 
            'node_id': f"UFJfTk9ERV9JRF8{id}==", # matches pattern
            'number': number, 
            'title': title,
            'user': pr_user_obj, # User who created the PR
            'labels': labels_data_list,
            'state': state, 'locked': False,
            'assignee': primary_assignee_obj, # Single assignee object
            'assignees': assignees_data_obj_list, # List of assignee objects
            'milestone': milestone_data_obj,
            'created_at': created_at, 'updated_at': updated_at,
            'closed_at': None, 'merged_at': None, # Defaults, can be overridden by kwargs
            'body': f'Body for PR {title}',
            'author_association': 'MEMBER', # Default association
            'draft': False, 'merged': False, 'mergeable': True, 'rebaseable': True,
            'mergeable_state': 'clean',
            'merged_by': merged_by_data_full_obj,
            'comments': 0, 'review_comments': 0, 'commits': 1,
            'additions': 10, 'deletions': 2, 'changed_files': 1,
            'head': { # Head of the PR (source branch)
                'label': f"{head_repo_full_obj['owner']['login']}:{head_branch}",
                'ref': head_branch, 'sha': f"head_sha_{id}",
                'user': head_owner_full_obj, # Owner of the head repo
                'repo': head_repo_full_obj  # Full head repository object
            },
            'base': { # Base of the PR (target branch)
                'label': f"{base_repo_full_obj['owner']['login']}:{base_branch}",
                'ref': base_branch, 'sha': f"base_sha_{id}",
                'user': base_owner_full_obj, # Owner of the base repo
                'repo': base_repo_full_obj   # Full base repository object
            }
        }
        # Apply any remaining kwargs to override defaults or add extra fields
        pr_data_dict.update(kwargs)
        return pr_data_dict
    def assert_pr_ids_in_response(self, response: Union[List[Dict[str, Any]], Dict[str, Any]], expected_ids: List[int]):
        # Handle both old list format and new dict format
        if isinstance(response, dict):
            prs = response["pull_requests"]
        else:
            prs = response
        response_ids = [pr['id'] for pr in prs]
        self.assertEqual(response_ids, expected_ids, f"Expected PR IDs {expected_ids}, got {response_ids}")

    # --- Owner/Repo Validation Tests ---
    def test_validate_owner_missing(self):
        self.assert_error_behavior(list_pull_requests, expected_exception_type=ValidationError, expected_message="Owner must be a string.", owner=None, repo='repo1') # type: ignore

    def test_validate_owner_empty_string(self):
        self.assert_error_behavior(list_pull_requests, expected_exception_type=ValidationError, expected_message="Owner cannot be empty.", owner="", repo='repo1')

    def test_validate_owner_not_string(self):
        self.assert_error_behavior(list_pull_requests, expected_exception_type=ValidationError, expected_message="Owner must be a string.", owner=123, repo='repo1') # type: ignore

    def test_validate_repo_missing(self):
        self.assert_error_behavior(list_pull_requests, expected_exception_type=ValidationError, expected_message="Repo must be a string.", owner='user1', repo=None) # type: ignore

    def test_validate_repo_empty_string(self):
        self.assert_error_behavior(list_pull_requests, expected_exception_type=ValidationError, expected_message="Repo cannot be empty.", owner='user1', repo="")

    def test_validate_repo_not_string(self):
        self.assert_error_behavior(list_pull_requests, expected_exception_type=ValidationError, expected_message="Repo must be a string.", owner='user1', repo=456) # type: ignore
        
    # --- Parameter Type and Value Validation Tests ---
    def test_validate_state_invalid_type(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="State must be a string.",owner='user1', repo='repo1', state=123) # type: ignore

    def test_validate_sort_invalid_type(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="Sort must be a string.",owner='user1', repo='repo1', sort=123) # type: ignore

    def test_validate_direction_invalid_type(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="Direction must be a string if provided and not None.",owner='user1', repo='repo1', direction=123) # type: ignore

    def test_validate_per_page_invalid_type(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="Per_page must be an integer.",owner='user1', repo='repo1', per_page="30") # type: ignore

    def test_validate_page_invalid_type(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="Page must be an integer.",owner='user1', repo='repo1', page="1") # type: ignore

    def test_optional_params_as_none(self):
        # Test call with optional string/int parameters explicitly set to None where allowed by type hints
        # `state`, `sort`, `per_page`, `page` have defaults and are not Optional[str/int] in the signature itself,
        # so they cannot be None unless the signature is changed. `direction` is Optional[str].
        prs = list_pull_requests(
            owner='user1', 
            repo='repo1',
            state='open', # Non-optional default used
            sort='created', # Non-optional default used
            direction=None, # Optional, testing None
            per_page=30,  # Non-optional default used
            page=1        # Non-optional default used
        )
        # Expected open PRs for user1/repo1: pr1, pr3, pr4, pr5
        # Sort 'created', direction 'desc' (because direction=None and sort='created'): pr4, pr1, pr3, pr5
        self.assert_pr_ids_in_response(prs, [self.pr4['id'], self.pr1['id'], self.pr3['id'], self.pr5['id']])

    # --- Basic Functionality Tests ---
    def test_list_open_prs_default_params(self):
        # Default: state='open', sort='created', direction='desc'
        prs = list_pull_requests(owner='user1', repo='repo1')
        self.assert_pr_ids_in_response(prs, [self.pr4['id'], self.pr1['id'], self.pr3['id'], self.pr5['id']])
        for pr in prs:
            self.assertEqual(pr['state'], 'open')

    def test_list_no_prs_found_for_repo(self):
        # This repo (org1/repo2) has no PRs by default in setUp
        prs = list_pull_requests(owner='org1', repo='repo2')
        self.assertIsInstance(prs, list)
        self.assertEqual(prs, [])

    def test_for_loop_skipped_if_no_prs_in_db_table(self): # Test DB.get("PullRequests") returning None
        original_pull_requests = self.DB.pop('PullRequests', None) # Remove the table/key
        prs = list_pull_requests(owner='user1', repo='repo1') # Repo user1/repo1 exists
        self.assertIsInstance(prs, list)
        self.assertEqual(prs, [])
        if original_pull_requests is not None:
            self.DB['PullRequests'] = original_pull_requests # Restore

    def test_for_loop_skipped_if_prs_db_table_is_empty_list(self): # Test DB.get("PullRequests") returning []
        self.DB['PullRequests'] = [] # Ensure it's an empty list
        prs = list_pull_requests(owner='user1', repo='repo1')
        self.assertIsInstance(prs, list)
        self.assertEqual(prs, [])
        
    def test_repo_not_found_when_db_repositories_table_missing(self): # Test DB.get("Repositories") returning None
        original_repositories = self.DB.pop('Repositories', None) # Remove the table/key
        self.assert_error_behavior(
            list_pull_requests,
            expected_exception_type=NotFoundError,
            expected_message="Repository 'user1/repo1' not found.",
            owner='user1', repo='repo1'
        )
        if original_repositories is not None:
            self.DB['Repositories'] = original_repositories # Restore

    def test_repo_not_found(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=NotFoundError,expected_message="Repository 'nonexistent/repo' not found.",owner='nonexistent', repo='repo')
    
    def test_repo_not_found_when_repositories_db_empty_list(self):
        self.DB['Repositories'] = [] # Ensure it's an empty list
        self.assert_error_behavior(list_pull_requests,expected_exception_type=NotFoundError,expected_message="Repository 'user1/repo1' not found.",owner='user1', repo='repo1')

    def test_repo_resolution_skips_malformed_repo_data_missing_fullname(self):
        malformed_repo_no_fullname = {"id": 999, "name": "malformed_repo", "owner": {"login": "user1"}} 
        original_repos = list(self.DB.get('Repositories', [])) # Get a copy
        self.DB['Repositories'].append(malformed_repo_no_fullname)
        
        prs = list_pull_requests(owner='user1', repo='repo1') # Should still find user1/repo1
        self.assert_pr_ids_in_response(prs, [self.pr4['id'], self.pr1['id'], self.pr3['id'], self.pr5['id']])
        self.DB['Repositories'] = original_repos # Restore DB

    # --- State Filtering ---
    def test_filter_by_state_closed(self):
        # Default sort 'created', direction 'desc'
        # Closed PRs for user1/repo1: pr2 (created T-10d), pr6 (created T-20d)
        # Expected order: pr2, pr6
        prs = list_pull_requests(owner='user1', repo='repo1', state='closed')
        self.assert_pr_ids_in_response(prs, [self.pr2['id'], self.pr6['id']])
        for pr in prs:
            self.assertEqual(pr['state'], 'closed')

    def test_filter_by_state_all(self):
        # Default sort 'created', direction 'desc'
        # All PRs for user1/repo1, sorted by created_at desc:
        # pr4(T-2d), pr1(T-5d), pr2(T-10d), pr6(T-20d), pr3(T-40d), pr5(T-60d)
        prs = list_pull_requests(owner='user1', repo='repo1', state='all')
        self.assert_pr_ids_in_response(prs, [self.pr4['id'], self.pr1['id'], self.pr2['id'], self.pr6['id'], self.pr3['id'], self.pr5['id']])

    def test_filter_by_state_invalid(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="Invalid state. Must be one of ['open', 'closed', 'all'].",owner='user1', repo='repo1', state='invalid_state')

    # --- Sorting ---
    def test_sort_by_created_asc(self):
        # Open PRs, created_at asc: pr5(T-60d), pr3(T-40d), pr1(T-5d), pr4(T-2d)
        prs = list_pull_requests(owner='user1', repo='repo1', sort='created', direction='asc')
        self.assert_pr_ids_in_response(prs, [self.pr5['id'], self.pr3['id'], self.pr1['id'], self.pr4['id']])

    def test_sort_by_updated_desc(self):
        # Open PRs: pr1(upd T-1d), pr3(upd T-2d), pr4(upd T-2d), pr5(upd T-35d)
        # Sorted by updated_at desc. Tie between pr3 and pr4.
        # Assuming stable sort, original relative order of pr3, pr4 (from filtered_prs) is maintained.
        # Default filter order (open state): pr1, pr3, pr4, pr5.
        # Expected result: pr1, pr3, pr4, pr5.
        prs = list_pull_requests(owner='user1', repo='repo1', sort='updated', direction='desc')
        self.assert_pr_ids_in_response(prs, [self.pr1['id'], self.pr3['id'], self.pr4['id'], self.pr5['id']])

    def test_sort_by_updated_asc_default_direction_if_direction_is_none(self):
        # direction=None, sort='updated' -> effective_direction='asc'
        # Open PRs: pr1(upd T-1d), pr3(upd T-2d), pr4(upd T-2d), pr5(upd T-35d)
        # Sorted by updated_at asc: pr5, (pr3, pr4 stable sort), pr1
        prs = list_pull_requests(owner='user1', repo='repo1', sort='updated', direction=None) 
        self.assert_pr_ids_in_response(prs, [self.pr5['id'], self.pr3['id'], self.pr4['id'], self.pr1['id']])

    def test_sort_by_updated_asc_when_direction_not_passed(self):
        # direction not passed -> signature default 'desc' is used.
        # sort='updated', direction='desc' (from signature)
        prs = list_pull_requests(owner='user1', repo='repo1', sort='updated')
        self.assert_pr_ids_in_response(prs, [self.pr1['id'], self.pr3['id'], self.pr4['id'], self.pr5['id']])

    def test_sort_by_popularity_desc(self):
        # Open PRs: pr1(5c), pr3(10c), pr4(0c), pr5(1c)
        # Sorted by comments desc: pr3, pr1, pr5, pr4
        prs = list_pull_requests(owner='user1', repo='repo1', sort='popularity', direction='desc')
        self.assert_pr_ids_in_response(prs, [self.pr3['id'], self.pr1['id'], self.pr5['id'], self.pr4['id']])

    def test_sort_by_popularity_asc_default_direction_if_direction_is_none(self):
        # direction=None, sort='popularity' -> effective_direction='asc'
        # Sorted by comments asc: pr4, pr5, pr1, pr3
        prs = list_pull_requests(owner='user1', repo='repo1', sort='popularity', direction=None) 
        self.assert_pr_ids_in_response(prs, [self.pr4['id'], self.pr5['id'], self.pr1['id'], self.pr3['id']])

    def test_sort_by_long_running_asc_default_direction_if_direction_is_none(self):
        # direction=None, sort='long-running' -> effective_direction='asc'
        # Long-running PRs sorted by created_at asc.
        # pr3 (created T-40d)
        pr_lr2 = self._create_db_pr(id=7,number=7,title='Very Old Active Feature',repo_full_name='user1/repo1',head_repo_full_name='user1/repo1',head_branch='lr_feature2',base_branch='main',user_login='user1',state='open',created_at=self._iso_timestamp(self.now - timedelta(days=100)),updated_at=self._iso_timestamp(self.now - timedelta(days=5)),comments=1)
        original_prs_db = list(self.DB['PullRequests'])
        self.DB['PullRequests'].append(pr_lr2) # lr2 (created T-100d)
        # Expected ASC: lr2, pr3
        prs = list_pull_requests(owner='user1', repo='repo1', sort='long-running', direction=None)
        self.assert_pr_ids_in_response(prs, [pr_lr2['id'], self.pr3['id']])
        self.DB['PullRequests'] = original_prs_db


    def test_sort_by_long_running_desc(self):
        # direction='desc', sort='long-running' -> effective_direction='desc'
        pr_lr2 = self._create_db_pr(id=7,number=7,title='Very Old Active Feature',repo_full_name='user1/repo1',head_repo_full_name='user1/repo1',head_branch='lr_feature2',base_branch='main',user_login='user1',state='open',created_at=self._iso_timestamp(self.now - timedelta(days=100)),updated_at=self._iso_timestamp(self.now - timedelta(days=5)),comments=1)
        original_prs_db = list(self.DB['PullRequests'])
        self.DB['PullRequests'].append(pr_lr2)
        # Expected DESC: pr3, lr2
        prs = list_pull_requests(owner='user1', repo='repo1', sort='long-running', direction='desc')
        self.assert_pr_ids_in_response(prs, [self.pr3['id'], pr_lr2['id']])
        self.DB['PullRequests'] = original_prs_db
        
    def test_sort_long_running_filters_out_old_inactive_pr(self):
        # This covers the case: created_at < one_month_ago (True for pr5), but updated_at > one_month_ago (False for pr5)
        # PR5: created 60d ago, updated 35d ago. Not active recently.
        original_prs_db = list(self.DB['PullRequests']) # Save current state
        # Isolate PRs for clarity: only pr3 (long-running) and pr5 (old, inactive)
        self.DB['PullRequests'] = [pr for pr in original_prs_db if pr['id'] in [self.pr3['id'], self.pr5['id']]]
        
        # state='open' is default, so both pr3 and pr5 pass initial state filter
        # sort='long-running', direction='desc' (default from signature)
        prs = list_pull_requests(owner='user1', repo='repo1', sort='long-running')
        self.assert_pr_ids_in_response(prs, [self.pr3['id']]) # pr5 should be filtered out by updated_at check
        self.DB['PullRequests'] = original_prs_db # Restore

    def test_sort_long_running_filters_out_recent_active_pr(self):
        # This covers the case: created_at < one_month_ago (False for pr1)
        # PR1: created 5d ago (recent), updated 1d ago (active).
        original_prs_db = list(self.DB['PullRequests'])
        # Isolate PRs: pr3 (long-running) and pr1 (recent, active)
        self.DB['PullRequests'] = [pr for pr in original_prs_db if pr['id'] in [self.pr3['id'], self.pr1['id']]]
        
        # state='open' is default. sort='long-running', direction='desc' (default)
        prs = list_pull_requests(owner='user1', repo='repo1', sort='long-running')
        self.assert_pr_ids_in_response(prs, [self.pr3['id']]) # pr1 should be filtered out by created_at check
        self.DB['PullRequests'] = original_prs_db

    def test_sort_long_running_with_malformed_created_at(self):
        pr_malformed = self._create_db_pr(id=7,number=7,title='Malformed Created Date PR',repo_full_name='user1/repo1',head_repo_full_name='user1/repo1',head_branch='malformed1_branch',base_branch='main',user_login='user1',state='open',created_at="invalid-date-string",updated_at=self._iso_timestamp(self.now-timedelta(days=3)),comments=1)
        original_prs_db = list(self.DB['PullRequests'])
        self.DB['PullRequests'].append(pr_malformed)
        prs = list_pull_requests(owner='user1', repo='repo1', sort='long-running')
        self.assert_pr_ids_in_response(prs, [self.pr3['id']]) # Malformed PR should be skipped
        self.DB['PullRequests'] = original_prs_db

    def test_sort_long_running_with_none_updated_at(self):
        # Note: _create_db_pr might not handle `updated_at=None` directly as an override if it expects str.
        # We can create a PR dict and then modify 'updated_at' to None.
        pr_none_upd = self._create_db_pr(id=8,number=8,title='None Updated At PR',repo_full_name='user1/repo1',head_repo_full_name='user1/repo1',head_branch='none_updated_branch',base_branch='main',user_login='user1',state='open',created_at=self._iso_timestamp(self.now-timedelta(days=45)),updated_at="dummy_date_to_be_replaced",comments=1)
        pr_none_upd['updated_at'] = None # type: ignore  Force None for testing
        original_prs_db = list(self.DB['PullRequests'])
        self.DB['PullRequests'].append(pr_none_upd)
        prs = list_pull_requests(owner='user1', repo='repo1', sort='long-running')
        self.assert_pr_ids_in_response(prs, [self.pr3['id']]) # PR with None updated_at should be skipped
        self.DB['PullRequests'] = original_prs_db
        
    def test_sort_long_running_only_includes_open_prs_and_skips_closed_ones(self):
        # This test ensures the `continue` for non-open PRs inside long-running logic is hit (line 258 approx).
        # The `closed_long_running_candidate` should pass the initial state filter (state='all'),
        # then be considered by the long-running sort logic, then skipped due to being 'closed'.
        closed_lr_candidate = self._create_db_pr(id=9,number=9,title='Closed Long Running Candidate',repo_full_name='user1/repo1',head_repo_full_name='user1/repo1',head_branch='closed_lr_branch',base_branch='main',user_login='user1',state='closed',created_at=self._iso_timestamp(self.now-timedelta(days=50)),updated_at=self._iso_timestamp(self.now-timedelta(days=5)),comments=1)
        original_prs_db = list(self.DB['PullRequests'])
        self.DB['PullRequests'].append(closed_lr_candidate)
        
        # Use state='all' to ensure the closed PR is not filtered out by the primary state filter.
        # Default sort direction for long-running (when direction not given) is 'desc'.
        prs = list_pull_requests(owner='user1', repo='repo1', sort='long-running', state='all')
        
        # Expected result should only contain pr3 (which is open and long-running)
        # and NOT the closed_long_running_candidate.
        self.assert_pr_ids_in_response(prs, [self.pr3['id']])
        self.DB['PullRequests'] = original_prs_db

    def test_sort_invalid(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="Invalid sort. Must be one of ['created', 'updated', 'popularity', 'long-running'].",owner='user1', repo='repo1', sort='invalid_sort_value')

    # --- Direction ---
    def test_direction_invalid(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="Invalid direction. Must be one of ['asc', 'desc'] or None.",owner='user1', repo='repo1', direction='sideways_direction')
    
    def test_sort_created_direction_none(self):
        # direction=None, sort='created' -> effective_direction='desc'
        prs = list_pull_requests(owner='user1', repo='repo1', sort='created', direction=None)
        self.assert_pr_ids_in_response(prs, [self.pr4['id'], self.pr1['id'], self.pr3['id'], self.pr5['id']])

    # --- Pagination ---
    def test_pagination_per_page_and_page_number(self):
        # Default sort is 'created', 'desc'. Open PRs: pr4, pr1, pr3, pr5
        prs_page1 = list_pull_requests(owner='user1', repo='repo1', per_page=2, page=1)
        self.assert_pr_ids_in_response(prs_page1, [self.pr4['id'], self.pr1['id']])

        prs_page2 = list_pull_requests(owner='user1', repo='repo1', per_page=2, page=2)
        self.assert_pr_ids_in_response(prs_page2, [self.pr3['id'], self.pr5['id']])

    def test_pagination_page_out_of_bounds(self):
        prs = list_pull_requests(owner='user1', repo='repo1', per_page=2, page=3) # 4 open PRs, page 3 should be empty
        self.assertIsInstance(prs, list)
        self.assertEqual(prs, [])

    def test_pagination_per_page_invalid_value_zero(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="per_page must be between 1 and 100.",owner='user1', repo='repo1', per_page=0)
        
    def test_pagination_per_page_invalid_value_too_high(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="per_page must be between 1 and 100.",owner='user1', repo='repo1', per_page=101)

    def test_pagination_page_invalid_value(self):
        self.assert_error_behavior(list_pull_requests,expected_exception_type=ValidationError,expected_message="page must be 1 or greater.",owner='user1', repo='repo1', page=0)

    # --- Case Insensitivity ---
    def test_owner_and_repo_case_insensitivity(self):
        # Default sort 'created', 'desc'
        prs = list_pull_requests(owner='UsEr1', repo='RePo1')
        self.assert_pr_ids_in_response(prs, [self.pr4['id'], self.pr1['id'], self.pr3['id'], self.pr5['id']])

    # --- Combined Filters ---
    def test_combined_filters_sort_pagination(self):
        # State: all, sort: popularity, direction: asc, per_page: 2, page: 1
        # The 'base' parameter is not supported by list_pull_requests, so we filter manually.
        # PRs on base 'main': pr1(5c), pr2(2c), pr3(10c), pr5(1c), pr6(3c)
        # Sorted by comments asc: pr5(1), pr2(2), pr6(3), pr1(5), pr3(10)
        # Page 1 of 2: pr5, pr2

        # Get all PRs with state='all', sort by popularity (comments), asc
        prs = list_pull_requests(
            owner='user1',
            repo='repo1',
            state='all',
            sort='popularity',
            direction='asc',
            per_page=100,  # get all, we'll paginate manually
            page=1
        )
        # Manually filter for base='main'
        prs_on_main = [pr for pr in prs if pr['base']['ref'] == 'main']
        # Now paginate: per_page=2, page=1
        paginated = prs_on_main[0:2]
        self.assert_pr_ids_in_response(paginated, [self.pr5['id'], self.pr2['id']])

    # --- PR Structure Verification ---
    def test_pr_structure_full(self):
        # Get pr1 specifically to check its structure (head='user1:feature1')
        prs = list_pull_requests(owner='user1', repo='repo1')
        pr_data_from_api = [pr for pr in prs if pr['id'] == self.pr1['id']][0]
        expected_pr1_data = self.pr1 # This is the dictionary created by _create_db_pr

        # Basic fields
        self.assertEqual(pr_data_from_api['id'], expected_pr1_data['id'])
        self.assertEqual(pr_data_from_api['node_id'], expected_pr1_data['node_id'])
        self.assertEqual(pr_data_from_api['number'], expected_pr1_data['number'])
        self.assertEqual(pr_data_from_api['title'], expected_pr1_data['title'])
        self.assertEqual(pr_data_from_api['state'], expected_pr1_data['state'])
        self.assertEqual(pr_data_from_api['locked'], expected_pr1_data['locked'])
        self.assertEqual(pr_data_from_api['created_at'], expected_pr1_data['created_at'])
        self.assertEqual(pr_data_from_api['updated_at'], expected_pr1_data['updated_at'])
        self.assertEqual(pr_data_from_api['closed_at'], expected_pr1_data['closed_at'])
        self.assertEqual(pr_data_from_api['merged_at'], expected_pr1_data['merged_at'])
        self.assertEqual(pr_data_from_api['body'], expected_pr1_data['body'])
        self.assertEqual(pr_data_from_api['author_association'], expected_pr1_data['author_association'])
        self.assertEqual(pr_data_from_api['draft'], expected_pr1_data['draft'])
        self.assertEqual(pr_data_from_api['merged'], expected_pr1_data['merged'])
        self.assertEqual(pr_data_from_api['mergeable'], expected_pr1_data['mergeable'])
        self.assertEqual(pr_data_from_api['rebaseable'], expected_pr1_data['rebaseable'])
        self.assertEqual(pr_data_from_api['mergeable_state'], expected_pr1_data['mergeable_state'])
        self.assertEqual(pr_data_from_api['comments'], expected_pr1_data['comments'])
        self.assertEqual(pr_data_from_api['review_comments'], expected_pr1_data['review_comments'])
        self.assertEqual(pr_data_from_api['commits'], expected_pr1_data['commits'])
        self.assertEqual(pr_data_from_api['additions'], expected_pr1_data['additions'])
        self.assertEqual(pr_data_from_api['deletions'], expected_pr1_data['deletions'])
        self.assertEqual(pr_data_from_api['changed_files'], expected_pr1_data['changed_files'])

        # User object
        self.assertDictEqual(pr_data_from_api['user'], expected_pr1_data['user'])

        # Labels list
        self.assertListEqual(pr_data_from_api['labels'], expected_pr1_data['labels'])

        # Assignee and Assignees
        # Handle None case for assignee by comparing to empty dict if None
        self.assertDictEqual(pr_data_from_api.get('assignee') or {}, expected_pr1_data.get('assignee') or {})
        self.assertListEqual(pr_data_from_api.get('assignees', []), expected_pr1_data.get('assignees', []))
        
        # Merged By
        self.assertDictEqual(pr_data_from_api.get('merged_by') or {}, expected_pr1_data.get('merged_by') or {})

        # Milestone object (compare carefully, can be None)
        if expected_pr1_data.get('milestone'):
            self.assertTrue(isinstance(pr_data_from_api.get('milestone'), dict))
            # Compare all relevant fields of the milestone
            self.assertDictEqual(pr_data_from_api['milestone'], expected_pr1_data['milestone'])
        else:
            self.assertIsNone(pr_data_from_api.get('milestone'))

        # Head and Base branches (these are complex nested dicts)
        self.assertDictEqual(pr_data_from_api['head'], expected_pr1_data['head'])
        self.assertDictEqual(pr_data_from_api['base'], expected_pr1_data['base'])
class TestUpdatePullRequest(BaseTestCaseWithErrorHandler): # type: ignore
    """
    Test suite for the update_pull_request function.
    """
    
    def setUp(self):
        """
        Set up the test environment before each test.
        Initializes the DB with default users, repository, branches, and a pull request.
        Timestamps are stored as ISO 8601 strings in the DB, matching utils behavior.
        """
        
        self.DB = DB # type: ignore # DB is globally available
        self.DB.clear()

        # Default Users
        self.user_owner_login = "testowner"
        self.user_creator_login = "prcreator"

        self.user_owner = {
            "id": 1, "login": self.user_owner_login,  "type": "User", "site_admin": False,
            "name": "Test Owner", "email": "owner@example.com",
            "created_at": "2020-01-01T00:00:00Z", "updated_at": "2020-01-01T00:00:00Z"
        }
        self.user_creator = {
            "id": 2, "login": self.user_creator_login, "type": "User", "site_admin": False,
            "name": "PR Creator", "email": "creator@example.com",
            "created_at": "2020-01-02T00:00:00Z", "updated_at": "2020-01-02T00:00:00Z"
        }
        self.DB["Users"] = [copy.deepcopy(self.user_owner), copy.deepcopy(self.user_creator)]

        # Default Repository
        self.repo_full_name = f"{self.user_owner_login}/test-repo"
        self.repo_name = "test-repo"
        self.repo_id = 101

        self.repo_owner_db_format = { # Corresponds to BaseUser in DB schema
            "id": self.user_owner["id"], "login": self.user_owner["login"],
            "type": self.user_owner["type"],
            "site_admin": self.user_owner["site_admin"]
        }
        self.repo_details = {
            "id": self.repo_id, "node_id": "REPO_NODE_1", "name": self.repo_name, "full_name": self.repo_full_name,
            "private": False, "owner": copy.deepcopy(self.repo_owner_db_format),
            "description": "A test repository", "fork": False,
            "created_at": "2021-01-01T12:00:00Z", "updated_at": "2021-01-01T12:00:00Z",
            "pushed_at": "2021-01-01T12:00:00Z", "size": 1024, "language": "Python", "default_branch": "main",
            "stargazers_count": 0, "watchers_count": 0, "forks_count": 0, "open_issues_count": 1,
            "has_issues": True, "has_projects": True, "has_downloads": True, "has_wiki": True, "has_pages": False,
            "archived": False, "disabled": False, "allow_forking": True, "is_template": False,
            "web_commit_signoff_required": False, "topics": [], "visibility": "public",
            "forks": 0, "open_issues": 1, "watchers": 0,
        }
        self.DB["Repositories"] = [copy.deepcopy(self.repo_details)]

        # Default Branches
        self.branch_main_sha = "main_branch_sha_deadbeef01"
        self.branch_develop_sha = "dev_branch_sha_deadbeef02"
        self.branch_feature_sha = "feat_branch_sha_deadbeef03"

        self.DB["Branches"] = [
            {"repository_id": self.repo_id, "name": "main", "commit": {"sha": self.branch_main_sha}, "protected": False},
            {"repository_id": self.repo_id, "name": "develop", "commit": {"sha": self.branch_develop_sha}, "protected": False},
            {"repository_id": self.repo_id, "name": "feature", "commit": {"sha": self.branch_feature_sha}, "protected": False},
        ]

        # Default Pull Request
        self.pr_number = 1
        self.initial_pr_created_at_str = "2023-01-01T10:00:00Z"
        self.initial_pr_updated_at_str = "2023-01-01T10:05:00Z"

        self.pr_user_for_db = { # Corresponds to BaseUser in DB schema
            "id": self.user_creator["id"], "login": self.user_creator["login"],
             "type": self.user_creator["type"],
            "site_admin": self.user_creator["site_admin"]
        }
        # For PR base/head.user, which is also BaseUser
        self.pr_branch_user_for_db = copy.deepcopy(self.repo_owner_db_format)


        # For PR base/head.repo, which is Repository model in DB schema
        self.pr_repo_for_db = copy.deepcopy(self.repo_details)

        self.default_pr = {
            "id": 1001, "node_id": "PR_NODE_1001", "number": self.pr_number,
            "title": "Initial Title", "body": "Initial body content.",
            "state": "open", "locked": False, "draft": False,
            "user": copy.deepcopy(self.pr_user_for_db),
            "created_at": self.initial_pr_created_at_str,
            "updated_at": self.initial_pr_updated_at_str,
            "closed_at": None, "merged_at": None,
            "merged": False, "mergeable": True, "mergeable_state": "clean", "merged_by": None,
            "comments": 0, "review_comments": 0, "commits": 2, "additions": 10, "deletions": 1, "changed_files": 1,
            "author_association": "CONTRIBUTOR",
            "assignee": None, "assignees": [], "labels": [], "milestone": None,
            "head": {
                "label": f"{self.user_creator_login}:feature", "ref": "feature", "sha": self.branch_feature_sha,
                "user": copy.deepcopy(self.pr_user_for_db),
                "repo": copy.deepcopy(self.pr_repo_for_db)
            },
            "base": {
                "label": f"{self.user_owner_login}:main", "ref": "main", "sha": self.branch_main_sha,
                "user": copy.deepcopy(self.pr_branch_user_for_db),
                "repo": copy.deepcopy(self.pr_repo_for_db)
            },
            "maintainer_can_modify": True
        }
        self.DB["PullRequests"] = [copy.deepcopy(self.default_pr)]

    def _get_pr_from_db(self, pr_number: int):
        # Helper to retrieve a PR from the DB by its number (assuming it's for self.repo_id)
        for pr_data in self.DB["PullRequests"]:
            if pr_data["number"] == pr_number and pr_data["base"]["repo"]["id"] == self.repo_id:
                return pr_data
        return None

    def _assert_timestamps_updated(self, original_updated_at_str: str, new_updated_at_str: str, new_closed_at_str: Optional[str] = "check_separately"):
        self.assertNotEqual(original_updated_at_str, new_updated_at_str, "updated_at timestamp was not changed.")
        datetime.fromisoformat(new_updated_at_str.replace("Z", "+00:00")) # Validate format

        if new_closed_at_str != "check_separately": # Allow skipping or explicit None check
            if new_closed_at_str is not None:
                 datetime.fromisoformat(new_closed_at_str.replace("Z", "+00:00")) # Validate format if present

    def _assert_pr_response_structure(self, result_pr: dict, db_pr_after_update: dict):
        """Verifies that the API response matches expected structure based on DB data"""
        
        # 1. Verify basic fields that match directly
        self.assertEqual(result_pr["id"], db_pr_after_update["id"])
        self.assertEqual(result_pr["number"], db_pr_after_update["number"])
        self.assertEqual(result_pr["state"], db_pr_after_update["state"])
        self.assertEqual(result_pr["title"], db_pr_after_update["title"])
        self.assertEqual(result_pr["body"], db_pr_after_update["body"])
        self.assertEqual(result_pr["draft"], db_pr_after_update["draft"])
        self.assertEqual(result_pr["merged"], db_pr_after_update["merged"])
        self.assertEqual(result_pr["mergeable"], db_pr_after_update["mergeable"])
        self.assertEqual(result_pr["mergeable_state"], db_pr_after_update["mergeable_state"])
        
        # 2. Verify timestamp fields are converted from datetime to string
        if isinstance(db_pr_after_update["created_at"], datetime):
            self.assertEqual(result_pr["created_at"], db_pr_after_update["created_at"].isoformat().replace("+00:00", "Z"))
        else:
            self.assertEqual(result_pr["created_at"], db_pr_after_update["created_at"])
            
        if isinstance(db_pr_after_update["updated_at"], datetime):
            self.assertEqual(result_pr["updated_at"], db_pr_after_update["updated_at"].isoformat().replace("+00:00", "Z"))
        else:
            self.assertEqual(result_pr["updated_at"], db_pr_after_update["updated_at"])
            
        # Optional timestamps
        if db_pr_after_update["closed_at"]:
            if isinstance(db_pr_after_update["closed_at"], datetime):
                self.assertEqual(result_pr["closed_at"], db_pr_after_update["closed_at"].isoformat().replace("+00:00", "Z"))
            else:
                self.assertEqual(result_pr["closed_at"], db_pr_after_update["closed_at"])
        else:
            self.assertIsNone(result_pr["closed_at"])
            
        if db_pr_after_update["merged_at"]:
            if isinstance(db_pr_after_update["merged_at"], datetime):
                self.assertEqual(result_pr["merged_at"], db_pr_after_update["merged_at"].isoformat().replace("+00:00", "Z"))
            else:
                self.assertEqual(result_pr["merged_at"], db_pr_after_update["merged_at"])
        else:
            self.assertIsNone(result_pr["merged_at"])
        
        # 3. Verify fields that are renamed
        self.assertEqual(result_pr["comments_count"], db_pr_after_update.get("comments", 0))
        self.assertEqual(result_pr["review_comments_count"], db_pr_after_update.get("review_comments", 0))
        self.assertEqual(result_pr["commits_count"], db_pr_after_update.get("commits", 0))
        self.assertEqual(result_pr["additions_count"], db_pr_after_update.get("additions", 0))
        self.assertEqual(result_pr["deletions_count"], db_pr_after_update.get("deletions", 0))
        self.assertEqual(result_pr["changed_files_count"], db_pr_after_update.get("changed_files", 0))
        
        # 4. Verify user transformation (DB:BaseUser -> Response:PullRequestUser)
        self.assertEqual(result_pr["user"]["id"], db_pr_after_update["user"]["id"])
        self.assertEqual(result_pr["user"]["login"], db_pr_after_update["user"]["login"])
        self.assertEqual(result_pr["user"]["type"], db_pr_after_update["user"]["type"])
        self.assertNotIn("node_id", result_pr["user"])
        self.assertNotIn("site_admin", result_pr["user"])
        
        # 5. Verify merged_by if present
        if db_pr_after_update.get("merged_by"):
            self.assertEqual(result_pr["merged_by"]["id"], db_pr_after_update["merged_by"]["id"])
            self.assertEqual(result_pr["merged_by"]["login"], db_pr_after_update["merged_by"]["login"])
            self.assertEqual(result_pr["merged_by"]["type"], db_pr_after_update["merged_by"]["type"])
            self.assertNotIn("node_id", result_pr["merged_by"])
            self.assertNotIn("site_admin", result_pr["merged_by"])
        else:
            self.assertIsNone(result_pr["merged_by"])
        
        # 6. Verify branch transformations
        for branch_type in ["base", "head"]:
            self.assertEqual(result_pr[branch_type]["label"], db_pr_after_update[branch_type]["label"])
            self.assertEqual(result_pr[branch_type]["ref"], db_pr_after_update[branch_type]["ref"])
            self.assertEqual(result_pr[branch_type]["sha"], db_pr_after_update[branch_type]["sha"])
            
            # Verify repo part of branch
            if db_pr_after_update[branch_type].get("repo"):
                self.assertEqual(result_pr[branch_type]["repo"]["id"], db_pr_after_update[branch_type]["repo"]["id"])
                self.assertEqual(result_pr[branch_type]["repo"]["name"], db_pr_after_update[branch_type]["repo"]["name"])
                self.assertEqual(result_pr[branch_type]["repo"]["full_name"], db_pr_after_update[branch_type]["repo"]["full_name"])
                self.assertEqual(result_pr[branch_type]["repo"]["private"], db_pr_after_update[branch_type]["repo"]["private"])
                self.assertNotIn("description", result_pr[branch_type]["repo"])
            else:
                self.assertIsNone(result_pr[branch_type]["repo"])
        
        # 7. Verify maintainer_can_modify (special case - added in response construction)
        self.assertIn("maintainer_can_modify", result_pr)
        
        # 8. Verify all expected fields are present
        expected_fields = [
            "id", "number", "state", "title", "body", "user", "created_at", "updated_at",
            "closed_at", "merged_at", "base", "head", "draft", "merged", "mergeable",
            "mergeable_state", "merged_by", "comments_count", "review_comments_count",
            "maintainer_can_modify", "commits_count", "additions_count", "deletions_count",
            "changed_files_count"
        ]
        for field in expected_fields:
            self.assertIn(field, result_pr, f"Field '{field}' missing in response")


    # --- Success Cases ---
    def test_update_title(self):
        new_title = "Updated PR Title"
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, title=new_title)

        self.assertEqual(result["title"], new_title)
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertEqual(db_pr["title"], new_title)
        self._assert_pr_response_structure(result, db_pr)

    def test_update_body(self):
        new_body = "Updated PR body content."
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, body=new_body)

        self.assertEqual(result["body"], new_body)
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertEqual(db_pr["body"], new_body)
        self._assert_pr_response_structure(result, db_pr)

    def test_update_state_to_closed(self):
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, state="closed")

        self.assertEqual(result["state"], "closed")
        self.assertIsNotNone(result["closed_at"])
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"], result["closed_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertEqual(db_pr["state"], "closed")
        self.assertIsNotNone(db_pr["closed_at"])
        self._assert_pr_response_structure(result, db_pr)

    def test_update_state_to_open_from_closed(self):
        # First, modify DB to simulate a closed PR
        closed_pr_db = self._get_pr_from_db(self.pr_number)
        closed_pr_db["state"] = "closed"
        closed_pr_db["closed_at"] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat() + "Z"
        closed_pr_db["updated_at"] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat() + "Z"
        initial_closed_updated_at = closed_pr_db["updated_at"]

        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, state="open")

        self.assertEqual(result["state"], "open")
        self.assertIsNone(result["closed_at"])
        self._assert_timestamps_updated(initial_closed_updated_at, result["updated_at"], result["closed_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertEqual(db_pr["state"], "open")
        self.assertIsNone(db_pr["closed_at"])
        self._assert_pr_response_structure(result, db_pr)

    def test_update_base_branch(self):
        new_base_ref = "develop"
        new_base_sha = self.branch_develop_sha
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, base=new_base_ref)

        self.assertEqual(result["base"]["ref"], new_base_ref)
        self.assertEqual(result["base"]["sha"], new_base_sha)
        self.assertEqual(result["base"]["label"], f"{self.user_owner_login}:{new_base_ref}")
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertEqual(db_pr["base"]["ref"], new_base_ref)
        self.assertEqual(db_pr["base"]["sha"], new_base_sha)
        self._assert_pr_response_structure(result, db_pr)

    def test_update_maintainer_can_modify_to_false(self):
        # Initial value is True in setUp
        self.assertTrue(self._get_pr_from_db(self.pr_number)["maintainer_can_modify"])
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, maintainer_can_modify=False)

        self.assertFalse(result["maintainer_can_modify"])
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertFalse(db_pr["maintainer_can_modify"])
        self._assert_pr_response_structure(result, db_pr)

    def test_update_maintainer_can_modify_to_true(self):
        self._get_pr_from_db(self.pr_number)["maintainer_can_modify"] = False # Set to False initially
        self.assertFalse(self._get_pr_from_db(self.pr_number)["maintainer_can_modify"])
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, maintainer_can_modify=True)

        self.assertTrue(result["maintainer_can_modify"])
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertTrue(db_pr["maintainer_can_modify"])
        self._assert_pr_response_structure(result, db_pr)

    def test_update_maintainer_can_modify_not_provided_defaults_to_false(self):
        # Initial value is True in setUp
        self.assertTrue(self._get_pr_from_db(self.pr_number)["maintainer_can_modify"])
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, title="Title change only")

        self.assertFalse(result["maintainer_can_modify"]) # Default behavior
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertFalse(db_pr["maintainer_can_modify"])
        self.assertEqual(db_pr["title"], "Title change only")
        self._assert_pr_response_structure(result, db_pr)

    def test_update_multiple_fields(self):
        new_title = "Completely New Title"
        new_body = "Completely new body."
        new_state = "closed"
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number,
                                     title=new_title, body=new_body, state=new_state, maintainer_can_modify=False)

        self.assertEqual(result["title"], new_title)
        self.assertEqual(result["body"], new_body)
        self.assertEqual(result["state"], new_state)
        self.assertFalse(result["maintainer_can_modify"])
        self.assertIsNotNone(result["closed_at"])
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"], result["closed_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self._assert_pr_response_structure(result, db_pr)

    def test_no_updates_if_all_optional_fields_are_none_except_mcm(self):
        # maintainer_can_modify defaults to False if not provided.
        # If provided as None, it means "no change".
        original_pr_data = copy.deepcopy(self._get_pr_from_db(self.pr_number))
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number,
                                     title=None, body=None, state=None, base=None, maintainer_can_modify=True)

        self.assertEqual(result["title"], original_pr_data["title"])
        self.assertEqual(result["body"], original_pr_data["body"])
        self.assertEqual(result["state"], original_pr_data["state"])
        self.assertEqual(result["base"]["ref"], original_pr_data["base"]["ref"])
        self.assertEqual(result["maintainer_can_modify"], original_pr_data["maintainer_can_modify"])
        self._assert_timestamps_updated(self.initial_pr_updated_at_str, result["updated_at"])
        db_pr = self._get_pr_from_db(self.pr_number)
        self._assert_pr_response_structure(result, db_pr)


    # --- Error Cases: NotFoundError ---
    def test_error_repo_not_found_by_owner(self):
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=NotFoundError, expected_message="Repository nonexistentowner/test-repo not found.", # type: ignore
            owner="nonexistentowner", repo=self.repo_name, pull_number=self.pr_number, title="New Title"
        )

    def test_error_repo_not_found_by_name(self):
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=NotFoundError, expected_message="Repository testowner/nonexistent-repo not found.", # type: ignore
            owner=self.user_owner_login, repo="nonexistent-repo", pull_number=self.pr_number, title="New Title"
        )

    def test_error_pr_not_found(self):
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=NotFoundError, expected_message="Pull request #999 not found in testowner/test-repo.", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=999, title="New Title"
        )

    # --- Error Cases: ValidationError ---
    def test_error_invalid_state_value(self):
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="State must be 'open' or 'closed'.", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=self.pr_number, state="invalid_state_value"
        )

    def test_error_invalid_title_type(self):
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="title must be a string", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=self.pr_number, title=12345
        )

    def test_error_invalid_body_type(self):
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="body must be a string", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=self.pr_number, body=12345
        )

    def test_error_invalid_pull_number_type(self):
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="pull_number must be an integer, got 'not-an-int'", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number="not-an-int", title="A title" # type: ignore
        )

    def test_error_invalid_maintainer_can_modify_type(self):
         self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="maintainer_can_modify must be a boolean", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=self.pr_number, maintainer_can_modify="not-a-bool" # type: ignore
        )

    def test_error_invalid_state_type(self):
        """Test that providing a non-string type for state raises ValidationError."""
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="state must be a string", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=self.pr_number, state=123  # Non-string type
        )

    def test_error_invalid_base_type(self):
        """Test that providing a non-string type for base raises ValidationError."""
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="base must be a string", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=self.pr_number, base=123  # Non-string type
        )

    def test_error_invalid_owner_type(self):
        """Test that providing a non-string type for owner raises ValidationError."""
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="owner must be a string", # type: ignore
            owner=123, repo=self.repo_name, pull_number=self.pr_number, base=123  # Non-string type
        )

    def test_error_invalid_repo_type(self):
        """Test that providing a non-string type for repo raises ValidationError."""
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="repo must be a string", # type: ignore
            owner=self.user_owner_login, repo=123, pull_number=self.pr_number, base=123  # Non-string type
        )

    def test_error_invalid_empty_owner(self):
        """Test that providing an empty string for owner raises ValidationError."""
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="owner cannot be empty", # type: ignore
            owner="", repo=self.repo_name, pull_number=self.pr_number, base=123  # Non-string type
        )

    def test_error_invalid_empty_repo(self):
        """Test that providing an empty string for repo raises ValidationError."""
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="repo cannot be empty", # type: ignore
            owner=self.user_owner_login, repo="", pull_number=self.pr_number, base=123  # Non-string type
        )

    def test_error_invalid_pull_number_type(self):
        """Test that providing a non-integer type for pull_number raises ValidationError."""
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="pull_number must be an integer", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number="not-an-int", base=123  # Non-string type
        )

    def test_error_invalid_pull_number_value(self):
        """Test that providing a non-positive integer for pull_number raises ValidationError."""
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=ValidationError, expected_message="pull_number must be a positive integer", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=-1, base=123  # Non-string type
        )

    def test_merged_pr_with_merged_by_field(self):
        """Test handling of merged PR with merged_by field to cover response formatting."""
        # Modify PR in DB to be merged with merged_by field
        pr = self._get_pr_from_db(self.pr_number)
        pr["merged"] = True
        pr["state"] = "closed"
        pr["merged_at"] = "2023-01-02T15:00:00Z"
        pr["closed_at"] = "2023-01-02T15:00:00Z"
        pr["merged_by"] = copy.deepcopy(self.repo_owner_db_format)  # Owner merged the PR
        pr["updated_at"] = "2023-01-02T15:00:00Z"
        
        # Update title to trigger PR update function
        result = update_pull_request(self.user_owner_login, self.repo_name, self.pr_number, title="Updated merged PR")
        
        # Verify merged_by field is properly formatted in response
        self.assertIsNotNone(result["merged_by"])
        self.assertEqual(result["merged_by"]["id"], self.user_owner["id"])
        self.assertEqual(result["merged_by"]["login"], self.user_owner["login"])
        self.assertEqual(result["merged_by"]["type"], self.user_owner["type"])
        self.assertNotIn("node_id", result["merged_by"])
        self.assertNotIn("site_admin", result["merged_by"])
        
        # Verify in DB that merged_by was preserved
        db_pr = self._get_pr_from_db(self.pr_number)
        self.assertEqual(db_pr["merged_by"]["id"], self.user_owner["id"])
        self.assertEqual(db_pr["title"], "Updated merged PR")

    # --- Error Cases: UnprocessableEntityError ---
    def test_error_update_base_to_nonexistent_branch(self):
        self.assert_error_behavior(
            update_pull_request, expected_exception_type=UnprocessableEntityError, expected_message="Base branch 'nonexistent-branch-name' not found in repository testowner/test-repo.", # type: ignore
            owner=self.user_owner_login, repo=self.repo_name, pull_number=self.pr_number, base="nonexistent-branch-name"
        )
class TestAddPullRequestReviewComment(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self.DB = DB  # DB is globally available
        self.DB.clear()

        self.commenter_user_id = 1
        self.commenter_login = "test_commenter"
        self.owner_login = "test_owner"
        self.repo_name = "test_repo"
        self.repo_full_name = f"{self.owner_login}/{self.repo_name}"

        self._setup_initial_data()

    def _get_iso_timestamp(self):
        return datetime.now(timezone.utc).isoformat()

    def _setup_initial_data(self):
        # Create timestamp for consistent user creation times
        user_created_at = self._get_iso_timestamp()
        user_updated_at = self._get_iso_timestamp()
        
        self.DB["Users"] = [
            User(id=self.commenter_user_id, login=self.commenter_login, node_id="usernode123commenter", type="User", site_admin=False, created_at=user_created_at, updated_at=user_updated_at).model_dump(by_alias=True, exclude_none=True, mode='json'),
            User(id=2, login=self.owner_login, node_id="usernode123owner", type="User", site_admin=False, created_at=user_created_at, updated_at=user_updated_at).model_dump(by_alias=True, exclude_none=True, mode='json'),
            User(id=3, login="another_user", node_id="usernode123another", type="User", site_admin=False, created_at=user_created_at, updated_at=user_updated_at).model_dump(by_alias=True, exclude_none=True, mode='json'),
            User(id=4, login="readonly_user", node_id="usernode123readonly", type="User", site_admin=False, created_at=user_created_at, updated_at=user_updated_at).model_dump(by_alias=True, exclude_none=True, mode='json'),
        ]
        
        # Set up current user
        self.DB["CurrentUser"] = {
            "login": self.commenter_login,
            "id": self.commenter_user_id
        }

        self.repo_id = 101
        repo_owner_data = BaseUser(id=2, login=self.owner_login, type="User").model_dump(by_alias=True, exclude_none=True, mode='json')
        self.DB["Repositories"] = [
            Repository(
                id=self.repo_id, node_id="reponode123", name=self.repo_name, full_name=self.repo_full_name, private=False,
                owner=repo_owner_data,
                fork=False, created_at=self._get_iso_timestamp(), updated_at=self._get_iso_timestamp(), pushed_at=self._get_iso_timestamp(),
                size=1024, default_branch="main"
            ).model_dump(by_alias=True, exclude_none=True, mode='json')
        ]
        self.test_repo_data = self.DB["Repositories"][0]


        self.commit_sha_1 = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
        self.commit_sha_2 = "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9"

        # Creating properly formatted SHA for tree
        self.tree_sha_1 = "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b"
        self.tree_sha_2 = "b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1"
        self.blob_sha_1 = "c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0"
        self.blob_sha_2 = "d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1"

        self.DB["Commits"] = [
            Commit(
                sha=self.commit_sha_1, node_id="commitnode123a",
                commit=CommitNested(
                    author=GitActor(name="Test Author", email="author@example.com", date=self._get_iso_timestamp()),
                    committer=GitActor(name="Test Committer", email="committer@example.com", date=self._get_iso_timestamp()),
                    message="Initial commit",
                    tree=Tree(sha=self.tree_sha_1)
                ),
                author=BaseUser(id=2, login=self.owner_login).model_dump(by_alias=True, exclude_none=True, mode='json'),
                parents=[],
                files=[
                    CommitFileChange(sha=self.blob_sha_1, filename="src/main.py", status="modified", additions=10, deletions=2, changes=12, patch="@@ -1,10 +1,10 @@ ...").model_dump(by_alias=True, exclude_none=True, mode='json'),
                    CommitFileChange(sha=self.blob_sha_2, filename="README.md", status="added", additions=5, deletions=0, changes=5, patch="@@ -0,0 +1,5 @@ ...").model_dump(by_alias=True, exclude_none=True, mode='json')
                ]
            ).model_dump(by_alias=True, exclude_none=True, mode='json'),
            Commit(
                sha=self.commit_sha_2, node_id="commitnode123b",
                commit=CommitNested(
                    author=GitActor(name="Test Author", email="author@example.com", date=self._get_iso_timestamp()),
                    committer=GitActor(name="Test Committer", email="committer@example.com", date=self._get_iso_timestamp()),
                    message="Second commit",
                    tree=Tree(sha=self.tree_sha_2)
                ),
                author=BaseUser(id=2, login=self.owner_login).model_dump(by_alias=True, exclude_none=True, mode='json'),
                parents=[CommitParent(sha=self.commit_sha_1).model_dump(by_alias=True, exclude_none=True, mode='json')]
            ).model_dump(by_alias=True, exclude_none=True, mode='json')
        ]

        self.pr_number_1 = 1
        self.pr_id_1 = 201
        self.DB["PullRequests"] = [
            PullRequest(
                id=self.pr_id_1, node_id="prnode123a", number=self.pr_number_1, title="Test PR 1",
                user=BaseUser(id=2, login=self.owner_login).model_dump(by_alias=True, exclude_none=True, mode='json'),
                state="open", locked=False, created_at=self._get_iso_timestamp(), updated_at=self._get_iso_timestamp(),
                head=PullRequestBranchInfo(label=f"{self.owner_login}:feature-branch", ref="feature-branch", sha=self.commit_sha_1, user=BaseUser(id=2, login=self.owner_login).model_dump(by_alias=True, exclude_none=True, mode='json'), repo=self.test_repo_data),
                base=PullRequestBranchInfo(label=f"{self.owner_login}:main", ref="main", sha=self.commit_sha_2, user=BaseUser(id=2, login=self.owner_login).model_dump(by_alias=True, exclude_none=True, mode='json'), repo=self.test_repo_data),
                commits=2, # Number of commits in PR
                author_association="OWNER"
            ).model_dump(by_alias=True, exclude_none=True, mode='json')
        ]

        self.existing_comment_id = 301
        self.DB["PullRequestReviewComments"] = [
            PullRequestItemComment(
                id=self.existing_comment_id, node_id="prcommentnode123a", pull_request_id=self.pr_id_1,
                user=BaseUser(id=3, login="another_user").model_dump(by_alias=True, exclude_none=True, mode='json'),
                body="This is an existing comment", commit_id=self.commit_sha_1, path="src/main.py", position=1,
                line=1, side="RIGHT", # Explicitly set for reply context inheritance
                created_at=self._get_iso_timestamp(), updated_at=self._get_iso_timestamp(),
                author_association="CONTRIBUTOR"
            ).model_dump(by_alias=True, exclude_none=True, mode='json')
        ]

        self.DB["RepositoryCollaborators"] = [
            RepositoryCollaborator(repository_id=self.repo_id, user_id=self.commenter_user_id, permission="write").model_dump(by_alias=True, exclude_none=True, mode='json'),
            RepositoryCollaborator(repository_id=self.repo_id, user_id=2, permission="admin").model_dump(by_alias=True, exclude_none=True, mode='json'),
            RepositoryCollaborator(repository_id=self.repo_id, user_id=3, permission="write").model_dump(by_alias=True, exclude_none=True, mode='json'), # another_user also has write
            RepositoryCollaborator(repository_id=self.repo_id, user_id=4, permission="read").model_dump(by_alias=True, exclude_none=True, mode='json'), # readonly_user
        ]
        # For simulating the authenticated user, we assume the function uses a mechanism
        # to identify the current user. For tests, we'll assume it's self.commenter_user_id (ID 1).
        # The ForbiddenError tests will manipulate this user's permissions.

    def _assert_common_comment_fields(self, comment_data, expected_body, expected_commit_id, expected_path):
        self.assertIsInstance(comment_data, dict)

        parsed_response = AddPullRequestReviewCommentResponse.model_validate(comment_data)

        self.assertTrue(parsed_response.id > 0)
        self.assertEqual(parsed_response.body, expected_body)
        self.assertEqual(parsed_response.commit_id, expected_commit_id)
        self.assertEqual(parsed_response.path, expected_path)
        self.assertEqual(parsed_response.user.id, self.commenter_user_id)
        self.assertEqual(parsed_response.user.login, self.commenter_login)
        self.assertIsInstance(parsed_response.created_at, str)
        self.assertIsInstance(parsed_response.updated_at, str)
        self.assertIsNone(parsed_response.pull_request_review_id)

        comments_table = self.DB.get("PullRequestReviewComments", [])
        db_comment = next((c for c in comments_table if c["id"] == parsed_response.id), None)
        self.assertIsNotNone(db_comment)
        self.assertEqual(db_comment["body"], expected_body)
        self.assertEqual(db_comment["pull_request_id"], self.pr_id_1)
        self.assertEqual(db_comment["user"]["id"], self.commenter_user_id)
        return parsed_response # Return for further specific assertions

    # --- Success Cases ---
    def test_add_new_line_comment_success(self):
        body = "This is a new line comment."
        path = "src/main.py"
        line = 10

        result = add_pull_request_review_comment(
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body=body, commit_id=self.commit_sha_1, path=path, line=line
        )
        parsed_response = self._assert_common_comment_fields(result, body, self.commit_sha_1, path)
        self.assertEqual(parsed_response.position, line)

        db_comment = next(c for c in self.DB["PullRequestReviewComments"] if c["id"] == result["id"])
        self.assertEqual(db_comment.get("line"), line)
        self.assertEqual(db_comment.get("side"), "RIGHT") # Default side

    def test_add_new_line_comment_explicit_side_left_success(self):
        body = "Comment on the LEFT side."
        path = "src/main.py"
        line = 5
        side = "LEFT"

        result = add_pull_request_review_comment(
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body=body, commit_id=self.commit_sha_1, path=path, line=line, side=side
        )
        parsed_response = self._assert_common_comment_fields(result, body, self.commit_sha_1, path)
        self.assertEqual(parsed_response.position, line)

        db_comment = next(c for c in self.DB["PullRequestReviewComments"] if c["id"] == result["id"])
        self.assertEqual(db_comment.get("line"), line)
        self.assertEqual(db_comment.get("side"), side)

    def test_add_new_multiline_comment_success(self):
        body = "This is a multi-line comment."
        path = "README.md"
        start_line = 2
        line = 4 
        side = "RIGHT"
        start_side = "RIGHT"

        result = add_pull_request_review_comment(
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body=body, commit_id=self.commit_sha_1, path=path,
            line=line, side=side, start_line=start_line, start_side=start_side
        )
        parsed_response = self._assert_common_comment_fields(result, body, self.commit_sha_1, path)
        self.assertEqual(parsed_response.position, line) 

        db_comment = next(c for c in self.DB["PullRequestReviewComments"] if c["id"] == result["id"])
        self.assertEqual(db_comment.get("line"), line)
        self.assertEqual(db_comment.get("side"), side)
        self.assertEqual(db_comment.get("start_line"), start_line)
        self.assertEqual(db_comment.get("start_side"), start_side)

    def test_add_new_file_comment_success(self):
        body = "This is a file-level comment."
        path = "src/main.py"
        subject_type = "file"

        result = add_pull_request_review_comment(
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body=body, commit_id=self.commit_sha_1, path=path, subject_type=subject_type
        )
        parsed_response = self._assert_common_comment_fields(result, body, self.commit_sha_1, path)
        self.assertIsNone(parsed_response.position)

        db_comment = next(c for c in self.DB["PullRequestReviewComments"] if c["id"] == result["id"])
        self.assertIsNone(db_comment.get("line"))
        self.assertIsNone(db_comment.get("side"))

    def test_add_reply_to_existing_comment_success(self):
        reply_body = "This is a reply to an existing comment."
        original_comment = next(c for c in self.DB["PullRequestReviewComments"] if c["id"] == self.existing_comment_id)

        result = add_pull_request_review_comment(
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body=reply_body, in_reply_to=self.existing_comment_id
        )
        parsed_response = self._assert_common_comment_fields(result, reply_body, original_comment["commit_id"], original_comment["path"])
        self.assertEqual(parsed_response.position, original_comment.get("position"))

        db_comment = next(c for c in self.DB["PullRequestReviewComments"] if c["id"] == result["id"])
        self.assertEqual(db_comment.get("in_reply_to"), self.existing_comment_id)
        self.assertEqual(db_comment.get("line"), original_comment.get("line"))
        self.assertEqual(db_comment.get("side"), original_comment.get("side"))
        self.assertEqual(db_comment.get("start_line"), original_comment.get("start_line"))
        self.assertEqual(db_comment.get("start_side"), original_comment.get("start_side"))


    def test_add_comment_owner_repo_case_insensitivity_lookup(self):
        body = "Testing case insensitivity for lookup."
        path = "src/main.py"
        line = 1

        result = add_pull_request_review_comment(
            owner=self.owner_login.upper(), repo=self.repo_name.capitalize(), pull_number=self.pr_number_1,
            body=body, commit_id=self.commit_sha_1, path=path, line=line
        )
        self._assert_common_comment_fields(result, body, self.commit_sha_1, path)

    def test_start_side_defaults_to_side_if_not_provided_for_multiline(self):
        body = "Multi-line, default start_side."
        path = "README.md"
        start_line = 2
        line = 3
        side = "LEFT"

        result = add_pull_request_review_comment(
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body=body, commit_id=self.commit_sha_1, path=path,
            line=line, side=side, start_line=start_line
        )
        self._assert_common_comment_fields(result, body, self.commit_sha_1, path)
        db_comment = next(c for c in self.DB["PullRequestReviewComments"] if c["id"] == result["id"])
        self.assertEqual(db_comment.get("start_side"), side)

    def test_subject_type_file_ignores_line_params_if_provided(self):
        body = "File comment, line params should be ignored."
        path = "src/main.py"
        subject_type = "file"

        result = add_pull_request_review_comment(
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body=body, commit_id=self.commit_sha_1, path=path, subject_type=subject_type,
            line=10, side="LEFT", start_line=5 # These should be ignored
        )
        parsed_response = self._assert_common_comment_fields(result, body, self.commit_sha_1, path)
        self.assertIsNone(parsed_response.position)
        db_comment = next(c for c in self.DB["PullRequestReviewComments"] if c["id"] == result["id"])
        self.assertIsNone(db_comment.get("line"))
        self.assertIsNone(db_comment.get("side"))

    # --- NotFoundError Cases ---
    def test_owner_not_found_raises_not_found_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, NotFoundError,
            expected_message="Repository nonexistent_owner/test_repo not found.",
            owner="nonexistent_owner", repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_repo_not_found_raises_not_found_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, NotFoundError,
            expected_message="Repository test_owner/nonexistent_repo not found.",
            owner=self.owner_login, repo="nonexistent_repo", pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_pull_number_not_found_raises_not_found_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, NotFoundError,
            expected_message="Pull request #999 not found in test_owner/test_repo.",
            owner=self.owner_login, repo=self.repo_name, pull_number=999,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_commit_id_not_found_for_new_comment_raises_not_found_error(self):
        invalid_commit_sha = "0000000000000000000000000000000000000000"
        self.assert_error_behavior(
            add_pull_request_review_comment, NotFoundError,
            expected_message="Commit with SHA 0000000000000000000000000000000000000000 not found in repository test_owner/test_repo.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=invalid_commit_sha, path="src/main.py", line=1
        )

    def test_in_reply_to_comment_id_not_found_raises_not_found_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, NotFoundError,
            expected_message="Parent comment with ID 9999 not found.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="reply test", in_reply_to=9999
        )

    # --- ValidationError Cases ---
    def test_missing_body_raises_validation_error(self): # Function expects str, empty str is validation
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="body is required and cannot be empty.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_missing_commit_id_for_new_comment_raises_validationerror(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="commit_id is required for new comments.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", path="src/main.py", line=1
        )

    def test_missing_path_for_new_comment_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="path is required for new comments.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, line=1
        )

    def test_missing_line_for_new_line_comment_if_inferred_raises_validationerror(self):
        self.assert_error_behavior( # Inferred by side
            add_pull_request_review_comment, ValidationError,
            expected_message="line is required when side is provided for line-level comments.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", side="RIGHT"
        )
        self.assert_error_behavior( # Explicit subject_type='line'
            add_pull_request_review_comment, ValidationError,
            expected_message="line is required for line-level comments.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", subject_type="line"
        )

    def test_invalid_side_value_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="side must be 'LEFT' or 'RIGHT'.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1, side="INVALID"
        )

    def test_invalid_start_side_value_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="start_side must be 'LEFT' or 'RIGHT'.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=2, start_line=1, start_side="INVALID"
        )

    def test_invalid_subject_type_value_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="Invalid subject_type: 'invalid_type'. Must be 'line' or 'file'.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", subject_type="invalid_type"
        )

    def test_start_line_without_line_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="Cannot determine comment type. Provide 'line' for a line comment, or set subject_type='file' for a file comment.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", start_line=1
        )

    def test_start_line_greater_than_line_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="start_line cannot be greater than line for multi-line comments.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1, start_line=2
        )

    def test_negative_or_zero_pull_number_raises_validation_error(self):
        for pull_num in [-1, 0]:
            self.assert_error_behavior(
                add_pull_request_review_comment, ValidationError,
                expected_message=f"pull_number must be a positive integer, got {pull_num}",
                owner=self.owner_login, repo=self.repo_name, pull_number=pull_num,
                body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
            )

    def test_negative_or_zero_line_raises_validationerror(self):
         for line_num in [-5, 0]:
            self.assert_error_behavior(
                add_pull_request_review_comment, ValidationError,
                expected_message=f"line must be a positive integer, got {line_num}",
                owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
                body="test", commit_id=self.commit_sha_1, path="src/main.py", line=line_num
            )

    def test_invalid_owner_type_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="owner must be a string, got 123",
            owner=123, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_empty_owner_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="owner cannot be empty.",
            owner="", repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_invalid_repo_type_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="repo must be a string, got 123",
            owner=self.owner_login, repo=123, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_empty_repo_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="repo cannot be empty.",
            owner=self.owner_login, repo="", pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_invalid_pull_number_type_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="pull_number must be an integer, got not-an-int",
            owner=self.owner_login, repo=self.repo_name, pull_number="not-an-int",
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    def test_invalid_body_type_raises_validation_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, ValidationError,
            expected_message="body must be a string, got 123",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body=123, commit_id=self.commit_sha_1, path="src/main.py", line=1
        )

    # --- UnprocessableEntityError Cases ---
    def test_path_not_in_commit_diff_raises_unprocessable_entity_error(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, UnprocessableEntityError,
            expected_message="Path 'non_existent_file.py' not found in commit a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="non_existent_file.py", line=1
        )

    def test_line_not_in_diff_for_path_raises_unprocessableentityerror(self):
        self.assert_error_behavior(
            add_pull_request_review_comment, UnprocessableEntityError,
            expected_message="Line 1000 is outside the diff range for path 'src/main.py'",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=self.commit_sha_1, path="src/main.py", line=1000
        )

    def test_commit_id_not_related_to_pr_head_raises_unprocessable_entity_error(self):
        unrelated_commit_sha = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef" # Valid SHA format
        unrelated_tree_sha = "e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1"
        self.DB["Commits"].append(
            Commit(
                sha=unrelated_commit_sha, node_id="commitnodeunrelated",
                commit=CommitNested(
                    author=GitActor(name="N A", email="na@example.com", date=self._get_iso_timestamp()),
                    committer=GitActor(name="N A", email="na@example.com", date=self._get_iso_timestamp()),
                    message="...",
                    tree=Tree(sha=unrelated_tree_sha)
                ),
                files=[CommitFileChange(sha="b1a2b3c4d5e6f7a8b9a0b1c2d3e4f5a6b7c8d9e0", filename="another.txt", status="added", additions=1, deletions=0, changes=1).model_dump(by_alias=True, exclude_none=True, mode='json')]
            ).model_dump(by_alias=True, exclude_none=True, mode='json')
        )
        self.assert_error_behavior(
            add_pull_request_review_comment, UnprocessableEntityError,
            expected_message=f"Commit {unrelated_commit_sha} is not related to pull request #{self.pr_number_1}",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test", commit_id=unrelated_commit_sha, path="another.txt", line=1
        )
    def test_reply_to_comment_in_different_pr_raises_unprocessable_entity_error(self):
        pr_id_2 = 202
        pr_number_2 = 2
        self.DB["PullRequests"].append(
            PullRequest(
                id=pr_id_2, node_id="prnode123b", number=pr_number_2, title="Test PR 2",
                user=BaseUser(id=2, login=self.owner_login).model_dump(by_alias=True, exclude_none=True, mode='json'), state="open", locked=False, created_at=self._get_iso_timestamp(), updated_at=self._get_iso_timestamp(),
                head=PullRequestBranchInfo(label="f2", ref="f2", sha=self.commit_sha_2, user=BaseUser(id=2, login=self.owner_login).model_dump(by_alias=True, exclude_none=True, mode='json'), repo=self.test_repo_data),
                base=PullRequestBranchInfo(label="main", ref="main", sha=self.commit_sha_1, user=BaseUser(id=2, login=self.owner_login).model_dump(by_alias=True, exclude_none=True, mode='json'), repo=self.test_repo_data),
                author_association="OWNER"
            ).model_dump(by_alias=True, exclude_none=True, mode='json')
        )
        self.assert_error_behavior(
            add_pull_request_review_comment, UnprocessableEntityError,
            expected_message="Parent comment 301 does not belong to pull request 2.",
            owner=self.owner_login, repo=self.repo_name, pull_number=pr_number_2,
            body="reply to comment in wrong PR", in_reply_to=self.existing_comment_id
        )

    # --- ForbiddenError Cases ---
    # Assumes the function determines the authenticated user is self.commenter_user_id (ID 1)
    def test_user_with_read_permission_raises_forbidden_error(self):
        original_collabs = copy.deepcopy(self.DB["RepositoryCollaborators"])
        for collab in self.DB["RepositoryCollaborators"]:
            if collab["user_id"] == self.commenter_user_id:
                collab["permission"] = "read"
                break

        self.assert_error_behavior(
            add_pull_request_review_comment, ForbiddenError,
            expected_message="User does not have permission to add review comments to this pull request.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test forbidden", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )
        self.DB["RepositoryCollaborators"] = original_collabs

    def test_user_not_collaborator_raises_forbidden_error(self):
        original_collabs = copy.deepcopy(self.DB["RepositoryCollaborators"])
        self.DB["RepositoryCollaborators"] = [
            c for c in self.DB["RepositoryCollaborators"] if c["user_id"] != self.commenter_user_id
        ]

        self.assert_error_behavior(
            add_pull_request_review_comment, ForbiddenError,
            expected_message="User does not have permission to add review comments to this pull request.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test forbidden no collab", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )
        self.DB["RepositoryCollaborators"] = original_collabs

    def test_no_current_user_raises_forbidden_error(self):
        # Temporarily remove current_user from DB
        original_current_user = self.DB.get("CurrentUser")
        self.DB.pop("CurrentUser", None)
        
        self.assert_error_behavior(
            add_pull_request_review_comment, ForbiddenError,
            expected_message="Unable to authenticate - no current user in the database.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test no current user", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )
        
        # Restore current_user
        self.DB["CurrentUser"] = original_current_user
        
    def test_invalid_current_user_raises_forbidden_error(self):
        # Save original current_user and Users table
        original_current_user = self.DB.get("CurrentUser")
        original_users = self.DB.get("Users")
        
        # Set current_user to a non-existent user ID
        non_existent_user_id = 9999
        self.DB["CurrentUser"] = {
            "login": "non_existent_user",
            "id": non_existent_user_id
        }
        
        self.assert_error_behavior(
            add_pull_request_review_comment, ForbiddenError,
            expected_message="Current user (ID: 9999) not found in user database.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pr_number_1,
            body="test invalid current user", commit_id=self.commit_sha_1, path="src/main.py", line=1
        )
        
        # Restore original values
        self.DB["CurrentUser"] = original_current_user
        self.DB["Users"] = original_users


class TestGetPullRequestFiles(BaseTestCaseWithErrorHandler): # type: ignore
    # type: ignore is used because BaseTestCaseWithErrorHandler is not defined here
    # but is expected to be in the global scope during test execution.
    
    def setUp(self):
        self.DB = DB # type: ignore # DB is globally available
        self.DB.clear()

        self.owner_login = "testowner"
        self.repo_name = "testrepo"
        self.repo_full_name = f"{self.owner_login}/{self.repo_name}"
        self.other_owner_login = "anotherowner"
        self.other_repo_name = "otherrepo"
        self.other_repo_full_name = f"{self.other_owner_login}/{self.other_repo_name}"

        # Users
        self.user_testowner_dict = {
            'id': 1, 'login': self.owner_login, 'node_id': 'user_node_1_aaaaaaaaaaaaaaaaaaaaaaaaaaaa',
            'type': 'User', 'site_admin': False, 'name': 'Test Owner',
            'email': 'owner@example.com', 'company': 'Test Inc.',
            'location': 'Test City', 'bio': 'A test user.',
            'public_repos': 1, 'public_gists': 0, 'followers': 10, 'following': 5,
            'created_at': '2020-01-01T00:00:00Z', 'updated_at': '2020-01-01T00:00:00Z',
            'score': 1.0  # Added score field to match DB.py structure
        }
        self.user_anotherowner_dict = {
            'id': 2, 'login': self.other_owner_login, 'node_id': 'user_node_2_bbbbbbbbbbbbbbbbbbbbbbbbbbbb',
            'type': 'User', 'site_admin': False, 'name': 'Another Owner',
            'created_at': '2020-02-01T00:00:00Z', 'updated_at': '2020-02-01T00:00:00Z',
            'score': 0.95  # Added score field to match DB.py structure
        }
        self.DB['Users'] = [self.user_testowner_dict, self.user_anotherowner_dict]

        # Embedded user representations for repository owner, PR user, etc.
        self.embedded_user_testowner = {'id': 1, 'login': self.owner_login, 'type': 'User', 'site_admin': False, 'node_id': 'user_node_1_aaaaaaaaaaaaaaaaaaaaaaaaaaaa'}
        self.embedded_user_anotherowner = {'id': 2, 'login': self.other_owner_login, 'type': 'User', 'site_admin': False, 'node_id': 'user_node_2_bbbbbbbbbbbbbbbbbbbbbbbbbbbb'}


        # Repositories
        self.repo_testrepo_data = {
            'id': 101, 'node_id': 'repo_node_101_cccccccccccccccccccccccccc', 'name': self.repo_name,
            'full_name': self.repo_full_name, 'private': False,
            'owner': self.embedded_user_testowner,
            'description': 'Test repository for pull request files.', 'fork': False,
            'created_at': '2021-01-01T00:00:00Z', 'updated_at': '2021-01-10T00:00:00Z',
            'pushed_at': '2021-01-10T00:00:00Z', 'size': 1024,
            'stargazers_count': 5, 'watchers_count': 5, 'language': 'Python',
            'has_issues': True, 'has_projects': True, 'has_downloads': True,
            'has_wiki': True, 'has_pages': False, 'forks_count': 0,
            'archived': False, 'disabled': False, 'open_issues_count': 1,
            'license': None, 'allow_forking': True, 'is_template': False,
            'web_commit_signoff_required': False, 'topics': ['testing', 'python'],
            'visibility': 'public', 'default_branch': 'main',
            'score': 1.0  # Added score field to match DB.py structure
            # Removed extra fields: 'forks', 'open_issues', 'watchers'
        }
        self.repo_otherrepo_data = {
            'id': 102, 'node_id': 'repo_node_102_dddddddddddddddddddddddddd', 'name': self.other_repo_name,
            'full_name': self.other_repo_full_name, 'private': False,
            'owner': self.embedded_user_anotherowner,
            'description': 'Another repository.', 'fork': False,
            'created_at': '2021-02-01T00:00:00Z', 'updated_at': '2021-02-10T00:00:00Z',
            'pushed_at': '2021-02-10T00:00:00Z', 'size': 512, 'default_branch': 'develop',
            'stargazers_count': 2, 'watchers_count': 2, 'language': 'JavaScript',
            'has_issues': True, 'has_projects': False, 'has_downloads': True,
            'has_wiki': False, 'has_pages': False, 'forks_count': 1,
            'archived': False, 'disabled': False, 'open_issues_count': 0,
            'license': None, 'allow_forking': True, 'is_template': False,
            'web_commit_signoff_required': False, 'topics': [], 'visibility': 'public',
            'score': 0.89  # Added score field to match DB.py structure
            # Removed extra fields: 'forks', 'open_issues', 'watchers'
        }
        self.DB['Repositories'] = [self.repo_testrepo_data, self.repo_otherrepo_data]

        # Define milestone template for PRs
        self.milestone_template = {
            'id': 1002604,
            'node_id': 'MDk6TWlsZXN0b25lMTAwMjYwNA==',
            'number': 3,
            'title': 'Test Milestone',
            'description': 'Test milestone description',
            'creator': self.embedded_user_testowner,
            'open_issues': 2,
            'closed_issues': 5,
            'state': 'open',
            'created_at': '2022-01-01T10:00:00Z',
            'updated_at': '2022-01-05T11:00:00Z',
            'closed_at': None,
            'due_on': '2022-05-30T23:59:59Z'
        }

        # Pull Requests
        pr1_repo_snapshot = copy.deepcopy(self.repo_testrepo_data)
        self.pr1_testrepo_data = {
            'id': 1, 'node_id': 'pr_node_1_eeeeeeeeeeeeeeeeeeeeeeeeeeeeee', 'number': 1,
            'repo_full_name': self.repo_full_name,
            'title': 'Feature Update for testrepo',
            'user': self.embedded_user_testowner, 'labels': [],
            'state': 'open', 'locked': False,
            'assignee': self.embedded_user_testowner,  # Added assignee field
            'assignees': [self.embedded_user_testowner],  # Added assignees array
            'milestone': self.milestone_template,  # Added milestone field
            'created_at': '2022-03-01T10:00:00Z', 'updated_at': '2022-03-01T11:00:00Z',
            'closed_at': None, 'merged_at': None,
            'head': {'label': f'{self.owner_login}:feature-branch', 'ref': 'feature-branch',
                     'sha': 'headsha0000000000000000000000000000000001',
                     'user': self.embedded_user_testowner, 'repo': pr1_repo_snapshot},
            'base': {'label': f'{self.owner_login}:main', 'ref': 'main',
                     'sha': 'basesha0000000000000000000000000000000001',
                     'user': self.embedded_user_testowner, 'repo': pr1_repo_snapshot},
            'body': 'Adds a new feature.', 'author_association': 'OWNER',
            'draft': False, 'merged': False, 'mergeable': True, 'rebaseable': True,
            'mergeable_state': 'clean', 'merged_by': None, 'comments': 0,
            'review_comments': 0, 'commits': 2, 'additions': 15, 'deletions': 3,
            'changed_files': 2, 'maintainer_can_modify': True  # Added maintainer_can_modify field
        }

        pr2_repo_snapshot = copy.deepcopy(self.repo_testrepo_data)
        self.pr2_testrepo_data = {
            'id': 2, 'node_id': 'pr_node_2_ffffffffffffffffffffffffffffff', 'number': 2,
            'repo_full_name': self.repo_full_name,
            'title': 'Documentation Update for testrepo',
            'user': self.embedded_user_testowner, 'labels': [],
            'state': 'open', 'locked': False,
            'assignee': None,  # Added assignee field (null)
            'assignees': [],  # Added empty assignees array
            'milestone': None,  # Added milestone field (null)
            'created_at': '2022-03-05T10:00:00Z', 'updated_at': '2022-03-05T11:00:00Z',
            'closed_at': None, 'merged_at': None,
            'head': {'label': f'{self.owner_login}:docs-update', 'ref': 'docs-update',
                     'sha': 'headsha0000000000000000000000000000000002',
                     'user': self.embedded_user_testowner, 'repo': pr2_repo_snapshot},
            'base': {'label': f'{self.owner_login}:main', 'ref': 'main',
                     'sha': 'basesha0000000000000000000000000000000002',
                     'user': self.embedded_user_testowner, 'repo': pr2_repo_snapshot},
            'body': 'Updates documentation.', 'author_association': 'OWNER',
            'draft': False, 'merged': False, 'mergeable': True, 'rebaseable': True,
            'mergeable_state': 'clean', 'merged_by': None, 'comments': 0,
            'review_comments': 0, 'commits': 1, 'additions': 20, 'deletions': 0,
            'changed_files': 1, 'maintainer_can_modify': True  # Added maintainer_can_modify field
        }

        pr1_otherrepo_snapshot = copy.deepcopy(self.repo_otherrepo_data)
        self.pr1_otherrepo_data = {
            'id': 3, 'node_id': 'pr_node_3_gggggggggggggggggggggggggggggg', 'number': 1,
            'repo_full_name': self.other_repo_full_name,
            'title': 'Bugfix for otherrepo',
            'user': self.embedded_user_anotherowner, 'labels': [],
            'state': 'open', 'locked': False,
            'assignee': self.embedded_user_anotherowner,  # Added assignee field
            'assignees': [self.embedded_user_anotherowner],  # Added assignees array
            'milestone': None,  # Added milestone field (null)
            'created_at': '2022-04-01T10:00:00Z', 'updated_at': '2022-04-01T11:00:00Z',
            'closed_at': None, 'merged_at': None,
            'head': {'label': f'{self.other_owner_login}:fix-bug', 'ref': 'fix-bug',
                     'sha': 'headsha0000000000000000000000000000000003',
                     'user': self.embedded_user_anotherowner, 'repo': pr1_otherrepo_snapshot},
            'base': {'label': f'{self.other_owner_login}:develop', 'ref': 'develop',
                     'sha': 'basesha0000000000000000000000000000000003',
                     'user': self.embedded_user_anotherowner, 'repo': pr1_otherrepo_snapshot},
            'body': 'Fixes a critical bug.', 'author_association': 'OWNER',
            'draft': False, 'merged': False, 'mergeable': True, 'rebaseable': True,
            'mergeable_state': 'clean', 'merged_by': None, 'comments': 0,
            'review_comments': 0, 'commits': 1, 'additions': 5, 'deletions': 5,
            'changed_files': 1, 'maintainer_can_modify': True  # Added maintainer_can_modify field
        }
        self.DB['PullRequests'] = [self.pr1_testrepo_data, self.pr2_testrepo_data, self.pr1_otherrepo_data]

        # Pull Request Files data
        self.file1_pr1 = {
            'sha': 'filesha0000000000000000000000000000000001', 'filename': 'src/main.py', 'status': 'modified',
            'additions': 10, 'deletions': 2, 'changes': 12, 'patch': '@@ -1,1 +1,10 @@ ...'
        }
        self.file2_pr1 = {
            'sha': 'filesha0000000000000000000000000000000002', 'filename': 'README.md', 'status': 'added',
            'additions': 5, 'deletions': 0, 'changes': 5, 'patch': '@@ -0,0 +1,5 @@ ...'
        }
        self.file_removed_pr1 = {
            'sha': 'filesha0000000000000000000000000000000003', 'filename': 'old_config.yml', 'status': 'removed',
            'additions': 0, 'deletions': 7, 'changes': 7, 'patch': '@@ -1,7 +0,0 @@ ...'
        }
        self.file_renamed_pr1 = {
            'sha': 'filesha0000000000000000000000000000000004', 'filename': 'utils/new_helper.py', 'status': 'renamed',
            'additions': 0, 'deletions': 0, 'changes': 0, 'patch': None
        }
        self.file_no_patch_pr1 = {
            'sha': 'filesha0000000000000000000000000000000005', 'filename': 'assets/logo.png', 'status': 'added',
            'additions': 1, 'deletions': 0, 'changes': 1, 'patch': None
        }

        self.pr1_files_entry = {
            'repo_full_name': self.repo_full_name,
            'pull_request_number': self.pr1_testrepo_data['number'],
            'files': [self.file1_pr1, self.file2_pr1]
        }
        self.pr2_files_entry_empty = {
            'repo_full_name': self.repo_full_name,
            'pull_request_number': self.pr2_testrepo_data['number'],
            'files': []
        }
        self.pr1_otherrepo_files_entry = {
            'repo_full_name': self.other_repo_full_name,
            'pull_request_number': self.pr1_otherrepo_data['number'],
            'files': [{'sha': 'othersha00000000000000000000000000000001', 'filename': 'index.js', 'status': 'modified',
                       'additions': 20, 'deletions': 5, 'changes': 25, 'patch': '...'}]
        }
        self.DB['PullRequestFilesCollection'] = [
            self.pr1_files_entry,
            self.pr2_files_entry_empty,
            self.pr1_otherrepo_files_entry
        ]

    def test_get_files_successfully(self):
        """Test retrieving files for a valid pull request using dynamic calculation."""
        # Clear the PullRequestFilesCollection to force dynamic calculation
        self.DB['PullRequestFilesCollection'] = []
        
        # Set up commits with actual file contents
        head_sha = self.pr1_testrepo_data['head']['sha']
        base_sha = self.pr1_testrepo_data['base']['sha']
        repo_id = self.repo_testrepo_data['id']
        
        # Add FileContents for both commits to simulate real file changes
        self.DB['FileContents'] = {
            f'{repo_id}:{base_sha}:file1.txt': {
                'type': 'file',
                'sha': 'base_file1_sha',
                'content': 'Original file1 content\n',
                'path': 'file1.txt',
                'name': 'file1.txt',
                'size': 22
            },
            f'{repo_id}:{base_sha}:file2.txt': {
                'type': 'file',
                'sha': 'base_file2_sha',
                'content': 'Original file2 content\n',
                'path': 'file2.txt',
                'name': 'file2.txt',
                'size': 22
            },
            # Head commit with modified files
            f'{repo_id}:{head_sha}:file1.txt': {
                'type': 'file',
                'sha': 'head_file1_sha',
                'content': 'Modified file1 content\n',
                'path': 'file1.txt',
                'name': 'file1.txt',
                'size': 23
            },
            f'{repo_id}:{head_sha}:file2.txt': {
                'type': 'file',
                'sha': 'head_file2_sha',
                'content': 'Modified file2 content\n',
                'path': 'file2.txt',
                'name': 'file2.txt',
                'size': 23
            }
        }
        
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1) # type: ignore
        self.assertEqual(len(files), 2)
        
        # Check that files have the expected structure and status
        file_names = {f['filename'] for f in files}
        self.assertEqual(file_names, {'file1.txt', 'file2.txt'})
        
        for file_data in files:
            self.assertEqual(file_data['status'], 'modified')
            self.assertIn('additions', file_data)
            self.assertIn('deletions', file_data)

    def test_get_files_for_pr_with_no_files_entry_in_collection(self):
        """Test PR exists but has no corresponding entry in PullRequestFilesCollection."""
        # Use PR #2 (ID 2) which exists, but remove its files entry from the collection
        self.DB['PullRequestFilesCollection'] = [
            self.pr1_files_entry, # Keep PR1's files
            self.pr1_otherrepo_files_entry # Keep other repo's PR files
        ] # PR2's files entry (pr2_files_entry_empty) is now missing

        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=2) # type: ignore
        self.assertEqual(files, [])

    def test_get_files_for_pr_with_empty_file_list(self):
        """Test retrieving files for a PR that has an empty list of files in its collection entry."""
        # PR #2 (ID 2) is set up with an empty files list via self.pr2_files_entry_empty
        # This entry is present in DB['PullRequestFilesCollection'] by default from setUp
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=2) # type: ignore
        self.assertEqual(files, [])

    def test_get_files_with_various_statuses_and_null_patch(self):
        """Test retrieving files with different statuses using dynamic calculation."""
        # Clear the PullRequestFilesCollection to force dynamic calculation
        self.DB['PullRequestFilesCollection'] = []
        
        # Set up commits with various file changes
        head_sha = self.pr1_testrepo_data['head']['sha']
        base_sha = self.pr1_testrepo_data['base']['sha']
        repo_id = self.repo_testrepo_data['id']
        
        # Add FileContents for various file operations
        self.DB['FileContents'] = {
            # Base commit files
            f'{repo_id}:{base_sha}:modified_file.txt': {
                'type': 'file',
                'sha': 'base_modified_sha',
                'content': 'Original content\n',
                'path': 'modified_file.txt',
                'name': 'modified_file.txt',
                'size': 17
            },
            f'{repo_id}:{base_sha}:removed_file.txt': {
                'type': 'file',
                'sha': 'removed_file_sha',
                'content': 'This file will be removed\n',
                'path': 'removed_file.txt',
                'name': 'removed_file.txt',
                'size': 26
            },
            f'{repo_id}:{base_sha}:old_name.txt': {
                'type': 'file',
                'sha': 'renamed_file_sha',
                'content': 'This file will be renamed\n',
                'path': 'old_name.txt',
                'name': 'old_name.txt',
                'size': 26
            },
            f'{repo_id}:{base_sha}:binary_file.jpg': {
                'type': 'file',
                'sha': 'binary_file_sha',
                'content': None,  # Binary file
                'path': 'binary_file.jpg',
                'name': 'binary_file.jpg',
                'size': 1024
            },
            # Head commit files
            f'{repo_id}:{head_sha}:modified_file.txt': {
                'type': 'file',
                'sha': 'head_modified_sha',
                'content': 'Modified content\n',
                'path': 'modified_file.txt',
                'name': 'modified_file.txt',
                'size': 17
            },
            f'{repo_id}:{head_sha}:added_file.txt': {
                'type': 'file',
                'sha': 'added_file_sha',
                'content': 'This is a new file\n',
                'path': 'added_file.txt',
                'name': 'added_file.txt',
                'size': 19
            },
            f'{repo_id}:{head_sha}:new_name.txt': {
                'type': 'file',
                'sha': 'renamed_file_sha',  # Same SHA as old_name.txt (renamed)
                'content': 'This file will be renamed\n',
                'path': 'new_name.txt',
                'name': 'new_name.txt',
                'size': 26
            },
            f'{repo_id}:{head_sha}:binary_file.jpg': {
                'type': 'file',
                'sha': 'binary_file_modified_sha',
                'content': None,  # Still binary but modified
                'path': 'binary_file.jpg',
                'name': 'binary_file.jpg',
                'size': 2048
            }
        }

        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1) # type: ignore
        self.assertEqual(len(files), 5)

        # Check different file statuses
        file_by_name = {f['filename']: f for f in files}
        
        # Modified file
        self.assertIn('modified_file.txt', file_by_name)
        self.assertEqual(file_by_name['modified_file.txt']['status'], 'modified')
        
        # Added file
        self.assertIn('added_file.txt', file_by_name)
        self.assertEqual(file_by_name['added_file.txt']['status'], 'added')
        
        # Removed file
        self.assertIn('removed_file.txt', file_by_name)
        self.assertEqual(file_by_name['removed_file.txt']['status'], 'removed')
        
        # Renamed file
        self.assertIn('new_name.txt', file_by_name)
        self.assertEqual(file_by_name['new_name.txt']['status'], 'renamed')
        self.assertEqual(file_by_name['new_name.txt']['previous_filename'], 'old_name.txt')
        
        # Binary file (should have null patch)
        self.assertIn('binary_file.jpg', file_by_name)
        self.assertEqual(file_by_name['binary_file.jpg']['status'], 'modified')
        self.assertIsNone(file_by_name['binary_file.jpg']['patch'])


    def test_repository_not_found_by_owner(self):
        """Test error when the repository owner does not exist."""
        self.assert_error_behavior(
            func_to_call=get_pull_request_files, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Repository 'nonexistent_owner/testrepo' not found.",
            owner="nonexistent_owner",
            repo=self.repo_name,
            pull_number=1
        )
    def test_repository_not_found_by_name(self):
        """Test error when the repository name does not exist for a valid owner."""
        self.assert_error_behavior(
            func_to_call=get_pull_request_files, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Repository 'testowner/nonexistent_repo' not found.",
            owner=self.owner_login,
            repo="nonexistent_repo",
            pull_number=1
        )

    def test_pull_request_not_found_in_repository(self):
        """Test error when the pull request number does not exist in the specified repository."""
        self.assert_error_behavior(
            func_to_call=get_pull_request_files, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Pull request #999 not found in repository 'testowner/testrepo'.",
            owner=self.owner_login,
            repo=self.repo_name,
            pull_number=999 # This PR number does not exist for testrepo
        )

    def test_pull_request_number_exists_but_for_different_repo(self):
        """Test error when PR number exists globally but not for the target repo."""
        # In setUp:
        # self.pr1_testrepo_data is PR #1 for testowner/testrepo
        # self.pr1_otherrepo_data is PR #1 for anotherowner/otherrepo
        # This test will try to get PR #1 from testowner/testrepo, but we'll change its number.

        original_pr1_testrepo_number = self.pr1_testrepo_data['number']

        # Find and modify the PR in DB directly
        for pr in self.DB['PullRequests']:
            if pr['id'] == self.pr1_testrepo_data['id']:
                pr['number'] = 10 # Change PR number for testrepo's PR to 10
                break

        # Now, testowner/testrepo has PRs #10 (ID 1) and #2 (ID 2).
        # anotherowner/otherrepo still has PR #1 (ID 3).
        # Query for PR #1 in testowner/testrepo. It should not be found.
        self.assert_error_behavior(
            func_to_call=get_pull_request_files, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Pull request #1 not found in repository 'testowner/testrepo'.",
            owner=self.owner_login,
            repo=self.repo_name,
            pull_number=1 # This PR number (1) no longer exists for testowner/testrepo
        )

        # Restore for other tests (though setUp re-initializes, good practice if tests could share state)
        for pr in self.DB['PullRequests']:
            if pr['id'] == self.pr1_testrepo_data['id']:
                pr['number'] = original_pr1_testrepo_number
                break

    
    def test_invalid_owner_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_files,
            expected_exception_type=ValidationError,
            expected_message="Parameter 'owner' must be a string.",
            owner=123, # Invalid type for owner
            repo=self.repo_name,
            pull_number=1
        )

    def test_invalid_repo_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_files,
            expected_exception_type=ValidationError,
            expected_message="Parameter 'repo' must be a string.",
            owner=self.owner_login, 
            repo=123, # Invalid type for repo
            pull_number=1
        )

    def test_invalid_pull_number_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_files,
            expected_exception_type=ValidationError,
            expected_message="Parameter 'pull_number' must be an integer.",
            owner=self.owner_login,
            repo=self.repo_name,
            pull_number="1" # Invalid type for pull_number (string)
        )

    def test_invalid_owner_empty_string(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_files,
            expected_exception_type=ValidationError,
            expected_message="Invalid input parameters.",
            owner="",
            repo=self.repo_name,
            pull_number=1
        )
    
    def test_invalid_repo_empty_string(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_files,
            expected_exception_type=ValidationError,
            expected_message="Invalid input parameters.",
            owner=self.owner_login,
            repo="",
            pull_number=1
        )
    
    def test_invalid_pull_number_zero(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_files,
            expected_exception_type=ValidationError,
            expected_message="Invalid input parameters.",
            owner=self.owner_login,
            repo=self.repo_name,
            pull_number=0
        )

    def test_invalid_pull_number_negative(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_files,
            expected_exception_type=ValidationError,
            expected_message="Invalid input parameters.",
            owner=self.owner_login,
            repo=self.repo_name,
            pull_number=-1
        )

    # NEW TESTS FOR DYNAMIC FILE DIFFERENCE CALCULATION
    
    def test_dynamic_file_calculation_with_file_changes(self):
        """Test dynamic file calculation when files are actually changed between commits."""
        # Clear the PullRequestFilesCollection to force dynamic calculation
        self.DB['PullRequestFilesCollection'] = []
        
        # Set up commits with actual file contents
        head_sha = self.pr1_testrepo_data['head']['sha']
        base_sha = self.pr1_testrepo_data['base']['sha']
        repo_id = self.repo_testrepo_data['id']
        
        # Add FileContents for base commit using correct dictionary format
        self.DB['FileContents'] = {
            f'{repo_id}:{base_sha}:README.md': {
                'type': 'file',
                'sha': 'base_readme_sha',
                'content': 'Initial README content\n',
                'path': 'README.md',
                'name': 'README.md',
                'size': 25
            },
            f'{repo_id}:{base_sha}:src/main.py': {
                'type': 'file',
                'sha': 'base_main_sha',
                'content': 'def main():\n    print("Hello World")\n',
                'path': 'src/main.py',
                'name': 'main.py',
                'size': 40
            },
            # Add FileContents for head commit (modified files)
            f'{repo_id}:{head_sha}:README.md': {
                'type': 'file',
                'sha': 'head_readme_sha',
                'content': 'Updated README content\nWith more details\n',
                'path': 'README.md',
                'name': 'README.md',
                'size': 45
            },
            f'{repo_id}:{head_sha}:src/main.py': {
                'type': 'file',
                'sha': 'head_main_sha',
                'content': 'def main():\n    print("Hello Updated World")\n    print("New feature added")\n',
                'path': 'src/main.py',
                'name': 'main.py',
                'size': 75
            },
            f'{repo_id}:{head_sha}:src/new_file.py': {
                'type': 'file',
                'sha': 'new_file_sha',
                'content': 'def new_function():\n    return "New file added"\n',
                'path': 'src/new_file.py',
                'name': 'new_file.py',
                'size': 50
            }
        }
        
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1)
        
        # Should return 3 files: 2 modified, 1 added
        self.assertEqual(len(files), 3)
        
        # Check file statuses
        file_statuses = {f['filename']: f['status'] for f in files}
        self.assertEqual(file_statuses['README.md'], 'modified')
        self.assertEqual(file_statuses['src/main.py'], 'modified')
        self.assertEqual(file_statuses['src/new_file.py'], 'added')
        
        # Check additions/deletions are calculated
        readme_file = next(f for f in files if f['filename'] == 'README.md')
        self.assertEqual(readme_file['additions'], 2)  # 2 new lines
        self.assertEqual(readme_file['deletions'], 1)  # 1 removed line
        self.assertEqual(readme_file['changes'], 3)     # total changes

    def test_dynamic_file_calculation_with_removed_files(self):
        """Test dynamic file calculation when files are removed."""
        # Clear the PullRequestFilesCollection to force dynamic calculation
        self.DB['PullRequestFilesCollection'] = []
        
        head_sha = self.pr1_testrepo_data['head']['sha']
        base_sha = self.pr1_testrepo_data['base']['sha']
        repo_id = self.repo_testrepo_data['id']
        
        # Base commit has files using correct dictionary format
        self.DB['FileContents'] = {
            f'{repo_id}:{base_sha}:old_file.txt': {
                'type': 'file',
                'sha': 'old_file_sha',
                'content': 'This file will be removed\n',
                'path': 'old_file.txt',
                'name': 'old_file.txt',
                'size': 26
            },
            f'{repo_id}:{base_sha}:kept_file.txt': {
                'type': 'file',
                'sha': 'kept_file_same_sha',
                'content': 'This file will be kept\n',
                'path': 'kept_file.txt',
                'name': 'kept_file.txt',
                'size': 24
            },
            # Head commit only has one file (other was removed)
            f'{repo_id}:{head_sha}:kept_file.txt': {
                'type': 'file',
                'sha': 'kept_file_same_sha',  # Same SHA means no change
                'content': 'This file will be kept\n',
                'path': 'kept_file.txt',
                'name': 'kept_file.txt',
                'size': 24
            }
        }
        
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1)
        
        # Should return 1 file: removed
        self.assertEqual(len(files), 1)
        
        removed_file = files[0]
        self.assertEqual(removed_file['filename'], 'old_file.txt')
        self.assertEqual(removed_file['status'], 'removed')
        self.assertEqual(removed_file['additions'], 0)
        self.assertEqual(removed_file['deletions'], 1)  # 1 line removed
        self.assertEqual(removed_file['changes'], 1)

    def test_dynamic_file_calculation_no_changes(self):
        """Test dynamic file calculation when no files are changed."""
        # Clear the PullRequestFilesCollection to force dynamic calculation
        self.DB['PullRequestFilesCollection'] = []
        
        head_sha = self.pr1_testrepo_data['head']['sha']
        base_sha = self.pr1_testrepo_data['base']['sha']
        repo_id = self.repo_testrepo_data['id']
        
        # Same files in both commits using correct dictionary format
        file_content = 'print("No changes here")\n'
        file_sha = 'unchanged_sha123'
        self.DB['FileContents'] = {
            f'{repo_id}:{base_sha}:unchanged.py': {
                'type': 'file',
                'sha': file_sha,
                'content': file_content,
                'path': 'unchanged.py',
                'name': 'unchanged.py',
                'size': 26
            },
            f'{repo_id}:{head_sha}:unchanged.py': {
                'type': 'file',
                'sha': file_sha,  # Same SHA indicates no change
                'content': file_content,
                'path': 'unchanged.py',
                'name': 'unchanged.py',
                'size': 26
            }
        }
        
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1)
        
        # Should return empty list when no files changed
        self.assertEqual(len(files), 0)

    def test_dynamic_file_calculation_missing_head_commit(self):
        """Test error handling when head commit is not found in database."""
        # Clear the PullRequestFilesCollection to force dynamic calculation
        self.DB['PullRequestFilesCollection'] = []
        
        # Don't add any FileContents for the head commit
        base_sha = self.pr1_testrepo_data['base']['sha']
        repo_id = self.repo_testrepo_data['id']
        
        self.DB['FileContents'] = {
            f'{repo_id}:{base_sha}:some_file.txt': {
                'type': 'file',
                'sha': 'base_file_sha',
                'content': 'Base content\n',
                'path': 'some_file.txt',
                'name': 'some_file.txt',
                'size': 13
            }
        }
        
        # Should still work, treating missing head commit as having no files
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1)
        
        # Should return 1 removed file
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['status'], 'removed')

    def test_dynamic_file_calculation_missing_base_commit(self):
        """Test error handling when base commit is not found in database."""
        # Clear the PullRequestFilesCollection to force dynamic calculation
        self.DB['PullRequestFilesCollection'] = []
        
        # Don't add any FileContents for the base commit
        head_sha = self.pr1_testrepo_data['head']['sha']
        repo_id = self.repo_testrepo_data['id']
        
        self.DB['FileContents'] = {
            f'{repo_id}:{head_sha}:new_file.txt': {
                'type': 'file',
                'sha': 'new_file_sha',
                'content': 'New content\n',
                'path': 'new_file.txt',
                'name': 'new_file.txt',
                'size': 12
            }
        }
        
        # Should still work, treating missing base commit as having no files
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1)
        
        # Should return 1 added file
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['status'], 'added')

    def test_dynamic_file_calculation_binary_files(self):
        """Test dynamic file calculation with binary files (no line counting)."""
        # Clear the PullRequestFilesCollection to force dynamic calculation
        self.DB['PullRequestFilesCollection'] = []
        
        head_sha = self.pr1_testrepo_data['head']['sha']
        base_sha = self.pr1_testrepo_data['base']['sha']
        repo_id = self.repo_testrepo_data['id']
        
        # Simulate binary file content (None indicates binary) using correct dictionary format
        self.DB['FileContents'] = {
            f'{repo_id}:{base_sha}:image.png': {
                'type': 'file',
                'sha': 'base_binary_sha',
                'content': None,  # Binary file
                'path': 'image.png',
                'name': 'image.png',
                'size': 1024
            },
            f'{repo_id}:{head_sha}:image.png': {
                'type': 'file',
                'sha': 'head_binary_sha',
                'content': None,  # Binary file (different binary content)
                'path': 'image.png',
                'name': 'image.png',
                'size': 2048
            }
        }
        
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1)
        
        # Should return 1 modified binary file
        self.assertEqual(len(files), 1)
        
        binary_file = files[0]
        self.assertEqual(binary_file['filename'], 'image.png')
        self.assertEqual(binary_file['status'], 'modified')
        # Binary files should have 0 additions/deletions
        self.assertEqual(binary_file['additions'], 0)
        self.assertEqual(binary_file['deletions'], 0)
        self.assertEqual(binary_file['changes'], 0)

    def test_dynamic_file_calculation_no_commit_data(self):
        """Test real-world behavior when no commit file data is available."""
        # Don't add any FileContents for commits (real-world: commits not found)
        self.DB['FileContents'] = {}
        
        # Real-world behavior: should return empty list when no commit data available
        files = get_pull_request_files(owner=self.owner_login, repo=self.repo_name, pull_number=1)
        
        # Should return empty list (no file data available)
        self.assertEqual(len(files), 0)
class TestMergePullRequest(BaseTestCaseWithErrorHandler):

    @classmethod
    def setUpClass(cls):
        # Save original DB state before any tests run
        cls.original_db_state = copy.deepcopy(DB)

    @classmethod
    def tearDownClass(cls):
        # Restore original DB state after all tests complete
        DB.clear()
        DB.update(copy.deepcopy(cls.original_db_state))

    def setUp(self):
        self.DB = DB # DB is globally available

        # Clear DB and set up fresh test data for each test
        self.DB.clear()

        self.owner_login = "testowner"
        self.repo_name = "testrepo"
        self.repo_full_name = f"{self.owner_login}/{self.repo_name}"

        self.user_id = 1
        self.acting_user_id = self.user_id # Assume this user performs actions

        self.repo_id = 101
        self.pull_number = 1
        self.pr_id = 1001 # Internal ID for the PR object

        self.base_branch_name = "main"
        self.head_branch_name = "feature"

        self.initial_base_sha = "base000000000000000000000000000000000000"
        self.initial_head_sha = "head000000000000000000000000000000000000"
        self.updated_head_sha = "head111111111111111111111111111111111111" 

        self.test_user_data = {
            "id": self.user_id, "login": self.owner_login, "node_id": "user_node_1",
            "type": "User", "site_admin": False, "name": "Test User", "email": "test@example.com",
            "company": None, "location": None, "bio": None, "public_repos": 1,
            "public_gists": 0, "followers": 0, "following": 0,
            "created_at": self._now(), "updated_at": self._now()
        }
        self.DB['Users'] = [copy.deepcopy(self.test_user_data)]

        # Add current user to the DB (same as the test user for most tests)
        self.DB['CurrentUser'] = copy.deepcopy(self.test_user_data)

        self.test_repo_owner_baseuser = {
            "id": self.user_id, "login": self.owner_login, "node_id": "user_node_1",
            "type": "User", "site_admin": False
        }

        self.test_repo_data = {
            "id": self.repo_id, "node_id": "repo_node_101", "name": self.repo_name,
            "full_name": self.repo_full_name, "private": False,
            "owner": copy.deepcopy(self.test_repo_owner_baseuser),
            "description": "A test repository", "fork": False,
            "created_at": self._now(), "updated_at": self._now(), "pushed_at": self._now(),
            "size": 1024, "stargazers_count": 0, "watchers_count": 0, "language": "Python",
            "has_issues": True, "has_projects": True, "has_downloads": True, "has_wiki": True,
            "has_pages": False, "forks_count": 0, "archived": False, "disabled": False,
            "open_issues_count": 0, "license": None, "allow_forking": True,
            "is_template": False, "web_commit_signoff_required": False, "topics": [],
            "visibility": "public", "default_branch": self.base_branch_name,
            "forks": 0, "open_issues": 0, "watchers": 0
        }
        self.DB['Repositories'] = [copy.deepcopy(self.test_repo_data)]

        self.DB['RepositoryCollaborators'] = [
            {"repository_id": self.repo_id, "user_id": self.acting_user_id, "permission": "admin"}
        ]

        self.DB['Branches'] = [
            self._create_branch_data(self.base_branch_name, self.initial_base_sha),
            self._create_branch_data(self.head_branch_name, self.initial_head_sha),
        ]

        self.DB['Commits'] = [
            self._create_commit_data(self.initial_base_sha, "Initial base commit", self.user_id),
            self._create_commit_data(self.initial_head_sha, "Initial head commit", self.user_id),
            self._create_commit_data(self.updated_head_sha, "Updated head commit", self.user_id),
        ]

        self.DB['PullRequests'] = [self._create_default_pr_data()]

        self.DB['CommitCombinedStatuses'] = [
            self._create_commit_status_data(self.initial_head_sha, "success", 1)
        ]

        # Save a snapshot of the initial test DB state
        self.initial_test_db_state = {}
        for key in self.DB:
            self.initial_test_db_state[key] = copy.deepcopy(self.DB[key])

    def tearDown(self):
        # Reset DB to initial test state after each test
        self.DB.clear()
        for key in self.initial_test_db_state:
            self.DB[key] = copy.deepcopy(self.initial_test_db_state[key])

    def _now(self):
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _is_valid_sha(self, sha_string):
        return isinstance(sha_string, str) and bool(re.match(r"^[a-f0-9]{40}$", sha_string))

    def _create_branch_data(self, name, sha):
        return {"name": name, "commit": {"sha": sha}, "protected": False, "repository_id": self.repo_id}

    def _create_commit_data(self, sha, message, user_id_for_commit, parents=None):
        user = next((u for u in self.DB['Users'] if u['id'] == user_id_for_commit), self.DB['Users'][0])

        author_committer_baseuser = {
            "id": user['id'], "login": user['login'], "node_id": user['node_id'], 
            "type": user['type'], "site_admin": user['site_admin']
        }
        git_actor = {"name": user.get('name', user['login']), "email": user.get('email', 'placeholder@example.com'), "date": self._now()}

        return {
            "sha": sha, "node_id": f"commit_node_{sha}", "repository_id": self.repo_id,
            "commit": {"author": git_actor, "committer": git_actor, "message": message, "tree": {"sha": "tree" + sha[:36]}},
            "author": author_committer_baseuser, "committer": author_committer_baseuser, 
            "parents": parents if parents else [],
            "stats": {"total": 0, "additions": 0, "deletions": 0}, "files": []
        }

    def _create_default_pr_data(self, **overrides):
        pr_user = copy.deepcopy(self.test_repo_owner_baseuser)
        # According to PullRequestBranchInfo, repo is a full Repository model
        pr_repo_details = copy.deepcopy(self.test_repo_data) 

        pr_data = {
            "id": self.pr_id, "node_id": f"pr_node_{self.pr_id}", "number": self.pull_number,
            "title": "Test Pull Request", "user": pr_user,
            "labels": [], "state": "open", "locked": False, "assignee": None, "assignees": [],
            "milestone": None, "created_at": self._now(), "updated_at": self._now(),
            "closed_at": None, "merged_at": None, "body": "Test PR body",
            "author_association": "OWNER", "draft": False, "merged": False,
            "mergeable": True, "rebaseable": True, "mergeable_state": "clean",
            "merged_by": None, "comments": 0, "review_comments": 0,
            "commits": 1, "additions": 10, "deletions": 2, "changed_files": 1,
            "head": {
                "label": f"{self.owner_login}:{self.head_branch_name}", "ref": self.head_branch_name,
                "sha": self.initial_head_sha, "user": pr_user, "repo": pr_repo_details
            },
            "base": {
                "label": f"{self.owner_login}:{self.base_branch_name}", "ref": self.base_branch_name,
                "sha": self.initial_base_sha, "user": pr_user, "repo": pr_repo_details
            }
        }
        pr_data.update(overrides)
        return pr_data

    def _create_commit_status_data(self, sha, state, total_count, context="ci/tests"):
        status_item = {
            "context": context, "state": state, 
            "description": f"Checks {state}", "created_at": self._now(), "updated_at": self._now()
        }
        return {
            "sha": sha, "repository_id": self.repo_id, "state": state, "total_count": total_count,
            "statuses": [status_item] if total_count > 0 else []
        }

    def _update_pr_in_db(self, pull_number_to_update, updates):
        for i, pr in enumerate(self.DB['PullRequests']):
            if pr['number'] == pull_number_to_update and pr['head']['repo']['id'] == self.repo_id : # Ensure it's the correct repo's PR
                self.DB['PullRequests'][i].update(updates)
                return self.DB['PullRequests'][i]
        raise ValueError(f"PR with number {pull_number_to_update} not found for update in repo {self.repo_id}.")

    def _get_pr_from_db(self, pull_number_to_get):
        for pr in self.DB['PullRequests']:
            if pr['number'] == pull_number_to_get and pr['head']['repo']['id'] == self.repo_id:
                return pr
        return None

    def _get_commit_from_db(self, commit_sha):
        for commit in self.DB['Commits']:
            if commit['sha'] == commit_sha:
                return commit
        return None

    # --- Success Test Cases ---
    def test_merge_pull_request_success_default_method(self):
        response = merge_pull_request(self.owner_login, self.repo_name, self.pull_number)

        self.assertTrue(response['merged'])
        self.assertTrue(self._is_valid_sha(response['sha']))
        self.assertIn("successfully merged", response['message'].lower())

        updated_pr = self._get_pr_from_db(self.pull_number)
        self.assertTrue(updated_pr['merged'])
        self.assertEqual(updated_pr['state'], 'closed')
        self.assertIsNotNone(updated_pr['merged_at'])
        self.assertIsNotNone(updated_pr['merged_by'])
        self.assertEqual(updated_pr['merged_by']['id'], self.acting_user_id)

        merge_commit = self._get_commit_from_db(response['sha'])
        self.assertIsNotNone(merge_commit)
        self.assertEqual(merge_commit['repository_id'], self.repo_id)

        expected_title_part = f"Merge pull request #{self.pull_number} from {self.head_branch_name}"
        self.assertIn(expected_title_part, merge_commit['commit']['message'])

    def test_merge_pull_request_success_with_commit_title_message(self):
        custom_title = "Custom Merge Title for PR"
        custom_message = "Detailed custom body for this merge."
        response = merge_pull_request(
            self.owner_login, self.repo_name, self.pull_number,
            commit_title=custom_title, commit_message=custom_message
        )

        self.assertTrue(response['merged'])
        self.assertTrue(self._is_valid_sha(response['sha']))

        merge_commit = self._get_commit_from_db(response['sha'])
        self.assertIsNotNone(merge_commit)
        self.assertIn(custom_title, merge_commit['commit']['message'])
        self.assertIn(custom_message, merge_commit['commit']['message'])

    def test_merge_pull_request_success_merge_method_squash(self):
        response = merge_pull_request(self.owner_login, self.repo_name, self.pull_number, merge_method="squash")
        self.assertTrue(response['merged'])
        self.assertTrue(self._is_valid_sha(response['sha']))
        self.assertIn("successfully merged", response['message'].lower())

        updated_pr = self._get_pr_from_db(self.pull_number)
        self.assertTrue(updated_pr['merged'])
        self.assertEqual(updated_pr['state'], 'closed')

        merge_commit = self._get_commit_from_db(response['sha'])
        self.assertIsNotNone(merge_commit)

    def test_merge_pull_request_success_merge_method_rebase(self):
        response = merge_pull_request(self.owner_login, self.repo_name, self.pull_number, merge_method="rebase")
        self.assertTrue(response['merged'])
        self.assertTrue(self._is_valid_sha(response['sha'])) # SHA of the new base branch head
        self.assertIn("successfully merged", response['message'].lower())

        updated_pr = self._get_pr_from_db(self.pull_number)
        self.assertTrue(updated_pr['merged'])
        self.assertEqual(updated_pr['state'], 'closed')

    # --- NotFoundError Test Cases ---
    def test_merge_pull_request_error_repo_not_found(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=NotFoundError,
            expected_message="Repository 'testowner/nonexistent-repo-name' not found.",
            owner=self.owner_login, repo="nonexistent-repo-name", pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_not_found(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=NotFoundError,
            expected_message="Pull request #9999 not found in 'testowner/testrepo'.",
            owner=self.owner_login, repo=self.repo_name, pull_number=9999
        )

    # --- MethodNotAllowedError Test Cases ---
    def test_merge_pull_request_error_pr_not_mergeable_dirty_state(self):
        self._update_pr_in_db(self.pull_number, {"mergeable": False, "mergeable_state": "dirty"})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull request cannot be merged due to conflicts. Please resolve conflicts.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_not_mergeable_blocked_by_policy(self):
        self._update_pr_in_db(self.pull_number, {"mergeable": False, "mergeable_state": "blocked"})
        self.DB['CommitCombinedStatuses'] = [ # Ensure checks are passing to isolate 'blocked' reason
            self._create_commit_status_data(self.initial_head_sha, "success", 1)
        ]
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull request cannot be merged: status checks are pending or failed, or required reviews are missing.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_checks_pending(self):
        self.DB['CommitCombinedStatuses'] = [
            self._create_commit_status_data(self.initial_head_sha, "pending", 1)
        ]
        # PR might still be 'mergeable: True' but 'mergeable_state: unstable' or 'blocked'
        self._update_pr_in_db(self.pull_number, {"mergeable_state": "blocked"}) # Or 'unstable'
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull request merge is blocked by status checks or required reviews (inconsistent state: mergeable is True but state is 'blocked').",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_checks_failed(self):
        self.DB['CommitCombinedStatuses'] = [
            self._create_commit_status_data(self.initial_head_sha, "failure", 1)
        ]
        self._update_pr_in_db(self.pull_number, {"mergeable": False, "mergeable_state": "blocked"})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull request cannot be merged: status checks are pending or failed, or required reviews are missing.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_is_draft(self):
        self._update_pr_in_db(self.pull_number, {"draft": True, "mergeable_state": "draft"})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Draft pull requests cannot be merged.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_already_merged(self):
        self._update_pr_in_db(self.pull_number, {"merged": True, "merged_at": self._now(), "state": "closed"})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull Request is not open.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_closed_not_merged(self):
        self._update_pr_in_db(self.pull_number, {"state": "closed", "merged": False, "closed_at": self._now()})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull Request is not open.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    # --- ConflictError Test Cases ---
    def test_merge_pull_request_error_head_commit_changed(self):
        # Original PR head is self.initial_head_sha
        # Simulate that the actual head branch moved to self.updated_head_sha
        self.DB['Branches'] = [
            self._create_branch_data(self.base_branch_name, self.initial_base_sha),
            self._create_branch_data(self.head_branch_name, self.updated_head_sha), 
        ]
        # Ensure PR itself is otherwise mergeable based on its own data
        self._update_pr_in_db(self.pull_number, {"mergeable": True, "mergeable_state": "clean"})
        self.DB['CommitCombinedStatuses'] = [ # Status for the PR's recorded head SHA
             self._create_commit_status_data(self.initial_head_sha, "success", 1)
        ]

        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ConflictError,
            expected_message="The pull request head branch (feature) has been modified since this pull request was created. Please review recent changes.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    # --- ValidationError Test Cases ---
    def test_merge_pull_request_error_invalid_owner_type(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ValidationError,
            expected_message="Owner must be a string, got int",
            owner=12345, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_empty_owner(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ValidationError,
            expected_message="Owner cannot be empty.",
            owner="", repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_empty_repo(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ValidationError,
            expected_message="Repository name cannot be empty.",
            owner=self.owner_login, repo="", pull_number=self.pull_number
        )

    def test_merge_pull_request_error_invalid_repo_type(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ValidationError,
            expected_message="Repository name must be a string, got int",
            owner=self.owner_login, repo=67890, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_invalid_pull_number_type(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ValidationError,
            expected_message="Pull request number must be an integer, got str",
            owner=self.owner_login, repo=self.repo_name, pull_number="not-a-number"
        )

    def test_merge_pull_request_error_invalid_pull_number_value_zero(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ValidationError,
            expected_message="Pull request number must be positive, got 0",
            owner=self.owner_login, repo=self.repo_name, pull_number=0
        )

    def test_merge_pull_request_error_invalid_pull_number_value_negative(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ValidationError,
            expected_message="Pull request number must be positive, got -5",
            owner=self.owner_login, repo=self.repo_name, pull_number=-5
        )

    def test_merge_pull_request_error_invalid_merge_method(self):
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ValidationError,
            expected_message="Invalid merge method 'non_existent_merge_strategy'. Allowed methods are: merge, squash, rebase.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number,
            merge_method="non_existent_merge_strategy"
        )

    # --- ForbiddenError Test Cases ---
    def test_merge_pull_request_error_no_permission_to_merge(self):
        # Create a new user with read-only permissions
        read_only_user = {
            "id": 999, "login": "readonly_user", "node_id": "user_node_999",
            "type": "User", "site_admin": False, "name": "Read Only User", "email": "readonly@example.com"
        }

        # Add the user to DB and set as current user
        self.DB['Users'].append(copy.deepcopy(read_only_user))
        self.DB['CurrentUser'] = copy.deepcopy(read_only_user)

        # Add read-only permission for this user
        self.DB['RepositoryCollaborators'].append({
            "repository_id": self.repo_id, 
            "user_id": read_only_user["id"], 
            "permission": "read"
        })

        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=ForbiddenError,
            expected_message="You do not have permission to merge pull requests in this repository.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    # Additional test cases to improve code coverage
    def test_merge_pull_request_error_pr_has_unknown_mergeability(self):
        # Set mergeable to None to test unknown mergeability status
        self._update_pr_in_db(self.pull_number, {"mergeable": None})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Mergeability status is unknown. Please try again later.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_behind_base_branch(self):
        # Test PR with merged=false and mergeable_state='behind'
        self._update_pr_in_db(self.pull_number, {"mergeable": False, "mergeable_state": "behind"})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull request cannot be merged: head branch is behind the base branch. Please update your branch.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_unknown_unmergeability_reason(self):
        # Test PR with merged=false and a non-standard mergeable_state
        self._update_pr_in_db(self.pull_number, {"mergeable": False, "mergeable_state": "unknown_reason"})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull request is not mergeable. Reason: unknown_reason.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_inconsistent_state_mergeable_but_dirty(self):
        # Test PR with inconsistent state: mergeable=true but dirty state
        self._update_pr_in_db(self.pull_number, {"mergeable": True, "mergeable_state": "dirty"})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull request cannot be merged due to conflicts (inconsistent state: mergeable is True but state is 'dirty').",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )

    def test_merge_pull_request_error_pr_already_merged_explicit_check(self):
        # Test trying to merge a PR that's marked as merged but not closed 
        # (different from test_merge_pull_request_error_pr_already_merged which sets both merged and closed state)
        self._update_pr_in_db(self.pull_number, {"merged": True, "merged_at": self._now()})
        self.assert_error_behavior(
            func_to_call=merge_pull_request,
            expected_exception_type=MethodNotAllowedError,
            expected_message="Pull request is already merged.",
            owner=self.owner_login, repo=self.repo_name, pull_number=self.pull_number
        )
class TestGetPullRequestStatus(BaseTestCaseWithErrorHandler): # type: ignore
    """
    Test suite for the get_pull_request_status function.
    """
    def setUp(self):
        """
        Initializes self.DB and populates it with common data.
        """
        self.DB = DB # type: ignore
        self.DB.clear()

        self.owner_login = "testowner"
        self.repo_name = "testrepo"
        self.repo_full_name = f"{self.owner_login}/{self.repo_name}"
        self.repo_id = 101
        self.user_id = 1

        self.created_at = datetime(2023, 1, 1, 0, 0, 0)
        self.updated_at = datetime(2023, 1, 1, 0, 0, 0)
        self.pushed_at = datetime(2023, 1, 1, 0, 0, 0)

        self.DB['Users'] = [
            {'id': self.user_id, 'login': self.owner_login, 'node_id': 'user_node_1', 'type': 'User', 'site_admin': False}
        ]
        self.DB['Repositories'] = [
            {
                'id': self.repo_id,
                'node_id': 'repo_node_1',
                'name': self.repo_name,
                'full_name': self.repo_full_name,
                'private': False,
                'owner': {'id': self.user_id, 'login': self.owner_login, 'node_id': 'user_node_1', 'type': 'User', 'site_admin': False},
                'description': 'A test repository',
                'fork': False,
                'created_at': self.created_at,
                'updated_at': self.updated_at,
                'pushed_at': self.pushed_at,
                'size': 1024,
                'stargazers_count': 10,
                'watchers_count': 10,
                'language': 'Python',
                'has_issues': True,
                'has_projects': True,
                'has_downloads': True,
                'has_wiki': True,
                'has_pages': False,
                'forks_count': 1,
                'archived': False,
                'disabled': False,
                'open_issues_count': 5,
                'default_branch': 'main',
            }
        ]
        self.DB['PullRequests'] = []
        self.DB['CommitCombinedStatuses'] = []

    def _create_repo_dict_for_pr(self, repo_id, repo_name, repo_full_name, owner_id, owner_login):
        """Helper to create the nested repo dict for PR head/base."""
        return {
            'id': repo_id,
            'node_id': f'repo_node_{repo_id}',
            'name': repo_name,
            'full_name': repo_full_name,
            'private': False,
            'owner': {'id': owner_id, 'login': owner_login, 'node_id': f'user_node_{owner_id}', 'type': 'User', 'site_admin': False},
            'description': 'A repository',
            'fork': False,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'pushed_at': self.pushed_at,
            'size': 1024,
            'stargazers_count': 0,
            'watchers_count': 0,
            'language': None,
            'has_issues': True,
            'has_projects': True,
            'has_downloads': True,
            'has_wiki': True,
            'has_pages': False,
            'forks_count': 0,
            'archived': False,
            'disabled': False,
            'open_issues_count': 0,
            'default_branch': 'main',
        }


    def _add_pull_request(self, pr_number: int, head_sha: str, pr_id: Optional[int] = None,
                          target_repo_id: Optional[int] = None,
                          target_repo_name: Optional[str] = None,
                          target_repo_full_name: Optional[str] = None,
                          target_owner_id: Optional[int] = None,
                          target_owner_login: Optional[str] = None):
        if pr_id is None:
            pr_id = pr_number

        _repo_id = target_repo_id if target_repo_id is not None else self.repo_id
        _repo_name = target_repo_name if target_repo_name is not None else self.repo_name
        _repo_full_name = target_repo_full_name if target_repo_full_name is not None else self.repo_full_name
        _owner_id = target_owner_id if target_owner_id is not None else self.user_id
        _owner_login = target_owner_login if target_owner_login is not None else self.owner_login

        repo_for_pr_branch = self._create_repo_dict_for_pr(_repo_id, _repo_name, _repo_full_name, _owner_id, _owner_login)

        # Fix SHA format to match 40-character hexadecimal pattern
        base_sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

        pr_data = {
            'id': pr_id,
            'node_id': f'pr_node_{pr_id}',
            'repository_id': _repo_id,  # Added this field to match model
            'number': pr_number,
            'title': f'Test PR {pr_number}',
            'user': {'id': _owner_id, 'login': _owner_login, 'node_id': f'user_node_{_owner_id}', 'type': 'User', 'site_admin': False},
            'labels': [],  # Added default empty list for labels
            'state': 'open',
            'locked': False,
            'assignees': [],   # Added default empty list for assignees
            'comments': 0,     # Added default comments count
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'author_association': 'OWNER',
            'head': {
                'label': f'{_owner_login}:feature-pr-{pr_number}',
                'ref': f'feature-pr-{pr_number}',
                'sha': head_sha,  # Use the exact SHA that was passed in
                'user': {'id': _owner_id, 'login': _owner_login, 'node_id': f'user_node_{_owner_id}', 'type': 'User', 'site_admin': False},
                'repo': copy.deepcopy(repo_for_pr_branch)
            },
            'base': {
                'label': f'{_owner_login}:main',
                'ref': 'main',
                'sha': base_sha,  # Using fixed 40-character SHA
                'user': {'id': _owner_id, 'login': _owner_login, 'node_id': f'user_node_{_owner_id}', 'type': 'User', 'site_admin': False},
                'repo': copy.deepcopy(repo_for_pr_branch)
            }
        }
        self.DB['PullRequests'].append(pr_data)

    def _add_commit_status(self, sha: str, overall_state: str, total_count: int, statuses: List[Dict[str, Any]], repo_id_override: Optional[int] = None):
        # Use the SHA as is - this is what our implementation expects in order to match with PR
        valid_sha = sha

        # Normalize statuses: ensure required fields exist according to CommitStatusItem model
        normalized_statuses = []
        for s_in in statuses:
            s_out = s_in.copy()
            # Ensure required fields are present
            if 'context' not in s_out:
                s_out['context'] = 'default'
            if 'state' not in s_out:
                s_out['state'] = 'pending'
            if 'description' not in s_out:
                s_out['description'] = None
            if 'created_at' not in s_out:
                s_out['created_at'] = self.created_at
            if 'updated_at' not in s_out:
                s_out['updated_at'] = self.updated_at
            normalized_statuses.append(s_out)

        status_data = {
            'sha': valid_sha,
            'repository_id': repo_id_override if repo_id_override is not None else self.repo_id,
            'state': overall_state,
            'total_count': total_count,
            'statuses': normalized_statuses
        }
        self.DB['CommitCombinedStatuses'].append(status_data)

    def test_success_all_checks_pass(self):
        pr_number = 1
        head_sha = "sha_success_all_abcdef1234567890abcdef12"
        self._add_pull_request(pr_number, head_sha)
        statuses_detail = [
            {'state': 'success', 'context': 'ci/travis', 'description': 'Build passed'},
            {'state': 'success', 'context': 'lint', 'description': 'Linting passed'}
        ]
        self._add_commit_status(head_sha, 'success', 2, statuses_detail)

        result = get_pull_request_status(self.owner_login, self.repo_name, pr_number) # type: ignore

        expected = {
            'state': 'success',
            'sha': head_sha,
            'total_count': 2,
            'statuses': statuses_detail # Already normalized by _add_commit_status
        }
        self.assertEqual(result, expected)

    def test_failure_one_check_fails(self):
        pr_number = 2
        head_sha = "sha_failure_one_abcdef1234567890abcdef12"
        self._add_pull_request(pr_number, head_sha)
        statuses_detail = [
            {'state': 'success', 'context': 'ci/travis', 'description': 'Build passed'},
            {'state': 'failure', 'context': 'test/unit', 'description': 'Tests failed'}
        ]
        self._add_commit_status(head_sha, 'failure', 2, statuses_detail)

        result = get_pull_request_status(self.owner_login, self.repo_name, pr_number) # type: ignore
        expected = {
            'state': 'failure',
            'sha': head_sha,
            'total_count': 2,
            'statuses': statuses_detail
        }
        self.assertEqual(result, expected)

    def test_pending_one_check_pending(self):
        pr_number = 3
        head_sha = "sha_pending_one_abcdef1234567890abcdef12"
        self._add_pull_request(pr_number, head_sha)
        statuses_detail = [
            {'state': 'success', 'context': 'lint', 'description': 'Linting passed'},
            {'state': 'pending', 'context': 'ci/deploy', 'description': 'Deployment in progress'}
        ]
        self._add_commit_status(head_sha, 'pending', 2, statuses_detail)

        result = get_pull_request_status(self.owner_login, self.repo_name, pr_number) # type: ignore
        expected = {
            'state': 'pending',
            'sha': head_sha,
            'total_count': 2,
            'statuses': statuses_detail
        }
        self.assertEqual(result, expected)

    def test_error_one_check_error_and_missing_description(self):
        pr_number = 4
        head_sha = "sha_error_one_abcdef1234567890abcdef12"
        self._add_pull_request(pr_number, head_sha)

        db_statuses_detail_raw = [ # Simulating raw data from DB where a description might be missing
            {'state': 'success', 'context': 'lint'}, 
            {'state': 'error', 'context': 'ci/config', 'description': 'Configuration error'}
        ]
        self._add_commit_status(head_sha, 'error', 2, db_statuses_detail_raw)

        result = get_pull_request_status(self.owner_login, self.repo_name, pr_number) # type: ignore

        expected_processed_statuses = [ # Function should return normalized statuses
            {'state': 'success', 'context': 'lint', 'description': None},
            {'state': 'error', 'context': 'ci/config', 'description': 'Configuration error'}
        ]
        expected = {
            'state': 'error',
            'sha': head_sha,
            'total_count': 2,
            'statuses': expected_processed_statuses
        }
        self.assertEqual(result, expected)

    def test_no_status_checks_for_commit(self):
        pr_number = 5
        head_sha = "sha_no_checks_abcdef1234567890abcdef12"
        self._add_pull_request(pr_number, head_sha)
        self._add_commit_status(head_sha, 'success', 0, []) # Overall state from DB

        result = get_pull_request_status(self.owner_login, self.repo_name, pr_number) # type: ignore
        expected = {
            'state': 'success', 
            'sha': head_sha,
            'total_count': 0,
            'statuses': []
        }
        self.assertEqual(result, expected)

    def test_status_check_description_is_explicitly_none_in_db(self):
        pr_number = 6
        head_sha = "sha_desc_none_abcdef1234567890abcdef12"
        self._add_pull_request(pr_number, head_sha)
        statuses_detail_db = [
            {'state': 'success', 'context': 'ci/travis', 'description': None}, 
            {'state': 'success', 'context': 'lint', 'description': 'Linting passed'}
        ]
        self._add_commit_status(head_sha, 'success', 2, statuses_detail_db)

        result = get_pull_request_status(self.owner_login, self.repo_name, pr_number) # type: ignore
        expected = {
            'state': 'success',
            'sha': head_sha,
            'total_count': 2,
            'statuses': statuses_detail_db 
        }
        self.assertEqual(result, expected)

    # --- Validation Error Tests ---
    def test_validation_error_invalid_owner_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=ValidationError, # type: ignore
            expected_message="Owner must be a non-empty string.",
            owner=123, repo=self.repo_name, pull_number=1
        )

    def test_validation_error_empty_owner(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=ValidationError, # type: ignore
            expected_message="Owner must be a non-empty string.",
            owner="", repo=self.repo_name, pull_number=1
        )

    def test_validation_error_invalid_repo_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=ValidationError, # type: ignore
            expected_message="Repo must be a non-empty string.",
            owner=self.owner_login, repo=123, pull_number=1
        )

    def test_validation_error_empty_repo(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=ValidationError, # type: ignore
            expected_message="Repo must be a non-empty string.",
            owner=self.owner_login, repo="", pull_number=1
        )

    def test_validation_error_invalid_pull_number_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=ValidationError, # type: ignore
            expected_message="Pull number must be a positive integer.",
            owner=self.owner_login, repo=self.repo_name, pull_number="abc"
        )

    def test_validation_error_invalid_pull_number_value_zero(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=ValidationError, # type: ignore
            expected_message="Pull number must be a positive integer.",
            owner=self.owner_login, repo=self.repo_name, pull_number=0
        )

    def test_validation_error_invalid_pull_number_value_negative(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=ValidationError, # type: ignore
            expected_message="Pull number must be a positive integer.",
            owner=self.owner_login, repo=self.repo_name, pull_number=-1
        )

    # --- NotFoundError Tests ---
    def test_not_found_error_repo_not_exist(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Repository 'testowner/nonexistent_repo' not found.",
            owner=self.owner_login, repo="nonexistent_repo", pull_number=1
        )

    def test_not_found_error_owner_not_exist_for_repo(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Repository 'bogusowner/testrepo' not found.",
            owner="bogusowner", repo=self.repo_name, pull_number=1
        )

    def test_not_found_error_pull_request_not_exist(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Pull request #999 not found in repository 'testowner/testrepo'.",
            owner=self.owner_login, repo=self.repo_name, pull_number=999
        )

    def test_not_found_error_pr_exists_but_for_different_repo(self):
        other_owner_login = "otherowner"
        other_repo_id = 102
        other_repo_name = "otherrepo"
        other_repo_full_name = f"{other_owner_login}/{other_repo_name}"
        other_user_id = 2

        self.DB['Users'].append({'id': other_user_id, 'login': other_owner_login, 'node_id': 'user_node_2', 'type': 'User', 'site_admin': False})
        self.DB['Repositories'].append(
             self._create_repo_dict_for_pr(other_repo_id, other_repo_name, other_repo_full_name, other_user_id, other_owner_login)
        )

        pr_number_for_other_repo = 10
        head_sha_other_repo_pr = "sha_other_repo_pr_abcdef1234567890abcd"

        self._add_pull_request(
            pr_number=pr_number_for_other_repo, 
            head_sha=head_sha_other_repo_pr,
            pr_id=pr_number_for_other_repo,
            target_repo_id=other_repo_id,
            target_repo_name=other_repo_name,
            target_repo_full_name=other_repo_full_name,
            target_owner_id=other_user_id,
            target_owner_login=other_owner_login
        )
        self._add_commit_status(head_sha_other_repo_pr, 'success', 0, [], repo_id_override=other_repo_id)

        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Pull request #10 not found in repository 'testowner/testrepo'.",
            owner=self.owner_login, repo=self.repo_name, pull_number=pr_number_for_other_repo
        )

    def test_not_found_error_commit_status_not_exist_for_pr_head_sha(self):
        pr_number = 7
        head_sha_no_status_entry = "sha_pr_nostatus_abcdef1234567890abcdef"
        self._add_pull_request(pr_number, head_sha_no_status_entry)
        # No entry in CommitCombinedStatuses for head_sha_no_status_entry

        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Combined status for commit SHA 'sha_pr_nostatus_abcdef1234567890abcdef' (head of PR #7) not found in repository 'testowner/testrepo'.",
            owner=self.owner_login, repo=self.repo_name, pull_number=pr_number
        )

    def test_not_found_error_commit_status_exists_but_for_different_repo_id(self):
        pr_number = 8
        head_sha = "sha_status_wrong_repo_abcdef1234567890"
        self._add_pull_request(pr_number, head_sha)

        different_repo_id = 999 
        self._add_commit_status(
            head_sha, 'success', 1, 
            [{'state': 'success', 'context': 'test', 'description': 'Pass'}],
            repo_id_override=different_repo_id
        )

        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Combined status for commit SHA 'sha_status_wrong_repo_abcdef1234567890' (head of PR #8) not found in repository 'testowner/testrepo'.",
            owner=self.owner_login, repo=self.repo_name, pull_number=pr_number
        )
        
    # Additional tests to improve code coverage
    def test_repo_with_missing_id(self):
        # Setup a repository without an ID
        repo_without_id = {
            'name': 'broken-repo',
            'full_name': 'testowner/broken-repo',
            'owner': {'id': self.user_id, 'login': self.owner_login}
            # No 'id' field
        }
        original_repos = self.DB['Repositories'].copy()
        self.DB['Repositories'] = [repo_without_id]
        
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Repository 'testowner/broken-repo' found but lacks an ID. Data inconsistency.",
            owner=self.owner_login, repo='broken-repo', pull_number=1
        )
        
        # Restore original repositories
        self.DB['Repositories'] = original_repos
    def test_pr_matched_via_head_repo_identifier(self):
        # Create a PR that will be matched via its head repo ID, not directly by repository_id
        pr_number = 20
        head_sha = "sha_head_repo_match_abcdef1234567890"
        
        # Create PR without repository_id field but with proper head repo reference
        pr_via_head = {
            'id': 2000,
            'node_id': 'pr_node_2000',
            # No 'repository_id' field
            'number': pr_number,
            'title': f'Test PR {pr_number}',
            'user': {'id': self.user_id, 'login': self.owner_login, 'node_id': f'user_node_{self.user_id}', 'type': 'User', 'site_admin': False},
            'labels': [],
            'state': 'open',
            'locked': False,
            'assignees': [],
            'comments': 0,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'author_association': 'OWNER',
            'head': {
                'label': f'{self.owner_login}:feature-pr-{pr_number}',
                'ref': f'feature-pr-{pr_number}',
                'sha': head_sha,
                'user': {'id': self.user_id, 'login': self.owner_login, 'node_id': f'user_node_{self.user_id}', 'type': 'User', 'site_admin': False},
                'repo': self._create_repo_dict_for_pr(
                    self.repo_id, self.repo_name, self.repo_full_name, 
                    self.user_id, self.owner_login
                )
            },
            'base': {
                'label': f'{self.owner_login}:main',
                'ref': 'main',
                'sha': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                'user': {'id': self.user_id, 'login': self.owner_login, 'node_id': f'user_node_{self.user_id}', 'type': 'User', 'site_admin': False},
                'repo': self._create_repo_dict_for_pr(
                    self.repo_id, self.repo_name, self.repo_full_name, 
                    self.user_id, self.owner_login
                )
            }
        }
        
        self.DB['PullRequests'].append(pr_via_head)
        self._add_commit_status(head_sha, 'success', 1, [{'state': 'success', 'context': 'test'}])
        
        result = get_pull_request_status(self.owner_login, self.repo_name, pr_number) # type: ignore
        
        expected = {
            'state': 'success',
            'sha': head_sha,
            'total_count': 1,
            'statuses': [{'state': 'success', 'context': 'test', 'description': None}]
        }
        self.assertEqual(result, expected)
        
    def test_pr_missing_head_sha(self):
        # Create a PR without head SHA to test that error path
        pr_number = 21
        
        # Create a PR with missing head SHA
        pr_missing_sha = {
            'id': 2100,
            'node_id': 'pr_node_2100',
            'repository_id': self.repo_id,
            'number': pr_number,
            'title': f'PR Missing SHA {pr_number}',
            'user': {'id': self.user_id, 'login': self.owner_login, 'node_id': f'user_node_{self.user_id}', 'type': 'User', 'site_admin': False},
            'labels': [],
            'state': 'open',
            'locked': False,
            'assignees': [],
            'comments': 0,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'author_association': 'OWNER',
            'head': {
                'label': f'{self.owner_login}:feature-pr-{pr_number}',
                'ref': f'feature-pr-{pr_number}',
                # No 'sha' field
                'user': {'id': self.user_id, 'login': self.owner_login, 'node_id': f'user_node_{self.user_id}', 'type': 'User', 'site_admin': False},
                'repo': self._create_repo_dict_for_pr(
                    self.repo_id, self.repo_name, self.repo_full_name, 
                    self.user_id, self.owner_login
                )
            },
            'base': {
                'label': f'{self.owner_login}:main',
                'ref': 'main',
                'sha': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                'user': {'id': self.user_id, 'login': self.owner_login, 'node_id': f'user_node_{self.user_id}', 'type': 'User', 'site_admin': False},
                'repo': self._create_repo_dict_for_pr(
                    self.repo_id, self.repo_name, self.repo_full_name, 
                    self.user_id, self.owner_login
                )
            }
        }
        
        self.DB['PullRequests'].append(pr_missing_sha)
        
        # The correct usage of assert_error_behavior with the exact error message
        repo_full_name = f"{self.owner_login}/{self.repo_name}"
        expected_msg = f"Could not determine head SHA for pull request #{pr_number} in repository '{repo_full_name}'. This may indicate inconsistent PR data."
        self.assert_error_behavior(
            func_to_call=get_pull_request_status, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message=expected_msg,
            owner=self.owner_login, 
            repo=self.repo_name, 
            pull_number=pr_number
        )
        
    def test_skip_non_matching_pr_numbers(self):
        # Test that PRs with non-matching numbers are skipped
        # This test explicitly exercises the 'continue' line in the loop
        
        # Create several PRs with different numbers
        for i in range(30, 35):
            self._add_pull_request(pr_number=i, head_sha=f"sha_skip_test_{i}")
            
        # Add status for one specific PR
        target_pr = 33
        target_sha = f"sha_skip_test_{target_pr}"
        self._add_commit_status(target_sha, 'success', 1, [{'state': 'success', 'context': 'test'}])
        
        # Verify we can successfully get the status for the target PR
        result = get_pull_request_status(self.owner_login, self.repo_name, target_pr) # type: ignore
        
        expected = {
            'state': 'success',
            'sha': target_sha,
            'total_count': 1,
            'statuses': [{'state': 'success', 'context': 'test', 'description': None}]
        }
        self.assertEqual(result, expected)

class TestGetPullRequestReviews(BaseTestCaseWithErrorHandler): # type: ignore
    """
    Test suite for the get_pull_request_reviews function.
    """
    
    @classmethod
    def setUpClass(cls):
        # Deep copy the DB state to restore later after all tests
        cls.original_db = copy.deepcopy(DB)

    @classmethod
    def tearDownClass(cls):
        # Restore the DB to its original state
        DB.clear()
        DB.update(cls.original_db)

    def setUp(self):
        """
        Set up the test environment before each test.
        Initializes the mock DB and populates it with test data.
        """
        self.DB = DB # type: ignore
        self.DB.clear()

        # Define User data structures
        # BaseUser structure for repository owners, PR creators
        self.owner_user_data = {
            'id': 1, 'login': 'owner1', 'node_id': 'MDQ6VXNlcjE=',
            'type': 'User', 'site_admin': False
        }
        # UserSimple structure for reviewers
        self.reviewer1_user_data = {'id': 2, 'login': 'reviewer1'}
        self.reviewer2_user_data = {'id': 3, 'login': 'reviewer2'}

        # Populate DB['Users'] - required by utils like _prepare_user_sub_document
        self.DB['Users'] = [
            {
                **self.owner_user_data, 'name': 'Owner One', 'email': 'owner1@example.com', 
                'company': None, 'location': None, 'bio': None, 'public_repos': 2, 
                'public_gists': 0, 'followers': 10, 'following': 5, 
                'created_at': "2020-01-01T00:00:00Z", 'updated_at': "2020-01-01T00:00:00Z"
            },
            {
                'id': 2, 'login': 'reviewer1', 'node_id': 'MDQ6VXNlcjI=', 
                'type': 'User', 'site_admin': False, 'name': 'Reviewer One', 
                'email': 'reviewer1@example.com', 'company': None, 'location': None, 'bio': None, 
                'public_repos': 1, 'public_gists': 0, 'followers': 0, 'following': 0, 
                'created_at': "2020-01-01T00:00:00Z", 'updated_at': "2020-01-01T00:00:00Z"
            },
            {
                'id': 3, 'login': 'reviewer2', 'node_id': 'MDQ6VXNlcjM=', 
                'type': 'User', 'site_admin': False, 'name': 'Reviewer Two', 
                'email': 'reviewer2@example.com', 'company': None, 'location': None, 'bio': None, 
                'public_repos': 0, 'public_gists': 0, 'followers': 0, 'following': 0, 
                'created_at': "2020-01-01T00:00:00Z", 'updated_at': "2020-01-01T00:00:00Z"
            },
        ]

        # Repository data
        self.repo1_data = {
            'id': 101, 'node_id': 'MDEwOlJlcG9zaXRvcnkxMDE=', 'name': 'repo1', 
            'full_name': 'owner1/repo1', 'private': False, 'owner': self.owner_user_data, 
            'description': 'Test repo 1', 'fork': False,
            'created_at': "2021-01-01T00:00:00Z", 'updated_at': "2021-01-01T00:00:00Z",
            'pushed_at': "2021-01-01T00:00:00Z", 'size': 1024, 'stargazers_count': 10,
            'watchers_count': 10, 'language': 'Python', 'has_issues': True, 
            'has_projects': True, 'has_downloads': True, 'has_wiki': True, 'has_pages': False, 
            'forks_count': 0, 'archived': False, 'disabled': False, 'open_issues_count': 1, 
            'license': None, 'allow_forking': True, 'is_template': False, 
            'web_commit_signoff_required': False, 'topics': [], 'visibility': 'public', 
            'default_branch': 'main'
        }
        self.repo2_data = {
            'id': 102, 'node_id': 'MDEwOlJlcG9zaXRvcnkxMDI=', 'name': 'repo2', 
            'full_name': 'owner1/repo2', 'private': False, 'owner': self.owner_user_data, 
            'description': 'Test repo 2', 'fork': False,
            'created_at': "2021-02-01T00:00:00Z", 'updated_at': "2021-02-01T00:00:00Z",
            'pushed_at': "2021-02-01T00:00:00Z", 'size': 512, 'stargazers_count': 0,
            'watchers_count': 0, 'language': 'Python', 'has_issues': True, 
            'has_projects': True, 'has_downloads': True, 'has_wiki': True, 'has_pages': False, 
            'forks_count': 0, 'archived': False, 'disabled': False, 'open_issues_count': 0, 
            'license': None, 'allow_forking': True, 'is_template': False, 
            'web_commit_signoff_required': False, 'topics': [], 'visibility': 'public', 
            'default_branch': 'main'
        }
        self.DB['Repositories'] = [self.repo1_data, self.repo2_data]

        # Pull Request data
        common_pr_fields = {
            'labels': [], 'assignee': None, 'assignees': [], 'milestone': None,
            'closed_at': None, 'merged_at': None, 'draft': False,
            'merged': False, 'mergeable': True, 'rebaseable': True, 'mergeable_state': 'clean',
            'merged_by': None, 'comments': 0, 'review_comments': 0, 'commits': 1,
            'additions': 10, 'deletions': 2, 'changed_files': 1,
        }
        self.pr1_repo1_data = {
            'id': 1001, 'node_id': 'PR_NODE_1001', 'number': 1, 'title': 'PR 1 for Repo 1',
            'user': self.owner_user_data, 'state': 'open', 'locked': False, 
            'created_at': "2022-01-01T10:00:00Z", 'updated_at': "2022-01-01T11:00:00Z",
            'author_association': 'OWNER', 'body': 'Body of PR 1',
            'head': {'label': 'owner1:feature-branch', 'ref': 'feature-branch', 'sha': '0000000000000000000000000000000000000001', 'user': self.owner_user_data, 'repo': self.repo1_data},
            'base': {'label': 'owner1:main', 'ref': 'main', 'sha': '0000000000000000000000000000000000000002', 'user': self.owner_user_data, 'repo': self.repo1_data},
            **common_pr_fields
        }
        self.pr2_repo1_data = { # PR with no reviews
            'id': 1002, 'node_id': 'PR_NODE_1002', 'number': 2, 'title': 'PR 2 for Repo 1 (no reviews)',
            'user': self.owner_user_data, 'state': 'open', 'locked': False,
            'created_at': "2022-02-01T10:00:00Z", 'updated_at': "2022-02-01T11:00:00Z",
            'author_association': 'OWNER', 'body': 'Body of PR 2',
            'head': {'label': 'owner1:another-feature', 'ref': 'another-feature', 'sha': '0000000000000000000000000000000000000003', 'user': self.owner_user_data, 'repo': self.repo1_data},
            'base': {'label': 'owner1:main', 'ref': 'main', 'sha': '0000000000000000000000000000000000000002', 'user': self.owner_user_data, 'repo': self.repo1_data},
            **common_pr_fields, 'additions': 5, 'deletions': 1
        }
        self.pr1_repo2_data = { # PR in another repo, with same number as pr1_repo1
            'id': 2001, 'node_id': 'PR_NODE_2001', 'number': 1, 'title': 'PR 1 for Repo 2',
            'user': self.owner_user_data, 'state': 'open', 'locked': False,
            'created_at': "2022-03-01T10:00:00Z", 'updated_at': "2022-03-01T11:00:00Z",
            'author_association': 'OWNER', 'body': 'Body of PR 1 in Repo 2',
            'head': {'label': 'owner1:repo2-feature', 'ref': 'repo2-feature', 'sha': '0000000000000000000000000000000000000004', 'user': self.owner_user_data, 'repo': self.repo2_data},
            'base': {'label': 'owner1:main', 'ref': 'main', 'sha': '0000000000000000000000000000000000000005', 'user': self.owner_user_data, 'repo': self.repo2_data},
            **common_pr_fields, 'additions': 20, 'deletions': 5, 'changed_files': 2
        }
        self.DB['PullRequests'] = [self.pr1_repo1_data, self.pr2_repo1_data, self.pr1_repo2_data]

        # Branch data - needed for branch protection tests
        self.feature_branch_name = "feature-branch"  # matches the head branch in pr1_repo1_data
        self.repository_data = self.repo1_data  # reference for the test
        self.DB['Branches'] = [
            {
                'id': 1, 'name': 'main', 'repository_id': 101, 'protected': False,
                'commit': {'sha': '0000000000000000000000000000000000000002'}
            },
            {
                'id': 2, 'name': self.feature_branch_name, 'repository_id': 101, 'protected': False,
                'commit': {'sha': '0000000000000000000000000000000000000001'}
            },
            {
                'id': 3, 'name': 'another-feature', 'repository_id': 101, 'protected': False,
                'commit': {'sha': '0000000000000000000000000000000000000003'}
            },
            {
                'id': 4, 'name': 'main', 'repository_id': 102, 'protected': False,
                'commit': {'sha': '0000000000000000000000000000000000000005'}
            },
            {
                'id': 5, 'name': 'repo2-feature', 'repository_id': 102, 'protected': False,
                'commit': {'sha': '0000000000000000000000000000000000000004'}
            }
        ]

        # Pull Request Review data for PR 1 (id: 1001) in Repo 1
        self.review1_pr1 = {
            'id': 1, 'node_id': 'PRR_NODE_1', 'pull_request_id': 1001,
            'user': self.reviewer1_user_data, 'body': 'Looks good!', 'state': 'APPROVED',
            'commit_id': '0000000000000000000000000000000000000001', 'submitted_at': "2023-01-01T12:00:00Z",
            'author_association': 'MEMBER'
        }
        self.review2_pr1 = {
            'id': 2, 'node_id': 'PRR_NODE_2', 'pull_request_id': 1001,
            'user': self.reviewer2_user_data, 'body': 'Please fix this.', 'state': 'CHANGES_REQUESTED',
            'commit_id': '0000000000000000000000000000000000000001', 'submitted_at': "2023-01-01T10:00:00Z",
            'author_association': 'CONTRIBUTOR'
        }
        self.review3_pr1 = { # Review with None submitted_at and None body
            'id': 3, 'node_id': 'PRR_NODE_3', 'pull_request_id': 1001,
            'user': self.reviewer1_user_data, 'body': None, 'state': 'COMMENTED',
            'commit_id': '0000000000000000000000000000000000000001', 'submitted_at': None,
            'author_association': 'MEMBER'
        }
        self.review4_pr1 = { # Another review to test sorting
            'id': 4, 'node_id': 'PRR_NODE_4', 'pull_request_id': 1001,
            'user': self.reviewer2_user_data, 'body': 'One more comment', 'state': 'COMMENTED',
            'commit_id': '0000000000000000000000000000000000000001', 'submitted_at': "2023-01-01T11:00:00Z",
            'author_association': 'CONTRIBUTOR'
        }
        # Review for a different PR (PR 1 in Repo 2, id: 2001)
        self.review1_pr1_repo2 = {
            'id': 5, 'node_id': 'PRR_NODE_5', 'pull_request_id': 2001,
            'user': self.reviewer1_user_data, 'body': 'Review for PR in repo2', 'state': 'APPROVED',
            'commit_id': '0000000000000000000000000000000000000004', 'submitted_at': "2023-02-01T10:00:00Z",
            'author_association': 'MEMBER'
        }
        self.DB['PullRequestReviews'] = [
            self.review1_pr1, self.review2_pr1, self.review3_pr1, self.review4_pr1,
            self.review1_pr1_repo2
        ]

    def _assert_review_data_matches(self, review_dict, db_review_data):
        """Helper to assert that a returned review dictionary matches DB data."""
        self.assertEqual(review_dict['id'], db_review_data['id'])
        self.assertEqual(review_dict['node_id'], db_review_data['node_id'])
        self.assertEqual(review_dict['user']['id'], db_review_data['user']['id'])
        self.assertEqual(review_dict['user']['login'], db_review_data['user']['login'])
        self.assertEqual(review_dict['body'], db_review_data['body'])
        self.assertEqual(review_dict['state'], db_review_data['state'])
        self.assertEqual(review_dict['commit_id'], db_review_data['commit_id'])
        self.assertEqual(review_dict['submitted_at'], db_review_data['submitted_at'])
        self.assertEqual(review_dict['author_association'], db_review_data['author_association'])

    def test_success_multiple_reviews_sorted_chronologically(self):
        """Test successfully retrieving multiple reviews, sorted by submission time."""
        reviews = get_pull_request_reviews(owner='owner1', repo='repo1', pull_number=1) # type: ignore
        self.assertEqual(len(reviews), 4)

        # Expected order: None submitted_at first, then chronological (older to newer)
        # review3 (None), review2 (10:00), review4 (11:00), review1 (12:00)

        submitted_ats = [r['submitted_at'] for r in reviews]
        expected_submitted_ats = [
            None, 
            "2023-01-01T10:00:00Z", 
            "2023-01-01T11:00:00Z", 
            "2023-01-01T12:00:00Z"
        ]
        self.assertEqual(submitted_ats, expected_submitted_ats, "Reviews are not sorted correctly by submitted_at.")

        self._assert_review_data_matches(reviews[0], self.review3_pr1)
        self._assert_review_data_matches(reviews[1], self.review2_pr1)
        self._assert_review_data_matches(reviews[2], self.review4_pr1)
        self._assert_review_data_matches(reviews[3], self.review1_pr1)

    def test_success_no_reviews_for_pull_request(self):
        """Test retrieving reviews for a PR that has no reviews, expecting an empty list."""
        reviews = get_pull_request_reviews(owner='owner1', repo='repo1', pull_number=2) # type: ignore
        self.assertEqual(len(reviews), 0)

    def test_success_case_insensitive_owner_repo_names(self):
        """Test that owner and repo names are treated case-insensitively."""
        reviews = get_pull_request_reviews(owner='OwNeR1', repo='RePo1', pull_number=1) # type: ignore
        self.assertEqual(len(reviews), 4) 
        # A light check; detailed content is verified in test_success_multiple_reviews_sorted_chronologically
        self.assertEqual(reviews[0]['id'], self.review3_pr1['id'])

    def test_success_pull_request_from_correct_repository(self):
        """Test retrieving reviews for a PR that has the same number as another PR but is in a different repo."""
        reviews = get_pull_request_reviews(owner='owner1', repo='repo2', pull_number=1) # type: ignore
        self.assertEqual(len(reviews), 1)
        self._assert_review_data_matches(reviews[0], self.review1_pr1_repo2)

    def test_notfounderror_repository_not_found_invalid_owner(self):
        """Test NotFoundError when the repository owner does not exist."""
        self.assert_error_behavior( # type: ignore
            func_to_call=get_pull_request_reviews, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Repository not found for owner 'nonexistent_owner'.",
            owner="nonexistent_owner", repo="repo1", pull_number=1
        )

    def test_notfounderror_repository_not_found_invalid_repo_name(self):
        """Test NotFoundError when the repository name does not exist for the given owner."""
        self.assert_error_behavior( # type: ignore
            func_to_call=get_pull_request_reviews, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Repository not found for owner 'owner1' and repo 'nonexistent_repo'.",
            owner="owner1", repo="nonexistent_repo", pull_number=1
        )

    def test_notfounderror_pull_request_not_found_invalid_pull_number(self):
        """Test NotFoundError when the pull request number does not exist in the specified repository."""
        self.assert_error_behavior( # type: ignore
            func_to_call=get_pull_request_reviews, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Pull request not found for owner 'owner1', repo 'repo1', and pull number 999.",
            owner="owner1", repo="repo1", pull_number=999 
        )

    def test_notfounderror_pull_request_not_found_repo_exists_but_no_such_pr_in_it(self):
        """Test NotFoundError when repo exists but specified pull number is not found in that repo."""
        # Repo2 exists, but PR number 3 does not exist in it (only PR #1 exists in repo2).
        self.assert_error_behavior( # type: ignore
            func_to_call=get_pull_request_reviews, # type: ignore
            expected_exception_type=NotFoundError, # type: ignore
            expected_message="Pull request not found for owner 'owner1', repo 'repo2', and pull number 3.",
            owner="owner1", repo="repo2", pull_number=3 
        )
    
    def test_submitted_at_with_datetime_objects(self):
        """If reviews carry datetime objects, they get ISO-formatted correctly."""
        from datetime import datetime, timezone
        # add two datetime-based reviews to PR #1
        dt_naive = datetime(2023, 1, 2, 9, 30)                # naive → assume UTC
        dt_aware = datetime(2023, 1, 2, 10, 45, tzinfo=timezone.utc)
        rev_naive = dict(self.review1_pr1, id=6, submitted_at=dt_naive)
        rev_aware = dict(self.review1_pr1, id=7, submitted_at=dt_aware)
        self.DB['PullRequestReviews'].extend([rev_naive, rev_aware])

        reviews = get_pull_request_reviews(owner='owner1', repo='repo1', pull_number=1) # type: ignore
        # find our two new ones by id
        got_naive = next(r for r in reviews if r['id']==6)
        got_aware = next(r for r in reviews if r['id']==7)

        self.assertEqual(got_naive['submitted_at'], "2023-01-02T09:30:00Z")
        self.assertEqual(got_aware['submitted_at'], "2023-01-02T10:45:00+00:00")

    def test_malformed_iso_submitted_at_handled_and_preserved(self):
        """Malformed ISO strings sort as earliest but are returned unchanged."""
        # insert a malformed timestamp
        bad = dict(self.review1_pr1, id=8, submitted_at="not-a-timestamp")
        self.DB['PullRequestReviews'].append(bad)

        reviews = get_pull_request_reviews(owner='owner1', repo='repo1', pull_number=1) # type: ignore
        # The malformed one should sort first (after the None one) but its string is preserved
        idx = [r['id'] for r in reviews].index(8)
        self.assertEqual(reviews[idx]['submitted_at'], "not-a-timestamp")

    def test_timezone_offset_string_submitted_at(self):
        """ISO strings with timezone offsets are parsed and sorted correctly."""
        # 12:00+05:30 → 06:30Z, should come just after the None entry
        offset_rev = dict(self.review1_pr1, id=9, submitted_at="2023-01-01T12:00:00+05:30")
        self.DB['PullRequestReviews'].append(offset_rev)

        reviews = get_pull_request_reviews(owner='owner1', repo='repo1', pull_number=1) # type: ignore
        submitted_ats = [r['submitted_at'] for r in reviews]
        # expected order start: None (id=3), then our offset (id=9)
        self.assertEqual(submitted_ats[0], None)
        self.assertEqual(submitted_ats[1], "2023-01-01T12:00:00+05:30")
    
    def test_missing_user_fields_yield_none(self):
        """If a review's user dict lacks login/id, they come back as None."""
        anon = {
            'id': 10, 'node_id': 'PRR_NODE_10', 'pull_request_id': 1001,
            'user': {}, 'body': 'Anon review', 'state': 'COMMENTED',
            'commit_id': 'sha...', 'submitted_at': "2023-01-03T00:00:00Z",
            'author_association': 'NONE'
        }
        self.DB['PullRequestReviews'].append(anon)
        reviews = get_pull_request_reviews(owner='owner1', repo='repo1', pull_number=1) # type: ignore
        last = next(r for r in reviews if r['id']==10)
        self.assertIsNone(last['user']['login'])
        self.assertIsNone(last['user']['id'])
    
    # --- New Input Validation Tests ---
    def test_invalid_owner_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_reviews,
            expected_exception_type=TypeError,
            expected_message="Argument 'owner' must be a string, got int.",
            owner=123, # Invalid type for owner
            repo="repo1",
            pull_number=1
        )

    def test_invalid_repo_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_reviews,
            expected_exception_type=TypeError,
            expected_message="Argument 'repo' must be a string, got int.",
            owner="owner1", 
            repo=123, # Invalid type for repo
            pull_number=1
        )

    def test_invalid_pull_number_type(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_reviews,
            expected_exception_type=TypeError,
            expected_message="Argument 'pull_number' must be an integer, got str.",
            owner="owner1",
            repo="repo1",
            pull_number="1" # Invalid type for pull_number (string)
        )

    def test_non_positive_pull_number_zero(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_reviews,
            expected_exception_type=ValueError,
            expected_message="Argument 'pull_number' must be a positive integer, got 0.",
            owner="owner1", 
            repo="repo1", 
            pull_number=0 
        )

    def test_non_positive_pull_number_negative(self):
        self.assert_error_behavior(
            func_to_call=get_pull_request_reviews,
            expected_exception_type=ValueError,
            expected_message="Argument 'pull_number' must be a positive integer, got -1.",
            owner="owner1", 
            repo="repo1", 
            pull_number=-1
        )
    # --- Existing Tests (preserved and should still pass) ---
    def test_success_multiple_reviews_sorted_chronologically(self):
        """Test successfully retrieving multiple reviews, sorted by submission time."""
        reviews = get_pull_request_reviews(owner='owner1', repo='repo1', pull_number=1)
        self.assertEqual(len(reviews), 4)

        submitted_ats = [r['submitted_at'] for r in reviews]
        expected_submitted_ats = [
            None, 
            "2023-01-01T10:00:00Z", 
            "2023-01-01T11:00:00Z", 
            "2023-01-01T12:00:00Z"
        ]
        self.assertEqual(submitted_ats, expected_submitted_ats, "Reviews are not sorted correctly by submitted_at.")

        self._assert_review_data_matches(reviews[0], self.review3_pr1)
        self._assert_review_data_matches(reviews[1], self.review2_pr1)
        self._assert_review_data_matches(reviews[2], self.review4_pr1)
        self._assert_review_data_matches(reviews[3], self.review1_pr1)

    def test_success_no_reviews_for_pull_request(self):
        """Test retrieving reviews for a PR that has no reviews, expecting an empty list."""
        reviews = get_pull_request_reviews(owner='owner1', repo='repo1', pull_number=2)
        self.assertEqual(len(reviews), 0)

    def test_success_case_insensitive_owner_repo_names(self):
        """Test that owner and repo names are treated case-insensitively."""
        reviews = get_pull_request_reviews(owner='OwNeR1', repo='RePo1', pull_number=1)
        self.assertEqual(len(reviews), 4) 
        self.assertEqual(reviews[0]['id'], self.review3_pr1['id'])

    def test_success_pull_request_from_correct_repository(self):
        """Test retrieving reviews for a PR that has the same number as another PR but is in a different repo."""
        reviews = get_pull_request_reviews(owner='owner1', repo='repo2', pull_number=1)
        self.assertEqual(len(reviews), 1)
        self._assert_review_data_matches(reviews[0], self.review1_pr1_repo2)

    def test_notfounderror_repository_not_found_invalid_owner(self):
        """Test NotFoundError when the repository owner does not exist."""
        self.assert_error_behavior( 
            func_to_call=get_pull_request_reviews, 
            expected_exception_type=NotFoundError, 
            expected_message="Repository 'nonexistent_owner/repo1' not found.",
            owner="nonexistent_owner", repo="repo1", pull_number=1
        )

    def test_notfounderror_repository_not_found_invalid_repo_name(self):
        """Test NotFoundError when the repository name does not exist for the given owner."""
        self.assert_error_behavior(
            func_to_call=get_pull_request_reviews,
            expected_exception_type=NotFoundError,
            expected_message="Repository 'owner1/nonexistent_repo' not found.",
            owner="owner1", repo="nonexistent_repo", pull_number=1
        )

    def test_notfounderror_pull_request_not_found_invalid_pull_number(self):
        """Test NotFoundError when the pull request number does not exist in the specified repository."""
        self.assert_error_behavior(
            func_to_call=get_pull_request_reviews,
            expected_exception_type=NotFoundError,
            expected_message="Pull request #999 not found in repository 'owner1/repo1'.",
            owner="owner1", repo="repo1", pull_number=999 
        )

    def test_notfounderror_pull_request_not_found_repo_exists_but_no_such_pr_in_it(self):
        """Test NotFoundError when repo exists but specified pull number is not found in that repo."""
        self.assert_error_behavior(
            func_to_call=get_pull_request_reviews,
            expected_exception_type=NotFoundError,
            expected_message="Pull request #3 not found in repository 'owner1/repo2'.",
            owner="owner1", repo="repo2", pull_number=3 
        )
    def test_update_branch_protection_prevents_update_on_head(self):
        # Test forbidden error when the head branch is protected and the current user is not an admin on the head repository.
        # In this default setup, the head branch is in the base repository, and the current user (collabuser) is not an admin.
        branch_idx = -1
        original_protection = None
        # Protect the head branch (feature_branch_name).
        for i, branch in enumerate(self.DB["Branches"]):
            if branch["name"] == self.feature_branch_name and \
               branch["repository_id"] == self.repository_data["id"]: 
                branch_idx = i
                original_protection = branch["protected"]
                self.DB["Branches"][branch_idx]["protected"] = True
                break
        else:
            self.fail("Test setup: Head branch (feature_branch_name) not found in the base repository to apply protection.")
        
        try:
            self.assert_error_behavior(
                func_to_call=update_pull_request_branch,
                expected_exception_type=ForbiddenError,
                expected_message="Authentication required to update pull request branch.",
                owner='owner1', repo='repo1', pull_number=1
            )
        finally: # Restore original branch protection status.
            if branch_idx != -1 and original_protection is not None:
                self.DB["Branches"][branch_idx]["protected"] = original_protection