import unittest
import copy
import json
import os
import tempfile
import sys

from common_utils.base_case import BaseTestCaseWithErrorHandler
from bigquery import describe_table
from ..SimulationEngine.custom_errors import TableNotFoundError, InvalidInputError, ProjectNotFoundError, DatasetNotFoundError
from ..SimulationEngine.db import DB

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class TestDescribeTable(BaseTestCaseWithErrorHandler):  # type: ignore
    """
    Test suite for the 'describe_table' function.
    """

    def setUp(self):
        """Set up test environment for each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.json_db_path = os.path.join(self.test_dir, "BigQueryDefaultDB.json")
        self.original_db_path = os.environ.get("BIGQUERY_DB_PATH")
        os.environ["BIGQUERY_DB_PATH"] = self.json_db_path

        # Load the actual BigQueryDefaultDB.json
        db_path = os.path.join(project_root, 'DBs', 'BigQueryDefaultDB.json')
        with open(db_path, 'r', encoding='utf-8') as f:
            self.test_data = json.load(f)

        self._write_test_json(self.test_data)

        self.project_id = "project-query"
        self.dataset_id = "user-activity-logs"
        self.table_id = "git-events"

    def tearDown(self):
        """Clean up after each test method."""
        if self.original_db_path is not None:
            os.environ["BIGQUERY_DB_PATH"] = self.original_db_path
        else:
            os.environ.pop("BIGQUERY_DB_PATH", None)
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
            os.rmdir(self.test_dir)

    def _write_test_json(self, data: dict):
        """Helper method to write test data to JSON file."""
        with open(self.json_db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        # Update the global DB variable to match the file
        global DB
        DB.clear()
        DB.update(data)

    def test_describe_table_success(self):
        """Test successful table description retrieval."""
        result = describe_table(self.project_id, self.dataset_id, self.table_id)

        # Check BigQuery API Table resource structure
        self.assertEqual(result["kind"], "bigquery#table")
        self.assertIn("etag", result)
        self.assertEqual(result["id"], f"{self.project_id}:{self.dataset_id}.{self.table_id}")
        self.assertIn("selfLink", result)
        
        # Check tableReference
        self.assertEqual(result["tableReference"]["projectId"], self.project_id)
        self.assertEqual(result["tableReference"]["datasetId"], self.dataset_id)
        self.assertEqual(result["tableReference"]["tableId"], self.table_id)
        
        self.assertEqual(result["type"], "TABLE")
        self.assertIsNone(result["expirationTime"])

        # Check schema
        self.assertIn("schema", result)
        self.assertIn("fields", result["schema"])
        schema_fields = result["schema"]["fields"]
        self.assertEqual(len(schema_fields), 8)

        field_names = {field["name"] for field in schema_fields}
        expected_fields = {
            "event_id", "repository_id", "repository_name", "actor_id",
            "actor_login", "event_type", "payload", "created_at"
        }
        self.assertEqual(field_names, expected_fields)

        # Check storage statistics
        self.assertEqual(result["numRows"], 4)
        self.assertIsNotNone(result["numBytes"])
        self.assertEqual(result["numLongTermBytes"], "0")
        self.assertEqual(result["numTotalLogicalBytes"], result["numBytes"])
        self.assertEqual(result["numActiveLogicalBytes"], result["numBytes"])

    def test_describe_empty_table(self):
        """Test describing a table with no rows."""
        test_data = copy.deepcopy(self.test_data)
        empty_table = {
            "table_id": "empty_table",
            "type": "TABLE",
            "creation_time": "2025-05-15T08:30:15Z",
            "last_modified_time": None,
            "expiration_time": None,
            "schema": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ],
            "rows": []
        }
        test_data["projects"][0]["datasets"][0]["tables"].append(empty_table)
        self._write_test_json(test_data)

        result = describe_table(self.project_id, self.dataset_id, "empty_table")

        self.assertEqual(result["tableReference"]["tableId"], "empty_table")
        self.assertEqual(result["numRows"], 0)
        self.assertIsNotNone(result["schema"])
        self.assertEqual(len(result["schema"]["fields"]), 1)

    def test_table_not_found(self):
        """Test error handling for non-existent table."""
        with self.assertRaises(TableNotFoundError) as context:
            describe_table(self.project_id, self.dataset_id, "NonExistentTable")
        self.assertIn("Table 'NonExistentTable' not found", str(context.exception))

    def test_project_not_found(self):
        """Test error handling for non-existent project."""
        with self.assertRaises(ProjectNotFoundError) as context:
            describe_table("invalid_project", self.dataset_id, self.table_id)
        self.assertIn("Project 'invalid_project' not found", str(context.exception))

    def test_dataset_not_found(self):
        """Test error handling for non-existent dataset."""
        with self.assertRaises(DatasetNotFoundError) as context:
            describe_table(self.project_id, "invalid_dataset", self.table_id)
        self.assertIn("Dataset 'invalid_dataset' not found", str(context.exception))

    def test_invalid_input_parameters(self):
        """Test error handling for invalid input parameters."""
        # Test empty project_id
        with self.assertRaises(InvalidInputError) as context:
            describe_table("", self.dataset_id, self.table_id)
        self.assertIn("project_id must be a non-empty string", str(context.exception))

        # Test empty dataset_id
        with self.assertRaises(InvalidInputError) as context:
            describe_table(self.project_id, "", self.table_id)
        self.assertIn("dataset_id must be a non-empty string", str(context.exception))

        # Test empty table_id
        with self.assertRaises(InvalidInputError) as context:
            describe_table(self.project_id, self.dataset_id, "")
        self.assertIn("table_id must be a non-empty string", str(context.exception))

        # Test None values
        with self.assertRaises(InvalidInputError) as context:
            describe_table(None, self.dataset_id, self.table_id)  # type: ignore
        self.assertIn("project_id must be a non-empty string", str(context.exception))

        with self.assertRaises(InvalidInputError) as context:
            describe_table(self.project_id, None, self.table_id)  # type: ignore
        self.assertIn("dataset_id must be a non-empty string", str(context.exception))

        with self.assertRaises(InvalidInputError) as context:
            describe_table(self.project_id, self.dataset_id, None)  # type: ignore
        self.assertIn("table_id must be a non-empty string", str(context.exception))

    def test_selected_fields_parameter(self):
        """Test the selected_fields parameter functionality."""
        result = describe_table(
            self.project_id, 
            self.dataset_id, 
            self.table_id, 
            selected_fields="kind,id,tableReference,type"
        )

        # Should only contain the selected fields
        self.assertEqual(set(result.keys()), {"kind", "id", "tableReference", "type"})
        self.assertEqual(result["kind"], "bigquery#table")
        self.assertEqual(result["id"], f"{self.project_id}:{self.dataset_id}.{self.table_id}")
        self.assertEqual(result["type"], "TABLE")

    def test_selected_fields_empty_string(self):
        """Test selected_fields parameter with empty string."""
        result = describe_table(
            self.project_id, 
            self.dataset_id, 
            self.table_id, 
            selected_fields=""
        )

        # Should return empty response when empty string is provided (no valid fields)
        self.assertEqual(result, {})

    def test_selected_fields_nonexistent_fields(self):
        """Test selected_fields parameter with non-existent fields."""
        result = describe_table(
            self.project_id, 
            self.dataset_id, 
            self.table_id, 
            selected_fields="nonexistent_field1,nonexistent_field2"
        )

        # Should return empty response when no valid fields are selected
        self.assertEqual(result, {})

    def test_view_parameter_basic(self):
        """Test the view parameter with BASIC view."""
        result = describe_table(
            self.project_id, 
            self.dataset_id, 
            self.table_id, 
            view="BASIC"
        )

        # BASIC view should not include storage statistics
        self.assertIn("kind", result)
        self.assertIn("tableReference", result)
        self.assertIn("schema", result)
        self.assertNotIn("numBytes", result)
        self.assertNotIn("numRows", result)
        self.assertNotIn("numLongTermBytes", result)

    def test_view_parameter_storage_stats(self):
        """Test the view parameter with STORAGE_STATS view (default)."""
        result = describe_table(
            self.project_id, 
            self.dataset_id, 
            self.table_id, 
            view="STORAGE_STATS"
        )

        # STORAGE_STATS view should include storage statistics
        self.assertIn("kind", result)
        self.assertIn("tableReference", result)
        self.assertIn("schema", result)
        self.assertIn("numBytes", result)
        self.assertIn("numRows", result)
        self.assertIn("numLongTermBytes", result)

    def test_view_parameter_full(self):
        """Test the view parameter with FULL view."""
        result = describe_table(
            self.project_id, 
            self.dataset_id, 
            self.table_id, 
            view="FULL"
        )

        # FULL view should include all information
        self.assertIn("kind", result)
        self.assertIn("tableReference", result)
        self.assertIn("schema", result)
        self.assertIn("numBytes", result)
        self.assertIn("numRows", result)
        self.assertIn("numLongTermBytes", result)

    def test_view_parameter_invalid(self):
        """Test the view parameter with invalid value."""
        result = describe_table(
            self.project_id, 
            self.dataset_id, 
            self.table_id, 
            view="INVALID_VIEW"
        )

        # Should default to STORAGE_STATS view for invalid values
        self.assertIn("kind", result)
        self.assertIn("tableReference", result)
        self.assertIn("schema", result)
        self.assertIn("numBytes", result)
        self.assertIn("numRows", result)
        self.assertIn("numLongTermBytes", result)

    def test_optional_fields_in_table_data(self):
        """Test that optional fields are included in the response when present."""
        test_data = copy.deepcopy(self.test_data)
        table_with_options = {
            "table_id": "table_with_options",
            "type": "TABLE",
            "creation_time": "2023-01-01T00:00:00Z",
            "last_modified_time": "2023-01-02T00:00:00Z",
            "expiration_time": "2024-01-01T00:00:00Z",
            "friendly_name": "My Friendly Table",
            "description": "A test table with optional fields",
            "labels": {"environment": "test", "team": "data"},
            "view": {"useLegacySql": False},
            "timePartitioning": {"type": "DAY"},
            "rangePartitioning": {"field": "id"},
            "clustering": {"fields": ["field1", "field2"]},
            "requirePartitionFilter": True,
            "location": "EU",
            "maxStaleness": "3600",
            "tableConstraints": {"primaryKey": {"columns": ["id"]}},
            "resourceTags": {"tag1": "value1"},
            "schema": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ],
            "rows": []
        }
        test_data["projects"][0]["datasets"][0]["tables"].append(table_with_options)
        self._write_test_json(test_data)

        result = describe_table(self.project_id, self.dataset_id, "table_with_options")

        # Check optional fields are included
        self.assertEqual(result["friendlyName"], "My Friendly Table")
        self.assertEqual(result["description"], "A test table with optional fields")
        self.assertEqual(result["labels"], {"environment": "test", "team": "data"})
        self.assertEqual(result["view"], {"useLegacySql": False})
        self.assertEqual(result["timePartitioning"], {"type": "DAY"})
        self.assertEqual(result["rangePartitioning"], {"field": "id"})
        self.assertEqual(result["clustering"], {"fields": ["field1", "field2"]})
        self.assertTrue(result["requirePartitionFilter"])
        self.assertEqual(result["location"], "EU")
        self.assertEqual(result["maxStaleness"], "3600")
        self.assertEqual(result["tableConstraints"], {"primaryKey": {"columns": ["id"]}})
        self.assertEqual(result["resourceTags"], {"tag1": "value1"})

    def test_timestamp_conversion(self):
        """Test that timestamps are properly converted to milliseconds."""
        test_data = copy.deepcopy(self.test_data)
        table_with_timestamps = {
            "table_id": "table_with_timestamps",
            "type": "TABLE",
            "creation_time": "2023-01-01T12:00:00Z",
            "last_modified_time": "2023-01-02T12:00:00Z",
            "expiration_time": "2024-01-01T12:00:00Z",
            "schema": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ],
            "rows": []
        }
        test_data["projects"][0]["datasets"][0]["tables"].append(table_with_timestamps)
        self._write_test_json(test_data)

        result = describe_table(self.project_id, self.dataset_id, "table_with_timestamps")

        # Check that timestamps are converted to milliseconds
        self.assertEqual(result["creationTime"], "1672574400000")  # 2023-01-01T12:00:00Z
        self.assertEqual(result["lastModifiedTime"], "1672660800000")  # 2023-01-02T12:00:00Z
        self.assertEqual(result["expirationTime"], "1704110400000")  # 2024-01-01T12:00:00Z

    def test_timestamp_conversion_ms_format(self):
        """Test timestamp conversion with _ms format."""
        test_data = copy.deepcopy(self.test_data)
        table_with_ms_timestamps = {
            "table_id": "table_with_ms_timestamps",
            "type": "TABLE",
            "creation_time_ms": "2023-01-01T12:00:00Z",
            "last_modified_time_ms": "2023-01-02T12:00:00Z",
            "expiration_time_ms": "2024-01-01T12:00:00Z",
            "schema": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ],
            "rows": []
        }
        test_data["projects"][0]["datasets"][0]["tables"].append(table_with_ms_timestamps)
        self._write_test_json(test_data)

        result = describe_table(self.project_id, self.dataset_id, "table_with_ms_timestamps")

        # Check that timestamps are converted to milliseconds
        self.assertEqual(result["creationTime"], "1672574400000")  # 2023-01-01T12:00:00Z
        self.assertEqual(result["lastModifiedTime"], "1672660800000")  # 2023-01-02T12:00:00Z
        self.assertEqual(result["expirationTime"], "1704110400000")  # 2024-01-01T12:00:00Z

    def test_timestamp_conversion_invalid_format(self):
        """Test timestamp conversion with invalid format."""
        test_data = copy.deepcopy(self.test_data)
        table_with_invalid_timestamps = {
            "table_id": "table_with_invalid_timestamps",
            "type": "TABLE",
            "creation_time": "invalid-timestamp",
            "last_modified_time": "another-invalid-timestamp",
            "expiration_time": "yet-another-invalid-timestamp",
            "schema": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ],
            "rows": []
        }
        test_data["projects"][0]["datasets"][0]["tables"].append(table_with_invalid_timestamps)
        self._write_test_json(test_data)

        result = describe_table(self.project_id, self.dataset_id, "table_with_invalid_timestamps")

        # Should keep original invalid timestamps
        self.assertEqual(result["creationTime"], "invalid-timestamp")
        self.assertEqual(result["lastModifiedTime"], "another-invalid-timestamp")
        self.assertEqual(result["expirationTime"], "yet-another-invalid-timestamp")

    def test_size_calculation_exception_handling(self):
        """Test size calculation when JSON serialization fails."""
        test_data = copy.deepcopy(self.test_data)
        table_with_complex_data = {
            "table_id": "table_with_complex_data",
            "type": "TABLE",
            "schema": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ],
            "rows": [{"id": "normal_row"}, {"id": {"complex": "data"}}]  # Complex data that might cause issues
        }
        test_data["projects"][0]["datasets"][0]["tables"].append(table_with_complex_data)
        self._write_test_json(test_data)

        result = describe_table(self.project_id, self.dataset_id, "table_with_complex_data")

        # Should handle the data and calculate size correctly
        self.assertEqual(result["numRows"], 2)
        self.assertIsNotNone(result["numBytes"])
        self.assertNotEqual(result["numBytes"], "0")

    def test_size_calculation_exception_silent_pass(self):
        """Test that exceptions during size calculation are silently caught and default values are used."""
        test_data = copy.deepcopy(self.test_data)
        
        # Create a table with rows that will cause an exception during JSON serialization
        # We'll mock the json.dumps to raise an exception
        import json
        original_dumps = json.dumps
        
        def mock_json_dumps_raises_exception(*args, **kwargs):
            raise Exception("JSON serialization failed")
        
        # Create table with problematic rows
        table_with_problematic_rows = {
            "table_id": "table_with_problematic_rows",
            "type": "TABLE",
            "schema": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ],
            "rows": [{"id": 1}, {"id": 2}]  # Normal rows that would work normally
        }
        test_data["projects"][0]["datasets"][0]["tables"].append(table_with_problematic_rows)
        self._write_test_json(test_data)

        # Temporarily replace json.dumps to simulate the exception
        json.dumps = mock_json_dumps_raises_exception
        
        try:
            result = describe_table(self.project_id, self.dataset_id, "table_with_problematic_rows")
            
            # Should use default values when exception occurs
            self.assertEqual(result["numRows"], 0)
            self.assertEqual(result["numBytes"], "0")
            
        finally:
            # Restore the original json.dumps
            json.dumps = original_dumps

    def test_table_without_rows_key(self):
        """Test table that doesn't have a 'rows' key."""
        test_data = copy.deepcopy(self.test_data)
        table_without_rows = {
            "table_id": "table_without_rows",
            "type": "TABLE",
            "schema": [
                {"name": "id", "type": "INTEGER", "mode": "REQUIRED"}
            ]
            # No 'rows' key
        }
        test_data["projects"][0]["datasets"][0]["tables"].append(table_without_rows)
        self._write_test_json(test_data)

        result = describe_table(self.project_id, self.dataset_id, "table_without_rows")

        # Should use default values when no rows key is present
        self.assertEqual(result["numRows"], 0)
        self.assertEqual(result["numBytes"], "0")

    def test_etag_generation(self):
        """Test that ETag is generated correctly."""
        result1 = describe_table(self.project_id, self.dataset_id, self.table_id)
        result2 = describe_table(self.project_id, self.dataset_id, self.table_id)

        # ETags should be the same for the same table
        self.assertEqual(result1["etag"], result2["etag"])
        self.assertIsInstance(result1["etag"], str)
        self.assertEqual(len(result1["etag"]), 32)  # MD5 hash length

    def test_self_link_generation(self):
        """Test that selfLink is generated correctly."""
        result = describe_table(self.project_id, self.dataset_id, self.table_id)

        expected_self_link = f"https://bigquery.googleapis.com/bigquery/v2/projects/{self.project_id}/datasets/{self.dataset_id}/tables/{self.table_id}"
        self.assertEqual(result["selfLink"], expected_self_link)

    def test_response_structure_completeness(self):
        """Test that all expected fields are present in the response."""
        result = describe_table(self.project_id, self.dataset_id, self.table_id)

        # Check all required fields are present
        required_fields = [
            "kind", "etag", "id", "selfLink", "tableReference", "type",
            "numBytes", "numLongTermBytes", "numRows", "creationTime", 
            "lastModifiedTime", "numTotalLogicalBytes", "numActiveLogicalBytes",
            "numLongTermLogicalBytes", "numTotalPhysicalBytes", "numActivePhysicalBytes",
            "numLongTermPhysicalBytes", "numPartitions", "schema"
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Required field '{field}' is missing")

        # Check tableReference structure
        self.assertIn("projectId", result["tableReference"])
        self.assertIn("datasetId", result["tableReference"])
        self.assertIn("tableId", result["tableReference"])

if __name__ == '__main__':
    unittest.main()
