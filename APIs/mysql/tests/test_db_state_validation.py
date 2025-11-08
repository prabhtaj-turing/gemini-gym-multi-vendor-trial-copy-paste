"""
Database State Validation and Load/Save Tests

This module tests database structure validation using Pydantic models,
state persistence, and load/save functionality as required by the 
Service Engineering Test Framework Guidelines.
"""

import unittest
import os
import shutil
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from common_utils.base_case import BaseTestCaseWithErrorHandler
from mysql.SimulationEngine.models import (
    MySQLDB, SimulationSnapshot, AttachedEntry,
    CustomerRecord, OrderRecord, ProductRecord, 
    StockLevelRecord, DatabaseSchema, DatabaseTable
)
from mysql.SimulationEngine.db import (
    DB, save_state, load_state, _load_json, _scan_duckdb_files, 
    _sync_snapshot, SIMULATION_DEFAULT_DB_PATH
)


class TestDatabaseValidation(BaseTestCaseWithErrorHandler):
    """
    Test database structure validation using Pydantic models.
    Ensures DB setup validates against expected schemas.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_dir = tempfile.mkdtemp(prefix="mysql_db_test_")
        cls.test_db_path = os.path.join(cls.test_dir, "test_mysql_db.json")

    @classmethod 
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        super().tearDownClass()

    def test_db_module_harmony(self):
        """
        Test that the database used by the db module is in harmony with the sample DB.
        This ensures that tests are running against the expected data structure.
        """
        try:
            validated_db = MySQLDB(**DB)
            self.assertIsInstance(validated_db, MySQLDB)
            self.assertEqual(validated_db.current, "main")
            self.assertIn("attached", validated_db.__dict__)
        except Exception as e:
            self.fail(f"DB module data structure validation failed: {e}")

    def test_mysql_db_validation_valid_structure(self):
        """Test MySQLDB model validates correct database structure"""
        valid_data = {
            "attached": {
                "main_db": {
                    "sanitized": "main_db",
                    "path": "main_db.duckdb"
                },
                "inventory_db": {
                    "sanitized": "inventory_db", 
                    "path": "inventory_db.duckdb"
                }
            },
            "current": "main",
            "primary_internal_name": "main_db",
            "version": "1.0",
            "databases": {}
        }
        
        validated_db = MySQLDB(**valid_data)
        self.assertEqual(validated_db.current, "main")
        self.assertEqual(validated_db.primary_internal_name, "main_db")
        self.assertIn("main_db", validated_db.attached)

    def test_mysql_db_validation_invalid_current(self):
        """Test MySQLDB model rejects invalid current database"""
        invalid_data = {
            "attached": {},
            "current": "",  # Empty string should fail
            "primary_internal_name": "main"
        }
        
        with self.assertRaises(ValueError) as context:
            MySQLDB(**invalid_data)
        
        self.assertIn("current database must be a non-empty string", str(context.exception))

    def test_mysql_db_validation_invalid_timestamp(self):
        """Test MySQLDB model validates timestamp format"""
        invalid_data = {
            "attached": {},
            "current": "main",
            "primary_internal_name": "main",
            "last_updated": "invalid-timestamp"
        }
        
        with self.assertRaises(ValueError) as context:
            MySQLDB(**invalid_data)
        
        self.assertIn("last_updated must be in ISO format", str(context.exception))

    def test_customer_record_validation(self):
        """Test CustomerRecord model validation"""
        valid_customer = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe", 
            "email": "john.doe@example.com",
            "city": "New York"
        }
        
        customer = CustomerRecord(**valid_customer)
        self.assertEqual(customer.id, 1)
        self.assertEqual(customer.email, "john.doe@example.com")

    def test_customer_record_invalid_email(self):
        """Test CustomerRecord rejects invalid email"""
        invalid_customer = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",  # Missing @ and domain
            "city": "New York"
        }
        
        with self.assertRaises(ValueError):
            CustomerRecord(**invalid_customer)

    def test_order_record_validation(self):
        """Test OrderRecord model validation"""
        valid_order = {
            "id": 100,
            "order_date": "2023-12-25",
            "customer_id": 1,
            "total_amount": 299.99
        }
        
        order = OrderRecord(**valid_order)
        self.assertEqual(order.id, 100)
        self.assertEqual(order.total_amount, 299.99)

    def test_order_record_invalid_date(self):
        """Test OrderRecord rejects invalid date format"""
        invalid_order = {
            "id": 100,
            "order_date": "25-12-2023",  # Wrong format
            "customer_id": 1,
            "total_amount": 299.99
        }
        
        with self.assertRaises(ValueError) as context:
            OrderRecord(**invalid_order)
        
        # Check for pattern mismatch error (Pydantic v2 format)
        error_str = str(context.exception)
        self.assertTrue(
            "string_pattern_mismatch" in error_str or "Order date must be in YYYY-MM-DD format" in error_str,
            f"Expected pattern validation error, got: {error_str}"
        )

    def test_simulation_snapshot_validation(self):
        """Test SimulationSnapshot model validation"""
        valid_snapshot = {
            "attached": {
                "test_db": {
                    "sanitized": "test_db",
                    "path": "test_db.duckdb"
                }
            },
            "current": "main",
            "primary_internal_name": "main"
        }
        
        snapshot = SimulationSnapshot(**valid_snapshot)
        self.assertEqual(snapshot.current, "main")
        self.assertIn("test_db", snapshot.attached)

    def test_simulation_snapshot_invalid_attached(self):
        """Test SimulationSnapshot rejects invalid attached structure"""
        invalid_snapshot = {
            "attached": "not-a-dict",  # Should be dict
            "current": "main", 
            "primary_internal_name": "main"
        }
        
        with self.assertRaises(TypeError) as context:
            SimulationSnapshot(**invalid_snapshot)
        
        self.assertIn("attached must be an object", str(context.exception))


class TestStateLoadSave(BaseTestCaseWithErrorHandler):
    """
    Test state load/save functionality with backward compatibility.
    Tests file I/O operations and state persistence.
    """

    def setUp(self):
        super().setUp()
        self.test_dir = tempfile.mkdtemp(prefix="mysql_state_test_")
        self.test_file = os.path.join(self.test_dir, "test_state.json")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        super().tearDown()

    def test_save_state_creates_file(self):
        """Test save_state creates file with correct content"""
        test_data = {
            "attached": {"test": {"sanitized": "test", "path": "test.duckdb"}},
            "current": "main"
        }
        
        # Temporarily override DB for testing
        original_db = DB.copy()
        DB.clear()
        DB.update(test_data)
        
        try:
            save_state(self.test_file)
            self.assertTrue(os.path.exists(self.test_file))
            
            with open(self.test_file, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data["current"], "main")
            self.assertIn("test", saved_data["attached"])
        
        finally:
            # Restore original DB
            DB.clear()
            DB.update(original_db)

    def test_load_state_overwrites_db(self):
        """Test load_state properly overwrites DB content"""
        test_data = {
            "attached": {"loaded": {"sanitized": "loaded", "path": "loaded.duckdb"}},
            "current": "loaded_db",
            "primary_internal_name": "loaded"
        }
        
        # Create test file
        with open(self.test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Store original DB
        original_db = DB.copy()
        
        try:
            load_state(self.test_file)
            self.assertEqual(DB["current"], "loaded_db")
            self.assertIn("loaded", DB["attached"])
        
        finally:
            # Restore original DB
            DB.clear()
            DB.update(original_db)

    def test_load_json_handles_corrupt_file(self):
        """Test _load_json gracefully handles corrupt JSON"""
        # Create corrupt JSON file
        with open(self.test_file, 'w') as f:
            f.write('{ invalid json')
        
        result = _load_json(self.test_file)
        self.assertEqual(result, {})  # Should return empty dict

    def test_load_json_handles_missing_file(self):
        """Test _load_json handles missing file"""
        nonexistent_file = os.path.join(self.test_dir, "missing.json")
        result = _load_json(nonexistent_file)
        self.assertEqual(result, {})  # Should return empty dict

    def test_load_json_handles_non_dict_content(self):
        """Test _load_json handles non-dictionary JSON content"""
        with open(self.test_file, 'w') as f:
            json.dump(["not", "a", "dict"], f)
        
        result = _load_json(self.test_file)
        self.assertEqual(result, {})  # Should return empty dict

    def test_scan_duckdb_files_finds_databases(self):
        """Test _scan_duckdb_files finds .duckdb files"""
        # Create temporary directory with .duckdb files
        sample_dir = os.path.join(self.test_dir, "sample_dbs")
        os.makedirs(sample_dir)
        
        # Create some .duckdb files
        test_files = ["test1.duckdb", "test2.duckdb", "not_db.txt"]
        for filename in test_files:
            Path(os.path.join(sample_dir, filename)).touch()
        
        # Mock SAMPLE_DB_DIR to our test directory
        with patch('mysql.SimulationEngine.db.SAMPLE_DB_DIR', sample_dir):
            result = _scan_duckdb_files()
        
        self.assertIn("test1", result)
        self.assertIn("test2", result)
        self.assertEqual(result["test1"], "test1.duckdb")
        self.assertEqual(result["test2"], "test2.duckdb")
        self.assertNotIn("not_db", result)

    def test_sync_snapshot_fixes_divergent_files(self):
        """Test _sync_snapshot fixes divergent snapshot and files"""
        # Create test directory with .duckdb files
        sample_dir = os.path.join(self.test_dir, "sample_dbs")
        os.makedirs(sample_dir)
        Path(os.path.join(sample_dir, "actual.duckdb")).touch()
        
        # Create snapshot with different files
        test_snapshot = {
            "attached": {
                "missing": {"sanitized": "missing", "path": "missing.duckdb"}
            },
            "current": "main"
        }
        
        # Mock dependencies
        with patch('mysql.SimulationEngine.db.SAMPLE_DB_DIR', sample_dir), \
             patch('mysql.SimulationEngine.db.db_manager') as mock_manager, \
             patch('mysql.SimulationEngine.db.SIMULATION_DEFAULT_DB_PATH', self.test_file):
            
            mock_manager._sanitize_for_duckdb_alias_and_filename.return_value = "actual"
            mock_manager._main_db_alias = "main"
            
            result = _sync_snapshot(test_snapshot)
        
        # Should create file and fix snapshot
        self.assertTrue(os.path.exists(self.test_file))
        self.assertIn("actual", result["attached"])
        self.assertNotIn("missing", result["attached"])

    def test_backward_compatibility_old_format(self):
        """Test loading state maintains backward compatibility"""
        # Test with older format that might be missing some fields
        old_format_data = {
            "attached": {"old_db": {"sanitized": "old_db", "path": "old.duckdb"}},
            "current": "main"
            # Missing some newer fields like version, etc.
        }
        
        with open(self.test_file, 'w') as f:
            json.dump(old_format_data, f)
        
        original_db = DB.copy()
        
        try:
            load_state(self.test_file)
            # Should load successfully without newer fields
            self.assertEqual(DB["current"], "main")
            self.assertIn("old_db", DB["attached"])
        
        finally:
            DB.clear()
            DB.update(original_db)

    def test_load_default_database_structure(self):
        """Test loading from existing default MySQL database structure"""
        default_db_file = os.path.join(PROJECT_ROOT, "DBs", "MySqlDefaultDB.json")
        
        # Verify default DB file exists
        self.assertTrue(os.path.exists(default_db_file), "Default MySQL DB file should exist")
        
        original_db = DB.copy()
        
        try:
            load_state(default_db_file)
            # Should load the default structure successfully
            self.assertEqual(DB["current"], "main")
            self.assertEqual(DB["primary_internal_name"], "main_db")
            self.assertIn("main_db", DB["attached"])
            self.assertIn("inventory_db", DB["attached"])
            
            # Verify MySQLDB validation works with default structure
            validated_db = MySQLDB(**DB)
            self.assertIsNotNone(validated_db)
            
        finally:
            DB.clear()
            DB.update(original_db)

    def test_minimal_state_structure_compatibility(self):
        """Test loading state with minimal structure for backward compatibility"""
        minimal_data = {
            "attached": {"legacy_db": {"sanitized": "legacy_db", "path": "legacy.duckdb"}},
            "current": "main"
            # Missing primary_internal_name and other newer fields
        }
        
        with open(self.test_file, 'w') as f:
            json.dump(minimal_data, f)
        
        original_db = DB.copy()
        
        try:
            load_state(self.test_file)
            # Should load minimal format successfully
            self.assertEqual(DB["current"], "main")
            self.assertIn("legacy_db", DB["attached"])
            
            # Should handle missing fields gracefully
            self.assertTrue("primary_internal_name" in DB or "primary_internal_name" not in DB)
        
        finally:
            DB.clear()
            DB.update(original_db)

    def test_save_and_reload_state_consistency(self):
        """Test that saved and reloaded state maintains consistency"""
        # Create test state
        test_state = {
            "attached": {
                "consistent_db": {"sanitized": "consistent_db", "path": "consistent.duckdb"}
            },
            "current": "consistent_db",
            "version": "1.0"
        }
        
        original_db = DB.copy()
        
        try:
            # Set test state
            DB.clear()
            DB.update(test_state)
            
            # Save state
            save_state(self.test_file)
            
            # Modify DB
            DB["current"] = "modified"
            
            # Reload state
            load_state(self.test_file)
            
            # Should match original test state
            self.assertEqual(DB["current"], "consistent_db")
            self.assertIn("consistent_db", DB["attached"])
            self.assertEqual(DB.get("version"), "1.0")
        
        finally:
            DB.clear()
            DB.update(original_db)


class TestModelsCoverageEnhancement(BaseTestCaseWithErrorHandler):
    """
    Additional tests to improve coverage of models.py
    """
    
    def test_validate_db_name_function(self):
        """Test _validate_db_name function directly"""
        from mysql.SimulationEngine.models import _validate_db_name
        
        # Valid names
        self.assertEqual(_validate_db_name("valid_db"), "valid_db")
        self.assertEqual(_validate_db_name("db123"), "db123")
        self.assertEqual(_validate_db_name("my-db"), "my-db")
        
        # Invalid names should raise ValueError
        with self.assertRaises(ValueError):
            _validate_db_name(".")
        
        with self.assertRaises(ValueError):
            _validate_db_name("..")
        
        with self.assertRaises(ValueError):
            _validate_db_name("invalid@db")

    def test_order_record_date_edge_cases(self):
        """Test OrderRecord date validation edge cases"""
        from mysql.SimulationEngine.models import OrderRecord
        
        # Test valid date parsing with different formats that should fail validation
        invalid_dates = [
            "2023-2-1",      # Single digit month/day
            "23-12-01",      # Two digit year 
            "2023/12/01",    # Wrong separator
            "01-12-2023",    # Wrong order
            "2023-13-01",    # Invalid month
            "2023-12-32",    # Invalid day
        ]
        
        for invalid_date in invalid_dates:
            with self.assertRaises(ValueError, msg=f"Should reject date: {invalid_date}"):
                OrderRecord(
                    id=1,
                    order_date=invalid_date,
                    customer_id=1,
                    total_amount=100.0
                )

    def test_mysql_db_validation_edge_cases(self):
        """Test MySQLDB validation edge cases"""
        from mysql.SimulationEngine.models import MySQLDB
        
        # Test with invalid timestamp format
        invalid_data = {
            "attached": {"test_db": {"sanitized": "test_db", "path": "test.duckdb"}},
            "current": "test_db",
            "primary_internal_name": "test_db",
            "last_updated": "not-a-timestamp"
        }
        
        with self.assertRaises(ValueError):
            MySQLDB(**invalid_data)
        
        # Test with valid timestamp
        valid_data = {
            "attached": {"test_db": {"sanitized": "test_db", "path": "test.duckdb"}},
            "current": "test_db", 
            "primary_internal_name": "test_db",
            "last_updated": "2023-12-25T14:30:45Z"
        }
        
        mysql_db = MySQLDB(**valid_data)
        self.assertIsNotNone(mysql_db)

    def test_database_schema_validation_edge_cases(self):
        """Test DatabaseSchema validation scenarios"""
        from mysql.SimulationEngine.models import DatabaseSchema, DatabaseTable
        
        # Test database name validation
        with self.assertRaises(ValueError):
            DatabaseSchema(
                database_name="invalid@name",
                tables={}
            )
        
        # Test valid database schema
        valid_schema = DatabaseSchema(
            database_name="valid_db",
            tables={
                "test_table": DatabaseTable(
                    table_name="test_table",
                    records=[{"id": 1, "name": "test"}]
                )
            }
        )
        self.assertEqual(valid_schema.database_name, "valid_db")


if __name__ == "__main__":
    unittest.main(verbosity=2)
