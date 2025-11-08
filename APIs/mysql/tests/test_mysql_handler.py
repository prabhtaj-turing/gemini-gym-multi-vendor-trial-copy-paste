import unittest
import os
import shutil
import sys
import json
from urllib.parse import quote
from unittest.mock import patch, call

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common_utils.base_case import BaseTestCaseWithErrorHandler
# Import DuckDBManager class for creating a new instance
from mysql.SimulationEngine.duckdb_manager import DuckDBManager
from mysql.SimulationEngine.custom_errors import InternalError

TEST_DIR_ROOT_MH = "test_mysql_handler_isolated_env" # New root for this specific test
MAIN_DB_FILE_MH_FOR_TEST = "handler_main_test.duckdb" # Specific main DB filename for these tests

class TestMySQLHandler(BaseTestCaseWithErrorHandler):
    # Modules that will be imported and used
    mh_module = None
    duckdb_lib = None # For duckdb.Error, duckdb.CatalogException

    # Patches and instances specific to this test class
    _test_dir_root_mh = TEST_DIR_ROOT_MH
    _current_class_test_dir_mh = ""
    _test_db_files_directory_mh = "" # Directory for *.duckdb files for this test
    _test_simulation_state_json_path_mh = "" # Path for the state.json for this test
    
    _original_db_manager_in_sim_db = None # To store the original db_manager from mysql.SimulationEngine.db
    _test_specific_db_manager = None # The new DuckDBManager instance for tests
    _db_manager_patcher = None # The patch object for 'mysql.SimulationEngine.db.db_manager'


    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # 1. Define paths for the isolated test environment
        cls._current_class_test_dir_mh = os.path.join(cls._test_dir_root_mh, cls.__name__)
        if os.path.exists(cls._current_class_test_dir_mh): # pragma: no cover
            shutil.rmtree(cls._current_class_test_dir_mh)
        os.makedirs(cls._current_class_test_dir_mh, exist_ok=True)

        cls._test_db_files_directory_mh = os.path.join(cls._current_class_test_dir_mh, "TestDBs")
        os.makedirs(cls._test_db_files_directory_mh, exist_ok=True)
        
        cls._test_simulation_state_json_path_mh = os.path.join(cls._current_class_test_dir_mh, "handler_simulation_state.json")

        # Ensure state JSON doesn't exist from a previous failed run before creating manager
        if os.path.exists(cls._test_simulation_state_json_path_mh): # pragma: no cover
            try: os.remove(cls._test_simulation_state_json_path_mh)
            except OSError: pass

        # 2. Create a new DuckDBManager instance configured for this isolated environment
        cls._test_specific_db_manager = DuckDBManager(
            main_url=MAIN_DB_FILE_MH_FOR_TEST, # This will be created inside _test_db_files_directory_mh
            database_directory=cls._test_db_files_directory_mh,
            simulation_state_path=cls._test_simulation_state_json_path_mh
        )

        try:
            from mysql.SimulationEngine.db import db_manager as original_global_manager
            cls._original_db_manager_in_sim_db = original_global_manager
        except ImportError: # pragma: no cover
            cls._original_db_manager_in_sim_db = None 

        cls._db_manager_patcher = patch('mysql.SimulationEngine.db.db_manager', cls._test_specific_db_manager)
        cls._db_manager_patcher.start()
        
        # Patch mysql_handler.db_manager as well, in case it was imported before SimulationEngine.db was patched
        # or if it uses `from .SimulationEngine.db import db_manager` directly.
        # This makes the patch more robust.
        cls._mh_db_manager_patcher = patch('mysql.mysql_handler.db_manager', cls._test_specific_db_manager)
        cls._mh_db_manager_patcher.start()


        import mysql.mysql_handler as handler_module
        import duckdb as ddb_lib 

        cls.mh_module = handler_module
        cls.duckdb_lib = ddb_lib


    @classmethod
    def tearDownClass(cls):
        if cls._mh_db_manager_patcher:
            cls._mh_db_manager_patcher.stop()
            cls._mh_db_manager_patcher = None

        if cls._db_manager_patcher:
            cls._db_manager_patcher.stop()
            cls._db_manager_patcher = None 

        if cls._test_specific_db_manager and cls._test_specific_db_manager._main_connection:
            try:
                cls._test_specific_db_manager.close_main_connection()
            except Exception: pass 
        cls._test_specific_db_manager = None 

        if os.path.exists(cls._current_class_test_dir_mh): 
            shutil.rmtree(cls._current_class_test_dir_mh)
        
        try: 
            if os.path.exists(cls._test_dir_root_mh) and not os.listdir(cls._test_dir_root_mh):
                os.rmdir(cls._test_dir_root_mh)
        except OSError: pass 
        
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        db_manager = self.__class__._test_specific_db_manager 

        if not (db_manager and db_manager._main_connection): # pragma: no cover
            self.fail("Test-specific DB Manager not available or connection closed at start of setUp.")

        try:
            if db_manager._current_db_alias != db_manager._main_db_alias:
                db_manager.execute_query(f"USE `{db_manager._main_db_alias}`")
        except Exception as e: # pragma: no cover
            print(f"Warning (setUp): Initial USE main failed: {e}")

        current_attachments = db_manager._attached_aliases.copy()
        for alias in current_attachments:
            try: db_manager.execute_query(f"DETACH DATABASE `{alias}`")
            except Exception as e: # pragma: no cover
                print(f"Warning (setUp): Detach DB '{alias}' failed: {e}.")
        
        db_manager._attached_aliases.clear()
        
        main_db_file_for_this_manager = os.path.join(
            db_manager._database_directory, 
            os.path.basename(db_manager._main_db_url) if db_manager._main_db_url != ":memory:" else ""
        )

        for fname in os.listdir(db_manager._database_directory): 
            file_to_check = os.path.join(db_manager._database_directory, fname)
            if file_to_check.endswith(".duckdb"):
                if db_manager._main_db_url != ":memory:" and file_to_check == main_db_file_for_this_manager:
                    continue
                # Also preserve the main DB file if it's the one defined in MAIN_DB_FILE_MH_FOR_TEST
                # This is more robust if main_url doesn't match its basename due to relative paths.
                expected_main_db_path = os.path.join(db_manager._database_directory, MAIN_DB_FILE_MH_FOR_TEST)
                if file_to_check == expected_main_db_path:
                    continue

                try: os.remove(file_to_check)
                except OSError as e: # pragma: no cover
                    print(f"Warning (setUp): Failed to remove stale DB file {file_to_check}: {e}")
        
        db_manager._current_db_alias = db_manager._main_db_alias
        db_manager._save_state() 

        try:
            conn = db_manager._main_connection
            actual_main_duckdb_name = db_manager._primary_internal_name
            if db_manager._is_main_memory : # pragma: no cover
                actual_main_duckdb_name = "memory"
            
            # Ensure we are in the main database context for table dropping
            current_ctx_query = "SELECT current_database();"
            # Sometimes current_database() might not be the alias, but the internal name.
            # So, using USE `{db_manager._main_db_alias}` is more reliable before SHOW TABLES.
            try:
                conn.execute(f"USE \"{actual_main_duckdb_name}\";")
            except Exception: # pragma: no cover
                 # Fallback if actual_main_duckdb_name is not usable in USE for some reason
                conn.execute(f"USE `{db_manager._main_db_alias}`;")


            tables = conn.execute("SHOW TABLES;").fetchall()
            for (table_name,) in tables:
                conn.execute(f'DROP TABLE IF EXISTS "{table_name}";')
        except Exception as e: # pragma: no cover
            print(f"Warning (setUp): Failed to drop tables from main DB: {e}")

    def tearDown(self):
        db_manager = self.__class__._test_specific_db_manager
        if db_manager and db_manager._main_connection:
            try:
                if db_manager._current_db_alias != db_manager._main_db_alias: # pragma: no cover
                    db_manager.execute_query(f"USE `{db_manager._main_db_alias}`")
            except Exception: pass 
        super().tearDown()

    def _execute_direct_manager(self, sql):
        return self.__class__._test_specific_db_manager.execute_query(sql)

    def _drop_db_if_exists(self, db_name_as_created):
        db_manager = self.__class__._test_specific_db_manager
        try:
            # Ensure context is main before detaching, as DETACH might depend on current context
            # or it's just safer.
            if db_manager._current_db_alias != db_manager._main_db_alias:
                db_manager.execute_query(f"USE `{db_manager._main_db_alias}`")
            
            # DuckDBManager's drop_database handles detach and file removal
            if db_name_as_created in db_manager._attached_aliases:
                db_manager.drop_database(db_name_as_created)
            else: # Fallback if not in _attached_aliases but might exist
                 db_manager.execute_query(f"DETACH DATABASE IF EXISTS `{db_name_as_created}`")
                 db_file_path = os.path.join(db_manager._database_directory, f"{db_name_as_created}.duckdb")
                 if os.path.exists(db_file_path): # pragma: no cover
                     try: os.remove(db_file_path)
                     except OSError: pass
        except Exception as e: # pragma: no cover
            print(f"Warning (_drop_db_if_exists): Failed to drop/detach DB '{db_name_as_created}': {e}")


    # --- Test Methods ---
    def test_mysql_query_insert(self):
        self._execute_direct_manager("CREATE TABLE test_insert (id INT);")
        result = self.mh_module.query("INSERT INTO test_insert VALUES (10);")
        schema_name = self.__class__._test_specific_db_manager._current_db_alias
        expected_text = f"Insert successful on schema '{schema_name}'. Affected rows: 1, Last insert ID: 1"
        self.assertEqual(result["content"][0]["text"], expected_text)

    def test_mysql_query_with_datetime(self):
        # Test handling of datetime values in query results
        self._execute_direct_manager("CREATE TABLE test_datetime (id INT, dt TIMESTAMP);")
        self._execute_direct_manager("INSERT INTO test_datetime VALUES (1, '2025-06-17 16:11:32');")
        
        # Query the table with datetime column
        result = self.mh_module.query("SELECT * FROM test_datetime;")
        
        # Verify the result can be parsed as JSON (no serialization errors)
        json_result = json.loads(result["content"][0]["text"])
        
        # Check that the datetime was properly serialized to ISO format string
        self.assertEqual(len(json_result), 1)
        self.assertEqual(len(json_result[0]), 2)  # Two columns
        self.assertEqual(json_result[0][0], 1)    # id column
        
        # The datetime should be serialized as a string in ISO format
        dt_str = json_result[0][1]
        self.assertIsInstance(dt_str, str)
        self.assertTrue(dt_str.startswith("2025-06-17T16:11:32"))

    def test_mysql_query_delete(self): # New test for delete message
        self._execute_direct_manager("CREATE TABLE test_delete (id INT);")
        self._execute_direct_manager("INSERT INTO test_delete VALUES (10);")
        result = self.mh_module.query("DELETE FROM test_delete WHERE id = 10;")
        schema_name = self.__class__._test_specific_db_manager._current_db_alias
        expected_text = f"Delete successful on schema '{schema_name}'. Affected rows: 1"
        self.assertEqual(result["content"][0]["text"], expected_text)

    def test_mysql_query_drop_table(self): # New test for DDL (DROP)
        self._execute_direct_manager("CREATE TABLE test_to_drop (id INT);")
        result = self.mh_module.query("DROP TABLE test_to_drop;")
        schema_name = self.__class__._test_specific_db_manager._current_db_alias
        expected_text = f"DDL operation successful on schema '{schema_name}'."
        self.assertEqual(result["content"][0]["text"], expected_text)

    def test_mysql_query_ddl_truncate(self):
        self._execute_direct_manager("CREATE TABLE test_truncate_ddl (id INT);")
        self._execute_direct_manager("INSERT INTO test_truncate_ddl VALUES(1);")
        result = self.mh_module.query("TRUNCATE TABLE test_truncate_ddl;")
        schema_name = self.__class__._test_specific_db_manager._current_db_alias
        expected_text = f"DDL operation successful on schema '{schema_name}'."
        self.assertEqual(result["content"][0]["text"], expected_text)
        count_res = self.mh_module.query("SELECT COUNT(*) FROM test_truncate_ddl;")
        data = json.loads(count_res['content'][0]['text'])
        self.assertEqual(data[0][0], 0)
    
    def test_mysql_query_invalid_sql_input(self): # New test for line 79
        with self.assertRaisesRegex(ValueError, "`sql` must be a non-empty string"):
            self.mh_module.query("")
        with self.assertRaisesRegex(ValueError, "`sql` must be a non-empty string"):
            self.mh_module.query("   ")
        with self.assertRaisesRegex(ValueError, "`sql` must be a non-empty string"):
            self.mh_module.query(None)
        with self.assertRaisesRegex(ValueError, "`sql` must be a non-empty string"):
            self.mh_module.query(123)

    def test_mysql_query_show_statement(self): # New test for line 116
        self._execute_direct_manager("CREATE TABLE test_for_show (id INT);")
        result = self.mh_module.query("SHOW TABLES;")
        # The result from db_manager for SHOW is like {'columns': [...], 'data': [[...]]}
        # This should be json.dumps(result, indent=2)
        expected_db_manager_result = self.__class__._test_specific_db_manager.execute_query("SHOW TABLES;")
        self.assertEqual(result["content"][0]["text"], json.dumps(expected_db_manager_result, indent=2))

    # New test for lines 127-132 (mocking db query results)
    def test_get_resources_list_mocked_db_query_results(self):
        # Case 1: execute_query returns {"data": None}
        with patch.object(self.__class__._test_specific_db_manager, 'get_db_names') as mock_execute:
            result = self.mh_module.get_resources_list()
            self.assertEqual(result, {"resources": []})
            mock_execute.assert_called_once_with()
            
    # New test for lines 127-132 (main DB exists but has no tables)
    def test_get_resources_list_main_db_no_tables_no_other_dbs(self):
        # Setup ensures main DB is empty and no other DBs are attached.
        # So, _tables_for_db(main_alias) will return [].
        # db_rows will contain main_alias, but the inner loop for tables won't add anything.
        result = self.mh_module.get_resources_list()
        self.assertEqual(result, {"resources": []})

    def test_get_resource_non_existent_db(self):
        with self.assertRaises(InternalError):
             self.mh_module.get_resource("ghost_db_for_resource_test/table/schema")

    def test_get_resource_non_existent_table(self):
        db_manager = self.__class__._test_specific_db_manager
        main_db_alias = db_manager._main_db_alias
        with self.assertRaises(InternalError):
             self.mh_module.get_resource(f"{main_db_alias}/ghost_table_for_resource_test/schema")
    
    # New test for line 158 (mocking DESCRIBE results)
    def test_get_resource_mocked_describe_results(self):
        db_manager = self.__class__._test_specific_db_manager
        db_name = db_manager._main_db_alias
        table_name = "table_for_mock_describe"
        
        # Table must exist for DESCRIBE to be attempted on it (not raise CatalogException for table)
        self._execute_direct_manager(f"USE `{db_name}`")
        self._execute_direct_manager(f"CREATE TABLE {table_name} (id INT);")
        
        uri = f"{db_name}/{table_name}/schema"
        
        original_execute_query_method = db_manager.execute_query

        # Case 1: DESCRIBE returns {"data": None}
        mock_describe_result_none = {"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "data": None}
        
        def side_effect_describe_none(*args, **kwargs):
            query_sql = args[0]
            if query_sql.upper().startswith("USE"):
                return original_execute_query_method(*args, **kwargs)
            # Handle different DESCRIBE formats including new secure case-preserved format (no semicolon)
            if (query_sql.upper() == f"DESCRIBE `{table_name.upper()}`" or 
                query_sql.upper() == f"DESCRIBE {table_name.upper()}" or
                query_sql == f"DESCRIBE `{table_name}`"):
                return mock_describe_result_none
            return original_execute_query_method(*args, **kwargs) # pragma: no cover

        with patch.object(db_manager, 'execute_query', side_effect=side_effect_describe_none) as mock_execute_qs:
            result = self.mh_module.get_resource(uri)
            self.assertEqual(json.loads(result["contents"][0]["text"]), [])
            # Check calls were made
            expected_calls = [
                 call(f"USE {db_name}"), # Note: get_resource does not quote db_name in USE
                 call(f"DESCRIBE {table_name}")
            ]
            # Check that the USE call happened - with new security escaping, identifiers are wrapped in backticks
            use_call_found = False
            describe_call_found = False
            
            for call_args in mock_execute_qs.call_args_list:
                sql_call = call_args[0][0]
                sql_upper = sql_call.upper()
                
                # Check for USE call - handle different escaping formats
                if (sql_upper == f"USE {db_name.upper()}" or 
                    sql_upper == f"USE `{db_name.upper()}`" or 
                    sql_call == f"USE `{db_name}`"):  # Case-preserved secure format
                    use_call_found = True
                
                # Check for DESCRIBE call - handle different escaping formats (no semicolon)
                if (sql_upper == f"DESCRIBE {table_name.upper()}" or 
                    sql_upper == f"DESCRIBE `{table_name.upper()}`" or 
                    sql_call == f"DESCRIBE `{table_name}`"):  # Case-preserved secure format
                    describe_call_found = True
            
            self.assertTrue(use_call_found, f"USE call not found in: {[c[0][0] for c in mock_execute_qs.call_args_list]}")
            self.assertTrue(describe_call_found, f"DESCRIBE call not found in: {[c[0][0] for c in mock_execute_qs.call_args_list]}")


        # Case 2: DESCRIBE returns {"data": []}
        mock_describe_result_empty = {"columns": ["column_name", "column_type", "null", "key", "default", "extra"], "data": []}

        def side_effect_describe_empty(*args, **kwargs):
            query_sql = args[0]
            if query_sql.upper().startswith("USE"):
                return original_execute_query_method(*args, **kwargs)
            # Handle different DESCRIBE formats including new secure case-preserved format (no semicolon)
            if (query_sql.upper() == f"DESCRIBE `{table_name.upper()}`" or 
                query_sql.upper() == f"DESCRIBE {table_name.upper()}" or
                query_sql == f"DESCRIBE `{table_name}`"):
                return mock_describe_result_empty
            return original_execute_query_method(*args, **kwargs) # pragma: no cover
        
        with patch.object(db_manager, 'execute_query', side_effect=side_effect_describe_empty) as mock_execute_qs:
            result = self.mh_module.get_resource(uri)
            self.assertEqual(json.loads(result["contents"][0]["text"]), [])

    def test_get_resource_invalid_identifier(self):
        """Test that invalid identifiers are properly rejected.
        
        Note: After the word boundary fix, identifiers like 'CREATE_TABLE' and 'DROPdb'
        are now correctly allowed since the keywords are part of larger words, not standalone.
        """
        # Character-based patterns (should be rejected)
        with self.assertRaisesRegex(ValueError, "Invalid URI: Invalid table name: contains forbidden pattern ';'"): 
            self.mh_module.get_resource("db/;table/schema")
        with self.assertRaisesRegex(ValueError, "Invalid URI: Invalid database name: contains forbidden pattern '--'"): 
            self.mh_module.get_resource("--db/table/schema")
        
        # Invalid characters (should be rejected)
        with self.assertRaisesRegex(ValueError, "Invalid URI: Invalid table name: contains invalid characters. Only letters, numbers, underscore, dot, and dash are allowed"): 
            self.mh_module.get_resource("db/table**name/schema")
        with self.assertRaisesRegex(ValueError, "Invalid URI: Invalid database name: contains invalid characters. Only letters, numbers, underscore, dot, and dash are allowed"): 
            self.mh_module.get_resource(f"db[]name/tablename/schema")
        
        # Standalone keywords with word boundaries (should be rejected)
        with self.assertRaisesRegex(ValueError, "Invalid URI: Invalid table name: contains forbidden keyword 'CREATE'"): 
            self.mh_module.get_resource("db/CREATE.TABLE/schema")  # Changed: dot creates word boundary
        with self.assertRaisesRegex(ValueError, "Invalid URI: Invalid database name: contains forbidden keyword 'DROP'"): 
            self.mh_module.get_resource("DROP-db/table/schema")  # Changed: dash creates word boundary

    def test_current_schema_default_fallback(self):
        db_manager_under_test = self.__class__._test_specific_db_manager 
        original_alias = db_manager_under_test._current_db_alias
        # Create tables with unique names to avoid conflicts if not dropped by schema name issues
        table_none = "test_schema_fallback_none"
        table_empty = "test_schema_fallback_empty"
        self._execute_direct_manager(f"DROP TABLE IF EXISTS {table_none}")
        self._execute_direct_manager(f"DROP TABLE IF EXISTS {table_empty}")
        try:
            with patch.object(db_manager_under_test, '_current_db_alias', None):
                # Need to be in *some* valid DB for CREATE TABLE to succeed if schema is 'main'
                # but operations are on the actual current connection's database.
                # The 'main' schema name is for display. Actual operations use the current DB.
                self._execute_direct_manager(f"CREATE TABLE {table_none} (id INT);")
                res = self.mh_module.query(f"INSERT INTO {table_none} VALUES (1);")
                self.assertIn("Insert successful on schema 'main'", res['content'][0]['text'])
            
            with patch.object(db_manager_under_test, '_current_db_alias', ""):
                self._execute_direct_manager(f"CREATE TABLE {table_empty} (id INT);")
                res = self.mh_module.query(f"INSERT INTO {table_empty} VALUES (1);")
                self.assertIn("Insert successful on schema 'main'", res['content'][0]['text'])
        finally: 
             db_manager_under_test._current_db_alias = original_alias
             # Restore context if original_alias was valid
             if original_alias:
                 try: 
                     # Ensure the alias is valid before trying to USE it
                     if original_alias == db_manager_under_test._main_db_alias or \
                        original_alias in db_manager_under_test._attached_aliases or \
                        any(original_alias == attached_info['alias'] for attached_info in db_manager_under_test._attached_aliases.values()): # More robust check for alias
                         db_manager_under_test.execute_query(f"USE `{original_alias}`")
                     else: # pragma: no cover
                         db_manager_under_test.execute_query(f"USE `{db_manager_under_test._main_db_alias}`")
                 except Exception: # pragma: no cover
                     # Fallback to main if restoration fails
                     try: db_manager_under_test.execute_query(f"USE `{db_manager_under_test._main_db_alias}`")
                     except Exception: pass
             else: # pragma: no cover
                  try: db_manager_under_test.execute_query(f"USE `{db_manager_under_test._main_db_alias}`")
                  except Exception: pass
             # Clean up tables created during test
             self._execute_direct_manager(f"DROP TABLE IF EXISTS {table_none}")
             self._execute_direct_manager(f"DROP TABLE IF EXISTS {table_empty}")


    def test_get_resource_valid_returns_full_schema(self):
        db_manager = self.__class__._test_specific_db_manager
        db_name = db_manager._main_db_alias
        table_name = "res_table_full_schema"
        self._execute_direct_manager(f"USE `{db_name}`")
        self._execute_direct_manager(f"""
            CREATE TABLE {table_name} (
                id INT PRIMARY KEY, name VARCHAR(255) NOT NULL DEFAULT 'Unnamed', 
                description TEXT, quantity INTEGER DEFAULT 0,
                price DECIMAL(10,2) NULL, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP); """)
        uri = f"{db_name}/{table_name}/schema"
        result = self.mh_module.get_resource(uri)
        content = result["contents"][0]
        self.assertEqual(content["uri"], uri); self.assertEqual(content["mimeType"], "application/json")
        schema_data = json.loads(content["text"])
        expected_schema_data = [
            {"column_name": "id", "data_type": "INTEGER", "is_nullable": "NO", "column_default": None},
            {"column_name": "name", "data_type": "VARCHAR", "is_nullable": "NO", "column_default": "'Unnamed'"},
            {"column_name": "description", "data_type": "VARCHAR", "is_nullable": "YES", "column_default": None}, # TEXT is an alias for VARCHAR in DuckDB describe
            {"column_name": "quantity", "data_type": "INTEGER", "is_nullable": "YES", "column_default": "0"},
            {"column_name": "price", "data_type": "DECIMAL(10,2)", "is_nullable": "YES", "column_default": None},
            {"column_name": "last_updated", "data_type": "TIMESTAMP", "is_nullable": "YES", "column_default": "now()"},] # DuckDB DESCRIBE shows 'now()' for CURRENT_TIMESTAMP
        self.assertEqual(len(schema_data), len(expected_schema_data), "Column count mismatch")
        for i, actual_col in enumerate(schema_data):
            expected_col = expected_schema_data[i]
            self.assertEqual(actual_col["column_name"], expected_col["column_name"])
            actual_base_type = actual_col["data_type"].split("(")[0].upper(); expected_base_type = expected_col["data_type"].split("(")[0].upper()
            if expected_base_type == "TEXT": expected_base_type = "VARCHAR" 
            if expected_base_type == "INT": expected_base_type = "INTEGER"
            if actual_base_type == "INT": actual_base_type = "INTEGER" # Normalize INT to INTEGER from DuckDB
            if expected_base_type == "DECIMAL": self.assertEqual(actual_col["data_type"].upper(), expected_col["data_type"].upper())
            elif expected_base_type == "TIMESTAMP": 
                # Accept both TIMESTAMP and TIMESTAMP WITH TIME ZONE
                self.assertTrue(actual_base_type in ["TIMESTAMP", "TIMESTAMP WITH TIME ZONE"])
            else: self.assertEqual(actual_base_type, expected_base_type)
            self.assertEqual(actual_col["is_nullable"], expected_col["is_nullable"])
            if expected_col["column_default"] is None: self.assertIsNone(actual_col["column_default"])
            elif expected_col["column_default"].lower() in ("now()", "current_timestamp"):
                 self.assertTrue(actual_col["column_default"] and ("now()" in actual_col["column_default"].lower() or "current_timestamp" in actual_col["column_default"].lower() or "duckdb_timestamp" in actual_col["column_default"].lower())) # duckdb specific variations
            else: self.assertEqual(str(actual_col["column_default"]), str(expected_col["column_default"]))

    def test_get_resource_empty_table_returns_full_schema(self):
        db_manager = self.__class__._test_specific_db_manager
        db_name = db_manager._main_db_alias
        table_name = "res_empty_table_full_schema"
        self._execute_direct_manager(f"USE `{db_name}`")
        self._execute_direct_manager(f"CREATE TABLE {table_name} (col_a BIGINT NOT NULL, col_b TEXT DEFAULT 'EMPTY');")
        uri = f"{db_name}/{table_name}/schema"
        result = self.mh_module.get_resource(uri)
        content = result["contents"][0]; schema_data = json.loads(content["text"])
        expected_schema_data = [
            {"column_name": "col_a", "data_type": "BIGINT", "is_nullable": "NO", "column_default": None},
            {"column_name": "col_b", "data_type": "VARCHAR", "is_nullable": "YES", "column_default": "'EMPTY'"},] # TEXT becomes VARCHAR
        self.assertEqual(len(schema_data), len(expected_schema_data))
        for i, actual_col in enumerate(schema_data):
            expected_col = expected_schema_data[i]; self.assertEqual(actual_col["column_name"], expected_col["column_name"])
            actual_base_type = actual_col["data_type"].split("(")[0].upper(); expected_base_type = expected_col["data_type"].split("(")[0].upper()
            if expected_base_type == "TEXT": expected_base_type = "VARCHAR"
            self.assertEqual(actual_base_type, expected_base_type)
            self.assertEqual(actual_col["is_nullable"], expected_col["is_nullable"]); self.assertEqual(actual_col["column_default"], expected_col["column_default"])

    def test_get_resource_invalid_uri_format(self):
        with self.assertRaisesRegex(ValueError, "`uri` must be in the form '<db>/<table>/schema'"): self.mh_module.get_resource("db/table")
        with self.assertRaisesRegex(ValueError, "`uri` must end with '/schema'"): self.mh_module.get_resource("db/table/invalid_tail")
        with self.assertRaisesRegex(ValueError, "`uri` must be in the form '<db>/<table>/schema'"): self.mh_module.get_resource(123) # type: ignore

    def test_mysql_query_database_exception_handling(self):
        """Test query when database operation fails (lines 66-67)"""
        from mysql.SimulationEngine.custom_errors import InternalError
        
        # Mock the db_manager to raise an exception during execute_query
        with patch.object(self._test_specific_db_manager, 'execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Database connection failed")
            
            with self.assertRaises(InternalError) as context:
                self.mh_module.query("SELECT * FROM users")
            
            # The InternalError should wrap the original exception
            self.assertIn("An error occurred during query execution", str(context.exception))

    def test_mysql_query_select_data_none_handling(self):
        """Test SELECT query handling when data is None vs missing"""
        # Test case 1: data key missing
        with patch.object(self._test_specific_db_manager, 'execute_query') as mock_execute:
            mock_execute.return_value = {"columns": ["id", "name"]}  # No 'data' key
            
            result = self.mh_module.query("SELECT id, name FROM users")
            
            # Should return empty array as JSON string
            self.assertEqual(result["content"][0]["text"], "[]")
        
        # Test case 2: data key exists but value is None
        with patch.object(self._test_specific_db_manager, 'execute_query') as mock_execute:
            mock_execute.return_value = {"columns": ["id", "name"], "data": None}
            
            result = self.mh_module.query("SELECT id, name FROM users")
            
            # Should return empty array as JSON string, not "null"
            self.assertEqual(result["content"][0]["text"], "[]")
        
        # Test case 3: data key exists with empty list
        with patch.object(self._test_specific_db_manager, 'execute_query') as mock_execute:
            mock_execute.return_value = {"columns": ["id", "name"], "data": []}
            
            result = self.mh_module.query("SELECT id, name FROM users")
            
            # Should return empty array as JSON string
            self.assertEqual(result["content"][0]["text"], "[]")
        
        # Test case 4: data key exists with actual data
        with patch.object(self._test_specific_db_manager, 'execute_query') as mock_execute:
            mock_execute.return_value = {"columns": ["id", "name"], "data": [[1, "John"], [2, "Jane"]]}
            
            result = self.mh_module.query("SELECT id, name FROM users")
            
            # Should return the data as formatted JSON
            expected_json = json.dumps([[1, "John"], [2, "Jane"]], indent=2)
            self.assertEqual(result["content"][0]["text"], expected_json)

    def test_get_resource_false_positive_keywords_in_names(self):
        """Test that legitimate table names containing SQL keywords as substrings are allowed.
        
        This addresses the false positive issue where names like 'scheduler_execution' 
        were incorrectly flagged for containing 'EXEC'.
        """
        db_manager = self.__class__._test_specific_db_manager
        db_name = db_manager._main_db_alias
        
        # Test cases: legitimate table names that contain SQL keywords as substrings
        test_cases = [
            ("scheduler_execution", "Contains 'exec' as substring"),
            ("update_log", "Contains 'update' as substring"),
            ("insert_queue", "Contains 'insert' as substring"),
            ("delete_history", "Contains 'delete' as substring"),
            ("create_timestamp", "Contains 'create' as substring"),
            ("drop_zone", "Contains 'drop' as substring"),
            ("alter_events", "Contains 'alter' as substring"),
            ("truncate_policy", "Contains 'truncate' as substring"),
            ("execute_plan", "Contains 'execute' as substring"),
            ("data_execution_log", "Contains 'execution' as substring"),
            ("pre_update_trigger", "Contains 'update' as substring"),
            ("post_insert_hook", "Contains 'insert' as substring"),
        ]
        
        for table_name, description in test_cases:
            with self.subTest(table_name=table_name, description=description):
                # Create table with the test name
                self._execute_direct_manager(f"USE `{db_name}`")
                self._execute_direct_manager(f"""
                    CREATE TABLE {table_name} (
                        id INT PRIMARY KEY,
                        name VARCHAR(100)
                    )
                """)
                
                # This should NOT raise an error - the keyword is part of a larger word
                uri = f"{db_name}/{table_name}/schema"
                try:
                    result = self.mh_module.get_resource(uri)
                    
                    # Verify we got a valid response
                    self.assertIn("contents", result)
                    self.assertEqual(len(result["contents"]), 1)
                    self.assertEqual(result["contents"][0]["uri"], uri)
                    
                    # Parse the schema to verify it's valid JSON
                    schema = json.loads(result["contents"][0]["text"])
                    self.assertIsInstance(schema, list)
                    self.assertGreater(len(schema), 0)
                    
                finally:
                    # Clean up
                    self._execute_direct_manager(f"DROP TABLE IF EXISTS {table_name}")

    def test_get_resource_rejects_actual_sql_keywords(self):
        """Test that table names that ARE actual SQL keywords are properly rejected.
        
        Note: Word boundaries in regex treat underscores as word characters, so
        'test_EXEC_table' is considered one word and EXEC is not a standalone keyword.
        This is correct behavior - we want to reject standalone keywords or keywords
        separated by non-alphanumeric characters (dots, dashes, spaces).
        """
        db_manager = self.__class__._test_specific_db_manager
        db_name = db_manager._main_db_alias
        
        # Test cases: names that are actual SQL keywords (should be rejected)
        # These use dots and dashes as separators, which ARE word boundaries
        malicious_cases = [
            ("EXEC", "Standalone EXEC keyword"),
            ("exec", "Lowercase exec keyword"),
            ("DROP", "Standalone DROP keyword"),
            ("UPDATE", "Standalone UPDATE keyword"),
            ("DELETE", "Standalone DELETE keyword"),
            ("INSERT", "Standalone INSERT keyword"),
            ("CREATE", "Standalone CREATE keyword"),
            ("ALTER", "Standalone ALTER keyword"),
            ("TRUNCATE", "Standalone TRUNCATE keyword"),
            ("EXECUTE", "Standalone EXECUTE keyword"),
            ("test.EXEC.table", "EXEC as whole word with dots"),
            ("test-DROP-table", "DROP as whole word with dashes"),
            ("UPDATE.log", "UPDATE as whole word at start"),
            ("log.DELETE", "DELETE as whole word at end"),
        ]
        
        for table_name, description in malicious_cases:
            with self.subTest(table_name=table_name, description=description):
                uri = f"{db_name}/{table_name}/schema"
                
                # This SHOULD raise a ValueError
                with self.assertRaises(ValueError) as context:
                    self.mh_module.get_resource(uri)
                
                # Verify the error message mentions the forbidden keyword
                error_msg = str(context.exception).lower()
                self.assertIn("forbidden", error_msg)

    def test_get_resource_rejects_character_patterns(self):
        """Test that character-based SQL injection patterns are properly rejected."""
        db_manager = self.__class__._test_specific_db_manager
        db_name = db_manager._main_db_alias
        
        # Test cases: names with dangerous character patterns
        # These should be rejected because they contain forbidden characters
        character_pattern_cases = [
            ("test;DROP", ";", "Contains semicolon"),
            ("test--comment", "--", "Contains SQL comment marker --"),
            ("users;", ";", "Contains semicolon"),
        ]
        
        for table_name, expected_pattern, description in character_pattern_cases:
            with self.subTest(table_name=table_name, description=description):
                uri = f"{db_name}/{table_name}/schema"
                
                # This SHOULD raise a ValueError
                with self.assertRaises(ValueError) as context:
                    self.mh_module.get_resource(uri)
                
                # Verify the error message mentions forbidden pattern
                error_msg = str(context.exception).lower()
                self.assertIn("forbidden", error_msg,
                             f"Expected 'forbidden' in error message for pattern '{expected_pattern}', got: {error_msg}")

    def test_get_resource_edge_cases_word_boundaries(self):
        """Test edge cases for word boundary detection in keyword matching.
        
        Word boundaries (\b) in regex:
        - Treat underscores as word characters (alphanumeric + underscore)
        - Treat dots, dashes, spaces as word boundaries
        - So 'test_EXEC_table' is ONE word (EXEC not standalone)
        - But 'test.EXEC.table' has EXEC as a standalone word
        """
        db_manager = self.__class__._test_specific_db_manager
        db_name = db_manager._main_db_alias
        
        # Test cases: edge cases that should be ALLOWED (keywords as substrings or with underscores)
        allowed_edge_cases = [
            ("execution", "Contains 'exec' but not as whole word"),
            ("executor", "Contains 'exec' but not as whole word"),
            ("inexecutable", "Contains 'exec' in middle"),
            ("updateable", "Contains 'update' but not as whole word"),
            ("inserted", "Contains 'insert' but not as whole word"),
            ("deleted", "Contains 'delete' but not as whole word"),
            ("created", "Contains 'create' but not as whole word"),
            ("altered", "Contains 'alter' but not as whole word"),
            ("droplet", "Contains 'drop' but not as whole word"),
            ("test_EXEC_table", "EXEC with underscores (one word)"),
            ("DROP_users", "DROP with underscore (one word)"),
            ("users_DELETE", "DELETE with underscore (one word)"),
            ("pre_UPDATE_log", "UPDATE with underscores (one word)"),
        ]
        
        for table_name, description in allowed_edge_cases:
            with self.subTest(table_name=table_name, description=description):
                self._execute_direct_manager(f"USE `{db_name}`")
                self._execute_direct_manager(f"""
                    CREATE TABLE {table_name} (id INT PRIMARY KEY)
                """)
                
                uri = f"{db_name}/{table_name}/schema"
                try:
                    # Should NOT raise an error
                    result = self.mh_module.get_resource(uri)
                    self.assertIn("contents", result)
                finally:
                    self._execute_direct_manager(f"DROP TABLE IF EXISTS {table_name}")
        
        # Test cases: edge cases that should be REJECTED (keywords as whole words with dots/dashes)
        rejected_edge_cases = [
            ("test.EXEC.table", "EXEC as whole word with dots"),
            ("test-DROP-table", "DROP as whole word with dashes"),
            ("UPDATE.log", "UPDATE as whole word at start"),
            ("log.DELETE", "DELETE as whole word at end"),
            ("pre-INSERT-post", "INSERT as whole word with dashes"),
        ]
        
        for table_name, description in rejected_edge_cases:
            with self.subTest(table_name=table_name, description=description):
                uri = f"{db_name}/{table_name}/schema"
                
                # Should raise ValueError
                with self.assertRaises(ValueError) as context:
                    self.mh_module.get_resource(uri)
                
                error_msg = str(context.exception).lower()
                self.assertIn("forbidden", error_msg)


if __name__ == "__main__": # pragma: no cover
    unittest.main(verbosity=2)