import unittest
from unittest.mock import patch
import sys
import os
import copy

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

sys.path.append("APIs")
import google_cloud_storage


class TestRelocateFunction(unittest.TestCase):
    """Test cases for the relocate function with comprehensive coverage."""

    def setUp(self):
        """Set up test data before each test."""
        # Reset the DB to a known state
        google_cloud_storage.Buckets.DB["buckets"] = {
            "test-bucket-1": {
                "name": "test-bucket-1",
                "project": "test-project",
                "metageneration": "1",
                "location": "us-central1",
                "storageClass": "STANDARD",
                "timeCreated": "2024-01-01T00:00:00Z",
                "updated": "2024-01-01T00:00:00Z"
            },
            "test-bucket-2": {
                "name": "test-bucket-2",
                "project": "test-project",
                "metageneration": "5",
                "location": "us-east1",
                "storageClass": "REGIONAL"
            }
        }

    def tearDown(self):
        """Clean up after each test."""
        google_cloud_storage.Buckets.DB["buckets"] = {}

    # --- Success Cases ---

    def test_relocate_success_basic(self):
        """Test successful bucket relocation with minimal request body."""
        request_body = {"destinationLocation": "us-west1"}
        result = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        
        # Verify response structure
        self.assertIn("done", result)
        self.assertIn("metadata", result)
        self.assertIn("name", result)
        self.assertIn("selfLink", result)
        self.assertIn("kind", result)
        
        # Verify values
        self.assertFalse(result["done"])
        self.assertEqual(result["kind"], "storage#operation")
        self.assertEqual(result["metadata"]["requestedLocation"], "us-west1")
        self.assertEqual(result["metadata"]["bucket"], "test-bucket-1")
        self.assertEqual(result["metadata"]["operationType"], "RELOCATE_BUCKET")
        self.assertFalse(result["metadata"]["validateOnly"])

    def test_relocate_success_with_custom_placement(self):
        """Test successful bucket relocation with custom placement configuration."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": ["us-west1-a", "us-west1-b"]
            }
        }
        result = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        
        self.assertFalse(result["done"])
        self.assertEqual(result["kind"], "storage#operation")
        self.assertIn("customPlacementConfig", result["metadata"])
        self.assertEqual(result["metadata"]["customPlacementConfig"]["dataLocations"], ["us-west1-a", "us-west1-b"])

    def test_relocate_success_validate_only_true(self):
        """Test successful validation-only request."""
        request_body = {
            "destinationLocation": "us-west1",
            "validateOnly": True
        }
        result = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        
        # Verify validation-only response
        self.assertTrue(result["done"])
        self.assertEqual(result["kind"], "storage#operation")
        self.assertTrue(result["metadata"]["validateOnly"])
        self.assertEqual(result["metadata"]["validationResult"], "Request is valid")
        self.assertIn("validation", result["name"])
        self.assertIn("validation", result["selfLink"])

    def test_relocate_success_validate_only_false(self):
        """Test successful request with validateOnly explicitly set to False."""
        request_body = {
            "destinationLocation": "us-west1",
            "validateOnly": False
        }
        result = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        
        self.assertFalse(result["done"])
        self.assertFalse(result["metadata"]["validateOnly"])

    def test_relocate_success_complex_request(self):
        """Test successful relocation with all optional fields."""
        request_body = {
            "destinationLocation": "europe-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": ["europe-west1-a", "europe-west1-b"]
            },
            "validateOnly": False
        }
        result = google_cloud_storage.Buckets.relocate("test-bucket-2", request_body)
        
        self.assertFalse(result["done"])
        self.assertEqual(result["metadata"]["requestedLocation"], "europe-west1")
        self.assertEqual(result["metadata"]["bucket"], "test-bucket-2")
        self.assertIn("customPlacementConfig", result["metadata"])

    # --- Type Validation Tests ---

    def test_relocate_invalid_bucket_type_int(self):
        """Test relocate with integer bucket type."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.relocate(123, request_body)
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_relocate_invalid_bucket_type_none(self):
        """Test relocate with None bucket type."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.relocate(None, request_body)
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_relocate_invalid_bucket_type_list(self):
        """Test relocate with list bucket type."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.relocate(["bucket"], request_body)
        self.assertIn("Argument 'bucket' must be a string", str(context.exception))

    def test_relocate_invalid_request_body_type_int(self):
        """Test relocate with integer request_body type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", 123)
        self.assertIn("Argument 'request_body' must be a dictionary", str(context.exception))

    def test_relocate_invalid_request_body_type_none(self):
        """Test relocate with None request_body type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", None)
        self.assertIn("Argument 'request_body' must be a dictionary", str(context.exception))

    def test_relocate_invalid_request_body_type_list(self):
        """Test relocate with list request_body type."""
        with self.assertRaises(TypeError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", ["location"])
        self.assertIn("Argument 'request_body' must be a dictionary", str(context.exception))

    # --- Bucket Name Validation Tests ---

    def test_relocate_empty_bucket_name(self):
        """Test relocate with empty bucket name."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("", request_body)
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_relocate_whitespace_only_bucket_name(self):
        """Test relocate with whitespace-only bucket name."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("   ", request_body)
        self.assertIn("cannot be empty or contain only whitespace", str(context.exception))

    def test_relocate_bucket_name_too_short(self):
        """Test relocate with bucket name too short."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("ab", request_body)
        self.assertIn("must be between 3 and 63 characters long", str(context.exception))

    def test_relocate_bucket_name_too_long(self):
        """Test relocate with bucket name too long."""
        long_name = "a" * 64
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate(long_name, request_body)
        self.assertIn("must be between 3 and 63 characters long", str(context.exception))

    def test_relocate_bucket_name_starts_with_dot(self):
        """Test relocate with bucket name starting with dot."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate(".test-bucket", request_body)
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_relocate_bucket_name_ends_with_dot(self):
        """Test relocate with bucket name ending with dot."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket.", request_body)
        self.assertIn("cannot start or end with dots", str(context.exception))

    def test_relocate_bucket_name_consecutive_dots(self):
        """Test relocate with bucket name containing consecutive dots."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test..bucket", request_body)
        self.assertIn("consecutive dots", str(context.exception))

    # --- Business Logic Error Tests ---

    def test_relocate_bucket_not_found(self):
        """Test relocate with non-existent bucket."""
        request_body = {"destinationLocation": "us-west1"}
        with self.assertRaises(Exception) as context:  # BucketNotFoundError
            google_cloud_storage.Buckets.relocate("non-existent-bucket", request_body)
        self.assertIn("not found", str(context.exception))

    def test_relocate_missing_destination_location(self):
        """Test relocate with missing destinationLocation."""
        request_body = {}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("Missing required field: destinationLocation", str(context.exception))

    def test_relocate_invalid_destination_location_empty_string(self):
        """Test relocate with empty destinationLocation."""
        request_body = {"destinationLocation": ""}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("Invalid destinationLocation", str(context.exception))

    def test_relocate_invalid_destination_location_whitespace(self):
        """Test relocate with whitespace-only destinationLocation."""
        request_body = {"destinationLocation": "   "}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("Invalid destinationLocation", str(context.exception))

    def test_relocate_invalid_destination_location_type(self):
        """Test relocate with non-string destinationLocation."""
        request_body = {"destinationLocation": 123}
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("Invalid destinationLocation", str(context.exception))

    # --- Custom Placement Config Validation Tests ---

    def test_relocate_invalid_custom_placement_config_type(self):
        """Test relocate with non-dict custom placement config."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": "not-a-dict"
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("destinationCustomPlacementConfig must be a dictionary", str(context.exception))

    def test_relocate_invalid_data_locations_type(self):
        """Test relocate with non-list dataLocations."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": "not-a-list"
            }
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("dataLocations must be a list", str(context.exception))

    def test_relocate_invalid_data_locations_count_too_few(self):
        """Test relocate with too few dataLocations."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": ["us-west1-a"]
            }
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("dataLocations must contain exactly 2 locations", str(context.exception))

    def test_relocate_invalid_data_locations_count_too_many(self):
        """Test relocate with too many dataLocations."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": ["us-west1-a", "us-west1-b", "us-west1-c"]
            }
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("dataLocations must contain exactly 2 locations", str(context.exception))

    def test_relocate_invalid_data_locations_non_string(self):
        """Test relocate with non-string dataLocations."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": [123, "us-west1-b"]
            }
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("All dataLocations must be non-empty strings", str(context.exception))

    def test_relocate_invalid_data_locations_empty_string(self):
        """Test relocate with empty string in dataLocations."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": ["", "us-west1-b"]
            }
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("All dataLocations must be non-empty strings", str(context.exception))

    def test_relocate_invalid_data_locations_whitespace(self):
        """Test relocate with whitespace-only string in dataLocations."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": ["   ", "us-west1-b"]
            }
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("All dataLocations must be non-empty strings", str(context.exception))

    # --- ValidateOnly Field Validation Tests ---

    def test_relocate_invalid_validate_only_type_string(self):
        """Test relocate with string validateOnly."""
        request_body = {
            "destinationLocation": "us-west1",
            "validateOnly": "true"
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("validateOnly must be a boolean", str(context.exception))

    def test_relocate_invalid_validate_only_type_int(self):
        """Test relocate with integer validateOnly."""
        request_body = {
            "destinationLocation": "us-west1",
            "validateOnly": 1
        }
        with self.assertRaises(ValueError) as context:
            google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertIn("validateOnly must be a boolean", str(context.exception))

    # --- Edge Cases ---

    def test_relocate_bucket_name_minimum_valid_length(self):
        """Test relocate with minimum valid bucket name length (3 characters)."""
        # Create a bucket with 3 characters
        google_cloud_storage.Buckets.DB["buckets"]["abc"] = {
            "name": "abc",
            "metageneration": "1"
        }
        
        request_body = {"destinationLocation": "us-west1"}
        result = google_cloud_storage.Buckets.relocate("abc", request_body)
        
        self.assertFalse(result["done"])
        self.assertEqual(result["metadata"]["bucket"], "abc")

    def test_relocate_bucket_name_maximum_valid_length(self):
        """Test relocate with maximum valid bucket name length (63 characters)."""
        # Create a bucket with 63 characters
        bucket_name = "a" * 63
        google_cloud_storage.Buckets.DB["buckets"][bucket_name] = {
            "name": bucket_name,
            "metageneration": "1"
        }
        
        request_body = {"destinationLocation": "us-west1"}
        result = google_cloud_storage.Buckets.relocate(bucket_name, request_body)
        
        self.assertFalse(result["done"])
        self.assertEqual(result["metadata"]["bucket"], bucket_name)

    def test_relocate_custom_placement_without_data_locations(self):
        """Test relocate with custom placement config but no dataLocations."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {}
        }
        result = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        
        self.assertFalse(result["done"])
        self.assertIn("customPlacementConfig", result["metadata"])

    # --- Operation Response Verification Tests ---

    def test_relocate_operation_name_format(self):
        """Test that operation name follows correct format."""
        request_body = {"destinationLocation": "us-west1"}
        result = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        
        # Regular operation should have timestamp and random component
        self.assertIn("operations/relocate-bucket-test-bucket-1-", result["name"])
        
        # Validation operation should have "validation" suffix
        request_body["validateOnly"] = True
        result_validation = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        self.assertEqual(result_validation["name"], "operations/relocate-bucket-test-bucket-1-validation")

    def test_relocate_self_link_format(self):
        """Test that selfLink follows correct format."""
        request_body = {"destinationLocation": "us-west1"}
        result = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        
        self.assertIn("https://storage.googleapis.com/storage/v1/operations/", result["selfLink"])
        self.assertIn("relocate-bucket-test-bucket-1", result["selfLink"])

    def test_relocate_metadata_structure(self):
        """Test that metadata has correct structure."""
        request_body = {
            "destinationLocation": "us-west1",
            "destinationCustomPlacementConfig": {
                "dataLocations": ["us-west1-a", "us-west1-b"]
            }
        }
        result = google_cloud_storage.Buckets.relocate("test-bucket-1", request_body)
        
        metadata = result["metadata"]
        self.assertIn("requestedLocation", metadata)
        self.assertIn("validateOnly", metadata)
        self.assertIn("bucket", metadata)
        self.assertIn("operationType", metadata)
        self.assertIn("customPlacementConfig", metadata)
        
        self.assertEqual(metadata["requestedLocation"], "us-west1")
        self.assertFalse(metadata["validateOnly"])
        self.assertEqual(metadata["bucket"], "test-bucket-1")
        self.assertEqual(metadata["operationType"], "RELOCATE_BUCKET")


if __name__ == "__main__":
    unittest.main() 