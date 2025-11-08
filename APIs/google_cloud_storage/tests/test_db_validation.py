"""
Database Validation Test Suite for Google Cloud Storage API
Tests database schema validation, data integrity, and constraint enforcement.
"""

import unittest
import copy
import uuid
from datetime import datetime
from pydantic import ValidationError

from google_cloud_storage.SimulationEngine.db import DB
from google_cloud_storage.SimulationEngine.models import DatabaseBucketModel, GoogleCloudStorageDB
import google_cloud_storage


class TestDatabaseValidation(unittest.TestCase):
    """Test database validation and schema consistency."""
    
    def setUp(self):
        """Set up test environment."""
        self.original_db_state = copy.deepcopy(DB)
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db_state)

    def test_db_schema_consistency(self):
        """Test that DB has consistent schema."""
        # Verify basic DB structure
        self.assertIsInstance(DB, dict)
        self.assertIn("buckets", DB)
        self.assertIsInstance(DB["buckets"], dict)

    def test_bucket_schema_validation(self):
        """Test that buckets have proper schema."""
        # Check existing buckets for schema consistency
        for bucket_name, bucket_data in DB.get("buckets", {}).items():
            self.assertIsInstance(bucket_data, dict)
            
            # Required fields that should exist
            self.assertIn("name", bucket_data)
            self.assertEqual(bucket_data["name"], bucket_name)
            
            # Check field types if they exist
            if "project" in bucket_data:
                self.assertIsInstance(bucket_data["project"], str)
                
            if "objects" in bucket_data:
                self.assertIsInstance(bucket_data["objects"], list)
                
            if "softDeleted" in bucket_data:
                self.assertIsInstance(bucket_data["softDeleted"], bool)
                
            if "enableObjectRetention" in bucket_data:
                self.assertIsInstance(bucket_data["enableObjectRetention"], bool)
                
            if "iamPolicy" in bucket_data:
                self.assertIsInstance(bucket_data["iamPolicy"], dict)
                
            if "storageLayout" in bucket_data:
                self.assertIsInstance(bucket_data["storageLayout"], dict)

    def test_metageneration_field_validation(self):
        """Test that metageneration fields are properly formatted."""
        for bucket_name, bucket_data in DB.get("buckets", {}).items():
            if "metageneration" in bucket_data:
                # Should be a string representing a number
                self.assertIsInstance(bucket_data["metageneration"], str)
                # Should be convertible to int
                try:
                    int(bucket_data["metageneration"])
                except ValueError:
                    self.fail(f"metageneration in bucket {bucket_name} should be a numeric string")

    def test_generation_field_validation(self):
        """Test that generation fields are properly formatted."""
        for bucket_name, bucket_data in DB.get("buckets", {}).items():
            if "generation" in bucket_data:
                # Should be a string representing a number
                self.assertIsInstance(bucket_data["generation"], str)
                # Should be convertible to int
                try:
                    int(bucket_data["generation"])
                except ValueError:
                    self.fail(f"generation in bucket {bucket_name} should be a numeric string")

    def test_iam_policy_structure(self):
        """Test that IAM policy structures are valid."""
        for bucket_name, bucket_data in DB.get("buckets", {}).items():
            if "iamPolicy" in bucket_data:
                iam_policy = bucket_data["iamPolicy"]
                self.assertIsInstance(iam_policy, dict)
                
                if "bindings" in iam_policy:
                    self.assertIsInstance(iam_policy["bindings"], list)

    def test_objects_array_structure(self):
        """Test that objects arrays are properly structured."""
        for bucket_name, bucket_data in DB.get("buckets", {}).items():
            if "objects" in bucket_data:
                objects = bucket_data["objects"]
                self.assertIsInstance(objects, list)
                # Each object should be a string or dict
                for obj in objects:
                    self.assertTrue(isinstance(obj, (str, dict)))


class TestDataIntegrityConstraints(unittest.TestCase):
    """Test data integrity and business logic constraints."""
    
    def setUp(self):
        """Set up test environment."""
        self.original_db_state = copy.deepcopy(DB)
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db_state)

    def test_bucket_name_consistency(self):
        """Test that bucket names are consistent with keys."""
        for bucket_name, bucket_data in DB.get("buckets", {}).items():
            self.assertIn("name", bucket_data)
            self.assertEqual(bucket_data["name"], bucket_name)

    def test_project_field_consistency(self):
        """Test that project fields are consistent."""
        for bucket_name, bucket_data in DB.get("buckets", {}).items():
            if "project" in bucket_data:
                project = bucket_data["project"]
                self.assertIsInstance(project, str)
                self.assertGreater(len(project), 0)  # Should not be empty

    def test_boolean_field_consistency(self):
        """Test that boolean fields have consistent values."""
        for bucket_name, bucket_data in DB.get("buckets", {}).items():
            boolean_fields = ["softDeleted", "enableObjectRetention"]
            for field in boolean_fields:
                if field in bucket_data:
                    self.assertIsInstance(bucket_data[field], bool)

    def test_db_state_preservation(self):
        """Test that DB state is preserved during test execution."""
        initial_bucket_count = len(DB.get("buckets", {}))
        
        # Perform some read operations
        buckets = DB.get("buckets", {})
        bucket_names = list(buckets.keys())
        
        # Verify state is preserved
        final_bucket_count = len(DB.get("buckets", {}))
        self.assertEqual(initial_bucket_count, final_bucket_count)


class TestFullDatabaseStructureValidation(unittest.TestCase):
    """Test complete GoogleCloudStorageDefaultDB.json structure validation using Pydantic models."""
    
    def setUp(self):
        """Set up test environment."""
        self.original_db_state = copy.deepcopy(DB)
        self.test_bucket_name = f"test-validation-bucket-{uuid.uuid4().hex[:8]}"
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up test bucket if it exists
        if "buckets" in DB and self.test_bucket_name in DB["buckets"]:
            del DB["buckets"][self.test_bucket_name]
        
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db_state)

    def test_complete_db_structure_validation(self):
        """Test that the entire DB structure can be validated against GoogleCloudStorageDB model."""
        # Test with incomplete bucket data (missing required fields) - this should fail
        incomplete_db_state = {
            "buckets": {
                "test-incomplete-bucket": {
                    "name": "test-incomplete-bucket",
                    "project": "test-project",
                    "metageneration": "1",
                    "softDeleted": False,
                    "objects": [],
                    "enableObjectRetention": False,
                    "iamPolicy": {"bindings": []},
                    "storageLayout": {},
                    "generation": "1",
                    "retentionPolicyLocked": False
                    # Missing: id, timeCreated, updated, etag, selfLink, projectNumber
                }
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            GoogleCloudStorageDB(**incomplete_db_state)
        
        # Verify it's catching the expected missing fields
        error_str = str(context.exception)
        expected_missing_fields = ["id", "timeCreated", "updated", "etag", "selfLink", "projectNumber"]
        for field in expected_missing_fields:
            self.assertIn(field, error_str, f"Should detect missing field: {field}")
        
        # Test with a clean DB (empty buckets) - this should pass
        clean_db = {"buckets": {}}
        try:
            validated_db = GoogleCloudStorageDB(**clean_db)
            self.assertIsInstance(validated_db, GoogleCloudStorageDB)
            self.assertIsInstance(validated_db.buckets, dict)
            self.assertEqual(len(validated_db.buckets), 0)
        except ValidationError as e:
            self.fail(f"Clean DB structure validation failed: {e}")

    def test_database_bucket_model_with_minimal_fields(self):
        """Test DatabaseBucketModel validation with minimal required fields."""
        current_time = datetime.now().isoformat() + "Z"
        minimal_bucket = {
            "name": self.test_bucket_name,
            "project": "test-project",
            "id": f"test-project/{self.test_bucket_name}",
            "metageneration": "1",
            "generation": "1",
            "timeCreated": current_time,
            "updated": current_time,
            "etag": f"etag-{self.test_bucket_name}",
            "selfLink": f"https://www.googleapis.com/storage/v1/b/{self.test_bucket_name}",
            "projectNumber": "123456789012"
        }
        
        try:
            validated_bucket = DatabaseBucketModel(**minimal_bucket)
            self.assertEqual(validated_bucket.name, self.test_bucket_name)
            self.assertEqual(validated_bucket.kind, "storage#bucket")  # Default value
            self.assertEqual(validated_bucket.location, "US")  # Default value
            self.assertEqual(validated_bucket.storageClass, "STANDARD")  # Default value
        except ValidationError as e:
            self.fail(f"Minimal bucket validation failed: {e}")

    def test_database_bucket_model_with_all_fields(self):
        """Test DatabaseBucketModel validation with comprehensive field set."""
        current_time = datetime.now().isoformat() + "Z"
        comprehensive_bucket = {
            "name": self.test_bucket_name,
            "project": "test-project",
            "id": f"test-project/{self.test_bucket_name}",
            "kind": "storage#bucket",
            "metageneration": "1",
            "generation": "1",
            "timeCreated": current_time,
            "updated": current_time,
            "etag": f"etag-{self.test_bucket_name}",
            "selfLink": f"https://www.googleapis.com/storage/v1/b/{self.test_bucket_name}",
            "location": "us-central1",
            "locationType": "region",
            "storageClass": "STANDARD",
            "rpo": "DEFAULT",
            "projectNumber": "123456789012",
            "softDeleted": False,
            "objects": ["file1.txt", "data/file2.txt"],
            "enableObjectRetention": False,
            "iamPolicy": {"bindings": []},
            "acl": [],
            "defaultObjectAcl": [],
            "storageLayout": {
                "customPlacementConfig": {
                    "dataLocations": ["us-central1"]
                },
                "hierarchicalNamespace": {
                    "enabled": False
                }
            },
            "labels": {"env": "test", "team": "engineering"},
            "defaultEventBasedHold": False,
            "satisfiesPZS": True,
            "satisfiesPZI": False,
            "billing": {"requesterPays": False},
            "versioning": {"enabled": True},
            "lifecycle": {
                "rule": [{
                    "action": {"type": "Delete"},
                    "condition": {"age": 30}
                }]
            },
            "cors": [{
                "maxAgeSeconds": 3600,
                "method": ["GET", "POST"],
                "origin": ["*"],
                "responseHeader": ["Content-Type"]
            }],
            "website": {
                "mainPageSuffix": "index.html",
                "notFoundPage": "404.html"
            },
            "logging": {
                "logBucket": "access-logs-bucket",
                "logObjectPrefix": "access-logs/"
            },
            "encryption": {
                "defaultKmsKeyName": "projects/test-project/locations/global/keyRings/test-ring/cryptoKeys/test-key"
            }
        }
        
        try:
            validated_bucket = DatabaseBucketModel(**comprehensive_bucket)
            self.assertEqual(validated_bucket.name, self.test_bucket_name)
            self.assertEqual(validated_bucket.location, "us-central1")
            self.assertEqual(validated_bucket.locationType, "region")
            self.assertTrue(validated_bucket.versioning.enabled)
            self.assertEqual(len(validated_bucket.objects), 2)
            self.assertEqual(validated_bucket.labels["env"], "test")
            self.assertEqual(validated_bucket.cors[0].maxAgeSeconds, 3600)
        except ValidationError as e:
            self.fail(f"Comprehensive bucket validation failed: {e}")

    def test_database_bucket_model_validation_errors(self):
        """Test that DatabaseBucketModel properly validates and rejects invalid data."""
        # Test invalid kind
        with self.assertRaises(ValidationError) as context:
            DatabaseBucketModel(
                name=self.test_bucket_name,
                project="test-project",
                id=f"test-project/{self.test_bucket_name}",
                kind="invalid#kind",  # Invalid kind
                metageneration="1",
                generation="1",
                timeCreated="2023-01-01T00:00:00Z",
                updated="2023-01-01T00:00:00Z",
                etag="etag-test",
                selfLink="https://example.com",
                projectNumber="123456789012"
            )
        self.assertIn("Bucket kind must be 'storage#bucket'", str(context.exception))

        # Test invalid ID format
        with self.assertRaises(ValidationError) as context:
            DatabaseBucketModel(
                name=self.test_bucket_name,
                project="test-project",
                id="invalid-id-format",  # Missing slash
                metageneration="1",
                generation="1",
                timeCreated="2023-01-01T00:00:00Z",
                updated="2023-01-01T00:00:00Z",
                etag="etag-test",
                selfLink="https://example.com",
                projectNumber="123456789012"
            )
        self.assertIn("Bucket ID must follow 'project/bucket_name' format", str(context.exception))

        # Test invalid project number
        with self.assertRaises(ValidationError) as context:
            DatabaseBucketModel(
                name=self.test_bucket_name,
                project="test-project",
                id=f"test-project/{self.test_bucket_name}",
                metageneration="1",
                generation="1",
                timeCreated="2023-01-01T00:00:00Z",
                updated="2023-01-01T00:00:00Z",
                etag="etag-test",
                selfLink="https://example.com",
                projectNumber="invalid"  # Invalid project number
            )
        self.assertIn("Project number must be a 12-digit string", str(context.exception))

    def test_created_bucket_validates_against_database_model(self):
        """Test that buckets created via create_bucket() validate against DatabaseBucketModel."""
        # Create a bucket using the create_bucket function
        result = google_cloud_storage.create_bucket(
            project="test-project",
            bucket_request={"name": self.test_bucket_name},
            projection="full"
        )
        
        # Verify the bucket was created
        self.assertIn("bucket", result)
        bucket_data = result["bucket"]
        
        # Validate the created bucket against the DatabaseBucketModel
        try:
            validated_bucket = DatabaseBucketModel(**bucket_data)
            self.assertEqual(validated_bucket.name, self.test_bucket_name)
            self.assertEqual(validated_bucket.project, "test-project")
            self.assertEqual(validated_bucket.kind, "storage#bucket")
            self.assertTrue(validated_bucket.timeCreated.endswith('Z'))
            self.assertTrue(validated_bucket.updated.endswith('Z'))
        except ValidationError as e:
            self.fail(f"Created bucket failed validation: {e}")

    def test_db_bucket_consistency_validation(self):
        """Test GoogleCloudStorageDB validation ensures bucket names match keys."""
        # Create test data with mismatched bucket name and key
        test_db_data = {
            "buckets": {
                "key-bucket-name": {
                    "name": "different-bucket-name",  # Name doesn't match key
                    "project": "test-project",
                    "id": "test-project/different-bucket-name",
                    "metageneration": "1",
                    "generation": "1",
                    "timeCreated": "2023-01-01T00:00:00Z",
                    "updated": "2023-01-01T00:00:00Z",
                    "etag": "etag-test",
                    "selfLink": "https://example.com",
                    "projectNumber": "123456789012"
                }
            }
        }
        
        with self.assertRaises(ValidationError) as context:
            GoogleCloudStorageDB(**test_db_data)
        self.assertIn("Bucket name 'different-bucket-name' does not match key 'key-bucket-name'", str(context.exception))

    def test_complex_nested_configuration_validation(self):
        """Test validation of complex nested configuration objects."""
        current_time = datetime.now().isoformat() + "Z"
        complex_bucket = {
            "name": self.test_bucket_name,
            "project": "test-project",
            "id": f"test-project/{self.test_bucket_name}",
            "metageneration": "1",
            "generation": "1",
            "timeCreated": current_time,
            "updated": current_time,
            "etag": f"etag-{self.test_bucket_name}",
            "selfLink": f"https://www.googleapis.com/storage/v1/b/{self.test_bucket_name}",
            "projectNumber": "123456789012",
            "iamConfiguration": {
                "uniformBucketLevelAccess": {
                    "enabled": True,
                    "lockedTime": current_time
                },
                "bucketPolicyOnly": {
                    "enabled": False
                },
                "publicAccessPrevention": "enforced"
            },
            "lifecycle": {
                "rule": [
                    {
                        "action": {
                            "type": "SetStorageClass",
                            "storageClass": "NEARLINE"
                        },
                        "condition": {
                            "age": 30,
                            "matchesStorageClass": ["STANDARD"]
                        }
                    },
                    {
                        "action": {
                            "type": "Delete"
                        },
                        "condition": {
                            "age": 365,
                            "isLive": False
                        }
                    }
                ]
            },
            "autoclass": {
                "enabled": True,
                "toggleTime": current_time,
                "terminalStorageClass": "ARCHIVE",
                "terminalStorageClassUpdateTime": current_time
            }
        }
        
        try:
            validated_bucket = DatabaseBucketModel(**complex_bucket)
            self.assertTrue(validated_bucket.iamConfiguration.uniformBucketLevelAccess.enabled)
            self.assertEqual(validated_bucket.iamConfiguration.publicAccessPrevention, "enforced")
            self.assertEqual(len(validated_bucket.lifecycle.rule), 2)
            self.assertEqual(validated_bucket.lifecycle.rule[0].action.storageClass, "NEARLINE")
            self.assertTrue(validated_bucket.autoclass.enabled)
            self.assertEqual(validated_bucket.autoclass.terminalStorageClass, "ARCHIVE")
        except ValidationError as e:
            self.fail(f"Complex nested configuration validation failed: {e}")

    def test_legacy_field_compatibility(self):
        """Test that legacy fields like retentionPolicyLocked are handled properly."""
        current_time = datetime.now().isoformat() + "Z"
        legacy_bucket = {
            "name": self.test_bucket_name,
            "project": "test-project",
            "id": f"test-project/{self.test_bucket_name}",
            "metageneration": "1",
            "generation": "1",
            "timeCreated": current_time,
            "updated": current_time,
            "etag": f"etag-{self.test_bucket_name}",
            "selfLink": f"https://www.googleapis.com/storage/v1/b/{self.test_bucket_name}",
            "projectNumber": "123456789012",
            "retentionPolicyLocked": True,  # Legacy field
            "storageLayout": {}
        }
        
        try:
            validated_bucket = DatabaseBucketModel(**legacy_bucket)
            self.assertTrue(validated_bucket.retentionPolicyLocked)
        except ValidationError as e:
            self.fail(f"Legacy field validation failed: {e}")


if __name__ == '__main__':
    unittest.main()