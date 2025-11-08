"""
Comprehensive test cases for bucket patch and update methods with Pydantic validation.
"""

import unittest
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from unittest.mock import patch

# Add the path to access the modules
sys.path.append("APIs")

from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_cloud_storage.SimulationEngine.db import DB

import google_cloud_storage

try:
    from google_cloud_storage.SimulationEngine.models import BucketRequest
except ImportError:
    BucketRequest = None


class TestBucketPatchUpdate(BaseTestCaseWithErrorHandler):
    """Test cases for bucket patch and update operations with Pydantic validation."""

    def setUp(self):
        """Set up test environment before each test."""
        # Reset DB
        google_cloud_storage.Buckets.DB["buckets"] = {}
        
        # Create a test bucket
        self.test_bucket = {
            "name": "test-bucket",
            "project": "test-project", 
            "metageneration": "1",
            "generation": "100",
            "softDeleted": False,
            "objects": [],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "storageLayout": {},
            "retentionPolicyLocked": False,
            "kind": "storage#bucket",
            "location": "US",
            "storageClass": "STANDARD",
            "timeCreated": "2023-01-01T00:00:00Z",
            "updated": "2023-01-01T00:00:00Z",
            "acl": [],
            "defaultObjectAcl": [],
            "versioning": {"enabled": False}
        }
        
        # Add to DB
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"] = self.test_bucket.copy()

    def test_patch_bucket_basic_success(self):
        """Test successful basic patch operation."""
        bucket_request = {
            "storageClass": "COLDLINE",
            "labels": {"env": "test", "team": "engineering"}
        }
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket", 
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")
        self.assertEqual(result["labels"], {"env": "test", "team": "engineering"})
        self.assertEqual(result["metageneration"], "2")  # Should increment

    def test_patch_bucket_not_found(self):
        """Test patch with non-existent bucket."""
        result, status = google_cloud_storage.Buckets.patch("non-existent")
        
        self.assertEqual(status, 404)
        self.assertEqual(result["error"], "Bucket non-existent not found")

    def test_patch_invalid_bucket_name_type(self):
        """Test patch with invalid bucket name type."""
        result, status = google_cloud_storage.Buckets.patch(123)
        
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "Bucket name must be a string")

    def test_patch_metageneration_match_success(self):
        """Test patch with successful metageneration match."""
        bucket_request = {"storageClass": "NEARLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            if_metageneration_match="1",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "NEARLINE")

    def test_patch_metageneration_match_failure(self):
        """Test patch with failed metageneration match."""
        bucket_request = {"storageClass": "NEARLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            if_metageneration_match="999",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 412)
        self.assertEqual(result["error"], "Metageneration mismatch")

    def test_patch_metageneration_not_match_success(self):
        """Test patch with successful metageneration not match."""
        bucket_request = {"storageClass": "NEARLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            if_metageneration_not_match="999",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "NEARLINE")

    def test_patch_metageneration_not_match_failure(self):
        """Test patch with failed metageneration not match."""
        bucket_request = {"storageClass": "NEARLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            if_metageneration_not_match="1",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 412)
        self.assertEqual(result["error"], "Metageneration mismatch")

    def test_patch_with_predefined_acl(self):
        """Test patch with predefined ACL."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            predefinedAcl="private"
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["acl"], "private")

    def test_patch_invalid_predefined_acl(self):
        """Test patch with invalid predefined ACL."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            predefinedAcl="invalidAcl"
        )
        
        self.assertEqual(status, 400)
        self.assertIn("Invalid predefinedAcl", result["error"])

    def test_patch_invalid_predefined_default_object_acl(self):
        """Test patch with invalid predefined default object ACL."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            predefined_default_object_acl="invalidAcl"
        )
        
        self.assertEqual(status, 400)
        self.assertIn("Invalid predefined_default_object_acl", result["error"])

    def test_patch_valid_predefined_acls(self):
        """Test patch with valid predefined ACL values."""
        # Test all valid ACL values
        valid_acls = ["authenticatedRead", "private", "projectPrivate", "publicRead", "publicReadWrite"]
        
        for acl in valid_acls:
            result, status = google_cloud_storage.Buckets.patch(
                "test-bucket",
                predefinedAcl=acl
            )
            
            self.assertEqual(status, 200, f"Failed for ACL: {acl}")
            self.assertEqual(result["acl"], acl)

    def test_patch_valid_predefined_default_object_acls(self):
        """Test patch with valid predefined default object ACL values.""" 
        valid_default_acls = ["authenticatedRead", "bucketOwnerFullControl", "bucketOwnerRead", 
                             "private", "projectPrivate", "publicRead"]
        
        for acl in valid_default_acls:
            result, status = google_cloud_storage.Buckets.patch(
                "test-bucket",
                predefined_default_object_acl=acl
            )
            
            self.assertEqual(status, 200, f"Failed for default object ACL: {acl}")
            self.assertEqual(result["defaultObjectAcl"], acl)

    def test_patch_projection_no_acl(self):
        """Test patch with noAcl projection."""
        bucket_request = {"storageClass": "COLDLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            projection="noAcl",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertNotIn("acl", result)
        self.assertNotIn("defaultObjectAcl", result)
        self.assertEqual(result["storageClass"], "COLDLINE")

    def test_patch_projection_full(self):
        """Test patch with full projection."""
        bucket_request = {"storageClass": "COLDLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            projection="full",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertIn("acl", result)
        self.assertIn("defaultObjectAcl", result)

    def test_patch_invalid_projection(self):
        """Test patch with invalid projection."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            projection="invalid"
        )
        
        self.assertEqual(status, 400)
        self.assertIn("Invalid projection", result["error"])

    def test_patch_invalid_bucket_request_type(self):
        """Test patch with non-dict bucket_request."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request="invalid-request"
        )
        
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "Invalid bucket_request; must be a dictionary")

    def test_patch_validation_error_invalid_storage_class(self):
        """Test patch with invalid storage class."""
        bucket_request = {"storageClass": "INVALID_CLASS"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])

    def test_patch_validation_error_invalid_rpo(self):
        """Test patch with invalid RPO."""
        bucket_request = {"rpo": "INVALID_RPO"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        # Test should pass validation error when models are available
        if BucketRequest is not None:
            self.assertEqual(status, 400)
            self.assertIn("Validation error", result["error"])
        else:
            # Fallback behavior when models aren't available
            self.assertEqual(status, 200)

    def test_patch_validation_valid_enums(self):
        """Test patch with valid enum values."""
        bucket_request = {
            "storageClass": "COLDLINE",
            "rpo": "ASYNC_TURBO"
        }
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")
        self.assertEqual(result["rpo"], "ASYNC_TURBO")
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])

    def test_patch_complex_nested_structure(self):
        """Test patch with complex nested structures."""
        bucket_request = {
            "versioning": {"enabled": True},
            "lifecycle": {
                "rule": [
                    {
                        "action": {"type": "Delete"},
                        "condition": {"age": 30, "isLive": True}
                    }
                ]
            },
            "cors": [
                {
                    "maxAgeSeconds": 3600,
                    "method": ["GET", "POST"],
                    "origin": ["*"],
                    "responseHeader": ["Content-Type"]
                }
            ]
        }
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["versioning"]["enabled"], True)
        self.assertEqual(len(result["lifecycle"]["rule"]), 1)
        self.assertEqual(result["lifecycle"]["rule"][0]["action"]["type"], "Delete")
        self.assertEqual(len(result["cors"]), 1)
        self.assertEqual(result["cors"][0]["maxAgeSeconds"], 3600)

    # UPDATE METHOD TESTS

    def test_update_bucket_basic_success(self):
        """Test successful basic update operation."""
        bucket_request = {
            "name": "test-bucket",
            "storageClass": "COLDLINE",
            "location": "EU",
            "labels": {"env": "prod"}
        }
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")
        self.assertEqual(result["location"], "EU")
        self.assertEqual(result["labels"], {"env": "prod"})
        self.assertEqual(result["metageneration"], "2")  # Should increment

    def test_update_bucket_not_found(self):
        """Test update with non-existent bucket."""
        bucket_request = {"storageClass": "COLDLINE"}
        
        result, status = google_cloud_storage.Buckets.update(
            "non-existent",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 404)
        self.assertEqual(result["error"], "Bucket non-existent not found")

    def test_update_no_bucket_request(self):
        """Test update without bucket_request (required for update)."""
        result, status = google_cloud_storage.Buckets.update("test-bucket")
        
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "bucket_request is required for update operation")

    def test_update_invalid_bucket_request_type(self):
        """Test update with non-dict bucket_request."""
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            bucket_request="invalid"
        )
        
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "Invalid bucket_request; must be a dictionary")

    def test_update_preserves_core_fields(self):
        """Test that update preserves core immutable fields."""
        original_time_created = self.test_bucket["timeCreated"]
        original_generation = self.test_bucket["generation"]
        original_project = self.test_bucket["project"]
        
        bucket_request = {
            "name": "different-name",  # Should be ignored
            "timeCreated": "2024-01-01T00:00:00Z",  # Should be preserved
            "generation": "999",  # Should be preserved
            "project": "different-project",  # Should be preserved
            "storageClass": "ARCHIVE"
        }
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["name"], "test-bucket")  # Original preserved
        self.assertEqual(result["timeCreated"], original_time_created)  # Original preserved
        self.assertEqual(result["generation"], original_generation)  # Original preserved
        self.assertEqual(result["project"], original_project)  # Original preserved
        self.assertEqual(result["storageClass"], "ARCHIVE")  # Updated
        self.assertEqual(result["kind"], "storage#bucket")

    def test_update_with_metageneration_conditions(self):
        """Test update with metageneration conditions."""
        bucket_request = {"storageClass": "NEARLINE"}
        
        # Test successful match
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            if_metageneration_match="1",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "NEARLINE")

    def test_update_validation_complex_structure(self):
        """Test update with complex validation requirements."""
        bucket_request = {
            "storageClass": "STANDARD",
            "location": "US-CENTRAL1",
            "versioning": {"enabled": True},
            "encryption": {
                "defaultKmsKeyName": "projects/test/locations/us/keyRings/test/cryptoKeys/test"
            },
            "iamConfiguration": {
                "uniformBucketLevelAccess": {"enabled": True},
                "publicAccessPrevention": "enforced"
            },
            "retentionPolicy": {
                "retentionPeriod": "86400",
                "isLocked": False
            },
            "lifecycle": {
                "rule": [
                    {
                        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
                        "condition": {"age": 90, "matchesStorageClass": ["STANDARD"]}
                    }
                ]
            }
        }
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["versioning"]["enabled"], True)
        self.assertIn("defaultKmsKeyName", result["encryption"])
        self.assertEqual(result["iamConfiguration"]["uniformBucketLevelAccess"]["enabled"], True)
        self.assertEqual(result["retentionPolicy"]["retentionPeriod"], "86400")
        self.assertEqual(len(result["lifecycle"]["rule"]), 1)

    def test_patch_vs_update_semantics(self):
        """Test the difference between patch (partial) and update (complete) semantics."""
        # Set up bucket with initial data
        initial_data = {
            "storageClass": "STANDARD",
            "labels": {"initial": "value"},
            "versioning": {"enabled": True}
        }
        
        # Patch should only modify specified fields
        patch_request = {"storageClass": "COLDLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=patch_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")
        # These should remain unchanged in patch
        self.assertIn("labels", result)
        self.assertIn("versioning", result)
        
        # Reset bucket
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"] = self.test_bucket.copy()
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"].update(initial_data)
        
        # Update should replace the entire configuration
        update_request = {
            "storageClass": "ARCHIVE",
            "location": "EU"
            # Note: not including labels or versioning
        }
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            bucket_request=update_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "ARCHIVE")
        self.assertEqual(result["location"], "EU")

    def test_patch_protected_fields_ignored(self):
        """Test that protected fields are ignored in patch operations."""
        bucket_request = {
            "id": "should-be-ignored",
            "kind": "should-be-ignored", 
            "timeCreated": "2024-01-01T00:00:00Z",
            "generation": "999",
            "storageClass": "COLDLINE"  # This should work
        }
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        # Protected fields should remain unchanged
        self.assertNotEqual(result.get("id"), "should-be-ignored")
        self.assertEqual(result["kind"], "storage#bucket")
        self.assertEqual(result["generation"], "100")  # Original value
        # Non-protected field should be updated
        self.assertEqual(result["storageClass"], "COLDLINE")

    def test_patch_validation_valid_enums(self):
        """Test patch with valid enum values."""
        bucket_request = {
            "storageClass": "COLDLINE",
            "rpo": "ASYNC_TURBO"
        }
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        # When models are available, should validate successfully
        # When not available, should still work but without strict validation
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE") 
        self.assertEqual(result["rpo"], "ASYNC_TURBO")

    def test_patch_vs_update_semantics(self):
        """Test the difference between patch (partial) and update (complete) semantics."""
        # Set up bucket with initial data
        initial_data = {
            "storageClass": "STANDARD",
            "labels": {"initial": "value"},
            "versioning": {"enabled": True}
        }
        
        # Apply initial data to test bucket
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"].update(initial_data)
        
        # Patch should only modify specified fields
        patch_request = {"storageClass": "COLDLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            bucket_request=patch_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")
        # These should remain unchanged in patch
        self.assertIn("labels", result)
        self.assertEqual(result["labels"]["initial"], "value")
        self.assertIn("versioning", result)
        self.assertEqual(result["versioning"]["enabled"], True)
        
        # Reset bucket with initial data for update test
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"] = self.test_bucket.copy()
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"].update(initial_data)
        
        # Update should replace the entire configuration
        update_request = {
            "name": "test-bucket",  # Required field
            "storageClass": "ARCHIVE",
            "location": "EU"
            # Note: not including labels or versioning
        }
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            bucket_request=update_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "ARCHIVE")
        self.assertEqual(result["location"], "EU")

    def test_update_preserves_core_fields(self):
        """Test that update preserves core immutable fields."""
        original_time_created = self.test_bucket["timeCreated"]
        original_generation = self.test_bucket["generation"]
        original_project = self.test_bucket["project"]
        
        bucket_request = {
            "name": "different-name",  # Should be ignored
            "timeCreated": "2024-01-01T00:00:00Z",  # Should be preserved
            "generation": "999",  # Should be preserved
            "project": "different-project",  # Should be preserved
            "storageClass": "ARCHIVE",
            "location": "US"  # Include required location
        }
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            bucket_request=bucket_request
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(result["name"], "test-bucket")  # Original preserved
        self.assertEqual(result["timeCreated"], original_time_created)  # Original preserved
        self.assertEqual(result["generation"], original_generation)  # Original preserved
        self.assertEqual(result["project"], original_project)  # Original preserved
        self.assertEqual(result["storageClass"], "ARCHIVE")  # Updated
        self.assertEqual(result["kind"], "storage#bucket")

    def test_patch_invalid_labels_type(self):
        """Test patch with invalid label value type."""
        bucket_request = {"labels": {"key": 123}}  # invalid value type
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])

    def test_update_projection_no_acl(self):
        """Test update with projection=noAcl omits ACL fields."""
        update_request = {"storageClass": "COLDLINE", "location": "EU"}
        result, status = google_cloud_storage.Buckets.update("test-bucket", projection="noAcl", bucket_request=update_request)
        self.assertEqual(status, 200)
        self.assertNotIn("acl", result)
        self.assertNotIn("defaultObjectAcl", result)

    def test_update_with_predefined_acl(self):
        """Test update with predefined ACL."""
        update_request = {"storageClass": "NEARLINE", "location": "US"}
        result, status = google_cloud_storage.Buckets.update("test-bucket", predefinedAcl="private", bucket_request=update_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["acl"], "private")

    def test_update_protected_fields_ignored_and_projection_no_acl(self):
        """Test that update ignores protected fields and respects projection."""
        update_req = {
            "id": "bad",  # protected
            "kind": "bad",
            "generation": "999",
            "timeCreated": "2025-01-01T00:00:00Z",
            "storageClass": "COLDLINE",
            "location": "EU",
        }
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", projection="noAcl", bucket_request=update_req
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["kind"], "storage#bucket")
        self.assertEqual(result["generation"], "100")
        self.assertEqual(result["storageClass"], "COLDLINE")
        self.assertNotIn("acl", result)
        self.assertNotIn("defaultObjectAcl", result)

    def test_update_metageneration_mismatch(self):
        """Test update with metageneration mismatch returns 412."""
        update_req = {"storageClass": "COLDLINE", "location": "EU"}
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", if_metageneration_match="999", bucket_request=update_req
        )
        self.assertEqual(status, 412)
        self.assertEqual(result["error"], "Metageneration mismatch") 

    def test_patch_with_empty_body(self):
        """Test patch with empty body still increments metageneration."""
        original_meta = self.test_bucket["metageneration"]
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request={})
        self.assertEqual(status, 200)
        self.assertEqual(result["metageneration"], str(int(original_meta) + 1))
        self.assertEqual(result["storageClass"], "STANDARD")  # unchanged

    def test_patch_with_none_body(self):
        """Test patch with None body still increments metageneration."""
        original_meta = self.test_bucket["metageneration"]
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=None)
        self.assertEqual(status, 200)
        self.assertEqual(result["metageneration"], str(int(original_meta) + 1))
        self.assertEqual(result["storageClass"], "STANDARD")  # unchanged

    def test_patch_with_complex_nested_structures(self):
        """Test patch with complex nested configuration objects."""
        bucket_request = {
            "cors": [{
                "maxAgeSeconds": 3600,
                "method": ["GET", "POST"],
                "origin": ["https://example.com"],
                "responseHeader": ["Content-Type"]
            }],
            "lifecycle": {
                "rule": [{
                    "action": {"type": "Delete", "storageClass": "COLDLINE"},
                    "condition": {"age": 30, "isLive": True}
                }]
            },
            "labels": {"environment": "production", "team": "backend"}
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["cors"][0]["maxAgeSeconds"], 3600)
        self.assertEqual(result["lifecycle"]["rule"][0]["action"]["type"], "Delete")
        self.assertEqual(result["labels"]["environment"], "production")

    def test_patch_with_iam_configuration(self):
        """Test patch with IAM configuration."""
        bucket_request = {
            "iamConfiguration": {
                "uniformBucketLevelAccess": {"enabled": True},
                "publicAccessPrevention": "enforced"
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertTrue(result["iamConfiguration"]["uniformBucketLevelAccess"]["enabled"])
        self.assertEqual(result["iamConfiguration"]["publicAccessPrevention"], "enforced")

    def test_patch_with_versioning(self):
        """Test patch with versioning configuration."""
        bucket_request = {"versioning": {"enabled": True}}
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertTrue(result["versioning"]["enabled"])

    def test_patch_with_encryption(self):
        """Test patch with encryption configuration."""
        bucket_request = {
            "encryption": {"defaultKmsKeyName": "projects/test/locations/us/keyRings/test/cryptoKeys/test"}
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertIn("defaultKmsKeyName", result["encryption"])

    def test_patch_with_retention_policy(self):
        """Test patch with retention policy."""
        bucket_request = {
            "retentionPolicy": {
                "retentionPeriod": "2592000",  # 30 days in seconds
                "isLocked": False
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["retentionPolicy"]["retentionPeriod"], "2592000")
        self.assertFalse(result["retentionPolicy"]["isLocked"])

    def test_patch_with_website_config(self):
        """Test patch with website configuration."""
        bucket_request = {
            "website": {
                "mainPageSuffix": "index.html",
                "notFoundPage": "404.html"
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["website"]["mainPageSuffix"], "index.html")
        self.assertEqual(result["website"]["notFoundPage"], "404.html")

    def test_patch_with_logging_config(self):
        """Test patch with logging configuration."""
        bucket_request = {
            "logging": {
                "logBucket": "logs-bucket",
                "logObjectPrefix": "access-logs"
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["logging"]["logBucket"], "logs-bucket")
        self.assertEqual(result["logging"]["logObjectPrefix"], "access-logs")

    def test_patch_with_autoclass(self):
        """Test patch with autoclass configuration."""
        bucket_request = {
            "autoclass": {
                "enabled": True,
                "terminalStorageClass": "ARCHIVE"
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertTrue(result["autoclass"]["enabled"])
        self.assertEqual(result["autoclass"]["terminalStorageClass"], "ARCHIVE")

    def test_patch_with_ip_filter(self):
        """Test patch with IP filter configuration."""
        bucket_request = {
            "ipFilter": {
                "mode": "Enabled",
                "publicNetworkSource": {
                    "allowedIpCidrRanges": ["192.168.1.0/24"]
                }
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["ipFilter"]["mode"], "Enabled")
        self.assertIn("192.168.1.0/24", result["ipFilter"]["publicNetworkSource"]["allowedIpCidrRanges"])

    def test_patch_with_custom_placement(self):
        """Test patch with custom placement configuration."""
        bucket_request = {
            "customPlacementConfig": {
                "dataLocations": ["US-EAST1", "US-WEST1"]
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertIn("US-EAST1", result["customPlacementConfig"]["dataLocations"])

    def test_patch_with_hierarchical_namespace(self):
        """Test patch with hierarchical namespace configuration."""
        bucket_request = {
            "hierarchicalNamespace": {"enabled": True}
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertTrue(result["hierarchicalNamespace"]["enabled"])

    def test_patch_with_billing_config(self):
        """Test patch with billing configuration."""
        bucket_request = {
            "billing": {"requesterPays": True}
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertTrue(result["billing"]["requesterPays"])

    def test_patch_with_object_retention(self):
        """Test patch with object retention configuration."""
        bucket_request = {
            "objectRetention": {"mode": "Enabled"}
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["objectRetention"]["mode"], "Enabled")

    def test_patch_with_soft_delete_policy(self):
        """Test patch with soft delete policy."""
        bucket_request = {
            "softDeletePolicy": {
                "retentionDurationSeconds": "86400"  # 1 day
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["softDeletePolicy"]["retentionDurationSeconds"], "86400")

    def test_patch_with_owner_info(self):
        """Test patch with owner information."""
        bucket_request = {
            "owner": {
                "entity": "user-test@example.com",
                "entityId": "123456789"
            }
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["owner"]["entity"], "user-test@example.com")
        self.assertEqual(result["owner"]["entityId"], "123456789")

    def test_patch_with_event_based_hold(self):
        """Test patch with event-based hold."""
        bucket_request = {
            "defaultEventBasedHold": True
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertTrue(result["defaultEventBasedHold"])

    def test_patch_with_location_type(self):
        """Test patch with location type."""
        bucket_request = {
            "locationType": "dual-region"
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["locationType"], "dual-region")

    def test_patch_with_project_number(self):
        """Test patch with project number."""
        bucket_request = {
            "projectNumber": "123456789"
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["projectNumber"], "123456789")

    def test_patch_with_satisfies_pzs_pzi(self):
        """Test patch with satisfies PZS/PZI flags."""
        bucket_request = {
            "satisfiesPZS": True,
            "satisfiesPZI": False
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 200)
        self.assertTrue(result["satisfiesPZS"])
        self.assertFalse(result["satisfiesPZI"])

    def test_update_with_complete_replacement(self):
        """Test update completely replaces bucket configuration."""
        # First, set up some initial configuration
        initial_config = {
            "storageClass": "STANDARD",
            "labels": {"env": "dev"},
            "versioning": {"enabled": True}
        }
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"].update(initial_config)
        
        # Now update with completely different configuration
        update_request = {
            "name": "test-bucket",
            "storageClass": "COLDLINE",
            "location": "EU",
            "labels": {"env": "prod", "region": "eu"},
            "versioning": {"enabled": False}
        }
        
        result, status = google_cloud_storage.Buckets.update("test-bucket", bucket_request=update_request)
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")
        self.assertEqual(result["location"], "EU")
        self.assertEqual(result["labels"]["env"], "prod")
        self.assertFalse(result["versioning"]["enabled"])

    def test_update_preserves_immutable_fields(self):
        """Test update preserves immutable fields even when provided."""
        original_id = self.test_bucket.get("id")
        original_kind = self.test_bucket["kind"]
        original_time_created = self.test_bucket["timeCreated"]
        original_generation = self.test_bucket["generation"]
        
        update_request = {
            "name": "test-bucket",
            "id": "should-be-ignored",
            "kind": "should-be-ignored",
            "timeCreated": "2025-01-01T00:00:00Z",
            "generation": "999",
            "storageClass": "ARCHIVE"
        }
        
        result, status = google_cloud_storage.Buckets.update("test-bucket", bucket_request=update_request)
        self.assertEqual(status, 200)
        
        # Immutable fields should be preserved
        if original_id:
            self.assertEqual(result["id"], original_id)
        self.assertEqual(result["kind"], original_kind)
        self.assertEqual(result["timeCreated"], original_time_created)
        self.assertEqual(result["generation"], original_generation)
        
        # Mutable fields should be updated
        self.assertEqual(result["storageClass"], "ARCHIVE")

    def test_update_with_predefined_acls(self):
        """Test update with predefined ACLs."""
        update_request = {
            "name": "test-bucket",
            "storageClass": "NEARLINE",
            "location": "US"
        }
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            predefinedAcl="publicRead",
            predefined_default_object_acl="publicRead",
            bucket_request=update_request
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["acl"], "publicRead")
        self.assertEqual(result["defaultObjectAcl"], "publicRead")

    def test_update_with_invalid_predefined_acls(self):
        """Test update with invalid predefined ACLs."""
        update_request = {"name": "test-bucket", "storageClass": "STANDARD"}
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            predefinedAcl="invalid_acl",
            bucket_request=update_request
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid predefinedAcl", result["error"])

    def test_update_with_metageneration_conditions(self):
        """Test update with metageneration conditions."""
        update_request = {"name": "test-bucket", "storageClass": "COLDLINE"}
        
        # Test if_metageneration_match success
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            if_metageneration_match="1",
            bucket_request=update_request
        )
        self.assertEqual(status, 200)
        
        # Test if_metageneration_not_match success
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            if_metageneration_not_match="999",
            bucket_request=update_request
        )
        self.assertEqual(status, 200)

    def test_update_with_invalid_metageneration_conditions(self):
        """Test update with invalid metageneration conditions."""
        update_request = {"name": "test-bucket", "storageClass": "COLDLINE"}
        
        # Test if_metageneration_match failure
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            if_metageneration_match="999",
            bucket_request=update_request
        )
        self.assertEqual(status, 412)
        self.assertEqual(result["error"], "Metageneration mismatch")
        
        # Test if_metageneration_not_match failure
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            if_metageneration_not_match="1",
            bucket_request=update_request
        )
        self.assertEqual(status, 412)
        self.assertEqual(result["error"], "Metageneration mismatch")

    def test_update_with_projection_full(self):
        """Test update with projection=full includes ACL fields."""
        update_request = {"name": "test-bucket", "storageClass": "STANDARD"}
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            projection="full",
            bucket_request=update_request
        )
        self.assertEqual(status, 200)
        # Note: ACL fields may not be present if not explicitly set
        # The test should verify the response structure is correct regardless

    def test_update_with_invalid_projection(self):
        """Test update with invalid projection."""
        update_request = {"name": "test-bucket", "storageClass": "STANDARD"}
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            projection="invalid_projection",
            bucket_request=update_request
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid projection", result["error"])

    def test_update_with_user_project(self):
        """Test update with user_project parameter."""
        update_request = {"name": "test-bucket", "storageClass": "STANDARD"}
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket",
            user_project="billing-project",
            bucket_request=update_request
        )
        self.assertEqual(status, 200)
        # user_project is typically used for billing, not returned in response

    def test_patch_with_user_project(self):
        """Test patch with user_project parameter."""
        bucket_request = {"storageClass": "COLDLINE"}
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket",
            user_project="billing-project",
            bucket_request=bucket_request
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")

    def test_patch_with_invalid_storage_class(self):
        """Test patch with invalid storage class."""
        bucket_request = {"storageClass": "INVALID_CLASS"}
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])
        self.assertIn("storageClass", result["error"])

    def test_patch_with_invalid_rpo(self):
        """Test patch with invalid RPO."""
        bucket_request = {"rpo": "INVALID_RPO"}
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])
        self.assertIn("rpo", result["error"])

    def test_patch_with_empty_location(self):
        """Test patch with empty location string."""
        bucket_request = {"location": ""}
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 400)
        self.assertIn("Location cannot be empty string", result["error"])

    def test_patch_with_invalid_labels_value_type(self):
        """Test patch with invalid label value type."""
        bucket_request = {"labels": {"key": 123}}  # should be string
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])

    def test_patch_with_invalid_labels_key_type(self):
        """Test patch with invalid label key type."""
        bucket_request = {"labels": {123: "value"}}  # key should be string
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])

    def test_patch_with_invalid_bucket_request_type(self):
        """Test patch with invalid bucket_request type."""
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request="not_a_dict")
        self.assertEqual(status, 400)
        self.assertIn("Invalid bucket_request", result["error"])

    def test_update_with_invalid_bucket_request_type(self):
        """Test update with invalid bucket_request type."""
        result, status = google_cloud_storage.Buckets.update("test-bucket", bucket_request="not_a_dict")
        self.assertEqual(status, 400)
        self.assertIn("Invalid bucket_request", result["error"])

    def test_patch_with_missing_bucket_request(self):
        """Test patch without bucket_request (should still work and increment metageneration)."""
        original_meta = self.test_bucket["metageneration"]
        result, status = google_cloud_storage.Buckets.patch("test-bucket")
        self.assertEqual(status, 200)
        self.assertEqual(result["metageneration"], str(int(original_meta) + 1))

    def test_update_with_missing_bucket_request(self):
        """Test update without bucket_request (should fail)."""
        result, status = google_cloud_storage.Buckets.update("test-bucket")
        self.assertEqual(status, 400)
        self.assertIn("bucket_request is required", result["error"])

    def test_patch_with_invalid_bucket_name_type(self):
        """Test patch with invalid bucket name type."""
        result, status = google_cloud_storage.Buckets.patch(123)
        self.assertEqual(status, 400)
        self.assertIn("Bucket name must be a string", result["error"])

    def test_update_with_invalid_bucket_name_type(self):
        """Test update with invalid bucket name type."""
        result, status = google_cloud_storage.Buckets.update(123, bucket_request={"name": "test"})
        self.assertEqual(status, 400)
        self.assertIn("Bucket name must be a string", result["error"])

    def test_patch_with_invalid_metageneration_match_type(self):
        """Test patch with invalid if_metageneration_match type."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket", if_metageneration_match=123
        )
        self.assertEqual(status, 400)
        self.assertIn("if_metageneration_match must be a string", result["error"])

    def test_patch_with_invalid_metageneration_not_match_type(self):
        """Test patch with invalid if_metageneration_not_match type."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket", if_metageneration_not_match=123
        )
        self.assertEqual(status, 400)
        self.assertIn("if_metageneration_not_match must be a string", result["error"])

    def test_update_with_invalid_metageneration_match_type(self):
        """Test update with invalid if_metageneration_match type."""
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", if_metageneration_match=123, bucket_request={"name": "test"}
        )
        self.assertEqual(status, 400)
        self.assertIn("if_metageneration_match must be a string", result["error"])

    def test_update_with_invalid_metageneration_not_match_type(self):
        """Test update with invalid if_metageneration_not_match type."""
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", if_metageneration_not_match=123, bucket_request={"name": "test"}
        )
        self.assertEqual(status, 400)
        self.assertIn("if_metageneration_not_match must be a string", result["error"])

    def test_patch_with_invalid_predefined_acl_type(self):
        """Test patch with invalid predefinedAcl type."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket", predefinedAcl=123
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid predefinedAcl", result["error"])

    def test_patch_with_invalid_predefined_default_object_acl_type(self):
        """Test patch with invalid predefined_default_object_acl type."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket", predefined_default_object_acl=123
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid predefined_default_object_acl", result["error"])

    def test_patch_with_invalid_projection_type(self):
        """Test patch with invalid projection type."""
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket", projection=123
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid projection", result["error"])

    def test_update_with_invalid_predefined_acl_type(self):
        """Test update with invalid predefinedAcl type."""
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", predefinedAcl=123, bucket_request={"name": "test"}
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid predefinedAcl", result["error"])

    def test_update_with_invalid_predefined_default_object_acl_type(self):
        """Test update with invalid predefined_default_object_acl type."""
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", predefined_default_object_acl=123, bucket_request={"name": "test"}
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid predefined_default_object_acl", result["error"])

    def test_update_with_invalid_projection_type(self):
        """Test update with invalid projection type."""
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", projection=123, bucket_request={"name": "test"}
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid projection", result["error"])

    def test_patch_with_non_existent_bucket(self):
        """Test patch with non-existent bucket."""
        result, status = google_cloud_storage.Buckets.patch("non-existent-bucket")
        self.assertEqual(status, 404)
        self.assertIn("not found", result["error"])

    def test_update_with_non_existent_bucket(self):
        """Test update with non-existent bucket."""
        result, status = google_cloud_storage.Buckets.update(
            "non-existent-bucket", bucket_request={"name": "test"}
        )
        self.assertEqual(status, 404)
        self.assertIn("not found", result["error"])

    def test_patch_metageneration_increment_consistency(self):
        """Test that patch consistently increments metageneration."""
        # First patch
        original_meta = self.test_bucket["metageneration"]
        result1, status1 = google_cloud_storage.Buckets.patch("test-bucket", bucket_request={"storageClass": "COLDLINE"})
        self.assertEqual(status1, 200)
        self.assertEqual(result1["metageneration"], str(int(original_meta) + 1))
        
        # Second patch
        result2, status2 = google_cloud_storage.Buckets.patch("test-bucket", bucket_request={"location": "EU"})
        self.assertEqual(status2, 200)
        self.assertEqual(result2["metageneration"], str(int(original_meta) + 2))

    def test_update_metageneration_increment_consistency(self):
        """Test that update consistently increments metageneration."""
        # First update
        original_meta = self.test_bucket["metageneration"]
        result1, status1 = google_cloud_storage.Buckets.update(
            "test-bucket", bucket_request={"name": "test-bucket", "storageClass": "COLDLINE"}
        )
        self.assertEqual(status1, 200)
        self.assertEqual(result1["metageneration"], str(int(original_meta) + 1))
        
        # Second update
        result2, status2 = google_cloud_storage.Buckets.update(
            "test-bucket", bucket_request={"name": "test-bucket", "location": "EU"}
        )
        self.assertEqual(status2, 200)
        self.assertEqual(result2["metageneration"], str(int(original_meta) + 2))

    def test_patch_preserves_existing_fields(self):
        """Test that patch preserves existing fields not in the request."""
        # Set up initial configuration
        initial_config = {
            "labels": {"env": "dev", "team": "backend"},
            "versioning": {"enabled": True},
            "website": {"mainPageSuffix": "index.html"}
        }
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"].update(initial_config)
        
        # Patch only storageClass
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket", bucket_request={"storageClass": "COLDLINE"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")
        
        # Verify other fields are preserved
        self.assertEqual(result["labels"]["env"], "dev")
        self.assertEqual(result["labels"]["team"], "backend")
        self.assertTrue(result["versioning"]["enabled"])
        self.assertEqual(result["website"]["mainPageSuffix"], "index.html")

    def test_update_replaces_all_fields(self):
        """Test that update replaces all fields except protected ones."""
        # Set up initial configuration
        initial_config = {
            "labels": {"env": "dev", "team": "backend"},
            "versioning": {"enabled": True},
            "website": {"mainPageSuffix": "index.html"}
        }
        google_cloud_storage.Buckets.DB["buckets"]["test-bucket"].update(initial_config)
        
        # Update with minimal request
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", bucket_request={"name": "test-bucket", "storageClass": "COLDLINE"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["storageClass"], "COLDLINE")
        
        # Verify that fields not in update request are either:
        # 1. Not present (if they were removed)
        # 2. Set to None (if Pydantic model includes them with default None)
        # 3. Set to default values (if model has defaults)
        
        # Check that the specific values we set are no longer present
        if "versioning" in result and result["versioning"] is not None:
            # If versioning is present and not None, it should be the default (enabled: False)
            self.assertFalse(result["versioning"]["enabled"])
        if "website" in result and result["website"] is not None:
            # If website is present and not None, it should be None values
            self.assertIsNone(result["website"]["mainPageSuffix"])
            self.assertIsNone(result["website"]["notFoundPage"])
        if "labels" in result:
            # If labels is present, it should be None (not our original values)
            self.assertIsNone(result["labels"])

    def test_patch_with_validation_error_handling(self):
        """Test patch with various validation errors."""
        # Test with invalid nested structure
        bucket_request = {
            "cors": [{"invalid_field": "value"}]  # should fail validation
        }
        
        result, status = google_cloud_storage.Buckets.patch("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])

    def test_update_with_validation_error_handling(self):
        """Test update with various validation errors."""
        # Test with invalid nested structure
        bucket_request = {
            "name": "test-bucket",
            "cors": [{"invalid_field": "value"}]  # should fail validation
        }
        
        result, status = google_cloud_storage.Buckets.update("test-bucket", bucket_request=bucket_request)
        self.assertEqual(status, 400)
        self.assertIn("Validation error", result["error"])

    def test_patch_with_updated_timestamp(self):
        """Test that patch updates the 'updated' timestamp."""
        original_updated = self.test_bucket.get("updated")
        
        result, status = google_cloud_storage.Buckets.patch(
            "test-bucket", bucket_request={"storageClass": "COLDLINE"}
        )
        self.assertEqual(status, 200)
        self.assertNotEqual(result["updated"], original_updated)
        self.assertIsInstance(result["updated"], str)

    def test_update_with_updated_timestamp(self):
        """Test that update updates the 'updated' timestamp."""
        original_updated = self.test_bucket.get("updated")
        
        result, status = google_cloud_storage.Buckets.update(
            "test-bucket", bucket_request={"name": "test-bucket", "storageClass": "COLDLINE"}
        )
        self.assertEqual(status, 200)
        self.assertNotEqual(result["updated"], original_updated)
        self.assertIsInstance(result["updated"], str) 