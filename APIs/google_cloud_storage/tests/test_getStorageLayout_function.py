import unittest
from unittest.mock import patch
import sys
import os

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

sys.path.append("APIs")
import google_cloud_storage
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestGetStorageLayoutFunction(BaseTestCaseWithErrorHandler):
    """Test cases for the getStorageLayout function with comprehensive coverage."""

    def setUp(self):
        """Set up test data before each test."""
        # Reset the DB to a known state
        google_cloud_storage.Buckets.DB["buckets"] = {
            "test-bucket-1": {
                "name": "test-bucket-1",
                "project": "test-project",
                "location": "us-central1",
                "locationType": "region",
                "objects": ["file1.txt", "data/file2.txt", "logs/app.log"],
                "storageLayout": {
                    "customPlacementConfig": {
                        "dataLocations": ["us-central1"]
                    },
                    "hierarchicalNamespace": {
                        "enabled": False
                    }
                }
            },
            "test-bucket-dual": {
                "name": "test-bucket-dual",
                "project": "test-project",
                "location": "us",
                "locationType": "dual-region",
                "objects": ["data/important.txt"],
                "storageLayout": {
                    "customPlacementConfig": {
                        "dataLocations": ["us-central1", "us-east1"]
                    },
                    "hierarchicalNamespace": {
                        "enabled": True
                    }
                }
            },
            "test-bucket-multi": {
                "name": "test-bucket-multi",
                "project": "test-project",
                "location": "eu",
                "locationType": "multi-region",
                "objects": ["file.txt"],
                "storageLayout": {}  # Empty layout to test defaults
            },
            "test-bucket-empty": {
                "name": "test-bucket-empty",
                "project": "test-project",
                "objects": []
                # No location or storageLayout to test complete defaults
            }
        }

    def tearDown(self):
        """Clean up after each test."""
        google_cloud_storage.Buckets.DB["buckets"] = {}

    # --- Success Cases ---

    def test_getStorageLayout_success_basic(self):
        """Test successful retrieval of storage layout without prefix."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1")
        
        self.assertIn("storageLayout", result)
        layout = result["storageLayout"]
        
        # Verify all required fields are present
        required_fields = ["bucket", "customPlacementConfig", "hierarchicalNamespace", "kind", "location", "locationType"]
        for field in required_fields:
            self.assertIn(field, layout)
        
        # Verify content
        self.assertEqual(layout["bucket"], "test-bucket-1")
        self.assertEqual(layout["kind"], "storage#storageLayout")
        self.assertEqual(layout["location"], "us-central1")
        self.assertEqual(layout["locationType"], "region")
        self.assertEqual(layout["customPlacementConfig"]["dataLocations"], ["us-central1"])
        self.assertEqual(layout["hierarchicalNamespace"]["enabled"], False)

    def test_getStorageLayout_success_with_valid_prefix(self):
        """Test successful retrieval with valid prefix."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1", prefix="data")
        
        self.assertIn("storageLayout", result)
        layout = result["storageLayout"]
        self.assertEqual(layout["bucket"], "test-bucket-1")

    def test_getStorageLayout_success_dual_region(self):
        """Test successful retrieval for dual-region bucket."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-dual")
        
        layout = result["storageLayout"]
        self.assertEqual(layout["locationType"], "dual-region")
        self.assertEqual(layout["customPlacementConfig"]["dataLocations"], ["us-central1", "us-east1"])
        self.assertEqual(layout["hierarchicalNamespace"]["enabled"], True)

    def test_getStorageLayout_success_multi_region_with_defaults(self):
        """Test successful retrieval for multi-region bucket with default generation."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-multi")
        
        layout = result["storageLayout"]
        self.assertEqual(layout["locationType"], "multi-region")
        self.assertEqual(layout["location"], "eu")
        # Should generate default EU multi-region locations
        self.assertIn("europe-west1", layout["customPlacementConfig"]["dataLocations"])
        self.assertIn("europe-west4", layout["customPlacementConfig"]["dataLocations"])
        self.assertIn("europe-north1", layout["customPlacementConfig"]["dataLocations"])

    def test_getStorageLayout_success_complete_defaults(self):
        """Test successful retrieval for bucket with complete default generation."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-empty")
        
        layout = result["storageLayout"]
        # Should use defaults
        self.assertEqual(layout["location"], "us-central1")  # Default location
        self.assertEqual(layout["locationType"], "region")   # Default type
        self.assertEqual(layout["customPlacementConfig"]["dataLocations"], ["us-central1"])
        self.assertEqual(layout["hierarchicalNamespace"]["enabled"], False)

    def test_getStorageLayout_success_with_prefix_matching_objects(self):
        """Test successful retrieval with prefix that matches existing objects."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1", prefix="logs")
        
        self.assertIn("storageLayout", result)
        layout = result["storageLayout"]
        self.assertEqual(layout["bucket"], "test-bucket-1")

    def test_getStorageLayout_success_with_prefix_no_objects(self):
        """Test successful retrieval with prefix on bucket with no objects."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-empty", prefix="any-prefix")
        
        self.assertIn("storageLayout", result)

    # --- Type Validation Tests ---

    def test_getStorageLayout_invalid_bucket_type_int(self):
        """Test getStorageLayout with integer bucket type."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=TypeError,
            expected_message="Argument 'bucket' must be a string, got int.",
            bucket=123
        )

    def test_getStorageLayout_invalid_bucket_type_none(self):
        """Test getStorageLayout with None bucket type."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=TypeError,
            expected_message="Argument 'bucket' must be a string, got NoneType.",
            bucket=None
        )

    def test_getStorageLayout_invalid_bucket_type_list(self):
        """Test getStorageLayout with list bucket type."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=TypeError,
            expected_message="Argument 'bucket' must be a string, got list.",
            bucket=["bucket"]
        )

    def test_getStorageLayout_invalid_prefix_type_int(self):
        """Test getStorageLayout with integer prefix type."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=TypeError,
            expected_message="Argument 'prefix' must be a string or None, got int.",
            bucket="test-bucket-1",
            prefix=123
        )

    def test_getStorageLayout_invalid_prefix_type_list(self):
        """Test getStorageLayout with list prefix type."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=TypeError,
            expected_message="Argument 'prefix' must be a string or None, got list.",
            bucket="test-bucket-1",
            prefix=["prefix"]
        )

    # --- Bucket Name Validation Tests ---

    def test_getStorageLayout_empty_bucket_name(self):
        """Test getStorageLayout with empty bucket name."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'bucket' cannot be empty or contain only whitespace.",
            bucket=""
        )

    def test_getStorageLayout_whitespace_only_bucket_name(self):
        """Test getStorageLayout with whitespace-only bucket name."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'bucket' cannot be empty or contain only whitespace.",
            bucket="   "
        )

    def test_getStorageLayout_bucket_name_too_short(self):
        """Test getStorageLayout with bucket name too short."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Bucket name must be between 3 and 63 characters long.",
            bucket="ab"
        )

    def test_getStorageLayout_bucket_name_too_long(self):
        """Test getStorageLayout with bucket name too long."""
        long_name = "a" * 64
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Bucket name must be between 3 and 63 characters long.",
            bucket=long_name
        )

    def test_getStorageLayout_bucket_name_starts_with_dot(self):
        """Test getStorageLayout with bucket name starting with dot."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Bucket name cannot start or end with dots, or contain consecutive dots.",
            bucket=".test-bucket"
        )

    def test_getStorageLayout_bucket_name_ends_with_dot(self):
        """Test getStorageLayout with bucket name ending with dot."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Bucket name cannot start or end with dots, or contain consecutive dots.",
            bucket="test-bucket."
        )

    def test_getStorageLayout_bucket_name_consecutive_dots(self):
        """Test getStorageLayout with bucket name containing consecutive dots."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Bucket name cannot start or end with dots, or contain consecutive dots.",
            bucket="test..bucket"
        )

    # --- Prefix Validation Tests ---

    def test_getStorageLayout_empty_prefix(self):
        """Test getStorageLayout with empty prefix."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'prefix' cannot be empty or contain only whitespace if specified.",
            bucket="test-bucket-1",
            prefix=""
        )

    def test_getStorageLayout_whitespace_prefix(self):
        """Test getStorageLayout with whitespace-only prefix."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'prefix' cannot be empty or contain only whitespace if specified.",
            bucket="test-bucket-1",
            prefix="   "
        )

    def test_getStorageLayout_prefix_with_carriage_return(self):
        """Test getStorageLayout with prefix containing carriage return."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'prefix' contains invalid characters (carriage return, newline, or null).",
            bucket="test-bucket-1",
            prefix="test\rprefix"
        )

    def test_getStorageLayout_prefix_with_newline(self):
        """Test getStorageLayout with prefix containing newline."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'prefix' contains invalid characters (carriage return, newline, or null).",
            bucket="test-bucket-1",
            prefix="test\nprefix"
        )

    def test_getStorageLayout_prefix_with_null_character(self):
        """Test getStorageLayout with prefix containing null character."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'prefix' contains invalid characters (carriage return, newline, or null).",
            bucket="test-bucket-1",
            prefix="test\0prefix"
        )

    # --- Business Logic Error Tests ---

    def test_getStorageLayout_bucket_not_found(self):
        """Test getStorageLayout with non-existent bucket."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=google_cloud_storage.SimulationEngine.custom_errors.BucketNotFoundError,
            expected_message="Bucket 'non-existent-bucket' not found.",
            bucket="non-existent-bucket"
        )

    def test_getStorageLayout_prefix_starts_with_slash(self):
        """Test getStorageLayout with prefix starting with slash (invalid format)."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'prefix' cannot start with '/' (absolute paths not allowed).",
            bucket="test-bucket-1",
            prefix="/invalid"
        )

    def test_getStorageLayout_prefix_ends_with_slash(self):
        """Test getStorageLayout with prefix ending with slash (valid format for folder-like prefixes)."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1", prefix="valid/")
        
        self.assertIn("storageLayout", result)

    def test_getStorageLayout_prefix_too_long(self):
        """Test getStorageLayout with prefix that is too long."""
        long_prefix = "a" * 1025
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Argument 'prefix' cannot exceed 1024 characters.",
            bucket="test-bucket-1",
            prefix=long_prefix
        )

    def test_getStorageLayout_restricted_prefix_admin(self):
        """Test getStorageLayout with restricted admin prefix."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Access denied for prefix 'admin/secret'. Restricted prefixes: ['admin/', 'system/', '.config/']",
            bucket="test-bucket-1",
            prefix="admin/secret"
        )

    def test_getStorageLayout_restricted_prefix_system(self):
        """Test getStorageLayout with restricted system prefix."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Access denied for prefix 'system/config'. Restricted prefixes: ['admin/', 'system/', '.config/']",
            bucket="test-bucket-1",
            prefix="system/config"
        )

    def test_getStorageLayout_restricted_prefix_config(self):
        """Test getStorageLayout with restricted config prefix."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=ValueError,
            expected_message="Access denied for prefix '.config/app'. Restricted prefixes: ['admin/', 'system/', '.config/']",
            bucket="test-bucket-1",
            prefix=".config/app"
        )

    # --- Edge Cases ---

    def test_getStorageLayout_bucket_name_minimum_valid_length(self):
        """Test getStorageLayout with minimum valid bucket name length (3 characters)."""
        # Create a bucket with 3 characters
        google_cloud_storage.Buckets.DB["buckets"]["abc"] = {
            "name": "abc",
            "project": "test-project"
        }
        
        result = google_cloud_storage.Buckets.getStorageLayout("abc")
        
        self.assertIn("storageLayout", result)
        self.assertEqual(result["storageLayout"]["bucket"], "abc")

    def test_getStorageLayout_bucket_name_maximum_valid_length(self):
        """Test getStorageLayout with maximum valid bucket name length (63 characters)."""
        # Create a bucket with 63 characters
        bucket_name = "a" * 63
        google_cloud_storage.Buckets.DB["buckets"][bucket_name] = {
            "name": bucket_name,
            "project": "test-project"
        }
        
        result = google_cloud_storage.Buckets.getStorageLayout(bucket_name)
        
        self.assertIn("storageLayout", result)
        self.assertEqual(result["storageLayout"]["bucket"], bucket_name)

    def test_getStorageLayout_prefix_maximum_valid_length(self):
        """Test getStorageLayout with maximum valid prefix length (1024 characters)."""
        valid_prefix = "a" * 1024
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1", prefix=valid_prefix)
        
        self.assertIn("storageLayout", result)

    def test_getStorageLayout_prefix_none_explicitly(self):
        """Test getStorageLayout with prefix explicitly set to None."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1", prefix=None)
        
        self.assertIn("storageLayout", result)

    def test_getStorageLayout_us_multi_region_defaults(self):
        """Test getStorageLayout defaults for US multi-region bucket."""
        google_cloud_storage.Buckets.DB["buckets"]["us-multi"] = {
            "name": "us-multi",
            "project": "test-project",
            "location": "us",
            "locationType": "multi-region",
            "storageLayout": {}
        }
        
        result = google_cloud_storage.Buckets.getStorageLayout("us-multi")
        
        layout = result["storageLayout"]
        data_locations = layout["customPlacementConfig"]["dataLocations"]
        self.assertIn("us-central1", data_locations)
        self.assertIn("us-east1", data_locations)
        self.assertIn("us-west1", data_locations)

    def test_getStorageLayout_asia_multi_region_defaults(self):
        """Test getStorageLayout defaults for ASIA multi-region bucket."""
        google_cloud_storage.Buckets.DB["buckets"]["asia-multi"] = {
            "name": "asia-multi",
            "project": "test-project",
            "location": "asia",
            "locationType": "multi-region",
            "storageLayout": {}
        }
        
        result = google_cloud_storage.Buckets.getStorageLayout("asia-multi")
        
        layout = result["storageLayout"]
        # Should default to single location for unknown multi-region
        data_locations = layout["customPlacementConfig"]["dataLocations"]
        self.assertEqual(data_locations, ["asia"])

    # --- State Verification Tests ---

    def test_getStorageLayout_preserves_bucket_data(self):
        """Test that getStorageLayout does not modify bucket data in the database."""
        original_bucket = google_cloud_storage.Buckets.DB["buckets"]["test-bucket-1"].copy()
        
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1")
        
        # Verify bucket data is unchanged
        self.assertEqual(
            google_cloud_storage.Buckets.DB["buckets"]["test-bucket-1"],
            original_bucket
        )
        self.assertIn("storageLayout", result)

    def test_getStorageLayout_no_side_effects_on_nonexistent_bucket(self):
        """Test that getStorageLayout doesn't create buckets or modify DB for non-existent buckets."""
        original_buckets = list(google_cloud_storage.Buckets.DB["buckets"].keys())
        
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=google_cloud_storage.SimulationEngine.custom_errors.BucketNotFoundError,
            expected_message="Bucket 'non-existent' not found.",
            bucket="non-existent"
        )
        
        # Verify no new buckets were created
        self.assertEqual(
            list(google_cloud_storage.Buckets.DB["buckets"].keys()),
            original_buckets
        )

    # --- Response Structure Verification Tests ---

    def test_getStorageLayout_response_structure_complete_success(self):
        """Test that successful getStorageLayout response has all required fields."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1")
        
        self.assertIn("storageLayout", result)
        layout = result["storageLayout"]
        
        # Verify all required fields are present
        required_fields = ["bucket", "customPlacementConfig", "hierarchicalNamespace", "kind", "location", "locationType"]
        for field in required_fields:
            self.assertIn(field, layout)
        
        # Verify nested structure
        self.assertIn("dataLocations", layout["customPlacementConfig"])
        self.assertIn("enabled", layout["hierarchicalNamespace"])

    def test_getStorageLayout_response_structure_complete_error(self):
        """Test that getStorageLayout raises exception for non-existent bucket."""
        self.assert_error_behavior(
            func_to_call=google_cloud_storage.Buckets.getStorageLayout,
            expected_exception_type=google_cloud_storage.SimulationEngine.custom_errors.BucketNotFoundError,
            expected_message="Bucket 'non-existent' not found.",
            bucket="non-existent"
        )

    def test_getStorageLayout_kind_field_consistency(self):
        """Test that kind field is always consistent."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1")
        
        layout = result["storageLayout"]
        self.assertEqual(layout["kind"], "storage#storageLayout")

    def test_getStorageLayout_custom_placement_structure(self):
        """Test that customPlacementConfig has proper structure."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1")
        
        custom_placement = result["storageLayout"]["customPlacementConfig"]
        self.assertIn("dataLocations", custom_placement)
        self.assertIsInstance(custom_placement["dataLocations"], list)
        self.assertTrue(len(custom_placement["dataLocations"]) > 0)

    def test_getStorageLayout_hierarchical_namespace_structure(self):
        """Test that hierarchicalNamespace has proper structure."""
        result = google_cloud_storage.Buckets.getStorageLayout("test-bucket-1")
        
        hierarchical_ns = result["storageLayout"]["hierarchicalNamespace"]
        self.assertIn("enabled", hierarchical_ns)
        self.assertIsInstance(hierarchical_ns["enabled"], bool)


if __name__ == "__main__":
    unittest.main() 