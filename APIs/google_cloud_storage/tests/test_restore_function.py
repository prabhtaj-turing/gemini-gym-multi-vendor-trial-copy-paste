import unittest
from unittest.mock import patch
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

sys.path.append("APIs")
import google_cloud_storage

# Import exceptions for testing
from google_cloud_storage.SimulationEngine.custom_errors import (
    BucketNotFoundError,
    NotSoftDeletedError,
    GenerationMismatchError,
    InvalidProjectionValueError
)


class TestRestoreFunction(unittest.TestCase):
    """Test cases for the restore function with comprehensive coverage."""

    def setUp(self):
        """Set up test data before each test."""
        # Reset the DB to a known state
        google_cloud_storage.Buckets.DB["buckets"] = {
            "test-bucket-1": {
                "name": "test-bucket-1",
                "project": "test-project",
                "metageneration": "1",
                "softDeleted": False,  # Not soft deleted
                "objects": [],
                "enableObjectRetention": False,
                "iamPolicy": {"bindings": []},
                "storageLayout": {},
                "generation": "1",
                "retentionPolicyLocked": False,
                "acl": [{"entity": "user-test", "role": "OWNER"}],
                "defaultObjectAcl": [{"entity": "user-test", "role": "OWNER"}]
            },
            "test-bucket-2": {
                "name": "test-bucket-2",
                "project": "test-project",
                "metageneration": "2",
                "softDeleted": True,  # Soft deleted
                "objects": ["file1", "file2"],
                "enableObjectRetention": True,
                "iamPolicy": {"bindings": []},
                "storageLayout": {},
                "generation": "2",
                "retentionPolicyLocked": True,
                "acl": [{"entity": "user-test", "role": "OWNER"}],
                "defaultObjectAcl": [{"entity": "user-test", "role": "OWNER"}]
            },
            "test-bucket-3": {
                "name": "test-bucket-3",
                "project": "test-project",
                "metageneration": "3",
                "softDeleted": True,  # Soft deleted with different generation
                "objects": [],
                "enableObjectRetention": False,
                "iamPolicy": {"bindings": []},
                "storageLayout": {},
                "generation": "5",  # Different generation
                "retentionPolicyLocked": False,
                "acl": [{"entity": "user-test", "role": "OWNER"}],
                "defaultObjectAcl": [{"entity": "user-test", "role": "OWNER"}]
            }
        }

    def tearDown(self):
        """Clean up after each test."""
        google_cloud_storage.Buckets.DB["buckets"] = {}

    # --- Success Cases ---

    def test_restore_success_with_full_projection(self):
        """Test successful bucket restoration with full projection."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2", "full")
        
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-2' restored successfully")
        self.assertIn("bucket", result)
        self.assertFalse(result["bucket"]["softDeleted"])
        self.assertIn("acl", result["bucket"])
        self.assertIn("defaultObjectAcl", result["bucket"])

    def test_restore_success_with_noacl_projection(self):
        """Test successful bucket restoration with noAcl projection."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2", "noAcl")
        
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-2' restored successfully")
        self.assertIn("bucket", result)
        self.assertFalse(result["bucket"]["softDeleted"])
        self.assertNotIn("acl", result["bucket"])
        self.assertNotIn("defaultObjectAcl", result["bucket"])

    def test_restore_success_with_default_projection(self):
        """Test successful bucket restoration with default projection (full)."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2")
        
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-2' restored successfully")
        self.assertIn("bucket", result)
        self.assertFalse(result["bucket"]["softDeleted"])
        self.assertIn("acl", result["bucket"])
        self.assertIn("defaultObjectAcl", result["bucket"])

    def test_restore_success_with_user_project_none(self):
        """Test successful bucket restoration with user_project as None."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2", "full", None)
        
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-2' restored successfully")
        self.assertIn("bucket", result)
        self.assertFalse(result["bucket"]["softDeleted"])

    def test_restore_success_with_user_project_string(self):
        """Test successful bucket restoration with user_project as string."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2", "full", "user-project-123")
        
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-2' restored successfully")
        self.assertIn("bucket", result)
        self.assertFalse(result["bucket"]["softDeleted"])

    # --- Type Validation Tests ---

    def test_restore_invalid_bucket_type(self):
        """Test restore with invalid bucket type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.restore(123, "2")
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_restore_invalid_generation_type(self):
        """Test restore with invalid generation type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-2", 2)
        self.assertIn("Argument 'generation' must be a string", str(context.exception))

    def test_restore_invalid_projection_type(self):
        """Test restore with invalid projection type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-2", "2", 123)
        self.assertIn("Argument 'projection' must be a string", str(context.exception))

    def test_restore_invalid_user_project_type(self):
        """Test restore with invalid user_project type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-2", "2", "full", 123)
        self.assertIn("Argument 'user_project' must be a string or None", str(context.exception))

    # --- Value Validation Tests ---

    def test_restore_empty_bucket_name(self):
        """Test restore with empty bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.restore("", "2")
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_restore_whitespace_only_bucket_name(self):
        """Test restore with whitespace-only bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.restore("   ", "2")
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_restore_bucket_name_too_short(self):
        """Test restore with bucket name too short."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.restore("ab", "2")
        self.assertIn("must be between 3 and 63 characters long", str(context.exception))

    def test_restore_bucket_name_too_long(self):
        """Test restore with bucket name too long."""
        long_name = "a" * 64
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.restore(long_name, "2")
        self.assertIn("must be between 3 and 63 characters long", str(context.exception))

    def test_restore_bucket_name_starts_with_dot(self):
        """Test restore with bucket name starting with dot."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.restore(".test-bucket", "2")
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_restore_bucket_name_ends_with_dot(self):
        """Test restore with bucket name ending with dot."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.restore("test-bucket.", "2")
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_restore_bucket_name_consecutive_dots(self):
        """Test restore with bucket name containing consecutive dots."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.restore("test..bucket", "2")
        self.assertIn("consecutive dots", str(context.exception))

    def test_restore_invalid_projection_value(self):
        """Test restore with invalid projection value."""
        with self.assertRaises(InvalidProjectionValueError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-2", "2", "invalid")
        self.assertIn("Invalid value for 'projection'", str(context.exception))

    # --- Business Logic Tests ---

    def test_restore_bucket_not_found(self):
        """Test restore with non-existent bucket."""
        with self.assertRaises(BucketNotFoundError) as context:
            google_cloud_storage.Buckets.restore("non-existent-bucket", "2")
        self.assertIn("Bucket 'non-existent-bucket' not found", str(context.exception))

    def test_restore_bucket_not_soft_deleted(self):
        """Test restore with bucket that is not soft deleted."""
        with self.assertRaises(NotSoftDeletedError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-1", "1")
        self.assertIn("Bucket 'test-bucket-1' is not soft deleted", str(context.exception))

    def test_restore_generation_mismatch(self):
        """Test restore with generation mismatch."""
        with self.assertRaises(GenerationMismatchError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-3", "2")
        self.assertIn("Generation mismatch for bucket 'test-bucket-3'", str(context.exception))

    # --- Edge Cases ---

    def test_restore_with_empty_string_generation(self):
        """Test restore with empty string generation."""
        # First, create a bucket with empty generation
        google_cloud_storage.Buckets.DB["buckets"]["empty-gen-bucket"] = {
            "name": "empty-gen-bucket",
            "project": "test-project",
            "metageneration": "1",
            "softDeleted": True,
            "objects": [],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "generation": "",
            "retentionPolicyLocked": False
        }
        
        result = google_cloud_storage.Buckets.restore("empty-gen-bucket", "")
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'empty-gen-bucket' restored successfully")

    def test_restore_with_numeric_string_generation(self):
        """Test restore with numeric string generation."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2")
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-2' restored successfully")

    def test_restore_with_special_characters_in_bucket_name(self):
        """Test restore with special characters in bucket name (valid ones)."""
        # Create a bucket with valid special characters
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket-valid"] = {
            "name": "test-bucket-valid",
            "project": "test-project",
            "metageneration": "1",
            "softDeleted": True,
            "objects": [],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "generation": "1",
            "retentionPolicyLocked": False
        }
        
        result = google_cloud_storage.Buckets.restore("test-bucket-valid", "1")
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-valid' restored successfully")

    def test_restore_bucket_name_minimum_valid_length(self):
        """Test restore with minimum valid bucket name length (3 characters)."""
        # Create a bucket with 3 characters
        google_cloud_storage.Buckets.DB["buckets"]["abc"] = {
            "name": "abc",
            "project": "test-project",
            "metageneration": "1",
            "softDeleted": True,
            "objects": [],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "generation": "1",
            "retentionPolicyLocked": False
        }
        
        result = google_cloud_storage.Buckets.restore("abc", "1")
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'abc' restored successfully")

    def test_restore_bucket_name_maximum_valid_length(self):
        """Test restore with maximum valid bucket name length (63 characters)."""
        # Create a bucket with 63 characters
        bucket_name = "a" * 63
        google_cloud_storage.Buckets.DB["buckets"][bucket_name] = {
            "name": bucket_name,
            "project": "test-project",
            "metageneration": "1",
            "softDeleted": True,
            "objects": [],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "generation": "1",
            "retentionPolicyLocked": False
        }
        
        result = google_cloud_storage.Buckets.restore(bucket_name, "1")
        self.assertIn("message", result)
        self.assertEqual(result["message"], f"Bucket '{bucket_name}' restored successfully")

    def test_restore_with_empty_string_user_project(self):
        """Test restore with empty string user_project."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2", "full", "")
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-2' restored successfully")

    def test_restore_bucket_with_none_generation_in_db(self):
        """Test restore with bucket that has None generation in database."""
        # Create a bucket with None generation
        google_cloud_storage.Buckets.DB["buckets"]["none-gen-bucket"] = {
            "name": "none-gen-bucket",
            "project": "test-project",
            "metageneration": "1",
            "softDeleted": True,
            "objects": [],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "generation": None,
            "retentionPolicyLocked": False
        }
        
        with self.assertRaises(GenerationMismatchError) as context:
            google_cloud_storage.Buckets.restore("none-gen-bucket", "1")
        self.assertIn("Generation mismatch for bucket 'none-gen-bucket'", str(context.exception))

    def test_restore_bucket_without_generation_key(self):
        """Test restore with bucket that doesn't have generation key in database."""
        # Create a bucket without generation key
        google_cloud_storage.Buckets.DB["buckets"]["no-gen-bucket"] = {
            "name": "no-gen-bucket",
            "project": "test-project",
            "metageneration": "1",
            "softDeleted": True,
            "objects": [],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "retentionPolicyLocked": False
        }
        
        with self.assertRaises(GenerationMismatchError) as context:
            google_cloud_storage.Buckets.restore("no-gen-bucket", "1")
        self.assertIn("Generation mismatch for bucket 'no-gen-bucket'", str(context.exception))

    def test_restore_bucket_without_softdeleted_key(self):
        """Test restore with bucket that doesn't have softDeleted key in database."""
        # Create a bucket without softDeleted key
        google_cloud_storage.Buckets.DB["buckets"]["no-soft-bucket"] = {
            "name": "no-soft-bucket",
            "project": "test-project",
            "metageneration": "1",
            "objects": [],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "generation": "1",
            "retentionPolicyLocked": False
        }
        
        with self.assertRaises(NotSoftDeletedError) as context:
            google_cloud_storage.Buckets.restore("no-soft-bucket", "1")
        self.assertIn("Bucket 'no-soft-bucket' is not soft deleted", str(context.exception))

    # --- State Verification Tests ---

    def test_restore_verifies_softdeleted_state_change(self):
        """Test that restore actually changes the softDeleted state."""
        # Verify initial state
        self.assertTrue(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"]["softDeleted"])
        
        # Perform restore
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2")
        
        # Verify state change
        self.assertFalse(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"]["softDeleted"])
        self.assertIn("message", result)
        self.assertEqual(result["message"], "Bucket 'test-bucket-2' restored successfully")

    def test_restore_preserves_other_bucket_properties(self):
        """Test that restore preserves other bucket properties."""
        original_bucket = google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"].copy()
        
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2")
        
        # Verify that only softDeleted changed
        self.assertFalse(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"]["softDeleted"])
        self.assertEqual(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"]["name"], original_bucket["name"])
        self.assertEqual(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"]["project"], original_bucket["project"])
        self.assertEqual(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"]["generation"], original_bucket["generation"])
        self.assertEqual(google_cloud_storage.Buckets.DB["buckets"]["test-bucket-2"]["objects"], original_bucket["objects"])

    # --- Projection Tests ---

    def test_restore_full_projection_includes_acl_fields(self):
        """Test that full projection includes acl and defaultObjectAcl fields."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2", "full")
        
        self.assertIn("bucket", result)
        self.assertIn("acl", result["bucket"])
        self.assertIn("defaultObjectAcl", result["bucket"])

    def test_restore_noacl_projection_excludes_acl_fields(self):
        """Test that noAcl projection excludes acl and defaultObjectAcl fields."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2", "noAcl")
        
        self.assertIn("bucket", result)
        self.assertNotIn("acl", result["bucket"])
        self.assertNotIn("defaultObjectAcl", result["bucket"])

    def test_restore_noacl_projection_preserves_other_fields(self):
        """Test that noAcl projection preserves other bucket fields."""
        result = google_cloud_storage.Buckets.restore("test-bucket-2", "2", "noAcl")
        
        self.assertIn("bucket", result)
        self.assertIn("name", result["bucket"])
        self.assertIn("project", result["bucket"])
        self.assertIn("generation", result["bucket"])
        self.assertIn("objects", result["bucket"])
        self.assertIn("iamPolicy", result["bucket"])

    # --- Error Message Tests ---

    def test_restore_error_message_bucket_not_found(self):
        """Test error message for bucket not found."""
        with self.assertRaises(BucketNotFoundError) as context:
            google_cloud_storage.Buckets.restore("missing-bucket", "1")
        self.assertEqual(str(context.exception), "Bucket 'missing-bucket' not found.")

    def test_restore_error_message_not_soft_deleted(self):
        """Test error message for bucket not soft deleted."""
        with self.assertRaises(NotSoftDeletedError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-1", "1")
        self.assertEqual(str(context.exception), "Bucket 'test-bucket-1' is not soft deleted.")

    def test_restore_error_message_generation_mismatch(self):
        """Test error message for generation mismatch."""
        with self.assertRaises(GenerationMismatchError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-3", "2")
        self.assertIn("Generation mismatch for bucket 'test-bucket-3'", str(context.exception))
        self.assertIn("Required '2', found '5'", str(context.exception))

    def test_restore_error_message_invalid_projection(self):
        """Test error message for invalid projection."""
        with self.assertRaises(InvalidProjectionValueError) as context:
            google_cloud_storage.Buckets.restore("test-bucket-2", "2", "invalid")
        self.assertIn("Invalid value for 'projection': 'invalid'", str(context.exception))
        self.assertIn("Must be 'full' or 'noAcl'", str(context.exception))


if __name__ == "__main__":
    unittest.main() 