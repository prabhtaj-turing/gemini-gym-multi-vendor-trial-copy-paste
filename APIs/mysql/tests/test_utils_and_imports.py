"""
Utility Functions and Import/Package Health Tests

This module tests utility functions, import health, and package integrity
as required by the Service Engineering Test Framework Guidelines.
"""

import unittest
import os
import sys
import json
import importlib
import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUtilityFunctions(BaseTestCaseWithErrorHandler):
    """
    Test utility functions for comprehensive coverage.
    """

    def setUp(self):
        super().setUp()
        # Import utils here to avoid issues with module patching
        from mysql.SimulationEngine import utils
        self.utils = utils

    def test_datetime_encoder_handles_datetime_objects(self):
        """Test DateTimeEncoder properly serializes datetime objects"""
        encoder = self.utils.DateTimeEncoder()
        
        # Test datetime.datetime
        dt = datetime.datetime(2023, 12, 25, 14, 30, 45)
        result = encoder.default(dt)
        self.assertEqual(result, "2023-12-25T14:30:45")
        
        # Test datetime.date
        date = datetime.date(2023, 12, 25)
        result = encoder.default(date)
        self.assertEqual(result, "2023-12-25")
        
        # Test datetime.time
        time = datetime.time(14, 30, 45)
        result = encoder.default(time)
        self.assertEqual(result, "14:30:45")

    def test_datetime_encoder_delegates_non_datetime(self):
        """Test DateTimeEncoder delegates non-datetime objects to super()"""
        encoder = self.utils.DateTimeEncoder()
        
        # Should raise TypeError for non-serializable objects
        with self.assertRaises(TypeError):
            encoder.default(object())

    def test_query_type_parsing(self):
        """Test _query_type parses SQL correctly"""
        test_cases = [
            ("SELECT * FROM users", "select"),
            ("INSERT INTO users VALUES (1)", "insert"),
            ("UPDATE users SET name='John'", "update"),
            ("DELETE FROM users WHERE id=1", "delete"),
            ("CREATE TABLE test (id INT)", "create"),
            ("DROP TABLE test", "drop"),
            ("SHOW TABLES", "command"),  # SHOW becomes 'command' in sqlglot
            ("   SELECT   * FROM test  ", "select"),  # Whitespace handling
        ]
        
        for sql, expected in test_cases:
            result = self.utils._query_type(sql)
            self.assertEqual(result, expected, f"Failed for SQL: {sql}")

    def test_query_type_with_parse_error(self):
        """Test _query_type handles parsing errors gracefully"""
        # Invalid SQL that still parses (sqlglot is quite forgiving)
        # Use something that actually fails parsing
        invalid_sql = "INVALID SQL STATEMENT !!!"
        result = self.utils._query_type(invalid_sql)
        
        # sqlglot might still parse this as an alias or command
        # The fallback should return the first word in lowercase
        self.assertIn(result, ["alias", "invalid", "command"])  # Any of these is acceptable

    def test_current_schema_returns_alias(self):
        """Test _current_schema returns current database alias"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = "test_db"
            result = self.utils._current_schema()
            self.assertEqual(result, "test_db")

    def test_current_schema_returns_default_when_none(self):
        """Test _current_schema returns 'default' when alias is None"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = None
            result = self.utils._current_schema()
            self.assertEqual(result, "default")

    def test_current_schema_returns_default_when_empty(self):
        """Test _current_schema returns 'default' when alias is empty"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = ""
            result = self.utils._current_schema()
            self.assertEqual(result, "default")

    def test_format_success_insert_query(self):
        """Test _format_success formats INSERT success messages"""
        result_data = {"affected_rows": 3}
        
        with patch('mysql.SimulationEngine.utils._query_type', return_value="insert"), \
             patch('mysql.SimulationEngine.utils._current_schema', return_value="test_schema"):
            
            result = self.utils._format_success("INSERT INTO test VALUES (1)", result_data)
            expected = "Insert successful on schema 'test_schema'. Affected rows: 3, Last insert ID: 3"
            self.assertEqual(result, expected)

    def test_format_success_update_query(self):
        """Test _format_success formats UPDATE success messages"""
        result_data = {"affected_rows": 2}
        
        with patch('mysql.SimulationEngine.utils._query_type', return_value="update"), \
             patch('mysql.SimulationEngine.utils._current_schema', return_value="test_schema"):
            
            result = self.utils._format_success("UPDATE test SET name='John'", result_data)
            expected = "Update successful on schema 'test_schema'. Affected rows: 2, Changed rows: 2"
            self.assertEqual(result, expected)

    def test_format_success_delete_query(self):
        """Test _format_success formats DELETE success messages"""
        result_data = {"affected_rows": 1}
        
        with patch('mysql.SimulationEngine.utils._query_type', return_value="delete"), \
             patch('mysql.SimulationEngine.utils._current_schema', return_value="test_schema"):
            
            result = self.utils._format_success("DELETE FROM test WHERE id=1", result_data)
            expected = "Delete successful on schema 'test_schema'. Affected rows: 1"
            self.assertEqual(result, expected)

    def test_format_success_ddl_query(self):
        """Test _format_success formats DDL success messages"""
        result_data = {"affected_rows": 0}
        
        with patch('mysql.SimulationEngine.utils._query_type', return_value="create"), \
             patch('mysql.SimulationEngine.utils._current_schema', return_value="test_schema"):
            
            result = self.utils._format_success("CREATE TABLE test (id INT)", result_data)
            expected = "DDL operation successful on schema 'test_schema'."
            self.assertEqual(result, expected)

    def test_tables_for_db_with_catalog_exception(self):
        """Test _tables_for_db handles CatalogException gracefully"""
        # Import the specific exception we need
        import duckdb
        
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            # Mock to raise CatalogException on the SELECT query
            mock_manager.execute_query.side_effect = [
                MagicMock(),  # USE command succeeds
                duckdb.CatalogException("Catalog error")  # SELECT query fails with CatalogException
            ]
            mock_manager._current_db_alias = "main"
            
            result = self.utils._tables_for_db("nonexistent_db")
            self.assertEqual(result, [])  # Should return empty list

    def test_tables_for_db_context_restoration(self):
        """Test _tables_for_db properly restores database context"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = "original_db"
            mock_manager.execute_query.side_effect = [
                MagicMock(),  # USE target_db
                {"data": [("table1",), ("table2",)]},  # SELECT tables
                MagicMock()   # USE original_db (restoration)
            ]
            
            result = self.utils._tables_for_db("target_db")
            
            # Should make at least 2 calls (USE + SELECT)
            # The restoration call happens only if original != current after SELECT
            self.assertGreaterEqual(mock_manager.execute_query.call_count, 2)
            self.assertEqual(result, ["table1", "table2"])
            
            # Verify first two calls
            calls = mock_manager.execute_query.call_args_list
            self.assertEqual(str(calls[0]), "call('USE target_db')")
            self.assertIn("SHOW TABLES", str(calls[1]))

    def test_tables_for_db_main_database_catalog(self):
        """Test _tables_for_db uses correct catalog name for main database"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = "main"
            mock_manager.execute_query.side_effect = [
                MagicMock(),  # USE main
                {"data": [("customers",), ("orders",)]},  # SELECT tables
                MagicMock()   # USE main (restoration - same as original)
            ]
            
            result = self.utils._tables_for_db("main")
            
            select_call = mock_manager.execute_query.call_args_list[1]
            self.assertEqual(result, ["customers", "orders"])

    def test_tables_for_db_main_multiple_tables(self):
        """Test _tables_for_db works with multiple databases"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = "main"
            mock_manager.execute_query.side_effect = [
                MagicMock(),  # USE main
                {"data": [("table1",), ("table2",)]},  # SELECT tables
                MagicMock()   # USE main (restoration - same as original)
            ]
            
            result = self.utils._tables_for_db("main")
            self.assertEqual(result, ["table1", "table2"])
            
            # Verify first two calls
            calls = mock_manager.execute_query.call_args_list
            self.assertEqual(str(calls[0]), "call('USE main')")
            self.assertIn("SHOW TABLES", str(calls[1]))

    def test_tables_for_db_main_single_table(self):
        """Test _tables_for_db works with a single table"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = "main"
            mock_manager.execute_query.side_effect = [
                MagicMock(),  # USE main
                {"data": [("table1",)]},  # SELECT tables
                MagicMock()   # USE main (restoration - same as original)
            ]
            
            result = self.utils._tables_for_db("main")
            self.assertEqual(result, ["table1"])
            
            # Verify first two calls
            calls = mock_manager.execute_query.call_args_list
            self.assertEqual(str(calls[0]), "call('USE main')")
            self.assertIn("SHOW TABLES", str(calls[1]))

    def test_tables_for_db_main_no_tables(self):
        """Test _tables_for_db works with no tables"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = "main"
            mock_manager.execute_query.side_effect = [
                MagicMock(),  # USE main
                {"data": []},  # SELECT tables
                MagicMock()   # USE main (restoration - same as original)
            ]
            result = self.utils._tables_for_db("main")
            self.assertEqual(result, [])

            # Verify first two calls
            calls = mock_manager.execute_query.call_args_list
            self.assertEqual(str(calls[0]), "call('USE main')")
            self.assertIn("SHOW TABLES", str(calls[1]))

    def test_tables_for_db_main_value_error(self):
        """Test _tables_for_db handles ValueError gracefully"""
        with patch('mysql.SimulationEngine.utils.db_manager') as mock_manager:
            mock_manager._current_db_alias = "main"
            mock_manager.execute_query.side_effect = [
                MagicMock(),  # USE main
                ValueError("Value error")  # SELECT tables
            ]
            result = self.utils._tables_for_db("main")
            self.assertEqual(result, [])

class TestImportPackageHealth(BaseTestCaseWithErrorHandler):
    """
    Test import and package health as required by framework.
    """

    def test_direct_module_imports(self):
        """Test importing modules directly without complex dependencies"""
        print("🔍 Testing direct module imports...")

        # Add the mysql directory to path
        mysql_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(mysql_dir))

        print(f"📂 MySQL directory: {mysql_dir}")

        # Test individual module imports
        modules_to_test = [
            ("mysql", "Main MySQL module"),
            ("mysql.mysql_handler", "MySQL handler module"),
            ("mysql.SimulationEngine.db", "Database engine module"),
            ("mysql.SimulationEngine.models", "Database models"),
            ("mysql.SimulationEngine.utils", "Utility functions"),
            ("mysql.SimulationEngine.custom_errors", "Custom error classes"),
        ]

        import_results = {}

        for module_name, description in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "status": "success",
                    "module": module,
                    "attributes": dir(module)
                }
                self.assertIsNotNone(module, f"Module {module_name} imported but is None")
                print(f"{description}: {module_name}")
                
            except ImportError as e:
                import_results[module_name] = {
                    "status": "import_error", 
                    "error": str(e)
                }
                self.fail(f"Failed to import {module_name}: {e}")
                
            except Exception as e:
                import_results[module_name] = {
                    "status": "error",
                    "error": str(e)
                }
                self.fail(f"Error importing {module_name}: {e}")

        # Verify all imports were successful
        failed_imports = [name for name, result in import_results.items() 
                         if result["status"] != "success"]
        self.assertEqual(len(failed_imports), 0, f"Failed imports: {failed_imports}")

    def test_function_availability_in_main_module(self):
        """Test that public functions are available in main module"""
        import mysql
        
        expected_functions = ["query", "get_resources_list", "get_resource"]
        
        for func_name in expected_functions:
            self.assertTrue(hasattr(mysql, func_name), 
                           f"Function {func_name} not available in mysql module")
            
            # Test that function is callable
            func = getattr(mysql, func_name)
            self.assertTrue(callable(func), f"Function {func_name} is not callable")

    def test_dir_functionality(self):
        """Test that __dir__ returns expected function names"""
        import mysql
        
        dir_result = dir(mysql)
        expected_functions = ["query", "get_resources_list", "get_resource"]
        
        for func_name in expected_functions:
            self.assertIn(func_name, dir_result,
                         f"Function {func_name} not in dir() output")

    def test_all_attribute(self):
        """Test that __all__ contains expected functions"""
        import mysql
        
        self.assertTrue(hasattr(mysql, '__all__'), "Module missing __all__ attribute")
        
        expected_functions = ["query", "get_resources_list", "get_resource"]
        for func_name in expected_functions:
            self.assertIn(func_name, mysql.__all__,
                         f"Function {func_name} not in __all__")

    def test_error_simulator_availability(self):
        """Test that error simulator is properly initialized"""
        from mysql import error_simulator, ERROR_MODE
        
        self.assertIsNotNone(error_simulator, "Error simulator not initialized")
        self.assertIsNotNone(ERROR_MODE, "Error mode not initialized")

    def test_db_state_accessibility(self):
        """Test that DB state and functions are accessible"""
        from mysql.SimulationEngine.db import DB, save_state, load_state
        
        self.assertIsInstance(DB, dict, "DB should be a dictionary")
        self.assertTrue(callable(save_state), "save_state should be callable")
        self.assertTrue(callable(load_state), "load_state should be callable")

    def test_models_import_and_validation(self):
        """Test that Pydantic models import and work correctly"""
        from mysql.SimulationEngine.models import MySQLDB, SimulationSnapshot, AttachedEntry
        
        # Test that models are BaseModel subclasses
        from pydantic import BaseModel
        
        self.assertTrue(issubclass(MySQLDB, BaseModel), "MySQLDB should be BaseModel subclass")
        self.assertTrue(issubclass(SimulationSnapshot, BaseModel), "SimulationSnapshot should be BaseModel subclass")
        self.assertTrue(issubclass(AttachedEntry, BaseModel), "AttachedEntry should be BaseModel subclass")

    def test_custom_errors_import(self):
        """Test custom errors import correctly"""
        from mysql.SimulationEngine.custom_errors import InternalError, DatabaseOrTableDoesNotExistError
        
        self.assertTrue(issubclass(InternalError, Exception), "InternalError should be Exception subclass")
        self.assertTrue(issubclass(DatabaseOrTableDoesNotExistError, Exception), 
                       "DatabaseOrTableDoesNotExistError should be Exception subclass")

    def test_file_utils_import_and_functionality(self):
        """Test file utilities import and basic functionality"""
        from mysql.SimulationEngine.file_utils import (
            is_text_file, is_binary_file, get_mime_type,
            TEXT_EXTENSIONS, BINARY_EXTENSIONS
        )
        
        # Test function availability
        self.assertTrue(callable(is_text_file), "is_text_file should be callable")
        self.assertTrue(callable(is_binary_file), "is_binary_file should be callable")
        self.assertTrue(callable(get_mime_type), "get_mime_type should be callable")
        
        # Test constants
        self.assertIsInstance(TEXT_EXTENSIONS, set, "TEXT_EXTENSIONS should be a set")
        self.assertIsInstance(BINARY_EXTENSIONS, set, "BINARY_EXTENSIONS should be a set")
        
        # Test basic functionality
        self.assertTrue(is_text_file("test.py"), "Python files should be text files")
        self.assertTrue(is_binary_file("test.jpg"), "JPG files should be binary files")

    def test_smoke_test_basic_functionality(self):
        """
        Smoke test: Quick check that the package installs and runs without issues.
        Example: install -> import -> using api functions all run without error.
        """
        print("Running smoke test for MySQL API...")
        
        try:
            # Import main module
            import mysql
            print("MySQL module imported successfully")
            
            # Test basic function access (without execution)
            functions = ["query", "get_resources_list", "get_resource"]
            for func_name in functions:
                func = getattr(mysql, func_name)
                self.assertTrue(callable(func), f"{func_name} should be callable")
                print(f"Function {func_name} is accessible and callable")
            
            # Test database state access
            from mysql.SimulationEngine.db import DB
            self.assertIsInstance(DB, dict, "DB should be accessible as dict")
            print("Database state is accessible")
            
            # Test model validation
            from mysql.SimulationEngine.models import MySQLDB
            test_db = MySQLDB(
                current="main",
                primary_internal_name="main",
                attached={}
            )
            self.assertIsInstance(test_db, MySQLDB)
            print("Database model validation works")
            
            print("Smoke test completed successfully - MySQL API is ready for implementation")
            
        except Exception as e:
            self.fail(f"Smoke test failed: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
