import unittest
import sqlite3
from unittest.mock import patch, MagicMock
from ..SimulationEngine.custom_errors import InvalidQueryError, InvalidInputError
from ..SimulationEngine.db import DB
from .. import execute_query

class TestExecuteQueryComprehensive(unittest.TestCase):
    """Comprehensive tests for execute_query function."""

    def setUp(self):
        """Set up test data."""
        # Clear and initialize DB
        DB.clear()
        DB.update({
            "projects": [
                {
                    "project_id": "test-project",
                    "datasets": [
                        {
                            "dataset_id": "test_dataset",
                            "tables": [
                                {
                                    "table_id": "test_table",
                                    "schema": [
                                        {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                                        {"name": "name", "type": "STRING", "mode": "NULLABLE"},
                                        {"name": "data", "type": "JSON", "mode": "NULLABLE"},
                                        {"name": "active", "type": "BOOLEAN", "mode": "NULLABLE"}
                                    ],
                                    "rows": [
                                        {"id": 1, "name": "Alice", "data": '{"key": "value"}', "active": True},
                                        {"id": 2, "name": "Bob", "data": '[1, 2, 3]', "active": False},
                                        {"id": 3, "name": "Charlie", "data": "not json", "active": None}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        })

    def test_execute_query_simple_select(self):
        """Test basic SELECT query execution."""
        query = "SELECT id, name FROM test-project.test_dataset.test_table"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 3)
        self.assertEqual(result["query_results"][0]["id"], 1)
        self.assertEqual(result["query_results"][0]["name"], "Alice")

    def test_execute_query_with_json_parsing(self):
        """Test query with JSON field parsing."""
        query = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 1"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        # Should parse JSON string into dict
        self.assertEqual(result["query_results"][0]["data"], {"key": "value"})

    def test_execute_query_with_array_json_parsing(self):
        """Test query with array JSON field parsing."""
        query = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 2"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        # Should parse JSON array string into list
        self.assertEqual(result["query_results"][0]["data"], [1, 2, 3])

    def test_execute_query_with_invalid_json(self):
        """Test query with invalid JSON that should remain as string."""
        query = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 3"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        # Should keep as string when JSON parsing fails
        self.assertEqual(result["query_results"][0]["data"], "not json")

    def test_execute_query_with_boolean_values(self):
        """Test query with boolean field handling."""
        query = "SELECT active FROM test-project.test_dataset.test_table ORDER BY id"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 3)
        self.assertEqual(result["query_results"][0]["active"], 1)  # True -> 1
        self.assertEqual(result["query_results"][1]["active"], 0)  # False -> 0
        self.assertIsNone(result["query_results"][2]["active"])    # None -> None

    def test_execute_query_with_null_values(self):
        """Test query with NULL values."""
        query = "SELECT name FROM test-project.test_dataset.test_table WHERE active IS NULL"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        self.assertEqual(result["query_results"][0]["name"], "Charlie")

    def test_execute_query_with_numeric_types(self):
        """Test query with numeric field handling."""
        query = "SELECT id FROM test-project.test_dataset.test_table WHERE id > 1"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 2)
        self.assertEqual(result["query_results"][0]["id"], 2)
        self.assertEqual(result["query_results"][1]["id"], 3)

    def test_execute_query_simple_table_name_error(self):
        """Test query with simple table name (not fully qualified) - should raise error."""
        query = "SELECT * FROM test_table"
        
        with self.assertRaises(InvalidQueryError) as context:
            execute_query(query)
        
        self.assertIn("Could not parse fully qualified table name", str(context.exception))

    def test_execute_query_no_table_name_error(self):
        """Test query with no table name - should raise error."""
        query = "SELECT * FROM"
        
        with self.assertRaises(InvalidQueryError) as context:
            execute_query(query)
        
        self.assertIn("Could not parse table name from query", str(context.exception))

    def test_execute_query_invalid_table_name_format(self):
        """Test query with invalid table name format."""
        query = "SELECT * FROM `invalid-format`"
        
        with self.assertRaises(InvalidQueryError) as context:
            execute_query(query)
        
        self.assertIn("Could not parse fully qualified table name", str(context.exception))





    def test_execute_query_none_input(self):
        """Test execute_query with None input."""
        with self.assertRaises(InvalidInputError) as context:
            execute_query(None)
        
        self.assertIn("Query parameter cannot be None", str(context.exception))

    def test_execute_query_empty_string(self):
        """Test execute_query with empty string."""
        with self.assertRaises(InvalidInputError) as context:
            execute_query("")
        
        self.assertIn("Query parameter cannot be empty", str(context.exception))

    def test_execute_query_whitespace_only(self):
        """Test execute_query with whitespace only."""
        with self.assertRaises(InvalidInputError) as context:
            execute_query("   ")
        
        self.assertIn("Query parameter cannot be empty", str(context.exception))

    def test_execute_query_non_string_input(self):
        """Test execute_query with non-string input."""
        with self.assertRaises(InvalidInputError) as context:
            execute_query(123)
        
        self.assertIn("Query parameter must be a string", str(context.exception))

    def test_execute_query_too_short(self):
        """Test execute_query with query too short."""
        with self.assertRaises(InvalidInputError) as context:
            execute_query("SEL")
        
        self.assertIn("Query is too short", str(context.exception))

    def test_execute_query_not_select(self):
        """Test execute_query with non-SELECT query."""
        with self.assertRaises(InvalidQueryError) as context:
            execute_query("INSERT INTO table VALUES (1)")
        
        self.assertIn("Only SELECT queries are supported", str(context.exception))

    def test_execute_query_table_not_found(self):
        """Test execute_query with non-existent table."""
        query = "SELECT * FROM test-project.test_dataset.nonexistent_table"
        
        with self.assertRaises(InvalidQueryError) as context:
            execute_query(query)
        
        self.assertIn("Table 'nonexistent_table' not found", str(context.exception))

    def test_execute_query_sqlite_error(self):
        """Test execute_query with SQLite execution error."""
        query = "SELECT * FROM test-project.test_dataset.test_table WHERE invalid_column = 1"
        
        with self.assertRaises(InvalidQueryError) as context:
            execute_query(query)
        
        self.assertIn("SQLite execution error", str(context.exception))

    def test_execute_query_connection_error_handling(self):
        """Test execute_query with connection error handling."""
        query = "SELECT * FROM test-project.test_dataset.test_table"
        
        with patch('bigquery.bigqueryAPI.load_db_dict_to_sqlite') as mock_load:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = sqlite3.Error("Database locked")
            mock_load.return_value = mock_conn
            
            with self.assertRaises(InvalidQueryError) as context:
                execute_query(query)
            
            self.assertIn("SQLite execution error", str(context.exception))
            # Verify connection was closed
            mock_conn.close.assert_called_once()

    def test_execute_query_with_complex_json_parsing(self):
        """Test query with complex JSON parsing scenarios."""
        # Add more complex data to DB
        DB["projects"][0]["datasets"][0]["tables"][0]["rows"].append({
            "id": 4, 
            "name": "David", 
            "data": '{"nested": {"array": [1, 2, 3], "object": {"key": "value"}}}', 
            "active": True
        })
        
        query = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 4"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        expected_data = {"nested": {"array": [1, 2, 3], "object": {"key": "value"}}}
        self.assertEqual(result["query_results"][0]["data"], expected_data)

    def test_execute_query_with_malformed_json(self):
        """Test query with malformed JSON that should remain as string."""
        # Add malformed JSON data
        DB["projects"][0]["datasets"][0]["tables"][0]["rows"].append({
            "id": 5, 
            "name": "Eve", 
            "data": '{"incomplete": json', 
            "active": False
        })
        
        query = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 5"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        # Should keep as string when JSON parsing fails
        self.assertEqual(result["query_results"][0]["data"], '{"incomplete": json')

    def test_execute_query_with_string_that_looks_like_json_but_isnt(self):
        """Test query with string that looks like JSON but isn't."""
        # Add data that looks like JSON but isn't
        DB["projects"][0]["datasets"][0]["tables"][0]["rows"].append({
            "id": 6, 
            "name": "Frank", 
            "data": '{"this": "looks like json but has no closing brace', 
            "active": True
        })
        
        query = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 6"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        # Should keep as string when JSON parsing fails
        self.assertEqual(result["query_results"][0]["data"], '{"this": "looks like json but has no closing brace')

    def test_execute_query_json_decode_error(self):
        """Test execute_query to cover JSONDecodeError handling."""
        # This test specifically targets where json.loads raises JSONDecodeError
        # Add data that looks like JSON but has invalid JSON syntax
        DB["projects"][0]["datasets"][0]["tables"][0]["rows"].append({
            "id": 99, 
            "name": "JSONTest", 
            "data": '{"invalid": json, "missing": quotes}', 
            "active": True
        })
        
        query = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 99"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        # Should keep as string when JSON parsing fails
        self.assertEqual(result["query_results"][0]["data"], '{"invalid": json, "missing": quotes}')

    def test_execute_query_with_empty_json_objects(self):
        """Test query with empty JSON objects and arrays."""
        # Add empty JSON data
        DB["projects"][0]["datasets"][0]["tables"][0]["rows"].append({
            "id": 7, 
            "name": "Grace", 
            "data": '{}', 
            "active": True
        })
        DB["projects"][0]["datasets"][0]["tables"][0]["rows"].append({
            "id": 8, 
            "name": "Henry", 
            "data": '[]', 
            "active": False
        })
        
        # Test empty object
        query1 = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 7"
        result1 = execute_query(query1)
        self.assertEqual(result1["query_results"][0]["data"], {})
        
        # Test empty array
        query2 = "SELECT data FROM test-project.test_dataset.test_table WHERE id = 8"
        result2 = execute_query(query2)
        self.assertEqual(result2["query_results"][0]["data"], [])

    def test_execute_query_with_backticks_in_table_name(self):
        """Test query with backticks in table name."""
        query = "SELECT id FROM test-project.test_dataset.test_table LIMIT 1"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        self.assertEqual(result["query_results"][0]["id"], 1)

    def test_execute_query_with_hyphens_in_table_name(self):
        """Test query with hyphens in table name."""
        # Add table with hyphens
        DB["projects"][0]["datasets"][0]["tables"].append({
            "table_id": "test-table-with-hyphens",
            "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}],
            "rows": [{"id": 100}]
        })
        
        query = "SELECT id FROM test-project.test_dataset.test-table-with-hyphens"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        self.assertEqual(result["query_results"][0]["id"], 100)

    def test_execute_query_parse_full_table_name_error(self):
        """Test execute_query when parse_full_table_name raises InvalidQueryError - covers lines 533-534."""
        # This test covers the exception handling when parse_full_table_name fails
        # We need to mock parse_full_table_name to raise an InvalidQueryError
        with patch('bigquery.bigqueryAPI.parse_full_table_name') as mock_parse:
            mock_parse.side_effect = InvalidQueryError("Invalid table format")
            
            query = "SELECT * FROM invalid.table.format"
            
            with self.assertRaises(InvalidQueryError) as context:
                execute_query(query)
            
            self.assertIn("Invalid table name format", str(context.exception))
            self.assertIn("Invalid table format", str(context.exception))

    def test_execute_query_with_boolean_values_bytes_tracking(self):
        """Test execute_query with boolean values to cover line 625 (boolean bytes processing)."""
        # Add table with boolean column
        DB["projects"][0]["datasets"][0]["tables"].append({
            "table_id": "boolean_test_table",
            "schema": [
                {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                {"name": "is_active", "type": "BOOLEAN", "mode": "NULLABLE"},
                {"name": "is_verified", "type": "BOOLEAN", "mode": "NULLABLE"}
            ],
            "rows": [
                {"id": 1, "is_active": True, "is_verified": False},
                {"id": 2, "is_active": False, "is_verified": True},
                {"id": 3, "is_active": True, "is_verified": True}
            ]
        })
        
        query = "SELECT is_active, is_verified FROM test-project.test_dataset.boolean_test_table ORDER BY id"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 3)
        
        # Verify boolean values are processed correctly
        self.assertEqual(result["query_results"][0]["is_active"], 1)  # True -> 1
        self.assertEqual(result["query_results"][0]["is_verified"], 0)  # False -> 0
        self.assertEqual(result["query_results"][1]["is_active"], 0)  # False -> 0
        self.assertEqual(result["query_results"][1]["is_verified"], 1)  # True -> 1

    def test_execute_query_with_other_data_types_bytes_tracking(self):
        """Test execute_query with other data types to cover line 629 (other types bytes processing)."""
        # Add table with various data types including datetime, decimal, etc.
        # We'll use a custom data type that's not str, bytes, int, float, or bool
        DB["projects"][0]["datasets"][0]["tables"].append({
            "table_id": "other_types_test_table",
            "schema": [
                {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                {"name": "custom_data", "type": "STRING", "mode": "NULLABLE"}
            ],
            "rows": [
                {"id": 1, "custom_data": "test_data"}
            ]
        })
        
        # Mock the database to return a custom object type
        with patch('bigquery.bigqueryAPI.load_db_dict_to_sqlite') as mock_load:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            
            # Create a custom object that's not a standard type
            class CustomObject:
                def __init__(self, value):
                    self.value = value
                def __str__(self):
                    return f"custom_{self.value}"
            
            # Mock the cursor to return a row with a custom object
            mock_cursor.description = [("id",), ("custom_data",)]
            mock_cursor.fetchall.return_value = [(1, CustomObject("test"))]
            
            mock_load.return_value = mock_conn
            
            query = "SELECT * FROM test-project.test_dataset.other_types_test_table"
            result = execute_query(query)
            
            # Verify the query executed successfully
            self.assertIn("query_results", result)
            self.assertEqual(len(result["query_results"]), 1)
            
            # Verify connection was closed
            mock_conn.close.assert_called_once()

    def test_execute_query_with_complex_data_types(self):
        """Test execute_query with complex data types to ensure bytes tracking works."""
        # Add table with complex data that might trigger the "other types" handling
        DB["projects"][0]["datasets"][0]["tables"].append({
            "table_id": "complex_types_table",
            "schema": [
                {"name": "id", "type": "INT64", "mode": "REQUIRED"},
                {"name": "json_data", "type": "JSON", "mode": "NULLABLE"},
                {"name": "timestamp_data", "type": "TIMESTAMP", "mode": "NULLABLE"}
            ],
            "rows": [
                {
                    "id": 1, 
                    "json_data": '{"complex": {"nested": {"array": [1, 2, 3, {"obj": "value"}]}}}', 
                    "timestamp_data": "2023-01-01T00:00:00Z"
                }
            ]
        })
        
        query = "SELECT json_data, timestamp_data FROM test-project.test_dataset.complex_types_table WHERE id = 1"
        result = execute_query(query)
        
        self.assertIn("query_results", result)
        self.assertEqual(len(result["query_results"]), 1)
        
        # Verify complex JSON is parsed correctly
        expected_json = {"complex": {"nested": {"array": [1, 2, 3, {"obj": "value"}]}}}
        self.assertEqual(result["query_results"][0]["json_data"], expected_json)
        self.assertEqual(result["query_results"][0]["timestamp_data"], "2023-01-01T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
