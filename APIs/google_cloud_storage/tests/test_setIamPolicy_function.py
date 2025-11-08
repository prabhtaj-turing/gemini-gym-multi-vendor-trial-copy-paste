import unittest
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import google_cloud_storage.Buckets
from google_cloud_storage.SimulationEngine.custom_errors import BucketNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestSetIamPolicyFunction(BaseTestCaseWithErrorHandler):
    
    def setUp(self):
        """Set up test environment before each test."""
        # Clear the database and add test data
        google_cloud_storage.Buckets.DB["buckets"] = {
            "test-bucket": {
                "name": "test-bucket",
                "project": "test-project",
                "metageneration": "1",
                "softDeleted": False,
                "objects": [],
                "iamPolicy": {"bindings": []},
                "storageLayout": {}
            }
        }

    def test_setIamPolicy_success_basic(self):
        """Test successful policy setting with basic binding."""
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:admin@example.com"]
                }
            ]
        }
        
        result = google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
        
        self.assertIn("bindings", result)
        self.assertIn("etag", result)
        self.assertIn("kind", result)
        self.assertIn("resourceId", result)
        self.assertIn("version", result)
        
        self.assertEqual(result["kind"], "storage#policy")
        self.assertEqual(result["resourceId"], "projects/_/buckets/test-bucket")
        self.assertEqual(result["version"], 1)
        self.assertEqual(len(result["bindings"]), 1)
        self.assertEqual(result["bindings"][0]["role"], "roles/storage.admin")
        self.assertEqual(result["bindings"][0]["members"], ["user:admin@example.com"])

    def test_setIamPolicy_success_multiple_bindings(self):
        """Test successful policy setting with multiple bindings."""
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:admin@example.com"]
                },
                {
                    "role": "roles/storage.objectViewer",
                    "members": ["user:viewer@example.com", "group:viewers@example.com"]
                }
            ]
        }
        
        result = google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
        
        self.assertEqual(len(result["bindings"]), 2)
        self.assertEqual(result["bindings"][0]["role"], "roles/storage.admin")
        self.assertEqual(result["bindings"][1]["role"], "roles/storage.objectViewer")
        self.assertEqual(len(result["bindings"][1]["members"]), 2)

    def test_setIamPolicy_success_with_condition(self):
        """Test successful policy setting with conditional binding."""
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:admin@example.com"],
                    "condition": {
                        "title": "Test condition",
                        "expression": "request.time.getHours() < 12",
                        "description": "Only allow morning access"
                    }
                }
            ]
        }
        
        result = google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
        
        self.assertEqual(len(result["bindings"]), 1)
        self.assertIn("condition", result["bindings"][0])
        self.assertEqual(result["bindings"][0]["condition"]["title"], "Test condition")
        self.assertEqual(result["bindings"][0]["condition"]["expression"], "request.time.getHours() < 12")

    def test_setIamPolicy_success_with_version(self):
        """Test successful policy setting with specific version."""
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:admin@example.com"]
                }
            ],
            "version": 3
        }
        
        result = google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
        
        self.assertEqual(result["version"], 3)

    def test_setIamPolicy_success_all_valid_roles(self):
        """Test successful policy setting with all valid roles."""
        valid_roles = [
            "roles/storage.admin",
            "roles/storage.objectViewer",
            "roles/storage.objectCreator",
            "roles/storage.objectAdmin",
            "roles/storage.legacyObjectReader",
            "roles/storage.legacyObjectOwner",
            "roles/storage.legacyBucketReader",
            "roles/storage.legacyBucketWriter",
            "roles/storage.legacyBucketOwner"
        ]
        
        for role in valid_roles:
            policy = {
                "bindings": [
                    {
                        "role": role,
                        "members": ["user:test@example.com"]
                    }
                ]
            }
            
            result = google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
            self.assertEqual(result["bindings"][0]["role"], role)

    def test_setIamPolicy_success_all_valid_members(self):
        """Test successful policy setting with all valid member formats."""
        valid_members = [
            "allUsers",
            "allAuthenticatedUsers",
            "user:test@example.com",
            "serviceAccount:service@project.iam.gserviceaccount.com",
            "group:group@example.com",
            "domain:example.com",
            "projectOwner:project-123",
            "projectEditor:project-123",
            "projectViewer:project-123"
        ]
        
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": valid_members
                }
            ]
        }
        
        result = google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
        self.assertEqual(result["bindings"][0]["members"], valid_members)

    # --- Type Error Tests ---

    def test_setIamPolicy_bucket_type_error(self):
        """Test TypeError when bucket is not a string."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["user:test@example.com"]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=TypeError,
            expected_message="Argument 'bucket' must be a string, got int.",
            bucket=123,
            policy=policy
        )

    def test_setIamPolicy_policy_type_error(self):
        """Test TypeError when policy is not a dictionary."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=TypeError,
            expected_message="Argument 'policy' must be a dictionary, got str.",
            bucket="test-bucket",
            policy="not a dict"
        )

    def test_setIamPolicy_user_project_type_error(self):
        """Test TypeError when user_project is not a string."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["user:test@example.com"]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=TypeError,
            expected_message="Argument 'user_project' must be a string or None, got int.",
            bucket="test-bucket",
            policy=policy,
            user_project=123
        )

    # --- ValueError Tests ---

    def test_setIamPolicy_empty_bucket_error(self):
        """Test ValueError when bucket is empty."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["user:test@example.com"]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Argument 'bucket' cannot be empty or contain only whitespace.",
            bucket="",
            policy=policy
        )

    def test_setIamPolicy_bucket_too_short_error(self):
        """Test ValueError when bucket name is too short."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["user:test@example.com"]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Bucket name must be between 3 and 63 characters long.",
            bucket="ab",
            policy=policy
        )

    def test_setIamPolicy_bucket_too_long_error(self):
        """Test ValueError when bucket name is too long."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["user:test@example.com"]}]}
        long_bucket = "a" * 64
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Bucket name must be between 3 and 63 characters long.",
            bucket=long_bucket,
            policy=policy
        )

    def test_setIamPolicy_bucket_dots_error(self):
        """Test ValueError when bucket name has invalid dots."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["user:test@example.com"]}]}
        
        invalid_names = [".bucket", "bucket.", "bu..cket"]
        for name in invalid_names:
            self.assert_error_behavior(
                func_to_call=google_cloud_storage.Buckets.setIamPolicy,
                expected_exception_type=ValueError,
                expected_message="Bucket name cannot start or end with dots, or contain consecutive dots.",
                bucket=name,
                policy=policy
            )

    def test_setIamPolicy_empty_policy_error(self):
        """Test ValueError when policy is empty."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Argument 'policy' cannot be empty.",
            bucket="test-bucket",
            policy={}
        )

    def test_setIamPolicy_empty_user_project_error(self):
        """Test ValueError when user_project is empty string."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["user:test@example.com"]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Argument 'user_project' cannot be empty or contain only whitespace if specified.",
            bucket="test-bucket",
            policy=policy,
            user_project=""
        )

    def test_setIamPolicy_missing_bindings_error(self):
        """Test ValueError when policy missing bindings field."""
        policy = {"version": 1}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings': Field required",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_bindings_not_list_error(self):
        """Test ValueError when bindings is not a list."""
        policy = {"bindings": "not a list"}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings': Input should be a valid list",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_binding_not_dict_error(self):
        """Test ValueError when binding is not a dictionary."""
        policy = {"bindings": ["not a dict"]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0': Input should be a valid dictionary or instance of IamBindingModel",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_missing_role_error(self):
        """Test ValueError when binding missing role field."""
        policy = {"bindings": [{"members": ["user:test@example.com"]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> role': Field required",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_role_not_string_error(self):
        """Test ValueError when role is not a string."""
        policy = {"bindings": [{"role": 123, "members": ["user:test@example.com"]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> role': Input should be a valid string",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_invalid_role_error(self):
        """Test ValueError when role is invalid."""
        policy = {"bindings": [{"role": "invalid/role", "members": ["user:test@example.com"]}]}
        
        try:
            google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
            self.fail("Expected ValueError to be raised")
        except ValueError as e:
            error_msg = str(e)
            self.assertIn("Policy validation error in 'bindings -> 0 -> role'", error_msg)
            self.assertIn("Invalid role 'invalid/role'", error_msg)
            self.assertIn("Valid roles", error_msg)

    def test_setIamPolicy_missing_members_error(self):
        """Test ValueError when binding missing members field."""
        policy = {"bindings": [{"role": "roles/storage.admin"}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> members': Field required",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_members_not_list_error(self):
        """Test ValueError when members is not a list."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": "not a list"}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> members': Input should be a valid list",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_empty_members_error(self):
        """Test ValueError when members list is empty."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": []}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> members': List should have at least 1 item after validation, not 0",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_member_not_string_error(self):
        """Test ValueError when member is not a string."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": [123]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> members -> 0': Input should be a valid string",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_invalid_member_format_error(self):
        """Test ValueError when member format is invalid."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["invalid:format"]}]}
        
        try:
            google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
            self.fail("Expected ValueError to be raised")
        except ValueError as e:
            error_msg = str(e)
            self.assertIn("Policy validation error in 'bindings -> 0 -> members'", error_msg)
            self.assertIn("Invalid member format 'invalid:format'", error_msg)
            self.assertIn("Must start with one of", error_msg)

    def test_setIamPolicy_invalid_email_format_error(self):
        """Test ValueError when email format in member is invalid."""
        invalid_emails = [
            "user:invalid-email",  # Missing @ symbol
            "serviceAccount:no-at-sign",  # Missing @ symbol
            "group:"  # Empty email part
        ]
        
        for email in invalid_emails:
            policy = {"bindings": [{"role": "roles/storage.admin", "members": [email]}]}
            
            try:
                google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
                self.fail(f"Expected ValueError to be raised for email: {email}")
            except ValueError as e:
                error_msg = str(e)
                self.assertIn("Policy validation error in 'bindings -> 0 -> members'", error_msg)
                self.assertIn(f"Invalid email format in member '{email}'", error_msg)

    def test_setIamPolicy_bucket_not_found_error(self):
        """Test BucketNotFoundError when bucket doesn't exist."""
        policy = {"bindings": [{"role": "roles/storage.admin", "members": ["user:test@example.com"]}]}
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=BucketNotFoundError,
            expected_message="Bucket 'nonexistent-bucket' not found.",
            bucket="nonexistent-bucket",
            policy=policy
        )

    def test_setIamPolicy_condition_not_dict_error(self):
        """Test ValueError when condition is not a dictionary."""
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:test@example.com"],
                    "condition": "not a dict"
                }
            ]
        }
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> condition': Input should be a valid dictionary or instance of IamConditionModel",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_condition_missing_expression_error(self):
        """Test ValueError when condition missing expression field."""
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:test@example.com"],
                    "condition": {
                        "title": "Test condition"
                    }
                }
            ]
        }
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> condition -> expression': Field required",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_condition_missing_title_error(self):
        """Test ValueError when condition missing title field."""
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:test@example.com"],
                    "condition": {
                        "expression": "request.time.getHours() < 12"
                    }
                }
            ]
        }
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.setIamPolicy,
            expected_exception_type=ValueError,
            expected_message="Policy validation error in 'bindings -> 0 -> condition -> title': Field required",
            bucket="test-bucket",
            policy=policy
        )

    def test_setIamPolicy_database_persistence(self):
        """Test that the policy is properly stored in the database."""
        policy = {
            "bindings": [
                {
                    "role": "roles/storage.admin",
                    "members": ["user:admin@example.com"]
                }
            ]
        }
        
        result = google_cloud_storage.Buckets.setIamPolicy("test-bucket", policy)
        
        # Check that the policy was stored in the database
        stored_policy = google_cloud_storage.Buckets.DB["buckets"]["test-bucket"]["iamPolicy"]
        self.assertEqual(stored_policy["bindings"], result["bindings"])
        self.assertEqual(stored_policy["etag"], result["etag"])
        self.assertEqual(stored_policy["kind"], result["kind"])
        self.assertEqual(stored_policy["resourceId"], result["resourceId"])
        self.assertEqual(stored_policy["version"], result["version"])


if __name__ == '__main__':
    unittest.main() 