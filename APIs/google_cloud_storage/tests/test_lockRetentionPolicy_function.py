import unittest
from unittest.mock import patch
import sys
import os
import copy

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

sys.path.append("APIs")
import google_cloud_storage


class TestLockRetentionPolicyFunction(unittest.TestCase):
    """Test cases for the lockRetentionPolicy function with comprehensive coverage."""

    def setUp(self):
        """Set up test data before each test."""
        # Reset the DB to a known state
        google_cloud_storage.Buckets.DB["buckets"] = {
            "test-bucket-1": {
                "name": "test-bucket-1",
                "project": "test-project",
                "metageneration": "1",
                "retentionPolicyLocked": False,
                "retentionPolicy": {
                    "effectiveTime": "2024-01-01T00:00:00Z",
                    "isLocked": False,
                    "retentionPeriod": "86400"
                },
                "location": "us-central1",
                "storageClass": "STANDARD",
                "timeCreated": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z"
            },
            "test-bucket-2": {
                "name": "test-bucket-2",
                "project": "test-project",
                "metageneration": "5",
                "retentionPolicyLocked": False,
                "retentionPolicy": {
                    "effectiveTime": "2024-01-01T00:00:00Z",
                    "isLocked": False,
                    "retentionPeriod": "172800"
                }
            },
            "test-bucket-locked": {
                "name": "test-bucket-locked",
                "project": "test-project", 
                "metageneration": "3",
                "retentionPolicyLocked": True,
                "retentionPolicy": {
                    "effectiveTime": "2024-01-01T00:00:00Z",
                    "isLocked": True,
                    "retentionPeriod": "259200"
                }
            }
        }

    def tearDown(self):
        """Clean up after each test."""
        google_cloud_storage.Buckets.DB["buckets"] = {}

    # --- Success Cases ---

    def test_lockRetentionPolicy_success_basic(self):
        """Test successful retention policy locking."""
        result = google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1")
        
        self.assertIn("bucket", result)
        bucket = result["bucket"]
        
        # Verify the retention policy is locked
        self.assertTrue(bucket["retentionPolicyLocked"])
        
        # Verify metageneration was incremented
        self.assertEqual(bucket["metageneration"], "2")
        
        # Verify bucket name is correct
        self.assertEqual(bucket["name"], "test-bucket-1")

    def test_lockRetentionPolicy_success_with_user_project(self):
        """Test successful retention policy locking with user_project."""
        result = google_cloud_storage.Buckets.lockRetentionPolicy(
            "test-bucket-2", "5", user_project="billing-project"
        )
        
        self.assertIn("bucket", result)
        bucket = result["bucket"]
        
        # Verify the retention policy is locked
        self.assertTrue(bucket["retentionPolicyLocked"])
        
        # Verify metageneration was incremented
        self.assertEqual(bucket["metageneration"], "6")

    def test_lockRetentionPolicy_success_higher_metageneration(self):
        """Test successful locking with higher metageneration number."""
        result = google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-2", "5")
        
        bucket = result["bucket"]
        self.assertTrue(bucket["retentionPolicyLocked"])
        self.assertEqual(bucket["metageneration"], "6")

    def test_lockRetentionPolicy_success_user_project_none(self):
        """Test successful locking with user_project explicitly None."""
        result = google_cloud_storage.Buckets.lockRetentionPolicy(
            "test-bucket-1", "1", user_project=None
        )
        
        self.assertIn("bucket", result)
        self.assertTrue(result["bucket"]["retentionPolicyLocked"])

    # --- Type Validation Tests ---

    def test_lockRetentionPolicy_invalid_bucket_type_int(self):
        """Test lockRetentionPolicy with integer bucket type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy(123, "1")
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_lockRetentionPolicy_invalid_bucket_type_none(self):
        """Test lockRetentionPolicy with None bucket type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy(None, "1")
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_lockRetentionPolicy_invalid_bucket_type_list(self):
        """Test lockRetentionPolicy with list bucket type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy(["bucket"], "1")
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_lockRetentionPolicy_invalid_metageneration_type_int(self):
        """Test lockRetentionPolicy with integer metageneration type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", 1)
        self.assertIn("Argument 'if_metageneration_match' must be a string", str(context.exception))

    def test_lockRetentionPolicy_invalid_metageneration_type_none(self):
        """Test lockRetentionPolicy with None metageneration type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", None)
        self.assertIn("Argument 'if_metageneration_match' must be a string", str(context.exception))

    def test_lockRetentionPolicy_invalid_user_project_type_int(self):
        """Test lockRetentionPolicy with integer user_project type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1", user_project=123)
        self.assertIn("Argument 'user_project' must be a string or None", str(context.exception))

    def test_lockRetentionPolicy_invalid_user_project_type_list(self):
        """Test lockRetentionPolicy with list user_project type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1", user_project=["project"])
        self.assertIn("Argument 'user_project' must be a string or None", str(context.exception))

    # --- Bucket Name Validation Tests ---

    def test_lockRetentionPolicy_empty_bucket_name(self):
        """Test lockRetentionPolicy with empty bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("", "1")
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_lockRetentionPolicy_whitespace_only_bucket_name(self):
        """Test lockRetentionPolicy with whitespace-only bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("   ", "1")
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_lockRetentionPolicy_bucket_name_too_short(self):
        """Test lockRetentionPolicy with bucket name too short."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("ab", "1")
        self.assertIn("must be between 3 and 63 characters long", str(context.exception))

    def test_lockRetentionPolicy_bucket_name_too_long(self):
        """Test lockRetentionPolicy with bucket name too long."""
        long_name = "a" * 64
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy(long_name, "1")
        self.assertIn("must be between 3 and 63 characters long", str(context.exception))

    def test_lockRetentionPolicy_bucket_name_starts_with_dot(self):
        """Test lockRetentionPolicy with bucket name starting with dot."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy(".test-bucket", "1")
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_lockRetentionPolicy_bucket_name_ends_with_dot(self):
        """Test lockRetentionPolicy with bucket name ending with dot."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket.", "1")
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_lockRetentionPolicy_bucket_name_consecutive_dots(self):
        """Test lockRetentionPolicy with bucket name containing consecutive dots."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test..bucket", "1")
        self.assertIn("consecutive dots", str(context.exception))

    # --- Metageneration Validation Tests ---

    def test_lockRetentionPolicy_empty_metageneration(self):
        """Test lockRetentionPolicy with empty metageneration."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "")
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_lockRetentionPolicy_whitespace_metageneration(self):
        """Test lockRetentionPolicy with whitespace-only metageneration."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "   ")
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_lockRetentionPolicy_non_numeric_metageneration(self):
        """Test lockRetentionPolicy with non-numeric metageneration."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "abc")
        self.assertIn("must be a numeric string", str(context.exception))

    def test_lockRetentionPolicy_metageneration_with_letters(self):
        """Test lockRetentionPolicy with metageneration containing letters."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1a2")
        self.assertIn("must be a numeric string", str(context.exception))

    def test_lockRetentionPolicy_metageneration_with_special_chars(self):
        """Test lockRetentionPolicy with metageneration containing special characters."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1-2")
        self.assertIn("must be a numeric string", str(context.exception))

    # --- User Project Validation Tests ---

    def test_lockRetentionPolicy_empty_user_project(self):
        """Test lockRetentionPolicy with empty user_project."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1", user_project="")
        self.assertIn("cannot be empty or contain only whitespace if specified", str(context.exception))

    def test_lockRetentionPolicy_whitespace_user_project(self):
        """Test lockRetentionPolicy with whitespace-only user_project."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1", user_project="   ")
        self.assertIn("cannot be empty or contain only whitespace if specified", str(context.exception))

    # --- Business Logic Error Tests ---

    def test_lockRetentionPolicy_bucket_not_found(self):
        """Test lockRetentionPolicy with non-existent bucket."""
        with self.assertRaises(Exception) as context:  # BucketNotFoundError
            google_cloud_storage.Buckets.lockRetentionPolicy("non-existent-bucket", "1")
        self.assertIn("not found", str(context.exception))

    def test_lockRetentionPolicy_metageneration_mismatch_lower(self):
        """Test lockRetentionPolicy with metageneration mismatch (lower)."""
        with self.assertRaises(Exception) as context:  # MetagenerationMismatchError
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-2", "4")
        self.assertIn("Metageneration mismatch", str(context.exception))
        self.assertIn("Required '4'", str(context.exception))
        self.assertIn("found '5'", str(context.exception))

    def test_lockRetentionPolicy_metageneration_mismatch_higher(self):
        """Test lockRetentionPolicy with metageneration mismatch (higher)."""
        with self.assertRaises(Exception) as context:  # MetagenerationMismatchError
            google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "2")
        self.assertIn("Metageneration mismatch", str(context.exception))
        self.assertIn("Required '2'", str(context.exception))
        self.assertIn("found '1'", str(context.exception))

    def test_lockRetentionPolicy_metageneration_zero_string(self):
        """Test lockRetentionPolicy with zero metageneration (valid numeric string)."""
        # Add bucket with metageneration 0
        google_cloud_storage.Buckets.DB["buckets"]["zero-meta"] = {
            "name": "zero-meta",
            "metageneration": "0",
            "retentionPolicyLocked": False
        }
        
        result = google_cloud_storage.Buckets.lockRetentionPolicy("zero-meta", "0")
        
        self.assertIn("bucket", result)
        self.assertTrue(result["bucket"]["retentionPolicyLocked"])
        self.assertEqual(result["bucket"]["metageneration"], "1")

    # --- Edge Cases ---

    def test_lockRetentionPolicy_bucket_name_minimum_valid_length(self):
        """Test lockRetentionPolicy with minimum valid bucket name length (3 characters)."""
        # Create a bucket with 3 characters
        google_cloud_storage.Buckets.DB["buckets"]["abc"] = {
            "name": "abc",
            "metageneration": "1",
            "retentionPolicyLocked": False
        }
        
        result = google_cloud_storage.Buckets.lockRetentionPolicy("abc", "1")
        
        self.assertIn("bucket", result)
        self.assertTrue(result["bucket"]["retentionPolicyLocked"])

    def test_lockRetentionPolicy_bucket_name_maximum_valid_length(self):
        """Test lockRetentionPolicy with maximum valid bucket name length (63 characters)."""
        # Create a bucket with 63 characters
        bucket_name = "a" * 63
        google_cloud_storage.Buckets.DB["buckets"][bucket_name] = {
            "name": bucket_name,
            "metageneration": "1",
            "retentionPolicyLocked": False
        }
        
        result = google_cloud_storage.Buckets.lockRetentionPolicy(bucket_name, "1")
        
        self.assertIn("bucket", result)
        self.assertTrue(result["bucket"]["retentionPolicyLocked"])

    def test_lockRetentionPolicy_large_metageneration_number(self):
        """Test lockRetentionPolicy with large metageneration number."""
        # Create bucket with large metageneration
        google_cloud_storage.Buckets.DB["buckets"]["large-meta"] = {
            "name": "large-meta",
            "metageneration": "999999",
            "retentionPolicyLocked": False
        }
        
        result = google_cloud_storage.Buckets.lockRetentionPolicy("large-meta", "999999")
        
        self.assertIn("bucket", result)
        self.assertTrue(result["bucket"]["retentionPolicyLocked"])
        self.assertEqual(result["bucket"]["metageneration"], "1000000")

    # --- State Verification Tests ---

    def test_lockRetentionPolicy_preserves_other_bucket_data(self):
        """Test that lockRetentionPolicy preserves other bucket data."""
        original_bucket = copy.deepcopy(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-1"])
        
        result = google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1")
        
        bucket = result["bucket"]
        
        # Verify retention policy was locked
        self.assertTrue(bucket["retentionPolicyLocked"])
        
        # Verify metageneration was incremented
        self.assertEqual(bucket["metageneration"], "2")
        
        # Verify other data is preserved
        self.assertEqual(bucket["name"], original_bucket["name"])
        self.assertEqual(bucket["project"], original_bucket["project"])
        self.assertEqual(bucket["location"], original_bucket["location"])

    def test_lockRetentionPolicy_modifies_database(self):
        """Test that lockRetentionPolicy actually modifies the database."""
        # Verify initial state
        self.assertFalse(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-1"]["retentionPolicyLocked"])
        self.assertEqual(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-1"]["metageneration"], "1")
        
        result = google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1")
        
        # Verify database was updated
        self.assertTrue(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-1"]["retentionPolicyLocked"])
        self.assertEqual(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-1"]["metageneration"], "2")

    def test_lockRetentionPolicy_no_side_effects_on_other_buckets(self):
        """Test that lockRetentionPolicy doesn't affect other buckets."""
        original_bucket2 = copy.deepcopy(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"])
        
        result = google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1")
        
        # Verify other bucket is unchanged
        self.assertEqual(
            google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"],
            original_bucket2
        )

    def test_lockRetentionPolicy_no_side_effects_on_nonexistent_bucket(self):
        """Test that lockRetentionPolicy doesn't create buckets for non-existent buckets."""
        original_buckets = list(google_cloud_storage.Buckets.DB["buckets"].keys())
        
        with self.assertRaises(Exception):  # BucketNotFoundError
            google_cloud_storage.Buckets.lockRetentionPolicy("non-existent", "1")
        
        # Verify no new buckets were created
        self.assertEqual(
            list(google_cloud_storage.Buckets.DB["buckets"].keys()),
            original_buckets
        )

    # --- Response Structure Verification Tests ---

    def test_lockRetentionPolicy_response_structure_complete(self):
        """Test that lockRetentionPolicy response has correct structure."""
        result = google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1")
        
        # Verify response structure
        self.assertIn("bucket", result)
        self.assertIsInstance(result["bucket"], dict)
        
        # Verify key fields are present
        bucket = result["bucket"]
        self.assertIn("name", bucket)
        self.assertIn("metageneration", bucket)
        self.assertIn("retentionPolicyLocked", bucket)

    def test_lockRetentionPolicy_return_value_is_bucket_data(self):
        """Test that lockRetentionPolicy returns the actual bucket data."""
        result = google_cloud_storage.Buckets.lockRetentionPolicy("test-bucket-1", "1")
        
        bucket = result["bucket"]
        db_bucket = google_cloud_storage.Buckets.DB["buckets"]["test-bucket-1"]
        
        # The returned bucket should be the same as the database bucket
        self.assertEqual(bucket, db_bucket)


if __name__ == "__main__":
    unittest.main() 