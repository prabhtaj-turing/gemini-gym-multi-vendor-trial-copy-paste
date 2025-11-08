import unittest
from datetime import datetime, timezone
import json
import os
import tempfile
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from bigquery import list_tables
from ..SimulationEngine.custom_errors import ProjectNotFoundError, DatasetNotFoundError, InvalidInputError
from ..SimulationEngine.models import TableMetadata


class TestListTables(BaseTestCaseWithErrorHandler):  # type: ignore
    """
    Test suite for the 'list_tables' function.
    """

    def setUp(self):
        """Set up test environment for each test method."""
        # Create a temporary directory for test JSON files
        self.test_dir = tempfile.mkdtemp()
        self.json_db_path = os.path.join(self.test_dir, "BigQueryDefaultDB.json")
        # Store original environment variable if it exists
        self.original_db_path = os.environ.get("BIGQUERY_DB_PATH")
        # Set the environment variable to point to our test JSON file
        os.environ["BIGQUERY_DB_PATH"] = self.json_db_path

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original environment variable
        if self.original_db_path is not None:
            os.environ["BIGQUERY_DB_PATH"] = self.original_db_path
        else:
            os.environ.pop("BIGQUERY_DB_PATH", None)
        # Remove the temporary directory and its contents
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
            os.rmdir(self.test_dir)

    def _datetime_to_ms_timestamp(self, dt: datetime) -> int:
        """Converts a datetime object to a Unix timestamp in milliseconds."""
        return int(dt.timestamp() * 1000)

    def _write_test_json(self, data: dict):
        """Helper method to write test data to JSON file."""
        with open(self.json_db_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Update the global DB variable to match the file
        global DB
        DB.clear()
        DB.update(data)

    def test_list_tables_empty_database(self):
        """Test listing tables when the database is empty."""
        self._write_test_json({"projects": []})
        
        # When database is empty, trying to list tables for any project should raise ProjectNotFoundError
        with self.assertRaises(ProjectNotFoundError) as context:
            list_tables("project-alpha", "dataset_one")
        self.assertIn("Project 'project-alpha' not found", str(context.exception))

    def test_list_tables_single_table_no_expiration(self):
        """Test listing a single table without an expiration time."""
        creation_ts = "2023-01-01T12:00:00Z"

        test_data = {
            "projects": [
                {
                    "project_id": "project-alpha",
                    "datasets": [
                        {
                            "dataset_id": "dataset_one",
                            "tables": [
                                {
                                    "table_id": "table_a",
                                    "type": "TABLE",
                                    "creation_time": creation_ts,
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-alpha", "dataset_one")
        
        self.assertEqual(result["kind"], "bigquery#tableList")
        self.assertEqual(result["totalItems"], 1)
        self.assertIsNone(result["nextPageToken"])
        self.assertIn("etag", result)
        
        tables = result["tables"]
        self.assertEqual(len(tables), 1)
        
        table = tables[0]
        self.assertEqual(table["kind"], "bigquery#table")
        self.assertEqual(table["id"], "project-alpha:dataset_one.table_a")
        self.assertEqual(table["tableReference"]["projectId"], "project-alpha")
        self.assertEqual(table["tableReference"]["datasetId"], "dataset_one")
        self.assertEqual(table["tableReference"]["tableId"], "table_a")
        self.assertEqual(table["type"], "TABLE")
        self.assertEqual(table["creationTime"], "1672574400000")  # Converted from ISO string
        self.assertIsNone(table["expirationTime"])

    def test_list_tables_single_table_with_expiration(self):
        """Test listing a single table with a defined expiration time."""
        creation_ts = "2023-02-01T00:00:00Z"
        expiration_ts = "2024-02-01T00:00:00Z"

        test_data = {
            "projects": [
                {
                    "project_id": "project-beta",
                    "datasets": [
                        {
                            "dataset_id": "dataset_two",
                            "tables": [
                                {
                                    "table_id": "table_b",
                                    "type": "VIEW",
                                    "creation_time": creation_ts,
                                    "expiration_time": expiration_ts,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-beta", "dataset_two")
        
        self.assertEqual(result["kind"], "bigquery#tableList")
        self.assertEqual(result["totalItems"], 1)
        
        tables = result["tables"]
        self.assertEqual(len(tables), 1)
        
        table = tables[0]
        self.assertEqual(table["kind"], "bigquery#table")
        self.assertEqual(table["id"], "project-beta:dataset_two.table_b")
        self.assertEqual(table["tableReference"]["projectId"], "project-beta")
        self.assertEqual(table["tableReference"]["datasetId"], "dataset_two")
        self.assertEqual(table["tableReference"]["tableId"], "table_b")
        self.assertEqual(table["type"], "VIEW")
        self.assertEqual(table["creationTime"], "1675209600000")  # Converted from ISO string
        self.assertEqual(table["expirationTime"], "1706745600000")  # Converted from ISO string

    def test_list_tables_multiple_tables_various_types(self):
        """Test listing multiple tables with different types and properties."""
        ts1_create = "2023-03-01T00:00:00Z"
        ts1_expire = "2025-03-01T00:00:00Z"
        ts2_create = "2023-04-01T00:00:00Z"

        test_data = {
            "projects": [
                {
                    "project_id": "project-gamma",
                    "datasets": [
                        {
                            "dataset_id": "dataset_three",
                            "tables": [
                                {
                                    "table_id": "table_c",
                                    "type": "MATERIALIZED_VIEW",
                                    "creation_time": ts1_create,
                                    "expiration_time": ts1_expire,
                                },
                                {
                                    "table_id": "table_d",
                                    "type": "TABLE",
                                    "creation_time": ts2_create,
                                    "expiration_time": None,
                                },
                            ],
                        }
                    ],
                },
                {
                    "project_id": "project-delta",
                    "datasets": [
                        {
                            "dataset_id": "dataset_four",
                            "tables": [
                                {
                                    "table_id": "table_e",
                                    "type": "VIEW",
                                    "creation_time": ts2_create,
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                },
            ]
        }
        self._write_test_json(test_data)

        # Test listing tables from first dataset
        result1 = list_tables("project-gamma", "dataset_three")
        self.assertEqual(result1["totalItems"], 2)
        self.assertEqual(len(result1["tables"]), 2)
        
        table_ids = [table["tableReference"]["tableId"] for table in result1["tables"]]
        self.assertIn("table_c", table_ids)
        self.assertIn("table_d", table_ids)

        # Test listing tables from second dataset
        result2 = list_tables("project-delta", "dataset_four")
        self.assertEqual(result2["totalItems"], 1)
        self.assertEqual(len(result2["tables"]), 1)
        self.assertEqual(result2["tables"][0]["tableReference"]["tableId"], "table_e")

    def test_list_tables_pagination(self):
        """Test pagination functionality."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-paginate",
                    "datasets": [
                        {
                            "dataset_id": "dataset_paginate",
                            "tables": [
                                {
                                    "table_id": f"table_{i}",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                                for i in range(5)  # Create 5 tables
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        # Test first page with max_results=2
        result1 = list_tables("project-paginate", "dataset_paginate", max_results=2)
        self.assertEqual(result1["totalItems"], 5)
        self.assertEqual(len(result1["tables"]), 2)
        self.assertIsNotNone(result1["nextPageToken"])
        self.assertEqual(result1["nextPageToken"], "2")

        # Test second page using page_token
        result2 = list_tables("project-paginate", "dataset_paginate", max_results=2, page_token="2")
        self.assertEqual(result2["totalItems"], 5)
        self.assertEqual(len(result2["tables"]), 2)
        self.assertIsNotNone(result2["nextPageToken"])
        self.assertEqual(result2["nextPageToken"], "4")

        # Test last page
        result3 = list_tables("project-paginate", "dataset_paginate", max_results=2, page_token="4")
        self.assertEqual(result3["totalItems"], 5)
        self.assertEqual(len(result3["tables"]), 1)
        self.assertIsNone(result3["nextPageToken"])

    def test_project_not_found_error(self):
        """Test that ProjectNotFoundError is raised when a project is not found."""
        test_data = {
            "projects": [
                {
                    "project_id": "existing-project",
                    "datasets": [],
                }
            ]
        }
        self._write_test_json(test_data)

        with self.assertRaises(ProjectNotFoundError) as context:
            list_tables("non-existent-project", "dataset_one")
        self.assertIn("Project 'non-existent-project' not found", str(context.exception))

    def test_dataset_not_found_error(self):
        """Test that DatasetNotFoundError is raised when a dataset is not found."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-alpha",
                    "datasets": [
                        {
                            "dataset_id": "existing-dataset"
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        with self.assertRaises(DatasetNotFoundError) as context:
            list_tables("project-alpha", "non-existent-dataset")
        self.assertIn("Dataset 'non-existent-dataset' not found in project 'project-alpha'", str(context.exception))

    def test_empty_projects_keyerror(self):
        """Test handling of empty projects in database."""
        test_data = {}
        self._write_test_json(test_data)
        with self.assertRaises(ProjectNotFoundError) as context:
            result = list_tables("project-alpha", "dataset_one")
        self.assertIn("Project 'project-alpha' not found", str(context.exception))

    def test_invalid_input_parameters(self):
        """Test that InvalidInputError is raised for invalid input parameters."""
        test_data = {"projects": []}
        self._write_test_json(test_data)

        # Test empty project_id
        with self.assertRaises(InvalidInputError) as context:
            list_tables("", "dataset_one")
        self.assertIn("project_id must be a non-empty string", str(context.exception))

        # Test empty dataset_id
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-alpha", "")
        self.assertIn("dataset_id must be a non-empty string", str(context.exception))

        # Test None project_id
        with self.assertRaises(InvalidInputError) as context:
            list_tables(None, "dataset_one")  # type: ignore
        self.assertIn("project_id must be a non-empty string", str(context.exception))

        # Test None dataset_id
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-alpha", None)  # type: ignore
        self.assertIn("dataset_id must be a non-empty string", str(context.exception))

    def test_optional_fields_in_table_data(self):
        """Test that optional fields are included in the response when present."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-optional",
                    "datasets": [
                        {
                            "dataset_id": "dataset_optional",
                            "tables": [
                                {
                                    "table_id": "table_with_options",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                    "friendly_name": "My Friendly Table",
                                    "labels": {"environment": "test", "team": "data"},
                                    "view": {"useLegacySql": False},
                                    "timePartitioning": {"type": "DAY"},
                                    "rangePartitioning": {"field": "id"},
                                    "clustering": {"fields": ["field1", "field2"]},
                                    "hivePartitioningOptions": {"mode": "AUTO"},
                                    "requirePartitionFilter": True
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-optional", "dataset_optional")
        table = result["tables"][0]
        
        self.assertEqual(table["friendlyName"], "My Friendly Table")
        self.assertEqual(table["labels"], {"environment": "test", "team": "data"})
        self.assertEqual(table["view"], {"useLegacySql": False})
        self.assertEqual(table["timePartitioning"], {"type": "DAY"})
        self.assertEqual(table["rangePartitioning"], {"field": "id"})
        self.assertEqual(table["clustering"], {"fields": ["field1", "field2"]})
        self.assertEqual(table["hivePartitioningOptions"], {"mode": "AUTO"})
        self.assertTrue(table["requirePartitionFilter"])

    def test_timestamp_conversion_edge_cases(self):
        """Test timestamp conversion with various edge cases."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-timestamps",
                    "datasets": [
                        {
                            "dataset_id": "dataset_timestamps",
                            "tables": [
                                {
                                    "table_id": "table_invalid_creation",
                                    "type": "TABLE",
                                    "creation_time": "invalid-timestamp",
                                    "expiration_time": None,
                                },
                                {
                                    "table_id": "table_invalid_expiration",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": "invalid-expiration",
                                },
                                {
                                    "table_id": "table_numeric_creation",
                                    "type": "TABLE",
                                    "creation_time": 1672574400000,  # Numeric timestamp
                                    "expiration_time": None,
                                },
                                {
                                    "table_id": "table_numeric_expiration",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": 1706745600000,  # Numeric timestamp
                                },
                                {
                                    "table_id": "table_null_timestamps",
                                    "type": "TABLE",
                                    "creation_time": None,
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-timestamps", "dataset_timestamps")
        tables = result["tables"]
        
        # Test invalid creation timestamp
        invalid_creation_table = next(t for t in tables if t["tableReference"]["tableId"] == "table_invalid_creation")
        self.assertEqual(invalid_creation_table["creationTime"], "invalid-timestamp")
        
        # Test invalid expiration timestamp
        invalid_expiration_table = next(t for t in tables if t["tableReference"]["tableId"] == "table_invalid_expiration")
        self.assertEqual(invalid_expiration_table["expirationTime"], "invalid-expiration")
        
        # Test numeric creation timestamp
        numeric_creation_table = next(t for t in tables if t["tableReference"]["tableId"] == "table_numeric_creation")
        self.assertEqual(numeric_creation_table["creationTime"], "1672574400000")
        
        # Test numeric expiration timestamp
        numeric_expiration_table = next(t for t in tables if t["tableReference"]["tableId"] == "table_numeric_expiration")
        self.assertEqual(numeric_expiration_table["expirationTime"], "1706745600000")
        
        # Test null timestamps
        null_timestamps_table = next(t for t in tables if t["tableReference"]["tableId"] == "table_null_timestamps")
        self.assertIsNone(null_timestamps_table["creationTime"])
        self.assertIsNone(null_timestamps_table["expirationTime"])

    def test_pagination_edge_cases(self):
        """Test pagination with edge cases."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-pagination-edge",
                    "datasets": [
                        {
                            "dataset_id": "dataset_pagination_edge",
                            "tables": [
                                {
                                    "table_id": f"table_{i}",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                                for i in range(3)  # Create 3 tables
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        # Test invalid page token (non-numeric)
        result1 = list_tables("project-pagination-edge", "dataset_pagination_edge", page_token="invalid")
        self.assertEqual(result1["totalItems"], 3)
        self.assertEqual(len(result1["tables"]), 3)  # Should return all tables when page_token is invalid
        
        # Test max_results=0 (should return all tables)
        result2 = list_tables("project-pagination-edge", "dataset_pagination_edge", max_results=0)
        self.assertEqual(result2["totalItems"], 3)
        self.assertEqual(len(result2["tables"]), 3)
        self.assertIsNone(result2["nextPageToken"])
        
        # Test max_results=None (should return all tables)
        result3 = list_tables("project-pagination-edge", "dataset_pagination_edge", max_results=None)
        self.assertEqual(result3["totalItems"], 3)
        self.assertEqual(len(result3["tables"]), 3)
        self.assertIsNone(result3["nextPageToken"])
        
        # Test max_results larger than total items
        result4 = list_tables("project-pagination-edge", "dataset_pagination_edge", max_results=10)
        self.assertEqual(result4["totalItems"], 3)
        self.assertEqual(len(result4["tables"]), 3)
        self.assertIsNone(result4["nextPageToken"])

    def test_tables_without_table_id(self):
        """Test handling of tables without table_id."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-no-table-id",
                    "datasets": [
                        {
                            "dataset_id": "dataset_no_table_id",
                            "tables": [
                                {
                                    "table_id": "valid_table",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                },
                                {
                                    "table_id": "",  # Empty table_id
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                },
                                {
                                    # Missing table_id entirely
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                },
                                {
                                    "table_id": None,  # None table_id
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-no-table-id", "dataset_no_table_id")
        
        # Should only return the valid table
        self.assertEqual(result["totalItems"], 1)
        self.assertEqual(len(result["tables"]), 1)
        self.assertEqual(result["tables"][0]["tableReference"]["tableId"], "valid_table")

    def test_empty_dataset(self):
        """Test listing tables from an empty dataset."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-empty-dataset",
                    "datasets": [
                        {
                            "dataset_id": "empty_dataset",
                            "tables": [],  # No tables
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-empty-dataset", "empty_dataset")
        
        self.assertEqual(result["kind"], "bigquery#tableList")
        self.assertEqual(result["totalItems"], 0)
        self.assertEqual(len(result["tables"]), 0)
        self.assertIsNone(result["nextPageToken"])
        self.assertIn("etag", result)

    def test_etag_generation_consistency(self):
        """Test that ETag generation is consistent for the same data."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-etag",
                    "datasets": [
                        {
                            "dataset_id": "dataset_etag",
                            "tables": [
                                {
                                    "table_id": "table_etag",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        # Call list_tables multiple times
        result1 = list_tables("project-etag", "dataset_etag")
        result2 = list_tables("project-etag", "dataset_etag")
        result3 = list_tables("project-etag", "dataset_etag")
        
        # ETags should be the same for the same data
        self.assertEqual(result1["etag"], result2["etag"])
        self.assertEqual(result2["etag"], result3["etag"])
        
        # ETag should be a valid MD5 hash (32 characters)
        self.assertEqual(len(result1["etag"]), 32)
        self.assertIsInstance(result1["etag"], str)

    def test_etag_generation_different_pages(self):
        """Test that ETag generation differs for different pages."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-etag-pages",
                    "datasets": [
                        {
                            "dataset_id": "dataset_etag_pages",
                            "tables": [
                                {
                                    "table_id": f"table_{i}",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                                for i in range(4)  # Create 4 tables
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        # Get different pages
        result1 = list_tables("project-etag-pages", "dataset_etag_pages", max_results=2)
        result2 = list_tables("project-etag-pages", "dataset_etag_pages", max_results=2, page_token="2")
        
        # ETags should be different for different pages
        self.assertNotEqual(result1["etag"], result2["etag"])

    def test_keyerror_handling_datasets(self):
        """Test KeyError handling when datasets key is missing."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-no-datasets",
                    # Missing "datasets" key
                }
            ]
        }
        self._write_test_json(test_data)

        with self.assertRaises(DatasetNotFoundError) as context:
            list_tables("project-no-datasets", "dataset_one")
        self.assertIn("Dataset 'dataset_one' not found in project 'project-no-datasets'", str(context.exception))

    def test_keyerror_handling_other_keys(self):
        """Test KeyError handling for other missing keys."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-other-keys",
                    "datasets": [
                        {
                            "dataset_id": "dataset_other_keys",
                            "tables": [
                                {
                                    "table_id": "table_other_keys",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        # This should work normally, but if there's a KeyError for other keys, it should be handled
        result = list_tables("project-other-keys", "dataset_other_keys")
        self.assertEqual(result["totalItems"], 1)

    def test_response_structure_completeness(self):
        """Test that the response structure is complete and correct."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-structure",
                    "datasets": [
                        {
                            "dataset_id": "dataset_structure",
                            "tables": [
                                {
                                    "table_id": "table_structure",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-structure", "dataset_structure")
        
        # Check top-level structure
        self.assertEqual(result["kind"], "bigquery#tableList")
        self.assertIn("etag", result)
        self.assertIn("nextPageToken", result)
        self.assertIn("tables", result)
        self.assertIn("totalItems", result)
        
        # Check table structure
        table = result["tables"][0]
        self.assertEqual(table["kind"], "bigquery#table")
        self.assertIn("id", table)
        self.assertIn("tableReference", table)
        self.assertIn("type", table)
        self.assertIn("creationTime", table)
        self.assertIn("expirationTime", table)
        
        # Check tableReference structure
        table_ref = table["tableReference"]
        self.assertIn("projectId", table_ref)
        self.assertIn("datasetId", table_ref)
        self.assertIn("tableId", table_ref)

    def test_optional_fields_not_present(self):
        """Test that optional fields are not included when not present in table data."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-no-optional",
                    "datasets": [
                        {
                            "dataset_id": "dataset_no_optional",
                            "tables": [
                                {
                                    "table_id": "table_no_optional",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                    # No optional fields
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-no-optional", "dataset_no_optional")
        table = result["tables"][0]
        
        # Check that optional fields are not present
        optional_fields = ["friendlyName", "labels", "view", "timePartitioning", 
                          "rangePartitioning", "clustering", "hivePartitioningOptions", 
                          "requirePartitionFilter"]
        
        for field in optional_fields:
            self.assertNotIn(field, table)

    def test_mixed_optional_fields(self):
        """Test tables with some optional fields present and others missing."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-mixed-optional",
                    "datasets": [
                        {
                            "dataset_id": "dataset_mixed_optional",
                            "tables": [
                                {
                                    "table_id": "table_mixed_optional",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                    "friendly_name": "Only Friendly Name",  # Only this optional field
                                    # Other optional fields missing
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        result = list_tables("project-mixed-optional", "dataset_mixed_optional")
        table = result["tables"][0]
        
        # Check that only the present optional field is included
        self.assertEqual(table["friendlyName"], "Only Friendly Name")
        
        # Check that other optional fields are not present
        other_optional_fields = ["labels", "view", "timePartitioning", 
                                "rangePartitioning", "clustering", 
                                "hivePartitioningOptions", "requirePartitionFilter"]
        
        for field in other_optional_fields:
            self.assertNotIn(field, table)

    def test_max_results_validation(self):
        """Test that InvalidInputError is raised for invalid max_results values."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-alpha",
                    "datasets": [
                        {
                            "dataset_id": "dataset_one",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        # Test negative max_results
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-alpha", "dataset_one", max_results=-1)
        self.assertIn("max_results must be a non-negative integer or None", str(context.exception))

        # Test non-integer max_results (string)
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-alpha", "dataset_one", max_results="invalid")  # type: ignore
        self.assertIn("max_results must be a non-negative integer or None", str(context.exception))

        # Test non-integer max_results (float)
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-alpha", "dataset_one", max_results=5.5)  # type: ignore
        self.assertIn("max_results must be a non-negative integer or None", str(context.exception))

        # Test non-integer max_results (list)
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-alpha", "dataset_one", max_results=[1, 2, 3])  # type: ignore
        self.assertIn("max_results must be a non-negative integer or None", str(context.exception))

        # Test valid max_results values (should not raise exceptions)
        try:
            list_tables("project-alpha", "dataset_one", max_results=0)
        except InvalidInputError:
            self.fail("max_results=0 should be valid")

        try:
            list_tables("project-alpha", "dataset_one", max_results=1)
        except InvalidInputError:
            self.fail("max_results=1 should be valid")

        try:
            list_tables("project-alpha", "dataset_one", max_results=None)
        except InvalidInputError:
            self.fail("max_results=None should be valid")

    def test_page_token_validation(self):
        """Test that InvalidInputError is raised for invalid page_token values."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-beta",
                    "datasets": [
                        {
                            "dataset_id": "dataset_two",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        # Test non-string page_token (integer)
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-beta", "dataset_two", page_token=123)  # type: ignore
        self.assertIn("page_token must be a string or None", str(context.exception))

        # Test non-string page_token (float)
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-beta", "dataset_two", page_token=1.5)  # type: ignore
        self.assertIn("page_token must be a string or None", str(context.exception))

        # Test non-string page_token (list)
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-beta", "dataset_two", page_token=["token"])  # type: ignore
        self.assertIn("page_token must be a string or None", str(context.exception))

        # Test non-string page_token (dict)
        with self.assertRaises(InvalidInputError) as context:
            list_tables("project-beta", "dataset_two", page_token={"token": "value"})  # type: ignore
        self.assertIn("page_token must be a string or None", str(context.exception))

        # Test valid page_token values (should not raise exceptions)
        try:
            list_tables("project-beta", "dataset_two", page_token=None)
        except InvalidInputError:
            self.fail("page_token=None should be valid")

        try:
            list_tables("project-beta", "dataset_two", page_token="")
        except InvalidInputError:
            self.fail("page_token='' should be valid")

        try:
            list_tables("project-beta", "dataset_two", page_token="valid_token")
        except InvalidInputError:
            self.fail("page_token='valid_token' should be valid")

        try:
            list_tables("project-beta", "dataset_two", page_token="123")
        except InvalidInputError:
            self.fail("page_token='123' should be valid")

    def test_negative_page_token_handling(self):
        """Test that negative page tokens are handled gracefully by setting start_index to 0."""
        test_data = {
            "projects": [
                {
                    "project_id": "project-negative-token",
                    "datasets": [
                        {
                            "dataset_id": "dataset_negative_token",
                            "tables": [
                                {
                                    "table_id": f"table_{i}",
                                    "type": "TABLE",
                                    "creation_time": "2023-01-01T00:00:00Z",
                                    "expiration_time": None,
                                }
                                for i in range(5)  # Create 5 tables
                            ],
                        }
                    ],
                }
            ]
        }
        self._write_test_json(test_data)

        # Test with negative page token
        result_negative = list_tables("project-negative-token", "dataset_negative_token", page_token="-1")
        
        # Should return all tables starting from index 0 (first page)
        self.assertEqual(result_negative["totalItems"], 5)
        self.assertEqual(len(result_negative["tables"]), 5)
        self.assertEqual(result_negative["tables"][0]["tableReference"]["tableId"], "table_0")
        self.assertEqual(result_negative["tables"][4]["tableReference"]["tableId"], "table_4")

        # Test with large negative page token
        result_large_negative = list_tables("project-negative-token", "dataset_negative_token", page_token="-100")
        
        # Should also return all tables starting from index 0
        self.assertEqual(result_large_negative["totalItems"], 5)
        self.assertEqual(len(result_large_negative["tables"]), 5)
        self.assertEqual(result_large_negative["tables"][0]["tableReference"]["tableId"], "table_0")

        # Test with zero page token (should behave the same as negative)
        result_zero = list_tables("project-negative-token", "dataset_negative_token", page_token="0")
        
        # Should return all tables starting from index 0
        self.assertEqual(result_zero["totalItems"], 5)
        self.assertEqual(len(result_zero["tables"]), 5)
        self.assertEqual(result_zero["tables"][0]["tableReference"]["tableId"], "table_0")

        # Test with positive page token for comparison
        result_positive = list_tables("project-negative-token", "dataset_negative_token", page_token="2")
        
        # Should return tables starting from index 2
        self.assertEqual(result_positive["totalItems"], 5)
        self.assertEqual(len(result_positive["tables"]), 3)  # tables 2, 3, 4
        self.assertEqual(result_positive["tables"][0]["tableReference"]["tableId"], "table_2")
        self.assertEqual(result_positive["tables"][2]["tableReference"]["tableId"], "table_4")

    def test_keyerror_handling_fallback(self):
        """Test that KeyError exceptions not related to 'projects' raise InvalidInputError."""
        # This test verifies that line 215 is reached when a KeyError occurs
        # that doesn't contain "projects" in the error message
        
        # Create a test that directly tests the fallback case by creating a scenario
        # where a KeyError occurs but doesn't contain "projects" in the message
        from unittest.mock import patch, MagicMock
        
        # Create a custom KeyError that doesn't contain "projects" in its message
        class CustomKeyError(KeyError):
            def __str__(self):
                return "missing_key"  # This doesn't contain "projects"
        
        # Create a mock DB that will raise our custom KeyError
        mock_db = MagicMock()
        mock_db.__getitem__.side_effect = CustomKeyError("missing_key")
        
        with patch('bigquery.bigqueryAPI.DB', mock_db):
            with self.assertRaises(InvalidInputError) as context:
                list_tables("project-keyerror", "dataset_keyerror")
            self.assertIn("Invalid database structure", str(context.exception))
            self.assertIn("missing_key", str(context.exception))


if __name__ == '__main__':
    unittest.main()
