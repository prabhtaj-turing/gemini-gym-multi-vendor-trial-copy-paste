"""
Comprehensive test cases for bucket insert method with Pydantic validation.
"""

import unittest
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from unittest.mock import patch, MagicMock

# Add the path to access the modules
sys.path.append("APIs")

from common_utils.base_case import BaseTestCaseWithErrorHandler
import google_cloud_storage

try:
    from google_cloud_storage.SimulationEngine.models import BucketRequest
except ImportError:
    BucketRequest = None


class TestBucketInsert(BaseTestCaseWithErrorHandler):
    """Test cases for bucket insert operations with Pydantic validation."""

    def setUp(self):
        """Set up test environment before each test."""
        # Reset DB using the exact same import path as the insert function
        try:
            from google_cloud_storage.SimulationEngine.db import DB as TestDB
            TestDB.clear()
            TestDB["buckets"] = {}
            self.test_db = TestDB
        except ImportError:
            # Fallback approach
            import google_cloud_storage.Buckets as BucketsModule
            if hasattr(BucketsModule, 'DB'):
                BucketsModule.DB.clear()
                BucketsModule.DB["buckets"] = {}
                self.test_db = BucketsModule.DB
            else:
                # Create a mock DB if needed
                self.test_db = {"buckets": {}}

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'test_db') and self.test_db:
            self.test_db.clear()
            self.test_db["buckets"] = {}

    def _verify_bucket_created(self, bucket_name):
        """Helper method to verify a bucket was created properly."""
        # Check in test response and DB
        try:
            from google_cloud_storage.SimulationEngine.db import DB
            return bucket_name in DB.get("buckets", {})
        except:
            return True  # Assume success if DB check fails

    # === BASIC FUNCTIONALITY TESTS ===
    
    def test_insert_bucket_basic_success(self):
        """Test successful basic bucket creation."""
        bucket_request = {
            "name": "test-bucket-basic",
            "location": "US",
            "storageClass": "STANDARD"
        }
        
        result = google_cloud_storage.Buckets.insert(
            "test-project", 
            bucket_request=bucket_request
        )
        
        self.assertIn("bucket", result)
        bucket_data = result["bucket"]
        self.assertEqual(bucket_data["name"], "test-bucket-basic")
        self.assertEqual(bucket_data["location"], "US")
        self.assertEqual(bucket_data["storageClass"], "STANDARD")
        self.assertEqual(bucket_data["project"], "test-project")
        self.assertEqual(bucket_data["metageneration"], "1")
        self.assertEqual(bucket_data["generation"], "1")

    def test_insert_bucket_minimal_request(self):
        """Test bucket creation with only required name field."""
        bucket_request = {"name": "minimal-bucket-test"}
        
        result = google_cloud_storage.Buckets.insert(
            "test-project", 
            bucket_request=bucket_request
        )
        
        self.assertIn("bucket", result)
        bucket_data = result["bucket"]
        self.assertEqual(bucket_data["name"], "minimal-bucket-test")
        self.assertEqual(bucket_data["project"], "test-project")
        self.assertEqual(bucket_data["storageClass"], "STANDARD")
        self.assertEqual(bucket_data["location"], "US")

    def test_insert_bucket_auto_generated_name(self):
        """Test insert without bucket_request (auto-generated name)."""
        result = google_cloud_storage.Buckets.insert("test-project")
        
        self.assertIn("bucket", result)
        bucket_data = result["bucket"]
        self.assertIn("name", bucket_data)
        self.assertTrue(bucket_data["name"].startswith("bucket-"))
        self.assertEqual(bucket_data["project"], "test-project")
        self.assertEqual(bucket_data["storageClass"], "STANDARD")
        self.assertEqual(bucket_data["location"], "US")

    def test_insert_bucket_metadata_fields(self):
        """Test that insert generates proper metadata fields."""
        bucket_request = {"name": "metadata-test", "location": "US"}
        
        result = google_cloud_storage.Buckets.insert("test-project", bucket_request=bucket_request)
        
        bucket_data = result["bucket"]
        
        # Check generated metadata
        self.assertEqual(bucket_data["name"], "metadata-test")
        self.assertEqual(bucket_data["id"], "test-project/metadata-test")
        self.assertEqual(bucket_data["kind"], "storage#bucket")
        self.assertEqual(bucket_data["projectNumber"], "123456789012")
        self.assertIn("timeCreated", bucket_data)
        self.assertIn("updated", bucket_data)
        self.assertIn("etag", bucket_data)
        self.assertIn("selfLink", bucket_data)

    def test_insert_bucket_timestamp_format(self):
        """Test that timestamps are in proper ISO format."""
        bucket_request = {"name": "timestamp-test", "location": "US"}
        
        result = google_cloud_storage.Buckets.insert("test-project", bucket_request=bucket_request)
        bucket_data = result["bucket"]
        
        # Check timestamp formats
        self.assertTrue(bucket_data["timeCreated"].endswith("Z"))
        self.assertTrue(bucket_data["updated"].endswith("Z"))
        
        # Verify ISO format
        from datetime import datetime
        try:
            datetime.fromisoformat(bucket_data["timeCreated"].replace('Z', '+00:00'))
            datetime.fromisoformat(bucket_data["updated"].replace('Z', '+00:00'))
        except ValueError:
            self.fail("Timestamps are not in valid ISO format")

    # === PARAMETER VALIDATION TESTS ===

    def test_insert_invalid_project_type(self):
        """Test insert with invalid project type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.insert(123, bucket_request={"name": "test", "location": "US"})
        self.assertIn("Project must be a string", str(context.exception))

    def test_insert_invalid_bucket_request_type(self):
        """Test insert with invalid bucket_request type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.insert("test-project", bucket_request="invalid")
        self.assertIn("Invalid bucket_request", str(context.exception))

    def test_insert_missing_bucket_name(self):
        """Test insert without bucket name."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.insert("test-project", bucket_request={"location": "US"})
        self.assertIn("Bucket name is required", str(context.exception))

    def test_insert_duplicate_bucket_name(self):
        """Test insert with duplicate bucket name."""
        bucket_request = {"name": "duplicate-test", "location": "US"}
        
        # First insert should succeed
        result1 = google_cloud_storage.Buckets.insert("test-project", bucket_request=bucket_request)
        self.assertIn("bucket", result1)
        
        # Second insert should fail
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.insert("test-project", bucket_request=bucket_request)
        self.assertIn("already exists", str(context.exception))

    def test_insert_empty_bucket_request(self):
        """Test insert with empty bucket_request dictionary."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.insert("test-project", bucket_request={})
        self.assertIn("Bucket name is required", str(context.exception))

    # === ACL AND PROJECTION TESTS ===

    def test_insert_with_predefined_acls(self):
        """Test bucket creation with predefined ACLs."""
        bucket_request = {"name": "acl-test", "location": "US"}
        
        result = google_cloud_storage.Buckets.insert(
            "test-project",
            predefinedAcl="publicRead",
            predefined_default_object_acl="bucketOwnerRead",
            projection="full",
            bucket_request=bucket_request
        )
        
        bucket_data = result["bucket"]
        self.assertEqual(bucket_data["name"], "acl-test")
        self.assertEqual(bucket_data["acl"], "publicRead")
        self.assertEqual(bucket_data["defaultObjectAcl"], "bucketOwnerRead")

    def test_insert_projection_filtering(self):
        """Test projection response filtering."""
        # Test noAcl projection
        result_no_acl = google_cloud_storage.Buckets.insert(
            "test-project",
            projection="noAcl",
            bucket_request={"name": "proj-no-acl", "location": "US"}
        )
        
        bucket_no_acl = result_no_acl["bucket"]
        self.assertNotIn("acl", bucket_no_acl)
        self.assertNotIn("defaultObjectAcl", bucket_no_acl)
        
        # Test full projection
        result_full = google_cloud_storage.Buckets.insert(
            "test-project",
            projection="full",
            bucket_request={"name": "proj-full", "location": "US"}
        )
        
        bucket_full = result_full["bucket"]
        self.assertIn("acl", bucket_full)
        self.assertIn("defaultObjectAcl", bucket_full)

    def test_insert_invalid_predefined_acl(self):
        """Test insert with invalid predefined ACL."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.insert(
                "test-project",
                predefinedAcl="invalid_acl",
                bucket_request={"name": "invalid-acl", "location": "US"}
            )
        self.assertIn("Invalid predefinedAcl", str(context.exception))

    def test_insert_invalid_projection(self):
        """Test insert with invalid projection."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.insert(
                "test-project",
                projection="invalid_projection",
                bucket_request={"name": "invalid-proj", "location": "US"}
            )
        self.assertIn("Invalid projection", str(context.exception))

    # === COMPLEX CONFIGURATION TESTS ===

    def test_insert_complex_configuration(self):
        """Test bucket creation with complex nested configuration."""
        bucket_request = {
            "name": "complex-config",
            "location": "EU",
            "storageClass": "COLDLINE",
            "labels": {"environment": "test", "team": "backend"},
            "versioning": {"enabled": True},
            "lifecycle": {
                "rule": [{
                    "action": {"type": "Delete", "storageClass": "ARCHIVE"},
                    "condition": {"age": 30, "isLive": True}
                }]
            },
            "cors": [{
                "maxAgeSeconds": 3600,
                "method": ["GET", "POST"],
                "origin": ["https://example.com"],
                "responseHeader": ["Content-Type"]
            }]
        }
        
        result = google_cloud_storage.Buckets.insert("test-project", bucket_request=bucket_request)
        
        bucket_data = result["bucket"]
        self.assertEqual(bucket_data["name"], "complex-config")
        self.assertEqual(bucket_data["location"], "EU")
        self.assertEqual(bucket_data["storageClass"], "COLDLINE")
        self.assertEqual(bucket_data["labels"]["environment"], "test")
        self.assertTrue(bucket_data["versioning"]["enabled"])
        self.assertEqual(bucket_data["lifecycle"]["rule"][0]["action"]["type"], "Delete")
        self.assertEqual(bucket_data["cors"][0]["maxAgeSeconds"], 3600)

    def test_insert_iam_and_encryption(self):
        """Test bucket creation with IAM and encryption."""
        bucket_request = {
            "name": "secure-config",
            "location": "US",
            "iamConfiguration": {
                "uniformBucketLevelAccess": {"enabled": True},
                "publicAccessPrevention": "enforced"
            },
            "encryption": {
                "defaultKmsKeyName": "projects/test/locations/us/keyRings/test/cryptoKeys/test"
            }
        }
        
        result = google_cloud_storage.Buckets.insert("test-project", bucket_request=bucket_request)
        
        bucket_data = result["bucket"]
        self.assertEqual(bucket_data["name"], "secure-config")
        self.assertTrue(bucket_data["iamConfiguration"]["uniformBucketLevelAccess"]["enabled"])
        self.assertEqual(bucket_data["iamConfiguration"]["publicAccessPrevention"], "enforced")
        self.assertIn("defaultKmsKeyName", bucket_data["encryption"])

    def test_insert_retention_policies(self):
        """Test bucket creation with retention and lifecycle policies."""
        bucket_request = {
            "name": "retention-config",
            "location": "US",
            "retentionPolicy": {"retentionPeriod": "2592000", "isLocked": False},
            "softDeletePolicy": {"retentionDurationSeconds": "86400"},
            "defaultEventBasedHold": True
        }
        
        result = google_cloud_storage.Buckets.insert(
            "test-project",
            enableObjectRetention=True,
            bucket_request=bucket_request
        )
        
        bucket_data = result["bucket"]
        self.assertEqual(bucket_data["name"], "retention-config")
        self.assertEqual(bucket_data["retentionPolicy"]["retentionPeriod"], "2592000")
        self.assertFalse(bucket_data["retentionPolicy"]["isLocked"])
        self.assertTrue(bucket_data["defaultEventBasedHold"])
        self.assertTrue(bucket_data["enableObjectRetention"])

    # === VALIDATION ERROR TESTS ===

    def test_insert_pydantic_validation_errors(self):
        """Test Pydantic validation errors."""
        # Invalid storage class
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.insert(
                "test-project",
                bucket_request={
                    "name": "invalid-storage",
                    "location": "US",
                    "storageClass": "INVALID_CLASS"
                }
            )
        self.assertIn("Validation error", str(context.exception))

    def test_insert_invalid_labels(self):
        """Test insert with invalid label types."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.insert(
                "test-project",
                bucket_request={
                    "name": "invalid-labels",
                    "location": "US",
                    "labels": {"key": 123}  # should be string
                }
            )
        self.assertIn("Validation error", str(context.exception))

    def test_insert_validation_error_details(self):
        """Test that ValidationError details are properly formatted."""
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.insert(
                "test-project",
                bucket_request={
                    "name": "validation-detail",
                    "location": "US",
                    "storageClass": "NONEXISTENT_CLASS"
                }
            )
        
        error_message = str(context.exception)
        self.assertIn("Validation error", error_message)

    # === FALLBACK VALIDATION TESTS ===

    def test_insert_fallback_validation_path(self):
        """Test fallback validation when Pydantic unavailable."""
        import google_cloud_storage.Buckets as Buckets
        original_bucket_request = getattr(Buckets, 'BucketRequest', None)
        
        # Disable BucketRequest to test fallback
        Buckets.BucketRequest = None
        
        try:
            # Test valid fallback case
            result = google_cloud_storage.Buckets.insert(
                "test-project",
                bucket_request={
                    "name": "fallback-valid",
                    "location": "US",
                    "storageClass": "STANDARD",
                    "rpo": "DEFAULT"
                }
            )
            
            self.assertIn("bucket", result)
            self.assertEqual(result["bucket"]["name"], "fallback-valid")
            
            # Test invalid fallback case
            with self.assertRaises(ValueError) as context:
                google_cloud_storage.Buckets.insert(
                    "test-project",
                    bucket_request={"name": "fallback-invalid", "location": ""}
                )
            self.assertIn("Location cannot be empty string", str(context.exception))
            
        finally:
            # Restore BucketRequest
            if original_bucket_request is not None:
                Buckets.BucketRequest = original_bucket_request

    def test_insert_fallback_invalid_storage_class(self):
        """Test fallback validation with invalid storage class."""
        import google_cloud_storage.Buckets as Buckets
        original = getattr(Buckets, 'BucketRequest', None)
        Buckets.BucketRequest = None
        
        try:
            with self.assertRaises(ValueError) as context:
                google_cloud_storage.Buckets.insert(
                    "test-project",
                    bucket_request={
                        "name": "fallback-invalid-storage",
                        "location": "US",
                        "storageClass": "INVALID_CLASS"
                    }
                )
            self.assertIn("Invalid storageClass", str(context.exception))
        finally:
            if original is not None:
                Buckets.BucketRequest = original

    def test_insert_fallback_invalid_rpo(self):
        """Test fallback validation with invalid RPO."""
        import google_cloud_storage.Buckets as Buckets
        original = getattr(Buckets, 'BucketRequest', None)
        Buckets.BucketRequest = None
        
        try:
            with self.assertRaises(ValueError) as context:
                google_cloud_storage.Buckets.insert(
                    "test-project",
                    bucket_request={
                        "name": "fallback-invalid-rpo",
                        "location": "US",
                        "rpo": "INVALID_RPO"
                    }
                )
            self.assertIn("Invalid rpo", str(context.exception))
        finally:
            if original is not None:
                Buckets.BucketRequest = original

    # === FIELD PROTECTION AND EDGE CASES ===

    def test_insert_critical_field_protection(self):
        """Test that critical fields cannot be overridden."""
        bucket_request = {
            "name": "field-protection",
            "location": "US",
            "labels": {"test": "protection"}
        }
        
        result = google_cloud_storage.Buckets.insert(
            "test-project",
            enableObjectRetention=True,
            bucket_request=bucket_request
        )
        
        bucket_data = result["bucket"]
        
        # Critical fields should be set by function, not overridden
        self.assertEqual(bucket_data["project"], "test-project")
        self.assertTrue(bucket_data["enableObjectRetention"])
        self.assertEqual(bucket_data["kind"], "storage#bucket")
        self.assertEqual(bucket_data["labels"]["test"], "protection")

    def test_insert_none_value_filtering(self):
        """Test that None values are properly filtered."""
        bucket_request = {
            "name": "none-filtering",
            "location": "US",
            "labels": None,  # Should be filtered out
            "website": {"mainPageSuffix": "index.html"},  # Should be kept
            "cors": None  # Should be filtered out
        }
        
        result = google_cloud_storage.Buckets.insert("test-project", bucket_request=bucket_request)
        bucket_data = result["bucket"]
        
        self.assertEqual(bucket_data["name"], "none-filtering")
        
        # None values should not be present in final bucket
        self.assertNotIn("labels", bucket_data)
        self.assertNotIn("cors", bucket_data)
        
        # Non-None values should be present
        self.assertIn("website", bucket_data)
        self.assertEqual(bucket_data["website"]["mainPageSuffix"], "index.html")

    def test_insert_auto_name_uniqueness(self):
        """Test that auto-generated names are unique."""
        generated_names = set()
        
        for i in range(3):
            result = google_cloud_storage.Buckets.insert("test-project")
            bucket_name = result["bucket"]["name"]
            self.assertNotIn(bucket_name, generated_names)
            generated_names.add(bucket_name)
            self.assertTrue(bucket_name.startswith("bucket-"))

    def test_insert_error_recovery(self):
        """Test error recovery scenarios."""
        # Test that after failed insert, next insert works
        with self.assertRaises(ValueError):
            google_cloud_storage.Buckets.insert(
                "test-project",
                bucket_request={"name": "recovery-fail", "location": ""}
            )
        
        # Valid insert should work after failure
        result = google_cloud_storage.Buckets.insert(
            "test-project",
            bucket_request={"name": "recovery-success", "location": "US"}
        )
        
        self.assertIn("bucket", result)
        self.assertEqual(result["bucket"]["name"], "recovery-success")

    # === EXCEPTION HANDLING TESTS ===

    def test_insert_exception_handling(self):
        """Test proper exception handling."""
        # Mock datetime to cause exception
        with patch('google_cloud_storage.Buckets.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Mock error")
            
            with self.assertRaises(ValueError) as context:
                google_cloud_storage.Buckets.insert(
                    "test-project",
                    bucket_request={"name": "exception-test", "location": "US"}
                )
            self.assertIn("Validation error: Mock error", str(context.exception))

    def test_insert_user_project_handling(self):
        """Test that user_project parameter is handled correctly."""
        result = google_cloud_storage.Buckets.insert(
            "test-project",
            user_project="billing-project",
            bucket_request={"name": "user-project-test", "location": "US"}
        )
        
        bucket_data = result["bucket"]
        self.assertEqual(bucket_data["name"], "user-project-test")
        self.assertEqual(bucket_data["project"], "test-project")  # Should be main project

    # === COMPREHENSIVE INTEGRATION TEST ===

    def test_insert_comprehensive_integration(self):
        """Comprehensive test covering multiple code paths."""
        # Test 1: Normal Pydantic validation
        result1 = google_cloud_storage.Buckets.insert(
            "test-project",
            predefinedAcl="private",
            projection="full",
            enableObjectRetention=True,
            bucket_request={
                "name": "integration-1",
                "location": "EU",
                "storageClass": "ARCHIVE",
                "labels": {"integration": "test1"}
            }
        )
        self.assertIn("bucket", result1)
        self.assertEqual(result1["bucket"]["name"], "integration-1")
        
        # Test 2: Auto-generated name
        result2 = google_cloud_storage.Buckets.insert("test-project")
        self.assertIn("bucket", result2)
        auto_name = result2["bucket"]["name"]
        self.assertTrue(auto_name.startswith("bucket-"))
        
        # Test 3: Fallback validation
        import google_cloud_storage.Buckets as Buckets
        original = getattr(Buckets, 'BucketRequest', None)
        Buckets.BucketRequest = None
        
        try:
            result3 = google_cloud_storage.Buckets.insert(
                "test-project",
                bucket_request={
                    "name": "integration-3",
                    "location": "US",
                    "storageClass": "STANDARD"
                }
            )
            self.assertIn("bucket", result3)
            self.assertEqual(result3["bucket"]["name"], "integration-3")
        finally:
            if original is not None:
                Buckets.BucketRequest = original

        # All three buckets should be successfully created
        self.assertIn("integration-1", result1["bucket"]["name"])
        self.assertTrue(result2["bucket"]["name"].startswith("bucket-"))
        self.assertEqual(result3["bucket"]["name"], "integration-3")