import unittest
from unittest.mock import patch
import sys
import os
import copy

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

sys.path.append("APIs")
import google_cloud_storage


class TestGetIamPolicyFunction(unittest.TestCase):
    """Test cases for the getIamPolicy function with comprehensive coverage."""

    def setUp(self):
        """Set up test data before each test."""
        # Reset the DB to a known state
        google_cloud_storage.Buckets.DB["buckets"] = {
            "test-bucket-1": {
                "name": "test-bucket-1",
                "project": "test-project",
                "metageneration": "1",
                "iamPolicy": {
                    "bindings": [
                        {
                            "role": "roles/storage.admin",
                            "members": ["user:admin@example.com", "group:admins@example.com"]
                        },
                        {
                            "role": "roles/storage.objectViewer", 
                            "members": ["user:viewer@example.com"],
                            "condition": {
                                "title": "View access only",
                                "description": "Allow viewing objects only",
                                "expression": "request.time.getHours() < 17"
                            }
                        }
                    ],
                    "version": 3
                }
            },
            "test-bucket-2": {
                "name": "test-bucket-2",
                "project": "test-project",
                "metageneration": "2",
                "iamPolicy": {
                    "bindings": [
                        {
                            "role": "roles/storage.legacyBucketReader",
                            "members": ["allUsers"]
                        }
                    ],
                    "version": 1
                }
            },
            "empty-policy-bucket": {
                "name": "empty-policy-bucket",
                "project": "test-project"
                # No iamPolicy field - should get default
            }
        }

    def tearDown(self):
        """Clean up after each test."""
        google_cloud_storage.Buckets.DB["buckets"] = {}

    # --- Success Cases ---

    def test_getIamPolicy_success_basic(self):
        """Test successful IAM policy retrieval with default parameters."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1")
        
        # Verify response structure
        self.assertIn("iamPolicy", result)
        iam_policy = result["iamPolicy"]
        
        # Verify all required fields are present
        self.assertIn("bindings", iam_policy)
        self.assertIn("etag", iam_policy)
        self.assertIn("kind", iam_policy)
        self.assertIn("resourceId", iam_policy)
        self.assertIn("version", iam_policy)
        
        # Verify values
        self.assertEqual(iam_policy["kind"], "storage#policy")
        self.assertEqual(iam_policy["resourceId"], "projects/_/buckets/test-bucket-1")
        self.assertEqual(iam_policy["version"], 3)  # Should use existing version
        
        # Verify bindings are present
        self.assertEqual(len(iam_policy["bindings"]), 2)

    def test_getIamPolicy_success_with_policy_version_1(self):
        """Test successful retrieval with policy version 1 (filters conditions)."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=1)
        
        iam_policy = result["iamPolicy"]
        self.assertEqual(iam_policy["version"], 1)
        
        # Verify conditions are filtered out for version 1
        for binding in iam_policy["bindings"]:
            self.assertNotIn("condition", binding)
            self.assertIn("role", binding)
            self.assertIn("members", binding)

    def test_getIamPolicy_success_with_policy_version_3(self):
        """Test successful retrieval with policy version 3 (preserves conditions)."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=3)
        
        iam_policy = result["iamPolicy"]
        self.assertEqual(iam_policy["version"], 3)
        
        # Check if any binding has a condition (should be preserved)
        has_condition = any("condition" in binding for binding in iam_policy["bindings"])
        self.assertTrue(has_condition)

    def test_getIamPolicy_success_with_user_project(self):
        """Test successful retrieval with user_project parameter."""
        result = google_cloud_storage.Buckets.getIamPolicy(
            "test-bucket-1", 
            user_project="billing-project"
        )
        
        self.assertIn("iamPolicy", result)
        iam_policy = result["iamPolicy"]
        self.assertEqual(iam_policy["resourceId"], "projects/_/buckets/test-bucket-1")

    def test_getIamPolicy_success_empty_policy_bucket(self):
        """Test successful retrieval for bucket with no existing IAM policy."""
        result = google_cloud_storage.Buckets.getIamPolicy("empty-policy-bucket")
        
        self.assertIn("iamPolicy", result)
        iam_policy = result["iamPolicy"]
        
        # Should have default structure
        self.assertIn("bindings", iam_policy)
        self.assertIn("etag", iam_policy)
        self.assertIn("kind", iam_policy)
        self.assertIn("resourceId", iam_policy)
        self.assertIn("version", iam_policy)
        
        # Default version should be 1
        self.assertEqual(iam_policy["version"], 1)
        self.assertEqual(iam_policy["bindings"], [])

    def test_getIamPolicy_success_existing_version_1_bucket(self):
        """Test successful retrieval for bucket with existing version 1 policy."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-2")
        
        iam_policy = result["iamPolicy"]
        self.assertEqual(iam_policy["version"], 1)  # Should use existing version
        self.assertEqual(len(iam_policy["bindings"]), 1)

    # --- Type Validation Tests ---

    def test_getIamPolicy_invalid_bucket_type_int(self):
        """Test getIamPolicy with integer bucket type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.getIamPolicy(123)
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_getIamPolicy_invalid_bucket_type_none(self):
        """Test getIamPolicy with None bucket type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.getIamPolicy(None)
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_getIamPolicy_invalid_bucket_type_list(self):
        """Test getIamPolicy with list bucket type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.getIamPolicy(["bucket"])
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_getIamPolicy_invalid_policy_version_type_string(self):
        """Test getIamPolicy with string policy version type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version="1")
        self.assertIn("Argument 'options_requested_policy_version' must be an integer", str(context.exception))

    def test_getIamPolicy_invalid_policy_version_type_float(self):
        """Test getIamPolicy with float policy version type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=1.5)
        self.assertIn("Argument 'options_requested_policy_version' must be an integer", str(context.exception))

    def test_getIamPolicy_invalid_user_project_type_int(self):
        """Test getIamPolicy with integer user_project type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", user_project=123)
        self.assertIn("Argument 'user_project' must be a string or None", str(context.exception))

    def test_getIamPolicy_invalid_user_project_type_list(self):
        """Test getIamPolicy with list user_project type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", user_project=["project"])
        self.assertIn("Argument 'user_project' must be a string or None", str(context.exception))

    # --- Bucket Name Validation Tests ---

    def test_getIamPolicy_empty_bucket_name(self):
        """Test getIamPolicy with empty bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("")
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_getIamPolicy_whitespace_only_bucket_name(self):
        """Test getIamPolicy with whitespace-only bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("   ")
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_getIamPolicy_bucket_name_too_short(self):
        """Test getIamPolicy with bucket name too short."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("ab")
        self.assertIn("must be between 3 and 63 characters long", str(context.exception))

    def test_getIamPolicy_bucket_name_too_long(self):
        """Test getIamPolicy with bucket name too long."""
        long_name = "a" * 64
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy(long_name)
        self.assertIn("must be between 3 and 63 characters long", str(context.exception))

    def test_getIamPolicy_bucket_name_starts_with_dot(self):
        """Test getIamPolicy with bucket name starting with dot."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy(".test-bucket")
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_getIamPolicy_bucket_name_ends_with_dot(self):
        """Test getIamPolicy with bucket name ending with dot."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket.")
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_getIamPolicy_bucket_name_consecutive_dots(self):
        """Test getIamPolicy with bucket name containing consecutive dots."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test..bucket")
        self.assertIn("consecutive dots", str(context.exception))

    # --- Policy Version Validation Tests ---

    def test_getIamPolicy_invalid_policy_version_zero(self):
        """Test getIamPolicy with policy version 0."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=0)
        self.assertIn("must be >= 1 if specified", str(context.exception))

    def test_getIamPolicy_invalid_policy_version_negative(self):
        """Test getIamPolicy with negative policy version."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=-1)
        self.assertIn("must be >= 1 if specified", str(context.exception))

    def test_getIamPolicy_invalid_policy_version_unsupported(self):
        """Test getIamPolicy with unsupported policy version."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=2)
        self.assertIn("Invalid policy version: 2", str(context.exception))
        self.assertIn("Supported versions are 1 and 3", str(context.exception))

    def test_getIamPolicy_invalid_policy_version_large(self):
        """Test getIamPolicy with large unsupported policy version."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=999)
        self.assertIn("Invalid policy version: 999", str(context.exception))

    # --- User Project Validation Tests ---

    def test_getIamPolicy_empty_user_project(self):
        """Test getIamPolicy with empty user_project."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", user_project="")
        self.assertIn("cannot be empty or contain only whitespace if specified", str(context.exception))

    def test_getIamPolicy_whitespace_user_project(self):
        """Test getIamPolicy with whitespace-only user_project."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", user_project="   ")
        self.assertIn("cannot be empty or contain only whitespace if specified", str(context.exception))

    # --- Business Logic Error Tests ---

    def test_getIamPolicy_bucket_not_found(self):
        """Test getIamPolicy with non-existent bucket."""
        with self.assertRaises(Exception) as context:  # BucketNotFoundError
            google_cloud_storage.Buckets.getIamPolicy("non-existent-bucket")
        self.assertIn("not found", str(context.exception))

    # --- Edge Cases ---

    def test_getIamPolicy_bucket_name_minimum_valid_length(self):
        """Test getIamPolicy with minimum valid bucket name length (3 characters)."""
        # Create a bucket with 3 characters
        google_cloud_storage.Buckets.DB["buckets"]["abc"] = {
            "name": "abc",
            "metageneration": "1"
        }
        
        result = google_cloud_storage.Buckets.getIamPolicy("abc")
        
        self.assertIn("iamPolicy", result)
        self.assertEqual(result["iamPolicy"]["resourceId"], "projects/_/buckets/abc")

    def test_getIamPolicy_bucket_name_maximum_valid_length(self):
        """Test getIamPolicy with maximum valid bucket name length (63 characters)."""
        # Create a bucket with 63 characters
        bucket_name = "a" * 63
        google_cloud_storage.Buckets.DB["buckets"][bucket_name] = {
            "name": bucket_name,
            "metageneration": "1"
        }
        
        result = google_cloud_storage.Buckets.getIamPolicy(bucket_name)
        
        self.assertIn("iamPolicy", result)
        self.assertEqual(result["iamPolicy"]["resourceId"], f"projects/_/buckets/{bucket_name}")

    def test_getIamPolicy_user_project_none(self):
        """Test getIamPolicy with user_project explicitly None."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", user_project=None)
        
        self.assertIn("iamPolicy", result)

    def test_getIamPolicy_policy_version_none(self):
        """Test getIamPolicy with options_requested_policy_version explicitly None."""
        result = google_cloud_storage.Buckets.getIamPolicy(
            "test-bucket-1", 
            options_requested_policy_version=None
        )
        
        self.assertIn("iamPolicy", result)
        # Should use existing version from bucket data (3)
        self.assertEqual(result["iamPolicy"]["version"], 3)

    # --- Response Structure Verification Tests ---

    def test_getIamPolicy_response_structure_complete(self):
        """Test that getIamPolicy response has correct structure."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1")
        
        # Verify response structure
        self.assertIn("iamPolicy", result)
        self.assertIsInstance(result["iamPolicy"], dict)
        
        # Verify all required fields
        iam_policy = result["iamPolicy"]
        required_fields = ["bindings", "etag", "kind", "resourceId", "version"]
        for field in required_fields:
            self.assertIn(field, iam_policy)

    def test_getIamPolicy_etag_generation(self):
        """Test that etag is consistently generated."""
        result1 = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1")
        result2 = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1")
        
        # ETags should be the same for same policy content
        self.assertEqual(result1["iamPolicy"]["etag"], result2["iamPolicy"]["etag"])

    def test_getIamPolicy_bindings_structure(self):
        """Test that bindings have correct structure."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1")
        
        bindings = result["iamPolicy"]["bindings"]
        self.assertIsInstance(bindings, list)
        
        for binding in bindings:
            self.assertIn("role", binding)
            self.assertIn("members", binding)
            self.assertIsInstance(binding["members"], list)

    def test_getIamPolicy_condition_filtering_version_1(self):
        """Test that conditions are properly filtered for version 1."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=1)
        
        bindings = result["iamPolicy"]["bindings"]
        for binding in bindings:
            # Version 1 should not have conditions
            self.assertNotIn("condition", binding)

    def test_getIamPolicy_condition_preservation_version_3(self):
        """Test that conditions are preserved for version 3."""
        result = google_cloud_storage.Buckets.getIamPolicy("test-bucket-1", options_requested_policy_version=3)
        
        bindings = result["iamPolicy"]["bindings"]
        
        # Find the binding that should have a condition
        condition_binding = None
        for binding in bindings:
            if "condition" in binding:
                condition_binding = binding
                break
        
        self.assertIsNotNone(condition_binding)
        condition = condition_binding["condition"]
        self.assertIn("title", condition)
        self.assertIn("expression", condition)


if __name__ == "__main__":
    unittest.main() 