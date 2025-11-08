"""
Comprehensive test cases for bucket delete method with full coverage of all scenarios.
"""

import unittest
import sys
import os
import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import patch, MagicMock

# Add the path to access the modules
sys.path.append("APIs")

from common_utils.base_case import BaseTestCaseWithErrorHandler
import google_cloud_storage
from google_cloud_storage.SimulationEngine.custom_errors import (
    BucketNotFoundError,
    MetagenerationMismatchError, 
    BucketNotEmptyError,
    SoftDeleteRetentionActiveError
)


# Create a mock DB that will be used throughout the tests
MOCK_DB = {"buckets": {}}


@patch('google_cloud_storage.Buckets.DB', MOCK_DB)
class TestBucketDelete(BaseTestCaseWithErrorHandler):
    """Test cases for bucket delete operations with comprehensive coverage."""

    def setUp(self):
        """Set up test environment before each test."""
        # Clear the mock DB for each test
        MOCK_DB.clear()
        MOCK_DB["buckets"] = {}
        self.test_db = MOCK_DB
        
        # Set up test buckets for different scenarios
        self.setup_test_buckets()

    def tearDown(self):
        """Clean up after each test."""
        # Clear the mock DB
        MOCK_DB.clear()
        MOCK_DB["buckets"] = {}

    def setup_test_buckets(self):
        """Set up various test bucket configurations."""
        
        # Empty bucket without soft delete policy - for normal deletion
        self.test_db["buckets"]["empty-bucket"] = {
            "name": "empty-bucket",
            "metageneration": "1",
            "objects": [],
            "softDeleted": False
        }

        # Empty bucket with soft delete policy - for soft deletion
        self.test_db["buckets"]["soft-delete-bucket"] = {
            "name": "soft-delete-bucket", 
            "metageneration": "1",
            "objects": [],
            "softDeleted": False,
            "softDeletePolicy": {
                "retentionDurationSeconds": "604800",  # 7 days
                "effectiveTime": "2023-01-01T00:00:00.000Z"
            }
        }

        # Non-empty bucket - should fail deletion
        self.test_db["buckets"]["non-empty-bucket"] = {
            "name": "non-empty-bucket",
            "metageneration": "1", 
            "objects": ["file1.txt", "file2.txt"],
            "softDeleted": False
        }

        # Already soft deleted bucket - retention period active
        current_time = datetime.datetime.now(datetime.timezone.utc)
        soft_delete_time = current_time - datetime.timedelta(hours=1)  # 1 hour ago
        
        self.test_db["buckets"]["already-soft-deleted"] = {
            "name": "already-soft-deleted",
            "metageneration": "1",
            "objects": [],
            "softDeleted": True,
            "softDeleteTime": soft_delete_time.isoformat() + "Z",
            "softDeletePolicy": {
                "retentionDurationSeconds": "604800",  # 7 days
                "effectiveTime": "2023-01-01T00:00:00.000Z"
            }
        }

        # Soft deleted bucket - retention period expired
        expired_time = current_time - datetime.timedelta(days=8)  # 8 days ago
        
        self.test_db["buckets"]["expired-soft-deleted"] = {
            "name": "expired-soft-deleted",
            "metageneration": "1", 
            "objects": [],
            "softDeleted": True,
            "softDeleteTime": expired_time.isoformat() + "Z",
            "softDeletePolicy": {
                "retentionDurationSeconds": "604800",  # 7 days  
                "effectiveTime": "2023-01-01T00:00:00.000Z"
            }
        }

        # Bucket with metageneration for testing conditions
        self.test_db["buckets"]["metageneration-test"] = {
            "name": "metageneration-test",
            "metageneration": "5",
            "objects": [],
            "softDeleted": False
        }

        # Bucket with inconsistent soft delete state (softDeleted=True but no softDeleteTime)
        self.test_db["buckets"]["inconsistent-state"] = {
            "name": "inconsistent-state",
            "metageneration": "1",
            "objects": [],
            "softDeleted": True,  # True but missing softDeleteTime
            "softDeletePolicy": {
                "retentionDurationSeconds": "604800",
                "effectiveTime": "2023-01-01T00:00:00.000Z"
            }
        }

        # Bucket with soft delete policy but invalid retention duration
        self.test_db["buckets"]["invalid-retention"] = {
            "name": "invalid-retention",
            "metageneration": "1",
            "objects": [],
            "softDeleted": False,
            "softDeletePolicy": {
                "retentionDurationSeconds": "invalid",  # Invalid value
                "effectiveTime": "2023-01-01T00:00:00.000Z"
            }
        }

    # ========================================================================
    # INPUT VALIDATION TESTS
    # ========================================================================

    def test_delete_bucket_invalid_bucket_type(self):
        """Test delete with non-string bucket parameter."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.delete_bucket(123)
        
        self.assertIn("must be a string", str(context.exception))

    def test_delete_bucket_invalid_metageneration_match_type(self):
        """Test delete with non-string if_metageneration_match parameter."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.delete_bucket("empty-bucket", if_metageneration_match=123)
        
        self.assertIn("if_metageneration_match", str(context.exception))
        self.assertIn("must be a string", str(context.exception))

    def test_delete_bucket_invalid_metageneration_not_match_type(self):
        """Test delete with non-string if_metageneration_not_match parameter.""" 
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.delete_bucket("empty-bucket", if_metageneration_not_match=456)
        
        self.assertIn("if_metageneration_not_match", str(context.exception))
        self.assertIn("must be a string", str(context.exception))

    def test_delete_bucket_empty_name(self):
        """Test delete with empty bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.delete_bucket("")
        
        self.assertIn("cannot be empty", str(context.exception))

    def test_delete_bucket_whitespace_name(self):
        """Test delete with whitespace-only bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.delete_bucket("   ")
        
        self.assertIn("cannot be empty", str(context.exception))

    def test_delete_bucket_name_too_short(self):
        """Test delete with bucket name shorter than 3 characters."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.delete_bucket("ab")
        
        self.assertIn("between 3 and 63 characters", str(context.exception))

    def test_delete_bucket_name_too_long(self):
        """Test delete with bucket name longer than 63 characters."""
        long_name = "a" * 64
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.delete_bucket(long_name)
        
        self.assertIn("between 3 and 63 characters", str(context.exception))

    def test_delete_bucket_name_starts_with_dot(self):
        """Test delete with bucket name starting with dot."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.delete_bucket(".invalid-bucket")
        
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_delete_bucket_name_ends_with_dot(self):
        """Test delete with bucket name ending with dot."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.delete_bucket("invalid-bucket.")
        
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_delete_bucket_name_consecutive_dots(self):
        """Test delete with bucket name containing consecutive dots.""" 
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.delete_bucket("invalid..bucket")
        
        self.assertIn("consecutive dots", str(context.exception))

    # ========================================================================
    # BUCKET NOT FOUND TESTS
    # ========================================================================

    def test_delete_nonexistent_bucket(self):
        """Test delete of bucket that doesn't exist."""
        with self.assertRaises(BucketNotFoundError) as context:
            google_cloud_storage.delete_bucket("nonexistent-bucket")
        
        self.assertIn("not found", str(context.exception))

    # ========================================================================
    # METAGENERATION CONDITION TESTS  
    # ========================================================================

    def test_delete_metageneration_match_success(self):
        """Test successful delete with matching metageneration."""
        result = google_cloud_storage.delete_bucket("metageneration-test", if_metageneration_match="5")
        
        self.assertEqual(result["message"], "Bucket 'metageneration-test' deleted successfully")
        self.assertNotIn("metageneration-test", self.test_db["buckets"])

    def test_delete_metageneration_match_failure(self):
        """Test delete failure with non-matching metageneration."""
        with self.assertRaises(MetagenerationMismatchError) as context:
            google_cloud_storage.delete_bucket("metageneration-test", if_metageneration_match="3")
        
        self.assertIn("mismatch", str(context.exception))
        self.assertIn("Required match '3'", str(context.exception))
        self.assertIn("found '5'", str(context.exception))

    def test_delete_metageneration_not_match_success(self):
        """Test successful delete with non-matching metageneration."""
        result = google_cloud_storage.delete_bucket("metageneration-test", if_metageneration_not_match="3")
        
        self.assertEqual(result["message"], "Bucket 'metageneration-test' deleted successfully")
        self.assertNotIn("metageneration-test", self.test_db["buckets"])

    def test_delete_metageneration_not_match_failure(self):
        """Test delete failure when metageneration matches (should not match)."""
        with self.assertRaises(MetagenerationMismatchError) as context:
            google_cloud_storage.delete_bucket("metageneration-test", if_metageneration_not_match="5")
        
        self.assertIn("mismatch", str(context.exception))
        self.assertIn("Required non-match '5'", str(context.exception))
        self.assertIn("found '5'", str(context.exception))

    # ========================================================================
    # BUCKET NOT EMPTY TESTS
    # ========================================================================

    def test_delete_non_empty_bucket(self):
        """Test delete of bucket that contains objects."""
        with self.assertRaises(BucketNotEmptyError) as context:
            google_cloud_storage.delete_bucket("non-empty-bucket")
        
        self.assertIn("not empty", str(context.exception))

    # ========================================================================
    # NORMAL HARD DELETE TESTS (No Soft Delete Policy)
    # ========================================================================

    def test_delete_empty_bucket_no_soft_delete(self):
        """Test successful hard delete of empty bucket without soft delete policy."""
        result = google_cloud_storage.delete_bucket("empty-bucket")
        
        self.assertEqual(result["message"], "Bucket 'empty-bucket' deleted successfully")
        self.assertNotIn("empty-bucket", self.test_db["buckets"])

    # ========================================================================
    # SOFT DELETE TESTS
    # ========================================================================

    def test_soft_delete_bucket_first_time(self):
        """Test soft delete of bucket for the first time."""
        result = google_cloud_storage.delete_bucket("soft-delete-bucket")
        
        self.assertEqual(result["message"], "Bucket 'soft-delete-bucket' soft deleted successfully")
        
        # Bucket should still exist but marked as soft deleted
        self.assertIn("soft-delete-bucket", self.test_db["buckets"])
        bucket = self.test_db["buckets"]["soft-delete-bucket"]
        self.assertTrue(bucket["softDeleted"])
        self.assertIsNotNone(bucket["softDeleteTime"])
        self.assertIsNotNone(bucket.get("hardDeleteTime"))

    def test_soft_delete_already_deleted_retention_active(self):
        """Test deletion of already soft deleted bucket with active retention period."""
        with self.assertRaises(SoftDeleteRetentionActiveError) as context:
            google_cloud_storage.delete_bucket("already-soft-deleted")
        
        self.assertIn("already soft deleted", str(context.exception))
        self.assertIn("cannot be deleted again", str(context.exception))
        self.assertIn("retention period expires", str(context.exception))
        
        # Bucket should still exist and remain soft deleted
        self.assertIn("already-soft-deleted", self.test_db["buckets"])
        bucket = self.test_db["buckets"]["already-soft-deleted"]
        self.assertTrue(bucket["softDeleted"])

    def test_soft_delete_already_deleted_retention_expired(self):
        """Test deletion of already soft deleted bucket with expired retention period."""
        result = google_cloud_storage.delete_bucket("expired-soft-deleted")
        
        self.assertIn("permanently deleted", result["message"])
        self.assertIn("retention period expired", result["message"])
        
        # Bucket should be completely removed
        self.assertNotIn("expired-soft-deleted", self.test_db["buckets"])

    def test_soft_delete_invalid_retention_duration(self):
        """Test soft delete with invalid retention duration."""
        result = google_cloud_storage.delete_bucket("invalid-retention")
        
        self.assertEqual(result["message"], "Bucket 'invalid-retention' soft deleted successfully")
        
        # Should still perform soft delete, but hardDeleteTime may be None
        self.assertIn("invalid-retention", self.test_db["buckets"])
        bucket = self.test_db["buckets"]["invalid-retention"]
        self.assertTrue(bucket["softDeleted"])
        self.assertIsNotNone(bucket["softDeleteTime"])
        # hardDeleteTime might be None due to invalid retention duration

    # ========================================================================
    # EDGE CASES AND DATETIME HANDLING
    # ========================================================================

    def test_soft_delete_bucket_with_zero_retention(self):
        """Test soft delete with zero retention period."""
        # Create bucket with zero retention
        self.test_db["buckets"]["zero-retention"] = {
            "name": "zero-retention",
            "metageneration": "1",
            "objects": [],
            "softDeleted": False,
            "softDeletePolicy": {
                "retentionDurationSeconds": "0",
                "effectiveTime": "2023-01-01T00:00:00.000Z"
            }
        }
        
        result = google_cloud_storage.delete_bucket("zero-retention")
        
        self.assertEqual(result["message"], "Bucket 'zero-retention' soft deleted successfully")
        
        # Check that hardDeleteTime is calculated correctly (should be immediate)
        bucket = self.test_db["buckets"]["zero-retention"]
        self.assertTrue(bucket["softDeleted"])
        self.assertIsNotNone(bucket["hardDeleteTime"])

    def test_soft_delete_bucket_without_retention_seconds(self):
        """Test soft delete with policy missing retentionDurationSeconds."""
        # Create bucket with incomplete soft delete policy
        self.test_db["buckets"]["no-retention-seconds"] = {
            "name": "no-retention-seconds",
            "metageneration": "1",
            "objects": [],
            "softDeleted": False,
            "softDeletePolicy": {
                "effectiveTime": "2023-01-01T00:00:00.000Z"
                # Missing retentionDurationSeconds
            }
        }
        
        result = google_cloud_storage.delete_bucket("no-retention-seconds")
        
        self.assertEqual(result["message"], "Bucket 'no-retention-seconds' soft deleted successfully")
        
        # Should still work, hardDeleteTime might be None
        bucket = self.test_db["buckets"]["no-retention-seconds"]
        self.assertTrue(bucket["softDeleted"])

    # ========================================================================
    # COMPLEX SCENARIOS
    # ========================================================================

    def test_soft_delete_with_metageneration_conditions(self):
        """Test soft delete combined with metageneration conditions."""
        # Create bucket with soft delete policy and specific metageneration
        self.test_db["buckets"]["soft-with-meta"] = {
            "name": "soft-with-meta",
            "metageneration": "3",
            "objects": [],
            "softDeleted": False,
            "softDeletePolicy": {
                "retentionDurationSeconds": "604800",
                "effectiveTime": "2023-01-01T00:00:00.000Z"
            }
        }
        
        # Test with matching metageneration
        result = google_cloud_storage.delete_bucket("soft-with-meta", if_metageneration_match="3")
        
        self.assertEqual(result["message"], "Bucket 'soft-with-meta' soft deleted successfully")
        self.assertTrue(self.test_db["buckets"]["soft-with-meta"]["softDeleted"])

    def test_soft_delete_metageneration_mismatch_before_soft_delete_check(self):
        """Test that metageneration is checked before soft delete logic."""
        with self.assertRaises(MetagenerationMismatchError):
            google_cloud_storage.delete_bucket("soft-delete-bucket", if_metageneration_match="999")
        
        # Bucket should remain unchanged 
        bucket = self.test_db["buckets"]["soft-delete-bucket"]
        self.assertFalse(bucket["softDeleted"])

    # ========================================================================
    # BOUNDARY TESTS
    # ========================================================================

    def test_delete_bucket_name_exactly_3_chars(self):
        """Test delete with bucket name of exactly 3 characters."""
        self.test_db["buckets"]["abc"] = {
            "name": "abc",
            "metageneration": "1",
            "objects": [],
            "softDeleted": False
        }
        
        result = google_cloud_storage.delete_bucket("abc")
        self.assertEqual(result["message"], "Bucket 'abc' deleted successfully")

    def test_delete_bucket_name_exactly_63_chars(self):
        """Test delete with bucket name of exactly 63 characters.""" 
        long_name = "a" * 63
        self.test_db["buckets"][long_name] = {
            "name": long_name,
            "metageneration": "1", 
            "objects": [],
            "softDeleted": False
        }
        
        result = google_cloud_storage.delete_bucket(long_name)
        self.assertEqual(result["message"], f"Bucket '{long_name}' deleted successfully")

    # ========================================================================
    # SOFT DELETE POLICY VALIDATION
    # ========================================================================

    def test_soft_delete_policy_without_effective_time(self):
        """Test soft delete behavior when policy lacks effectiveTime."""
        # Create bucket with soft delete policy missing effectiveTime
        self.test_db["buckets"]["no-effective-time"] = {
            "name": "no-effective-time",
            "metageneration": "1",
            "objects": [],
            "softDeleted": False,
            "softDeletePolicy": {
                "retentionDurationSeconds": "604800"
                # Missing effectiveTime
            }
        }
        
        result = google_cloud_storage.delete_bucket("no-effective-time")
        
        # Should fall back to hard delete since policy is incomplete
        self.assertEqual(result["message"], "Bucket 'no-effective-time' deleted successfully")
        self.assertNotIn("no-effective-time", self.test_db["buckets"])

    def test_soft_delete_policy_non_dict(self):
        """Test soft delete behavior when policy is not a dictionary."""
        # Create bucket with invalid soft delete policy type
        self.test_db["buckets"]["invalid-policy-type"] = {
            "name": "invalid-policy-type",
            "metageneration": "1",
            "objects": [],
            "softDeleted": False,
            "softDeletePolicy": "invalid-string-policy"
        }
        
        result = google_cloud_storage.delete_bucket("invalid-policy-type")
        
        # Should fall back to hard delete since policy is invalid type
        self.assertEqual(result["message"], "Bucket 'invalid-policy-type' deleted successfully")
        self.assertNotIn("invalid-policy-type", self.test_db["buckets"])

    # ========================================================================
    # COMPREHENSIVE INTEGRATION TESTS
    # ========================================================================

    def test_complete_soft_delete_lifecycle(self):
        """Test complete soft delete lifecycle from creation to expiration."""
        bucket_name = "lifecycle-test"
        
        # Create bucket with 1 second retention for fast testing
        self.test_db["buckets"][bucket_name] = {
            "name": bucket_name,
            "metageneration": "1",
            "objects": [],
            "softDeleted": False,
            "softDeletePolicy": {
                "retentionDurationSeconds": "1",  # 1 second for testing
                "effectiveTime": "2023-01-01T00:00:00.000Z"
            }
        }
        
        # First deletion - should soft delete
        result1 = google_cloud_storage.delete_bucket(bucket_name)
        self.assertIn("soft deleted successfully", result1["message"])
        self.assertTrue(self.test_db["buckets"][bucket_name]["softDeleted"])
        
        # Second deletion immediately - should raise exception
        with self.assertRaises(SoftDeleteRetentionActiveError) as context:
            google_cloud_storage.delete_bucket(bucket_name)
        self.assertIn("already soft deleted", str(context.exception))
        self.assertIn("retention period expires", str(context.exception))
        
        # Simulate time passing by modifying softDeleteTime to be old
        old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=2)
        self.test_db["buckets"][bucket_name]["softDeleteTime"] = old_time.isoformat() + "Z"
        
        # Third deletion after expiration - should hard delete
        result3 = google_cloud_storage.delete_bucket(bucket_name)
        self.assertIn("permanently deleted", result3["message"]) 
        self.assertIn("retention period expired", result3["message"])
        self.assertNotIn(bucket_name, self.test_db["buckets"])


if __name__ == '__main__':
    unittest.main()
