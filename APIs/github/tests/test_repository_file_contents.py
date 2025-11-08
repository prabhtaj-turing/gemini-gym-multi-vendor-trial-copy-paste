import copy
import unittest
from datetime import datetime, timezone
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import NotFoundError, ValidationError
from ..SimulationEngine.db import DB
from ..repositories import get_file_contents
import datetime
import pytest
from github.SimulationEngine import models


class TestGetFileContents(BaseTestCaseWithErrorHandler):

    OWNER_LOGIN = "testowner"
    REPO_NAME = "testrepo"
    REPO_ID = 101 # New: For direct use in keys

    REPO_NO_DEFAULT_NAME = "testrepo_no_default"
    REPO_NO_DEFAULT_ID = 102 # New: For direct use in keys

    OTHER_OWNER_LOGIN = "otherowner"

    MAIN_BRANCH = "main"
    FEATURE_BRANCH = "feature"
    DEV_BRANCH = "dev"

    # Specific Commit SHAs for branches
    MAIN_COMMIT_SHA = "maincommitref123abc456def78901234567890"
    FEATURE_COMMIT_SHA = "featurecommitref456abc789def01234567890"
    DEV_COMMIT_SHA = "devcommitsha000000000000000000000000000"

    VALID_BLOB_SHA_README_MAIN = "1111111111111111111111111111111111111111"
    VALID_BLOB_SHA_README_FEATURE = "2222222222222222222222222222222222222222"
    VALID_BLOB_SHA_APP_PY = "3333333333333333333333333333333333333333"
    VALID_BLOB_SHA_CONFIG_JSON = "4444444444444444444444444444444444444444"
    VALID_BLOB_SHA_MAIN_PY_DEV = "5555555555555555555555555555555555555555"
    VALID_BLOB_SHA_EMPTY_TXT = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
    VALID_BLOB_SHA_README_LOWER = "6666666666666666666666666666666666666666"

    VALID_TREE_SHA_SRC_LIB = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    VALID_TREE_SHA_ROOT_SRC = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    original_db_state = None # To store the initial state of the DB
    TAG_NAME = "v1.0"
    TAGGED_COMMIT_SHA = "taggedcommitshaforv10abc"
    TAG_FILE_PATH = "docs/release_notes.txt"
    MALFORMED_TAG_NAME = "v0.9-broken-tag"

    BRANCH_FOR_SHA_REF = "dev-feature-x"
    COMMIT_SHA_AT_BRANCH_TIP_ONLY = "commitshabranchtiponly789" # This SHA will NOT be in DB['Commits']
    FILE_PATH_FOR_SHA_AT_BRANCH_TIP = "src/core_module.py"

    # Content for new test files
    tag_release_notes_content = {
        "type": "file", "encoding": "base64", "size": 15, "name": "release_notes.txt",
        "path": TAG_FILE_PATH, "content": "VjEuMCByZWxlYXNlZA==", "sha": "tagfilessha123abc"
    }
    sha_at_branch_tip_content = {
        "type": "file", "encoding": "base64", "size": 20, "name": "core_module.py",
        "path": FILE_PATH_FOR_SHA_AT_BRANCH_TIP, "content": "Y29yZSBtb2R1bGUgY29kZQ==", "sha": "coremodfilesha456def"
    }

    @classmethod
    def setUpClass(cls):
        """Set up once before all tests in the class."""
        # Deep copy the DB state to restore later after all tests
        cls.original_db_state = copy.deepcopy(DB)

    @classmethod
    def tearDownClass(cls):
        """Tear down once after all tests in the class."""
        # Restore the DB to its original state
        DB.clear()
        DB.update(cls.original_db_state)

    def setUp(self):
        """Set up the test environment before each test method."""
        DB.clear() # Clear DB before each test
        # Repopulate with a fresh copy of necessary data structures for each test
        # This ensures test independence regarding DB state.

        DB['Users'] = [
            {
                'id': 1, 'login': self.OWNER_LOGIN, 'node_id': 'U_NODEID_1', 'type': 'User',
                'site_admin': False, 'name': 'Test Owner', 'email': 'owner@example.com',
                'company': 'Test Inc', 'location': 'Test City', 'bio': 'A test user.',
                'public_repos': 2, 'public_gists': 0, 'followers': 10, 'following': 5,
                'created_at': datetime.datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
                'updated_at': datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
            },
            {
                'id': 2, 'login': self.OTHER_OWNER_LOGIN, 'node_id': 'U_NODEID_2', 'type': 'User',
                'site_admin': False, 'name': 'Other Owner', 'email': 'other@example.com',
                'company': 'Other Corp', 'location': 'Other City', 'bio': 'Another test user.',
                'public_repos': 1, 'public_gists': 1, 'followers': 5, 'following': 2,
                'created_at': datetime.datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
                'updated_at': datetime.datetime(2023, 2, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
            },
        ]
        DB['Repositories'] = [
            {
                'id': self.REPO_ID, 'node_id': 'R_NODEID_101', 'name': self.REPO_NAME,
                'full_name': f"{self.OWNER_LOGIN}/{self.REPO_NAME}", # full_name still used for repo lookup
                'private': False, 'owner': {'id': 1, 'login': self.OWNER_LOGIN, 'node_id': 'U_NODEID_1', 'type': 'User', 'site_admin': False},
                'description': 'Test repository', 'fork': False,
                'created_at': datetime.datetime(2022, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                'updated_at': datetime.datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                'pushed_at': datetime.datetime(2023, 1, 15, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                'size': 1024, 'default_branch': self.MAIN_BRANCH, 'stargazers_count': 5, 'watchers_count': 5,
                'language': 'Python', 'has_issues': True, 'has_projects': True, 'has_downloads': True,
                'has_wiki': True, 'has_pages': False, 'forks_count': 0, 'archived': False, 'disabled': False,
                'open_issues_count': 2, 'license': None, 'allow_forking': True, 'is_template': False,
                'web_commit_signoff_required': False, 'topics': ['test', 'python'], 'visibility': 'public',
                'forks': 0, 'open_issues': 2, 'watchers': 5,
            },
            {
                'id': self.REPO_NO_DEFAULT_ID, 'node_id': 'R_NODEID_102', 'name': self.REPO_NO_DEFAULT_NAME,
                'full_name': f"{self.OWNER_LOGIN}/{self.REPO_NO_DEFAULT_NAME}", 'private': False,
                'owner': {'id': 1, 'login': self.OWNER_LOGIN, 'node_id': 'U_NODEID_1', 'type': 'User', 'site_admin': False},
                'description': 'Repo without default branch', 'fork': False,
                'created_at': datetime.datetime(2022, 2, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                'updated_at': datetime.datetime(2023, 2, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                'pushed_at': datetime.datetime(2023, 2, 15, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                'size': 512, 'default_branch': None, 'stargazers_count': 1, 'watchers_count': 1,
                'language': 'JavaScript', 'has_issues': False, 'has_projects': False, 'has_downloads': True,
                'has_wiki': False, 'has_pages': True, 'forks_count': 1, 'archived': True, 'disabled': False,
                'open_issues_count': 0, 'license': None, 'allow_forking': False, 'is_template': True,
                'web_commit_signoff_required': True, 'topics': ['template'], 'visibility': 'public',
                'forks': 1, 'open_issues': 0, 'watchers': 1,
            }
        ]


        DB['Branches'] = [
            {'name': self.MAIN_BRANCH, 'commit': {'sha': self.MAIN_COMMIT_SHA}, 'protected': False, 'repository_id': self.REPO_ID},
            {'name': self.FEATURE_BRANCH, 'commit': {'sha': self.FEATURE_COMMIT_SHA}, 'protected': False, 'repository_id': self.REPO_ID},
            {'name': self.DEV_BRANCH, 'commit': {'sha': self.DEV_COMMIT_SHA}, 'protected': False, 'repository_id': self.REPO_NO_DEFAULT_ID},
            {'name': self.BRANCH_FOR_SHA_REF, 'commit': {'sha': self.COMMIT_SHA_AT_BRANCH_TIP_ONLY}, 'protected': False, 'repository_id': self.REPO_ID},
        ]

        DB['Commits'] = [
            {'sha': self.MAIN_COMMIT_SHA, 'repository_id': self.REPO_ID, 'message': 'Initial commit'},
            {'sha': self.FEATURE_COMMIT_SHA, 'repository_id': self.REPO_ID, 'message': 'Feature commit'},
            {'sha': self.DEV_COMMIT_SHA, 'repository_id': self.REPO_NO_DEFAULT_ID, 'message': 'Dev commit'},
            {'sha': self.TAGGED_COMMIT_SHA, 'repository_id': self.REPO_ID, 'message': 'Commit for v1.0 tag'},
        ]

        DB['Tags'] = [
            {'name': self.TAG_NAME, 'commit': {'sha': self.TAGGED_COMMIT_SHA}, 'repository_id': self.REPO_ID, 'message': 'Release version 1.0'},
            {'name': self.MALFORMED_TAG_NAME, 'commit': {'no_sha_here': 'some_value'}, 'repository_id': self.REPO_ID, 'message': 'A broken tag entry'},
        ]

        self.readme_content_main = {
            "type": "file", "encoding": "base64", "size": 33, "name": "README.md", "path": "README.md",
            "content": "UmVhZG1lIGNvbnRlbnQgZm9yIG1haW4gYnJhbmNoLg==", "sha": self.VALID_BLOB_SHA_README_MAIN
        }
        self.readme_content_feature = {
            "type": "file", "encoding": "base64", "size": 36, "name": "README.md", "path": "README.md",
            "content": "UmVhZG1lIGNvbnRlbnQgZm9yIGZlYXR1cmUgYnJhbmNoLg==", "sha": self.VALID_BLOB_SHA_README_FEATURE
        }
        self.app_py_content_main = {
            "type": "file", "encoding": "base64", "size": 20, "name": "app.py", "path": "src/app.py",
            "content": "cHJpbnQoIkhlbGxvLCBhcHAucHkhIik=", "sha": self.VALID_BLOB_SHA_APP_PY
        }
        self.config_json_content_commit = {
            "type": "file", "encoding": "base64", "size": 17, "name": "config.json", "path": "config.json",
            "content": "eyJrZXkiOiAidmFsdWUifQ==", "sha": self.VALID_BLOB_SHA_CONFIG_JSON
        }
        self.src_dir_content_main = [
            {"type": "file", "size": 20, "name": "app.py", "path": "src/app.py", "sha": self.VALID_BLOB_SHA_APP_PY},
            {"type": "dir", "size": 0, "name": "lib", "path": "src/lib", "sha": self.VALID_TREE_SHA_SRC_LIB}
        ]
        self.root_dir_content_main = [
            {"type": "file", "size": 33, "name": "README.md", "path": "README.md", "sha": self.VALID_BLOB_SHA_README_MAIN},
            {"type": "dir", "size": 0, "name": "src", "path": "src", "sha": self.VALID_TREE_SHA_ROOT_SRC}
        ]


        DB['FileContents'] = {
            # Existing content keys
            f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:README.md": self.readme_content_main,
            f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:src": self.src_dir_content_main,
            f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:src/app.py": self.app_py_content_main,
            f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:": self.root_dir_content_main,
            f"{self.REPO_ID}:{self.FEATURE_COMMIT_SHA}:README.md": self.readme_content_feature,
            f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:config.json": self.config_json_content_commit,
            f"{self.REPO_NO_DEFAULT_ID}:{self.DEV_COMMIT_SHA}:main.py": {
                "type": "file", "encoding": "base64", "size": 19, "name": "main.py", "path": "main.py",
                "content": "cHJpbnQoImRldiBicmFuY2giKQ==", "sha": self.VALID_BLOB_SHA_MAIN_PY_DEV
            },
            # New content keys for tag and SHA-only ref tests
            f"{self.REPO_ID}:{self.TAGGED_COMMIT_SHA}:{self.TAG_FILE_PATH}": self.tag_release_notes_content,
            f"{self.REPO_ID}:{self.COMMIT_SHA_AT_BRANCH_TIP_ONLY}:{self.FILE_PATH_FOR_SHA_AT_BRANCH_TIP}": self.sha_at_branch_tip_content,
        }

    def test_get_content_empty_owner_raises_ValidationError(self):
        self.assert_error_behavior(get_file_contents, ValidationError, expected_message="Repository owner cannot be empty.", owner="", repo=self.REPO_NAME, path="README.md")

    def test_get_content_empty_repo_raises_ValidationError(self):
        self.assert_error_behavior(get_file_contents, ValidationError, expected_message="Repository name cannot be empty.", owner=self.OWNER_LOGIN, repo="", path="README.md")

    def test_get_content_empty_path_raises_ValidationError(self):
        """Tests that an empty path string now raises ValidationError."""
        self.assert_error_behavior(get_file_contents, ValidationError, expected_message="Path cannot be empty.", owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="")


    def test_get_file_content_default_branch_success(self):
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="README.md")
        self.assertEqual(result, self.readme_content_main)
        self.assertIsInstance(result, dict)

    def test_get_directory_content_default_branch_success(self):
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="src")
        self.assertEqual(result, self.src_dir_content_main)
        self.assertIsInstance(result, list)
        if isinstance(result, list):
            self.assertTrue(all(isinstance(item, dict) for item in result))

    def test_get_root_directory_content_default_branch_raises_badrequest(self):
        """Tests that path="" now raises ValidationError due to `if not path:` validation."""
        # Empty path argument
        self.assert_error_behavior(get_file_contents, ValidationError, expected_message="Path cannot be empty.", owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="")

    def test_get_file_content_with_branch_ref_success(self):
        """Tests successfully retrieving file content when a specific branch name is provided as ref."""
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="README.md", ref=self.FEATURE_BRANCH) # type: ignore
        self.assertEqual(result, self.readme_content_feature)

    def test_get_file_content_with_commit_sha_ref_success(self):
        """Tests successfully retrieving file content when a specific commit SHA is provided as ref."""
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="config.json", ref=self.MAIN_COMMIT_SHA) # type: ignore
        self.assertEqual(result, self.config_json_content_commit)

    def test_get_content_path_with_leading_slash(self):
        """Tests that paths with leading slashes are correctly handled (normalized) for both files and directories."""
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="/README.md", ref=self.MAIN_BRANCH)
        self.assertEqual(result, self.readme_content_main)

        result_dir = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="/src", ref=self.MAIN_BRANCH)
        self.assertEqual(result_dir, self.src_dir_content_main)


    def test_get_content_non_existent_owner_raises_notfounderror(self):
        self.assert_error_behavior(func_to_call=get_file_contents, # type: ignore
            expected_exception_type=NotFoundError, expected_message="Repository 'nonexistentowner/testrepo' not found.", # type: ignore
            owner="nonexistentowner", repo=self.REPO_NAME, path="README.md")

    def test_get_content_non_existent_repo_raises_notfounderror(self):
        self.assert_error_behavior(func_to_call=get_file_contents, # type: ignore
            expected_exception_type=NotFoundError, expected_message="Repository 'testowner/nonexistentrepo' not found.", # type: ignore
            owner=self.OWNER_LOGIN, repo="nonexistentrepo", path="README.md")

    def test_get_content_non_existent_path_file_raises_notfounderror(self):
        self.assert_error_behavior(func_to_call=get_file_contents, # type: ignore
            expected_exception_type=NotFoundError, expected_message="Path 'nonexistentfile.txt' (key: '101:maincommitref123abc456def78901234567890:nonexistentfile.txt') not found at ref 'main' (commit: maincommitref123abc456def78901234567890) in repository 'testowner/testrepo'.", # type: ignore
            owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="nonexistentfile.txt", ref=self.MAIN_BRANCH)

    def test_get_content_non_existent_path_directory_raises_notfounderror(self):
        self.assert_error_behavior(func_to_call=get_file_contents, # type: ignore
            expected_exception_type=NotFoundError, expected_message="Path 'nonexistentdir' (key: '101:maincommitref123abc456def78901234567890:nonexistentdir') not found at ref 'main' (commit: maincommitref123abc456def78901234567890) in repository 'testowner/testrepo'.", # type: ignore
            owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="nonexistentdir", ref=self.MAIN_BRANCH)

    def test_get_content_non_existent_ref_raises_notfounderror(self):
        self.assert_error_behavior(func_to_call=get_file_contents, # type: ignore
            expected_exception_type=NotFoundError, expected_message="Ref 'nonexistentref12345678901234567890' does not exist or could not be resolved to a commit in repository 'testowner/testrepo'.", # type: ignore
            owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="README.md", ref="nonexistentref12345678901234567890")

    def test_get_content_repo_with_no_default_branch_and_no_ref_raises_notfounderror(self):
        self.assert_error_behavior(func_to_call=get_file_contents, # type: ignore
            expected_exception_type=NotFoundError, expected_message="Repository 'testowner/testrepo_no_default' does not have a default branch.", # type: ignore
            owner=self.OWNER_LOGIN, repo=self.REPO_NO_DEFAULT_NAME, path="main.py")

    def test_get_file_content_with_no_default_branch_but_valid_ref_success(self):
        """Tests successful content retrieval if a valid ref is provided, even if the repo has no default branch."""
        expected_content = DB['FileContents'][f"{self.REPO_NO_DEFAULT_ID}:{self.DEV_COMMIT_SHA}:main.py"]
        result = get_file_contents( # type: ignore
            owner=self.OWNER_LOGIN,
            repo=self.REPO_NO_DEFAULT_NAME,
            path="main.py",
            ref=self.DEV_BRANCH
        )
        self.assertEqual(result, expected_content)

    def test_get_file_content_empty_file(self):
        """Tests retrieving the content of a file that is empty (0 bytes)."""
        empty_file_content = {
            "type": "file", "encoding": "base64", "size": 0, "name": "empty.txt", "path": "empty.txt",
            "content": "",
            "sha": self.VALID_BLOB_SHA_EMPTY_TXT
        }
        DB['FileContents'][f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:empty.txt"] = empty_file_content

        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="empty.txt", ref=self.MAIN_BRANCH) # type: ignore
        self.assertEqual(result, empty_file_content)

    def test_get_directory_content_empty_directory(self):
        """Tests retrieving the content of a directory that is empty (contains no files or subdirectories)."""
        empty_dir_content: list = []
        DB['FileContents'][f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:emptydir"] = empty_dir_content

        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="emptydir", ref=self.MAIN_BRANCH) # type: ignore
        self.assertEqual(result, empty_dir_content)
        self.assertIsInstance(result, list)

    def test_path_is_case_sensitive_by_default_in_key(self):
        """Tests that the path component of the FileContents key is treated as case-sensitive."""
        readme_lower_content = {
            "type": "file", "encoding": "base64", "size": 10, "name": "readme.md", "path": "readme.md",
            "content": "bG93ZXJjYXNl", "sha": self.VALID_BLOB_SHA_README_LOWER
        }
        DB['FileContents'][f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:readme.md"] = readme_lower_content

        # Should get the original mixed-case one for "README.md"
        result_upper = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="README.md", ref=self.MAIN_BRANCH) # type: ignore
        self.assertEqual(result_upper, self.readme_content_main)

        # Should get the lowercase one for "readme.md"
        result_lower = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="readme.md", ref=self.MAIN_BRANCH) # type: ignore
        self.assertEqual(result_lower, readme_lower_content)

        # Should fail for a different casing like "Readme.md" if not explicitly keyed
        self.assert_error_behavior(func_to_call=get_file_contents, # type: ignore
            expected_exception_type=NotFoundError, expected_message="Path 'Readme.md' (key: '101:maincommitref123abc456def78901234567890:Readme.md') not found at ref 'main' (commit: maincommitref123abc456def78901234567890) in repository 'testowner/testrepo'.", # type: ignore
            owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="Readme.md", ref=self.MAIN_BRANCH)

    def test_get_content_path_with_dot_segment(self):
        self.assert_error_behavior(func_to_call=get_file_contents, expected_exception_type=NotFoundError, expected_message="Path 'src/./app.py' (key: '101:maincommitref123abc456def78901234567890:src/./app.py') not found at ref 'main' (commit: maincommitref123abc456def78901234567890) in repository 'testowner/testrepo'.", owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="src/./app.py", ref=self.MAIN_BRANCH)

    def test_get_content_path_with_double_dot_segment(self):
        self.assert_error_behavior(func_to_call=get_file_contents, expected_exception_type=NotFoundError, expected_message="Path 'src/../README.md' (key: '101:maincommitref123abc456def78901234567890:src/../README.md') not found at ref 'main' (commit: maincommitref123abc456def78901234567890) in repository 'testowner/testrepo'.", owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="src/../README.md", ref=self.MAIN_BRANCH)

    def test_get_content_path_with_double_slash_segment(self):
        self.assert_error_behavior(func_to_call=get_file_contents, expected_exception_type=NotFoundError, expected_message="Path 'src//app.py' (key: '101:maincommitref123abc456def78901234567890:src//app.py') not found at ref 'main' (commit: maincommitref123abc456def78901234567890) in repository 'testowner/testrepo'.", owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="src//app.py", ref=self.MAIN_BRANCH)

    def test_get_content_ref_is_sha_like_branch_name(self):
        """Tests resolving a branch whose name is a hex string (SHA-like), ensuring it's treated as a branch name."""
        sha_like_branch_name = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
        actual_commit_for_sha_like_branch = "realcommitabc123"

        DB['Branches'].append({
            'name': sha_like_branch_name,
            'commit': {'sha': actual_commit_for_sha_like_branch},
            'protected': False,
            'repository_id': 101
        })

        sha_like_branch_content = {
            "type": "file", "encoding": "base64", "size": 10, "name": "sha_branch.txt",
            "path": "sha_branch.txt", "content": "c2hhIGJyYW5jaA==", "sha": "shafileblob123"
        }
        DB['FileContents'][f"{self.REPO_ID}:{actual_commit_for_sha_like_branch}:sha_branch.txt"] = sha_like_branch_content

        result = get_file_contents(
            owner=self.OWNER_LOGIN,
            repo=self.REPO_NAME,
            path="sha_branch.txt",
            ref=sha_like_branch_name
        )
        self.assertEqual(result, sha_like_branch_content)

    def test_ref_name_case_sensitive_in_resolution_leading_to_different_content(self):
        """
        Tests that branch name resolution is case-sensitive. "Main" and "main"
        can be different branches pointing to different commits.
        """
        main_upper_branch_name = "Main" # Case-different branch name
        main_upper_commit_sha = "mainuppercommitsha789"

        DB['Branches'].append({
            'name': main_upper_branch_name,
            'commit': {'sha': main_upper_commit_sha},
            'protected': False, 'repository_id': self.REPO_ID
        })
        if not any(c['sha'] == main_upper_commit_sha for c in DB['Commits']):
            DB['Commits'].append({
                'sha': main_upper_commit_sha, 'repository_id': self.REPO_ID, 'message': 'Commit for Main (uppercase) branch'
            })


        readme_content_main_upper_ref = { # Distinct content for this branch/commit
            "type": "file", "encoding": "base64", "size": 34, "name": "README.md", "path": "README.md",
            "content": "UmVhZG1lIGNvbnRlbnQgZm9yIE1BSU4gYnJhbmNoLg==", # Slightly different content
            "sha": "mainupperblobsha456xyz"
        }
        DB['FileContents'][f"{self.REPO_ID}:{main_upper_commit_sha}:README.md"] = readme_content_main_upper_ref

        # 1. Fetch with ref="Main" (uppercase) -> resolves to main_upper_commit_sha
        result_upper = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="README.md", ref=main_upper_branch_name)
        self.assertEqual(result_upper, readme_content_main_upper_ref)

        # 2. Fetch with ref="main" (lowercase) -> resolves to self.MAIN_COMMIT_SHA
        result_lower = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="README.md", ref=self.MAIN_BRANCH)
        self.assertEqual(result_lower, self.readme_content_main) # Original content for 'main'

        # 3. Delete content for "Main" branch's commit; fetching with ref="Main" should now fail
        del DB['FileContents'][f"{self.REPO_ID}:{main_upper_commit_sha}:README.md"]
        self.assert_error_behavior(get_file_contents, NotFoundError, expected_message="Path 'README.md' (key: '101:mainuppercommitsha789:README.md') not found at ref 'Main' (commit: mainuppercommitsha789) in repository 'testowner/testrepo'.", owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="README.md", ref=main_upper_branch_name)
    def test_get_file_content_with_tag_ref_success(self):
        """Covers lines 1247-1250: Successfully retrieving file content using a tag name."""
        result = get_file_contents(
            owner=self.OWNER_LOGIN,
            repo=self.REPO_NAME,
            path=self.TAG_FILE_PATH,
            ref=self.TAG_NAME
        )
        self.assertEqual(result, self.tag_release_notes_content)

    def test_get_file_content_with_malformed_tag_ref_raises_notfounderror(self):
        self.assert_error_behavior(get_file_contents, NotFoundError, expected_message="Ref 'v0.9-broken-tag' does not exist or could not be resolved to a commit in repository 'testowner/testrepo'.", # Expected because commit_sha won't be resolved from this tag
            owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path=self.TAG_FILE_PATH, # Path doesn't matter as much as ref resolution failing
            ref=self.MALFORMED_TAG_NAME)
        # This test ensures that if a tag's commit object is malformed (e.g., no 'sha'),
        # commit_sha remains None after the tag loop, and the function proceeds to other
        # resolution methods, likely failing if the MALFORMED_TAG_NAME isn't a valid commit SHA
        # or another resolvable ref. The final NotFoundError would likely be from L1272.

    def test_get_file_content_with_commit_sha_as_branch_tip_not_in_commits_db_success(self):
        """
        This SHA is NOT in DB['Commits'] but IS a tip of a branch.
        """
        # Pre-condition check: Ensure the SHA is not in DB['Commits']
        self.assertFalse(
            any(c['sha'] == self.COMMIT_SHA_AT_BRANCH_TIP_ONLY for c in DB['Commits']),
            f"{self.COMMIT_SHA_AT_BRANCH_TIP_ONLY} should not be in DB['Commits'] for this test."
        )
        # Pre-condition check: Ensure the SHA is a branch tip
        self.assertTrue(
            any(b['name'] == self.BRANCH_FOR_SHA_REF and b['commit']['sha'] == self.COMMIT_SHA_AT_BRANCH_TIP_ONLY for b in DB['Branches']),
             f"{self.COMMIT_SHA_AT_BRANCH_TIP_ONLY} should be a tip of branch {self.BRANCH_FOR_SHA_REF}."
        )

        result = get_file_contents(
            owner=self.OWNER_LOGIN,
            repo=self.REPO_NAME,
            path=self.FILE_PATH_FOR_SHA_AT_BRANCH_TIP,
            ref=self.COMMIT_SHA_AT_BRANCH_TIP_ONLY # This ref is the commit SHA itself
        )
        self.assertEqual(result, self.sha_at_branch_tip_content)
    
    def test_get_file_content_owner_not_string_validation_error(self):
        """Tests that providing an owner that is not a string leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Repository owner name must be a string.",
            owner=123, repo="repo1", path="README.md", ref="main"
        )
    
    def test_get_file_content_repo_not_string_validation_error(self):
        """Tests that providing a repository that is not a string leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Repository name must be a string.",
            owner="owner1", repo=123, path="README.md", ref="main"
        )
    
    def test_get_file_content_path_not_string_validation_error(self):
        """Tests that providing a path that is not a string leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Path must be a string.",
            owner="owner1", repo="repo1", path=123, ref="main"
        )
    
    def test_get_file_content_ref_not_string_validation_error(self):
        """Tests that providing a ref that is not a string leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Ref must be a string.",
            owner="owner1", repo="repo1", path="README.md", ref=123
        )
    
    def test_get_file_content_ref_empty_validation_error(self):
        """Tests that providing a ref that is empty leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Ref cannot be empty.",
            owner="owner1", repo="repo1", path="README.md", ref=""
        )
    
    def test_get_file_content_owner_only_whitespace_validation_error(self):
        """Tests that providing an owner that contains only whitespace leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Repository owner name cannot have only whitespace characters.",
            owner=" ",
            repo="repo1",
            path="README.md",
            ref="main"
        )
    
    def test_get_file_content_repo_only_whitespace_validation_error(self):
        """Tests that providing a repository that contains only whitespace leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Repository name cannot have only whitespace characters.",
            owner="owner1", repo=" ", path="README.md", ref="main"
        )
    
    def test_get_file_content_path_only_whitespace_validation_error(self):
        """Tests that providing a path that contains only whitespace leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Path cannot have only whitespace characters.",
            owner="owner 1", repo="repo1", path=" ", ref="main"
        )
    
    def test_get_file_content_ref_only_whitespace_validation_error(self):
        """Tests that providing a ref that contains only whitespace leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Ref cannot have only whitespace characters.",
            owner="owner 1", repo="repo1", path="README.md", ref=" "
        )
    
    def test_get_file_content_owner_contains_whitespace_validation_error(self):
        """Tests that providing an owner that contains whitespace leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Repository owner name cannot contain whitespace characters.",
            owner="owner 1", repo="repo1", path="README.md", ref="main"
        )
    
    def test_get_file_content_repo_contains_whitespace_validation_error(self):
        """Tests that providing a repository that contains whitespace leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Repository name cannot contain whitespace characters.",
            owner="owner1", repo="repo 1", path="README.md", ref="main"
        )
    
    def test_get_file_content_path_contains_whitespace_validation_error(self):
        """Tests that providing a path that contains whitespace leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Path cannot contain whitespace characters.",
            owner="owner1", repo="repo1", path="README md", ref="main"
        )
    
    def test_get_file_content_ref_contains_whitespace_validation_error(self):
        """Tests that providing a ref that contains whitespace leads to ValidationError."""
        self.assert_error_behavior(
            func_to_call=get_file_contents,
            expected_exception_type=ValidationError,
            expected_message="Ref cannot contain whitespace characters.",
            owner="owner1", repo="repo1", path="README.md", ref="main "
        )
    

class TestRepositoryModels(TestGetFileContents):
    def test_git_actor(self):
        actor = models.GitActor(name="Alice", email="alice@example.com", date=datetime.datetime.now().isoformat())
        assert actor.name == "Alice"
        assert "@" in actor.email

    def test_commit_file_change(self):
        file_change = models.CommitFileChange(
            sha="a"*40,
            filename="file.txt",
            status="added",
            additions=1,
            deletions=0,
            changes=1,
            patch="diff --git a/file.txt b/file.txt"
        )
        assert file_change.status == "added"
        assert file_change.additions == 1

    def test_commit_stats(self):
        stats = models.CommitStats(total=10, additions=7, deletions=3)
        assert stats.total == 10
        assert stats.additions + stats.deletions == stats.total

    def test_commit_parent(self):
        parent = models.CommitParent(sha="b"*40, node_id=None)
        assert parent.sha.startswith("b")

    def test_tree(self):
        tree = models.Tree(sha="c"*40)
        assert tree.sha.startswith("c")

    def test_commit(self):
        actor = models.GitActor(name="Bob", email="bob@example.com", date=datetime.datetime.now().isoformat())
        tree = models.Tree(sha="d"*40)
        commit_nested = models.CommitNested(author=actor, committer=actor, message="msg", tree=tree, comment_count=0)
        parent = models.CommitParent(sha="e"*40, node_id=None)
        stats = models.CommitStats(total=2, additions=1, deletions=1)
        file_change = models.CommitFileChange(
            sha="f"*40,
            filename="file2.txt",
            status="modified",
            additions=1,
            deletions=1,
            changes=2
        )
        commit = models.Commit(
            sha="a"*40,  # Use valid hex string
            node_id="nodeid",
            commit=commit_nested,
            author=None,
            committer=None,
            parents=[parent],
            stats=stats,
            files=[file_change]
        )
        assert commit.sha.startswith("a")
        assert commit.commit.message == "msg"

    def test_get_root_directory_content_with_proper_structure(self):
        """Test that root directory listing works correctly with proper structure."""
        # Create a root directory listing with files and directories
        root_dir_content = [
            {'type': 'file', 'name': 'README.md', 'path': 'README.md', 'sha': 'readme_sha_123'},
            {'type': 'dir', 'name': 'src', 'path': 'src', 'sha': 'src_dir_sha_456'},
            {'type': 'file', 'name': 'config.json', 'path': 'config.json', 'sha': 'config_sha_789'}
        ]
        
        # Fix: Use empty string for path key, not "/" - as that's how it's stored in the database
        DB['FileContents'][f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:"] = root_dir_content
        
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="/", ref=self.MAIN_BRANCH)
        self.assertEqual(result, root_dir_content)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_get_root_directory_content_empty_repository(self):
        """Test that root directory listing returns empty list for empty repository."""
        # Ensure no root directory listing exists
        # Fix: Use empty string for path key, not "/" - as that's how it's stored in the database
        root_dir_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:"
        if root_dir_key in DB['FileContents']:
            del DB['FileContents'][root_dir_key]
        
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path="/", ref=self.MAIN_BRANCH)
        self.assertEqual(result, [])
        self.assertIsInstance(result, list)

    def test_dynamic_directory_generation_with_files(self):
        """Test dynamic directory generation when directory key is missing but files exist."""
        # Setup: Add files in a directory but don't add the directory listing key
        test_dir_path = "test_dynamic_dir"
        
        # Add files in the directory
        file1_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{test_dir_path}/file1.txt"
        file2_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{test_dir_path}/file2.py"
        
        DB['FileContents'][file1_key] = {
            'type': 'file',
            'size': 100,
            'name': 'file1.txt',
            'path': f'{test_dir_path}/file1.txt',
            'sha': 'file1sha123456789',
            'content': 'VGVzdCBjb250ZW50'
        }
        
        DB['FileContents'][file2_key] = {
            'type': 'file',
            'size': 200,
            'name': 'file2.py',
            'path': f'{test_dir_path}/file2.py',
            'sha': 'file2sha987654321',
            'content': 'cHl0aG9uIGNvZGU='
        }
        
        # Ensure the directory key doesn't exist
        dir_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{test_dir_path}/"
        if dir_key in DB['FileContents']:
            del DB['FileContents'][dir_key]
        
        # Test: Request directory listing
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path=test_dir_path, ref=self.MAIN_BRANCH)
        
        # Verify: Should return dynamically generated directory listing
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        
        # Check that both files are included
        file_names = [item['name'] for item in result]
        self.assertIn('file1.txt', file_names)
        self.assertIn('file2.py', file_names)
        
        # Verify file details
        for item in result:
            self.assertEqual(item['type'], 'file')
            if item['name'] == 'file1.txt':
                self.assertEqual(item['size'], 100)
                self.assertEqual(item['sha'], 'file1sha123456789')
            elif item['name'] == 'file2.py':
                self.assertEqual(item['size'], 200)
                self.assertEqual(item['sha'], 'file2sha987654321')
        
        # Cleanup
        del DB['FileContents'][file1_key]
        del DB['FileContents'][file2_key]

    def test_dynamic_directory_generation_with_subdirectories(self):
        """Test dynamic directory generation with nested subdirectories."""
        # Setup: Add files in nested subdirectories
        base_dir = "nested_test"
        
        # Add files in subdirectories
        subdir1_file_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{base_dir}/subdir1/nested_file.txt"
        subdir2_file_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{base_dir}/subdir2/another_file.py"
        
        DB['FileContents'][subdir1_file_key] = {
            'type': 'file',
            'size': 150,
            'name': 'nested_file.txt',
            'path': f'{base_dir}/subdir1/nested_file.txt',
            'sha': 'nestedsha123',
            'content': 'bmVzdGVkIGNvbnRlbnQ='
        }
        
        DB['FileContents'][subdir2_file_key] = {
            'type': 'file',
            'size': 250,
            'name': 'another_file.py',
            'path': f'{base_dir}/subdir2/another_file.py',
            'sha': 'anothersha456',
            'content': 'cHl0aG9uIG5lc3RlZA=='
        }
        
        # Ensure the base directory key doesn't exist
        dir_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{base_dir}/"
        if dir_key in DB['FileContents']:
            del DB['FileContents'][dir_key]
        
        # Test: Request base directory listing
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path=base_dir, ref=self.MAIN_BRANCH)
        
        # Verify: Should return dynamically generated directory listing with subdirectories
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        
        # Check that both subdirectories are included
        dir_names = [item['name'] for item in result]
        self.assertIn('subdir1', dir_names)
        self.assertIn('subdir2', dir_names)
        
        # Verify directory details
        for item in result:
            self.assertEqual(item['type'], 'dir')
            self.assertEqual(item['size'], 0)
            self.assertIn(item['name'], ['subdir1', 'subdir2'])
            self.assertEqual(item['path'], f"{base_dir}/{item['name']}")
        
        # Cleanup
        del DB['FileContents'][subdir1_file_key]
        del DB['FileContents'][subdir2_file_key]

    def test_dynamic_directory_generation_mixed_content(self):
        """Test dynamic directory generation with both files and subdirectories."""
        # Setup: Add both direct files and files in subdirectories
        mixed_dir = "mixed_content"
        
        # Direct file in the directory
        direct_file_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{mixed_dir}/direct_file.md"
        # File in subdirectory
        nested_file_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{mixed_dir}/subdir/nested_file.txt"
        
        DB['FileContents'][direct_file_key] = {
            'type': 'file',
            'size': 300,
            'name': 'direct_file.md',
            'path': f'{mixed_dir}/direct_file.md',
            'sha': 'directsha789',
            'content': 'bWFya2Rvd24gY29udGVudA=='
        }
        
        DB['FileContents'][nested_file_key] = {
            'type': 'file',
            'size': 400,
            'name': 'nested_file.txt',
            'path': f'{mixed_dir}/subdir/nested_file.txt',
            'sha': 'nestedsha012',
            'content': 'bmVzdGVkIGZpbGUgY29udGVudA=='
        }
        
        # Ensure the directory key doesn't exist
        dir_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{mixed_dir}/"
        if dir_key in DB['FileContents']:
            del DB['FileContents'][dir_key]
        
        # Test: Request directory listing
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path=mixed_dir, ref=self.MAIN_BRANCH)
        
        # Verify: Should return both file and directory
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        
        # Separate files and directories
        files = [item for item in result if item['type'] == 'file']
        dirs = [item for item in result if item['type'] == 'dir']
        
        self.assertEqual(len(files), 1)
        self.assertEqual(len(dirs), 1)
        
        # Verify file details
        file_item = files[0]
        self.assertEqual(file_item['name'], 'direct_file.md')
        self.assertEqual(file_item['size'], 300)
        self.assertEqual(file_item['sha'], 'directsha789')
        
        # Verify directory details
        dir_item = dirs[0]
        self.assertEqual(dir_item['name'], 'subdir')
        self.assertEqual(dir_item['type'], 'dir')
        self.assertEqual(dir_item['size'], 0)
        
        # Cleanup
        del DB['FileContents'][direct_file_key]
        del DB['FileContents'][nested_file_key]

    def test_dynamic_directory_generation_no_matching_files(self):
        """Test that NotFoundError is raised when no files match the directory path."""
        # Test: Request directory that doesn't exist and has no files
        nonexistent_dir = "completely_nonexistent_directory"
        
        with self.assertRaises(NotFoundError) as context:
            get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path=nonexistent_dir, ref=self.MAIN_BRANCH)
        
        # Verify error message contains expected information
        error_msg = str(context.exception)
        self.assertIn(nonexistent_dir, error_msg)
        self.assertIn("not found", error_msg)

    def test_file_content_text_encoding_conversion(self):
        """Test text encoding to base64 conversion for file content."""
        # Setup: Add a file with text encoding
        text_file_path = "text_file.txt"
        file_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{text_file_path}"
        
        # Add file with text encoding (not base64)
        DB['FileContents'][file_key] = {
            'type': 'file',
            'size': 100,
            'name': 'text_file.txt',
            'path': text_file_path,
            'sha': 'textfilesha123',
            'content': 'This is plain text content',
            'encoding': 'text'  # This should trigger conversion to base64
        }
        
        # Test: Request file content
        result = get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path=text_file_path, ref=self.MAIN_BRANCH)
        
        # Verify: Should return file with base64 encoded content
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'file')
        self.assertEqual(result['encoding'], 'base64')
        
        # Verify content is base64 encoded
        import base64
        decoded_content = base64.b64decode(result['content']).decode('utf-8')
        self.assertEqual(decoded_content, 'This is plain text content')
        
        # Cleanup
        del DB['FileContents'][file_key]

    def test_invalid_content_type_error(self):
        """Test that NotFoundError is raised for invalid content type."""
        # Setup: Add invalid content type (not dict or list)
        invalid_file_path = "invalid_content_file.txt"
        file_key = f"{self.REPO_ID}:{self.MAIN_COMMIT_SHA}:{invalid_file_path}"
        
        # Add invalid content type (string instead of dict/list)
        DB['FileContents'][file_key] = "invalid_content_type"
        
        # Test: Request file content should raise error
        with self.assertRaises(NotFoundError) as context:
            get_file_contents(owner=self.OWNER_LOGIN, repo=self.REPO_NAME, path=invalid_file_path, ref=self.MAIN_BRANCH)
        
        # Verify error message contains expected information
        error_msg = str(context.exception)
        self.assertIn("Invalid content type", error_msg)
        self.assertIn(invalid_file_path, error_msg)
        
        # Cleanup
        del DB['FileContents'][file_key]

if __name__ == '__main__':
    unittest.main()